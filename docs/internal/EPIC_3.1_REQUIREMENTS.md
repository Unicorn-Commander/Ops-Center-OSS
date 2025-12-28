# Epic 3.1: LiteLLM Multi-Provider Routing - Requirements Document

**Date**: October 23, 2025
**Status**: 📋 REQUIREMENTS ANALYSIS
**Priority**: HIGH
**Estimated Duration**: 5-7 days
**Complexity**: MEDIUM-HIGH

---

## 🎯 Executive Summary

Epic 3.1 focuses on implementing **comprehensive multi-provider LLM routing** with WilmerAI-style intelligent routing, BYOK (Bring Your Own Key) support, and power level optimization. This feature will enable users to bring their own API keys for various LLM providers, reducing costs and giving them control over their AI infrastructure.

**What This Enables**:
- Users can add their own API keys for OpenAI, Anthropic, Google, etc.
- WilmerAI-style power levels (Eco/Balanced/Precision)
- Automatic fallback routing when providers fail
- Cost optimization through intelligent provider selection
- Usage analytics per provider and per user
- Subscription tier integration with feature gating

---

## 📊 Current State Analysis

### ✅ What's Already Implemented

#### Backend Infrastructure (85% Complete)

**1. LiteLLM Configuration** (`litellm_config.yaml`)
- ✅ **625 lines** of comprehensive YAML configuration
- ✅ **28 models** configured across 3 tiers:
  - **Tier 0 (Free)**: Local vLLM, Ollama, Groq, HuggingFace
  - **Tier 1 (Starter)**: Together AI, Fireworks, DeepInfra
  - **Tier 2 (Professional)**: OpenRouter gateway (Claude, GPT models via proxy)
  - **Tier 3 (Enterprise)**: Direct Anthropic, OpenAI APIs
- ✅ **Power level routing** configuration (Eco/Balanced/Precision)
- ✅ **Fallback chains** for different use cases (code, chat, long-context, premium, budget, privacy)
- ✅ **Rate limiting** per tier (free, starter, professional, enterprise)
- ✅ **Cost tracking** and provider pricing data

**2. Credit System** (`litellm_credit_system.py`)
- ✅ **579 lines** of core credit management
- ✅ Credit balance tracking with Redis caching (60s TTL)
- ✅ Debit/credit transactions with atomic database operations
- ✅ Cost calculation based on:
  - Tokens used
  - Model pricing (28 models configured)
  - Power level multipliers (Eco: 0.1x, Balanced: 0.25x, Precision: 1.0x)
  - Tier markup (Free: 0%, Starter: 40%, Pro: 60%, Enterprise: 80%)
- ✅ Monthly spending caps with enforcement
- ✅ Usage statistics and provider breakdown
- ✅ Transaction history with metadata

**3. Database Schema** (`sql/litellm_schema.sql`)
- ✅ **627 lines** of comprehensive PostgreSQL schema
- ✅ **8 tables** already defined:
  - `user_credits` - Credit balances, tiers, power levels
  - `credit_transactions` - Complete audit log
  - `user_provider_keys` - **BYOK storage with Fernet encryption** ✅
  - `llm_usage_log` - Detailed request logging
  - `provider_health` - Cached provider status
  - `credit_packages` - Purchase options
  - `power_level_configs` - Routing strategy configuration
  - `schema_version` - Version control
- ✅ **Stored procedures**:
  - `debit_user_credits()` - Atomic debit with balance checking
  - `add_user_credits()` - Credit addition with transaction logging
  - `get_user_balance()` - Balance retrieval
- ✅ **Materialized view**: `llm_usage_summary` for analytics
- ✅ **Comprehensive indexes** for performance
- ✅ **Seed data** for credit packages and power level configs

**4. LiteLLM API** (`litellm_api.py`)
- ✅ **574 lines** implementing OpenAI-compatible API
- ✅ `/v1/chat/completions` endpoint with:
  - Credit system integration
  - Power level routing
  - Usage tracking
  - Cost calculation
  - Transaction recording
- ✅ Credit management endpoints:
  - `GET /api/v1/llm/credits` - Get balance
  - `POST /api/v1/llm/credits/purchase` - Buy credits (Stripe)
  - `GET /api/v1/llm/credits/history` - Transaction history
- ✅ Model listing endpoint with tier filtering
- ✅ Usage statistics endpoint
- ✅ **BYOK endpoints** (partial):
  - `POST /api/v1/llm/byok/keys` - Add API key
  - `GET /api/v1/llm/byok/keys` - List keys (masked)
  - `DELETE /api/v1/llm/byok/keys/{provider}` - Delete key
- ✅ Health check endpoint

**5. BYOK API** (`byok_api.py`)
- ✅ **512 lines** of BYOK management
- ✅ **8 supported providers**:
  - OpenAI (key format: `sk-`)
  - Anthropic (key format: `sk-ant-`)
  - HuggingFace (key format: `hf_`)
  - Cohere
  - Together AI
  - Perplexity (key format: `pplx-`)
  - Groq (key format: `gsk_`)
  - Custom endpoints
- ✅ **Key validation** via provider APIs:
  - OpenAI: `GET /v1/models`
  - Anthropic: `POST /v1/messages` (minimal payload)
  - Others: GET requests to test endpoints
- ✅ **Keycloak integration** for key storage:
  - Keys stored as user attributes
  - Encrypted with Fernet encryption
  - Arrays for Keycloak compatibility
- ✅ **API endpoints**:
  - `GET /api/v1/byok/providers` - List supported providers
  - `GET /api/v1/byok/keys` - List user keys (masked)
  - `POST /api/v1/byok/keys/add` - Add/update key (Starter+ tier)
  - `DELETE /api/v1/byok/keys/{provider}` - Remove key
  - `POST /api/v1/byok/keys/test/{provider}` - Test key validity
  - `GET /api/v1/byok/stats` - BYOK statistics

