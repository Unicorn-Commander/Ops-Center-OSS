# Subscription Payment Flow - Comprehensive Test Plan

**Version**: 1.0
**Date**: October 23, 2025
**Author**: UC-Cloud Testing Team
**Status**: Ready for Execution

## Executive Summary

This test plan validates the complete subscription payment flow after applying critical fixes to the Ops-Center billing system. It covers end-to-end user journeys, edge cases, integrations, security, and performance.

**Fixes Applied**:
1. ✅ Fixed Stripe price ID retrieval from plan metadata
2. ✅ Added success_url and cancel_url to checkout session
3. ✅ Fixed Lago customer creation payload structure
4. ✅ Added webhook signature verification
5. ✅ Added idempotency handling for duplicate webhooks
6. ✅ Enhanced error logging and handling
7. ✅ Added frontend success/cancel pages

---

## 1. Pre-Test Checklist

**Environment Verification** (Complete BEFORE starting tests):

### Infrastructure
- [ ] **Stripe Configuration**
  - [ ] Test publishable key in `.env.auth`: `STRIPE_PUBLISHABLE_KEY=pk_test_...`
  - [ ] Test secret key in `.env.auth`: `STRIPE_SECRET_KEY=sk_test_...`
  - [ ] Webhook endpoint configured in Stripe dashboard
  - [ ] Webhook secret in `.env.auth`: `STRIPE_WEBHOOK_SECRET=whsec_...`
  - [ ] Stripe dashboard accessible: https://dashboard.stripe.com/test

- [ ] **Lago Configuration**
  - [ ] Lago API accessible: https://billing-api.unicorncommander.ai/health
  - [ ] Lago API key configured: `LAGO_API_KEY=...`
  - [ ] Lago admin dashboard accessible: https://billing.unicorncommander.ai
  - [ ] All 4 subscription plans visible in Lago

- [ ] **Keycloak SSO**
  - [ ] Keycloak accessible: https://auth.unicorncommander.ai
  - [ ] uchub realm active
  - [ ] ops-center client configured
  - [ ] Test user account exists
  - [ ] Identity providers working (Google/GitHub/Microsoft)

- [ ] **Ops-Center Service**
  - [ ] Backend running: `docker ps | grep ops-center-direct`
  - [ ] Frontend rebuilt: `docker compose -f docker-compose.direct.yml build ops-center-direct`
  - [ ] Service restarted: `docker compose -f docker-compose.direct.yml restart ops-center-direct`
  - [ ] Health check passing: `curl https://unicorncommander.ai/api/v1/health`

### Plan Configuration Verification

- [ ] **Trial Plan** (`trial`)
  - [ ] Lago plan ID exists: `bbbba413-45de-468d-b03e-f23713684354`
  - [ ] Stripe price ID in metadata: `price_1SHCEsDzk9HqAZnHGaVxXxXx`
  - [ ] Price: $1.00/week
  - [ ] Trial period: 7 days

- [ ] **Starter Plan** (`starter`)
  - [ ] Lago plan ID exists: `02a9058d-e0f6-4e09-9c39-a775d57676d1`
  - [ ] Stripe price ID in metadata: `price_1SHCEsDzk9HqAZnHGaVxXxXx`
  - [ ] Price: $19.00/month

- [ ] **Professional Plan** (`professional`)
  - [ ] Lago plan ID exists: `0eefed2d-cdf8-4d0a-b5d0-852dacf9909d`
  - [ ] Stripe price ID in metadata: `price_1SHCEsDzk9HqAZnHGaVxXxXx`
  - [ ] Price: $49.00/month

- [ ] **Enterprise Plan** (`enterprise`)
  - [ ] Lago plan ID exists: `ee2d9d3d-e985-4166-97ba-2fd6e8cd5b0b`
  - [ ] Stripe price ID in metadata: `price_1SHCEsDzk9HqAZnHGaVxXxXx`
  - [ ] Price: $99.00/month

### Test Data Preparation

- [ ] Test Stripe cards ready (see section 2.1)
- [ ] Test user account credentials recorded
- [ ] Lago admin credentials available: `admin@example.com` / `your-admin-password`
- [ ] Browser developer tools open for debugging
- [ ] Screenshot tool ready for documentation

### Logging & Monitoring

- [ ] Backend logs streaming: `docker logs ops-center-direct -f`
- [ ] Stripe webhook logs accessible in dashboard
- [ ] Lago API logs available: `docker logs unicorn-lago-api -f`
- [ ] Browser console open for JavaScript errors

---

## 2. Test Cases by Plan Tier

### 2.1 Stripe Test Card Numbers

Use these official Stripe test cards:

| Purpose | Card Number | Expected Result |
|---------|-------------|-----------------|
| **Success** | `4242 4242 4242 4242` | Payment succeeds |
| **Declined** | `4000 0000 0000 0002` | Card declined |
| **Insufficient Funds** | `4000 0000 0000 9995` | Insufficient funds error |
| **Expired Card** | `4000 0000 0000 0069` | Expired card error |
| **Incorrect CVC** | `4000 0000 0000 0127` | Incorrect CVC error |
| **Processing Error** | `4000 0000 0000 0119` | Generic processing error |
| **Requires Auth** | `4000 0025 0000 3155` | 3D Secure authentication required |

**Additional Details for All Tests**:
- Expiry: Any future date (e.g., `12/26`)
- CVC: Any 3 digits (e.g., `123`)
- ZIP: Any 5 digits (e.g., `12345`)

---

### 2.2 Trial Plan ($1.00/week) - Test Suite

#### Test Case T1: Successful Trial Signup

**Prerequisites**:
- User logged into Ops-Center via Keycloak SSO
- User has no existing subscription
- Trial plan visible on plans page

**Test Steps**:
1. Navigate to `/admin/subscription/plan`
2. Locate "Trial Plan" card ($1.00/week)
3. Click "Select Plan" button
4. **Verify**: Redirected to Stripe Checkout
5. **Verify**: Checkout shows:
   - Amount: $1.00
   - Interval: weekly
   - Trial period: 7 days free
6. Enter payment details:
   - Card: `4242 4242 4242 4242`
   - Expiry: `12/26`
   - CVC: `123`
   - ZIP: `12345`
7. Click "Subscribe" button
8. **Verify**: Payment processing indicator appears
9. **Wait**: For redirect (should be < 5 seconds)
10. **Verify**: Redirected to `/admin/subscription/success?session_id=...`
11. **Verify**: Success page shows:
    - "Subscription Activated!" message
    - Plan details: Trial Plan
    - Next billing date displayed
    - Link to billing settings

**Backend Verification**:
```bash
# Check Lago subscription created
docker exec unicorn-lago-postgres psql -U lago -d lago -c \
  "SELECT * FROM subscriptions WHERE external_customer_id = 'USER_EMAIL' ORDER BY created_at DESC LIMIT 1;"

# Check Keycloak user tier updated
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users \
  --realm uchub --query "email=USER_EMAIL" \
  --fields id,attributes | grep subscription_tier

# Check audit log entry
docker exec ops-center-direct sqlite3 /app/data/audit.db \
  "SELECT * FROM audit_log WHERE user_email = 'USER_EMAIL' ORDER BY timestamp DESC LIMIT 5;"
```

**Expected Results**:
- ✅ Stripe checkout session created successfully
- ✅ Payment processed without errors
- ✅ User redirected to success page with session_id parameter
- ✅ Lago subscription created with status "active"
- ✅ Keycloak attribute `subscription_tier` = "trial"
- ✅ Keycloak attribute `subscription_status` = "active"
- ✅ Keycloak attribute `api_calls_limit` = "700" (100/day × 7 days)
- ✅ Audit log entry: "subscription_created" action recorded
- ✅ Stripe dashboard shows successful payment
- ✅ Lago dashboard shows new subscription

