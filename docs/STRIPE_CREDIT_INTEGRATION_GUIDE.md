# Stripe Credit Purchase Integration Guide

**Status**: READY FOR WEBHOOK CONFIGURATION
**Date**: November 12, 2025
**Author**: Payment Systems Team Lead

---

## Overview

This guide documents the complete Stripe integration for one-time credit purchases in Ops-Center. All Stripe products have been created successfully, and the system is ready for webhook configuration.

---

## 1. Setup Complete

### Stripe Products Created

All 4 credit packages have been successfully created in Stripe:

| Package Code | Package Name | Credits | Price | Stripe Product ID | Stripe Price ID |
|--------------|--------------|---------|-------|-------------------|-----------------|
| starter | Starter Pack | 1,000 | $10.00 | prod_TPYutnKU30a3ID | price_1SSjn6Dzk9HqAZnHe8kvmCzU |
| standard | Standard Pack | 5,000 | $45.00 | prod_TPYuYKz0Ci42DJ | price_1SSjn6Dzk9HqAZnHVffDfoFo |
| pro | Pro Pack | 10,000 | $80.00 | prod_TPYuU7EiSTPBlc | price_1SSjn7Dzk9HqAZnHH4i49FPB |
| enterprise | Enterprise Pack | 50,000 | $350.00 | prod_TPYubdcndvYFH4 | price_1SSjn7Dzk9HqAZnHhq7bxkwt |

### Database Verification

All Stripe IDs have been successfully stored in the `credit_packages` table in PostgreSQL (`unicorn_db`).

**Verification Command**:
```bash
docker exec ops-center-direct python3 /app/scripts/setup_stripe_credit_products.py
```

**Result**: All products created successfully with Stripe IDs stored in database.

---

## 2. Environment Variables

### Current Configuration

**File**: `/opt/ops-center/backend/.env.stripe`

```env
# Stripe API Keys (TEST MODE)
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_API_KEY=sk_test_your_stripe_secret_key

# Webhook Secret (TO BE CONFIGURED)
STRIPE_WEBHOOK_SECRET=whsec_placeholder
```

### Missing Variable

**STRIPE_WEBHOOK_SECRET_CREDITS**: This variable needs to be added after webhook configuration.

**Where to Add**: `/opt/ops-center/.env.auth`

