# Organization Billing System - Implementation Summary

**Date**: November 12, 2025
**Status**: Backend Complete ✅ | Frontend In Progress 🚧
**Version**: 1.0.0

---

## Executive Summary

A complete **organization-level billing system** has been implemented for Ops-Center, enabling:

1. **Organization Subscriptions** - Three plan types (Platform, BYOK, Hybrid)
2. **Shared Credit Pools** - Organization-wide credit management
3. **User Credit Allocations** - Per-user limits within organizations
4. **Usage Attribution** - Track which user consumed which credits
5. **Multi-Org Membership** - Users can belong to multiple organizations with different allocations

This system extends the existing user-level billing with enterprise features for team collaboration and cost management.

---

## Architecture Overview

### Three-Level Billing Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    System Admin Level                        │
│  - View all organizations                                    │
│  - Revenue analytics (MRR, ARR)                             │
│  - Subscription distribution                                 │
│  - Top organizations by usage                                │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
┌───────────────────▼──────────┐  ┌────▼─────────────────────┐
│   Organization Admin Level    │  │  Organization Admin Level │
│   (Org A)                     │  │  (Org B)                  │
│  - Org subscription plan      │  │  - Org subscription plan  │
│  - Credit pool management     │  │  - Credit pool management │
│  - Per-user allocations       │  │  - Per-user allocations   │
│  - Usage attribution table    │  │  - Usage attribution table│
└───────────────────┬───────────┘  └────┬──────────────────────┘
                    │                   │
        ┌───────────┼───────────────────┼──────────┐
        │           │                   │          │
    ┌───▼───┐  ┌───▼───┐          ┌────▼────┐ ┌──▼───┐
    │User 1 │  │User 2 │   ...    │User 10  │ │User 3│
    │       │  │       │          │         │ │      │
    │1000   │  │500    │          │Org A:   │ │Org B:│
    │credits│  │credits│          │2000 cred│ │1500  │
    │Org A  │  │Org A  │          │Org B:   │ │cred  │
    └───────┘  └───────┘          │3000 cred│ └──────┘
                                   └─────────┘
