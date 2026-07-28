"""
Provider Keys API - System-level Provider Key Management

This module provides admin-only endpoints for managing system provider API keys.
Used by the LLM Hub frontend to configure OpenRouter, OpenAI, Anthropic, Google, etc.

Features:
- List all provider keys with masked values
- Add/update provider keys with encryption
- Test provider keys against their APIs
- Delete provider keys

Security:
- Admin-only access (session-based auth)
- Fernet encryption for API keys
- Rate limiting on test endpoints
- Audit logging for all operations

Author: Backend Developer #2
Date: October 27, 2025
"""

import logging
import os
from typing import Dict, List, Optional
from datetime import datetime
import httpx
from collections import defaultdict
from time import time as current_time

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/v1/llm/providers", tags=["Provider Keys"])

# Encryption key (shared with BYOK system)
BYOK_ENCRYPTION_KEY = os.getenv('BYOK_ENCRYPTION_KEY')

# Provider configurations with test endpoints
PROVIDER_CONFIGS = {
    'openrouter': {
        'display_name': 'OpenRouter',
        'test_url': 'https://openrouter.ai/api/v1/models',
        'test_method': 'GET',
        'auth_type': 'bearer',
        'headers': {
            'HTTP-Referer': 'https://unicorncommander.ai',
            'X-Title': 'UC-1 Pro Ops Center'
        },
        'key_format': 'sk-or-v1-...',
        'description': 'Universal LLM proxy - 200+ models'
    },
    'openai': {
        'display_name': 'OpenAI',
        'test_url': 'https://api.openai.com/v1/models',
        'test_method': 'GET',
        'auth_type': 'bearer',
        'headers': {},
        'key_format': 'sk-proj-...',
        'description': 'GPT-4o, GPT-4-turbo, o1-preview, DALL-E 3'
    },
    'anthropic': {
        'display_name': 'Anthropic',
        'test_url': 'https://api.anthropic.com/v1/messages',
        'test_method': 'POST',
        'auth_type': 'x-api-key',
        'headers': {
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        },
        'test_body': {
            'model': 'claude-3-haiku-20240307',
            'max_tokens': 1,
            'messages': [{'role': 'user', 'content': 'Hi'}]
        },
        'key_format': 'sk-ant-...',
        'description': 'Claude 3.5 Sonnet, Claude 3 Opus/Sonnet/Haiku'
    },
    'google': {
        'display_name': 'Google AI',
        'test_url': 'https://generativelanguage.googleapis.com/v1beta/models',
        'test_method': 'GET',
        'auth_type': 'query_param',
        'auth_param': 'key',
        'headers': {},
        'key_format': 'AIza...',
        'description': 'Gemini 2.0 Flash, Gemini 1.5 Pro/Flash'
    },
    'cohere': {
        'display_name': 'Cohere',
        'test_url': 'https://api.cohere.ai/v1/models',
        'test_method': 'GET',
        'auth_type': 'bearer',
        'headers': {},
        'key_format': 'Bearer ...',
        'description': 'Command R+, Command, Embed models'
    },
    'groq': {
        'display_name': 'Groq',
        'test_url': 'https://api.groq.com/openai/v1/models',
        'test_method': 'GET',
        'auth_type': 'bearer',
        'headers': {},
        'key_format': 'gsk_...',
        'description': 'Ultra-fast inference (Llama 3, Mixtral)'
    },
    'together': {
        'display_name': 'Together AI',
        'test_url': 'https://api.together.xyz/models',
        'test_method': 'GET',
        'auth_type': 'bearer',
        'headers': {},
        'key_format': 'Bearer ...',
        'description': 'Open-source models (Llama 3, Qwen, Mixtral)'
    },
    'mistral': {
        'display_name': 'Mistral AI',
        'test_url': 'https://api.mistral.ai/v1/models',
        'test_method': 'GET',
        'auth_type': 'bearer',
        'headers': {},
        'key_format': 'Bearer ...',
        'description': 'Mistral Large, Medium, Small'
    },
    'custom': {
        'display_name': 'Custom Endpoint',
        'test_url': None,  # User-provided
        'test_method': 'GET',
        'auth_type': 'bearer',
        'headers': {},
        'key_format': 'Any',
        'description': 'Custom OpenAI-compatible endpoint'
    }
}


# ============================================================================
# Request/Response Models
# ============================================================================

