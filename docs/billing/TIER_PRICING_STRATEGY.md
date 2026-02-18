# Tier Management & Pricing Strategy Guide
**UC-Cloud Ops-Center**
**Last Updated**: November 3, 2025
**Version**: 2.0

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [What's Already Built](#whats-already-built)
3. [Usage-Based Billing Architecture](#usage-based-billing-architecture)
4. [LLM Cost Control & Pricing](#llm-cost-control--pricing)
5. [Tier Management System](#tier-management-system)
6. [Use Cases & Examples](#use-cases--examples)
7. [Best Practices](#best-practices)
8. [Advanced Features](#advanced-features)

---

## Overview

UC-Cloud's Ops-Center provides a **complete, production-ready billing and tier management system** with:

- ✅ **Usage-based billing** (credits deducted per API call)
- ✅ **LLM cost tracking** (actual costs from OpenRouter, OpenAI, Anthropic, etc.)
- ✅ **Flexible pricing** (markup, passthrough, or hybrid)
- ✅ **Unlimited tiers** (create any subscription package)
- ✅ **Unlimited features** (mix and match services/apps)
- ✅ **Model access control** (different tiers get different models)
- ✅ **Credit system** (prepaid credits or subscription allocations)

**Core Value Proposition**: You control pricing, your users pay for usage, and you profit from the markup.

---

## What's Already Built

### 1. Credit System (`credit_api.py`)

**20 API Endpoints** for complete credit management:

#### Credit Management (5 endpoints)
```python
GET  /api/v1/credits/balance              # Get user credit balance
POST /api/v1/credits/allocate             # Allocate credits to user
POST /api/v1/credits/deduct               # Deduct credits for usage
POST /api/v1/credits/refund               # Refund credits to user
POST /api/v1/credits/transfer             # Transfer credits between users
```

#### Usage Metering (5 endpoints)
```python
POST /api/v1/credits/usage/track          # Track API usage event
GET  /api/v1/credits/usage/summary        # Usage summary by date range
GET  /api/v1/credits/usage/by-model       # Usage breakdown by model
GET  /api/v1/credits/usage/by-service     # Usage breakdown by service
GET  /api/v1/credits/usage/export         # Export usage data (CSV)
```

#### OpenRouter BYOK (4 endpoints)
```python
POST /api/v1/credits/openrouter/register  # Register OpenRouter key
GET  /api/v1/credits/openrouter/balance   # Check OpenRouter balance
GET  /api/v1/credits/openrouter/keys      # List user's OR keys
DEL  /api/v1/credits/openrouter/keys/{id} # Remove OR key
```

#### Coupon System (5 endpoints)
```python
POST /api/v1/credits/coupons/redeem       # Redeem coupon code
GET  /api/v1/credits/coupons/available    # List available coupons
POST /api/v1/credits/coupons/create       # Create coupon (admin)
GET  /api/v1/credits/coupons/{code}       # Get coupon details
DEL  /api/v1/credits/coupons/{code}       # Delete coupon (admin)
```

### 2. LLM API with Cost Tracking (`litellm_api.py`)

**OpenAI-Compatible Endpoint** that tracks costs:

```python
POST /api/v1/llm/chat/completions  # OpenAI-compatible chat
GET  /api/v1/llm/models             # List available models
GET  /api/v1/llm/usage              # Usage statistics
POST /api/v1/llm/checkout           # Credit purchase via Stripe
```

**Key Features**:
- Routes through LiteLLM proxy (`unicorn-litellm-wilmer:4000`)
- Tracks actual costs from OpenRouter/OpenAI/Anthropic
- Deducts credits based on configurable pricing
- Supports BYOK (Bring Your Own Key) mode
- Supports streaming responses

### 3. Subscription Tiers (`subscription_tiers` table)

**Database Schema** for unlimited tier creation:

| Column | Type | Description |
|--------|------|-------------|
| `tier_code` | varchar(50) | Unique identifier (e.g., "professional") |
| `tier_name` | varchar(100) | Display name |
| `price_monthly` | numeric(10,2) | Monthly price in dollars |
| `price_yearly` | numeric(10,2) | Yearly price (usually 10-20% discount) |
| `api_calls_limit` | integer | Monthly API call quota |
| `team_seats` | integer | Number of seats/users |
| `byok_enabled` | boolean | Allow Bring Your Own Key |
| `priority_support` | boolean | Priority support flag |
| `lago_plan_code` | varchar(100) | Lago billing plan ID |
| `stripe_price_monthly` | varchar(100) | Stripe price ID (monthly) |
| `stripe_price_yearly` | varchar(100) | Stripe price ID (yearly) |

### 4. Feature-to-Tier Mapping (`tier_features` table)

**Many-to-Many Relationship** between tiers and features:

| Column | Type | Description |
|--------|------|-------------|
| `tier_id` | integer | Foreign key to `subscription_tiers` |
| `feature_key` | varchar(100) | Feature identifier (e.g., "chat_access") |
| `enabled` | boolean | Feature enabled for this tier |

### 5. Tier Management GUI

**Two Admin Interfaces**:

1. **App Management** (`/admin/system/feature-management`)
   - Create/edit/delete features
   - View which tiers include each feature
   - Color-coded tier badges (Gold = VIP, Purple = BYOK, Blue = Managed)

2. **Subscription Management** (`/admin/system/subscription-management`)
   - Create/edit/delete tiers
   - Manage pricing and limits
   - Assign features to tiers (checkbox UI)
   - User migration tools

---

## Usage-Based Billing Architecture

### How It Works

```
┌──────────────────────────────────────────────────────────┐
│                    User Makes API Call                    │
│          POST /api/v1/llm/chat/completions               │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │   Check Credit Balance │
            │   (Enough credits?)    │
            └───────────┬────────────┘
                        │
                ┌───────┴───────┐
                │               │
         ❌ No Credits     ✅ Has Credits
                │               │
                ▼               ▼
        Return 402         ┌────────────────┐
      "Insufficient        │ Route to LiteLLM│
        Credits"           │  Proxy (Wilmer) │
                           └────────┬────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌────────────┐  ┌────────────┐  ┌────────────┐
            │ OpenRouter │  │   OpenAI   │  │ Anthropic  │
            └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
                  │               │               │
                  └───────────────┼───────────────┘
                                  │
                        ┌─────────▼─────────┐
                        │  Get Actual Cost  │
                        │  (e.g., $0.0025)  │
                        └─────────┬─────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   Calculate User Charge    │
                    │  (cost × markup = charge)  │
                    │   e.g., $0.0025 × 2 =     │
                    │        $0.005              │
                    └─────────────┬──────────────┘
                                  │
                        ┌─────────▼──────────┐
                        │  Deduct Credits    │
                        │   from Balance     │
                        └─────────┬──────────┘
                                  │
                        ┌─────────▼──────────┐
                        │  Record Transaction│
                        │  (usage_events)    │
                        └────────────────────┘
```

### Cost Calculation Example

**Real-World Scenario**:
- User calls GPT-4 via your platform
- OpenRouter charges: **$0.03 per 1k tokens** (input) + **$0.06 per 1k tokens** (output)
- User's request: 500 input tokens, 1000 output tokens
- **Actual Cost**: (500 × $0.03 / 1000) + (1000 × $0.06 / 1000) = **$0.0015 + $0.06 = $0.0615**

**Your Pricing Options**:

1. **Passthrough (0% markup)**:
   - User pays: $0.0615
   - Your profit: $0.00
   - Use case: BYOK users, enterprise contracts

2. **2x Markup (100% markup)**:
   - User pays: $0.123
   - Your profit: $0.0615
   - Use case: Standard pricing

3. **Fixed Rate ($0.10 per call)**:
   - User pays: $0.10
   - Your profit: $0.0385
   - Use case: Predictable pricing for users

### Credit Pricing

**Credit-to-Dollar Conversion**:
```
1 credit = $0.001 (one-tenth of a cent)

Examples:
- 10,000 credits = $10 of usage
- 100,000 credits = $100 of usage
- 1,000,000 credits = $1,000 of usage
```

**Credit Packages** (suggested):
```
Starter Pack:     10,000 credits = $12  (20% markup)
Professional Pack: 100,000 credits = $110 (10% markup)
Enterprise Pack:  1,000,000 credits = $1,000 (0% markup)
```

---

## LLM Cost Control & Pricing

### 1. Markup Configuration

**Three Pricing Models**:

#### A. Passthrough Pricing (BYOK Mode)
```python
# User brings their own OpenRouter/OpenAI key
# You don't mark up costs
# User sees actual provider costs

Example:
- OpenRouter charges user: $0.05
- Your platform deducts: $0.05 (passthrough)
- Your profit: $0.00
```

#### B. Fixed Markup (Recommended)
```python
# Set a percentage markup on all LLM calls
# Simple to implement and explain

Example (2x markup = 100%):
- OpenRouter cost: $0.03
- Your platform charges: $0.06
- Your profit: $0.03

Example (1.5x markup = 50%):
- OpenRouter cost: $0.03
- Your platform charges: $0.045
- Your profit: $0.015
```

#### C. Per-Model Pricing
```python
# Set different markups per model
# More control over margins

Example:
{
  "gpt-4-turbo": {
    "markup": 1.5,  # 50% markup
    "min_charge": 0.01  # Minimum $0.01 per call
  },
  "gpt-3.5-turbo": {
    "markup": 2.0,  # 100% markup
    "min_charge": 0.001
  },
  "claude-3-opus": {
    "markup": 1.3,  # 30% markup
    "min_charge": 0.02
  }
}
```

### 2. Model Access per Tier

**Configure which models each tier can access**:

```python
# Database: tier_model_access table (to be created)

Tier: Free
  ✓ gpt-3.5-turbo (limited to 100 calls/day)
  ✗ gpt-4
  ✗ claude-3-opus

Tier: Professional ($49/mo)
  ✓ gpt-3.5-turbo (unlimited)
  ✓ gpt-4-turbo (up to 1000 calls/mo)
  ✓ claude-3-sonnet
  ✗ claude-3-opus (too expensive)

Tier: Enterprise (Custom)
  ✓ All models
  ✓ Custom model fine-tuning
  ✓ Dedicated inference endpoints
```

### 3. Cost Tracking & Reporting

**Already Built**:

```python
# Track every API call
POST /api/v1/credits/usage/track
{
  "user_id": "user-123",
  "service": "openrouter",
  "model": "gpt-4-turbo",
  "input_tokens": 500,
  "output_tokens": 1000,
  "actual_cost": 0.0615,
  "charged_amount": 0.123,
  "credits_deducted": 123
}

# Get usage summary
GET /api/v1/credits/usage/summary?from=2025-11-01&to=2025-11-30

Response:
{
  "total_calls": 1543,
  "total_cost": $95.23,
  "total_charged": $190.46,
  "profit_margin": $95.23,
  "by_model": {
    "gpt-4-turbo": {"calls": 892, "cost": $54.32, "charged": $108.64},
    "gpt-3.5-turbo": {"calls": 651, "cost": $40.91, "charged": $81.82}
  }
}
```

---

## Tier Management System

### Creating Custom Tiers

**Example 1: Freemium Model**

```sql
INSERT INTO subscription_tiers (
  tier_code, tier_name, price_monthly, price_yearly,
  api_calls_limit, team_seats, byok_enabled
) VALUES (
  'free',
  'Free Forever',
  0.00,
  0.00,
  100,  -- 100 calls per month
  1,
  false
);

-- Add features
INSERT INTO tier_features (tier_id, feature_key, enabled)
SELECT id, 'chat_access', true FROM subscription_tiers WHERE tier_code = 'free'
UNION ALL
SELECT id, 'basic_search', true FROM subscription_tiers WHERE tier_code = 'free';
```

**Example 2: Power User Tier**

```sql
INSERT INTO subscription_tiers (
  tier_code, tier_name, price_monthly, price_yearly,
  api_calls_limit, team_seats, byok_enabled, priority_support
) VALUES (
  'power_user',
  'Power User Pro',
  99.00,
  990.00,  -- 2 months free (16% discount)
  50000,
  3,
  true,  -- BYOK enabled
  true
);

-- Add all features
INSERT INTO tier_features (tier_id, feature_key, enabled)
SELECT id, feature_key, true
FROM subscription_tiers, (
  SELECT 'chat_access' AS feature_key
  UNION ALL SELECT 'search_enabled'
  UNION ALL SELECT 'brigade_access'
  UNION ALL SELECT 'bolt_access'
  UNION ALL SELECT 'tts_enabled'
  UNION ALL SELECT 'stt_enabled'
) features
WHERE tier_code = 'power_user';
```

### Managing via GUI

**Step-by-Step Workflow**:

1. **Create Tier** (`/admin/system/subscription-management`)
   - Click "Create Tier"
   - Set: Name, Code, Pricing, Limits
   - Click Save

2. **Assign Features**
   - Click Sync icon (⟳) on the tier
   - Check boxes for features to include
   - Click "Save Features"

3. **View Associations** (`/admin/system/feature-management`)
   - See which tiers include each feature
   - Color-coded badges for easy identification

4. **Lago Integration**
   - Create matching plan in Lago
   - Copy Lago plan code to `lago_plan_code` field
   - Lago handles billing, your platform enforces access

---

## Use Cases & Examples

### Use Case 1: SaaS Startup

**Goal**: Simple 3-tier model with clear value props

```
Free Tier - $0/mo
  ✓ 100 API calls/month
  ✓ Chat access (GPT-3.5 only)
  ✓ Community support

Starter - $19/mo
  ✓ 5,000 API calls/month
  ✓ Chat + Search
  ✓ GPT-3.5 + GPT-4 access
  ✓ Email support

Professional - $49/mo
  ✓ 50,000 API calls/month
  ✓ All services
  ✓ All models (GPT-4, Claude-3)
  ✓ Priority support
  ✓ BYOK option
```

### Use Case 2: Enterprise B2B

**Goal**: Custom packages for different team sizes

```
Team (5 seats) - $199/mo
  ✓ 100,000 API calls/month
  ✓ All features
  ✓ SSO integration
  ✓ Dedicated account manager

Business (20 seats) - $599/mo
  ✓ 500,000 API calls/month
  ✓ Custom integrations
  ✓ SLA guarantees
  ✓ White-label options

Enterprise (Unlimited) - Custom
  ✓ Unlimited everything
  ✓ On-premise deployment
  ✓ Custom model training
  ✓ 24/7 dedicated support
```

### Use Case 3: Pay-As-You-Go

**Goal**: No subscriptions, pure usage-based

```
Prepaid Credits
  - Buy 10,000 credits for $12
  - Buy 100,000 credits for $110
  - Buy 1,000,000 credits for $1,000

Usage Rates (with markup):
  - GPT-3.5: $0.002 per 1k tokens (2x OpenAI)
  - GPT-4: $0.06 per 1k tokens (2x OpenAI)
  - Claude-3-Sonnet: $0.006 per 1k tokens (2x Anthropic)
  - Claude-3-Opus: $0.03 per 1k tokens (2x Anthropic)

No monthly fees, credits never expire
```

### Use Case 4: Industry-Specific

**Goal**: Specialized packages for different industries

```
Healthcare Pro - $149/mo
  ✓ HIPAA-compliant infrastructure
  ✓ Medical terminology models
  ✓ EHR integration
  ✓ Patient data encryption
  ✓ Audit logging

Legal Pro - $199/mo
  ✓ Legal research access
  ✓ Case law database
  ✓ Contract analysis
  ✓ eDiscovery tools
  ✓ Attorney-client privilege protection

Finance Pro - $249/mo
  ✓ Real-time market data
  ✓ Financial modeling
  ✓ Risk analysis
  ✓ SEC filing analysis
  ✓ Compliance reporting
```

---

## Best Practices

### 1. Pricing Psychology

**Recommended Tier Structure**:
```
Free → Starter → Professional → Team → Enterprise
$0     $19       $49             $149    Custom

Why?
- Free tier: Lead generation
- Starter: Converts free users ($19 is impulse buy)
- Professional: Your sweet spot (50-70% of revenue)
- Team: Upsell for growing companies
- Enterprise: High-value custom deals
```

**Pricing Anchoring**:
- Show "Most Popular" badge on Professional tier
- Annual plans save 16-20% (2 months free)
- Show "Save $X/year" to highlight discount

### 2. Feature Distribution

**The 80/20 Rule**:
```
Free Tier:
  - 20% of features
  - Core functionality only
  - Enough to demonstrate value

Starter Tier:
  - 50% of features
  - Removes most frustrating limits
  - Good value for solo users

Professional Tier:
  - 80% of features
  - Everything most users need
  - Best value per dollar

Enterprise Tier:
  - 100% of features + custom
  - Unlimited everything
  - White-glove service
```

### 3. Credit Allocation

**Monthly Allocation Strategy**:
```python
# Allocate credits at start of billing cycle
def allocate_monthly_credits(user_id, tier_code):
    tier = get_tier(tier_code)

    # Calculate credit allocation
    # Assumption: $1 = 1000 credits
    monthly_credits = tier.price_monthly * 1000

    # Add to user balance
    credit_manager.allocate(
        user_id=user_id,
        amount=monthly_credits,
        source=f"monthly_allocation_{tier_code}",
        metadata={"tier": tier_code}
    )

    # Reset usage counters
    reset_usage_counters(user_id)
```

**Bonus Credits**:
```python
# Referral bonus
credit_manager.allocate(
    user_id=referrer_id,
    amount=5000,  # $5 bonus
    source="referral_bonus"
)

# First-time user bonus
credit_manager.allocate(
    user_id=new_user_id,
    amount=1000,  # $1 bonus
    source="welcome_bonus"
)
```

### 4. Usage Limits & Throttling

**Prevent Abuse**:
```python
# Check rate limits
async def check_rate_limit(user_id, tier_code):
    tier = get_tier(tier_code)

    # Get current usage this month
    usage = await get_monthly_usage(user_id)

    # Check API call limit
    if usage.api_calls >= tier.api_calls_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly API limit reached ({tier.api_calls_limit} calls). Upgrade to continue."
        )

    # Check credit balance
    balance = await credit_manager.get_balance(user_id)
    if balance <= 0:
        raise HTTPException(
            status_code=402,
            detail="Insufficient credits. Please purchase more credits."
        )
```

**Soft Limits (Warnings)**:
```python
# Send warning at 80% usage
if usage.api_calls >= tier.api_calls_limit * 0.8:
    await send_email_notification(
        user_id,
        subject="Usage Warning: 80% of API Calls Used",
        template="usage_warning",
        data={"remaining": tier.api_calls_limit - usage.api_calls}
    )
```

### 5. Migration Strategy

**Upgrading Users**:
```python
# User upgrades from Starter to Professional
async def upgrade_tier(user_id, from_tier, to_tier):
    # Calculate prorated credit
    days_remaining = get_days_remaining_in_billing_cycle(user_id)
    total_days = get_billing_cycle_length(user_id)
    proration_factor = days_remaining / total_days

    # Refund unused portion of old tier
    refund = from_tier.price_monthly * proration_factor

    # Charge for new tier (prorated)
    charge = to_tier.price_monthly * proration_factor

    # Process payment
    net_charge = charge - refund
    if net_charge > 0:
        await stripe.charge(user_id, net_charge)

    # Update tier
    await update_user_tier(user_id, to_tier.tier_code)

    # Allocate new monthly credits (prorated)
    new_credits = (to_tier.price_monthly * 1000) * proration_factor
    await credit_manager.allocate(
        user_id=user_id,
        amount=new_credits,
        source=f"upgrade_{from_tier.tier_code}_to_{to_tier.tier_code}"
    )
```

---

## Advanced Features

### 1. Dynamic Pricing

**Adjust prices based on demand**:
```python
# Peak pricing (higher costs during high demand)
def get_dynamic_price(model, time_of_day, user_tier):
    base_cost = get_model_base_cost(model)

    # Peak hours (9am-5pm): 1.5x markup
    if 9 <= time_of_day.hour <= 17:
        base_cost *= 1.5

    # Enterprise tier: always gets best price
    if user_tier == "enterprise":
        return base_cost

    # Professional tier: 1.2x markup
    elif user_tier == "professional":
        return base_cost * 1.2

    # Standard tier: 1.5x markup
    else:
        return base_cost * 1.5
```

### 2. Quota Management

**Rollover Credits**:
```python
# Allow unused credits to roll over
def rollover_unused_credits(user_id):
    balance = credit_manager.get_balance(user_id)
    tier = get_user_tier(user_id)

    # Max rollover: 50% of monthly allocation
    max_rollover = (tier.price_monthly * 1000) * 0.5

    # If balance exceeds max, cap it
    if balance > max_rollover:
        excess = balance - max_rollover
        credit_manager.deduct(
            user_id=user_id,
            amount=excess,
            service="rollover_cap",
            metadata={"reason": "Max rollover exceeded"}
        )
```

### 3. Spend Alerts

**Proactive Notifications**:
```python
# Monitor spending and alert users
async def monitor_spending(user_id):
    balance = await credit_manager.get_balance(user_id)
    usage = await get_monthly_usage(user_id)
    tier = await get_user_tier(user_id)

    # Alert thresholds
    if balance < 1000:  # Less than $1
        await send_alert(user_id, "low_balance", {"balance": balance})

    if usage.api_calls >= tier.api_calls_limit * 0.9:
        await send_alert(user_id, "approaching_limit", {
            "used": usage.api_calls,
            "limit": tier.api_calls_limit
        })
```

### 4. A/B Testing Tiers

**Experiment with pricing**:
```python
# Test two pricing models
def assign_test_group(user_id):
    # 50/50 split
    group = "A" if hash(user_id) % 2 == 0 else "B"

    if group == "A":
        # Control: Standard pricing
        return {
            "tier": "professional",
            "price": 49.00,
            "credits": 49000
        }
    else:
        # Test: Higher price, more credits
        return {
            "tier": "professional_premium",
            "price": 69.00,
            "credits": 80000  # Better value
        }
```

### 5. Custom Integrations

**Webhooks for Events**:
```python
# Notify external systems on events
WEBHOOK_EVENTS = [
    "tier.upgraded",
    "tier.downgraded",
    "credits.low",
    "credits.exhausted",
    "usage.exceeded"
]

async def trigger_webhook(user_id, event, data):
    webhooks = await get_user_webhooks(user_id)

    for webhook in webhooks:
        if event in webhook.subscribed_events:
            await httpx.post(
                webhook.url,
                json={
                    "event": event,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": data
                },
                headers={"X-Webhook-Signature": sign(data, webhook.secret)}
            )
```

---

## Summary

**What You Have**:
- ✅ Complete usage-based billing system
- ✅ LLM cost tracking and markup control
- ✅ Unlimited tier and feature management
- ✅ Credit system with prepaid and subscription models
- ✅ BYOK (Bring Your Own Key) support
- ✅ Visual admin interfaces for management
- ✅ Lago + Stripe integration for payments

**What You Can Do**:
- Create any tier structure (freemium, pay-as-you-go, enterprise)
- Set markup on LLM costs (passthrough, fixed %, per-model)
- Control which models each tier can access
- Track costs and revenue in real-time
- Offer credits, coupons, and bonuses
- Manage unlimited apps/features

**How to Use It**:
1. Create tiers in Subscription Management
2. Assign features to each tier
3. Set pricing (monthly/yearly)
4. Configure LLM markup in LiteLLM proxy
5. Users pay, credits deduct automatically
6. You profit from the markup!

**Next Steps**:
- Configure your markup percentage
- Create your initial tier structure
- Set up Stripe for credit purchases
- Launch and iterate based on metrics

---

## Questions?

**Common Questions**:

**Q: Can I change pricing later?**
A: Yes! Create a new Lago plan with new pricing, migrate users, grandfather existing users.

**Q: What's the ideal markup?**
A: 50-100% (1.5x to 2x) is standard for SaaS. Higher for specialized/custom models.

**Q: Should I offer BYOK?**
A: Yes for enterprise tiers. Users trust you more, you still profit from subscriptions.

**Q: How do I prevent abuse?**
A: Rate limits, credit caps, CAPTCHA on signup, monitor suspicious patterns.

**Q: Can I offer custom models?**
A: Yes! Add custom model endpoints in LiteLLM, restrict to specific tiers.

---

**This is a production-ready, enterprise-grade billing system. Use it to build your AI SaaS business!** 🚀