```

### Key Design Principles

1. **Multi-Org Support**: Users can be members of multiple organizations
2. **Isolated Credit Pools**: Each organization has its own credit pool
3. **Fair Attribution**: Every credit usage is tracked to specific user + organization
4. **Flexible Allocations**: Organizations can allocate credits to users with different reset periods
5. **Three Subscription Plans**: Platform (managed), BYOK (passthrough), Hybrid (mixed)

---

## Database Schema

### New Tables (5 total)

#### 1. `organization_subscriptions`
**Purpose**: Organization-level subscription plans

```sql
CREATE TABLE organization_subscriptions (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    subscription_plan VARCHAR(50), -- 'platform', 'byok', 'hybrid'
    monthly_price DECIMAL(10,2),
    billing_cycle VARCHAR(20),     -- 'monthly', 'yearly', 'custom'
    status VARCHAR(50),            -- 'active', 'trialing', 'past_due', 'canceled'
    lago_subscription_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    trial_ends_at TIMESTAMP,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Pricing Structure**:
- **Platform Plan**: $50/month - Managed credits with 1.5x markup
- **BYOK Plan**: $30/month - Bring Your Own Keys, passthrough pricing
- **Hybrid Plan**: $99/month - Mix of managed and BYOK credits

#### 2. `organization_credit_pools`
**Purpose**: Shared credit pools for organizations

```sql
CREATE TABLE organization_credit_pools (
    id UUID PRIMARY KEY,
    org_id UUID UNIQUE REFERENCES organizations(id),
    total_credits BIGINT,           -- Total credits in pool
    allocated_credits BIGINT,       -- Sum of all user allocations
    used_credits BIGINT,            -- Total consumed
    available_credits BIGINT,       -- COMPUTED: total - allocated
    monthly_refresh_amount BIGINT,  -- Auto-refresh credits
    last_refresh_date TIMESTAMP,
    next_refresh_date TIMESTAMP,
    allow_overage BOOLEAN,
    overage_limit BIGINT,
    overage_rate DECIMAL(10,6),
    lifetime_purchased_credits BIGINT,
    lifetime_spent_amount DECIMAL(12,2),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Credit Flow**:
```
Organization Purchases Credits
         ↓
   Credit Pool (total_credits)
         ↓
   Allocated to Users (allocated_credits)
         ↓
   Users Consume Credits (used_credits)
```

#### 3. `user_credit_allocations`
**Purpose**: Per-user credit limits within organizations

```sql
CREATE TABLE user_credit_allocations (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    user_id VARCHAR(255),           -- Keycloak user UUID
    allocated_credits BIGINT,       -- User's credit limit
    used_credits BIGINT,            -- User's consumption
    remaining_credits BIGINT,       -- COMPUTED: allocated - used
    reset_period VARCHAR(20),       -- 'daily', 'weekly', 'monthly', 'never'
    last_reset_date TIMESTAMP,
    next_reset_date TIMESTAMP,
    is_active BOOLEAN,
    allocated_by VARCHAR(255),      -- Admin who set allocation
    notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(org_id, user_id)
);
```

**Reset Periods**:
- **Daily**: Resets every 24 hours (good for high-frequency users)
- **Weekly**: Resets every 7 days (good for moderate users)
- **Monthly**: Resets every 30 days (standard for most organizations)
- **Never**: No automatic reset (manual management only)

#### 4. `credit_usage_attribution`
**Purpose**: Detailed audit trail of credit consumption

```sql
CREATE TABLE credit_usage_attribution (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    user_id VARCHAR(255),
    allocation_id UUID REFERENCES user_credit_allocations(id),
    credits_used BIGINT,
    service_type VARCHAR(100),      -- 'llm', 'image_generation', 'embeddings'
    service_name VARCHAR(200),      -- Specific model/service
    api_cost DECIMAL(12,6),         -- Actual API cost (if BYOK)
    markup_applied DECIMAL(12,6),   -- Markup charged (if Platform)
    total_cost DECIMAL(12,6),       -- COMPUTED: api_cost + markup
    request_id VARCHAR(255),
    request_metadata JSONB,         -- Store tokens, latency, etc.
    created_at TIMESTAMP
);
```

**Tracks**:
- Which organization paid for the request
- Which user made the request
- What service was used (LLM, image gen, embeddings)
- Actual API cost vs markup charged
- Full request metadata for analytics

#### 5. `org_billing_history`
**Purpose**: Invoice and payment tracking

```sql
CREATE TABLE org_billing_history (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    subscription_id UUID REFERENCES organization_subscriptions(id),
    event_type VARCHAR(50),         -- 'invoice_created', 'invoice_paid', 'subscription_upgraded'
    lago_invoice_id VARCHAR(255),
    stripe_invoice_id VARCHAR(255),
    amount DECIMAL(12,2),
    currency VARCHAR(3),
    payment_status VARCHAR(50),     -- 'pending', 'paid', 'failed', 'refunded'
    payment_method VARCHAR(100),
    paid_at TIMESTAMP,
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    event_metadata JSONB,
    notes TEXT,
    created_at TIMESTAMP
);
```

---

## Database Functions

### 4 Stored Functions Created

#### 1. `has_sufficient_credits(org_id, user_id, credits_needed)`
**Purpose**: Check if user has enough credits before operation

```sql
-- Returns: BOOLEAN
-- Usage: SELECT has_sufficient_credits(org_id, user_id, 100);
```

#### 2. `deduct_credits(org_id, user_id, credits_used, service_type, ...)`
**Purpose**: Atomically deduct credits and record usage

```sql
-- Returns: BOOLEAN
-- Side Effects:
--   1. Updates user_credit_allocations.used_credits
--   2. Updates organization_credit_pools.used_credits
--   3. Inserts credit_usage_attribution record
-- Usage: SELECT deduct_credits(org_id, user_id, 50, 'llm', 'gpt-4');
```

**Transaction-Safe**: Uses row locking to prevent race conditions

#### 3. `add_credits_to_pool(org_id, credits_amount, purchase_amount)`
**Purpose**: Add credits to organization pool

```sql
-- Returns: BOOLEAN
-- Side Effects:
--   1. Updates total_credits
--   2. Updates lifetime_purchased_credits
--   3. Updates lifetime_spent_amount
-- Usage: SELECT add_credits_to_pool(org_id, 10000, 100.00);
```

#### 4. `allocate_credits_to_user(org_id, user_id, credits_amount, allocated_by)`
**Purpose**: Allocate credits from pool to user

```sql
-- Returns: BOOLEAN
-- Side Effects:
--   1. Creates or updates user_credit_allocations
--   2. Updates organization_credit_pools.allocated_credits
-- Usage: SELECT allocate_credits_to_user(org_id, user_id, 1000, admin_id);
```

**Prevents**:
- Allocating more credits than available in pool
- Creating invalid allocations

---

## API Endpoints

### Base Path: `/api/v1/org-billing`

### Organization Subscription Management

```http
POST   /subscriptions
GET    /subscriptions/{org_id}
PUT    /subscriptions/{org_id}/upgrade
```

**Example: Create Subscription**
```bash
curl -X POST http://localhost:8084/api/v1/org-billing/subscriptions \
  -H "Cookie: session_token=..." \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "123e4567-e89b-12d3-a456-426614174000",
    "subscription_plan": "platform",
    "monthly_price": 50.00,
    "billing_cycle": "monthly",
    "trial_days": 14
  }'
