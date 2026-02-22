import asyncio
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from openrouter_agent.tools.filesystem import ListDirectoryTool, ListDirectoryArgs, WriteFileTool, WriteFileArgs


async def reproduce():
    """
    Проверяет что list_directory не генерирует взрывной вывод при рекурсивном обходе.
    Использует изолированную временную директорию вместо текущей (которая может содержать .venv).
    """
    tool = ListDirectoryTool()

    print("=== Test 1: list_directory recursive=True на текущей директории ===")
    try:
        result = await tool.run(ListDirectoryArgs(directory=".", recursive=True))
        size = len(result)
        print(f"Result Length: {size} chars")
        if size > 50000:
            print(f"❌ Massive output detected! First 300 chars:\n{result[:300]}")
        elif size > 10000:
            print(f"⚠️  Large output ({size} chars) - возможно .venv попал в обход")
            print(f"First 300 chars:\n{result[:300]}")
        else:
            print("✅ Output size acceptable.")
    except Exception as e:
        print(f"Error: {e}")

    print("\n=== Test 2: list_directory в изолированной директории с несколькими файлами ===")
    with tempfile.TemporaryDirectory(prefix="ergodeon_repro_") as tmp_dir:
        write_tool = WriteFileTool()

        # Создаём вложенную структуру
        (Path(tmp_dir) / "subdir").mkdir()
        for name in ["a.txt", "b.txt", "subdir/c.txt"]:
            await write_tool.run(WriteFileArgs(
                path=str(Path(tmp_dir) / name),
                content=f"content of {name}",
            ))

        result = await tool.run(ListDirectoryArgs(directory=tmp_dir, recursive=True))
        print(f"Result:\n{result}")
        assert "a.txt" in result
        assert "b.txt" in result
        assert "c.txt" in result
        print("✅ Recursive listing correct.")

    print("\n=== Test 3: list_directory non-recursive ===")
    with tempfile.TemporaryDirectory(prefix="ergodeon_repro_") as tmp_dir:
        write_tool = WriteFileTool()
        (Path(tmp_dir) / "nested").mkdir()
        await write_tool.run(WriteFileArgs(
            path=str(Path(tmp_dir) / "root.txt"),
            content="root",
        ))
        await write_tool.run(WriteFileArgs(
            path=str(Path(tmp_dir) / "nested" / "deep.txt"),
            content="deep",
        ))

        result = await tool.run(ListDirectoryArgs(directory=tmp_dir, recursive=False))
        print(f"Result:\n{result}")
        assert "root.txt" in result, "root.txt should appear"
        # deep.txt НЕ должен появиться при recursive=False
        assert "deep.txt" not in result, "deep.txt should NOT appear in non-recursive listing"
        print("✅ Non-recursive listing correct.")

    print("\n=== Test 4: list_directory несуществующей директории ===")
    result = await tool.run(ListDirectoryArgs(directory="/nonexistent/path/xyz", recursive=False))
    print(f"Result: {result}")
    assert "Error" in result or "does not exist" in result
    print("✅ Error handling correct.")


if __name__ == "__main__":
    asyncio.run(reproduce())
