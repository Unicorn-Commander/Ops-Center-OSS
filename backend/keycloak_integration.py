"""
Keycloak Integration for UC-1 Pro
Provides admin token management and user operations
"""

import httpx
import os
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Keycloak Configuration
# NOTE: use `(os.getenv(...) or default)` so an env var that is SET-but-EMPTY
# still falls back to the sane default (a bare getenv default does not).
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL") or "https://auth.unicorncommander.ai"
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM") or "master"
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID") or "admin-cli"
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
KEYCLOAK_ADMIN_USERNAME = os.getenv("KEYCLOAK_ADMIN_USER") or os.getenv("KEYCLOAK_ADMIN_USERNAME") or "admin"
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "")

# Token cache
_admin_token_cache = {
    "token": None,
    "expires_at": None
}


async def get_admin_token() -> str:
    """
    Get Keycloak admin access token
    Uses cached token if still valid
    """
    # Check if cached token is still valid
    if _admin_token_cache["token"] and _admin_token_cache["expires_at"]:
        if datetime.now() < _admin_token_cache["expires_at"]:
            return _admin_token_cache["token"]

    # Request new token from master realm (admin user exists in master, not uchub)
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
                data={
                    "grant_type": "password",
                    "client_id": KEYCLOAK_CLIENT_ID,
                    "username": KEYCLOAK_ADMIN_USERNAME,
                    "password": KEYCLOAK_ADMIN_PASSWORD
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0
            )

            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 300)  # Default 5 minutes

                # Cache token with 30 second buffer before expiration
                _admin_token_cache["token"] = access_token
                _admin_token_cache["expires_at"] = datetime.now() + timedelta(seconds=expires_in - 30)

                logger.info("Successfully obtained Keycloak admin token")
                return access_token
            else:
                logger.error(f"Failed to get admin token: {response.status_code} - {response.text}")
                raise Exception(f"Failed to authenticate with Keycloak: {response.status_code}")

    except Exception as e:
        logger.error(f"Error getting admin token: {e}")
        raise


# Keycloak's own PostgreSQL database (read-only fallback). Used to list users
# when the admin REST API is unavailable on this node (e.g. the admin-cli
# password is not provisioned here). The Keycloak admin REST API remains the
# primary path; this fallback is read-only and never used for writes.
KEYCLOAK_DB_HOST = os.getenv("KEYCLOAK_DB_HOST") or "keycloak-db"
KEYCLOAK_DB_PORT = int(os.getenv("KEYCLOAK_DB_PORT") or "5432")
KEYCLOAK_DB_NAME = os.getenv("KEYCLOAK_DB_NAME") or "keycloak"
KEYCLOAK_DB_USER = os.getenv("KEYCLOAK_DB_USER") or "keycloak"
KEYCLOAK_DB_PASSWORD = os.getenv("KEYCLOAK_DB_PASSWORD") or "keycloak_secure_password_2025"


