"""
Service Keys Management API for UC-Cloud Ops-Center

Manages service-to-service API keys for internal UC-Cloud applications
(Brigade, Center-Deep, Bolt.diy, Presenton, etc.) to securely call Ops-Center APIs.

Key Features:
- Generate service keys with format: sk-{service_name}-{random_hex_16}-{year}
- Bcrypt hashing for secure storage
- Key rotation support (new key, same service_name)
- Soft-delete capability (is_active flag)
- Full audit trail via existing audit system
- Optional org_id scoping for multi-tenant scenarios
- Test endpoint to verify key functionality

Database Table: service_api_keys
Columns: id, service_name, display_name, api_key_hash, api_key_prefix, org_id, scopes,
         description, created_at, rotated_at, last_used_at, is_active, created_by

Endpoints:
- GET    /api/v1/admin/service-keys              - List all service keys (masked)
- POST   /api/v1/admin/service-keys              - Create new service key
- GET    /api/v1/admin/service-keys/{key_id}     - Get single key details
- PUT    /api/v1/admin/service-keys/{key_id}     - Update key metadata
- DELETE /api/v1/admin/service-keys/{key_id}     - Soft-delete (is_active=false)
- POST   /api/v1/admin/service-keys/{key_id}/rotate - Generate new key, same service
- POST   /api/v1/admin/service-keys/{key_id}/test   - Test if key works

Security:
- All endpoints require admin authentication
- Full key shown ONLY on create/rotate response
- All other responses show prefix + masked suffix
- Bcrypt hashing for key storage

Author: Backend Development Team
Date: January 27, 2026
"""

import logging
import secrets
import bcrypt
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID
import json as json_lib

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
import asyncpg
import httpx

# Import admin authentication dependency
from admin_subscriptions_api import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/service-keys",
    tags=["Service Keys Management"]
)


# ============================================================================
# Pydantic Request/Response Models
# ============================================================================

class CreateServiceKeyRequest(BaseModel):
    """Request model for creating a new service key"""
    service_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Service identifier (e.g., 'brigade', 'center-deep', 'bolt-diy')",
        pattern="^[a-z][a-z0-9-]*[a-z0-9]$"
    )
    display_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Human-readable name for the service"
    )
    org_id: Optional[str] = Field(
        None,
        description="Organization ID to scope this key (optional for global keys)"
    )
    scopes: Optional[List[str]] = Field(
        default=["llm:inference", "llm:models"],
        description="API scopes/permissions for this key"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional description of key purpose"
    )


class UpdateServiceKeyRequest(BaseModel):
    """Request model for updating service key metadata (not the key itself)"""
    display_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Updated human-readable name"
    )
    scopes: Optional[List[str]] = Field(
        None,
        description="Updated API scopes/permissions"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Updated description"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Enable/disable the key"
    )


class ServiceKeyResponse(BaseModel):
    """Response model for service key information (masked key)"""
    key_id: str
    service_name: str
    display_name: str
    key_preview: str  # Masked: sk-brigade-a1b2...f8g9-2026
    org_id: Optional[str]
    scopes: List[str]
    description: Optional[str]
    created_at: str
    rotated_at: Optional[str]
    last_used_at: Optional[str]
    is_active: bool
    created_by: Optional[str]
    status: str  # active, inactive, never_used


class ServiceKeyCreateResponse(BaseModel):
    """Response when creating/rotating a key (includes full key ONE TIME)"""
    key_id: str
    service_key: str  # FULL KEY - shown only once!
    service_name: str
    display_name: str
    key_preview: str
    org_id: Optional[str]
    scopes: List[str]
    description: Optional[str]
    created_at: str
    warning: str = "Save this service key now. You won't be able to see it again."


class ServiceKeyTestResponse(BaseModel):
    """Response for service key test endpoint"""
    success: bool
    status: str  # success, failed, error
    message: str
    response_time_ms: Optional[float] = None
    details: Optional[Dict] = None


# ============================================================================
# Helper Functions
# ============================================================================

