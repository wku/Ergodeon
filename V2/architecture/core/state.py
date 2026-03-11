"""
State Manager
Centralized state management for workflows and tasks
"""

from typing import Dict, Optional, List, Any
from datetime import datetime
from enum import Enum

from ..models.workflow import WorkflowState, TaskState, WorkflowType, Phase, TaskStatus
from .events import EventBus


class StateManager:
    """Manages state for workflows, tasks, and sessions"""
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.workflows: Dict[str, WorkflowState] = {}
        self.tasks: Dict[str, TaskState] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.event_bus = event_bus or EventBus()
    
    def get_or_create_workflow(
        self,
        workflow_type: str,
        feature_name: Optional[str] = None
    ) -> WorkflowState:
        """
        Get or create workflow state
        
        Args:
            workflow_type: Type of workflow
            feature_name: Feature name (optional)
            
        Returns:
            WorkflowState object
        """
        workflow_id = feature_name or self._generate_workflow_id()
        
        if workflow_id in self.workflows:
            return self.workflows[workflow_id]
        
        spec_type = 'bugfix' if 'bugfix' in workflow_type else 'feature'
        
        workflow = WorkflowState(
            id=workflow_id,
            type=workflow_type,
            spec_type=spec_type,
            feature_name=feature_name or workflow_id,
            current_phase='requirements',
            current_agent=workflow_type,
            files_created=[],
            approvals=[],
            status='active',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.workflows[workflow_id] = workflow
        self.event_bus.emit('workflow:created', {'workflow': workflow.dict()})
        
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow by ID"""
        return self.workflows.get(workflow_id)
    
    def update_workflow(
        self,
        workflow_id: str,
        updates: Dict[str, Any]
    ) -> None:
        """
        Update workflow state
        
        Args:
            workflow_id: Workflow ID
            updates: Dictionary of updates
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return
        
        # Update fields
        for key, value in updates.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)
        
        workflow.updated_at = datetime.now()
        
        self.event_bus.emit('workflow:updated', {'workflow': workflow.dict()})
    
    def complete_workflow(self, workflow_id: str) -> None:
        """Mark workflow as completed"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return
        
        workflow.status = 'completed'
        workflow.updated_at = datetime.now()
        
        self.event_bus.emit('workflow:completed', {'workflow': workflow.dict()})
    
    def get_active_workflows(self) -> List[WorkflowState]:
        """Get all active workflows"""
        return [w for w in self.workflows.values() if w.status == 'active']
    
    def create_task(self, spec_path: str, task_id: str) -> TaskState:
        """
        Create task state
        
        Args:
            spec_path: Path to spec
            task_id: Task identifier
            
        Returns:
            TaskState object
        """
        task_key = f"{spec_path}:{task_id}"
        
        task = TaskState(
            id=task_key,
            spec_path=spec_path,
            task_id=task_id,
            status=TaskStatus.NOT_STARTED,
            attempts=0,
            errors=[]
        )
        
        self.tasks[task_key] = task
        self.event_bus.emit('task:created', {'task': task.dict()})
        
        return task
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """
        Update task status
        
        Args:
            task_id: Task ID
            status: New status
        """
        task = self.tasks.get(task_id)
        if not task:
            return
        
        old_status = task.status
        task.status = status
        
        if status == TaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = datetime.now()
        
        if status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.now()
        
        self.event_bus.emit('task:status-changed', {
            'task': task.dict(),
            'old_status': old_status.value,
            'new_status': status.value
        })
    
    def get_task(self, task_id: str) -> Optional[TaskState]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def get_tasks_for_spec(self, spec_path: str) -> List[TaskState]:
        """Get all tasks for a spec"""
        return [t for t in self.tasks.values() if t.spec_path == spec_path]
    
    def record_task_error(self, task_id: str, error: str) -> None:
        """Record task error"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        task.attempts += 1
        task.errors.append(error)
        
        self.event_bus.emit('task:error', {
            'task': task.dict(),
            'error': error
        })
    
    def create_session(self, user_id: str) -> str:
        """Create new session"""
        session_id = self._generate_session_id()
        
        self.sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.now(),
            'workflows': [],
            'tasks': []
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def add_workflow_to_session(self, session_id: str, workflow_id: str) -> None:
        """Add workflow to session"""
        session = self.sessions.get(session_id)
        if session:
            session['workflows'].append(workflow_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get state statistics"""
        return {
            'workflows': {
                'total': len(self.workflows),
                'active': len(self.get_active_workflows()),
                'completed': len([w for w in self.workflows.values() if w.status == 'completed'])
            },
            'tasks': {
                'total': len(self.tasks),
                'completed': len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
                'in_progress': len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS])
            },
            'sessions': len(self.sessions)
        }
    
    def clear_completed(self, older_than_hours: int = 24) -> None:
        """Clear completed workflows older than specified hours"""
        cutoff = datetime.now().timestamp() - (older_than_hours * 60 * 60)
        
        to_remove = []
        for workflow_id, workflow in self.workflows.items():
            if (workflow.status == 'completed' and 
                workflow.updated_at.timestamp() < cutoff):
                to_remove.append(workflow_id)
        
        for workflow_id in to_remove:
            del self.workflows[workflow_id]
            self.event_bus.emit('workflow:cleared', {'id': workflow_id})
    
    def _generate_workflow_id(self) -> str:
        """Generate unique workflow ID"""
        import random
        import string
        
        timestamp = int(datetime.now().timestamp())
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
        
        return f"workflow-{timestamp}-{random_str}"
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import random
        import string
        
        timestamp = int(datetime.now().timestamp())
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
        
        return f"session-{timestamp}-{random_str}"
