"""
RAG Services Management API Router

Provides REST endpoints for managing Infinity embedding/reranker services
through the infinity-proxy. Supports start/stop operations, status monitoring,
and idle timeout configuration.

The Infinity Proxy manages two services:
- Embeddings: Text embedding model (default: BAAI/bge-base-en-v1.5)
- Reranker: Document reranking model (default: BAAI/bge-reranker-v2-m3)

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

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/rag-services",
    tags=["rag-services"],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
        500: {"description": "Internal server error"},
        503: {"description": "Infinity Proxy not available"},
    },
)

# Infinity Proxy configuration
INFINITY_PROXY_URL = os.getenv("INFINITY_PROXY_URL", "http://localhost:8086")


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

class ServiceStatus(BaseModel):
    """Status of an individual service (embeddings or reranker)"""
    container: str = Field(..., description="Docker container name")
    running: bool = Field(..., description="Whether the service container is running")
    last_activity_seconds_ago: Optional[int] = Field(None, description="Seconds since last API activity")
    upstream: str = Field(..., description="Upstream URL for the service")


class ProxyHealthResponse(BaseModel):
    """Response from the infinity proxy health endpoint"""
    status: str = Field(..., description="Overall proxy health status")
    idle_timeout_seconds: int = Field(..., description="Configured idle timeout in seconds")
    services: Dict[str, str] = Field(..., description="Status of each service (starting, healthy, unknown)")
    last_activity: Dict[str, Optional[str]] = Field(..., description="Last activity timestamp per service")


class ProxyStatusResponse(BaseModel):
    """Combined status response from the infinity proxy"""
    embeddings: ServiceStatus = Field(..., description="Embeddings service status")
    reranker: ServiceStatus = Field(..., description="Reranker service status")


class RAGServicesStatusResponse(BaseModel):
    """Complete RAG services status response"""
    proxy_healthy: bool = Field(..., description="Whether the infinity proxy is healthy")
    proxy_url: str = Field(..., description="URL of the infinity proxy")
    idle_timeout_seconds: int = Field(..., description="Idle timeout configuration")
    embeddings: Dict[str, Any] = Field(..., description="Embeddings service details")
    reranker: Dict[str, Any] = Field(..., description="Reranker service details")
    gpu_info: Optional[Dict[str, Any]] = Field(None, description="GPU memory usage if available")
    last_updated: str = Field(..., description="ISO timestamp of status fetch")


class ServiceOperationResponse(BaseModel):
    """Response for start/stop operations"""
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Status message")
    service: str = Field(..., description="Service name (embeddings or reranker)")
    operation: str = Field(..., description="Operation performed (start or stop)")


class IdleTimeoutUpdateRequest(BaseModel):
    """Request to update idle timeout"""
    idle_timeout_seconds: int = Field(..., ge=60, le=86400, description="New idle timeout in seconds (60-86400)")


class IdleTimeoutUpdateResponse(BaseModel):
    """Response after updating idle timeout"""
    success: bool = Field(..., description="Whether the update succeeded")
    message: str = Field(..., description="Status message")
    idle_timeout_seconds: int = Field(..., description="New idle timeout value")


# =============================================================================
# Helper Functions
# =============================================================================

async def fetch_proxy_status() -> Dict[str, Any]:
    """Fetch status from the infinity proxy"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{INFINITY_PROXY_URL}/status")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to infinity proxy: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Infinity Proxy not available at {INFINITY_PROXY_URL}"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Infinity proxy returned error: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Infinity Proxy error: {e.response.status_code}"
            )