**6. Routing API** (`litellm_routing_api.py`)
- ✅ **1,251 lines** of comprehensive routing management
- ✅ **Database initialization** with automatic table creation:
  - `llm_providers` - Provider configurations
  - `llm_models` - Model catalog
  - `llm_routing_rules` - Routing strategies
  - `user_llm_settings` - User preferences
  - `llm_usage_logs` - Analytics
- ✅ **Provider management**:
  - `GET /api/v1/llm/providers` - List providers
  - `POST /api/v1/llm/providers` - Add provider
  - `PUT /api/v1/llm/providers/{id}` - Update provider
  - `DELETE /api/v1/llm/providers/{id}` - Remove provider
- ✅ **Model management**:
  - `GET /api/v1/llm/models` - List models (sortable)
  - `POST /api/v1/llm/models` - Add model
- ✅ **Routing rules**:
  - `GET /api/v1/llm/routing/rules` - Get routing config
  - `PUT /api/v1/llm/routing/rules` - Update routing
- ✅ **User BYOK management**:
  - `POST /api/v1/llm/users/{user_id}/byok` - Set user BYOK
  - `GET /api/v1/llm/users/{user_id}/byok` - Get user BYOK (masked)
- ✅ **Usage analytics**:
  - `GET /api/v1/llm/usage` - Analytics with provider breakdown
- ✅ **Provider testing**:
  - `POST /api/v1/llm/test` - Test provider connection
- ✅ **Encryption** with Fernet cipher suite
- ✅ **Redis caching** for routing rules

**7. Encryption Infrastructure**
- ✅ **`key_encryption.py`** (referenced in byok_api.py)
- ✅ Fernet symmetric encryption (AES-128-CBC)
- ✅ Key masking for display (`sk-...****`)
- ✅ Environment-based encryption key (`ENCRYPTION_KEY`)

**8. Secret Management** (`secret_manager.py`)
- ✅ **150+ lines** of centralized secret management
- ✅ Fernet encryption wrapper
- ✅ Support for multiple secret types:
  - Cloudflare API tokens
  - NameCheap API keys
  - User API keys
  - OAuth client secrets
- ✅ Audit logging for all operations
- ✅ Secret masking
- ✅ Key rotation support

**9. Credential Manager** (`services/credential_manager.py`)
- ✅ **200+ lines** of credential management
- ✅ **4 supported services**:
  - Cloudflare
  - NameCheap
  - GitHub
  - Stripe
- ✅ Credential validation and testing
- ✅ Environment variable fallback

#### Frontend Infrastructure (40% Complete)

**1. Existing LLM Pages**
- ✅ `LiteLLMManagement.jsx` - Main LiteLLM management page
- ✅ `LLMManagement.jsx` - General LLM management
- ✅ `LLMProviderManagement.jsx` - Provider management (30KB)
- ✅ `LLMProviderSettings.jsx` - Provider settings (23KB)
- ✅ Component: `llm/ProviderCard.jsx` - Provider card UI

**2. BYOK References**
- ✅ `src/data/tierFeatures.js` mentions BYOK:
  - Free tier: "No BYOK"
  - Starter tier: "BYOK support (Bring Your Own API Keys)"
  - Professional tier: "BYOK support with usage optimization"
  - Enterprise tier: (likely "BYOK with dedicated support")

**3. Theme System**
- ✅ Material-UI components
- ✅ Framer Motion animations
- ✅ Chart.js for analytics (already registered)
- ✅ Toast notifications
- ✅ Dark/Light theme support

---

## ❌ What's Missing (Gap Analysis)

### Backend Gaps (15% Remaining)

#### 1. BYOK Manager Module (`byok_manager.py`) - MISSING
**Status**: Referenced in `litellm_api.py` line 28 but **file doesn't exist**

**Required Implementation**:
```python
class BYOKManager:
    async def get_all_user_keys(user_id: str) -> Dict[str, str]
    async def validate_api_key(user_id: str, provider: str, key: str) -> bool
    async def store_user_api_key(user_id: str, provider: str, key: str) -> str
    async def list_user_providers(user_id: str) -> List[str]
    async def delete_user_api_key(user_id: str, provider: str) -> bool
    async def get_user_key(user_id: str, provider: str) -> Optional[str]
```

**Functionality**:
- Bridge between `byok_api.py` (Keycloak storage) and `litellm_api.py` (usage)
- Decrypt keys on demand for LLM requests
- Cache decrypted keys in Redis (60s TTL, security concern!)
- Track key usage statistics

#### 2. Power Level Routing Logic - INCOMPLETE
**Status**: Configuration exists, but **routing implementation missing**

**Required Implementation**:
- Automatic provider selection based on power level
- Cost optimization algorithm (cheapest matching criteria)
- Latency optimization (fastest matching criteria)
- Quality threshold enforcement
- Fallback chain execution
- Provider health checking before routing

**Current**: User can set power level, but it only affects cost calculation, not actual routing.

#### 3. Provider Health Monitoring - PARTIAL
**Status**: Database table exists, but **monitoring logic missing**

**Required Implementation**:
- Background job to ping providers every 5 minutes
- Health status updates in `provider_health` table
- Automatic failover to healthy providers
- Alert generation for provider outages
- Performance metrics tracking (P95 latency, success rate)

#### 4. LiteLLM Proxy Integration - UNCLEAR
**Status**: Configuration points to `http://unicorn-litellm-wilmer:4000`

**Verification Needed**:
- Is LiteLLM proxy container deployed?
- Does it have the master key configured?
- Are environment variables properly injected?
- Does proxy honor routing rules from ops-center?

**Potential Issues**:
- `litellm_api.py` calls proxy at `/chat/completions`
- But routing logic is in `litellm_routing_api.py`
- How do user BYOK keys get passed to proxy?

#### 5. Stripe Integration - INCOMPLETE
**Status**: Code exists for credit purchases, but **Stripe not configured**

**Required**:
- Stripe API keys in environment
- Webhook endpoint for payment confirmation
- Credit package pricing sync with Stripe
- Refund handling
- Failed payment retry logic

### Frontend Gaps (60% Remaining)

