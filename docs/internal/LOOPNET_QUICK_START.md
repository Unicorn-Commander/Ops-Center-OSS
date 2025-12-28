# LoopNet Integration - Quick Start Card

**Date**: November 12, 2025
**Complete Guide**: See `LOOPNET_INTEGRATION_GUIDE.md` (2,380 lines)

---

## 5-Minute Integration

### 1. Get User Context

```python
import requests

def get_user_org_context(session_token: str) -> dict:
    """Get user's org_id and remaining credits"""
    response = requests.get(
        'https://api.your-domain.com/api/v1/org-billing/billing/user',
        cookies={'session_token': session_token}
    )
    data = response.json()
    org = data['organizations'][0]  # Or let user select

    return {
        'user_id': data['user_id'],
        'org_id': org['org_id'],
        'remaining_credits': org['remaining_credits']
    }
```

### 2. Check Credits (Optional)

```python
import asyncpg

async def check_credits(org_id: str, user_id: str, needed: int) -> bool:
    """Check if user has enough credits"""
    conn = await asyncpg.connect("postgresql://unicorn:password@unicorn-postgresql/unicorn_db")
    try:
        return await conn.fetchval(
            "SELECT has_sufficient_credits($1, $2, $3)",
            org_id, user_id, needed
        )
    finally:
        await conn.close()
```

### 3. Deduct Credits (After Success)

```python
async def deduct_credits(
    org_id: str,
    user_id: str,
    credits: int,
    service_type: str,
    metadata: dict = None
):
    """Deduct credits after successful operation"""
    conn = await asyncpg.connect("postgresql://unicorn:password@unicorn-postgresql/unicorn_db")
    try:
        await conn.execute(
            "SELECT deduct_credits($1, $2, $3, $4, $5, $6, $7::jsonb)",
            org_id,
            user_id,
            credits,
            service_type,
            f"LoopNet {service_type.title()}",
            f"req_{uuid.uuid4().hex[:12]}",
            json.dumps(metadata or {})
        )
    finally:
        await conn.close()
```

### 4. Complete Example

```python
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

@router.post("/loopnet/company/enrich")
async def enrich_company(company_id: str, request: Request):
    """Enrich company data (costs 50 credits)"""

    # 1. Get user context
    session_token = request.cookies.get('session_token')
    context = get_user_org_context(session_token)

    # 2. Check credits
    if not await check_credits(context['org_id'], context['user_id'], 50):
        raise HTTPException(402, "Insufficient credits")

    # 3. Perform operation
    try:
        result = await perform_enrichment(company_id)

        # 4. Deduct credits ONLY if success
        await deduct_credits(
            org_id=context['org_id'],
            user_id=context['user_id'],
            credits=50,
            service_type='company_enrichment',
            metadata={'company_id': company_id}
        )

        return {"success": True, "data": result, "credits_used": 50}

    except Exception as e:
        # Operation failed - NO credit deduction
        raise HTTPException(500, str(e))
```

---

## Credit Pricing

| Operation | Credits | USD |
|-----------|---------|-----|
| Company Enrichment | 50 | $0.05 |
| Contact Lookup | 10 | $0.01 |
| Bulk Export (per record) | 5 | $0.005 |
| Intelligence Cache | 2 | $0.002 |

---

## Service Types

Use these for `service_type` parameter:

- `company_enrichment` - Enrich company data
- `contact_lookup` - Find contacts
- `bulk_export` - Export data
- `intelligence_cache_lookup` - Use cached data
- `property_search` - Search properties
- `valuation` - Property valuations

---

## API Endpoints

**Base**: `https://api.your-domain.com/api/v1/org-billing`

### User Endpoints

```bash
# Get user's orgs and credits
GET /billing/user
Cookie: session_token=YOUR_TOKEN

# Get org credit pool
GET /credits/{org_id}
Cookie: session_token=YOUR_TOKEN

# Get usage stats
GET /credits/{org_id}/usage?days=30
Cookie: session_token=YOUR_TOKEN
```

### Admin Endpoints

```bash
# Add credits to pool
POST /credits/{org_id}/add?credits=5000
Cookie: session_token=ADMIN_TOKEN

# Allocate to user
POST /credits/{org_id}/allocate
Content-Type: application/json
Cookie: session_token=ADMIN_TOKEN

{
  "user_id": "user_uuid",
  "allocated_credits": 1000,
  "reset_period": "monthly"
}
```

---

## Error Handling

```python
try:
    await deduct_credits(...)
except asyncpg.exceptions.RaiseException as e:
    if "Insufficient credits" in str(e):
        raise HTTPException(402, "Insufficient credits")
    elif "No credit allocation" in str(e):
        raise HTTPException(403, "No allocation found")
    else:
        raise HTTPException(500, str(e))
```

---

## Testing

### Create Test Org

Contact: ops-center@your-domain.com

```json
{
  "org_name": "test-loopnet",
  "initial_credits": 10000,
  "test_users": ["loopnet-test-1@example.com"]
}
```

### Test Queries

```bash
# Check user credits
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  SELECT user_id, allocated_credits, used_credits, remaining_credits
  FROM user_credit_allocations
  WHERE org_id = 'ORG_UUID';"

# View recent usage
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  SELECT service_type, credits_used, created_at
  FROM credit_usage_attribution
  WHERE org_id = 'ORG_UUID'
  ORDER BY created_at DESC LIMIT 10;"
```

---

## Common Mistakes

### ❌ DON'T

```python
# Deduct before operation
await deduct_credits(50)
result = await enrich()  # Fails = credits lost
```

### ✅ DO

```python
# Deduct after operation
result = await enrich()
await deduct_credits(50)  # Only if success
```

---

## Database Connection

**Connection String** (internal):
```
postgresql://unicorn:password@unicorn-postgresql:5432/unicorn_db
```

**Tables**:
- `organization_credit_pools` - Org credit balances
- `user_credit_allocations` - Per-user limits
- `credit_usage_attribution` - Usage audit trail

**Functions**:
- `has_sufficient_credits(org_id, user_id, credits)` → boolean
- `deduct_credits(org_id, user_id, credits, service_type, ...)` → boolean

---

## Rate Limits

- **POST**: 20 requests/minute
- **GET**: 100 requests/minute

**On 429 error**: Wait 60 seconds

---

## Security

✅ **DO**:
- Validate session token before operations
- Deduct credits in database transaction
- Include `X-Request-ID` header for debugging
- Sanitize metadata (no API keys, passwords)

❌ **DON'T**:
- Hardcode org_id (get from user session)
- Trust client-side credit calculations
- Include sensitive data in metadata

---

## Support

**Documentation**:
- **Complete Guide**: `LOOPNET_INTEGRATION_GUIDE.md` (2,380 lines)
- **Summary**: `LOOPNET_INTEGRATION_SUMMARY.md`

**Contact**:
- Email: ops-center@your-domain.com
- Slack: #ops-center-integration

**API**:
- Base URL: `https://api.your-domain.com`
- Database: `unicorn-postgresql:5432/unicorn_db`

---

**Ready to integrate!** 🚀

See complete guide for:
- Full API reference (17 endpoints)
- Complete code examples (4 examples)
- Testing guide (6-phase plan)
- FAQ (10 questions)
- Security best practices
