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


def _show_resume_info(project_dir: str) -> tuple[int, int] | None:
    """
    Показывает таблицу стейджей проекта и статус execution_log.
    Возвращает (stage, version) последнего прерванного стейджа или None.
    """
    max_stage, max_version = get_latest_stage_version(project_dir)
    if max_stage == 0:
        return None

    doc_gen = DocumentGenerator()
    docs_dir = _docs_dir_path(project_dir, max_stage, max_version)
    execution_log = doc_gen.load_execution_log(docs_dir)

    table = Table(title=f"Стейдж {max_stage} / Версия {max_version}", show_lines=True)
    table.add_column("Параметр", style="cyan")
    table.add_column("Значение")

    if execution_log:
        meta = execution_log.get("meta", {})
        stats = execution_log.get("stats", {})
        steps = execution_log.get("steps", [])
        pipeline_status = meta.get("status", "unknown")

        table.add_row("Статус пайплайна", pipeline_status)
        table.add_row("Запущен", meta.get("started_at", "—"))
        table.add_row("Завершён", meta.get("finished_at", "прерван"))
        table.add_row("Всего шагов", str(meta.get("total_steps", len(steps))))
        table.add_row("Выполнено", str(stats.get("completed", 0)))
        table.add_row("Ошибок", str(stats.get("failed", 0)))
        table.add_row("Заблокировано", str(stats.get("blocked", 0)))

        # Находим первый незавершённый шаг
        completed_ids = {str(e.get("checklist_id")) for e in steps if e.get("status") == "completed"}
        plan = doc_gen.load_plan(docs_dir)
        pending = []
        if plan:
            for s in plan.get("steps", []):
                if str(s.get("checklist_id", "")) not in completed_ids:
                    pending.append(f"Шаг {s.get('step_number')}: {s.get('description', '')[:60]}")

        if pending:
            table.add_row("Ожидают выполнения", f"{len(pending)} шагов")
            table.add_row("Следующий", pending[0] if pending else "—")
            console.print(table)
            return max_stage, max_version
        else:
            table.add_row("Незавершённых шагов", "нет (все выполнены)")
            console.print(table)
            return None
    else:
        # Документы есть, но лог не сохранён - прерывание до начала имплементации
        plan = doc_gen.load_plan(docs_dir)
        if plan:
            steps_count = len(plan.get("steps", []))
            table.add_row("Статус", "прерван до имплементации")
            table.add_row("Шагов в плане", str(steps_count))
            console.print(table)
            return max_stage, max_version
        return None


async def main():
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
        f"[bold green]OpenRouter Agent[/bold green]  model={model}\n"
        f"AUTO_CONFIRM=[{'green]true' if auto_confirm else 'red]false'}[/]\n"
        "Команды: exit / quit / reset / resume <путь_к_проекту>",
        style="blue",
    ))

    agent = Agent(
        api_key=api_key,
        model=model,
        confirmation_callback=_build_confirmation_callback(auto_confirm),
        pipeline_config=PipelineConfig.from_env(),
    )

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

        # Сброс контекста
        if stripped.lower() == "reset":
            agent.active_project_dir = None
            agent.history.clear()
            console.print("[dim]Контекст сброшен.[/dim]")
            continue

        # Команда resume
        if stripped.lower().startswith("resume"):
            parts = stripped.split(maxsplit=1)
            if len(parts) == 2:
                resume_dir = parts[1].strip()
            elif agent.active_project_dir:
                resume_dir = agent.active_project_dir
            else:
                console.print("[yellow]Укажите путь к проекту: resume /path/to/project[/yellow]")
                continue

            resume_dir = os.path.abspath(resume_dir)
            if not os.path.isdir(resume_dir):
                console.print(f"[red]Директория не найдена: {resume_dir}[/red]")
                continue

            resume_info = _show_resume_info(resume_dir)
            if resume_info is None:
                console.print("[green]Незавершённых шагов не найдено. Проект завершён или не начат.[/green]")
                continue

            stage, version = resume_info
            confirmed = Confirm.ask(
                f"\nПродолжить выполнение стейджа {stage} версии {version}?",
                default=True,
            )
            if not confirmed:
                continue

            async def review_callback(msg: str) -> str:
                spinner_stop()
                console.rule("[bold blue]РЕВЬЮ ДОКУМЕНТОВ[/bold blue]")
                console.print(msg)
                answer = Prompt.ask("[bold]Ваш ответ[/bold] (пусто = ok)")
                console.rule()
                return answer

            spinner_start("Продолжаю выполнение...")
            try:
                result = await agent.resume_pipeline(
                    resume_dir,
                    stage=stage,
                    version=version,
                    review_callback=review_callback,
                )
            finally:
                spinner_stop()

            status_val = result.get("status", "unknown")
            color = {"success": "green", "partial_success": "yellow"}.get(status_val, "red")
            console.print(f"\n[bold {color}]Resume: {status_val}[/bold {color}]")

            ver = result.get("stages", {}).get("verification", {})
            if ver:
                console.print(
                    f"[dim]Всего {ver.get('total', 0)}, "
                    f"выполнено {ver.get('completed', 0)}, "
                    f"ошибок {ver.get('failed', 0)}, "
                    f"заблокировано {ver.get('blocked', 0)}[/dim]"
                )
            if result.get("error"):
                console.print(f"[red]{result['error']}[/red]")
            continue

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

                async def review_callback(msg: str) -> str:
                    spinner_stop()
                    console.rule("[bold blue]РЕВЬЮ ДОКУМЕНТОВ[/bold blue]")
                    console.print(msg)
                    console.print(
                        "\n[dim]Добавьте <!-- COMMENT: текст --> в файлы документов "
                        "или напишите комментарий здесь. Пустой ввод = ok.[/dim]"
                    )
                    answer = Prompt.ask("[bold]Ваш ответ[/bold]")
                    console.rule()
                    return answer

                spinner_start("Выполняю пайплайн...")
                try:
                    result = await agent.run_pipeline(project_dir, stripped, review_callback)
                finally:
                    spinner_stop()

                status_val = result.get("status", "unknown")
                color = {
                    "success": "green",
                    "partial_success": "yellow",
                    "needs_clarification": "yellow",
                }.get(status_val, "red")
                console.print(f"\n[bold {color}]Пайплайн: {status_val}[/bold {color}]")

                ver = result.get("stages", {}).get("verification", {})
                if ver:
                    console.print(
                        f"[dim]Шагов {ver.get('total', 0)}, "
                        f"выполнено {ver.get('completed', 0)}, "
                        f"ошибок {ver.get('failed', 0)}, "
                        f"заблокировано {ver.get('blocked', 0)}[/dim]"
                    )

                if status_val == "needs_clarification":
                    console.print("[yellow]Требуются уточнения:[/yellow]")
                    for q in result.get("questions", []):
                        console.print(f"  - {q}")
                elif status_val in ("partial_success", "critical_failure"):
                    console.print(
                        f"[dim]Для продолжения используйте: resume {project_dir}[/dim]"
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
            console.print("\n[yellow]Выход...[/yellow]")
            break
        except Exception as e:
            spinner_stop()
            log.error(f"ошибка: {e}", exc_info=True)
            console.print(f"\n[red]Ошибка:[/red] {e}")


if __name__ == "__main__":
    asyncio.run(main())
