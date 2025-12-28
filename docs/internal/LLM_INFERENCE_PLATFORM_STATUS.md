# LLM Inference Platform Status - Ops-Center

**Date**: November 12, 2025
**Status**: ✅ **INFRASTRUCTURE READY** - Needs Organizational Billing Integration

---

## Executive Summary

Ops-Center **already has a complete LLM inference platform** with credit management, BYOK support, and multi-provider routing. However, it currently uses a **user-level credit system** instead of the **organizational billing system** we just deployed.

**Current State**: Individual user credits (existing system)
**Desired State**: Organizational credit pools with user allocations (new system)

**Integration Effort**: 4-6 hours to connect organizational billing to LLM inference

---

## What's Already Working ✅

### 1. LiteLLM API (Fully Operational)

**Base URL**: `http://localhost:8084/api/v1/llm`

**Endpoints Available** (29 total):

#### Chat & Image Generation
- ✅ `POST /api/v1/llm/chat/completions` - OpenAI-compatible chat completions
- ✅ `POST /api/v1/llm/image/generations` - Image generation (DALL-E, Stable Diffusion)

#### Credit Management (User-Level)
- ✅ `GET /api/v1/llm/credits` - Get user credit balance
- ✅ `POST /api/v1/llm/credits/purchase` - Purchase credits via Stripe
- ✅ `GET /api/v1/llm/credits/history` - Credit transaction history

#### Model Management
- ✅ `GET /api/v1/llm/models` - List all available models
- ✅ `GET /api/v1/llm/models/categorized` - Models grouped by BYOK vs Platform

#### BYOK (Bring Your Own Key)
- ✅ `POST /api/v1/llm/byok/keys` - Add provider API key (OpenAI, Anthropic, etc.)
- ✅ `GET /api/v1/llm/byok/keys` - List user's BYOK keys
- ✅ `DELETE /api/v1/llm/byok/keys/{provider}` - Remove BYOK key
- ✅ `POST /api/v1/llm/byok/keys/{provider}/toggle` - Enable/disable key
- ✅ `POST /api/v1/llm/byok/keys/{provider}/test` - Test key validity
- ✅ `GET /api/v1/llm/byok/keys/{provider}/usage` - BYOK usage stats

#### Usage Statistics
- ✅ `GET /api/v1/llm/usage` - User usage statistics

#### Admin Functions
- ✅ `GET /api/v1/llm/admin/system-keys` - View system provider keys
- ✅ `PUT /api/v1/llm/admin/system-keys/{provider_id}` - Update system key
- ✅ `DELETE /api/v1/llm/admin/system-keys/{provider_id}` - Delete system key
- ✅ `POST /api/v1/llm/admin/system-keys/{provider_id}/test` - Test system key
- ✅ `GET /api/v1/llm/admin/models/openrouter` - Fetch OpenRouter model catalog
- ✅ `POST /api/v1/llm/admin/models/bulk-update` - Bulk update model configs
- ✅ `PUT /api/v1/llm/admin/models/{model_id}/toggle` - Enable/disable models

---

### 2. Supported Providers

**BYOK Providers** (user can bring their own keys):
- ✅ OpenAI (GPT-3.5, GPT-4, GPT-4o, o1, o3)
- ✅ Anthropic (Claude 3/3.5 Opus, Sonnet, Haiku)
- ✅ OpenRouter (348+ models via single API key)
- ✅ Google (Gemini Pro, Gemini Flash)
- ✅ Ollama (local models)
- ✅ Ollama Cloud

**Platform Providers** (managed by system):
- ✅ OpenRouter (system key)
- ✅ Together AI
- ✅ Fireworks AI
- ✅ DeepInfra
- ✅ Groq (free tier)
- ✅ HuggingFace (free tier)

---

### 3. Credit System (Existing - User Level)

**Current Implementation**:
- Each user has an individual credit balance
- Credits stored in PostgreSQL `credit_balances` table
- Redis caching for fast balance checks
- Stripe integration for purchasing credits

