# Epic 1.8: Credit & Usage Metering System - Test Plan

**Date**: October 24, 2025
**Status**: Ready for Testing
**Estimated Time**: 4-6 hours
**Priority Order**: P0 → P1 → P2 → P3

---

## 🎯 Testing Goals

1. **Verify Core Functionality** - All credit operations work correctly
2. **Validate Business Logic** - Tier-based rules enforced properly
3. **Ensure Data Integrity** - Transactions are atomic and accurate
4. **Confirm Security** - Authorization and encryption working
5. **Test User Experience** - Frontend components load and function

---

## 📊 Test Priorities

- **P0 (Blocker)** - Must pass before ANY deployment
- **P1 (Critical)** - Core features, must pass before production
- **P2 (Important)** - Should work, but non-blocking
- **P3 (Nice-to-have)** - Polish features, can fix later

---

## 🧪 Test Categories

### Category 1: Database Schema (P0 - 15 minutes)

**Test 1.1: Verify All Tables Exist**
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  SELECT tablename FROM pg_tables
  WHERE schemaname = 'public'
  AND tablename IN ('user_credits', 'credit_transactions', 'openrouter_accounts', 'coupon_codes', 'usage_events')
  ORDER BY tablename;
"
```
**Expected**: 5 rows returned
**Actual**: ___________
**Pass/Fail**: ___________

**Test 1.2: Verify Indexes Created**
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  SELECT indexname FROM pg_indexes
  WHERE schemaname = 'public'
  AND tablename IN ('user_credits', 'credit_transactions', 'openrouter_accounts', 'coupon_codes', 'usage_events')
  ORDER BY indexname;
"
```
**Expected**: 15+ indexes
**Actual**: ___________
**Pass/Fail**: ___________

**Test 1.3: Verify Constraints**
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d user_credits"
```
**Expected**:
- `credits_remaining_positive` CHECK constraint
- `valid_tier` CHECK constraint
- `user_id` UNIQUE constraint
**Actual**: ___________
**Pass/Fail**: ___________

---

### Category 2: API Endpoints - Public (P0 - 10 minutes)

**Test 2.1: Tier Comparison (Public)**
```bash
curl -s http://localhost:8084/api/v1/credits/tiers/compare | python3 -m json.tool
```
**Expected**:
- 200 OK status
- 4 tiers returned (trial, starter, professional, enterprise)
- Each tier has: name, price_monthly, credits_monthly, features[]
**Actual**: ___________
**Pass/Fail**: ___________

**Test 2.2: API Documentation Includes Credit Endpoints**
```bash
curl -s http://localhost:8084/docs | grep -i "credit"
```
**Expected**: OpenAPI docs include /api/v1/credits/* endpoints
**Actual**: ___________
**Pass/Fail**: ___________

---

### Category 3: Authentication & Authorization (P0 - 20 minutes)

**Setup: Get Auth Token**
```bash
# Login via Keycloak to get JWT token
# Store token in variable for subsequent tests
TOKEN="<paste-token-here>"
```

**Test 3.1: Balance Endpoint Requires Auth**
```bash
# Without token (should fail)
curl -s http://localhost:8084/api/v1/credits/balance

# With token (should succeed)
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8084/api/v1/credits/balance | python3 -m json.tool
```
**Expected**:
- No token: 401 Unauthorized
- With token: 200 OK with balance data
**Actual**: ___________
**Pass/Fail**: ___________

**Test 3.2: Admin Endpoints Require Admin Role**
```bash
# Regular user trying admin endpoint (should fail)
curl -s -H "Authorization: Bearer $USER_TOKEN" \
  -X POST http://localhost:8084/api/v1/credits/allocate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user", "amount": 100}'