```

**Response**:
```json
{
  "id": "sub_abc123",
  "org_id": "123e4567-e89b-12d3-a456-426614174000",
  "org_name": "Acme Corp",
  "subscription_plan": "platform",
  "monthly_price": 50.00,
  "billing_cycle": "monthly",
  "status": "trialing",
  "trial_ends_at": "2025-11-26T12:00:00Z",
  "current_period_end": "2025-12-12T12:00:00Z",
  "created_at": "2025-11-12T12:00:00Z"
}
```

### Credit Pool Management

```http
GET    /credits/{org_id}
POST   /credits/{org_id}/add
POST   /credits/{org_id}/allocate
GET    /credits/{org_id}/allocations
GET    /credits/{org_id}/usage
```

**Example: Add Credits to Pool**
```bash
curl -X POST "http://localhost:8084/api/v1/org-billing/credits/123/add?credits=10000&purchase_amount=100.00" \
  -H "Cookie: session_token=..."
```

**Response**:
```json
{
  "success": true,
  "message": "Added 10000 credits to pool",
  "total_credits": 10000,
  "available_credits": 10000
}
```

**Example: Allocate Credits to User**
```bash
curl -X POST http://localhost:8084/api/v1/org-billing/credits/123/allocate \
  -H "Cookie: session_token=..." \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_456",
    "allocated_credits": 1000,
    "reset_period": "monthly",
    "notes": "Marketing team member - standard allocation"
  }'
```

**Response**:
```json
{
  "id": "alloc_789",
  "org_id": "123",
  "user_id": "user_456",
  "allocated_credits": 1000,
  "used_credits": 0,
  "remaining_credits": 1000,
  "reset_period": "monthly",
  "next_reset_date": "2025-12-12T12:00:00Z",
  "is_active": true,
  "created_at": "2025-11-12T12:00:00Z"
}
```

### Billing Screen Endpoints

```http
GET    /billing/user              # User's multi-org dashboard
GET    /billing/org/{org_id}      # Org admin billing screen
GET    /billing/system            # System admin overview
GET    /billing/{org_id}/history  # Billing history
```

**Example: User Billing Dashboard**
```bash
curl http://localhost:8084/api/v1/org-billing/billing/user \
  -H "Cookie: session_token=..."