class SaveProviderKeyRequest(BaseModel):
    """Request model for saving provider API key"""
    provider_type: str = Field(..., description="Provider type (openrouter, openai, etc.)")
    api_key: str = Field(..., description="API key from provider", min_length=10)
    name: Optional[str] = Field(None, description="Custom provider name (optional)")
    config: Optional[Dict] = Field(None, description="Additional provider config (optional)")


class TestProviderKeyRequest(BaseModel):
    """Request model for testing provider API key"""
    provider_type: str = Field(..., description="Provider type to test")
    api_key: Optional[str] = Field(None, description="API key to test (if None, use stored key)")


class ProviderKeyResponse(BaseModel):
    """Response model for provider key operations"""
    id: str
    name: str
    provider_type: str
    has_key: bool
    enabled: bool
    health_status: Optional[str]
    last_tested: Optional[str]
    key_preview: Optional[str]
    config: Optional[Dict]


class TestResultResponse(BaseModel):
    """Response model for API key test results"""
    success: bool
    latency_ms: int
    models_found: Optional[int]
    error: Optional[str]


# ============================================================================
# Authentication & Dependencies
# ============================================================================

async def require_admin_from_session(request: Request) -> Dict:
    """
    Require admin role from session (same pattern as litellm_api.py)

    Returns:
        User dict if admin

    Raises:
        HTTPException 401 if not authenticated
        HTTPException 403 if not admin
    """
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no session token")

    # Get sessions from app state (shared with main server.py)
    sessions = getattr(request.app.state, "sessions", {})
    session_data = sessions.get(session_token)

    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session - please login again")

    user = session_data.get("user", {})
    if not user:
        raise HTTPException(status_code=401, detail="User not found in session")

    # Check if user is admin
    user_role = user.get("role", "viewer")
    if user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail=f"Admin access required (current role: {user_role})"
        )

    return user


async def get_db_pool(request: Request):
    """Get database pool from app state"""
    if not hasattr(request.app.state, 'db_pool') or not request.app.state.db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return request.app.state.db_pool


# ============================================================================
# Rate Limiting for Test Endpoint
# ============================================================================

_test_rate_limits = defaultdict(list)
TEST_RATE_LIMIT = 10  # Max 10 tests per minute
TEST_RATE_WINDOW = 60  # 60 seconds


def check_test_rate_limit(user_id: str) -> bool:
    """Check if user is within rate limit for testing"""
    now = current_time()

    # Clean old timestamps
    _test_rate_limits[user_id] = [
        ts for ts in _test_rate_limits[user_id]
        if now - ts < TEST_RATE_WINDOW
    ]

    # Check limit
    if len(_test_rate_limits[user_id]) >= TEST_RATE_LIMIT:
        return False

    # Add new timestamp
    _test_rate_limits[user_id].append(now)
    return True


# ============================================================================
# Key Encryption/Decryption Helper
# ============================================================================

class KeyEncryption:
    """Helper class for encrypting/decrypting API keys"""

    def __init__(self, encryption_key: str):
        if not encryption_key:
            raise ValueError("BYOK_ENCRYPTION_KEY environment variable required")
        self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

    def encrypt(self, api_key: str) -> str:
        """Encrypt API key"""
        return self.cipher.encrypt(api_key.encode()).decode()

    def decrypt(self, encrypted_key: str) -> str:
        """Decrypt API key"""
        return self.cipher.decrypt(encrypted_key.encode()).decode()

    def mask_key(self, encrypted_key: str) -> str:
        """Show first 7 and last 4 chars: sk-or-v...1234"""
        if not encrypted_key:
            return None
        try:
            decrypted = self.decrypt(encrypted_key)
            if len(decrypted) > 20:
                return f"{decrypted[:7]}...{decrypted[-4:]}"
            return "***"
        except Exception as e:
            logger.error(f"Failed to mask key: {e}")
            return "***"


# ============================================================================
# Provider API Testing
# ============================================================================

