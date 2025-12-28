# UC-1 Pro User Signup & Billing Guide

## 🎯 Complete User Journey

This document explains how new users sign up, select plans, and make payments in UC-1 Pro.

---

## 📋 User Flow Overview

```
1. User lands on website
   ↓
2. Views subscription plans (/plans.html)
   ↓
3. Selects a plan
   ↓
4. Redirected to signup flow (/signup-flow.html)
   ↓
5. Creates account via Keycloak (if not authenticated)
   ↓
6. Redirected to Stripe Checkout
   ↓
7. Enters payment information
   ↓
8. Payment processed
   ↓
9. Webhook updates subscription in Keycloak
   ↓
10. User redirected to dashboard with active subscription
```

---

## 🚪 Entry Points

### Option 1: Public Plans Page (Recommended)
**URL**: `https://your-domain.com/plans.html`

- **Purpose**: Public page showing all 4 subscription tiers
- **Authentication**: NOT required (anyone can view)
- **Features**:
  - Displays all plans with pricing and features
  - "Most Popular" badge on Professional tier
  - Click any plan → redirects to signup flow

**User Experience**:
```
User visits /plans.html
  → Sees 4 beautiful cards (Trial, Starter, Professional, Enterprise)
  → Clicks "Select Professional"
  → Redirected to /signup-flow.html?plan=professional
```

### Option 2: Direct Signup Flow
**URL**: `https://your-domain.com/signup-flow.html`

- **Purpose**: Direct entry with tier selection
- **Authentication**: NOT required initially
- **Features**:
  - Step 1: Select Plan (shows all 4 tiers)
  - Step 2: Payment (Stripe Checkout)
  - Step 3: Complete (success confirmation)

---

## 💳 Subscription Tiers

### Trial - $1/month (7 days)
- 1,000 API calls
- Basic AI models
- Open-WebUI chat access
- Community support
- **No credit card required for viewing**
- **Card required to activate trial**

### Starter - $19/month
- 10,000 API calls/month
- All AI models
- Center-Deep search
- BYOK enabled
- Email support

### Professional - $49/month ⭐ Most Popular
- 100,000 API calls/month
- All features from Starter
- TTS & STT access
- Billing dashboard
- Priority support

### Enterprise - $99/month
- Unlimited API calls
- All Professional features
- Team management (5 seats)
- Custom integrations
- 24/7 dedicated support

---

## 🔐 Authentication Flow

### For New Users:

1. **User clicks "Select Plan" on /plans.html**
   - Not authenticated yet

2. **Redirected to /signup-flow.html?plan=professional**
   - Shows tier selection (pre-selected if ?plan= parameter present)

3. **User clicks "Continue to Payment"**
   - Backend checks authentication via `/api/v1/auth/me`
   - If NOT authenticated → redirects to Keycloak login/registration
   - If authenticated → continues to Stripe Checkout

4. **Keycloak Registration**
   ```
   https://auth.your-domain.com/realms/uchub/protocol/openid-connect/auth?
     client_id=ops-center&
     redirect_uri=https://your-domain.com/signup-flow.html&
     response_type=code&
     scope=openid profile email
   ```

5. **After Keycloak auth, back to signup flow**
   - Now authenticated with session cookie
   - API call to create Stripe checkout session
   - Redirected to Stripe

6. **Stripe Checkout**
   - User enters card information
   - Secure payment processing
   - No card data touches UC-1 Pro servers

7. **Payment Success**
   - Stripe sends webhook to `/api/v1/billing/webhooks/stripe`
   - Subscription data synced to Keycloak user attributes:
     - `subscription_tier` = "professional"
     - `subscription_status` = "active"
     - `stripe_customer_id` = "cus_..."
     - `stripe_subscription_id` = "sub_..."
   - User redirected to success page

8. **User lands on dashboard**
   - Tier badge shows "Professional"
   - Access to all Professional tier features

---

## 🧪 Testing with Test Users

### Using Stripe Test Mode:

1. **Visit**: `https://your-domain.com/plans.html`

2. **Select any tier** (Professional recommended)

3. **Create test account** in Keycloak:
   - Email: `testuser@example.com`
   - Password: `TestPassword123!`

