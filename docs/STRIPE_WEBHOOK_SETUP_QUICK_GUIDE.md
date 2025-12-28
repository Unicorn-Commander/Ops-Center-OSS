# Stripe Webhook Setup - Quick Guide

**Date**: November 12, 2025
**Status**: READY FOR USER CONFIGURATION

---

## Quick Setup Steps

### 1. Login to Stripe Dashboard

Go to: **https://dashboard.stripe.com/test/webhooks**

### 2. Create New Webhook

Click **"Add endpoint"** button

### 3. Enter Webhook URL

```
https://your-domain.com/api/v1/billing/credits/webhook
```

### 4. Select Event

Check the box for:

- **checkout.session.completed**

### 5. Get Webhook Secret

After creation:

1. Click on the webhook you just created
2. Find "Signing secret" section
3. Click **"Reveal"** button
4. Copy the secret (starts with `whsec_`)

### 6. Update Environment Variable

Edit the file:
```bash
nano /home/muut/Production/UC-Cloud/services/ops-center/.env.auth
```

Add this line at the end:
```env
STRIPE_WEBHOOK_SECRET_CREDITS=whsec_YOUR_SECRET_HERE
```

Replace `whsec_YOUR_SECRET_HERE` with the actual secret from Stripe.

### 7. Restart Ops-Center

```bash
docker restart ops-center-direct
```

### 8. Verify Setup

Check logs for successful startup:
```bash
docker logs ops-center-direct --tail 50 | grep -i stripe
```

---

## Testing the Webhook

### Option 1: Stripe Dashboard Test

1. Go to your webhook in Stripe dashboard
2. Click **"Send test webhook"**
3. Select event: **checkout.session.completed**
4. Click **"Send test webhook"**
5. Check response is 200 OK

### Option 2: Test Purchase

1. Login to Ops-Center: https://your-domain.com
2. Go to Credit Dashboard: `/admin/credits`
3. Click "Purchase Credits" on Starter Pack
4. Use test card: **4242 4242 4242 4242**
5. Expiry: **12/25**, CVC: **123**, ZIP: **12345**
6. Complete payment
7. Verify credits were added

### Option 3: Check Webhook Logs

View webhook delivery logs in Stripe:
1. Go to webhook endpoint
2. Click **"Recent deliveries"** tab
3. Check for successful deliveries (200 status)
4. View request/response details

---

## What Happens After Webhook Configuration?

1. User purchases credits via Stripe Checkout
2. Stripe processes payment
3. Stripe sends webhook to Ops-Center
4. Ops-Center verifies webhook signature
5. Ops-Center adds credits to user account
6. User sees updated credit balance

---

## Troubleshooting

### Webhook Not Firing

**Check**:
- Webhook is enabled in Stripe dashboard
- URL is exactly: `https://your-domain.com/api/v1/billing/credits/webhook`
- Event `checkout.session.completed` is selected

**Fix**:
- Verify URL has no typos
- Make sure endpoint is reachable: `curl -X POST https://your-domain.com/api/v1/billing/credits/webhook`

### Invalid Signature Error

**Check**:
- STRIPE_WEBHOOK_SECRET_CREDITS is correct in .env.auth
- Secret matches the one in Stripe dashboard

**Fix**:
- Copy secret again from Stripe
- Update .env.auth
- Restart ops-center-direct

### Credits Not Added

**Check**:
- Webhook delivered successfully (200 status)
- Ops-Center logs show "Successfully processed credit purchase"

**Fix**:
```bash
# View logs
docker logs ops-center-direct --tail 100 | grep -i credit

# Check database connection
docker exec ops-center-direct python3 -c "
import asyncio, asyncpg, os
async def test():
    conn = await asyncpg.connect(
        host='unicorn-postgresql', port=5432,
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB')
    )
    print('Database OK!')
    await conn.close()
asyncio.run(test())
"
```

---

## Important Notes

- Use **test mode** keys for development (start with `sk_test_`)
- Switch to **live mode** keys only when ready for production
- Keep webhook secret secure (never commit to Git)
- Monitor webhook delivery in Stripe dashboard

---

## Need Help?

- **Stripe Webhook Docs**: https://stripe.com/docs/webhooks
- **Stripe Test Cards**: https://stripe.com/docs/testing
- **Full Guide**: See `STRIPE_CREDIT_INTEGRATION_GUIDE.md`

---

**Estimated Time**: 5-10 minutes
