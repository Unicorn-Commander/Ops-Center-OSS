# Ops-Center Credential Management - Comprehensive Analysis Report

**Date**: October 23, 2025
**Status**: In-Depth Exploration Complete
**Scope**: Backend encryption/credential system + Frontend credential UI + Current API implementation

---

## Executive Summary

The Ops-Center currently has a **robust encryption and credential management system** in place with:

1. **Backend Encryption Infrastructure** - Fully implemented and operational
   - Fernet symmetric encryption (AES-128-CBC) via `cryptography` library
   - Centralized encryption module (`key_encryption.py`)
   - Secret manager with support for 7 credential types
   - Database schema for encrypted credential storage

2. **Environment-Based Credential Loading** - Currently in use for:
   - Cloudflare API tokens (Epic 1.6)
   - NameCheap API keys (Epic 1.7)
   - System-level credentials loaded from `.env.auth`

3. **User-Level BYOK System** - Partially implemented:
   - API router for user-provided LLM provider keys (`/api/v1/byok`)
   - Encryption using same Fernet cipher
   - Storage in Keycloak user attributes (not PostgreSQL)
   - Frontend component for key management

4. **NO GUI for Cloudflare/NameCheap Credentials** - This is the gap we need to fill

---

## 1. Current Backend Implementation

### 1.1 Encryption Infrastructure

**File**: `/home/muut/Production/UC-Cloud/services/ops-center/backend/key_encryption.py` (92 lines)

```python
class KeyEncryption:
    """Handles encryption/decryption of API keys"""
    
    def __init__(self):
        """Initialize encryption with key from environment"""
        encryption_key = os.getenv('ENCRYPTION_KEY')
        # ... validation ...
        self.cipher = Fernet(encryption_key.encode())
    
    def encrypt_key(self, api_key: str) -> str:
        """Encrypt an API key"""
        encrypted = self.cipher.encrypt(api_key.encode())
        return encrypted.decode()
    
    def decrypt_key(self, encrypted_key: str) -> str:
        """Decrypt an API key"""
        decrypted = self.cipher.decrypt(encrypted_key.encode())
        return decrypted.decode()
    
    def mask_key(self, api_key: str, visible_chars: int = 4) -> str:
        """Mask an API key for display (e.g., "sk-1234...5678")"""
        return f"{api_key[:visible_chars]}...{api_key[-visible_chars:]}"
```

**Key Features**:
- Singleton pattern for encryption instance
- `Fernet` from `cryptography` library (industry-standard)
- Key stored in `ENCRYPTION_KEY` environment variable
- Masking function for secure display

### 1.2 Secret Manager

**File**: `/home/muut/Production/UC-Cloud/services/ops-center/backend/secret_manager.py` (512 lines)

```python
class SecretManager:
    """Centralized secret management with encryption"""
    
    def encrypt_secret(self, secret: str, secret_type: str = SecretType.GENERIC, 
                       metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Encrypt a secret and return with metadata"""
        # Returns: {
        #   "encrypted_value": encrypted_string,
        #   "secret_type": secret_type,
        #   "encrypted_at": ISO timestamp,
        #   "metadata": dict
        # }
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt a secret"""
        # Returns: plaintext secret
    
    def mask_secret(self, secret: str, visible_chars: int = 4) -> str:
        """Mask secret for display"""
    
    def store_encrypted_credential(self, user_id: str, service: str, 
                                   credential_type: str, secret: str, 
                                   db_connection) -> Dict[str, Any]:
        """Store encrypted credential in PostgreSQL"""
        # Parameterized SQL INSERT
        # Returns: {id, user_id, service, credential_type, created_at, masked_value}
    
    def retrieve_decrypted_credential(self, user_id: str, service: str,
                                      credential_type: str, 
                                      db_connection) -> Optional[str]:
        """Retrieve and decrypt credential"""
        # Returns: plaintext secret or None
    
    def rotate_encryption_key(self, old_key: str, new_key: str, 
                              db_connection) -> Dict[str, Any]:
        """Re-encrypt all secrets with new key"""
        # Returns: {success, total_credentials, rotated, failed, rotated_at}
```

