"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from typing import Dict, Any

from core.memory import MemorySystem
from core.events import EventBus
from core.state import StateManager
from core.orchestrator import CoreOrchestrator
from tools.registry import ToolRegistry
from models.agent import AgentConfig


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_memory():
    """Mock memory system"""
    memory = MemorySystem({'db_path': ':memory:', 'collection_name': 'test'})
    await memory.initialize()
    yield memory
    await memory.shutdown()


@pytest.fixture
def mock_event_bus():
    """Mock event bus"""
    return EventBus()


@pytest.fixture
def mock_state():
    """Mock state manager"""
    return StateManager()


@pytest.fixture
async def mock_tools():
    """Mock tool registry"""
    tools = ToolRegistry()
    await tools.initialize()
    yield tools


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration"""
    return AgentConfig(
        name="test-agent",
        display_name="Test Agent",
        description="Agent for testing",
        allowed_tools=["readFile", "fsWrite"],
        max_iterations=5,
        timeout=60
    )


@pytest.fixture
async def orchestrator(mock_memory, mock_tools, mock_event_bus, mock_state):
    """Orchestrator fixture"""
    config = {
        'orchestrator': {
            'max_concurrent_agents': 5,
            'timeout': 300
        },
        'memory': {
            'db_path': ':memory:'
        }
    }
    
    orch = CoreOrchestrator(config)
    orch.memory = mock_memory
    orch.tools = mock_tools
    orch.event_bus = mock_event_bus
    orch.state = mock_state
    
    await orch.initialize()
    yield orch
    await orch.shutdown()


@pytest.fixture
def sample_user_request():
    """Sample user request"""
    from models.agent import UserRequest
    return UserRequest(
        text="Create a login form",
        user_id="test_user",
        session_id="test_session"
    )


@pytest.fixture
def sample_agent_context(sample_user_request):
    """Sample agent context"""
    from models.agent import AgentContext, IntentAnalysis, IntentType
    
    intent = IntentAnalysis(
        type=IntentType.GENERAL,
        keywords=["login", "form"],
        feature_name="login-form"
    )
    
    return AgentContext(
        request=sample_user_request.text,
        intent=intent,
        preset=None
    )


# Helper functions

def create_mock_file_system():
    """Create mock file system for testing"""
    return {
        'src/app.py': 'print("Hello")',
        'src/utils.py': 'def helper(): pass',
        'tests/test_app.py': 'def test_app(): pass'
    }


def create_mock_spec_files():
    """Create mock spec files"""
    return {
        'requirements.md': '# Requirements\n\n## User Stories\n1. Story 1',
        'design.md': '# Design\n\n## Architecture\n...',
        'tasks.md': '# Tasks\n\n- [ ] 1. Task 1\n- [ ] 2. Task 2'
    }
