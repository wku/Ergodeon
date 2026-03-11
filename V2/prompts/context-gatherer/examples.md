# Context Gatherer Agent - Examples

## Example 1: New Developer Onboarding

### Input
```json
{
  "name": "context-gatherer",
  "prompt": "This is an e-commerce application. Explain the overall architecture: how components are organized, where business logic lives, how state management works, and where API integration happens.",
  "explanation": "Onboarding new developer - project architecture overview"
}
```

### Analysis Process
```
1. listDirectory(., depth=2) - Get structure
2. readFile(package.json) - Identify stack
3. readFile(README.md) - Project description
4. Identify patterns:
   - src/components/ - React components
   - src/services/ - Business logic
   - src/store/ - Redux state
   - src/api/ - API integration
5. readCode on key files from each area
6. Map relationships
```

### Output
```markdown
## E-Commerce Application Architecture

### Project Structure

```
src/
├── components/     # React UI components
├── services/       # Business logic layer
├── store/          # Redux state management
├── api/            # API client and endpoints
├── utils/          # Utility functions
└── hooks/          # Custom React hooks
```

### Technology Stack

- Frontend: React 18 with hooks
- State: Redux Toolkit
- Routing: React Router v6
- API: Axios with interceptors
- Styling: Tailwind CSS

### Key Components

1. **src/components/ProductList.jsx**
   - Displays products
   - Uses useProducts hook
   - Connects to Redux store

2. **src/services/productService.js**
   - Product business logic
   - Filtering, sorting
   - Price calculations

3. **src/store/productSlice.js**
   - Redux slice for products
   - Actions: fetchProducts, addToCart
   - Selectors for filtered products

4. **src/api/productApi.js**
   - API calls for products
   - GET /products, POST /products
   - Error handling

### Data Flow

```
Component → Hook → Service → API → Backend
    ↓
  Redux Store (state management)
```

### Recommendations

- Start with src/components/ for UI changes
- Modify src/services/ for business logic
- Update src/store/ for state changes
- Extend src/api/ for new endpoints
```

---

## Example 2: Bug Investigation - Form Not Submitting

### Input
```json
{
  "name": "context-gatherer",
  "prompt": "Users report registration form doesn't submit data to server. Need to understand which components and files handle registration form processing.",
  "explanation": "Investigating registration form submission bug"
}
```

### Analysis Process
```
1. fileSearch("registration") - Find form files
2. grepSearch("onSubmit|handleSubmit") - Find handlers
3. grepSearch("register|signup") - Find related code
4. readCode on found files
5. Trace submission flow
6. Identify API calls
```

### Output
```markdown
## Registration Form Submission Analysis

### Relevant Files

1. **src/components/RegistrationForm.jsx** (PRIMARY)
   - Form component
   - handleSubmit function at line 45
   - Calls authService.register()
   - Issue: Missing error handling

2. **src/services/authService.js** (CRITICAL)
   - register(userData) function at line 78
   - Makes POST to /api/auth/register
   - Issue: Axios call missing .catch()

3. **src/api/apiClient.js**
   - Axios instance configuration
   - Base URL: process.env.REACT_APP_API_URL
   - Issue: May be undefined in production

4. **src/store/authSlice.js**
   - Redux actions for registration
   - registerUser thunk
   - Not being dispatched from form

### Execution Flow

```
RegistrationForm.handleSubmit()
    ↓
authService.register(data)
    ↓
apiClient.post('/api/auth/register', data)
    ↓
[FAILS HERE - no error handling]
```

### Identified Issues

1. **Missing error handling** in authService.register()
2. **Environment variable** may be undefined
3. **Redux thunk** not being used
4. **No loading state** in form

### Recommendations

1. **Start here**: Add error handling in authService.js line 78
2. **Check**: Environment variables in production build
3. **Consider**: Using Redux thunk instead of direct service call
4. **Add**: Loading state and error display in form

### Potential Root Causes

- Network error not caught → silent failure
- API URL misconfigured → request goes nowhere
- CORS issue → request blocked
```

---

## Example 3: Performance Issue Investigation

### Input
```json
{
  "name": "context-gatherer",
  "prompt": "Dashboard page loads slowly. Find components that render on dashboard, what API requests are made, and where performance bottleneck might be.",
  "explanation": "Identifying components for dashboard performance analysis"
}
```

### Analysis Process
```
1. fileSearch("dashboard") - Find dashboard files
2. readCode(Dashboard component) - Understand structure
3. grepSearch("useEffect|componentDidMount") - Find data fetching
4. grepSearch("api\\.|axios\\.") - Find API calls
5. Identify rendering patterns
6. Count re-renders potential
```

