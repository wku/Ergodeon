import os
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Awaitable
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from openrouter_agent.tools.registry import ToolRegistry
from openrouter_agent.agent.intent import IntentClassifier
from openrouter_agent.agent.memory import EpisodeMemory
from openrouter_agent.agent.planner import Planner
from openrouter_agent.agent.scanner import ProjectScanner
from openrouter_agent.agent.doc_generator import DocumentGenerator
from openrouter_agent.agent.sandbox import Sandbox
from openrouter_agent.agent.config import PipelineConfig
from openrouter_agent.agent.prompts import PROMPT_EXECUTE_STEP
from openrouter_agent.utils import find_balanced_json, load_yaml

log = logging.getLogger(__name__)

DANGEROUS_TOOLS = {
    "write_file", "delete_file", "edit_file", "edit_file_by_lines",
    "move_file", "execute_command", "multi_edit_file",
}

PATH_ARGS = {"path", "directory", "source", "destination", "cwd"}


def get_latest_stage_version(project_dir: str) -> tuple[int, int]:
    base = os.path.join(project_dir, "флоу-разработки")
    if not os.path.exists(base):
        return 0, 0
    stages = [d for d in os.listdir(base) if d.startswith("стейдж-") and os.path.isdir(os.path.join(base, d))]
    if not stages:
        return 0, 0
    max_stage = max([int(s.split("-")[1]) for s in stages if s.split("-")[1].isdigit()], default=0)
    if max_stage == 0:
        return 0, 0
    stage_dir = os.path.join(base, f"стейдж-{max_stage}")
    versions = [d for d in os.listdir(stage_dir) if d.startswith("версия-") and os.path.isdir(os.path.join(stage_dir, d))]
    if not versions:
        return max_stage, 0
    max_version = max([int(v.split("-")[1]) for v in versions if v.split("-")[1].isdigit()], default=0)
    return max_stage, max_version


def _docs_dir_path(project_dir: str, stage: int, version: int) -> str:
    return os.path.join(project_dir, "флоу-разработки", f"стейдж-{stage}", f"версия-{version}")


