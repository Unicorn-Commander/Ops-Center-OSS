# Admin Subscription Management API

## Overview

The Admin Subscription Management API provides comprehensive tools for administrators to manage user subscriptions, billing, and usage analytics across the UC-1 Pro platform.

## Authentication

All endpoints require admin authentication. Users must have one of:
- `role` set to `"admin"`
- `is_admin` set to `true`
- `is_superuser` set to `true`
- `"admin"` in their `groups` array

## Base URL

```
/api/v1/admin/subscriptions
```

## Endpoints

### List All Subscriptions

Get a list of all user subscriptions with basic info.

**Endpoint:** `GET /api/v1/admin/subscriptions/list`

**Response:**
```json
{
  "success": true,
  "subscriptions": [
    {
      "email": "user@example.com",
      "username": "user123",
      "tier": "professional",
      "status": "active",
      "usage": 5000,
      "limit": 100000,
      "joined_date": "2025-01-15T10:30:00Z",
      "last_login": "2025-10-10T08:45:00Z",
      "is_active": true,
      "byok_providers": ["openai", "anthropic"]
    }
  ],
  "total": 1
}
```

### Get User Subscription Details

Get detailed subscription information for a specific user.

**Endpoint:** `GET /api/v1/admin/subscriptions/{email}`

**Response:**
```json
{
  "success": true,
  "user": {
    "email": "user@example.com",
    "username": "user123",
    "name": "John Doe",
    "is_active": true,
    "tier": "professional",
    "status": "active",
    "subscription_id": "sub_1234567890",
    "usage": {
      "api_calls_used": 5000,
      "api_calls_limit": 100000,
      "period_start": "2025-10-01T00:00:00Z",
      "period_end": "2025-10-31T23:59:59Z"
    },
    "byok_keys": ["openai", "anthropic"],
    "subscription_updated_at": "2025-10-01T12:00:00Z",
    "joined_date": "2025-01-15T10:30:00Z",
    "last_login": "2025-10-10T08:45:00Z"
  }
}
```

### Update User Subscription

Manually update a user's subscription tier and status (for support cases).

**Endpoint:** `PATCH /api/v1/admin/subscriptions/{email}`

**Request Body:**
```json
{
  "tier": "professional",
  "status": "active",
  "notes": "Upgraded for customer support issue #1234"
}
```

**Valid Tiers:**
- `free` - Free tier (100 API calls/month)
- `trial` - Trial tier (1,000 API calls/month)
- `starter` - Starter tier (10,000 API calls/month) - $19/mo
- `professional` - Professional tier (100,000 API calls/month) - $49/mo
- `enterprise` - Enterprise tier (1,000,000 API calls/month) - $99/mo

**Valid Statuses:**
- `active` - Active subscription
- `trial` - Trial period
- `cancelled` - Cancelled subscription
- `suspended` - Suspended (payment issues, etc.)

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

### Reset User Usage

Reset a user's API usage counters (e.g., for billing period reset or support).

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

### Analytics Overview

Get high-level subscription and revenue analytics.

**Endpoint:** `GET /api/v1/admin/subscriptions/analytics/overview`

**Response:**
```json
{
  "success": true,
  "analytics": {
    "total_users": 150,
    "active_subscriptions": 120,
    "tier_distribution": {
      "free": 30,
      "trial": 20,
      "starter": 40,
      "professional": 35,
      "enterprise": 25
    },
    "revenue": {
      "monthly_recurring_revenue": 5985,
      "annual_recurring_revenue": 71820
    },
    "usage": {
      "total_api_calls": 1500000,
      "average_per_user": 10000
    }
  }
}
```

