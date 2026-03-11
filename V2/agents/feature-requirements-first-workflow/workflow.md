# Feature Requirements-First Workflow - Workflow Diagrams

## Overview

Агент для создания спецификаций новых функций, начиная с требований.

---

## Main Workflow

```mermaid
flowchart TD
    A[User: Create Feature Spec] --> B[Core: Feature or Bugfix?]
    B --> C[User: Feature]
    C --> D[Core: Requirements or Design?]
    D --> E[User: Requirements]
    E --> F[Extract Feature Name]
    F --> G[Phase 1: Requirements]
    G --> H[Create requirements.md]
    H --> I[User Review]
    I -->|Approved| J[Phase 2: Design]
    I -->|Changes| G
    J --> K[Create design.md]
    K --> L[User Review]
    L -->|Approved| M[Phase 3: Tasks]
    L -->|Changes| J
    M --> N[Create tasks.md]
    N --> O[Ready for Execution]
```

---

## Phase Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant C as Core
    participant RF as requirements-first
    participant FS as File System
    
    U->>C: "Add user authentication"
    C->>U: Feature or Bugfix?
    U->>C: Feature
    C->>U: Requirements or Design?
    U->>C: Requirements
    
    C->>RF: preset="requirements"
    RF->>RF: Analyze request
    RF->>RF: Generate requirements
    RF->>FS: Write requirements.md
    RF->>FS: Write .config.kiro
    RF->>U: Review requirements.md
    U->>RF: Approved
    
    RF->>C: Requirements complete
    C->>RF: preset="design"
    RF->>FS: Read requirements.md
    RF->>RF: Generate design
    RF->>FS: Write design.md
    RF->>U: Review design.md
    U->>RF: Approved
    
    RF->>C: Design complete
    C->>RF: preset="tasks"
    RF->>FS: Read requirements.md, design.md
    RF->>RF: Generate tasks
    RF->>FS: Write tasks.md
    RF->>C: Tasks complete
    C->>U: Ready for execution
```

---

## Requirements Phase

```mermaid
flowchart TD
    A[Start Requirements] --> B[Analyze User Request]
    B --> C[Search Memory for Context]
    C --> D[Generate Requirements Structure]
    D --> E[Create User Stories]
    E --> F[Define Acceptance Criteria]
    F --> G[Define Correctness Properties]
    G --> H[Add Non-Functional Requirements]
    H --> I[Write requirements.md]
    I --> J[Create .config.kiro]
    J --> K[Request User Review]
    K --> L{Approved?}
    L -->|Yes| M[Phase Complete]
    L -->|No| N[Gather Feedback]
    N --> D
```

---

## Design Phase

```mermaid
flowchart TD
    A[Start Design] --> B[Read requirements.md]
    B --> C[Analyze Requirements]
    C --> D[Create High-Level Design]
    D --> E[Define Architecture]
    E --> F[Design Data Models]
    F --> G[Design APIs]
    G --> H[Create Low-Level Design]
    H --> I[Add Implementation Details]
    I --> J[Write design.md]
    J --> K[Request User Review]
    K --> L{Approved?}
    L -->|Yes| M[Phase Complete]
    L -->|No| N[Gather Feedback]
    N --> D
```

---

## Tasks Phase

```mermaid
flowchart TD
    A[Start Tasks] --> B[Read requirements.md]
    B --> C[Read design.md]
    C --> D[Analyze Both Documents]
    D --> E[Break Down into Tasks]
    E --> F[Create Task Hierarchy]
    F --> G[Add Sub-tasks]
    G --> H[Mark Required/Optional]
    H --> I[Add Task Details]
    I --> J[Write tasks.md]
    J --> K[Phase Complete]
```

---

## Document Structure

### requirements.md

```mermaid
graph TB
    A[requirements.md] --> B[Feature Overview]
    A --> C[User Stories]
    A --> D[Acceptance Criteria]
    A --> E[Correctness Properties]
    A --> F[Non-Functional Requirements]
    
    C --> C1[Story 1]
    C --> C2[Story 2]
    C --> C3[Story N]
    
    D --> D1[Criterion 1]
    D --> D2[Criterion 2]
    
    E --> E1[Property 1]
    E --> E2[Property 2]
    
    F --> F1[Performance]
    F --> F2[Security]
    F --> F3[Accessibility]