**Failure Criteria**:
- ❌ 404 error when selecting plan
- ❌ 500 error during checkout creation
- ❌ Stripe checkout doesn't load
- ❌ Payment succeeds but no subscription in Lago
- ❌ Keycloak attributes not updated
- ❌ User redirected to error page

**Screenshots to Capture**:
1. Plans page with Trial plan visible
2. Stripe checkout page with $1.00 amount
3. Success page after payment
4. Lago dashboard showing subscription
5. Keycloak user attributes showing trial tier

---

#### Test Case T2: Trial Signup - Payment Declined

**Prerequisites**: Same as T1

**Test Steps**:
1. Navigate to `/admin/subscription/plan`
2. Click "Select Plan" for Trial
3. Enter declined card: `4000 0000 0000 0002`
4. Click "Subscribe"
5. **Verify**: Stripe shows decline error message
6. **Verify**: User remains on checkout page
7. Click "Try Again"
8. Enter successful card: `4242 4242 4242 4242`
9. Complete payment
10. **Verify**: Success flow (same as T1)

**Expected Results**:
- ✅ Declined card shows appropriate error message
- ✅ No subscription created in Lago after decline
- ✅ No charge made to Stripe account
- ✅ User can retry with valid card
- ✅ Successful retry creates subscription normally

**Failure Criteria**:
- ❌ Declined card creates subscription anyway
- ❌ User can't retry payment
- ❌ Error message unclear or missing

---

#### Test Case T3: Trial Signup - Requires Authentication (3D Secure)

**Prerequisites**: Same as T1

**Test Steps**:
1. Navigate to `/admin/subscription/plan`
2. Click "Select Plan" for Trial
3. Enter authentication-required card: `4000 0025 0000 3155`
4. Click "Subscribe"
5. **Verify**: 3D Secure authentication modal appears
6. Click "Complete Authentication" in test modal
7. **Verify**: Authentication succeeds
8. **Verify**: Payment completes
9. **Verify**: Success flow (same as T1)

**Expected Results**:
- ✅ 3D Secure modal appears correctly
- ✅ Test authentication succeeds
- ✅ Payment completes after authentication
- ✅ Subscription created normally

---

### 2.3 Starter Plan ($19.00/month) - Test Suite

#### Test Case S1: Successful Starter Signup

**Prerequisites**:
- User logged into Ops-Center
- User has no existing subscription

**Test Steps**: (Same structure as T1 but with Starter plan specifics)

1. Navigate to `/admin/subscription/plan`
2. Locate "Starter Plan" card ($19.00/month)
3. Click "Select Plan" button
4. **Verify**: Checkout shows $19.00/month
5. Complete payment with `4242 4242 4242 4242`
6. **Verify**: Success page displayed
7. **Verify**: Keycloak tier = "starter"
8. **Verify**: API calls limit = 1,000

**Expected Results**:
- ✅ All same validations as Trial plan
- ✅ Keycloak attribute `subscription_tier` = "starter"
- ✅ Keycloak attribute `api_calls_limit` = "1000"
- ✅ User can access BYOK features
- ✅ Email support access enabled

---

### 2.4 Professional Plan ($49.00/month) - Test Suite

#### Test Case P1: Successful Professional Signup

**Prerequisites**: Same as S1

**Test Steps**: (Same structure as S1)

1. Navigate to `/admin/subscription/plan`
2. Locate "Professional Plan" card ($49.00/month)
3. Note "Most Popular" badge displayed
4. Click "Select Plan" button
5. **Verify**: Checkout shows $49.00/month
6. Complete payment
7. **Verify**: Tier = "professional"
8. **Verify**: API calls limit = 10,000

**Expected Results**:
- ✅ Keycloak attribute `subscription_tier` = "professional"
- ✅ Keycloak attribute `api_calls_limit` = "10000"
- ✅ Access to all services (Chat, Search, TTS, STT)
- ✅ Billing dashboard access enabled
- ✅ Priority support queue access

---

### 2.5 Enterprise Plan ($99.00/month) - Test Suite

#### Test Case E1: Successful Enterprise Signup

**Prerequisites**: Same as S1

**Test Steps**: (Same structure as P1)

1. Navigate to `/admin/subscription/plan`
2. Locate "Enterprise Plan" card ($99.00/month)
3. Click "Select Plan" button
4. **Verify**: Checkout shows $99.00/month
5. Complete payment
6. **Verify**: Tier = "enterprise"
7. **Verify**: API calls limit = "unlimited" or very high number

**Expected Results**:
- ✅ Keycloak attribute `subscription_tier` = "enterprise"
- ✅ Keycloak attribute `api_calls_limit` = "999999" (or unlimited)
- ✅ Team management features enabled
- ✅ Custom integrations available
- ✅ 24/7 support access
- ✅ White-label options visible

---

## 3. Edge Cases & Error Handling

### 3.1 User Cancels During Checkout

**Test Case EC1: Cancel Before Payment**

**Test Steps**:
1. Start checkout flow for any plan
2. Wait for Stripe checkout to load
3. Click browser "Back" button OR
4. Click "← Back" link in Stripe checkout
5. **Verify**: User returned to `/admin/subscription/plan`
6. **Verify**: No subscription created in Lago
7. **Verify**: No charge in Stripe
8. **Verify**: User can start new checkout

**Expected Results**:
- ✅ User navigates back to plan selection
- ✅ No subscription created
- ✅ No payment processed
- ✅ No audit log entry for subscription
- ✅ User can retry checkout

**Backend Verification**:
```bash
# Verify no Lago subscription
docker exec unicorn-lago-postgres psql -U lago -d lago -c \
  "SELECT COUNT(*) FROM subscriptions WHERE external_customer_id = 'USER_EMAIL';"
# Should return 0

# Verify no Stripe payment
# Check Stripe dashboard - Payments section should show no charge
```

---

### 3.2 Payment Failures

**Test Case EC2: Insufficient Funds**

**Test Steps**:
1. Start checkout for any plan
2. Enter card: `4000 0000 0000 9995`
3. Click "Subscribe"
4. **Verify**: Error message: "Your card has insufficient funds."
5. **Verify**: No subscription created
6. **Verify**: User remains on checkout page
7. Enter valid card and retry
8. **Verify**: Success flow works

**Expected Results**:
- ✅ Clear error message displayed
- ✅ No subscription created
- ✅ Retry mechanism works

---

**Test Case EC3: Expired Card**

**Test Steps**:
1. Start checkout for any plan
2. Enter card: `4000 0000 0000 0069`
3. Click "Subscribe"
4. **Verify**: Error message: "Your card has expired."
5. **Verify**: No subscription created
6. Retry with valid card

**Expected Results**:
- ✅ Clear error message
- ✅ No subscription created
- ✅ Retry works

---

**Test Case EC4: Incorrect CVC**

**Test Steps**:
1. Start checkout for any plan
2. Enter card: `4000 0000 0000 0127`
3. Click "Subscribe"
4. **Verify**: Error message: "Your card's security code is incorrect."
5. Retry with valid card

**Expected Results**:
- ✅ Clear error message
- ✅ No subscription created
- ✅ Retry works

---

### 3.3 Webhook Failures & Recovery

**Test Case EC5: Webhook Disabled During Payment**

