# Admin Billing Guide

**Complete guide for administrators managing the Ops-Center billing system.**

This guide covers administrative tasks including configuring dynamic pricing, managing subscriptions, allocating credits, analyzing revenue, and troubleshooting billing issues.

---

## Table of Contents

1. [Admin Dashboard Overview](#admin-dashboard-overview)
2. [Dynamic Pricing Configuration](#dynamic-pricing-configuration)
3. [Credit Allocation & Management](#credit-allocation--management)
4. [Subscription Management](#subscription-management)
5. [BYOK Rule Management](#byok-rule-management)
6. [Revenue Analytics](#revenue-analytics)
7. [User Support & Refunds](#user-support--refunds)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Admin Dashboard Overview

### Accessing Admin Features

**Requirements:**
- Admin role in Keycloak (uchub realm)
- Logged in to Ops-Center

**Access:**
1. Login to https://unicorncommander.ai
2. Navigate to **Admin** → **Billing** in sidebar

### Dashboard Sections

```
┌─────────────────────────────────────────────────────────┐
│                  Billing Admin Dashboard                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📊 Revenue Overview                                    │
│  ├─ MRR: $15,840                                        │
│  ├─ ARR: $190,080                                       │
│  ├─ Active Subscriptions: 360                          │
│  └─ Churn Rate: 2.3%                                    │
│                                                          │
│  💳 Credit System                                       │
│  ├─ Total Allocated: 3,600,000 credits                 │
│  ├─ Total Used: 2,160,000 credits                      │
│  ├─ Utilization: 60%                                    │
│  └─ Users with BYOK: 145 (40%)                         │
│                                                          │
│  📈 Growth Metrics                                      │
│  ├─ New Subscriptions (30d): 28                        │
│  ├─ Upgrades (30d): 12                                 │
│  ├─ Downgrades (30d): 3                                │
│  └─ Cancellations (30d): 5                             │
│                                                          │
│  ⚙️ System Health                                       │
│  ├─ Lago API: ✅ Operational                           │
│  ├─ Stripe API: ✅ Operational                         │
│  ├─ Payment Success Rate: 98.5%                        │
│  └─ Webhook Delivery: 99.2%                            │
└─────────────────────────────────────────────────────────┘
```

---

## Dynamic Pricing Configuration

### Understanding Pricing Tiers

**Two Pricing Models:**

1. **Platform Tier** - Managed infrastructure (default)
   - Ops-Center handles all LLM provider keys
   - Simple pricing, no user configuration needed
   - Higher markup to cover infrastructure costs

2. **BYOK Tier** - Bring Your Own Key
   - Users provide their own API keys
   - Lower markup (5-10%) for platform usage
   - Users save 60-90% on AI costs

### Configuring Platform Pricing

#### Access Platform Rules

1. Navigate to **Admin** → **Pricing** → **Platform Rules**
2. View rules by tier

#### Example Platform Rule (Professional Tier)

```json
{
  "tier_code": "professional",
  "rule_type": "platform",
  "markup_value": "1.60",
  "markup_type": "multiplier",
  "description": "Standard 60% markup on provider costs",
  "provider_overrides": {
    "openrouter": {
      "markup_value": "1.50"
    },
    "openai": {
      "markup_value": "1.80"
    }
  },
  "is_active": true
}
```

**Field Explanations:**
- `markup_value: 1.60` = 60% markup (provider cost × 1.60)
- `provider_overrides` = Different markups per provider
- Lower override for OpenRouter (cheaper baseline)
- Higher override for OpenAI (premium provider)

#### Update Platform Pricing

**API Request:**
```bash
curl -X PUT \
  https://unicorncommander.ai/api/v1/pricing/rules/platform/professional \
  -H 'Cookie: session_token=<ADMIN_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "markup_value": "1.70",
    "description": "Increased to 70% markup for Q1 2025"
  }'
```

**When to Adjust:**
- 📈 **Increase markup** - Rising infrastructure costs, low margins
- 📉 **Decrease markup** - Competitive pressure, user retention
- 🎯 **Provider overrides** - Negotiate better rates, pass savings to users

---

### Configuring BYOK Pricing

#### Access BYOK Rules

1. Navigate to **Admin** → **Pricing** → **BYOK Rules**
2. Click **Create Rule** to add new provider

#### Example BYOK Rule (OpenRouter)

```json
{
  "provider": "openrouter",
  "rule_type": "byok",
  "markup_type": "percentage",
  "markup_value": "0.05",
  "min_charge": "0.001",
  "free_credits_monthly": "5.00",
  "applies_to_tiers": ["starter", "professional", "enterprise"],
  "rule_name": "OpenRouter Standard",
  "description": "5% platform fee on OpenRouter API costs",
  "priority": 10,
  "is_active": true
}
```

**Field Explanations:**
- `markup_type: percentage` = Apply percentage of provider cost
- `markup_value: 0.05` = 5% markup
- `min_charge: 0.001` = Minimum 0.1 cent per request
- `free_credits_monthly: 5.00` = First $5 free each month per user
- `applies_to_tiers` = Which subscription tiers can use this
- `priority: 10` = Rule matching priority (higher = first)

#### Create BYOK Rule

**Via API:**
```bash
curl -X POST \
  https://unicorncommander.ai/api/v1/pricing/rules/byok \
  -H 'Cookie: session_token=<ADMIN_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "provider": "huggingface",
    "markup_type": "percentage",
    "markup_value": "0.03",
    "min_charge": "0.001",
    "free_credits_monthly": "10.00",
    "applies_to_tiers": ["professional", "enterprise"],
    "rule_name": "HuggingFace Professional",
    "description": "3% fee for HuggingFace inference",
    "priority": 5
  }'
```

**Via UI:**
1. Click **Create BYOK Rule**
2. Fill in form:
   - **Provider:** `huggingface`
   - **Markup Type:** `Percentage`
   - **Markup Value:** `3%`
   - **Min Charge:** `$0.001`
   - **Free Credits:** `$10/month`
   - **Tiers:** Check Professional, Enterprise
   - **Priority:** `5`
3. Click **Save**

#### When to Create Rules

**New Provider Support:**
- User requests support for Anthropic Direct
- Check Anthropic API pricing
- Calculate appropriate markup (typically 3-10%)
- Create rule with appropriate free credits

**Promotional Pricing:**
- Launch promotion: "First $10 free on HuggingFace"
- Increase `free_credits_monthly` to `10.00`
- Set expiration date (optional)
- Monitor usage and adjust

**Competitive Response:**
- Competitor offers 2% markup on OpenRouter
- Review your margins
- Adjust `markup_value` from 0.05 → 0.03
- Announce change to users

---

### Pricing Strategy Examples

#### Scenario 1: Encourage BYOK Adoption

**Goal:** Get more users to use BYOK (reduces infrastructure costs)

**Actions:**
1. **Increase platform markup** to make managed tier less attractive
   ```json
   {
     "tier_code": "professional",
     "markup_value": "1.80"  // Was 1.60, now 80% markup
   }
   ```

2. **Decrease BYOK markup** to make it more attractive
   ```json
   {
     "provider": "openrouter",
     "markup_value": "0.03"  // Was 0.05, now 3% markup
   }
   ```

3. **Increase free credits** for popular providers
   ```json
   {
     "provider": "openrouter",
     "free_credits_monthly": "10.00"  // Was $5, now $10 free
   }
   ```

**Expected Result:**
- BYOK adoption increases from 40% → 60%
- Infrastructure costs decrease
- Margins improve on BYOK tier

---

#### Scenario 2: Premium Positioning

**Goal:** Position as high-quality managed service

**Actions:**
1. **Moderate platform markup** with excellent service
   ```json
   {
     "tier_code": "professional",
     "markup_value": "1.60"  // 60% markup
   }
   ```

2. **Premium support** included in price
   - 24-hour response time
   - Dedicated Slack channel
   - Monthly usage reviews

3. **Value-added features:**
   - Advanced analytics
   - Cost optimization recommendations
   - Automatic model selection

**Expected Result:**
- Users willing to pay premium for managed experience
- Lower churn rate
- Higher ARPU (Average Revenue Per User)

---

#### Scenario 3: Freemium Growth

**Goal:** Maximize user acquisition, monetize later

**Actions:**
1. **Generous free tier**
   ```json
   {
     "tier_code": "trial",
     "price_monthly": 0.00,  // Free forever
     "credits_monthly": 1000  // Decent allowance
   }
   ```

2. **Low BYOK markup** (almost cost-neutral)
   ```json
   {
     "markup_value": "0.01"  // Only 1% markup
   }
   ```

3. **Upgrade prompts** at 80% credit usage

**Expected Result:**
- High signup rate
- Low initial revenue
- Upgrade conversion rate critical for success

---

## Credit Allocation & Management

### Manual Credit Allocation

#### When to Allocate Credits

**Common Reasons:**
- 🎁 **Promotional campaigns** - "First 1000 users get 500 bonus credits"
- 🆘 **Service outage compensation** - Reimburse for downtime
- 💝 **Customer retention** - Reward loyal customers
- 🐛 **Bug compensation** - Reimburse for platform errors
- 🎉 **Referral bonuses** - Reward users who bring new customers

#### Allocate Credits (Single User)

**Via API:**
```bash
curl -X POST \
  https://unicorncommander.ai/api/v1/credits/allocate \
  -H 'Cookie: session_token=<ADMIN_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
    "amount": "1000.00",
    "source": "retention_bonus",
    "metadata": {
      "reason": "6-month anniversary bonus",
      "campaign": "loyal_user_2025_q1",
      "approved_by": "admin@unicorncommander.ai"
    }
  }'
```

**Via UI:**
1. Go to **Admin** → **Users**
2. Search for user by email
3. Click **Allocate Credits** button
4. Fill in form:
   - **Amount:** `1000`
   - **Source:** `Retention Bonus`
   - **Reason:** `6-month anniversary`
5. Click **Allocate**

**Response:**
```json
{
  "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
  "balance": "11000.50",  // Was 10000.50, now 11000.50
  "allocated_monthly": "10000.00",
  "bonus_credits": "1000.00",
  "reset_date": "2025-02-01T00:00:00Z"
}
```

**Email Notification:**
User receives email:
```
Subject: 1,000 Bonus Credits Added to Your Account!

Hi Admin,

Great news! We've added 1,000 bonus credits to your account.

Reason: 6-month anniversary bonus

Your new balance: 11,000 credits

These bonus credits don't expire on your monthly reset!

Thanks for being a loyal customer.
```

---

#### Bulk Credit Allocation

**Use Case:** Promotional campaign for 500 users

**Via CSV Import:**

1. Prepare CSV file (`credit_allocation.csv`):
   ```csv
   user_id,amount,source,reason
   user_001,500,promo_2025_q1,New Year promotion
   user_002,500,promo_2025_q1,New Year promotion
   user_003,500,promo_2025_q1,New Year promotion
   ...
   ```

2. Navigate to **Admin** → **Credits** → **Bulk Allocate**

3. Upload CSV file

4. Review summary:
   ```
   Total Users: 500
   Total Credits: 250,000 credits
   Cost: $250 (estimated revenue impact)

   Proceed with allocation?
   [Cancel] [Confirm]
   ```

5. Click **Confirm**

6. System processes allocations (may take 1-2 minutes)

7. View results:
   ```
   ✅ Success: 498 allocations
   ❌ Failed: 2 allocations

   Failed Users:
   - user_234: User not found
   - user_456: Invalid user_id format
   ```

---

### Credit Deductions (Manual)

**When to Deduct:**
- 🚫 Abuse detected (credit farming, ToS violation)
- ❌ Accidental over-allocation
- 🔄 Manual correction for billing errors

**⚠️ Use Sparingly:** Most deductions are automatic via usage metering.

**API Request:**
```bash
curl -X POST \
  https://unicorncommander.ai/api/v1/credits/deduct \
  -H 'Cookie: session_token=<ADMIN_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
    "amount": "500.00",
    "service": "manual_deduction",
    "metadata": {
      "reason": "ToS violation - credit farming detected",
      "ticket_id": "SUPPORT-2025-001",
      "reviewed_by": "admin@unicorncommander.ai"
    }
  }'
```

---

### Credit Refunds

**When to Refund:**
- 🐛 Platform bug caused incorrect charges
- 🔥 Service outage prevented usage
- 🤝 Goodwill gesture for poor experience
- ❌ Duplicate charge

**Process:**

1. **Investigate Issue**
   - Review user's transaction history
   - Verify the complaint (check logs)
   - Calculate fair refund amount

2. **Issue Refund**
   ```bash
   curl -X POST \
     https://unicorncommander.ai/api/v1/credits/refund \
     -H 'Cookie: session_token=<ADMIN_TOKEN>' \
     -H 'Content-Type: application/json' \
     -d '{
       "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
       "amount": "150.00",
       "reason": "Service outage on 2025-01-14, 3 hours downtime",
       "metadata": {
         "incident_id": "INC-2025-001",
         "downtime_hours": 3,
         "avg_hourly_usage": 50
       }
     }'
   ```

3. **Document**
   - Add note to user's account
   - Log in support ticket
   - Update incident report

4. **Communicate**
   ```
   Subject: Credit Refund Issued - Apology for Service Outage

   Hi Admin,

   We sincerely apologize for the service outage on January 14th.

   As compensation, we've added 150 credits back to your account.

   Your new balance: 10,150 credits

   Incident ID: INC-2025-001
   Duration: 3 hours (2pm - 5pm PST)

   We've taken steps to prevent this from happening again.

   Thank you for your patience and understanding.
   ```

---

## Subscription Management

### View All Subscriptions

**Navigate:** **Admin** → **Subscriptions** → **All Subscriptions**

**Dashboard View:**
```
┌─────────────────────────────────────────────────────────────┐
│ Total Subscriptions: 360                                     │
│ ├─ Trial: 45 (12.5%)                                        │
│ ├─ Starter: 120 (33.3%)                                     │
│ ├─ Professional: 180 (50.0%)  ⭐ Most Popular               │
│ └─ Enterprise: 15 (4.2%)                                    │
│                                                              │
│ Subscription Status:                                         │
│ ├─ Active: 348 (96.7%)                                      │
│ ├─ Paused: 5 (1.4%)                                         │
│ ├─ Past Due: 4 (1.1%)                                       │
│ └─ Canceled: 3 (0.8%)                                       │
└─────────────────────────────────────────────────────────────┘

Filter: [All] [Active] [Past Due] [Canceled]
Sort by: [Created Date ▼] [MRR] [Tier] [Status]

┌─────────────────────────────────────────────────────────────┐
│ User              │ Tier         │ MRR   │ Status  │ Actions│
├───────────────────┼──────────────┼───────┼─────────┼────────┤
│ admin@example.com    │ Professional │ $49   │ Active  │ [...]  │
│ john@example.com  │ Enterprise   │ $99   │ Active  │ [...]  │
│ jane@company.com  │ Starter      │ $19   │ Past Due│ [...]  │
│ bob@startup.io    │ Professional │ $49   │ Paused  │ [...]  │
└─────────────────────────────────────────────────────────────┘
```

---

### Handle Past Due Subscriptions

**What Happened:**
- Payment failed (declined card, insufficient funds)
- User needs to update payment method
- Lago/Stripe automatically retries payment

**Process:**

1. **Identify Past Due**
   - Filter: **Status** = `Past Due`
   - Sort by: **Days Past Due** (descending)

2. **Check Retry Status**
   ```
   User: jane@company.com
   Status: Past Due (3 days)
   Last Attempt: Jan 12, 2025
   Next Retry: Jan 15, 2025
   Failure Reason: Insufficient funds
   ```

3. **Contact User** (automated email sent by system)
   ```
   Subject: Payment Failed - Update Payment Method

   Hi Jane,

   Your payment of $49.00 for Professional subscription failed.

   Reason: Insufficient funds

   Please update your payment method to avoid service interruption:
   https://unicorncommander.ai/billing/payment-methods

   We'll retry on Jan 15, 2025.

   If payment continues to fail, your subscription will be suspended.
   ```

4. **Manual Follow-up** (if automated retries fail after 7 days)
   - Send personal email
   - Offer payment plan if financial hardship
   - Consider temporary credit extension

5. **Suspend or Cancel** (after 14 days)
   - Suspend account (disable API access)
   - Preserve data for 30 days
   - Send final notice with reactivation instructions

---

### Force Subscription Update (Admin Override)

**Use Case:** User needs immediate tier change without payment flow

**Scenarios:**
- Enterprise deal closed, needs instant access
- Customer support escalation
- Beta tester special arrangement

**API Request:**
```bash
curl -X PUT \
  https://unicorncommander.ai/api/v1/admin/subscriptions/7a6bfd31 \
  -H 'Cookie: session_token=<ADMIN_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "tier": "enterprise",
    "credits_allocated": 999999,
    "bypass_payment": true,
    "notes": "Enterprise deal - 6-month pilot program",
    "expires_at": "2025-07-01T00:00:00Z"
  }'
```

**⚠️ Caution:** This bypasses normal billing flow. Use only when necessary and document reason.

---

## BYOK Rule Management

### List All BYOK Rules

**API Request:**
```bash
curl -X GET \
  'https://unicorncommander.ai/api/v1/pricing/rules/byok' \
  -H 'Cookie: session_token=<ADMIN_TOKEN>'
```

**Response:**
```json
{
  "rules": [
    {
      "id": "rule_openrouter",
      "provider": "openrouter",
      "markup_value": "0.05",
      "min_charge": "0.001",
      "free_credits_monthly": "5.00",
      "priority": 10,
      "is_active": true,
      "created_at": "2024-12-01T00:00:00Z"
    },
    {
      "id": "rule_huggingface",
      "provider": "huggingface",
      "markup_value": "0.03",
      "min_charge": "0.001",
      "free_credits_monthly": "10.00",
      "priority": 5,
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 2
}
```

---

### Update BYOK Rule

**Scenario:** Adjust OpenRouter markup from 5% → 3%

**API Request:**
```bash
curl -X PUT \
  https://unicorncommander.ai/api/v1/pricing/rules/byok/rule_openrouter \
  -H 'Cookie: session_token=<ADMIN_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "markup_value": "0.03",
    "description": "Reduced to 3% to compete with market rates"
  }'
```

**Response:**
```json
{
  "id": "rule_openrouter",
  "provider": "openrouter",
  "markup_value": "0.03",
  "description": "Reduced to 3% to compete with market rates",
  "updated_at": "2025-01-15T10:30:00Z",
  "updated_by": "admin@unicorncommander.ai"
}
```

**Communicate Change:**
```
Subject: Great News - Lower BYOK Fees!

We've reduced our OpenRouter BYOK markup from 5% → 3%.

This means even more savings when you use your own API keys!

Example savings:
- 10,000 tokens on Claude 3.5 Sonnet
- Provider cost: $0.003
- Old platform fee: $0.00015 (5%)
- New platform fee: $0.00009 (3%)
- You save: 40% on platform fees!

Start saving: https://unicorncommander.ai/settings/byok
```

---

### Deactivate BYOK Provider

**Scenario:** Provider API changed, need to disable temporarily

**API Request:**
```bash
curl -X PUT \
  https://unicorncommander.ai/api/v1/pricing/rules/byok/rule_huggingface \
  -H 'Cookie: session_token=<ADMIN_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "is_active": false,
    "description": "Disabled due to HuggingFace API v3 migration"
  }'
```

**Communicate:**
```
Subject: Temporary Service Interruption - HuggingFace BYOK

We've temporarily disabled HuggingFace BYOK while we update our integration for their new API.

Affected users: 23
Expected resolution: 2-3 business days

Alternative:
- Use OpenRouter BYOK (includes HuggingFace models)
- Use Platform tier (no interruption)

We'll notify you when HuggingFace BYOK is restored.
```

---

## Revenue Analytics

### Key Metrics to Track

#### Monthly Recurring Revenue (MRR)

**Formula:** `Sum of all active monthly subscriptions`

```sql
SELECT
  SUM(
    CASE
      WHEN tier = 'trial' THEN 1.00
      WHEN tier = 'starter' THEN 19.00
      WHEN tier = 'professional' THEN 49.00
      WHEN tier = 'enterprise' THEN 99.00
    END
  ) as mrr
FROM subscriptions
WHERE status = 'active';
```

**Result:** `$15,840 MRR`

**Tracking:**
- Track daily (detect trends early)
- Compare month-over-month: `(Jan MRR - Dec MRR) / Dec MRR * 100`
- Target growth: 10-20% monthly for early-stage SaaS

---

#### Annual Recurring Revenue (ARR)

**Formula:** `MRR × 12`

```
ARR = $15,840 × 12 = $190,080
```

**Use Cases:**
- Investor reporting
- Company valuation (SaaS multiple: 5-10× ARR)
- Long-term planning

---

#### Average Revenue Per User (ARPU)

**Formula:** `Total MRR / Active Users`

```
ARPU = $15,840 / 360 users = $44/month/user
```

**Insights:**
- Higher ARPU = Users on premium tiers
- Lower ARPU = More free/trial users
- Target ARPU depends on positioning

**Segmented ARPU:**
```
Trial users: $1/month
Starter users: $19/month
Professional users: $49/month
Enterprise users: $99/month
```

---

#### Customer Lifetime Value (LTV)

**Formula:** `ARPU × Average Customer Lifespan (months)`

```
Assumptions:
- ARPU = $44/month
- Average lifespan = 24 months (based on churn rate)

LTV = $44 × 24 = $1,056
```

**Compare to Customer Acquisition Cost (CAC):**
```
LTV:CAC Ratio = $1,056 / $150 = 7:1

Healthy SaaS: 3:1 or higher
Our ratio: 7:1 (excellent!)
```

---

#### Churn Rate

**Formula:** `(Canceled Subscriptions / Total Active Start of Month) × 100`

```
Month: January 2025
Active at start: 355
Canceled during month: 8
New signups: 13

Churn Rate = (8 / 355) × 100 = 2.25%
```

**Benchmarks:**
- < 2% - Excellent
- 2-5% - Good
- 5-10% - Acceptable
- > 10% - Concerning

**Actions if High Churn:**
- Interview churned customers (exit surveys)
- Identify patterns (tier, usage, tenure)
- Improve onboarding
- Add more value
- Consider win-back campaigns

---

### Revenue Dashboards

#### Monthly Revenue Report

**Query:**
```sql
SELECT
  DATE_TRUNC('month', created_at) as month,
  COUNT(*) as new_subscriptions,
  SUM(
    CASE
      WHEN tier = 'trial' THEN 1.00
      WHEN tier = 'starter' THEN 19.00
      WHEN tier = 'professional' THEN 49.00
      WHEN tier = 'enterprise' THEN 99.00
    END
  ) as new_mrr,
  (SELECT COUNT(*) FROM subscriptions WHERE status = 'canceled'
   AND canceled_at BETWEEN DATE_TRUNC('month', $1)
   AND DATE_TRUNC('month', $1) + INTERVAL '1 month') as churned,
  (SELECT SUM(price) FROM subscriptions WHERE status = 'canceled'
   AND canceled_at BETWEEN DATE_TRUNC('month', $1)
   AND DATE_TRUNC('month', $1) + INTERVAL '1 month') as churned_mrr
FROM subscriptions
WHERE created_at >= DATE_TRUNC('month', $1)
  AND created_at < DATE_TRUNC('month', $1) + INTERVAL '1 month'
GROUP BY month;
```

**Result:**
```
Month: January 2025
New Subscriptions: 28
New MRR: +$1,372
Churned Subscriptions: 8
Churned MRR: -$296
Net MRR Growth: +$1,076 (+7.3%)
```

---

#### Tier Distribution

**Query:**
```sql
SELECT
  tier,
  COUNT(*) as count,
  ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 1) as percentage,
  SUM(
    CASE
      WHEN tier = 'trial' THEN 1.00
      WHEN tier = 'starter' THEN 19.00
      WHEN tier = 'professional' THEN 49.00
      WHEN tier = 'enterprise' THEN 99.00
    END
  ) as mrr
FROM subscriptions
WHERE status = 'active'
GROUP BY tier
ORDER BY count DESC;
```

**Result:**
```
┌────────────────┬───────┬────────────┬─────────┐
│ Tier           │ Count │ Percentage │ MRR     │
├────────────────┼───────┼────────────┼─────────┤
│ Professional   │ 180   │ 50.0%      │ $8,820  │
│ Starter        │ 120   │ 33.3%      │ $2,280  │
│ Trial          │ 45    │ 12.5%      │ $45     │
│ Enterprise     │ 15    │ 4.2%       │ $1,485  │
└────────────────┴───────┴────────────┴─────────┘
```

**Insights:**
- Professional is most popular (50%)
- Trial → Starter conversion needs improvement
- Enterprise is small but high-value

---

## User Support & Refunds

### Handling Refund Requests

#### Refund Policy (Recommended)

**Full Refunds:**
- ✅ Within 7 days of initial subscription
- ✅ Service outages > 4 hours
- ✅ Billing errors (duplicate charges)
- ✅ Account compromise (fraud)

**Partial Refunds:**
- ✅ Service outages < 4 hours (prorated)
- ✅ Downgrade requests (prorated for remainder)
- ✅ Early cancellation (special circumstances)

**No Refunds:**
- ❌ Unused credits (explicitly non-refundable)
- ❌ Change of mind after 7 days
- ❌ ToS violations
- ❌ User error (incorrect usage)

#### Process Refund

**Step 1: Verify Request**
- Check subscription history
- Verify payment date
- Confirm refund eligibility

**Step 2: Calculate Amount**
```python
# Full refund
refund_amount = last_payment_amount

# Prorated refund (early cancel)
days_remaining = (period_end - today).days
days_in_period = 30
refund_amount = last_payment_amount * (days_remaining / days_in_period)

# Partial refund (outage)
outage_hours = 3
hours_in_month = 720  # 30 days * 24 hours
refund_amount = monthly_price * (outage_hours / hours_in_month)
```

**Step 3: Issue via Stripe**
```bash
# Stripe CLI or Dashboard
stripe refunds create \
  --charge=ch_abc123 \
  --amount=4900 \  # $49.00 in cents
  --reason="requested_by_customer" \
  --metadata[reason]="Service outage on 2025-01-14"
```

**Step 4: Document**
- Add note to user's account
- Update support ticket
- Log in refund tracker

**Step 5: Communicate**
```
Subject: Refund Processed - $49.00

Hi Jane,

Your refund of $49.00 has been processed.

Refund Details:
- Amount: $49.00
- Reason: Service outage on January 14, 2025
- Original Charge: Jan 1, 2025
- Refund Date: Jan 15, 2025
- Expected in account: 5-10 business days

Ticket ID: SUP-2025-012

We apologize for the inconvenience.
```

---

### Credit Goodwill Gestures

**Alternative to Refunds:** Offer bonus credits instead of cash refunds

**Advantages:**
- ✅ Retains user on platform (vs. cash refund = potential churn)
- ✅ Cheaper for company (credits cost < face value)
- ✅ User gets more value (100 credits ≈ $0.10 cost, $0.10 value to user)

**Example:**
```
User requests $49 refund due to poor experience.

Option A: Cash refund
- Refund: $49
- User may churn
- Lost revenue: $49

Option B: Credit bonus
- Bonus: 1,000 credits (face value $100)
- Cost to company: ~$15 (depends on usage)
- User stays on platform
- User perception: "Wow, double my money!"
- User likely to use more services = potential upsell
```

**Offer:**
```
Subject: We'd Like to Make This Right

Hi Admin,

We're sorry your experience didn't meet expectations.

Instead of a $49 refund, we'd like to offer you:

🎁 1,000 BONUS CREDITS (Value: $100)

That's more than double your subscription cost!

These credits:
- Never expire
- Can be used on any service
- Stack with your monthly allocation

We'd love another chance to serve you.

Accept bonus credits? [Yes, Apply Credits]
Prefer cash refund instead? [Request Refund]
```

**Conversion Rate:** 70-80% of users choose credits over refund

---

## Troubleshooting

### Common Issues

#### Issue: Webhook Delivery Failing

**Symptoms:**
- Subscriptions not updating in Ops-Center
- Payments processed in Stripe but not reflected
- Invoice events not triggering

**Diagnosis:**
```bash
# Check webhook logs
docker logs ops-center-direct | grep webhook | tail -50

# Check Stripe webhook dashboard
# https://dashboard.stripe.com/test/webhooks

# Check Lago webhook logs
# https://billing.unicorncommander.ai/admin (login required)
```

**Solution:**
1. **Verify webhook endpoints configured:**
   ```bash
   # Stripe
   curl https://api.stripe.com/v1/webhook_endpoints \
     -u sk_test_...:

   # Lago
   curl https://billing-api.unicorncommander.ai/webhooks \
     -H "Authorization: Bearer d87f40d7..."
   ```

2. **Test webhook delivery:**
   ```bash
   # Stripe CLI
   stripe trigger payment_intent.succeeded

   # Check ops-center logs
   docker logs ops-center-direct --tail 20
   ```

3. **Retry failed webhooks:**
   - Stripe Dashboard → Webhooks → Failed Events → Retry
   - Lago Dashboard → Webhooks → Failed Events → Resend

---

#### Issue: Incorrect Credit Calculation

**Symptoms:**
- User reports being charged wrong amount
- Credits don't match expected cost
- Usage reports differ from actual credits deducted

**Diagnosis:**
```bash
# Get user's transactions
curl -X GET \
  'https://unicorncommander.ai/api/v1/credits/transactions?limit=100' \
  -H 'Cookie: session_token=<USER_TOKEN>' \
  | jq '.[] | select(.transaction_type == "deducted") | {model, tokens: .metadata.tokens, cost: .cost_breakdown}'

# Compare with pricing rules
curl -X POST \
  https://unicorncommander.ai/api/v1/pricing/calculate/comparison \
  -H 'Cookie: session_token=<ADMIN_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "provider": "openrouter",
    "model": "anthropic/claude-3-5-sonnet",
    "tokens_used": 10000,
    "user_tier": "professional"
  }'
```

**Solution:**
1. **Review pricing rule:**
   - Check markup percentages
   - Verify provider overrides
   - Confirm rule priority

2. **Recalculate cost:**
   ```python
   # Expected cost
   base_cost = (tokens / 1000) * model_price_per_1k
   platform_markup = base_cost * markup_percentage
   total_cost = base_cost + platform_markup

   # Compare to actual deduction
   actual_deduction = transaction.cost_breakdown
   difference = total_cost - actual_deduction
   ```

3. **Issue correction:**
   - If overcharged: Issue credit refund
   - If undercharged: Note for future (don't retroactively charge)
   - Update pricing rule if systemic issue

---

#### Issue: Payment Declined Multiple Times

**Symptoms:**
- User's subscription shows "Past Due"
- Multiple failed payment attempts
- User claims card is valid

**Diagnosis:**
```bash
# Check Stripe payment attempts
curl https://api.stripe.com/v1/charges?customer=cus_abc123 \
  -u sk_test_...: \
  | jq '.data[] | select(.status == "failed")'

# Common failure reasons:
# - insufficient_funds
# - card_declined
# - expired_card
# - incorrect_cvc
# - processing_error
```

**Solutions:**

**1. Soft Decline (insufficient_funds, temporary):**
- Email user with retry date
- Offer to delay retry by 3-5 days
- Maintain service during grace period

**2. Hard Decline (card_declined, expired_card):**
- Prompt user to update payment method
- Provide direct link: `https://unicorncommander.ai/billing/payment-methods`
- If no response after 7 days, suspend subscription

**3. Fraud Detection (card_issuer flagged):**
- User may need to call their bank
- Provide transaction details (amount, date, merchant name)
- Suggest trying different payment method

**4. Processing Error (Stripe issue):**
- Check Stripe status page: https://status.stripe.com
- Wait for Stripe to resolve
- Retry payment manually after resolution

---

## Best Practices

### Pricing Strategy

**1. Anchor with Premium Tier**
```
❌ Bad: Show Trial first (sets low anchor)
✅ Good: Show Professional first (high anchor)

Layout:
[Professional - $49] [Starter - $19] [Trial - $1]
           ⭐ MOST POPULAR

Users perceive Professional as "normal" price.
Starter looks like great deal (vs. Professional).
Trial for risk-free testing.
```

---

**2. Value-Based Pricing**
```
❌ Don't say: "10,000 credits/month"
✅ Do say: "~200 GPT-4 conversations" or "~1,600 images"

Users understand value, not abstract credits.
```

---

**3. Decoy Pricing**
```
Trial: $1/week (700 credits)
Starter: $19/month (1,000 credits)  ← Decoy
Professional: $49/month (10,000 credits)  ← Target

Starter is poor value (only 42% more credits for 19× price).
Makes Professional look like incredible deal.
Most users skip Starter → go straight to Professional.
```

---

**4. Annual Discount**
```
Monthly: $49/month = $588/year
Annual: $490/year (save $98, 17% off)

Sweet spot: 15-20% discount for annual
Too low (<10%): Not compelling
Too high (>25%): Lose monthly revenue
```

---

### Credit Allocation Philosophy

**1. Conservative Initial Allocation**
```
Trial: 700 credits (enough to evaluate, not abuse)
Starter: 1,000 credits (light usage)
Professional: 10,000 credits (heavy usage)
Enterprise: Unlimited (no worries)
```

Better to have users upgrade (good problem) than over-allocate (revenue loss).

---

**2. Smart Warnings**
```
At 75% usage: "You're using credits faster than expected. Consider upgrading?"
At 90% usage: "You'll run out in ~5 days. Upgrade now to avoid interruption."
At 100% usage: "Out of credits. Upgrade to continue."
```

Warnings drive upgrades without being annoying.

---

**3. Promotional Credits**
```
Frequency: Quarterly or special events
Amount: 500-1,000 credits (enough to be meaningful, not abuse)
Expiration: 60-90 days (creates urgency)
Targeting: Inactive users (re-engagement) or power users (retention)
```

---

### Communication Best Practices

**1. Proactive > Reactive**
```
❌ Wait for user to discover issue
✅ Email immediately when problem detected

Examples:
- Payment failed → Email within 1 hour
- Service outage → Email within 15 minutes + status page
- Pricing change → Email 30 days advance notice
```

---

**2. Transparency**
```
Show users:
✅ Exact credit costs before requests
✅ Real-time usage tracking
✅ Pricing breakdown (base cost + markup)
✅ Comparison with alternatives (BYOK savings)

Users appreciate transparency → builds trust.
```

---

**3. Explain Changes**
```
When adjusting pricing:
❌ "Prices are changing."
✅ "Infrastructure costs increased 15% this year.
   We're adjusting pricing to maintain service quality.
   Your new price: $X (increase of $Y)
   Effective: 30 days from today"

Explain why → users more accepting.
```

---

### Monitoring & Alerts

**Set Up Alerts for:**
```
Critical:
- Payment failure rate > 5%
- Webhook delivery failure rate > 2%
- Credit allocation errors
- Duplicate charges detected
- Subscription sync issues (Lago ↔ Ops-Center)

Important:
- Churn rate increase > 1% month-over-month
- MRR growth < 5% month-over-month
- Trial → Paid conversion rate < 10%
- Average credit utilization < 40% (users not using product)
- BYOK adoption rate changes significantly

Informational:
- Daily/weekly revenue reports
- New subscriptions
- Upgrade/downgrade trends
- Credit usage patterns
```

---

**Alert Channels:**
```
Critical → PagerDuty / Slack #critical-alerts
Important → Email + Slack #billing-alerts
Informational → Daily/weekly email digest
```

---

### Documentation & Training

**Keep Updated:**
- ✅ Admin runbooks (this document)
- ✅ User FAQ
- ✅ API documentation
- ✅ Support team scripts
- ✅ Pricing calculator spreadsheet

**Train Team:**
- Quarterly billing system review
- New feature demos
- Common issue walkthroughs
- Lago/Stripe dashboard tutorials

---

## Conclusion

Billing is the **lifeblood of your SaaS**. Master it, and your company thrives.

**Key Takeaways:**
- 💰 **Pricing** - Strategic, value-based, regularly reviewed
- 🎁 **Credits** - Conservative initial allocation, generous promotions
- 📊 **Analytics** - Track MRR, churn, LTV:CAC obsessively
- 🛟 **Support** - Proactive, transparent, fair
- 🔧 **Maintenance** - Monitor webhooks, pricing rules, system health

**Resources:**
- 📧 Support: support@magicunicorn.tech
- 📚 Docs: https://unicorncommander.ai/docs
- 🐛 Report Issues: https://git.unicorncommander.ai/issues

---

**Last Updated:** November 12, 2025
**Version:** 1.0.0
