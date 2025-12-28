# Keycloak Subscription Sync Documentation

## Overview

The Ops Center integrates with Lago billing system and Keycloak authentication to automatically sync subscription data to user attributes. When subscription events occur in Lago (via Stripe), webhooks trigger updates to Keycloak user attributes.

## Architecture

```
User → Stripe Checkout → Lago Billing → Webhook → Ops Center → Keycloak User Attributes
```

### Flow:

1. **User subscribes/updates** via Stripe Checkout
2. **Stripe notifies** Lago of payment events
3. **Lago sends webhook** to `https://your-domain.com/api/v1/webhooks/lago`
4. **Ops Center receives** webhook and validates signature
5. **Ops Center updates** Keycloak user attributes
6. **User permissions** automatically reflect new tier

## Environment Variables

Add these to your `.env` file or docker-compose environment:

```bash
# Keycloak Configuration
KEYCLOAK_URL=https://auth.your-domain.com
KEYCLOAK_REALM=uchub
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=your-admin-password
KEYCLOAK_ADMIN_CLIENT_ID=admin-cli

# Lago Webhook Configuration
LAGO_WEBHOOK_SECRET=your_webhook_secret_from_lago_admin
```

### Getting the Lago Webhook Secret

1. Log into Lago admin panel
2. Go to **Settings** → **Integrations** → **Webhooks**
3. Copy the webhook secret
4. Set it as `LAGO_WEBHOOK_SECRET` environment variable

## Keycloak User Attributes

When subscriptions sync, the following attributes are set (all stored as arrays in Keycloak):

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `subscription_tier` | string[] | Tier name | `["professional"]` |
| `subscription_status` | string[] | Status | `["active"]` |
| `subscription_id` | string[] | Lago subscription ID | `["sub_abc123"]` |
| `subscription_plan_code` | string[] | Original plan code | `["professional_monthly"]` |
| `subscription_updated_at` | string[] | ISO timestamp | `["2025-10-10T20:00:00"]` |
| `api_calls_used` | string[] | Usage counter | `["0"]` |
| `last_reset_date` | string[] | Last usage reset | `["2025-10-10T20:00:00"]` |

### Tier Values

- `free` - Free tier (default)
- `basic` - Basic/Starter tier
- `professional` - Professional tier
- `enterprise` - Enterprise tier

### Status Values

- `active` - Active subscription
- `cancelled` - Cancelled (still has access until period end)
- `terminated` - Fully terminated (no access)
- `past_due` - Payment failed

## Webhook Events

### Supported Events

#### 1. `subscription.created`

Triggered when a new subscription is created.

**Lago Payload:**
```json
{
  "webhook_type": "subscription.created",
  "customer": {
    "email": "user@example.com"
  },
  "subscription": {
    "lago_id": "sub_abc123",
    "plan_code": "professional_monthly",
    "status": "active"
  }
}
```

**Keycloak Update:**
- Sets `subscription_tier` based on plan code
- Sets `subscription_status` to active
- Resets `api_calls_used` to 0

#### 2. `subscription.updated`

Triggered on upgrades, downgrades, or status changes.

**Lago Payload:**
```json
{
  "webhook_type": "subscription.updated",
  "customer": {
    "email": "user@example.com"
  },
  "subscription": {
    "lago_id": "sub_abc123",
    "plan_code": "enterprise_annual",
    "status": "active"
  }
}
```

**Keycloak Update:**
- Updates `subscription_tier` to new tier
- Updates `subscription_status`
- Resets usage counters if moving to active

#### 3. `subscription.cancelled` / `subscription.terminated`

Triggered when subscription is cancelled.

**Lago Payload:**
```json
{
  "webhook_type": "subscription.cancelled",
  "customer": {
    "email": "user@example.com"
  },
  "subscription": {
    "lago_id": "sub_abc123"
  }
}
```

**Keycloak Update:**
- Downgrades to `free` tier
- Sets status to `cancelled`

#### 4. `invoice.paid`

Triggered after successful payment.

**Lago Payload:**
```json
{
  "webhook_type": "invoice.paid",
  "customer": {
    "email": "user@example.com"
  },
  "invoice": {
    "lago_id": "inv_xyz789",
    "payment_status": "succeeded"
  }
}
```

**Keycloak Update:**
- Resets `api_calls_used` to 0
- Updates `last_reset_date`

## Plan Code Mapping

The webhook handler automatically maps Lago plan codes to tier names:

| Plan Code Pattern | Mapped Tier |
|-------------------|-------------|
| Contains "enterprise" or "unlimited" | `enterprise` |
| Contains "pro" or "professional" | `professional` |
| Contains "basic" or "starter" | `basic` |
| Everything else | `free` |

Example mappings:
- `professional_monthly` → `professional`
- `enterprise_annual` → `enterprise`
- `basic_plan` → `basic`

## Configuration in Lago

### Set Webhook URL

In Lago admin panel:

1. Navigate to **Settings** → **Integrations** → **Webhooks**
2. Set webhook endpoint URL:
   ```
   https://your-domain.com/api/v1/webhooks/lago
   ```
3. Enable the following events:
   - `subscription.created`
   - `subscription.updated`
   - `subscription.cancelled`
   - `subscription.terminated`
   - `invoice.paid`
   - `invoice.payment_status_updated`

### Webhook Signature Verification

The webhook handler verifies Lago signatures using HMAC SHA-256:

1. Lago sends signature in `X-Lago-Signature` header
2. Handler computes expected signature using `LAGO_WEBHOOK_SECRET`
3. Request rejected if signatures don't match

**Security Note:** If `LAGO_WEBHOOK_SECRET` is not set, signature verification is **skipped** (development mode only).

