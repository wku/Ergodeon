"""
Basic Usage Examples for Kiro Agent System
"""

import asyncio
import yaml
from pathlib import Path

from core.orchestrator import CoreOrchestrator
from core.memory import MemorySystem
from core.events import EventBus
from core.state import StateManager
from tools.registry import ToolRegistry
from models.agent import UserRequest, AgentConfig
from agents.workflow.requirements_first import RequirementsFirstAgent


async def example_1_simple_request():
    """Example 1: Simple user request processing"""
    
    # Load configuration
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize orchestrator
    orchestrator = CoreOrchestrator(config)
    await orchestrator.initialize()
    
    # Create user request
    request = UserRequest(
        text="Create a login form component",
        user_id="user123",
        session_id="session456"
    )
    
    # Process request
    result = await orchestrator.process_request(request)
    
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Files created: {result.files_created}")
    
    # Shutdown
    await orchestrator.shutdown()


async def example_2_feature_spec_workflow():
    """Example 2: Create feature spec with requirements-first workflow"""
    
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    orchestrator = CoreOrchestrator(config)
    await orchestrator.initialize()
    
    # User wants to create a feature spec
    request = UserRequest(
        text="Add user authentication with JWT tokens",
        user_id="user123",
        session_id="session456"
    )
    
    # Process - orchestrator will ask user for choices
    result = await orchestrator.process_request(request)
    
    # Orchestrator will:
    # 1. Ask: Feature or Bugfix? (user selects Feature)
    # 2. Ask: Requirements or Design first? (user selects Requirements)
    # 3. Delegate to feature-requirements-first-workflow
    # 4. Create requirements.md
    # 5. Request user approval
    # 6. Create design.md
    # 7. Request user approval
    # 8. Create tasks.md
    # 9. Ready for execution
    
    print(f"Spec created at: {result.result.get('spec_path')}")
    
    await orchestrator.shutdown()


async def example_3_bugfix_workflow():
    """Example 3: Bugfix workflow"""
    
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    orchestrator = CoreOrchestrator(config)
    await orchestrator.initialize()
    
    # User reports a bug
    request = UserRequest(
        text="App crashes when quantity is set to zero",
        user_id="user123",
        session_id="session456"
    )
    
    # Process - orchestrator will detect bugfix intent
    result = await orchestrator.process_request(request)
    
    # Orchestrator will:
    # 1. Ask: Feature or Bugfix? (user selects Bugfix)
    # 2. Delegate to bugfix-workflow (skip workflow choice)
    # 3. Create bugfix.md with root cause analysis
    # 4. Request user validation of root cause
    # 5. Create design.md with fix design
    # 6. Request user approval
    # 7. Create tasks.md
    # 8. Execute Task 1 (exploration test)
    # 9. If test fails (expected), proceed with fix
    # 10. If test passes (unexpected), ask user to re-investigate
    
    print(f"Bugfix spec created at: {result.result.get('spec_path')}")
    
    await orchestrator.shutdown()


async def example_4_direct_agent_usage():
    """Example 4: Using an agent directly"""
    
    # Initialize components
    memory = MemorySystem({'db_path': './data/chroma'})
    await memory.initialize()
    
    tools = ToolRegistry()
    await tools.initialize()
    
    event_bus = EventBus()
    
    # Create agent config
    config = AgentConfig(
        name="feature-requirements-first-workflow",
        display_name="Feature Requirements-First Workflow",
        description="Creates feature specs starting with requirements",
        allowed_tools=["readFile", "fsWrite", "grepSearch"]
    )
    
    # Grant tool permissions
    tools.grant_permission(config.name, config.allowed_tools)
    
    # Create agent
    agent = RequirementsFirstAgent(config, memory, tools, event_bus)
    
    # Create context
    from models.agent import AgentContext, IntentAnalysis, IntentType
    
    intent = IntentAnalysis(
        type=IntentType.SPEC,
        feature_name="user-authentication",
        keywords=["authentication", "user", "login"]
    )
    
    context = AgentContext(
        request="Add user authentication",
        intent=intent,
        preset="requirements"
    )
    
    # Execute agent
    result = await agent.run(context)
    
    print(f"Agent result: {result.status}")
    print(f"Files created: {result.files_created}")
    
    # Cleanup
    await memory.shutdown()


