"""
My Apps API - Returns apps filtered by user's subscription tier and organization grants

Integrates with existing RBAC system:
- tier_features: Features granted by user's subscription tier
- org_features: Features explicitly granted to user's organization

User sees an app IF: (tier includes feature) OR (org has explicit grant for feature)
"""

import os
import sys
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import asyncpg

# Router configuration
router = APIRouter(prefix="/api/v1/my-apps", tags=["my-apps"])


# =============================================================================
# Pydantic Models
# =============================================================================

class AppResponse(BaseModel):
    """App available to user"""
    id: int
    name: str
    slug: str
    description: str
    icon_url: Optional[str]
    launch_url: str
    category: str
    feature_key: Optional[str]
    access_type: str  # 'tier_included', 'org_granted', 'premium_purchased', 'upgrade_required'


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
# Authentication Dependency
# =============================================================================

async def get_current_user_tier(request: Request) -> str:
    """
    Extract user's subscription tier from session cookies.
    Uses Redis session manager (same pattern as require_admin dependency).

    Returns:
        User's subscription tier (vip_founder, byok, managed)
        Defaults to 'managed' if not authenticated or tier not found

    Database tiers:
        - vip_founder: 4 features (chat, search, litellm, priority_support)
        - byok: 7 features (adds brigade, tts, stt)
        - managed: 11 features (adds bolt, billing, dedicated support)
    """
    # Add parent directory to path if needed
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    try:
        from redis_session import RedisSessionManager

        # Get session token from cookie
        session_token = request.cookies.get("session_token")
        if not session_token:
            # Not authenticated - return trial tier (limited access)
            return 'trial'

        # Get Redis connection info
        redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))

        # Initialize session manager
        sessions = RedisSessionManager(host=redis_host, port=redis_port)

        # Get session data
        if session_token not in sessions:
            # Session expired - return trial tier
            return 'trial'

        session_data = sessions[session_token]

        # Check for tier at root level (OAuth sessions) or nested under "user" key (legacy)
        tier = session_data.get("subscription_tier")
        if not tier:
            # Try legacy nested structure
            user = session_data.get("user", {})
            tier = user.get("subscription_tier") or user.get("tier")

        # If tier not set or invalid, try database fallback
        # Valid tiers: vip_founder, byok, managed, founder_friend, trial, starter, professional, enterprise
        valid_tiers = ['vip_founder', 'byok', 'managed', 'founder_friend', 'founder-friend', 'trial', 'starter', 'professional', 'enterprise', 'nda-autopilot', 'partnerpulse', 'm10_partner']
        if not tier or tier not in valid_tiers:
            # Try database fallback - get tier from user's organization
            # First try to get user's Keycloak sub (stored as zitadel_id in users table)
            keycloak_sub = session_data.get("sub") or session_data.get("user", {}).get("sub")

            import logging
            logger = logging.getLogger(__name__)

            # Also get user's email for fallback lookup
            user_email = session_data.get("email") or session_data.get("user", {}).get("email")

            if keycloak_sub or user_email:
                try:
                    conn = await get_db_connection()
                    try:
                        tier_row = None
                        user_id_to_update = None

                        # First, try lookup by zitadel_id (Keycloak sub)
                        if keycloak_sub:
                            tier_row = await conn.fetchrow("""
                                SELECT o.plan_tier, u.id as user_id
                                FROM users u
                                JOIN organization_members om ON u.id::text = om.user_id
                                JOIN organizations o ON om.org_id = o.id
                                WHERE u.zitadel_id = $1
                                ORDER BY om.is_default DESC, om.joined_at ASC
                                LIMIT 1
                            """, str(keycloak_sub))

                        # Fallback: lookup by email if zitadel_id lookup failed
                        if not tier_row and user_email:
                            logger.info(f"[MY-APPS] zitadel_id lookup failed, trying email fallback: {user_email}")
                            tier_row = await conn.fetchrow("""
                                SELECT o.plan_tier, u.id as user_id
                                FROM users u
                                JOIN organization_members om ON u.id::text = om.user_id
                                JOIN organizations o ON om.org_id = o.id
                                WHERE u.email = $1
                                ORDER BY om.is_default DESC, om.joined_at ASC
                                LIMIT 1
                            """, user_email)

                            # If found by email, update zitadel_id for future lookups
                            if tier_row and keycloak_sub:
                                user_id_to_update = tier_row['user_id']
                                await conn.execute(
                                    "UPDATE users SET zitadel_id = $1 WHERE id = $2",
                                    str(keycloak_sub), user_id_to_update
                                )
                                logger.info(f"[MY-APPS] Updated zitadel_id for user {user_email} to {keycloak_sub}")

                        if tier_row and tier_row['plan_tier']:
                            tier = tier_row['plan_tier']
                            logger.info(f"[MY-APPS] Tier from database lookup: {tier} for user {user_email or keycloak_sub}")
                    finally:
                        await conn.close()
                except Exception as db_error:
                    logger.warning(f"Database tier lookup failed: {db_error}")

            # If still no tier, default to trial (limited access until they subscribe)
            if not tier or tier not in valid_tiers:
                tier = 'trial'

        return tier

    except Exception as e:
        # On any error, default to trial tier (limited access)
        # Log warning but don't fail the request
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error extracting user tier from session: {e}")
        return 'trial'


