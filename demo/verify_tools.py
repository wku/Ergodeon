import asyncio
import os
import sys
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from openrouter_agent.tools.registry import ToolRegistry


async def verify_tools():
    print("Verifying tools...")
    registry = ToolRegistry()

    test_dir = Path(__file__).parent / "demo_test_env"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    passed = 0
    failed = 0

    try:
        # 1. Write File
        print("\n[Test] Write File")
        write_tool = registry.get("write_file")
        test_file = test_dir / "hello.txt"
        result = await write_tool.run(write_tool.validate_args({
            "path": str(test_file),
            "content": "Hello World\nLine 2\nLine 3",
        }))
        print(f"Result: {result}")
        assert test_file.exists(), "File not created"
        assert test_file.read_text() == "Hello World\nLine 2\nLine 3", "Content mismatch"
        print("✅ Write File Passed")
        passed += 1

        # 2. Read File
        print("\n[Test] Read File")
        read_tool = registry.get("read_file")
        content = await read_tool.run(read_tool.validate_args({
            "path": str(test_file),
        }))
        print(f"Content: {content}")
        assert "Hello World" in content, "Expected text not found"
        print("✅ Read File Passed")
        passed += 1

        # 3. Read File with line range
        print("\n[Test] Read File (line range)")
        content_partial = await read_tool.run(read_tool.validate_args({
            "path": str(test_file),
            "start_line": 2,
            "end_line": 2,
            "show_line_numbers": True,
        }))
        print(f"Partial Content: {content_partial}")
        assert "Line 2" in content_partial, "Line 2 not found"
        assert "Hello World" not in content_partial, "Line 1 should not appear"
        print("✅ Read File (line range) Passed")
        passed += 1

        # 4. List Directory
        print("\n[Test] List Directory")
        list_tool = registry.get("list_directory")
        listing = await list_tool.run(list_tool.validate_args({
            "directory": str(test_dir),
        }))
        print(f"Listing: {listing}")
        assert "hello.txt" in listing, "File not listed"
        print("✅ List Directory Passed")
        passed += 1

        # 5. Edit File
        print("\n[Test] Edit File")
        edit_tool = registry.get("edit_file")
        result = await edit_tool.run(edit_tool.validate_args({
            "path": str(test_file),
            "old_text": "Hello World",
            "new_text": "Hello New World",
        }))
        print(f"Result: {result}")
        content = test_file.read_text()
        assert "Hello New World" in content, "Edit not applied"
        assert "Hello World\n" not in content, "Old text still present"
        print("✅ Edit File Passed")
        passed += 1

        # 6. Get File Info
        print("\n[Test] Get File Info")
        info_tool = registry.get("get_file_info")
        info = await info_tool.run(info_tool.validate_args({
            "path": str(test_file),
        }))
        print(f"File Info: {info}")
        assert "hello.txt" in info or str(test_file) in info, "File name not in info"
        print("✅ Get File Info Passed")
        passed += 1

        # 7. Delete File
        print("\n[Test] Delete File")
        delete_tool = registry.get("delete_file")
        result = await delete_tool.run(delete_tool.validate_args({
            "path": str(test_file),
        }))
        print(f"Result: {result}")
        assert not test_file.exists(), "File still exists after delete"
        print("✅ Delete File Passed")
        passed += 1

        # 8. Error handling - read nonexistent file
        print("\n[Test] Read Nonexistent File (error handling)")
        result = await read_tool.run(read_tool.validate_args({
            "path": str(test_dir / "nonexistent.txt"),
        }))
        print(f"Result: {result}")
        assert "Error" in result or "does not exist" in result, "Expected error message"
        print("✅ Error Handling Passed")
        passed += 1

    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        failed += 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        failed += 1
    finally:
        if test_dir.exists():
            shutil.rmtree(test_dir)

    print(f"\n--- Summary: {passed} passed, {failed} failed ---")


if __name__ == "__main__":
    asyncio.run(verify_tools())
