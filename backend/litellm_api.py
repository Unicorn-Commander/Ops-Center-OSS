"""
LiteLLM API - OpenAI-compatible chat completions with credit system

This module provides:
- OpenAI-compatible /v1/chat/completions endpoint
- Credit management endpoints
- Model listing
- Usage statistics
- Stripe payment integration for credit purchases

Author: Backend Developer #1
Date: October 20, 2025
"""

import logging
import os
from typing import Dict, List, Optional, Union
from datetime import datetime
import json
import time
import httpx

from fastapi import APIRouter, HTTPException, Header, Request, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import stripe

from litellm_credit_system import CreditSystem, POWER_LEVELS
from byok_manager import BYOKManager
from usage_metering import usage_meter
from cryptography.fernet import Fernet

# Import universal credential helper
from get_credential import get_credential

# Import organizational credit integration
from org_credit_integration import get_org_credit_integration

logger = logging.getLogger(__name__)

# Initialize Stripe - read credentials from database first, then environment
stripe.api_key = get_credential('STRIPE_SECRET_KEY')

# Router
router = APIRouter(prefix="/api/v1/llm", tags=["LLM"])

# Access to sessions store (set by server.py when registering this router)
sessions = {}

def set_sessions_store(sessions_dict):
    """Set reference to server's sessions store"""
    global sessions
    sessions = sessions_dict

# LiteLLM proxy URL
LITELLM_PROXY_URL = os.getenv('LITELLM_PROXY_URL', 'http://unicorn-litellm-wilmer:4000')

# BYOK encryption key (used for both user and system keys)
BYOK_ENCRYPTION_KEY = os.getenv('BYOK_ENCRYPTION_KEY')


# ============================================================================
# Provider Configuration
# ============================================================================

# Provider configurations for BYOK routing
PROVIDER_CONFIGS = {
    'openai': {
        'base_url': 'https://api.openai.com/v1',
        'model_prefixes': ['openai/', 'gpt-', 'o1-', 'o3-'],
        'default_headers': {}
    },
    'anthropic': {
        'base_url': 'https://api.anthropic.com/v1',
        'model_prefixes': ['anthropic/', 'claude-'],
        'default_headers': {
            'anthropic-version': '2023-06-01'
        }
    },
    'openrouter': {
        'base_url': 'https://openrouter.ai/api/v1',
        'model_prefixes': [],  # Accepts all models
        'default_headers': {
            'HTTP-Referer': os.getenv('APP_URL', 'http://localhost:8084'),
            'X-Title': os.getenv('APP_TITLE', 'Ops Center')
        }
    },
    'google': {
        'base_url': 'https://generativelanguage.googleapis.com/v1beta',
        'model_prefixes': ['google/', 'gemini-'],
        'default_headers': {}
    },
    'ollama': {
        'base_url': 'http://localhost:11434/v1',
        'model_prefixes': ['ollama/'],
        'default_headers': {}
    },
    'ollama_cloud': {
        'base_url': 'https://ollama.com/api/v1',
        'model_prefixes': ['ollama-cloud/'],
        'default_headers': {}
    }
}


def detect_provider_from_model(model_name: str) -> str:
    """
    Detect provider from model name

    Args:
        model_name: Model identifier (e.g., "openai/gpt-4", "claude-3-opus")

    Returns:
        Provider name (openai, anthropic, openrouter, google)
    """
    if not model_name:
        return 'openrouter'  # Default to OpenRouter

    model_lower = model_name.lower()

    # Check each provider's prefixes
    for provider, config in PROVIDER_CONFIGS.items():
        for prefix in config['model_prefixes']:
            if model_lower.startswith(prefix.lower()):
                return provider

    # Default to OpenRouter (handles all models)
    return 'openrouter'


# Model ID normalization mapping for OpenRouter
# Maps short/abbreviated model names to full OpenRouter model IDs
MODEL_ID_MAPPING = {
    # Llama 3.3 variants
    'llama-3.3-70b': 'meta-llama/llama-3.3-70b-instruct',
    'llama-3.3-70b-instruct': 'meta-llama/llama-3.3-70b-instruct',
    'llama-3.3': 'meta-llama/llama-3.3-70b-instruct',

    # Llama 3.2 variants
    'llama-3.2-90b': 'meta-llama/llama-3.2-90b-vision-instruct',
    'llama-3.2-11b': 'meta-llama/llama-3.2-11b-vision-instruct',
    'llama-3.2-3b': 'meta-llama/llama-3.2-3b-instruct',
    'llama-3.2-1b': 'meta-llama/llama-3.2-1b-instruct',

    # Llama 3.1 variants
    'llama-3.1-405b': 'meta-llama/llama-3.1-405b-instruct',
    'llama-3.1-70b': 'meta-llama/llama-3.1-70b-instruct',
    'llama-3.1-8b': 'meta-llama/llama-3.1-8b-instruct',

    # Llama 3 variants
    'llama-3-70b': 'meta-llama/llama-3-70b-instruct',
    'llama-3-8b': 'meta-llama/llama-3-8b-instruct',

    # GPT variants (for compatibility)
    'gpt-4': 'openai/gpt-4',
    'gpt-4-turbo': 'openai/gpt-4-turbo',
    'gpt-4o': 'openai/gpt-4o',
    'gpt-3.5-turbo': 'openai/gpt-3.5-turbo',

    # Claude variants
    'claude-3-opus': 'anthropic/claude-3-opus',
    'claude-3-sonnet': 'anthropic/claude-3-sonnet',
    'claude-3.5-sonnet': 'anthropic/claude-3.5-sonnet',

    # Mistral variants
    'mistral-7b': 'mistralai/mistral-7b-instruct',
    'mixtral-8x7b': 'mistralai/mixtral-8x7b-instruct',
    'mixtral-8x22b': 'mistralai/mixtral-8x22b-instruct',

    # DeepSeek variants (note: deepseek-coder doesn't exist, redirect to chat)
    'deepseek-coder': 'deepseek/deepseek-chat-v3.1',
    'deepseek/deepseek-coder': 'deepseek/deepseek-chat-v3.1',
    'deepseek-chat': 'deepseek/deepseek-chat-v3.1',
    'deepseek/deepseek-chat': 'deepseek/deepseek-chat-v3.1',
    'deepseek-r1': 'deepseek/deepseek-r1-0528',
    'deepseek/deepseek-r1': 'deepseek/deepseek-r1-0528',

    # Qwen variants
    'qwen3-coder': 'qwen/qwen3-coder',
    'qwen/qwen3-coder': 'qwen/qwen3-coder',
    'qwen-2.5-coder': 'qwen/qwen-2.5-coder-32b-instruct',
    'qwen-2.5-72b': 'qwen/qwen-2.5-72b-instruct',
    'qwen-2-72b': 'qwen/qwen-2-72b-instruct',
}


def normalize_model_id(model_name: str) -> str:
    """
    Normalize model ID to full OpenRouter format

    Converts short model names (e.g., "llama-3.3-70b") to full OpenRouter IDs
    (e.g., "meta-llama/llama-3.3-70b-instruct")

    Also strips incorrect SDK-added prefixes when using custom baseURL.
    Various AI SDKs (@ai-sdk/openai, @ai-sdk/ai21, etc.) prepend their provider name
    even when routing through OpenRouter.

    Examples:
      - "openai/openrouter/deepseek/deepseek-coder" → "deepseek/deepseek-coder"
      - "ai21/openrouter/qwen/qwen3-coder" → "qwen/qwen3-coder"
      - "openai/deepseek/deepseek-chat" → "deepseek/deepseek-chat"

    Args:
        model_name: Short or full model identifier

    Returns:
        Full OpenRouter model ID
    """
    if not model_name:
        return model_name

    original_name = model_name

    # List of SDK prefixes that should be stripped
    # These are added by various AI SDKs when using custom baseURL
    sdk_prefixes = ['openai/', 'ai21/', 'anthropic/', 'cohere/', 'google/', 'mistral/']

    # Strip SDK-added provider prefix if present
    for prefix in sdk_prefixes:
        if model_name.startswith(prefix) and model_name.count('/') >= 2:
            # Only strip if it looks like: sdk/provider/model or sdk/openrouter/provider/model
            model_name = model_name[len(prefix):]
            logger.info(f"Stripped SDK prefix '{prefix}': {original_name} → {model_name}")
            break

    # Now check if there's a redundant "openrouter/" prefix
    # This happens when the model ID is like "openrouter/qwen/qwen3-coder"
    # but it should just be "qwen/qwen3-coder" for the OpenRouter API
    if model_name.startswith('openrouter/') and model_name.count('/') >= 2:
        cleaned = model_name[11:]  # Remove "openrouter/" prefix (11 chars)
        logger.info(f"Stripped redundant openrouter/ prefix: {model_name} → {cleaned}")
        model_name = cleaned

    # If we made any changes, return the cleaned version
    if model_name != original_name:
        return model_name

    # Check if already in full format (contains provider prefix)
    if '/' in model_name and not model_name.startswith('/'):
        return model_name

    # Check mapping for short names
    model_lower = model_name.lower()
    if model_lower in MODEL_ID_MAPPING:
        normalized = MODEL_ID_MAPPING[model_lower]
        logger.info(f"Normalized model ID: {model_name} → {normalized}")
        return normalized

    # Return as-is if no mapping found
    return model_name


# ============================================================================
# Session-Based Authentication for Admin Endpoints
# ============================================================================