## Testing

### Health Check

Check webhook and Keycloak connectivity:

```bash
curl https://your-domain.com/api/v1/webhooks/lago/health
```

Expected response:
```json
{
  "status": "healthy",
  "webhook_endpoint": "/api/v1/webhooks/lago",
  "signature_verification": true,
  "keycloak": {
    "status": "healthy",
    "keycloak_url": "https://auth.your-domain.com",
    "realm": "uchub",
    "authenticated": true,
    "timestamp": "2025-10-10T20:00:00"
  }
}
```

### Manual Webhook Test

Test subscription creation:

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

### Verify Keycloak Attributes

After webhook, check user attributes in Keycloak:

```bash
# Get admin token
TOKEN=$(curl -s -X POST \
  "https://auth.your-domain.com/realms/master/protocol/openid-connect/token" \
  -d "username=admin" \
  -d "password=your-admin-password" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  | jq -r '.access_token')

# Get user by email
curl -s "https://auth.your-domain.com/admin/realms/uchub/users?email=admin@example.com&exact=true" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.[0].attributes'
```

Expected attributes:
```json
{
  "subscription_tier": ["professional"],
  "subscription_status": ["active"],
  "subscription_id": ["test_sub_123"],
  "subscription_plan_code": ["professional_monthly"],
  "subscription_updated_at": ["2025-10-10T20:00:00.123456"],
  "api_calls_used": ["0"],
  "last_reset_date": ["2025-10-10T20:00:00.123456"]
}
```

## Troubleshooting

### Webhook Not Receiving Events

1. **Check Lago configuration:**
   - Webhook URL correct?
   - Events enabled?
   - Webhook endpoint status shows "healthy"?

2. **Check network connectivity:**
   ```bash
   curl -I https://your-domain.com/api/v1/webhooks/lago/health
   ```

3. **Check Ops Center logs:**
   ```bash
   docker logs unicorn-ops-center | grep -i "lago\|webhook"
   ```

### User Not Found in Keycloak

Error: `User not found: user@example.com`

**Solutions:**
1. Verify user exists in Keycloak realm `uchub`
2. Check email address matches exactly (case-sensitive)
3. Ensure user has logged in at least once

### Authentication Failed

Error: `Failed to authenticate with Keycloak`

**Solutions:**
1. Verify `KEYCLOAK_ADMIN_PASSWORD` is correct
2. Check admin user has permissions in master realm
3. Test authentication manually:
   ```bash
   curl -X POST "https://auth.your-domain.com/realms/master/protocol/openid-connect/token" \
     -d "username=admin" \
     -d "password=your-admin-password" \
     -d "grant_type=password" \
     -d "client_id=admin-cli"
   ```

### Invalid Signature

Error: `Invalid Lago webhook signature`

**Solutions:**
1. Verify `LAGO_WEBHOOK_SECRET` matches Lago admin panel
2. Check Lago webhook logs for signature value
3. Temporarily disable signature verification for testing (not recommended for production)

## API Reference

### Keycloak Integration Module

Location: `/home/muut/Production/UC-1-Pro/services/ops-center/backend/keycloak_integration.py`

#### Key Functions

##### `get_admin_token() -> str`

Get admin access token for Keycloak API calls.

**Returns:** Access token string

**Raises:** `httpx.HTTPStatusError` if authentication fails

##### `get_user_by_email(email: str) -> Optional[Dict]`

Find user by email address.

**Args:**
- `email`: User's email address

**Returns:** User dict if found, None otherwise

##### `update_user_attributes(email: str, attributes: Dict[str, List[str]])`

Update user attributes in Keycloak.

**Args:**
- `email`: User's email address
- `attributes`: Dict of attributes (values must be arrays)

**Example:**
```python
await update_user_attributes(
    "user@example.com",
    {
        "subscription_tier": ["professional"],
        "subscription_status": ["active"]
    }
)
```

**Raises:**
- `ValueError` if user not found
- `httpx.HTTPStatusError` if API call fails

### Webhook Handler

Location: `/home/muut/Production/UC-1-Pro/services/ops-center/backend/lago_webhooks.py`

#### Endpoints

##### `POST /api/v1/webhooks/lago`

Receive webhook events from Lago.

**Headers:**
- `X-Lago-Signature`: HMAC signature for verification

**Body:** Lago event payload (JSON)

**Response:** `{"status": "received", "event_type": "..."}`

##### `GET /api/v1/webhooks/lago/health`

Health check for webhook system.

**Response:**
```json
{
  "status": "healthy",
  "webhook_endpoint": "/api/v1/webhooks/lago",
  "signature_verification": true,
  "keycloak": { ... }
}
```

## Security Considerations

1. **Always use HTTPS** for webhook endpoint
2. **Enable signature verification** in production
3. **Rotate webhook secret** periodically
4. **Monitor webhook logs** for suspicious activity
5. **Rate limit** webhook endpoint if needed
6. **Validate all input** from webhook payloads

## Support

For issues or questions:

1. Check Ops Center logs: `docker logs unicorn-ops-center`
2. Check Keycloak logs: `docker logs keycloak`
3. Review Lago webhook delivery logs in admin panel
4. Contact support: admin@example.com

## Related Documentation

- [Keycloak Setup Guide](/home/muut/Production/UC-1-Pro/services/ops-center/KEYCLOAK_SETUP.md)
- [Billing Integration](/home/muut/Production/UC-1-Pro/services/ops-center/BILLING_API_IMPLEMENTATION.md)
- [Subscription Management](/home/muut/Production/UC-1-Pro/services/ops-center/SUBSCRIPTION_FEATURE_SUMMARY.md)
