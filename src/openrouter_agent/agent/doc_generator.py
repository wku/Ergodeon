import os
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from openai import AsyncOpenAI
from openrouter_agent.utils import find_balanced_json, save_json, load_json
from openrouter_agent.agent.prompts import (
    PROMPT_PARSE_REQUEST, PROMPT_PROJECT_DIGEST, PROMPT_CHECKLIST,
    PROMPT_WALKTHROUGH, PROMPT_IMPLEMENTATION_PLAN, PROMPT_REVIEW_COMMENTS,
)
from openrouter_agent.agent.config import PipelineConfig

log = logging.getLogger(__name__)

TASK_STATUSES = {"pending", "in_progress", "completed", "failed", "blocked", "skipped"}


class DocumentGenerator:
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()

    async def parse_request(self, client_request: str, project_digest: str,
                            client: AsyncOpenAI, model: str) -> Dict[str, Any]:
        prompt = PROMPT_PARSE_REQUEST.format(
            client_request=client_request,
            project_digest=project_digest or "не доступен",
        )
        return await self._llm_json(prompt, client, model, self.config.temperature_analysis)

    async def generate_digest(self, file_tree: str, file_contents: str,
                              parsed_request: str, client: AsyncOpenAI, model: str) -> Dict[str, Any]:
        prompt = PROMPT_PROJECT_DIGEST.format(
            file_tree=file_tree,
            file_contents=file_contents,
            parsed_request=parsed_request,
        )
        return await self._llm_json(prompt, client, model, self.config.temperature_analysis)

    async def generate_checklist(self, project_digest: str, parsed_request: str,
                                 client: AsyncOpenAI, model: str) -> Dict[str, Any]:
        prompt = PROMPT_CHECKLIST.format(
            project_digest=project_digest,
            parsed_request=parsed_request,
        )
        return await self._llm_json(prompt, client, model, self.config.temperature_generation)

    async def generate_walkthrough(self, project_digest: str, parsed_request: str,
                                   checklist: str, client: AsyncOpenAI, model: str) -> Dict[str, Any]:
        prompt = PROMPT_WALKTHROUGH.format(
            project_digest=project_digest,
            parsed_request=parsed_request,
            checklist=checklist,
        )
        return await self._llm_json(prompt, client, model, self.config.temperature_generation)

    async def generate_plan(self, project_digest: str, parsed_request: str,
                            checklist: str, walkthrough: str,
                            client: AsyncOpenAI, model: str) -> Dict[str, Any]:
        prompt = PROMPT_IMPLEMENTATION_PLAN.format(
            project_digest=project_digest,
            parsed_request=parsed_request,
            checklist=checklist,
            walkthrough=walkthrough,
        )
        return await self._llm_json(prompt, client, model, self.config.temperature_generation)

    async def parse_review_comments(self, comments: str, checklist: str,
                                    walkthrough: str, plan: str,
                                    client: AsyncOpenAI, model: str) -> Dict[str, Any]:
        prompt = PROMPT_REVIEW_COMMENTS.format(
            client_comments=comments,
            checklist=checklist,
            walkthrough=walkthrough,
            implementation_plan=plan,
        )
        return await self._llm_json(prompt, client, model, self.config.temperature_analysis)

    def validate_documents(self, checklist: Dict, walkthrough: Dict, plan: Dict) -> Tuple[bool, List[str]]:
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

    def save_to_project(self, docs_dir: str, docs: Dict[str, Any]) -> str:
        os.makedirs(docs_dir, exist_ok=True)

        if "parsed_request" in docs:
            save_json(os.path.join(docs_dir, "parsed_request.json"), docs["parsed_request"])

        if "digest" in docs:
            save_json(os.path.join(docs_dir, "project_digest.json"), docs["digest"])

        if "checklist" in docs:
            self._save_checklist_md(docs_dir, docs["checklist"])
            save_json(os.path.join(docs_dir, "checklist.json"), docs["checklist"])

        if "walkthrough" in docs:
            self._save_walkthrough_md(docs_dir, docs["walkthrough"])
            save_json(os.path.join(docs_dir, "walkthrough.json"), docs["walkthrough"])

        if "plan" in docs:
            self._save_plan_md(docs_dir, docs["plan"])
            save_json(os.path.join(docs_dir, "implementation_plan.json"), docs["plan"])

        review_path = os.path.join(docs_dir, "review_comments.md")
        if not os.path.exists(review_path):
            with open(review_path, "w", encoding="utf-8") as f:
                f.write("# Обратная связь и комментарии\n\n")
                f.write("Вы можете оставлять комментарии прямо в markdown документах (`checklist.md`, `walkthrough.md`, `implementation_plan.md`) с помощью следующего формата:\n\n")
                f.write("```markdown\n<!-- COMMENT: ваш текст комментария -->\n```\n\n")
                f.write("Размещайте этот тег сразу **после строки или блока**, к которому относится комментарий.\n")
                f.write("Агент соберет эти комментарии, проанализирует их, и обновит документы.\n")

        log.info(f"docs saved to {docs_dir}")
        return docs_dir

    def extract_inline_comments(self, docs_dir: str) -> str:
        if not os.path.exists(docs_dir):
            return ""

        extracted = []
        md_files = ["checklist.md", "walkthrough.md", "implementation_plan.md"]
        
        for md_file in md_files:
            file_path = os.path.join(docs_dir, md_file)
            if not os.path.exists(file_path):
                continue
                
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            new_lines = []
            file_comments = []
            
            for i, line in enumerate(lines):
                if "<!-- COMMENT:" in line:
                    comment_text = line.split("<!-- COMMENT:")[1].split("-->")[0].strip()
                    context = lines[i-1].strip() if i > 0 else "Начало документа"
                    file_comments.append(f"В файле {md_file}, к строке '{context}':\n> {comment_text}")
                else:
                    new_lines.append(line)
                    
            if file_comments:
                extracted.extend(file_comments)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                    
        return "\n\n".join(extracted)

    def save_execution_log(self, docs_dir: str, log_entries: List[Dict]) -> str:
        os.makedirs(docs_dir, exist_ok=True)
        log_path = os.path.join(docs_dir, "execution_log.md")

        lines = ["# Лог выполнения\n\n"]
        for entry in log_entries:
            status = entry.get("status", "unknown")
            step = entry.get("step_number", "?")
            desc = entry.get("description", "")
            elapsed = entry.get("elapsed", 0)
            error = entry.get("error", "")
            marker = "x" if status == "completed" else " "
            lines.append(f"- [{marker}] Шаг {step}: {desc} [{status}] ({elapsed:.1f}s)")
            if error:
                lines.append(f"  - Ошибка: {error}")
            lines.append("")

        stats = {"completed": 0, "failed": 0, "blocked": 0, "skipped": 0}
        for e in log_entries:
            s = e.get("status", "unknown")
            if s in stats:
                stats[s] += 1

        lines.append("## Статистика\n")
        for k, v in stats.items():
            lines.append(f"- {k}: {v}")

        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        log.info(f"execution log saved to {log_path}")
        return log_path

    def mark_step_completed(self, docs_dir: str, checklist_id: str, step_number: str):
        if not os.path.exists(docs_dir):
            return

        # Обновление checklist.md
        checklist_path = os.path.join(docs_dir, "checklist.md")
        if os.path.exists(checklist_path):
            with open(checklist_path, "r", encoding="utf-8") as f:
                cl_lines = f.readlines()
            for i, line in enumerate(cl_lines):
                if line.startswith("- [ ]") and f"**{checklist_id}**" in line:
                    cl_lines[i] = line.replace("- [ ]", "- [x]", 1)
            with open(checklist_path, "w", encoding="utf-8") as f:
                f.writelines(cl_lines)

        # Обновление implementation_plan.md
        plan_path = os.path.join(docs_dir, "implementation_plan.md")
        if os.path.exists(plan_path):
            with open(plan_path, "r", encoding="utf-8") as f:
                pl_lines = f.readlines()
            for i, line in enumerate(pl_lines):
                if line.startswith("### Шаг") and f"[{checklist_id}]" in line and str(step_number) in line:
                    pl_lines[i] = line.replace("### Шаг", "### [x] Шаг", 1)
            with open(plan_path, "w", encoding="utf-8") as f:
                f.writelines(pl_lines)
                
        # Также обновить JSON-файлы, чтобы LLM знала статус при следующей итерации
        cl_json_path = os.path.join(docs_dir, "checklist.json")
        if os.path.exists(cl_json_path):
            try:
                cl_data = load_json(cl_json_path)
                for task in cl_data.get("checklist", []):
                    if task.get("id") == checklist_id:
                        task["status"] = "completed"
                save_json(cl_json_path, cl_data)
            except Exception as e:
                log.error(f"Failed to update checklist.json: {e}")

    def _save_checklist_md(self, docs_dir: str, checklist: Dict):
        path = os.path.join(docs_dir, "checklist.md")
        lines = ["# Чеклист задач\n\n"]
        current_cat = None
        for task in checklist.get("checklist", []):
            cat = task.get("category", "OTHER")
            if cat != current_cat:
                current_cat = cat
                lines.append(f"\n## {cat}\n")
            tid = task.get("id", "???")
            title = task.get("title", "")
            desc = task.get("description", "")
            deps = task.get("depends_on", [])
            criteria = task.get("acceptance_criteria", "")
            status = task.get("status", "pending")
            marker = "x" if status == "completed" else " "
            lines.append(f"- [{marker}] **{tid}** {title}")
            lines.append(f"  - {desc}")
            if deps:
                lines.append(f"  - Зависит от: {', '.join(deps)}")
            lines.append(f"  - Критерий: {criteria}")
            lines.append("")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _save_walkthrough_md(self, docs_dir: str, walkthrough: Dict):
        path = os.path.join(docs_dir, "walkthrough.md")
        lines = [f"# {walkthrough.get('title', 'Walkthrough')}\n\n"]
        summary = walkthrough.get("summary", "")
        if summary:
            lines.append(f"{summary}\n\n")
        for block in walkthrough.get("blocks", []):
            lines.append(f"## {block.get('name', '')}\n")
            lines.append(f"Цель: {block.get('purpose', '')}\n")
            lines.append("Файлы:\n")
            for fi in block.get("files", []):
                lines.append(f"- `{fi.get('path', '')}` [{fi.get('operation', '')}] - {fi.get('changes_description', '')}")
            lines.append("")
            cids = block.get("checklist_ids", [])
            if cids:
                lines.append(f"Задачи: {', '.join(cids)}\n")
            risks = block.get("risks", [])
            if risks:
                lines.append("Риски:")
                for r in risks:
                    lines.append(f"- {r}")
            lines.append("\n---\n")
        verif = walkthrough.get("verification", {})
        if verif:
            lines.append("\n## Верификация\n")
            for ac in verif.get("automated_checks", []):
                lines.append(f"- [auto] {ac}")
            for mc in verif.get("manual_checks", []):
                lines.append(f"- [manual] {mc}")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _save_plan_md(self, docs_dir: str, plan: Dict):
        path = os.path.join(docs_dir, "implementation_plan.md")
        lines = ["# План имплементации\n\n"]
        prereqs = plan.get("prerequisites", [])
        if prereqs:
            lines.append("## Предпосылки\n")
            for p in prereqs:
                lines.append(f"- {p}")
            lines.append("")
        lines.append("## Шаги\n")
        for step in plan.get("steps", []):
            num = step.get("step_number", "?")
            cid = step.get("checklist_id", "")
            atype = step.get("action_type", "")
            target = step.get("target", "")
            desc = step.get("description", "")
            lines.append(f"### Шаг {num} [{cid}]")
            lines.append(f"- Действие: {atype}")
            lines.append(f"- Цель: {target}")
            lines.append(f"- Описание: {desc}")
            details = step.get("details", "")
            if details:
                lines.append(f"- Детали: {details}")
            rollback = step.get("rollback", "")
            if rollback:
                lines.append(f"- Откат: {rollback}")
            lines.append("")
        review = plan.get("review_required", [])
        if review:
            lines.append("## Требует ревью\n")
            for r in review:
                lines.append(f"- **{r.get('item', '')}**: {r.get('description', '')}")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    async def _llm_json(self, prompt: str, client: AsyncOpenAI, model: str,
                        temperature: float) -> Dict[str, Any]:
        for attempt in range(3):
            try:
                r = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                )
                raw = r.choices[0].message.content or ""
                js = find_balanced_json(raw)
                if js:
                    return json.loads(js)
                log.warning(f"llm returned no json (attempt {attempt+1}): {raw[:200]}")
                prompt = prompt + f"\n\nПопытка {attempt+2}. Предыдущий ответ не содержал валидный JSON. Верни строго JSON."
            except Exception as e:
                log.error(f"llm_json error (attempt {attempt+1}): {e}")
        return {}
