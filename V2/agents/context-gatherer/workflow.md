# Context Gatherer Agent - Workflow Diagrams

## Main Analysis Flow

```mermaid
flowchart TD
    A[Receive Analysis Request] --> B[Parse Problem/Question]
    B --> C[Identify Analysis Type]
    C --> D{Type?}
    
    D -->|Bug Investigation| E[Bug Analysis Flow]
    D -->|Architecture Understanding| F[Architecture Flow]
    D -->|Dependency Analysis| G[Dependency Flow]
    D -->|Feature Planning| H[Planning Flow]
    
    E --> I[Synthesize Findings]
    F --> I
    G --> I
    H --> I
    
    I --> J[Structure Report]
    J --> K[Prioritize Information]
    K --> L[Generate Recommendations]
    L --> M[Return Analysis]
```

---

## Bug Investigation Flow

```mermaid
flowchart TD
    A[Bug Description] --> B[Extract Keywords]
    B --> C[Search for Error Messages]
    C --> D[grepSearch for symptoms]
    D --> E[Find Relevant Files]
    E --> F[Read Suspicious Files]
    F --> G[Trace Execution Path]
    G --> H[Identify Failure Points]
    H --> I[Map Related Components]
    I --> J[Analyze Dependencies]
    J --> K[Formulate Hypothesis]
    K --> L[Report Findings]
```

---

## Architecture Understanding Flow

```mermaid
flowchart TD
    A[Architecture Question] --> B[Explore Root Directory]
    B --> C[Read package.json]
    C --> D[Identify Framework]
    D --> E{Framework Type?}
    
    E -->|React| F[Find components/, App.jsx]
    E -->|Express| G[Find routes/, server.js]
    E -->|Vue| H[Find .vue files]
    E -->|Other| I[Identify patterns]
    
    F --> J[Map Component Structure]
    G --> K[Map Route Structure]
    H --> L[Map Vue Structure]
    I --> M[Map Generic Structure]
    
    J --> N[Analyze State Management]
    K --> N
    L --> N
    M --> N
    
    N --> O[Identify Data Flow]
    O --> P[Document Architecture]
```

---

## Dependency Analysis Flow

```mermaid
flowchart TD
    A[Target Symbol/File] --> B[Search for Imports]
    B --> C[grepSearch: import.*target]
    C --> D[Find All Importers]
    D --> E[Read Each Importer]
    E --> F[Identify Usage Patterns]
    F --> G[Count Usage Frequency]
    G --> H[Analyze Call Patterns]
    H --> I[Map Dependency Tree]
    I --> J[Identify Critical Paths]
    J --> K[Assess Impact]
    K --> L[Report Dependencies]
```

---

## Feature Planning Flow

```mermaid
flowchart TD
    A[New Feature Description] --> B[Identify Similar Existing Code]
    B --> C[Search for Related Patterns]
    C --> D[Analyze Current Structure]
    D --> E[Identify Integration Points]
    E --> F[Find Affected Components]
    F --> G[Assess Modification Needs]
    G --> H[Recommend File Locations]
    H --> I[Suggest Architecture]
    I --> J[Identify Risks]
    J --> K[Report Recommendations]
```

---

## Search Strategy Decision

```mermaid
flowchart TD
    A[Need to Find Code] --> B{What to Find?}
    
    B -->|File by Name| C[fileSearch]
    B -->|Code Pattern| D[grepSearch]
    B -->|Symbol/Function| E[readCode with selector]
    B -->|Imports| F[grepSearch: import.*]
    
    C --> G[Analyze Results]
    D --> G
    E --> G
    F --> G
    
    G --> H{Found Relevant?}
    H -->|Yes| I[Read Details]
    H -->|No| J[Refine Search]
    J --> B
    I --> K[Continue Analysis]
```

---

## Exploration Depth Strategy

```mermaid
flowchart TD
    A[Start Analysis] --> B{Project Size?}
    
    B -->|Small <50 files| C[Shallow Exploration]
    B -->|Medium 50-500| D[Targeted Exploration]
    B -->|Large >500| E[Focused Exploration]
    
    C --> F[List all directories]
    C --> G[Read key files]
    
    D --> H[Search for keywords]
    D --> I[Read matching files]
    
    E --> J[Identify entry points]
    E --> K[Trace from entry]
    
    F --> L[Comprehensive View]
    G --> L
    H --> M[Focused View]
    I --> M
    J --> N[Minimal View]
    K --> N
    
    L --> O[Report]
    M --> O
    N --> O
```

---

## File Relevance Scoring

```mermaid
flowchart TD
    A[Found File] --> B[Calculate Relevance Score]
    
    B --> C{Filename Match?}
    C -->|Yes| D[+10 points]
    C -->|No| E[+0 points]
    
    D --> F{Content Match?}
    E --> F
    F -->|High| G[+20 points]
    F -->|Medium| H[+10 points]
    F -->|Low| I[+5 points]
    F -->|None| J[+0 points]
    
    G --> K{Import Frequency?}
    H --> K
    I --> K
    J --> K
    
    K -->|High| L[+15 points]
    K -->|Medium| M[+10 points]
    K -->|Low| N[+5 points]
    
    L --> O[Total Score]
    M --> O
    N --> O
    
    O --> P{Score > 20?}
    P -->|Yes| Q[Include in Report]
    P -->|No| R[Exclude]
```

---

## Component Relationship Mapping

```mermaid
flowchart TD
    A[Identify Components] --> B[For Each Component]
    B --> C[Find Imports]
    C --> D[Find Exports]
    D --> E[Find Usage]
    E --> F[Build Relationship Graph]
    
    F --> G[Component A]
    F --> H[Component B]
    F --> I[Component C]
    
    G -->|imports| H
    H -->|imports| I
    G -->|uses| I
    
    I --> J[Identify Patterns]
    J --> K{Pattern Type?}
    K -->|Layered| L[Layer Diagram]
    K -->|Hub-Spoke| M[Hub Diagram]
    K -->|Pipeline| N[Flow Diagram]
    
    L --> O[Document Architecture]
    M --> O
    N --> O
```

