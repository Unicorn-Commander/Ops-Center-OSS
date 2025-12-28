# Billing API Quick Reference

## Files Modified/Created

```
backend/
├── billing/
│   ├── __init__.py          # NEW: Billing module initialization
│   └── stripe_client.py     # NEW: Stripe integration client
└── server.py                # MODIFIED: Added billing endpoints (lines 1585-1955)
```

## API Endpoints Summary

### User Endpoints (Require Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/billing/subscription` | Get user's subscription |
| GET | `/api/v1/billing/invoices` | Get user's invoices |
| GET | `/api/v1/billing/payment-methods` | Get user's payment methods |
| GET | `/api/v1/billing/usage` | Get usage statistics (Lago) |

### Admin Endpoints (Require Admin Role)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/billing/stats` | Revenue & subscription stats |
| GET | `/api/v1/admin/billing/customers` | List all customers |
| GET | `/api/v1/admin/billing/subscriptions` | List all subscriptions |
| GET | `/api/v1/admin/billing/recent-charges` | Recent payments |

## StripeClient Methods

```python
from billing import StripeClient

stripe_client = StripeClient()

# Customer operations
customer = await stripe_client.get_customer_by_email("user@example.com")

# Subscription operations
subscription = await stripe_client.get_customer_subscription(customer_id)

# Invoice operations
invoices = await stripe_client.get_customer_invoices(customer_id, limit=10)

# Payment methods
payment_methods = await stripe_client.get_customer_payment_methods(customer_id)

# Admin: Customer list
customers = await stripe_client.get_all_customers(limit=100)

# Admin: Subscription list
subscriptions = await stripe_client.get_all_subscriptions(status="active", limit=100)

# Admin: Revenue statistics
stats = await stripe_client.get_revenue_stats()

# Admin: Recent charges
charges = await stripe_client.get_recent_charges(limit=20)
```

## Environment Variables Required

```bash
# Required
STRIPE_SECRET_KEY=sk_test_...

# Optional (for usage tracking)
LAGO_API_URL=http://unicorn-lago-api:3000
LAGO_API_KEY=your_lago_api_key
```

## Testing Commands

```bash
# Test module import
cd /home/muut/Production/UC-1-Pro/services/ops-center/backend
python3 -c "from billing import StripeClient; print('✓ OK')"

# Test user subscription endpoint
curl -b "session_token=TOKEN" http://localhost:8084/api/v1/billing/subscription

# Test admin stats endpoint
curl -b "session_token=ADMIN_TOKEN" http://localhost:8084/api/v1/admin/billing/stats
```

## Response Format Examples

### Subscription Response
```json
{
  "tier": "professional",
  "status": "active",
  "current_period_end": "2025-11-08T00:00:00Z",
  "cancel_at_period_end": false,
  "amount": 49.00,
  "interval": "month"
}
```

### Admin Stats Response
```json
{
  "total_customers": 150,
  "active_subscriptions": 120,
  "monthly_revenue": 5880.00,
  "trial_subscriptions": 10
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 401 | Not authenticated |
| 403 | Not an admin (admin endpoints only) |
| 500 | Stripe API error / Server error |

## Integration Points

- **SessionManager**: User authentication
- **UsageTracker**: Lago usage tracking
- **Database**: `users` table (`stripe_customer_id` column)
- **require_admin()**: Admin authentication dependency

## Key Features

✅ User subscription details  
✅ Invoice history with PDF links  
✅ Payment method management  
✅ Usage tracking integration (Lago)  
✅ Admin revenue statistics  
✅ Customer management (admin)  
✅ Subscription filtering by status  
✅ Comprehensive error handling  
✅ Detailed logging  
✅ Graceful degradation (Stripe not configured)  

---

**Quick Start:**
1. Set `STRIPE_SECRET_KEY` in environment
2. Restart ops-center service
3. Test endpoints with valid session tokens
4. Check logs: `docker logs unicorn-ops-center`