#### 1. BYOK Management UI - COMPLETELY MISSING

**Required Pages/Components**:
```
src/pages/llm/BYOKManagement.jsx         # Main BYOK page
src/components/llm/BYOKProviderCard.jsx  # Provider card with "Add Key" button
src/components/llm/AddKeyModal.jsx       # Modal to add/edit API key
src/components/llm/TestKeyButton.jsx     # Button to test key validity
src/components/llm/KeyListTable.jsx      # Table of user's keys (masked)
```

**Features Needed**:
- List of supported providers (8 total) with logos
- Add/edit API key modal with:
  - Provider selection dropdown
  - API key input (password field)
  - Optional label/name
  - Key format validation (client-side)
  - Test connection button
- Display user's configured keys:
  - Provider name
  - Key preview (masked: `sk-...****`)
  - Last tested date
  - Test status (valid/invalid/untested)
  - Delete button
  - Re-test button
- Visual indication of which providers have keys configured
- Tier gate: Show "Upgrade to Starter" if user is on Free tier

#### 2. Power Level Selector - MISSING

**Required Component**:
```
src/components/llm/PowerLevelSelector.jsx
```

**Features**:
- Toggle/radio buttons for Eco/Balanced/Precision
- Description of each level:
  - **Eco**: "Cheapest models, slower response"
  - **Balanced**: "Mix of cost and quality" (default)
  - **Precision**: "Best models, highest cost"
- Live cost estimate comparison
- Visual indicator of current selection
- Persistence in user settings

#### 3. Provider Dashboard - PARTIAL

**Current**: `LLMProviderManagement.jsx` exists (30KB)

**Missing Features**:
- Provider health status indicators
- Real-time usage per provider
- Cost breakdown per provider
- BYOK vs Platform key indicator
- Provider performance metrics (latency, success rate)
- Add custom provider form

#### 4. Usage Analytics Dashboard - MISSING

**Required Page**:
```
src/pages/llm/UsageAnalytics.jsx
```

**Features**:
- Time-series charts:
  - Requests per day
  - Tokens consumed per day
  - Cost per day
- Provider breakdown pie chart
- Model usage histogram
- Power level usage distribution
- BYOK vs Platform usage ratio
- Export to CSV

#### 5. Credit Management UI - INCOMPLETE

**Status**: Mentioned in `litellm_api.py` but **no frontend exists**

**Required Components**:
```
src/pages/subscription/Credits.jsx
src/components/credits/PurchaseModal.jsx
src/components/credits/TransactionHistory.jsx
```

**Features**:
- Current credit balance (large, prominent)
- Credit packages:
  - $10 = 10,000 credits
  - $50 = 55,000 credits (10% bonus)
  - $100 = 120,000 credits (20% bonus)
- Purchase flow with Stripe Checkout
- Transaction history table
- Usage projections ("Credits will last ~X days")
- Low balance alerts

#### 6. Model Catalog - MISSING

**Required Page**:
```
src/pages/llm/ModelCatalog.jsx
```

**Features**:
- Searchable/filterable table of 28 models
- Columns:
  - Model name
  - Provider
  - Tier (Free/Starter/Pro/Enterprise)
  - Cost per 1K tokens
  - Context length
  - Avg latency
  - Available (✅/❌ based on user tier)
- Filter by:
  - Provider
  - Tier
  - Use case (code, chat, long-context, etc.)
- Sort by cost, latency, popularity

---

## 🔧 Technical Requirements

### Database Schema Changes

#### No Changes Needed ✅
All required tables already exist in `sql/litellm_schema.sql`:
- `user_provider_keys` - BYOK storage
- `user_credits` - Credit balances
- `credit_transactions` - Transaction log
- `llm_usage_log` - Usage analytics
- `provider_health` - Health monitoring
- `llm_providers` - Provider catalog
- `llm_models` - Model catalog
- `llm_routing_rules` - Routing configuration
- `user_llm_settings` - User preferences

**Action Required**: Run schema initialization script to create tables:
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db < /path/to/litellm_schema.sql
```

### API Endpoint Specifications

#### New Endpoints Required

**1. BYOK Manager Endpoints** (via `byok_manager.py`)
```python
# Internal use only (not exposed as REST endpoints)
BYOKManager.get_all_user_keys(user_id) -> Dict[provider, key]
BYOKManager.get_user_key(user_id, provider) -> Optional[str]
```

**2. Enhanced Chat Completions Endpoint**
```python
POST /api/v1/llm/chat/completions
# Changes:
# - Check user's BYOK keys before routing
# - If user has key for preferred provider, use it
# - Track byok_used = true in llm_usage_log
# - Don't charge credits if BYOK used (or reduced rate)
```

**3. Power Level Management**
```python
GET  /api/v1/llm/users/{user_id}/power-level
PUT  /api/v1/llm/users/{user_id}/power-level
  Body: { "power_level": "eco" | "balanced" | "precision" }