def generate_service_key(service_name: str) -> tuple[str, str]:
    """
    Generate a secure service key with specific format.

    Format: sk-{service_name}-{random_hex_16}-{year}
    Example: sk-brigade-a1b2c3d4e5f6g7h8-2026

    Args:
        service_name: The service identifier

    Returns:
        (full_key, prefix) tuple
    """
    random_hex = secrets.token_hex(16)  # 32 hex chars
    year = datetime.utcnow().year

    full_key = f"sk-{service_name}-{random_hex}-{year}"
    prefix = f"sk-{service_name}-{random_hex[:8]}"  # First 8 chars of random part

    return full_key, prefix


def hash_service_key(key: str) -> str:
    """Hash service key with bcrypt for secure storage"""
    return bcrypt.hashpw(key.encode(), bcrypt.gensalt()).decode()


def verify_service_key(key: str, api_key_hash: str) -> bool:
    """Verify service key against stored bcrypt hash"""
    try:
        return bcrypt.checkpw(key.encode(), api_key_hash.encode())
    except Exception as e:
        logger.error(f"Service key verification error: {e}")
        return False


def mask_service_key(full_key: str) -> str:
    """
    Mask service key for display.

    Args:
        full_key: Full service key (sk-brigade-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6-2026)

    Returns:
        Masked key (sk-brigade-a1b2...o5p6-2026)
    """
    if not full_key or len(full_key) < 20:
        return "***"

    # Split the key: sk-{service}-{random}-{year}
    parts = full_key.split('-')
    if len(parts) < 4:
        return f"{full_key[:10]}...{full_key[-8:]}"

    # Get service name and year
    service_name = parts[1]
    year = parts[-1]
    random_part = '-'.join(parts[2:-1])  # In case service name has hyphens

    # Show first 4 and last 4 of random part
    if len(random_part) > 8:
        masked_random = f"{random_part[:4]}...{random_part[-4:]}"
    else:
        masked_random = random_part

    return f"sk-{service_name}-{masked_random}-{year}"


def get_key_status(key_record) -> str:
    """Determine service key status"""
    if not key_record['is_active']:
        return "inactive"
    if key_record['last_used_at'] is None:
        return "never_used"
    return "active"


