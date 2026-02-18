# Admin Provider Key Management Guide

**Last Updated**: October 27, 2025
**Status**: Analysis Complete

---

## Executive Summary

This document clarifies **where admins configure system-level provider API keys** for metering users (not user BYOK keys).

### TL;DR: Current State

**System provider keys are stored in the PostgreSQL database (`llm_providers` table)**, but there is **NO CLEAR ADMIN UI** for setting them.

**Key Distinction**:
1. **System Provider Keys** (Admin sets) → Used for metering ALL users → **❓ UI UNCLEAR**
2. **User BYOK Keys** (User brings) → User pays provider directly → **✅ AccountAPIKeys.jsx DONE**

---

## Current Architecture Analysis

### 1. Where System Keys ARE Stored

**Database**: PostgreSQL `llm_providers` table
**Schema**:
```sql
CREATE TABLE llm_providers (
    id SERIAL PRIMARY KEY,
    provider_name VARCHAR(100) UNIQUE NOT NULL,
    provider_slug VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    base_url VARCHAR(500),
    auth_type VARCHAR(50) DEFAULT 'api_key',
    api_key_format VARCHAR(100),  -- e.g., "sk-*", "Bearer *"

    -- System key storage (plaintext for now, should be encrypted)
    -- NOTE: No encrypted_api_key column exists in the schema!
    -- Keys are likely stored in environment variables or config files

    is_active BOOLEAN DEFAULT TRUE,
    is_byok_supported BOOLEAN DEFAULT TRUE,
    is_system_provider BOOLEAN DEFAULT FALSE,  -- System-managed provider

    health_status VARCHAR(50) DEFAULT 'unknown',
    min_tier_required VARCHAR(50) DEFAULT 'free',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Critical Finding**: The schema does NOT include an `encrypted_api_key` column for storing system provider keys! This suggests keys are managed via:
- Environment variables (`.env`)
- Config files
- External secret management

### 2. Backend API Endpoints

**Existing Admin APIs**:
- **`/api/v1/admin/llm/providers`** (GET) - List providers
- **`/api/v1/admin/llm/providers`** (POST) - Create provider
- **`/api/v1/admin/llm/providers/{id}`** (PUT) - Update provider
- **`/api/v1/admin/llm/providers/{id}/test`** (POST) - Test connection

**Key Management Endpoints** (from `litellm_api.py`):
```python
# These endpoints are for BYOK (user keys), NOT system keys!
POST   /api/v1/llm/byok/keys              # Add user BYOK key
GET    /api/v1/llm/byok/keys              # List user BYOK keys
DELETE /api/v1/llm/byok/keys/{provider}   # Delete user BYOK key
POST   /api/v1/llm/byok/keys/{provider}/test  # Test user BYOK key
```

**⚠️ No dedicated endpoints for system key management found!**

### 3. Frontend Pages Analysis

#### Page 1: `LLMProviderSettings.jsx`
**Location**: `/opt/ops-center/src/pages/LLMProviderSettings.jsx`

**What it does**:
- **Two tabs**: "AI Servers" and "API Keys"
- **AI Servers**: Manage local inference servers (vLLM, Ollama, LocalAI)
  - Endpoints: `/api/v1/llm-config/servers`
  - **NOT for provider API keys!**
- **API Keys**: **USER BYOK keys** (not system keys!)
  - Endpoints: `/api/v1/llm-config/api-keys`
  - **User-level, not admin system keys!**

**Verdict**: ❌ **NOT for system provider keys**

---

#### Page 2: `OpenRouterSettings.jsx`
**Location**: `/opt/ops-center/src/pages/OpenRouterSettings.jsx`

**What it does**:
- Single provider configuration page for **OpenRouter**
- **API Key Input**: Password field with save/test buttons
- **Endpoints**:
  - GET `/api/v1/llm/providers` - Fetch OpenRouter provider
  - PUT `/api/v1/llm/providers/{id}` - Update API key
  - POST `/api/v1/llm/chat/completions` - Test API key

**Code Snippet**:
```javascript
const saveApiKey = async () => {
  const response = await fetch(`/api/v1/llm/providers/${provider.id}`, {
    method: 'PUT',
    body: JSON.stringify({
      api_key_encrypted: apiKey,  // Stored as 'api_key_encrypted'
      enabled: true
    })
  });
};
```

**Verdict**: ✅ **This IS for system OpenRouter key!**
**Issue**: Only handles OpenRouter, not OpenAI/Anthropic/Google

---

#### Page 3: `LLMProviderManagement.jsx`
**Location**: `/opt/ops-center/src/pages/LLMProviderManagement.jsx`

**What it does**:
- **Comprehensive multi-provider management UI**
- **5 Tabs**:
  1. **Providers** - List/create/edit/delete providers
  2. **Models** - Manage models for each provider
  3. **Routing Rules** - Configure WilmerAI-style routing
  4. **Usage Analytics** - View usage stats
  5. **BYOK Settings** - User BYOK configuration instructions

**Provider Dialog** (Add/Edit):
```javascript
<TextField
  label="API Key"
  type="password"
  value={providerForm.api_key}
  onChange={(e) => setProviderForm({ ...providerForm, api_key: e.target.value })}
  placeholder={editingProvider ? "Leave blank to keep current key" : "sk-..."}
  helperText="OpenAI: platform.openai.com/api-keys | Anthropic: console.anthropic.com"