### Revenue By Tier

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
      "users": 35,
      "monthly_revenue": 1715,
      "annual_revenue": 20580
    },
    "enterprise": {
      "users": 25,
      "monthly_revenue": 2475,
      "annual_revenue": 29700
    }
  }
}
```

### Usage Statistics

Get detailed API usage statistics by tier.

**Endpoint:** `GET /api/v1/admin/subscriptions/analytics/usage-stats`

**Response:**
```json
{
  "success": true,
  "usage_stats": {
    "total_users": 150,
    "users_with_usage": 95,
    "total_api_calls": 1500000,
    "usage_by_tier": {
      "free": {
        "users": 30,
        "total_calls": 1500,
        "average_calls": 50
      },
      "trial": {
        "users": 20,
        "total_calls": 12000,
        "average_calls": 600
      },
      "starter": {
        "users": 40,
        "total_calls": 180000,
        "average_calls": 4500
      },
      "professional": {
        "users": 35,
        "total_calls": 525000,
        "average_calls": 15000
      },
      "enterprise": {
        "users": 25,
        "total_calls": 781500,
        "average_calls": 31260
      }
    }
  }
}
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

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
  "detail": "Invalid tier. Must be one of: free, trial, starter, professional, enterprise"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "detail": "Error message details"
}
```

## Frontend Dashboard

A complete admin dashboard is available at:

```
/admin/subscriptions.html
```

**Features:**
- View all user subscriptions in a sortable, searchable table
- Real-time analytics dashboard (MRR, ARR, user counts)
- Edit subscription tiers and statuses
- Reset user API usage
- Export subscription data to CSV
- Detailed user subscription views

## Usage Examples

### Using curl

```bash
# Get all subscriptions
curl -X GET http://localhost:8084/api/v1/admin/subscriptions/list \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN"

# Get specific user
curl -X GET http://localhost:8084/api/v1/admin/subscriptions/user@example.com \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN"

# Update subscription
curl -X PATCH http://localhost:8084/api/v1/admin/subscriptions/user@example.com \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tier": "professional", "status": "active", "notes": "Support upgrade"}'

# Reset usage
curl -X POST http://localhost:8084/api/v1/admin/subscriptions/user@example.com/reset-usage \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN"

# Get analytics
curl -X GET http://localhost:8084/api/v1/admin/subscriptions/analytics/overview \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN"
```

### Using Python

```python
import httpx

async def get_subscriptions():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8084/api/v1/admin/subscriptions/list",
            cookies={"session_token": "YOUR_SESSION_TOKEN"}
        )
        return response.json()

async def update_subscription(email, tier, status):
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"http://localhost:8084/api/v1/admin/subscriptions/{email}",
            json={"tier": tier, "status": status},
            cookies={"session_token": "YOUR_SESSION_TOKEN"}
        )
        return response.json()
```

## Integration with Authentik

All user data is stored in Authentik user attributes:

- `subscription_tier` - User's subscription tier
- `subscription_status` - Subscription status
- `subscription_id` - External billing system ID (e.g., Stripe)
- `api_calls_used` - Current period API usage
- `api_calls_limit` - Maximum API calls for tier
- `billing_period_start` - Start of current billing period
- `billing_period_end` - End of current billing period
- `byok_*_key` - Encrypted BYOK provider keys
- `subscription_updated_at` - Last update timestamp
- `subscription_updated_by` - Admin who made the update
- `admin_notes` - Internal admin notes

## Security Considerations

1. **Admin Access Required** - All endpoints verify admin role
2. **Audit Logging** - All admin actions are logged
3. **BYOK Key Privacy** - Only provider names shown, not actual keys
4. **Rate Limiting** - Admin endpoints have higher rate limits
5. **Session Security** - Requires valid session cookie

## Testing

Run the test suite:

```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center
python3 backend/tests/test_admin_subscriptions.py
```

Test requirements:
- Ops Center server running on port 8084
- Active admin session (login via browser first)
- Authentik API token configured

## Files

### Backend
- `/home/muut/Production/UC-1-Pro/services/ops-center/backend/admin_subscriptions_api.py` - Main API router
- `/home/muut/Production/UC-1-Pro/services/ops-center/backend/authentik_integration.py` - Authentik integration

### Frontend
- `/home/muut/Production/UC-1-Pro/services/ops-center/public/admin/subscriptions.html` - Admin dashboard

### Tests
- `/home/muut/Production/UC-1-Pro/services/ops-center/backend/tests/test_admin_subscriptions.py` - API tests

### Documentation
- This file - API documentation
