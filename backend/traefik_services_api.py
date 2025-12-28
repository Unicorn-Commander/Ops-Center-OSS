"""
Traefik Services Management API

FastAPI endpoints for managing Traefik backend services.
Includes Docker container discovery and health monitoring.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
import logging
import docker
from datetime import datetime

from traefik_config_manager import traefik_config_manager, TraefikService
from audit_logger import audit_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/traefik/services", tags=["Traefik Services"])


class ServiceCreate(BaseModel):
    """Create new backend service"""
    name: str = Field(..., description="Unique service name", min_length=1, max_length=100)
    servers: List[Dict[str, str]] = Field(..., description="Backend server URLs")
    pass_host_header: bool = Field(default=True, description="Pass Host header to backend")
    health_check: Optional[Dict[str, Any]] = Field(default=None, description="Health check configuration")

    @validator('servers')
    def validate_servers(cls, v):
        """Validate server configurations"""
        if not v:
            raise ValueError("At least one server is required")
        for server in v:
            if 'url' not in server:
                raise ValueError("Each server must have a 'url' field")
        return v


class ServiceUpdate(BaseModel):
    """Update existing service"""
    servers: Optional[List[Dict[str, str]]] = Field(default=None, description="Backend server URLs")
    pass_host_header: Optional[bool] = Field(default=None, description="Pass Host header to backend")
    health_check: Optional[Dict[str, Any]] = Field(default=None, description="Health check configuration")


class ServiceInfo(BaseModel):
    """Service information"""
    name: str
    servers: List[Dict[str, str]]
    pass_host_header: bool
    health_check: Optional[Dict[str, Any]]
    status: str = "active"
    health_status: Optional[str] = None


class DiscoveredContainer(BaseModel):
    """Docker container discovered for service creation"""
    container_id: str
    container_name: str
    image: str
    status: str
    ports: List[Dict[str, Any]]
    networks: List[str]
    suggested_url: Optional[str] = None


def require_admin(user_info: Dict = Depends(lambda: {"role": "admin", "username": "admin"})):
    """Require admin role"""
    if user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_info


@router.get("", response_model=List[ServiceInfo])
async def list_services(admin: Dict = Depends(require_admin)):
    """
    List all Traefik backend services.

    Returns:
        List of service information
    """
    try:
        config = await traefik_config_manager.get_current_config()
        services = []

        if config.http and 'services' in config.http:
            for name, service_config in config.http['services'].items():
                lb_config = service_config.get('loadBalancer', {})
                services.append(ServiceInfo(
                    name=name,
                    servers=lb_config.get('servers', []),
                    pass_host_header=lb_config.get('passHostHeader', True),
                    health_check=lb_config.get('healthCheck'),
                    status="active"
                ))

        logger.info(f"Listed {len(services)} services")
        return services
    except Exception as e:
        logger.error(f"Error listing services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{service_id}", response_model=ServiceInfo)
async def get_service(service_id: str, admin: Dict = Depends(require_admin)):
    """
    Get specific service details.

    Args:
        service_id: Service name

    Returns:
        Service information
    """
    try:
        config = await traefik_config_manager.get_current_config()

        if not config.http or 'services' not in config.http:
            raise HTTPException(status_code=404, detail="Service not found")

        service_config = config.http['services'].get(service_id)
        if not service_config:
            raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")

        lb_config = service_config.get('loadBalancer', {})
        return ServiceInfo(
            name=service_id,
            servers=lb_config.get('servers', []),
            pass_host_header=lb_config.get('passHostHeader', True),
            health_check=lb_config.get('healthCheck'),
            status="active"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service {service_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=ServiceInfo)
async def create_service(service: ServiceCreate, admin: Dict = Depends(require_admin)):
    """
    Create a new backend service.

    Args:
        service: Service configuration

    Returns:
        Created service information
    """
    try:
        # Get current config
        config = await traefik_config_manager.get_current_config()

        # Check if service already exists
        if config.http and 'services' in config.http and service.name in config.http['services']:
            raise HTTPException(status_code=409, detail=f"Service '{service.name}' already exists")

        # Prepare new service config
        new_service = {
            "loadBalancer": {
                "servers": service.servers,
                "passHostHeader": service.pass_host_header
            }
        }

        if service.health_check:
            new_service["loadBalancer"]["healthCheck"] = service.health_check

        # Add to config
        if not config.http:
            config.http = {}
        if 'services' not in config.http:
            config.http['services'] = {}

        config.http['services'][service.name] = new_service

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
            action="traefik.service.create",
            user_id=admin.get("username", "admin"),
            resource_type="traefik_service",
            resource_id=service.name,
            details={
                "servers": service.servers,
                "pass_host_header": service.pass_host_header
            }
        )

        logger.info(f"Created service: {service.name}")

        return ServiceInfo(
            name=service.name,
            servers=service.servers,
            pass_host_header=service.pass_host_header,
            health_check=service.health_check,
            status="active"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating service {service.name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{service_id}", response_model=ServiceInfo)
async def update_service(
    service_id: str,
    service: ServiceUpdate,
    admin: Dict = Depends(require_admin)
):
    """
    Update an existing backend service.

    Args:
        service_id: Service name
        service: Updated service configuration

    Returns:
        Updated service information
    """
    try:
        # Get current config
        config = await traefik_config_manager.get_current_config()

        # Check if service exists
        if not config.http or 'services' not in config.http or service_id not in config.http['services']:
            raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")

        current_service = config.http['services'][service_id]
        lb_config = current_service.get('loadBalancer', {})

        # Update fields
        if service.servers is not None:
            lb_config['servers'] = service.servers

        if service.pass_host_header is not None:
            lb_config['passHostHeader'] = service.pass_host_header

        if service.health_check is not None:
            lb_config['healthCheck'] = service.health_check

        current_service['loadBalancer'] = lb_config

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
            action="traefik.service.update",
            user_id=admin.get("username", "admin"),
            resource_type="traefik_service",
            resource_id=service_id,
            details=service.dict(exclude_none=True)
        )

        logger.info(f"Updated service: {service_id}")

        return ServiceInfo(
            name=service_id,
            servers=lb_config.get('servers', []),
            pass_host_header=lb_config.get('passHostHeader', True),
            health_check=lb_config.get('healthCheck'),
            status="active"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating service {service_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{service_id}")
async def delete_service(service_id: str, admin: Dict = Depends(require_admin)):
    """
    Delete a backend service.

    Args:
        service_id: Service name

    Returns:
        Success message
    """
    try:
        # Get current config
        config = await traefik_config_manager.get_current_config()

        # Check if service exists
        if not config.http or 'services' not in config.http or service_id not in config.http['services']:
            raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")

        # Check if service is used by any router
        if config.http and 'routers' in config.http:
            used_by = [
                router_name
                for router_name, router_config in config.http['routers'].items()
                if router_config.get('service') == service_id
            ]
            if used_by:
                raise HTTPException(
                    status_code=409,
                    detail=f"Service is used by router(s): {', '.join(used_by)}. Delete routers first."
                )

        # Remove service
        deleted_service = config.http['services'].pop(service_id)

        # Update config
        await traefik_config_manager.update_config(config)

        # Audit log
        await audit_logger.log_action(
            action="traefik.service.delete",
            user_id=admin.get("username", "admin"),
            resource_type="traefik_service",
            resource_id=service_id,
            details={"deleted_config": deleted_service}
        )

        logger.info(f"Deleted service: {service_id}")

        return {"message": f"Service '{service_id}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting service {service_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discover/containers", response_model=List[DiscoveredContainer])
async def discover_containers(admin: Dict = Depends(require_admin)):
    """
    Discover running Docker containers for service creation.

    Returns:
        List of discovered containers
    """
    try:
        client = docker.from_env()
        containers = []

        for container in client.containers.list():
            # Get container info
            container_info = container.attrs

            # Extract ports
            ports = []
            port_bindings = container_info.get('NetworkSettings', {}).get('Ports', {})
            for container_port, host_bindings in port_bindings.items():
                if host_bindings:
                    for binding in host_bindings:
                        ports.append({
                            "container_port": container_port,
                            "host_port": binding.get('HostPort'),
                            "protocol": "tcp" if "/" not in container_port else container_port.split("/")[1]
                        })

            # Extract networks
            networks = list(container_info.get('NetworkSettings', {}).get('Networks', {}).keys())

            # Suggest URL based on first exposed port
            suggested_url = None
            if ports:
                container_name = container.name
                first_port = ports[0]['container_port'].split('/')[0]
                # Use internal Docker network URL
                suggested_url = f"http://{container_name}:{first_port}"

            containers.append(DiscoveredContainer(
                container_id=container.id[:12],
                container_name=container.name,
                image=container_info['Config']['Image'],
                status=container.status,
                ports=ports,
                networks=networks,
                suggested_url=suggested_url
            ))

        logger.info(f"Discovered {len(containers)} containers")
        return containers

    except docker.errors.DockerException as e:
        logger.error(f"Docker error: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")
    except Exception as e:
        logger.error(f"Error discovering containers: {e}")
        raise HTTPException(status_code=500, detail=str(e))
