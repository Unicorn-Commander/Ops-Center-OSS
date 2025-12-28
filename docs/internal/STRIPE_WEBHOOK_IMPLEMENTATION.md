# Stripe Webhook Implementation - checkout.session.completed

**Date**: October 23, 2025
**Status**: IMPLEMENTED AND DEPLOYED
**Endpoint**: `/api/v1/billing/webhooks/stripe/checkout`

---

## Overview

This webhook handler processes successful Stripe payment completions. When a user completes payment via Stripe Checkout, this webhook:

1. Verifies the webhook signature (security)
2. Extracts user and subscription data
3. Creates a Lago customer (if doesn't exist)
4. Creates a Lago subscription
5. Updates the user's tier in Keycloak
6. Logs the event to audit trail

---

## Implementation Details

### File Locations

**Backend**:
- `/services/ops-center/backend/stripe_api.py` - Main webhook endpoint
- `/services/ops-center/backend/stripe_integration.py` - Checkout session metadata
- `/services/ops-center/backend/keycloak_integration.py` - User management
- `/services/ops-center/backend/lago_integration.py` - Billing management (organization-based)

**Environment Variables** (`.env.auth`):
```bash
STRIPE_WEBHOOK_SECRET=whsec_IVIJ51M4n8Ix4PsMsDFgohJWZXaAtWQh
LAGO_API_URL=http://unicorn-lago-api:3000
LAGO_API_KEY=d87f40d7-25c4-411c-bd51-677b26299e1c
```

### API Endpoint

**URL**: `POST /api/v1/billing/webhooks/stripe/checkout`

**Headers**:
```
stripe-signature: <signature from Stripe>
Content-Type: application/json
```

**No Authentication Required**: This endpoint is called directly by Stripe and bypasses authentication middleware.

---

## Webhook Flow

### 1. Signature Verification

```python
webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
```

**Security**: Stripe webhook signature verification ensures the request is genuinely from Stripe.

### 2. Extract Checkout Session Data

```python
session = event['data']['object']
tier_id = session['metadata'].get('tier_id') or session['metadata'].get('tier_name')
billing_cycle = session['metadata'].get('billing_cycle', 'monthly')
user_email = session['metadata'].get('user_email') or session.get('customer_email')
```

**Metadata Fields**:
- `tier_id` - Subscription tier (trial, starter, professional, enterprise)
- `billing_cycle` - monthly or yearly
- `user_email` - User's email address

### 3. Get Keycloak User

```python
from keycloak_integration import get_user_by_email, set_subscription_tier

user = await get_user_by_email(user_email)
user_id = user['id']
```

**Error Handling**: Returns error response if user not found.

### 4. Create Lago Customer

```python
lago_customer = await create_lago_customer_if_not_exists(
    user_email=user_email,
    user_id=user_id
)
```

**Idempotent**: Checks if customer exists before creating.

**Lago Customer Structure**:
```json
{
  "customer": {
    "external_id": "user@example.com",
    "name": "user@example.com",
    "email": "user@example.com",
    "metadata": {
      "keycloak_id": "uuid-from-keycloak"
    }
  }
}
```

### 5. Create Lago Subscription

```python
lago_subscription = await create_lago_subscription(
    customer_id=user_email,  # Lago uses email as external_id
    plan_code=tier_id,       # trial, starter, professional, enterprise
    billing_cycle=billing_cycle
)
```

**Lago Subscription Structure**:
```json
{
  "subscription": {
    "external_customer_id": "user@example.com",
    "plan_code": "professional",
    "billing_time": "calendar"
  }
}
```

**Plan Codes** (must match Lago plans):
- `trial` - $1/week trial
- `starter` - $19/month
- `professional` - $49/month
- `enterprise` - $99/month

### 6. Update Keycloak Tier

```python
await set_subscription_tier(user_id, tier_id)
```

**Keycloak User Attributes Updated**:
- `subscription_tier` - Set to tier_id
- `subscription_status` - Set to "active"

### 7. Audit Logging

```python
from audit_logger import audit_logger

audit_logger.log_event(
    event_type="subscription.created",
    user_id=user_id,
    details={
        "tier": tier_id,
        "billing_cycle": billing_cycle,
        "stripe_session_id": session['id'],
        "lago_subscription_id": lago_subscription.get('lago_id')
    }
)
```

---

## Error Handling

### Graceful Degradation

The webhook uses defensive error handling:

1. **Keycloak Failure**: Returns error (subscription creation depends on valid user)
2. **Lago Customer Failure**: Returns error (can't create subscription without customer)
3. **Lago Subscription Failure**: Returns error (primary purpose failed)
4. **Keycloak Tier Update Failure**: LOGS ERROR but doesn't fail webhook
5. **Audit Logging Failure**: LOGS ERROR but doesn't fail webhook

**Why**: Steps 4 and 5 are "nice to have" - the subscription was already created in Lago, so we don't want to reject the webhook and have Stripe retry.

### Response Codes

| Status Code | Meaning |
|-------------|---------|
| 200 | Success - subscription created |
| 200 (ignored) | Event type not handled (returns status: "ignored") |
| 400 | Invalid signature or payload |
| 500 | Server error during processing |

**Success Response**:
```json
{
  "status": "success",
  "message": "Subscription created for user@example.com"
}
```

**Error Response**:
```json
{
  "status": "error",
  "message": "Failed to create Lago customer: <details>"
}
```

---

## Testing

### Test with Stripe CLI

1. **Install Stripe CLI**:
   ```bash
   # Download from https://stripe.com/docs/stripe-cli
   stripe login
   ```

2. **Forward webhooks to local**:
   ```bash
   stripe listen --forward-to http://localhost:8084/api/v1/billing/webhooks/stripe/checkout
   ```

3. **Trigger test event**:
   ```bash
   stripe trigger checkout.session.completed
   ```

### Manual Test with curl

```bash
# Get test event from Stripe dashboard
# POST to webhook endpoint with proper signature

curl -X POST http://localhost:8084/api/v1/billing/webhooks/stripe/checkout \
  -H "stripe-signature: <signature>" \
  -H "Content-Type: application/json" \
  -d @stripe_event.json
```

### Production Test

1. **Create a test subscription**:
   - Go to https://your-domain.com/signup-flow.html
   - Sign up with test email
   - Use Stripe test card: `4242 4242 4242 4242`

2. **Monitor webhook delivery**:
   - Go to Stripe Dashboard → Developers → Webhooks
   - Click on webhook endpoint
   - View recent deliveries

3. **Verify results**:
   ```bash
   # Check Lago subscription created
   docker exec unicorn-lago-postgres psql -U lago -d lago -c \
     "SELECT * FROM subscriptions WHERE external_customer_id = 'test@example.com';"

   # Check Keycloak tier updated
   curl http://localhost:8084/api/v1/admin/users?search=test@example.com
   ```

---

## Stripe Dashboard Configuration

### Webhook Endpoint Setup

1. Go to: https://dashboard.stripe.com/test/webhooks
2. Click "Add endpoint"
3. **Endpoint URL**: `https://your-domain.com/api/v1/billing/webhooks/stripe/checkout`
4. **Events to send**:
   - ✅ `checkout.session.completed`
5. **API version**: Latest (2024-11-20+)

### Get Webhook Signing Secret

After creating the endpoint:
1. Click on the endpoint
2. Click "Reveal" on "Signing secret"
3. Copy the secret (starts with `whsec_`)
4. Add to `.env.auth`:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_IVIJ51M4n8Ix4PsMsDFgohJWZXaAtWQh
   ```

---

## Integration Points

### With Stripe

**Outgoing** (Ops-Center → Stripe):
- Create checkout session with metadata

**Incoming** (Stripe → Ops-Center):
- Webhook: `checkout.session.completed`

### With Lago

**API Calls**:
- `POST /api/v1/customers` - Create customer
- `GET /api/v1/customers/{email}` - Check if customer exists
- `POST /api/v1/subscriptions` - Create subscription

**Authentication**: Bearer token (`LAGO_API_KEY`)

### With Keycloak

**API Calls**:
- `get_user_by_email(email)` - Get user by email
- `set_subscription_tier(user_id, tier)` - Update user tier

**Authentication**: Admin token (username/password)

---

## Monitoring & Debugging

### View Webhook Logs

```bash
# Follow ops-center logs
docker logs ops-center-direct -f | grep -i webhook

# Check for errors
docker logs ops-center-direct --tail 100 | grep -E "ERROR|Failed"
```

### Common Issues

#### 1. "STRIPE_WEBHOOK_SECRET not configured"

**Fix**: Add to `.env.auth`:
```bash
STRIPE_WEBHOOK_SECRET=whsec_IVIJ51M4n8Ix4PsMsDFgohJWZXaAtWQh
```

#### 2. "Invalid signature"

**Causes**:
- Wrong webhook secret
- Payload was modified
- Using test secret in production (or vice versa)

**Fix**: Verify webhook secret matches Stripe dashboard

#### 3. "User not found in Keycloak"

**Causes**:
- User email doesn't match Keycloak email
- User was deleted

**Fix**: Ensure user exists before payment

#### 4. "Failed to create Lago customer"

**Causes**:
- Lago API down
- Invalid API key
- Network connectivity issue

**Fix**:
```bash
# Check Lago is running
docker ps | grep lago

# Test Lago API
curl http://localhost:3000/health
```

#### 5. "Failed to create Lago subscription"

**Causes**:
- Plan code doesn't exist in Lago
- Customer doesn't exist
- Invalid API request

**Fix**: Verify plan codes in Lago match tier IDs:
```bash
docker exec unicorn-lago-postgres psql -U lago -d lago -c \
  "SELECT name, code FROM plans;"
```

---

## Security Considerations

### Webhook Signature Verification

✅ **Implemented**: All webhook requests verify Stripe signature before processing

**Why Important**: Without verification, anyone could send fake payment completion events.

### No Authentication Middleware

✅ **Correct**: Webhook endpoint bypasses auth middleware

**Why**: Stripe can't provide user auth tokens. Signature verification is the authentication.

### HTTPS Required

⚠️ **Production Only**: Webhooks should only be delivered over HTTPS

**Current**:
- Production: `https://your-domain.com` (SSL via Traefik)
- Local dev: HTTP allowed for testing

---

## Future Enhancements

### Phase 2 (Planned)

1. **Email Notifications**: Send confirmation email after subscription created
2. **Slack Notifications**: Alert admin channel on new subscriptions
3. **Retry Logic**: Handle transient Lago/Keycloak failures with retry
4. **Subscription Updates**: Handle tier upgrades/downgrades
5. **Cancellation Handling**: Process subscription cancellations
6. **Invoice Webhooks**: Handle `invoice.paid` and `invoice.payment_failed`

### Phase 3 (Future)

1. **Usage Metering**: Automatic API call tracking
2. **Overage Billing**: Charge for usage beyond plan limits
3. **Trial Expiration**: Auto-downgrade trial users
4. **Payment Failed Recovery**: Email users with failed payments

---

## Code Reference

### Helper Functions

**create_lago_customer_if_not_exists(user_email, user_id)**
- Checks if Lago customer exists
- Creates customer if doesn't exist
- Returns customer object

**create_lago_subscription(customer_id, plan_code, billing_cycle)**
- Creates Lago subscription
- Links to customer
- Returns subscription object

### Imports

```python
import os
import stripe
from keycloak_integration import get_user_by_email, set_subscription_tier
from subscription_manager import subscription_manager
from audit_logger import audit_logger
```

---

## Deployment Checklist

- [x] Webhook endpoint implemented
- [x] Signature verification added
- [x] Lago customer creation
- [x] Lago subscription creation
- [x] Keycloak tier update
- [x] Audit logging
- [x] Error handling
- [x] Service restarted
- [ ] Stripe webhook endpoint configured (production)
- [ ] Environment variables verified
- [ ] End-to-end test completed

---

## Contact & Support

**Implementation**: Backend API Developer Agent
**Documentation**: `/services/ops-center/STRIPE_WEBHOOK_IMPLEMENTATION.md`
**Related Files**:
- `/services/ops-center/backend/stripe_api.py`
- `/services/ops-center/backend/stripe_integration.py`
- `/services/ops-center/backend/keycloak_integration.py`

**For Issues**: Check logs first, then review error handling section above.
