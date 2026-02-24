"""
ContextManager - управление context.yaml на уровне проекта.

Хранит краткую сводку о проекте, обновляется после каждого стейджа.
Передаётся в LLM при классификации и планировании.
"""

import os
import logging
from typing import Dict, Any, Optional
from openrouter_agent.utils import save_yaml, load_yaml

log = logging.getLogger(__name__)

CONTEXT_FILE = "flow/context.yaml"

DEFAULT_CONTEXT = {
    "project_name": "",
    "stack": [],
    "summary": "",
    "stages_completed": 0,
    "last_stage_summary": "",
    "known_issues": [],
}


class ContextManager:
    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        self.context_path = os.path.join(self.project_dir, CONTEXT_FILE)

    def load(self) -> Dict[str, Any]:
        if os.path.exists(self.context_path):
            return load_yaml(self.context_path) or dict(DEFAULT_CONTEXT)
        return dict(DEFAULT_CONTEXT)

    def save(self, ctx: Dict[str, Any]):
        os.makedirs(os.path.dirname(self.context_path), exist_ok=True)
        save_yaml(self.context_path, ctx)

    def exists(self) -> bool:
        return os.path.exists(self.context_path)

    def update_after_stage(self, stage_num: int, workflow: str,
                           query: str, status: str,
                           summary: str = "", stack: list = None,
                           issues: list = None):
        ctx = self.load()
        ctx["stages_completed"] = stage_num
        ctx["last_stage_summary"] = summary or f"[{workflow}] {query[:100]}"
        if stack:
            existing = set(ctx.get("stack", []))
            existing.update(stack)
            ctx["stack"] = sorted(existing)
        if issues:
            ctx["known_issues"] = issues
        self.save(ctx)
        log.info(f"context updated after stage-{stage_num}")

    def get_for_llm(self) -> str:
        ctx = self.load()
        if not ctx.get("summary") and not ctx.get("last_stage_summary"):
            return ""
        lines = []
        if ctx.get("project_name"):
            lines.append(f"Проект: {ctx['project_name']}")
        if ctx.get("stack"):
            lines.append(f"Стек: {', '.join(ctx['stack'])}")
        if ctx.get("summary"):
            lines.append(f"Описание: {ctx['summary']}")
        if ctx.get("last_stage_summary"):
            lines.append(f"Последнее действие: {ctx['last_stage_summary']}")
        if ctx.get("stages_completed"):
            lines.append(f"Завершённых стейджей: {ctx['stages_completed']}")
        if ctx.get("known_issues"):
            lines.append(f"Известные проблемы: {'; '.join(ctx['known_issues'])}")
        return "\n".join(lines)
