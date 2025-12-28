# Platform Keys API - Multi-Provider LLM Key Management

**Version**: 2.0
**Date**: November 14, 2025
**Status**: Production Ready

---

## Overview

The Platform Keys API provides centralized management for LLM provider API keys across the UC-Cloud ecosystem. All keys are stored encrypted in the `platform_settings` database table using Fernet symmetric encryption.

**Key Features**:
- ✅ Support for 7 major LLM providers
- ✅ Encrypted storage with Fernet encryption
- ✅ Format validation for each provider
- ✅ Admin-only access control
- ✅ Environment variable fallback
- ✅ Masked preview display
- ✅ Audit logging

---

## Supported Providers

### 1. OpenRouter (✅ Configured)
**Provider**: OpenRouter
**Key Format**: `sk-or-v1-...`
**Database Key**: `openrouter_api_key`
**Environment Variable**: `OPENROUTER_API_KEY`
**Description**: OpenRouter API key for LLM inference routing (348+ models)
**Models**: All major LLMs (OpenAI, Anthropic, Google, Meta, Mistral, etc.)

**Endpoints**:
```bash
PUT  /api/v1/admin/platform-keys/openrouter      # Update key
GET  /api/v1/admin/platform-keys/openrouter/decrypted  # Retrieve key
```

---

### 2. OpenAI
**Provider**: OpenAI
**Key Format**: `sk-proj-...` (or `sk-...`)
**Database Key**: `openai_api_key`
**Environment Variable**: `OPENAI_API_KEY`
**Description**: OpenAI API key for GPT-4, GPT-3.5, and DALL-E models
**Models**: GPT-4 Turbo, GPT-4, GPT-3.5-turbo, DALL-E 3, DALL-E 2

**Endpoints**:
```bash
PUT  /api/v1/admin/platform-keys/openai      # Update key
GET  /api/v1/admin/platform-keys/openai/decrypted  # Retrieve key
```

**Example**:
```bash
curl -X PUT http://localhost:8084/api/v1/admin/platform-keys/openai \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_SESSION" \
  -d '{"api_key": "sk-proj-AbCd1234EfGh5678..."}'
```

---

### 3. Anthropic
**Provider**: Anthropic
**Key Format**: `sk-ant-...`
**Database Key**: `anthropic_api_key`
**Environment Variable**: `ANTHROPIC_API_KEY`
**Description**: Anthropic API key for Claude models (Opus, Sonnet, Haiku)
**Models**: Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku

**Endpoints**:
```bash
PUT  /api/v1/admin/platform-keys/anthropic      # Update key
GET  /api/v1/admin/platform-keys/anthropic/decrypted  # Retrieve key
```

**Example**:
```bash
curl -X PUT http://localhost:8084/api/v1/admin/platform-keys/anthropic \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_SESSION" \
  -d '{"api_key": "sk-ant-api03-AbCd1234..."}'
```

---

### 4. HuggingFace
**Provider**: HuggingFace
**Key Format**: `hf_...`
**Database Key**: `huggingface_api_key`
**Environment Variable**: `HUGGINGFACE_API_KEY`
**Description**: HuggingFace API key for inference API and model downloads
**Models**: 100,000+ models on HuggingFace Hub

**Endpoints**:
```bash
PUT  /api/v1/admin/platform-keys/huggingface      # Update key
GET  /api/v1/admin/platform-keys/huggingface/decrypted  # Retrieve key
```

**Example**:
```bash
curl -X PUT http://localhost:8084/api/v1/admin/platform-keys/huggingface \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_SESSION" \
  -d '{"api_key": "hf_AbCdEfGh1234..."}'
```

---

### 5. Groq
**Provider**: Groq
**Key Format**: `gsk_...`
**Database Key**: `groq_api_key`
**Environment Variable**: `GROQ_API_KEY`
**Description**: Groq API key for ultra-fast LLM inference
**Models**: Llama 3, Mixtral, Gemma (all with ultra-low latency)

**Endpoints**:
```bash
PUT  /api/v1/admin/platform-keys/groq      # Update key
GET  /api/v1/admin/platform-keys/groq/decrypted  # Retrieve key
```

**Example**:
```bash
curl -X PUT http://localhost:8084/api/v1/admin/platform-keys/groq \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_SESSION" \
  -d '{"api_key": "gsk_AbCd1234EfGh..."}'
```

