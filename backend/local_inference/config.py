"""
Configuration Management for Local Inference Providers

Handles loading, saving, and managing configuration for local inference
providers. Supports both database and environment variable configuration.

Author: Ops-Center Backend Team
Created: 2026-01-24
"""

import os
import json
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration Models
# =============================================================================

class ProviderConfigStatus(str, Enum):
    """Provider configuration status"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    AUTO = "auto"  # Auto-detect and enable if available


class ProviderConfig(BaseModel):
    """Configuration for a single provider"""
    name: str = Field(..., description="Provider name (e.g., ollama, llama-cpp)")
    url: str = Field(..., description="Provider API URL")
    status: ProviderConfigStatus = Field(
        ProviderConfigStatus.AUTO,
        description="Provider enable status"
    )
    priority: int = Field(0, description="Provider priority (higher = preferred)")

    # Timeouts and limits
    idle_timeout_seconds: Optional[int] = Field(
        300,
        description="Idle timeout before unloading models"
    )
    max_loaded_models: Optional[int] = Field(
        3,
        description="Maximum models to keep loaded"
    )
    request_timeout_seconds: int = Field(
        30,
        description="HTTP request timeout"
    )

    # Authentication
    api_key: Optional[str] = Field(None, description="API key if required")

    # GPU settings
    default_gpu_layers: Optional[int] = Field(
        None,
        description="Default GPU layers for loading"
    )
    default_context_size: Optional[int] = Field(
        None,
        description="Default context window size"
    )

    # Extra provider-specific settings
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific settings"
    )


class GlobalConfig(BaseModel):
    """Global settings for local inference"""
    auto_detect_on_startup: bool = Field(
        True,
        description="Automatically detect providers on startup"
    )
    health_check_interval_seconds: int = Field(
        60,
        description="Interval between health checks"
    )
    default_provider: Optional[str] = Field(
        None,
        description="Default provider to use if multiple available"
    )

    # GPU management
    monitor_gpu_usage: bool = Field(
        True,
        description="Enable GPU usage monitoring"
    )
    gpu_memory_threshold_percent: int = Field(
        90,
        description="GPU memory threshold for warnings"
    )

    # Model management
    auto_unload_on_idle: bool = Field(
        True,
        description="Auto-unload models after idle timeout"
    )
    preload_models: List[str] = Field(
        default_factory=list,
        description="Models to preload on startup"
    )


class LocalInferenceConfig(BaseModel):
    """Complete configuration for local inference system"""
    version: str = Field("1.0", description="Config version")
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    updated_by: Optional[str] = Field(None, description="Who updated the config")

    # Global settings
    global_config: GlobalConfig = Field(
        default_factory=GlobalConfig,
        description="Global settings"
    )

    # Provider configurations
    providers: Dict[str, ProviderConfig] = Field(
        default_factory=dict,
        description="Provider configurations by name"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# =============================================================================
# Default Configuration
# =============================================================================

def get_default_config() -> LocalInferenceConfig:
    """
    Get default configuration with common providers.

    Returns:
        Default LocalInferenceConfig with standard settings
    """
    return LocalInferenceConfig(
        version="1.0",
        global_config=GlobalConfig(),
        providers={
            "ollama": ProviderConfig(
                name="ollama",
                url="http://localhost:11434",
                status=ProviderConfigStatus.AUTO,
                priority=100,
                idle_timeout_seconds=300,
                max_loaded_models=3,
            ),
            "llama-cpp": ProviderConfig(
                name="llama-cpp",
                url="http://localhost:8080",
                status=ProviderConfigStatus.AUTO,
                priority=90,
                idle_timeout_seconds=600,
                max_loaded_models=1,
            ),
            "vllm": ProviderConfig(
                name="vllm",
                url="http://localhost:8000",
                status=ProviderConfigStatus.AUTO,
                priority=80,
                idle_timeout_seconds=None,  # vLLM manages its own model
                max_loaded_models=1,
            ),
            "tabbyapi": ProviderConfig(
                name="tabbyapi",
                url="http://localhost:5000",
                status=ProviderConfigStatus.AUTO,
                priority=70,
                idle_timeout_seconds=300,
                max_loaded_models=2,
            ),
            "exllama": ProviderConfig(
                name="exllama",
                url="http://localhost:5005",
                status=ProviderConfigStatus.AUTO,
                priority=60,
                idle_timeout_seconds=300,
                max_loaded_models=1,
            ),
        }
    )


# =============================================================================
# Environment Variable Loading
# =============================================================================

def load_config_from_env() -> LocalInferenceConfig:
    """
    Load configuration from environment variables.

    Environment variables:
        LOCAL_INFERENCE_OLLAMA_URL: Ollama API URL
        LOCAL_INFERENCE_OLLAMA_ENABLED: Enable Ollama (true/false)
        LOCAL_INFERENCE_LLAMA_CPP_URL: llama.cpp server URL
        LOCAL_INFERENCE_LLAMA_CPP_ENABLED: Enable llama.cpp
        LOCAL_INFERENCE_VLLM_URL: vLLM server URL
        LOCAL_INFERENCE_VLLM_ENABLED: Enable vLLM
        LOCAL_INFERENCE_DEFAULT_PROVIDER: Default provider name
        LOCAL_INFERENCE_AUTO_DETECT: Auto-detect providers (true/false)
        LOCAL_INFERENCE_HEALTH_INTERVAL: Health check interval in seconds
        LOCAL_INFERENCE_GPU_MONITOR: Enable GPU monitoring (true/false)
        LOCAL_INFERENCE_AUTO_UNLOAD: Auto-unload idle models (true/false)
        LOCAL_INFERENCE_PRELOAD_MODELS: Comma-separated list of models to preload

    Returns:
        LocalInferenceConfig populated from environment
    """
    config = get_default_config()

    # Global settings
    if os.getenv("LOCAL_INFERENCE_AUTO_DETECT"):
        config.global_config.auto_detect_on_startup = (
            os.getenv("LOCAL_INFERENCE_AUTO_DETECT", "true").lower() == "true"
        )

    if os.getenv("LOCAL_INFERENCE_HEALTH_INTERVAL"):
        try:
            config.global_config.health_check_interval_seconds = int(
                os.getenv("LOCAL_INFERENCE_HEALTH_INTERVAL")
            )
        except ValueError:
            pass

    if os.getenv("LOCAL_INFERENCE_DEFAULT_PROVIDER"):
        config.global_config.default_provider = os.getenv(
            "LOCAL_INFERENCE_DEFAULT_PROVIDER"
        )

    if os.getenv("LOCAL_INFERENCE_GPU_MONITOR"):
        config.global_config.monitor_gpu_usage = (
            os.getenv("LOCAL_INFERENCE_GPU_MONITOR", "true").lower() == "true"
        )

    if os.getenv("LOCAL_INFERENCE_AUTO_UNLOAD"):
        config.global_config.auto_unload_on_idle = (
            os.getenv("LOCAL_INFERENCE_AUTO_UNLOAD", "true").lower() == "true"
        )

    if os.getenv("LOCAL_INFERENCE_PRELOAD_MODELS"):
        models = os.getenv("LOCAL_INFERENCE_PRELOAD_MODELS", "").split(",")
        config.global_config.preload_models = [m.strip() for m in models if m.strip()]

    # Provider-specific settings
    provider_env_map = {
        "ollama": "OLLAMA",
        "llama-cpp": "LLAMA_CPP",
        "vllm": "VLLM",
        "tabbyapi": "TABBYAPI",
        "exllama": "EXLLAMA",
    }

    for provider_name, env_prefix in provider_env_map.items():
        provider = config.providers.get(provider_name)
        if not provider:
            continue

        # URL
        url_env = f"LOCAL_INFERENCE_{env_prefix}_URL"
        if os.getenv(url_env):
            provider.url = os.getenv(url_env)

        # Enabled status
        enabled_env = f"LOCAL_INFERENCE_{env_prefix}_ENABLED"
        if os.getenv(enabled_env):
            enabled = os.getenv(enabled_env, "auto").lower()
            if enabled == "true":
                provider.status = ProviderConfigStatus.ENABLED
            elif enabled == "false":
                provider.status = ProviderConfigStatus.DISABLED
            else:
                provider.status = ProviderConfigStatus.AUTO

        # API key
        key_env = f"LOCAL_INFERENCE_{env_prefix}_API_KEY"
        if os.getenv(key_env):
            provider.api_key = os.getenv(key_env)

        # Timeout
        timeout_env = f"LOCAL_INFERENCE_{env_prefix}_TIMEOUT"
        if os.getenv(timeout_env):
            try:
                provider.request_timeout_seconds = int(os.getenv(timeout_env))
            except ValueError:
                pass

        # Idle timeout
        idle_env = f"LOCAL_INFERENCE_{env_prefix}_IDLE_TIMEOUT"
        if os.getenv(idle_env):
            try:
                provider.idle_timeout_seconds = int(os.getenv(idle_env))
            except ValueError:
                pass

        # Max loaded models
        max_env = f"LOCAL_INFERENCE_{env_prefix}_MAX_MODELS"
        if os.getenv(max_env):
            try:
                provider.max_loaded_models = int(os.getenv(max_env))
            except ValueError:
                pass

    logger.info("Loaded local inference config from environment variables")
    return config


# =============================================================================
# Database Configuration
# =============================================================================

async def load_config_from_db() -> Optional[LocalInferenceConfig]:
    """
    Load configuration from database.

    Queries the local_inference_config table for the active configuration.

    Returns:
        LocalInferenceConfig if found, None otherwise
    """
    try:
        # Import here to avoid circular imports
        from ..database import get_db_connection

        conn = await get_db_connection()
        try:
            # Query the config table
            row = await conn.fetchrow(
                """
                SELECT config_data, updated_at, updated_by
                FROM local_inference_config
                WHERE is_active = true
                ORDER BY updated_at DESC
                LIMIT 1
                """
            )

            if row:
                config_data = json.loads(row["config_data"])
                config = LocalInferenceConfig(**config_data)
                config.updated_at = row["updated_at"]
                config.updated_by = row["updated_by"]
                logger.info("Loaded local inference config from database")
                return config

            logger.info("No local inference config found in database")
            return None

        finally:
            await conn.close()

    except ImportError:
        logger.warning("Database module not available, skipping DB config load")
        return None
    except Exception as e:
        logger.error(f"Error loading config from database: {e}")
        return None


async def save_config_to_db(
    config: LocalInferenceConfig,
    updated_by: str = "system"
) -> bool:
    """
    Save configuration to database.

    Creates or updates the active configuration.

    Args:
        config: Configuration to save
        updated_by: Username or identifier of who made the change

    Returns:
        True if saved successfully, False otherwise
    """
    try:
        from ..database import get_db_connection

        config.updated_at = datetime.now()
        config.updated_by = updated_by

        conn = await get_db_connection()
        try:
            # First, deactivate any existing active configs
            await conn.execute(
                """
                UPDATE local_inference_config
                SET is_active = false
                WHERE is_active = true
                """
            )

            # Insert new config
            await conn.execute(
                """
                INSERT INTO local_inference_config
                (config_data, is_active, updated_at, updated_by)
                VALUES ($1, true, $2, $3)
                """,
                json.dumps(config.dict()),
                config.updated_at,
                updated_by,
            )

            logger.info(f"Saved local inference config to database (by: {updated_by})")
            return True

        finally:
            await conn.close()

    except ImportError:
        logger.warning("Database module not available, skipping DB config save")
        return False
    except Exception as e:
        logger.error(f"Error saving config to database: {e}")
        return False


# =============================================================================
# Configuration Management
# =============================================================================

# Global config cache
_cached_config: Optional[LocalInferenceConfig] = None


async def get_config(
    force_refresh: bool = False
) -> LocalInferenceConfig:
    """
    Get the active configuration.

    Loads configuration in order of priority:
    1. Database configuration (if available)
    2. Environment variables
    3. Default configuration

    Args:
        force_refresh: Force reload from sources

    Returns:
        Active LocalInferenceConfig
    """
    global _cached_config

    if _cached_config is not None and not force_refresh:
        return _cached_config

    # Try database first
    config = await load_config_from_db()

    if config is None:
        # Fall back to environment variables
        config = load_config_from_env()

    _cached_config = config
    return config


async def save_config(
    config: LocalInferenceConfig,
    updated_by: str = "system"
) -> bool:
    """
    Save configuration.

    Saves to database if available, updates cache.

    Args:
        config: Configuration to save
        updated_by: Who made the change

    Returns:
        True if saved successfully
    """
    global _cached_config

    success = await save_config_to_db(config, updated_by)

    # Update cache regardless
    _cached_config = config

    return success


def clear_config_cache() -> None:
    """Clear the cached configuration"""
    global _cached_config
    _cached_config = None


# =============================================================================
# Provider Configuration Helpers
# =============================================================================

async def get_provider_config(provider_name: str) -> Optional[ProviderConfig]:
    """
    Get configuration for a specific provider.

    Args:
        provider_name: Provider name

    Returns:
        ProviderConfig if found, None otherwise
    """
    config = await get_config()
    return config.providers.get(provider_name)


async def update_provider_config(
    provider_name: str,
    updates: Dict[str, Any],
    updated_by: str = "system"
) -> Optional[ProviderConfig]:
    """
    Update configuration for a specific provider.

    Args:
        provider_name: Provider name
        updates: Dictionary of settings to update
        updated_by: Who made the change

    Returns:
        Updated ProviderConfig if successful, None otherwise
    """
    config = await get_config()
    provider = config.providers.get(provider_name)

    if not provider:
        return None

    # Apply updates
    for key, value in updates.items():
        if hasattr(provider, key):
            setattr(provider, key, value)

    # Save the updated config
    await save_config(config, updated_by)

    return provider


async def set_provider_status(
    provider_name: str,
    status: ProviderConfigStatus,
    updated_by: str = "system"
) -> bool:
    """
    Enable or disable a provider.

    Args:
        provider_name: Provider name
        status: New status
        updated_by: Who made the change

    Returns:
        True if successful
    """
    result = await update_provider_config(
        provider_name,
        {"status": status},
        updated_by
    )
    return result is not None


async def add_provider_config(
    provider: ProviderConfig,
    updated_by: str = "system"
) -> bool:
    """
    Add a new provider configuration.

    Args:
        provider: Provider configuration
        updated_by: Who made the change

    Returns:
        True if successful
    """
    config = await get_config()

    if provider.name in config.providers:
        logger.warning(f"Provider {provider.name} already exists")
        return False

    config.providers[provider.name] = provider

    return await save_config(config, updated_by)


async def remove_provider_config(
    provider_name: str,
    updated_by: str = "system"
) -> bool:
    """
    Remove a provider configuration.

    Args:
        provider_name: Provider name
        updated_by: Who made the change

    Returns:
        True if successful
    """
    config = await get_config()

    if provider_name not in config.providers:
        logger.warning(f"Provider {provider_name} not found")
        return False

    del config.providers[provider_name]

    return await save_config(config, updated_by)
