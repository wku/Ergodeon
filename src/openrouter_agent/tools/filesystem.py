import os
import shutil
from typing import List, Optional
import msgspec
from pathlib import Path
from .base import BaseTool

# --- Schemas ---

class ReadFileArgs(msgspec.Struct):

    path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    show_line_numbers: bool = False

class WriteFileArgs(msgspec.Struct):
    path: str
    content: str

class ListDirectoryArgs(msgspec.Struct):
    directory: str
    recursive: bool = False

class DeleteFileArgs(msgspec.Struct):
    path: str
    recursive: bool = False

class EditFileArgs(msgspec.Struct):
    path: str
    old_text: str
    new_text: str

class EditFileByLinesArgs(msgspec.Struct):
    path: str
    start_line: int
    end_line: int
    new_content: str

class MultiEditArgs(msgspec.Struct):
    path: str
    edits: List[EditFileArgs] # Reuse EditFileArgs structure for simple replacements

class MoveFileArgs(msgspec.Struct):
    source: str
    destination: str

class GetFileInfoArgs(msgspec.Struct):
    path: str

class SearchFilesArgs(msgspec.Struct):
    directory: str
    pattern: str
    recursive: bool = True



# --- Tools ---

class ReadFileTool(BaseTool[ReadFileArgs]):
    name = "read_file"
    description = "Read content from a file. Can read specific lines."
    args_schema = ReadFileArgs

    async def run(self, args: ReadFileArgs) -> str:
        path = Path(args.path).resolve()
        if not path.exists():
            return f"Error: File {path} does not exist."
        
        try:
            content = path.read_text(encoding="utf-8")
            lines = content.splitlines()
            
            start = (args.start_line - 1) if args.start_line else 0
            end = args.end_line if args.end_line else len(lines)
            
            selected_lines = lines[start:end]
            
            if args.show_line_numbers:
                return "\n".join([f"{i+1+start} | {line}" for i, line in enumerate(selected_lines)])
            
            return "\n".join(selected_lines)
        except Exception as e:
            return f"Error reading file: {e}"

class WriteFileTool(BaseTool[WriteFileArgs]):
    name = "write_file"
    description = "Write content to a file. Creates directories if needed."
    args_schema = WriteFileArgs

    async def run(self, args: WriteFileArgs) -> str:
        path = Path(args.path).resolve()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(args.content, encoding="utf-8")
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {e}"

class ListDirectoryTool(BaseTool[ListDirectoryArgs]):
    name = "list_directory"
    description = "List files and directories."
    args_schema = ListDirectoryArgs

    async def run(self, args: ListDirectoryArgs) -> str:
        root = Path(args.directory).resolve()
        if not root.exists():
            return f"Error: Directory {root} does not exist."
        
        try:
            entries = []
            
            # Common ignored directories
            IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache", ".idea", ".vscode"}
            
            if args.recursive:
                count = 0
                for path in root.rglob("*"):
                    try:
                        rel_path = path.relative_to(root)
                        if any(part in IGNORED_DIRS for part in rel_path.parts):
                            continue
                    except ValueError:
                        continue 

                    prefix = "📁 " if path.is_dir() else "📄 "
                    indent = "    " * (len(rel_path.parts) - 1)
                    entries.append(f"{indent}{prefix}{path.name}")
                    
                    count += 1
                    if count > 1000:
                        entries.append("... (truncated: too many files)")
                        break
            else:
                for path in sorted(root.iterdir()):
                    if path.name in IGNORED_DIRS:
                        continue
                    prefix = "📁 " if path.is_dir() else "📄 "
                    entries.append(f"{prefix}{path.name}")
            
            return "\n".join(entries)
        except Exception as e:
            return f"Error listing directory: {e}"

class DeleteFileTool(BaseTool[DeleteFileArgs]):
    name = "delete_file"
    description = "Delete a file or directory."
    args_schema = DeleteFileArgs

    async def run(self, args: DeleteFileArgs) -> str:
        path = Path(args.path).resolve()
        if not path.exists():
            return f"Error: Path {path} does not exist."
        
        try:
            if path.is_file():
                path.unlink()
                return f"Successfully deleted file: {path}"
            elif path.is_dir():
                if args.recursive:
                    shutil.rmtree(path)
                    return f"Successfully deleted directory: {path}"
                else:
                    path.rmdir()
                    return f"Successfully deleted directory: {path}"
            return "Error: Unknown path type"
        except Exception as e:
            return f"Error deleting: {e}"

