"""
Spec Task Execution Agent
Executes tasks from specifications
"""

from typing import Any, Dict
from ...core.base_agent import BaseAgent
from ...models.agent import AgentContext, AgentResult, AgentResultStatus


class SpecTaskAgent(BaseAgent):
    """Agent for spec task execution"""
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute spec task"""
        
        # Extract task information from context
        task_id = context.metadata.get('task_id')
        spec_path = context.metadata.get('spec_path')
        
        self.update_progress(10, f"Reading task {task_id}")
        
        # Read spec files
        spec_files = await self._read_spec_files(spec_path)
        
        self.update_progress(30, "Analyzing task requirements")
        
        # Parse task details
        task_details = await self._parse_task(task_id, spec_files['tasks'])
        
        self.update_progress(50, "Executing task")
        
        # Execute the task
        result = await self._execute_spec_task(
            task_details,
            spec_files,
            context
        )
        
        self.update_progress(90, "Running tests")
        
        # Run tests
        test_result = await self._run_tests(task_details)
        
        self.update_progress(100, "Task complete")
        
        return AgentResult(
            status=AgentResultStatus.SUCCESS if test_result['passed'] else AgentResultStatus.FAILED,
            agent_name=self.config.name,
            files_created=result.get('files_created', []),
            files_modified=result.get('files_modified', []),
            output=result.get('output', 'Task completed'),
            result={
                **result,
                'test_result': test_result
            }
        )
    
    async def validate(self, context: AgentContext) -> bool:
        """Validate context"""
        return (
            context.metadata.get('task_id') is not None and
            context.metadata.get('spec_path') is not None
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
    
    async def _read_spec_files(self, spec_path: str) -> Dict[str, str]:
        """Read all spec files"""
        
        files = await self.use_tool("readMultipleFiles", {
            "paths": [
                f"{spec_path}requirements.md",
                f"{spec_path}design.md",
                f"{spec_path}tasks.md"
            ]
        })
        
        return {
            'requirements': files.get(f"{spec_path}requirements.md", ''),
            'design': files.get(f"{spec_path}design.md", ''),
            'tasks': files.get(f"{spec_path}tasks.md", '')
        }
    
    async def _parse_task(self, task_id: str, tasks_content: str) -> Dict[str, Any]:
        """Parse task details from tasks.md"""
        
        lines = tasks_content.split('\n')
        task_text = ''
        sub_tasks = []
        
        for line in lines:
            if f"{task_id}." in line or f"{task_id} " in line:
                task_text = line.strip()
            elif task_text and line.strip().startswith(f"- [ ] {task_id}."):
                sub_tasks.append(line.strip())
        
        return {
            'id': task_id,
            'text': task_text,
            'sub_tasks': sub_tasks,
            'is_exploration_test': 'exploration' in task_text.lower() and 'test' in task_text.lower()
        }
    
    async def _execute_spec_task(
        self,
        task_details: Dict[str, Any],
        spec_files: Dict[str, str],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Execute the spec task"""
        
        if task_details['is_exploration_test']:
            return await self._execute_exploration_test(task_details, spec_files)
        else:
            return await self._execute_implementation_task(task_details, spec_files)
    
    async def _execute_exploration_test(
        self,
        task_details: Dict[str, Any],
        spec_files: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute exploration test (for bugfix workflow)"""
        
        files_created = []
        
        # Extract bug condition from bugfix.md or requirements.md
        bug_condition = self._extract_bug_condition(spec_files)
        
        # Generate exploration test
        test_path = "tests/test_bug_exploration.py"
        test_content = self._generate_exploration_test(bug_condition)
        
        await self.use_tool("fsWrite", {
            "path": test_path,
            "text": test_content
        })
        files_created.append(test_path)
        
        # Run test on unfixed code
        test_result = await self.use_tool("executeBash", {
            "command": "pytest tests/test_bug_exploration.py -v"
        })
        
        # Check if test failed as expected
        test_failed = 'FAILED' in test_result or 'ERROR' in test_result
        
        if not test_failed:
            # Test passed unexpectedly - bug might not exist
            return {
                'files_created': files_created,
                'output': 'WARNING: Exploration test passed unexpectedly',
                'unexpected_pass': True,
                'test_output': test_result
            }
        
        return {
            'files_created': files_created,
            'output': 'Exploration test failed as expected - bug confirmed',
            'bug_confirmed': True,
            'test_output': test_result
        }
    
    async def _execute_implementation_task(
        self,
        task_details: Dict[str, Any],
        spec_files: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute implementation task"""
        
        files_created = []
        files_modified = []
        
        # Extract implementation details from design
        implementation_details = self._extract_implementation_details(
            spec_files['design'],
            task_details['text']
        )
        
        # Implement the task
        for file_path, content in implementation_details.items():
            # Check if file exists
            try:
                existing = await self.use_tool("readFile", {"path": file_path})
                # File exists, modify it
                await self.use_tool("editCode", {
                    "path": file_path,
                    "operation": "insert_node",
                    "selector": "end",
                    "replacement": content
                })
                files_modified.append(file_path)
            except:
                # File doesn't exist, create it
                await self.use_tool("fsWrite", {
                    "path": file_path,
                    "text": content
                })
                files_created.append(file_path)
        
        return {
            'files_created': files_created,
            'files_modified': files_modified,
            'output': f"Task implemented: {len(files_created)} files created, {len(files_modified)} modified"
        }
    
    async def _run_tests(self, task_details: Dict[str, Any]) -> Dict[str, Any]:
        """Run tests for the task"""
        
        # Run relevant tests
        test_result = await self.use_tool("executeBash", {
            "command": "npm test"
        })
        
        passed = 'FAILED' not in test_result and 'ERROR' not in test_result
        
        return {
            'passed': passed,
            'output': test_result
        }
    
    def _extract_bug_condition(self, spec_files: Dict[str, str]) -> Dict[str, Any]:
        """Extract bug condition from spec files"""
        
        # Parse bugfix.md or requirements.md for bug condition
        content = spec_files.get('requirements', '')
        
        return {
            'preconditions': 'System in normal state',
            'trigger': 'User action that causes bug',
            'expected': 'Expected behavior',
            'actual': 'Buggy behavior'
        }
    
    def _generate_exploration_test(self, bug_condition: Dict[str, Any]) -> str:
        """Generate exploration test code"""
        
        return f"""import pytest

def test_bug_condition_exploration():
    \"\"\"
    Exploration test for bug condition.
    This test should FAIL on unfixed code.
    
    Preconditions: {bug_condition['preconditions']}
    Trigger: {bug_condition['trigger']}
    Expected: {bug_condition['expected']}
    Actual: {bug_condition['actual']}
    \"\"\"
    
    # Setup preconditions
    # ...
    
    # Trigger bug condition
    # This should raise an error or produce wrong result
    with pytest.raises(Exception):
        # Code that triggers the bug
        result = buggy_function()
    
    # If we reach here, bug exists
    assert False, "Bug condition not triggered"
"""
    
    def _extract_implementation_details(
        self,
        design: str,
        task_text: str
    ) -> Dict[str, str]:
        """Extract implementation details from design"""
        
        # Parse design document for implementation details
        # This is simplified - real implementation would parse markdown
        
        return {
            'src/feature.py': '''def new_feature():
    """Implementation of new feature"""
    pass
''',
            'tests/test_feature.py': '''def test_new_feature():
    """Test for new feature"""
    assert new_feature() is not None
'''
        }
