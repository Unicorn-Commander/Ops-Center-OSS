# End-to-End Testing Guide: Complete Credit Flow

## Overview

This E2E test suite validates the complete user journey from organization creation through LLM usage with credit deduction across all integration points.

## Test Scope

### Systems Under Test

1. **Keycloak SSO** - User authentication and session management
2. **PostgreSQL** - User data, organizations, credit balances
3. **Redis** - Caching and session storage
4. **Lago** - Subscription management and billing
5. **LiteLLM** - LLM routing and provider management
6. **Ops-Center API** - Credit system and usage tracking

### Test Flows

#### Flow 1: Individual User (Lago + Individual Credits)
```
User signs up
  → Lago subscription created (Professional $49/mo)
  → User gets tier features (10,000 API calls)
  → User makes LLM request
  → Usage Tracking checks quota (9,999/10,000)
  → Individual credits deducted
  → LiteLLM routes to provider
  → Response returned
```

#### Flow 2: Organization User (Lago + Org Credits)
```
Admin creates organization
  → Org subscription created (Platform $50/mo)
  → Org purchases 10,000 credits
  → Admin allocates 2,500 credits to user
  → User makes LLM request
  → Usage Tracking checks quota
  → Org credit integration checks org credits
  → Org credits deducted (2,500 → 2,491)
  → LiteLLM routes to provider
  → Credit usage attributed to user
  → Response returned
```

#### Flow 3: BYOK User (Lago + Own Keys)
```
User adds OpenRouter API key
  → User makes LLM request
  → Usage Tracking checks quota (still enforced!)
  → LiteLLM detects BYOK key
  → Routes to OpenRouter with user's key
  → NO credits deducted
  → Response returned
```

#### Flow 4: Edge Cases
- Insufficient org credits (should return 402)
- API quota exceeded (should return 429)
- No organization membership (fallback to individual credits)
- Org exists but no credit allocation (should fail gracefully)

## Prerequisites

### 1. Running Services

Ensure all services are running:

```bash
# Check Ops-Center
docker ps | grep ops-center-direct

# Check Keycloak
docker ps | grep uchub-keycloak

# Check PostgreSQL
docker ps | grep unicorn-postgresql

# Check Redis
docker ps | grep unicorn-redis

# Check Lago
docker ps | grep lago

# Check LiteLLM
docker ps | grep litellm
```

### 2. Test User Creation

