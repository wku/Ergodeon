# Spec Task Execution Agent - Workflow Diagrams

## Main Execution Flow

```mermaid
flowchart TD
    A[Receive Task] --> B[Parse Task Details]
    B --> C[Read Spec Context]
    C --> D{Has Sub-tasks?}
    
    D -->|Yes| E[Process Sub-tasks]
    D -->|No| F[Direct Implementation]
    
    E --> G[Sub-task 1]
    G --> H[Sub-task 2]
    H --> I[Sub-task N]
    I --> J[All Sub-tasks Complete]
    
    F --> K[Implement Task]
    J --> K
    
    K --> L[Create Tests]
    L --> M[Run Tests]
    M --> N{Tests Pass?}
    
    N -->|No| O[Fix Issues]
    O --> P{Attempt < 3?}
    P -->|Yes| K
    P -->|No| Q[Report Failure]
    
    N -->|Yes| R[Validate with getDiagnostics]
    R --> S{Errors?}
    S -->|Yes| O
    S -->|No| T[Task Complete]
```

---

## Sub-task Processing

```mermaid
flowchart TD
    A[Task with Sub-tasks] --> B[Identify All Sub-tasks]
    B --> C[Order by Dependencies]
    C --> D[Start First Sub-task]
    
    D --> E[Update Status: in_progress]
    E --> F[Implement Sub-task]
    F --> G[Validate]
    G --> H{Success?}
    
    H -->|No| I[Fix Issues]
    I --> F
    
    H -->|Yes| J[Update Status: completed]
    J --> K{More Sub-tasks?}
    
    K -->|Yes| L[Next Sub-task]
    L --> E
    
    K -->|No| M[Parent Task Complete]
```

---

## Property-Based Testing Flow

```mermaid
flowchart TD
    A[Identify Correctness Property] --> B[Design PBT Test]
    B --> C[Choose Generators]
    C --> D[Write Property Assertion]
    D --> E[Set Test Parameters]
    E --> F[Run PBT]
    
    F --> G{Result?}
    
    G -->|Pass| H[Property Validated]
    G -->|Fail| I[Analyze Counterexample]
    
    I --> J[Understand Failure]
    J --> K[Fix Implementation]
    K --> L[Re-run PBT]
    L --> M{Pass Now?}
    
    M -->|Yes| H
    M -->|No| N{Attempt < 3?}
    N -->|Yes| I
    N -->|No| O[Report PBT Failure]
    
    H --> P[Document Property]
```

---

## Bugfix Exploration Test (Task 1)

```mermaid
flowchart TD
    A[Task 1: Exploration Test] --> B[Read Bug Condition C X]
    B --> C[Design Test for C X]
    C --> D[Create Test File]
    D --> E[Write PBT Test]
    E --> F[Run Test on Buggy Code]
    
    F --> G{Test Result?}
    
    G -->|FAIL Expected| H[Bug Confirmed]
    H --> I[Document Counterexample]
    I --> J[updatePBTStatus: passed]
    J --> K[Report Success]
    K --> L[Ready for Task 2]
    
    G -->|PASS Unexpected| M[Bug NOT Detected]
    M --> N[Analyze Why]
    N --> O[Output Detailed Analysis]
    O --> P[updatePBTStatus: unexpected_pass]
    P --> Q[Request User Input]
    
    Q --> R{User Choice?}
    R -->|Continue Anyway| S[Proceed to Task 2]
    R -->|Re-investigate| T[Stop Execution]
```

---

## Test Failure Recovery

```mermaid
flowchart TD
    A[Tests Failed] --> B[Analyze Failure Output]
    B --> C{Failure Type?}
    
    C -->|Assertion Failed| D[Logic Error]
    C -->|Exception Thrown| E[Runtime Error]
    C -->|Timeout| F[Performance Issue]
    
    D --> G[Review Implementation Logic]
    E --> H[Add Error Handling]
    F --> I[Optimize Code]
    
    G --> J[Apply Fix]
    H --> J
    I --> J
    
    J --> K[Re-run Tests]
    K --> L{Pass Now?}
    
    L -->|Yes| M[Success]
    L -->|No| N{Attempt Count?}
    
    N -->|< 3| O[Try Alternative Fix]
    O --> J
    
    N -->|>= 3| P[Report Failure to Orchestrator]
```

---

## Implementation with Validation

