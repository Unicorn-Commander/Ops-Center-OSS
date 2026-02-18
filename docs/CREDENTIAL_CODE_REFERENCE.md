# Ops-Center Credential Management - Code Reference & Snippets

---

## File Locations (Absolute Paths)

### Backend Core Files
```
/opt/ops-center/backend/key_encryption.py
/opt/ops-center/backend/secret_manager.py
/opt/ops-center/backend/byok_service.py
/opt/ops-center/backend/byok_manager.py
/opt/ops-center/backend/byok_api.py
/opt/ops-center/backend/cloudflare_api.py
/opt/ops-center/backend/server.py
```

### Frontend Components
```
/opt/ops-center/src/pages/account/AccountAPIKeys.jsx
/opt/ops-center/src/components/llm/APIKeyCard.jsx
/opt/ops-center/src/components/llm/AddAPIKeyModal.jsx
```

### Configuration
```
/opt/ops-center/.env.auth
/opt/ops-center/docker-compose.direct.yml
```

---

## Key Code Snippets

### 1. Encryption Usage (key_encryption.py)

```python
# Line 10-25: Class initialization
class KeyEncryption:
    def __init__(self):
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError(
                "ENCRYPTION_KEY environment variable not set. "
                "Generate one with: python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        
        try:
            self.cipher = Fernet(encryption_key.encode())
        except Exception as e:
            raise ValueError(f"Invalid ENCRYPTION_KEY format: {e}")

# Line 27-44: Encryption method
def encrypt_key(self, api_key: str) -> str:
    if not api_key:
        raise ValueError("API key cannot be empty")
    
    try:
        encrypted = self.cipher.encrypt(api_key.encode())
        return encrypted.decode()
    except Exception as e:
        raise ValueError(f"Encryption failed: {e}")

# Line 46-63: Decryption method
def decrypt_key(self, encrypted_key: str) -> str:
    if not encrypted_key:
        raise ValueError("Encrypted key cannot be empty")
    
    try:
        decrypted = self.cipher.decrypt(encrypted_key.encode())
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")

# Line 65-79: Masking method
def mask_key(self, api_key: str, visible_chars: int = 4) -> str:
    if not api_key or len(api_key) < visible_chars * 2:
        return "****"
    
    return f"{api_key[:visible_chars]}...{api_key[-visible_chars:]}"

# Line 86-91: Singleton pattern
_encryption_instance: Optional[KeyEncryption] = None

def get_encryption() -> KeyEncryption:
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = KeyEncryption()
    return _encryption_instance
```

### 2. Secret Manager Storage (secret_manager.py)

```python
# Lines 106-143: Encrypt and store
def encrypt_secret(
    self,
    secret: str,
    secret_type: str = SecretType.GENERIC,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    try:
        encrypted = self.encryption.encrypt_key(secret)
        result = {
            "encrypted_value": encrypted,
            "secret_type": secret_type,
            "encrypted_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        logger.info(f"Secret encrypted successfully (type: {secret_type})")
        return result
    except Exception as e:
        logger.error(f"Failed to encrypt secret: {e}")
        raise EncryptionError(f"Encryption failed: {e}")

# Lines 184-255: Database storage
def store_encrypted_credential(
    self,
    user_id: str,
    service: str,
    credential_type: str,
    secret: str,
    db_connection
) -> Dict[str, Any]:
    try:
        encrypted_data = self.encrypt_secret(
            secret=secret,
            secret_type=credential_type,
            metadata={"user_id": user_id, "service": service}
        )
        
        cursor = db_connection.cursor()
        cursor.execute(
            """
            INSERT INTO encrypted_credentials
            (user_id, service, credential_type, encrypted_value, encrypted_at, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
            """,
            (
                user_id,
                service,
                credential_type,
                encrypted_data["encrypted_value"],
                encrypted_data["encrypted_at"],
                str(encrypted_data["metadata"])
            )
        )
        
        result = cursor.fetchone()
        db_connection.commit()
        
        logger.info(
            f"Credential stored: user={user_id}, service={service}, type={credential_type}"
        )
        
        return {
            "id": result[0],
            "user_id": user_id,
            "service": service,
            "credential_type": credential_type,
            "created_at": result[1].isoformat(),
            "masked_value": self.mask_secret(secret)
        }
    except Exception as e:
        db_connection.rollback()
        logger.error(f"Failed to store credential: {e}")
        raise
```

