# Billing Systems Quick Reference Guide

**For**: Development Team, Product Managers, Support Staff
**Date**: November 14, 2025

---

## TL;DR - The Answer in 30 Seconds

**Question**: Do we have duplicate billing systems?

**Answer**: **NO** - All 4 systems are complementary and necessary.

**Why**:
- **Lago** = Monthly subscription fee ($19-$99)
- **Org Credits** = Pre-paid usage pools (like gift cards)
- **Usage Tracking** = API call quotas (rate limiting)
- **LiteLLM** = Token-level cost tracking (actual usage)

**Recommendation**: **Keep all systems** - they work together perfectly.

---

## What Each System Does (One Sentence)

| System | What It Does | Example |
|--------|--------------|---------|
| **Lago Billing** | Charges monthly subscription fees and generates invoices | "Your $49/month subscription is due on Dec 1st" |
| **Org Credits** | Manages pre-paid LLM usage credit pools for organizations | "Your org has 9,500 credits remaining" |
| **Usage Tracking** | Enforces API call quotas and blocks requests when limit exceeded | "You've made 9,876 of 10,000 allowed API calls this month" |
| **LiteLLM** | Calculates token-level costs and routes to AI providers | "This request used 1,500 tokens and cost 0.009 credits" |

---

## What Gets Measured

| Measurement | Lago | Org Credits | Usage Tracking | LiteLLM |
|-------------|:----:|:-----------:|:--------------:|:-------:|
| **Subscription Fee** | ✅ $49 | | | |
| **API Call Count** | ℹ️ Info | | ✅ Enforced | ℹ️ Info |
| **Token Usage** | ℹ️ Info | | ℹ️ Info | ✅ Calculated |
| **Credit Deduction** | | ✅ Primary | | 🔄 Fallback |
| **Dollar Cost** | ✅ Billed | | | 💰 Tracked |
| **Rate Limiting** | | | ✅ Enforced | |

**Legend**:
- ✅ Primary responsibility
- 🔄 Fallback/alternative method
- ℹ️ Informational/analytics only
- 💰 Calculated but not enforced

---

## When Each System Takes Action

### Before LLM Request
1. **Usage Tracking**: "Do you have API calls left?" (Check quota)
2. **Org Credits**: "Do you have credits to pay for this?" (Check balance)

### During LLM Request
3. **LiteLLM**: "Which provider should handle this?" (Route request)

### After LLM Request
4. **LiteLLM**: "How many tokens were used?" (Calculate cost)
5. **Org Credits**: "Deduct X credits from your pool" (Charge usage)
6. **Usage Tracking**: "Increment API call counter" (Track usage)
7. **Lago**: "Log this event for analytics" (Optional reporting)

---

## Real-World Examples

### Example 1: Professional Plan Organization

**Setup**:
- Subscription: Professional ($49/month via Lago)
- Credit Purchase: $100 (10,000 credits via Org Credits)
- Team: 5 users
- API Quota: 10,000 calls/month (via Usage Tracking)

**Monthly Breakdown**:
```
Lago charges:         $49.00  (subscription base fee)
Org credits used:     $95.00  (9,500 credits × $0.01)
API calls made:       9,750   (within 10,000 limit)
Total cost:           $144.00
```

**What each system did**:
- **Lago**: Charged $49 on Dec 1st, sent invoice
- **Org Credits**: Deducted 9,500 credits from pool
- **Usage Tracking**: Counted 9,750 API calls, allowed all (under limit)
- **LiteLLM**: Processed 14.2M tokens, calculated costs

---

### Example 2: BYOK (Bring Your Own Key) User

**Setup**:
- Subscription: Starter ($19/month via Lago)
- BYOK: User has their own OpenRouter API key
- API Quota: 1,000 calls/month (via Usage Tracking)

**Monthly Breakdown**:
```
Lago charges:         $19.00  (subscription base fee)
Org credits used:     $0.00   (BYOK - no platform credits)
API calls made:       850     (within 1,000 limit)
OpenRouter charges:   $X      (user pays provider directly)
Total UC cost:        $19.00
```

**What each system did**:
- **Lago**: Charged $19 subscription
- **Org Credits**: Not used (BYOK bypass)
- **Usage Tracking**: Counted 850 API calls (still enforced!)
- **LiteLLM**: Routed to OpenRouter with user's key, logged usage

**Key Point**: BYOK users still have API call quotas, but don't use credits!

---

## Database Tables Cheat Sheet

