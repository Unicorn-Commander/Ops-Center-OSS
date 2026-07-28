"""
BYOK (Bring Your Own Key) API Router
Allows users to store and manage their own API keys for LLM providers
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import httpx
import os
from datetime import datetime
import logging

from key_encryption import get_encryption
from tier_middleware import require_tier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/byok", tags=["byok"])

# Access to sessions store (set by server.py when registering this router)
sessions = {}

def set_sessions_store(sessions_dict):
    """Set reference to server's sessions store"""
    global sessions
    sessions = sessions_dict

# Supported providers
SUPPORTED_PROVIDERS = {
    "openrouter": {
        "name": "OpenRouter",
        "test_url": "https://openrouter.ai/api/v1/models",
        "auth_type": "bearer",
        "key_format": "sk-or-v1-"
    },
    "openai": {
        "name": "OpenAI",
        "test_url": "https://api.openai.com/v1/models",
        "auth_type": "bearer",
        "key_format": "sk-"
    },
    "anthropic": {
        "name": "Anthropic",
        "test_url": "https://api.anthropic.com/v1/messages",
        "auth_type": "x-api-key",
        "key_format": "sk-ant-"
    },
    "huggingface": {
        "name": "HuggingFace",
        "test_url": "https://huggingface.co/api/whoami",
        "auth_type": "bearer",
        "key_format": "hf_"
    },
    "cohere": {
        "name": "Cohere",
        "test_url": "https://api.cohere.ai/v1/check-api-key",
        "auth_type": "bearer",
        "key_format": None
    },
    "together": {
        "name": "Together AI",
        "test_url": "https://api.together.xyz/v1/models",
        "auth_type": "bearer",
        "key_format": None
    },
    "perplexity": {
        "name": "Perplexity AI",
        "test_url": "https://api.perplexity.ai/chat/completions",
        "auth_type": "bearer",
        "key_format": "pplx-"
    },
    "groq": {
        "name": "Groq",
        "test_url": "https://api.groq.com/openai/v1/models",
        "auth_type": "bearer",
        "key_format": "gsk_"
    },
    "ollama": {
        "name": "Ollama",
        "test_url": "http://localhost:11434/api/tags",
        "auth_type": "none",
        "key_format": None
    },
    "ollama_cloud": {
        "name": "Ollama Cloud",
        "test_url": "https://ollama.com/api/tags",
        "auth_type": "bearer",
        "key_format": None
    },
    "custom": {
        "name": "Custom Endpoint",
        "test_url": None,
        "auth_type": "bearer",
        "key_format": None
    }
}

class APIKeyAdd(BaseModel):
    """Request to add/update an API key"""
    provider: str = Field(..., description="Provider name (openai, anthropic, huggingface, etc.)")
    key: str = Field(..., min_length=10, description="API key")
    label: Optional[str] = Field(None, max_length=100, description="Optional label for the key")
    endpoint: Optional[str] = Field(None, description="Custom endpoint URL (for custom provider)")

    @validator('provider')
    def validate_provider(cls, v):
        if v not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider. Must be one of: {', '.join(SUPPORTED_PROVIDERS.keys())}")
        return v

    @validator('key')
    def validate_key_format(cls, v, values):
        if 'provider' in values:
            provider = values['provider']
            provider_config = SUPPORTED_PROVIDERS.get(provider, {})
            key_format = provider_config.get('key_format')

            if key_format and not v.startswith(key_format):
                logger.warning(f"API key for {provider} doesn't match expected format {key_format}")

        return v

class APIKeyResponse(BaseModel):
    """Response with API key info (masked)"""
    provider: str
    provider_name: str
    key_preview: str
    label: Optional[str]
    added_date: str
    last_tested: Optional[str]
    test_status: Optional[str]

class APIKeyTestResult(BaseModel):
    """Result of API key test"""
    provider: str
    status: str  # "valid", "invalid", "error"
    message: str
    details: Optional[Dict[str, Any]] = None

class ProviderInfo(BaseModel):
    """Information about a supported provider"""
    id: str
    name: str
    key_format: Optional[str]
    configured: bool

# Helper functions

async def get_user_email(request: Request) -> str:
    """Extract user email from session using session_token cookie"""
    session_token = request.cookies.get("session_token")

    if not session_token or session_token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = sessions[session_token]
    user_data = session.get("user", {})

    email = user_data.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="User email not found in session")

    return email

