"""
System Audit Log API Router

Provides system-wide audit logging for security, compliance, and debugging.

Author: Ops-Center AI
Created: January 31, 2026

Endpoints:
    - GET  /api/v1/admin/audit-log          - Get audit entries with filtering
    - GET  /api/v1/admin/audit-log/export   - Export audit log to CSV
    - GET  /api/v1/admin/audit-log/stats    - Get audit statistics
    - POST /api/v1/audit/log                - Internal endpoint to create entries
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import json
import io
import csv
import sys
import os

if '/app' not in sys.path:
    sys.path.insert(0, '/app')

from database.connection import get_db_pool

logger = logging.getLogger(__name__)

# Constants
DEFAULT_LIMIT = 50
MAX_LIMIT = 500
VALID_EVENT_TYPES = ['auth', 'billing', 'service', 'admin', 'api', 'user', 'system', 'security']
VALID_SEVERITIES = ['info', 'warning', 'error', 'critical']


# =============================================================================
# Pydantic Models
# =============================================================================

class AuditLogEntry(BaseModel):
    """Single audit log entry"""
    id: int
    event_type: str
    severity: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    description: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class AuditLogCreateRequest(BaseModel):
    """Request to create audit entry"""
    event_type: str = Field(..., description="Event category")
    action: str = Field(..., min_length=1, max_length=255)
    severity: str = Field(default="info")
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    description: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v):
        if v.lower() not in VALID_EVENT_TYPES:
            raise ValueError(f"event_type must be one of: {', '.join(VALID_EVENT_TYPES)}")
        return v.lower()

    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        if v.lower() not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of: {', '.join(VALID_SEVERITIES)}")
        return v.lower()


class AuditLogListResponse(BaseModel):
    """Paginated audit log list"""
    entries: List[AuditLogEntry]
    total: int
    limit: int
    offset: int
    has_more: bool


class AuditLogStats(BaseModel):
    """Audit statistics"""
    total_entries: int
    entries_by_type: Dict[str, int]
    entries_by_severity: Dict[str, int]
    entries_last_24h: int
    entries_last_7d: int
    entries_last_30d: int
    top_actions: List[Dict[str, Any]]
    top_users: List[Dict[str, Any]]
    error_rate_24h: float
    critical_events_24h: int
    calculated_at: datetime


# =============================================================================
# Routers
# =============================================================================

admin_router = APIRouter(prefix="/api/v1/admin/audit-log", tags=["Admin - Audit Log"])
internal_router = APIRouter(prefix="/api/v1/audit", tags=["Audit Log - Internal"])


# =============================================================================
# Authentication
# =============================================================================

async def get_current_user(request: Request) -> dict:
    """Verify user is authenticated via Redis session"""
    from redis_session import RedisSessionManager

    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    sessions = RedisSessionManager(host=redis_host, port=redis_port)

    if session_token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    user = sessions[session_token].get("user", {})
    if not user:
        raise HTTPException(status_code=401, detail="User not found in session")
    return user


async def require_admin(request: Request) -> dict:
    """Verify user has admin role"""
    user = await get_current_user(request)
    if not user.get("is_admin") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# =============================================================================
# Helper Function (exported for other routers)
# =============================================================================

async def log_audit_event(
    event_type: str,
    action: str,
    user_id: str = None,
    user_email: str = None,
    description: str = None,
    resource_type: str = None,
    resource_id: str = None,
    ip_address: str = None,
    user_agent: str = None,
    severity: str = "info",
    metadata: dict = None
) -> Optional[int]:
    """
    Log an audit event to the database.

    Args:
        event_type: Category (auth, billing, service, admin, api, user, system, security)
        action: Brief action (e.g., 'user.login', 'subscription.upgrade')
        user_id: Keycloak user ID (optional for system events)
        user_email: User email for quick reference
        description: Detailed description
        resource_type: Type of affected resource
        resource_id: ID of the affected resource
        ip_address: Client IP address
        user_agent: Browser/client user agent
        severity: Level (info, warning, error, critical)
        metadata: Additional context as dict

    Returns:
        int: Created entry ID, or None if failed

    Example:
        await log_audit_event(
            event_type="auth",
            action="user.login",
            user_id="user-123",
            user_email="user@example.com",
            ip_address="192.168.1.1",
            metadata={"method": "password"}
        )
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval(
                """
                INSERT INTO audit_log (
                    event_type, severity, user_id, user_email, action, description,
                    resource_type, resource_id, ip_address, user_agent, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
                """,
                event_type.lower(), severity.lower(), user_id, user_email, action,
                description, resource_type, resource_id, ip_address, user_agent,
                json.dumps(metadata or {})
            )
            logger.debug(f"Audit log created: id={result}, action={action}")
            return result
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        return None