```

**Response** (User in Multiple Organizations):
```json
{
  "user_id": "user_456",
  "user_email": "john@example.com",
  "organizations": [
    {
      "org_id": "org_123",
      "org_name": "Acme Corp",
      "role": "member",
      "subscription_plan": "platform",
      "monthly_price": 50.00,
      "allocated_credits": 1000,
      "used_credits": 234,
      "remaining_credits": 766
    },
    {
      "org_id": "org_789",
      "org_name": "Beta LLC",
      "role": "admin",
      "subscription_plan": "hybrid",
      "monthly_price": 99.00,
      "allocated_credits": 5000,
      "used_credits": 1203,
      "remaining_credits": 3797
    }
  ],
  "total_usage_last_30_days": {
    "total_credits_used": 1437,
    "org_count": 2,
    "request_count": 578
  }
}
```

---

## Subscription Plans

### Platform Plan - $50/month

**Target**: Organizations that want managed infrastructure

**Features**:
- Ops-Center manages all API keys and providers
- 1.5x markup on API costs for support and infrastructure
- No API key management burden
- Automatic provider failover and optimization
- Included support and monitoring

**Credit Calculation**:
```
User makes LLM request → OpenAI charges $0.002 → User charged 3 credits
(1 credit = $0.001, so $0.002 × 1.5 markup = $0.003 = 3 credits)
```

### BYOK Plan - $30/month

**Target**: Organizations that want to use their own API keys

**Features**:
- Bring Your Own Keys (OpenAI, Anthropic, etc.)
- Passthrough pricing (no markup)
- Organization manages API keys
- Ops-Center provides routing and usage tracking
- Lower monthly fee since infrastructure cost is lower

**Credit Calculation**:
```
User makes LLM request → OpenAI charges org's key $0.002 → User charged 2 credits
(1 credit = $0.001, so $0.002 = 2 credits, no markup)
```

### Hybrid Plan - $99/month

**Target**: Large organizations that want flexibility

**Features**:
- Mix of managed (Platform) and BYOK services
- Some services use Ops-Center keys (with markup)
- Some services use organization's keys (no markup)
- Best of both worlds
- Priority support and SLA guarantees

**Credit Calculation**:
```
User makes GPT-4 request (managed) → Charged 3 credits (with markup)
User makes Claude request (BYOK) → Charged 2 credits (passthrough)
```

---

## Security & Permissions

### Role-Based Access Control

#### System Admin
- Can view all organizations
- Can create/modify any organization subscription
- Can view revenue analytics across all orgs
- Can allocate credits to any organization

#### Organization Admin
- Can view their organization's subscription
- Can upgrade/downgrade subscription plan
- Can add credits to organization pool
- Can allocate credits to users within organization
- Can view usage attribution for their org

#### Organization Member
- Can view their own credit allocation(s)
- Can see which organizations they belong to
- Can view their own usage history
- Cannot modify credit allocations or subscriptions

### Permission Checks

All endpoints implement three-level security:

```python
1. Authentication: User must have valid session
2. Organization Membership: User must belong to organization
3. Role Check: User must have required role (admin/member)
```

**Example**:
```python
# In endpoint
user = await get_current_user(request)
is_admin = await check_system_admin(user)
is_org_admin = await check_org_admin(conn, org_id, user["user_id"])

if not is_admin and not is_org_admin:
    raise HTTPException(status_code=403, detail="Not authorized")
```

---

## Integration with Existing Systems

### Keycloak SSO Integration

**User Identification**:
```python
# Map Keycloak 'sub' field to 'user_id'
if "user_id" not in user and "sub" in user:
    user["user_id"] = user["sub"]
```

**Organization Membership**:
- Stored in `organization_members` table
- Linked to Keycloak user via `user_id` (UUID)
- Roles: `owner`, `admin`, `billing_admin`, `member`

### Lago Billing Integration

**Sync Strategy**:
1. Organization subscription created in Ops-Center
2. Lago customer created (if not exists)
3. Lago subscription created with external_id
4. Store `lago_subscription_id` in `organization_subscriptions`

**Webhook Handling**:
- `subscription.started` → Update status to 'active'
- `invoice.paid` → Record in `org_billing_history`
- `invoice.payment_failed` → Update status to 'past_due'

### Credit System Integration

**When User Makes API Call**:
```python
# 1. Check if user has sufficient credits
has_credits = await conn.fetchval(
    "SELECT has_sufficient_credits($1, $2, $3)",
    org_id, user_id, credits_needed
)

if not has_credits:
    raise InsufficientCreditsError()

# 2. Make API call to LLM provider
response = await llm_provider.complete(request)

