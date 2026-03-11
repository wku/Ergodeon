"""
Task-related Pydantic models
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Task execution status"""
    NOT_STARTED = "not_started"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskType(str, Enum):
    """Task types"""
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    BUGFIX = "bugfix"


class Task(BaseModel):
    """Individual task"""
    id: str = Field(..., description="Task ID (e.g., '1', '1.1', '2')")
    text: str = Field(..., description="Task description")
    status: TaskStatus = Field(default=TaskStatus.NOT_STARTED, description="Task status")
    type: TaskType = Field(default=TaskType.IMPLEMENTATION, description="Task type")
    
    parent_id: Optional[str] = Field(None, description="Parent task ID if sub-task")
    sub_tasks: List[str] = Field(default_factory=list, description="Sub-task IDs")
    
    required: bool = Field(default=True, description="Is task required or optional")
    
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    
    files_created: List[str] = Field(default_factory=list, description="Files created")
    files_modified: List[str] = Field(default_factory=list, description="Files modified")
    
    result: Optional[Dict[str, Any]] = Field(None, description="Task result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def is_leaf(self) -> bool:
        """Check if task is a leaf (no sub-tasks)"""
        return len(self.sub_tasks) == 0
    
    def is_complete(self) -> bool:
        """Check if task is complete"""
        return self.status == TaskStatus.COMPLETED


class TaskState(BaseModel):
    """State of all tasks in a spec"""
    spec_path: str = Field(..., description="Path to spec directory")
    tasks: Dict[str, Task] = Field(default_factory=dict, description="Tasks by ID")
    
    created_at: datetime = Field(default_factory=datetime.now, description="State creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, **kwargs) -> None:
        """Update task data"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        self.updated_at = datetime.now()
    
    def get_incomplete_required_tasks(self) -> List[Task]:
        """Get all incomplete required leaf tasks"""
        return [
            task for task in self.tasks.values()
            if task.required 
            and task.is_leaf() 
            and not task.is_complete()
        ]
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get tasks by status"""
        return [task for task in self.tasks.values() if task.status == status]
    
    def all_required_tasks_complete(self) -> bool:
        """Check if all required tasks are complete"""
        return len(self.get_incomplete_required_tasks()) == 0
