"""
LLM Provider Management API

CRUD endpoints for managing LLM providers (OpenAI, Anthropic, Google, etc.)

Endpoints:
- GET    /api/v1/admin/llm/providers          - List all providers
- GET    /api/v1/admin/llm/providers/{id}     - Get provider details
- POST   /api/v1/admin/llm/providers          - Create provider (admin only)
- PUT    /api/v1/admin/llm/providers/{id}     - Update provider (admin only)
- DELETE /api/v1/admin/llm/providers/{id}     - Delete provider (admin only)
- GET    /api/v1/admin/llm/providers/{id}/health - Check provider health
- POST   /api/v1/admin/llm/providers/{id}/test   - Test provider connection

Author: Backend API Developer
Epic: 3.1 - LiteLLM Multi-Provider Routing
Date: October 23, 2025
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from models.llm_models import LLMProvider
from keycloak_integration import get_user_tier_info
from audit_logger import log_audit_event
import httpx

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/v1/admin/llm/providers", tags=["LLM Providers"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ProviderCreate(BaseModel):
    """Request model for creating provider"""
    provider_name: str = Field(..., min_length=1, max_length=100)
    provider_slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    base_url: Optional[str] = Field(None, max_length=500)
    auth_type: str = Field('api_key', max_length=50)
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    rate_limit_rpm: Optional[int] = Field(None, ge=0)
    rate_limit_tpm: Optional[int] = Field(None, ge=0)
    rate_limit_rpd: Optional[int] = Field(None, ge=0)
    is_active: bool = True
    is_byok_supported: bool = True
    is_system_provider: bool = False
    api_key_format: Optional[str] = Field(None, max_length=100)
    documentation_url: Optional[str] = Field(None, max_length=500)
    pricing_url: Optional[str] = Field(None, max_length=500)
    status_page_url: Optional[str] = Field(None, max_length=500)
    min_tier_required: str = Field('free', max_length=50)

    @validator('auth_type')
    def validate_auth_type(cls, v):
        """Validate auth type"""
        valid_types = ['api_key', 'oauth2', 'bearer', 'none']
        if v not in valid_types:
            raise ValueError(f"auth_type must be one of {valid_types}")
        return v

    @validator('min_tier_required')
    def validate_tier(cls, v):
        """Validate tier"""
        valid_tiers = ['free', 'starter', 'professional', 'enterprise']
        if v not in valid_tiers:
            raise ValueError(f"min_tier_required must be one of {valid_tiers}")
        return v


class ProviderUpdate(BaseModel):
    """Request model for updating provider"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    base_url: Optional[str] = Field(None, max_length=500)
    auth_type: Optional[str] = Field(None, max_length=50)
    supports_streaming: Optional[bool] = None
    supports_function_calling: Optional[bool] = None
    supports_vision: Optional[bool] = None
    rate_limit_rpm: Optional[int] = Field(None, ge=0)
    rate_limit_tpm: Optional[int] = Field(None, ge=0)
    rate_limit_rpd: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    is_byok_supported: Optional[bool] = None
    api_key_format: Optional[str] = Field(None, max_length=100)
    documentation_url: Optional[str] = Field(None, max_length=500)
    pricing_url: Optional[str] = Field(None, max_length=500)
    status_page_url: Optional[str] = Field(None, max_length=500)
    min_tier_required: Optional[str] = Field(None, max_length=50)


class ProviderResponse(BaseModel):
    """Response model for provider"""
    id: int
    provider_name: str
    provider_slug: str
    display_name: str
    description: Optional[str]
    base_url: Optional[str]
    auth_type: str
    supports_streaming: bool
    supports_function_calling: bool
    supports_vision: bool
    rate_limit_rpm: Optional[int]
    rate_limit_tpm: Optional[int]
    rate_limit_rpd: Optional[int]
    is_active: bool
    is_byok_supported: bool
    is_system_provider: bool
    api_key_format: Optional[str]
    documentation_url: Optional[str]
    pricing_url: Optional[str]
    status_page_url: Optional[str]
    health_status: str
    health_last_checked: Optional[str]
    health_response_time_ms: Optional[int]
    min_tier_required: str
    model_count: int = 0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ProviderHealthResponse(BaseModel):
    """Response model for provider health check"""
    provider_id: int
    provider_name: str
    health_status: str
    response_time_ms: int
    tested_at: str
    error_message: Optional[str] = None


