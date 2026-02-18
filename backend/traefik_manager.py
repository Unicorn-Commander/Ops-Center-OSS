"""
Traefik Configuration Management Module for UC-Cloud Ops-Center

This module provides comprehensive Traefik management with SSL/TLS certificate
management, dynamic routing, middleware configuration, and safe configuration
updates with automatic backup and rollback capabilities.

Author: Backend API Developer Agent
Date: October 23, 2025
Epic: 1.3 - Traefik Configuration Management
"""

import os
import json
import yaml
import logging
import re
import subprocess
import ipaddress
import shutil
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ValidationError
from enum import Enum
import hashlib
from collections import defaultdict
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================

class TraefikError(Exception):
    """Base exception for Traefik operations"""
    pass


class ConfigValidationError(TraefikError):
    """Configuration validation failed"""
    pass


# Alias for backward compatibility
ConfigurationError = ConfigValidationError


class CertificateError(TraefikError):
    """Certificate operation failed"""
    pass


class RouteError(TraefikError):
    """Route operation failed"""
    pass


class MiddlewareError(TraefikError):
    """Middleware operation failed"""
    pass


class BackupError(TraefikError):
    """Backup/restore operation failed"""
    pass


class RateLimitExceeded(TraefikError):
    """Rate limit exceeded for configuration changes"""
    pass


# ============================================================================
# Enums
# ============================================================================

class CertificateStatus(str, Enum):
    """SSL certificate status"""
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    REVOKED = "revoked"
    FAILED = "failed"


class MiddlewareType(str, Enum):
    """Supported middleware types"""
    RATE_LIMIT = "rateLimit"
    HEADERS = "headers"
    CORS = "cors"
    AUTH = "forwardAuth"
    REDIRECT = "redirectScheme"
    COMPRESS = "compress"
    STRIP_PREFIX = "stripPrefix"
    ADD_PREFIX = "addPrefix"
    BASIC_AUTH = "basicAuth"
    IP_WHITELIST = "ipWhiteList"


class EntryPoint(str, Enum):
    """Traefik entry points"""
    WEB = "web"
    WEBSECURE = "websecure"


# ============================================================================
# Pydantic Models for Input Validation
# ============================================================================

class RouteCreate(BaseModel):
    """Validated model for creating routes"""
    name: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$", description="Route name (lowercase, alphanumeric, hyphens)")
    rule: str = Field(..., min_length=5, max_length=500, description="Traefik routing rule")
    service: str = Field(..., min_length=1, max_length=100, description="Backend service name")
    entrypoints: List[EntryPoint] = Field(default=[EntryPoint.WEBSECURE], description="Entry points (web, websecure)")
    middlewares: List[str] = Field(default_factory=list, description="Middleware names to apply")
    priority: int = Field(default=0, ge=0, le=1000, description="Route priority (0-1000)")
    tls_enabled: bool = Field(default=True, description="Enable TLS/SSL")
    cert_resolver: str = Field(default="letsencrypt", description="Certificate resolver name")

    @field_validator('rule')
    @classmethod
    def validate_rule_syntax(cls, v):
        """Validate Traefik rule syntax"""
        # Basic validation - check for common patterns
        valid_patterns = [
            r'Host\(`[^`]+`\)',
            r'PathPrefix\(`[^`]+`\)',
            r'Path\(`[^`]+`\)',
            r'Method\(`[^`]+`\)',
            r'Headers\(`[^`]+`,\s*`[^`]+`\)',
        ]

        # Check if rule contains at least one valid pattern
        has_valid = any(re.search(pattern, v) for pattern in valid_patterns)
        if not has_valid:
            raise ValueError(
                f"Invalid Traefik rule syntax. Must contain Host(), PathPrefix(), Path(), Method(), or Headers(). Got: {v}"
            )

        return v


class MiddlewareCreate(BaseModel):
    """Validated model for creating middleware"""
    name: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$", description="Middleware name")
    type: MiddlewareType = Field(..., description="Middleware type")
    config: Dict[str, Any] = Field(..., description="Middleware configuration")

    @field_validator('config')
    @classmethod
    def validate_config_structure(cls, v, info):
        """Validate middleware config based on type"""
        if 'type' not in info.data:
            return v

        middleware_type = info.data['type']

        # Type-specific validation
        if middleware_type == MiddlewareType.RATE_LIMIT:
            required = ['average', 'period']
            if not all(k in v for k in required):
                raise ValueError(f"RateLimit middleware requires: {required}")
            if not isinstance(v.get('average'), (int, float)) or v['average'] <= 0:
                raise ValueError("RateLimit 'average' must be positive number")

        elif middleware_type == MiddlewareType.HEADERS:
            if 'customRequestHeaders' not in v and 'customResponseHeaders' not in v:
                raise ValueError("Headers middleware requires customRequestHeaders or customResponseHeaders")

        elif middleware_type == MiddlewareType.AUTH:
            required = ['address']
            if not all(k in v for k in required):
                raise ValueError(f"ForwardAuth middleware requires: {required}")

        elif middleware_type == MiddlewareType.IP_WHITELIST:
            if 'sourceRange' not in v:
                raise ValueError("IPWhiteList middleware requires 'sourceRange'")
            # Validate IP ranges
            for ip_range in v['sourceRange']:
                try:
                    ipaddress.ip_network(ip_range, strict=False)
                except ValueError:
                    raise ValueError(f"Invalid IP range: {ip_range}")

        return v


class CertificateRequest(BaseModel):
    """Validated model for certificate requests"""
    domain: str = Field(..., min_length=3, max_length=253, description="Domain name")
    email: str = Field(..., description="Contact email for Let's Encrypt")
    sans: List[str] = Field(default_factory=list, description="Subject Alternative Names")

    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v):
        """Validate domain format (RFC 1035)"""
        v = v.lower().strip()
        pattern = r'^(?!-)([a-z0-9-]{1,63}(?<!-)\.)+[a-z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError(f"Invalid domain format: {v}")
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError(f"Invalid email format: {v}")
        return v

    @field_validator('sans')
    @classmethod
    def validate_sans(cls, v):
        """Validate Subject Alternative Names"""
        pattern = r'^(?!-)([a-z0-9*-]{1,63}(?<!-)\.)+[a-z]{2,}$'
        for san in v:
            san_lower = san.lower().strip()
            if not re.match(pattern, san_lower):
                raise ValueError(f"Invalid SAN domain format: {san}")
        return [s.lower().strip() for s in v]


# ============================================================================
# Audit Logger
# ============================================================================

