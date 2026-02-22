import json
import logging
from typing import Dict, Any, List, Tuple
from llm_client import LLMClient
from utils import find_balanced_json
from config import PLAN_STEP_LIMIT

log = logging.getLogger(__name__)

ALLOWED_ACTIONS = {"write_file", "run_file", "read_file", "print", "explain", "test"}


class Planner:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate_plan(self, goal: str, memory: List[Dict[str, Any]]) -> Tuple[bool, List[Dict[str, Any]], str]:
        sample = {
            "plan": [
                {"action": "write_file", "filename": "sum.py", "content": "def add(a,b):\\n    return a+b\\n\\nprint(add(2,3))"},
                {"action": "run_file", "filename": "sum.py", "args": []},
            ]
        }
        prompt = f"""You are a planning assistant. Output ONLY a single VALID JSON object (no explanations).
Schema:
{{ "plan": [ step1, step2, ... ] }}
Each step must be an object with:
- action: one of "write_file", "run_file", "read_file", "print", "explain", "test"
- write_file: include filename and content (full file text)
- run_file: include filename and optional args (list)
- read_file: include filename
- print: include text
- explain: include filename (agent will run LLM-based explanation)
- test: include filename and tests list (optional)

Keep steps minimal & deterministic. Use filenames only (no absolute paths).
Example:
{json.dumps(sample, indent=2)}

Goal: {goal}
Recent memory (last attempts): {json.dumps(memory[-5:], ensure_ascii=False)}"""

        raw = self.llm.call(prompt)
        log.info(f"raw plan response: {raw[:200]}")
        js = find_balanced_json(raw)
        if not js:
            return False, [], f"llm did not return json plan. raw: {raw[:200]}"
        try:
            plan_obj = json.loads(js)
        except Exception as e:
            return False, [], f"json parse failed: {e}"
        steps = plan_obj.get("plan", [])
        ok, msg = self.validate(steps)
        if not ok:
            return False, steps, msg
        return True, steps, "ok"

    def suggest_fix(self, goal: str, step: Dict[str, Any], observed_output: str, memory: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = f"""You are a helpful assistant that FIXES a single step when it failed.
Output ONLY a single valid JSON object.

Input:
- Goal: {goal}
- Failed step: {json.dumps(step, ensure_ascii=False)}
- Observed output / error: {observed_output}

Rules:
- Return JSON like: {{ "fixed_step": {{ ... }} }} where fixed_step follows the step schema.
- If you cannot fix it, return: {{ "action": "abort", "reason": "..." }}
- Do NOT include any explanation text.
- Constrain fixes: allowed actions: write_file (full content), run_file (args), read_file, print, explain, test.
- Do NOT return shell commands or absolute paths.

Recent memory: {json.dumps(memory[-5:], ensure_ascii=False)}"""
        raw = self.llm.call(prompt)
        js = find_balanced_json(raw)
        if not js:
            return {}
        try:
            return json.loads(js)
        except Exception:
            return {}

    def suggest_interactive_fix(self, goal: str, step: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""Return ONLY JSON: {{ "fixed_step": {{ ... }} }} to replace the failing step.
The failing step requires interactive stdin. Provide a non-interactive alternative:
e.g. change the write_file content to include defaults or make run_file accept args.
Failing step: {json.dumps(step, ensure_ascii=False)}
Goal: {goal}"""
        raw = self.llm.call(prompt)
        js = find_balanced_json(raw)
        if not js:
            return {}
        try:
            return json.loads(js)
        except Exception:
            return {}

    def evaluate(self, goal: str, plan: List[Dict[str, Any]], results: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = f"""You are an evaluator. Return ONLY JSON:
{{"ok": true, "score": 0.9, "notes": "..."}}

Input:
- Goal: {goal}
- Plan: {json.dumps(plan, ensure_ascii=False)}
- Results: {json.dumps(results, ensure_ascii=False)}

Assess whether the plan + results achieved the goal. Give a score 0.0-1.0 and short notes."""
        raw = self.llm.call(prompt)
        js = find_balanced_json(raw)
        if not js:
            return {"ok": False, "score": 0.0, "notes": "no_json_from_llm"}
        try:
            return json.loads(js)
        except Exception:
            return {"ok": False, "score": 0.0, "notes": "json_parse_error"}

    def explain_code(self, content: str) -> str:
        prompt = f"""You are a code explainer. Return ONLY JSON:
{{"explanation":"..."}}
Explain what this python program does in simple terms (1-3 short sentences). Return only JSON.
Code:
{content}"""
        raw = self.llm.call(prompt)
        js = find_balanced_json(raw)
        if not js:
            return ""
        try:
            return json.loads(js).get("explanation", "")
        except Exception:
            return ""

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