# Admin user trying admin endpoint (should succeed)
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  -X POST http://localhost:8084/api/v1/credits/allocate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user", "amount": 100}'
```
**Expected**:
- Regular user: 403 Forbidden
- Admin user: 200 OK
**Actual**: ___________
**Pass/Fail**: ___________

---

### Category 4: Credit Operations (P1 - 30 minutes)

**Test 4.1: Get User Balance (Fresh User)**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8084/api/v1/credits/balance | python3 -m json.tool
```
**Expected**:
```json
{
  "user_id": "test-user-id",
  "credits_remaining": 0.0,
  "credits_allocated": 0.0,
  "tier": "free",
  "last_reset": "<timestamp>",
  "created_at": "<timestamp>",
  "updated_at": "<timestamp>"
}
```
**Actual**: ___________
**Pass/Fail**: ___________

**Test 4.2: Allocate Credits (Admin)**
```bash
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  -X POST http://localhost:8084/api/v1/credits/allocate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-id",
    "amount": 50.0,
    "tier": "starter",
    "reason": "Initial allocation"
  }' | python3 -m json.tool
```
**Expected**:
- 200 OK
- credits_remaining: 50.0
- tier: "starter"
**Actual**: ___________
**Pass/Fail**: ___________

**Test 4.3: Deduct Credits (Internal)**
```bash
curl -s -H "Authorization: Bearer $INTERNAL_TOKEN" \
  -X POST http://localhost:8084/api/v1/credits/deduct \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-id",
    "amount": 5.0,
    "reason": "LLM API call",
    "metadata": {
      "model": "gpt-4",
      "tokens": 1000,
      "provider": "openai"
    }
  }' | python3 -m json.tool
```
**Expected**:
- 200 OK
- credits_remaining: 45.0 (50 - 5)
- Transaction recorded in credit_transactions
**Actual**: ___________
**Pass/Fail**: ___________

**Test 4.4: Refund Credits (Admin)**
```bash
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  -X POST http://localhost:8084/api/v1/credits/refund \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-id",
    "amount": 5.0,
    "reason": "Service error refund"
  }' | python3 -m json.tool
```
**Expected**:
- 200 OK
- credits_remaining: 50.0 (45 + 5)
**Actual**: ___________
**Pass/Fail**: ___________

**Test 4.5: Cannot Deduct More Than Balance**
```bash
curl -s -H "Authorization: Bearer $INTERNAL_TOKEN" \
  -X POST http://localhost:8084/api/v1/credits/deduct \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-id",
    "amount": 100.0,
    "reason": "Large API call"
  }'
```
**Expected**:
- 400 Bad Request or 402 Payment Required
- Error message: "Insufficient credits"
**Actual**: ___________
**Pass/Fail**: ___________

---

### Category 5: Transaction History (P1 - 15 minutes)

**Test 5.1: Get Transaction History**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8084/api/v1/credits/transactions?limit=10" | python3 -m json.tool
```
**Expected**:
- 200 OK
- Array of transactions
- Each transaction has: id, user_id, amount, transaction_type, created_at
- Transactions sorted by created_at DESC
**Actual**: ___________
**Pass/Fail**: ___________

**Test 5.2: Verify Transaction Audit Trail**
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  SELECT user_id, amount, transaction_type, created_at
  FROM credit_transactions
  WHERE user_id = 'test-user-id'
  ORDER BY created_at DESC
  LIMIT 5;
"
```
**Expected**:
- Allocation transaction (+50.0)
- Deduction transaction (-5.0)
- Refund transaction (+5.0)
- All timestamps accurate
**Actual**: ___________
**Pass/Fail**: ___________

---

### Category 6: Coupon System (P1 - 20 minutes)

**Test 6.1: Create Coupon (Admin)**
```bash
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  -X POST http://localhost:8084/api/v1/coupons/create \
  -H "Content-Type: application/json" \
  -d '{
    "code": "WELCOME10",
    "discount_type": "fixed",
    "discount_value": 10.0,
    "max_uses": 100,
    "expires_at": "2025-12-31T23:59:59Z"
  }' | python3 -m json.tool
```
**Expected**:
- 200 OK
- Coupon created with code "WELCOME10"
**Actual**: ___________
**Pass/Fail**: ___________

