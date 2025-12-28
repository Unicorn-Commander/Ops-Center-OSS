# Organization Billing API Reference

**Version**: 1.0.0
**Base URL**: `/api/v1/org-billing`
**Authentication**: Session-based (Keycloak SSO)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Subscription Management](#subscription-management)
3. [Credit Pool Management](#credit-pool-management)
4. [User Allocations](#user-allocations)
5. [Billing Dashboards](#billing-dashboards)
6. [Usage Analytics](#usage-analytics)
7. [Error Codes](#error-codes)
8. [Rate Limits](#rate-limits)

---

## Authentication

All endpoints require a valid session token obtained through Keycloak SSO.

### Session Token

```http
Cookie: session_token=<JWT_TOKEN>
```

### Permission Levels

| Role | Access |
|------|--------|
| **System Admin** | All endpoints |
| **Org Admin** | Own organization only |
| **Org Member** | Read-only for own organization |
| **Anonymous** | None |

---

## Subscription Management

### Create Organization Subscription

Creates a new subscription for an organization.

```http
POST /api/v1/org-billing/subscriptions
```

**Request Body**:
```json
{
  "org_id": "string",           // Required: Organization ID
  "plan_code": "string",        // Required: Plan code (platform/byok/hybrid)
  "org_name": "string",         // Required: Organization name
  "billing_email": "string",    // Required: Billing contact email
  "initial_credits": number,    // Optional: Credits to add on signup
  "user_id": "string"           // Required: User creating subscription
}
```

**Response** (`200 OK`):
```json
{
  "subscription": {
    "id": "uuid",
    "org_id": "org_abc123",
    "plan_code": "professional",
    "plan_name": "Professional Plan",
    "monthly_price": 49.00,
    "lago_subscription_id": "sub_lago_123",
    "status": "active",
    "billing_cycle_start": "2025-11-01",
    "billing_cycle_end": "2025-11-30",
    "created_at": "2025-11-01T00:00:00Z"
  },
  "credit_pool": {
    "total_credits": 10000.0,
    "allocated_credits": 0.0,
    "used_credits": 0.0,
    "available_credits": 10000.0
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid request body
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to create subscription
- `409 Conflict`: Organization already has active subscription

---

### Get Organization Subscription

Retrieves the current subscription for an organization.

```http
GET /api/v1/org-billing/subscriptions/{org_id}
```

**Path Parameters**:
- `org_id` (string, required): Organization ID

**Response** (`200 OK`):
```json
{
  "subscription": {
    "id": "uuid",
    "org_id": "org_abc123",
    "plan_code": "professional",
    "plan_name": "Professional Plan",
    "monthly_price": 49.00,
    "status": "active",
    "billing_cycle_start": "2025-11-01",
    "billing_cycle_end": "2025-11-30"
  },
  "lago_status": "active",
  "next_billing_date": "2025-12-01",
  "outstanding_balance": 0.00
}
```

**Error Responses**:
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to view subscription
- `404 Not Found`: No subscription found

---

### Upgrade Subscription

Upgrades organization to a different plan.

```http
PUT /api/v1/org-billing/subscriptions/{org_id}/upgrade
```

**Path Parameters**:
- `org_id` (string, required): Organization ID

**Request Body**:
```json
{
  "new_plan_code": "string",       // Required: New plan code
  "effective_immediately": boolean  // Optional: Default true
}
```

**Response** (`200 OK`):
```json
{
  "subscription": {
    "id": "uuid",
    "org_id": "org_abc123",
    "plan_code": "enterprise",
    "monthly_price": 99.00,
    "status": "active"
  },
  "price_change": {
    "old_price": 49.00,
    "new_price": 99.00,
    "proration": 25.00
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid plan code or downgrade attempt
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Org admin permission required
- `404 Not Found`: Subscription not found

---

## Credit Pool Management

### Get Credit Pool Status

Retrieves the organization's credit pool status.

```http
GET /api/v1/org-billing/credits/{org_id}
```

**Path Parameters**:
- `org_id` (string, required): Organization ID

**Response** (`200 OK`):
```json
{
  "org_id": "org_abc123",
  "total_credits": 10000.0,
  "allocated_credits": 8000.0,
  "used_credits": 3456.0,
  "available_credits": 2000.0,
  "allocation_percentage": 80.0,
  "usage_percentage": 43.2,
  "monthly_refresh_amount": 0.0,
  "last_refresh_date": null
}
```

**Calculations**:
- `available_credits = total_credits - allocated_credits`
- `allocation_percentage = (allocated_credits / total_credits) * 100`
- `usage_percentage = (used_credits / allocated_credits) * 100`

**Error Responses**:
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to view pool
- `404 Not Found`: Organization not found

---

### Add Credits to Pool

Purchases and adds credits to the organization pool.

```http
POST /api/v1/org-billing/credits/{org_id}/add
```

**Path Parameters**:
- `org_id` (string, required): Organization ID

**Request Body**:
```json
{
  "credits": number,              // Required: Credits to add
  "purchase_amount": number,      // Required: Dollar amount
  "stripe_payment_id": "string"   // Optional: Stripe payment ID
}
```

**Response** (`200 OK`):
```json
{
  "pool": {
    "total_credits": 15000.0,
    "allocated_credits": 8000.0,
    "used_credits": 3456.0,
    "available_credits": 7000.0
  },
  "transaction": {
    "id": "uuid",
    "event_type": "credits_purchased",
    "amount": 50.00,
    "credits": 5000.0,
    "created_at": "2025-11-15T10:30:00Z"
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid credits amount
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Org admin permission required
- `422 Unprocessable Entity`: Payment processing failed

---

## User Allocations

### Allocate Credits to User

Allocates credits from the organization pool to a specific user.

```http
POST /api/v1/org-billing/credits/{org_id}/allocate
```

**Path Parameters**:
- `org_id` (string, required): Organization ID

**Request Body**:
```json
{
  "user_id": "string",          // Required: User ID
  "credits": number,            // Required: Credits to allocate
  "expires_at": "string"        // Optional: ISO 8601 timestamp
}
```

**Response** (`200 OK`):
```json
{
  "allocation": {
    "id": "uuid",
    "org_id": "org_abc123",
    "user_id": "user_xyz789",
    "allocated_credits": 1000.0,
    "used_credits": 0.0,
    "remaining_credits": 1000.0,
    "is_active": true,
    "allocated_by": "user_admin_456",
    "created_at": "2025-11-15T10:35:00Z",
    "expires_at": null
  },
  "pool_updated": {
    "allocated_credits": 9000.0,
    "available_credits": 1000.0
  }
}
```

**Error Responses**:
- `400 Bad Request`: Insufficient credits in pool
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Org admin permission required
- `404 Not Found`: User not found

---

### Get User Allocations

Lists all user credit allocations for an organization.

```http
GET /api/v1/org-billing/credits/{org_id}/allocations
```

**Path Parameters**:
- `org_id` (string, required): Organization ID

**Query Parameters**:
- `user_id` (string, optional): Filter by specific user
- `is_active` (boolean, optional): Filter active/inactive allocations
- `limit` (number, optional): Results per page (default: 50, max: 100)
- `offset` (number, optional): Pagination offset (default: 0)

**Response** (`200 OK`):
```json
{
  "allocations": [
    {
      "user_id": "user_xyz789",
      "user_email": "john@acme.com",
      "allocated_credits": 5000.0,
      "used_credits": 2300.0,
      "remaining_credits": 2700.0,
      "usage_percentage": 46.0,
      "is_active": true,
      "allocated_at": "2025-11-01T00:00:00Z"
    }
  ],
  "total": 15,
  "limit": 50,
  "offset": 0
}
```

**Error Responses**:
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to view allocations

---

## Billing Dashboards

### User Multi-Org Dashboard

Retrieves billing information for all organizations the user belongs to.

```http
GET /api/v1/org-billing/billing/user
```

**Response** (`200 OK`):
```json
{
  "organizations": [
    {
      "org_id": "org_abc123",
      "org_name": "ACME Corporation",
      "role": "member",
      "subscription": {
        "plan_code": "professional",
        "monthly_price": 49.00,
        "status": "active"
      },
      "allocation": {
        "allocated_credits": 5000.0,
        "used_credits": 2300.0,
        "remaining_credits": 2700.0,
        "usage_percentage": 46.0
      },
      "next_reset_date": "2025-12-01"
    }
  ],
  "total_credits_available": 8200.0,
  "total_credits_used": 3450.0,
  "usage_last_30_days": {
    "total_requests": 1523,
    "total_credits": 3456.0,
    "avg_cost_per_request": 2.27
  }
}
```

**Error Responses**:
- `401 Unauthorized`: Not authenticated

---

### Organization Admin Dashboard

Comprehensive billing dashboard for organization administrators.

```http
GET /api/v1/org-billing/billing/org/{org_id}
```

**Path Parameters**:
- `org_id` (string, required): Organization ID

**Response** (`200 OK`):
```json
{
  "organization": {
    "org_id": "org_abc123",
    "org_name": "ACME Corporation",
    "created_at": "2025-10-01T00:00:00Z"
  },
  "subscription": {
    "plan_code": "professional",
    "plan_name": "Professional Plan",
    "monthly_price": 49.00,
    "status": "active",
    "next_billing_date": "2025-12-01"
  },
  "credit_pool": {
    "total_credits": 10000.0,
    "allocated_credits": 8000.0,
    "used_credits": 3456.0,
    "available_credits": 2000.0
  },
  "user_allocations": [
    {
      "user_id": "user_xyz789",
      "user_email": "john@acme.com",
      "allocated_credits": 2000.0,
      "used_credits": 856.0,
      "remaining_credits": 1144.0,
      "usage_percentage": 42.8
    }
  ],
  "usage_stats": {
    "last_30_days": {
      "total_credits": 3456.0,
      "total_requests": 1523,
      "by_service": {
        "llm_inference": {
          "credits": 3200.0,
          "requests": 1450
        },
        "image_generation": {
          "credits": 256.0,
          "requests": 73
        }
      },
      "by_user": [
        {
          "user_email": "john@acme.com",
          "credits": 2300.0,
          "requests": 980
        }
      ]
    }
  },
  "recent_activity": [
    {
      "event_type": "credits_purchased",
      "amount": 100.00,
      "credits": 10000.0,
      "created_at": "2025-11-01T00:00:00Z"
    }
  ]
}
```

**Error Responses**:
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Org admin permission required
- `404 Not Found`: Organization not found

---

### System Admin Overview

System-wide billing overview for administrators.

```http
GET /api/v1/org-billing/billing/system
```

**Permissions**: System admin only

**Response** (`200 OK`):
```json
{
  "metrics": {
    "total_organizations": 45,
    "active_subscriptions": 42,
    "total_mrr": 2145.00,
    "total_arr": 25740.00,
    "total_credits_allocated": 450000.0,
    "total_credits_used": 125000.0
  },
  "subscription_distribution": {
    "platform": {
      "count": 25,
      "mrr": 1250.00
    },
    "byok": {
      "count": 15,
      "mrr": 450.00
    },
    "hybrid": {
      "count": 5,
      "mrr": 495.00
    }
  },
  "top_organizations": [
    {
      "org_id": "org_abc123",
      "org_name": "ACME Corporation",
      "plan_code": "enterprise",
      "mrr": 99.00,
      "credits_used_30d": 45600.0,
      "status": "active"
    }
  ],
  "usage_trends": {
    "last_7_days": [
      {
        "date": "2025-11-14",
        "total_credits": 8900.0,
        "total_requests": 3200
      }
    ]
  }
}
```

**Error Responses**:
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: System admin permission required

---

## Usage Analytics

### Get Usage Statistics

Detailed usage statistics for an organization.

```http
GET /api/v1/org-billing/credits/{org_id}/usage
```

**Path Parameters**:
- `org_id` (string, required): Organization ID

**Query Parameters**:
- `start_date` (string, optional): ISO 8601 date (default: 30 days ago)
- `end_date` (string, optional): ISO 8601 date (default: now)
- `user_id` (string, optional): Filter by specific user
- `service_type` (string, optional): Filter by service (llm_inference, image_generation)
- `group_by` (string, optional): Group by user, service, day, week, month

**Response** (`200 OK`):
```json
{
  "total_credits_used": 3456.0,
  "total_requests": 1523,
  "breakdown_by_service": {
    "llm_inference": {
      "credits_used": 3200.0,
      "requests": 1450,
      "avg_cost_per_request": 2.21
    },
    "image_generation": {
      "credits_used": 256.0,
      "requests": 73,
      "avg_cost_per_request": 3.51
    }
  },
  "breakdown_by_user": [
    {
      "user_id": "user_xyz789",
      "user_email": "john@acme.com",
      "credits_used": 2300.0,
      "requests": 980,
      "percentage": 66.6
    }
  ],
  "breakdown_by_day": [
    {
      "date": "2025-11-14",
      "credits_used": 234.0,
      "requests": 103
    }
  ]
}
```

**Error Responses**:
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to view usage

---

### Get Billing History

Historical billing events for an organization.

```http
GET /api/v1/org-billing/{org_id}/history
```

**Path Parameters**:
- `org_id` (string, required): Organization ID

**Query Parameters**:
- `event_type` (string, optional): Filter by event type
- `limit` (number, optional): Results per page (default: 20, max: 100)
- `offset` (number, optional): Pagination offset (default: 0)

**Response** (`200 OK`):
```json
{
  "history": [
    {
      "id": "uuid",
      "event_type": "subscription_created",
      "amount": 49.00,
      "currency": "USD",
      "status": "paid",
      "lago_invoice_id": "inv_lago_123",
      "created_at": "2025-11-01T00:00:00Z"
    },
    {
      "id": "uuid",
      "event_type": "credits_purchased",
      "amount": 100.00,
      "status": "paid",
      "stripe_payment_id": "pi_stripe_456",
      "metadata": {
        "credits": 10000.0
      },
      "created_at": "2025-11-01T00:05:00Z"
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0
}
```

**Event Types**:
- `subscription_created` - New subscription started
- `subscription_upgraded` - Plan upgraded
- `subscription_canceled` - Subscription canceled
- `credits_purchased` - Credits added to pool
- `invoice_paid` - Invoice payment completed
- `invoice_failed` - Payment failed

**Error Responses**:
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to view history

---

## Error Codes

### Standard HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request successful |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid request body or parameters |
| `401` | Unauthorized | Not authenticated (missing or invalid session token) |
| `403` | Forbidden | Not authorized to access resource |
| `404` | Not Found | Resource not found |
| `409` | Conflict | Resource already exists |
| `422` | Unprocessable Entity | Validation failed |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |
| `503` | Service Unavailable | Service temporarily unavailable |

### Error Response Format

```json
{
  "error": {
    "code": "INSUFFICIENT_CREDITS",
    "message": "Organization credit pool has insufficient credits",
    "details": {
      "required": 5000.0,
      "available": 2000.0
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Authentication required |
| `PERMISSION_DENIED` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `ALREADY_EXISTS` | 409 | Resource already exists |
| `INSUFFICIENT_CREDITS` | 400 | Not enough credits in pool |
| `ALLOCATION_LIMIT_EXCEEDED` | 400 | Cannot allocate more than available |
| `SUBSCRIPTION_EXISTS` | 409 | Organization already has subscription |
| `PAYMENT_FAILED` | 422 | Payment processing failed |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |

---

## Rate Limits

### Per-Endpoint Limits

| Endpoint | Method | Limit | Window |
|----------|--------|-------|--------|
| All GET endpoints | GET | 100 requests | 1 minute |
| All POST/PUT endpoints | POST/PUT | 20 requests | 1 minute |
| Create subscription | POST | 5 requests | 1 hour |
| Add credits | POST | 20 requests | 1 minute |
| Allocate credits | POST | 30 requests | 1 minute |
| Usage stats | GET | 60 requests | 1 minute |

### Rate Limit Headers

All responses include rate limit headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1731628800
```

### Exceeded Rate Limit Response

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1731628800

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 45 seconds.",
    "details": {
      "limit": 100,
      "reset_at": "2025-11-15T10:30:00Z"
    }
  }
}
```

---

## Pagination

All list endpoints support pagination:

### Query Parameters

- `limit` (number, optional): Results per page (default varies by endpoint, max 100)
- `offset` (number, optional): Skip N results (default: 0)

### Response Format

```json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

---

## Versioning

API version is specified in the URL path:

- Current: `/api/v1/org-billing`
- Future: `/api/v2/org-billing` (when available)

Breaking changes will result in a new API version.

---

## Testing Endpoints

### Test Environment

Base URL: `http://localhost:8084/api/v1/org-billing`

### Sample curl Commands

```bash
# Create subscription
curl -X POST http://localhost:8084/api/v1/org-billing/subscriptions \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_TOKEN" \
  -d '{
    "org_id": "test-org-001",
    "plan_code": "professional",
    "org_name": "Test Organization",
    "billing_email": "billing@test.com",
    "initial_credits": 5000.0,
    "user_id": "test-user-123"
  }'

# Get credit pool
curl http://localhost:8084/api/v1/org-billing/credits/test-org-001 \
  -H "Cookie: session_token=YOUR_TOKEN"

# Allocate credits
curl -X POST http://localhost:8084/api/v1/org-billing/credits/test-org-001/allocate \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_TOKEN" \
  -d '{
    "user_id": "test-user-123",
    "credits": 2000.0
  }'

# Get usage stats
curl "http://localhost:8084/api/v1/org-billing/credits/test-org-001/usage?group_by=user" \
  -H "Cookie: session_token=YOUR_TOKEN"
```

---

**API Documentation Version**: 1.0.0
**Last Updated**: November 15, 2025
