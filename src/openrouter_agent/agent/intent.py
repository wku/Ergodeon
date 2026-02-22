import re
import json
import logging
from typing import Optional
from difflib import get_close_matches
from openai import AsyncOpenAI
from openrouter_agent.utils import find_balanced_json

log = logging.getLogger(__name__)

INTENT_KEYWORDS = {
    "create": ["create", "make", "write", "build", "generate"],
    "edit": ["edit", "modify", "change", "update"],
    "run": ["run", "execute", "start"],
    "explain": ["explain", "what does", "describe"],
    "test": ["test", "verify", "check"],
    "optimize": ["optimize", "improve", "refactor"],
}


class IntentClassifier:
    def classify(self, goal: str) -> str:
        intent = self._fuzzy_match(goal)
        if intent:
            return intent
        low = goal.lower()
        if "what does" in low or "explain" in low:
            return "explain"
        return "create"

    async def classify_with_llm(self, goal: str, client: AsyncOpenAI, model: str) -> str:
        intent = self._fuzzy_match(goal)
        if intent:
            return intent
        low = goal.lower()
        if "what does" in low or "explain" in low:
            return "explain"
        result = await self._llm_fallback(goal, client, model)
        return result or "create"

    def _fuzzy_match(self, text: str, cutoff: float = 0.75) -> Optional[str]:
        words = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        for intent, keywords in INTENT_KEYWORDS.items():
            for w in words:
                if get_close_matches(w, keywords, n=1, cutoff=cutoff):
                    return intent
        return None

    async def _llm_fallback(self, goal: str, client: AsyncOpenAI, model: str) -> Optional[str]:
        prompt = (
            "You are a strict JSON responder. Classify the user's intent into one of: "
            "create, edit, run, explain, test, optimize.\n"
            'Return ONLY JSON like: {"intent":"create","confidence":0.95}\n'
            f"User text: {goal}"
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
                return None
            return json.loads(js).get("intent")
        except Exception as e:
            log.warning(f"intent llm fallback error: {e}")
            return None
