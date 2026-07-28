"""
User API Keys Router
REST API endpoints for managing user BYOK (Bring Your Own Key) API keys
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
import logging

from key_encryption import get_encryption
from authentik_keys import get_authentik_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/user/api-keys", tags=["user-api-keys"])


# Request/Response models
class SaveAPIKeyRequest(BaseModel):
    """Request to save a new API key"""
    provider: str = Field(..., description="API provider (openai, anthropic, etc.)")
    api_key: str = Field(..., description="Plain text API key to encrypt and store")
    name: Optional[str] = Field(None, description="Optional custom name for the key")


class UpdateAPIKeyRequest(BaseModel):
    """Request to update an existing API key"""
    api_key: Optional[str] = Field(None, description="New API key (leave empty to keep existing)")
    name: Optional[str] = Field(None, description="New name (leave empty to keep existing)")


class APIKeyResponse(BaseModel):
    """Response with API key information"""
    provider: str
    name: str
    masked_key: str
    created_at: str
    updated_at: str


class APIKeyListResponse(BaseModel):
    """Response with list of user's API keys"""
    keys: List[APIKeyResponse]
    count: int


class APIKeyDecryptedResponse(BaseModel):
    """Response with decrypted API key"""
    provider: str
    api_key: str
    name: str


# Helper function to get current user
async def get_current_user(request: Request) -> str:
    """Get current authenticated user from session"""
    username = request.session.get('user')
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return username


@router.post("", response_model=Dict[str, str], status_code=201)
async def save_api_key(
    key_request: SaveAPIKeyRequest,
    username: str = Depends(get_current_user)
):
    """
    Save a new encrypted API key for the current user

    - **provider**: API provider name (openai, anthropic, cohere, etc.)
    - **api_key**: Plain text API key to encrypt and store
    - **name**: Optional custom name for the key
    """
    try:
        # Encrypt the key
        encryption = get_encryption()
        encrypted_key = encryption.encrypt_key(key_request.api_key)

        # Save to Authentik
        manager = get_authentik_manager()
        success = await manager.save_user_api_key(
            username=username,
            provider=key_request.provider,
            encrypted_key=encrypted_key,
            key_name=key_request.name
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save API key")

        return {
            "status": "success",
            "message": f"API key for {key_request.provider} saved successfully",
            "provider": key_request.provider
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving API key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=APIKeyListResponse)
async def list_api_keys(username: str = Depends(get_current_user)):
    """
    List all API keys for the current user (with masked keys)

    Returns list of API keys with metadata but keys are masked for security
    """
    try:
        manager = get_authentik_manager()
        keys = await manager.get_user_api_keys(username)

        encryption = get_encryption()
        key_list = []

        for provider, key_data in keys.items():
            # Decrypt only to mask, don't return plain text
            try:
                decrypted = encryption.decrypt_key(key_data['encrypted_key'])
                masked = encryption.mask_key(decrypted)
            except Exception as e:
                logger.error(f"Error decrypting key for masking: {e}")
                masked = "****"

            key_list.append(APIKeyResponse(
                provider=provider,
                name=key_data.get('name', provider),
                masked_key=masked,
                created_at=key_data.get('created_at', ''),
                updated_at=key_data.get('updated_at', '')
            ))

        return APIKeyListResponse(
            keys=key_list,
            count=len(key_list)
        )

    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{provider}", response_model=APIKeyDecryptedResponse)
async def get_api_key(provider: str, username: str = Depends(get_current_user)):
    """
    Get a specific decrypted API key for the current user

    - **provider**: API provider name to retrieve

    Returns the decrypted API key (use with caution, this exposes the key)
    """
    try:
        manager = get_authentik_manager()
        encrypted_key = await manager.get_user_api_key(username, provider)

        if not encrypted_key:
            raise HTTPException(status_code=404, detail=f"No API key found for provider: {provider}")

        # Decrypt the key
        encryption = get_encryption()
        decrypted_key = encryption.decrypt_key(encrypted_key)

        # Get key metadata
        keys = await manager.get_user_api_keys(username)
        key_data = keys.get(provider, {})

        return APIKeyDecryptedResponse(
            provider=provider,
            api_key=decrypted_key,
            name=key_data.get('name', provider)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving API key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{provider}", response_model=Dict[str, str])
async def update_api_key(
    provider: str,
    key_request: UpdateAPIKeyRequest,
    username: str = Depends(get_current_user)
):
    """
    Update an existing API key

    - **provider**: API provider name to update
    - **api_key**: New API key (optional, leave empty to keep existing)
    - **name**: New name (optional, leave empty to keep existing)
    """
    try:
        # Encrypt new key if provided
        encrypted_key = None
        if key_request.api_key:
            encryption = get_encryption()
            encrypted_key = encryption.encrypt_key(key_request.api_key)

        # Update in Authentik
        manager = get_authentik_manager()
        success = await manager.update_user_api_key(
            username=username,
            provider=provider,
            encrypted_key=encrypted_key,
            key_name=key_request.name
        )

        if not success:
            raise HTTPException(status_code=404, detail=f"No API key found for provider: {provider}")

        return {
            "status": "success",
            "message": f"API key for {provider} updated successfully",
            "provider": provider
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating API key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{provider}", response_model=Dict[str, str])
async def delete_api_key(provider: str, username: str = Depends(get_current_user)):
    """
    Delete an API key

    - **provider**: API provider name to delete
    """
    try:
        manager = get_authentik_manager()
        success = await manager.delete_user_api_key(username, provider)

        if not success:
            raise HTTPException(status_code=404, detail=f"No API key found for provider: {provider}")

        return {
            "status": "success",
            "message": f"API key for {provider} deleted successfully",
            "provider": provider
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
