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

try:
    from openrouter_agent.agent.core import Agent
    from openrouter_agent.agent.config import PipelineConfig
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    from openrouter_agent.agent.core import Agent
    from openrouter_agent.agent.config import PipelineConfig

console = Console()


def _build_confirmation_callback(auto_confirm: bool):
    """
    Возвращает коллбэк подтверждения опасных операций.
    При auto_confirm=True подтверждает без интерактивного запроса.
    """
    if auto_confirm:
        async def _auto(tool_name: str, args: Any) -> bool:
            logging.getLogger(__name__).info(f"AUTO_CONFIRM: {tool_name}")
            return True
        return _auto

    async def _interactive(tool_name: str, args: Any) -> bool:
        console.print(f"\n[bold red]⚠️  DANGEROUS ACTION DETECTED[/bold red]")
        console.print(f"Tool: [cyan]{tool_name}[/cyan]")
        console.print(f"Arguments: {args}")
        return Confirm.ask("Do you want to proceed?")

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
            console.print("[red]API Key is required to run the agent.[/red]")
            return

    auto_confirm = os.getenv("AUTO_CONFIRM", "false").strip().lower() in ("true", "1", "yes")
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")

    if auto_confirm:
        console.print("[dim]AUTO_CONFIRM включён - опасные операции подтверждаются автоматически[/dim]")

    agent = Agent(
        api_key=api_key,
        model=model,
        confirmation_callback=_build_confirmation_callback(auto_confirm),
        pipeline_config=PipelineConfig.from_env(),
    )

    console.print(Panel.fit(
        "[bold green]OpenRouter Agent (Python)[/bold green]\n"
        "Type 'exit' or 'quit' to stop.\n"
        "Type 'reset' to clear active project context.",
        style="blue",
    ))

    while True:
        try:
            user_input = Prompt.ask("\n[bold]User[/bold]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Exiting...[/yellow]")
            break

        stripped = user_input.strip()
        if not stripped:
            continue

        if stripped.lower() in ("exit", "quit"):
            console.print("[yellow]Exiting...[/yellow]")
            break

        # Сброс активного проекта и истории диалога
        if stripped.lower() == "reset":
            agent.active_project_dir = None
            agent.history.clear()
            console.print("[dim]Контекст активного проекта сброшен.[/dim]")
            continue

        try:
            with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
                is_pipeline = await agent.detect_pipeline_request(stripped)

            if is_pipeline:
                confirmed = Confirm.ask(
                    "\n[bold yellow]Похоже, что это задача для пайплайна. "
                    "Запустить пайплайн генерации проекта?[/bold yellow]"
                )
                if confirmed:
                    with console.status("[bold green]Генерирую имя проекта...[/bold green]", spinner="dots"):
                        project_dir = await agent.create_project_dir(stripped)
                    console.print(f"[green]Проект будет создан в: {project_dir}[/green]")

                    async def review_callback(msg: str) -> str:
                        console.print(f"\n[bold blue]АГЕНТ:[/bold blue] {msg}")
                        return Prompt.ask("[bold]Ваш ответ (или 'ok')[/bold]")

                    with console.status("[bold green]Выполняю пайплайн...[/bold green]", spinner="dots"):
                        result = await agent.run_pipeline(project_dir, stripped, review_callback)

                    status_val = result.get("status", "unknown")
                    color = "green" if status_val == "success" else "yellow" if status_val == "partial_success" else "red"
                    console.print(f"\n[bold {color}]Пайплайн завершен со статусом: {status_val}[/bold {color}]")

                    verification = result.get("stages", {}).get("verification", {})
                    if verification:
                        console.print(
                            f"[dim]Шагов: {verification.get('total', 0)}, "
                            f"выполнено: {verification.get('completed', 0)}, "
                            f"ошибок: {verification.get('failed', 0)}[/dim]"
                        )

                    if result.get("status") == "needs_clarification":
                        console.print("[yellow]Требуются уточнения:[/yellow]")
                        for q in result.get("questions", []):
                            console.print(f"  - {q}")
                    continue

                # Пользователь отказался от пайплайна - обрабатываем как обычный чат

            with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
                response = await agent.chat(stripped)

            console.print("\n[bold]Agent:[/bold]")
            console.print(Markdown(response))

        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting...[/yellow]")
            break
        except Exception as e:
            logging.getLogger(__name__).error(f"error: {e}", exc_info=True)
            console.print(f"\n[red]Error:[/red] {e}")


if __name__ == "__main__":
    asyncio.run(main())
