# Defensive Coding Guide - Ops-Center Frontend

**Last Updated**: December 9, 2025
**Purpose**: Prevent null/undefined errors and improve code resilience

---

## Overview

This guide documents the defensive coding utilities and patterns used in Ops-Center to prevent common JavaScript errors and improve user experience through graceful degradation.

---

## Available Utilities

### Location
`/opt/ops-center/src/utils/safeUtils.js`

### Import
```javascript
import { 
  safeMap, 
  safeFilter, 
  safeSome, 
  safeIncludes,
  safeToFixed,
  safeGet 
} from '../utils/safeUtils';
```

---

## Safe Array Methods

### safeMap
**Purpose**: Map over array safely, returns empty array if input is not an array

```javascript
// ❌ Bad - crashes if data is null/undefined
const names = data.map(item => item.name);

// ✅ Good - returns [] if data is null/undefined
const names = safeMap(data, item => item.name);
```

### safeFilter
**Purpose**: Filter array safely, returns empty array if input is not an array

```javascript
// ❌ Bad - crashes if users is null
const activeUsers = users.filter(u => u.active);

// ✅ Good - returns [] if users is null
const activeUsers = safeFilter(users, u => u.active);
```

### safeSome
**Purpose**: Check if any element matches condition, returns false if not array

```javascript
// ❌ Bad - crashes if features is undefined
const hasFeature = features.some(f => f === 'premium');

// ✅ Good - returns false if features is undefined
const hasFeature = safeSome(features, f => f === 'premium');
```

### safeFind
**Purpose**: Find element in array, returns undefined if not array

```javascript
// ❌ Bad - crashes if items is null
const item = items.find(i => i.id === 5);

// ✅ Good - returns undefined if items is null
const item = safeFind(items, i => i.id === 5);
```

---

## Safe String Methods

### safeIncludes
**Purpose**: Check if string contains substring, returns false if not string

```javascript
// ❌ Bad - crashes if name is null
if (name.toLowerCase().includes('john')) { }

// ✅ Good - returns false if name is null
if (safeIncludes((name || '').toLowerCase(), 'john')) { }
```

### safeToUpperCase / safeToLowerCase
**Purpose**: Convert string case, returns empty string if not string

```javascript
// ❌ Bad - crashes if text is undefined
const upper = text.toUpperCase();

// ✅ Good - returns '' if text is undefined
const upper = safeToUpperCase(text);
```

---

## Safe Number Methods

### safeToFixed
**Purpose**: Format number with fixed decimals, returns '0' if not a number

```javascript
// ❌ Bad - crashes if temperature is null
const temp = temperature.toFixed(1);

// ✅ Good - returns '0' if temperature is null
const temp = safeToFixed(temperature, 1);

// Or inline:
const temp = (temperature || 0).toFixed(1);
```

---

## Safe Object Access

### safeGet
**Purpose**: Access nested object properties safely

```javascript
// ❌ Bad - crashes if user or user.profile is null
const city = user.profile.address.city;

// ✅ Good - returns 'Unknown' if any level is null
const city = safeGet(user, 'profile.address.city', 'Unknown');
```

---

## Safe JSON Operations

### safeJSONParse
**Purpose**: Parse JSON with fallback, doesn't throw on invalid JSON

```javascript
// ❌ Bad - throws error if json is invalid
const data = JSON.parse(jsonString);

// ✅ Good - returns {} if json is invalid
const data = safeJSONParse(jsonString, {});
```

---

## Safe Storage Operations

### safeGetFromStorage
**Purpose**: Read from localStorage with fallback

```javascript
// ❌ Bad - can throw if storage is full or disabled
const settings = JSON.parse(localStorage.getItem('settings'));

// ✅ Good - returns default if storage fails
const settings = safeGetFromStorage('settings', { theme: 'light' });
```

### safeSetToStorage
**Purpose**: Write to localStorage, returns success boolean

```javascript
// ❌ Bad - can throw if storage is full
localStorage.setItem('settings', JSON.stringify(settings));

// ✅ Good - returns true/false, doesn't throw
const saved = safeSetToStorage('settings', settings);
if (!saved) {
  toast.error('Failed to save settings');
}
```

