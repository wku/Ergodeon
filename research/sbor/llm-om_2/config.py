import os

OPENROUTER_URL = "https://openrouter.ai/api/v1"
OPENROUTER_KEY = "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"
MODEL = "google/gemini-2.5-flash"

BASE_WORKDIR = "workspace"
MEMORY_DIR = "memory"
EPISODES_FILE = os.path.join(MEMORY_DIR, "episodes.json")
MAX_STEP_RETRIES = 1
PLAN_STEP_LIMIT = 12
LLM_TIMEOUT = 30

os.makedirs(BASE_WORKDIR, exist_ok=True)
os.makedirs(MEMORY_DIR, exist_ok=True)
