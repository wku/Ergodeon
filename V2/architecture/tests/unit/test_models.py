"""
Tests for Pydantic models
"""

import pytest
from datetime import datetime

from models.agent import (
    AgentConfig,
    UserRequest,
    IntentAnalysis,
    AgentContext,
    AgentResult,
    IntentType,
    AgentResultStatus
)
from models.workflow import WorkflowState, WorkflowType, Phase, PhaseStatus
from models.task import Task, TaskStatus, TaskState


def test_agent_config_creation():
    """Test AgentConfig model"""
    config = AgentConfig(
        name="test-agent",
        display_name="Test Agent",
        description="Test description",
        allowed_tools=["readFile", "fsWrite"]
    )
    
    assert config.name == "test-agent"
    assert config.display_name == "Test Agent"
    assert len(config.allowed_tools) == 2


def test_user_request_creation():
    """Test UserRequest model"""
    request = UserRequest(
        text="Create a component",
        user_id="user123",
        session_id="session456"
    )
    
    assert request.text == "Create a component"
    assert request.user_id == "user123"
    assert isinstance(request.timestamp, datetime)


def test_intent_analysis_creation():
    """Test IntentAnalysis model"""
    intent = IntentAnalysis(
        type=IntentType.SPEC,
        keywords=["auth", "login"],
        feature_name="user-auth"
    )
    
    assert intent.type == IntentType.SPEC
    assert len(intent.keywords) == 2
    assert intent.feature_name == "user-auth"


def test_agent_context_creation():
    """Test AgentContext model"""
    intent = IntentAnalysis(
        type=IntentType.GENERAL,
        keywords=["test"]
    )
    
    context = AgentContext(
        request="Test request",
        intent=intent,
        preset="test"
    )
    
    assert context.request == "Test request"
    assert context.intent == intent
    assert context.preset == "test"


def test_agent_result_creation():
    """Test AgentResult model"""
    result = AgentResult(
        status=AgentResultStatus.SUCCESS,
        agent_name="test-agent",
        output="Task completed",
        files_created=["file1.py", "file2.py"]
    )
    
    assert result.status == AgentResultStatus.SUCCESS
    assert result.agent_name == "test-agent"
    assert len(result.files_created) == 2


def test_workflow_state_creation():
    """Test WorkflowState model"""
    workflow = WorkflowState(
        id="workflow-123",
        type=WorkflowType.FEATURE_REQUIREMENTS_FIRST,
        feature_name="user-auth",
        spec_path=".kiro/specs/user-auth/"
    )
    
    assert workflow.id == "workflow-123"
    assert workflow.type == WorkflowType.FEATURE_REQUIREMENTS_FIRST
    assert workflow.feature_name == "user-auth"


def test_workflow_phase_management():
    """Test workflow phase management"""
    workflow = WorkflowState(
        id="workflow-123",
        type=WorkflowType.FEATURE_REQUIREMENTS_FIRST,
        feature_name="test",
        spec_path=".kiro/specs/test/"
    )
    
    # Update phase
    workflow.update_phase("requirements", status=PhaseStatus.COMPLETED)
    
    assert workflow.is_phase_complete("requirements")
    assert not workflow.is_phase_complete("design")


def test_task_creation():
    """Test Task model"""
    task = Task(
        id="1",
        text="Implement feature",
        status=TaskStatus.NOT_STARTED,
        required=True
    )
    
    assert task.id == "1"
    assert task.text == "Implement feature"
    assert task.status == TaskStatus.NOT_STARTED
    assert task.required is True


def test_task_state_management():
    """Test TaskState model"""
    task_state = TaskState(
        spec_path=".kiro/specs/test/"
    )
    
    # Add task
    task = Task(id="1", text="Task 1", required=True)
    task_state.tasks["1"] = task
    
    # Get task
    retrieved = task_state.get_task("1")
    assert retrieved == task
    
    # Update task
    task_state.update_task("1", status=TaskStatus.COMPLETED)
    assert task_state.get_task("1").status == TaskStatus.COMPLETED


def test_task_state_incomplete_tasks():
    """Test getting incomplete tasks"""
    task_state = TaskState(spec_path=".kiro/specs/test/")
    
    # Add tasks
    task_state.tasks["1"] = Task(id="1", text="Task 1", required=True, status=TaskStatus.NOT_STARTED)
    task_state.tasks["2"] = Task(id="2", text="Task 2", required=True, status=TaskStatus.COMPLETED)
    task_state.tasks["3"] = Task(id="3", text="Task 3", required=False, status=TaskStatus.NOT_STARTED)
    
    incomplete = task_state.get_incomplete_required_tasks()
    
    assert len(incomplete) == 1
    assert incomplete[0].id == "1"
