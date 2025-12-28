# Lago Org-Based Billing - Quick Reference

## 🚀 Quick Start

```python
from lago_integration import (
    subscribe_org_to_plan,
    record_api_call,
    get_current_usage,
    get_subscription
)
```

## 📋 Common Operations

### Create Organization with Billing
```python
# One-call setup: creates customer + subscription
subscription = await subscribe_org_to_plan(
    org_id="org_abc123",
    plan_code="professional_monthly",
    org_name="ACME Corporation",
    email="billing@acme.com",
    user_id="user_creator_id"
)
```

### Track API Usage
```python
from uuid import uuid4

await record_api_call(
    org_id="org_abc123",
    transaction_id=f"tx_{uuid4()}",
    endpoint="/api/v1/chat/completions",
    user_id="user_making_call",
    tokens=1500,
    model="gpt-4"
)
```

### Check Subscription Status
```python
subscription = await get_subscription("org_abc123")
if subscription and subscription.get("status") == "active":
    print(f"Active on plan: {subscription.get('plan_code')}")
```

### Get Current Usage
```python
usage = await get_current_usage("org_abc123")
total_amount = usage.get("total_amount", 0)
```

### Upgrade/Downgrade Plan
```python
from lago_integration import terminate_subscription, create_subscription

# Cancel current
await terminate_subscription("org_abc123")

# Create new
await create_subscription("org_abc123", "enterprise_annual")
```

### Get Invoices
```python
from lago_integration import get_invoices

invoices = await get_invoices("org_abc123", limit=5)
for invoice in invoices:
    print(f"{invoice['number']}: ${invoice['total_amount']}")
```

## 🔧 Middleware Integration

```python
from lago_integration import record_api_call
from uuid import uuid4

async def auto_track_usage(request: Request, call_next):
    """Add to FastAPI app to auto-track all API calls"""
    org_id = request.state.user.get("org_id")
    response = await call_next(request)

    if org_id and response.status_code < 400:
        await record_api_call(
            org_id=org_id,
            transaction_id=f"tx_{uuid4()}",
            endpoint=request.url.path,
            user_id=request.state.user.get("id"),
            tokens=int(response.headers.get("X-Tokens-Used", 0))
        )

    return response

# Register middleware
app.middleware("http")(auto_track_usage)
```

## 🛡️ Access Control Helper

```python
from lago_integration import get_subscription

async def check_active_subscription(org_id: str) -> bool:
    """Use in endpoint dependencies"""
    subscription = await get_subscription(org_id)
    return subscription and subscription.get("status") == "active"

# In endpoint
@router.get("/protected")
async def protected_endpoint(org_id: str):
    if not await check_active_subscription(org_id):
        raise HTTPException(403, "No active subscription")
    return {"data": "..."}
```

## 📊 Usage Limits Enforcement

```python
from lago_integration import get_current_usage

async def check_usage_limits(org_id: str, limit: int) -> bool:
    """Check if org is within usage limits"""
    usage = await get_current_usage(org_id)
    if not usage:
        return True

    total_units = sum(
        charge.get("units", 0)
        for charge in usage.get("charges_usage", [])
    )

    return total_units < limit

# Before processing request
if not await check_usage_limits(org_id, 10000):
    raise HTTPException(429, "Usage limit exceeded")
```

## 🔄 Migration

```bash
# Dry run (see what would happen)
python scripts/migrate_lago_to_org_billing.py

# Execute migration
python scripts/migrate_lago_to_org_billing.py --execute

# Verify
python scripts/migrate_lago_to_org_billing.py --verify
```

## ⚙️ Configuration

```bash
# Environment variables
LAGO_API_URL=http://unicorn-lago-api:3000
LAGO_API_KEY=your_api_key_here
```

## 🏥 Health Check

```python
from lago_integration import check_lago_health

health = await check_lago_health()
# Returns: {"status": "healthy", "api_url": "...", "message": "..."}
```

## ⚠️ Error Handling

```python
from lago_integration import LagoIntegrationError

try:
    subscription = await subscribe_org_to_plan(...)
except LagoIntegrationError as e:
    logger.error(f"Billing error: {e}")
    # Handle error
```

## 📖 Key Differences: User vs Org

| Aspect | User-Based (OLD) | Org-Based (NEW) |
|--------|------------------|-----------------|
| Customer ID | `user_id` | `org_id` |
| Customer Name | User email | Organization name |
| Billing Entity | Individual user | Organization |
| Multi-User | No | Yes |
| User Tracking | N/A | In event metadata |

## 🔗 Related Files

- **Core Module:** `lago_integration.py`
- **Documentation:** `docs/LAGO_ORG_BILLING_INTEGRATION.md`
- **Examples:** `examples/lago_org_billing_example.py`
- **Migration Script:** `scripts/migrate_lago_to_org_billing.py`
- **Summary:** `LAGO_ORG_MIGRATION_SUMMARY.md`

## 💡 Pro Tips

1. **Always use `get_or_create_customer()`** instead of creating directly - it handles existing customers
2. **Track user_id in metadata** - helps with usage attribution and auditing
3. **Use transaction IDs** - UUIDs work well: `f"tx_{uuid4()}"`
4. **Cache subscription data** - reduce API calls by caching in Redis/memory
5. **Handle webhook events** - update your database when Lago sends webhooks
6. **Test in dry-run** - always test migrations with dry-run first

## 🆘 Common Issues

### Issue: "Customer already exists"
```python
# Use get_or_create_customer instead of create_org_customer
customer = await get_or_create_customer(...)
```

### Issue: "No active subscription"
```python
# Check subscription status before operations
subscription = await get_subscription(org_id)
if not subscription:
    # Handle no subscription case
```

### Issue: "Usage not recorded"
```python
# Ensure unique transaction IDs
transaction_id = f"tx_{uuid4()}"  # Not the same ID twice!
```

## 📞 Need Help?

- **Full Documentation:** `docs/LAGO_ORG_BILLING_INTEGRATION.md`
- **Working Examples:** `examples/lago_org_billing_example.py`
- **Lago API Docs:** https://doc.getlago.com/
