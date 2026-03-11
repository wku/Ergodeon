# Bugfix Workflow - Workflow Diagrams

## Overview

Агент для систематического исправления багов с использованием bug condition methodology.

---

## Main Workflow

```mermaid
flowchart TD
    A[User: Report Bug] --> B[Core: Feature or Bugfix?]
    B --> C[User: Bugfix]
    C --> D[Extract Bug Name]
    D --> E[Phase 1: Bug Analysis]
    E --> F[Create bugfix.md]
    F --> G[User Review Root Cause]
    G -->|Correct| H[Phase 2: Fix Design]
    G -->|Incorrect| E
    H --> I[Create design.md]
    I --> J[User Review Fix]
    J -->|Approved| K[Phase 3: Tasks]
    J -->|Changes| H
    K --> L[Create tasks.md]
    L --> M[Execute Task 1: Exploration Test]
    M --> N{Test Result?}
    N -->|Fails as Expected| O[Bug Confirmed]
    N -->|Passes Unexpectedly| P[Re-investigate]
    O --> Q[Execute Remaining Tasks]
    Q --> R[Bug Fixed]
```

---

## Phase Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant C as Core
    participant BF as bugfix-workflow
    participant STE as spec-task-execution
    participant FS as File System
    
    U->>C: "App crashes when quantity is zero"
    C->>U: Feature or Bugfix?
    U->>C: Bugfix
    
    C->>BF: preset="requirements"
    BF->>BF: Analyze bug
    BF->>BF: Identify root cause
    BF->>BF: Define bug condition C(X)
    BF->>FS: Write bugfix.md
    BF->>FS: Write .config.kiro
    BF->>U: Review root cause
    U->>BF: Root cause correct
    
    BF->>C: Bug analysis complete
    C->>BF: preset="design"
    BF->>FS: Read bugfix.md
    BF->>BF: Design fix
    BF->>FS: Write design.md
    BF->>U: Review fix design
    U->>BF: Approved
    
    BF->>C: Fix design complete
    C->>BF: preset="tasks"
    BF->>FS: Read bugfix.md, design.md
    BF->>BF: Generate tasks
    BF->>FS: Write tasks.md
    BF->>C: Tasks complete
    
    C->>STE: Execute Task 1 (exploration test)
    STE->>STE: Write exploration test
    STE->>STE: Run test on unfixed code
    
    alt Test Fails (Expected)
        STE->>C: Bug confirmed
        C->>STE: Execute Task 2 (implement fix)
        STE->>STE: Implement fix
        STE->>C: Fix complete
    else Test Passes (Unexpected)
        STE->>U: Test passed unexpectedly
        U->>STE: "Continue" or "Re-investigate"
    end
```

---

## Bug Analysis Phase

```mermaid
flowchart TD
    A[Start Bug Analysis] --> B[Gather Bug Information]
    B --> C[Reproduce Bug]
    C --> D{Reproduced?}
    D -->|No| E[Request More Info]
    E --> B
    D -->|Yes| F[Analyze Root Cause]
    F --> G[Identify Bug Condition C(X)]
    G --> H[Define Affected Code]
    H --> I[Assess Impact]
    I --> J[Write bugfix.md]
    J --> K[Request User Validation]
    K --> L{Root Cause Correct?}
    L -->|Yes| M[Phase Complete]
    L -->|No| N[Gather Feedback]
    N --> F
```

---

## Bug Condition Methodology

```mermaid
graph TB
    A[Bug Condition C(X)] --> B[Preconditions]
    A --> C[Trigger Conditions]
    A --> D[Expected Behavior]
    A --> E[Actual Behavior]
    
    B --> B1[System State]
    B --> B2[Input Constraints]
    
    C --> C1[User Action]
    C --> C2[System Event]
    
    D --> D1[Correct Output]
    D --> D2[Correct State]
    
    E --> E1[Buggy Output]
    E --> E2[Buggy State]