async def get_user_from_keycloak(email: str) -> Optional[Dict[str, Any]]:
    """Fetch user data from Keycloak"""
    from keycloak_integration import get_user_by_email as kc_get_user

    try:
        user = await kc_get_user(email)
        if not user:
            logger.warning(f"User not found in Keycloak: {email}")
        return user
    except Exception as e:
        logger.error(f"Error fetching user from Keycloak: {e}")
        raise HTTPException(status_code=500, detail="Failed to communicate with authentication service")

async def update_user_attributes_keycloak(email: str, attributes: Dict[str, Any]) -> bool:
    """Update user attributes in Keycloak"""
    from keycloak_integration import update_user_attributes as kc_update_attrs

    try:
        # Keycloak expects attributes as arrays, convert if needed
        kc_attributes = {}
        for key, value in attributes.items():
            if isinstance(value, list):
                kc_attributes[key] = value
            else:
                kc_attributes[key] = [str(value)]

        success = await kc_update_attrs(email, kc_attributes)
        return success

    except Exception as e:
        logger.error(f"Error updating user attributes in Keycloak: {e}")
        return False

async def test_api_key(provider: str, api_key: str, endpoint: Optional[str] = None) -> APIKeyTestResult:
    """Test if an API key is valid"""
    provider_config = SUPPORTED_PROVIDERS.get(provider)

    if not provider_config:
        return APIKeyTestResult(
            provider=provider,
            status="error",
            message="Unknown provider"
        )

    test_url = endpoint if provider == "custom" and endpoint else provider_config.get("test_url")

    if not test_url:
        return APIKeyTestResult(
            provider=provider,
            status="unknown",
            message="No test endpoint available for this provider"
        )

    auth_type = provider_config.get("auth_type", "bearer")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            headers = {}

            if auth_type == "bearer":
                headers["Authorization"] = f"Bearer {api_key}"
            elif auth_type == "x-api-key":
                headers["x-api-key"] = api_key
                headers["anthropic-version"] = "2023-06-01"
            elif auth_type == "none":
                # Ollama local doesn't require authentication
                pass

            # Special handling for different providers
            if provider == "anthropic":
                # Anthropic needs a POST with minimal payload
                response = await client.post(
                    test_url,
                    headers=headers,
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "test"}]
                    }
                )
                # Any response that's not 401/403 means the key is valid
                is_valid = response.status_code not in [401, 403]
            else:
                response = await client.get(test_url, headers=headers)
                is_valid = response.status_code in [200, 201]

            if is_valid:
                return APIKeyTestResult(
                    provider=provider,
                    status="valid",
                    message="API key is valid and working",
                    details={"status_code": response.status_code}
                )
            else:
                return APIKeyTestResult(
                    provider=provider,
                    status="invalid",
                    message=f"API key validation failed (HTTP {response.status_code})",
                    details={"status_code": response.status_code}
                )

    except httpx.TimeoutException:
        return APIKeyTestResult(
            provider=provider,
            status="error",
            message="Request timeout - provider may be unreachable"
        )
    except Exception as e:
        logger.error(f"Error testing {provider} key: {e}")
        return APIKeyTestResult(
            provider=provider,
            status="error",
            message=f"Test failed: {str(e)}"
        )

# API Endpoints

@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers(request: Request):
    """Get list of supported providers"""
    try:
        user_email = await get_user_email(request)
        user = await get_user_from_keycloak(user_email)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        attributes = user.get("attributes", {})

        providers = []
        for provider_id, config in SUPPORTED_PROVIDERS.items():
            # Keycloak stores attributes as arrays
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

