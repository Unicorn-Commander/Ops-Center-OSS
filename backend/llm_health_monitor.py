"""
LLM Health Monitor

Background service to monitor LLM provider health:
- Ping each provider's API every 5 minutes
- Update provider health status in database
- Track response times
- Disable providers that are down
- Re-enable when they come back up

Author: Backend API Developer
Epic: 3.1 - LiteLLM Multi-Provider Routing
Date: October 23, 2025
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx

from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.llm_models import LLMProvider, LLMModel

logger = logging.getLogger(__name__)


# ============================================================================
-- Provider Health Check Endpoints
# ============================================================================

PROVIDER_HEALTH_ENDPOINTS = {
    'openai': {
        'url': 'https://api.openai.com/v1/models',
        'method': 'GET',
        'timeout': 10.0,
        'expected_status': [200],
        'auth_required': True
    },
    'anthropic': {
        'url': 'https://api.anthropic.com/v1/messages',
        'method': 'POST',
        'timeout': 10.0,
        'expected_status': [200, 400],  # 400 = missing required fields, but API is up
        'auth_required': True,
        'test_payload': {'model': 'claude-3-haiku-20240307', 'messages': [], 'max_tokens': 1}
    },
    'google': {
        'url': 'https://generativelanguage.googleapis.com/v1/models',
        'method': 'GET',
        'timeout': 10.0,
        'expected_status': [200, 400, 401],  # API is up even without auth
        'auth_required': False
    },
    'openrouter': {
        'url': 'https://openrouter.ai/api/v1/models',
        'method': 'GET',
        'timeout': 10.0,
        'expected_status': [200],
        'auth_required': False
    },
    'groq': {
        'url': 'https://api.groq.com/openai/v1/models',
        'method': 'GET',
        'timeout': 10.0,
        'expected_status': [200, 401],  # 401 = no auth, but API is up
        'auth_required': False
    },
    'together': {
        'url': 'https://api.together.xyz/v1/models',
        'method': 'GET',
        'timeout': 10.0,
        'expected_status': [200, 401],
        'auth_required': False
    },
    'fireworks': {
        'url': 'https://api.fireworks.ai/inference/v1/models',
        'method': 'GET',
        'timeout': 10.0,
        'expected_status': [200, 401],
        'auth_required': False
    },
    'huggingface': {
        'url': 'https://api-inference.huggingface.co/models',
        'method': 'GET',
        'timeout': 10.0,
        'expected_status': [200],
        'auth_required': False
    },
    'cohere': {
        'url': 'https://api.cohere.ai/v1/models',
        'method': 'GET',
        'timeout': 10.0,
        'expected_status': [200, 401],
        'auth_required': False
    },
    'replicate': {
        'url': 'https://api.replicate.com/v1/models',
        'method': 'GET',
        'timeout': 10.0,
        'expected_status': [200, 401],
        'auth_required': False
    }
}


# ============================================================================
# Health Status Types
# ============================================================================

class ProviderHealthStatus:
    """Provider health status constants"""
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    DOWN = 'down'
    UNKNOWN = 'unknown'


# ============================================================================
# LLM Health Monitor
# ============================================================================

class LLMHealthMonitor:
    """
    LLM Health Monitor

    Background service that:
    - Monitors provider API health every 5 minutes
    - Updates database with health status and response times
    - Automatically disables/enables providers based on health
    - Provides health check on-demand
    """

    def __init__(self, db_session_factory, check_interval_seconds: int = 300):
        """
        Initialize health monitor

        Args:
            db_session_factory: Callable that returns SQLAlchemy Session
            check_interval_seconds: How often to check health (default 300 = 5 minutes)
        """
        self.db_session_factory = db_session_factory
        self.check_interval = check_interval_seconds
        self.running = False
        self._task = None

    async def check_provider_health(
        self,
        provider_id: int,
        provider_slug: str,
        system_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check health of a single provider

        Args:
            provider_id: Provider database ID
            provider_slug: Provider slug (e.g., 'openai')
            system_api_key: System API key for auth (if available)

        Returns:
            Health check result with status and response time
        """
        # Get health check configuration
        health_config = PROVIDER_HEALTH_ENDPOINTS.get(provider_slug)

        if not health_config:
            logger.debug(f"No health endpoint configured for {provider_slug}")
            return {
                'provider_id': provider_id,
                'provider_slug': provider_slug,
                'status': ProviderHealthStatus.UNKNOWN,
                'response_time_ms': None,
                'error': 'No health endpoint configured'
            }

        try:
            start_time = datetime.utcnow()

            # Prepare request
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'UC-Cloud-Ops-Center/1.0'
            }

            # Add auth if available and required
            if health_config.get('auth_required') and system_api_key:
                if provider_slug == 'anthropic':
                    headers['x-api-key'] = system_api_key
                elif provider_slug == 'google':
                    # Google uses query param
                    pass
                else:
                    headers['Authorization'] = f"Bearer {system_api_key}"

            # Make request
            async with httpx.AsyncClient(timeout=health_config['timeout']) as client:
                if health_config['method'] == 'GET':
                    response = await client.get(
                        health_config['url'],
                        headers=headers
                    )
                else:  # POST
                    payload = health_config.get('test_payload', {})
                    response = await client.post(
                        health_config['url'],
                        headers=headers,
                        json=payload
                    )

                end_time = datetime.utcnow()
                response_time_ms = int((end_time - start_time).total_seconds() * 1000)

                # Check if response is expected
                if response.status_code in health_config['expected_status']:
                    status = ProviderHealthStatus.HEALTHY
                    error = None
                elif response.status_code >= 500:
                    status = ProviderHealthStatus.DOWN
                    error = f"Server error: {response.status_code}"
                elif response.status_code == 429:
                    status = ProviderHealthStatus.DEGRADED
                    error = "Rate limited"
                else:
                    status = ProviderHealthStatus.DEGRADED
                    error = f"Unexpected status: {response.status_code}"

                logger.debug(
                    f"Health check for {provider_slug}: {status} ({response_time_ms}ms)"
                )

                return {
                    'provider_id': provider_id,
                    'provider_slug': provider_slug,
                    'status': status,
                    'response_time_ms': response_time_ms,
                    'status_code': response.status_code,
                    'error': error
                }

        except httpx.TimeoutException:
            logger.warning(f"Health check timeout for {provider_slug}")
            return {
                'provider_id': provider_id,
                'provider_slug': provider_slug,
                'status': ProviderHealthStatus.DOWN,
                'response_time_ms': None,
                'error': 'Timeout'
            }
        except httpx.ConnectError:
            logger.warning(f"Connection error for {provider_slug}")
            return {
                'provider_id': provider_id,
                'provider_slug': provider_slug,
                'status': ProviderHealthStatus.DOWN,
                'response_time_ms': None,
                'error': 'Connection refused'
            }
        except Exception as e:
            logger.error(f"Health check error for {provider_slug}: {e}", exc_info=True)
            return {
                'provider_id': provider_id,
                'provider_slug': provider_slug,
                'status': ProviderHealthStatus.UNKNOWN,
                'response_time_ms': None,
                'error': str(e)
            }

    async def update_provider_status(
        self,
        provider_id: int,
        status: str,
        response_time_ms: Optional[int],
        auto_disable: bool = True
    ) -> bool:
        """
        Update provider health status in database

        Args:
            provider_id: Provider database ID
            status: Health status
            response_time_ms: Response time in milliseconds
            auto_disable: Automatically disable provider if down

        Returns:
            True if updated successfully
        """
        try:
            db = self.db_session_factory()

            try:
                provider = db.query(LLMProvider).filter(
                    LLMProvider.id == provider_id
                ).first()

                if not provider:
                    logger.warning(f"Provider {provider_id} not found")
                    return False

                # Update health status
                provider.health_status = status
                provider.health_last_checked = datetime.utcnow()
                if response_time_ms is not None:
                    provider.health_response_time_ms = response_time_ms

                # Auto-disable if down (unless it's a system provider)
                if auto_disable and status == ProviderHealthStatus.DOWN:
                    if not provider.is_system_provider:
                        old_active = provider.is_active
                        provider.is_active = False
                        if old_active:
                            logger.warning(
                                f"Provider {provider.provider_name} auto-disabled due to health check failure"
                            )

                # Auto-enable if healthy and was disabled by health check
                if status == ProviderHealthStatus.HEALTHY and not provider.is_active:
                    # Only auto-enable if it was disabled by health check (not manually)
                    # Check if last health status was DOWN
                    if provider.health_status == ProviderHealthStatus.DOWN:
                        provider.is_active = True
                        logger.info(
                            f"Provider {provider.provider_name} auto-enabled after health recovery"
                        )

                db.commit()
                return True

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error updating provider status: {e}", exc_info=True)
            return False

    async def check_all_providers(self) -> List[Dict[str, Any]]:
        """
        Check health of all active providers

        Returns:
            List of health check results
        """
        try:
            db = self.db_session_factory()

            try:
                # Get all providers that should be monitored
                providers = db.query(LLMProvider).filter(
                    LLMProvider.is_active == True
                ).all()

                logger.info(f"Running health checks for {len(providers)} providers")

                # Check all providers concurrently
                tasks = []
                for provider in providers:
                    tasks.append(
                        self.check_provider_health(
                            provider.id,
                            provider.provider_slug,
                            None  # No system API keys for now
                        )
                    )

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Update database with results
                successful_updates = 0
                for result in results:
                    if isinstance(result, dict):
                        updated = await self.update_provider_status(
                            result['provider_id'],
                            result['status'],
                            result.get('response_time_ms')
                        )
                        if updated:
                            successful_updates += 1
                    else:
                        logger.error(f"Health check task failed: {result}")

                logger.info(
                    f"Health check complete: {successful_updates}/{len(providers)} updated"
                )

                return [r for r in results if isinstance(r, dict)]

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error checking all providers: {e}", exc_info=True)
            return []

    async def get_healthy_providers(self) -> List[LLMProvider]:
        """
        Get list of healthy providers

        Returns:
            List of healthy LLMProvider objects
        """
        try:
            db = self.db_session_factory()

            try:
                providers = db.query(LLMProvider).filter(
                    and_(
                        LLMProvider.is_active == True,
                        LLMProvider.health_status.in_([
                            ProviderHealthStatus.HEALTHY,
                            ProviderHealthStatus.DEGRADED
                        ])
                    )
                ).all()

                return providers

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error getting healthy providers: {e}", exc_info=True)
            return []

    async def _run_health_checks_loop(self):
        """Background loop that runs health checks periodically"""
        logger.info(f"Health monitor started (interval: {self.check_interval}s)")

        while self.running:
            try:
                # Run health checks
                await self.check_all_providers()

                # Wait for next interval
                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                logger.info("Health monitor task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}", exc_info=True)
                # Continue after error, wait a bit before retrying
                await asyncio.sleep(60)

        logger.info("Health monitor stopped")

    def start(self):
        """Start the health monitor background task"""
        if self.running:
            logger.warning("Health monitor already running")
            return

        self.running = True
        self._task = asyncio.create_task(self._run_health_checks_loop())
        logger.info("Health monitor task created")

    async def stop(self):
        """Stop the health monitor background task"""
        if not self.running:
            return

        self.running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Health monitor stopped")


# ============================================================================
# Module-level Functions
# ============================================================================

def get_health_monitor(db_session_factory, check_interval: int = 300) -> LLMHealthMonitor:
    """
    Get health monitor instance

    Args:
        db_session_factory: Callable that returns SQLAlchemy Session
        check_interval: Check interval in seconds

    Returns:
        LLMHealthMonitor instance
    """
    return LLMHealthMonitor(db_session_factory, check_interval)
