"""
Custom Agent Creator
Creates new custom agents
"""

from typing import Any, Dict
from ..core.base_agent import BaseAgent
from ..models.agent import AgentContext, AgentResult, AgentResultStatus


class CustomAgentCreatorAgent(BaseAgent):
    """Agent for creating custom agents"""
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute custom agent creation"""
        
        self.update_progress(10, "Analyzing agent requirements")
        
        # Parse agent requirements
        agent_spec = await self._parse_agent_requirements(context.request)
        
        self.update_progress(30, "Generating agent structure")
        
        # Generate agent files
        agent_files = await self._generate_agent_files(agent_spec)
        
        self.update_progress(60, "Creating agent files")
        
        # Write agent files
        files_created = await self._write_agent_files(agent_spec['name'], agent_files)
        
        self.update_progress(80, "Validating agent")
        
        # Validate agent structure
        validation = await self._validate_agent(agent_spec['name'])
        
        self.update_progress(100, "Agent created")
        
        return AgentResult(
            status=AgentResultStatus.SUCCESS if validation else AgentResultStatus.PARTIAL,
            agent_name=self.config.name,
            files_created=files_created,
            output=f"Custom agent '{agent_spec['name']}' created successfully",
            result={
                'agent_name': agent_spec['name'],
                'agent_path': f".kiro/agents/{agent_spec['name']}/",
                'validation': validation
            }
        )
    
    async def validate(self, context: AgentContext) -> bool:
        """Validate context"""
        return context.request is not None and len(context.request) > 0
    
    def process_result(self, result: Any) -> AgentResult:
        """Process result"""
        if isinstance(result, AgentResult):
            return result
        
        return AgentResult(
            status=AgentResultStatus.SUCCESS,
            agent_name=self.config.name,
            result=result
        )
    
    async def _parse_agent_requirements(self, request: str) -> Dict[str, Any]:
        """Parse agent requirements from request"""
        
        # Extract agent name
        name = self._extract_agent_name(request)
        
        # Extract purpose
        purpose = self._extract_purpose(request)
        
        # Determine required tools
        tools = self._determine_required_tools(request)
        
        # Determine capabilities
        capabilities = self._determine_capabilities(request)
        
        return {
            'name': name,
            'purpose': purpose,
            'tools': tools,
            'capabilities': capabilities,
            'request': request
        }
    
    def _extract_agent_name(self, request: str) -> str:
        """Extract agent name from request"""
        
        # Simple extraction - would be more sophisticated in real implementation
        words = request.lower().split()
        
        # Look for "agent that/for/to"
        for i, word in enumerate(words):
            if word in ['that', 'for', 'to'] and i > 0:
                # Use previous words as name
                name_words = words[max(0, i-3):i]
                name = '-'.join(name_words)
                if name:
                    return name
        
        # Default name
        return 'custom-agent'
    
    def _extract_purpose(self, request: str) -> str:
        """Extract agent purpose from request"""
        
        # Remove "create an agent" prefix
        purpose = request.lower()
        for prefix in ['create an agent', 'create agent', 'make an agent', 'make agent']:
            purpose = purpose.replace(prefix, '').strip()
        
        return purpose or request
    
    def _determine_required_tools(self, request: str) -> list:
        """Determine required tools based on request"""
        
        tools = ['readFile', 'readMultipleFiles', 'listDirectory']
        
        request_lower = request.lower()
        
        if any(word in request_lower for word in ['write', 'create', 'modify']):
            tools.extend(['fsWrite', 'fsAppend', 'editCode'])
        
        if any(word in request_lower for word in ['search', 'find', 'analyze']):
            tools.extend(['grepSearch', 'fileSearch'])
        
        if any(word in request_lower for word in ['run', 'execute', 'test']):
            tools.append('executeBash')
        
        return list(set(tools))  # Remove duplicates
    
    def _determine_capabilities(self, request: str) -> list:
        """Determine agent capabilities"""
        
        capabilities = []
        
        request_lower = request.lower()
        
        if 'analyze' in request_lower or 'analysis' in request_lower:
            capabilities.append('Code analysis')
        
        if 'test' in request_lower:
            capabilities.append('Testing')
        
        if 'document' in request_lower:
            capabilities.append('Documentation')
        
        if 'refactor' in request_lower:
            capabilities.append('Refactoring')
        
        return capabilities or ['General task execution']
    
    async def _generate_agent_files(self, agent_spec: Dict[str, Any]) -> Dict[str, str]:
        """Generate agent files"""
        
        files = {}
        
        # Generate config.json
        files['config.json'] = self._generate_config(agent_spec)
        
        # Generate prompt.md
        files['prompt.md'] = self._generate_prompt(agent_spec)
        
        # Generate rules.md
        files['rules.md'] = self._generate_rules(agent_spec)
        
        # Generate examples.md
        files['examples.md'] = self._generate_examples(agent_spec)
        
        # Generate README.md
        files['README.md'] = self._generate_readme(agent_spec)
        
        return files
    
    def _generate_config(self, agent_spec: Dict[str, Any]) -> str:
        """Generate config.json"""
        
        import json
        
        config = {
            "name": agent_spec['name'],
            "version": "1.0.0",
            "description": agent_spec['purpose'],
            "tools": agent_spec['tools'],
            "capabilities": agent_spec['capabilities']
        }
        
        return json.dumps(config, indent=2)
    
    def _generate_prompt(self, agent_spec: Dict[str, Any]) -> str:
        """Generate prompt.md"""
        
        return f"""# {agent_spec['name'].replace('-', ' ').title()} Agent

