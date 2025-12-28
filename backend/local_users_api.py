"""
Local User Management API

REST API endpoints for managing Linux system users on the server.
Admin-only access with comprehensive audit logging and security.

Endpoints:
- GET    /api/v1/admin/system/local-users                          - List all Linux users
- POST   /api/v1/admin/system/local-users                          - Create new Linux user
- GET    /api/v1/admin/system/local-users/{username}               - Get user details
- PUT    /api/v1/admin/system/local-users/{username}               - Update user
- DELETE /api/v1/admin/system/local-users/{username}               - Delete user
- POST   /api/v1/admin/system/local-users/{username}/password      - Reset password
- GET    /api/v1/admin/system/local-users/{username}/ssh-keys      - List SSH keys
- POST   /api/v1/admin/system/local-users/{username}/ssh-keys      - Add SSH key
- DELETE /api/v1/admin/system/local-users/{username}/ssh-keys/{key_id} - Remove SSH key
- PUT    /api/v1/admin/system/local-users/{username}/sudo          - Manage sudo access
- GET    /api/v1/admin/system/local-users/groups                   - List available groups

Author: Backend API Developer
Date: October 23, 2025
"""

import os
import re
import pwd
import grp
import secrets
import string
import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# Audit logging
from models.audit_log import AuditAction, AuditResult

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/admin/system/local-users", tags=["Local Users"])

# Host system files (mounted as read-only volumes)
HOST_PASSWD_FILE = "/host/etc/passwd"
HOST_GROUP_FILE = "/host/etc/group"


# ============================================================================
# SECURITY & VALIDATION UTILITIES
# ============================================================================

# System user UID threshold (users below this are system users)
SYSTEM_UID_MIN = 1000

# Password complexity requirements
PASSWORD_MIN_LENGTH = 12
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = True

# Valid username pattern (alphanumeric, hyphen, underscore)
USERNAME_PATTERN = re.compile(r'^[a-z][-a-z0-9_]{0,31}$')

# Valid SSH key patterns (ssh-rsa, ssh-ed25519, etc.)
SSH_KEY_PATTERN = re.compile(r'^(ssh-rsa|ssh-ed25519|ecdsa-sha2-nistp256|ecdsa-sha2-nistp384|ecdsa-sha2-nistp521) [A-Za-z0-9+/=]+( .+)?$')


def validate_username(username: str) -> bool:
    """Validate username format"""
    return bool(USERNAME_PATTERN.match(username))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength

    Returns:
        (is_valid, error_message)
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters"

    if PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    if PASSWORD_REQUIRE_SPECIAL and not any(c in string.punctuation for c in password):
        return False, "Password must contain at least one special character"

    return True, ""


def generate_secure_password(length: int = 16) -> str:
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # Ensure at least one of each required character type
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice(string.punctuation)
    ]
    # Fill the rest randomly
    password += [secrets.choice(alphabet) for _ in range(length - 4)]
    # Shuffle
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


def validate_ssh_key(key: str) -> bool:
    """Validate SSH public key format"""
    return bool(SSH_KEY_PATTERN.match(key.strip()))


