"""
Traefik Live Data API

Reads REAL Traefik routes from Docker container labels and Traefik dynamic config.
This provides actual production data instead of mock/static data.

Author: Backend API Developer Agent
Date: October 30, 2025
Epic: Traefik Dashboard - Live Data Integration
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import subprocess
import json
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/traefik/live", tags=["Traefik Live Data"])


class LiveRoute(BaseModel):
    """Live Traefik route from Docker labels"""
    name: str
    rule: str
    service: str
    entrypoints: List[str]
    middlewares: Optional[List[str]] = None
    priority: Optional[int] = None
    tls: Optional[Dict[str, Any]] = None
    container: str
    status: str = "active"


class LiveService(BaseModel):
    """Live Traefik service"""
    name: str
    url: str
    container: str
    port: Optional[int] = None
    loadBalancer: Optional[Dict[str, Any]] = None


class LiveMiddleware(BaseModel):
    """Live Traefik middleware"""
    name: str
    type: str
    config: Dict[str, Any]


class TraefikOverview(BaseModel):
    """Traefik overview statistics"""
    routes_count: int
    services_count: int
    middlewares_count: int
    containers_with_traefik: int
    tls_routes_count: int
    http_routes_count: int
    timestamp: str


def parse_traefik_labels(container_name: str, labels: Dict[str, str]) -> Dict[str, Any]:
    """
    Parse Traefik labels from a container.

    Args:
        container_name: Name of the container
        labels: Docker labels dictionary

    Returns:
        Dictionary with parsed routers, services, and middlewares
    """
    routers = {}
    services = {}
    middlewares = {}

    # Parse router labels
    router_names = set()
    for key in labels.keys():
        if key.startswith("traefik.http.routers."):
            parts = key.split(".")
            if len(parts) >= 4:
                router_name = parts[3]
                router_names.add(router_name)

    # Extract router configurations
    for router_name in router_names:
        router_config = {
            "name": router_name,
            "container": container_name,
            "entrypoints": [],
            "middlewares": []
        }

        # Get all properties for this router
        for key, value in labels.items():
            if key.startswith(f"traefik.http.routers.{router_name}."):
                prop = key.split(".")[-1]

                if prop == "rule":
                    router_config["rule"] = value
                elif prop == "service":
                    router_config["service"] = value
                elif prop == "entrypoints":
                    router_config["entrypoints"] = value.split(",")
                elif prop == "middlewares":
                    router_config["middlewares"] = value.split(",")
                elif prop == "priority":
                    router_config["priority"] = int(value)
                elif prop == "tls":
                    if value.lower() in ("true", "1"):
                        router_config["tls"] = {"enabled": True}
                elif prop == "certresolver":
                    if "tls" not in router_config:
                        router_config["tls"] = {}
                    router_config["tls"]["certResolver"] = value

        # Only include routers with at least a rule
        if "rule" in router_config:
            routers[router_name] = router_config

    # Parse service labels
    service_names = set()
    for key in labels.keys():
        if key.startswith("traefik.http.services."):
            parts = key.split(".")
            if len(parts) >= 4:
                service_name = parts[3]
                service_names.add(service_name)

    # Extract service configurations
    for service_name in service_names:
        service_config = {
            "name": service_name,
            "container": container_name
        }

        for key, value in labels.items():
            if key.startswith(f"traefik.http.services.{service_name}."):
                if "loadbalancer.server.port" in key:
                    service_config["port"] = int(value)
                    service_config["url"] = f"http://{container_name}:{value}"
                elif "loadbalancer" in key:
                    if "loadBalancer" not in service_config:
                        service_config["loadBalancer"] = {}
                    # Parse loadbalancer config
                    prop = key.split(".")[-1]
                    service_config["loadBalancer"][prop] = value

        if "url" in service_config:
            services[service_name] = service_config

    # Parse middleware labels
    middleware_names = set()
    for key in labels.keys():
        if key.startswith("traefik.http.middlewares."):
            parts = key.split(".")
            if len(parts) >= 4:
                middleware_name = parts[3]
                middleware_names.add(middleware_name)

    # Extract middleware configurations
    for middleware_name in middleware_names:
        middleware_config = {
            "name": middleware_name,
            "config": {}
        }

        # Determine middleware type
        middleware_type = None
        for key in labels.keys():
            if key.startswith(f"traefik.http.middlewares.{middleware_name}."):
                parts = key.split(".")
                if len(parts) >= 5:
                    middleware_type = parts[4]
                    break

        if middleware_type:
            middleware_config["type"] = middleware_type

            # Get all config for this middleware
            for key, value in labels.items():
                if key.startswith(f"traefik.http.middlewares.{middleware_name}.{middleware_type}."):
                    prop = key.split(".")[-1]
                    middleware_config["config"][prop] = value

            middlewares[middleware_name] = middleware_config

    return {
        "routers": routers,
        "services": services,
        "middlewares": middlewares
    }


def get_docker_containers_with_traefik() -> List[Dict[str, Any]]:
    """
    Get all Docker containers with Traefik labels.

    Returns:
        List of containers with their Traefik configurations
    """
    try:
        # Get all running containers
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )

        container_names = [name.strip() for name in result.stdout.split("\n") if name.strip()]

        containers_data = []

        for container_name in container_names:
            try:
                # Get container labels
                result = subprocess.run(
                    ["docker", "inspect", container_name, "--format", "{{json .Config.Labels}}"],
                    capture_output=True,
                    text=True,
                    check=True
                )

                labels = json.loads(result.stdout.strip())

                # Check if container has Traefik labels
                has_traefik = any(key.startswith("traefik") for key in labels.keys())

                if has_traefik and labels.get("traefik.enable") in ("true", "True", "1"):
                    parsed = parse_traefik_labels(container_name, labels)
                    if parsed["routers"] or parsed["services"] or parsed["middlewares"]:
                        containers_data.append({
                            "container": container_name,
                            "labels": labels,
                            "parsed": parsed
                        })
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to inspect container {container_name}: {e}")
                continue
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse labels for {container_name}: {e}")
                continue

        return containers_data

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to list Docker containers: {e}")
        raise HTTPException(status_code=500, detail="Failed to query Docker containers")


@router.get("/overview", response_model=TraefikOverview)
async def get_live_overview():
    """
    Get overview statistics of live Traefik configuration.

    Returns:
        Overview with route, service, and middleware counts
    """
    try:
        containers_data = get_docker_containers_with_traefik()

        total_routes = 0
        total_services = 0
        total_middlewares = 0
        tls_routes = 0
        http_routes = 0

        for container in containers_data:
            parsed = container["parsed"]
            total_routes += len(parsed["routers"])
            total_services += len(parsed["services"])
            total_middlewares += len(parsed["middlewares"])

            # Count TLS vs HTTP routes
            for router in parsed["routers"].values():
                if router.get("tls"):
                    tls_routes += 1
                else:
                    http_routes += 1

        return TraefikOverview(
            routes_count=total_routes,
            services_count=total_services,
            middlewares_count=total_middlewares,
            containers_with_traefik=len(containers_data),
            tls_routes_count=tls_routes,
            http_routes_count=http_routes,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Failed to get live overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routes", response_model=List[LiveRoute])
async def get_live_routes():
    """
    Get all live Traefik routes from Docker container labels.

    Returns:
        List of active routes with full configuration
    """
    try:
        containers_data = get_docker_containers_with_traefik()

        routes = []

        for container in containers_data:
            parsed = container["parsed"]

            for router_name, router_config in parsed["routers"].items():
                routes.append(LiveRoute(
                    name=router_name,
                    rule=router_config.get("rule", ""),
                    service=router_config.get("service", ""),
                    entrypoints=router_config.get("entrypoints", []),
                    middlewares=router_config.get("middlewares") if router_config.get("middlewares") else None,
                    priority=router_config.get("priority"),
                    tls=router_config.get("tls"),
                    container=router_config["container"],
                    status="active"
                ))

        # Sort by name
        routes.sort(key=lambda r: r.name)

        return routes

    except Exception as e:
        logger.error(f"Failed to get live routes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services", response_model=List[LiveService])
async def get_live_services():
    """
    Get all live Traefik services from Docker container labels.

    Returns:
        List of active services
    """
    try:
        containers_data = get_docker_containers_with_traefik()

        services = []

        for container in containers_data:
            parsed = container["parsed"]

            for service_name, service_config in parsed["services"].items():
                services.append(LiveService(
                    name=service_name,
                    url=service_config.get("url", ""),
                    container=service_config["container"],
                    port=service_config.get("port"),
                    loadBalancer=service_config.get("loadBalancer")
                ))

        # Sort by name
        services.sort(key=lambda s: s.name)

        return services

    except Exception as e:
        logger.error(f"Failed to get live services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/middlewares", response_model=List[LiveMiddleware])
async def get_live_middlewares():
    """
    Get all live Traefik middlewares from Docker container labels.

    Returns:
        List of active middlewares
    """
    try:
        containers_data = get_docker_containers_with_traefik()

        middlewares = []

        for container in containers_data:
            parsed = container["parsed"]

            for middleware_name, middleware_config in parsed["middlewares"].items():
                middlewares.append(LiveMiddleware(
                    name=middleware_name,
                    type=middleware_config.get("type", "unknown"),
                    config=middleware_config.get("config", {})
                ))

        # Sort by name
        middlewares.sort(key=lambda m: m.name)

        return middlewares

    except Exception as e:
        logger.error(f"Failed to get live middlewares: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routes/{route_name}")
async def get_live_route_detail(route_name: str):
    """
    Get detailed information about a specific route.

    Args:
        route_name: Name of the route

    Returns:
        Detailed route information
    """
    try:
        containers_data = get_docker_containers_with_traefik()

        for container in containers_data:
            parsed = container["parsed"]

            if route_name in parsed["routers"]:
                router_config = parsed["routers"][route_name]

                # Get associated service details
                service_name = router_config.get("service")
                service_details = None
                if service_name and service_name in parsed["services"]:
                    service_details = parsed["services"][service_name]

                return {
                    "route": router_config,
                    "service": service_details,
                    "container": container["container"],
                    "raw_labels": {k: v for k, v in container["labels"].items()
                                 if k.startswith(f"traefik.http.routers.{route_name}.")}
                }

        raise HTTPException(status_code=404, detail=f"Route '{route_name}' not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get route detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "traefik-live-data-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


class DomainStatus(BaseModel):
    """Domain health status"""
    domain: str
    status: str  # up, down, unknown
    response_time_ms: Optional[int] = None
    status_code: Optional[int] = None
    error: Optional[str] = None


@router.get("/website-status", response_model=Dict[str, DomainStatus])
async def get_website_status():
    """
    Quick health check for all domains from Traefik routes.
    Returns status for each unique domain.

    Note: This does quick HTTP HEAD requests with short timeouts.
    For comprehensive monitoring, use the website-monitor API.
    """
    import httpx
    import asyncio

    containers_data = get_docker_containers_with_traefik()

    # Extract unique domains from routes
    domains = set()
    for container in containers_data:
        parsed = container["parsed"]
        for router_config in parsed["routers"].values():
            rule = router_config.get("rule", "")
            # Extract domain from Host(`domain.com`)
            match = re.search(r"Host\(`([^`]+)`\)", rule)
            if match:
                domains.add(match.group(1))

    async def check_domain(domain: str) -> DomainStatus:
        """Check a single domain's health"""
        # Determine protocol based on common patterns
        url = f"https://{domain}"

        try:
            async with httpx.AsyncClient(timeout=5.0, verify=False, follow_redirects=True) as client:
                start = datetime.utcnow()
                response = await client.head(url)
                elapsed = (datetime.utcnow() - start).total_seconds() * 1000

                return DomainStatus(
                    domain=domain,
                    status="up" if response.status_code < 500 else "down",
                    response_time_ms=int(elapsed),
                    status_code=response.status_code
                )
        except httpx.ConnectError:
            return DomainStatus(domain=domain, status="down", error="Connection refused")
        except httpx.TimeoutException:
            return DomainStatus(domain=domain, status="down", error="Timeout")
        except Exception as e:
            return DomainStatus(domain=domain, status="unknown", error=str(e)[:100])

    # Check all domains concurrently (limit concurrency to avoid overwhelming)
    semaphore = asyncio.Semaphore(10)

    async def limited_check(domain):
        async with semaphore:
            return await check_domain(domain)

    results = await asyncio.gather(*[limited_check(d) for d in domains])

    return {status.domain: status for status in results}