# =============================================================================
# Helper Functions
# =============================================================================

def get_tier_level(tier_name: str) -> int:
    """Convert tier name to level for comparison"""
    tier_levels = {
        'trial': 1,
        'starter': 2,
        'professional': 3,
        'enterprise': 4
    }
    return tier_levels.get(tier_name.lower(), 0)


async def get_user_org_from_session(request: Request) -> Optional[str]:
    """
    Get user's current organization ID from session or database fallback.

    Returns:
        Organization ID (UUID string) or None if user has no org
    """
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    import logging
    logger = logging.getLogger(__name__)

    try:
        from redis_session import RedisSessionManager

        # Get session token from cookie
        session_token = request.cookies.get("session_token")
        if not session_token:
            return None

        # Get Redis connection info
        redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))

        # Initialize session manager
        sessions = RedisSessionManager(host=redis_host, port=redis_port)

        # Get session data
        if session_token not in sessions:
            return None

        session_data = sessions[session_token]

        # Try to get org_id from session (set by auth flow)
        org_id = session_data.get("org_id")
        if org_id:
            return org_id

        # Try nested user structure
        user = session_data.get("user", {})
        org_id = user.get("org_id")
        if org_id:
            return org_id

        # Database fallback: Look up user's org from organization_members
        # Get Keycloak sub from session (could be in 'sub' or nested 'user.sub')
        keycloak_sub = session_data.get("sub") or user.get("sub")

        if keycloak_sub:
            try:
                conn = await get_db_connection()
                try:
                    # First, look up our internal user_id from the Keycloak sub (zitadel_id)
                    # Then find their organization
                    org_row = await conn.fetchrow("""
                        SELECT om.org_id
                        FROM users u
                        JOIN organization_members om ON u.id::text = om.user_id
                        WHERE u.zitadel_id = $1
                        LIMIT 1
                    """, str(keycloak_sub))
                    if org_row:
                        org_id = str(org_row['org_id'])
                        logger.info(f"[MY-APPS] Found org_id {org_id} for Keycloak sub {keycloak_sub} via database fallback")
                        return org_id
                finally:
                    await conn.close()
            except Exception as db_error:
                logger.warning(f"Database org lookup failed for Keycloak sub {keycloak_sub}: {db_error}")

        return None

    except Exception as e:
        logger.warning(f"Error getting org from session: {e}")
        return None