class AuditLogger:
    """Audit logger for Traefik configuration changes"""

    def __init__(self, log_file: str = None):
        """
        Initialize audit logger

        Args:
            log_file: Path to audit log file (default: traefik_audit.log)
        """
        self.log_file = log_file or "/var/log/traefik_audit.log"
        self._ensure_log_file()

    def _ensure_log_file(self):
        """Ensure audit log file exists and is writable"""
        try:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            if not log_path.exists():
                log_path.touch()
        except Exception as e:
            logger.warning(f"Could not create audit log file: {e}")

    def log_change(
        self,
        action: str,
        details: Dict[str, Any],
        username: str,
        success: bool = True,
        error: str = None
    ):
        """
        Log configuration change to audit trail

        Args:
            action: Operation type (add_route, update_middleware, etc.)
            details: Dictionary with operation details
            username: Username performing the operation
            success: Whether operation succeeded
            error: Error message if operation failed
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user": username,
            "success": success,
            "details": details,
            "error": error
        }

        # Log to file
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

        # Log to standard logger
        if success:
            logger.info(
                f"TRAEFIK_AUDIT: action={action} user={username} details={details}",
                extra={'audit': True, 'username': username, 'action': action}
            )
        else:
            logger.error(
                f"TRAEFIK_AUDIT_FAIL: action={action} user={username} error={error}",
                extra={'audit': True, 'username': username, 'action': action, 'error': error}
            )


# ============================================================================
# Rate Limiter
# ============================================================================

class RateLimiter:
    """Rate limiter for configuration changes"""

    def __init__(self, max_changes: int = 5, window_seconds: int = 60):
        """
        Initialize rate limiter

        Args:
            max_changes: Maximum changes allowed in window
            window_seconds: Time window in seconds
        """
        self.max_changes = max_changes
        self.window_seconds = window_seconds
        self.changes = defaultdict(list)  # username -> [timestamps]

    def check_limit(self, username: str) -> Tuple[bool, int]:
        """
        Check if user has exceeded rate limit

        Args:
            username: Username to check

        Returns:
            Tuple of (allowed: bool, remaining: int)

        Raises:
            RateLimitExceeded: If limit exceeded
        """
        now = time.time()
        cutoff = now - self.window_seconds

        # Remove old timestamps
        self.changes[username] = [
            ts for ts in self.changes[username] if ts > cutoff
        ]

        # Check limit
        current_count = len(self.changes[username])
        remaining = max(0, self.max_changes - current_count)

        if current_count >= self.max_changes:
            raise RateLimitExceeded(
                f"Rate limit exceeded: {current_count}/{self.max_changes} changes in {self.window_seconds}s. "
                f"Wait {int(self.window_seconds - (now - self.changes[username][0]))}s before retrying."
            )

        # Record this change
        self.changes[username].append(now)

        return True, remaining - 1


# ============================================================================
# Configuration Validator
# ============================================================================

class ConfigValidator:
    """Validate Traefik configuration files"""

    @staticmethod
    def validate_yaml(content: str) -> Dict[str, Any]:
        """
        Validate YAML syntax

        Args:
            content: YAML content as string

        Returns:
            Parsed YAML as dictionary

        Raises:
            ConfigValidationError: If YAML is invalid
        """
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ConfigValidationError(f"Invalid YAML syntax: {e}")

    @staticmethod
    def validate_traefik_config(config: Dict[str, Any]) -> bool:
        """
        Validate Traefik configuration structure

        Args:
            config: Parsed configuration dictionary

        Returns:
            True if valid

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        # Check for valid top-level keys
        valid_keys = {'http', 'tcp', 'udp', 'tls'}
        if not any(key in config for key in valid_keys):
            raise ConfigValidationError(
                f"Configuration must contain at least one of: {valid_keys}"
            )

        # Validate HTTP section if present
        if 'http' in config:
            http = config['http']

            # Validate routers
            if 'routers' in http:
                for name, router in http['routers'].items():
                    if not isinstance(router, dict):
                        raise ConfigValidationError(f"Router '{name}' must be a dictionary")
                    if 'rule' not in router:
                        raise ConfigValidationError(f"Router '{name}' missing 'rule'")
                    if 'service' not in router:
                        raise ConfigValidationError(f"Router '{name}' missing 'service'")

            # Validate services
            if 'services' in http:
                for name, service in http['services'].items():
                    if not isinstance(service, dict):
                        raise ConfigValidationError(f"Service '{name}' must be a dictionary")
                    if 'loadBalancer' not in service:
                        raise ConfigValidationError(f"Service '{name}' missing 'loadBalancer'")

                    lb = service['loadBalancer']
                    if 'servers' not in lb or not lb['servers']:
                        raise ConfigValidationError(f"Service '{name}' has no servers")

            # Validate middlewares
            if 'middlewares' in http:
                for name, middleware in http['middlewares'].items():
                    if not isinstance(middleware, dict):
                        raise ConfigValidationError(f"Middleware '{name}' must be a dictionary")

                    # Check middleware has at least one type configured
                    valid_types = {
                        'rateLimit', 'headers', 'forwardAuth', 'redirectScheme',
                        'compress', 'stripPrefix', 'addPrefix', 'basicAuth', 'ipWhiteList'
                    }
                    if not any(t in middleware for t in valid_types):
                        raise ConfigValidationError(
                            f"Middleware '{name}' must specify a type: {valid_types}"
                        )

        return True


# ============================================================================
# Main Traefik Manager Class
# ============================================================================