async def test_provider_api_key(provider_type: str, api_key: str, custom_endpoint: str = None) -> TestResultResponse:
    """
    Test API key against provider's API

    Args:
        provider_type: Provider type (openrouter, openai, etc.)
        api_key: API key to test
        custom_endpoint: Custom endpoint URL (for 'custom' provider type)

    Returns:
        TestResultResponse with success status and details
    """
    provider_type_lower = provider_type.lower()

    if provider_type_lower not in PROVIDER_CONFIGS:
        return TestResultResponse(
            success=False,
            latency_ms=0,
            error=f"Unknown provider type: {provider_type}"
        )

    config = PROVIDER_CONFIGS[provider_type_lower]

    # Handle custom endpoint
    if provider_type_lower == 'custom':
        if not custom_endpoint:
            return TestResultResponse(
                success=False,
                latency_ms=0,
                error="Custom endpoint URL required for custom provider"
            )
        test_url = f"{custom_endpoint.rstrip('/')}/v1/models"
    else:
        test_url = config['test_url']

    # Build headers based on auth type
    headers = dict(config['headers'])

    if config['auth_type'] == 'bearer':
        headers['Authorization'] = f'Bearer {api_key}'
    elif config['auth_type'] == 'x-api-key':
        headers['x-api-key'] = api_key

    try:
        start_time = current_time()

        async with httpx.AsyncClient(timeout=10.0) as client:
            if config['test_method'] == 'GET':
                # Handle query param auth (Google)
                if config['auth_type'] == 'query_param':
                    test_url = f"{test_url}?{config['auth_param']}={api_key}"

                response = await client.get(test_url, headers=headers)
            else:  # POST
                test_body = config.get('test_body', {})
                response = await client.post(test_url, headers=headers, json=test_body)

        latency_ms = int((current_time() - start_time) * 1000)

        # Parse response
        if response.status_code == 200:
            data = response.json()

            # Count models based on provider response format
            models_found = 0
            if 'data' in data:  # OpenAI/OpenRouter format
                models_found = len(data['data'])
            elif 'models' in data:  # Google format
                models_found = len(data['models'])
            elif 'id' in data:  # Anthropic successful response
                models_found = 1  # Anthropic doesn't return count, just success

            return TestResultResponse(
                success=True,
                latency_ms=latency_ms,
                models_found=models_found,
                error=None
            )
        elif response.status_code == 401:
            return TestResultResponse(
                success=False,
                latency_ms=latency_ms,
                error="Invalid API key - authentication failed"
            )
        elif response.status_code == 403:
            return TestResultResponse(
                success=False,
                latency_ms=latency_ms,
                error="API key lacks required permissions"
            )
        else:
            return TestResultResponse(
                success=False,
                latency_ms=latency_ms,
                error=f"API error: HTTP {response.status_code}"
            )

    except httpx.TimeoutException:
        return TestResultResponse(
            success=False,
            latency_ms=10000,
            error="Request timeout - API not responding"
        )
    except httpx.ConnectError:
        return TestResultResponse(
            success=False,
            latency_ms=0,
            error="Connection failed - unable to reach API endpoint"
        )
    except Exception as e:
        logger.error(f"Provider API test error: {e}", exc_info=True)
        return TestResultResponse(
            success=False,
            latency_ms=0,
            error=f"Test failed: {str(e)}"
        )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/keys")
