# Lago Org-Based Billing Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     UC-1 Pro Application                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │   User 1     │      │   User 2     │      │   User 3     │ │
│  │ aaron@...    │      │ bob@...      │      │ carol@...    │ │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘ │
│         │                     │                     │          │
│         └─────────────────────┴─────────────────────┘          │
│                               │                                │
│                               ▼                                │
│              ┌────────────────────────────────┐                │
│              │    Organization: ACME Corp     │                │
│              │    org_id: org_abc123          │                │
│              │    Billing Email: billing@...  │                │
│              └────────────────┬───────────────┘                │
│                               │                                │
└───────────────────────────────┼────────────────────────────────┘
                                │
                                │ Uses org_id for billing
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              lago_integration.py Module                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Customer Management:                                           │
│  ├─ create_org_customer(org_id, org_name, email)              │
│  ├─ get_or_create_customer(org_id, ...)                       │
│  └─ update_org_customer(org_id, ...)                          │
│                                                                 │
│  Subscription Management:                                       │
│  ├─ subscribe_org_to_plan(org_id, plan_code)                  │
│  ├─ get_subscription(org_id)                                   │
│  └─ terminate_subscription(org_id)                             │
│                                                                 │
│  Usage Tracking:                                                │
│  ├─ record_usage(org_id, event_code, properties)              │
│  └─ record_api_call(org_id, endpoint, user_id, tokens)        │
│                                                                 │
│  Billing Info:                                                  │
│  ├─ get_current_usage(org_id)                                  │
│  └─ get_invoices(org_id)                                       │
│                                                                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ HTTP API calls
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Lago Billing API                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Customer Database:                                             │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ external_id: org_abc123                              │      │
│  │ name: ACME Corp                                      │      │
│  │ email: billing@acme.com                              │      │
│  │ metadata:                                            │      │
│  │   - created_by_user_id: user_xyz789                 │      │
│  │   - billing_type: organization                       │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
│  Subscriptions:                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ customer: org_abc123                                 │      │
│  │ plan: professional_monthly                           │      │
│  │ status: active                                       │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
│  Usage Events:                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ customer: org_abc123                                 │      │
│  │ event: api_call                                      │      │
│  │ properties:                                          │      │
│  │   - user_id: user_xyz789    ← Tracks which user     │      │
│  │   - org_id: org_abc123      ← Organization          │      │
│  │   - tokens: 1500                                     │      │
│  │   - model: gpt-4                                     │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Organization Creation & Billing Setup

```
User creates org → Backend → lago_integration.py → Lago API
                                                      │
                                                      ▼
                                            Customer created:
                                            - external_id = org_id
                                            - name = org_name
                                            - metadata contains user_id
```

### 2. API Call Usage Tracking

```
User makes API call → Middleware intercepts → lago_integration.py → Lago API
                                                                       │
                      org_id from user session                         ▼
                      user_id from user session                Event recorded:
                                                                - customer = org_id
                                                                - properties.user_id = user_id
                                                                - properties.tokens = 1500
```

### 3. Billing & Invoicing

```
End of month → Lago calculates usage → Invoice generated for org_abc123
                                                 │
                                                 ▼
                                        Invoice includes:
                                        - All users' API calls
                                        - Total tokens used
                                        - Total cost
                                        - Sent to org billing email
```

## Key Design Principles

### 1. Organization as Billing Entity
- **One subscription per organization**, not per user
- Multiple users can be part of one organization
- All users in org share the same subscription limits

### 2. User Attribution
- Even though billing is per org, **individual user activity is tracked**
- Usage events include `user_id` in properties
- Enables detailed usage reporting and auditing

### 3. Metadata Preservation
- Organization customers store **original creator's user_id** in metadata
- Migration history tracked in metadata
- Custom business data can be stored

### 4. Backward Compatibility
- Migration helpers provided for user-based → org-based transition
- `is_org_customer()` helper detects customer type
- Gradual migration supported

## Comparison: User-Based vs Org-Based

### User-Based (OLD)

```
User A (user_123) → Customer A → Subscription A → Invoice A
User B (user_456) → Customer B → Subscription B → Invoice B
User C (user_789) → Customer C → Subscription C → Invoice C

Result: 3 subscriptions, 3 invoices, 3 payments
```

### Org-Based (NEW)

```
                    ┌─ User A (user_123)
Organization ───────┼─ User B (user_456)
(org_abc123)        └─ User C (user_789)
    │
    └─→ Customer (org_abc123)
            │
            └─→ Subscription
                    │
                    └─→ Invoice (includes all users' usage)

Result: 1 subscription, 1 invoice, 1 payment
```