```

#### Existing Endpoints to Enhance

**1. BYOK Key Testing** (byok_api.py line 416)
```python
POST /api/v1/byok/keys/test/{provider}
# Add response time tracking
# Add success/failure logging
# Update last_tested timestamp
```

**2. Provider Health** (litellm_routing_api.py)
```python
GET /api/v1/llm/providers
# Add real-time health status from provider_health table
# Add latency metrics
```

**3. Usage Analytics** (litellm_routing_api.py line 832)
```python
GET /api/v1/llm/usage?user_id=X&days=30
# Add BYOK vs Platform breakdown
# Add power level distribution
# Add model popularity ranking
```

### Security Requirements

#### 1. Encryption Standards ✅
- **Algorithm**: Fernet (AES-128-CBC) ✅
- **Key Storage**: `ENCRYPTION_KEY` environment variable ✅
- **Key Rotation**: Support in secret_manager.py ✅

#### 2. Key Storage Best Practices

**Current Approach**:
- BYOK keys stored in **Keycloak user attributes** (byok_api.py)
- Keys encrypted with Fernet before storage ✅
- Keys stored as arrays (Keycloak requirement) ✅

**Security Concerns**:
1. ⚠️ **Redis Caching of Decrypted Keys**
   - `litellm_credit_system.py` caches credit balances (OK)
   - If we cache decrypted BYOK keys → **SECURITY RISK**
   - **Recommendation**: Decrypt on-demand, cache encrypted values only

2. ⚠️ **Key Exposure in Logs**
   - Ensure all logging masks API keys
   - Use `secret_manager.mask_secret()` everywhere
   - Review all log statements in llm endpoints

3. ✅ **API Key Validation**
   - Test keys before storing (byok_api.py line 163) ✅
   - Re-test periodically (every 7 days?)
   - Alert user if key becomes invalid

#### 3. Access Control

**Tier Gates**:
- **Free Tier**: No BYOK access (show upgrade prompt)
- **Starter Tier**: BYOK for all providers, 1 key per provider
- **Professional Tier**: BYOK + usage optimization, unlimited keys
- **Enterprise Tier**: BYOK + dedicated support, API key management

**Implementation**:
```python
@require_tier(["starter", "professional", "enterprise"])
async def add_key(key_data: APIKeyAdd, request: Request):
    # Already implemented in byok_api.py line 327 ✅
```

#### 4. Audit Logging

**Requirements**:
- Log all BYOK key additions/deletions
- Log all provider selection decisions
- Log all credit transactions
- Log all power level changes

**Implementation**: Use existing `audit_logger.py` ✅

### Performance Requirements

#### 1. Response Time Targets
- **BYOK key retrieval**: < 50ms (from Keycloak + decrypt)
- **Provider routing decision**: < 100ms
- **Chat completion (proxy call)**: < 2000ms (depends on LLM)
- **Analytics dashboard load**: < 500ms (use materialized view)

#### 2. Caching Strategy

**Redis Cache Keys**:
```
credits:balance:{user_id}              # TTL: 60s
byok:providers:{user_id}               # TTL: 300s (list of providers)
provider:health:{provider_name}        # TTL: 120s
routing:rules                          # TTL: 600s
llm:models:tier:{tier}                 # TTL: 3600s
```

**Database Optimization**:
- Materialized view: `llm_usage_summary` ✅
- Indexes on:
  - `llm_usage_log(user_id, created_at)` ✅
  - `credit_transactions(user_id, created_at)` ✅
  - `user_provider_keys(user_id, is_active)` ✅

#### 3. Rate Limiting

**Per-Tier Limits** (from litellm_config.yaml):
```yaml
free:
  tpm: 10,000    # Tokens per minute
  rpm: 10        # Requests per minute
starter:
  tpm: 100,000
  rpm: 100
professional:
  tpm: 500,000
  rpm: 500
enterprise:
  tpm: 2,000,000
  rpm: 2,000
```

**Implementation**: LiteLLM proxy handles rate limiting (needs verification)

---

## 🎨 Frontend UI Requirements

### Design Patterns

**1. Theme Consistency**
- Use existing Material-UI components ✅
- Follow `ThemeContext` patterns ✅
- Use Framer Motion for animations ✅
- Glassmorphism style for modals

**2. Color Scheme**
```javascript
PROVIDER_COLORS = {
  openai: '#10A37F',      // OpenAI green
  anthropic: '#D97706',   // Anthropic orange
  openrouter: '#7C3AED',  // Purple
  together: '#3B82F6',    // Blue
  groq: '#06B6D4',        // Cyan
  // ... already defined in LiteLLMManagement.jsx ✅
}
```

**3. Component Hierarchy**
```
src/pages/llm/
  ├── BYOKManagement.jsx          # Main BYOK page
  ├── UsageAnalytics.jsx          # Analytics dashboard
  └── ModelCatalog.jsx            # Model directory

src/components/llm/
  ├── BYOKProviderCard.jsx        # Provider card with key status
  ├── AddKeyModal.jsx             # Add/edit key modal
  ├── KeyListTable.jsx            # Table of user's keys
  ├── TestKeyButton.jsx           # Test connection button
  ├── PowerLevelSelector.jsx      # Power level toggle
  ├── ProviderHealthIndicator.jsx # Health status badge
  └── CostEstimator.jsx           # Real-time cost calculator

src/components/credits/
  ├── CreditBalance.jsx           # Large balance display
  ├── PurchaseModal.jsx           # Stripe checkout modal
  └── TransactionHistory.jsx      # Transaction table
```

### User Flows

#### Flow 1: Add BYOK Key
```
1. User navigates to /admin/llm/byok
2. Sees grid of 8 provider cards
3. Clicks "Add Key" on OpenAI card
4. Modal opens with:
   - Provider: OpenAI (locked)
   - Label: "My OpenAI Key" (optional)
   - API Key: [password input]
   - Test Connection button
5. User enters key: sk-proj-abc123...
6. Client validates format (starts with sk-)
7. User clicks "Test Connection"
8. POST /api/v1/byok/keys/test/openai
9. API validates key with OpenAI
10. Returns: { status: "valid", message: "API key is working" }
11. Green checkmark shown
12. User clicks "Save"
13. POST /api/v1/byok/keys/add
14. Key encrypted and stored
15. Modal closes
16. OpenAI card now shows:
    - Green badge: "Connected"
    - Key preview: "sk-...****"
    - "Last tested: Just now"
    - "Re-test" and "Delete" buttons
```

#### Flow 2: Select Power Level
```
1. User navigates to /admin/account/settings
2. Scrolls to "LLM Preferences" section
3. Sees power level selector:
   [○ Eco] [● Balanced] [○ Precision]
4. Clicks "Eco"
5. PUT /api/v1/llm/users/{user_id}/power-level
   Body: { "power_level": "eco" }
6. Backend updates user_llm_settings.power_level
7. Real-time cost estimate updates:
   - Before: ~$0.50 per 1K tokens
   - After: ~$0.05 per 1K tokens (10x cheaper)
