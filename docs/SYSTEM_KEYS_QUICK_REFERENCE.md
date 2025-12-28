# System Provider Keys - Quick Reference

**Last Updated**: October 27, 2025

---

## TL;DR: Where Admin Sets System Keys

### ✅ Currently Working

**Page**: `OpenRouterSettings.jsx`
**Route**: `/admin/openrouter-settings`
**What it does**: Configure OpenRouter system API key
**Endpoint**: `PUT /api/v1/llm/providers/{id}`

**How to use**:
1. Go to: https://your-domain.com/admin/openrouter-settings
2. Enter OpenRouter API key: `sk-or-v1-...`
3. Click **Save** → Key stored as `api_key_encrypted`
4. Click **Test** → Validates key works

---

### ⚠️ Partially Working

**Page**: `LLMProviderManagement.jsx`
**Route**: `/admin/llm-management` (or similar)
**What it does**: Configure ALL providers (OpenAI, Anthropic, Google, etc.)
**Endpoints**:
- `POST /api/v1/llm/providers` - Create provider with API key
- `PUT /api/v1/llm/providers/{id}` - Update provider with API key

**How to use**:
1. Go to: https://your-domain.com/admin/llm-management
2. Click **Add Provider** button
3. Fill form:
   - Provider Name: `OpenAI`
   - Provider Type: `openai`
   - **API Key**: `sk-proj-...`
   - Base URL: `https://api.openai.com/v1`
4. Click **Create** → Provider added with system key

**⚠️ Issue**: Database schema missing `encrypted_api_key` column!

---

### ❌ Not Implemented

**Dedicated System Keys Page**: DOES NOT EXIST YET
**Recommended**: Create `/admin/system-provider-keys` page

---

## Key Distinction

| Type | Who Sets | Where Stored | Used For |
|------|----------|--------------|----------|
| **System Provider Key** | Admin | Database or `.env` | Metering ALL users |
| **User BYOK Key** | User | Keycloak attributes | User pays directly |

---

## Environment Variables (Current Best Practice)

**File**: `/home/muut/Production/UC-Cloud/services/ops-center/.env.auth`

```bash
# System Provider Keys (used when users don't have BYOK)
OPENROUTER_API_KEY=sk-or-v1-...
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-api03-...
GOOGLE_API_KEY=AIza...
TOGETHER_API_KEY=...
HUGGINGFACE_TOKEN=hf_...
GROQ_API_KEY=gsk_...
```

**⚠️ Requires container restart to update**

**Restart command**:
```bash
docker restart ops-center-direct
```

---

## Where to Get API Keys

- **OpenRouter**: https://openrouter.ai/keys (Universal proxy for 348+ models)
- **OpenAI**: https://platform.openai.com/api-keys (GPT-4, GPT-3.5)
- **Anthropic**: https://console.anthropic.com/account/keys (Claude 3)
- **Google AI**: https://makersuite.google.com/app/apikey (Gemini, PaLM)
- **Together AI**: https://api.together.xyz/settings/api-keys (Open-source models)
- **HuggingFace**: https://huggingface.co/settings/tokens (10K+ models)
- **Groq**: https://console.groq.com/keys (Fast inference)

---

## Recommended: OpenRouter Only

**Why OpenRouter is enough**:
- Universal proxy supporting 348+ models from all providers
- Single API key gives access to:
  - OpenAI (GPT-4, GPT-3.5, o1, o3)
  - Anthropic (Claude 3 Opus, Sonnet, Haiku)
  - Google (Gemini Pro, Ultra)
  - Meta (Llama 3, Llama 2)
  - Mistral, Cohere, and 300+ more
- Unified billing and rate limits
- No need to manage multiple provider keys

**Setup**:
1. Create account at https://openrouter.ai
2. Add credits ($5 minimum)
3. Generate API key: https://openrouter.ai/keys
4. Set in Ops Center: `OpenRouterSettings.jsx`
5. Done! All 348 models available

**Cost**: Pay-as-you-go, typically $0.10-$1.00 per 1M tokens

---

## User BYOK (Different System!)

**User BYOK keys are managed separately**:
- **User Page**: `/admin/account/api-keys`
- **Component**: `AccountAPIKeys.jsx`
- **Storage**: Keycloak user attributes (encrypted)
- **Endpoints**:
  - `POST /api/v1/llm/byok/keys` - Add user BYOK key
  - `GET /api/v1/llm/byok/keys` - List user BYOK keys
  - `DELETE /api/v1/llm/byok/keys/{provider}` - Delete user BYOK key

**How it works**:
1. User goes to **Account → API Keys**
2. User adds their own OpenRouter/OpenAI/Anthropic key
3. User's requests use their key (not system key)
4. User pays provider directly
5. System doesn't charge credits

---

## Implementation TODO

**To fix system key management**:

### Phase 1: Database Schema ✅ **HIGH PRIORITY**
```sql
ALTER TABLE llm_providers
ADD COLUMN encrypted_api_key TEXT NULL;

ALTER TABLE llm_providers
ADD COLUMN api_key_source VARCHAR(50) DEFAULT 'environment';

ALTER TABLE llm_providers
ADD COLUMN api_key_updated_at TIMESTAMP NULL;
```

### Phase 2: Backend API ✅ **HIGH PRIORITY**
```python
# Add to llm_provider_management_api.py

@router.put("/{provider_id}/system-key")
async def update_provider_system_key(provider_id, api_key):
    # Encrypt and store system key
    pass

@router.post("/{provider_id}/test-system-key")
async def test_provider_system_key(provider_id, api_key):
    # Test key before saving
    pass
```

### Phase 3: Admin UI ✅ **MEDIUM PRIORITY**
- **Option A**: Update `LLMProviderManagement.jsx` with clearer labels
- **Option B**: Create new `/admin/system-provider-keys` page
- **Recommended**: Option B (cleaner separation)

---

## Quick Diagnosis Commands

### Check if system keys are set
```bash
# Environment variables
docker exec ops-center-direct env | grep -E "OPENROUTER|OPENAI|ANTHROPIC|GOOGLE"

# Database (if column exists)
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c \
  "SELECT provider_name, encrypted_api_key IS NOT NULL as has_key FROM llm_providers;"
```

### Test system key manually
```bash
# OpenRouter
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer sk-or-v1-YOUR_KEY" \
  -H "HTTP-Referer: https://your-domain.com"

# OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-proj-YOUR_KEY"

# Anthropic
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: sk-ant-YOUR_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-haiku-20240307","max_tokens":1,"messages":[{"role":"user","content":"Hi"}]}'
```

---

## Support

**Questions?**
- Read full documentation: `/services/ops-center/docs/ADMIN_PROVIDER_KEY_MANAGEMENT.md`
- Check backend code: `/services/ops-center/backend/litellm_api.py`
- Review UI pages:
  - `/services/ops-center/src/pages/OpenRouterSettings.jsx`
  - `/services/ops-center/src/pages/LLMProviderManagement.jsx`
  - `/services/ops-center/src/pages/account/AccountAPIKeys.jsx`

**Troubleshooting**:
1. "No LLM providers configured" error
   → Set `OPENROUTER_API_KEY` in `.env.auth`
2. "Invalid API key" error
   → Test key manually with curl commands above
3. Keys not persisting
   → Database schema missing `encrypted_api_key` column (see Phase 1)

---

**Document Status**: ✅ Complete • Last verified: 2025-10-27