### Output
```markdown
## Dashboard Performance Analysis

### Dashboard Components

1. **src/pages/Dashboard.jsx** (MAIN)
   - Renders 6 child components
   - Makes 4 API calls in useEffect
   - No memoization

2. **src/components/StatisticsWidget.jsx**
   - Fetches data independently
   - Re-renders on every parent update
   - Heavy calculations in render

3. **src/components/RecentOrders.jsx**
   - Polls API every 5 seconds
   - No pagination (loads all orders)
   - Large data rendering

4. **src/components/UserActivity.jsx**
   - Real-time updates via WebSocket
   - No throttling
   - Causes frequent re-renders

### API Calls on Load

1. GET /api/statistics - 2.3s response time
2. GET /api/orders?limit=100 - 1.8s response time
3. GET /api/users/activity - 0.5s response time
4. GET /api/notifications - 0.3s response time

**Total: ~5 seconds of sequential API calls**

### Performance Bottlenecks

1. **Sequential API calls** - Should be parallel
2. **No memoization** - Components re-render unnecessarily
3. **Large data sets** - RecentOrders loads 100+ items
4. **Frequent polling** - Every 5 seconds
5. **Heavy calculations** - StatisticsWidget calculates in render

### Recommendations

1. **Immediate**: Parallelize API calls with Promise.all
2. **High impact**: Add React.memo to child components
3. **Medium impact**: Implement pagination for RecentOrders
4. **Optimization**: Move calculations to useMemo
5. **Consider**: Increase polling interval to 30 seconds

### Expected Improvements

- Parallel API calls: 5s → 2.3s (57% faster)
- Memoization: Reduce re-renders by ~70%
- Pagination: Reduce data transfer by 80%
```

---

## Example 4: Adding New Feature - Where to Start

### Input
```json
{
  "name": "context-gatherer",
  "prompt": "Want to add shopping cart functionality. Where should this be implemented? What existing code will be affected?",
  "explanation": "Planning shopping cart feature implementation"
}
```

### Analysis Process
```
1. Search for existing cart code: grepSearch("cart")
2. Identify state management: readFile(src/store/)
3. Find product components: fileSearch("product")
4. Check API structure: readCode(src/api/)
5. Identify integration points
```

### Output
```markdown
## Shopping Cart Implementation Analysis

### Current State

No existing cart implementation found.

### Recommended Structure

**New files to create**:
```
src/
├── components/
│   ├── Cart.jsx (cart UI)
│   ├── CartItem.jsx (cart item)
│   └── AddToCartButton.jsx (add button)
├── store/
│   └── cartSlice.js (Redux slice)
├── services/
│   └── cartService.js (business logic)
└── api/
    └── cartApi.js (API calls)
```

### Integration Points

1. **ProductList.jsx** - Add "Add to Cart" buttons
2. **Header.jsx** - Add cart icon with item count
3. **Checkout.jsx** - Read cart data for checkout
4. **Redux store** - Add cartSlice to store config

### Existing Code to Modify

1. **src/store/index.js**
   - Import and add cartSlice reducer

2. **src/components/Header.jsx**
   - Add cart icon
   - Display item count from Redux

3. **src/components/ProductCard.jsx**
   - Add AddToCartButton component

4. **src/api/apiClient.js**
   - May need cart endpoints

### Data Model

```javascript
Cart State:
{
  items: [
    { productId, quantity, price, name }
  ],
  total: number,
  itemCount: number
}
```

### Recommendations

1. **Start**: Create cartSlice.js with Redux logic
2. **Then**: Create Cart.jsx component
3. **Then**: Add AddToCartButton to products
4. **Finally**: Integrate with checkout

### Considerations

- Persist cart to localStorage
- Handle quantity updates
- Calculate totals correctly
- Handle out-of-stock items
```

---

## Example 5: Dependency Impact Analysis

### Input
```json
{
  "name": "context-gatherer",
  "prompt": "Planning to refactor calculateDiscount function. Find all places where it's used and how it interacts with pricing system.",
  "explanation": "Impact analysis before refactoring discount calculation"
}
```

### Analysis Process
```
1. grepSearch("calculateDiscount") - Find all usages
2. readCode on files that use it
3. Identify call patterns
4. Check for variations
5. Map to pricing flow
```

### Output
```markdown
## calculateDiscount Impact Analysis

### Usage Statistics

- **Total usages**: 23 across 7 files
- **Most frequent**: src/services/pricingService.js (12 calls)
- **Critical paths**: Checkout flow, Cart display, Product page

### Files Using calculateDiscount

1. **src/services/pricingService.js** (12 calls)
   - calculateFinalPrice() - applies discount
   - calculateBulkDiscount() - volume discounts
   - applyPromoCode() - promo code discounts

2. **src/components/Cart.jsx** (5 calls)
   - Displays discounted prices
   - Shows savings amount

3. **src/components/ProductCard.jsx** (3 calls)
   - Shows sale price
   - Displays discount badge

4. **src/api/orderApi.js** (2 calls)
   - Validates discount before order
   - Sends discounted total to backend

5. **src/utils/priceFormatter.js** (1 call)
   - Formats discounted prices

### Call Patterns

**Pattern 1: Single discount**
```javascript
const discounted = calculateDiscount(price, discountPercent);
```

**Pattern 2: Multiple discounts**
```javascript
let price = basePrice;
price = calculateDiscount(price, memberDiscount);
price = calculateDiscount(price, promoDiscount);
```

**Pattern 3: Conditional discount**
```javascript
const final = hasDiscount ? calculateDiscount(price, percent) : price;
```

### Integration with Pricing System

```
Product Price
    ↓
calculateDiscount (member discount)
    ↓
calculateDiscount (promo code)
    ↓
calculateDiscount (bulk discount)
    ↓
Final Price
```

### Refactoring Recommendations

1. **Maintain signature** - Too many dependents
2. **Add new function** - calculateMultipleDiscounts()
3. **Deprecate gradually** - Add warnings
4. **Test thoroughly** - Critical for revenue

### Test Coverage Needed

- Single discount scenarios
- Multiple discount combinations
- Edge cases: 0%, 100%, negative
- Rounding behavior
- Currency handling

### Risk Level: HIGH

- Affects pricing (revenue impact)
- 23 call sites to verify
- Complex discount combinations
- Requires extensive testing
```
