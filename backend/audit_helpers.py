"""Audit Logging Helper Functions

Convenience functions and decorators for audit logging.
"""

import functools
from typing import Optional, Callable, Any
from fastapi import Request

from audit_logger import audit_logger
from models.audit_log import AuditAction, AuditResult


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies

    Args:
        request: FastAPI request object

    Returns:
        Client IP address
    """
    # Check X-Forwarded-For header first (for proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain
        return forwarded.split(",")[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct client
    if request.client:
        return request.client.host

    return "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request

    Args:
        request: FastAPI request object

    Returns:
        User agent string
    """
    return request.headers.get("User-Agent", "unknown")


def get_session_id(request: Request) -> Optional[str]:
    """Extract session ID from request

    Args:
        request: FastAPI request object

    Returns:
        Session ID if available
    """
    # Try to get from cookies
    session_id = request.cookies.get("session_id")
    if session_id:
        return session_id

    # Try to get from headers
    session_id = request.headers.get("X-Session-ID")
    if session_id:
        return session_id

    return None


async def log_auth_success(
    request: Request,
    user_id: str,
    username: str,
    metadata: Optional[dict] = None
):
    """Log successful authentication

    Args:
        request: FastAPI request
        user_id: User ID
        username: Username
        metadata: Additional metadata
    """
    await audit_logger.log(
        action=AuditAction.AUTH_LOGIN_SUCCESS.value,
        result=AuditResult.SUCCESS.value,
        user_id=user_id,
        username=username,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        session_id=get_session_id(request),
        metadata=metadata or {}
    )


async def log_auth_failure(
    request: Request,
    username: str,
    reason: str,
    metadata: Optional[dict] = None
):
    """Log failed authentication attempt

    Args:
        request: FastAPI request
        username: Attempted username
        reason: Failure reason
        metadata: Additional metadata
    """
    await audit_logger.log(
        action=AuditAction.AUTH_LOGIN_FAILED.value,
        result=AuditResult.FAILURE.value,
        username=username,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        error_message=reason,
        metadata=metadata or {}
    )


async def log_logout(
    request: Request,
    user_id: str,
    username: str,
    metadata: Optional[dict] = None
):
    """Log user logout

    Args:
        request: FastAPI request
        user_id: User ID
        username: Username
        metadata: Additional metadata
    """
    await audit_logger.log(
        action=AuditAction.AUTH_LOGOUT.value,
        result=AuditResult.SUCCESS.value,
        user_id=user_id,
        username=username,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        session_id=get_session_id(request),
        metadata=metadata or {}
    )


async def log_permission_denied(
    request: Request,
    user_id: Optional[str],
    username: Optional[str],
    resource_type: str,
    resource_id: Optional[str] = None,
    required_permission: Optional[str] = None
):
    """Log permission denied event

    Args:
        request: FastAPI request
        user_id: User ID
        username: Username
        resource_type: Type of resource
        resource_id: Resource ID
        required_permission: Required permission that was missing
    """
    await audit_logger.log(
        action=AuditAction.PERMISSION_DENIED.value,
        result=AuditResult.DENIED.value,
        user_id=user_id,
        username=username,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        resource_type=resource_type,
        resource_id=resource_id,
        metadata={
            "required_permission": required_permission
        }
    )


async def log_service_operation(
    request: Request,
    user_id: str,
    username: str,
    operation: str,
    service_name: str,
    success: bool,
    error_message: Optional[str] = None
):
    """Log service start/stop/restart operation

    Args:
        request: FastAPI request
        user_id: User ID
        username: Username
        operation: Operation type ('start', 'stop', 'restart')
        service_name: Name of the service
        success: Whether operation succeeded
        error_message: Error message if failed
    """
    action_map = {
        "start": AuditAction.SERVICE_START.value,
        "stop": AuditAction.SERVICE_STOP.value,
        "restart": AuditAction.SERVICE_RESTART.value
    }

    await audit_logger.log(
        action=action_map.get(operation, AuditAction.SERVICE_CONFIGURE.value),
        result=AuditResult.SUCCESS.value if success else AuditResult.FAILURE.value,
        user_id=user_id,
        username=username,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        resource_type="service",
        resource_id=service_name,
        error_message=error_message,
        metadata={"operation": operation}
    )