### Lago (External DB)
```sql
customers        -- Organizations subscribed to plans
subscriptions    -- Active subscriptions with plan details
invoices         -- Monthly invoices for subscription fees
events           -- Usage events (informational only)
```

### Org Credits (unicorn_db)
```sql
organization_credit_pools     -- Total, allocated, used credits per org
user_credit_allocations       -- Credits allocated to each user
credit_usage_attribution      -- Logs of credit deductions per request
```

### Usage Tracking (unicorn_db + Redis)
```sql
usage_quotas                  -- User tier and API call limits
api_usage                     -- Historical API call records

-- Redis keys:
usage:{user_id}:{YYYY-MM}:calls        -- Monthly counter
usage:{user_id}:{YYYY-MM-DD}:calls     -- Daily counter
```

### LiteLLM (unicorn_db)
```sql
llm_usage_logs               -- Token usage, costs, providers, models
llm_providers                -- Configured API providers (OpenRouter, etc.)
credit_transactions          -- Individual user credit transactions (fallback)
```

---

## API Endpoints Per System

### Lago Billing
```
POST /api/v1/billing/subscriptions/create      # Subscribe to plan
GET  /api/v1/billing/subscriptions/current     # Get current subscription
POST /api/v1/billing/subscriptions/cancel      # Cancel subscription
GET  /api/v1/billing/invoices                  # Invoice history
```

### Org Credits
```
GET  /api/v1/organizations/{id}/credits         # Get credit pool status
POST /api/v1/organizations/{id}/credits/purchase # Buy more credits
POST /api/v1/organizations/{id}/credits/allocate # Allocate to users
GET  /api/v1/organizations/{id}/credits/usage   # Usage breakdown
```

### Usage Tracking
```
GET  /api/v1/usage/current                     # Current usage stats
GET  /api/v1/usage/history                     # Historical data
POST /api/v1/admin/usage/reset                 # Reset quota (admin)
```

### LiteLLM
```
POST /api/v1/llm/chat/completions              # Make LLM request
GET  /api/v1/llm/models                        # List available models
GET  /api/v1/llm/usage                         # Usage statistics
POST /api/v1/llm/byok/keys                     # Add BYOK key
```

---

## Error Codes Cheat Sheet

| Error | Code | System | Meaning | Solution |
|-------|------|--------|---------|----------|
| **Rate Limit Exceeded** | 429 | Usage Tracking | Over API call quota | Wait until reset date or upgrade plan |
| **Payment Required** | 402 | Org Credits | Insufficient credits | Purchase more credits or upgrade tier |
| **Payment Required** | 402 | LiteLLM | Insufficient individual credits | Add credits to account |
| **Unauthorized** | 401 | Usage Middleware | No session cookie | Login required |
| **Service Unavailable** | 503 | LiteLLM | No providers configured | Configure OpenRouter API key |

---

## Credit Calculation Formula

```python
# Base cost per 1K tokens (varies by provider/model)
base_cost = {
    "gpt-4o": 0.015,
    "claude-3-opus": 0.015,
    "mixtral-8x7b": 0.003,
    "local models": 0.0
}

# Power level multipliers
power_multipliers = {
    "eco": 0.1,        # Cheapest, uses free/local models
    "balanced": 0.25,  # Default, good quality/cost ratio
    "precision": 1.0   # Best quality, highest cost
}

# Tier markups (platform fees)
tier_markups = {
    "trial": 0.0,         # Free tier (no markup)
    "starter": 0.4,       # 40% markup
    "professional": 0.6,  # 60% markup
    "enterprise": 0.8     # 80% markup
}

# Final calculation
tokens_used = 1500  # Example
model = "gpt-4o"
power_level = "balanced"
user_tier = "professional"

cost = (tokens_used / 1000) * base_cost[model] * power_multipliers[power_level] * (1 + tier_markups[user_tier])
     = (1500 / 1000) * 0.015 * 0.25 * 1.6
     = 1.5 * 0.015 * 0.25 * 1.6
     = 0.009 credits
```

**Real-world cost**: 0.009 credits ≈ $0.009 (less than 1 cent)

---

## Response Headers Explained

When you make an LLM API call, the response includes these headers:

```
X-RateLimit-Limit: 10000
  → Your total API call quota for the month (from Usage Tracking)

X-RateLimit-Remaining: 9875
  → How many API calls you have left (from Usage Tracking)

X-RateLimit-Reset: 1731628800
  → Unix timestamp when quota resets (from Usage Tracking)

X-RateLimit-Tier: professional
  → Your subscription tier (from Usage Tracking)

X-Provider-Used: OpenRouter
  → Which AI provider handled your request (from LiteLLM)

X-Cost-Incurred: 0.009
  → How many credits this request cost (from LiteLLM)

X-Credits-Remaining: 9991.0
  → Your credit balance after this request (from Org Credits or LiteLLM)
```

---

## Support Scenarios

### Scenario 1: "Why was my request blocked with 429?"

**Check**:
1. What's their tier? (trial/starter/pro/enterprise)
2. How many API calls have they made this month?
3. When does their quota reset?

**Response**:
> "You're on the Starter plan which includes 1,000 API calls per month. You've used all 1,000 calls. Your quota will reset on [date]. You can either wait until then or upgrade to Professional (10,000 calls/month)."

**System**: Usage Tracking

---

### Scenario 2: "Why was my request blocked with 402?"

**Check**:
1. Do they belong to an organization?
2. If yes, check org credit balance
3. If no, check individual credit balance

**Response (Org)**:
> "Your organization's credit pool is depleted (0.02 credits remaining, but request needs 0.05 credits). Please contact your organization admin to purchase more credits."

**Response (Individual)**:
> "Your credit balance is too low (0.5 credits remaining, but request needs 2.0 credits). You can purchase credits at /admin/credits or add a BYOK key to use your own API provider."

**Systems**: Org Credits or LiteLLM

---

### Scenario 3: "Do I get charged if I use my own API key?"

**Answer**:
> "No! When you use BYOK (Bring Your Own Key), you pay your provider directly (OpenRouter, OpenAI, etc.) and we don't charge any credits. You still count toward your API call quota though (e.g., 1,000 calls/month on Starter plan)."

**Systems**: LiteLLM (routes to BYOK), Usage Tracking (still counts calls)

---

### Scenario 4: "What's the difference between credits and subscription?"

**Answer**:
> "Your subscription ($19-$99/month) is the base fee for access to the platform. Credits are for LLM usage - each AI request costs credits based on tokens used. Think of it like:
> - Subscription = Netflix monthly fee (access to service)
> - Credits = Pay-per-view movies (usage-based charges)"

**Systems**: Lago (subscription), Org Credits or LiteLLM (usage)

---

## Developer Notes

### Adding a New LLM Provider

1. Add to `llm_providers` table (LiteLLM)
2. Configure API key (system or BYOK)
3. Add pricing to `MODEL_PRICING` dict (LiteLLM)
4. No changes needed to Lago, Org Credits, or Usage Tracking

### Adding a New Subscription Tier

1. Add to Lago (create plan, get Stripe Price ID)
2. Add to `subscription_manager.py` DEFAULT_PLANS
3. Add to `usage_tracking.py` TIER_LIMITS
4. Add to `litellm_credit_system.py` TIER_MARKUP
5. Update Org Credits allocation defaults (optional)

### Changing API Call Limits

**File**: `backend/usage_tracking.py`
**Dict**: `TIER_LIMITS`

```python
TIER_LIMITS = {
    "starter": {
        "daily_limit": 34,
        "monthly_limit": 1000,  # Change this
        "reset_period": "monthly"
    }
}
```

### Changing Credit Pricing

**File**: `backend/litellm_credit_system.py`
**Dicts**: `PRICING`, `MODEL_PRICING`, `TIER_MARKUP`

```python
MODEL_PRICING = {
    "gpt-4o": 0.015  # Change cost per 1K tokens
}

TIER_MARKUP = {
    "professional": 0.6  # Change markup (60%)
}
```

---

## Testing Checklist

### Test 1: Subscription Billing (Lago)
- [ ] Can create subscription via Stripe Checkout
- [ ] Invoice generated on 1st of month
- [ ] Payment processed successfully
- [ ] Subscription status shows "active"

### Test 2: Organization Credits
- [ ] Admin can purchase credits
- [ ] Admin can allocate credits to users
- [ ] Credits deducted on LLM request
- [ ] Insufficient credits returns 402

### Test 3: Usage Tracking
- [ ] API calls increment counter
- [ ] 429 returned when over limit
- [ ] Quota resets on billing cycle
- [ ] Rate limit headers accurate

### Test 4: LiteLLM
- [ ] Token usage calculated correctly
- [ ] Credits deducted accurately
- [ ] BYOK bypasses credit charge
- [ ] Provider routing works

---

## Conclusion

**All four systems are necessary and complementary**:

