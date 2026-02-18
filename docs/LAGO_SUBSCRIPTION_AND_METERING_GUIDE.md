# Lago Subscription & Metering Management Guide

**Last Updated**: October 30, 2025
**Purpose**: Complete guide to managing subscriptions, pricing, and service metering
**Status**: Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Accessing Lago Admin Dashboard](#accessing-lago-admin-dashboard)
3. [Managing Subscription Plans](#managing-subscription-plans)
4. [Creating Billable Metrics (Meters)](#creating-billable-metrics-meters)
5. [Adding Charges to Plans](#adding-charges-to-plans)
6. [Passthrough Services (Free/Unmetered)](#passthrough-services-freeunmetered)
7. [Service-Specific Metering](#service-specific-metering)
8. [API Reference](#api-reference)
9. [Examples](#examples)

---

## Overview

### Lago Billing Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Billing Flow                                                    │
└─────────────────────────────────────────────────────────────────┘

1. User signs up → Ops-Center creates customer in Lago
2. User selects plan → Subscription created in Lago
3. User uses service → Usage event sent to Lago
4. Lago aggregates usage → Calculates charges
5. End of billing period → Invoice generated
6. Stripe processes payment → Funds transferred
```

### Key Concepts

**Plans**: Monthly/annual subscription tiers (Trial, Starter, Professional, Enterprise)

**Billable Metrics**: What you measure (API calls, tokens, storage GB, etc.)

**Charges**: How you price the metrics (per-unit, package, percentage, etc.)

**Usage Events**: Real-time tracking of what users consume

**Invoices**: Generated automatically at end of billing period

---

## Accessing Lago Admin Dashboard

### Login Credentials

**URL**: https://billing.unicorncommander.ai

**Admin Account**:
- Email: `admin@example.com`
- Password: `your-admin-password`
- Role: Admin
- Organization: UC-1 Pro

### Dashboard Sections

```
Lago Admin Dashboard
├── Customers - View all customers (organizations/users)
├── Plans - Create and edit subscription plans
├── Billable Metrics - Define what to meter
├── Add-ons - Optional paid extras
├── Coupons - Discount codes
├── Invoices - Generated bills
├── Settings
│   ├── Organization - Org details and API key
│   ├── Integrations - Stripe, webhooks
│   ├── Taxes - Tax rates
│   └── Emails - Invoice templates
└── Developers - API documentation and logs
```

---

## Managing Subscription Plans

### Current Plans (As of Oct 2025)

| Plan | Code | Price | Features |
|------|------|-------|----------|
| Trial | `trial` | $1.00/week | 7-day trial, 100 API calls/day |
| Starter | `starter` | $19/month | 1,000 API calls, BYOK, email support |
| Professional | `professional` | $49/month | 10,000 API calls, all services, priority |
| Enterprise | `enterprise` | $99/month | Unlimited, teams, custom integrations |

### Creating a New Plan

#### Via Admin Dashboard

1. **Navigate to Plans**
   ```
   Dashboard → Plans → Create Plan
   ```

2. **Basic Information**
   ```
   Name: Professional Plan
   Code: professional (unique identifier, no spaces)
   Description: Best for professionals and small teams
   ```

3. **Pricing**
   ```
   Interval: Monthly (or Yearly)
   Amount: $49.00 USD
   Trial Period: 0 days (or 7 days for trial)
   ```

4. **Billing Settings**
   ```
   Pay in advance: ✅ (charge at start of period)
   Invoice net terms: 0 days (due immediately)
   ```

5. **Save Plan**
   - Plan is now available for assignment
   - Can add charges (metering) next

#### Via GraphQL API

```bash
# Get JWT token first
TOKEN=$(curl -X POST https://billing-api.unicorncommander.ai/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { loginUser(input: {email: \"admin@example.com\", password: \"your-admin-password\"}) { token user { id } } }"
  }' | jq -r '.data.loginUser.token')

# Create plan
curl -X POST https://billing-api.unicorncommander.ai/graphql \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Lago-Organization: 2e82bd29-924d-49fe-ae05-658f8e8971fa" \
  -d '{
    "query": "mutation {
      createPlan(input: {
        name: \"Professional Plan\"
        code: \"professional\"
        interval: monthly
        amountCents: 4900
        amountCurrency: USD
        trialPeriod: 0
        payInAdvance: true
        charges: []
        description: \"Best for professionals\"
      }) {
        id
        name
        code
      }
    }"
  }'
```

### Editing an Existing Plan

1. **Navigate to Plan**
   ```
   Dashboard → Plans → Select Plan
   ```

2. **Update Fields**
   - Change price (affects new subscriptions only)
   - Modify description
   - Adjust trial period
   - Add/remove charges

3. **Version Control**
   - Lago creates new version automatically
   - Existing subscriptions stay on old version
   - New subscriptions use new version

---

## Creating Billable Metrics (Meters)

### What Are Billable Metrics?

Billable metrics define **what you measure** for billing purposes.

**Examples**:
- API calls made
- Tokens used in LLM requests
- Storage GB consumed
- Active users per month
- Data transferred (GB)

### Aggregation Types

| Type | Description | Example |
|------|-------------|---------|
| **Count** | Simple count of events | API calls made |
| **Sum** | Total of a numeric field | Tokens used across all requests |
| **Max** | Highest value in period | Peak concurrent users |
| **Unique Count** | Count distinct values | Active users (unique user_ids) |
| **Recurring Count** | Count per unit (e.g., per user) | API calls per user |
| **Weighted Sum** | Sum with different weights | Premium API calls worth 2x |

### Creating a Billable Metric

#### Example: LLM API Calls

1. **Navigate to Billable Metrics**
   ```
   Dashboard → Billable Metrics → Create Metric
   ```

2. **Basic Information**
   ```
   Name: LLM API Calls
   Code: llm_api_calls (unique identifier)
   Description: Count of LLM inference API calls
   ```

3. **Aggregation Settings**
   ```
   Aggregation type: Count
   Field to aggregate: (leave empty for simple count)
   ```

4. **Filters** (Optional)
   ```
   Filter by service: litellm
   Filter by model: openai/gpt-4o
   # Only count specific types of requests
   ```

5. **Save Metric**

#### Example: Token Usage (Sum)

1. **Create Metric**
   ```
   Name: Token Usage
   Code: token_usage
   Description: Total tokens used across all LLM requests
   ```

2. **Aggregation Settings**
   ```
   Aggregation type: Sum
   Field to aggregate: tokens (numeric field in event)
   ```

3. **Filters**
   ```
   Filter by service: litellm
   # Sum tokens across all models
   ```

#### Via GraphQL API

```bash
# Create billable metric
curl -X POST https://billing-api.unicorncommander.ai/graphql \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Lago-Organization: 2e82bd29-924d-49fe-ae05-658f8e8971fa" \
  -d '{
    "query": "mutation {
      createBillableMetric(input: {
        name: \"LLM API Calls\"
        code: \"llm_api_calls\"
        description: \"Count of LLM inference requests\"
        aggregationType: count_agg
      }) {
        id
        name
        code
      }
    }"
  }'
```

---

## Adding Charges to Plans

### Charge Models

Lago supports several pricing models:

#### 1. Standard Pricing (Per Unit)

**Use case**: Fixed price per API call, per GB, etc.

**Example**: $0.01 per API call

```
Charge model: Standard
Price: $0.01 per unit
Free units: 1000 (first 1000 free)
```

#### 2. Package Pricing

**Use case**: Bundled units (e.g., 1000 API calls for $10)

**Example**: 1000 API calls for $10 (effectively $0.01 each)

```
Charge model: Package
Package size: 1000
Price: $10.00
Free units: 0
```

#### 3. Graduated Pricing

**Use case**: Price decreases as usage increases

**Example**:
- 0-1,000 calls: $0.02 each
- 1,001-10,000 calls: $0.01 each
- 10,001+ calls: $0.005 each

```
Charge model: Graduated
Ranges:
  Range 1: 0-1000 units @ $0.02 per unit
  Range 2: 1001-10000 units @ $0.01 per unit
  Range 3: 10001+ units @ $0.005 per unit
```

#### 4. Volume Pricing

**Use case**: All units priced at tier reached

**Example**: If you use 5,000 calls, ALL calls are $0.01 (not just those over 1,000)

```
Charge model: Volume
Ranges:
  0-1000 calls: $0.02 per unit
  1001-10000 calls: $0.01 per unit (applies to ALL)
  10001+ calls: $0.005 per unit (applies to ALL)
```

#### 5. Percentage Pricing

**Use case**: Charge a percentage of transaction value

**Example**: 2.9% + $0.30 per transaction (like Stripe)

```
Charge model: Percentage
Percentage: 2.9%
Fixed fee: $0.30
```

### Adding a Charge to a Plan

#### Via Admin Dashboard

1. **Navigate to Plan**
   ```
   Dashboard → Plans → Select Plan (e.g., Professional)
   ```

2. **Add Charge**
   ```
   Charges section → Add charge
   ```

3. **Select Billable Metric**
   ```
   Metric: LLM API Calls (from dropdown)
   ```

4. **Configure Pricing**
   ```
   Charge model: Graduated

   Range 1:
     From: 0
     To: 10,000
     Per unit: $0.00 (free tier)

   Range 2:
     From: 10,001
     To: 100,000
     Per unit: $0.001 ($1 per 1000 calls)

   Range 3:
     From: 100,001
     To: ∞
     Per unit: $0.0005 ($0.50 per 1000 calls)
   ```

5. **Additional Settings**
   ```
   Invoice display name: LLM API Usage
   Pay in advance: No (charge based on actual usage)
   Prorated: Yes (charge proportionally for partial periods)
   ```

6. **Save Charge**

#### Via GraphQL API

```bash
# Add charge to plan
curl -X POST https://billing-api.unicorncommander.ai/graphql \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Lago-Organization: 2e82bd29-924d-49fe-ae05-658f8e8971fa" \
  -d '{
    "query": "mutation {
      updatePlan(input: {
        id: \"0eefed2d-cdf8-4d0a-b5d0-852dacf9909d\"
        charges: [{
          billableMetricId: \"<metric-id>\"
          chargeModel: graduated
          properties: {
            graduatedRanges: [
              {fromValue: 0, toValue: 10000, perUnitAmount: \"0\", flatAmount: \"0\"},
              {fromValue: 10001, toValue: 100000, perUnitAmount: \"0.001\", flatAmount: \"0\"},
              {fromValue: 100001, toValue: null, perUnitAmount: \"0.0005\", flatAmount: \"0\"}
            ]
          }
        }]
      }) {
        id
        name
      }
    }"
  }'
```

---

## Passthrough Services (Free/Unmetered)

### What Are Passthrough Services?

**Passthrough services** are services you don't charge for. Users can use them without affecting their bill.

**Common use cases**:
- Free tier services (dashboard access, account management)
- Internal tools (admin panels, monitoring)
- Services bundled in base subscription (unlimited access)

### Implementation Options

#### Option 1: Don't Send Usage Events

**Simplest approach**: Don't track usage for free services.

```python
# In your service code
def track_usage(service: str, user_id: str, metric: str, value: int):
    """Track usage only for billable services"""

    # Define passthrough services
    PASSTHROUGH_SERVICES = [
        'dashboard',
        'account-management',
        'system-monitoring',
        'admin-panel'
    ]

    # Skip tracking for passthrough services
    if service in PASSTHROUGH_SERVICES:
        logger.info(f"Passthrough service '{service}' - not tracked for billing")
        return

    # Track usage for billable services
    await lago_send_event(
        external_customer_id=user_id,
        transaction_id=str(uuid.uuid4()),
        code=metric,
        properties={'value': value}
    )
```

#### Option 2: Create Free Metric (0 Cost)

Track usage but charge $0.00.

**Why?**
- Analytics (see how much users use free services)
- Impose limits (e.g., 1000 free API calls per month)
- Upgrade prompts ("You've used 900/1000 free calls")

**Setup**:

1. **Create Billable Metric**
   ```
   Name: Dashboard Views
   Code: dashboard_views
   Aggregation: Count
   ```

2. **Add to Plan with $0.00 Charge**
   ```
   Metric: Dashboard Views
   Charge model: Standard
   Price: $0.00 per unit
   Free units: Unlimited
   ```

**Result**: Usage is tracked but never charged.

#### Option 3: Include in Base Subscription

Some services are "bundled" - you pay the monthly fee, get unlimited access.

**Setup**:

1. **Don't add charges for these services**
   - User pays $49/month for Professional plan
   - Gets unlimited dashboard, account management, etc.
   - Only pay extra for metered services (LLM API, storage)

2. **Track usage for analytics only**
   ```python
   # Track but don't bill
   await send_analytics_event(
       service='dashboard',
       user_id=user_id,
       action='page_view'
   )
   # NOT sent to Lago, only internal analytics
   ```

---

## Service-Specific Metering

### LLM API (litellm) - Token-Based Metering

**What to meter**: Token usage (more accurate than API call count)

**Billable Metric**:
```
Name: LLM Token Usage
Code: llm_tokens
Aggregation: Sum
Field: tokens
```

**Charge Configuration**:
```
Charge model: Graduated
Ranges:
  0-1M tokens: $0.00 (free tier)
  1M-10M tokens: $0.002 per 1K tokens
  10M+ tokens: $0.001 per 1K tokens
```

**Sending Events**:
```python
# In backend/litellm_api.py
await lago_send_event(
    external_customer_id=user_id,
    transaction_id=str(uuid.uuid4()),
    code='llm_tokens',
    properties={
        'tokens': tokens_used,
        'model': 'openai/gpt-4o-mini',
        'service': 'litellm'
    }
)
```

### Open-WebUI - API Call Count

**What to meter**: Chat completion requests

**Billable Metric**:
```
Name: Chat API Calls
Code: chat_api_calls
Aggregation: Count
```

**Charge Configuration**:
```
Charge model: Package
Package size: 1000
Price: $10.00
```

**Sending Events**:
```python
await lago_send_event(
    external_customer_id=user_id,
    transaction_id=str(uuid.uuid4()),
    code='chat_api_calls',
    properties={'service': 'openwebui'}
)
```

### Brigade - Agent Invocations

**What to meter**: Agent runs

**Billable Metric**:
```
Name: Agent Invocations
Code: agent_invocations
Aggregation: Count
```

**Charge Configuration**:
```
Charge model: Standard
Price: $0.05 per invocation
Free units: 100
```

### Center-Deep - Search Queries

**Passthrough (Free)**: Search is included in subscription

**Implementation**:
```python
# Don't send to Lago, just track internally
await analytics.track(
    user_id=user_id,
    event='search_query',
    properties={'query': query}
)
# No billing
```

### Storage (Future) - GB-Hours

**What to meter**: Storage consumed over time

**Billable Metric**:
```
Name: Storage Usage
Code: storage_gb_hours
Aggregation: Sum
Field: gb_hours
```

**Charge Configuration**:
```
Charge model: Standard
Price: $0.10 per GB-hour
Free units: 100 GB-hours
```

**Sending Events**:
```python
# Calculate GB-hours (e.g., 5 GB stored for 24 hours = 120 GB-hours)
gb_hours = storage_gb * hours
await lago_send_event(
    external_customer_id=user_id,
    transaction_id=str(uuid.uuid4()),
    code='storage_gb_hours',
    properties={'gb_hours': gb_hours}
)
```

---

## API Reference

### Sending Usage Events

**Endpoint**: `POST /api/v1/events`

**Headers**:
```
Authorization: Bearer <LAGO_API_KEY>
Content-Type: application/json
```

**Request Body**:
```json
{
  "event": {
    "transaction_id": "unique-uuid",
    "external_customer_id": "user@example.com",
    "code": "llm_tokens",
    "timestamp": "2025-10-30T12:00:00Z",
    "properties": {
      "tokens": 1500,
      "model": "openai/gpt-4o-mini",
      "service": "litellm"
    }
  }
}
```

**Response**:
```json
{
  "event": {
    "lago_id": "event-uuid",
    "transaction_id": "unique-uuid",
    "code": "llm_tokens",
    "timestamp": "2025-10-30T12:00:00Z"
  }
}
```

### Querying Usage

**Endpoint**: `GET /api/v1/customers/:external_id/usage`

**Query Parameters**:
```
external_subscription_id: subscription-uuid
from: 2025-10-01
to: 2025-10-31
```

**Response**:
```json
{
  "usage": {
    "from_datetime": "2025-10-01T00:00:00Z",
    "to_datetime": "2025-10-31T23:59:59Z",
    "charges_usage": [
      {
        "billable_metric": {
          "name": "LLM Token Usage",
          "code": "llm_tokens"
        },
        "units": "1542867",
        "amount_cents": 3086,
        "amount_currency": "USD"
      }
    ]
  }
}
```

---

## Examples

### Example 1: Free Trial with Usage Limits

**Goal**: Give new users 7 days free with 100 API calls per day.

**Setup**:

1. **Create Trial Plan**
   ```
   Name: Trial Plan
   Code: trial
   Price: $1.00/week
   Trial period: 7 days
   ```

2. **Create Billable Metric**
   ```
   Name: API Calls
   Code: api_calls
   Aggregation: Count
   ```

3. **Add Charge to Plan**
   ```
   Metric: API Calls
   Charge model: Standard
   Price: $0.01 per call
   Free units: 700 (100/day * 7 days)
   ```

4. **Enforce Limit in Code**
   ```python
   if user_plan == 'trial':
       if usage_today >= 100:
           raise HTTPException(429, "Daily limit reached. Upgrade to continue.")
   ```

### Example 2: Freemium Model (Free + Paid)

**Goal**: Free tier (limited), paid tiers (more usage).

**Setup**:

1. **Create Free Plan**
   ```
   Name: Free Plan
   Code: free
   Price: $0.00/month
   ```

2. **Add Limited Charge**
   ```
   Metric: LLM API Calls
   Charge model: Package
   Package size: 100
   Price: $0.00
   ```

3. **Enforce in Code**
   ```python
   if user_plan == 'free':
       monthly_usage = await get_monthly_usage(user_id, 'api_calls')
       if monthly_usage >= 100:
           raise HTTPException(402, "Free tier limit reached. Upgrade to Professional for 10,000 calls/month.")
   ```

### Example 3: Pay-As-You-Go (Usage-Based Only)

**Goal**: No monthly fee, only pay for what you use.

**Setup**:

1. **Create PAYG Plan**
   ```
   Name: Pay As You Go
   Code: payg
   Price: $0.00/month (no base fee)
   ```

2. **Add Usage Charge**
   ```
   Metric: LLM Tokens
   Charge model: Standard
   Price: $0.002 per 1K tokens
   Free units: 0
   ```

3. **Bill at End of Month**
   - User pays only for tokens used
   - Invoice generated automatically

### Example 4: Hybrid (Base + Usage)

**Goal**: Monthly base fee + pay for usage over limit.

**Setup**:

1. **Create Professional Plan**
   ```
   Name: Professional
   Code: professional
   Price: $49.00/month
   ```

2. **Add Usage Charge**
   ```
   Metric: LLM API Calls
   Charge model: Graduated
   Range 1: 0-10,000 calls @ $0.00 (included)
   Range 2: 10,001+ calls @ $0.001 per call
   ```

3. **Result**
   - User pays $49/month
   - Gets 10,000 free API calls
   - Pays $1 per 1,000 calls over limit

---

## Best Practices

### 1. Start Simple

**Don't over-engineer**:
- Start with flat pricing ($49/month unlimited)
- Add metering only when needed
- Test with small group before rollout

### 2. Granular Metrics

**Track at service level**:
```
llm_api_calls          # General LLM usage
llm_api_calls_gpt4     # Specific to GPT-4 (higher cost)
llm_api_calls_claude   # Specific to Claude
```

**Why?**: Different models have different costs. Bill accordingly.

### 3. Include Free Tier

**Psychology**:
- Users love "free" (even if limited)
- Easier to upsell from free → paid
- Shows value before asking for money

**Example**:
```
Free: 100 API calls/month
Starter: 1,000 API calls/month ($19)
Professional: 10,000 API calls/month ($49)
```

### 4. Graduated Pricing

**Reward heavy users**:
```
0-1K tokens: $0.002 per 1K
1K-10K tokens: $0.001 per 1K
10K+ tokens: $0.0005 per 1K
```

**Why?**: Encourages usage, retains high-volume customers.

### 5. Set Usage Alerts

**Notify users**:
```python
if usage >= limit * 0.8:
    send_email(
        to=user_email,
        subject="80% of monthly quota used",
        body="You've used 8,000 of 10,000 API calls. Upgrade to avoid overages."
    )
```

---

## Common Patterns

### Pattern 1: All-Inclusive Plans

**Use case**: Simplest billing, predictable revenue

**Setup**:
- Professional: $49/month → Everything unlimited
- No metering, no overages
- User knows exact cost upfront

**Pros**: Simple, predictable
**Cons**: Heavy users cost you money

### Pattern 2: Tiered Usage

**Use case**: Balance simplicity and fairness

**Setup**:
- Starter: $19/month → 1,000 API calls
- Professional: $49/month → 10,000 API calls
- Enterprise: $99/month → 100,000 API calls

**Pros**: Clear tiers, easy to understand
**Cons**: Users might feel limited

### Pattern 3: Base + Overages

**Use case**: Best of both worlds

**Setup**:
- Professional: $49/month → 10,000 API calls included
- Overage: $0.001 per call over limit

**Pros**: Predictable base, scales with usage
**Cons**: Slightly complex billing

### Pattern 4: Pure Usage-Based

**Use case**: Fair, scales perfectly

**Setup**:
- No monthly fee
- Pay $0.002 per 1K tokens used
- Bill at end of month

**Pros**: Fairest, scales naturally
**Cons**: Unpredictable bills, hard to budget

---

## Troubleshooting

### Usage Events Not Showing Up

**Check**:
1. Lago API key is correct
2. Event code matches billable metric code
3. external_customer_id matches Lago customer
4. Check Lago logs: Dashboard → Developers → API Logs

### Charges Not Calculating

**Check**:
1. Billable metric added to plan as charge
2. Charge model configured correctly
3. Plan is active on subscription
4. Usage events received (check API logs)

### Invoice Not Generated

**Check**:
1. Subscription is active
2. Billing period ended
3. Stripe integration enabled
4. Check Lago logs for invoice generation errors

---

## Summary

### Quick Reference

**To manage subscriptions**:
1. Login to https://billing.unicorncommander.ai
2. Go to Plans section
3. Create/edit plans and charges

**To add metering**:
1. Create billable metric (what to measure)
2. Add charge to plan (how to price)
3. Send usage events from your code

**To make service free**:
1. Don't send usage events, OR
2. Add charge with $0.00 price, OR
3. Include in base subscription (no separate charge)

**To test**:
1. Create test customer
2. Assign test plan
3. Send test usage events
4. Check Dashboard → Customers → Usage

---

**Document Status**: ✅ Production Ready
**Last Updated**: October 30, 2025
**Next Review**: When adding new services or pricing changes
