# LLM Integration Guide - Ergodeon

Руководство по интеграции и использованию LLM моделей в Ergodeon Agent System.

## Поддерживаемые провайдеры

Ergodeon поддерживает три LLM провайдера:

1. **OpenAI** - GPT-4, GPT-3.5 и другие модели OpenAI
2. **Anthropic** - Claude 3 (Opus, Sonnet, Haiku)
3. **OpenRouter** - Доступ к множеству моделей через единый API

## Быстрый старт

### 1. Установка зависимостей

Все необходимые зависимости уже включены в `requirements.txt` и `pyproject.toml`:

```bash
# С pip
pip install openai anthropic

# С Poetry
poetry install
```

### 2. Настройка API ключей

Создайте `.env` файл из примера:

```bash
cp .env.example .env
```

Добавьте ваши API ключи:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# OpenRouter
OPENROUTER_API_KEY=sk-or-...
```

### 3. Выбор провайдера

В `config.yaml` или через переменные окружения:

```yaml
llm:
  provider: "openrouter"  # "openai", "anthropic", или "openrouter"
  model: "anthropic/claude-3-opus"
  base_url: "https://openrouter.ai/api/v1"  # Только для OpenRouter
  temperature: 0.7
  max_tokens: 4000
```

Или через `.env`:

```bash
LLM_PROVIDER=openrouter
LLM_MODEL=anthropic/claude-3-opus
LLM_BASE_URL=https://openrouter.ai/api/v1
```

## Использование

### Базовый пример

```python
from core.llm_client import create_llm_client

# Создать клиент
client = create_llm_client(
    provider="openrouter",
    model="anthropic/claude-3-opus"
)

# Отправить запрос
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
]

response = await client.chat_completion(messages)
print(response)
```

### OpenAI

```python
client = create_llm_client(
    provider="openai",
    model="gpt-4-turbo-preview",
    temperature=0.7,
    max_tokens=4000
)

messages = [
    {"role": "system", "content": "You are a coding assistant."},
    {"role": "user", "content": "Write a Python function."}
]

response = await client.chat_completion(messages)
```

### OpenRouter

```python
client = create_llm_client(
    provider="openrouter",
    model="anthropic/claude-3-opus",
    api_key="sk-or-..."  # Или из env
)

response = await client.chat_completion(
    messages,
    http_referer="https://github.com/wku/Ergodeon",
    x_title="Ergodeon Agent System"
)
```

### Anthropic Claude

```python
client = create_llm_client(
    provider="anthropic",
    model="claude-3-opus-20240229",
    temperature=0.7
)

response = await client.chat_completion(messages)
```

### Streaming

```python
client = create_llm_client(provider="openai")

async for chunk in client.stream_completion(messages):
    print(chunk, end="", flush=True)
```

## Доступные модели

### OpenAI

- `gpt-4-turbo-preview` - GPT-4 Turbo (рекомендуется)
- `gpt-4` - GPT-4
- `gpt-3.5-turbo` - GPT-3.5 Turbo

### Anthropic

- `claude-3-opus-20240229` - Claude 3 Opus (самый мощный)
- `claude-3-sonnet-20240229` - Claude 3 Sonnet (баланс)
- `claude-3-haiku-20240307` - Claude 3 Haiku (быстрый)

### OpenRouter

OpenRouter предоставляет доступ к множеству моделей:

**Anthropic:**
- `anthropic/claude-3-opus` - Claude 3 Opus
- `anthropic/claude-3-sonnet` - Claude 3 Sonnet
- `anthropic/claude-3-haiku` - Claude 3 Haiku

**OpenAI:**
- `openai/gpt-4-turbo-preview` - GPT-4 Turbo
- `openai/gpt-4` - GPT-4
- `openai/gpt-3.5-turbo` - GPT-3.5

**Google:**
- `google/gemini-pro` - Gemini Pro
- `google/gemini-pro-vision` - Gemini Pro Vision

**Meta:**
- `meta-llama/llama-3-70b-instruct` - Llama 3 70B
- `meta-llama/llama-3-8b-instruct` - Llama 3 8B

**Mistral:**
- `mistralai/mistral-large` - Mistral Large
- `mistralai/mistral-medium` - Mistral Medium

Полный список: https://openrouter.ai/models

## Продвинутое использование

### Использование LLMConfig

```python
from core.llm_client import LLMClient, LLMConfig

