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
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

try:
    from openrouter_agent.agent.core import Agent
    from openrouter_agent.agent.config import PipelineConfig
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    from openrouter_agent.agent.core import Agent
    from openrouter_agent.agent.config import PipelineConfig

console = Console()
log = logging.getLogger(__name__)

# Глобальный флаг - спиннер сейчас активен или нет
# Нужен чтобы коллбэки могли его останавливать перед вводом
_spinner_live: Live | None = None


def spinner_start(msg: str) -> Live:
    """Запускает спиннер и возвращает объект Live для последующей остановки."""
    global _spinner_live
    live = Live(
        Text.from_markup(f"[bold green]{msg}[/bold green]"),
        console=console,
        refresh_per_second=10,
        transient=True,   # удаляет строку спиннера после stop()
    )
    live.start()
    _spinner_live = live
    return live


def spinner_stop():
    """Останавливает текущий спиннер если он активен."""
    global _spinner_live
    if _spinner_live is not None:
        try:
            _spinner_live.stop()
        except Exception:
            pass
        _spinner_live = None


def _build_confirmation_callback(auto_confirm: bool):
    """
    Коллбэк для опасных файловых операций (write_file, edit_file, execute_command и т.д.).
    AUTO_CONFIRM=true  -> не показывает интерфейс, пишет только в лог.
    AUTO_CONFIRM=false -> останавливает спиннер, явно ждёт y/n, затем возобновляет.
    """
    if auto_confirm:
        async def _auto(tool_name: str, args: Any) -> bool:
            log.info(f"AUTO_CONFIRM tool={tool_name}")
            return True
        return _auto

    async def _interactive(tool_name: str, args: Any) -> bool:
        # Обязательно останавливаем спиннер перед вводом
        spinner_stop()

        console.print(f"\n[bold red]⚠  ОПАСНАЯ ОПЕРАЦИЯ[/bold red]")
        console.print(f"Инструмент : [cyan]{tool_name}[/cyan]")
        # Показываем путь или команду кратко, не весь args
        target = (
            args.get("path") or args.get("command") or
            args.get("source") or args.get("destination") or str(args)
        )
        if len(target) > 200:
            target = target[:200] + "..."
        console.print(f"Цель       : {target}")

        result = Confirm.ask("Выполнить?", default=False)
        return result

    return _interactive


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
        "Команды: exit / quit / reset",
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
        if stripped.lower() == "reset":
            agent.active_project_dir = None
            agent.history.clear()
            console.print("[dim]Контекст сброшен.[/dim]")
            continue

        try:
            # --- определяем тип запроса ---
            live = spinner_start("Анализирую запрос...")
            try:
                is_pipeline = await agent.detect_pipeline_request(stripped)
            finally:
                spinner_stop()

            # --- pipeline path ---
            if is_pipeline:
                confirmed = Confirm.ask(
                    "\n[bold yellow]Задача для пайплайна. Запустить?[/bold yellow]",
                    default=True,
                )
                if not confirmed:
                    # Не пайплайн - обрабатываем как чат
                    is_pipeline = False

            if is_pipeline:
                live = spinner_start("Генерирую имя проекта...")
                try:
                    project_dir = await agent.create_project_dir(stripped)
                finally:
                    spinner_stop()

                console.print(f"[green]Проект: {project_dir}[/green]")

                # review_callback - останавливает спиннер, показывает сообщение агента,
                # явно ждёт подтверждения (всегда, независимо от AUTO_CONFIRM)
                async def review_callback(msg: str) -> str:
                    spinner_stop()
                    console.rule("[bold blue]РЕВЬЮ ДОКУМЕНТОВ[/bold blue]")
                    console.print(msg)
                    console.print(
                        "\n[dim]Откройте документы в папке проекта, добавьте "
                        "<!-- COMMENT: текст --> и нажмите Enter, или напишите комментарий здесь.[/dim]"
                    )
                    answer = Prompt.ask("[bold]Ваш ответ[/bold] (пусто = ok)")
                    console.rule()
                    return answer

                live = spinner_start("Выполняю пайплайн...")
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
                        f"[dim]Шагов всего {ver.get('total', 0)}, "
                        f"выполнено {ver.get('completed', 0)}, "
                        f"ошибок {ver.get('failed', 0)}, "
                        f"заблокировано {ver.get('blocked', 0)}[/dim]"
                    )

                if status_val == "needs_clarification":
                    console.print("[yellow]Требуются уточнения:[/yellow]")
                    for q in result.get("questions", []):
                        console.print(f"  - {q}")
                continue

            # --- chat path ---
            live = spinner_start("Думаю...")
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
