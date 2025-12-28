"""
Local User Management API
FastAPI endpoints for managing Linux system users.

Security: All endpoints require admin role.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from local_user_manager import (
    create_user, delete_user, set_password, add_ssh_key, remove_ssh_key,
    list_ssh_keys, set_sudo_permissions, get_user_info, list_users,
    get_statistics,
    ValidationError, SecurityError, SystemError as LocalSystemError
)
from audit_logger import audit_logger
from audit_helpers import get_client_ip, get_user_agent

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/local-users", tags=["Local Users"])


# Pydantic models
class CreateUserRequest(BaseModel):
    username: str = Field(..., description="Username for new user")
    full_name: Optional[str] = Field(None, description="Full name (GECOS field)")
    shell: str = Field("/bin/bash", description="Login shell")
    create_home: bool = Field(True, description="Create home directory")
    groups: Optional[List[str]] = Field(None, description="Additional groups")
    password: Optional[str] = Field(None, description="Initial password")

    @validator('username')
    def validate_username(cls, v):
        if not v:
            raise ValueError("Username cannot be empty")
        if len(v) > 32:
            raise ValueError("Username too long (max 32 characters)")
        return v.lower()


class SetPasswordRequest(BaseModel):
    # SECURITY FIX: Increased minimum password length from 8 to 12
    password: str = Field(..., min_length=12, description="New password (min 12 characters with complexity)")


class AddSSHKeyRequest(BaseModel):
    ssh_key: str = Field(..., description="SSH public key")
    key_title: Optional[str] = Field(None, description="Optional key title/comment")

    @validator('ssh_key')
    def validate_ssh_key(cls, v):
        if not v or not v.strip():
            raise ValueError("SSH key cannot be empty")
        return v.strip()


class RemoveSSHKeyRequest(BaseModel):
    key_fingerprint: str = Field(..., description="Fingerprint of key to remove")


class SudoPermissionsRequest(BaseModel):
    grant: bool = Field(..., description="True to grant sudo, False to revoke")


class UserResponse(BaseModel):
    username: str
    uid: int
    gid: int
    full_name: str
    home_dir: str
    shell: str
    groups: List[str]
    has_sudo: bool
    home_size_bytes: int
    is_system_user: bool


class SSHKeyResponse(BaseModel):
    type: str
    fingerprint: str
    comment: str


class AuditLogEntry(BaseModel):
    action: str
    username: str
    performed_by: str
    success: bool
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]
    timestamp: datetime


# Dependency for admin role check
async def require_admin_role(request: Request):
    """
    Ensure user has admin role for local user management.

    SECURITY: Verifies authentication and authorization before allowing operations.

    Raises:
        HTTPException: If user is not authenticated or not admin
    """
    # SECURITY FIX: Defensive checks for authentication middleware
    # Get session from request state (set by auth middleware)
    user_info = getattr(request.state, 'user_info', None)

    if not user_info:
        logger.warning("Unauthorized access attempt to local user API - no user_info in request.state")
        # SECURITY: Log authentication failure for audit
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please log in to access local user management."
        )

    # SECURITY: Validate user_info has required fields
    if not user_info.get('id') and not user_info.get('email'):
        logger.error("Invalid user_info in request.state - missing id and email")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication session. Please log in again."
        )

    # Check if user has admin role
    user_roles = user_info.get('roles', [])
    if 'admin' not in user_roles:
        logger.warning(f"Non-admin user {user_info.get('email')} attempted local user operation")
        # SECURITY: Log permission denial
        await audit_logger.log_permission_denied(
            user_id=user_info.get('id'),
            resource="local-users",
            action="access",
            reason="Admin role required"
        )
        raise HTTPException(
            status_code=403,
            detail="Admin role required. Contact your system administrator for access."
        )

    return user_info


async def log_audit(
    action: str,
    username: str,
    user_info: dict,
    success: bool,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log local user management action to audit log.
    """
    try:
        await audit_logger.log_custom(
            user_id=user_info.get('id'),
            action=action,
            resource_type="local_user",
            resource_id=username,
            details={
                "username": username,
                "performed_by": user_info.get('email'),
                "success": success,
                "error_message": error_message,
                "metadata": metadata or {}
            },
            severity="high" if action in ['create', 'delete', 'sudo_grant'] else "medium"
        )
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")


# API Endpoints

