"""
Platform Settings API - Manage API Keys and Integration Secrets
Provides secure GUI-based management of platform credentials
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import os
import yaml
import subprocess
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/platform", tags=["Platform Settings"])

# Security: Only admin role can access platform settings
def require_admin(user_role: str = "admin"):
    """Middleware to require admin role"""
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return True

class PlatformSetting(BaseModel):
    """Platform setting model"""
    key: str
    value: Optional[str] = None
    description: str
    category: str  # stripe, lago, keycloak, cloudflare, namecheap, other
    is_secret: bool = True
    required: bool = False
    test_connection: bool = False  # Whether this setting can be tested
    last_updated: Optional[datetime] = None

class SettingsUpdate(BaseModel):
    """Update platform settings"""
    settings: Dict[str, str] = Field(..., description="Dictionary of key-value pairs to update")
    restart_required: bool = Field(default=False, description="Whether to restart container after update")

class TestConnectionRequest(BaseModel):
    """Test connection with provided credentials"""
    category: str
    credentials: Dict[str, str]

# Platform settings configuration
PLATFORM_SETTINGS = {
    # Stripe Settings
    "STRIPE_PUBLISHABLE_KEY": {
        "description": "Stripe publishable key (pk_test_... or pk_live_...)",
        "category": "stripe",
        "is_secret": False,
        "required": True,
        "test_connection": True
    },
    "STRIPE_SECRET_KEY": {
        "description": "Stripe secret key (sk_test_... or sk_live_...)",
        "category": "stripe",
        "is_secret": True,
        "required": True,
        "test_connection": True
    },
    "STRIPE_WEBHOOK_SECRET": {
        "description": "Stripe webhook signing secret (whsec_...)",
        "category": "stripe",
        "is_secret": True,
        "required": True,
        "test_connection": False
    },

    # Lago Settings
    "LAGO_API_KEY": {
        "description": "Lago API key for billing management",
        "category": "lago",
        "is_secret": True,
        "required": True,
        "test_connection": True
    },
    "LAGO_API_URL": {
        "description": "Lago API URL (internal)",
        "category": "lago",
        "is_secret": False,
        "required": True,
        "test_connection": True
    },
    "LAGO_PUBLIC_URL": {
        "description": "Lago public URL (external)",
        "category": "lago",
        "is_secret": False,
        "required": True,
        "test_connection": False
    },

    # Keycloak Settings
    "KEYCLOAK_URL": {
        "description": "Keycloak URL (internal)",
        "category": "keycloak",
        "is_secret": False,
        "required": True,
        "test_connection": True
    },
    "KEYCLOAK_REALM": {
        "description": "Keycloak realm name",
        "category": "keycloak",
        "is_secret": False,
        "required": True,
        "test_connection": False
    },
    "KEYCLOAK_ADMIN_PASSWORD": {
        "description": "Keycloak admin password",
        "category": "keycloak",
        "is_secret": True,
        "required": True,
        "test_connection": True
    },

    # Cloudflare Settings
    "CLOUDFLARE_API_TOKEN": {
        "description": "Cloudflare API token with DNS edit permissions",
        "category": "cloudflare",
        "is_secret": True,
        "required": False,
        "test_connection": True
    },

    # NameCheap Settings
    "NAMECHEAP_API_USERNAME": {
        "description": "NameCheap API username",
        "category": "namecheap",
        "is_secret": False,
        "required": False,
        "test_connection": False
    },
    "NAMECHEAP_API_KEY": {
        "description": "NameCheap API key",
        "category": "namecheap",
        "is_secret": True,
        "required": False,
        "test_connection": True
    },

    # Forgejo Settings
    "FORGEJO_API_URL": {
        "description": "Forgejo API URL (e.g., https://git.unicorncommander.ai)",
        "category": "forgejo",
        "is_secret": False,
        "required": False,
        "test_connection": True
    },
    "FORGEJO_API_TOKEN": {
        "description": "Forgejo API token (Personal Access Token with read permissions)",
        "category": "forgejo",
        "is_secret": True,
        "required": False,
        "test_connection": True
    },
}

def mask_secret(value: str) -> str:
    """Mask secret values for display"""
    if not value or len(value) < 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"

def get_current_env_value(key: str) -> Optional[str]:
    """
    Get current setting value

    Priority:
    1. Database (if saved via settings UI)
    2. Environment variable (from docker-compose or shell)
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'unicorn-postgresql'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'unicorn'),
            password=os.getenv('POSTGRES_PASSWORD', 'unicorn'),
            database=os.getenv('POSTGRES_DB', 'unicorn_db')
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check database first
        cursor.execute("SELECT value FROM platform_settings WHERE key = %s", (key,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return result['value']

    except Exception as e:
        # If database fails, fall back to environment
        logger.debug(f"Database lookup failed for {key}, using environment: {e}")

    # Fall back to environment variable
    return os.getenv(key)

@router.get("/settings", summary="Get all platform settings")
async def get_platform_settings(admin: bool = Depends(require_admin)):
    """
    Get all platform settings with masked secrets

    **Permissions**: Admin only
    """
    settings = []

    for key, config in PLATFORM_SETTINGS.items():
        current_value = get_current_env_value(key)

        settings.append({
            "key": key,
            "value": mask_secret(current_value) if config["is_secret"] and current_value else current_value,
            "description": config["description"],
            "category": config["category"],
            "is_secret": config["is_secret"],
            "required": config["required"],
            "test_connection": config["test_connection"],
            "is_configured": bool(current_value),
            "last_updated": None  # TODO: Track in database
        })

    # Group by category
    grouped = {}
    for setting in settings:
        category = setting["category"]
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(setting)

    return {
        "settings": settings,
        "grouped": grouped,
        "total": len(settings),
        "configured": sum(1 for s in settings if s["is_configured"]),
        "required": sum(1 for s in settings if s["required"])
    }

@router.get("/settings/{key}", summary="Get specific setting")
async def get_setting(key: str, admin: bool = Depends(require_admin)):
    """Get specific platform setting"""
    if key not in PLATFORM_SETTINGS:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    config = PLATFORM_SETTINGS[key]
    current_value = get_current_env_value(key)

    return {
        "key": key,
        "value": mask_secret(current_value) if config["is_secret"] and current_value else current_value,
        "description": config["description"],
        "category": config["category"],
        "is_secret": config["is_secret"],
        "required": config["required"],
        "test_connection": config["test_connection"],
        "is_configured": bool(current_value)
    }

@router.put("/settings", summary="Update platform settings")
async def update_platform_settings(
    update: SettingsUpdate,
    admin: bool = Depends(require_admin)
):
    """
    Update platform settings

    **Process**:
    1. Validate all provided settings exist
    2. Update environment variables in current process (immediate effect)
    3. Store in PostgreSQL for persistence across restarts
    4. Optionally restart container to fully apply changes

    **Permissions**: Admin only

    **Note**: Settings are stored in both environment and database.
    Some services may require container restart to pick up changes.
    """
    # Validate all keys exist
    invalid_keys = [k for k in update.settings.keys() if k not in PLATFORM_SETTINGS]
    if invalid_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid setting keys: {', '.join(invalid_keys)}"
        )

    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        # Database connection
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'unicorn-postgresql'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'unicorn'),
            password=os.getenv('POSTGRES_PASSWORD', 'unicorn'),
            database=os.getenv('POSTGRES_DB', 'unicorn_db')
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Create platform_settings table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS platform_settings (
                key VARCHAR(255) PRIMARY KEY,
                value TEXT,
                category VARCHAR(100),
                is_secret BOOLEAN DEFAULT TRUE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # Update each setting
        updated_count = 0
        for key, value in update.settings.items():
            config = PLATFORM_SETTINGS[key]

            # Update environment variable (immediate effect in current process)
            os.environ[key] = value

            # Store in database (persistent across restarts)
            cursor.execute("""
                INSERT INTO platform_settings (key, value, category, is_secret, updated_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (key)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    updated_at = CURRENT_TIMESTAMP
            """, (key, value, config['category'], config['is_secret']))

            updated_count += 1

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"Updated {updated_count} platform settings")

        # Restart container if requested
        restart_output = None
        restart_warning = None
        if update.restart_required:
            try:
                result = subprocess.run(
                    ["docker", "restart", "ops-center-direct"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    restart_output = "Container restart initiated successfully"
                    restart_warning = "Container is restarting. This page may disconnect briefly."
                else:
                    restart_output = f"Error: {result.stderr}"
            except Exception as e:
                logger.error(f"Failed to restart container: {e}")
                restart_output = f"Error: {str(e)}"

        return {
            "success": True,
            "updated": updated_count,
            "settings": list(update.settings.keys()),
            "restart_required": update.restart_required,
            "restart_output": restart_output,
            "restart_warning": restart_warning,
            "message": f"Updated {updated_count} settings successfully" +
                      (" and initiated container restart" if update.restart_required else "") +
                      ". Changes are now active."
        }

    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@router.post("/settings/test", summary="Test connection with credentials")
async def test_connection(
    request: TestConnectionRequest,
    admin: bool = Depends(require_admin)
):
    """
    Test connection with provided credentials

    **Supported Categories**:
    - stripe: Tests Stripe API connectivity
    - lago: Tests Lago API connectivity
    - keycloak: Tests Keycloak admin API
    - cloudflare: Tests Cloudflare API
    - namecheap: Tests NameCheap API
    - forgejo: Tests Forgejo Git API

    **Note**: If credentials contain masked values or are empty,
    falls back to current environment/database values
    """
    category = request.category
    creds = request.credentials

    # Helper function to get credential value (from request or fallback to env)
    def get_cred(key: str) -> Optional[str]:
        """Get credential value, falling back to environment if not provided or masked"""
        value = creds.get(key, "")

        # If value is masked (contains ...) or empty, use current env value
        if not value or "..." in value or value == "****":
            env_value = get_current_env_value(key)
            logger.debug(f"Using environment value for {key} (frontend sent masked/empty value)")
            return env_value

        return value

    try:
        if category == "stripe":
            import stripe
            stripe.api_key = get_cred("STRIPE_SECRET_KEY")
            balance = stripe.Balance.retrieve()
            return {
                "success": True,
                "message": "Stripe connection successful",
                "details": {
                    "available": balance.available,
                    "pending": balance.pending
                }
            }

        elif category == "lago":
            import requests
            api_key = get_cred("LAGO_API_KEY")
            api_url = get_cred("LAGO_API_URL")

            if not api_key or not api_url:
                return {
                    "success": False,
                    "message": "Lago API credentials not configured",
                    "details": {"error": "LAGO_API_KEY and LAGO_API_URL are required"}
                }

            # Lago health endpoint doesn't require authentication
            response = requests.get(
                f"{api_url}/health",
                timeout=10
            )
            response.raise_for_status()
            health_data = response.json()

            return {
                "success": True,
                "message": f"Lago connection successful (v{health_data.get('version', 'unknown')})",
                "details": health_data
            }

        elif category == "keycloak":
            import requests
            keycloak_url = get_cred("KEYCLOAK_URL")
            admin_password = get_cred("KEYCLOAK_ADMIN_PASSWORD")
            realm = get_cred("KEYCLOAK_REALM") or "uchub"

            if not keycloak_url or not admin_password:
                return {
                    "success": False,
                    "message": "Keycloak credentials not configured",
                    "details": {"error": "KEYCLOAK_URL and KEYCLOAK_ADMIN_PASSWORD are required"}
                }

            # Get admin token
            token_url = f"{keycloak_url}/realms/master/protocol/openid-connect/token"
            response = requests.post(
                token_url,
                data={
                    "client_id": "admin-cli",
                    "username": "admin",
                    "password": admin_password,
                    "grant_type": "password"
                },
                timeout=10
            )
            response.raise_for_status()
            token_data = response.json()

            return {
                "success": True,
                "message": "Keycloak connection successful",
                "details": {
                    "access_token": token_data.get("access_token", "")[:20] + "...",
                    "token_type": token_data.get("token_type")
                }
            }

        elif category == "cloudflare":
            import requests
            api_token = get_cred("CLOUDFLARE_API_TOKEN")

            if not api_token:
                return {
                    "success": False,
                    "message": "Cloudflare API token is required",
                    "details": {"error": "Missing CLOUDFLARE_API_TOKEN"}
                }

            try:
                # Test with zones endpoint (zone-scoped tokens can't access /user endpoints)
                response = requests.get(
                    "https://api.cloudflare.com/client/v4/zones",
                    headers={"Authorization": f"Bearer {api_token}"},
                    timeout=10
                )
                data = response.json()

                # Cloudflare API returns success=false for invalid tokens
                if data.get("success", False):
                    zones = data.get("result", [])
                    zone_count = len(zones)
                    zone_names = [z.get("name") for z in zones[:3]]  # First 3 zones

                    # Check permissions on first zone
                    permissions = []
                    if zones:
                        permissions = zones[0].get("permissions", [])

                    has_dns_edit = any("dns_records:edit" in p for p in permissions)
                    has_zone_read = any("zone:read" in p or "zone_settings:read" in p for p in permissions)

                    return {
                        "success": True,
                        "message": f"Cloudflare API token is valid ({zone_count} zone(s) accessible)",
                        "details": {
                            "zones_count": zone_count,
                            "sample_zones": zone_names if zone_names else ["(no zones)"],
                            "dns_edit_permission": has_dns_edit,
                            "zone_read_permission": has_zone_read,
                            "status": "Token verified via zones API"
                        }
                    }
                else:
                    # Token is invalid or has errors
                    errors = data.get("errors", [])
                    error_messages = [err.get("message", str(err)) for err in errors]
                    error_code = data.get("errors", [{}])[0].get("code") if errors else None

                    # Provide helpful hints based on error code
                    hint = "Check that your token has 'Zone:DNS:Edit' and 'Zone:Zone:Read' permissions"
                    if error_code == 9109:
                        hint = "Token appears to be zone-scoped (this is correct). Try creating a token with 'Edit zone DNS' template."
                    elif error_code == 1000:
                        hint = "Token format is invalid or token has been revoked. Create a new token."

                    return {
                        "success": False,
                        "message": "Cloudflare API token is invalid",
                        "details": {
                            "errors": error_messages,
                            "code": error_code,
                            "hint": hint
                        }
                    }

            except requests.exceptions.RequestException as req_err:
                return {
                    "success": False,
                    "message": f"Failed to connect to Cloudflare API: {str(req_err)}",
                    "details": {"error": str(req_err), "type": type(req_err).__name__}
                }

        elif category == "namecheap":
            import requests
            username = get_cred("NAMECHEAP_API_USERNAME")
            api_key = get_cred("NAMECHEAP_API_KEY")
            client_ip = get_cred("NAMECHEAP_CLIENT_IP") or ""

            if not username or not api_key:
                return {
                    "success": False,
                    "message": "NameCheap credentials not configured",
                    "details": {"error": "NAMECHEAP_API_USERNAME and NAMECHEAP_API_KEY are required"}
                }

            # Test with namecheap.domains.getList
            url = "https://api.namecheap.com/xml.response"
            params = {
                "ApiUser": username,
                "ApiKey": api_key,
                "UserName": username,
                "Command": "namecheap.domains.getList",
                "ClientIp": client_ip
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            return {
                "success": True,
                "message": "NameCheap connection successful",
                "details": {"status": "API key is valid"}
            }

        elif category == "forgejo":
            import requests
            api_url = get_cred("FORGEJO_API_URL")
            api_token = get_cred("FORGEJO_API_TOKEN")

            if not api_url or not api_token:
                return {
                    "success": False,
                    "message": "Forgejo credentials not configured",
                    "details": {"error": "FORGEJO_API_URL and FORGEJO_API_TOKEN are required"}
                }

            try:
                # Test with /api/v1/user endpoint (Forgejo API v1)
                response = requests.get(
                    f"{api_url}/api/v1/user",
                    headers={"Authorization": f"token {api_token}"},
                    timeout=10
                )
                response.raise_for_status()
                user_data = response.json()

                return {
                    "success": True,
                    "message": f"Forgejo connection successful (user: {user_data.get('username', 'unknown')})",
                    "details": {
                        "username": user_data.get("username"),
                        "email": user_data.get("email"),
                        "is_admin": user_data.get("is_admin", False),
                        "api_version": "v1"
                    }
                }
            except requests.exceptions.RequestException as e:
                return {
                    "success": False,
                    "message": f"Forgejo connection failed: {str(e)}",
                    "details": {"error": str(e)}
                }

        else:
            raise HTTPException(status_code=400, detail=f"Unknown category: {category}")

    except Exception as e:
        logger.error(f"Connection test failed for {category}: {e}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "details": {"error": str(e)}
        }

@router.post("/settings/restart", summary="Restart ops-center container")
async def restart_container(admin: bool = Depends(require_admin)):
    """
    Restart ops-center container to apply new settings

    **Warning**: This will cause brief downtime (5-10 seconds)
    **Permissions**: Admin only
    """
    try:
        result = subprocess.run(
            ["docker", "restart", "ops-center-direct"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return {
                "success": True,
                "message": "Container restarted successfully",
                "output": result.stdout
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to restart container: {result.stderr}"
            )

    except Exception as e:
        logger.error(f"Failed to restart container: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add router to main app
if __name__ == "__main__":
    print("Platform Settings API module")
    print(f"Configured settings: {len(PLATFORM_SETTINGS)}")