/>
```

**Endpoints**:
```javascript
POST /api/v1/llm/providers          // Create provider (includes api_key)
PUT  /api/v1/llm/providers/{id}      // Update provider (optional api_key)
GET  /api/v1/llm/providers           // List providers
DELETE /api/v1/llm/providers/{id}    // Delete provider
POST /api/v1/llm/test                // Test provider
```

**Verdict**: ✅ **This IS for system provider keys!**
**Designed for**: OpenRouter, OpenAI, Anthropic, Google, etc.

---

## Summary: Where Admin Sets System Keys

### Current Implementation

| Provider | UI Page | API Endpoint | Database Storage | Status |
|----------|---------|--------------|------------------|--------|
| **OpenRouter** | `OpenRouterSettings.jsx` | `/api/v1/llm/providers/{id}` | `api_key_encrypted` field | ✅ Working |
| **OpenAI, Anthropic, Google** | `LLMProviderManagement.jsx` | `/api/v1/llm/providers` (POST/PUT) | `api_key` field (NOT in schema!) | ⚠️ Unclear |
| **All Providers** | `LLMProviderManagement.jsx` | `/api/v1/admin/llm/providers` | Database table `llm_providers` | ⚠️ Unclear |

### Critical Gap Identified

**Problem**: The database schema (`llm_providers` table) **does NOT have a column for storing system API keys!**

**Evidence**:
1. `OpenRouterSettings.jsx` sends `api_key_encrypted` field
2. `LLMProviderManagement.jsx` sends `api_key` field
3. Database schema in `llm_models.py` shows:
   - ✅ `api_key_format` (format pattern, e.g., "sk-*")
   - ❌ **NO `api_key_encrypted` or `api_key` column!**

**Where are system keys actually stored?**

Looking at `litellm_api.py` (line 322-346):
```python
# Get OpenRouter provider from database
provider = await conn.fetchrow("""
    SELECT id, name, type, api_key_encrypted, config
    FROM llm_providers
    WHERE enabled = true AND type = 'openrouter'
    ORDER BY priority DESC
    LIMIT 1
""")

api_key = provider['api_key_encrypted']  # Plain text for now
```

**This query references `api_key_encrypted` column, but it's NOT in the schema!**

### Likely Explanation

**System keys are stored in environment variables:**
- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`

**Evidence from `byok_helpers.py` (line 117-121)**:
```python
# Fallback to system key
system_key = os.getenv(fallback_env_var)

if system_key:
    logger.info(f"Using system key for {user_email}/{provider}")
    return system_key
```

