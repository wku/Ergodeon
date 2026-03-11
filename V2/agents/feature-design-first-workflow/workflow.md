# Feature Design-First Workflow - Workflow Diagrams

## Overview

Агент для создания спецификаций новых функций, начиная с технического дизайна.

---

## Main Workflow

```mermaid
flowchart TD
    A[User: Create Feature Spec] --> B[Core: Feature or Bugfix?]
    B --> C[User: Feature]
    C --> D[Core: Requirements or Design?]
    D --> E[User: Technical Design]
    E --> F[Extract Feature Name]
    F --> G[Phase 1: Design]
    G --> H[Create design.md]
    H --> I[User Review]
    I -->|Approved| J[Phase 2: Requirements]
    I -->|Changes| G
    J --> K[Create requirements.md]
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
    participant DF as design-first
    participant FS as File System
    
    U->>C: "Implement microservices with event sourcing"
    C->>U: Feature or Bugfix?
    U->>C: Feature
    C->>U: Requirements or Design?
    U->>C: Technical Design
    
    C->>DF: preset="design"
    DF->>DF: Analyze technical approach
    DF->>DF: Generate design
    DF->>FS: Write design.md
    DF->>FS: Write .config.kiro
    DF->>U: Review design.md
    U->>DF: Approved
    
    DF->>C: Design complete
    C->>DF: preset="requirements"
    DF->>FS: Read design.md
    DF->>DF: Derive requirements
    DF->>FS: Write requirements.md
    DF->>U: Review requirements.md
    U->>DF: Approved
    
    DF->>C: Requirements complete
    C->>DF: preset="tasks"
    DF->>FS: Read design.md, requirements.md
    DF->>DF: Generate tasks
    DF->>FS: Write tasks.md
    DF->>C: Tasks complete
    C->>U: Ready for execution
```

---

## Design Phase (First)

```mermaid
flowchart TD
    A[Start Design] --> B[Analyze Technical Request]
    B --> C[Search Memory for Patterns]
    C --> D[Create High-Level Architecture]
    D --> E[Define Components]
    E --> F[Design Data Models]
    F --> G[Design APIs]
    G --> H[Add Low-Level Details]
    H --> I[Add Implementation Notes]
    I --> J[Write design.md]
    J --> K[Create .config.kiro]
    K --> L[Request User Review]
    L --> M{Approved?}
    M -->|Yes| N[Phase Complete]
    M -->|No| O[Gather Feedback]
    O --> D
```

---

## Requirements Phase (Second)

```mermaid
flowchart TD
    A[Start Requirements] --> B[Read design.md]
    B --> C[Analyze Technical Design]
    C --> D[Derive User Stories]
    D --> E[Extract Business Requirements]
    E --> F[Define Acceptance Criteria]
    F --> G[Define Correctness Properties]
    G --> H[Add Non-Functional Requirements]
    H --> I[Write requirements.md]
    I --> J[Request User Review]
    J --> K{Approved?}
    K -->|Yes| L[Phase Complete]
    K -->|No| M[Gather Feedback]
    M --> D
```

---

## Tasks Phase (Third)

```mermaid
flowchart TD
    A[Start Tasks] --> B[Read design.md]
    B --> C[Read requirements.md]
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

### design.md (Created First)

```mermaid
graph TB
    A[design.md] --> B[High-Level Design]
    A --> C[Architecture Diagrams]
    A --> D[Component Design]
    A --> E[Data Models]
    A --> F[API Design]
    A --> G[Low-Level Design]
    
    B --> B1[System Overview]
    B --> B2[Technology Stack]
    B --> B3[Design Patterns]
    
    C --> C1[Architecture Diagram]
    C --> C2[Component Diagram]
    C --> C3[Sequence Diagrams]
    
    D --> D1[Component 1]
    D --> D2[Component 2]
    
    E --> E1[Entities]
    E --> E2[Relationships]
    E --> E3[Schemas]
    
    F --> F1[Endpoints]
    F --> F2[Request/Response]
    
    G --> G1[Algorithms]
    G --> G2[Code Structure]
    G --> G3[Implementation Details]
```

### requirements.md (Derived from Design)

```mermaid
graph TB
    A[requirements.md] --> B[Feature Overview]
    A --> C[User Stories]
    A --> D[Acceptance Criteria]
    A --> E[Correctness Properties]
    A --> F[Non-Functional Requirements]
    
    C --> C1[Story 1: Derived from Design]
    C --> C2[Story 2: Derived from Design]
    
    D --> D1[Criterion 1]
    D --> D2[Criterion 2]
    
    E --> E1[Property 1]
    E --> E2[Property 2]
    
    F --> F1[Performance]
    F --> F2[Security]
    F --> F3[Accessibility]
