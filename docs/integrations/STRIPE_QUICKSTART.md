# Stripe Integration - Quick Start Guide

## 🚀 5-Minute Setup

### Prerequisites
- Stripe account (sign up at https://stripe.com)
- UC-1 Pro Ops Center running
- Admin access to Keycloak

### Step 1: Install Dependencies (30 seconds)

```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center
pip install stripe==10.0.0
```

### Step 2: Get Stripe API Keys (1 minute)

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/apikeys)
2. Copy your **Secret key** (starts with `sk_test_` or `sk_live_`)
3. Add to your environment:

```bash
export STRIPE_API_KEY="sk_test_..."
```

### Step 3: Create Products in Stripe (2 minutes)

```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center
python backend/setup_stripe_products.py
```

This will:
- Create 4 products (Trial, Starter, Professional, Enterprise)
- Create monthly and yearly prices
- Output price IDs you need for next step

### Step 4: Update Price IDs (1 minute)

Edit `backend/subscription_manager.py` and add the price IDs from Step 3:

```python
SubscriptionPlan(
    id="trial",
    # ... other fields ...
    stripe_price_id="price_xxxxxxxxxxxxx"  # Add this line
),
```

Repeat for all 4 tiers.

### Step 5: Configure Webhook (1 minute)

1. Go to [Stripe Webhooks](https://dashboard.stripe.com/webhooks)
2. Click **Add endpoint**
3. Enter URL: `https://your-domain.com/api/v1/billing/webhooks/stripe`
4. Select events:
   - ✅ `checkout.session.completed`
   - ✅ `customer.subscription.created`
   - ✅ `customer.subscription.updated`
   - ✅ `customer.subscription.deleted`
   - ✅ `invoice.paid`
   - ✅ `invoice.payment_failed`
5. Copy **Signing secret** (starts with `whsec_`)
6. Add to environment:

```bash
export STRIPE_WEBHOOK_SECRET="whsec_..."
```

### Step 6: Restart Server (30 seconds)

```bash
docker restart unicorn-ops-center
```

## ✅ Verify Installation

Run the verification script:

```bash
python backend/verify_stripe_integration.py
```

Should see all green checkmarks ✓

## 🧪 Test Payment Flow

### Using Stripe Test Mode

1. **Test Card**: `4242 4242 4242 4242`
2. **Expiry**: Any future date
3. **CVC**: Any 3 digits
4. **ZIP**: Any 5 digits

### Test Checkout

```bash
curl -X POST https://your-domain.com/api/v1/billing/checkout/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "tier_id": "professional",
    "billing_cycle": "monthly"
  }'
```

Returns checkout URL → Open in browser → Complete payment with test card

## 📊 Monitor Payments

### View in Stripe Dashboard
- **Payments**: https://dashboard.stripe.com/payments
- **Subscriptions**: https://dashboard.stripe.com/subscriptions
- **Customers**: https://dashboard.stripe.com/customers
- **Webhooks**: https://dashboard.stripe.com/webhooks

### View in Logs
```bash
docker logs unicorn-ops-center 2>&1 | grep -i stripe
```

## 🔧 Troubleshooting

### "No module named 'stripe'"
```bash
pip install stripe==10.0.0
```

### "STRIPE_API_KEY not set"
```bash
export STRIPE_API_KEY="sk_test_..."
# Or add to .env file
```

### "Invalid webhook signature"
```bash
# Get correct secret from Stripe dashboard
export STRIPE_WEBHOOK_SECRET="whsec_..."
```

### "Price ID not configured"
```bash
# Run setup script and update subscription_manager.py
python backend/setup_stripe_products.py
```

## 📚 Full Documentation

- **Complete Guide**: `backend/STRIPE_INTEGRATION.md`
- **Implementation Report**: `STRIPE_IMPLEMENTATION_REPORT.md`
- **Environment Template**: `backend/.env.stripe.example`

## 🎯 API Endpoints Available

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/billing/checkout/create` | POST | Create checkout session |
| `/api/v1/billing/portal/create` | POST | Customer portal |
| `/api/v1/billing/payment-methods` | GET | List payment methods |
| `/api/v1/billing/subscription-status` | GET | Get subscription |
| `/api/v1/billing/subscription/cancel` | POST | Cancel subscription |
| `/api/v1/billing/subscription/upgrade` | POST | Change tier |
| `/api/v1/billing/webhooks/stripe` | POST | Stripe webhooks |

## 🚀 Go Live Checklist

When ready for production:

1. [ ] Get live API key from Stripe (starts with `sk_live_`)
2. [ ] Run `setup_stripe_products.py` in live mode
3. [ ] Update price IDs in `subscription_manager.py`
4. [ ] Configure live webhook endpoint
5. [ ] Update `STRIPE_API_KEY` to live key
6. [ ] Update `STRIPE_WEBHOOK_SECRET` to live secret
7. [ ] Test with real card (will charge!)
8. [ ] Enable email receipts in Stripe
9. [ ] Configure tax settings if needed
10. [ ] Set up monitoring alerts

## 💡 Tips

- **Always test in test mode first** - Use `sk_test_` keys
- **Keep webhook secrets secure** - Never commit to git
- **Monitor webhook deliveries** - Check Stripe dashboard
- **Test all scenarios** - Success, failure, cancellation
- **Check Keycloak sync** - Verify user attributes updated
- **Review Lago data** - Ensure billing records created

---

**Need Help?**
- Full docs: `backend/STRIPE_INTEGRATION.md`
- Stripe docs: https://stripe.com/docs
- Support: https://github.com/Unicorn-Commander/UC-1-Pro/issues