**Database Schema** (included in secret_manager.py):
```sql
CREATE TABLE IF NOT EXISTS encrypted_credentials (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    service VARCHAR(100) NOT NULL,
    credential_type VARCHAR(100) NOT NULL,
    encrypted_value TEXT NOT NULL,
    encrypted_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    UNIQUE(user_id, service, credential_type)
);

CREATE INDEX idx_encrypted_credentials_user ON encrypted_credentials(user_id);
CREATE INDEX idx_encrypted_credentials_service ON encrypted_credentials(service);
```

**Supported Secret Types**:
```python
class SecretType:
    CLOUDFLARE_API_TOKEN = "cloudflare_api_token"
    NAMECHEAP_API_KEY = "namecheap_api_key"
    USER_API_KEY = "user_api_key"
    OAUTH_CLIENT_SECRET = "oauth_client_secret"
    STRIPE_SECRET_KEY = "stripe_secret_key"
    DATABASE_PASSWORD = "database_password"
    GENERIC = "generic"
```

### 1.3 BYOK (Bring Your Own Key) System

**Files**:
- `/home/muut/Production/UC-Cloud/services/ops-center/backend/byok_service.py` (354 lines)
- `/home/muut/Production/UC-Cloud/services/ops-center/backend/byok_manager.py` (400 lines)
- `/home/muut/Production/UC-Cloud/services/ops-center/backend/byok_api.py` (512 lines)

**BYOK Service** (`byok_service.py`):
```python
class BYOKService:
    """Service for managing BYOK configurations"""
    
    async def get_user_provider_config(user: Dict, preferred_provider: Optional[str] = None,
                                      preferred_model: Optional[str] = None) -> Dict:
        """Get LLM provider config for user with fallback to system default"""
        # Priority: User preference → User BYOK → System default
        # Returns: {provider, api_key, base_url, model, format, supports_streaming, is_byok}
    
    def _get_user_byok_providers(attributes: Dict) -> Dict:
        """Extract BYOK providers from Keycloak user attributes"""
        # Extracts attributes like: byok_{provider}_key, byok_{provider}_label, etc.
    
    async def get_execution_server_config(user_id: str, server_id: Optional[str]) -> Optional[Dict]:
        """Get Brigade execution server config"""
```

**BYOK Manager** (`byok_manager.py`):
```python
class BYOKManager:
    """Manage user-provided API keys with encryption"""
    
    async def store_user_api_key(user_id: str, provider: str, api_key: str,
                                metadata: Optional[Dict] = None) -> str:
        """Store encrypted user API key in database"""
        # Stores in: user_provider_keys table
        # Returns: key_id (UUID)
    
    async def get_user_api_key(user_id: str, provider: str) -> Optional[str]:
        """Retrieve and decrypt user's API key"""
        # Returns: plaintext API key or None
    
    async def list_user_providers(user_id: str) -> List[Dict]:
        """List all providers with stored API keys for user"""
        # Returns: List of {id, provider, enabled, metadata, created_at, updated_at}
    
    async def validate_api_key(user_id: str, provider: str, api_key: str) -> bool:
        """Validate API key format"""
        # Provider-specific validation rules (OpenAI, Anthropic, etc.)
```

### 1.4 BYOK API Router

**File**: `/home/muut/Production/UC-Cloud/services/ops-center/backend/byok_api.py` (512 lines)