**Test Steps**:
1. Temporarily disable webhook in Stripe dashboard:
   - Go to Developers → Webhooks
   - Click webhook endpoint
   - Click "Disable endpoint"
2. Complete payment for any plan using valid card
3. **Verify**: Payment succeeds in Stripe
4. **Verify**: User redirected to success page
5. **Verify**: Subscription NOT created in Lago (webhook failed)
6. Check backend logs for webhook error
7. Re-enable webhook in Stripe dashboard
8. Click "Send test webhook" in Stripe dashboard
9. Select event: `checkout.session.completed`
10. **Verify**: Webhook processes successfully
11. **Verify**: Subscription now created in Lago
12. **Verify**: Keycloak attributes updated

**Expected Results**:
- ✅ Payment succeeds regardless of webhook status
- ✅ Webhook failure logged in backend
- ✅ Manual webhook replay creates subscription
- ✅ User's payment is not lost
- ✅ Final state is consistent (subscription active)

**Backend Verification**:
```bash
# Check webhook error in logs
docker logs ops-center-direct | grep -i webhook | tail -20

# Verify Lago subscription after webhook replay
docker exec unicorn-lago-postgres psql -U lago -d lago -c \
  "SELECT external_id, status, created_at FROM subscriptions WHERE external_customer_id = 'USER_EMAIL';"
```

---

**Test Case EC6: Duplicate Webhook (Idempotency Test)**

**Test Steps**:
1. Complete successful payment for any plan
2. **Verify**: Subscription created in Lago
3. Record subscription ID from Lago
4. In Stripe dashboard, find the webhook event
5. Click "Resend" to replay webhook
6. **Verify**: Backend logs show "Duplicate webhook event" message
7. **Verify**: No duplicate subscription created in Lago
8. **Verify**: Original subscription unchanged

**Expected Results**:
- ✅ Duplicate webhook detected via `stripe_session_id` check
- ✅ No duplicate subscription created
- ✅ Idempotency key prevents duplicate processing
- ✅ Backend logs: "Webhook event already processed: session_id"

**Backend Verification**:
```bash
# Verify only one subscription exists
docker exec unicorn-lago-postgres psql -U lago -d lago -c \
  "SELECT COUNT(*) FROM subscriptions WHERE external_customer_id = 'USER_EMAIL';"
# Should return 1, not 2

# Check for idempotency log
docker logs ops-center-direct | grep -i "already processed" | tail -5
```

---

### 3.4 Invalid Requests

**Test Case EC7: Invalid Plan ID**

**Test Steps**:
1. Manually craft API request:
   ```bash
   curl -X POST https://unicorncommander.ai/api/v1/billing/subscriptions/checkout \
     -H "Authorization: Bearer USER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"tier_id": "invalid_plan_id"}'
   ```
2. **Verify**: Response code: 404
3. **Verify**: Error message: "Plan not found"
4. **Verify**: No checkout session created

**Expected Results**:
- ✅ 404 HTTP status code
- ✅ Clear error message in response body
- ✅ No Stripe session created
- ✅ Error logged in backend

---

**Test Case EC8: Missing Stripe Price ID**

**Test Steps**:
1. Temporarily remove Stripe price ID from a plan's metadata in Lago
2. Attempt to checkout with that plan
3. **Verify**: Response code: 500
4. **Verify**: Error message: "Stripe price ID not configured for this plan"
5. **Verify**: No checkout session created
6. Restore Stripe price ID

**Expected Results**:
- ✅ 500 HTTP status code
- ✅ Clear error message
- ✅ Backend logs error details
- ✅ No partial state created

---

**Test Case EC9: Stripe API Error**

**Test Steps**:
1. Temporarily change Stripe secret key to invalid value in `.env.auth`
2. Restart ops-center backend
3. Attempt to checkout with any plan
4. **Verify**: Response code: 400 or 500
5. **Verify**: Error message includes Stripe error details
6. **Verify**: User sees error page or message
7. Restore correct Stripe key
8. Restart backend
9. **Verify**: Checkout works again

**Expected Results**:
- ✅ Clear error message
- ✅ Stripe error details logged
- ✅ No subscription created
- ✅ Recovery works after fix

---

**Test Case EC10: Lago API Error**

**Test Steps**:
1. Temporarily change Lago API key to invalid value
2. Complete payment in Stripe (payment will succeed)
3. **Verify**: Webhook receives event
4. **Verify**: Backend logs Lago API error
5. **Verify**: Webhook returns error status
6. **Verify**: Stripe retries webhook automatically (after delays)
7. Restore correct Lago API key
8. Wait for Stripe webhook retry (or manually resend)
9. **Verify**: Subscription created on retry
10. **Verify**: Final state consistent

**Expected Results**:
- ✅ Payment not lost even with Lago error
- ✅ Error logged clearly
- ✅ Stripe webhook retry mechanism works
- ✅ Eventually consistent state achieved

---

## 4. Upgrade & Downgrade Tests

### 4.1 Plan Upgrades

**Test Case U1: Starter → Professional Upgrade**

**Prerequisites**:
- User has active Starter subscription ($19/month)
- User wants to upgrade to Professional ($49/month)

**Test Steps**:
1. Login to Ops-Center
2. Navigate to `/admin/subscription/plan`
3. **Verify**: Current plan badge shows "Starter (Active)"
4. Locate Professional plan card
5. Click "Upgrade to Professional" button
6. **Verify**: Modal appears explaining:
   - New price: $49/month
   - Proration details (credit for unused Starter time)
   - New billing date
7. Click "Confirm Upgrade"
8. **Verify**: Redirect to Stripe checkout
9. **Verify**: Checkout shows prorated amount
10. Complete payment
11. **Verify**: Success page shows upgraded plan
12. **Verify**: Keycloak tier updated to "professional"
13. **Verify**: API calls limit increased to 10,000
14. **Verify**: Lago subscription updated (not duplicate)

**Expected Results**:
- ✅ Proration calculated correctly
- ✅ Lago subscription updated (not new subscription)
- ✅ Keycloak attributes reflect new tier
- ✅ User immediately has Professional features
- ✅ Billing dashboard shows upgrade transaction

**Backend Verification**:
```bash
# Verify subscription upgraded (not duplicate)
docker exec unicorn-lago-postgres psql -U lago -d lago -c \
  "SELECT external_id, plan_code, status, updated_at FROM subscriptions WHERE external_customer_id = 'USER_EMAIL' ORDER BY updated_at DESC;"
# Should show ONE subscription with plan_code = 'professional'

# Verify Keycloak attributes
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users \
  --realm uchub --query "email=USER_EMAIL" \
  --fields attributes | grep subscription_tier
# Should show "professional"
```

---

**Test Case U2: Trial → Enterprise Upgrade**

**Prerequisites**:
- User has active Trial subscription ($1/week)
- User wants to upgrade to Enterprise ($99/month)

**Test Steps**: (Similar to U1)

1. Navigate to plans page
2. Click "Upgrade to Enterprise"
3. **Verify**: Modal explains upgrade from trial
4. Complete checkout
5. **Verify**: Trial subscription cancelled
6. **Verify**: Enterprise subscription activated
7. **Verify**: Unlimited API calls enabled
8. **Verify**: Team management features accessible

**Expected Results**:
- ✅ Trial subscription properly replaced
- ✅ No duplicate billing
- ✅ Enterprise features immediately available
- ✅ Team invite functionality works

---

### 4.2 Plan Downgrades

**Test Case D1: Professional → Starter Downgrade**

**Prerequisites**:
- User has active Professional subscription ($49/month)
- User wants to downgrade to Starter ($19/month)