async def get_org_features(org_id: str, conn) -> set:
    """
    Get all feature keys explicitly granted to an organization.

    Args:
        org_id: Organization UUID
        conn: Database connection

    Returns:
        Set of feature_key strings enabled for this org
    """
    if not org_id:
        return set()

    try:
        # Query org_features table for explicit feature grants
        feature_rows = await conn.fetch(
            "SELECT feature_key FROM org_features WHERE org_id = $1 AND enabled = TRUE",
            org_id
        )
        return {row['feature_key'] for row in feature_rows}
    except Exception as e:
        # Table might not exist yet - gracefully return empty set
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"org_features query failed (table may not exist): {e}")
        return set()


async def get_user_tier_features(user_tier: str, conn) -> set:
    """Get all app keys enabled for user's tier"""
    # Validate tier before database query
    valid_tiers = ['trial', 'starter', 'professional', 'enterprise', 'vip_founder', 'founder_friend', 'founder-friend', 'byok', 'managed', 'nda-autopilot', 'partnerpulse', 'm10_partner']
    if user_tier.lower() not in valid_tiers:
        raise HTTPException(status_code=400, detail=f"Invalid subscription tier: {user_tier}")

    # Get tier_id from subscription_tiers (using tier_code which matches Keycloak attribute)
    tier_row = await conn.fetchrow(
        "SELECT id FROM subscription_tiers WHERE tier_code = $1",
        user_tier.lower()  # tier_code is lowercase
    )

    if not tier_row:
        return set()

    tier_id = tier_row['id']

    # Get all enabled features for this tier from tier_features table
    feature_rows = await conn.fetch(
        "SELECT feature_key FROM tier_features WHERE tier_id = $1 AND enabled = TRUE",
        tier_id
    )

    return {row['feature_key'] for row in feature_rows}


