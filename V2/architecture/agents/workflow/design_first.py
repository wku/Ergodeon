"""
Feature Design-First Workflow Agent
Creates specs starting with technical design
"""

from typing import Any, Dict
from ...core.base_agent import BaseAgent
from ...models.agent import AgentContext, AgentResult, AgentResultStatus


class DesignFirstAgent(BaseAgent):
    """Agent for design-first workflow"""
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute design-first workflow"""
        
        preset = context.preset or "design"
        feature_name = context.intent.feature_name
        spec_path = f".kiro/specs/{feature_name}/"
        
        if preset == "design":
            return await self._create_design(context, spec_path)
        elif preset == "requirements":
            return await self._create_requirements(context, spec_path)
        elif preset == "tasks":
            return await self._create_tasks(context, spec_path)
        else:
            raise ValueError(f"Unknown preset: {preset}")
    
    async def validate(self, context: AgentContext) -> bool:
        """Validate context"""
        return (
            context.intent is not None and
            context.intent.feature_name is not None
        )
    
    def process_result(self, result: Any) -> AgentResult:
        """Process result"""
        if isinstance(result, AgentResult):
            return result
        
        return AgentResult(
            status=AgentResultStatus.SUCCESS,
            agent_name=self.config.name,
            result=result
        )
    
    async def _create_design(
        self,
        context: AgentContext,
        spec_path: str
    ) -> AgentResult:
        """Create design.md first"""
        
        self.update_progress(10, "Analyzing technical approach")
        
        # Gather context from memory
        relevant_context = await self.search_memory(context.request, limit=10)
        
        self.update_progress(30, "Generating design document")
        
        # Generate design content
        design_content = await self._generate_design_content(
            context.request,
            relevant_context
        )
        
        self.update_progress(60, "Creating design.md")
        
        # Write design file
        design_path = f"{spec_path}design.md"
        await self.use_tool("fsWrite", {
            "path": design_path,
            "text": design_content
        })
        
        self.update_progress(80, "Creating config file")
        
        # Create config file
        config_content = self._generate_config(
            spec_type="feature",
            workflow_type="design-first"
        )
        await self.use_tool("fsWrite", {
            "path": f"{spec_path}.config.kiro",
            "text": config_content
        })
        
        self.update_progress(100, "Design complete")
        
        # Request user approval
        approval = await self.request_user_input(
            "Design document created. Please review design.md. Continue?",
            options=["Yes", "No", "Modify"]
        )
        
        return AgentResult(
            status=AgentResultStatus.SUCCESS,
            agent_name=self.config.name,
            files_created=[design_path, f"{spec_path}.config.kiro"],
            output="Design document created successfully",
            next_action={
                "phase": "requirements",
                "requires_approval": True,
                "approved": approval.lower() in ["yes", "y", "continue"]
            }
        )
    
    async def _create_requirements(
        self,
        context: AgentContext,
        spec_path: str
    ) -> AgentResult:
        """Create requirements.md derived from design"""
        
        self.update_progress(10, "Reading design")
        
        # Read design
        design = await self.use_tool("readFile", {
            "path": f"{spec_path}design.md"
        })
        
        self.update_progress(30, "Deriving requirements from design")
        
        # Generate requirements content
        requirements_content = await self._generate_requirements_from_design(
            design,
            context.request
        )
        
        self.update_progress(70, "Creating requirements.md")
        
        # Write requirements file
        requirements_path = f"{spec_path}requirements.md"
        await self.use_tool("fsWrite", {
            "path": requirements_path,
            "text": requirements_content
        })
        
        self.update_progress(100, "Requirements complete")
        
        # Request user approval
        approval = await self.request_user_input(
            "Requirements document created. Please review requirements.md. Continue?",
            options=["Yes", "No", "Modify"]
        )
        
        return AgentResult(
            status=AgentResultStatus.SUCCESS,
            agent_name=self.config.name,
            files_created=[requirements_path],
            output="Requirements document created successfully",
            next_action={
                "phase": "tasks",
                "requires_approval": True,
                "approved": approval.lower() in ["yes", "y", "continue"]
            }
        )
    
    async def _create_tasks(
        self,
        context: AgentContext,
        spec_path: str
    ) -> AgentResult:
        """Create tasks.md"""
        
        self.update_progress(10, "Reading design and requirements")
        
        # Read design and requirements
        files = await self.use_tool("readMultipleFiles", {
            "paths": [
                f"{spec_path}design.md",
                f"{spec_path}requirements.md"
            ]
        })
        
        self.update_progress(40, "Generating task list")
        
        # Generate tasks content
        tasks_content = await self._generate_tasks_content(
            files[f"{spec_path}design.md"],
            files[f"{spec_path}requirements.md"]
        )
        
        self.update_progress(80, "Creating tasks.md")
        
        # Write tasks file
        tasks_path = f"{spec_path}tasks.md"
        await self.use_tool("fsWrite", {
            "path": tasks_path,
            "text": tasks_content
        })
        
        self.update_progress(100, "Tasks complete")
        
        return AgentResult(
            status=AgentResultStatus.SUCCESS,
            agent_name=self.config.name,
            files_created=[tasks_path],
            output="Task list created successfully. Ready for execution.",
            next_action={
                "phase": None,
                "ready_for_execution": True
            }
        )
    
    async def _generate_design_content(
        self,
        request: str,
        context: list
    ) -> str:
        """Generate design document content"""
        # This would use LLM to generate content
        return f"""# Design Document

## High-Level Design

### Architecture Overview
{request}

### Technology Stack
- Frontend: React
- Backend: Node.js
- Database: PostgreSQL

### Design Patterns
- MVC
- Repository Pattern

## Component Design

### Component 1
...

### Component 2
...

## Data Models

### Entity 1
```typescript
interface Entity1 {{
  id: string;
  name: string;
}}
```

## API Design

### Endpoints
- GET /api/resource
- POST /api/resource

## Low-Level Design

### Algorithms
...

### Implementation Details
...
"""
    
    async def _generate_requirements_from_design(
        self,
        design: str,
        request: str
    ) -> str:
        """Generate requirements derived from design"""
        return f"""# Requirements Document

## Feature Overview
Derived from technical design: {request}

## User Stories
1. As a user, I want to use the system designed in design.md
2. As a developer, I want to implement the architecture

## Acceptance Criteria
- [ ] All components from design are implemented
- [ ] API endpoints work as designed
- [ ] Data models match design

## Correctness Properties
1. Property 1: System maintains data consistency
2. Property 2: API responses match design spec

## Non-Functional Requirements
- Performance: As specified in design
- Security: As specified in design
- Accessibility: WCAG 2.1 AA compliance
"""
    
    async def _generate_tasks_content(
        self,
        design: str,
        requirements: str
    ) -> str:
        """Generate tasks document content"""
        return f"""# Implementation Tasks

- [ ] 1. Setup project structure
  - [ ] 1.1 Initialize repository
  - [ ] 1.2 Setup build system
- [ ] 2. Implement core components
  - [ ] 2.1 Component 1
  - [ ] 2.2 Component 2
- [ ] 3. Implement API
  - [ ] 3.1 Setup routes
  - [ ] 3.2 Implement handlers
- [ ] 4. Testing
  - [ ] 4.1 Unit tests
  - [ ] 4.2 Integration tests
"""
    
    def _generate_config(self, spec_type: str, workflow_type: str) -> str:
        """Generate config file content"""
        return f"""specType: {spec_type}
workflowType: {workflow_type}
"""