**Version**: 1.0.0
**Purpose**: {agent_spec['purpose']}

## Identity

You are a specialized agent for {agent_spec['purpose']}.

## Capabilities

{chr(10).join(f'- {cap}' for cap in agent_spec['capabilities'])}

## Tools Available

{chr(10).join(f'- {tool}' for tool in agent_spec['tools'])}

## Input Format

Describe expected input format here.

## Output Format

Describe expected output format here.

## Execution Process

1. Step 1
2. Step 2
3. Step 3

## Rules

1. Rule 1
2. Rule 2
3. Rule 3

## Examples

See examples.md for usage examples.
"""
    
    def _generate_rules(self, agent_spec: Dict[str, Any]) -> str:
        """Generate rules.md"""
        
        return f"""# {agent_spec['name'].replace('-', ' ').title()} Agent - Rules

## Critical Rules

1. Always validate input before processing
2. Use appropriate tools for each task
3. Provide clear error messages
4. Update progress regularly

## Tool Usage Rules

{chr(10).join(f'- {tool}: Use for appropriate operations' for tool in agent_spec['tools'])}

## Error Handling

1. Catch and handle all exceptions
2. Provide meaningful error messages
3. Suggest recovery actions

## Best Practices

1. Keep operations atomic
2. Validate results before returning
3. Log important operations
4. Clean up resources
"""
    
    def _generate_examples(self, agent_spec: Dict[str, Any]) -> str:
        """Generate examples.md"""
        
        return f"""# {agent_spec['name'].replace('-', ' ').title()} Agent - Examples

## Example 1: Basic Usage

**Input**:
```
{agent_spec['request']}
```

**Output**:
```
Task completed successfully
```

## Example 2: Advanced Usage

**Input**:
```
Advanced task description
```

**Output**:
```
Advanced task completed
```

## Example 3: Error Handling

**Input**:
```
Invalid input
```

**Output**:
```
Error: Invalid input provided
```
"""
    
    def _generate_readme(self, agent_spec: Dict[str, Any]) -> str:
        """Generate README.md"""
        
        return f"""# {agent_spec['name'].replace('-', ' ').title()} Agent

## Overview

{agent_spec['purpose']}

## Capabilities

{chr(10).join(f'- {cap}' for cap in agent_spec['capabilities'])}

## Usage

```python
from agents.{agent_spec['name'].replace('-', '_')} import {agent_spec['name'].replace('-', ' ').title().replace(' ', '')}Agent

agent = {agent_spec['name'].replace('-', ' ').title().replace(' ', '')}Agent(config, memory, tools, event_bus)
result = await agent.run(context)
```

## Configuration

See `config.json` for configuration options.

## Documentation

- `prompt.md` - System prompt
- `rules.md` - Detailed rules
- `examples.md` - Usage examples
"""
    
    async def _write_agent_files(
        self,
        agent_name: str,
        agent_files: Dict[str, str]
    ) -> list:
        """Write agent files to disk"""
        
        files_created = []
        base_path = f".kiro/agents/{agent_name}/"
        
        for filename, content in agent_files.items():
            file_path = f"{base_path}{filename}"
            
            await self.use_tool("fsWrite", {
                "path": file_path,
                "text": content
            })
            
            files_created.append(file_path)
        
        return files_created
    
    async def _validate_agent(self, agent_name: str) -> bool:
        """Validate agent structure"""
        
        base_path = f".kiro/agents/{agent_name}/"
        required_files = ['config.json', 'prompt.md', 'rules.md', 'examples.md', 'README.md']
        
        for filename in required_files:
            try:
                await self.use_tool("readFile", {
                    "path": f"{base_path}{filename}"
                })
            except:
                return False
        
        return True
