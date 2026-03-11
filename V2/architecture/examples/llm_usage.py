"""
Examples of using LLM Client with different providers
"""

import asyncio
from core.llm_client import create_llm_client, LLMConfig


async def example_openai():
    """Example: Using OpenAI"""
    print("=== OpenAI Example ===")
    
    client = create_llm_client(
        provider="openai",
        model="gpt-4-turbo-preview",
        temperature=0.7
    )
    
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a Python function to calculate fibonacci numbers."}
    ]
    
    response = await client.chat_completion(messages)
    print(f"Response: {response[:200]}...")
    print(f"Model info: {client.get_model_info()}")


async def example_openrouter():
    """Example: Using OpenRouter"""
    print("\n=== OpenRouter Example ===")
    
    client = create_llm_client(
        provider="openrouter",
        model="anthropic/claude-3-opus",
        # api_key will be read from OPENROUTER_API_KEY env var
        temperature=0.7
    )
    
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Explain async/await in Python."}
    ]
    
    response = await client.chat_completion(
        messages,
        http_referer="https://github.com/wku/Ergodeon",
        x_title="Ergodeon Agent System"
    )
    print(f"Response: {response[:200]}...")
    print(f"Model info: {client.get_model_info()}")


async def example_anthropic():
    """Example: Using Anthropic Claude"""
    print("\n=== Anthropic Example ===")
    
    client = create_llm_client(
        provider="anthropic",
        model="claude-3-opus-20240229",
        temperature=0.7
    )
    
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "What are the benefits of type hints in Python?"}
    ]
    
    response = await client.chat_completion(messages)
    print(f"Response: {response[:200]}...")
    print(f"Model info: {client.get_model_info()}")


async def example_streaming():
    """Example: Streaming responses"""
    print("\n=== Streaming Example ===")
    
    client = create_llm_client(
        provider="openai",
        model="gpt-4-turbo-preview"
    )
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Count from 1 to 5 slowly."}
    ]
    
    print("Streaming response: ", end="", flush=True)
    async for chunk in client.stream_completion(messages):
        print(chunk, end="", flush=True)
    print("\n")


async def example_openrouter_models():
    """Example: Different OpenRouter models"""
    print("\n=== OpenRouter Multiple Models ===")
    
    models = [
        "anthropic/claude-3-opus",
        "openai/gpt-4-turbo-preview",
        "google/gemini-pro",
        "meta-llama/llama-3-70b-instruct"
    ]
    
    messages = [
        {"role": "user", "content": "Say hello in one sentence."}
    ]
    
    for model in models:
        print(f"\nModel: {model}")
        try:
            client = create_llm_client(
                provider="openrouter",
                model=model,
                max_tokens=100
            )
            
            response = await client.chat_completion(messages)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")


async def example_with_config():
    """Example: Using LLMConfig directly"""
    print("\n=== Using LLMConfig ===")
    
    from core.llm_client import LLMClient
    
    config = LLMConfig(
        provider="openrouter",
        model="anthropic/claude-3-sonnet",
        temperature=0.5,
        max_tokens=2000,
        base_url="https://openrouter.ai/api/v1"
    )
    
    client = LLMClient(config)
    
    messages = [
        {"role": "user", "content": "What is the capital of France?"}
    ]
    
    response = await client.chat_completion(messages)
    print(f"Response: {response}")
    print(f"Config: {config.model_dump()}")


async def main():
    """Run all examples"""
    
    # Run examples based on available API keys
    import os
    
    if os.getenv("OPENAI_API_KEY"):
        await example_openai()
        await example_streaming()
    else:
        print("Skipping OpenAI examples (no API key)")
    
    if os.getenv("OPENROUTER_API_KEY"):
        await example_openrouter()
        await example_openrouter_models()
        await example_with_config()
    else:
        print("\nSkipping OpenRouter examples (no API key)")
    
    if os.getenv("ANTHROPIC_API_KEY"):
        await example_anthropic()
    else:
        print("\nSkipping Anthropic examples (no API key)")


if __name__ == "__main__":
    asyncio.run(main())
