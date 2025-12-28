"""
Landing Page Settings API - Configure landing page behavior and branding

This module provides endpoints for:
- Public landing page configuration (no auth)
- Admin landing page management (auth required)
- Branding and customization settings
- Landing page mode selection (direct_sso, public_marketplace, custom)

Used by:
- RootRedirect component (frontend)
- Landing page components
- Admin settings pages

Author: Claude Code
Date: November 29, 2025
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, validator
import asyncpg

from dependencies import get_db_pool, require_admin, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Landing Page Settings"])


# ============================================================================
# Pydantic Models
# ============================================================================

class BrandingSettings(BaseModel):
    """Branding configuration"""
    company_name: str = Field("Unicorn Commander", max_length=100)
    logo_url: str = Field("/logos/magic_unicorn_logo.webp", max_length=500)
    favicon_url: Optional[str] = Field("/favicon.ico", max_length=500)
    primary_color: str = Field("#7c3aed", pattern=r'^#[0-9a-fA-F]{6}$')
    secondary_color: Optional[str] = Field(None, pattern=r'^#[0-9a-fA-F]{6}$')
    font_family: Optional[str] = Field(None, max_length=100)


class LandingPageSettings(BaseModel):
    """Public landing page settings"""
    landing_page_mode: str = Field(
        "direct_sso",
        pattern=r'^(direct_sso|public_marketplace|custom)$'
    )
    branding: BrandingSettings
    sso_enabled: bool = True
    allow_registration: bool = False
    show_pricing: bool = True
    show_features: bool = True
    custom_css_url: Optional[str] = None
    custom_js_url: Optional[str] = None
    announcement_banner: Optional[Dict[str, Any]] = None


class LandingPageSettingsAdmin(LandingPageSettings):
    """Admin landing page settings with additional fields"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


class LandingPageSettingsUpdate(BaseModel):
    """Admin update payload"""
    landing_page_mode: Optional[str] = Field(
        None,
        pattern=r'^(direct_sso|public_marketplace|custom)$'
    )
    branding: Optional[BrandingSettings] = None
    sso_enabled: Optional[bool] = None
    allow_registration: Optional[bool] = None
    show_pricing: Optional[bool] = None
    show_features: Optional[bool] = None
    custom_css_url: Optional[str] = None
    custom_js_url: Optional[str] = None
    announcement_banner: Optional[Dict[str, Any]] = None


# ============================================================================
# Public Endpoint (No Authentication)
# ============================================================================

@router.get("/api/v1/system/settings", response_model=LandingPageSettings)
async def get_public_landing_settings(request: Request):
    """
    Get public landing page settings

    This endpoint is PUBLIC - no authentication required.
    Used by RootRedirect to determine landing page behavior.

    Returns:
        Landing page configuration
    """
    try:
        db_pool = await get_db_pool(request)

        async with db_pool.acquire() as conn:
            settings_row = await conn.fetchrow("""
                SELECT
                    landing_page_mode,
                    branding,
                    sso_enabled,
                    allow_registration,
                    show_pricing,
                    show_features,
                    custom_css_url,
                    custom_js_url,
                    announcement_banner
                FROM landing_page_settings
                WHERE is_active = true
                LIMIT 1
            """)

            if settings_row:
                settings_dict = dict(settings_row)

                # Parse branding JSON
                if isinstance(settings_dict.get('branding'), dict):
                    settings_dict['branding'] = BrandingSettings(**settings_dict['branding'])
                else:
                    settings_dict['branding'] = BrandingSettings()

                return LandingPageSettings(**settings_dict)
            else:
                # Return defaults if no settings in database
                return get_default_landing_settings()

    except asyncpg.PostgresError as e:
        logger.error(f"Database error retrieving landing settings: {e}")
        return get_default_landing_settings()
    except Exception as e:
        logger.error(f"Error retrieving landing settings: {e}")
        return get_default_landing_settings()


# ============================================================================
# Admin Endpoints (Authentication Required)
# ============================================================================

