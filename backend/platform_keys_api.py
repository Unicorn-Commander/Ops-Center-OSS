"""
Platform Keys Management API - Admin-Only Provider Key Management

This module provides admin-only endpoints for managing system-level provider API keys:
- OpenRouter API key
- Magic Unicorn provisioning key
- Other platform provider keys

These are DIFFERENT from user BYOK keys (user_api_keys.py) and UC API keys (uc_api_keys.py).

Platform keys are stored in the platform_settings table with encryption.

Database Table: platform_settings
Columns: id, key, value (encrypted), description, category, is_encrypted, created_at, updated_at

Author: Backend API Developer
Date: November 3, 2025
"""

import logging
import os
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
import asyncpg
from key_encryption import get_encryption

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/platform-keys", tags=["Platform Keys (Admin)"])


# ============================================================================
# Request/Response Models
# ============================================================================

class UpdatePlatformKeyRequest(BaseModel):
    """Request to update a platform API key"""
    api_key: str = Field(..., description="Plain text API key (will be encrypted)", min_length=10)


class PlatformKeyResponse(BaseModel):
    """Response with platform key information"""
    key_name: str
    description: str
    has_key: bool
    key_preview: Optional[str]  # Masked preview if key exists
    last_updated: Optional[str]
    source: str  # database, environment, or not_set


class PlatformKeysListResponse(BaseModel):
    """Response with all platform keys"""
    keys: List[PlatformKeyResponse]
    total: int


# ============================================================================
# Authentication Dependency
# ============================================================================

async def require_admin(request: Request) -> Dict:
    """
    Require admin role from session

    Returns:
        User dict if admin

    Raises:
        HTTPException 401 if not authenticated
        HTTPException 403 if not admin
    """
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no session token")

    # Get sessions from app state
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


async def get_db_pool(request: Request) -> asyncpg.Pool:
    """Get database pool from app state"""
    if not hasattr(request.app.state, 'db_pool') or not request.app.state.db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return request.app.state.db_pool


# ============================================================================
# Helper Functions
# ============================================================================

def mask_api_key(api_key: str) -> str:
    """
    Mask API key for display

    Args:
        api_key: Full API key

    Returns:
        Masked key (first 7 chars + ... + last 4 chars)
    """
    if len(api_key) < 12:
        return "***"

    return f"{api_key[:7]}...{api_key[-4:]}"


