"""
Tool Registry
Manages all available tools and their execution
"""

import asyncio
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
from enum import Enum


class ToolCategory(str, Enum):
    """Tool categories"""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    CODE_EDIT = "code_edit"
    SHELL = "shell"
    DIAGNOSTICS = "diagnostics"
    SEARCH = "search"
    USER_INPUT = "user_input"
    SUBAGENT = "subagent"


class ToolPermission(str, Enum):
    """Permission levels"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class Tool:
    """Tool definition"""
    
    def __init__(
        self,
        name: str,
        category: ToolCategory,
        handler: Callable,
        description: str = "",
        required_permission: ToolPermission = ToolPermission.READ,
        async_handler: bool = True
    ):
        self.name = name
        self.category = category
        self.handler = handler
        self.description = description
        self.required_permission = required_permission
        self.async_handler = async_handler
        self.execution_count = 0
        self.last_executed: Optional[datetime] = None
    
    async def execute(self, params: Dict[str, Any], agent_name: str) -> Any:
        """Execute tool"""
        self.execution_count += 1
        self.last_executed = datetime.now()
        
        if self.async_handler:
            return await self.handler(params, agent_name)
        else:
            return self.handler(params, agent_name)


class ToolRegistry:
    """Registry for all tools"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.agent_permissions: Dict[str, List[str]] = {}
        self.execution_log: List[Dict[str, Any]] = []
    
    async def initialize(self) -> None:
        """Initialize registry and register default tools"""
        await self._register_default_tools()
    
    def register_tool(self, tool: Tool) -> None:
        """Register a tool"""
        self.tools[tool.name] = tool
    
    def grant_permission(self, agent_name: str, tool_names: List[str]) -> None:
        """Grant tool permissions to agent"""
        if agent_name not in self.agent_permissions:
            self.agent_permissions[agent_name] = []
        
        self.agent_permissions[agent_name].extend(tool_names)
    
    def has_permission(self, agent_name: str, tool_name: str) -> bool:
        """Check if agent has permission for tool"""
        if agent_name not in self.agent_permissions:
            return False
        
        return tool_name in self.agent_permissions[agent_name]
    
    async def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        agent_name: str
    ) -> Any:
        """Execute a tool"""
        
        # Check tool exists
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found")
        
        # Check permission
        if not self.has_permission(agent_name, tool_name):
            raise PermissionError(
                f"Agent {agent_name} does not have permission for tool {tool_name}"
            )
        
        # Log execution
        log_entry = {
            'tool': tool_name,
            'agent': agent_name,
            'timestamp': datetime.now(),
            'params': params
        }
        
        try:
            result = await tool.execute(params, agent_name)
            log_entry['status'] = 'success'
            log_entry['result'] = result
            return result
        except Exception as error:
            log_entry['status'] = 'failed'
            log_entry['error'] = str(error)
            raise
        finally:
            self.execution_log.append(log_entry)
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get tool by name"""
        return self.tools.get(tool_name)
    
    def get_tools_by_category(self, category: ToolCategory) -> List[Tool]:
        """Get all tools in category"""
        return [tool for tool in self.tools.values() if tool.category == category]
    
    def get_agent_tools(self, agent_name: str) -> List[Tool]:
        """Get all tools available to agent"""
        if agent_name not in self.agent_permissions:
            return []
        
        tool_names = self.agent_permissions[agent_name]
        return [self.tools[name] for name in tool_names if name in self.tools]
    
    async def _register_default_tools(self) -> None:
        """Register default tools"""
        
        # File read tools
        self.register_tool(Tool(
            name="readFile",
            category=ToolCategory.FILE_READ,
            handler=self._read_file,
            description="Read file content",
            required_permission=ToolPermission.READ
        ))
        
        self.register_tool(Tool(
            name="readMultipleFiles",
            category=ToolCategory.FILE_READ,
            handler=self._read_multiple_files,
            description="Read multiple files",
            required_permission=ToolPermission.READ
        ))
        
        self.register_tool(Tool(
            name="listDirectory",
            category=ToolCategory.FILE_READ,
            handler=self._list_directory,
            description="List directory contents",
            required_permission=ToolPermission.READ
        ))
        
        # File write tools
        self.register_tool(Tool(
            name="fsWrite",
            category=ToolCategory.FILE_WRITE,
            handler=self._write_file,
            description="Write file",
            required_permission=ToolPermission.WRITE
        ))
        
        self.register_tool(Tool(
            name="fsAppend",
            category=ToolCategory.FILE_WRITE,
            handler=self._append_file,
            description="Append to file",
            required_permission=ToolPermission.WRITE
        ))
        
        self.register_tool(Tool(
            name="deleteFile",
            category=ToolCategory.FILE_WRITE,
            handler=self._delete_file,
            description="Delete file",
            required_permission=ToolPermission.WRITE
        ))
        
        # Code edit tools
        self.register_tool(Tool(
            name="editCode",
            category=ToolCategory.CODE_EDIT,
            handler=self._edit_code,
            description="Edit code using AST",
            required_permission=ToolPermission.WRITE
        ))
        
        self.register_tool(Tool(
            name="strReplace",
            category=ToolCategory.CODE_EDIT,
            handler=self._str_replace,
            description="String replacement in file",
            required_permission=ToolPermission.WRITE
        ))
        
        # Shell tools
        self.register_tool(Tool(
            name="executeBash",
            category=ToolCategory.SHELL,
            handler=self._execute_bash,
            description="Execute bash command",
            required_permission=ToolPermission.EXECUTE
        ))
        
        # Search tools
        self.register_tool(Tool(
            name="grepSearch",
            category=ToolCategory.SEARCH,
            handler=self._grep_search,
            description="Search in files",
            required_permission=ToolPermission.READ
        ))
        
        self.register_tool(Tool(
            name="fileSearch",
            category=ToolCategory.SEARCH,
            handler=self._file_search,
            description="Search for files",
            required_permission=ToolPermission.READ
        ))
    
    # Tool implementations (stubs - would be implemented with actual logic)
    
    async def _read_file(self, params: Dict[str, Any], agent: str) -> str:
        """Read file implementation"""
        # Actual implementation would read from filesystem
        return f"File content from {params.get('path')}"
    
    async def _read_multiple_files(self, params: Dict[str, Any], agent: str) -> Dict[str, str]:
        """Read multiple files implementation"""
        return {path: f"Content of {path}" for path in params.get('paths', [])}
    
    async def _list_directory(self, params: Dict[str, Any], agent: str) -> List[str]:
        """List directory implementation"""
        return ["file1.py", "file2.py", "dir1/"]
    
    async def _write_file(self, params: Dict[str, Any], agent: str) -> str:
        """Write file implementation"""
        return f"Written to {params.get('path')}"
    
    async def _append_file(self, params: Dict[str, Any], agent: str) -> str:
        """Append to file implementation"""
        return f"Appended to {params.get('path')}"
    
    async def _delete_file(self, params: Dict[str, Any], agent: str) -> str:
        """Delete file implementation"""
        return f"Deleted {params.get('path')}"
    
    async def _edit_code(self, params: Dict[str, Any], agent: str) -> str:
        """Edit code implementation"""
        return f"Edited {params.get('path')}"
    
    async def _str_replace(self, params: Dict[str, Any], agent: str) -> str:
        """String replace implementation"""
        return f"Replaced in {params.get('path')}"
    
    async def _execute_bash(self, params: Dict[str, Any], agent: str) -> str:
        """Execute bash implementation"""
        return f"Executed: {params.get('command')}"
    
    async def _grep_search(self, params: Dict[str, Any], agent: str) -> List[Dict[str, Any]]:
        """Grep search implementation"""
        return [{"file": "test.py", "line": 10, "content": "match"}]
    
    async def _file_search(self, params: Dict[str, Any], agent: str) -> List[str]:
        """File search implementation"""
        return ["path/to/file.py"]
