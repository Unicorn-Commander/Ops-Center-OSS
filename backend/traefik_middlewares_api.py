"""
Traefik Middlewares Management API

FastAPI endpoints for managing Traefik middlewares.
Includes CORS, headers, rate limiting, authentication, and more.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging

from traefik_config_manager import traefik_config_manager
from audit_logger import audit_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/traefik/middlewares", tags=["Traefik Middlewares"])


class MiddlewareCreate(BaseModel):
    """Create new middleware"""
    name: str = Field(..., description="Unique middleware name", min_length=1, max_length=100)
    type: str = Field(..., description="Middleware type (headers, ratelimit, auth, etc.)")
    config: Dict[str, Any] = Field(..., description="Middleware configuration")


class MiddlewareUpdate(BaseModel):
    """Update existing middleware"""
    config: Dict[str, Any] = Field(..., description="Updated middleware configuration")


class MiddlewareInfo(BaseModel):
    """Middleware information"""
    name: str
    type: str
    config: Dict[str, Any]
    used_by: List[str] = Field(default_factory=list, description="Routes using this middleware")


class MiddlewareTemplate(BaseModel):
    """Middleware template"""
    name: str
    type: str
    description: str
    example_config: Dict[str, Any]


def require_admin(user_info: Dict = Depends(lambda: {"role": "admin", "username": "admin"})):
    """Require admin role"""
    if user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_info


# Middleware templates
MIDDLEWARE_TEMPLATES = [
    {
        "name": "Security Headers",
        "type": "headers",
        "description": "Add security headers to responses",
        "example_config": {
            "headers": {
                "customResponseHeaders": {
                    "X-Frame-Options": "SAMEORIGIN",
                    "X-Content-Type-Options": "nosniff",
                    "X-XSS-Protection": "1; mode=block"
                },
                "stsSeconds": 31536000,
                "stsIncludeSubdomains": True,
                "stsPreload": True
            }
        }
    },
    {
        "name": "CORS",
        "type": "headers",
        "description": "Enable Cross-Origin Resource Sharing",
        "example_config": {
            "headers": {
                "accessControlAllowOriginList": ["*"],
                "accessControlAllowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "accessControlAllowHeaders": ["Content-Type", "Authorization"],
                "accessControlMaxAge": 100,
                "addVaryHeader": True
            }
        }
    },
    {
        "name": "Rate Limit",
        "type": "rateLimit",
        "description": "Limit request rate per IP",
        "example_config": {
            "rateLimit": {
                "average": 100,
                "period": "1m",
                "burst": 50
            }
        }
    },
    {
        "name": "Basic Auth",
        "type": "basicAuth",
        "description": "HTTP Basic Authentication",
        "example_config": {
            "basicAuth": {
                "users": [
                    "user:$apr1$..."  # Use htpasswd to generate
                ]
            }
        }
    },
    {
        "name": "Redirect to HTTPS",
        "type": "redirectScheme",
        "description": "Redirect HTTP to HTTPS",
        "example_config": {
            "redirectScheme": {
                "scheme": "https",
                "permanent": True
            }
        }
    },
    {
        "name": "Strip Prefix",
        "type": "stripPrefix",
        "description": "Remove prefix from request path",
        "example_config": {
            "stripPrefix": {
                "prefixes": ["/api"]
            }
        }
    },
    {
        "name": "Add Prefix",
        "type": "addPrefix",
        "description": "Add prefix to request path",
        "example_config": {
            "addPrefix": {
                "prefix": "/api"
            }
        }
    },
    {
        "name": "Compress",
        "type": "compress",
        "description": "Enable gzip compression",
        "example_config": {
            "compress": {}
        }
    }
]


@router.get("/templates", response_model=List[MiddlewareTemplate])
async def list_middleware_templates(admin: Dict = Depends(require_admin)):
    """
    List available middleware templates.

    Returns:
        List of middleware templates
    """
    return [MiddlewareTemplate(**template) for template in MIDDLEWARE_TEMPLATES]


@router.get("", response_model=List[MiddlewareInfo])
async def list_middlewares(admin: Dict = Depends(require_admin)):
    """
    List all Traefik middlewares.

    Returns:
        List of middleware information
    """
    try:
        config = await traefik_config_manager.get_current_config()
        middlewares = []

        if config.http and 'middlewares' in config.http:
            # Get routers to find which middlewares are used
            routers = config.http.get('routers', {})

            for name, mw_config in config.http['middlewares'].items():
                # Determine middleware type from config
                mw_type = list(mw_config.keys())[0] if mw_config else "unknown"

                # Find routers using this middleware
                used_by = [
                    router_name
                    for router_name, router_config in routers.items()
                    if name in router_config.get('middlewares', [])
                ]

                middlewares.append(MiddlewareInfo(
                    name=name,
                    type=mw_type,
                    config=mw_config,
                    used_by=used_by
                ))

        logger.info(f"Listed {len(middlewares)} middlewares")
        return middlewares

    except Exception as e:
        logger.error(f"Error listing middlewares: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{middleware_id}", response_model=MiddlewareInfo)
async def get_middleware(middleware_id: str, admin: Dict = Depends(require_admin)):
    """
    Get specific middleware details.

    Args:
        middleware_id: Middleware name

    Returns:
        Middleware information
    """
    try:
        config = await traefik_config_manager.get_current_config()

        if not config.http or 'middlewares' not in config.http:
            raise HTTPException(status_code=404, detail="Middleware not found")

        mw_config = config.http['middlewares'].get(middleware_id)
        if not mw_config:
            raise HTTPException(status_code=404, detail=f"Middleware '{middleware_id}' not found")

        # Determine type
        mw_type = list(mw_config.keys())[0] if mw_config else "unknown"

        # Find usage
        routers = config.http.get('routers', {})
        used_by = [
            router_name
            for router_name, router_config in routers.items()
            if middleware_id in router_config.get('middlewares', [])
        ]

        return MiddlewareInfo(
            name=middleware_id,
            type=mw_type,
            config=mw_config,
            used_by=used_by
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting middleware {middleware_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=MiddlewareInfo)
async def create_middleware(middleware: MiddlewareCreate, admin: Dict = Depends(require_admin)):
    """
    Create a new middleware.

    Args:
        middleware: Middleware configuration

    Returns:
        Created middleware information
    """
    try:
        # Get current config
        config = await traefik_config_manager.get_current_config()

        # Check if middleware already exists
        if config.http and 'middlewares' in config.http and middleware.name in config.http['middlewares']:
            raise HTTPException(status_code=409, detail=f"Middleware '{middleware.name}' already exists")

        # Add to config
        if not config.http:
            config.http = {}
        if 'middlewares' not in config.http:
            config.http['middlewares'] = {}

        config.http['middlewares'][middleware.name] = middleware.config

        # Validate
        validation = await traefik_config_manager.validate_config(config)
        if not validation.valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid configuration: {'; '.join(validation.errors)}"
            )

        # Update config
        await traefik_config_manager.update_config(config)

        # Audit log
        await audit_logger.log_action(
            action="traefik.middleware.create",
            user_id=admin.get("username", "admin"),
            resource_type="traefik_middleware",
            resource_id=middleware.name,
            details={
                "type": middleware.type,
                "config": middleware.config
            }
        )

        logger.info(f"Created middleware: {middleware.name}")

        return MiddlewareInfo(
            name=middleware.name,
            type=middleware.type,
            config=middleware.config,
            used_by=[]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating middleware {middleware.name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{middleware_id}", response_model=MiddlewareInfo)
async def update_middleware(
    middleware_id: str,
    middleware: MiddlewareUpdate,
    admin: Dict = Depends(require_admin)
):
    """
    Update an existing middleware.

    Args:
        middleware_id: Middleware name
        middleware: Updated middleware configuration

    Returns:
        Updated middleware information
    """
    try:
        # Get current config
        config = await traefik_config_manager.get_current_config()

        # Check if middleware exists
        if not config.http or 'middlewares' not in config.http or middleware_id not in config.http['middlewares']:
            raise HTTPException(status_code=404, detail=f"Middleware '{middleware_id}' not found")

        # Update config
        config.http['middlewares'][middleware_id] = middleware.config

        # Validate
        validation = await traefik_config_manager.validate_config(config)
        if not validation.valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid configuration: {'; '.join(validation.errors)}"
            )

        # Update config
        await traefik_config_manager.update_config(config)

        # Audit log
        await audit_logger.log_action(
            action="traefik.middleware.update",
            user_id=admin.get("username", "admin"),
            resource_type="traefik_middleware",
            resource_id=middleware_id,
            details={"config": middleware.config}
        )

        logger.info(f"Updated middleware: {middleware_id}")

        # Determine type
        mw_type = list(middleware.config.keys())[0] if middleware.config else "unknown"

        # Find usage
        routers = config.http.get('routers', {})
        used_by = [
            router_name
            for router_name, router_config in routers.items()
            if middleware_id in router_config.get('middlewares', [])
        ]

        return MiddlewareInfo(
            name=middleware_id,
            type=mw_type,
            config=middleware.config,
            used_by=used_by
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating middleware {middleware_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{middleware_id}")
async def delete_middleware(middleware_id: str, admin: Dict = Depends(require_admin)):
    """
    Delete a middleware.

    Args:
        middleware_id: Middleware name

    Returns:
        Success message
    """
    try:
        # Get current config
        config = await traefik_config_manager.get_current_config()

        # Check if middleware exists
        if not config.http or 'middlewares' not in config.http or middleware_id not in config.http['middlewares']:
            raise HTTPException(status_code=404, detail=f"Middleware '{middleware_id}' not found")

        # Check if middleware is used by any router
        if config.http and 'routers' in config.http:
            used_by = [
                router_name
                for router_name, router_config in config.http['routers'].items()
                if middleware_id in router_config.get('middlewares', [])
            ]
            if used_by:
                raise HTTPException(
                    status_code=409,
                    detail=f"Middleware is used by router(s): {', '.join(used_by)}. Remove from routers first."
                )

        # Remove middleware
        deleted_middleware = config.http['middlewares'].pop(middleware_id)

        # Update config
        await traefik_config_manager.update_config(config)

        # Audit log
        await audit_logger.log_action(
            action="traefik.middleware.delete",
            user_id=admin.get("username", "admin"),
            resource_type="traefik_middleware",
            resource_id=middleware_id,
            details={"deleted_config": deleted_middleware}
        )

        logger.info(f"Deleted middleware: {middleware_id}")

        return {"message": f"Middleware '{middleware_id}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting middleware {middleware_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
