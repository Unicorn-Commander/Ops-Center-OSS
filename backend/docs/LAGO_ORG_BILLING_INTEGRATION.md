# Lago Organization-Based Billing Integration

## Overview

The Lago integration has been updated to use **organization IDs (org_id)** as the primary customer identifier instead of user IDs. This enables:

- Multiple users within an organization sharing a single subscription
- Team-based billing and usage tracking
- Better scalability for enterprise customers
- Clearer separation between user accounts and billing entities

## Key Changes

### 1. Customer Creation - Uses `org_id`

**Before (user-based):**
```python
external_id = user_id
customer_name = user_email
```

**After (org-based):**
```python
external_id = org_id  # Organization ID
customer_name = org_name  # Organization name
metadata = {
    "created_by_user_id": user_id,  # Track who created it
    "created_at": timestamp,
    "billing_type": "organization"
}
```

### 2. Main Functions Updated

#### `create_org_customer()`
Creates a Lago customer for an organization:
```python
await create_org_customer(
    org_id="org_abc123",
    org_name="ACME Corporation",
    email="billing@acme.com",
    user_id="user_xyz789",  # Optional: who created the org
    metadata={"department": "engineering"}  # Optional
)
```

#### `get_or_create_customer()`
Ensures a customer exists (creates if needed):
```python
customer = await get_or_create_customer(
    org_id="org_abc123",
    org_name="ACME Corporation",
    email="billing@acme.com",
    user_id="user_xyz789"
)
```

#### `subscribe_org_to_plan()`
Convenience function that creates customer AND subscription:
```python
subscription = await subscribe_org_to_plan(
    org_id="org_abc123",
    plan_code="professional_monthly",
    org_name="ACME Corporation",
    email="billing@acme.com",
    user_id="user_xyz789"
)
```

#### `record_usage()`
Records usage events for an organization:
```python
await record_usage(
    org_id="org_abc123",
    event_code="api_call",
    transaction_id="tx_unique_123",
    properties={
        "endpoint": "/api/v1/chat/completions",
        "user_id": "user_xyz789",  # Track which user made the call
        "tokens": 1500,
        "model": "gpt-4"
    }
)
```

#### `record_api_call()`
Convenience wrapper for API usage tracking:
```python
await record_api_call(
    org_id="org_abc123",
    transaction_id="tx_unique_456",
    endpoint="/api/v1/chat/completions",
    user_id="user_xyz789",
    tokens=1500,
    model="gpt-4"
)
```

## Usage Examples

### Complete Workflow: New Organization

```python
from lago_integration import (
    get_or_create_customer,
    subscribe_org_to_plan,
    record_api_call,
    get_current_usage
)

# 1. Create organization and subscribe to plan
subscription = await subscribe_org_to_plan(
    org_id="org_new_company",
    plan_code="professional_monthly",
    org_name="New Company Inc",
    email="billing@newcompany.com",
    user_id="user_founder_123"
)

# 2. Record usage as users make API calls
await record_api_call(
    org_id="org_new_company",
    transaction_id=f"tx_{uuid.uuid4()}",
    endpoint="/api/v1/chat/completions",
    user_id="user_founder_123",
    tokens=1500,
    model="gpt-4"
)

# 3. Check current usage
usage = await get_current_usage("org_new_company")
print(f"Current usage: {usage}")
```

### Checking Subscription Status

```python
from lago_integration import get_subscription, get_invoices

# Get active subscription
subscription = await get_subscription("org_abc123")
if subscription:
    plan_code = subscription.get("plan_code")
    status = subscription.get("status")
    print(f"Org is on {plan_code} plan (status: {status})")

# Get recent invoices
invoices = await get_invoices("org_abc123", limit=5)
for invoice in invoices:
    print(f"Invoice {invoice['number']}: ${invoice['total_amount']}")
```

### Upgrading/Downgrading

```python
from lago_integration import terminate_subscription, create_subscription

# Cancel current subscription
await terminate_subscription("org_abc123")

# Create new subscription with different plan
new_subscription = await create_subscription(
    org_id="org_abc123",
    plan_code="enterprise_annual"
)
```

## Migration from User-Based Billing

For backward compatibility, a migration helper is provided:

```python
from lago_integration import migrate_user_to_org

# Migrate existing user-based customer to org-based
success = await migrate_user_to_org(
    user_id="user_old_123",
    org_id="org_new_456",
    org_name="User's Organization",
    email="user@example.com"
)
```

### ID Format Detection

The `is_org_customer()` helper can detect if an ID is org-based or user-based:

```python
from lago_integration import is_org_customer

if is_org_customer(customer_id):
    # Handle as org-based billing
    usage = await get_current_usage(customer_id)
else:
    # Legacy user-based billing
    # Migrate or handle differently
    pass
```

