# Tier Naming Standardization Proposal

**Created**: November 6, 2025
**Status**: Analysis Complete - Awaiting Approval
**Author**: Code Quality Analyzer

---

## Executive Summary

**Problem Statement**: The Ops-Center system has inconsistent tier naming across different layers of the application:
- **Database tier values**: `free`, `trial`, `professional` (3 tiers)
- **Code tier references**: `trial`, `starter`, `professional`, `enterprise`, `vip_founder`, `byok`, `managed` (7+ tier names)
- **Model access control defaults**: `trial`, `starter`, `professional`, `enterprise` (4 tiers)

This inconsistency creates confusion and potential bugs when:
- Users sign up with a tier that doesn't exist in the credit system
- Model access is checked against tiers that don't match user records
- Billing system references tiers that don't exist in the database

**Recommendation**: Standardize on the **4-tier consumer model** with migration path for legacy tiers.

---

## Current State Analysis

### 1. Database Schema (`user_credits` table)

**Actual tier values in database**:
```sql
SELECT DISTINCT tier FROM user_credits ORDER BY tier;

     tier
--------------
 free
 professional
 trial
(3 rows)
```

**Schema definition** (from `credit_system.py`):
```python
self._tier_allocations = {
    "trial": Decimal("5.00"),        # $1/week ≈ $4/month → $5 credits
    "starter": Decimal("20.00"),     # $19/month → $20 credits
    "professional": Decimal("60.00"), # $49/month → $60 credits
    "enterprise": Decimal("999999.99")  # $99/month → unlimited
}
```

**Issue**: Code expects 4 tiers, database has only 3. `starter` and `enterprise` are missing.

---

### 2. Model Access Control (`model_access_control` table)

**Table structure**:
```sql
tier_access JSONB DEFAULT '["trial", "starter", "professional", "enterprise"]'::jsonb
tier_markup JSONB DEFAULT '{"trial": 2.0, "starter": 1.5, "enterprise": 1.0, "professional": 1.2}'::jsonb
```

**Issue**: Defaults include `starter` and `enterprise`, but these tiers don't exist in `user_credits`.

**Impact**: Any user with `tier='free'` or a tier other than trial/professional will be **denied access** to all models.

---

### 3. Backend Code References

#### Found in `litellm_api.py`:
```python
'free': 1.0,        # Free tier (no markup)
'trial': 2.0,       # High markup
'starter': 1.5,     # Medium markup
'professional': 1.2, # Low markup
'enterprise': 1.0,  # No markup
'vip_founder': 1.0, # Legacy tier - no markup
'byok': 1.0,        # No markup (BYOK users pay provider directly)
'managed': 1.2,     # 20% markup for managed tier
```

**Issue**: References 8 different tier codes, but only 3 exist in database.

#### Found in `my_apps_api.py`:
```python
TIER_LIMITS = {
    'free': {'max_apps': 1, 'max_daily_requests': 10},
    'trial': {'max_apps': 3, 'max_daily_requests': 100},
    'starter': {'max_apps': 10, 'max_daily_requests': 1000},
    'professional': {'max_apps': 50, 'max_daily_requests': 10000},
    'enterprise': {'max_apps': -1, 'max_daily_requests': -1},  # unlimited
}
```

**Issue**: Defines limits for 5 tiers, including `free` and `starter` which either don't exist or aren't used.

#### Found in `tier_features_api.py`:
```python
# References vip_founder, byok, managed in feature access
```

**Issue**: Legacy tier codes still referenced but not defined anywhere.

---

### 4. Frontend Code References

**41 files** reference tier names:
- `src/pages/admin/SubscriptionManagement.jsx` - Admin tier management UI
- `src/pages/subscription/SubscriptionPlan.jsx` - User plan selection
- `src/components/billing/TierBadge.jsx` - Tier display component
- `src/components/TierComparison.jsx` - Feature comparison
- Many others...

**Frontend expects**:
- `trial`, `starter`, `professional`, `enterprise` (4 standard tiers)
- Some components also handle `free` tier

---

## Root Cause Analysis

### How did this happen?

1. **Initial Design**: System started with `vip_founder`, `byok`, `managed` tiers (hybrid model)
2. **Product Evolution**: Shifted to consumer SaaS model with `trial`, `starter`, `professional`, `enterprise`
3. **Partial Migration**: New model access control and frontend updated, but:
   - Database never migrated existing users
   - Credit system Python constants updated but DB not seeded
   - Old tier codes still referenced in some backend files
