"""
UnifiedRouter - единая точка входа для обработки запросов пользователя.

Заменяет все текущие точки входа (chat, pipeline, adopt, resume, analyze).
Один метод handle_request(text) определяет workflow, создаёт stage,
выполняет фазы и возвращает результат.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, Callable, Awaitable, List
from openai import AsyncOpenAI
from openrouter_agent.agent.stage_manager import StageManager, Stage
from openrouter_agent.agent.context_manager import ContextManager
from openrouter_agent.agent.workflow_registry import WorkflowRegistry, WorkflowDef
from openrouter_agent.agent.workflow_classifier import WorkflowClassifier, ClassificationResult
from openrouter_agent.agent.scanner import ProjectScanner
from openrouter_agent.agent.doc_generator import DocumentGenerator
from openrouter_agent.agent.config import PipelineConfig
from openrouter_agent.agent.memory import EpisodeMemory
from openrouter_agent.tools.registry import ToolRegistry
from openrouter_agent.agent.prompts import (
    PROMPT_PARSE_REQUEST, PROMPT_PROJECT_DIGEST, PROMPT_CHECKLIST,
    PROMPT_WALKTHROUGH, PROMPT_IMPLEMENTATION_PLAN, PROMPT_REVIEW_COMMENTS,
    PROMPT_EXECUTE_STEP,
)
from openrouter_agent.utils import find_balanced_json, load_yaml
from pathlib import Path
from datetime import datetime, timezone
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam

log = logging.getLogger(__name__)

DANGEROUS_TOOLS = {
    "write_file", "delete_file", "edit_file", "edit_file_by_lines",
    "move_file", "execute_command", "multi_edit_file",
}
PATH_ARGS = {"path", "directory", "source", "destination", "cwd"}

PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "promt"


def _load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        log.error(f"prompt file not found: {path}")
        return ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _resolve_and_guard(raw_path: str, project_dir: str) -> str:
    project_root = Path(project_dir).resolve()
    resolved = (project_root / raw_path).resolve() if not os.path.isabs(raw_path) else Path(raw_path).resolve()
    try:
        resolved.relative_to(project_root)
    except ValueError:
        raise ValueError(f"Путь '{raw_path}' выходит за пределы проекта '{project_root}'")
    return str(resolved)


class RequestResult:
    def __init__(self, workflow: str, status: str, message: str = "",
                 stage_num: int = 0, data: Dict[str, Any] = None):
        self.workflow = workflow
        self.status = status
        self.message = message
        self.stage_num = stage_num
        self.data = data or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow": self.workflow, "status": self.status,
            "message": self.message, "stage_num": self.stage_num,
            "data": self.data,
        }


class ProgressCallback:
    """Интерфейс для отправки прогресса (CLI spinner / WebSocket events)."""

    async def on_phase_start(self, phase_name: str, description: str): pass
    async def on_step_start(self, step_num: Any, total: int, description: str): pass
    async def on_step_done(self, step_num: Any, status: str): pass
    async def on_message(self, text: str, msg_type: str = "system"): pass
    async def on_review_request(self, msg: str) -> str: return "ok"
    async def on_done(self, status: str): pass


class UnifiedRouter:
    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o",
        confirmation_callback: Callable[[str, Any], Awaitable[bool]] = None,
        pipeline_config: PipelineConfig = None,
        memory_path: str = "memory/episodes.json",
        progress: ProgressCallback = None,
    ):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.model = model
        self.api_key = api_key
        self.tools_registry = ToolRegistry()
        self.history: List[ChatCompletionMessageParam] = []
        self.confirmation_callback = confirmation_callback
        self.config = pipeline_config or PipelineConfig()
        self.memory = EpisodeMemory(memory_path)
        self.scanner = ProjectScanner(self.config)
        self.doc_generator = DocumentGenerator(self.config)
        self.classifier = WorkflowClassifier()
        self.workflow_registry = WorkflowRegistry()
        self.progress = progress or ProgressCallback()

        self.active_project_dir: Optional[str] = None

        system_base = _load_prompt("system_base")
        self.system_prompt = (
            "You are a helpful AI coding assistant. "
            "You can read and write files, execute commands, and more.\n\n"
            f"{system_base}"
        )
        log.info(f"unified router initialized, model={model}")

    async def handle_request(self, text: str) -> RequestResult:
        text = text.strip()
        if not text:
            return RequestResult("chat", "completed", "Пустой запрос")

        # 1. Быстрая эвристика
        heuristic = self.classifier.classify_heuristic(text)

        if heuristic and heuristic.workflow == "reset":
            self.active_project_dir = None
            self.history.clear()
            return RequestResult("reset", "completed", "Контекст сброшен")

        if heuristic and heuristic.workflow == "resume":
            return await self._handle_resume(text)

        if heuristic and heuristic.workflow == "serve_project":
            path = self.classifier.extract_path(text)
            if path and os.path.isdir(path):
                self.active_project_dir = path
                return RequestResult("serve_project", "completed",
                                     f"Активный проект: {path}")
            return RequestResult("serve_project", "failed", "Директория не найдена")

        # 2. Загрузить контекст
        project_context = ""
        if self.active_project_dir:
            ctx_mgr = ContextManager(self.active_project_dir)
            project_context = ctx_mgr.get_for_llm()

        # 3. Классификация через LLM
        classification = await self.classifier.classify(
            text, project_context, self.client, self.model
        )
        log.info(f"classified: {classification.workflow} ({classification.confidence})")

        if classification.confidence < 0.7 and classification.workflow != "chat":
            return RequestResult(
                classification.workflow, "needs_clarification",
                f"Уверенность классификации низкая ({classification.confidence:.0%}). "
                f"Предполагаемый тип: {classification.workflow}. Уточните запрос."
            )

        # 4. Chat - без стейджа
        if classification.workflow == "chat":
            return await self._handle_chat(text)

        # 5. Нужен активный проект
        if not self.active_project_dir:
            return RequestResult(
                classification.workflow, "needs_project",
                "Проект не выбран. Укажите путь через adopt или создайте новый."
            )

        # 6. Создать стейдж и выполнить
        return await self._execute_workflow(classification.workflow, text)

    async def _handle_chat(self, text: str) -> RequestResult:
        if self.active_project_dir:
            mode_prompt = _load_prompt("chat_mode")
            if mode_prompt:
                mode_prompt = mode_prompt.format(active_project_dir=self.active_project_dir)
                if not any(mode_prompt in str(m.get("content", "")) for m in self.history[-3:]):
                    self.history.append({"role": "system", "content": mode_prompt})

        self.history.append({"role": "user", "content": text})
        response = await self._step(project_dir=self.active_project_dir)
        self.memory.add({
            "goal": text, "intent": "chat",
            "response_preview": response[:200] if response else "",
            "timestamp": time.time(),
        })
        return RequestResult("chat", "completed", response)

    async def _handle_resume(self, text: str) -> RequestResult:
        path = self.classifier.extract_path(text) or self.active_project_dir
        if not path or not os.path.isdir(path):
            return RequestResult("resume", "failed", "Укажите путь к проекту")

        self.active_project_dir = path
        stage_mgr = StageManager(path)
        stage = stage_mgr.find_resumable_stage()
        if not stage:
            return RequestResult("resume", "failed", "Нет прерванных стейджей для продолжения")

        return await self._resume_stage(stage, stage_mgr)

    async def _execute_workflow(self, workflow_name: str, query: str) -> RequestResult:
        wf_def = self.workflow_registry.get(workflow_name)
        if not wf_def:
            return RequestResult(workflow_name, "failed", f"Воркфлоу {workflow_name} не найден")

        stage_mgr = StageManager(self.active_project_dir)
        ctx_mgr = ContextManager(self.active_project_dir)

        # Читаем контекст предыдущих стейджей
        prev_context = ctx_mgr.get_for_llm()

        stage = stage_mgr.create_stage(workflow_name, query)
        await self.progress.on_phase_start("init", f"Создан стейдж {stage.num} [{workflow_name}]")

        try:
            result_data = await self._run_phases(wf_def, stage, query, prev_context)

            status = result_data.get("status", "completed")
            stage.update_status(status)

            # Обновляем контекст проекта
            ctx_mgr.update_after_stage(
                stage_num=stage.num,
                workflow=workflow_name,
                query=query,
                status=status,
                summary=result_data.get("summary", ""),
                stack=result_data.get("stack"),
                issues=result_data.get("issues"),
            )

            self.memory.add({
                "goal": query, "intent": workflow_name,
                "project": self.active_project_dir,
                "status": status, "stage": stage.num,
                "timestamp": time.time(),
            })

            await self.progress.on_done(status)
            return RequestResult(
                workflow_name, status,
                result_data.get("message", ""),
                stage_num=stage.num,
                data=result_data,
            )

        except Exception as e:
            log.error(f"workflow {workflow_name} error: {e}", exc_info=True)
            stage.update_status("failed")
            await self.progress.on_done("failed")
            return RequestResult(workflow_name, "failed", str(e), stage_num=stage.num)

    async def _run_phases(self, wf_def: WorkflowDef, stage: Stage,
                          query: str, prev_context: str) -> Dict[str, Any]:
        result = {"status": "completed", "phases": {}}
        project_dir = self.active_project_dir

        # Общие данные которые накапливаются между фазами
        parsed_request = {}
        digest = {}
        checklist = {}
        walkthrough = {}
        plan = {}
        scan_data = {"file_tree": "", "file_contents": ""}

        for phase_def in wf_def.phases:
            phase_name = phase_def.name
            await self.progress.on_phase_start(phase_name, phase_def.description)
            log.info(f"phase: {phase_name}")

            if phase_name == "parse_request":
                goal_with_ctx = query
                if prev_context:
                    goal_with_ctx = f"Запрос: {query}\n\nКонтекст проекта:\n{prev_context}"
                parsed_request = await self.doc_generator.parse_request(
                    goal_with_ctx, "", self.client, self.model
                )
                stage.save_artifact("parsed_request.yaml", parsed_request)
                if parsed_request.get("clarification_needed"):
                    result["status"] = "needs_clarification"
                    result["questions"] = parsed_request["clarification_needed"]
                    return result

            elif phase_name == "scan_project":
                if project_dir and os.path.isdir(project_dir):
                    files = self.scanner.scan(project_dir)
                    prioritized = self.scanner.prioritize(files, query)
                    scan_data["file_tree"] = self.scanner.get_file_tree(files)
                    scan_data["file_contents"] = "\n\n".join(
                        f"--- {k} ---\n{v}"
                        for k, v in self.scanner.read_files(prioritized).items()
                    )
                    stage.save_artifact("scan_results.yaml", {
                        "files_count": len(files),
                        "file_tree": scan_data["file_tree"],
                    })

            elif phase_name == "scan_affected":
                if project_dir:
                    files = self.scanner.scan(project_dir)
                    prioritized = self.scanner.prioritize(files, query)[:20]
                    scan_data["file_tree"] = self.scanner.get_file_tree(prioritized)
                    scan_data["file_contents"] = "\n\n".join(
                        f"--- {k} ---\n{v}"
                        for k, v in self.scanner.read_files(prioritized).items()
                    )
                    stage.save_artifact("affected_files.yaml", {
                        "files": [f["path"] for f in prioritized],
                    })

            elif phase_name == "generate_digest":
                parsed_str = json.dumps(parsed_request, ensure_ascii=False)
                digest = await self.doc_generator.generate_digest(
                    scan_data["file_tree"], scan_data["file_contents"],
                    parsed_str, self.client, self.model,
                )
                stage.save_artifact("project_digest.yaml", digest)

            elif phase_name == "generate_checklist":
                digest_str = json.dumps(digest, ensure_ascii=False)
                parsed_str = json.dumps(parsed_request, ensure_ascii=False)
                checklist = await self.doc_generator.generate_checklist(
                    digest_str, parsed_str, self.client, self.model,
                )
                stage.save_artifact("checklist.yaml", checklist)

            elif phase_name == "generate_walkthrough":
                digest_str = json.dumps(digest, ensure_ascii=False)
                parsed_str = json.dumps(parsed_request, ensure_ascii=False)
                checklist_str = json.dumps(checklist, ensure_ascii=False)
                walkthrough = await self.doc_generator.generate_walkthrough(
                    digest_str, parsed_str, checklist_str, self.client, self.model,
                )
                stage.save_artifact("walkthrough.yaml", walkthrough)

            elif phase_name == "generate_plan":
                digest_str = json.dumps(digest or {}, ensure_ascii=False)
                parsed_str = json.dumps(parsed_request, ensure_ascii=False)
                checklist_str = json.dumps(checklist or {}, ensure_ascii=False)
                walkthrough_str = json.dumps(walkthrough or {}, ensure_ascii=False)

                if wf_def.name == "build":
                    plan_data = await self.doc_generator.generate_plan(
                        digest_str, parsed_str, checklist_str,
                        walkthrough_str, self.client, self.model,
                    )
                else:
                    plan_data = await self._generate_light_plan(
                        wf_def.name, query, parsed_request,
                        scan_data, prev_context,
                    )

                plan = plan_data
                if wf_def.name == "build" and checklist and walkthrough and plan:
                    valid, issues = self.doc_generator.validate_documents(checklist, walkthrough, plan)
                    if not valid:
                        log.warning(f"document validation issues: {issues}")
                        result.setdefault("warnings", []).extend(issues)
                stage.save_artifact(f"{wf_def.name}_plan.yaml" if wf_def.name != "build" else "implementation_plan.yaml", plan)
                stage.save_plan(self._to_stage_plan(wf_def, plan))

            elif phase_name == "review":
                if phase_def.skippable:
                    review_response = await self.progress.on_review_request(
                        f"Документы сгенерированы в stage-{stage.num}\n"
                        "Проверьте артефакты. Пустой ввод или 'ok' - продолжить."
                    )
                    inline = self.doc_generator.extract_inline_comments(stage.artifacts_dir)
                    all_comments = []
                    if review_response and review_response.strip().lower() not in ("ok", "approved", "да", ""):
                        all_comments.append(review_response)
                    if inline:
                        all_comments.append(f"Inline: {inline}")
                    combined = "\n".join(all_comments)
                    if combined:
                        await self._handle_review(
                            combined, stage, checklist, walkthrough, plan,
                            digest, parsed_request,
                        )

            elif phase_name == "implement":
                exec_result = await self._execute_implementation(
                    stage, plan, digest, project_dir,
                )
                result["phases"]["implementation"] = exec_result
                if exec_result.get("failed_percent", 0) > self.config.failed_tasks_threshold_percent:
                    result["status"] = "critical_failure"
                elif exec_result.get("failed", 0) > 0:
                    result["status"] = "partial"

            elif phase_name == "verify":
                pass

            elif phase_name == "investigate":
                investigation = await self._run_investigation(query, scan_data, parsed_request)
                stage.save_artifact("investigation.yaml", investigation)
                stage.save_artifact("investigation.md", investigation.get("report", ""))

            elif phase_name in ("analyze", "research", "synthesize", "generate_report"):
                report = await self._run_llm_phase(
                    phase_name, wf_def.name, query, parsed_request,
                    scan_data, prev_context,
                )
                artifact_name = {
                    "analyze": "analysis_report.md",
                    "generate_report": f"{wf_def.name}_report.md",
                    "research": "sources.yaml",
                    "synthesize": "synthesis.md",
                }.get(phase_name, f"{phase_name}.md")
                stage.save_artifact(artifact_name, report)
                if phase_name == "generate_report":
                    result["message"] = report if isinstance(report, str) else json.dumps(report, ensure_ascii=False)

            elif phase_name == "respond":
                pass

            result["phases"][phase_name] = "completed"

        return result

    async def _generate_light_plan(self, workflow: str, query: str,
                                   parsed_request: Dict,
                                   scan_data: Dict, prev_context: str) -> Dict:
        prompt = (
            f"Создай короткий план для задачи типа '{workflow}'.\n\n"
            f"Запрос: {query}\n"
            f"Разбор запроса: {json.dumps(parsed_request, ensure_ascii=False)}\n"
            f"Файлы проекта:\n{scan_data.get('file_tree', 'не доступны')[:2000]}\n"
            f"{'Контекст: ' + prev_context if prev_context else ''}\n\n"
            "Верни JSON с полем 'steps' - массив шагов.\n"
            "Каждый шаг: {step_number, description, files_to_modify, checklist_id}\n"
            "Верни ТОЛЬКО JSON."
        )
        return await self.doc_generator.llm_json(prompt, self.client, self.model, 0.2)

    async def _run_investigation(self, query: str, scan_data: Dict,
                                 parsed_request: Dict) -> Dict:
        prompt = (
            "Проведи расследование проблемы.\n\n"
            f"Описание: {query}\n"
            f"Разбор: {json.dumps(parsed_request, ensure_ascii=False)}\n"
            f"Структура проекта:\n{scan_data.get('file_tree', '')[:3000]}\n\n"
            "Верни JSON: {root_cause, affected_files, fix_strategy, report}"
        )
        return await self.doc_generator.llm_json(prompt, self.client, self.model, 0.1)

    async def _run_llm_phase(self, phase_name: str, workflow: str, query: str,
                             parsed_request: Dict, scan_data: Dict,
                             prev_context: str) -> Any:
        research_prompt = _load_prompt("research_mode")
        if workflow == "analyze" and phase_name == "analyze":
            prompt = (
                f"Проведи глубокий анализ проекта.\nЗапрос: {query}\n"
                f"Структура проекта:\n{scan_data.get('file_tree', '')[:4000]}\n"
                f"Содержимое ключевых файлов:\n{scan_data.get('file_contents', '')[:8000]}\n"
                f"Разбор запроса: {json.dumps(parsed_request, ensure_ascii=False)}\n\n"
                "Включи: стек, архитектура, точки входа, потоки данных, технический долг, рекомендации."
            )
        elif workflow == "research" and phase_name == "research":
            prompt = (
                f"Исследуй тему и собери информацию.\nЗапрос: {query}\n"
                f"Разбор: {json.dumps(parsed_request, ensure_ascii=False)}\n"
                f"{('Контекст проекта: ' + prev_context) if prev_context else ''}\n\n"
                "Используй web_fetch и web_api для сбора данных.\n"
                "Для каждого источника укажи URL и краткую выжимку."
            )
        elif phase_name == "generate_report":
            prompt = (
                f"Сформируй финальный отчёт по результатам {workflow}.\nЗапрос: {query}\n"
                f"Разбор: {json.dumps(parsed_request, ensure_ascii=False)}\n"
                f"Структура:\n{scan_data.get('file_tree', '')[:3000]}\n"
                f"{('Контекст: ' + prev_context) if prev_context else ''}\n\n"
                "Формат: markdown отчёт с секциями, выводами и рекомендациями."
            )
        else:
            prompt = (
                f"Выполни фазу '{phase_name}' воркфлоу '{workflow}'.\n\n"
                f"Запрос: {query}\n"
                f"Разбор: {json.dumps(parsed_request, ensure_ascii=False)}\n"
                f"Структура:\n{scan_data.get('file_tree', '')[:3000]}\n"
                f"{'Контекст: ' + prev_context if prev_context else ''}\n\n"
                "Выполни задачу и верни результат."
            )
        if self.active_project_dir and workflow in ("analyze", "research"):
            sys_prompt = (research_prompt or "").format(active_project_dir=self.active_project_dir or "")
            if sys_prompt and not any(sys_prompt in str(m.get("content", "")) for m in self.history[-3:]):
                self.history.append({"role": "system", "content": sys_prompt})
        self.history.append({"role": "user", "content": prompt})
        return await self._step(project_dir=self.active_project_dir)

    async def _execute_implementation(self, stage: Stage, plan: Dict,
                                      digest: Dict, project_dir: str) -> Dict:
        steps = plan.get("steps", [])
        if not steps:
            return {"total": 0, "completed": 0, "failed": 0, "blocked": 0, "failed_percent": 0}

        digest_str = json.dumps(digest, ensure_ascii=False)
        execution_log: List[Dict] = []
        completed_ids: set = set()
        failed_ids: set = set()
        log_meta = {
            "project_dir": project_dir,
            "stage": stage.num,
            "started_at": _now_iso(),
            "status": "running",
        }

        for step in steps:
            step_num = step.get("step_number", "?")
            cid = str(step.get("checklist_id", step.get("id", "")))
            desc = step.get("description", "")

            deps = set(str(d) for d in step.get("depends_on", []))
            if deps & failed_ids:
                log.warning(f"step {step_num} blocked by failed dependency")
                execution_log.append({
                    "step_number": step_num, "checklist_id": cid,
                    "description": desc, "status": "blocked",
                    "elapsed": 0, "error": "dependency failed",
                })
                stage.save_execution_log(execution_log, {**log_meta, "status": "running"})
                continue

            await self.progress.on_step_start(step_num, len(steps), desc)
            log.info(f"step {step_num}: {desc}")
            start = time.time()
            status = "completed"
            error = ""

            for attempt in range(self.config.max_retry_per_step):
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
                        f"CRITICAL: The absolute root directory is {project_dir}\n"
                        f"ALL file paths MUST point inside {project_dir}."
                    )
                    self.history.append({"role": "system", "content": system_instruction})
                    self.history.append({"role": "user", "content": prompt})
                    await self._step(project_dir=project_dir)
                    status = "completed"
                    completed_ids.add(cid)
                    self.doc_generator.mark_step_completed(stage.artifacts_dir, cid, step_num)
                    error = ""
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
            stage.save_execution_log(execution_log, {**log_meta, "status": "running"})
            await self.progress.on_step_done(step_num, status)

        total = len(steps)
        completed = sum(1 for e in execution_log if e["status"] == "completed")
        failed = sum(1 for e in execution_log if e["status"] == "failed")
        blocked = sum(1 for e in execution_log if e["status"] == "blocked")
        failed_pct = (failed / max(total, 1)) * 100

        log_meta["status"] = "completed"
        log_meta["finished_at"] = _now_iso()
        stage.save_execution_log(execution_log, log_meta)

        return {
            "total": total, "completed": completed,
            "failed": failed, "blocked": blocked,
            "failed_percent": round(failed_pct, 1),
        }

    async def _handle_review(self, comments: str, stage: Stage,
                             checklist: Dict, walkthrough: Dict, plan: Dict,
                             digest: Dict, parsed_request: Dict):
        review_result = await self.doc_generator.parse_review_comments(
            comments,
            json.dumps(checklist, ensure_ascii=False),
            json.dumps(walkthrough, ensure_ascii=False),
            json.dumps(plan, ensure_ascii=False),
            self.client, self.model,
        )
        to_regen = review_result.get("documents_to_regenerate", [])
        if to_regen:
            digest_str = json.dumps(digest, ensure_ascii=False)
            parsed_str = json.dumps(parsed_request, ensure_ascii=False) + f"\nКомментарии: {comments}"
            if "checklist" in to_regen:
                checklist = await self.doc_generator.generate_checklist(
                    digest_str, parsed_str, self.client, self.model,
                )
                stage.save_artifact("checklist.yaml", checklist)
            if "walkthrough" in to_regen or "checklist" in to_regen:
                walkthrough = await self.doc_generator.generate_walkthrough(
                    digest_str, parsed_str,
                    json.dumps(checklist, ensure_ascii=False),
                    self.client, self.model,
                )
                stage.save_artifact("walkthrough.yaml", walkthrough)
            plan = await self.doc_generator.generate_plan(
                digest_str, parsed_str,
                json.dumps(checklist, ensure_ascii=False),
                json.dumps(walkthrough, ensure_ascii=False),
                self.client, self.model,
            )
            stage.save_artifact("implementation_plan.yaml", plan)

    async def _resume_stage(self, stage: Stage, stage_mgr: StageManager) -> RequestResult:
        execution_log_data = stage.load_execution_log()
        plan = stage.load_plan()
        if not plan:
            artifact_plan = stage.load_artifact("implementation_plan.yaml")
            if not artifact_plan:
                artifact_plan = stage.load_artifact(f"{stage.workflow}_plan.yaml")
            plan = artifact_plan

        if not plan:
            return RequestResult("resume", "failed", "План не найден для возобновления")

        digest = stage.load_artifact("project_digest.yaml") or {}

        completed_ids = set()
        prev_entries = []
        if execution_log_data:
            for entry in execution_log_data.get("steps", []):
                if entry.get("status") == "completed":
                    completed_ids.add(str(entry.get("checklist_id", "")))
            prev_entries = execution_log_data.get("steps", [])

        steps = plan.get("steps", [])
        pending = [s for s in steps if str(s.get("checklist_id", s.get("id", ""))) not in completed_ids]

        if not pending:
            stage.update_status("completed")
            return RequestResult("resume", "completed", "Все шаги уже выполнены")

        log.info(f"resume stage-{stage.num}: {len(pending)} pending of {len(steps)}")

        # Выполняем оставшиеся шаги
        temp_plan = {"steps": pending}
        exec_result = await self._execute_implementation(
            stage, temp_plan, digest, self.active_project_dir,
        )

        status = "completed"
        if exec_result.get("failed_percent", 0) > self.config.failed_tasks_threshold_percent:
            status = "critical_failure"
        elif exec_result.get("failed", 0) > 0:
            status = "partial"

        stage.update_status(status)

        self.memory.add({
            "goal": f"resume stage-{stage.num}",
            "intent": "resume",
            "project": self.active_project_dir,
            "status": status,
            "timestamp": time.time(),
        })

        await self.progress.on_done(status)
        return RequestResult("resume", status, data=exec_result, stage_num=stage.num)

    def _to_stage_plan(self, wf_def: WorkflowDef, plan_data: Dict) -> Dict:
        """Конвертирует план в формат stage plan.yaml."""
        phases = []
        for phase_def in wf_def.phases:
            phase = {
                "name": phase_def.name,
                "status": "pending",
                "steps": [],
            }
            if phase_def.name == "implement":
                for step in plan_data.get("steps", []):
                    phase["steps"].append({
                        "id": str(step.get("step_number", step.get("id", ""))),
                        "description": step.get("description", ""),
                        "status": "pending",
                        "depends_on": [str(d) for d in step.get("depends_on", [])],
                    })
            phases.append(phase)
        return {"workflow": wf_def.name, "phases": phases}

    async def _step(self, project_dir: str = None) -> str:
        messages = [{"role": "system", "content": self.system_prompt}] + self.history
        tools = self.tools_registry.get_openai_schemas()

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
        )

        message = response.choices[0].message
        msg_dict = {k: v for k, v in message.model_dump().items() if v is not None}
        self.history.append(msg_dict)

        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                arguments_str = tool_call.function.arguments
                result = None

                try:
                    tool_args = json.loads(arguments_str)

                    if project_dir:
                        path_error = None
                        for k in list(tool_args.keys()):
                            if k in PATH_ARGS and isinstance(tool_args[k], str):
                                try:
                                    tool_args[k] = _resolve_and_guard(tool_args[k], project_dir)
                                except ValueError as e:
                                    path_error = str(e)
                                    break
                        if path_error:
                            result = f"ERROR: {path_error}"
                        else:
                            if tool_name == "execute_command" and "cwd" not in tool_args:
                                tool_args["cwd"] = project_dir

                    if result is None:
                        tool = self.tools_registry.get(tool_name)
                        if not tool:
                            result = f"Error: Tool {tool_name} not found"
                        else:
                            if tool_name in DANGEROUS_TOOLS and self.confirmation_callback:
                                confirmed = await self.confirmation_callback(tool_name, tool_args)
                                if not confirmed:
                                    result = "Tool execution cancelled by user."
                                else:
                                    result = await tool.run(tool.validate_args(tool_args))
                            else:
                                result = await tool.run(tool.validate_args(tool_args))

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

    async def create_project_dir(self, goal: str) -> str:
        prompt = (
            "You are a strict JSON responder. Generate a short kebab-case directory name.\n"
            'Return ONLY JSON: {"dir_name": "my-project"}\n'
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
            name = json.loads(js).get("dir_name", "new-project") if js else "new-project"
        except Exception:
            name = "new-project"

        name = f"{name}_{int(time.time())}"
        base_dir = os.path.abspath(self.config.projects_dir)
        project_dir = os.path.join(base_dir, name)
        os.makedirs(project_dir, exist_ok=True)
        self.active_project_dir = project_dir
        return project_dir