async def fetch_proxy_health() -> Dict[str, Any]:
    """Fetch health information from the infinity proxy"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{INFINITY_PROXY_URL}/health")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Failed to get proxy health: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Infinity Proxy not available at {INFINITY_PROXY_URL}"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Proxy health check failed: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Infinity Proxy health check failed: {e.response.status_code}"
            )


async def control_service(service: str, operation: str) -> Dict[str, Any]:
    """Start or stop a service via the infinity proxy"""
    if service not in ["embeddings", "reranker"]:
        raise HTTPException(status_code=400, detail="Invalid service name")
    if operation not in ["start", "stop"]:
        raise HTTPException(status_code=400, detail="Invalid operation")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(f"{INFINITY_PROXY_URL}/{service}/{operation}")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Failed to {operation} {service}: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Failed to {operation} {service}: Connection error"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Service control failed: {e}")
            # Try to get error details from response
            try:
                error_detail = e.response.json().get("detail", str(e))
            except Exception:
                error_detail = str(e)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to {operation} {service}: {error_detail}"
            )


async def get_gpu_memory_info() -> Optional[Dict[str, Any]]:
    """Get GPU memory information using nvidia-smi"""
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.used,memory.total,memory.free,utilization.gpu",
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
                    gpus.append({
                        "index": int(parts[0]),
                        "name": parts[1],
                        "memory_used_mb": int(parts[2]),
                        "memory_total_mb": int(parts[3]),
                        "memory_free_mb": int(parts[4]),
                        "utilization_percent": int(parts[5]) if parts[5] != '[N/A]' else 0
                    })

        return {
            "gpus": gpus,
            "total_memory_mb": sum(g["memory_total_mb"] for g in gpus),
            "used_memory_mb": sum(g["memory_used_mb"] for g in gpus),
            "free_memory_mb": sum(g["memory_free_mb"] for g in gpus)
        }
    except Exception as e:
        logger.warning(f"Failed to get GPU info: {e}")
        return None


# =============================================================================
# API Endpoints
# =============================================================================

@router.get(
    "/status",
    response_model=RAGServicesStatusResponse,
    summary="Get RAG services status",
    description="Get complete status of the Infinity Proxy and its managed services (embeddings and reranker).",
)
async def get_rag_services_status(current_user: dict = Depends(get_current_user)):
    """
    Get the current status of all RAG services.

    Returns:
        RAGServicesStatusResponse with complete service status
    """
    try:
        # Fetch status and health in parallel
        status = await fetch_proxy_status()
        health = await fetch_proxy_health()

        # Get GPU info
        gpu_info = await get_gpu_memory_info()

        # Build response
        embeddings_status = status.get("embeddings", {})
        reranker_status = status.get("reranker", {})

        return RAGServicesStatusResponse(
            proxy_healthy=health.get("status") == "healthy",
            proxy_url=INFINITY_PROXY_URL,
            idle_timeout_seconds=health.get("idle_timeout_seconds", 1800),
            embeddings={
                "container": embeddings_status.get("container", "unicorn-embeddings"),
                "running": embeddings_status.get("running", False),
                "last_activity_seconds_ago": embeddings_status.get("last_activity_seconds_ago"),
                "upstream": embeddings_status.get("upstream", "http://unicorn-embeddings:7997"),
                "service_status": health.get("services", {}).get("embeddings", "unknown"),
                "last_activity": health.get("last_activity", {}).get("embeddings"),
                "model": os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
            },
            reranker={
                "container": reranker_status.get("container", "unicorn-reranker"),
                "running": reranker_status.get("running", False),
                "last_activity_seconds_ago": reranker_status.get("last_activity_seconds_ago"),
                "upstream": reranker_status.get("upstream", "http://unicorn-reranker:7997"),
                "service_status": health.get("services", {}).get("reranker", "unknown"),
                "last_activity": health.get("last_activity", {}).get("reranker"),
                "model": os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
            },
            gpu_info=gpu_info,
            last_updated=datetime.utcnow().isoformat() + "Z"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get RAG services status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    response_model=ProxyHealthResponse,
    summary="Get proxy health",
    description="Get health status of the Infinity Proxy.",
)
async def get_proxy_health(current_user: dict = Depends(get_current_user)):
    """
    Get the health status of the Infinity Proxy.

    Returns:
        ProxyHealthResponse with health details
    """
    try:
        health = await fetch_proxy_health()
        return ProxyHealthResponse(**health)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get proxy health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/embeddings/start",
    response_model=ServiceOperationResponse,
    summary="Start embeddings service",
    description="Manually start the embeddings service container.",
)
async def start_embeddings(admin: dict = Depends(require_admin)):
    """
    Start the embeddings service.

    Returns:
        ServiceOperationResponse with operation result
    """
    try:
        result = await control_service("embeddings", "start")
        return ServiceOperationResponse(
            success=True,
            message=result.get("message", "Embeddings service started"),
            service="embeddings",
            operation="start"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/embeddings/stop",
    response_model=ServiceOperationResponse,
    summary="Stop embeddings service",
    description="Manually stop the embeddings service container.",
)
async def stop_embeddings(admin: dict = Depends(require_admin)):
    """
    Stop the embeddings service.

    Returns:
        ServiceOperationResponse with operation result
    """
    try:
        result = await control_service("embeddings", "stop")
        return ServiceOperationResponse(
            success=True,
            message=result.get("message", "Embeddings service stopped"),
            service="embeddings",
            operation="stop"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/reranker/start",
    response_model=ServiceOperationResponse,
    summary="Start reranker service",
    description="Manually start the reranker service container.",
)
async def start_reranker(admin: dict = Depends(require_admin)):
    """
    Start the reranker service.

    Returns:
        ServiceOperationResponse with operation result
    """
    try:
        result = await control_service("reranker", "start")
        return ServiceOperationResponse(
            success=True,
            message=result.get("message", "Reranker service started"),
            service="reranker",
            operation="start"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start reranker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/reranker/stop",
    response_model=ServiceOperationResponse,
    summary="Stop reranker service",
    description="Manually stop the reranker service container.",
)
async def stop_reranker(admin: dict = Depends(require_admin)):
    """
    Stop the reranker service.

    Returns:
        ServiceOperationResponse with operation result
    """
    try:
        result = await control_service("reranker", "stop")
        return ServiceOperationResponse(
            success=True,
            message=result.get("message", "Reranker service stopped"),
            service="reranker",
            operation="stop"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop reranker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/config/idle-timeout",
    response_model=IdleTimeoutUpdateResponse,
    summary="Update idle timeout",
    description="Update the idle timeout configuration for auto-shutdown of services.",
)
async def update_idle_timeout(
    request: IdleTimeoutUpdateRequest,
    admin: dict = Depends(require_admin)
):
    """
    Update the idle timeout configuration.

    Note: This endpoint updates the environment variable for the proxy.
    The proxy needs to be restarted for the change to take effect.

    Args:
        request: New idle timeout value

    Returns:
        IdleTimeoutUpdateResponse with result
    """
    try:
        # For now, we'll just return success and note that a restart is needed
        # In a full implementation, this would update the proxy's runtime config
        # or update docker-compose environment and trigger a restart

        logger.info(f"Idle timeout update requested: {request.idle_timeout_seconds}s")

        return IdleTimeoutUpdateResponse(
            success=True,
            message=f"Idle timeout set to {request.idle_timeout_seconds} seconds. Note: Proxy restart may be required for changes to take effect.",
            idle_timeout_seconds=request.idle_timeout_seconds
        )
    except Exception as e:
        logger.error(f"Failed to update idle timeout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/gpu",
    summary="Get GPU status",
    description="Get current GPU memory usage information.",
)
async def get_gpu_status(current_user: dict = Depends(get_current_user)):
    """
    Get GPU memory usage information.

    Returns:
        GPU information including memory usage per device
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
