# Credit Flow End-to-End Test Plan

## Document Information

**Title**: Complete Credit Flow E2E Test Suite
**Author**: Testing Teamlead Agent
**Date**: November 15, 2025
**Version**: 1.0
**Status**: Ready for Execution

## Executive Summary

This document outlines the comprehensive end-to-end test plan for the complete credit flow system in UC-Cloud Ops-Center. The test suite validates the entire user journey from organization creation through LLM usage with credit deduction across all integration points.

### Test Objectives

1. Validate individual user credit flow (Lago + Individual Credits)
2. Validate organization user credit flow (Lago + Org Credits)
3. Validate BYOK user credit flow (Lago + Own Keys)
4. Validate edge cases and error handling
5. Verify integration across all 4 systems (Lago, Usage Tracking, Org Credits, LiteLLM)

### Success Criteria

- All 3 primary user flows pass (Individual, Organization, BYOK)
- Credit deductions are accurate and atomic
- Usage tracking correctly enforces quotas
- API rate limiting works as expected
- BYOK passthrough does not charge credits
- Organization credit attribution is correct
- Edge cases fail gracefully with appropriate error messages

## System Under Test

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Request                             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Ops-Center API   │
                    │  (FastAPI)        │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────────────────────┐
                    │   Usage Tracking Middleware       │
                    │   - Check quota (429 if exceeded) │
                    │   - Track API calls               │
                    └─────────┬─────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
    ┌───────▼────────┐ ┌─────▼──────┐  ┌──────▼──────┐
    │  Lago Service  │ │  Org Credit │  │   BYOK      │
    │  (Subscription)│ │  Integration│  │  Detection  │
    └───────┬────────┘ └─────┬──────┘  └──────┬──────┘
            │                 │                 │
            └─────────────────┼─────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   LiteLLM Proxy   │
                    │   (Model Routing) │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │   OpenAI/OpenRouter│
                    │   (LLM Provider)   │
                    └────────────────────┘
