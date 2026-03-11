"""
Unit tests for LLM Client
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.llm_client import LLMClient, LLMConfig, create_llm_client


class TestLLMConfig:
    """Test LLMConfig model"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = LLMConfig()
        
        assert config.provider == "openai"
        assert config.model == "gpt-4-turbo-preview"
        assert config.temperature == 0.7
        assert config.max_tokens == 4000
        assert config.timeout == 60
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = LLMConfig(
            provider="openrouter",
            model="anthropic/claude-3-opus",
            base_url="https://openrouter.ai/api/v1",
            temperature=0.5,
            max_tokens=2000
        )
        
        assert config.provider == "openrouter"
        assert config.model == "anthropic/claude-3-opus"
        assert config.base_url == "https://openrouter.ai/api/v1"
        assert config.temperature == 0.5
        assert config.max_tokens == 2000


class TestLLMClient:
    """Test LLMClient"""
    
    @pytest.fixture
    def openai_config(self):
        """OpenAI configuration"""
        return LLMConfig(
            provider="openai",
            model="gpt-4-turbo-preview",
            api_key="test-key"
        )
    
    @pytest.fixture
    def openrouter_config(self):
        """OpenRouter configuration"""
        return LLMConfig(
            provider="openrouter",
            model="anthropic/claude-3-opus",
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1"
        )
    
    @pytest.fixture
    def anthropic_config(self):
        """Anthropic configuration"""
        return LLMConfig(
            provider="anthropic",
            model="claude-3-opus-20240229",
            api_key="test-key"
        )
    
    def test_init_openai(self, openai_config):
        """Test OpenAI client initialization"""
        with patch('core.llm_client.AsyncOpenAI'):
            client = LLMClient(openai_config)
            assert client.provider == "openai"
            assert client.config.model == "gpt-4-turbo-preview"
    
    def test_init_openrouter(self, openrouter_config):
        """Test OpenRouter client initialization"""
        with patch('core.llm_client.AsyncOpenAI'):
            client = LLMClient(openrouter_config)
            assert client.provider == "openrouter"
            assert client.config.base_url == "https://openrouter.ai/api/v1"
    
    def test_init_anthropic(self, anthropic_config):
        """Test Anthropic client initialization"""
        with patch('core.llm_client.anthropic.AsyncAnthropic'):
            client = LLMClient(anthropic_config)
            assert client.provider == "anthropic"
    
    def test_init_invalid_provider(self):
        """Test invalid provider"""
        config = LLMConfig(provider="invalid")
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMClient(config)
    
    @pytest.mark.asyncio
    async def test_openai_completion(self, openai_config):
        """Test OpenAI completion"""
        with patch('core.llm_client.AsyncOpenAI') as mock_openai:
            # Mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response"
            
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            client = LLMClient(openai_config)
            
            messages = [
                {"role": "user", "content": "Hello"}
            ]
            
            response = await client.chat_completion(messages)
            
            assert response == "Test response"
            mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_openrouter_completion(self, openrouter_config):
        """Test OpenRouter completion with headers"""
        with patch('core.llm_client.AsyncOpenAI') as mock_openai:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response"
            
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            client = LLMClient(openrouter_config)
            
            messages = [{"role": "user", "content": "Hello"}]
            
            response = await client.chat_completion(
                messages,
                http_referer="https://test.com",
                x_title="Test App"
            )
            
            assert response == "Test response"
            
            # Verify extra headers were passed
            call_args = mock_client.chat.completions.create.call_args
            assert call_args is not None
    
    @pytest.mark.asyncio
    async def test_anthropic_completion(self, anthropic_config):
        """Test Anthropic completion"""
        with patch('core.llm_client.anthropic.AsyncAnthropic') as mock_anthropic:
            # Mock response
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = "Test response"
            
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client
            
            client = LLMClient(anthropic_config)
            
            messages = [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hello"}
            ]
            
            response = await client.chat_completion(messages)
            
            assert response == "Test response"
            mock_client.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_temperature_override(self, openai_config):
        """Test temperature override"""
        with patch('core.llm_client.AsyncOpenAI') as mock_openai:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test"
            
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            client = LLMClient(openai_config)
            
            messages = [{"role": "user", "content": "Test"}]
            
            await client.chat_completion(messages, temperature=0.9)
            
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["temperature"] == 0.9
    
    def test_get_model_info(self, openai_config):
        """Test get_model_info"""
        with patch('core.llm_client.AsyncOpenAI'):
            client = LLMClient(openai_config)
            
            info = client.get_model_info()
            
            assert info["provider"] == "openai"
            assert info["model"] == "gpt-4-turbo-preview"
            assert info["temperature"] == 0.7
            assert info["max_tokens"] == 4000


class TestCreateLLMClient:
    """Test create_llm_client factory function"""
    
    def test_create_openai_client(self):
        """Test creating OpenAI client"""
        with patch('core.llm_client.AsyncOpenAI'):
            client = create_llm_client(
                provider="openai",
                model="gpt-4",
                api_key="test-key"
            )
            
            assert client.provider == "openai"
            assert client.config.model == "gpt-4"
    
    def test_create_openrouter_client(self):
        """Test creating OpenRouter client"""
        with patch('core.llm_client.AsyncOpenAI'):
            client = create_llm_client(
                provider="openrouter",
                model="anthropic/claude-3-opus",
                api_key="test-key"
            )
            
            assert client.provider == "openrouter"
            assert client.config.model == "anthropic/claude-3-opus"
    
    def test_create_anthropic_client(self):
        """Test creating Anthropic client"""
        with patch('core.llm_client.anthropic.AsyncAnthropic'):
            client = create_llm_client(
                provider="anthropic",
                model="claude-3-opus-20240229",
                api_key="test-key"
            )
            
            assert client.provider == "anthropic"
    
    def test_default_models(self):
        """Test default models for each provider"""
        with patch('core.llm_client.AsyncOpenAI'):
            client = create_llm_client(provider="openai", api_key="test")
            assert client.config.model == "gpt-4-turbo-preview"
        
        with patch('core.llm_client.AsyncOpenAI'):
            client = create_llm_client(provider="openrouter", api_key="test")
            assert client.config.model == "anthropic/claude-3-opus"
        
        with patch('core.llm_client.anthropic.AsyncAnthropic'):
            client = create_llm_client(provider="anthropic", api_key="test")
            assert client.config.model == "claude-3-opus-20240229"
    
    def test_custom_parameters(self):
        """Test custom parameters"""
        with patch('core.llm_client.AsyncOpenAI'):
            client = create_llm_client(
                provider="openai",
                model="gpt-4",
                temperature=0.5,
                max_tokens=2000,
                timeout=120
            )
            
            assert client.config.temperature == 0.5
            assert client.config.max_tokens == 2000
            assert client.config.timeout == 120


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