## Configuration

Set these environment variables:

```bash
# Lago API Configuration
LAGO_API_URL=http://unicorn-lago-api:3000
LAGO_API_KEY=your_lago_api_key_here
```

## Error Handling

All functions that modify data raise `LagoIntegrationError` on failure:

```python
from lago_integration import LagoIntegrationError, create_org_customer

try:
    customer = await create_org_customer(
        org_id="org_test",
        org_name="Test Org",
        email="test@example.com"
    )
except LagoIntegrationError as e:
    logger.error(f"Failed to create customer: {e}")
    # Handle error appropriately
```

## Integration with Existing Code

### Update Billing Manager

In `billing_manager.py`, update to use org-based functions:

```python
from lago_integration import subscribe_org_to_plan, record_api_call

@router.post("/organizations/{org_id}/subscribe")
async def subscribe_organization(org_id: str, plan_code: str):
    """Subscribe an organization to a plan"""
    org_data = get_organization(org_id)  # Your org lookup

    subscription = await subscribe_org_to_plan(
        org_id=org_id,
        plan_code=plan_code,
        org_name=org_data["name"],
        email=org_data["billing_email"],
        user_id=current_user["id"]
    )

    return {"subscription": subscription}
```

### Update Usage Tracking Middleware

```python
from lago_integration import record_api_call
from uuid import uuid4

async def track_api_usage(request: Request, call_next):
    """Middleware to track API usage per organization"""

    # Get org_id from user's token/session
    org_id = request.state.user.get("org_id")

    response = await call_next(request)

    # Record usage in Lago
    if org_id:
        await record_api_call(
            org_id=org_id,
            transaction_id=f"tx_{uuid4()}",
            endpoint=request.url.path,
            user_id=request.state.user.get("id"),
            tokens=response.headers.get("X-Tokens-Used", 0),
            model=response.headers.get("X-Model-Used")
        )

    return response
```

### Update Webhooks

In `lago_webhooks.py`, webhooks will now receive org_id in the customer data:

```python
async def handle_subscription_created(payload: Dict[str, Any]):
    subscription = payload.get("subscription", {})
    customer = payload.get("customer", {})

    org_id = customer.get("external_id")  # This is now org_id
    plan_code = subscription.get("plan_code")

    # Update your organization's subscription status
    await update_organization_subscription(org_id, plan_code, "active")
```

## Benefits of Org-Based Billing

1. **Multi-User Support**: Multiple users can be part of one organization sharing a subscription
2. **Team Management**: Easier to manage teams and departments within organizations
3. **Enterprise-Ready**: Better suited for B2B SaaS model
4. **Usage Attribution**: Can still track which user made each API call via metadata
5. **Scalability**: Clearer separation between authentication (users) and billing (orgs)

## Backward Compatibility

The integration includes helpers for migrating from user-based to org-based billing:

- `migrate_user_to_org()`: Migrates existing user customers to org customers
- `is_org_customer()`: Detects customer type based on ID format
- Metadata tracking: Old user_id stored in org customer metadata

## Testing

Test the integration with:

```python
from lago_integration import check_lago_health

# Check if Lago API is accessible
health = await check_lago_health()
print(health)
# Output: {"status": "healthy", "api_url": "...", "message": "..."}
```

## Next Steps

1. Update your organization management system to use these functions
2. Migrate existing user-based customers to org-based (if applicable)
3. Update middleware to track usage by org_id
4. Update webhooks to handle org-based events
5. Test with a trial organization before rolling out

## API Reference

### Customer Management
- `create_org_customer()` - Create org customer
- `get_customer()` - Get customer by org_id
- `update_org_customer()` - Update customer info
- `get_or_create_customer()` - Ensure customer exists

### Subscription Management
- `create_subscription()` - Create subscription
- `subscribe_org_to_plan()` - Create customer + subscription
- `get_subscription()` - Get active subscription
- `terminate_subscription()` - Cancel subscription

### Usage Tracking
- `record_usage()` - Record generic usage event
- `record_api_call()` - Record API call (convenience)
- `get_current_usage()` - Get current period usage

### Billing Info
- `get_invoices()` - Get organization invoices
- `get_current_usage()` - Get usage breakdown

### Migration & Utils
- `migrate_user_to_org()` - Migrate from user to org
- `is_org_customer()` - Detect customer type
- `check_lago_health()` - Health check

## Support

For issues or questions, check:
- Lago API docs: https://doc.getlago.com/
- This integration: `/backend/lago_integration.py`
- Webhooks: `/backend/lago_webhooks.py`
