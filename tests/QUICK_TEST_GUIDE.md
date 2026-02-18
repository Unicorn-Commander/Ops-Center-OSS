# Quick Test Guide - Plans Page

## Run All Tests

```bash
cd /home/deploy/Production/UC-1-Pro/services/ops-center
bash tests/test_plans_page.sh
```

## Quick Manual Tests

### 1. Check Plans Page
```bash
curl -I https://unicorncommander.ai/plans.html
# Expected: HTTP/2 200
```

### 2. Check API Endpoint
```bash
curl https://unicorncommander.ai/api/v1/subscriptions/plans | jq
# Expected: JSON with 4 plans
```

### 3. Verify Trial Tier
```bash
curl -s https://unicorncommander.ai/api/v1/subscriptions/plans | \
  jq '.plans[] | select(.name == "trial")'
```

**Expected Output:**
```json
{
  "id": "trial",
  "name": "trial",
  "display_name": "Trial",
  "price_monthly": 1.0,
  "features": ["7-day trial period", ...],
  "api_calls_limit": 700
}
```

### 4. Test in Browser
```
1. Open: https://unicorncommander.ai/plans.html
2. Open browser console (F12)
3. Check for errors
4. Click "Select Trial" button
5. Verify redirect to: /signup-flow.html?plan=trial
```

## Test Results

**Status:** ✅ ALL TESTS PASSED

**Key Findings:**
- Plans page loads in 28ms
- API responds in 28ms
- Trial tier: $1 for 7 days ✓
- All 4 tiers present ✓

## Test Reports

- Full Report: `/tests/PLANS_PAGE_TEST_REPORT.md`
- Summary: `/tests/TEST_SUMMARY.txt`
- Test Script: `/tests/test_plans_page.sh`

## Warnings

1. POST method returns 500 (should be 405) - LOW PRIORITY
2. Missing Stripe Price IDs - Add when payments go live

## Next Steps

1. Monitor user signups
2. Add Stripe Price IDs
3. Collect user feedback
4. Implement UX enhancements
