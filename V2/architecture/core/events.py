"""
Event Bus
Pub/Sub system for agent communication
"""

import asyncio
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
from collections import defaultdict


class EventBus:
    """Event bus for agent communication using pub/sub pattern"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000
        self._lock = asyncio.Lock()
    
    def on(self, event: str, handler: Callable) -> None:
        """
        Subscribe to event
        
        Args:
            event: Event name
            handler: Handler function (can be sync or async)
        """
        self._handlers[event].append(handler)
    
    def off(self, event: str, handler: Callable) -> None:
        """
        Unsubscribe from event
        
        Args:
            event: Event name
            handler: Handler function to remove
        """
        if event in self._handlers:
            self._handlers[event].remove(handler)
    
    def emit(self, event: str, data: Dict[str, Any]) -> None:
        """
        Emit event synchronously
        
        Args:
            event: Event name
            data: Event data
        """
        event_obj = {
            'type': event,
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
        
        # Record in history
        self._record_event(event_obj)
        
        # Call handlers
        if event in self._handlers:
            for handler in self._handlers[event]:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(data))
                else:
                    handler(data)
        
        # Call wildcard handlers
        wildcard = event.split(':')[0] + ':*'
        if wildcard in self._handlers:
            for handler in self._handlers[wildcard]:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(data))
                else:
                    handler(data)
    
    async def emit_async(self, event: str, data: Dict[str, Any]) -> None:
        """
        Emit event asynchronously and wait for all handlers
        
        Args:
            event: Event name
            data: Event data
        """
        event_obj = {
            'type': event,
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
        
        # Record in history
        self._record_event(event_obj)
        
        # Collect all handlers
        handlers = []
        if event in self._handlers:
            handlers.extend(self._handlers[event])
        
        wildcard = event.split(':')[0] + ':*'
        if wildcard in self._handlers:
            handlers.extend(self._handlers[wildcard])
        
        # Execute all handlers
        tasks = []
        for handler in handlers:
            if asyncio.iscoroutinefunction(handler):
                tasks.append(handler(data))
            else:
                # Wrap sync function in async
                tasks.append(asyncio.to_thread(handler, data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def publish_agent_event(self, event_type: str, agent: str, data: Any) -> None:
        """
        Publish agent-specific event
        
        Args:
            event_type: Type of event
            agent: Agent name
            data: Event data
        """
        event_data = {
            'agent': agent,
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
        
        self.emit(f'agent:{event_type}', event_data)
    
    def publish_workflow_event(self, event_data: Dict[str, Any]) -> None:
        """
        Publish workflow event
        
        Args:
            event_data: Workflow event data
        """
        event_type = event_data.get('type', 'unknown')
        self.emit(f'workflow:{event_type}', event_data)
    
    def publish_delegation(self, from_agent: str, to_agent: str, context: Any) -> None:
        """
        Publish delegation event
        
        Args:
            from_agent: Source agent
            to_agent: Target agent
            context: Delegation context
        """
        event_data = {
            'from': from_agent,
            'to': to_agent,
            'context': context,
            'timestamp': datetime.now().timestamp()
        }
        
        self.emit('delegation', event_data)
        self.emit(f'delegation:{from_agent}:{to_agent}', event_data)
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get event history
        
        Args:
            limit: Maximum events to return
            
        Returns:
            List of events
        """
        if limit:
            return self._event_history[-limit:]
        return self._event_history.copy()
    
    def get_events_by_type(self, event_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get events by type
        
        Args:
            event_type: Event type to filter
            limit: Maximum events
            
        Returns:
            Filtered events
        """
        events = [e for e in self._event_history if e['type'] == event_type]
        
        if limit:
            return events[-limit:]
        return events
    
    def get_events_by_agent(self, agent: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get events by agent
        
        Args:
            agent: Agent name
            limit: Maximum events
            
        Returns:
            Filtered events
        """
        events = [
            e for e in self._event_history
            if e.get('data', {}).get('agent') == agent
        ]
        
        if limit:
            return events[-limit:]
        return events
    
    def clear_history(self) -> None:
        """Clear event history"""
        self._event_history.clear()
        self.emit('history:cleared', {})
    
    def _record_event(self, event: Dict[str, Any]) -> None:
        """Record event in history"""
        self._event_history.append(event)
        
        # Maintain max size
        if len(self._event_history) > self._max_history_size:
            self._event_history.pop(0)
    
    def remove_all_listeners(self, event: Optional[str] = None) -> None:
        """
        Remove all listeners
        
        Args:
            event: Specific event (optional, removes all if None)
        """
        if event:
            self._handlers[event].clear()
        else:
            self._handlers.clear()
