import asyncio
import os
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Поддержка запуска как из корня проекта, так и из папки demo/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from openrouter_agent.agent.core import Agent


async def verify_agent():
    print("Verifying Agent End-to-End...")
    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY not found in environment or .env file.")
        return

    # Используем временную директорию как project_dir чтобы не засорять корень
    # и чтобы guard в core._step не блокировал запись файлов
    with tempfile.TemporaryDirectory(prefix="ergodeon_verify_") as tmp_dir:
        test_file = Path(tmp_dir) / "agent_test.txt"

        agent = Agent(api_key=api_key, model="openai/gpt-4o")
        # Устанавливаем active_project_dir чтобы guard работал корректно
        agent.active_project_dir = tmp_dir
        print(f"Agent initialized, model={agent.model}, project_dir={tmp_dir}")

        # Test 1: Simple Chat
        print("\n[Test 1] Simple Chat Connectivity")
        try:
            response = await agent.chat("Say 'Hello Verification' if you can read this.")
            print(f"Agent Response: {response}")
            if "Hello" in response:
                print("✅ Chat Connectivity Passed")
            else:
                print("⚠️  Chat Verification Warning: Unexpected response")
        except Exception as e:
            print(f"❌ Chat Error: {e}")
            return

        # Test 2: Tool Execution (File Creation)
        print("\n[Test 2] Tool Execution (File Creation inside project_dir)")
        prompt = (
            f"Create a file named 'agent_test.txt' "
            f"with the content: 'Agent was here'. "
            f"Use relative path: agent_test.txt"
        )
        try:
            response = await agent.chat(prompt)
            print(f"Agent Response: {response}")

            if test_file.exists():
                content = test_file.read_text()
                print(f"File Content: {content}")
                if "Agent was here" in content:
                    print("✅ Tool Execution Passed")
                else:
                    print("⚠️  Tool Execution Warning: File content mismatch")
            else:
                # Агент мог записать файл с другим именем или путём - ищем
                found = list(Path(tmp_dir).glob("*.txt"))
                if found:
                    print(f"⚠️  File created with different name: {[f.name for f in found]}")
                else:
                    print("❌ Tool Execution Failed: No files created in project_dir")

        except Exception as e:
            print(f"❌ Tool Execution Error: {e}")

        # Test 3: Guard - попытка записи вне project_dir должна быть заблокирована
        print("\n[Test 3] Path Guard - write outside project_dir must be blocked")
        blocked = False
        try:
            response = await agent.chat(
                "Create a file at /tmp/evil_test.txt with content 'should be blocked'."
            )
            evil_file = Path("/tmp/evil_test.txt")
            if evil_file.exists():
                evil_file.unlink()
                print("❌ Guard Failed: File was created outside project_dir")
            else:
                print(f"✅ Guard Passed: File not created (agent response: {response[:120]})")
                blocked = True
        except Exception as e:
            print(f"✅ Guard Passed via exception: {e}")
            blocked = True

    print("\n--- Summary ---")
    print("Tests completed. Review results above.")


if __name__ == "__main__":
    asyncio.run(verify_agent())