---

## Recommendations

### Option A: Environment Variable Configuration (Current State)

**How it works**:
1. Admin sets environment variables in `.env.auth`:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-...
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   GOOGLE_API_KEY=...
   ```
2. Backend reads from `os.getenv()` when no user BYOK key exists
3. Requires container restart to update

**Pros**:
- ✅ Simple and secure (keys outside database)
- ✅ Standard practice for secrets
- ✅ Works with secret management tools (Docker secrets, Kubernetes secrets)

**Cons**:
- ❌ No UI for admins to change keys
- ❌ Requires SSH/shell access
- ❌ Requires container restart

**Current Documentation Location**:
- Main `.env.auth` file in `/opt/ops-center/.env.auth`
- Instructions in project README

---

### Option B: Database Storage (Encrypted)

**How it works**:
1. Add `encrypted_api_key` column to `llm_providers` table
2. Admin sets keys via UI (either existing page or new dedicated page)
3. Keys encrypted with AES-256 before storage
4. Backend decrypts on use

**Database Migration**:
```sql
ALTER TABLE llm_providers
ADD COLUMN encrypted_api_key TEXT NULL;

-- Update existing providers
UPDATE llm_providers
SET encrypted_api_key = encrypt_key(getenv('OPENROUTER_API_KEY'))
WHERE provider_slug = 'openrouter';
```

**Backend Implementation** (update `llm_provider_management_api.py`):
```python
from key_encryption import get_encryption

@router.put("/{provider_id}/api-key")
async def update_provider_api_key(
    provider_id: int,
    api_key: str,
    db: Session = Depends(get_db),
    user: str = Depends(require_admin)
):
    """
    Update provider system API key

    Admin only. Encrypts and stores key in database.
    """
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Encrypt key
    encryption = get_encryption()
    encrypted_key = encryption.encrypt_key(api_key)

    # Store
    provider.encrypted_api_key = encrypted_key
    provider.updated_at = datetime.utcnow()

    db.commit()

    return {"success": True, "message": "API key updated"}
```

**Frontend Implementation** (new page or update existing):
```javascript
// SystemProviderKeys.jsx
const saveSystemKey = async (provider, apiKey) => {
  const response = await fetch(`/api/v1/admin/llm/providers/${provider.id}/api-key`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey })
  });

  if (response.ok) {
    showToast('System API key updated successfully', 'success');
  }
};
```

**Pros**:
- ✅ No container restart needed
- ✅ UI-based management
- ✅ Encrypted at rest
- ✅ Admin can update keys dynamically

**Cons**:
- ❌ Keys in database (even if encrypted)
- ❌ Requires database migration
- ❌ Encryption key management needed

---

### Option C: Hybrid Approach (Recommended)

**How it works**:
1. System prefers environment variables (most secure)
2. Fallback to database if env var not set
3. Admin UI shows which source is being used
4. Admin can override env var with database key via UI

**Implementation**:
```python
async def get_system_api_key(provider_slug: str, db: Session) -> Optional[str]:
    """
    Get system API key for provider

    Priority:
    1. Environment variable (most secure)
    2. Database encrypted_api_key
    3. None (error)
    """
    # Try environment variable first
    env_var_map = {
        'openrouter': 'OPENROUTER_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'google': 'GOOGLE_API_KEY'
    }

    env_key = os.getenv(env_var_map.get(provider_slug))
    if env_key:
        logger.info(f"Using system key from environment for {provider_slug}")
        return env_key

    # Fallback to database
    provider = db.query(LLMProvider).filter(
        LLMProvider.provider_slug == provider_slug
    ).first()

    if provider and provider.encrypted_api_key:
        encryption = get_encryption()
        decrypted_key = encryption.decrypt_key(provider.encrypted_api_key)
        logger.info(f"Using system key from database for {provider_slug}")
        return decrypted_key

    logger.error(f"No system key found for {provider_slug}")
    return None
