"""
Provider Registry for Local Inference

Manages registration, discovery, and lifecycle of inference providers.
Supports auto-detection of running providers and dynamic provider loading.

Author: Ops-Center Backend Team
Created: 2026-01-24
"""

import asyncio
import logging
from typing import Dict, List, Optional, Type, Any
from datetime import datetime, timedelta
import httpx

from .base_provider import (
    LocalInferenceProvider,
    ProviderSettings,
    ProviderStatus,
    HealthCheckResult,
    ProviderNotAvailableError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Provider Registration Decorator
# =============================================================================

# Storage for registered provider classes
_registered_providers: Dict[str, Type[LocalInferenceProvider]] = {}


def register_provider(name: str):
    """
    Decorator to register a provider class.

    Usage:
        @register_provider("ollama")
        class OllamaProvider(LocalInferenceProvider):
            ...
    """
    def decorator(cls: Type[LocalInferenceProvider]):
        _registered_providers[name] = cls
        cls.provider_name = name
        logger.debug(f"Registered provider: {name}")
        return cls
    return decorator


def get_registered_providers() -> Dict[str, Type[LocalInferenceProvider]]:
    """Get all registered provider classes"""
    return _registered_providers.copy()


# =============================================================================
# Provider Registry
# =============================================================================

class ProviderRegistry:
    """
    Registry for managing local inference providers.

    Features:
    - Register and manage multiple provider backends
    - Auto-detect running providers
    - Health monitoring and status tracking
    - Dynamic provider enable/disable
    - Singleton pattern for global access

    Usage:
        registry = ProviderRegistry()
        await registry.initialize()

        # Auto-detect running providers
        await registry.auto_detect()

        # Get active providers
        providers = await registry.get_active_providers()

        # Get specific provider
        ollama = registry.get_provider("ollama")
    """

    _instance: Optional["ProviderRegistry"] = None

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize registry (runs only once due to singleton)"""
        if not hasattr(self, '_providers'):
            self._providers: Dict[str, LocalInferenceProvider] = {}
            self._health_cache: Dict[str, HealthCheckResult] = {}
            self._health_cache_ttl: timedelta = timedelta(seconds=30)
            self._last_health_check: Dict[str, datetime] = {}
            self._default_settings: Dict[str, ProviderSettings] = {}
            self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the registry and all registered providers"""
        if self._initialized:
            return

        logger.info("Initializing provider registry...")

        # Set up default settings for known providers
        self._default_settings = {
            "ollama": ProviderSettings(
                url="http://localhost:11434",
                enabled=True,
                idle_timeout_seconds=300,
                max_loaded_models=3,
            ),
            "llama-cpp": ProviderSettings(
                url="http://localhost:8080",
                enabled=True,
                idle_timeout_seconds=600,
                max_loaded_models=1,
            ),
            "vllm": ProviderSettings(
                url="http://localhost:8000",
                enabled=True,
                idle_timeout_seconds=None,  # vLLM manages its own model
                max_loaded_models=1,
            ),
            "tabbyapi": ProviderSettings(
                url="http://localhost:5000",
                enabled=True,
                idle_timeout_seconds=300,
                max_loaded_models=2,
            ),
            "exllama": ProviderSettings(
                url="http://localhost:5005",
                enabled=True,
                idle_timeout_seconds=300,
                max_loaded_models=1,
            ),
        }

        self._initialized = True
        logger.info("Provider registry initialized")

    async def shutdown(self) -> None:
        """Shutdown all providers and cleanup resources"""
        logger.info("Shutting down provider registry...")

        for name, provider in self._providers.items():
            try:
                await provider.cleanup()
                logger.debug(f"Cleaned up provider: {name}")
            except Exception as e:
                logger.error(f"Error cleaning up {name}: {e}")

        self._providers.clear()
        self._health_cache.clear()
        self._initialized = False

        logger.info("Provider registry shutdown complete")

    # =========================================================================
    # Provider Management
    # =========================================================================

    def register(
        self,
        provider: LocalInferenceProvider,
        override: bool = False
    ) -> None:
        """
        Register a provider instance.

        Args:
            provider: Provider instance to register
            override: If True, override existing provider with same name
        """
        name = provider.provider_name

        if name in self._providers and not override:
            logger.warning(f"Provider {name} already registered, skipping")
            return

        self._providers[name] = provider
        logger.info(f"Registered provider instance: {name}")

    def unregister(self, name: str) -> Optional[LocalInferenceProvider]:
        """
        Unregister a provider.

        Args:
            name: Provider name to unregister

        Returns:
            Removed provider instance, or None if not found
        """
        provider = self._providers.pop(name, None)
        self._health_cache.pop(name, None)
        self._last_health_check.pop(name, None)

        if provider:
            logger.info(f"Unregistered provider: {name}")

        return provider

    def get_provider(self, name: str) -> Optional[LocalInferenceProvider]:
        """
        Get a registered provider by name.

        Args:
            name: Provider name

        Returns:
            Provider instance or None if not found
        """
        return self._providers.get(name)

    def get_all_providers(self) -> Dict[str, LocalInferenceProvider]:
        """Get all registered provider instances"""
        return self._providers.copy()

    async def get_active_providers(self) -> List[LocalInferenceProvider]:
        """
        Get all active (enabled and healthy) providers.

        Returns:
            List of active provider instances
        """
        active = []

        for name, provider in self._providers.items():
            if not provider.settings.enabled:
                continue

            try:
                health = await self.check_health(name)
                if health.status == ProviderStatus.ONLINE:
                    active.append(provider)
            except Exception as e:
                logger.debug(f"Provider {name} not active: {e}")

        return active

    # =========================================================================
    # Auto-Detection
    # =========================================================================

    async def auto_detect(
        self,
        timeout: float = 2.0,
        provider_names: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Auto-detect running providers by checking health endpoints.

        Args:
            timeout: Timeout for health checks
            provider_names: Specific providers to check (None = all known)

        Returns:
            Dictionary of provider_name -> is_detected
        """
        async with self._lock:
            logger.info("Auto-detecting local inference providers...")

            results = {}
            providers_to_check = provider_names or list(self._default_settings.keys())

            # Check each provider in parallel
            tasks = []
            for name in providers_to_check:
                settings = self._default_settings.get(name)
                if settings:
                    tasks.append(self._detect_provider(name, settings, timeout))

            detection_results = await asyncio.gather(*tasks, return_exceptions=True)

            for name, result in zip(providers_to_check, detection_results):
                if isinstance(result, Exception):
                    results[name] = False
                    logger.debug(f"Provider {name} not detected: {result}")
                else:
                    results[name] = result
                    if result:
                        logger.info(f"Detected provider: {name}")

            return results

    async def _detect_provider(
        self,
        name: str,
        settings: ProviderSettings,
        timeout: float
    ) -> bool:
        """
        Detect if a specific provider is running.

        Returns:
            True if provider is detected and responding
        """
        # Known health endpoints for different providers
        health_endpoints = {
            "ollama": "/api/version",
            "llama-cpp": "/health",
            "vllm": "/health",
            "tabbyapi": "/v1/health",
            "exllama": "/health",
        }

        endpoint = health_endpoints.get(name, "/health")
        url = f"{settings.url.rstrip('/')}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    # Provider is responding, create and register instance
                    await self._create_and_register_provider(name, settings)
                    return True

        except httpx.ConnectError:
            pass  # Provider not running
        except httpx.TimeoutException:
            pass  # Provider not responding in time
        except Exception as e:
            logger.debug(f"Error detecting {name}: {e}")

        return False

    async def _create_and_register_provider(
        self,
        name: str,
        settings: ProviderSettings
    ) -> None:
        """Create and register a provider instance"""
        # Check if we have a registered provider class
        provider_class = _registered_providers.get(name)

        if not provider_class:
            # Use a generic placeholder for unknown providers
            logger.warning(
                f"No provider class registered for {name}, "
                "using placeholder"
            )
            return

        # Create instance and initialize
        provider = provider_class(settings)
        await provider.initialize()

        # Register the instance
        self.register(provider, override=True)

    # =========================================================================
    # Health Monitoring
    # =========================================================================

    async def check_health(
        self,
        provider_name: str,
        force_refresh: bool = False
    ) -> HealthCheckResult:
        """
        Check health of a specific provider.

        Uses cached results unless expired or force_refresh is True.

        Args:
            provider_name: Provider name to check
            force_refresh: Force a fresh health check

        Returns:
            HealthCheckResult with current status
        """
        provider = self._providers.get(provider_name)

        if not provider:
            return HealthCheckResult(
                status=ProviderStatus.UNKNOWN,
                provider=provider_name,
                message="Provider not registered"
            )

        # Check cache
        if not force_refresh:
            cached = self._get_cached_health(provider_name)
            if cached:
                return cached

        # Perform health check
        try:
            result = await provider.health_check()
            self._cache_health(provider_name, result)
            return result
        except ProviderNotAvailableError:
            result = HealthCheckResult(
                status=ProviderStatus.OFFLINE,
                provider=provider_name,
                message="Provider not available"
            )
            self._cache_health(provider_name, result)
            return result
        except Exception as e:
            result = HealthCheckResult(
                status=ProviderStatus.UNKNOWN,
                provider=provider_name,
                message=str(e)
            )
            self._cache_health(provider_name, result)
            return result

    async def check_all_health(
        self,
        force_refresh: bool = False
    ) -> Dict[str, HealthCheckResult]:
        """
        Check health of all registered providers.

        Args:
            force_refresh: Force fresh health checks

        Returns:
            Dictionary of provider_name -> HealthCheckResult
        """
        results = {}
        tasks = []

        for name in self._providers:
            tasks.append(self.check_health(name, force_refresh))

        health_results = await asyncio.gather(*tasks, return_exceptions=True)

        for name, result in zip(self._providers.keys(), health_results):
            if isinstance(result, Exception):
                results[name] = HealthCheckResult(
                    status=ProviderStatus.UNKNOWN,
                    provider=name,
                    message=str(result)
                )
            else:
                results[name] = result

        return results

    def _get_cached_health(
        self,
        provider_name: str
    ) -> Optional[HealthCheckResult]:
        """Get cached health result if not expired"""
        last_check = self._last_health_check.get(provider_name)

        if last_check and datetime.now() - last_check < self._health_cache_ttl:
            return self._health_cache.get(provider_name)

        return None

    def _cache_health(
        self,
        provider_name: str,
        result: HealthCheckResult
    ) -> None:
        """Cache a health check result"""
        self._health_cache[provider_name] = result
        self._last_health_check[provider_name] = datetime.now()

    # =========================================================================
    # Configuration
    # =========================================================================

    def set_default_settings(
        self,
        provider_name: str,
        settings: ProviderSettings
    ) -> None:
        """
        Set default settings for a provider.

        Used during auto-detection if provider is found.
        """
        self._default_settings[provider_name] = settings

    def get_default_settings(
        self,
        provider_name: str
    ) -> Optional[ProviderSettings]:
        """Get default settings for a provider"""
        return self._default_settings.get(provider_name)

    def update_provider_settings(
        self,
        provider_name: str,
        settings: Dict[str, Any]
    ) -> Optional[ProviderSettings]:
        """
        Update settings for a registered provider.

        Args:
            provider_name: Provider to update
            settings: Settings to update

        Returns:
            Updated settings, or None if provider not found
        """
        provider = self._providers.get(provider_name)

        if not provider:
            return None

        # Update the provider's settings
        for key, value in settings.items():
            if hasattr(provider.settings, key):
                setattr(provider.settings, key, value)

        return provider.settings

    def enable_provider(self, provider_name: str) -> bool:
        """Enable a provider"""
        provider = self._providers.get(provider_name)
        if provider:
            provider.settings.enabled = True
            return True
        return False

    def disable_provider(self, provider_name: str) -> bool:
        """Disable a provider"""
        provider = self._providers.get(provider_name)
        if provider:
            provider.settings.enabled = False
            return True
        return False

    # =========================================================================
    # Utilities
    # =========================================================================

    def get_status_summary(self) -> Dict[str, Any]:
        """
        Get summary of all providers and their status.

        Returns:
            Dictionary with provider status summary
        """
        summary = {
            "total_providers": len(self._providers),
            "enabled_providers": sum(
                1 for p in self._providers.values()
                if p.settings.enabled
            ),
            "providers": {},
        }

        for name, provider in self._providers.items():
            health = self._health_cache.get(name)
            summary["providers"][name] = {
                "display_name": provider.display_name,
                "enabled": provider.settings.enabled,
                "url": provider.settings.url,
                "status": health.status if health else ProviderStatus.UNKNOWN,
                "last_check": self._last_health_check.get(name),
            }

        return summary


# =============================================================================
# Global Access
# =============================================================================

_registry: Optional[ProviderRegistry] = None


def get_registry() -> ProviderRegistry:
    """
    Get the global provider registry instance.

    Creates and returns the singleton registry instance.
    """
    global _registry

    if _registry is None:
        _registry = ProviderRegistry()

    return _registry


async def initialize_registry() -> ProviderRegistry:
    """
    Initialize and return the global registry.

    Convenience function for startup.
    """
    registry = get_registry()
    await registry.initialize()
    return registry


async def shutdown_registry() -> None:
    """
    Shutdown the global registry.

    Convenience function for cleanup.
    """
    global _registry

    if _registry:
        await _registry.shutdown()
        _registry = None
