import asyncio
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Ensure we can import from src
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.openrouter_agent.agent.core import Agent

async def verify_agent():
    print("Verifying Agent End-to-End...")
    load_dotenv()
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY not found.")
        return

    # Cleanup previous test
    test_file = Path("agent_test.txt")
    if test_file.exists():
        test_file.unlink()

    agent = Agent(api_key=api_key, model="openai/gpt-3.5-turbo") # Use a cheap/fast model for verification if possible, or default
    # Note: Using default model from Agent class if not specified, which is openai/gpt-4o. 
    # Let's stick to default or specify one. The user provided an OpenRouter key, so we should ensure the model is available on OpenRouter.
    # The default in core.py is "openai/gpt-4o". Let's use "openai/gpt-3.5-turbo" for a quick cheap test, or "google/gemini-flash-1.5" etc.
    # Actually, let's just use "openai/gpt-3.5-turbo" as it's usually standard.
    agent.model = "openai/gpt-3.5-turbo"

    print(f"🤖 Initialized Agent with model: {agent.model}")

    # Test 1: Simple Chat
    print("\n[Test 1] Simple Chat Connectivity")
    try:
        response = await agent.chat("Say 'Hello Verification' if you can read this.")
        print(f"Agent Response: {response}")
        if "Hello Verification" in response or "Hello" in response:
            print("✅ Chat Connectivity Passed")
        else:
            print("⚠️  Chat Verification Warning: Unexpected response")
    except Exception as e:
        print(f"❌ Chat Error: {e}")
        return

    # Test 2: Tool Execution (File Creation)
    print("\n[Test 2] Tool Execution (File Creation)")
    prompt = f"Create a file named '{test_file.name}' with the content: 'Agent was here'."
    
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
            print("❌ Tool Execution Failed: File not created")
            
    except Exception as e:
        print(f"❌ Tool Execution Error: {e}")
    finally:
        if test_file.exists():
            test_file.unlink()

if __name__ == "__main__":
    asyncio.run(verify_agent())
