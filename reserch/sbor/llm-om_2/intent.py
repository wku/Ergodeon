import re
import json
import logging
from typing import Optional
from difflib import get_close_matches
from llm_client import LLMClient
from utils import find_balanced_json

log = logging.getLogger(__name__)

INTENT_KEYWORDS = {
    "create": ["create", "make", "write", "build", "generate"],
    "edit": ["edit", "modify", "change", "update"],
    "run": ["run", "execute", "start"],
    "explain": ["explain", "what does", "describe"],
    "test": ["test", "verify", "check"],
    "optimize": ["optimize", "improve", "refactor"]
}


class IntentClassifier:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def classify(self, goal: str) -> str:
        intent = self._fuzzy_match(goal)
        if intent:
            return intent
        low = goal.lower()
        if "what does" in low or "explain" in low:
            return "explain"
        intent = self._llm_fallback(goal)
        return intent or "create"

    def _fuzzy_match(self, text: str, cutoff=0.75) -> Optional[str]:
        words = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        for intent, keywords in INTENT_KEYWORDS.items():
            for w in words:
                if get_close_matches(w, keywords, n=1, cutoff=cutoff):
                    return intent
        return None

    def _llm_fallback(self, goal: str) -> Optional[str]:
        prompt = f"""You are a strict JSON responder. Classify the user's intent into one of:
create, edit, run, explain, test, optimize.

Return ONLY JSON like:
{{"intent":"create","confidence":0.95}}

User text:
{goal}"""
        raw = self.llm.call(prompt)
        js = find_balanced_json(raw)
        if not js:
            return None
        try:
            return json.loads(js).get("intent")
        except Exception:
            return None