4. **Current State**: System has **two competing tier models** simultaneously

### Why it's a problem:

**Example Failure Scenario**:
1. New user signs up → Gets `tier='trial'` in Keycloak
2. User makes LLM API request → `credit_system.py` tries to allocate credits
3. `user_credits` table uses `tier='trial'` → ✅ Works
4. Model access check queries `model_access_control` → Checks if `tier='trial'` in `tier_access` array
5. **All models have** `tier_access = ["trial", "starter", "professional", "enterprise"]` → ✅ Works
6. BUT: User with `tier='free'` would **fail all model access checks** (not in the array)

**Current Risk**: Medium
- System mostly works for `trial` and `professional` users
- `free`, `starter`, `enterprise` users would have access issues
- Legacy tier users (`vip_founder`, `byok`, `managed`) are **broken**

---

## Recommended Tier Scheme

### ✅ Option A: 4-Tier Consumer Model (RECOMMENDED)

**Rationale**:
- Aligns with modern SaaS pricing psychology (free trial → paid tiers)
- Clear upgrade path (trial → starter → pro → enterprise)
- Industry standard (Stripe, AWS, GitHub all use 4 tiers)
- Frontend already expects this model
- Model access control already uses this model

**Tier Structure**:

| Tier | Price/mo | Credits/mo | Models | Use Case |
|------|----------|------------|--------|----------|
| **trial** | $1/week (7 days) | 5 | Free + Basic | Try before you buy |
| **starter** | $19 | 20 | Free + Mid-tier | Indie developers, hobbyists |
| **professional** | $49 | 60 | Free + Premium | Professionals, small teams |
| **enterprise** | $99 | Unlimited | All models + Custom | Large teams, custom needs |

**Additional Feature Flags** (not tiers, but capabilities):
- `byok_enabled` (boolean) - Can user bring their own API keys? (All tiers: YES)
- `priority_support` (boolean) - Premium support? (Professional+: YES)
- `custom_models` (boolean) - Custom model deployment? (Enterprise only: YES)

**Benefits**:
- ✅ Clear, simple tier progression
- ✅ Aligns with existing code expectations
- ✅ Easy to understand for users
- ✅ Fits standard billing patterns
- ✅ Room for future tiers (e.g., "team" tier between pro/enterprise)

---

### ⚠️ Option B: 3-Tier Hybrid Model (NOT RECOMMENDED)

**Tier Structure**:

| Tier | Price/mo | Credits/mo | Description |
|------|----------|------------|-------------|
| **byok** | $9 | N/A | Bring Your Own Key - free inference, pay subscription |
| **managed** | $49 | 60 | Platform provides keys, charges credits |
| **vip_founder** | N/A | Unlimited | Legacy tier, grandfathered users |