# ============================================================================
# Dependency Injection
# ============================================================================

def get_db():
    """Get database session (implement based on your DB setup)"""
    # TODO: Import and return your database session
    # Example:
    # from database import SessionLocal
    # db = SessionLocal()
    # try:
    #     yield db
    # finally:
    #     db.close()
    raise NotImplementedError("Database session dependency not implemented")


async def require_admin(user_email: str = Depends(lambda: "admin@example.com")):
    """Require admin role for endpoint"""
    # TODO: Implement actual authentication check
    # This is a placeholder - integrate with keycloak_integration.py
    return user_email


# ============================================================================
# Provider CRUD Endpoints
# ============================================================================

@router.get("", response_model=List[ProviderResponse])
async def list_providers(
    active_only: bool = Query(False, description="Filter active providers only"),
    byok_supported: bool = Query(False, description="Filter BYOK-supported providers"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db),
    user: str = Depends(require_admin)
):
    """
    List all LLM providers

    Returns list of providers with model counts.
    """
    try:
        # Build query
        query = db.query(
            LLMProvider,
            func.count(LLMProvider.models).label('model_count')
        ).outerjoin(LLMProvider.models)

        # Apply filters
        if active_only:
            query = query.filter(LLMProvider.is_active == True)

        if byok_supported:
            query = query.filter(LLMProvider.is_byok_supported == True)

        if search:
            query = query.filter(
                or_(
                    LLMProvider.provider_name.ilike(f'%{search}%'),
                    LLMProvider.display_name.ilike(f'%{search}%')
                )
            )

        # Group by provider and execute
        providers = query.group_by(LLMProvider.id).all()

        # Build response
        result = []
        for provider, model_count in providers:
            provider_dict = provider.to_dict()
            provider_dict['model_count'] = model_count
            result.append(ProviderResponse(**provider_dict))

        logger.info(f"Listed {len(result)} providers")
        return result

    except Exception as e:
        logger.error(f"Error listing providers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(require_admin)
):
    """
    Get provider by ID

    Returns provider details with model count.
    """
    try:
        provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()

        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

        # Count models
        model_count = len(provider.models)

        # Build response
        provider_dict = provider.to_dict()
        provider_dict['model_count'] = model_count

        return ProviderResponse(**provider_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider {provider_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=ProviderResponse, status_code=201)
async def create_provider(
    provider: ProviderCreate,
    db: Session = Depends(get_db),
    user: str = Depends(require_admin)
):
    """
    Create new LLM provider

    Admin only. Creates provider with initial status.
    """
    try:
        # Check if provider name already exists
        existing = db.query(LLMProvider).filter(
            or_(
                LLMProvider.provider_name == provider.provider_name,
                LLMProvider.provider_slug == provider.provider_slug
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Provider with name '{provider.provider_name}' or slug '{provider.provider_slug}' already exists"
            )

        # Create provider
        new_provider = LLMProvider(
            **provider.dict(),
            health_status='unknown',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_provider)
        db.commit()
        db.refresh(new_provider)

        # Audit log
        await log_audit_event(
            action='llm.provider.create',
            user_id=user,
            resource_type='llm_provider',
            resource_id=str(new_provider.id),
            result='success',
            metadata={'provider_name': provider.provider_name}
        )

        logger.info(f"Created provider: {provider.provider_name} (ID: {new_provider.id})")

        # Build response
        provider_dict = new_provider.to_dict()
        provider_dict['model_count'] = 0

        return ProviderResponse(**provider_dict)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating provider: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: int,
    updates: ProviderUpdate,
    db: Session = Depends(get_db),
    user: str = Depends(require_admin)
):
    """
    Update LLM provider

    Admin only. Updates provider configuration.
    """
    try:
        provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()

        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

        # Update fields
        update_data = updates.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(provider, field, value)

        provider.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(provider)

        # Audit log
        await log_audit_event(
            action='llm.provider.update',
            user_id=user,
            resource_type='llm_provider',
            resource_id=str(provider_id),
            result='success',
            metadata={'updates': update_data}
        )

        logger.info(f"Updated provider: {provider.provider_name} (ID: {provider_id})")

        # Build response
        provider_dict = provider.to_dict()
        provider_dict['model_count'] = len(provider.models)

        return ProviderResponse(**provider_dict)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating provider {provider_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{provider_id}", status_code=204)
async def delete_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(require_admin)
):
    """
    Delete LLM provider

    Admin only. Deletes provider and all associated models.
    System providers cannot be deleted.
    """
    try:
        provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()

        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

        if provider.is_system_provider:
            raise HTTPException(
                status_code=403,
                detail="Cannot delete system provider"
            )

        provider_name = provider.provider_name

        # Delete provider (cascade deletes models and routing rules)
        db.delete(provider)
        db.commit()

        # Audit log
        await log_audit_event(
            action='llm.provider.delete',
            user_id=user,
            resource_type='llm_provider',
            resource_id=str(provider_id),
            result='success',
            metadata={'provider_name': provider_name}
        )

        logger.info(f"Deleted provider: {provider_name} (ID: {provider_id})")

        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting provider {provider_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Provider Health & Testing
# ============================================================================

@router.get("/{provider_id}/health", response_model=ProviderHealthResponse)
async def check_provider_health(
    provider_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(require_admin)
):
    """
    Check provider health status

    Tests provider API endpoint and updates health status.
    """
    try:
        provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()

        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

        # Test provider endpoint
        health_status = 'unknown'
        response_time_ms = 0
        error_message = None

        if provider.base_url:
            try:
                start_time = datetime.utcnow()

                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Simple GET request to base URL
                    response = await client.get(provider.base_url)

                end_time = datetime.utcnow()
                response_time_ms = int((end_time - start_time).total_seconds() * 1000)

                if response.status_code < 500:
                    health_status = 'healthy'
                else:
                    health_status = 'degraded'

            except Exception as e:
                health_status = 'down'
                error_message = str(e)
                logger.error(f"Provider {provider.provider_name} health check failed: {e}")

        # Update provider health
        provider.health_status = health_status
        provider.health_last_checked = datetime.utcnow()
        provider.health_response_time_ms = response_time_ms if response_time_ms > 0 else None

        db.commit()

        return ProviderHealthResponse(
            provider_id=provider.id,
            provider_name=provider.provider_name,
            health_status=health_status,
            response_time_ms=response_time_ms,
            tested_at=datetime.utcnow().isoformat(),
            error_message=error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking provider health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{provider_id}/test")
async def test_provider_connection(
    provider_id: int,
    api_key: str = Query(..., description="API key to test"),
    db: Session = Depends(get_db),
    user: str = Depends(require_admin)
):
    """
    Test provider API connection with API key

    Admin only. Tests if provided API key works with provider.
    Does NOT store the key.
    """
    try:
        provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()

        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

        if not provider.base_url:
            raise HTTPException(
                status_code=400,
                detail=f"Provider {provider.provider_name} has no base_url configured"
            )

        # Test API key with simple request
        # NOTE: This is provider-specific logic - you'll need to customize per provider
        test_result = {
            'provider_id': provider.id,
            'provider_name': provider.provider_name,
            'test_passed': False,
            'error_message': None,
            'tested_at': datetime.utcnow().isoformat()
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {}

                # Add auth header based on auth type
                if provider.auth_type == 'bearer' or provider.auth_type == 'api_key':
                    headers['Authorization'] = f'Bearer {api_key}'

                # Make test request (adjust endpoint per provider)
                response = await client.get(
                    f"{provider.base_url}/models",  # Common endpoint
                    headers=headers
                )

                if response.status_code == 200:
                    test_result['test_passed'] = True
                else:
                    test_result['error_message'] = f"HTTP {response.status_code}: {response.text[:200]}"

        except Exception as e:
            test_result['error_message'] = str(e)

        # Audit log
        await log_audit_event(
            action='llm.provider.test',
            user_id=user,
            resource_type='llm_provider',
            resource_id=str(provider_id),
            result='success' if test_result['test_passed'] else 'failure',
            metadata={'provider_name': provider.provider_name}
        )

        return test_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing provider connection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
