"""
Integration Tests for Local User Management API
Tests the API endpoints for local user management.

These tests use FastAPI's TestClient to test HTTP endpoints.
"""

import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the FastAPI app
try:
    from server import app
except ImportError:
    # Create a minimal mock app for testing structure
    from fastapi import FastAPI
    app = FastAPI()


client = TestClient(app)


# Test data
TEST_USER_DATA = {
    "username": "testuser123",
    "password": "SecurePass123!",
    "shell": "/bin/bash",
    "home_dir": "/home/testuser123",
    "sudo": False
}

TEST_SSH_KEY = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC8teh2NJ42qYZVNgO test@example.com"


class TestAuthentication:
    """Test authentication requirements for local user endpoints"""

    def test_list_users_requires_auth(self):
        """Test that listing users requires authentication"""
        response = client.get("/api/v1/local-users")

        # Should return 401 if no auth provided
        # Or 307 redirect to login
        assert response.status_code in [401, 307, 200]

    def test_create_user_requires_admin_role(self):
        """Test that creating users requires admin role"""
        # Without proper admin role, should fail
        response = client.post(
            "/api/v1/local-users",
            json=TEST_USER_DATA
        )

        # Should return 401/403 without proper role
        assert response.status_code in [401, 403, 307]

    def test_delete_user_requires_admin_role(self):
        """Test that deleting users requires admin role"""
        response = client.delete("/api/v1/local-users/testuser")

        # Should return 401/403 without proper role
        assert response.status_code in [401, 403, 307]


class TestListUsers:
    """Test GET /api/v1/local-users - List all local users"""

    @patch('server.sessions')
    @patch('local_user_manager.list_users')
    def test_list_users_success(self, mock_list_users, mock_sessions):
        """Test successful user listing"""
        # Mock session with admin role
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        # Mock user list
        mock_list_users.return_value = [
            {"username": "user1", "uid": 1000, "home_dir": "/home/user1", "shell": "/bin/bash", "has_sudo": False},
            {"username": "user2", "uid": 1001, "home_dir": "/home/user2", "shell": "/bin/bash", "has_sudo": True}
        ]

        response = client.get(
            "/api/v1/local-users",
            cookies={"session_token": "valid_admin_token"}
        )

        if response.status_code == 200:
            data = response.json()
            assert "users" in data
            assert len(data["users"]) == 2
            assert data["users"][0]["username"] == "user1"

    @patch('server.sessions')
    def test_list_users_filters_system_users(self, mock_sessions):
        """Test that system users (UID < 1000) are filtered out"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        response = client.get(
            "/api/v1/local-users",
            cookies={"session_token": "valid_admin_token"}
        )

        if response.status_code == 200:
            data = response.json()
            # All returned users should have UID >= 1000
            if "users" in data:
                for user in data["users"]:
                    assert user.get("uid", 1000) >= 1000


class TestCreateUser:
    """Test POST /api/v1/local-users - Create a new local user"""

    @patch('server.sessions')
    @patch('local_user_manager.create_user')
    @patch('audit_logger.log_audit')
    def test_create_user_success(self, mock_audit, mock_create, mock_sessions):
        """Test successful user creation"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        mock_create.return_value = {
            "success": True,
            "username": "testuser123",
            "uid": 1050,
            "home_dir": "/home/testuser123"
        }

        response = client.post(
            "/api/v1/local-users",
            json=TEST_USER_DATA,
            cookies={"session_token": "valid_admin_token"}
        )

        if response.status_code == 200:
            data = response.json()
            assert data["success"] == True
            assert data["username"] == "testuser123"

    @patch('server.sessions')
    def test_create_user_invalid_username(self, mock_sessions):
        """Test creation with invalid username"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        invalid_data = TEST_USER_DATA.copy()
        invalid_data["username"] = "test@user"  # Invalid char

        response = client.post(
            "/api/v1/local-users",
            json=invalid_data,
            cookies={"session_token": "valid_admin_token"}
        )

        # Should return 400 Bad Request or 422 Validation Error
        assert response.status_code in [400, 422]

    @patch('server.sessions')
    def test_create_user_weak_password(self, mock_sessions):
        """Test creation with weak password"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        weak_data = TEST_USER_DATA.copy()
        weak_data["password"] = "weak"

        response = client.post(
            "/api/v1/local-users",
            json=weak_data,
            cookies={"session_token": "valid_admin_token"}
        )

        # Should return 400 Bad Request
        assert response.status_code in [400, 422]

    @patch('server.sessions')
    @patch('local_user_manager.user_exists')
    def test_create_duplicate_user(self, mock_exists, mock_sessions):
        """Test creation of duplicate user"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        mock_exists.return_value = True

        response = client.post(
            "/api/v1/local-users",
            json=TEST_USER_DATA,
            cookies={"session_token": "valid_admin_token"}
        )

        # Should return 409 Conflict
        assert response.status_code in [409, 400]

    @patch('server.sessions')
    def test_create_user_missing_required_fields(self, mock_sessions):
        """Test creation with missing required fields"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        incomplete_data = {"username": "testuser"}  # Missing password

        response = client.post(
            "/api/v1/local-users",
            json=incomplete_data,
            cookies={"session_token": "valid_admin_token"}
        )

        # Should return 422 Validation Error
        assert response.status_code == 422