```mermaid
flowchart TD
    A[Start Implementation] --> B[Write Code]
    B --> C[Save File]
    C --> D[getDiagnostics]
    
    D --> E{Syntax Errors?}
    E -->|Yes| F[Fix Syntax]
    F --> B
    
    E -->|No| G{Type Errors?}
    G -->|Yes| H[Fix Types]
    H --> B
    
    G -->|No| I[Create Unit Tests]
    I --> J[Run Unit Tests]
    
    J --> K{Pass?}
    K -->|No| L[Fix Implementation]
    L --> B
    
    K -->|Yes| M{Has Correctness Property?}
    M -->|Yes| N[Create PBT Test]
    M -->|No| O[Implementation Complete]
    
    N --> P[Run PBT]
    P --> Q{Pass?}
    Q -->|No| L
    Q -->|Yes| O
```

---

## Task Status Lifecycle

```mermaid
stateDiagram-v2
    [*] --> not_started: Task created
    not_started --> queued: Queued for execution
    not_started --> in_progress: Single task execution
    queued --> in_progress: Orchestrator starts task
    in_progress --> completed: Task successful
    in_progress --> failed: Task failed
    in_progress --> in_progress: Retry after fix
    failed --> in_progress: Retry
    completed --> [*]
    failed --> [*]: Max retries reached
```

---

## Dependency Installation Flow

```mermaid
flowchart TD
    A[Code Needs Dependency] --> B[Check package.json]
    B --> C{Installed?}
    
    C -->|Yes| D[Check Version]
    D --> E{Compatible?}
    E -->|Yes| F[Use Dependency]
    E -->|No| G[Update Version]
    
    C -->|No| H[Determine Package Manager]
    H --> I{npm or yarn?}
    
    I -->|npm| J[executeBash: npm install]
    I -->|yarn| K[executeBash: yarn add]
    
    J --> L[Verify Installation]
    K --> L
    G --> L
    
    L --> M{Success?}
    M -->|Yes| F
    M -->|No| N[Report Error]
```

---

## Integration Test Flow

```mermaid
flowchart TD
    A[Implementation Complete] --> B{Integration Tests Needed?}
    
    B -->|Yes| C[Identify Integration Points]
    B -->|No| D[Skip to Completion]
    
    C --> E[Create Integration Tests]
    E --> F[Setup Test Environment]
    F --> G[Run Integration Tests]
    
    G --> H{Results?}
    
    H -->|All Pass| I[Integration Verified]
    H -->|Some Fail| J[Analyze Failures]
    
    J --> K{Issue in?}
    K -->|Implementation| L[Fix Code]
    K -->|Test| M[Fix Test]
    K -->|Environment| N[Fix Setup]
    
    L --> G
    M --> G
    N --> G
    
    I --> D
    D --> O[Report Completion]
```

---

## Real Scenario: Implement Login Form

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant S as spec-task-execution
    participant FS as File System
    participant T as Test Runner
    participant D as Diagnostics
    
    O->>S: Task 2: Implement login form
    S->>S: Read requirements & design
    S->>FS: fsWrite(LoginForm.jsx)
    FS-->>S: File created
    S->>D: getDiagnostics(LoginForm.jsx)
    D-->>S: No errors
    S->>FS: fsWrite(LoginForm.test.jsx)
    FS-->>S: Test file created
    S->>T: executeBash(npm test LoginForm)
    T-->>S: 8 tests passed
    S->>O: Task complete
```

---

## Real Scenario: Bugfix with Exploration Test

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant S as spec-task-execution
    participant FS as File System
    participant T as Test Runner
    
    Note over O,T: Task 1: Exploration Test
    
    O->>S: Execute Task 1
    S->>S: Read bug condition C(X)
    S->>FS: Create exploration test
    FS-->>S: Test created
    S->>T: Run test on buggy code
    
    alt Test Fails (Expected)
        T-->>S: Test FAILED
        S->>S: Bug confirmed!
        S->>O: Success - ready for Task 2
    else Test Passes (Unexpected)
        T-->>S: Test PASSED
        S->>S: Problem - bug not detected
        S->>User: Request decision
        User-->>S: "Continue" or "Re-investigate"
        alt Continue
            S->>O: Proceed to Task 2
        else Re-investigate
            S->>O: Stop execution
        end
    end
```

---

## Multi-File Implementation

```mermaid
flowchart TD
    A[Task: Implement Feature X] --> B[Identify Required Files]
    B --> C[File 1: Component]
    B --> D[File 2: Service]
    B --> E[File 3: Types]
    B --> F[File 4: Tests]
    
    C --> G[Create Component]
    D --> H[Create Service]
    E --> I[Create Types]
    
    G --> J[Link Component to Service]
    H --> J
    I --> J
    
    J --> F
    F --> K[Create All Tests]
    K --> L[Run Test Suite]
    L --> M{All Pass?}
    
    M -->|Yes| N[Complete]
    M -->|No| O[Fix Issues]
    O --> L
```