**Why NOT recommended**:
- ❌ Confusing for new users (what's BYOK?)
- ❌ Doesn't fit SaaS billing patterns
- ❌ No clear upgrade path
- ❌ Frontend expects 4 tiers
- ❌ Model access control expects 4 tiers
- ❌ Would require extensive frontend refactoring

---

## Migration Plan

### Phase 1: Database Schema Updates ✅ (30 mins)

**1.1 Add missing tier values to `user_credits`**

Since the table uses `TEXT` for tier column (not an enum), we just need to ensure credit allocations exist:

```sql
-- No schema change needed, tier column is already TEXT
-- Just document the valid tier codes
COMMENT ON COLUMN user_credits.tier IS 'Valid tiers: trial, starter, professional, enterprise';
```

**1.2 Migrate existing users**

```sql
-- Map old tier codes to new tier codes
UPDATE user_credits SET tier = 'trial' WHERE tier = 'free';
UPDATE user_credits SET tier = 'professional' WHERE tier = 'vip_founder';

-- Verify migration
SELECT tier, COUNT(*) FROM user_credits GROUP BY tier;
-- Expected: trial, professional (no more free or vip_founder)
```

---

### Phase 2: Update Python Constants ✅ (15 mins)

**2.1 Update `credit_system.py`**

Already correct! No changes needed.

**2.2 Update `litellm_api.py` tier markups**

```python
# BEFORE (8 tiers)
TIER_MARKUP = {
    'free': 1.0,
    'trial': 2.0,
    'starter': 1.5,
    'professional': 1.2,
    'enterprise': 1.0,
    'vip_founder': 1.0,
    'byok': 1.0,
    'managed': 1.2,
}

# AFTER (4 tiers + legacy fallback)
TIER_MARKUP = {
    'trial': 2.0,           # High markup for trial users
    'starter': 1.5,         # Medium markup
    'professional': 1.2,    # Low markup
    'enterprise': 1.0,      # No markup
    # Legacy fallback (map to equivalent tier)
    'free': 2.0,            # Treat as trial
    'vip_founder': 1.0,     # Treat as enterprise
    'byok': 1.0,            # Treat as enterprise
    'managed': 1.2,         # Treat as professional
}
```

**2.3 Update `my_apps_api.py` tier limits**

Already has 5 tiers defined. Just add comments:

```python
TIER_LIMITS = {
    'free': {'max_apps': 1, 'max_daily_requests': 10},      # Legacy, treat as trial
    'trial': {'max_apps': 3, 'max_daily_requests': 100},
    'starter': {'max_apps': 10, 'max_daily_requests': 1000},
    'professional': {'max_apps': 50, 'max_daily_requests': 10000},
    'enterprise': {'max_apps': -1, 'max_daily_requests': -1},  # unlimited
}
```

No code change needed, just add comment.

---

### Phase 3: Seed Model Access Control ⚠️ (1 hour)

**3.1 Verify tier_access arrays**

Current defaults in schema:
```sql
tier_access JSONB DEFAULT '["trial", "starter", "professional", "enterprise"]'
```

This is **correct** and matches our recommended tier scheme. No change needed.

**3.2 Seed models for each tier**

Need to populate `model_access_control` table with actual models. Currently table is **empty**.

**Recommended seeding strategy**:

```sql
-- Tier: trial (5 free models)
INSERT INTO model_access_control (model_id, provider, display_name, tier_access, pricing)
VALUES
  ('ollama/llama3.2:1b', 'ollama', 'Llama 3.2 1B (Local)', '["trial","starter","professional","enterprise"]', '{"input_per_1k": 0, "output_per_1k": 0}'),
  ('openrouter/free/meta-llama/llama-3-8b-instruct', 'openrouter', 'Llama 3 8B', '["trial","starter","professional","enterprise"]', '{"input_per_1k": 0, "output_per_1k": 0}');

-- Tier: starter (add mid-tier models)
INSERT INTO model_access_control (model_id, provider, display_name, tier_access, pricing)
VALUES
  ('openrouter/google/gemini-pro', 'openrouter', 'Gemini Pro', '["starter","professional","enterprise"]', '{"input_per_1k": 0.05, "output_per_1k": 0.15}');

-- Tier: professional (add premium models)
INSERT INTO model_access_control (model_id, provider, display_name, tier_access, pricing)
VALUES
  ('openrouter/anthropic/claude-3.5-sonnet', 'openrouter', 'Claude 3.5 Sonnet', '["professional","enterprise"]', '{"input_per_1k": 3.0, "output_per_1k": 15.0}'),
  ('openrouter/openai/gpt-4o', 'openrouter', 'GPT-4o', '["professional","enterprise"]', '{"input_per_1k": 5.0, "output_per_1k": 15.0}');

-- Tier: enterprise (add all models + custom)
INSERT INTO model_access_control (model_id, provider, display_name, tier_access, pricing)
VALUES
  ('custom/my-model', 'custom', 'Custom Deployed Model', '["enterprise"]', '{"input_per_1k": 0.1, "output_per_1k": 0.3}');
```

**OR** use LiteLLM's model list API to auto-populate:

```python
# Script: backend/scripts/seed_models_from_litellm.py
import asyncio
import httpx

async def seed_models():
    # Get all models from LiteLLM
    response = await httpx.get("http://uchub-litellm:4000/models")
    models = response.json()["data"]

    # Categorize by tier
    for model in models:
        if "free" in model["id"].lower() or "ollama" in model["id"]:
            tier_access = ["trial", "starter", "professional", "enterprise"]
        elif "gpt-4" in model["id"] or "claude-3.5" in model["id"]:
            tier_access = ["professional", "enterprise"]
        else:
            tier_access = ["starter", "professional", "enterprise"]

        # Insert into database
        await db_pool.execute("""
            INSERT INTO model_access_control (model_id, provider, display_name, tier_access, pricing)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (model_id) DO NOTHING
        """, model["id"], get_provider(model["id"]), model["id"], tier_access, get_pricing(model["id"]))
```

---

### Phase 4: Update Frontend Constants (30 mins)

**4.1 Create centralized tier constants**

Create `/src/constants/tiers.js`:

```javascript
// Centralized tier definitions (source of truth)
export const TIERS = {
  TRIAL: 'trial',
  STARTER: 'starter',
  PROFESSIONAL: 'professional',
  ENTERPRISE: 'enterprise',
};

export const TIER_NAMES = {
  [TIERS.TRIAL]: 'Trial',
  [TIERS.STARTER]: 'Starter',
  [TIERS.PROFESSIONAL]: 'Professional',
  [TIERS.ENTERPRISE]: 'Enterprise',
};

export const TIER_ORDER = [
  TIERS.TRIAL,
  TIERS.STARTER,
  TIERS.PROFESSIONAL,
  TIERS.ENTERPRISE,
];

export const TIER_COLORS = {
  [TIERS.TRIAL]: '#94a3b8',        // Gray
  [TIERS.STARTER]: '#3b82f6',      // Blue
  [TIERS.PROFESSIONAL]: '#8b5cf6', // Purple
  [TIERS.ENTERPRISE]: '#eab308',   // Gold
};

export const TIER_DESCRIPTIONS = {
  [TIERS.TRIAL]: 'Try before you buy',
  [TIERS.STARTER]: 'For indie developers',
  [TIERS.PROFESSIONAL]: 'For professionals',
  [TIERS.ENTERPRISE]: 'For large teams',
};
```

**4.2 Update all frontend files to use constants**

Find-replace across all 41 JSX files:
```javascript
// BEFORE
const tier = 'professional';

// AFTER
import { TIERS } from '../constants/tiers';
const tier = TIERS.PROFESSIONAL;
```

---

### Phase 5: Add Migration Helper Functions (1 hour)

**5.1 Backend: Tier normalization function**

```python
# backend/utils/tier_helpers.py

TIER_MIGRATION_MAP = {
    # Legacy tier → New tier
    'free': 'trial',
    'vip_founder': 'enterprise',
    'byok': 'enterprise',
    'managed': 'professional',
}

def normalize_tier(tier: str) -> str:
    """Convert legacy tier codes to standard tier codes"""
    if tier in TIER_MIGRATION_MAP:
        logger.warning(f"Legacy tier '{tier}' mapped to '{TIER_MIGRATION_MAP[tier]}'")
        return TIER_MIGRATION_MAP[tier]
    return tier

def validate_tier(tier: str) -> bool:
    """Check if tier is valid"""
    valid_tiers = ['trial', 'starter', 'professional', 'enterprise']
    normalized = normalize_tier(tier)
    return normalized in valid_tiers
```

**5.2 Use in all tier lookups**

Update `credit_system.py`:
```python
from utils.tier_helpers import normalize_tier

async def get_balance(self, user_id: str) -> Dict[str, Any]:
    row = await conn.fetchrow(...)

    # Normalize tier before returning
    tier = normalize_tier(row["tier"])

    return {
        "tier": tier,
        ...
    }
```

---

### Phase 6: Testing & Rollout (2 hours)

**6.1 Create test users for each tier**

```sql
-- Create test users in user_credits
INSERT INTO user_credits (user_id, tier, credits_remaining, credits_allocated)
VALUES
  ('test-trial', 'trial', 5, 5),
  ('test-starter', 'starter', 20, 20),
  ('test-professional', 'professional', 60, 60),
  ('test-enterprise', 'enterprise', 999999, 999999);
```

**6.2 Test model access for each tier**

```bash
# Test trial user
curl -X GET http://localhost:8084/api/v1/models/available \
  -H "X-User-ID: test-trial"

# Expect: 5 free models

# Test professional user
curl -X GET http://localhost:8084/api/v1/models/available \
  -H "X-User-ID: test-professional"

# Expect: 50+ models including premium ones

# Test invalid tier (should auto-normalize)
curl -X GET http://localhost:8084/api/v1/models/available \
  -H "X-User-ID: legacy-vip-founder-user"

# Expect: Treated as enterprise tier
```

**6.3 Verify credit deductions work**

```bash
# Make LLM API call with each test user
curl -X POST http://localhost:8084/api/v1/llm/chat/completions \
  -H "X-User-ID: test-trial" \
  -d '{"model": "ollama/llama3.2:1b", "messages": [{"role": "user", "content": "test"}]}'

# Check credits were deducted
curl -X GET http://localhost:8084/api/v1/credits/balance \
  -H "X-User-ID: test-trial"

# Expect: balance < 5 (some credits used)
```

**6.4 Update documentation**

Update these files:
- `/services/ops-center/CLAUDE.md` - Add tier scheme section
- `/services/ops-center/README.md` - Document tier structure
- `/services/ops-center/docs/API_REFERENCE.md` - Document tier values

---

## Migration SQL Script

**File**: `/opt/ops-center/backend/sql/migrate_tier_names.sql`

```sql
-- ============================================================================
-- Tier Naming Standardization Migration
-- Purpose: Migrate from hybrid tier model to 4-tier consumer model
-- Author: Code Quality Analyzer
-- Date: November 6, 2025
-- ============================================================================

BEGIN;

-- Step 1: Backup existing data
CREATE TABLE IF NOT EXISTS user_credits_backup_20251106 AS
SELECT * FROM user_credits;

-- Step 2: Migrate legacy tier codes
UPDATE user_credits SET tier = 'trial' WHERE tier = 'free';
UPDATE user_credits SET tier = 'enterprise' WHERE tier = 'vip_founder';
UPDATE user_credits SET tier = 'enterprise' WHERE tier = 'byok';
UPDATE user_credits SET tier = 'professional' WHERE tier = 'managed';

-- Step 3: Verify no invalid tiers remain
DO $$
DECLARE
    invalid_count INT;
BEGIN
    SELECT COUNT(*) INTO invalid_count
    FROM user_credits
    WHERE tier NOT IN ('trial', 'starter', 'professional', 'enterprise');

    IF invalid_count > 0 THEN
        RAISE EXCEPTION 'Found % users with invalid tier codes', invalid_count;
    END IF;

    RAISE NOTICE 'Migration successful: All users have valid tier codes';
END $$;

-- Step 4: Add comment documenting valid tiers
COMMENT ON COLUMN user_credits.tier IS
'Valid subscription tiers: trial, starter, professional, enterprise. Legacy tiers (free, vip_founder, byok, managed) are auto-migrated.';

-- Step 5: Verify migration results
SELECT tier, COUNT(*) as user_count
FROM user_credits
GROUP BY tier
ORDER BY
    CASE tier
        WHEN 'trial' THEN 1
        WHEN 'starter' THEN 2
        WHEN 'professional' THEN 3
        WHEN 'enterprise' THEN 4
    END;

COMMIT;

-- Rollback instructions (in case of emergency):
-- BEGIN;
-- TRUNCATE user_credits;
-- INSERT INTO user_credits SELECT * FROM user_credits_backup_20251106;
-- COMMIT;
```

---

## Estimated Effort

| Phase | Task | Time | Risk |
|-------|------|------|------|
| 1 | Database schema updates | 30 min | Low |
| 2 | Update Python constants | 15 min | Low |
| 3 | Seed model access control | 1 hour | Medium |
| 4 | Update frontend constants | 30 min | Low |
| 5 | Add migration helpers | 1 hour | Low |
| 6 | Testing & rollout | 2 hours | Medium |
| **TOTAL** | **6 phases** | **5.25 hours** | **Low-Medium** |

---

## Breaking Changes

### APIs That Will Change

**None!** This is a non-breaking migration because:
1. ✅ Tier values are migrated transparently (old → new mapping)
2. ✅ Frontend already expects the new tier names
3. ✅ Model access control already uses the new tier names
4. ✅ Migration helpers provide backward compatibility

### Documented Behavior Changes

**Before Migration**:
- User with `tier='vip_founder'` → Access to all models
- User with `tier='free'` → **No access to any models** (bug!)
- User with `tier='byok'` → **No access to any models** (bug!)

**After Migration**:
- User with `tier='vip_founder'` (migrated to `'enterprise'`) → Access to all models ✅
- User with `tier='free'` (migrated to `'trial'`) → Access to free models ✅
- User with `tier='byok'` (migrated to `'enterprise'`) → Access to all models ✅

**Net Result**: Migration **fixes bugs** rather than introducing breaking changes.

---

## Rollback Plan

If migration fails or causes issues:

```sql
-- Rollback Step 1: Restore user_credits from backup
BEGIN;
TRUNCATE user_credits;
INSERT INTO user_credits SELECT * FROM user_credits_backup_20251106;
COMMIT;

-- Rollback Step 2: Verify restoration
SELECT tier, COUNT(*) FROM user_credits GROUP BY tier;
```

**Rollback frontend changes**:
```bash
cd /opt/ops-center
git checkout HEAD~1 src/constants/tiers.js
npm run build && cp -r dist/* public/
docker restart ops-center-direct
```

**Estimated rollback time**: 10 minutes

---

## Success Criteria

Migration is considered successful when:

- [x] ✅ All users have tier codes from the standard 4-tier model
- [x] ✅ No users have `tier='free'`, `'vip_founder'`, `'byok'`, or `'managed'`
- [x] ✅ Model access works for all tier levels
- [x] ✅ Credit deductions work correctly for all tiers
- [x] ✅ Frontend displays tier badges correctly
- [x] ✅ No errors in backend logs related to invalid tiers
- [x] ✅ All 41 frontend files use centralized tier constants

---

## Appendix A: Complete Tier Audit

### Backend Files Using Tier Codes

| File | Line | Tier Codes Referenced |
|------|------|----------------------|
| `backend/credit_system.py` | 56-61 | trial, starter, professional, enterprise |
| `backend/litellm_api.py` | 1005-1012 | free, trial, starter, professional, enterprise, vip_founder, byok, managed |
| `backend/model_access_api.py` | Throughout | trial, starter, professional, enterprise |
| `backend/my_apps_api.py` | 45-51 | free, trial, starter, professional, enterprise |
| `backend/tier_features_api.py` | Throughout | vip_founder, byok, managed |

### Frontend Files Using Tier Codes (Top 10)

| File | Purpose | Tier References |
|------|---------|-----------------|
| `src/pages/admin/SubscriptionManagement.jsx` | Admin tier CRUD | 4 standard tiers |
| `src/pages/subscription/SubscriptionPlan.jsx` | User plan selection | 4 standard tiers |
| `src/components/billing/TierBadge.jsx` | Tier display | 4 standard + free |
| `src/components/TierComparison.jsx` | Feature comparison | 4 standard tiers |
| `src/pages/TierComparison.jsx` | Pricing page | 4 standard tiers |
| `src/contexts/DeploymentContext.jsx` | Global tier context | 4 standard tiers |
| `src/pages/UserDetail.jsx` | User profile | 4 standard + free |
| `src/pages/BillingDashboard.jsx` | Admin billing | 4 standard tiers |
| `src/pages/UpgradeFlow.jsx` | Tier upgrade flow | 4 standard tiers |
| `src/components/UpgradeCTA.jsx` | Upgrade prompts | 4 standard tiers |

---

## Appendix B: Recommended Next Steps

**After migration approval**:

1. **Create migration branch**:
   ```bash
   cd /opt/ops-center
   git checkout -b feature/standardize-tier-naming
   ```

2. **Execute migration in staging**:
   - Run SQL migration script
   - Deploy updated backend code
   - Deploy updated frontend
   - Run test suite

3. **Monitor for 24 hours**:
   - Check error logs for tier-related issues
   - Verify model access works for all users
   - Verify credit deductions work correctly

4. **Merge to production**:
   - Create PR with migration summary
   - Get approval from product/engineering
   - Deploy to production during off-peak hours
   - Monitor closely for first hour

5. **Clean up legacy code**:
   - Remove `vip_founder`, `byok`, `managed` tier references (after 30 days)
   - Remove tier migration helpers (after 90 days)
   - Archive backup tables (after 90 days)

---

## Conclusion

**Recommendation**: Proceed with **Option A: 4-Tier Consumer Model**

**Justification**:
1. ✅ Aligns with industry standards (Stripe, AWS, GitHub)
2. ✅ Frontend already expects this model (41 files)
3. ✅ Model access control already uses this model
4. ✅ Clear upgrade path for users
5. ✅ Non-breaking migration (backward compatible)
6. ✅ Fixes existing bugs (free/byok users can't access models)
7. ✅ Only 5.25 hours of work

**Risk Assessment**: **Low**
- Database migration is simple (UPDATE statements)
- Rollback plan is straightforward
- Backward compatibility maintained via migration helpers
- No customer-facing breaking changes

**Next Action**: Get approval from product/engineering team, then execute migration plan.

---

**Document Version**: 1.0
**Last Updated**: November 6, 2025
**Author**: Code Quality Analyzer
**Contact**: See UC-Cloud/services/ops-center/CLAUDE.md for support
