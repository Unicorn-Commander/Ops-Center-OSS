"""
Org Access API - Organization-centric multi-tenancy endpoints

Provides endpoints for:
- Getting user's organizations with their tier info and accessible apps
- Switching between organizations
- Getting current org context

This is the core of the org-centric model where:
- Organizations own subscription tiers (not users)
- Users can belong to multiple organizations
- App access is determined by org's tier
"""

import os
import sys
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, Response, Query
from pydantic import BaseModel
import asyncpg

# Configure logging
logger = logging.getLogger(__name__)

# Router configuration
router = APIRouter(prefix="/api/v1/users/me", tags=["org-access"])


# =============================================================================
# Pydantic Models
# =============================================================================

class AppInfo(BaseModel):
    """App accessible via organization tier"""
    slug: str
    name: str
    url: str
    icon: Optional[str] = None


class TierInfo(BaseModel):
    """Subscription tier information"""
    code: str
    name: str


class OrganizationInfo(BaseModel):
    """Organization with tier and app access info"""
    id: str
    name: str
    slug: str
    role: str
    tier: TierInfo
    apps: List[AppInfo]


class OrganizationsResponse(BaseModel):
    """Response for user's organizations"""
    organizations: List[OrganizationInfo]
    current_org_id: Optional[str] = None
    default_org_id: Optional[str] = None


class SwitchOrgRequest(BaseModel):
    """Request to switch organization"""
    org_id: str


class SwitchOrgResponse(BaseModel):
    """Response after switching organization"""
    success: bool
    org_id: str
    org_name: str
    tier_code: str


class CurrentOrgResponse(BaseModel):
    """Current organization context"""
    org_id: Optional[str] = None
    org_name: Optional[str] = None
    org_slug: Optional[str] = None
    tier_code: Optional[str] = None
    tier_name: Optional[str] = None
    role: Optional[str] = None
    apps: List[AppInfo] = []


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
# Authentication Helpers
# =============================================================================

async def get_user_id_from_session(request: Request) -> Optional[str]:
    """
    Extract user ID from session cookie.
    Returns None if not authenticated.
    """
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    try:
        from redis_session import RedisSessionManager

        session_token = request.cookies.get("session_token")
        if not session_token:
            return None

        redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))

        sessions = RedisSessionManager(host=redis_host, port=redis_port)

        if session_token not in sessions:
            return None

        session_data = sessions[session_token]

        # Get user_id from session (multiple possible locations)
        user_id = (
            session_data.get("user_id") or
            session_data.get("sub") or
            session_data.get("id") or
            session_data.get("user", {}).get("id") or
            session_data.get("user", {}).get("sub")
        )

        return user_id

    except Exception as e:
        logger.warning(f"Error extracting user ID from session: {e}")
        return None


