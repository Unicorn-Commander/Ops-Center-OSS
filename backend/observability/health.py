"""
Comprehensive Health Check System

Provides multiple health check endpoints:
- /health - Simple liveness check
- /health/ready - Readiness check (DB, Redis, external APIs)
- /health/detailed - Full system diagnostics

Includes version info, uptime, and resource usage.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import psutil
import os
import time

try:
    import asyncpg
except ImportError:
    asyncpg = None

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

try:
    import httpx
except ImportError:
    httpx = None

router = APIRouter()


class HealthChecker:
    """Health check manager for Ops-Center."""

    def __init__(self):
        self.start_time = datetime.utcnow()
        self.version = os.getenv("OPS_CENTER_VERSION", "2.3.0")
        self.commit = os.getenv("GIT_COMMIT", "unknown")
        self.build_date = os.getenv("BUILD_DATE", "unknown")

        # Connection pools (to be set externally)
        self.db_pool: Optional[Any] = None
        self.redis_client: Optional[Any] = None

        # External service URLs
        self.keycloak_url = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
        self.litellm_url = os.getenv("LITELLM_PROXY_URL", "http://unicorn-litellm:4000")
        self.lago_url = os.getenv("LAGO_API_URL", "http://unicorn-lago-api:3000")

    def set_db_pool(self, pool):
        """Set database connection pool."""
        self.db_pool = pool

    def set_redis_client(self, client):
        """Set Redis client."""
        self.redis_client = client

    async def check_liveness(self) -> Dict[str, Any]:
        """
        Basic liveness check - is the service running?

        Returns:
            dict: Status and basic info
        """
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": "ops-center",
            "version": self.version
        }

    async def check_readiness(self) -> Dict[str, Any]:
        """
        Readiness check - can the service handle requests?

        Checks:
        - Database connection
        - Redis connection
        - Critical external services

        Returns:
            dict: Readiness status with component checks
        """
        checks = {}
        overall_ready = True

        # Check database
        db_status = await self._check_database()
        checks["database"] = db_status
        if db_status["status"] != "healthy":
            overall_ready = False

        # Check Redis
        redis_status = await self._check_redis()
        checks["redis"] = redis_status
        if redis_status["status"] != "healthy":
            overall_ready = False

        # Check Keycloak (authentication)
        keycloak_status = await self._check_keycloak()
        checks["keycloak"] = keycloak_status
        if keycloak_status["status"] != "healthy":
            overall_ready = False

        return {
            "status": "ready" if overall_ready else "not_ready",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checks": checks
        }

    async def check_detailed(self) -> Dict[str, Any]:
        """
        Detailed system diagnostics.

        Includes:
        - All readiness checks
        - System resources (CPU, memory, disk)
        - Uptime
        - Build information
        - Optional service checks (LiteLLM, Lago)

        Returns:
            dict: Comprehensive system status
        """
        # Get readiness checks
        readiness = await self.check_readiness()

        # Calculate uptime
        uptime = datetime.utcnow() - self.start_time
        uptime_seconds = int(uptime.total_seconds())

        # Get system resources
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Check optional services
        optional_checks = {}
        optional_checks["litellm"] = await self._check_litellm()
        optional_checks["lago"] = await self._check_lago()

        return {
            "status": readiness["status"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": "ops-center",
            "version": {
                "version": self.version,
                "commit": self.commit,
                "build_date": self.build_date
            },
            "uptime": {
                "seconds": uptime_seconds,
                "human_readable": str(uptime).split('.')[0]
            },
            "resources": {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "percent": disk.percent
                }
            },
            "checks": {
                "critical": readiness["checks"],
                "optional": optional_checks
            }
        }

    async def _check_database(self) -> Dict[str, Any]:
        """Check PostgreSQL database connection."""
        if not self.db_pool and not asyncpg:
            return {
                "status": "unknown",
                "message": "Database pool not configured"
            }

        try:
            start_time = time.time()

            if self.db_pool:
                # Use existing pool
                async with self.db_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
            else:
                # Create temporary connection
                db_host = os.getenv("POSTGRES_HOST", "unicorn-postgresql")
                db_port = int(os.getenv("POSTGRES_PORT", "5432"))
                db_user = os.getenv("POSTGRES_USER", "unicorn")
                db_password = os.getenv("POSTGRES_PASSWORD", "unicorn")
                db_name = os.getenv("POSTGRES_DB", "unicorn_db")

                conn = await asyncpg.connect(
                    host=db_host,
                    port=db_port,
                    user=db_user,
                    password=db_password,
                    database=db_name,
                    timeout=5.0
                )
                await conn.fetchval("SELECT 1")
                await conn.close()

            duration_ms = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "response_time_ms": round(duration_ms, 2),
                "message": "Database connection successful"
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Database connection failed"
            }

    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connection."""
        if not self.redis_client and not aioredis:
            return {
                "status": "unknown",
                "message": "Redis client not configured"
            }

        try:
            start_time = time.time()

            if self.redis_client:
                # Use existing client
                await self.redis_client.ping()
            else:
                # Create temporary connection
                redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
                redis_port = int(os.getenv("REDIS_PORT", "6379"))

                client = aioredis.from_url(
                    f"redis://{redis_host}:{redis_port}",
                    socket_connect_timeout=5
                )
                await client.ping()
                await client.close()

            duration_ms = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "response_time_ms": round(duration_ms, 2),
                "message": "Redis connection successful"
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Redis connection failed"
            }

    async def _check_keycloak(self) -> Dict[str, Any]:
        """Check Keycloak authentication service."""
        if not httpx:
            return {
                "status": "unknown",
                "message": "httpx not available for health check"
            }

        try:
            start_time = time.time()

            async with httpx.AsyncClient(timeout=5.0) as client:
                realm = os.getenv("KEYCLOAK_REALM", "uchub")
                url = f"{self.keycloak_url}/realms/{realm}/.well-known/openid-configuration"
                response = await client.get(url)
                response.raise_for_status()

            duration_ms = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "response_time_ms": round(duration_ms, 2),
                "message": "Keycloak is accessible"
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Keycloak health check failed"
            }

    async def _check_litellm(self) -> Dict[str, Any]:
        """Check LiteLLM proxy (optional)."""
        if not httpx:
            return {
                "status": "unknown",
                "message": "httpx not available"
            }

        try:
            start_time = time.time()

            async with httpx.AsyncClient(timeout=5.0) as client:
                url = f"{self.litellm_url}/health"
                response = await client.get(url)
                response.raise_for_status()

            duration_ms = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "response_time_ms": round(duration_ms, 2),
                "message": "LiteLLM is accessible"
            }

        except Exception as e:
            return {
                "status": "degraded",
                "error": str(e),
                "message": "LiteLLM health check failed (optional service)"
            }

    async def _check_lago(self) -> Dict[str, Any]:
        """Check Lago billing service (optional)."""
        if not httpx:
            return {
                "status": "unknown",
                "message": "httpx not available"
            }

        try:
            start_time = time.time()

            async with httpx.AsyncClient(timeout=5.0) as client:
                url = f"{self.lago_url}/health"
                response = await client.get(url)
                response.raise_for_status()

            duration_ms = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "response_time_ms": round(duration_ms, 2),
                "message": "Lago is accessible"
            }

        except Exception as e:
            return {
                "status": "degraded",
                "error": str(e),
                "message": "Lago health check failed (optional service)"
            }


