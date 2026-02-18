"""
GPU Services Management API Router

Provides REST endpoints for managing GPU services through the Infinity and Granite proxies.
Supports start/stop operations, status monitoring, and GPU memory tracking.

The Infinity Proxy manages:
- Embeddings: Text embedding model (BAAI/bge-base-en-v1.5)
- Reranker: Document reranking model (BAAI/bge-reranker-v2-m3)

The Granite Proxy manages:
- Granite1: First Granite extraction LLM
- Granite2: Second Granite extraction LLM

Author: Ops-Center Backend Team
Created: 2026-01-25
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import logging
import sys
import os
import httpx
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/gpu-services",
    tags=["gpu-services"],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
        500: {"description": "Internal server error"},
        503: {"description": "Proxy not available"},
    },
)

# Proxy configuration
INFINITY_PROXY_URL = os.getenv("INFINITY_PROXY_URL", "http://unicorn-infinity-proxy:8080")
GRANITE_PROXY_URL = os.getenv("GRANITE_PROXY_URL", "http://unicorn-granite-proxy:8080")


# =============================================================================
# Enums
# =============================================================================

class GPUService(str, Enum):
    """Available GPU services"""
    EMBEDDINGS = "embeddings"
    RERANKER = "reranker"
    GRANITE1 = "granite1"
    GRANITE2 = "granite2"


# =============================================================================
# Authentication Dependencies
# =============================================================================

async def get_current_user(request: Request):
    """Verify user is authenticated (uses Redis session manager)"""
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    from redis_session import RedisSessionManager

    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    sessions = RedisSessionManager(host=redis_host, port=redis_port)

    if session_token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    session_data = sessions[session_token]
    user = session_data.get("user", {})

    if not user:
        raise HTTPException(status_code=401, detail="User not found in session")

    return user


async def require_admin(request: Request):
    """Verify user is authenticated and has admin role"""
    user = await get_current_user(request)

    if not user.get("is_admin") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


# =============================================================================
# Request/Response Models
# =============================================================================

class ServiceInfo(BaseModel):
    """Information about a single service"""
    container: Optional[str] = Field(None, description="Docker container name")
    running: bool = Field(False, description="Whether the service is running")
    last_activity_seconds_ago: Optional[int] = Field(None, description="Seconds since last API activity")
    upstream: Optional[str] = Field(None, description="Upstream URL for the service")
    service_status: str = Field("unknown", description="Service status (starting, healthy, unknown)")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")


class ProxyStatus(BaseModel):
    """Status of a proxy (Infinity or Granite)"""
    healthy: bool = Field(False, description="Whether the proxy is healthy")
    idle_timeout_seconds: Optional[int] = Field(None, description="Configured idle timeout in seconds")
    services: Dict[str, ServiceInfo] = Field(default_factory=dict, description="Status of each service")


class GPUInfo(BaseModel):
    """GPU information"""
    index: int = Field(..., description="GPU index")
    name: str = Field(..., description="GPU name")
    memory_used_mb: int = Field(..., description="Used memory in MB")
    memory_total_mb: int = Field(..., description="Total memory in MB")
    memory_free_mb: int = Field(..., description="Free memory in MB")
    utilization_percent: int = Field(0, description="GPU utilization percentage")
    temperature: Optional[int] = Field(None, description="GPU temperature in Celsius")


class GPUMemoryInfo(BaseModel):
    """GPU memory information"""
    gpus: List[GPUInfo] = Field(default_factory=list, description="Per-GPU information")
    total_memory_mb: int = Field(0, description="Total GPU memory across all GPUs")
    used_memory_mb: int = Field(0, description="Total used GPU memory")
    free_memory_mb: int = Field(0, description="Total free GPU memory")


class GPUServicesStatusResponse(BaseModel):
    """Complete GPU services status response"""
    infinity_proxy: ProxyStatus = Field(..., description="Status of Infinity Proxy (embeddings/reranker)")
    granite_proxy: ProxyStatus = Field(..., description="Status of Granite Proxy (extraction LLMs)")
    gpu_info: Optional[GPUMemoryInfo] = Field(None, description="GPU memory usage information")
    last_updated: str = Field(..., description="ISO timestamp of status fetch")


class ServiceOperationResponse(BaseModel):
    """Response for start/stop operations"""
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Status message")
    service: str = Field(..., description="Service name")
    operation: str = Field(..., description="Operation performed (start or stop)")


# =============================================================================
# Helper Functions
# =============================================================================

def get_service_proxy_url(service: str) -> tuple[str, str]:
    """
    Get the proxy URL and service name for a given service.
    Returns (proxy_url, service_name_on_proxy)
    """
    if service in ["embeddings", "reranker"]:
        return INFINITY_PROXY_URL, service
    elif service in ["granite1", "granite2"]:
        return GRANITE_PROXY_URL, service
    else:
        raise HTTPException(status_code=400, detail=f"Invalid service name: {service}")


async def fetch_proxy_status(proxy_url: str, proxy_name: str) -> Dict[str, Any]:
    """Fetch status from a proxy"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{proxy_url}/status")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.warning(f"Failed to connect to {proxy_name} at {proxy_url}: {e}")
            return {"error": f"Connection failed: {str(e)}"}
        except httpx.HTTPStatusError as e:
            logger.warning(f"{proxy_name} returned error: {e}")
            return {"error": f"HTTP error: {e.response.status_code}"}