def _resolve_and_guard(raw_path: str, project_dir: str) -> str:
    """
    Разрешает путь и проверяет что он внутри project_dir.
    Выбрасывает ValueError если нет.
    """
    project_root = Path(project_dir).resolve()
    if not os.path.isabs(raw_path):
        resolved = (project_root / raw_path).resolve()
    else:
        resolved = Path(raw_path).resolve()
    try:
        resolved.relative_to(project_root)
    except ValueError:
        raise ValueError(
            f"Доступ запрещён: путь '{raw_path}' выходит за пределы директории проекта '{project_root}'. "
            f"Все операции с файлами разрешены только внутри {project_root}."
        )
    return str(resolved)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Agent:
    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o",
        system_prompt: str | None = None,
        confirmation_callback: Callable[[str, Any], Awaitable[bool]] | None = None,
        memory_path: str = "memory/episodes.json",
        pipeline_config: PipelineConfig = None,
    ):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.model = model
        self.api_key = api_key
        self.tools_registry = ToolRegistry()
        self.history: List[ChatCompletionMessageParam] = []
        self.system_prompt = system_prompt or (
            "You are a helpful AI coding assistant. "
            "You can read and write files, execute commands, and more."
        )
        self.confirmation_callback = confirmation_callback
        self.active_project_dir: str | None = None

        self.intent_classifier = IntentClassifier()
        self.memory = EpisodeMemory(memory_path)
        self.planner = Planner()
        self.scanner = ProjectScanner()
        self.doc_generator = DocumentGenerator()
        self.pipeline_config = pipeline_config or PipelineConfig()

        log.info(f"agent initialized, model={model}, memory={memory_path}")

    # ------------------------------------------------------------------ public API

    async def detect_pipeline_request(self, user_input: str) -> bool:
        intent = await self.intent_classifier.classify_with_llm(user_input, self.client, self.model)
        return intent == "pipeline"

    async def create_project_dir(self, goal: str) -> str:
        prompt = (
            "You are a strict JSON responder. Based on the user's project request, "
            "generate a short, snake_case or kebab-case directory name for the project.\n"
            'Return ONLY JSON like: {"dir_name": "my_new_project"}\n'
            f"Request: {goal}"
        )
        try:
            r = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            raw = r.choices[0].message.content or ""
            js = find_balanced_json(raw)
            name = json.loads(js).get("dir_name", "new_project") if js else "new_project"
        except Exception as e:
            log.warning(f"error generating project name: {e}")
            name = "new_project"

        name = f"{name}_{int(time.time())}"
        base_dir = os.path.abspath(self.pipeline_config.projects_dir)
        project_dir = os.path.join(base_dir, name)
        os.makedirs(project_dir, exist_ok=True)
        return project_dir

    async def chat(self, user_input: str) -> str:
        intent = self.intent_classifier.classify(user_input)
        log.info(f"intent: {intent}, input: {user_input[:100]}")

        similar = self.memory.find_similar(user_input)
        if similar:
            log.info(f"similar episode found: {similar.get('goal', '')[:80]}")

        if self.active_project_dir and not any(
            "active_project_dir" in str(m.get("content", "")) for m in self.history[-3:]
        ):
            self.history.append({
                "role": "system",
                "content": (
                    f"Текущий активный проект: {self.active_project_dir}\n"
                    f"ВСЕ файловые операции выполнять ТОЛЬКО внутри этой директории. "
                    f"Запрещено создавать или изменять файлы вне {self.active_project_dir}."
                ),
            })

        self.history.append({"role": "user", "content": user_input})
        start_time = time.time()
        response = await self._step(project_dir=self.active_project_dir)
        elapsed = time.time() - start_time

        self.memory.add({
            "goal": user_input, "intent": intent,
            "response_preview": response[:200] if response else "",
            "elapsed": round(elapsed, 2), "timestamp": time.time(),
        })
        log.info(f"chat completed in {elapsed:.1f}s")
        return response

    # ------------------------------------------------------------------ resume_pipeline

    async def resume_pipeline(
        self,
        project_dir: str,
        stage: int | None = None,
        version: int | None = None,
        review_callback: Callable[[str], Awaitable[str]] | None = None,
    ) -> Dict[str, Any]:
        """
        Продолжает выполнение прерванного пайплайна.

        Алгоритм:
        1. Если stage/version не указаны - берёт последний стейдж/версию.
        2. Читает implementation_plan.yaml (или .json legacy).
        3. Читает execution_log.yaml - строит множество completed_ids.
        4. Запускает цикл выполнения только для незавершённых шагов.
        5. Сохраняет обновлённый лог.
        """
        self.active_project_dir = os.path.abspath(project_dir)

        if stage is None or version is None:
            max_stage, max_version = get_latest_stage_version(project_dir)
            if max_stage == 0:
                return {"status": "error", "error": "Не найдено ни одного стейджа. Запустите run_pipeline сначала."}
            stage = stage or max_stage
            version = version or max_version

        docs_dir = _docs_dir_path(project_dir, stage, version)
        log.info(f"resume_pipeline: project={project_dir}, stage={stage}, version={version}")

        # Загружаем план
        plan = self.doc_generator.load_plan(docs_dir)
        if not plan:
            return {
                "status": "error",
                "error": f"implementation_plan не найден в {docs_dir}. Невозможно продолжить.",
            }

        # Загружаем чеклист для зависимостей
        checklist = self.doc_generator.load_checklist(docs_dir) or {}

        # Строим множество выполненных шагов из лога
        existing_log = self.doc_generator.load_execution_log(docs_dir)
        completed_ids: set[str] = set()
        previous_entries: List[Dict] = []

        if existing_log:
            for entry in existing_log.get("steps", []):
                if entry.get("status") == "completed":
                    completed_ids.add(str(entry.get("checklist_id", "")))
            previous_entries = existing_log.get("steps", [])
            log.info(f"resume: найдено {len(completed_ids)} выполненных шагов: {completed_ids}")
        else:
            log.info("resume: лог не найден, выполняем все шаги")

        steps = plan.get("steps", [])
        pending_steps = [
            s for s in steps
            if str(s.get("checklist_id", "")) not in completed_ids
        ]

        if not pending_steps:
            log.info("resume: все шаги уже выполнены")
            return {
                "status": "success",
                "message": "Все шаги уже выполнены.",
                "stages": {"execution": previous_entries},
            }

        log.info(f"resume: {len(pending_steps)} шагов к выполнению из {len(steps)} всего")

        # Формируем digest строку для промтов
        from openrouter_agent.utils import load_yaml as _load_yaml
        digest_data = _load_yaml(os.path.join(docs_dir, "project_digest.yaml")) or {}
        digest_str = json.dumps(digest_data, ensure_ascii=False)

        result = {
            "status": "started",
            "stage": stage,
            "version": version,
            "stages": {},
        }

        # Метаданные для лога
        log_meta = {
            "project_dir": project_dir,
            "stage": stage,
            "version": version,
            "resumed_at": _now_iso(),
            "status": "running",
            "total_steps": len(steps),
            "skipped_completed": len(completed_ids),
        }

        execution_log = list(previous_entries)  # сохраняем историю предыдущего запуска
        failed_ids: set[str] = set()

        for step in pending_steps:
            step_num = step.get("step_number", "?")
            cid = str(step.get("checklist_id", ""))
            desc = step.get("description", "")

            # Проверяем зависимости
            deps: set[str] = set()
            for task in checklist.get("checklist", []):
                if str(task.get("id")) == cid:
                    deps = set(str(d) for d in task.get("depends_on", []))
                    break

            if deps & failed_ids:
                log.warning(f"step {step_num} blocked: dependency failed")
                execution_log.append({
                    "step_number": step_num, "checklist_id": cid,
                    "description": desc, "status": "blocked",
                    "elapsed": 0, "error": "dependency failed",
                })
                self.doc_generator.save_execution_log(docs_dir, execution_log, {**log_meta, "status": "running"})
                continue

            log.info(f"resume: выполняю шаг {step_num}: {desc}")
            start = time.time()
            status = "completed"
            error = ""

            for attempt in range(self.pipeline_config.max_retry_per_step):
                try:
                    step_prompt = json.dumps(step, ensure_ascii=False)
                    prompt = PROMPT_EXECUTE_STEP.format(
                        step=step_prompt,
                        project_digest=digest_str,
                        current_file_content="Определи сам в процессе",
                        previous_steps_log=json.dumps(execution_log[-10:], ensure_ascii=False),
                    )
                    system_instruction = (
                        f"You are executing a step in the implementation plan.\n"
                        f"CRITICAL: The absolute root directory for this project is {project_dir}\n"
                        f"ALL file paths MUST point inside {project_dir}. "
                        f"It is STRICTLY FORBIDDEN to create or modify files outside {project_dir}."
                    )
                    self.history.append({"role": "system", "content": system_instruction})
                    self.history.append({"role": "user", "content": prompt})
                    await self._step(project_dir=project_dir)
                    status = "completed"
                    completed_ids.add(cid)
                    error = ""
                    self.doc_generator.mark_step_completed(docs_dir, cid, step_num)
                    break
                except Exception as e:
                    log.error(f"step {step_num} attempt {attempt + 1} error: {e}")
                    error = str(e)
                    status = "failed"

            if status == "failed":
                failed_ids.add(cid)

            elapsed = time.time() - start
            execution_log.append({
                "step_number": step_num, "checklist_id": cid,
                "description": desc, "status": status,
                "elapsed": round(elapsed, 2), "error": error,
            })

            # Сохраняем лог после каждого шага чтобы прерывание не теряло прогресс
            self.doc_generator.save_execution_log(
                docs_dir, execution_log,
                {**log_meta, "status": "running"},
            )

        # Финальный статус
        total = len(steps)
        completed = sum(1 for e in execution_log if e["status"] == "completed")
        failed = sum(1 for e in execution_log if e["status"] == "failed")
        blocked = sum(1 for e in execution_log if e["status"] == "blocked")
        failed_pct = (failed / max(total, 1)) * 100

        if failed_pct > self.pipeline_config.failed_tasks_threshold_percent:
            result["status"] = "critical_failure"
        elif failed > 0:
            result["status"] = "partial_success"
        else:
            result["status"] = "success"

        log_meta["status"] = result["status"]
        log_meta["finished_at"] = _now_iso()
        self.doc_generator.save_execution_log(docs_dir, execution_log, log_meta)

        result["stages"]["execution"] = execution_log
        result["stages"]["verification"] = {
            "total": total, "completed": completed,
            "failed": failed, "blocked": blocked,
            "failed_percent": round(failed_pct, 1),
        }

        self.memory.add({
            "goal": f"resume stage={stage} version={version}",
            "intent": "resume",
            "project": project_dir,
            "status": result["status"],
            "stats": result["stages"]["verification"],
            "timestamp": time.time(),
        })

        log.info(f"resume_pipeline finished: {result['status']}")
        return result

    # ------------------------------------------------------------------ run_pipeline

    async def run_pipeline(
        self,
        project_dir: str,
        goal: str,
        review_callback: Callable[[str], Awaitable[str]] | None = None,
    ) -> Dict[str, Any]:
        log.info(f"pipeline started: project={project_dir}, goal={goal[:100]}")
        self.active_project_dir = os.path.abspath(project_dir)
        result = {"status": "started", "stages": {}}

        max_stage, max_version = get_latest_stage_version(project_dir)
        old_context = ""

        if max_stage > 0 and max_version > 0:
            prev_docs_dir = _docs_dir_path(project_dir, max_stage, max_version)

            parsed_req = self.doc_generator.load_plan(prev_docs_dir)  # reuse loader
            # Загружаем parsed_request отдельно
            from openrouter_agent.utils import load_yaml as _ly
            old_req = _ly(os.path.join(prev_docs_dir, "parsed_request.yaml"))
            if old_req:
                old_context += f"ПРЕДЫДУЩИЙ ЗАПРОС:\n{json.dumps(old_req, ensure_ascii=False)}\n\n"
            old_cl = self.doc_generator.load_checklist(prev_docs_dir)
            if old_cl:
                old_context += (
                    f"ТЕКУЩИЙ ЧЕКЛИСТ:\n{json.dumps(old_cl, ensure_ascii=False)}\n\n"
                    "ВАЖНО: Добавь новые задачи в этот чеклист. Старые задачи сохрани как есть (если они не отменены)!"
                )

            current_stage = max_stage + 1
        else:
            current_stage = 1

        current_version = 1
        docs_dir = _docs_dir_path(project_dir, current_stage, current_version)

        # Стадия 1
        log.info("stage 1: parsing request")
        goal_with_ctx = f"Новый запрос: {goal}\n\n---\nИстория проекта:\n{old_context}" if old_context else goal
        parsed = await self.doc_generator.parse_request(goal_with_ctx, "", self.client, self.model)
        result["stages"]["parse_request"] = parsed
        if parsed.get("clarification_needed"):
            result["status"] = "needs_clarification"
            result["questions"] = parsed["clarification_needed"]
            return result

        # Стадия 2-3
        log.info("stage 2-3: scanning project and generating digest")
        files = self.scanner.scan(project_dir)
        prioritized = self.scanner.prioritize(files, goal)
        file_tree = self.scanner.get_file_tree(files)
        file_contents = self.scanner.read_files(prioritized)
        contents_str = "\n\n".join(f"--- {k} ---\n{v}" for k, v in file_contents.items())

        digest = await self.doc_generator.generate_digest(
            file_tree, contents_str, json.dumps(parsed, ensure_ascii=False),
            self.client, self.model,
        )
        result["stages"]["digest"] = digest

        # Стадия 4
        log.info("stage 4: generating documents")
        parsed_str = json.dumps(parsed, ensure_ascii=False)
        digest_str = json.dumps(digest, ensure_ascii=False)

        checklist = await self.doc_generator.generate_checklist(digest_str, parsed_str, self.client, self.model)
        walkthrough = await self.doc_generator.generate_walkthrough(
            digest_str, parsed_str, json.dumps(checklist, ensure_ascii=False), self.client, self.model,
        )
        plan = await self.doc_generator.generate_plan(
            digest_str, parsed_str,
            json.dumps(checklist, ensure_ascii=False),
            json.dumps(walkthrough, ensure_ascii=False),
            self.client, self.model,
        )

        valid, issues = self.doc_generator.validate_documents(checklist, walkthrough, plan)
        if not valid:
            log.warning(f"document validation issues: {issues}")

        docs = {"parsed_request": parsed, "digest": digest,
                "checklist": checklist, "walkthrough": walkthrough, "plan": plan}
        self.doc_generator.save_to_project(docs_dir, docs)
        result["stages"]["documents"] = {"path": docs_dir, "valid": valid, "issues": issues}

        # Стадия 5 - ревью
        if review_callback:
            log.info("stage 5: requesting review")
            review_iterations = 0
            while review_iterations < self.pipeline_config.max_review_iterations:
                review_iterations += 1
                comments_cli = await review_callback(
                    f"Документы сгенерированы в:\n{docs_dir}\n\n"
                    f"Откройте checklist.md, walkthrough.md, implementation_plan.md.\n"
                    f"Оставьте <!-- COMMENT: текст --> прямо в файлах или напишите комментарии здесь.\n"
                    f"Пустой ввод или 'ok' - продолжить выполнение."
                )
                inline_comments = self.doc_generator.extract_inline_comments(docs_dir)
                all_comments = []
                if comments_cli and comments_cli.strip().lower() not in ("ok", "approved", "да", ""):
                    all_comments.append(f"Комментарии из чата:\n{comments_cli}")
                if inline_comments:
                    all_comments.append(f"Inline комментарии:\n{inline_comments}")
                comments = "\n\n".join(all_comments)

                if not comments:
                    log.info("review: approved")
                    break

                log.info("review: processing comments")
                review_result = await self.doc_generator.parse_review_comments(
                    comments,
                    json.dumps(checklist, ensure_ascii=False),
                    json.dumps(walkthrough, ensure_ascii=False),
                    json.dumps(plan, ensure_ascii=False),
                    self.client, self.model,
                )
                overall = review_result.get("overall_status", "needs_revision")
                if overall == "approved":
                    break
                if overall == "rejected":
                    result["status"] = "rejected"
                    return result

                to_regen = review_result.get("documents_to_regenerate", [])
                if to_regen:
                    current_version += 1
                    docs_dir = _docs_dir_path(project_dir, current_stage, current_version)
                    if "checklist" in to_regen:
                        checklist = await self.doc_generator.generate_checklist(
                            digest_str, parsed_str + f"\nКомментарии: {comments}", self.client, self.model,
                        )
                        walkthrough = await self.doc_generator.generate_walkthrough(
                            digest_str, parsed_str, json.dumps(checklist, ensure_ascii=False),
                            self.client, self.model,
                        )
                        plan = await self.doc_generator.generate_plan(
                            digest_str, parsed_str,
                            json.dumps(checklist, ensure_ascii=False),
                            json.dumps(walkthrough, ensure_ascii=False),
                            self.client, self.model,
                        )
                    elif "walkthrough" in to_regen:
                        walkthrough = await self.doc_generator.generate_walkthrough(
                            digest_str, parsed_str + f"\nКомментарии: {comments}",
                            json.dumps(checklist, ensure_ascii=False), self.client, self.model,
                        )
                        plan = await self.doc_generator.generate_plan(
                            digest_str, parsed_str,
                            json.dumps(checklist, ensure_ascii=False),
                            json.dumps(walkthrough, ensure_ascii=False),
                            self.client, self.model,
                        )
                    elif "implementation_plan" in to_regen:
                        plan = await self.doc_generator.generate_plan(
                            digest_str, parsed_str + f"\nКомментарии: {comments}",
                            json.dumps(checklist, ensure_ascii=False),
                            json.dumps(walkthrough, ensure_ascii=False),
                            self.client, self.model,
                        )
                    docs.update({"checklist": checklist, "walkthrough": walkthrough, "plan": plan})
                    self.doc_generator.save_to_project(docs_dir, docs)

        # Стадия 6 - имплементация
        log.info("stage 6: implementation")

        log_meta = {
            "project_dir": project_dir,
            "stage": current_stage,
            "version": current_version,
            "started_at": _now_iso(),
            "status": "running",
        }

        execution_log: List[Dict] = []
        steps = plan.get("steps", [])
        completed_ids: set[str] = set()
        failed_ids: set[str] = set()

        for step in steps:
            step_num = step.get("step_number", "?")
            cid = str(step.get("checklist_id", ""))
            desc = step.get("description", "")

            deps: set[str] = set()
            for task in checklist.get("checklist", []):
                if str(task.get("id")) == cid:
                    deps = set(str(d) for d in task.get("depends_on", []))
                    break

            if deps & failed_ids:
                log.warning(f"step {step_num} blocked: dependency failed")
                execution_log.append({
                    "step_number": step_num, "checklist_id": cid,
                    "description": desc, "status": "blocked",
                    "elapsed": 0, "error": "dependency failed",
                })
                # Сохраняем прогресс немедленно
                self.doc_generator.save_execution_log(
                    docs_dir, execution_log, {**log_meta, "status": "running"},
                )
                continue

            log.info(f"Начинаю выполнение шага {step_num}: {desc}")
            start = time.time()
            status = "completed"
            error = ""

            for attempt in range(self.pipeline_config.max_retry_per_step):
                try:
                    step_prompt = json.dumps(step, ensure_ascii=False)
                    prompt = PROMPT_EXECUTE_STEP.format(
                        step=step_prompt,
                        project_digest=digest_str,
                        current_file_content="Определи сам в процессе",
                        previous_steps_log=json.dumps(execution_log[-10:], ensure_ascii=False),
                    )
                    system_instruction = (
                        f"You are executing a step in the implementation plan.\n"
                        f"CRITICAL: The absolute root directory for this project is {project_dir}\n"
                        f"ALL file paths in your tool calls MUST point inside {project_dir}. "
                        f"It is STRICTLY FORBIDDEN to create or modify files outside {project_dir}. "
                        f"Use relative paths only."
                    )
                    self.history.append({"role": "system", "content": system_instruction})
                    self.history.append({"role": "user", "content": prompt})
                    await self._step(project_dir=project_dir)
                    status = "completed"
                    completed_ids.add(cid)
                    error = ""
                    self.doc_generator.mark_step_completed(docs_dir, cid, step_num)
                    break
                except Exception as e:
                    log.error(f"step {step_num} attempt {attempt + 1} error: {e}")
                    error = str(e)
                    status = "failed"

            if status == "failed":
                failed_ids.add(cid)

            elapsed = time.time() - start
            execution_log.append({
                "step_number": step_num, "checklist_id": cid,
                "description": desc, "status": status,
                "elapsed": round(elapsed, 2), "error": error,
            })

            # Сохраняем лог после каждого шага
            self.doc_generator.save_execution_log(
                docs_dir, execution_log,
                {**log_meta, "status": "running"},
            )

        result["stages"]["execution"] = execution_log

        # Стадия 7
        log.info("stage 7: final verification")
        total = len(steps)
        completed = sum(1 for e in execution_log if e["status"] == "completed")
        failed = sum(1 for e in execution_log if e["status"] == "failed")
        blocked = sum(1 for e in execution_log if e["status"] == "blocked")
        failed_pct = (failed / max(total, 1)) * 100

        if failed_pct > self.pipeline_config.failed_tasks_threshold_percent:
            result["status"] = "critical_failure"
            log.error(f"critical failure: {failed_pct:.0f}% tasks failed")
        elif failed > 0:
            result["status"] = "partial_success"
        else:
            result["status"] = "success"

        log_meta["status"] = result["status"]
        log_meta["finished_at"] = _now_iso()
        self.doc_generator.save_execution_log(docs_dir, execution_log, log_meta)

        result["stages"]["verification"] = {
            "total": total, "completed": completed,
            "failed": failed, "blocked": blocked,
            "failed_percent": round(failed_pct, 1),
        }

        self.memory.add({
            "goal": goal, "intent": "pipeline", "project": project_dir,
            "status": result["status"],
            "stats": result["stages"]["verification"],
            "timestamp": time.time(),
        })

        log.info(f"pipeline finished: {result['status']}")
        return result

    # ------------------------------------------------------------------ _step

    async def _step(self, project_dir: str | None = None) -> str:
        messages = [{"role": "system", "content": self.system_prompt}] + self.history
        tools = self._get_openai_tools()

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
        )

        message = response.choices[0].message
        self.history.append(message.model_dump())

        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                arguments_str = tool_call.function.arguments

                try:
                    tool_args = json.loads(arguments_str)

                    if project_dir:
                        for k in list(tool_args.keys()):
                            if k in PATH_ARGS and isinstance(tool_args[k], str):
                                try:
                                    tool_args[k] = _resolve_and_guard(tool_args[k], project_dir)
                                except ValueError as path_err:
                                    log.error(str(path_err))
                                    self.history.append({
                                        "role": "tool",
                                        "tool_call_id": tool_call.id,
                                        "name": tool_name,
                                        "content": f"ERROR: {path_err}",
                                    })
                                    continue

                        if tool_name == "execute_command" and "cwd" not in tool_args:
                            tool_args["cwd"] = project_dir

                    tool = self.tools_registry.get(tool_name)

                    if not tool:
                        result = f"Error: Tool {tool_name} not found"
                    else:
                        log.info(f"Использую инструмент: {tool_name} с аргументами: {tool_args}")
                        if tool_name in DANGEROUS_TOOLS and self.confirmation_callback:
                            confirmed = await self.confirmation_callback(tool_name, tool_args)
                            if not confirmed:
                                result = "Tool execution cancelled by user."
                            else:
                                validated_args = tool.validate_args(tool_args)
                                result = await tool.run(validated_args)
                        else:
                            validated_args = tool.validate_args(tool_args)
                            result = await tool.run(validated_args)

                except json.JSONDecodeError:
                    result = f"Error: Invalid JSON arguments for {tool_name}"
                except Exception as e:
                    log.error(f"tool {tool_name} error: {e}")
                    result = f"Error executing tool {tool_name}: {e}"

                self.history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": str(result),
                })

            return await self._step(project_dir=project_dir)

        return message.content or ""

    def _get_openai_tools(self) -> List[ChatCompletionToolParam]:
        return self.tools_registry.get_openai_schemas()
