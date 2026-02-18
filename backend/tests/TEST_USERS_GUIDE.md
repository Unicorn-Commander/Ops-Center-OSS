# Test Users Guide - Tier-Based Model Access Testing

**Created**: November 6, 2025
**Purpose**: Enable comprehensive testing of tier-based model access controls

---

## Overview

This guide documents the 4 test users created for testing subscription tier-based model access controls in the Ops-Center LLM API.

**Test Objective**: Verify that each subscription tier only has access to appropriate models based on pricing and tier restrictions.

---

## Test Users

### 1. Trial User (trial@test.unicorncommander.ai)

**User ID**: `test-trial-user-00000000-0000-0000-0000-000000000001`
**Subscription Tier**: `trial`
**Credits Allocated**: 5.00 credits
**Expected Model Access**: 50-80 models (free/cheap models only)

**Access Restrictions**:
- ✅ Free models (input_cost = 0, output_cost = 0)
- ✅ Very cheap models (total cost < $0.001 per 1K tokens)
- ❌ Mid-tier models ($0.001-$0.01 per 1K tokens)
- ❌ Premium models (>$0.01 per 1K tokens)

**Use Case**: Testing basic access for trial users

---

### 2. Starter User (starter@test.unicorncommander.ai)

**User ID**: `test-starter-user-00000000-0000-0000-0000-000000000002`
**Subscription Tier**: `starter`
**Credits Allocated**: 20.00 credits
**Expected Model Access**: 150-200 models

**Access Restrictions**:
- ✅ All trial tier models
- ✅ Mid-tier models ($0.001-$0.01 per 1K tokens)
- ⚠️ Some premium models (limited access)
- ❌ Most expensive models (>$0.05 per 1K tokens)

**Use Case**: Testing mid-tier subscription access

---

### 3. Professional User (professional@test.unicorncommander.ai)

**User ID**: `test-professional-user-00000000-0000-0000-0000-000000000003`
**Subscription Tier**: `professional`
**Credits Allocated**: 60.00 credits
**Expected Model Access**: 250-300 models

**Access Restrictions**:
- ✅ All starter tier models
- ✅ Most premium models
- ✅ Advanced models (GPT-4, Claude, Gemini Pro)
- ❌ Ultra-premium models (>$0.10 per 1K tokens)

**Use Case**: Testing professional tier with broad model access

---

### 4. Enterprise User (enterprise@test.unicorncommander.ai)

**User ID**: `test-enterprise-user-00000000-0000-0000-0000-000000000004`
**Subscription Tier**: `enterprise`
**Credits Allocated**: 999,999.99 credits (unlimited)
**Expected Model Access**: 370+ models (ALL available models)

**Access Restrictions**: ✅ NONE - Full access to all models

**Use Case**: Testing unlimited enterprise access

---

## Database Schema

Test users are stored in the `user_credits` table in `unicorn_db`:

```sql
SELECT user_id, tier, credits_remaining, credits_allocated
FROM user_credits
WHERE user_id LIKE 'test-%'
ORDER BY tier;
```

**Current Status**:
```
                           user_id                           |     tier     | credits_remaining | credits_allocated
-------------------------------------------------------------+--------------+-------------------+-------------------
 test-enterprise-user-00000000-0000-0000-0000-000000000004  | enterprise   |     999999.990000 |     999999.990000
 test-professional-user-00000000-0000-0000-0000-000000000003| professional |         60.000000 |         60.000000
 test-starter-user-00000000-0000-0000-0000-000000000002     | starter      |         20.000000 |         20.000000
 test-trial-user-00000000-0000-0000-0000-000000000001       | trial        |          5.000000 |          5.000000
```

---

## Testing Instructions

### 1. Automated Testing

Run the automated tier access test:

```bash
cd /opt/ops-center/backend/tests
./test_tier_access.sh
```

**Expected Output**:
- Trial User: 50-80 models ✅
- Starter User: 150-200 models ✅
- Professional User: 250-300 models ✅
- Enterprise User: 370+ models ✅

---

### 2. Manual API Testing

Test each tier manually using curl:

```bash
# Trial User
curl "http://localhost:8084/api/v1/llm/models/available?user_id=test-trial-user-00000000-0000-0000-0000-000000000001" | jq '. | length'

# Starter User
curl "http://localhost:8084/api/v1/llm/models/available?user_id=test-starter-user-00000000-0000-0000-0000-000000000002" | jq '. | length'

# Professional User
curl "http://localhost:8084/api/v1/llm/models/available?user_id=test-professional-user-00000000-0000-0000-0000-000000000003" | jq '. | length'

# Enterprise User
curl "http://localhost:8084/api/v1/llm/models/available?user_id=test-enterprise-user-00000000-0000-0000-0000-000000000004" | jq '. | length'
```

---

### 3. Test Specific Model Access

Verify that trial users CANNOT access expensive models:

```bash
# Try to access GPT-4 (expensive model) as trial user
curl -X POST http://localhost:8084/api/v1/llm/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4",
    "messages": [{"role": "user", "content": "test"}],
    "user": "test-trial-user-00000000-0000-0000-0000-000000000001"
  }'

# Expected: HTTP 403 Forbidden (model not available for tier)
```

Verify that enterprise users CAN access all models:

```bash
# Try to access GPT-4 as enterprise user
curl -X POST http://localhost:8084/api/v1/llm/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4",
    "messages": [{"role": "user", "content": "test"}],
    "user": "test-enterprise-user-00000000-0000-0000-0000-000000000004"
  }'

# Expected: HTTP 200 OK (with response)
```

---

## Recreating Test Users

If test users need to be recreated (e.g., after database reset):

```bash
# Run the creation script
docker exec ops-center-direct python3 /app/scripts/create_test_users.py

# Verify creation
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT user_id, tier, credits_remaining FROM user_credits WHERE user_id LIKE 'test-%';"
```

---

## Test User Credentials File

**Location**: `/opt/ops-center/backend/tests/test_users.json`

**Format**:
```json
{
  "test_users": [
    {
      "user_id": "test-trial-user-00000000-0000-0000-0000-000000000001",
      "email": "trial@test.unicorncommander.ai",
      "tier": "trial",
      "credits": "5.00",
      "description": "Trial user - should see 50-80 free/cheap models only"
    },
    ...
  ],
  "created_at": "2025-11-06T00:00:00.000000",
  "database": "unicorn-postgresql:5432/unicorn_db"
}
```

---

## Success Criteria

✅ **Tier Separation Working**: Each tier sees different model counts
✅ **Trial Restrictions Working**: Trial users blocked from premium models
✅ **Enterprise Access Working**: Enterprise users see all 370+ models
✅ **API Enforcement Working**: POST requests respect tier restrictions
✅ **Credit Tracking Working**: Credits deducted correctly per tier

---

## Troubleshooting

### Test Users Not Found

**Problem**: Test script reports users don't exist

**Solution**:
```bash
docker exec ops-center-direct python3 /app/scripts/create_test_users.py
```

### Wrong Model Counts

**Problem**: Model counts don't match expected ranges

**Possible Causes**:
1. **Tier logic not implemented**: Check `backend/litellm_api.py` tier filtering
2. **Database tier mismatch**: Verify user tier in database
3. **Cache issue**: Clear Redis cache: `docker exec unicorn-redis redis-cli FLUSHDB`

**Debug**:
```bash
# Check actual tier in database
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT user_id, tier FROM user_credits WHERE user_id LIKE 'test-%';"

# Check API response for specific user
curl "http://localhost:8084/api/v1/llm/models/available?user_id=test-trial-user-00000000-0000-0000-0000-000000000001" | jq '.[:5]'
```

### API Returns 401 Unauthorized

**Problem**: API rejects test user requests

**Solution**: Test users are in `user_credits` table but not in Keycloak. For API testing, the user_id is sufficient. For full SSO testing, create corresponding Keycloak users.

---

## Next Steps

1. ✅ **Test users created** (4 tiers)
2. ⏳ **Implement tier filtering** in LLM API (`backend/litellm_api.py`)
3. ⏳ **Run automated tests** to verify model counts
4. ⏳ **Document model access rules** per tier
5. ⏳ **Create tier enforcement tests** for API endpoints

---

## Related Documentation

- **Credit System**: `/services/ops-center/backend/credit_system.py`
- **LLM API**: `/services/ops-center/backend/litellm_api.py`
- **Test Script**: `/services/ops-center/backend/tests/test_tier_access.sh`
- **Creation Script**: `/services/ops-center/backend/scripts/create_test_users.py`

---

**Status**: ✅ Test Users Created and Ready for Testing
**Last Updated**: November 6, 2025