```
┌─────────────┐
│    LAGO     │ → "You pay $49/month for access"
└─────────────┘

┌─────────────┐
│ ORG CREDITS │ → "Your org has 10,000 credits to spend"
└─────────────┘

┌─────────────┐
│   USAGE     │ → "You can make 10,000 API calls this month"
│  TRACKING   │
└─────────────┘

┌─────────────┐
│  LITELLM    │ → "This call used 1,500 tokens = 0.009 credits"
└─────────────┘
```

**They measure different things at different levels**:
- Lago = Dollars (subscription)
- Org Credits = Credits (pre-paid usage)
- Usage Tracking = API calls (quota)
- LiteLLM = Tokens (cost calculation)

**No duplicates, no conflicts, all working together!**

---

## Organization Billing Examples

### Example 3: Organization with Team Members

**Setup**:
- Organization: "ACME Corporation"
- Subscription: Professional ($49/month via Lago)
- Credit Pool: $200 (20,000 credits purchased via Org Credits)
- Team Members: 5 users
- Credit Allocations:
  - Alice (Admin): 5,000 credits
  - Bob (Dev): 5,000 credits
  - Carol (Dev): 5,000 credits
  - David (QA): 3,000 credits
  - Eve (PM): 2,000 credits
- Total Allocated: 20,000 credits
- API Quota: 10,000 calls/month (via Usage Tracking)

**Monthly Breakdown**:
```
Lago charges:                 $49.00  (subscription base fee)
Org credit pool purchased:    $200.00 (20,000 credits)
Total setup cost:             $249.00

Usage by team member:
- Alice: 3,200 credits (8 LLM requests, 150 image gen)
- Bob: 4,500 credits (heavy GPT-4 usage)
- Carol: 2,800 credits (mainly GPT-3.5)
- David: 1,200 credits (testing, light usage)
- Eve: 900 credits (summaries, reports)

Total org usage:              12,600 credits
Remaining pool:               7,400 credits
API calls made:               4,230 (within 10,000 limit)

Total cost for month:         $249.00 (fixed, prepaid)
```

**What each system did**:
- **Lago**: Charged $49 subscription on Dec 1st
- **Org Credits**:
  - Admin purchased 20,000 credits for $200
  - Allocated credits to each team member
  - Deducted 12,600 credits from pool
  - Tracked usage attribution per user
- **Usage Tracking**: Counted 4,230 API calls across all users (still enforced!)
- **LiteLLM**: Processed all requests, calculated token costs, routed to providers

**Key Features Used**:
- Shared credit pool (team collaboration)
- Per-user allocations (budget control)
- Usage attribution (accountability)
- Individual vs org automatic detection
- BYOK not used (all via platform models)

### Example 4: Multi-Organization User

**Setup**:
- User: john@example.com
- Organization A: "Startup Inc" (member)
  - Allocation: 2,000 credits
  - Used: 500 credits
- Organization B: "Consulting LLC" (admin)
  - Allocation: 5,000 credits
  - Used: 1,200 credits
- Personal Account: Individual credits
  - Balance: 100 credits (fallback)

**User Dashboard View**:
```
Your Organizations:
┌──────────────────────────────────────────────────────┐
│ Startup Inc (Member)                                 │
│ Allocated: 2,000  Used: 500  Remaining: 1,500      │
│ Plan: Starter ($19/mo)                               │
└──────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────┐
│ Consulting LLC (Admin) ⭐                            │
│ Allocated: 5,000  Used: 1,200  Remaining: 3,800    │
│ Plan: Professional ($49/mo)                          │
└──────────────────────────────────────────────────────┘

Total Credits Available: 5,300 across 2 organizations
+ 100 individual credits (fallback)

Usage Last 30 Days: 1,700 credits (780 requests)
```

**How It Works**:
1. User logs in → Keycloak session established
2. User makes LLM request → System checks:
   - Does user belong to any org? **Yes** (2 orgs)
   - Which org to use? **Default org** or **first org** (Startup Inc)
   - Does that org allocation have credits? **Yes** (1,500 remaining)
   - Deduct from org pool ✓
3. If user switches context to Organization B:
   - System uses Organization B credits instead
   - All usage attributed to Organization B
4. If user leaves both organizations:
   - System falls back to individual credits (100 remaining)

**System Behavior**:
- **Lago**: Both orgs have separate subscriptions
- **Org Credits**: Separate pools per organization, user has allocations in both
- **Usage Tracking**: Quotas tracked per organization
- **LiteLLM**: Routes based on user's current org context

