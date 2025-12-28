"""
Traefik Metrics API

Expose Traefik metrics from Prometheus endpoint.
Provides route performance, error rates, and traffic statistics.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/traefik/metrics", tags=["Traefik Metrics"])

# Traefik Prometheus metrics endpoint
TRAEFIK_METRICS_URL = "http://traefik:8082/metrics"


class RouteMetrics(BaseModel):
    """Metrics for a specific route"""
    route_name: str
    service_name: str
    request_count: int = 0
    avg_response_time_ms: float = 0.0
    error_count: int = 0
    error_rate: float = 0.0
    status_codes: Dict[str, int] = Field(default_factory=dict)


class TraefikStats(BaseModel):
    """Overall Traefik statistics"""
    total_requests: int
    active_connections: int
    total_routers: int
    total_services: int
    total_middlewares: int
    uptime_seconds: int


class ServiceHealth(BaseModel):
    """Backend service health status"""
    service_name: str
    server_url: str
    status: str  # up, down, unknown
    response_time_ms: Optional[float] = None
    last_check: str


def require_admin(user_info: Dict = Depends(lambda: {"role": "admin", "username": "admin"})):
    """Require admin role"""
    if user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_info


async def fetch_prometheus_metrics() -> str:
    """
    Fetch raw Prometheus metrics from Traefik.

    Returns:
        Raw metrics text
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(TRAEFIK_METRICS_URL, timeout=10.0)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as e:
        logger.error(f"Error fetching Traefik metrics: {e}")
        raise HTTPException(status_code=503, detail="Traefik metrics endpoint unavailable")
    except Exception as e:
        logger.error(f"Unexpected error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def parse_prometheus_metrics(metrics_text: str) -> Dict[str, Any]:
    """
    Parse Prometheus metrics text format.

    Args:
        metrics_text: Raw Prometheus metrics

    Returns:
        Parsed metrics dictionary
    """
    parsed = {
        "requests": {},
        "durations": {},
        "connections": 0,
        "routers": 0,
        "services": 0,
        "middlewares": 0
    }

    for line in metrics_text.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        try:
            # Parse metric line: metric_name{labels} value
            if '{' in line:
                metric_name = line.split('{')[0]
                labels_and_value = line.split('{')[1]
                labels_str = labels_and_value.split('}')[0]
                value = float(labels_and_value.split('}')[1].strip())

                # Parse labels
                labels = {}
                for label in labels_str.split(','):
                    if '=' in label:
                        key, val = label.split('=', 1)
                        labels[key.strip()] = val.strip('"')

                # Store based on metric type
                if 'request' in metric_name:
                    router = labels.get('router', 'unknown')
                    service = labels.get('service', 'unknown')
                    code = labels.get('code', 'unknown')

                    if router not in parsed['requests']:
                        parsed['requests'][router] = {
                            'service': service,
                            'total': 0,
                            'codes': {}
                        }

                    parsed['requests'][router]['total'] += int(value)
                    parsed['requests'][router]['codes'][code] = int(value)

                elif 'duration' in metric_name:
                    router = labels.get('router', 'unknown')
                    if router not in parsed['durations']:
                        parsed['durations'][router] = 0
                    parsed['durations'][router] = value

            else:
                # Simple metric without labels
                parts = line.split()
                if len(parts) == 2:
                    metric_name, value = parts
                    if 'connection' in metric_name:
                        parsed['connections'] = int(float(value))
                    elif 'router' in metric_name and 'total' in metric_name:
                        parsed['routers'] = int(float(value))
                    elif 'service' in metric_name and 'total' in metric_name:
                        parsed['services'] = int(float(value))
                    elif 'middleware' in metric_name and 'total' in metric_name:
                        parsed['middlewares'] = int(float(value))

        except Exception as e:
            logger.debug(f"Error parsing metric line '{line}': {e}")
            continue

    return parsed


@router.get("/overview", response_model=TraefikStats)
async def get_traefik_stats(admin: Dict = Depends(require_admin)):
    """
    Get overall Traefik statistics.

    Returns:
        Traefik stats
    """
    try:
        metrics_text = await fetch_prometheus_metrics()
        parsed = parse_prometheus_metrics(metrics_text)

        total_requests = sum(
            data['total'] for data in parsed['requests'].values()
        )

        stats = TraefikStats(
            total_requests=total_requests,
            active_connections=parsed.get('connections', 0),
            total_routers=parsed.get('routers', 0),
            total_services=parsed.get('services', 0),
            total_middlewares=parsed.get('middlewares', 0),
            uptime_seconds=0  # Would need to track this separately
        )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Traefik stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routes", response_model=List[RouteMetrics])
async def get_route_metrics(admin: Dict = Depends(require_admin)):
    """
    Get metrics for all routes.

    Returns:
        List of route metrics
    """
    try:
        metrics_text = await fetch_prometheus_metrics()
        parsed = parse_prometheus_metrics(metrics_text)

        route_metrics = []

        for router_name, request_data in parsed['requests'].items():
            total_requests = request_data['total']
            error_count = sum(
                count for code, count in request_data['codes'].items()
                if code.startswith('4') or code.startswith('5')
            )

            avg_duration = parsed['durations'].get(router_name, 0.0)

            metrics = RouteMetrics(
                route_name=router_name,
                service_name=request_data['service'],
                request_count=total_requests,
                avg_response_time_ms=avg_duration * 1000,  # Convert to ms
                error_count=error_count,
                error_rate=error_count / total_requests if total_requests > 0 else 0.0,
                status_codes=request_data['codes']
            )

            route_metrics.append(metrics)

        return route_metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting route metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routes/{route_name}", response_model=RouteMetrics)
async def get_route_metric(route_name: str, admin: Dict = Depends(require_admin)):
    """
    Get metrics for a specific route.

    Args:
        route_name: Route name

    Returns:
        Route metrics
    """
    try:
        route_metrics = await get_route_metrics(admin)

        for metrics in route_metrics:
            if metrics.route_name == route_name:
                return metrics

        raise HTTPException(status_code=404, detail=f"No metrics found for route '{route_name}'")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics for route {route_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/errors")
async def get_error_summary(admin: Dict = Depends(require_admin)):
    """
    Get error summary across all routes.

    Returns:
        Error summary
    """
    try:
        route_metrics = await get_route_metrics(admin)

        total_errors = sum(m.error_count for m in route_metrics)
        total_requests = sum(m.request_count for m in route_metrics)

        errors_by_route = [
            {
                "route": m.route_name,
                "error_count": m.error_count,
                "error_rate": m.error_rate,
                "status_codes": m.status_codes
            }
            for m in route_metrics
            if m.error_count > 0
        ]

        return {
            "total_errors": total_errors,
            "total_requests": total_requests,
            "overall_error_rate": total_errors / total_requests if total_requests > 0 else 0.0,
            "errors_by_route": errors_by_route
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting error summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_summary(admin: Dict = Depends(require_admin)):
    """
    Get performance summary across all routes.

    Returns:
        Performance summary
    """
    try:
        route_metrics = await get_route_metrics(admin)

        if not route_metrics:
            return {
                "routes_count": 0,
                "avg_response_time_ms": 0.0,
                "slowest_routes": [],
                "fastest_routes": []
            }

        # Calculate average response time
        total_weighted_time = sum(
            m.avg_response_time_ms * m.request_count
            for m in route_metrics
        )
        total_requests = sum(m.request_count for m in route_metrics)
        avg_response_time = total_weighted_time / total_requests if total_requests > 0 else 0.0

        # Get slowest and fastest routes
        sorted_by_time = sorted(route_metrics, key=lambda m: m.avg_response_time_ms, reverse=True)

        slowest = [
            {
                "route": m.route_name,
                "avg_response_time_ms": m.avg_response_time_ms,
                "request_count": m.request_count
            }
            for m in sorted_by_time[:5]
        ]

        fastest = [
            {
                "route": m.route_name,
                "avg_response_time_ms": m.avg_response_time_ms,
                "request_count": m.request_count
            }
            for m in sorted_by_time[-5:]
        ]

        return {
            "routes_count": len(route_metrics),
            "avg_response_time_ms": avg_response_time,
            "slowest_routes": slowest,
            "fastest_routes": fastest
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/raw")
async def get_raw_metrics(admin: Dict = Depends(require_admin)):
    """
    Get raw Prometheus metrics from Traefik.

    Returns:
        Raw metrics text
    """
    try:
        metrics_text = await fetch_prometheus_metrics()
        return {"metrics": metrics_text}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting raw metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
