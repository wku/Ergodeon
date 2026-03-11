# Ergodeon Agent System - Complete Documentation

Полная документация системы агентов Ergodeon для разработки ПО.

## 🔮 О проекте

**Ergodeon** - это полнофункциональная система AI-агентов для автоматизации разработки программного обеспечения, использующая:

- 🤖 **8 специализированных агентов** для различных задач
- 🔮 **Event-driven архитектуру** с pub/sub
- ⚡ **Асинхронное выполнение** на asyncio
- 🧠 **Векторную память** с ChromaDB
- 📋 **Spec-driven development** методологию
- 🧪 **Property-based testing** подход
- 🐛 **Bug condition methodology** для исправления багов
- 🌐 **Unified LLM support** - OpenAI, Anthropic, OpenRouter

## 📁 Структура проекта

```
ergodeon/
├── agents/                    # API документация агентов
├── prompts/                   # Системные промпты
├── architecture/              # Реализация на Python
│   ├── core/                 # Ядро системы (orchestrator, llm_client, memory)
│   ├── agents/               # Реализации агентов
│   ├── models/               # Pydantic модели
│   ├── src/                  # CLI, API, UI
│   ├── tests/                # Тесты
│   ├── examples/             # Примеры использования
│   ├── Dockerfile            # Production образ
│   ├── docker-compose.yml    # Docker конфигурация
│   ├── pyproject.toml        # Poetry конфигурация
│   └── LLM_INTEGRATION.md    # LLM руководство
└── doc-1.md                  # Обзор агентов (русский)
```

## 🚀 Быстрый старт

### С Docker (рекомендуется)

```bash
cd architecture

# Настроить переменные окружения
cp .env.example .env
# Отредактировать .env и добавить API ключи

# Запустить
docker-compose up -d

# Просмотр логов
docker-compose logs -f ergodeon
```

### С Poetry

```bash
cd architecture
poetry install --extras all
poetry shell
cp .env.example .env
# Отредактировать .env
ergodeon
```

### С pip

```bash
cd architecture
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Отредактировать .env
python -m src.main
```

## 🤖 LLM Integration

Ergodeon поддерживает множество LLM провайдеров через unified API:

### Поддерживаемые провайдеры

- **OpenAI** - GPT-4, GPT-3.5
- **Anthropic** - Claude 3 (Opus, Sonnet, Haiku)
- **OpenRouter** - 100+ моделей через единый API

### Быстрая настройка

```bash
# В .env файле
OPENROUTER_API_KEY=sk-or-...
LLM_PROVIDER=openrouter
LLM_MODEL=anthropic/claude-3-opus
```

### Использование

```python
from core.llm_client import create_llm_client

client = create_llm_client(
    provider="openrouter",
    model="anthropic/claude-3-opus"
)

messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello!"}
]

response = await client.chat_completion(messages)
```

Подробнее: [architecture/LLM_INTEGRATION.md](architecture/LLM_INTEGRATION.md)

## 📚 Документация

### Основные документы

- **[FINAL_COMPLETION_REPORT.md](FINAL_COMPLETION_REPORT.md)** - Финальный отчет
- **[LLM_INTEGRATION_COMPLETE.md](LLM_INTEGRATION_COMPLETE.md)** - LLM интеграция
- **[QUICKSTART.md](QUICKSTART.md)** - Быстрый старт
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Руководство разработчика
- **[doc-1.md](doc-1.md)** - Обзор агентов (русский)

### Техническая документация

- **[architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)** - Архитектура кода
- **[architecture/DOCKER.md](architecture/DOCKER.md)** - Docker руководство
- **[architecture/LLM_INTEGRATION.md](architecture/LLM_INTEGRATION.md)** - LLM интеграция
- **[prompts/SYSTEM_OVERVIEW.md](prompts/SYSTEM_OVERVIEW.md)** - Система промптов

### API документация агентов

