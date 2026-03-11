"""
Feature Requirements-First Workflow Agent
Creates specs starting with requirements
"""

from typing import Any, Dict
from ...core.base_agent import BaseAgent
from ...models.agent import AgentContext, AgentResult, AgentResultStatus


class RequirementsFirstAgent(BaseAgent):
    """Agent for requirements-first workflow"""
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute requirements-first workflow"""
        
        preset = context.preset or "requirements"
        feature_name = context.intent.feature_name
        spec_path = f".kiro/specs/{feature_name}/"
        
        if preset == "requirements":
            return await self._create_requirements(context, spec_path)
        elif preset == "design":
            return await self._create_design(context, spec_path)
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
    
    async def _create_requirements(
        self,
        context: AgentContext,
        spec_path: str
    ) -> AgentResult:
        """Create requirements.md"""
        
        self.update_progress(10, "Analyzing user request")
        
        # Gather context from memory
        relevant_context = await self.search_memory(context.request, limit=10)
        
        self.update_progress(30, "Generating requirements document")
        
        # Generate requirements content
        requirements_content = await self._generate_requirements_content(
            context.request,
            relevant_context
        )
        
        self.update_progress(60, "Creating requirements.md")
        
        # Write requirements file
        requirements_path = f"{spec_path}requirements.md"
        await self.use_tool("fsWrite", {
            "path": requirements_path,
            "text": requirements_content
        })
        
        self.update_progress(80, "Creating config file")
        
        # Create config file
        config_content = self._generate_config(
            spec_type="feature",
            workflow_type="requirements-first"
        )
        await self.use_tool("fsWrite", {
            "path": f"{spec_path}.config.kiro",
            "text": config_content
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
            files_created=[requirements_path, f"{spec_path}.config.kiro"],
            output="Requirements document created successfully",
            next_action={
                "phase": "design",
                "requires_approval": True,
                "approved": approval.lower() in ["yes", "y", "continue"]
            }
        )
    
    async def _create_design(
        self,
        context: AgentContext,
        spec_path: str
    ) -> AgentResult:
        """Create design.md"""
        
        self.update_progress(10, "Reading requirements")
        
        # Read requirements
        requirements = await self.use_tool("readFile", {
            "path": f"{spec_path}requirements.md"
        })
        
        self.update_progress(30, "Generating design document")
        
        # Generate design content
        design_content = await self._generate_design_content(
            requirements,
            context.request
        )
        
        self.update_progress(70, "Creating design.md")
        
        # Write design file
        design_path = f"{spec_path}design.md"
        await self.use_tool("fsWrite", {
            "path": design_path,
            "text": design_content
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
            files_created=[design_path],
            output="Design document created successfully",
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
        
        self.update_progress(10, "Reading requirements and design")
        
        # Read requirements and design
        files = await self.use_tool("readMultipleFiles", {
            "paths": [
                f"{spec_path}requirements.md",
                f"{spec_path}design.md"
            ]
        })
        
        self.update_progress(40, "Generating task list")
        
        # Generate tasks content
        tasks_content = await self._generate_tasks_content(
            files[f"{spec_path}requirements.md"],
            files[f"{spec_path}design.md"]
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
    
    async def _generate_requirements_content(
        self,
        request: str,
        context: list
    ) -> str:
        """Generate requirements document content"""
        # This would use LLM to generate content
        # For now, return template
        return f"""# Requirements Document

## Feature Overview
{request}

## User Stories
1. As a user, I want to...

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Correctness Properties
1. Property 1: ...

## Non-Functional Requirements
- Performance
- Security
- Accessibility
"""
    
    async def _generate_design_content(
        self,
        requirements: str,
        request: str
    ) -> str:
        """Generate design document content"""
        return f"""# Design Document

## High-Level Design
...

## Low-Level Design
...

## Data Models
...

## API Design
...
"""
    
    async def _generate_tasks_content(
        self,
        requirements: str,
        design: str
    ) -> str:
        """Generate tasks document content"""
        return f"""# Implementation Tasks

- [ ] 1. Task 1
  - [ ] 1.1 Sub-task 1
  - [ ] 1.2 Sub-task 2
- [ ] 2. Task 2
- [ ] 3. Task 3
"""
    
    def _generate_config(self, spec_type: str, workflow_type: str) -> str:
        """Generate config file content"""
        return f"""specType: {spec_type}
workflowType: {workflow_type}
"""
