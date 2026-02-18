# Tier Enforcement - Quick Test Guide

## Prerequisites

1. **Keycloak running** at `https://auth.unicorncommander.ai/realms/uchub`
2. **Admin credentials** configured in environment
3. **Test user** created in Keycloak with email address

## Environment Setup

```bash
export KEYCLOAK_URL=https://auth.unicorncommander.ai
export KEYCLOAK_REALM=uchub
export KEYCLOAK_ADMIN_USERNAME=admin
export KEYCLOAK_ADMIN_PASSWORD=your_password
export TIER_ENFORCEMENT_ENABLED=true
```

## Quick Tests

### Test 1: Python Integration Test

```bash
cd /home/deploy/Production/UC-1-Pro/services/ops-center/backend

# Run test suite
python3 tests/test_tier_enforcement.py your@email.com
```

**Expected Output**:
```
✅ PASS | Keycloak Connection | Token obtained: ...
✅ PASS | User Retrieval | User found: username
✅ PASS | Tier Info Retrieval | Tier: trial, Status: active, Usage: 0
✅ PASS | Usage Reset | Before: 5, After: 0
✅ PASS | Usage Increment | Before: 0, After: 1
✅ PASS | Tier Change | Before: trial, After: professional
✅ PASS | Tier Limits Configuration | Limits: {...}

TEST SUMMARY
Total Tests: 7
Passed: 7
Failed: 0
```

### Test 2: Live API Test

```bash
# Step 1: Login and save session
curl -c /tmp/session.txt -X POST https://unicorncommander.ai/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpass"}'

# Step 2: Check current usage
curl -b /tmp/session.txt https://unicorncommander.ai/api/v1/usage/current | jq

# Step 3: Make API call with headers
curl -b /tmp/session.txt https://unicorncommander.ai/api/v1/services -v 2>&1 | grep X-
```

**Expected Headers**:
```http
X-Tier: trial
X-Tier-Status: active
X-API-Calls-Used: 1
X-API-Calls-Limit: 100
X-API-Calls-Remaining: 99
```

### Test 3: Full Test Suite (Bash)

```bash
# Run comprehensive bash tests
SESSION_FILE=/tmp/session.txt \
  /home/deploy/Production/UC-1-Pro/services/ops-center/backend/tests/test_tier_enforcement.sh
```

**Expected Output**:
```
[1] Testing authentication status...
✅ Authenticated

[2] Testing usage API - current usage...
✅ Usage data retrieved

[3] Testing usage API - tier limits...
✅ Tier limits retrieved

[4] Testing usage API - tier features...
✅ Tier features retrieved

[5] Testing tier enforcement headers...
✅ Tier headers present
   Tier: trial
   Status: active
   Used: 5
   Limit: 100
   Remaining: 95

[6] Testing usage counter increment (5 calls)...
   Call 1: Usage = 6
   Call 2: Usage = 7
   Call 3: Usage = 8
   Call 4: Usage = 9
   Call 5: Usage = 10
✅ Usage counter incremented correctly
```

## Manual Verification

### Check Keycloak User Attributes

```bash
# Get admin token
TOKEN=$(curl -s -X POST \
  "https://auth.unicorncommander.ai/realms/uchub/protocol/openid-connect/token" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=$KEYCLOAK_ADMIN_USERNAME" \
  -d "password=$KEYCLOAK_ADMIN_PASSWORD" | jq -r '.access_token')

# Get user attributes
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://auth.unicorncommander.ai/admin/realms/uchub/users?email=your@email.com" \
  | jq '.[] | .attributes'
```

**Expected Output**:
```json
{
  "subscription_tier": ["trial"],
  "subscription_status": ["active"],
  "api_calls_used": ["10"],
  "api_calls_reset_date": ["2025-10-10"]
}
```

## Common Test Scenarios

### Scenario 1: Hit Rate Limit

```bash
# Set tier to trial (100 calls/day)
# Make 100+ API calls
for i in {1..105}; do
  curl -b /tmp/session.txt https://unicorncommander.ai/api/v1/services -s -o /dev/null -w "Call $i: %{http_code}\n"
  sleep 0.1
done
```

**Expected**: First 100 return `200`, then `429` with error message.

### Scenario 2: Inactive Subscription

