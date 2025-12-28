# Database Schema Documentation

**Project**: UC-Cloud Ops-Center
**Database**: unicorn_db (PostgreSQL 16)
**Last Updated**: October 27, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [LLM Infrastructure Tables](#llm-infrastructure-tables)
3. [System API Key Management](#system-api-key-management)
4. [User BYOK Tables](#user-byok-tables)
5. [Encryption Strategy](#encryption-strategy)
6. [Key Rotation](#key-rotation)
7. [Migration History](#migration-history)

---

## Overview

The Ops-Center database manages:
- LLM provider configurations (OpenAI, Anthropic, Google, etc.)
- LLM model definitions with pricing and capabilities
- User BYOK (Bring Your Own Key) storage
- System API keys (admin-configured shared keys)
- LLM routing rules for power levels
- Usage tracking and billing integration

All sensitive data (API keys) is encrypted using **Fernet symmetric encryption** with the `BYOK_ENCRYPTION_KEY` environment variable.

---

## LLM Infrastructure Tables

### 1. `llm_providers`

Stores LLM provider configurations and system API keys.

**Purpose**: Define available LLM providers (OpenAI, Anthropic, etc.) with their API endpoints, capabilities, and optional system-level API keys.

#### Schema

```sql
CREATE TABLE llm_providers (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Provider Identity
    provider_name VARCHAR(100) UNIQUE NOT NULL,
    provider_slug VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- API Configuration
    base_url VARCHAR(500),
    auth_type VARCHAR(50) DEFAULT 'api_key' NOT NULL,
    supports_streaming BOOLEAN DEFAULT TRUE,
    supports_function_calling BOOLEAN DEFAULT FALSE,
    supports_vision BOOLEAN DEFAULT FALSE,

    -- Rate Limits
    rate_limit_rpm INTEGER,
    rate_limit_tpm INTEGER,
    rate_limit_rpd INTEGER,

    -- Provider Status
    is_active BOOLEAN DEFAULT TRUE,
    is_byok_supported BOOLEAN DEFAULT TRUE,
    is_system_provider BOOLEAN DEFAULT FALSE,

    -- System API Key Storage (Added in Migration 002)
    encrypted_api_key TEXT NULL,
    api_key_source VARCHAR(50) DEFAULT 'environment',
    api_key_updated_at TIMESTAMP NULL,
    api_key_last_tested TIMESTAMP NULL,
    api_key_test_status VARCHAR(20) NULL,

    -- Metadata
    api_key_format VARCHAR(100),
    documentation_url VARCHAR(500),
    pricing_url VARCHAR(500),
    status_page_url VARCHAR(500),

    -- Health Monitoring
    health_status VARCHAR(50) DEFAULT 'unknown',
    health_last_checked TIMESTAMP,
    health_response_time_ms INTEGER,

    -- Access Control
    min_tier_required VARCHAR(50) DEFAULT 'free',

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

#### Indexes

```sql
CREATE INDEX idx_llm_providers_active ON llm_providers(is_active);
CREATE INDEX idx_llm_providers_slug ON llm_providers(provider_slug);
CREATE INDEX idx_llm_providers_health ON llm_providers(health_status, is_active);
CREATE INDEX idx_llm_providers_api_key_source ON llm_providers(api_key_source) WHERE is_active = TRUE;
CREATE INDEX idx_llm_providers_has_db_key ON llm_providers(id) WHERE encrypted_api_key IS NOT NULL;
```

#### Key Columns

| Column | Type | Description |
|--------|------|-------------|
| `encrypted_api_key` | TEXT | Fernet-encrypted system API key (NULL if not configured) |
| `api_key_source` | VARCHAR(50) | Source priority: `environment`, `database`, or `hybrid` |
| `api_key_updated_at` | TIMESTAMP | When system key was last updated |
| `api_key_last_tested` | TIMESTAMP | When key was last successfully validated |
| `api_key_test_status` | VARCHAR(20) | Test result: `valid`, `invalid`, `untested`, `error` |

#### API Key Source Priority

The `api_key_source` column determines where the system retrieves API keys:

1. **`environment`** - Only use environment variable (default for backward compatibility)
   - Looks for: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
   - Falls back to: `OPENROUTER_API_KEY` (default)
   - Database key is ignored

2. **`database`** - Only use encrypted_api_key from database
   - Requires: `encrypted_api_key IS NOT NULL`
   - Environment variables are ignored
   - Fails if database key is missing

3. **`hybrid`** - Database first, environment fallback (recommended)
   - Prefers: `encrypted_api_key` if present
   - Falls back to: Environment variable
   - Most flexible option

**Example**:
```python
# In litellm_api.py
def get_provider_api_key(provider_slug: str) -> str:
    provider = db.query(llm_providers).filter_by(provider_slug=provider_slug).first()

    if provider.api_key_source == 'database':
        return decrypt_api_key(provider.encrypted_api_key)

    elif provider.api_key_source == 'environment':
        return os.getenv(f'{provider_slug.upper()}_API_KEY')

    elif provider.api_key_source == 'hybrid':
        if provider.encrypted_api_key:
            return decrypt_api_key(provider.encrypted_api_key)
        return os.getenv(f'{provider_slug.upper()}_API_KEY')
```

---

### 2. `llm_models`

Stores individual LLM model definitions with pricing and capabilities.

**Purpose**: Define available models for each provider with pricing, context limits, and power level mappings.

#### Schema

```sql
CREATE TABLE llm_models (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES llm_providers(id) ON DELETE CASCADE NOT NULL,

    -- Model Identity
    model_name VARCHAR(200) NOT NULL,
    model_id VARCHAR(200) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Capabilities
    max_tokens INTEGER DEFAULT 4096 NOT NULL,
    context_window INTEGER DEFAULT 8192 NOT NULL,
    supports_streaming BOOLEAN DEFAULT TRUE,
    supports_function_calling BOOLEAN DEFAULT FALSE,
    supports_vision BOOLEAN DEFAULT FALSE,
    supports_json_mode BOOLEAN DEFAULT FALSE,

    -- Pricing (per 1M tokens in USD)
    cost_per_1m_input_tokens DECIMAL(10, 6),
    cost_per_1m_output_tokens DECIMAL(10, 6),
    cost_per_1m_tokens_cached DECIMAL(10, 6),

    -- Power Level Mapping
    power_level VARCHAR(50),
    power_level_priority INTEGER DEFAULT 999,

    -- Model Status
    is_active BOOLEAN DEFAULT TRUE,
    is_deprecated BOOLEAN DEFAULT FALSE,
    deprecation_date TIMESTAMP,
    replacement_model_id INTEGER REFERENCES llm_models(id),

    -- Access Control
    min_tier_required VARCHAR(50) DEFAULT 'free',

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    UNIQUE(provider_id, model_id)
);
```

---

### 3. `user_api_keys` (BYOK)

Stores user-provided API keys (Bring Your Own Key).

**Purpose**: Allow users to use their own API keys for LLM providers instead of system keys.

#### Schema

```sql
CREATE TABLE user_api_keys (
    id SERIAL PRIMARY KEY,

    -- Foreign Keys
    user_id VARCHAR(255) NOT NULL,  -- Keycloak user ID
    provider_id INTEGER REFERENCES llm_providers(id) ON DELETE CASCADE NOT NULL,

    -- Key Details
    key_name VARCHAR(200),
    encrypted_api_key TEXT NOT NULL,
    key_prefix VARCHAR(20),
    key_suffix VARCHAR(20),

    -- Key Status
    is_active BOOLEAN DEFAULT TRUE,
    is_validated BOOLEAN DEFAULT FALSE,
    validation_error TEXT,
    last_validated_at TIMESTAMP,

    -- Usage Statistics
    total_requests INTEGER DEFAULT 0,
    total_tokens BIGINT DEFAULT 0,
    total_cost_usd DECIMAL(10, 6) DEFAULT 0.0,
    last_used_at TIMESTAMP,

    -- Security
    created_ip VARCHAR(100),
    last_rotated_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    UNIQUE(user_id, provider_id)
);
```

#### Key Differences: System Keys vs BYOK

| Feature | System Keys (`llm_providers`) | User Keys (`user_api_keys`) |
|---------|-------------------------------|------------------------------|
| **Scope** | Shared across all users | Per-user |
| **Management** | Admin-only | User self-service |
| **Billing** | Charged to organization | User's own account |
| **Storage** | `llm_providers.encrypted_api_key` | `user_api_keys.encrypted_api_key` |
| **Priority** | Lower (fallback) | Higher (preferred if available) |

**Routing Logic**:
```python
# Priority order:
# 1. User's BYOK (user_api_keys) - if configured
# 2. System key from database (llm_providers.encrypted_api_key) - if configured
# 3. System key from environment (env vars) - default fallback
```

---

## System API Key Management

### Encryption Method

**Algorithm**: Fernet (symmetric encryption)
**Library**: `cryptography.fernet`
**Key Source**: `BYOK_ENCRYPTION_KEY` environment variable

#### Encryption Process

```python
from cryptography.fernet import Fernet

# 1. Generate encryption key (one-time setup)
encryption_key = Fernet.generate_key()
# Save to .env: BYOK_ENCRYPTION_KEY=<base64-encoded-key>

# 2. Initialize cipher
cipher = Fernet(os.getenv('BYOK_ENCRYPTION_KEY'))

# 3. Encrypt API key
plaintext_key = "sk-ant-api03-AbCdEf1234..."
encrypted_key = cipher.encrypt(plaintext_key.encode()).decode()

# 4. Store in database
db.execute("""
    UPDATE llm_providers
    SET encrypted_api_key = %s,
        api_key_source = 'database',
        api_key_updated_at = NOW()
    WHERE provider_slug = 'anthropic'
""", [encrypted_key])

# 5. Decrypt when needed
decrypted_key = cipher.decrypt(encrypted_key.encode()).decode()
```

#### Security Features

1. **Encryption at Rest**: All keys encrypted in database
2. **Key Masking**: Only show first 8 and last 4 characters in UI
3. **Audit Logging**: Track all key creation/updates/deletions
4. **IP Tracking**: Record IP address of key creator
5. **Validation**: Test keys before saving
6. **Rotation**: Support for key rotation with history

### Key Validation

Before storing a system API key, validate it:

```python
async def validate_api_key(provider_slug: str, api_key: str) -> dict:
    """
    Test API key by making a minimal API call

    Returns:
        {
            'is_valid': bool,
            'error': str or None,
            'response_time_ms': int,
            'tested_at': datetime
        }
    """
    if provider_slug == 'openai':
        # Test with /v1/models endpoint
        response = await httpx.get(
            'https://api.openai.com/v1/models',
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=10.0
        )
        return {
            'is_valid': response.status_code == 200,
            'error': None if response.status_code == 200 else response.text,
            'response_time_ms': int(response.elapsed.total_seconds() * 1000),
            'tested_at': datetime.now()
        }
```

---

## Key Rotation

### Rotation Strategy

1. **Automatic Expiration**: Keys older than 90 days trigger rotation warning
2. **Manual Rotation**: Admin can force rotation at any time
3. **Gradual Rollout**: New key tested before old key disabled
4. **Audit Trail**: All rotations logged with reason and timestamp

### Rotation Process

```sql
-- Step 1: Admin sets new key
UPDATE llm_providers
SET encrypted_api_key = '<new-encrypted-key>',
    api_key_updated_at = NOW(),
    api_key_test_status = 'untested'
WHERE provider_slug = 'openai';

-- Step 2: Validate new key
-- (Run validation via API endpoint)

-- Step 3: Mark as valid
UPDATE llm_providers
SET api_key_test_status = 'valid',
    api_key_last_tested = NOW()
WHERE provider_slug = 'openai';

-- Step 4: Log rotation in audit_logs
INSERT INTO audit_logs (
    user_id, action, resource_type, resource_id,
    changes, ip_address, created_at
) VALUES (
    '<admin-user-id>',
    'rotate_system_api_key',
    'llm_provider',
    '<provider-id>',
    '{"provider": "openai", "reason": "scheduled_rotation"}',
    '<admin-ip>',
    NOW()
);
```

### Rotation Monitoring

Query to find keys needing rotation:

```sql
SELECT
    provider_slug,
    provider_name,
    api_key_updated_at,
    EXTRACT(DAY FROM NOW() - api_key_updated_at) as days_old,
    api_key_test_status
FROM llm_providers
WHERE encrypted_api_key IS NOT NULL
AND api_key_updated_at < NOW() - INTERVAL '90 days'
ORDER BY api_key_updated_at ASC;
```

---

## Migration History

### Migration 001: Initial LLM Tables

**File**: `001_create_llm_tables.sql`
**Applied**: October 23, 2025
**Changes**:
- Created `llm_providers` table (without system key columns)
- Created `llm_models` table
- Created `user_api_keys` table
- Created `llm_routing_rules` table
- Created `llm_usage_logs` table
- Seeded initial providers (OpenAI, Anthropic, Google, OpenRouter, etc.)

### Migration 002: System API Key Storage

**File**: `002_add_system_api_keys.sql`
**Applied**: October 27, 2025
**Changes**:
- Added `encrypted_api_key` column to `llm_providers`
- Added `api_key_source` column (environment/database/hybrid)
- Added `api_key_updated_at` column
- Added `api_key_last_tested` column
- Added `api_key_test_status` column
- Created indexes for performance
- Added column documentation comments

**Rollback**: `002_add_system_api_keys_rollback.sql`

---

## Common Queries

### Get All Active Providers with System Keys

```sql
SELECT
    provider_slug,
    display_name,
    base_url,
    api_key_source,
    CASE
        WHEN encrypted_api_key IS NOT NULL THEN 'Configured'
        ELSE 'Not Configured'
    END as system_key_status,
    api_key_test_status,
    api_key_last_tested
FROM llm_providers
WHERE is_active = TRUE
ORDER BY provider_name;
```

### Get User's BYOK Keys

```sql
SELECT
    p.provider_slug,
    p.display_name,
    k.key_name,
    k.key_prefix,
    k.key_suffix,
    k.is_validated,
    k.last_validated_at,
    k.total_requests,
    k.last_used_at
FROM user_api_keys k
JOIN llm_providers p ON k.provider_id = p.id
WHERE k.user_id = '<keycloak-user-id>'
AND k.is_active = TRUE;
```

### Get Provider Key Priority

```sql
SELECT
    provider_slug,
    api_key_source,
    CASE
        WHEN api_key_source = 'database' AND encrypted_api_key IS NOT NULL THEN 'Database Only'
        WHEN api_key_source = 'environment' THEN 'Environment Only'
        WHEN api_key_source = 'hybrid' AND encrypted_api_key IS NOT NULL THEN 'Database (with env fallback)'
        WHEN api_key_source = 'hybrid' AND encrypted_api_key IS NULL THEN 'Environment (no database key)'
        ELSE 'Unconfigured'
    END as key_priority
FROM llm_providers
WHERE is_active = TRUE;
```

---

## Security Best Practices

### 1. Environment Variables

**DO**:
- Store `BYOK_ENCRYPTION_KEY` in `.env.auth` (never commit to git)
- Use different encryption keys for dev/staging/production
- Rotate encryption key annually

**DON'T**:
- Store plaintext API keys in database
- Log decrypted API keys
- Share encryption keys between environments

### 2. Database Access

**DO**:
- Use read-only database users for reporting queries
- Limit `UPDATE` access to `encrypted_api_key` column
- Enable PostgreSQL audit logging for sensitive tables

**DON'T**:
- Query `encrypted_api_key` column in frontend code
- Expose decrypted keys in API responses
- Allow users to read other users' BYOK keys

### 3. Key Management

**DO**:
- Validate keys before storing
- Test keys periodically (health checks)
- Rotate keys on schedule
- Log all key operations in `audit_logs`

**DON'T**:
- Store expired keys
- Reuse old encryption keys after rotation
- Skip validation to save time

---

## Appendix: Example Data

### Sample Provider Row

```sql
INSERT INTO llm_providers (
    provider_name, provider_slug, display_name, description,
    base_url, auth_type, supports_streaming,
    encrypted_api_key, api_key_source, api_key_updated_at,
    api_key_test_status, is_active
) VALUES (
    'OpenAI', 'openai', 'OpenAI', 'GPT-4 and GPT-3.5 models',
    'https://api.openai.com/v1', 'api_key', TRUE,
    'gAAAAABmF...encrypted-key...zYw==',  -- Fernet encrypted
    'hybrid',  -- Prefer database, fall back to environment
    NOW(),
    'valid',  -- Last test passed
    TRUE
);
```

### Sample User BYOK Row

```sql
INSERT INTO user_api_keys (
    user_id, provider_id, key_name,
    encrypted_api_key, key_prefix, key_suffix,
    is_active, is_validated, last_validated_at,
    created_ip
) VALUES (
    '123e4567-e89b-12d3-a456-426614174000',  -- Keycloak user ID
    1,  -- OpenAI provider
    'My OpenAI Key',
    'gAAAAABmF...encrypted-user-key...abc==',
    'sk-proj-',
    '...xyz9',
    TRUE,
    TRUE,
    NOW(),
    '192.168.1.100'
);
```

---

## References

- **Fernet Encryption**: https://cryptography.io/en/latest/fernet/
- **PostgreSQL Triggers**: https://www.postgresql.org/docs/current/triggers.html
- **LiteLLM Documentation**: https://docs.litellm.ai/
- **UC-Cloud Main Docs**: `/home/muut/Production/UC-Cloud/CLAUDE.md`

---

**Last Updated**: October 27, 2025
**Maintained By**: Backend API Developer Team
**Review Schedule**: Monthly