**Test 6.2: Validate Coupon**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8084/api/v1/coupons/validate?code=WELCOME10" | python3 -m json.tool
```
**Expected**:
- 200 OK
- valid: true
- discount_value: 10.0
**Actual**: ___________
**Pass/Fail**: ___________

**Test 6.3: Redeem Coupon**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  -X POST http://localhost:8084/api/v1/coupons/redeem \
  -H "Content-Type: application/json" \
  -d '{
    "code": "WELCOME10"
  }' | python3 -m json.tool
```
**Expected**:
- 200 OK
- Credits increased by 10.0
- Coupon times_used incremented
**Actual**: ___________
**Pass/Fail**: ___________

**Test 6.4: Cannot Redeem Expired Coupon**
```bash
# Create expired coupon
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  -X POST http://localhost:8084/api/v1/coupons/create \
  -H "Content-Type: application/json" \
  -d '{
    "code": "EXPIRED",
    "discount_type": "fixed",
    "discount_value": 5.0,
    "expires_at": "2020-01-01T00:00:00Z"
  }'

# Try to redeem
curl -s -H "Authorization: Bearer $TOKEN" \
  -X POST http://localhost:8084/api/v1/coupons/redeem \
  -H "Content-Type: application/json" \
  -d '{"code": "EXPIRED"}'
```
**Expected**:
- 400 Bad Request
- Error: "Coupon expired"
**Actual**: ___________
**Pass/Fail**: ___________

---

### Category 7: Usage Metering (P2 - 20 minutes)

**Test 7.1: Track Usage Event**
```bash
curl -s -H "Authorization: Bearer $INTERNAL_TOKEN" \
  -X POST http://localhost:8084/api/v1/metering/track \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-id",
    "event_type": "llm_completion",
    "service": "litellm",
    "provider": "openai",
    "model": "gpt-4",
    "tokens_used": 1500,
    "cost": 0.045,
    "power_level": "balanced",
    "success": true
  }' | python3 -m json.tool
```
**Expected**:
- 200 OK
- Event recorded in usage_events table
**Actual**: ___________
**Pass/Fail**: ___________

**Test 7.2: Get Usage Summary**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8084/api/v1/metering/summary?days=7" | python3 -m json.tool
```
**Expected**:
- 200 OK
- total_events, total_tokens, total_cost
- Breakdown by service
**Actual**: ___________
**Pass/Fail**: ___________

**Test 7.3: Get Usage by Model**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8084/api/v1/metering/by-model?days=30" | python3 -m json.tool
```
**Expected**:
- 200 OK
- Array of models with usage stats
- Sorted by usage descending
**Actual**: ___________
**Pass/Fail**: ___________

---

### Category 8: OpenRouter BYOK (P2 - 25 minutes)

**Test 8.1: Create OpenRouter Account**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  -X POST http://localhost:8084/api/v1/openrouter/create-account \
  -H "Content-Type: application/json" \
  -d '{
    "openrouter_api_key": "sk-or-test-key-12345"
  }' | python3 -m json.tool
```
**Expected**:
- 200 OK
- Account created
- API key encrypted with Fernet
**Actual**: ___________
**Pass/Fail**: ___________

**Test 8.2: Verify API Key Encryption**
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  SELECT user_id, openrouter_api_key_encrypted, created_at
  FROM openrouter_accounts
  WHERE user_id = 'test-user-id';
"
```
**Expected**:
- API key is encrypted (not plaintext)
- Starts with "gAAAAA" (Fernet encryption)
**Actual**: ___________
**Pass/Fail**: ___________

