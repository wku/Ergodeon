import json
import time
import logging
from typing import Dict, Any
from config import BASE_WORKDIR, MAX_STEP_RETRIES
from llm_client import LLMClient
from intent import IntentClassifier
from memory import EpisodeMemory
from executor import Executor, Sandbox
from planner import Planner

log = logging.getLogger(__name__)


class Agent:
    def __init__(self):
        self.llm = LLMClient()
        self.intent_classifier = IntentClassifier(self.llm)
        self.memory = EpisodeMemory()
        self.executor = Executor(BASE_WORKDIR)
        self.planner = Planner(self.llm)

    def run_episode(self, original_goal: str) -> Dict[str, Any]:
        goal = original_goal.strip()
        log.info(f"goal: {goal}")

        intent = self.intent_classifier.classify(goal)
        log.info(f"intent: {intent}")

        similar = self.memory.find_similar(goal)
        if similar and similar.get("goal", "").lower() == goal.lower():
            log.info("exact match found in memory, reusing")
            return {"success": True, "reused_episode": similar}

        ok, steps, msg = self.planner.generate_plan(goal, self.memory.recent())
        if not ok:
            log.error(f"plan failed: {msg}")
            return {"success": False, "reason": "plan_failed", "detail": msg}

        episode_id = str(int(time.time() * 1000))
        epdir = Sandbox.prepare(BASE_WORKDIR, episode_id)
        Sandbox.snapshot(BASE_WORKDIR, epdir)

        record = {
            "goal": goal,
            "intent": intent,
            "plan": steps,
            "results": [],
            "timestamp": time.time(),
            "episode_dir": epdir
        }

        for i, step in enumerate(steps):
            log.info(f"step {i+1}/{len(steps)}: {step.get('action')}")
            current_step = step
            attempt = 0

            while attempt <= MAX_STEP_RETRIES:
                filename = current_step.get("filename")
                before_content = self.executor.read_file_content(filename) if filename else None

                result = self.executor.execute_step(current_step)

                if result.get("_needs_llm_explain"):
                    explanation = self.planner.explain_code(result.get("output", ""))
                    result = {"success": True, "output": explanation}

                after_content = self.executor.read_file_content(filename) if filename else None
                diff = Executor.compute_diff(before_content, after_content)

                record["results"].append({
                    "step": current_step,
                    "result": result,
                    "attempt": attempt,
                    "file_diff": diff
                })

                if result.get("success"):
                    log.info(f"step {i+1} ok: {str(result.get('output', ''))[:100]}")
                    break

                log.warning(f"step {i+1} failed: {result.get('error')}")

                if result.get("error") == "interactive_program_requires_input":
                    fix_obj = self.planner.suggest_interactive_fix(goal, current_step)
                else:
                    fix_obj = self.planner.suggest_fix(
                        goal, current_step,
                        json.dumps(result, ensure_ascii=False),
                        self.memory.recent()
                    )

                if not fix_obj:
                    log.warning("no fix from llm")
                    break

                if fix_obj.get("action") == "abort":
                    log.warning(f"llm abort: {fix_obj.get('reason')}")
                    return {"success": False, "reason": "llm_abort", "detail": fix_obj.get("reason")}

                fixed_step = fix_obj.get("fixed_step")
                if not fixed_step:
                    break

                v_ok, v_msg = self.planner.validate([fixed_step])
                if not v_ok:
                    log.warning(f"fixed step invalid: {v_msg}")
                    break

                current_step = fixed_step
                attempt += 1
            else:
                log.error(f"step {i+1} failed after retries")
                return {
                    "success": False,
                    "reason": "step_failed",
                    "step_index": i,
                    "step": current_step,
                    "episode": record
                }

        critique = self.planner.evaluate(goal, steps, record["results"])
        record["evaluation"] = critique
        self.memory.add(record)
        log.info("episode completed")
        return {"success": True, "episode": record}
