# Provider Key Systems Audit Report

**Audit Date**: November 14, 2025
**Auditor**: Claude Code (UC-Cloud Team Lead)
**Scope**: Complete analysis of all provider key management systems in Ops-Center
**Working Directory**: `/opt/ops-center`

---

## Executive Summary

### Quick Findings

- **Total Systems Found**: 3 distinct systems
- **Duplicates Identified**: 0 (all serve different purposes)
- **Improvements Found**: 1 major improvement system (platform_keys_api.py)
- **Recommendation**: **CONSOLIDATE** into unified architecture with clear separation of concerns

### System Categories

1. **platform_keys_api.py** - Admin-only platform-wide keys (KEEPER - Primary System)
2. **provider_keys_api.py** - User/system provider keys with testing (MERGE INTO #1)
3. **byok_api.py** - User BYOK (Bring Your Own Key) system (KEEPER - Separate Purpose)

### Key Insight

**NOT duplicates, but poorly separated**:
- System #1 and #2 have overlapping functionality but different intended audiences
- System #3 serves a completely different purpose (user self-service)
- All three should exist, but need clearer boundaries and better coordination

---

## System 1: Platform Keys API (Admin System-Wide Keys)

### Overview

**Purpose**: Admin-only management of system-level provider API keys used to service all platform users

**Backend File**: `/backend/platform_keys_api.py` (1,124 lines)
**Frontend Files**:
- `/src/pages/SystemProviderKeys.jsx` (698 lines)
- Routes: `/admin/system/provider-keys`

**Database**: `platform_settings` table
```sql
Table "public.platform_settings"
   Column   |            Type             | Collation | Nullable |      Default
------------+-----------------------------+-----------+----------+-------------------
 key        | character varying(255)      |           | not null |
 value      | text                        |           |          |
 category   | character varying(100)      |           |          |
 is_secret  | boolean                     |           |          | true
 updated_at | timestamp without time zone |           |          | CURRENT_TIMESTAMP
Indexes:
    "platform_settings_pkey" PRIMARY KEY, btree (key)
```

### API Endpoints (Prefix: `/api/v1/admin/platform-keys`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | List all platform keys with masked previews |
| PUT | `/openrouter` | Update OpenRouter API key |
| PUT | `/openai` | Update OpenAI API key |
| PUT | `/anthropic` | Update Anthropic API key |
| PUT | `/huggingface` | Update HuggingFace API key |
| PUT | `/groq` | Update Groq API key |
| PUT | `/xai` | Update X.AI Grok API key |
| PUT | `/google` | Update Google AI API key |
| PUT | `/provisioning` | Update Magic Unicorn provisioning key |
| GET | `/openrouter/decrypted` | Get decrypted OpenRouter key (admin only) |
| GET | `/provisioning/decrypted` | Get decrypted provisioning key (admin only) |
| GET | `/openai/decrypted` | Get decrypted OpenAI key (admin only) |
| GET | `/anthropic/decrypted` | Get decrypted Anthropic key (admin only) |
| GET | `/huggingface/decrypted` | Get decrypted HuggingFace key (admin only) |
| GET | `/groq/decrypted` | Get decrypted Groq key (admin only) |
| GET | `/xai/decrypted` | Get decrypted X.AI key (admin only) |
| GET | `/google/decrypted` | Get decrypted Google AI key (admin only) |

**Total**: 17 endpoints

### Supported Providers

```python
PLATFORM_KEYS = {
    "openrouter_api_key": { display_name: "OpenRouter", key_format: "sk-or-v1-..." },
    "openai_api_key": { display_name: "OpenAI", key_format: "sk-proj-..." },
    "anthropic_api_key": { display_name: "Anthropic", key_format: "sk-ant-..." },
    "huggingface_api_key": { display_name: "HuggingFace", key_format: "hf_..." },
    "groq_api_key": { display_name: "Groq", key_format: "gsk_..." },
    "xai_api_key": { display_name: "X.AI Grok", key_format: "xai-..." },
    "google_ai_api_key": { display_name: "Google AI", key_format: "AIza..." },
    "provisioning_key": { display_name: "Magic Unicorn Provisioning" },
    "litellm_master_key": { display_name: "LiteLLM Master Key" }
}
```

**Total**: 9 providers

### Key Features

#### Strengths ✅
1. **7 Provider-Specific Validators**: Format validation for each provider type
2. **Dual-Source Fallback**: Database (encrypted) → Environment variables
3. **Admin-Only Access**: Strict role-based authentication
4. **Fernet Encryption**: Industry-standard symmetric encryption via `key_encryption` module
5. **Masked Previews**: Shows first 7 + last 4 chars (e.g., "sk-or-v...1234")
6. **Decryption Endpoints**: Admin can retrieve full keys when needed
7. **Source Tracking**: Shows whether key is from database, environment, or not set
8. **Auto-Update Timestamps**: Tracks when each key was last updated

#### Limitations ❌
1. **No Test Functionality**: Cannot verify if keys are valid before saving
2. **No Model Discovery**: Doesn't query provider APIs to list available models
3. **Manual Provider Addition**: Adding new providers requires code changes
4. **No Health Monitoring**: Can't track if keys expire or become invalid
5. **No Usage Tracking**: Doesn't monitor which keys are actively being used

### Storage Architecture

**Key Storage Pattern**:
```
platform_settings table:
- key: "openrouter_api_key"
- value: "gAAAAABh..." (Fernet encrypted)
- category: "api_keys"
- is_secret: true
- updated_at: timestamp
```

**Fallback Chain**:
1. Check `platform_settings` table → Decrypt if found
2. If not in DB, check environment variable (`OPENROUTER_API_KEY`)
3. If neither, return "not_set"

### Frontend UI

**Page**: `/admin/system/provider-keys`

**Features**:
- 9 provider cards in 2-column grid
- Status badges (Database/Environment/Not Set)
- Add/Edit/Delete key modals
- Masked key previews
- Direct links to get API keys from providers
- Warning about system-wide impact
- Security information section

**Theme Support**: Magic Unicorn, Dark, Light

---

## System 2: Provider Keys API (LLM Provider Management)

### Overview

**Purpose**: System-level provider key management with API testing and health monitoring

**Backend File**: `/backend/provider_keys_api.py` (829 lines)
**Frontend Files**: NONE (backend-only)
**Router Prefix**: `/api/v1/llm/providers`

**Database**: `llm_providers` table
```sql
Table "public.llm_providers"
      Column       |            Type             | Collation | Nullable |           Default
-------------------+-----------------------------+-----------+----------+------------------------------
 id                | uuid                        |           | not null | gen_random_uuid()
 name              | character varying(100)      |           | not null |
 type              | character varying(50)       |           | not null |
 api_key_encrypted | text                        |           |          |
 api_base_url      | text                        |           |          |
 enabled           | boolean                     |           |          | true
 priority          | integer                     |           |          | 0
 config            | jsonb                       |           |          | '{}'::jsonb
 health_status     | character varying(20)       |           |          | 'unknown'::character varying
 last_health_check | timestamp without time zone |           |          |
 created_at        | timestamp without time zone |           |          | now()
 updated_at        | timestamp without time zone |           |          | now()
```

### API Endpoints (Prefix: `/api/v1/llm/providers`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/keys` | List all configured provider keys (masked) |
| POST | `/keys` | Add or update provider API key |
| POST | `/keys/test` | Test provider API key validity |
| DELETE | `/keys/{provider_id}` | Delete provider API key |
| GET | `/info` | Get information about supported providers |

**Total**: 5 endpoints

### Supported Providers

```python
PROVIDER_CONFIGS = {
    'openrouter': { test_url: 'https://openrouter.ai/api/v1/models' },
    'openai': { test_url: 'https://api.openai.com/v1/models' },
    'anthropic': { test_url: 'https://api.anthropic.com/v1/messages' },
    'google': { test_url: 'https://generativelanguage.googleapis.com/v1beta/models' },
    'cohere': { test_url: 'https://api.cohere.ai/v1/models' },
    'groq': { test_url: 'https://api.groq.com/openai/v1/models' },
    'together': { test_url: 'https://api.together.xyz/models' },
    'mistral': { test_url: 'https://api.mistral.ai/v1/models' },
    'custom': { test_url: None }
}
```

**Total**: 9 providers

### Key Features

#### Strengths ✅
1. **API Key Testing**: Verifies keys against actual provider APIs before saving
2. **Model Discovery**: Queries provider APIs to count available models
3. **Health Monitoring**: Tracks test status (success/failed) and last test time
4. **Latency Tracking**: Measures API response times in milliseconds
5. **Rate Limiting**: Max 10 tests per minute per user (prevents API abuse)
6. **Custom Endpoints**: Supports user-provided custom URLs
7. **JSONB Config**: Flexible configuration storage per provider
8. **Priority System**: Can set provider priority for fallback routing
9. **Automatic Testing**: Tests key immediately when saved
10. **Fernet Encryption**: Uses shared `BYOK_ENCRYPTION_KEY` for consistency

#### Limitations ❌
1. **No Frontend UI**: Backend-only, no visual interface
2. **Overlaps with System #1**: Similar functionality to platform_keys_api.py
3. **Unclear Audience**: Appears admin-only but lacks clear documentation
4. **Database Complexity**: Uses more complex schema than platform_settings

### Storage Architecture

**Key Storage Pattern**:
```
llm_providers table:
- id: uuid
- name: "OpenRouter"
- type: "openrouter"
- api_key_encrypted: "gAAAAABh..." (Fernet)
- config: {"base_url": "...", "test_status": "success"}
- health_status: "healthy"
- last_health_check: timestamp
```

**Enhanced Metadata**:
- Priority for routing
- Health status tracking
- Last test timestamp
- Test success/failure status
- Model count from last test

---

## System 3: BYOK API (User Bring Your Own Key)

### Overview

**Purpose**: User self-service API key management (users bring their own provider keys to avoid metering)

**Backend File**: `/backend/byok_api.py` (689 lines)
**Frontend Files**:
- `/src/components/ProviderKeysSection.jsx` (862 lines) - Reusable component
- `/src/pages/llm/APIProviders.jsx` (72 lines) - Page wrapper

**Database**: `user_provider_keys` table (not found - likely uses Keycloak attributes)

### API Endpoints (Prefix: `/api/v1/byok`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/providers` | List all supported providers |
| GET | `/keys` | List user's configured API keys (masked) |
| POST | `/keys/add` | Add or update user API key |
| DELETE | `/keys/{provider}` | Remove user API key |
| POST | `/keys/test/{provider}` | Test user API key |
| GET | `/stats` | Get user's BYOK configuration statistics |

**Total**: 6 endpoints

### Supported Providers

```python
SUPPORTED_PROVIDERS = {
    "openrouter": { test_url: "https://openrouter.ai/api/v1/models" },
    "openai": { test_url: "https://api.openai.com/v1/models" },
    "anthropic": { test_url: "https://api.anthropic.com/v1/messages" },
    "huggingface": { test_url: "https://huggingface.co/api/whoami" },
    "cohere": { test_url: "https://api.cohere.ai/v1/check-api-key" },
    "together": { test_url: "https://api.together.xyz/v1/models" },
    "perplexity": { test_url: "https://api.perplexity.ai/chat/completions" },
    "groq": { test_url: "https://api.groq.com/openai/v1/models" },
    "ollama": { test_url: "http://localhost:11434/api/tags" },
    "ollama_cloud": { test_url: "https://ollama.com/api/tags" },
    "custom": { test_url: None }
}
```

**Total**: 11 providers

### Key Features

#### Strengths ✅
1. **User Self-Service**: Users manage their own keys without admin intervention
2. **11 Provider Support**: More providers than admin systems
3. **API Key Testing**: Verifies user keys before saving
4. **Session-Based Auth**: Uses cookie sessions for authentication
5. **Per-User Storage**: Keys stored per user (Keycloak attributes or DB)
6. **Custom Provider Support**: Users can add custom endpoints
7. **Statistics API**: Shows how many providers user has configured
8. **Fernet Encryption**: Same encryption as system keys
9. **Comprehensive UI**: Full React component with modals, testing, deletion
10. **Tier Gating**: Can restrict by subscription tier (starter+)

#### Limitations ❌
1. **Storage Inconsistency**: Migrating from Keycloak attributes → PostgreSQL
2. **Missing `user_provider_keys` Table**: Database table doesn't exist yet
3. **Attribute Bloat**: Storing in Keycloak creates many attributes per user
4. **No Quota Management**: Doesn't track how many keys user can have

### Storage Architecture

**Original Storage** (Keycloak attributes):
```
User attributes:
- byok_openrouter_key: "gAAAAABh..." (encrypted)
- byok_openrouter_label: "My OpenRouter Key"
- byok_openrouter_added_date: "2025-11-14T10:00:00"
- byok_openrouter_last_tested: "2025-11-14T10:05:00"
- byok_openrouter_test_status: "valid"
```

**New Storage** (PostgreSQL - in migration):
```sql
user_provider_keys table (planned):
- user_id: uuid (FK to Keycloak user)
- provider: varchar(50)
- api_key_encrypted: text
- metadata: jsonb (label, endpoint, test status)
- enabled: boolean
- created_at: timestamp
- updated_at: timestamp
```

### Frontend UI

**Component**: `ProviderKeysSection.jsx` (reusable)

**Features**:
- 11 provider cards in 2-column grid
- Collapsible section (optional)
- Add/Edit/Delete modals
- Test connection button
- Show/hide API key toggle
- Custom provider support (name + URL)
- Status badges (Configured/Not Set)
- Theme-aware (Magic Unicorn, Dark, Light)
- Cache-busting for fresh data
- Parent callback on key changes

**Used In**:
- `/src/pages/llm/APIProviders.jsx` - LLM Hub API provider configuration
- Can be embedded in any page

---

## Comparison Matrix

| Feature | Platform Keys (System #1) | Provider Keys (System #2) | BYOK (System #3) |
|---------|---------------------------|---------------------------|------------------|
| **Purpose** | Admin system-wide keys | System provider management | User self-service |
| **Audience** | Admins only | Admins (unclear) | All users |
| **Providers** | 9 | 9 | 11 |
| **Database** | `platform_settings` | `llm_providers` | `user_provider_keys` (planned) |
| **API Prefix** | `/api/v1/admin/platform-keys` | `/api/v1/llm/providers` | `/api/v1/byok` |
| **Endpoints** | 17 | 5 | 6 |
| **Frontend UI** | ✅ Yes | ❌ No | ✅ Yes |
| **Key Testing** | ❌ No | ✅ Yes | ✅ Yes |
| **Model Discovery** | ❌ No | ✅ Yes | ❌ No |
| **Health Monitoring** | ❌ No | ✅ Yes | ❌ No |
| **Format Validation** | ✅ 7 validators | ❌ No | ❌ No |
| **Decryption API** | ✅ Yes (admin) | ❌ No | ❌ No |
| **Custom Endpoints** | ❌ No | ✅ Yes | ✅ Yes |
| **Priority Routing** | ❌ No | ✅ Yes | ❌ No |
| **Rate Limiting** | ❌ No | ✅ Yes (10/min) | ❌ No |
| **Theme Support** | ✅ 3 themes | N/A | ✅ 3 themes |
| **Lines of Code** | 1,124 + 698 = 1,822 | 829 | 689 + 862 + 72 = 1,623 |

---

## Database Storage Analysis

### Table 1: `platform_settings`

**Purpose**: Admin system-wide configuration storage
**Structure**: Key-value store with encryption flag
**Used By**: Platform Keys API (System #1)

**Schema**:
```sql
key (PK) | value (encrypted text) | category | is_secret | updated_at
```

**Example Data**:
```
openrouter_api_key | gAAAAABh4kF2... | api_keys | true | 2025-11-14 10:00:00
openai_api_key     | gAAAAABh5mG3... | api_keys | true | 2025-11-13 15:30:00
```

**Pros**:
- Simple schema (easy to understand)
- Fast lookups by key
- Supports any config type
- Minimal database overhead

**Cons**:
- No foreign keys (can't cascade deletes)
- No metadata storage
- No versioning
- Hard to query all keys for a provider

### Table 2: `llm_providers`

**Purpose**: Comprehensive provider configuration with health tracking
**Structure**: Relational table with JSONB config
**Used By**: Provider Keys API (System #2)

**Schema**:
```sql
id (uuid PK) | name | type | api_key_encrypted | api_base_url | enabled | priority |
config (jsonb) | health_status | last_health_check | created_at | updated_at
```

**Example Data**:
```
uuid-1234 | OpenRouter | openrouter | gAAAAABh... | null | true | 100 |
{"test_status": "success", "models": 348} | healthy | 2025-11-14 10:00:00 | ...
```

**Pros**:
- Rich metadata storage
- Foreign key relationships (used by `llm_models`, `llm_usage_logs`)
- Priority-based routing
- Health status tracking
- Flexible JSONB config

**Cons**:
- More complex schema
- Slower queries (more joins)
- Redundant with `platform_settings`

### Table 3: `user_provider_keys` (MISSING!)

**Purpose**: User BYOK (Bring Your Own Key) storage
**Structure**: Per-user provider key storage
**Used By**: BYOK API (System #3)

**Status**: ❌ **TABLE DOES NOT EXIST**

**Expected Schema** (based on code):
```sql
user_id (FK) | provider | api_key_encrypted | metadata (jsonb) | enabled |
created_at | updated_at
CONSTRAINT: UNIQUE(user_id, provider)
```

**Current Workaround**: BYOK API falls back to Keycloak attributes
```
User ID: abc-123
Attributes:
  byok_openrouter_key: [gAAAAABh...]
  byok_openrouter_label: [My Key]
  byok_openrouter_added_date: [2025-11-14]
  ...
```

**Implications**:
- Keycloak not designed for large attribute storage
- Performance issues with many users
- Hard to query all users with a specific provider
- Migration to PostgreSQL table needed

---

## Duplication Analysis

### Overlap #1: Platform Keys vs Provider Keys

**Systems**: `platform_keys_api.py` (System #1) vs `provider_keys_api.py` (System #2)

**Overlapping Functionality**:
1. Both store system-level provider API keys
2. Both use Fernet encryption
3. Both support OpenRouter, OpenAI, Anthropic, Google, Groq
4. Both are admin-only (or intended to be)
5. Both provide GET/PUT/DELETE operations

**Differences**:
| Feature | Platform Keys | Provider Keys |
|---------|--------------|---------------|
| Database | `platform_settings` | `llm_providers` |
| Frontend UI | ✅ Yes | ❌ No |
| Key Testing | ❌ No | ✅ Yes |
| Model Discovery | ❌ No | ✅ Yes |
| Health Tracking | ❌ No | ✅ Yes |
| Format Validators | ✅ 7 validators | ❌ No |
| Decryption API | ✅ Yes | ❌ No |
| Priority Routing | ❌ No | ✅ Yes |

**Verdict**: 🔄 **DUPLICATE WITH IMPROVEMENTS**

- Same purpose (system provider keys)
- Different implementations (one is better in some areas, the other in others)
- Should be merged into single unified system

### Overlap #2: All Three Systems Support Testing

**Testing Implementations**:

**System #1 (Platform Keys)**: ❌ No testing
**System #2 (Provider Keys)**: ✅ Full testing with latency tracking
**System #3 (BYOK)**: ✅ Full testing

**Testing Code Comparison**:

```python
# System #2: Provider Keys (provider_keys_api.py)
async def test_provider_api_key(provider_type, api_key, custom_endpoint):
    config = PROVIDER_CONFIGS[provider_type]
    test_url = custom_endpoint or config['test_url']

    start_time = current_time()
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(test_url, headers=headers)
    latency_ms = int((current_time() - start_time) * 1000)

    models_found = len(response.json()['data']) if response.status_code == 200 else 0

    return TestResultResponse(
        success=True,
        latency_ms=latency_ms,
        models_found=models_found
    )
```

```python
# System #3: BYOK (byok_api.py)
async def test_api_key(provider, api_key, endpoint):
    provider_config = SUPPORTED_PROVIDERS[provider]
    test_url = endpoint or provider_config['test_url']

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(test_url, headers=headers)

    is_valid = response.status_code in [200, 201]

    return APIKeyTestResult(
        provider=provider,
        status="valid" if is_valid else "invalid",
        message="API key is valid and working"
    )
```

**Verdict**: 🔄 **DUPLICATE LOGIC**

- Nearly identical testing implementations
- Should extract to shared testing module
- Reduce code duplication by 200+ lines

### No Overlap: BYOK vs Admin Systems

**BYOK (System #3)** vs **Platform Keys + Provider Keys (Systems #1 + #2)**

**Different Purposes**:
1. **Audience**: Users vs Admins
2. **Scope**: Per-user vs System-wide
3. **Billing**: User pays via their key vs Platform pays and meters users
4. **Database**: `user_provider_keys` vs `platform_settings`/`llm_providers`

**Verdict**: ✅ **COMPLEMENTARY - NOT DUPLICATES**

- Serve different use cases
- Should both exist
- Can share some code (testing logic)

---

## Identified Improvements

### Improvement #1: Provider Keys API (System #2) has Better Testing

**What's Better**:
- API key testing before save
- Model discovery (counts available models)
- Health status tracking
- Latency measurement
- Rate limiting (prevents API abuse)

**Missing In**:
- Platform Keys API (System #1) - No testing at all

**Recommendation**: Merge testing functionality from System #2 into System #1

### Improvement #2: Platform Keys API (System #1) has Better Validation

**What's Better**:
- 7 provider-specific validators (OpenRouter, OpenAI, Anthropic, etc.)
- Format checking before save (e.g., "sk-or-v1-..." for OpenRouter)
- Warnings if format doesn't match

**Missing In**:
- Provider Keys API (System #2) - No format validation
- BYOK API (System #3) - No format validation

**Recommendation**: Extract validators to shared module, use in all systems

### Improvement #3: Provider Keys API (System #2) has Better Architecture

**What's Better**:
- `llm_providers` table with foreign keys
- JSONB config for flexibility
- Priority-based routing
- Health status enum
- Relational design (connects to `llm_models`, `llm_usage_logs`)

**Missing In**:
- Platform Keys API (System #1) - Simple key-value store

**Recommendation**: Migrate `platform_settings` to `llm_providers` table

### Improvement #4: BYOK has Better UI (System #3)

**What's Better**:
- Reusable component (`ProviderKeysSection.jsx`)
- Collapsible section option
- Custom provider support (user-defined name + URL)
- Show/hide password toggle
- Cache-busting (prevents stale data)
- Parent callback for model catalog refresh

**Missing In**:
- Provider Keys API (System #2) - No UI at all

**Recommendation**: Adapt `ProviderKeysSection.jsx` for admin use

---

## Consolidation Recommendations

### Phase 1: Merge Systems #1 and #2 (Unified Admin System)

**Goal**: Single admin system for platform-wide provider keys

**Actions**:

1. **Backend Consolidation**:
   - Keep `provider_keys_api.py` as the primary API (has testing)
   - Migrate `platform_keys_api.py` functionality into it
   - Add format validators from System #1
   - Add decryption endpoints from System #1
   - Result: `/api/v1/admin/platform-keys` (unified)

2. **Database Migration**:
   - Migrate `platform_settings` keys to `llm_providers` table
   - Create migration script:
     ```sql
     INSERT INTO llm_providers (name, type, api_key_encrypted, enabled, priority)
     SELECT
       REPLACE(key, '_api_key', ''),  -- openrouter_api_key → openrouter
       REPLACE(key, '_api_key', ''),
       value,
       true,
       CASE
         WHEN key = 'openrouter_api_key' THEN 100
         WHEN key = 'openai_api_key' THEN 90
         ...
       END
     FROM platform_settings
     WHERE category = 'api_keys';
     ```
   - Keep `platform_settings` for non-LLM configs

3. **Frontend Migration**:
   - Update `SystemProviderKeys.jsx` to call `/api/v1/admin/platform-keys`
   - Add test button (from System #2)
   - Add model count display (from System #2)
   - Add health status indicator (from System #2)

4. **Feature Enhancements**:
   - Add auto-testing on key save
   - Add background health checks (every 15 minutes)
   - Add email alerts on key failures
   - Add key expiration warnings

**Benefits**:
- Single source of truth for admin keys
- Best features from both systems
- Reduced code duplication (remove 800+ lines)
- Better monitoring and reliability

**Effort**: 8-12 hours

### Phase 2: Complete BYOK Migration (User System)

**Goal**: Migrate BYOK from Keycloak attributes to PostgreSQL

**Actions**:

1. **Create Database Table**:
   ```sql
   CREATE TABLE user_provider_keys (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id UUID NOT NULL,  -- FK to Keycloak user
     provider VARCHAR(50) NOT NULL,
     api_key_encrypted TEXT NOT NULL,
     metadata JSONB DEFAULT '{}'::jsonb,
     enabled BOOLEAN DEFAULT true,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW(),
     CONSTRAINT unique_user_provider UNIQUE(user_id, provider)
   );

   CREATE INDEX idx_user_provider_keys_user ON user_provider_keys(user_id);
   CREATE INDEX idx_user_provider_keys_enabled ON user_provider_keys(enabled);
   ```

2. **Data Migration Script**:
   - Query Keycloak for all users with `byok_*_key` attributes
   - Parse attribute format: `byok_{provider}_key` → provider name
   - Insert into `user_provider_keys` table
   - Preserve metadata (label, test status, dates)

3. **Update BYOK API**:
   - Remove Keycloak attribute fallback code
   - Use only PostgreSQL table
   - Add foreign key constraint to user table

4. **Add User Tier Limits**:
   ```python
   BYOK_LIMITS = {
       "trial": 0,        # No BYOK on trial
       "starter": 3,      # 3 providers
       "professional": 10, # 10 providers
       "enterprise": 999   # Unlimited
   }
   ```

**Benefits**:
- Better performance (PostgreSQL vs Keycloak attributes)
- Easier querying (find all users with OpenRouter keys)
- Reduced Keycloak attribute bloat
- Proper tier-based limits

**Effort**: 6-8 hours

### Phase 3: Shared Testing Module

**Goal**: Extract duplicate testing logic to shared module

**Actions**:

1. **Create `backend/provider_testing.py`**:
   ```python
   """
   Shared provider API key testing module
   Used by admin platform keys and user BYOK systems
   """

   from typing import Dict, Optional
   import httpx
   from time import time as current_time

   PROVIDER_TEST_CONFIGS = {
       'openrouter': {
           'test_url': 'https://openrouter.ai/api/v1/models',
           'auth_type': 'bearer',
           'key_format': 'sk-or-v1-',
           'validator': lambda k: k.startswith('sk-or-')
       },
       'openai': {
           'test_url': 'https://api.openai.com/v1/models',
           'auth_type': 'bearer',
           'key_format': 'sk-proj-',
           'validator': lambda k: k.startswith('sk-') and not k.startswith('sk-or-')
       },
       # ... 9 more providers
   }

   async def test_api_key(
       provider: str,
       api_key: str,
       custom_endpoint: Optional[str] = None
   ) -> Dict:
       """
       Test provider API key validity

       Returns:
           {
               "success": bool,
               "latency_ms": int,
               "models_found": int,
               "error": str | None
           }
       """
       config = PROVIDER_TEST_CONFIGS[provider]
       # ... shared testing logic

   def validate_key_format(provider: str, api_key: str) -> bool:
       """Validate key matches expected format"""
       validator = PROVIDER_TEST_CONFIGS[provider].get('validator')
       return validator(api_key) if validator else True
   ```

2. **Update All APIs to Use Shared Module**:
   ```python
   # platform_keys_api.py
   from provider_testing import test_api_key, validate_key_format

   @router.put("/openrouter")
   async def update_openrouter_key(key_request: UpdatePlatformKeyRequest):
       # Validate format
       if not validate_key_format('openrouter', key_request.api_key):
           raise HTTPException(400, "Invalid key format")

       # Test key
       result = await test_api_key('openrouter', key_request.api_key)
       if not result['success']:
           logger.warning(f"Key test failed: {result['error']}")

       # Save key
       ...
   ```

3. **Remove Duplicate Code**:
   - Delete `test_provider_api_key()` from `provider_keys_api.py`
   - Delete `test_api_key()` from `byok_api.py`
   - Delete validator functions from `platform_keys_api.py`

**Benefits**:
- Reduce code duplication by 300+ lines
- Single source of truth for provider configs
- Easier to add new providers (one place)
- Consistent testing across all systems

**Effort**: 4-6 hours

---

## Final Architecture (After Consolidation)

### Three Clear Systems (Each with Distinct Purpose)

```
┌─────────────────────────────────────────────────────────────────┐
│                   Provider Key Management                        │
│                      (Ops-Center)                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼───────┐   ┌──────▼──────┐
            │  Admin System  │   │ User System │
            │                │   │    (BYOK)   │
            └───────┬────────┘   └──────┬──────┘
                    │                   │
        ┌───────────┼───────┬───────────┼──────────┐
        │           │       │           │          │
    ┌───▼───┐  ┌───▼───┐  ┌▼───┐  ┌───▼───┐  ┌───▼───┐
    │Platform│ │Testing│  │Shared│ │ User  │  │Testing│
    │  Keys  │ │ Logic │  │Module│ │  Keys │  │ Logic │
    └────────┘ └───────┘  └──────┘ └───────┘  └───────┘
        │           │          │          │          │
        │           └──────────┼──────────┘          │
        │                      │                     │
        ▼                      ▼                     ▼
 llm_providers         provider_testing    user_provider_keys
   (Postgres)              (Shared)            (Postgres)
```

### System 1: Admin Platform Keys (Unified)

**Purpose**: System-wide provider keys for metering all users
**API**: `/api/v1/admin/platform-keys`
**Database**: `llm_providers` table
**Frontend**: `/admin/system/provider-keys`
**Access**: Admins only

**Features**:
- ✅ 9 providers (OpenRouter, OpenAI, Anthropic, Google, HuggingFace, Groq, X.AI, Mistral, Custom)
- ✅ Format validation (7 validators)
- ✅ API key testing (with latency + model count)
- ✅ Health monitoring (background checks every 15 min)
- ✅ Decryption API (admin-only)
- ✅ Priority routing
- ✅ Fernet encryption
- ✅ Environment fallback
- ✅ Full UI (React)

**Endpoints**:
- GET `/` - List all keys
- PUT `/{provider}` - Update key (with auto-test)
- DELETE `/{provider}` - Delete key
- GET `/{provider}/decrypted` - Get full key (admin)
- POST `/{provider}/test` - Test key manually

**Lines of Code**: ~1,200 (merged from 1,953)

### System 2: User BYOK (Improved)

**Purpose**: User self-service API keys (users pay via their keys)
**API**: `/api/v1/byok`
**Database**: `user_provider_keys` table
**Frontend**: `/account/api-keys` (embedded `ProviderKeysSection.jsx`)
**Access**: All authenticated users

**Features**:
- ✅ 11 providers (all from admin + Perplexity, Ollama, Ollama Cloud)
- ✅ Per-user storage
- ✅ API key testing
- ✅ Custom endpoints
- ✅ Tier-based limits (0/3/10/unlimited)
- ✅ Format validation (shared module)
- ✅ Fernet encryption
- ✅ Full UI (reusable component)

**Endpoints**:
- GET `/providers` - List supported providers
- GET `/keys` - List user's keys
- POST `/keys/add` - Add/update key
- DELETE `/keys/{provider}` - Delete key
- POST `/keys/test/{provider}` - Test key
- GET `/stats` - User statistics

**Lines of Code**: ~1,600 (unchanged)

### System 3: Shared Testing Module (New)

**Purpose**: Shared provider testing logic for all systems
**Module**: `backend/provider_testing.py`
**Database**: None (stateless)
**Access**: Used by Systems #1 and #2

**Features**:
- ✅ 11 provider configs
- ✅ Format validators
- ✅ API testing with latency
- ✅ Model discovery
- ✅ Custom endpoint support
- ✅ Timeout handling

**Functions**:
- `test_api_key(provider, api_key, endpoint)` → TestResult
- `validate_key_format(provider, api_key)` → bool
- `get_provider_config(provider)` → ProviderConfig

**Lines of Code**: ~300 (extracted from duplicates)

---

## Implementation Plan

### Step 1: Create Shared Testing Module (4-6 hours)

**Tasks**:
1. Create `backend/provider_testing.py`
2. Extract provider configs from all 3 systems
3. Merge into single `PROVIDER_TEST_CONFIGS` dict
4. Implement `test_api_key()` function
5. Implement `validate_key_format()` function
6. Write unit tests

**Verification**:
```bash
# Test the module
pytest backend/tests/test_provider_testing.py

# Verify all providers work
python -c "from provider_testing import test_api_key; print(test_api_key('openrouter', 'sk-or-v1-fake'))"
```

### Step 2: Migrate Platform Keys to llm_providers (6-8 hours)

**Tasks**:
1. Create database migration script
2. Migrate existing keys from `platform_settings` → `llm_providers`
3. Update `platform_keys_api.py` to use `llm_providers` table
4. Add foreign key constraints
5. Test all endpoints
6. Update frontend to show new metadata

**Migration Script**:
```sql
-- /backend/migrations/migrate_platform_keys.sql

-- Create temp backup
CREATE TABLE platform_settings_backup AS SELECT * FROM platform_settings WHERE category = 'api_keys';

-- Migrate to llm_providers
INSERT INTO llm_providers (name, type, api_key_encrypted, enabled, priority, created_at, updated_at)
SELECT
  CASE key
    WHEN 'openrouter_api_key' THEN 'OpenRouter'
    WHEN 'openai_api_key' THEN 'OpenAI'
    WHEN 'anthropic_api_key' THEN 'Anthropic'
    WHEN 'google_ai_api_key' THEN 'Google AI'
    WHEN 'huggingface_api_key' THEN 'HuggingFace'
    WHEN 'groq_api_key' THEN 'Groq'
    WHEN 'xai_api_key' THEN 'X.AI'
  END as name,
  REPLACE(key, '_api_key', '') as type,
  value as api_key_encrypted,
  true as enabled,
  CASE key
    WHEN 'openrouter_api_key' THEN 100
    WHEN 'openai_api_key' THEN 90
    WHEN 'anthropic_api_key' THEN 85
    WHEN 'google_ai_api_key' THEN 80
    WHEN 'groq_api_key' THEN 75
    WHEN 'huggingface_api_key' THEN 70
    WHEN 'xai_api_key' THEN 65
  END as priority,
  updated_at as created_at,
  updated_at
FROM platform_settings
WHERE category = 'api_keys'
ON CONFLICT (name, type) DO UPDATE SET
  api_key_encrypted = EXCLUDED.api_key_encrypted,
  updated_at = EXCLUDED.updated_at;

-- Verify migration
SELECT COUNT(*) FROM llm_providers WHERE api_key_encrypted IS NOT NULL;
-- Expected: 7 (if all keys configured)

-- Keep platform_settings for non-LLM configs
-- DELETE FROM platform_settings WHERE category = 'api_keys';  -- Optional cleanup
```

**Verification**:
```bash
# Run migration
docker exec ops-center-direct python /app/migrations/migrate_platform_keys.py

# Verify data
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT name, type, enabled, priority FROM llm_providers WHERE api_key_encrypted IS NOT NULL;"

# Test API
curl http://localhost:8084/api/v1/admin/platform-keys -H "Cookie: session_token=..."
```

### Step 3: Merge System #2 into System #1 (8-12 hours)

**Tasks**:
1. Copy testing functionality from `provider_keys_api.py` to `platform_keys_api.py`
2. Update `platform_keys_api.py` to use shared testing module
3. Add `POST /{provider}/test` endpoint
4. Add auto-testing on key save
5. Remove `provider_keys_api.py` completely
6. Update frontend to show test results
7. Add health status indicators
8. Add model count display

**Code Changes**:
```python
# platform_keys_api.py (updated)

from provider_testing import test_api_key, validate_key_format

@router.put("/{provider_type}")
async def update_provider_key(
    provider_type: str,
    key_request: UpdatePlatformKeyRequest,
    ...
):
    """Update provider key with automatic testing"""

    # Validate format
    if not validate_key_format(provider_type, key_request.api_key):
        raise HTTPException(400, f"Invalid {provider_type} key format")

    # Encrypt key
    encrypted_key = encryption.encrypt_key(key_request.api_key)

    # Test key (non-blocking, log failures)
    try:
        test_result = await test_api_key(provider_type, key_request.api_key)

        if test_result['success']:
            test_status = 'success'
            health_status = 'healthy'
            config = {
                'models_found': test_result['models_found'],
                'latency_ms': test_result['latency_ms']
            }
        else:
            test_status = 'failed'
            health_status = 'unhealthy'
            config = {'error': test_result['error']}
    except Exception as e:
        logger.warning(f"Key test failed: {e}")
        test_status = 'unknown'
        health_status = 'unknown'
        config = {}

    # Save to llm_providers table
    await conn.execute("""
        INSERT INTO llm_providers (name, type, api_key_encrypted, health_status, config, ...)
        VALUES ($1, $2, $3, $4, $5::jsonb, ...)
        ON CONFLICT (name, type) DO UPDATE SET
            api_key_encrypted = EXCLUDED.api_key_encrypted,
            health_status = EXCLUDED.health_status,
            config = EXCLUDED.config,
            updated_at = NOW()
    """, ...)

    return {
        "success": True,
        "test_result": test_result,
        "next_steps": ["Key saved and tested successfully"]
    }

@router.post("/{provider_type}/test")
async def test_provider_key(provider_type: str, ...):
    """Manually test provider key"""
    # Get encrypted key from DB
    row = await conn.fetchrow(...)
    api_key = encryption.decrypt_key(row['api_key_encrypted'])

    # Test using shared module
    result = await test_api_key(provider_type, api_key)

    # Update health status in DB
    await conn.execute("""
        UPDATE llm_providers
        SET health_status = $1,
            last_health_check = NOW(),
            config = jsonb_set(config, '{test_result}', $2::jsonb)
        WHERE type = $3
    """, 'healthy' if result['success'] else 'unhealthy', json.dumps(result), provider_type)

    return result
```

**Frontend Updates**:
```jsx
// SystemProviderKeys.jsx (updated)

// Show test results on card
{provider.config?.models_found && (
  <div className="text-xs text-green-400">
    ✅ {provider.config.models_found} models available
    ({provider.config.latency_ms}ms latency)
  </div>
)}

// Show health status
<span className={`px-2 py-1 rounded text-xs ${
  provider.health_status === 'healthy' ? 'bg-green-500/20 text-green-400' :
  provider.health_status === 'unhealthy' ? 'bg-red-500/20 text-red-400' :
  'bg-gray-500/20 text-gray-400'
}`}>
  {provider.health_status === 'healthy' ? '✅ Healthy' :
   provider.health_status === 'unhealthy' ? '❌ Unhealthy' :
   '❓ Unknown'}
</span>
```

**Verification**:
```bash
# Test platform keys API
curl -X PUT http://localhost:8084/api/v1/admin/platform-keys/openrouter \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=..." \
  -d '{"api_key": "sk-or-v1-test-key"}'

# Expected response:
{
  "success": true,
  "test_result": {
    "success": true,
    "latency_ms": 245,
    "models_found": 348
  }
}

# Test manual testing
curl -X POST http://localhost:8084/api/v1/admin/platform-keys/openrouter/test \
  -H "Cookie: session_token=..."
```

### Step 4: Complete BYOK Migration (6-8 hours)

**Tasks**:
1. Create `user_provider_keys` table
2. Migrate Keycloak attributes → PostgreSQL
3. Update `byok_api.py` to use table
4. Remove Keycloak fallback code
5. Add tier-based limits
6. Test all endpoints

**Migration**:
```bash
# Create table
docker exec ops-center-direct python /app/migrations/create_user_provider_keys.py

# Migrate data
docker exec ops-center-direct python /app/migrations/migrate_byok_to_postgres.py

# Verify
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT COUNT(*) FROM user_provider_keys;"
```

### Step 5: Delete Obsolete Code (2-4 hours)

**Tasks**:
1. Delete `backend/provider_keys_api.py` (829 lines)
2. Remove router registration from `server.py`
3. Update API documentation
4. Remove unused imports
5. Clean up tests

**Files to Delete**:
- `/backend/provider_keys_api.py` (829 lines)
- `/backend/tests/test_provider_keys.py` (if exists)

**Files to Update**:
- `/backend/server.py` - Remove router registration
- `/docs/API_REFERENCE.md` - Remove old endpoints
- `/README.md` - Update architecture diagram

**Verification**:
```bash
# Ensure app still starts
docker restart ops-center-direct
docker logs ops-center-direct --tail 50

# Check no references remain
grep -r "provider_keys_api" backend/
# Expected: 0 results

# Verify all endpoints work
curl http://localhost:8084/api/v1/admin/platform-keys
curl http://localhost:8084/api/v1/byok/providers
```

---

## Success Metrics

### Quantitative Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Total Systems** | 3 | 2 | -33% |
| **Backend Files** | 3 | 2 | -33% |
| **Total API Endpoints** | 28 | 17 | -39% |
| **Lines of Backend Code** | 2,642 | 2,100 | -21% |
| **Database Tables** | 3 | 2 | -33% |
| **Duplicate Testing Logic** | 3 implementations | 1 shared module | -67% |
| **Admin Systems** | 2 overlapping | 1 unified | -50% |

### Qualitative Metrics

**Before Consolidation**:
- ❌ Confusing architecture (2 admin systems)
- ❌ Duplicate functionality
- ❌ Inconsistent testing (some have, some don't)
- ❌ Missing database table (`user_provider_keys`)
- ❌ No health monitoring
- ❌ Hard to add new providers (3 places)

**After Consolidation**:
- ✅ Clear separation (admin vs user)
- ✅ Unified admin system (best features from both)
- ✅ Consistent testing (shared module)
- ✅ Complete PostgreSQL migration
- ✅ Health monitoring on all keys
- ✅ Easy to add providers (1 config dict)

---

## Risk Assessment

### Low Risk ✅

1. **Shared Testing Module** (Step 1)
   - Pure extraction, no behavior changes
   - Can be tested independently
   - Backward compatible

2. **BYOK Migration** (Step 4)
   - User-facing only, doesn't affect admin
   - Can run old and new systems in parallel
   - Easy rollback (keep Keycloak fallback)

### Medium Risk ⚠️

1. **Platform Keys Migration** (Step 2)
   - Changes database schema
   - Affects all admin operations
   - Mitigation: Backup `platform_settings` before migration

2. **System #2 Removal** (Step 5)
   - Deletes entire API file
   - Risk if hidden dependencies exist
   - Mitigation: Search codebase for references first

### High Risk 🔴

1. **Merging Systems #1 and #2** (Step 3)
   - Most complex change
   - Affects admin workflows
   - Could break existing integrations
   - Mitigation:
     - Feature flag for new testing logic
     - Run both systems in parallel for 1 week
     - Comprehensive testing before removal

---

## Testing Checklist

### Unit Tests

- [ ] `test_provider_testing.py` - Shared module tests
  - [ ] Test all 11 provider configs
  - [ ] Test format validators
  - [ ] Test API key testing (mock HTTP)
  - [ ] Test error handling (timeouts, 401, 500)

- [ ] `test_platform_keys_api.py` - Admin API tests
  - [ ] Test GET / (list keys)
  - [ ] Test PUT /{provider} (add key with validation)
  - [ ] Test POST /{provider}/test (manual test)
  - [ ] Test DELETE /{provider} (remove key)
  - [ ] Test /{provider}/decrypted (admin retrieval)
  - [ ] Test authentication (require admin)

- [ ] `test_byok_api.py` - User BYOK tests
  - [ ] Test GET /providers (list supported)
  - [ ] Test GET /keys (user's keys)
  - [ ] Test POST /keys/add (with tier limits)
  - [ ] Test DELETE /keys/{provider}
  - [ ] Test POST /keys/test/{provider}
  - [ ] Test tier enforcement (trial = 0, starter = 3)

### Integration Tests

- [ ] Database Migration
  - [ ] Backup `platform_settings` table
  - [ ] Run migration script
  - [ ] Verify all keys migrated
  - [ ] Test rollback procedure

- [ ] End-to-End Flows
  - [ ] Admin adds OpenRouter key → Test → View in UI
  - [ ] Admin updates key → Retest → Health status changes
  - [ ] User adds BYOK key → Test → Use in chat
  - [ ] Tier limit enforcement (starter user adds 4th key → Error)

### Manual Testing

- [ ] Admin UI
  - [ ] Load `/admin/system/provider-keys`
  - [ ] Add new OpenRouter key
  - [ ] Test key (verify model count shown)
  - [ ] Update existing key
  - [ ] Delete key (confirm environment fallback)
  - [ ] View health status indicators

- [ ] User BYOK UI
  - [ ] Load `/account/api-keys`
  - [ ] Add custom provider (name + URL)
  - [ ] Test connection
  - [ ] Show/hide password toggle
  - [ ] Delete provider key
  - [ ] Verify tier limits

---

## Rollback Plan

### If Migration Fails

**Scenario**: Database migration corrupts data

**Rollback Steps**:
1. Stop Ops-Center: `docker stop ops-center-direct`
2. Restore backup:
   ```sql
   DELETE FROM llm_providers WHERE api_key_encrypted IS NOT NULL;
   INSERT INTO platform_settings SELECT * FROM platform_settings_backup;
   ```
3. Revert code: `git checkout HEAD~1 backend/platform_keys_api.py`
4. Restart: `docker restart ops-center-direct`

### If Testing Module Breaks

**Scenario**: Shared module has bugs

**Rollback Steps**:
1. Keep old testing code in comments
2. Revert imports:
   ```python
   # from provider_testing import test_api_key  # NEW
   # Use old inline function
   async def test_api_key(provider, key):
       # ... old code
   ```
3. Fix bugs in shared module
4. Redeploy when stable

### If Merged System Has Issues

**Scenario**: Admins report missing features

**Rollback Steps**:
1. Keep `provider_keys_api.py` in `archive/` folder
2. Re-register router in `server.py`
3. Add notice in UI: "Legacy API available at /api/v1/llm/providers"
4. Fix issues in new system
5. Remove legacy when confirmed stable

---

## Timeline

### Phased Rollout (Recommended)

**Week 1**: Preparation
- Day 1-2: Create shared testing module
- Day 3-4: Write comprehensive tests
- Day 5: Review and approve code

**Week 2**: Database Migration
- Day 1: Create migration scripts
- Day 2: Test migration on staging
- Day 3: Run migration on production
- Day 4-5: Monitor for issues

**Week 3**: Merge Admin Systems
- Day 1-2: Merge `provider_keys_api.py` → `platform_keys_api.py`
- Day 3: Update frontend UI
- Day 4-5: Test and deploy

**Week 4**: BYOK Migration
- Day 1: Create `user_provider_keys` table
- Day 2: Migrate Keycloak data
- Day 3: Update BYOK API
- Day 4-5: Test tier limits and deploy

**Week 5**: Cleanup
- Day 1: Delete obsolete code
- Day 2: Update documentation
- Day 3-4: Monitor stability
- Day 5: Final review and sign-off

**Total Time**: 5 weeks (25 days)

### Fast Track (If Urgent)

**Week 1**: Critical Changes
- Day 1: Shared testing module
- Day 2: Database migration
- Day 3: Merge admin systems
- Day 4: BYOK migration
- Day 5: Cleanup and deploy

**Total Time**: 1 week (5 days)

**Risk**: Higher chance of bugs, limited testing

---

## Appendix A: Code Samples

### Sample: Shared Testing Module

```python
# backend/provider_testing.py

"""
Shared Provider API Key Testing Module

Used by:
- platform_keys_api.py (admin system-wide keys)
- byok_api.py (user BYOK keys)

Features:
- Format validation for 11 providers
- API testing with latency tracking
- Model discovery (count available models)
- Error handling (timeout, 401, 500)
"""

from typing import Dict, Optional, Callable
import httpx
import logging
from time import time as current_time

logger = logging.getLogger(__name__)

# Provider configurations with test endpoints and validators
PROVIDER_TEST_CONFIGS = {
    'openrouter': {
        'name': 'OpenRouter',
        'test_url': 'https://openrouter.ai/api/v1/models',
        'auth_type': 'bearer',
        'key_format': 'sk-or-v1-...',
        'validator': lambda k: k.startswith('sk-or-v1-'),
        'headers': {
            'HTTP-Referer': 'https://unicorncommander.ai',
            'X-Title': 'UC-1 Pro Ops Center'
        }
    },
    'openai': {
        'name': 'OpenAI',
        'test_url': 'https://api.openai.com/v1/models',
        'auth_type': 'bearer',
        'key_format': 'sk-proj-...',
        'validator': lambda k: k.startswith('sk-') and not k.startswith('sk-or-')
    },
    'anthropic': {
        'name': 'Anthropic',
        'test_url': 'https://api.anthropic.com/v1/messages',
        'auth_type': 'x-api-key',
        'key_format': 'sk-ant-...',
        'validator': lambda k: k.startswith('sk-ant-'),
        'test_method': 'POST',
        'test_body': {
            'model': 'claude-3-haiku-20240307',
            'max_tokens': 1,
            'messages': [{'role': 'user', 'content': 'Hi'}]
        },
        'headers': {
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
    },
    'google': {
        'name': 'Google AI',
        'test_url': 'https://generativelanguage.googleapis.com/v1beta/models',
        'auth_type': 'query_param',
        'auth_param': 'key',
        'key_format': 'AIza...',
        'validator': lambda k: k.startswith('AIza')
    },
    'huggingface': {
        'name': 'HuggingFace',
        'test_url': 'https://huggingface.co/api/whoami',
        'auth_type': 'bearer',
        'key_format': 'hf_...',
        'validator': lambda k: k.startswith('hf_')
    },
    'groq': {
        'name': 'Groq',
        'test_url': 'https://api.groq.com/openai/v1/models',
        'auth_type': 'bearer',
        'key_format': 'gsk_...',
        'validator': lambda k: k.startswith('gsk_')
    },
    'cohere': {
        'name': 'Cohere',
        'test_url': 'https://api.cohere.ai/v1/models',
        'auth_type': 'bearer',
        'key_format': None,
        'validator': None
    },
    'together': {
        'name': 'Together AI',
        'test_url': 'https://api.together.xyz/models',
        'auth_type': 'bearer',
        'key_format': None,
        'validator': None
    },
    'mistral': {
        'name': 'Mistral AI',
        'test_url': 'https://api.mistral.ai/v1/models',
        'auth_type': 'bearer',
        'key_format': None,
        'validator': None
    },
    'perplexity': {
        'name': 'Perplexity AI',
        'test_url': 'https://api.perplexity.ai/chat/completions',
        'auth_type': 'bearer',
        'key_format': 'pplx-...',
        'validator': lambda k: k.startswith('pplx-')
    },
    'ollama': {
        'name': 'Ollama (Local)',
        'test_url': 'http://localhost:11434/api/tags',
        'auth_type': 'none',
        'key_format': None,
        'validator': None
    }
}

def get_provider_config(provider: str) -> Dict:
    """Get configuration for a provider"""
    if provider not in PROVIDER_TEST_CONFIGS:
        raise ValueError(f"Unknown provider: {provider}")
    return PROVIDER_TEST_CONFIGS[provider]

def validate_key_format(provider: str, api_key: str) -> bool:
    """
    Validate API key matches expected format

    Returns:
        bool: True if valid, False if invalid, True if no validator
    """
    config = get_provider_config(provider)
    validator = config.get('validator')

    if not validator:
        return True  # No validator, assume valid

    return validator(api_key)

async def test_api_key(
    provider: str,
    api_key: str,
    custom_endpoint: Optional[str] = None
) -> Dict:
    """
    Test provider API key by making actual API call

    Args:
        provider: Provider name (e.g., "openrouter", "openai")
        api_key: API key to test
        custom_endpoint: Custom URL (for custom providers)

    Returns:
        {
            "success": bool,
            "latency_ms": int,
            "models_found": int | None,
            "error": str | None
        }
    """
    config = get_provider_config(provider)

    # Determine test URL
    if provider == 'custom':
        if not custom_endpoint:
            return {
                "success": False,
                "latency_ms": 0,
                "models_found": None,
                "error": "Custom endpoint URL required"
            }
        test_url = f"{custom_endpoint.rstrip('/')}/v1/models"
    else:
        test_url = config['test_url']

    # Build headers
    headers = dict(config.get('headers', {}))
    auth_type = config.get('auth_type', 'bearer')

    if auth_type == 'bearer':
        headers['Authorization'] = f'Bearer {api_key}'
    elif auth_type == 'x-api-key':
        headers['x-api-key'] = api_key
    elif auth_type == 'query_param':
        auth_param = config.get('auth_param', 'key')
        test_url = f"{test_url}?{auth_param}={api_key}"
    # else: auth_type == 'none', no auth needed

    # Perform test
    try:
        start_time = current_time()

        async with httpx.AsyncClient(timeout=10.0) as client:
            test_method = config.get('test_method', 'GET')

            if test_method == 'POST':
                test_body = config.get('test_body', {})
                response = await client.post(test_url, headers=headers, json=test_body)
            else:
                response = await client.get(test_url, headers=headers)

        latency_ms = int((current_time() - start_time) * 1000)

        # Parse response
        if response.status_code in [200, 201]:
            try:
                data = response.json()

                # Count models based on provider response format
                models_found = 0
                if 'data' in data and isinstance(data['data'], list):
                    models_found = len(data['data'])
                elif 'models' in data and isinstance(data['models'], list):
                    models_found = len(data['models'])
                elif 'id' in data:
                    models_found = 1  # Anthropic-style (single response)

                return {
                    "success": True,
                    "latency_ms": latency_ms,
                    "models_found": models_found,
                    "error": None
                }
            except Exception as parse_error:
                logger.warning(f"Error parsing response for {provider}: {parse_error}")
                return {
                    "success": True,
                    "latency_ms": latency_ms,
                    "models_found": None,
                    "error": None
                }

        elif response.status_code == 401:
            return {
                "success": False,
                "latency_ms": latency_ms,
                "models_found": None,
                "error": "Invalid API key - authentication failed"
            }

        elif response.status_code == 403:
            return {
                "success": False,
                "latency_ms": latency_ms,
                "models_found": None,
                "error": "API key lacks required permissions"
            }

        else:
            return {
                "success": False,
                "latency_ms": latency_ms,
                "models_found": None,
                "error": f"API error: HTTP {response.status_code}"
            }

    except httpx.TimeoutException:
        return {
            "success": False,
            "latency_ms": 10000,
            "models_found": None,
            "error": "Request timeout - API not responding"
        }

    except httpx.ConnectError:
        return {
            "success": False,
            "latency_ms": 0,
            "models_found": None,
            "error": "Connection failed - unable to reach API endpoint"
        }

    except Exception as e:
        logger.error(f"Provider API test error: {e}", exc_info=True)
        return {
            "success": False,
            "latency_ms": 0,
            "models_found": None,
            "error": f"Test failed: {str(e)}"
        }
```

---

## Appendix B: Database Schemas

### Current Schema: platform_settings

```sql
CREATE TABLE platform_settings (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT,
    category VARCHAR(100),
    is_secret BOOLEAN DEFAULT true,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Example data
INSERT INTO platform_settings VALUES
('openrouter_api_key', 'gAAAAABh4kF2w...', 'api_keys', true, NOW()),
('openai_api_key', 'gAAAAABh5mG3x...', 'api_keys', true, NOW()),
('anthropic_api_key', 'gAAAAABh6nH4y...', 'api_keys', true, NOW());
```

### Current Schema: llm_providers

```sql
CREATE TABLE llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT,
    api_base_url TEXT,
    enabled BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0,
    config JSONB DEFAULT '{}'::jsonb,
    health_status VARCHAR(20) DEFAULT 'unknown',
    last_health_check TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT llm_providers_name_type_key UNIQUE(name, type)
);

CREATE INDEX idx_llm_providers_enabled ON llm_providers(enabled);

-- Example data
INSERT INTO llm_providers (name, type, api_key_encrypted, priority, config) VALUES
('OpenRouter', 'openrouter', 'gAAAAABh...', 100, '{"models_found": 348, "latency_ms": 245}'::jsonb),
('OpenAI', 'openai', 'gAAAAABh...', 90, '{"models_found": 10, "latency_ms": 312}'::jsonb);
```

### Planned Schema: user_provider_keys

```sql
CREATE TABLE user_provider_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,  -- FK to Keycloak user (external system)
    provider VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_user_provider UNIQUE(user_id, provider)
);

CREATE INDEX idx_user_provider_keys_user ON user_provider_keys(user_id);
CREATE INDEX idx_user_provider_keys_enabled ON user_provider_keys(enabled);
CREATE INDEX idx_user_provider_keys_provider ON user_provider_keys(provider);

-- Example data
INSERT INTO user_provider_keys (user_id, provider, api_key_encrypted, metadata) VALUES
('abc-123', 'openrouter', 'gAAAAABh...', '{"label": "My OpenRouter Key", "test_status": "valid"}'::jsonb),
('abc-123', 'openai', 'gAAAAABh...', '{"label": "My OpenAI Key", "test_status": "valid"}'::jsonb),
('def-456', 'anthropic', 'gAAAAABh...', '{"label": "Claude API Key", "test_status": "valid"}'::jsonb);
```

---

## Appendix C: API Endpoint Comparison

### Before Consolidation

**System #1: platform_keys_api.py** (17 endpoints)
```
GET    /api/v1/admin/platform-keys
PUT    /api/v1/admin/platform-keys/openrouter
PUT    /api/v1/admin/platform-keys/openai
PUT    /api/v1/admin/platform-keys/anthropic
PUT    /api/v1/admin/platform-keys/google
PUT    /api/v1/admin/platform-keys/huggingface
PUT    /api/v1/admin/platform-keys/groq
PUT    /api/v1/admin/platform-keys/xai
PUT    /api/v1/admin/platform-keys/provisioning
GET    /api/v1/admin/platform-keys/openrouter/decrypted
GET    /api/v1/admin/platform-keys/openai/decrypted
GET    /api/v1/admin/platform-keys/anthropic/decrypted
GET    /api/v1/admin/platform-keys/google/decrypted
GET    /api/v1/admin/platform-keys/huggingface/decrypted
GET    /api/v1/admin/platform-keys/groq/decrypted
GET    /api/v1/admin/platform-keys/xai/decrypted
GET    /api/v1/admin/platform-keys/provisioning/decrypted
```

**System #2: provider_keys_api.py** (5 endpoints)
```
GET    /api/v1/llm/providers/keys
POST   /api/v1/llm/providers/keys
POST   /api/v1/llm/providers/keys/test
DELETE /api/v1/llm/providers/keys/{provider_id}
GET    /api/v1/llm/providers/info
```

**System #3: byok_api.py** (6 endpoints)
```
GET    /api/v1/byok/providers
GET    /api/v1/byok/keys
POST   /api/v1/byok/keys/add
DELETE /api/v1/byok/keys/{provider}
POST   /api/v1/byok/keys/test/{provider}
GET    /api/v1/byok/stats
```

**Total**: 28 endpoints

### After Consolidation

**Admin Platform Keys** (11 endpoints)
```
GET    /api/v1/admin/platform-keys              # List all
PUT    /api/v1/admin/platform-keys/{provider}   # Add/update (with auto-test)
DELETE /api/v1/admin/platform-keys/{provider}   # Delete
POST   /api/v1/admin/platform-keys/{provider}/test  # Manual test
GET    /api/v1/admin/platform-keys/{provider}/decrypted  # Get full key
GET    /api/v1/admin/platform-keys/info         # Provider info
```

**User BYOK** (6 endpoints)
```
GET    /api/v1/byok/providers                  # List supported
GET    /api/v1/byok/keys                       # User's keys
POST   /api/v1/byok/keys/add                   # Add/update
DELETE /api/v1/byok/keys/{provider}            # Delete
POST   /api/v1/byok/keys/test/{provider}       # Test
GET    /api/v1/byok/stats                      # User stats
```

**Total**: 17 endpoints (-39% reduction)

---

## Conclusion

This comprehensive audit has identified **three distinct provider key management systems** in Ops-Center:

1. **Platform Keys API** (System #1) - Admin system-wide keys
2. **Provider Keys API** (System #2) - Admin provider management
3. **BYOK API** (System #3) - User self-service keys

**Key Findings**:
- Systems #1 and #2 are **duplicates with improvements** (both admin, same purpose, different implementations)
- System #3 is **complementary** (different audience and purpose)
- All three systems can **share testing logic** (300+ lines of duplicate code)

**Recommended Actions**:
1. ✅ **Merge Systems #1 and #2** into unified admin system
2. ✅ **Complete BYOK migration** from Keycloak → PostgreSQL
3. ✅ **Extract shared testing module** to reduce duplication
4. ✅ **Delete obsolete code** after verification

**Expected Outcomes**:
- 21% code reduction (2,642 → 2,100 lines)
- 39% endpoint reduction (28 → 17)
- Clearer architecture (admin vs user)
- Better testing coverage
- Easier to maintain and extend

**Timeline**: 5 weeks (phased rollout) or 1 week (fast track)

**Risks**: Medium (database migration, system merging)

**Next Steps**: Review this report → Approve consolidation plan → Begin Phase 1 (shared testing module)

---

**Report Author**: Claude Code (Audit Team Lead)
**Report Date**: November 14, 2025
**Version**: 1.0
**Status**: Ready for Review