async def fetch_proxy_health(proxy_url: str, proxy_name: str) -> Dict[str, Any]:
    """Fetch health information from a proxy"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{proxy_url}/health")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.warning(f"Failed to get {proxy_name} health: {e}")
            return {"status": "unhealthy", "error": str(e)}
        except httpx.HTTPStatusError as e:
            logger.warning(f"{proxy_name} health check failed: {e}")
            return {"status": "unhealthy", "error": f"HTTP {e.response.status_code}"}


async def control_service(service: str, operation: str) -> Dict[str, Any]:
    """Start or stop a service via the appropriate proxy"""
    if operation not in ["start", "stop"]:
        raise HTTPException(status_code=400, detail="Invalid operation. Use 'start' or 'stop'")

    proxy_url, service_name = get_service_proxy_url(service)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(f"{proxy_url}/{service_name}/{operation}")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Failed to {operation} {service}: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Failed to {operation} {service}: Connection error to proxy"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Service control failed: {e}")
            try:
                error_detail = e.response.json().get("detail", str(e))
            except Exception:
                error_detail = str(e)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to {operation} {service}: {error_detail}"
            )


async def get_gpu_memory_info() -> Optional[GPUMemoryInfo]:
    """Get GPU memory information using nvidia-smi"""
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.used,memory.total,memory.free,utilization.gpu,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return None

        gpus = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 6:
                    # Parse temperature (7th field if available)
                    temperature = None
                    if len(parts) >= 7 and parts[6] not in ['[N/A]', '[Not Supported]', '']:
                        try:
                            temperature = int(parts[6])
                        except ValueError:
                            pass

                    gpus.append(GPUInfo(
                        index=int(parts[0]),
                        name=parts[1],
                        memory_used_mb=int(parts[2]),
                        memory_total_mb=int(parts[3]),
                        memory_free_mb=int(parts[4]),
                        utilization_percent=int(parts[5]) if parts[5] not in ['[N/A]', '[Not Supported]', ''] else 0,
                        temperature=temperature
                    ))

        return GPUMemoryInfo(
            gpus=gpus,
            total_memory_mb=sum(g.memory_total_mb for g in gpus),
            used_memory_mb=sum(g.memory_used_mb for g in gpus),
            free_memory_mb=sum(g.memory_free_mb for g in gpus)
        )
    except Exception as e:
        logger.warning(f"Failed to get GPU info: {e}")
        return None


def build_proxy_status(status: Dict[str, Any], health: Dict[str, Any], services: List[str]) -> ProxyStatus:
    """Build a ProxyStatus from raw status and health data"""
    is_healthy = health.get("status") == "healthy" and "error" not in health

    service_infos = {}
    for svc in services:
        svc_status = status.get(svc, {})
        svc_health = health.get("services", {}).get(svc, "unknown")
        svc_last_activity = health.get("last_activity", {}).get(svc)

        service_infos[svc] = ServiceInfo(
            container=svc_status.get("container"),
            running=svc_status.get("running", False),
            last_activity_seconds_ago=svc_status.get("last_activity_seconds_ago"),
            upstream=svc_status.get("upstream"),
            service_status=svc_health if isinstance(svc_health, str) else "unknown",
            last_activity=str(svc_last_activity) if svc_last_activity is not None else None
        )

    return ProxyStatus(
        healthy=is_healthy,
        idle_timeout_seconds=health.get("idle_timeout_seconds"),
        services=service_infos
    )


# =============================================================================
# API Endpoints
# =============================================================================

@router.get(
    "/status",
    response_model=GPUServicesStatusResponse,
    summary="Get status of all GPU services",
    description="Get complete status of Infinity Proxy (embeddings/reranker) and Granite Proxy (extraction LLMs), plus GPU memory information.",
)
async def get_gpu_services_status(current_user: dict = Depends(get_current_user)):
    """
    Get the current status of all GPU services.

    Returns:
        GPUServicesStatusResponse with complete service and GPU status
    """
    try:
        # Fetch status and health from both proxies in parallel
        infinity_status = await fetch_proxy_status(INFINITY_PROXY_URL, "Infinity Proxy")
        infinity_health = await fetch_proxy_health(INFINITY_PROXY_URL, "Infinity Proxy")

        granite_status = await fetch_proxy_status(GRANITE_PROXY_URL, "Granite Proxy")
        granite_health = await fetch_proxy_health(GRANITE_PROXY_URL, "Granite Proxy")

        # Get GPU info
        gpu_info = await get_gpu_memory_info()

        # Build response
        infinity_proxy_status = build_proxy_status(
            infinity_status, infinity_health, ["embeddings", "reranker"]
        )
        granite_proxy_status = build_proxy_status(
            granite_status, granite_health, ["granite1", "granite2"]
        )

        return GPUServicesStatusResponse(
            infinity_proxy=infinity_proxy_status,
            granite_proxy=granite_proxy_status,
            gpu_info=gpu_info,
            last_updated=datetime.utcnow().isoformat() + "Z"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get GPU services status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{service}/start",
    response_model=ServiceOperationResponse,
    summary="Start a specific GPU service",
    description="Start a GPU service (embeddings, reranker, granite1, or granite2).",
)
async def start_service(service: GPUService, admin: dict = Depends(require_admin)):
    """
    Start a GPU service.

    Args:
        service: The service to start (embeddings, reranker, granite1, granite2)

    Returns:
        ServiceOperationResponse with operation result
    """
    try:
        result = await control_service(service.value, "start")
        return ServiceOperationResponse(
            success=True,
            message=result.get("message", f"{service.value} service started"),
            service=service.value,
            operation="start"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start {service.value}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{service}/stop",
    response_model=ServiceOperationResponse,
    summary="Stop a specific GPU service",
    description="Stop a GPU service (embeddings, reranker, granite1, or granite2).",
)
async def stop_service(service: GPUService, admin: dict = Depends(require_admin)):
    """
    Stop a GPU service.

    Args:
        service: The service to stop (embeddings, reranker, granite1, granite2)

    Returns:
        ServiceOperationResponse with operation result
    """
    try:
        result = await control_service(service.value, "stop")
        return ServiceOperationResponse(
            success=True,
            message=result.get("message", f"{service.value} service stopped"),
            service=service.value,
            operation="stop"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop {service.value}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/gpu",
    response_model=GPUMemoryInfo,
    summary="Get GPU memory information",
    description="Get current GPU memory usage information using nvidia-smi.",
)
async def get_gpu_status(current_user: dict = Depends(get_current_user)):
    """
    Get GPU memory usage information.

    Returns:
        GPUMemoryInfo including per-GPU and aggregate memory usage
    """
    try:
        gpu_info = await get_gpu_memory_info()
        if gpu_info is None:
            raise HTTPException(
                status_code=404,
                detail="No GPU information available. nvidia-smi may not be accessible."
            )
        return gpu_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get GPU status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/infinity/status",
    response_model=ProxyStatus,
    summary="Get Infinity Proxy status",
    description="Get status of the Infinity Proxy which manages embeddings and reranker services.",
)
async def get_infinity_status(current_user: dict = Depends(get_current_user)):
    """
    Get the status of the Infinity Proxy (embeddings/reranker).

    Returns:
        ProxyStatus with embeddings and reranker service details
    """
    try:
        status = await fetch_proxy_status(INFINITY_PROXY_URL, "Infinity Proxy")
        health = await fetch_proxy_health(INFINITY_PROXY_URL, "Infinity Proxy")

        return build_proxy_status(status, health, ["embeddings", "reranker"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Infinity Proxy status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/granite/status",
    response_model=ProxyStatus,
    summary="Get Granite Proxy status",
    description="Get status of the Granite Proxy which manages extraction LLM services.",
)
async def get_granite_status(current_user: dict = Depends(get_current_user)):
    """
    Get the status of the Granite Proxy (extraction LLMs).

    Returns:
        ProxyStatus with granite1 and granite2 service details
    """
    try:
        status = await fetch_proxy_status(GRANITE_PROXY_URL, "Granite Proxy")
        health = await fetch_proxy_health(GRANITE_PROXY_URL, "Granite Proxy")

        return build_proxy_status(status, health, ["granite1", "granite2"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Granite Proxy status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
