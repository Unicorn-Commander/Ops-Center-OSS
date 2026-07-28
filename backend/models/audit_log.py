"""Audit Log Models

This module defines the data models for audit logging functionality.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AuditAction(str, Enum):
    """Enumeration of audit-able actions"""
    # Authentication
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILED = "auth.login.failed"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_REFRESH = "auth.token.refresh"
    AUTH_PASSWORD_CHANGE = "auth.password.change"
    AUTH_PASSWORD_RESET = "auth.password.reset"

    # Service Management
    SERVICE_START = "service.start"
    SERVICE_STOP = "service.stop"
    SERVICE_RESTART = "service.restart"
    SERVICE_CONFIGURE = "service.configure"

    # Model Management
    MODEL_DOWNLOAD = "model.download"
    MODEL_DELETE = "model.delete"
    MODEL_CONFIGURE = "model.configure"
    MODEL_UPDATE = "model.update"

    # Network Configuration
    NETWORK_CONFIGURE = "network.configure"
    NETWORK_DNS_UPDATE = "network.dns.update"
    NETWORK_FIREWALL_UPDATE = "network.firewall.update"

    # Backup & Restore
    BACKUP_CREATE = "backup.create"
    BACKUP_RESTORE = "backup.restore"
    BACKUP_DELETE = "backup.delete"
    BACKUP_DOWNLOAD = "backup.download"

    # User Management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ROLE_CHANGE = "user.role.change"
    USER_ACTIVATE = "user.activate"
    USER_DEACTIVATE = "user.deactivate"

    # API Key Management
    APIKEY_CREATE = "apikey.create"
    APIKEY_REVOKE = "apikey.revoke"
    APIKEY_UPDATE = "apikey.update"

    # Security Events
    PERMISSION_DENIED = "security.permission.denied"
    CSRF_VALIDATION_FAILED = "security.csrf.failed"
    RATE_LIMIT_EXCEEDED = "security.ratelimit.exceeded"
    INVALID_TOKEN = "security.token.invalid"
    SUSPICIOUS_ACTIVITY = "security.suspicious.activity"

    # Data Access
    DATA_VIEW = "data.view"
    DATA_EXPORT = "data.export"
    CONFIG_VIEW = "config.view"
    CONFIG_EXPORT = "config.export"

    # System Operations
    SYSTEM_UPDATE = "system.update"
    SYSTEM_RESTART = "system.restart"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_PACKAGE_INSTALL = "system.package.install"
    SYSTEM_PACKAGE_REMOVE = "system.package.remove"

    # Billing & Subscription
    BILLING_SUBSCRIPTION_CREATE = "billing.subscription.create"
    BILLING_SUBSCRIPTION_UPDATE = "billing.subscription.update"
    BILLING_SUBSCRIPTION_CANCEL = "billing.subscription.cancel"
    BILLING_PAYMENT_PROCESS = "billing.payment.process"


class AuditResult(str, Enum):
    """Enumeration of audit event results"""
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    DENIED = "denied"


class AuditLog(BaseModel):
    """Audit log entry model"""
    id: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    result: str
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    session_id: Optional[str] = None

    class Config:
        use_enum_values = True


class AuditLogCreate(BaseModel):
    """Model for creating audit log entries"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    result: str
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

    @validator('action')
    def validate_action(cls, v):
        """Ensure action is a valid audit action"""
        valid_actions = [action.value for action in AuditAction]
        if v not in valid_actions:
            # Allow custom actions but log a warning
            pass
        return v

    @validator('result')
    def validate_result(cls, v):
        """Ensure result is a valid audit result"""
        valid_results = [result.value for result in AuditResult]
        if v not in valid_results:
            raise ValueError(f"Invalid result: {v}. Must be one of {valid_results}")
        return v


class AuditLogFilter(BaseModel):
    """Model for filtering audit logs"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    result: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    ip_address: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        """Validate ISO date format"""
        if v:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError("Date must be in ISO format (YYYY-MM-DDTHH:MM:SS)")
        return v


class AuditLogResponse(BaseModel):
    """Response model for audit log queries"""
    total: int
    offset: int
    limit: int
    logs: List[AuditLog]


class AuditStats(BaseModel):
    """Audit statistics model"""
    total_events: int
    events_by_action: Dict[str, int]
    events_by_result: Dict[str, int]
    events_by_user: Dict[str, int]
    failed_logins: int
    security_events: int
    recent_suspicious_ips: List[str]
    period_start: str
    period_end: str
