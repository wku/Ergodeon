"""
LLM Client for Ergodeon Agent System
Supports OpenAI, Anthropic, and OpenRouter
"""

from typing import Optional, Dict, Any, List
import os
from openai import AsyncOpenAI
import anthropic
from pydantic import BaseModel


class LLMConfig(BaseModel):
    """LLM Configuration"""
    provider: str = "openai"  # openai, anthropic, openrouter
    model: str = "gpt-4-turbo-preview"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000
    timeout: int = 60


class LLMClient:
    """Unified LLM client supporting multiple providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider = config.provider.lower()
        
        # Initialize clients
        if self.provider == "openai":
            self.client = AsyncOpenAI(
                api_key=config.api_key or os.getenv("OPENAI_API_KEY"),
                timeout=config.timeout
            )
        elif self.provider == "openrouter":
            self.client = AsyncOpenAI(
                api_key=config.api_key or os.getenv("OPENROUTER_API_KEY"),
                base_url=config.base_url or "https://openrouter.ai/api/v1",
                timeout=config.timeout
            )
        elif self.provider == "anthropic":
            self.anthropic_client = anthropic.AsyncAnthropic(
                api_key=config.api_key or os.getenv("ANTHROPIC_API_KEY"),
                timeout=config.timeout
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate chat completion
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text response
        """
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        if self.provider in ["openai", "openrouter"]:
            return await self._openai_completion(messages, temp, tokens, **kwargs)
        elif self.provider == "anthropic":
            return await self._anthropic_completion(messages, temp, tokens, **kwargs)
    
    async def _openai_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """OpenAI/OpenRouter completion"""
        
        # OpenRouter specific headers
        extra_headers = {}
        if self.provider == "openrouter":
            extra_headers = {
                "HTTP-Referer": kwargs.get("http_referer", "https://github.com/wku/Ergodeon"),
                "X-Title": kwargs.get("x_title", "Ergodeon Agent System")
            }
        
        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers=extra_headers if extra_headers else None,
            **{k: v for k, v in kwargs.items() if k not in ["http_referer", "x_title"]}
        )
        
        return response.choices[0].message.content
    
    async def _anthropic_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """Anthropic Claude completion"""
        
        # Convert messages format for Anthropic
        system_message = None
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        response = await self.anthropic_client.messages.create(
            model=self.config.model,
            messages=anthropic_messages,
            system=system_message,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return response.content[0].text
    
    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Stream chat completion
        
        Args:
            messages: List of message dicts
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional parameters
            
        Yields:
            Text chunks as they arrive
        """
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        if self.provider in ["openai", "openrouter"]:
            async for chunk in self._openai_stream(messages, temp, tokens, **kwargs):
                yield chunk
        elif self.provider == "anthropic":
            async for chunk in self._anthropic_stream(messages, temp, tokens, **kwargs):
                yield chunk
    
    async def _openai_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs
    ):
        """OpenAI/OpenRouter streaming"""
        
        extra_headers = {}
        if self.provider == "openrouter":
            extra_headers = {
                "HTTP-Referer": kwargs.get("http_referer", "https://github.com/wku/Ergodeon"),
                "X-Title": kwargs.get("x_title", "Ergodeon Agent System")
            }
        
        stream = await self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            extra_headers=extra_headers if extra_headers else None,
            **{k: v for k, v in kwargs.items() if k not in ["http_referer", "x_title"]}
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def _anthropic_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs
    ):
        """Anthropic streaming"""
        
        system_message = None
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        async with self.anthropic_client.messages.stream(
            model=self.config.model,
            messages=anthropic_messages,
            system=system_message,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        ) as stream:
            async for text in stream.text_stream:
                yield text
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model"""
        return {
            "provider": self.provider,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "base_url": self.config.base_url if self.provider == "openrouter" else None
        }


# Factory function
def create_llm_client(
    provider: str = "openai",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs
) -> LLMClient:
    """
    Create LLM client
    
    Args:
        provider: "openai", "anthropic", or "openrouter"
        model: Model name (provider-specific)
        api_key: API key (or use env var)
        base_url: Base URL (for OpenRouter)
        **kwargs: Additional config parameters
        
    Returns:
        Configured LLMClient instance
        
    Examples:
        # OpenAI
        client = create_llm_client("openai", model="gpt-4-turbo-preview")
        
        # OpenRouter
        client = create_llm_client(
            "openrouter",
            model="anthropic/claude-3-opus",
            api_key="sk-or-..."
        )
        
        # Anthropic
        client = create_llm_client("anthropic", model="claude-3-opus-20240229")
    """
    
    # Default models
    default_models = {
        "openai": "gpt-4-turbo-preview",
        "openrouter": "anthropic/claude-3-opus",
        "anthropic": "claude-3-opus-20240229"
    }
    
    config = LLMConfig(
        provider=provider,
        model=model or default_models.get(provider, "gpt-4-turbo-preview"),
        api_key=api_key,
        base_url=base_url,
        **kwargs
    )
    
    return LLMClient(config)
