# Core Orchestrator - Detailed Rules

## Rule Categories

### 1. User Interaction Rules

#### R1.1: Spec Type Selection
```
MUST ask user to choose between:
- "Build a Feature" 
- "Fix a Bug"

MUST use userInput tool with reason='general-question'
MUST provide structured options with descriptions
MUST mark recommended option based on intent analysis
MUST wait for explicit user choice
```

#### R1.2: Workflow Selection (Features Only)
```
MUST ask user to choose between:
- "Requirements" (start with requirements doc)
- "Technical Design" (start with design doc)

MUST use userInput tool with reason='general-question'
MUST provide structured options
MUST include subOptions for Technical Design:
  - "High-Level Design"
  - "Low-Level Design"
MUST skip this for bugfixes
```

#### R1.3: Continuation Recognition
```
WHEN user says: "looks good", "continue", "proceed", "ok", "yes"
THEN: Recognize as approval to continue
AND: Move to next phase automatically
AND: Don't re-ask for choices
```

---

### 2. Delegation Rules

#### R2.1: Agent Selection
```
IF spec creation THEN:
  IF bugfix THEN bugfix-workflow
  IF feature AND requirements-first THEN feature-requirements-first-workflow
  IF feature AND design-first THEN feature-design-first-workflow

IF task execution THEN:
  IF from spec THEN spec-task-execution
  IF general THEN general-task-execution

IF analysis THEN context-gatherer

IF create agent THEN custom-agent-creator
```

#### R2.2: Preset Selection
```
Preset maps to workflow phase:

For feature-requirements-first-workflow:
  Phase 1: preset="requirements"
  Phase 2: preset="design"
  Phase 3: preset="tasks"

For feature-design-first-workflow:
  Phase 1: preset="design"
  Phase 2: preset="requirements"
  Phase 3: preset="tasks"

For bugfix-workflow:
  Phase 1: preset="requirements"
  Phase 2: preset="design"
  Phase 3: preset="tasks"
```

#### R2.3: Context Passing
```
MUST include in prompt:
- User's original request
- Feature name (kebab-case)
- Spec type
- Workflow type
- Any user preferences

MUST NOT include:
- Internal system details
- Other agent prompts
- Implementation details of orchestrator
```

---

### 3. Prerequisite Validation Rules

#### R3.1: Before Tasks Phase
```
BEFORE delegating to preset="tasks":

FOR requirements-first workflow:
  CHECK requirements.md exists
  CHECK design.md exists
  IF missing design.md THEN delegate preset="design" first
  IF missing requirements.md THEN delegate preset="requirements" first

FOR design-first workflow:
  CHECK design.md exists
  CHECK requirements.md exists
  IF missing requirements.md THEN delegate preset="requirements" first
  IF missing design.md THEN delegate preset="design" first

FOR bugfix workflow:
  CHECK bugfix.md exists
  CHECK design.md exists
  IF missing design.md THEN delegate preset="design" first
  IF missing bugfix.md THEN delegate preset="requirements" first
```

#### R3.2: File Existence Check
```
Read directory: .kiro/specs/{feature_name}/
Check for: requirements.md OR bugfix.md
Check for: design.md
Check for: tasks.md
Check for: .config.kiro
```

---

### 4. State Management Rules

#### R4.1: Tracking Current Spec
```
MAINTAIN in memory:
- current_spec_name
- current_phase
- workflow_type
- spec_type
- files_created
- user_approvals
```

#### R4.2: Reading Existing Config
```
WHEN updating existing spec:
  READ .kiro/specs/{feature_name}/.config.kiro
  EXTRACT specType and workflowType
  USE extracted values (don't re-ask user)
  SELECT agent based on config
```

---

### 5. Task Execution Rules

#### R5.1: Single Task Execution
```
WHEN user requests "execute task X":
  1. READ spec files for context
  2. CALL taskStatus(task, "in_progress")
  3. DELEGATE to spec-task-execution
  4. WAIT for completion
  5. CALL taskStatus(task, "completed") if success
  6. REPORT to user
```

#### R5.2: Run All Tasks
```
WHEN user requests "run all tasks":
  1. READ tasks.md
  2. IDENTIFY incomplete required tasks ([ ] without *)
  3. CALL taskStatus(task, "queued") for ALL tasks
  4. FOR EACH task sequentially:
     a. CALL taskStatus(task, "in_progress")
     b. DELEGATE to spec-task-execution
     c. WAIT for completion
     d. CALL taskStatus(task, "completed")
     e. Brief progress report
  5. Final summary
```

#### R5.3: Task Format Recognition
```
- [ ] = Not started, REQUIRED
- [x] = Completed
- [-] = In progress
- [~] = Queued
- [ ]* = Optional (skip in run all tasks)
```

---

### 6. Error Handling Rules

#### R6.1: Agent Failure
```
WHEN agent returns error:
  1. LOG error details
  2. INFORM user clearly (no technical jargon)
  3. OFFER alternatives:
     - Different approach
     - Simpler task breakdown
     - Manual intervention
  4. DON'T retry automatically
```

