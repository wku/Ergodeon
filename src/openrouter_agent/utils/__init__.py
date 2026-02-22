import os
import json
import logging
from typing import Optional, Any
from difflib import unified_diff

log = logging.getLogger(__name__)


def find_balanced_json(text: str) -> Optional[str]:
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '"' and not esc:
            in_string = not in_string
        if ch == "\\" and not esc:
            esc = True
            continue
        else:
            esc = False
        if not in_string:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return None


def load_json(path: str, default: Any = None) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.warning(f"load_json error {path}: {e}")
        return default


def save_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def compute_diff(before: Optional[str], after: Optional[str]) -> str:
    a = before.splitlines(keepends=True) if before else []
    b = after.splitlines(keepends=True) if after else []
    return ''.join(unified_diff(a, b, fromfile='before', tofile='after'))
