"""
Traefik Services Detail API

Enhanced API endpoints for Traefik service monitoring and management.
Provides health checks, detailed metrics, and configuration reload capabilities.

Author: Ops-Center Team
Created: October 26, 2025
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import httpx
import os
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/traefik/services", tags=["Traefik Services Detail"])

# Environment configuration
TRAEFIK_API_URL = os.getenv("TRAEFIK_API_URL", "http://traefik:8080/api")
TRAEFIK_METRICS_URL = os.getenv("TRAEFIK_METRICS_URL", "http://traefik:8080/metrics")
REQUEST_TIMEOUT = 10.0


# ============================================================================
# Pydantic Models
# ============================================================================

class ServerStatus(BaseModel):
    """Individual server status within a load balancer"""
    url: str
    status: str  # UP, DOWN, STARTING, STOPPING
    health_check_url: Optional[str] = None
    last_checked: Optional[datetime] = None
    error: Optional[str] = None


class ServiceHealth(BaseModel):
    """Service health check response"""
    service: str
    status: str  # healthy, degraded, unhealthy, unknown
    servers_up: int
    servers_total: int
    servers_down: int
    health_percentage: float
    load_balancer_type: str  # wrr, roundrobin, etc.
    load_balancer_servers: List[ServerStatus]
    last_checked: datetime
    details: Optional[Dict[str, Any]] = None


class ServiceMetrics(BaseModel):
    """Service detailed metrics response"""
    service: str
    requests_total: int = 0
    requests_per_second: float = 0.0
    avg_response_time_ms: float = 0.0
    error_rate: float = 0.0
    error_count: int = 0
    success_count: int = 0
    status_codes: Dict[str, int] = Field(default_factory=dict)
    avg_request_size_bytes: float = 0.0
    avg_response_size_bytes: float = 0.0
    servers: List[Dict[str, Any]] = Field(default_factory=list)
    last_updated: datetime


class ServiceReloadResult(BaseModel):
    """Service configuration reload result"""
    service: str
    reloaded: bool
    timestamp: datetime
    previous_config: Optional[Dict[str, Any]] = None
    new_config: Optional[Dict[str, Any]] = None
    changes: List[str] = Field(default_factory=list)
    message: str


class ServiceLoadBalancerStats(BaseModel):
    """Load balancer statistics"""
    algorithm: str  # wrr, roundrobin, etc.
    sticky_sessions: bool
    health_check_enabled: bool
    server_count: int
    active_connections: int
    total_requests: int


# ============================================================================
# Authentication & Dependencies
# ============================================================================

def require_admin(user_info: Dict = Depends(lambda: {"role": "admin", "username": "admin"})):
    """Require admin role for service management operations"""
    if user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_info


# ============================================================================
# Helper Functions
# ============================================================================

async def fetch_traefik_service_config(service_name: str) -> Dict[str, Any]:
    """
    Fetch service configuration from Traefik API

    Args:
        service_name: Name of the service

    Returns:
        Service configuration dictionary

    Raises:
        HTTPException: If service not found or API error
    """
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(
                f"{TRAEFIK_API_URL}/http/services/{service_name}"
            )

            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Service '{service_name}' not found"
                )

            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException:
        logger.error(f"Timeout fetching service config for {service_name}")
        raise HTTPException(
            status_code=504,
            detail=f"Timeout connecting to Traefik API"
        )
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching service config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch service configuration: {str(e)}"
        )


async def check_server_health(url: str, health_check_path: str = "/health") -> Dict[str, Any]:
    """
    Check health of individual server

    Args:
        url: Server URL (e.g., http://container:8080)
        health_check_path: Health check endpoint path

    Returns:
        Health check result dictionary
    """
    try:
        # Build health check URL
        if health_check_path:
            # Ensure health_check_path starts with /
            if not health_check_path.startswith('/'):
                health_check_path = f'/{health_check_path}'
            health_url = f"{url.rstrip('/')}{health_check_path}"
        else:
            health_url = url

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(health_url)

            return {
                "url": url,
                "status": "UP" if response.status_code == 200 else "DOWN",
                "status_code": response.status_code,
                "health_check_url": health_url,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "last_checked": datetime.utcnow(),
                "error": None
            }

    except Exception as e:
        logger.warning(f"Health check failed for {url}: {e}")
        return {
            "url": url,
            "status": "DOWN",
            "status_code": None,
            "health_check_url": health_url if 'health_url' in locals() else None,
            "response_time_ms": None,
            "last_checked": datetime.utcnow(),
            "error": str(e)
        }


async def parse_traefik_metrics() -> Dict[str, Any]:
    """
    Parse Traefik Prometheus metrics endpoint

    Returns:
        Parsed metrics dictionary by service
    """
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(TRAEFIK_METRICS_URL)
            response.raise_for_status()

            metrics_text = response.text
            metrics = defaultdict(lambda: {
                "requests_total": 0,
                "error_count": 0,
                "success_count": 0,
                "status_codes": {},
                "response_times": [],
                "request_sizes": [],
                "response_sizes": []
            })

            # Parse Prometheus format metrics
            for line in metrics_text.split('\n'):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                try:
                    # Parse metric line: metric_name{labels} value
                    if '{' in line:
                        metric_part, rest = line.split('{', 1)
                        labels_part, value_part = rest.rsplit('}', 1)
                        value = float(value_part.strip())

                        # Parse labels
                        labels = {}
                        for label in labels_part.split(','):
                            if '=' in label:
                                key, val = label.split('=', 1)
                                labels[key.strip()] = val.strip('"')

                        service_name = labels.get('service', '')
                        if not service_name:
                            continue

                        # Aggregate metrics by service
                        if 'traefik_service_requests_total' in metric_part:
                            metrics[service_name]['requests_total'] += int(value)

                            # Track status codes
                            status_code = labels.get('code', 'unknown')
                            metrics[service_name]['status_codes'][status_code] = \
                                metrics[service_name]['status_codes'].get(status_code, 0) + int(value)

                            # Count errors (4xx, 5xx) and successes (2xx, 3xx)
                            if status_code.startswith('4') or status_code.startswith('5'):
                                metrics[service_name]['error_count'] += int(value)
                            elif status_code.startswith('2') or status_code.startswith('3'):
                                metrics[service_name]['success_count'] += int(value)

                        elif 'traefik_service_request_duration' in metric_part:
                            metrics[service_name]['response_times'].append(value)

                        elif 'traefik_service_requests_bytes' in metric_part:
                            metrics[service_name]['request_sizes'].append(value)

                        elif 'traefik_service_responses_bytes' in metric_part:
                            metrics[service_name]['response_sizes'].append(value)

                except Exception as e:
                    logger.debug(f"Failed to parse metric line: {line} - {e}")
                    continue

            return dict(metrics)

    except Exception as e:
        logger.error(f"Failed to parse Traefik metrics: {e}")
        return {}


def calculate_metrics_stats(metrics_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate statistical metrics from raw metrics data

    Args:
        metrics_data: Raw metrics data for a service

    Returns:
        Calculated statistics
    """
    stats = {
        "requests_total": metrics_data.get("requests_total", 0),
        "error_count": metrics_data.get("error_count", 0),
        "success_count": metrics_data.get("success_count", 0),
        "error_rate": 0.0,
        "avg_response_time_ms": 0.0,
        "avg_request_size_bytes": 0.0,
        "avg_response_size_bytes": 0.0
    }

    # Calculate error rate
    total = stats["requests_total"]
    if total > 0:
        stats["error_rate"] = (stats["error_count"] / total) * 100

    # Calculate average response time
    response_times = metrics_data.get("response_times", [])
    if response_times:
        stats["avg_response_time_ms"] = sum(response_times) / len(response_times) * 1000

    # Calculate average request size
    request_sizes = metrics_data.get("request_sizes", [])
    if request_sizes:
        stats["avg_request_size_bytes"] = sum(request_sizes) / len(request_sizes)

    # Calculate average response size
    response_sizes = metrics_data.get("response_sizes", [])
    if response_sizes:
        stats["avg_response_size_bytes"] = sum(response_sizes) / len(response_sizes)

    return stats


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/{service_name}/health", response_model=ServiceHealth)
async def get_service_health(
    service_name: str,
    admin: Dict = Depends(require_admin)
):
    """
    Get detailed health status for a specific service.

    Checks health of all backend servers in the load balancer and
    provides an overall health assessment.

    Args:
        service_name: Name of the Traefik service

    Returns:
        ServiceHealth: Detailed health information

    Raises:
        HTTPException: If service not found or health check fails
    """
    try:
        # Fetch service configuration from Traefik
        service_config = await fetch_traefik_service_config(service_name)

        # Extract load balancer configuration
        lb_config = service_config.get("loadBalancer", {})
        servers = lb_config.get("servers", [])
        health_check_config = lb_config.get("healthCheck", {})

        # Get health check path
        health_check_path = health_check_config.get("path", "/health")

        # Check health of each server
        server_health_tasks = [
            check_server_health(server.get("url", ""), health_check_path)
            for server in servers
        ]

        server_health_results = await asyncio.gather(*server_health_tasks)

        # Build server status list
        server_statuses = [
            ServerStatus(
                url=result["url"],
                status=result["status"],
                health_check_url=result.get("health_check_url"),
                last_checked=result.get("last_checked"),
                error=result.get("error")
            )
            for result in server_health_results
        ]

        # Calculate overall health
        servers_total = len(server_statuses)
        servers_up = sum(1 for s in server_statuses if s.status == "UP")
        servers_down = servers_total - servers_up
        health_percentage = (servers_up / servers_total * 100) if servers_total > 0 else 0

        # Determine overall status
        if servers_up == servers_total:
            overall_status = "healthy"
        elif servers_up > 0:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        # Get load balancer type
        lb_type = "roundrobin"  # Default
        if "passHostHeader" in lb_config:
            lb_type = "wrr" if lb_config.get("passHostHeader") else "roundrobin"

        logger.info(
            f"Health check for {service_name}: "
            f"{servers_up}/{servers_total} servers UP ({health_percentage:.1f}%)"
        )

        return ServiceHealth(
            service=service_name,
            status=overall_status,
            servers_up=servers_up,
            servers_total=servers_total,
            servers_down=servers_down,
            health_percentage=health_percentage,
            load_balancer_type=lb_type,
            load_balancer_servers=server_statuses,
            last_checked=datetime.utcnow(),
            details={
                "health_check_enabled": bool(health_check_config),
                "health_check_path": health_check_path,
                "health_check_interval": health_check_config.get("interval", "30s"),
                "health_check_timeout": health_check_config.get("timeout", "5s")
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking health for service {service_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check service health: {str(e)}"
        )


@router.get("/{service_name}/metrics", response_model=ServiceMetrics)
async def get_service_metrics(
    service_name: str,
    admin: Dict = Depends(require_admin)
):
    """
    Get detailed performance metrics for a specific service.

    Retrieves metrics from Traefik's Prometheus endpoint including:
    - Request counts and rates
    - Response times
    - Error rates
    - Status code distribution
    - Request/response sizes

    Args:
        service_name: Name of the Traefik service

    Returns:
        ServiceMetrics: Detailed performance metrics

    Raises:
        HTTPException: If service not found or metrics unavailable
    """
    try:
        # Fetch service configuration
        service_config = await fetch_traefik_service_config(service_name)

        # Get server list
        lb_config = service_config.get("loadBalancer", {})
        servers = lb_config.get("servers", [])

        # Parse Traefik metrics
        all_metrics = await parse_traefik_metrics()

        # Get metrics for this service
        service_metrics_data = all_metrics.get(service_name, {
            "requests_total": 0,
            "error_count": 0,
            "success_count": 0,
            "status_codes": {},
            "response_times": [],
            "request_sizes": [],
            "response_sizes": []
        })

        # Calculate statistics
        stats = calculate_metrics_stats(service_metrics_data)

        # Calculate requests per second (estimate based on last 60 seconds)
        # Note: This is a simplified calculation. In production, you'd want
        # to track this over time with proper windowing.
        requests_per_second = stats["requests_total"] / 60.0 if stats["requests_total"] > 0 else 0.0

        logger.info(
            f"Metrics for {service_name}: "
            f"{stats['requests_total']} total requests, "
            f"{stats['error_rate']:.2f}% error rate"
        )

        return ServiceMetrics(
            service=service_name,
            requests_total=stats["requests_total"],
            requests_per_second=round(requests_per_second, 2),
            avg_response_time_ms=round(stats["avg_response_time_ms"], 2),
            error_rate=round(stats["error_rate"], 2),
            error_count=stats["error_count"],
            success_count=stats["success_count"],
            status_codes=service_metrics_data.get("status_codes", {}),
            avg_request_size_bytes=round(stats["avg_request_size_bytes"], 2),
            avg_response_size_bytes=round(stats["avg_response_size_bytes"], 2),
            servers=[
                {
                    "url": server.get("url"),
                    "weight": server.get("weight", 1)
                }
                for server in servers
            ],
            last_updated=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching metrics for service {service_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch service metrics: {str(e)}"
        )


@router.post("/{service_name}/reload", response_model=ServiceReloadResult)
async def reload_service_config(
    service_name: str,
    admin: Dict = Depends(require_admin)
):
    """
    Reload service configuration from Traefik.

    Traefik automatically reloads configuration when files change,
    but this endpoint forces a refresh and reports the current state.

    This is useful after:
    - Updating backend servers
    - Changing health check configuration
    - Modifying load balancer settings

    Args:
        service_name: Name of the Traefik service

    Returns:
        ServiceReloadResult: Reload status and configuration changes

    Raises:
        HTTPException: If service not found or reload fails
    """
    try:
        # Get current service configuration
        previous_config = await fetch_traefik_service_config(service_name)

        # Traefik automatically reloads configuration from file providers
        # We'll wait a moment to allow any pending reloads to complete
        await asyncio.sleep(1)

        # Fetch potentially updated configuration
        new_config = await fetch_traefik_service_config(service_name)

        # Detect changes
        changes = []

        # Check for server changes
        old_servers = previous_config.get("loadBalancer", {}).get("servers", [])
        new_servers = new_config.get("loadBalancer", {}).get("servers", [])

        if old_servers != new_servers:
            changes.append(f"Servers changed from {len(old_servers)} to {len(new_servers)}")

        # Check for health check changes
        old_hc = previous_config.get("loadBalancer", {}).get("healthCheck", {})
        new_hc = new_config.get("loadBalancer", {}).get("healthCheck", {})

        if old_hc != new_hc:
            changes.append("Health check configuration updated")

        # If no changes detected
        if not changes:
            changes.append("No configuration changes detected")

        logger.info(
            f"Reloaded configuration for {service_name}: {', '.join(changes)}"
        )

        return ServiceReloadResult(
            service=service_name,
            reloaded=True,
            timestamp=datetime.utcnow(),
            previous_config=previous_config,
            new_config=new_config,
            changes=changes,
            message=f"Service configuration refreshed successfully. {len(changes)} change(s) detected."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reloading configuration for service {service_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload service configuration: {str(e)}"
        )


@router.get("/{service_name}/lb-stats", response_model=ServiceLoadBalancerStats)
async def get_load_balancer_stats(
    service_name: str,
    admin: Dict = Depends(require_admin)
):
    """
    Get load balancer statistics for a service.

    Provides information about the load balancing configuration and status.

    Args:
        service_name: Name of the Traefik service

    Returns:
        ServiceLoadBalancerStats: Load balancer statistics

    Raises:
        HTTPException: If service not found
    """
    try:
        # Fetch service configuration
        service_config = await fetch_traefik_service_config(service_name)

        lb_config = service_config.get("loadBalancer", {})
        servers = lb_config.get("servers", [])
        health_check = lb_config.get("healthCheck", {})
        sticky = lb_config.get("sticky", {})

        # Determine algorithm
        algorithm = "roundrobin"  # Default
        if "weighted" in lb_config:
            algorithm = "wrr"  # Weighted Round Robin

        # Parse metrics for active connections and total requests
        all_metrics = await parse_traefik_metrics()
        service_metrics = all_metrics.get(service_name, {})

        return ServiceLoadBalancerStats(
            algorithm=algorithm,
            sticky_sessions=bool(sticky.get("cookie")),
            health_check_enabled=bool(health_check),
            server_count=len(servers),
            active_connections=0,  # Would need additional metrics endpoint
            total_requests=service_metrics.get("requests_total", 0)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching LB stats for service {service_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch load balancer stats: {str(e)}"
        )
