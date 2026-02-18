"""
Tier Apps API
Manage app associations with subscription tiers.
"""

import os
from typing import List, Optional
from datetime import datetime

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

# Router configuration
router = APIRouter(prefix="/api/v1", tags=["subscriptions", "apps"])


# =============================================================================
# Authentication
# =============================================================================

async def get_current_admin(request: Request) -> str:
    """Get current admin user from session"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sessions = getattr(request.app.state, "sessions", {})
    session_data = sessions.get(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = session_data.get("user", {})
    username = user.get("username") or user.get("email", "unknown")

    # Check if user has admin role
    role = user.get("role", "").lower()
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return username


# =============================================================================
# Pydantic Models
# =============================================================================

class AppInfo(BaseModel):
    """App information"""
    id: int
    app_key: str
    app_name: str
    category: str
    description: Optional[str] = None
    is_active: bool
    sort_order: int


class TierAppResponse(BaseModel):
    """Tier app association"""
    tier_id: int
    tier_code: str
    tier_name: str
    app_id: int
    app_key: str
    app_name: str
    category: str
    enabled: bool
    description: Optional[str] = None


class TierAppsListResponse(BaseModel):
    """Complete list of apps for a tier"""
    tier_id: int
    tier_code: str
    tier_name: str
    apps: List[AppInfo]


class UpdateTierAppRequest(BaseModel):
    """Request to update a tier-app association"""
    app_key: str = Field(..., description="App key to update")
    enabled: bool = Field(..., description="Whether to enable or disable this app")


# =============================================================================
# Database Connection
# =============================================================================

async def get_db_connection():
    """Create database connection."""
    return await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "unicorn"),
        password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
        database=os.getenv("POSTGRES_DB", "unicorn_db")
    )


# =============================================================================
# Public Endpoints (No Auth Required)
# =============================================================================

@router.get("/tiers/apps", response_model=List[TierAppsListResponse])
async def list_all_tier_apps():
    """
    Get all subscription tiers with their associated apps.
    This endpoint is public - no authentication required.
    """
    conn = await get_db_connection()
    try:
        # Get all active tiers
        tiers_query = """
            SELECT id, tier_code, tier_name
            FROM subscription_tiers
            WHERE is_active = TRUE
            ORDER BY sort_order
        """
        tiers = await conn.fetch(tiers_query)

        result = []
        for tier in tiers:
            # Get apps for this tier
            apps_query = """
                SELECT
                    ao.id,
                    COALESCE(ao.slug, tf.feature_key) as app_key,
                    ao.name as app_name,
                    ao.category,
                    ao.description,
                    ao.is_active,
                    0 as sort_order
                FROM tier_features tf
                JOIN add_ons ao ON tf.feature_key = ao.slug OR tf.feature_key = CONCAT(ao.slug, '_access')
                WHERE tf.tier_id = $1 AND tf.enabled = TRUE AND ao.is_active = TRUE
                ORDER BY ao.category, ao.name
            """
            apps = await conn.fetch(apps_query, tier['id'])

            result.append({
                "tier_id": tier['id'],
                "tier_code": tier['tier_code'],
                "tier_name": tier['tier_name'],
                "apps": [dict(a) for a in apps]
            })

        return result
    finally:
        await conn.close()


@router.get("/tiers/{tier_code}/apps", response_model=TierAppsListResponse)
async def get_tier_apps(tier_code: str):
    """
    Get all apps for a specific tier by tier code.
    This endpoint is public - no authentication required.

    - **tier_code**: Tier code (e.g., 'vip_founder', 'byok', 'managed')
    """
    conn = await get_db_connection()
    try:
        # Get tier info
        tier_query = """
            SELECT id, tier_code, tier_name
            FROM subscription_tiers
            WHERE tier_code = $1 AND is_active = TRUE
        """
        tier = await conn.fetchrow(tier_query, tier_code)

        if not tier:
            raise HTTPException(status_code=404, detail=f"Tier '{tier_code}' not found")

        # Get apps for this tier (uses tier_features and add_ons tables)
        apps_query = """
            SELECT
                ao.id,
                COALESCE(ao.slug, tf.feature_key) as app_key,
                ao.name as app_name,
                ao.category,
                ao.description,
                ao.is_active,
                COALESCE(ao.sort_order, 0) as sort_order
            FROM tier_features tf
            JOIN add_ons ao ON tf.feature_key = ao.slug OR tf.feature_key = ao.feature_key
            WHERE tf.tier_id = $1 AND tf.enabled = TRUE AND ao.is_active = TRUE
            ORDER BY ao.category, COALESCE(ao.sort_order, 0), ao.name
        """
        apps = await conn.fetch(apps_query, tier['id'])

        return {
            "tier_id": tier['id'],
            "tier_code": tier['tier_code'],
            "tier_name": tier['tier_name'],
            "apps": [dict(a) for a in apps]
        }
    finally:
        await conn.close()


# =============================================================================
# Admin Endpoints (Auth Required)
# =============================================================================

@router.get("/admin/tiers/apps/detailed", response_model=List[TierAppResponse])
async def list_all_tier_apps_detailed(
    admin: str = Depends(get_current_admin)
):
    """
    Get detailed view of all tier-app associations.
    Admin only.
    """
    conn = await get_db_connection()
    try:
        query = """
            SELECT
                st.id as tier_id,
                st.tier_code,
                st.tier_name,
                ao.id as app_id,
                COALESCE(ao.slug, tf.feature_key) as app_key,
                ao.name as app_name,
                ao.category,
                ao.description,
                tf.enabled
            FROM tier_features tf
            JOIN subscription_tiers st ON tf.tier_id = st.id
            JOIN add_ons ao ON tf.feature_key = ao.slug OR tf.feature_key = ao.feature_key
            WHERE st.is_active = TRUE AND ao.is_active = TRUE
            ORDER BY st.sort_order, ao.category, COALESCE(ao.sort_order, 0), ao.name
        """
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    finally:
        await conn.close()


@router.put("/admin/tiers/{tier_code}/apps")
async def update_tier_apps(
    tier_code: str,
    updates: List[UpdateTierAppRequest],
    admin: str = Depends(get_current_admin)
):
    """
    Update which apps are enabled for a specific tier.
    Admin only.

    - **tier_code**: Tier code to update
    - **updates**: List of app updates
    """
    conn = await get_db_connection()
    try:
        # Get tier ID
        tier = await conn.fetchrow(
            "SELECT id FROM subscription_tiers WHERE tier_code = $1",
            tier_code
        )
        if not tier:
            raise HTTPException(status_code=404, detail=f"Tier '{tier_code}' not found")

        tier_id = tier['id']

        # Update each app (uses tier_features table with feature_key column)
        updated_count = 0
        for update in updates:
            # Check if association exists
            existing = await conn.fetchrow(
                "SELECT id FROM tier_features WHERE tier_id = $1 AND feature_key = $2",
                tier_id, update.app_key
            )

            if existing:
                # Update existing
                await conn.execute(
                    """
                    UPDATE tier_features
                    SET enabled = $1, updated_at = NOW()
                    WHERE tier_id = $2 AND feature_key = $3
                    """,
                    update.enabled, tier_id, update.app_key
                )
                updated_count += 1
            else:
                # Insert new
                await conn.execute(
                    """
                    INSERT INTO tier_features (tier_id, feature_key, enabled)
                    VALUES ($1, $2, $3)
                    """,
                    tier_id, update.app_key, update.enabled
                )
                updated_count += 1

        return {
            "success": True,
            "tier_code": tier_code,
            "updated_count": updated_count,
            "message": f"Updated {updated_count} app(s) for tier '{tier_code}'"
        }
    finally:
        await conn.close()


@router.post("/admin/tiers/{tier_code}/apps/bulk")
async def bulk_set_tier_apps(
    tier_code: str,
    app_keys: List[str],
    enabled: bool = True,
    admin: str = Depends(get_current_admin)
):
    """
    Bulk enable/disable multiple apps for a tier.
    Admin only.

    - **tier_code**: Tier code to update
    - **app_keys**: List of app keys to update
    - **enabled**: Whether to enable or disable these apps
    """
    conn = await get_db_connection()
    try:
        # Get tier ID
        tier = await conn.fetchrow(
            "SELECT id FROM subscription_tiers WHERE tier_code = $1",
            tier_code
        )
        if not tier:
            raise HTTPException(status_code=404, detail=f"Tier '{tier_code}' not found")

        tier_id = tier['id']

        # Update all apps (uses tier_features table with feature_key column)
        for app_key in app_keys:
            # Upsert (insert or update)
            await conn.execute(
                """
                INSERT INTO tier_features (tier_id, feature_key, enabled)
                VALUES ($1, $2, $3)
                ON CONFLICT (tier_id, feature_key)
                DO UPDATE SET enabled = $3, updated_at = NOW()
                """,
                tier_id, app_key, enabled
            )

        return {
            "success": True,
            "tier_code": tier_code,
            "app_count": len(app_keys),
            "enabled": enabled,
            "message": f"Bulk {'enabled' if enabled else 'disabled'} {len(app_keys)} app(s) for tier '{tier_code}'"
        }
    finally:
        await conn.close()