Create test users in Keycloak admin console (https://auth.unicorncommander.ai/admin/uchub/console):

**Individual User**:
- Username: `test_individual`
- Email: `test_individual@example.com`
- Password: `TestPassword123!`
- Tier: `professional`

**Org Admin**:
- Username: `test_org_admin`
- Email: `test_org_admin@example.com`
- Password: `TestPassword123!`
- Tier: `platform`

**Org Member**:
- Username: `test_org_member`
- Email: `test_org_member@example.com`
- Password: `TestPassword123!`
- Tier: `platform`

**BYOK User**:
- Username: `test_byok`
- Email: `test_byok@example.com`
- Password: `TestPassword123!`
- Tier: `professional`

### 3. Environment Variables

Set these environment variables before running tests:

```bash
export OPS_CENTER_URL="http://localhost:8084"
export KEYCLOAK_URL="http://localhost:8080"
export TEST_OPENROUTER_KEY="sk-or-test-your-key-here"
```

### 4. Database Setup

Ensure test database is initialized:

```bash
# Connect to PostgreSQL
docker exec -it unicorn-postgresql psql -U unicorn -d unicorn_db

# Verify tables exist
\dt

# Expected tables:
# - organizations
# - organization_members
# - organization_credits
# - user_credits
# - credit_transactions
# - usage_tracking
```

## Running Tests

### Option 1: Run All Tests with Pytest

```bash
cd /opt/ops-center

# Run all E2E tests
pytest backend/tests/e2e/test_complete_credit_flow.py -v

# Run specific flow
pytest backend/tests/e2e/test_complete_credit_flow.py::test_individual_user_flow -v

# Run with detailed output
pytest backend/tests/e2e/test_complete_credit_flow.py -vv -s
```

### Option 2: Run Standalone

```bash
cd /opt/ops-center

# Run test suite directly
python3 backend/tests/e2e/test_complete_credit_flow.py
```

### Option 3: Docker Container

```bash
# Run tests inside ops-center container
docker exec ops-center-direct pytest /app/tests/e2e/test_complete_credit_flow.py -v
```

## Expected Output

### Successful Test Run

```
================================================================================
CREDIT FLOW E2E TEST SUITE - SETUP
================================================================================

1. Authenticating test users...
   ✓ individual: Authenticated
   ✓ org_admin: Authenticated
   ✓ org_member: Authenticated
   ✓ byok_user: Authenticated

2. Creating test organization...
   ✓ Organization created: org_e9c5241a-fff4-45e1-972b-f5c53cdc64f0

3. Purchasing organization credits...
   ✓ Purchased 10,000 credits for organization

4. Adding organization member...
   ✓ Added member with 2,500 credit allocation

5. Configuring BYOK user...
   ✓ BYOK configured (OpenRouter)

✓ Setup complete!

================================================================================
TEST FLOW 1: INDIVIDUAL USER
================================================================================

Step 1: Checking initial state...
   Credits: 10000
   API Calls: 0/10000

Step 2: Making LLM request...
   ✓ Response received
   Cost: 9 credits

Step 3: Verifying credit deduction...
   ✓ Credits deducted: 9
   ✓ API call tracked: 1/10000

Step 4: Testing quota enforcement...
   ⊘ Quota not reached yet, skipping enforcement test

✓ INDIVIDUAL USER FLOW: PASSED

================================================================================
TEST FLOW 2: ORGANIZATION USER
================================================================================

Step 1: Checking initial organization state...
   Org Credits: 10000
   Allocated: 2500

Step 2: Checking member allocation...
   Allocated: 2500
   Used: 0
   Remaining: 2500

Step 3: Making LLM request as org member...
   ✓ Response received
   Cost: 9 credits

Step 4: Verifying org credit deduction...
   ✓ Org credits deducted: 9

Step 5: Verifying member allocation updated...
   ✓ Member usage tracked: 9 credits

Step 6: Verifying credit attribution to user...
   ✓ Usage attributed to test_org_member@example.com
   Credits: 9
   API Calls: 1

✓ ORGANIZATION USER FLOW: PASSED

================================================================================
TEST FLOW 3: BYOK USER
================================================================================

Step 1: Verifying BYOK configuration...
   ✓ OpenRouter key configured

Step 2: Checking initial state...
   Credits: 1000
   API Calls: 0/10000

Step 3: Making LLM request with BYOK...
   ✓ Response received
   BYOK Used: True
   Cost: 0 credits (should be 0)

Step 4: Verifying NO credit deduction...
   ✓ No credits deducted (BYOK passthrough)
   ✓ API call still tracked: 1/10000

✓ BYOK USER FLOW: PASSED

================================================================================
TEST FLOW 4: EDGE CASES
================================================================================

Case 1: Testing insufficient org credits...
   ⊘ Manual test required

Case 2: Testing API quota exceeded...
   ⊘ Manual test required

Case 3: Testing no organization membership...
   ✓ Fallback to individual credits worked

Case 4: Testing org with no credit allocation...
   ⊘ Manual test required

✓ EDGE CASES: PARTIAL (manual tests required)

================================================================================
CREDIT FLOW E2E TEST REPORT
================================================================================

SUMMARY
--------------------------------------------------------------------------------
✓ Individual Flow: PASSED
✓ Org Flow: PASSED
✓ BYOK Flow: PASSED
◐ Edge Cases: PARTIAL

Report saved to: /tmp/credit_flow_e2e_report.txt
```

## Troubleshooting

### Authentication Failures

**Problem**: `401 Unauthorized` errors

**Solution**:
```bash
# Verify Keycloak is accessible
curl http://localhost:8080/realms/uchub/.well-known/openid-configuration

# Check test users exist
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users \
  --realm uchub --fields username,email

# Verify client secret
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get clients \
  --realm uchub --fields clientId,secret | grep ops-center
```

### Database Connection Errors

**Problem**: `Could not connect to database`

**Solution**:
```bash
# Check PostgreSQL is running
docker ps | grep unicorn-postgresql

# Test connection
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT 1;"

# Check database exists
docker exec unicorn-postgresql psql -U unicorn -c "\l" | grep unicorn_db
```

### Credit Deduction Not Working

**Problem**: Credits not deducted after LLM request

**Solution**:
```bash
# Check credit system tables exist
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt" | grep credit

# Verify credit middleware is enabled
docker logs ops-center-direct | grep "credit"

# Check LiteLLM integration
docker logs ops-center-direct | grep "litellm"
```

### Organization Creation Fails

**Problem**: Cannot create organization

**Solution**:
```bash
# Check organization tables
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt" | grep org

# Verify org API is accessible
curl http://localhost:8084/api/v1/org -H "Authorization: Bearer TOKEN"

# Check Lago integration
docker logs unicorn-lago-api | tail -50
```

### BYOK Not Working

**Problem**: BYOK key not detected

**Solution**:
```bash
# Verify BYOK key storage table
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT * FROM user_byok_keys;"

# Check LiteLLM proxy configuration
docker logs uchub-litellm | grep "byok"

# Verify OpenRouter key is valid
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer YOUR_KEY"
```

## Performance Benchmarks

### Expected Response Times

- **Authentication**: < 500ms
- **LLM Request (GPT-3.5-turbo)**: 500-2000ms
- **Credit Deduction**: < 100ms
- **Usage Tracking**: < 50ms
- **Organization Queries**: < 200ms

### Expected Credit Costs

- **GPT-3.5-turbo** (100 tokens): ~9 credits (~$0.009)
- **GPT-4** (100 tokens): ~48 credits (~$0.048)
- **GPT-4-turbo** (100 tokens): ~24 credits (~$0.024)
- **Claude-3-Sonnet** (100 tokens): ~15 credits (~$0.015)

## Manual Test Cases

Some edge cases require manual testing:

### 1. Insufficient Org Credits

**Steps**:
1. Create organization with 100 credits
2. Allocate 100 credits to user
3. Make LLM request costing > 100 credits
4. Verify **402 Payment Required** error
5. Verify error message includes upgrade prompt

### 2. API Quota Exceeded

**Steps**:
1. Create trial user (700 API calls limit)
2. Make 700 LLM requests
3. Attempt 701st request
4. Verify **429 Too Many Requests** error
5. Verify `X-RateLimit-Reset` header present

### 3. No Credit Allocation

**Steps**:
1. Create organization
2. Add member WITHOUT credit allocation
3. Member makes LLM request
4. Verify graceful failure (not 500 error)
5. Verify error message explains missing allocation

### 4. Concurrent Requests

**Steps**:
1. Create user with 1000 credits
2. Make 10 simultaneous LLM requests (100 credits each)
3. Verify correct final balance (0 credits)
4. Verify no race conditions or double-charging

## Integration Verification Checklist

- [ ] Keycloak authentication works
- [ ] PostgreSQL queries execute correctly
- [ ] Redis caching operational
- [ ] Lago subscription synced
- [ ] LiteLLM routing functional
- [ ] Credit deduction accurate
- [ ] Usage tracking increments
- [ ] Quota enforcement works
- [ ] BYOK passthrough correct
- [ ] Org credit attribution correct
- [ ] Error handling graceful
- [ ] Performance within benchmarks

## Report Files

Test reports are saved to:

- **E2E Report**: `/tmp/credit_flow_e2e_report.txt`
- **Performance Metrics**: `/tmp/credit_flow_performance.json` (if enabled)
- **Error Logs**: `/tmp/credit_flow_errors.log` (if errors occur)

## CI/CD Integration

### GitHub Actions

```yaml
name: E2E Credit Flow Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: unicorn_db
          POSTGRES_USER: unicorn
          POSTGRES_PASSWORD: unicorn
        ports:
          - 5432:5432

      redis:
        image: redis:7.4
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio httpx

      - name: Run E2E tests
        env:
          OPS_CENTER_URL: http://localhost:8084
          KEYCLOAK_URL: http://localhost:8080
          TEST_OPENROUTER_KEY: ${{ secrets.TEST_OPENROUTER_KEY }}
        run: |
          pytest backend/tests/e2e/test_complete_credit_flow.py -v

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-test-report
          path: /tmp/credit_flow_e2e_report.txt
```

## Next Steps

After successful E2E testing:

1. **Performance Testing** - Load test with concurrent users
2. **Security Testing** - Penetration testing on credit endpoints
3. **Chaos Engineering** - Test with service failures
4. **User Acceptance Testing** - Real user scenarios
5. **Production Deployment** - Gradual rollout with monitoring

## Support

For issues or questions:

- **Documentation**: `/services/ops-center/docs/`
- **API Reference**: `/services/ops-center/docs/API_REFERENCE.md`
- **GitHub Issues**: https://github.com/Unicorn-Commander/UC-Cloud/issues