# =============================================================================
# Query Builder Helper
# =============================================================================

def build_filter_query(
    event_type: str = None,
    user_id: str = None,
    severity: str = None,
    date_from: datetime = None,
    date_to: datetime = None,
    search: str = None,
    resource_type: str = None,
    resource_id: str = None
) -> tuple[str, list]:
    """Build WHERE clause and params for audit log queries"""
    conditions = []
    params = []
    param_count = 0

    if event_type:
        param_count += 1
        conditions.append(f"event_type = ${param_count}")
        params.append(event_type.lower())

    if user_id:
        param_count += 1
        conditions.append(f"user_id = ${param_count}")
        params.append(user_id)

    if severity:
        param_count += 1
        conditions.append(f"severity = ${param_count}")
        params.append(severity.lower())

    if date_from:
        param_count += 1
        conditions.append(f"created_at >= ${param_count}")
        params.append(date_from)

    if date_to:
        param_count += 1
        conditions.append(f"created_at <= ${param_count}")
        params.append(date_to)

    if resource_type:
        param_count += 1
        conditions.append(f"resource_type = ${param_count}")
        params.append(resource_type)

    if resource_id:
        param_count += 1
        conditions.append(f"resource_id = ${param_count}")
        params.append(resource_id)

    if search:
        param_count += 1
        conditions.append(f"to_tsvector('english', action || ' ' || COALESCE(description, '')) @@ plainto_tsquery('english', ${param_count})")
        params.append(search)

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    return where_clause, params, param_count


# =============================================================================
# Admin Endpoints
# =============================================================================

