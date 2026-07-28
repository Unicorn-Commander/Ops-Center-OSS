"""
Shared pytest fixtures for Traefik management tests

This file provides common fixtures used across both unit and integration tests.
To use these fixtures in your tests, pytest will automatically discover them.
"""
import pytest
import asyncio
import httpx
from typing import Dict, Any, AsyncGenerator
from pathlib import Path
import os
import tempfile
import yaml


# ==================== ASYNC EVENT LOOP CONFIGURATION ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ==================== BASE URL CONFIGURATION ====================

@pytest.fixture(scope="session")
def ops_center_base_url():
    """Base URL for Ops-Center API"""
    return os.getenv("OPS_CENTER_URL", "http://localhost:8084")


# ==================== TEST USER CREDENTIALS ====================

@pytest.fixture(scope="session")
def admin_credentials():
    """Admin user credentials for testing"""
    return {
        "username": os.getenv("TEST_ADMIN_USERNAME", "admin_test"),
        "password": os.getenv("TEST_ADMIN_PASSWORD", "Test123!")
    }


@pytest.fixture(scope="session")
def moderator_credentials():
    """Moderator user credentials for testing"""
    return {
        "username": os.getenv("TEST_MODERATOR_USERNAME", "moderator_test"),
        "password": os.getenv("TEST_MODERATOR_PASSWORD", "Test123!")
    }


@pytest.fixture(scope="session")
def viewer_credentials():
    """Viewer (non-admin) user credentials for testing"""
    return {
        "username": os.getenv("TEST_VIEWER_USERNAME", "user_test"),
        "password": os.getenv("TEST_VIEWER_PASSWORD", "Test123!")
    }


# ==================== HTTP CLIENTS ====================

