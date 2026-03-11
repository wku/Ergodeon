"""
General Task Execution Agent
Executes general development tasks
"""

from typing import Any, Dict, List
from ...core.base_agent import BaseAgent
from ...models.agent import AgentContext, AgentResult, AgentResultStatus


class GeneralTaskAgent(BaseAgent):
    """Agent for general task execution"""
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute general task"""
        
        self.update_progress(10, "Analyzing task")
        
        # Analyze task requirements
        task_analysis = await self._analyze_task(context.request)
        
        self.update_progress(30, "Gathering context")
        
        # Search memory for relevant context
        relevant_context = await self.search_memory(context.request, limit=10)
        
        self.update_progress(50, "Executing task")
        
        # Execute the task
        result = await self._execute_task(
            task_analysis,
            relevant_context,
            context
        )
        
        self.update_progress(90, "Validating result")
        
        # Validate result
        validation = await self._validate_result(result)
        
        self.update_progress(100, "Task complete")
        
        return AgentResult(
            status=AgentResultStatus.SUCCESS if validation else AgentResultStatus.PARTIAL,
            agent_name=self.config.name,
            files_created=result.get('files_created', []),
            files_modified=result.get('files_modified', []),
            output=result.get('output', 'Task completed'),
            result=result
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
    
    async def _analyze_task(self, request: str) -> Dict[str, Any]:
        """Analyze task to determine what needs to be done"""
        
        task_type = self._determine_task_type(request)
        
        return {
            'type': task_type,
            'request': request,
            'requires_code_changes': task_type in ['implement', 'refactor', 'fix'],
            'requires_testing': task_type in ['implement', 'fix'],
            'requires_documentation': task_type in ['implement', 'document']
        }
    
    def _determine_task_type(self, request: str) -> str:
        """Determine task type from request"""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ['create', 'add', 'implement', 'build']):
            return 'implement'
        elif any(word in request_lower for word in ['refactor', 'improve', 'optimize']):
            return 'refactor'
        elif any(word in request_lower for word in ['fix', 'bug', 'error']):
            return 'fix'
        elif any(word in request_lower for word in ['test', 'testing']):
            return 'test'
        elif any(word in request_lower for word in ['document', 'documentation']):
            return 'document'
        else:
            return 'general'
    
    async def _execute_task(
        self,
        task_analysis: Dict[str, Any],
        context: List[Dict],
        agent_context: AgentContext
    ) -> Dict[str, Any]:
        """Execute the actual task"""
        
        task_type = task_analysis['type']
        
        if task_type == 'implement':
            return await self._implement_feature(task_analysis, context)
        elif task_type == 'refactor':
            return await self._refactor_code(task_analysis, context)
        elif task_type == 'fix':
            return await self._fix_issue(task_analysis, context)
        elif task_type == 'test':
            return await self._write_tests(task_analysis, context)
        elif task_type == 'document':
            return await self._write_documentation(task_analysis, context)
        else:
            return await self._execute_general_task(task_analysis, context)
    
    async def _implement_feature(
        self,
        task_analysis: Dict[str, Any],
        context: List[Dict]
    ) -> Dict[str, Any]:
        """Implement a new feature"""
        
        files_created = []
        files_modified = []
        
        # Example: Create component file
        component_path = "src/components/NewComponent.tsx"
        component_content = self._generate_component_code(task_analysis['request'])
        
        await self.use_tool("fsWrite", {
            "path": component_path,
            "text": component_content
        })
        files_created.append(component_path)
        
        # Create test file
        test_path = "src/components/NewComponent.test.tsx"
        test_content = self._generate_test_code(task_analysis['request'])
        
        await self.use_tool("fsWrite", {
            "path": test_path,
            "text": test_content
        })
        files_created.append(test_path)
        
        # Run tests
        test_result = await self.use_tool("executeBash", {
            "command": "npm test -- NewComponent.test.tsx"
        })
        
        return {
            'files_created': files_created,
            'files_modified': files_modified,
            'output': f"Feature implemented: {len(files_created)} files created",
            'test_result': test_result
        }
    
    async def _refactor_code(
        self,
        task_analysis: Dict[str, Any],
        context: List[Dict]
    ) -> Dict[str, Any]:
        """Refactor existing code"""
        
        files_modified = []
        
        # Find files to refactor
        files = await self.use_tool("grepSearch", {
            "query": "function.*Component"
        })
        
        # Refactor each file
        for file_info in files[:3]:  # Limit to 3 files
            file_path = file_info['file']
            
            # Read file
            content = await self.use_tool("readFile", {
                "path": file_path
            })
            
            # Apply refactoring
            await self.use_tool("editCode", {
                "path": file_path,
                "operation": "replace_node",
                "selector": "ComponentName",
                "replacement": "// Refactored code"
            })
            
            files_modified.append(file_path)
        
        return {
            'files_modified': files_modified,
            'output': f"Refactored {len(files_modified)} files"
        }
    
    async def _fix_issue(
        self,
        task_analysis: Dict[str, Any],
        context: List[Dict]
    ) -> Dict[str, Any]:
        """Fix an issue"""
        
        files_modified = []
        
        # Identify file with issue
        file_path = "src/utils/helper.ts"
        
        # Read file
        content = await self.use_tool("readFile", {
            "path": file_path
        })
        
        # Apply fix
        await self.use_tool("strReplace", {
            "path": file_path,
            "oldStr": "const result = value / 0;",
            "newStr": "const result = value / (divisor || 1);"
        })
        
        files_modified.append(file_path)
        
        # Run tests
        test_result = await self.use_tool("executeBash", {
            "command": "npm test"
        })
        
        return {
            'files_modified': files_modified,
            'output': f"Issue fixed in {len(files_modified)} files",
            'test_result': test_result
        }
    
    async def _write_tests(
        self,
        task_analysis: Dict[str, Any],
        context: List[Dict]
    ) -> Dict[str, Any]:
        """Write tests"""
        
        files_created = []
        
        test_path = "tests/unit/test_feature.py"
        test_content = self._generate_test_code(task_analysis['request'])
        
        await self.use_tool("fsWrite", {
            "path": test_path,
            "text": test_content
        })
        files_created.append(test_path)
        
        # Run tests
        test_result = await self.use_tool("executeBash", {
            "command": "pytest tests/unit/test_feature.py"
        })
        
        return {
            'files_created': files_created,
            'output': f"Tests created: {len(files_created)} files",
            'test_result': test_result
        }
    
    async def _write_documentation(
        self,
        task_analysis: Dict[str, Any],
        context: List[Dict]
    ) -> Dict[str, Any]:
        """Write documentation"""
        
        files_created = []
        
        doc_path = "docs/feature.md"
        doc_content = self._generate_documentation(task_analysis['request'])
        
        await self.use_tool("fsWrite", {
            "path": doc_path,
            "text": doc_content
        })
        files_created.append(doc_path)
        
        return {
            'files_created': files_created,
            'output': f"Documentation created: {len(files_created)} files"
        }
    
    async def _execute_general_task(
        self,
        task_analysis: Dict[str, Any],
        context: List[Dict]
    ) -> Dict[str, Any]:
        """Execute general task"""
        
        return {
            'output': f"General task executed: {task_analysis['request']}"
        }
    
    async def _validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate task result"""
        
        # Check if files were created/modified
        has_changes = (
            len(result.get('files_created', [])) > 0 or
            len(result.get('files_modified', [])) > 0
        )
        
        # Check if tests passed (if applicable)
        test_result = result.get('test_result', '')
        tests_passed = 'FAILED' not in test_result if test_result else True
        
        return has_changes or tests_passed
    
    def _generate_component_code(self, request: str) -> str:
        """Generate component code"""
        return f"""import React from 'react';

interface Props {{
  // Props here
}}

export const NewComponent: React.FC<Props> = (props) => {{
  return (
    <div>
      {/* Component implementation */}
    </div>
  );
}};
"""
    
    def _generate_test_code(self, request: str) -> str:
        """Generate test code"""
        return f"""import {{ render, screen }} from '@testing-library/react';
import {{ NewComponent }} from './NewComponent';

describe('NewComponent', () => {{
  it('renders correctly', () => {{
    render(<NewComponent />);
    expect(screen.getByText(/component/i)).toBeInTheDocument();
  }});
}});
"""
    
    def _generate_documentation(self, request: str) -> str:
        """Generate documentation"""
        return f"""# Feature Documentation

## Overview
{request}

## Usage
...

## API
...

## Examples
...
"""