---

### 6. X.AI Grok
**Provider**: X.AI
**Key Format**: `xai-...`
**Database Key**: `xai_api_key`
**Environment Variable**: `XAI_API_KEY`
**Description**: X.AI API key for Grok models
**Models**: Grok-1, Grok-1.5

**Endpoints**:
```bash
PUT  /api/v1/admin/platform-keys/xai      # Update key
GET  /api/v1/admin/platform-keys/xai/decrypted  # Retrieve key
```

**Example**:
```bash
curl -X PUT http://localhost:8084/api/v1/admin/platform-keys/xai \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_SESSION" \
  -d '{"api_key": "xai-AbCd1234EfGh..."}'
```

---

### 7. Google AI
**Provider**: Google
**Key Format**: `AIza...`
**Database Key**: `google_ai_api_key`
**Environment Variable**: `GOOGLE_AI_API_KEY`
**Description**: Google AI API key for Gemini models
**Models**: Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini Pro

**Endpoints**:
```bash
PUT  /api/v1/admin/platform-keys/google      # Update key
GET  /api/v1/admin/platform-keys/google/decrypted  # Retrieve key
```

**Example**:
```bash
curl -X PUT http://localhost:8084/api/v1/admin/platform-keys/google \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_SESSION" \
  -d '{"api_key": "AIzaSyAbCd1234EfGh..."}'
```

---

## API Endpoints Summary

### List All Platform Keys
```
GET /api/v1/admin/platform-keys
```

**Response**:
```json
{
  "keys": [
    {
      "key_name": "OpenRouter API Key",
      "description": "OpenRouter API key for LLM inference routing (348+ models)",
      "has_key": true,
      "key_preview": "sk-or-v...ab12",
      "last_updated": "2025-11-14T22:28:05.702296",
      "source": "database"
    },
    {
      "key_name": "OpenAI API Key",
      "description": "OpenAI API key for GPT-4, GPT-3.5, and DALL-E models",
      "has_key": false,
      "key_preview": null,
      "last_updated": null,
      "source": "not_set"
    }
    // ... 7 more providers
  ],
  "total": 9
}
```

---

### Update Provider Key (PUT)
```
PUT /api/v1/admin/platform-keys/{provider}
```

**Providers**: `openrouter`, `openai`, `anthropic`, `huggingface`, `groq`, `xai`, `google`

**Request Body**:
```json
{
  "api_key": "your-api-key-here"
}
```

**Response** (Success):
```json
{
  "success": true,
  "message": "OpenAI API key updated successfully",
  "key_preview": "sk-proj...ab12"
}
```

**Response** (Validation Error):
```json
{
  "detail": "Invalid OpenAI API key format. Expected format: sk-proj-..."
}
```

---

### Get Decrypted Key (GET)
```
GET /api/v1/admin/platform-keys/{provider}/decrypted
```

**⚠️ WARNING**: This endpoint exposes the full API key. Use with extreme caution.

**Providers**: `openrouter`, `openai`, `anthropic`, `huggingface`, `groq`, `xai`, `google`

**Response**:
```json
{
  "api_key": "sk-proj-AbCd1234EfGh5678...",
  "source": "database",
  "warning": "This is the full API key. Keep it secure."
}
```

**Response** (Not Configured):
```json
{
  "detail": "OpenAI API key not configured"
}
```

---

## Key Validation Rules

Each provider has specific key format validation:

| Provider | Format | Regex Pattern | Example |
|----------|--------|---------------|---------|
| OpenRouter | `sk-or-*` | `^sk-or-` | `sk-or-v1-abc123...` |
| OpenAI | `sk-*` (not `sk-or-`) | `^sk-(?!or-)` | `sk-proj-abc123...` |
| Anthropic | `sk-ant-*` | `^sk-ant-` | `sk-ant-api03-abc123...` |
| HuggingFace | `hf_*` | `^hf_` | `hf_abc123...` |
| Groq | `gsk_*` | `^gsk_` | `gsk_abc123...` |
| X.AI | `xai-*` | `^xai-` | `xai-abc123...` |
| Google AI | `AIza*` | `^AIza` | `AIzaSy...` |

**Validation Behavior**:
- ✅ Valid key → Key saved, 200 OK response
- ❌ Invalid format → 400 Bad Request with format hint

