"""
Keycloak Status API for Ops-Center Admin UI
Provides endpoints for displaying Keycloak configuration and status
"""

import logging
import httpx
import os
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from keycloak_integration import (
    get_admin_token,
    KEYCLOAK_URL,
    KEYCLOAK_REALM,
    get_all_users
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/system/keycloak", tags=["keycloak-status"])

# Keycloak container name
KEYCLOAK_CONTAINER = "keycloak"


async def check_keycloak_container() -> Dict[str, Any]:
    """Check if Keycloak container is running"""
    try:
        import docker
        client = docker.from_env()

        try:
            container = client.containers.get(KEYCLOAK_CONTAINER)
            return {
                "running": container.status == "running",
                "status": container.status,
                "health": getattr(container.health, "status", "unknown") if hasattr(container, "health") else "unknown"
            }
        except docker.errors.NotFound:
            return {
                "running": False,
                "status": "not_found",
                "health": "unknown"
            }
    except Exception as e:
        logger.error(f"Error checking Keycloak container: {e}")
        return {
            "running": False,
            "status": "error",
            "health": "unknown"
        }


async def get_identity_providers() -> List[Dict[str, Any]]:
    """Get configured identity providers from Keycloak"""
    try:
        token = await get_admin_token()

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/identity-provider/instances",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 200:
                providers = response.json()

                # Format provider data
                formatted_providers = []
                for provider in providers:
                    formatted_providers.append({
                        "name": provider.get("alias", "").title(),
                        "alias": provider.get("alias"),
                        "enabled": provider.get("enabled", False),
                        "provider_id": provider.get("providerId"),
                        "link_only": provider.get("linkOnly", False),
                        "first_broker_login_flow": provider.get("firstBrokerLoginFlowAlias")
                    })

                return formatted_providers
            else:
                logger.error(f"Failed to fetch identity providers: {response.status_code}")
                return []

    except Exception as e:
        logger.error(f"Error fetching identity providers: {e}")
        return []


async def get_user_count_by_provider(provider_alias: str) -> int:
    """Get count of users using a specific identity provider"""
    try:
        # This would require querying federated identities
        # For now, return 0 as this requires more complex queries
        return 0
    except Exception as e:
        logger.error(f"Error getting user count for provider {provider_alias}: {e}")
        return 0


async def get_active_sessions_count() -> int:
    """Get count of active user sessions"""
    try:
        token = await get_admin_token()

        # Get all clients to find session counts
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/client-session-stats",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 200:
                session_stats = response.json()
                # Sum up active sessions across all clients
                total_sessions = sum(stat.get("active", 0) for stat in session_stats)
                return total_sessions
            else:
                return 0

    except Exception as e:
        logger.error(f"Error getting session count: {e}")
        return 0


async def get_oauth_clients() -> List[Dict[str, Any]]:
    """Get configured OAuth clients from Keycloak"""
    try:
        token = await get_admin_token()

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 200:
                all_clients = response.json()

                # Filter to only our application clients (not system clients)
                app_clients = []
                for client in all_clients:
                    client_id = client.get("clientId", "")

                    # Skip system/internal clients
                    if client_id.startswith("account") or client_id.startswith("admin") or \
                       client_id.startswith("broker") or client_id.startswith("realm") or \
                       client_id.startswith("security"):
                        continue

                    # Only include our application clients
                    if client_id in ["ops-center", "brigade", "center-deep", "open-webui"]:
                        app_clients.append({
                            "client_id": client_id,
                            "name": client.get("name", client_id),
                            "enabled": client.get("enabled", False),
                            "redirect_uris": client.get("redirectUris", []),
                            "web_origins": client.get("webOrigins", []),
                            "protocol": client.get("protocol", "openid-connect"),
                            "public_client": client.get("publicClient", False),
                            "service_accounts_enabled": client.get("serviceAccountsEnabled", False)
                        })

                return app_clients
            else:
                logger.error(f"Failed to fetch OAuth clients: {response.status_code}")
                return []

    except Exception as e:
        logger.error(f"Error fetching OAuth clients: {e}")
        return []


@router.get("/status")
async def get_keycloak_status():
    """
    Get Keycloak service status and configuration

    Returns:
        - Service status (running/stopped)
        - Realm information
        - User count
        - Active sessions
        - Configured identity providers
    """
    try:
        # Check container status
        container_info = await check_keycloak_container()

        if not container_info["running"]:
            return {
                "status": "stopped",
                "realm": KEYCLOAK_REALM,
                "admin_url": f"{KEYCLOAK_URL}/admin/{KEYCLOAK_REALM}/console",
                "error": "Keycloak container is not running"
            }

        # Get user count
        users = await get_all_users()
        user_count = len(users)

        # Get active sessions
        active_sessions = await get_active_sessions_count()

        # Get identity providers
        providers = await get_identity_providers()

        # For each provider, get user count (simplified for now)
        for provider in providers:
            provider["users"] = await get_user_count_by_provider(provider["alias"])

        return {
            "status": "running",
            "health": container_info.get("health", "unknown"),
            "realm": KEYCLOAK_REALM,
            "admin_url": f"{KEYCLOAK_URL}/admin/{KEYCLOAK_REALM}/console",
            "users": user_count,
            "active_sessions": active_sessions,
            "identity_providers": providers,
            "container_status": container_info["status"]
        }

    except Exception as e:
        logger.error(f"Error getting Keycloak status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get Keycloak status: {str(e)}")


@router.get("/clients")
async def get_clients():
    """
    List OAuth clients configured in Keycloak

    Returns:
        List of OAuth clients with their configuration
    """
    try:
        clients = await get_oauth_clients()

        # Add status based on enabled flag
        for client in clients:
            client["status"] = "active" if client["enabled"] else "inactive"

        return {
            "clients": clients,
            "total": len(clients)
        }

    except Exception as e:
        logger.error(f"Error getting OAuth clients: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get OAuth clients: {str(e)}")


@router.get("/api-credentials")
async def get_api_credentials():
    """
    Get service account credentials for Ops-Center API

    NOTE: This endpoint should be admin-only!
    Returns sensitive credential information.
    """
    try:
        # These should match what's in .env.auth
        return {
            "client_id": "ops-center-api",
            "client_secret": os.getenv("KEYCLOAK_API_CLIENT_SECRET", "your-client-secret"),
            "service_account": "ops-center-api",
            "permissions": ["manage-clients", "view-users", "manage-users"],
            "token_endpoint": f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token",
            "realm": KEYCLOAK_REALM
        }

    except Exception as e:
        logger.error(f"Error getting API credentials: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get API credentials: {str(e)}")


@router.get("/session-config")
async def get_session_config():
    """
    Get session configuration from Keycloak realm settings
    """
    try:
        token = await get_admin_token()

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 200:
                realm_data = response.json()

                return {
                    "sso_session_idle_timeout": realm_data.get("ssoSessionIdleTimeout", 1800),  # 30 min default
                    "sso_session_max_lifespan": realm_data.get("ssoSessionMaxLifespan", 36000),  # 10 hours default
                    "offline_session_idle_timeout": realm_data.get("offlineSessionIdleTimeout", 2592000),  # 30 days
                    "access_token_lifespan": realm_data.get("accessTokenLifespan", 300),  # 5 min
                    "remember_me": realm_data.get("rememberMe", True),
                    "login_lifespan": realm_data.get("accessCodeLifespan", 60)  # 1 min
                }
            else:
                logger.error(f"Failed to fetch realm settings: {response.status_code}")
                raise HTTPException(status_code=500, detail="Failed to fetch realm settings")

    except Exception as e:
        logger.error(f"Error getting session config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session config: {str(e)}")


@router.get("/ssl-status")
async def get_ssl_status():
    """
    Get SSL/TLS certificate status for Keycloak
    """
    try:
        # Check if using Cloudflare (based on EXTERNAL_PROTOCOL)
        external_protocol = os.getenv("EXTERNAL_PROTOCOL", "https")
        external_host = os.getenv("EXTERNAL_HOST", "your-domain.com")

        # Determine SSL mode
        if external_protocol == "https":
            ssl_mode = "Full" if "cloudflare" in os.getenv("DNS_PROVIDER", "").lower() else "Let's Encrypt"
        else:
            ssl_mode = "Disabled"

        return {
            "ssl_enabled": external_protocol == "https",
            "ssl_mode": ssl_mode,
            "certificate_provider": "Cloudflare" if "cloudflare" in os.getenv("DNS_PROVIDER", "").lower() else "Let's Encrypt",
            "domains": [
                f"auth.{external_host}",
                external_host
            ],
            "auto_renewal": True,
            "https_redirect": True
        }

    except Exception as e:
        logger.error(f"Error getting SSL status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get SSL status: {str(e)}")


@router.post("/test-connection")
async def test_keycloak_connection():
    """
    Test connection to Keycloak and verify admin credentials
    """
    try:
        # Try to get admin token
        token = await get_admin_token()

        if token:
            return {
                "success": True,
                "message": "Successfully connected to Keycloak",
                "realm": KEYCLOAK_REALM,
                "url": KEYCLOAK_URL
            }
        else:
            return {
                "success": False,
                "message": "Failed to obtain admin token",
                "realm": KEYCLOAK_REALM,
                "url": KEYCLOAK_URL
            }

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "realm": KEYCLOAK_REALM,
            "url": KEYCLOAK_URL
        }
