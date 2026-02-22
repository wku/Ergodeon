"""
Ergodeon CLI

Режимы запуска:
    ./run_demo.sh                              обычный чат
    ./run_demo.sh --project /path/to/project   открыть проект (с документами или без)
    ./run_demo.sh --resume  /path/to/project   сразу возобновить прерванный пайплайн

Команды в чате:
    exit / quit         выход
    reset               сбросить контекст активного проекта
    project             показать текущий активный проект
    adopt <путь>        взять существующую папку как проект (без документов)
    resume [путь]       возобновить прерванный пайплайн
    analyze [путь]      запустить анализ проекта и сохранить в .md файл
"""

import argparse
import asyncio
import os
import sys
import logging
from typing import Any
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

try:
    from openrouter_agent.agent.core import Agent, get_latest_stage_version, _docs_dir_path
    from openrouter_agent.agent.config import PipelineConfig
    from openrouter_agent.agent.doc_generator import DocumentGenerator
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    from openrouter_agent.agent.core import Agent, get_latest_stage_version, _docs_dir_path
    from openrouter_agent.agent.config import PipelineConfig
    from openrouter_agent.agent.doc_generator import DocumentGenerator

console = Console()
log = logging.getLogger(__name__)

_spinner_live = None


def spinner_start(msg: str):
    from rich.live import Live
    from rich.text import Text
    global _spinner_live
    spinner_stop()
    live = Live(
        Text.from_markup(f"[bold green]{msg}[/bold green]"),
        console=console,
        refresh_per_second=10,
        transient=True,
    )
    live.start()
    _spinner_live = live
    return live


def spinner_stop():
    global _spinner_live
    if _spinner_live is not None:
        try:
            _spinner_live.stop()
        except Exception:
            pass
        _spinner_live = None


def _build_confirmation_callback(auto_confirm: bool):
    if auto_confirm:
        async def _auto(tool_name: str, args: Any) -> bool:
            log.info(f"AUTO_CONFIRM: {tool_name}")
            return True
        return _auto

    async def _interactive(tool_name: str, args: Any) -> bool:
        spinner_stop()
        console.print(f"\n[bold red]⚠  ОПАСНАЯ ОПЕРАЦИЯ[/bold red]")
        console.print(f"Инструмент: [cyan]{tool_name}[/cyan]")
        target = (
            args.get("path") or args.get("command") or
            args.get("source") or args.get("destination") or str(args)
        )
        if len(str(target)) > 200:
            target = str(target)[:200] + "..."
        console.print(f"Цель: {target}")
        return Confirm.ask("Выполнить?", default=False)

    return _interactive


# ------------------------------------------------------------------ проект helpers

def _project_status(project_dir: str) -> dict:
    """
    Возвращает статус проекта:
    - has_docs: bool - есть ли флоу-разработки документы
    - has_interrupted: bool - есть ли прерванный пайплайн
    - stage, version: int - последний стейдж/версия
    - pending_steps: int - незавершённых шагов
    - next_step: str - описание следующего шага
    """
    result = {
        "has_docs": False,
        "has_interrupted": False,
        "stage": 0,
        "version": 0,
        "pending_steps": 0,
        "next_step": "",
        "pipeline_status": "",
    }

    max_stage, max_version = get_latest_stage_version(project_dir)
    if max_stage == 0:
        return result

    result["has_docs"] = True
    result["stage"] = max_stage
    result["version"] = max_version

    doc_gen = DocumentGenerator()
    docs_dir = _docs_dir_path(project_dir, max_stage, max_version)
    execution_log = doc_gen.load_execution_log(docs_dir)

    plan = doc_gen.load_plan(docs_dir)
    steps = plan.get("steps", []) if plan else []

    if execution_log:
        meta = execution_log.get("meta", {})
        pipeline_status = meta.get("status", "unknown")
        result["pipeline_status"] = pipeline_status

        if pipeline_status not in ("success",):
            completed_ids = {
                str(e.get("checklist_id"))
                for e in execution_log.get("steps", [])
                if e.get("status") == "completed"
            }
            pending = [
                s for s in steps
                if str(s.get("checklist_id", "")) not in completed_ids
            ]
            result["pending_steps"] = len(pending)
            if pending:
                s = pending[0]
                result["next_step"] = f"Шаг {s.get('step_number')}: {s.get('description', '')[:70]}"
            result["has_interrupted"] = len(pending) > 0
    else:
        # Документы есть, лог нет - прерывание до имплементации
        if steps:
            result["has_interrupted"] = True
            result["pending_steps"] = len(steps)
            s = steps[0]
            result["next_step"] = f"Шаг {s.get('step_number')}: {s.get('description', '')[:70]}"
            result["pipeline_status"] = "interrupted_before_implementation"

    return result