**Test Steps**:
1. Navigate to `/admin/subscription/plan`
2. **Verify**: Current plan badge shows "Professional (Active)"
3. Locate Starter plan card
4. Click "Downgrade to Starter" button
5. **Verify**: Warning modal appears:
   - "Are you sure you want to downgrade?"
   - Lists features that will be lost
   - Explains billing changes (downgrade at next billing cycle)
6. Click "Confirm Downgrade"
7. **Verify**: Success message: "Downgrade scheduled for [next billing date]"
8. **Verify**: Current subscription remains Professional until billing date
9. **Verify**: Lago subscription marked for downgrade
10. Wait for billing cycle OR manually trigger in Lago
11. **Verify**: Subscription downgrades to Starter
12. **Verify**: API calls limit reduced to 1,000
13. **Verify**: Professional features disabled

**Expected Results**:
- ✅ Downgrade scheduled (not immediate)
- ✅ User retains Professional access until billing date
- ✅ Downgrade executes automatically at billing cycle
- ✅ Features properly restricted after downgrade
- ✅ No pro-rata refund (as per typical SaaS practice)

**Backend Verification**:
```bash
# Check subscription has downgrade scheduled
docker exec unicorn-lago-postgres psql -U lago -d lago -c \
  "SELECT external_id, plan_code, status, next_plan_code, downgrade_at FROM subscriptions WHERE external_customer_id = 'USER_EMAIL';"
# Should show next_plan_code = 'starter' and downgrade_at = [future date]
```

---

**Test Case D2: Enterprise → Professional Downgrade**

**Test Steps**: (Similar to D1)

1. Initiate downgrade from Enterprise to Professional
2. **Verify**: Warning about team seat reduction
3. **Verify**: Warning about custom integrations
4. Confirm downgrade
5. **Verify**: Downgrade scheduled
6. After billing cycle:
   - **Verify**: Team reduced to single user
   - **Verify**: Custom integrations disabled
   - **Verify**: Billing updated to $49/month

**Expected Results**:
- ✅ Team members notified of upcoming change
- ✅ Downgrade happens smoothly
- ✅ No data loss during downgrade
- ✅ Billing reflects new amount

---

## 5. Integration Tests

### 5.1 Lago Sync Tests

**Test Case I1: End-to-End Lago Integration**

**Test Steps**:
1. Create new test user in Keycloak:
   - Email: `test-lago-sync@example.com`
   - Name: "Test Lago Sync"
2. Login as test user
3. Purchase Starter plan
4. Verify in Lago admin dashboard:
   - Navigate to https://billing.unicorncommander.ai
   - Login as admin
   - Go to Customers section
   - **Verify**: New customer created with correct details:
     - External ID: `test-lago-sync@example.com`
     - Name: "Test Lago Sync"
     - Email: `test-lago-sync@example.com`
     - Metadata: Contains `keycloak_id` and `keycloak_username`
   - Go to Subscriptions section
   - **Verify**: Subscription created:
     - Customer: `test-lago-sync@example.com`
     - Plan: "Starter Plan"
     - Status: "active"
     - Started at: Current timestamp
     - Billing date: Correct next month date
5. **Verify**: Billing meters configured:
   - Go to Usage section
   - **Verify**: API calls meter shows 0/1000 usage
6. Simulate API usage:
   ```bash
   curl -X POST https://unicorncommander.ai/api/v1/test/api-call \
     -H "Authorization: Bearer USER_TOKEN"
   ```
7. **Verify**: Usage increments in Lago dashboard
8. Wait for invoice generation (or manually trigger)
9. **Verify**: Invoice created in Lago:
   - Amount: $19.00
   - Status: "pending" or "paid"
   - Line items: Starter Plan subscription

**Expected Results**:
- ✅ Customer automatically created in Lago
- ✅ Customer metadata populated correctly
- ✅ Subscription created with correct plan
- ✅ Billing cycle calculated correctly
- ✅ Usage meters active and tracking
- ✅ Invoices generated automatically

---

**Test Case I2: Lago Customer Metadata**

**Test Steps**:
1. Create subscription for user
2. Access Lago database directly:
   ```bash
   docker exec unicorn-lago-postgres psql -U lago -d lago -c \
     "SELECT external_id, name, email, metadata FROM customers WHERE email = 'USER_EMAIL';"
   ```
3. **Verify**: Metadata JSON contains:
   ```json
   {
     "keycloak_id": "uuid-value",
     "keycloak_username": "username",
     "signup_date": "ISO-8601-timestamp",
     "initial_plan": "plan-name"
   }
   ```

**Expected Results**:
- ✅ All metadata fields populated
- ✅ Keycloak ID matches user's UUID
- ✅ JSON structure valid

---

### 5.2 Keycloak Sync Tests

**Test Case I3: Keycloak Attribute Updates**

**Test Steps**:
1. Create subscription for user
2. Access Keycloak admin console:
   - URL: https://auth.unicorncommander.ai/admin/uchub/console/
   - Navigate to Users → Search for user
   - Click on user → Attributes tab
3. **Verify**: Following attributes exist and are correct:
   - `subscription_tier`: "starter" | "professional" | "enterprise" | "trial"
   - `subscription_status`: "active" | "cancelled" | "expired"
   - `subscription_started_at`: ISO-8601 timestamp
   - `subscription_expires_at`: ISO-8601 timestamp (if applicable)
   - `api_calls_limit`: "1000" (for Starter)
   - `api_calls_used`: "0" (initial value)
   - `billing_customer_id`: Lago customer UUID
4. Upgrade user's subscription
5. **Verify**: Attributes updated immediately:
   - `subscription_tier`: Changed to new tier
   - `api_calls_limit`: Increased to new tier limit
   - Audit trail: `subscription_upgraded_at` timestamp added
6. Cancel subscription
7. **Verify**: Attributes reflect cancellation:
   - `subscription_status`: "cancelled"
   - `subscription_expires_at`: Set to end of billing period
   - Tier and limits unchanged until expiry

**Expected Results**:
- ✅ All attributes created on first subscription
- ✅ Attributes update synchronously during webhook processing
- ✅ Data types correct (strings for limits, timestamps in ISO format)
- ✅ Cancellation properly reflected

**CLI Verification**:
```bash
# Get user attributes
USER_ID=$(docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users \
  --realm uchub --query "email=USER_EMAIL" --fields id | grep '"id"' | cut -d'"' -f4)

docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users/$USER_ID \
  --realm uchub --fields attributes

# Expected output:
# {
#   "attributes": {
#     "subscription_tier": ["starter"],
#     "subscription_status": ["active"],
#     "api_calls_limit": ["1000"],
#     ...
#   }
# }
```

---

**Test Case I4: Cross-Service Authorization**

**Test Steps**:
1. User with Starter subscription attempts to access feature requiring Professional tier
2. Backend checks Keycloak `subscription_tier` attribute
3. **Verify**: Access denied with clear message
4. Upgrade user to Professional
5. **Verify**: Access immediately granted
6. Attempt to use API beyond limit
7. **Verify**: Rate limit error when `api_calls_used` >= `api_calls_limit`

**Expected Results**:
- ✅ Tier-based authorization works
- ✅ API limits enforced correctly
- ✅ Immediate access after upgrade
- ✅ Clear error messages for restrictions

---

### 5.3 Stripe Integration Tests

**Test Case I5: Stripe Customer Portal**

**Test Steps**:
1. User with active subscription navigates to `/admin/subscription/manage`
2. Click "Manage Billing" button
3. **Verify**: Redirect to Stripe Customer Portal
4. **Verify**: Portal shows:
   - Current subscription details
   - Payment method on file
   - Billing history (invoices)
   - Option to update payment method
   - Option to cancel subscription
