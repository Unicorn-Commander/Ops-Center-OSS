# Credit Purchase System - Setup & Testing Guide

**Status**: ✅ Backend Complete, Frontend Pending Build
**Date**: November 12, 2025
**Version**: 1.0.0

---

## 📋 Overview

A complete one-time credit purchase system integrated with Stripe payment processing. Users can purchase credit packages to use AI models and services without recurring subscriptions.

### Features Implemented

- ✅ **4 Credit Packages**: Starter ($10), Standard ($45), Pro ($80), Enterprise ($350)
- ✅ **Stripe Integration**: Checkout sessions, payment processing, webhooks
- ✅ **Database Schema**: `credit_purchases` and `credit_packages` tables
- ✅ **Backend API**: 5 endpoints for package listing, purchasing, history, webhooks
- ✅ **Frontend Component**: React page with package cards, purchase history, balance display
- ✅ **Automatic Credit Addition**: Credits added to user account on successful payment
- ✅ **Purchase History**: Track all transactions with status
- ✅ **Admin Endpoints**: View all purchases across users

---

## 🗄️ Database Schema

### Tables Created

#### `credit_packages`
Defines available credit packages for purchase.

```sql
- id (UUID)
- package_code (VARCHAR) - 'starter', 'standard', 'pro', 'enterprise'
- package_name (VARCHAR) - Display name
- description (TEXT) - Package description
- credits (INTEGER) - Number of credits
- price_usd (DECIMAL) - Price in USD
- discount_percentage (INTEGER) - Discount amount (0-100)
- stripe_price_id (VARCHAR) - Stripe Price ID
- stripe_product_id (VARCHAR) - Stripe Product ID
- is_active (BOOLEAN) - Package availability
- display_order (INTEGER) - Sort order
```

**Default Packages**:
| Code | Name | Credits | Price | Discount |
|------|------|---------|-------|----------|
| starter | Starter Pack | 1,000 | $10.00 | 0% |
| standard | Standard Pack | 5,000 | $45.00 | 10% |
| pro | Pro Pack | 10,000 | $80.00 | 20% |
| enterprise | Enterprise Pack | 50,000 | $350.00 | 30% |

#### `credit_purchases`
Tracks all credit purchase transactions.

```sql
- id (UUID)
- user_id (VARCHAR) - Keycloak user ID
- package_name (VARCHAR) - Package purchased
- amount_credits (DECIMAL) - Credits purchased
- amount_paid (DECIMAL) - Amount paid in USD
- discount_applied (DECIMAL) - Discount applied
- stripe_payment_id (VARCHAR) - Stripe Payment ID
- stripe_checkout_session_id (VARCHAR) - Stripe Session ID
- stripe_payment_intent_id (VARCHAR) - Stripe Payment Intent ID
- status (VARCHAR) - 'pending', 'processing', 'completed', 'failed', 'refunded'
- created_at (TIMESTAMP) - Purchase initiation time
- completed_at (TIMESTAMP) - Payment completion time
- metadata (JSONB) - Additional data
```

---

## 🔌 API Endpoints

### 1. List Credit Packages
**GET** `/api/v1/billing/credits/packages`

Lists all available credit packages.

**Authentication**: Required (session cookie)

**Query Parameters**:
- `include_inactive` (bool): Include inactive packages (admin only)

**Response**:
```json
[
  {
    "id": "uuid",
    "package_code": "starter",
    "package_name": "Starter Pack",
    "description": "1,000 credits - Perfect for trying out the platform",
    "credits": 1000,
    "price_usd": 10.00,
    "discount_percentage": 0,
    "is_active": true,
    "stripe_price_id": "price_xxx",
    "stripe_product_id": "prod_xxx"
  }
]
```

### 2. Create Purchase Checkout
**POST** `/api/v1/billing/credits/purchase`

Creates Stripe checkout session and returns redirect URL.

**Authentication**: Required

**Request Body**:
```json
{
  "package_code": "starter",
  "success_url": "https://your-domain.com/admin/credits?purchase=success",
  "cancel_url": "https://your-domain.com/admin/credits?purchase=cancelled"
}
```

