# Tier Enforcement with Keycloak - Setup Guide

## Overview

This implementation uses **Keycloak** (not Authentik) for subscription tier management and usage tracking. User subscription tiers and API usage counters are stored as Keycloak user attributes.

**Keycloak Instance**: `https://auth.your-domain.com/realms/uchub`

## Architecture

```
┌─────────────────┐
│   Frontend      │
│  (React/Vue)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Tier Enforcement Middleware       │
│  (tier_enforcement_middleware.py)   │
│                                     │
│  1. Extract user from session       │
│  2. Fetch tier from Keycloak        │
│  3. Check limits                    │
│  4. Increment usage counter         │
│  5. Add headers to response         │
└────────┬────────────────────────────┘
         │
         ├────────► Keycloak Admin API
         │          (get/update user attributes)
         │
         ▼
┌─────────────────────────────────────┐
│   Protected API Endpoints           │
│  (FastAPI routes)                   │
└─────────────────────────────────────┘
```

## Environment Variables

Add these to your `.env` file or docker-compose environment:

```bash
# Keycloak Configuration
KEYCLOAK_URL=https://auth.your-domain.com
KEYCLOAK_REALM=uchub
KEYCLOAK_CLIENT_ID=admin-cli
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=your_admin_password

# Tier Enforcement
TIER_ENFORCEMENT_ENABLED=true
ENVIRONMENT=development  # or production
```

## Keycloak User Attributes

The system uses these user attributes in Keycloak:

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `subscription_tier` | String (array) | User's subscription tier | `["trial"]` |
| `subscription_status` | String (array) | Subscription status | `["active"]` |
| `api_calls_used` | String (array) | Daily API call counter | `["42"]` |
| `api_calls_reset_date` | String (array) | Last reset date | `["2025-10-10"]` |
| `stripe_customer_id` | String (array) | Stripe customer ID (optional) | `["cus_xxx"]` |
| `subscription_start_date` | String (array) | Subscription start (optional) | `["2025-10-01"]` |
| `subscription_end_date` | String (array) | Subscription end (optional) | `["2025-11-01"]` |

**Important**: Keycloak stores all user attributes as arrays (multi-valued). The code handles this automatically.

## Subscription Tiers

| Tier | Daily Limit | Monthly Limit | Features |
|------|-------------|---------------|----------|
| **Trial** | 100 | 3,000 | Basic access, chat, ops-center |
| **Free** | 33 | 1,000 | Basic access, chat, ops-center |
| **Starter** | 33 | 1,000 | Basic access, chat, ops-center |
| **Professional** | 333 | 10,000 | All above + search, litellm, billing, tts, stt |
| **Enterprise** | Unlimited | Unlimited | All features + team management, SSO, audit logs |

## Files Modified/Created

### Core Implementation

1. **`keycloak_integration.py`** (NEW)
   - Keycloak Admin API client
   - User tier retrieval
   - Usage counter management
   - Tier updates

2. **`tier_enforcement_middleware.py`** (UPDATED)
   - Middleware for FastAPI
   - Reads tier from Keycloak
   - Enforces limits per request
   - Adds usage headers to responses

3. **`usage_api.py`** (UPDATED)
   - REST API endpoints for usage info
   - `/api/v1/usage/current` - Current usage stats
   - `/api/v1/usage/limits` - Tier limits
   - `/api/v1/usage/features` - Feature access
   - `/api/v1/usage/history` - Usage history (TODO)
   - `/api/v1/usage/reset-demo` - Reset counter (dev only)

### Testing

4. **`tests/test_tier_enforcement.py`** (NEW)
   - Comprehensive Python test suite
   - Tests all Keycloak operations
   - Validates tier enforcement logic

5. **`tests/test_tier_enforcement.sh`** (NEW)
   - Bash script for live API testing
   - Tests authenticated endpoints
   - Validates HTTP headers

## Integration with server.py

The middleware is already integrated in `server.py`. Verify these lines exist:

```python
from tier_enforcement_middleware import TierEnforcementMiddleware
from usage_api import router as usage_router

# Add middleware
if TIER_ENFORCEMENT_ENABLED:
    app.add_middleware(TierEnforcementMiddleware)

# Register usage API routes
app.include_router(usage_router)
```

## Setting Up a Test User in Keycloak

### Option 1: Via Keycloak Admin Console

1. Login to Keycloak admin console:
   ```
   https://auth.your-domain.com/admin/master/console/#/uchub
   ```

2. Go to **Users** → Select user → **Attributes** tab

3. Add these attributes:
   ```
   subscription_tier = trial
   subscription_status = active
   api_calls_used = 0
   api_calls_reset_date = 2025-10-10
   ```

### Option 2: Via Python Script

```python
from keycloak_integration import set_subscription_tier, reset_usage
import asyncio

async def setup_test_user():
    email = "test@example.com"

    # Set tier
    await set_subscription_tier(email, "trial", "active")

    # Reset usage
    await reset_usage(email)

    print(f"User {email} configured for testing")

asyncio.run(setup_test_user())
```

## Testing the Implementation

### 1. Python Unit Tests

```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center/backend
python3 tests/test_tier_enforcement.py test@example.com
```

