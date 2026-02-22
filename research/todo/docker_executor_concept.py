import os
import subprocess
import uuid
import json
from typing import Any, List, Optional, Tuple

# Note: This is a concept file consolidated from `trae-agent-main`'s `docker_manager.py` and `docker_tool_executor.py`.
# It simplifies dependencies to show the core logic of managing Docker containers and executing tools within them.
# Real usage would require `docker` library (`pip install docker`) and `pexpect`.

try:
    import docker
    from docker.errors import DockerException, ImageNotFound, NotFound
    import pexpect
except ImportError:
    # Adding placeholders for linting/concept purposes if dependencies aren't installed
    docker = Any
    DockerException = Exception
    ImageNotFound = Exception
    NotFound = Exception
    pexpect = Any


class DockerManager:
    """
    Manages Docker container lifecycle and command execution for the agent.
    Supports both stateless (non-interactive) and stateful (interactive) modes.
    """

    CONTAINER_TOOLS_PATH = "/agent_tools"

    def __init__(
        self,
        image: str | None = None,
        container_id: str | None = None,
        dockerfile_path: str | None = None,
        workspace_dir: str | None = None,
        tools_dir: str | None = None,
    ):
        self.client = docker.from_env()
        self.image = image
        self.container_id = container_id
        self.dockerfile_path = dockerfile_path
        self.workspace_dir = workspace_dir
        self.tools_dir = tools_dir
        self.container_workspace = "/workspace"
        self.container = None
        self.shell = None
        self._is_managed = True

    def start(self):
        """Starts/attaches to the container, mounts the workspace, copies tools, and starts the shell."""
        try:
            # 1. Build Image if needed
            if self.dockerfile_path:
                build_context = os.path.dirname(self.dockerfile_path)
                unique_tag = f"agent-custom:{uuid.uuid4()}"
                print(f"Building Docker image from '{self.dockerfile_path}'...")
                new_image, _ = self.client.images.build(
                    path=build_context, tag=unique_tag, rm=True
                )
                self.image = new_image.tags[0]

            # 2. Start Container
            if self.container_id:
                print(f"Attaching to existing container: {self.container_id}...")
                self.container = self.client.containers.get(self.container_id)
                self._is_managed = False
            elif self.image:
                print(f"Starting new container from image: {self.image}...")
                volumes = {}
                if self.workspace_dir:
                    os.makedirs(self.workspace_dir, exist_ok=True)
                    volumes[os.path.abspath(self.workspace_dir)] = {
                        "bind": self.container_workspace,
                        "mode": "rw",
                    }
                
                self.container = self.client.containers.run(
                    self.image,
                    command="sleep infinity",
                    detach=True,
                    volumes=volumes,
                    working_dir=self.container_workspace,
                )
                self.container_id = self.container.id
                self._is_managed = True
            
            # 3. Copy Tools
            self._copy_tools_to_container()
            
            # 4. Start Shell
            self._start_persistent_shell()
            
        except Exception as e:
            print(f"Failed to start DockerManager: {e}")
            raise

    def stop(self):
        """Stops the shell and container."""
        if self.shell and self.shell.isalive():
            self.shell.close(force=True)
        
        if self.container and self._is_managed:
            try:
                self.container.stop()
                self.container.remove()
            except Exception as e:
                print(f"Warning: Could not cleanup container: {e}")

    def execute_interactive(self, command: str, timeout: int = 300) -> Tuple[int, str]:
        """Executes a command within the existing persistent shell."""
        if not self.shell or not self.shell.isalive():
            self._start_persistent_shell()

        marker = "---CMD_DONE---"
        full_command = command.strip()
        marker_command = f"echo {marker}$?"
        
        self.shell.sendline(full_command)
        self.shell.sendline(marker_command)
        
        try:
            self.shell.expect(marker + r"(\d+)", timeout=timeout)
        except pexpect.exceptions.TIMEOUT:
            return -1, f"Timeout after {timeout}s. Partial output:\n{self.shell.before}"
            
        exit_code = int(self.shell.match.group(1))
        output = self.shell.before
        
        # Clean output (remove command echo and marker)
        clean_lines = [
            line for line in output.splitlines() 
            if line.strip() != full_command and marker_command not in line
        ]
        return exit_code, "\n".join(clean_lines).strip()

    def _copy_tools_to_container(self):
        """Copies local tools to container."""
        if not self.tools_dir or not os.path.isdir(self.tools_dir):
            return
            
        cmd = f"docker cp '{os.path.abspath(self.tools_dir)}' '{self.container.id}:{self.CONTAINER_TOOLS_PATH}'"
        subprocess.run(cmd, shell=True, check=True, capture_output=True)

    def _start_persistent_shell(self):
        """Spawns a persistent bash shell inside the container using pexpect."""
        if not self.container: return
        command = f"docker exec -it {self.container.id} /bin/bash"
        self.shell = pexpect.spawn(command, encoding="utf-8", timeout=120)
        self.shell.expect([r"\$", r"#"], timeout=120)


class DockerToolExecutor:
    """
    Routes specific tool calls to the Docker container while executing others locally.
    """
    
    def __init__(
        self,
        docker_manager: DockerManager,
        docker_tools: List[str], # List of tool names to run in Docker
        host_workspace_dir: str | None,
        container_workspace_dir: str,
    ):
        self.docker_manager = docker_manager
        self.docker_tools_set = set(docker_tools)
        self.host_workspace_dir = os.path.abspath(host_workspace_dir) if host_workspace_dir else None
        self.container_workspace_dir = container_workspace_dir

    def execute_tool(self, tool_name: str, arguments: dict) -> Any:
        # Check if this tool should run in Docker
        if tool_name in self.docker_tools_set:
            return self._execute_in_docker(tool_name, arguments)
        else:
            # Fallback to local execution (implementation not shown here)
            return f"Executing {tool_name} locally..."

    def _translate_path(self, host_path: str) -> str:
        """Translates host path to container path."""
        if not self.host_workspace_dir:
            return host_path
            
        abs_host_path = os.path.abspath(host_path)
        if os.path.commonpath([abs_host_path, self.host_workspace_dir]) == self.host_workspace_dir:
            relative_path = os.path.relpath(abs_host_path, self.host_workspace_dir)
            return os.path.join(self.container_workspace_dir, relative_path)
            
        return host_path

    def _execute_in_docker(self, tool_name: str, arguments: dict) -> str:
        """Builds command and executes in Docker."""
        
        # 1. Translate paths in arguments
        processed_args = arguments.copy()
        if "path" in processed_args and isinstance(processed_args["path"], str):
            processed_args["path"] = self._translate_path(processed_args["path"])
            
        # 2. Build Command logic (Simplified)
        command_to_run = ""
        
        if tool_name == "bash":
            command_to_run = processed_args.get("command", "")
            
        elif tool_name == "edit_file":
            # Example: map to a CLI tool inside container
            exe = f"{self.docker_manager.CONTAINER_TOOLS_PATH}/edit_tool"
            # Construct CLI args...
            command_to_run = f"{exe} --path '{processed_args.get('path')}' ..."
            
        else:
            raise NotImplementedError(f"Docker logic for {tool_name} not implemented.")

        # 3. Execute
        exit_code, output = self.docker_manager.execute_interactive(command_to_run)
        
        if exit_code == 0:
            return output
        else:
            raise RuntimeError(f"Tool execution failed: {output}")
