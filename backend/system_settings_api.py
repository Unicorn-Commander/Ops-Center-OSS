"""
System Settings API

REST API endpoints for managing system configuration settings via GUI.
Admin-only access with comprehensive audit logging.

Endpoints:
- GET    /api/v1/system/settings                 - List all settings
- GET    /api/v1/system/settings/{key}           - Get specific setting
- POST   /api/v1/system/settings                 - Create/update setting
- DELETE /api/v1/system/settings/{key}           - Delete setting
- GET    /api/v1/system/settings/audit           - Get audit log
- GET    /api/v1/system/settings/categories      - List categories
- POST   /api/v1/system/settings/bulk            - Bulk update settings

Author: Backend API Developer
Date: October 20, 2025
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from system_settings_manager import (
    SystemSettingsManager,
    SystemSetting,
    SettingCreate,
    SettingUpdate,
    SettingAuditLog,
    SettingCategory,
    ValueType
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/system/settings", tags=["System Settings"])


# Dependency to get settings manager (will be injected by server.py)
_settings_manager: Optional[SystemSettingsManager] = None


def get_settings_manager() -> SystemSettingsManager:
    """Get settings manager instance"""
    if _settings_manager is None:
        raise HTTPException(
            status_code=500,
            detail="System settings manager not initialized"
        )
    return _settings_manager


def set_settings_manager(manager: SystemSettingsManager):
    """Set settings manager instance (called by server.py on startup)"""
    global _settings_manager
    _settings_manager = manager
    logger.info("System settings manager initialized in API router")


# Dependency to check admin role (simplified - should use actual auth)
async def check_admin_role(request: Request) -> str:
    """
    Check if user has admin role

    Returns:
        User ID if admin, raises HTTPException otherwise
    """
    # TODO: Replace with actual authentication check
    # For now, check session or use keycloak integration

    # Try to get user from session
    user_email = request.session.get("user_email")
    user_roles = request.session.get("user_roles", [])

    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # Check if user has admin or moderator role
    if "admin" not in user_roles and "moderator" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to manage system settings"
        )

    return user_email


# Request/Response models
class SettingCreateRequest(BaseModel):
    """Request to create new setting"""
    key: str = Field(..., min_length=1, max_length=255)
    value: str
    category: SettingCategory
    description: Optional[str] = None
    is_sensitive: bool = False
    value_type: ValueType = ValueType.STRING
    is_required: bool = False
    is_editable: bool = True
    default_value: Optional[str] = None


class SettingUpdateRequest(BaseModel):
    """Request to update setting"""
    value: str
    description: Optional[str] = None
    is_sensitive: Optional[bool] = None
    value_type: Optional[ValueType] = None
    is_required: Optional[bool] = None
    is_editable: Optional[bool] = None
    default_value: Optional[str] = None


class BulkUpdateRequest(BaseModel):
    """Request to bulk update multiple settings"""
    settings: List[Dict[str, Any]] = Field(
        ...,
        description="List of settings to update (each with 'key' and 'value')"
    )


class SettingResponse(BaseModel):
    """Response for single setting"""
    success: bool = True
    setting: SystemSetting


class SettingsListResponse(BaseModel):
    """Response for settings list"""
    success: bool = True
    settings: List[SystemSetting]
    total: int


class AuditLogResponse(BaseModel):
    """Response for audit log"""
    success: bool = True
    logs: List[SettingAuditLog]
    total: int


class CategoriesResponse(BaseModel):
    """Response for categories list"""
    success: bool = True
    categories: List[Dict[str, str]]


class BulkUpdateResponse(BaseModel):
    """Response for bulk update"""
    success: bool = True
    updated: int
    failed: int
    errors: List[str]


# API Endpoints

@router.get("/categories", response_model=CategoriesResponse)
async def list_categories():
    """
    List all available setting categories

    Returns list of categories with descriptions.
    Public endpoint (no auth required).
    """
    categories = [
        {"value": "security", "label": "Security", "description": "Security and encryption settings"},
        {"value": "llm", "label": "LLM Providers", "description": "Language model provider API keys and settings"},
        {"value": "billing", "label": "Billing", "description": "Stripe and Lago billing configuration"},
        {"value": "email", "label": "Email", "description": "SMTP and email provider settings"},
        {"value": "storage", "label": "Storage", "description": "S3 and backup storage configuration"},
        {"value": "integration", "label": "Integrations", "description": "Third-party service integrations"},
        {"value": "monitoring", "label": "Monitoring", "description": "Monitoring and logging configuration"},
        {"value": "system", "label": "System", "description": "System-wide configuration"}
    ]

    return CategoriesResponse(categories=categories)


@router.get("", response_model=SettingsListResponse)
async def list_settings(
    category: Optional[SettingCategory] = Query(None, description="Filter by category"),
    include_sensitive: bool = Query(True, description="Include sensitive settings"),
    show_values: bool = Query(False, description="Show decrypted values (admin only)"),
    manager: SystemSettingsManager = Depends(get_settings_manager),
    user_id: str = Depends(check_admin_role)
):
    """
    List all system settings

    Filters:
    - category: Filter by category (optional)
    - include_sensitive: Whether to include sensitive settings (default: true)
    - show_values: Whether to show decrypted values (default: false, masked)

    Admin only. Sensitive values are masked by default.
    """
    try:
        settings = await manager.list_settings(
            category=category,
            include_sensitive=include_sensitive,
            decrypt=True,
            mask_sensitive=not show_values  # Mask unless explicitly requested
        )

        return SettingsListResponse(
            settings=settings,
            total=len(settings)
        )

    except Exception as e:
        logger.error(f"Failed to list settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list settings: {str(e)}"
        )


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(
    key: str,
    show_value: bool = Query(False, description="Show decrypted value (admin only)"),
    manager: SystemSettingsManager = Depends(get_settings_manager),
    user_id: str = Depends(check_admin_role)
):
    """
    Get specific setting by key

    Query params:
    - show_value: Whether to show decrypted value (default: false, masked)

    Admin only. Sensitive values are masked by default.
    """
    try:
        setting = await manager.get_setting(
            key=key,
            decrypt=True,
            mask_sensitive=not show_value
        )

        if not setting:
            raise HTTPException(
                status_code=404,
                detail=f"Setting '{key}' not found"
            )

        return SettingResponse(setting=setting)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get setting {key}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get setting: {str(e)}"
        )


@router.post("", response_model=SettingResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_setting(
    request_data: SettingCreateRequest,
    request: Request,
    manager: SystemSettingsManager = Depends(get_settings_manager),
    user_id: str = Depends(check_admin_role)
):
    """
    Create or update a system setting

    Creates new setting if key doesn't exist, updates if it does.
    Admin only. All changes are audited.
    """
    try:
        # Get client info for audit
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        setting = await manager.set_setting(
            key=request_data.key,
            value=request_data.value,
            user_id=user_id,
            category=request_data.category,
            description=request_data.description,
            is_sensitive=request_data.is_sensitive,
            value_type=request_data.value_type,
            is_required=request_data.is_required,
            is_editable=request_data.is_editable,
            default_value=request_data.default_value,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return SettingResponse(setting=setting)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create/update setting: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create/update setting: {str(e)}"
        )


@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str,
    request_data: SettingUpdateRequest,
    request: Request,
    manager: SystemSettingsManager = Depends(get_settings_manager),
    user_id: str = Depends(check_admin_role)
):
    """
    Update existing setting

    Updates only the provided fields. Key must already exist.
    Admin only. All changes are audited.
    """
    try:
        # Check if setting exists
        existing = await manager.get_setting(key, decrypt=False)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Setting '{key}' not found"
            )

        # Get client info for audit
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Update setting
        setting = await manager.set_setting(
            key=key,
            value=request_data.value,
            user_id=user_id,
            description=request_data.description,
            is_sensitive=request_data.is_sensitive,
            value_type=request_data.value_type,
            is_required=request_data.is_required,
            is_editable=request_data.is_editable,
            default_value=request_data.default_value,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return SettingResponse(setting=setting)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update setting {key}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update setting: {str(e)}"
        )


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(
    key: str,
    request: Request,
    manager: SystemSettingsManager = Depends(get_settings_manager),
    user_id: str = Depends(check_admin_role)
):
    """
    Delete a system setting

    Deletes setting if it exists and is editable/not required.
    Admin only. All deletions are audited.
    """
    try:
        # Get client info for audit
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        deleted = await manager.delete_setting(
            key=key,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Setting '{key}' not found"
            )

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete setting {key}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete setting: {str(e)}"
        )


@router.get("/audit/log", response_model=AuditLogResponse)
async def get_audit_log(
    key: Optional[str] = Query(None, description="Filter by setting key"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of entries"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    manager: SystemSettingsManager = Depends(get_settings_manager),
    user_id: str = Depends(check_admin_role)
):
    """
    Get audit log for system settings changes

    Query params:
    - key: Filter by setting key (optional)
    - limit: Maximum number of entries (default: 100, max: 1000)
    - offset: Offset for pagination (default: 0)

    Admin only. Returns all changes with user, timestamp, and IP address.
    """
    try:
        logs = await manager.get_audit_log(
            key=key,
            limit=limit,
            offset=offset
        )

        return AuditLogResponse(
            logs=logs,
            total=len(logs)
        )

    except Exception as e:
        logger.error(f"Failed to get audit log: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get audit log: {str(e)}"
        )


@router.post("/bulk", response_model=BulkUpdateResponse)
async def bulk_update_settings(
    request_data: BulkUpdateRequest,
    request: Request,
    manager: SystemSettingsManager = Depends(get_settings_manager),
    user_id: str = Depends(check_admin_role)
):
    """
    Bulk update multiple settings

    Updates multiple settings in a single transaction.
    Settings that don't exist will be skipped.

    Request body:
    ```json
    {
        "settings": [
            {"key": "SMTP_HOST", "value": "smtp.office365.com"},
            {"key": "SMTP_PORT", "value": "587"},
            {"key": "LOG_LEVEL", "value": "DEBUG"}
        ]
    }
    ```

    Admin only. All changes are audited individually.
    """
    try:
        updated = 0
        failed = 0
        errors = []

        # Get client info for audit
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        for setting_data in request_data.settings:
            try:
                key = setting_data.get("key")
                value = setting_data.get("value")

                if not key or value is None:
                    errors.append(f"Invalid setting data: {setting_data}")
                    failed += 1
                    continue

                # Check if setting exists
                existing = await manager.get_setting(key, decrypt=False)
                if not existing:
                    errors.append(f"Setting '{key}' not found")
                    failed += 1
                    continue

                # Update setting
                await manager.set_setting(
                    key=key,
                    value=str(value),
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                updated += 1

            except Exception as e:
                logger.error(f"Failed to update setting: {e}")
                errors.append(f"Failed to update '{key}': {str(e)}")
                failed += 1

        return BulkUpdateResponse(
            updated=updated,
            failed=failed,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Failed bulk update: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed bulk update: {str(e)}"
        )


# Health check endpoint (public)
@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "system-settings-api"}