async def log_model_operation(
    request: Request,
    user_id: str,
    username: str,
    operation: str,
    model_name: str,
    success: bool,
    error_message: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Log model download/delete/configure operation

    Args:
        request: FastAPI request
        user_id: User ID
        username: Username
        operation: Operation type ('download', 'delete', 'configure')
        model_name: Name of the model
        success: Whether operation succeeded
        error_message: Error message if failed
        metadata: Additional metadata
    """
    action_map = {
        "download": AuditAction.MODEL_DOWNLOAD.value,
        "delete": AuditAction.MODEL_DELETE.value,
        "configure": AuditAction.MODEL_CONFIGURE.value,
        "update": AuditAction.MODEL_UPDATE.value
    }

    await audit_logger.log(
        action=action_map.get(operation, AuditAction.MODEL_CONFIGURE.value),
        result=AuditResult.SUCCESS.value if success else AuditResult.FAILURE.value,
        user_id=user_id,
        username=username,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        resource_type="model",
        resource_id=model_name,
        error_message=error_message,
        metadata=metadata or {"operation": operation}
    )


async def log_user_management(
    request: Request,
    admin_user_id: str,
    admin_username: str,
    operation: str,
    target_user_id: str,
    target_username: str,
    success: bool,
    error_message: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Log user management operation

    Args:
        request: FastAPI request
        admin_user_id: Admin user ID
        admin_username: Admin username
        operation: Operation type ('create', 'update', 'delete', 'role_change')
        target_user_id: Target user ID
        target_username: Target username
        success: Whether operation succeeded
        error_message: Error message if failed
        metadata: Additional metadata
    """
    action_map = {
        "create": AuditAction.USER_CREATE.value,
        "update": AuditAction.USER_UPDATE.value,
        "delete": AuditAction.USER_DELETE.value,
        "role_change": AuditAction.USER_ROLE_CHANGE.value,
        "activate": AuditAction.USER_ACTIVATE.value,
        "deactivate": AuditAction.USER_DEACTIVATE.value
    }

    meta = metadata or {}
    meta.update({
        "target_user_id": target_user_id,
        "target_username": target_username
    })

    await audit_logger.log(
        action=action_map.get(operation, AuditAction.USER_UPDATE.value),
        result=AuditResult.SUCCESS.value if success else AuditResult.FAILURE.value,
        user_id=admin_user_id,
        username=admin_username,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        resource_type="user",
        resource_id=target_user_id,
        error_message=error_message,
        metadata=meta
    )


async def log_data_access(
    request: Request,
    user_id: str,
    username: str,
    data_type: str,
    operation: str = "view",
    resource_id: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Log data access/export

    Args:
        request: FastAPI request
        user_id: User ID
        username: Username
        data_type: Type of data accessed
        operation: Operation type ('view', 'export')
        resource_id: Resource ID if applicable
        metadata: Additional metadata
    """
    action_map = {
        "view": AuditAction.DATA_VIEW.value,
        "export": AuditAction.DATA_EXPORT.value,
        "config_view": AuditAction.CONFIG_VIEW.value,
        "config_export": AuditAction.CONFIG_EXPORT.value
    }

    await audit_logger.log(
        action=action_map.get(operation, AuditAction.DATA_VIEW.value),
        result=AuditResult.SUCCESS.value,
        user_id=user_id,
        username=username,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        resource_type=data_type,
        resource_id=resource_id,
        metadata=metadata or {}
    )


def audit_operation(
    action: str,
    resource_type: Optional[str] = None,
    get_resource_id: Optional[Callable] = None
):
    """Decorator for auditing operations

    Example:
        @audit_operation(
            action=AuditAction.SERVICE_START.value,
            resource_type="service",
            get_resource_id=lambda kwargs: kwargs.get("service_name")
        )
        async def start_service(request: Request, service_name: str):
            # ... implementation
            pass

    Args:
        action: Audit action
        resource_type: Type of resource
        get_resource_id: Function to extract resource ID from kwargs
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            user_id = None
            username = None

            # Extract request and user info from args/kwargs
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if "request" in kwargs:
                request = kwargs["request"]

            # Try to get user from request state
            if request and hasattr(request.state, "user"):
                user = request.state.user
                user_id = getattr(user, "id", None)
                username = getattr(user, "username", None)

            # Extract resource ID if function provided
            resource_id = None
            if get_resource_id:
                try:
                    resource_id = get_resource_id(kwargs)
                except Exception:
                    pass

            try:
                # Execute the function
                result = await func(*args, **kwargs)

                # Log success
                if request:
                    await audit_logger.log(
                        action=action,
                        result=AuditResult.SUCCESS.value,
                        user_id=user_id,
                        username=username,
                        ip_address=get_client_ip(request) if request else None,
                        user_agent=get_user_agent(request) if request else None,
                        resource_type=resource_type,
                        resource_id=resource_id
                    )

                return result

            except Exception as e:
                # Log failure
                if request:
                    await audit_logger.log(
                        action=action,
                        result=AuditResult.ERROR.value,
                        user_id=user_id,
                        username=username,
                        ip_address=get_client_ip(request) if request else None,
                        user_agent=get_user_agent(request) if request else None,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        error_message=str(e)
                    )
                raise

        return wrapper
    return decorator