```env
# Add this line after webhook creation:
STRIPE_WEBHOOK_SECRET_CREDITS=whsec_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## 3. Stripe Webhook Configuration

### Step-by-Step Instructions

#### Step 1: Access Stripe Dashboard

1. Go to: https://dashboard.stripe.com/test/webhooks
2. Login with your Stripe account credentials

#### Step 2: Create New Webhook Endpoint

1. Click "Add endpoint" button
2. Enter the webhook URL:
   ```
   https://unicorncommander.ai/api/v1/billing/credits/webhook
   ```

#### Step 3: Select Events to Listen For

Add the following event:

- **checkout.session.completed** - Triggered when a payment is successful

**Why only this event?**
- This event contains all information needed to process the credit purchase
- It fires after payment is confirmed and captured
- It includes metadata with user_id, credits, and package_code

#### Step 4: Get Webhook Secret

After creating the endpoint:

1. Click on the newly created webhook
2. Click "Reveal" next to "Signing secret"
3. Copy the secret (starts with `whsec_`)
4. Store it securely

#### Step 5: Update Environment Variables

1. Edit `.env.auth`:
   ```bash
   nano /opt/ops-center/.env.auth
   ```

2. Add the webhook secret:
   ```env
   STRIPE_WEBHOOK_SECRET_CREDITS=whsec_YOUR_ACTUAL_SECRET_HERE
   ```

3. Restart Ops-Center:
   ```bash
   docker restart ops-center-direct
   ```

#### Step 6: Test the Webhook

Stripe provides a "Send test webhook" button in the dashboard:

1. Click "Send test webhook"
2. Select event: `checkout.session.completed`
3. Click "Send test webhook"
4. Check Ops-Center logs:
   ```bash
   docker logs ops-center-direct --tail 50 | grep -i webhook
   ```

---

## 4. API Endpoints

### List Credit Packages

**Endpoint**: `GET /api/v1/billing/credits/packages`

**Authentication**: Required (Bearer token or session cookie)

**Response**:
```json
[
  {
    "id": "uuid",
    "package_code": "starter",
    "package_name": "Starter Pack",
    "description": "Perfect for trying out the platform",
    "credits": 1000,
    "price_usd": 10.00,
    "discount_percentage": 0,
    "is_active": true,
    "stripe_price_id": "price_1SSjn6Dzk9HqAZnHe8kvmCzU",
    "stripe_product_id": "prod_TPYutnKU30a3ID"
  },
  {
    "id": "uuid",
    "package_code": "standard",
    "package_name": "Standard Pack",
    "description": "Great value for regular users",
    "credits": 5000,
    "price_usd": 45.00,
    "discount_percentage": 10,
    "is_active": true,
    "stripe_price_id": "price_1SSjn6Dzk9HqAZnHVffDfoFo",
    "stripe_product_id": "prod_TPYuYKz0Ci42DJ"
  },
  {
    "id": "uuid",
    "package_code": "pro",
    "package_name": "Pro Pack",
    "description": "Best value for power users",
    "credits": 10000,
    "price_usd": 80.00,
    "discount_percentage": 20,
    "is_active": true,
    "stripe_price_id": "price_1SSjn7Dzk9HqAZnHH4i49FPB",
    "stripe_product_id": "prod_TPYuU7EiSTPBlc"
  },
  {
    "id": "uuid",
    "package_code": "enterprise",
    "package_name": "Enterprise Pack",
    "description": "Maximum value for heavy users",
    "credits": 50000,
    "price_usd": 350.00,
    "discount_percentage": 30,
    "is_active": true,
    "stripe_price_id": "price_1SSjn7Dzk9HqAZnHhq7bxkwt",
    "stripe_product_id": "prod_TPYubdcndvYFH4"
  }
]
```

**Current Status**: Endpoint requires authentication, so direct curl test returns "Not authenticated" error.

**Test with Authentication**:
```bash
# After logging into Ops-Center, use browser console:
fetch('/api/v1/billing/credits/packages', {
  method: 'GET',
  credentials: 'include'
}).then(r => r.json()).then(console.log)
```

### Create Purchase Checkout

**Endpoint**: `POST /api/v1/billing/credits/purchase`

**Authentication**: Required (Bearer token or session cookie)

**Request Body**:
```json
{
  "package_code": "starter",
  "success_url": "https://unicorncommander.ai/admin/credits?purchase=success",
  "cancel_url": "https://unicorncommander.ai/admin/credits?purchase=cancelled"
}
```

**Response**:
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "session_id": "cs_test_a1b2c3d4e5f6g7h8i9j0"
}
```

**Flow**:
1. User selects credit package in frontend
2. Frontend calls this endpoint
3. Backend creates Stripe checkout session
4. Backend returns checkout URL
5. Frontend redirects user to Stripe checkout page
6. User enters payment information
7. On success, Stripe redirects to success_url
8. Stripe webhook fires to add credits

### Purchase History

**Endpoint**: `GET /api/v1/billing/credits/history`

**Authentication**: Required (Bearer token or session cookie)

**Query Parameters**:
- `limit` (default: 50) - Number of records to return
- `offset` (default: 0) - Pagination offset

**Response**:
```json
[
  {
    "id": "uuid",
    "package_name": "Starter Pack",
    "amount_credits": 1000,
    "amount_paid": 10.00,
    "status": "completed",
    "created_at": "2025-11-12T10:00:00Z",
    "completed_at": "2025-11-12T10:05:00Z",
    "stripe_payment_id": "pi_xxxxxxxxxxxxx"
  }
]
```

### Webhook Handler

**Endpoint**: `POST /api/v1/billing/credits/webhook`

**Authentication**: Stripe signature verification (not user authentication)