8. Description updates:
   "Eco mode uses the cheapest models (local, Groq, OpenRouter budget tier)"
9. User makes next LLM request
10. Routing logic selects local vLLM or Groq
11. Cost calculated with 0.1x multiplier
```

#### Flow 3: Purchase Credits
```
1. User sees banner: "Low balance: 10 credits remaining"
2. Clicks "Buy More Credits"
3. Modal opens with 4 packages:
   - $10 = 10,000 credits
   - $50 = 55,000 credits (10% bonus) ⭐ POPULAR
   - $100 = 120,000 credits (20% bonus) 💎 BEST VALUE
   - Custom amount
4. User selects $50 package
5. Clicks "Purchase"
6. Redirects to Stripe Checkout
7. User enters payment info
8. Stripe processes payment
9. Webhook → POST /api/v1/billing/webhooks/stripe
10. Backend calls add_user_credits(user_id, 55000, "purchase")
11. Redirects to /admin/subscription/credits?success=true
12. Shows: "Success! 55,000 credits added"
13. Balance updates: 10 → 55,010 credits
```

### Responsive Design

**Breakpoints**:
- Mobile: < 768px (single column layout)
- Tablet: 768px - 1024px (2 columns)
- Desktop: > 1024px (3-4 columns)

**Key Responsiveness**:
- Provider grid: 4 cols → 2 cols → 1 col
- Charts: Full width on mobile
- Modals: Full screen on mobile
- Tables: Horizontal scroll on mobile

### Accessibility

**Requirements**:
- ARIA labels on all interactive elements
- Keyboard navigation support (Tab, Enter, Escape)
- Screen reader friendly
- Color contrast ratio ≥ 4.5:1
- Focus indicators visible
- Error messages announced to screen readers

---

## 🔗 Integration Points

### Subscription Tier Integration

**Implementation** (exists in `tier_check_api.py`):
```python
@require_tier(["starter", "professional", "enterprise"])
async def add_key(...):
    # Already implemented in byok_api.py ✅
```

**Frontend Checks**:
```javascript
// In BYOKManagement.jsx
const canUseBYOK = ['starter', 'professional', 'enterprise'].includes(user.tier);

if (!canUseBYOK) {
  return (
    <UpgradePrompt
      feature="BYOK (Bring Your Own Key)"
      minTier="Starter"
      benefits={[
        "Use your own OpenAI, Anthropic, etc. API keys",
        "Pay provider costs directly (no markup)",
        "Unlimited usage with your keys"
      ]}
    />
  );
}
```

### Lago Billing Integration

**Credit Purchase Flow**:
1. User clicks "Buy Credits"
2. Frontend: POST /api/v1/billing/checkout/create
3. Backend creates Stripe Checkout Session
4. User completes payment on Stripe
5. Stripe webhook → POST /api/v1/billing/webhooks/stripe
6. Backend:
   - Verifies payment
   - Calls `add_user_credits()`
   - Creates invoice in Lago
7. User redirected with success=true

**Usage Metering**:
- Every LLM request logs to `llm_usage_log`
- Daily cron job aggregates usage
- Pushes usage events to Lago:
  ```python
  lago_client.events.create({
    "transaction_id": request_id,
    "external_customer_id": user_id,
    "code": "llm_tokens",
    "properties": {
      "tokens": total_tokens,
      "provider": provider_name,
      "model": model_name,
      "byok_used": false
    }
  })
  ```

### Keycloak SSO Integration

**User Attributes** (already used):
- `subscription_tier` - For tier gating
- `byok_*_key` - For BYOK key storage (encrypted)
- `byok_*_label` - Key labels
- `byok_*_added_date` - When key was added
- `byok_*_last_tested` - Last test timestamp
- `byok_*_test_status` - Test result (valid/invalid)

**Session Management**:
- User authentication via Keycloak ✅
- Session cookies: `.your-domain.com` domain ✅
- Token refresh handled by frontend ✅

### LiteLLM Proxy Integration

**Configuration Needed**:
```yaml
# In docker-compose.yml or .env
LITELLM_PROXY_URL=http://unicorn-litellm-wilmer:4000
LITELLM_MASTER_KEY=<generated-key>