def _show_project_status(project_dir: str):
    """Выводит таблицу статуса проекта."""
    abs_dir = os.path.abspath(project_dir)
    status = _project_status(project_dir)

    table = Table(title=f"Проект: {abs_dir}", show_lines=True)
    table.add_column("Параметр", style="cyan", no_wrap=True)
    table.add_column("Значение")

    table.add_row("Путь", abs_dir)

    if not status["has_docs"]:
        table.add_row("Документы", "[yellow]отсутствуют[/yellow]")
        table.add_row("Режим", "adopt - работа без пайплайна")
    else:
        table.add_row("Стейдж / Версия", f"{status['stage']} / {status['version']}")
        table.add_row("Статус пайплайна", status["pipeline_status"])
        if status["has_interrupted"]:
            table.add_row("Незавершённых шагов", str(status["pending_steps"]))
            table.add_row("Следующий шаг", status["next_step"])
            table.add_row("Действие", "[bold yellow]resume[/bold yellow] для продолжения")
        else:
            table.add_row("Незавершённых шагов", "[green]нет[/green]")

    console.print(table)


async def _run_adopt(agent: Agent, project_dir: str):
    """
    Берёт существующую папку как активный проект.
    Предлагает варианты действий: анализ / пайплайн / просто работать.
    """
    abs_dir = os.path.abspath(project_dir)
    if not os.path.isdir(abs_dir):
        console.print(f"[red]Директория не найдена: {abs_dir}[/red]")
        return

    agent.active_project_dir = abs_dir
    agent.history.clear()
    _show_project_status(abs_dir)

    console.print("\nЧто хотите сделать с проектом?")
    console.print("  [cyan]1[/cyan] Проанализировать и сохранить анализ в analysis.md")
    console.print("  [cyan]2[/cyan] Запустить пайплайн (создать документы и реализацию)")
    console.print("  [cyan]3[/cyan] Просто работать в режиме чата (без документов)")

    choice = Prompt.ask("Выбор", choices=["1", "2", "3"], default="3")
    return choice


async def _run_analyze(agent: Agent, project_dir: str):
    """
    Анализирует проект и сохраняет результат в analysis.md внутри project_dir.
    """
    abs_dir = os.path.abspath(project_dir)
    agent.active_project_dir = abs_dir

    prompt = (
        "Проанализируй этот проект полностью. "
        "Изучи структуру директорий и содержимое ключевых файлов. "
        "Подготовь подробный анализ который включает: "
        "1) стек технологий и зависимости, "
        "2) архитектуру и основные модули, "
        "3) точки входа и потоки данных, "
        "4) слабые места и технический долг, "
        "5) рекомендации по улучшению. "
        f"Сохрани анализ в файл analysis.md внутри директории {abs_dir}."
    )
    spinner_start("Анализирую проект...")
    try:
        response = await agent.chat(prompt)
    finally:
        spinner_stop()

    console.print("\n[bold]Agent:[/bold]")
    console.print(Markdown(response))

    analysis_path = os.path.join(abs_dir, "analysis.md")
    if os.path.exists(analysis_path):
        console.print(f"\n[green]Анализ сохранён: {analysis_path}[/green]")


async def _run_resume(agent: Agent, project_dir: str, review_callback):
    """Возобновляет прерванный пайплайн."""
    abs_dir = os.path.abspath(project_dir)
    status = _project_status(abs_dir)

    if not status["has_docs"]:
        console.print("[yellow]В этом проекте нет документов пайплайна. Используйте новый запрос.[/yellow]")
        return

    if not status["has_interrupted"]:
        console.print("[green]Все шаги уже выполнены. Нечего продолжать.[/green]")
        return

    _show_project_status(abs_dir)
    confirmed = Confirm.ask(
        f"\nПродолжить с шага: {status['next_step'][:60]}?",
        default=True,
    )
    if not confirmed:
        return

    spinner_start("Продолжаю выполнение...")
    try:
        result = await agent.resume_pipeline(
            abs_dir,
            stage=status["stage"],
            version=status["version"],
            review_callback=review_callback,
        )
    finally:
        spinner_stop()

    _print_pipeline_result(result)
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")


def _print_pipeline_result(result: dict):
    status_val = result.get("status", "unknown")
    color = {"success": "green", "partial_success": "yellow"}.get(status_val, "red")
    console.print(f"\n[bold {color}]Статус: {status_val}[/bold {color}]")
    ver = result.get("stages", {}).get("verification", {})
    if ver:
        console.print(
            f"[dim]Шагов {ver.get('total', 0)}, "
            f"выполнено {ver.get('completed', 0)}, "
            f"ошибок {ver.get('failed', 0)}, "
            f"заблокировано {ver.get('blocked', 0)}[/dim]"
        )


# ------------------------------------------------------------------ интент детектор

