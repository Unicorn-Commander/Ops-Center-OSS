"""
Subscription Tier Management API
Provides admin interface for managing subscription tiers, features, and user migrations
Epic 4.4: Subscription Management GUI
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import asyncpg
import json

# Import Lago integration for plan synchronization
from lago_integration import (
    create_subscription,
    update_subscription_plan,
    get_subscription,
    LagoIntegrationError
)

# Import Keycloak integration for user tier updates
from keycloak_integration import (
    update_user_attributes,
    get_user_by_id
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin/tiers", tags=["subscription-tiers"])


# ============================================
# Pydantic Models
# ============================================

class SubscriptionTierBase(BaseModel):
    """Base subscription tier model"""
    tier_code: str = Field(..., min_length=2, max_length=50, description="Unique tier code (lowercase)")
    tier_name: str = Field(..., min_length=2, max_length=100, description="Display name")
    description: Optional[str] = Field(None, description="Tier description")
    price_monthly: float = Field(..., ge=0, description="Monthly price")
    price_yearly: Optional[float] = Field(None, ge=0, description="Yearly price")
    is_active: bool = Field(True, description="Is tier active")
    is_invite_only: bool = Field(False, description="Invite-only tier")
    sort_order: int = Field(0, ge=0, description="Display order")
    api_calls_limit: int = Field(0, ge=-1, description="API calls limit (-1 = unlimited)")
    team_seats: int = Field(1, ge=1, description="Team seats")
    byok_enabled: bool = Field(False, description="BYOK enabled")
    priority_support: bool = Field(False, description="Priority support")
    lago_plan_code: Optional[str] = Field(None, description="Lago plan code")
    stripe_price_monthly: Optional[str] = Field(None, description="Stripe monthly price ID")
    stripe_price_yearly: Optional[str] = Field(None, description="Stripe yearly price ID")

    @validator('tier_code')
    def tier_code_lowercase(cls, v):
        """Ensure tier_code is lowercase"""
        return v.lower().strip()


class SubscriptionTierCreate(SubscriptionTierBase):
    """Create subscription tier request"""
    pass


class SubscriptionTierUpdate(BaseModel):
    """Update subscription tier request (all fields optional)"""
    tier_name: Optional[str] = None
    description: Optional[str] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    is_active: Optional[bool] = None
    is_invite_only: Optional[bool] = None
    sort_order: Optional[int] = None
    api_calls_limit: Optional[int] = None
    team_seats: Optional[int] = None
    byok_enabled: Optional[bool] = None
    priority_support: Optional[bool] = None
    lago_plan_code: Optional[str] = None
    stripe_price_monthly: Optional[str] = None
    stripe_price_yearly: Optional[str] = None


class SubscriptionTierResponse(SubscriptionTierBase):
    """Subscription tier response"""
    id: int
    feature_count: int = 0
    active_user_count: int = 0
    monthly_revenue: float = 0.0
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class TierFeature(BaseModel):
    """Tier feature model"""
    feature_key: str
    feature_value: Optional[str] = None
    enabled: bool = True


class TierFeatureUpdate(BaseModel):
    """Update tier features request"""
    features: List[TierFeature]


class UserTierMigration(BaseModel):
    """User tier migration request"""
    user_id: str
    new_tier_code: str
    reason: str = Field(..., min_length=10, description="Reason for tier change")
    send_notification: bool = Field(True, description="Send email notification")


class TierMigrationHistory(BaseModel):
    """Tier migration history entry"""
    id: int
    user_id: str
    user_email: Optional[str]
    old_tier_code: Optional[str]
    new_tier_code: str
    change_reason: str
    changed_by: str
    change_timestamp: datetime
    old_api_limit: Optional[int]
    new_api_limit: Optional[int]
    api_calls_used: Optional[int]


class TierAnalytics(BaseModel):
    """Tier analytics response"""
    total_tiers: int
    active_tiers: int
    total_users: int
    tier_distribution: Dict[str, int]
    revenue_by_tier: Dict[str, float]


# ============================================
# Dependency: Get database connection
# ============================================

async def get_db_connection():
    """Get PostgreSQL database connection"""
    import os
    try:
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            user=os.getenv("POSTGRES_USER", "unicorn"),
            password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
            database=os.getenv("POSTGRES_DB", "unicorn_db")
        )
        yield conn
    finally:
        if conn:
            await conn.close()


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

    # Check if user has admin role - check both singular role and roles array for compatibility
    user_role = user.get("role", "")
    user_roles = user.get("roles", [])

    is_admin = (
        user_role == "admin" or
        user_role == "system_admin" or
        "admin" in user_roles or
        "system_admin" in user_roles
    )

    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return username


# ============================================
# CRUD: Subscription Tiers
# ============================================

@router.get("/", response_model=List[SubscriptionTierResponse])
async def list_tiers(
    active_only: bool = False,
    conn = Depends(get_db_connection)
):
    """
    List all subscription tiers.

    Args:
        active_only: Filter to active tiers only

    Returns:
        List of subscription tiers with analytics
    """
    try:
        query = """
            SELECT
                st.id, st.tier_code, st.tier_name, st.description,
                st.price_monthly, st.price_yearly, st.is_active, st.is_invite_only,
                st.sort_order, st.api_calls_limit, st.team_seats,
                st.byok_enabled, st.priority_support,
                st.lago_plan_code, st.stripe_price_monthly, st.stripe_price_yearly,
                st.created_at, st.updated_at, st.created_by, st.updated_by,
                COALESCE(COUNT(DISTINCT ta.id), 0) AS feature_count
            FROM subscription_tiers st
            LEFT JOIN tier_features ta ON st.id = ta.tier_id AND ta.enabled = TRUE
        """

        if active_only:
            query += " WHERE st.is_active = TRUE"

        query += """
            GROUP BY st.id
            ORDER BY st.sort_order, st.tier_name
        """

        rows = await conn.fetch(query)

        tiers = []
        for row in rows:
            tier_data = dict(row)
            # TODO: Get active user count and revenue from Keycloak/Lago
            tier_data['active_user_count'] = 0
            tier_data['monthly_revenue'] = 0.0
            tiers.append(SubscriptionTierResponse(**tier_data))

        return tiers

    except Exception as e:
        logger.error(f"Error listing tiers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list tiers: {str(e)}")


@router.get("/{tier_id}", response_model=SubscriptionTierResponse)
async def get_tier(
    tier_id: int,
    conn = Depends(get_db_connection)
):
    """
    Get subscription tier by ID.

    Args:
        tier_id: Tier ID

    Returns:
        Subscription tier details
    """
    try:
        query = """
            SELECT
                st.id, st.tier_code, st.tier_name, st.description,
                st.price_monthly, st.price_yearly, st.is_active, st.is_invite_only,
                st.sort_order, st.api_calls_limit, st.team_seats,
                st.byok_enabled, st.priority_support,
                st.lago_plan_code, st.stripe_price_monthly, st.stripe_price_yearly,
                st.created_at, st.updated_at, st.created_by, st.updated_by,
                COALESCE(COUNT(DISTINCT ta.id), 0) AS feature_count
            FROM subscription_tiers st
            LEFT JOIN tier_features ta ON st.id = ta.tier_id AND ta.enabled = TRUE
            WHERE st.id = $1
            GROUP BY st.id
        """

        row = await conn.fetchrow(query, tier_id)

        if not row:
            raise HTTPException(status_code=404, detail=f"Tier {tier_id} not found")

        tier_data = dict(row)
        tier_data['active_user_count'] = 0
        tier_data['monthly_revenue'] = 0.0

        return SubscriptionTierResponse(**tier_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tier {tier_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get tier: {str(e)}")


@router.post("/", response_model=SubscriptionTierResponse, status_code=201)
async def create_tier(
    tier: SubscriptionTierCreate,
    request: Request,
    admin: str = Depends(get_current_admin),
    conn = Depends(get_db_connection)
):
    """
    Create new subscription tier.

    Args:
        tier: Tier definition

    Returns:
        Created tier

    Raises:
        HTTPException: If tier_code already exists or Lago sync fails
    """
    try:
        # Check if tier_code already exists
        existing = await conn.fetchrow(
            "SELECT id FROM subscription_tiers WHERE tier_code = $1",
            tier.tier_code
        )

        if existing:
            raise HTTPException(status_code=409, detail=f"Tier code '{tier.tier_code}' already exists")

        # Insert tier
        query = """
            INSERT INTO subscription_tiers (
                tier_code, tier_name, description, price_monthly, price_yearly,
                is_active, is_invite_only, sort_order, api_calls_limit, team_seats,
                byok_enabled, priority_support, lago_plan_code,
                stripe_price_monthly, stripe_price_yearly, created_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            RETURNING id, created_at, updated_at
        """

        row = await conn.fetchrow(
            query,
            tier.tier_code, tier.tier_name, tier.description,
            tier.price_monthly, tier.price_yearly, tier.is_active,
            tier.is_invite_only, tier.sort_order, tier.api_calls_limit,
            tier.team_seats, tier.byok_enabled, tier.priority_support,
            tier.lago_plan_code, tier.stripe_price_monthly,
            tier.stripe_price_yearly, admin
        )

        # Sync with Lago if plan code provided
        if tier.lago_plan_code:
            logger.info(f"Tier {tier.tier_code} created, Lago plan: {tier.lago_plan_code}")
            # Note: Lago plans should be created in Lago dashboard first
            # This is just for reference/mapping

        # Return created tier
        created_tier = SubscriptionTierResponse(
            id=row['id'],
            **tier.dict(),
            feature_count=0,
            active_user_count=0,
            monthly_revenue=0.0,
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            created_by=admin,
            updated_by=admin
        )

        logger.info(f"Created tier: {tier.tier_code} by {admin}")
        return created_tier

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tier: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create tier: {str(e)}")


@router.put("/{tier_id}", response_model=SubscriptionTierResponse)
async def update_tier(
    tier_id: int,
    tier_update: SubscriptionTierUpdate,
    request: Request,
    admin: str = Depends(get_current_admin),
    conn = Depends(get_db_connection)
):
    """
    Update subscription tier.

    Args:
        tier_id: Tier ID
        tier_update: Fields to update

    Returns:
        Updated tier
    """
    try:
        # Check tier exists
        existing = await conn.fetchrow("SELECT * FROM subscription_tiers WHERE id = $1", tier_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Tier {tier_id} not found")

        # Build update query dynamically
        updates = []
        params = []
        param_idx = 1

        for field, value in tier_update.dict(exclude_unset=True).items():
            updates.append(f"{field} = ${param_idx}")
            params.append(value)
            param_idx += 1

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Add updated_by
        updates.append(f"updated_by = ${param_idx}")
        params.append(admin)
        param_idx += 1

        # Add tier_id for WHERE clause
        params.append(tier_id)

        query = f"""
            UPDATE subscription_tiers
            SET {', '.join(updates)}
            WHERE id = ${param_idx}
            RETURNING *
        """

        row = await conn.fetchrow(query, *params)

        logger.info(f"Updated tier {tier_id} by {admin}")

        # Return updated tier
        return await get_tier(tier_id, conn)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tier {tier_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update tier: {str(e)}")


@router.delete("/{tier_id}")
async def delete_tier(
    tier_id: int,
    admin: str = Depends(get_current_admin),
    conn = Depends(get_db_connection)
):
    """
    Soft delete subscription tier (mark as inactive).

    Args:
        tier_id: Tier ID

    Returns:
        Success message
    """
    try:
        # Check tier exists
        existing = await conn.fetchrow("SELECT tier_code FROM subscription_tiers WHERE id = $1", tier_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Tier {tier_id} not found")

        # Check if any users are on this tier
        # TODO: Query Keycloak for users with this tier
        # For now, just soft delete

        # Soft delete (mark inactive)
        await conn.execute(
            "UPDATE subscription_tiers SET is_active = FALSE, updated_by = $1 WHERE id = $2",
            admin, tier_id
        )

        logger.info(f"Soft deleted tier {tier_id} ({existing['tier_code']}) by {admin}")

        return {
            "success": True,
            "message": f"Tier '{existing['tier_code']}' marked as inactive"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tier {tier_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete tier: {str(e)}")


@router.post("/{tier_code}/clone", response_model=SubscriptionTierResponse, status_code=201)
async def clone_tier(
    tier_code: str,
    new_tier_code: str,
    new_tier_name: str,
    price_monthly: Optional[float] = None,
    admin: str = Depends(get_current_admin),
    conn = Depends(get_db_connection)
):
    """
    Clone an existing subscription tier with all its settings and apps.

    Args:
        tier_code: Source tier code to clone
        new_tier_code: New tier code (must be unique)
        new_tier_name: New tier display name
        price_monthly: Optional new monthly price (defaults to source tier price)

    Returns:
        Created tier with cloned settings

    Raises:
        HTTPException: If source tier not found or new tier_code already exists
    """
    try:
        # Get source tier
        source_tier = await conn.fetchrow(
            "SELECT * FROM subscription_tiers WHERE tier_code = $1",
            tier_code
        )

        if not source_tier:
            raise HTTPException(status_code=404, detail=f"Source tier '{tier_code}' not found")

        # Check if new tier_code already exists
        existing = await conn.fetchrow(
            "SELECT id FROM subscription_tiers WHERE tier_code = $1",
            new_tier_code.lower().strip()
        )

        if existing:
            raise HTTPException(status_code=409, detail=f"Tier code '{new_tier_code}' already exists")

        # Use provided price or copy from source
        final_price = price_monthly if price_monthly is not None else source_tier['price_monthly']

        # Start transaction to clone tier and apps atomically
        async with conn.transaction():
            # Insert cloned tier
            query = """
                INSERT INTO subscription_tiers (
                    tier_code, tier_name, description, price_monthly, price_yearly,
                    is_active, is_invite_only, sort_order, api_calls_limit, team_seats,
                    byok_enabled, priority_support, lago_plan_code,
                    stripe_price_monthly, stripe_price_yearly, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                RETURNING id, created_at, updated_at
            """

            row = await conn.fetchrow(
                query,
                new_tier_code.lower().strip(),
                new_tier_name,
                source_tier['description'],
                final_price,
                source_tier['price_yearly'],
                source_tier['is_active'],
                source_tier['is_invite_only'],
                source_tier['sort_order'] + 1,  # Place after source tier
                source_tier['api_calls_limit'],
                source_tier['team_seats'],
                source_tier['byok_enabled'],
                source_tier['priority_support'],
                None,  # Don't clone Lago plan code
                None,  # Don't clone Stripe price ID
                None,  # Don't clone Stripe yearly price ID
                admin
            )

            new_tier_id = row['id']

            # Clone all tier-app associations
            clone_apps_query = """
                INSERT INTO tier_features (tier_id, feature_key, enabled)
                SELECT $1, feature_key, enabled
                FROM tier_features
                WHERE tier_id = $2
            """

            await conn.execute(clone_apps_query, new_tier_id, source_tier['id'])

            # Get app count
            app_count = await conn.fetchval(
                "SELECT COUNT(*) FROM tier_features WHERE tier_id = $1 AND enabled = TRUE",
                new_tier_id
            )

        logger.info(f"Cloned tier '{tier_code}' to '{new_tier_code}' with {app_count} apps by {admin}")

        # Return created tier
        created_tier = SubscriptionTierResponse(
            id=new_tier_id,
            tier_code=new_tier_code.lower().strip(),
            tier_name=new_tier_name,
            description=source_tier['description'],
            price_monthly=final_price,
            price_yearly=source_tier['price_yearly'],
            is_active=source_tier['is_active'],
            is_invite_only=source_tier['is_invite_only'],
            sort_order=source_tier['sort_order'] + 1,
            api_calls_limit=source_tier['api_calls_limit'],
            team_seats=source_tier['team_seats'],
            byok_enabled=source_tier['byok_enabled'],
            priority_support=source_tier['priority_support'],
            lago_plan_code=None,
            stripe_price_monthly=None,
            stripe_price_yearly=None,
            feature_count=app_count,
            active_user_count=0,
            monthly_revenue=0.0,
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            created_by=admin,
            updated_by=admin
        )

        return created_tier

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cloning tier '{tier_code}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clone tier: {str(e)}")


# ============================================
# App Management
# ============================================

@router.get("/{tier_id}/apps", response_model=List[TierFeature])
async def get_tier_features(
    tier_id: int,
    conn = Depends(get_db_connection)
):
    """
    Get apps for a tier.

    Args:
        tier_id: Tier ID

    Returns:
        List of tier apps
    """
    try:
        query = """
            SELECT feature_key, feature_value, enabled
            FROM tier_features
            WHERE tier_id = $1
            ORDER BY feature_key
        """

        rows = await conn.fetch(query, tier_id)

        return [TierFeature(**dict(row)) for row in rows]

    except Exception as e:
        logger.error(f"Error getting apps for tier {tier_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get apps: {str(e)}")


@router.put("/{tier_id}/apps")
async def update_tier_features(
    tier_id: int,
    apps: TierFeatureUpdate,
    admin: str = Depends(get_current_admin),
    conn = Depends(get_db_connection)
):
    """
    Update tier apps (replace all).

    Args:
        tier_id: Tier ID
        apps: App list

    Returns:
        Success message
    """
    try:
        # Check tier exists
        existing = await conn.fetchrow("SELECT tier_code FROM subscription_tiers WHERE id = $1", tier_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Tier {tier_id} not found")

        # Start transaction
        async with conn.transaction():
            # Delete existing apps
            await conn.execute("DELETE FROM tier_features WHERE tier_id = $1", tier_id)

            # Insert new apps
            for app in apps.features:
                await conn.execute(
                    """
                    INSERT INTO tier_features (tier_id, feature_key, feature_value, enabled)
                    VALUES ($1, $2, $3, $4)
                    """,
                    tier_id, app.feature_key, app.feature_value, app.enabled
                )

        logger.info(f"Updated {len(apps.features)} apps for tier {tier_id} by {admin}")

        return {
            "success": True,
            "message": f"Updated {len(apps.features)} apps for tier '{existing['tier_code']}'"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating apps for tier {tier_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update apps: {str(e)}")


# ============================================
# User Tier Migration
# ============================================

@router.post("/users/{user_id}/migrate-tier")
async def migrate_user_tier(
    user_id: str,
    migration: UserTierMigration,
    request: Request,
    admin: str = Depends(get_current_admin),
    conn = Depends(get_db_connection)
):
    """
    Migrate user to new tier.

    Args:
        user_id: Keycloak user ID
        migration: Migration details

    Returns:
        Migration result

    Raises:
        HTTPException: If user not found or tier invalid
    """
    try:
        # Get user from Keycloak
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        user_email = user.get("email", "unknown")

        # Get new tier
        new_tier = await conn.fetchrow(
            "SELECT * FROM subscription_tiers WHERE tier_code = $1 AND is_active = TRUE",
            migration.new_tier_code
        )

        if not new_tier:
            raise HTTPException(status_code=404, detail=f"Tier '{migration.new_tier_code}' not found")

        # Get old tier from user attributes
        old_tier_code = user.get("attributes", {}).get("subscription_tier", [None])[0]
        old_api_limit = user.get("attributes", {}).get("api_calls_limit", [0])[0]
        api_calls_used = user.get("attributes", {}).get("api_calls_used", [0])[0]

        # Record migration in history
        await conn.execute(
            """
            INSERT INTO user_tier_history (
                user_id, user_email, old_tier_code, new_tier_code,
                change_reason, changed_by, old_api_limit, new_api_limit, api_calls_used
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            user_id, user_email, old_tier_code, migration.new_tier_code,
            migration.reason, admin,
            int(old_api_limit) if old_api_limit else 0,
            new_tier['api_calls_limit'], int(api_calls_used) if api_calls_used else 0
        )

        # Update user attributes in Keycloak
        await update_user_attributes(user_id, {
            "subscription_tier": migration.new_tier_code,
            "api_calls_limit": str(new_tier['api_calls_limit']),
            "subscription_status": "active"
        })

        logger.info(f"Migrated user {user_id} from {old_tier_code} to {migration.new_tier_code} by {admin}")

        # TODO: Send notification email if migration.send_notification

        return {
            "success": True,
            "message": f"User migrated from '{old_tier_code}' to '{migration.new_tier_code}'",
            "user_id": user_id,
            "user_email": user_email,
            "old_tier": old_tier_code,
            "new_tier": migration.new_tier_code,
            "new_api_limit": new_tier['api_calls_limit']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error migrating user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to migrate user: {str(e)}")


@router.get("/migrations", response_model=List[TierMigrationHistory])
async def get_tier_migrations(
    user_id: Optional[str] = None,
    tier_code: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    conn = Depends(get_db_connection)
):
    """
    Get tier migration audit log.

    Args:
        user_id: Filter by user ID
        tier_code: Filter by new tier code
        limit: Pagination limit
        offset: Pagination offset

    Returns:
        List of migration history entries
    """
    try:
        query = """
            SELECT
                id, user_id, user_email, old_tier_code, new_tier_code,
                change_reason, changed_by, change_timestamp,
                old_api_limit, new_api_limit, api_calls_used
            FROM user_tier_history
            WHERE 1=1
        """

        params = []
        param_idx = 1

        if user_id:
            query += f" AND user_id = ${param_idx}"
            params.append(user_id)
            param_idx += 1

        if tier_code:
            query += f" AND new_tier_code = ${param_idx}"
            params.append(tier_code)
            param_idx += 1

        query += f" ORDER BY change_timestamp DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        rows = await conn.fetch(query, *params)

        return [TierMigrationHistory(**dict(row)) for row in rows]

    except Exception as e:
        logger.error(f"Error getting migration history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get migration history: {str(e)}")


# ============================================
# Analytics
# ============================================

@router.get("/analytics/summary", response_model=TierAnalytics)
async def get_tier_analytics(
    conn = Depends(get_db_connection)
):
    """
    Get tier analytics summary.

    Returns:
        Tier distribution and revenue analytics
    """
    try:
        # Count tiers
        total_tiers = await conn.fetchval("SELECT COUNT(*) FROM subscription_tiers")
        active_tiers = await conn.fetchval("SELECT COUNT(*) FROM subscription_tiers WHERE is_active = TRUE")

        # TODO: Get user counts from Keycloak
        # For now, return placeholder data
        tier_distribution = {}
        revenue_by_tier = {}

        return TierAnalytics(
            total_tiers=total_tiers,
            active_tiers=active_tiers,
            total_users=0,
            tier_distribution=tier_distribution,
            revenue_by_tier=revenue_by_tier
        )

    except Exception as e:
        logger.error(f"Error getting tier analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")
