import asyncio
import os
import shutil
from pathlib import Path
from openrouter_agent.tools.registry import ToolRegistry
from openrouter_agent.tools.filesystem import EditFileByLinesArgs, MoveFileArgs, SearchFilesArgs, MultiEditArgs, EditFileArgs
from openrouter_agent.tools.system import ExecuteCommandArgs
import shutil

async def verify_advanced_tools():
    print("Verifying Advanced Tools...")
    registry = ToolRegistry()
    
    test_dir = Path("demo_test_advanced")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    try:
        # Setup: Create some files
        file1 = test_dir / "file1.txt"
        file1.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")
        file2 = test_dir / "file2.txt"
        file2.write_text("To be moved")
        
        # 1. Test Execute Command
        print("\n[Test] Execute Command")
        exec_tool = registry.get("execute_command")
        result = await exec_tool.run(exec_tool.validate_args({
            "command": f"ls -l {str(test_dir)}"
        }))
        print(f"Command Output:\n{result}")
        assert "file1.txt" in result
        print("✅ Execute Command Passed")

        # 2. Test Edit File By Lines
        print("\n[Test] Edit File By Lines")
        edit_lines_tool = registry.get("edit_file_by_lines")
        # Replace lines 2-4
        result = await edit_lines_tool.run(edit_lines_tool.validate_args({
            "path": str(file1),
            "start_line": 2,
            "end_line": 4,
            "new_content": "New Line A\nNew Line B"
        }))
        content = file1.read_text()
        print(f"Content:\n{content}")
        assert "New Line A" in content
        assert "Line 3" not in content
        assert "Line 5" in content
        print("✅ Edit File By Lines Passed")

        # 3. Test Move File
        print("\n[Test] Move File")
        move_tool = registry.get("move_file")
        file2_moved = test_dir / "subdir" / "file2_moved.txt"
        result = await move_tool.run(move_tool.validate_args({
            "source": str(file2),
            "destination": str(file2_moved)
        }))
        assert not file2.exists()
        assert file2_moved.exists()
        assert file2_moved.read_text() == "To be moved"
        print("✅ Move File Passed")

        # 4. Test Multi Edit
        print("\n[Test] Multi Edit")
        multi_tool = registry.get("multi_edit_file")
        # Reuse file1: 
        # Line 1
        # New Line A
        # New Line B
        # Line 5
        
        result = await multi_tool.run(multi_tool.validate_args({
            "path": str(file1),
            "edits": [
                {"path": str(file1), "old_text": "Line 1", "new_text": "Header"},
                {"path": str(file1), "old_text": "Line 5", "new_text": "Footer"}
            ]
        }))
        content = file1.read_text()
        print(f"Content:\n{content}")
        assert "Header" in content
        assert "Footer" in content
        print("✅ Multi Edit Passed")

        # 5. Test Search Files
        print("\n[Test] Search Files")
        search_tool = registry.get("search_files")
        result = await search_tool.run(search_tool.validate_args({
            "directory": str(test_dir),
            "pattern": "*moved*"
        }))
        print(f"Search Result: {result}")
        assert "file2_moved.txt" in result
        print("✅ Search Files Passed")

    finally:
        if test_dir.exists():
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    asyncio.run(verify_advanced_tools())