```python
# Endpoints:
@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers(request: Request):
    """Get list of supported providers"""
    # Returns: [{"id": "openai", "name": "OpenAI", "key_format": "sk-", "configured": bool}]

@router.get("/keys", response_model=List[APIKeyResponse])
async def list_keys(request: Request):
    """List user's configured API keys (masked)"""
    # Returns: [{"provider": "openai", "provider_name": "OpenAI", "key_preview": "sk-1234...5678", ...}]

@router.post("/keys/add")
@require_tier(["starter", "professional", "enterprise"])
async def add_key(key_data: APIKeyAdd, request: Request):
    """Add or update an API key (tier-restricted)"""
    # Encrypts key and stores in Keycloak user attributes

@router.delete("/keys/{provider}")
async def delete_key(provider: str, request: Request):
    """Remove an API key"""

@router.post("/keys/test/{provider}", response_model=APIKeyTestResult)
async def test_key(provider: str, request: Request):
    """Test if an API key is valid"""
    # Makes HTTP request to provider to validate

@router.get("/stats")
async def get_byok_stats(request: Request):
    """Get statistics about user's BYOK configuration"""
```

**IMPORTANT**: BYOK keys are stored in **Keycloak user attributes**, NOT in PostgreSQL:
- `byok_{provider}_key` - Encrypted API key
- `byok_{provider}_label` - User-provided label
- `byok_{provider}_endpoint` - Custom endpoint URL
- `byok_{provider}_added_date` - When key was added
- `byok_{provider}_last_tested` - Last test timestamp
- `byok_{provider}_test_status` - Last test result

---

## 2. Current Environment Credential Loading

### 2.1 Cloudflare Credentials

**File**: `/home/muut/Production/UC-Cloud/services/ops-center/.env.auth` (56 lines)

```bash
# === Cloudflare DNS Management (Epic 1.6) ===
CLOUDFLARE_API_TOKEN=<CLOUDFLARE_API_TOKEN_REDACTED>
CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_API_BASE_URL=https://api.cloudflare.com/client/v4

# ⚠️ SECURITY WARNING: Current API token is exposed
# TODO: Revoke and replace with new token before production use
```

**Usage** (`backend/cloudflare_api.py`, lines 45-48):
```python
import os
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
cloudflare_manager = CloudflareManager(api_token=CLOUDFLARE_API_TOKEN) if CLOUDFLARE_API_TOKEN else None
```