async def get_current_user_from_session(request: Request) -> Dict:
    """
    Get current user from session cookie (used by admin endpoints)

    This uses the same session-based authentication as other admin endpoints
    in ops-center (user_management_api, subscription_api, etc.)

    Returns:
        User dict with email, username, role, etc.

    Raises:
        HTTPException 401 if not authenticated
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

    return user


async def require_admin_from_session(request: Request) -> Dict:
    """
    Require admin role from session (used by admin endpoints)

    Returns:
        User dict if admin

    Raises:
        HTTPException 401 if not authenticated
        HTTPException 403 if not admin
    """
    user = await get_current_user_from_session(request)

    # Check if user is admin
    user_role = user.get("role", "viewer")
    if user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail=f"Admin access required (current role: {user_role})"
        )

    return user


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    model: Optional[str] = Field(None, description="Model override (optional)")
    max_tokens: Optional[int] = Field(None, description="Max tokens to generate")
    temperature: Optional[float] = Field(None, description="Sampling temperature")
    stream: bool = Field(False, description="Stream response")
    task_type: Optional[str] = Field(None, description="Task type (code, chat, rag, creative)")
    privacy_required: bool = Field(False, description="Require local models")
    power_level: str = Field("balanced", description="Power level (eco, balanced, precision)")
    tools: Optional[List[dict]] = Field(None, description="Function/tool definitions for structured output")
    tool_choice: Optional[Union[str, dict]] = Field(None, description="Tool choice (auto, required, or specific tool)")


class CreditPurchaseRequest(BaseModel):
    amount: float = Field(..., description="Credits to purchase (10, 50, 100)")
    stripe_token: str = Field(..., description="Stripe payment token")


class CreditResponse(BaseModel):
    user_id: str
    credits_remaining: float
    tier: str
    monthly_cap: Optional[float]


class UsageStats(BaseModel):
    total_requests: int
    total_tokens: int
    total_cost: float
    avg_cost_per_request: float
    providers: List[Dict]


class AddBYOKKeyRequest(BaseModel):
    """Request model for adding/updating a BYOK key"""
    provider: str = Field(..., description="Provider name (openrouter, openai, anthropic, google)")
    api_key: str = Field(..., description="API key from provider", min_length=10)
    metadata: Optional[Dict] = Field(None, description="Optional metadata")


class ToggleBYOKRequest(BaseModel):
    """Request model for toggling BYOK key status"""
    enabled: bool = Field(..., description="Enable or disable key")


class ImageGenerationRequest(BaseModel):
    """Request model for image generation"""
    prompt: str = Field(..., description="Text description of the image to generate", min_length=1)
    model: Optional[str] = Field(None, description="Model to use (dall-e-3, dall-e-2, stable-diffusion-xl, etc.)")
    n: int = Field(1, description="Number of images to generate", ge=1, le=10)
    size: Optional[str] = Field("1024x1024", description="Image size (256x256, 512x512, 1024x1024, 1792x1024, 1024x1792)")
    quality: Optional[str] = Field("standard", description="Image quality (standard, hd)")
    style: Optional[str] = Field(None, description="Style preset (vivid, natural)")
    response_format: Optional[str] = Field("url", description="Response format (url, b64_json)")


class ImageGenerationResponse(BaseModel):
    """Response model for image generation"""
    created: int
    data: List[Dict]
    _metadata: Optional[Dict] = None


# ============================================================================
# System Key Manager (Admin Provider Keys)
# ============================================================================

class SystemKeyManager:
    """Manages system-level provider API keys for metering users"""

    def __init__(self, db_pool, encryption_key):
        """
        Initialize System Key Manager

        Args:
            db_pool: PostgreSQL connection pool
            encryption_key: Fernet encryption key
        """
        self.pool = db_pool
        if not encryption_key:
            raise ValueError("BYOK_ENCRYPTION_KEY environment variable required")
        self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

    async def set_system_key(self, provider_id: str, api_key: str, source: str = 'database'):
        """
        Encrypt and store system API key

        If provider doesn't exist in database (MD5 hash ID), creates it first.

        Args:
            provider_id: Provider UUID or MD5 hash
            api_key: Plain text API key
            source: 'database' or 'environment'
        """
        try:
            import hashlib
            encrypted = self.cipher.encrypt(api_key.encode()).decode()

            async with self.pool.acquire() as conn:
                # Check if this is an MD5 hash (temp ID for provider not in DB)
                if len(provider_id) == 32 and all(c in '0123456789abcdef' for c in provider_id):
                    # This is a temp ID - need to find or create the provider
                    ALL_PROVIDERS = [
                        {'type': 'openrouter', 'name': 'OpenRouter'},
                        {'type': 'openai', 'name': 'OpenAI'},
                        {'type': 'anthropic', 'name': 'Anthropic'},
                        {'type': 'google', 'name': 'Google'},
                        {'type': 'cohere', 'name': 'Cohere'},
                        {'type': 'groq', 'name': 'Groq'},
                        {'type': 'together', 'name': 'Together'},
                        {'type': 'mistral', 'name': 'Mistral'},
                        {'type': 'ollama-cloud', 'name': 'Ollama Cloud'},
                        {'type': 'huggingface', 'name': 'HuggingFace'},
                        {'type': 'unicorn-commander', 'name': 'Unicorn Commander'},
                        {'type': 'custom', 'name': 'Custom Provider'}
                    ]

                    # Find which provider this MD5 represents
                    provider_type = None
                    provider_name = None
                    for p in ALL_PROVIDERS:
                        if hashlib.md5(p['type'].encode()).hexdigest() == provider_id:
                            provider_type = p['type']
                            provider_name = p['name']
                            break

                    if not provider_type:
                        raise HTTPException(status_code=400, detail="Invalid provider ID")

                    # Insert or update provider
                    await conn.execute("""
                        INSERT INTO llm_providers (name, type, api_key_encrypted, api_key_source, enabled, created_at, updated_at, api_key_updated_at)
                        VALUES ($1, $2, $3, $4, TRUE, NOW(), NOW(), NOW())
                        ON CONFLICT (name) DO UPDATE
                        SET api_key_encrypted = $3,
                            api_key_source = $4,
                            api_key_updated_at = NOW()
                    """, provider_name, provider_type, encrypted, source)
                    logger.info(f"Created/updated provider {provider_name} ({provider_type}) with system key")
                else:
                    # Regular UUID - update existing provider
                    await conn.execute("""
                        UPDATE llm_providers
                        SET api_key_encrypted = $1,
                            api_key_source = $2,
                            api_key_updated_at = NOW()
                        WHERE id = $3
                    """, encrypted, source, provider_id)
                    logger.info(f"Updated system key for provider {provider_id}")
        except Exception as e:
            logger.error(f"Failed to set system key: {e}")
            raise HTTPException(status_code=500, detail="Failed to store system key")

    async def get_system_key(self, provider_id: str) -> Optional[str]:
        """
        Get decrypted system API key (database > environment)

        Args:
            provider_id: Provider UUID

        Returns:
            Decrypted API key or None
        """
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT api_key_encrypted, api_key_source, name
                    FROM llm_providers WHERE id = $1
                """, provider_id)

                if not row:
                    return None

                # Try database key first
                if row['api_key_encrypted']:
                    try:
                        return self.cipher.decrypt(row['api_key_encrypted'].encode()).decode()
                    except Exception as e:
                        logger.error(f"Failed to decrypt system key: {e}")

                # Fallback to environment variable
                env_var = f"{row['name'].upper().replace('-', '_')}_API_KEY"
                return os.getenv(env_var)

        except Exception as e:
            logger.error(f"Failed to get system key: {e}")
            return None

    async def delete_system_key(self, provider_id: str):
        """
        Delete system API key (falls back to environment)

        Args:
            provider_id: Provider UUID
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE llm_providers
                    SET api_key_encrypted = NULL,
                        api_key_source = 'environment',
                        api_key_updated_at = NOW()
                    WHERE id = $1
                """, provider_id)
                logger.info(f"Deleted system key for provider {provider_id}")
        except Exception as e:
            logger.error(f"Failed to delete system key: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete system key")

    async def get_all_providers_with_keys(self):
        """
        Get all providers with masked keys

        Returns ALL available providers (from code), not just ones in database.
        Merges with database records to show key status.
        """
        try:
            # Define all available providers
            ALL_PROVIDERS = [
                {'type': 'openrouter', 'name': 'OpenRouter'},
                {'type': 'openai', 'name': 'OpenAI'},
                {'type': 'anthropic', 'name': 'Anthropic'},
                {'type': 'google', 'name': 'Google'},
                {'type': 'cohere', 'name': 'Cohere'},
                {'type': 'groq', 'name': 'Groq'},
                {'type': 'together', 'name': 'Together'},
                {'type': 'mistral', 'name': 'Mistral'},
                {'type': 'ollama-cloud', 'name': 'Ollama Cloud'},
                {'type': 'huggingface', 'name': 'HuggingFace'},
                {'type': 'unicorn-commander', 'name': 'Unicorn Commander'},
                {'type': 'custom', 'name': 'Custom Provider'}
            ]

            # Get providers from database
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, name, type as provider_type, api_key_encrypted,
                           api_key_source, api_key_last_tested, api_key_test_status
                    FROM llm_providers
                    WHERE enabled = TRUE
                    ORDER BY name
                """)

                # Create dict of database providers by type
                db_providers = {row['provider_type']: row for row in rows}

            # Merge: show ALL providers, with database status if available
            result = []
            for provider_def in ALL_PROVIDERS:
                provider_type = provider_def['type']
                db_row = db_providers.get(provider_type)

                # Check environment variables
                env_var = f"{provider_def['name'].upper().replace('-', '_').replace(' ', '_')}_API_KEY"
                has_env_key = bool(os.getenv(env_var))

                if db_row:
                    # Provider exists in database
                    has_db_key = bool(db_row['api_key_encrypted'])
                    provider_id = str(db_row['id'])
                else:
                    # Provider not in database - generate temp ID from type
                    import hashlib
                    provider_id = hashlib.md5(provider_type.encode()).hexdigest()
                    has_db_key = False

                # Determine key_source for frontend
                if has_db_key:
                    key_source = 'database'
                elif has_env_key:
                    key_source = 'environment'
                else:
                    key_source = 'not_set'

                result.append({
                    'id': provider_id,
                    'name': provider_def['name'],
                    'type': provider_type,
                    'provider_type': provider_type,  # Keep for backwards compatibility
                    'has_db_key': has_db_key,
                    'has_env_key': has_env_key,
                    'key_source': key_source,
                    'last_tested': db_row['api_key_last_tested'].isoformat() if db_row and db_row['api_key_last_tested'] else None,
                    'test_status': db_row['api_key_test_status'] if db_row else None,
                    'key_preview': self._mask_key(db_row['api_key_encrypted']) if db_row and has_db_key else None
                })

            return result

        except Exception as e:
            logger.error(f"Failed to get providers with keys: {e}")
            return []

    def _mask_key(self, encrypted_key):
        """Show first 7 and last 4 chars: sk-or-v...1234"""
        if not encrypted_key:
            return None
        try:
            decrypted = self.cipher.decrypt(encrypted_key.encode()).decode()
            if len(decrypted) > 20:
                return f"{decrypted[:7]}...{decrypted[-4:]}"
            return "***"
        except Exception as e:
            logger.error(f"Failed to mask key: {e}")
            return "***"


# ============================================================================
# Dependency Injection
# ============================================================================

async def get_credit_system(request: Request) -> CreditSystem:
    """Get credit system from app state"""
    return request.app.state.credit_system


async def get_byok_manager(request: Request) -> BYOKManager:
    """Get BYOK manager from app state"""
    return request.app.state.byok_manager


async def get_user_id(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> str:
    """
    Extract user ID from authorization header OR session cookie

    Supports four authentication methods:
    1. Session Cookie: session_token cookie (for browser-based requests)
    2. API Key: Bearer uc_<hex-key>
    3. JWT Token: Bearer <jwt-token>
    4. Service Key: Bearer sk-<service-name>-service-key-<year>
    """
    # Try session-based authentication first (for browser requests)
    if not authorization:
        logger.info("No Authorization header, trying session cookie authentication")
        session_token = request.cookies.get("session_token")

        if session_token and session_token in sessions:
            session = sessions[session_token]
            user_data = session.get("user", {})

            # Try to get user_id from session
            user_id = user_data.get("user_id") or user_data.get("sub") or user_data.get("id")

            if user_id:
                logger.info(f"✅ Session authenticated: user_id={user_id}")
                return user_id
            else:
                logger.warning("Session found but no user_id in session data")
                raise HTTPException(status_code=401, detail="Invalid session: user_id not found")
        else:
            logger.warning("No Authorization header and no valid session")
            raise HTTPException(status_code=401, detail="Authentication required (Authorization header or session cookie)")

    # Authorization header provided - use existing token-based auth
    if not authorization.startswith('Bearer '):
        logger.warning(f"Invalid auth format: {authorization[:20]}...")
        raise HTTPException(status_code=401, detail="Invalid authorization format. Use: Authorization: Bearer <api-key>")

    # Extract token
    token = authorization[7:]
    logger.info(f"🔍 Auth token received - Length: {len(token)}, Prefix: {token[:10]}...")

    # Check for service key (format: sk-<service>-service-key-<year>)
    if token.startswith('sk-'):
        logger.info(f"🔑 Token starts with 'sk-', checking service keys...")
        # Service keys are pre-configured trusted keys for internal services
        service_keys = {
            'sk-bolt-diy-service-key-2025': 'bolt-diy-service',
            'sk-presenton-service-key-2025': 'presenton-service',
            'sk-brigade-service-key-2025': 'brigade-service',
            'sk-centerdeep-service-key-2025': 'centerdeep-service',
            'sk-partnerpulse-service-key-2025': 'partnerpulse-service'
        }

        # FIX P0: Map service names to actual UUIDs from database (not strings)
        # These are the actual organization UUIDs for service accounts
        service_org_ids = {
            'bolt-diy-service': '3766e9ee-7cc1-472f-92ae-afec687f0d74',      # UUID for bolt-diy-service org
            'presenton-service': '13587747-66e6-43df-b21d-4411c7373465',     # UUID for presenton-service org
            'brigade-service': 'e9b40f6b-b683-4bcf-b462-9fd526cfbb37',       # UUID for brigade-service org
            'centerdeep-service': '91d3b68e-e4c4-457e-80ce-de6997243c34',    # UUID for centerdeep-service org
            'partnerpulse-service': '8f5bf9a9-2e7c-4465-93d8-97f18bdac098'   # UUID for partnerpulse-service org
        }

        if token in service_keys:
            service_name = service_keys[token]

            # Check for X-User-ID header (service proxying on behalf of user)
            x_user_id = request.headers.get('X-User-ID')
            if x_user_id:
                # Service is proxying for a user - bill to user's account
                logger.info(f"✅ Service key authenticated: {service_name} proxying for user: {x_user_id}")
                return x_user_id
            else:
                # No user context - use service organization account for billing
                service_org_id = service_org_ids.get(service_name)
                if service_org_id:
                    # Prefix with 'org_' so credit system recognizes this as an organization
                    org_prefixed_id = f"org_{service_org_id}"
                    logger.info(f"✅ Service key authenticated: {service_name} using org credits: {org_prefixed_id}")
                    return org_prefixed_id
                else:
                    logger.error(f"❌ Service org ID not configured for: {service_name}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Service organization not configured for {service_name}. Contact system administrator."
                    )
        else:
            logger.warning(f"❌ Unknown service key: {token[:20]}... (full length: {len(token)})")
            raise HTTPException(status_code=401, detail="Invalid service key")
    else:
        logger.info(f"ℹ️ Token does NOT start with 'sk-', will try API key or JWT validation")

    # Try API key validation (format: uc_<hex>)
    if token.startswith('uc_'):
        from api_key_manager import get_api_key_manager
        try:
            manager = get_api_key_manager()
            user_info = await manager.validate_api_key(token)

            if user_info:
                # API key is valid
                return user_info['user_id']
            else:
                raise HTTPException(status_code=401, detail="Invalid or expired API key")
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            raise HTTPException(status_code=401, detail="API key validation failed")

    # Try JWT token validation
    try:
        from api_key_manager import get_api_key_manager
        manager = get_api_key_manager()
        payload = manager.validate_jwt_token(token)

        if payload and 'user_id' in payload:
            return payload['user_id']
        else:
            raise HTTPException(status_code=401, detail="Invalid or expired JWT token")
    except Exception as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(status_code=401, detail="Token validation failed")


def get_user_role(user_id: str) -> str:
    """
    Get user role from userInfo (cached in memory or fetch from Keycloak)

    Args:
        user_id: User identifier

    Returns:
        User role (admin, moderator, developer, analyst, viewer)

    Note: This is a placeholder implementation. In production, this should:
    1. Validate JWT token and extract roles
    2. Query Keycloak for user roles
    3. Cache results in Redis for performance
    """
    # TODO: Implement proper role extraction from JWT or Keycloak
    # For now, assume all users are viewers unless explicitly admin

    # Simple check: if user_id contains 'admin' or is in admin list
    admin_users = os.getenv('ADMIN_USER_IDS', '').split(',')
    if user_id in admin_users or 'admin' in user_id.lower():
        return 'admin'

    return 'viewer'


# ============================================================================
# Chat Completions Endpoint
# ============================================================================

@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    user_id: str = Depends(get_user_id),
    credit_system: CreditSystem = Depends(get_credit_system),
    byok_manager: BYOKManager = Depends(get_byok_manager),
    x_power_level: Optional[str] = Header(None, alias="X-Power-Level")
):
    """
    OpenAI-compatible chat completions endpoint with credit system

    Request Headers:
        Authorization: Bearer <user-api-key>
        X-Power-Level: eco | balanced | precision (optional)

    Returns:
        OpenAI-compatible chat completion response
        + X-Provider-Used: Provider that handled request
        + X-Cost-Incurred: Credits deducted
        + X-Credits-Remaining: Updated balance
    """
    try:
        # Determine power level
        power_level = x_power_level or request.power_level
        if power_level not in POWER_LEVELS:
            power_level = "balanced"

        # Get user tier for cost calculation
        user_tier = await credit_system.get_user_tier(user_id)

        # Get power level config
        power_config = POWER_LEVELS[power_level]

        # Check if user has BYOK for preferred providers
        user_keys = await byok_manager.get_all_user_keys(user_id)

        # Determine BYOK routing:
        # 1. If user has OpenRouter BYOK, use it for ALL models (OpenRouter is universal proxy)
        # 2. Otherwise, check if user has provider-specific BYOK for this model
        using_byok = False
        user_byok_key = None
        detected_provider = None

        if 'openrouter' in user_keys:
            # User has OpenRouter BYOK - use it for all models
            using_byok = True
            user_byok_key = user_keys['openrouter']
            detected_provider = 'openrouter'
            logger.info(f"User {user_id} has OpenRouter BYOK - using for all models")
        else:
            # Check for provider-specific BYOK
            detected_provider = detect_provider_from_model(request.model)
            if detected_provider in user_keys:
                using_byok = True
                user_byok_key = user_keys[detected_provider]
                logger.info(f"User {user_id} has {detected_provider} BYOK")

        # Estimate tokens for pre-check (rough estimate)
        estimated_tokens = sum(len(msg.content.split()) * 1.5 for msg in request.messages)
        estimated_tokens = int(estimated_tokens)

        # Calculate estimated cost (ASYNC NOW)
        estimated_cost = await credit_system.calculate_cost(
            tokens_used=estimated_tokens,
            model=request.model or "balanced",
            power_level=power_level,
            user_tier=user_tier
        )

        # Check credits BEFORE making request (skip if using BYOK)
        org_id = None  # Will be set if using org billing
        if not using_byok and user_tier != 'free':
            # Try organizational billing first
            org_integration = get_org_credit_integration()
            has_org_credits, org_id, message = await org_integration.has_sufficient_org_credits(
                user_id=user_id,
                credits_needed=estimated_cost,
                request_state=getattr(request, 'state', None) if hasattr(request, 'state') else None
            )

            if org_id:
                # User belongs to organization - use org billing
                if not has_org_credits:
                    raise HTTPException(
                        status_code=402,  # Payment Required
                        detail=f"Insufficient organization credits. {message}"
                    )
                logger.info(f"User {user_id} using org billing (org: {org_id})")
            else:
                # Fallback to individual credits (backward compatibility)
                current_balance = await credit_system.get_user_credits(user_id)

                if current_balance < estimated_cost:
                    raise HTTPException(
                        status_code=402,  # Payment Required
                        detail=f"Insufficient credits. Balance: {current_balance:.6f}, Estimated cost: {estimated_cost:.6f}"
                    )

                # Check monthly cap
                within_cap = await credit_system.check_monthly_cap(user_id, estimated_cost)
                if not within_cap:
                    raise HTTPException(
                        status_code=429,  # Too Many Requests
                        detail="Monthly spending cap exceeded"
                    )
                logger.info(f"User {user_id} using individual billing (no org)")

        # Prepare request for LiteLLM proxy
        proxy_request = {
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "max_tokens": request.max_tokens or power_config["max_tokens"],
            "temperature": request.temperature or power_config["temperature"],
            "stream": request.stream,
            "user": user_id,  # For usage tracking
            "metadata": {
                "user_id": user_id,
                "power_level": power_level,
                "task_type": request.task_type,
                "privacy_required": request.privacy_required,
                "user_tier": user_tier
            }
        }

        # Include tools and tool_choice if provided (for structured output like ResponseSchema)
        if request.tools:
            proxy_request["tools"] = request.tools
            logger.info(f"Including {len(request.tools)} tools in request (structured output)")
        if request.tool_choice:
            proxy_request["tool_choice"] = request.tool_choice
            logger.info(f"Including tool_choice: {request.tool_choice}")

        # Add model if specified (normalize to full OpenRouter ID first)
        if request.model:
            normalized_model = normalize_model_id(request.model)
            proxy_request["model"] = normalized_model
            logger.info(f"Using model: {normalized_model} (original: {request.model})")

        # Determine API endpoint and headers based on BYOK or system key
        if using_byok:
            # User is using their own API key
            logger.info(f"Using BYOK for {user_id} with provider {detected_provider}")

            # Get provider config
            provider_config = PROVIDER_CONFIGS.get(detected_provider, PROVIDER_CONFIGS['openrouter'])
            base_url = provider_config['base_url']
            api_key = user_byok_key
            provider_name = detected_provider.title()

            # Build headers
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                **provider_config['default_headers']
            }

        else:
            # Using system OpenRouter key (charge credits)
            logger.info(f"Using system OpenRouter key for {user_id}")

            # Get provider info from database for direct API call
            async with credit_system.db_pool.acquire() as conn:
                # Get OpenRouter provider (or first enabled provider)
                provider = await conn.fetchrow("""
                    SELECT id, name, type, api_key_encrypted, config
                    FROM llm_providers
                    WHERE enabled = true AND type = 'openrouter'
                    ORDER BY priority DESC
                    LIMIT 1
                """)

                if not provider:
                    raise HTTPException(
                        status_code=503,
                        detail="No LLM providers configured. Please configure OpenRouter in Platform Settings."
                    )

                # Get provider config (handle both dict and JSON string)
                provider_db_config = provider['config'] or {}
                if isinstance(provider_db_config, str):
                    import json
                    provider_db_config = json.loads(provider_db_config)

                base_url = provider_db_config.get('base_url', 'https://openrouter.ai/api/v1')
                provider_name = provider['name']

                # Get system API key (prefer database over environment)
                api_key = None
                try:
                    # Try to use SystemKeyManager if encryption key is available
                    system_key_manager = SystemKeyManager(credit_system.db_pool, BYOK_ENCRYPTION_KEY)
                    api_key = await system_key_manager.get_system_key(provider['id'])
                except Exception as e:
                    logger.warning(f"SystemKeyManager failed: {e}, falling back to direct decryption")
                    api_key = None
                if not api_key:
                    # Fallback: Try to decrypt the key directly
                    encrypted_key = provider['api_key_encrypted']
                    if not encrypted_key:
                        raise HTTPException(
                            status_code=503,
                            detail="No API key configured for system provider. Please configure in Platform Settings."
                        )

                    try:
                        # Try to decrypt if it looks like Fernet encrypted data
                        if encrypted_key.startswith('gAAAAA'):
                            from cryptography.fernet import Fernet
                            cipher = Fernet(BYOK_ENCRYPTION_KEY.encode() if isinstance(BYOK_ENCRYPTION_KEY, str) else BYOK_ENCRYPTION_KEY)
                            api_key = cipher.decrypt(encrypted_key.encode()).decode()
                            logger.info("Successfully decrypted system API key from database")
                        else:
                            # Assume it's plain text
                            api_key = encrypted_key
                            logger.info("Using plain text API key from database")
                    except Exception as e:
                        logger.error(f"Failed to decrypt API key, trying as plain text: {e}")
                        api_key = encrypted_key

            # Build headers for OpenRouter
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv('APP_URL', 'http://localhost:8084'),  # Required by OpenRouter
                "X-Title": os.getenv('APP_TITLE', 'Ops Center')  # Required by OpenRouter
            }

        # Call provider API directly
        # Handle streaming vs non-streaming requests differently
        if request.stream:
            # STREAMING PATH: Return Server-Sent Events (SSE)
            logger.info(f"Streaming request for user {user_id}, model: {request.model}")

            async def stream_generator():
                """
                Generator that forwards SSE events from OpenRouter to client.

                CRITICAL: Each yield must be followed by await asyncio.sleep(0) to force
                FastAPI to send buffered chunks immediately. Without this, clients receive
                zero bytes until stream completes.
                """
                import asyncio  # Import here for sleep(0) flush
                total_tokens = 0
                provider_used = request.model or "unknown"
                chunks_received = 0

                # Send an initial comment to keep connection alive and force headers
                yield ": ping\n\n"
                await asyncio.sleep(0)

                try:
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        async with client.stream(
                            'POST',
                            f"{base_url}/chat/completions",
                            json=proxy_request,
                            headers=headers
                        ) as response:
                            if response.status_code != 200:
                                error_text = await response.aread()
                                logger.error(f"OpenRouter streaming error: {error_text.decode()}")
                                error_data = {
                                    "error": {
                                        "message": f"LLM provider error: {error_text.decode()}",
                                        "type": "api_error",
                                        "code": response.status_code
                                    }
                                }
                                yield f"data: {json.dumps(error_data)}\n\n"
                                await asyncio.sleep(0)  # Force flush
                                return

                            # Stream SSE events from provider
                            async for line in response.aiter_lines():
                                if not line:
                                    continue

                                if line.startswith('data: '):
                                    data_str = line[6:]  # Remove 'data: ' prefix

                                    # Check for completion marker
                                    if data_str.strip() == '[DONE]':
                                        logger.info(f"Streaming complete: {chunks_received} chunks, ~{total_tokens} tokens")
                                        yield f"data: [DONE]\n\n"
                                        await asyncio.sleep(0)  # Force flush
                                        break

                                    # Parse and forward chunk
                                    try:
                                        chunk = json.loads(data_str)
                                        chunks_received += 1

                                        # Extract usage tokens from final chunk (if present)
                                        if 'usage' in chunk:
                                            usage = chunk['usage']
                                            total_tokens = usage.get('total_tokens', 0)
                                            logger.info(f"Received usage data: {total_tokens} tokens")

                                        # Extract model info if present
                                        if 'model' in chunk and chunk['model']:
                                            provider_used = chunk['model']

                                        # Forward chunk to client
                                        yield f"data: {data_str}\n\n"

                                        # CRITICAL FIX: Force flush by yielding to event loop
                                        # This ensures FastAPI sends buffered data immediately
                                        # Without this, chunks are buffered and client receives nothing
                                        await asyncio.sleep(0)

                                    except json.JSONDecodeError as e:
                                        logger.warning(f"Failed to parse SSE chunk: {e}, data: {data_str[:100]}")
                                        continue

                    # After streaming completes, deduct credits
                    if not using_byok and (user_tier != 'free' or total_tokens > 0):
                        # Use actual tokens if available, otherwise estimate
                        tokens_for_billing = total_tokens if total_tokens > 0 else estimated_tokens

                        # Calculate actual cost (ASYNC NOW)
                        actual_cost = await credit_system.calculate_cost(
                            tokens_used=tokens_for_billing,
                            model=provider_used,
                            power_level=power_level,
                            user_tier=user_tier
                        )

                        # Deduct credits
                        if org_id:
                            # Organization billing
                            success, used_org_id, remaining_credits = await get_org_credit_integration().deduct_org_credits(
                                user_id=user_id,
                                credits_used=actual_cost,
                                service_name=provider_used,
                                provider=provider_used,
                                model=request.model,
                                tokens_used=tokens_for_billing,
                                power_level=power_level,
                                task_type=request.task_type,
                                request_id=None,
                                org_id=org_id
                            )
                            if success:
                                logger.info(f"Deducted {actual_cost:.6f} credits from org {used_org_id} for streaming request")
                        else:
                            # Individual billing
                            await credit_system.debit_credits(
                                user_id=user_id,
                                amount=actual_cost,
                                metadata={
                                    'provider': provider_used,
                                    'model': provider_used,
                                    'tokens_used': tokens_for_billing,
                                    'power_level': power_level,
                                    'task_type': request.task_type,
                                    'cost': actual_cost,
                                    'streaming': True
                                }
                            )
                            logger.info(f"Deducted {actual_cost:.6f} credits from user {user_id} for streaming request")

                        # Track usage event
                        try:
                            from decimal import Decimal
                            await usage_meter.track_usage(
                                user_id=user_id,
                                service="litellm",
                                model=provider_used,
                                tokens=tokens_for_billing,
                                cost=Decimal(str(actual_cost)),  # FIX: Convert float to Decimal
                                is_free=False,
                                metadata={
                                    'power_level': power_level,
                                    'task_type': request.task_type,
                                    'streaming': True
                                }
                            )
                        except Exception as usage_error:
                            logger.error(f"Failed to track streaming usage: {usage_error}")

                except Exception as stream_error:
                    logger.error(f"Streaming error: {stream_error}", exc_info=True)
                    error_data = {
                        "error": {
                            "message": f"Streaming error: {str(stream_error)}",
                            "type": "internal_error"
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"

            # Return streaming response with aggressive anti-buffering headers
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "X-Accel-Buffering": "no",  # Disable nginx buffering
                    "Connection": "keep-alive",  # Keep connection open
                    "Transfer-Encoding": "chunked",  # Force chunked encoding
                    "Pragma": "no-cache",  # HTTP/1.0 compatibility
                    "Expires": "0"  # Prevent caching
                }
            )

        else:
            # NON-STREAMING PATH: Return complete JSON response
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    json=proxy_request,
                    headers=headers
                )

                if response.status_code != 200:
                    logger.error(f"OpenRouter API error: {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"LLM provider error: {response.text}"
                    )

                # Log response details for debugging
                logger.info(f"OpenRouter response status: {response.status_code}")
                logger.info(f"OpenRouter response headers: {dict(response.headers)}")
                logger.info(f"OpenRouter response content length: {len(response.content)} bytes")
                logger.info(f"OpenRouter response text preview: {response.text[:500]}")

                # Try to parse JSON with better error handling
                try:
                    response_data = response.json()
                except Exception as json_error:
                    logger.error(f"Failed to parse OpenRouter response as JSON: {json_error}")
                    logger.error(f"Raw response text: {response.text}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Invalid response from LLM provider: {str(json_error)}"
                    )

        # Extract usage information (non-streaming only)
        usage = response_data.get('usage', {})
        tokens_used = usage.get('total_tokens', estimated_tokens)
        provider_used = response_data.get('model', 'unknown')

        # Calculate actual cost (ASYNC NOW)
        actual_cost = await credit_system.calculate_cost(
            tokens_used=tokens_used,
            model=provider_used,
            power_level=power_level,
            user_tier=user_tier
        )

        # Debit credits (skip if using BYOK - user pays provider directly)
        if using_byok:
            # User is using their own API key - no credit charge
            if org_id:
                # Get org balance for display
                _, _, new_balance = await get_org_credit_integration().get_user_org_credits(
                    user_id=user_id,
                    request_state=getattr(request, 'state', None) if hasattr(request, 'state') else None
                )
                new_balance = new_balance / 1000.0 if new_balance else 0.0  # Convert milicredits to credits
            else:
                new_balance = await credit_system.get_user_credits(user_id)
            transaction_id = None
            actual_cost = 0.0  # No cost to user's credit balance
            logger.info(f"BYOK request for {user_id} - no credits charged")
        elif user_tier != 'free' or actual_cost > 0:
            # Check if using org billing or individual billing
            if org_id:
                # Using organization billing
                success, used_org_id, remaining_credits = await get_org_credit_integration().deduct_org_credits(
                    user_id=user_id,
                    credits_used=actual_cost,
                    service_name=provider_used,
                    provider=provider_used,
                    model=request.model,
                    tokens_used=tokens_used,
                    power_level=power_level,
                    task_type=request.task_type,
                    request_id=None,  # Could add request tracking here
                    org_id=org_id
                )

                if success:
                    new_balance = remaining_credits / 1000.0 if remaining_credits else 0.0  # Convert to credits
                    transaction_id = f"org-{used_org_id}-{user_id}"
                    logger.info(f"Deducted {actual_cost:.6f} credits from org {used_org_id} for user {user_id}")
                else:
                    logger.error(f"Failed to deduct org credits for user {user_id}")
                    raise HTTPException(status_code=500, detail="Failed to deduct credits")
            else:
                # Using individual credits - charge credits
                new_balance, transaction_id = await credit_system.debit_credits(
                    user_id=user_id,
                    amount=actual_cost,
                    metadata={
                        'provider': provider_used,
                        'model': provider_used,
                        'tokens_used': tokens_used,
                        'power_level': power_level,
                        'task_type': request.task_type,
                        'cost': actual_cost
                    }
                )
        else:
            # Free tier with free model
            if org_id:
                _, _, new_balance = await get_org_credit_integration().get_user_org_credits(
                    user_id=user_id,
                    request_state=getattr(request, 'state', None) if hasattr(request, 'state') else None
                )
                new_balance = new_balance / 1000.0 if new_balance else 0.0
            else:
                new_balance = await credit_system.get_user_credits(user_id)
            transaction_id = None

        # Track usage event (Epic 1.8: Usage Metering)
        try:
            from decimal import Decimal
            await usage_meter.track_usage(
                user_id=user_id,
                service="litellm",
                model=provider_used,
                tokens=tokens_used,
                cost=Decimal(str(actual_cost)),  # FIX: Convert float to Decimal
                is_free=(user_tier == 'free' and actual_cost == 0),
                metadata={
                    'power_level': power_level,
                    'task_type': request.task_type,
                    'privacy_required': request.privacy_required,
                    'provider': provider_used,
                    'transaction_id': transaction_id
                }
            )
        except Exception as usage_error:
            # Log error but don't fail the request
            logger.error(f"Failed to track usage: {usage_error}")

        # Add custom headers to response
        response_data['_metadata'] = {
            'provider_used': provider_used,
            'cost_incurred': actual_cost,
            'credits_remaining': new_balance,
            'transaction_id': transaction_id,
            'power_level': power_level,
            'user_tier': user_tier,
            'using_byok': using_byok,
            'byok_provider': detected_provider if using_byok else None
        }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat completion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ============================================================================
# Image Generation Endpoint
# ============================================================================

def calculate_image_cost(model: str, size: str, quality: str, n: int, user_tier: str) -> float:
    """
    Calculate cost for image generation based on model, size, quality, and tier

    Pricing based on OpenAI/OpenRouter rates (in credits, where 1 credit = $0.001):
    - DALL-E 3: 40 credits (standard 1024x1024), 80 credits (HD 1024x1024)
    - DALL-E 2: 16 credits (512x512), 18 credits (1024x1024)
    - Stable Diffusion: 2-5 credits (varies by size)
    """
    # Base costs per image in dollars
    base_costs = {
        'dall-e-3': {
            'standard': {'1024x1024': 0.040, '1792x1024': 0.080, '1024x1792': 0.080},
            'hd': {'1024x1024': 0.080, '1792x1024': 0.120, '1024x1792': 0.120}
        },
        'dall-e-2': {
            'standard': {'256x256': 0.016, '512x512': 0.016, '1024x1024': 0.018}
        },
        'stable-diffusion-xl': {
            'standard': {'512x512': 0.002, '1024x1024': 0.005, '1536x1536': 0.008}
        },
        'stable-diffusion-3': {
            'standard': {'512x512': 0.003, '1024x1024': 0.006, '1536x1536': 0.010}
        }
    }

    # Normalize model name
    model_lower = model.lower() if model else 'dall-e-3'

    # Detect model family
    if 'dall-e-3' in model_lower or 'dalle-3' in model_lower:
        model_family = 'dall-e-3'
    elif 'dall-e-2' in model_lower or 'dalle-2' in model_lower:
        model_family = 'dall-e-2'
    elif 'stable-diffusion-xl' in model_lower or 'sdxl' in model_lower:
        model_family = 'stable-diffusion-xl'
    elif 'stable-diffusion-3' in model_lower or 'sd3' in model_lower:
        model_family = 'stable-diffusion-3'
    else:
        model_family = 'dall-e-3'  # Default

    # Get base cost
    quality_key = quality if quality in ['standard', 'hd'] else 'standard'

    if model_family not in base_costs:
        model_family = 'dall-e-3'

    if quality_key not in base_costs[model_family]:
        quality_key = 'standard'

    if size not in base_costs[model_family][quality_key]:
        size = '1024x1024'  # Default size

    cost_per_image = base_costs[model_family][quality_key][size]

    # Tier multipliers
    tier_multipliers = {
        'free': 1.5,        # 50% markup for free tier
        'byok': 1.0,        # No markup (BYOK users pay provider directly)
        'managed': 1.2,     # 20% markup for managed tier
        'vip_founder': 1.0  # No markup for VIP founders
    }

    multiplier = tier_multipliers.get(user_tier, 1.2)

    # Total cost in dollars
    total_cost_dollars = cost_per_image * n * multiplier

    # Convert to credits (1 credit = $0.001)
    total_cost_credits = total_cost_dollars * 1000

    return total_cost_credits


@router.post("/image/generations", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest,
    user_id: str = Depends(get_user_id),
    credit_system: CreditSystem = Depends(get_credit_system),
    byok_manager: BYOKManager = Depends(get_byok_manager)
):
    """
    OpenAI-compatible image generation endpoint (Updated Nov 2025)

    Supports multiple providers:
    - OpenAI GPT Image 1 / GPT Image 1 Mini (replaces DALL-E 3)
    - OpenAI DALL-E 3 (still supported, being phased out)
    - Google Gemini 2.5 Flash Image Preview "Nano Banana" (via OpenRouter)
    - Google Imagen 3 (direct via Gemini API)
    - OpenRouter (added image support Aug 2025)
    - Stable Diffusion (via OpenRouter)

    Usage:
        POST /api/v1/llm/image/generations
        {
            "prompt": "A cute cat wearing a wizard hat",
            "model": "gpt-image-1",  # or "dall-e-3", "gemini-2.5-flash-image", "imagen-3"
            "size": "1024x1024",
            "quality": "high",  # GPT Image 1: low/medium/high; DALL-E 3: standard/hd
            "n": 1
        }

    Returns:
        OpenAI-compatible response with image URLs

    Credits (Nov 2025):
        - GPT Image 1 (high quality): ~50 credits
        - GPT Image 1 Mini: ~15 credits
        - DALL-E 3 (standard 1024x1024): ~40 credits
        - Gemini 2.5 Flash Image (Nano Banana): ~35 credits
        - Imagen 3: ~30 credits ($0.03 per image)
        - Stable Diffusion XL: ~2-5 credits
    """
    try:
        # Validate model (default to gpt-image-1, the latest Nov 2025 model)
        model = request.model or "gpt-image-1"

        # Get user tier for cost calculation
        user_tier = await credit_system.get_user_tier(user_id)

        # Check if user has BYOK for image generation providers
        user_keys = await byok_manager.get_all_user_keys(user_id)

        # Determine BYOK routing
        using_byok = False
        user_byok_key = None
        detected_provider = None

        # UPDATED Nov 2025: OpenRouter now supports image generation!
        # Detect model type and available BYOK keys
        is_openai_model = any(x in model.lower() for x in ['dall-e', 'dalle', 'gpt-image'])
        is_gemini_model = any(x in model.lower() for x in ['gemini', 'imagen', 'nano-banana'])

        if is_openai_model and 'openai' in user_keys:
            # OpenAI models (GPT Image 1, DALL-E 3) with OpenAI BYOK
            using_byok = True
            user_byok_key = user_keys['openai']
            detected_provider = 'openai'
            logger.info(f"User {user_id} using OpenAI BYOK for {model}")
        elif is_gemini_model and 'gemini' in user_keys:
            # Gemini models (Imagen 3, Nano Banana) with Gemini BYOK
            using_byok = True
            user_byok_key = user_keys['gemini']
            detected_provider = 'gemini'
            logger.info(f"User {user_id} using Gemini BYOK for {model}")
        elif 'openrouter' in user_keys:
            # OpenRouter BYOK - now supports image generation (Aug 2025)
            using_byok = True
            user_byok_key = user_keys['openrouter']
            detected_provider = 'openrouter'
            logger.info(f"User {user_id} using OpenRouter BYOK for image generation: {model}")

        # Calculate estimated cost
        estimated_cost = calculate_image_cost(
            model=model,
            size=request.size,
            quality=request.quality,
            n=request.n,
            user_tier=user_tier
        )

        # Check credits BEFORE making request (skip if using BYOK)
        org_id = None  # Will be set if using org billing
        if not using_byok and user_tier != 'free':
            # Try organizational billing first
            org_integration = get_org_credit_integration()
            has_org_credits, org_id, message = await org_integration.has_sufficient_org_credits(
                user_id=user_id,
                credits_needed=estimated_cost,
                request_state=getattr(request, 'state', None) if hasattr(request, 'state') else None
            )

            if org_id:
                # User belongs to organization - use org billing
                if not has_org_credits:
                    raise HTTPException(
                        status_code=402,
                        detail=f"Insufficient organization credits for image generation. {message}"
                    )
                logger.info(f"User {user_id} using org billing for image generation (org: {org_id})")
            else:
                # Fallback to individual credits
                current_balance = await credit_system.get_user_credits(user_id)

                if current_balance < estimated_cost:
                    raise HTTPException(
                        status_code=402,
                        detail=f"Insufficient credits. Balance: {current_balance:.2f}, Estimated cost: {estimated_cost:.2f} credits"
                    )

                # Check monthly cap
                within_cap = await credit_system.check_monthly_cap(user_id, estimated_cost)
                if not within_cap:
                    raise HTTPException(
                        status_code=429,
                        detail="Monthly spending cap exceeded"
                    )
                logger.info(f"User {user_id} using individual billing for image generation")

        # Prepare request for provider API
        image_request = {
            "prompt": request.prompt,
            "model": model,
            "n": request.n,
            "size": request.size,
            "response_format": request.response_format
        }

        # Add optional parameters
        if request.quality and 'dall-e-3' in model.lower():
            image_request["quality"] = request.quality
        if request.style and 'dall-e-3' in model.lower():
            image_request["style"] = request.style

        # Determine API endpoint and headers based on BYOK or system key
        if using_byok:
            logger.info(f"Using BYOK for image generation: {user_id} with provider {detected_provider}")

            if detected_provider == 'openai':
                # OpenAI: GPT Image 1, DALL-E 3
                base_url = 'https://api.openai.com/v1'
                api_key = user_byok_key
                provider_name = 'OpenAI'
                use_openrouter_format = False

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            elif detected_provider == 'gemini':
                # Gemini: Imagen 3, Nano Banana
                base_url = 'https://generativelanguage.googleapis.com/v1beta'
                api_key = user_byok_key
                provider_name = 'Gemini'
                use_openrouter_format = False

                headers = {
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key  # Gemini uses header instead of Bearer
                }
            elif detected_provider == 'openrouter':
                # OpenRouter: NEW image generation support (Aug 2025)
                # Uses /chat/completions with modalities parameter
                base_url = 'https://openrouter.ai/api/v1'
                api_key = user_byok_key
                provider_name = 'OpenRouter'
                use_openrouter_format = True  # Different endpoint/format

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": os.getenv('APP_URL', 'http://localhost:8084'),
                    "X-Title": os.getenv('APP_TITLE', 'Ops Center')
                }
            else:
                # Should never reach here
                raise HTTPException(
                    status_code=500,
                    detail=f"Unexpected provider {detected_provider} for BYOK image generation"
                )

        else:
            # Using system key (charge credits)
            logger.info(f"Using system key for image generation: {user_id}")

            system_key_manager = SystemKeyManager(credit_system.db_pool, BYOK_ENCRYPTION_KEY)

            # UPDATED Nov 2025: Smart routing based on model type
            # OpenAI models (GPT Image, DALL-E) → OpenAI API
            # Gemini models (Imagen, Nano Banana) → Gemini API or OpenRouter
            # Other models → OpenRouter (now supports images via /chat/completions)
            is_openai_model = any(x in model.lower() for x in ['dall-e', 'dalle', 'gpt-image'])
            is_gemini_model = any(x in model.lower() for x in ['gemini', 'imagen', 'nano-banana'])

            if is_openai_model:
                # OpenAI models (GPT Image 1, DALL-E 3) go to OpenAI API
                logger.info(f"Routing {model} to OpenAI API")

                async with credit_system.db_pool.acquire() as conn:
                    provider = await conn.fetchrow("""
                        SELECT id, name, type, api_key_encrypted, config
                        FROM llm_providers
                        WHERE enabled = true AND type = 'openai'
                        ORDER BY priority DESC
                        LIMIT 1
                    """)

                    if not provider:
                        raise HTTPException(
                            status_code=503,
                            detail="No OpenAI provider configured. GPT Image/DALL-E requires OpenAI API. Please configure OpenAI in Platform Settings."
                        )

                    provider_db_config = provider['config'] or {}
                    if isinstance(provider_db_config, str):
                        provider_db_config = json.loads(provider_db_config)

                    base_url = provider_db_config.get('base_url', 'https://api.openai.com/v1')
                    provider_name = provider['name']

                    api_key = await system_key_manager.get_system_key(provider['id'])
                    if not api_key:
                        api_key = provider['api_key_encrypted']
                        if not api_key:
                            raise HTTPException(
                                status_code=503,
                                detail="No API key configured for OpenAI provider."
                            )

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                use_openrouter_format = False

                # Don't need to prefix model for OpenAI direct
                # image_request["model"] already contains the model name

            elif is_gemini_model:
                # Gemini models (Imagen 3, Nano Banana) - try Gemini API first
                logger.info(f"Routing {model} to Gemini API")

                async with credit_system.db_pool.acquire() as conn:
                    provider = await conn.fetchrow("""
                        SELECT id, name, type, api_key_encrypted, config
                        FROM llm_providers
                        WHERE enabled = true AND type = 'gemini'
                        ORDER BY priority DESC
                        LIMIT 1
                    """)

                    if not provider:
                        raise HTTPException(
                            status_code=503,
                            detail="No Gemini provider configured. Imagen/Nano Banana requires Gemini API. Please configure Gemini in Platform Settings."
                        )

                    provider_db_config = provider['config'] or {}
                    if isinstance(provider_db_config, str):
                        provider_db_config = json.loads(provider_db_config)

                    base_url = provider_db_config.get('base_url', 'https://generativelanguage.googleapis.com/v1beta')
                    provider_name = provider['name']

                    api_key = await system_key_manager.get_system_key(provider['id'])
                    if not api_key:
                        api_key = provider['api_key_encrypted']
                        if not api_key:
                            raise HTTPException(
                                status_code=503,
                                detail="No API key configured for Gemini provider."
                            )

                headers = {
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key
                }
                use_openrouter_format = False

            else:
                # Other models (Stable Diffusion, Nano Banana via OpenRouter, etc.)
                # OpenRouter NOW supports image generation (Aug 2025)!
                logger.info(f"Routing {model} to OpenRouter for image generation (NEW: supports images as of Aug 2025)")

                async with credit_system.db_pool.acquire() as conn:
                    provider = await conn.fetchrow("""
                        SELECT id, name, type, api_key_encrypted, config
                        FROM llm_providers
                        WHERE enabled = true AND type = 'openrouter'
                        ORDER BY priority DESC
                        LIMIT 1
                    """)

                    if not provider:
                        raise HTTPException(
                            status_code=503,
                            detail="No OpenRouter provider configured. Please configure OpenRouter in Platform Settings."
                        )

                    provider_db_config = provider['config'] or {}
                    if isinstance(provider_db_config, str):
                        provider_db_config = json.loads(provider_db_config)

                    base_url = provider_db_config.get('base_url', 'https://openrouter.ai/api/v1')
                    provider_name = provider['name']

                    api_key = await system_key_manager.get_system_key(provider['id'])
                    if not api_key:
                        api_key = provider['api_key_encrypted']
                        if not api_key:
                            raise HTTPException(
                                status_code=503,
                                detail="No API key configured for OpenRouter provider."
                            )

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": os.getenv('APP_URL', 'http://localhost:8084'),
                    "X-Title": os.getenv('APP_TITLE', 'Ops Center')
                }

                # Prefix model for OpenRouter (e.g., "stable-diffusion-xl" -> "stability-ai/stable-diffusion-xl")
                if not model.startswith("stability-ai/") and not model.startswith("openai/") and not model.startswith("google/"):
                    image_request["model"] = f"stability-ai/{model}"

                use_openrouter_format = True  # OpenRouter uses different API format

        # Call provider API (UPDATED Nov 2025: Handle OpenRouter's new format)
        async with httpx.AsyncClient(timeout=180.0) as client:
            if use_openrouter_format:
                # OpenRouter: Uses /chat/completions with modalities (added Aug 2025)
                logger.info(f"Using OpenRouter image generation format for model: {model}")

                openrouter_request = {
                    "model": model,
                    "messages": [{"role": "user", "content": request.prompt}],
                    "modalities": ["image", "text"],  # NEW: Enable image generation
                    "n": request.n,
                    "temperature": 1.0  # Default for image generation
                }

                response = await client.post(
                    f"{base_url}/chat/completions",
                    json=openrouter_request,
                    headers=headers
                )

                if response.status_code != 200:
                    logger.error(f"OpenRouter image generation API error: {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"OpenRouter image generation error: {response.text}"
                    )

                openrouter_response = response.json()

                # Convert OpenRouter response to OpenAI format
                # OpenRouter returns images in: choices[0].message.images[]
                if "choices" in openrouter_response and len(openrouter_response["choices"]) > 0:
                    message = openrouter_response["choices"][0].get("message", {})
                    images = message.get("images", [])

                    if images:
                        # Convert to OpenAI format
                        response_data = {
                            "created": openrouter_response.get("created", int(time.time())),
                            "data": [
                                {"b64_json": img} if isinstance(img, str) else img
                                for img in images
                            ]
                        }
                    else:
                        raise HTTPException(
                            status_code=500,
                            detail="OpenRouter returned no images"
                        )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Invalid OpenRouter response format"
                    )

            else:
                # OpenAI/Gemini: Standard /images/generations endpoint
                response = await client.post(
                    f"{base_url}/images/generations",
                    json=image_request,
                    headers=headers
                )

                if response.status_code != 200:
                    logger.error(f"Image generation API error: {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Image generation provider error: {response.text}"
                    )

                response_data = response.json()

        # Calculate actual cost
        actual_cost = estimated_cost

        # Debit credits (skip if using BYOK)
        if using_byok:
            if org_id:
                _, _, new_balance = await get_org_credit_integration().get_user_org_credits(
                    user_id=user_id,
                    request_state=getattr(request, 'state', None) if hasattr(request, 'state') else None
                )
                new_balance = new_balance / 1000.0 if new_balance else 0.0
            else:
                new_balance = await credit_system.get_user_credits(user_id)
            transaction_id = None
            actual_cost = 0.0
            logger.info(f"BYOK image generation for {user_id} - no credits charged")
        elif user_tier != 'free' or actual_cost > 0:
            if org_id:
                # Using organization billing
                success, used_org_id, remaining_credits = await get_org_credit_integration().deduct_org_credits(
                    user_id=user_id,
                    credits_used=actual_cost,
                    service_name=f"image_generation_{model}",
                    provider=provider_name,
                    model=model,
                    tokens_used=0,  # Not applicable for images
                    power_level="standard",
                    task_type="image_generation",
                    request_id=None,
                    org_id=org_id
                )

                if success:
                    new_balance = remaining_credits / 1000.0 if remaining_credits else 0.0
                    transaction_id = f"org-{used_org_id}-{user_id}"
                    logger.info(f"Deducted {actual_cost:.2f} credits from org {used_org_id} for image generation")
                else:
                    logger.error(f"Failed to deduct org credits for image generation")
                    raise HTTPException(status_code=500, detail="Failed to deduct credits")
            else:
                # Using individual credits
                new_balance, transaction_id = await credit_system.debit_credits(
                    user_id=user_id,
                    amount=actual_cost,
                    metadata={
                        'provider': provider_name,
                        'model': model,
                        'image_count': request.n,
                        'size': request.size,
                        'quality': request.quality,
                        'cost': actual_cost
                    }
                )
        else:
            if org_id:
                _, _, new_balance = await get_org_credit_integration().get_user_org_credits(
                    user_id=user_id,
                    request_state=getattr(request, 'state', None) if hasattr(request, 'state') else None
                )
                new_balance = new_balance / 1000.0 if new_balance else 0.0
            else:
                new_balance = await credit_system.get_user_credits(user_id)
            transaction_id = None

        # Track usage event
        try:
            from decimal import Decimal
            await usage_meter.track_usage(
                user_id=user_id,
                service="image_generation",
                model=model,
                tokens=0,
                cost=Decimal(str(actual_cost)),  # FIX: Convert float to Decimal
                is_free=(user_tier == 'free' and actual_cost == 0),
                metadata={
                    'image_count': request.n,
                    'size': request.size,
                    'quality': request.quality,
                    'provider': provider_name if not using_byok else detected_provider,
                    'transaction_id': transaction_id,
                    'using_byok': using_byok
                }
            )
        except Exception as usage_error:
            logger.error(f"Failed to track image generation usage: {usage_error}")

        # Add metadata to response
        response_data['_metadata'] = {
            'provider_used': provider_name if not using_byok else detected_provider,
            'cost_incurred': actual_cost,
            'credits_remaining': new_balance,
            'transaction_id': transaction_id,
            'user_tier': user_tier,
            'using_byok': using_byok,
            'byok_provider': detected_provider if using_byok else None,
            'images_generated': request.n,
            'size': request.size,
            'quality': request.quality
        }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ============================================================================
# Credit Management Endpoints
# ============================================================================

@router.get("/credits", response_model=CreditResponse)
async def get_credits(
    user_id: str = Depends(get_user_id),
    credit_system: CreditSystem = Depends(get_credit_system)
):
    """Get current credit balance"""
    try:
        balance = await credit_system.get_user_credits(user_id)
        tier = await credit_system.get_user_tier(user_id)

        return {
            'user_id': user_id,
            'credits_remaining': balance,
            'tier': tier,
            'monthly_cap': None  # TODO: fetch from database
        }

    except Exception as e:
        logger.error(f"Error getting credits: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve credits")


@router.post("/credits/purchase")
async def purchase_credits(
    purchase: CreditPurchaseRequest,
    user_id: str = Depends(get_user_id),
    credit_system: CreditSystem = Depends(get_credit_system)
):
    """
    Purchase credits via Stripe

    Credit packages:
    - $10 = 10,000 credits
    - $50 = 55,000 credits (10% bonus)
    - $100 = 120,000 credits (20% bonus)
    """
    try:
        # Validate amount
        valid_amounts = {10.0: 10000, 50.0: 55000, 100.0: 120000}

        if purchase.amount not in valid_amounts:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid amount. Valid amounts: {list(valid_amounts.keys())}"
            )

        credits_to_add = valid_amounts[purchase.amount]

        # Create Stripe charge
        try:
            charge = stripe.Charge.create(
                amount=int(purchase.amount * 100),  # Convert to cents
                currency='usd',
                source=purchase.stripe_token,
                description=f"Credit purchase: {credits_to_add} credits",
                metadata={
                    'user_id': user_id,
                    'credits': credits_to_add
                }
            )

            if charge.status != 'succeeded':
                raise HTTPException(status_code=402, detail="Payment failed")

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise HTTPException(status_code=402, detail=f"Payment error: {str(e)}")

        # Add credits to account
        new_balance = await credit_system.credit_credits(
            user_id=user_id,
            amount=credits_to_add,
            reason="purchase"
        )

        return {
            'success': True,
            'credits_added': credits_to_add,
            'new_balance': new_balance,
            'transaction_id': charge.id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Purchase error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Purchase failed")


@router.get("/credits/history")
async def get_credit_history(
    limit: int = 100,
    offset: int = 0,
    user_id: str = Depends(get_user_id),
    credit_system: CreditSystem = Depends(get_credit_system)
):
    """Get credit transaction history"""
    try:
        history = await credit_system.get_credit_history(
            user_id=user_id,
            limit=min(limit, 1000),  # Cap at 1000
            offset=offset
        )

        return {
            'transactions': history,
            'total': len(history),
            'limit': limit,
            'offset': offset
        }

    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")


# ============================================================================
# Model & Usage Endpoints
# ============================================================================

# Curated models list - best FREE models from OpenRouter (updated Nov 2025)
CURATED_MODELS = [
    # Coding specialists
    {
        'id': 'qwen/qwen3-coder:free',
        'object': 'model',
        'name': 'Qwen3 Coder (FREE)',
        'provider': 'OpenRouter',
        'context_length': 262144,
        'category': 'coding',
        'description': 'Best FREE coding model - 262K context, 480B params, excellent for development',
        'free': True
    },
    {
        'id': 'deepseek/deepseek-r1:free',
        'object': 'model',
        'name': 'DeepSeek R1 (FREE)',
        'provider': 'OpenRouter',
        'context_length': 163840,
        'category': 'reasoning',
        'description': 'FREE reasoning model with chain-of-thought - great for coding and analysis',
        'free': True
    },
    # General purpose - fast
    {
        'id': 'google/gemini-2.0-flash-exp:free',
        'object': 'model',
        'name': 'Gemini 2.0 Flash (FREE)',
        'provider': 'OpenRouter',
        'context_length': 1048576,
        'category': 'general',
        'description': 'Ultra-fast with 1M context window - best for large documents',
        'free': True
    },
    {
        'id': 'mistralai/mistral-small-3.2-24b-instruct:free',
        'object': 'model',
        'name': 'Mistral Small 3.2 (FREE)',
        'provider': 'OpenRouter',
        'context_length': 131072,
        'category': 'fast',
        'description': 'Fast and efficient - 128K context, great for quick tasks',
        'free': True
    },
    # Large models
    {
        'id': 'meta-llama/llama-3.3-70b-instruct:free',
        'object': 'model',
        'name': 'Llama 3.3 70B (FREE)',
        'provider': 'OpenRouter',
        'context_length': 131072,
        'category': 'general',
        'description': 'Meta\'s flagship 70B model - excellent quality, 128K context',
        'free': True
    },
    {
        'id': 'nousresearch/hermes-3-llama-3.1-405b:free',
        'object': 'model',
        'name': 'Hermes 3 405B (FREE)',
        'provider': 'OpenRouter',
        'context_length': 131072,
        'category': 'general',
        'description': 'Massive 405B model - best quality for complex tasks',
        'free': True
    },
    # Specialized
    {
        'id': 'deepseek/deepseek-chat-v3.1',
        'object': 'model',
        'name': 'DeepSeek Chat v3.1',
        'provider': 'OpenRouter',
        'context_length': 131072,
        'category': 'general',
        'description': 'DeepSeek\'s latest chat model - excellent for presentations and content',
        'free': False
    },
    {
        'id': 'nvidia/nemotron-nano-9b-v2:free',
        'object': 'model',
        'name': 'NVIDIA Nemotron Nano (FREE)',
        'provider': 'OpenRouter',
        'context_length': 128000,
        'category': 'fast',
        'description': 'NVIDIA\'s efficient 9B model - fast inference',
        'free': True
    },
    {
        'id': 'google/gemini-2.5-pro-exp-03-25:free',
        'object': 'model',
        'name': 'Gemini 2.5 Pro (FREE)',
        'provider': 'OpenRouter',
        'context_length': 1048576,
        'category': 'general',
        'description': 'Google\'s most capable model - 1M context, multi-modal',
        'free': True
    },
    {
        'id': 'anthropic/claude-3.5-haiku:free',
        'object': 'model',
        'name': 'Claude 3.5 Haiku (FREE)',
        'provider': 'OpenRouter',
        'context_length': 200000,
        'category': 'fast',
        'description': 'Anthropic\'s fast model - 200K context, excellent quality',
        'free': True
    }
]


async def get_curated_models_from_db(request: Request, app_slug: str = None, user_tier: str = None):
    """Fetch curated models from database for the specified app."""
    try:
        db_pool = request.app.state.db_pool
        if not db_pool:
            return None

        async with db_pool.acquire() as conn:
            list_row = None

            # Find the list (app-specific or global)
            if app_slug:
                list_query = """
                    SELECT id, name, slug FROM app_model_lists
                    WHERE (slug = $1 OR app_identifier = $1) AND is_active = TRUE
                    ORDER BY is_default DESC LIMIT 1
                """
                list_row = await conn.fetchrow(list_query, app_slug)

            if not list_row:
                # Fall back to global list
                list_query = "SELECT id, name, slug FROM app_model_lists WHERE slug = 'global' AND is_active = TRUE"
                list_row = await conn.fetchrow(list_query)

            if not list_row:
                return None  # No database list, use hardcoded

            # Get models from the list
            models_query = """
                SELECT model_id, display_name, description, category, is_free, context_length,
                       tier_trial, tier_starter, tier_professional, tier_enterprise,
                       tier_vip_founder, tier_byok
                FROM app_model_list_items
                WHERE list_id = $1
                ORDER BY sort_order ASC
            """

            rows = await conn.fetch(models_query, list_row['id'])

            models = []
            for row in rows:
                # Apply tier filtering if specified
                if user_tier:
                    tier_col_name = f"tier_{user_tier.replace('-', '_').replace(' ', '_').lower()}"
                    tier_enabled = True
                    if tier_col_name == 'tier_trial':
                        tier_enabled = row['tier_trial']
                    elif tier_col_name == 'tier_starter':
                        tier_enabled = row['tier_starter']
                    elif tier_col_name == 'tier_professional':
                        tier_enabled = row['tier_professional']
                    elif tier_col_name == 'tier_enterprise':
                        tier_enabled = row['tier_enterprise']
                    elif tier_col_name == 'tier_vip_founder':
                        tier_enabled = row['tier_vip_founder']
                    elif tier_col_name == 'tier_byok':
                        tier_enabled = row['tier_byok']

                    if not tier_enabled:
                        continue

                models.append({
                    'id': row['model_id'],
                    'object': 'model',
                    'name': row['display_name'] or row['model_id'],
                    'provider': 'OpenRouter',
                    'context_length': row['context_length'] or 32768,
                    'category': row['category'] or 'general',
                    'description': row['description'],
                    'free': row['is_free'] if row['is_free'] is not None else False
                })

            return models

    except Exception as e:
        logger.error(f"Error fetching curated models from database: {e}")
        return None


@router.get("/models/curated")
async def list_curated_models(
    request: Request,
    app: Optional[str] = Query(None, description="App identifier (bolt-diy, presenton, open-webui)"),
    tier: Optional[str] = Query(None, description="User tier for filtering")
):
    """
    List curated models - the best FREE and recommended models.

    Supports app-specific lists (bolt-diy, presenton, open-webui) and tier filtering.

    Returns a curated list of high-quality models that are:
    - FREE to use (no credits charged)
    - High performance
    - Suitable for various use cases (coding, general, fast)

    Use these models as the default for "Unicorn Commander (Curated)" provider.
    For access to all 1,300+ models, use /models/categorized endpoint.
    """
    try:
        # Try to get from database first
        db_models = await get_curated_models_from_db(request, app, tier)

        if db_models is not None and len(db_models) > 0:
            models = db_models
            source = 'database'
        else:
            # Fall back to hardcoded CURATED_MODELS
            models = CURATED_MODELS
            source = 'hardcoded'

        # Group models by category
        by_category = {}
        for model in models:
            category = model.get('category', 'general')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(model)

        # Count FREE models
        free_count = sum(1 for m in models if m.get('free', False))

        return {
            'object': 'list',
            'data': models,
            'by_category': by_category,
            'app': app,
            'source': source,
            'summary': {
                'total': len(models),
                'free_count': free_count,
                'categories': list(by_category.keys()),
                'last_updated': datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Error listing curated models: {e}")
        raise HTTPException(status_code=500, detail="Failed to list curated models")


@router.get("/models")
async def list_models(
    user_id: str = Depends(get_user_id),
    credit_system: CreditSystem = Depends(get_credit_system)
):
    """
    List available models based on user tier

    Returns OpenAI-compatible model list
    """
    try:
        tier = await credit_system.get_user_tier(user_id)

        # Define models by tier
        models_by_tier = {
            'free': [
                {'id': 'llama3-8b-local', 'object': 'model', 'owned_by': 'local', 'tier': 'free'},
                {'id': 'qwen-32b-local', 'object': 'model', 'owned_by': 'local', 'tier': 'free'},
                {'id': 'llama3-70b-groq', 'object': 'model', 'owned_by': 'groq', 'tier': 'free'},
                {'id': 'mixtral-8x7b-hf', 'object': 'model', 'owned_by': 'huggingface', 'tier': 'free'},
            ],
            'starter': [
                {'id': 'mixtral-8x22b-together', 'object': 'model', 'owned_by': 'together', 'tier': 'starter'},
                {'id': 'llama3-70b-deepinfra', 'object': 'model', 'owned_by': 'deepinfra', 'tier': 'starter'},
                {'id': 'qwen-72b-fireworks', 'object': 'model', 'owned_by': 'fireworks', 'tier': 'starter'},
            ],
            'professional': [
                {'id': 'claude-3.5-sonnet-openrouter', 'object': 'model', 'owned_by': 'openrouter', 'tier': 'professional'},
                {'id': 'gpt-4o-openrouter', 'object': 'model', 'owned_by': 'openrouter', 'tier': 'professional'},
            ],
            'enterprise': [
                {'id': 'claude-3.5-sonnet', 'object': 'model', 'owned_by': 'anthropic', 'tier': 'enterprise'},
                {'id': 'gpt-4o', 'object': 'model', 'owned_by': 'openai', 'tier': 'enterprise'},
            ]
        }

        # Collect all models up to user's tier
        tier_order = ['free', 'starter', 'professional', 'enterprise']
        user_tier_index = tier_order.index(tier) if tier in tier_order else 0

        available_models = []
        for i in range(user_tier_index + 1):
            available_models.extend(models_by_tier.get(tier_order[i], []))

        return {
            'object': 'list',
            'data': available_models
        }

    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail="Failed to list models")


def get_model_pricing(model_id: str, model_info: dict, tier_markup: float) -> dict:
    """
    Calculate model pricing with tier-based markup

    Args:
        model_id: Model identifier
        model_info: Model metadata including pricing
        tier_markup: Tier markup percentage (0-100)

    Returns:
        Dict with: credits_per_1k_input, credits_per_1k_output, tier_markup, display
    """
    try:
        logger.info(f"[PRICING DEBUG] Calculating for {model_id}, markup: {tier_markup}%")

        # Get base costs from OpenRouter pricing data (already per-token)
        pricing_data = model_info.get('pricing', {})
        logger.info(f"[PRICING DEBUG] pricing_data: {pricing_data}")

        # Base cost is per-token, we want per-1K tokens
        base_input_cost = float(pricing_data.get('prompt', 0)) * 1000
        base_output_cost = float(pricing_data.get('completion', 0)) * 1000

        # If no pricing data, check model_info for pre-calculated values
        if base_input_cost == 0 and base_output_cost == 0:
            base_input_cost = float(model_info.get('cost_per_1m_input', 0)) / 1000  # Convert 1M to 1K
            base_output_cost = float(model_info.get('cost_per_1m_output', 0)) / 1000
            logger.info(f"[PRICING DEBUG] Using cost_per_1m: input={base_input_cost}, output={base_output_cost}")

        # Apply tier markup: final_cost = base_cost * (1 + markup/100)
        markup_multiplier = 1 + (tier_markup / 100)
        final_input_cost = base_input_cost * markup_multiplier
        final_output_cost = base_output_cost * markup_multiplier

        # Convert to credits (1 credit = $0.001)
        credits_per_1k_input = final_input_cost * 1000  # Convert dollars to credits
        credits_per_1k_output = final_output_cost * 1000

        result = {
            'credits_per_1k_input': round(credits_per_1k_input, 4),
            'credits_per_1k_output': round(credits_per_1k_output, 4),
            'tier_markup': tier_markup,
            'display': f"{round(credits_per_1k_input, 2)}/{round(credits_per_1k_output, 2)} credits per 1K tokens"
        }
        logger.info(f"[PRICING DEBUG] Result: {result}")
        return result

    except (ValueError, TypeError, KeyError) as e:
        logger.warning(f"Failed to calculate pricing for {model_id}: {e}")
        return {
            'credits_per_1k_input': 0,
            'credits_per_1k_output': 0,
            'tier_markup': tier_markup,
            'display': 'Pricing unavailable'
        }


@router.get("/models/categorized")
async def list_models_categorized(
    user_id: str = Depends(get_user_id),
    byok_manager: BYOKManager = Depends(get_byok_manager),
    credit_system: CreditSystem = Depends(get_credit_system)
):
    """
    List models categorized by access method (BYOK vs Platform)

    Dynamically fetches models from LiteLLM proxy and categorizes them based on
    user's BYOK providers (OpenRouter, HuggingFace, etc.)

    Returns:
        {
            "byok_models": [...],    # Models using user's API keys (free)
            "platform_models": [...], # Models using platform keys (charged)
            "summary": {...}          # Statistics and provider list
        }
    """
    try:
        # Get user's tier and tier markup percentage
        user_tier = await credit_system.get_user_tier(user_id)

        # Fetch tier markup from database
        tier_markup = 0.0
        try:
            async with credit_system.db_pool.acquire() as conn:
                tier_result = await conn.fetchrow(
                    "SELECT llm_markup_percentage FROM subscription_tiers WHERE tier_code = $1",
                    user_tier
                )
                if tier_result:
                    tier_markup = float(tier_result['llm_markup_percentage'])
                    logger.info(f"User {user_id} tier {user_tier} has markup {tier_markup}%")
        except Exception as e:
            logger.warning(f"Failed to fetch tier markup for {user_tier}: {e}")
            tier_markup = 0.0

        # Get user's BYOK providers
        byok_providers_list = await byok_manager.list_user_providers(user_id)
        byok_provider_names = {p['provider'].lower() for p in byok_providers_list if p.get('enabled')}

        # Fetch models from LiteLLM proxy
        import httpx
        litellm_url = os.getenv("LITELLM_PROXY_URL", "http://uchub-litellm:4000")
        litellm_key = os.getenv("LITELLM_MASTER_KEY", "sk-e75f71c1d931d183e216c9ed6580e56a7be04533fe0729faccc7bcb8fec80375")

        # Get OpenRouter API key for pricing data
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")

        async with httpx.AsyncClient(timeout=15.0) as client:
            # Fetch base model list from LiteLLM
            response = await client.get(
                f"{litellm_url}/v1/models",
                headers={"Authorization": f"Bearer {litellm_key}"}
            )
            response.raise_for_status()
            models_data = response.json()

            # Fetch detailed model info from OpenRouter (pricing, context, descriptions)
            openrouter_models = {}
            try:
                or_response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {openrouter_key}"},  # FIXED: Use correct OpenRouter key
                    timeout=10.0
                )
                if or_response.status_code == 200:
                    or_data = or_response.json()
                    for model in or_data.get('data', []):
                        model_id = model.get('id', '')
                        openrouter_models[model_id] = {
                            'context_length': model.get('context_length', 0),
                            'pricing': model.get('pricing', {}),
                            'description': model.get('description', ''),
                            'architecture': model.get('architecture', {}),
                            'top_provider': model.get('top_provider', {}),
                        }
                    logger.info(f"Fetched metadata for {len(openrouter_models)} OpenRouter models")
            except Exception as e:
                logger.warning(f"Failed to fetch OpenRouter model metadata: {e}")

        # Process models
        all_models = models_data.get('data', [])

        # Group models by provider
        provider_models = {}
        for model in all_models:
            model_id = model.get('id', '')

            # Skip wildcard entries
            if '/*' in model_id or model_id == '*/*':
                continue

            # Determine provider from model ID
            provider = None
            if model_id.startswith('gpt-') or model_id.startswith('o1-'):
                provider = 'openai'
            elif model_id.startswith('claude-'):
                provider = 'anthropic'
            elif model_id.startswith('gemini-'):
                provider = 'google'
            elif model_id.startswith('llama-'):
                provider = 'meta'
            elif model_id.startswith('mistral-') or model_id.startswith('mixtral-'):
                provider = 'mistral'
            elif model_id.startswith('deepseek-'):
                provider = 'deepseek'
            elif '/' in model_id:
                # Format like "openrouter/anthropic/claude-3.5-sonnet"
                parts = model_id.split('/')
                if len(parts) >= 2:
                    provider = parts[0].lower()
            else:
                provider = 'other'

            if provider not in provider_models:
                provider_models[provider] = []

            # Build model info with metadata
            model_info = {
                'id': model_id,
                'object': 'model',
                'name': model_id,
                'display_name': model_id.replace('/', ' / '),
                'created': model.get('created', 0)
            }

            # Add OpenRouter metadata if available
            if model_id in openrouter_models:
                or_meta = openrouter_models[model_id]
                model_info['context_length'] = or_meta.get('context_length', 0)
                model_info['description'] = or_meta.get('description', '')

                # Add pricing info (convert from per-token to per-1M-tokens)
                pricing = or_meta.get('pricing', {})
                if pricing:
                    try:
                        # OpenRouter returns price per token (e.g., "0.000003")
                        # Convert to price per 1M tokens
                        prompt_price = float(pricing.get('prompt', '0'))
                        completion_price = float(pricing.get('completion', '0'))

                        model_info['cost_per_1m_input'] = prompt_price * 1_000_000
                        model_info['cost_per_1m_output'] = completion_price * 1_000_000

                        # Keep raw pricing for reference
                        model_info['pricing'] = {
                            'prompt': pricing.get('prompt', '0'),
                            'completion': pricing.get('completion', '0'),
                            'request': pricing.get('request', '0'),
                            'image': pricing.get('image', '0')
                        }
                    except (ValueError, TypeError):
                        logger.warning(f"Failed to parse pricing for {model_id}")
                        model_info['cost_per_1m_input'] = 0
                        model_info['cost_per_1m_output'] = 0

                # Add architecture info (modality, instruct type)
                arch = or_meta.get('architecture', {})
                if arch:
                    model_info['architecture'] = {
                        'modality': arch.get('modality', 'text'),
                        'tokenizer': arch.get('tokenizer', ''),
                        'instruct_type': arch.get('instruct_type', '')
                    }

            # Add tier-based pricing for platform models
            if model_info.get('pricing') or model_info.get('cost_per_1m_input'):
                tier_pricing = get_model_pricing(model_id, model_info, tier_markup)
                model_info['tier_pricing'] = tier_pricing
                logger.info(f"[PRICING DEBUG] Model {model_id} has tier_pricing: {tier_pricing}")
            else:
                logger.info(f"[PRICING DEBUG] Model {model_id} missing pricing data: pricing={model_info.get('pricing')}, cost_per_1m_input={model_info.get('cost_per_1m_input')}")

            provider_models[provider].append(model_info)

        # Categorize by BYOK vs Platform
        byok_models = []
        platform_models = []

        # Provider display names
        provider_names = {
            'openai': 'OpenAI',
            'anthropic': 'Anthropic',
            'google': 'Google',
            'meta': 'Meta',
            'mistral': 'Mistral AI',
            'deepseek': 'DeepSeek',
            'openrouter': 'OpenRouter',
            'huggingface': 'HuggingFace',
            'cohere': 'Cohere',
            'together': 'Together AI',
            'groq': 'Groq',
            'other': 'Other'
        }

        for provider_key, models_list in provider_models.items():
            if not models_list:
                continue

            provider_display = provider_names.get(provider_key, provider_key.title())
            is_byok = provider_key in byok_provider_names or 'openrouter' in byok_provider_names

            provider_info = {
                'provider': provider_display,
                'provider_type': provider_key,
                'models': models_list,
                'count': len(models_list),
                'tier_markup': tier_markup  # Add tier markup percentage
            }

            if is_byok:
                provider_info['free'] = True
                provider_info['note'] = f"Using your {provider_display} API key - no credits charged"
                provider_info['source'] = 'byok'
                byok_models.append(provider_info)
            else:
                provider_info['note'] = f"Charged with credits from your account (tier markup: {tier_markup}%)"
                provider_info['source'] = 'platform'
                platform_models.append(provider_info)

        # Build summary
        total_byok = sum(p['count'] for p in byok_models)
        total_platform = sum(p['count'] for p in platform_models)

        return {
            'byok_models': byok_models,
            'platform_models': platform_models,
            'summary': {
                'total_models': total_byok + total_platform,
                'byok_count': total_byok,
                'platform_count': total_platform,
                'has_byok_keys': len(byok_provider_names) > 0,
                'byok_providers': list(byok_provider_names)
            }
        }

    except Exception as e:
        logger.error(f"Error categorizing models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to categorize models: {str(e)}")


@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(
    days: int = 30,
    user_id: str = Depends(get_user_id),
    credit_system: CreditSystem = Depends(get_credit_system)
):
    """Get usage statistics"""
    try:
        stats = await credit_system.get_usage_stats(user_id, days=days)
        return stats

    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve usage statistics")


# ============================================================================
# BYOK Endpoints
# ============================================================================

@router.post("/byok/keys")
async def add_byok_key(
    request: AddBYOKKeyRequest,
    user_id: str = Depends(get_user_id),
    byok_manager: BYOKManager = Depends(get_byok_manager)
):
    """
    Add or update a BYOK key

    This endpoint validates the API key format and optionally tests it
    against the provider's API before storing.

    Args:
        request: BYOK key information (provider, api_key, metadata)

    Returns:
        Success message with key ID and test results

    Raises:
        400: Invalid provider or key format
        503: API test failed (warning only, still stores key)
    """
    try:
        # Validate key format
        is_valid = await byok_manager.validate_api_key(
            user_id=user_id,
            provider=request.provider,
            api_key=request.api_key
        )

        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid API key format for {request.provider}"
            )

        # Optional: Test key before storing (recommended but non-blocking)
        test_result = None
        try:
            test_result = await test_provider_api_key(request.provider, request.api_key)
            if not test_result.get('success'):
                logger.warning(
                    f"BYOK test failed for {user_id}/{request.provider}: {test_result.get('message')}"
                )
                # Store anyway but include warning in response
        except Exception as test_error:
            logger.warning(f"BYOK test error for {user_id}/{request.provider}: {test_error}")
            # Continue storing even if test fails

        # Store key
        key_id = await byok_manager.store_user_api_key(
            user_id=user_id,
            provider=request.provider,
            api_key=request.api_key,
            metadata=request.metadata
        )

        logger.info(f"User {user_id} added/updated BYOK key for {request.provider}")

        return {
            'success': True,
            'key_id': key_id,
            'provider': request.provider,
            'message': 'API key stored successfully',
            'test_result': test_result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding BYOK key for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add API key")


@router.get("/byok/keys")
async def list_byok_keys(
    user_id: str = Depends(get_user_id),
    byok_manager: BYOKManager = Depends(get_byok_manager)
):
    """List user's stored provider keys (masked)"""
    try:
        providers = await byok_manager.list_user_providers(user_id)
        return {'providers': providers}

    except Exception as e:
        logger.error(f"Error listing BYOK keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to list keys")