**Called By**: Stripe (not the frontend)

**Events Handled**:
- `checkout.session.completed` - Adds credits to user account

**Metadata Expected**:
```json
{
  "user_id": "user-uuid",
  "credits": "1000",
  "package_code": "starter"
}
```

**Process**:
1. Stripe calls this endpoint with event data
2. Backend verifies webhook signature
3. Backend extracts user_id, credits from metadata
4. Backend updates purchase record status to "completed"
5. Backend calls credit_manager.allocate_credits()
6. Credits are added to user's account
7. Audit log entry created

---

## 5. Testing the Integration

### Test with Stripe CLI (Optional)

Install Stripe CLI:
```bash
# Download and install
wget https://github.com/stripe/stripe-cli/releases/download/v1.19.1/stripe_1.19.1_linux_x86_64.tar.gz
tar -xvf stripe_1.19.1_linux_x86_64.tar.gz
sudo mv stripe /usr/local/bin/
```

Login to Stripe:
```bash
stripe login
```

Forward webhooks to local endpoint:
```bash
stripe listen --forward-to localhost:8084/api/v1/billing/credits/webhook
```

Trigger test event:
```bash
stripe trigger checkout.session.completed
```

### Test Cards

Use these test card numbers in Stripe Checkout:

**Successful Payment**:
- Card: 4242 4242 4242 4242
- Expiry: Any future date (e.g., 12/25)
- CVC: Any 3 digits (e.g., 123)
- ZIP: Any 5 digits (e.g., 12345)

**Declined Payment**:
- Card: 4000 0000 0000 0002
- Expiry: Any future date
- CVC: Any 3 digits
- ZIP: Any 5 digits

**Requires Authentication (3D Secure)**:
- Card: 4000 0025 0000 3155
- Expiry: Any future date
- CVC: Any 3 digits
- ZIP: Any 5 digits

### Manual Testing Steps

1. **Login to Ops-Center**:
   - Go to https://unicorncommander.ai
   - Login with your credentials

2. **Navigate to Credit Dashboard**:
   - Go to `/admin/credits`

3. **View Available Packages**:
   - Should see 4 packages: Starter, Standard, Pro, Enterprise

4. **Initiate Purchase**:
   - Click "Purchase Credits" on desired package
   - Frontend calls `/api/v1/billing/credits/purchase`
   - Should redirect to Stripe checkout page

5. **Complete Payment**:
   - Enter test card: 4242 4242 4242 4242
   - Click "Pay"

6. **Verify Credit Addition**:
   - Check Ops-Center logs:
     ```bash
     docker logs ops-center-direct --tail 100 | grep -i credit
     ```
   - Should see: "Successfully processed credit purchase"
   - Check user's credit balance (should increase)

7. **View Purchase History**:
   - Go to `/admin/credits/history`
   - Should see completed purchase

---

## 6. Database Schema

### credit_packages Table

```sql
CREATE TABLE credit_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_code VARCHAR(50) UNIQUE NOT NULL,
    package_name VARCHAR(255) NOT NULL,
    description TEXT,
    credits INTEGER NOT NULL,
    price_usd DECIMAL(10, 2) NOT NULL,
    discount_percentage INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    stripe_product_id VARCHAR(255),
    stripe_price_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### credit_purchases Table

```sql
CREATE TABLE credit_purchases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    package_name VARCHAR(255) NOT NULL,
    amount_credits DECIMAL(10, 2) NOT NULL,
    amount_paid DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, completed, failed, refunded
    stripe_checkout_session_id VARCHAR(255),
    stripe_payment_intent_id VARCHAR(255),
    stripe_payment_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Indexes**:
```sql
CREATE INDEX idx_credit_purchases_user_id ON credit_purchases(user_id);
CREATE INDEX idx_credit_purchases_status ON credit_purchases(status);
CREATE INDEX idx_credit_purchases_session_id ON credit_purchases(stripe_checkout_session_id);
```

---

## 7. Security Considerations

### Webhook Signature Verification