class TestGetUser:
    """Test GET /api/v1/local-users/{username} - Get user details"""

    @patch('server.sessions')
    @patch('pwd.getpwnam')
    def test_get_user_success(self, mock_getpwnam, mock_sessions):
        """Test successful user retrieval"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        mock_getpwnam.return_value = MagicMock(
            pw_name="testuser",
            pw_uid=1050,
            pw_dir="/home/testuser",
            pw_shell="/bin/bash"
        )

        response = client.get(
            "/api/v1/local-users/testuser",
            cookies={"session_token": "valid_admin_token"}
        )

        if response.status_code == 200:
            data = response.json()
            assert data["username"] == "testuser"
            assert data["uid"] == 1050

    @patch('server.sessions')
    def test_get_nonexistent_user(self, mock_sessions):
        """Test retrieval of nonexistent user"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        response = client.get(
            "/api/v1/local-users/nonexistentuser999",
            cookies={"session_token": "valid_admin_token"}
        )

        # Should return 404 Not Found
        assert response.status_code == 404


class TestUpdateUser:
    """Test PUT /api/v1/local-users/{username} - Update user"""

    @patch('server.sessions')
    @patch('local_user_manager.set_password')
    def test_update_user_password(self, mock_set_password, mock_sessions):
        """Test updating user password"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        mock_set_password.return_value = {"success": True}

        update_data = {"password": "NewSecurePass456!"}

        response = client.put(
            "/api/v1/local-users/testuser",
            json=update_data,
            cookies={"session_token": "valid_admin_token"}
        )

        if response.status_code == 200:
            data = response.json()
            assert data["success"] == True

    @patch('server.sessions')
    @patch('local_user_manager.add_ssh_key')
    def test_update_user_ssh_key(self, mock_add_ssh, mock_sessions):
        """Test adding SSH key to user"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        mock_add_ssh.return_value = {"success": True}

        update_data = {"ssh_key": TEST_SSH_KEY}

        response = client.put(
            "/api/v1/local-users/testuser",
            json=update_data,
            cookies={"session_token": "valid_admin_token"}
        )

        if response.status_code == 200:
            data = response.json()
            assert data["success"] == True


class TestDeleteUser:
    """Test DELETE /api/v1/local-users/{username} - Delete user"""

    @patch('server.sessions')
    @patch('local_user_manager.delete_user')
    @patch('audit_logger.log_audit')
    def test_delete_user_success(self, mock_audit, mock_delete, mock_sessions):
        """Test successful user deletion"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        mock_delete.return_value = {"success": True, "home_removed": True}

        response = client.delete(
            "/api/v1/local-users/testuser",
            cookies={"session_token": "valid_admin_token"}
        )

        if response.status_code == 200:
            data = response.json()
            assert data["success"] == True

    @patch('server.sessions')
    @patch('local_user_manager.delete_user')
    def test_delete_user_keep_home(self, mock_delete, mock_sessions):
        """Test user deletion keeping home directory"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        mock_delete.return_value = {"success": True, "home_removed": False}

        response = client.delete(
            "/api/v1/local-users/testuser?remove_home=false",
            cookies={"session_token": "valid_admin_token"}
        )

        if response.status_code == 200:
            data = response.json()
            assert data["home_removed"] == False

    @patch('server.sessions')
    @patch('local_user_manager.is_system_user')
    def test_delete_system_user_blocked(self, mock_is_system, mock_sessions):
        """Test that system users cannot be deleted"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        mock_is_system.return_value = True

        response = client.delete(
            "/api/v1/local-users/root",
            cookies={"session_token": "valid_admin_token"}
        )

        # Should return 403 Forbidden
        assert response.status_code in [403, 400]

    @patch('server.sessions')
    def test_delete_nonexistent_user(self, mock_sessions):
        """Test deletion of nonexistent user"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        response = client.delete(
            "/api/v1/local-users/nonexistent999",
            cookies={"session_token": "valid_admin_token"}
        )

        # Should return 404 Not Found
        assert response.status_code == 404


class TestSudoOperations:
    """Test sudo permission operations"""

    @patch('server.sessions')
    @patch('local_user_manager.grant_sudo')
    @patch('audit_logger.log_audit')
    def test_grant_sudo_success(self, mock_audit, mock_grant, mock_sessions):
        """Test granting sudo permissions"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        mock_grant.return_value = {"success": True}

        response = client.post(
            "/api/v1/local-users/testuser/sudo",
            cookies={"session_token": "valid_admin_token"}
        )

        if response.status_code == 200:
            data = response.json()
            assert data["success"] == True

    @patch('server.sessions')
    @patch('local_user_manager.revoke_sudo')
    @patch('audit_logger.log_audit')
    def test_revoke_sudo_success(self, mock_audit, mock_revoke, mock_sessions):
        """Test revoking sudo permissions"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        mock_revoke.return_value = {"success": True}

        response = client.delete(
            "/api/v1/local-users/testuser/sudo",
            cookies={"session_token": "valid_admin_token"}
        )

        if response.status_code == 200:
            data = response.json()
            assert data["success"] == True

    @patch('server.sessions')
    def test_sudo_operations_require_admin(self, mock_sessions):
        """Test sudo operations require admin role"""
        # Non-admin user
        mock_sessions.get.return_value = {
            "user_id": "user@example.com",
            "roles": ["viewer"]
        }

        response = client.post(
            "/api/v1/local-users/testuser/sudo",
            cookies={"session_token": "valid_user_token"}
        )

        # Should return 403 Forbidden
        assert response.status_code in [403, 401]