# LiteLLM proxy environment
LITELLM_CONFIG=/app/litellm_config.yaml
DATABASE_URL=postgresql://unicorn:password@unicorn-postgresql:5432/unicorn_db
REDIS_HOST=unicorn-redis
REDIS_PORT=6379
```

**Dynamic Key Injection**:
When user makes request with BYOK:
1. Ops-Center intercepts request
2. Checks if user has key for selected provider
3. If yes:
   - Decrypts user's key
   - Passes key to LiteLLM proxy in request headers
   - LiteLLM uses user's key instead of platform key
4. If no:
   - LiteLLM uses platform key (from config)
   - User charged credits

**Challenge**: How to pass per-user keys to LiteLLM proxy?
- Option 1: Proxy request through Ops-Center (current approach)
- Option 2: Use LiteLLM's virtual keys feature (requires setup)
- Option 3: Direct user → proxy with custom auth (complex)

**Recommendation**: Keep current proxy-through-ops-center approach.

---

## 📈 Success Metrics

### Technical Metrics

1. **Performance**:
   - API response time < 100ms (excluding LLM call)
   - BYOK key retrieval < 50ms
   - Analytics dashboard load < 500ms

2. **Reliability**:
   - 99.9% uptime for routing logic
   - Automatic fallback success rate > 95%
   - Zero key leakage incidents

3. **Scalability**:
   - Support 10,000+ concurrent users
   - Handle 1,000 requests/second
   - 1M+ usage logs without performance degradation

### Business Metrics

1. **Adoption**:
   - 40% of Starter+ users add at least one BYOK key
   - 60% of Professional users use BYOK
   - 20% reduction in platform LLM costs

2. **Revenue**:
   - 15% increase in Starter tier conversions
   - $5,000+ monthly credit purchases
   - 25% reduction in free tier abuse

3. **User Satisfaction**:
   - NPS score > 50
   - Support tickets < 5/week related to BYOK
   - Average session time increases 30%

---

## 🚀 Implementation Plan

### Phase 1: Backend Core (2 days)

**Day 1: BYOK Manager**
- [ ] Create `byok_manager.py` module
- [ ] Implement all 6 required methods
- [ ] Add Redis caching for provider lists (not keys!)
- [ ] Write unit tests (pytest)
- [ ] Test Keycloak attribute storage
- [ ] Verify encryption/decryption cycle

**Day 2: Routing Logic**
- [ ] Implement power level routing in `litellm_api.py`
- [ ] Add provider health checking
- [ ] Implement fallback chain logic
- [ ] Add BYOK key injection to proxy requests
- [ ] Test routing with mock providers
- [ ] Load test with 100 concurrent requests

**Deliverables**:
- `backend/byok_manager.py` (300 lines)
- Enhanced `backend/litellm_api.py` (+200 lines)
- Test suite: `backend/tests/test_byok.py` (150 lines)
- Documentation: Backend API reference update

### Phase 2: Frontend Core (2 days)

**Day 3: BYOK UI**
- [ ] Create `BYOKManagement.jsx` page
- [ ] Create `BYOKProviderCard.jsx` component
- [ ] Create `AddKeyModal.jsx` component
- [ ] Create `KeyListTable.jsx` component
- [ ] Add to routing (`src/App.jsx`)
- [ ] Add to navigation menu
- [ ] Test on Free tier (should show upgrade prompt)
- [ ] Test on Starter tier (should allow adding keys)

**Day 4: Power Level & Credits**
- [ ] Create `PowerLevelSelector.jsx` component
- [ ] Add to Account Settings page
- [ ] Create `Credits.jsx` page
- [ ] Create `PurchaseModal.jsx` (Stripe integration)
- [ ] Create `TransactionHistory.jsx` component
- [ ] Test full purchase flow (Stripe test mode)
- [ ] Add low balance alerts

**Deliverables**:
- `src/pages/llm/BYOKManagement.jsx` (800 lines)
- `src/components/llm/` (5 new components, 1,200 lines total)
- `src/pages/subscription/Credits.jsx` (600 lines)
- Updated navigation and routes

### Phase 3: Analytics & Polish (1.5 days)

**Day 5 Morning: Analytics Dashboard**
- [ ] Create `UsageAnalytics.jsx` page
- [ ] Add time-series chart (requests/day)
- [ ] Add provider breakdown pie chart
- [ ] Add cost breakdown table
- [ ] Add model usage histogram
- [ ] Test with mock data
- [ ] Test with real usage logs

**Day 5 Afternoon: Model Catalog**
- [ ] Create `ModelCatalog.jsx` page
- [ ] Add searchable/filterable table
- [ ] Add tier badges
- [ ] Add "Available to you" indicator
- [ ] Add cost comparison tool
- [ ] Test filtering and sorting

**Deliverables**:
- `src/pages/llm/UsageAnalytics.jsx` (900 lines)
- `src/pages/llm/ModelCatalog.jsx` (700 lines)
- Chart configurations and data fetching logic

### Phase 4: Integration & Testing (1.5 days)

**Day 6: End-to-End Testing**
- [ ] Test Free tier restrictions (no BYOK access)
- [ ] Test Starter tier (can add keys)
- [ ] Test Professional tier (usage optimization)
- [ ] Test Enterprise tier (all features)
- [ ] Test BYOK key rotation
- [ ] Test provider failover
- [ ] Test power level changes
- [ ] Test credit purchases
- [ ] Load test (1000 requests)
- [ ] Security audit (key exposure check)

**Day 7 Morning: Bug Fixes & Polish**
- [ ] Fix any issues from testing
- [ ] Polish UI animations
- [ ] Add loading states
- [ ] Add error handling
- [ ] Improve error messages
- [ ] Add helpful tooltips
- [ ] Test on mobile devices

**Day 7 Afternoon: Documentation & Deployment**
- [ ] Write user guide: "How to Use BYOK"
- [ ] Write admin guide: "Managing LLM Providers"
- [ ] Update API documentation
- [ ] Create migration guide (if schema changes)
- [ ] Deploy to staging
- [ ] QA testing on staging
- [ ] Deploy to production
- [ ] Monitor for 2 hours post-deployment

**Deliverables**:
- Test report: `EPIC_3.1_TEST_REPORT.md`
- User documentation: `docs/BYOK_USER_GUIDE.md`
- Admin documentation: `docs/LLM_ADMIN_GUIDE.md`
- Deployment checklist completed

---

## ⚠️ Risks & Mitigation

### Risk 1: LiteLLM Proxy Not Deployed
**Impact**: HIGH
**Likelihood**: MEDIUM

**Current Status**: Configuration points to `unicorn-litellm-wilmer:4000` but unclear if deployed.

**Mitigation**:
1. Verify if container exists: `docker ps | grep litellm`
2. If not, check docker-compose files for LiteLLM service
3. If missing, add LiteLLM proxy service:
   ```yaml
   unicorn-litellm:
     image: ghcr.io/berriai/litellm:latest
     ports:
       - "4000:4000"
     volumes:
       - ./litellm_config.yaml:/app/config.yaml
     environment:
       - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
     networks:
       - unicorn-network
   ```

### Risk 2: BYOK Key Security Breach
**Impact**: CRITICAL
**Likelihood**: LOW

**Vulnerabilities**:
- Keys stored in Keycloak (encrypted) ✅
- Keys might be cached in Redis (decrypted) ⚠️
- Keys passed to LiteLLM proxy (potential interception) ⚠️

**Mitigation**:
1. Never cache decrypted keys in Redis
2. Use HTTPS for all internal communication
3. Rotate encryption key quarterly
4. Add key usage alerts (unusual activity)
5. Implement key expiration (force re-test after 90 days)
6. Add 2FA requirement for adding/editing keys

### Risk 3: Provider API Rate Limits
**Impact**: MEDIUM
**Likelihood**: HIGH

**Scenario**: User adds BYOK key, makes 1000 requests, hits OpenAI rate limit.

**Mitigation**:
1. Track rate limits per user per provider
2. Implement client-side rate limiting
3. Show "Rate limit approaching" warnings
4. Automatic fallback to next provider
5. Queue requests when rate limited
6. Educate users about provider rate limits

### Risk 4: Cost Calculation Errors
**Impact**: MEDIUM
**Likelihood**: MEDIUM

**Scenario**: Cost calculation incorrect, users charged wrong amount.

**Mitigation**:
1. Unit tests for all cost calculations
2. Log all cost calculations for audit
3. Monthly cost reconciliation with usage logs
4. User-facing cost estimates before request
5. Detailed invoices with token breakdown

### Risk 5: Stripe Payment Failures
**Impact**: MEDIUM
**Likelihood**: MEDIUM

**Scenario**: Webhook not received, user pays but credits not added.

**Mitigation**:
1. Implement webhook retry logic (Stripe built-in)
2. Manual reconciliation process (daily cron)
3. User can "Report Missing Credits" button
4. Store Stripe transaction ID with every credit addition
5. Alert admin if webhook fails 3+ times

---

## 📝 Documentation Requirements

### User Documentation

**1. BYOK User Guide** (`docs/BYOK_USER_GUIDE.md`)
- What is BYOK?
- Why use BYOK?
- Supported providers
- How to get API keys (links to provider docs)
- Step-by-step: Adding your first key
- Step-by-step: Testing a key
- Troubleshooting: "Invalid key" errors
- Troubleshooting: Rate limit errors
- Best practices: Key rotation
- Best practices: Cost management

**2. Power Level Guide** (`docs/POWER_LEVEL_GUIDE.md`)
- What are power levels?
- Eco vs Balanced vs Precision comparison table
- Cost examples
- Use case recommendations
- How to change power level
- When to use each level

**3. Credits Guide** (`docs/CREDITS_GUIDE.md`)
- How credits work
- Credit packages and pricing
- How to purchase credits
- Payment methods (Stripe)
- Refund policy
- Troubleshooting: "Insufficient credits" errors

### Developer Documentation

**1. API Reference Update** (`docs/API_REFERENCE.md`)
- Add BYOK endpoints section
- Add power level endpoints
- Add credit endpoints
- Add request/response examples
- Add error codes

**2. Integration Guide** (`docs/LLM_INTEGRATION_GUIDE.md`)
- How to call LLM API from external apps
- Authentication (Bearer token)
- Power level header (`X-Power-Level`)
- BYOK preference header (`X-Prefer-BYOK`)
- Rate limiting
- Error handling
- Webhook integration (for usage tracking)

**3. Architecture Document** (`docs/LITELLM_ARCHITECTURE.md`)
- System architecture diagram
- Component interactions
- Data flow: Request → Routing → LLM → Response
- Database schema overview
- Security architecture
- Scaling considerations

### Admin Documentation

**1. Provider Management Guide** (`docs/LLM_ADMIN_GUIDE.md`)
- How to add new providers
- How to update provider pricing
- How to configure routing rules
- How to monitor provider health
- How to handle provider outages
- Emergency procedures

**2. Cost Management Guide** (`docs/LLM_COST_MANAGEMENT.md`)
- Platform vs BYOK cost comparison
- How to optimize platform costs
- Monthly cost reports
- Budget alerts
- Chargeback prevention

---

## 🎯 Acceptance Criteria

### Feature Complete ✅ When:

#### Backend
- [ ] All 16 API endpoints operational
- [ ] BYOK keys stored encrypted in Keycloak
- [ ] Power level routing logic implemented
- [ ] Fallback chains working correctly
- [ ] Cost calculation accurate (tested with 100+ scenarios)
- [ ] Credit purchase flow working (Stripe test mode)
- [ ] Provider health monitoring running
- [ ] All database tables created
- [ ] All indexes created for performance
- [ ] No N+1 query issues
- [ ] API response times < 100ms (95th percentile)
- [ ] Zero security vulnerabilities (automated scan passed)

#### Frontend
- [ ] BYOK Management page accessible at `/admin/llm/byok`
- [ ] Can add keys for all 8 supported providers
- [ ] Keys displayed masked (`sk-...****`)
- [ ] Test connection button works for all providers
- [ ] Power level selector on Account Settings
- [ ] Credits page shows current balance
- [ ] Can purchase credits via Stripe Checkout
- [ ] Transaction history displays correctly
- [ ] Usage analytics dashboard loads < 500ms
- [ ] Model catalog searchable and filterable
- [ ] All pages mobile responsive
- [ ] No console errors or warnings
- [ ] Accessibility score > 90 (Lighthouse)

#### Integration
- [ ] Free tier users see "Upgrade to Starter" prompt
- [ ] Starter tier users can add 1 key per provider
- [ ] Professional tier users get usage optimization
- [ ] Enterprise tier gets all features
- [ ] Keycloak user attributes updated correctly
- [ ] Lago usage metering events sent
- [ ] Stripe webhooks received and processed
- [ ] Audit logs created for all sensitive operations

#### Testing
- [ ] Unit tests pass (backend: 90%+ coverage)
- [ ] Integration tests pass (E2E flows)
- [ ] Load testing passed (1000 concurrent users)
- [ ] Security audit passed (no critical/high issues)
- [ ] Manual QA checklist 100% complete
- [ ] Staging deployment successful
- [ ] Production smoke tests passed

#### Documentation
- [ ] User guide published
- [ ] Admin guide published
- [ ] API documentation updated
- [ ] Architecture document created
- [ ] Deployment guide created
- [ ] All code commented (docstrings)

---

## 📞 Support & Rollout Plan

### Soft Launch (Week 1)
- Enable for 10 beta users (Professional tier)
- Monitor error rates and usage patterns
- Daily check-ins with beta users
- Fix any critical bugs within 24 hours

### General Availability (Week 2)
- Enable for all Starter+ users
- Send announcement email
- Publish blog post: "Introducing BYOK"
- Monitor support tickets
- Update FAQ based on common questions

### Marketing Push (Week 3)
- Social media announcement
- Video tutorial: "How to Use BYOK"
- Case study: "How BYOK saved Company X 60% on AI costs"
- Webinar: "Maximizing ROI with UC-Cloud LLM"

---

## 📊 Cost-Benefit Analysis

### Development Cost
- Backend developer: 3 days × $800/day = $2,400
- Frontend developer: 2 days × $800/day = $1,600
- QA engineer: 1 day × $600/day = $600
- DevOps: 0.5 day × $800/day = $400
- **Total**: $5,000

### Operational Cost (Monthly)
- LiteLLM proxy: Included in UC-Cloud infra ($0)
- Increased database storage: ~10GB = $10
- Increased Redis memory: Negligible
- Support overhead: ~5 hours/month = $300
- **Total**: $310/month

### Revenue Impact (Monthly)
- Starter tier conversions: 50 users × $19/mo = $950
- Credit purchases: 100 transactions × $30 avg = $3,000
- Reduced platform LLM costs: $2,000 saved
- **Total**: $5,950/month

### ROI
- Break-even: 1 month
- 6-month ROI: ($5,950 × 6) - $5,000 - ($310 × 6) = $29,860
- **1,196% ROI over 6 months**

---

## 🔄 Future Enhancements (Post-Epic 3.1)

### Phase 2 Features
1. **Custom Models**
   - User uploads fine-tuned models
   - Deploy to user's own compute (Azure, AWS)
   - Auto-scale based on demand

2. **Advanced Routing**
   - A/B testing different models
   - Quality feedback loop (user ratings)
   - Automatic model selection based on task complexity

3. **Cost Optimization AI**
   - ML model predicts request cost
   - Recommends cheapest provider meeting quality threshold
   - Learns from user preferences over time

4. **Team Management**
   - Shared BYOK keys for organizations
   - Quota management per team member
   - Centralized billing

5. **Enterprise Features**
   - VPC peering for private LLM access
   - Custom SLAs
   - Dedicated support channel
   - White-label options

---

## ✅ Checklist for PM/Tech Lead

### Before Starting Development
- [ ] Review requirements with stakeholders
- [ ] Confirm LiteLLM proxy deployment status
- [ ] Verify Stripe account setup
- [ ] Allocate backend and frontend developers
- [ ] Schedule daily standups
- [ ] Set up staging environment

### During Development
- [ ] Daily progress check-ins
- [ ] Code reviews within 24 hours
- [ ] Update JIRA/Linear tickets daily
- [ ] Address blockers immediately
- [ ] Run security scans on Day 5

### Before Deployment
- [ ] QA sign-off
- [ ] Security audit passed
- [ ] Load testing completed
- [ ] Staging deployment validated
- [ ] Rollback plan documented
- [ ] Support team trained

### Post-Deployment
- [ ] Monitor error rates (first 24 hours)
- [ ] Collect user feedback
- [ ] Track adoption metrics
- [ ] Schedule retro meeting
- [ ] Plan next iteration

---

## 📄 Appendix

### A. API Key Format Reference

| Provider | Format | Example | Length |
|----------|--------|---------|--------|
| OpenAI | `sk-` or `sk-proj-` | `sk-abc123...` | 48-51 chars |
| Anthropic | `sk-ant-` | `sk-ant-api03-xyz...` | 64+ chars |
| HuggingFace | `hf_` | `hf_AbCdEf...` | 37 chars |
| Groq | `gsk_` | `gsk_123456...` | 56 chars |
| Perplexity | `pplx-` | `pplx-api-key...` | Variable |
| Cohere | No prefix | `AbCdEf...` | 40 chars |
| Together | No prefix | `1234567890abcdef...` | 64 chars |

### B. Environment Variables Checklist

```bash
# Required for Epic 3.1
LITELLM_PROXY_URL=http://unicorn-litellm-wilmer:4000
LITELLM_MASTER_KEY=<generate-with-openssl>
ENCRYPTION_KEY=<generate-with-fernet>
STRIPE_SECRET_KEY=sk_test_<your-stripe-key>
STRIPE_PUBLISHABLE_KEY=pk_test_<your-stripe-key>
STRIPE_WEBHOOK_SECRET=whsec_<your-webhook-secret>