# 3. Deduct credits and record usage
await conn.execute(
    "SELECT deduct_credits($1, $2, $3, $4, $5, $6, $7)",
    org_id, user_id, credits_used, 'llm',
    'gpt-4', request_id, metadata
)
```

---

## Views & Analytics

### 4 Database Views Created

#### 1. `org_billing_summary`
**Purpose**: Quick overview of organization billing status

```sql
SELECT * FROM org_billing_summary;
```

**Returns**:
- Organization name
- Subscription plan and price
- Total/allocated/used/available credits
- Member count
- Lifetime spending

#### 2. `user_multi_org_credits`
**Purpose**: Show user's credit allocations across all organizations

```sql
SELECT * FROM user_multi_org_credits WHERE user_id = 'user_456';
```

**Returns**:
- All organizations user belongs to
- Credit allocation in each org
- Used and remaining credits per org
- Reset periods and dates

#### 3. `top_credit_users_by_org`
**Purpose**: Identify highest credit consumers per organization

```sql
SELECT * FROM top_credit_users_by_org WHERE org_id = 'org_123';
```

**Returns**:
- Top 10 users by credit consumption
- Total credits used (last 30 days)
- Request count
- Services used

#### 4. `org_billing_metrics`
**Purpose**: Organization-level metrics for analytics

```sql
SELECT * FROM org_billing_metrics;
```

**Returns**:
- Invoice count (last 30 days)
- Total revenue
- Failed payments
- Total credits used
- Active user count

---

## Testing Scenarios

### Scenario 1: Multi-Org User

**Setup**:
1. User "alice" joins Organization A (allocated 1000 credits)
2. User "alice" joins Organization B (allocated 500 credits)
3. User makes 100 LLM requests from Org A (uses 200 credits)
4. User makes 50 LLM requests from Org B (uses 100 credits)

**Expected Results**:
- Org A credit pool: 1000 allocated, 200 used, 800 available
- Org B credit pool: 500 allocated, 100 used, 400 available
- Alice's dashboard shows both organizations with separate allocations
- Usage attribution table shows which org paid for which request

### Scenario 2: Credit Exhaustion

**Setup**:
1. Organization C has 5000 total credits
2. Allocate 2000 to User 1, 2000 to User 2, 1000 to User 3
3. Try to allocate 500 to User 4

**Expected Results**:
- `allocate_credits_to_user()` function raises error: "Insufficient credits in pool"
- Organization must purchase more credits before allocating to User 4

### Scenario 3: Subscription Upgrade

**Setup**:
1. Organization D starts with BYOK plan ($30/month)
2. Admin upgrades to Hybrid plan ($99/month)

**Expected Results**:
- Subscription plan updated to 'hybrid'
- Monthly price updated to $99.00
- Billing history records 'subscription_upgraded' event
- Organization can now use mix of managed and BYOK services

---

## Next Steps (Phase 2: Frontend)

### 1. User Billing Dashboard
**Location**: `src/pages/billing/UserBillingDashboard.jsx`

**Features**:
- Show all organizations user belongs to
- Display credit allocation per org
- Personal usage statistics
- Multi-org credit selector
- Quick links to each org's billing page

**UI Components**:
```jsx
<OrganizationCard>
  <OrgName>Acme Corp</OrgName>
  <SubscriptionPlan>Platform ($50/mo)</SubscriptionPlan>
  <CreditAllocation>1000 credits allocated</CreditAllocation>
  <CreditUsage>234 used | 766 remaining</CreditUsage>
  <ProgressBar value={23.4} />
  <Button>View Details</Button>
</OrganizationCard>
```

### 2. Org Admin Billing Screen
**Location**: `src/pages/organization/OrganizationBillingPro.jsx`

**Features**:
- Organization subscription plan display
- Credit pool management (add credits)
- Per-user allocation table
- Usage attribution chart
- Upgrade/downgrade options
- Billing history timeline

**UI Sections**:
1. **Subscription Overview** - Current plan, next billing date, amount
2. **Credit Pool** - Total/allocated/used/available with visual indicators
3. **User Allocations Table** - Sortable, filterable list of all users
4. **Usage Chart** - Line chart showing daily credit consumption
5. **Top Users** - Bar chart of highest consumers
6. **Billing History** - Invoices, payments, subscription changes

### 3. System Admin Billing Screen
**Location**: `src/pages/admin/SystemBillingOverview.jsx`

**Features**:
- All organizations list with billing status
- Revenue analytics (MRR, ARR)
- Subscription distribution pie chart
- Top organizations by usage
- Credit pool summaries
- Payment failure alerts

**Key Metrics Cards**:
```jsx
<MetricsRow>
  <MetricCard title="MRR" value="$12,450" trend="+12%" />
  <MetricCard title="ARR" value="$149,400" trend="+12%" />
  <MetricCard title="Active Orgs" value="45" trend="+3" />
  <MetricCard title="Total Credits Used" value="2.4M" trend="+18%" />
