"""
Test suite for CSRF protection implementation
Run with: python test_csrf.py
"""

import asyncio
import secrets
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
from csrf_protection import create_csrf_protection, get_csrf_token
import pytest


def create_test_app(csrf_enabled=True):
    """Create a test FastAPI app with CSRF protection"""
    app = FastAPI()
    sessions = {}

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*", "X-CSRF-Token"],
    )

    # CSRF Protection
    csrf_protect, csrf_middleware = create_csrf_protection(
        enabled=csrf_enabled,
        secret_key="test-secret-key",
        exempt_urls={"/auth/login", "/exempt"},
        sessions_store=sessions,
        cookie_secure=False
    )
    app.add_middleware(csrf_middleware)

    # Test endpoints
    @app.post("/auth/login")
    async def login():
        """Simulated login endpoint (exempt from CSRF)"""
        session_token = secrets.token_urlsafe(32)
        sessions[session_token] = {
            "user": {"id": 1, "username": "testuser"}
        }
        return {
            "message": "Login successful",
            "session_token": session_token
        }

    @app.get("/api/v1/auth/csrf-token")
    async def get_csrf_token_endpoint(request: Request):
        """Get CSRF token"""
        csrf_token = get_csrf_token(request, sessions)
        if not csrf_token:
            return {"error": "No session"}, 401
        return {
            "csrf_token": csrf_token,
            "header_name": "X-CSRF-Token"
        }

    @app.get("/api/data")
    async def get_data():
        """GET endpoint (safe method, no CSRF required)"""
        return {"data": "test data"}

    @app.post("/api/data")
    async def create_data(request: Request):
        """POST endpoint (requires CSRF)"""
        return {"message": "Data created"}

    @app.put("/api/data")
    async def update_data():
        """PUT endpoint (requires CSRF)"""
        return {"message": "Data updated"}

    @app.delete("/api/data")
    async def delete_data():
        """DELETE endpoint (requires CSRF)"""
        return {"message": "Data deleted"}

    @app.post("/exempt")
    async def exempt_endpoint():
        """Exempt endpoint"""
        return {"message": "Exempt endpoint"}

    return app, sessions


