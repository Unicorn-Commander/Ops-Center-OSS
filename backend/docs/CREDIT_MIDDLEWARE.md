# Credit Deduction Middleware

**Status**: Production Ready
**Author**: Backend Integration Teamlead
**Date**: November 15, 2025
**Version**: 1.0.0

## Overview

The Credit Deduction Middleware is a production-ready FastAPI middleware that automatically deducts credits for all LLM API requests. It provides:

- **Automatic credit checking** before processing requests
- **Exact credit deduction** after successful responses
- **Organization and individual billing** support
- **BYOK passthrough** (no charges for user-owned keys)
- **Fail-open design** (never blocks users due to billing failures)
- **Atomic transactions** (credit deduction + usage attribution)

## Architecture

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Request                              │
│            POST /api/v1/llm/chat/completions                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         Credit Deduction Middleware                          │
└─────────────────────────────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Check    │  │ Estimate │  │ Check    │
│ Session  │  │ Credits  │  │ BYOK     │
└──────────┘  └──────────┘  └──────────┘
      │              │              │
      └──────────────┼──────────────┘
                     │
                     ▼
              ┌──────────────┐
              │ BYOK Enabled?│
              └──────┬───────┘
                     │
         ┌───────────┴───────────┐
         │                       │
       Yes                      No
         │                       │
         ▼                       ▼
   ┌──────────┐          ┌──────────────┐
   │Passthrough│          │Check Credits │
   │(No charge)│          │(Org or Indiv)│
   └──────────┘          └──────┬───────┘
         │                      │
         │              ┌───────┴────────┐
         │              │                │
         │         Sufficient      Insufficient
         │              │                │
         │              ▼                ▼
         │      ┌──────────┐      ┌──────────┐
         │      │Process   │      │Return 402│
         │      │Request   │      │Payment   │
         │      └────┬─────┘      │Required  │
         │           │            └──────────┘
         └───────────┼────────────┘
                     │
                     ▼
            ┌────────────────┐
            │ LLM API Call   │
            │ (vLLM, OpenAI) │
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │Extract Actual  │
            │Cost from Response│
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │Deduct Exact    │
            │Credits         │
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │Add Credit      │
            │Headers         │
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │Return Response │
            └────────────────┘
```

### Middleware Order

The middleware stack is applied in this order (innermost to outermost):

1. **CORS** - Handle cross-origin requests
2. **GZip** - Compress responses
3. **RequestID** - Add request tracking
4. **Cache** - Add cache headers
5. **Compression** - Additional compression
6. **Session** - Session management
7. **CSRF** - CSRF protection
8. **TierEnforcement** - Check subscription tiers
9. **CreditDeduction** ← **YOU ARE HERE**
10. **Routes** - API endpoints

## Features

### 1. Automatic Credit Checking (Pre-Request)

Before processing any LLM request, the middleware:

- Estimates credit cost based on endpoint type
- Checks if user has sufficient credits (org or individual)
- Returns 402 Payment Required if insufficient
- Prevents wasteful API calls when credits are low

**Estimation Logic**:
- Chat/completions: ~9 credits (1500 tokens × $0.006)
- Image generation: ~48 credits (DALL-E 3 standard)
- Embeddings: ~3 credits (average batch)

### 2. Exact Credit Deduction (Post-Response)

After successful LLM response, the middleware:

- Extracts actual token usage from response
- Calculates exact cost based on usage
- Deducts credits atomically (single transaction)
- Logs usage attribution for analytics

**Cost Extraction**:
```json
{
  "usage": {"total_tokens": 150},
  "cost": 0.9,
  "model": "openai/gpt-4"
}
```

### 3. Organization vs Individual Billing

The middleware intelligently routes billing:

**Organization Billing**:
- User belongs to organization → deduct from org pool
- Tracks per-user attribution within org
- Enforces org-level quotas
- Header: `X-Org-Credits: true`

**Individual Billing**:
- User has no organization → deduct from personal balance
- Enforces individual quotas and monthly caps
- Header: `X-Org-Credits: false`

### 4. BYOK Passthrough

Users with Bring Your Own Key (BYOK) configured:

- Credits are NOT deducted
- Requests passthrough to LLM with user's key
- Header: `X-BYOK: true`
- Header: `X-Credits-Used: 0.0`

**BYOK Providers Supported**:
- OpenRouter
- OpenAI
- Anthropic
- HuggingFace
- Cohere

### 5. Fail-Open Design

On any billing system failure:

- Request is ALLOWED to proceed
- Error is logged for investigation
- User is NOT blocked
- Credits may not be deducted (acceptable trade-off)

**Philosophy**: User experience > perfect billing accuracy

## Configuration

### Environment Variables

```bash
# Redis (for session management)
REDIS_HOST=unicorn-redis
REDIS_PORT=6379