class EditFileTool(BaseTool[EditFileArgs]):
    name = "edit_file"
    description = "Edit a file by replacing text."
    args_schema = EditFileArgs

    async def run(self, args: EditFileArgs) -> str:
        path = Path(args.path).resolve()
        if not path.exists():
            return f"Error: File {path} does not exist."
        
        try:
            content = path.read_text(encoding="utf-8")
            if args.old_text not in content:
                # Try with normalized newlines if exact match fails?
                # For now simple string replace
                return f"Error: old_text not found in {path}"
            
            new_content = content.replace(args.old_text, args.new_text)
            path.write_text(new_content, encoding="utf-8")
            return f"Successfully edited {path}"
        except Exception as e:
            return f"Error editing file: {e}"

class EditFileByLinesTool(BaseTool[EditFileByLinesArgs]):
    name = "edit_file_by_lines"
    description = "Replace a range of lines in a file with new content."
    args_schema = EditFileByLinesArgs

    async def run(self, args: EditFileByLinesArgs) -> str:
        path = Path(args.path).resolve()
        if not path.exists():
            return f"Error: File {path} does not exist."
        
        try:
            content = path.read_text(encoding="utf-8")
            lines = content.splitlines()
            total_lines = len(lines)
            
            # Validate lines
            if args.start_line < 1 or args.end_line > total_lines or args.start_line > args.end_line:
                return f"Error: Invalid line range {args.start_line}-{args.end_line} (File has {total_lines} lines)"

            new_lines_content = args.new_content.splitlines()
            
            # Replace lines
            # start_line is 1-based, so index is start_line-1
            # splice: lines[:start-1] + new + lines[end:]
            
            result_lines = lines[:args.start_line-1] + new_lines_content + lines[args.end_line:]
            
            path.write_text("\n".join(result_lines), encoding="utf-8")
            return f"Successfully edited lines {args.start_line}-{args.end_line} in {path}"
        except Exception as e:
            return f"Error editing lines: {e}"

class MoveFileTool(BaseTool[MoveFileArgs]):
    name = "move_file"
    description = "Move or rename a file or directory."
    args_schema = MoveFileArgs

    async def run(self, args: MoveFileArgs) -> str:
        src = Path(args.source).resolve()
        dst = Path(args.destination).resolve()
        
        if not src.exists():
            return f"Error: Source {src} does not exist."
        
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            return f"Successfully moved {src} to {dst}"
        except Exception as e:
            return f"Error moving file: {e}"

class GetFileInfoTool(BaseTool[GetFileInfoArgs]):
    name = "get_file_info"
    description = "Get information about a file or directory."
    args_schema = GetFileInfoArgs

    async def run(self, args: GetFileInfoArgs) -> str:
        path = Path(args.path).resolve()
        if not path.exists():
            return f"Error: Path {path} does not exist."
        
        try:
            stats = path.stat()
            type_str = "Directory" if path.is_dir() else "File"
            size_str = f"{stats.st_size} bytes"
            return f"Path: {path}\nType: {type_str}\nSize: {size_str}\nPermissions: {oct(stats.st_mode)[-3:]}"
        except Exception as e:
            return f"Error getting info: {e}"

class SearchFilesTool(BaseTool[SearchFilesArgs]):
    name = "search_files"
    description = "Search for files searching the pattern in the name."
    args_schema = SearchFilesArgs

    async def run(self, args: SearchFilesArgs) -> str:
        root = Path(args.directory).resolve()
        if not root.exists():
            return f"Error: Directory {root} does not exist."
        
        try:
            results = []
            if args.recursive:
                for path in root.rglob(args.pattern):
                    results.append(str(path))
            else:
                for path in root.glob(args.pattern):
                    results.append(str(path))
            
            if not results:
                return "No files found."
            return "\n".join(results[:50]) # Limit to 50
        except Exception as e:
            return f"Error searching files: {e}"

class MultiEditFileTool(BaseTool[MultiEditArgs]):
    name = "multi_edit_file"
    description = "Perform multiple text replacements in a single file."
    args_schema = MultiEditArgs

    async def run(self, args: MultiEditArgs) -> str:
        path = Path(args.path).resolve()
        if not path.exists():
            return f"Error: File {path} does not exist."
        
        try:
            content = path.read_text(encoding="utf-8")
            original_content = content
            
            for edit in args.edits:
                if edit.old_text not in content:
                    return f"Error: old_text '{edit.old_text}' not found (aborted all edits)"
                content = content.replace(edit.old_text, edit.new_text)
            
            if content == original_content:
                return "Warning: No changes made"
            
            path.write_text(content, encoding="utf-8")
            return f"Successfully applied {len(args.edits)} edits to {path}"
        except Exception as e:
            return f"Error applying multi-edits: {e}"


