"""
Traefik Routes Management API

FastAPI endpoints for managing Traefik HTTP routes (routers).
Admin-only access with full audit logging.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from traefik_config_manager import (
    traefik_config_manager,
    TraefikRouter,
    TraefikConfig,
    ValidationResult
)
from audit_logger import audit_logger
from audit_helpers import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/traefik/routes", tags=["Traefik Routes"])


class RouteCreate(BaseModel):
    """Create new Traefik route"""
    name: str = Field(..., description="Unique route name", min_length=1, max_length=100)
    rule: str = Field(..., description="Traefik rule (e.g., Host(`example.com`))")
    service: str = Field(..., description="Backend service name")
    entryPoints: List[str] = Field(default=["https"], description="Entry points")
    middlewares: Optional[List[str]] = Field(default=None, description="Middleware names")
    priority: Optional[int] = Field(default=None, description="Router priority")
    enable_tls: bool = Field(default=True, description="Enable TLS/HTTPS")
    cert_resolver: str = Field(default="letsencrypt", description="Certificate resolver")

    @validator('name')
    def validate_name(cls, v):
        """Validate route name"""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Route name must be alphanumeric (hyphens and underscores allowed)")
        return v


class RouteUpdate(BaseModel):
    """Update existing Traefik route"""
    rule: Optional[str] = Field(default=None, description="Traefik rule")
    service: Optional[str] = Field(default=None, description="Backend service name")
    entryPoints: Optional[List[str]] = Field(default=None, description="Entry points")
    middlewares: Optional[List[str]] = Field(default=None, description="Middleware names")
    priority: Optional[int] = Field(default=None, description="Router priority")
    enable_tls: Optional[bool] = Field(default=None, description="Enable TLS/HTTPS")
    cert_resolver: Optional[str] = Field(default=None, description="Certificate resolver")


class RouteInfo(BaseModel):
    """Route information"""
    name: str
    rule: str
    service: str
    entryPoints: List[str]
    middlewares: Optional[List[str]]
    priority: Optional[int]
    tls: Optional[Dict[str, Any]]
    status: str = "active"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RouteTestResult(BaseModel):
    """Route test result"""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


def require_admin(user_info: Dict = Depends(lambda: {"role": "admin", "username": "admin"})):
    """Require admin role (simplified for now, replace with actual auth)"""
    # TODO: Replace with actual Keycloak authentication
    if user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_info


@router.get("", response_model=List[RouteInfo])
async def list_routes(admin: Dict = Depends(require_admin)):
    """
    List all Traefik routes.

    Returns:
        List of route information
    """
    try:
        config = await traefik_config_manager.get_current_config()
        routes = []

        if config.http and 'routers' in config.http:
            for name, router_config in config.http['routers'].items():
                routes.append(RouteInfo(
                    name=name,
                    rule=router_config.get('rule', ''),
                    service=router_config.get('service', ''),
                    entryPoints=router_config.get('entryPoints', ['https']),
                    middlewares=router_config.get('middlewares'),
                    priority=router_config.get('priority'),
                    tls=router_config.get('tls'),
                    status="active"
                ))

        logger.info(f"Listed {len(routes)} routes")
        return routes
    except Exception as e:
        logger.error(f"Error listing routes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{route_id}", response_model=RouteInfo)
async def get_route(route_id: str, admin: Dict = Depends(require_admin)):
    """
    Get specific route details.

    Args:
        route_id: Route name

    Returns:
        Route information
    """
    try:
        config = await traefik_config_manager.get_current_config()

        if not config.http or 'routers' not in config.http:
            raise HTTPException(status_code=404, detail="Route not found")

        router_config = config.http['routers'].get(route_id)
        if not router_config:
            raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found")

        return RouteInfo(
            name=route_id,
            rule=router_config.get('rule', ''),
            service=router_config.get('service', ''),
            entryPoints=router_config.get('entryPoints', ['https']),
            middlewares=router_config.get('middlewares'),
            priority=router_config.get('priority'),
            tls=router_config.get('tls'),
            status="active"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting route {route_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=RouteInfo)
async def create_route(route: RouteCreate, admin: Dict = Depends(require_admin)):
    """
    Create a new Traefik route.

    Args:
        route: Route configuration

    Returns:
        Created route information
    """
    try:
        # Get current config
        config = await traefik_config_manager.get_current_config()

        # Check if route already exists
        if config.http and 'routers' in config.http and route.name in config.http['routers']:
            raise HTTPException(status_code=409, detail=f"Route '{route.name}' already exists")

        # Check for rule conflicts
        conflicts = await traefik_config_manager.get_router_conflicts(route.rule)
        if conflicts:
            raise HTTPException(
                status_code=409,
                detail=f"Rule conflicts with existing route(s): {', '.join(conflicts)}"
            )

        # Prepare new router config
        new_router = {
            "rule": route.rule,
            "service": route.service,
            "entryPoints": route.entryPoints
        }

        if route.middlewares:
            new_router["middlewares"] = route.middlewares

        if route.priority:
            new_router["priority"] = route.priority

        if route.enable_tls:
            new_router["tls"] = {
                "certResolver": route.cert_resolver
            }

        # Add to config
        if not config.http:
            config.http = {}
        if 'routers' not in config.http:
            config.http['routers'] = {}

        config.http['routers'][route.name] = new_router

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
            action="traefik.route.create",
            user_id=admin.get("username", "admin"),
            resource_type="traefik_route",
            resource_id=route.name,
            details={
                "rule": route.rule,
                "service": route.service,
                "entry_points": route.entryPoints
            }
        )

        logger.info(f"Created route: {route.name}")

        return RouteInfo(
            name=route.name,
            rule=route.rule,
            service=route.service,
            entryPoints=route.entryPoints,
            middlewares=route.middlewares,
            priority=route.priority,
            tls=new_router.get('tls'),
            status="active",
            created_at=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating route {route.name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{route_id}", response_model=RouteInfo)
async def update_route(
    route_id: str,
    route: RouteUpdate,
    admin: Dict = Depends(require_admin)
):
    """
    Update an existing Traefik route.

    Args:
        route_id: Route name
        route: Updated route configuration

    Returns:
        Updated route information
    """
    try:
        # Get current config
        config = await traefik_config_manager.get_current_config()

        # Check if route exists
        if not config.http or 'routers' not in config.http or route_id not in config.http['routers']:
            raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found")

        current_router = config.http['routers'][route_id]

        # Update fields
        if route.rule is not None:
            # Check for conflicts with new rule
            conflicts = await traefik_config_manager.get_router_conflicts(route.rule, exclude_router=route_id)
            if conflicts:
                raise HTTPException(
                    status_code=409,
                    detail=f"Rule conflicts with existing route(s): {', '.join(conflicts)}"
                )
            current_router['rule'] = route.rule

        if route.service is not None:
            current_router['service'] = route.service

        if route.entryPoints is not None:
            current_router['entryPoints'] = route.entryPoints

        if route.middlewares is not None:
            current_router['middlewares'] = route.middlewares

        if route.priority is not None:
            current_router['priority'] = route.priority

        if route.enable_tls is not None:
            if route.enable_tls:
                current_router['tls'] = {
                    "certResolver": route.cert_resolver or "letsencrypt"
                }
            else:
                current_router.pop('tls', None)

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
            action="traefik.route.update",
            user_id=admin.get("username", "admin"),
            resource_type="traefik_route",
            resource_id=route_id,
            details=route.dict(exclude_none=True)
        )

        logger.info(f"Updated route: {route_id}")

        return RouteInfo(
            name=route_id,
            rule=current_router.get('rule', ''),
            service=current_router.get('service', ''),
            entryPoints=current_router.get('entryPoints', ['https']),
            middlewares=current_router.get('middlewares'),
            priority=current_router.get('priority'),
            tls=current_router.get('tls'),
            status="active",
            updated_at=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating route {route_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{route_id}")
async def delete_route(route_id: str, admin: Dict = Depends(require_admin)):
    """
    Delete a Traefik route.

    Args:
        route_id: Route name

    Returns:
        Success message
    """
    try:
        # Get current config
        config = await traefik_config_manager.get_current_config()

        # Check if route exists
        if not config.http or 'routers' not in config.http or route_id not in config.http['routers']:
            raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found")

        # Remove route
        deleted_router = config.http['routers'].pop(route_id)

        # Update config
        await traefik_config_manager.update_config(config)

        # Audit log
        await audit_logger.log_action(
            action="traefik.route.delete",
            user_id=admin.get("username", "admin"),
            resource_type="traefik_route",
            resource_id=route_id,
            details={"deleted_config": deleted_router}
        )

        logger.info(f"Deleted route: {route_id}")

        return {"message": f"Route '{route_id}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting route {route_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{route_id}/test", response_model=RouteTestResult)
async def test_route(route_id: str, admin: Dict = Depends(require_admin)):
    """
    Test a Traefik route configuration.

    Args:
        route_id: Route name

    Returns:
        Test result
    """
    try:
        # Get route config
        config = await traefik_config_manager.get_current_config()

        if not config.http or 'routers' not in config.http or route_id not in config.http['routers']:
            raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found")

        router_config = config.http['routers'][route_id]

        # Validate router
        try:
            TraefikRouter(**router_config)
        except Exception as e:
            return RouteTestResult(
                success=False,
                message=f"Router validation failed: {str(e)}"
            )

        # Check service exists
        service_name = router_config.get('service')
        if service_name and config.http and 'services' in config.http:
            if service_name not in config.http['services']:
                return RouteTestResult(
                    success=False,
                    message=f"Referenced service '{service_name}' not found"
                )

        # Check middlewares exist
        middlewares = router_config.get('middlewares', [])
        if middlewares and config.http and 'middlewares' in config.http:
            missing_mw = [mw for mw in middlewares if mw not in config.http['middlewares']]
            if missing_mw:
                return RouteTestResult(
                    success=False,
                    message=f"Referenced middleware(s) not found: {', '.join(missing_mw)}"
                )

        return RouteTestResult(
            success=True,
            message="Route configuration is valid",
            details={
                "rule": router_config.get('rule'),
                "service": service_name,
                "tls_enabled": 'tls' in router_config
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing route {route_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