5. Update payment method to new test card
6. **Verify**: Payment method updated in Stripe
7. **Verify**: Lago reflects payment method change (if synced)

**Expected Results**:
- ✅ Customer portal accessible
- ✅ All subscription details visible
- ✅ Payment method updates work
- ✅ Invoice history accurate

---

**Test Case I6: Stripe Invoice Generation**

**Test Steps**:
1. Create monthly subscription (Starter, Professional, or Enterprise)
2. Wait for 1 month OR manually advance clock in Stripe test mode:
   - Stripe Dashboard → Developers → Events → Advance clock
3. **Verify**: Stripe generates invoice automatically
4. **Verify**: Webhook `invoice.created` sent to ops-center
5. **Verify**: Webhook `invoice.paid` sent after payment
6. **Verify**: Lago reflects invoice payment
7. **Verify**: User receives invoice email (if configured)
8. Access invoice in Stripe Dashboard
9. **Verify**: Invoice details correct:
   - Amount: Correct plan price
   - Description: Plan name
   - Status: "paid"

**Expected Results**:
- ✅ Invoices generated automatically
- ✅ Webhooks processed correctly
- ✅ Lago and Stripe in sync
- ✅ Invoice details accurate

---

## 6. Error Handling Tests

### 6.1 API Error Handling

**Test Case E1: Malformed Request Body**

**Test Steps**:
```bash
curl -X POST https://unicorncommander.ai/api/v1/billing/subscriptions/checkout \
  -H "Authorization: Bearer USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"invalid_field": "value"}'
```

**Expected Results**:
- ✅ 400 Bad Request
- ✅ Error message: "Missing required field: tier_id"
- ✅ Error logged in backend

---

**Test Case E2: Unauthorized Access**

**Test Steps**:
```bash
curl -X POST https://unicorncommander.ai/api/v1/billing/subscriptions/checkout \
  -H "Content-Type: application/json" \
  -d '{"tier_id": "starter"}'
```
(No Authorization header)

**Expected Results**:
- ✅ 401 Unauthorized
- ✅ Error message: "Authentication required"
- ✅ No checkout session created

---

**Test Case E3: Invalid JWT Token**

**Test Steps**:
```bash
curl -X POST https://unicorncommander.ai/api/v1/billing/subscriptions/checkout \
  -H "Authorization: Bearer invalid.jwt.token" \
  -H "Content-Type: application/json" \
  -d '{"tier_id": "starter"}'
```

**Expected Results**:
- ✅ 401 Unauthorized
- ✅ Error message: "Invalid or expired token"

---

### 6.2 Webhook Error Handling

**Test Case E4: Invalid Webhook Signature**

**Test Steps**:
1. Craft webhook request with incorrect signature:
   ```bash
   curl -X POST https://unicorncommander.ai/api/v1/billing/webhooks/stripe \
     -H "Content-Type: application/json" \
     -H "Stripe-Signature: t=1234567890,v1=invalid_signature" \
     -d '{
       "type": "checkout.session.completed",
       "data": {
         "object": {
           "id": "cs_test_123",
           "payment_status": "paid"
         }
       }
     }'
   ```
2. **Verify**: Response code: 400
3. **Verify**: Error message: "Invalid webhook signature"
4. **Verify**: Webhook NOT processed
5. **Verify**: Backend logs security warning

**Expected Results**:
- ✅ 400 Bad Request response
- ✅ Webhook rejected
- ✅ Security log entry created
- ✅ No subscription created

---

**Test Case E5: Unknown Webhook Event Type**

**Test Steps**:
1. Send valid webhook with unhandled event type:
   ```bash
   # Use Stripe CLI to send test webhook
   stripe trigger payment_intent.created
   ```
2. **Verify**: Webhook received by backend
3. **Verify**: Backend logs: "Unhandled webhook event type: payment_intent.created"
4. **Verify**: No error returned (200 OK to acknowledge receipt)
5. **Verify**: Event ignored gracefully

**Expected Results**:
- ✅ Webhook acknowledged (200 OK)
- ✅ Unknown events ignored without errors
- ✅ Proper logging of unhandled events

---

**Test Case E6: Malformed Webhook Payload**

**Test Steps**:
1. Send webhook with missing required fields:
   ```bash
   curl -X POST https://unicorncommander.ai/api/v1/billing/webhooks/stripe \
     -H "Content-Type: application/json" \
     -H "Stripe-Signature: $(generate_valid_signature)" \
     -d '{
       "type": "checkout.session.completed",
       "data": {}
     }'
   ```
2. **Verify**: Backend handles gracefully
3. **Verify**: Error logged: "Missing required fields in webhook payload"
4. **Verify**: Returns 400 error to trigger Stripe retry

**Expected Results**:
- ✅ Error logged with details
- ✅ 400 response triggers Stripe retry
- ✅ No partial state created
- ✅ Retry with correct payload succeeds

---

## 7. Performance Tests

### 7.1 Response Time Tests

**Test Case P1: Checkout Creation Performance**

**Test Steps**:
1. Clear browser cache
2. Open browser developer tools → Network tab
3. Navigate to `/admin/subscription/plan`
4. Click "Select Plan" for any tier
5. Measure time from click to Stripe redirect
6. **Verify**: Total time < 2 seconds
7. Check network waterfall:
   - API request time
   - Server processing time
   - Stripe redirect time
8. Repeat test 10 times and calculate average

**Expected Results**:
- ✅ 95th percentile: < 2 seconds
- ✅ Average: < 1 second
- ✅ API endpoint response: < 500ms
- ✅ No timeout errors

**Performance Targets**:
- API request: < 200ms
- Stripe session creation: < 500ms
- Redirect: < 100ms
- **Total**: < 2 seconds

---

**Test Case P2: Webhook Processing Performance**

**Test Steps**:
1. Complete payment
2. Measure webhook processing time:
   - Start: Webhook received timestamp (from Stripe dashboard)
   - End: Subscription created timestamp (from Lago database)
3. **Verify**: Processing time < 5 seconds
4. Repeat with 10 concurrent payments
5. **Verify**: All webhooks process within 10 seconds

**Expected Results**:
- ✅ Single webhook: < 5 seconds
- ✅ Concurrent webhooks: < 10 seconds each
- ✅ No webhook failures under load
- ✅ Correct subscription creation for all

**Measurement**:
```bash
# Check webhook processing time in logs
docker logs ops-center-direct | grep "checkout.session.completed" | grep "processed in"
# Should show: "Webhook processed in X.XXX seconds"
```

---

**Test Case P3: Dashboard Load Performance**

**Test Steps**:
1. Login to Ops-Center
2. Navigate to `/admin/subscription/plan`
3. Measure page load time (Network tab → Load event)
4. **Verify**: Initial load < 3 seconds
5. **Verify**: Plan cards render within 1 second
6. Check for:
   - Lazy loading of images
   - Efficient API calls
   - No unnecessary re-renders

**Expected Results**:
- ✅ First Contentful Paint: < 1 second
- ✅ Time to Interactive: < 3 seconds
- ✅ Lighthouse performance score: > 80

---

### 7.2 Load Tests

**Test Case P4: Concurrent Checkouts**

**Test Steps**:
1. Create 10 test users
2. Simultaneously initiate checkout for all users:
   ```bash
   # Use load testing tool like Apache Bench or k6
   k6 run --vus 10 --duration 30s load-test.js
   ```
