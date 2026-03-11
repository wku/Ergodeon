# Custom Agent Creator - Workflow Diagrams

## Overview

Агент для создания новых пользовательских агентов в системе Kiro.

---

## Main Workflow

```mermaid
flowchart TD
    A[User Request: Create Agent] --> B[Parse Agent Requirements]
    B --> C{Validate Requirements}
    C -->|Invalid| D[Request Clarification]
    D --> B
    C -->|Valid| E[Generate Agent Structure]
    E --> F[Create Agent Files]
    F --> G[Generate Prompt]
    G --> H[Generate Config]
    H --> I[Create Documentation]
    I --> J[Validate Agent]
    J -->|Failed| K[Report Errors]
    J -->|Success| L[Register Agent]
    L --> M[Return Success]
```

---

## Agent Creation Process

```mermaid
sequenceDiagram
    participant U as User
    participant CAC as custom-agent-creator
    participant FS as File System
    participant V as Validator
    
    U->>CAC: "Create agent for X"
    CAC->>CAC: Parse requirements
    CAC->>U: Confirm agent details?
    U->>CAC: Confirmed
    
    CAC->>FS: Create agent directory
    CAC->>FS: Write config.json
    CAC->>FS: Write prompt.md
    CAC->>FS: Write rules.md
    CAC->>FS: Write examples.md
    CAC->>FS: Write README.md
    
    CAC->>V: Validate agent structure
    V->>CAC: Validation result
    
    alt Validation Success
        CAC->>U: Agent created successfully
    else Validation Failed
        CAC->>U: Errors found, fix needed
    end
```

---

## File Generation Flow

```mermaid
flowchart LR
    A[Agent Requirements] --> B[Generate Config]
    A --> C[Generate Prompt]
    A --> D[Generate Rules]
    A --> E[Generate Examples]
    A --> F[Generate README]
    
    B --> G[config.json]
    C --> H[prompt.md]
    D --> I[rules.md]
    E --> J[examples.md]
    F --> K[README.md]
    
    G --> L[Validate Structure]
    H --> L
    I --> L
    J --> L
    K --> L
    
    L --> M{Valid?}
    M -->|Yes| N[Agent Ready]
    M -->|No| O[Report Issues]
```

---

## Agent Configuration Structure

```mermaid
graph TB
    A[Agent Config] --> B[Identity]
    A --> C[Capabilities]
    A --> D[Tools]
    A --> E[Rules]
    A --> F[Examples]
    
    B --> B1[Name]
    B --> B2[Description]
    B --> B3[Version]
    
    C --> C1[Input Format]
    C --> C2[Output Format]
    C --> C3[Execution Process]
    
    D --> D1[Allowed Tools]
    D --> D2[Tool Permissions]
    
    E --> E1[Critical Rules]
    E --> E2[Interaction Rules]
    E --> E3[Delegation Rules]
    
    F --> F1[Usage Examples]
    F --> F2[Integration Examples]
```

---

## Validation Process

```mermaid
flowchart TD
    A[Start Validation] --> B{Config Valid?}
    B -->|No| C[Report Config Errors]
    B -->|Yes| D{Prompt Valid?}
    D -->|No| E[Report Prompt Errors]
    D -->|Yes| F{Rules Valid?}
    F -->|No| G[Report Rules Errors]
    F -->|Yes| H{Examples Valid?}
    H -->|No| I[Report Example Errors]
    H -->|Yes| J{README Valid?}
    J -->|No| K[Report README Errors]
    J -->|Yes| L[All Valid]
    
    C --> M[Validation Failed]
    E --> M
    G --> M
    I --> M
    K --> M
    L --> N[Validation Passed]
```

---

## Agent Registration Flow

```mermaid
sequenceDiagram
    participant CAC as custom-agent-creator
    participant FS as File System
    participant Reg as Agent Registry
    participant Orch as Orchestrator
    
    CAC->>FS: Read agent config
    FS->>CAC: Config data
    
    CAC->>Reg: Register agent
    Reg->>Reg: Validate config
    Reg->>Reg: Add to registry
    
    Reg->>Orch: Notify new agent
    Orch->>Orch: Update routing table
    
    Orch->>CAC: Registration complete
    CAC->>CAC: Return success
```

---

## Error Handling

```mermaid
flowchart TD
    A[Error Detected] --> B{Error Type?}
    
    B -->|Invalid Config| C[Show Config Errors]
    B -->|Missing Files| D[List Missing Files]
    B -->|Invalid Syntax| E[Show Syntax Errors]
    B -->|Permission Error| F[Show Permission Issues]
    
    C --> G[Provide Fix Suggestions]
    D --> G
    E --> G
    F --> G
    
    G --> H[User Fixes]
    H --> I[Re-validate]
    I --> J{Fixed?}
    J -->|Yes| K[Continue]
    J -->|No| A
```

---

## Agent Template Structure

```
.kiro/agents/{agent-name}/
├── config.json          # Agent configuration
├── prompt.md            # System prompt
├── rules.md             # Detailed rules
├── examples.md          # Usage examples
└── README.md            # Documentation
```

---

## Key Features

1. **Automated Generation**: Создает все необходимые файлы автоматически
2. **Validation**: Проверяет корректность структуры агента
3. **Templates**: Использует шаблоны для генерации
4. **Documentation**: Автоматически создает документацию
5. **Registration**: Регистрирует агента в системе

---

## Usage Example

```
User: "Create an agent that analyzes code complexity"

Agent:
1. Parses requirement
2. Generates agent structure:
   - Name: code-complexity-analyzer
   - Tools: readFile, readCode, grepSearch
   - Capabilities: AST analysis, metrics calculation
3. Creates all files
4. Validates structure
5. Registers agent
6. Returns success
```

---

## Integration Points

### Input
- Agent requirements (name, purpose, capabilities)
- Tool requirements
- Example use cases

### Output
- Complete agent directory structure
- All configuration files
- Documentation
- Registration confirmation

### Dependencies
- File system access
- Template engine
- Validator
- Agent registry