---

## Organization Billing Flow Diagrams

### Credit Purchase & Allocation

```
1. ORG ADMIN PURCHASES CREDITS
   Admin clicks "Add Credits" → Stripe Checkout
        ↓
   Lago records purchase
        ↓
   org_billing_history.event_type = 'credits_purchased'
        ↓
   organization_credit_pools.total_credits += 20,000,000 milicredits
        ↓
   Unallocated credits available for distribution

2. ADMIN ALLOCATES TO TEAM MEMBERS
   Admin selects user + amount
        ↓
   Check: available_credits >= allocation? ✓
        ↓
   user_credit_allocations INSERT (allocated: 5,000,000 milicredits)
        ↓
   organization_credit_pools.allocated_credits += 5,000,000
        ↓
   User can now make LLM requests using org credits
```

### LLM Request with Org Billing

```
1. USER MAKES REQUEST
   POST /api/v1/llm/chat/completions
        ↓
2. DETECT ORGANIZATION
   Query: organization_members WHERE user_id = ?
        ↓
   Found: org_id = 'acme-corp'
        ↓
3. CHECK ORG CREDITS
   Function: has_sufficient_credits(org_id, user_id, 50 milicredits)
        ↓
   remaining_credits = allocated - used = 5,000,000 - 2,000,000 = 3,000,000
        ↓
   3,000,000 >= 50? YES ✓
        ↓
4. PROCESS LLM REQUEST
   LiteLLM → OpenRouter → GPT-4 → Response
        ↓
5. DEDUCT CREDITS ATOMICALLY
   Function: deduct_credits(org_id, user_id, 50, 'llm_inference', 'gpt-4', ...)
        ↓
   BEGIN TRANSACTION
        ↓
   user_credit_allocations.used_credits += 50  (row lock)
        ↓
   organization_credit_pools.used_credits += 50
        ↓
   credit_usage_attribution INSERT (audit trail)
        ↓
   COMMIT
        ↓
6. RETURN RESPONSE WITH HEADERS
   X-Credits-Remaining: 2999.95
   X-Cost-Incurred: 0.05
```

### Org vs Individual Fallback Logic

```
┌─────────────────────────────────────────────────────┐
│  User makes LLM request                             │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Check organization   │
        │ membership           │
        └──────┬───────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐   ┌─────────────┐
│ HAS ORG     │   │ NO ORG      │
│             │   │             │
│ Use org     │   │ Use         │
│ credits     │   │ individual  │
│             │   │ credits     │
└─────────────┘   └─────────────┘
       │                │
       │                │
       ▼                ▼
┌─────────────┐   ┌─────────────┐
│ Deduct from │   │ Deduct from │
│ org pool    │   │ user balance│
│             │   │             │
│ Record to:  │   │ Record to:  │
│ - user_     │   │ - credit_   │
│   credit_   │   │   trans-    │
│   alloc..   │   │   actions   │
│ - org_pool  │   │             │
│ - usage_    │   │             │
│   attrib..  │   │             │
└─────────────┘   └─────────────┘
```

---

## Database Table Quick Reference

### Org Billing Tables (New)

```sql
-- 1. Subscriptions
organization_subscriptions
  - org_id (PK)
  - plan_code, monthly_price
  - lago_subscription_id
  - status (active, canceled, past_due)

-- 2. Credit Pools
organization_credit_pools
  - org_id (PK)
  - total_credits (BIGINT milicredits)
  - allocated_credits (BIGINT)
  - used_credits (BIGINT)
  - available_credits (GENERATED: total - allocated)

-- 3. User Allocations
user_credit_allocations
  - org_id + user_id (composite key)
  - allocated_credits (BIGINT milicredits)
  - used_credits (BIGINT)
  - remaining_credits (GENERATED: allocated - used)
  - is_active (BOOLEAN)

-- 4. Usage Attribution
credit_usage_attribution
  - org_id, user_id
  - service_type ('llm_inference', 'image_generation')
  - service_name (model name)
  - credits_used (BIGINT milicredits)
  - request_metadata (JSONB)

-- 5. Billing History
org_billing_history
  - org_id
  - event_type (subscription_created, credits_purchased, etc.)
  - amount (DECIMAL)
  - lago_invoice_id, stripe_payment_id
```

### Database Functions

