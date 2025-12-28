"""
Prometheus API Integration
Manages Prometheus scrape targets, retention policies, and alert rules
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import httpx
import yaml
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/monitoring/prometheus", tags=["Monitoring"])

# Prometheus Configuration
PROMETHEUS_URL = "http://prometheus.your-domain.com:9090"
PROMETHEUS_TIMEOUT = 30.0

# Pre-defined scrape targets
DEFAULT_TARGETS = [
    {
        "name": "Ops Center API",
        "endpoint": "http://ops-center-direct:8084/metrics",
        "interval": "15s",
        "enabled": False
    },
    {
        "name": "Keycloak",
        "endpoint": "http://keycloak:8080/metrics",
        "interval": "30s",
        "enabled": False
    },
    {
        "name": "PostgreSQL Exporter",
        "endpoint": "http://postgres-exporter:9187/metrics",
        "interval": "15s",
        "enabled": False
    },
    {
        "name": "Redis Exporter",
        "endpoint": "http://redis-exporter:9121/metrics",
        "interval": "15s",
        "enabled": False
    },
    {
        "name": "Node Exporter",
        "endpoint": "http://node-exporter:9100/metrics",
        "interval": "15s",
        "enabled": False
    },
    {
        "name": "GPU Exporter",
        "endpoint": "http://gpu-exporter:9835/metrics",
        "interval": "15s",
        "enabled": False
    }
]

class PrometheusConfig(BaseModel):
    url: str
    scrape_interval: str = "15s"
    evaluation_interval: str = "15s"
    retention_time: str = "15d"
    retention_size: str = "50GB"

class ScrapeTarget(BaseModel):
    name: str
    endpoint: str
    interval: str = "15s"
    enabled: bool = False
    labels: Optional[Dict[str, str]] = {}

@router.get("/health")
async def check_prometheus_health():
    """Check if Prometheus is accessible"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{PROMETHEUS_URL}/-/healthy")
            if response.status_code == 200:
                return {
                    "success": True,
                    "status": "healthy",
                    "message": "Prometheus is running"
                }
    except Exception as e:
        logger.error(f"Prometheus health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }

@router.post("/test-connection")
async def test_prometheus_connection(config: PrometheusConfig):
    """Test Prometheus API connection"""
    try:
        async with httpx.AsyncClient(timeout=PROMETHEUS_TIMEOUT) as client:
            # Test with /api/v1/status/config endpoint
            response = await client.get(f"{config.url}/api/v1/status/config")

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Connected to Prometheus successfully",
                    "details": {"status": "operational"}
                }
            else:
                return {
                    "success": False,
                    "message": f"Prometheus connection failed: {response.status_code}",
                    "error": response.text
                }
    except Exception as e:
        logger.error(f"Prometheus connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/targets")
async def list_scrape_targets():
    """List all configured scrape targets"""
    try:
        async with httpx.AsyncClient(timeout=PROMETHEUS_TIMEOUT) as client:
            response = await client.get(f"{PROMETHEUS_URL}/api/v1/targets")

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "targets": data.get("data", {}).get("activeTargets", []),
                    "default_targets": DEFAULT_TARGETS
                }
            else:
                # Return default targets if Prometheus not accessible
                return {
                    "success": True,
                    "targets": [],
                    "default_targets": DEFAULT_TARGETS,
                    "note": "Returning default targets (Prometheus not accessible)"
                }
    except Exception as e:
        logger.error(f"Failed to list targets: {e}")
        # Return default targets on error
        return {
            "success": True,
            "targets": [],
            "default_targets": DEFAULT_TARGETS,
            "note": "Returning default targets (error occurred)"
        }

@router.post("/targets")
async def create_scrape_target(target: ScrapeTarget):
    """Create new scrape target"""
    # This would typically write to Prometheus config file
    # For now, return success with instructions
    return {
        "success": True,
        "message": f"Scrape target '{target.name}' configuration generated",
        "config": {
            "job_name": target.name.lower().replace(" ", "_"),
            "scrape_interval": target.interval,
            "static_configs": [{
                "targets": [target.endpoint],
                "labels": target.labels
            }]
        },
        "note": "Add this to prometheus.yml scrape_configs section"
    }

@router.get("/metrics")
async def query_metrics(query: str):
    """Query Prometheus metrics"""
    try:
        async with httpx.AsyncClient(timeout=PROMETHEUS_TIMEOUT) as client:
            response = await client.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={"query": query}
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to query metrics: {response.text}"
                )
    except Exception as e:
        logger.error(f"Failed to query metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_prometheus_config():
    """Get current Prometheus configuration"""
    try:
        async with httpx.AsyncClient(timeout=PROMETHEUS_TIMEOUT) as client:
            response = await client.get(f"{PROMETHEUS_URL}/api/v1/status/config")

            if response.status_code == 200:
                return {
                    "success": True,
                    "config": response.json()
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch config: {response.text}"
                )
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

logger.info("Prometheus API module initialized with 6 default targets")
