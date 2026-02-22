import asyncio
from pathlib import Path
from openrouter_agent.tools.filesystem import ListDirectoryTool, ListDirectoryArgs

async def reproduce():
    tool = ListDirectoryTool()
    print("Running list_directory recursive=True on .")
    
    # Run on current directory which contains .venv
    try:
        result = await tool.run(ListDirectoryArgs(directory=".", recursive=True))
        print(f"Result Length: {len(result)}")
        if len(result) > 10000:
            print("❌ Massive output detected!")
            print(f"First 500 chars: {result[:500]}")
        else:
            print("✅ Output size acceptable.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(reproduce())
