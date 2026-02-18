# Sprint 2 Execution Plan - Data Integrity Fixes

**Generated**: October 25, 2025
**Team Lead**: Sprint 2 Coordinator
**Estimated Time**: 14-18 hours total (4-6 hours parallel)

---

## Objectives

Fix 3 critical data integrity issues that prevent users from understanding what data is real vs fake:

1. **C05**: Remove fake data fallbacks in LLM Usage
2. **C06**: Enable subscription functionality in Credits & Tiers
3. **H15**: Fix network stats always showing 0

---

## Agent Assignments

### Agent 1: Data Integrity Specialist (C05)
**Task**: Remove fake data fallbacks in LLMUsage.jsx
**Files**: `src/pages/LLMUsage.jsx`
**Estimated Time**: 4-6 hours

**Current Issues**:
- Lines 113-131: Fake usage data when `/api/v1/llm/usage/summary` fails
- Lines 142-151: Fake provider data when `/api/v1/llm/usage/by-provider` fails
- Lines 162-170: Fake power level data when `/api/v1/llm/usage/by-power-level` fails
- Lines 518-542: Recent requests table uses hardcoded fake data (always renders 10 fake rows)

**Requirements**:
1. Remove all `// Mock data` fallback blocks
2. Add error states to show when APIs fail
3. Add empty states when no data exists
4. Show loading spinners during fetch
5. Display clear error messages (not silent failures)

**Expected Output**:
```jsx
// BEFORE (lines 113-131)
} else {
  // Mock data for demo
  setUsageData({
    total_calls: 45230,
    total_cost: 124.56,
    // ... fake data ...
  });
}

// AFTER
} else {
  console.error('Failed to load usage summary:', summaryResponse.status);
  setUsageData(null); // Set to null to trigger error state
}

// Then add error UI:
{!usageData && !loading && (
  <div className="text-center py-12">
    <ExclamationTriangleIcon className="h-12 w-12 text-red-400 mx-auto mb-4" />
    <h3 className={`text-lg font-semibold ${themeClasses.text}`}>
      Failed to Load Usage Data
    </h3>
    <p className={themeClasses.subtext}>
      Could not fetch usage statistics. Please try again later.
    </p>
    <button onClick={loadUsageData} className={themeClasses.button}>
      Retry
    </button>
  </div>
)}
```

**Acceptance Criteria**:
- [ ] No fake data generation anywhere in the file
- [ ] Error states show clear messages when APIs fail
- [ ] Empty states show when no data exists (different from error)
- [ ] Loading states show during API calls
- [ ] Users can retry failed API calls
- [ ] Recent requests table either loads real data or shows "No recent requests"

---

### Agent 2: Billing Integration Specialist (C06)
**Task**: Enable subscription functionality in TierComparison.jsx
**Files**: `src/pages/TierComparison.jsx`, `backend/lago_integration.py`
**Estimated Time**: 8-12 hours

**Current Issues**:
- Lines 12-97: All tier data is hardcoded
- Lines 214-223: Buttons use `href` (page navigation), not Stripe Checkout
- No integration with Lago billing API
- No real-time plan data from backend
- No "Select Plan" functionality

**Requirements**:

**Backend (4-6 hours)**:
1. Create `/api/v1/billing/plans/public` endpoint
   - Returns all 4 subscription plans with pricing
   - No authentication required (public data)
   - Response format:
   ```json
   {
     "plans": [
       {
         "id": "bbbba413-45de-468d-b03e-f23713684354",
         "code": "trial",
         "name": "Trial",
         "description": "Perfect for testing...",
         "amount_cents": 100,
         "interval": "weekly",
         "credits": 10,
         "features": ["Auto OpenRouter...", "..."],
         "limitations": ["No paid models", "..."]
       },
       // ... other plans
     ]
   }
   ```

2. Create `/api/v1/billing/checkout/create` endpoint
   - Accepts: `{ plan_code: "starter" }`
   - Creates Stripe Checkout session
   - Returns: `{ checkout_url: "https://checkout.stripe.com/..." }`
   - Requires authentication

**Frontend (4-6 hours)**:
1. Replace hardcoded tiers with API call to `/api/v1/billing/plans/public`
2. Add loading states while fetching plans
3. Replace `href` buttons with `onClick` handlers
4. Implement Stripe Checkout flow:
   ```jsx
   const handleSelectPlan = async (planCode) => {
     try {
       const response = await fetch('/api/v1/billing/checkout/create', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         credentials: 'include',
         body: JSON.stringify({ plan_code: planCode })
       });

       const data = await response.json();
       if (data.checkout_url) {
         window.location.href = data.checkout_url; // Redirect to Stripe
       }
     } catch (error) {
       // Show error toast
     }
   };
   ```
5. Add error handling and user feedback
6. Show current subscription tier (if user is logged in)

**Acceptance Criteria**:
- [ ] `/api/v1/billing/plans/public` returns real plan data from Lago
- [ ] `/api/v1/billing/checkout/create` creates Stripe Checkout session
- [ ] "Select Plan" button redirects to Stripe Checkout
- [ ] Error handling shows clear messages to users
- [ ] Loading states during API calls
- [ ] Current subscription highlighted if user logged in
- [ ] Free tier allows signup without payment

---

### Agent 3: System Monitoring Specialist (H15)
**Task**: Fix network stats always showing 0
**Files**: `src/pages/System.jsx`
**Estimated Time**: 2-3 hours