def get_current_org_id_from_cookie(request: Request) -> Optional[str]:
    """Get current org ID from cookie."""
    return request.cookies.get("current_org_id")


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/organizations", response_model=OrganizationsResponse)
async def get_user_organizations(request: Request):
    """
    Get all organizations the current user belongs to.

    Returns organization list with:
    - Organization details (id, name, slug)
    - User's role in each org
    - Tier information
    - Accessible apps based on tier

    Also returns current_org_id (from cookie) and default_org_id (first org).
    """
    user_id = await get_user_id_from_session(request)

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    conn = await get_db_connection()
    try:
        # Query user's organizations with tier and app info
        query = """
            SELECT
                o.id::text as org_id,
                o.name as org_name,
                COALESCE(LOWER(REPLACE(o.name, ' ', '-')), o.id::text) as org_slug,
                om.role,
                COALESCE(st.tier_code, o.plan_tier, 'managed') as tier_code,
                COALESCE(st.tier_name, INITCAP(REPLACE(o.plan_tier, '_', ' ')), 'Managed') as tier_name
            FROM organization_members om
            JOIN organizations o ON om.org_id = o.id
            LEFT JOIN subscription_tiers st ON o.plan_tier = st.tier_code
            WHERE om.user_id = $1
              AND o.status = 'active'
            ORDER BY o.name
        """

        org_rows = await conn.fetch(query, user_id)

        if not org_rows:
            # User has no organizations - return empty list
            return OrganizationsResponse(
                organizations=[],
                current_org_id=None,
                default_org_id=None
            )

        # Build organizations list with apps
        organizations = []
        for org_row in org_rows:
            org_id = org_row['org_id']

            # Get apps for this org's tier
            apps_query = """
                SELECT
                    ao.slug,
                    ao.name,
                    ao.launch_url as url,
                    ao.icon_url as icon
                FROM tier_features tf
                JOIN add_ons ao ON tf.feature_key = ao.feature_key
                JOIN subscription_tiers st ON tf.tier_id = st.id
                JOIN organizations o ON o.plan_tier = st.tier_code
                WHERE o.id = $1
                  AND tf.enabled = TRUE
                  AND ao.is_active = TRUE
                  AND ao.launch_url IS NOT NULL
                ORDER BY ao.sort_order, ao.name
            """

            try:
                app_rows = await conn.fetch(apps_query, org_id)
                apps = [
                    AppInfo(
                        slug=row['slug'],
                        name=row['name'],
                        url=row['url'],
                        icon=row['icon']
                    )
                    for row in app_rows
                ]
            except Exception as e:
                logger.warning(f"Error fetching apps for org {org_id}: {e}")
                apps = []

            organizations.append(OrganizationInfo(
                id=org_id,
                name=org_row['org_name'],
                slug=org_row['org_slug'],
                role=org_row['role'],
                tier=TierInfo(
                    code=org_row['tier_code'],
                    name=org_row['tier_name']
                ),
                apps=apps
            ))

        # Get current org from cookie, validate it's in user's list
        current_org_id = get_current_org_id_from_cookie(request)
        org_ids = [org.id for org in organizations]

        if current_org_id and current_org_id not in org_ids:
            current_org_id = None

        default_org_id = org_ids[0] if org_ids else None

        return OrganizationsResponse(
            organizations=organizations,
            current_org_id=current_org_id or default_org_id,
            default_org_id=default_org_id
        )

    except asyncpg.PostgresError as e:
        logger.error(f"Database error in get_user_organizations: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        await conn.close()


@router.post("/switch-org", response_model=SwitchOrgResponse)
async def switch_organization(
    request: Request,
    response: Response,
    body: SwitchOrgRequest
):
    """
    Switch user's active organization context.

    Validates user is member of the requested org, then:
    - Sets current_org_id cookie
    - Returns org details for confirmation
    """
    user_id = await get_user_id_from_session(request)

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    conn = await get_db_connection()
    try:
        # Verify user is member of this org
        membership_query = """
            SELECT
                o.id::text as org_id,
                o.name as org_name,
                om.role,
                COALESCE(st.tier_code, 'managed') as tier_code
            FROM organization_members om
            JOIN organizations o ON om.org_id = o.id
            LEFT JOIN subscription_tiers st ON o.plan_tier = st.tier_code
            WHERE om.user_id = $1
              AND o.id = $2
              AND o.status = 'active'
        """

        row = await conn.fetchrow(membership_query, user_id, body.org_id)

        if not row:
            raise HTTPException(
                status_code=403,
                detail="Not a member of this organization"
            )

        # Set cookie for current org
        # Use secure settings for production
        response.set_cookie(
            key="current_org_id",
            value=row['org_id'],
            httponly=True,
            secure=os.getenv("ENVIRONMENT", "production") == "production",
            samesite="lax",
            max_age=60 * 60 * 24 * 365,  # 1 year
            domain=os.getenv("SESSION_COOKIE_DOMAIN", None)  # Allow cross-subdomain
        )

        logger.info(f"User {user_id} switched to org {row['org_id']} ({row['org_name']})")

        return SwitchOrgResponse(
            success=True,
            org_id=row['org_id'],
            org_name=row['org_name'],
            tier_code=row['tier_code']
        )

    except asyncpg.PostgresError as e:
        logger.error(f"Database error in switch_organization: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        await conn.close()


@router.get("/current-org", response_model=CurrentOrgResponse)
async def get_current_organization(request: Request):
    """
    Get user's currently active organization.

    Uses current_org_id from cookie, falls back to first org if not set.
    Returns full org details including accessible apps.
    """
    user_id = await get_user_id_from_session(request)

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    current_org_id = get_current_org_id_from_cookie(request)

    conn = await get_db_connection()
    try:
        # Build query - either for specific org or first available
        if current_org_id:
            query = """
                SELECT
                    o.id::text as org_id,
                    o.name as org_name,
                    COALESCE(o.slug, LOWER(REPLACE(o.name, ' ', '-'))) as org_slug,
                    om.role,
                    COALESCE(st.tier_code, 'managed') as tier_code,
                    COALESCE(st.tier_name, 'Managed') as tier_name
                FROM organization_members om
                JOIN organizations o ON om.org_id = o.id
                LEFT JOIN subscription_tiers st ON o.plan_tier = st.tier_code
                WHERE om.user_id = $1
                  AND o.id = $2
                  AND o.status = 'active'
            """
            row = await conn.fetchrow(query, user_id, current_org_id)
        else:
            row = None

        # Fall back to first org if cookie invalid or not set
        if not row:
            query = """
                SELECT
                    o.id::text as org_id,
                    o.name as org_name,
                    COALESCE(o.slug, LOWER(REPLACE(o.name, ' ', '-'))) as org_slug,
                    om.role,
                    COALESCE(st.tier_code, 'managed') as tier_code,
                    COALESCE(st.tier_name, 'Managed') as tier_name
                FROM organization_members om
                JOIN organizations o ON om.org_id = o.id
                LEFT JOIN subscription_tiers st ON o.plan_tier = st.tier_code
                WHERE om.user_id = $1
                  AND o.status = 'active'
                ORDER BY o.name
                LIMIT 1
            """
            row = await conn.fetchrow(query, user_id)

        if not row:
            # User has no organizations
            return CurrentOrgResponse()

        org_id = row['org_id']

        # Get apps for this org
        apps_query = """
            SELECT
                ao.slug,
                ao.name,
                ao.launch_url as url,
                ao.icon_url as icon
            FROM tier_features tf
            JOIN add_ons ao ON tf.feature_key = ao.feature_key
            JOIN subscription_tiers st ON tf.tier_id = st.id
            JOIN organizations o ON o.plan_tier = st.tier_code
            WHERE o.id = $1
              AND tf.enabled = TRUE
              AND ao.is_active = TRUE
              AND ao.launch_url IS NOT NULL
            ORDER BY ao.sort_order, ao.name
        """

        try:
            app_rows = await conn.fetch(apps_query, org_id)
            apps = [
                AppInfo(
                    slug=r['slug'],
                    name=r['name'],
                    url=r['url'],
                    icon=r['icon']
                )
                for r in app_rows
            ]
        except Exception as e:
            logger.warning(f"Error fetching apps for current org: {e}")
            apps = []

        return CurrentOrgResponse(
            org_id=org_id,
            org_name=row['org_name'],
            org_slug=row['org_slug'],
            tier_code=row['tier_code'],
            tier_name=row['tier_name'],
            role=row['role'],
            apps=apps
        )

    except asyncpg.PostgresError as e:
        logger.error(f"Database error in get_current_organization: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        await conn.close()


# =============================================================================
# Org-Aware My Apps Endpoint
# =============================================================================

@router.get("/apps", response_model=List[AppInfo])
async def get_org_apps(
    request: Request,
    org_id: Optional[str] = Query(None, description="Organization ID (uses current org if not specified)")
):
    """
    Get apps accessible in the specified organization context.

    If org_id not provided, uses current_org_id from cookie.
    Returns apps based on the organization's subscription tier.
    """
    user_id = await get_user_id_from_session(request)

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Use provided org_id or fall back to cookie
    target_org_id = org_id or get_current_org_id_from_cookie(request)

    conn = await get_db_connection()
    try:
        # If no org specified, get user's first org
        if not target_org_id:
            first_org_query = """
                SELECT o.id::text as org_id
                FROM organization_members om
                JOIN organizations o ON om.org_id = o.id
                WHERE om.user_id = $1 AND o.status = 'active'
                ORDER BY o.name LIMIT 1
            """
            row = await conn.fetchrow(first_org_query, user_id)
            if row:
                target_org_id = row['org_id']

        if not target_org_id:
            return []  # User has no organizations

        # Verify user is member
        member_check = """
            SELECT 1 FROM organization_members om
            JOIN organizations o ON om.org_id = o.id
            WHERE om.user_id = $1 AND o.id = $2 AND o.status = 'active'
        """
        is_member = await conn.fetchrow(member_check, user_id, target_org_id)

        if not is_member:
            raise HTTPException(
                status_code=403,
                detail="Not a member of this organization"
            )

        # Get apps for org's tier
        apps_query = """
            SELECT
                ao.slug,
                ao.name,
                ao.launch_url as url,
                ao.icon_url as icon
            FROM tier_features tf
            JOIN add_ons ao ON tf.feature_key = ao.feature_key
            JOIN subscription_tiers st ON tf.tier_id = st.id
            JOIN organizations o ON o.plan_tier = st.tier_code
            WHERE o.id = $1
              AND tf.enabled = TRUE
              AND ao.is_active = TRUE
              AND ao.launch_url IS NOT NULL
            ORDER BY ao.sort_order, ao.name
        """

        app_rows = await conn.fetch(apps_query, target_org_id)

        return [
            AppInfo(
                slug=r['slug'],
                name=r['name'],
                url=r['url'],
                icon=r['icon']
            )
            for r in app_rows
        ]

    except asyncpg.PostgresError as e:
        logger.error(f"Database error in get_org_apps: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        await conn.close()
