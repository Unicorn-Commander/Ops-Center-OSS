"""Audit Log API Endpoints

This module provides REST API endpoints for querying and managing audit logs.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from typing import Optional
from datetime import datetime, timedelta

from audit_logger import audit_logger
from models.audit_log import (
    AuditLogFilter, AuditLogResponse, AuditStats,
    AuditAction, AuditResult
)


# Create router
router = APIRouter(prefix="/api/v1/audit", tags=["Audit Logs"])


# Dependency for admin authentication (placeholder - integrate with your auth)
async def require_admin(request: Request):
    """Require admin role for audit log access

    This should be replaced with your actual authentication logic.
    """
    # TODO: Integrate with actual auth system
    # For now, check for a simple header or session
    # In production, this should verify JWT token and check user role

    # Example implementation:
    # auth_header = request.headers.get("Authorization")
    # if not auth_header:
    #     raise HTTPException(status_code=401, detail="Not authenticated")
    #
    # user = await verify_token(auth_header)
    # if user.role != "admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")

    pass


@router.get("/logs", response_model=AuditLogResponse)
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    username: Optional[str] = Query(None, description="Filter by username"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    result: Optional[str] = Query(None, description="Filter by result (success/failure/error/denied)"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    admin: str = Depends(require_admin)
):
    """Query audit logs with filtering and pagination

    Returns a paginated list of audit log entries based on the provided filters.

    **Required Role:** Admin

    **Query Parameters:**
    - user_id: Filter by user ID
    - username: Filter by username
    - action: Filter by action (e.g., 'auth.login.success')
    - resource_type: Filter by resource type (e.g., 'service', 'model')
    - resource_id: Filter by specific resource ID
    - result: Filter by result (success, failure, error, denied)
    - ip_address: Filter by IP address
    - start_date: Start date in ISO format (YYYY-MM-DDTHH:MM:SS)
    - end_date: End date in ISO format
    - limit: Number of results per page (max 1000)
    - offset: Pagination offset

    **Returns:**
    - total: Total number of matching logs
    - offset: Current offset
    - limit: Current limit
    - logs: Array of audit log entries
    """
    try:
        filter_params = AuditLogFilter(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            ip_address=ip_address,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        response = await audit_logger.query_logs(filter_params)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query audit logs: {str(e)}")


@router.get("/stats", response_model=AuditStats)
async def get_audit_statistics(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    admin: str = Depends(require_admin)
):
    """Get audit statistics for a time period

    Returns comprehensive statistics about audit events, including:
    - Total events
    - Events by action type
    - Events by result
    - Events by user
    - Failed login attempts
    - Security events
    - Suspicious IP addresses

    **Required Role:** Admin

    **Query Parameters:**
    - start_date: Start date in ISO format (defaults to 30 days ago)
    - end_date: End date in ISO format (defaults to now)

    **Returns:**
    - Audit statistics for the specified time period
    """
    try:
        stats = await audit_logger.get_statistics(start_date, end_date)
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit statistics: {str(e)}")


@router.get("/actions", response_model=dict)
async def get_available_actions(admin: str = Depends(require_admin)):
    """Get list of available audit actions

    Returns a categorized list of all available audit actions that can be logged.

    **Required Role:** Admin

    **Returns:**
    - Dictionary of action categories with their actions
    """
    actions_by_category = {
        "Authentication": [
            AuditAction.AUTH_LOGIN_SUCCESS.value,
            AuditAction.AUTH_LOGIN_FAILED.value,
            AuditAction.AUTH_LOGOUT.value,
            AuditAction.AUTH_TOKEN_REFRESH.value,
            AuditAction.AUTH_PASSWORD_CHANGE.value,
            AuditAction.AUTH_PASSWORD_RESET.value,
        ],
        "Service Management": [
            AuditAction.SERVICE_START.value,
            AuditAction.SERVICE_STOP.value,
            AuditAction.SERVICE_RESTART.value,
            AuditAction.SERVICE_CONFIGURE.value,
        ],
        "Model Management": [
            AuditAction.MODEL_DOWNLOAD.value,
            AuditAction.MODEL_DELETE.value,
            AuditAction.MODEL_CONFIGURE.value,
            AuditAction.MODEL_UPDATE.value,
        ],
        "Network Configuration": [
            AuditAction.NETWORK_CONFIGURE.value,
            AuditAction.NETWORK_DNS_UPDATE.value,
            AuditAction.NETWORK_FIREWALL_UPDATE.value,
        ],
        "Backup & Restore": [
            AuditAction.BACKUP_CREATE.value,
            AuditAction.BACKUP_RESTORE.value,
            AuditAction.BACKUP_DELETE.value,
            AuditAction.BACKUP_DOWNLOAD.value,
        ],
        "User Management": [
            AuditAction.USER_CREATE.value,
            AuditAction.USER_UPDATE.value,
            AuditAction.USER_DELETE.value,
            AuditAction.USER_ROLE_CHANGE.value,
            AuditAction.USER_ACTIVATE.value,
            AuditAction.USER_DEACTIVATE.value,
        ],
        "API Key Management": [
            AuditAction.APIKEY_CREATE.value,
            AuditAction.APIKEY_REVOKE.value,
            AuditAction.APIKEY_UPDATE.value,
        ],
        "Security Events": [
            AuditAction.PERMISSION_DENIED.value,
            AuditAction.CSRF_VALIDATION_FAILED.value,
            AuditAction.RATE_LIMIT_EXCEEDED.value,
            AuditAction.INVALID_TOKEN.value,
            AuditAction.SUSPICIOUS_ACTIVITY.value,
        ],
        "Data Access": [
            AuditAction.DATA_VIEW.value,
            AuditAction.DATA_EXPORT.value,
            AuditAction.CONFIG_VIEW.value,
            AuditAction.CONFIG_EXPORT.value,
        ],
        "System Operations": [
            AuditAction.SYSTEM_UPDATE.value,
            AuditAction.SYSTEM_RESTART.value,
            AuditAction.SYSTEM_SHUTDOWN.value,
            AuditAction.SYSTEM_PACKAGE_INSTALL.value,
            AuditAction.SYSTEM_PACKAGE_REMOVE.value,
        ],
        "Billing & Subscription": [
            AuditAction.BILLING_SUBSCRIPTION_CREATE.value,
            AuditAction.BILLING_SUBSCRIPTION_UPDATE.value,
            AuditAction.BILLING_SUBSCRIPTION_CANCEL.value,
            AuditAction.BILLING_PAYMENT_PROCESS.value,
        ]
    }

    return {
        "categories": actions_by_category,
        "all_actions": [action.value for action in AuditAction],
        "results": [result.value for result in AuditResult]
    }


@router.get("/recent", response_model=AuditLogResponse)
async def get_recent_logs(
    limit: int = Query(50, ge=1, le=500, description="Number of recent logs"),
    admin: str = Depends(require_admin)
):
    """Get most recent audit logs

    Returns the most recent audit log entries.

    **Required Role:** Admin

    **Query Parameters:**
    - limit: Number of recent logs to return (max 500)

    **Returns:**
    - Recent audit log entries
    """
    try:
        filter_params = AuditLogFilter(limit=limit, offset=0)
        response = await audit_logger.query_logs(filter_params)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent logs: {str(e)}")


@router.get("/security", response_model=AuditLogResponse)
async def get_security_events(
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    admin: str = Depends(require_admin)
):
    """Get security-related audit events

    Returns audit logs for security-related events including:
    - Failed login attempts
    - Permission denials
    - CSRF validation failures
    - Invalid tokens
    - Rate limit violations
    - Suspicious activities

    **Required Role:** Admin

    **Query Parameters:**
    - limit: Number of results per page (max 1000)
    - offset: Pagination offset

    **Returns:**
    - Security-related audit log entries
    """
    try:
        # Get failed logins
        failed_logins = AuditLogFilter(
            action=AuditAction.AUTH_LOGIN_FAILED.value,
            limit=limit,
            offset=offset
        )

        # For a comprehensive security view, you'd combine multiple queries
        # This is a simplified version
        response = await audit_logger.query_logs(failed_logins)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get security events: {str(e)}")


@router.delete("/cleanup")
async def cleanup_old_logs(
    days_to_keep: int = Query(90, ge=30, le=365, description="Days of logs to keep"),
    admin: str = Depends(require_admin)
):
    """Clean up old audit logs

    Deletes audit logs older than the specified number of days.
    Minimum retention is 30 days, maximum is 365 days.

    **Required Role:** Admin

    **Query Parameters:**
    - days_to_keep: Number of days of logs to keep (30-365)

    **Returns:**
    - Number of logs deleted
    """
    try:
        deleted_count = await audit_logger.cleanup_old_logs(days_to_keep)

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "days_kept": days_to_keep,
            "message": f"Deleted {deleted_count} audit logs older than {days_to_keep} days"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup logs: {str(e)}")