4. **Enter test card** in Stripe Checkout:
   - Card Number: `4242 4242 4242 4242`
   - Expiry: Any future date (e.g., `12/34`)
   - CVC: Any 3 digits (e.g., `123`)
   - Zip: Any 5 digits (e.g., `12345`)

5. **Complete payment**
   - Webhook processes subscription
   - User tier updated in Keycloak
   - Redirected to dashboard

6. **Verify subscription**:
   - Visit `/billing-settings.html`
   - Should show active subscription
   - Tier badge should reflect selected plan

---

## 📊 Backend Flow

### API Endpoints Used During Signup:

1. **GET /api/v1/subscriptions/plans**
   - Public endpoint (no auth required)
   - Returns all 4 subscription tiers

2. **GET /api/v1/auth/me**
   - Checks if user is authenticated
   - Returns user info if logged in

3. **POST /api/v1/billing/checkout/create**
   - Requires authentication
   - Creates Stripe checkout session
   - Parameters:
     ```json
     {
       "tier": "professional",
       "success_url": "https://your-domain.com/billing/success",
       "cancel_url": "https://your-domain.com/billing/canceled"
     }
     ```

4. **POST /api/v1/billing/webhooks/stripe** (webhook)
   - Called by Stripe after payment
   - Updates Keycloak user attributes
   - Creates Lago billing customer

---

## 🔄 Subscription Changes

### Upgrading:

1. **User visits /billing-settings.html**
2. **Clicks "Upgrade Plan"**
3. **Selects higher tier** from modal
4. **Redirected to Stripe Checkout**
5. **Payment processed** (prorated)
6. **Webhook updates** tier immediately

### Downgrading:

1. **User visits /billing-settings.html**
2. **Clicks "Change Plan" or "Cancel"**
3. **Selects lower tier**
4. **Changes take effect** at end of billing period

### Cancellation:

1. **User clicks "Cancel Subscription"**
2. **Confirmation modal** appears
3. **Confirms cancellation**
4. **Access continues** until end of billing period
5. **Auto-downgrade to Trial** after period ends

---

## 🛠️ For Developers

### Adding the Plans Link to Your Site:

```html
<!-- In navigation or homepage -->
<a href="/plans.html">View Plans</a>

<!-- Direct signup link -->
<a href="/signup-flow.html">Sign Up</a>

<!-- Preselect a tier -->
<a href="/signup-flow.html?plan=professional">Start Professional Trial</a>
```

### Checking User's Subscription in Frontend:

```javascript
// Fetch current user subscription
const response = await fetch('/api/v1/subscriptions/my-access', {
    credentials: 'include'
});

const data = await response.json();
console.log('Current tier:', data.plan.name);
console.log('API calls limit:', data.plan.api_calls_limit);
console.log('BYOK enabled:', data.plan.byok_enabled);
```

### Testing Subscription Sync:

```bash
# Check Keycloak user attributes
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users \
  -r uchub --fields id,username,attributes

# Check Stripe subscription
curl -u sk_test_...: https://api.stripe.com/v1/subscriptions/sub_...

# Check webhook logs
docker logs ops-center-direct | grep "Stripe webhook"
```

---

## ❓ FAQ

### Q: Can users view plans without signing up?
**A**: YES! The `/plans.html` page is public and shows all tiers.

### Q: Do users need a credit card to browse plans?
**A**: NO! Only required when they click "Select Plan" and proceed to checkout.

### Q: Can users change their mind after selecting a plan?
**A**: YES! They can cancel the Stripe checkout and return to plans page.

### Q: What happens if payment fails?
**A**: User stays on Trial tier. They can retry payment from `/billing-settings.html`.

### Q: Can users upgrade immediately?
**A**: YES! Upgrades are prorated and take effect immediately.

### Q: Is the trial automatically converted to paid?
**A**: YES, if they complete checkout for Trial. NO auto-upgrade after trial expires.

---

## 🎉 Summary

**TL;DR for Users**:
1. Visit `/plans.html` to see all options
2. Click "Select Plan"
3. Create account (if new)
4. Enter payment info in Stripe
5. Start using UC-1 Pro with your chosen tier!

**TL;DR for Developers**:
- `/plans.html` - Public plan viewer
- `/signup-flow.html` - Registration + payment flow
- `/billing-settings.html` - Manage existing subscription
- All connected via Stripe Checkout + Keycloak SSO

**Everything is ready to accept real users and payments!** 🚀