@router.get("/keys", response_model=List[APIKeyResponse])
async def list_keys(request: Request):
    """List user's configured API keys (masked)"""
    try:
        user_email = await get_user_email(request)
        user = await get_user_from_keycloak(user_email)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user.get("id")
        if not user_id:
            raise HTTPException(status_code=404, detail="User ID not found")

        encryption = get_encryption()
        keys = []

        # Query database for BYOK keys
        import asyncpg

        # Get database pool from app state
        db_pool = request.app.state.db_pool
        if not db_pool:
            logger.warning("Database connection not available, BYOK keys cannot be retrieved")
            return []

        try:
            # Get connection from pool
            async with db_pool.acquire() as conn:
                # Fetch user provider keys from database
                db_keys = await conn.fetch("""
                    SELECT provider, api_key_encrypted, metadata, enabled, created_at, updated_at
                    FROM user_provider_keys
                    WHERE user_id = $1 AND enabled = true
                """, user_id)

            # Process database keys
            for row in db_keys:
                provider_id = row['provider']

                # Only show supported providers
                if provider_id not in SUPPORTED_PROVIDERS:
                    continue

                try:
                    # Decrypt to mask properly
                    decrypted = encryption.decrypt_key(row['api_key_encrypted'])
                    key_preview = encryption.mask_key(decrypted)
                except Exception as e:
                    logger.error(f"Error decrypting key for {provider_id}: {e}")
                    key_preview = "***error***"

                # Parse metadata JSON string to dict
                import json
                metadata_raw = row.get('metadata')
                if isinstance(metadata_raw, str):
                    try:
                        metadata = json.loads(metadata_raw)
                    except:
                        metadata = {}
                else:
                    metadata = metadata_raw or {}

                keys.append(APIKeyResponse(
                    provider=provider_id,
                    provider_name=SUPPORTED_PROVIDERS[provider_id]["name"],
                    key_preview=key_preview,
                    label=metadata.get('name'),
                    added_date=row['created_at'].isoformat() if row['created_at'] else "Unknown",
                    last_tested=metadata.get('last_tested'),
                    test_status=metadata.get('test_status')
                ))

        except Exception as e:
            logger.error(f"Error querying database for BYOK keys: {e}")
            # Fall back to Keycloak attributes for backward compatibility
            attributes = user.get("attributes", {})

            def get_attr(key, default=None):
                val = attributes.get(key, [default])
                return val[0] if isinstance(val, list) and val else default

            for provider_id in SUPPORTED_PROVIDERS.keys():
                encrypted_key = get_attr(f"byok_{provider_id}_key")

                if encrypted_key:
                    try:
                        decrypted = encryption.decrypt_key(encrypted_key)
                        key_preview = encryption.mask_key(decrypted)
                    except Exception as e:
                        logger.error(f"Error decrypting key for {provider_id}: {e}")
                        key_preview = "***error***"

                    keys.append(APIKeyResponse(
                        provider=provider_id,
                        provider_name=SUPPORTED_PROVIDERS[provider_id]["name"],
                        key_preview=key_preview,
                        label=get_attr(f"byok_{provider_id}_label"),
                        added_date=get_attr(f"byok_{provider_id}_added_date", "Unknown"),
                        last_tested=get_attr(f"byok_{provider_id}_last_tested"),
                        test_status=get_attr(f"byok_{provider_id}_test_status")
                    ))

        return keys

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")

@router.post("/keys/add")
# @require_tier(["starter", "professional", "enterprise"])  # Disabled: Flask decorator incompatible with FastAPI
async def add_key(key_data: APIKeyAdd, request: Request):
    """Add or update an API key (stores in PostgreSQL database)"""
    try:
        user_email = await get_user_email(request)
        user = await get_user_from_keycloak(user_email)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user.get("id")
        if not user_id:
            raise HTTPException(status_code=404, detail="User ID not found")

        # Encrypt the key
        encryption = get_encryption()
        encrypted_key = encryption.encrypt_key(key_data.key)

        # Build metadata JSON
        metadata = {
            "name": key_data.label or f"{SUPPORTED_PROVIDERS[key_data.provider]['name']} Key",
            "added_date": datetime.utcnow().isoformat()
        }

        if key_data.endpoint:
            metadata["endpoint"] = key_data.endpoint

        # Store in PostgreSQL database
        import asyncpg
        import json

        # Get database pool from app state
        db_pool = request.app.state.db_pool
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database connection not available")

        try:
            # Get connection from pool
            async with db_pool.acquire() as conn:
                # Upsert: Insert or update if exists
                await conn.execute("""
                    INSERT INTO user_provider_keys (
                        user_id, provider, api_key_encrypted, metadata, enabled,
                        created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4::jsonb, true, NOW(), NOW())
                    ON CONFLICT (user_id, provider)
                    DO UPDATE SET
                        api_key_encrypted = EXCLUDED.api_key_encrypted,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                """, user_id, key_data.provider, encrypted_key, json.dumps(metadata))

            logger.info(f"Added BYOK key for {user_email} (user_id: {user_id}): {key_data.provider}")

            return {
                "message": "API key added successfully",
                "provider": key_data.provider,
                "provider_name": SUPPORTED_PROVIDERS[key_data.provider]["name"]
            }

        except Exception as e:
            logger.error(f"Database error adding key: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to store API key in database: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add API key: {str(e)}")

