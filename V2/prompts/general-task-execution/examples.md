# General Task Execution Agent - Examples

## Example 1: Create React Component

### Input
```json
{
  "name": "general-task-execution",
  "prompt": "Create a Button component in src/components/Button.jsx. Props: label (string), onClick (function), disabled (boolean), variant ('primary' | 'secondary'). Use styled-components for styling. Add PropTypes.",
  "explanation": "Creating reusable Button component"
}
```

### Execution Steps
```
1. fsWrite(src/components/Button.jsx) - Create component
2. getDiagnostics(src/components/Button.jsx) - Check for errors
3. (if needed) Fix any issues
```

### Output
```
Created src/components/Button.jsx:
- Button component with all required props
- Styled with styled-components
- PropTypes validation included
- Ready to use
```

---

## Example 2: Add API Endpoint

### Input
```json
{
  "name": "general-task-execution",
  "prompt": "Add POST /api/users endpoint in src/routes/users.js. Endpoint should create new user, validate email and password, hash password with bcrypt, save to database. Add error handling.",
  "explanation": "Adding user creation endpoint"
}
```

### Execution Steps
```
1. readCode(src/routes/users.js) - Understand current structure
2. editCode - Add new route handler
3. Check dependencies: bcrypt installed?
4. If not: executeBash(npm install bcrypt)
5. getDiagnostics - Validate code
6. Create test: fsWrite(src/routes/__tests__/users.test.js)
7. executeBash(npm test) - Run tests
```

### Output
```
Added POST /api/users endpoint:
- Input validation
- Password hashing with bcrypt
- Database integration
- Error handling
- Unit tests created and passing
```

---

## Example 3: Refactor to TypeScript

### Input
```json
{
  "name": "general-task-execution",
  "prompt": "Convert src/utils/helpers.js to TypeScript. Add proper types for all functions, create interfaces for complex objects, ensure strict type checking.",
  "explanation": "Migrating utility file to TypeScript"
}
```

### Execution Steps
```
1. readFile(src/utils/helpers.js) - Read current code
2. smartRelocate(src/utils/helpers.js → src/utils/helpers.ts)
3. editCode - Add TypeScript types
4. Create: fsWrite(src/types/helpers.d.ts) if needed
5. getDiagnostics(src/utils/helpers.ts) - Check types
6. Fix type errors if any
7. Update imports in dependent files (automatic via smartRelocate)
```

### Output
```
Converted to TypeScript:
- src/utils/helpers.ts created
- All functions typed
- Interfaces defined
- No type errors
- Imports updated automatically
```

---

## Example 4: Setup Testing Framework

### Input
```json
{
  "name": "general-task-execution",
  "prompt": "Set up Vitest for this project. Install dependencies, create vitest.config.js, add test script to package.json, create example test file.",
  "explanation": "Setting up Vitest testing framework"
}
```

### Execution Steps
```
1. readFile(package.json) - Check current setup
2. executeBash(npm install --save-dev vitest @vitest/ui)
3. fsWrite(vitest.config.js) - Create config
4. editCode(package.json) - Add test script
5. fsWrite(src/example.test.js) - Create example test
6. executeBash(npm test) - Verify setup
```

### Output
```
Vitest configured:
- Dependencies installed
- vitest.config.js created
- npm test script added
- Example test created and passing
```

---

## Example 5: Fix Linting Errors

### Input
```json
{
  "name": "general-task-execution",
  "prompt": "Fix all ESLint errors in src/components/ directory. Focus on unused variables, missing PropTypes, and console.log statements.",
  "explanation": "Cleaning up linting errors in components"
}
```

### Execution Steps
```
1. executeBash(npm run lint src/components/) - Get errors
2. Parse error output
3. For each file with errors:
   a. readCode(file)
   b. editCode to fix issues
   c. getDiagnostics(file)
4. executeBash(npm run lint src/components/) - Verify all fixed
```

### Output
```
Fixed ESLint errors in 5 files:
- Removed unused variables
- Added missing PropTypes
- Removed console.log statements
- All files now pass linting
```

---

## Example 6: Create API Client

### Input
```json
{
  "name": "general-task-execution",
  "prompt": "Create API client in src/api/client.js using axios. Include methods: get, post, put, delete. Add interceptors for auth token. Add error handling with retry logic.",
  "explanation": "Creating centralized API client"
}
```