---

## Database Schema

### Table: `platform_settings`

```sql
CREATE TABLE platform_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT,  -- Encrypted with Fernet
    category VARCHAR(100),
    is_secret BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Key Values**:
- `openrouter_api_key`
- `openai_api_key`
- `anthropic_api_key`
- `huggingface_api_key`
- `groq_api_key`
- `xai_api_key`
- `google_ai_api_key`

**Example Row**:
```
key                | value                    | category | is_secret | updated_at
-------------------+--------------------------+----------+-----------+----------------------------
openrouter_api_key | gAAAABhm...encrypted...= | api_keys | true      | 2025-11-14 22:28:05.702296
```

---

## Encryption Details

**Encryption Method**: Fernet (symmetric encryption)
**Key Location**: `ENCRYPTION_KEY` environment variable
**Implementation**: `key_encryption.py`

**Encryption Process**:
1. Admin submits plain text API key
2. Backend validates key format
3. Fernet encrypts the key
4. Encrypted key stored in database
5. Database column type: `TEXT` (base64 encoded)

**Decryption Process**:
1. Backend retrieves encrypted key from database
2. Fernet decrypts using `ENCRYPTION_KEY`
3. Plain text key returned (only via `/decrypted` endpoint)

**Security Features**:
- ✅ All keys stored encrypted at rest
- ✅ Admin-only access (role-based authentication)
- ✅ Session-based authentication (no API key exposure in logs)
- ✅ Audit logging for all key operations
- ✅ Environment variable fallback (no database required)

---

## Authentication & Authorization

**Authentication Method**: Session-based (Keycloak SSO)
**Required Role**: `admin`

**Access Control**:
- ✅ Admin users: Full CRUD access to all platform keys
- ❌ Non-admin users: No access (403 Forbidden)
- ❌ Unauthenticated: No access (401 Unauthorized)

**Session Validation**:
```python
session_token = request.cookies.get("session_token")
session_data = sessions.get(session_token)
user_role = session_data["user"]["role"]

if user_role != "admin":
    raise HTTPException(status_code=403, detail="Admin access required")
```

---

## Usage Examples

### Example 1: Update OpenRouter Key
```bash
# Login first to get session cookie
curl -X POST http://localhost:8084/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin@example.com", "password": "password"}' \
  -c cookies.txt

# Update OpenRouter key
curl -X PUT http://localhost:8084/api/v1/admin/platform-keys/openrouter \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"api_key": "sk-or-v1-abc123..."}'
```

### Example 2: List All Keys
```bash
curl -X GET http://localhost:8084/api/v1/admin/platform-keys \
  -b cookies.txt
```

### Example 3: Retrieve Decrypted OpenAI Key
```bash
curl -X GET http://localhost:8084/api/v1/admin/platform-keys/openai/decrypted \
  -b cookies.txt
```

### Example 4: Update Multiple Providers
```bash
# OpenAI
curl -X PUT http://localhost:8084/api/v1/admin/platform-keys/openai \
  -H "Content-Type: application/json" -b cookies.txt \
  -d '{"api_key": "sk-proj-abc123..."}'

# Anthropic
curl -X PUT http://localhost:8084/api/v1/admin/platform-keys/anthropic \
  -H "Content-Type: application/json" -b cookies.txt \
  -d '{"api_key": "sk-ant-api03-abc123..."}'

# HuggingFace
curl -X PUT http://localhost:8084/api/v1/admin/platform-keys/huggingface \
  -H "Content-Type: application/json" -b cookies.txt \
  -d '{"api_key": "hf_abc123..."}'
```

---

## Testing

### Test OpenRouter Key (Already Saved)
```bash
# Check if key exists
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT key, category, updated_at FROM platform_settings WHERE key = 'openrouter_api_key';"

# Expected output:
#        key         | category |         updated_at
# -------------------+----------+----------------------------
#  openrouter_api_key | api_keys | 2025-11-14 22:28:05.702296
```

### Test Key Format Validation
```bash
# Valid OpenAI key (should succeed)
curl -X PUT http://localhost:8084/api/v1/admin/platform-keys/openai \
  -H "Content-Type: application/json" -b cookies.txt \
  -d '{"api_key": "sk-proj-test123"}'

