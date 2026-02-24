"""
DocumentGenerator - генерация документов планирования.
Рефакторинг: llm_json публичный, добавлены extract_inline_comments и mark_step_completed.
"""

import os
import re
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from openai import AsyncOpenAI
from openrouter_agent.utils import find_balanced_json, save_yaml, load_yaml, save_json, load_json
from openrouter_agent.agent.prompts import (
    PROMPT_PARSE_REQUEST, PROMPT_PROJECT_DIGEST, PROMPT_CHECKLIST,
    PROMPT_WALKTHROUGH, PROMPT_IMPLEMENTATION_PLAN, PROMPT_REVIEW_COMMENTS,
)
from openrouter_agent.agent.config import PipelineConfig

log = logging.getLogger(__name__)

TASK_STATUSES = {"pending", "in_progress", "completed", "failed", "blocked", "skipped"}

DOCS_FILES = {
    "parsed_request": "parsed_request.yaml",
    "digest": "project_digest.yaml",
    "checklist": "checklist.yaml",
    "walkthrough": "walkthrough.yaml",
    "plan": "implementation_plan.yaml",
    "execution_log": "execution_log.yaml",
}

LEGACY_FILES = {
    "parsed_request": "parsed_request.json",
    "digest": "project_digest.json",
    "checklist": "checklist.json",
    "walkthrough": "walkthrough.json",
    "plan": "implementation_plan.json",
    "execution_log": "execution_log.json",
}


def _load_doc(docs_dir: str, key: str) -> Any:
    yaml_path = os.path.join(docs_dir, DOCS_FILES[key])
    if os.path.exists(yaml_path):
        return load_yaml(yaml_path)
    legacy_path = os.path.join(docs_dir, LEGACY_FILES.get(key, ""))
    if legacy_path and os.path.exists(legacy_path):
        log.info(f"loading legacy json for {key}: {legacy_path}")
        return load_json(legacy_path)
    return None


