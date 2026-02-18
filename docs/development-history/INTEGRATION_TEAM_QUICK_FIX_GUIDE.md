# Integration Team - Quick Fix Guide
**Priority**: 🔥 URGENT
**Time Required**: 1 hour
**Complexity**: Easy

---

## ⚡ Quick Summary

You built great code, but forgot to wire it up! Here's how to fix it fast.

**3 Critical Issues**:
1. API not registered → 404 errors
2. Page has no route → Unreachable
3. Mock data in production → Fake numbers

**Fixes**: 3 files to edit, 10 minutes each

---

## 🔧 Fix #1: Register Dynamic Pricing API (5 minutes)

### Problem:
```bash
curl https://unicorncommander.ai/api/v1/pricing/rules/byok
{"detail":"Not Found"}  # ❌ 404 Error
```

### Root Cause:
You created `dynamic_pricing_api.py` but never imported it in `server.py`

### Fix:
```bash
cd /opt/ops-center

# Edit server.py
vim backend/server.py

# Find this line (around line 77):
from org_billing_api import router as org_billing_router

# Add BELOW it:
from dynamic_pricing_api import router as dynamic_pricing_router

# Find this line (around line 640):
app.include_router(org_billing_router)

# Add BELOW it:
app.include_router(dynamic_pricing_router)
logger.info("Dynamic Pricing API endpoints registered at /api/v1/pricing")

# Save and exit (:wq)
```

### Test:
```bash
# Restart backend
docker restart ops-center-direct

# Wait 10 seconds
sleep 10

# Test API (should now work)
curl https://unicorncommander.ai/api/v1/pricing/rules/byok
# Should return: [] or pricing data (not 404!)
```

### Expected Result:
✅ All pricing endpoints now return 200 OK instead of 404

---

## 🔧 Fix #2: Add User Billing Dashboard Route (5 minutes)

### Problem:
```
User clicks link to /billing/dashboard
Browser shows: 404 Not Found
```

### Root Cause:
You created `UserBillingDashboard.jsx` but never added route in `App.jsx`

### Fix:
```bash
cd /opt/ops-center

# Edit App.jsx
vim src/App.jsx

# Find the lazy imports section (around line 30-80)
# Look for lines like:
const OrganizationBilling = lazy(() => import('./pages/organization/OrganizationBilling'));

# Add this line with the others:
const UserBillingDashboard = lazy(() => import('./pages/billing/UserBillingDashboard'));

# Now find the Routes section (around line 200-300)
# Look for organization/billing routes like:
<Route path="organization/billing" element={<OrganizationBilling />} />

# Add this line near billing-related routes:
<Route path="billing/dashboard" element={<UserBillingDashboard />} />

# Save and exit (:wq)
```

### Test:
```bash
# Build frontend
npm run build

# Deploy to public/
cp -r dist/* public/

# Clear browser cache and visit:
# https://unicorncommander.ai/billing/dashboard
# Should now load page (not 404!)
```

### Expected Result:
✅ Page loads at /billing/dashboard

---

## 🔧 Fix #3: Replace Mock Data with Real API (30 minutes)

### Problem:
Organization Billing page shows hardcoded fake data:
- Plan: "Professional" (always)
- Amount: $49.00 (always)
- API Calls: 8,547 / 10,000 (always)

### Root Cause:
Lines 45-73 of `OrganizationBilling.jsx` use hardcoded mock object

### Fix (Full Code):
```bash
cd /opt/ops-center

# Edit OrganizationBilling.jsx
vim src/pages/organization/OrganizationBilling.jsx
```

**Replace lines 45-73** (the mock billing object) with:
```javascript
// Real data from API (not mock)
const [billing, setBilling] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);
```

