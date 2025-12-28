# Admin Subscription Management API

**Version:** 1.0
**Authentication:** Keycloak
**Base URL:** `https://your-domain.com/api/v1/admin/subscriptions`

## Overview

The Admin Subscription Management API provides admin-only access to manage user subscriptions, usage, and billing within the UC-1 Pro platform. All user data is stored in Keycloak user attributes.

## Authentication

All endpoints require admin authentication. The user must have one of the following:
- `role == "admin"`
- `is_admin == True`
- `is_superuser == True`
- `"admin"` in `groups` array

Authentication is handled via session cookies from the main application.

## Keycloak Configuration

### Environment Variables

```bash
KEYCLOAK_URL=https://auth.your-domain.com
KEYCLOAK_REALM=uchub
KEYCLOAK_CLIENT_ID=admin-cli
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=your_admin_password
```

### User Attributes

Subscription data is stored in Keycloak user attributes:

```json
{
  "subscription_tier": ["free|trial|starter|professional|enterprise"],
  "subscription_status": ["active|cancelled|suspended|trial"],
  "api_calls_used": ["0"],
  "api_calls_limit": ["100"],
  "api_calls_reset_date": ["2025-10-10"],
  "subscription_id": ["stripe_sub_xxx"],
  "subscription_updated_at": ["2025-10-10T12:00:00Z"],
  "subscription_updated_by": ["admin@example.com"],
  "billing_period_start": ["2025-10-01"],
  "billing_period_end": ["2025-11-01"],
  "stripe_customer_id": ["cus_xxx"]
}
```

**Note:** Keycloak stores all attributes as arrays. The API handles this automatically.

## API Endpoints

### 1. List All Subscriptions

Get a list of all user subscriptions with usage stats.

**Endpoint:** `GET /api/v1/admin/subscriptions/list`

**Response:**
```json
{
  "success": true,
  "subscriptions": [
    {
      "email": "user@example.com",
      "username": "johndoe",
      "tier": "professional",
      "status": "active",
      "usage": 5432,
      "limit": 100000,
      "joined_date": 1696723200000,
      "last_login": 1696723200000,
      "is_active": true,
      "byok_providers": ["openai", "anthropic"]
    }
  ],
  "total": 42
}
```

### 2. Get User Subscription

Get detailed subscription info for a specific user.

**Endpoint:** `GET /api/v1/admin/subscriptions/{email}`

**Response:**
```json
{
  "success": true,
  "user": {
    "email": "user@example.com",
    "username": "johndoe",
    "name": "John Doe",
    "is_active": true,
    "tier": "professional",
    "status": "active",
    "subscription_id": "sub_xxx",
    "usage": {
      "api_calls_used": 5432,
      "api_calls_limit": 100000,
      "period_start": "2025-10-01",
      "period_end": "2025-11-01"
    },
    "byok_keys": ["openai", "anthropic"],
    "subscription_updated_at": "2025-10-10T12:00:00Z",
    "joined_date": 1696723200000,
    "last_login": 1696723200000
  }
}
```

### 3. Update User Subscription

Manually update a user's subscription (for support cases).

**Endpoint:** `PATCH /api/v1/admin/subscriptions/{email}`

**Request Body:**
```json
{
  "tier": "professional",
  "status": "active",
  "notes": "Upgraded manually by support"
}
```

**Valid Tiers:**
- `free` - Free tier (100 API calls/day)
- `trial` - Trial tier (1,000 API calls/day)
- `starter` - Starter tier (10,000 API calls/day) - $19/mo
- `professional` - Professional tier (100,000 API calls/day) - $49/mo
- `enterprise` - Enterprise tier (1,000,000 API calls/day) - $99/mo

**Valid Statuses:**
- `active` - Active subscription
- `cancelled` - Cancelled (access until period end)
- `suspended` - Suspended (no access)
- `trial` - Trial period

**Response:**
```json
{
  "success": true,
  "message": "Subscription updated successfully",
  "email": "user@example.com",
  "tier": "professional",
  "status": "active"
}
```

### 4. Reset User Usage

Reset a user's API usage counters.

**Endpoint:** `POST /api/v1/admin/subscriptions/{email}/reset-usage`

**Response:**
```json
{
  "success": true,
  "message": "Usage reset successfully",
  "email": "user@example.com",
  "reset_by": "admin@example.com"
}
```

### 5. Get Analytics Overview

Get subscription analytics and revenue metrics.

**Endpoint:** `GET /api/v1/admin/subscriptions/analytics/overview`

**Response:**
```json
{
  "success": true,
  "analytics": {
    "total_users": 150,
    "active_subscriptions": 120,
    "tier_distribution": {
      "free": 50,
      "trial": 30,
      "starter": 40,
      "professional": 25,
      "enterprise": 5
    },
    "revenue": {
      "monthly_recurring_revenue": 2830,
      "annual_recurring_revenue": 33960
    },
    "usage": {
      "total_api_calls": 1250000,
      "average_per_user": 8333.33
    }
  }
}
```

### 6. Get Revenue by Tier

Get revenue breakdown by subscription tier.

**Endpoint:** `GET /api/v1/admin/subscriptions/analytics/revenue-by-tier`