# Invalid OpenAI key (should fail with 400)
curl -X PUT http://localhost:8084/api/v1/admin/platform-keys/openai \
  -H "Content-Type: application/json" -b cookies.txt \
  -d '{"api_key": "invalid-key"}'
```

### Test Encryption/Decryption
```bash
# 1. Save a test key
curl -X PUT http://localhost:8084/api/v1/admin/platform-keys/groq \
  -H "Content-Type: application/json" -b cookies.txt \
  -d '{"api_key": "gsk_test123456"}'

# 2. Verify encrypted in database
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT value FROM platform_settings WHERE key = 'groq_api_key';"
# Should show: gAAAABhm...encrypted...=

# 3. Retrieve decrypted key
curl http://localhost:8084/api/v1/admin/platform-keys/groq/decrypted -b cookies.txt
# Should show: {"api_key": "gsk_test123456", ...}
```

---

## Integration with LiteLLM

The platform keys system integrates with LiteLLM for multi-provider routing:

**LiteLLM Configuration** (`litellm_api.py`):
```python
PROVIDER_CONFIGS = {
    'openai': {
        'base_url': 'https://api.openai.com/v1',
        'model_prefixes': ['openai/', 'gpt-', 'o1-', 'o3-']
    },
    'anthropic': {
        'base_url': 'https://api.anthropic.com/v1',
        'model_prefixes': ['anthropic/', 'claude-']
    },
    'openrouter': {
        'base_url': 'https://openrouter.ai/api/v1',
        'model_prefixes': []  # Accepts all models
    },
    'google': {
        'base_url': 'https://generativelanguage.googleapis.com/v1beta',
        'model_prefixes': ['google/', 'gemini-']
    }
}
```

**Provider Detection**:
```python
def detect_provider_from_model(model_name: str) -> str:
    """Detect provider from model name"""
    for provider, config in PROVIDER_CONFIGS.items():
        for prefix in config['model_prefixes']:
            if model_name.lower().startswith(prefix.lower()):
                return provider
    return 'openrouter'  # Default
```

**Key Retrieval for LLM Calls**:
```python
# Get provider API key from database or environment
async def get_provider_api_key(provider: str) -> str:
    key_name = f"{provider}_api_key"

    # Check database first
    db_encrypted = await get_platform_key_from_db(db_pool, key_name)
    if db_encrypted:
        return encryption.decrypt_key(db_encrypted)

    # Fallback to environment variable
    env_var = PLATFORM_KEYS[key_name]["env_var"]
    return os.getenv(env_var)
```

---

## Troubleshooting

### Issue: "Not authenticated - no session token"
**Cause**: Missing or invalid session cookie
**Solution**: Login first to obtain session token
```bash
curl -X POST http://localhost:8084/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin@example.com", "password": "password"}' \
  -c cookies.txt
```

### Issue: "Admin access required (current role: viewer)"
**Cause**: User doesn't have admin role
**Solution**: Upgrade user to admin role in Keycloak

### Issue: "Invalid API key format"
**Cause**: API key doesn't match expected format
**Solution**: Check key format in provider documentation
- OpenRouter: `sk-or-v1-...`
- OpenAI: `sk-proj-...`
- Anthropic: `sk-ant-...`

### Issue: "Encryption failed"
**Cause**: Missing or invalid `ENCRYPTION_KEY` environment variable
**Solution**: Set encryption key in `.env.auth`
```bash
# Generate new encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env.auth
echo "ENCRYPTION_KEY=your-generated-key-here" >> .env.auth