Expected output:
```
✅ PASS | Keycloak Connection | Token obtained: ...
✅ PASS | User Retrieval | User found: testuser
✅ PASS | Tier Info Retrieval | Tier: trial, Status: active, Usage: 0
✅ PASS | Usage Reset | Before: 5, After: 0
✅ PASS | Usage Increment | Before: 0, After: 1
✅ PASS | Tier Change | Before: trial, After: professional
✅ PASS | Tier Limits Configuration | Limits: {...}
```

### 2. Live API Tests

```bash
# First, login to get session
curl -c /tmp/session.txt -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"yourpass"}'

# Run test suite
SESSION_FILE=/tmp/session.txt \
  ./tests/test_tier_enforcement.sh
```

### 3. Manual Header Verification

```bash
# Make authenticated API call
curl -b /tmp/session.txt https://your-domain.com/api/v1/services -v 2>&1 | grep X-

# Expected headers:
X-Tier: trial
X-Tier-Status: active
X-API-Calls-Used: 1
X-API-Calls-Limit: 100
X-API-Calls-Remaining: 99
```

### 4. Test Usage API

```bash
# Get current usage
curl -b /tmp/session.txt https://your-domain.com/api/v1/usage/current | jq

# Expected response:
{
  "user": {
    "email": "test@example.com",
    "username": "testuser"
  },
  "subscription": {
    "tier": "trial",
    "tier_name": "Trial",
    "status": "active"
  },
  "usage": {
    "api_calls": {
      "used": 1,
      "remaining": 99,
      "daily_limit": 100,
      "percentage": 1.0
    }
  }
}
```

## Rate Limiting Behavior

### Active Subscription

- Requests are counted against daily limit
- Headers show current usage
- When limit reached: `429 Too Many Requests` with upgrade prompt

### Inactive Subscription

- All API calls blocked (except exempt paths)
- Returns: `403 Forbidden` with reactivation prompt

### Exempt Paths (No Limits)

- `/` - Home page
- `/auth/*` - Authentication endpoints
- `/api/v1/auth/*` - Auth API
- `/api/v1/webhooks/*` - Webhooks (Lago, Stripe)
- `/api/v1/subscription/*` - Subscription management
- `/api/v1/usage/*` - Usage information
- `/health`, `/docs`, `/redoc` - System endpoints

## Error Responses

### Rate Limit Exceeded

```json
{
  "error": "rate_limit_exceeded",
  "message": "Daily API limit reached (100 calls). Upgrade for higher limits.",
  "tier": "trial",
  "used": 100,
  "limit": 100,
  "upgrade_url": "/subscription",
  "timestamp": "2025-10-10T12:34:56.789Z"
}
```

### Subscription Inactive

```json
{
  "error": "subscription_inactive",
  "message": "Your subscription is not active. Please update your payment method or contact support.",
  "tier": "professional",
  "status": "cancelled",
  "upgrade_url": "/subscription",
  "timestamp": "2025-10-10T12:34:56.789Z"
}
```

## Monitoring & Debugging

### Check Keycloak User Attributes

```bash
# Via Keycloak Admin API
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://auth.your-domain.com/admin/realms/uchub/users?email=test@example.com" | jq '.[] | .attributes'
```

### Check Application Logs

```bash
docker logs unicorn-ops-center | grep -E "Tier|usage|Keycloak"
```

### Reset Usage Counter (Development)

```bash
curl -b /tmp/session.txt -X POST \
  https://your-domain.com/api/v1/usage/reset-demo
```

## Troubleshooting

### Issue: "Failed to get admin token"

**Cause**: Invalid Keycloak credentials

**Fix**:
1. Check `KEYCLOAK_ADMIN_USERNAME` and `KEYCLOAK_ADMIN_PASSWORD`
2. Verify admin user exists in Keycloak
3. Check Keycloak logs: `docker logs keycloak`

### Issue: "User not found"

**Cause**: User doesn't exist in Keycloak realm

**Fix**:
1. Verify user exists: Keycloak Admin → Users
2. Check correct realm is configured (`uchub`)
3. Ensure email matches exactly

### Issue: "Attributes not updating"

**Cause**: Keycloak API permission issues

**Fix**:
1. Verify admin user has `realm-management` client role
2. Check token has sufficient scope
3. Use client credentials grant with admin-cli client

### Issue: Headers not appearing

**Cause**: Middleware not registered or request is exempt

**Fix**:
1. Verify `TIER_ENFORCEMENT_ENABLED=true`
2. Check path is not in `EXEMPT_PATHS`
3. Ensure user is authenticated
4. Check middleware order in `server.py`

## Production Considerations

1. **Token Caching**: Admin token is cached for 5 minutes (with 30s buffer)
2. **Error Handling**: Tier enforcement fails open (allows request on error)
3. **Performance**: Usage increment is fire-and-forget (async task)
4. **Daily Reset**: Automatic reset at UTC midnight
5. **SSL Verification**: Currently disabled (`verify=False`). Enable in production.

## Future Enhancements

- [ ] Historical usage tracking (time-series database)
- [ ] Per-service usage limits
- [ ] Burst allowances
- [ ] Usage analytics dashboard
- [ ] Webhook notifications on limit reached
- [ ] Grace period for expired subscriptions
- [ ] Multi-tier feature gates

## Support

For issues or questions:
- GitHub: https://github.com/Unicorn-Commander/UC-1-Pro/issues
- Documentation: https://github.com/Unicorn-Commander/UC-1-Pro/docs