async def get_combined_features(user_tier: str, org_id: Optional[str], conn) -> set:
    """
    Get all feature keys the user has access to.

    Combines:
    - Features from user's subscription tier (tier_features)
    - Features explicitly granted to user's organization (org_features)

    User sees an app IF: (tier includes feature) OR (org has explicit grant)

    Args:
        user_tier: User's subscription tier code
        org_id: User's current organization ID (may be None)
        conn: Database connection

    Returns:
        Set of all feature_key strings user has access to
    """
    # Get tier-based features
    tier_features = await get_user_tier_features(user_tier, conn)

    # Get org-based features (if user has an org)
    org_features = await get_org_features(org_id, conn)

    # Union of both sets - user sees app if EITHER grants access
    return tier_features.union(org_features)


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/authorized", response_model=List[AppResponse])
async def get_my_apps(request: Request, user_tier: str = Depends(get_current_user_tier)):
    """
    Get apps the current user is authorized to access based on their subscription tier
    and organization grants.

    Returns apps where:
    - User's tier includes the app's feature_key (tier_features table)
    - User's organization has explicit access grant (org_features table)
    - User has purchased the app separately (future: check user_add_ons table)
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[MY-APPS] User tier detected: {user_tier}")

    # Get user's current organization from session
    org_id = await get_user_org_from_session(request)
    logger.info(f"[MY-APPS] User org_id from session: {org_id}")

    conn = await get_db_connection()
    try:
        # User's tier is now extracted from session via dependency injection
        # Valid tiers: 'vip_founder', 'byok', 'managed' (defaults to 'managed')

        # Get tier-based features for determining access_type
        tier_features = await get_user_tier_features(user_tier, conn)
        logger.info(f"[MY-APPS] Tier features for {user_tier}: {tier_features}")

        # Get org-based features (if user has an org)
        org_features_set = await get_org_features(org_id, conn)
        if org_features_set:
            logger.info(f"[MY-APPS] Org features for {org_id}: {org_features_set}")

        # Combined features - user sees app if EITHER tier OR org grants access
        enabled_features = tier_features.union(org_features_set)
        logger.info(f"[MY-APPS] Combined enabled features: {enabled_features}")

        # Get all active apps
        apps_query = """
            SELECT id, name, slug, description, icon_url, launch_url,
                   category, feature_key, base_price, features
            FROM add_ons
            WHERE is_active = TRUE
            ORDER BY sort_order, name
        """
        app_rows = await conn.fetch(apps_query)
        logger.info(f"[MY-APPS] Fetched {len(app_rows)} apps from database")

        # Filter apps based on user's tier and org grants
        authorized_apps = []
        for app in app_rows:
            logger.info(f"[MY-APPS] Processing app: {dict(app).get('name')} (feature_key: {dict(app).get('feature_key')})")
            app_dict = dict(app)
            feature_key = app_dict.get('feature_key')

            # Skip apps without launch URLs
            if not app_dict.get('launch_url'):
                continue

            # Check if user has access and determine access_type
            access_type = None

            if feature_key:
                # Check if access comes from tier or org
                in_tier = feature_key in tier_features
                in_org = feature_key in org_features_set

                if in_tier:
                    # User's subscription tier includes this app
                    access_type = 'tier_included'
                elif in_org:
                    # User's org has explicit grant for this app
                    access_type = 'org_granted'
                else:
                    # User has no access - skip
                    continue
            elif app_dict['base_price'] == 0 and not feature_key:
                # Free app with no feature restriction
                access_type = 'tier_included'
            else:
                # App not included - skip it for now
                # (Later: check if user purchased it separately)
                continue

            authorized_apps.append({
                'id': app_dict['id'],
                'name': app_dict['name'],
                'slug': app_dict['slug'],
                'description': app_dict['description'] or '',
                'icon_url': app_dict['icon_url'],
                'launch_url': app_dict['launch_url'],
                'category': app_dict['category'] or 'general',
                'feature_key': feature_key,
                'access_type': access_type,
                'features': app_dict.get('features') or {}
            })
            logger.info(f"[MY-APPS] Added app {app_dict['name']} to authorized list (access: {access_type})")

        logger.info(f"[MY-APPS] Returning {len(authorized_apps)} authorized apps")
        return authorized_apps

    except asyncpg.PostgresError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )
    finally:
        await conn.close()


@router.get("/marketplace", response_model=List[AppResponse])
async def get_marketplace_apps(request: Request, user_tier: str = Depends(get_current_user_tier)):
    """
    Get apps available for purchase (not included in user's current tier or org).

    Returns:
    - Premium apps user can purchase
    - Apps requiring tier upgrade
    """
    # Get user's current organization from session
    org_id = await get_user_org_from_session(request)

    conn = await get_db_connection()
    try:
        # User's tier is now extracted from session via dependency injection

        # Get combined features (tier + org) - user already has access to these
        enabled_features = await get_combined_features(user_tier, org_id, conn)

        # Get all active apps
        apps_query = """
            SELECT id, name, slug, description, icon_url, launch_url,
                   category, feature_key, base_price, billing_type
            FROM add_ons
            WHERE is_active = TRUE
            ORDER BY base_price DESC, name
        """
        app_rows = await conn.fetch(apps_query)

        # Filter to apps NOT in user's tier
        marketplace_apps = []
        for app in app_rows:
            app_dict = dict(app)
            feature_key = app_dict.get('feature_key')

            # Skip apps without launch URLs
            if not app_dict.get('launch_url'):
                continue

            # Skip apps user already has access to
            if feature_key and feature_key in enabled_features:
                continue

            # Determine access type
            access_type = 'premium_purchase' if app_dict['base_price'] > 0 else 'upgrade_required'

            marketplace_apps.append({
                'id': app_dict['id'],
                'name': app_dict['name'],
                'slug': app_dict['slug'],
                'description': app_dict['description'] or '',
                'icon_url': app_dict['icon_url'],
                'launch_url': app_dict['launch_url'],
                'category': app_dict['category'] or 'general',
                'feature_key': feature_key,
                'access_type': access_type,
                'price': float(app_dict['base_price']) if app_dict['base_price'] else 0,
                'billing_type': app_dict.get('billing_type', 'monthly')
            })

        return marketplace_apps

    except asyncpg.PostgresError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )
    finally:
        await conn.close()