# Optional (for provider API key validation)
OPENAI_API_KEY=<platform-key>
ANTHROPIC_API_KEY=<platform-key>
OPENROUTER_API_KEY=<platform-key>
```

### C. Database Migration Script

```sql
-- Verify all tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
  'user_credits',
  'credit_transactions',
  'user_provider_keys',
  'llm_usage_log',
  'provider_health',
  'credit_packages',
  'power_level_configs',
  'llm_providers',
  'llm_models',
  'llm_routing_rules',
  'user_llm_settings'
);

-- Should return 11 rows
-- If missing, run: psql -U unicorn -d unicorn_db < sql/litellm_schema.sql
```

---

**Document Version**: 1.0
**Last Updated**: October 23, 2025
**Author**: Research Agent (Claude Code)
**Review Status**: Ready for PM/Tech Lead Review

---

## 🚀 Next Steps

1. **PM Review** (1 hour)
   - Approve scope and timeline
   - Clarify any unclear requirements
   - Prioritize P0 vs P1 features

2. **Technical Design Review** (2 hours)
   - Review with backend lead
   - Review with frontend lead
   - Review with DevOps lead
   - Identify any architectural concerns

3. **Sprint Planning** (1 hour)
   - Break down into JIRA tickets
   - Assign developers
   - Set up daily standup time
   - Define DoD (Definition of Done)

4. **Kickoff Meeting** (30 mins)
   - Introduce team
   - Review requirements document
   - Answer questions
   - Schedule first code review

**Estimated Start Date**: October 24, 2025
**Estimated Completion Date**: October 31, 2025 (7 business days)

---

**Questions or Concerns?**
Contact: Research Agent via Claude Code
