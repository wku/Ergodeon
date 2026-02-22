import logging
from openai import OpenAI
from config import OPENROUTER_URL, OPENROUTER_KEY, MODEL, LLM_TIMEOUT

log = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, url=OPENROUTER_URL, key=OPENROUTER_KEY, model=MODEL, timeout=LLM_TIMEOUT):
        self.model = model
        self.client = OpenAI(base_url=url, api_key=key, timeout=timeout)

    def call(self, prompt: str) -> str:
        try:
            r = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return r.choices[0].message.content or ""
        except Exception as e:
            log.error(f"llm call failed: {e}")
            return f"__LLM_ERROR__ {e}"
