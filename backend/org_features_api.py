"""
Organization Features Admin API
===============================

Admin endpoints for managing organization-level feature grants.
Allows granting/revoking features to specific organizations independent of their subscription tier.

Endpoints:
- GET  /api/v1/admin/orgs/{org_id}/features - List all features granted to an org
- POST /api/v1/admin/orgs/{org_id}/features - Grant a feature to an org
- DELETE /api/v1/admin/orgs/{org_id}/features/{feature_key} - Revoke a feature
- GET  /api/v1/admin/features/available - List all available features that can be granted

Author: Ops-Center Team
Created: 2026-01-31
"""

import os
import sys
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

# Add parent directory to path
if '/app' not in sys.path:
    sys.path.insert(0, '/app')

from database.connection import get_db_pool
from auth_dependencies import require_admin_user

logger = logging.getLogger(__name__)

# Router configuration
router = APIRouter(prefix="/api/v1/admin", tags=["org-features"])


# =============================================================================
# Pydantic Models
# =============================================================================

class OrgFeatureGrant(BaseModel):
    """Request model for granting a feature to an organization"""
    feature_key: str
    notes: Optional[str] = None


class OrgFeatureResponse(BaseModel):
    """Response model for an organization feature grant"""
    id: str
    org_id: str
    feature_key: str
    enabled: bool
    granted_by: Optional[str]
    granted_at: Optional[datetime]
    notes: Optional[str]
    app_name: Optional[str] = None  # From add_ons table


class AvailableFeatureResponse(BaseModel):
    """Response model for an available feature"""
    feature_key: str
    app_name: str
    description: Optional[str]


class GrantSuccessResponse(BaseModel):
    """Response model for successful grant"""
    success: bool
    message: str
    grant: OrgFeatureResponse


class RevokeSuccessResponse(BaseModel):
    """Response model for successful revoke"""
    success: bool
    message: str


# =============================================================================
# Helper Functions
# =============================================================================

async def verify_org_exists(pool, org_id: str) -> bool:
    """Check if organization exists in database"""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM organizations WHERE id = $1)",
            org_id
        )
        return result


async def verify_feature_key_exists(pool, feature_key: str) -> bool:
    """Check if feature_key exists in add_ons table"""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM add_ons WHERE feature_key = $1)",
            feature_key
        )
        return result


async def get_app_name_for_feature(pool, feature_key: str) -> Optional[str]:
    """Get the app name for a feature key from add_ons table"""
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT name FROM add_ons WHERE feature_key = $1",
            feature_key
        )
        return result


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/orgs/{org_id}/features", response_model=List[OrgFeatureResponse])
async def list_org_features(
    org_id: str,
    admin_user: dict = Depends(require_admin_user)
):
    """
    List all features granted to an organization.

    Returns list of features with:
    - feature_key: The feature identifier
    - enabled: Whether the grant is currently active
    - granted_by: Admin who granted the feature
    - granted_at: When the feature was granted
    - notes: Optional explanation
    - app_name: Name of the app (from add_ons table)

    Example:
        GET /api/v1/admin/orgs/123e4567-e89b-12d3-a456-426614174000/features
        Response: [
            {
                "id": "abc...",
                "org_id": "123...",
                "feature_key": "forgejo",
                "enabled": true,
                "granted_by": "admin@example.com",
                "granted_at": "2026-01-31T10:00:00Z",
                "notes": "Partner deal",
                "app_name": "Forgejo Git Server"
            }
        ]
    """
    pool = await get_db_pool()

    # Verify org exists
    if not await verify_org_exists(pool, org_id):
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")

    async with pool.acquire() as conn:
        # Query org_features with LEFT JOIN to add_ons for app names
        rows = await conn.fetch(
            """
            SELECT
                of.id,
                of.org_id,
                of.feature_key,
                of.enabled,
                of.granted_by,
                of.granted_at,
                of.notes,
                ao.name as app_name
            FROM org_features of
            LEFT JOIN add_ons ao ON of.feature_key = ao.feature_key
            WHERE of.org_id = $1
            ORDER BY of.granted_at DESC
            """,
            org_id
        )

        features = []
        for row in rows:
            features.append(OrgFeatureResponse(
                id=str(row['id']),
                org_id=str(row['org_id']),
                feature_key=row['feature_key'],
                enabled=row['enabled'],
                granted_by=row['granted_by'],
                granted_at=row['granted_at'],
                notes=row['notes'],
                app_name=row['app_name']
            ))

        logger.info(f"Admin {admin_user.get('email')} listed {len(features)} features for org {org_id}")
        return features


