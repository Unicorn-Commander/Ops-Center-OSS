"""
Shared pytest fixtures for Cloudflare DNS management tests

This file provides common fixtures used across unit, integration, and E2E tests.
Pytest automatically discovers these fixtures.
"""
import pytest
import asyncio
import httpx
from typing import Dict, Any, List
import os
import time

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
async def admin_client(ops_center_base_url, admin_credentials):
    """Create authenticated admin HTTP client"""
    async with httpx.AsyncClient(
        base_url=ops_center_base_url,
        timeout=30.0,
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
async def moderator_client(ops_center_base_url, moderator_credentials):
    """Create authenticated moderator HTTP client"""
    async with httpx.AsyncClient(
        base_url=ops_center_base_url,
        timeout=30.0,
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
async def viewer_client(ops_center_base_url, viewer_credentials):
    """Create authenticated viewer (non-admin) HTTP client"""
    async with httpx.AsyncClient(
        base_url=ops_center_base_url,
        timeout=30.0,
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
async def unauthenticated_client(ops_center_base_url):
    """Create HTTP client without authentication"""
    async with httpx.AsyncClient(
        base_url=ops_center_base_url,
        timeout=30.0,
        follow_redirects=True
    ) as client:
        yield client


# ==================== CLOUDFLARE TEST DATA ====================

@pytest.fixture
def valid_zone_data():
    """Valid zone creation data"""
    timestamp = int(time.time())
    return {
        "domain": f"test-{timestamp}.com",
        "jump_start": True,
        "priority": "normal"
    }


@pytest.fixture
def bulk_zone_data():
    """Bulk zone creation data"""
    timestamp = int(time.time())
    return {
        "domains": [
            {"domain": f"bulk1-{timestamp}.com", "priority": "critical"},
            {"domain": f"bulk2-{timestamp}.com", "priority": "high"},
            {"domain": f"bulk3-{timestamp}.com", "priority": "normal"}
        ]
    }


@pytest.fixture
def invalid_zone_data():
    """Invalid zone data (malformed domain)"""
    return {
        "domain": "invalid..domain.com",
        "jump_start": True
    }


@pytest.fixture
def valid_a_record():
    """Valid A record data"""
    return {
        "type": "A",
        "name": "@",
        "content": "your-server-ip",
        "proxied": True,
        "ttl": 1
    }


@pytest.fixture
def valid_aaaa_record():
    """Valid AAAA record data (IPv6)"""
    return {
        "type": "AAAA",
        "name": "@",
        "content": "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        "proxied": False,
        "ttl": 3600
    }


@pytest.fixture
def valid_cname_record():
    """Valid CNAME record data"""
    return {
        "type": "CNAME",
        "name": "www",
        "content": "example.com",
        "proxied": True,
        "ttl": 1
    }


@pytest.fixture
def valid_mx_record():
    """Valid MX record data"""
    return {
        "type": "MX",
        "name": "@",
        "content": "mail.example.com",
        "priority": 10,
        "proxied": False,
        "ttl": 3600
    }


@pytest.fixture
def valid_txt_record():
    """Valid TXT record data (SPF)"""
    return {
        "type": "TXT",
        "name": "@",
        "content": "v=spf1 include:spf.protection.outlook.com -all",
        "ttl": 3600
    }


@pytest.fixture
def bulk_dns_records():
    """Bulk DNS record creation data"""
    return {
        "records": [
            {"type": "A", "name": "@", "content": "your-server-ip", "proxied": True},
            {"type": "CNAME", "name": "www", "content": "example.com", "proxied": True},
            {"type": "MX", "name": "@", "content": "mail.example.com", "priority": 10}
        ]
    }


@pytest.fixture
def email_dns_records():
    """Complete email DNS setup"""
    return {
        "records": [
            {"type": "MX", "name": "@", "content": "superiorbsolutions-com.mail.protection.outlook.com", "priority": 0},
            {"type": "TXT", "name": "@", "content": "v=spf1 include:spf.protection.outlook.com -all"},
            {"type": "TXT", "name": "_dmarc", "content": "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com"}
        ]
    }


@pytest.fixture
def invalid_dns_record():
    """Invalid DNS record (bad IP)"""
    return {
        "type": "A",
        "name": "@",
        "content": "999.999.999.999"
    }


# ==================== MOCK IDS ====================

@pytest.fixture
def mock_zone_id():
    """Mock zone ID for testing"""
    return "zone_test_12345"


@pytest.fixture
def mock_record_id():
    """Mock DNS record ID for testing"""
    return "rec_test_67890"


@pytest.fixture
def mock_queue_id():
    """Mock queue ID for testing"""
    return 1


# ==================== MOCK CLOUDFLARE RESPONSES ====================

@pytest.fixture
def mock_zone_response():
    """Mock Cloudflare zone response"""
    return {
        "zone_id": "zone_abc123",
        "domain": "unicorncommander.ai",
        "status": "active",
        "nameservers": ["vera.ns.cloudflare.com", "walt.ns.cloudflare.com"],
        "plan": "free",
        "created_at": "2025-10-22T10:00:00Z",
        "activated_at": "2025-10-22T14:30:00Z"
    }


@pytest.fixture
def mock_dns_record_response():
    """Mock Cloudflare DNS record response"""
    return {
        "id": "rec_xyz789",
        "type": "A",
        "name": "unicorncommander.ai",
        "content": "your-server-ip",
        "proxied": True,
        "ttl": 1,
        "created_at": "2025-10-22T10:00:00Z"
    }


@pytest.fixture
def mock_zone_list_response():
    """Mock zone list response"""
    return {
        "zones": [
            {
                "zone_id": "zone_1",
                "domain": "unicorncommander.ai",
                "status": "active",
                "nameservers": ["vera.ns.cloudflare.com", "walt.ns.cloudflare.com"]
            },
            {
                "zone_id": "zone_2",
                "domain": "superiorbsolutions.com",
                "status": "pending",
                "nameservers": ["ted.ns.cloudflare.com", "uma.ns.cloudflare.com"]
            },
            {
                "zone_id": "zone_3",
                "domain": "magicunicorn.tech",
                "status": "active",
                "nameservers": ["vera.ns.cloudflare.com", "walt.ns.cloudflare.com"]
            }
        ],
        "total": 3,
        "pending_count": 1,
        "active_count": 2
    }


@pytest.fixture
def mock_queue_response():
    """Mock queue status response"""
    return {
        "queue": [
            {
                "id": 1,
                "domain": "queued1.com",
                "priority": "high",
                "queue_position": 1,
                "status": "queued",
                "created_at": "2025-10-22T20:00:00Z"
            },
            {
                "id": 2,
                "domain": "queued2.com",
                "priority": "normal",
                "queue_position": 2,
                "status": "queued",
                "created_at": "2025-10-22T20:05:00Z"
            }
        ],
        "total": 2
    }


@pytest.fixture
def mock_account_limits_response():
    """Mock account limits response"""
    return {
        "plan": "free",
        "zones": {
            "total": 11,
            "active": 8,
            "pending": 3,
            "limit": 3,
            "at_limit": True
        },
        "rate_limit": {
            "requests_per_5min": 1200,
            "current_usage": 342,
            "percent_used": 28.5,
            "reset_at": "2025-10-22T20:05:00Z"
        },
        "features": {
            "page_rules": {"used": 2, "limit": 3},
            "firewall_rules": {"used": 5, "limit": 5},
            "ssl": "flexible",
            "ddos_protection": "basic"
        }
    }


@pytest.fixture
def mock_propagation_response():
    """Mock nameserver propagation response"""
    return {
        "zone_id": "zone_123",
        "status": "active",
        "status_changed": False,
        "nameserver_propagation": {
            "cloudflare_dns": True,
            "google_dns": True,
            "quad9_dns": True,
            "local_dns": False
        }
    }


# ==================== CLEANUP FIXTURES ====================

@pytest.fixture(autouse=True)
async def cleanup_test_zones(admin_client):
    """
    Automatically cleanup test zones after each test

    This fixture runs automatically and removes zones created during testing
    (identified by "test-" prefix in domain)
    """
    # BEFORE test: nothing to do
    yield

    # AFTER test: cleanup
    try:
        response = await admin_client.get("/api/v1/cloudflare/zones")

        if response.status_code == 200:
            data = response.json()
            zones = data.get("zones", [])

            # Delete all test zones
            for zone in zones:
                domain = zone.get("domain", "")
                if domain.startswith("test-") or domain.startswith("bulk"):
                    zone_id = zone.get("zone_id")
                    if zone_id:
                        await admin_client.delete(
                            f"/api/v1/cloudflare/zones/{zone_id}"
                        )

    except Exception as e:
        # Cleanup errors are non-fatal
        print(f"Warning: Cleanup error: {e}")


# ==================== HELPER FIXTURES ====================

@pytest.fixture
def assert_valid_zone_response():
    """Helper to assert valid zone response structure"""
    def _assert(data: Dict[str, Any]):
        assert "zone_id" in data
        assert "domain" in data
        assert "status" in data
        assert "nameservers" in data

        # Status must be valid
        assert data["status"] in ["pending", "active", "deactivated", "deleted"]

        # Nameservers must be list of 2
        assert isinstance(data["nameservers"], list)
        assert len(data["nameservers"]) == 2

    return _assert


@pytest.fixture
def assert_valid_dns_record():
    """Helper to assert valid DNS record structure"""
    def _assert(record: Dict[str, Any]):
        assert "id" in record or "record_id" in record
        assert "type" in record
        assert record["type"] in ["A", "AAAA", "CNAME", "MX", "TXT", "SRV", "CAA"]
        assert "name" in record
        assert "content" in record

        # MX records must have priority
        if record["type"] == "MX":
            assert "priority" in record

    return _assert


@pytest.fixture
def assert_valid_queue_entry():
    """Helper to assert valid queue entry structure"""
    def _assert(entry: Dict[str, Any]):
        assert "id" in entry
        assert "domain" in entry
        assert "priority" in entry
        assert entry["priority"] in ["critical", "high", "normal", "low"]
        assert "queue_position" in entry
        assert "status" in entry

    return _assert


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


# ==================== PYTEST MARKERS ====================

def pytest_configure(config):
    """
    Register custom pytest markers

    Usage in tests:
        @pytest.mark.cloudflare
        def test_something():
            pass
    """
    config.addinivalue_line(
        "markers", "cloudflare: marks tests as Cloudflare DNS tests"
    )
    config.addinivalue_line(
        "markers", "zone: marks tests as zone management tests"
    )
    config.addinivalue_line(
        "markers", "dns: marks tests as DNS record management tests"
    )
    config.addinivalue_line(
        "markers", "queue: marks tests as queue management tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end workflow tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (> 1 second)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


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
    print("CLOUDFLARE DNS MANAGEMENT TEST SUITE")
    print("="*60)
    print(f"Ops-Center URL: {os.getenv('OPS_CENTER_URL', 'http://localhost:8084')}")
    print(f"Test Environment: {os.getenv('ENVIRONMENT', 'test')}")
    print(f"Cloudflare API Token: {os.getenv('CLOUDFLARE_API_TOKEN', '(not set)')[:20]}...")
    print("="*60 + "\n")

    yield

    # Teardown
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60 + "\n")


# ==================== SKIP CONDITIONS ====================

@pytest.fixture
def skip_if_no_cloudflare_token():
    """Skip test if Cloudflare API token not configured"""
    token = os.getenv("CLOUDFLARE_API_TOKEN")
    if not token:
        pytest.skip("CLOUDFLARE_API_TOKEN not set")


@pytest.fixture
def skip_if_cloudflare_quota_exceeded():
    """Skip test if Cloudflare zone quota exceeded"""
    # In real implementation, would check actual quota
    # For now, always run tests
    pass


# ==================== RATE LIMIT HELPERS ====================

@pytest.fixture
def rate_limit_tracker():
    """Track API rate limit usage during tests"""
    class RateLimitTracker:
        def __init__(self):
            self.request_count = 0
            self.start_time = time.time()

        def increment(self):
            self.request_count += 1

        def get_rate(self):
            """Get requests per second"""
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                return self.request_count / elapsed
            return 0

        def is_approaching_limit(self, limit: int = 1200, window: int = 300):
            """Check if approaching 1200 req/5min limit"""
            elapsed = time.time() - self.start_time
            if elapsed < window:
                # Scale to full window
                projected = (self.request_count / elapsed) * window
                return projected > (limit * 0.8)  # 80% threshold
            return self.request_count > (limit * 0.8)

    return RateLimitTracker()