3. **Verify**: All checkouts succeed
4. **Verify**: No timeout errors
5. **Verify**: No rate limiting errors
6. **Verify**: Backend handles load gracefully

**Expected Results**:
- ✅ 100% success rate for checkout creation
- ✅ Average response time < 2 seconds
- ✅ No 5xx errors
- ✅ No database deadlocks

---

**Test Case P5: Webhook Burst**

**Test Steps**:
1. Simulate 50 webhook events arriving simultaneously:
   ```bash
   # Use Stripe CLI or custom script
   for i in {1..50}; do
     stripe trigger checkout.session.completed &
   done
   ```
2. **Verify**: All webhooks processed successfully
3. **Verify**: No duplicate subscriptions created
4. **Verify**: Processing time < 30 seconds total
5. **Verify**: No database connection exhaustion

**Expected Results**:
- ✅ 100% webhook success rate
- ✅ Idempotency maintained (no duplicates)
- ✅ Database connections handled efficiently
- ✅ Queue system works correctly

---

## 8. Security Tests

### 8.1 Authentication & Authorization

**Test Case S1: Unauthenticated Access Blocked**

**Test Steps**:
1. Logout of Ops-Center
2. Try to access `/admin/subscription/plan` directly
3. **Verify**: Redirected to Keycloak login
4. Try API endpoint without auth:
   ```bash
   curl https://unicorncommander.ai/api/v1/billing/subscriptions/checkout \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"tier_id": "starter"}'
   ```
5. **Verify**: 401 Unauthorized

**Expected Results**:
- ✅ All protected routes require authentication
- ✅ API endpoints enforce auth
- ✅ No sensitive data leaked in errors

---

**Test Case S2: Cross-User Access Prevention**

**Test Steps**:
1. User A creates subscription
2. User B attempts to access User A's subscription details:
   ```bash
   curl https://unicorncommander.ai/api/v1/billing/subscriptions/USER_A_ID \
     -H "Authorization: Bearer USER_B_TOKEN"
   ```
3. **Verify**: 403 Forbidden
4. **Verify**: No subscription data returned

**Expected Results**:
- ✅ Users can only access own data
- ✅ Authorization checks enforce ownership
- ✅ Admin users can access all data (if applicable)

---

**Test Case S3: JWT Token Security**

**Test Steps**:
1. Login and capture JWT token
2. Decode token (using jwt.io or similar)
3. **Verify**: Token contains:
   - `sub`: User ID
   - `email`: User email
   - `exp`: Expiration timestamp
   - `iss`: Keycloak issuer
4. **Verify**: Token does NOT contain:
   - Passwords
   - API keys
   - Sensitive metadata
5. Wait for token to expire (typically 5-15 minutes)
6. Attempt to use expired token
7. **Verify**: 401 Unauthorized

**Expected Results**:
- ✅ Tokens expire appropriately
- ✅ Expired tokens rejected
- ✅ No sensitive data in tokens
- ✅ Token refresh mechanism works

---

### 8.2 Data Security

**Test Case S4: Webhook Signature Verification**

**Test Steps**: (Already covered in E4, but emphasizing security)

1. **Verify**: All webhook requests validate signature
2. **Verify**: Invalid signatures rejected immediately
3. **Verify**: Signature validation uses constant-time comparison
4. **Verify**: Security events logged

**Expected Results**:
- ✅ No webhooks processed without valid signature
- ✅ Timing attack prevention (constant-time comparison)
- ✅ Security audit trail

---

**Test Case S5: HTTPS Enforcement**

**Test Steps**:
1. Attempt HTTP request to API:
   ```bash
   curl http://unicorncommander.ai/api/v1/billing/subscriptions/checkout \
     -X POST \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"tier_id": "starter"}'
   ```
2. **Verify**: Redirect to HTTPS or connection refused
3. **Verify**: Stripe checkout uses HTTPS
4. **Verify**: Webhook endpoint requires HTTPS

**Expected Results**:
- ✅ All endpoints use HTTPS
- ✅ HTTP requests redirected or blocked
- ✅ SSL/TLS certificates valid

---

**Test Case S6: Sensitive Data Handling**

**Test Steps**:
1. Complete payment flow
2. Check backend logs
3. **Verify**: No credit card numbers logged
4. **Verify**: No Stripe secret key logged
5. **Verify**: No user passwords logged
6. **Verify**: PII (email, name) only logged when necessary
7. Check database
8. **Verify**: No plain-text sensitive data stored

**Expected Results**:
- ✅ PCI compliance maintained
- ✅ Stripe handles all card data (no card data touches our servers)
- ✅ Sensitive config in environment variables
- ✅ Logs safe for debugging without exposing secrets

---

### 8.3 Input Validation

**Test Case S7: SQL Injection Prevention**

**Test Steps**:
1. Attempt SQL injection in tier_id:
   ```bash
   curl -X POST https://unicorncommander.ai/api/v1/billing/subscriptions/checkout \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"tier_id": "starter OR 1=1--"}'
   ```
2. **Verify**: Request rejected or sanitized
3. **Verify**: No database error
4. **Verify**: No unauthorized access

**Expected Results**:
- ✅ Input properly sanitized
- ✅ Prepared statements used (no raw SQL)
- ✅ No SQL errors in logs

---

**Test Case S8: XSS Prevention**

**Test Steps**:
1. Attempt XSS in user input:
   ```bash
   # Try to inject script via user name during signup
   curl -X POST https://unicorncommander.ai/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "name": "<script>alert(\"XSS\")</script>",
       "password": "password123"
     }'
   ```
2. View user profile page
3. **Verify**: Script not executed
4. **Verify**: HTML escaped properly

**Expected Results**:
- ✅ All user input escaped
- ✅ No script execution
- ✅ Content Security Policy headers set

---

## 9. Monitoring & Logging

### 9.1 Audit Logging

**Test Case M1: Subscription Events Logged**

**Test Steps**:
1. Complete subscription creation
2. Query audit log:
   ```bash
   docker exec ops-center-direct sqlite3 /app/data/audit.db \
     "SELECT * FROM audit_log WHERE user_email = 'USER_EMAIL' ORDER BY timestamp DESC LIMIT 10;"
   ```
3. **Verify**: Following events logged:
   - `subscription_checkout_initiated`
   - `subscription_payment_completed`
   - `subscription_created`
   - `keycloak_attributes_updated`

**Expected Results**:
- ✅ All critical events logged
- ✅ Log entries include:
   - Timestamp
   - User ID/email
   - Action type
   - Details (tier, amount, etc.)
   - IP address
   - User agent

---

**Test Case M2: Error Logging**

**Test Steps**:
1. Trigger various errors (declined card, API errors, etc.)
2. Check backend logs:
   ```bash
   docker logs ops-center-direct | grep -i error | tail -50
   ```
3. **Verify**: Errors logged with:
   - Error type
   - Error message
   - Stack trace
   - Context (user, request details)
   - Timestamp

**Expected Results**:
- ✅ All errors logged
- ✅ Stack traces captured
- ✅ Sufficient context for debugging
- ✅ No sensitive data in logs

---

### 9.2 Metrics & Alerting

**Test Case M3: Stripe Dashboard Metrics**

**Test Steps**:
1. Access Stripe Dashboard: https://dashboard.stripe.com/test
2. Navigate to Payments section
3. **Verify**: All successful payments visible
4. Navigate to Subscriptions section
5. **Verify**: All active subscriptions listed
6. Check webhook events
7. **Verify**: All events logged with success/failure status

**Expected Results**:
- ✅ Stripe dashboard reflects all transactions
- ✅ Webhook success rate > 99%
- ✅ No failed payments without corresponding error logs