@router.get("/", response_model=List[UserResponse])
async def list_local_users(
    include_system: bool = False,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    has_sudo: Optional[bool] = None,
    uid_min: Optional[int] = None,
    uid_max: Optional[int] = None,
    user_info: dict = Depends(require_admin_role)
):
    """
    List local Linux users with pagination and filtering.

    **Requires**: Admin role

    **NEW FEATURES**:
    - Pagination support (skip/limit)
    - Search by username
    - Filter by sudo status
    - Filter by UID range

    **Parameters**:
    - `include_system`: Include system users (UID < 1000)
    - `skip`: Number of users to skip (pagination offset) [default: 0]
    - `limit`: Maximum number of users to return [default: 50, max: 100]
    - `search`: Search username pattern (partial match)
    - `has_sudo`: Filter by sudo status (true/false)
    - `uid_min`: Minimum UID to include
    - `uid_max`: Maximum UID to include

    **Returns**: List of user information objects (paginated)
    """
    try:
        # Validate pagination parameters
        if skip < 0:
            raise HTTPException(status_code=400, detail="skip must be >= 0")
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

        # Get all users
        all_users = list_users(include_system=include_system)

        # Apply filters
        filtered_users = all_users

        # Search filter (case-insensitive partial match)
        if search:
            search_lower = search.lower()
            filtered_users = [u for u in filtered_users if search_lower in u['username'].lower()]

        # Sudo filter
        if has_sudo is not None:
            filtered_users = [u for u in filtered_users if u['has_sudo'] == has_sudo]

        # UID range filter
        if uid_min is not None:
            filtered_users = [u for u in filtered_users if u['uid'] >= uid_min]
        if uid_max is not None:
            filtered_users = [u for u in filtered_users if u['uid'] <= uid_max]

        # Apply pagination
        total_count = len(filtered_users)
        paginated_users = filtered_users[skip:skip + limit]

        await log_audit(
            action="list_users",
            username="*",
            user_info=user_info,
            success=True,
            metadata={
                "include_system": include_system,
                "total_count": total_count,
                "returned_count": len(paginated_users),
                "skip": skip,
                "limit": limit,
                "filters": {
                    "search": search,
                    "has_sudo": has_sudo,
                    "uid_min": uid_min,
                    "uid_max": uid_max
                }
            }
        )

        return paginated_users

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to list users: {e}")
        await log_audit(
            action="list_users",
            username="*",
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


@router.post("/", response_model=UserResponse)
async def create_local_user(
    request: CreateUserRequest,
    user_info: dict = Depends(require_admin_role)
):
    """
    Create a new local Linux user.

    **Requires**: Admin role

    **Parameters**:
    - `username`: Username for new user (lowercase, alphanumeric + underscore/hyphen)
    - `full_name`: Full name (GECOS field)
    - `shell`: Login shell (default: /bin/bash)
    - `create_home`: Create home directory (default: true)
    - `groups`: Additional groups to add user to
    - `password`: Initial password (optional, min 12 characters with complexity)

    **Returns**: Created user information
    """
    try:
        # Create user
        created_user = create_user(
            username=request.username,
            full_name=request.full_name,
            shell=request.shell,
            create_home=request.create_home,
            groups=request.groups
        )

        # Set password if provided
        if request.password:
            set_password(request.username, request.password)

        await log_audit(
            action="create_user",
            username=request.username,
            user_info=user_info,
            success=True,
            metadata={
                "full_name": request.full_name,
                "shell": request.shell,
                "create_home": request.create_home,
                "groups": request.groups
            }
        )

        logger.info(f"User created: {request.username} by {user_info.get('email')}")
        return created_user

    except ValidationError as e:
        await log_audit(
            action="create_user",
            username=request.username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))
    except SecurityError as e:
        await log_audit(
            action="create_user",
            username=request.username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=403, detail=str(e))
    except LocalSystemError as e:
        await log_audit(
            action="create_user",
            username=request.username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error creating user: {e}")
        await log_audit(
            action="create_user",
            username=request.username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/statistics")
async def get_user_statistics(
    user_info: dict = Depends(require_admin_role)
):
    """
    Get statistics about local users.

    **NEW FEATURE**: System-wide user statistics endpoint.

    **Requires**: Admin role

    **Returns**: Statistics object with:
    - `total_users`: Total number of non-system users
    - `sudo_users`: Number of users with sudo privileges
    - `system_users`: Number of system users (UID < 1000)
    - `users_by_shell`: Count by shell type
    - `total_home_size_bytes`: Total size of all home directories
    - `total_home_size_gb`: Total size in GB
    - `uid_range`: Min and max UID values
    """
    try:
        stats = get_statistics()

        await log_audit(
            action="get_statistics",
            username="*",
            user_info=user_info,
            success=True,
            metadata=stats
        )

        return stats

    except Exception as e:
        logger.exception(f"Failed to get statistics: {e}")
        await log_audit(
            action="get_statistics",
            username="*",
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/{username}", response_model=UserResponse)
async def get_local_user(
    username: str,
    user_info: dict = Depends(require_admin_role)
):
    """
    Get detailed information about a local user.

    **Requires**: Admin role

    **Parameters**:
    - `username`: Username to query

    **Returns**: User information object
    """
    try:
        user = get_user_info(username)
        return user

    except ValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to get user info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user info: {str(e)}")


@router.delete("/{username}")
async def delete_local_user(
    username: str,
    remove_home: bool = False,
    user_info: dict = Depends(require_admin_role),
    request: Request = None
):
    """
    Delete a local Linux user.

    **Requires**: Admin role

    **WARNING**: This operation cannot be undone!

    **SECURITY**: Prevents admins from deleting their own account.

    **Parameters**:
    - `username`: Username to delete
    - `remove_home`: Also remove home directory (default: false)

    **Returns**: Success message
    """
    # SECURITY FIX: Prevent self-deletion
    # Get current user from session
    current_user = user_info.get('preferred_username') or user_info.get('email')

    if not current_user:
        # Fallback: try to get username from request state
        if hasattr(request.state, 'user_info'):
            current_user = request.state.user_info.get('preferred_username') or request.state.user_info.get('email')

    if current_user and username.lower() == current_user.lower():
        logger.warning(f"User {current_user} attempted to delete their own account")
        await log_audit(
            action="delete_user",
            username=username,
            user_info=user_info,
            success=False,
            error_message="Cannot delete your own user account"
        )
        raise HTTPException(
            status_code=403,
            detail="Cannot delete your own user account. Please use another admin account."
        )

    try:
        delete_user(username, remove_home=remove_home)

        await log_audit(
            action="delete_user",
            username=username,
            user_info=user_info,
            success=True,
            metadata={"remove_home": remove_home}
        )

        logger.warning(f"User deleted: {username} by {user_info.get('email')}")
        return {"success": True, "message": f"User {username} deleted successfully"}

    except ValidationError as e:
        await log_audit(
            action="delete_user",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))
    except SecurityError as e:
        await log_audit(
            action="delete_user",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=403, detail=str(e))
    except LocalSystemError as e:
        await log_audit(
            action="delete_user",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error deleting user: {e}")
        await log_audit(
            action="delete_user",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/{username}/password")
async def set_user_password(
    username: str,
    request: SetPasswordRequest,
    user_info: dict = Depends(require_admin_role)
):
    """
    Set password for a local user.

    **Requires**: Admin role

    **Parameters**:
    - `username`: Username
    - `password`: New password (min 12 characters with uppercase, lowercase, digit, special character)

    **Returns**: Success message
    """
    try:
        set_password(username, request.password)

        await log_audit(
            action="set_password",
            username=username,
            user_info=user_info,
            success=True
        )

        logger.info(f"Password set for user: {username} by {user_info.get('email')}")
        return {"success": True, "message": f"Password set for user {username}"}

    except ValidationError as e:
        await log_audit(
            action="set_password",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))
    except SecurityError as e:
        await log_audit(
            action="set_password",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=403, detail=str(e))
    except LocalSystemError as e:
        await log_audit(
            action="set_password",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error setting password: {e}")
        await log_audit(
            action="set_password",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/{username}/ssh-keys", response_model=List[SSHKeyResponse])
async def get_ssh_keys(
    username: str,
    user_info: dict = Depends(require_admin_role)
):
    """
    List SSH public keys for a user.

    **Requires**: Admin role

    **Parameters**:
    - `username`: Username

    **Returns**: List of SSH key objects
    """
    try:
        keys = list_ssh_keys(username)
        return keys

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to list SSH keys: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list SSH keys: {str(e)}")


@router.post("/{username}/ssh-keys")
async def add_user_ssh_key(
    username: str,
    request: AddSSHKeyRequest,
    user_info: dict = Depends(require_admin_role)
):
    """
    Add SSH public key to user's authorized_keys.

    **Requires**: Admin role

    **Parameters**:
    - `username`: Username
    - `ssh_key`: SSH public key (must be valid format)
    - `key_title`: Optional title/comment for the key

    **Returns**: Key information with fingerprint
    """
    try:
        result = add_ssh_key(username, request.ssh_key, request.key_title)

        await log_audit(
            action="add_ssh_key",
            username=username,
            user_info=user_info,
            success=True,
            metadata={
                "key_fingerprint": result.get("key_fingerprint"),
                "key_title": request.key_title
            }
        )

        logger.info(f"SSH key added for user: {username} by {user_info.get('email')}")
        return result

    except ValidationError as e:
        await log_audit(
            action="add_ssh_key",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))
    except SecurityError as e:
        await log_audit(
            action="add_ssh_key",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=403, detail=str(e))
    except LocalSystemError as e:
        await log_audit(
            action="add_ssh_key",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error adding SSH key: {e}")
        await log_audit(
            action="add_ssh_key",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.delete("/{username}/ssh-keys/{key_fingerprint}")
async def remove_user_ssh_key(
    username: str,
    key_fingerprint: str,
    user_info: dict = Depends(require_admin_role)
):
    """
    Remove SSH public key from user's authorized_keys.

    **Requires**: Admin role

    **Parameters**:
    - `username`: Username
    - `key_fingerprint`: Fingerprint of key to remove

    **Returns**: Success message
    """
    try:
        remove_ssh_key(username, key_fingerprint)

        await log_audit(
            action="remove_ssh_key",
            username=username,
            user_info=user_info,
            success=True,
            metadata={"key_fingerprint": key_fingerprint}
        )

        logger.info(f"SSH key removed for user: {username} by {user_info.get('email')}")
        return {"success": True, "message": f"SSH key removed for user {username}"}

    except ValidationError as e:
        await log_audit(
            action="remove_ssh_key",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))
    except SecurityError as e:
        await log_audit(
            action="remove_ssh_key",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=403, detail=str(e))
    except LocalSystemError as e:
        await log_audit(
            action="remove_ssh_key",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error removing SSH key: {e}")
        await log_audit(
            action="remove_ssh_key",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/{username}/sudo")
async def grant_sudo(
    username: str,
    user_info: dict = Depends(require_admin_role)
):
    """
    Grant sudo permissions to a user.

    **Requires**: Admin role

    **WARNING**: This gives the user full system access via sudo!

    **Parameters**:
    - `username`: Username

    **Returns**: Success message
    """
    try:
        set_sudo_permissions(username, grant=True)

        await log_audit(
            action="sudo_grant",
            username=username,
            user_info=user_info,
            success=True
        )

        logger.warning(f"Sudo granted to user: {username} by {user_info.get('email')}")
        return {"success": True, "message": f"Sudo permissions granted to user {username}"}

    except ValidationError as e:
        await log_audit(
            action="sudo_grant",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))
    except SecurityError as e:
        await log_audit(
            action="sudo_grant",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=403, detail=str(e))
    except LocalSystemError as e:
        await log_audit(
            action="sudo_grant",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error granting sudo: {e}")
        await log_audit(
            action="sudo_grant",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.delete("/{username}/sudo")
async def revoke_sudo(
    username: str,
    user_info: dict = Depends(require_admin_role)
):
    """
    Revoke sudo permissions from a user.

    **Requires**: Admin role

    **Parameters**:
    - `username`: Username

    **Returns**: Success message
    """
    try:
        set_sudo_permissions(username, grant=False)

        await log_audit(
            action="sudo_revoke",
            username=username,
            user_info=user_info,
            success=True
        )

        logger.info(f"Sudo revoked from user: {username} by {user_info.get('email')}")
        return {"success": True, "message": f"Sudo permissions revoked from user {username}"}

    except ValidationError as e:
        await log_audit(
            action="sudo_revoke",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))
    except SecurityError as e:
        await log_audit(
            action="sudo_revoke",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=403, detail=str(e))
    except LocalSystemError as e:
        await log_audit(
            action="sudo_revoke",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error revoking sudo: {e}")
        await log_audit(
            action="sudo_revoke",
            username=username,
            user_info=user_info,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