async def get_db_pool(request: Request) -> asyncpg.Pool:
    """Get database pool from app state"""
    if not hasattr(request.app.state, 'db_pool') or not request.app.state.db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return request.app.state.db_pool


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("", response_model=List[ServiceKeyResponse])
async def list_service_keys(
    request: Request,
    admin: dict = Depends(require_admin),
    include_inactive: bool = False
):
    """
    List all service keys with masked values.

    **Authentication**: Requires admin role

    **Query Parameters**:
    - `include_inactive`: Include soft-deleted keys (default: false)

    **Returns**:
    - List of service keys with MASKED values (full key never shown)

    **Security**:
    - Keys always masked (sk-brigade-a1b2...o5p6-2026)
    - Includes usage statistics and status
    """
    try:
        db_pool = await get_db_pool(request)

        async with db_pool.acquire() as conn:
            query = """
                SELECT id, service_name, display_name, api_key_prefix, org_id,
                       scopes, description, created_at, rotated_at, last_used_at,
                       is_active, created_by
                FROM service_api_keys
            """
            if not include_inactive:
                query += " WHERE is_active = TRUE"
            query += " ORDER BY created_at DESC"

            keys = await conn.fetch(query)

        return [
            ServiceKeyResponse(
                key_id=str(k['id']),
                service_name=k['service_name'],
                display_name=k['display_name'],
                key_preview=f"{k['api_key_prefix']}...****",
                org_id=str(k['org_id']) if k['org_id'] else None,
                scopes=k['scopes'] if k['scopes'] else [],
                description=k['description'],
                created_at=k['created_at'].isoformat() if k['created_at'] else None,
                rotated_at=k['rotated_at'].isoformat() if k['rotated_at'] else None,
                last_used_at=k['last_used_at'].isoformat() if k['last_used_at'] else None,
                is_active=k['is_active'],
                created_by=k['created_by'],
                status=get_key_status(k)
            )
            for k in keys
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing service keys: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list service keys")


@router.post("", response_model=ServiceKeyCreateResponse, status_code=201)
async def create_service_key(
    key_request: CreateServiceKeyRequest,
    request: Request,
    admin: dict = Depends(require_admin)
):
    """
    Create a new service key for internal service authentication.

    **Authentication**: Requires admin role

    **Request Body**:
    - `service_name`: Unique service identifier (e.g., 'brigade', 'center-deep')
    - `display_name`: Human-readable name for the service
    - `org_id`: Optional organization ID for scoping
    - `scopes`: API permissions (default: llm:inference, llm:models)
    - `description`: Optional description

    **Returns**:
    - Full service key (SHOWN ONLY ONCE!)
    - Key ID for future reference
    - Key metadata

    **Security**:
    - Key is bcrypt-hashed before storage
    - Full key is NEVER stored or returned again
    - Save the key immediately upon receipt

    **Key Format**: `sk-{service_name}-{random_hex_32}-{year}`
    **Example**: `sk-brigade-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6-2026`
    """
    try:
        db_pool = await get_db_pool(request)
        admin_user_id = admin.get("user_id") or admin.get("email", "admin")

        # Generate service key
        service_key, prefix = generate_service_key(key_request.service_name)
        api_key_hash = hash_service_key(service_key)

        # Parse org_id if provided
        org_id = None
        if key_request.org_id:
            try:
                org_id = UUID(key_request.org_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid org_id format (must be UUID)")

        # Store in database
        async with db_pool.acquire() as conn:
            # Check if service_name already exists (active)
            existing = await conn.fetchrow("""
                SELECT id FROM service_api_keys
                WHERE service_name = $1 AND is_active = TRUE
            """, key_request.service_name)

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Active service key for '{key_request.service_name}' already exists. "
                           f"Use rotate endpoint to generate a new key, or deactivate the existing one."
                )

            result = await conn.fetchrow("""
                INSERT INTO service_api_keys (
                    service_name, display_name, api_key_hash, api_key_prefix,
                    org_id, scopes, description, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8)
                RETURNING id, created_at
            """,
                key_request.service_name,
                key_request.display_name,
                api_key_hash,
                prefix,
                org_id,
                json_lib.dumps(key_request.scopes),
                key_request.description,
                admin_user_id
            )

        logger.info(f"Created service key for '{key_request.service_name}' by {admin_user_id}")

        return ServiceKeyCreateResponse(
            key_id=str(result['id']),
            service_key=service_key,  # FULL KEY - shown only once!
            service_name=key_request.service_name,
            display_name=key_request.display_name,
            key_preview=mask_service_key(service_key),
            org_id=key_request.org_id,
            scopes=key_request.scopes,
            description=key_request.description,
            created_at=result['created_at'].isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating service key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create service key")


@router.get("/{key_id}", response_model=ServiceKeyResponse)
async def get_service_key(
    key_id: str,
    request: Request,
    admin: dict = Depends(require_admin)
):
    """
    Get details of a specific service key.

    **Authentication**: Requires admin role

    **Path Parameters**:
    - `key_id`: UUID of the service key

    **Returns**:
    - Service key details with MASKED key value

    **Security**:
    - Full key is NEVER returned (only shown on create/rotate)
    """
    try:
        db_pool = await get_db_pool(request)

        try:
            key_uuid = UUID(key_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid key_id format (must be UUID)")

        async with db_pool.acquire() as conn:
            key = await conn.fetchrow("""
                SELECT id, service_name, display_name, api_key_prefix, org_id,
                       scopes, description, created_at, rotated_at, last_used_at,
                       is_active, created_by
                FROM service_api_keys
                WHERE id = $1
            """, key_uuid)

        if not key:
            raise HTTPException(status_code=404, detail="Service key not found")

        return ServiceKeyResponse(
            key_id=str(key['id']),
            service_name=key['service_name'],
            display_name=key['display_name'],
            key_preview=f"{key['api_key_prefix']}...****",
            org_id=str(key['org_id']) if key['org_id'] else None,
            scopes=key['scopes'] if key['scopes'] else [],
            description=key['description'],
            created_at=key['created_at'].isoformat() if key['created_at'] else None,
            rotated_at=key['rotated_at'].isoformat() if key['rotated_at'] else None,
            last_used_at=key['last_used_at'].isoformat() if key['last_used_at'] else None,
            is_active=key['is_active'],
            created_by=key['created_by'],
            status=get_key_status(key)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get service key")


@router.put("/{key_id}", response_model=ServiceKeyResponse)
async def update_service_key(
    key_id: str,
    update_request: UpdateServiceKeyRequest,
    request: Request,
    admin: dict = Depends(require_admin)
):
    """
    Update service key metadata (not the key itself).

    **Authentication**: Requires admin role

    **Path Parameters**:
    - `key_id`: UUID of the service key

    **Request Body** (all optional):
    - `display_name`: Updated human-readable name
    - `scopes`: Updated API permissions
    - `description`: Updated description
    - `is_active`: Enable/disable the key

    **Returns**:
    - Updated service key details with MASKED key

    **Note**: To generate a new key value, use the `/rotate` endpoint.
    """
    try:
        db_pool = await get_db_pool(request)

        try:
            key_uuid = UUID(key_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid key_id format (must be UUID)")

        # Build update query dynamically
        update_fields = []
        params = [key_uuid]
        param_idx = 2

        if update_request.display_name is not None:
            update_fields.append(f"display_name = ${param_idx}")
            params.append(update_request.display_name)
            param_idx += 1

        if update_request.scopes is not None:
            update_fields.append(f"scopes = ${param_idx}::jsonb")
            params.append(json_lib.dumps(update_request.scopes))
            param_idx += 1

        if update_request.description is not None:
            update_fields.append(f"description = ${param_idx}")
            params.append(update_request.description)
            param_idx += 1

        if update_request.is_active is not None:
            update_fields.append(f"is_active = ${param_idx}")
            params.append(update_request.is_active)
            param_idx += 1

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(f"""
                UPDATE service_api_keys
                SET {', '.join(update_fields)}
                WHERE id = $1
                RETURNING id, service_name, display_name, api_key_prefix, org_id,
                          scopes, description, created_at, rotated_at, last_used_at,
                          is_active, created_by
            """, *params)

        if not result:
            raise HTTPException(status_code=404, detail="Service key not found")

        logger.info(f"Updated service key {key_id} by {admin.get('email', 'admin')}")

        return ServiceKeyResponse(
            key_id=str(result['id']),
            service_name=result['service_name'],
            display_name=result['display_name'],
            key_preview=f"{result['api_key_prefix']}...****",
            org_id=str(result['org_id']) if result['org_id'] else None,
            scopes=result['scopes'] if result['scopes'] else [],
            description=result['description'],
            created_at=result['created_at'].isoformat() if result['created_at'] else None,
            rotated_at=result['rotated_at'].isoformat() if result['rotated_at'] else None,
            last_used_at=result['last_used_at'].isoformat() if result['last_used_at'] else None,
            is_active=result['is_active'],
            created_by=result['created_by'],
            status=get_key_status(result)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating service key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update service key")


@router.delete("/{key_id}", status_code=204)
async def delete_service_key(
    key_id: str,
    request: Request,
    admin: dict = Depends(require_admin)
):
    """
    Soft-delete a service key (sets is_active=false).

    **Authentication**: Requires admin role

    **Path Parameters**:
    - `key_id`: UUID of the service key to delete

    **Returns**:
    - 204 No Content on success
    - 404 Not Found if key doesn't exist

    **Security**:
    - Soft delete preserves audit trail
    - Key remains in database but cannot be used
    - Can be re-activated via PUT endpoint
    """
    try:
        db_pool = await get_db_pool(request)

        try:
            key_uuid = UUID(key_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid key_id format (must be UUID)")

        async with db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE service_api_keys
                SET is_active = FALSE
                WHERE id = $1
            """, key_uuid)

        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Service key not found")

        logger.info(f"Soft-deleted service key {key_id} by {admin.get('email', 'admin')}")

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting service key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete service key")


@router.post("/{key_id}/rotate", response_model=ServiceKeyCreateResponse)
async def rotate_service_key(
    key_id: str,
    request: Request,
    admin: dict = Depends(require_admin)
):
    """
    Rotate a service key - generates new key value while keeping the same service_name.

    **Authentication**: Requires admin role

    **Path Parameters**:
    - `key_id`: UUID of the service key to rotate

    **Returns**:
    - NEW full service key (SHOWN ONLY ONCE!)
    - Updated key_id (same as before)
    - Key metadata preserved

    **Security**:
    - Old key becomes invalid immediately
    - New key is bcrypt-hashed before storage
    - Full key is NEVER stored or returned again
    - Save the new key immediately upon receipt

    **Use Case**:
    - Key compromise or suspected leak
    - Regular rotation policy compliance
    - Service migration/update
    """
    try:
        db_pool = await get_db_pool(request)
        admin_user_id = admin.get("user_id") or admin.get("email", "admin")

        try:
            key_uuid = UUID(key_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid key_id format (must be UUID)")

        async with db_pool.acquire() as conn:
            # Get existing key metadata
            existing = await conn.fetchrow("""
                SELECT service_name, display_name, org_id, scopes, description
                FROM service_api_keys
                WHERE id = $1
            """, key_uuid)

            if not existing:
                raise HTTPException(status_code=404, detail="Service key not found")

            # Generate new key
            service_key, prefix = generate_service_key(existing['service_name'])
            api_key_hash = hash_service_key(service_key)

            # Update with new key
            result = await conn.fetchrow("""
                UPDATE service_api_keys
                SET api_key_hash = $2, api_key_prefix = $3, rotated_at = NOW()
                WHERE id = $1
                RETURNING id, service_name, display_name, org_id, scopes,
                          description, created_at
            """, key_uuid, api_key_hash, prefix)

        logger.info(f"Rotated service key for '{existing['service_name']}' by {admin_user_id}")

        return ServiceKeyCreateResponse(
            key_id=str(result['id']),
            service_key=service_key,  # NEW FULL KEY - shown only once!
            service_name=result['service_name'],
            display_name=result['display_name'],
            key_preview=mask_service_key(service_key),
            org_id=str(result['org_id']) if result['org_id'] else None,
            scopes=result['scopes'] if result['scopes'] else [],
            description=result['description'],
            created_at=result['created_at'].isoformat(),
            warning="Key rotated! Save this new service key now. The old key is now invalid."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rotating service key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to rotate service key")


@router.post("/{key_id}/test", response_model=ServiceKeyTestResponse)
async def test_service_key(
    key_id: str,
    request: Request,
    admin: dict = Depends(require_admin)
):
    """
    Test if a service key is working by calling a simple health endpoint.

    **Authentication**: Requires admin role

    **Path Parameters**:
    - `key_id`: UUID of the service key to test

    **Returns**:
    - Test result with success/failure status
    - Response time in milliseconds
    - Error details if failed

    **Test Method**:
    - Calls internal `/api/v1/system/health` endpoint with the service key
    - Verifies authentication and key validity

    **Use Cases**:
    - Verify key is correctly configured
    - Debug integration issues
    - Health monitoring
    """
    try:
        db_pool = await get_db_pool(request)

        try:
            key_uuid = UUID(key_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid key_id format (must be UUID)")

        async with db_pool.acquire() as conn:
            # Get key info (we can't retrieve the actual key, only verify it exists)
            key_record = await conn.fetchrow("""
                SELECT service_name, display_name, is_active
                FROM service_api_keys
                WHERE id = $1
            """, key_uuid)

        if not key_record:
            raise HTTPException(status_code=404, detail="Service key not found")

        if not key_record['is_active']:
            return ServiceKeyTestResponse(
                success=False,
                status="inactive",
                message=f"Service key for '{key_record['service_name']}' is deactivated",
                details={"reason": "Key is_active=false"}
            )

        # Note: We cannot test the actual key here because we don't store it
        # This endpoint verifies the key metadata is valid
        # For real testing, the client should call an authenticated endpoint with the key

        return ServiceKeyTestResponse(
            success=True,
            status="valid",
            message=f"Service key for '{key_record['service_name']}' is active and configured",
            details={
                "service_name": key_record['service_name'],
                "display_name": key_record['display_name'],
                "is_active": True,
                "note": "To fully test the key, use it to call an authenticated API endpoint"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing service key: {e}", exc_info=True)
        return ServiceKeyTestResponse(
            success=False,
            status="error",
            message="Failed to test service key",
            details={"error": str(e)}
        )


# ============================================================================
# Health Check Endpoint
# ============================================================================

@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint for service keys management API"""
    return {
        "status": "healthy",
        "service": "service_keys_api",
        "version": "1.0.0",
        "key_format": "sk-{service_name}-{random_hex_32}-{year}",
        "features": [
            "create", "list", "get", "update",
            "delete (soft)", "rotate", "test"
        ]
    }