**Current Issue**:
- Line 180: `const [networkStats, setNetworkStats] = useState({ in: 0, out: 0 });`
- State is initialized but never updated
- No `fetchNetworkStats()` function exists
- `updateHistoricalData()` doesn't populate network data

**Requirements**:

**Frontend (2-3 hours)**:
1. Create `fetchNetworkStats()` function:
   ```jsx
   const fetchNetworkStats = async () => {
     try {
       const response = await fetch('/api/v1/system/network');
       if (response.ok) {
         const data = await response.json();
         setNetworkStats({
           in: data.bytes_recv_per_sec || 0,
           out: data.bytes_sent_per_sec || 0
         });
       }
     } catch (error) {
       console.error('Failed to fetch network stats:', error);
     }
   };
   ```

2. Call `fetchNetworkStats()` in useEffect interval (line 193-196)
3. Update `updateHistoricalData()` to include network data:
   ```jsx
   network: [...dataRef.current.network, {
     time: timestamp,
     in: networkStats.in,
     out: networkStats.out
   }].slice(-maxDataPoints)
   ```

4. Add error handling if network API fails

**Backend Verification**:
- Verify `/api/v1/system/network` endpoint exists in `backend/server.py`
- If not, create it to return network I/O stats

**Acceptance Criteria**:
- [ ] `fetchNetworkStats()` function implemented
- [ ] Function called in useEffect interval
- [ ] `networkStats` state updates with real data
- [ ] Network tab shows live data (not 0)
- [ ] Historical network chart populates
- [ ] Error handling if API unavailable

---

## Testing Checklist

### C05 Testing (LLM Usage)
- [ ] Visit `/admin/llm/usage` with working backend → Shows real data
- [ ] Disable backend API → Shows error state with retry button
- [ ] Click retry → Attempts to reload data
- [ ] No data available → Shows "No usage data yet" empty state
- [ ] Loading states appear during API calls
- [ ] No fake/random data appears anywhere

### C06 Testing (Subscription Tiers)
- [ ] Visit `/admin/subscription/plan` → Loads real plans from API
- [ ] Click "Select Plan" (Free) → Redirects to signup/payment flow
- [ ] Click "Select Plan" (Starter) → Opens Stripe Checkout
- [ ] Click "Select Plan" (Pro) → Opens Stripe Checkout
- [ ] Click "Contact Sales" (Enterprise) → Opens email client
- [ ] Logged-in user sees current tier highlighted
- [ ] API errors show toast notifications

### H15 Testing (Network Stats)
- [ ] Visit `/admin/system/monitoring` → Network stats show non-zero values
- [ ] Switch to Network tab → Shows live network I/O chart
- [ ] Historical data populates over time
- [ ] Network in/out displays in cards with proper units (KB/s, MB/s)
- [ ] Auto-refresh updates network stats every 2 seconds

---

## Backend API Requirements

### Existing Endpoints (Verify)
- `GET /api/v1/llm/usage/summary` - Returns usage statistics
- `GET /api/v1/llm/usage/by-provider` - Returns provider breakdown
- `GET /api/v1/llm/usage/by-power-level` - Returns power level breakdown
- `GET /api/v1/system/network` - Returns network I/O stats

### New Endpoints (Create)
- `GET /api/v1/billing/plans/public` - Returns all subscription plans (public)
- `POST /api/v1/billing/checkout/create` - Creates Stripe Checkout session

**File**: `backend/lago_integration.py` or `backend/subscription_manager.py`

---

## Deployment Steps

After all agents complete their work:

1. **Build Frontend**:
   ```bash
   cd /opt/ops-center
   npm run build
   cp -r dist/* public/
   ```

2. **Restart Backend**:
   ```bash
   docker restart ops-center-direct
   ```

3. **Verify Services**:
   ```bash
   docker logs ops-center-direct --tail 50
   curl http://localhost:8084/api/v1/billing/plans/public
   curl http://localhost:8084/api/v1/system/network
   ```

4. **Test in Browser**:
   - LLM Usage: https://unicorncommander.ai/admin/llm/usage
   - Subscription: https://unicorncommander.ai/admin/subscription/plan
   - Monitoring: https://unicorncommander.ai/admin/system/monitoring

5. **Git Commit**:
   ```bash
   git add .
   git commit -m "fix: Sprint 2 Data Integrity - Remove fake data, enable subscriptions, fix network stats

   - C05: Removed fake data fallbacks in LLMUsage.jsx, added error/empty states
   - C06: Integrated Stripe Checkout for subscription tiers, connected to Lago API
   - H15: Fixed network stats always showing 0, added fetchNetworkStats()

   All data integrity issues resolved. Users can now distinguish real data from errors."
   ```

---

## Success Metrics

**Before Sprint 2**:
- LLM Usage showed fake data when APIs failed (silent failure)
- Subscription page had non-functional "Select Plan" buttons
- Network stats always showed 0 KB/s

**After Sprint 2**:
- LLM Usage shows clear error states when APIs fail
- Subscription page integrates with Stripe Checkout
- Network stats show live network I/O data

**User Impact**:
- Users can trust the data they see (no silent fake data)
- Users can successfully subscribe to paid tiers
- Admins can monitor real-time network performance

---

## Coordination Notes

- **Agent 1** can work independently (frontend-only changes)
- **Agent 2** requires backend + frontend (most complex task)
- **Agent 3** can work independently (frontend-only, possibly new backend endpoint)

**Parallel Execution**:
- All 3 agents can work simultaneously
- No file conflicts (different files)
- Merge after all complete

**Communication**:
- Each agent commits to separate branch
- Team lead reviews and merges
- Final integration test before deployment