@router.get(
    "/api/v1/admin/settings/landing",
    response_model=LandingPageSettingsAdmin,
    dependencies=[Depends(require_admin)]
)
async def get_admin_landing_settings(request: Request):
    """
    Get landing page settings (admin)

    Requires: admin role

    Returns:
        Complete landing page configuration with metadata
    """
    try:
        db_pool = await get_db_pool(request)

        async with db_pool.acquire() as conn:
            settings_row = await conn.fetchrow("""
                SELECT
                    landing_page_mode,
                    branding,
                    sso_enabled,
                    allow_registration,
                    show_pricing,
                    show_features,
                    custom_css_url,
                    custom_js_url,
                    announcement_banner,
                    created_at,
                    updated_at,
                    updated_by
                FROM landing_page_settings
                WHERE is_active = true
                LIMIT 1
            """)

            if settings_row:
                settings_dict = dict(settings_row)

                # Parse branding JSON
                if isinstance(settings_dict.get('branding'), dict):
                    settings_dict['branding'] = BrandingSettings(**settings_dict['branding'])
                else:
                    settings_dict['branding'] = BrandingSettings()

                return LandingPageSettingsAdmin(**settings_dict)
            else:
                # Return defaults
                default_settings = get_default_landing_settings()
                return LandingPageSettingsAdmin(
                    **default_settings.dict(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

    except Exception as e:
        logger.error(f"Error retrieving admin landing settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve landing settings")


@router.put(
    "/api/v1/admin/settings/landing",
    response_model=LandingPageSettingsAdmin,
    dependencies=[Depends(require_admin)]
)
async def update_landing_settings(
    request: Request,
    settings: LandingPageSettingsUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Update landing page settings (admin)

    Requires: admin role

    Args:
        settings: Settings to update (partial)

    Returns:
        Updated landing page configuration
    """
    try:
        db_pool = await get_db_pool(request)
        user_id = current_user.get('user_id', 'unknown')

        async with db_pool.acquire() as conn:
            # Get current settings
            current_row = await conn.fetchrow("""
                SELECT * FROM landing_page_settings
                WHERE is_active = true
                LIMIT 1
            """)

            if current_row:
                # Update existing settings
                update_fields = []
                update_values = []
                param_counter = 1

                for field, value in settings.dict(exclude_unset=True).items():
                    if value is not None:
                        if field == 'branding':
                            # Convert Pydantic model to dict for JSON storage
                            update_fields.append(f"{field} = ${param_counter}")
                            update_values.append(value.dict())
                        else:
                            update_fields.append(f"{field} = ${param_counter}")
                            update_values.append(value)
                        param_counter += 1

                if update_fields:
                    update_values.append(user_id)
                    update_values.append(current_row['id'])

                    query = f"""
                        UPDATE landing_page_settings
                        SET {', '.join(update_fields)},
                            updated_at = NOW(),
                            updated_by = ${param_counter}
                        WHERE id = ${param_counter + 1}
                        RETURNING *
                    """

                    updated_row = await conn.fetchrow(query, *update_values)
                else:
                    updated_row = current_row
            else:
                # Insert new settings
                settings_dict = settings.dict(exclude_unset=True)

                # Set defaults for required fields
                if 'landing_page_mode' not in settings_dict:
                    settings_dict['landing_page_mode'] = 'direct_sso'
                if 'branding' not in settings_dict:
                    settings_dict['branding'] = BrandingSettings().dict()
                elif isinstance(settings_dict['branding'], BrandingSettings):
                    settings_dict['branding'] = settings_dict['branding'].dict()

                updated_row = await conn.fetchrow("""
                    INSERT INTO landing_page_settings (
                        landing_page_mode,
                        branding,
                        sso_enabled,
                        allow_registration,
                        show_pricing,
                        show_features,
                        custom_css_url,
                        custom_js_url,
                        announcement_banner,
                        is_active,
                        created_by,
                        updated_by
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, true, $10, $10)
                    RETURNING *
                """,
                    settings_dict.get('landing_page_mode', 'direct_sso'),
                    settings_dict.get('branding'),
                    settings_dict.get('sso_enabled', True),
                    settings_dict.get('allow_registration', False),
                    settings_dict.get('show_pricing', True),
                    settings_dict.get('show_features', True),
                    settings_dict.get('custom_css_url'),
                    settings_dict.get('custom_js_url'),
                    settings_dict.get('announcement_banner'),
                    user_id
                )

            # Parse response
            result_dict = dict(updated_row)
            if isinstance(result_dict.get('branding'), dict):
                result_dict['branding'] = BrandingSettings(**result_dict['branding'])
            else:
                result_dict['branding'] = BrandingSettings()

            logger.info(f"Landing settings updated by user {user_id}")
            return LandingPageSettingsAdmin(**result_dict)

    except asyncpg.PostgresError as e:
        logger.error(f"Database error updating landing settings: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating landing settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update landing settings")


@router.post(
    "/api/v1/admin/settings/landing/reset",
    response_model=LandingPageSettingsAdmin,
    dependencies=[Depends(require_admin)]
)
async def reset_landing_settings(
    request: Request,
    current_user: Dict = Depends(get_current_user)
):
    """
    Reset landing page settings to defaults (admin)

    Requires: admin role

    Returns:
        Default landing page configuration
    """
    try:
        db_pool = await get_db_pool(request)
        user_id = current_user.get('user_id', 'unknown')

        async with db_pool.acquire() as conn:
            # Deactivate current settings
            await conn.execute("""
                UPDATE landing_page_settings
                SET is_active = false
                WHERE is_active = true
            """)

            # Insert defaults
            defaults = get_default_landing_settings()

            new_row = await conn.fetchrow("""
                INSERT INTO landing_page_settings (
                    landing_page_mode,
                    branding,
                    sso_enabled,
                    allow_registration,
                    show_pricing,
                    show_features,
                    is_active,
                    created_by,
                    updated_by
                ) VALUES ($1, $2, $3, $4, $5, $6, true, $7, $7)
                RETURNING *
            """,
                defaults.landing_page_mode,
                defaults.branding.dict(),
                defaults.sso_enabled,
                defaults.allow_registration,
                defaults.show_pricing,
                defaults.show_features,
                user_id
            )

            result_dict = dict(new_row)
            result_dict['branding'] = BrandingSettings(**result_dict['branding'])

            logger.info(f"Landing settings reset to defaults by user {user_id}")
            return LandingPageSettingsAdmin(**result_dict)

    except Exception as e:
        logger.error(f"Error resetting landing settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset landing settings")


# ============================================================================
# Helper Functions
# ============================================================================

def get_default_landing_settings() -> LandingPageSettings:
    """Get default landing page settings"""
    return LandingPageSettings(
        landing_page_mode="direct_sso",
        branding=BrandingSettings(
            company_name="Unicorn Commander",
            logo_url="/logos/magic_unicorn_logo.webp",
            favicon_url="/favicon.ico",
            primary_color="#7c3aed"
        ),
        sso_enabled=True,
        allow_registration=False,
        show_pricing=True,
        show_features=True
    )


logger.info("Landing Page Settings API initialized")