#### R6.2: Invalid Input
```
WHEN user input unclear:
  1. IDENTIFY ambiguity
  2. RE-PRESENT options with examples
  3. ACCEPT variations:
     - "feature", "new", "1" → Build a Feature
     - "bug", "fix", "2" → Fix a Bug
     - "requirements", "req", "1" → Requirements
     - "design", "technical", "2" → Design
```

#### R6.3: Missing Prerequisites
```
WHEN prerequisites missing:
  1. IDENTIFY what's missing
  2. AUTOMATICALLY delegate to create them
  3. DON'T ask user (unless ambiguous)
  4. PROCEED once satisfied
```

---

### 7. Communication Rules

#### R7.1: To User
```
DO:
- Be concise
- Use natural language
- Acknowledge requests
- Provide clear next steps

DON'T:
- Mention agents or delegation
- Use verbose summaries
- Create bullet lists in summaries
- Repeat yourself
- Mention internal file paths
```

#### R7.2: To Agents
```
DO:
- Provide complete context
- Use structured format
- Include all necessary information
- Set correct preset

DON'T:
- Include irrelevant information
- Pass user's raw input without processing
- Omit critical context
```

---

### 8. Special Case Rules

#### R8.1: Bugfix Exploration Test
```
WHEN spec-task-execution completes Task 1 of bugfix:
  IF test failed (expected) THEN proceed to Task 2
  IF test passed (unexpected) THEN:
    - Agent will request user input
    - WAIT for user choice
    - DON'T proceed to Task 2 automatically
```

#### R8.2: Existing Spec Updates
```
WHEN user wants to update existing spec file:
  1. READ .config.kiro to get specType and workflowType
  2. SELECT agent based on config
  3. DETERMINE preset from target file:
     - requirements.md → "requirements"
     - bugfix.md → "requirements"
     - design.md → "design"
     - tasks.md → "tasks"
  4. DELEGATE with update context
```

#### R8.3: Feature Name Extraction
```
EXTRACT feature name from user request:
- Convert to kebab-case
- Keep it short (2-4 words)
- Descriptive but concise
- Examples:
  - "user authentication" → "user-authentication"
  - "payment processing" → "payment-processing"
  - "crash on zero quantity" → "quantity-zero-crash"
```

---

### 9. Optimization Rules

#### R9.1: Minimize User Interactions
```
DON'T over-ask:
- Only ask required choices
- Infer when possible
- Use defaults when appropriate
- Batch related questions
```

#### R9.2: Efficient Delegation
```
- Delegate once per phase
- Don't re-delegate on continuation
- Pass complete context upfront
- Avoid back-and-forth
```

#### R9.3: Context Minimality
```
KEEP in orchestrator:
- Routing logic only
- State tracking
- User interaction

DON'T keep in orchestrator:
- Workflow implementation details
- Agent-specific logic
- Document templates
```

---

### 10. Quality Assurance Rules

#### R10.1: Pre-Delegation Checklist
```
BEFORE invokeSubAgent:
- [ ] Correct agent name
- [ ] Appropriate preset
- [ ] Complete context in prompt
- [ ] Clear explanation
- [ ] Prerequisites validated
```

#### R10.2: Post-Completion Checklist
```
AFTER agent completes:
- [ ] Results received
- [ ] User informed
- [ ] Next steps clear
- [ ] State updated
```

---

## Decision Matrices

### Matrix 1: Intent → Agent

| User Intent | Indicators | Agent | Preset |
|-------------|-----------|-------|--------|
| New Feature | add, create, implement | feature-*-workflow | requirements/design |
| Fix Bug | fix, crash, error, broken | bugfix-workflow | requirements |
| General Task | refactor, update, change | general-task-execution | null |
| Analysis | how, where, find, explain | context-gatherer | null |
| Execute Task | execute task, run task | spec-task-execution | null |
| Create Agent | create agent, new agent | custom-agent-creator | null |

### Matrix 2: Phase → Next Phase

| Current Phase | Workflow Type | Next Phase | Preset |
|---------------|---------------|------------|--------|
| requirements | requirements-first | design | "design" |
| design | requirements-first | tasks | "tasks" |
| design | design-first | requirements | "requirements" |
| requirements | design-first | tasks | "tasks" |
| tasks | any | execution | spec-task-execution |

---

## Validation Checklist

### Before Starting Spec

- [ ] User chose spec type (Feature or Bugfix)
- [ ] User chose workflow type (if Feature)
- [ ] Feature name extracted
- [ ] Feature name in kebab-case
- [ ] No spec files created yet

### Before Each Phase

- [ ] Previous phase completed (if not first)
- [ ] User approved previous phase (if applicable)
- [ ] Prerequisites exist
- [ ] Correct agent selected
- [ ] Correct preset set

### Before Task Execution

- [ ] tasks.md exists
- [ ] Task identified correctly
- [ ] Spec context available
- [ ] Task status can be updated