async def get_all_users_from_db() -> List[Dict[str, Any]]:
    """
    Read users for the configured realm directly from Keycloak's PostgreSQL DB.

    Returns dicts shaped like the Keycloak admin REST API (id, username, email,
    firstName, lastName, enabled, emailVerified, createdTimestamp, attributes,
    realmRoles) so existing callers work unchanged. Read-only fallback only.
    """
    import asyncpg

    conn = await asyncpg.connect(
        host=KEYCLOAK_DB_HOST,
        port=KEYCLOAK_DB_PORT,
        user=KEYCLOAK_DB_USER,
        password=KEYCLOAK_DB_PASSWORD,
        database=KEYCLOAK_DB_NAME,
    )
    try:
        user_rows = await conn.fetch(
            """
            SELECT u.id, u.username, u.email, u.first_name, u.last_name,
                   u.enabled, u.email_verified, u.created_timestamp
            FROM user_entity u
            JOIN realm r ON u.realm_id = r.id
            WHERE r.name = $1
            ORDER BY u.created_timestamp DESC
            """,
            KEYCLOAK_REALM,
        )

        user_ids = [row["id"] for row in user_rows]
        attrs_by_user: Dict[str, Dict[str, List[str]]] = {}
        roles_by_user: Dict[str, List[str]] = {}

        if user_ids:
            attr_rows = await conn.fetch(
                """
                SELECT user_id, name, value
                FROM user_attribute
                WHERE user_id = ANY($1::varchar[])
                """,
                user_ids,
            )
            for ar in attr_rows:
                attrs_by_user.setdefault(ar["user_id"], {}).setdefault(ar["name"], []).append(ar["value"])

            role_rows = await conn.fetch(
                """
                SELECT urm.user_id, kr.name AS role_name
                FROM user_role_mapping urm
                JOIN keycloak_role kr ON urm.role_id = kr.id
                WHERE urm.user_id = ANY($1::varchar[])
                """,
                user_ids,
            )
            for rr in role_rows:
                roles_by_user.setdefault(rr["user_id"], []).append(rr["role_name"])

        users: List[Dict[str, Any]] = []
        for row in user_rows:
            uid = row["id"]
            users.append({
                "id": uid,
                "username": row["username"],
                "email": row["email"],
                "firstName": row["first_name"] or "",
                "lastName": row["last_name"] or "",
                "enabled": bool(row["enabled"]),
                "emailVerified": bool(row["email_verified"]),
                "createdTimestamp": row["created_timestamp"],
                "attributes": attrs_by_user.get(uid, {}),
                "realmRoles": roles_by_user.get(uid, []),
            })

        logger.info(f"Fetched {len(users)} users from Keycloak DB (realm={KEYCLOAK_REALM})")
        return users
    finally:
        await conn.close()


async def get_all_users() -> List[Dict[str, Any]]:
    """
    Fetch all users from Keycloak.

    Primary path: the Keycloak admin REST API. If that is unavailable on this
    node (e.g. admin credentials not provisioned) it falls back to a read-only
    query against Keycloak's PostgreSQL database so the admin UI still shows
    real users.
    """
    try:
        token = await get_admin_token()

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users",
                headers={"Authorization": f"Bearer {token}"},
                params={"max": 1000},
                timeout=10.0
            )

            if response.status_code == 200:
                users = response.json()
                logger.info(f"Successfully fetched {len(users)} users from Keycloak")
                return users
            else:
                logger.error(f"Failed to fetch users: {response.status_code} - {response.text}")

    except Exception as e:
        logger.error(f"Error fetching users from Keycloak REST API: {e}")

    # Fallback: read users directly from Keycloak's database (read-only).
    try:
        return await get_all_users_from_db()
    except Exception as db_err:
        logger.error(f"Keycloak DB fallback for user list failed: {db_err}")
        return []


async def _get_user_from_db(field: str, value: str) -> Optional[Dict[str, Any]]:
    """
    Read a single user from Keycloak's database by 'email', 'username', or 'id'.
    Read-only fallback for when the admin REST API is unavailable on this node.
    """
    if field not in ("email", "username", "id"):
        return None

    try:
        all_users = await get_all_users_from_db()
    except Exception as db_err:
        logger.error(f"Keycloak DB fallback lookup ({field}) failed: {db_err}")
        return None

    needle = (value or "").lower() if field != "id" else value
    for user in all_users:
        candidate = user.get(field)
        if candidate is None:
            continue
        if field == "id":
            if candidate == value:
                return user
        elif candidate.lower() == needle:
            return user
    return None