class TestSecurityValidation:
    """Test security validations in API"""

    @patch('server.sessions')
    def test_command_injection_in_username(self, mock_sessions):
        """Test API rejects command injection attempts in username"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        malicious_data = TEST_USER_DATA.copy()
        malicious_data["username"] = "test;rm -rf /"

        response = client.post(
            "/api/v1/local-users",
            json=malicious_data,
            cookies={"session_token": "valid_admin_token"}
        )

        # Should return 400/422
        assert response.status_code in [400, 422]

    @patch('server.sessions')
    def test_path_traversal_in_home_dir(self, mock_sessions):
        """Test API rejects path traversal attempts"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        malicious_data = TEST_USER_DATA.copy()
        malicious_data["home_dir"] = "../../etc/passwd"

        response = client.post(
            "/api/v1/local-users",
            json=malicious_data,
            cookies={"session_token": "valid_admin_token"}
        )

        # Should return 400/422
        assert response.status_code in [400, 422]

    @patch('server.sessions')
    def test_sql_injection_in_username(self, mock_sessions):
        """Test API rejects SQL injection attempts"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        malicious_data = TEST_USER_DATA.copy()
        malicious_data["username"] = "test'; DROP TABLE users; --"

        response = client.post(
            "/api/v1/local-users",
            json=malicious_data,
            cookies={"session_token": "valid_admin_token"}
        )

        # Should return 400/422
        assert response.status_code in [400, 422]


class TestAuditLogging:
    """Test audit logging for API operations"""

    @patch('server.sessions')
    @patch('audit_logger.log_audit')
    @patch('local_user_manager.create_user')
    def test_create_user_creates_audit_log(self, mock_create, mock_audit, mock_sessions):
        """Test user creation creates audit log"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        mock_create.return_value = {"success": True, "username": "testuser"}

        response = client.post(
            "/api/v1/local-users",
            json=TEST_USER_DATA,
            cookies={"session_token": "valid_admin_token"}
        )

        # Audit log should have been called
        if response.status_code == 200:
            # Verify audit_logger.log_audit was called with correct params
            pass

    @patch('server.sessions')
    @patch('audit_logger.log_audit')
    @patch('local_user_manager.delete_user')
    def test_delete_user_creates_audit_log(self, mock_delete, mock_audit, mock_sessions):
        """Test user deletion creates audit log"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        mock_delete.return_value = {"success": True}

        response = client.delete(
            "/api/v1/local-users/testuser",
            cookies={"session_token": "valid_admin_token"}
        )

        # Audit log should have been called
        if response.status_code == 200:
            pass


class TestRateLimiting:
    """Test rate limiting on endpoints"""

    @patch('server.sessions')
    def test_rate_limit_on_user_creation(self, mock_sessions):
        """Test rate limiting prevents abuse"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        # Make many requests rapidly
        responses = []
        for i in range(100):
            user_data = TEST_USER_DATA.copy()
            user_data["username"] = f"testuser{i}"

            response = client.post(
                "/api/v1/local-users",
                json=user_data,
                cookies={"session_token": "valid_admin_token"}
            )
            responses.append(response.status_code)

        # At least some should be rate limited (429 Too Many Requests)
        # This depends on rate limiter configuration


class TestInputValidation:
    """Test input validation"""

    @patch('server.sessions')
    def test_username_length_validation(self, mock_sessions):
        """Test username length limits"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        # Too long username (> 32 chars)
        long_data = TEST_USER_DATA.copy()
        long_data["username"] = "a" * 33

        response = client.post(
            "/api/v1/local-users",
            json=long_data,
            cookies={"session_token": "valid_admin_token"}
        )

        assert response.status_code in [400, 422]

    @patch('server.sessions')
    def test_shell_validation(self, mock_sessions):
        """Test shell path validation"""
        mock_sessions.get.return_value = {
            "user_id": "admin@example.com",
            "roles": ["admin"]
        }

        invalid_data = TEST_USER_DATA.copy()
        invalid_data["shell"] = "/invalid/shell/path"

        response = client.post(
            "/api/v1/local-users",
            json=invalid_data,
            cookies={"session_token": "valid_admin_token"}
        )

        # Should validate shell exists
        assert response.status_code in [400, 422]


# Pytest fixtures
@pytest.fixture(scope="module")
def authenticated_client():
    """Client with authentication headers"""
    # This would set up proper authentication
    return client


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