```bash
# Via Python
python3 -c "
import asyncio
from keycloak_integration import set_subscription_tier

async def test():
    await set_subscription_tier('your@email.com', 'trial', 'inactive')

asyncio.run(test())
"

# Test API call
curl -b /tmp/session.txt https://unicorncommander.ai/api/v1/services
```

**Expected**: `403 Forbidden` with subscription_inactive error.

### Scenario 3: Tier Upgrade

```bash
# Upgrade to professional
python3 -c "
import asyncio
from keycloak_integration import set_subscription_tier, reset_usage

async def test():
    await set_subscription_tier('your@email.com', 'professional', 'active')
    await reset_usage('your@email.com')

asyncio.run(test())
"

# Verify new limit
curl -b /tmp/session.txt https://unicorncommander.ai/api/v1/usage/current | jq '.usage.api_calls.daily_limit'
```

**Expected**: `333` (professional tier limit)

## Debugging Commands

### Check if middleware is loaded

```bash
docker logs unicorn-ops-center 2>&1 | grep "TierEnforcementMiddleware initialized"
```

### Check tier enforcement logs

```bash
docker logs unicorn-ops-center 2>&1 | grep -E "Tier|usage|Keycloak" | tail -50
```

### Test Keycloak connection

```bash
python3 -c "
import asyncio
from keycloak_integration import get_admin_token

async def test():
    token = await get_admin_token()
    print(f'Token: {token[:50]}...' if token else 'Failed')

asyncio.run(test())
"
```

## Troubleshooting Quick Fixes

### Issue: Can't connect to Keycloak

```bash
# Check environment variables
env | grep KEYCLOAK

# Test direct connection
curl https://auth.unicorncommander.ai/realms/uchub/.well-known/openid-configuration
```

### Issue: Attributes not updating

```bash
# Reset and try again
python3 -c "
import asyncio
from keycloak_integration import reset_usage

async def test():
    success = await reset_usage('your@email.com')
    print('Reset:', 'Success' if success else 'Failed')

asyncio.run(test())
"
```

### Issue: Headers missing

```bash
# Check if path is exempt
curl -b /tmp/session.txt https://unicorncommander.ai/api/v1/services -v 2>&1 | grep X-Tier

# If no headers, check if tier enforcement enabled
docker exec unicorn-ops-center env | grep TIER_ENFORCEMENT_ENABLED
```

## Reset Everything (Clean Slate)

```bash
# Reset user to trial with clean usage
python3 -c "
import asyncio
from keycloak_integration import set_subscription_tier, reset_usage

async def reset():
    email = 'your@email.com'
    await set_subscription_tier(email, 'trial', 'active')
    await reset_usage(email)
    print(f'Reset {email} to trial tier with 0 usage')

asyncio.run(reset())
"
```

## Production Verification Checklist

Before declaring success in production:

- [ ] Python tests pass (7/7)
- [ ] Bash tests pass (all checks green)
- [ ] Headers appear in responses
- [ ] Usage counter increments
- [ ] Rate limit enforced at threshold
- [ ] Inactive subscription blocked
- [ ] Keycloak attributes update correctly
- [ ] Daily reset works (test after UTC midnight)
- [ ] Error responses are user-friendly
- [ ] Logs show no errors

## Quick Reference: API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/usage/current` | GET | Current usage and tier |
| `/api/v1/usage/limits` | GET | Limits for all tiers |
| `/api/v1/usage/features` | GET | Features by tier |
| `/api/v1/usage/history` | GET | Historical data |
| `/api/v1/usage/reset-demo` | POST | Reset counter (dev only) |

## Quick Reference: Tier Limits

| Tier | Daily | Monthly | Status |
|------|-------|---------|--------|
| Trial | 100 | 3,000 | Default |
| Starter | 33 | 1,000 | Paid |
| Professional | 333 | 10,000 | Paid |
| Enterprise | ∞ | ∞ | Paid |

## Success Confirmation

If all these return positive results, tier enforcement is working:

1. ✅ Keycloak connection successful
2. ✅ User tier retrieved
3. ✅ Usage counter increments
4. ✅ Headers present in responses
5. ✅ Rate limit enforced
6. ✅ API endpoints return correct data

**Status**: Ready for production deployment!

---

**Last Updated**: October 10, 2025
