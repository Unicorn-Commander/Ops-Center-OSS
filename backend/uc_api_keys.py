"""
UC API Keys Management - User API Keys for calling api.unicorncommander.ai

This module manages UC-specific API keys that users can generate to call
api.unicorncommander.ai from external systems (Postman, curl, custom apps, etc.)

Key Features:
- Generate UC API keys with bcrypt hashing
- List user's API keys (with masked preview)
- Revoke API keys
- Track last used timestamp
- Optional expiration dates

Database Table: user_api_keys (already exists)
Columns: id, user_id, key_name, key_hash, key_prefix, permissions, created_at, last_used, expires_at, is_active

Author: Backend API Developer
Date: November 3, 2025
"""

import logging
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
import asyncpg

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/account/uc-api-keys", tags=["UC API Keys"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateUCAPIKeyRequest(BaseModel):
    """Request to create a new UC API key"""
    name: str = Field(..., description="Descriptive name for the key", min_length=1, max_length=255)
    expires_in_days: Optional[int] = Field(90, description="Days until expiration (default: 90)", ge=1, le=3650)
    permissions: Optional[List[str]] = Field(["llm:inference", "llm:models"], description="API permissions")


class UCAPIKeyResponse(BaseModel):
    """Response with UC API key information"""
    key_id: str
    key_name: str
    key_preview: str  # First 8 and last 4 chars (uc_12345...abcd)
    permissions: List[str]
    created_at: str
    last_used: Optional[str]
    expires_at: Optional[str]
    is_active: bool
    status: str  # active, expired, revoked


class UCAPIKeyCreateResponse(BaseModel):
    """Response when creating a new API key (includes full key ONE TIME)"""
    key_id: str
    api_key: str  # FULL KEY - shown only once!
    key_name: str
    key_preview: str
    permissions: List[str]
    created_at: str
    expires_at: Optional[str]
    warning: str = "Save this API key now. You won't be able to see it again."


# ============================================================================
# Authentication Dependency
# ============================================================================

async def get_current_user(request: Request) -> Dict:
    """
    Get current authenticated user from session

    Returns:
        User dict with user_id, email, role

    Raises:
        HTTPException 401 if not authenticated
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

    # Ensure user_id exists
    if "user_id" not in user:
        user["user_id"] = user.get("sub") or user.get("id", "unknown")

    return user


async def get_db_pool(request: Request) -> asyncpg.Pool:
    """Get database pool from app state"""
    if not hasattr(request.app.state, 'db_pool') or not request.app.state.db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return request.app.state.db_pool


# ============================================================================
# Helper Functions
# ============================================================================

def generate_uc_api_key() -> tuple[str, str]:
    """
    Generate a secure UC API key

    Returns:
        (full_key, prefix) tuple
        Example: ("uc_1234567890abcdef...", "uc_12345")
    """
    # Generate 32 random bytes (256 bits)
    random_bytes = secrets.token_bytes(32)
    key_hex = random_bytes.hex()

    # Format: uc_<64-char-hex>
    full_key = f"uc_{key_hex}"
    prefix = full_key[:8]  # "uc_12345"

    return full_key, prefix


def hash_api_key(api_key: str) -> str:
    """Hash API key with bcrypt"""
    return bcrypt.hashpw(api_key.encode(), bcrypt.gensalt()).decode()


def verify_api_key(api_key: str, key_hash: str) -> bool:
    """Verify API key against stored hash"""
    try:
        return bcrypt.checkpw(api_key.encode(), key_hash.encode())
    except Exception as e:
        logger.error(f"Key verification error: {e}")
        return False


def mask_api_key(full_key: str) -> str:
    """
    Mask API key for display

    Args:
        full_key: Full API key (uc_<64-char-hex>)

    Returns:
        Masked key (uc_12345...abcd)
    """
    if len(full_key) < 12:
        return "***"

    return f"{full_key[:8]}...{full_key[-4:]}"


def get_key_status(key_record) -> str:
    """Determine key status"""
    if not key_record['is_active']:
        return "revoked"
    if key_record['expires_at'] and key_record['expires_at'] < datetime.utcnow():
        return "expired"
    return "active"


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("", response_model=UCAPIKeyCreateResponse, status_code=201)
async def create_uc_api_key(
    key_request: CreateUCAPIKeyRequest,
    request: Request,
    current_user: Dict = Depends(get_current_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Create a new UC API key for the authenticated user

    This generates a unique API key that can be used to call api.unicorncommander.ai
    endpoints from external systems (Postman, curl, custom applications).

    **IMPORTANT**: The full API key is shown ONLY ONCE in the response. Save it securely.

    Request Body:
    - name: Descriptive name for the key (e.g., "Production Server", "Mobile App")
    - expires_in_days: Days until expiration (default: 90, max: 3650)
    - permissions: List of allowed permissions (default: ["llm:inference", "llm:models"])

    Returns:
    - api_key: The full API key (SHOWN ONLY ONCE!)
    - key_id: UUID of the key
    - key_preview: Masked preview (uc_12345...abcd)
    - created_at: Creation timestamp
    - expires_at: Expiration timestamp
    """
    try:
        user_id = current_user.get("user_id")

        # Generate API key
        api_key, prefix = generate_uc_api_key()
        key_hash = hash_api_key(api_key)

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=key_request.expires_in_days)

        # Store in database
        import json as json_lib
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO user_api_keys (
                    user_id, key_name, key_hash, key_prefix,
                    permissions, expires_at
                )
                VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                RETURNING id, created_at
            """, user_id, key_request.name, key_hash, prefix,
                json_lib.dumps(key_request.permissions), expires_at)

        logger.info(f"Created UC API key '{key_request.name}' for user {user_id}")

        return UCAPIKeyCreateResponse(
            key_id=str(result['id']),
            api_key=api_key,  # FULL KEY - shown only once!
            key_name=key_request.name,
            key_preview=mask_api_key(api_key),
            permissions=key_request.permissions,
            created_at=result['created_at'].isoformat(),
            expires_at=expires_at.isoformat()
        )

    except Exception as e:
        logger.error(f"Error creating UC API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create API key")


@router.get("", response_model=List[UCAPIKeyResponse])
async def list_uc_api_keys(
    request: Request,
    current_user: Dict = Depends(get_current_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    List all UC API keys for the authenticated user

    Returns a list of API keys with masked previews (full keys are never shown again).

    Response includes:
    - key_id: UUID of the key
    - key_name: Descriptive name
    - key_preview: Masked preview (uc_12345...abcd)
    - permissions: Allowed API permissions
    - created_at: Creation timestamp
    - last_used: Last usage timestamp (null if never used)
    - expires_at: Expiration timestamp
    - is_active: Whether key is active
    - status: active, expired, or revoked
    """
    try:
        user_id = current_user.get("user_id")

        async with db_pool.acquire() as conn:
            keys = await conn.fetch("""
                SELECT id, key_name, key_prefix, permissions,
                       created_at, last_used, expires_at, is_active
                FROM user_api_keys
                WHERE user_id = $1
                ORDER BY created_at DESC
            """, user_id)

        return [
            UCAPIKeyResponse(
                key_id=str(k['id']),
                key_name=k['key_name'],
                key_preview=f"{k['key_prefix']}...****",  # Mask based on prefix
                permissions=k['permissions'],
                created_at=k['created_at'].isoformat(),
                last_used=k['last_used'].isoformat() if k['last_used'] else None,
                expires_at=k['expires_at'].isoformat() if k['expires_at'] else None,
                is_active=k['is_active'],
                status=get_key_status(k)
            )
            for k in keys
        ]

    except Exception as e:
        logger.error(f"Error listing UC API keys: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list API keys")