@router.delete("/byok/keys/{provider}")
async def delete_byok_key(
    provider: str,
    user_id: str = Depends(get_user_id),
    byok_manager: BYOKManager = Depends(get_byok_manager)
):
    """Delete user's API key for a provider"""
    try:
        deleted = await byok_manager.delete_user_api_key(user_id, provider)

        if not deleted:
            raise HTTPException(status_code=404, detail="Provider key not found")

        return {'success': True, 'provider': provider}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting BYOK key: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete key")


@router.post("/byok/keys/{provider}/toggle")
async def toggle_byok_key(
    provider: str,
    request: ToggleBYOKRequest,
    user_id: str = Depends(get_user_id),
    byok_manager: BYOKManager = Depends(get_byok_manager)
):
    """
    Enable or disable a BYOK key

    Args:
        provider: Provider name
        request: Toggle request (enabled: true/false)

    Returns:
        New enabled status

    Raises:
        404: Key not found
    """
    try:
        updated = await byok_manager.toggle_provider(user_id, provider, request.enabled)

        if not updated:
            raise HTTPException(
                status_code=404,
                detail=f"No API key found for provider '{provider}'"
            )

        action = "enabled" if request.enabled else "disabled"
        logger.info(f"User {user_id} {action} BYOK key for {provider}")

        return {
            'success': True,
            'provider': provider,
            'enabled': request.enabled,
            'message': f'API key for {provider} {action} successfully'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling BYOK key: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle API key")


# Rate limiting for test endpoint (simple in-memory tracker)
from collections import defaultdict
from time import time as current_time

_test_rate_limits = defaultdict(list)
TEST_RATE_LIMIT = 5  # Max 5 tests per minute
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


async def test_provider_api_key(provider: str, api_key: str) -> Dict:
    """Test API key against provider's API"""

    # Normalize provider name to lowercase for comparison
    provider_lower = provider.lower()

    if provider_lower == 'openrouter':
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    'https://openrouter.ai/api/v1/models',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'HTTP-Referer': os.getenv('APP_URL', 'http://localhost:8084'),
                        'X-Title': os.getenv('APP_TITLE', 'Ops Center')
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    model_count = len(data.get('data', []))
                    return {
                        'success': True,
                        'message': f'Valid OpenRouter key. {model_count} models available.',
                        'model_count': model_count
                    }
                elif response.status_code == 401:
                    return {'success': False, 'message': 'Invalid API key'}
                elif response.status_code == 403:
                    return {'success': False, 'message': 'API key lacks permissions'}
                else:
                    return {'success': False, 'message': f'API error: {response.status_code}'}

        except httpx.TimeoutException:
            return {'success': False, 'message': 'Request timeout'}
        except Exception as e:
            return {'success': False, 'message': f'Test failed: {str(e)}'}

    elif provider_lower == 'openai':
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    'https://api.openai.com/v1/models',
                    headers={'Authorization': f'Bearer {api_key}'}
                )

                if response.status_code == 200:
                    data = response.json()
                    model_count = len(data.get('data', []))
                    return {
                        'success': True,
                        'message': f'Valid OpenAI key. {model_count} models available.',
                        'model_count': model_count
                    }
                elif response.status_code == 401:
                    return {'success': False, 'message': 'Invalid API key'}
                else:
                    return {'success': False, 'message': f'API error: {response.status_code}'}

        except Exception as e:
            return {'success': False, 'message': f'Test failed: {str(e)}'}

    elif provider_lower == 'anthropic':
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    'https://api.anthropic.com/v1/messages',
                    headers={
                        'x-api-key': api_key,
                        'anthropic-version': '2023-06-01',
                        'content-type': 'application/json'
                    },
                    json={
                        'model': 'claude-3-haiku-20240307',
                        'max_tokens': 1,
                        'messages': [{'role': 'user', 'content': 'Hi'}]
                    }
                )

                if response.status_code == 200:
                    return {
                        'success': True,
                        'message': 'Valid Anthropic API key.',
                        'model': 'claude-3-haiku-20240307'
                    }
                elif response.status_code == 401:
                    return {'success': False, 'message': 'Invalid API key'}
                else:
                    return {'success': False, 'message': f'API error: {response.status_code}'}

        except Exception as e:
            return {'success': False, 'message': f'Test failed: {str(e)}'}

    elif provider_lower == 'google':
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'
                )

                if response.status_code == 200:
                    data = response.json()
                    model_count = len(data.get('models', []))
                    return {
                        'success': True,
                        'message': f'Valid Google API key. {model_count} models available.',
                        'model_count': model_count
                    }
                elif response.status_code == 400:
                    return {'success': False, 'message': 'Invalid API key'}
                else:
                    return {'success': False, 'message': f'API error: {response.status_code}'}

        except Exception as e:
            return {'success': False, 'message': f'Test failed: {str(e)}'}

    else:
        return {'success': False, 'message': f'Testing not supported for provider: {provider}'}


