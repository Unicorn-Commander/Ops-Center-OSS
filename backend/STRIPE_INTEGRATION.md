# Stripe Payment Integration for UC-1 Pro

Complete Stripe payment processing integration for the UC-1 Pro billing system with Keycloak SSO and Lago billing platform synchronization.

## Overview

This integration provides:
- **Subscription Management**: Create, update, and cancel subscriptions
- **Payment Processing**: Stripe Checkout for secure payment collection
- **Webhook Handling**: Automatic synchronization of payment events
- **Customer Portal**: Self-service subscription management
- **Multi-platform Sync**: Automatic updates to Keycloak and Lago

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Stripe    │────▶│  Ops Center  │────▶│   Keycloak   │
│  (Payment)  │     │   (Backend)  │     │    (Auth)    │
└─────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │     Lago     │
                    │   (Billing)  │
                    └──────────────┘
```

## Files Created

### Core Integration
- **`stripe_integration.py`** - Stripe client wrapper with all core functions
- **`stripe_api.py`** - FastAPI endpoints for payment operations
- **`setup_stripe_products.py`** - Script to create Stripe products and prices

### Configuration
- **`.env.stripe.example`** - Environment variable template
- **`STRIPE_INTEGRATION.md`** - This documentation file

### Server Updates
- **`server.py`** - Added Stripe router registration and webhook CSRF exemption
- **`requirements.txt`** - Added `stripe==10.0.0` dependency

## Installation

### 1. Install Dependencies

```bash
cd /home/deploy/Production/UC-1-Pro/services/ops-center/backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example file and update with your values:

```bash
cp .env.stripe.example .env
# Edit .env with your Stripe credentials
```

Required environment variables:
```bash
STRIPE_API_KEY=sk_test_...           # Stripe secret key
STRIPE_WEBHOOK_SECRET=whsec_...      # Webhook signing secret
STRIPE_SUCCESS_URL=https://unicorncommander.ai/billing/success
STRIPE_CANCEL_URL=https://unicorncommander.ai/billing/canceled
```

### 3. Set Up Stripe Products

Run the setup script to create products and prices in Stripe:

```bash
python setup_stripe_products.py
```

This will create 4 products:
- **Trial** - $1/month (7-day trial)
- **Starter** - $19/month or $190/year
- **Professional** - $49/month or $490/year
- **Enterprise** - $99/month or $990/year

The script will output price IDs that you need to add to `subscription_manager.py`.

### 4. Update Subscription Manager

Edit `subscription_manager.py` and add the Stripe price IDs:

```python
SubscriptionPlan(
    id="trial",
    name="trial",
    # ... other fields ...
    stripe_price_id="price_xxxxxxxxxxxxx"  # Add this
),
```

### 5. Configure Stripe Webhook