@router.delete("/keys/{provider}")
async def delete_key(provider: str, request: Request):
    """Remove an API key"""
    try:
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(status_code=400, detail="Invalid provider")

        user_email = await get_user_email(request)
        user = await get_user_from_keycloak(user_email)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Import Keycloak delete function
        from keycloak_integration import update_user_attributes as kc_update_attrs

        # Get current attributes
        attributes = user.get("attributes", {})

        # Remove all related attributes
        attributes.pop(f"byok_{provider}_key", None)
        attributes.pop(f"byok_{provider}_label", None)
        attributes.pop(f"byok_{provider}_added_date", None)
        attributes.pop(f"byok_{provider}_endpoint", None)
        attributes.pop(f"byok_{provider}_last_tested", None)
        attributes.pop(f"byok_{provider}_test_status", None)

        # Update user with cleaned attributes
        success = await kc_update_attrs(user_email, attributes)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to remove API key")

        logger.info(f"Removed BYOK key for {user_email}: {provider}")

        return {"message": "API key removed successfully", "provider": provider}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting key: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove API key")

@router.post("/keys/test/{provider}", response_model=APIKeyTestResult)
async def test_key(provider: str, request: Request):
    """Test if an API key is valid (reads from PostgreSQL database)"""
    try:
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(status_code=400, detail="Invalid provider")

        user_email = await get_user_email(request)
        user = await get_user_from_keycloak(user_email)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user.get("id")
        if not user_id:
            raise HTTPException(status_code=404, detail="User ID not found")

        # Get key from database
        import asyncpg
        import json

        db_pool = request.app.state.db_pool
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database connection not available")

        encrypted_key = None
        endpoint = None

        async with db_pool.acquire() as conn:
            # Fetch the specific provider key
            row = await conn.fetchrow("""
                SELECT api_key_encrypted, metadata
                FROM user_provider_keys
                WHERE user_id = $1 AND provider = $2 AND enabled = true
            """, user_id, provider)

            if not row:
                raise HTTPException(status_code=404, detail="API key not found for this provider")

            encrypted_key = row['api_key_encrypted']

            # Parse metadata for endpoint
            metadata_raw = row.get('metadata')
            if isinstance(metadata_raw, str):
                try:
                    metadata = json.loads(metadata_raw)
                    endpoint = metadata.get('endpoint')
                except:
                    pass

        # Decrypt key
        encryption = get_encryption()
        api_key = encryption.decrypt_key(encrypted_key)

        # Test the key
        result = await test_api_key(provider, api_key, endpoint)

        # Update test results in database
        async with db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE user_provider_keys
                SET metadata = jsonb_set(
                    jsonb_set(
                        COALESCE(metadata::jsonb, '{}'::jsonb),
                        '{last_tested}', $3::jsonb
                    ),
                    '{test_status}', $4::jsonb
                ),
                updated_at = NOW()
                WHERE user_id = $1 AND provider = $2
            """, user_id, provider, json.dumps(datetime.utcnow().isoformat()), json.dumps(result.status))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing key: {e}")
        raise HTTPException(status_code=500, detail="Failed to test API key")

@router.get("/stats")
async def get_byok_stats(request: Request):
    """Get statistics about user's BYOK configuration (from PostgreSQL database)"""
    try:
        user_email = await get_user_email(request)
        user = await get_user_from_keycloak(user_email)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user.get("id")
        if not user_id:
            raise HTTPException(status_code=404, detail="User ID not found")

        configured_count = 0
        tested_count = 0
        valid_count = 0

        # Query database for stats
        import asyncpg

        db_pool = request.app.state.db_pool
        if db_pool:
            try:
                async with db_pool.acquire() as conn:
                    # Count configured providers
                    db_keys = await conn.fetch("""
                        SELECT provider, metadata
                        FROM user_provider_keys
                        WHERE user_id = $1 AND enabled = true
                    """, user_id)

                    configured_count = len(db_keys)

                    # Count tested and valid providers
                    for row in db_keys:
                        # Parse metadata JSON string to dict
                        import json
                        metadata_raw = row.get('metadata')
                        if isinstance(metadata_raw, str):
                            try:
                                metadata = json.loads(metadata_raw)
                            except:
                                metadata = {}
                        else:
                            metadata = metadata_raw or {}

                        if metadata.get('last_tested'):
                            tested_count += 1
                        if metadata.get('test_status') == 'valid':
                            valid_count += 1

            except Exception as e:
                logger.error(f"Error getting BYOK stats: {e}")

        return {
            "total_providers": len(SUPPORTED_PROVIDERS),
            "configured_providers": configured_count,
            "tested_providers": tested_count,
            "valid_providers": valid_count,
            "user_tier": request.state.tier if hasattr(request.state, "tier") else "unknown"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")
