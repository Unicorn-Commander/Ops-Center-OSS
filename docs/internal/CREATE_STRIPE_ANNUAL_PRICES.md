# Creating Annual Stripe Prices - Step-by-Step Guide

**Status**: ⚠️ REQUIRED BEFORE PRODUCTION
**Priority**: HIGH
**Estimated Time**: 15-20 minutes

---

## Prerequisites

- Access to Stripe Dashboard: https://dashboard.stripe.com/test
- Stripe account with existing monthly prices configured
- Text editor to copy/paste price IDs

---

## Current Monthly Prices

These monthly prices already exist:

| Plan | Monthly Price ID | Amount |
|------|------------------|--------|
| Trial | `price_1SI0FHDzk9HqAZnHbUgvaidP` | $1.00/week |
| Starter | `price_1SI0FHDzk9HqAZnHAsMKY9tS` | $19.00/month |
| Professional | `price_1SI0FIDzk9HqAZnHgA63KIpk` | $49.00/month |
| Enterprise | `price_1SI0FIDzk9HqAZnHZFRzBjgP` | $99.00/month |

---

## Step-by-Step Instructions

### 1. Access Stripe Dashboard

```bash
# Open in browser
https://dashboard.stripe.com/test/products
```

Login with Stripe account credentials.

---

### 2. Create Annual Price for Starter Plan

1. Click on the **Starter** product (or find product with monthly price `price_1SI0FHDzk9HqAZnHAsMKY9tS`)

2. Scroll to "Pricing" section

3. Click **"+ Add another price"**

4. Configure the annual price:
   - **Price**: $190.00 USD
   - **Billing period**: Yearly (12 months)
   - **Usage is metered**: Leave unchecked
   - **Price description**: "Annual subscription - $15.83/month (17% savings)"

5. Click **"Add price"**

6. **Copy the price ID** (format: `price_XXXXXXXXXXXX`)
   - Example: `price_1SJabcDzk9HqAZnH12345678`

7. Update `subscription_manager.py`:
   ```python
   # Line 98
   stripe_annual_price_id="price_PASTE_HERE"  # Replace with copied ID
   ```

---

### 3. Create Annual Price for Professional Plan

1. Click on the **Professional** product (or find product with monthly price `price_1SI0FIDzk9HqAZnHgA63KIpk`)

2. Click **"+ Add another price"**

3. Configure:
   - **Price**: $490.00 USD
   - **Billing period**: Yearly (12 months)
   - **Price description**: "Annual subscription - $40.83/month (17% savings)"

4. Click **"Add price"**

5. **Copy the price ID**

6. Update `subscription_manager.py`:
   ```python
   # Line 129 (Professional)
   stripe_annual_price_id="price_PASTE_HERE"

   # Line 163 (Founder's Friend - same as Professional)
   stripe_annual_price_id="price_PASTE_HERE"
   ```

---

### 4. Create Annual Price for Enterprise Plan

1. Click on the **Enterprise** product (or find product with monthly price `price_1SI0FIDzk9HqAZnHZFRzBjgP`)

2. Click **"+ Add another price"**

3. Configure:
   - **Price**: $990.00 USD
   - **Billing period**: Yearly (12 months)
   - **Price description**: "Annual subscription - $82.50/month (17% savings)"

4. Click **"Add price"**

5. **Copy the price ID**

6. Update `subscription_manager.py`:
   ```python
   # Line 196
   stripe_annual_price_id="price_PASTE_HERE"
   ```

---

### 5. Update Configuration File

Edit the subscription manager file:

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center
vim backend/subscription_manager.py
```

Replace all `TODO: Create annual price in Stripe` comments with actual price IDs.

**Example**:
```python
# BEFORE:
stripe_annual_price_id="price_1SI0FHDzk9HqAZnHAsMKY9tS"  # TODO: Create annual price in Stripe

# AFTER:
stripe_annual_price_id="price_1SJabcDzk9HqAZnH12345678"  # Annual: $190/year
```

---

### 6. Restart Service

Apply the configuration changes:

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center
docker restart ops-center-direct

# Wait for startup
sleep 5

# Verify service is running
docker logs ops-center-direct --tail 20
```

Look for:
```
INFO:server:Stripe payment API endpoints registered at /api/v1/billing
INFO:     Application startup complete.
```

---

### 7. Test Annual Pricing

#### Verify Plans API Returns Annual Prices

```bash
curl https://your-domain.com/api/v1/billing/plans | jq '.[] | {
  id: .id,
  name: .display_name,
  monthly: .price_monthly,
  yearly: .price_yearly,
  stripe_monthly: .stripe_price_id,
  stripe_annual: .stripe_annual_price_id
}'
```