1. **[general-task-execution](agents/general-task-execution/)** - Выполнение общих задач
2. **[context-gatherer](agents/context-gatherer/)** - Анализ кодовой базы
3. **[spec-task-execution](agents/spec-task-execution/)** - Выполнение задач из спецификаций
4. **[feature-requirements-first-workflow](agents/feature-requirements-first-workflow/)** - Requirements → Design → Tasks
5. **[feature-design-first-workflow](agents/feature-design-first-workflow/)** - Design → Requirements → Tasks
6. **[bugfix-workflow](agents/bugfix-workflow/)** - Исправление багов
7. **[custom-agent-creator](agents/custom-agent-creator/)** - Создание новых агентов

## 🏗️ Архитектура

### Технологический стек

**Backend:**
- Python 3.11+, asyncio, Pydantic
- ChromaDB (векторная БД), Redis (state management)
- OpenAI SDK, Anthropic SDK (LLM интеграция)

**API & UI:**
- FastAPI (REST API), Streamlit (Web UI)
- uvicorn (ASGI сервер)

**DevOps:**
- Docker, Docker Compose, Nginx
- Poetry (package management)

**Testing:**
- pytest, pytest-asyncio, pytest-cov

## 📖 Основные концепции

### Агенты

1. **Core Orchestrator** - главный координатор
2. **General Task Execution** - выполнение общих задач
3. **Context Gatherer** - анализ кодовой базы
4. **Spec Task Execution** - выполнение задач из спецификаций
5. **Feature Requirements-First** - Requirements → Design → Tasks
6. **Feature Design-First** - Design → Requirements → Tasks
7. **Bugfix Workflow** - систематическое исправление багов
8. **Custom Agent Creator** - создание новых агентов

### Workflow типы

**Feature Spec:**
- Requirements-First: Требования → Дизайн → Задачи
- Design-First: Дизайн → Требования → Задачи

**Bugfix Spec:**
- Requirements-First с bug condition methodology
- Exploration test для подтверждения бага

## 🐳 Docker

### Запуск всех сервисов

```bash
cd architecture

# Все сервисы (CLI + API + UI + Redis + ChromaDB)
docker-compose --profile api --profile ui up -d

# Только CLI
docker-compose up -d

# С API
docker-compose --profile api up -d
```

### Makefile команды

```bash
make docker-build        # Собрать образы
make docker-up           # Запустить контейнеры
make docker-down         # Остановить контейнеры
make docker-logs         # Просмотр логов
make docker-up-all       # Все сервисы
```

## 📝 Примеры использования

### CLI

```bash
ergodeon

# Создать feature spec
> Add user authentication with JWT tokens

# Исправить баг
> Fix crash when quantity is zero
```

### REST API

```bash
docker-compose --profile api up -d

curl -X POST http://localhost:8002/api/request \
  -H "Content-Type: application/json" \
  -d '{"text": "Create a login form"}'
```

### Streamlit UI

```bash
docker-compose --profile ui up -d
open http://localhost:8501
```

### Python API

```python
from core.orchestrator import CoreOrchestrator
from core.llm_client import create_llm_client

# Создать LLM клиент
llm = create_llm_client(
    provider="openrouter",
    model="anthropic/claude-3-opus"
)

# Использовать в агенте
orchestrator = CoreOrchestrator(config)
await orchestrator.initialize()
```

## 🧪 Тестирование

```bash
cd architecture

# Все тесты
pytest

# С покрытием
pytest --cov=. --cov-report=html

# LLM тесты
pytest tests/unit/test_llm_client.py -v

# Или через Makefile
make test
make test-coverage
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте feature branch
3. Закоммитьте изменения
4. Запушьте в branch
5. Откройте Pull Request

## 📄 Лицензия

MIT License

## 🔗 Полезные ссылки

- **Документация**: [README.md](README.md)
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Development**: [DEVELOPMENT.md](DEVELOPMENT.md)
- **Docker**: [architecture/DOCKER.md](architecture/DOCKER.md)
- **LLM Integration**: [architecture/LLM_INTEGRATION.md](architecture/LLM_INTEGRATION.md)
- **Агенты**: [agents/](agents/)
- **Промпты**: [prompts/](prompts/)
- **Примеры**: [architecture/examples/](architecture/examples/)

## 📧 Контакты

Для вопросов и предложений создавайте issues в репозитории.

---

**Ergodeon v1.0.0** - AI-powered software development agent system  
🔮 **Ergodeon - Empowering developers with AI agents**