```

**Admin UI** (update `LLMProviderManagement.jsx`):
```javascript
// Show which source is being used
<Alert severity="info">
  {provider.api_key_source === 'environment' ? (
    <>
      <strong>Using environment variable</strong>: OPENROUTER_API_KEY
      <br/>To override, enter a new key below.
    </>
  ) : (
    <>
      <strong>Using database key</strong>
      <br/>Last updated: {provider.api_key_updated_at}
    </>
  )}
</Alert>

<TextField
  label="System API Key"
  type="password"
  placeholder="Leave blank to use environment variable"
  helperText="Overrides OPENROUTER_API_KEY environment variable"
/>
```

**Pros**:
- ✅ Best of both worlds
- ✅ Environment variables for production (most secure)
- ✅ Database override for development/testing
- ✅ Clear admin visibility

**Cons**:
- ❌ More complex implementation
- ❌ Potential confusion about which key is active

---

## Implementation Plan

### Phase 1: Fix Database Schema ✅ **REQUIRED**

**Add missing column**:
```sql
ALTER TABLE llm_providers
ADD COLUMN encrypted_api_key TEXT NULL;

ALTER TABLE llm_providers
ADD COLUMN api_key_source VARCHAR(50) DEFAULT 'environment';  -- 'environment' or 'database'

ALTER TABLE llm_providers
ADD COLUMN api_key_updated_at TIMESTAMP NULL;
```

**Update backend models** (`llm_models.py`):
```python
class LLMProvider(Base):
    # ... existing fields ...

    # System API Key (encrypted)
    encrypted_api_key = Column(Text, nullable=True)
    api_key_source = Column(String(50), default='environment')  # 'environment' or 'database'
    api_key_updated_at = Column(DateTime, nullable=True)
```

---

### Phase 2: Update Backend API ✅ **REQUIRED**

**Create new endpoint** (`llm_provider_management_api.py`):
```python
@router.put("/{provider_id}/system-key")
async def update_provider_system_key(
    provider_id: int,
    api_key: str,
    db: Session = Depends(get_db),
    user: str = Depends(require_admin)
):
    """
    Update provider system API key

    Admin only. Encrypts and stores key in database.
    Overrides environment variable.
    """
    # Implementation as shown in Option B

@router.delete("/{provider_id}/system-key")
async def delete_provider_system_key(
    provider_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(require_admin)
):
    """
    Delete provider system API key

    Falls back to environment variable.
    """
    # Set encrypted_api_key = NULL, api_key_source = 'environment'

@router.post("/{provider_id}/test-system-key")
async def test_provider_system_key(
    provider_id: int,
    api_key: Optional[str] = None,
    db: Session = Depends(get_db),
    user: str = Depends(require_admin)
):
    """
    Test provider system API key

    If api_key provided, test it without saving.
    If not provided, test currently active key.
    """
    # Make test API call to provider
```

---

### Phase 3: Update Admin UI ✅ **REQUIRED**

**Option 3A: Update Existing Page (`LLMProviderManagement.jsx`)**

Add "System Key" tab or section:
```javascript
<Dialog open={systemKeyDialogOpen}>
  <DialogTitle>Configure System API Key - {provider.display_name}</DialogTitle>
  <DialogContent>
    <Alert severity="info" sx={{ mb: 2 }}>
      <Typography variant="body2">
        <strong>Current Source:</strong> {provider.api_key_source === 'environment' ?
          'Environment Variable' : 'Database (Encrypted)'}
      </Typography>
      {provider.api_key_source === 'environment' && (
        <Typography variant="caption">
          Using: {getEnvVarName(provider.provider_slug)}
        </Typography>
      )}
    </Alert>

    <TextField
      fullWidth
      label="System API Key"
      type={showKey ? 'text' : 'password'}
      value={systemKey}
      onChange={(e) => setSystemKey(e.target.value)}
      placeholder="sk-..."
      helperText="This key will be used for ALL users (unless they have BYOK configured)"
    />

    <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
      <Button
        variant="outlined"
        startIcon={<TestIcon />}
        onClick={() => testSystemKey(provider.id, systemKey)}
      >
        Test Connection
      </Button>
      <Button
        variant="contained"
        startIcon={<SaveIcon />}
        onClick={() => saveSystemKey(provider.id, systemKey)}
      >
        Save Key
      </Button>
      {provider.api_key_source === 'database' && (
        <Button
          variant="outlined"
          color="error"
          startIcon={<DeleteIcon />}
          onClick={() => deleteSystemKey(provider.id)}
        >
          Delete (Use Env Var)
        </Button>
      )}
    </Box>
  </DialogContent>
