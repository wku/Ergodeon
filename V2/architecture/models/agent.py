"""
Agent-related Pydantic models
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class AgentConfig(BaseModel):
    """Agent configuration"""
    name: str = Field(..., description="Unique agent identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Agent purpose")
    version: str = Field(default="1.0.0", description="Agent version")
    allowed_tools: List[str] = Field(default_factory=list, description="Tools agent can use")
    max_iterations: int = Field(default=10, description="Max execution iterations")
    timeout: int = Field(default=300, description="Timeout in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class UserRequest(BaseModel):
    """User request model"""
    text: str = Field(..., description="User's request text")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Request timestamp")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class IntentType(str, Enum):
    """Request intent types"""
    SPEC = "spec"
    TASK_EXECUTION = "task-execution"
    ANALYSIS = "analysis"
    GENERAL = "general"


class SpecType(str, Enum):
    """Spec types"""
    FEATURE = "feature"
    BUGFIX = "bugfix"


class WorkflowTypeEnum(str, Enum):
    """Workflow types"""
    REQUIREMENTS_FIRST = "requirements-first"
    DESIGN_FIRST = "design-first"


class IntentAnalysis(BaseModel):
    """Analysis of user intent"""
    type: IntentType = Field(..., description="Request type")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    context: List[Dict[str, Any]] = Field(default_factory=list, description="Relevant context from memory")
    spec_type: Optional[SpecType] = Field(None, description="Spec type if applicable")
    workflow_type: Optional[WorkflowTypeEnum] = Field(None, description="Workflow type if applicable")
    feature_name: Optional[str] = Field(None, description="Feature name in kebab-case")
    suggested_agent: Optional[str] = Field(None, description="Suggested agent to handle request")
    confidence: float = Field(default=0.0, description="Confidence score 0-1")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional analysis data")


class AgentContext(BaseModel):
    """Context passed to agent for execution"""
    request: str = Field(..., description="Original user request")
    intent: IntentAnalysis = Field(..., description="Analyzed intent")
    workflow_state: Optional[Any] = Field(None, description="Current workflow state")
    memory: List[Dict[str, Any]] = Field(default_factory=list, description="Relevant memory entries")
    preset: Optional[str] = Field(None, description="Preset/phase to execute")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentResultStatus(str, Enum):
    """Agent result status"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    DELEGATED = "delegated"


class AgentResult(BaseModel):
    """Result from agent execution"""
    status: AgentResultStatus = Field(..., description="Execution status")
    agent_name: str = Field(..., description="Agent that produced result")
    result: Dict[str, Any] = Field(default_factory=dict, description="Result data")
    files_created: List[str] = Field(default_factory=list, description="Files created")
    files_modified: List[str] = Field(default_factory=list, description="Files modified")
    output: str = Field(default="", description="Human-readable output")
    next_action: Optional[Dict[str, Any]] = Field(None, description="Suggested next action")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Result timestamp")