async def list_provider_keys(
    request: Request,
    current_user: Dict = Depends(require_admin_from_session),
    db_pool = Depends(get_db_pool)
):
    """
    List all configured system provider keys (admin only)

    Returns list of providers with:
    - id: Provider UUID
    - name: Provider name
    - provider_type: openrouter, openai, etc.
    - has_key: Whether DB key is configured
    - enabled: Whether provider is enabled
    - health_status: Last health check status
    - last_tested: Last test timestamp
    - key_preview: Masked API key preview
    """
    try:
        user_id = current_user.get("email", current_user.get("username", "unknown"))

        # Initialize encryption helper
        key_encryption = KeyEncryption(BYOK_ENCRYPTION_KEY)

        # Get all providers from database
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    id,
                    name,
                    type as provider_type,
                    api_key_encrypted,
                    enabled,
                    health_status,
                    api_key_last_tested,
                    api_key_test_status,
                    config
                FROM llm_providers
                ORDER BY
                    CASE
                        WHEN api_key_encrypted IS NOT NULL THEN 0
                        ELSE 1
                    END,
                    priority DESC,
                    name
            """)

        # Build response with masked keys
        result = []
        for row in rows:
            has_db_key = bool(row['api_key_encrypted'])

            # Get environment key if no DB key
            env_var = f"{row['name'].upper().replace('-', '_')}_API_KEY"
            has_env_key = bool(os.getenv(env_var))

            result.append({
                'id': str(row['id']),
                'name': row['name'],
                'provider_type': row['provider_type'],
                'has_key': has_db_key or has_env_key,
                'key_source': 'database' if has_db_key else ('environment' if has_env_key else 'not_set'),
                'enabled': row['enabled'],
                'health_status': row['health_status'] or 'unknown',
                'last_tested': row['api_key_last_tested'].isoformat() if row['api_key_last_tested'] else None,
                'test_status': row['api_key_test_status'],
                'key_preview': key_encryption.mask_key(row['api_key_encrypted']) if has_db_key else None,
                'config': row['config'] or {}
            })

        logger.info(f"Admin {user_id} retrieved {len(result)} provider keys")

        return {
            'success': True,
            'providers': result,
            'total': len(result)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing provider keys: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve provider keys")


@router.post("/keys")
async def save_provider_key(
    key_request: SaveProviderKeyRequest,
    request: Request,
    current_user: Dict = Depends(require_admin_from_session),
    db_pool = Depends(get_db_pool)
):
    """
    Add or update system provider API key (admin only)

    Request body:
    - provider_type: openrouter, openai, anthropic, google, etc.
    - api_key: API key from provider (will be encrypted)
    - name: Optional custom name (defaults to provider_type)
    - config: Optional configuration (base_url, etc.)

    Returns:
    - provider_id: UUID of provider
    - test_result: API key test results
    """
    try:
        user_id = current_user.get("email", current_user.get("username", "unknown"))

        # Validate provider type
        if key_request.provider_type.lower() not in PROVIDER_CONFIGS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider type. Supported: {', '.join(PROVIDER_CONFIGS.keys())}"
            )

        # Initialize encryption helper
        key_encryption = KeyEncryption(BYOK_ENCRYPTION_KEY)

        # Encrypt API key
        encrypted_key = key_encryption.encrypt(key_request.api_key)

        # Determine provider name
        provider_name = key_request.name or PROVIDER_CONFIGS[key_request.provider_type.lower()]['display_name']

        # Get custom endpoint from config if provided
        custom_endpoint = None
        if key_request.config and 'base_url' in key_request.config:
            custom_endpoint = key_request.config['base_url']

        # Test API key before storing (non-blocking)
        test_result = None
        try:
            test_result = await test_provider_api_key(
                key_request.provider_type,
                key_request.api_key,
                custom_endpoint
            )

            if not test_result.success:
                logger.warning(
                    f"API key test failed for {provider_name}: {test_result.error}"
                )
                # Store anyway but include warning in response
        except Exception as test_error:
            logger.warning(f"API key test error for {provider_name}: {test_error}")
            # Continue storing even if test fails

        # Store or update provider key
        async with db_pool.acquire() as conn:
            # Check if provider exists
            existing = await conn.fetchrow("""
                SELECT id FROM llm_providers WHERE LOWER(name) = LOWER($1)
            """, provider_name)

            if existing:
                # Update existing provider
                await conn.execute("""
                    UPDATE llm_providers
                    SET api_key_encrypted = $1,
                        type = $2,
                        api_key_source = 'database',
                        api_key_updated_at = NOW(),
                        api_key_last_tested = NOW(),
                        api_key_test_status = $3,
                        config = COALESCE($4, config),
                        updated_at = NOW()
                    WHERE id = $5
                """,
                    encrypted_key,
                    key_request.provider_type.lower(),
                    'success' if (test_result and test_result.success) else 'failed',
                    key_request.config,
                    existing['id']
                )
                provider_id = str(existing['id'])
                logger.info(f"Admin {user_id} updated provider key: {provider_name}")
            else:
                # Insert new provider
                row = await conn.fetchrow("""
                    INSERT INTO llm_providers (
                        name, type, api_key_encrypted,
                        api_key_source, api_key_updated_at,
                        api_key_last_tested, api_key_test_status,
                        enabled, priority, config
                    )
                    VALUES ($1, $2, $3, 'database', NOW(), NOW(), $4, TRUE, 50, $5)
                    RETURNING id
                """,
                    provider_name,
                    key_request.provider_type.lower(),
                    encrypted_key,
                    'success' if (test_result and test_result.success) else 'failed',
                    key_request.config or {}
                )
                provider_id = str(row['id'])
                logger.info(f"Admin {user_id} added new provider key: {provider_name}")

        return {
            'success': True,
            'provider_id': provider_id,
            'name': provider_name,
            'provider_type': key_request.provider_type.lower(),
            'has_key': True,
            'enabled': True,
            'test_result': test_result.dict() if test_result else None,
            'message': 'API key saved successfully'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving provider key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save provider key")


@router.post("/keys/test")
async def test_provider_key(
    test_request: TestProviderKeyRequest,
    request: Request,
    current_user: Dict = Depends(require_admin_from_session),
    db_pool = Depends(get_db_pool)
):
    """
    Test provider API key (admin only)

    Rate Limited: 10 tests per minute per user

    Request body:
    - provider_type: Provider type to test
    - api_key: API key to test (optional, uses stored key if omitted)

    Returns:
    - success: Whether test succeeded
    - latency_ms: Response time in milliseconds
    - models_found: Number of models available (if applicable)
    - error: Error message if test failed
    """
    try:
        user_id = current_user.get("email", current_user.get("username", "unknown"))

        # Check rate limit
        if not check_test_rate_limit(user_id):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Maximum 10 tests per minute."
            )

        # Validate provider type
        if test_request.provider_type.lower() not in PROVIDER_CONFIGS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider type. Supported: {', '.join(PROVIDER_CONFIGS.keys())}"
            )

        # Get API key (either from request or database)
        api_key = test_request.api_key
        custom_endpoint = None

        if not api_key:
            # Fetch from database
            key_encryption = KeyEncryption(BYOK_ENCRYPTION_KEY)

            async with db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT api_key_encrypted, config
                    FROM llm_providers
                    WHERE LOWER(type) = LOWER($1) OR LOWER(name) = LOWER($1)
                    ORDER BY priority DESC
                    LIMIT 1
                """, test_request.provider_type)

                if not row or not row['api_key_encrypted']:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No API key configured for provider: {test_request.provider_type}"
                    )

                api_key = key_encryption.decrypt(row['api_key_encrypted'])

                # Get custom endpoint if configured
                config = row['config'] or {}
                if 'base_url' in config:
                    custom_endpoint = config['base_url']

        # Test the API key
        test_result = await test_provider_api_key(
            test_request.provider_type,
            api_key,
            custom_endpoint
        )

        # Update test status in database (only if testing stored key)
        if not test_request.api_key:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE llm_providers
                    SET api_key_last_tested = NOW(),
                        api_key_test_status = $1,
                        health_status = $2
                    WHERE LOWER(type) = LOWER($3) OR LOWER(name) = LOWER($3)
                """,
                    'success' if test_result.success else 'failed',
                    'healthy' if test_result.success else 'unhealthy',
                    test_request.provider_type
                )

        logger.info(
            f"Admin {user_id} tested {test_request.provider_type} API key: "
            f"{'success' if test_result.success else 'failed'}"
        )

        return test_result.dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing provider key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to test provider key")


@router.delete("/keys/{provider_id}")
async def delete_provider_key(
    provider_id: str,
    request: Request,
    current_user: Dict = Depends(require_admin_from_session),
    db_pool = Depends(get_db_pool)
):
    """
    Delete system provider API key (admin only)

    Note: This removes the database key but provider will fall back to
    environment variable if configured.

    Args:
        provider_id: Provider UUID

    Returns:
        success message
    """
    try:
        user_id = current_user.get("email", current_user.get("username", "unknown"))

        async with db_pool.acquire() as conn:
            # Check if provider exists
            provider = await conn.fetchrow("""
                SELECT name FROM llm_providers WHERE id = $1
            """, provider_id)

            if not provider:
                raise HTTPException(status_code=404, detail="Provider not found")

            # Delete API key (set to NULL, keep provider record)
            await conn.execute("""
                UPDATE llm_providers
                SET api_key_encrypted = NULL,
                    api_key_source = 'environment',
                    api_key_updated_at = NOW(),
                    api_key_test_status = NULL
                WHERE id = $1
            """, provider_id)

        logger.info(f"Admin {user_id} deleted API key for provider: {provider['name']}")

        return {
            'success': True,
            'provider_id': provider_id,
            'message': 'API key deleted successfully (will fall back to environment variable if configured)'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting provider key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete provider key")


@router.get("/info")
async def get_provider_info(
    current_user: Dict = Depends(require_admin_from_session)
):
    """
    Get information about all supported providers (admin only)

    Returns list of provider configurations including:
    - Provider name and type
    - Description
    - Key format
    - Test capabilities
    """
    try:
        providers_info = []

        for provider_type, config in PROVIDER_CONFIGS.items():
            providers_info.append({
                'provider_type': provider_type,
                'display_name': config['display_name'],
                'description': config['description'],
                'key_format': config['key_format'],
                'supports_test': config['test_url'] is not None,
                'auth_type': config['auth_type']
            })

        return {
            'success': True,
            'providers': providers_info,
            'total': len(providers_info)
        }

    except Exception as e:
        logger.error(f"Error getting provider info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get provider information")