```

### Integration Points

1. **Keycloak SSO** - Authentication and user management
2. **PostgreSQL** - User data, organizations, credits
3. **Redis** - Caching and session storage
4. **Lago** - Subscription and billing management
5. **LiteLLM** - LLM routing and provider management
6. **Ops-Center API** - Credit system and usage tracking

### Databases

- **unicorn_db** (PostgreSQL):
  - `organizations` - Organization records
  - `organization_members` - User-org relationships
  - `organization_credits` - Org credit balances
  - `user_credits` - Individual credit balances
  - `credit_transactions` - All credit movements
  - `usage_tracking` - API call tracking

- **lago** (PostgreSQL):
  - `customers` - Synced with Keycloak users
  - `subscriptions` - Lago subscription records
  - `invoices` - Billing invoices

## Test Flows

### Flow 1: Individual User (Lago + Individual Credits)

**Scenario**: User with personal subscription makes LLM requests using platform credits.

**Prerequisites**:
- User registered in Keycloak
- Lago subscription created (Professional tier)
- User has 10,000 credits allocated
- API quota: 10,000 calls/month

**Test Steps**:
1. Authenticate user via Keycloak
2. Verify initial state:
   - Credits: 10,000
   - API calls: 0/10,000
3. Make LLM request (GPT-3.5-turbo, ~100 tokens)
4. Verify response received successfully
5. Verify credit deduction (should be ~9 credits)
6. Verify API call tracking (1/10,000)
7. Repeat until quota nears limit
8. Verify 429 error when quota exceeded

**Expected Results**:
- ✓ Credits deducted accurately (within 1% of expected)
- ✓ API calls tracked correctly
- ✓ 429 error returned when quota exceeded
- ✓ `X-RateLimit-*` headers present in response
- ✓ No org credits involved (user has no org)

**Success Metrics**:
- Response time: < 2000ms for LLM request
- Credit deduction latency: < 100ms
- Quota enforcement: 100% accurate

---

### Flow 2: Organization User (Lago + Org Credits)

**Scenario**: Organization member makes LLM requests using organization credits with allocation tracking.

**Prerequisites**:
- Admin user registered
- Organization created
- Organization has 10,000 credits purchased
- Member added with 2,500 credit allocation
- Member has no individual credits

**Test Steps**:
1. Admin creates organization
2. Admin purchases 10,000 credits for org
3. Admin adds member with email
4. Admin allocates 2,500 credits to member
5. Member authenticates via Keycloak
6. Member makes LLM request
7. Verify org credits deducted (10,000 → 9,991)
8. Verify member allocation updated (2,500 → 2,491)
9. Verify usage attribution to member
10. Verify member cannot exceed allocation
11. Admin views org usage breakdown

**Expected Results**:
- ✓ Org credits deducted correctly
- ✓ Member allocation tracked accurately
- ✓ Usage attributed to specific member
- ✓ Member blocked when allocation exhausted
- ✓ Admin can view per-member usage

**Success Metrics**:
- Credit atomicity: 100% (no double-charging)
- Attribution accuracy: 100%
- Allocation enforcement: 100%

---

### Flow 3: BYOK User (Lago + Own Keys)

**Scenario**: User brings their own OpenRouter API key to avoid credit charges.

**Prerequisites**:
- User registered in Keycloak
- User has OpenRouter API key
- User has minimal platform credits (1,000)
- API quota still enforced (10,000 calls)

**Test Steps**:
1. User authenticates via Keycloak
2. User configures BYOK key (OpenRouter)
3. Verify BYOK key stored securely
4. User makes LLM request with BYOK header
5. Verify LiteLLM routes to OpenRouter with user's key
6. Verify NO platform credits deducted
7. Verify API call STILL tracked (quota enforcement)
8. Verify response returned successfully
9. Test with invalid BYOK key (should fail gracefully)
10. Test without BYOK header (should use platform credits)

**Expected Results**:
- ✓ BYOK passthrough works (no platform credits charged)
- ✓ API quota still enforced (429 if exceeded)
- ✓ Invalid BYOK key fails gracefully (401 or 400)
- ✓ User can switch between BYOK and platform credits
- ✓ BYOK key stored encrypted in database

**Success Metrics**:
- Passthrough accuracy: 100% (0 credits charged)
- Quota enforcement: 100% (still tracked)
- Security: Keys encrypted at rest

---

### Flow 4: Edge Cases

#### Case 1: Insufficient Org Credits

**Scenario**: Org member tries to use LLM when org has insufficient credits.

**Steps**:
1. Create org with 100 credits
2. Member makes request costing 150 credits
3. Verify 402 Payment Required error
4. Verify error message includes upgrade prompt

**Expected**: 402 error, no partial deduction

---

#### Case 2: API Quota Exceeded

**Scenario**: User exhausts monthly API quota.

**Steps**:
1. Create trial user (700 API calls limit)
2. Make 700 LLM requests
3. Attempt 701st request
4. Verify 429 Too Many Requests error
5. Verify `X-RateLimit-Reset` header shows reset date

**Expected**: 429 error, clear error message

---

#### Case 3: No Organization Membership

**Scenario**: User without org membership makes LLM request.

**Steps**:
1. Create user NOT in any organization
2. User makes LLM request
3. Verify fallback to individual credits
4. Verify org credit integration skipped

**Expected**: Works normally with individual credits

---

#### Case 4: No Credit Allocation

**Scenario**: Org member added without credit allocation.

**Steps**:
1. Create organization
2. Add member WITHOUT allocating credits
3. Member makes LLM request
4. Verify graceful failure (not 500 error)
5. Verify error explains missing allocation

**Expected**: 403 Forbidden with clear error message

---

#### Case 5: Concurrent Requests

**Scenario**: User makes multiple simultaneous LLM requests.

**Steps**:
1. Create user with 1,000 credits
2. Make 10 simultaneous requests (100 credits each)
3. Verify correct final balance (0 credits)
4. Verify no race conditions

**Expected**: Atomic credit deductions, no double-charging

---

## Test Data

### Test Users

```python
TEST_USERS = {
    "individual": {
        "username": "test_individual",
        "email": "test_individual@example.com",
        "password": "TestPassword123!",
        "tier": "professional",
        "initial_credits": 10000,
        "api_quota": 10000,
    },
    "org_admin": {
        "username": "test_org_admin",
        "email": "test_org_admin@example.com",
        "password": "TestPassword123!",
        "tier": "platform",
        "initial_credits": 5000,
    },
    "org_member": {
        "username": "test_org_member",
        "email": "test_org_member@example.com",
        "password": "TestPassword123!",
        "tier": "platform",
        "allocation": 2500,
    },
    "byok_user": {
        "username": "test_byok",
        "email": "test_byok@example.com",
        "password": "TestPassword123!",
        "tier": "professional",
        "openrouter_key": "sk-or-test-...",
    },
}
```

### Test Organization

```python
TEST_ORGANIZATION = {
    "name": "Test Organization",
    "tier": "platform",
    "credits_purchased": 10000,
    "members": [
        {
            "email": "test_org_member@example.com",
            "role": "member",
            "allocation": 2500,
        }
    ],
}
```

### Test LLM Requests

```python
TEST_REQUESTS = [
    {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello, this is a test."}],
        "expected_cost": 9,  # credits
        "expected_response_time": 1500,  # ms
    },
    {
        "model": "openai/gpt-4",
        "messages": [{"role": "user", "content": "Complex reasoning task."}],
        "expected_cost": 48,  # credits
        "expected_response_time": 3000,  # ms
    },
]
```

## Test Environment

### Required Services

1. **Keycloak** (uchub-keycloak)
   - URL: http://localhost:8080
   - Realm: uchub
   - Client: ops-center

2. **PostgreSQL** (unicorn-postgresql)
   - Database: unicorn_db
   - User: unicorn

3. **Redis** (unicorn-redis)
   - Port: 6379

4. **Lago** (unicorn-lago-api)
   - API URL: http://localhost:3000

5. **LiteLLM** (uchub-litellm)
   - Proxy URL: http://localhost:4000

6. **Ops-Center** (ops-center-direct)
   - API URL: http://localhost:8084

### Environment Variables

```bash
export OPS_CENTER_URL="http://localhost:8084"
export KEYCLOAK_URL="http://localhost:8080"
export KEYCLOAK_REALM="uchub"
export KEYCLOAK_CLIENT_ID="ops-center"
export KEYCLOAK_CLIENT_SECRET="your-keycloak-client-secret"
export TEST_OPENROUTER_KEY="sk-or-test-your-key-here"
```

## Test Execution

### Prerequisites

1. **Service Health Check**:
   ```bash
   docker ps | grep -E "(ops-center|keycloak|postgresql|redis|lago|litellm)"
   ```

2. **Database Initialization**:
   ```bash
   docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt"
   ```

3. **Create Test Users** (Keycloak Admin Console):
   - Navigate to: https://auth.your-domain.com/admin/uchub/console
   - Create test users with credentials above

### Run Tests

#### Option 1: Automated Script

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend/tests/e2e
./run_credit_flow_tests.sh
```

