# Agent 1: Data Integrity Specialist - C05 Task

**Mission**: Remove ALL fake data fallbacks in LLMUsage.jsx

**File**: `/home/muut/Production/UC-Cloud/services/ops-center/src/pages/LLMUsage.jsx`

**Duration**: 4-6 hours

---

## Issues to Fix

### 1. Fake Usage Summary Data (Lines 113-131)
**Location**: `loadUsageData()` function, else block after `if (summaryResponse.ok)`

**Current Code**:
```javascript
} else {
  // Mock data for demo
  setUsageData({
    total_calls: 45230,
    total_cost: 124.56,
    avg_cost_per_call: 0.00275,
    quota_used_percent: 78,
    quota_limit: 100000,
    timeline: Array.from({ length: 30 }, (_, i) => ({
      date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      calls: Math.floor(Math.random() * 2000) + 1000,
      cost: Math.random() * 5 + 2
    })),
    growth: {
      calls: 12,
      cost: 8,
      avg_cost: -3
    }
  });
}
```

**Fix**: Replace with:
```javascript
} else {
  console.error('Failed to load usage summary:', summaryResponse.status);
  setUsageData(null); // Will trigger error state
}
```

### 2. Fake Provider Data (Lines 142-151)
**Location**: `loadUsageData()` function, else block after provider fetch

**Current Code**:
```javascript
} else {
  // Mock data
  setProviderData({
    providers: [
      { name: 'OpenAI', calls: 20350, cost: 56.23, percentage: 45 },
      { name: 'Anthropic', calls: 13570, cost: 38.12, percentage: 30 },
      { name: 'Google AI', calls: 9050, cost: 21.45, percentage: 20 },
      { name: 'Cohere', calls: 2260, cost: 8.76, percentage: 5 }
    ]
  });
}
```

**Fix**: Replace with:
```javascript
} else {
  console.error('Failed to load provider data:', providerResponse.status);
  setProviderData(null); // Will trigger error state
}
```

### 3. Fake Power Level Data (Lines 162-170)
**Location**: `loadUsageData()` function, else block after power level fetch

**Current Code**:
```javascript
} else {
  // Mock data
  setPowerLevelData({
    levels: [
      { level: 'eco', calls: 27140, cost: 28.34, percentage: 60 },
      { level: 'balanced', calls: 13570, cost: 62.15, percentage: 30 },
      { level: 'precision', calls: 4520, cost: 34.07, percentage: 10 }
    ]
  });
}
```

**Fix**: Replace with:
```javascript
} else {
  console.error('Failed to load power level data:', powerLevelResponse.status);
  setPowerLevelData(null); // Will trigger error state
}
```

### 4. Fake Recent Requests Table (Lines 518-542)
**Location**: Recent Requests Table tbody

**Current Code**:
```javascript
<tbody>
  {[...Array(10)].map((_, idx) => (
    <tr key={idx} className={...}>
      <td className={...}>
        {new Date(Date.now() - idx * 60000).toLocaleTimeString()}
      </td>
      <td className={...}>
        {['GPT-4', 'Claude Sonnet', 'GPT-3.5'][idx % 3]}
      </td>
      <td className={...}>
        <span className={...}>
          {['Eco', 'Balanced', 'Precision'][idx % 3]}
        </span>
      </td>
      <td className={...}>
        ${(Math.random() * 0.01).toFixed(4)}
      </td>
      <td className={...}>
        {Math.floor(Math.random() * 2000 + 500)}ms
      </td>
    </tr>
  ))}
</tbody>
```

**Fix**: Either fetch real data OR show empty state:
```javascript
<tbody>
  {usageData?.recent_requests?.length > 0 ? (
    usageData.recent_requests.map((req, idx) => (
      <tr key={idx} className={...}>
        <td className={...}>
          {new Date(req.timestamp).toLocaleTimeString()}
        </td>
        <td className={...}>{req.model}</td>
        <td className={...}>
          <span className={...}>{req.power_level}</span>
        </td>
        <td className={...}>${req.cost.toFixed(4)}</td>
        <td className={...}>{req.latency}ms</td>
      </tr>
    ))
  ) : (
    <tr>
      <td colSpan="5" className="text-center py-8">
        <p className={themeClasses.subtext}>
          No recent requests to display
        </p>
      </td>
    </tr>
  )}
</tbody>
```

---

## Error State UI to Add

Add this section after the loading spinner check (around line 207):

```javascript
if (loading) {
  return (
    <div className="flex items-center justify-center h-96">
      <div className="text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-500 mx-auto mb-4"></div>
        <p className={themeClasses.text}>Loading usage data...</p>
      </div>
    </div>
  );
}

// ADD THIS ERROR STATE:
if (!loading && !usageData) {
  return (
    <div className="flex items-center justify-center h-96">
      <div className="text-center max-w-md">
        <ExclamationTriangleIcon className="h-16 w-16 text-red-400 mx-auto mb-4" />
        <h3 className={`text-xl font-semibold ${themeClasses.text} mb-2`}>
          Failed to Load Usage Data
        </h3>
        <p className={`${themeClasses.subtext} mb-6`}>
          Unable to fetch LLM usage statistics. This could be due to a network issue or the API being unavailable.
        </p>
        <button
          onClick={loadUsageData}
          className={`flex items-center gap-2 px-6 py-3 rounded-lg ${themeClasses.button} mx-auto`}
        >
          <ArrowPathIcon className="h-5 w-5" />
          Retry
        </button>
      </div>
    </div>
  );
}
```

---

## Charts Error Handling

For the charts (lines 405-497), add conditional rendering:

```javascript
{/* Usage by Provider */}
<div className={`rounded-xl border p-6 ${themeClasses.card}`}>
  <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4`}>
    Usage by Provider
  </h3>
  {providerData?.providers?.length > 0 ? (
    <>
      <div className="h-64 mb-4">
        <Pie data={...} options={...} />
      </div>
      <div className="space-y-2">
        {providerData.providers.map((provider, idx) => (
          <div key={idx} className="flex items-center justify-between text-sm">
            ...
          </div>
        ))}
      </div>
    </>
  ) : (
    <div className="h-64 flex items-center justify-center">
      <p className={themeClasses.subtext}>No provider data available</p>
    </div>
  )}
</div>
```

Same pattern for power level chart.

---

## Acceptance Criteria

- [ ] All 4 fake data blocks removed
- [ ] Error state shows when APIs fail
- [ ] Empty state shows when no data exists (different from error)
- [ ] Loading state shows during API calls
- [ ] Retry button works
- [ ] No console warnings about missing data
- [ ] Charts handle null/undefined data gracefully
- [ ] Recent requests table shows empty state OR real data only

---

## Testing Commands

```bash
# Build and deploy
cd /home/muut/Production/UC-Cloud/services/ops-center
npm run build
cp -r dist/* public/
docker restart ops-center-direct

# Test in browser
# 1. Visit: https://your-domain.com/admin/llm/usage
# 2. Disable backend API (simulate failure)
# 3. Verify error state appears with retry button
# 4. Re-enable API and click retry
# 5. Verify real data loads
```

---

## Deliverables

1. Modified `src/pages/LLMUsage.jsx` with all fake data removed
2. Error states implemented
3. Empty states implemented
4. Working retry functionality
5. Report any API endpoints that don't exist (so backend team can create them)