**Pricing Structure**:
```python
POWER_LEVELS = {
    "eco": {
        "cost_multiplier": 0.1,  # 10% of base cost
        "max_tokens": 2000,
        "preferred_providers": ["local", "groq", "huggingface"]
    },
    "balanced": {
        "cost_multiplier": 0.25,  # 25% of base cost
        "max_tokens": 4000,
        "preferred_providers": ["together", "fireworks", "openrouter"]
    },
    "precision": {
        "cost_multiplier": 1.0,  # 100% of base cost (premium)
        "max_tokens": 16000,
        "preferred_providers": ["anthropic", "openai", "openrouter:premium"]
    }
}
```

**Cost Calculation**:
- Per-token pricing for each model/provider
- Platform markup included (1.5x for managed tier)
- BYOK = $0 (no credits charged when using own keys)

---

### 4. Integration Points

**Who Uses Ops-Center LLM API**:
- ✅ **Unicorn Brigade** - Routes all LLM calls through `/api/v1/llm/chat/completions`
- ✅ **Bolt.DIY** - Uses `/api/llmcall` proxy endpoint
- ⏳ **LoopNet Leads** - Could use it (not yet integrated)
- ⏳ **Center-Deep Intelligence** - Could use it (not yet integrated)
- ⏳ **Presenton** - Could use it (not yet integrated)

**Container**: `ops-center-centerdeep` (port 8084)

**Backend Files**:
- `backend/litellm_api.py` (2,579 lines) - Main LLM API router
- `backend/litellm_credit_system.py` (582 lines) - Credit management
- `backend/litellm_routing_api.py` (1,247 lines) - Request routing
- `backend/llm_provider_settings_api.py` (665 lines) - Provider management
- `backend/byok_manager.py` - BYOK key encryption/decryption

---

## What Needs Integration ⚠️

### Problem: Two Separate Credit Systems

**Current State**:
1. **User-Level Credits** (existing system in `litellm_credit_system.py`)
   - Individual user balances
   - No organization hierarchy
   - No shared pools
   - No user allocations

2. **Organizational Billing** (new system we just deployed)
   - Organization credit pools
   - User allocations from pools
   - Shared budgets
   - Usage attribution

**These systems are NOT connected!**

---

## Integration Plan: Connect Organizational Billing to LLM Inference

### Option 1: Replace User Credits with Org Credits (Recommended)

**What to Change**:
1. Modify `litellm_api.py` chat completions endpoint:
   - Replace `CreditSystem.get_balance(user_id)` with org billing credit check
   - Call `has_sufficient_credits(org_id, user_id, credits_needed)`
   - Deduct from org pool instead of user balance

2. Update credit deduction flow:
   - Before: `CreditSystem.debit_credits(user_id, cost)`
   - After: `deduct_credits(org_id, user_id, credits_used, "llm_inference", model_name, request_id, metadata)`

3. Remove individual credit purchases:
   - Disable `POST /api/v1/llm/credits/purchase`
   - Credits now come from org pool allocations

**Benefits**:
- ✅ Single source of truth for billing
- ✅ Shared budgets across team
- ✅ Better cost control for admins
- ✅ Complete usage attribution

**Implementation Time**: 4-6 hours

---

### Option 2: Hybrid System (Both Systems Coexist)

**What to Add**:
1. Add organization context detection:
   - Check if user belongs to an organization
   - If yes, use org billing
   - If no, fall back to individual credits

2. Add toggle in user settings:
   - "Use organization credits" vs "Use personal credits"
   - Org admins can enforce org credits

**Benefits**:
- ✅ Backward compatible
- ✅ Supports both individual and team users
- ✅ Gradual migration

**Drawbacks**:
- ⚠️ More complex code
- ⚠️ Two systems to maintain

**Implementation Time**: 8-10 hours

---

## Integration Steps (Option 1 - Recommended)

### Phase 1: Modify Credit Check (2 hours)

**File**: `backend/litellm_api.py`

**Current Code** (line ~640):
```python
@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest, ...):
    # Get user's credit balance
    credit_system = await get_credit_system(request)
    balance = await credit_system.get_balance(user_id)

    if balance < estimated_cost:
        raise HTTPException(status_code=402, detail="Insufficient credits")
```