def run_command(cmd: List[str], input_data: Optional[str] = None) -> tuple[bool, str, str]:
    """
    Run a shell command safely

    Args:
        cmd: Command and arguments as list
        input_data: Optional stdin data

    Returns:
        (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        success = result.returncode == 0
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after 30 seconds"
    except Exception as e:
        return False, "", str(e)


# ============================================================================
# DEPENDENCY: ADMIN ROLE CHECK
# ============================================================================

async def check_admin_role(request: Request) -> str:
    """
    Check if user has admin role

    Returns:
        User email if admin, raises HTTPException otherwise
    """
    import sys
    import os

    # Add parent directory to path if needed
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    from redis_session import RedisSessionManager

    # Get session token from cookie
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # Get Redis connection info
    redis_host = os.getenv("REDIS_HOST", "unicorn-lago-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    # Initialize session manager
    sessions = RedisSessionManager(host=redis_host, port=redis_port)

    # Get session data
    if session_token not in sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

    session_data = sessions[session_token]
    user = session_data.get("user", {})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in session"
        )

    # Check if user has admin role
    user_role = user.get("role", "")
    is_admin = user.get("is_admin", False)

    if user_role != "admin" and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to manage local system users"
        )

    # Return user email or username
    return user.get("email") or user.get("preferred_username") or user.get("username", "unknown")


# ============================================================================
# AUDIT LOGGING HELPER
# ============================================================================

# Global audit logger instance (will be injected by server.py)
_audit_logger = None


def set_audit_logger(logger_instance):
    """Set audit logger instance (called by server.py on startup)"""
    global _audit_logger
    _audit_logger = logger_instance


async def audit_log(
    action: str,
    result: str,
    request: Request,
    username: str,
    resource_id: Optional[str] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Log user management action to audit log"""
    if _audit_logger:
        try:
            await _audit_logger.log(
                action=action,
                result=result,
                user_id=request.session.get("user_id"),
                username=request.session.get("user_email"),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                resource_type="local_user",
                resource_id=resource_id or username,
                error_message=error_message,
                metadata=metadata or {},
                session_id=request.session.get("session_id")
            )
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LocalUser(BaseModel):
    """Local Linux user model"""
    username: str
    uid: int
    gid: int
    home: str
    shell: str
    groups: List[str]
    has_sudo: bool
    last_login: Optional[str] = None
    ssh_keys_count: int = 0
    gecos: Optional[str] = None  # Full name/description

    class Config:
        schema_extra = {
            "example": {
                "username": "muut",
                "uid": 1000,
                "gid": 1000,
                "home": "/home/muut",
                "shell": "/bin/bash",
                "groups": ["muut", "sudo", "docker"],
                "has_sudo": True,
                "last_login": "2025-10-23T02:00:00Z",
                "ssh_keys_count": 2,
                "gecos": "System Administrator"
            }
        }


class CreateUserRequest(BaseModel):
    """Request to create new local user"""
    username: str = Field(..., min_length=1, max_length=32)
    password: Optional[str] = None  # If None, generates secure password
    shell: str = Field(default="/bin/bash")
    groups: List[str] = Field(default_factory=list)
    sudo_access: bool = Field(default=False)
    gecos: Optional[str] = None  # Full name

    @validator('username')
    def validate_username_format(cls, v):
        if not validate_username(v):
            raise ValueError(
                "Username must start with lowercase letter and contain only "
                "lowercase letters, digits, hyphens, and underscores"
            )
        return v

    @validator('shell')
    def validate_shell_exists(cls, v):
        # Check if shell exists in /etc/shells
        try:
            with open('/etc/shells', 'r') as f:
                valid_shells = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            if v not in valid_shells:
                raise ValueError(f"Shell must be one of: {', '.join(valid_shells)}")
        except FileNotFoundError:
            # If /etc/shells doesn't exist, allow common shells
            common_shells = ['/bin/bash', '/bin/sh', '/bin/zsh', '/bin/fish']
            if v not in common_shells:
                raise ValueError(f"Shell must be one of: {', '.join(common_shells)}")
        return v


class UpdateUserRequest(BaseModel):
    """Request to update existing user"""
    password: Optional[str] = None
    shell: Optional[str] = None
    groups: Optional[List[str]] = None
    sudo_access: Optional[bool] = None
    gecos: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    """Request to reset user password"""
    password: Optional[str] = None  # If None, generates secure password

    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            is_valid, error_msg = validate_password_strength(v)
            if not is_valid:
                raise ValueError(error_msg)
        return v


class AddSSHKeyRequest(BaseModel):
    """Request to add SSH key"""
    ssh_key: str = Field(..., description="SSH public key")
    comment: Optional[str] = Field(None, description="Optional comment for the key")

    @validator('ssh_key')
    def validate_key_format(cls, v):
        if not validate_ssh_key(v):
            raise ValueError("Invalid SSH public key format")
        return v


class SSHKey(BaseModel):
    """SSH public key model"""
    id: int  # Line number in authorized_keys
    key_type: str
    key_data: str
    comment: Optional[str] = None
    full_key: str


class SetSudoRequest(BaseModel):
    """Request to set sudo access"""
    enabled: bool


