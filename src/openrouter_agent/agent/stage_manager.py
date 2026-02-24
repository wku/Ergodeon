"""
StageManager - управление стейджами в папке flow/ проекта.

Каждый запрос пользователя (кроме chat) создаёт новый stage-N/.
Внутри хранятся meta.yaml, plan.yaml, execution_log.yaml и artifacts/.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from openrouter_agent.utils import save_yaml, load_yaml

log = logging.getLogger(__name__)

FLOW_DIR = "flow"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class StageManager:
    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        self.flow_dir = os.path.join(self.project_dir, FLOW_DIR)

    def _stage_dir(self, stage_num: int) -> str:
        return os.path.join(self.flow_dir, f"stage-{stage_num}")

    def get_latest_stage_num(self) -> int:
        if not os.path.isdir(self.flow_dir):
            return 0
        nums = []
        for d in os.listdir(self.flow_dir):
            if d.startswith("stage-") and os.path.isdir(os.path.join(self.flow_dir, d)):
                try:
                    nums.append(int(d.split("-", 1)[1]))
                except ValueError:
                    pass
        return max(nums) if nums else 0

    def create_stage(self, workflow: str, query: str) -> "Stage":
        num = self.get_latest_stage_num() + 1
        stage_dir = self._stage_dir(num)
        os.makedirs(stage_dir, exist_ok=True)
        os.makedirs(os.path.join(stage_dir, "artifacts"), exist_ok=True)

        meta = {
            "stage": num,
            "workflow": workflow,
            "query": query,
            "status": "running",
            "started_at": _now_iso(),
            "finished_at": None,
            "previous_stages_read": [],
        }
        save_yaml(os.path.join(stage_dir, "meta.yaml"), meta)
        log.info(f"created stage-{num} [{workflow}]")
        return Stage(stage_dir, meta)

    def load_stage(self, stage_num: int) -> Optional["Stage"]:
        stage_dir = self._stage_dir(stage_num)
        meta_path = os.path.join(stage_dir, "meta.yaml")
        if not os.path.exists(meta_path):
            return None
        meta = load_yaml(meta_path) or {}
        return Stage(stage_dir, meta)

    def load_latest_stage(self) -> Optional["Stage"]:
        num = self.get_latest_stage_num()
        return self.load_stage(num) if num > 0 else None

    def find_resumable_stage(self) -> Optional["Stage"]:
        """Ищет последний стейдж со статусом != completed/failed."""
        for num in range(self.get_latest_stage_num(), 0, -1):
            stage = self.load_stage(num)
            if stage and stage.meta.get("status") in ("running", "partial", "paused"):
                return stage
        return None

    def list_stages(self) -> List[Dict[str, Any]]:
        result = []
        for num in range(1, self.get_latest_stage_num() + 1):
            stage = self.load_stage(num)
            if stage:
                result.append({
                    "num": num,
                    "workflow": stage.meta.get("workflow"),
                    "query": stage.meta.get("query", "")[:100],
                    "status": stage.meta.get("status"),
                })
        return result


class Stage:
    def __init__(self, stage_dir: str, meta: Dict[str, Any]):
        self.stage_dir = stage_dir
        self.meta = meta
        self.artifacts_dir = os.path.join(stage_dir, "artifacts")

    @property
    def num(self) -> int:
        return self.meta.get("stage", 0)

    @property
    def workflow(self) -> str:
        return self.meta.get("workflow", "")

    @property
    def status(self) -> str:
        return self.meta.get("status", "unknown")

    def update_status(self, status: str):
        self.meta["status"] = status
        if status in ("completed", "failed", "partial"):
            self.meta["finished_at"] = _now_iso()
        self._save_meta()

    def _save_meta(self):
        save_yaml(os.path.join(self.stage_dir, "meta.yaml"), self.meta)

    def save_plan(self, plan: Dict[str, Any]):
        save_yaml(os.path.join(self.stage_dir, "plan.yaml"), plan)
        self._save_plan_md(plan)

    def load_plan(self) -> Optional[Dict[str, Any]]:
        return load_yaml(os.path.join(self.stage_dir, "plan.yaml"))

    def save_artifact(self, name: str, data: Any):
        path = os.path.join(self.artifacts_dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if isinstance(data, str):
            with open(path, "w", encoding="utf-8") as f:
                f.write(data)
        else:
            save_yaml(path, data)

    def load_artifact(self, name: str) -> Any:
        path = os.path.join(self.artifacts_dir, name)
        if not os.path.exists(path):
            return None
        if name.endswith((".yaml", ".yml")):
            return load_yaml(path)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def save_execution_log(self, entries: List[Dict], log_meta: Dict[str, Any] = None):
        stats = {"completed": 0, "failed": 0, "blocked": 0, "skipped": 0}
        for e in entries:
            s = e.get("status", "unknown")
            if s in stats:
                stats[s] += 1

        data = {"meta": log_meta or {}, "stats": stats, "steps": entries}
        save_yaml(os.path.join(self.stage_dir, "execution_log.yaml"), data)
        self._save_execution_log_md(entries, stats)

    def load_execution_log(self) -> Optional[Dict[str, Any]]:
        return load_yaml(os.path.join(self.stage_dir, "execution_log.yaml"))

    def mark_previous_read(self, stage_nums: List[int]):
        self.meta.setdefault("previous_stages_read", [])
        for n in stage_nums:
            if n not in self.meta["previous_stages_read"]:
                self.meta["previous_stages_read"].append(n)
        self._save_meta()

    def _save_plan_md(self, plan: Dict[str, Any]):
        lines = [f"# План выполнения [{self.workflow}]\n"]
        for phase in plan.get("phases", []):
            lines.append(f"\n## {phase.get('name', '')}")
            lines.append(f"Статус: {phase.get('status', 'pending')}\n")
            for step in phase.get("steps", []):
                marker = "x" if step.get("status") == "completed" else " "
                lines.append(f"- [{marker}] {step.get('id', '')}: {step.get('description', '')}")
                deps = step.get("depends_on", [])
                if deps:
                    lines.append(f"  Зависит от: {', '.join(deps)}")
        path = os.path.join(self.stage_dir, "plan.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _save_execution_log_md(self, entries: List[Dict], stats: Dict):
        lines = ["# Лог выполнения\n"]
        for entry in entries:
            status = entry.get("status", "unknown")
            step = entry.get("step_number", entry.get("id", "?"))
            desc = entry.get("description", "")
            elapsed = entry.get("elapsed", 0)
            error = entry.get("error", "")
            marker = "x" if status == "completed" else " "
            lines.append(f"- [{marker}] Шаг {step}: {desc} [{status}] ({elapsed:.1f}s)")
            if error:
                lines.append(f"  Ошибка: {error}")
        lines.append("\n## Статистика\n")
        for k, v in stats.items():
            lines.append(f"- {k}: {v}")
        path = os.path.join(self.stage_dir, "execution_log.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
