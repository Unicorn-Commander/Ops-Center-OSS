"""
Traefik Configuration Management API - Simplified for Pydantic v2 Compatibility
Epic 1.3: Traefik Configuration Management

This is a simplified version focused on core functionality.
Full comprehensive version with complex validators will be developed in future iteration.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from traefik_manager import (
    TraefikManager,
    TraefikError,
    CertificateError,
    RouteError,
    MiddlewareError,
    ConfigurationError
)

router = APIRouter(prefix="/api/v1/traefik", tags=["Traefik Management (Epic 1.3)"])
logger = logging.getLogger(__name__)

# Initialize Traefik manager
traefik_manager = TraefikManager()


# ==================== Simple Request Models ====================

class RouteCreate(BaseModel):
    """Simplified route creation model"""
    name: str = Field(..., description="Route name")
    rule: str = Field(..., description="Traefik rule (e.g., Host(`example.com`))")
    service: str = Field(..., description="Target service name")
    entrypoints: List[str] = Field(default=["http"], description="Entry points")
    priority: int = Field(default=100, description="Route priority")
    middlewares: List[str] = Field(default=[], description="Middleware names")


class RouteUpdate(BaseModel):
    """Route update model"""
    rule: Optional[str] = Field(None, description="Traefik rule")
    service: Optional[str] = Field(None, description="Target service name")
    priority: Optional[int] = Field(None, description="Route priority")
    middlewares: Optional[List[str]] = Field(None, description="Middleware names")


class ServiceCreate(BaseModel):
    """Simplified service creation model"""
    name: str = Field(..., description="Service name")
    url: str = Field(..., description="Backend URL (e.g., http://backend:8080)")
    healthcheck_path: Optional[str] = Field(None, description="Health check path")


class ServiceUpdate(BaseModel):
    """Service update model"""
    url: Optional[str] = Field(None, description="Backend URL")
    healthcheck_path: Optional[str] = Field(None, description="Health check path")


class MiddlewareCreate(BaseModel):
    """Simplified middleware creation model"""
    name: str = Field(..., description="Middleware name")
    type: str = Field(..., description="Middleware type (compress, ratelimit, etc.)")
    config: Dict[str, Any] = Field(default={}, description="Middleware configuration")


class MiddlewareUpdate(BaseModel):
    """Middleware update model"""
    config: Optional[Dict[str, Any]] = Field(None, description="Middleware configuration")


# ==================== Health & Status Endpoints ====================

@router.get("/health")
async def health_check():
    """Health check endpoint for Traefik management API"""
    return {
        "status": "healthy",
        "service": "traefik-management-api",
        "version": "1.0.0-simplified",
        "epic": "1.3"
    }


@router.get("/status")
async def get_traefik_status():
    """Get overall Traefik status"""
    try:
        routes = traefik_manager.list_routes()
        certificates = traefik_manager.list_certificates()

        return {
            "status": "operational",
            "routes_count": len(routes),
            "certificates_count": len(certificates),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get Traefik status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Route Management ====================

@router.get("/routes")
async def list_routes():
    """List all Traefik routes"""
    try:
        routes = traefik_manager.list_routes()
        return {"routes": routes, "count": len(routes)}
    except TraefikError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/routes", status_code=201)
async def create_route(route: RouteCreate):
    """Create a new Traefik route"""
    try:
        result = traefik_manager.create_route(
            name=route.name,
            rule=route.rule,
            service=route.service,
            entrypoints=route.entrypoints,
            middlewares=route.middlewares,
            priority=route.priority,
            username="api-user"
        )
        return result
    except RouteError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create route: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routes/{route_name}")
async def get_route(route_name: str):
    """Get details of a specific route"""
    try:
        routes = traefik_manager.list_routes()
        route = next((r for r in routes if r['name'] == route_name), None)

        if not route:
            raise HTTPException(status_code=404, detail=f"Route '{route_name}' not found")

        return {"route": route}
    except RouteError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/routes/{route_name}")
async def update_route(route_name: str, updates: RouteUpdate):
    """Update an existing route"""
    try:
        # Convert Pydantic model to dict, excluding None values
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}

        if not update_dict:
            raise HTTPException(status_code=400, detail="No updates provided")

        result = traefik_manager.update_route(
            name=route_name,
            updates=update_dict,
            username="api-user"
        )
        return result
    except RouteError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update route: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/routes/{route_name}")
async def delete_route(route_name: str):
    """Delete a Traefik route"""
    try:
        result = traefik_manager.delete_route(name=route_name, username="api-user")
        return result
    except RouteError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete route: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SSL Certificate Management ====================

@router.get("/certificates")
async def list_certificates():
    """List all SSL certificates"""
    try:
        certificates = traefik_manager.list_certificates()
        return {"certificates": certificates, "count": len(certificates)}
    except CertificateError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/certificates/{domain}")
async def get_certificate(domain: str):
    """Get SSL certificate information for a domain"""
    try:
        cert_info = traefik_manager.get_certificate_info(domain)
        return {"certificate": cert_info}
    except CertificateError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/acme/status")
async def get_acme_status():
    """Get ACME (Let's Encrypt) status"""
    try:
        status = traefik_manager.get_acme_status()
        return {"acme_status": status}
    except TraefikError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Service Management ====================

@router.get("/services/discover")
async def discover_docker_services():
    """
    Discover Docker services suitable for Traefik routing (C11)

    Scans running Docker containers and suggests Traefik configurations
    for services with traefik.enable=true label.

    Returns:
        List of discoverable services with suggested route configurations
    """
    try:
        import docker

        # Connect to Docker
        try:
            client = docker.from_env()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to Docker: {e}"
            )

        discovered_services = []

        # List all running containers
        containers = client.containers.list()

        for container in containers:
            try:
                # Get container details
                labels = container.labels
                name = container.name
                networks = list(container.attrs['NetworkSettings']['Networks'].keys())

                # Check if Traefik is enabled
                traefik_enabled = labels.get('traefik.enable', '').lower() == 'true'

                # Get exposed ports
                ports_config = container.attrs['NetworkSettings']['Ports'] or {}
                ports = []
                for port_spec, bindings in ports_config.items():
                    if bindings:
                        for binding in bindings:
                            ports.append({
                                'container_port': port_spec,
                                'host_port': binding.get('HostPort', '')
                            })

                # Extract Traefik-specific labels
                traefik_labels = {
                    k: v for k, v in labels.items()
                    if k.startswith('traefik.')
                }

                # Determine suggested configuration
                suggested_host = labels.get('traefik.http.routers.rule', '')
                if not suggested_host and traefik_enabled:
                    # Generate suggestion based on container name
                    suggested_host = f"Host(`{name}.unicorncommander.ai`)"

                suggested_service = labels.get('traefik.http.services.loadbalancer.server.port', '')
                if not suggested_service and ports:
                    # Use first exposed port
                    suggested_service = f"http://{name}:{ports[0]['container_port'].split('/')[0]}"

                service_info = {
                    'container_name': name,
                    'container_id': container.short_id,
                    'networks': networks,
                    'ports': ports,
                    'traefik_enabled': traefik_enabled,
                    'traefik_labels': traefik_labels,
                    'suggested_config': {
                        'route_name': f"{name}-route",
                        'rule': suggested_host or f"Host(`{name}.localhost`)",
                        'service': f"{name}-service",
                        'backend_url': suggested_service or f"http://{name}:80",
                        'entrypoints': ['websecure'],
                        'tls_enabled': True
                    } if traefik_enabled or not traefik_labels else None
                }

                # Only include if relevant for Traefik
                if traefik_enabled or traefik_labels or ports:
                    discovered_services.append(service_info)

            except Exception as e:
                logger.warning(f"Failed to process container {container.name}: {e}")
                continue

        return {
            "discovered_services": discovered_services,
            "count": len(discovered_services),
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to discover services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services")
async def list_services():
    """List all Traefik services"""
    try:
        services = []
        for config_path in traefik_manager.dynamic_dir.glob("*.yml"):
            try:
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)

                if config and 'http' in config and 'services' in config['http']:
                    for name, service in config['http']['services'].items():
                        services.append({
                            'name': name,
                            'type': 'loadBalancer' if 'loadBalancer' in service else 'unknown',
                            'servers': service.get('loadBalancer', {}).get('servers', []),
                            'healthCheck': service.get('loadBalancer', {}).get('healthCheck', None),
                            'source_file': config_path.name
                        })
            except Exception as e:
                logger.warning(f"Failed to parse {config_path.name}: {e}")

        return {"services": services, "count": len(services)}
    except Exception as e:
        logger.error(f"Failed to list services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/services", status_code=201)