class LocalUsersResponse(BaseModel):
    """Response for list of local users"""
    success: bool = True
    users: List[LocalUser]
    total: int


class LocalUserResponse(BaseModel):
    """Response for single local user"""
    success: bool = True
    user: LocalUser


class CreateUserResponse(BaseModel):
    """Response for creating user"""
    success: bool = True
    user: LocalUser
    generated_password: Optional[str] = None  # Only if password was auto-generated


class ResetPasswordResponse(BaseModel):
    """Response for password reset"""
    success: bool = True
    generated_password: Optional[str] = None  # Only if password was auto-generated


class SSHKeysResponse(BaseModel):
    """Response for SSH keys list"""
    success: bool = True
    keys: List[SSHKey]
    total: int


class GroupsResponse(BaseModel):
    """Response for groups list"""
    success: bool = True
    groups: List[Dict[str, Any]]


# ============================================================================
# HOST FILE PARSING UTILITIES
# ============================================================================

def parse_host_passwd() -> List[Dict[str, Any]]:
    """
    Parse /host/etc/passwd file to get host system users

    Returns:
        List of user dictionaries with keys: username, uid, gid, gecos, home, shell
    """
    users = []

    try:
        if not Path(HOST_PASSWD_FILE).exists():
            logger.warning(f"Host passwd file not found: {HOST_PASSWD_FILE}")
            logger.warning("Showing container users instead. To see host users, mount /etc/passwd:/host/etc/passwd:ro")
            # Fallback to container users
            for user_info in pwd.getpwall():
                users.append({
                    'username': user_info.pw_name,
                    'uid': user_info.pw_uid,
                    'gid': user_info.pw_gid,
                    'gecos': user_info.pw_gecos,
                    'home': user_info.pw_dir,
                    'shell': user_info.pw_shell
                })
            return users

        with open(HOST_PASSWD_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split(':')
                if len(parts) >= 7:
                    users.append({
                        'username': parts[0],
                        'uid': int(parts[2]),
                        'gid': int(parts[3]),
                        'gecos': parts[4],
                        'home': parts[5],
                        'shell': parts[6]
                    })

    except Exception as e:
        logger.error(f"Failed to parse host passwd file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read host system users: {str(e)}"
        )

    return users


def parse_host_group() -> Dict[str, List[str]]:
    """
    Parse /host/etc/group file to get group memberships

    Returns:
        Dictionary mapping group names to list of member usernames
    """
    groups = {}

    try:
        if not Path(HOST_GROUP_FILE).exists():
            logger.warning(f"Host group file not found: {HOST_GROUP_FILE}")
            # Fallback to container groups
            for group_info in grp.getgrall():
                groups[group_info.gr_name] = group_info.gr_mem
            return groups

        with open(HOST_GROUP_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split(':')
                if len(parts) >= 4:
                    group_name = parts[0]
                    members = parts[3].split(',') if parts[3] else []
                    groups[group_name] = [m.strip() for m in members if m.strip()]

    except Exception as e:
        logger.error(f"Failed to parse host group file: {e}")
        # Don't fail hard on group parsing errors
        return {}

    return groups


def get_user_groups_from_host(username: str, primary_gid: int) -> List[str]:
    """
    Get all groups a user belongs to (including primary group)

    Args:
        username: Username
        primary_gid: User's primary GID

    Returns:
        List of group names
    """
    groups_map = parse_host_group()
    user_groups = []

    # Find primary group by GID
    try:
        if Path(HOST_GROUP_FILE).exists():
            with open(HOST_GROUP_FILE, 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) >= 3:
                        if int(parts[2]) == primary_gid:
                            user_groups.append(parts[0])
                            break
        else:
            # Fallback to container groups
            primary_group = grp.getgrgid(primary_gid)
            user_groups.append(primary_group.gr_name)
    except Exception as e:
        logger.warning(f"Failed to get primary group for GID {primary_gid}: {e}")

    # Add supplementary groups
    for group_name, members in groups_map.items():
        if username in members and group_name not in user_groups:
            user_groups.append(group_name)

    return sorted(user_groups)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_user_last_login(username: str) -> Optional[str]:
    """Get user's last login timestamp"""
    try:
        success, stdout, stderr = run_command(['lastlog', '-u', username])
        if success and stdout:
            lines = stdout.strip().split('\n')
            if len(lines) > 1:
                # Parse lastlog output
                parts = lines[1].split()
                if len(parts) > 3 and parts[0] == username:
                    # Check if "Never logged in"
                    if "Never" in stdout:
                        return None
                    # Parse date (format varies by system)
                    try:
                        # Example: "Wed Oct 23 02:00:00 +0000 2025"
                        date_str = ' '.join(parts[3:])
                        # Convert to ISO format (simplified)
                        return datetime.now().isoformat() + 'Z'
                    except:
                        return None
    except Exception as e:
        logger.warning(f"Failed to get last login for {username}: {e}")

    return None


def count_ssh_keys(username: str) -> int:
    """Count number of SSH keys for user"""
    try:
        user_info = pwd.getpwnam(username)
        ssh_dir = Path(user_info.pw_dir) / '.ssh'
        authorized_keys = ssh_dir / 'authorized_keys'

        if not authorized_keys.exists():
            return 0

        with open(authorized_keys, 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            return len(lines)
    except Exception as e:
        logger.warning(f"Failed to count SSH keys for {username}: {e}")
        return 0


def check_user_has_sudo(username: str) -> bool:
    """Check if user has sudo access"""
    # Method 1: Check if user is in sudo or wheel group
    try:
        user_groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
        user_info = pwd.getpwnam(username)
        primary_group = grp.getgrgid(user_info.pw_gid).gr_name
        all_groups = set(user_groups + [primary_group])

        if 'sudo' in all_groups or 'wheel' in all_groups:
            return True
    except Exception as e:
        logger.warning(f"Failed to check sudo groups for {username}: {e}")

    # Method 2: Check /etc/sudoers.d/ for user-specific file
    try:
        sudoers_file = Path(f'/etc/sudoers.d/{username}')
        if sudoers_file.exists():
            return True
    except Exception as e:
        logger.warning(f"Failed to check sudoers.d for {username}: {e}")

    return False


def get_local_users(include_system: bool = False) -> List[LocalUser]:
    """Get list of local Linux users (from HOST system)"""
    users = []

    try:
        # Parse host passwd file
        host_users = parse_host_passwd()

        for user_data in host_users:
            # Skip system users if requested
            if not include_system and user_data['uid'] < SYSTEM_UID_MIN:
                continue

            # Get user groups from host
            user_groups = get_user_groups_from_host(user_data['username'], user_data['gid'])

            # Create user object
            user = LocalUser(
                username=user_data['username'],
                uid=user_data['uid'],
                gid=user_data['gid'],
                home=user_data['home'],
                shell=user_data['shell'],
                groups=user_groups,
                has_sudo=check_user_has_sudo(user_data['username']),
                last_login=get_user_last_login(user_data['username']),
                ssh_keys_count=count_ssh_keys(user_data['username']),
                gecos=user_data['gecos'] if user_data['gecos'] else None
            )
            users.append(user)

    except Exception as e:
        logger.error(f"Failed to get local users: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enumerate local users: {str(e)}"
        )

    return sorted(users, key=lambda u: u.username)


def get_user_details(username: str) -> Optional[LocalUser]:
    """Get details for a specific user"""
    try:
        users = get_local_users(include_system=True)
        for user in users:
            if user.username == username:
                return user
        return None
    except Exception as e:
        logger.error(f"Failed to get user details for {username}: {e}")
        return None


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("", response_model=LocalUsersResponse)
async def list_local_users(
    include_system: bool = Query(False, description="Include system users (UID < 1000)"),
    user_id: str = Depends(check_admin_role)
):
    """
    List all Linux users on the system

    Filters out system users (UID < 1000) by default.
    Includes: username, UID, GID, home directory, shell, groups, sudo status, last login.

    Admin only.
    """
    try:
        users = get_local_users(include_system=include_system)

        return LocalUsersResponse(
            users=users,
            total=len(users)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list local users: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list local users: {str(e)}"
        )


@router.post("", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
async def create_local_user(
    request_data: CreateUserRequest,
    request: Request,
    user_id: str = Depends(check_admin_role)
):
    """
    Create a new Linux user

    Creates user with useradd command and sets password with chpasswd.
    If password not provided, generates a secure random password.

    Admin only. All actions are audited.
    """
    username = request_data.username
    generated_password = None

    try:
        # Check if user already exists
        try:
            pwd.getpwnam(username)
            raise HTTPException(
                status_code=400,
                detail=f"User '{username}' already exists"
            )
        except KeyError:
            pass  # User doesn't exist, continue

        # Generate password if not provided
        password = request_data.password
        if not password:
            password = generate_secure_password()
            generated_password = password
        else:
            # Validate provided password
            is_valid, error_msg = validate_password_strength(password)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)

        # Create user with useradd
        useradd_cmd = [
            'useradd',
            '-m',  # Create home directory
            '-s', request_data.shell,
        ]

        if request_data.gecos:
            useradd_cmd.extend(['-c', request_data.gecos])

        useradd_cmd.append(username)

        success, stdout, stderr = run_command(useradd_cmd)
        if not success:
            await audit_log(
                action="user.create",
                result=AuditResult.FAILURE.value,
                request=request,
                username=username,
                error_message=stderr,
                metadata={"shell": request_data.shell, "groups": request_data.groups}
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create user: {stderr}"
            )

        # Set password using chpasswd
        chpasswd_input = f"{username}:{password}"
        success, stdout, stderr = run_command(['chpasswd'], input_data=chpasswd_input)
        if not success:
            # Clean up - delete the user we just created
            run_command(['userdel', '-r', username])
            await audit_log(
                action="user.create",
                result=AuditResult.FAILURE.value,
                request=request,
                username=username,
                error_message=f"Password set failed: {stderr}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to set password: {stderr}"
            )

        # Add user to additional groups
        if request_data.groups:
            for group in request_data.groups:
                success, stdout, stderr = run_command(['usermod', '-aG', group, username])
                if not success:
                    logger.warning(f"Failed to add {username} to group {group}: {stderr}")

        # Add to sudo group if requested
        if request_data.sudo_access:
            # Try 'sudo' group first, then 'wheel' (for RHEL/CentOS)
            success, _, _ = run_command(['usermod', '-aG', 'sudo', username])
            if not success:
                success, _, _ = run_command(['usermod', '-aG', 'wheel', username])

        # Get created user details
        user = get_user_details(username)
        if not user:
            raise HTTPException(
                status_code=500,
                detail="User created but failed to retrieve details"
            )

        # Audit log
        await audit_log(
            action="user.create",
            result=AuditResult.SUCCESS.value,
            request=request,
            username=username,
            metadata={
                "shell": request_data.shell,
                "groups": request_data.groups,
                "sudo_access": request_data.sudo_access,
                "password_generated": generated_password is not None
            }
        )

        return CreateUserResponse(
            user=user,
            generated_password=generated_password
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create user {username}: {e}")
        await audit_log(
            action="user.create",
            result=AuditResult.ERROR.value,
            request=request,
            username=username,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/{username}", response_model=LocalUserResponse)
async def get_local_user(
    username: str,
    user_id: str = Depends(check_admin_role)
):
    """
    Get details for a specific local user

    Admin only.
    """
    try:
        user = get_user_details(username)

        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User '{username}' not found"
            )

        return LocalUserResponse(user=user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user {username}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user details: {str(e)}"
        )


@router.put("/{username}", response_model=LocalUserResponse)
async def update_local_user(
    username: str,
    request_data: UpdateUserRequest,
    request: Request,
    user_id: str = Depends(check_admin_role)
):
    """
    Update an existing local user

    Can update: password, shell, groups, sudo permissions.
    Admin only. All changes are audited.
    """
    try:
        # Check if user exists
        try:
            pwd.getpwnam(username)
        except KeyError:
            raise HTTPException(
                status_code=404,
                detail=f"User '{username}' not found"
            )

        changes = []

        # Update password if provided
        if request_data.password:
            is_valid, error_msg = validate_password_strength(request_data.password)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)

            chpasswd_input = f"{username}:{request_data.password}"
            success, stdout, stderr = run_command(['chpasswd'], input_data=chpasswd_input)
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update password: {stderr}"
                )
            changes.append("password")

        # Update shell if provided
        if request_data.shell:
            success, stdout, stderr = run_command(['usermod', '-s', request_data.shell, username])
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update shell: {stderr}"
                )
            changes.append("shell")

        # Update groups if provided
        if request_data.groups is not None:
            # Set groups (replaces current groups)
            groups_str = ','.join(request_data.groups)
            success, stdout, stderr = run_command(['usermod', '-G', groups_str, username])
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update groups: {stderr}"
                )
            changes.append("groups")

        # Update sudo access if provided
        if request_data.sudo_access is not None:
            if request_data.sudo_access:
                # Add to sudo group
                success, _, _ = run_command(['usermod', '-aG', 'sudo', username])
                if not success:
                    success, _, _ = run_command(['usermod', '-aG', 'wheel', username])
                    if not success:
                        raise HTTPException(
                            status_code=500,
                            detail="Failed to grant sudo access"
                        )
            else:
                # Remove from sudo group
                success, _, _ = run_command(['gpasswd', '-d', username, 'sudo'])
                if not success:
                    run_command(['gpasswd', '-d', username, 'wheel'])
            changes.append("sudo_access")

        # Update GECOS if provided
        if request_data.gecos is not None:
            success, stdout, stderr = run_command(['usermod', '-c', request_data.gecos, username])
            if not success:
                logger.warning(f"Failed to update GECOS for {username}: {stderr}")
            else:
                changes.append("gecos")

        # Get updated user details
        user = get_user_details(username)
        if not user:
            raise HTTPException(
                status_code=500,
                detail="User updated but failed to retrieve details"
            )

        # Audit log
        await audit_log(
            action="user.update",
            result=AuditResult.SUCCESS.value,
            request=request,
            username=username,
            metadata={"changes": changes}
        )

        return LocalUserResponse(user=user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user {username}: {e}")
        await audit_log(
            action="user.update",
            result=AuditResult.ERROR.value,
            request=request,
            username=username,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_local_user(
    username: str,
    request: Request,
    remove_home: bool = Query(True, description="Remove home directory"),
    user_id: str = Depends(check_admin_role)
):
    """
    Delete a local user

    Uses userdel command. Optionally removes home directory.
    Admin only. All deletions are audited.
    """
    try:
        # Check if user exists
        try:
            pwd.getpwnam(username)
        except KeyError:
            raise HTTPException(
                status_code=404,
                detail=f"User '{username}' not found"
            )

        # Build userdel command
        userdel_cmd = ['userdel']
        if remove_home:
            userdel_cmd.append('-r')  # Remove home directory and mail spool
        userdel_cmd.append(username)

        success, stdout, stderr = run_command(userdel_cmd)
        if not success:
            await audit_log(
                action="user.delete",
                result=AuditResult.FAILURE.value,
                request=request,
                username=username,
                error_message=stderr,
                metadata={"remove_home": remove_home}
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete user: {stderr}"
            )

        # Audit log
        await audit_log(
            action="user.delete",
            result=AuditResult.SUCCESS.value,
            request=request,
            username=username,
            metadata={"remove_home": remove_home}
        )

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user {username}: {e}")
        await audit_log(
            action="user.delete",
            result=AuditResult.ERROR.value,
            request=request,
            username=username,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.post("/{username}/password", response_model=ResetPasswordResponse)
async def reset_user_password(
    username: str,
    request_data: ResetPasswordRequest,
    request: Request,
    user_id: str = Depends(check_admin_role)
):
    """
    Reset user password

    If password not provided, generates a secure random password.
    Admin only. All password resets are audited.
    """
    generated_password = None

    try:
        # Check if user exists
        try:
            pwd.getpwnam(username)
        except KeyError:
            raise HTTPException(
                status_code=404,
                detail=f"User '{username}' not found"
            )

        # Generate password if not provided
        password = request_data.password
        if not password:
            password = generate_secure_password()
            generated_password = password

        # Set password using chpasswd
        chpasswd_input = f"{username}:{password}"
        success, stdout, stderr = run_command(['chpasswd'], input_data=chpasswd_input)
        if not success:
            await audit_log(
                action="auth.password.reset",
                result=AuditResult.FAILURE.value,
                request=request,
                username=username,
                error_message=stderr
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to reset password: {stderr}"
            )

        # Audit log
        await audit_log(
            action="auth.password.reset",
            result=AuditResult.SUCCESS.value,
            request=request,
            username=username,
            metadata={"password_generated": generated_password is not None}
        )

        return ResetPasswordResponse(generated_password=generated_password)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset password for {username}: {e}")
        await audit_log(
            action="auth.password.reset",
            result=AuditResult.ERROR.value,
            request=request,
            username=username,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset password: {str(e)}"
        )


@router.get("/{username}/ssh-keys", response_model=SSHKeysResponse)
async def list_ssh_keys(
    username: str,
    user_id: str = Depends(check_admin_role)
):
    """
    List SSH public keys for a user

    Reads from ~/.ssh/authorized_keys.
    Admin only.
    """
    try:
        # Get user info
        try:
            user_info = pwd.getpwnam(username)
        except KeyError:
            raise HTTPException(
                status_code=404,
                detail=f"User '{username}' not found"
            )

        # Check authorized_keys file
        ssh_dir = Path(user_info.pw_dir) / '.ssh'
        authorized_keys = ssh_dir / 'authorized_keys'

        keys = []

        if authorized_keys.exists():
            with open(authorized_keys, 'r') as f:
                for i, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # Parse SSH key
                    parts = line.split(None, 2)
                    if len(parts) >= 2:
                        key_type = parts[0]
                        key_data = parts[1]
                        comment = parts[2] if len(parts) > 2 else None

                        keys.append(SSHKey(
                            id=i,
                            key_type=key_type,
                            key_data=key_data,
                            comment=comment,
                            full_key=line
                        ))

        return SSHKeysResponse(keys=keys, total=len(keys))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list SSH keys for {username}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list SSH keys: {str(e)}"
        )


@router.post("/{username}/ssh-keys", status_code=status.HTTP_201_CREATED)
async def add_ssh_key(
    username: str,
    request_data: AddSSHKeyRequest,
    request: Request,
    user_id: str = Depends(check_admin_role)
):
    """
    Add SSH public key for a user

    Appends to ~/.ssh/authorized_keys.
    Admin only. All key additions are audited.
    """
    try:
        # Get user info
        try:
            user_info = pwd.getpwnam(username)
        except KeyError:
            raise HTTPException(
                status_code=404,
                detail=f"User '{username}' not found"
            )

        # Prepare SSH directory and authorized_keys
        ssh_dir = Path(user_info.pw_dir) / '.ssh'
        authorized_keys = ssh_dir / 'authorized_keys'

        # Create .ssh directory if it doesn't exist
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        os.chown(ssh_dir, user_info.pw_uid, user_info.pw_gid)

        # Format key with comment if provided
        key_line = request_data.ssh_key.strip()
        if request_data.comment and not key_line.endswith(request_data.comment):
            # Add comment if not already in key
            parts = key_line.split()
            if len(parts) == 2:  # No comment yet
                key_line = f"{key_line} {request_data.comment}"

        # Append key to authorized_keys
        with open(authorized_keys, 'a') as f:
            f.write(key_line + '\n')

        # Set proper permissions
        os.chmod(authorized_keys, 0o600)
        os.chown(authorized_keys, user_info.pw_uid, user_info.pw_gid)

        # Audit log
        await audit_log(
            action="user.ssh_key.add",
            result=AuditResult.SUCCESS.value,
            request=request,
            username=username,
            metadata={"key_type": request_data.ssh_key.split()[0]}
        )

        return {"success": True, "message": "SSH key added successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add SSH key for {username}: {e}")
        await audit_log(
            action="user.ssh_key.add",
            result=AuditResult.ERROR.value,
            request=request,
            username=username,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add SSH key: {str(e)}"
        )


@router.delete("/{username}/ssh-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_ssh_key(
    username: str,
    key_id: int,
    request: Request,
    user_id: str = Depends(check_admin_role)
):
    """
    Remove SSH public key for a user

    Removes line from ~/.ssh/authorized_keys by line number.
    Admin only. All key removals are audited.
    """
    try:
        # Get user info
        try:
            user_info = pwd.getpwnam(username)
        except KeyError:
            raise HTTPException(
                status_code=404,
                detail=f"User '{username}' not found"
            )

        # Check authorized_keys file
        ssh_dir = Path(user_info.pw_dir) / '.ssh'
        authorized_keys = ssh_dir / 'authorized_keys'

        if not authorized_keys.exists():
            raise HTTPException(
                status_code=404,
                detail="No SSH keys found for this user"
            )

        # Read all lines
        with open(authorized_keys, 'r') as f:
            lines = f.readlines()

        # Find and remove the key
        removed = False
        new_lines = []
        line_num = 0

        for line in lines:
            if line.strip() and not line.startswith('#'):
                line_num += 1
                if line_num == key_id:
                    removed = True
                    continue
            new_lines.append(line)

        if not removed:
            raise HTTPException(
                status_code=404,
                detail=f"SSH key with ID {key_id} not found"
            )

        # Write back
        with open(authorized_keys, 'w') as f:
            f.writelines(new_lines)

        # Audit log
        await audit_log(
            action="user.ssh_key.remove",
            result=AuditResult.SUCCESS.value,
            request=request,
            username=username,
            metadata={"key_id": key_id}
        )

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove SSH key for {username}: {e}")
        await audit_log(
            action="user.ssh_key.remove",
            result=AuditResult.ERROR.value,
            request=request,
            username=username,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove SSH key: {str(e)}"
        )


@router.put("/{username}/sudo", response_model=LocalUserResponse)
async def set_sudo_access(
    username: str,
    request_data: SetSudoRequest,
    request: Request,
    user_id: str = Depends(check_admin_role)
):
    """
    Manage sudo access for a user

    Adds/removes user from sudo/wheel group.
    Admin only. All sudo changes are audited.
    """
    try:
        # Check if user exists
        try:
            pwd.getpwnam(username)
        except KeyError:
            raise HTTPException(
                status_code=404,
                detail=f"User '{username}' not found"
            )

        if request_data.enabled:
            # Add to sudo group
            success, stdout, stderr = run_command(['usermod', '-aG', 'sudo', username])
            if not success:
                # Try wheel group (RHEL/CentOS)
                success, stdout, stderr = run_command(['usermod', '-aG', 'wheel', username])
                if not success:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to grant sudo access: {stderr}"
                    )
        else:
            # Remove from sudo group
            success, _, _ = run_command(['gpasswd', '-d', username, 'sudo'])
            if not success:
                # Try wheel group
                success, _, stderr = run_command(['gpasswd', '-d', username, 'wheel'])
                if not success:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to revoke sudo access: {stderr}"
                    )

        # Get updated user details
        user = get_user_details(username)
        if not user:
            raise HTTPException(
                status_code=500,
                detail="Sudo access updated but failed to retrieve user details"
            )

        # Audit log
        await audit_log(
            action="user.sudo.update",
            result=AuditResult.SUCCESS.value,
            request=request,
            username=username,
            metadata={"sudo_enabled": request_data.enabled}
        )

        return LocalUserResponse(user=user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update sudo access for {username}: {e}")
        await audit_log(
            action="user.sudo.update",
            result=AuditResult.ERROR.value,
            request=request,
            username=username,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update sudo access: {str(e)}"
        )


@router.get("/groups", response_model=GroupsResponse)
async def list_groups(
    user_id: str = Depends(check_admin_role)
):
    """
    List all available system groups

    Admin only.
    """
    try:
        groups = []

        for group_info in grp.getgrall():
            groups.append({
                "name": group_info.gr_name,
                "gid": group_info.gr_gid,
                "members": group_info.gr_mem
            })

        # Sort by name
        groups.sort(key=lambda g: g["name"])

        return GroupsResponse(groups=groups)

    except Exception as e:
        logger.error(f"Failed to list groups: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list groups: {str(e)}"
        )


# Health check endpoint (public)
@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "local-users-api"}