Expected output:
```json
{
  "id": "starter",
  "name": "Starter",
  "monthly": 19,
  "yearly": 190,
  "stripe_monthly": "price_1SI0FHDzk9HqAZnHAsMKY9tS",
  "stripe_annual": "price_1SJabcDzk9HqAZnH12345678"  // NEW PRICE ID
}
```

#### Test Checkout Session Creation

```bash
# Test yearly checkout
curl -X POST https://your-domain.com/api/v1/billing/subscriptions/checkout \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tier_id": "starter",
    "billing_cycle": "yearly"
  }'
```

Expected response:
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "session_id": "cs_test_..."
}
```

#### Complete Test Checkout

1. Open the `checkout_url` in browser
2. Use Stripe test card: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVC: Any 3 digits
   - ZIP: Any 5 digits
3. Complete payment
4. Verify you're charged $190 (not $19)
5. Check subscription in Stripe Dashboard shows "Yearly" interval

---

## Verification Checklist

After creating all annual prices, verify:

- [ ] Starter annual price created ($190/year)
- [ ] Professional annual price created ($490/year)
- [ ] Enterprise annual price created ($990/year)
- [ ] All price IDs copied to `subscription_manager.py`
- [ ] Service restarted successfully
- [ ] `/api/v1/billing/plans` returns correct annual price IDs
- [ ] Checkout session creates with annual price ID when `billing_cycle=yearly`
- [ ] Test payment completes successfully
- [ ] Stripe Dashboard shows subscription with yearly interval

---

## Pricing Summary

| Plan | Monthly | Annual | Savings | Effective Monthly |
|------|---------|--------|---------|-------------------|
| Trial | $1/week | N/A | N/A | N/A |
| Starter | $19/month | $190/year | $38 (17%) | $15.83/month |
| Professional | $49/month | $490/year | $98 (17%) | $40.83/month |
| Founder's Friend | $49/month | $490/year | $98 (17%) | $40.83/month |
| Enterprise | $99/month | $990/year | $198 (17%) | $82.50/month |

**Savings Calculation**:
- Monthly cost × 12 months = Full annual cost
- Annual price = 10 months of service (2 months free)
- Savings = (Monthly × 12) - Annual

---

## Troubleshooting

### "Price not found" Error

**Cause**: Price ID doesn't exist in Stripe
**Solution**: Double-check price ID copied correctly, verify in Stripe Dashboard

### Checkout Shows Monthly Price Instead of Annual

**Cause**: Code not updated or service not restarted
**Solution**:
```bash
# Verify price ID in code
grep -A 1 "stripe_annual_price_id" backend/subscription_manager.py

# Restart service
docker restart ops-center-direct
```

### Wrong Amount Charged

**Cause**: Wrong price ID used
**Solution**: Check Stripe Dashboard → Prices to verify the price ID matches the annual amount

---

## Production Deployment

Once tested in test mode:

1. **Switch to Live Mode** in Stripe Dashboard
2. **Create annual prices in live mode** (repeat steps above)
3. **Update `.env.auth`** with live Stripe keys:
   ```bash
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_PUBLISHABLE_KEY=pk_live_...
   ```
4. **Update `subscription_manager.py`** with LIVE annual price IDs
5. **Restart service** in production
6. **Test with real card** (small amount first!)

---

## Quick Reference Commands

```bash
# View current configuration
docker exec ops-center-direct cat /app/backend/subscription_manager.py | grep stripe_annual_price_id

# Restart after changes
docker restart ops-center-direct

# Check logs for errors
docker logs ops-center-direct --tail 50 | grep -i stripe

# Test plans API
curl https://your-domain.com/api/v1/billing/plans | jq

# Test checkout (replace YOUR_TOKEN)
curl -X POST https://your-domain.com/api/v1/billing/subscriptions/checkout \
  -H "Cookie: session_token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tier_id":"starter","billing_cycle":"yearly"}'
```

---

## Related Documentation

- **Stripe Integration Fixes**: `/services/ops-center/STRIPE_INTEGRATION_FIXES.md`
- **Ops-Center Configuration**: `/services/ops-center/CLAUDE.md`
- **Stripe Dashboard**: https://dashboard.stripe.com/test
- **Stripe Price API Docs**: https://stripe.com/docs/api/prices

---

**Last Updated**: October 23, 2025
**Status**: Awaiting annual price creation
**Priority**: HIGH - Required before production launch