**Test 8.3: Get OpenRouter Account Info**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8084/api/v1/openrouter/account | python3 -m json.tool
```
**Expected**:
- 200 OK
- user_id, free_credits, last_synced
- API key NOT returned (security)
**Actual**: ___________
**Pass/Fail**: ___________

**Test 8.4: Sync Free Credits Balance**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  -X POST http://localhost:8084/api/v1/openrouter/sync-balance | python3 -m json.tool
```
**Expected**:
- 200 OK (or 501 if not implemented yet)
- free_credits updated from OpenRouter API
**Actual**: ___________
**Pass/Fail**: ___________

---

### Category 9: Frontend Testing (P1 - 30 minutes)

**Test 9.1: Credit Dashboard Loads**
1. Navigate to https://your-domain.com/admin/credits
2. Verify page loads without errors
3. Check browser console for errors (F12)

**Expected**:
- Page loads in < 3 seconds
- No JavaScript errors
- 4 tabs visible: Overview, Usage Metrics, Transactions, Account
**Actual**: ___________
**Pass/Fail**: ___________

**Test 9.2: Overview Tab**
1. Click "Overview" tab
2. Verify credit balance displays
3. Verify tier badge shows current tier
4. Check progress bars render

**Expected**:
- Balance shows numeric value
- Tier badge shows one of: Trial, Starter, Professional, Enterprise
- Progress bars show credit usage percentage
**Actual**: ___________
**Pass/Fail**: ___________

**Test 9.3: Transactions Tab**
1. Click "Transactions" tab
2. Verify transaction history table loads
3. Check pagination works
4. Test filters (type, date range)

**Expected**:
- Table shows recent transactions
- Columns: Date, Type, Amount, Balance After, Description
- Pagination controls functional
- Filters update results
**Actual**: ___________
**Pass/Fail**: ___________

**Test 9.4: Usage Metrics Tab**
1. Click "Usage Metrics" tab
2. Verify charts render (Chart.js)
3. Check model usage breakdown
4. Test date range selector

**Expected**:
- Charts display without errors
- Model usage bar chart shows data
- Date range selector updates charts
**Actual**: ___________
**Pass/Fail**: ___________

**Test 9.5: Tier Comparison Page**
1. Navigate to https://your-domain.com/admin/credits/tiers
2. Verify all 4 tiers display
3. Check "Select Plan" buttons

**Expected**:
- 4 pricing cards visible (Trial, Starter, Professional, Enterprise)
- Each card shows: price, features, CTA button
- Current tier highlighted
**Actual**: ___________
**Pass/Fail**: ___________

**Test 9.6: Coupon Redemption Component**
1. Navigate to credit dashboard
2. Find coupon redemption form
3. Enter code "WELCOME10"
4. Submit form

**Expected**:
- Form accepts input
- Submit button triggers API call
- Success/error message displays
- Balance updates on success
**Actual**: ___________
**Pass/Fail**: ___________

---

### Category 10: Security Testing (P1 - 20 minutes)

**Test 10.1: SQL Injection Prevention**
```bash
# Try SQL injection in user_id parameter
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  -X POST http://localhost:8084/api/v1/credits/allocate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test'; DROP TABLE user_credits; --",
    "amount": 100.0
  }'
```
**Expected**:
- Request rejected or sanitized
- Table NOT dropped
**Actual**: ___________
**Pass/Fail**: ___________

**Test 10.2: XSS Prevention**
```bash
# Try XSS in coupon code
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  -X POST http://localhost:8084/api/v1/coupons/create \
  -H "Content-Type: application/json" \
  -d '{
    "code": "<script>alert(\"XSS\")</script>",
    "discount_type": "fixed",
    "discount_value": 10.0
  }'
```
**Expected**:
- Script tags escaped or rejected
- Code stored safely
**Actual**: ___________
**Pass/Fail**: ___________

**Test 10.3: API Key Encryption Strength**
```bash
# Verify Fernet encryption is used
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  SELECT LENGTH(openrouter_api_key_encrypted) as encrypted_length,
         LEFT(openrouter_api_key_encrypted, 10) as encrypted_prefix
  FROM openrouter_accounts
  LIMIT 1;
"
```
**Expected**:
- Encrypted length > original key length
- Prefix starts with "gAAAAA" (Fernet signature)
**Actual**: ___________
**Pass/Fail**: ___________