### 3. BYOK API Router (byok_api.py)

```python
# Lines 244-275: List providers
@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers(request: Request):
    try:
        user_email = await get_user_email(request)
        user = await get_user_from_keycloak(user_email)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        attributes = user.get("attributes", {})
        
        providers = []
        for provider_id, config in SUPPORTED_PROVIDERS.items():
            attr_key = f"byok_{provider_id}_key"
            configured = attr_key in attributes and len(attributes.get(attr_key, [])) > 0
            
            providers.append(ProviderInfo(
                id=provider_id,
                name=config["name"],
                key_format=config.get("key_format"),
                configured=configured
            ))
        
        return providers
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing providers: {e}")
        raise HTTPException(status_code=500, detail="Failed to list providers")

# Lines 326-371: Add API key
@router.post("/keys/add")
@require_tier(["starter", "professional", "enterprise"])
async def add_key(key_data: APIKeyAdd, request: Request):
    try:
        user_email = await get_user_email(request)
        user = await get_user_from_keycloak(user_email)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        encryption = get_encryption()
        encrypted_key = encryption.encrypt_key(key_data.key)
        
        attributes = {
            f"byok_{key_data.provider}_key": [encrypted_key],
            f"byok_{key_data.provider}_added_date": [datetime.utcnow().isoformat()]
        }
        
        if key_data.label:
            attributes[f"byok_{key_data.provider}_label"] = [key_data.label]
        
        if key_data.endpoint:
            attributes[f"byok_{key_data.provider}_endpoint"] = [key_data.endpoint]
        
        success = await update_user_attributes_keycloak(user_email, attributes)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to store API key")
        
        logger.info(f"Added BYOK key for {user_email}: {key_data.provider}")
        
        return {
            "message": "API key added successfully",
            "provider": key_data.provider,
            "provider_name": SUPPORTED_PROVIDERS[key_data.provider]["name"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add API key: {str(e)}")

# Lines 416-463: Test API key
@router.post("/keys/test/{provider}", response_model=APIKeyTestResult)
async def test_key(provider: str, request: Request):
    try:
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(status_code=400, detail="Invalid provider")
        
        user_email = await get_user_email(request)
        user = await get_user_from_keycloak(user_email)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        attributes = user.get("attributes", {})
        
        def get_attr(key, default=None):
            val = attributes.get(key, [default])
            return val[0] if isinstance(val, list) and val else default
        
        encrypted_key = get_attr(f"byok_{provider}_key")
        if not encrypted_key:
            raise HTTPException(status_code=404, detail="API key not found for this provider")
        
        encryption = get_encryption()
        api_key = encryption.decrypt_key(encrypted_key)
        endpoint = get_attr(f"byok_{provider}_endpoint")
        
        result = await test_api_key(provider, api_key, endpoint)
        
        test_attrs = {
            f"byok_{provider}_last_tested": [datetime.utcnow().isoformat()],
            f"byok_{provider}_test_status": [result.status]
        }
        await update_user_attributes_keycloak(user_email, test_attrs)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing key: {e}")
        raise HTTPException(status_code=500, detail="Failed to test API key")
```

### 4. Cloudflare Integration (cloudflare_api.py)

```python
# Lines 46-48: Current implementation (HARDCODED)
import os
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
cloudflare_manager = CloudflareManager(api_token=CLOUDFLARE_API_TOKEN) if CLOUDFLARE_API_TOKEN else None

# Lines 53-87: Zone creation endpoint
@router.post("/zones", response_model=ZoneResponse, status_code=201)
@require_admin
async def create_zone(
    zone_data: ZoneCreateRequest,
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Create a new Cloudflare zone (admin only)"""
    
    if not cloudflare_manager:
        raise HTTPException(
            status_code=503,
            detail="Cloudflare API is not configured"
        )
    
    try:
        # Rate limiting
        await check_rate_limit_manual(
            request,
            category="cloudflare",
            limit=10,
            period=3600
        )
        
        # Create zone
        zone = await cloudflare_manager.create_zone(
            domain=zone_data.domain,
            account_id=zone_data.account_id,
            jump_start=zone_data.jump_start
        )
        
        # Audit log
        await audit_logger.log(
            user_id=request.state.user_id,
            action=AuditAction.NETWORK_CONFIGURE,
            resource_type="cloudflare_zone",
            resource_id=zone["id"],
            result=AuditResult.SUCCESS,
            metadata={"domain": zone_data.domain, "zone_id": zone["id"]}
        )
        
        return ZoneResponse(**zone)
    
    except CloudflareAuthError:
        raise HTTPException(status_code=401, detail="Cloudflare authentication failed")
    except CloudflareRateLimitError:
        raise HTTPException(status_code=429, detail="Cloudflare API rate limit exceeded")
    except CloudflareError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating zone: {e}")
        raise HTTPException(status_code=500, detail="Failed to create zone")
```