@router.post("/byok/keys/{provider}/test")
async def test_byok_key(
    provider: str,
    user_id: str = Depends(get_user_id),
    byok_manager: BYOKManager = Depends(get_byok_manager)
):
    """
    Test a BYOK key against provider API

    Rate Limited: 5 tests per minute per user

    Args:
        provider: Provider name to test

    Returns:
        Test results with success status and details
    """
    try:
        # Check rate limit
        if not check_test_rate_limit(user_id):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Maximum 5 tests per minute."
            )

        # Get decrypted key
        api_key = await byok_manager.get_user_api_key(user_id, provider)

        if not api_key:
            raise HTTPException(
                status_code=404,
                detail=f"No API key found for provider '{provider}'"
            )

        # Test key
        test_result = await test_provider_api_key(provider, api_key)

        logger.info(f"User {user_id} tested BYOK key for {provider}: {test_result.get('success')}")

        return {
            'success': test_result.get('success'),
            'provider': provider,
            'message': test_result.get('message'),
            'details': {k: v for k, v in test_result.items() if k not in ['success', 'message']}
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing BYOK key: {e}")
        raise HTTPException(status_code=500, detail="Failed to test API key")


@router.get("/byok/keys/{provider}/usage")
async def get_byok_usage(
    provider: str,
    user_id: str = Depends(get_user_id),
    byok_manager: BYOKManager = Depends(get_byok_manager)
):
    """
    Get usage statistics for a BYOK key

    NOTE: Placeholder for Phase 2 - usage tracking integration

    Args:
        provider: Provider name

    Returns:
        Usage statistics
    """
    try:
        # Verify key exists
        providers = await byok_manager.list_user_providers(user_id)
        provider_exists = any(p['provider'] == provider for p in providers)

        if not provider_exists:
            raise HTTPException(
                status_code=404,
                detail=f"No API key found for provider '{provider}'"
            )

        # TODO: Query usage_metering table for BYOK requests
        # For now, return placeholder

        return {
            'provider': provider,
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'last_used': None,
            'message': 'Usage tracking integration coming in Phase 2'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting BYOK usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to get usage statistics")


@router.get("/byok/providers")
async def list_supported_providers():
    """
    List all supported BYOK providers

    Returns:
        List of provider configurations with details
    """
    return {
        'providers': [
            {
                'name': 'openrouter',
                'display_name': 'OpenRouter',
                'description': 'Universal LLM proxy - 200+ models including GPT-4o, Claude 3.5 Sonnet, Gemini 2.0',
                'key_format': 'sk-or-v1-...',
                'signup_url': 'https://openrouter.ai',
                'docs_url': 'https://openrouter.ai/docs',
                'supports_test': True
            },
            {
                'name': 'openai',
                'display_name': 'OpenAI',
                'description': 'GPT-4o, GPT-4o-mini, GPT-4-turbo, o1-preview, o1-mini, DALL-E 3',
                'key_format': 'sk-proj-...',
                'signup_url': 'https://platform.openai.com',
                'docs_url': 'https://platform.openai.com/docs',
                'supports_test': True
            },
            {
                'name': 'anthropic',
                'display_name': 'Anthropic',
                'description': 'Claude 3.5 Sonnet (latest), Claude 3 Opus/Sonnet/Haiku',
                'key_format': 'sk-ant-...',
                'signup_url': 'https://console.anthropic.com',
                'docs_url': 'https://docs.anthropic.com',
                'supports_test': True
            },
            {
                'name': 'google',
                'display_name': 'Google AI',
                'description': 'Gemini 2.0 Flash, Gemini 1.5 Pro/Flash (up to 2M context)',
                'key_format': 'AIza...',
                'signup_url': 'https://aistudio.google.com/apikey',
                'docs_url': 'https://ai.google.dev/docs',
                'supports_test': True
            },
            {
                'name': 'ollama-cloud',
                'display_name': 'Ollama Cloud',
                'description': 'Self-hosted and managed Ollama models with cloud API',
                'key_format': 'xxx.yyy',
                'signup_url': 'https://ollama.ai/cloud',
                'docs_url': 'https://docs.ollama.ai/cloud',
                'supports_test': False
            },
            {
                'name': 'huggingface',
                'display_name': 'HuggingFace',
                'description': 'Access 350,000+ models via HuggingFace Inference API',
                'key_format': 'hf_...',
                'signup_url': 'https://huggingface.co/settings/tokens',
                'docs_url': 'https://huggingface.co/docs/api-inference',
                'supports_test': False
            },
            {
                'name': 'ops-center',
                'display_name': 'Ops Center',
                'description': 'This platform - local vLLM models (Qwen 2.5 32B, etc.)',
                'key_format': 'internal',
                'signup_url': os.getenv('APP_URL', 'http://localhost:8084'),
                'docs_url': os.getenv('DOCS_URL', 'http://localhost:8084/docs'),
                'supports_test': True
            },
            {
                'name': 'custom',
                'display_name': 'Custom Provider',
                'description': 'Any OpenAI-compatible endpoint (LM Studio, vLLM, LocalAI, etc.)',
                'key_format': 'varies',
                'signup_url': '',
                'docs_url': '',
                'supports_test': False
            }
        ]
    }


# ============================================================================
# System Provider Keys (Admin Only)
# ============================================================================

@router.get("/admin/system-keys")
async def get_system_provider_keys(
    request: Request,
    credit_system: CreditSystem = Depends(get_credit_system)
):
    """
    Get all providers with system key status (admin only)

    Authentication: Uses session cookie (same as other admin endpoints)

    Returns:
        List of providers with key configuration status
    """
    try:
        # Check admin role from session
        user = await require_admin_from_session(request)
        user_id = user.get("email", user.get("username", "unknown"))

        # Get system key manager
        system_key_manager = SystemKeyManager(credit_system.db_pool, BYOK_ENCRYPTION_KEY)
        providers = await system_key_manager.get_all_providers_with_keys()

        logger.info(f"Admin {user_id} retrieved system provider keys")

        return {'providers': providers}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system keys: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve system keys")


@router.put("/admin/system-keys/{provider_id}")
async def set_system_provider_key(
    provider_id: str,
    request_obj: Request,
    credit_system: CreditSystem = Depends(get_credit_system)
):
    """
    Set system API key for a provider (admin only)

    Authentication: Uses session cookie (same as other admin endpoints)

    Args:
        provider_id: Provider UUID
        request_obj: FastAPI request (contains session cookie)
        Body: {"api_key": "sk-..."}

    Returns:
        Success message
    """
    try:
        # Check admin role from session
        user = await require_admin_from_session(request_obj)
        user_id = user.get("email", user.get("username", "unknown"))

        # Parse request body
        body = await request_obj.json()
        api_key = body.get('api_key')
        if not api_key or len(api_key) < 10:
            raise HTTPException(status_code=400, detail="Invalid API key")

        # Store system key
        system_key_manager = SystemKeyManager(credit_system.db_pool, BYOK_ENCRYPTION_KEY)
        await system_key_manager.set_system_key(provider_id, api_key, 'database')

        logger.info(f"Admin {user_id} updated system key for provider {provider_id}")

        return {
            'success': True,
            'message': 'System key updated successfully',
            'provider_id': provider_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting system key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to set system key")


@router.delete("/admin/system-keys/{provider_id}")
async def delete_system_provider_key(
    provider_id: str,
    request: Request,
    credit_system: CreditSystem = Depends(get_credit_system)
):
    """
    Delete system API key (falls back to environment) (admin only)

    Authentication: Uses session cookie (same as other admin endpoints)

    Args:
        provider_id: Provider UUID
        request: FastAPI request (contains session cookie)

    Returns:
        Success message
    """
    try:
        # Check admin role from session
        user = await require_admin_from_session(request)
        user_id = user.get("email", user.get("username", "unknown"))

        # Delete system key
        system_key_manager = SystemKeyManager(credit_system.db_pool, BYOK_ENCRYPTION_KEY)
        await system_key_manager.delete_system_key(provider_id)

        logger.info(f"Admin {user_id} deleted system key for provider {provider_id}")

        return {
            'success': True,
            'message': 'System key deleted (will fall back to environment variable)',
            'provider_id': provider_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting system key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete system key")


@router.post("/admin/system-keys/{provider_id}/test")
async def test_system_provider_key(
    provider_id: str,
    request: Request,
    credit_system: CreditSystem = Depends(get_credit_system)
):
    """
    Test system API key connection (admin only)

    Authentication: Uses session cookie (same as other admin endpoints)
    Rate Limited: 5 tests per minute per user

    Args:
        provider_id: Provider UUID
        request: FastAPI request (contains session cookie)

    Returns:
        Test results with success status and details
    """
    try:
        # Check admin role from session
        user = await require_admin_from_session(request)
        user_id = user.get("email", user.get("username", "unknown"))

        # Check rate limit
        if not check_test_rate_limit(user_id):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Maximum 5 tests per minute."
            )

        # Get system key manager
        system_key_manager = SystemKeyManager(credit_system.db_pool, BYOK_ENCRYPTION_KEY)

        # Get provider info
        async with credit_system.db_pool.acquire() as conn:
            provider = await conn.fetchrow("""
                SELECT name, type as provider_type FROM llm_providers WHERE id = $1
            """, provider_id)

            if not provider:
                raise HTTPException(status_code=404, detail="Provider not found")

        # Get system key
        api_key = await system_key_manager.get_system_key(provider_id)
        if not api_key:
            raise HTTPException(status_code=400, detail="No API key configured")

        # Test using existing test function
        test_result = await test_provider_api_key(provider['name'], api_key)

        # Update test status in database
        async with credit_system.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE llm_providers
                SET api_key_last_tested = NOW(),
                    api_key_test_status = $1
                WHERE id = $2
            """, 'success' if test_result['success'] else 'failed', provider_id)

        logger.info(f"Admin {user_id} tested system key for provider {provider_id}: {test_result.get('success')}")

        return {
            'success': test_result.get('success'),
            'provider_id': provider_id,
            'provider_name': provider['name'],
            'message': test_result.get('message'),
            'details': {k: v for k, v in test_result.items() if k not in ['success', 'message']}
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing system key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to test system key")


# ============================================================================
# Health Check
# ============================================================================

@router.get("/admin/models/openrouter")
async def get_openrouter_models(
    request: Request,
    credit_system: CreditSystem = Depends(get_credit_system)
):
    """
    Fetch all models from OpenRouter API and merge with database status

    Returns:
        List of models with pricing, capabilities, and enable/disable status
    """
    try:
        # Check admin permission
        user = await require_admin_from_session(request)
        user_id = user.get("email", user.get("username", "unknown"))

        logger.info(f"Admin {user_id} requesting OpenRouter model catalog")

        # Get OpenRouter API key from database
        async with credit_system.db_pool.acquire() as conn:
            # Get OpenRouter provider
            provider = await conn.fetchrow("""
                SELECT id, name, api_key_encrypted
                FROM llm_providers
                WHERE LOWER(name) = 'openrouter'
            """)

            if not provider or not provider['api_key_encrypted']:
                raise HTTPException(status_code=404, detail="OpenRouter system key not configured")

            # Decrypt API key
            cipher = Fernet(BYOK_ENCRYPTION_KEY.encode())
            api_key = cipher.decrypt(provider['api_key_encrypted'].encode()).decode()

            # Fetch models from OpenRouter
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    'https://openrouter.ai/api/v1/models',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'HTTP-Referer': os.getenv('APP_URL', 'http://localhost:8084'),
                        'X-Title': os.getenv('APP_TITLE', 'Ops Center')
                    }
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"OpenRouter API error: {response.text}"
                    )

                openrouter_models = response.json().get('data', [])

            # Get enabled/disabled status from our database
            db_models = await conn.fetch("""
                SELECT name, enabled
                FROM llm_models
                WHERE provider_id = $1
            """, provider['id'])

            # Create a lookup dict for database models
            db_models_dict = {m['name']: m for m in db_models}

        # Merge OpenRouter data with our database status
        enriched_models = []
        for model in openrouter_models:
            model_id = model.get('id')
            # Try to match by model ID (which OpenRouter uses as the name)
            db_model = db_models_dict.get(model_id, {})

            # Extract pricing info
            pricing = model.get('pricing', {})
            prompt_cost = float(pricing.get('prompt', 0))
            completion_cost = float(pricing.get('completion', 0))

            # Extract provider name from top_provider object (with null safety)
            top_provider = model.get('top_provider') or {}
            provider_name = top_provider.get('name', 'OpenRouter') if isinstance(top_provider, dict) else 'OpenRouter'

            # Extract performance metrics (if available from OpenRouter) - with null safety
            per_request_limits = model.get('per_request_limits') or {}
            architecture = model.get('architecture') or {}

            enriched_models.append({
                'id': model_id,
                'name': model_id,  # Model ID (e.g., "openai/gpt-4")
                'display_name': model.get('name', model_id),  # Human-readable name
                'provider_name': provider_name,  # Extracted from top_provider
                'description': model.get('description', ''),
                'context_length': model.get('context_length', 0),
                'architecture': architecture.get('modality', 'text') if isinstance(architecture, dict) else 'text',
                # Flatten pricing for frontend compatibility
                'cost_per_1m_input': prompt_cost * 1_000_000,  # Per 1M tokens
                'cost_per_1m_output': completion_cost * 1_000_000,  # Per 1M tokens
                # Keep nested pricing for backward compatibility
                'pricing': {
                    'prompt': prompt_cost,  # Per token
                    'completion': completion_cost,  # Per token
                    'prompt_per_1m': prompt_cost * 1_000_000,
                    'completion_per_1m': completion_cost * 1_000_000
                },
                'top_provider': top_provider if isinstance(top_provider, dict) else {},  # Full provider object
                'enabled': db_model.get('enabled', False),  # Renamed from is_active
                # Performance metrics (null-safe)
                'rating': model.get('rating'),  # Model quality rating (if available)
                'latency_ms': top_provider.get('max_completion_tokens') if isinstance(top_provider, dict) else None,
                'throughput': per_request_limits.get('prompt_tokens') if isinstance(per_request_limits, dict) else None,
                # Capabilities (null-safe)
                'supports_streaming': True,  # OpenRouter supports streaming
                'supports_function_calling': 'tool' in architecture.get('modality', '').lower() if isinstance(architecture, dict) else False,
                'supports_vision': 'vision' in architecture.get('modality', '').lower() if isinstance(architecture, dict) else False
            })

        logger.info(f"Returning {len(enriched_models)} OpenRouter models to admin {user_id}")

        return {
            'success': True,
            'total_models': len(enriched_models),
            'models': enriched_models,
            'provider': {
                'id': provider['id'],
                'name': provider['name']
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching OpenRouter models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")


@router.post("/admin/models/bulk-update")
async def bulk_update_models(
    request: Request,
    update_request: dict,
    credit_system: CreditSystem = Depends(get_credit_system)
):
    """
    Bulk enable/disable models or update their settings

    Request body:
    {
        "model_ids": ["openai/gpt-4", "anthropic/claude-3"],
        "action": "enable" | "disable" | "update",
        "updates": {  // Only for "update" action
            "enabled": true/false,
            // ... other fields
        }
    }
    """
    try:
        user = await require_admin_from_session(request)
        user_id = user.get("email", user.get("username", "unknown"))

        model_ids = update_request.get('model_ids', [])
        action = update_request.get('action', 'update')
        updates = update_request.get('updates', {})

        if not model_ids or not isinstance(model_ids, list):
            raise HTTPException(status_code=400, detail="model_ids must be a non-empty list")

        logger.info(f"Admin {user_id} bulk updating {len(model_ids)} models: action={action}")

        # Get OpenRouter provider
        async with credit_system.db_pool.acquire() as conn:
            provider = await conn.fetchrow("""
                SELECT id, name
                FROM llm_providers
                WHERE LOWER(name) = 'openrouter'
            """)

            if not provider:
                raise HTTPException(status_code=404, detail="OpenRouter provider not found")

            provider_id = provider['id']

            # Determine enabled status based on action
            if action == 'enable':
                enabled = True
            elif action == 'disable':
                enabled = False
            elif action == 'update':
                enabled = updates.get('enabled', True)
            else:
                raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

            # Upsert models (insert if not exists, update if exists)
            updated_count = 0
            for model_id in model_ids:
                result = await conn.execute("""
                    INSERT INTO llm_models (name, provider_id, enabled, created_at, updated_at)
                    VALUES ($1, $2, $3, NOW(), NOW())
                    ON CONFLICT (name, provider_id)
                    DO UPDATE SET
                        enabled = $3,
                        updated_at = NOW()
                """, model_id, provider_id, enabled)
                updated_count += 1

        logger.info(f"Admin {user_id} bulk updated {updated_count} models to enabled={enabled}")

        return {
            'success': True,
            'updated_count': updated_count,
            'action': action,
            'enabled': enabled,
            'model_ids': model_ids
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk updating models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to bulk update models: {str(e)}")


@router.put("/admin/models/{model_id}/toggle")
async def toggle_model_status(
    model_id: str,
    request: Request,
    credit_system: CreditSystem = Depends(get_credit_system)
):
    """
    Enable or disable a specific model

    Args:
        model_id: Model identifier (e.g., "openai/gpt-4")

    Returns:
        Updated model status
    """
    try:
        # Check admin permission
        user = await require_admin_from_session(request)
        user_id = user.get("email", user.get("username", "unknown"))

        logger.info(f"Admin {user_id} toggling model {model_id}")

        async with credit_system.db_pool.acquire() as conn:
            # Check if model exists
            existing_model = await conn.fetchrow("""
                SELECT id, enabled, provider_id
                FROM llm_models
                WHERE name = $1
            """, model_id)

            if existing_model:
                # Toggle existing model
                new_status = not existing_model['enabled']
                await conn.execute("""
                    UPDATE llm_models
                    SET enabled = $1, updated_at = NOW()
                    WHERE name = $2
                """, new_status, model_id)

                logger.info(f"Admin {user_id} set model {model_id} to {'enabled' if new_status else 'disabled'}")

                return {
                    'success': True,
                    'model_id': model_id,
                    'is_active': new_status,
                    'message': f"Model {'enabled' if new_status else 'disabled'} successfully"
                }
            else:
                # Model doesn't exist in DB yet, create it as enabled
                # First, get the OpenRouter provider ID
                provider = await conn.fetchrow("""
                    SELECT id FROM llm_providers
                    WHERE LOWER(name) = 'openrouter'
                """)

                if not provider:
                    raise HTTPException(status_code=404, detail="OpenRouter provider not found")

                # Insert new model as enabled
                await conn.execute("""
                    INSERT INTO llm_models (
                        provider_id, name, display_name,
                        enabled, created_at, updated_at
                    )
                    VALUES ($1, $2, $2, TRUE, NOW(), NOW())
                """, provider['id'], model_id)

                logger.info(f"Admin {user_id} enabled new model {model_id}")

                return {
                    'success': True,
                    'model_id': model_id,
                    'is_active': True,
                    'message': 'Model enabled successfully'
                }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling model {model_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to toggle model: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test LiteLLM proxy connection
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LITELLM_PROXY_URL}/health")
            litellm_healthy = response.status_code == 200

        return {
            'status': 'healthy' if litellm_healthy else 'degraded',
            'litellm_proxy': 'up' if litellm_healthy else 'down',
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'degraded',
            'litellm_proxy': 'down',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