**⚠️ SECURITY ISSUES**:
- Token is exposed in `.env.auth` file (checked into git!)
- Loaded at module initialization (can't be changed without restart)
- No GUI for rotation
- No encryption in environment variable

### 2.2 NameCheap Credentials

**File**: `/home/muut/Production/UC-Cloud/services/ops-center/.env.auth` (39-49)

```bash
# === NameCheap Migration (Epic 1.7) ===
NAMECHEAP_API_USERNAME=SkyBehind
NAMECHEAP_API_KEY=your-example-api-key
NAMECHEAP_USERNAME=SkyBehind
NAMECHEAP_CLIENT_IP=YOUR_SERVER_IP
NAMECHEAP_SANDBOX=false

# ⚠️ SECURITY WARNING: Current API credentials are exposed
# TODO: User will rotate credentials in separate session
```

**⚠️ SAME SECURITY ISSUES AS CLOUDFLARE**

---

## 3. Current Frontend Implementation

### 3.1 BYOK API Keys Component

**File**: `/home/muut/Production/UC-Cloud/services/ops-center/src/pages/account/AccountAPIKeys.jsx` (17,000+ lines)

**Features Implemented**:
- List of configured API keys (masked display)
- Add/edit/delete key forms
- Provider selection dropdown
- Key validity testing
- Show/hide key toggle
- Tier restrictions (Starter+ only)

**Example Providers**:
```javascript
const providers = [
  { value: 'openai', label: 'OpenAI', placeholder: 'sk-...' },
  { value: 'anthropic', label: 'Anthropic', placeholder: 'sk-ant-...' },
  { value: 'huggingface', label: 'HuggingFace', placeholder: 'hf_...' },
  { value: 'cohere', label: 'Cohere', placeholder: 'co-...' },
  { value: 'replicate', label: 'Replicate', placeholder: 'r8_...' },
  { value: 'custom', label: 'Custom Endpoint', placeholder: 'API Key' }
];
```

**API Endpoints Used**:
```javascript
// List API keys
GET /api/v1/auth/byok/keys
// Add new API key
POST /api/v1/auth/byok/keys
// Delete API key
DELETE /api/v1/auth/byok/keys/{key_id}
// Test API key
POST /api/v1/auth/byok/keys/{key_id}/test
```

### 3.2 APIKeyCard Component

**File**: `/home/muut/Production/UC-Cloud/services/ops-center/src/components/llm/APIKeyCard.jsx` (332 lines)

**Features**:
- Beautiful card UI with gradient background
- Provider-specific icons and colors
- Test result indicator
- Usage statistics display
- Enable/disable toggle
- Edit/delete actions

### 3.3 AddAPIKeyModal Component

**File**: `/home/muut/Production/UC-Cloud/services/ops-center/src/components/llm/AddAPIKeyModal.jsx` (partial, 80+ lines)

**Features**:
- Modal dialog with provider selection
- Key format validation
- Test button to validate before saving
- Custom endpoint support

---

## 4. Current API Endpoint Structure

### 4.1 BYOK Router Registration

**File**: `/home/muut/Production/UC-Cloud/services/ops-center/backend/server.py`

```python
# Line 63
from byok_api import router as byok_router

# Line 298
app.include_router(byok_router)

# Line 74
from cloudflare_api import router as cloudflare_router

# Line 342-343
app.include_router(cloudflare_router)
logger.info("Cloudflare DNS API endpoints registered at /api/v1/cloudflare")
```

**Registered Routers**:
1. `byok_router` - `/api/v1/byok/*` endpoints
2. `cloudflare_router` - `/api/v1/cloudflare/*` endpoints

---

## 5. CRITICAL GAPS & MISSING IMPLEMENTATION

### 5.1 NO ADMIN GUI FOR SERVICE CREDENTIALS

**Current State**: Cloudflare and NameCheap credentials are:
- ✅ Loaded from environment
- ❌ NOT encrypted in environment variable
- ❌ NOT stored in database
- ❌ NOT manageable via GUI
- ❌ NOT rotatable without container restart
- ❌ NOT user-level (admin only)

**What's Missing**:
1. **Backend API Endpoints** for credential management:
   - `GET /api/v1/admin/credentials` - List all credentials
   - `POST /api/v1/admin/credentials` - Add/update credential
   - `DELETE /api/v1/admin/credentials/{id}` - Delete credential
   - `GET /api/v1/admin/credentials/{id}/test` - Test credential
   - Tier restrictions (admin only)

2. **Database Schema** for service credentials:
   ```sql
   CREATE TABLE service_credentials (
     id SERIAL PRIMARY KEY,
     user_id VARCHAR(255),  -- NULL for system-level
     service VARCHAR(100) NOT NULL,  -- cloudflare, namecheap, etc.
     credential_type VARCHAR(100) NOT NULL,  -- api_token, api_key, etc.
     encrypted_value TEXT NOT NULL,
     is_system_level BOOLEAN DEFAULT FALSE,
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     last_used TIMESTAMP,
     test_status VARCHAR(50),
     UNIQUE(user_id, service, credential_type) -- or service, credential_type for system
   );
   ```

3. **Frontend Admin Panel** for credential management:
   - `/admin/system/credentials` page
   - List of all configured credentials
   - Add/edit/delete forms
   - Test credential buttons
   - Rotation instructions
   - Permission checks (admin only)

4. **Encryption for Environment Credentials**:
   - Migrate Cloudflare/NameCheap from `.env.auth` to database
   - Use existing `secret_manager.py` infrastructure
   - Keep initial values in environment for bootstrap

### 5.2 MISSING INTEGRATION POINTS

**With Cloudflare API** (`backend/cloudflare_api.py`):
- Credentials hardcoded from environment (line 47)
- No way to use multiple credentials
- No rotation without restart

**With NameCheap Integration** (if exists):
- ❓ File not found in exploration, but referenced in `.env.auth`
- Likely has same issues as Cloudflare

---

## 6. RECOMMENDED ARCHITECTURE

### 6.1 Storage Hierarchy

```
┌─────────────────────────────────────────────────┐
│          Service Credentials                     │
├─────────────────────────────────────────────────┤
│  1. Cloudflare (Epic 1.6)                       │
│     - Admin-managed (system-level)              │
│     - Shared across all users                   │
│     - Stored: PostgreSQL (encrypted)            │
│                                                  │
│  2. NameCheap (Epic 1.7)                        │
│     - Admin-managed (system-level)              │
│     - Shared across all users                   │
│     - Stored: PostgreSQL (encrypted)            │
│                                                  │
│  3. BYOK Keys (Current - User-level)            │
│     - User-managed                              │
│     - Per-user LLM providers                    │
│     - Stored: Keycloak user attributes          │
│                                                  │
│  4. System Defaults (Fallback)                  │
│     - Environment variables                     │
│     - Only for bootstrap/emergency              │
│     - NOT recommended for production            │
└─────────────────────────────────────────────────┘
```

### 6.2 Encryption Strategy

Use existing `secret_manager.py`:

```python
# For Cloudflare credential
from secret_manager import get_secret_manager

manager = get_secret_manager()

# Encrypt on store
encrypted = manager.encrypt_secret(
    secret=api_token,
    secret_type=SecretType.CLOUDFLARE_API_TOKEN,
    metadata={"service": "cloudflare", "account_id": "..."}
)

# Decrypt on use
decrypted = manager.decrypt_secret(encrypted["encrypted_value"])

# Mask for display
masked = manager.mask_secret(api_token)  # "0LVXYAz...iogQCmsegC_"
```

---

## 7. IMPLEMENTATION ROADMAP

### Phase 1: Backend Credential Storage (1-2 days)
1. Create `service_credentials_api.py` with CRUD endpoints
2. Add database table migration
3. Create credential manager class
4. Migrate Cloudflare/NameCheap from environment to database
5. Add Keycloak admin role check middleware
6. Implement encryption using `secret_manager.py`

### Phase 2: Admin UI (2-3 days)
1. Create `/admin/system/credentials` page
2. Add credential list with masking
3. Build add/edit forms with validation
4. Implement test button functionality
5. Add rotation workflow with instructions
6. Export/backup functionality

### Phase 3: Integration (1 day)
1. Update `cloudflare_api.py` to load from database
2. Create NameCheap manager and integrate
3. Add fallback to environment for backward compatibility
4. Testing and validation

### Phase 4: Documentation (1 day)
1. Admin guide for credential rotation
2. Security best practices
3. API documentation
4. Migration guide from environment

---

## 8. Key Files & Paths Summary

### Backend Files
| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `backend/key_encryption.py` | Encryption engine | 92 | ✅ Implemented |
| `backend/secret_manager.py` | Secret storage & rotation | 512 | ✅ Implemented |
| `backend/byok_service.py` | User BYOK service | 354 | ✅ Implemented |
| `backend/byok_manager.py` | BYOK database ops | 400 | ✅ Implemented |
| `backend/byok_api.py` | BYOK API endpoints | 512 | ✅ Implemented |
| `backend/cloudflare_api.py` | Cloudflare integration | 100+ | ⚠️ Partial (hardcoded creds) |
| `backend/cloudflare_manager.py` | Cloudflare client | ? | ⚠️ Likely hardcoded |
| `models/audit_log.py` | Audit logging | 189 | ✅ Implemented |
| `.env.auth` | Environment config | 56 | ⚠️ Exposed credentials |

### Frontend Files
| File | Purpose | Status |
|------|---------|--------|
| `src/pages/account/AccountAPIKeys.jsx` | BYOK key management | ✅ Implemented |
| `src/components/llm/APIKeyCard.jsx` | API key card display | ✅ Implemented |
| `src/components/llm/AddAPIKeyModal.jsx` | Add API key modal | ✅ Implemented |
| `/admin/system/credentials` | Admin credential panel | ❌ Missing |

---

## 9. Security Considerations

### Current Weaknesses
1. **Cloudflare/NameCheap in .env** - Exposed in git history and env vars
2. **No database encryption** - Environment variables not encrypted
3. **No credential rotation** - Requires container restart
4. **No audit logging** - Can't track who accessed/changed credentials
5. **No backup strategy** - Lost if database fails

### Recommended Improvements
1. **Move to PostgreSQL** with Fernet encryption
2. **Add rotation capability** without restart
3. **Implement audit logging** using existing `audit_logger.py`
4. **Add backup/restore** functionality
5. **Implement access logging** to track credential usage
6. **Add credential testing** before commit
7. **Keycloak-only rotation** - admins only

---

## 10. Code Examples

### Example: Using Encrypted Credentials

```python
# In cloudflare_api.py (FUTURE - with database)

from secret_manager import get_secret_manager
import asyncpg

async def get_cloudflare_token(db_pool: asyncpg.Pool) -> str:
    """Get Cloudflare API token from database"""
    manager = get_secret_manager()
    
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT encrypted_value FROM service_credentials
            WHERE service = 'cloudflare' AND credential_type = 'api_token'
            ORDER BY created_at DESC LIMIT 1
            """
        )
    
    if not result:
        # Fallback to environment for bootstrap
        import os
        token = os.getenv("CLOUDFLARE_API_TOKEN")
        if not token:
            raise ValueError("Cloudflare API token not configured")
        return token
    
    # Decrypt and return
    return manager.decrypt_secret(result['encrypted_value'])
```

### Example: API Endpoint

```python
# service_credentials_api.py (NEW)

from fastapi import APIRouter, HTTPException, Depends
from admin_subscriptions_api import require_admin
from secret_manager import get_secret_manager, SecretType

router = APIRouter(prefix="/api/v1/admin/credentials", tags=["admin", "credentials"])

@router.post("/")
@require_admin
async def store_credential(
    service: str,
    credential_type: str,
    secret: str,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Store encrypted service credential (admin only)"""
    manager = get_secret_manager()
    
    # Encrypt
    encrypted_data = manager.encrypt_secret(
        secret=secret,
        secret_type=f"{service}_{credential_type}",
        metadata={"service": service}
    )
    
    # Store in database
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO service_credentials
            (service, credential_type, encrypted_value, is_system_level)
            VALUES ($1, $2, $3, TRUE)
            ON CONFLICT (service, credential_type) 
            DO UPDATE SET encrypted_value = EXCLUDED.encrypted_value
            """,
            service, credential_type, encrypted_data["encrypted_value"]
        )
    
    return {
        "message": "Credential stored successfully",
        "service": service,
        "credential_type": credential_type,
        "masked_value": manager.mask_secret(secret)
    }
```

---

## Summary Table: Current vs. Needed

| Feature | Current | Status | Needed |
|---------|---------|--------|--------|
| Encryption | Fernet AES-128 | ✅ Yes | Already exists |
| Database Schema | `encrypted_credentials` table | ✅ Yes | For service creds |
| Service Creds GUI | None | ❌ No | AdminPanel page |
| API Endpoints | BYOK only | ⚠️ Partial | Service creds endpoints |
| Cloudflare Integration | .env hardcoded | ⚠️ Bad | Database + GUI |
| NameCheap Integration | .env hardcoded | ⚠️ Bad | Database + GUI |
| Rotation | Key rotation in code | ✅ Yes | Without restart |
| Audit Logging | Audit logger exists | ✅ Yes | Hook to secret ops |
| Testing Creds | BYOK has test | ✅ Yes | For service creds |
| Masking | Implemented | ✅ Yes | Reusable |

---

## Conclusion

The Ops-Center has an **excellent encryption and credential management foundation**. The infrastructure is in place and well-designed. We need to:

1. **Extend the BYOK system** to service-level credentials (Cloudflare, NameCheap)
2. **Add admin GUI** for credential management
3. **Move credentials from `.env.auth`** to encrypted database storage
4. **Implement rotation** without container restart
5. **Add comprehensive audit logging**

This is a **3-4 day implementation** with the existing infrastructure doing most of the heavy lifting.