```

### design.md

```mermaid
graph TB
    A[design.md] --> B[High-Level Design]
    A --> C[Low-Level Design]
    A --> D[Data Models]
    A --> E[API Design]
    
    B --> B1[Architecture]
    B --> B2[Components]
    B --> B3[Diagrams]
    
    C --> C1[Algorithms]
    C --> C2[Code Structure]
    C --> C3[Implementation Details]
    
    D --> D1[Entities]
    D --> D2[Relationships]
    D --> D3[Schemas]
    
    E --> E1[Endpoints]
    E --> E2[Request/Response]
    E --> E3[Error Handling]
```

### tasks.md

```mermaid
graph TB
    A[tasks.md] --> B[Task 1]
    A --> C[Task 2]
    A --> D[Task N]
    
    B --> B1[Sub-task 1.1]
    B --> B2[Sub-task 1.2]
    
    C --> C1[Sub-task 2.1]
    
    style B fill:#90EE90
    style C fill:#90EE90
    style D fill:#FFB6C1
```

---

## State Management

```mermaid
stateDiagram-v2
    [*] --> NotStarted
    NotStarted --> Requirements: Start
    Requirements --> RequirementsReview: Document Created
    RequirementsReview --> Requirements: Changes Requested
    RequirementsReview --> Design: Approved
    Design --> DesignReview: Document Created
    DesignReview --> Design: Changes Requested
    DesignReview --> Tasks: Approved
    Tasks --> Complete: Document Created
    Complete --> [*]
```

---

## Error Handling

```mermaid
flowchart TD
    A[Error Detected] --> B{Error Type?}
    
    B -->|Invalid Input| C[Request Clarification]
    B -->|File Error| D[Retry File Operation]
    B -->|Generation Error| E[Regenerate Content]
    B -->|User Rejection| F[Gather Feedback]
    
    C --> G[Continue]
    D --> H{Success?}
    H -->|Yes| G
    H -->|No| I[Report Error]
    E --> G
    F --> G
```

---

## File System Operations

```mermaid
flowchart LR
    A[Agent] --> B[Create Directory]
    B --> C[.kiro/specs/feature-name/]
    
    C --> D[requirements.md]
    C --> E[design.md]
    C --> F[tasks.md]
    C --> G[.config.kiro]
    
    D --> H[User Review]
    E --> H
    F --> H
```

---

## Integration with Task Execution

```mermaid
sequenceDiagram
    participant RF as requirements-first
    participant C as Core
    participant STE as spec-task-execution
    
    RF->>C: Tasks created
    C->>C: User: "Run all tasks"
    
    loop For each task
        C->>STE: Execute task
        STE->>STE: Implement
        STE->>STE: Test
        STE->>C: Task complete
    end
    
    C->>C: All tasks complete
```

---

## Key Features

1. **Requirements-Driven**: Начинает с бизнес-требований
2. **User Approval**: Требует подтверждения на каждом этапе
3. **Iterative**: Позволяет вносить изменения
4. **Structured**: Создает четкую структуру документов
5. **Property-Based**: Включает correctness properties для тестирования

---

## Usage Example

```
User: "I want to add user authentication"

Workflow:
1. Core asks: Feature or Bugfix? → Feature
2. Core asks: Requirements or Design? → Requirements
3. Extract feature_name: "user-authentication"
4. Phase 1: Create requirements.md
   - User stories
   - Acceptance criteria
   - Correctness properties
5. User reviews and approves
6. Phase 2: Create design.md
   - Architecture
   - Data models
   - API design
7. User reviews and approves
8. Phase 3: Create tasks.md
   - Implementation tasks
   - Testing tasks
9. Ready for execution
```

---

## Best Practices

1. **Clear Requirements**: Убедитесь, что требования понятны
2. **User Involvement**: Получайте обратную связь на каждом этапе
3. **Completeness**: Включайте все необходимые детали
4. **Testability**: Определяйте correctness properties
5. **Maintainability**: Структурируйте документы для легкого обновления