### 5. Frontend BYOK Component (AccountAPIKeys.jsx)

```javascript
// Lines 97-131: Load API keys
const loadAPIKeys = async () => {
  try {
    const response = await fetch('/api/v1/auth/byok/keys');
    if (response.ok) {
      const data = await response.json();
      setApiKeys(data.keys || []);
    }
  } catch (error) {
    console.error('Failed to load API keys:', error);
    setApiKeys([
      {
        id: '1',
        provider: 'openai',
        name: 'OpenAI Production',
        apiKey: 'sk-proj-abc123def456ghi789',
        description: 'Primary OpenAI key for production',
        createdAt: '2024-10-01',
        lastUsed: '2 hours ago',
        status: 'active'
      }
    ]);
  } finally {
    setLoading(false);
  }
};

// Lines 143-180: Add new API key
const handleAddKey = async (e) => {
  e.preventDefault();
  
  try {
    const response = await fetch('/api/v1/auth/byok/keys', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        provider: keyForm.provider,
        key: keyForm.apiKey,
        label: keyForm.name,
        description: keyForm.description
      })
    });
    
    if (response.ok) {
      setMessage({
        type: 'success',
        text: 'API key added successfully'
      });
      setShowAddModal(false);
      setKeyForm({
        provider: 'openai',
        name: '',
        apiKey: '',
        description: ''
      });
      loadAPIKeys();
    } else {
      const error = await response.json();
      setMessage({
        type: 'error',
        text: error.detail || 'Failed to add API key'
      });
    }
  } catch (error) {
    console.error('Error adding key:', error);
    setMessage({
      type: 'error',
      text: 'Failed to add API key'
    });
  }
};

// Lines 200+: Test API key
const handleTestKey = async (keyId) => {
  setTestingKey(keyId);
  try {
    const response = await fetch(`/api/v1/auth/byok/keys/test/${keyId}`, {
      method: 'POST'
    });
    
    if (response.ok) {
      const result = await response.json();
      return {
        success: result.status === 'valid',
        message: result.message
      };
    } else {
      return {
        success: false,
        error: 'Test failed'
      };
    }
  } catch (error) {
    console.error('Error testing key:', error);
    return {
      success: false,
      error: error.message
    };
  } finally {
    setTestingKey(null);
  }
};
```

---

## Database Schema

### Encrypted Credentials Table (from secret_manager.py, lines 397-413)

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

### Proposed Service Credentials Table (NEW)

```sql
CREATE TABLE IF NOT EXISTS service_credentials (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    service VARCHAR(100) NOT NULL,
    credential_type VARCHAR(100) NOT NULL,
    encrypted_value TEXT NOT NULL,
    is_system_level BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    test_status VARCHAR(50),
    test_message TEXT,
    UNIQUE(CASE WHEN user_id IS NULL THEN service ELSE user_id END, 
           service, credential_type)
);

CREATE INDEX idx_service_credentials_service ON service_credentials(service);
CREATE INDEX idx_service_credentials_system ON service_credentials(is_system_level);
CREATE INDEX idx_service_credentials_updated ON service_credentials(updated_at);
```

---

## Environment Variables

### Current (.env.auth)

```bash
# Lines 4-27: Cloudflare configuration
CLOUDFLARE_API_TOKEN=<CLOUDFLARE_API_TOKEN_REDACTED>
CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_API_BASE_URL=https://api.cloudflare.com/client/v4

# Lines 30-38: NameCheap configuration
NAMECHEAP_API_USERNAME=your-namecheap-username
NAMECHEAP_API_KEY=your-namecheap-api-key
NAMECHEAP_USERNAME=your-namecheap-username
NAMECHEAP_CLIENT_IP=your-server-ip
NAMECHEAP_SANDBOX=false

# Needed for encryption (usually set in docker-compose)
ENCRYPTION_KEY=<base64-encoded-fernet-key>
```