async def get_platform_key_from_db(db_pool: asyncpg.Pool, key_name: str) -> Optional[str]:
    """
    Get encrypted platform key from database

    Args:
        db_pool: Database pool
        key_name: Key name (e.g., "openrouter_api_key")

    Returns:
        Encrypted key string or None if not found
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow("""
            SELECT value
            FROM platform_settings
            WHERE key = $1 AND category = 'api_keys' AND is_secret = TRUE
        """, key_name)

        return result['value'] if result else None


async def set_platform_key_in_db(
    db_pool: asyncpg.Pool,
    key_name: str,
    encrypted_value: str
) -> bool:
    """
    Set encrypted platform key in database

    Args:
        db_pool: Database pool
        key_name: Key name (e.g., "openrouter_api_key")
        encrypted_value: Encrypted API key

    Returns:
        True if successful
    """
    async with db_pool.acquire() as conn:
        # Upsert (insert or update)
        await conn.execute("""
            INSERT INTO platform_settings (key, value, category, is_secret, updated_at)
            VALUES ($1, $2, 'api_keys', TRUE, NOW())
            ON CONFLICT (key)
            DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = NOW()
        """, key_name, encrypted_value)

    return True


# ============================================================================
# Key Validation Functions
# ============================================================================

def validate_openrouter_key(api_key: str) -> bool:
    """Validate OpenRouter API key format (sk-or-v1-...)"""
    return api_key.startswith("sk-or-")

def validate_openai_key(api_key: str) -> bool:
    """Validate OpenAI API key format (sk-proj-...)"""
    return api_key.startswith("sk-") and not api_key.startswith("sk-or-")

def validate_anthropic_key(api_key: str) -> bool:
    """Validate Anthropic API key format (sk-ant-...)"""
    return api_key.startswith("sk-ant-")

def validate_huggingface_key(api_key: str) -> bool:
    """Validate HuggingFace API key format (hf_...)"""
    return api_key.startswith("hf_")

def validate_groq_key(api_key: str) -> bool:
    """Validate Groq API key format (gsk_...)"""
    return api_key.startswith("gsk_")

def validate_xai_key(api_key: str) -> bool:
    """Validate X.AI Grok API key format (xai-...)"""
    return api_key.startswith("xai-")

def validate_google_key(api_key: str) -> bool:
    """Validate Google AI API key format (AIza...)"""
    return api_key.startswith("AIza")


# ============================================================================
# Platform Key Definitions
# ============================================================================

PLATFORM_KEYS = {
    "openrouter_api_key": {
        "display_name": "OpenRouter API Key",
        "description": "OpenRouter API key for LLM inference routing (348+ models)",
        "env_var": "OPENROUTER_API_KEY",
        "key_format": "sk-or-v1-...",
        "validator": validate_openrouter_key
    },
    "openai_api_key": {
        "display_name": "OpenAI API Key",
        "description": "OpenAI API key for GPT-4, GPT-3.5, and DALL-E models",
        "env_var": "OPENAI_API_KEY",
        "key_format": "sk-proj-...",
        "validator": validate_openai_key
    },
    "anthropic_api_key": {
        "display_name": "Anthropic API Key",
        "description": "Anthropic API key for Claude models (Opus, Sonnet, Haiku)",
        "env_var": "ANTHROPIC_API_KEY",
        "key_format": "sk-ant-...",
        "validator": validate_anthropic_key
    },
    "huggingface_api_key": {
        "display_name": "HuggingFace API Key",
        "description": "HuggingFace API key for inference API and model downloads",
        "env_var": "HUGGINGFACE_API_KEY",
        "key_format": "hf_...",
        "validator": validate_huggingface_key
    },
    "groq_api_key": {
        "display_name": "Groq API Key",
        "description": "Groq API key for ultra-fast LLM inference",
        "env_var": "GROQ_API_KEY",
        "key_format": "gsk_...",
        "validator": validate_groq_key
    },
    "xai_api_key": {
        "display_name": "X.AI Grok API Key",
        "description": "X.AI API key for Grok models",
        "env_var": "XAI_API_KEY",
        "key_format": "xai-...",
        "validator": validate_xai_key
    },
    "google_ai_api_key": {
        "display_name": "Google AI API Key",
        "description": "Google AI API key for Gemini models",
        "env_var": "GOOGLE_AI_API_KEY",
        "key_format": "AIza...",
        "validator": validate_google_key
    },
    "provisioning_key": {
        "display_name": "Magic Unicorn Provisioning Key",
        "description": "Provisioning key for Magic Unicorn services",
        "env_var": "PROVISIONING_KEY",
        "key_format": "mu-prov-...",
        "validator": None  # No specific validation
    },
    "litellm_master_key": {
        "display_name": "LiteLLM Master Key",
        "description": "Master key for LiteLLM proxy administration",
        "env_var": "LITELLM_MASTER_KEY",
        "key_format": "sk-litellm-...",
        "validator": None  # No specific validation
    }
}


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("", response_model=PlatformKeysListResponse)
async def list_platform_keys(
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    List all platform API keys (admin only)

    Returns information about all configured platform keys with masked previews.
    Shows whether each key is stored in database, environment, or not set.

    Returns:
    - keys: List of platform keys with metadata
    - total: Total number of keys
    """
    try:
        encryption = get_encryption()
        key_list = []

        for key_name, config in PLATFORM_KEYS.items():
            # Check database
            db_encrypted = await get_platform_key_from_db(db_pool, key_name)

            # Check environment
            env_value = os.getenv(config['env_var'])

            # Determine source and preview
            if db_encrypted:
                source = "database"
                has_key = True
                try:
                    decrypted = encryption.decrypt_key(db_encrypted)
                    preview = mask_api_key(decrypted)
                except Exception as e:
                    logger.error(f"Error decrypting {key_name}: {e}")
                    preview = "***"
            elif env_value:
                source = "environment"
                has_key = True
                preview = mask_api_key(env_value)
            else:
                source = "not_set"
                has_key = False
                preview = None

            # Get last updated timestamp from database
            async with db_pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT updated_at FROM platform_settings WHERE key = $1
                """, key_name)

            last_updated = result['updated_at'].isoformat() if result else None

            key_list.append(PlatformKeyResponse(
                key_name=config['display_name'],
                description=config['description'],
                has_key=has_key,
                key_preview=preview,
                last_updated=last_updated,
                source=source
            ))

        logger.info(f"Admin {current_user.get('email', 'unknown')} listed platform keys")

        return PlatformKeysListResponse(
            keys=key_list,
            total=len(key_list)
        )

    except Exception as e:
        logger.error(f"Error listing platform keys: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list platform keys")


@router.put("/openrouter")
async def update_openrouter_key(
    key_request: UpdatePlatformKeyRequest,
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Update OpenRouter API key (admin only)

    Stores the OpenRouter API key in encrypted form in the database.
    This key is used by LiteLLM for routing LLM inference requests.

    **Note**: After updating, you'll need to restart the LiteLLM container
    or update its configuration to use the new key.

    Request Body:
    - api_key: OpenRouter API key (plain text, will be encrypted)

    Returns:
    - success: True if updated
    - message: Confirmation message
    """
    try:
        # Validate key format
        config = PLATFORM_KEYS["openrouter_api_key"]
        if config["validator"] and not config["validator"](key_request.api_key):
            logger.warning(f"OpenRouter key doesn't match expected format ({config['key_format']})")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid OpenRouter API key format. Expected format: {config['key_format']}"
            )

        # Encrypt the key
        encryption = get_encryption()
        encrypted_key = encryption.encrypt_key(key_request.api_key)

        # Store in database
        await set_platform_key_in_db(
            db_pool,
            "openrouter_api_key",
            encrypted_key
        )

        logger.info(f"Admin {current_user.get('email', 'unknown')} updated OpenRouter API key")

        return {
            "success": True,
            "message": "OpenRouter API key updated successfully",
            "key_preview": mask_api_key(key_request.api_key),
            "next_steps": [
                "Key stored in database (encrypted)",
                "To use this key, restart LiteLLM container or update its config",
                "See LITELLM_CONFIG_UPDATE.md for instructions"
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating OpenRouter key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update OpenRouter key")


@router.put("/openai")
async def update_openai_key(
    key_request: UpdatePlatformKeyRequest,
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Update OpenAI API key (admin only)

    Stores the OpenAI API key in encrypted form in the database.
    This key is used for GPT-4, GPT-3.5, and DALL-E models.

    Request Body:
    - api_key: OpenAI API key starting with sk-proj- (plain text, will be encrypted)

    Returns:
    - success: True if updated
    - message: Confirmation message
    """
    try:
        # Validate key format
        config = PLATFORM_KEYS["openai_api_key"]
        if config["validator"] and not config["validator"](key_request.api_key):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid OpenAI API key format. Expected format: {config['key_format']}"
            )

        # Encrypt the key
        encryption = get_encryption()
        encrypted_key = encryption.encrypt_key(key_request.api_key)

        # Store in database
        await set_platform_key_in_db(db_pool, "openai_api_key", encrypted_key)

        logger.info(f"Admin {current_user.get('email', 'unknown')} updated OpenAI API key")

        return {
            "success": True,
            "message": "OpenAI API key updated successfully",
            "key_preview": mask_api_key(key_request.api_key)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating OpenAI key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update OpenAI key")


@router.put("/anthropic")
async def update_anthropic_key(
    key_request: UpdatePlatformKeyRequest,
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Update Anthropic API key (admin only)

    Stores the Anthropic API key in encrypted form in the database.
    This key is used for Claude models (Opus, Sonnet, Haiku).

    Request Body:
    - api_key: Anthropic API key starting with sk-ant- (plain text, will be encrypted)

    Returns:
    - success: True if updated
    - message: Confirmation message
    """
    try:
        # Validate key format
        config = PLATFORM_KEYS["anthropic_api_key"]
        if config["validator"] and not config["validator"](key_request.api_key):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid Anthropic API key format. Expected format: {config['key_format']}"
            )

        # Encrypt the key
        encryption = get_encryption()
        encrypted_key = encryption.encrypt_key(key_request.api_key)

        # Store in database
        await set_platform_key_in_db(db_pool, "anthropic_api_key", encrypted_key)

        logger.info(f"Admin {current_user.get('email', 'unknown')} updated Anthropic API key")

        return {
            "success": True,
            "message": "Anthropic API key updated successfully",
            "key_preview": mask_api_key(key_request.api_key)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Anthropic key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update Anthropic key")


@router.put("/huggingface")
async def update_huggingface_key(
    key_request: UpdatePlatformKeyRequest,
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Update HuggingFace API key (admin only)

    Stores the HuggingFace API key in encrypted form in the database.
    This key is used for inference API and model downloads.

    Request Body:
    - api_key: HuggingFace API key starting with hf_ (plain text, will be encrypted)

    Returns:
    - success: True if updated
    - message: Confirmation message
    """
    try:
        # Validate key format
        config = PLATFORM_KEYS["huggingface_api_key"]
        if config["validator"] and not config["validator"](key_request.api_key):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid HuggingFace API key format. Expected format: {config['key_format']}"
            )

        # Encrypt the key
        encryption = get_encryption()
        encrypted_key = encryption.encrypt_key(key_request.api_key)

        # Store in database
        await set_platform_key_in_db(db_pool, "huggingface_api_key", encrypted_key)

        logger.info(f"Admin {current_user.get('email', 'unknown')} updated HuggingFace API key")

        return {
            "success": True,
            "message": "HuggingFace API key updated successfully",
            "key_preview": mask_api_key(key_request.api_key)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating HuggingFace key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update HuggingFace key")


@router.put("/groq")
async def update_groq_key(
    key_request: UpdatePlatformKeyRequest,
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Update Groq API key (admin only)

    Stores the Groq API key in encrypted form in the database.
    This key is used for ultra-fast LLM inference.

    Request Body:
    - api_key: Groq API key starting with gsk_ (plain text, will be encrypted)

    Returns:
    - success: True if updated
    - message: Confirmation message
    """
    try:
        # Validate key format
        config = PLATFORM_KEYS["groq_api_key"]
        if config["validator"] and not config["validator"](key_request.api_key):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid Groq API key format. Expected format: {config['key_format']}"
            )

        # Encrypt the key
        encryption = get_encryption()
        encrypted_key = encryption.encrypt_key(key_request.api_key)

        # Store in database
        await set_platform_key_in_db(db_pool, "groq_api_key", encrypted_key)

        logger.info(f"Admin {current_user.get('email', 'unknown')} updated Groq API key")

        return {
            "success": True,
            "message": "Groq API key updated successfully",
            "key_preview": mask_api_key(key_request.api_key)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Groq key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update Groq key")


@router.put("/xai")
async def update_xai_key(
    key_request: UpdatePlatformKeyRequest,
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Update X.AI Grok API key (admin only)

    Stores the X.AI API key in encrypted form in the database.
    This key is used for Grok models.

    Request Body:
    - api_key: X.AI API key starting with xai- (plain text, will be encrypted)

    Returns:
    - success: True if updated
    - message: Confirmation message
    """
    try:
        # Validate key format
        config = PLATFORM_KEYS["xai_api_key"]
        if config["validator"] and not config["validator"](key_request.api_key):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid X.AI API key format. Expected format: {config['key_format']}"
            )

        # Encrypt the key
        encryption = get_encryption()
        encrypted_key = encryption.encrypt_key(key_request.api_key)

        # Store in database
        await set_platform_key_in_db(db_pool, "xai_api_key", encrypted_key)

        logger.info(f"Admin {current_user.get('email', 'unknown')} updated X.AI API key")

        return {
            "success": True,
            "message": "X.AI API key updated successfully",
            "key_preview": mask_api_key(key_request.api_key)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating X.AI key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update X.AI key")


@router.put("/google")
async def update_google_key(
    key_request: UpdatePlatformKeyRequest,
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Update Google AI API key (admin only)

    Stores the Google AI API key in encrypted form in the database.
    This key is used for Gemini models.

    Request Body:
    - api_key: Google AI API key starting with AIza (plain text, will be encrypted)

    Returns:
    - success: True if updated
    - message: Confirmation message
    """
    try:
        # Validate key format
        config = PLATFORM_KEYS["google_ai_api_key"]
        if config["validator"] and not config["validator"](key_request.api_key):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid Google AI API key format. Expected format: {config['key_format']}"
            )

        # Encrypt the key
        encryption = get_encryption()
        encrypted_key = encryption.encrypt_key(key_request.api_key)

        # Store in database
        await set_platform_key_in_db(db_pool, "google_ai_api_key", encrypted_key)

        logger.info(f"Admin {current_user.get('email', 'unknown')} updated Google AI API key")

        return {
            "success": True,
            "message": "Google AI API key updated successfully",
            "key_preview": mask_api_key(key_request.api_key)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Google AI key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update Google AI key")


@router.put("/provisioning")
async def update_provisioning_key(
    key_request: UpdatePlatformKeyRequest,
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Update Magic Unicorn provisioning key (admin only)

    Stores the provisioning key in encrypted form in the database.
    This key is used for provisioning Magic Unicorn services.

    Request Body:
    - api_key: Provisioning key (plain text, will be encrypted)

    Returns:
    - success: True if updated
    - message: Confirmation message
    """
    try:
        # Encrypt the key
        encryption = get_encryption()
        encrypted_key = encryption.encrypt_key(key_request.api_key)

        # Store in database
        await set_platform_key_in_db(
            db_pool,
            "provisioning_key",
            encrypted_key
        )

        logger.info(f"Admin {current_user.get('email', 'unknown')} updated provisioning key")

        return {
            "success": True,
            "message": "Provisioning key updated successfully",
            "key_preview": mask_api_key(key_request.api_key)
        }

    except Exception as e:
        logger.error(f"Error updating provisioning key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update provisioning key")


@router.get("/openrouter/decrypted")
async def get_openrouter_key_decrypted(
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get decrypted OpenRouter API key (admin only)

    **WARNING**: This exposes the full API key. Use with caution.

    Returns:
    - api_key: Decrypted API key
    - source: database or environment
    """
    try:
        # Check database first
        db_encrypted = await get_platform_key_from_db(db_pool, "openrouter_api_key")

        if db_encrypted:
            encryption = get_encryption()
            api_key = encryption.decrypt_key(db_encrypted)
            source = "database"
        else:
            # Fall back to environment
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise HTTPException(status_code=404, detail="OpenRouter API key not configured")
            source = "environment"

        logger.info(f"Admin {current_user.get('email', 'unknown')} retrieved OpenRouter API key")

        return {
            "api_key": api_key,
            "source": source,
            "warning": "This is the full API key. Keep it secure."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving OpenRouter key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve OpenRouter key")


@router.get("/provisioning/decrypted")
async def get_provisioning_key_decrypted(
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get decrypted provisioning key (admin only)

    **WARNING**: This exposes the full provisioning key. Use with caution.

    Returns:
    - api_key: Decrypted provisioning key
    - source: database or environment
    """
    try:
        # Check database first
        db_encrypted = await get_platform_key_from_db(db_pool, "provisioning_key")

        if db_encrypted:
            encryption = get_encryption()
            api_key = encryption.decrypt_key(db_encrypted)
            source = "database"
        else:
            # Fall back to environment
            api_key = os.getenv("PROVISIONING_KEY")
            if not api_key:
                raise HTTPException(status_code=404, detail="Provisioning key not configured")
            source = "environment"

        logger.info(f"Admin {current_user.get('email', 'unknown')} retrieved provisioning key")

        return {
            "api_key": api_key,
            "source": source,
            "warning": "This is the full provisioning key. Keep it secure."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving provisioning key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve provisioning key")


@router.get("/openai/decrypted")
async def get_openai_key_decrypted(
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get decrypted OpenAI API key (admin only)

    **WARNING**: This exposes the full API key. Use with caution.

    Returns:
    - api_key: Decrypted API key
    - source: database or environment
    """
    try:
        db_encrypted = await get_platform_key_from_db(db_pool, "openai_api_key")

        if db_encrypted:
            encryption = get_encryption()
            api_key = encryption.decrypt_key(db_encrypted)
            source = "database"
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise HTTPException(status_code=404, detail="OpenAI API key not configured")
            source = "environment"

        logger.info(f"Admin {current_user.get('email', 'unknown')} retrieved OpenAI API key")

        return {
            "api_key": api_key,
            "source": source,
            "warning": "This is the full API key. Keep it secure."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving OpenAI key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve OpenAI key")


@router.get("/anthropic/decrypted")
async def get_anthropic_key_decrypted(
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get decrypted Anthropic API key (admin only)

    **WARNING**: This exposes the full API key. Use with caution.

    Returns:
    - api_key: Decrypted API key
    - source: database or environment
    """
    try:
        db_encrypted = await get_platform_key_from_db(db_pool, "anthropic_api_key")

        if db_encrypted:
            encryption = get_encryption()
            api_key = encryption.decrypt_key(db_encrypted)
            source = "database"
        else:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise HTTPException(status_code=404, detail="Anthropic API key not configured")
            source = "environment"

        logger.info(f"Admin {current_user.get('email', 'unknown')} retrieved Anthropic API key")

        return {
            "api_key": api_key,
            "source": source,
            "warning": "This is the full API key. Keep it secure."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving Anthropic key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve Anthropic key")


@router.get("/huggingface/decrypted")
async def get_huggingface_key_decrypted(
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get decrypted HuggingFace API key (admin only)

    **WARNING**: This exposes the full API key. Use with caution.

    Returns:
    - api_key: Decrypted API key
    - source: database or environment
    """
    try:
        db_encrypted = await get_platform_key_from_db(db_pool, "huggingface_api_key")

        if db_encrypted:
            encryption = get_encryption()
            api_key = encryption.decrypt_key(db_encrypted)
            source = "database"
        else:
            api_key = os.getenv("HUGGINGFACE_API_KEY")
            if not api_key:
                raise HTTPException(status_code=404, detail="HuggingFace API key not configured")
            source = "environment"

        logger.info(f"Admin {current_user.get('email', 'unknown')} retrieved HuggingFace API key")

        return {
            "api_key": api_key,
            "source": source,
            "warning": "This is the full API key. Keep it secure."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving HuggingFace key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve HuggingFace key")


@router.get("/groq/decrypted")
async def get_groq_key_decrypted(
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get decrypted Groq API key (admin only)

    **WARNING**: This exposes the full API key. Use with caution.

    Returns:
    - api_key: Decrypted API key
    - source: database or environment
    """
    try:
        db_encrypted = await get_platform_key_from_db(db_pool, "groq_api_key")

        if db_encrypted:
            encryption = get_encryption()
            api_key = encryption.decrypt_key(db_encrypted)
            source = "database"
        else:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise HTTPException(status_code=404, detail="Groq API key not configured")
            source = "environment"

        logger.info(f"Admin {current_user.get('email', 'unknown')} retrieved Groq API key")

        return {
            "api_key": api_key,
            "source": source,
            "warning": "This is the full API key. Keep it secure."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving Groq key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve Groq key")


@router.get("/xai/decrypted")
async def get_xai_key_decrypted(
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get decrypted X.AI API key (admin only)

    **WARNING**: This exposes the full API key. Use with caution.

    Returns:
    - api_key: Decrypted API key
    - source: database or environment
    """
    try:
        db_encrypted = await get_platform_key_from_db(db_pool, "xai_api_key")

        if db_encrypted:
            encryption = get_encryption()
            api_key = encryption.decrypt_key(db_encrypted)
            source = "database"
        else:
            api_key = os.getenv("XAI_API_KEY")
            if not api_key:
                raise HTTPException(status_code=404, detail="X.AI API key not configured")
            source = "environment"

        logger.info(f"Admin {current_user.get('email', 'unknown')} retrieved X.AI API key")

        return {
            "api_key": api_key,
            "source": source,
            "warning": "This is the full API key. Keep it secure."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving X.AI key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve X.AI key")


@router.get("/google/decrypted")
async def get_google_key_decrypted(
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get decrypted Google AI API key (admin only)

    **WARNING**: This exposes the full API key. Use with caution.

    Returns:
    - api_key: Decrypted API key
    - source: database or environment
    """
    try:
        db_encrypted = await get_platform_key_from_db(db_pool, "google_ai_api_key")

        if db_encrypted:
            encryption = get_encryption()
            api_key = encryption.decrypt_key(db_encrypted)
            source = "database"
        else:
            api_key = os.getenv("GOOGLE_AI_API_KEY")
            if not api_key:
                raise HTTPException(status_code=404, detail="Google AI API key not configured")
            source = "environment"

        logger.info(f"Admin {current_user.get('email', 'unknown')} retrieved Google AI API key")

        return {
            "api_key": api_key,
            "source": source,
            "warning": "This is the full API key. Keep it secure."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving Google AI key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve Google AI key")


# ============================================================================
# === T6 === Live key tests: POST /api/v1/admin/platform-keys/{key_type}/test
# ============================================================================
#
# Per-type live checks against the provider's own API. The key is resolved the
# same way the /decrypted endpoints resolve it (database first, env fallback);
# stripe/cloudflare resolve via platform_settings/env through get_credential.
# The response NEVER echoes the key.

import httpx
from get_credential import get_credential_async

TEST_TIMEOUT_SECONDS = 8.0

# key_type (URL slug, matching the PUT endpoints) -> internal key name
TESTABLE_KEY_TYPES = {
    "openrouter": "openrouter_api_key",
    "openai": "openai_api_key",
    "anthropic": "anthropic_api_key",
    "huggingface": "huggingface_api_key",
    "groq": "groq_api_key",
    "xai": "xai_api_key",
    "google": "google_ai_api_key",
    # Not stored in PLATFORM_KEYS; resolved via get_credential (platform_settings/env)
    "stripe": "STRIPE_SECRET_KEY",
    "cloudflare": "CLOUDFLARE_API_TOKEN",
}


async def _resolve_platform_key(db_pool: asyncpg.Pool, key_type: str):
    """Resolve (api_key, source) for a testable key type; (None, None) if unset."""
    if key_type in ("stripe", "cloudflare"):
        credential_name = TESTABLE_KEY_TYPES[key_type]
        value = await get_credential_async(credential_name, "")
        if value:
            # get_credential checks the database first, then the environment
            return value, "database_or_environment"
        return None, None

    key_name = TESTABLE_KEY_TYPES[key_type]
    db_encrypted = await get_platform_key_from_db(db_pool, key_name)
    if db_encrypted:
        encryption = get_encryption()
        return encryption.decrypt_key(db_encrypted), "database"

    env_var = PLATFORM_KEYS[key_name]["env_var"]
    env_value = os.getenv(env_var)
    if env_value:
        return env_value, "environment"
    return None, None


async def _run_key_test(key_type: str, api_key: str):
    """
    Perform the provider-specific live check.

    Returns (ok: bool, status_code: int|None, detail: str).
    A 401/403 from the provider means the key is invalid/unauthorized; other
    HTTP errors after successful auth are reported but treated as key-valid
    where the provider semantics make that unambiguous (e.g. Anthropic 400).
    """
    async with httpx.AsyncClient(timeout=TEST_TIMEOUT_SECONDS) as client:
        if key_type == "openrouter":
            # GET /api/v1/key requires auth and returns key metadata
            # (GET /models is unauthenticated and would not validate the key)
            resp = await client.get(
                "https://openrouter.ai/api/v1/key",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                return True, 200, "OpenRouter accepted the key."
            if resp.status_code in (401, 403):
                return False, resp.status_code, "OpenRouter rejected the key (unauthorized)."
            return False, resp.status_code, f"OpenRouter returned HTTP {resp.status_code}."

        if key_type == "openai":
            resp = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                return True, 200, "OpenAI accepted the key (models list OK)."
            if resp.status_code in (401, 403):
                return False, resp.status_code, "OpenAI rejected the key (unauthorized)."
            return False, resp.status_code, f"OpenAI returned HTTP {resp.status_code}."

        if key_type == "anthropic":
            # Cheapest possible live ping: 1-token message on the cheapest
            # current model. 401/403 = bad key. A 400/404/429 means auth
            # PASSED (invalid keys never get that far), so the key is valid.
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "ping"}],
                },
            )
            if resp.status_code == 200:
                return True, 200, "Anthropic accepted the key (1-token ping OK)."
            if resp.status_code in (401, 403):
                return False, resp.status_code, "Anthropic rejected the key (unauthorized)."
            if resp.status_code in (400, 404, 429):
                return True, resp.status_code, (
                    f"Key authenticated (Anthropic returned HTTP {resp.status_code} "
                    f"after auth — e.g. model/billing/rate-limit, not an auth failure)."
                )
            return False, resp.status_code, f"Anthropic returned HTTP {resp.status_code}."

        if key_type == "huggingface":
            resp = await client.get(
                "https://huggingface.co/api/whoami-v2",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                return True, 200, "Hugging Face accepted the token (whoami OK)."
            if resp.status_code in (401, 403):
                return False, resp.status_code, "Hugging Face rejected the token (unauthorized)."
            return False, resp.status_code, f"Hugging Face returned HTTP {resp.status_code}."

        if key_type == "groq":
            resp = await client.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                return True, 200, "Groq accepted the key (models list OK)."
            if resp.status_code in (401, 403):
                return False, resp.status_code, "Groq rejected the key (unauthorized)."
            return False, resp.status_code, f"Groq returned HTTP {resp.status_code}."

        if key_type == "xai":
            resp = await client.get(
                "https://api.x.ai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                return True, 200, "X.AI accepted the key (models list OK)."
            if resp.status_code in (401, 403):
                return False, resp.status_code, "X.AI rejected the key (unauthorized)."
            return False, resp.status_code, f"X.AI returned HTTP {resp.status_code}."

        if key_type == "google":
            resp = await client.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                params={"key": api_key, "pageSize": 1},
            )
            if resp.status_code == 200:
                return True, 200, "Google AI accepted the key (models list OK)."
            if resp.status_code in (400, 401, 403):
                return False, resp.status_code, "Google AI rejected the key (unauthorized/invalid)."
            return False, resp.status_code, f"Google AI returned HTTP {resp.status_code}."

        if key_type == "stripe":
            resp = await client.get(
                "https://api.stripe.com/v1/balance",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                return True, 200, "Stripe accepted the key (balance retrieved)."
            if resp.status_code in (401, 403):
                return False, resp.status_code, "Stripe rejected the key (unauthorized)."
            return False, resp.status_code, f"Stripe returned HTTP {resp.status_code}."

        if key_type == "cloudflare":
            resp = await client.get(
                "https://api.cloudflare.com/client/v4/user/tokens/verify",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                body = resp.json()
                token_status = ((body.get("result") or {}).get("status")) or "unknown"
                if body.get("success") and token_status == "active":
                    return True, 200, "Cloudflare token verified (status: active)."
                return False, 200, f"Cloudflare token verify returned status '{token_status}'."
            if resp.status_code in (401, 403):
                return False, resp.status_code, "Cloudflare rejected the token (unauthorized)."
            return False, resp.status_code, f"Cloudflare returned HTTP {resp.status_code}."

    return False, None, "No live test implemented for this key type."


@router.post("/{key_type}/test")
async def test_platform_key(
    key_type: str,
    request: Request,
    current_user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
):
    """
    Live-test a platform API key against its provider (admin only).

    Supported key types: openrouter, openai, anthropic, huggingface, groq,
    xai, google, stripe, cloudflare. Provisioning/LiteLLM keys have no
    external verification endpoint and return 400.

    Returns {ok, key_type, source, status_code, latency_ms, detail}.
    The key itself is never included in the response.
    """
    key_type = key_type.lower()

    if key_type in ("provisioning", "litellm"):
        raise HTTPException(
            status_code=400,
            detail=f"No live test available for key type '{key_type}' (no external verification endpoint).",
        )

    if key_type not in TESTABLE_KEY_TYPES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown key type '{key_type}'. Testable types: {', '.join(sorted(TESTABLE_KEY_TYPES))}",
        )

    try:
        api_key, source = await _resolve_platform_key(db_pool, key_type)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving {key_type} key for test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to resolve stored key")

    if not api_key:
        raise HTTPException(
            status_code=404,
            detail=f"No {key_type} key configured (checked database and environment).",
        )

    started = datetime.utcnow()
    try:
        ok, status_code, detail = await _run_key_test(key_type, api_key)
    except httpx.TimeoutException:
        latency_ms = round((datetime.utcnow() - started).total_seconds() * 1000, 1)
        return {
            "ok": False,
            "key_type": key_type,
            "source": source,
            "status_code": None,
            "latency_ms": latency_ms,
            "detail": f"Provider did not respond within {TEST_TIMEOUT_SECONDS:.0f}s.",
        }
    except httpx.HTTPError as e:
        latency_ms = round((datetime.utcnow() - started).total_seconds() * 1000, 1)
        return {
            "ok": False,
            "key_type": key_type,
            "source": source,
            "status_code": None,
            "latency_ms": latency_ms,
            "detail": f"Network error reaching provider: {e.__class__.__name__}: {e}",
        }

    latency_ms = round((datetime.utcnow() - started).total_seconds() * 1000, 1)

    logger.info(
        f"Admin {current_user.get('email', 'unknown')} tested platform key "
        f"'{key_type}' -> ok={ok} status={status_code}"
    )

    return {
        "ok": ok,
        "key_type": key_type,
        "source": source,
        "status_code": status_code,
        "latency_ms": latency_ms,
        "detail": detail,
    }