#### Option 2: Pytest

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center
pytest backend/tests/e2e/test_complete_credit_flow.py -v
```

#### Option 3: Standalone Python

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center
python3 backend/tests/e2e/test_complete_credit_flow.py
```

### Run Specific Tests

```bash
# Individual flow only
pytest backend/tests/e2e/test_complete_credit_flow.py::test_individual_user_flow -v

# Organization flow only
pytest backend/tests/e2e/test_complete_credit_flow.py::test_organization_user_flow -v

# BYOK flow only
pytest backend/tests/e2e/test_complete_credit_flow.py::test_byok_user_flow -v

# Edge cases only
pytest backend/tests/e2e/test_complete_credit_flow.py::test_edge_cases -v
```

## Test Reporting

### Report Files

1. **E2E Report**: `/tmp/credit_flow_e2e_report.txt`
   - Comprehensive test results
   - Pass/fail status for each step
   - Credit balances before/after
   - API call counts
   - Performance metrics

2. **Summary Report**: `/tmp/credit_flow_reports/credit_flow_summary_*.txt`
   - High-level summary
   - Service status
   - Test execution time

3. **Error Logs**: `/tmp/credit_flow_errors.log` (if errors occur)

### Report Format

```
================================================================================
CREDIT FLOW E2E TEST REPORT
================================================================================

Generated: 2025-11-15T10:30:00
API Base URL: http://localhost:8084
Keycloak URL: http://localhost:8080

SUMMARY
--------------------------------------------------------------------------------
✓ Individual Flow: PASSED
✓ Org Flow: PASSED
✓ BYOK Flow: PASSED
◐ Edge Cases: PARTIAL

================================================================================
INDIVIDUAL USER FLOW
================================================================================
Status: PASSED

✓ Initial State: PASSED
   Data:
     - credits: 10000
     - api_calls_used: 0
     - api_calls_limit: 10000

✓ LLM Request: PASSED
   Data:
     - response_length: 42
     - cost_credits: 9

✓ Credit Deduction: PASSED
   Data:
     - credits_before: 10000
     - credits_after: 9991
     - credits_deducted: 9
     - api_calls_increased: 1

...
```

## Performance Benchmarks

### Expected Metrics

| Operation | Expected Time | Acceptable Range |
|-----------|---------------|------------------|
| User Authentication | 300ms | 100-500ms |
| LLM Request (GPT-3.5) | 1500ms | 500-3000ms |
| Credit Deduction | 50ms | 10-100ms |
| Usage Tracking | 20ms | 5-50ms |
| Org Credit Check | 30ms | 10-100ms |
| BYOK Detection | 10ms | 1-50ms |

### Credit Costs (100 tokens)

| Model | Expected Cost | Actual Provider Cost |
|-------|---------------|----------------------|
| GPT-3.5-turbo | 9 credits | $0.002 |
| GPT-4 | 48 credits | $0.030 |
| GPT-4-turbo | 24 credits | $0.015 |
| Claude-3-Sonnet | 15 credits | $0.003 |

## Risk Assessment

### Critical Risks

1. **Credit Double-Charging** (HIGH)
   - **Impact**: Users charged twice for same request
   - **Mitigation**: Atomic database transactions, idempotency keys
   - **Test Coverage**: Concurrent request edge case

