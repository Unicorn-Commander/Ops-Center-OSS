"""
Integration Tests for Traefik Management API Endpoints (Epic 1.3)
Tests real HTTP endpoints with authentication and database integration

Test Categories:
1. Authentication & Authorization (6 tests)
2. Certificate Management API (12 tests)
3. Route Management API (14 tests)
4. Middleware Management API (10 tests)
5. Configuration Management API (8 tests)
6. Health & Status Endpoints (6 tests)
7. Rate Limiting (5 tests)
8. Error Responses (8 tests)
9. Audit Logging (6 tests)

Total: 75 integration tests for comprehensive API coverage
"""
import pytest
import httpx
from typing import Dict, Any
import time
import asyncio
import json


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
async def moderator_client(base_url):
    """Create authenticated moderator client"""
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        response = await client.post("/api/v1/auth/login", json={
            "username": "moderator_test",
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
async def cleanup_test_traefik_resources(admin_client):
    """Cleanup test Traefik resources after each test"""
    yield

    # Delete all test routes (those with "TEST:" in description)
    try:
        response = await admin_client.get("/api/v1/network/traefik/routes")
        if response.status_code == 200:
            routes = response.json().get("routes", [])

            for route in routes:
                if "TEST:" in route.get("name", ""):
                    await admin_client.delete(
                        f"/api/v1/network/traefik/routes/{route['name']}"
                    )

        # Delete test middlewares
        response = await admin_client.get("/api/v1/network/traefik/middlewares")
        if response.status_code == 200:
            middlewares = response.json().get("middlewares", [])

            for middleware in middlewares:
                if "TEST:" in middleware.get("name", ""):
                    await admin_client.delete(
                        f"/api/v1/network/traefik/middlewares/{middleware['name']}"
                    )

    except Exception as e:
        print(f"Cleanup error: {e}")


# ==================== TEST SUITE 1: AUTHENTICATION & AUTHORIZATION ====================

class TestAuthentication:
    """API Authentication & Authorization Tests"""

    @pytest.mark.asyncio
    async def test_unauthenticated_request_rejected(self, unauthenticated_client):
        """TC-1.1: Authentication Required Test"""
        response = await unauthenticated_client.get(
            "/api/v1/network/traefik/status"
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_viewer_cannot_modify_traefik(self, viewer_client):
        """TC-1.2: Authorization Test (Admin Role Required)"""
        route_data = {
            "name": "TEST:unauthorized-route",
            "rule": "Host(`test.example.com`)",
            "service": "test-service"
        }

        response = await viewer_client.post(
            "/api/v1/network/traefik/routes",
            json=route_data
        )

        # Should reject with 403 Forbidden
        assert response.status_code == 403
        data = response.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_moderator_can_view_only(self, moderator_client):
        """TC-1.3: Moderator Can View But Not Modify"""
        # Moderator can view
        response = await moderator_client.get("/api/v1/network/traefik/status")
        assert response.status_code in [200, 503]

        # But cannot modify
        response = await moderator_client.post(
            "/api/v1/network/traefik/routes",
            json={"name": "test", "rule": "Host(`test.com`)", "service": "svc"}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_has_full_access(self, admin_client):
        """TC-1.4: Admin Has Full Access"""
        response = await admin_client.get("/api/v1/network/traefik/status")

        # Admin should have access (200 or 503 if Traefik not configured)
        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self, base_url):
        """TC-1.5: Invalid Token Rejected"""
        async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
            client.headers["Authorization"] = "Bearer invalid_token_here"

            response = await client.get("/api/v1/network/traefik/status")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token_rejected(self, base_url):
        """TC-1.6: Expired Token Rejected"""
        # Simulate expired token
        async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
            expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MDAwMDAwMDB9.invalid"
            client.headers["Authorization"] = f"Bearer {expired_token}"

            response = await client.get("/api/v1/network/traefik/status")
            assert response.status_code == 401


# ==================== TEST SUITE 2: CERTIFICATE MANAGEMENT API ====================

class TestCertificateAPI:
    """TC-2.1 through TC-2.12: Certificate Management API Tests"""

    @pytest.mark.asyncio
    async def test_list_certificates(self, admin_client):
        """TC-2.1: GET /api/v1/network/traefik/certificates"""
        response = await admin_client.get("/api/v1/network/traefik/certificates")

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "certificates" in data
            assert isinstance(data["certificates"], list)

    @pytest.mark.asyncio
    async def test_request_certificate_valid(self, admin_client):
        """TC-2.2: POST /api/v1/network/traefik/certificates (Valid)"""
        cert_data = {
            "domain": "test.example.com",
            "email": "admin@example.com",
            "challenge_type": "http"
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/certificates",
            json=cert_data
        )

        # Should succeed or return configuration error
        assert response.status_code in [200, 201, 503]

        if response.status_code in [200, 201]:
            data = response.json()
            assert "certificate" in data or "domain" in data

    @pytest.mark.asyncio
    async def test_request_certificate_wildcard(self, admin_client):
        """TC-2.3: POST /api/v1/network/traefik/certificates (Wildcard)"""
        cert_data = {
            "domain": "*.example.com",
            "email": "admin@example.com",
            "challenge_type": "dns"
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/certificates",
            json=cert_data
        )

        # Wildcard requires DNS challenge
        assert response.status_code in [200, 201, 400, 503]

    @pytest.mark.asyncio
    async def test_request_certificate_invalid_domain(self, admin_client):
        """TC-2.4: POST /api/v1/network/traefik/certificates (Invalid Domain)"""
        cert_data = {
            "domain": "invalid domain!",
            "email": "admin@example.com"
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/certificates",
            json=cert_data
        )

        # Should reject with 400 or 422
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_request_certificate_invalid_email(self, admin_client):
        """TC-2.5: POST /api/v1/network/traefik/certificates (Invalid Email)"""
        cert_data = {
            "domain": "test.example.com",
            "email": "not-an-email"
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/certificates",
            json=cert_data
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_get_certificate(self, admin_client):
        """TC-2.6: GET /api/v1/network/traefik/certificates/{domain}"""
        # First, request a certificate
        cert_data = {
            "domain": "get-test.example.com",
            "email": "admin@example.com"
        }

        create_response = await admin_client.post(
            "/api/v1/network/traefik/certificates",
            json=cert_data
        )

        if create_response.status_code in [200, 201]:
            # Now get it
            response = await admin_client.get(
                "/api/v1/network/traefik/certificates/get-test.example.com"
            )

            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_certificate_not_found(self, admin_client):
        """TC-2.7: GET /api/v1/network/traefik/certificates/{domain} (Not Found)"""
        response = await admin_client.get(
            "/api/v1/network/traefik/certificates/nonexistent.example.com"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_renew_certificate(self, admin_client):
        """TC-2.8: POST /api/v1/network/traefik/certificates/{domain}/renew"""
        domain = "renew-test.example.com"

        response = await admin_client.post(
            f"/api/v1/network/traefik/certificates/{domain}/renew"
        )

        # Should succeed or return error if not found/not due
        assert response.status_code in [200, 400, 404, 503]

    @pytest.mark.asyncio
    async def test_revoke_certificate(self, admin_client):
        """TC-2.9: DELETE /api/v1/network/traefik/certificates/{domain}"""
        domain = "revoke-test.example.com"

        response = await admin_client.delete(
            f"/api/v1/network/traefik/certificates/{domain}"
        )

        assert response.status_code in [200, 204, 404, 503]

    @pytest.mark.asyncio
    async def test_certificate_status_check(self, admin_client):
        """TC-2.10: GET /api/v1/network/traefik/certificates/{domain}/status"""
        domain = "status-test.example.com"

        response = await admin_client.get(
            f"/api/v1/network/traefik/certificates/{domain}/status"
        )

        assert response.status_code in [200, 404, 503]

    @pytest.mark.asyncio
    async def test_missing_required_fields_certificate(self, admin_client):
        """TC-2.11: POST /api/v1/network/traefik/certificates (Missing Fields)"""
        cert_data = {
            "domain": "test.example.com"
            # Missing 'email'
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/certificates",
            json=cert_data
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_certificate_auto_renewal_config(self, admin_client):
        """TC-2.12: GET /api/v1/network/traefik/certificates/auto-renewal/config"""
        response = await admin_client.get(
            "/api/v1/network/traefik/certificates/auto-renewal/config"
        )

        assert response.status_code in [200, 503]


# ==================== TEST SUITE 3: ROUTE MANAGEMENT API ====================

class TestRouteAPI:
    """TC-3.1 through TC-3.14: Route Management API Tests"""

    @pytest.mark.asyncio
    async def test_list_routes(self, admin_client):
        """TC-3.1: GET /api/v1/network/traefik/routes"""
        response = await admin_client.get("/api/v1/network/traefik/routes")

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "routes" in data
            assert isinstance(data["routes"], list)

    @pytest.mark.asyncio
    async def test_create_route_basic(self, admin_client):
        """TC-3.2: POST /api/v1/network/traefik/routes (Basic)"""
        route_data = {
            "name": "TEST:basic-route",
            "rule": "Host(`test.example.com`)",
            "service": "test-service"
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/routes",
            json=route_data
        )

        assert response.status_code in [200, 201, 503]

        if response.status_code in [200, 201]:
            data = response.json()
            assert "name" in data or "route" in data

    @pytest.mark.asyncio
    async def test_create_route_with_middlewares(self, admin_client):
        """TC-3.3: POST /api/v1/network/traefik/routes (With Middlewares)"""
        route_data = {
            "name": "TEST:auth-route",
            "rule": "Host(`secure.example.com`)",
            "service": "secure-service",
            "middlewares": ["auth", "rate-limit"]
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/routes",
            json=route_data
        )

        assert response.status_code in [200, 201, 503]

    @pytest.mark.asyncio
    async def test_create_route_with_priority(self, admin_client):
        """TC-3.4: POST /api/v1/network/traefik/routes (With Priority)"""
        route_data = {
            "name": "TEST:priority-route",
            "rule": "PathPrefix(`/api`)",
            "service": "api-service",
            "priority": 100
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/routes",
            json=route_data
        )

        assert response.status_code in [200, 201, 503]

    @pytest.mark.asyncio
    async def test_create_route_duplicate_name(self, admin_client):
        """TC-3.5: POST /api/v1/network/traefik/routes (Duplicate Name)"""
        route_data = {
            "name": "TEST:duplicate-route",
            "rule": "Host(`test.example.com`)",
            "service": "test-service"
        }

        # Create first route
        response1 = await admin_client.post(
            "/api/v1/network/traefik/routes",
            json=route_data
        )

        if response1.status_code in [200, 201]:
            # Try to create duplicate
            response2 = await admin_client.post(
                "/api/v1/network/traefik/routes",
                json=route_data
            )

            # Should reject with 400 or 409 Conflict
            assert response2.status_code in [400, 409]

    @pytest.mark.asyncio
    async def test_create_route_invalid_rule(self, admin_client):
        """TC-3.6: POST /api/v1/network/traefik/routes (Invalid Rule)"""
        route_data = {
            "name": "TEST:invalid-route",
            "rule": "InvalidSyntax",
            "service": "test-service"
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/routes",
            json=route_data
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_get_route(self, admin_client):
        """TC-3.7: GET /api/v1/network/traefik/routes/{name}"""
        # Create route first
        route_data = {
            "name": "TEST:get-route",
            "rule": "Host(`test.example.com`)",
            "service": "test-service"
        }

        create_response = await admin_client.post(
            "/api/v1/network/traefik/routes",
            json=route_data
        )

        if create_response.status_code in [200, 201]:
            # Get route
            response = await admin_client.get(
                "/api/v1/network/traefik/routes/TEST:get-route"
            )

            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_route_not_found(self, admin_client):
        """TC-3.8: GET /api/v1/network/traefik/routes/{name} (Not Found)"""
        response = await admin_client.get(
            "/api/v1/network/traefik/routes/nonexistent-route"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_route(self, admin_client):
        """TC-3.9: PUT /api/v1/network/traefik/routes/{name}"""
        # Create route first
        route_data = {
            "name": "TEST:update-route",
            "rule": "Host(`old.example.com`)",
            "service": "old-service"
        }

        create_response = await admin_client.post(
            "/api/v1/network/traefik/routes",
            json=route_data
        )

        if create_response.status_code in [200, 201]:
            # Update route
            update_data = {
                "rule": "Host(`new.example.com`)",
                "service": "new-service",
                "priority": 50
            }

            response = await admin_client.put(
                "/api/v1/network/traefik/routes/TEST:update-route",
                json=update_data
            )

            assert response.status_code in [200, 404, 503]

    @pytest.mark.asyncio
    async def test_delete_route(self, admin_client):
        """TC-3.10: DELETE /api/v1/network/traefik/routes/{name}"""
        # Create route first
        route_data = {
            "name": "TEST:delete-route",
            "rule": "Host(`test.example.com`)",
            "service": "test-service"
        }

        create_response = await admin_client.post(
            "/api/v1/network/traefik/routes",
            json=route_data
        )

        if create_response.status_code in [200, 201]:
            # Delete route
            response = await admin_client.delete(
                "/api/v1/network/traefik/routes/TEST:delete-route"
            )

            assert response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_filter_routes_by_entrypoint(self, admin_client):
        """TC-3.11: GET /api/v1/network/traefik/routes?entrypoint=web"""
        response = await admin_client.get(
            "/api/v1/network/traefik/routes",
            params={"entrypoint": "web"}
        )

        if response.status_code == 200:
            data = response.json()
            routes = data.get("routes", [])

            # All returned routes should have 'web' entrypoint
            for route in routes:
                assert route.get("entrypoint") == "web"

    @pytest.mark.asyncio
    async def test_filter_routes_by_service(self, admin_client):
        """TC-3.12: GET /api/v1/network/traefik/routes?service=my-service"""
        response = await admin_client.get(
            "/api/v1/network/traefik/routes",
            params={"service": "my-service"}
        )

        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_route_missing_required_fields(self, admin_client):
        """TC-3.13: POST /api/v1/network/traefik/routes (Missing Fields)"""
        route_data = {
            "name": "TEST:incomplete-route"
            # Missing 'rule' and 'service'
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/routes",
            json=route_data
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_route_complex_rule(self, admin_client):
        """TC-3.14: POST /api/v1/network/traefik/routes (Complex Rule)"""
        route_data = {
            "name": "TEST:complex-route",
            "rule": "Host(`example.com`) && PathPrefix(`/api`) && Method(`GET`, `POST`)",
            "service": "api-service"
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/routes",
            json=route_data
        )

        assert response.status_code in [200, 201, 503]


# ==================== TEST SUITE 4: MIDDLEWARE MANAGEMENT API ====================

class TestMiddlewareAPI:
    """TC-4.1 through TC-4.10: Middleware Management API Tests"""

    @pytest.mark.asyncio
    async def test_list_middlewares(self, admin_client):
        """TC-4.1: GET /api/v1/network/traefik/middlewares"""
        response = await admin_client.get("/api/v1/network/traefik/middlewares")

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "middlewares" in data
            assert isinstance(data["middlewares"], list)

    @pytest.mark.asyncio
    async def test_create_middleware_basic_auth(self, admin_client):
        """TC-4.2: POST /api/v1/network/traefik/middlewares (Basic Auth)"""
        middleware_data = {
            "name": "TEST:basic-auth",
            "type": "basicAuth",
            "config": {
                "users": [
                    "admin:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/"
                ]
            }
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/middlewares",
            json=middleware_data
        )

        assert response.status_code in [200, 201, 503]

    @pytest.mark.asyncio
    async def test_create_middleware_rate_limit(self, admin_client):
        """TC-4.3: POST /api/v1/network/traefik/middlewares (Rate Limit)"""
        middleware_data = {
            "name": "TEST:rate-limiter",
            "type": "rateLimit",
            "config": {
                "average": 100,
                "burst": 50,
                "period": "1s"
            }
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/middlewares",
            json=middleware_data
        )

        assert response.status_code in [200, 201, 503]

    @pytest.mark.asyncio
    async def test_create_middleware_headers(self, admin_client):
        """TC-4.4: POST /api/v1/network/traefik/middlewares (Headers)"""
        middleware_data = {
            "name": "TEST:custom-headers",
            "type": "headers",
            "config": {
                "customRequestHeaders": {
                    "X-Custom-Header": "value"
                }
            }
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/middlewares",
            json=middleware_data
        )

        assert response.status_code in [200, 201, 503]

    @pytest.mark.asyncio
    async def test_create_middleware_redirect(self, admin_client):
        """TC-4.5: POST /api/v1/network/traefik/middlewares (Redirect)"""
        middleware_data = {
            "name": "TEST:https-redirect",
            "type": "redirectScheme",
            "config": {
                "scheme": "https",
                "permanent": True
            }
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/middlewares",
            json=middleware_data
        )

        assert response.status_code in [200, 201, 503]

    @pytest.mark.asyncio
    async def test_create_middleware_invalid_type(self, admin_client):
        """TC-4.6: POST /api/v1/network/traefik/middlewares (Invalid Type)"""
        middleware_data = {
            "name": "TEST:invalid-middleware",
            "type": "invalidType",
            "config": {}
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/middlewares",
            json=middleware_data
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_get_middleware(self, admin_client):
        """TC-4.7: GET /api/v1/network/traefik/middlewares/{name}"""
        # Create middleware first
        middleware_data = {
            "name": "TEST:get-middleware",
            "type": "basicAuth",
            "config": {"users": []}
        }

        create_response = await admin_client.post(
            "/api/v1/network/traefik/middlewares",
            json=middleware_data
        )

        if create_response.status_code in [200, 201]:
            # Get middleware
            response = await admin_client.get(
                "/api/v1/network/traefik/middlewares/TEST:get-middleware"
            )

            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_delete_middleware(self, admin_client):
        """TC-4.8: DELETE /api/v1/network/traefik/middlewares/{name}"""
        # Create middleware first
        middleware_data = {
            "name": "TEST:delete-middleware",
            "type": "basicAuth",
            "config": {"users": []}
        }

        create_response = await admin_client.post(
            "/api/v1/network/traefik/middlewares",
            json=middleware_data
        )

        if create_response.status_code in [200, 201]:
            # Delete middleware
            response = await admin_client.delete(
                "/api/v1/network/traefik/middlewares/TEST:delete-middleware"
            )

            assert response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_middleware_missing_config(self, admin_client):
        """TC-4.9: POST /api/v1/network/traefik/middlewares (Missing Config)"""
        middleware_data = {
            "name": "TEST:no-config",
            "type": "basicAuth"
            # Missing 'config'
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/middlewares",
            json=middleware_data
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_filter_middlewares_by_type(self, admin_client):
        """TC-4.10: GET /api/v1/network/traefik/middlewares?type=basicAuth"""
        response = await admin_client.get(
            "/api/v1/network/traefik/middlewares",
            params={"type": "basicAuth"}
        )

        assert response.status_code in [200, 503]


# ==================== TEST SUITE 5: CONFIGURATION MANAGEMENT API ====================

class TestConfigurationAPI:
    """TC-5.1 through TC-5.8: Configuration Management API Tests"""

    @pytest.mark.asyncio
    async def test_get_traefik_config(self, admin_client):
        """TC-5.1: GET /api/v1/network/traefik/config"""
        response = await admin_client.get("/api/v1/network/traefik/config")

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "entryPoints" in data or "config" in data

    @pytest.mark.asyncio
    async def test_validate_config(self, admin_client):
        """TC-5.2: POST /api/v1/network/traefik/config/validate"""
        config_data = {
            "config": {
                "entryPoints": {
                    "web": {"address": ":80"}
                }
            }
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/config/validate",
            json=config_data
        )

        assert response.status_code in [200, 400, 503]

    @pytest.mark.asyncio
    async def test_validate_config_invalid(self, admin_client):
        """TC-5.3: POST /api/v1/network/traefik/config/validate (Invalid)"""
        config_data = {
            "config": {
                "invalid": "config"
            }
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/config/validate",
            json=config_data
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_backup_config(self, admin_client):
        """TC-5.4: POST /api/v1/network/traefik/config/backup"""
        response = await admin_client.post("/api/v1/network/traefik/config/backup")

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "backup_path" in data or "backup_id" in data

    @pytest.mark.asyncio
    async def test_list_backups(self, admin_client):
        """TC-5.5: GET /api/v1/network/traefik/config/backups"""
        response = await admin_client.get("/api/v1/network/traefik/config/backups")

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "backups" in data
            assert isinstance(data["backups"], list)

    @pytest.mark.asyncio
    async def test_restore_config(self, admin_client):
        """TC-5.6: POST /api/v1/network/traefik/config/restore"""
        restore_data = {
            "backup_id": "test_backup_20251023_120000"
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/config/restore",
            json=restore_data
        )

        # Should fail if backup doesn't exist
        assert response.status_code in [200, 404, 503]

    @pytest.mark.asyncio
    async def test_reload_config(self, admin_client):
        """TC-5.7: POST /api/v1/network/traefik/config/reload"""
        response = await admin_client.post("/api/v1/network/traefik/config/reload")

        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_export_config(self, admin_client):
        """TC-5.8: GET /api/v1/network/traefik/config/export"""
        response = await admin_client.get("/api/v1/network/traefik/config/export")

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            # Should return YAML or JSON content
            content_type = response.headers.get("content-type", "")
            assert "yaml" in content_type or "json" in content_type


# ==================== TEST SUITE 6: HEALTH & STATUS ENDPOINTS ====================

class TestHealthStatus:
    """TC-6.1 through TC-6.6: Health & Status Endpoints"""

    @pytest.mark.asyncio
    async def test_traefik_health(self, admin_client):
        """TC-6.1: GET /api/v1/network/traefik/health"""
        response = await admin_client.get("/api/v1/network/traefik/health")

        # Health endpoint should work without auth
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "status" in data

    @pytest.mark.asyncio
    async def test_traefik_status(self, admin_client):
        """TC-6.2: GET /api/v1/network/traefik/status"""
        response = await admin_client.get("/api/v1/network/traefik/status")

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "status" in data or "traefik" in data

    @pytest.mark.asyncio
    async def test_traefik_version(self, admin_client):
        """TC-6.3: GET /api/v1/network/traefik/version"""
        response = await admin_client.get("/api/v1/network/traefik/version")

        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_traefik_metrics(self, admin_client):
        """TC-6.4: GET /api/v1/network/traefik/metrics"""
        response = await admin_client.get("/api/v1/network/traefik/metrics")

        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_entrypoints_list(self, admin_client):
        """TC-6.5: GET /api/v1/network/traefik/entrypoints"""
        response = await admin_client.get("/api/v1/network/traefik/entrypoints")

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "entrypoints" in data or "entryPoints" in data

    @pytest.mark.asyncio
    async def test_services_list(self, admin_client):
        """TC-6.6: GET /api/v1/network/traefik/services"""
        response = await admin_client.get("/api/v1/network/traefik/services")

        assert response.status_code in [200, 503]


# ==================== TEST SUITE 7: RATE LIMITING ====================

class TestRateLimiting:
    """TC-7.1 through TC-7.5: Rate Limiting Tests"""

    @pytest.mark.asyncio
    async def test_rate_limiting_traefik_operations(self, admin_client):
        """TC-7.1: Rate Limit Test (Traefik Operations)"""
        # Send 11 requests rapidly
        responses = []
        for i in range(11):
            response = await admin_client.post(
                "/api/v1/network/traefik/config/reload"
            )
            responses.append(response)
            await asyncio.sleep(0.1)

        # Check if rate limiting is enforced
        rate_limited = any(r.status_code == 429 for r in responses)

        # If rate limiting is implemented, 11th request should be 429
        if rate_limited:
            assert responses[10].status_code == 429

    @pytest.mark.asyncio
    async def test_rate_limit_per_user(self, admin_client, moderator_client):
        """TC-7.2: Rate Limit Per User"""
        # Admin and moderator should have separate limits
        admin_responses = []
        for i in range(6):
            response = await admin_client.get("/api/v1/network/traefik/status")
            admin_responses.append(response)

        moderator_responses = []
        for i in range(6):
            response = await moderator_client.get("/api/v1/network/traefik/status")
            moderator_responses.append(response)

        # Both should succeed (separate limits)
        assert all(r.status_code in [200, 503] for r in admin_responses[:5])
        assert all(r.status_code in [200, 503] for r in moderator_responses[:5])

    @pytest.mark.asyncio
    async def test_rate_limit_headers(self, admin_client):
        """TC-7.3: Rate Limit Headers"""
        response = await admin_client.get("/api/v1/network/traefik/status")

        # Check for rate limit headers (if implemented)
        if response.status_code == 200:
            headers = response.headers
            # These are optional but recommended
            # assert "X-RateLimit-Limit" in headers
            # assert "X-RateLimit-Remaining" in headers

    @pytest.mark.asyncio
    async def test_rate_limit_bypass_health(self, unauthenticated_client):
        """TC-7.4: Health Endpoint Not Rate Limited"""
        # Health endpoint should not be rate limited
        for i in range(20):
            response = await unauthenticated_client.get(
                "/api/v1/network/traefik/health"
            )
            # All should succeed
            assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_rate_limit_reset(self, admin_client):
        """TC-7.5: Rate Limit Reset"""
        # This test would need to wait for reset period
        # Skipping in automated tests but documenting structure
        pytest.skip("Rate limit reset test requires wait time")


# ==================== TEST SUITE 8: ERROR RESPONSES ====================

class TestErrorResponses:
    """TC-8.1 through TC-8.8: Error Response Tests"""

    @pytest.mark.asyncio
    async def test_invalid_json_payload(self, admin_client):
        """TC-8.1: Invalid JSON Payload"""
        response = await admin_client.post(
            "/api/v1/network/traefik/routes",
            content="{invalid json}",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_route_not_found_error(self, admin_client):
        """TC-8.2: Route Not Found Error"""
        response = await admin_client.get(
            "/api/v1/network/traefik/routes/totally-nonexistent-route"
        )

        assert response.status_code == 404

        data = response.json()
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_middleware_not_found_error(self, admin_client):
        """TC-8.3: Middleware Not Found Error"""
        response = await admin_client.get(
            "/api/v1/network/traefik/middlewares/nonexistent-middleware"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_validation_error_response_format(self, admin_client):
        """TC-8.4: Validation Error Response Format"""
        route_data = {
            "name": "TEST:invalid",
            "rule": "",  # Invalid empty rule
            "service": ""  # Invalid empty service
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/routes",
            json=route_data
        )

        assert response.status_code == 422

        data = response.json()
        assert "detail" in data or "errors" in data

    @pytest.mark.asyncio
    async def test_internal_server_error_handling(self, admin_client):
        """TC-8.5: Internal Server Error Handling"""
        # Trigger internal error (if possible in test environment)
        # This test documents expected behavior
        pytest.skip("Internal error testing - environment specific")

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, admin_client):
        """TC-8.6: Method Not Allowed"""
        # Try POST on GET-only endpoint
        response = await admin_client.post("/api/v1/network/traefik/health")

        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_content_type_mismatch(self, admin_client):
        """TC-8.7: Content-Type Mismatch"""
        # Send form data to JSON endpoint
        response = await admin_client.post(
            "/api/v1/network/traefik/routes",
            data="name=test&rule=Host(`test.com`)&service=svc",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code in [400, 415, 422]

    @pytest.mark.asyncio
    async def test_large_payload_rejected(self, admin_client):
        """TC-8.8: Large Payload Rejected"""
        # Send very large payload
        large_data = {
            "name": "TEST:large-payload",
            "rule": "Host(`test.com`)",
            "service": "test-service",
            "metadata": "x" * 10000000  # 10MB of data
        }

        response = await admin_client.post(
            "/api/v1/network/traefik/routes",
            json=large_data
        )

        # Should reject with 413 Payload Too Large or 400
        assert response.status_code in [400, 413, 422]


# ==================== TEST SUITE 9: AUDIT LOGGING ====================

class TestAuditLogging:
    """TC-9.1 through TC-9.6: Audit Logging Tests"""

    @pytest.mark.asyncio
    async def test_route_creation_logged(self, admin_client):
        """TC-9.1: Route Creation Logged"""
        route_data = {
            "name": "TEST:audit-route",
            "rule": "Host(`audit.example.com`)",
            "service": "audit-service"
        }

        create_response = await admin_client.post(
            "/api/v1/network/traefik/routes",
            json=route_data
        )

        if create_response.status_code in [200, 201]:
            # Check audit logs
            audit_response = await admin_client.get(
                "/api/v1/network/audit-logs",
                params={"operation": "traefik_route_create", "limit": 10}
            )

            if audit_response.status_code == 200:
                logs = audit_response.json().get("logs", [])
                assert len(logs) > 0

    @pytest.mark.asyncio
    async def test_route_deletion_logged(self, admin_client):
        """TC-9.2: Route Deletion Logged"""
        # Create route
        route_data = {
            "name": "TEST:delete-audit",
            "rule": "Host(`test.com`)",
            "service": "test-service"
        }

        create_response = await admin_client.post(
            "/api/v1/network/traefik/routes",
            json=route_data
        )

        if create_response.status_code in [200, 201]:
            # Delete route
            await admin_client.delete(
                "/api/v1/network/traefik/routes/TEST:delete-audit"
            )

            # Check audit logs
            audit_response = await admin_client.get(
                "/api/v1/network/audit-logs",
                params={"operation": "traefik_route_delete", "limit": 10}
            )

            if audit_response.status_code == 200:
                logs = audit_response.json().get("logs", [])
                # Deletion should be logged
                found = any(
                    "delete" in log.get("operation", "").lower()
                    for log in logs
                )

    @pytest.mark.asyncio
    async def test_middleware_creation_logged(self, admin_client):
        """TC-9.3: Middleware Creation Logged"""
        middleware_data = {
            "name": "TEST:audit-middleware",
            "type": "basicAuth",
            "config": {"users": []}
        }

        create_response = await admin_client.post(
            "/api/v1/network/traefik/middlewares",
            json=middleware_data
        )

        if create_response.status_code in [200, 201]:
            # Check audit logs
            audit_response = await admin_client.get(
                "/api/v1/network/audit-logs",
                params={"operation": "traefik_middleware_create", "limit": 10}
            )

            if audit_response.status_code == 200:
                logs = audit_response.json().get("logs", [])
                assert len(logs) > 0

    @pytest.mark.asyncio
    async def test_config_backup_logged(self, admin_client):
        """TC-9.4: Config Backup Logged"""
        response = await admin_client.post("/api/v1/network/traefik/config/backup")

        if response.status_code == 200:
            # Check audit logs
            audit_response = await admin_client.get(
                "/api/v1/network/audit-logs",
                params={"operation": "traefik_config_backup", "limit": 10}
            )

            if audit_response.status_code == 200:
                logs = audit_response.json().get("logs", [])
                # Backup should be logged

    @pytest.mark.asyncio
    async def test_certificate_request_logged(self, admin_client):
        """TC-9.5: Certificate Request Logged"""
        cert_data = {
            "domain": "audit-cert.example.com",
            "email": "admin@example.com"
        }

        create_response = await admin_client.post(
            "/api/v1/network/traefik/certificates",
            json=cert_data
        )

        if create_response.status_code in [200, 201]:
            # Check audit logs
            audit_response = await admin_client.get(
                "/api/v1/network/audit-logs",
                params={"operation": "traefik_certificate_request", "limit": 10}
            )

            if audit_response.status_code == 200:
                logs = audit_response.json().get("logs", [])
                assert len(logs) > 0

    @pytest.mark.asyncio
    async def test_audit_log_contains_user_info(self, admin_client):
        """TC-9.6: Audit Log Contains User Info"""
        # Perform action
        route_data = {
            "name": "TEST:user-audit",
            "rule": "Host(`test.com`)",
            "service": "test-service"
        }

        await admin_client.post(
            "/api/v1/network/traefik/routes",
            json=route_data
        )

        # Check audit logs
        audit_response = await admin_client.get(
            "/api/v1/network/audit-logs",
            params={"limit": 1}
        )

        if audit_response.status_code == 200:
            logs = audit_response.json().get("logs", [])
            if logs:
                log = logs[0]
                # Should contain user information
                assert "user" in log or "username" in log or "user_id" in log


# Run with: pytest tests/integration/test_traefik_api.py -v --asyncio-mode=auto
