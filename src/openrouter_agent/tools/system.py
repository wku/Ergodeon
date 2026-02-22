import os
import subprocess
import msgspec
from typing import Optional
from .base import BaseTool

class ExecuteCommandArgs(msgspec.Struct):
    command: str
    cwd: Optional[str] = None

class GetCurrentDirectoryArgs(msgspec.Struct):
    pass

class ExecuteCommandTool(BaseTool[ExecuteCommandArgs]):
    name = "execute_command"
    description = "Execute a shell command."
    args_schema = ExecuteCommandArgs

    async def run(self, args: ExecuteCommandArgs) -> str:
        cwd = args.cwd if args.cwd else os.getcwd()
        try:
            # Capture both stdout and stderr
            result = subprocess.run(
                args.command, 
                shell=True, 
                cwd=cwd, 
                text=True, 
                capture_output=True,
                timeout=60 # Default timeout 60s
            )
            output = result.stdout
            if result.stderr:
                output += f"\nstderr:\n{result.stderr}"
            return output if output.strip() else "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error executing command: {e}"

class GetCurrentDirectoryTool(BaseTool[GetCurrentDirectoryArgs]):
    name = "get_current_directory"
    description = "Get the current working directory."
    args_schema = GetCurrentDirectoryArgs

    async def run(self, args: GetCurrentDirectoryArgs) -> str:
        return os.getcwd()
