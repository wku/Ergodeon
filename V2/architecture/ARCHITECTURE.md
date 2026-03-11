# Kiro Agent System - Python Architecture

**Version**: 1.0.0  
**Language**: Python 3.11+  
**Architecture**: Event-Driven, Async, Memory-Enhanced

---

## Overview

Асинхронная система агентов с векторной базой данных для управления контекстом и памятью.

### Key Features

- **Async/Await**: Все операции асинхронные (asyncio)
- **Event-Driven**: Pub/Sub для коммуникации агентов
- **Vector Memory**: ChromaDB для семантического поиска
- **State Management**: Централизованное управление состоянием
- **Type-Safe**: Полная типизация с Pydantic
- **Extensible**: Легко добавлять новых агентов

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │     CLI      │  │   FastAPI    │  │   Streamlit  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Orchestration Layer                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │           CoreOrchestrator                        │  │
│  │  - Request routing                                │  │
│  │  - Agent lifecycle management                     │  │
│  │  - State coordination                             │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                      Agent Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Workflow │  │Execution │  │ Analysis │             │
│  │  Agents  │  │  Agents  │  │  Agents  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Memory  │  │  Event   │  │   Tool   │             │
│  │  System  │  │   Bus    │  │ Registry │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## Technology Stack

- **Runtime**: Python 3.11+
- **Async**: asyncio, aiofiles
- **Vector DB**: ChromaDB
- **Event Bus**: asyncio.Queue + EventEmitter
- **State**: Pydantic models + Redis (optional)
- **LLM**: OpenAI API / Anthropic Claude (via litellm)
- **Web**: FastAPI (optional API)
- **Testing**: pytest + pytest-asyncio

---

## Directory Structure

```
src/
├── core/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── base_agent.py
│   ├── memory.py
│   ├── events.py
│   └── state.py
├── agents/
│   ├── __init__.py
│   ├── workflow/
│   │   ├── __init__.py
│   │   ├── requirements_first.py
│   │   ├── design_first.py
│   │   └── bugfix.py
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── general_task.py
│   │   └── spec_task.py
│   └── analysis/
│       ├── __init__.py
│       └── context_gatherer.py
├── tools/
│   ├── __init__.py
│   ├── registry.py
│   ├── filesystem.py
│   ├── code.py
│   └── shell.py
├── models/
│   ├── __init__.py
│   ├── agent.py
│   ├── workflow.py
│   └── task.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   └── config.py
└── main.py
```

---

## Dependencies

```
# Core
python = "^3.11"
asyncio
aiofiles

# Data & Validation
pydantic = "^2.0"
pydantic-settings

# Vector DB
chromadb = "^0.4"

# LLM
litellm = "^1.0"
openai = "^1.0"
anthropic = "^0.18"

# Optional
fastapi = "^0.109"  # API
uvicorn = "^0.27"   # ASGI server
redis = "^5.0"      # State persistence
streamlit = "^1.30" # UI

# Dev
pytest = "^8.0"
pytest-asyncio = "^0.23"
black = "^24.0"
ruff = "^0.1"
mypy = "^1.8"
```

---

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install ChromaDB
pip install chromadb

# Setup environment
cp .env.example .env
# Edit .env with your API keys
```

---

## Configuration

```python
# config.yaml
orchestrator:
  max_concurrent_agents: 10
  timeout: 300

memory:
  db_path: "./data/chroma"
  embedding_model: "text-embedding-3-small"
  max_entries: 10000
  retention_days: 30

llm:
  provider: "openai"  # or "anthropic"
  model: "gpt-4-turbo-preview"
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.7
  max_tokens: 4000

agents:
  general_task_execution:
    enabled: true
    tools: ["fs", "code", "shell", "search"]
  
  context_gatherer:
    enabled: true
    tools: ["fs", "code", "search"]
  
  spec_task_execution:
    enabled: true
    tools: ["fs", "code", "shell", "diagnostics"]
```

---

## Usage Examples

### CLI Usage

```bash
# Start interactive session
python -m src.main

# Execute single command
python -m src.main "Create a Button component"

# Run spec workflow
python -m src.main spec create --type feature --name user-auth

# Execute task
python -m src.main spec task execute --spec user-auth --task 2
```

### Python API

```python
import asyncio
from src.core.orchestrator import CoreOrchestrator
from src.models.agent import UserRequest

async def main():
    # Initialize orchestrator
    orchestrator = CoreOrchestrator()
    await orchestrator.initialize()
    
    # Process request
    request = UserRequest(
        text="Create a login form component",
        user_id="user123",
        session_id="session456"
    )
    
    result = await orchestrator.process_request(request)
    print(result)
    
    # Shutdown
    await orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

### FastAPI Integration

```python
from fastapi import FastAPI
from src.core.orchestrator import CoreOrchestrator

app = FastAPI()
orchestrator = CoreOrchestrator()

@app.on_event("startup")
async def startup():
    await orchestrator.initialize()

@app.post("/api/request")
async def process_request(request: UserRequest):
    result = await orchestrator.process_request(request)
    return result

@app.on_event("shutdown")
async def shutdown():
    await orchestrator.shutdown()
```

---

## Key Classes

### 1. CoreOrchestrator
- Main coordinator
- Routes requests to agents
- Manages lifecycle

### 2. BaseAgent
- Abstract base for all agents
- Async execution
- Memory integration

### 3. MemorySystem
- ChromaDB integration
- Semantic search
- Context storage

### 4. EventBus
- Pub/Sub messaging
- Agent communication
- Event history

### 5. StateManager
- Workflow state
- Task tracking
- Session management

### 6. ToolRegistry
- Tool management
- Permission control
- Execution logging

---

## Next Steps

1. Implement core classes
2. Create agent implementations
3. Setup testing framework
4. Add CLI interface
5. Optional: FastAPI + Streamlit UI
