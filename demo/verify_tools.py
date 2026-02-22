import asyncio
import os
import shutil
from pathlib import Path
from openrouter_agent.tools.registry import ToolRegistry

async def verify_tools():
    print("Verifying tools...")
    registry = ToolRegistry()
    
    test_dir = Path("demo_test_env")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    try:
        # 1. Test Write File
        print("\n[Test] Write File")
        write_tool = registry.get("write_file")
        test_file = test_dir / "hello.txt"
        result = await write_tool.run(write_tool.validate_args({
            "path": str(test_file),
            "content": "Hello World\nLine 2\nLine 3"
        }))
        print(f"Result: {result}")
        assert test_file.exists()
        assert test_file.read_text() == "Hello World\nLine 2\nLine 3"
        print("✅ Write File Passed")

        # 2. Test Read File
        print("\n[Test] Read File")
        read_tool = registry.get("read_file")
        content = await read_tool.run(read_tool.validate_args({
            "path": str(test_file)
        }))
        print(f"Content: {content}")
        assert "Hello World" in content
        print("✅ Read File Passed")

        # 3. Test List Directory
        print("\n[Test] List Directory")
        list_tool = registry.get("list_directory")
        listing = await list_tool.run(list_tool.validate_args({
            "directory": str(test_dir)
        }))
        print(f"Listing: {listing}")
        assert "hello.txt" in listing
        print("✅ List Directory Passed")

        # 4. Test Delete File
        print("\n[Test] Delete File")
        delete_tool = registry.get("delete_file")
        result = await delete_tool.run(delete_tool.validate_args({
            "path": str(test_file)
        }))
        print(f"Result: {result}")
        assert not test_file.exists()
        print("✅ Delete File Passed")

        # 5. Test Edit File
        print("\n[Test] Edit File")
        # Write file again first
        await write_tool.run(write_tool.validate_args({
            "path": str(test_file),
            "content": "Hello Old World"
        }))
        
        edit_tool = registry.get("edit_file")
        result = await edit_tool.run(edit_tool.validate_args({
            "path": str(test_file),
            "old_text": "Old World",
            "new_text": "New World"
        }))
        print(f"Result: {result}")
        content = test_file.read_text()
        assert "Hello New World" in content
        print("✅ Edit File Passed")
        
    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    asyncio.run(verify_tools())
