# UC-Cloud Ops-Center API Schemas

**Version**: 2.1.0
**Total Endpoints**: 310
**Last Updated**: October 25, 2025

---

## Table of Contents

1. [Authentication](#authentication)
2. [Common Schemas](#common-schemas)
3. [User Management](#user-management)
4. [Organization Management](#organization-management)
5. [Billing & Subscriptions](#billing--subscriptions)
6. [LLM Infrastructure](#llm-infrastructure)
7. [Service Management](#service-management)
8. [Analytics & Monitoring](#analytics--monitoring)
9. [Error Responses](#error-responses)

---

## Authentication

All API endpoints require JWT Bearer token authentication via Keycloak SSO.

### Security Scheme

```yaml
securitySchemes:
  BearerAuth:
    type: http
    scheme: bearer
    bearerFormat: JWT
    description: JWT token obtained from Keycloak SSO
```

### Authentication Flow

1. **Login**: Navigate to `https://auth.unicorncommander.ai`
2. **Authenticate**: Login with credentials or OAuth provider (Google, GitHub, Microsoft)
3. **Retrieve Token**: Extract `access_token` from response
4. **Use Token**: Include in all API requests:
   ```
   Authorization: Bearer <access_token>
   ```

### Token Expiration

- **Access Token**: 15 minutes
- **Refresh Token**: 30 days
- **Session Token**: 24 hours (for impersonation)

---

## Common Schemas

### Error Response

```json
{
  "detail": "string",
  "status_code": 400,
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2025-10-25T12:34:56Z"
}
```

**Fields**:
- `detail` (string): Human-readable error message
- `status_code` (integer): HTTP status code
- `error_code` (string): Machine-readable error code
- `timestamp` (string): ISO 8601 timestamp

### Pagination Response

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

**Fields**:
- `items` (array): Page of results
- `total` (integer): Total items across all pages
- `page` (integer): Current page number (1-indexed)
- `page_size` (integer): Items per page
- `total_pages` (integer): Total number of pages

---

## User Management

### User Schema

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "john_doe",
  "firstName": "John",
  "lastName": "Doe",
  "emailVerified": true,
  "enabled": true,
  "createdTimestamp": 1698765432000,
  "attributes": {
    "subscription_tier": ["professional"],
    "subscription_status": ["active"],
    "org_id": ["org_123"],
    "org_name": ["Acme Corp"],
    "org_role": ["member"],
    "api_calls_limit": ["10000"],
    "api_calls_used": ["2543"],
    "api_calls_reset_date": ["2025-11-01"],
    "byok_enabled": ["true"]
  },
  "roles": ["developer", "viewer"],
  "groups": [],
  "requiredActions": []
}
```

**Key Attributes**:
- `subscription_tier`: Subscription level (trial, starter, professional, enterprise)
- `subscription_status`: Account status (active, suspended, cancelled)
- `org_id`: Organization UUID
- `org_name`: Organization name
- `org_role`: Role within organization (owner, billing_admin, member)
- `api_calls_limit`: API call quota per billing period
- `api_calls_used`: API calls consumed in current period
- `api_calls_reset_date`: Date when quota resets
- `byok_enabled`: Bring Your Own Key enabled

### Role Hierarchy

```
admin         → Full system access
  └── moderator     → User & content management
      └── developer     → Service access & API keys
          └── analyst       → Read-only analytics
              └── viewer        → Basic read access
```

### User List Request

**Endpoint**: `GET /api/v1/admin/users`

**Query Parameters**:
```
?search=aaron
&tier=professional
&role=admin
&status=enabled
&org_id=org_123
&created_from=2025-01-01
&created_to=2025-12-31
&last_login_from=2025-10-01
&email_verified=true
&byok_enabled=true
&limit=50
&offset=0
```

**Response**:
```json
{
  "users": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "admin@example.com",
      "username": "aaron",
      "subscription_tier": "professional",
      "subscription_status": "active",
      "roles": ["admin"],
      "created_at": "2025-01-15T08:30:00Z",
      "last_login": "2025-10-25T10:15:23Z",
      "org_id": "org_123",
      "org_name": "Magic Unicorn",
      "api_calls_used": 2543,
      "api_calls_limit": 10000
    }
  ],
  "total": 9,
  "page": 1,
  "page_size": 50,
  "total_pages": 1,
  "filters_applied": {
    "search": "aaron",
    "tier": "professional",
    "role": "admin"
  }
}
```

### Bulk Operations

#### Bulk Import CSV

**Endpoint**: `POST /api/v1/admin/users/bulk/import`

**Request Body**:
```json
{
  "csv_data": "email,first_name,last_name,tier\naaron@example.com,Aaron,Smith,professional\njane@example.com,Jane,Doe,starter",
  "send_welcome_email": true,
  "auto_activate": true
}
```

**Response**:
```json
{
  "success": true,
  "created": 2,
  "failed": 0,
  "errors": [],
  "users_created": [
    {
      "email": "aaron@example.com",
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "tier": "professional"
    },
    {
      "email": "jane@example.com",
      "id": "660f9511-f39c-52e5-b827-557766551111",
      "tier": "starter"
    }
  ]
}
```

### API Key Management

#### Generate API Key

**Endpoint**: `POST /api/v1/admin/users/{user_id}/api-keys`

**Request Body**:
```json
{
  "name": "Production API Key",
  "expires_in_days": 90,
  "scopes": ["llm:read", "llm:write", "billing:read"]
}
```

**Response**:
```json
{
  "id": "key_abc123",
  "key": "uc_sk_1234567890abcdef1234567890abcdef",
  "name": "Production API Key",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-10-25T12:00:00Z",
  "expires_at": "2026-01-23T12:00:00Z",
  "scopes": ["llm:read", "llm:write", "billing:read"],
  "last_used": null
}
```

⚠️ **Important**: The full API key is only shown once during creation. Store securely.

---

## Organization Management

### Organization Schema

```json
{
  "id": "org_123",
  "name": "Magic Unicorn Inc",
  "slug": "magic-unicorn",
  "owner_id": "550e8400-e29b-41d4-a716-446655440000",
  "subscription_tier": "enterprise",
  "member_count": 25,
  "settings": {
    "byok_enabled": true,
    "sso_enforced": false,
    "allow_member_invites": true,
    "api_call_limit": 100000,
    "max_seats": 50
  },
  "created_at": "2025-01-01T00:00:00Z",
  "billing": {
    "lago_customer_id": "cus_abc123",
    "stripe_customer_id": "cus_stripe123",
    "current_period_start": "2025-10-01T00:00:00Z",
    "current_period_end": "2025-11-01T00:00:00Z",
    "api_calls_used": 45230,
    "api_calls_limit": 100000
  }
}
```

### Create Organization

**Endpoint**: `POST /api/v1/org`

**Request Body**:
```json
{
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "plan": "professional",
  "owner_email": "owner@acme.com"
}
```

**Response**:
```json
{
  "id": "org_456",
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "owner_id": "770f9622-g49d-63f6-c938-668877662222",
  "subscription_tier": "professional",
  "member_count": 1,
  "created_at": "2025-10-25T12:34:56Z"
}
```

### Organization Member Roles

```json
{
  "roles": [
    {
      "id": "owner",
      "name": "Owner",
      "description": "Full organization control",
      "permissions": [
        "manage_members",
        "manage_billing",
        "manage_settings",
        "delete_org"
      ]
    },
    {
      "id": "billing_admin",
      "name": "Billing Admin",
      "description": "Billing and subscription management",
      "permissions": [
        "view_billing",
        "update_payment_methods",
        "view_invoices"
      ]
    },
    {
      "id": "member",
      "name": "Member",
      "description": "Standard organization member",
      "permissions": [
        "use_services",
        "view_usage"
      ]
    }
  ]
}
```

---

## Billing & Subscriptions

### Subscription Plans

```json
{
  "plans": [
    {
      "id": "trial",
      "code": "trial",
      "name": "Trial Plan",
      "price": 1.00,
      "interval": "weekly",
      "api_calls_limit": 700,
      "features": [
        "100 API calls per day",
        "Open-WebUI access",
        "Basic AI models",
        "Community support"
      ]
    },
    {
      "id": "starter",
      "code": "starter",
      "name": "Starter Plan",
      "price": 19.00,
      "interval": "monthly",
      "api_calls_limit": 1000,
      "features": [
        "1,000 API calls per month",
        "Open-WebUI + Center-Deep access",
        "All AI models",
        "BYOK support",
        "Email support"
      ]
    },
    {
      "id": "professional",
      "code": "professional",
      "name": "Professional Plan",
      "price": 49.00,
      "interval": "monthly",
      "api_calls_limit": 10000,
      "features": [
        "10,000 API calls per month",
        "All services (Chat, Search, TTS, STT)",
        "Billing dashboard access",
        "Priority support",
        "BYOK support"
      ],
      "most_popular": true
    },
    {
      "id": "enterprise",
      "code": "enterprise",
      "name": "Enterprise Plan",
      "price": 99.00,
      "interval": "monthly",
      "api_calls_limit": null,
      "features": [
        "Unlimited API calls",
        "Team management (5 seats)",
        "Custom integrations",
        "24/7 dedicated support",
        "White-label options"
      ]
    }
  ]
}
```

### Current Subscription

**Endpoint**: `GET /api/v1/subscriptions/current`

**Response**:
```json
{
  "id": "sub_abc123",
  "customer_id": "cus_abc123",
  "plan_code": "professional",
  "status": "active",
  "current_period_start": "2025-10-01T00:00:00Z",
  "current_period_end": "2025-11-01T00:00:00Z",
  "api_calls_used": 2543,
  "api_calls_limit": 10000,
  "usage_percentage": 25.43,
  "billing": {
    "amount": 49.00,
    "currency": "USD",
    "interval": "monthly",
    "next_billing_date": "2025-11-01T00:00:00Z"
  },
  "payment_method": {
    "type": "card",
    "last4": "4242",
    "exp_month": 12,
    "exp_year": 2026,
    "brand": "Visa"
  }
}
```

### Create Subscription

**Endpoint**: `POST /api/v1/subscriptions/create`

**Request Body**:
```json
{
  "plan_code": "professional",
  "payment_method_id": "pm_stripe123",
  "billing_email": "billing@acme.com",
  "org_id": "org_456"
}
```

**Response**:
```json
{
  "subscription_id": "sub_new123",
  "status": "active",
  "plan_code": "professional",
  "next_billing_date": "2025-11-25T00:00:00Z",
  "amount": 49.00,
  "stripe_payment_intent": "pi_abc123"
}
```

### Invoice Schema

```json
{
  "id": "inv_abc123",
  "subscription_id": "sub_abc123",
  "number": "INV-2025-001",
  "status": "paid",
  "amount_due": 49.00,
  "amount_paid": 49.00,
  "currency": "USD",
  "period_start": "2025-10-01T00:00:00Z",
  "period_end": "2025-11-01T00:00:00Z",
  "issued_at": "2025-10-01T00:00:00Z",
  "paid_at": "2025-10-01T12:34:56Z",
  "pdf_url": "https://billing.unicorncommander.ai/invoices/inv_abc123.pdf",
  "line_items": [
    {
      "description": "Professional Plan - October 2025",
      "quantity": 1,
      "unit_price": 49.00,
      "amount": 49.00
    },
    {
      "description": "API Usage Overage (543 calls)",
      "quantity": 543,
      "unit_price": 0.01,
      "amount": 5.43
    }
  ],
  "total": 54.43
}
```

---

## LLM Infrastructure

### Chat Completions

**Endpoint**: `POST /api/v1/llm/chat/completions`

**Request Body** (OpenAI-compatible):
```json
{
  "model": "openai/gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "What is the capital of France?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 150,
  "stream": false,
  "user": "user@example.com"
}
```

**Response**:
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1729857296,
  "model": "openai/gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The capital of France is Paris."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 8,
    "total_tokens": 33,
    "cost": 0.00099,
    "credits_used": 1
  }
}
```

### Available Models

**Endpoint**: `GET /api/v1/llm/models`

**Response**:
```json
{
  "models": [
    {
      "id": "openai/gpt-4",
      "name": "GPT-4",
      "provider": "openai",
      "tier_required": "professional",
      "credits_per_request": 1,
      "max_tokens": 8192,
      "supports_streaming": true,
      "supports_functions": true
    },
    {
      "id": "anthropic/claude-3-opus",
      "name": "Claude 3 Opus",
      "provider": "anthropic",
      "tier_required": "professional",
      "credits_per_request": 2,
      "max_tokens": 200000,
      "supports_streaming": true,
      "supports_functions": false
    },
    {
      "id": "openrouter/meta-llama/llama-3.1-70b",
      "name": "Llama 3.1 70B",
      "provider": "openrouter",
      "tier_required": "starter",
      "credits_per_request": 0.5,
      "max_tokens": 8192,
      "supports_streaming": true,
      "supports_functions": true
    }
  ],
  "total": 100,
  "user_tier": "professional",
  "available_count": 75
}
```

### BYOK (Bring Your Own Key)

**Endpoint**: `POST /api/v1/llm/byok/keys`

**Request Body**:
```json
{
  "provider": "openai",
  "api_key": "sk-abc123...",
  "organization_id": "org-xyz789"
}
```

**Response**:
```json
{
  "provider": "openai",
  "key_preview": "sk-abc...789",
  "created_at": "2025-10-25T12:34:56Z",
  "status": "active"
}
```

---

## Service Management

### Docker Services

**Endpoint**: `GET /api/v1/services`

**Response**:
```json
{
  "services": [
    {
      "id": "ops-center-direct",
      "name": "Ops-Center",
      "image": "ops-center:latest",
      "status": "running",
      "health": "healthy",
      "ports": ["8084:8084"],
      "networks": ["unicorn-network", "web", "uchub-network"],
      "uptime": "15d 4h 23m",
      "memory_usage": 256.5,
      "cpu_usage": 12.3
    },
    {
      "id": "unicorn-postgresql",
      "name": "PostgreSQL",
      "image": "postgres:16",
      "status": "running",
      "health": "healthy",
      "ports": ["5432:5432"],
      "memory_usage": 512.8,
      "cpu_usage": 8.7
    }
  ],
  "total": 12,
  "running": 11,
  "stopped": 1
}
```

### Traefik Routes

**Endpoint**: `GET /api/v1/traefik/routes`

**Response**:
```json
{
  "routes": [
    {
      "name": "ops-center-https",
      "rule": "Host(`unicorncommander.ai`)",
      "service": "ops-center-direct",
      "tls": true,
      "priority": 100,
      "middlewares": ["redirect-https", "gzip-compress"]
    },
    {
      "name": "brigade-https",
      "rule": "Host(`brigade.unicorncommander.ai`)",
      "service": "unicorn-brigade-ui",
      "tls": true,
      "priority": 90
    }
  ],
  "total": 15
}
```

---

## Analytics & Monitoring

### System Metrics

**Endpoint**: `GET /api/v1/system-metrics/current`

**Response**:
```json
{
  "timestamp": "2025-10-25T12:34:56Z",
  "cpu": {
    "usage_percent": 45.2,
    "cores": 16,
    "load_average": [2.5, 2.3, 2.1]
  },
  "memory": {
    "total_gb": 64.0,
    "used_gb": 32.5,
    "available_gb": 31.5,
    "usage_percent": 50.8
  },
  "gpu": {
    "name": "NVIDIA RTX 5090",
    "memory_total_mb": 32768,
    "memory_used_mb": 28672,
    "memory_usage_percent": 87.5,
    "temperature_c": 65,
    "utilization_percent": 92
  },
  "disk": {
    "total_gb": 2000,
    "used_gb": 856,
    "available_gb": 1144,
    "usage_percent": 42.8
  },
  "network": {
    "bytes_sent": 1234567890,
    "bytes_received": 9876543210,
    "connections_active": 127
  }
}
```

### Usage Analytics

**Endpoint**: `GET /api/v1/analytics/usage`

**Query Parameters**: `?start_date=2025-10-01&end_date=2025-10-31&granularity=daily`

**Response**:
```json
{
  "period": {
    "start": "2025-10-01T00:00:00Z",
    "end": "2025-10-31T23:59:59Z",
    "granularity": "daily"
  },
  "data": [
    {
      "date": "2025-10-01",
      "api_calls": 350,
      "unique_users": 25,
      "credits_used": 420,
      "average_response_time_ms": 245
    },
    {
      "date": "2025-10-02",
      "api_calls": 427,
      "unique_users": 28,
      "credits_used": 512,
      "average_response_time_ms": 238
    }
  ],
  "summary": {
    "total_api_calls": 10543,
    "total_unique_users": 89,
    "total_credits_used": 12650,
    "average_response_time_ms": 242
  }
}
```

### Revenue Analytics

**Endpoint**: `GET /api/v1/analytics/revenue`

**Response**:
```json
{
  "current_month": {
    "month": "2025-10",
    "revenue": 12450.00,
    "subscriptions": 254,
    "churn_rate": 3.2,
    "mrr": 12450.00,
    "arr": 149400.00
  },
  "by_plan": [
    {
      "plan": "enterprise",
      "subscribers": 15,
      "revenue": 1485.00,
      "percentage": 11.9
    },
    {
      "plan": "professional",
      "subscribers": 125,
      "revenue": 6125.00,
      "percentage": 49.2
    },
    {
      "plan": "starter",
      "subscribers": 104,
      "revenue": 1976.00,
      "percentage": 15.9
    },
    {
      "plan": "trial",
      "subscribers": 10,
      "revenue": 10.00,
      "percentage": 0.1
    }
  ],
  "growth": {
    "month_over_month": 8.5,
    "quarter_over_quarter": 23.4,
    "year_over_year": 145.2
  }
}
```

---

## Error Responses

### Standard Error Format

All errors follow this format:

```json
{
  "detail": "Human-readable error message",
  "status_code": 400,
  "error_code": "ERROR_TYPE",
  "timestamp": "2025-10-25T12:34:56Z",
  "request_id": "req_abc123"
}
```

### Common Error Codes

| Status | Error Code | Description | Example |
|--------|------------|-------------|---------|
| 400 | `VALIDATION_ERROR` | Invalid request parameters | Missing required field |
| 401 | `UNAUTHORIZED` | Authentication required | No Bearer token provided |
| 403 | `FORBIDDEN` | Insufficient permissions | Non-admin accessing admin endpoint |
| 404 | `NOT_FOUND` | Resource not found | User ID doesn't exist |
| 409 | `CONFLICT` | Resource conflict | Email already registered |
| 422 | `UNPROCESSABLE_ENTITY` | Semantic error | Invalid email format |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests | Tier quota exhausted |
| 500 | `INTERNAL_ERROR` | Server error | Database connection failed |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily down | Maintenance mode |

### Example Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Authentication required. Please log in to access local user management.",
  "status_code": 401,
  "error_code": "UNAUTHORIZED"
}
```

#### 403 Forbidden
```json
{
  "detail": "Admin role required. Contact your system administrator for access.",
  "status_code": 403,
  "error_code": "FORBIDDEN"
}
```

#### 429 Rate Limit Exceeded
```json
{
  "detail": "API call limit exceeded. Upgrade to Professional plan for higher limits.",
  "status_code": 429,
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 3600,
  "current_usage": 1000,
  "limit": 1000,
  "reset_at": "2025-11-01T00:00:00Z"
}
```

---

## API Versioning

### Current Version: 2.1.0

All endpoints are prefixed with `/api/v1/` to support future versioning.

### Version History

- **v2.1.0** (October 2025): Added analytics endpoints, BYOK, bulk operations
- **v2.0.0** (September 2025): Lago billing integration, organization management
- **v1.0.0** (August 2025): Initial release with user management and LLM proxy

### Deprecation Policy

- Deprecated endpoints will be supported for minimum 6 months
- Deprecation warnings included in response headers: `X-API-Deprecated: true`
- Migration guides provided in documentation

---

## Rate Limiting

### Limits by Tier

| Tier | Daily Limit | Burst Limit | Window |
|------|-------------|-------------|--------|
| Trial | 100 requests | 10/minute | 24 hours |
| Starter | 1,000 requests | 50/minute | 30 days |
| Professional | 10,000 requests | 200/minute | 30 days |
| Enterprise | Unlimited | 1000/minute | N/A |

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 7543
X-RateLimit-Reset: 1730419200
X-RateLimit-Tier: professional
```

---

## Webhooks

### Supported Events

- `user.created` - New user registered
- `user.updated` - User profile changed
- `user.deleted` - User account deleted
- `subscription.created` - New subscription started
- `subscription.updated` - Subscription tier changed
- `subscription.cancelled` - Subscription cancelled
- `payment.succeeded` - Payment processed successfully
- `payment.failed` - Payment failed
- `invoice.created` - New invoice generated

### Webhook Payload Example

```json
{
  "event": "subscription.created",
  "timestamp": "2025-10-25T12:34:56Z",
  "data": {
    "subscription_id": "sub_abc123",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "plan": "professional",
    "status": "active"
  },
  "signature": "sha256=abc123..."
}
```

---

## Best Practices

### Authentication
- Always use HTTPS in production
- Store access tokens securely (encrypted)
- Refresh tokens before expiration
- Implement token rotation

### Error Handling
- Check `status_code` for success (2xx)
- Parse `error_code` for programmatic error handling
- Display `detail` to end users
- Log full error response for debugging

### Pagination
- Use `limit` and `offset` parameters
- Check `total_pages` to determine if more data exists
- Default page size: 20 items
- Maximum page size: 100 items

### Performance
- Use caching where appropriate (Redis-backed)
- Implement exponential backoff for retries
- Monitor rate limit headers
- Use streaming for large responses

---

**End of API Schemas Documentation**

For full OpenAPI 3.0 specification, see: [openapi.yaml](./openapi.yaml)
