# Development Guide - Kiro Agent System

Руководство по разработке и расширению системы агентов Kiro.

## Содержание

1. [Начало работы](#начало-работы)
2. [Архитектура](#архитектура)
3. [Создание нового агента](#создание-нового-агента)
4. [Тестирование](#тестирование)
5. [Стиль кода](#стиль-кода)
6. [Отладка](#отладка)
7. [Deployment](#deployment)

---

## Начало работы

### Установка для разработки

```bash
# Клонировать репозиторий
git clone <repository-url>
cd kiro-agent-system

# Создать виртуальное окружение
cd architecture
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить зависимости для разработки
pip install -r requirements.txt
pip install -r requirements-dev.txt  # если есть

# Настроить pre-commit hooks
pre-commit install

# Скопировать и настроить .env
cp .env.example .env
# Отредактировать .env и добавить API ключи
```

### Структура проекта

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
├── tools/              # Инструменты
├── tests/              # Тесты
├── examples/           # Примеры
└── config.yaml         # Конфигурация
```

---

## Архитектура

### Основные компоненты

#### 1. CoreOrchestrator
Главный координатор системы.

**Ответственность**:
- Маршрутизация запросов к агентам
- Управление жизненным циклом агентов
- Координация workflow
- Управление состоянием

**Ключевые методы**:
```python
async def process_request(request: UserRequest) -> AgentResult
async def _analyze_intent(request: UserRequest) -> IntentAnalysis
async def _determine_workflow(intent: IntentAnalysis) -> str
async def _execute_agent(agent_name: str, context: AgentContext) -> AgentResult
```

#### 2. BaseAgent
Базовый класс для всех агентов.

**Ответственность**:
- Выполнение задач
- Взаимодействие с памятью
- Использование инструментов
- Делегирование другим агентам

**Ключевые методы**:
```python
async def execute(context: AgentContext) -> AgentResult  # Абстрактный
async def validate(context: AgentContext) -> bool  # Абстрактный
async def run(context: AgentContext) -> AgentResult
async def use_tool(tool_name: str, params: Dict) -> Any
async def delegate_to_agent(agent_name: str, context: AgentContext) -> AgentResult
```

#### 3. MemorySystem
Векторная память для семантического поиска.

**Ответственность**:
- Хранение контекста
- Семантический поиск
- Управление коллекциями

**Ключевые методы**:
```python
async def store_context(agent_name: str, context: Dict) -> None
async def store_result(agent_name: str, result: Dict) -> None
async def search(query: str, limit: int) -> List[Dict]
```

#### 4. EventBus
Pub/Sub для коммуникации.

**Ответственность**:
- Публикация событий
- Подписка на события
- История событий

**Ключевые методы**:
```python
def emit(event: str, data: Dict) -> None
def on(event: str, handler: Callable) -> None
def off(event: str, handler: Callable) -> None
```

#### 5. StateManager
Управление состоянием workflow.

**Ответственность**:
- Хранение состояния workflow
- Отслеживание задач
- Управление сессиями

**Ключевые методы**:
```python
def get_or_create_workflow(workflow_type: str, feature_name: str) -> WorkflowState
def update_workflow(workflow_id: str, data: Dict) -> None
def get_workflow(workflow_id: str) -> Optional[WorkflowState]
```

---

## Создание нового агента

### Шаг 1: Определить назначение

Определите:
- Какую задачу решает агент
- Какие инструменты ему нужны
- С какими агентами он взаимодействует
- Какой формат входа/выхода

### Шаг 2: Создать документацию

Создайте в `agents/{agent-name}/`:
- `api.md` - API документация
- `workflow.md` - Workflow диаграммы

### Шаг 3: Создать промпт

Создайте в `prompts/{agent-name}/`:
- `prompt.md` - Системный промпт
- `examples.md` - Примеры использования (опционально)

### Шаг 4: Реализовать агента

```python
# architecture/agents/category/my_agent.py

from typing import Any
from ...core.base_agent import BaseAgent
from ...models.agent import AgentContext, AgentResult, AgentResultStatus


class MyAgent(BaseAgent):
    """My custom agent"""
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Main execution logic"""
        
        # 1. Validate input
        if not await self.validate(context):
            raise ValueError("Invalid context")
        
        # 2. Update progress
        self.update_progress(10, "Starting task")
        
        # 3. Search memory for context
        relevant_context = await self.search_memory(
            context.request, 
            limit=10
        )
        
        # 4. Use tools
        result = await self.use_tool("readFile", {
            "path": "some/file.py"
        })
        
        # 5. Process result
        self.update_progress(50, "Processing")
        
        # 6. Delegate if needed
        if needs_delegation:
            delegated_result = await self.delegate_to_agent(
                "other-agent",
                context
            )
        
        # 7. Return result
        self.update_progress(100, "Complete")
        
        return AgentResult(
            status=AgentResultStatus.SUCCESS,
            agent_name=self.config.name,
            output="Task completed",
            files_created=["file1.py"],
            result={"key": "value"}
        )
    
    async def validate(self, context: AgentContext) -> bool:
        """Validate input"""
        return context.request is not None
    
    def process_result(self, result: Any) -> AgentResult:
        """Process result before returning"""
        if isinstance(result, AgentResult):
            return result
        
        return AgentResult(
            status=AgentResultStatus.SUCCESS,
            agent_name=self.config.name,
            result=result
        )
```

### Шаг 5: Зарегистрировать агента

```python
# В orchestrator.py или отдельном registry

from agents.category.my_agent import MyAgent

# Create config
config = AgentConfig(
    name="my-agent",
    display_name="My Agent",
    description="Does something useful",
    allowed_tools=["readFile", "fsWrite"]
)

# Create agent
agent = MyAgent(config, memory, tools, event_bus)

# Register
orchestrator.register_agent(agent)
```

### Шаг 6: Добавить тесты

```python
# tests/test_my_agent.py

import pytest
from agents.category.my_agent import MyAgent
from models.agent import AgentContext, IntentAnalysis


@pytest.mark.asyncio
async def test_my_agent_execute(mock_memory, mock_tools, mock_event_bus):
    """Test agent execution"""
    
    # Setup
    config = AgentConfig(name="my-agent", ...)
    agent = MyAgent(config, mock_memory, mock_tools, mock_event_bus)
    
    # Create context
    context = AgentContext(
        request="Do something",
        intent=IntentAnalysis(...)
    )
    
    # Execute
    result = await agent.run(context)
    
    # Assert
    assert result.status == AgentResultStatus.SUCCESS
    assert len(result.files_created) > 0


@pytest.mark.asyncio
async def test_my_agent_validation(mock_memory, mock_tools, mock_event_bus):
    """Test input validation"""
    
    config = AgentConfig(name="my-agent", ...)
    agent = MyAgent(config, mock_memory, mock_tools, mock_event_bus)
    
    # Valid context
    valid_context = AgentContext(request="Valid", ...)
    assert await agent.validate(valid_context) == True
    
    # Invalid context
    invalid_context = AgentContext(request=None, ...)
    assert await agent.validate(invalid_context) == False
```

---

## Тестирование

### Структура тестов

```
tests/
├── unit/               # Unit тесты
│   ├── test_orchestrator.py
│   ├── test_base_agent.py
│   ├── test_memory.py
│   └── test_agents/
├── integration/        # Integration тесты
│   ├── test_workflow.py
│   └── test_delegation.py
└── e2e/               # End-to-end тесты
    └── test_scenarios.py
```

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=architecture --cov-report=html

# Конкретный файл
pytest tests/unit/test_orchestrator.py

# Конкретный тест
pytest tests/unit/test_orchestrator.py::test_process_request

# С verbose
pytest -v

# Только unit тесты
pytest tests/unit/

# Только integration тесты
pytest tests/integration/
```

### Fixtures

```python
# tests/conftest.py

import pytest
from core.memory import MemorySystem
from core.events import EventBus
from tools.registry import ToolRegistry


@pytest.fixture
async def mock_memory():
    """Mock memory system"""
    memory = MemorySystem({'db_path': ':memory:'})
    await memory.initialize()
    yield memory
    await memory.shutdown()


@pytest.fixture
def mock_event_bus():
    """Mock event bus"""
    return EventBus()


@pytest.fixture
async def mock_tools():
    """Mock tool registry"""
    tools = ToolRegistry()
    await tools.initialize()
    return tools


@pytest.fixture
async def orchestrator(mock_memory, mock_tools, mock_event_bus):
    """Orchestrator fixture"""
    config = {...}
    orch = CoreOrchestrator(config)
    orch.memory = mock_memory
    orch.tools = mock_tools
    orch.event_bus = mock_event_bus
    await orch.initialize()
    yield orch
    await orch.shutdown()
```

---

## Стиль кода

### Python Style Guide

Следуем PEP 8 с некоторыми дополнениями:

```python
# Imports
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_agent import BaseAgent
from ..models.agent import AgentContext

# Constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 300

# Classes
class MyClass:
    """Class docstring"""
    
    def __init__(self, param: str):
        self.param = param
    
    async def method(self, arg: int) -> str:
        """Method docstring"""
        return f"{self.param}: {arg}"

# Functions
async def my_function(param: str) -> Dict[str, Any]:
    """Function docstring"""
    result = await some_async_operation(param)
    return {"result": result}
```

### Docstrings

```python
def function(param1: str, param2: int) -> bool:
    """
    Short description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param1 is empty
    """
    pass
```

### Type Hints

Всегда используйте type hints:

```python
from typing import Dict, List, Optional, Any

def process(data: Dict[str, Any]) -> Optional[List[str]]:
    pass

async def async_process(items: List[str]) -> Dict[str, int]:
    pass
```

### Форматирование

```bash
# Black для форматирования
black architecture/

# Ruff для линтинга
ruff check architecture/

# MyPy для проверки типов
mypy architecture/

# isort для сортировки imports
isort architecture/
```

---

## Отладка

### Логирование

```python
import logging

logger = logging.getLogger(__name__)

class MyAgent(BaseAgent):
    async def execute(self, context: AgentContext) -> AgentResult:
        logger.info(f"Starting execution for {context.request}")
        
        try:
            result = await self._do_work()
            logger.debug(f"Work completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Error during execution: {e}", exc_info=True)
            raise
```

### Debugging с breakpoints

```python
# Использовать pdb
import pdb; pdb.set_trace()

# Или ipdb для лучшего опыта
import ipdb; ipdb.set_trace()

# Или встроенный breakpoint() (Python 3.7+)
breakpoint()
```

### Event monitoring

```python
# Подписаться на все события для отладки
def debug_handler(data):
    print(f"Event: {data}")

event_bus.on('*', debug_handler)
```

### Memory inspection

```python
# Проверить содержимое памяти
results = await memory.search("", limit=100)
for result in results:
    print(result)
```

---

## Deployment

### Production checklist

- [ ] Все тесты проходят
- [ ] Покрытие тестами > 80%
- [ ] Линтинг без ошибок
- [ ] Type checking без ошибок
- [ ] Документация обновлена
- [ ] CHANGELOG обновлен
- [ ] Версия обновлена
- [ ] Environment variables настроены
- [ ] Логирование настроено
- [ ] Мониторинг настроен

### Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "src.main"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  kiro:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    ports:
      - "8000:8000"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Environment variables

```bash
# Production
export OPENAI_API_KEY=sk-...
export LOG_LEVEL=INFO
export DEBUG=false

# Staging
export OPENAI_API_KEY=sk-...
export LOG_LEVEL=DEBUG
export DEBUG=true
```

---

## Best Practices

### 1. Async/Await

```python
# Good
async def process_items(items: List[str]) -> List[str]:
    tasks = [process_item(item) for item in items]
    return await asyncio.gather(*tasks)

# Bad - blocking
def process_items(items: List[str]) -> List[str]:
    return [process_item(item) for item in items]
```

### 2. Error Handling

```python
# Good
try:
    result = await agent.execute(context)
except ValueError as e:
    logger.error(f"Validation error: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise

# Bad - catching everything
try:
    result = await agent.execute(context)
except:
    pass
```

### 3. Resource Management

```python
# Good
async with memory_system() as memory:
    result = await memory.search(query)

# Or
memory = MemorySystem()
try:
    await memory.initialize()
    result = await memory.search(query)
finally:
    await memory.shutdown()

# Bad - no cleanup
memory = MemorySystem()
await memory.initialize()
result = await memory.search(query)
```

### 4. Configuration

```python
# Good - use config
config = load_config('config.yaml')
timeout = config['orchestrator']['timeout']

# Bad - hardcoded
timeout = 300
```

---

## Troubleshooting

### Common Issues

#### 1. ChromaDB connection errors

```python
# Check if ChromaDB is running
import chromadb
client = chromadb.Client()
```

#### 2. Async context errors

```python
# Make sure to use async context
async def main():
    orchestrator = CoreOrchestrator(config)
    await orchestrator.initialize()
    # ... work ...
    await orchestrator.shutdown()

# Run with asyncio
asyncio.run(main())
```

#### 3. Import errors

```python
# Use relative imports within package
from .base_agent import BaseAgent
from ..models.agent import AgentContext

# Use absolute imports from outside
from architecture.core.base_agent import BaseAgent
```

---

## Contributing

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Напишите тесты
4. Реализуйте feature
5. Убедитесь что все тесты проходят
6. Закоммитьте изменения (`git commit -m 'Add amazing feature'`)
7. Запушьте в branch (`git push origin feature/amazing-feature`)
8. Откройте Pull Request

---

## Resources

- [Python Async/Await](https://docs.python.org/3/library/asyncio.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [Black Code Style](https://black.readthedocs.io/)
