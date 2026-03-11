"""
Bugfix Workflow Agent
Systematic bug fixing using bug condition methodology
"""

from typing import Any, Dict
from ...core.base_agent import BaseAgent
from ...models.agent import AgentContext, AgentResult, AgentResultStatus


class BugfixAgent(BaseAgent):
    """Agent for bugfix workflow"""
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute bugfix workflow"""
        
        preset = context.preset or "requirements"
        feature_name = context.intent.feature_name
        spec_path = f".kiro/specs/{feature_name}/"
        
        if preset == "requirements":
            return await self._create_bugfix_analysis(context, spec_path)
        elif preset == "design":
            return await self._create_fix_design(context, spec_path)
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
    
    async def _create_bugfix_analysis(
        self,
        context: AgentContext,
        spec_path: str
    ) -> AgentResult:
        """Create bugfix.md with bug analysis"""
        
        self.update_progress(10, "Analyzing bug report")
        
        # Gather context from memory
        relevant_context = await self.search_memory(context.request, limit=10)
        
        self.update_progress(30, "Identifying root cause")
        
        # Analyze bug and identify root cause
        bugfix_content = await self._generate_bugfix_content(
            context.request,
            relevant_context
        )
        
        self.update_progress(60, "Creating bugfix.md")
        
        # Write bugfix file
        bugfix_path = f"{spec_path}bugfix.md"
        await self.use_tool("fsWrite", {
            "path": bugfix_path,
            "text": bugfix_content
        })
        
        self.update_progress(80, "Creating config file")
        
        # Create config file
        config_content = self._generate_config(
            spec_type="bugfix",
            workflow_type="requirements-first"
        )
        await self.use_tool("fsWrite", {
            "path": f"{spec_path}.config.kiro",
            "text": config_content
        })
        
        self.update_progress(100, "Bug analysis complete")
        
        # Request user validation of root cause
        approval = await self.request_user_input(
            "Bug analysis complete. Is the root cause correct?",
            options=["Yes", "No - Re-investigate"]
        )
        
        return AgentResult(
            status=AgentResultStatus.SUCCESS,
            agent_name=self.config.name,
            files_created=[bugfix_path, f"{spec_path}.config.kiro"],
            output="Bug analysis completed successfully",
            next_action={
                "phase": "design",
                "requires_approval": True,
                "approved": approval.lower() in ["yes", "y"]
            }
        )
    
    async def _create_fix_design(
        self,
        context: AgentContext,
        spec_path: str
    ) -> AgentResult:
        """Create design.md with fix design"""
        
        self.update_progress(10, "Reading bug analysis")
        
        # Read bugfix analysis
        bugfix = await self.use_tool("readFile", {
            "path": f"{spec_path}bugfix.md"
        })
        
        self.update_progress(30, "Designing fix")
        
        # Generate fix design
        design_content = await self._generate_fix_design_content(
            bugfix,
            context.request
        )
        
        self.update_progress(70, "Creating design.md")
        
        # Write design file
        design_path = f"{spec_path}design.md"
        await self.use_tool("fsWrite", {
            "path": design_path,
            "text": design_content
        })
        
        self.update_progress(100, "Fix design complete")
        
        # Request user approval
        approval = await self.request_user_input(
            "Fix design created. Please review design.md. Continue?",
            options=["Yes", "No", "Modify"]
        )
        
        return AgentResult(
            status=AgentResultStatus.SUCCESS,
            agent_name=self.config.name,
            files_created=[design_path],
            output="Fix design created successfully",
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
        """Create tasks.md for bugfix"""
        
        self.update_progress(10, "Reading bugfix analysis and design")
        
        # Read bugfix and design
        files = await self.use_tool("readMultipleFiles", {
            "paths": [
                f"{spec_path}bugfix.md",
                f"{spec_path}design.md"
            ]
        })
        
        self.update_progress(40, "Generating task list")
        
        # Generate tasks content
        tasks_content = await self._generate_bugfix_tasks_content(
            files[f"{spec_path}bugfix.md"],
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
            output="Task list created. Ready for execution starting with exploration test.",
            next_action={
                "phase": None,
                "ready_for_execution": True,
                "special_note": "Task 1 is exploration test - expected to fail on unfixed code"
            }
        )
    
    async def _generate_bugfix_content(
        self,
        request: str,
        context: list
    ) -> str:
        """Generate bugfix analysis content"""
        return f"""# Bugfix Analysis