**Test 10.4: Rate Limiting (if implemented)**
```bash
# Make 100 rapid requests
for i in {1..100}; do
  curl -s -H "Authorization: Bearer $TOKEN" \
    http://localhost:8084/api/v1/credits/balance > /dev/null &
done
wait
```
**Expected**:
- Some requests return 429 Too Many Requests
- Server doesn't crash
**Actual**: ___________
**Pass/Fail**: ___________

---

### Category 11: Performance Testing (P2 - 15 minutes)

**Test 11.1: API Response Time**
```bash
# Measure response time for balance endpoint
time curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8084/api/v1/credits/balance > /dev/null
```
**Expected**: < 200ms
**Actual**: ___________
**Pass/Fail**: ___________

**Test 11.2: Database Query Performance**
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  EXPLAIN ANALYZE
  SELECT * FROM credit_transactions
  WHERE user_id = 'test-user-id'
  ORDER BY created_at DESC
  LIMIT 20;
"
```
**Expected**:
- Uses index scan (not seq scan)
- Execution time < 10ms
**Actual**: ___________
**Pass/Fail**: ___________

**Test 11.3: Concurrent Credit Deductions**
```bash
# Simulate 10 concurrent deductions
for i in {1..10}; do
  curl -s -H "Authorization: Bearer $INTERNAL_TOKEN" \
    -X POST http://localhost:8084/api/v1/credits/deduct \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"test-user-id\", \"amount\": 1.0, \"reason\": \"test-$i\"}" &
done
wait

# Check final balance
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8084/api/v1/credits/balance | python3 -m json.tool
```
**Expected**:
- All deductions succeed (no race conditions)
- Final balance = initial - 10.0
**Actual**: ___________
**Pass/Fail**: ___________

---

### Category 12: Integration Flows (P1 - 30 minutes)

**Test 12.1: New User Signup Flow**
1. Create new user in Keycloak
2. User logs into ops-center
3. User allocated trial credits automatically
4. User redeems WELCOME10 coupon
5. User uses credits for LLM call
6. User views transaction history

**Expected**:
- User starts with 0 credits
- Trial allocation gives 5 credits
- WELCOME10 adds 10 credits (total 15)
- LLM call deducts credits
- Transaction history shows all events
**Actual**: ___________
**Pass/Fail**: ___________

**Test 12.2: Tier Upgrade Flow**
1. User starts on Trial tier
2. User navigates to tier comparison
3. User selects Professional tier
4. Credits allocated based on new tier
5. Monthly cap updated

**Expected**:
- Tier switches from trial → professional
- Credits allocated: 60.0
- Monthly cap set to 60.0
**Actual**: ___________
**Pass/Fail**: ___________

**Test 12.3: Monthly Credit Reset**
```bash
# Manually trigger reset for test user
# (This may require admin script or SQL update)
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  UPDATE user_credits
  SET last_reset = NOW() - INTERVAL '31 days',
      credits_remaining = 5.0
  WHERE user_id = 'test-user-id';
"

# Trigger reset logic (call API or cron job)
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  -X POST http://localhost:8084/api/v1/credits/reset-monthly

