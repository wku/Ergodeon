import os
import json
import asyncio
import logging
import time
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
from openrouter_agent.utils import find_balanced_json

log = logging.getLogger(__name__)

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
    if not os.path.exists(stage_dir):
         return max_stage, 0
    versions = [d for d in os.listdir(stage_dir) if d.startswith("версия-") and os.path.isdir(os.path.join(stage_dir, d))]
    if not versions:
         return max_stage, 0
    max_version = max([int(v.split("-")[1]) for v in versions if v.split("-")[1].isdigit()], default=0)
    return max_stage, max_version


DANGEROUS_TOOLS = {
    "write_file", "delete_file", "edit_file", "edit_file_by_lines",
    "move_file", "execute_command", "multi_edit_file"
}


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
        self.system_prompt = system_prompt or "You are a helpful AI coding assistant. You can read and write files, execute commands, and more."
        self.confirmation_callback = confirmation_callback

        self.intent_classifier = IntentClassifier()
        self.memory = EpisodeMemory(memory_path)
        self.planner = Planner()
        self.scanner = ProjectScanner()
        self.doc_generator = DocumentGenerator()
        self.pipeline_config = pipeline_config or PipelineConfig()

        log.info(f"agent initialized, model={model}, memory={memory_path}")

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
            if js:
                name = json.loads(js).get("dir_name", "new_project")
            else:
                name = "new_project"
        except Exception as e:
            log.warning(f"Error generating name: {e}")
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

        self.history.append({"role": "user", "content": user_input})

        start_time = time.time()
        response = await self._step()
        elapsed = time.time() - start_time

        self.memory.add({
            "goal": user_input,
            "intent": intent,
            "response_preview": response[:200] if response else "",
            "elapsed": round(elapsed, 2),
            "timestamp": time.time(),
        })

        log.info(f"chat completed in {elapsed:.1f}s, intent={intent}")
        return response

    async def run_pipeline(
        self,
        project_dir: str,
        goal: str,
        review_callback: Callable[[str], Awaitable[str]] | None = None,
    ) -> Dict[str, Any]:
        log.info(f"pipeline started: project={project_dir}, goal={goal[:100]}")
        result = {"status": "started", "stages": {}}

        # Определение текущего стейджа и версии
        max_stage, max_version = get_latest_stage_version(project_dir)
        old_context = ""
        
        if max_stage > 0 and max_version > 0:
            docs_dir = os.path.join(project_dir, "флоу-разработки", f"стейдж-{max_stage}", f"версия-{max_version}")
            try:
                with open(os.path.join(docs_dir, "parsed_request.json"), "r", encoding="utf-8") as f:
                    old_req = f.read()
                    old_context += f"ПРЕДЫДУЩИЙ ЗАПРОС:\n{old_req}\n\n"
            except FileNotFoundError:
                pass
            try:
                with open(os.path.join(docs_dir, "checklist.json"), "r", encoding="utf-8") as f:
                    old_cl = f.read()
                    old_context += f"ТЕКУЩИЙ ЧЕКЛИСТ:\n{old_cl}\n\nВАЖНО: Добавь новые задачи в этот чеклист. Старые задачи сохрани как есть (если они не отменены)!"
            except FileNotFoundError:
                pass
            current_stage = max_stage + 1
        else:
            current_stage = 1
            
        current_version = 1
        docs_dir = os.path.join(project_dir, "флоу-разработки", f"стейдж-{current_stage}", f"версия-{current_version}")

        # etap 1 - parsning zaprosa
        log.info("stage 1: parsing request")
        if old_context:
            goal_with_ctx = f"Новый запрос: {goal}\n\n---\nИстория проекта:\n{old_context}"
        else:
            goal_with_ctx = goal
            
        parsed = await self.doc_generator.parse_request(goal_with_ctx, "", self.client, self.model)
        result["stages"]["parse_request"] = parsed
        if parsed.get("clarification_needed"):
            result["status"] = "needs_clarification"
            result["questions"] = parsed["clarification_needed"]
            return result

        # etap 2-3 - issledovanie proekta i digest
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

        # etap 4 - generaciya 3 dokumentov
        log.info("stage 4: generating documents")
        parsed_str = json.dumps(parsed, ensure_ascii=False)
        digest_str = json.dumps(digest, ensure_ascii=False)

        checklist = await self.doc_generator.generate_checklist(
            digest_str, parsed_str, self.client, self.model,
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

        valid, issues = self.doc_generator.validate_documents(checklist, walkthrough, plan)
        if not valid:
            log.warning(f"document validation issues: {issues}")

        docs = {
            "parsed_request": parsed,
            "digest": digest,
            "checklist": checklist,
            "walkthrough": walkthrough,
            "plan": plan,
        }
        self.doc_generator.save_to_project(docs_dir, docs)
        result["stages"]["documents"] = {"path": docs_dir, "valid": valid, "issues": issues}

        # etap 5 - revyu klientom
        if review_callback:
            log.info("stage 5: requesting review")
            while True:
                comments_cli = await review_callback(
                    f"Документы сгенерированы в {docs_dir}. "
                    f"Проверьте checklist.md, walkthrough.md, implementation_plan.md.\n"
                    f"Оставьте `<!-- COMMENT: текст -->` прямо в файлах (будут удалены после прочтения агентом)\n"
                    f"Или напишите комментарии ниже в чате. Отправьте комментарии или напишите 'ok' для продолжения."
                )
                
                inline_comments = self.doc_generator.extract_inline_comments(docs_dir)
                
                all_comments = []
                if comments_cli and comments_cli.strip().lower() not in ("ok", "approved", "да", ""):
                    all_comments.append(f"Комментарии из чата:\n{comments_cli}")
                if inline_comments:
                    all_comments.append(f"Inline комментарии из документов:\n{inline_comments}")
                    
                comments = "\n\n".join(all_comments)
                
                if not comments:
                    log.info("review: approved")
                    break
                    
                log.info(f"review processing comments")
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
                    docs_dir = os.path.join(project_dir, "флоу-разработки", f"стейдж-{current_stage}", f"версия-{current_version}")
                if "checklist" in to_regen:
                    checklist = await self.doc_generator.generate_checklist(
                        digest_str, parsed_str + f"\nКомментарии: {comments}",
                        self.client, self.model,
                    )
                    walkthrough = await self.doc_generator.generate_walkthrough(
                        digest_str, parsed_str,
                        json.dumps(checklist, ensure_ascii=False),
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
                        json.dumps(checklist, ensure_ascii=False),
                        self.client, self.model,
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

                docs["checklist"] = checklist
                docs["walkthrough"] = walkthrough
                docs["plan"] = plan
                self.doc_generator.save_to_project(docs_dir, docs)

        # etap 6 - implementaciya
        log.info("stage 6: implementation")
        # snapshot_dir = Sandbox.snapshot(project_dir, docs_dir)
        result["stages"]["snapshot"] = "skipped"

        execution_log = []
        steps = plan.get("steps", [])
        completed_ids = set()
        failed_ids = set()

        for step in steps:
            step_num = step.get("step_number", "?")
            cid = step.get("checklist_id", "")
            desc = step.get("description", "")

            deps = set()
            for task in checklist.get("checklist", []):
                if task.get("id") == cid:
                    deps = set(task.get("depends_on", []))
                    break

            if deps & failed_ids:
                log.warning(f"step {step_num} blocked: dependency failed")
                execution_log.append({
                    "step_number": step_num, "checklist_id": cid,
                    "description": desc, "status": "blocked",
                    "elapsed": 0, "error": "dependency failed",
                })
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
                        previous_steps_log=json.dumps(execution_log, ensure_ascii=False)
                    )
                    
                    system_instruction = (
                        f"You are executing a step in the implementation plan.\n"
                        f"IMPORTANT: The absolute root directory for this project is {project_dir}\n"
                        f"All file paths in your tool calls (write_file, edit_file, execute_command, etc.) "
                        f"MUST be relative to it or absolute paths inside {project_dir}. "
                        f"Do NOT create or modify files outside {project_dir}. Use your tools strictly."
                    )
                    self.history.append({"role": "system", "content": system_instruction})
                    self.history.append({"role": "user", "content": prompt})
                    response = await self._step(project_dir=project_dir)
                    
                    status = "completed"
                    completed_ids.add(cid)
                    error = ""
                    self.doc_generator.mark_step_completed(docs_dir, cid, step_num)
                    break
                except Exception as e:
                    log.error(f"step {step_num} attempt {attempt+1} error: {e}")
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

        self.doc_generator.save_execution_log(docs_dir, execution_log)
        result["stages"]["execution"] = execution_log

        # etap 7 - finalnaya verifikaciya
        log.info("stage 7: final verification")
        total = len(steps)
        completed = sum(1 for e in execution_log if e["status"] == "completed")
        failed = sum(1 for e in execution_log if e["status"] == "failed")
        blocked = sum(1 for e in execution_log if e["status"] == "blocked")

        failed_pct = (failed / max(total, 1)) * 100
        if failed_pct > self.pipeline_config.failed_tasks_threshold_percent:
            result["status"] = "critical_failure"
            log.error(f"critical failure: {failed_pct:.0f}% tasks failed (threshold {self.pipeline_config.failed_tasks_threshold_percent}%)")
        elif failed > 0:
            result["status"] = "partial_success"
        else:
            result["status"] = "success"

        result["stages"]["verification"] = {
            "total": total, "completed": completed,
            "failed": failed, "blocked": blocked,
            "failed_percent": round(failed_pct, 1),
        }

        self.memory.add({
            "goal": goal, "intent": "pipeline",
            "project": project_dir,
            "status": result["status"],
            "stats": result["stages"]["verification"],
            "timestamp": time.time(),
        })

        log.info(f"pipeline finished: {result['status']}")
        return result

    async def _step(self, project_dir: str | None = None) -> str:
        messages = [{"role": "system", "content": self.system_prompt}] + self.history
        tools = self._get_openai_tools()

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None
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
                        for k, v in list(tool_args.items()):
                            if k in ("path", "directory", "source", "destination", "cwd") and isinstance(v, str):
                                if not os.path.isabs(v):
                                    tool_args[k] = os.path.normpath(os.path.join(project_dir, v))
                                elif not v.startswith(project_dir):
                                    relative = v.lstrip("/")
                                    tool_args[k] = os.path.normpath(os.path.join(project_dir, relative))
                        if tool_name == "execute_command" and "cwd" not in tool_args:
                            tool_args["cwd"] = project_dir

                    tool = self.tools_registry.get(tool_name)

                    if not tool:
                        result = f"Error: Tool {tool_name} not found"
                    else:
                        log.info(f"Использую инструмент: [cyan]{tool_name}[/cyan] с аргументами: {tool_args}")
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
                    "content": str(result)
                })

            return await self._step(project_dir=project_dir)

        return message.content or ""

    def _get_openai_tools(self) -> List[ChatCompletionToolParam]:
        schemas = self.tools_registry.get_openai_schemas()
        return schemas