</Dialog>
```

**Option 3B: Create New Dedicated Page (`SystemProviderKeys.jsx`)**

```javascript
// src/pages/SystemProviderKeys.jsx

export default function SystemProviderKeys() {
  const [providers, setProviders] = useState([]);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>
        System Provider API Keys
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          These are system-level keys used for metering ALL users.
          Users with BYOK (Bring Your Own Key) will use their own keys instead.
        </Typography>
      </Alert>

      <Grid container spacing={3}>
        {providers.map(provider => (
          <Grid item xs={12} md={6} key={provider.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{provider.display_name}</Typography>
                <Chip
                  label={provider.api_key_source === 'environment' ?
                    'Environment Variable' : 'Database (Encrypted)'
                  }
                  color={provider.api_key_source === 'environment' ? 'success' : 'primary'}
                  size="small"
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  label="System API Key"
                  type="password"
                  placeholder="Enter API key to override environment variable"
                  helperText={`Get from: ${provider.documentation_url}`}
                />

                <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                  <Button variant="outlined" startIcon={<TestIcon />}>Test</Button>
                  <Button variant="contained" startIcon={<SaveIcon />}>Save</Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
```

**Navigation Update** (`Layout.jsx`):
```javascript
{/* Under Platform section */}
<ListItem button component={Link} to="/admin/system-provider-keys">
  <ListItemIcon><KeyIcon /></ListItemIcon>
  <ListItemText primary="System Provider Keys" secondary="Platform API Keys" />
</ListItem>
```

---

## Security Best Practices

### 1. Encryption at Rest
```python
from cryptography.fernet import Fernet
from key_encryption import get_encryption

encryption = get_encryption()

# Encrypt before storing
encrypted_key = encryption.encrypt_key(api_key)

# Decrypt when using
decrypted_key = encryption.decrypt_key(encrypted_key)
```

### 2. Key Rotation
- Admin can update keys via UI without downtime
- Old key remains active until new key is saved
- Test new key before saving to prevent service disruption

### 3. Access Control
- **Admin-only endpoints** - Enforce RBAC via `require_admin()`
- **Audit logging** - Log all key changes
- **Masked display** - Show only last 4 characters in UI

### 4. Environment Variables (Production)
```bash
# .env.auth (most secure)
OPENROUTER_API_KEY=sk-or-v1-...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Docker secrets (even more secure)
docker secret create openrouter_api_key /path/to/key
```

---

## User Flow Examples

### Admin Setting System Key (First Time)

1. Admin logs in → Opens **Platform → System Provider Keys**
2. Sees list of providers (OpenRouter, OpenAI, Anthropic, Google)
3. Each provider card shows:
   - Current source: "Environment Variable (Not Set)" or "Database (Encrypted)"
   - API key input (masked)
   - Test button, Save button
4. Admin enters OpenRouter API key `sk-or-v1-...`
5. Clicks **Test** → Success: "Valid API key. 348 models available."
6. Clicks **Save** → Key encrypted and stored in database
7. Provider card updates: "Database (Encrypted) • Last updated: 2025-10-27"

### Admin Updating Existing Key

1. Admin opens **System Provider Keys**
2. OpenRouter card shows: "Database (Encrypted) • Last updated: 2025-10-27"
3. Admin enters new key
4. Clicks **Test** → Success
5. Clicks **Save** → Old key replaced, no downtime
6. Audit log created: "admin@example.com updated system key for openrouter"

### Admin Deleting Database Key (Fallback to Env Var)

1. Admin opens **System Provider Keys**
2. OpenRouter card shows: "Database (Encrypted)"
3. Admin clicks **Delete Key** button
4. Confirmation: "This will delete the database key and fallback to environment variable. Continue?"
5. Clicks **Confirm** → `encrypted_api_key` set to NULL, `api_key_source` = 'environment'
6. Card updates: "Environment Variable (OPENROUTER_API_KEY)"

---

## Testing Checklist

### Backend Tests
- [ ] Add system key to database (encrypted)
- [ ] Retrieve system key (decrypted)
- [ ] Update system key (old key deleted)
- [ ] Delete system key (fallback to env var)
- [ ] Test system key against provider API
- [ ] Verify environment variable takes priority
- [ ] Verify database key works when env var not set

### Frontend Tests
- [ ] Load system provider keys page
- [ ] Display current key source (environment vs database)
- [ ] Enter new API key (masked)
- [ ] Toggle show/hide key
- [ ] Test connection button (success/failure)
- [ ] Save key (success/error handling)
- [ ] Delete key (confirmation dialog)
- [ ] Refresh page (key masked, last 4 chars shown)

### Integration Tests
- [ ] User with BYOK uses their own key (not system key)
- [ ] User without BYOK uses system key
- [ ] System key update doesn't break existing requests
- [ ] Audit log records all key changes
- [ ] Admin permission enforced (non-admin gets 403)

---

## Appendix: Environment Variable Names

### Supported Providers

| Provider | Env Var Name | Example Key Format |
|----------|--------------|-------------------|
| OpenRouter | `OPENROUTER_API_KEY` | `sk-or-v1-...` |
| OpenAI | `OPENAI_API_KEY` | `sk-proj-...` |
| Anthropic | `ANTHROPIC_API_KEY` | `sk-ant-api03-...` |
| Google AI | `GOOGLE_API_KEY` | `AIza...` |
| Together AI | `TOGETHER_API_KEY` | `...` |
| HuggingFace | `HUGGINGFACE_TOKEN` | `hf_...` |
| Groq | `GROQ_API_KEY` | `gsk_...` |

### Where to Get Keys

- **OpenRouter**: https://openrouter.ai/keys
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/account/keys
- **Google AI**: https://makersuite.google.com/app/apikey
- **Together AI**: https://api.together.xyz/settings/api-keys
- **HuggingFace**: https://huggingface.co/settings/tokens

---

## Conclusion

**Current Answer to User's Question**:

> "Where do I, as admin, set the provider keys for the SERVER?"

**Answer**:
1. **OpenRouter ONLY**: Use `OpenRouterSettings.jsx` page (currently working)
2. **All Providers** (OpenAI, Anthropic, Google): Use `LLMProviderManagement.jsx` → Providers tab → Edit provider → Enter API key
3. **Backend**: Keys stored in environment variables (`.env.auth`) as fallback

**Critical Gap**:
- Database schema missing `encrypted_api_key` column
- No clear dedicated UI for system key management
- Current UI mixes provider CRUD with key management

**Recommended Next Steps**:
1. **Phase 1**: Add `encrypted_api_key` column to database ✅
2. **Phase 2**: Create dedicated `/admin/system-provider-keys` page ✅
3. **Phase 3**: Implement hybrid approach (env var + database) ✅
4. **Phase 4**: Update existing pages with clear labels ("System Keys" vs "User BYOK") ✅

---

**Document Status**: ✅ Analysis Complete • ⚠️ Implementation Pending

**Related Documents**:
- User BYOK Management: `/services/ops-center/src/pages/account/AccountAPIKeys.jsx`
- Backend Provider API: `/services/ops-center/backend/llm_provider_management_api.py`
- Database Models: `/services/ops-center/backend/models/llm_models.py`
- BYOK Helpers: `/services/ops-center/backend/byok_helpers.py`