## Bug Description
{request}

## Reproduction Steps
1. Step 1
2. Step 2
3. Observe the bug

## Root Cause Analysis

### Investigation Process
- Analyzed code in module X
- Found issue in function Y
- Root cause: Division by zero when quantity is 0

### Root Cause
The bug occurs because the code does not check for zero values before division.

### Why It Happens
When quantity is set to 0, the calculation `total / quantity` causes a division by zero error.

## Bug Condition C(X)

### Preconditions
- System is in normal state
- User has access to quantity field

### Trigger
- User sets quantity to 0
- System attempts calculation

### Expected Behavior
- System should handle zero quantity gracefully
- Display appropriate message or use default value

### Actual Behavior
- Application crashes with division by zero error
- User sees error screen

## Affected Code

### Files
- `src/calculator.py`

### Functions
- `calculate_average(total, quantity)`

### Lines
- Line 45: `average = total / quantity`

## Impact Assessment
- Severity: High (causes crash)
- Affected users: All users who can set quantity
- Workaround: Avoid setting quantity to 0
"""
    
    async def _generate_fix_design_content(
        self,
        bugfix: str,
        request: str
    ) -> str:
        """Generate fix design content"""
        return f"""# Fix Design

## Fix Strategy

### Approach
Add validation to check for zero quantity before division.

### Rationale
- Prevents division by zero
- Maintains existing functionality for non-zero values
- Minimal code change

## Fix Implementation

### Code Changes
```python
def calculate_average(total, quantity):
    if quantity == 0:
        return 0  # or raise ValueError("Quantity cannot be zero")
    return total / quantity
```

### Algorithm
1. Check if quantity is 0
2. If yes, return 0 (or handle appropriately)
3. If no, proceed with division

## Preservation Check

### Existing Behavior to Preserve
- Calculation works correctly for non-zero quantities
- Return type remains the same
- Function signature unchanged

### Preservation Plan
- Add tests for existing behavior
- Ensure all existing tests still pass
- Verify no regression in related functionality

## Testing Strategy

### Exploration Test
Test that confirms bug exists on unfixed code:
```python
def test_bug_condition_quantity_zero():
    # This test should FAIL on unfixed code
    with pytest.raises(ZeroDivisionError):
        calculate_average(100, 0)
```

### Preservation Test
Test that existing behavior is preserved:
```python
def test_calculate_average_normal():
    assert calculate_average(100, 10) == 10
    assert calculate_average(50, 5) == 10
```

### Integration Test
Test the fix in full context:
```python
def test_quantity_zero_handled():
    result = calculate_average(100, 0)
    assert result == 0  # or appropriate handling
```
"""
    
    async def _generate_bugfix_tasks_content(
        self,
        bugfix: str,
        design: str
    ) -> str:
        """Generate bugfix tasks content"""
        return f"""# Bugfix Implementation Tasks

- [ ] 1. Write bug condition exploration property test
  - [ ] 1.1 Create test that checks bug condition C(X)
  - [ ] 1.2 Run test on unfixed code (should FAIL)
  - [ ] 1.3 Document counterexample

- [ ] 2. Implement fix
  - [ ] 2.1 Add zero check before division
  - [ ] 2.2 Handle zero case appropriately
  - [ ] 2.3 Run exploration test (should PASS now)

- [ ] 3. Write preservation property tests
  - [ ] 3.1 Test existing behavior with non-zero values
  - [ ] 3.2 Verify no regression
  - [ ] 3.3 All existing tests pass

- [ ] 4. Integration testing
  - [ ] 4.1 Test in full application context
  - [ ] 4.2 Test edge cases
  - [ ] 4.3 Manual testing

- [ ]* 5. Update documentation (optional)
  - [ ]* 5.1 Update function documentation
  - [ ]* 5.2 Add comments about zero handling
"""
    
    def _generate_config(self, spec_type: str, workflow_type: str) -> str:
        """Generate config file content"""
        return f"""specType: {spec_type}
workflowType: {workflow_type}
"""