---

**Test Case M4: Lago Dashboard Metrics**

**Test Steps**:
1. Access Lago Dashboard: https://billing.unicorncommander.ai
2. Login as admin
3. Navigate to Analytics section
4. **Verify**: Metrics visible:
   - Total customers
   - Active subscriptions
   - MRR (Monthly Recurring Revenue)
   - Churn rate
5. **Verify**: Matches actual data

**Expected Results**:
- ✅ Accurate metrics
- ✅ Real-time updates
- ✅ Export functionality works

---

## 10. Documentation & Reporting

### 10.1 Test Execution Tracking

Use this checklist during test execution:

```markdown
## Test Execution Log

### Trial Plan Tests
- [ ] T1: Successful Trial Signup - PASS/FAIL
  - Notes: _______________________________________
- [ ] T2: Trial Signup - Payment Declined - PASS/FAIL
  - Notes: _______________________________________
- [ ] T3: Trial Signup - 3D Secure - PASS/FAIL
  - Notes: _______________________________________

### Starter Plan Tests
- [ ] S1: Successful Starter Signup - PASS/FAIL
  - Notes: _______________________________________

### Professional Plan Tests
- [ ] P1: Successful Professional Signup - PASS/FAIL
  - Notes: _______________________________________

### Enterprise Plan Tests
- [ ] E1: Successful Enterprise Signup - PASS/FAIL
  - Notes: _______________________________________

### Edge Cases
- [ ] EC1: Cancel Before Payment - PASS/FAIL
- [ ] EC2: Insufficient Funds - PASS/FAIL
- [ ] EC3: Expired Card - PASS/FAIL
- [ ] EC4: Incorrect CVC - PASS/FAIL
- [ ] EC5: Webhook Disabled - PASS/FAIL
- [ ] EC6: Duplicate Webhook - PASS/FAIL
- [ ] EC7: Invalid Plan ID - PASS/FAIL
- [ ] EC8: Missing Stripe Price ID - PASS/FAIL
- [ ] EC9: Stripe API Error - PASS/FAIL
- [ ] EC10: Lago API Error - PASS/FAIL

### Upgrade/Downgrade Tests
- [ ] U1: Starter → Professional - PASS/FAIL
- [ ] U2: Trial → Enterprise - PASS/FAIL
- [ ] D1: Professional → Starter - PASS/FAIL
- [ ] D2: Enterprise → Professional - PASS/FAIL

### Integration Tests
- [ ] I1: Lago Integration - PASS/FAIL
- [ ] I2: Lago Metadata - PASS/FAIL
- [ ] I3: Keycloak Attributes - PASS/FAIL
- [ ] I4: Cross-Service Auth - PASS/FAIL
- [ ] I5: Stripe Customer Portal - PASS/FAIL
- [ ] I6: Stripe Invoices - PASS/FAIL

### Error Handling
- [ ] E1: Malformed Request - PASS/FAIL
- [ ] E2: Unauthorized Access - PASS/FAIL
- [ ] E3: Invalid JWT - PASS/FAIL
- [ ] E4: Invalid Webhook Signature - PASS/FAIL
- [ ] E5: Unknown Webhook Event - PASS/FAIL
- [ ] E6: Malformed Webhook - PASS/FAIL

### Performance Tests
- [ ] P1: Checkout Performance - PASS/FAIL
  - Average time: ______ seconds
- [ ] P2: Webhook Performance - PASS/FAIL
  - Average time: ______ seconds
- [ ] P3: Dashboard Load - PASS/FAIL
  - Load time: ______ seconds
- [ ] P4: Concurrent Checkouts - PASS/FAIL
- [ ] P5: Webhook Burst - PASS/FAIL

### Security Tests
- [ ] S1: Unauthenticated Access - PASS/FAIL
- [ ] S2: Cross-User Access - PASS/FAIL
- [ ] S3: JWT Token Security - PASS/FAIL
- [ ] S4: Webhook Signature - PASS/FAIL
- [ ] S5: HTTPS Enforcement - PASS/FAIL
- [ ] S6: Sensitive Data Handling - PASS/FAIL
- [ ] S7: SQL Injection Prevention - PASS/FAIL
- [ ] S8: XSS Prevention - PASS/FAIL

### Monitoring & Logging
- [ ] M1: Audit Logging - PASS/FAIL
- [ ] M2: Error Logging - PASS/FAIL
- [ ] M3: Stripe Metrics - PASS/FAIL
- [ ] M4: Lago Metrics - PASS/FAIL
```

---

### 10.2 Screenshot Requirements

Capture screenshots for:

1. **Happy Path Screenshots**:
   - [ ] Plans page with all 4 tiers displayed
   - [ ] Stripe checkout page for each plan
   - [ ] Success page after payment
   - [ ] Lago dashboard showing subscriptions
   - [ ] Keycloak user attributes
   - [ ] Stripe dashboard with successful payment

2. **Error Screenshots**:
   - [ ] Declined card error message
   - [ ] Invalid plan error page
   - [ ] Webhook failure in Stripe dashboard
   - [ ] Backend error logs (with sensitive data redacted)

3. **Integration Screenshots**:
   - [ ] Lago customer details
   - [ ] Stripe subscription details
   - [ ] Keycloak attributes panel
   - [ ] Audit log entries

4. **Performance Screenshots**:
   - [ ] Browser Network waterfall
   - [ ] Lighthouse performance report
   - [ ] Backend logs showing response times

---

### 10.3 Final Test Report Template

```markdown
# Subscription Payment Flow - Test Results Report

**Test Date**: [Date]
**Tester**: [Name]
**Environment**: Production/Staging/Test
**Version**: [Git commit hash]

## Executive Summary

- **Total Test Cases**: X
- **Passed**: X (XX%)
- **Failed**: X (XX%)
- **Blocked**: X (XX%)
- **Not Tested**: X (XX%)

## Critical Issues Found

### Issue #1: [Title]
- **Severity**: Critical/Major/Minor
- **Test Case**: [Test case ID]
- **Description**: [What went wrong]
- **Steps to Reproduce**:
  1. ...
  2. ...
- **Expected**: [What should happen]
- **Actual**: [What actually happened]
- **Screenshot**: [Link or attachment]
- **Workaround**: [If any]
- **Fix Required**: [Description]

## Test Results by Category

### ✅ Subscription Creation (4/4 plans tested)
- [x] Trial Plan - PASS
- [x] Starter Plan - PASS
- [x] Professional Plan - PASS
- [x] Enterprise Plan - PASS

### ✅ Edge Cases (10/10 tested)
- [x] All edge case tests passed
- Notes: [Any observations]

### ✅ Integration Tests (6/6 tested)
- [x] Lago integration working
- [x] Keycloak sync operational
- [x] Stripe integration complete

### ⚠️ Performance Tests (5/5 tested)
- [x] Checkout performance: Average 1.2s (Target: < 2s) ✅
- [x] Webhook processing: Average 3.8s (Target: < 5s) ✅
- [ ] Dashboard load: Average 3.5s (Target: < 3s) ⚠️
  - Recommendation: Optimize image loading

### ✅ Security Tests (8/8 tested)
- [x] All security tests passed
- No vulnerabilities found

## Performance Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Checkout Creation | < 2s | 1.2s | ✅ PASS |
| Webhook Processing | < 5s | 3.8s | ✅ PASS |
| Dashboard Load | < 3s | 3.5s | ⚠️ WARN |
| API Response Time | < 500ms | 320ms | ✅ PASS |

## Lago Dashboard Verification

- [x] All subscriptions visible
- [x] Customer data accurate
- [x] Invoices generated correctly
- [x] Metrics calculations correct

## Keycloak Integration

- [x] User attributes populated
- [x] Tier changes reflected
- [x] API limits enforced
- [x] Authorization working

## Stripe Integration

- [x] Payments processing
- [x] Webhooks delivering
- [x] Customer portal working
- [x] Invoices accurate

## Recommendations

1. **High Priority**:
   - [List any critical fixes needed]

2. **Medium Priority**:
   - Dashboard load time optimization
   - [Other medium priority items]

3. **Low Priority/Future**:
   - [Nice-to-have improvements]

## Sign-Off

- [ ] All critical tests passed
- [ ] No blocking issues
- [ ] Documentation updated
- [ ] Ready for production deployment

**Approved By**: _______________________
**Date**: _______________________
```