@admin_router.get("", response_model=AuditLogListResponse)
async def get_audit_log(
    admin: dict = Depends(require_admin),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    date_from: Optional[datetime] = Query(None, description="Filter from date (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="Filter to date (ISO 8601)"),
    search: Optional[str] = Query(None, min_length=2, description="Full-text search"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0)
):
    """Get audit log entries with filtering and pagination. Requires admin role."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            where_clause, params, param_count = build_filter_query(
                event_type, user_id, severity, date_from, date_to, search, resource_type, resource_id
            )

            # Count total
            total = await conn.fetchval(f"SELECT COUNT(*) FROM audit_log WHERE {where_clause}", *params)

            # Get entries
            query = f"""
                SELECT id, event_type, severity, user_id, user_email, action, description,
                       resource_type, resource_id, ip_address, user_agent, metadata, created_at
                FROM audit_log WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            params.extend([limit, offset])
            rows = await conn.fetch(query, *params)

            entries = []
            for row in rows:
                entry = dict(row)
                if entry.get('metadata') and isinstance(entry['metadata'], str):
                    entry['metadata'] = json.loads(entry['metadata'])
                entries.append(AuditLogEntry(**entry))

            return AuditLogListResponse(
                entries=entries, total=total, limit=limit, offset=offset,
                has_more=(offset + limit) < total
            )
    except Exception as e:
        logger.error(f"Failed to fetch audit log: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@admin_router.get("/export")
async def export_audit_log(
    admin: dict = Depends(require_admin),
    event_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None)
):
    """Export audit log to CSV. Requires admin role."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            where_clause, params, _ = build_filter_query(
                event_type, user_id, severity, date_from, date_to, search
            )

            rows = await conn.fetch(f"""
                SELECT id, event_type, severity, user_id, user_email, action, description,
                       resource_type, resource_id, ip_address, user_agent, metadata, created_at
                FROM audit_log WHERE {where_clause}
                ORDER BY created_at DESC LIMIT 10000
            """, *params)

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                'ID', 'Event Type', 'Severity', 'User ID', 'User Email', 'Action',
                'Description', 'Resource Type', 'Resource ID', 'IP Address',
                'User Agent', 'Metadata', 'Created At'
            ])

            for row in rows:
                writer.writerow([
                    row['id'], row['event_type'], row['severity'],
                    row['user_id'] or '', row['user_email'] or '', row['action'],
                    row['description'] or '', row['resource_type'] or '', row['resource_id'] or '',
                    row['ip_address'] or '', row['user_agent'] or '',
                    json.dumps(row['metadata']) if row['metadata'] else '',
                    row['created_at'].isoformat() if row['created_at'] else ''
                ])

            filename = f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    except Exception as e:
        logger.error(f"Failed to export audit log: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@admin_router.get("/stats", response_model=AuditLogStats)
async def get_audit_stats(admin: dict = Depends(require_admin)):
    """Get audit log statistics. Requires admin role."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            now = datetime.now()

            # Total and breakdown queries
            total = await conn.fetchval("SELECT COUNT(*) FROM audit_log")

            type_rows = await conn.fetch(
                "SELECT event_type, COUNT(*) as count FROM audit_log GROUP BY event_type"
            )
            entries_by_type = {r['event_type']: r['count'] for r in type_rows}

            severity_rows = await conn.fetch(
                "SELECT severity, COUNT(*) as count FROM audit_log GROUP BY severity"
            )
            entries_by_severity = {r['severity']: r['count'] for r in severity_rows}

            # Time-based counts
            entries_24h = await conn.fetchval(
                "SELECT COUNT(*) FROM audit_log WHERE created_at >= $1",
                now - timedelta(hours=24)
            )
            entries_7d = await conn.fetchval(
                "SELECT COUNT(*) FROM audit_log WHERE created_at >= $1",
                now - timedelta(days=7)
            )
            entries_30d = await conn.fetchval(
                "SELECT COUNT(*) FROM audit_log WHERE created_at >= $1",
                now - timedelta(days=30)
            )

            # Top actions (last 7 days)
            action_rows = await conn.fetch("""
                SELECT action, COUNT(*) as count FROM audit_log
                WHERE created_at >= $1 GROUP BY action ORDER BY count DESC LIMIT 10
            """, now - timedelta(days=7))
            top_actions = [{"action": r['action'], "count": r['count']} for r in action_rows]

            # Top users (last 7 days)
            user_rows = await conn.fetch("""
                SELECT user_id, user_email, COUNT(*) as count FROM audit_log
                WHERE user_id IS NOT NULL AND created_at >= $1
                GROUP BY user_id, user_email ORDER BY count DESC LIMIT 10
            """, now - timedelta(days=7))
            top_users = [
                {"user_id": r['user_id'], "user_email": r['user_email'], "count": r['count']}
                for r in user_rows
            ]

            # Error metrics
            error_count_24h = await conn.fetchval(
                "SELECT COUNT(*) FROM audit_log WHERE severity IN ('error', 'critical') AND created_at >= $1",
                now - timedelta(hours=24)
            )
            error_rate_24h = (error_count_24h / entries_24h * 100) if entries_24h > 0 else 0

            critical_24h = await conn.fetchval(
                "SELECT COUNT(*) FROM audit_log WHERE severity = 'critical' AND created_at >= $1",
                now - timedelta(hours=24)
            )

            return AuditLogStats(
                total_entries=total,
                entries_by_type=entries_by_type,
                entries_by_severity=entries_by_severity,
                entries_last_24h=entries_24h,
                entries_last_7d=entries_7d,
                entries_last_30d=entries_30d,
                top_actions=top_actions,
                top_users=top_users,
                error_rate_24h=round(error_rate_24h, 2),
                critical_events_24h=critical_24h,
                calculated_at=now
            )
    except Exception as e:
        logger.error(f"Failed to get audit stats: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# =============================================================================
# Internal Endpoint (No Auth)
# =============================================================================

@internal_router.post("/log")
async def create_audit_log(entry: AuditLogCreateRequest, request: Request):
    """
    Create audit log entry. Internal endpoint - no authentication required.
    For service-to-service calls. Restrict access via network policies.
    """
    try:
        ip = entry.ip_address or (request.client.host if request.client else None)
        ua = entry.user_agent or request.headers.get("user-agent")

        entry_id = await log_audit_event(
            event_type=entry.event_type,
            action=entry.action,
            severity=entry.severity,
            user_id=entry.user_id,
            user_email=entry.user_email,
            description=entry.description,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            ip_address=ip,
            user_agent=ua,
            metadata=entry.metadata
        )

        if entry_id:
            return {"success": True, "id": entry_id, "message": "Audit log entry created"}
        raise HTTPException(status_code=500, detail="Failed to create audit log entry")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# =============================================================================
# Exports
# =============================================================================

__all__ = ["admin_router", "internal_router", "log_audit_event"]