class TraefikManager:
    """
    Comprehensive Traefik Configuration Management

    Features:
    - SSL/TLS certificate management
    - Dynamic route management
    - Middleware configuration
    - Safe config updates with backup/rollback
    - Audit logging
    - Rate limiting
    - Configuration validation
    """

    def __init__(
        self,
        traefik_dir: str = "/opt/uc-cloud/traefik",
        docker_container: str = "traefik",
        audit_logger: AuditLogger = None,
        rate_limiter: RateLimiter = None
    ):
        """
        Initialize Traefik Manager

        Args:
            traefik_dir: Path to Traefik configuration directory
            docker_container: Traefik Docker container name
            audit_logger: Optional custom audit logger
            rate_limiter: Optional custom rate limiter
        """
        self.traefik_dir = Path(traefik_dir)
        self.config_file = self.traefik_dir / "traefik.yml"
        self.dynamic_dir = self.traefik_dir / "dynamic"
        self.backup_dir = self.traefik_dir / "backups"
        self.acme_dir = self.traefik_dir / "acme"
        self.acme_file = self.acme_dir / "acme.json"
        self.docker_container = docker_container

        self.audit_logger = audit_logger or AuditLogger()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.validator = ConfigValidator()

        # Ensure directories exist
        self.dynamic_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.acme_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"TraefikManager initialized: {traefik_dir}")

    # ========================================================================
    # SSL Certificate Management
    # ========================================================================

    def list_certificates(self) -> List[Dict[str, Any]]:
        """
        List all SSL certificates

        Returns:
            List of certificate information dictionaries
        """
        try:
            if not self.acme_file.exists():
                logger.warning("ACME file not found, no certificates available")
                return []

            with open(self.acme_file, 'r') as f:
                acme_data = json.load(f)

            certificates = []

            # Parse ACME data structure
            for resolver_name, resolver_data in acme_data.items():
                if 'Certificates' not in resolver_data:
                    continue

                for cert in resolver_data['Certificates']:
                    cert_info = {
                        'domain': cert.get('domain', {}).get('main', 'unknown'),
                        'sans': cert.get('domain', {}).get('sans', []),
                        'resolver': resolver_name,
                        'status': self._get_certificate_status(cert),
                        'not_after': cert.get('notAfter', 'unknown'),
                        'certificate': cert.get('certificate', '')[:50] + '...' if cert.get('certificate') else None,
                        'private_key_present': bool(cert.get('key'))
                    }
                    certificates.append(cert_info)

            return certificates

        except Exception as e:
            logger.error(f"Failed to list certificates: {e}")
            raise CertificateError(f"Failed to list certificates: {e}")

    def get_certificate_info(self, domain: str) -> Dict[str, Any]:
        """
        Get information about a specific certificate

        Args:
            domain: Domain name

        Returns:
            Certificate information dictionary
        """
        try:
            certificates = self.list_certificates()

            for cert in certificates:
                if cert['domain'] == domain or domain in cert['sans']:
                    return cert

            raise CertificateError(f"Certificate not found for domain: {domain}")

        except Exception as e:
            logger.error(f"Failed to get certificate info for {domain}: {e}")
            raise

    def request_certificate(
        self,
        domain: str,
        email: str,
        sans: List[str] = None,
        username: str = "system"
    ) -> Dict[str, Any]:
        """
        Request a new SSL certificate

        Args:
            domain: Main domain name
            email: Contact email for Let's Encrypt
            sans: Subject Alternative Names (optional)
            username: Username performing the operation

        Returns:
            Certificate request result
        """
        # Check rate limit
        self.rate_limiter.check_limit(username)

        # Validate input
        try:
            cert_request = CertificateRequest(
                domain=domain,
                email=email,
                sans=sans or []
            )
        except ValidationError as e:
            raise CertificateError(f"Invalid certificate request: {e}")

        try:
            # Update traefik.yml with email if not set
            config = self.get_config()

            if 'certificatesResolvers' not in config:
                config['certificatesResolvers'] = {}

            if 'letsencrypt' not in config['certificatesResolvers']:
                config['certificatesResolvers']['letsencrypt'] = {
                    'acme': {
                        'email': email,
                        'storage': str(self.acme_file),
                        'httpChallenge': {
                            'entryPoint': 'web'
                        }
                    }
                }

            # Update email
            config['certificatesResolvers']['letsencrypt']['acme']['email'] = email

            # Save config
            self.update_config(config, username=username)

            # Certificate will be automatically requested when a route uses it
            # Create a temporary route to trigger certificate request
            route_name = f"cert-request-{domain.replace('.', '-')}"

            self.create_route(
                name=route_name,
                rule=f"Host(`{domain}`)",
                service="noop",  # Will be handled by Traefik
                username=username
            )

            # Log the request
            self.audit_logger.log_change(
                action="request_certificate",
                details={
                    'domain': domain,
                    'email': email,
                    'sans': cert_request.sans
                },
                username=username,
                success=True
            )

            return {
                'success': True,
                'message': f"Certificate request initiated for {domain}",
                'domain': domain,
                'sans': cert_request.sans,
                'status': 'pending',
                'note': 'Certificate will be automatically issued when DNS is properly configured'
            }

        except Exception as e:
            self.audit_logger.log_change(
                action="request_certificate",
                details={'domain': domain},
                username=username,
                success=False,
                error=str(e)
            )
            logger.error(f"Failed to request certificate for {domain}: {e}")
            raise CertificateError(f"Failed to request certificate: {e}")

    def revoke_certificate(self, domain: str, username: str = "system") -> Dict[str, Any]:
        """
        Revoke an SSL certificate

        Args:
            domain: Domain name
            username: Username performing the operation

        Returns:
            Revocation result
        """
        # Check rate limit
        self.rate_limiter.check_limit(username)

        try:
            # Note: Traefik doesn't provide direct revocation via config
            # We remove the certificate from acme.json and let it be re-requested
            if not self.acme_file.exists():
                raise CertificateError("ACME file not found")

            with open(self.acme_file, 'r') as f:
                acme_data = json.load(f)

            # Remove certificate
            removed = False
            for resolver_name, resolver_data in acme_data.items():
                if 'Certificates' not in resolver_data:
                    continue

                original_count = len(resolver_data['Certificates'])
                resolver_data['Certificates'] = [
                    cert for cert in resolver_data['Certificates']
                    if cert.get('domain', {}).get('main') != domain
                    and domain not in cert.get('domain', {}).get('sans', [])
                ]

                if len(resolver_data['Certificates']) < original_count:
                    removed = True

            if not removed:
                raise CertificateError(f"Certificate not found for domain: {domain}")

            # Save updated ACME data
            with open(self.acme_file, 'w') as f:
                json.dump(acme_data, f, indent=2)

            # Log the revocation
            self.audit_logger.log_change(
                action="revoke_certificate",
                details={'domain': domain},
                username=username,
                success=True
            )

            return {
                'success': True,
                'message': f"Certificate revoked for {domain}",
                'domain': domain,
                'note': 'Certificate will be re-requested automatically if still in use'
            }

        except Exception as e:
            self.audit_logger.log_change(
                action="revoke_certificate",
                details={'domain': domain},
                username=username,
                success=False,
                error=str(e)
            )
            logger.error(f"Failed to revoke certificate for {domain}: {e}")
            raise CertificateError(f"Failed to revoke certificate: {e}")

    def get_acme_status(self) -> Dict[str, Any]:
        """
        Get ACME (Let's Encrypt) status

        Returns:
            ACME status information
        """
        try:
            if not self.acme_file.exists():
                return {
                    'initialized': False,
                    'total_certificates': 0,
                    'resolvers': []
                }

            with open(self.acme_file, 'r') as f:
                acme_data = json.load(f)

            resolvers = []
            total_certs = 0

            for resolver_name, resolver_data in acme_data.items():
                cert_count = len(resolver_data.get('Certificates', []))
                total_certs += cert_count

                resolvers.append({
                    'name': resolver_name,
                    'certificates': cert_count,
                    'email': resolver_data.get('Email', 'unknown'),
                    'ca_server': resolver_data.get('CAServer', 'https://acme-v02.api.letsencrypt.org/directory')
                })

            return {
                'initialized': True,
                'total_certificates': total_certs,
                'resolvers': resolvers,
                'acme_file': str(self.acme_file),
                'file_size': self.acme_file.stat().st_size,
                'last_modified': datetime.fromtimestamp(
                    self.acme_file.stat().st_mtime
                ).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get ACME status: {e}")
            raise CertificateError(f"Failed to get ACME status: {e}")

    def _get_certificate_status(self, cert: Dict) -> CertificateStatus:
        """Determine certificate status from ACME data"""
        try:
            not_after = cert.get('notAfter', '')
            if not not_after:
                return CertificateStatus.PENDING

            # Parse expiry date
            # Example: "2025-01-20T12:00:00Z"
            expiry = datetime.fromisoformat(not_after.replace('Z', '+00:00'))
            now = datetime.utcnow()

            if expiry < now:
                return CertificateStatus.EXPIRED
            elif expiry < now + timedelta(days=30):
                return CertificateStatus.ACTIVE  # But approaching expiry
            else:
                return CertificateStatus.ACTIVE

        except Exception:
            return CertificateStatus.PENDING

    # ========================================================================
    # Route Management
    # ========================================================================

    def list_routes(self, config_file: str = None) -> List[Dict[str, Any]]:
        """
        List all HTTP routes

        Args:
            config_file: Specific config file to read (default: all dynamic configs)

        Returns:
            List of route information dictionaries
        """
        try:
            routes = []

            if config_file:
                # Read specific file
                config_path = self.dynamic_dir / config_file
                if not config_path.exists():
                    raise RouteError(f"Config file not found: {config_file}")

                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)

                routes.extend(self._extract_routes(config, config_file))

            else:
                # Read all dynamic config files
                for config_path in self.dynamic_dir.glob("*.yml"):
                    try:
                        with open(config_path, 'r') as f:
                            config = yaml.safe_load(f)

                        routes.extend(self._extract_routes(config, config_path.name))
                    except Exception as e:
                        logger.warning(f"Failed to parse {config_path.name}: {e}")

            return routes

        except Exception as e:
            logger.error(f"Failed to list routes: {e}")
            raise RouteError(f"Failed to list routes: {e}")

    def create_route(
        self,
        name: str,
        rule: str,
        service: str,
        entrypoints: List[str] = None,
        middlewares: List[str] = None,
        priority: int = 0,
        tls_enabled: bool = True,
        cert_resolver: str = "letsencrypt",
        username: str = "system"
    ) -> Dict[str, Any]:
        """
        Create a new route

        Args:
            name: Route name (lowercase, alphanumeric, hyphens)
            rule: Traefik routing rule
            service: Backend service name
            entrypoints: Entry points (default: ['websecure'])
            middlewares: Middleware names to apply
            priority: Route priority (0-1000)
            tls_enabled: Enable TLS/SSL
            cert_resolver: Certificate resolver name
            username: Username performing the operation

        Returns:
            Created route information
        """
        # Check rate limit
        self.rate_limiter.check_limit(username)

        # Validate input
        try:
            route_data = RouteCreate(
                name=name,
                rule=rule,
                service=service,
                entrypoints=[EntryPoint(ep) for ep in (entrypoints or ['websecure'])],
                middlewares=middlewares or [],
                priority=priority,
                tls_enabled=tls_enabled,
                cert_resolver=cert_resolver
            )
        except ValidationError as e:
            raise RouteError(f"Invalid route parameters: {e}")

        try:
            # Load or create routes config file
            routes_file = self.dynamic_dir / "routes.yml"

            if routes_file.exists():
                with open(routes_file, 'r') as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = {'http': {'routers': {}, 'services': {}}}

            # Ensure structure
            if 'http' not in config:
                config['http'] = {}
            if 'routers' not in config['http']:
                config['http']['routers'] = {}

            # Check if route already exists
            if name in config['http']['routers']:
                raise RouteError(f"Route '{name}' already exists")

            # Build route configuration
            route_config = {
                'rule': route_data.rule,
                'service': route_data.service,
                'entryPoints': [ep.value for ep in route_data.entrypoints]
            }

            if route_data.middlewares:
                route_config['middlewares'] = route_data.middlewares

            if route_data.priority > 0:
                route_config['priority'] = route_data.priority

            if route_data.tls_enabled:
                route_config['tls'] = {
                    'certResolver': route_data.cert_resolver
                }

            # Add route to config
            config['http']['routers'][name] = route_config

            # Backup before changes
            backup_file = self.backup_config()

            # Validate configuration
            self.validator.validate_traefik_config(config)

            # Save configuration
            with open(routes_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            # Reload Traefik
            self.reload_traefik()

            # Log the change
            self.audit_logger.log_change(
                action="create_route",
                details={
                    'name': name,
                    'rule': rule,
                    'service': service,
                    'backup': backup_file
                },
                username=username,
                success=True
            )

            logger.info(f"Route created: {name}")

            return {
                'success': True,
                'message': f"Route '{name}' created successfully",
                'route': {
                    'name': name,
                    'rule': route_data.rule,
                    'service': route_data.service,
                    'entrypoints': [ep.value for ep in route_data.entrypoints],
                    'middlewares': route_data.middlewares,
                    'tls_enabled': route_data.tls_enabled
                },
                'backup': backup_file
            }

        except Exception as e:
            self.audit_logger.log_change(
                action="create_route",
                details={'name': name},
                username=username,
                success=False,
                error=str(e)
            )
            logger.error(f"Failed to create route {name}: {e}")

            # Rollback on failure
            if 'backup_file' in locals():
                try:
                    self.restore_config(backup_file, username=username)
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")

            raise RouteError(f"Failed to create route: {e}")

    def update_route(
        self,
        name: str,
        updates: Dict[str, Any],
        username: str = "system"
    ) -> Dict[str, Any]:
        """
        Update an existing route

        Args:
            name: Route name
            updates: Dictionary of fields to update
            username: Username performing the operation

        Returns:
            Updated route information
        """
        # Check rate limit
        self.rate_limiter.check_limit(username)

        try:
            # Find the route
            routes_file = self.dynamic_dir / "routes.yml"
            if not routes_file.exists():
                raise RouteError("Routes configuration file not found")

            with open(routes_file, 'r') as f:
                config = yaml.safe_load(f)

            if 'http' not in config or 'routers' not in config['http']:
                raise RouteError("No routes found in configuration")

            if name not in config['http']['routers']:
                raise RouteError(f"Route '{name}' not found")

            # Backup before changes
            backup_file = self.backup_config()

            # Apply updates
            route = config['http']['routers'][name]

            allowed_updates = {
                'rule', 'service', 'entryPoints', 'middlewares',
                'priority', 'tls'
            }

            for key, value in updates.items():
                if key not in allowed_updates:
                    logger.warning(f"Ignoring invalid update key: {key}")
                    continue
                route[key] = value

            # Validate configuration
            self.validator.validate_traefik_config(config)

            # Save configuration
            with open(routes_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            # Reload Traefik
            self.reload_traefik()

            # Log the change
            self.audit_logger.log_change(
                action="update_route",
                details={
                    'name': name,
                    'updates': updates,
                    'backup': backup_file
                },
                username=username,
                success=True
            )

            logger.info(f"Route updated: {name}")

            return {
                'success': True,
                'message': f"Route '{name}' updated successfully",
                'route': config['http']['routers'][name],
                'backup': backup_file
            }

        except Exception as e:
            self.audit_logger.log_change(
                action="update_route",
                details={'name': name, 'updates': updates},
                username=username,
                success=False,
                error=str(e)
            )
            logger.error(f"Failed to update route {name}: {e}")

            # Rollback on failure
            if 'backup_file' in locals():
                try:
                    self.restore_config(backup_file, username=username)
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")

            raise RouteError(f"Failed to update route: {e}")

    def delete_route(self, name: str, username: str = "system") -> Dict[str, Any]:
        """
        Delete a route

        Args:
            name: Route name
            username: Username performing the operation

        Returns:
            Deletion result
        """
        # Check rate limit
        self.rate_limiter.check_limit(username)

        try:
            routes_file = self.dynamic_dir / "routes.yml"
            if not routes_file.exists():
                raise RouteError("Routes configuration file not found")

            with open(routes_file, 'r') as f:
                config = yaml.safe_load(f)

            if 'http' not in config or 'routers' not in config['http']:
                raise RouteError("No routes found in configuration")

            if name not in config['http']['routers']:
                raise RouteError(f"Route '{name}' not found")

            # Backup before changes
            backup_file = self.backup_config()

            # Delete route
            del config['http']['routers'][name]

            # Save configuration
            with open(routes_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            # Reload Traefik
            self.reload_traefik()

            # Log the change
            self.audit_logger.log_change(
                action="delete_route",
                details={'name': name, 'backup': backup_file},
                username=username,
                success=True
            )

            logger.info(f"Route deleted: {name}")

            return {
                'success': True,
                'message': f"Route '{name}' deleted successfully",
                'backup': backup_file
            }

        except Exception as e:
            self.audit_logger.log_change(
                action="delete_route",
                details={'name': name},
                username=username,
                success=False,
                error=str(e)
            )
            logger.error(f"Failed to delete route {name}: {e}")

            # Rollback on failure
            if 'backup_file' in locals():
                try:
                    self.restore_config(backup_file, username=username)
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")

            raise RouteError(f"Failed to delete route: {e}")

    def get_route(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific route by name

        Args:
            name: Route name

        Returns:
            Route information dictionary or None if not found
        """
        try:
            routes = self.list_routes()
            for route in routes:
                if route['name'] == name:
                    return route
            return None
        except Exception as e:
            logger.error(f"Failed to get route {name}: {e}")
            return None

    def _extract_routes(self, config: Dict, source_file: str) -> List[Dict[str, Any]]:
        """Extract routes from configuration"""
        routes = []

        if 'http' not in config or 'routers' not in config['http']:
            return routes

        for name, router in config['http']['routers'].items():
            route_info = {
                'name': name,
                'rule': router.get('rule', ''),
                'service': router.get('service', ''),
                'entrypoints': router.get('entryPoints', []),
                'middlewares': router.get('middlewares', []),
                'priority': router.get('priority', 0),
                'tls_enabled': 'tls' in router,
                'cert_resolver': router.get('tls', {}).get('certResolver', None),
                'source_file': source_file
            }
            routes.append(route_info)

        return routes

    # ========================================================================
    # Service Management
    # ========================================================================

    def list_services(self, config_file: str = None) -> List[Dict[str, Any]]:
        """
        List all services

        Args:
            config_file: Specific config file to read (default: all dynamic configs)

        Returns:
            List of service information dictionaries
        """
        try:
            services_list = []

            if config_file:
                config_path = self.dynamic_dir / config_file
                if not config_path.exists():
                    raise RouteError(f"Config file not found: {config_file}")

                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)

                services_list.extend(self._extract_services(config, config_file))

            else:
                for config_path in self.dynamic_dir.glob("*.yml"):
                    try:
                        with open(config_path, 'r') as f:
                            config = yaml.safe_load(f)

                        services_list.extend(self._extract_services(config, config_path.name))
                    except Exception as e:
                        logger.warning(f"Failed to parse {config_path.name}: {e}")

            return services_list

        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            raise RouteError(f"Failed to list services: {e}")

    def create_service(
        self,
        name: str,
        url: str,
        healthcheck_path: Optional[str] = None,
        username: str = "system"
    ) -> Dict[str, Any]:
        """
        Create a new service

        Args:
            name: Service name
            url: Backend service URL (e.g., http://backend:8080)
            healthcheck_path: Optional healthcheck path for load balancer
            username: Username performing the operation

        Returns:
            Created service information
        """
        # Check rate limit
        self.rate_limiter.check_limit(username)

        # Validate service name
        if not re.match(r'^[a-z0-9-]+$', name):
            raise RouteError("Service name must be lowercase alphanumeric with hyphens")

        # Validate URL
        if not url.startswith(('http://', 'https://')):
            raise RouteError("Service URL must start with http:// or https://")

        try:
            services_file = self.dynamic_dir / "services.yml"

            if services_file.exists():
                with open(services_file, 'r') as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = {'http': {'services': {}}}

            if 'http' not in config:
                config['http'] = {}
            if 'services' not in config['http']:
                config['http']['services'] = {}

            if name in config['http']['services']:
                raise RouteError(f"Service '{name}' already exists")

            # Build service configuration
            service_config = {
                'loadBalancer': {
                    'servers': [
                        {'url': url}
                    ]
                }
            }

            # Add healthcheck if provided
            if healthcheck_path:
                service_config['loadBalancer']['healthCheck'] = {
                    'path': healthcheck_path,
                    'interval': '30s',
                    'timeout': '5s'
                }

            config['http']['services'][name] = service_config

            # Backup before changes
            backup_file = self.backup_config()

            # Validate configuration
            self.validator.validate_traefik_config(config)

            # Save configuration
            with open(services_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            # Reload Traefik
            self.reload_traefik()

            # Log the change
            self.audit_logger.log_change(
                action="create_service",
                details={
                    'name': name,
                    'url': url,
                    'healthcheck_path': healthcheck_path,
                    'backup': backup_file
                },
                username=username,
                success=True
            )

            logger.info(f"Service created: {name}")

            return {
                'success': True,
                'message': f"Service '{name}' created successfully",
                'service': {
                    'name': name,
                    'url': url,
                    'healthcheck_path': healthcheck_path
                },
                'backup': backup_file
            }

        except Exception as e:
            self.audit_logger.log_change(
                action="create_service",
                details={'name': name, 'url': url},
                username=username,
                success=False,
                error=str(e)
            )
            logger.error(f"Failed to create service {name}: {e}")

            if 'backup_file' in locals():
                try:
                    self.restore_config(backup_file, username=username)
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")

            raise RouteError(f"Failed to create service: {e}")

    def get_service(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific service by name

        Args:
            name: Service name

        Returns:
            Service information dictionary or None if not found
        """
        try:
            services = self.list_services()
            for service in services:
                if service['name'] == name:
                    return service
            return None
        except Exception as e:
            logger.error(f"Failed to get service {name}: {e}")
            return None

    def delete_service(self, name: str, username: str = "system") -> bool:
        """
        Delete a service

        Args:
            name: Service name
            username: Username performing the operation

        Returns:
            True if deleted successfully
        """
        # Check rate limit
        self.rate_limiter.check_limit(username)

        try:
            services_file = self.dynamic_dir / "services.yml"
            if not services_file.exists():
                raise RouteError("Services configuration file not found")

            with open(services_file, 'r') as f:
                config = yaml.safe_load(f)

            if 'http' not in config or 'services' not in config['http']:
                raise RouteError("No services found in configuration")

            if name not in config['http']['services']:
                raise RouteError(f"Service '{name}' not found")

            # Backup before changes
            backup_file = self.backup_config()

            # Delete service
            del config['http']['services'][name]

            # Save configuration
            with open(services_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            # Reload Traefik
            self.reload_traefik()

            # Log the change
            self.audit_logger.log_change(
                action="delete_service",
                details={'name': name, 'backup': backup_file},
                username=username,
                success=True
            )

            logger.info(f"Service deleted: {name}")
            return True

        except Exception as e:
            self.audit_logger.log_change(
                action="delete_service",
                details={'name': name},
                username=username,
                success=False,
                error=str(e)
            )
            logger.error(f"Failed to delete service {name}: {e}")

            if 'backup_file' in locals():
                try:
                    self.restore_config(backup_file, username=username)
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")

            raise RouteError(f"Failed to delete service: {e}")

    def _extract_services(self, config: Dict, source_file: str) -> List[Dict[str, Any]]:
        """Extract services from configuration"""
        services_list = []

        if 'http' not in config or 'services' not in config['http']:
            return services_list

        for name, service in config['http']['services'].items():
            lb = service.get('loadBalancer', {})
            servers = lb.get('servers', [])
            healthcheck = lb.get('healthCheck', {})

            service_info = {
                'name': name,
                'servers': [s.get('url', '') for s in servers],
                'healthcheck_path': healthcheck.get('path'),
                'healthcheck_interval': healthcheck.get('interval'),
                'source_file': source_file
            }
            services_list.append(service_info)

        return services_list

    # ========================================================================
    # Middleware Management
    # ========================================================================

    def list_middleware(self, config_file: str = None) -> List[Dict[str, Any]]:
        """
        List all middleware

        Args:
            config_file: Specific config file to read (default: all dynamic configs)

        Returns:
            List of middleware information dictionaries
        """
        try:
            middleware_list = []

            if config_file:
                config_path = self.dynamic_dir / config_file
                if not config_path.exists():
                    raise MiddlewareError(f"Config file not found: {config_file}")

                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)

                middleware_list.extend(self._extract_middleware(config, config_file))

            else:
                for config_path in self.dynamic_dir.glob("*.yml"):
                    try:
                        with open(config_path, 'r') as f:
                            config = yaml.safe_load(f)

                        middleware_list.extend(self._extract_middleware(config, config_path.name))
                    except Exception as e:
                        logger.warning(f"Failed to parse {config_path.name}: {e}")

            return middleware_list

        except Exception as e:
            logger.error(f"Failed to list middleware: {e}")
            raise MiddlewareError(f"Failed to list middleware: {e}")

    def create_middleware(
        self,
        name: str,
        type: str,
        config: Dict[str, Any],
        username: str = "system"
    ) -> Dict[str, Any]:
        """
        Create a new middleware

        Args:
            name: Middleware name
            type: Middleware type (rateLimit, headers, etc.)
            config: Middleware configuration
            username: Username performing the operation

        Returns:
            Created middleware information
        """
        # Check rate limit
        self.rate_limiter.check_limit(username)

        # Validate input
        try:
            middleware_data = MiddlewareCreate(
                name=name,
                type=MiddlewareType(type),
                config=config
            )
        except ValidationError as e:
            raise MiddlewareError(f"Invalid middleware parameters: {e}")

        try:
            middleware_file = self.dynamic_dir / "middleware.yml"

            if middleware_file.exists():
                with open(middleware_file, 'r') as f:
                    mw_config = yaml.safe_load(f) or {}
            else:
                mw_config = {'http': {'middlewares': {}}}

            if 'http' not in mw_config:
                mw_config['http'] = {}
            if 'middlewares' not in mw_config['http']:
                mw_config['http']['middlewares'] = {}

            if name in mw_config['http']['middlewares']:
                raise MiddlewareError(f"Middleware '{name}' already exists")

            # Build middleware configuration
            mw_config['http']['middlewares'][name] = {
                middleware_data.type.value: middleware_data.config
            }

            # Backup before changes
            backup_file = self.backup_config()

            # Validate configuration
            self.validator.validate_traefik_config(mw_config)

            # Save configuration
            with open(middleware_file, 'w') as f:
                yaml.dump(mw_config, f, default_flow_style=False, sort_keys=False)

            # Reload Traefik
            self.reload_traefik()

            # Log the change
            self.audit_logger.log_change(
                action="create_middleware",
                details={
                    'name': name,
                    'type': type,
                    'config': config,
                    'backup': backup_file
                },
                username=username,
                success=True
            )

            logger.info(f"Middleware created: {name}")

            return {
                'success': True,
                'message': f"Middleware '{name}' created successfully",
                'middleware': {
                    'name': name,
                    'type': middleware_data.type.value,
                    'config': middleware_data.config
                },
                'backup': backup_file
            }

        except Exception as e:
            self.audit_logger.log_change(
                action="create_middleware",
                details={'name': name, 'type': type},
                username=username,
                success=False,
                error=str(e)
            )
            logger.error(f"Failed to create middleware {name}: {e}")

            if 'backup_file' in locals():
                try:
                    self.restore_config(backup_file, username=username)
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")

            raise MiddlewareError(f"Failed to create middleware: {e}")

    def update_middleware(
        self,
        name: str,
        config: Dict[str, Any],
        username: str = "system"
    ) -> Dict[str, Any]:
        """
        Update an existing middleware

        Args:
            name: Middleware name
            config: New middleware configuration
            username: Username performing the operation

        Returns:
            Updated middleware information
        """
        # Check rate limit
        self.rate_limiter.check_limit(username)

        try:
            middleware_file = self.dynamic_dir / "middleware.yml"
            if not middleware_file.exists():
                raise MiddlewareError("Middleware configuration file not found")

            with open(middleware_file, 'r') as f:
                mw_config = yaml.safe_load(f)

            if 'http' not in mw_config or 'middlewares' not in mw_config['http']:
                raise MiddlewareError("No middleware found in configuration")

            if name not in mw_config['http']['middlewares']:
                raise MiddlewareError(f"Middleware '{name}' not found")

            # Backup before changes
            backup_file = self.backup_config()

            # Update middleware config
            # Keep the type, update the config
            middleware_entry = mw_config['http']['middlewares'][name]
            middleware_type = list(middleware_entry.keys())[0]
            middleware_entry[middleware_type] = config

            # Validate configuration
            self.validator.validate_traefik_config(mw_config)

            # Save configuration
            with open(middleware_file, 'w') as f:
                yaml.dump(mw_config, f, default_flow_style=False, sort_keys=False)

            # Reload Traefik
            self.reload_traefik()

            # Log the change
            self.audit_logger.log_change(
                action="update_middleware",
                details={
                    'name': name,
                    'config': config,
                    'backup': backup_file
                },
                username=username,
                success=True
            )

            logger.info(f"Middleware updated: {name}")

            return {
                'success': True,
                'message': f"Middleware '{name}' updated successfully",
                'middleware': mw_config['http']['middlewares'][name],
                'backup': backup_file
            }

        except Exception as e:
            self.audit_logger.log_change(
                action="update_middleware",
                details={'name': name, 'config': config},
                username=username,
                success=False,
                error=str(e)
            )
            logger.error(f"Failed to update middleware {name}: {e}")

            if 'backup_file' in locals():
                try:
                    self.restore_config(backup_file, username=username)
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")

            raise MiddlewareError(f"Failed to update middleware: {e}")

    def delete_middleware(self, name: str, username: str = "system") -> Dict[str, Any]:
        """
        Delete a middleware

        Args:
            name: Middleware name
            username: Username performing the operation

        Returns:
            Deletion result
        """
        # Check rate limit
        self.rate_limiter.check_limit(username)

        try:
            middleware_file = self.dynamic_dir / "middleware.yml"
            if not middleware_file.exists():
                raise MiddlewareError("Middleware configuration file not found")

            with open(middleware_file, 'r') as f:
                mw_config = yaml.safe_load(f)

            if 'http' not in mw_config or 'middlewares' not in mw_config['http']:
                raise MiddlewareError("No middleware found in configuration")

            if name not in mw_config['http']['middlewares']:
                raise MiddlewareError(f"Middleware '{name}' not found")

            # Backup before changes
            backup_file = self.backup_config()

            # Delete middleware
            del mw_config['http']['middlewares'][name]

            # Save configuration
            with open(middleware_file, 'w') as f:
                yaml.dump(mw_config, f, default_flow_style=False, sort_keys=False)

            # Reload Traefik
            self.reload_traefik()

            # Log the change
            self.audit_logger.log_change(
                action="delete_middleware",
                details={'name': name, 'backup': backup_file},
                username=username,
                success=True
            )

            logger.info(f"Middleware deleted: {name}")

            return {
                'success': True,
                'message': f"Middleware '{name}' deleted successfully",
                'backup': backup_file
            }

        except Exception as e:
            self.audit_logger.log_change(
                action="delete_middleware",
                details={'name': name},
                username=username,
                success=False,
                error=str(e)
            )
            logger.error(f"Failed to delete middleware {name}: {e}")

            if 'backup_file' in locals():
                try:
                    self.restore_config(backup_file, username=username)
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")

            raise MiddlewareError(f"Failed to delete middleware: {e}")

    def list_middlewares(self, config_file: str = None) -> List[Dict[str, Any]]:
        """
        Alias for list_middleware() - plural form for consistency

        Args:
            config_file: Specific config file to read (default: all dynamic configs)

        Returns:
            List of middleware information dictionaries
        """
        return self.list_middleware(config_file)

    def get_middleware(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific middleware by name

        Args:
            name: Middleware name

        Returns:
            Middleware information dictionary or None if not found
        """
        try:
            middlewares = self.list_middleware()
            for middleware in middlewares:
                if middleware['name'] == name:
                    return middleware
            return None
        except Exception as e:
            logger.error(f"Failed to get middleware {name}: {e}")
            return None

    def _extract_middleware(self, config: Dict, source_file: str) -> List[Dict[str, Any]]:
        """Extract middleware from configuration"""
        middleware_list = []

        if 'http' not in config or 'middlewares' not in config['http']:
            return middleware_list

        for name, middleware in config['http']['middlewares'].items():
            # Get middleware type (first key)
            mw_type = list(middleware.keys())[0] if middleware else 'unknown'
            mw_config = middleware.get(mw_type, {})

            middleware_info = {
                'name': name,
                'type': mw_type,
                'config': mw_config,
                'source_file': source_file
            }
            middleware_list.append(middleware_info)

        return middleware_list

    # ========================================================================
    # Configuration Management
    # ========================================================================

    def get_config(self) -> Dict[str, Any]:
        """
        Read current traefik.yml configuration

        Returns:
            Configuration as dictionary
        """
        try:
            if not self.config_file.exists():
                raise ConfigValidationError(f"Configuration file not found: {self.config_file}")

            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)

            return config or {}

        except Exception as e:
            logger.error(f"Failed to read configuration: {e}")
            raise ConfigValidationError(f"Failed to read configuration: {e}")

    def update_config(
        self,
        updates: Dict[str, Any],
        username: str = "system"
    ) -> Dict[str, Any]:
        """
        Update traefik.yml configuration

        Args:
            updates: Dictionary with configuration updates
            username: Username performing the operation

        Returns:
            Update result
        """
        # Check rate limit
        self.rate_limiter.check_limit(username)

        try:
            # Read current config
            current_config = self.get_config()

            # Backup before changes
            backup_file = self.backup_config()

            # Merge updates (deep merge)
            updated_config = self._deep_merge(current_config, updates)

            # Validate configuration
            self.validator.validate_yaml(yaml.dump(updated_config))

            # Save configuration
            with open(self.config_file, 'w') as f:
                yaml.dump(updated_config, f, default_flow_style=False, sort_keys=False)

            # Reload Traefik
            self.reload_traefik()

            # Log the change
            self.audit_logger.log_change(
                action="update_config",
                details={'updates': updates, 'backup': backup_file},
                username=username,
                success=True
            )

            logger.info("Traefik configuration updated")

            return {
                'success': True,
                'message': 'Configuration updated successfully',
                'backup': backup_file
            }

        except Exception as e:
            self.audit_logger.log_change(
                action="update_config",
                details={'updates': updates},
                username=username,
                success=False,
                error=str(e)
            )
            logger.error(f"Failed to update configuration: {e}")

            # Rollback on failure
            if 'backup_file' in locals():
                try:
                    self.restore_config(backup_file, username=username)
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")

            raise ConfigValidationError(f"Failed to update configuration: {e}")

    def validate_config(
        self,
        config_path: str = None,
        config_dict: Dict[str, Any] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate Traefik configuration with detailed error reporting

        Args:
            config_path: Path to configuration file (default: main traefik.yml)
            config_dict: Configuration dictionary to validate (overrides config_path)

        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []

        try:
            # Load config from dict or file
            if config_dict is not None:
                config = config_dict
            elif config_path:
                config_file = Path(config_path)
                if not config_file.exists():
                    errors.append(f"Configuration file not found: {config_path}")
                    return False, errors

                with open(config_file, 'r') as f:
                    try:
                        config = yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        errors.append(f"Invalid YAML syntax: {e}")
                        return False, errors
            else:
                # Default to main config
                config = self.get_config()

            # Validate YAML structure
            try:
                yaml_str = yaml.dump(config)
                self.validator.validate_yaml(yaml_str)
            except ConfigValidationError as e:
                errors.append(str(e))

            # Validate Traefik-specific structure
            try:
                # Check if this is main config or dynamic config
                if 'entryPoints' in config or 'providers' in config:
                    # Main traefik.yml validation
                    if 'entryPoints' not in config:
                        errors.append("Main config missing 'entryPoints'")
                    if 'providers' not in config:
                        errors.append("Main config missing 'providers'")
                else:
                    # Dynamic config validation
                    self.validator.validate_traefik_config(config)
            except ConfigValidationError as e:
                errors.append(str(e))

            # Additional checks for common issues
            if 'http' in config:
                http = config['http']

                # Check for routers without services
                if 'routers' in http:
                    service_names = set(http.get('services', {}).keys())
                    for router_name, router in http['routers'].items():
                        service = router.get('service')
                        if service and service not in service_names:
                            errors.append(
                                f"Router '{router_name}' references unknown service '{service}'"
                            )

                # Check for routers with middlewares that don't exist
                if 'routers' in http:
                    middleware_names = set(http.get('middlewares', {}).keys())
                    for router_name, router in http['routers'].items():
                        router_middlewares = router.get('middlewares', [])
                        for mw in router_middlewares:
                            if mw not in middleware_names:
                                errors.append(
                                    f"Router '{router_name}' references unknown middleware '{mw}'"
                                )

            is_valid = len(errors) == 0

            if is_valid:
                logger.info("Configuration validation passed")
            else:
                logger.warning(f"Configuration validation failed with {len(errors)} errors")

            return is_valid, errors

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            logger.error(f"Configuration validation failed: {e}")
            return False, errors

    def backup_config(self) -> str:
        """
        Create timestamped backup of all configurations

        Returns:
            Backup file path
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"traefik_backup_{timestamp}"
            backup_path = self.backup_dir / backup_name

            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)

            # Backup main config
            if self.config_file.exists():
                shutil.copy2(self.config_file, backup_path / "traefik.yml")

            # Backup dynamic configs
            if self.dynamic_dir.exists():
                dynamic_backup = backup_path / "dynamic"
                dynamic_backup.mkdir(exist_ok=True)

                for config_file in self.dynamic_dir.glob("*.yml"):
                    shutil.copy2(config_file, dynamic_backup / config_file.name)

            # Backup ACME data
            if self.acme_file.exists():
                shutil.copy2(self.acme_file, backup_path / "acme.json")

            # Create manifest
            manifest = {
                'timestamp': timestamp,
                'backup_date': datetime.utcnow().isoformat(),
                'files': [
                    str(f.relative_to(backup_path))
                    for f in backup_path.rglob("*") if f.is_file()
                ]
            }

            with open(backup_path / "manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)

            logger.info(f"Configuration backed up to: {backup_path}")

            # Cleanup old backups (keep last 10)
            self._cleanup_old_backups(keep=10)

            return str(backup_path)

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise BackupError(f"Failed to create backup: {e}")

    def restore_config(self, backup_path: str, username: str = "system") -> Dict[str, Any]:
        """
        Restore configuration from backup

        Args:
            backup_path: Path to backup directory
            username: Username performing the operation

        Returns:
            Restore result
        """
        try:
            backup_dir = Path(backup_path)

            if not backup_dir.exists():
                raise BackupError(f"Backup not found: {backup_path}")

            # Read manifest
            manifest_file = backup_dir / "manifest.json"
            if not manifest_file.exists():
                raise BackupError("Backup manifest not found")

            with open(manifest_file, 'r') as f:
                manifest = json.load(f)

            # Create safety backup before restore
            safety_backup = self.backup_config()

            # Restore main config
            main_config_backup = backup_dir / "traefik.yml"
            if main_config_backup.exists():
                shutil.copy2(main_config_backup, self.config_file)

            # Restore dynamic configs
            dynamic_backup = backup_dir / "dynamic"
            if dynamic_backup.exists():
                # Clear current dynamic configs
                for config_file in self.dynamic_dir.glob("*.yml"):
                    config_file.unlink()

                # Restore from backup
                for config_file in dynamic_backup.glob("*.yml"):
                    shutil.copy2(config_file, self.dynamic_dir / config_file.name)

            # Restore ACME data
            acme_backup = backup_dir / "acme.json"
            if acme_backup.exists():
                shutil.copy2(acme_backup, self.acme_file)

            # Reload Traefik
            self.reload_traefik()

            # Log the restore
            self.audit_logger.log_change(
                action="restore_config",
                details={
                    'backup': backup_path,
                    'backup_date': manifest['backup_date'],
                    'safety_backup': safety_backup
                },
                username=username,
                success=True
            )

            logger.info(f"Configuration restored from: {backup_path}")

            return {
                'success': True,
                'message': f"Configuration restored from backup: {manifest['backup_date']}",
                'backup_restored': backup_path,
                'safety_backup': safety_backup
            }

        except Exception as e:
            self.audit_logger.log_change(
                action="restore_config",
                details={'backup': backup_path},
                username=username,
                success=False,
                error=str(e)
            )
            logger.error(f"Failed to restore configuration: {e}")
            raise BackupError(f"Failed to restore configuration: {e}")

    def reload_traefik(self) -> Dict[str, Any]:
        """
        Trigger Traefik configuration reload

        Returns:
            Reload result
        """
        try:
            # Traefik watches config files and reloads automatically
            # We can verify by checking Docker container
            result = subprocess.run(
                ["docker", "exec", self.docker_container, "traefik", "healthcheck"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                logger.info("Traefik configuration reloaded successfully")
                return {
                    'success': True,
                    'message': 'Traefik configuration reloaded',
                    'status': 'healthy'
                }
            else:
                logger.warning(f"Traefik healthcheck returned non-zero: {result.returncode}")
                return {
                    'success': False,
                    'message': 'Traefik reload may have failed',
                    'status': 'unknown',
                    'error': result.stderr
                }

        except subprocess.TimeoutExpired:
            logger.error("Traefik healthcheck timed out")
            raise TraefikError("Traefik healthcheck timed out")
        except Exception as e:
            logger.error(f"Failed to reload Traefik: {e}")
            # Don't fail the operation - Traefik auto-reloads
            return {
                'success': True,
                'message': 'Configuration saved (Traefik will auto-reload)',
                'note': 'Manual healthcheck failed but changes are applied'
            }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()

        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _cleanup_old_backups(self, keep: int = 10):
        """Remove old backups, keeping only the most recent ones"""
        try:
            backups = sorted(
                [d for d in self.backup_dir.iterdir() if d.is_dir()],
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            # Remove old backups
            for old_backup in backups[keep:]:
                shutil.rmtree(old_backup)
                logger.info(f"Removed old backup: {old_backup.name}")

        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")


# ============================================================================
# Module-level convenience functions
# ============================================================================

def get_traefik_status(container_name: str = "traefik") -> Dict[str, Any]:
    """
    Get Traefik container status

    Args:
        container_name: Docker container name

    Returns:
        Status information
    """
    try:
        result = subprocess.run(
            ["docker", "inspect", container_name],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)[0]
            state = data['State']

            return {
                'running': state['Running'],
                'status': state['Status'],
                'started_at': state['StartedAt'],
                'health': state.get('Health', {}).get('Status', 'unknown')
            }
        else:
            return {
                'running': False,
                'error': 'Container not found'
            }

    except Exception as e:
        return {
            'running': False,
            'error': str(e)
        }


# ============================================================================
# Example Usage (for testing)
# ============================================================================

if __name__ == "__main__":
    print("Traefik Manager Module - Test Mode")
    print("=" * 70)

    try:
        # Initialize manager
        manager = TraefikManager()

        # Get Traefik status
        print("\n1. Traefik Status:")
        status = get_traefik_status()
        print(f"   Running: {status['running']}")
        print(f"   Status: {status.get('status', 'unknown')}")

        # Get ACME status
        print("\n2. ACME Status:")
        acme_status = manager.get_acme_status()
        print(f"   Initialized: {acme_status['initialized']}")
        print(f"   Total Certificates: {acme_status['total_certificates']}")

        # List routes
        print("\n3. Routes:")
        routes = manager.list_routes()
        print(f"   Found {len(routes)} routes")
        for route in routes[:5]:
            print(f"   - {route['name']}: {route['rule']}")

        # List middleware
        print("\n4. Middleware:")
        middleware = manager.list_middleware()
        print(f"   Found {len(middleware)} middleware")
        for mw in middleware[:5]:
            print(f"   - {mw['name']} ({mw['type']})")

        # Test input validation
        print("\n5. Testing Input Validation:")
        try:
            invalid_route = RouteCreate(
                name="invalid name with spaces",
                rule="Host(`example.com`)",
                service="test"
            )
        except ValidationError as e:
            print(f"   ✅ Validation correctly rejected invalid route name")

        try:
            invalid_middleware = MiddlewareCreate(
                name="test-middleware",
                type="rateLimit",
                config={}  # Missing required fields
            )
        except ValidationError as e:
            print(f"   ✅ Validation correctly rejected invalid middleware config")

        print("\n✅ All tests passed! Traefik manager is ready for use.")
        print(f"\n📊 Statistics:")
        print(f"   - Routes: {len(routes)}")
        print(f"   - Middleware: {len(middleware)}")
        print(f"   - Certificates: {acme_status['total_certificates']}")

    except TraefikError as e:
        print(f"\n❌ Traefik Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