---

## 11. Quick Reference Commands

### Pre-Test Setup

```bash
# 1. Ensure services running
cd /opt/ops-center
docker compose -f docker-compose.direct.yml ps

# 2. Tail logs for testing
docker logs ops-center-direct -f

# 3. Access Lago admin
# URL: https://billing.unicorncommander.ai
# User: admin@example.com
# Pass: your-admin-password

# 4. Access Keycloak admin
# URL: https://auth.unicorncommander.ai/admin/uchub/console/
# User: admin
# Pass: your-admin-password

# 5. Access Stripe dashboard
# URL: https://dashboard.stripe.com/test
# Use your Stripe account credentials
```

### During Testing

```bash
# Check subscription created in Lago
docker exec unicorn-lago-postgres psql -U lago -d lago -c \
  "SELECT external_id, plan_code, status FROM subscriptions ORDER BY created_at DESC LIMIT 5;"

# Check Keycloak user attributes
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users \
  --realm uchub --query "email=USER_EMAIL" --fields attributes

# Check audit log
docker exec ops-center-direct sqlite3 /app/data/audit.db \
  "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10;"

# Check backend logs for errors
docker logs ops-center-direct | grep -i error | tail -20

# Check webhook events
docker logs ops-center-direct | grep -i webhook | tail -20

# Restart backend if needed
docker compose -f docker-compose.direct.yml restart ops-center-direct
```

### Test Stripe Webhooks

```bash
# Install Stripe CLI (if not installed)
# https://stripe.com/docs/stripe-cli

# Login to Stripe CLI
stripe login

# Forward webhooks to local (for testing)
stripe listen --forward-to https://unicorncommander.ai/api/v1/billing/webhooks/stripe

# Trigger test webhook
stripe trigger checkout.session.completed

# View webhook logs
stripe events list --limit 10
```

---

## 12. Success Criteria

The subscription payment flow is considered **PRODUCTION READY** when:

### Core Functionality
- ✅ All 4 subscription plans can be purchased successfully
- ✅ Stripe checkout loads and processes payments correctly
- ✅ Success/cancel pages display appropriately
- ✅ Webhooks process reliably (>99% success rate)
- ✅ Idempotency prevents duplicate subscriptions

### Integration
- ✅ Lago subscriptions created accurately
- ✅ Keycloak attributes sync correctly
- ✅ Stripe customer portal accessible
- ✅ Cross-service authorization works

### Error Handling
- ✅ Payment failures handled gracefully
- ✅ Invalid requests return clear errors
- ✅ Webhook failures don't lose payments
- ✅ Security errors logged appropriately

### Performance
- ✅ Checkout creation: < 2 seconds (95th percentile)
- ✅ Webhook processing: < 5 seconds
- ✅ Dashboard load: < 3 seconds
- ✅ Concurrent requests handled without errors

### Security
- ✅ Authentication required for all protected endpoints
- ✅ Webhook signatures validated
- ✅ HTTPS enforced everywhere
- ✅ No sensitive data in logs
- ✅ PCI compliance maintained

### Documentation
- ✅ All test cases documented
- ✅ Screenshots captured
- ✅ Issues tracked
- ✅ Final report completed

---

## 13. Post-Testing Activities

### After Test Completion

1. **Review Test Results**:
   - [ ] Calculate pass/fail percentages
   - [ ] Identify patterns in failures
   - [ ] Prioritize issues by severity

2. **Update Documentation**:
   - [ ] Update SUBSCRIPTION_PAYMENT_FIXES.md with results
   - [ ] Document any new issues found
   - [ ] Add workarounds or known issues section

3. **Create GitHub Issues**:
   - [ ] For each failed test, create GitHub issue with:
     - Test case ID
     - Steps to reproduce
     - Expected vs actual results
     - Screenshots
     - Priority level

4. **Communicate Results**:
   - [ ] Share test report with team
   - [ ] Schedule follow-up meeting if issues found
   - [ ] Update project status in Ops-Center

5. **Plan Next Steps**:
   - [ ] If all tests pass: Schedule production deployment
   - [ ] If issues found: Assign fixes and re-test
   - [ ] Document lessons learned

---

## 14. Contacts & Resources

### Key People
- **Product Owner**: [Name]
- **Backend Developer**: [Name]
- **DevOps**: [Name]
- **QA Lead**: [Name]

### Important Links
- **Ops-Center**: https://unicorncommander.ai
- **Lago Dashboard**: https://billing.unicorncommander.ai
- **Keycloak Admin**: https://auth.unicorncommander.ai/admin/uchub/console/
- **Stripe Dashboard**: https://dashboard.stripe.com/test
- **GitHub Repository**: https://github.com/Unicorn-Commander/UC-Cloud
- **Documentation**: `/opt/ops-center/docs/`

### Support
- **Stripe Support**: https://support.stripe.com
- **Lago Documentation**: https://doc.getlago.com
- **Keycloak Docs**: https://www.keycloak.org/documentation

---

## Appendix A: Environment Variables Checklist

```bash
# Required in .env.auth for testing

# Stripe (Test Mode)
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Lago
LAGO_API_KEY=your-lago-api-key
LAGO_API_URL=http://unicorn-lago-api:3000
LAGO_PUBLIC_URL=https://billing-api.unicorncommander.ai

# Keycloak
KEYCLOAK_URL=http://uchub-keycloak:8080
KEYCLOAK_REALM=uchub
KEYCLOAK_CLIENT_ID=ops-center
KEYCLOAK_CLIENT_SECRET=your-keycloak-client-secret

# Application
EXTERNAL_HOST=unicorncommander.ai
EXTERNAL_PROTOCOL=https
```

---

## Appendix B: Test Data

### Test User Accounts

Create these test users in Keycloak before testing:

1. **Basic Test User**:
   - Email: `test-basic@example.com`
   - Name: "Test Basic User"
   - Use for: Basic subscription tests

2. **Upgrade Test User**:
   - Email: `test-upgrade@example.com`
   - Name: "Test Upgrade User"
   - Use for: Upgrade/downgrade tests
   - Start with: Starter subscription

3. **Error Test User**:
   - Email: `test-error@example.com`
   - Name: "Test Error User"
   - Use for: Error handling tests

### Stripe Test Cards Summary

| Card Number | Purpose |
|-------------|---------|
| `4242 4242 4242 4242` | ✅ Success |
| `4000 0000 0000 0002` | ❌ Declined |
| `4000 0000 0000 9995` | ❌ Insufficient Funds |
| `4000 0000 0000 0069` | ❌ Expired |
| `4000 0000 0000 0127` | ❌ Incorrect CVC |
| `4000 0025 0000 3155` | 🔐 Requires 3D Secure |

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-23 | Initial test plan created | UC-Cloud Team |

---

**End of Test Plan**
