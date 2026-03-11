# Docker Guide - Ergodeon Agent System

Руководство по использованию Docker для Ergodeon Agent System.

## Быстрый старт

### 1. Подготовка

```bash
# Скопировать пример переменных окружения
cp .env.example .env

# Отредактировать .env и добавить API ключи
nano .env
```

### 2. Запуск с Docker Compose

```bash
# Собрать и запустить
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановить
docker-compose down
```

### 3. Использование

```bash
# Открыть интерактивную сессию
docker-compose exec ergodeon python -m src.main

# Выполнить команду
docker-compose exec ergodeon python -m src.main "Create a login form"

# Открыть shell
docker-compose exec ergodeon /bin/bash
```

## Конфигурации

### Production (по умолчанию)

```bash
docker-compose up -d
```

Включает:
- ergodeon Agent System
- Redis (state management)
- ChromaDB (vector database)

### С API сервером

```bash
docker-compose --profile api up -d
```

Дополнительно включает:
- FastAPI REST API на порту 8002

### С UI

```bash
docker-compose --profile ui up -d
```

Дополнительно включает:
- Streamlit UI на порту 8501

### Все сервисы

```bash
docker-compose --profile api --profile ui up -d
```

### Development

```bash
docker-compose -f docker-compose.dev.yml up -d
```

Особенности:
- Hot reload (монтирование исходного кода)
- DEBUG режим
- Debugpy порт 5678

## Makefile команды

```bash
# Сборка
make docker-build

# Запуск
make docker-up

# Остановка
make docker-down

# Логи
make docker-logs

# Shell
make docker-shell

# Очистка
make docker-clean

# С профилями
make docker-up-api
make docker-up-ui
make docker-up-all

# Пересборка
make docker-rebuild
```

## Структура сервисов

### ergodeon (main)
- **Порт**: 8000
- **Описание**: Основное приложение ergodeon
- **Volumes**:
  - `./data:/app/data` - Данные ChromaDB
  - `./logs:/app/logs` - Логи
  - `./.ergodeon:/app/.ergodeon` - Спецификации
  - `./workspace:/app/workspace` - Рабочее пространство

### redis
- **Порт**: 6379
- **Описание**: State management
- **Volume**: `redis-data:/data`

### chromadb
- **Порт**: 8001
- **Описание**: Vector database
- **Volume**: `chroma-data:/chroma/chroma`

### api (optional)
- **Порт**: 8002
- **Описание**: REST API
- **Profile**: `api`

### ui (optional)
- **Порт**: 8501
- **Описание**: Streamlit UI
- **Profile**: `ui`

## Переменные окружения

### Обязательные

```bash
OPENAI_API_KEY=sk-...
```

### Опциональные

```bash
# LLM
ANTHROPIC_API_KEY=...
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Logging
LOG_LEVEL=INFO

# Performance
MAX_CONCURRENT_AGENTS=10
AGENT_TIMEOUT=300
```

## Volumes

### Persistent data

```bash
# Просмотр volumes
docker volume ls | grep ergodeon

# Удаление volumes
docker-compose down -v
```

### Backup

```bash
# Backup ChromaDB
docker run --rm -v ergodeon_chroma-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/chroma-backup.tar.gz -C /data .

# Restore ChromaDB
docker run --rm -v ergodeon_chroma-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/chroma-backup.tar.gz -C /data
```

## Troubleshooting

### Проблема: Container не запускается

```bash
# Проверить логи
docker-compose logs ergodeon

# Проверить статус
docker-compose ps
```

### Проблема: API key не найден

```bash
# Проверить переменные окружения
docker-compose exec ergodeon env | grep API_KEY

# Пересоздать контейнер
docker-compose up -d --force-recreate ergodeon
```

### Проблема: ChromaDB connection error

```bash
# Проверить ChromaDB
docker-compose logs chromadb

# Перезапустить ChromaDB
docker-compose restart chromadb
```

### Проблема: Permission denied

```bash
# Исправить права
sudo chown -R $USER:$USER data logs

# Или создать директории заранее
mkdir -p data/chroma logs
```

## Development

### Hot reload

```bash
# Использовать dev compose
docker-compose -f docker-compose.dev.yml up -d

# Изменения в коде применяются автоматически
```

### Debugging

```bash
# Подключиться к debugpy
# В VS Code: Remote Attach, localhost:5678
```

### Тестирование

```bash
# Запустить тесты в контейнере
docker-compose exec ergodeon pytest

# С покрытием
docker-compose exec ergodeon pytest --cov=.
```

## Production

### Best practices

1. **Используйте secrets для API keys**:
```yaml
secrets:
  openai_api_key:
    external: true
```

2. **Ограничьте ресурсы**:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

3. **Используйте health checks**:
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
  interval: 30s
  timeout: 10s
  retries: 3
```

4. **Логирование**:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Scaling

```bash
# Масштабирование API
docker-compose up -d --scale api=3

# С load balancer (nginx)
# См. docker-compose.prod.yml
```

## Мониторинг

### Логи

```bash
# Все логи
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f ergodeon

# Последние N строк
docker-compose logs --tail=100 ergodeon
```

### Метрики

```bash
# Использование ресурсов
docker stats

# Конкретный контейнер
docker stats ergodeon-agent-system
```

### Health checks

```bash
# Проверить health
docker inspect --format='{{.State.Health.Status}}' ergodeon-agent-system
```

## Очистка

```bash
# Остановить и удалить контейнеры
docker-compose down

# Удалить volumes
docker-compose down -v

# Удалить images
docker-compose down --rmi all

# Полная очистка
make docker-clean
```

## Дополнительные ресурсы

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Best Practices](https://docs.docker.com/develop/dev-best-practices/)
