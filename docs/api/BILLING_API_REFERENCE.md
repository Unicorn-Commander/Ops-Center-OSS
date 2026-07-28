# Billing API Reference

**Version:** 1.0.0
**Base URL:** `https://unicorncommander.ai/api/v1`
**Authentication:** Session-based (Keycloak SSO)

Complete API reference for the Ops-Center billing system. All endpoints require authentication unless otherwise noted.

---

## Table of Contents

- [Authentication](#authentication)
- [Billing Endpoints](#billing-endpoints)
  - [Subscription Plans](#subscription-plans)
  - [Invoices](#invoices)
  - [Billing Cycle](#billing-cycle)
  - [Payment Methods](#payment-methods)
- [Credit System](#credit-system)
  - [Balance](#balance)
  - [Transactions](#transactions)
  - [Allocation](#allocation)
  - [Refunds](#refunds)
- [Dynamic Pricing](#dynamic-pricing)
  - [BYOK Rules](#byok-rules)
  - [Platform Rules](#platform-rules)
  - [Cost Calculation](#cost-calculation)
- [Subscription Management](#subscription-management)
  - [Current Subscription](#current-subscription)
  - [Upgrades](#upgrades)
  - [Downgrades](#downgrades)
  - [Cancellation](#cancellation)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Webhooks](#webhooks)
- [Code Examples](#code-examples)

---

## Authentication

All API requests require authentication via session cookies obtained through Keycloak SSO.

### Login Flow

```http
GET /auth/login
```

Redirects to Keycloak login page with SSO options (Google, GitHub, Microsoft).

### Session Cookie

After successful authentication, a session cookie named `session_token` is set:

```
Set-Cookie: session_token=<JWT>; Path=/; HttpOnly; Secure; SameSite=Lax
```

Include this cookie in all subsequent API requests.

### Logout

```http
POST /auth/logout
```

Invalidates the session token and ends the user session.

---

## Billing Endpoints

### Subscription Plans

#### GET /api/v1/billing/plans

Get all available subscription plans.

**Authentication:** None required (public endpoint)

**Request:**
```http
GET /api/v1/billing/plans HTTP/1.1
Host: unicorncommander.ai
```

**Response:**
```json
{
  "plans": [
    {
      "plan_id": "bbbba413-45de-468d-b03e-f23713684354",
      "plan_code": "trial",
      "name": "Trial",
      "description": "7-day trial with basic features",
      "price_monthly": 1.00,
      "price_yearly": null,
      "interval": "weekly",
      "features": [
        "100 API calls/day",
        "Open-WebUI access",
        "Basic AI models",
        "Community support"
      ],
      "api_calls_limit": 700,
      "is_trial": true
    },
    {
      "plan_id": "02a9058d-e0f6-4e09-9c39-a775d57676d1",
      "plan_code": "starter",
      "name": "Starter",
      "description": "Perfect for individuals and small projects",
      "price_monthly": 19.00,
      "price_yearly": 190.00,
      "interval": "monthly",
      "features": [
        "1,000 API calls/month",
        "All AI models",
        "BYOK support",
        "Email support"
      ],
      "api_calls_limit": 1000,
      "is_trial": false
    },
    {
      "plan_id": "0eefed2d-cdf8-4d0a-b5d0-852dacf9909d",
      "plan_code": "professional",
      "name": "Professional",
      "description": "Most popular - for growing teams",
      "price_monthly": 49.00,
      "price_yearly": 490.00,
      "interval": "monthly",
      "features": [
        "10,000 API calls/month",
        "All services",
        "Priority support",
        "Billing dashboard"
      ],
      "api_calls_limit": 10000,
      "is_trial": false,
      "is_popular": true
    },
    {
      "plan_id": "ee2d9d3d-e985-4166-97ba-2fd6e8cd5b0b",
      "plan_code": "enterprise",
      "name": "Enterprise",
      "description": "For organizations with advanced needs",
      "price_monthly": 99.00,
      "price_yearly": 990.00,
      "interval": "monthly",
      "features": [
        "Unlimited API calls",
        "Team management (5 seats)",
        "Custom integrations",
        "24/7 support",
        "White-label"
      ],
      "api_calls_limit": -1,
      "is_trial": false
    }
  ],
  "currency": "USD",
  "billing_provider": "lago"
}
```

**Status Codes:**
- `200 OK` - Success

---

### Invoices

#### GET /api/v1/billing/invoices

Get invoice history from Lago.

**Authentication:** Required

**Query Parameters:**
- `limit` (integer, optional) - Maximum number of invoices to return (default: 50)

**Request:**
```http
GET /api/v1/billing/invoices?limit=10 HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "invoice_number": "INV-2025-001",
    "amount": 49.00,
    "currency": "USD",
    "status": "paid",
    "issued_date": "2025-01-01",
    "due_date": "2025-01-15",
    "paid_date": "2025-01-02",
    "pdf_url": "https://billing.lago.com/invoices/550e8400.pdf",
    "period_start": "2025-01-01",
    "period_end": "2025-01-31",
    "description": "Invoice for 2025-01-01 - 2025-01-31"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "invoice_number": "INV-2025-002",
    "amount": 49.00,
    "currency": "USD",
    "status": "pending",
    "issued_date": "2025-02-01",
    "due_date": "2025-02-15",
    "paid_date": null,
    "pdf_url": null,
    "period_start": "2025-02-01",
    "period_end": "2025-02-28",
    "description": "Invoice for 2025-02-01 - 2025-02-28"
  }
]
```

**Status Codes:**
- `200 OK` - Success (may return empty array)
- `401 Unauthorized` - Not authenticated
- `500 Internal Server Error` - Server error

---

#### POST /api/v1/billing/download-invoice/{invoice_id}

Generate download URL for invoice PDF.

**Authentication:** Required

**Path Parameters:**
- `invoice_id` (string) - Lago invoice ID

**Request:**
```http
POST /api/v1/billing/download-invoice/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
```

**Response:**
```json
{
  "download_url": "https://billing.lago.com/invoices/550e8400.pdf?token=abc123",
  "invoice_number": "INV-2025-001",
  "expires_in": 3600
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Not authenticated
- `404 Not Found` - Invoice not found or PDF not available
- `500 Internal Server Error` - Server error

---

### Billing Cycle

#### GET /api/v1/billing/cycle

Get current billing cycle information.

**Authentication:** Required

**Request:**
```http
GET /api/v1/billing/cycle HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
```

**Response (With Active Subscription):**
```json
{
  "has_cycle": true,
  "period_start": "2025-01-01T00:00:00Z",
  "period_end": "2025-01-31T23:59:59Z",
  "next_billing_date": "2025-02-01T00:00:00Z",
  "billing_time": "anniversary",
  "status": "active"
}
```

**Response (No Active Subscription):**
```json
{
  "has_cycle": false,
  "message": "No active subscription"
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Not authenticated

---

### Payment Methods

#### GET /api/v1/billing/payment-methods

Get stored payment methods (Stripe).

**Authentication:** Required

**Request:**
```http
GET /api/v1/billing/payment-methods HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
```

**Response:**
```json
{
  "payment_methods": [],
  "default_method": null,
  "message": "Stripe payment methods integration coming soon"
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Not authenticated

---

#### GET /api/v1/billing/summary

Get billing summary with total spend, upcoming charges, etc.

**Authentication:** Required

**Request:**
```http
GET /api/v1/billing/summary HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
```

**Response:**
```json
{
  "total_paid": 588.00,
  "total_pending": 49.00,
  "failed_payments": 0,
  "invoice_count": 13,
  "currency": "USD"
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Not authenticated

---

## Credit System

### Balance

#### GET /api/v1/credits/balance

Get user's current credit balance.

**Authentication:** Required

**Request:**
```http
GET /api/v1/credits/balance HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
```

**Response:**
```json
{
  "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
  "balance": "9850.50",
  "allocated_monthly": "10000.00",
  "bonus_credits": "0.00",
  "free_tier_used": "149.50",
  "reset_date": "2025-02-01T00:00:00Z",
  "last_updated": "2025-01-15T14:30:00Z",
  "tier": "professional",
  "created_at": "2024-12-01T00:00:00Z"
}
```

**Field Descriptions:**
- `balance` - Current credit balance (credits_remaining in DB)
- `allocated_monthly` - Monthly credit allocation (credits_allocated in DB)
- `bonus_credits` - Bonus credits from promotions
- `free_tier_used` - Credits used from free tier allowance
- `reset_date` - When credits will reset (last_reset + 1 month)
- `tier` - Current subscription tier

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Not authenticated
- `500 Internal Server Error` - Server error

---

### Transactions

#### GET /api/v1/credits/transactions

Get credit transaction history.

**Authentication:** Required

**Query Parameters:**
- `limit` (integer, optional) - Maximum transactions (1-500, default: 50)
- `offset` (integer, optional) - Pagination offset (default: 0)
- `transaction_type` (string, optional) - Filter by type (allocated, deducted, refunded, expired)

**Request:**
```http
GET /api/v1/credits/transactions?limit=20&offset=0 HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
```

**Response:**
```json
[
  {
    "id": "tx_abc123",
    "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
    "amount": "-5.50",
    "balance_after": "9850.50",
    "transaction_type": "deducted",
    "service": "openrouter",
    "model": "anthropic/claude-3-5-sonnet",
    "cost_breakdown": "5.50",
    "metadata": {
      "tokens": 10000,
      "prompt_tokens": 8000,
      "completion_tokens": 2000
    },
    "created_at": "2025-01-15T14:30:00Z"
  },
  {
    "id": "tx_def456",
    "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
    "amount": "10000.00",
    "balance_after": "10000.00",
    "transaction_type": "allocated",
    "service": null,
    "model": null,
    "cost_breakdown": null,
    "metadata": {
      "source": "monthly_reset",
      "tier": "professional"
    },
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Not authenticated
- `500 Internal Server Error` - Server error

---

### Allocation

#### POST /api/v1/credits/allocate

Allocate credits to a user (admin only).

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
  "amount": "1000.00",
  "source": "manual",
  "metadata": {
    "reason": "Customer retention bonus",
    "approved_by": "admin@unicorncommander.ai"
  }
}
```

**Field Descriptions:**
- `user_id` - Keycloak user ID
- `amount` - Credit amount to allocate (must be > 0)
- `source` - Source of allocation (tier_upgrade, manual, bonus, etc.)
- `metadata` - Optional additional context

**Request:**
```http
POST /api/v1/credits/allocate HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
Content-Type: application/json

{
  "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
  "amount": "1000.00",
  "source": "manual"
}
```

**Response:**
```json
{
  "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
  "balance": "10850.50",
  "allocated_monthly": "10000.00",
  "bonus_credits": "1000.00",
  "reset_date": "2025-02-01T00:00:00Z",
  "last_updated": "2025-01-15T14:35:00Z",
  "tier": "professional",
  "created_at": "2024-12-01T00:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid amount or parameters
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not an admin
- `500 Internal Server Error` - Server error

---

### Refunds

#### POST /api/v1/credits/refund

Refund credits to user (admin only).

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
  "amount": "50.00",
  "reason": "Service outage on 2025-01-14",
  "metadata": {
    "incident_id": "INC-2025-001"
  }
}
```

**Request:**
```http
POST /api/v1/credits/refund HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
Content-Type: application/json

{
  "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
  "amount": "50.00",
  "reason": "Service outage refund"
}
```

**Response:**
```json
{
  "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
  "balance": "10900.50",
  "allocated_monthly": "10000.00",
  "reset_date": "2025-02-01T00:00:00Z",
  "last_updated": "2025-01-15T14:40:00Z",
  "tier": "professional"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid amount
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not an admin
- `500 Internal Server Error` - Server error

---

## Dynamic Pricing

### BYOK Rules

#### GET /api/v1/pricing/rules/byok

List all BYOK pricing rules.

**Authentication:** Required (Admin role)

**Query Parameters:**
- `provider` (string, optional) - Filter by provider (openrouter, huggingface, etc.)
- `is_active` (boolean, optional) - Filter by active status (default: true)
- `include_inactive` (boolean, optional) - Include inactive rules (default: false)

**Request:**
```http
GET /api/v1/pricing/rules/byok?provider=openrouter&is_active=true HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
```

**Response:**
```json
{
  "rules": [
    {
      "id": "rule_abc123",
      "rule_type": "byok",
      "provider": "openrouter",
      "markup_type": "percentage",
      "markup_value": "0.05",
      "min_charge": "0.001",
      "free_credits_monthly": "5.00",
      "applies_to_tiers": ["starter", "professional", "enterprise"],
      "rule_name": "OpenRouter Standard Markup",
      "description": "5% markup on OpenRouter API costs",
      "priority": 10,
      "is_active": true,
      "created_at": "2024-12-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z",
      "created_by": "admin@unicorncommander.ai",
      "updated_by": "admin@unicorncommander.ai"
    }
  ],
  "total": 1
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not an admin

---

#### POST /api/v1/pricing/rules/byok

Create new BYOK pricing rule.

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "provider": "openrouter",
  "markup_type": "percentage",
  "markup_value": "0.05",
  "min_charge": "0.001",
  "free_credits_monthly": "5.00",
  "applies_to_tiers": ["starter", "professional", "enterprise"],
  "rule_name": "OpenRouter Standard Markup",
  "description": "5% markup on OpenRouter API costs",
  "priority": 10
}
```

**Field Descriptions:**
- `provider` - Provider name (pattern: `^[a-z0-9_*]+$`, use `*` for wildcard)
- `markup_type` - Type of markup (percentage, fixed, none)
- `markup_value` - Markup value (0.0 - 1.0 for percentage, e.g., 0.05 = 5%)
- `min_charge` - Minimum charge per request (0.0001 - 1.0)
- `free_credits_monthly` - Free credits per month for this provider
- `applies_to_tiers` - Array of tier codes
- `priority` - Rule priority (0-100, higher = more priority)

**Request:**
```http
POST /api/v1/pricing/rules/byok HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
Content-Type: application/json

{
  "provider": "huggingface",
  "markup_type": "percentage",
  "markup_value": "0.03",
  "min_charge": "0.001",
  "free_credits_monthly": "10.00",
  "applies_to_tiers": ["professional", "enterprise"],
  "rule_name": "HuggingFace Professional Markup",
  "description": "3% markup for HuggingFace inference",
  "priority": 5
}
```

**Response:**
```json
{
  "id": "rule_def456",
  "rule_type": "byok",
  "provider": "huggingface",
  "markup_type": "percentage",
  "markup_value": "0.03",
  "min_charge": "0.001",
  "free_credits_monthly": "10.00",
  "applies_to_tiers": ["professional", "enterprise"],
  "rule_name": "HuggingFace Professional Markup",
  "description": "3% markup for HuggingFace inference",
  "priority": 5,
  "is_active": true,
  "created_at": "2025-01-15T14:45:00Z",
  "updated_at": "2025-01-15T14:45:00Z",
  "created_by": "admin@unicorncommander.ai"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not an admin
- `500 Internal Server Error` - Server error

---

#### PUT /api/v1/pricing/rules/byok/{rule_id}

Update existing BYOK pricing rule.

**Authentication:** Required (Admin role)

**Path Parameters:**
- `rule_id` (UUID) - Rule ID

**Request Body:**
```json
{
  "markup_value": "0.10",
  "description": "Increased to 10% markup",
  "is_active": true
}
```

**Request:**
```http
PUT /api/v1/pricing/rules/byok/rule_abc123 HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
Content-Type: application/json

{
  "markup_value": "0.10"
}
```

**Response:**
```json
{
  "id": "rule_abc123",
  "rule_type": "byok",
  "provider": "openrouter",
  "markup_type": "percentage",
  "markup_value": "0.10",
  "min_charge": "0.001",
  "free_credits_monthly": "5.00",
  "applies_to_tiers": ["starter", "professional", "enterprise"],
  "rule_name": "OpenRouter Standard Markup",
  "description": "Increased to 10% markup",
  "priority": 10,
  "is_active": true,
  "created_at": "2024-12-01T00:00:00Z",
  "updated_at": "2025-01-15T14:50:00Z",
  "updated_by": "admin@unicorncommander.ai"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - No fields to update
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not an admin
- `404 Not Found` - Rule not found
- `500 Internal Server Error` - Server error

---

#### DELETE /api/v1/pricing/rules/byok/{rule_id}

Delete BYOK pricing rule.

**Authentication:** Required (Admin role)

**Path Parameters:**
- `rule_id` (UUID) - Rule ID

**Request:**
```http
DELETE /api/v1/pricing/rules/byok/rule_abc123 HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
```

**Response:**
```json
{
  "status": "deleted",
  "rule_id": "rule_abc123"
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not an admin
- `404 Not Found` - Rule not found

---

### Cost Calculation

#### POST /api/v1/pricing/calculate/byok

Calculate BYOK cost preview (admin testing).

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "provider": "openrouter",
  "model": "anthropic/claude-3-5-sonnet",
  "tokens_used": 10000,
  "user_tier": "professional"
}
```

**Request:**
```http
POST /api/v1/pricing/calculate/byok HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
Content-Type: application/json

{
  "provider": "openrouter",
  "model": "anthropic/claude-3-5-sonnet",
  "tokens_used": 10000,
  "user_tier": "professional"
}
```

**Response:**
```json
{
  "provider": "openrouter",
  "model": "anthropic/claude-3-5-sonnet",
  "tokens_used": 10000,
  "base_cost": "0.50",
  "markup_percentage": "0.05",
  "markup_amount": "0.025",
  "total_cost": "0.525",
  "free_credits_applied": "0.00",
  "final_charge": "0.525",
  "currency": "USD"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not an admin
- `500 Internal Server Error` - Server error

---

#### POST /api/v1/pricing/calculate/comparison

Calculate side-by-side BYOK vs Platform cost comparison.

**Authentication:** Required

**Request Body:**
```json
{
  "provider": "openrouter",
  "model": "anthropic/claude-3-5-sonnet",
  "tokens_used": 10000,
  "user_tier": "professional"
}
```

**Request:**
```http
POST /api/v1/pricing/calculate/comparison HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
Content-Type: application/json

{
  "provider": "openrouter",
  "model": "anthropic/claude-3-5-sonnet",
  "tokens_used": 10000,
  "user_tier": "professional"
}
```

**Response:**
```json
{
  "provider": "openrouter",
  "model": "anthropic/claude-3-5-sonnet",
  "tokens_used": 10000,
  "byok_cost": {
    "base_cost": "0.50",
    "markup": "0.025",
    "total": "0.525",
    "savings": "60%"
  },
  "platform_cost": {
    "base_cost": "0.50",
    "markup": "0.80",
    "total": "1.30"
  },
  "recommendation": "BYOK - Save $0.775 per request",
  "annual_savings": "$930.00"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Not authenticated
- `500 Internal Server Error` - Server error

---

## Subscription Management

### Current Subscription

#### GET /api/v1/subscriptions/current

Get current subscription details from Lago.

**Authentication:** Required

**Request:**
```http
GET /api/v1/subscriptions/current HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
```

**Response (With Active Subscription):**
```json
{
  "has_subscription": true,
  "tier": "professional",
  "plan_code": "professional_monthly",
  "price": 49.00,
  "status": "active",
  "next_billing_date": "2025-02-01T00:00:00Z",
  "lago_id": "sub_abc123",
  "external_id": "org_e9c5241a",
  "billing_time": "anniversary",
  "plan_name": "Professional"
}
```

**Response (No Active Subscription):**
```json
{
  "has_subscription": false,
  "tier": "trial",
  "price": 0,
  "status": "none",
  "message": "No active Lago subscription found"
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Not authenticated
- `500 Internal Server Error` - Server error

---

### Upgrades

#### POST /api/v1/subscriptions/upgrade

Initiate subscription upgrade flow with Stripe Checkout.

**Authentication:** Required

**Request Body:**
```json
{
  "target_tier": "professional"
}
```

**Request:**
```http
POST /api/v1/subscriptions/upgrade HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
Content-Type: application/json

{
  "target_tier": "professional"
}
```

**Response:**
```json
{
  "success": true,
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_abc123",
  "current_tier": "starter",
  "target_tier": "professional",
  "target_price": 49.00,
  "message": "Redirecting to payment for professional upgrade"
}
```

**Flow:**
1. User clicks upgrade button
2. API creates Stripe checkout session
3. User redirected to Stripe for payment
4. After payment, user redirected back to `/subscription/success`
5. Webhook confirms upgrade in Lago

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Cannot upgrade to same/lower tier, or invalid tier
- `401 Unauthorized` - Not authenticated
- `404 Not Found` - No active subscription or plan not found
- `500 Internal Server Error` - Server error (Stripe not configured, etc.)

---

#### POST /api/v1/subscriptions/confirm-upgrade

Confirm upgrade after successful Stripe payment (webhook callback).

**Authentication:** Required

**Query Parameters:**
- `checkout_session_id` (string) - Stripe checkout session ID

**Request:**
```http
POST /api/v1/subscriptions/confirm-upgrade?checkout_session_id=cs_abc123 HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
```

**Response:**
```json
{
  "success": true,
  "old_tier": "starter",
  "new_tier": "professional",
  "subscription_id": "sub_abc123",
  "message": "Successfully upgraded to professional"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Payment not completed or tier missing
- `401 Unauthorized` - Not authenticated
- `500 Internal Server Error` - Server error

---

#### GET /api/v1/subscriptions/preview-change

Preview subscription change with proration calculation.

**Authentication:** Required

**Query Parameters:**
- `target_tier` (string) - Target tier code

**Request:**
```http
GET /api/v1/subscriptions/preview-change?target_tier=enterprise HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
```

**Response:**
```json
{
  "old_tier": "professional",
  "new_tier": "enterprise",
  "old_price": 49.00,
  "new_price": 99.00,
  "proration_amount": 25.00,
  "proration_credit": 0.00,
  "effective_date": "immediate",
  "is_upgrade": true
}
```

**Field Descriptions:**
- `proration_amount` - Amount to charge for remaining period
- `proration_credit` - Credit for remaining period (if downgrade)
- `effective_date` - When change takes effect (immediate for upgrades)

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Not authenticated
- `404 Not Found` - No active subscription or plan not found
- `500 Internal Server Error` - Server error

---

### Downgrades

#### POST /api/v1/subscriptions/downgrade

Schedule subscription downgrade at end of current billing period.

**Authentication:** Required

**Request Body:**
```json
{
  "target_tier": "starter"
}
```

**Request:**
```http
POST /api/v1/subscriptions/downgrade HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
Content-Type: application/json

{
  "target_tier": "starter"
}
```

**Response:**
```json
{
  "success": true,
  "current_tier": "professional",
  "target_tier": "starter",
  "effective_date": "2025-01-31T23:59:59Z",
  "message": "Downgrade to starter scheduled for end of billing period",
  "current_period_end": "2025-01-31T23:59:59Z",
  "new_price": 19.00
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Cannot downgrade to same/higher tier
- `401 Unauthorized` - Not authenticated
- `404 Not Found` - No active subscription or plan not found
- `500 Internal Server Error` - Server error

---

### Cancellation

#### POST /api/v1/subscriptions/cancel

Cancel current subscription.

**Authentication:** Required

**Request:**
```http
POST /api/v1/subscriptions/cancel HTTP/1.1
Host: unicorncommander.ai
Cookie: session_token=<JWT>
```

**Response:**
```json
{
  "success": true,
  "message": "Subscription canceled successfully",
  "access_until": "2025-01-31T23:59:59Z",
  "tier": "professional"
}
```

**Note:** Access continues until end of billing period.

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Not authenticated
- `404 Not Found` - No active subscription to cancel
- `500 Internal Server Error` - Server error

---

## Error Codes

Standard HTTP status codes with detailed error messages:

### 400 Bad Request

```json
{
  "detail": "target_tier required"
}
```

Common causes:
- Missing required parameters
- Invalid parameter values
- Cannot upgrade/downgrade to invalid tier

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

Causes:
- Missing or invalid session token
- Session expired

**Solution:** Redirect to `/auth/login`

### 403 Forbidden

```json
{
  "detail": "Admin access required"
}
```

Causes:
- User lacks required role (admin)

### 404 Not Found

```json
{
  "detail": "Invoice not found"
}
```

Causes:
- Resource does not exist
- Subscription not found
- Plan not found

### 500 Internal Server Error

```json
{
  "detail": "Failed to fetch subscription: Connection error"
}
```

Causes:
- Server error
- Database connection issues
- External service (Lago, Stripe) unavailable

---

## Rate Limiting

**Limits:**
- 100 requests per minute per user
- 1000 requests per hour per user

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1736960000
```

**429 Too Many Requests:**
```json
{
  "detail": "Rate limit exceeded. Try again in 30 seconds."
}
```

---

## Webhooks

### Lago Webhooks

**Endpoint:** `POST /api/v1/billing/webhooks/lago`

Events handled:
- `subscription.created` - New subscription created
- `subscription.updated` - Subscription modified
- `subscription.terminated` - Subscription canceled
- `invoice.created` - New invoice generated
- `invoice.paid` - Invoice paid
- `invoice.payment_failed` - Payment failed

**Webhook Signature Verification:**
Lago signs webhooks with `X-Lago-Signature` header.

### Stripe Webhooks

**Endpoint:** `POST /api/v1/billing/webhooks/stripe`

Events handled:
- `checkout.session.completed` - Payment completed
- `customer.subscription.created` - New subscription
- `customer.subscription.updated` - Subscription changed
- `customer.subscription.deleted` - Subscription cancelled
- `invoice.paid` - Invoice paid
- `invoice.payment_failed` - Payment failed

**Webhook Secret:** Configured in `.env.stripe`

---

## Code Examples

### Python

#### Get Credit Balance

```python
import requests

BASE_URL = "https://unicorncommander.ai/api/v1"

# Login first to get session cookie
session = requests.Session()
response = session.get(f"{BASE_URL}/auth/login")
# Complete Keycloak SSO flow...

# Get credit balance
response = session.get(f"{BASE_URL}/credits/balance")
balance = response.json()

print(f"Current Balance: {balance['balance']} credits")
print(f"Monthly Allocation: {balance['allocated_monthly']} credits")
print(f"Next Reset: {balance['reset_date']}")
```

#### Get Invoice History

```python
import requests

session = requests.Session()
# Assume authenticated session

response = session.get(
    "https://unicorncommander.ai/api/v1/billing/invoices",
    params={"limit": 10}
)

invoices = response.json()

for invoice in invoices:
    print(f"{invoice['invoice_number']}: ${invoice['amount']} ({invoice['status']})")
```

#### Upgrade Subscription

```python
import requests

session = requests.Session()
# Assume authenticated session

response = session.post(
    "https://unicorncommander.ai/api/v1/subscriptions/upgrade",
    json={"target_tier": "professional"}
)

data = response.json()

if data["success"]:
    print(f"Redirecting to: {data['checkout_url']}")
    # Redirect user to Stripe Checkout
```

---

### JavaScript

#### Get Credit Balance

```javascript
const BASE_URL = "https://unicorncommander.ai/api/v1";

async function getCreditBalance() {
  const response = await fetch(`${BASE_URL}/credits/balance`, {
    credentials: 'include' // Include session cookie
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const balance = await response.json();

  console.log(`Current Balance: ${balance.balance} credits`);
  console.log(`Monthly Allocation: ${balance.allocated_monthly} credits`);

  return balance;
}

getCreditBalance().catch(console.error);
```

#### Get Transaction History

```javascript
async function getTransactions(limit = 50, offset = 0) {
  const url = new URL(`${BASE_URL}/credits/transactions`);
  url.searchParams.set('limit', limit);
  url.searchParams.set('offset', offset);

  const response = await fetch(url, {
    credentials: 'include'
  });

  const transactions = await response.json();

  transactions.forEach(tx => {
    console.log(`${tx.created_at}: ${tx.transaction_type} ${tx.amount} credits`);
  });

  return transactions;
}
```

#### Upgrade with Stripe Checkout

```javascript
async function upgradeSubscription(targetTier) {
  const response = await fetch(`${BASE_URL}/subscriptions/upgrade`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      target_tier: targetTier
    })
  });

  const data = await response.json();

  if (data.success) {
    // Redirect to Stripe Checkout
    window.location.href = data.checkout_url;
  } else {
    alert(`Upgrade failed: ${data.message}`);
  }
}

// Usage
upgradeSubscription('professional');
```

---

### cURL

#### Get Credit Balance

```bash
curl -X GET \
  https://unicorncommander.ai/api/v1/credits/balance \
  -H 'Cookie: session_token=YOUR_SESSION_TOKEN'
```

#### Get Invoices

```bash
curl -X GET \
  'https://unicorncommander.ai/api/v1/billing/invoices?limit=10' \
  -H 'Cookie: session_token=YOUR_SESSION_TOKEN'
```

#### Create BYOK Rule (Admin)

```bash
curl -X POST \
  https://unicorncommander.ai/api/v1/pricing/rules/byok \
  -H 'Cookie: session_token=YOUR_SESSION_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "provider": "openrouter",
    "markup_type": "percentage",
    "markup_value": "0.05",
    "min_charge": "0.001",
    "free_credits_monthly": "5.00",
    "applies_to_tiers": ["starter", "professional", "enterprise"],
    "rule_name": "OpenRouter Standard Markup",
    "priority": 10
  }'
```

#### Upgrade Subscription

```bash
curl -X POST \
  https://unicorncommander.ai/api/v1/subscriptions/upgrade \
  -H 'Cookie: session_token=YOUR_SESSION_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "target_tier": "professional"
  }'
```

---

## Support

**Documentation:** https://unicorncommander.ai/docs
**API Status:** https://status.unicorncommander.ai
**Support Email:** support@magicunicorn.tech

**Report Issues:** https://git.unicorncommander.ai/UnicornCommander/Ops-Center/issues

---

**Last Updated:** November 12, 2025
**API Version:** 1.0.0
