# LoopNet Leads - Ops-Center Organizational Billing Integration Guide

**Version**: 1.0
**Date**: November 12, 2025
**For**: LoopNet Agent Development Team
**From**: Ops-Center Integration Team Lead

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Getting Started](#getting-started)
4. [Authentication & Authorization](#authentication--authorization)
5. [Credit System Explained](#credit-system-explained)
6. [API Endpoint Reference](#api-endpoint-reference)
7. [Credit Deduction Service](#credit-deduction-service)
8. [Usage Attribution](#usage-attribution)
9. [Organization Context](#organization-context)
10. [Code Examples](#code-examples)
11. [Error Handling](#error-handling)
12. [Testing Guide](#testing-guide)
13. [Security Considerations](#security-considerations)
14. [FAQ](#faq)
15. [Support & Resources](#support--resources)

---

## Executive Summary

### What is Organizational Billing?

Ops-Center provides a **credit-based billing system** where:

1. **Organizations** purchase credit pools (shared budgets)
2. **Admins** allocate credits to individual users
3. **Services** (like LoopNet) deduct credits when users perform operations
4. **System** tracks all usage for billing and analytics

### Why Credit-Based?

- **Predictable Costs**: Organizations know their monthly budget
- **Flexible Allocation**: Admins control per-user limits
- **Multi-Org Support**: Users can belong to multiple organizations
- **Detailed Attribution**: Every credit deduction is tracked for reporting

### Integration Checklist

- [ ] Understand credit system architecture
- [ ] Get test organization credentials
- [ ] Implement authentication flow
- [ ] Add credit checking before operations
- [ ] Add credit deduction after operations
- [ ] Implement error handling
- [ ] Add usage attribution metadata
- [ ] Test with sample operations
- [ ] Monitor credit deductions in logs

---

## Architecture Overview

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Ops-Center Billing System                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼───────┐   ┌──────▼──────┐
            │ Organizations │   │    Users     │
            │ (Credit Pools)│   │ (Allocations)│
            └───────┬───────┘   └──────┬───────┘
                    │                   │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Credit Deduction  │
                    │   (Your Service)   │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Usage Attribution │
                    │   (Audit Trail)   │
                    └────────────────────┘
```

### Credit Flow Diagram

```
Organization Pool (10,000 credits)
    │
    ├─→ User A (1,000 allocated)
    │   ├─→ Company Enrichment: -50 credits
    │   ├─→ Contact Lookup: -10 credits
    │   └─→ Remaining: 940 credits
    │
    ├─→ User B (2,000 allocated)
    │   ├─→ Bulk Export: -200 credits
    │   └─→ Remaining: 1,800 credits
    │
    └─→ Unallocated: 7,000 credits
```

### Subscription Plans

| Plan | Monthly Price | Description |
|------|--------------|-------------|
| **Platform** | $50/mo | Managed credits with 1.5x markup |
| **BYOK** | $30/mo | Bring Your Own Keys (passthrough pricing) |
| **Hybrid** | $99/mo | Mix of managed and BYOK credits |

---

## Getting Started

### Prerequisites

1. **Access to Ops-Center API**: `https://api.your-domain.com`
2. **Keycloak Session Token**: Obtained via user login
3. **Organization ID**: User's current organization context
4. **Test Credentials**: Provided by Ops-Center team

### Base URL

```
Production: https://api.your-domain.com
Development: http://localhost:8084
```

### Required Headers

```http
Cookie: session_token=<keycloak_session_token>
Content-Type: application/json
X-Request-ID: <unique_request_id>  # Optional but recommended
```

### Quick Test

```bash
# Test API connectivity
curl -X GET "https://api.your-domain.com/api/v1/org-billing/billing/user" \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN"
```

**Expected Response**:
```json
{
  "user_id": "uuid",
  "user_email": "user@example.com",
  "organizations": [
    {
      "org_id": "uuid",
      "org_name": "My Organization",
      "allocated_credits": 1000,
      "used_credits": 50,
      "remaining_credits": 950
    }
  ]
}
```

---

## Authentication & Authorization

### How Authentication Works

1. User logs in via Keycloak SSO
2. Keycloak creates session and returns `session_token` cookie
3. Ops-Center validates session on every API request
4. User's `user_id` and organization memberships are extracted

### Getting User Session

**Frontend (Browser)**:
```javascript
// Session cookie is automatically included in fetch requests
const response = await fetch('https://api.your-domain.com/api/v1/org-billing/billing/user', {
  method: 'GET',
  credentials: 'include'  // Include cookies
});
const userData = await response.json();
```

**Backend (Server)**:
```python
import requests

# Get session token from user's authenticated request
session_token = request.cookies.get('session_token')

# Make API call to Ops-Center
response = requests.get(
    'https://api.your-domain.com/api/v1/org-billing/billing/user',
    cookies={'session_token': session_token}
)
user_data = response.json()
```

### Extracting Organization Context

**From User Session**:
```python
def get_user_org_context(session_token: str) -> dict:
    """Get user's current organization context"""
    response = requests.get(
        'https://api.your-domain.com/api/v1/org-billing/billing/user',
        cookies={'session_token': session_token}
    )

    if response.status_code != 200:
        raise Exception("User not authenticated")

    data = response.json()

    # User may belong to multiple orgs
    # Application should let user select which org to use
    organizations = data['organizations']

    if not organizations:
        raise Exception("User not a member of any organization")

    # For now, use first org (or implement org selector)
    current_org = organizations[0]

    return {
        'user_id': data['user_id'],
        'org_id': current_org['org_id'],
        'org_name': current_org['org_name'],
        'remaining_credits': current_org['remaining_credits']
    }
```

### Permission Levels

| Role | View Credits | Use Credits | Allocate Credits | Admin Billing |
|------|-------------|------------|-----------------|--------------|
| **Org Member** | Own allocation | ✓ Yes | ✗ No | ✗ No |
| **Org Admin** | All users | ✓ Yes | ✓ Yes | ✓ Yes |
| **System Admin** | All orgs | ✓ Yes | ✓ Yes | ✓ Yes |

---

## Credit System Explained

### What Are Credits?

Credits are **usage units** that represent the cost of operations:

- **1 credit ≈ $0.001** (0.1 cents)
- Credits are purchased by organizations
- Users get allocated a portion of org's credit pool
- Services deduct credits when operations are performed

### Credit Pricing Examples

| Service | Operation | Cost (Credits) | USD Equivalent |
|---------|-----------|---------------|----------------|
| LoopNet | Company Enrichment | 50 | $0.05 |
| LoopNet | Contact Lookup | 10 | $0.01 |
| LoopNet | Bulk Export (100 records) | 500 | $0.50 |
| LoopNet | Intelligence Cache Lookup | 2 | $0.002 |
| LLM | GPT-4 Turbo (1K tokens) | 30 | $0.03 |
| LLM | Claude 3 Sonnet (1K tokens) | 15 | $0.015 |
| Image | DALL-E 3 (1024x1024) | 48 | $0.048 |

### Credit Lifecycle

```
1. Organization purchases credits
   └─→ Credits added to org pool

2. Admin allocates credits to users
   └─→ User gets their allocation (e.g., 1,000 credits)

3. User performs operation (e.g., company enrichment)
   └─→ Service checks if user has credits
   └─→ Operation executes
   └─→ Service deducts credits from user allocation

4. Usage is tracked
   └─→ Attribution record created
   └─→ Visible in analytics dashboards
```

### Credit Resets

Users can have automatic credit resets:

- **Daily**: Credits reset every 24 hours
- **Weekly**: Credits reset every 7 days
- **Monthly**: Credits reset every 30 days
- **Never**: One-time allocation

**Example**: User allocated 1,000 credits with monthly reset
- Day 1: Uses 500 credits (500 remaining)
- Day 15: Uses 300 credits (200 remaining)
- Day 30: Reset triggered → Back to 1,000 credits

---

## API Endpoint Reference

### Base Path

All organizational billing endpoints are under:
```
/api/v1/org-billing
```

### Endpoint Categories

1. **Subscription Management** (5 endpoints)
2. **Credit Management** (6 endpoints)
3. **Billing Queries** (3 endpoints)
4. **Organization Management** (3 endpoints)

---

### 1. Subscription Management Endpoints

#### 1.1 Create Organization Subscription

**Endpoint**: `POST /api/v1/org-billing/subscriptions`

**Required Role**: Org Admin or System Admin

**Request Body**:
```json
{
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "subscription_plan": "platform",
  "monthly_price": 50.00,
  "billing_cycle": "monthly",
  "trial_days": 7
}
```

**Response**:
```json
{
  "id": "sub_uuid",
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "org_name": "Magic Unicorn Inc",
  "subscription_plan": "platform",
  "monthly_price": 50.00,
  "billing_cycle": "monthly",
  "status": "trialing",
  "trial_ends_at": "2025-11-19T00:00:00Z",
  "current_period_start": "2025-11-12T00:00:00Z",
  "current_period_end": "2025-12-12T00:00:00Z",
  "created_at": "2025-11-12T00:00:00Z"
}
```

**cURL Example**:
```bash
curl -X POST "https://api.your-domain.com/api/v1/org-billing/subscriptions" \
  -H "Cookie: session_token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "550e8400-e29b-41d4-a716-446655440000",
    "subscription_plan": "platform",
    "monthly_price": 50.00,
    "billing_cycle": "monthly",
    "trial_days": 7
  }'
```

---

#### 1.2 Get Organization Subscription

**Endpoint**: `GET /api/v1/org-billing/subscriptions/{org_id}`

**Required Role**: Org Member or System Admin

**Response**:
```json
{
  "id": "sub_uuid",
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "org_name": "Magic Unicorn Inc",
  "subscription_plan": "platform",
  "monthly_price": 50.00,
  "status": "active"
}
```

**cURL Example**:
```bash
curl -X GET "https://api.your-domain.com/api/v1/org-billing/subscriptions/550e8400-e29b-41d4-a716-446655440000" \
  -H "Cookie: session_token=YOUR_TOKEN"
```

---

#### 1.3 Upgrade Organization Subscription

**Endpoint**: `PUT /api/v1/org-billing/subscriptions/{org_id}/upgrade?new_plan=hybrid`

**Required Role**: Org Admin or System Admin

**Query Parameters**:
- `new_plan`: New plan type (`platform`, `byok`, `hybrid`)

**Response**:
```json
{
  "success": true,
  "message": "Subscription upgraded to hybrid",
  "old_plan": "platform",
  "new_plan": "hybrid",
  "old_price": 50.00,
  "new_price": 99.00
}
```

**cURL Example**:
```bash
curl -X PUT "https://api.your-domain.com/api/v1/org-billing/subscriptions/550e8400-e29b-41d4-a716-446655440000/upgrade?new_plan=hybrid" \
  -H "Cookie: session_token=YOUR_TOKEN"
```

---

### 2. Credit Management Endpoints

#### 2.1 Get Organization Credit Pool

**Endpoint**: `GET /api/v1/org-billing/credits/{org_id}`

**Required Role**: Org Member or System Admin

**Response**:
```json
{
  "id": "pool_uuid",
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "org_name": "Magic Unicorn Inc",
  "total_credits": 10000,
  "allocated_credits": 3000,
  "used_credits": 450,
  "available_credits": 7000,
  "monthly_refresh_amount": 10000,
  "last_refresh_date": "2025-11-01T00:00:00Z",
  "next_refresh_date": "2025-12-01T00:00:00Z",
  "allow_overage": false,
  "overage_limit": 0,
  "lifetime_purchased_credits": 50000,
  "lifetime_spent_amount": 500.00
}
```

**What This Means**:
- Org has 10,000 total credits
- 3,000 allocated to users
- 450 used so far
- 7,000 still available for allocation
- Auto-refreshes monthly

---

#### 2.2 Add Credits to Pool

**Endpoint**: `POST /api/v1/org-billing/credits/{org_id}/add?credits=5000&purchase_amount=50.00`

**Required Role**: Org Admin or System Admin

**Query Parameters**:
- `credits` (required): Number of credits to add
- `purchase_amount` (optional): Purchase cost in USD

**Response**:
```json
{
  "success": true,
  "message": "Added 5000 credits to pool",
  "total_credits": 15000,
  "available_credits": 12000
}
```

**cURL Example**:
```bash
curl -X POST "https://api.your-domain.com/api/v1/org-billing/credits/550e8400-e29b-41d4-a716-446655440000/add?credits=5000&purchase_amount=50.00" \
  -H "Cookie: session_token=YOUR_TOKEN"
```

---

#### 2.3 Allocate Credits to User

**Endpoint**: `POST /api/v1/org-billing/credits/{org_id}/allocate`

**Required Role**: Org Admin or System Admin

**Request Body**:
```json
{
  "user_id": "user_uuid",
  "allocated_credits": 1000,
  "reset_period": "monthly",
  "notes": "Monthly allocation for Q4"
}
```

**Response**:
```json
{
  "id": "allocation_uuid",
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_uuid",
  "user_email": "user@example.com",
  "user_name": "John Doe",
  "allocated_credits": 1000,
  "used_credits": 0,
  "remaining_credits": 1000,
  "reset_period": "monthly",
  "last_reset_date": "2025-11-12T00:00:00Z",
  "next_reset_date": "2025-12-12T00:00:00Z",
  "is_active": true,
  "created_at": "2025-11-12T00:00:00Z"
}
```

**cURL Example**:
```bash
curl -X POST "https://api.your-domain.com/api/v1/org-billing/credits/550e8400-e29b-41d4-a716-446655440000/allocate" \
  -H "Cookie: session_token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_uuid",
    "allocated_credits": 1000,
    "reset_period": "monthly",
    "notes": "Monthly allocation for Q4"
  }'
```

---

#### 2.4 Get User Credit Allocation

**Endpoint**: `GET /api/v1/org-billing/credits/{org_id}/allocations`

**Required Role**: Org Admin or System Admin

**Response**:
```json
[
  {
    "id": "allocation_uuid_1",
    "org_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user_uuid_1",
    "allocated_credits": 1000,
    "used_credits": 250,
    "remaining_credits": 750,
    "reset_period": "monthly"
  },
  {
    "id": "allocation_uuid_2",
    "org_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user_uuid_2",
    "allocated_credits": 2000,
    "used_credits": 500,
    "remaining_credits": 1500,
    "reset_period": "monthly"
  }
]
```

---

#### 2.5 Get Organization Credit Usage

**Endpoint**: `GET /api/v1/org-billing/credits/{org_id}/usage?days=30`

**Required Role**: Org Member or System Admin

**Query Parameters**:
- `days` (optional): Number of days to analyze (default: 30, max: 365)

**Response**:
```json
{
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_credits_used": 2500,
  "user_count": 5,
  "service_breakdown": {
    "company_enrichment": 1500,
    "contact_lookup": 500,
    "bulk_export": 400,
    "intelligence_cache": 100
  },
  "top_users": [
    {
      "user_id": "user_uuid_1",
      "total_credits": 1200,
      "request_count": 150
    },
    {
      "user_id": "user_uuid_2",
      "total_credits": 800,
      "request_count": 80
    }
  ],
  "date_range_start": "2025-10-13T00:00:00Z",
  "date_range_end": "2025-11-12T00:00:00Z"
}
```

---

### 3. Billing Query Endpoints

#### 3.1 User Billing Dashboard

**Endpoint**: `GET /api/v1/org-billing/billing/user`

**Required Role**: Any authenticated user

**Purpose**: Shows all organizations user belongs to with their credit status

**Response**:
```json
{
  "user_id": "user_uuid",
  "user_email": "user@example.com",
  "organizations": [
    {
      "org_id": "org_uuid_1",
      "org_name": "Magic Unicorn Inc",
      "role": "member",
      "subscription_plan": "platform",
      "monthly_price": 50.00,
      "allocated_credits": 1000,
      "used_credits": 250,
      "remaining_credits": 750
    },
    {
      "org_id": "org_uuid_2",
      "org_name": "Startup Co",
      "role": "admin",
      "subscription_plan": "byok",
      "monthly_price": 30.00,
      "allocated_credits": 2000,
      "used_credits": 100,
      "remaining_credits": 1900
    }
  ],
  "total_usage_last_30_days": {
    "total_credits_used": 350,
    "org_count": 2,
    "request_count": 45
  }
}
```

**Use Case**: Display user's credit status across all organizations

---

#### 3.2 Organization Admin Billing Screen

**Endpoint**: `GET /api/v1/org-billing/billing/org/{org_id}`

**Required Role**: Org Admin or System Admin

**Purpose**: Organization admin billing control panel

**Response**:
```json
{
  "organization": {
    "id": "org_uuid",
    "name": "magic-unicorn-inc",
    "display_name": "Magic Unicorn Inc",
    "max_seats": 50,
    "status": "active"
  },
  "subscription": {
    "plan": "platform",
    "monthly_price": 50.00,
    "status": "active",
    "current_period_end": "2025-12-12T00:00:00Z"
  },
  "credit_pool": {
    "total_credits": 10000,
    "allocated_credits": 3000,
    "used_credits": 450,
    "available_credits": 7000,
    "monthly_refresh_amount": 10000
  },
  "user_allocations": [
    {
      "user_id": "user_uuid_1",
      "allocated_credits": 1000,
      "used_credits": 250,
      "remaining_credits": 750,
      "reset_period": "monthly"
    }
  ],
  "usage_stats_30_days": {
    "total_credits_used": 2500,
    "active_users": 5,
    "total_requests": 320
  }
}
```

**Use Case**: Admin manages organization billing, allocates credits to users

---

#### 3.3 System Admin Billing Overview

**Endpoint**: `GET /api/v1/org-billing/billing/system`

**Required Role**: System Admin

**Purpose**: Platform-wide billing analytics

**Response**:
```json
{
  "organizations": [
    {
      "org_id": "org_uuid_1",
      "org_name": "Magic Unicorn Inc",
      "subscription_plan": "platform",
      "monthly_price": 50.00,
      "total_credits": 10000,
      "used_credits": 2500,
      "member_count": 10,
      "lifetime_spent": 500.00
    }
  ],
  "revenue_metrics": {
    "total_mrr": 5000.00,
    "total_arr": 60000.00,
    "active_subscriptions": 100
  },
  "subscription_distribution": [
    {
      "plan": "platform",
      "count": 60,
      "mrr": 3000.00
    },
    {
      "plan": "byok",
      "count": 30,
      "mrr": 900.00
    },
    {
      "plan": "hybrid",
      "count": 10,
      "mrr": 990.00
    }
  ]
}
```

---

## Credit Deduction Service

### When to Deduct Credits

Credits should be deducted **after** an operation successfully completes:

1. **Check** if user has sufficient credits (optional, for UX)
2. **Execute** the operation (company enrichment, contact lookup, etc.)
3. **Deduct** credits if operation succeeded
4. **Record** usage attribution for analytics

### Using the Database Function Directly

The credit deduction happens via PostgreSQL stored function:

```sql
SELECT deduct_credits(
    p_org_id := 'org_uuid',
    p_user_id := 'user_uuid',
    p_credits_used := 50,
    p_service_type := 'company_enrichment',
    p_service_name := 'LoopNet Company Enrichment v2',
    p_request_id := 'req_abc123',
    p_request_metadata := '{"property_id": "123", "enrichment_level": "full"}'::jsonb
);
```

### Python Integration Example

```python
import asyncpg
from typing import Dict, Optional
import json

class CreditDeductionService:
    """Service for deducting credits from user allocations"""

    def __init__(self, db_connection_string: str):
        self.db_connection = db_connection_string

    async def check_sufficient_credits(
        self,
        org_id: str,
        user_id: str,
        credits_needed: int
    ) -> bool:
        """Check if user has enough credits before operation"""
        conn = await asyncpg.connect(self.db_connection)
        try:
            result = await conn.fetchval(
                "SELECT has_sufficient_credits($1, $2, $3)",
                org_id, user_id, credits_needed
            )
            return result
        finally:
            await conn.close()

    async def deduct_credits(
        self,
        org_id: str,
        user_id: str,
        credits_used: int,
        service_type: str,
        service_name: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Deduct credits from user allocation and record usage

        Args:
            org_id: Organization UUID
            user_id: User UUID (Keycloak sub)
            credits_used: Number of credits to deduct
            service_type: Service category (company_enrichment, contact_lookup, etc.)
            service_name: Specific operation name
            request_id: Unique request ID for tracking
            metadata: Additional context (JSON)

        Returns:
            True if deduction succeeded

        Raises:
            Exception: If insufficient credits or allocation not found
        """
        conn = await asyncpg.connect(self.db_connection)
        try:
            # Convert metadata dict to JSON
            metadata_json = json.dumps(metadata) if metadata else None

            # Call stored function
            await conn.execute(
                "SELECT deduct_credits($1, $2, $3, $4, $5, $6, $7)",
                org_id,
                user_id,
                credits_used,
                service_type,
                service_name,
                request_id,
                metadata_json
            )

            return True

        except asyncpg.exceptions.RaiseException as e:
            # Database function raised exception (insufficient credits)
            raise Exception(f"Credit deduction failed: {str(e)}")

        finally:
            await conn.close()


# Usage Example
async def enrich_company(org_id: str, user_id: str, company_id: str):
    """Example: Enrich company data with credit deduction"""

    credit_service = CreditDeductionService("postgresql://unicorn:password@localhost/unicorn_db")

    # 1. Check if user has sufficient credits (optional, for better UX)
    has_credits = await credit_service.check_sufficient_credits(
        org_id=org_id,
        user_id=user_id,
        credits_needed=50
    )

    if not has_credits:
        raise Exception("Insufficient credits. Please contact your organization admin.")

    # 2. Perform the actual operation
    try:
        enrichment_data = await perform_company_enrichment(company_id)

        # 3. Deduct credits AFTER successful operation
        await credit_service.deduct_credits(
            org_id=org_id,
            user_id=user_id,
            credits_used=50,
            service_type="company_enrichment",
            service_name="LoopNet Company Enrichment v2",
            request_id=f"req_{company_id}_{int(time.time())}",
            metadata={
                "company_id": company_id,
                "enrichment_fields": ["financials", "contacts", "properties"],
                "data_sources": ["loopnet", "costar", "public_records"]
            }
        )

        return enrichment_data

    except Exception as e:
        # Operation failed - DO NOT deduct credits
        raise Exception(f"Enrichment failed: {str(e)}")
```

### FastAPI Endpoint Integration

```python
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/loopnet")

class CompanyEnrichmentRequest(BaseModel):
    company_id: str
    enrichment_level: str = "standard"

@router.post("/company/enrich")
async def enrich_company_endpoint(
    request: Request,
    enrichment_request: CompanyEnrichmentRequest
):
    """
    Enrich company data (deducts credits)

    Cost: 50 credits for standard, 100 credits for full
    """
    # Get user session
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get user's org context from Ops-Center
    user_context = await get_user_org_context(session_token)
    org_id = user_context['org_id']
    user_id = user_context['user_id']

    # Determine credit cost
    credit_cost = 100 if enrichment_request.enrichment_level == "full" else 50

    # Initialize credit service
    credit_service = CreditDeductionService(
        "postgresql://unicorn:password@unicorn-postgresql/unicorn_db"
    )

    # Check credits (optional UX improvement)
    has_credits = await credit_service.check_sufficient_credits(
        org_id, user_id, credit_cost
    )

    if not has_credits:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail=f"Insufficient credits. Need {credit_cost}, contact org admin."
        )

    # Perform enrichment
    try:
        enrichment_data = await perform_company_enrichment(
            enrichment_request.company_id,
            enrichment_request.enrichment_level
        )

        # Deduct credits AFTER success
        await credit_service.deduct_credits(
            org_id=org_id,
            user_id=user_id,
            credits_used=credit_cost,
            service_type="company_enrichment",
            service_name=f"LoopNet Company Enrichment ({enrichment_request.enrichment_level})",
            request_id=request.headers.get("X-Request-ID"),
            metadata={
                "company_id": enrichment_request.company_id,
                "enrichment_level": enrichment_request.enrichment_level
            }
        )

        return {
            "success": True,
            "company_id": enrichment_request.company_id,
            "enrichment_data": enrichment_data,
            "credits_used": credit_cost
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Usage Attribution

### Service Name Taxonomy

Use consistent service names for analytics:

| Service Type | Description | Example Service Names |
|-------------|-------------|---------------------|
| `company_enrichment` | Enrich company data | `LoopNet Company Enrichment v2`, `LoopNet Property Data`, `LoopNet Financial Analysis` |
| `contact_lookup` | Find contact information | `LoopNet Contact Finder`, `LoopNet Email Lookup`, `LoopNet Phone Verification` |
| `bulk_export` | Export data in bulk | `LoopNet Bulk Company Export`, `LoopNet CSV Download` |
| `intelligence_cache_lookup` | Use shared intelligence | `LoopNet Cached Company Data`, `LoopNet Historical Lookup` |
| `property_search` | Search properties | `LoopNet Property Search`, `LoopNet Market Analysis` |
| `valuation` | Property valuations | `LoopNet Property Valuation`, `LoopNet Comp Analysis` |

### Metadata Structure

Include these fields in `request_metadata` JSON:

```json
{
  "operation": "company_enrichment",
  "company_id": "comp_12345",
  "property_id": "prop_67890",
  "enrichment_fields": ["financials", "contacts", "properties"],
  "data_sources": ["loopnet", "costar", "public_records"],
  "enrichment_level": "full",
  "record_count": 1,
  "processing_time_ms": 1250,
  "cache_hit": false,
  "api_version": "v2"
}
```

### Attribution Record Structure

When you call `deduct_credits()`, a record is created in `credit_usage_attribution`:

```sql
-- Attribution record example
INSERT INTO credit_usage_attribution (
    id,
    org_id,
    user_id,
    allocation_id,
    credits_used,
    service_type,
    service_name,
    api_cost,
    markup_applied,
    total_cost,
    request_id,
    request_metadata,
    created_at
) VALUES (
    'uuid',
    'org_uuid',
    'user_uuid',
    'allocation_uuid',
    50,
    'company_enrichment',
    'LoopNet Company Enrichment v2',
    0.04,  -- Actual API cost
    0.02,  -- Markup (1.5x on Platform plan)
    0.06,  -- Total cost
    'req_abc123',
    '{"company_id": "comp_12345", "enrichment_level": "full"}'::jsonb,
    CURRENT_TIMESTAMP
);
```

### Analytics Queries

**Top Services by Usage**:
```sql
SELECT
    service_type,
    service_name,
    SUM(credits_used) as total_credits,
    COUNT(*) as request_count,
    AVG(credits_used) as avg_credits_per_request
FROM credit_usage_attribution
WHERE org_id = 'org_uuid'
  AND created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY service_type, service_name
ORDER BY total_credits DESC;
```

**User Activity Report**:
```sql
SELECT
    user_id,
    service_type,
    COUNT(*) as request_count,
    SUM(credits_used) as total_credits,
    MAX(created_at) as last_activity
FROM credit_usage_attribution
WHERE org_id = 'org_uuid'
  AND created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
GROUP BY user_id, service_type
ORDER BY total_credits DESC;
```

---

## Organization Context

### Getting Organization ID

Users may belong to multiple organizations. Your application should:

1. **Fetch** all organizations user is a member of
2. **Display** organization selector (if multiple)
3. **Store** selected org_id in session/context
4. **Use** that org_id for all credit operations

### Multi-Org Support Example

```python
from typing import List, Optional

class OrganizationContext:
    """Manage user's organization context"""

    def __init__(self, session_token: str):
        self.session_token = session_token
        self.organizations = []
        self.current_org_id = None

    async def load_organizations(self):
        """Load all organizations user belongs to"""
        response = requests.get(
            'https://api.your-domain.com/api/v1/org-billing/billing/user',
            cookies={'session_token': self.session_token}
        )

        if response.status_code != 200:
            raise Exception("Failed to load organizations")

        data = response.json()
        self.organizations = data['organizations']

        # Auto-select first org if only one
        if len(self.organizations) == 1:
            self.current_org_id = self.organizations[0]['org_id']

        return self.organizations

    def set_current_organization(self, org_id: str):
        """Set which organization to use for operations"""
        org = next((o for o in self.organizations if o['org_id'] == org_id), None)
        if not org:
            raise Exception(f"User not a member of organization {org_id}")

        self.current_org_id = org_id

    def get_current_org(self) -> Optional[dict]:
        """Get currently selected organization"""
        if not self.current_org_id:
            return None

        return next(
            (o for o in self.organizations if o['org_id'] == self.current_org_id),
            None
        )

    def get_remaining_credits(self) -> int:
        """Get remaining credits for current org"""
        org = self.get_current_org()
        if not org:
            return 0

        return org.get('remaining_credits', 0)


# Usage in your application
async def initialize_user_context(session_token: str) -> OrganizationContext:
    """Initialize organization context for user"""
    context = OrganizationContext(session_token)

    # Load all orgs
    orgs = await context.load_organizations()

    # If multiple orgs, let user select
    if len(orgs) > 1:
        # Display org selector UI
        # User selects org_id
        selected_org_id = await display_org_selector(orgs)
        context.set_current_organization(selected_org_id)

    return context
```

### Verifying Organization Membership

Before operations, verify user is still a member:

```python
async def verify_org_membership(org_id: str, user_id: str) -> bool:
    """Check if user is member of organization"""
    conn = await asyncpg.connect(DB_CONNECTION)
    try:
        result = await conn.fetchval(
            "SELECT 1 FROM organization_members WHERE org_id = $1 AND user_id = $2",
            org_id, user_id
        )
        return result is not None
    finally:
        await conn.close()
```

---

## Code Examples

### Example 1: Simple Credit Check

```python
import asyncpg

async def can_user_afford_operation(
    org_id: str,
    user_id: str,
    credit_cost: int
) -> tuple[bool, str]:
    """
    Check if user can afford operation

    Returns: (can_afford, message)
    """
    conn = await asyncpg.connect("postgresql://unicorn:password@localhost/unicorn_db")
    try:
        has_credits = await conn.fetchval(
            "SELECT has_sufficient_credits($1, $2, $3)",
            org_id, user_id, credit_cost
        )

        if has_credits:
            return (True, "Sufficient credits")

        # Get remaining credits for better error message
        remaining = await conn.fetchval(
            """
            SELECT remaining_credits
            FROM user_credit_allocations
            WHERE org_id = $1 AND user_id = $2 AND is_active = TRUE
            """,
            org_id, user_id
        )

        if remaining is None:
            return (False, "No credit allocation found. Contact your organization admin.")

        return (False, f"Insufficient credits. Need {credit_cost}, have {remaining}.")

    finally:
        await conn.close()


# Usage
can_afford, message = await can_user_afford_operation(
    org_id="550e8400-e29b-41d4-a716-446655440000",
    user_id="user_uuid",
    credit_cost=50
)

if not can_afford:
    print(f"Operation blocked: {message}")
```

---

### Example 2: Company Enrichment with Credits

```python
import asyncpg
import uuid
from datetime import datetime

async def enrich_company_with_credits(
    org_id: str,
    user_id: str,
    company_id: str,
    enrichment_level: str = "standard"
) -> dict:
    """
    Enrich company data and deduct credits

    Cost:
    - standard: 50 credits
    - full: 100 credits
    """
    # Determine cost
    credit_cost = 100 if enrichment_level == "full" else 50

    # Generate request ID
    request_id = f"req_{company_id}_{uuid.uuid4().hex[:8]}"

    # Database connection
    conn = await asyncpg.connect("postgresql://unicorn:password@localhost/unicorn_db")

    try:
        # 1. Check sufficient credits
        has_credits = await conn.fetchval(
            "SELECT has_sufficient_credits($1, $2, $3)",
            org_id, user_id, credit_cost
        )

        if not has_credits:
            raise Exception("Insufficient credits for enrichment")

        # 2. Perform enrichment (your business logic)
        start_time = datetime.now()
        enrichment_data = await your_enrichment_api(company_id, enrichment_level)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # 3. Deduct credits
        metadata = {
            "company_id": company_id,
            "enrichment_level": enrichment_level,
            "fields_enriched": ["financials", "contacts", "properties"],
            "data_sources": ["loopnet", "costar"],
            "processing_time_ms": processing_time,
            "cache_hit": False
        }

        await conn.execute(
            "SELECT deduct_credits($1, $2, $3, $4, $5, $6, $7::jsonb)",
            org_id,
            user_id,
            credit_cost,
            "company_enrichment",
            f"LoopNet Company Enrichment ({enrichment_level})",
            request_id,
            json.dumps(metadata)
        )

        return {
            "success": True,
            "request_id": request_id,
            "credits_used": credit_cost,
            "enrichment_data": enrichment_data
        }

    except asyncpg.exceptions.RaiseException as e:
        # Database error (insufficient credits, no allocation)
        raise Exception(f"Credit deduction failed: {str(e)}")

    except Exception as e:
        # Business logic error - don't deduct credits
        raise Exception(f"Enrichment failed: {str(e)}")

    finally:
        await conn.close()
```

---

### Example 3: Bulk Operations

```python
async def bulk_export_companies(
    org_id: str,
    user_id: str,
    company_ids: list[str],
    export_format: str = "csv"
) -> dict:
    """
    Export multiple companies (credits per record)

    Cost: 5 credits per company
    """
    record_count = len(company_ids)
    total_credits = record_count * 5

    conn = await asyncpg.connect("postgresql://unicorn:password@localhost/unicorn_db")

    try:
        # Check credits
        has_credits = await conn.fetchval(
            "SELECT has_sufficient_credits($1, $2, $3)",
            org_id, user_id, total_credits
        )

        if not has_credits:
            raise Exception(f"Insufficient credits. Need {total_credits} for {record_count} records.")

        # Perform export
        export_data = await your_bulk_export_api(company_ids, export_format)

        # Deduct credits
        metadata = {
            "record_count": record_count,
            "export_format": export_format,
            "company_ids": company_ids[:10],  # Store sample
            "credits_per_record": 5
        }

        await conn.execute(
            "SELECT deduct_credits($1, $2, $3, $4, $5, $6, $7::jsonb)",
            org_id,
            user_id,
            total_credits,
            "bulk_export",
            f"LoopNet Bulk Company Export ({export_format.upper()})",
            f"req_bulk_{uuid.uuid4().hex[:8]}",
            json.dumps(metadata)
        )

        return {
            "success": True,
            "records_exported": record_count,
            "credits_used": total_credits,
            "export_url": export_data['download_url']
        }

    finally:
        await conn.close()
```

---

### Example 4: Intelligence Cache Lookup (Low Cost)

```python
async def lookup_cached_intelligence(
    org_id: str,
    user_id: str,
    company_id: str
) -> dict:
    """
    Look up company in shared intelligence cache

    Cost: 2 credits (much cheaper than enrichment)
    """
    credit_cost = 2

    conn = await asyncpg.connect("postgresql://unicorn:password@localhost/unicorn_db")

    try:
        # Check cache first
        cached_data = await your_cache_lookup(company_id)

        if not cached_data:
            return {
                "success": False,
                "message": "No cached data available",
                "credits_used": 0
            }

        # Deduct credits for cache hit
        metadata = {
            "company_id": company_id,
            "cache_age_hours": cached_data['age_hours'],
            "cache_source": "shared_intelligence"
        }

        await conn.execute(
            "SELECT deduct_credits($1, $2, $3, $4, $5, $6, $7::jsonb)",
            org_id,
            user_id,
            credit_cost,
            "intelligence_cache_lookup",
            "LoopNet Cached Company Data",
            f"req_cache_{company_id}",
            json.dumps(metadata)
        )

        return {
            "success": True,
            "credits_used": credit_cost,
            "cache_hit": True,
            "data": cached_data
        }

    finally:
        await conn.close()
```

---

## Error Handling

### Common Error Scenarios

#### 1. Insufficient Credits

```python
try:
    await deduct_credits(org_id, user_id, 50, "company_enrichment")
except asyncpg.exceptions.RaiseException as e:
    if "Insufficient credits" in str(e):
        # Parse remaining credits from error message
        # "Insufficient credits: 20 available, 50 needed"
        raise HTTPException(
            status_code=402,  # Payment Required
            detail={
                "error": "insufficient_credits",
                "message": str(e),
                "suggested_action": "Contact your organization admin to add more credits"
            }
        )
```

#### 2. No Credit Allocation

```python
try:
    await deduct_credits(org_id, user_id, 50, "company_enrichment")
except asyncpg.exceptions.RaiseException as e:
    if "No credit allocation found" in str(e):
        raise HTTPException(
            status_code=403,  # Forbidden
            detail={
                "error": "no_allocation",
                "message": "No credit allocation found for your account",
                "suggested_action": "Contact your organization admin to allocate credits to your account"
            }
        )
```

#### 3. Not Authenticated

```python
session_token = request.cookies.get("session_token")
if not session_token:
    raise HTTPException(
        status_code=401,
        detail={
            "error": "not_authenticated",
            "message": "Authentication required",
            "suggested_action": "Login via Keycloak SSO"
        }
    )
```

#### 4. Not Organization Member

```python
# After fetching user's orgs
user_orgs = data['organizations']
if not user_orgs:
    raise HTTPException(
        status_code=403,
        detail={
            "error": "no_organization",
            "message": "User not a member of any organization",
            "suggested_action": "Request invitation from an organization admin"
        }
    )
```

#### 5. Rate Limit Exceeded

```python
response = requests.post(
    'https://api.your-domain.com/api/v1/org-billing/credits/add',
    ...
)

if response.status_code == 429:
    # Rate limit: 20 POST requests per minute
    raise HTTPException(
        status_code=429,
        detail={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Rate limit: 20 POST/min, 100 GET/min",
            "suggested_action": "Wait 60 seconds and try again"
        }
    )
```

### Error Response Format

All Ops-Center API errors follow this format:

```json
{
  "detail": {
    "error": "error_code",
    "message": "Human-readable error message",
    "suggested_action": "What user should do"
  }
}
```

### Retry Strategy

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def deduct_credits_with_retry(
    org_id: str,
    user_id: str,
    credits: int,
    service_type: str
):
    """Deduct credits with automatic retry on transient errors"""
    conn = await asyncpg.connect(DB_CONNECTION)
    try:
        await conn.execute(
            "SELECT deduct_credits($1, $2, $3, $4)",
            org_id, user_id, credits, service_type
        )
        return True
    except asyncpg.exceptions.DeadlockDetectedError:
        # Retry on deadlock
        raise
    except asyncpg.exceptions.RaiseException as e:
        if "Insufficient credits" in str(e):
            # Don't retry - user actually doesn't have credits
            raise
        # Retry on other errors
        raise
    finally:
        await conn.close()
```

---

## Testing Guide

### Test Organization Setup

Contact Ops-Center team to create a test organization:

```json
{
  "org_name": "test-loopnet-integration",
  "display_name": "LoopNet Test Organization",
  "subscription_plan": "platform",
  "initial_credits": 10000,
  "test_users": [
    {
      "email": "loopnet-test-1@example.com",
      "allocated_credits": 1000
    },
    {
      "email": "loopnet-test-2@example.com",
      "allocated_credits": 500
    }
  ]
}
```

### Testing Checklist

#### Phase 1: Authentication

- [ ] Can authenticate with Keycloak SSO
- [ ] Session token is stored in cookies
- [ ] Can retrieve user's organizations
- [ ] Can extract org_id and user_id from session

#### Phase 2: Credit Checks

- [ ] Can check if user has sufficient credits
- [ ] Returns correct boolean for has_sufficient_credits()
- [ ] Error message shows remaining credits

#### Phase 3: Credit Deduction

- [ ] Can deduct credits for successful operation
- [ ] User's remaining_credits decreases correctly
- [ ] Org's used_credits increases correctly
- [ ] Attribution record created in database

#### Phase 4: Error Handling

- [ ] Insufficient credits returns 402 Payment Required
- [ ] No allocation returns 403 Forbidden
- [ ] Invalid org_id returns 404 Not Found
- [ ] Deduction fails on operation failure (no credit loss)

#### Phase 5: Multi-Operation Testing

- [ ] Sequential operations deduct correctly
- [ ] Concurrent operations handled (no race conditions)
- [ ] Bulk operations calculate total cost correctly
- [ ] Cache hits deduct lower credit amount

#### Phase 6: Analytics

- [ ] Usage attribution records have correct metadata
- [ ] Service type categorized correctly
- [ ] Can query usage by service type
- [ ] Can query usage by user

### Test Cases

#### Test Case 1: Happy Path

```python
import pytest

@pytest.mark.asyncio
async def test_company_enrichment_happy_path():
    """Test successful company enrichment with credit deduction"""

    # Arrange
    org_id = "test-org-uuid"
    user_id = "test-user-uuid"
    company_id = "test-company-123"

    # Get initial credits
    initial_credits = await get_user_remaining_credits(org_id, user_id)
    assert initial_credits >= 50, "User needs at least 50 credits"

    # Act
    result = await enrich_company_with_credits(
        org_id=org_id,
        user_id=user_id,
        company_id=company_id,
        enrichment_level="standard"
    )

    # Assert
    assert result['success'] is True
    assert result['credits_used'] == 50
    assert 'enrichment_data' in result

    # Verify credits deducted
    final_credits = await get_user_remaining_credits(org_id, user_id)
    assert final_credits == initial_credits - 50
```

#### Test Case 2: Insufficient Credits

```python
@pytest.mark.asyncio
async def test_insufficient_credits():
    """Test operation fails when user has insufficient credits"""

    # Arrange
    org_id = "test-org-uuid"
    user_id = "test-user-low-credits"  # User with only 10 credits
    company_id = "test-company-123"

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await enrich_company_with_credits(
            org_id=org_id,
            user_id=user_id,
            company_id=company_id,
            enrichment_level="standard"  # Costs 50 credits
        )

    assert "Insufficient credits" in str(exc_info.value)
```

#### Test Case 3: No Allocation

```python
@pytest.mark.asyncio
async def test_no_credit_allocation():
    """Test operation fails when user has no credit allocation"""

    # Arrange
    org_id = "test-org-uuid"
    user_id = "test-user-no-allocation"  # User without allocation
    company_id = "test-company-123"

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await enrich_company_with_credits(
            org_id=org_id,
            user_id=user_id,
            company_id=company_id,
            enrichment_level="standard"
        )

    assert "No credit allocation found" in str(exc_info.value)
```

#### Test Case 4: Operation Failure (No Credit Loss)

```python
@pytest.mark.asyncio
async def test_operation_failure_no_credit_loss():
    """Test credits NOT deducted when operation fails"""

    # Arrange
    org_id = "test-org-uuid"
    user_id = "test-user-uuid"
    company_id = "invalid-company-id"  # Will cause enrichment to fail

    initial_credits = await get_user_remaining_credits(org_id, user_id)

    # Act
    with pytest.raises(Exception):
        await enrich_company_with_credits(
            org_id=org_id,
            user_id=user_id,
            company_id=company_id,
            enrichment_level="standard"
        )

    # Assert - credits unchanged
    final_credits = await get_user_remaining_credits(org_id, user_id)
    assert final_credits == initial_credits  # No change!
```

### Manual Testing

Use these cURL commands to test API endpoints directly:

```bash
# 1. Get user's organizations and credit status
curl -X GET "https://api.your-domain.com/api/v1/org-billing/billing/user" \
  -H "Cookie: session_token=YOUR_TOKEN" \
  | jq '.'

# 2. Get organization credit pool
curl -X GET "https://api.your-domain.com/api/v1/org-billing/credits/ORG_UUID" \
  -H "Cookie: session_token=YOUR_TOKEN" \
  | jq '.'

# 3. Get credit usage stats
curl -X GET "https://api.your-domain.com/api/v1/org-billing/credits/ORG_UUID/usage?days=7" \
  -H "Cookie: session_token=YOUR_TOKEN" \
  | jq '.service_breakdown'

# 4. Check database directly (from postgres container)
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  SELECT
    user_id,
    allocated_credits,
    used_credits,
    remaining_credits
  FROM user_credit_allocations
  WHERE org_id = 'ORG_UUID';
"

# 5. View recent attribution records
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  SELECT
    service_type,
    service_name,
    credits_used,
    request_metadata->>'company_id' as company_id,
    created_at
  FROM credit_usage_attribution
  WHERE org_id = 'ORG_UUID'
  ORDER BY created_at DESC
  LIMIT 10;
"
```

---

## Security Considerations

### 1. Authentication Order

✅ **CORRECT**: Authenticate BEFORE body validation
```python
@router.post("/credits/{org_id}/add")
async def add_credits(
    request: Request,
    org_id: str,
    user: Dict = Depends(require_authenticated_user),  # ← Auth FIRST
    credits: int = Query(..., ge=1)  # ← Validation AFTER
):
    # User is authenticated before validating request parameters
    pass
```

❌ **INCORRECT**: Body validation before auth
```python
@router.post("/credits/{org_id}/add")
async def add_credits(
    org_id: str,
    credits: int = Query(..., ge=1),  # ← Validation FIRST
    request: Request = None,
    user: Dict = Depends(require_authenticated_user)  # ← Auth AFTER
):
    # Body is validated before checking authentication
    # This allows unauthenticated users to test for validation errors
    pass
```

### 2. Rate Limiting

Ops-Center enforces rate limits:

- **POST endpoints**: 20 requests per minute
- **GET endpoints**: 100 requests per minute

**Response on rate limit**:
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

**Best Practice**: Implement client-side rate limiting
```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=15, period=60)  # Stay under limit
async def call_ops_center_api():
    # Your API call
    pass
```

### 3. CORS Restrictions

Ops-Center API enforces CORS:

**Allowed Origins**:
- `https://your-domain.com`
- `https://*.your-domain.com`
- `http://localhost:*` (development only)

If your service runs on a different domain, contact Ops-Center team to whitelist your origin.

### 4. Request ID Tracking

Always include `X-Request-ID` header for debugging:

```python
import uuid

request_id = f"loopnet_{uuid.uuid4()}"

response = requests.post(
    'https://api.your-domain.com/api/v1/org-billing/...',
    headers={'X-Request-ID': request_id},
    ...
)
```

This allows Ops-Center team to trace your request in logs.

### 5. Atomic Operations

Credit deduction uses database transactions with row-level locking:

```sql
-- This happens automatically in deduct_credits() function
SELECT id, remaining_credits
FROM user_credit_allocations
WHERE org_id = '...' AND user_id = '...'
FOR UPDATE;  -- ← Row locked until transaction completes
```

**Why?** Prevents race conditions when multiple operations run concurrently.

### 6. Input Validation

Never trust user input. Always validate:

```python
# Validate UUIDs
import uuid

def validate_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

# Validate credit amounts
def validate_credits(credits: int) -> bool:
    if credits < 1:
        raise ValueError("Credits must be positive")
    if credits > 1_000_000:
        raise ValueError("Credits too large (max 1M)")
    return True

# Sanitize metadata
import json

def sanitize_metadata(metadata: dict) -> dict:
    """Remove sensitive fields from metadata"""
    safe_metadata = metadata.copy()

    # Remove sensitive keys
    for key in ['password', 'api_key', 'secret', 'token']:
        safe_metadata.pop(key, None)

    # Ensure JSON serializable
    try:
        json.dumps(safe_metadata)
        return safe_metadata
    except TypeError:
        return {}
```

### 7. Sensitive Data

**DO NOT** include these in metadata:
- API keys
- Passwords
- Tokens
- Personal financial information
- SSN or other PII

**DO** include these in metadata:
- Operation parameters (company_id, property_id)
- Processing metrics (time, cache hit)
- Result counts (records processed)
- Non-sensitive configuration

---

## FAQ

### Q1: What if user belongs to multiple organizations?

**A**: User can select which organization to use. Store `org_id` in session:

```python
# Frontend: Let user select organization
selected_org = user_organizations[0]  # Or show selector

# Store in session
session['current_org_id'] = selected_org['org_id']

# Use for all operations
org_id = session.get('current_org_id')
```

### Q2: How do I know credit cost before operation?

**A**: Define pricing in your service documentation:

```python
CREDIT_PRICING = {
    'company_enrichment_standard': 50,
    'company_enrichment_full': 100,
    'contact_lookup': 10,
    'bulk_export_per_record': 5,
    'intelligence_cache': 2
}

def get_operation_cost(operation: str, **kwargs) -> int:
    """Calculate credit cost for operation"""
    if operation == 'company_enrichment':
        level = kwargs.get('level', 'standard')
        return CREDIT_PRICING[f'company_enrichment_{level}']

    elif operation == 'bulk_export':
        record_count = kwargs.get('record_count', 1)
        return CREDIT_PRICING['bulk_export_per_record'] * record_count

    elif operation == 'contact_lookup':
        return CREDIT_PRICING['contact_lookup']

    return 0
```

### Q3: What happens if operation fails after credit deduction?

**A**: You should **ONLY** deduct credits **AFTER** successful operation:

```python
# ✅ CORRECT
result = await perform_operation()  # Operation first
if result.success:
    await deduct_credits()  # Credits only if success

# ❌ INCORRECT
await deduct_credits()  # Credits deducted
result = await perform_operation()  # Then operation (fails = credits lost)
```

### Q4: Can I refund credits?

**A**: Yes, but only admins can do this. Contact org admin to add credits back to pool, then reallocate to user.

**Admin API** (requires admin role):
```bash
# Add credits back to pool
curl -X POST "https://api.your-domain.com/api/v1/org-billing/credits/ORG_ID/add?credits=50&purchase_amount=0" \
  -H "Cookie: session_token=ADMIN_TOKEN"

# Reallocate to user
curl -X POST "https://api.your-domain.com/api/v1/org-billing/credits/ORG_ID/allocate" \
  -H "Cookie: session_token=ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "USER_ID", "allocated_credits": 50, "notes": "Refund for failed operation"}'
```

### Q5: How often do credits reset?

**A**: Depends on allocation configuration:

- `reset_period: "daily"` - Every 24 hours
- `reset_period: "weekly"` - Every 7 days
- `reset_period: "monthly"` - Every 30 days
- `reset_period: "never"` - One-time allocation

Check user's allocation:
```python
allocation = await get_user_allocation(org_id, user_id)
reset_period = allocation['reset_period']
next_reset = allocation['next_reset_date']
```

### Q6: Can users purchase credits directly?

**A**: No. Only **organization admins** can purchase credits for the org pool. Individual users get allocations from that pool.

**Workflow**:
1. Org admin purchases credits (via Stripe, invoicing, etc.)
2. Ops-Center adds credits to org pool
3. Org admin allocates credits to users
4. Users consume credits via services

### Q7: What's the difference between `allocated_credits` and `available_credits`?

**Organization Pool**:
- `total_credits`: Total credits org owns (10,000)
- `allocated_credits`: Credits given to users (3,000)
- `available_credits`: Credits not yet allocated (7,000)

**User Allocation**:
- `allocated_credits`: Credits user can use (1,000)
- `used_credits`: Credits user has consumed (250)
- `remaining_credits`: Credits user has left (750)

### Q8: How do I test without spending real credits?

**A**: Use test organization with test credits:

1. Contact Ops-Center team for test org
2. Test org has unlimited credits (not billed)
3. Test user allocated 10,000 credits
4. Perform operations as normal
5. Credits deducted but not charged

### Q9: What if database connection fails during deduction?

**A**: Transaction will roll back automatically:

```python
try:
    async with conn.transaction():
        # Deduct credits
        await conn.execute("SELECT deduct_credits(...)")
        # If any error occurs, transaction rolls back
except Exception as e:
    # Credits NOT deducted
    logger.error(f"Credit deduction failed: {e}")
    raise
```

### Q10: Can I deduct fractional credits?

**A**: No. Credits are **integers** (BIGINT in database). Round up:

```python
import math

# Example: API cost is $0.0023 (2.3 credits)
api_cost_dollars = 0.0023
credits_needed = math.ceil(api_cost_dollars * 1000)  # 3 credits
```

---

## Support & Resources

### Documentation

- **Ops-Center CLAUDE.md**: `/home/muut/Production/UC-Cloud/services/ops-center/CLAUDE.md`
- **Database Schema**: `/home/muut/Production/UC-Cloud/services/ops-center/backend/migrations/create_org_billing.sql`
- **API Implementation**: `/home/muut/Production/UC-Cloud/services/ops-center/backend/org_billing_api.py`
- **Deployment Checklist**: `/home/muut/Production/UC-Cloud/services/ops-center/OPS_CENTER_DEPLOYMENT_CHECKLIST.md`

### API Reference

**Base URL**: `https://api.your-domain.com`

**Endpoints**:
- Subscription: `/api/v1/org-billing/subscriptions`
- Credits: `/api/v1/org-billing/credits`
- Billing: `/api/v1/org-billing/billing`

**OpenAPI Spec**: (Coming soon)

### Database Access

**Connection String** (internal):
```
postgresql://unicorn:password@unicorn-postgresql:5432/unicorn_db
```

**Tables**:
- `organization_subscriptions` - Org-level plans
- `organization_credit_pools` - Shared credit pools
- `user_credit_allocations` - Per-user limits
- `credit_usage_attribution` - Detailed audit trail
- `org_billing_history` - Invoices & payments

### Example Code Repository

Request access to example repository:
```
https://github.com/Unicorn-Commander/ops-center-integration-examples
```

Includes:
- Python integration examples
- FastAPI endpoint templates
- Test cases
- Mock services

### Contact

**Ops-Center Integration Team**:
- Email: ops-center@your-domain.com
- Slack: #ops-center-integration
- GitHub Issues: https://github.com/Unicorn-Commander/Ops-Center/issues

**For Urgent Issues**:
- Create ticket with `[URGENT]` prefix
- Include request ID from `X-Request-ID` header
- Attach relevant logs

---

## Appendix A: Credit Pricing Reference

### LoopNet Operations

| Operation | Credits | USD | Description |
|-----------|---------|-----|-------------|
| Company Enrichment (Standard) | 50 | $0.05 | Basic company data |
| Company Enrichment (Full) | 100 | $0.10 | Complete company profile |
| Contact Lookup | 10 | $0.01 | Find contact information |
| Bulk Export (per record) | 5 | $0.005 | Export company data |
| Intelligence Cache Lookup | 2 | $0.002 | Shared intelligence cache |
| Property Search (per result) | 3 | $0.003 | Property search results |
| Property Valuation | 75 | $0.075 | Property valuation analysis |
| Market Analysis | 150 | $0.15 | Market trend analysis |

### General Operations

| Operation | Credits | USD | Description |
|-----------|---------|-----|-------------|
| LLM Call (GPT-4 Turbo, 1K tokens) | 30 | $0.03 | Language model inference |
| LLM Call (Claude Sonnet, 1K tokens) | 15 | $0.015 | Language model inference |
| Image Generation (DALL-E 3) | 48 | $0.048 | AI image generation |
| Embedding (1K tokens) | 0.02 | $0.00002 | Text embeddings |
| Speech-to-Text (per minute) | 6 | $0.006 | Audio transcription |

---

## Appendix B: Database Schema Quick Reference

### Tables

```sql
-- Organization subscription
CREATE TABLE organization_subscriptions (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    subscription_plan VARCHAR(50),  -- platform, byok, hybrid
    monthly_price DECIMAL(10, 2),
    status VARCHAR(50),  -- active, trialing, canceled
    current_period_end TIMESTAMP
);

-- Organization credit pool
CREATE TABLE organization_credit_pools (
    id UUID PRIMARY KEY,
    org_id UUID UNIQUE REFERENCES organizations(id),
    total_credits BIGINT,
    allocated_credits BIGINT,
    used_credits BIGINT,
    available_credits BIGINT,  -- Generated column
    monthly_refresh_amount BIGINT
);

-- User credit allocation
CREATE TABLE user_credit_allocations (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    user_id VARCHAR(255),
    allocated_credits BIGINT,
    used_credits BIGINT,
    remaining_credits BIGINT,  -- Generated column
    reset_period VARCHAR(20),  -- daily, weekly, monthly, never
    is_active BOOLEAN
);

-- Credit usage attribution
CREATE TABLE credit_usage_attribution (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    user_id VARCHAR(255),
    credits_used BIGINT,
    service_type VARCHAR(100),
    service_name VARCHAR(200),
    request_id VARCHAR(255),
    request_metadata JSONB,
    created_at TIMESTAMP
);
```

### Stored Functions

```sql
-- Check if user has sufficient credits
SELECT has_sufficient_credits(
    p_org_id UUID,
    p_user_id VARCHAR,
    p_credits_needed BIGINT
) RETURNS BOOLEAN;

-- Deduct credits from user allocation
SELECT deduct_credits(
    p_org_id UUID,
    p_user_id VARCHAR,
    p_credits_used BIGINT,
    p_service_type VARCHAR,
    p_service_name VARCHAR DEFAULT NULL,
    p_request_id VARCHAR DEFAULT NULL,
    p_request_metadata JSONB DEFAULT NULL
) RETURNS BOOLEAN;

-- Add credits to org pool
SELECT add_credits_to_pool(
    p_org_id UUID,
    p_credits_amount BIGINT,
    p_purchase_amount DECIMAL DEFAULT 0.00
) RETURNS BOOLEAN;

-- Allocate credits to user
SELECT allocate_credits_to_user(
    p_org_id UUID,
    p_user_id VARCHAR,
    p_credits_amount BIGINT,
    p_allocated_by VARCHAR DEFAULT NULL
) RETURNS BOOLEAN;
```

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **Organization (Org)** | A group that purchases credits and manages users |
| **Credit Pool** | Shared credit balance owned by an organization |
| **Credit Allocation** | Credits assigned to individual user from org pool |
| **Credit Deduction** | Removing credits when user performs operation |
| **Usage Attribution** | Record of who used credits, when, and why |
| **Subscription Plan** | Organization's billing tier (Platform/BYOK/Hybrid) |
| **Reset Period** | How often user's credits refresh (daily/weekly/monthly) |
| **Service Type** | Category of operation (company_enrichment, contact_lookup) |
| **Service Name** | Specific operation (LoopNet Company Enrichment v2) |
| **Request Metadata** | JSON data stored with attribution for analytics |
| **Org Admin** | User with permission to manage org billing |
| **System Admin** | User with access to all organizations |

---

**End of Integration Guide**

**Version**: 1.0
**Last Updated**: November 12, 2025
**Questions?** Contact ops-center@your-domain.com
