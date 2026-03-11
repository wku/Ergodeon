"""
Base Agent Class
All agents inherit from this base class
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum

from .memory import MemorySystem
from .events import EventBus
from ..tools.registry import ToolRegistry
from ..models.agent import AgentConfig, AgentContext, AgentResult


class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DELEGATED = "delegated"


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(
        self,
        config: AgentConfig,
        memory: MemorySystem,
        tools: ToolRegistry,
        event_bus: EventBus
    ):
        self.config = config
        self.memory = memory
        self.tools = tools
        self.event_bus = event_bus
        self.status = AgentStatus.IDLE
        self.context: Optional[AgentContext] = None
        self._event_handlers: Dict[str, List[callable]] = {}
    
    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Main execution method - must be implemented by subclasses
        
        Args:
            context: Execution context
            
        Returns:
            AgentResult with execution results
        """
        pass
    
    @abstractmethod
    async def validate(self, context: AgentContext) -> bool:
        """
        Validate input before execution
        
        Args:
            context: Context to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def process_result(self, result: Any) -> AgentResult:
        """
        Process result before returning
        
        Args:
            result: Raw result from execution
            
        Returns:
            Processed AgentResult
        """
        pass
    
    async def run(self, context: AgentContext) -> AgentResult:
        """
        Public method to run the agent
        
        Args:
            context: Execution context
            
        Returns:
            AgentResult
        """
        try:
            self.status = AgentStatus.RUNNING
            self.context = context
            
            self.emit('agent:start', {
                'agent': self.config.name,
                'context': context
            })
            
            # Validate input
            is_valid = await self.validate(context)
            if not is_valid:
                raise ValueError('Invalid context provided')
            
            # Store context in memory
            await self.memory.store_context(self.config.name, context.dict())
            
            # Execute agent logic
            result = await self.execute(context)
            
            # Process and validate result
            processed_result = self.process_result(result)
            
            # Store result in memory
            await self.memory.store_result(self.config.name, processed_result.dict())
            
            self.status = AgentStatus.COMPLETED
            self.emit('agent:complete', {
                'agent': self.config.name,
                'result': processed_result
            })
            
            return processed_result
            
        except Exception as error:
            self.status = AgentStatus.FAILED
            self.emit('agent:error', {
                'agent': self.config.name,
                'error': str(error)
            })
            raise
        finally:
            self.context = None
    
    def get_status(self) -> AgentStatus:
        """Get current agent status"""
        return self.status
    
    def get_config(self) -> AgentConfig:
        """Get agent configuration"""
        return self.config
    
    async def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search memory for relevant context
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of search results
        """
        return await self.memory.search(query, limit)
    
    async def use_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Use a tool
        
        Args:
            tool_name: Name of tool to use
            params: Tool parameters
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.config.allowed_tools:
            raise PermissionError(
                f"Tool {tool_name} not allowed for agent {self.config.name}"
            )
        
        return await self.tools.execute(tool_name, params, self.config.name)
    
    async def delegate_to_agent(
        self,
        agent_name: str,
        context: AgentContext
    ) -> AgentResult:
        """
        Delegate to another agent
        
        Args:
            agent_name: Target agent name
            context: Context to pass
            
        Returns:
            AgentResult from delegated agent
        """
        self.emit('agent:delegate', {
            'from': self.config.name,
            'to': agent_name,
            'context': context
        })
        
        # This will be handled by orchestrator
        return AgentResult(
            status='delegated',
            agent_name=agent_name,
            result={'context': context.dict()}
        )
    
    async def request_user_input(
        self,
        question: str,
        options: Optional[List[str]] = None
    ) -> str:
        """
        Request user input
        
        Args:
            question: Question to ask
            options: Optional list of choices
            
        Returns:
            User's response
        """
        future = asyncio.Future()
        
        self.emit('agent:user-input-required', {
            'agent': self.config.name,
            'question': question,
            'options': options,
            'callback': lambda response: future.set_result(response)
        })
        
        return await future
    
    def update_progress(self, progress: int, message: Optional[str] = None) -> None:
        """
        Update progress
        
        Args:
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        self.emit('agent:progress', {
            'agent': self.config.name,
            'progress': progress,
            'message': message
        })
    
    def emit(self, event: str, data: Dict[str, Any]) -> None:
        """
        Emit event
        
        Args:
            event: Event name
            data: Event data
        """
        self.event_bus.emit(event, data)
        
        # Call local handlers
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                handler(data)
    
    def on(self, event: str, handler: callable) -> None:
        """
        Register event handler
        
        Args:
            event: Event name
            handler: Handler function
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    async def shutdown(self) -> None:
        """Shutdown agent"""
        self.status = AgentStatus.IDLE
        self.context = None
        self._event_handlers.clear()