```

---

## State Management

```mermaid
stateDiagram-v2
    [*] --> NotStarted
    NotStarted --> Design: Start
    Design --> DesignReview: Document Created
    DesignReview --> Design: Changes Requested
    DesignReview --> Requirements: Approved
    Requirements --> RequirementsReview: Document Created
    RequirementsReview --> Requirements: Changes Requested
    RequirementsReview --> Tasks: Approved
    Tasks --> Complete: Document Created
    Complete --> [*]
```

---

## Design-First vs Requirements-First

```mermaid
graph LR
    A[User Request] --> B{Approach?}
    
    B -->|Design-First| C[Technical Vision Clear]
    B -->|Requirements-First| D[Business Needs Clear]
    
    C --> E[Design → Requirements → Tasks]
    D --> F[Requirements → Design → Tasks]
    
    E --> G[Implementation]
    F --> G
```

---

## When to Use Design-First

```mermaid
flowchart TD
    A[Evaluate Request] --> B{Technical Approach Clear?}
    B -->|Yes| C{Business Requirements Unclear?}
    B -->|No| D[Use Requirements-First]
    
    C -->|Yes| E[Use Design-First]
    C -->|No| F{Refactoring/Migration?}
    
    F -->|Yes| E
    F -->|No| D
    
    E --> G[Start with Technical Design]
    D --> H[Start with Business Requirements]
```

---

## Requirements Derivation Process

```mermaid
flowchart TD
    A[Read design.md] --> B[Identify Components]
    B --> C[Extract User-Facing Features]
    C --> D[Convert to User Stories]
    D --> E[Define Acceptance Criteria]
    E --> F[Map to Design Elements]
    F --> G[Add Correctness Properties]
    G --> H[Write requirements.md]
```

---

## Error Handling

```mermaid
flowchart TD
    A[Error Detected] --> B{Error Type?}
    
    B -->|Invalid Design| C[Request Technical Clarification]
    B -->|Incomplete Design| D[Request Missing Details]
    B -->|Requirements Mismatch| E[Reconcile with Design]
    B -->|User Rejection| F[Gather Feedback]
    
    C --> G[Continue]
    D --> G
    E --> G
    F --> G
```

---

## Integration with Task Execution

```mermaid
sequenceDiagram
    participant DF as design-first
    participant C as Core
    participant STE as spec-task-execution
    
    DF->>C: Tasks created
    C->>C: User: "Run all tasks"
    
    loop For each task
        C->>STE: Execute task
        STE->>STE: Implement based on design
        STE->>STE: Test against requirements
        STE->>C: Task complete
    end
    
    C->>C: All tasks complete
```

---

## Key Features

1. **Design-Driven**: Начинает с технического решения
2. **Requirements Derivation**: Автоматически выводит требования из дизайна
3. **User Approval**: Требует подтверждения на каждом этапе
4. **Iterative**: Позволяет вносить изменения
5. **Consistency**: Обеспечивает согласованность дизайна и требований

---

## Usage Example

```
User: "Implement microservices architecture with event sourcing"

Workflow:
1. Core asks: Feature or Bugfix? → Feature
2. Core asks: Requirements or Design? → Technical Design
3. Extract feature_name: "microservices-event-sourcing"
4. Phase 1: Create design.md
   - Architecture diagrams
   - Component design
   - Event sourcing patterns
   - API design
5. User reviews and approves
6. Phase 2: Create requirements.md (derived from design)
   - User stories based on components
   - Acceptance criteria from design
   - Correctness properties
7. User reviews and approves
8. Phase 3: Create tasks.md
   - Implementation tasks
   - Testing tasks
9. Ready for execution
```

---

## Best Practices

1. **Clear Technical Vision**: Убедитесь, что технический подход понятен
2. **Complete Design**: Включайте все архитектурные детали
3. **Derive Requirements**: Выводите требования из дизайна, не изобретайте заново
4. **Consistency Check**: Проверяйте согласованность дизайна и требований
5. **User Validation**: Получайте подтверждение на каждом этапе

---

## Comparison with Requirements-First

| Aspect | Design-First | Requirements-First |
|--------|--------------|-------------------|
| Start Point | Technical design | Business requirements |
| Best For | Technical refactoring, migrations | New features, user-facing |
| First Document | design.md | requirements.md |
| Requirements | Derived from design | Drive the design |
| Use Case | Clear technical approach | Clear business needs |
