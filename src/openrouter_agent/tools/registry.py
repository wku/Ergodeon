from typing import Dict, Type, Any, List
from .base import BaseTool
from .filesystem import (
    ReadFileTool, WriteFileTool, ListDirectoryTool, 
    DeleteFileTool, EditFileTool, EditFileByLinesTool,
    MoveFileTool, GetFileInfoTool, SearchFilesTool, MultiEditFileTool
)
from .system import ExecuteCommandTool, GetCurrentDirectoryTool
from .web import WebFetchTool, WebAPITool
from .code import CodeAnalysisTool
from .reasoning import SequentialThinkingTool
from .json_edit import JSONEditTool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        
        # Filesystem Tools
        self.register(ReadFileTool())
        self.register(WriteFileTool())
        self.register(ListDirectoryTool())
        self.register(DeleteFileTool())
        self.register(EditFileTool())
        self.register(EditFileByLinesTool())
        self.register(MoveFileTool())
        self.register(GetFileInfoTool())
        self.register(SearchFilesTool())
        self.register(MultiEditFileTool())
        
        # System Tools
        self.register(ExecuteCommandTool())
        self.register(GetCurrentDirectoryTool())

        # Web Tools
        self.register(WebFetchTool())
        self.register(WebAPITool())

        # Code Tools
        self.register(CodeAnalysisTool())

        # Reasoning Tools
        self.register(SequentialThinkingTool())

        # JSON Tools
        self.register(JSONEditTool())

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_all_tools(self) -> Dict[str, BaseTool]:
        return self._tools

    def get_openai_schemas(self) -> List[Dict[str, Any]]:
        # Automatically generate accessible schemas using msgspec/type hints if possible
        # For now, we manually map widely used tools or use a helper
        # We will iterate over all tools and generate a basic schema
        # Since we use msgspec, we can try to introspect, but for reliability in this demo,
        # we will continue the manual mapping but expanded.
        
        schemas = []
        for tool in self._tools.values():
            function_def = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            
            # Basic Schema Generation based on tool name (simplified for demo)
            # In a real app, use `msgspec.json.schema(tool.args_schema)`
            if tool.name == "read_file":
                function_def["parameters"] = {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "start_line": {"type": "integer"},
                        "end_line": {"type": "integer"},
                        "show_line_numbers": {"type": "boolean"}
                    },
                    "required": ["path"]
                }
            elif tool.name == "write_file":
                function_def["parameters"] = {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["path", "content"]
                }
            elif tool.name == "edit_file":
                 function_def["parameters"] = {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "old_text": {"type": "string"},
                        "new_text": {"type": "string"}
                    },
                    "required": ["path", "old_text", "new_text"]
                }
            elif tool.name == "edit_file_by_lines":
                 function_def["parameters"] = {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "start_line": {"type": "integer"},
                        "end_line": {"type": "integer"},
                        "new_content": {"type": "string"}
                    },
                    "required": ["path", "start_line", "end_line", "new_content"]
                }
            elif tool.name == "execute_command":
                function_def["parameters"] = {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"},
                        "cwd": {"type": "string"}
                    },
                    "required": ["command"]
                }
            elif tool.name == "list_directory":
                function_def["parameters"] = {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string"},
                        "recursive": {"type": "boolean"}
                    },
                    "required": ["directory"]
                }
            elif tool.name == "delete_file":
                function_def["parameters"] = {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "recursive": {"type": "boolean"}
                    },
                    "required": ["path"]
                }
            elif tool.name == "move_file":
                 function_def["parameters"] = {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string"},
                        "destination": {"type": "string"}
                    },
                    "required": ["source", "destination"]
                }
            elif tool.name == "search_files":
                 function_def["parameters"] = {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string"},
                        "pattern": {"type": "string"},
                         "recursive": {"type": "boolean"}
                    },
                    "required": ["directory", "pattern"]
                }
            elif tool.name == "get_current_directory":
                 function_def["parameters"] = {
                    "type": "object",
                    "properties": {},
                }
            elif tool.name == "web_fetch":
                function_def["parameters"] = {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "extract_text": {"type": "boolean"}
                    },
                    "required": ["url"]
                }
            elif tool.name == "web_api":
                function_def["parameters"] = {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "method": {"type": "string"},
                        "data": {"type": "object"},
                        "headers": {"type": "object"},
                        "timeout": {"type": "integer"}
                    },
                    "required": ["url"]
                }
            elif tool.name == "analyze_code":
                function_def["parameters"] = {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"}
                    },
                    "required": ["path"]
                }
            elif tool.name == "sequential_thinking":
                function_def["parameters"] = {
                    "type": "object",
                    "properties": {
                        "thought": {"type": "string"},
                        "thought_number": {"type": "integer"},
                        "total_thoughts": {"type": "integer"},
                        "next_thought_needed": {"type": "boolean"},
                        "is_revision": {"type": "boolean"},
                        "revises_thought": {"type": "integer"},
                        "branch_from_thought": {"type": "integer"},
                        "branch_id": {"type": "string"},
                        "needs_more_thoughts": {"type": "boolean"}
                    },
                    "required": ["thought", "thought_number", "total_thoughts", "next_thought_needed"]
                }
            elif tool.name == "json_edit":
                function_def["parameters"] = {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string", "enum": ["view", "set", "add", "remove"]},
                        "file_path": {"type": "string"},
                        "json_path": {"type": "string"},
                        "value": {"type": "object"}, # Any type
                        "pretty_print": {"type": "boolean"}
                    },
                    "required": ["operation", "file_path"]
                }
            
            schemas.append({
                "type": "function",
                "function": function_def
            })
            
        return schemas