# Restart container
docker restart ops-center-centerdeep
```

### Issue: Keys not persisting after restart
**Cause**: Database volume not mounted correctly
**Solution**: Check docker-compose.yml has PostgreSQL volume
```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
```

---

## Security Best Practices

### 1. Encryption Key Management
- ✅ Store `ENCRYPTION_KEY` securely (environment variable, never commit to git)
- ✅ Use strong encryption key (Fernet generates cryptographically secure keys)
- ✅ Rotate encryption key periodically (requires re-encrypting all keys)

### 2. Access Control
- ✅ Limit admin access to trusted personnel only
- ✅ Use session-based authentication (no API keys in URLs)
- ✅ Enable audit logging for all key operations

### 3. Network Security
- ✅ Use HTTPS/SSL for all API requests
- ✅ Implement rate limiting on key update endpoints
- ✅ Restrict `/decrypted` endpoints to internal networks only

### 4. Database Security
- ✅ Use strong PostgreSQL passwords
- ✅ Enable PostgreSQL SSL connections
- ✅ Regular database backups
- ✅ Monitor for unauthorized database access

### 5. Audit Logging
All key operations are logged:
```python
logger.info(f"Admin {current_user.get('email')} updated OpenAI API key")
logger.info(f"Admin {current_user.get('email')} retrieved OpenRouter API key")
```

**Log Location**: Docker container logs (`docker logs ops-center-centerdeep`)

---

## Future Enhancements

### Phase 2 (Planned)
- [ ] Key rotation automation
- [ ] Multi-region key replication
- [ ] Key usage analytics
- [ ] Provider health monitoring
- [ ] Cost tracking per provider
- [ ] API key expiration warnings

### Phase 3 (Planned)
- [ ] Frontend UI for key management
- [ ] Bulk key import/export
- [ ] Key versioning and rollback
- [ ] Granular access control (per-provider permissions)
- [ ] Webhook notifications for key changes

---

## API Endpoint Reference

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/admin/platform-keys` | GET | List all platform keys | Admin |
| `/api/v1/admin/platform-keys/openrouter` | PUT | Update OpenRouter key | Admin |
| `/api/v1/admin/platform-keys/openrouter/decrypted` | GET | Get OpenRouter key | Admin |
| `/api/v1/admin/platform-keys/openai` | PUT | Update OpenAI key | Admin |
| `/api/v1/admin/platform-keys/openai/decrypted` | GET | Get OpenAI key | Admin |
| `/api/v1/admin/platform-keys/anthropic` | PUT | Update Anthropic key | Admin |
| `/api/v1/admin/platform-keys/anthropic/decrypted` | GET | Get Anthropic key | Admin |
| `/api/v1/admin/platform-keys/huggingface` | PUT | Update HuggingFace key | Admin |
| `/api/v1/admin/platform-keys/huggingface/decrypted` | GET | Get HuggingFace key | Admin |
| `/api/v1/admin/platform-keys/groq` | PUT | Update Groq key | Admin |
| `/api/v1/admin/platform-keys/groq/decrypted` | GET | Get Groq key | Admin |
| `/api/v1/admin/platform-keys/xai` | PUT | Update X.AI key | Admin |
| `/api/v1/admin/platform-keys/xai/decrypted` | GET | Get X.AI key | Admin |
| `/api/v1/admin/platform-keys/google` | PUT | Update Google AI key | Admin |
| `/api/v1/admin/platform-keys/google/decrypted` | GET | Get Google AI key | Admin |

**Total Endpoints**: 16 (2 per provider × 7 providers + 2 list/provisioning)

---

## Provider Comparison

| Provider | Models | Speed | Cost | Key Format | Status |
|----------|--------|-------|------|------------|--------|
| OpenRouter | 348+ | Fast | Variable | `sk-or-v1-...` | ✅ Configured |
| OpenAI | 15+ | Fast | High | `sk-proj-...` | ⚪ Ready |
| Anthropic | 6+ | Fast | High | `sk-ant-...` | ⚪ Ready |
| HuggingFace | 100k+ | Variable | Low/Free | `hf_...` | ⚪ Ready |
| Groq | 10+ | Ultra-Fast | Medium | `gsk_...` | ⚪ Ready |
| X.AI | 2+ | Fast | Medium | `xai-...` | ⚪ Ready |
| Google AI | 4+ | Fast | Low | `AIza...` | ⚪ Ready |

---

## Conclusion

The Platform Keys API provides a secure, centralized, and scalable solution for managing LLM provider API keys across the UC-Cloud ecosystem. With support for 7 major providers, encrypted storage, and comprehensive validation, it ensures that your API keys are protected while remaining easily accessible to authorized administrators.

**Ready to Use**: All 7 providers are now supported. Simply obtain API keys from your chosen providers and use the PUT endpoints to configure them.

**Questions or Issues?**: Check the troubleshooting section or contact the backend team.

---

**Document Version**: 2.0
**Last Updated**: November 14, 2025
**Maintained By**: Backend Team Lead
**Related Files**:
- `/backend/platform_keys_api.py` - Main implementation
- `/backend/key_encryption.py` - Encryption utilities
- `/backend/litellm_api.py` - LLM provider integration
