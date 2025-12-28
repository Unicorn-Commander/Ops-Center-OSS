"""
Provider Health Monitoring System

Monitors health and availability of all LLM providers.

Author: Ops-Center Backend Team
Date: October 20, 2025
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)


@dataclass
class ProviderHealthStatus:
    """Health status for a provider"""
    provider: str
    is_healthy: bool
    response_time_ms: Optional[float]
    last_check: datetime
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    availability_percentage: float = 100.0


class ProviderHealthChecker:
    """
    Monitor health of LLM providers.

    Performs periodic health checks and tracks availability.
    """

    def __init__(self, redis_client=None):
        """
        Initialize health checker.

        Args:
            redis_client: Optional Redis client for storing health data
        """
        self.redis_client = redis_client
        self.health_status: Dict[str, ProviderHealthStatus] = {}
        self.check_interval_seconds = 60
        self.is_monitoring = False
        self._monitor_task = None

    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.is_monitoring:
            logger.warning("Health monitoring already started")
            return

        self.is_monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Provider health monitoring started")

    async def stop_monitoring(self):
        """Stop health monitoring."""
        self.is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Provider health monitoring stopped")

    async def _monitor_loop(self):
        """Continuous monitoring loop."""
        while self.is_monitoring:
            try:
                await self.check_all_providers()
                await asyncio.sleep(self.check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval_seconds)

    async def check_all_providers(self) -> Dict[str, ProviderHealthStatus]:
        """
        Check health of all providers.

        Returns:
            Dict mapping provider names to health status
        """
        providers_to_check = [
            "local",
            "groq",
            "huggingface",
            "together",
            "fireworks",
            "deepinfra",
            "openrouter",
            "anthropic",
            "openai"
        ]

        check_tasks = [
            self._check_provider(provider)
            for provider in providers_to_check
        ]

        results = await asyncio.gather(*check_tasks, return_exceptions=True)

        for provider, result in zip(providers_to_check, results):
            if isinstance(result, Exception):
                logger.error(f"Health check failed for {provider}: {result}")
                self._update_status(provider, False, None, str(result))
            else:
                self.health_status[provider] = result

        # Store in Redis if available
        if self.redis_client:
            await self._store_health_status()

        return self.health_status

    async def _check_provider(self, provider: str) -> ProviderHealthStatus:
        """
        Check health of specific provider.

        Args:
            provider: Provider name

        Returns:
            ProviderHealthStatus
        """
        start_time = datetime.now()

        try:
            if provider == "local":
                # Check local services (vLLM, Ollama)
                is_healthy, response_time = await self._check_local_services()
            else:
                # Check external provider
                is_healthy, response_time = await self._check_external_provider(provider)

            elapsed_ms = response_time if response_time else (
                (datetime.now() - start_time).total_seconds() * 1000
            )

            # Update consecutive failures
            previous = self.health_status.get(provider)
            consecutive_failures = 0 if is_healthy else (
                previous.consecutive_failures + 1 if previous else 1
            )

            # Calculate availability percentage (last 24 hours)
            availability = await self._calculate_availability(provider)

            return ProviderHealthStatus(
                provider=provider,
                is_healthy=is_healthy,
                response_time_ms=elapsed_ms,
                last_check=datetime.now(),
                consecutive_failures=consecutive_failures,
                availability_percentage=availability
            )

        except Exception as e:
            logger.error(f"Health check failed for {provider}: {e}")

            previous = self.health_status.get(provider)
            consecutive_failures = previous.consecutive_failures + 1 if previous else 1

            return ProviderHealthStatus(
                provider=provider,
                is_healthy=False,
                response_time_ms=None,
                last_check=datetime.now(),
                error_message=str(e),
                consecutive_failures=consecutive_failures,
                availability_percentage=await self._calculate_availability(provider)
            )

    async def _check_local_services(self) -> tuple[bool, Optional[float]]:
        """
        Check health of local services (vLLM, Ollama).

        Returns:
            Tuple of (is_healthy, response_time_ms)
        """
        start_time = datetime.now()

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Check vLLM
                try:
                    response = await client.get("http://unicorn-vllm:8000/health")
                    vllm_healthy = response.status_code == 200
                except Exception:
                    vllm_healthy = False

                # Check Ollama
                try:
                    response = await client.get("http://unicorn-ollama:11434/api/tags")
                    ollama_healthy = response.status_code == 200
                except Exception:
                    ollama_healthy = False

                # At least one service should be healthy
                is_healthy = vllm_healthy or ollama_healthy

                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

                return is_healthy, elapsed_ms

        except Exception as e:
            logger.error(f"Local service health check failed: {e}")
            return False, None

    async def _check_external_provider(self, provider: str) -> tuple[bool, Optional[float]]:
        """
        Check health of external provider.

        For now, assume healthy unless we have evidence otherwise.
        In production, this would make actual API calls.

        Args:
            provider: Provider name

        Returns:
            Tuple of (is_healthy, response_time_ms)
        """
        # Map providers to their API endpoints
        health_endpoints = {
            "groq": "https://api.groq.com/openai/v1/models",
            "openai": "https://api.openai.com/v1/models",
            "anthropic": "https://api.anthropic.com/v1/messages",
            "openrouter": "https://openrouter.ai/api/v1/models"
        }

        endpoint = health_endpoints.get(provider)

        if not endpoint:
            # For providers without health endpoint, assume healthy
            logger.debug(f"No health endpoint for {provider}, assuming healthy")
            return True, 100.0

        start_time = datetime.now()

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Most providers require authentication, so just check connection
                response = await client.get(endpoint, follow_redirects=True)

                # Consider 2xx, 401 (auth required), 403 (forbidden) as "healthy"
                # (proves service is reachable)
                is_healthy = response.status_code in [200, 401, 403]

                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

                return is_healthy, elapsed_ms

        except httpx.TimeoutException:
            logger.warning(f"{provider} health check timed out")
            return False, 5000.0
        except Exception as e:
            logger.error(f"{provider} health check failed: {e}")
            return False, None

    async def _calculate_availability(self, provider: str) -> float:
        """
        Calculate availability percentage for provider over last 24 hours.

        Args:
            provider: Provider name

        Returns:
            Availability percentage (0-100)
        """
        if not self.redis_client:
            # Without Redis, use current status
            current = self.health_status.get(provider)
            return 100.0 if current and current.is_healthy else 0.0

        # Get health check history from Redis
        key = f"provider_health:{provider}:history"
        try:
            # This would query health check history stored in Redis
            # For now, return current status
            current = self.health_status.get(provider)
            return 100.0 if current and current.is_healthy else 0.0
        except Exception as e:
            logger.error(f"Failed to calculate availability for {provider}: {e}")
            return 50.0  # Unknown

    def _update_status(
        self,
        provider: str,
        is_healthy: bool,
        response_time_ms: Optional[float],
        error_message: Optional[str]
    ):
        """Update provider health status."""
        previous = self.health_status.get(provider)
        consecutive_failures = 0 if is_healthy else (
            previous.consecutive_failures + 1 if previous else 1
        )

        self.health_status[provider] = ProviderHealthStatus(
            provider=provider,
            is_healthy=is_healthy,
            response_time_ms=response_time_ms,
            last_check=datetime.now(),
            error_message=error_message,
            consecutive_failures=consecutive_failures,
            availability_percentage=100.0 if is_healthy else 0.0
        )

    async def _store_health_status(self):
        """Store health status in Redis."""
        if not self.redis_client:
            return

        try:
            # Store current health status
            for provider, status in self.health_status.items():
                key = f"provider_health:{provider}:current"
                data = {
                    "is_healthy": status.is_healthy,
                    "response_time_ms": status.response_time_ms,
                    "last_check": status.last_check.isoformat(),
                    "consecutive_failures": status.consecutive_failures,
                    "availability_percentage": status.availability_percentage
                }
                if status.error_message:
                    data["error_message"] = status.error_message

                await self.redis_client.setex(
                    key,
                    3600,  # 1 hour TTL
                    str(data)
                )

                # Store in history (for availability calculation)
                history_key = f"provider_health:{provider}:history"
                await self.redis_client.lpush(
                    history_key,
                    f"{datetime.now().isoformat()}:{1 if status.is_healthy else 0}"
                )
                # Keep last 1440 entries (24 hours at 1-minute intervals)
                await self.redis_client.ltrim(history_key, 0, 1439)

        except Exception as e:
            logger.error(f"Failed to store health status: {e}")

    async def get_healthy_providers(self) -> List[str]:
        """
        Get list of currently healthy providers.

        Returns:
            List of provider names
        """
        if not self.health_status:
            await self.check_all_providers()

        return [
            provider
            for provider, status in self.health_status.items()
            if status.is_healthy
        ]

    async def is_provider_healthy(self, provider: str) -> bool:
        """
        Check if specific provider is healthy.

        Args:
            provider: Provider name

        Returns:
            True if healthy
        """
        status = self.health_status.get(provider)

        if not status:
            # No recent check, perform one
            status = await self._check_provider(provider)

        # Check if status is recent (within last 5 minutes)
        if (datetime.now() - status.last_check).total_seconds() > 300:
            # Status is stale, refresh
            status = await self._check_provider(provider)

        return status.is_healthy

    def get_provider_latency(self, provider: str) -> Optional[float]:
        """
        Get average latency for provider.

        Args:
            provider: Provider name

        Returns:
            Average latency in milliseconds, or None if unavailable
        """
        status = self.health_status.get(provider)
        return status.response_time_ms if status else None

    async def get_health_summary(self) -> Dict[str, Any]:
        """
        Get summary of provider health.

        Returns:
            Summary dict with overall health stats
        """
        if not self.health_status:
            await self.check_all_providers()

        total_providers = len(self.health_status)
        healthy_providers = sum(
            1 for status in self.health_status.values()
            if status.is_healthy
        )

        avg_response_time = None
        response_times = [
            status.response_time_ms
            for status in self.health_status.values()
            if status.response_time_ms is not None
        ]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)

        return {
            "total_providers": total_providers,
            "healthy_providers": healthy_providers,
            "unhealthy_providers": total_providers - healthy_providers,
            "overall_health_percentage": (
                (healthy_providers / total_providers * 100)
                if total_providers > 0 else 0
            ),
            "average_response_time_ms": avg_response_time,
            "last_check": max(
                (status.last_check for status in self.health_status.values()),
                default=None
            ),
            "providers": [
                {
                    "provider": status.provider,
                    "is_healthy": status.is_healthy,
                    "response_time_ms": status.response_time_ms,
                    "consecutive_failures": status.consecutive_failures,
                    "availability_percentage": status.availability_percentage
                }
                for status in self.health_status.values()
            ]
        }


# Singleton instance
_health_checker: Optional[ProviderHealthChecker] = None


def get_health_checker(redis_client=None) -> ProviderHealthChecker:
    """Get or create singleton ProviderHealthChecker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = ProviderHealthChecker(redis_client)
    return _health_checker