```sql
-- Check if user has sufficient credits
has_sufficient_credits(org_id, user_id, credits_needed) → BOOLEAN

-- Atomically deduct credits (race-condition safe)
deduct_credits(org_id, user_id, credits_used, service_type, ...)
  → TABLE(success BOOLEAN, remaining_credits BIGINT)

-- Add credits to organization pool
add_credits_to_pool(org_id, credits, purchase_amount) → VOID

-- Allocate credits to user
allocate_credits_to_user(org_id, user_id, credits, allocated_by) → UUID
```

---

## API Endpoints Cheat Sheet

### Organization Billing API (`/api/v1/org-billing`)

```bash
# Subscriptions
POST   /subscriptions                      # Create subscription
GET    /subscriptions/{org_id}             # Get subscription details
PUT    /subscriptions/{org_id}/upgrade     # Upgrade plan

# Credit Pools
GET    /credits/{org_id}                   # Get pool status
POST   /credits/{org_id}/add               # Purchase credits
POST   /credits/{org_id}/allocate          # Allocate to user
GET    /credits/{org_id}/allocations       # List allocations
GET    /credits/{org_id}/usage             # Usage statistics

# Dashboards
GET    /billing/user                       # Multi-org user dashboard
GET    /billing/org/{org_id}               # Org admin dashboard
GET    /billing/system                     # System admin overview

# History
GET    /{org_id}/history                   # Billing event history
```

---

## Testing Checklist (Updated)

### Test 5: Organization Billing

- [ ] Admin can create org subscription
- [ ] Admin can purchase credits for org
- [ ] Admin can allocate credits to users
- [ ] Users automatically use org credits
- [ ] Credits deducted from org pool
- [ ] Usage attributed to user + org
- [ ] Insufficient org credits returns 402
- [ ] Users without org fall back to individual credits

---

## Troubleshooting (Updated)

### Issue: User Not Using Org Credits

**Symptoms**:
- User is in organization
- Organization has credits
- But LLM requests use individual credits

**Check**:
```sql
-- 1. Verify user is in organization
SELECT * FROM organization_members
WHERE user_id = 'USER_ID' AND status = 'active';

-- 2. Check user has allocation
SELECT * FROM user_credit_allocations
WHERE user_id = 'USER_ID' AND is_active = TRUE;

-- 3. Check org has credits
SELECT total_credits / 1000.0 as total,
       allocated_credits / 1000.0 as allocated,
       used_credits / 1000.0 as used
FROM organization_credit_pools
WHERE org_id = 'ORG_ID';
```

**Fix**:
```sql
-- Allocate credits if missing
SELECT allocate_credits_to_user(
    'ORG_ID'::VARCHAR,
    'USER_ID'::VARCHAR,
    5000000::BIGINT,  -- 5,000 credits
    'admin'::VARCHAR
);
```

### Issue: Org Pool Shows Negative Available

**Symptoms**:
- `available_credits` is negative
- Can't allocate more credits

**Check**:
```sql
SELECT
    total_credits / 1000.0 as total,
    allocated_credits / 1000.0 as allocated,
    available_credits / 1000.0 as available
FROM organization_credit_pools
WHERE org_id = 'ORG_ID';
```

**Fix**:
```sql
-- Recalculate allocated_credits
UPDATE organization_credit_pools
SET allocated_credits = (
    SELECT COALESCE(SUM(allocated_credits), 0)
    FROM user_credit_allocations
    WHERE org_id = organization_credit_pools.org_id
      AND is_active = TRUE
)
WHERE org_id = 'ORG_ID';
```

---

## Conclusion (Updated)

**All FIVE systems work together**:

```
┌─────────────┐
│    LAGO     │ → "Organization pays $49/month for access"
└─────────────┘

┌─────────────┐
│ ORG CREDITS │ → "Organization has 10,000 credits pool"
│             │ → "Alice allocated 2,000 credits"
└─────────────┘

┌─────────────┐
│   USAGE     │ → "Organization can make 10,000 API calls/month"
│  TRACKING   │ → "Alice has made 150 calls"
└─────────────┘

┌─────────────┐
│  LITELLM    │ → "This call used 1,500 tokens = 0.009 credits"
└─────────────┘
```

**Key Differences**:
- **Individual Billing**: User → Credits → LLM
- **Org Billing**: Org → Credit Pool → User Allocation → Credits → LLM
- **Hybrid**: Both work simultaneously with automatic detection

**Backward Compatible**: Existing individual billing continues to work for users without organizations!

---

**Quick Reference Version**: 2.0.0 (Updated with Organization Billing)
**Last Updated**: November 15, 2025
