"""
Credential Management API Endpoints for UC-Cloud Ops-Center

REST API for managing service credentials (Cloudflare, NameCheap, GitHub, Stripe)

Endpoints:
- POST   /api/v1/credentials                  - Create credential
- GET    /api/v1/credentials                  - List all credentials (masked)
- GET    /api/v1/credentials/{service}/{type} - Get single credential (masked)
- PUT    /api/v1/credentials/{service}/{type} - Update credential
- DELETE /api/v1/credentials/{service}/{type} - Delete credential
- POST   /api/v1/credentials/{service}/test   - Test credential validity
- GET    /api/v1/credentials/services         - List supported services

Security:
- Requires admin authentication
- All credentials returned with masked values
- Audit logging for all operations
- Rate limiting on test operations

Epic 1.6/1.7: Service Credential Management
Author: Backend Development Team Lead
Date: October 23, 2025
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import logging

# Import credential manager
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))
from credential_manager import (
    CredentialManager,
    CredentialManagementError,
    CredentialNotFoundError,
    CredentialValidationError,
    UnsupportedServiceError,
    SUPPORTED_SERVICES,
    get_supported_services,
    validate_service
)

# Import authentication
from admin_subscriptions_api import require_admin

# Import database connection
from database.connection import get_db_pool

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/credentials", tags=["credentials", "security"])


# ==================== Pydantic Request Models ====================

class CreateCredentialRequest(BaseModel):
    """Request model for creating credential"""
    service: str = Field(..., min_length=2, max_length=50, description="Service name (cloudflare, namecheap, github, stripe)")
    credential_type: str = Field(..., min_length=2, max_length=50, description="Credential type (api_token, api_key, etc.)")
    value: str = Field(..., min_length=10, description="Credential value (plaintext)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata (description, etc.)")

    @validator('service')
    def validate_service_name(cls, v):
        """Validate service name"""
        v = v.lower().strip()
        if not validate_service(v):
            supported = ', '.join(SUPPORTED_SERVICES.keys())
            raise ValueError(f"Unsupported service. Supported services: {supported}")
        return v

    @validator('credential_type')
    def validate_credential_type(cls, v, values):
        """Validate credential type for service"""
        v = v.lower().strip()
        if 'service' in values:
            service = values['service']
            service_config = SUPPORTED_SERVICES.get(service, {})
            valid_types = service_config.get('credential_types', [])
            if v not in valid_types:
                raise ValueError(
                    f"Invalid credential type '{v}' for service '{service}'. "
                    f"Valid types: {', '.join(valid_types)}"
                )
        return v


class UpdateCredentialRequest(BaseModel):
    """Request model for updating credential"""
    value: str = Field(..., min_length=10, description="New credential value (plaintext)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional updated metadata")


class TestCredentialRequest(BaseModel):
    """Request model for testing credential"""
    value: Optional[str] = Field(None, min_length=10, description="Credential value to test (if not stored)")


class CredentialResponse(BaseModel):
    """Response model for credential info"""
    id: str
    service: str
    service_name: str
    credential_type: str
    masked_value: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: Optional[str] = None
    last_tested: Optional[str] = None
    test_status: Optional[str] = None


class ServiceInfo(BaseModel):
    """Response model for service info"""
    service: str
    name: str
    credential_types: List[str]
    has_test: bool
    configured: bool = False


class TestResultResponse(BaseModel):
    """Response model for credential test result"""
    success: bool
    status: str  # success, failed, error
    message: str
    details: Optional[Dict[str, Any]] = None


# ==================== Helper Functions ====================

async def get_credential_manager(request: Request) -> CredentialManager:
    """
    Get CredentialManager instance with database connection

    Args:
        request: FastAPI request object

    Returns:
        CredentialManager instance
    """
    db_pool = await get_db_pool()
    async with db_pool.acquire() as connection:
        return CredentialManager(db_connection=connection)


# ==================== API Endpoints ====================

@router.post("", response_model=CredentialResponse, status_code=201)
async def create_credential(
    request: CreateCredentialRequest,
    admin: dict = Depends(require_admin)
):
    """
    Create or update service credential

    **Authentication**: Requires admin role

    **Request Body**:
    - `service`: Service name (cloudflare, namecheap, github, stripe)
    - `credential_type`: Credential type (api_token, api_key, etc.)
    - `value`: Plaintext credential value
    - `metadata`: Optional metadata (description, etc.)

    **Returns**:
    - Credential info with MASKED value (never returns plaintext)

    **Security**:
    - Credential encrypted with Fernet (AES-128-CBC)
    - Stored in PostgreSQL service_credentials table
    - Audit log created for operation
    - Value never exposed in response
    """
    try:
        credential_manager = await get_credential_manager(request)
        user_id = admin.get("user_id") or admin.get("email")

        result = await credential_manager.create_credential(
            user_id=user_id,
            service=request.service,
            credential_type=request.credential_type,
            value=request.value,
            metadata=request.metadata
        )

        return CredentialResponse(**result)

    except UnsupportedServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CredentialValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create credential: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create credential: {str(e)}")


@router.get("", response_model=List[CredentialResponse])
async def list_credentials(
    request: Request,
    admin: dict = Depends(require_admin)
):
    """
    List all credentials for authenticated user

    **Authentication**: Requires admin role

    **Returns**:
    - List of credentials with MASKED values (never returns plaintext)

    **Security**:
    - Only returns credentials owned by authenticated user
    - Values always masked (e.g., "sk-ab***xyz")
    - Includes test status and last tested timestamp
    """
    try:
        credential_manager = await get_credential_manager(request)
        user_id = admin.get("user_id") or admin.get("email")

        credentials = await credential_manager.list_credentials(user_id=user_id)

        return [CredentialResponse(**cred) for cred in credentials]

    except Exception as e:
        logger.error(f"Failed to list credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to list credentials")


@router.get("/{service}/{credential_type}", response_model=CredentialResponse)
async def get_credential(
    service: str,
    credential_type: str,
    request: Request,
    admin: dict = Depends(require_admin)
):
    """
    Get single credential info (MASKED value only)

    **Authentication**: Requires admin role

    **Path Parameters**:
    - `service`: Service name
    - `credential_type`: Credential type

    **Returns**:
    - Credential info with MASKED value

    **Security**:
    - NEVER returns plaintext credential
    - Use `get_credential_for_api()` internally for API calls
    """
    try:
        credential_manager = await get_credential_manager(request)
        user_id = admin.get("user_id") or admin.get("email")

        credentials = await credential_manager.list_credentials(user_id=user_id)

        # Find matching credential
        for cred in credentials:
            if cred["service"] == service and cred["credential_type"] == credential_type:
                return CredentialResponse(**cred)

        raise HTTPException(
            status_code=404,
            detail=f"Credential not found for service={service}, type={credential_type}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get credential: {e}")
        raise HTTPException(status_code=500, detail="Failed to get credential")


@router.put("/{service}/{credential_type}", response_model=CredentialResponse)
async def update_credential(
    service: str,
    credential_type: str,
    request_body: UpdateCredentialRequest,
    request: Request,
    admin: dict = Depends(require_admin)
):
    """
    Update existing credential

    **Authentication**: Requires admin role

    **Path Parameters**:
    - `service`: Service name
    - `credential_type`: Credential type

    **Request Body**:
    - `value`: New plaintext credential value
    - `metadata`: Optional updated metadata

    **Returns**:
    - Updated credential info with MASKED value

    **Security**:
    - Credential re-encrypted with new value
    - Audit log created for update
    - Test status reset (requires re-test)
    """
    try:
        credential_manager = await get_credential_manager(request)
        user_id = admin.get("user_id") or admin.get("email")

        result = await credential_manager.update_credential(
            user_id=user_id,
            service=service,
            credential_type=credential_type,
            new_value=request_body.value,
            metadata=request_body.metadata
        )

        return CredentialResponse(**result)

    except UnsupportedServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CredentialValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update credential: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update credential: {str(e)}")


@router.delete("/{service}/{credential_type}", status_code=204)
async def delete_credential(
    service: str,
    credential_type: str,
    request: Request,
    admin: dict = Depends(require_admin)
):
    """
    Delete credential (soft delete)

    **Authentication**: Requires admin role

    **Path Parameters**:
    - `service`: Service name
    - `credential_type`: Credential type

    **Returns**:
    - 204 No Content on success
    - 404 Not Found if credential doesn't exist

    **Security**:
    - Soft delete (sets is_active = false)
    - Credential remains in database for audit trail
    - Audit log created for deletion
    """
    try:
        credential_manager = await get_credential_manager(request)
        user_id = admin.get("user_id") or admin.get("email")

        deleted = await credential_manager.delete_credential(
            user_id=user_id,
            service=service,
            credential_type=credential_type
        )

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Credential not found for service={service}, type={credential_type}"
            )

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete credential: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete credential")


@router.post("/{service}/test", response_model=TestResultResponse)
async def test_credential(
    service: str,
    request_body: TestCredentialRequest,
    request: Request,
    admin: dict = Depends(require_admin)
):
    """
    Test credential by calling service API

    **Authentication**: Requires admin role

    **Path Parameters**:
    - `service`: Service name

    **Request Body**:
    - `value`: Optional credential value to test (if not stored in DB)

    **Returns**:
    - Test result with success/failure status and message

    **Supported Services**:
    - **Cloudflare**: Calls `/user/tokens/verify` endpoint
    - **GitHub**: Calls `/user` endpoint
    - **Stripe**: Calls `/v1/balance` endpoint
    - **NameCheap**: Format validation only (API requires IP whitelist)

    **Security**:
    - Rate limited to prevent abuse
    - Test result stored in database
    - Audit log created for test
    """
    try:
        credential_manager = await get_credential_manager(request)
        user_id = admin.get("user_id") or admin.get("email")

        # Validate service
        if not validate_service(service):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported service. Supported services: {', '.join(SUPPORTED_SERVICES.keys())}"
            )

        # Determine credential type (use first supported type for service)
        service_config = SUPPORTED_SERVICES[service]
        credential_type = service_config["credential_types"][0]

        # Test credential
        result = await credential_manager.test_credential(
            user_id=user_id,
            service=service,
            credential_type=credential_type,
            value=request_body.value
        )

        return TestResultResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test credential: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test credential: {str(e)}")


@router.get("/services", response_model=List[ServiceInfo])
async def list_supported_services(
    request: Request,
    admin: dict = Depends(require_admin)
):
    """
    List all supported services and their credential types

    **Authentication**: Requires admin role

    **Returns**:
    - List of supported services with:
      - Service name and display name
      - Supported credential types
      - Whether test endpoint is available
      - Whether user has configured credentials

    **Example Response**:
    ```json
    [
      {
        "service": "cloudflare",
        "name": "Cloudflare",
        "credential_types": ["api_token"],
        "has_test": true,
        "configured": false
      },
      ...
    ]
    ```
    """
    try:
        credential_manager = await get_credential_manager(request)
        user_id = admin.get("user_id") or admin.get("email")

        # Get user's configured credentials
        user_credentials = await credential_manager.list_credentials(user_id=user_id)
        configured_services = {cred["service"] for cred in user_credentials}

        # Build service info list
        services = []
        for service, config in get_supported_services().items():
            services.append(ServiceInfo(
                service=service,
                name=config["name"],
                credential_types=config["credential_types"],
                has_test=config["test_url"] is not None,
                configured=service in configured_services
            ))

        return services

    except Exception as e:
        logger.error(f"Failed to list services: {e}")
        raise HTTPException(status_code=500, detail="Failed to list services")


# ==================== Health Check ====================

@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint for credential management API"""
    return {
        "status": "healthy",
        "service": "credential_api",
        "supported_services": list(SUPPORTED_SERVICES.keys()),
        "encryption": "fernet_aes128"
    }