# Ключевые слова для определения пользовательского намерения без LLM
_ADOPT_KEYWORDS = (
    "возьми проект", "открой проект", "работай с проектом", "добавь проект",
    "подключи проект", "вот проект", "загрузи проект", "adopt",
    "take this project", "open project", "load project",
)
_RESUME_KEYWORDS = (
    "продолжи", "возобнови", "resume", "continue pipeline",
    "продолжить выполнение", "продолжи с того места",
)
_ANALYZE_KEYWORDS = (
    "проанализируй проект", "анализ проекта", "analyze project",
    "изучи проект", "сделай анализ", "analyse", "analyze",
    "сохрани анализ", "save analysis",
)


def _extract_path_from_input(text: str) -> str | None:
    """
    Пытается извлечь путь из текста пользователя.
    Ищет токены начинающиеся с / или ./ или ~/
    """
    tokens = text.split()
    for token in tokens:
        if token.startswith("/") or token.startswith("./") or token.startswith("~/"):
            expanded = os.path.expanduser(token)
            if os.path.exists(expanded):
                return expanded
    return None


def _detect_user_mode(text: str) -> tuple[str, str | None]:
    """
    Определяет намерение пользователя по тексту.
    Возвращает (mode, path) где mode одно из:
    'adopt', 'resume', 'analyze', 'pipeline', 'chat'
    """
    lower = text.lower()
    path = _extract_path_from_input(text)

    if any(kw in lower for kw in _RESUME_KEYWORDS):
        return "resume", path
    if any(kw in lower for kw in _ANALYZE_KEYWORDS):
        return "analyze", path
    if any(kw in lower for kw in _ADOPT_KEYWORDS):
        return "adopt", path

    # Если пользователь просто кинул путь к директории - спросим что делать
    if path and os.path.isdir(path) and len(text.split()) <= 3:
        return "adopt", path

    return "chat", None


# ------------------------------------------------------------------ main