class DocumentGenerator:
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()

    # ── LLM вызовы для генерации документов ──

    async def parse_request(self, client_request: str, project_digest: str,
                            client: AsyncOpenAI, model: str) -> Dict[str, Any]:
        prompt = PROMPT_PARSE_REQUEST.format(
            client_request=client_request,
            project_digest=project_digest or "не доступен",
        )
        return await self.llm_json(prompt, client, model, self.config.temperature_analysis)

    async def generate_digest(self, file_tree: str, file_contents: str,
                              parsed_request: str, client: AsyncOpenAI,
                              model: str) -> Dict[str, Any]:
        prompt = PROMPT_PROJECT_DIGEST.format(
            file_tree=file_tree,
            file_contents=file_contents,
            parsed_request=parsed_request,
        )
        return await self.llm_json(prompt, client, model, self.config.temperature_analysis)

    async def generate_checklist(self, project_digest: str, parsed_request: str,
                                 client: AsyncOpenAI, model: str) -> Dict[str, Any]:
        prompt = PROMPT_CHECKLIST.format(
            project_digest=project_digest,
            parsed_request=parsed_request,
        )
        return await self.llm_json(prompt, client, model, self.config.temperature_generation)

    async def generate_walkthrough(self, project_digest: str, parsed_request: str,
                                   checklist: str, client: AsyncOpenAI,
                                   model: str) -> Dict[str, Any]:
        prompt = PROMPT_WALKTHROUGH.format(
            project_digest=project_digest,
            parsed_request=parsed_request,
            checklist=checklist,
        )
        return await self.llm_json(prompt, client, model, self.config.temperature_generation)

    async def generate_plan(self, project_digest: str, parsed_request: str,
                            checklist: str, walkthrough: str,
                            client: AsyncOpenAI, model: str) -> Dict[str, Any]:
        prompt = PROMPT_IMPLEMENTATION_PLAN.format(
            project_digest=project_digest,
            parsed_request=parsed_request,
            checklist=checklist,
            walkthrough=walkthrough,
        )
        return await self.llm_json(prompt, client, model, self.config.temperature_generation)

    async def parse_review_comments(self, comments: str, checklist: str,
                                    walkthrough: str, plan: str,
                                    client: AsyncOpenAI, model: str) -> Dict[str, Any]:
        prompt = PROMPT_REVIEW_COMMENTS.format(
            client_comments=comments,
            checklist=checklist,
            walkthrough=walkthrough,
            implementation_plan=plan,
        )
        return await self.llm_json(prompt, client, model, self.config.temperature_analysis)

    # ── Валидация ──

    def validate_documents(self, checklist: Dict, walkthrough: Dict,
                           plan: Dict) -> Tuple[bool, List[str]]:
        issues = []
        checklist_ids = {t["id"] for t in checklist.get("checklist", [])}

        wt_covered = set()
        for block in walkthrough.get("blocks", []):
            for cid in block.get("checklist_ids", []):
                wt_covered.add(cid)
        uncovered = checklist_ids - wt_covered
        if uncovered:
            issues.append(f"checklist ids not covered by walkthrough: {uncovered}")

        plan_covered = set()
        for step in plan.get("steps", []):
            cid = step.get("checklist_id")
            if cid:
                plan_covered.add(cid)
        plan_uncovered = checklist_ids - plan_covered
        if plan_uncovered:
            issues.append(f"checklist ids not covered by plan: {plan_uncovered}")

        return len(issues) == 0, issues

    # ── Inline comments extraction ──

    def extract_inline_comments(self, docs_dir: str) -> str:
        comments = []
        for fname in ("checklist.md", "walkthrough.md", "implementation_plan.md"):
            fpath = os.path.join(docs_dir, fname)
            if not os.path.exists(fpath):
                continue
            try:
                with open(fpath, "r", encoding="utf-8") as fh:
                    content = fh.read()
                found = re.findall(r"<!--\s*COMMENT:\s*(.*?)\s*-->", content, re.DOTALL)
                for c in found:
                    comments.append(f"[{fname}] {c.strip()}")
            except Exception as e:
                log.warning(f"error reading {fpath}: {e}")
        return "\n".join(comments)

    # ── Mark step in checklist ──

    def mark_step_completed(self, docs_dir: str, checklist_id: str,
                            step_number: Any):
        cl_path = os.path.join(docs_dir, "checklist.md")
        if not os.path.exists(cl_path):
            cl_path = os.path.join(docs_dir, "artifacts", "checklist.md")
        if not os.path.exists(cl_path):
            return
        try:
            with open(cl_path, "r", encoding="utf-8") as fh:
                content = fh.read()
            pattern = rf"(\- \[) \](\s*{re.escape(str(checklist_id))})"
            updated = re.sub(pattern, r"\1x]\2", content, count=1)
            if updated != content:
                with open(cl_path, "w", encoding="utf-8") as fh:
                    fh.write(updated)
        except Exception as e:
            log.warning(f"mark_step_completed error: {e}")

    # ── Сохранение ──

    def save_to_project(self, docs_dir: str, docs: Dict[str, Any]) -> str:
        os.makedirs(docs_dir, exist_ok=True)
        if "parsed_request" in docs:
            save_yaml(os.path.join(docs_dir, DOCS_FILES["parsed_request"]),
                      docs["parsed_request"])
        if "digest" in docs:
            save_yaml(os.path.join(docs_dir, DOCS_FILES["digest"]),
                      docs["digest"])
        if "checklist" in docs:
            self._save_checklist_md(docs_dir, docs["checklist"])
            save_yaml(os.path.join(docs_dir, DOCS_FILES["checklist"]),
                      docs["checklist"])
        if "walkthrough" in docs:
            self._save_walkthrough_md(docs_dir, docs["walkthrough"])
            save_yaml(os.path.join(docs_dir, DOCS_FILES["walkthrough"]),
                      docs["walkthrough"])
        if "plan" in docs:
            self._save_plan_md(docs_dir, docs["plan"])
            save_yaml(os.path.join(docs_dir, DOCS_FILES["plan"]),
                      docs["plan"])
        review_path = os.path.join(docs_dir, "review_comments.md")
        if not os.path.exists(review_path):
            with open(review_path, "w", encoding="utf-8") as fh:
                fh.write("# Review Comments\n\n")
                fh.write("Оставляйте комментарии в markdown файлах:\n\n")
                fh.write("```\n<!-- COMMENT: текст комментария -->\n```\n\n")
                fh.write("Размещайте тег после строки к которой относится комментарий.\n")
        log.info(f"docs saved to {docs_dir}")
        return docs_dir

    def save_execution_log(self, docs_dir: str, log_entries: List[Dict],
                           meta: Dict[str, Any] = None) -> str:
        os.makedirs(docs_dir, exist_ok=True)
        stats = {"completed": 0, "failed": 0, "blocked": 0, "skipped": 0}
        for e in log_entries:
            s = e.get("status", "unknown")
            if s in stats:
                stats[s] += 1
        data = {"meta": meta or {}, "stats": stats, "steps": log_entries}
        yaml_path = os.path.join(docs_dir, DOCS_FILES["execution_log"])
        save_yaml(yaml_path, data)
        self._save_execution_log_md(docs_dir, log_entries, stats)
        log.info(f"execution log saved: {yaml_path}")
        return yaml_path

    def load_execution_log(self, docs_dir: str) -> Optional[Dict[str, Any]]:
        return _load_doc(docs_dir, "execution_log")

    def load_plan(self, docs_dir: str) -> Optional[Dict[str, Any]]:
        return _load_doc(docs_dir, "plan")

    # ── Публичный LLM JSON метод ──

    async def llm_json(self, prompt: str, client: AsyncOpenAI, model: str,
                       temperature: float = 0.2) -> Dict[str, Any]:
        try:
            r = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            raw = r.choices[0].message.content or ""
            js = find_balanced_json(raw)
            if not js:
                log.warning(f"llm returned no json, raw: {raw[:300]}")
                return {}
            return json.loads(js)
        except Exception as e:
            log.error(f"llm_json error: {e}")
            return {}

    # Обратная совместимость
    _llm_json = llm_json

    # ── MD генераторы ──

    def _save_checklist_md(self, docs_dir: str, checklist: Dict):
        lines = ["# Чеклист задач\n"]
        for task in checklist.get("checklist", []):
            tid = task.get("id", "?")
            title = task.get("title", "")
            cat = task.get("category", "")
            deps = task.get("depends_on", [])
            lines.append(f"- [ ] {tid} [{cat}] {title}")
            if deps:
                lines.append(f"  Зависит от: {', '.join(str(d) for d in deps)}")
        path = os.path.join(docs_dir, "checklist.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

    def _save_walkthrough_md(self, docs_dir: str, walkthrough: Dict):
        lines = [f"# {walkthrough.get('title', 'Walkthrough')}\n"]
        lines.append(f"{walkthrough.get('summary', '')}\n")
        for block in walkthrough.get("blocks", []):
            lines.append(f"\n## {block.get('name', '')}")
            lines.append(f"Цель: {block.get('purpose', '')}")
            for fi in block.get("files", []):
                lines.append(
                    f"- [{fi.get('operation', '?')}] {fi.get('path', '')} "
                    f"- {fi.get('changes_description', '')}"
                )
            ids = block.get("checklist_ids", [])
            if ids:
                lines.append(f"Чеклист: {', '.join(str(i) for i in ids)}")
            risks = block.get("risks", [])
            if risks:
                lines.append(f"Риски: {', '.join(risks)}")
        path = os.path.join(docs_dir, "walkthrough.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

    def _save_plan_md(self, docs_dir: str, plan: Dict):
        lines = ["# План имплементации\n"]
        for step in plan.get("steps", []):
            sn = step.get("step_number", "?")
            desc = step.get("description", "")
            target = step.get("target", "")
            lines.append(f"- [ ] Шаг {sn}: {desc}")
            if target:
                lines.append(f"  Файл: {target}")
        path = os.path.join(docs_dir, "implementation_plan.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

    def _save_execution_log_md(self, docs_dir: str, log_entries: List[Dict],
                               stats: Dict):
        lines = ["# Лог выполнения\n"]
        for entry in log_entries:
            status = entry.get("status", "unknown")
            step = entry.get("step_number", "?")
            desc = entry.get("description", "")
            elapsed = entry.get("elapsed", 0)
            error = entry.get("error", "")
            marker = "x" if status == "completed" else " "
            lines.append(
                f"- [{marker}] Шаг {step}: {desc} [{status}] ({elapsed:.1f}s)"
            )
            if error:
                lines.append(f"  Ошибка: {error}")
        lines.append("\n## Статистика\n")
        for k, v in stats.items():
            lines.append(f"- {k}: {v}")
        path = os.path.join(docs_dir, "execution_log.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