---

## Analysis Prioritization

```mermaid
flowchart TD
    A[All Found Files] --> B[Score by Relevance]
    B --> C[Sort by Score]
    C --> D[Top 10 Files]
    D --> E[Read in Detail]
    E --> F[Extract Key Info]
    F --> G[Next 10 Files]
    G --> H{Need More Context?}
    H -->|Yes| I[Read Next Batch]
    H -->|No| J[Synthesize Findings]
    I --> F
    J --> K[Generate Report]
```

---

## Codebase Type Detection

```mermaid
flowchart TD
    A[Analyze Project] --> B[Read package.json]
    B --> C{Dependencies?}
    
    C -->|react| D[React Application]
    C -->|express| E[Express Backend]
    C -->|vue| F[Vue Application]
    C -->|@angular| G[Angular Application]
    C -->|next| H[Next.js Application]
    
    D --> I[Check for Redux/MobX]
    E --> J[Check for ORM]
    F --> K[Check for Vuex]
    G --> L[Check for NgRx]
    H --> M[Check for API routes]
    
    I --> N[Document Stack]
    J --> N
    K --> N
    L --> N
    M --> N
    
    N --> O[Adapt Analysis Strategy]
```

---

## Report Generation Flow

```mermaid
flowchart TD
    A[Analysis Complete] --> B[Organize Findings]
    B --> C[Group by Category]
    
    C --> D[Relevant Files Section]
    C --> E[Architecture Section]
    C --> F[Key Findings Section]
    C --> G[Recommendations Section]
    
    D --> H[Prioritize by Relevance]
    E --> I[Create Diagrams]
    F --> J[Highlight Important]
    G --> K[Order by Priority]
    
    H --> L[Format Report]
    I --> L
    J --> L
    K --> L
    
    L --> M[Add Context]
    M --> N[Add Examples]
    N --> O[Final Report]
```

---

## Interaction with Other Agents

```mermaid
sequenceDiagram
    participant C as Core Orchestrator
    participant CG as context-gatherer
    participant GTE as general-task-execution
    
    C->>CG: "Analyze authentication system"
    CG->>CG: Explore codebase
    CG->>CG: Find relevant files
    CG->>CG: Map architecture
    CG->>C: Return analysis
    
    C->>C: Review analysis
    C->>GTE: "Refactor auth based on analysis"
    GTE->>GTE: Use context from CG
    GTE->>GTE: Implement changes
    GTE->>C: Return results
    
    C->>User: Present results
```

---

## Efficiency Optimization

```mermaid
flowchart TD
    A[Start Analysis] --> B{Cache Available?}
    B -->|Yes| C[Use Cached Structure]
    B -->|No| D[Fresh Analysis]
    
    C --> E[Incremental Update]
    D --> F[Full Exploration]
    
    E --> G[Quick Results]
    F --> H[Complete Results]
    
    G --> I[Return Findings]
    H --> I
    
    I --> J[Cache Results]
    J --> K[Future Requests Faster]
```

---

## Analysis Patterns

### Pattern 1: Top-Down

```mermaid
flowchart TD
    A[Entry Point] --> B[Main Module]
    B --> C[Sub-Module 1]
    B --> D[Sub-Module 2]
    C --> E[Component 1]
    C --> F[Component 2]
    D --> G[Component 3]
    
    style A fill:#90EE90
    style B fill:#87CEEB
    style C fill:#DDA0DD
    style D fill:#DDA0DD
    style E fill:#FFB6C1
    style F fill:#FFB6C1
    style G fill:#FFB6C1
```

### Pattern 2: Bottom-Up

```mermaid
flowchart BT
    A[Target Component] --> B[Direct Users]
    B --> C[Indirect Users]
    C --> D[Top-Level Modules]
    D --> E[Entry Points]
    
    style A fill:#FFB6C1
    style B fill:#DDA0DD
    style C fill:#87CEEB
    style D fill:#90EE90
    style E fill:#FFD700
```

---

## Real-World Scenario: Performance Issue

```mermaid
sequenceDiagram
    participant U as User
    participant CG as context-gatherer
    participant FS as File System
    
    U->>CG: "Dashboard loads slowly"
    CG->>FS: fileSearch("dashboard")
    FS-->>CG: Dashboard.jsx found
    CG->>FS: readCode(Dashboard.jsx)
    FS-->>CG: Component code
    CG->>CG: Identify child components
    CG->>FS: grepSearch("useEffect")
    FS-->>CG: Data fetching locations
    CG->>FS: grepSearch("api\\.")
    FS-->>CG: API call locations
    CG->>CG: Analyze patterns
    CG->>CG: Identify bottlenecks
    CG->>U: Report with recommendations
```

---

## Analysis Output Structure

```mermaid
graph TD
    A[Analysis Result] --> B[Relevant Files]
    A --> C[Architecture Overview]
    A --> D[Key Findings]
    A --> E[Recommendations]
    
    B --> B1[File 1: Role & Details]
    B --> B2[File 2: Role & Details]
    B --> B3[File N: Role & Details]
    
    C --> C1[Component Diagram]
    C --> C2[Data Flow]
    C --> C3[Integration Points]
    
    D --> D1[Finding 1]
    D --> D2[Finding 2]
    D --> D3[Finding N]
    
    E --> E1[Action 1: Priority High]
    E --> E2[Action 2: Priority Medium]
    E --> E3[Action 3: Priority Low]
```