</MetricsRow>
```

---

## Files Modified/Created

### Backend Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `backend/migrations/create_org_billing.sql` | 600+ | Database schema migration |
| `backend/org_billing_api.py` | 1000+ | RESTful API endpoints |

### Backend Files Modified

| File | Changes | Purpose |
|------|---------|---------|
| `backend/server.py` | +2 lines | Import and register router |

### Frontend Files To Create

| File | Est. Lines | Purpose |
|------|------------|---------|
| `src/pages/billing/UserBillingDashboard.jsx` | 400-500 | User multi-org billing view |
| `src/pages/organization/OrganizationBillingPro.jsx` | 800-1000 | Org admin billing screen |
| `src/pages/admin/SystemBillingOverview.jsx` | 600-700 | System admin analytics |

---

## Architecture Decisions

### Decision 1: Three Subscription Plans vs Variable Pricing

**Chosen**: Three Fixed Plans (Platform, BYOK, Hybrid)

**Rationale**:
- Simpler for customers to understand
- Easier to market and sell
- Predictable revenue forecasting
- Reduces decision paralysis

**Alternative Considered**: Variable pricing based on usage
- Rejected: Too complex for SMB customers
- Rejected: Harder to predict costs

### Decision 2: Credit Pools vs Direct User Credits

**Chosen**: Organization Credit Pools with User Allocations

**Rationale**:
- Enables team cost management
- Admins can reallocate credits between users
- Prevents individual users from exhausting entire org budget
- Better visibility into who's consuming credits

**Alternative Considered**: Direct user credits (no pool)
- Rejected: No org-level control
- Rejected: Can't transfer credits between users

### Decision 3: Stored Functions vs Application Logic

**Chosen**: PostgreSQL Stored Functions for Credit Operations

**Rationale**:
- Atomic operations (no race conditions)
- Database-level transaction safety
- Better performance (less network round-trips)
- Easier to audit and debug

**Alternative Considered**: Python application logic
- Rejected: Risk of race conditions
- Rejected: Harder to ensure consistency

### Decision 4: Multi-Org Membership Model

**Chosen**: Allow users to belong to multiple organizations

**Rationale**:
- Matches real-world usage (consultants, contractors)
- Each org has separate credit allocation
- User sees all orgs in one dashboard
- Attribution tracks which org paid for each request

**Alternative Considered**: Single-org membership
- Rejected: Too limiting for power users
- Rejected: Requires duplicate accounts

### Decision 5: Reset Periods (Daily/Weekly/Monthly/Never)

**Chosen**: Flexible reset periods per user allocation

**Rationale**:
- Different users have different usage patterns
- High-frequency users need daily resets
- Standard users work with monthly limits
- Special accounts (demo, test) use 'never'

**Alternative Considered**: Fixed monthly reset for all
- Rejected: Not flexible enough
- Rejected: Some users need more frequent resets

---

## Performance Considerations

### Database Indexes

**Critical Indexes**:
```sql
CREATE INDEX idx_credit_usage_org_id ON credit_usage_attribution(org_id);
CREATE INDEX idx_credit_usage_user_id ON credit_usage_attribution(user_id);
CREATE INDEX idx_credit_usage_created_at ON credit_usage_attribution(created_at);
```

**Why**: Credit usage attribution will grow rapidly (millions of rows). Indexes ensure fast queries for:
- User billing dashboard (filter by user_id)
- Org admin screen (filter by org_id)
- Analytics queries (filter by date range)

### Query Optimization

**Use Views for Common Queries**:
```sql
-- Instead of complex JOIN every time
SELECT * FROM org_billing_summary WHERE org_id = 'org_123';

-- Instead of aggregation query
SELECT * FROM top_credit_users_by_org WHERE org_id = 'org_123';
```

**Expected Query Times**:
- User billing dashboard: <50ms (2-3 orgs)
- Org admin screen: <100ms (100 users)
- System admin overview: <200ms (1000 orgs)

### Caching Strategy

**Redis Caching**:
```python
# Cache org credit pool for 60 seconds
cache_key = f"org_credit_pool:{org_id}"
cached = await redis.get(cache_key)
if cached:
    return json.loads(cached)