async def main():
    parser = argparse.ArgumentParser(description="Ergodeon Agent CLI")
    parser.add_argument(
        "--project", "-p",
        metavar="PATH",
        help="Открыть существующий проект (с документами или без)",
    )
    parser.add_argument(
        "--resume", "-r",
        metavar="PATH",
        help="Сразу возобновить прерванный пайплайн в указанном проекте",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, markup=True)],
    )
    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        api_key = Prompt.ask("Enter your OpenRouter API Key", password=True)
        if not api_key:
            console.print("[red]API Key не указан.[/red]")
            return

    auto_confirm = os.getenv("AUTO_CONFIRM", "false").strip().lower() in ("true", "1", "yes")
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")

    console.print(Panel.fit(
        f"[bold green]Ergodeon Agent[/bold green]  model={model}\n"
        f"AUTO_CONFIRM=[{'green]true' if auto_confirm else 'red]false'}[/]\n"
        "Команды: exit  reset  project  adopt <путь>  resume [путь]  analyze [путь]",
        style="blue",
    ))

    agent = Agent(
        api_key=api_key,
        model=model,
        confirmation_callback=_build_confirmation_callback(auto_confirm),
        pipeline_config=PipelineConfig.from_env(),
    )

    async def review_callback(msg: str) -> str:
        spinner_stop()
        console.rule("[bold blue]РЕВЬЮ ДОКУМЕНТОВ[/bold blue]")
        console.print(msg)
        console.print("[dim]Добавьте <!-- COMMENT: текст --> в файлы или напишите здесь. Пусто = ok.[/dim]")
        answer = Prompt.ask("[bold]Ваш ответ[/bold]")
        console.rule()
        return answer

    # ---- обработка флагов запуска ----

    if args.resume:
        resume_dir = os.path.abspath(args.resume)
        await _run_resume(agent, resume_dir, review_callback)

    elif args.project:
        project_dir = os.path.abspath(args.project)
        if not os.path.isdir(project_dir):
            console.print(f"[red]Директория не найдена: {project_dir}[/red]")
            return

        agent.active_project_dir = project_dir
        _show_project_status(project_dir)

        status = _project_status(project_dir)
        if status["has_interrupted"]:
            if Confirm.ask("\nОбнаружен прерванный пайплайн. Продолжить?", default=True):
                await _run_resume(agent, project_dir, review_callback)

    # ---- основной цикл ----

    while True:
        try:
            user_input = Prompt.ask("\n[bold]User[/bold]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Выход...[/yellow]")
            break

        stripped = user_input.strip()
        if not stripped:
            continue
        if stripped.lower() in ("exit", "quit"):
            console.print("[yellow]Выход...[/yellow]")
            break

        # ---- встроенные команды ----

        if stripped.lower() == "reset":
            agent.active_project_dir = None
            agent.history.clear()
            console.print("[dim]Контекст сброшен.[/dim]")
            continue

        if stripped.lower() == "project":
            if agent.active_project_dir:
                _show_project_status(agent.active_project_dir)
            else:
                console.print("[dim]Активный проект не установлен.[/dim]")
            continue

        if stripped.lower().startswith("adopt"):
            parts = stripped.split(maxsplit=1)
            path = os.path.abspath(parts[1]) if len(parts) == 2 else None
            if not path:
                console.print("[yellow]Укажите путь: adopt /path/to/project[/yellow]")
                continue
            choice = await _run_adopt(agent, path)
            if choice == "1":
                await _run_analyze(agent, path)
            elif choice == "2":
                spinner_start("Анализирую запрос...")
                try:
                    is_pipeline = await agent.detect_pipeline_request(
                        "создай план разработки для этого проекта"
                    )
                finally:
                    spinner_stop()
                # Запускаем пайплайн на существующем project_dir
                spinner_start("Выполняю пайплайн...")
                try:
                    result = await agent.run_pipeline(path, "Доработай и улучши проект", review_callback)
                finally:
                    spinner_stop()
                _print_pipeline_result(result)
            # choice == "3": просто работаем, active_project_dir уже установлен
            continue

        if stripped.lower().startswith("resume"):
            parts = stripped.split(maxsplit=1)
            if len(parts) == 2:
                resume_path = os.path.abspath(parts[1])
            elif agent.active_project_dir:
                resume_path = agent.active_project_dir
            else:
                console.print("[yellow]Укажите путь: resume /path/to/project[/yellow]")
                continue
            await _run_resume(agent, resume_path, review_callback)
            continue

        if stripped.lower().startswith("analyze"):
            parts = stripped.split(maxsplit=1)
            if len(parts) == 2:
                analyze_path = os.path.abspath(parts[1])
            elif agent.active_project_dir:
                analyze_path = agent.active_project_dir
            else:
                console.print("[yellow]Укажите путь: analyze /path/to/project[/yellow]")
                continue
            await _run_analyze(agent, analyze_path)
            continue

        # ---- детектор намерения по тексту ----
        # Позволяет писать естественным языком без знания команд

        mode, detected_path = _detect_user_mode(stripped)

        if mode == "adopt" and detected_path:
            choice = await _run_adopt(agent, detected_path)
            if choice == "1":
                await _run_analyze(agent, detected_path)
            elif choice == "2":
                spinner_start("Выполняю пайплайн...")
                try:
                    result = await agent.run_pipeline(detected_path, stripped, review_callback)
                finally:
                    spinner_stop()
                _print_pipeline_result(result)
            continue

        if mode == "resume":
            path = detected_path or agent.active_project_dir
            if path:
                await _run_resume(agent, path, review_callback)
            else:
                console.print("[yellow]Укажите путь к проекту.[/yellow]")
            continue

        if mode == "analyze":
            path = detected_path or agent.active_project_dir
            if path:
                await _run_analyze(agent, path)
            else:
                console.print("[yellow]Укажите путь к проекту.[/yellow]")
            continue

        # ---- pipeline или chat через LLM детектор ----

        try:
            spinner_start("Анализирую запрос...")
            try:
                is_pipeline = await agent.detect_pipeline_request(stripped)
            finally:
                spinner_stop()

            if is_pipeline:
                confirmed = Confirm.ask(
                    "\n[bold yellow]Задача для пайплайна. Запустить?[/bold yellow]",
                    default=True,
                )
                if not confirmed:
                    is_pipeline = False

            if is_pipeline:
                spinner_start("Генерирую имя проекта...")
                try:
                    project_dir = await agent.create_project_dir(stripped)
                finally:
                    spinner_stop()

                console.print(f"[green]Проект: {project_dir}[/green]")

                spinner_start("Выполняю пайплайн...")
                try:
                    result = await agent.run_pipeline(project_dir, stripped, review_callback)
                finally:
                    spinner_stop()

                _print_pipeline_result(result)
                status_val = result.get("status", "")
                if status_val == "needs_clarification":
                    console.print("[yellow]Требуются уточнения:[/yellow]")
                    for q in result.get("questions", []):
                        console.print(f"  - {q}")
                elif status_val in ("partial_success", "critical_failure"):
                    console.print(
                        f"[dim]Для продолжения: resume {project_dir}[/dim]"
                    )
                continue

            # Обычный чат
            spinner_start("Думаю...")
            try:
                response = await agent.chat(stripped)
            finally:
                spinner_stop()

            console.print("\n[bold]Agent:[/bold]")
            console.print(Markdown(response))

        except KeyboardInterrupt:
            spinner_stop()
            console.print("\n[yellow]Прервано.[/yellow]")
        except Exception as e:
            spinner_stop()
            log.error(f"ошибка: {e}", exc_info=True)
            console.print(f"\n[red]Ошибка:[/red] {e}")


if __name__ == "__main__":
    asyncio.run(main())
