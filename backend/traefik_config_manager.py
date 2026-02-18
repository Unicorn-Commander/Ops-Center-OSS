"""
Traefik Configuration Manager

Core module for managing Traefik configuration files.
Handles reading, writing, validation, backup, and rollback of Traefik configs.
"""

import os
import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import shutil
import asyncio
import logging
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

# Configuration paths
TRAEFIK_DYNAMIC_DIR = Path("/home/deploy/Infrastructure/traefik/dynamic")
TRAEFIK_BACKUP_DIR = Path("/home/deploy/Infrastructure/traefik/backups")
TRAEFIK_BACKUP_DIR.mkdir(parents=True, exist_ok=True)


class TraefikRouter(BaseModel):
    """Traefik HTTP router configuration"""
    rule: str = Field(..., description="Router rule (e.g., Host(`example.com`))")
    service: str = Field(..., description="Service name to route to")
    entryPoints: Optional[List[str]] = Field(default=["https"], description="Entry points")
    middlewares: Optional[List[str]] = Field(default=None, description="Middleware names")
    priority: Optional[int] = Field(default=None, description="Router priority")
    tls: Optional[Dict[str, Any]] = Field(default=None, description="TLS configuration")

    @validator('rule')
    def validate_rule(cls, v):
        """Validate router rule syntax"""
        if not v or len(v) < 5:
            raise ValueError("Router rule must be a valid Traefik rule")
        # Basic validation - should contain Host() or Path() or similar
        if not any(keyword in v for keyword in ['Host(', 'Path(', 'Method(', 'Headers(']):
            raise ValueError("Router rule must contain valid Traefik matcher (Host, Path, etc.)")
        return v


class TraefikService(BaseModel):
    """Traefik HTTP service configuration"""
    loadBalancer: Dict[str, Any] = Field(..., description="Load balancer configuration")

    @validator('loadBalancer')
    def validate_load_balancer(cls, v):
        """Validate load balancer has servers"""
        if 'servers' not in v or not v['servers']:
            raise ValueError("Load balancer must have at least one server")
        for server in v['servers']:
            if 'url' not in server:
                raise ValueError("Each server must have a URL")
        return v


class TraefikMiddleware(BaseModel):
    """Traefik middleware configuration"""
    type: str = Field(..., description="Middleware type")
    config: Dict[str, Any] = Field(..., description="Middleware configuration")


class TraefikConfig(BaseModel):
    """Complete Traefik configuration"""
    http: Dict[str, Any] = Field(default_factory=dict, description="HTTP configuration")
    tcp: Optional[Dict[str, Any]] = Field(default=None, description="TCP configuration")
    udp: Optional[Dict[str, Any]] = Field(default=None, description="UDP configuration")
    tls: Optional[Dict[str, Any]] = Field(default=None, description="TLS configuration")