**New Code**:
```python
@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest, ...):
    # Get user's organization context
    org_id = await get_user_org_id(user_id)

    # Check organizational credit pool
    has_credits = await db.fetchval(
        "SELECT has_sufficient_credits($1, $2, $3)",
        org_id, user_id, estimated_cost
    )

    if not has_credits:
        raise HTTPException(status_code=402, detail="Insufficient organization credits")
```

---

### Phase 2: Modify Credit Deduction (2 hours)

**File**: `backend/litellm_api.py`

**Current Code** (line ~800):
```python
# Deduct credits after successful completion
await credit_system.debit_credits(user_id, actual_cost)
```

**New Code**:
```python
# Deduct from organization credit pool
await db.execute(
    "SELECT deduct_credits($1, $2, $3, $4, $5, $6, $7)",
    org_id,                    # Organization ID
    user_id,                   # User ID
    actual_cost,               # Credits used
    "llm_inference",           # Service type
    model_name,                # Service name (specific model)
    request_id,                # Request ID for tracking
    {                          # Metadata (JSON)
        "provider": provider,
        "model": model_name,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "byok": is_byok
    }
)
```

---

### Phase 3: Add Organization Context Helper (1 hour)

**File**: `backend/litellm_api.py` (add new function)

```python
async def get_user_org_id(user_id: str) -> str:
    """
    Get user's current organization ID.

    Multi-org users may belong to multiple organizations.
    Use session state or query parameter to determine active org.
    """
    # Option 1: From session
    org_id = request.state.active_org_id

    # Option 2: From database (default org)
    if not org_id:
        org_id = await db.fetchval(
            "SELECT org_id FROM organization_members "
            "WHERE user_id = $1 AND is_default = true",
            user_id
        )

    # Option 3: First org (if user only has one)
    if not org_id:
        org_id = await db.fetchval(
            "SELECT org_id FROM organization_members "
            "WHERE user_id = $1 LIMIT 1",
            user_id
        )

    if not org_id:
        raise HTTPException(
            status_code=403,
            detail="User does not belong to any organization"
        )

    return org_id
```

---

### Phase 4: Update Image Generation Endpoint (1 hour)

**File**: `backend/litellm_api.py`

Same changes as chat completions:
1. Check org credits before generation
2. Deduct from org pool after generation
3. Add usage attribution with metadata

---

### Phase 5: Disable Individual Credit Purchases (30 minutes)

**File**: `backend/litellm_api.py`

```python
@router.post("/credits/purchase")
async def purchase_credits(...):
    # Disable individual purchases
    raise HTTPException(
        status_code=410,
        detail="Individual credit purchases have been disabled. "
               "Please contact your organization admin to allocate credits."
    )
```

**Alternative**: Redirect to org admin dashboard

---

### Phase 6: Testing & Validation (1 hour)

**Test Cases**:
1. ✅ User with org allocation can make LLM calls
2. ✅ User without credits gets 402 error
3. ✅ Credits deducted from correct org pool
4. ✅ Usage attribution recorded correctly
5. ✅ BYOK users not charged (credits = 0)
6. ✅ Multi-org users can switch organizations
7. ✅ Request IDs tracked for debugging

**Test Script**:
```bash
# Test 1: Check org credits
curl -X GET http://localhost:8084/api/v1/org-billing/credits/user/{user_id}

# Test 2: Make LLM call
curl -X POST http://localhost:8084/api/v1/llm/chat/completions \
  -H "Cookie: session_token=..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Test 3: Verify deduction
curl -X GET http://localhost:8084/api/v1/org-billing/credits/{org_id}/usage
```

---

## Migration Strategy

### Existing Users with Individual Credits

**Option A: Credit Transfer**
- Transfer individual balances to organization pools
- Create personal organizations for solo users
- Allocate transferred credits to users

**Option B: Credit Refund**
- Refund remaining individual credits via Stripe
- Users start fresh with org allocations

**Option C: Grace Period**
- Allow individual credits to be used until depleted
- New usage goes through org billing only

---

## Benefits of Integration

### For Users
- ✅ **Shared budgets** - Teams pool resources
- ✅ **No individual purchases** - Admins manage credits
- ✅ **Better tracking** - See org-wide usage
- ✅ **Multi-app support** - Same credits for all services