async def get_realm_session_config_from_db() -> Optional[Dict[str, Any]]:
    """
    Read the realm's session/token settings directly from Keycloak's database.

    Read-only fallback for when the admin REST API is unavailable on this node.
    Returns a dict using the Keycloak admin-API camelCase keys so callers that
    expect the REST shape work unchanged.
    """
    import asyncpg

    conn = await asyncpg.connect(
        host=KEYCLOAK_DB_HOST,
        port=KEYCLOAK_DB_PORT,
        user=KEYCLOAK_DB_USER,
        password=KEYCLOAK_DB_PASSWORD,
        database=KEYCLOAK_DB_NAME,
    )
    try:
        row = await conn.fetchrow(
            """
            SELECT sso_idle_timeout, sso_max_lifespan, offline_session_idle_timeout,
                   access_token_lifespan, access_code_lifespan, remember_me, login_lifespan
            FROM realm
            WHERE name = $1
            """,
            KEYCLOAK_REALM,
        )
        if not row:
            return None
        return {
            "ssoSessionIdleTimeout": row["sso_idle_timeout"],
            "ssoSessionMaxLifespan": row["sso_max_lifespan"],
            "offlineSessionIdleTimeout": row["offline_session_idle_timeout"],
            "accessTokenLifespan": row["access_token_lifespan"],
            "rememberMe": bool(row["remember_me"]),
            "accessCodeLifespan": row["access_code_lifespan"],
        }
    finally:
        await conn.close()


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Fetch specific user by email from Keycloak
    """
    try:
        token = await get_admin_token()

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users",
                headers={"Authorization": f"Bearer {token}"},
                params={"email": email, "exact": "true"},
                timeout=10.0
            )

            if response.status_code == 200:
                users = response.json()
                if users:
                    logger.info(f"Found user: {email}")
                    return users[0]
                else:
                    logger.warning(f"No user found with email: {email}")
                    return None
            else:
                logger.error(f"Failed to fetch user {email}: {response.status_code}")

    except Exception as e:
        logger.error(f"Error fetching user by email (REST): {e}")

    # Read-only DB fallback when the admin REST API is unavailable.
    return await _get_user_from_db("email", email)


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Fetch specific user by username from Keycloak
    """
    try:
        token = await get_admin_token()

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users",
                headers={"Authorization": f"Bearer {token}"},
                params={"username": username, "exact": "true"},
                timeout=10.0
            )

            if response.status_code == 200:
                users = response.json()
                if users:
                    logger.info(f"Found user: {username}")
                    return users[0]
                else:
                    logger.warning(f"No user found with username: {username}")
                    return None
            else:
                logger.error(f"Failed to fetch user {username}: {response.status_code}")

    except Exception as e:
        logger.error(f"Error fetching user by username (REST): {e}")

    # Read-only DB fallback when the admin REST API is unavailable.
    return await _get_user_from_db("username", username)


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch specific user by Keycloak user ID
    """
    try:
        token = await get_admin_token()

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 200:
                user = response.json()
                logger.info(f"Found user by ID: {user_id}")
                return user
            elif response.status_code == 404:
                logger.warning(f"No user found with ID: {user_id}")
                return None
            else:
                logger.error(f"Failed to fetch user {user_id}: {response.status_code}")

    except Exception as e:
        logger.error(f"Error fetching user by ID (REST): {e}")

    # Read-only DB fallback when the admin REST API is unavailable.
    return await _get_user_from_db("id", user_id)


async def update_user_attributes(email: str, attributes: Dict[str, List[str]]) -> bool:
    """
    Update user attributes in Keycloak
    Attributes should be in format: {"key": ["value"]} (Keycloak expects arrays)
    """
    try:
        # Get user first
        user = await get_user_by_email(email)
        if not user:
            logger.error(f"User not found: {email}")
            return False

        user_id = user.get("id")
        token = await get_admin_token()

        # Get existing attributes
        existing_attrs = user.get("attributes", {})

        # Merge with new attributes
        updated_attrs = {**existing_attrs, **attributes}

        # Update user
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.put(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={"attributes": updated_attrs},
                timeout=10.0
            )

            if response.status_code == 204:  # Keycloak returns 204 No Content on success
                logger.info(f"Successfully updated attributes for user: {email}")
                return True
            else:
                logger.error(f"Failed to update user attributes: {response.status_code} - {response.text}")
                return False

    except Exception as e:
        logger.error(f"Error updating user attributes: {e}")
        return False


async def create_user(email: str, username: str, first_name: str = "", last_name: str = "",
                     attributes: Dict[str, List[str]] = None, email_verified: bool = True) -> Optional[str]:
    """
    Create a new user in Keycloak
    Returns user ID on success, None on failure
    """
    try:
        token = await get_admin_token()

        user_data = {
            "email": email,
            "username": username,
            "enabled": True,
            "emailVerified": email_verified,
            "firstName": first_name,
            "lastName": last_name,
            "attributes": attributes or {}
        }

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=user_data,
                timeout=10.0
            )

            if response.status_code == 201:
                # Extract user ID from Location header
                location = response.headers.get("Location", "")
                user_id = location.split("/")[-1] if location else None
                logger.info(f"Successfully created user: {email} (ID: {user_id})")
                return user_id
            else:
                logger.error(f"Failed to create user: {response.status_code} - {response.text}")
                return None

    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None


async def delete_user(email: str) -> bool:
    """
    Delete a user from Keycloak
    """
    try:
        # Get user first
        user = await get_user_by_email(email)
        if not user:
            logger.error(f"User not found: {email}")
            return False

        user_id = user.get("id")
        token = await get_admin_token()

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.delete(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 204:
                logger.info(f"Successfully deleted user: {email}")
                return True
            else:
                logger.error(f"Failed to delete user: {response.status_code} - {response.text}")
                return False

    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return False


async def get_user_groups(email: str) -> List[str]:
    """
    Get list of groups a user belongs to
    """
    try:
        user = await get_user_by_email(email)
        if not user:
            return []

        user_id = user.get("id")
        token = await get_admin_token()

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/groups",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 200:
                groups = response.json()
                return [group.get("name") for group in groups]
            else:
                logger.error(f"Failed to get user groups: {response.status_code}")
                return []

    except Exception as e:
        logger.error(f"Error getting user groups: {e}")
        return []


# Tier-specific helper functions

def _get_attr_value(attrs: Dict, key: str, default: Any = None) -> Any:
    """
    Get attribute value from Keycloak attributes dict.
    Keycloak stores attributes as arrays, so extract first element.
    """
    value = attrs.get(key, [default])
    if isinstance(value, list):
        return value[0] if value else default
    return value


async def get_user_tier_info(email: str) -> Dict[str, Any]:
    """
    Get user's subscription tier and usage information.

    Returns:
        Dictionary with tier info:
        {
            "user_id": str,
            "username": str,
            "email": str,
            "subscription_tier": "trial|starter|professional|enterprise",
            "subscription_status": "active|inactive|cancelled",
            "api_calls_used": int,
            "api_calls_reset_date": "YYYY-MM-DD",
            "stripe_customer_id": str or None,
            "subscription_start_date": str or None,
            "subscription_end_date": str or None
        }
    """
    user = await get_user_by_email(email)

    if not user:
        # Return default trial tier for unknown users
        return {
            "user_id": None,
            "username": None,
            "email": email,
            "subscription_tier": "trial",
            "subscription_status": "active",
            "api_calls_used": 0,
            "api_calls_reset_date": datetime.utcnow().date().isoformat(),
            "stripe_customer_id": None,
            "subscription_start_date": None,
            "subscription_end_date": None,
        }

    # Extract attributes (Keycloak stores as arrays)
    attrs = user.get("attributes", {})

    return {
        "user_id": user.get("id"),
        "username": user.get("username"),
        "email": user.get("email"),
        "subscription_tier": _get_attr_value(attrs, "subscription_tier", "trial"),
        "subscription_status": _get_attr_value(attrs, "subscription_status", "active"),
        "api_calls_used": int(_get_attr_value(attrs, "api_calls_used", "0")),
        "api_calls_reset_date": _get_attr_value(
            attrs,
            "api_calls_reset_date",
            datetime.utcnow().date().isoformat()
        ),
        "stripe_customer_id": _get_attr_value(attrs, "stripe_customer_id"),
        "subscription_start_date": _get_attr_value(attrs, "subscription_start_date"),
        "subscription_end_date": _get_attr_value(attrs, "subscription_end_date"),
    }


async def increment_usage(email: str, current_usage: int = None) -> bool:
    """
    Increment user's API usage counter.
    Handles daily reset automatically.

    Args:
        email: User's email address
        current_usage: Current usage count (if known), otherwise fetches from Keycloak

    Returns:
        True if successful, False otherwise
    """
    # Get current tier info
    tier_info = await get_user_tier_info(email)

    if not tier_info.get("user_id"):
        logger.warning(f"Cannot increment usage: user not found ({email})")
        return False

    # Get current usage and reset date
    if current_usage is None:
        current_usage = tier_info.get("api_calls_used", 0)

    reset_date = tier_info.get("api_calls_reset_date")
    today = datetime.utcnow().date().isoformat()

    # Check if we need to reset counter (new day)
    if reset_date != today:
        # New day - reset counter
        new_usage = 1
        logger.info(f"Daily usage reset for {email}")
    else:
        # Increment counter
        new_usage = current_usage + 1

    # Update attributes (Keycloak expects arrays)
    return await update_user_attributes(email, {
        "api_calls_used": [str(new_usage)],
        "api_calls_reset_date": [today],
    })


async def reset_usage(email: str) -> bool:
    """
    Reset user's API usage counter to 0.
    Useful for testing or manual resets.
    """
    today = datetime.utcnow().date().isoformat()
    return await update_user_attributes(email, {
        "api_calls_used": ["0"],
        "api_calls_reset_date": [today],
    })


async def set_subscription_tier(
    email: str,
    tier: str,
    status: str = "active"
) -> bool:
    """
    Set user's subscription tier.

    Args:
        email: User's email address
        tier: Tier name (trial, starter, professional, enterprise)
        status: Subscription status (active, inactive, cancelled)

    Returns:
        True if successful, False otherwise
    """
    valid_tiers = ["trial", "free", "starter", "professional", "enterprise"]
    if tier not in valid_tiers:
        logger.error(f"Invalid tier: {tier}. Must be one of {valid_tiers}")
        return False

    return await update_user_attributes(email, {
        "subscription_tier": [tier],
        "subscription_status": [status],
    })


async def set_user_password(user_id: str, password: str, temporary: bool = False) -> bool:
    """
    Set password for a Keycloak user.

    Args:
        user_id: Keycloak user ID
        password: New password
        temporary: If True, user must change password on first login

    Returns:
        True if successful, False otherwise
    """
    try:
        token = await get_admin_token()

        password_data = {
            "type": "password",
            "value": password,
            "temporary": temporary
        }

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.put(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/reset-password",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=password_data,
                timeout=10.0
            )

            if response.status_code == 204:
                logger.info(f"Successfully set password for user ID: {user_id}")
                return True
            else:
                logger.error(f"Failed to set password: {response.status_code} - {response.text}")
                return False

    except Exception as e:
        logger.error(f"Error setting user password: {e}")
        return False


async def get_current_user_id() -> Optional[str]:
    """
    Get the current authenticated user's Keycloak ID from request context.

    This function is designed to be used as a FastAPI dependency:

    Example:
        @router.get("/me")
        async def get_me(user_id: str = Depends(get_current_user_id)):
            return {"user_id": user_id}

    Note: This is a placeholder implementation. In production, you should:
    1. Use FastAPI's Security dependencies (OAuth2PasswordBearer)
    2. Validate JWT tokens from request headers
    3. Extract user_id from token claims

    For now, this returns None to indicate the feature needs proper OAuth2 integration.

    Returns:
        Keycloak user ID of authenticated user, or None if not authenticated
    """
    # TODO: Implement proper JWT token validation and user ID extraction
    # This requires:
    # 1. Extract Authorization header from FastAPI Request
    # 2. Validate JWT token against Keycloak public keys
    # 3. Parse token claims to get user_id (sub claim)
    # 4. Return user_id

    logger.warning(
        "get_current_user_id() called but not fully implemented. "
        "This needs OAuth2 token validation. Returning None."
    )
    return None


# ============================================================================
# TWO-FACTOR AUTHENTICATION (2FA) MANAGEMENT
# ============================================================================


async def get_user_credentials(user_id: str) -> List[Dict[str, Any]]:
    """
    Get user's credentials from Keycloak.
    This includes TOTP secrets, WebAuthn keys, passwords, etc.

    Returns:
        List of credential objects:
        [
            {
                "id": "cred-id",
                "type": "otp" | "webauthn" | "password",
                "userLabel": "Google Authenticator",
                "createdDate": 1698765432000
            }
        ]
    """
    try:
        token = await get_admin_token()

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/credentials",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 200:
                credentials = response.json()
                logger.info(f"Retrieved {len(credentials)} credentials for user {user_id}")
                return credentials
            else:
                logger.error(f"Failed to get credentials: {response.status_code} - {response.text}")
                return []

    except Exception as e:
        logger.error(f"Error getting user credentials: {e}")
        return []


async def remove_user_credential(user_id: str, credential_id: str) -> bool:
    """
    Remove a specific credential from user.
    Used for resetting 2FA (removing TOTP or WebAuthn credentials).

    Args:
        user_id: Keycloak user ID
        credential_id: ID of credential to remove

    Returns:
        True if successful, False otherwise
    """
    try:
        token = await get_admin_token()

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.delete(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/credentials/{credential_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 204:
                logger.info(f"Successfully removed credential {credential_id} for user {user_id}")
                return True
            else:
                logger.error(f"Failed to remove credential: {response.status_code} - {response.text}")
                return False

    except Exception as e:
        logger.error(f"Error removing credential: {e}")
        return False


async def get_user_2fa_status(user_id: str) -> Dict[str, Any]:
    """
    Get comprehensive 2FA status for a user.

    Returns:
        {
            "user_id": str,
            "username": str,
            "email": str,
            "two_factor_enabled": bool,
            "two_factor_methods": [
                {
                    "id": str,
                    "type": "otp" | "webauthn",
                    "label": str,
                    "created_date": str (ISO format)
                }
            ],
            "setup_pending": bool,  # If CONFIGURE_TOTP in requiredActions
            "last_used": str or None  # Not available from Keycloak API
        }
    """
    try:
        # Get user details
        user = await get_user_by_id(user_id)
        if not user:
            return {
                "error": "User not found",
                "user_id": user_id,
                "two_factor_enabled": False
            }

        # Get user's credentials
        credentials = await get_user_credentials(user_id)

        # Filter for 2FA credentials (OTP and WebAuthn)
        two_factor_methods = []
        for cred in credentials:
            if cred.get("type") in ["otp", "webauthn"]:
                # Convert timestamp to ISO format
                created_timestamp = cred.get("createdDate", 0)
                created_date = datetime.fromtimestamp(created_timestamp / 1000).isoformat() if created_timestamp else None

                two_factor_methods.append({
                    "id": cred.get("id"),
                    "type": cred.get("type"),
                    "label": cred.get("userLabel", "Unnamed Device"),
                    "created_date": created_date
                })

        # Check if user has pending 2FA setup
        required_actions = user.get("requiredActions", [])
        setup_pending = "CONFIGURE_TOTP" in required_actions

        return {
            "user_id": user_id,
            "username": user.get("username"),
            "email": user.get("email"),
            "two_factor_enabled": len(two_factor_methods) > 0,
            "two_factor_methods": two_factor_methods,
            "setup_pending": setup_pending,
            "last_used": None  # Not available from Keycloak API
        }

    except Exception as e:
        logger.error(f"Error getting 2FA status: {e}")
        return {
            "error": str(e),
            "user_id": user_id,
            "two_factor_enabled": False
        }


async def send_account_action_email(
    user_id: str,
    actions: List[str],
    lifespan: int = 43200,
    client_id: Optional[str] = None,
    redirect_uri: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send a Keycloak "required actions" email to a user (server-side, no password
    ever leaves the system). This is the realm-native self-service primitive:

      - ["UPDATE_PASSWORD"]               -> "set / reset your password" link
      - ["VERIFY_EMAIL"]                  -> "verify your email" link
      - ["UPDATE_PASSWORD","VERIFY_EMAIL"] -> onboarding: set password + verify

    Delivery uses the realm's configured SMTP (Postmark) and templates. Returns a
    status dict; never raises into the caller.

    Args:
        user_id:      Keycloak user UUID
        actions:      list of KC required-action ids (see above)
        lifespan:     link validity in seconds (default 12h; onboarding wants longer)
        client_id:    optional OIDC client to land in after the action completes
        redirect_uri: optional post-action redirect (must be a valid redirect URI
                      for client_id) — both omitted => KC's generic info page
    """
    if not user_id or not actions:
        return {"success": False, "user_id": user_id, "message": "user_id and actions required"}
    try:
        token = await get_admin_token()
        params: Dict[str, Any] = {"lifespan": lifespan}
        if client_id:
            params["client_id"] = client_id
        if redirect_uri:
            params["redirect_uri"] = redirect_uri

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.put(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/execute-actions-email",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=actions,
                params=params,
                timeout=15.0,
            )
        if response.status_code == 204:
            logger.info(f"Sent account-action email {actions} to user {user_id}")
            return {"success": True, "user_id": user_id, "actions": actions, "message": "Email sent"}
        logger.error(f"Failed to send account-action email to {user_id}: {response.status_code} - {response.text}")
        return {
            "success": False, "user_id": user_id, "actions": actions,
            "status_code": response.status_code,
            "message": f"Keycloak returned {response.status_code} (check realm SMTP config)",
        }
    except Exception as e:
        logger.error(f"Error sending account-action email to {user_id}: {e}")
        return {"success": False, "user_id": user_id, "message": str(e)}


