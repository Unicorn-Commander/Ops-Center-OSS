# Billing API Implementation

## Overview

Added comprehensive REST API endpoints for billing and subscription management to the Ops Center backend. This implementation integrates with Stripe for payment processing and Lago for usage-based billing.

## Files Created

### 1. `/backend/billing/__init__.py`
- Module initialization
- Exports StripeClient class

### 2. `/backend/billing/stripe_client.py`
- Complete Stripe integration client
- Methods for subscriptions, invoices, payment methods, and admin statistics
- Comprehensive error handling and logging
- Graceful degradation when Stripe is not configured

## API Endpoints Added

### User Endpoints (Authentication Required)

#### `GET /api/v1/billing/subscription`
Get current user's subscription information.

**Response:**
```json
{
  "tier": "professional",
  "status": "active",
  "current_period_start": "2025-09-08T00:00:00Z",
  "current_period_end": "2025-10-08T00:00:00Z",
  "cancel_at_period_end": false,
  "amount": 49.00,
  "interval": "month",
  "currency": "usd"
}
```

**Error Codes:**
- 401: Not authenticated
- 500: Stripe API error

---

#### `GET /api/v1/billing/invoices?limit=10`
Get current user's invoices.

**Query Parameters:**
- `limit` (optional): Maximum invoices to return (default: 10)

**Response:**
```json
[
  {
    "id": "in_1234...",
    "number": "INV-2025-0001",
    "amount_due": 49.00,
    "amount_paid": 49.00,
    "currency": "usd",
    "status": "paid",
    "created": "2025-09-08T00:00:00Z",
    "due_date": "2025-09-15T00:00:00Z",
    "paid": true,
    "invoice_pdf": "https://stripe.com/...",
    "hosted_invoice_url": "https://stripe.com/..."
  }
]
```

---

#### `GET /api/v1/billing/payment-methods`
Get current user's payment methods.

**Response:**
```json
[
  {
    "id": "pm_1234...",
    "type": "card",
    "card": {
      "brand": "visa",
      "last4": "4242",
      "exp_month": 12,
      "exp_year": 2026
    },
    "created": "2025-09-08T00:00:00Z"
  }
]
```

---

#### `GET /api/v1/billing/usage`
Get current user's usage statistics from Lago.

**Response:**
```json
{
  "usage": {
    "today": {
      "inference": 15,
      "embedding": 5,
      "tts": 0,
      "stt": 0
    },
    "month": {
      "inference": 450,
      "embedding": 120,
      "tts": 10,
      "stt": 5
    }
  },
  "credits": {
    "tier": "professional",
    "included_credits": 500,
    "used": 585,
    "remaining": 0,
    "overage": 85,
    "overage_cost": 0.17,
    "price_per_1k": 2.00
  },
  "tier": "professional"
}
```

---

### Admin Endpoints (Admin Role Required)

#### `GET /api/v1/admin/billing/stats`
Get revenue and subscription statistics.

**Response:**
```json
{
  "total_customers": 150,
  "active_subscriptions": 120,
  "trial_subscriptions": 10,
  "monthly_revenue": 5880.00,
  "tier_breakdown": {
    "trial": {
      "count": 10,
      "revenue": 0
    },
    "starter": {
      "count": 30,
      "revenue": 570.00
    },
    "professional": {
      "count": 70,
      "revenue": 3430.00
    },
    "enterprise": {
      "count": 10,
      "revenue": 990.00
    }
  }
}
```

**Error Codes:**
- 401: Not authenticated
- 403: Not an admin
- 500: Stripe API error

---

#### `GET /api/v1/admin/billing/customers?limit=100`
Get all Stripe customers.

**Query Parameters:**
- `limit` (optional): Maximum customers to return (default: 100)

**Response:**
```json
{
  "customers": [
    {
      "id": "cus_1234...",
      "email": "user@example.com",
      "name": "John Doe",
      "created": "2025-09-01T00:00:00Z",
      "metadata": {
        "user_id": "abc123",
        "tier": "professional"
      }
    }
  ],
  "total": 150
}
```

---

#### `GET /api/v1/admin/billing/subscriptions?status=active&limit=100`
Get all subscriptions.

**Query Parameters:**
- `status` (optional): Filter by status (active, canceled, etc.)
- `limit` (optional): Maximum subscriptions to return (default: 100)

**Response:**
```json
{
  "subscriptions": [
    {
      "id": "sub_1234...",
      "customer": "cus_5678...",
      "tier": "professional",
      "status": "active",
      "amount": 49.00,
      "currency": "usd",
      "interval": "month",
      "current_period_end": "2025-10-08T00:00:00Z",
      "cancel_at_period_end": false
    }
  ],
  "total": 120
}
```

---

#### `GET /api/v1/admin/billing/recent-charges?limit=20`
Get recent charges/payments.

**Query Parameters:**
- `limit` (optional): Maximum charges to return (default: 20)

**Response:**
```json
{
  "charges": [
    {
      "id": "ch_1234...",
      "amount": 49.00,
      "currency": "usd",
      "status": "succeeded",
      "customer": "cus_5678...",
      "description": "Professional subscription",
      "created": "2025-09-08T00:00:00Z",
      "paid": true,
      "refunded": false
    }
  ],
  "total": 20
}
```

---

## Integration with Existing Code

### StripeClient Features

The `StripeClient` class provides:

1. **Customer Management**
   - Find customer by email
   - Get customer details
   - List all customers (admin)

2. **Subscription Management**
   - Get active subscription for customer
   - List all subscriptions (admin)
   - Filter by status

3. **Invoice Management**
   - Get customer invoices
   - Access invoice PDFs
   - View payment status

4. **Payment Methods**
   - List customer payment methods
   - Card details (brand, last4, expiration)

5. **Revenue Statistics**
   - Total customers
   - Active subscriptions
   - Monthly recurring revenue (MRR)
   - Revenue breakdown by tier
   - Trial subscription count

6. **Recent Charges**
   - Recent payment history
   - Charge status and details

### UsageTracker Integration

The billing endpoints integrate with the existing `UsageTracker` from the auth module:

- Tracks API usage in Redis (fast)
- Optionally syncs with Lago for accurate billing
- Calculates remaining credits
- Computes overage costs
- Supports all event types (inference, embedding, tts, stt)

### Authentication

All endpoints require valid session authentication:
- User endpoints: Any authenticated user
- Admin endpoints: Admin role required via `require_admin()` dependency

### Database Integration

Endpoints use the existing SQLite database:
- Links users to Stripe customers via `stripe_customer_id`
- Stores subscription tier information
- Maintains user email for Stripe lookup

## Environment Variables

Required environment variables:

```bash
# Stripe Configuration (Required)
STRIPE_SECRET_KEY=sk_test_...

# Lago Configuration (Optional - for usage tracking)
LAGO_API_URL=http://unicorn-lago-api:3000
LAGO_API_KEY=your_lago_api_key

# Redis (Already configured)
REDIS_URL=redis://unicorn-redis:6379/0
```

## Error Handling

All endpoints include comprehensive error handling:

1. **Authentication Errors** (401)
   - Missing session token
   - Invalid/expired session

2. **Authorization Errors** (403)
   - Admin endpoints accessed by non-admin users

3. **Stripe API Errors** (500)
   - Logged with detailed error messages
   - User-friendly error responses
   - Graceful degradation when Stripe not configured

4. **Missing Data**
   - Returns empty arrays for customers without Stripe accounts
   - Returns basic tier info for users without subscriptions

## Logging

All endpoints include comprehensive logging:

- Info level: Successful operations
- Warning level: Authentication issues
- Error level: API errors with full stack traces

Example log output:
```
2025-10-08 03:45:12 - __main__ - INFO - Retrieved subscription for user user@example.com
2025-10-08 03:45:15 - __main__ - INFO - Admin retrieved billing statistics
2025-10-08 03:45:20 - __main__ - ERROR - Error retrieving subscription for user@example.com: StripeError: Invalid API key
```

## Testing

### Manual Testing

Test user endpoints:
```bash
# Get subscription (requires valid session cookie)
curl -b "session_token=YOUR_SESSION_TOKEN" \
  http://localhost:8084/api/v1/billing/subscription

# Get invoices
curl -b "session_token=YOUR_SESSION_TOKEN" \
  http://localhost:8084/api/v1/billing/invoices?limit=5

# Get usage
curl -b "session_token=YOUR_SESSION_TOKEN" \
  http://localhost:8084/api/v1/billing/usage
```

Test admin endpoints:
```bash
# Get billing stats (requires admin session)
curl -b "session_token=ADMIN_SESSION_TOKEN" \
  http://localhost:8084/api/v1/admin/billing/stats

# Get all customers
curl -b "session_token=ADMIN_SESSION_TOKEN" \
  http://localhost:8084/api/v1/admin/billing/customers?limit=50

# Get active subscriptions
curl -b "session_token=ADMIN_SESSION_TOKEN" \
  http://localhost:8084/api/v1/admin/billing/subscriptions?status=active
```

### Integration Testing

The implementation integrates with:
- Existing `SessionManager` for authentication
- Existing `UsageTracker` for Lago integration
- Existing database schema (users table)
- Existing `require_admin()` dependency

## Security Considerations

1. **Authentication Required**
   - All endpoints require valid session
   - Admin endpoints verify admin role

2. **Data Isolation**
   - Users can only access their own billing data
   - Admin endpoints restricted to admin role

3. **Error Messages**
   - Don't expose sensitive Stripe data
   - Generic error messages to users
   - Detailed errors logged server-side

4. **API Key Security**
   - Stripe key from environment variable
   - Never exposed in responses
   - Validated on startup

## Future Enhancements

Potential improvements:

1. **Caching**
   - Cache Stripe data in Redis
   - Reduce API calls
   - Improve response times

2. **Webhooks**
   - Real-time subscription updates
   - Payment status changes
   - Customer updates

3. **Usage Limits**
   - Enforce usage limits
   - Auto-throttling
   - Overage warnings

4. **Analytics**
   - Revenue trends
   - Churn analysis
   - Customer lifetime value

5. **Exports**
   - CSV/PDF reports
   - Invoice bulk download
   - Usage reports

## Support

For issues or questions:
- Check logs: `docker logs unicorn-ops-center`
- Verify Stripe key: `echo $STRIPE_SECRET_KEY`
- Test Stripe connection: Python REPL with `import stripe; stripe.api_key = "sk_..."; stripe.Customer.list(limit=1)`

---

**Implementation Date:** October 8, 2025  
**Version:** 1.0.0  
**Author:** Backend API Developer Agent