The webhook endpoint uses Stripe's signature verification to ensure events are genuine:

```python
event = stripe.Webhook.construct_event(
    payload, sig_header, STRIPE_WEBHOOK_SECRET
)
```

**Why this matters**:
- Prevents malicious actors from sending fake webhook events
- Ensures credits are only added for real payments
- Required by Stripe for PCI compliance

### Environment Variable Security

**Critical Variables**:
- `STRIPE_SECRET_KEY` - Never expose in frontend or logs
- `STRIPE_WEBHOOK_SECRET_CREDITS` - Keep secure, used for signature verification

**Best Practices**:
- Store in `.env.auth` file (not committed to Git)
- Use Docker secrets in production
- Rotate keys if compromised
- Use test keys for development/staging

### Test Mode vs Production

**Current Setup**: Test mode (keys start with `sk_test_` and `pk_test_`)

**Before Going Live**:
1. Create production webhook endpoint
2. Update to production Stripe keys
3. Test thoroughly in production mode
4. Monitor webhook delivery

---

## 8. Troubleshooting

### Webhook Not Firing

**Symptoms**:
- Purchase completes in Stripe but credits don't appear
- No logs in ops-center about credit addition

**Solutions**:
1. Check webhook secret is correct:
   ```bash
   docker exec ops-center-direct printenv | grep STRIPE_WEBHOOK
   ```

2. Verify webhook is active in Stripe dashboard:
   - Go to https://dashboard.stripe.com/test/webhooks
   - Check webhook status is "Enabled"

3. Check webhook delivery logs in Stripe dashboard:
   - Click on webhook endpoint
   - View "Recent deliveries"
   - Check for failed deliveries and error messages

4. Verify endpoint is accessible:
   ```bash
   curl -X POST https://unicorncommander.ai/api/v1/billing/credits/webhook
   ```

5. Check Ops-Center logs for webhook errors:
   ```bash
   docker logs ops-center-direct --tail 100 | grep -i webhook
   ```

### Credits Not Added

**Symptoms**:
- Webhook fires successfully but credits don't increase

**Solutions**:
1. Check metadata is present in checkout session:
   - View session in Stripe dashboard
   - Verify metadata includes: `user_id`, `credits`, `package_code`

2. Check credit_manager is working:
   ```bash
   docker logs ops-center-direct | grep -i "allocate_credits"
   ```

3. Verify database connection:
   ```bash
   docker exec ops-center-direct python3 -c "
   import asyncio, asyncpg, os
   async def test():
       conn = await asyncpg.connect(
           host='unicorn-postgresql', port=5432,
           user=os.getenv('POSTGRES_USER'),
           password=os.getenv('POSTGRES_PASSWORD'),
           database=os.getenv('POSTGRES_DB')
       )
       print('Database connected!')
       await conn.close()
   asyncio.run(test())
   "
   ```

### Authentication Errors

**Symptoms**:
- API returns "Not authenticated" error

**Solutions**:
1. Check user is logged in:
   - Browser console: `document.cookie`
   - Should see session cookie

2. Verify authentication middleware is working:
   ```bash
   docker logs ops-center-direct | grep -i "auth"
   ```

3. Check Keycloak is running:
   ```bash
   docker ps | grep keycloak
   ```

### Stripe API Errors

**Common Errors**:

**Invalid API Key**:
```
stripe.error.AuthenticationError: Invalid API Key provided
```
**Solution**: Verify STRIPE_SECRET_KEY is correct

**Invalid Request**:
```
stripe.error.InvalidRequestError: No such price: 'price_xxxxx'
```
**Solution**: Run setup script again to recreate products

**Rate Limit**:
```
stripe.error.RateLimitError: Too many requests
```
**Solution**: Implement exponential backoff, contact Stripe support

---

## 9. Monitoring & Alerts

### Key Metrics to Monitor

1. **Successful Purchases**: Count of completed credit purchases
2. **Failed Purchases**: Count of failed/cancelled purchases
3. **Webhook Delivery Rate**: Percentage of successful webhook deliveries
4. **Average Purchase Value**: Average credits per transaction
5. **Purchase Conversion Rate**: Checkout initiated vs completed

