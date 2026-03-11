"""
Workflow-related Pydantic models
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class WorkflowType(str, Enum):
    """Workflow types"""
    FEATURE_REQUIREMENTS_FIRST = "feature-requirements-first-workflow"
    FEATURE_DESIGN_FIRST = "feature-design-first-workflow"
    BUGFIX = "bugfix-workflow"
    GENERAL_TASK = "general-task-execution"
    SPEC_TASK = "spec-task-execution"
    CONTEXT_GATHER = "context-gatherer"
    CUSTOM_AGENT = "custom-agent-creator"


class PhaseStatus(str, Enum):
    """Phase execution status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_APPROVAL = "requires_approval"


class Phase(BaseModel):
    """Workflow phase"""
    name: str = Field(..., description="Phase name (requirements, design, tasks)")
    status: PhaseStatus = Field(default=PhaseStatus.NOT_STARTED, description="Phase status")
    started_at: Optional[datetime] = Field(None, description="Phase start time")
    completed_at: Optional[datetime] = Field(None, description="Phase completion time")
    files_created: List[str] = Field(default_factory=list, description="Files created in this phase")
    approved: bool = Field(default=False, description="User approval received")
    result: Optional[Dict[str, Any]] = Field(None, description="Phase result data")


class WorkflowState(BaseModel):
    """State of a workflow execution"""
    id: str = Field(..., description="Unique workflow ID")
    type: WorkflowType = Field(..., description="Workflow type")
    feature_name: str = Field(..., description="Feature/bugfix name")
    spec_path: str = Field(..., description="Path to spec directory")
    
    current_phase: Optional[str] = Field(None, description="Current phase name")
    current_agent: Optional[str] = Field(None, description="Current agent executing")
    
    phases: Dict[str, Phase] = Field(default_factory=dict, description="Phase states")
    
    created_at: datetime = Field(default_factory=datetime.now, description="Workflow creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    completed_at: Optional[datetime] = Field(None, description="Workflow completion time")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def get_phase(self, phase_name: str) -> Optional[Phase]:
        """Get phase by name"""
        return self.phases.get(phase_name)
    
    def update_phase(self, phase_name: str, **kwargs) -> None:
        """Update phase data"""
        if phase_name not in self.phases:
            self.phases[phase_name] = Phase(name=phase_name)
        
        phase = self.phases[phase_name]
        for key, value in kwargs.items():
            if hasattr(phase, key):
                setattr(phase, key, value)
        
        self.updated_at = datetime.now()
    
    def is_phase_complete(self, phase_name: str) -> bool:
        """Check if phase is complete"""
        phase = self.get_phase(phase_name)
        return phase is not None and phase.status == PhaseStatus.COMPLETED
    
    def get_next_phase(self) -> Optional[str]:
        """Determine next phase based on workflow type"""
        phase_sequences = {
            WorkflowType.FEATURE_REQUIREMENTS_FIRST: ["requirements", "design", "tasks"],
            WorkflowType.FEATURE_DESIGN_FIRST: ["design", "requirements", "tasks"],
            WorkflowType.BUGFIX: ["requirements", "design", "tasks"]
        }
        
        sequence = phase_sequences.get(self.type)
        if not sequence:
            return None
        
        for phase in sequence:
            if not self.is_phase_complete(phase):
                return phase
        
        return None  # All phases complete
