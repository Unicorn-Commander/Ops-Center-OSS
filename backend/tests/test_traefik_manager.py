"""
Comprehensive Unit Tests for TraefikManager

Tests all TraefikManager methods with mocked file I/O, Docker commands,
and validates business logic, error handling, and edge cases.

Author: Testing & QA Specialist Agent
Date: October 24, 2025
Epic: 1.3 - Traefik Configuration Management
"""

import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime, timedelta
import subprocess

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from traefik_manager import (
    TraefikManager,
    TraefikError,
    ConfigValidationError,
    CertificateError,
    RouteError,
    MiddlewareError,
    BackupError,
    RateLimitExceeded,
    CertificateStatus,
    MiddlewareType,
    RouteCreate,
    MiddlewareCreate,
    CertificateRequest,
    AuditLogger,
    RateLimiter,
    ConfigValidator
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_traefik_dir(tmp_path):
    """Create temporary Traefik directory structure"""
    traefik_dir = tmp_path / "traefik"
    traefik_dir.mkdir()

    # Create subdirectories
    (traefik_dir / "dynamic").mkdir()
    (traefik_dir / "backups").mkdir()
    (traefik_dir / "acme").mkdir()

    # Create dummy traefik.yml
    config = {
        'entryPoints': {
            'web': {'address': ':80'},
            'websecure': {'address': ':443'}
        },
        'providers': {'file': {'directory': str(traefik_dir / 'dynamic')}}
    }

    with open(traefik_dir / "traefik.yml", 'w') as f:
        yaml.dump(config, f)

    # Create dummy acme.json
    acme_data = {
        'letsencrypt': {
            'Email': 'test@example.com',
            'CAServer': 'https://acme-v02.api.letsencrypt.org/directory',
            'Certificates': [
                {
                    'domain': {
                        'main': 'example.com',
                        'sans': ['www.example.com']
                    },
                    'certificate': 'base64encodedcert',
                    'key': 'base64encodedkey',
                    'notAfter': (datetime.utcnow() + timedelta(days=60)).isoformat() + 'Z'
                }
            ]
        }
    }

    with open(traefik_dir / "acme" / "acme.json", 'w') as f:
        json.dump(acme_data, f)

    return traefik_dir


@pytest.fixture
def traefik_manager(temp_traefik_dir):
    """Create TraefikManager instance with temp directory"""
    return TraefikManager(
        traefik_dir=str(temp_traefik_dir),
        docker_container="test-traefik"
    )


@pytest.fixture
def mock_audit_logger():
    """Mock audit logger"""
    logger = Mock(spec=AuditLogger)
    logger.log_change = Mock()
    return logger


@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter"""
    limiter = Mock(spec=RateLimiter)
    limiter.check_limit = Mock(return_value=(True, 4))
    return limiter


@pytest.fixture
def sample_route_config():
    """Sample route configuration"""
    return {
        'http': {
            'routers': {
                'test-route': {
                    'rule': 'Host(`example.com`)',
                    'service': 'test-service',
                    'entryPoints': ['websecure'],
                    'tls': {'certResolver': 'letsencrypt'}
                }
            },
            'services': {
                'test-service': {
                    'loadBalancer': {
                        'servers': [{'url': 'http://backend:8080'}]
                    }
                }
            }
        }
    }


# ============================================================================
# Certificate Management Tests
# ============================================================================

class TestCertificateManagement:
    """Tests for SSL certificate management"""

    def test_list_certificates_success(self, traefik_manager):
        """Test listing certificates successfully"""
        certificates = traefik_manager.list_certificates()

        assert isinstance(certificates, list)
        assert len(certificates) == 1
        assert certificates[0]['domain'] == 'example.com'
        assert 'www.example.com' in certificates[0]['sans']
        assert certificates[0]['status'] == CertificateStatus.ACTIVE

    def test_list_certificates_no_acme_file(self, traefik_manager):
        """Test listing certificates when acme.json doesn't exist"""
        traefik_manager.acme_file.unlink()

        certificates = traefik_manager.list_certificates()
        assert certificates == []

    def test_list_certificates_malformed_json(self, traefik_manager):
        """Test handling of malformed acme.json"""
        with open(traefik_manager.acme_file, 'w') as f:
            f.write("invalid json{")

        with pytest.raises(CertificateError, match="Failed to list certificates"):
            traefik_manager.list_certificates()

    def test_get_certificate_info_success(self, traefik_manager):
        """Test getting certificate info for existing domain"""
        cert_info = traefik_manager.get_certificate_info('example.com')

        assert cert_info['domain'] == 'example.com'
        assert cert_info['resolver'] == 'letsencrypt'
        assert cert_info['private_key_present'] is True

    def test_get_certificate_info_not_found(self, traefik_manager):
        """Test getting certificate info for non-existent domain"""
        with pytest.raises(CertificateError, match="Certificate not found"):
            traefik_manager.get_certificate_info('nonexistent.com')

    @patch('traefik_manager.TraefikManager.reload_traefik')
    def test_request_certificate_success(self, mock_reload, traefik_manager):
        """Test requesting a new certificate"""
        mock_reload.return_value = {'success': True}

        result = traefik_manager.request_certificate(
            domain='newdomain.com',
            email='admin@newdomain.com',
            sans=['www.newdomain.com'],
            username='testadmin'
        )

        assert result['success'] is True
        assert result['domain'] == 'newdomain.com'
        assert result['status'] == 'pending'
        assert 'newdomain.com' in result['note']

    def test_request_certificate_invalid_domain(self, traefik_manager):
        """Test requesting certificate with invalid domain"""
        with pytest.raises(CertificateError, match="Invalid certificate request"):
            traefik_manager.request_certificate(
                domain='invalid_domain!',
                email='test@example.com',
                username='testadmin'
            )

    def test_request_certificate_invalid_email(self, traefik_manager):
        """Test requesting certificate with invalid email"""
        with pytest.raises(CertificateError, match="Invalid certificate request"):
            traefik_manager.request_certificate(
                domain='example.com',
                email='not-an-email',
                username='testadmin'
            )

    def test_revoke_certificate_success(self, traefik_manager):
        """Test revoking an existing certificate"""
        result = traefik_manager.revoke_certificate('example.com', username='testadmin')

        assert result['success'] is True
        assert result['domain'] == 'example.com'

        # Verify certificate was removed
        certificates = traefik_manager.list_certificates()
        domains = [c['domain'] for c in certificates]
        assert 'example.com' not in domains

    def test_revoke_certificate_not_found(self, traefik_manager):
        """Test revoking non-existent certificate"""
        with pytest.raises(CertificateError, match="Certificate not found"):
            traefik_manager.revoke_certificate('nonexistent.com', username='testadmin')

    def test_get_acme_status(self, traefik_manager):
        """Test getting ACME status"""
        status = traefik_manager.get_acme_status()

        assert status['initialized'] is True
        assert status['total_certificates'] == 1
        assert len(status['resolvers']) == 1
        assert status['resolvers'][0]['name'] == 'letsencrypt'

    def test_certificate_status_expired(self, traefik_manager):
        """Test certificate status detection for expired cert"""
        # Modify acme.json to have expired certificate
        acme_data = {
            'letsencrypt': {
                'Certificates': [
                    {
                        'domain': {'main': 'expired.com'},
                        'notAfter': '2020-01-01T00:00:00Z'
                    }
                ]
            }
        }

        with open(traefik_manager.acme_file, 'w') as f:
            json.dump(acme_data, f)

        certificates = traefik_manager.list_certificates()
        assert certificates[0]['status'] == CertificateStatus.EXPIRED


# ============================================================================
# Route Management Tests
# ============================================================================

class TestRouteManagement:
    """Tests for route management"""

    def test_list_routes_empty(self, traefik_manager):
        """Test listing routes when no routes exist"""
        routes = traefik_manager.list_routes()
        assert routes == []

    def test_list_routes_with_data(self, traefik_manager, sample_route_config):
        """Test listing routes with existing routes"""
        routes_file = traefik_manager.dynamic_dir / "routes.yml"

        with open(routes_file, 'w') as f:
            yaml.dump(sample_route_config, f)

        routes = traefik_manager.list_routes()

        assert len(routes) == 1
        assert routes[0]['name'] == 'test-route'
        assert routes[0]['rule'] == 'Host(`example.com`)'
        assert routes[0]['service'] == 'test-service'

    @patch('traefik_manager.TraefikManager.reload_traefik')
    def test_create_route_success(self, mock_reload, traefik_manager):
        """Test creating a new route"""
        mock_reload.return_value = {'success': True}

        result = traefik_manager.create_route(
            name='new-route',
            rule='Host(`newdomain.com`)',
            service='new-service',
            username='testadmin'
        )

        assert result['success'] is True
        assert result['route']['name'] == 'new-route'

        # Verify route was created
        routes = traefik_manager.list_routes()
        assert len(routes) == 1
        assert routes[0]['name'] == 'new-route'

    def test_create_route_duplicate(self, traefik_manager):
        """Test creating route with duplicate name"""
        # Create first route
        traefik_manager.create_route(
            name='test-route',
            rule='Host(`example.com`)',
            service='test-service',
            username='testadmin'
        )

        # Try to create duplicate
        with pytest.raises(RouteError, match="already exists"):
            traefik_manager.create_route(
                name='test-route',
                rule='Host(`example2.com`)',
                service='test-service',
                username='testadmin'
            )

    def test_create_route_invalid_name(self, traefik_manager):
        """Test creating route with invalid name"""
        with pytest.raises(RouteError, match="Invalid route parameters"):
            traefik_manager.create_route(
                name='invalid name with spaces',
                rule='Host(`example.com`)',
                service='test-service',
                username='testadmin'
            )

    def test_create_route_invalid_rule(self, traefik_manager):
        """Test creating route with invalid rule"""
        with pytest.raises(RouteError, match="Invalid route parameters"):
            traefik_manager.create_route(
                name='test-route',
                rule='invalid rule',  # Missing Host(), Path(), etc.
                service='test-service',
                username='testadmin'
            )

    @patch('traefik_manager.TraefikManager.reload_traefik')
    def test_update_route_success(self, mock_reload, traefik_manager, sample_route_config):
        """Test updating an existing route"""
        mock_reload.return_value = {'success': True}

        # Create initial route
        routes_file = traefik_manager.dynamic_dir / "routes.yml"
        with open(routes_file, 'w') as f:
            yaml.dump(sample_route_config, f)

        # Update route
        result = traefik_manager.update_route(
            name='test-route',
            updates={'rule': 'Host(`updated.com`)'},
            username='testadmin'
        )

        assert result['success'] is True
        assert result['route']['rule'] == 'Host(`updated.com`)'

    def test_update_route_not_found(self, traefik_manager):
        """Test updating non-existent route"""
        with pytest.raises(RouteError, match="not found"):
            traefik_manager.update_route(
                name='nonexistent',
                updates={'rule': 'Host(`example.com`)'},
                username='testadmin'
            )

    @patch('traefik_manager.TraefikManager.reload_traefik')
    def test_delete_route_success(self, mock_reload, traefik_manager, sample_route_config):
        """Test deleting a route"""
        mock_reload.return_value = {'success': True}

        # Create initial route
        routes_file = traefik_manager.dynamic_dir / "routes.yml"
        with open(routes_file, 'w') as f:
            yaml.dump(sample_route_config, f)

        # Delete route
        result = traefik_manager.delete_route('test-route', username='testadmin')

        assert result['success'] is True

        # Verify route was deleted
        routes = traefik_manager.list_routes()
        assert len(routes) == 0

    def test_delete_route_not_found(self, traefik_manager):
        """Test deleting non-existent route"""
        with pytest.raises(RouteError, match="not found"):
            traefik_manager.delete_route('nonexistent', username='testadmin')

    def test_get_route_success(self, traefik_manager, sample_route_config):
        """Test getting a specific route"""
        routes_file = traefik_manager.dynamic_dir / "routes.yml"
        with open(routes_file, 'w') as f:
            yaml.dump(sample_route_config, f)

        route = traefik_manager.get_route('test-route')

        assert route is not None
        assert route['name'] == 'test-route'

    def test_get_route_not_found(self, traefik_manager):
        """Test getting non-existent route"""
        route = traefik_manager.get_route('nonexistent')
        assert route is None


# ============================================================================
# Middleware Management Tests
# ============================================================================

class TestMiddlewareManagement:
    """Tests for middleware management"""

    def test_list_middleware_empty(self, traefik_manager):
        """Test listing middleware when none exist"""
        middleware = traefik_manager.list_middleware()
        assert middleware == []

    @patch('traefik_manager.TraefikManager.reload_traefik')
    def test_create_middleware_ratelimit(self, mock_reload, traefik_manager):
        """Test creating rate limit middleware"""
        mock_reload.return_value = {'success': True}

        result = traefik_manager.create_middleware(
            name='api-ratelimit',
            type='rateLimit',
            config={'average': 100, 'period': '1s'},
            username='testadmin'
        )

        assert result['success'] is True
        assert result['middleware']['name'] == 'api-ratelimit'

        # Verify middleware was created
        middleware = traefik_manager.list_middleware()
        assert len(middleware) == 1

    @patch('traefik_manager.TraefikManager.reload_traefik')
    def test_create_middleware_headers(self, mock_reload, traefik_manager):
        """Test creating headers middleware"""
        mock_reload.return_value = {'success': True}

        result = traefik_manager.create_middleware(
            name='security-headers',
            type='headers',
            config={'customRequestHeaders': {'X-Custom': 'value'}},
            username='testadmin'
        )

        assert result['success'] is True

    def test_create_middleware_invalid_ratelimit_config(self, traefik_manager):
        """Test creating rate limit middleware with invalid config"""
        with pytest.raises(MiddlewareError, match="Invalid middleware parameters"):
            traefik_manager.create_middleware(
                name='bad-ratelimit',
                type='rateLimit',
                config={},  # Missing required fields
                username='testadmin'
            )

    def test_create_middleware_invalid_ipwhitelist(self, traefik_manager):
        """Test creating IP whitelist with invalid IP range"""
        with pytest.raises(MiddlewareError, match="Invalid middleware parameters"):
            traefik_manager.create_middleware(
                name='ip-whitelist',
                type='ipWhiteList',
                config={'sourceRange': ['invalid-ip']},
                username='testadmin'
            )

    @patch('traefik_manager.TraefikManager.reload_traefik')
    def test_update_middleware(self, mock_reload, traefik_manager):
        """Test updating middleware configuration"""
        mock_reload.return_value = {'success': True}

        # Create middleware first
        traefik_manager.create_middleware(
            name='api-ratelimit',
            type='rateLimit',
            config={'average': 100, 'period': '1s'},
            username='testadmin'
        )

        # Update it
        result = traefik_manager.update_middleware(
            name='api-ratelimit',
            config={'average': 200, 'period': '1s'},
            username='testadmin'
        )

        assert result['success'] is True

    @patch('traefik_manager.TraefikManager.reload_traefik')
    def test_delete_middleware(self, mock_reload, traefik_manager):
        """Test deleting middleware"""
        mock_reload.return_value = {'success': True}

        # Create middleware first
        traefik_manager.create_middleware(
            name='api-ratelimit',
            type='rateLimit',
            config={'average': 100, 'period': '1s'},
            username='testadmin'
        )

        # Delete it
        result = traefik_manager.delete_middleware('api-ratelimit', username='testadmin')

        assert result['success'] is True

        # Verify deletion
        middleware = traefik_manager.list_middleware()
        assert len(middleware) == 0


# ============================================================================
# Configuration Management Tests
# ============================================================================

class TestConfigurationManagement:
    """Tests for configuration management"""

    def test_get_config_success(self, traefik_manager):
        """Test reading configuration"""
        config = traefik_manager.get_config()

        assert 'entryPoints' in config
        assert 'providers' in config

    def test_get_config_missing_file(self, traefik_manager):
        """Test reading config when file doesn't exist"""
        traefik_manager.config_file.unlink()

        with pytest.raises(ConfigValidationError, match="not found"):
            traefik_manager.get_config()

    @patch('traefik_manager.TraefikManager.reload_traefik')
    def test_update_config(self, mock_reload, traefik_manager):
        """Test updating configuration"""
        mock_reload.return_value = {'success': True}

        result = traefik_manager.update_config(
            updates={'log': {'level': 'DEBUG'}},
            username='testadmin'
        )

        assert result['success'] is True

        # Verify update
        config = traefik_manager.get_config()
        assert config['log']['level'] == 'DEBUG'

    def test_validate_config_success(self, traefik_manager):
        """Test validating valid configuration"""
        assert traefik_manager.validate_config() is True

    def test_validate_config_invalid_yaml(self, traefik_manager):
        """Test validating invalid YAML"""
        invalid_config = "invalid: yaml: structure:"

        with pytest.raises(ConfigValidationError):
            traefik_manager.validator.validate_yaml(invalid_config)

    def test_backup_config(self, traefik_manager):
        """Test configuration backup"""
        backup_path = traefik_manager.backup_config()

        assert Path(backup_path).exists()
        assert (Path(backup_path) / "traefik.yml").exists()
        assert (Path(backup_path) / "manifest.json").exists()

    @patch('traefik_manager.TraefikManager.reload_traefik')
    def test_restore_config(self, mock_reload, traefik_manager):
        """Test configuration restoration"""
        mock_reload.return_value = {'success': True}

        # Create backup
        backup_path = traefik_manager.backup_config()

        # Modify config
        traefik_manager.update_config(
            updates={'log': {'level': 'ERROR'}},
            username='testadmin'
        )

        # Restore from backup
        result = traefik_manager.restore_config(backup_path, username='testadmin')

        assert result['success'] is True

    def test_restore_config_not_found(self, traefik_manager):
        """Test restoring from non-existent backup"""
        with pytest.raises(BackupError, match="Backup not found"):
            traefik_manager.restore_config('/nonexistent/backup', username='testadmin')


# ============================================================================
# Rate Limiting Tests
# ============================================================================

class TestRateLimiting:
    """Tests for rate limiting"""

    def test_rate_limiter_allows_under_limit(self):
        """Test rate limiter allows requests under limit"""
        limiter = RateLimiter(max_changes=3, window_seconds=60)

        # Should allow first 3 requests
        assert limiter.check_limit('testuser') == (True, 2)
        assert limiter.check_limit('testuser') == (True, 1)
        assert limiter.check_limit('testuser') == (True, 0)

    def test_rate_limiter_blocks_over_limit(self):
        """Test rate limiter blocks when limit exceeded"""
        limiter = RateLimiter(max_changes=2, window_seconds=60)

        limiter.check_limit('testuser')
        limiter.check_limit('testuser')

        # Third request should be blocked
        with pytest.raises(RateLimitExceeded):
            limiter.check_limit('testuser')

    def test_rate_limiter_per_user(self):
        """Test rate limiter tracks per user"""
        limiter = RateLimiter(max_changes=2, window_seconds=60)

        limiter.check_limit('user1')
        limiter.check_limit('user1')

        # user2 should have separate limit
        assert limiter.check_limit('user2') == (True, 1)


# ============================================================================
# Validation Tests
# ============================================================================

class TestValidation:
    """Tests for input validation"""

    def test_route_create_validation_success(self):
        """Test valid route creation model"""
        route = RouteCreate(
            name='test-route',
            rule='Host(`example.com`)',
            service='test-service'
        )

        assert route.name == 'test-route'

    def test_route_create_invalid_name(self):
        """Test route creation with invalid name"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RouteCreate(
                name='invalid name',  # Spaces not allowed
                rule='Host(`example.com`)',
                service='test'
            )

    def test_route_create_invalid_rule(self):
        """Test route creation with invalid rule"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RouteCreate(
                name='test',
                rule='invalid',  # Must contain Host(), Path(), etc.
                service='test'
            )

    def test_middleware_create_validation(self):
        """Test valid middleware creation"""
        mw = MiddlewareCreate(
            name='test-middleware',
            type=MiddlewareType.RATE_LIMIT,
            config={'average': 100, 'period': '1s'}
        )

        assert mw.name == 'test-middleware'

    def test_certificate_request_validation(self):
        """Test valid certificate request"""
        cert = CertificateRequest(
            domain='example.com',
            email='admin@example.com',
            sans=['www.example.com']
        )

        assert cert.domain == 'example.com'

    def test_certificate_request_invalid_domain(self):
        """Test certificate request with invalid domain"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CertificateRequest(
                domain='invalid_domain!',
                email='admin@example.com'
            )


# ============================================================================
# Audit Logging Tests
# ============================================================================

class TestAuditLogging:
    """Tests for audit logging"""

    def test_audit_logger_logs_change(self, tmp_path):
        """Test audit logger records changes"""
        log_file = tmp_path / "audit.log"
        logger = AuditLogger(log_file=str(log_file))

        logger.log_change(
            action='create_route',
            details={'route': 'test'},
            username='testadmin',
            success=True
        )

        assert log_file.exists()

        with open(log_file) as f:
            lines = f.readlines()
            assert len(lines) == 1

            log_entry = json.loads(lines[0])
            assert log_entry['action'] == 'create_route'
            assert log_entry['user'] == 'testadmin'
            assert log_entry['success'] is True


# ============================================================================
# Edge Cases & Error Handling Tests
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_reload_traefik_container_not_found(self, traefik_manager):
        """Test reload when Docker container doesn't exist"""
        traefik_manager.docker_container = 'nonexistent-container'

        result = traefik_manager.reload_traefik()

        # Should not fail but return graceful message
        assert result['success'] is True
        assert 'auto-reload' in result['message']

    @patch('subprocess.run')
    def test_reload_traefik_timeout(self, mock_run, traefik_manager):
        """Test reload with subprocess timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired('cmd', 10)

        with pytest.raises(TraefikError, match="timed out"):
            traefik_manager.reload_traefik()

    def test_concurrent_backups(self, traefik_manager):
        """Test multiple backups don't conflict"""
        backup1 = traefik_manager.backup_config()
        backup2 = traefik_manager.backup_config()

        assert backup1 != backup2
        assert Path(backup1).exists()
        assert Path(backup2).exists()

    def test_backup_cleanup(self, traefik_manager):
        """Test old backups are cleaned up"""
        # Create 15 backups
        for i in range(15):
            traefik_manager.backup_config()

        # Check only 10 remain (default keep limit)
        backups = list(traefik_manager.backup_dir.iterdir())
        assert len(backups) <= 10