async def enforce_user_2fa(user_id: str, method: str = "email", lifespan: int = 86400) -> Dict[str, Any]:
    """
    Enforce 2FA for a user.

    Args:
        user_id: Keycloak user ID
        method: "email" (send setup email) or "immediate" (require on next login)
        lifespan: Email link validity in seconds (default 24 hours)

    Returns:
        {
            "success": bool,
            "user_id": str,
            "action_taken": str,
            "message": str
        }
    """
    try:
        # Get user to check if 2FA already enabled
        status = await get_user_2fa_status(user_id)
        if status.get("two_factor_enabled"):
            return {
                "success": True,
                "user_id": user_id,
                "action_taken": "none",
                "message": "User already has 2FA enabled"
            }

        token = await get_admin_token()

        if method == "email":
            # Send execute actions email with CONFIGURE_TOTP action
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.put(
                    f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/execute-actions-email",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json=["CONFIGURE_TOTP"],
                    params={"lifespan": lifespan},
                    timeout=10.0
                )

                if response.status_code == 204:
                    logger.info(f"Sent 2FA setup email to user {user_id}")
                    return {
                        "success": True,
                        "user_id": user_id,
                        "action_taken": "email_sent",
                        "message": "2FA setup email sent. User must configure 2FA via link in email."
                    }
                else:
                    logger.error(f"Failed to send 2FA email: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "user_id": user_id,
                        "action_taken": "none",
                        "message": f"Failed to send email: {response.status_code}"
                    }

        elif method == "immediate":
            # Add CONFIGURE_TOTP to required actions
            user = await get_user_by_id(user_id)
            required_actions = user.get("requiredActions", [])

            if "CONFIGURE_TOTP" not in required_actions:
                required_actions.append("CONFIGURE_TOTP")

                async with httpx.AsyncClient(verify=False) as client:
                    response = await client.put(
                        f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json"
                        },
                        json={"requiredActions": required_actions},
                        timeout=10.0
                    )

                    if response.status_code == 204:
                        logger.info(f"Set CONFIGURE_TOTP required action for user {user_id}")
                        return {
                            "success": True,
                            "user_id": user_id,
                            "action_taken": "required_action_set",
                            "message": "User will be prompted to setup 2FA on next login."
                        }
                    else:
                        logger.error(f"Failed to set required action: {response.status_code}")
                        return {
                            "success": False,
                            "user_id": user_id,
                            "action_taken": "none",
                            "message": f"Failed to set required action: {response.status_code}"
                        }
            else:
                return {
                    "success": True,
                    "user_id": user_id,
                    "action_taken": "none",
                    "message": "CONFIGURE_TOTP already in required actions"
                }

        else:
            return {
                "success": False,
                "user_id": user_id,
                "action_taken": "none",
                "message": f"Invalid method: {method}. Must be 'email' or 'immediate'."
            }

    except Exception as e:
        logger.error(f"Error enforcing 2FA: {e}")
        return {
            "success": False,
            "user_id": user_id,
            "action_taken": "none",
            "message": f"Error: {str(e)}"
        }