class ValidationResult(BaseModel):
    """Configuration validation result"""
    valid: bool = Field(..., description="Whether configuration is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


class TraefikConfigManager:
    """
    Manager for Traefik dynamic configuration files.

    Features:
    - Read/write YAML configuration files
    - Validate configuration before applying
    - Automatic backup before changes
    - Rollback on errors
    - Configuration merging across multiple files
    """

    def __init__(self, dynamic_dir: Path = TRAEFIK_DYNAMIC_DIR):
        self.dynamic_dir = dynamic_dir
        self.backup_dir = TRAEFIK_BACKUP_DIR
        logger.info(f"TraefikConfigManager initialized with directory: {dynamic_dir}")

    async def get_current_config(self) -> TraefikConfig:
        """
        Get current Traefik configuration by merging all YAML files.

        Returns:
            TraefikConfig: Complete merged configuration
        """
        merged_config = {
            "http": {
                "routers": {},
                "services": {},
                "middlewares": {}
            }
        }

        try:
            # Read all YAML files in dynamic directory
            for yaml_file in self.dynamic_dir.glob("*.yml"):
                try:
                    with open(yaml_file, 'r') as f:
                        config = yaml.safe_load(f) or {}

                    # Merge HTTP routers
                    if 'http' in config:
                        if 'routers' in config['http']:
                            merged_config['http']['routers'].update(config['http']['routers'])
                        if 'services' in config['http']:
                            merged_config['http']['services'].update(config['http']['services'])
                        if 'middlewares' in config['http']:
                            merged_config['http']['middlewares'].update(config['http']['middlewares'])

                    # Merge TCP/UDP/TLS if present
                    for key in ['tcp', 'udp', 'tls']:
                        if key in config:
                            if key not in merged_config:
                                merged_config[key] = {}
                            merged_config[key].update(config[key])

                    logger.debug(f"Loaded config from {yaml_file.name}")
                except Exception as e:
                    logger.error(f"Error loading {yaml_file.name}: {e}")
                    continue

            return TraefikConfig(**merged_config)
        except Exception as e:
            logger.error(f"Error getting current config: {e}")
            raise

    async def get_config_file(self, filename: str) -> Dict[str, Any]:
        """
        Get configuration from a specific file.

        Args:
            filename: Name of the configuration file (e.g., 'domains.yml')

        Returns:
            Dict: Configuration from the file
        """
        file_path = self.dynamic_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {filename}")

        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}

    async def write_config_file(self, filename: str, config: Dict[str, Any]) -> bool:
        """
        Write configuration to a specific file.

        Args:
            filename: Name of the configuration file
            config: Configuration dictionary to write

        Returns:
            bool: True if successful
        """
        file_path = self.dynamic_dir / filename
        temp_path = self.dynamic_dir / f"{filename}.tmp"

        try:
            # Write to temporary file first
            with open(temp_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            # Atomic move
            shutil.move(str(temp_path), str(file_path))
            logger.info(f"Configuration written to {filename}")

            # Traefik will auto-reload via file watcher
            return True
        except Exception as e:
            logger.error(f"Error writing config file {filename}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise

    async def update_config(self, config: TraefikConfig) -> bool:
        """
        Update Traefik configuration (currently writes to domains.yml).
        Creates backup before updating.

        Args:
            config: New Traefik configuration

        Returns:
            bool: True if successful
        """
        try:
            # Validate first
            validation = await self.validate_config(config)
            if not validation.valid:
                raise ValueError(f"Invalid configuration: {validation.errors}")

            # Create backup
            backup_id = await self.backup_config()
            logger.info(f"Created backup: {backup_id}")

            # Write new configuration
            config_dict = config.dict(exclude_none=True)
            await self.write_config_file("domains.yml", config_dict)

            return True
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            raise

    async def validate_config(self, config: TraefikConfig) -> ValidationResult:
        """
        Validate Traefik configuration.

        Args:
            config: Configuration to validate

        Returns:
            ValidationResult: Validation result with errors/warnings
        """
        errors = []
        warnings = []

        try:
            # Validate HTTP routers
            if config.http and 'routers' in config.http:
                routers = config.http['routers']
                services = config.http.get('services', {})

                for router_name, router_config in routers.items():
                    try:
                        # Validate router
                        router = TraefikRouter(**router_config)

                        # Check if referenced service exists
                        if router.service not in services:
                            warnings.append(f"Router '{router_name}' references non-existent service '{router.service}'")

                        # Check middleware references
                        if router.middlewares:
                            available_middlewares = config.http.get('middlewares', {})
                            for mw in router.middlewares:
                                if mw not in available_middlewares:
                                    warnings.append(f"Router '{router_name}' references non-existent middleware '{mw}'")

                    except Exception as e:
                        errors.append(f"Invalid router '{router_name}': {str(e)}")

            # Validate HTTP services
            if config.http and 'services' in config.http:
                for service_name, service_config in config.http['services'].items():
                    try:
                        TraefikService(**service_config)
                    except Exception as e:
                        errors.append(f"Invalid service '{service_name}': {str(e)}")

            # Check for duplicate routes
            if config.http and 'routers' in config.http:
                rules = {}
                for router_name, router_config in config.http['routers'].items():
                    rule = router_config.get('rule')
                    if rule in rules:
                        warnings.append(f"Duplicate rule detected: '{rule}' in routers '{rules[rule]}' and '{router_name}'")
                    else:
                        rules[rule] = router_name

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    async def backup_config(self, filename: Optional[str] = None) -> str:
        """
        Create backup of current configuration.

        Args:
            filename: Specific file to backup (default: all files)

        Returns:
            str: Backup ID (timestamp)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(exist_ok=True)

        try:
            if filename:
                # Backup specific file
                source = self.dynamic_dir / filename
                if source.exists():
                    shutil.copy2(source, backup_path / filename)
            else:
                # Backup all YAML files
                for yaml_file in self.dynamic_dir.glob("*.yml"):
                    shutil.copy2(yaml_file, backup_path / yaml_file.name)

            logger.info(f"Created backup: {backup_id}")
            return backup_id
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise

    async def restore_config(self, backup_id: str) -> bool:
        """
        Restore configuration from backup.

        Args:
            backup_id: Backup ID to restore from

        Returns:
            bool: True if successful
        """
        backup_path = self.backup_dir / backup_id

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")

        try:
            # Restore all files from backup
            for backup_file in backup_path.glob("*.yml"):
                dest = self.dynamic_dir / backup_file.name
                shutil.copy2(backup_file, dest)
                logger.info(f"Restored {backup_file.name} from backup {backup_id}")

            return True
        except Exception as e:
            logger.error(f"Error restoring backup {backup_id}: {e}")
            raise

    async def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups.

        Returns:
            List of backup information dictionaries
        """
        backups = []

        for backup_dir in sorted(self.backup_dir.glob("backup_*"), reverse=True):
            files = list(backup_dir.glob("*.yml"))
            backup_info = {
                "id": backup_dir.name,
                "timestamp": backup_dir.stat().st_mtime,
                "files": [f.name for f in files],
                "size": sum(f.stat().st_size for f in files)
            }
            backups.append(backup_info)

        return backups

    async def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup.

        Args:
            backup_id: Backup ID to delete

        Returns:
            bool: True if successful
        """
        backup_path = self.backup_dir / backup_id

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")

        try:
            shutil.rmtree(backup_path)
            logger.info(f"Deleted backup: {backup_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting backup {backup_id}: {e}")
            raise

    async def get_router_conflicts(self, rule: str, exclude_router: Optional[str] = None) -> List[str]:
        """
        Check for router conflicts with the given rule.

        Args:
            rule: Router rule to check
            exclude_router: Router name to exclude from conflict check

        Returns:
            List of conflicting router names
        """
        config = await self.get_current_config()
        conflicts = []

        if config.http and 'routers' in config.http:
            for router_name, router_config in config.http['routers'].items():
                if router_name == exclude_router:
                    continue
                if router_config.get('rule') == rule:
                    conflicts.append(router_name)

        return conflicts


# Global instance
traefik_config_manager = TraefikConfigManager()