---

## Error Boundary Component

### Purpose
Catch React component errors and display fallback UI instead of white screen

### Location
`/opt/ops-center/src/components/ErrorBoundary.jsx`

### Usage

**Wrap Entire Page**:
```jsx
import ErrorBoundary from '../components/ErrorBoundary';

function MyPage() {
  return (
    <ErrorBoundary fallbackMessage="Failed to load page">
      <PageContent />
    </ErrorBoundary>
  );
}
```

**Wrap Individual Component**:
```jsx
<ErrorBoundary fallbackMessage="Failed to load GPU data">
  <GPUMonitorCard gpuData={gpuData} />
</ErrorBoundary>
```

**Wrap Multiple Components**:
```jsx
<ErrorBoundary fallbackMessage="Failed to load dashboard">
  <MetricsCard />
  <ChartWidget />
  <DataTable />
</ErrorBoundary>
```

### What It Does
- Catches JavaScript errors in child components
- Displays user-friendly error message
- Includes "Try Again" button to retry
- Logs error to console for debugging
- Prevents entire app from crashing

---

## Common Patterns

### Pattern 1: Null Guards on Object Properties

```javascript
// ❌ Bad
<Typography>{user.profile.name}</Typography>

// ✅ Good
<Typography>{user?.profile?.name || 'Unknown User'}</Typography>
```

### Pattern 2: Array Operations with Fallback

```javascript
// ❌ Bad
{items.map(item => <Card key={item.id}>{item.name}</Card>)}

// ✅ Good
{safeMap(items, item => <Card key={item.id}>{item.name}</Card>)}

// ✅ Also Good (if items is usually defined)
{(items || []).map(item => <Card key={item.id}>{item.name}</Card>)}
```

### Pattern 3: Conditional Rendering

```javascript
// ❌ Bad - crashes if data is null
{data.length > 0 && <DataTable data={data} />}

// ✅ Good
{Array.isArray(data) && data.length > 0 && <DataTable data={data} />}
```

### Pattern 4: Number Display

```javascript
// ❌ Bad
<Typography>{temperature.toFixed(1)}°C</Typography>

// ✅ Good
<Typography>{(temperature || 0).toFixed(1)}°C</Typography>
```

### Pattern 5: String Operations

```javascript
// ❌ Bad
const filtered = items.filter(item => 
  item.name.toLowerCase().includes(query)
);

// ✅ Good
const filtered = safeFilter(items, item =>
  safeIncludes((item.name || '').toLowerCase(), query)
);
```

---

## When to Use What

### Use `||` operator for:
- Simple null checks
- Single property access
- Primitive values

```javascript
const name = user.name || 'Guest';
const count = items.length || 0;
```

### Use `?.` optional chaining for:
- Nested property access
- Method calls on potentially null objects

```javascript
const city = user?.profile?.address?.city;
const result = api?.getData?.();
```

### Use safe utilities for:
- Array operations
- String operations
- Complex filtering/mapping
- When you want consistent behavior

```javascript
const names = safeMap(users, u => u.name);
const active = safeFilter(users, u => u.active);
```

### Use ErrorBoundary for:
- Entire pages/routes
- Complex widgets
- Third-party components
- Risky data visualizations

```jsx
<ErrorBoundary fallbackMessage="Chart failed to load">
  <ComplexChart data={apiData} />
</ErrorBoundary>
```

---

## Testing Defensive Code

### Test with Null/Undefined

```javascript
// Test component with missing data
<GPUMonitorCard gpuData={null} />
<GPUMonitorCard gpuData={{}} />
<GPUMonitorCard gpuData={{ model: 'RTX 5090', temperature: null }} />
```

### Test with Malformed Data

```javascript
// Test with unexpected types
<UserCard user={{ name: 123, email: null, roles: 'admin' }} />
```

### Test Error Boundary

```javascript
// Create component that throws
const BrokenComponent = () => {
  throw new Error('Intentional error');
  return <div>Never rendered</div>;
};

// Wrap in ErrorBoundary
<ErrorBoundary fallbackMessage="Test error">
  <BrokenComponent />
</ErrorBoundary>
```