**Response:**
```json
{
  "success": true,
  "revenue_by_tier": {
    "starter": {
      "users": 40,
      "monthly_revenue": 760,
      "annual_revenue": 9120
    },
    "professional": {
      "users": 25,
      "monthly_revenue": 1225,
      "annual_revenue": 14700
    },
    "enterprise": {
      "users": 5,
      "monthly_revenue": 495,
      "annual_revenue": 5940
    }
  }
}
```

### 7. Get Usage Statistics

Get detailed usage statistics.

**Endpoint:** `GET /api/v1/admin/subscriptions/analytics/usage-stats`

**Response:**
```json
{
  "success": true,
  "usage_stats": {
    "total_users": 150,
    "users_with_usage": 120,
    "total_api_calls": 1250000,
    "usage_by_tier": {
      "free": {
        "users": 50,
        "total_calls": 2500,
        "average_calls": 50
      },
      "professional": {
        "users": 25,
        "total_calls": 500000,
        "average_calls": 20000
      }
    }
  }
}
```

## Error Responses

### 403 Forbidden
```json
{
  "detail": "Admin access required"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid tier. Must be one of: ['free', 'trial', 'starter', 'professional', 'enterprise']"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to update subscription"
}
```

## Frontend Integration

### Admin Dashboard

The admin dashboard is available at `/admin/subscriptions.html`

**Features:**
- DataTables with search and pagination
- Real-time analytics dashboard
- Edit subscription modal
- Reset usage functionality
- Tier distribution charts
- Revenue metrics

**JavaScript API Calls:**

```javascript
// List all subscriptions
const response = await fetch('/api/v1/admin/subscriptions/list');
const data = await response.json();

// Update subscription
const response = await fetch(`/api/v1/admin/subscriptions/${email}`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    tier: 'professional',
    status: 'active',
    notes: 'Upgraded by support'
  })
});

// Reset usage
const response = await fetch(`/api/v1/admin/subscriptions/${email}/reset-usage`, {
  method: 'POST'
});

// Get analytics
const response = await fetch('/api/v1/admin/subscriptions/analytics/overview');
const data = await response.json();
```

## Testing

### Run Test Suite

```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center/tests
./run_admin_tests.sh
```

### Manual Testing

1. **Login as admin:**
   ```
   https://your-domain.com/login.html
   ```

2. **Access admin dashboard:**
   ```
   https://your-domain.com/admin/subscriptions.html
   ```

3. **Test API directly:**
   ```bash
   # Get all subscriptions
   curl -X GET https://your-domain.com/api/v1/admin/subscriptions/list \
     -H "Cookie: session=your_session_cookie"

   # Update subscription
   curl -X PATCH https://your-domain.com/api/v1/admin/subscriptions/user@example.com \
     -H "Cookie: session=your_session_cookie" \
     -H "Content-Type: application/json" \
     -d '{"tier":"professional","status":"active"}'
   ```

### Python Tests

```python
import sys
sys.path.insert(0, '/home/muut/Production/UC-1-Pro/services/ops-center/backend')

from keycloak_integration import get_all_users, get_user_tier_info

# Get all users
users = await get_all_users()
print(f"Total users: {len(users)}")

# Get tier info
tier_info = await get_user_tier_info("user@example.com")
print(f"Tier: {tier_info['subscription_tier']}")
```

## Security Considerations

1. **Admin Authentication:**
   - All endpoints require admin role
   - Session-based authentication
   - No public access

2. **Keycloak Integration:**
   - Uses admin credentials securely
   - Token caching with expiration
   - SSL/TLS for all connections

3. **Audit Trail:**
   - All updates tracked with admin email
   - Timestamps on all modifications
   - Admin notes field for documentation

4. **Rate Limiting:**
   - Apply rate limiting to admin endpoints
   - Monitor for abuse
   - Log all admin actions

## Subscription Tiers & Pricing

| Tier | Price | API Calls/Day | Features |
|------|-------|---------------|----------|
| Free | $0 | 100 | Basic access |
| Trial | $0 | 1,000 | Trial period |
| Starter | $19/mo | 10,000 | BYOK support |
| Professional | $49/mo | 100,000 | Priority support, BYOK |
| Enterprise | $99/mo | 1,000,000 | Team features, BYOK, SLA |

## Files

**Backend:**
- `/home/muut/Production/UC-1-Pro/services/ops-center/backend/keycloak_integration.py` - Keycloak client
- `/home/muut/Production/UC-1-Pro/services/ops-center/backend/admin_subscriptions_api.py` - API endpoints

**Frontend:**
- `/home/muut/Production/UC-1-Pro/services/ops-center/public/admin/subscriptions.html` - Admin UI

**Tests:**
- `/home/muut/Production/UC-1-Pro/services/ops-center/tests/test_keycloak_admin.py` - Test suite
- `/home/muut/Production/UC-1-Pro/services/ops-center/tests/run_admin_tests.sh` - Test runner

## Support

For issues or questions:
- Check logs: `docker logs unicorn-ops-center`
- Keycloak admin: `https://auth.your-domain.com/admin/uchub/console`
- GitHub Issues: https://github.com/Unicorn-Commander/UC-1-Pro/issues