```

---

## Fix Design Phase

```mermaid
flowchart TD
    A[Start Fix Design] --> B[Read bugfix.md]
    B --> C[Understand Bug Condition]
    C --> D[Design Fix Strategy]
    D --> E[Ensure Preservation]
    E --> F[Design Fix Implementation]
    F --> G[Plan Testing Strategy]
    G --> H[Write design.md]
    H --> I[Request User Review]
    I --> J{Approved?}
    J -->|Yes| K[Phase Complete]
    J -->|No| L[Gather Feedback]
    L --> D
```

---

## Tasks Phase

```mermaid
flowchart TD
    A[Start Tasks] --> B[Read bugfix.md]
    B --> C[Read design.md]
    C --> D[Create Task 1: Exploration Test]
    D --> E[Create Task 2: Implement Fix]
    E --> F[Create Task 3: Preservation Test]
    F --> G[Create Task 4: Integration Test]
    G --> H[Add Optional Tasks]
    H --> I[Write tasks.md]
    I --> J[Phase Complete]
```

---

## Exploration Test Execution

```mermaid
flowchart TD
    A[Execute Task 1] --> B[Write Exploration Test]
    B --> C[Test Checks Bug Condition C(X)]
    C --> D[Run Test on Unfixed Code]
    D --> E{Test Result?}
    
    E -->|Fails| F[Bug Confirmed]
    E -->|Passes| G[Unexpected Pass]
    
    F --> H[Document Counterexample]
    F --> I[Mark Task Complete]
    F --> J[Proceed to Task 2]
    
    G --> K[Analyze Why Test Passed]
    K --> L[Present Options to User]
    L --> M{User Choice?}
    M -->|Continue| J
    M -->|Re-investigate| N[Return to Bug Analysis]
```

---

## Unexpected Pass Handling

```mermaid
sequenceDiagram
    participant STE as spec-task-execution
    participant U as User
    participant C as Core
    
    STE->>STE: Run exploration test
    STE->>STE: Test passes (unexpected)
    
    STE->>U: Analysis: Why test passed
    Note over STE,U: Possible reasons:<br/>1. Code already fixed<br/>2. Root cause incorrect<br/>3. Test logic issue
    
    STE->>U: Options:<br/>1. Continue anyway<br/>2. Re-investigate
    
    U->>STE: Choice
    
    alt Continue
        STE->>C: Proceed to Task 2
    else Re-investigate
        STE->>C: Stop execution
        C->>U: Please re-investigate root cause
    end
```

---

## Document Structure

### bugfix.md

```mermaid
graph TB
    A[bugfix.md] --> B[Bug Description]
    A --> C[Reproduction Steps]
    A --> D[Root Cause Analysis]
    A --> E[Bug Condition C(X)]
    A --> F[Affected Code]
    A --> G[Impact Assessment]
    
    D --> D1[Investigation Process]
    D --> D2[Root Cause]
    D --> D3[Why It Happens]
    
    E --> E1[Preconditions]
    E --> E2[Trigger]
    E --> E3[Expected vs Actual]
    
    F --> F1[Files]
    F --> F2[Functions]
    F --> F3[Lines]
```

### design.md (for bugfix)

```mermaid
graph TB
    A[design.md] --> B[Fix Strategy]
    A --> C[Fix Implementation]
    A --> D[Preservation Check]
    A --> E[Testing Strategy]
    
    B --> B1[Approach]
    B --> B2[Rationale]
    
    C --> C1[Code Changes]
    C --> C2[Algorithm]
    
    D --> D1[Existing Behavior]
    D --> D2[Preservation Plan]
    
    E --> E1[Exploration Test]
    E --> E2[Preservation Test]
    E --> E3[Integration Test]