---

## API Request/Response Examples

### List Providers (BYOK)

```bash
# Request
GET /api/v1/byok/providers
Authorization: Bearer <jwt-token>

# Response
[
  {
    "id": "openai",
    "name": "OpenAI",
    "key_format": "sk-",
    "configured": true
  },
  {
    "id": "anthropic",
    "name": "Anthropic",
    "key_format": "sk-ant-",
    "configured": false
  },
  ...
]
```

### Add API Key (BYOK)

```bash
# Request
POST /api/v1/byok/keys/add
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
  "provider": "openai",
  "key": "sk-proj-...",
  "label": "Production OpenAI Key",
  "endpoint": null
}

# Response
{
  "message": "API key added successfully",
  "provider": "openai",
  "provider_name": "OpenAI"
}
```

### Test API Key (BYOK)

```bash
# Request
POST /api/v1/byok/keys/test/openai
Authorization: Bearer <jwt-token>

# Response - Success
{
  "provider": "openai",
  "status": "valid",
  "message": "API key is valid and working",
  "details": {
    "status_code": 200
  }
}

# Response - Failed
{
  "provider": "openai",
  "status": "invalid",
  "message": "API key validation failed (HTTP 401)",
  "details": {
    "status_code": 401
  }
}
```

### Create Zone (Cloudflare - requires admin)

```bash
# Request
POST /api/v1/cloudflare/zones
Authorization: Bearer <admin-jwt-token>
Content-Type: application/json

{
  "domain": "example.com",
  "account_id": null,
  "jump_start": true,
  "priority": "normal"
}

# Response
{
  "id": "c029d2ce45c12046e50bac63b249179a",
  "name": "example.com",
  "status": "active",
  "type": "full",
  "plan": {
    "id": "0feeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "name": "Free",
    "price": 0,
    "currency": "USD",
    "frequency": "monthly",
    "legacy_id": "free",
    "legacy_discount": false,
    "externally_managed": false
  },
  "created_on": "2014-01-02T00:01:13.123456Z",
  "modified_on": "2014-01-02T00:01:13.123456Z",
  "account": {
    "id": "372e67954025e0ba6aaa6d586b9e0b59",
    "name": "Example Account"
  },
  "verification_key": "aee3b0e9c4ef0b03adf6"
}
```

---

## Integration Points

### How Cloudflare Uses Token (Currently)

```python
# backend/cloudflare_api.py, lines 20-48
from cloudflare_manager import CloudflareManager
import os

CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
cloudflare_manager = CloudflareManager(api_token=CLOUDFLARE_API_TOKEN) if CLOUDFLARE_API_TOKEN else None

# Then used in any endpoint that needs to call Cloudflare API:
# cloudflare_manager.create_zone(...)
# cloudflare_manager.list_zones(...)
# etc.
```

### How to Make It Database-Driven (Proposed)

```python
# backend/service_credentials_api.py (NEW)

from secret_manager import get_secret_manager
import asyncpg

async def get_service_credential(
    db_pool: asyncpg.Pool,
    service: str,
    credential_type: str
) -> Optional[str]:
    """Get and decrypt a service credential"""
    manager = get_secret_manager()
    
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT encrypted_value FROM service_credentials
            WHERE service = $1 AND credential_type = $2 
            AND is_system_level = TRUE
            ORDER BY updated_at DESC LIMIT 1
            """,
            service, credential_type
        )
    
    if not result:
        # Fallback to environment for backward compatibility
        env_var = f"{service.upper()}_{credential_type.upper()}"
        import os
        token = os.getenv(env_var)
        if token:
            logger.warning(f"Using {env_var} from environment (not recommended)")
        return token
    
    return manager.decrypt_secret(result['encrypted_value'])

# Then in cloudflare_api.py:
@router.post("/zones")
@require_admin
async def create_zone(
    zone_data: ZoneCreateRequest,
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    # Get token from database instead of environment
    api_token = await get_service_credential(
        db_pool, 
        "cloudflare", 
        "api_token"
    )
    
    if not api_token:
        raise HTTPException(status_code=503, detail="Cloudflare API is not configured")
    
    cloudflare_manager = CloudflareManager(api_token=api_token)
    # ... rest of endpoint
```