1. Go to [Stripe Dashboard → Webhooks](https://dashboard.stripe.com/webhooks)
2. Click "Add endpoint"
3. Set endpoint URL: `https://unicorncommander.ai/api/v1/billing/webhooks/stripe`
4. Select these events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`
5. Copy the webhook signing secret
6. Add to `.env` as `STRIPE_WEBHOOK_SECRET`

## API Endpoints

All endpoints are prefixed with `/api/v1/billing`

### Create Checkout Session
```http
POST /api/v1/billing/checkout/create
Content-Type: application/json

{
  "tier_id": "professional",
  "billing_cycle": "monthly"
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_...",
  "session_id": "cs_..."
}
```

### Create Customer Portal Session
```http
POST /api/v1/billing/portal/create
```

**Response:**
```json
{
  "portal_url": "https://billing.stripe.com/p/session/..."
}
```

### Get Payment Methods
```http
GET /api/v1/billing/payment-methods
```

**Response:**
```json
[
  {
    "id": "pm_...",
    "brand": "visa",
    "last4": "4242",
    "exp_month": 12,
    "exp_year": 2025
  }
]
```

### Get Subscription Status
```http
GET /api/v1/billing/subscription-status
```

**Response:**
```json
{
  "has_subscription": true,
  "current_tier": "professional",
  "status": "active",
  "subscriptions": [
    {
      "id": "sub_...",
      "status": "active",
      "current_period_end": "2025-11-11T00:00:00",
      "cancel_at_period_end": false,
      "tier_name": "professional",
      "billing_cycle": "monthly",
      "amount": 49.0
    }
  ]
}
```

### Cancel Subscription
```http
POST /api/v1/billing/subscription/cancel
Content-Type: application/json

{
  "subscription_id": "sub_...",
  "at_period_end": true
}
```

### Upgrade/Downgrade Subscription
```http
POST /api/v1/billing/subscription/upgrade
Content-Type: application/json

{
  "new_tier_id": "enterprise",
  "billing_cycle": "yearly"
}
```

### Webhook Endpoint (Stripe Only)
```http
POST /api/v1/billing/webhooks/stripe
Stripe-Signature: t=...,v1=...
```

## Webhook Events Handled

### checkout.session.completed
- Creates/updates Stripe customer
- Activates subscription in Keycloak
- Creates customer in Lago
- Sets user tier and status

### customer.subscription.created
- Records subscription start date
- Updates user tier in Keycloak
- Syncs to Lago

### customer.subscription.updated
- Updates subscription status (active, past_due, etc.)
- Updates tier if changed
- Syncs to Keycloak and Lago

### customer.subscription.deleted
- Downgrades user to trial tier
- Marks subscription as cancelled
- Updates all systems

### invoice.paid
- Confirms active subscription status
- Resets any past_due status
- Updates payment tracking

### invoice.payment_failed
- Marks subscription as past_due
- Can trigger grace period logic
- Notifies user (future enhancement)

## Data Synchronization

### Keycloak User Attributes

The integration updates these Keycloak user attributes:

```python
{
  "subscription_tier": ["professional"],
  "subscription_status": ["active"],
  "stripe_customer_id": ["cus_..."],
  "stripe_subscription_id": ["sub_..."],
  "subscription_start_date": ["2025-10-11T00:00:00"],
  "subscription_end_date": ["2025-11-11T00:00:00"]
}
```

### Lago Customer Sync

Creates/updates Lago customer with:
- External ID: Stripe customer ID
- Payment provider configuration
- Metadata with tier and subscription info

## Security

### CSRF Protection
- Webhook endpoint is CSRF-exempt (verified by Stripe signature)
- All other endpoints require valid CSRF token
- Webhook signatures validated using Stripe's library

### Authentication
- All endpoints require authenticated user
- User email extracted from session/JWT
- Subscription operations validated against user ownership

### Rate Limiting
- Standard rate limits apply to all endpoints
- Webhook endpoint has higher limits for reliability

## Testing

### Test Mode
1. Use Stripe test API key: `sk_test_...`
2. Use test webhook secret: `whsec_test_...`
3. Test cards: https://stripe.com/docs/testing

### Test Card Numbers
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- Authentication Required: `4000 0025 0000 3155`

### Testing Webhooks Locally

Use Stripe CLI to forward webhooks to localhost:

```bash
stripe listen --forward-to localhost:8084/api/v1/billing/webhooks/stripe
```

## Error Handling

### Common Issues

**"No Stripe customer found"**
- User hasn't subscribed yet
- Solution: Create checkout session first

**"Failed to create checkout session"**
- Invalid price ID in subscription_manager.py
- Solution: Run setup_stripe_products.py and update price IDs

**"CSRF validation failed"**
- Webhook endpoint not in CSRF exempt list
- Solution: Already added to server.py

**"Invalid webhook signature"**
- Wrong webhook secret
- Solution: Copy correct secret from Stripe dashboard

## Monitoring

### Logs
All operations are logged with appropriate levels:
- INFO: Successful operations
- WARNING: Payment failures, downgrades
- ERROR: Integration failures, webhook errors

### Check Logs
```bash
# Ops Center logs
docker logs unicorn-ops-center

# Filter for Stripe events
docker logs unicorn-ops-center 2>&1 | grep -i stripe
```

### Stripe Dashboard
Monitor in real-time:
- [Payments](https://dashboard.stripe.com/payments)
- [Subscriptions](https://dashboard.stripe.com/subscriptions)
- [Webhooks](https://dashboard.stripe.com/webhooks)
- [Customers](https://dashboard.stripe.com/customers)

## Production Checklist

Before going live:

- [ ] Set `STRIPE_API_KEY` to live key (`sk_live_...`)
- [ ] Set `STRIPE_WEBHOOK_SECRET` to live webhook secret
- [ ] Run `setup_stripe_products.py` in live mode
- [ ] Update price IDs in `subscription_manager.py`
- [ ] Configure live webhook endpoint in Stripe
- [ ] Test full payment flow in live mode
- [ ] Set up Stripe email notifications
- [ ] Configure invoice settings
- [ ] Set up tax collection (if required)
- [ ] Enable 3D Secure authentication
- [ ] Review fraud detection settings

## Support

### Stripe Documentation
- [API Reference](https://stripe.com/docs/api)
- [Webhooks](https://stripe.com/docs/webhooks)
- [Testing](https://stripe.com/docs/testing)

### UC-1 Pro Support
- Documentation: https://github.com/Unicorn-Commander/UC-1-Pro
- Issues: https://github.com/Unicorn-Commander/UC-1-Pro/issues

## Future Enhancements

Planned features:
- [ ] Proration handling for upgrades/downgrades
- [ ] Usage-based billing integration
- [ ] Coupon and discount support
- [ ] Free trial extension logic
- [ ] Payment retry logic
- [ ] Email notifications for payment events
- [ ] Revenue analytics dashboard
- [ ] Refund handling
- [ ] Multi-currency support
- [ ] Payment method update flow

---

**Last Updated:** October 11, 2025
**Version:** 1.0.0
**Maintainer:** UC-1 Pro Team
