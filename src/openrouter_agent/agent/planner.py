import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from openai import AsyncOpenAI
from openrouter_agent.utils import find_balanced_json

log = logging.getLogger(__name__)

ALLOWED_ACTIONS = {"write_file", "run_file", "read_file", "print", "explain", "test"}
PLAN_STEP_LIMIT = 12


class Planner:
    async def generate_plan(
        self, goal: str, memory: List[Dict[str, Any]], client: AsyncOpenAI, model: str
    ) -> Tuple[bool, List[Dict[str, Any]], str]:
        sample = {
            "plan": [
                {"action": "write_file", "filename": "sum.py", "content": "def add(a,b):\\n    return a+b\\n\\nprint(add(2,3))"},
                {"action": "run_file", "filename": "sum.py", "args": []},
            ]
        }
        prompt = (
            "You are a planning assistant. Output ONLY a single VALID JSON object (no explanations).\n"
            "Schema:\n"
            '{ "plan": [ step1, step2, ... ] }\n'
            "Each step must be an object with:\n"
            '- action: one of "write_file", "run_file", "read_file", "print", "explain", "test"\n'
            "- write_file: include filename and content (full file text)\n"
            "- run_file: include filename and optional args (list)\n"
            "- read_file: include filename\n"
            "- print: include text\n"
            "- explain: include filename\n"
            "- test: include filename and tests list (optional)\n\n"
            "Keep steps minimal & deterministic. Use filenames only (no absolute paths).\n"
            f"Example:\n{json.dumps(sample, indent=2)}\n\n"
            f"Goal: {goal}\n"
            f"Recent memory: {json.dumps(memory[-5:], ensure_ascii=False)}"
        )
        try:
            r = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            raw = r.choices[0].message.content or ""
            log.info(f"raw plan response: {raw[:200]}")
            js = find_balanced_json(raw)
            if not js:
                return False, [], f"llm did not return json plan. raw: {raw[:200]}"
            plan_obj = json.loads(js)
            steps = plan_obj.get("plan", [])
            ok, msg = self.validate(steps)
            if not ok:
                return False, steps, msg
            return True, steps, "ok"
        except Exception as e:
            log.error(f"generate_plan error: {e}")
            return False, [], str(e)

    async def suggest_fix(
        self,
        goal: str,
        step: Dict[str, Any],
        observed_output: str,
        memory: List[Dict[str, Any]],
        client: AsyncOpenAI,
        model: str,
    ) -> Dict[str, Any]:
        prompt = (
            "You are a helpful assistant that FIXES a single step when it failed.\n"
            "Output ONLY a single valid JSON object.\n\n"
            f"Input:\n"
            f"- Goal: {goal}\n"
            f"- Failed step: {json.dumps(step, ensure_ascii=False)}\n"
            f"- Observed output / error: {observed_output}\n\n"
            "Rules:\n"
            '- Return JSON like: { "fixed_step": { ... } } where fixed_step follows the step schema.\n'
            '- If you cannot fix it, return: { "action": "abort", "reason": "..." }\n'
            "- Do NOT include any explanation text.\n"
            "- Allowed actions: write_file (full content), run_file (args), read_file, print, explain, test.\n"
            "- Do NOT return shell commands or absolute paths.\n\n"
            f"Recent memory: {json.dumps(memory[-5:], ensure_ascii=False)}"
        )
        try:
            r = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            raw = r.choices[0].message.content or ""
            js = find_balanced_json(raw)
            if not js:
                return {}
            return json.loads(js)
        except Exception as e:
            log.error(f"suggest_fix error: {e}")
            return {}

    async def evaluate(
        self,
        goal: str,
        plan: List[Dict[str, Any]],
        results: List[Dict[str, Any]],
        client: AsyncOpenAI,
        model: str,
    ) -> Dict[str, Any]:
        prompt = (
            "You are an evaluator. Return ONLY JSON:\n"
            '{"ok": true, "score": 0.9, "notes": "..."}\n\n'
            f"Input:\n"
            f"- Goal: {goal}\n"
            f"- Plan: {json.dumps(plan, ensure_ascii=False)}\n"
            f"- Results: {json.dumps(results, ensure_ascii=False)}\n\n"
            "Assess whether the plan + results achieved the goal. Give a score 0.0-1.0 and short notes."
        )
        try:
            r = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            raw = r.choices[0].message.content or ""
            js = find_balanced_json(raw)
            if not js:
                return {"ok": False, "score": 0.0, "notes": "no_json_from_llm"}
            return json.loads(js)
        except Exception as e:
            log.error(f"evaluate error: {e}")
            return {"ok": False, "score": 0.0, "notes": str(e)}

    @staticmethod
    def validate(plan: List[Dict[str, Any]]) -> Tuple[bool, str]:
        if not isinstance(plan, list):
            return False, "plan must be a list"
        if len(plan) == 0:
            return False, "plan empty"
        if len(plan) > PLAN_STEP_LIMIT:
            return False, f"plan too long (>{PLAN_STEP_LIMIT})"
        for step in plan:
            action = step.get("action")
            if action not in ALLOWED_ACTIONS:
                return False, f"action not allowed: {action}"
            if action == "write_file":
                fn = step.get("filename")
                if not fn or ".." in fn or fn.startswith("/") or "\\" in fn:
                    return False, f"unsafe filename: {fn}"
                if step.get("content") is None:
                    return False, "write_file missing content"
            if action in ("run_file", "read_file", "explain", "test"):
                fn = step.get("filename")
                if not fn or ".." in fn or fn.startswith("/") or "\\" in fn:
                    return False, f"unsafe filename: {fn}"
        return True, "ok"
