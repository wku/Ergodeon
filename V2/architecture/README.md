# Kiro Agent System - Python Implementation

Асинхронная система агентов для разработки ПО с векторной памятью и event-driven архитектурой.

## Быстрый старт

### Установка

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt

# Настроить переменные окружения
cp .env.example .env
# Отредактировать .env и добавить API ключи
```

### Конфигурация

Отредактируйте `config.yaml` для настройки:
- Параметров оркестратора
- Настроек памяти (ChromaDB)
- LLM провайдера и модели
- Разрешений агентов
- Логирования

### Использование

```python
import asyncio
from core.orchestrator import CoreOrchestrator
from models.agent import UserRequest

async def main():
    # Инициализация
    orchestrator = CoreOrchestrator(config)
    await orchestrator.initialize()
    
    # Обработка запроса
    request = UserRequest(
        text="Create a login form",
        user_id="user123",
        session_id="session456"
    )
    
    result = await orchestrator.process_request(request)
    print(result)
    
    # Завершение
    await orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## Архитектура

### Компоненты

- **CoreOrchestrator**: Главный координатор
- **BaseAgent**: Базовый класс для всех агентов
- **MemorySystem**: Векторная память (ChromaDB)
- **EventBus**: Pub/Sub для событий
- **StateManager**: Управление состоянием
- **ToolRegistry**: Реестр инструментов

### Агенты

1. **general-task-execution**: Общие задачи
2. **context-gatherer**: Анализ кодовой базы
3. **spec-task-execution**: Выполнение задач из спецификаций
4. **feature-requirements-first-workflow**: Создание спецификаций (требования → дизайн → задачи)
5. **feature-design-first-workflow**: Создание спецификаций (дизайн → требования → задачи)
6. **bugfix-workflow**: Исправление багов
7. **custom-agent-creator**: Создание новых агентов

## Структура проекта

```
architecture/
├── core/               # Ядро системы
│   ├── base_agent.py
│   ├── orchestrator.py
│   ├── memory.py
│   ├── events.py
│   └── state.py
├── agents/             # Реализации агентов
│   ├── workflow/
│   ├── execution/
│   └── analysis/
├── models/             # Pydantic модели
│   ├── agent.py
│   ├── workflow.py
│   └── task.py
├── tools/              # Инструменты
│   └── registry.py
├── config.yaml         # Конфигурация
├── requirements.txt    # Зависимости
└── README.md          # Этот файл
```

## Разработка

### Тестирование

```bash
# Запустить все тесты
pytest

# С покрытием
pytest --cov=architecture

# Конкретный тест
pytest tests/test_orchestrator.py
```

### Линтинг

```bash
# Black форматирование
black architecture/

# Ruff проверка
ruff check architecture/

# MyPy типизация
mypy architecture/
```

## Документация

- [ARCHITECTURE.md](ARCHITECTURE.md) - Полное описание архитектуры
- [../prompts/](../prompts/) - Промпты для всех агентов
- [../agents/](../agents/) - API документация агентов

## Лицензия

MIT