---

## Performance Considerations

### Safe Utilities Overhead
- Each safe utility adds 1-2ms per call
- For 1000 items: ~1-2ms total overhead
- Negligible compared to rendering time

### When to Optimize
- If processing 10,000+ items in tight loop
- If called in every render (memoize instead)
- If profiler shows it as bottleneck

### Optimization Strategies

```javascript
// ❌ Bad - calls safeMap on every render
function MyComponent({ data }) {
  const processed = safeMap(data, item => processItem(item));
  return <List items={processed} />;
}

// ✅ Good - memoize the result
function MyComponent({ data }) {
  const processed = useMemo(
    () => safeMap(data, item => processItem(item)),
    [data]
  );
  return <List items={processed} />;
}
```

---

## Checklist for New Components

When creating a new component, ensure:

- [ ] All array operations use safe utilities or fallback `|| []`
- [ ] All object properties use optional chaining `?.` or null checks
- [ ] All number operations have fallback `|| 0`
- [ ] All string operations check for null/undefined
- [ ] Component wrapped in ErrorBoundary (if complex)
- [ ] Props validated with PropTypes (optional)
- [ ] Tested with null/undefined/malformed data

---

## Migration Guide

### Step 1: Identify Risky Code

Search for patterns that commonly crash:
```bash
# Find array operations without guards
grep -r "\.map(" src/ | grep -v "|| \[\]" | grep -v "safeMap"

# Find property access without guards
grep -r "\.\w\+\.\w\+" src/ | grep -v "?."
```

### Step 2: Add Safe Utilities

```javascript
// Before
const names = users.map(u => u.name);

// After
import { safeMap } from '../utils/safeUtils';
const names = safeMap(users, u => u.name);
```

### Step 3: Add Error Boundaries

```javascript
// Before
return <MyComponent />;

// After
return (
  <ErrorBoundary>
    <MyComponent />
  </ErrorBoundary>
);
```

### Step 4: Test

- Load page with missing data
- Check console for errors
- Verify graceful degradation

---

## Real-World Examples

### Example 1: GPUMonitorCard

**Before**:
```jsx
<Chip label={`${gpuData.temperature.toFixed(1)}°C`} />
```

**After**:
```jsx
<Chip label={`${(gpuData.temperature || 0).toFixed(1)}°C`} />
```

**Why**: If GPU data loading fails, component shows "0.0°C" instead of crashing

---

### Example 2: AppsMarketplace

**Before**:
```javascript
const filtered = services.filter(service =>
  service.name.toLowerCase().includes(query)
);
```

**After**:
```javascript
const filtered = safeFilter(services, service =>
  safeIncludes((service.name || '').toLowerCase(), query)
);
```

**Why**: If API returns malformed service without name, search doesn't crash

---

### Example 3: Dashboard Metrics

**Before**:
```jsx
<MetricCard value={metrics.activeUsers} />
```

**After**:
```jsx
<ErrorBoundary fallbackMessage="Failed to load metrics">
  <MetricCard value={metrics?.activeUsers || 0} />
</ErrorBoundary>
```

**Why**: If metrics API fails, shows error message instead of blank card

---

## FAQ

**Q: Should I use safe utilities everywhere?**
A: No, only where data might be null/undefined. If data is guaranteed to exist (e.g., hardcoded constants), native methods are fine.

**Q: What's the performance impact?**
A: Minimal (~1-2ms per 1000 calls). Benefits of preventing crashes far outweigh the cost.

**Q: Can I use safe utilities in backend code?**
A: Yes! They're pure JavaScript functions that work anywhere.

**Q: Should I wrap every component in ErrorBoundary?**
A: No, only wrap pages and complex components. Too many boundaries can hide bugs.

**Q: What if I need custom error handling?**
A: Create a custom ErrorBoundary that accepts an `onError` prop for custom logic.

---

## Additional Resources

- React Error Boundaries: https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary
- Optional Chaining: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining
- Nullish Coalescing: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing

---

**End of Guide**

Remember: Defensive coding is about **graceful degradation**, not preventing all errors. The goal is a better user experience when things go wrong.