async def reset_user_2fa(user_id: str, require_reconfigure: bool = True) -> Dict[str, Any]:
    """
    Reset user's 2FA by removing all OTP and WebAuthn credentials.

    Args:
        user_id: Keycloak user ID
        require_reconfigure: If True, add CONFIGURE_TOTP to requiredActions

    Returns:
        {
            "success": bool,
            "user_id": str,
            "credentials_removed": List[str],  # IDs of removed credentials
            "required_action_set": bool,
            "message": str
        }
    """
    try:
        # Get user's credentials
        credentials = await get_user_credentials(user_id)

        # Filter for 2FA credentials
        two_factor_creds = [c for c in credentials if c.get("type") in ["otp", "webauthn"]]

        if not two_factor_creds:
            return {
                "success": True,
                "user_id": user_id,
                "credentials_removed": [],
                "required_action_set": False,
                "message": "No 2FA credentials found for user"
            }

        # Remove each 2FA credential
        removed_cred_ids = []
        for cred in two_factor_creds:
            cred_id = cred.get("id")
            if await remove_user_credential(user_id, cred_id):
                removed_cred_ids.append(cred_id)
            else:
                logger.warning(f"Failed to remove credential {cred_id}")

        # Optionally require reconfiguration
        required_action_set = False
        if require_reconfigure:
            result = await enforce_user_2fa(user_id, method="immediate")
            required_action_set = result.get("success", False)

        logger.info(f"Reset 2FA for user {user_id}: removed {len(removed_cred_ids)} credentials")

        return {
            "success": True,
            "user_id": user_id,
            "credentials_removed": removed_cred_ids,
            "required_action_set": required_action_set,
            "message": f"Successfully removed {len(removed_cred_ids)} 2FA credential(s)"
        }

    except Exception as e:
        logger.error(f"Error resetting 2FA: {e}")
        return {
            "success": False,
            "user_id": user_id,
            "credentials_removed": [],
            "required_action_set": False,
            "message": f"Error: {str(e)}"
        }


async def logout_user_sessions(user_id: str) -> bool:
    """
    Logout all sessions for a user.
    Useful after 2FA reset to force re-authentication.

    Args:
        user_id: Keycloak user ID

    Returns:
        True if successful, False otherwise
    """
    try:
        token = await get_admin_token()

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/logout",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 204:
                logger.info(f"Successfully logged out all sessions for user {user_id}")
                return True
            else:
                logger.error(f"Failed to logout user sessions: {response.status_code}")
                return False

    except Exception as e:
        logger.error(f"Error logging out user sessions: {e}")
        return False
