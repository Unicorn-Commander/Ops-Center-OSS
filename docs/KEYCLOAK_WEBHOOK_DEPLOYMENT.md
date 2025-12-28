# Keycloak Subscription Sync - Deployment Guide

## Status: Ready for Deployment

All code has been implemented and is ready to deploy. The integration is complete but requires container rebuild to activate.

## What Was Implemented

### 1. Keycloak Integration Module
**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/backend/keycloak_integration.py`

- Admin token management with caching
- User lookup by email
- User attribute updates (with proper array formatting for Keycloak)
- Helper functions for tier management
- Health check endpoint

### 2. Updated Lago Webhook Handler
**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/backend/lago_webhooks.py`

**Changes Made:**
- ✅ Replaced Authentik integration with Keycloak
- ✅ Updated all attribute formats to use arrays (Keycloak requirement)
- ✅ Maintained all webhook event handlers:
  - `subscription.created`
  - `subscription.updated`
  - `subscription.cancelled` / `subscription.terminated`
  - `invoice.paid`
- ✅ Updated health check to report Keycloak status

### 3. Fixed FastAPI Route Handling
**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/backend/server.py` (line 3763)

**Problem:** Catch-all route was intercepting API endpoints
**Solution:** Added API path exclusion to catch-all handler

```python
# Skip API routes - let them be handled by registered routers
if full_path.startswith("api/"):
    raise HTTPException(status_code=404, detail="API endpoint not found")
```

### 4. Documentation
**Files Created:**
- `/home/muut/Production/UC-1-Pro/services/ops-center/docs/KEYCLOAK_SUBSCRIPTION_SYNC.md` - Complete integration guide
- `/home/muut/Production/UC-1-Pro/services/ops-center/scripts/test_keycloak_webhook.sh` - Comprehensive test suite

## Architecture Flow

```
┌─────────┐      ┌───────┐      ┌──────────┐      ┌────────────┐      ┌──────────┐
│  User   │─────>│Stripe │─────>│   Lago   │─────>│ Ops Center │─────>│ Keycloak │
│ Subscribes│    │Payment│      │ Billing  │      │  Webhook   │      │   User   │
│         │      │       │      │          │      │  Handler   │      │Attributes│
└─────────┘      └───────┘      └──────────┘      └────────────┘      └──────────┘
```

## Environment Variables Required

Add these to your `.env` file or docker-compose environment:

```bash
# Keycloak Configuration
KEYCLOAK_URL=https://auth.your-domain.com
KEYCLOAK_REALM=uchub
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=your-admin-password
KEYCLOAK_ADMIN_CLIENT_ID=admin-cli

# Lago Webhook Configuration
LAGO_WEBHOOK_SECRET=your_webhook_secret_from_lago
```

## Deployment Steps

### Step 1: Add Environment Variables

Edit your docker-compose file for ops-center and add the environment variables above.

### Step 2: Rebuild Container

Since backend code is baked into the image, rebuild is required:

```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center

# Stop current container
docker stop ops-center-direct

# Rebuild image
docker build -t uc-1-pro-ops-center .

# Start with new image
docker start ops-center-direct
# OR
docker-compose up -d ops-center
```

### Step 3: Verify Deployment

```bash
# Test webhook health
curl https://your-domain.com/api/v1/webhooks/lago/health

# Expected response:
{
  "status": "healthy",
  "webhook_endpoint": "/api/v1/webhooks/lago",
  "signature_verification": true,
  "keycloak": {
    "status": "healthy",
    "keycloak_url": "https://auth.your-domain.com",
    "realm": "uchub",
    "authenticated": true,
    "timestamp": "2025-10-10T..."
  }
}
```

### Step 4: Configure Lago Webhook

In Lago admin panel:
1. Go to **Settings** → **Integrations** → **Webhooks**
2. Set webhook URL: `https://your-domain.com/api/v1/webhooks/lago`
3. Copy the webhook secret and set as `LAGO_WEBHOOK_SECRET` environment variable
4. Enable these events:
   - subscription.created
   - subscription.updated
   - subscription.cancelled
   - subscription.terminated
   - invoice.paid
   - invoice.payment_status_updated

### Step 5: Run Test Suite

```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center
./scripts/test_keycloak_webhook.sh
```

The test will:
- ✅ Check webhook health
- ✅ Authenticate with Keycloak
- ✅ Send test subscription events
- ✅ Verify attributes are updated correctly

## What Gets Synced

When a subscription event occurs, these Keycloak user attributes are updated:

