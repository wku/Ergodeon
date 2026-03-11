"""
Core Orchestrator
Main coordinator for all agents
"""

import asyncio
from typing import Dict, Optional, Any
from datetime import datetime
import re

from .base_agent import BaseAgent
from .memory import MemorySystem
from .state import StateManager
from .events import EventBus
from ..tools.registry import ToolRegistry
from ..models.agent import (
    UserRequest,
    AgentContext,
    AgentResult,
    IntentAnalysis,
    WorkflowState
)


class CoreOrchestrator:
    """Main orchestrator that coordinates all agents"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agents: Dict[str, BaseAgent] = {}
        self.memory = MemorySystem(config.get('memory', {}))
        self.state = StateManager()
        self.event_bus = EventBus()
        self.tools = ToolRegistry()
        
        self._setup_event_listeners()
    
    async def initialize(self) -> None:
        """Initialize orchestrator and all subsystems"""
        await self.memory.initialize()
        await self.tools.initialize()
        self.event_bus.emit('orchestrator:initialized', {})
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the orchestrator"""
        name = agent.config.name
        self.agents[name] = agent
        
        # Forward agent events
        agent.on('agent:delegate', self._handle_delegation)
        agent.on('agent:user-input-required', self._handle_user_input_request)
        
        self.event_bus.emit('agent:registered', {'name': name})
    
    async def process_request(self, request: UserRequest) -> AgentResult:
        """
        Main entry point - process user request
        
        Args:
            request: User request object
            
        Returns:
            AgentResult with execution results
        """
        try:
            self.event_bus.emit('request:start', {'request': request})
            
            # Analyze request intent
            intent = await self._analyze_intent(request)
            
            # Determine workflow type
            workflow_type = await self._determine_workflow(intent)
            
            # Get or create workflow state
            workflow_state = self.state.get_or_create_workflow(
                workflow_type,
                intent.get('feature_name')
            )
            
            # Select appropriate agent
            agent_name = self._select_agent(intent, workflow_state)
            
            # Build context
            context = await self._build_context(request, intent, workflow_state)
            
            # Execute agent
            result = await self._execute_agent(agent_name, context)
            
            # Update state
            self.state.update_workflow(workflow_state.id, result)
            
            self.event_bus.emit('request:complete', {
                'request': request,
                'result': result
            })
            
            return result
            
        except Exception as error:
            self.event_bus.emit('request:error', {
                'request': request,
                'error': str(error)
            })
            raise
    
    async def _analyze_intent(self, request: UserRequest) -> IntentAnalysis:
        """Analyze user intent using memory and patterns"""
        
        # Search memory for similar requests
        similar_requests = await self.memory.search(request.text, limit=5)
        
        # Detect request type
        request_type = self._detect_request_type(request.text)
        
        # Extract keywords
        keywords = self._extract_keywords(request.text)
        
        # Detect spec type
        spec_type = self._detect_spec_type(request.text)
        
        # Detect workflow type
        workflow_type = self._detect_workflow_type(request.text)
        
        # Extract feature name
        feature_name = self._extract_feature_name(request.text)
        
        return IntentAnalysis(
            type=request_type,
            keywords=keywords,
            context=similar_requests,
            spec_type=spec_type,
            workflow_type=workflow_type,
            feature_name=feature_name,
            confidence=0.8
        )
    
    async def _determine_workflow(self, intent: IntentAnalysis) -> str:
        """Determine which workflow to use"""
        
        if intent.type == 'spec':
            if intent.spec_type == 'bugfix':
                return 'bugfix-workflow'
            elif intent.workflow_type == 'design-first':
                return 'feature-design-first-workflow'
            else:
                return 'feature-requirements-first-workflow'
        elif intent.type == 'task-execution':
            return 'spec-task-execution'
        elif intent.type == 'analysis':
            return 'context-gatherer'
        else:
            return 'general-task-execution'
    
    def _select_agent(self, intent: IntentAnalysis, state: WorkflowState) -> str:
        """Select agent based on intent and state"""
        
        # If in workflow, continue with same agent
        if state.current_agent:
            return state.current_agent
        
        # Otherwise select based on intent
        return intent.suggested_agent or 'general-task-execution'
    
    async def _build_context(
        self,
        request: UserRequest,
        intent: IntentAnalysis,
        state: WorkflowState
    ) -> AgentContext:
        """Build execution context for agent"""
        
        # Get relevant memory
        relevant_memory = await self.memory.search(request.text, limit=10)
        
        # Build context
        context = AgentContext(
            request=request.text,
            intent=intent,
            workflow_state=state,
            memory=relevant_memory,
            preset=state.current_phase,
            metadata={
                'timestamp': datetime.now().timestamp(),
                'user_id': request.user_id,
                'session_id': request.session_id,
                'feature_name': intent.feature_name
            }
        )
        
        return context
    
    async def _execute_agent(
        self,
        agent_name: str,
        context: AgentContext
    ) -> AgentResult:
        """Execute agent with context"""
        
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} not found")
        
        return await agent.run(context)
    
    async def _handle_delegation(self, data: Dict[str, Any]) -> None:
        """Handle delegation from one agent to another"""
        
        from_agent = data['from']
        to_agent = data['to']
        context = data['context']
        
        self.event_bus.emit('delegation:start', {'from': from_agent, 'to': to_agent})
        
        result = await self._execute_agent(to_agent, context)
        
        self.event_bus.emit('delegation:complete', {
            'from': from_agent,
            'to': to_agent,
            'result': result
        })
    
    def _handle_user_input_request(self, data: Dict[str, Any]) -> None:
        """Handle user input request from agent"""
        self.event_bus.emit('user-input-required', data)
    
    def _setup_event_listeners(self) -> None:
        """Setup event listeners"""
        
        self.event_bus.on('workflow:phase-complete', self._handle_phase_complete)
        self.event_bus.on('workflow:approval-required', 
                         lambda data: self.event_bus.emit('approval-required', data))
    
    async def _handle_phase_complete(self, data: Dict[str, Any]) -> None:
        """Handle workflow phase completion"""
        
        workflow_id = data['workflow_id']
        phase = data['phase']
        result = data['result']
        
        workflow = self.state.get_workflow(workflow_id)
        if not workflow:
            return
        
        # Determine next phase
        next_phase = self._determine_next_phase(workflow, phase)
        
        if next_phase:
            workflow.current_phase = next_phase
            self.state.update_workflow(workflow_id, workflow)
    
    def _determine_next_phase(self, workflow: WorkflowState, current_phase: str) -> Optional[str]:
        """Determine next phase in workflow"""
        
        phase_map = {
            'feature-requirements-first-workflow': {
                'requirements': 'design',
                'design': 'tasks',
                'tasks': None
            },
            'feature-design-first-workflow': {
                'design': 'requirements',
                'requirements': 'tasks',
                'tasks': None
            },
            'bugfix-workflow': {
                'requirements': 'design',
                'design': 'tasks',
                'tasks': None
            }
        }
        
        return phase_map.get(workflow.type, {}).get(current_phase)
    
    def _detect_request_type(self, text: str) -> str:
        """Detect request type from text"""
        
        text_lower = text.lower()
        
        if re.search(r'(create|add|implement|build).*spec', text, re.I):
            return 'spec'
        elif re.search(r'(execute|run).*task', text, re.I):
            return 'task-execution'
        elif re.search(r'(how|where|find|analyze)', text, re.I):
            return 'analysis'
        else:
            return 'general'
    
    def _detect_spec_type(self, text: str) -> Optional[str]:
        """Detect spec type (feature or bugfix)"""
        
        bugfix_pattern = r'fix|bug|crash|error|broken|issue'
        feature_pattern = r'add|create|implement|build|new'
        
        if re.search(bugfix_pattern, text, re.I):
            return 'bugfix'
        elif re.search(feature_pattern, text, re.I):
            return 'feature'
        
        return None
    
    def _detect_workflow_type(self, text: str) -> Optional[str]:
        """Detect workflow type"""
        
        if re.search(r'design.*first|technical.*design', text, re.I):
            return 'design-first'
        
        return 'requirements-first'  # Default
    
    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text"""
        
        words = text.lower().split()
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        
        return [w for w in words if len(w) > 3 and w not in stop_words]
    
    def _extract_feature_name(self, text: str) -> str:
        """Extract and format feature name"""
        
        # Remove special characters and convert to kebab-case
        words = re.sub(r'[^a-z0-9\s]', '', text.lower()).split()
        words = [w for w in words if len(w) > 2][:4]
        
        return '-'.join(words) if words else 'feature'
    
    async def shutdown(self) -> None:
        """Shutdown orchestrator"""
        await self.memory.shutdown()
        self.event_bus.emit('orchestrator:shutdown', {})
