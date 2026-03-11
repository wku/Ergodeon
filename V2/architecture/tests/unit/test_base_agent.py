"""
Tests for BaseAgent
"""

import pytest
from core.base_agent import BaseAgent, AgentStatus
from models.agent import AgentContext, AgentResult, AgentResultStatus


class TestAgent(BaseAgent):
    """Test agent implementation"""
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Test execution"""
        return AgentResult(
            status=AgentResultStatus.SUCCESS,
            agent_name=self.config.name,
            output="Test completed"
        )
    
    async def validate(self, context: AgentContext) -> bool:
        """Test validation"""
        return context.request is not None
    
    def process_result(self, result) -> AgentResult:
        """Test result processing"""
        if isinstance(result, AgentResult):
            return result
        return AgentResult(
            status=AgentResultStatus.SUCCESS,
            agent_name=self.config.name,
            result=result
        )


@pytest.mark.asyncio
async def test_agent_initialization(sample_agent_config, mock_memory, mock_tools, mock_event_bus):
    """Test agent initializes correctly"""
    agent = TestAgent(sample_agent_config, mock_memory, mock_tools, mock_event_bus)
    
    assert agent.config == sample_agent_config
    assert agent.status == AgentStatus.IDLE
    assert agent.context is None


@pytest.mark.asyncio
async def test_agent_run_success(sample_agent_config, mock_memory, mock_tools, mock_event_bus, sample_agent_context):
    """Test successful agent execution"""
    agent = TestAgent(sample_agent_config, mock_memory, mock_tools, mock_event_bus)
    
    result = await agent.run(sample_agent_context)
    
    assert result.status == AgentResultStatus.SUCCESS
    assert result.agent_name == sample_agent_config.name
    assert agent.status == AgentStatus.COMPLETED


@pytest.mark.asyncio
async def test_agent_validation(sample_agent_config, mock_memory, mock_tools, mock_event_bus, sample_agent_context):
    """Test agent validation"""
    agent = TestAgent(sample_agent_config, mock_memory, mock_tools, mock_event_bus)
    
    # Valid context
    is_valid = await agent.validate(sample_agent_context)
    assert is_valid is True
    
    # Invalid context
    invalid_context = AgentContext(request=None, intent=sample_agent_context.intent)
    is_valid = await agent.validate(invalid_context)
    assert is_valid is False


@pytest.mark.asyncio
async def test_agent_get_status(sample_agent_config, mock_memory, mock_tools, mock_event_bus):
    """Test agent status retrieval"""
    agent = TestAgent(sample_agent_config, mock_memory, mock_tools, mock_event_bus)
    
    assert agent.get_status() == AgentStatus.IDLE


@pytest.mark.asyncio
async def test_agent_get_config(sample_agent_config, mock_memory, mock_tools, mock_event_bus):
    """Test agent config retrieval"""
    agent = TestAgent(sample_agent_config, mock_memory, mock_tools, mock_event_bus)
    
    config = agent.get_config()
    assert config == sample_agent_config


@pytest.mark.asyncio
async def test_agent_search_memory(sample_agent_config, mock_memory, mock_tools, mock_event_bus):
    """Test agent memory search"""
    agent = TestAgent(sample_agent_config, mock_memory, mock_tools, mock_event_bus)
    
    # Store some data
    await mock_memory.store_context("test", {"key": "value"})
    
    # Search
    results = await agent.search_memory("test", limit=5)
    
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_agent_update_progress(sample_agent_config, mock_memory, mock_tools, mock_event_bus):
    """Test agent progress updates"""
    agent = TestAgent(sample_agent_config, mock_memory, mock_tools, mock_event_bus)
    
    events = []
    
    def progress_handler(data):
        events.append(data)
    
    agent.on('agent:progress', progress_handler)
    
    agent.update_progress(50, "Halfway done")
    
    assert len(events) == 1
    assert events[0]['progress'] == 50
    assert events[0]['message'] == "Halfway done"