**Replace lines 102-107** (empty fetchBillingData) with:
```javascript
const fetchBillingData = async () => {
  if (!currentOrg) {
    console.log('No organization selected');
    return;
  }

  try {
    setLoading(true);
    setError(null);

    // Fetch organization billing data
    const billingResponse = await fetch(`/api/v1/org-billing/billing/org/${currentOrg.id}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      }
    });

    if (!billingResponse.ok) {
      throw new Error('Failed to load billing data');
    }

    const billingData = await billingResponse.json();

    // Fetch credit pool data
    const creditsResponse = await fetch(`/api/v1/org-billing/credits/${currentOrg.id}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      }
    });

    const creditsData = creditsResponse.ok ? await creditsResponse.json() : null;

    // Fetch credit allocations
    const allocationsResponse = await fetch(`/api/v1/org-billing/credits/${currentOrg.id}/allocations`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      }
    });

    const allocationsData = allocationsResponse.ok ? await allocationsResponse.json() : [];

    // Fetch usage data
    const usageResponse = await fetch(`/api/v1/org-billing/credits/${currentOrg.id}/usage`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      }
    });

    const usageData = usageResponse.ok ? await usageResponse.json() : { by_user: [], by_model: [] };

    // Combine all data
    setBilling({
      subscription: billingData.subscription || {
        plan: 'Free',
        status: 'active',
        amount: 0,
        currency: 'USD',
        interval: 'month'
      },
      credits: creditsData || {
        total_credits: 0,
        allocated_credits: 0,
        available_credits: 0
      },
      allocations: allocationsData,
      usage: usageData
    });

    showToast('Billing data loaded successfully', 'success');
  } catch (err) {
    console.error('Failed to fetch billing data:', err);
    setError(err.message);
    showToast(`Failed to load billing data: ${err.message}`, 'error');
  } finally {
    setLoading(false);
  }
};
```

**Update the UI to handle null billing state** (around line 150-200):
```javascript
// Add loading check
if (loading) {
  return (
    <div className="flex justify-center items-center h-screen">
      <div className="text-center">
        <ArrowPathIcon className="h-8 w-8 animate-spin mx-auto mb-2 text-purple-500" />
        <p className="text-gray-400">Loading billing data...</p>
      </div>
    </div>
  );
}

// Add error check
if (error) {
  return (
    <div className="flex justify-center items-center h-screen">
      <div className="text-center">
        <ExclamationTriangleIcon className="h-12 w-12 mx-auto mb-4 text-red-500" />
        <p className="text-gray-400 mb-4">Failed to load billing data</p>
        <p className="text-sm text-gray-500 mb-4">{error}</p>
        <button
          onClick={() => fetchBillingData()}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
        >
          Retry
        </button>
      </div>
    </div>
  );
}

// Add null check
if (!billing) {
  return (
    <div className="flex justify-center items-center h-screen">
      <p className="text-gray-400">No billing data available</p>
    </div>
  );
}
```

**Update subscription card** (around line 220-250) to use real data:
```javascript
{/* Subscription Plan Card */}
<div className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-6 border border-gray-700">
  <div className="flex justify-between items-start mb-4">
    <div>
      <p className="text-sm text-gray-400 mb-1">Current Plan</p>
      <h3 className="text-2xl font-bold text-white">
        {billing.subscription.plan || 'Free'}
      </h3>
    </div>
    <span className={`px-3 py-1 rounded-full text-sm ${
      billing.subscription.status === 'active' ? 'bg-green-500/20 text-green-400' :
      billing.subscription.status === 'trialing' ? 'bg-blue-500/20 text-blue-400' :
      billing.subscription.status === 'past_due' ? 'bg-yellow-500/20 text-yellow-400' :
      'bg-red-500/20 text-red-400'
    }`}>
      {billing.subscription.status}
    </span>
  </div>

  <div className="text-3xl font-bold text-white mb-4">
    ${billing.subscription.amount?.toFixed(2) || '0.00'}
    <span className="text-sm text-gray-400 font-normal">
      /{billing.subscription.interval || 'month'}
    </span>
  </div>

  {billing.subscription.nextBillingDate && (
    <p className="text-sm text-gray-400 mb-4">
      Next billing: {new Date(billing.subscription.nextBillingDate).toLocaleDateString()}
    </p>
  )}

  {/* Only show upgrade if not on highest tier */}
  {billing.subscription.plan !== 'Enterprise' && (
    <button
      onClick={handleUpgradePlan}
      className="w-full px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:opacity-90 transition-all"
    >
      <ArrowUpIcon className="h-4 w-4 inline mr-2" />
      Upgrade Plan
    </button>
  )}
</div>
```

**Update credit pool card** (around line 270-300) to use real data:
```javascript
{/* Credit Pool Card */}
<div className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-6 border border-gray-700">
  <div className="flex justify-between items-center mb-4">
    <div>
      <p className="text-sm text-gray-400 mb-1">Credit Pool</p>
      <h3 className="text-2xl font-bold text-white">
        {billing.credits?.total_credits?.toLocaleString() || '0'} credits
      </h3>
    </div>
    <BanknotesIcon className="h-8 w-8 text-purple-400" />
  </div>

  <div className="mb-4">
    <div className="flex justify-between text-sm mb-2">
      <span className="text-gray-400">Allocated</span>
      <span className="text-white">
        {billing.credits?.allocated_credits?.toLocaleString() || '0'} credits
      </span>
    </div>
    <div className="flex justify-between text-sm mb-4">
      <span className="text-gray-400">Available</span>
      <span className="text-green-400">
        {billing.credits?.available_credits?.toLocaleString() || '0'} credits
      </span>
    </div>

    {/* Progress bar */}
    <div className="w-full bg-gray-700 rounded-full h-2">
      <div
        className="bg-gradient-to-r from-purple-600 to-pink-600 h-2 rounded-full transition-all"
        style={{
          width: `${billing.credits?.total_credits > 0
            ? (billing.credits.allocated_credits / billing.credits.total_credits * 100)
            : 0}%`
        }}
      />
    </div>
  </div>

  <button
    onClick={() => setShowAddCreditsModal(true)}
    className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-all"
  >
    <BanknotesIcon className="h-4 w-4 inline mr-2" />
    Add Credits
  </button>
</div>
```

Save and exit (:wq)

### Test:
```bash
# Build frontend
npm run build

# Deploy
cp -r dist/* public/

# Restart backend
docker restart ops-center-direct

# Test in browser:
# 1. Login as org admin
# 2. Navigate to /organization/{org_id}/billing
# 3. Should see REAL data (not always 8,547 API calls)
# 4. Should match data from database
```

### Expected Result:
✅ Real subscription data displays
✅ Real credit pool displays
✅ Real usage data displays
✅ No more hardcoded numbers

---

## 📋 Complete Deployment Checklist

After making all 3 fixes, run this checklist:

```bash
# 1. Verify API is registered
grep "dynamic_pricing_api" backend/server.py
# Should see: from dynamic_pricing_api import router

# 2. Verify route is added
grep "UserBillingDashboard" src/App.jsx
# Should see: const UserBillingDashboard = lazy(...)
# Should see: <Route path="billing/dashboard"

# 3. Verify mock data removed
grep -n "plan: 'Professional'" src/pages/organization/OrganizationBilling.jsx
# Should NOT find hardcoded plan (if found, you missed it!)

# 4. Build and deploy
npm run build
cp -r dist/* public/
docker restart ops-center-direct

# 5. Wait for restart
sleep 15

# 6. Test APIs
curl https://unicorncommander.ai/api/v1/pricing/rules/byok
curl https://unicorncommander.ai/api/v1/org-billing/billing/user

# Both should return 200 OK (or 401 if not authenticated)
# Neither should return 404!

# 7. Check container logs
docker logs ops-center-direct --tail 50
# Should see: "Dynamic Pricing API endpoints registered"
# Should NOT see errors

# 8. Manual test in browser
# Login → Navigate to each page → Verify data loads
```

---

## ⚠️ Common Mistakes to Avoid

### Mistake #1: Typo in import
```python
# ❌ WRONG
from dynamic_pricing import router  # Missing _api

# ✅ CORRECT
from dynamic_pricing_api import router as dynamic_pricing_router
```

### Mistake #2: Forgot to build frontend
```bash
# ❌ WRONG (editing source but not deploying)
vim src/App.jsx
# (no build step)
docker restart ops-center-direct  # Changes not applied!

# ✅ CORRECT
vim src/App.jsx
npm run build           # Build changes
cp -r dist/* public/   # Deploy to public/
docker restart ops-center-direct  # Apply changes
```

### Mistake #3: Incomplete mock data removal
```javascript
// ❌ WRONG (still has mock data)
const [billing, setBilling] = useState({
  subscription: { plan: 'Professional', ... }  // Still hardcoded!
});

// ✅ CORRECT (no initial value)
const [billing, setBilling] = useState(null);
```

---

## 🐛 Troubleshooting

### Issue: API still returns 404 after fix
**Solution**:
```bash
# Check if import is actually in server.py
docker exec ops-center-direct grep "dynamic_pricing" /app/server.py

# If not found, edit again and verify save worked
# Then restart with logs:
docker restart ops-center-direct && docker logs ops-center-direct -f

# Look for: "Dynamic Pricing API endpoints registered"
```

### Issue: Page still shows 404 after adding route
**Solution**:
```bash
# Verify build included new route
grep -r "billing/dashboard" public/assets/*.js

# If not found, rebuild:
rm -rf node_modules/.vite dist  # Clear cache
npm run build
cp -r dist/* public/

# Verify deployed:
ls -lh public/assets/
```

### Issue: Still seeing mock data
**Solution**:
```bash
# Check if you actually removed it
grep -C 5 "plan: 'Professional'" src/pages/organization/OrganizationBilling.jsx

# If still there, you missed it - go back and remove
# Then rebuild and deploy
```

### Issue: API returns 401 Unauthorized
**Solution**:
This is NORMAL if not logged in. The fix is working!
```bash
# Test with authentication:
# 1. Login to unicorncommander.ai in browser
# 2. Open DevTools (F12)
# 3. Go to Application → Local Storage
# 4. Copy authToken value
# 5. Test with token:

curl https://unicorncommander.ai/api/v1/pricing/rules/byok \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Should now return 200 OK with data
```

---

## ✅ Success Criteria

After all fixes, you should see:

### API Tests:
```bash
curl https://unicorncommander.ai/api/v1/pricing/rules/byok
# Returns: [] or [...pricing rules...] (200 OK) ✅

curl https://unicorncommander.ai/api/v1/org-billing/billing/user
# Returns: {"detail":"Not authenticated"} (401) ✅
# (401 is good! Means endpoint exists, just needs auth)
```

### Browser Tests:
1. ✅ Navigate to `/billing/dashboard` → Page loads (not 404)
2. ✅ Navigate to `/organization/1/billing` → Real data displays (not mock)
3. ✅ Credit numbers change based on database (not always 8,547)

### Log Messages:
```bash
docker logs ops-center-direct --tail 20

# Should see:
# ✅ "Dynamic Pricing API endpoints registered at /api/v1/pricing"
# ✅ "Organization Billing API endpoints registered at /api/v1/org-billing"
# ✅ No errors
```

---

## 🚀 After You're Done

Once all 3 fixes are deployed:

1. **Update QA Team**:
   - "Emergency fixes deployed"
   - "API endpoints now accessible"
   - "Ready for manual testing"

2. **Test Each Page**:
   - Login as different user types (admin, org admin, regular user)
   - Verify real data displays
   - Check for console errors (F12)

3. **Document Any New Issues**:
   - If you find bugs during testing, add them to KNOWN_ISSUES.md
   - Don't spend time fixing them now - we need the basics working first

4. **Move to Phase 2**:
   - Once these 3 fixes are confirmed working
   - Start creating the 2 missing pages (DynamicPricing, BillingOverview)
   - See DEPLOYMENT_STATUS_DIAGRAM.md for Phase 2 plan

---

## 📞 Need Help?

**If stuck for more than 15 minutes**, stop and ask for help!

**Common issues**:
- Docker container won't restart → Check docker logs
- Build fails → Check for syntax errors in edited files
- API returns 500 error → Check backend logs for Python errors
- Page still 404 → Clear browser cache (Ctrl+Shift+Delete)

**Quick help commands**:
```bash
# Check if backend is running
docker ps | grep ops-center

# View recent logs
docker logs ops-center-direct --tail 50

# Check for syntax errors
npm run build  # Will show errors if code has issues

# Restart everything
docker restart ops-center-direct
```

---

**Good luck! You've got this! 🚀**

**Estimated Time**: 45-60 minutes
**Difficulty**: Easy (just editing 3 files)
**Impact**: Huge (goes from 35% → 60% complete)

---

**Created**: November 12, 2025, 8:30 PM
**For**: Integration Team
**By**: QA & Testing Team Lead
