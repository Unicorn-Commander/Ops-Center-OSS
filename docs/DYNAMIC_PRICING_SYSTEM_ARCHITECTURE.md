# Dynamic Pricing Configuration System Architecture

**Date**: January 12, 2025
**Status**: Design Document
**Author**: System Architecture Designer
**Version**: 1.0

---

## Executive Summary

This document describes the comprehensive dynamic pricing configuration system for UC-Cloud Ops-Center. The system enables administrators to configure pricing for BYOK (Bring Your Own Key) usage, Platform keys, and credit packages through a user-friendly GUI without code deployments.

### Key Features

1. **BYOK Pricing Model**: Configure small markups (5-10%) on user-provided API keys
2. **Platform Key Pricing**: Dynamic tier-based multipliers with admin-configurable markups
3. **Credit Package Management**: Add/edit/remove credit packages with promotional pricing
4. **Free Credit Allocation**: Per-tier free monthly credits for BYOK usage
5. **Real-Time Configuration**: All changes take effect immediately without restarts

---

## Table of Contents

1. [Current System Analysis](#current-system-analysis)
2. [Database Schema Design](#database-schema-design)
3. [API Endpoint Specifications](#api-endpoint-specifications)
4. [Frontend UI Mockups](#frontend-ui-mockups)
5. [Credit Calculation Logic](#credit-calculation-logic)
6. [Implementation Roadmap](#implementation-roadmap)
7. [Migration Strategy](#migration-strategy)
8. [Security Considerations](#security-considerations)

---

## 1. Current System Analysis

### Existing Pricing Structure

**Current State**:
- **BYOK**: Currently free (no credits charged)
- **Platform Keys**: Fixed markup per tier (0-20%) in `TIER_MARKUP` dict
- **Credit Packages**: 4 hardcoded packages in code
- **Model Pricing**: Hardcoded in `MODEL_PRICING` and `PRICING` dicts

**Pain Points**:
1. All pricing changes require code deployment
2. No differentiation between BYOK and Platform usage in billing
3. Cannot run promotions or A/B test pricing
4. No free monthly BYOK credit allocation
5. Limited flexibility for different provider costs

### Desired State

**Goals**:
- BYOK usage charges small markup (5-10% configurable)
- Credits go further with BYOK vs Platform keys
- Admin can configure all pricing through GUI
- Support promotional pricing and discounts
- Per-tier free BYOK credit allocation
- Provider-specific BYOK markups

**Example Pricing Comparison**:
```
Same API Call:
- Platform Key: 100 credits (~$0.10)
- BYOK: 10 credits (~$0.01)
- User saves 90 credits = 10x cheaper with BYOK
```

---

## 2. Database Schema Design

### 2.1 BYOK Pricing Configuration

```sql
-- Table: byok_pricing_rules
-- Purpose: Configure BYOK markups per provider or globally
CREATE TABLE byok_pricing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Provider Configuration
    provider VARCHAR(50) NOT NULL,  -- 'openrouter', 'openai', 'anthropic', '*' (global)

    -- Pricing Rules
    markup_type VARCHAR(20) NOT NULL DEFAULT 'percentage',  -- 'percentage', 'fixed', 'none'
    markup_value DECIMAL(10, 6) NOT NULL DEFAULT 0.10,      -- 0.10 = 10% markup
    min_charge DECIMAL(10, 6) DEFAULT 0.001,                -- Minimum charge per request

    -- Free Credit Allocation (monthly)
    free_credits_monthly DECIMAL(10, 2) DEFAULT 0.00,       -- Free BYOK credits per month
    applies_to_tiers TEXT[] DEFAULT ARRAY['starter', 'professional', 'enterprise'], -- Which tiers get free credits

    -- Metadata
    rule_name VARCHAR(200),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,  -- Higher priority = applied first (for conflicts)

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Constraints
    UNIQUE(provider, priority)
);

-- Indexes
CREATE INDEX idx_byok_pricing_provider ON byok_pricing_rules(provider) WHERE is_active = TRUE;
CREATE INDEX idx_byok_pricing_active ON byok_pricing_rules(is_active, priority);

-- Default Rules
INSERT INTO byok_pricing_rules (provider, markup_type, markup_value, rule_name, description, free_credits_monthly, applies_to_tiers) VALUES
-- Global default (10% markup)
('*', 'percentage', 0.10, 'Global BYOK Markup', 'Default 10% markup for all BYOK providers', 0.00, ARRAY['starter', 'professional', 'enterprise']),

-- OpenRouter (5% markup - preferred provider)
('openrouter', 'percentage', 0.05, 'OpenRouter BYOK', 'Preferred provider - lower markup', 100.00, ARRAY['professional', 'enterprise']),

-- OpenAI (15% markup - premium)
('openai', 'percentage', 0.15, 'OpenAI BYOK', 'Premium provider - higher markup', 0.00, ARRAY['professional', 'enterprise']),

-- Anthropic (15% markup - premium)
('anthropic', 'percentage', 0.15, 'Anthropic BYOK', 'Premium provider - higher markup', 0.00, ARRAY['professional', 'enterprise']),

-- HuggingFace (8% markup - community)
('huggingface', 'percentage', 0.08, 'HuggingFace BYOK', 'Community provider - mid-tier markup', 50.00, ARRAY['starter', 'professional', 'enterprise']);
```

### 2.2 Platform Key Pricing Configuration

```sql
-- Table: platform_pricing_rules
-- Purpose: Configure platform key markups per tier
CREATE TABLE platform_pricing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Tier Configuration
    tier_code VARCHAR(50) NOT NULL,  -- 'trial', 'starter', 'professional', 'enterprise'

    -- Pricing Rules
    markup_type VARCHAR(20) NOT NULL DEFAULT 'percentage',  -- 'percentage', 'fixed', 'multiplier'
    markup_value DECIMAL(10, 6) NOT NULL DEFAULT 0.20,      -- 0.20 = 20% markup

    -- Base Cost Override (optional)
    base_cost_override DECIMAL(10, 6),  -- Override provider's base cost if set

    -- Per-Provider Overrides (JSON)
    provider_overrides JSONB DEFAULT '{}'::jsonb,
    -- Example: {"openai": {"markup": 0.30}, "anthropic": {"markup": 0.25}}

    -- Metadata
    rule_name VARCHAR(200),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Constraints
    UNIQUE(tier_code)
);

-- Indexes
CREATE INDEX idx_platform_pricing_tier ON platform_pricing_rules(tier_code) WHERE is_active = TRUE;

-- Default Rules (matching current TIER_MARKUP)
INSERT INTO platform_pricing_rules (tier_code, markup_type, markup_value, rule_name, description) VALUES
('trial', 'percentage', 0.00, 'Trial Tier Markup', 'Free tier - platform absorbs costs'),
('starter', 'percentage', 0.40, 'Starter Tier Markup', '40% markup for starter tier'),
('professional', 'percentage', 0.60, 'Professional Tier Markup', '60% markup for professional tier'),
('enterprise', 'percentage', 0.80, 'Enterprise Tier Markup', '80% markup for enterprise tier');
```

### 2.3 Credit Package Configuration

```sql
-- Table: credit_packages
-- Purpose: Dynamic credit package management
CREATE TABLE credit_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Package Details
    package_code VARCHAR(50) NOT NULL UNIQUE,  -- 'credits_100', 'credits_500', etc.
    package_name VARCHAR(200) NOT NULL,        -- 'Starter Pack', 'Professional Pack', etc.
    description TEXT,

    -- Pricing
    credits INTEGER NOT NULL,                   -- Number of credits in package
    price_usd DECIMAL(10, 2) NOT NULL,         -- Price in USD
    discount_percentage INTEGER DEFAULT 0,      -- Discount % from base price

    -- Promotional Pricing
    promo_price DECIMAL(10, 2),                -- Promotional price (if active)
    promo_code VARCHAR(50),                     -- Associated promo code
    promo_start_date TIMESTAMP WITH TIME ZONE, -- Promo start date
    promo_end_date TIMESTAMP WITH TIME ZONE,   -- Promo end date

    -- Display Configuration
    display_order INTEGER DEFAULT 0,            -- Sort order in UI
    is_featured BOOLEAN DEFAULT FALSE,          -- Highlight in UI
    badge_text VARCHAR(50),                     -- e.g., "Most Popular", "Best Value"

    -- Stripe Integration
    stripe_price_id VARCHAR(100),               -- Stripe price ID
    stripe_product_id VARCHAR(100),             -- Stripe product ID

    -- Availability
    is_active BOOLEAN DEFAULT TRUE,
    available_to_tiers TEXT[] DEFAULT ARRAY['trial', 'starter', 'professional', 'enterprise'],

    -- Purchase Limits
    max_purchases_per_user INTEGER,             -- NULL = unlimited
    max_purchases_per_month INTEGER,            -- NULL = unlimited

    -- Metadata
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],        -- e.g., ['popular', 'value', 'enterprise']

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_credit_packages_active ON credit_packages(is_active, display_order);
CREATE INDEX idx_credit_packages_code ON credit_packages(package_code);
CREATE INDEX idx_credit_packages_promo ON credit_packages(promo_code) WHERE promo_code IS NOT NULL;

-- Default Packages (enhanced from current 4 packages)
INSERT INTO credit_packages (package_code, package_name, description, credits, price_usd, discount_percentage, display_order, is_featured, badge_text, tags) VALUES
-- Starter Tier
('credits_100', 'Starter Pack', 'Perfect for trying out premium models', 100, 10.00, 0, 1, FALSE, NULL, ARRAY['starter']),
('credits_500', 'Basic Pack', 'For regular users', 500, 45.00, 10, 2, FALSE, NULL, ARRAY['basic']),

-- Professional Tier
('credits_1000', 'Professional Pack', 'Most popular choice for professionals', 1000, 85.00, 15, 3, TRUE, 'Most Popular', ARRAY['professional', 'popular']),
('credits_5000', 'Business Pack', 'For power users and small teams', 5000, 400.00, 20, 4, FALSE, 'Best Value', ARRAY['business', 'value']),

-- Enterprise Tier
('credits_10000', 'Enterprise Pack', 'For large teams and high-volume usage', 10000, 750.00, 25, 5, FALSE, NULL, ARRAY['enterprise']),
('credits_50000', 'Corporate Pack', 'Maximum value for corporate accounts', 50000, 3500.00, 30, 6, FALSE, NULL, ARRAY['enterprise', 'corporate']);
```

### 2.4 User BYOK Credits Tracking

```sql
-- Table: user_byok_credits
-- Purpose: Track free monthly BYOK credits per user
CREATE TABLE user_byok_credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User Details
    user_id VARCHAR(100) NOT NULL,
    tier_code VARCHAR(50) NOT NULL,

    -- Credits
    monthly_allowance DECIMAL(10, 2) NOT NULL DEFAULT 0.00,  -- Free credits per month
    credits_used DECIMAL(10, 2) DEFAULT 0.00,                 -- Credits used this period
    credits_remaining DECIMAL(10, 2) DEFAULT 0.00,            -- Remaining free credits

    -- Reset Tracking
    last_reset TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    next_reset TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '1 month'),

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    UNIQUE(user_id, tier_code)
);

-- Indexes
CREATE INDEX idx_user_byok_credits_user ON user_byok_credits(user_id);
CREATE INDEX idx_user_byok_credits_reset ON user_byok_credits(next_reset);

-- Function to reset monthly BYOK credits
CREATE OR REPLACE FUNCTION reset_monthly_byok_credits()
RETURNS INTEGER AS $$
DECLARE
    reset_count INTEGER := 0;
BEGIN
    -- Reset credits for users whose reset date has passed
    WITH reset_users AS (
        UPDATE user_byok_credits
        SET credits_used = 0.00,
            credits_remaining = monthly_allowance,
            last_reset = NOW(),
            next_reset = NOW() + INTERVAL '1 month',
            updated_at = NOW()
        WHERE next_reset <= NOW()
        RETURNING id
    )
    SELECT COUNT(*) INTO reset_count FROM reset_users;

    RETURN reset_count;
END;
$$ LANGUAGE plpgsql;

-- Scheduled job (run daily via pg_cron or external scheduler)
-- SELECT reset_monthly_byok_credits();
```

### 2.5 Pricing History & Audit

```sql
-- Table: pricing_change_history
-- Purpose: Audit trail for all pricing configuration changes
CREATE TABLE pricing_change_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Change Details
    change_type VARCHAR(50) NOT NULL,  -- 'byok_pricing', 'platform_pricing', 'credit_package'
    entity_id UUID NOT NULL,           -- ID of the changed entity
    entity_type VARCHAR(50) NOT NULL,  -- Table name

    -- Change Data
    old_values JSONB,                  -- Previous values
    new_values JSONB,                  -- New values
    change_summary TEXT,               -- Human-readable summary

    -- Metadata
    changed_by VARCHAR(100) NOT NULL,
    change_reason TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_pricing_history_type ON pricing_change_history(change_type, created_at DESC);
CREATE INDEX idx_pricing_history_entity ON pricing_change_history(entity_id, entity_type);
CREATE INDEX idx_pricing_history_user ON pricing_change_history(changed_by, created_at DESC);
```

---

## 3. API Endpoint Specifications

### 3.1 BYOK Pricing Configuration API

**Base Path**: `/api/v1/admin/pricing/byok`

#### List BYOK Pricing Rules

```http
GET /api/v1/admin/pricing/byok/rules

Query Parameters:
- provider (optional): Filter by provider
- is_active (optional): Filter by active status (default: true)
- include_inactive (optional): Include inactive rules (default: false)

Response: 200 OK
{
  "rules": [
    {
      "id": "uuid",
      "provider": "openrouter",
      "markup_type": "percentage",
      "markup_value": 0.05,
      "min_charge": 0.001,
      "free_credits_monthly": 100.00,
      "applies_to_tiers": ["professional", "enterprise"],
      "rule_name": "OpenRouter BYOK",
      "description": "Preferred provider - lower markup",
      "is_active": true,
      "priority": 1,
      "created_at": "2025-01-12T00:00:00Z",
      "updated_at": "2025-01-12T00:00:00Z"
    }
  ],
  "total": 5
}
```

#### Create BYOK Pricing Rule

```http
POST /api/v1/admin/pricing/byok/rules

Request Body:
{
  "provider": "cohere",
  "markup_type": "percentage",
  "markup_value": 0.08,
  "min_charge": 0.001,
  "free_credits_monthly": 50.00,
  "applies_to_tiers": ["professional", "enterprise"],
  "rule_name": "Cohere BYOK",
  "description": "Standard markup for Cohere API",
  "priority": 5
}

Response: 201 Created
{
  "id": "uuid",
  "provider": "cohere",
  ...
}
```

#### Update BYOK Pricing Rule

```http
PUT /api/v1/admin/pricing/byok/rules/{rule_id}

Request Body:
{
  "markup_value": 0.10,
  "free_credits_monthly": 75.00,
  "description": "Updated markup for Cohere API"
}

Response: 200 OK
{
  "id": "uuid",
  "provider": "cohere",
  "markup_value": 0.10,
  ...
}
```

#### Delete BYOK Pricing Rule

```http
DELETE /api/v1/admin/pricing/byok/rules/{rule_id}

Response: 204 No Content
```

#### Calculate BYOK Cost Preview

```http
POST /api/v1/admin/pricing/byok/calculate

Request Body:
{
  "provider": "openrouter",
  "base_cost": 0.01,
  "user_tier": "professional"
}

Response: 200 OK
{
  "base_cost": 0.01,
  "markup": 0.0005,
  "final_cost": 0.0105,
  "credits_charged": 0.0105,
  "rule_applied": {
    "rule_id": "uuid",
    "rule_name": "OpenRouter BYOK",
    "markup_percentage": 5.0
  }
}
```

### 3.2 Platform Pricing Configuration API

**Base Path**: `/api/v1/admin/pricing/platform`

#### List Platform Pricing Rules

```http
GET /api/v1/admin/pricing/platform/rules

Query Parameters:
- tier_code (optional): Filter by tier
- is_active (optional): Filter by active status

Response: 200 OK
{
  "rules": [
    {
      "id": "uuid",
      "tier_code": "professional",
      "markup_type": "percentage",
      "markup_value": 0.60,
      "base_cost_override": null,
      "provider_overrides": {
        "openai": {"markup": 0.70},
        "anthropic": {"markup": 0.65}
      },
      "rule_name": "Professional Tier Markup",
      "description": "60% markup for professional tier",
      "is_active": true,
      "created_at": "2025-01-12T00:00:00Z"
    }
  ],
  "total": 4
}
```

#### Update Platform Pricing Rule

```http
PUT /api/v1/admin/pricing/platform/rules/{tier_code}

Request Body:
{
  "markup_value": 0.65,
  "provider_overrides": {
    "openai": {"markup": 0.75},
    "anthropic": {"markup": 0.70}
  },
  "description": "Updated markup for professional tier"
}

Response: 200 OK
{
  "id": "uuid",
  "tier_code": "professional",
  "markup_value": 0.65,
  ...
}
```

#### Calculate Platform Cost Preview

```http
POST /api/v1/admin/pricing/platform/calculate

Request Body:
{
  "provider": "openai",
  "model": "gpt-4",
  "tokens_used": 1000,
  "user_tier": "professional"
}

Response: 200 OK
{
  "base_cost": 0.03,
  "markup": 0.018,
  "final_cost": 0.048,
  "credits_charged": 0.048,
  "rule_applied": {
    "tier_code": "professional",
    "markup_percentage": 60.0,
    "provider_override": true,
    "provider_markup": 70.0
  }
}
```

### 3.3 Credit Package Management API

**Base Path**: `/api/v1/admin/pricing/packages`

#### List Credit Packages

```http
GET /api/v1/admin/pricing/packages

Query Parameters:
- is_active (optional): Filter by active status
- include_inactive (optional): Include inactive packages
- tier (optional): Filter by available tier
- tags (optional): Filter by tags (comma-separated)

Response: 200 OK
{
  "packages": [
    {
      "id": "uuid",
      "package_code": "credits_1000",
      "package_name": "Professional Pack",
      "description": "Most popular choice for professionals",
      "credits": 1000,
      "price_usd": 85.00,
      "discount_percentage": 15,
      "promo_price": 75.00,
      "promo_code": "LAUNCH2025",
      "promo_start_date": "2025-01-01T00:00:00Z",
      "promo_end_date": "2025-01-31T23:59:59Z",
      "display_order": 3,
      "is_featured": true,
      "badge_text": "Most Popular",
      "stripe_price_id": "price_xxx",
      "stripe_product_id": "prod_yyy",
      "is_active": true,
      "available_to_tiers": ["trial", "starter", "professional", "enterprise"],
      "tags": ["professional", "popular"],
      "created_at": "2025-01-12T00:00:00Z"
    }
  ],
  "total": 6
}
```

#### Create Credit Package

```http
POST /api/v1/admin/pricing/packages

Request Body:
{
  "package_code": "credits_2500",
  "package_name": "Premium Pack",
  "description": "For serious power users",
  "credits": 2500,
  "price_usd": 200.00,
  "discount_percentage": 20,
  "display_order": 4,
  "is_featured": false,
  "badge_text": null,
  "available_to_tiers": ["professional", "enterprise"],
  "tags": ["premium", "value"]
}

Response: 201 Created
{
  "id": "uuid",
  "package_code": "credits_2500",
  ...
}
```

#### Update Credit Package

```http
PUT /api/v1/admin/pricing/packages/{package_id}

Request Body:
{
  "price_usd": 180.00,
  "discount_percentage": 25,
  "is_featured": true,
  "badge_text": "Best Value"
}

Response: 200 OK
{
  "id": "uuid",
  "package_code": "credits_2500",
  "price_usd": 180.00,
  ...
}
```

#### Add Promotion to Package

```http
POST /api/v1/admin/pricing/packages/{package_id}/promo

Request Body:
{
  "promo_price": 75.00,
  "promo_code": "FLASH50",
  "promo_start_date": "2025-02-01T00:00:00Z",
  "promo_end_date": "2025-02-07T23:59:59Z"
}

Response: 200 OK
{
  "id": "uuid",
  "promo_price": 75.00,
  "promo_code": "FLASH50",
  "promo_active": true,
  ...
}
```

#### Delete Credit Package

```http
DELETE /api/v1/admin/pricing/packages/{package_id}

Query Parameters:
- soft_delete (optional): Soft delete (mark inactive) vs hard delete (default: true)

Response: 204 No Content
```

### 3.4 User BYOK Credits API

**Base Path**: `/api/v1/credits/byok`

#### Get User BYOK Credits Balance

```http
GET /api/v1/credits/byok/balance

Headers:
- Authorization: Bearer {token}

Response: 200 OK
{
  "user_id": "user@example.com",
  "tier_code": "professional",
  "monthly_allowance": 100.00,
  "credits_used": 35.50,
  "credits_remaining": 64.50,
  "last_reset": "2025-01-01T00:00:00Z",
  "next_reset": "2025-02-01T00:00:00Z",
  "days_until_reset": 20
}
```

#### Get BYOK Credits Usage History

```http
GET /api/v1/credits/byok/history

Query Parameters:
- limit (optional): Number of records (default: 50, max: 200)
- offset (optional): Pagination offset (default: 0)
- start_date (optional): Filter by start date
- end_date (optional): Filter by end date

Response: 200 OK
{
  "history": [
    {
      "id": "uuid",
      "provider": "openrouter",
      "model": "anthropic/claude-3.5-sonnet",
      "base_cost": 0.008,
      "markup": 0.0004,
      "final_cost": 0.0084,
      "credits_charged": 0.0084,
      "created_at": "2025-01-12T10:30:00Z"
    }
  ],
  "total": 125,
  "offset": 0,
  "limit": 50
}
```

### 3.5 Pricing Configuration Dashboard API

**Base Path**: `/api/v1/admin/pricing/dashboard`

#### Get Pricing Overview

```http
GET /api/v1/admin/pricing/dashboard/overview

Response: 200 OK
{
  "summary": {
    "byok_rules_active": 5,
    "platform_rules_active": 4,
    "credit_packages_active": 6,
    "users_with_byok": 1250,
    "total_byok_credits_allocated": 125000.00,
    "total_byok_credits_used": 67500.00,
    "avg_byok_savings": "87.5%"
  },
  "revenue_impact": {
    "byok_revenue_monthly": 675.00,
    "platform_revenue_monthly": 12500.00,
    "credit_package_revenue_monthly": 8900.00,
    "total_revenue_monthly": 22075.00
  },
  "top_providers": [
    {
      "provider": "openrouter",
      "users": 850,
      "requests_monthly": 125000,
      "credits_charged": 450.00
    }
  ]
}
```

---

## 4. Frontend UI Mockups

### 4.1 Main Pricing Configuration Page

**Route**: `/admin/system/pricing-config`

**Layout**: Tabbed interface with 4 main sections

```
┌─────────────────────────────────────────────────────────────┐
│  Pricing Configuration                                       │
│  ┌─────────┬──────────┬────────────┬───────────────┐       │
│  │ BYOK    │ Platform │  Credit    │  Dashboard   │        │
│  │ Markups │  Pricing │  Packages  │  & Analytics │        │
│  └─────────┴──────────┴────────────┴───────────────┘       │
│                                                              │
│  Current Tab: BYOK Markups                                  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Provider          │ Markup │ Free Credits │ Tiers │    │
│  ├────────────────────────────────────────────────────┤    │
│  │  * (Global)        │  10%   │     $0       │  All  │    │
│  │  OpenRouter        │   5%   │    $100      │ Pro+  │    │
│  │  OpenAI            │  15%   │     $0       │ Pro+  │    │
│  │  Anthropic         │  15%   │     $0       │ Pro+  │    │
│  │  HuggingFace       │   8%   │    $50       │  All  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  [+ Add New Provider Rule]                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 BYOK Markup Configuration Modal

```
┌──────────────────────────────────────────────────────┐
│  Configure BYOK Markup                               │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Provider:  [OpenRouter ▼]                          │
│                                                       │
│  Rule Name: [OpenRouter BYOK Pricing]               │
│                                                       │
│  Markup Type: ⦿ Percentage  ○ Fixed  ○ None        │
│                                                       │
│  Markup Value: [5] %                                 │
│               ────────────────────────────────        │
│               Explanation: Users pay 5% more than    │
│               provider cost. Example: $0.10 →        │
│               $0.105 (0.5¢ markup)                   │
│                                                       │
│  Minimum Charge: [0.001] credits                     │
│                                                       │
│  Free Monthly Credits:                               │
│  [100.00] credits                                    │
│                                                       │
│  Applies to Tiers:                                   │
│  ☑ Trial      ☐ Starter                             │
│  ☑ Professional  ☑ Enterprise                        │
│                                                       │
│  Description:                                        │
│  ┌─────────────────────────────────────────┐        │
│  │ Preferred provider - lower markup       │        │
│  │                                          │        │
│  └─────────────────────────────────────────┘        │
│                                                       │
│  Priority: [1] (1 = highest)                        │
│                                                       │
│  ☑ Active                                            │
│                                                       │
├──────────────────────────────────────────────────────┤
│            [Cancel]  [Save Changes]                  │
└──────────────────────────────────────────────────────┘
```

### 4.3 Platform Pricing Configuration

```
┌─────────────────────────────────────────────────────────────┐
│  Platform Key Pricing                                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Configure markups for users using platform API keys        │
│  (UC-Cloud managed keys)                                     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Tier          │ Base Markup │ Provider Overrides  │    │
│  ├────────────────────────────────────────────────────┤    │
│  │  Trial         │     0%      │  None              │    │
│  │  Starter       │    40%      │  None              │    │
│  │  Professional  │    60%      │  OpenAI: 70%       │    │
│  │                │             │  Anthropic: 65%    │    │
│  │  Enterprise    │    80%      │  OpenAI: 75%       │    │
│  │                │             │  Anthropic: 70%    │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  [Edit Tier Pricing]                                        │
│                                                              │
│  ─────────────────────────────────────────────────────      │
│                                                              │
│  Cost Calculator Preview:                                   │
│                                                              │
│  Provider:  [OpenAI ▼]                                      │
│  Model:     [gpt-4o    ▼]                                   │
│  Tokens:    [1000     ]                                     │
│  Tier:      [Professional ▼]                                │
│                                                              │
│  ┌────────────────────────────────────────┐                │
│  │  Base Cost:        $0.030              │                │
│  │  Markup (70%):     $0.021              │                │
│  │  ────────────────────────────           │                │
│  │  Final Cost:       $0.051              │                │
│  │  Credits Charged:   0.051              │                │
│  └────────────────────────────────────────┘                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 Credit Package Management

```
┌─────────────────────────────────────────────────────────────┐
│  Credit Packages                                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Manage one-time credit purchase packages                   │
│                                                              │
│  [+ Add New Package]  [Bulk Import]                         │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Package          Credits  Price    Discount  Active│    │
│  ├────────────────────────────────────────────────────┤    │
│  │ Starter Pack       100    $10.00      0%      ✓   │    │
│  │ Basic Pack         500    $45.00     10%      ✓   │    │
│  │ Professional Pack 1,000   $85.00     15%  ⭐ ✓   │    │
│  │                                    (Most Popular)  │    │
│  │ Business Pack    5,000   $400.00     20%      ✓   │    │
│  │                                    (Best Value)    │    │
│  │ Enterprise Pack 10,000   $750.00     25%      ✓   │    │
│  │ Corporate Pack  50,000  $3,500.00    30%      ✓   │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Selected: Professional Pack                                │
│                                                              │
│  [Edit]  [Duplicate]  [Add Promotion]  [Deactivate]        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.5 Edit Credit Package Modal

```
┌──────────────────────────────────────────────────────┐
│  Edit Credit Package                                 │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Package Code: [credits_1000]                        │
│  Package Name: [Professional Pack]                   │
│                                                       │
│  Description:                                        │
│  ┌─────────────────────────────────────────┐        │
│  │ Most popular choice for professionals   │        │
│  └─────────────────────────────────────────┘        │
│                                                       │
│  Credits: [1000]                                     │
│  Base Price: [$85.00]                                │
│  Discount: [15] %                                    │
│                                                       │
│  Effective Price: $85.00 (15% off $100)             │
│  Price per Credit: $0.085                            │
│                                                       │
│  ─────────────────────────────────────────────       │
│                                                       │
│  Promotional Pricing:                                │
│                                                       │
│  ☑ Active Promotion                                  │
│                                                       │
│  Promo Price: [$75.00]                               │
│  Promo Code:  [LAUNCH2025]                          │
│                                                       │
│  Start Date: [2025-01-01] [00:00]                   │
│  End Date:   [2025-01-31] [23:59]                   │
│                                                       │
│  ─────────────────────────────────────────────       │
│                                                       │
│  Display Options:                                    │
│                                                       │
│  Display Order: [3]                                  │
│                                                       │
│  ☑ Featured Package                                  │
│  Badge Text: [Most Popular ▼]                       │
│                                                       │
│  Tags: [professional] [popular]                      │
│        [+ Add Tag]                                    │
│                                                       │
│  Available to Tiers:                                 │
│  ☑ Trial      ☑ Starter                             │
│  ☑ Professional  ☑ Enterprise                        │
│                                                       │
│  ─────────────────────────────────────────────       │
│                                                       │
│  Stripe Integration:                                 │
│                                                       │
│  Product ID: [prod_xxx]                              │
│  Price ID:   [price_yyy]                             │
│                                                       │
│  [Sync with Stripe]                                  │
│                                                       │
│  ─────────────────────────────────────────────       │
│                                                       │
│  ☑ Active                                            │
│                                                       │
├──────────────────────────────────────────────────────┤
│            [Cancel]  [Save Changes]                  │
└──────────────────────────────────────────────────────┘
```

### 4.6 Dashboard & Analytics

```
┌─────────────────────────────────────────────────────────────┐
│  Pricing Dashboard & Analytics                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Summary Metrics:                                           │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Users with  │  │ Total BYOK   │  │  Avg BYOK    │     │
│  │     BYOK     │  │   Credits    │  │   Savings    │     │
│  │              │  │              │  │              │     │
│  │    1,250     │  │   125,000    │  │    87.5%     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  Revenue Impact (Monthly):                                  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  BYOK Revenue:           $675.00                   │    │
│  │  Platform Key Revenue:  $12,500.00                 │    │
│  │  Credit Package Sales:   $8,900.00                 │    │
│  │  ─────────────────────────────────                  │    │
│  │  Total Revenue:         $22,075.00                 │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Top BYOK Providers:                                        │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Provider      Users  Requests  Revenue            │    │
│  ├────────────────────────────────────────────────────┤    │
│  │  OpenRouter     850   125,000    $450.00          │    │
│  │  HuggingFace    250    45,000    $125.00          │    │
│  │  OpenAI         100    15,000     $75.00          │    │
│  │  Anthropic       50    10,000     $25.00          │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Credit Package Performance:                                │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Package           Sales  Revenue    Conversion    │    │
│  ├────────────────────────────────────────────────────┤    │
│  │  Professional Pack   45   $3,825.00    12.5%      │    │
│  │  Business Pack       18   $7,200.00     5.0%      │    │
│  │  Starter Pack        32   $320.00       8.9%      │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  [Export Report]  [Download CSV]                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Credit Calculation Logic

### 5.1 BYOK Credit Calculation

```python
# File: backend/pricing_engine.py

from typing import Dict, Optional, Tuple
from decimal import Decimal
import asyncpg
import logging

logger = logging.getLogger(__name__)

class PricingEngine:
    """Dynamic pricing engine for BYOK and Platform usage"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def calculate_byok_cost(
        self,
        provider: str,
        base_cost: Decimal,
        user_tier: str,
        user_id: str
    ) -> Dict:
        """
        Calculate cost for BYOK request

        Args:
            provider: Provider name (e.g., 'openrouter', 'openai')
            base_cost: Provider's base cost in credits
            user_tier: User's subscription tier
            user_id: User identifier

        Returns:
            {
                'base_cost': Decimal,
                'markup': Decimal,
                'final_cost': Decimal,
                'credits_charged': Decimal,
                'free_credits_used': Decimal,
                'paid_credits_used': Decimal,
                'rule_applied': dict
            }
        """
        async with self.db_pool.acquire() as conn:
            # Get pricing rule (provider-specific or global)
            rule = await conn.fetchrow(
                """
                SELECT * FROM byok_pricing_rules
                WHERE (provider = $1 OR provider = '*')
                  AND is_active = TRUE
                  AND $2 = ANY(applies_to_tiers)
                ORDER BY
                    CASE WHEN provider = $1 THEN 0 ELSE 1 END,
                    priority DESC
                LIMIT 1
                """,
                provider, user_tier
            )

            if not rule:
                # Fallback to 10% markup
                logger.warning(f"No BYOK pricing rule found for {provider}/{user_tier}, using 10% default")
                markup_value = Decimal('0.10')
                markup_type = 'percentage'
                min_charge = Decimal('0.001')
            else:
                markup_value = rule['markup_value']
                markup_type = rule['markup_type']
                min_charge = rule['min_charge']

            # Calculate markup
            if markup_type == 'percentage':
                markup = base_cost * markup_value
            elif markup_type == 'fixed':
                markup = markup_value
            else:  # 'none'
                markup = Decimal('0')

            # Apply minimum charge
            final_cost = max(base_cost + markup, min_charge)

            # Check if user has free BYOK credits
            free_credits = await self._get_user_byok_credits(conn, user_id, user_tier)

            if free_credits >= final_cost:
                # Deduct from free credits
                free_credits_used = final_cost
                paid_credits_used = Decimal('0')
                await self._deduct_byok_credits(conn, user_id, free_credits_used)
            elif free_credits > 0:
                # Use remaining free credits, charge rest
                free_credits_used = free_credits
                paid_credits_used = final_cost - free_credits
                await self._deduct_byok_credits(conn, user_id, free_credits_used)
            else:
                # Charge full amount
                free_credits_used = Decimal('0')
                paid_credits_used = final_cost

            return {
                'base_cost': float(base_cost),
                'markup': float(markup),
                'final_cost': float(final_cost),
                'credits_charged': float(final_cost),
                'free_credits_used': float(free_credits_used),
                'paid_credits_used': float(paid_credits_used),
                'rule_applied': {
                    'rule_id': str(rule['id']) if rule else None,
                    'rule_name': rule['rule_name'] if rule else 'Default 10%',
                    'provider': provider,
                    'markup_type': markup_type,
                    'markup_percentage': float(markup_value * 100) if markup_type == 'percentage' else None
                }
            }

    async def _get_user_byok_credits(
        self,
        conn: asyncpg.Connection,
        user_id: str,
        tier_code: str
    ) -> Decimal:
        """Get user's remaining free BYOK credits"""
        result = await conn.fetchrow(
            """
            SELECT credits_remaining FROM user_byok_credits
            WHERE user_id = $1 AND tier_code = $2
            """,
            user_id, tier_code
        )

        if not result:
            # Auto-provision BYOK credits if user doesn't have entry
            return await self._provision_byok_credits(conn, user_id, tier_code)

        return result['credits_remaining']

    async def _provision_byok_credits(
        self,
        conn: asyncpg.Connection,
        user_id: str,
        tier_code: str
    ) -> Decimal:
        """Provision monthly BYOK credits for new user"""
        # Get tier's monthly allowance
        rule = await conn.fetchrow(
            """
            SELECT free_credits_monthly FROM byok_pricing_rules
            WHERE $1 = ANY(applies_to_tiers)
              AND is_active = TRUE
              AND free_credits_monthly > 0
            ORDER BY free_credits_monthly DESC
            LIMIT 1
            """,
            tier_code
        )

        allowance = rule['free_credits_monthly'] if rule else Decimal('0')

        if allowance > 0:
            await conn.execute(
                """
                INSERT INTO user_byok_credits (
                    user_id, tier_code, monthly_allowance, credits_remaining
                )
                VALUES ($1, $2, $3, $3)
                ON CONFLICT (user_id, tier_code) DO NOTHING
                """,
                user_id, tier_code, allowance
            )

            logger.info(f"Provisioned {allowance} BYOK credits for {user_id}/{tier_code}")

        return allowance

    async def _deduct_byok_credits(
        self,
        conn: asyncpg.Connection,
        user_id: str,
        amount: Decimal
    ):
        """Deduct from user's free BYOK credits"""
        await conn.execute(
            """
            UPDATE user_byok_credits
            SET credits_used = credits_used + $1,
                credits_remaining = credits_remaining - $1,
                updated_at = NOW()
            WHERE user_id = $2
            """,
            amount, user_id
        )
```

### 5.2 Platform Key Credit Calculation

```python
async def calculate_platform_cost(
    self,
    provider: str,
    model: str,
    tokens_used: int,
    user_tier: str
) -> Dict:
    """
    Calculate cost for Platform key request

    Args:
        provider: Provider name (e.g., 'openai', 'anthropic')
        model: Model name (e.g., 'gpt-4', 'claude-3.5-sonnet')
        tokens_used: Number of tokens consumed
        user_tier: User's subscription tier

    Returns:
        {
            'base_cost': Decimal,
            'markup': Decimal,
            'final_cost': Decimal,
            'credits_charged': Decimal,
            'rule_applied': dict
        }
    """
    async with self.db_pool.acquire() as conn:
        # Get platform pricing rule for tier
        rule = await conn.fetchrow(
            """
            SELECT * FROM platform_pricing_rules
            WHERE tier_code = $1 AND is_active = TRUE
            LIMIT 1
            """,
            user_tier
        )

        if not rule:
            logger.warning(f"No platform pricing rule for {user_tier}, using 0% default")
            markup_value = Decimal('0')
            markup_type = 'percentage'
            provider_overrides = {}
        else:
            markup_value = rule['markup_value']
            markup_type = rule['markup_type']
            provider_overrides = rule['provider_overrides'] or {}

        # Check for provider-specific override
        if provider in provider_overrides:
            override = provider_overrides[provider]
            if 'markup' in override:
                markup_value = Decimal(str(override['markup']))
                logger.debug(f"Using provider override for {provider}: {markup_value}")

        # Calculate base cost from model/tokens
        base_cost = await self._get_model_base_cost(conn, provider, model, tokens_used)

        # Calculate markup
        if markup_type == 'percentage':
            markup = base_cost * markup_value
        elif markup_type == 'multiplier':
            markup = base_cost * (markup_value - 1)  # e.g., 1.5x multiplier = 50% markup
        elif markup_type == 'fixed':
            markup = markup_value
        else:
            markup = Decimal('0')

        final_cost = base_cost + markup

        return {
            'base_cost': float(base_cost),
            'markup': float(markup),
            'final_cost': float(final_cost),
            'credits_charged': float(final_cost),
            'rule_applied': {
                'tier_code': user_tier,
                'markup_type': markup_type,
                'markup_percentage': float(markup_value * 100) if markup_type == 'percentage' else None,
                'provider_override': provider in provider_overrides
            }
        }

async def _get_model_base_cost(
    self,
    conn: asyncpg.Connection,
    provider: str,
    model: str,
    tokens_used: int
) -> Decimal:
    """
    Get base cost from model pricing table or hardcoded pricing

    This would query your existing MODEL_PRICING or fetch from LiteLLM
    """
    # Fallback to hardcoded pricing from litellm_credit_system.py
    # In production, this should query a database table

    from litellm_credit_system import MODEL_PRICING, PRICING

    if model in MODEL_PRICING:
        cost_per_1k = MODEL_PRICING[model]
    else:
        cost_per_1k = PRICING.get(provider, PRICING.get('default', 0.01))

    base_cost = Decimal(str(cost_per_1k)) * (tokens_used / 1000)
    return base_cost
```

### 5.3 Credit Calculation Comparison Examples

#### Example 1: OpenRouter Request (BYOK vs Platform)

**Scenario**: User makes request to Claude 3.5 Sonnet via OpenRouter, 1000 tokens

**BYOK User** (Professional tier with OpenRouter key):
```python
# User has configured their own OpenRouter API key

base_cost = 0.008  # $0.008 per 1K tokens (OpenRouter rate)
markup = 0.008 * 0.05  # 5% BYOK markup
final_cost = 0.008 + 0.0004 = 0.0084 credits

# User has 100 free BYOK credits/month, currently at 85 remaining
free_credits_used = 0.0084
paid_credits_used = 0.00

TOTAL CHARGED: 0.0084 credits (from free allowance)
COST TO USER: $0 (free tier)
```

**Platform User** (Professional tier, no BYOK key):
```python
# User uses UC-Cloud's OpenRouter key

base_cost = 0.008  # Same base cost
markup = 0.008 * 0.60  # 60% platform markup (professional tier)
final_cost = 0.008 + 0.0048 = 0.0128 credits

TOTAL CHARGED: 0.0128 credits
COST TO USER: $0.0128 (~1.3 cents)

SAVINGS WITH BYOK: 0.0044 credits = 34% savings
                  + Free credits = 100% savings (until free credits exhausted)
```

#### Example 2: OpenAI GPT-4 Request (BYOK)

**Scenario**: Professional tier user with OpenAI key, GPT-4 request, 2000 tokens

```python
base_cost = 0.030  # $0.03 per 1K tokens
markup = 0.030 * 0.15  # 15% BYOK markup (OpenAI premium provider)
final_cost = 0.030 + 0.0045 = 0.0345 credits

# User has 0 free BYOK credits remaining this month
free_credits_used = 0.00
paid_credits_used = 0.0345

TOTAL CHARGED: 0.0345 credits ($0.0345 = 3.45 cents)

vs Platform (60% markup):
platform_cost = 0.030 + (0.030 * 0.60) = 0.048 credits

SAVINGS WITH BYOK: 0.0135 credits = 28% savings
```

#### Example 3: Monthly BYOK Credits Exhaustion

**Scenario**: Professional tier user with 100 free BYOK credits/month

```python
# Month start
monthly_allowance = 100.00 credits
credits_remaining = 100.00 credits

# Request 1 (using free credits)
cost = 0.0084 credits
credits_remaining = 100.00 - 0.0084 = 99.9916 credits
charged_to_user = 0.00

# ... (many requests later)

# Request N (free credits exhausted)
credits_remaining = 0.25 credits
cost = 0.5 credits

free_credits_used = 0.25 credits
paid_credits_used = 0.25 credits
total_charged = 0.5 credits

charged_to_user = 0.25 credits ($0.0025 = 0.25 cents)

# All subsequent requests charged at BYOK rate (5-15% markup)
# Still significantly cheaper than platform rate (60% markup)
```

---

## 6. Implementation Roadmap

### Phase 1: Database Schema & Backend API (Week 1-2)

**Tasks**:
1. Create database migration scripts for all new tables
2. Implement PricingEngine class with BYOK/Platform calculation logic
3. Build BYOK pricing API endpoints (CRUD operations)
4. Build Platform pricing API endpoints
5. Build Credit Package management API
6. Build User BYOK credits API
7. Add comprehensive unit tests for pricing calculations
8. Add integration tests for API endpoints

**Deliverables**:
- [ ] Migration script: `001_create_pricing_tables.sql`
- [ ] Backend file: `backend/pricing_engine.py`
- [ ] Backend file: `backend/byok_pricing_api.py`
- [ ] Backend file: `backend/platform_pricing_api.py`
- [ ] Backend file: `backend/credit_package_api.py`
- [ ] Backend file: `backend/user_byok_credits_api.py`
- [ ] Test file: `backend/tests/test_pricing_engine.py`
- [ ] Documentation: API reference for all new endpoints

**Dependencies**:
- PostgreSQL 16+ (for JSONB and array support)
- Existing `credit_system.py` for integration
- Existing `litellm_credit_system.py` for model pricing

### Phase 2: Frontend UI (Week 3-4)

**Tasks**:
1. Create main Pricing Configuration page with tabs
2. Build BYOK markup configuration UI
3. Build Platform pricing configuration UI
4. Build Credit Package management UI
5. Build Dashboard & Analytics page
6. Add form validation and error handling
7. Implement cost calculator preview widgets
8. Add real-time updates and notifications

**Deliverables**:
- [ ] Frontend page: `src/pages/admin/PricingConfiguration.jsx`
- [ ] Component: `src/components/pricing/BYOKPricingRules.jsx`
- [ ] Component: `src/components/pricing/PlatformPricingRules.jsx`
- [ ] Component: `src/components/pricing/CreditPackageManager.jsx`
- [ ] Component: `src/components/pricing/PricingDashboard.jsx`
- [ ] Component: `src/components/pricing/CostCalculator.jsx`
- [ ] Component: `src/components/pricing/BYOKMarkupModal.jsx`
- [ ] Component: `src/components/pricing/CreditPackageModal.jsx`

**Dependencies**:
- Material-UI v5 for UI components
- React Hook Form for form management
- React Query for API state management

### Phase 3: Integration & Migration (Week 5)

**Tasks**:
1. Migrate hardcoded pricing to database tables
2. Update `litellm_credit_system.py` to use PricingEngine
3. Update `credit_system.py` to support BYOK credits
4. Implement monthly BYOK credit reset job
5. Add pricing change audit logging
6. Create admin documentation
7. Create user-facing BYOK setup guide
8. Run load testing on pricing calculations

**Deliverables**:
- [ ] Migration script: `002_migrate_hardcoded_pricing.sql`
- [ ] Updated: `backend/litellm_credit_system.py`
- [ ] Updated: `backend/credit_system.py`
- [ ] Script: `backend/scripts/reset_monthly_byok_credits.py`
- [ ] Documentation: `ADMIN_PRICING_GUIDE.md`
- [ ] Documentation: `USER_BYOK_SETUP_GUIDE.md`
- [ ] Test report: `PRICING_LOAD_TEST_RESULTS.md`

### Phase 4: Testing & Rollout (Week 6)

**Tasks**:
1. End-to-end testing of all pricing scenarios
2. Beta testing with select users
3. Monitor credit calculation accuracy
4. Gather feedback and fix bugs
5. Prepare rollout announcement
6. Deploy to production
7. Monitor for issues in first 48 hours

**Deliverables**:
- [ ] Test plan: `PRICING_E2E_TEST_PLAN.md`
- [ ] Bug reports and fixes
- [ ] Rollout plan: `PRICING_ROLLOUT_PLAN.md`
- [ ] Announcement: Blog post and email to users
- [ ] Monitoring dashboard: Real-time pricing metrics

---

## 7. Migration Strategy

### 7.1 Backward Compatibility

**Requirement**: All existing credit calculations must continue to work during migration.

**Strategy**:
1. **Dual-Mode Operation**: Run both old and new pricing systems in parallel
2. **Feature Flag**: `ENABLE_DYNAMIC_PRICING` environment variable
3. **Gradual Rollout**: Enable for tiers incrementally (trial → starter → pro → enterprise)
4. **Fallback Mechanism**: If new system fails, fall back to hardcoded pricing

### 7.2 Migration Steps

#### Step 1: Create Tables (No Impact)

```bash
# Run migration script
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /migrations/001_create_pricing_tables.sql

# Verify tables created
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt *pricing*"
```

#### Step 2: Populate with Current Values

```sql
-- Populate with existing TIER_MARKUP values from litellm_credit_system.py
INSERT INTO platform_pricing_rules (tier_code, markup_value, rule_name) VALUES
('trial', 0.00, 'Trial (Current)'),
('starter', 0.40, 'Starter (Current)'),
('professional', 0.60, 'Professional (Current)'),
('enterprise', 0.80, 'Enterprise (Current)');

-- Create default BYOK rules (10% global)
INSERT INTO byok_pricing_rules (provider, markup_value, rule_name) VALUES
('*', 0.10, 'Global BYOK Default');
```

#### Step 3: Enable Read-Only Mode

```python
# In pricing_engine.py

class PricingEngine:
    def __init__(self, db_pool: asyncpg.Pool, read_only: bool = True):
        self.db_pool = db_pool
        self.read_only = read_only  # Only read from DB, don't apply yet

    async def calculate_byok_cost(self, ...):
        if self.read_only:
            # Calculate using database rules
            new_cost = await self._calculate_from_db(...)

            # Calculate using old hardcoded rules
            old_cost = self._calculate_legacy(...)

            # Log comparison (don't charge user yet)
            logger.info(f"Pricing comparison: Old={old_cost}, New={new_cost}, Diff={new_cost - old_cost}")

            # Return old cost (no change in behavior)
            return old_cost
        else:
            # Use new pricing
            return await self._calculate_from_db(...)
```

#### Step 4: Validate Accuracy

```bash
# Run validation script
python backend/scripts/validate_pricing_migration.py

# Compare 1000 sample requests (old vs new pricing)
# Report any discrepancies > 1%
```

#### Step 5: Enable for Trial Tier (Low Risk)

```bash
# Set environment variable
ENABLE_DYNAMIC_PRICING_TIERS=trial

# Restart service
docker restart ops-center-direct

# Monitor for 24 hours
# Check error rates, credit calculation accuracy
```

#### Step 6: Gradual Rollout

```bash
# Day 1: Trial tier only
ENABLE_DYNAMIC_PRICING_TIERS=trial

# Day 3: Add starter tier (if no issues)
ENABLE_DYNAMIC_PRICING_TIERS=trial,starter

# Day 5: Add professional tier
ENABLE_DYNAMIC_PRICING_TIERS=trial,starter,professional

# Day 7: Full rollout (all tiers)
ENABLE_DYNAMIC_PRICING_TIERS=all
```

#### Step 7: Remove Legacy Code

```python
# After 2 weeks of stable operation, remove fallback code
# Delete old TIER_MARKUP dict
# Remove read_only mode
# Remove legacy calculation methods
```

### 7.3 Rollback Plan

**If issues detected during rollout**:

```bash
# Immediate rollback
ENABLE_DYNAMIC_PRICING_TIERS=none
docker restart ops-center-direct

# Investigate logs
docker logs ops-center-direct | grep -i "pricing\|credit"

# Fix issue in development
# Re-test thoroughly
# Restart rollout
```

---

## 8. Security Considerations

### 8.1 Admin Access Control

**Requirements**:
- Only users with `admin` role can access pricing configuration
- All changes must be audit logged
- Changes must be approved for production environments

**Implementation**:
```python
# In pricing API endpoints

@router.put("/api/v1/admin/pricing/byok/rules/{rule_id}")
async def update_byok_rule(
    rule_id: str,
    updates: BYOKRuleUpdate,
    current_user: dict = Depends(require_admin_from_request)
):
    # Validate admin role
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Update rule
    result = await pricing_engine.update_byok_rule(rule_id, updates.dict())

    # Audit log
    await audit_logger.log(
        action="pricing.byok.update",
        user_id=current_user["user_id"],
        resource_type="byok_pricing_rule",
        resource_id=rule_id,
        details={
            "old_values": result["old_values"],
            "new_values": result["new_values"]
        }
    )

    return result
```

### 8.2 Rate Limiting

**Protect pricing configuration endpoints from abuse**:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.put("/api/v1/admin/pricing/platform/rules/{tier_code}")
@limiter.limit("10/minute")  # Max 10 pricing updates per minute
async def update_platform_rule(...):
    ...
```

### 8.3 Input Validation

**Prevent malicious pricing configurations**:

```python
class BYOKRuleCreate(BaseModel):
    provider: str = Field(..., regex=r'^[a-z0-9_*]+$', max_length=50)
    markup_type: str = Field(..., regex=r'^(percentage|fixed|none)$')
    markup_value: Decimal = Field(..., ge=0, le=1.0)  # 0-100% markup max
    min_charge: Decimal = Field(..., ge=0.0001, le=1.0)  # Prevent $0 or excessive charges

    @validator('markup_value')
    def validate_markup(cls, v, values):
        if values.get('markup_type') == 'percentage' and v > 1.0:
            raise ValueError("Percentage markup cannot exceed 100%")
        return v
```

### 8.4 Database Security

**Encrypt sensitive pricing data**:

```sql
-- Use PostgreSQL row-level security (RLS)
ALTER TABLE byok_pricing_rules ENABLE ROW LEVEL SECURITY;

-- Only ops-center backend can read/write
CREATE POLICY pricing_admin_access ON byok_pricing_rules
    USING (current_user = 'unicorn');

-- Audit all changes via triggers
CREATE OR REPLACE FUNCTION log_pricing_change()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO pricing_change_history (
        change_type, entity_id, entity_type, old_values, new_values
    )
    VALUES (
        TG_TABLE_NAME,
        NEW.id,
        TG_TABLE_NAME,
        row_to_json(OLD),
        row_to_json(NEW)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER byok_pricing_change_trigger
AFTER UPDATE ON byok_pricing_rules
FOR EACH ROW EXECUTE FUNCTION log_pricing_change();
```

### 8.5 CSRF Protection

**All POST/PUT/DELETE requests must include CSRF token**:

```javascript
// Frontend: Include CSRF token in all requests
const response = await fetch('/api/v1/admin/pricing/byok/rules', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': getCsrfToken()
  },
  body: JSON.stringify(ruleData)
});
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

**Test pricing calculations independently**:

```python
# tests/test_pricing_engine.py

import pytest
from decimal import Decimal
from pricing_engine import PricingEngine

@pytest.mark.asyncio
async def test_byok_cost_calculation_with_free_credits():
    """Test BYOK cost when user has free credits"""
    engine = PricingEngine(mock_db_pool)

    # Setup: User has 50 free BYOK credits
    mock_db_pool.add_user_byok_credits("user123", "professional", Decimal('50.00'))

    # Execute: Calculate cost for $0.01 request with 5% markup
    result = await engine.calculate_byok_cost(
        provider="openrouter",
        base_cost=Decimal('0.01'),
        user_tier="professional",
        user_id="user123"
    )

    # Assert: Free credits used, no paid credits charged
    assert result['base_cost'] == 0.01
    assert result['markup'] == 0.0005  # 5% of 0.01
    assert result['final_cost'] == 0.0105
    assert result['free_credits_used'] == 0.0105
    assert result['paid_credits_used'] == 0.00
    assert result['credits_charged'] == 0.0105

@pytest.mark.asyncio
async def test_platform_cost_with_provider_override():
    """Test platform cost with provider-specific markup"""
    engine = PricingEngine(mock_db_pool)

    # Setup: Professional tier has 60% base markup, 70% for OpenAI
    mock_db_pool.add_platform_rule(
        "professional",
        markup_value=Decimal('0.60'),
        provider_overrides={"openai": {"markup": 0.70}}
    )

    # Execute: Calculate cost for OpenAI request
    result = await engine.calculate_platform_cost(
        provider="openai",
        model="gpt-4",
        tokens_used=1000,
        user_tier="professional"
    )

    # Assert: 70% markup applied (not 60%)
    assert result['base_cost'] == 0.03
    assert result['markup'] == 0.021  # 70% of 0.03
    assert result['final_cost'] == 0.051
    assert result['rule_applied']['provider_override'] == True
```

### 9.2 Integration Tests

**Test API endpoints end-to-end**:

```python
# tests/integration/test_pricing_api.py

@pytest.mark.asyncio
async def test_create_byok_rule(client, admin_token):
    """Test creating new BYOK pricing rule via API"""
    response = await client.post(
        "/api/v1/admin/pricing/byok/rules",
        json={
            "provider": "cohere",
            "markup_type": "percentage",
            "markup_value": 0.08,
            "rule_name": "Cohere BYOK"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data['provider'] == 'cohere'
    assert data['markup_value'] == 0.08

    # Verify rule was actually created in database
    rule = await db.fetch_one(
        "SELECT * FROM byok_pricing_rules WHERE provider = 'cohere'"
    )
    assert rule is not None

@pytest.mark.asyncio
async def test_unauthorized_pricing_access(client, user_token):
    """Test non-admin cannot access pricing configuration"""
    response = await client.get(
        "/api/v1/admin/pricing/byok/rules",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 403
    assert "Admin access required" in response.json()['detail']
```

### 9.3 Load Testing

**Ensure pricing calculations don't slow down LLM requests**:

```python
# tests/performance/test_pricing_performance.py

import asyncio
import time

@pytest.mark.asyncio
async def test_pricing_calculation_performance():
    """Test pricing engine can handle 1000 calculations/second"""
    engine = PricingEngine(db_pool)

    # Generate 10,000 test scenarios
    scenarios = generate_test_scenarios(10000)

    # Time 10,000 pricing calculations
    start = time.time()
    tasks = [
        engine.calculate_byok_cost(**scenario)
        for scenario in scenarios
    ]
    results = await asyncio.gather(*tasks)
    duration = time.time() - start

    # Assert: < 10 seconds for 10,000 calculations (1000/sec)
    assert duration < 10.0
    assert len(results) == 10000

    # Assert: Average < 1ms per calculation
    avg_time = duration / len(results)
    assert avg_time < 0.001
```

---

## 10. Monitoring & Alerting

### 10.1 Key Metrics to Track

**Dashboard**: Grafana dashboard for pricing system

**Metrics**:
1. **Pricing Calculation Latency**: p50, p95, p99 (target: < 1ms)
2. **BYOK vs Platform Usage**: Percentage split
3. **BYOK Markup Revenue**: Daily/Monthly revenue from BYOK markups
4. **Free BYOK Credits Usage**: % of users using free credits
5. **Credit Package Sales**: Revenue per package, conversion rates
6. **Pricing Errors**: Failed calculations, fallbacks to default

### 10.2 Alerts

**Alert Conditions**:
- Pricing calculation errors > 0.1%
- Average BYOK markup revenue drops > 20% (possible misconfiguration)
- Credit package sales drop > 30% week-over-week
- Database query latency > 100ms for pricing rules

### 10.3 Audit Dashboard

**Admin Dashboard**: `/admin/pricing-audit`

**Features**:
- Recent pricing changes (last 100)
- Who changed what and when
- Comparison view (before/after)
- Rollback capability for recent changes

---

## 11. Future Enhancements

### 11.1 Dynamic Pricing Algorithms

**Goal**: Automatically adjust BYOK markups based on demand/usage

```python
# Auto-adjust OpenRouter markup based on usage volume
if monthly_openrouter_requests > 1000000:
    markup = 0.03  # 3% for high-volume users
else:
    markup = 0.05  # 5% for regular users
```

### 11.2 Promotional Campaigns

**Goal**: Time-limited promotional pricing

```sql
-- Example: 50% off all credit packages for Black Friday
UPDATE credit_packages
SET promo_price = price_usd * 0.5,
    promo_code = 'BLACKFRIDAY2025',
    promo_start_date = '2025-11-24 00:00:00',
    promo_end_date = '2025-11-30 23:59:59'
WHERE is_active = TRUE;
```

### 11.3 Referral Bonuses

**Goal**: Give bonus BYOK credits for referrals

```python
# When user refers friend, give 50 free BYOK credits
await pricing_engine.add_bonus_byok_credits(
    user_id="referrer@example.com",
    credits=50.00,
    reason="referral_bonus",
    metadata={"referred_user": "new_user@example.com"}
)
```

### 11.4 Usage-Based Tier Upgrades

**Goal**: Auto-suggest tier upgrades when user hits limits

```python
# If user exhausts free BYOK credits in first week
if days_since_reset < 7 and free_credits_remaining == 0:
    send_notification(
        user_id,
        "Consider upgrading to Enterprise for unlimited BYOK credits!"
    )
```

---

## Conclusion

This dynamic pricing configuration system provides comprehensive control over BYOK and Platform pricing, enabling UC-Cloud to optimize revenue while maintaining competitive pricing for users who bring their own API keys.

**Key Benefits**:
1. **Flexibility**: Change pricing without code deployments
2. **Revenue Optimization**: Capture value from BYOK usage while staying competitive
3. **User Incentives**: Free monthly BYOK credits encourage key management
4. **Promotional Capability**: Run time-limited offers and A/B tests
5. **Transparency**: Users see clear cost breakdown (BYOK vs Platform)
6. **Scalability**: Database-driven pricing scales to any number of providers/tiers

**Next Steps**:
1. Review and approve this design document
2. Begin Phase 1 implementation (database schema + backend API)
3. Schedule stakeholder demo after Phase 2 (frontend UI)
4. Plan beta testing program with select users
5. Prepare rollout communication and documentation

---

**Document Version**: 1.0
**Last Updated**: January 12, 2025
**Status**: Awaiting Approval
**Approvers**: Backend Team Lead, Frontend Team Lead, Product Manager
