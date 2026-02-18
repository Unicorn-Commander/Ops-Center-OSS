# Quick Testing Guide - Subscription Payment Flow

**Status**: ✅ All fixes deployed - Ready to test!

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Configure Stripe Webhook (ONE TIME)

1. **Go to**: https://dashboard.stripe.com/test/webhooks
2. **Click**: "Add endpoint"
3. **Webhook URL**:
   ```
   https://unicorncommander.ai/api/v1/billing/webhooks/stripe/checkout
   ```
4. **Select Events**: `checkout.session.completed`
5. **Click**: "Add endpoint"
6. **Copy webhook secret** (starts with `whsec_...`)
7. **Add to environment**:
   ```bash
   cd /opt/ops-center

   # Edit .env.auth
   vim .env.auth

   # Add/update line:
   STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET_HERE

   # Restart
   docker restart ops-center-direct
   ```

### Step 2: Test Payment Flow (2 Minutes)

1. **Open**: https://unicorncommander.ai/admin/subscription/plan
2. **Click**: "View Plans" or "Upgrade Plan"
3. **Click**: "Select Plan" on **Trial** ($1.00/week)
4. **You should see**: Stripe Checkout page
5. **Enter test card**:
   ```
   Card Number: 4242 4242 4242 4242
   Expiry: 12/25
   CVC: 123
   ZIP: 12345
   Name: Test User
   ```
6. **Click**: "Subscribe"
7. **You should see**: Success page

### Step 3: Verify Backend (1 Minute)

```bash
# Check webhook received event
docker logs ops-center-direct --tail 20 | grep checkout.session.completed

# Check Lago subscription created
curl -s https://billing-api.unicorncommander.ai/api/v1/subscriptions \
  -H "Authorization: Bearer your-lago-api-key" | grep -i email
```

---

## 🧪 Full Test Cases

### ✅ Test 1: Successful Payment

**URL**: https://unicorncommander.ai/admin/subscription/plan

**Steps**:
1. Click "Select Plan" on **Trial**
2. Enter test card: `4242 4242 4242 4242`
3. Complete payment

**Expected**:
- ✅ Redirected to Stripe Checkout
- ✅ Price shows $1.00/week
- ✅ Payment completes successfully
- ✅ Redirected to success page
- ✅ Webhook processes event
- ✅ Lago subscription created
- ✅ Keycloak tier updated

### ❌ Test 2: Canceled Payment

**Steps**:
1. Click "Select Plan"
2. In Stripe Checkout, click **← Back**

**Expected**:
- ✅ Redirected back to plans page
- ✅ Error message: "Checkout was canceled..."
- ✅ No subscription created

### ❌ Test 3: Declined Card

**Steps**:
1. Click "Select Plan"
2. Enter declined card: `4000 0000 0000 0002`
3. Try to complete payment

**Expected**:
- ✅ Stripe shows "Card declined"
- ✅ User remains on Stripe page
- ✅ Can try different card
- ✅ No subscription created

---

## 🎯 Stripe Test Cards

### Successful Cards

| Card Number | Expiry | CVC | ZIP |
|------------|--------|-----|-----|
| 4242 4242 4242 4242 | Any | Any | Any |
| 4000 0566 5566 5556 | Any | Any | Any |

### Declined Cards

| Card Number | Error |
|------------|-------|
| 4000 0000 0000 0002 | Generic decline |
| 4000 0000 0000 9995 | Insufficient funds |
| 4000 0000 0000 0069 | Expired card |
| 4000 0000 0000 0127 | CVC incorrect |

**More cards**: https://stripe.com/docs/testing#cards

---

## 🔍 Debugging

### Check Backend Logs

```bash
# Real-time logs
docker logs ops-center-direct -f | grep -E "(checkout|stripe|webhook)"

# Last 50 lines
docker logs ops-center-direct --tail 50
```

### Check Stripe Environment

```bash
docker exec ops-center-direct printenv | grep STRIPE
```

### Test Stripe Connection

```bash
docker exec ops-center-direct python3 << 'EOF'
import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
balance = stripe.Balance.retrieve()
print(f"✅ Stripe connection OK - Balance: {balance}")
EOF
```

### Check Webhook Endpoint

```bash
# Test webhook endpoint is accessible
curl -I https://unicorncommander.ai/api/v1/billing/webhooks/stripe/checkout
```

---

## 📊 What Should Happen

### Frontend (User Sees)

```
1. Plans page → Click "Select Plan"
2. Loading modal → "Redirecting to Stripe Checkout..."
3. Stripe Checkout page → Payment form
4. Success page → "Subscription activated!"
```

### Backend (Logs Show)

```
1. POST /api/v1/billing/subscriptions/checkout
   → Creating Stripe checkout session...
   → Checkout session created: cs_test_...

2. POST /api/v1/billing/webhooks/stripe/checkout
   → Webhook received: checkout.session.completed
   → Processing checkout session: cs_test_...
   → User email: user@example.com
   → Creating Lago customer...
   → Creating Lago subscription...
   → Updating Keycloak tier to: trial
   → ✅ Subscription activated
```

### Lago Dashboard

```
Visit: https://billing.unicorncommander.ai
Login: admin@example.com / your-admin-password

Should see:
- New customer: user@example.com
- New subscription: Trial plan, Active
- Next billing date: 7 days from now
```

### Keycloak Admin

```
Visit: https://auth.unicorncommander.ai/admin/uchub/console
Login: admin / your-admin-password
Navigate: Users → Find user by email

Should see (in Attributes tab):
- subscription_tier: trial
- subscription_status: active
- api_calls_limit: 700 (100 per day × 7 days)
```

---

## ✅ Success Checklist

After testing, verify:

```
Payment Flow:
✅ Stripe checkout appears with correct plan/price
✅ Test card completes payment successfully
✅ User redirected to success page after payment
✅ Canceled checkout returns to plans page with error
✅ Declined card shows error on Stripe page

Backend Integration:
✅ Webhook received checkout.session.completed event
✅ Lago customer created (check billing dashboard)
✅ Lago subscription created with correct plan
✅ Keycloak user tier updated to subscription tier
✅ User can access subscription features

All Plans:
✅ Trial ($1/week) checkout works
✅ Starter ($19/month) checkout works
✅ Professional ($49/month) checkout works
✅ Enterprise ($99/month) checkout works
```

---

## 🎉 If Everything Works

Congratulations! The payment flow is fully operational.

**Next steps**:
1. Test with all 4 subscription tiers
2. Test upgrade/downgrade flows
3. Test subscription cancellation
4. Configure annual prices (optional)
5. Switch to live Stripe keys when ready for production

---

## 🐛 Common Issues

### Issue: Webhook not received

**Fix**: Check webhook is configured in Stripe dashboard with correct URL

### Issue: "Invalid signature" error

**Fix**: Verify STRIPE_WEBHOOK_SECRET matches Stripe dashboard

### Issue: Lago subscription not created

**Fix**: Check LAGO_API_KEY is correct, check Lago service is running

### Issue: Keycloak tier not updated

**Fix**: Check KEYCLOAK_ADMIN_PASSWORD is correct

---

**Quick Reference**: This guide covers the essential testing steps. For comprehensive documentation, see `PHASE_2_PAYMENT_FLOW_COMPLETE.md`.

**Estimated Testing Time**: 10-15 minutes

**Current Status**: ✅ All backend/frontend changes deployed, ready to test with your Stripe test keys!