## Integration Points

### 1. Organization Creation
```python
# When creating a new organization
await subscribe_org_to_plan(
    org_id=new_org.id,
    plan_code="professional_monthly",
    org_name=new_org.name,
    email=new_org.billing_email,
    user_id=creator.id  # Who created the org
)
```

### 2. User Authentication Middleware
```python
# Extract org_id from user's JWT/session
user_data = decode_jwt(token)
org_id = user_data.get("org_id")
request.state.org_id = org_id
request.state.user_id = user_data.get("user_id")
```

### 3. Usage Tracking Middleware
```python
# After processing request
await record_api_call(
    org_id=request.state.org_id,  # Org pays
    user_id=request.state.user_id,  # User who made call
    transaction_id=f"tx_{uuid4()}",
    endpoint=request.url.path,
    tokens=tokens_used
)
```

### 4. Webhook Handling
```python
# Lago sends webhook for subscription events
async def handle_subscription_created(payload):
    customer = payload["customer"]
    org_id = customer["external_id"]  # This is now org_id

    # Update your database
    await update_org_subscription_status(org_id, "active")
```

## Security Considerations

### 1. Access Control
```python
# Check user belongs to org
if user.org_id != requested_org_id:
    raise HTTPException(403, "Access denied")

# Check org has active subscription
if not await has_active_subscription(org_id):
    raise HTTPException(402, "Payment required")
```

### 2. Usage Limits
```python
# Check before allowing API call
usage = await get_current_usage(org_id)
if usage > org_limits:
    raise HTTPException(429, "Usage limit exceeded")
```

### 3. Audit Trail
- All usage events include user_id for accountability
- Customer metadata tracks org creator
- Event properties can include IP, timestamp, etc.

## Scaling Considerations

### Multi-Tenant Database Design
```sql
-- Organizations table
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    billing_email VARCHAR(255),
    lago_customer_id VARCHAR(255),
    created_by_user_id UUID,
    created_at TIMESTAMP
);

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    email VARCHAR(255),
    role VARCHAR(50)
);

-- Subscription cache (optional)
CREATE TABLE subscription_cache (
    org_id UUID PRIMARY KEY REFERENCES organizations(id),
    plan_code VARCHAR(100),
    status VARCHAR(50),
    expires_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Caching Strategy
```python
# Cache subscription data to reduce API calls
@cache(ttl=300)  # 5 minutes
async def get_cached_subscription(org_id):
    return await get_subscription(org_id)

# Cache usage data
@cache(ttl=60)  # 1 minute
async def get_cached_usage(org_id):
    return await get_current_usage(org_id)
```

## Error Handling Flow

```
API Request
    │
    ├─→ Check org_id present → Error: 401 Unauthorized
    │
    ├─→ Check org exists → Error: 404 Not Found
    │
    ├─→ Check user in org → Error: 403 Forbidden
    │
    ├─→ Check subscription active → Error: 402 Payment Required
    │
    ├─→ Check usage limits → Error: 429 Too Many Requests
    │
    └─→ Process request → Success: 200 OK
            │
            └─→ Record usage in background
                    │
                    ├─→ Success: Logged
                    └─→ Failure: Log error, don't fail request
```

## Monitoring & Observability

### Key Metrics to Track
1. **API success rate to Lago**
   - Monitor create_customer, create_subscription, record_usage
2. **Usage recording delays**
   - Track time between API call and usage event recorded
3. **Failed usage recordings**
   - Alert on high failure rates
4. **Subscription status mismatches**
   - Compare Lago vs your database
5. **Usage limit breaches**
   - Alert when orgs approach limits

### Logging Strategy
```python
# Structured logging for troubleshooting
logger.info(
    "Usage recorded",
    extra={
        "org_id": org_id,
        "user_id": user_id,
        "transaction_id": transaction_id,
        "tokens": tokens,
        "lago_response_time_ms": response_time
    }
)
```

## Future Enhancements

1. **Multi-Org Support per User**
   - User can belong to multiple organizations
   - Switch between orgs in UI

2. **Team Role-Based Billing**
   - Different usage limits per team role
   - Admin vs Member vs Viewer

3. **Usage Forecasting**
   - Predict monthly costs based on current usage
   - Alert before hitting limits

4. **Cost Allocation**
   - Track costs per user within org
   - Chargeback reports for departments

5. **Automated Tier Upgrades**
   - Auto-upgrade when approaching limits
   - Downgrade during low usage periods