async def create_service(service: ServiceCreate):
    """Create a new Traefik service"""
    try:
        import yaml
        services_file = traefik_manager.dynamic_dir / "services.yml"

        if services_file.exists():
            with open(services_file, 'r') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {'http': {'services': {}}}

        if 'http' not in config:
            config['http'] = {}
        if 'services' not in config['http']:
            config['http']['services'] = {}

        if service.name in config['http']['services']:
            raise HTTPException(status_code=400, detail=f"Service '{service.name}' already exists")

        # Build service configuration
        service_config = {
            'loadBalancer': {
                'servers': [{'url': service.url}]
            }
        }

        if service.healthcheck_path:
            service_config['loadBalancer']['healthCheck'] = {
                'path': service.healthcheck_path,
                'interval': '10s',
                'timeout': '3s'
            }

        config['http']['services'][service.name] = service_config

        # Save configuration
        with open(services_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        # Reload Traefik
        traefik_manager.reload_traefik()

        logger.info(f"Service created: {service.name}")

        return {
            'success': True,
            'message': f"Service '{service.name}' created successfully",
            'service': {
                'name': service.name,
                'url': service.url,
                'healthcheck_path': service.healthcheck_path
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/{service_name}")
async def get_service(service_name: str):
    """Get details of a specific service"""
    try:
        import yaml
        for config_path in traefik_manager.dynamic_dir.glob("*.yml"):
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)

                if config and 'http' in config and 'services' in config['http']:
                    if service_name in config['http']['services']:
                        service_data = config['http']['services'][service_name]
                        return {
                            'service': {
                                'name': service_name,
                                'config': service_data,
                                'source_file': config_path.name
                            }
                        }
            except Exception as e:
                logger.warning(f"Failed to parse {config_path.name}: {e}")

        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/services/{service_name}")
async def delete_service(service_name: str):
    """Delete a Traefik service"""
    try:
        import yaml
        deleted = False

        for config_path in traefik_manager.dynamic_dir.glob("*.yml"):
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)

                if config and 'http' in config and 'services' in config['http']:
                    if service_name in config['http']['services']:
                        del config['http']['services'][service_name]

                        with open(config_path, 'w') as f:
                            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

                        deleted = True
                        break
            except Exception as e:
                logger.warning(f"Failed to process {config_path.name}: {e}")

        if not deleted:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

        # Reload Traefik
        traefik_manager.reload_traefik()

        logger.info(f"Service deleted: {service_name}")

        return {
            'success': True,
            'message': f"Service '{service_name}' deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Middleware Management ====================

@router.get("/middlewares")
async def list_middlewares():
    """List all Traefik middlewares"""
    try:
        middleware_list = traefik_manager.list_middleware()
        return {"middlewares": middleware_list, "count": len(middleware_list)}
    except MiddlewareError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/middlewares", status_code=201)
async def create_middleware(middleware: MiddlewareCreate):
    """Create a new Traefik middleware"""
    try:
        result = traefik_manager.create_middleware(
            name=middleware.name,
            type=middleware.type,
            config=middleware.config,
            username="api-user"
        )
        return result
    except MiddlewareError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create middleware: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/middlewares/{middleware_name}")
async def get_middleware(middleware_name: str):
    """Get details of a specific middleware"""
    try:
        middleware_list = traefik_manager.list_middleware()
        middleware = next((m for m in middleware_list if m['name'] == middleware_name), None)

        if not middleware:
            raise HTTPException(status_code=404, detail=f"Middleware '{middleware_name}' not found")

        return {"middleware": middleware}
    except MiddlewareError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/middlewares/{middleware_name}")
async def update_middleware(middleware_name: str, updates: MiddlewareUpdate):
    """Update an existing middleware"""
    try:
        if not updates.config:
            raise HTTPException(status_code=400, detail="No config updates provided")

        result = traefik_manager.update_middleware(
            name=middleware_name,
            config=updates.config,
            username="api-user"
        )
        return result
    except MiddlewareError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update middleware: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/middlewares/{middleware_name}")
async def delete_middleware(middleware_name: str):
    """Delete a Traefik middleware"""
    try:
        result = traefik_manager.delete_middleware(name=middleware_name, username="api-user")
        return result
    except MiddlewareError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete middleware: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Configuration Management ====================

@router.get("/config/summary")
async def get_config_summary():
    """Get Traefik configuration summary"""
    try:
        routes = traefik_manager.list_routes()
        certificates = traefik_manager.list_certificates()

        return {
            "summary": {
                "routes": len(routes),
                "certificates": len(certificates)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except TraefikError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/reload")
async def reload_config():
    """Reload Traefik configuration"""
    try:
        result = traefik_manager.reload_traefik()
        return result
    except TraefikError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/validate")
async def validate_config():
    """Validate Traefik configuration"""
    try:
        is_valid = traefik_manager.validate_config()
        return {
            "valid": is_valid,
            "message": "Configuration is valid" if is_valid else "Configuration is invalid",
            "timestamp": datetime.utcnow().isoformat()
        }
    except ConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to validate config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Dashboard & Metrics (C10, C13) ====================

@router.get("/dashboard")
async def get_traefik_dashboard():
    """
    Get comprehensive Traefik dashboard metrics (C10)

    Aggregates all Traefik metrics for dashboard display:
    - Routes, certificates, services, middleware counts
    - Recent activity and health status
    - System information
    """
    try:
        # Gather all metrics
        routes = traefik_manager.list_routes()
        certificates = traefik_manager.list_certificates()

        # Get services by parsing all dynamic configs
        services = []
        for config_path in traefik_manager.dynamic_dir.glob("*.yml"):
            try:
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                if config and 'http' in config and 'services' in config['http']:
                    for name, service in config['http']['services'].items():
                        services.append({
                            'name': name,
                            'type': 'loadBalancer' if 'loadBalancer' in service else 'unknown',
                            'servers': service.get('loadBalancer', {}).get('servers', []),
                            'source_file': config_path.name
                        })
            except Exception as e:
                logger.warning(f"Failed to parse {config_path.name}: {e}")

        # Get middleware
        middleware_list = traefik_manager.list_middleware()

        # Get ACME status
        acme_status = traefik_manager.get_acme_status()

        # Calculate health metrics
        active_certs = sum(1 for cert in certificates if cert.get('status') == 'active')
        expired_certs = sum(1 for cert in certificates if cert.get('status') == 'expired')

        # Build dashboard response
        dashboard = {
            "summary": {
                "routes": len(routes),
                "certificates": len(certificates),
                "services": len(services),
                "middlewares": len(middleware_list)
            },
            "certificate_health": {
                "total": len(certificates),
                "active": active_certs,
                "expired": expired_certs,
                "pending": len(certificates) - active_certs - expired_certs
            },
            "acme": {
                "initialized": acme_status.get('initialized', False),
                "resolvers": len(acme_status.get('resolvers', []))
            },
            "recent_activity": {
                "last_config_change": datetime.utcnow().isoformat(),
                "total_configurations": len(list(traefik_manager.dynamic_dir.glob("*.yml")))
            },
            "health_status": "healthy" if len(routes) > 0 else "no_routes",
            "timestamp": datetime.utcnow().isoformat()
        }

        return dashboard

    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_traefik_metrics(format: str = Query(default="json", regex="^(json|csv)$")):
    """
    Get Traefik metrics with optional CSV export (C13)

    Query Parameters:
        format: Response format - 'json' (default) or 'csv'

    Returns:
        JSON or CSV formatted metrics
    """
    try:
        from fastapi.responses import StreamingResponse
        import io

        # Gather metrics
        routes = traefik_manager.list_routes()
        certificates = traefik_manager.list_certificates()
        services = []
        middleware = traefik_manager.list_middleware()

        # Parse services from configs
        for config_path in traefik_manager.dynamic_dir.glob("*.yml"):
            try:
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                if config and 'http' in config and 'services' in config['http']:
                    services.extend(config['http']['services'].keys())
            except Exception:
                pass

        # Build metrics
        metrics_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": [
                {"name": "routes_total", "value": len(routes), "unit": "count"},
                {"name": "certificates_total", "value": len(certificates), "unit": "count"},
                {"name": "services_total", "value": len(services), "unit": "count"},
                {"name": "middlewares_total", "value": len(middleware), "unit": "count"},
                {"name": "routes_with_tls", "value": sum(1 for r in routes if r.get('tls_enabled')), "unit": "count"},
                {"name": "certificates_active", "value": sum(1 for c in certificates if c.get('status') == 'active'), "unit": "count"},
                {"name": "certificates_expired", "value": sum(1 for c in certificates if c.get('status') == 'expired'), "unit": "count"}
            ]
        }

        # Return CSV if requested
        if format == "csv":
            import csv
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(["timestamp", "metric_name", "value", "unit"])

            # Write metrics
            timestamp = metrics_data["timestamp"]
            for metric in metrics_data["metrics"]:
                writer.writerow([
                    timestamp,
                    metric["name"],
                    metric["value"],
                    metric["unit"]
                ])

            # Return CSV response
            output.seek(0)
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=traefik_metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
            )

        # Return JSON by default
        return metrics_data

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SSL Certificate Renewal (C12) ====================

@router.post("/ssl/renew/bulk")
async def renew_certificates_bulk(certificate_ids: List[str]):
    """
    Renew multiple SSL certificates in bulk (C12)

    Request Body:
        certificate_ids: Array of certificate domain names or IDs

    Returns:
        Bulk renewal results with success/failure counts
    """
    try:
        import asyncio

        results = {
            "total": len(certificate_ids),
            "successful": 0,
            "failed": 0,
            "results": []
        }

        for cert_id in certificate_ids:
            try:
                # Attempt renewal
                renewal = await renew_certificate(cert_id)
                results["successful"] += 1
                results["results"].append({
                    "certificate_id": cert_id,
                    "status": "success",
                    "result": renewal
                })

            except HTTPException as e:
                results["failed"] += 1
                results["results"].append({
                    "certificate_id": cert_id,
                    "status": "failed",
                    "error": e.detail
                })
                logger.error(f"Bulk renewal failed for {cert_id}: {e.detail}")

            except Exception as e:
                results["failed"] += 1
                results["results"].append({
                    "certificate_id": cert_id,
                    "status": "failed",
                    "error": str(e)
                })
                logger.error(f"Bulk renewal failed for {cert_id}: {e}")

        return {
            "success": results["failed"] == 0,
            "summary": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Bulk certificate renewal failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ssl/renew/{certificate_id}")
async def renew_certificate(certificate_id: str):
    """
    Renew a single SSL certificate (C12)

    Args:
        certificate_id: Certificate domain name or ID

    Returns:
        Renewal result with new expiry date
    """
    try:
        # Get certificate info
        certificates = traefik_manager.list_certificates()
        cert = None

        for c in certificates:
            if c['domain'] == certificate_id or certificate_id in c.get('sans', []):
                cert = c
                break

        if not cert:
            raise HTTPException(
                status_code=404,
                detail=f"Certificate not found: {certificate_id}"
            )

        domain = cert['domain']

        # Revoke old certificate to trigger renewal
        logger.info(f"Revoking certificate for renewal: {domain}")
        revoke_result = traefik_manager.revoke_certificate(domain, username="api-admin")

        # Request new certificate
        logger.info(f"Requesting new certificate: {domain}")

        # Extract email from ACME config
        config = traefik_manager.get_config()
        email = config.get('certificatesResolvers', {}).get('letsencrypt', {}).get('acme', {}).get('email', 'admin@unicorncommander.ai')

        renewal_result = traefik_manager.request_certificate(
            domain=domain,
            email=email,
            sans=cert.get('sans', []),
            username="api-admin"
        )

        return {
            "success": True,
            "message": f"Certificate renewal initiated for {domain}",
            "domain": domain,
            "status": "pending",
            "revoke_result": revoke_result,
            "renewal_result": renewal_result,
            "note": "Certificate will be automatically issued when ACME challenge is completed",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to renew certificate {certificate_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


logger.info("Traefik Management API (Epic 1.3) initialized - Full CRUD version with Dashboard, Metrics, Discovery, and SSL Renewal")