### Execution Steps
```
1. Check: Is axios installed?
2. If not: executeBash(npm install axios)
3. fsWrite(src/api/client.js) - First 50 lines
4. fsAppend(src/api/client.js) - Remaining code
5. getDiagnostics(src/api/client.js)
6. fsWrite(src/api/__tests__/client.test.js) - Tests
7. executeBash(npm test) - Run tests
```

### Output
```
Created src/api/client.js:
- Axios-based client
- Auth interceptors
- Error handling with retry
- Comprehensive tests
```

---

## Example 7: Database Migration

### Input
```json
{
  "name": "general-task-execution",
  "prompt": "Create database migration to add 'email_verified' boolean column to users table. Use Knex.js migration format. Include up and down migrations.",
  "explanation": "Adding email verification column to users table"
}
```

### Execution Steps
```
1. Check: Knex installed and configured?
2. executeBash(npx knex migrate:make add_email_verified_to_users)
3. Find created migration file: fileSearch
4. editCode - Add up/down migrations
5. getDiagnostics - Validate
```

### Output
```
Created migration:
- migrations/20260310_add_email_verified_to_users.js
- up: adds email_verified column (default false)
- down: removes column
- Ready to run with knex migrate:latest
```

---

## Example 8: Performance Optimization

### Input
```json
{
  "name": "general-task-execution",
  "prompt": "Optimize src/utils/dataProcessor.js. Function processLargeDataset is slow. Add memoization, use efficient algorithms, create benchmark tests.",
  "explanation": "Optimizing slow data processing function"
}
```

### Execution Steps
```
1. readCode(src/utils/dataProcessor.js)
2. Analyze algorithm complexity
3. editCode - Apply optimizations:
   - Add memoization
   - Improve algorithm
   - Reduce iterations
4. fsWrite(src/utils/__benchmarks__/dataProcessor.bench.js)
5. executeBash(npm run benchmark)
6. Compare before/after performance
```

### Output
```
Optimized processLargeDataset:
- Added memoization for repeated calls
- Improved algorithm from O(n²) to O(n log n)
- Benchmark shows 10x speed improvement
- Benchmark tests created
```

---

## Example 9: Add Logging

### Input
```json
{
  "name": "general-task-execution",
  "prompt": "Add logging to src/services/paymentService.js. Use winston logger. Log all payment attempts, successes, and failures with appropriate levels. Don't log sensitive data.",
  "explanation": "Adding structured logging to payment service"
}
```

### Execution Steps
```
1. Check winston: readFile(package.json)
2. If not installed: executeBash(npm install winston)
3. fsWrite(src/config/logger.js) - Logger config
4. readCode(src/services/paymentService.js)
5. editCode - Add logging statements
6. Ensure no PII in logs
7. getDiagnostics
```

### Output
```
Added logging to paymentService:
- Winston logger configured
- Logs payment attempts (info level)
- Logs failures (error level)
- Logs successes (info level)
- No sensitive data logged
```

---

## Example 10: Create Docker Configuration

### Input
```json
{
  "name": "general-task-execution",
  "prompt": "Create Dockerfile for Node.js app. Multi-stage build, production optimized. Also create docker-compose.yml with app, postgres, and redis services.",
  "explanation": "Containerizing application with Docker"
}
```

### Execution Steps
```
1. fsWrite(Dockerfile) - Multi-stage build
2. fsWrite(docker-compose.yml) - Services config
3. fsWrite(.dockerignore) - Ignore patterns
4. Validate syntax
5. Create: fsWrite(README-docker.md) - Usage instructions
```

### Output
```
Docker configuration created:
- Dockerfile (multi-stage, optimized)
- docker-compose.yml (app + postgres + redis)
- .dockerignore
- README-docker.md with instructions
```

---

## Common Patterns

### Pattern: Add Feature to Existing Code

```
1. readCode - Understand current structure
2. editCode - Add new functionality
3. Update tests - Add test cases
4. Run tests - Verify
5. getDiagnostics - Final check
```

### Pattern: Fix Code Issue

```
1. getDiagnostics - Identify issue
2. readCode - Understand context
3. editCode - Apply fix
4. getDiagnostics - Verify fixed
5. Run tests - Ensure no regression
```

### Pattern: Create Module with Tests

```
1. fsWrite - Create main file
2. fsWrite - Create test file
3. executeBash(npm test) - Run tests
4. If fail: Fix and retry
5. getDiagnostics - Final validation
```