```

### tasks.md (for bugfix)

```mermaid
graph TB
    A[tasks.md] --> B[Task 1: Exploration Test]
    A --> C[Task 2: Implement Fix]
    A --> D[Task 3: Preservation Test]
    A --> E[Task 4: Integration Test]
    A --> F[Optional Tasks]
    
    B --> B1[Write test for C(X)]
    B --> B2[Run on unfixed code]
    B --> B3[Confirm bug exists]
    
    C --> C1[Implement fix]
    C --> C2[Run exploration test]
    C --> C3[Verify fix works]
    
    D --> D1[Test existing behavior]
    D --> D2[Ensure no regression]
    
    E --> E1[Full integration test]
    E --> E2[Edge cases]
    
    style B fill:#FFB6C1
    style C fill:#90EE90
    style D fill:#90EE90
    style E fill:#90EE90
```

---

## State Management

```mermaid
stateDiagram-v2
    [*] --> NotStarted
    NotStarted --> BugAnalysis: Start
    BugAnalysis --> BugReview: bugfix.md Created
    BugReview --> BugAnalysis: Root Cause Incorrect
    BugReview --> FixDesign: Root Cause Correct
    FixDesign --> FixReview: design.md Created
    FixReview --> FixDesign: Changes Requested
    FixReview --> Tasks: Approved
    Tasks --> ExplorationTest: tasks.md Created
    ExplorationTest --> BugConfirmed: Test Fails
    ExplorationTest --> Reinvestigate: Test Passes
    Reinvestigate --> BugAnalysis: User Choice
    Reinvestigate --> ImplementFix: Continue Anyway
    BugConfirmed --> ImplementFix: Proceed
    ImplementFix --> Complete: All Tasks Done
    Complete --> [*]
```

---

## Error Handling

```mermaid
flowchart TD
    A[Error Detected] --> B{Error Type?}
    
    B -->|Cannot Reproduce| C[Request More Info]
    B -->|Root Cause Unclear| D[Deeper Investigation]
    B -->|Test Passes Unexpectedly| E[User Decision]
    B -->|Fix Breaks Tests| F[Revise Fix]
    
    C --> G[Continue]
    D --> G
    E --> H{Choice?}
    H -->|Continue| G
    H -->|Re-investigate| I[Back to Analysis]
    F --> G
```

---

## Key Concepts

### Bug Condition C(X)

```
C(X) = {
  preconditions: [state before bug],
  trigger: [action that causes bug],
  expected: [correct behavior],
  actual: [buggy behavior]
}
```

### Preservation

```
Preservation = {
  existing_behavior: [what should not change],
  tests: [tests to verify preservation],
  validation: [how to check]
}
```

### Fix Checking

```
Fix Checking = {
  exploration_test: [confirms bug exists],
  fix_test: [confirms fix works],
  preservation_test: [confirms no regression]
}
```

---

## Key Features

1. **Systematic Approach**: Структурированный процесс исправления багов
2. **Bug Condition**: Формальное определение условий бага
3. **Exploration Test**: Тест, подтверждающий существование бага
4. **Preservation**: Проверка, что исправление не ломает существующую функциональность
5. **User Validation**: Подтверждение root cause перед исправлением

---

## Usage Example

```
User: "App crashes when quantity is zero"

Workflow:
1. Core asks: Feature or Bugfix? → Bugfix
2. Extract bug_name: "quantity-zero-crash"
3. Phase 1: Create bugfix.md
   - Reproduce bug
   - Root cause: Division by zero
   - Bug condition C(X)
4. User confirms root cause
5. Phase 2: Create design.md
   - Fix strategy: Add zero check
   - Preservation: Existing calculations
6. User approves fix design
7. Phase 3: Create tasks.md
   - Task 1: Exploration test
   - Task 2: Implement fix
   - Task 3: Preservation test
8. Execute Task 1:
   - Test fails (expected) → Bug confirmed
9. Execute remaining tasks
10. Bug fixed
```

---

## Best Practices

1. **Reproduce First**: Всегда воспроизводите баг перед анализом
2. **Clear Root Cause**: Определите точную причину бага
3. **Formal Bug Condition**: Используйте формальное определение C(X)
4. **Exploration Test**: Пишите тест, который подтверждает баг
5. **Preservation**: Проверяйте, что исправление не ломает существующую функциональность
6. **User Validation**: Получайте подтверждение root cause перед исправлением
