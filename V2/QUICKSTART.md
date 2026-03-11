# Kiro Agent System - Quick Start Guide

Быстрое руководство по запуску системы агентов Kiro.

## Установка

### 1. Требования

- Python 3.11 или выше
- pip (менеджер пакетов Python)
- Git

### 2. Клонирование репозитория

```bash
git clone <repository-url>
cd kiro-agent-system
```

### 3. Установка зависимостей

```bash
cd architecture

# Создать виртуальное окружение
python -m venv venv

# Активировать виртуальное окружение
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

```bash
# Скопировать пример
cp .env.example .env

# Отредактировать .env и добавить API ключи
nano .env  # или используйте любой редактор
```

Минимальная конфигурация `.env`:
```bash
OPENAI_API_KEY=your_openai_api_key_here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
```

## Запуск

### Интерактивный режим

```bash
python -m src.main
```

Вы увидите:
```
============================================================
Kiro Agent System - Interactive Mode
============================================================

Commands:
  - Type your request naturally
  - 'help' - Show help
  - 'exit' or 'quit' - Exit
============================================================

> 
```

### Примеры команд

#### 1. Создать feature spec

```
> Add user authentication with JWT tokens
```

Система спросит:
- Feature или Bugfix? → Выберите "Feature"
- Requirements или Design first? → Выберите "Requirements"

Результат:
- Создаст `.kiro/specs/user-authentication/requirements.md`
- Создаст `.kiro/specs/user-authentication/design.md`
- Создаст `.kiro/specs/user-authentication/tasks.md`

#### 2. Исправить баг

```
> Fix crash when quantity is zero
```

Система спросит:
- Feature или Bugfix? → Выберите "Bugfix"

Результат:
- Создаст `.kiro/specs/quantity-zero-crash/bugfix.md`
- Создаст `.kiro/specs/quantity-zero-crash/design.md`
- Создаст `.kiro/specs/quantity-zero-crash/tasks.md`

#### 3. Выполнить задачу

```
> Execute task 2 from user-authentication spec
```

Результат:
- Выполнит задачу 2 из спецификации
- Создаст/изменит файлы
- Запустит тесты

#### 4. Выполнить все задачи

```
> Run all tasks from user-authentication spec
```

Результат:
- Выполнит все задачи последовательно
- Обновит статус каждой задачи
- Запустит тесты после каждой задачи

#### 5. Общие задачи

```
> Refactor the UserList component
```

Результат:
- Проанализирует компонент
- Применит рефакторинг
- Запустит тесты

#### 6. Анализ кода

```
> How is authentication implemented?
```

Результат:
- Найдет релевантные файлы
- Проанализирует код
- Предоставит summary

### Однократное выполнение команды

```bash
python -m src.main "Create a login form component"
```

## Тестирование

### Запуск всех тестов

```bash
pytest
```

### Запуск с покрытием

```bash
pytest --cov=. --cov-report=html
```

### Запуск конкретного теста

```bash
pytest tests/unit/test_orchestrator.py
```

## Структура проекта

```
architecture/
├── src/
│   ├── main.py          # Точка входа
│   └── cli.py           # CLI интерфейс
├── core/                # Ядро системы
│   ├── orchestrator.py  # Главный координатор
│   ├── base_agent.py    # Базовый класс агента
│   ├── memory.py        # Векторная память
│   ├── events.py        # Event bus
│   └── state.py         # State manager
├── agents/              # Реализации агентов
│   ├── workflow/        # Workflow агенты
│   ├── execution/       # Execution агенты
│   └── analysis/        # Analysis агенты
├── models/              # Pydantic модели
├── tools/               # Инструменты
├── utils/               # Утилиты
├── tests/               # Тесты
├── examples/            # Примеры
├── config.yaml          # Конфигурация
└── requirements.txt     # Зависимости
```

## Конфигурация

Отредактируйте `config.yaml` для настройки:

```yaml
orchestrator:
  max_concurrent_agents: 10
  timeout: 300

memory:
  db_path: "./data/chroma"
  embedding_model: "text-embedding-3-small"

llm:
  provider: "openai"
  model: "gpt-4-turbo-preview"
  temperature: 0.7
  max_tokens: 4000

agents:
  general_task_execution:
    enabled: true
    tools: ["readFile", "fsWrite", ...]
```

## Troubleshooting

### Проблема: ModuleNotFoundError

**Решение**: Убедитесь, что виртуальное окружение активировано и зависимости установлены:
```bash
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
```

### Проблема: ChromaDB connection error

**Решение**: ChromaDB создаст базу данных автоматически. Убедитесь, что папка `data/` доступна для записи:
```bash
mkdir -p data/chroma
```

### Проблема: OpenAI API key not found

**Решение**: Проверьте файл `.env`:
```bash
cat .env | grep OPENAI_API_KEY
```

Убедитесь, что ключ установлен правильно.

### Проблема: Tests fail

**Решение**: Запустите тесты с verbose:
```bash
pytest -v
```

Проверьте логи в `logs/kiro.log`.

## Следующие шаги

1. **Изучите документацию**:
   - [README.md](README.md) - Полный обзор
   - [DEVELOPMENT.md](DEVELOPMENT.md) - Руководство по разработке
   - [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) - Архитектура

2. **Попробуйте примеры**:
   ```bash
   python architecture/examples/basic_usage.py
   ```

3. **Создайте свой первый spec**:
   - Запустите CLI
   - Введите описание feature
   - Следуйте инструкциям системы

4. **Изучите созданные файлы**:
   - Посмотрите `.kiro/specs/` для спецификаций
   - Изучите структуру документов

## Полезные команды

```bash
# Запустить CLI
python -m src.main

# Запустить тесты
pytest

# Проверить код
black architecture/
ruff check architecture/
mypy architecture/

# Просмотреть логи
tail -f logs/kiro.log

# Очистить кэш
rm -rf data/chroma/*
rm -rf __pycache__
```

## Получение помощи

- Документация: [README.md](README.md)
- Примеры: [architecture/examples/](architecture/examples/)
- Issues: Создайте issue в репозитории

## Лицензия

MIT