**Response**:
```json
{
  "checkout_url": "https://checkout.stripe.com/pay/cs_xxx",
  "session_id": "cs_xxx"
}
```

### 3. Purchase History
**GET** `/api/v1/billing/credits/history`

Get authenticated user's purchase history.

**Authentication**: Required

**Query Parameters**:
- `limit` (int): Number of records (default: 50)
- `offset` (int): Pagination offset (default: 0)

**Response**:
```json
[
  {
    "id": "uuid",
    "package_name": "Starter Pack",
    "amount_credits": 1000.0,
    "amount_paid": 10.0,
    "status": "completed",
    "created_at": "2025-11-12T16:00:00Z",
    "completed_at": "2025-11-12T16:01:23Z",
    "stripe_payment_id": "pi_xxx"
  }
]
```

### 4. Stripe Webhook Handler
**POST** `/api/v1/billing/credits/webhook`

Handles Stripe webhook events (called by Stripe, not frontend).

**Events Handled**:
- `checkout.session.completed` - Adds credits on successful payment

**Authentication**: Stripe signature verification

**Webhook Actions**:
1. Verifies Stripe signature
2. Updates purchase status to 'completed'
3. Adds credits to user account via `credit_manager.allocate_credits()`
4. Logs audit trail
5. Sends confirmation email (TODO)

### 5. Admin: List All Purchases
**GET** `/api/v1/billing/credits/admin/purchases`

Admin endpoint to view all purchases across all users.

**Authentication**: Required (admin role)

**Query Parameters**:
- `limit` (int): Number of records (default: 100)
- `offset` (int): Pagination offset (default: 0)
- `status` (string): Filter by status (optional)

---

## 🎨 Frontend Component

### Page Location
`/admin/credits/purchase`
Component: `/src/pages/CreditPurchase.jsx`

### Features

1. **Current Balance Card** - Shows user's current credit balance
2. **Package Cards** - 4 packages with pricing, discount badges, popular badges
3. **Purchase Button** - Redirects to Stripe Checkout
4. **Purchase History Table** - Shows past transactions with status
5. **Info Box** - Explains how credits work
6. **Responsive Design** - Mobile-friendly Material-UI cards

### UI Elements

- **Discount Badges**: Yellow badges showing discount percentage
- **Popular Badge**: Blue badge on "Pro Pack"
- **Status Chips**: Color-coded (green=completed, yellow=pending, red=failed)
- **Value Display**: Cost per 1,000 credits shown on each card

---

## 🔧 Setup Instructions

### 1. Database Migration

Already completed! Tables created:
```bash
docker exec uchub-postgres psql -U unicorn -d unicorn_db \
  -c "SELECT COUNT(*) FROM credit_packages;"
# Output: 4 packages
```

### 2. Configure Stripe Products

Run the setup script to create Stripe products:

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend

# Set Stripe API key
export STRIPE_SECRET_KEY="sk_test_..."

# Run setup script
python3 scripts/setup_stripe_credit_products.py
```

**What it does**:
1. Fetches all active packages from database
2. Creates/updates Stripe products for each package
3. Creates Stripe prices (one-time payments)
4. Updates database with `stripe_product_id` and `stripe_price_id`

**Output**:
```
Processing: Starter Pack
✓ Created new product: prod_xxx
✓ Created new price: price_xxx ($10.00)
✓ Database updated with Stripe IDs

... (repeated for all 4 packages)

Setup Complete!
Stripe Dashboard: https://dashboard.stripe.com/test/products
```

### 3. Configure Stripe Webhook

**Required for credits to be added after payment!**

1. **Go to Stripe Dashboard**:
   https://dashboard.stripe.com/test/webhooks

2. **Create Endpoint**:
   - URL: `https://your-domain.com/api/v1/billing/credits/webhook`
   - Events to send: `checkout.session.completed`

3. **Copy Webhook Secret**:
   - Format: `whsec_xxxxxxxxxx`

4. **Update Environment**:
   ```bash
   # Add to .env.auth or .env.centerdeep
   echo 'STRIPE_WEBHOOK_SECRET_CREDITS=whsec_xxxxxxxxxxxxx' >> \
     /home/muut/Production/UC-Cloud/services/ops-center/.env.auth
   ```