class TestCSRFProtection:
    """Test cases for CSRF protection"""

    def setup_method(self):
        """Setup for each test"""
        self.app, self.sessions = create_test_app(csrf_enabled=True)
        self.client = TestClient(self.app)

    def test_get_request_no_csrf_required(self):
        """GET requests should work without CSRF token"""
        response = self.client.get("/api/data")
        assert response.status_code == 200
        assert response.json() == {"data": "test data"}

    def test_exempt_endpoint_no_csrf_required(self):
        """Exempt endpoints should work without CSRF token"""
        response = self.client.post("/exempt")
        assert response.status_code == 200
        assert response.json() == {"message": "Exempt endpoint"}

    def test_login_endpoint_exempt(self):
        """Login endpoint should work without CSRF token"""
        response = self.client.post("/auth/login")
        assert response.status_code == 200
        assert "session_token" in response.json()

    def test_post_without_csrf_fails(self):
        """POST request without CSRF token should fail"""
        # Login first
        login_response = self.client.post("/auth/login")
        session_token = login_response.json()["session_token"]

        # Try POST without CSRF token
        response = self.client.post(
            "/api/data",
            cookies={"session_token": session_token}
        )
        assert response.status_code == 403
        assert "CSRF validation failed" in response.json()["detail"]

    def test_post_with_csrf_succeeds(self):
        """POST request with valid CSRF token should succeed"""
        # Login
        login_response = self.client.post("/auth/login")
        session_token = login_response.json()["session_token"]

        # Get CSRF token (this also generates it in session)
        self.client.get("/api/data", cookies={"session_token": session_token})

        # Get the CSRF token from session
        csrf_token = self.sessions[session_token].get("csrf_token")

        # POST with CSRF token
        response = self.client.post(
            "/api/data",
            headers={"X-CSRF-Token": csrf_token},
            cookies={"session_token": session_token}
        )
        assert response.status_code == 200
        assert response.json() == {"message": "Data created"}

    def test_put_with_csrf_succeeds(self):
        """PUT request with valid CSRF token should succeed"""
        # Login
        login_response = self.client.post("/auth/login")
        session_token = login_response.json()["session_token"]

        # Generate CSRF token
        self.client.get("/api/data", cookies={"session_token": session_token})
        csrf_token = self.sessions[session_token].get("csrf_token")

        # PUT with CSRF token
        response = self.client.put(
            "/api/data",
            headers={"X-CSRF-Token": csrf_token},
            cookies={"session_token": session_token}
        )
        assert response.status_code == 200
        assert response.json() == {"message": "Data updated"}

    def test_delete_with_csrf_succeeds(self):
        """DELETE request with valid CSRF token should succeed"""
        # Login
        login_response = self.client.post("/auth/login")
        session_token = login_response.json()["session_token"]

        # Generate CSRF token
        self.client.get("/api/data", cookies={"session_token": session_token})
        csrf_token = self.sessions[session_token].get("csrf_token")

        # DELETE with CSRF token
        response = self.client.delete(
            "/api/data",
            headers={"X-CSRF-Token": csrf_token},
            cookies={"session_token": session_token}
        )
        assert response.status_code == 200
        assert response.json() == {"message": "Data deleted"}

    def test_csrf_token_endpoint(self):
        """CSRF token endpoint should return valid token"""
        # Login
        login_response = self.client.post("/auth/login")
        session_token = login_response.json()["session_token"]

        # Generate CSRF token
        self.client.get("/api/data", cookies={"session_token": session_token})

        # Get CSRF token via endpoint
        response = self.client.get(
            "/api/v1/auth/csrf-token",
            cookies={"session_token": session_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "csrf_token" in data
        assert data["header_name"] == "X-CSRF-Token"

        # Verify it's the same token as in session
        assert data["csrf_token"] == self.sessions[session_token]["csrf_token"]

    def test_invalid_csrf_token_fails(self):
        """POST with invalid CSRF token should fail"""
        # Login
        login_response = self.client.post("/auth/login")
        session_token = login_response.json()["session_token"]

        # POST with invalid CSRF token
        response = self.client.post(
            "/api/data",
            headers={"X-CSRF-Token": "invalid-token"},
            cookies={"session_token": session_token}
        )
        assert response.status_code == 403

    def test_no_session_fails(self):
        """POST without session should fail"""
        response = self.client.post(
            "/api/data",
            headers={"X-CSRF-Token": "some-token"}
        )
        assert response.status_code == 403

    def test_csrf_cookie_set_on_get(self):
        """CSRF cookie should be set on GET requests"""
        # Login
        login_response = self.client.post("/auth/login")
        session_token = login_response.json()["session_token"]

        # GET request should set CSRF cookie
        response = self.client.get(
            "/api/data",
            cookies={"session_token": session_token}
        )
        assert response.status_code == 200
        assert "csrf_token" in response.cookies

    def test_double_submit_cookie_validation(self):
        """Cookie-based CSRF validation should work"""
        # Login
        login_response = self.client.post("/auth/login")
        session_token = login_response.json()["session_token"]

        # Generate CSRF token
        get_response = self.client.get(
            "/api/data",
            cookies={"session_token": session_token}
        )
        csrf_cookie = get_response.cookies.get("csrf_token")

        # POST with CSRF in cookie (double-submit)
        response = self.client.post(
            "/api/data",
            cookies={
                "session_token": session_token,
                "csrf_token": csrf_cookie
            }
        )
        # Should succeed (cookie matches session token)
        assert response.status_code == 200


class TestCSRFDisabled:
    """Test with CSRF protection disabled"""

    def setup_method(self):
        """Setup for each test"""
        self.app, self.sessions = create_test_app(csrf_enabled=False)
        self.client = TestClient(self.app)

    def test_post_without_csrf_succeeds_when_disabled(self):
        """POST should work without CSRF when protection is disabled"""
        # Login
        login_response = self.client.post("/auth/login")
        session_token = login_response.json()["session_token"]

        # POST without CSRF token should succeed
        response = self.client.post(
            "/api/data",
            cookies={"session_token": session_token}
        )
        assert response.status_code == 200


def run_manual_tests():
    """Run manual tests with detailed output"""
    print("=" * 60)
    print("CSRF Protection Test Suite")
    print("=" * 60)

    # Test 1: CSRF enabled - GET request
    print("\n[TEST 1] GET request (no CSRF required)")
    app, sessions = create_test_app(csrf_enabled=True)
    client = TestClient(app)
    response = client.get("/api/data")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✓ PASSED")

    # Test 2: CSRF enabled - POST without token
    print("\n[TEST 2] POST request without CSRF token (should fail)")
    login_response = client.post("/auth/login")
    session_token = login_response.json()["session_token"]
    response = client.post("/api/data", cookies={"session_token": session_token})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 403
    print("✓ PASSED")

    # Test 3: CSRF enabled - POST with token
    print("\n[TEST 3] POST request with CSRF token (should succeed)")
    # Generate CSRF token
    client.get("/api/data", cookies={"session_token": session_token})
    csrf_token = sessions[session_token]["csrf_token"]
    response = client.post(
        "/api/data",
        headers={"X-CSRF-Token": csrf_token},
        cookies={"session_token": session_token}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✓ PASSED")

    # Test 4: CSRF token endpoint
    print("\n[TEST 4] CSRF token endpoint")
    response = client.get(
        "/api/v1/auth/csrf-token",
        cookies={"session_token": session_token}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert "csrf_token" in response.json()
    print("✓ PASSED")

    # Test 5: CSRF disabled
    print("\n[TEST 5] POST without CSRF when protection disabled")
    app_disabled, _ = create_test_app(csrf_enabled=False)
    client_disabled = TestClient(app_disabled)
    login_response = client_disabled.post("/auth/login")
    session_token = login_response.json()["session_token"]
    response = client_disabled.post(
        "/api/data",
        cookies={"session_token": session_token}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✓ PASSED")

    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        # Run manual tests with output
        run_manual_tests()
    else:
        # Run pytest
        print("Running pytest tests...")
        print("Use --manual flag for detailed manual tests")
        pytest.main([__file__, "-v"])