@pytest.fixture
async def admin_client(ops_center_base_url, admin_credentials) -> AsyncGenerator:
    """Create authenticated admin HTTP client"""
    async with httpx.AsyncClient(
        base_url=ops_center_base_url,
        timeout=10.0,
        follow_redirects=True
    ) as client:
        try:
            response = await client.post(
                "/api/v1/auth/login",
                json=admin_credentials
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token") or data.get("token")

                if token:
                    client.headers["Authorization"] = f"Bearer {token}"

        except Exception as e:
            print(f"Admin login failed: {e}")

        yield client


@pytest.fixture
async def moderator_client(ops_center_base_url, moderator_credentials) -> AsyncGenerator:
    """Create authenticated moderator HTTP client"""
    async with httpx.AsyncClient(
        base_url=ops_center_base_url,
        timeout=10.0,
        follow_redirects=True
    ) as client:
        try:
            response = await client.post(
                "/api/v1/auth/login",
                json=moderator_credentials
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token") or data.get("token")

                if token:
                    client.headers["Authorization"] = f"Bearer {token}"

        except Exception as e:
            print(f"Moderator login failed: {e}")

        yield client


@pytest.fixture
async def viewer_client(ops_center_base_url, viewer_credentials) -> AsyncGenerator:
    """Create authenticated viewer (non-admin) HTTP client"""
    async with httpx.AsyncClient(
        base_url=ops_center_base_url,
        timeout=10.0,
        follow_redirects=True
    ) as client:
        try:
            response = await client.post(
                "/api/v1/auth/login",
                json=viewer_credentials
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token") or data.get("token")

                if token:
                    client.headers["Authorization"] = f"Bearer {token}"

        except Exception as e:
            print(f"Viewer login failed: {e}")

        yield client


@pytest.fixture
async def unauthenticated_client(ops_center_base_url) -> AsyncGenerator:
    """Create HTTP client without authentication"""
    async with httpx.AsyncClient(
        base_url=ops_center_base_url,
        timeout=10.0,
        follow_redirects=True
    ) as client:
        yield client


# ==================== TEST DATA - CERTIFICATES ====================

@pytest.fixture
def valid_certificate_request():
    """Valid certificate request data"""
    return {
        "domain": "test.example.com",
        "email": "admin@example.com",
        "challenge_type": "http"
    }


@pytest.fixture
def valid_wildcard_certificate_request():
    """Valid wildcard certificate request data"""
    return {
        "domain": "*.example.com",
        "email": "admin@example.com",
        "challenge_type": "dns"
    }


@pytest.fixture
def invalid_certificate_request():
    """Invalid certificate request data"""
    return {
        "domain": "invalid domain!",
        "email": "not-an-email"
    }


@pytest.fixture
def mock_certificate():
    """Mock certificate data"""
    return {
        "domain": "example.com",
        "status": "valid",
        "expiry": "2026-01-01T00:00:00Z",
        "issuer": "Let's Encrypt",
        "created_at": "2025-01-01T00:00:00Z"
    }


# ==================== TEST DATA - ROUTES ====================

@pytest.fixture
def valid_route():
    """Valid route for testing"""
    return {
        "name": "TEST:valid-route",
        "rule": "Host(`test.example.com`)",
        "service": "test-service",
        "entrypoint": "websecure"
    }


@pytest.fixture
def valid_route_with_middlewares():
    """Valid route with middlewares"""
    return {
        "name": "TEST:auth-route",
        "rule": "Host(`secure.example.com`)",
        "service": "secure-service",
        "entrypoint": "websecure",
        "middlewares": ["auth", "rate-limit"]
    }


@pytest.fixture
def valid_route_with_priority():
    """Valid route with priority"""
    return {
        "name": "TEST:priority-route",
        "rule": "PathPrefix(`/api`)",
        "service": "api-service",
        "priority": 100
    }


@pytest.fixture
def invalid_route():
    """Invalid route data"""
    return {
        "name": "TEST:invalid",
        "rule": "InvalidSyntax",
        "service": "test-service"
    }


@pytest.fixture
def complex_route_rule():
    """Complex route rule"""
    return {
        "name": "TEST:complex-route",
        "rule": "Host(`example.com`) && PathPrefix(`/api`) && Method(`GET`, `POST`)",
        "service": "api-service"
    }


@pytest.fixture
def mock_route():
    """Mock route data"""
    return {
        "name": "test-route",
        "rule": "Host(`test.example.com`)",
        "service": "test-service",
        "entrypoint": "websecure",
        "priority": 0,
        "middlewares": [],
        "created_at": "2025-01-01T00:00:00Z"
    }


# ==================== TEST DATA - MIDDLEWARES ====================

@pytest.fixture
def valid_middleware_basic_auth():
    """Valid basic auth middleware"""
    return {
        "name": "TEST:basic-auth",
        "type": "basicAuth",
        "config": {
            "users": [
                "admin:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/",  # admin:admin
                "user:$apr1$8rS96TGZ$UxhGM9H4BrV2p9P8H0G6T."   # user:password
            ]
        }
    }


@pytest.fixture
def valid_middleware_rate_limit():
    """Valid rate limit middleware"""
    return {
        "name": "TEST:rate-limiter",
        "type": "rateLimit",
        "config": {
            "average": 100,
            "burst": 50,
            "period": "1s"
        }
    }


@pytest.fixture
def valid_middleware_headers():
    """Valid headers middleware"""
    return {
        "name": "TEST:custom-headers",
        "type": "headers",
        "config": {
            "customRequestHeaders": {
                "X-Custom-Header": "value"
            },
            "customResponseHeaders": {
                "X-Response-Header": "value"
            }
        }
    }


@pytest.fixture
def valid_middleware_redirect():
    """Valid redirect middleware"""
    return {
        "name": "TEST:https-redirect",
        "type": "redirectScheme",
        "config": {
            "scheme": "https",
            "permanent": True
        }
    }


@pytest.fixture
def valid_middleware_strip_prefix():
    """Valid strip prefix middleware"""
    return {
        "name": "TEST:strip-api",
        "type": "stripPrefix",
        "config": {
            "prefixes": ["/api", "/v1"]
        }
    }


@pytest.fixture
def invalid_middleware():
    """Invalid middleware data"""
    return {
        "name": "TEST:invalid",
        "type": "invalidType",
        "config": {}
    }


# ==================== TEST DATA - CONFIGURATION ====================

@pytest.fixture
def valid_traefik_config():
    """Valid Traefik configuration"""
    return {
        "entryPoints": {
            "web": {
                "address": ":80"
            },
            "websecure": {
                "address": ":443"
            }
        },
        "certificatesResolvers": {
            "letsencrypt": {
                "acme": {
                    "email": "admin@example.com",
                    "storage": "/letsencrypt/acme.json",
                    "httpChallenge": {
                        "entryPoint": "web"
                    }
                }
            }
        }
    }


@pytest.fixture
def invalid_traefik_config():
    """Invalid Traefik configuration"""
    return {
        "invalid": "config",
        "missing": "entryPoints"
    }


@pytest.fixture
def temp_traefik_config_file():
    """Create temporary Traefik config file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        config = {
            'entryPoints': {
                'web': {'address': ':80'},
                'websecure': {'address': ':443'}
            },
            'certificatesResolvers': {
                'letsencrypt': {
                    'acme': {
                        'email': 'admin@example.com',
                        'storage': '/letsencrypt/acme.json'
                    }
                }
            }
        }
        yaml.dump(config, f)
        yield f.name
    Path(f.name).unlink()


# ==================== CLEANUP FIXTURES ====================

@pytest.fixture(autouse=True)
async def cleanup_test_traefik_resources(admin_client):
    """
    Automatically cleanup test Traefik resources after each test

    This fixture runs automatically for all tests and removes
    any resources created during testing (identified by "TEST:" prefix)
    """
    # BEFORE test: nothing to do
    yield

    # AFTER test: cleanup
    try:
        # Cleanup routes
        response = await admin_client.get("/api/v1/network/traefik/routes")

        if response.status_code == 200:
            data = response.json()
            routes = data.get("routes", [])

            # Delete all test routes
            for route in routes:
                name = route.get("name", "")
                if name and "TEST:" in name:
                    await admin_client.delete(
                        f"/api/v1/network/traefik/routes/{name}"
                    )

        # Cleanup middlewares
        response = await admin_client.get("/api/v1/network/traefik/middlewares")

        if response.status_code == 200:
            data = response.json()
            middlewares = data.get("middlewares", [])

            for middleware in middlewares:
                name = middleware.get("name", "")
                if name and "TEST:" in name:
                    await admin_client.delete(
                        f"/api/v1/network/traefik/middlewares/{name}"
                    )

    except Exception as e:
        # Cleanup errors are non-fatal
        print(f"Warning: Cleanup error: {e}")


# ==================== HELPER FIXTURES ====================

@pytest.fixture
def assert_valid_certificate():
    """Helper to assert valid certificate response"""
    def _assert(data: Dict[str, Any]):
        assert "domain" in data
        assert "status" in data
        assert "created_at" in data or "expiry" in data

    return _assert


@pytest.fixture
def assert_valid_route():
    """Helper to assert valid route structure"""
    def _assert(route: Dict[str, Any]):
        assert "name" in route
        assert "rule" in route
        assert "service" in route
        assert "entrypoint" in route

    return _assert


@pytest.fixture
def assert_valid_middleware():
    """Helper to assert valid middleware structure"""
    def _assert(middleware: Dict[str, Any]):
        assert "name" in middleware
        assert "type" in middleware
        assert "config" in middleware

    return _assert


@pytest.fixture
def assert_valid_traefik_status():
    """Helper to assert valid Traefik status response"""
    def _assert(data: Dict[str, Any]):
        assert "status" in data or "traefik" in data
        # May contain version, uptime, etc.

    return _assert


# ==================== SKIP CONDITIONS ====================

@pytest.fixture
def skip_if_traefik_not_configured():
    """Skip test if Traefik is not configured"""
    import httpx
    try:
        response = httpx.get("http://localhost:8080/api/overview", timeout=2.0)
        if response.status_code != 200:
            pytest.skip("Traefik is not configured or not running")
    except Exception:
        pytest.skip("Traefik is not accessible")


@pytest.fixture
def skip_if_no_sudo():
    """Skip test if running without sudo privileges"""
    import os
    if os.geteuid() != 0:
        pytest.skip("Test requires sudo privileges")


# ==================== PERFORMANCE MONITORING ====================

@pytest.fixture
def performance_monitor():
    """Monitor test performance"""
    import time

    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

        def assert_duration_under(self, max_seconds: float):
            assert self.duration is not None, "Timer not started/stopped"
            assert self.duration < max_seconds, \
                f"Operation took {self.duration:.3f}s (expected < {max_seconds}s)"

    return PerformanceMonitor()


# ==================== ENVIRONMENT SETUP ====================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Setup test environment before running any tests

    This runs once at the start of the test session
    """
    # Set test environment variables
    os.environ["ENVIRONMENT"] = "test"
    os.environ["LOG_LEVEL"] = "DEBUG"

    print("\n" + "="*60)
    print("TRAEFIK MANAGEMENT TEST SUITE (Epic 1.3)")
    print("="*60)
    print(f"Ops-Center URL: {os.getenv('OPS_CENTER_URL', 'http://localhost:8084')}")
    print(f"Test Environment: {os.getenv('ENVIRONMENT', 'test')}")
    print("="*60 + "\n")

    yield

    # Teardown
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60 + "\n")


# ==================== PYTEST MARKERS ====================

def pytest_configure(config):
    """
    Register custom pytest markers

    Usage in tests:
        @pytest.mark.requires_traefik
        def test_something():
            pass
    """
    config.addinivalue_line(
        "markers", "requires_traefik: marks tests as requiring Traefik to be running"
    )
    config.addinivalue_line(
        "markers", "requires_sudo: marks tests as requiring sudo permissions"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (> 1 second)"
    )
    config.addinivalue_line(
        "markers", "destructive: marks tests that modify system state"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "certificate: marks certificate-related tests"
    )
    config.addinivalue_line(
        "markers", "route: marks route-related tests"
    )
    config.addinivalue_line(
        "markers", "middleware: marks middleware-related tests"
    )
    config.addinivalue_line(
        "markers", "config: marks configuration-related tests"
    )


# ==================== MOCK DATA GENERATORS ====================

@pytest.fixture
def generate_mock_certificates():
    """Generate multiple mock certificates for testing"""
    def _generate(count: int = 5):
        from datetime import datetime, timedelta
        certificates = []

        for i in range(count):
            cert = {
                "domain": f"test{i}.example.com",
                "status": "valid",
                "expiry": (datetime.now() + timedelta(days=90)).isoformat(),
                "issuer": "Let's Encrypt",
                "created_at": datetime.now().isoformat()
            }
            certificates.append(cert)

        return certificates

    return _generate


@pytest.fixture
def generate_mock_routes():
    """Generate multiple mock routes for testing"""
    def _generate(count: int = 10):
        routes = []

        for i in range(count):
            route = {
                "name": f"test-route-{i}",
                "rule": f"Host(`test{i}.example.com`)",
                "service": f"test-service-{i}",
                "entrypoint": "websecure",
                "priority": i * 10,
                "middlewares": []
            }
            routes.append(route)

        return routes

    return _generate


@pytest.fixture
def generate_mock_middlewares():
    """Generate multiple mock middlewares for testing"""
    def _generate(count: int = 5):
        middlewares = []

        middleware_types = ["basicAuth", "rateLimit", "headers", "compress", "retry"]

        for i in range(count):
            middleware = {
                "name": f"test-middleware-{i}",
                "type": middleware_types[i % len(middleware_types)],
                "config": {}
            }
            middlewares.append(middleware)

        return middlewares

    return _generate