# PostgreSQL (for credit tables)
POSTGRES_HOST=unicorn-postgresql
POSTGRES_PORT=5432
POSTGRES_USER=unicorn
POSTGRES_PASSWORD=unicorn
POSTGRES_DB=unicorn_db

# Credit System Settings (optional)
CREDIT_ESTIMATION_TOKENS=1500          # Default estimated tokens
CREDIT_ESTIMATION_COST_PER_1K=0.006    # Default cost per 1K tokens
```

### Tracked Endpoints

The middleware tracks these endpoints:

| Endpoint | Description | Estimated Cost |
|----------|-------------|----------------|
| `/api/v1/llm/chat/completions` | Chat completions | ~9 credits |
| `/api/v1/llm/completions` | Text completions | ~9 credits |
| `/api/v1/llm/image/generations` | Image generation | ~48 credits |
| `/api/v1/llm/embeddings` | Text embeddings | ~3 credits |

### Excluded Endpoints

These endpoints do NOT consume credits:

- `/api/v1/llm/models` - Model list
- `/api/v1/llm/health` - Health check
- `/api/v1/admin/*` - Admin endpoints
- `/api/v1/billing/*` - Billing management
- `/api/v1/credits/*` - Credit management

## Response Headers

The middleware adds these headers to responses:

| Header | Description | Example |
|--------|-------------|---------|
| `X-Credits-Used` | Credits deducted for this request | `0.009` |
| `X-Credits-Remaining` | Credits remaining in account | `2491.50` |
| `X-Org-Credits` | Whether org credits were used | `true` / `false` |
| `X-BYOK` | Whether BYOK key was used | `true` / `false` |
| `X-BYOK-Provider` | BYOK provider name (if applicable) | `openrouter` |

## Error Responses

### 401 Unauthorized

Returned when no valid session token is provided.

```json
{
  "error": "Unauthorized",
  "message": "Authentication required. Please login to access this endpoint."
}
```

### 402 Payment Required

Returned when user has insufficient credits.

```json
{
  "error": "Payment Required",
  "message": "Insufficient credits. Balance: 5.00, needed: 10.00",
  "estimated_cost": 10.0,
  "org_credits": false,
  "org_id": null,
  "upgrade_url": "/admin/subscription/plan"
}
```

**Headers**:
- `X-Credits-Required: 10.0`
- `X-Org-Credits: false`

## Database Schema

### Organization Credit Tables

```sql
-- Organization credit pools
CREATE TABLE organization_credits (
    org_id UUID PRIMARY KEY,
    total_credits BIGINT NOT NULL,          -- Total allocated (milicredits)
    used_credits BIGINT DEFAULT 0,          -- Total used (milicredits)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User credit allocations within org
CREATE TABLE user_credit_allocations (
    id SERIAL PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    user_id TEXT NOT NULL,
    allocated_credits BIGINT NOT NULL,      -- Allocated to user
    used_credits BIGINT DEFAULT 0,          -- Used by user
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Credit usage tracking
CREATE TABLE credit_usage_tracking (
    id SERIAL PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    user_id TEXT NOT NULL,
    credits_used BIGINT NOT NULL,           -- Amount deducted
    service_type TEXT NOT NULL,             -- 'llm_inference'
    service_name TEXT,                      -- Model name
    request_id TEXT,                        -- Optional request ID
    metadata JSONB,                         -- Token count, provider, etc.
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Individual Credit Tables

```sql
-- User credit balances
CREATE TABLE user_credits (
    user_id TEXT PRIMARY KEY,
    balance NUMERIC(12,6) NOT NULL DEFAULT 0.0,
    total_spent NUMERIC(12,6) DEFAULT 0.0,
    monthly_cap NUMERIC(12,6),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Credit transactions
CREATE TABLE credit_transactions (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES user_credits(user_id),
    transaction_id TEXT UNIQUE NOT NULL,
    amount NUMERIC(12,6) NOT NULL,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Integration Guide

### Step 1: Register Middleware

In `server.py`:

```python
from credit_deduction_middleware import CreditDeductionMiddleware

# Add after tier enforcement, before routes
app.add_middleware(CreditDeductionMiddleware)
logger.info("Credit Deduction Middleware enabled")
```

### Step 2: Remove Manual Credit Checks

In `litellm_api.py`, remove manual credit checking code:

```python
# BEFORE (manual credit check)
if not using_byok and user_tier != 'free':
    org_integration = get_org_credit_integration()
    has_org_credits, org_id, message = await org_integration.has_sufficient_org_credits(...)
    if not has_org_credits:
        raise HTTPException(status_code=402, detail=message)

# AFTER (middleware handles it)
# No credit check needed - middleware handles automatically
```

### Step 3: Remove Manual Credit Deduction

In `litellm_api.py`, remove manual deduction code:

```python
# BEFORE (manual deduction)
if not using_byok:
    success, org_id, remaining = await org_integration.deduct_org_credits(...)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to deduct credits")

# AFTER (middleware handles it)
# No deduction needed - middleware deducts automatically
```

### Step 4: Test

```bash
# Run unit tests
cd /home/muut/Production/UC-Cloud/services/ops-center/backend/tests
pytest test_credit_deduction_middleware.py -v

# Run integration tests
ORG_USER_TOKEN=<token> python integration_test_credit_middleware.py
```

## Performance

### Overhead

The middleware adds minimal overhead:

- Pre-check: ~5ms (Redis session + credit check)
- Post-deduction: ~10ms (DB transaction + attribution)
- Total overhead: **~15ms per request**

### Optimization

The middleware is optimized for production:

- **Lazy initialization** - Only initializes on first use
- **Async operations** - All DB calls are async
- **Fail-fast checks** - BYOK and exclusions checked first
- **Atomic transactions** - Single DB call for deduction + attribution

## Testing

### Unit Tests

Run with pytest:

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend/tests
pytest test_credit_deduction_middleware.py -v -s
```

**Test Coverage**:
- Endpoint tracking/exclusion
- BYOK detection
- Credit estimation
- Org vs individual billing
- Insufficient credits
- Concurrent requests
- Error handling (fail-open)

### Integration Tests

Run with real backend:

```bash
# Set session tokens for test users
export ORG_USER_TOKEN="<org-user-session-token>"
export INDIVIDUAL_USER_TOKEN="<individual-user-session-token>"
export BYOK_USER_TOKEN="<byok-user-session-token>"

# Run integration tests
python integration_test_credit_middleware.py
```

**Test Scenarios**:
1. Backend health check
2. Org credit deduction
3. Individual credit deduction
4. BYOK passthrough
5. Concurrent requests (atomic deduction)

## Troubleshooting

### Issue: Credits not being deducted

**Symptoms**: LLM requests succeed but no credit headers

**Possible Causes**:
1. Endpoint not in `CREDIT_ENDPOINTS` list
2. BYOK enabled (intentional bypass)
3. Middleware initialization failed

**Debug**:
```bash
# Check middleware logs
docker logs ops-center-direct | grep -i "credit"

# Check if middleware is registered
docker logs ops-center-direct | grep "Credit Deduction Middleware enabled"
```

### Issue: 402 errors when user has credits

**Symptoms**: User sees "Payment Required" despite having balance

**Possible Causes**:
1. Org membership not detected
2. Credit allocation not set
3. Credit check query failing

**Debug**:
```sql
-- Check user's org membership
SELECT * FROM organization_members WHERE user_id = '<user-id>';

-- Check org credits
SELECT * FROM organization_credits WHERE org_id = '<org-id>';

-- Check user allocation
SELECT * FROM user_credit_allocations
WHERE org_id = '<org-id>' AND user_id = '<user-id>';

-- Check individual balance
SELECT * FROM user_credits WHERE user_id = '<user-id>';
```

### Issue: BYOK not working

**Symptoms**: BYOK user is being charged credits

**Possible Causes**:
1. BYOK key not configured in database
2. Model provider mismatch
3. BYOKManager initialization failed

**Debug**:
```sql
-- Check BYOK keys
SELECT user_id, provider, key_name, is_active
FROM byok_keys
WHERE user_id = '<user-id>';
```

```bash
# Check middleware BYOK detection
docker logs ops-center-direct | grep -i "byok"
```

### Issue: Middleware not running

**Symptoms**: No credit headers, no 402 errors

**Possible Causes**:
1. Middleware not imported in server.py
2. Middleware not registered
3. Server restart needed

**Fix**:
```bash
# Restart backend
docker restart ops-center-direct

# Check logs for middleware registration
docker logs ops-center-direct | grep "Credit Deduction Middleware"
```

## Security Considerations

### 1. Session Validation

The middleware validates session tokens from Redis:
- Checks cookie: `session_token`
- Retrieves user data from Redis
- Maps Keycloak `sub` to `user_id`

### 2. Credit Check Race Conditions

The middleware prevents race conditions:
- Pre-check prevents over-spending
- Atomic deduction (single DB transaction)
- Fail-open on errors (user experience priority)

### 3. BYOK Key Security

BYOK keys are handled securely:
- Keys stored encrypted in database
- Only key existence checked (not exposed)
- Requests passthrough to LLM directly

### 4. Audit Logging

All credit operations are logged:
- User ID and org ID
- Credits deducted
- Service name and model
- Token usage
- Timestamp

## Future Enhancements

### Phase 2 (Planned)

1. **Dynamic Pricing** - Adjust credit costs based on model/provider
2. **Credit Alerts** - Notify users when credits low
3. **Usage Quotas** - Per-user limits within organizations
4. **Credit Rollover** - Unused credits carry over month-to-month
5. **Refunds** - Automatic refunds for failed requests

### Phase 3 (Planned)

1. **Prepaid Packages** - Bulk credit purchases at discounts
2. **Credit Sharing** - Transfer credits between users
3. **Usage Analytics** - Detailed charts and reports
4. **Cost Optimization** - Automatic model selection for cost
5. **Budget Alerts** - Slack/email notifications for thresholds

## Support

**Documentation**: `/home/muut/Production/UC-Cloud/services/ops-center/backend/docs/CREDIT_MIDDLEWARE.md`
**Source Code**: `/home/muut/Production/UC-Cloud/services/ops-center/backend/credit_deduction_middleware.py`
**Tests**: `/home/muut/Production/UC-Cloud/services/ops-center/backend/tests/test_credit_deduction_middleware.py`
**Integration**: `/home/muut/Production/UC-Cloud/services/ops-center/backend/tests/integration_test_credit_middleware.py`

For issues or questions, check:
- Docker logs: `docker logs ops-center-direct`
- Database queries: PostgreSQL `unicorn_db`
- Redis sessions: `unicorn-redis`

---

**Version**: 1.0.0
**Last Updated**: November 15, 2025
**Status**: Production Ready