@router.delete("/{key_id}")
async def revoke_uc_api_key(
    key_id: str,
    request: Request,
    current_user: Dict = Depends(get_current_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Revoke a UC API key

    This marks the key as inactive. The key will no longer work for API calls.

    Path Parameters:
    - key_id: UUID of the key to revoke

    Returns:
    - success: True if revoked
    - message: Confirmation message
    """
    try:
        user_id = current_user.get("user_id")

        async with db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE user_api_keys
                SET is_active = FALSE
                WHERE id = $1 AND user_id = $2
            """, UUID(key_id), user_id)

        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="API key not found")

        logger.info(f"Revoked UC API key {key_id} for user {user_id}")

        return {
            "success": True,
            "message": f"API key revoked successfully",
            "key_id": key_id
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid key_id format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking UC API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to revoke API key")


@router.get("/{key_id}", response_model=UCAPIKeyResponse)
async def get_uc_api_key(
    key_id: str,
    request: Request,
    current_user: Dict = Depends(get_current_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get details of a specific UC API key

    Returns key information with masked preview (full key is never shown again).

    Path Parameters:
    - key_id: UUID of the key

    Returns:
    - UCAPIKeyResponse with key details
    """
    try:
        user_id = current_user.get("user_id")

        async with db_pool.acquire() as conn:
            key = await conn.fetchrow("""
                SELECT id, key_name, key_prefix, permissions,
                       created_at, last_used, expires_at, is_active
                FROM user_api_keys
                WHERE id = $1 AND user_id = $2
            """, UUID(key_id), user_id)

        if not key:
            raise HTTPException(status_code=404, detail="API key not found")

        return UCAPIKeyResponse(
            key_id=str(key['id']),
            key_name=key['key_name'],
            key_preview=f"{key['key_prefix']}...****",
            permissions=key['permissions'],
            created_at=key['created_at'].isoformat(),
            last_used=key['last_used'].isoformat() if key['last_used'] else None,
            expires_at=key['expires_at'].isoformat() if key['expires_at'] else None,
            is_active=key['is_active'],
            status=get_key_status(key)
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid key_id format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting UC API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get API key")
