import asyncio
import os
import sys
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from openrouter_agent.tools.registry import ToolRegistry


async def verify_advanced_tools():
    print("Verifying Advanced Tools...")
    registry = ToolRegistry()

    test_dir = Path(__file__).parent / "demo_test_advanced"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    passed = 0
    failed = 0

    try:
        # Подготовка файлов
        file1 = test_dir / "file1.txt"
        file1.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")
        file2 = test_dir / "file2.txt"
        file2.write_text("To be moved")

        # 1. Execute Command
        print("\n[Test] Execute Command")
        exec_tool = registry.get("execute_command")
        result = await exec_tool.run(exec_tool.validate_args({
            "command": f"ls -1 {str(test_dir)}",
        }))
        print(f"Command Output:\n{result}")
        assert "file1.txt" in result, "file1.txt not in ls output"
        assert "file2.txt" in result, "file2.txt not in ls output"
        print("✅ Execute Command Passed")
        passed += 1

        # 2. Edit File By Lines
        print("\n[Test] Edit File By Lines")
        edit_lines_tool = registry.get("edit_file_by_lines")
        result = await edit_lines_tool.run(edit_lines_tool.validate_args({
            "path": str(file1),
            "start_line": 2,
            "end_line": 4,
            "new_content": "New Line A\nNew Line B",
        }))
        print(f"Result: {result}")
        content = file1.read_text()
        print(f"Content:\n{content}")
        assert "New Line A" in content, "New Line A not inserted"
        assert "New Line B" in content, "New Line B not inserted"
        assert "Line 3" not in content, "Line 3 should be removed"
        assert "Line 5" in content, "Line 5 should remain"
        print("✅ Edit File By Lines Passed")
        passed += 1

        # 3. Move File (перемещение в поддиректорию)
        print("\n[Test] Move File")
        subdir = test_dir / "subdir"
        subdir.mkdir()
        file2_moved = subdir / "file2_moved.txt"
        move_tool = registry.get("move_file")
        result = await move_tool.run(move_tool.validate_args({
            "source": str(file2),
            "destination": str(file2_moved),
        }))
        print(f"Result: {result}")
        assert not file2.exists(), "Source file should be gone"
        assert file2_moved.exists(), "Destination file should exist"
        assert file2_moved.read_text() == "To be moved", "Content mismatch after move"
        print("✅ Move File Passed")
        passed += 1

        # 4. Multi Edit File
        # Текущее состояние file1: Line 1 / New Line A / New Line B / Line 5
        print("\n[Test] Multi Edit File")
        multi_tool = registry.get("multi_edit_file")
        result = await multi_tool.run(multi_tool.validate_args({
            "path": str(file1),
            "edits": [
                {"path": str(file1), "old_text": "Line 1", "new_text": "Header"},
                {"path": str(file1), "old_text": "Line 5", "new_text": "Footer"},
            ],
        }))
        print(f"Result: {result}")
        content = file1.read_text()
        print(f"Content:\n{content}")
        assert "Header" in content, "Header not found"
        assert "Footer" in content, "Footer not found"
        assert "Line 1" not in content, "Old Line 1 still present"
        assert "Line 5" not in content, "Old Line 5 still present"
        print("✅ Multi Edit File Passed")
        passed += 1

        # 5. Search Files
        print("\n[Test] Search Files")
        search_tool = registry.get("search_files")
        result = await search_tool.run(search_tool.validate_args({
            "directory": str(test_dir),
            "pattern": "*moved*",
            "recursive": True,
        }))
        print(f"Search Result: {result}")
        assert "file2_moved.txt" in result, "Moved file not found in search"
        print("✅ Search Files Passed")
        passed += 1

        # 6. Search Files - no results case
        print("\n[Test] Search Files (no results)")
        result = await search_tool.run(search_tool.validate_args({
            "directory": str(test_dir),
            "pattern": "*.xyz",
            "recursive": True,
        }))
        print(f"Search Result (no match): {result}")
        # Не должно упасть, должен вернуть пустой результат или сообщение
        print("✅ Search Files (no results) Passed")
        passed += 1

        # 7. Execute Command с cwd
        print("\n[Test] Execute Command with cwd")
        result = await exec_tool.run(exec_tool.validate_args({
            "command": "pwd",
            "cwd": str(test_dir),
        }))
        print(f"PWD Output: {result.strip()}")
        assert str(test_dir) in result, "cwd not reflected in pwd output"
        print("✅ Execute Command with cwd Passed")
        passed += 1

    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        failed += 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
    finally:
        if test_dir.exists():
            shutil.rmtree(test_dir)

    print(f"\n--- Summary: {passed} passed, {failed} failed ---")


if __name__ == "__main__":
    asyncio.run(verify_advanced_tools())