# Global health checker instance
health_checker = HealthChecker()


@router.get("", summary="Liveness Check", tags=["health"])
@router.get("/", summary="Liveness Check", tags=["health"])
async def liveness_check():
    """
    Basic liveness check - is the service running?

    Returns 200 if the service is alive.
    """
    result = await health_checker.check_liveness()
    return JSONResponse(content=result, status_code=200)


@router.get("/ready", summary="Readiness Check", tags=["health"])
async def readiness_check():
    """
    Readiness check - can the service handle requests?

    Checks:
    - Database connection
    - Redis connection
    - Keycloak authentication

    Returns 200 if ready, 503 if not ready.
    """
    result = await health_checker.check_readiness()
    status_code = 200 if result["status"] == "ready" else 503
    return JSONResponse(content=result, status_code=status_code)


@router.get("/detailed", summary="Detailed Health Check", tags=["health"])
async def detailed_health_check():
    """
    Detailed system diagnostics.

    Includes:
    - All readiness checks
    - System resources (CPU, memory, disk)
    - Uptime and version information
    - Optional service checks (LiteLLM, Lago)

    Returns 200 if ready, 503 if critical services are down.
    """
    result = await health_checker.check_detailed()
    status_code = 200 if result["status"] == "ready" else 503
    return JSONResponse(content=result, status_code=status_code)