| Attribute | Description | Example Value |
|-----------|-------------|---------------|
| `subscription_tier` | Tier name | `["professional"]` |
| `subscription_status` | Status | `["active"]` |
| `subscription_id` | Lago ID | `["sub_abc123"]` |
| `subscription_plan_code` | Plan code | `["professional_monthly"]` |
| `subscription_updated_at` | Timestamp | `["2025-10-10T20:00:00"]` |
| `api_calls_used` | Usage counter | `["0"]` |
| `last_reset_date` | Last reset | `["2025-10-10"]` |

**Note:** All values are arrays because Keycloak requires this format.

## Tier Mapping

Plan codes are automatically mapped to tiers:

| Plan Code Contains | Maps To |
|-------------------|---------|
| "enterprise" or "unlimited" | `enterprise` |
| "pro" or "professional" | `professional` |
| "basic" or "starter" | `basic` |
| (anything else) | `free` |

## Testing After Deployment

### Manual Test: Create Subscription

```bash
curl -X POST https://your-domain.com/api/v1/webhooks/lago \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_type": "subscription.created",
    "customer": {
      "email": "admin@example.com"
    },
    "subscription": {
      "lago_id": "test_sub_123",
      "plan_code": "professional_monthly",
      "status": "active"
    }
  }'
```

### Verify in Keycloak

```bash
# Get admin token
TOKEN=$(curl -sk -X POST \
  "https://auth.your-domain.com/realms/master/protocol/openid-connect/token" \
  -d "username=admin" \
  -d "password=your-admin-password" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

# Get user attributes
curl -sk "https://auth.your-domain.com/admin/realms/uchub/users?email=admin@example.com&exact=true" \
  -H "Authorization: Bearer $TOKEN" | jq '.[0].attributes'
```

Expected output:
```json
{
  "subscription_tier": ["professional"],
  "subscription_status": ["active"],
  "subscription_id": ["test_sub_123"],
  "subscription_plan_code": ["professional_monthly"],
  "subscription_updated_at": ["2025-10-10T20:45:12.345678"],
  "api_calls_used": ["0"],
  "last_reset_date": ["2025-10-10T20:45:12.345678"]
}
```

## Troubleshooting

### Issue: Webhook Returns HTML Instead of JSON

**Cause:** Container is running old code without the catch-all route fix.

**Solution:** Rebuild container (see Step 2 above).

### Issue: "User not found" Error

**Cause:** User doesn't exist in Keycloak or email doesn't match.

**Solutions:**
1. Verify user exists in realm `uchub`
2. Check email is exactly correct (case-sensitive)
3. Ensure user has logged in at least once

### Issue: "Failed to authenticate with Keycloak"

**Cause:** Admin credentials incorrect or permissions insufficient.

**Solutions:**
1. Verify `KEYCLOAK_ADMIN_PASSWORD` is correct
2. Test authentication manually:
   ```bash
   curl -X POST "https://auth.your-domain.com/realms/master/protocol/openid-connect/token" \
     -d "username=admin" \
     -d "password=your-admin-password" \
     -d "grant_type=password" \
     -d "client_id=admin-cli"
   ```
3. Check admin has permissions in master realm

### Issue: "Invalid signature" Error

**Cause:** `LAGO_WEBHOOK_SECRET` doesn't match Lago configuration.

**Solutions:**
1. Copy exact secret from Lago admin panel
2. Update environment variable
3. Restart container

## Security Notes

1. ✅ **Webhook signature verification** - Lago signatures are verified using HMAC SHA-256
2. ✅ **HTTPS required** - All webhooks must use HTTPS
3. ✅ **Token caching** - Admin tokens are cached to reduce auth requests
4. ✅ **SSL verification disabled** - Using `verify=False` for self-signed Keycloak certs (update for production)

## Next Steps

1. ✅ Code implementation - COMPLETE
2. ⏳ Container rebuild - REQUIRED
3. ⏳ Environment variables - REQUIRED
4. ⏳ Lago webhook configuration - REQUIRED
5. ⏳ Testing - After deployment

## Support Files

- **Integration Guide:** `KEYCLOAK_SUBSCRIPTION_SYNC.md`
- **Test Script:** `scripts/test_keycloak_webhook.sh`
- **Source Code:**
  - `backend/keycloak_integration.py`
  - `backend/lago_webhooks.py`
  - `backend/server.py` (routing fix)

## Contact

For questions or issues:
- Email: admin@example.com
- Check logs: `docker logs ops-center-direct`