@router.post("/orgs/{org_id}/features", response_model=GrantSuccessResponse)
async def grant_org_feature(
    org_id: str,
    grant_data: OrgFeatureGrant,
    admin_user: dict = Depends(require_admin_user)
):
    """
    Grant a feature to an organization.

    The feature_key must exist in the add_ons table.

    Args:
        org_id: Organization UUID
        grant_data: Feature key and optional notes

    Returns:
        Success response with the created grant

    Example:
        POST /api/v1/admin/orgs/123e4567-e89b-12d3-a456-426614174000/features
        Body: {"feature_key": "forgejo", "notes": "Partner deal Q1 2026"}
        Response: {
            "success": true,
            "message": "Feature 'forgejo' granted to organization",
            "grant": {...}
        }
    """
    pool = await get_db_pool()

    # Verify org exists
    if not await verify_org_exists(pool, org_id):
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")

    # Verify feature_key exists in add_ons
    if not await verify_feature_key_exists(pool, grant_data.feature_key):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid feature_key: '{grant_data.feature_key}'. Feature must exist in add_ons table."
        )

    # Get admin email for audit
    admin_email = admin_user.get('email') or admin_user.get('user_id') or 'unknown'

    async with pool.acquire() as conn:
        try:
            # Insert or update the feature grant (upsert)
            row = await conn.fetchrow(
                """
                INSERT INTO org_features (org_id, feature_key, enabled, granted_by, notes)
                VALUES ($1, $2, TRUE, $3, $4)
                ON CONFLICT (org_id, feature_key)
                DO UPDATE SET
                    enabled = TRUE,
                    granted_by = EXCLUDED.granted_by,
                    granted_at = CURRENT_TIMESTAMP,
                    notes = EXCLUDED.notes
                RETURNING id, org_id, feature_key, enabled, granted_by, granted_at, notes
                """,
                org_id,
                grant_data.feature_key,
                admin_email,
                grant_data.notes
            )

            # Get app name
            app_name = await get_app_name_for_feature(pool, grant_data.feature_key)

            grant = OrgFeatureResponse(
                id=str(row['id']),
                org_id=str(row['org_id']),
                feature_key=row['feature_key'],
                enabled=row['enabled'],
                granted_by=row['granted_by'],
                granted_at=row['granted_at'],
                notes=row['notes'],
                app_name=app_name
            )

            logger.info(
                f"Admin {admin_email} granted feature '{grant_data.feature_key}' to org {org_id}"
            )

            return GrantSuccessResponse(
                success=True,
                message=f"Feature '{grant_data.feature_key}' granted to organization",
                grant=grant
            )

        except Exception as e:
            logger.error(f"Error granting feature to org {org_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to grant feature: {str(e)}")


@router.delete("/orgs/{org_id}/features/{feature_key}", response_model=RevokeSuccessResponse)
async def revoke_org_feature(
    org_id: str,
    feature_key: str,
    admin_user: dict = Depends(require_admin_user)
):
    """
    Revoke a feature from an organization.

    This permanently removes the feature grant. To temporarily disable,
    consider updating the 'enabled' field instead (not implemented in this version).

    Args:
        org_id: Organization UUID
        feature_key: The feature key to revoke

    Returns:
        Success message

    Example:
        DELETE /api/v1/admin/orgs/123e4567-e89b-12d3-a456-426614174000/features/forgejo
        Response: {
            "success": true,
            "message": "Feature 'forgejo' revoked from organization"
        }
    """
    pool = await get_db_pool()

    # Verify org exists
    if not await verify_org_exists(pool, org_id):
        raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")

    admin_email = admin_user.get('email') or admin_user.get('user_id') or 'unknown'

    async with pool.acquire() as conn:
        # Delete the feature grant
        result = await conn.execute(
            """
            DELETE FROM org_features
            WHERE org_id = $1 AND feature_key = $2
            """,
            org_id,
            feature_key
        )

        # Check if anything was deleted
        rows_affected = int(result.split()[-1])

        if rows_affected == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Feature grant not found: org_id={org_id}, feature_key={feature_key}"
            )

        logger.info(
            f"Admin {admin_email} revoked feature '{feature_key}' from org {org_id}"
        )

        return RevokeSuccessResponse(
            success=True,
            message=f"Feature '{feature_key}' revoked from organization"
        )


@router.get("/features/available", response_model=List[AvailableFeatureResponse])
async def list_available_features(
    admin_user: dict = Depends(require_admin_user)
):
    """
    List all available features that can be granted to organizations.

    Returns all features from the add_ons table with their feature_key,
    app name, and description.

    Example:
        GET /api/v1/admin/features/available
        Response: [
            {
                "feature_key": "forgejo",
                "app_name": "Forgejo Git Server",
                "description": "Self-hosted Git server with GitHub-like features"
            },
            {
                "feature_key": "open_webui",
                "app_name": "Open-WebUI",
                "description": "AI chat interface"
            }
        ]
    """
    pool = await get_db_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT feature_key, name, description
            FROM add_ons
            WHERE feature_key IS NOT NULL
            AND is_active = TRUE
            ORDER BY name
            """
        )

        features = []
        for row in rows:
            features.append(AvailableFeatureResponse(
                feature_key=row['feature_key'],
                app_name=row['name'],
                description=row['description']
            ))

        logger.info(f"Admin {admin_user.get('email')} listed {len(features)} available features")
        return features