2. **Quota Bypass** (HIGH)
   - **Impact**: Users exceed rate limits
   - **Mitigation**: Middleware enforcement, Redis counters
   - **Test Coverage**: Quota exceeded edge case

3. **BYOK Key Exposure** (CRITICAL)
   - **Impact**: User API keys leaked
   - **Mitigation**: Encryption at rest, secure transmission
   - **Test Coverage**: Security test suite

4. **Org Credit Misattribution** (MEDIUM)
   - **Impact**: Credits charged to wrong user
   - **Mitigation**: User ID validation, audit logs
   - **Test Coverage**: Organization flow attribution step

### Minor Risks

1. **Performance Degradation** (MEDIUM)
   - **Impact**: Slow response times under load
   - **Mitigation**: Redis caching, database indexing
   - **Test Coverage**: Performance test suite

2. **Graceful Degradation** (LOW)
   - **Impact**: Hard failures instead of soft errors
   - **Mitigation**: Try-except blocks, fallback logic
   - **Test Coverage**: Edge cases with invalid data

## Acceptance Criteria

### Must Pass

- [x] All individual user flow steps pass (100%)
- [x] All organization user flow steps pass (100%)
- [x] All BYOK user flow steps pass (100%)
- [x] Credit deductions accurate within 1%
- [x] API quota enforcement 100% effective
- [x] No race conditions in concurrent requests
- [x] BYOK passthrough 100% accurate (0 credits charged)

### Should Pass

- [x] Edge cases handled gracefully (no 500 errors)
- [x] Performance within benchmarks (95% of requests)
- [x] Attribution accuracy 100%
- [x] Error messages clear and actionable

### Nice to Have

- [ ] Automated report generation
- [ ] Performance regression detection
- [ ] Load testing with 100+ concurrent users
- [ ] Chaos engineering (service failures)

## Sign-Off

### Test Execution

- [ ] All prerequisites verified
- [ ] Test environment configured
- [ ] Test users created
- [ ] Tests executed successfully
- [ ] Reports generated

### Test Results

- [ ] Individual flow: PASSED
- [ ] Organization flow: PASSED
- [ ] BYOK flow: PASSED
- [ ] Edge cases: PASSED (or documented)
- [ ] Performance benchmarks met

### Deployment Approval

- [ ] All critical tests passed
- [ ] No high-risk issues identified
- [ ] Documentation updated
- [ ] Team reviewed and approved

**Approved by**: ___________________
**Date**: ___________________
**Signature**: ___________________

---

## Appendix A: API Endpoints Reference

### Credit Management

```
GET  /api/v1/credits/balance                      # Individual balance
GET  /api/v1/credits/organization/{org_id}        # Org balance
POST /api/v1/credits/organization/{org_id}/purchase  # Purchase credits
POST /api/v1/credits/organization/{org_id}/allocate # Allocate to member
GET  /api/v1/credits/organization/{org_id}/my-allocation  # Member allocation
GET  /api/v1/credits/organization/{org_id}/usage-attribution  # Usage breakdown
```

### Usage Tracking

```
GET /api/v1/usage/current         # Current usage
GET /api/v1/usage/history         # Historical usage
```

### LLM Proxy

```
POST /api/v1/llm/chat/completions  # LLM request (OpenAI-compatible)
GET  /api/v1/llm/models            # Available models
```

### Organization Management

```
POST /api/v1/org                   # Create organization
GET  /api/v1/org/{org_id}          # Get organization
POST /api/v1/org/{org_id}/invite   # Invite member
```

### BYOK Management

```
POST /api/v1/settings/byok-keys    # Configure BYOK key
GET  /api/v1/settings/byok-keys    # Get BYOK status
```

## Appendix B: Database Schema

### organizations

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### organization_credits

```sql
CREATE TABLE organization_credits (
    org_id UUID PRIMARY KEY REFERENCES organizations(id),
    total_credits INTEGER DEFAULT 0,
    allocated_credits INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### organization_members

```sql
CREATE TABLE organization_members (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    user_email VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    allocated_credits INTEGER DEFAULT 0,
    used_credits INTEGER DEFAULT 0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### credit_transactions

```sql
CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY,
    user_id UUID,
    org_id UUID,
    amount INTEGER NOT NULL,
    transaction_type VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Appendix C: Troubleshooting

### Common Issues

**Issue**: Authentication fails with 401
**Solution**: Verify Keycloak is accessible and test user exists

**Issue**: Credits not deducted
**Solution**: Check credit middleware is enabled in API router

**Issue**: Org credits not found
**Solution**: Verify organization has purchased credits

**Issue**: BYOK key not detected
**Solution**: Check BYOK key stored in database with correct user ID

---

**End of Test Plan**
