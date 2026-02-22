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
from rich.status import Status

# Ensure we can import from src
# In installed package mode this might not be needed but for dev it helps
try:
    from openrouter_agent.agent.core import Agent
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    from openrouter_agent.agent.core import Agent

# Global status object to be controlled by callback
console = Console()
status = console.status("[bold green]Thinking...[/bold green]", spinner="dots")

async def confirmation_callback(tool_name: str, args: Any) -> bool:
    # Stop spinner to allow user input
    status.stop()
    console.print(f"\n[bold red]⚠️  DANGEROUS ACTION DETECTED[/bold red]")
    console.print(f"Tool: [cyan]{tool_name}[/cyan]")
    console.print(f"Arguments: {args}")
    
    # Force print to ensure it's visible
    result = Confirm.ask("Do you want to proceed?")
    
    # Restart spinner execution resumes
    status.start()
    return result

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, markup=True)]
    )
    load_dotenv()
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        api_key = Prompt.ask("Enter your OpenRouter API Key", password=True)
        if not api_key:
            console.print("[red]API Key is required to run the agent.[/red]")
            return

    console.print(Panel.fit("[bold green]OpenRouter Agent (Python)[/bold green]\nType 'exit' or 'quit' to stop.", style="blue"))

    agent = Agent(
        api_key=api_key, 
        model="openai/gpt-4o",
        confirmation_callback=confirmation_callback
    )

    while True:
        try:
            user_input = Prompt.ask("\n[bold user]User[/bold user]")
            if user_input.lower() in ("exit", "quit"):
                break
            
            status.start()
            try:
                is_pipeline = await agent.detect_pipeline_request(user_input)
            finally:
                status.stop()

            if is_pipeline:
                confirmed = Confirm.ask("\n[bold yellow]Похоже, что это задача для пайплайна. Запустить пайплайн генерации проекта?[/bold yellow]")
                if confirmed:
                    project_dir = await agent.create_project_dir(user_input)
                    console.print(f"[green]Проект будет создан в: {project_dir}[/green]")
                    
                    async def review_callback(msg: str) -> str:
                        status.stop()
                        console.print(f"\n[bold blue]АГЕНТ:[/bold blue] {msg}")
                        user_resp = Prompt.ask("[bold user]Ваш ответ (или 'ok')[/bold user]")
                        status.start()
                        return user_resp

                    status.start()
                    try:
                        result = await agent.run_pipeline(project_dir, user_input, review_callback)
                        console.print(f"\n[bold green]Пайплайн завершен со статусом:[/bold green] {result['status']}")
                    finally:
                        status.stop()
                    continue

            status.start()
            try:
                response = await agent.chat(user_input)
            finally:
                status.stop()
            
            console.print("\n[bold assistant]Agent:[/bold assistant]")
            console.print(Markdown(response))
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting...[/yellow]")
            break
        except Exception as e:
            status.stop()
            console.print(f"\n[red]Error:[/red] {e}")

if __name__ == "__main__":
    asyncio.run(main())