### For Admins
- ✅ **Centralized control** - Manage all team credits
- ✅ **Usage attribution** - See who's using what
- ✅ **Cost forecasting** - Predict monthly spend
- ✅ **Quota enforcement** - Set user limits

### For Platform
- ✅ **Unified billing** - One system for all apps
- ✅ **Better analytics** - Org-level insights
- ✅ **Enterprise ready** - Multi-tenant architecture
- ✅ **Integration ready** - LoopNet, Center-Deep can use same system

---

## Technical Architecture

### Before Integration

```
User → LLM API → User Credit Check (litellm_credit_system.py)
                    ↓
                 PostgreSQL (credit_balances table)
                    ↓
                 Deduct from user balance
                    ↓
                 LiteLLM Proxy → Provider API
```

### After Integration

```
User → LLM API → Org Context Detection
                    ↓
                 Org Credit Check (has_sufficient_credits function)
                    ↓
                 PostgreSQL (organization_credit_pools table)
                    ↓
                 Deduct from org pool (deduct_credits function)
                    ↓
                 Record attribution (credit_usage_attribution table)
                    ↓
                 LiteLLM Proxy → Provider API
```

---

## Configuration Checklist

### Database Setup
- ✅ Organizational billing tables deployed (from today's work)
- ✅ Stored functions available (has_sufficient_credits, deduct_credits, etc.)
- ⏳ Organizations created in database
- ⏳ Users assigned to organizations
- ⏳ Credit pools funded
- ⏳ User allocations configured

### Code Changes
- ⏳ Modify chat completions endpoint
- ⏳ Modify image generation endpoint
- ⏳ Add organization context helper
- ⏳ Update credit check logic
- ⏳ Update credit deduction logic
- ⏳ Disable individual purchases (or redirect)

### Testing
- ⏳ Create test organization
- ⏳ Allocate test credits
- ⏳ Test LLM calls with org credits
- ⏳ Verify usage attribution
- ⏳ Test BYOK (should be free)
- ⏳ Test insufficient credits error

### Documentation
- ⏳ Update API documentation
- ⏳ Create admin guide (how to allocate credits)
- ⏳ Create user guide (how to check usage)
- ⏳ Update integration docs for LoopNet/Center-Deep

---

## Next Steps

### Immediate (This Session - 30 min)
1. ✅ Create this status document
2. ⏳ Decide: Option 1 (replace) or Option 2 (hybrid)?
3. ⏳ Create test organization for validation

### Short-Term (Next Session - 4-6 hours)
1. ⏳ Implement Option 1 changes (recommended)
2. ⏳ Test with real LLM calls
3. ⏳ Deploy to production

### Medium-Term (Next Week)
1. ⏳ Integrate LoopNet Leads with Ops-Center LLM API
2. ⏳ Integrate Center-Deep Intelligence with Ops-Center LLM API
3. ⏳ Document for other apps (Presenton, Bolt.DIY)

---

## Questions for Decision

1. **Migration Strategy**: Transfer individual credits or refund?
2. **Implementation**: Option 1 (replace) or Option 2 (hybrid)?
3. **Multi-Org Users**: How to select active organization?
4. **Pricing**: Keep existing power levels (eco/balanced/precision)?
5. **BYOK Policy**: Still free for org users with their own keys?

---

## Summary

**Current State**:
- ✅ Complete LLM inference platform operational
- ✅ 29 API endpoints available
- ✅ Multi-provider support (OpenAI, Anthropic, OpenRouter, etc.)
- ✅ BYOK support (user keys)
- ⚠️ Individual credit system (not org-based)

**What's Needed**:
- ⏳ Connect to organizational billing (4-6 hours)
- ⏳ Test with real organizations
- ⏳ Document for LoopNet/Center-Deep integration

**When Ready**:
- ✅ LoopNet Leads can use `/api/v1/llm/chat/completions`
- ✅ Center-Deep can use `/api/v1/llm/chat/completions`
- ✅ All apps share same credit pools
- ✅ Centralized usage tracking and billing

---

**Ready to integrate? Let's discuss the migration strategy and get started!** 🚀