# Check updated balance
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8084/api/v1/credits/balance | python3 -m json.tool
```
**Expected**:
- credits_remaining reset to credits_allocated (based on tier)
- last_reset updated to current date
**Actual**: ___________
**Pass/Fail**: ___________

---

## 🎯 Acceptance Criteria

### Must Pass Before Deployment (P0 + P1)

**Database**: ✅ / ❌
- [ ] All 5 tables exist
- [ ] All indexes created
- [ ] Constraints enforced

**API Endpoints**: ✅ / ❌
- [ ] Public tier comparison works
- [ ] Authentication required for user endpoints
- [ ] Admin endpoints require admin role
- [ ] Credit operations (allocate, deduct, refund) work
- [ ] Transaction history accurate
- [ ] Coupon creation and redemption work

**Frontend**: ✅ / ❌
- [ ] Credit dashboard loads without errors
- [ ] All 4 tabs functional
- [ ] Tier comparison page displays correctly
- [ ] Charts render properly

**Security**: ✅ / ❌
- [ ] API keys encrypted with Fernet
- [ ] SQL injection prevented
- [ ] XSS prevented
- [ ] Authorization enforced

**Integration**: ✅ / ❌
- [ ] New user signup flow works end-to-end
- [ ] Tier upgrade flow works
- [ ] Transaction audit trail complete

---

## 📋 Test Execution Checklist

### Pre-Testing Setup (10 minutes)
- [ ] Get Keycloak auth tokens (admin and regular user)
- [ ] Create test user accounts (3-5 users with different tiers)
- [ ] Verify ops-center backend is running (`docker logs ops-center-direct`)
- [ ] Verify database is healthy (`docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT 1;"`)

### P0 Tests (30 minutes)
- [ ] Category 1: Database Schema
- [ ] Category 2: API Endpoints - Public
- [ ] Category 3: Authentication & Authorization

### P1 Tests (2-3 hours)
- [ ] Category 4: Credit Operations
- [ ] Category 5: Transaction History
- [ ] Category 6: Coupon System
- [ ] Category 9: Frontend Testing
- [ ] Category 10: Security Testing
- [ ] Category 12: Integration Flows

### P2 Tests (1-2 hours)
- [ ] Category 7: Usage Metering
- [ ] Category 8: OpenRouter BYOK
- [ ] Category 11: Performance Testing

### P3 Tests (Optional)
- [ ] Edge cases (negative amounts, invalid tiers)
- [ ] Concurrent user scenarios
- [ ] Load testing (100+ users)
- [ ] Mobile responsiveness

---

## 🐛 Issue Tracking Template

| Test ID | Priority | Description | Status | Notes |
|---------|----------|-------------|--------|-------|
| 4.5 | P1 | Insufficient credits error | ❌ Fail | Returns 500 instead of 400 |
| 9.3 | P1 | Transaction pagination | ✅ Pass | Works as expected |
| ... | ... | ... | ... | ... |

---

## 📊 Test Summary Report Template

```
Epic 1.8 Test Execution Summary
Date: __________
Tester: __________

P0 Tests:
- Total: 5
- Passed: ___
- Failed: ___
- Blocked: ___

P1 Tests:
- Total: 20
- Passed: ___
- Failed: ___
- Blocked: ___

P2 Tests:
- Total: 10
- Passed: ___
- Failed: ___
- Blocked: ___

Critical Issues Found: ___
Blocker Issues: ___

Recommendation:
[ ] Ready for production deployment
[ ] Needs minor fixes (deploy with known issues)
[ ] Needs major fixes (block deployment)

Next Steps:
1. _______________
2. _______________
3. _______________
```

---

## 🚀 Deployment Decision Matrix

| Scenario | P0 Pass Rate | P1 Pass Rate | Decision |
|----------|--------------|--------------|----------|
| Best Case | 100% | 100% | ✅ Deploy immediately |
| Good Case | 100% | ≥ 80% | ✅ Deploy with known issues documented |
| Acceptable | 100% | ≥ 60% | ⚠️ Deploy to staging, fix P1 failures |
| Risky | < 100% | Any % | ❌ Block deployment, fix P0 failures first |

---

## 📝 Notes

- Store all curl commands in a shell script for easy re-testing
- Use `jq` instead of `python3 -m json.tool` for better formatting (if installed)
- Document any test data created (user IDs, coupon codes) for cleanup
- Take screenshots of frontend tests for documentation
- Record API response times for performance baseline

---

**Testing begins after this plan is approved.**
**Estimated total testing time: 4-6 hours**
**Required personnel: 1 QA tester + 1 developer (for fixing issues)**