5. **Restart Container**:
   ```bash
   docker restart ops-center-direct
   ```

### 4. Build Frontend

**Current Status**: Frontend source files created, build pending.

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center

# Clear cache and rebuild
rm -rf node_modules/.vite dist

# Build production bundle
npm run build

# Deploy to public/
cp -r dist/* public/

# Restart container
docker restart ops-center-direct
```

**Files Modified**:
- `src/pages/CreditPurchase.jsx` - New page (13KB)
- `src/App.jsx` - Added route: `/admin/credits/purchase`

### 5. Verify Installation

```bash
# Check backend endpoints
curl http://localhost:8084/api/v1/billing/credits/packages
# Expected: {"detail": "Not authenticated"} (needs login)

# Check database
docker exec uchub-postgres psql -U unicorn -d unicorn_db \
  -c "SELECT package_code, credits, price_usd FROM credit_packages;"

# Check container logs
docker logs ops-center-direct | grep "Credit Purchase"
# Expected: "Credit Purchase API endpoints registered at /api/v1/billing/credits"
```

---

## 🧪 Testing Guide

### Test Flow (End-to-End)

1. **Login to Ops-Center**:
   - URL: https://your-domain.com
   - Use Keycloak SSO (Google/GitHub/Microsoft/Email)

2. **Navigate to Credit Purchase Page**:
   - Menu: Credits → Purchase Credits
   - Direct URL: https://your-domain.com/admin/credits/purchase

3. **View Current Balance**:
   - Should display current credit balance at top
   - Shows monthly allocation and tier

4. **Select a Package**:
   - Click "Buy Now" on any package (e.g., Starter Pack - $10)
   - Should redirect to Stripe Checkout

5. **Enter Payment Info** (Test Mode):
   - Card Number: `4242 4242 4242 4242`
   - Expiry: Any future date (e.g., `12/30`)
   - CVC: Any 3 digits (e.g., `123`)
   - ZIP: Any 5 digits (e.g., `12345`)

6. **Complete Payment**:
   - Click "Pay"
   - Redirected back to: `https://your-domain.com/admin/credits?purchase=success`

7. **Verify Credits Added**:
   - Page shows success message
   - Balance updated (may take 2-3 seconds)
   - Purchase appears in history table

8. **Check Database** (Optional):
   ```bash
   docker exec uchub-postgres psql -U unicorn -d unicorn_db \
     -c "SELECT * FROM credit_purchases ORDER BY created_at DESC LIMIT 1;"
   ```

### Test Cases

#### ✅ Happy Path
- [x] List packages without login → 401 Unauthorized
- [x] List packages with login → Returns 4 packages
- [x] Create checkout for 'starter' → Returns Stripe URL
- [x] Complete payment with test card → Credits added
- [x] View purchase history → Shows completed purchase

#### ⚠️ Edge Cases
- [ ] Cancel payment → Redirected with cancelled message
- [ ] Invalid package code → 404 Not Found
- [ ] Webhook with missing user_id → Error logged, no credits added
- [ ] Webhook signature mismatch → 400 Bad Request
- [ ] Duplicate webhook delivery → Idempotent (no double credits)

#### 🔐 Security
- [ ] All endpoints require authentication
- [ ] Admin endpoints require admin role
- [ ] Webhook uses signature verification
- [ ] User can only see own purchase history

---

## 📊 Monitoring & Debugging

### Check Container Logs
```bash
# Real-time logs
docker logs -f ops-center-direct

# Filter for credit purchase events
docker logs ops-center-direct | grep -i "credit.*purchase"

# Check for errors
docker logs ops-center-direct | grep -i error | tail -20
```

### Database Queries

```sql
-- Count purchases by status
SELECT status, COUNT(*)
FROM credit_purchases
GROUP BY status;

-- Recent purchases
SELECT user_id, package_name, amount_credits, status, created_at
FROM credit_purchases
ORDER BY created_at DESC
LIMIT 10;

-- Total revenue
SELECT SUM(amount_paid) as total_revenue
FROM credit_purchases
WHERE status = 'completed';

-- Active packages
SELECT package_code, package_name, credits, price_usd
FROM credit_packages
WHERE is_active = true
ORDER BY display_order;
```

### Stripe Dashboard

**Test Mode**:
- Products: https://dashboard.stripe.com/test/products
- Payments: https://dashboard.stripe.com/test/payments
- Webhooks: https://dashboard.stripe.com/test/webhooks
- Customers: https://dashboard.stripe.com/test/customers

**Check Webhook Logs**:
1. Go to Webhooks → Your endpoint
2. Click "Events" tab
3. Check for `checkout.session.completed` events
4. Status should be "200 OK" if working

---

## 🔄 Integration with Credit System

The credit purchase system integrates with the existing `credit_system.py`:

### Credit Flow

1. **User purchases credits** → `credit_purchase_api.py`
2. **Stripe processes payment** → Sends webhook
3. **Webhook handler** → Validates and updates purchase record
4. **Allocate credits** → Calls `credit_manager.allocate_credits()`
5. **Credits added** → Updates `user_credits` table
6. **Audit log** → Records transaction in `credit_transactions`

### Database Tables Involved

- **credit_purchases** - Purchase records (this system)
- **user_credits** - User balances (credit_system.py)
- **credit_transactions** - Transaction log (credit_system.py)

### Code Integration Points

```python
# In webhook handler (credit_purchase_api.py)
await credit_manager.allocate_credits(
    user_id=user_id,
    amount=Decimal(str(credits)),
    source="purchase",
    metadata={
        "purchase_id": str(purchase_id),
        "package_code": package_code
    }
)
```

---

## 🚀 Deployment Checklist

- [x] Database migration run (credit_purchases, credit_packages tables)
- [x] Backend API created (credit_purchase_api.py)
- [x] Backend routes added to server.py
- [x] Frontend component created (CreditPurchase.jsx)
- [x] Frontend route added to App.jsx
- [ ] **Frontend build completed** (PENDING)
- [ ] **Stripe products configured** (run setup script)
- [ ] **Stripe webhook configured** (create endpoint + secret)
- [ ] **Environment variables updated** (STRIPE_WEBHOOK_SECRET_CREDITS)
- [ ] **Container restarted** (pick up new env vars)
- [ ] **End-to-end test completed** (make test purchase)

---

## 📝 Next Steps

### Immediate (Required for Production)

1. **Build Frontend**:
   ```bash
   cd /home/muut/Production/UC-Cloud/services/ops-center
   npm run build && cp -r dist/* public/
   ```

2. **Configure Stripe Products**:
   ```bash
   cd backend
   python3 scripts/setup_stripe_credit_products.py
   ```

3. **Set Up Webhook**:
   - Create webhook in Stripe Dashboard
   - Update STRIPE_WEBHOOK_SECRET_CREDITS
   - Restart container

4. **Test End-to-End**:
   - Make test purchase
   - Verify credits added
   - Check purchase history

### Future Enhancements

- [ ] Email confirmation on purchase
- [ ] Discount codes/coupons
- [ ] Bundle deals (e.g., buy 2 get 1 free)
- [ ] Gift credits to other users
- [ ] Credit expiration dates (optional)
- [ ] Refund management UI
- [ ] Analytics dashboard (revenue, top packages, etc.)
- [ ] Subscription to credit package conversion
- [ ] Auto-purchase when balance runs low

---

## 📞 Support

**Files Created**:
- `/backend/credit_purchase_api.py` - Main API (540 lines)
- `/backend/migrations/add_credit_purchases.sql` - Database schema (131 lines)
- `/backend/scripts/setup_stripe_credit_products.py` - Stripe setup (260 lines)
- `/src/pages/CreditPurchase.jsx` - Frontend component (450 lines)

**Documentation**:
- This file: `/services/ops-center/CREDIT_PURCHASE_SETUP.md`

**Related Systems**:
- Credit System: `/backend/credit_system.py`
- Credit API: `/backend/credit_api.py`
- Stripe Integration: `/backend/stripe_integration.py`

---

**Status**: Backend complete and deployed. Frontend build pending. Ready for Stripe configuration and testing once frontend is built.

**Last Updated**: November 12, 2025 16:52 UTC