# ============================================================================
# Integration Tests (with mocked external dependencies)
# ============================================================================

class TestIntegration:
    """Integration tests with mocked external dependencies"""

    @patch('traefik_manager.TraefikManager.reload_traefik')
    def test_complete_route_workflow(self, mock_reload, traefik_manager):
        """Test complete route lifecycle"""
        mock_reload.return_value = {'success': True}

        # Create route
        traefik_manager.create_route(
            name='test-route',
            rule='Host(`example.com`)',
            service='test-service',
            username='testadmin'
        )

        # List routes
        routes = traefik_manager.list_routes()
        assert len(routes) == 1

        # Get specific route
        route = traefik_manager.get_route('test-route')
        assert route is not None

        # Update route
        traefik_manager.update_route(
            name='test-route',
            updates={'rule': 'Host(`updated.com`)'},
            username='testadmin'
        )

        # Verify update
        route = traefik_manager.get_route('test-route')
        assert route['rule'] == 'Host(`updated.com`)'

        # Delete route
        traefik_manager.delete_route('test-route', username='testadmin')

        # Verify deletion
        routes = traefik_manager.list_routes()
        assert len(routes) == 0

    @patch('traefik_manager.TraefikManager.reload_traefik')
    def test_rollback_on_failure(self, mock_reload, traefik_manager):
        """Test automatic rollback on configuration error"""
        mock_reload.return_value = {'success': True}

        # Create valid route
        traefik_manager.create_route(
            name='valid-route',
            rule='Host(`example.com`)',
            service='test-service',
            username='testadmin'
        )

        # Try to create invalid route (should trigger rollback)
        with pytest.raises(RouteError):
            with patch.object(traefik_manager.validator, 'validate_traefik_config') as mock_validate:
                mock_validate.side_effect = ConfigValidationError("Invalid config")

                traefik_manager.create_route(
                    name='invalid-route',
                    rule='Host(`invalid.com`)',
                    service='bad-service',
                    username='testadmin'
                )

        # Verify only valid route remains
        routes = traefik_manager.list_routes()
        assert len(routes) == 1
        assert routes[0]['name'] == 'valid-route'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