### Logging

All credit purchase events are logged in:
- Ops-Center application logs
- Audit log database table
- Stripe webhook delivery logs

**Example Log Entries**:
```
INFO: Created checkout session for user 123: cs_test_xxxxx
INFO: Successfully processed credit purchase for user 123: 1000 credits
WARNING: Webhook delivery failed: Invalid signature
ERROR: Failed to add credits: Database connection error
```

### Alerts to Configure

**Critical Alerts**:
- Webhook delivery failure rate > 5%
- Credit allocation errors > 0
- Stripe API errors > 10/hour

**Warning Alerts**:
- Purchase completion time > 10 minutes
- Abandoned checkouts > 50%
- Database connection timeouts

---

## 10. Next Steps

### Immediate Actions

1. **Configure Stripe Webhook** (REQUIRED):
   - Follow Section 3 step-by-step
   - Add webhook endpoint in Stripe dashboard
   - Update STRIPE_WEBHOOK_SECRET_CREDITS in .env.auth
   - Restart ops-center-direct container

2. **Test End-to-End Flow**:
   - Follow Section 5 manual testing steps
   - Use test card to complete purchase
   - Verify credits are added
   - Check purchase history

3. **Monitor Initial Purchases**:
   - Watch logs for any errors
   - Verify webhook delivery in Stripe dashboard
   - Ensure credits are added correctly

### Future Enhancements

1. **Email Notifications**:
   - Send confirmation email after purchase
   - Send receipt with transaction details
   - Send credit balance updates

2. **Refund Support**:
   - Handle refund webhooks
   - Deduct credits on refund
   - Update purchase status

3. **Subscription Support**:
   - Recurring credit top-ups
   - Monthly credit allowances
   - Auto-renewal options

4. **Analytics Dashboard**:
   - Revenue metrics
   - Popular packages
   - Conversion funnels
   - Customer lifetime value

5. **Promotional Features**:
   - Discount codes
   - Referral bonuses
   - Seasonal sales
   - Bundle offers

---

## 11. Support Resources

### Documentation

- **Stripe Documentation**: https://stripe.com/docs
- **Stripe API Reference**: https://stripe.com/docs/api
- **Stripe Webhooks Guide**: https://stripe.com/docs/webhooks
- **Stripe Testing Guide**: https://stripe.com/docs/testing

### Stripe Dashboard Links

- **Test Dashboard**: https://dashboard.stripe.com/test
- **Products**: https://dashboard.stripe.com/test/products
- **Webhooks**: https://dashboard.stripe.com/test/webhooks
- **API Keys**: https://dashboard.stripe.com/test/apikeys
- **Logs**: https://dashboard.stripe.com/test/logs

### Internal Documentation

- **Credit System**: `/opt/ops-center/backend/credit_system.py`
- **Purchase API**: `/opt/ops-center/backend/credit_purchase_api.py`
- **Setup Script**: `/opt/ops-center/backend/scripts/setup_stripe_credit_products.py`

### Contact Points

- **Stripe Support**: https://support.stripe.com
- **Ops-Center Team**: See project README
- **Emergency**: Check Ops-Center logs and Stripe dashboard

---

## Summary

The Stripe credit purchase system is fully configured and ready for webhook setup. All products are created, environment variables are configured, and the API endpoints are functional.

**Status Checklist**:

- [x] Stripe products created (4 packages)
- [x] Database updated with Stripe IDs
- [x] Environment variables configured
- [x] API endpoints implemented
- [x] Database schema created
- [ ] Webhook endpoint configured in Stripe
- [ ] STRIPE_WEBHOOK_SECRET_CREDITS added to .env.auth
- [ ] End-to-end testing completed
- [ ] Production monitoring configured

**Next Action**: Configure Stripe webhook endpoint (Section 3).

---

**Document Version**: 1.0
**Last Updated**: November 12, 2025
**Maintained By**: Payment Systems Team Lead