# Fetch from DB
pool = await fetch_credit_pool(org_id)
await redis.setex(cache_key, 60, json.dumps(pool))
return pool
```

**Invalidation**:
- Invalidate on credit addition
- Invalidate on credit allocation
- Invalidate on credit deduction

---

## Monitoring & Alerts

### Key Metrics to Track

1. **Credit Pool Utilization**
   - Alert when organization uses >80% of allocated credits
   - Suggest purchasing more credits

2. **User Allocation Exhaustion**
   - Alert when user uses >90% of their allocation
   - Suggest increasing allocation or optimization

3. **Payment Failures**
   - Alert system admin when subscription payment fails
   - Auto-suspend organization after 3 failed attempts

4. **Subscription Churn**
   - Track subscription cancellations
   - Analyze reasons for downgrades

### Logging Strategy

**Audit Log Events**:
```
- org.subscription.created
- org.subscription.upgraded
- org.subscription.downgraded
- org.subscription.canceled
- org.credits.purchased
- org.credits.allocated
- org.credits.exhausted
- user.allocation.created
- user.allocation.reset
```

---

## Migration Path for Existing Users

### Step 1: Create Default Organizations

```sql
-- Create personal organization for each existing user
INSERT INTO organizations (name, display_name, plan_tier, max_seats)
SELECT
    'personal-' || user_id,
    user_email || '''s Organization',
    'professional',
    1
FROM users
WHERE NOT EXISTS (
    SELECT 1 FROM organization_members WHERE user_id = users.user_id
);
```

### Step 2: Migrate User Credits to Org Credit Pools

```sql
-- Create credit pool for each new org
INSERT INTO organization_credit_pools (org_id, total_credits)
SELECT id, 10000 FROM organizations WHERE name LIKE 'personal-%';

-- Allocate credits to users
INSERT INTO user_credit_allocations (org_id, user_id, allocated_credits)
SELECT
    o.id,
    u.user_id,
    u.current_credits
FROM users u
JOIN organizations o ON o.name = 'personal-' || u.user_id;
```

### Step 3: Migrate User Subscriptions to Org Subscriptions

```sql
-- Create org subscription from user subscription
INSERT INTO organization_subscriptions (org_id, subscription_plan, monthly_price)
SELECT
    o.id,
    u.subscription_tier,  -- Map to plan (trial→platform, etc.)
    CASE u.subscription_tier
        WHEN 'trial' THEN 1.00
        WHEN 'starter' THEN 19.00
        WHEN 'professional' THEN 50.00  -- Upgraded to Platform plan
        WHEN 'enterprise' THEN 99.00    -- Upgraded to Hybrid plan
    END
FROM users u
JOIN organizations o ON o.name = 'personal-' || u.user_id;
```

---

## Troubleshooting

### Common Issues

#### Issue 1: "Insufficient credits in pool"

**Cause**: Trying to allocate more credits than available

**Solution**:
```bash
# Add credits to pool first
curl -X POST "http://localhost:8084/api/v1/org-billing/credits/org_123/add?credits=5000"

# Then allocate to user
curl -X POST "http://localhost:8084/api/v1/org-billing/credits/org_123/allocate" \
  -d '{"user_id": "user_456", "allocated_credits": 1000}'
```

#### Issue 2: User belongs to multiple orgs, which one to charge?

**Cause**: Ambiguous organization context in API request

**Solution**: Always include org_id in request headers
```bash
curl -X POST http://localhost:8084/api/v1/llm/chat/completions \
  -H "X-Organization-ID: org_123" \
  -d '{"model": "gpt-4", "messages": [...]}'
```

#### Issue 3: Credit deduction fails with "concurrent update"

**Cause**: Race condition (two requests deducting credits simultaneously)

**Solution**: Use database row locking (already implemented in `deduct_credits()`)
```sql
SELECT remaining_credits
FROM user_credit_allocations
WHERE org_id = $1 AND user_id = $2
FOR UPDATE;  -- Lock row
```

---

## Testing Checklist

### Database Schema Tests

- [x] All tables created successfully
- [x] Indexes created on foreign keys
- [x] Partial unique index works (one active subscription per org)
- [x] Computed columns work (available_credits, remaining_credits)
- [x] Triggers fire correctly (updated_at timestamps)
- [ ] Foreign key cascades work correctly
- [ ] Check constraints prevent invalid data

### Function Tests

- [ ] `has_sufficient_credits()` returns correct boolean
- [ ] `deduct_credits()` atomically updates all 3 tables
- [ ] `add_credits_to_pool()` updates lifetime totals
- [ ] `allocate_credits_to_user()` prevents over-allocation
- [ ] Race condition handling (concurrent credit deductions)
- [ ] Error handling (negative credits, invalid org_id)

### API Endpoint Tests

- [ ] Create subscription (success, validation errors)
- [ ] Get subscription (authorized, unauthorized)
- [ ] Upgrade subscription (valid plans, invalid plans)
- [ ] Add credits to pool (positive amount, negative amount)
- [ ] Allocate credits to user (within limit, exceeds limit)
- [ ] Get credit allocations (pagination, filtering)
- [ ] Get usage statistics (date range, aggregations)
- [ ] User billing dashboard (multi-org display)
- [ ] Org admin billing screen (permissions, data accuracy)
- [ ] System admin overview (revenue metrics, top orgs)

### Integration Tests

- [ ] Keycloak SSO authentication
- [ ] Multi-org membership handling
- [ ] Credit deduction during LLM request
- [ ] Lago subscription sync
- [ ] Stripe payment webhook handling
- [ ] Billing history recording

### Performance Tests

- [ ] Query performance with 1M+ credit usage records
- [ ] Concurrent credit deductions (100 simultaneous requests)
- [ ] Dashboard load time with 100 organizations
- [ ] Redis caching effectiveness

---

## Deployment Checklist

### Pre-Deployment

- [x] Database migration script reviewed
- [x] API endpoints documented
- [ ] Frontend screens designed (wireframes)
- [ ] Security audit completed
- [ ] Performance testing completed
- [ ] Staging environment tested

### Deployment Steps

1. **Backup Database**
   ```bash
   docker exec uchub-postgres pg_dump -U unicorn -d unicorn_db > backup_pre_org_billing.sql
   ```

2. **Run Migration**
   ```bash
   cat backend/migrations/create_org_billing.sql | \
   docker exec -i uchub-postgres psql -U unicorn -d unicorn_db
   ```

3. **Verify Schema**
   ```bash
   docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "\dt org*"
   docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "\df *credit*"
   ```

4. **Restart Backend**
   ```bash
   docker restart ops-center-direct
   ```

5. **Test API**
   ```bash
   curl http://localhost:8084/api/v1/org-billing/billing/user -H "Cookie: session_token=..."
   ```

6. **Monitor Logs**
   ```bash
   docker logs ops-center-direct -f | grep "org-billing"
   ```

### Post-Deployment

- [ ] Verify all endpoints return 200/201 (not 500)
- [ ] Test user billing dashboard loads
- [ ] Test org admin screen loads
- [ ] Test system admin overview loads
- [ ] Verify credit deduction works end-to-end
- [ ] Monitor database query performance
- [ ] Check for any error logs

---

## Future Enhancements

### Phase 3: Advanced Features

1. **Credit Gifting**
   - Organization admin can transfer credits between users
   - Endpoint: `POST /credits/{org_id}/transfer`

2. **Credit Expiration**
   - Set expiration dates on credit allocations
   - Auto-expire unused credits after X days
   - Alert users before expiration

3. **Budget Alerts**
   - Email/Slack notification when org hits 80% credit usage
   - Webhook for external systems
   - Configurable thresholds per organization

4. **Usage Forecasting**
   - ML model predicts next month's credit usage
   - Suggests optimal credit purchase amount
   - Alerts when credit pool may run out

5. **Credit Marketplace**
   - Organizations can sell unused credits to others
   - Peer-to-peer credit transfer
   - Platform takes 5% transaction fee

6. **Volume Discounts**
   - Bulk credit purchases at discount
   - Example: Buy 100K credits, get 10K free
   - Loyalty rewards for long-term customers

---

## Conclusion

The organization billing system is now **functionally complete at the backend level**. All database tables, functions, views, and API endpoints are implemented and ready for frontend integration.

**What's Done**:
- ✅ Database schema (5 tables, 4 functions, 4 views)
- ✅ RESTful API (17 endpoints)
- ✅ Multi-org membership support
- ✅ Credit pool management
- ✅ Usage attribution tracking
- ✅ Three subscription plans
- ✅ Security & permissions
- ✅ Integration with Keycloak, Lago, existing credit system

**What's Next** (Phase 2):
- 🚧 User billing dashboard UI
- 🚧 Org admin billing screen UI
- 🚧 System admin overview UI
- 🚧 End-to-end testing
- 🚧 Production deployment

**Estimated Timeline for Phase 2**: 1-2 weeks

**Total Lines of Code Added**: 1,600+ lines (backend only)

---

**Document Version**: 1.0.0
**Last Updated**: November 12, 2025
**Author**: Ops-Center System Architecture Team
**Review Status**: Pending Frontend Implementation
