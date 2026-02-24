import os
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# Assuming structure: Ergodeon/src/openrouter_agent/agent/prompts.py
# Target: Ergodeon/promt
PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "promt"

def _load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        log.error(f"Prompt file not found: {path}")
        return ""

PROMPT_PARSE_REQUEST = _load_prompt('prompt_parse_request')
PROMPT_PROJECT_DIGEST = _load_prompt('prompt_project_digest')
PROMPT_CHECKLIST = _load_prompt('prompt_checklist')
PROMPT_WALKTHROUGH = _load_prompt('prompt_walkthrough')
PROMPT_IMPLEMENTATION_PLAN = _load_prompt('prompt_implementation_plan')
PROMPT_REVIEW_COMMENTS = _load_prompt('prompt_review_comments')
PROMPT_EXECUTE_STEP = _load_prompt('prompt_execute_step')