async def example_5_event_handling():
    """Example 5: Event handling and monitoring"""
    
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    orchestrator = CoreOrchestrator(config)
    
    # Register event handlers
    def on_agent_start(data):
        print(f"Agent started: {data['agent']}")
    
    def on_agent_complete(data):
        print(f"Agent completed: {data['agent']}")
        print(f"Result: {data['result'].status}")
    
    def on_agent_error(data):
        print(f"Agent error: {data['agent']}")
        print(f"Error: {data['error']}")
    
    orchestrator.event_bus.on('agent:start', on_agent_start)
    orchestrator.event_bus.on('agent:complete', on_agent_complete)
    orchestrator.event_bus.on('agent:error', on_agent_error)
    
    await orchestrator.initialize()
    
    # Process request
    request = UserRequest(
        text="Create a button component",
        user_id="user123",
        session_id="session456"
    )
    
    result = await orchestrator.process_request(request)
    
    await orchestrator.shutdown()


async def example_6_memory_search():
    """Example 6: Using memory system for semantic search"""
    
    memory = MemorySystem({'db_path': './data/chroma'})
    await memory.initialize()
    
    # Store some context
    await memory.store_context("test-agent", {
        "request": "Create login form",
        "result": "Created LoginForm.tsx"
    })
    
    await memory.store_context("test-agent", {
        "request": "Add authentication",
        "result": "Added JWT auth"
    })
    
    # Search memory
    results = await memory.search("authentication", limit=5)
    
    print("Search results:")
    for result in results:
        print(f"- {result}")
    
    await memory.shutdown()


async def example_7_task_execution():
    """Example 7: Execute tasks from a spec"""
    
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    orchestrator = CoreOrchestrator(config)
    await orchestrator.initialize()
    
    # Assume spec already exists at .kiro/specs/user-authentication/
    
    # Execute single task
    request = UserRequest(
        text="Execute task 2 from user-authentication spec",
        user_id="user123",
        session_id="session456"
    )
    
    result = await orchestrator.process_request(request)
    
    print(f"Task execution result: {result.status}")
    
    # Execute all tasks
    request = UserRequest(
        text="Run all tasks from user-authentication spec",
        user_id="user123",
        session_id="session456"
    )
    
    result = await orchestrator.process_request(request)
    
    print(f"All tasks completed: {result.status}")
    
    await orchestrator.shutdown()


async def example_8_custom_agent():
    """Example 8: Create a custom agent"""
    
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    orchestrator = CoreOrchestrator(config)
    await orchestrator.initialize()
    
    # Request to create custom agent
    request = UserRequest(
        text="Create an agent that analyzes code complexity",
        user_id="user123",
        session_id="session456"
    )
    
    result = await orchestrator.process_request(request)
    
    # Orchestrator will delegate to custom-agent-creator
    # which will create all necessary files
    
    print(f"Custom agent created: {result.output}")
    print(f"Files: {result.files_created}")
    
    await orchestrator.shutdown()


# Run examples
if __name__ == "__main__":
    print("=== Example 1: Simple Request ===")
    asyncio.run(example_1_simple_request())
    
    print("\n=== Example 2: Feature Spec Workflow ===")
    asyncio.run(example_2_feature_spec_workflow())
    
    print("\n=== Example 3: Bugfix Workflow ===")
    asyncio.run(example_3_bugfix_workflow())
    
    print("\n=== Example 4: Direct Agent Usage ===")
    asyncio.run(example_4_direct_agent_usage())
    
    print("\n=== Example 5: Event Handling ===")
    asyncio.run(example_5_event_handling())
    
    print("\n=== Example 6: Memory Search ===")
    asyncio.run(example_6_memory_search())
    
    print("\n=== Example 7: Task Execution ===")
    asyncio.run(example_7_task_execution())
    
    print("\n=== Example 8: Custom Agent ===")
    asyncio.run(example_8_custom_agent())
