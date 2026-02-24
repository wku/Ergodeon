#!/usr/bin/env python3
"""CLI для Ergodeon через UnifiedRouter."""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from openrouter_agent.agent.unified_router import UnifiedRouter, ProgressCallback, RequestResult
from openrouter_agent.agent.config import PipelineConfig

console = Console()
log = logging.getLogger(__name__)


class CLIProgress(ProgressCallback):
    def __init__(self):
        self._console = console

    async def on_phase_start(self, phase: str, desc: str):
        self._console.print(f"\n[bold cyan]>> Фаза: {phase}[/] {desc}")

    async def on_step_start(self, step_num, total: int, desc: str):
        self._console.print(f"  [dim]Шаг {step_num}/{total}:[/] {desc}")

    async def on_step_done(self, step_num, status: str):
        color = "green" if status == "completed" else "red" if status == "failed" else "yellow"
        self._console.print(f"  [{color}]{status}[/]")

    async def on_message(self, text: str, msg_type: str = "system"):
        self._console.print(f"[dim]{text}[/]")

    async def on_review_request(self, msg: str) -> str:
        self._console.print(Panel(msg, title="Review", border_style="yellow"))
        return Prompt.ask("[yellow]Комментарии (Enter = ok)[/]", default="ok")

    async def on_done(self, status: str):
        color = "green" if status == "completed" else "red" if "fail" in status else "yellow"
        self._console.print(f"\n[bold {color}]Результат: {status}[/]")


async def _confirm_dangerous(tool_name: str, args) -> bool:
    console.print(f"\n[bold red]Подтвердите {tool_name}[/]")
    console.print(f"  args: {args}")
    resp = Prompt.ask("[red]Выполнить? (y/n)[/]", default="n")
    return resp.lower() in ("y", "yes", "да")


def _show_result(r: RequestResult):
    if r.workflow == "chat":
        console.print(f"\n{r.message}")
    elif r.status == "completed":
        console.print(Panel(
            f"Workflow: {r.workflow}\nStage: {r.stage_num}\n{r.message or 'Готово'}",
            title="Completed", border_style="green",
        ))
    elif r.status in ("needs_clarification", "needs_project"):
        console.print(Panel(r.message, title="Нужно уточнение", border_style="yellow"))
    else:
        console.print(Panel(
            f"Workflow: {r.workflow}\nStage: {r.stage_num}\n{r.message or r.status}",
            title=r.status, border_style="red",
        ))
    data = r.data
    if data and "phases" in data and "implementation" in data["phases"]:
        impl = data["phases"]["implementation"]
        console.print(
            f"  Шагов: {impl.get('total', 0)}, "
            f"выполнено: {impl.get('completed', 0)}, "
            f"ошибок: {impl.get('failed', 0)}, "
            f"заблокировано: {impl.get('blocked', 0)}"
        )


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ergodeon CLI")
    parser.add_argument("--project", "-p", help="Путь к проекту")
    parser.add_argument("--resume", "-r", action="store_true", help="Возобновить последний стейдж")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        console.print("[red]OPENROUTER_API_KEY не задан[/]")
        sys.exit(1)

    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
    config = PipelineConfig.from_env()
    auto_confirm = os.getenv("AUTO_CONFIRM", "false").lower() == "true"

    router = UnifiedRouter(
        api_key=api_key,
        model=model,
        confirmation_callback=None if auto_confirm else _confirm_dangerous,
        pipeline_config=config,
        progress=CLIProgress(),
    )

    if args.project:
        r = await router.handle_request(f"project {args.project}")
        _show_result(r)

    if args.resume:
        r = await router.handle_request("resume")
        _show_result(r)
        return

    console.print(Panel(
        "Ergodeon AI Agent\nВведите запрос или 'quit' для выхода",
        border_style="blue",
    ))

    while True:
        try:
            text = Prompt.ask("\n[bold blue]>[/]")
        except (EOFError, KeyboardInterrupt):
            break
        if text.strip().lower() in ("quit", "exit", "q"):
            break
        if not text.strip():
            continue
        try:
            r = await router.handle_request(text)
            _show_result(r)
        except Exception as e:
            console.print(f"[red]Ошибка: {e}[/]")
            log.exception("CLI error")


if __name__ == "__main__":
    asyncio.run(main())