config = LLMConfig(
    provider="openrouter",
    model="anthropic/claude-3-opus",
    api_key="sk-or-...",
    base_url="https://openrouter.ai/api/v1",
    temperature=0.5,
    max_tokens=2000,
    timeout=120
)

client = LLMClient(config)
```

### Переопределение параметров

```python
# Использовать другую температуру для конкретного запроса
response = await client.chat_completion(
    messages,
    temperature=0.9,
    max_tokens=1000
)
```

### Получение информации о модели

```python
info = client.get_model_info()
print(info)
# {
#     "provider": "openrouter",
#     "model": "anthropic/claude-3-opus",
#     "temperature": 0.7,
#     "max_tokens": 4000,
#     "base_url": "https://openrouter.ai/api/v1"
# }
```

## Интеграция с агентами

### В базовом агенте

```python
from core.base_agent import BaseAgent
from core.llm_client import create_llm_client

class MyAgent(BaseAgent):
    async def initialize(self):
        await super().initialize()
        
        # Создать LLM клиент
        self.llm = create_llm_client(
            provider=self.config.get("llm_provider", "openai"),
            model=self.config.get("llm_model", "gpt-4-turbo-preview")
        )
    
    async def execute(self, task):
        messages = [
            {"role": "system", "content": "You are an agent."},
            {"role": "user", "content": task.description}
        ]
        
        response = await self.llm.chat_completion(messages)
        return response
```

### В оркестраторе

```python
from core.orchestrator import CoreOrchestrator
from core.llm_client import create_llm_client

class MyOrchestrator(CoreOrchestrator):
    async def initialize(self):
        await super().initialize()
        
        # Создать LLM клиент из конфигурации
        llm_config = self.config.get("llm", {})
        self.llm = create_llm_client(
            provider=llm_config.get("provider", "openai"),
            model=llm_config.get("model"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 4000)
        )
```

## Примеры

Полные примеры использования находятся в:

```bash
architecture/examples/llm_usage.py
```

Запуск примеров:

```bash
cd architecture
python examples/llm_usage.py
```

## Стоимость и лимиты

### OpenAI

- GPT-4 Turbo: ~$0.01-0.03 за 1K токенов
- GPT-3.5 Turbo: ~$0.0005-0.0015 за 1K токенов

### Anthropic

- Claude 3 Opus: ~$0.015-0.075 за 1K токенов
- Claude 3 Sonnet: ~$0.003-0.015 за 1K токенов
- Claude 3 Haiku: ~$0.00025-0.00125 за 1K токенов

### OpenRouter

Цены варьируются в зависимости от модели. OpenRouter добавляет небольшую наценку к базовой цене провайдера.

Актуальные цены: https://openrouter.ai/models

## Обработка ошибок

```python
try:
    response = await client.chat_completion(messages)
except Exception as e:
    print(f"LLM Error: {e}")
    # Обработка ошибки
```

Типичные ошибки:

- `AuthenticationError` - Неверный API ключ
- `RateLimitError` - Превышен лимит запросов
- `APIError` - Ошибка API
- `Timeout` - Превышено время ожидания

## Best Practices

1. **Используйте переменные окружения** для API ключей
2. **Кэшируйте результаты** для одинаковых запросов
3. **Обрабатывайте ошибки** gracefully
4. **Мониторьте использование** и стоимость
5. **Используйте streaming** для длинных ответов
6. **Настраивайте temperature** в зависимости от задачи:
   - 0.0-0.3: Детерминированные задачи (код, факты)
   - 0.4-0.7: Сбалансированные задачи
   - 0.8-1.0: Креативные задачи

## Troubleshooting

### Ошибка: "Invalid API key"

Проверьте, что API ключ правильно установлен:

```bash
echo $OPENAI_API_KEY
echo $OPENROUTER_API_KEY
echo $ANTHROPIC_API_KEY
```

### Ошибка: "Rate limit exceeded"

Добавьте retry логику или уменьшите частоту запросов.

### Ошибка: "Model not found"

Проверьте правильность имени модели для выбранного провайдера.

### OpenRouter: "Insufficient credits"

Пополните баланс на https://openrouter.ai/credits

## Дополнительные ресурсы

- **OpenAI API**: https://platform.openai.com/docs
- **Anthropic API**: https://docs.anthropic.com
- **OpenRouter**: https://openrouter.ai/docs
- **Ergodeon Examples**: `architecture/examples/llm_usage.py`

## Поддержка

Для вопросов и проблем создавайте issues в репозитории:
https://github.com/wku/Ergodeon/issues
