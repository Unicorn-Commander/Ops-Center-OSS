"""
Alerts Management API Router

Provides REST endpoints for managing alerts and alert rules with Prometheus integration.
Supports:
- Listing active and historical alerts
- Alert rule configuration (thresholds, intervals)
- Alert acknowledgment workflow
- Prometheus API integration for real-time metrics

Author: Ops-Center Backend Team
Created: 2026-01-31
"""

from fastapi import APIRouter, HTTPException, Request, Query, Depends
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import logging
import os
import sys
import httpx

# Import database connection
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db_pool

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/monitoring",
    tags=["alerts"],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
        500: {"description": "Internal server error"},
        503: {"description": "Prometheus not available"},
    },
)

# Configuration
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
PROMETHEUS_TIMEOUT = int(os.getenv("PROMETHEUS_TIMEOUT", "10"))


# =============================================================================
# Enums
# =============================================================================

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status values"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertSource(str, Enum):
    """Alert source identifiers"""
    PROMETHEUS = "prometheus"
    GRAFANA = "grafana"
    SYSTEM = "system"
    MANUAL = "manual"


class ComparisonOperator(str, Enum):
    """Comparison operators for thresholds"""
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    EQ = "=="
    NE = "!="


# =============================================================================
# Authentication Dependencies
# =============================================================================

async def get_current_user(request: Request):
    """Verify user is authenticated (uses Redis session manager)"""
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    from redis_session import RedisSessionManager

    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    sessions = RedisSessionManager(host=redis_host, port=redis_port)

    if session_token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    session_data = sessions[session_token]
    user = session_data.get("user", {})

    if not user:
        raise HTTPException(status_code=401, detail="User not found in session")

    return user


async def require_admin(request: Request):
    """Verify user is authenticated and has admin role"""
    user = await get_current_user(request)

    if not user.get("is_admin") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


# =============================================================================
# Request/Response Models
# =============================================================================

class AlertRuleBase(BaseModel):
    """Base model for alert rules"""
    name: str = Field(..., min_length=1, max_length=100, description="Rule name")
    metric: str = Field(..., min_length=1, max_length=100, description="Metric identifier")
    description: Optional[str] = Field(None, max_length=500, description="Rule description")
    warning_threshold: Optional[float] = Field(None, description="Warning threshold value")
    critical_threshold: Optional[float] = Field(None, description="Critical threshold value")
    comparison_operator: ComparisonOperator = Field(
        ComparisonOperator.GT, description="Comparison operator for threshold"
    )
    unit: Optional[str] = Field(None, max_length=50, description="Metric unit (e.g., percent, ms)")
    enabled: bool = Field(True, description="Whether the rule is active")
    check_interval_seconds: int = Field(60, ge=10, le=86400, description="Check interval in seconds")
    notification_channels: List[str] = Field(default=["email"], description="Notification channels")


class AlertRuleCreate(AlertRuleBase):
    """Model for creating a new alert rule"""
    pass


class AlertRuleUpdate(BaseModel):
    """Model for updating an existing alert rule"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    metric: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    comparison_operator: Optional[ComparisonOperator] = None
    unit: Optional[str] = Field(None, max_length=50)
    enabled: Optional[bool] = None
    check_interval_seconds: Optional[int] = Field(None, ge=10, le=86400)
    notification_channels: Optional[List[str]] = None


class AlertRuleResponse(AlertRuleBase):
    """Response model for alert rules"""
    id: int
    created_at: datetime
    updated_at: datetime


class AlertResponse(BaseModel):
    """Response model for alerts"""
    id: int
    rule_id: Optional[int] = None
    severity: AlertSeverity
    name: str
    message: Optional[str] = None
    source: AlertSource
    labels: Dict[str, Any] = Field(default_factory=dict)
    value: Optional[float] = None
    status: AlertStatus
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    acknowledge_note: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_note: Optional[str] = None
    # Joined from rule
    metric: Optional[str] = None
    unit: Optional[str] = None


class AcknowledgeAlertRequest(BaseModel):
    """Request model for acknowledging an alert"""
    note: Optional[str] = Field(None, max_length=500, description="Acknowledgment note")


class AlertStatistics(BaseModel):
    """Alert statistics summary"""
    active_count: int
    acknowledged_count: int
    resolved_24h_count: int
    critical_active: int
    warning_active: int
    info_active: int
    total_24h: int
    total_7d: int


class AlertsListResponse(BaseModel):
    """Response model for alerts list"""
    alerts: List[AlertResponse]
    total: int
    page: int
    page_size: int
    statistics: Optional[AlertStatistics] = None


class AlertRulesListResponse(BaseModel):
    """Response model for alert rules list"""
    rules: List[AlertRuleResponse]
    total: int


class PrometheusAlertResponse(BaseModel):
    """Prometheus alert format"""
    alertname: str
    state: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    activeAt: Optional[str] = None
    value: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================

async def query_prometheus(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """
    Query Prometheus API with error handling.

    Args:
        endpoint: Prometheus API endpoint (e.g., '/api/v1/alerts')
        params: Optional query parameters

    Returns:
        JSON response from Prometheus or None if unavailable
    """
    try:
        async with httpx.AsyncClient(timeout=PROMETHEUS_TIMEOUT) as client:
            url = f"{PROMETHEUS_URL}{endpoint}"
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.warning(f"Prometheus request error: {e}")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(f"Prometheus HTTP error: {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error querying Prometheus: {e}")
        return None


async def fetch_prometheus_alerts() -> List[Dict]:
    """
    Fetch active alerts from Prometheus.

    Returns:
        List of Prometheus alerts or empty list if unavailable
    """
    result = await query_prometheus("/api/v1/alerts")
    if result and result.get("status") == "success":
        alerts = result.get("data", {}).get("alerts", [])
        return alerts
    return []


def map_prometheus_severity(labels: Dict[str, str]) -> AlertSeverity:
    """Map Prometheus alert labels to severity level"""
    severity = labels.get("severity", "warning").lower()
    if severity in ("critical", "error", "fatal"):
        return AlertSeverity.CRITICAL
    elif severity in ("warning", "warn"):
        return AlertSeverity.WARNING
    return AlertSeverity.INFO


async def sync_prometheus_alerts(pool) -> int:
    """
    Sync alerts from Prometheus into the database.

    Args:
        pool: Database connection pool

    Returns:
        Number of alerts synced
    """
    prometheus_alerts = await fetch_prometheus_alerts()
    if not prometheus_alerts:
        return 0

    synced = 0
    async with pool.acquire() as conn:
        for alert in prometheus_alerts:
            labels = alert.get("labels", {})
            annotations = alert.get("annotations", {})
            alertname = labels.get("alertname", "Unknown Alert")

            # Check if alert already exists (by name and active status)
            existing = await conn.fetchrow(
                """
                SELECT id FROM alerts
                WHERE name = $1 AND source = 'prometheus' AND status = 'active'
                """,
                alertname
            )

            if not existing:
                severity = map_prometheus_severity(labels)
                message = annotations.get("summary") or annotations.get("description") or ""

                await conn.execute(
                    """
                    INSERT INTO alerts (name, severity, message, source, labels, status)
                    VALUES ($1, $2, $3, $4, $5, 'active')
                    """,
                    alertname,
                    severity.value,
                    message,
                    "prometheus",
                    labels
                )
                synced += 1

    return synced


# =============================================================================
# API Endpoints
# =============================================================================

@router.get(
    "/alerts",
    response_model=AlertsListResponse,
    summary="List all alerts",
    description="Get a paginated list of alerts with optional filtering by status, severity, and source.",
)
async def list_alerts(
    status: Optional[AlertStatus] = Query(None, description="Filter by status"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    source: Optional[AlertSource] = Query(None, description="Filter by source"),
    include_resolved: bool = Query(False, description="Include resolved alerts"),
    hours: int = Query(24, ge=1, le=720, description="Hours of history to include"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    sync_prometheus: bool = Query(True, description="Sync alerts from Prometheus first"),
    current_user: dict = Depends(get_current_user)
):
    """
    List all alerts with filtering and pagination.

    Optionally syncs with Prometheus before returning results.
    """
    try:
        pool = await get_db_pool()

        # Optionally sync Prometheus alerts first
        if sync_prometheus:
            synced = await sync_prometheus_alerts(pool)
            if synced > 0:
                logger.info(f"Synced {synced} alerts from Prometheus")

        async with pool.acquire() as conn:
            # Build query conditions
            conditions = []
            params = []
            param_idx = 1

            if status:
                conditions.append(f"a.status = ${param_idx}")
                params.append(status.value)
                param_idx += 1
            elif not include_resolved:
                conditions.append("a.status != 'resolved'")

            if severity:
                conditions.append(f"a.severity = ${param_idx}")
                params.append(severity.value)
                param_idx += 1

            if source:
                conditions.append(f"a.source = ${param_idx}")
                params.append(source.value)
                param_idx += 1

            # Time filter
            conditions.append(f"a.created_at > NOW() - INTERVAL '{hours} hours'")

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            # Count total
            count_query = f"SELECT COUNT(*) FROM alerts a WHERE {where_clause}"
            total = await conn.fetchval(count_query, *params)

            # Fetch alerts with rule info
            offset = (page - 1) * page_size
            alerts_query = f"""
                SELECT
                    a.id, a.rule_id, a.severity, a.name, a.message, a.source,
                    a.labels, a.value, a.status, a.acknowledged_by, a.acknowledged_at,
                    a.acknowledge_note, a.created_at, a.resolved_at, a.resolved_by,
                    a.resolution_note, r.metric, r.unit
                FROM alerts a
                LEFT JOIN alert_rules r ON a.rule_id = r.id
                WHERE {where_clause}
                ORDER BY
                    CASE a.severity
                        WHEN 'critical' THEN 1
                        WHEN 'warning' THEN 2
                        ELSE 3
                    END,
                    a.created_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            params.extend([page_size, offset])
            rows = await conn.fetch(alerts_query, *params)

            # Get statistics
            stats_row = await conn.fetchrow("SELECT * FROM alert_statistics_view")

            alerts = []
            for row in rows:
                alerts.append(AlertResponse(
                    id=row["id"],
                    rule_id=row["rule_id"],
                    severity=AlertSeverity(row["severity"]),
                    name=row["name"],
                    message=row["message"],
                    source=AlertSource(row["source"]) if row["source"] else AlertSource.SYSTEM,
                    labels=row["labels"] or {},
                    value=float(row["value"]) if row["value"] else None,
                    status=AlertStatus(row["status"]),
                    acknowledged_by=row["acknowledged_by"],
                    acknowledged_at=row["acknowledged_at"],
                    acknowledge_note=row["acknowledge_note"],
                    created_at=row["created_at"],
                    resolved_at=row["resolved_at"],
                    resolved_by=row["resolved_by"],
                    resolution_note=row["resolution_note"],
                    metric=row["metric"],
                    unit=row["unit"]
                ))

            statistics = None
            if stats_row:
                statistics = AlertStatistics(
                    active_count=stats_row["active_count"],
                    acknowledged_count=stats_row["acknowledged_count"],
                    resolved_24h_count=stats_row["resolved_24h_count"],
                    critical_active=stats_row["critical_active"],
                    warning_active=stats_row["warning_active"],
                    info_active=stats_row["info_active"],
                    total_24h=stats_row["total_24h"],
                    total_7d=stats_row["total_7d"]
                )

            return AlertsListResponse(
                alerts=alerts,
                total=total,
                page=page,
                page_size=page_size,
                statistics=statistics
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/alerts/rules",
    response_model=AlertRulesListResponse,
    summary="Get alert rule configurations",
    description="Get all configured alert rules with their thresholds and settings.",
)
async def get_alert_rules(
    enabled_only: bool = Query(False, description="Only return enabled rules"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all alert rule configurations.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            if enabled_only:
                rows = await conn.fetch(
                    """
                    SELECT * FROM alert_rules WHERE enabled = true ORDER BY name
                    """
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM alert_rules ORDER BY name"
                )

            rules = []
            for row in rows:
                rules.append(AlertRuleResponse(
                    id=row["id"],
                    name=row["name"],
                    metric=row["metric"],
                    description=row["description"],
                    warning_threshold=float(row["warning_threshold"]) if row["warning_threshold"] else None,
                    critical_threshold=float(row["critical_threshold"]) if row["critical_threshold"] else None,
                    comparison_operator=ComparisonOperator(row["comparison_operator"]),
                    unit=row["unit"],
                    enabled=row["enabled"],
                    check_interval_seconds=row["check_interval_seconds"],
                    notification_channels=row["notification_channels"] or [],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                ))

            return AlertRulesListResponse(rules=rules, total=len(rules))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching alert rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/alerts/rules",
    response_model=AlertRulesListResponse,
    summary="Update alert rules",
    description="Bulk update alert rules. Pass a list of rules with their IDs.",
)
async def update_alert_rules(
    rules: List[Dict[str, Any]],
    admin: dict = Depends(require_admin)
):
    """
    Bulk update alert rules.

    Each rule in the list should have an 'id' field and any fields to update.
    """
    try:
        pool = await get_db_pool()
        updated_rules = []

        async with pool.acquire() as conn:
            for rule_data in rules:
                rule_id = rule_data.get("id")
                if not rule_id:
                    continue

                # Build update query dynamically
                updates = []
                params = []
                param_idx = 1

                updatable_fields = [
                    "name", "metric", "description", "warning_threshold",
                    "critical_threshold", "comparison_operator", "unit",
                    "enabled", "check_interval_seconds", "notification_channels"
                ]

                for field in updatable_fields:
                    if field in rule_data and rule_data[field] is not None:
                        updates.append(f"{field} = ${param_idx}")
                        params.append(rule_data[field])
                        param_idx += 1

                if not updates:
                    continue

                params.append(rule_id)
                query = f"""
                    UPDATE alert_rules
                    SET {', '.join(updates)}, updated_at = NOW()
                    WHERE id = ${param_idx}
                    RETURNING *
                """

                row = await conn.fetchrow(query, *params)
                if row:
                    updated_rules.append(AlertRuleResponse(
                        id=row["id"],
                        name=row["name"],
                        metric=row["metric"],
                        description=row["description"],
                        warning_threshold=float(row["warning_threshold"]) if row["warning_threshold"] else None,
                        critical_threshold=float(row["critical_threshold"]) if row["critical_threshold"] else None,
                        comparison_operator=ComparisonOperator(row["comparison_operator"]),
                        unit=row["unit"],
                        enabled=row["enabled"],
                        check_interval_seconds=row["check_interval_seconds"],
                        notification_channels=row["notification_channels"] or [],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"]
                    ))

            logger.info(f"Admin {admin.get('email')} updated {len(updated_rules)} alert rules")

            return AlertRulesListResponse(rules=updated_rules, total=len(updated_rules))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/alerts/rules",
    response_model=AlertRuleResponse,
    summary="Create a new alert rule",
    description="Create a new alert rule with thresholds and notification settings.",
)
async def create_alert_rule(
    rule: AlertRuleCreate,
    admin: dict = Depends(require_admin)
):
    """
    Create a new alert rule.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO alert_rules (
                    name, metric, description, warning_threshold, critical_threshold,
                    comparison_operator, unit, enabled, check_interval_seconds, notification_channels
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING *
                """,
                rule.name, rule.metric, rule.description, rule.warning_threshold,
                rule.critical_threshold, rule.comparison_operator.value, rule.unit,
                rule.enabled, rule.check_interval_seconds, rule.notification_channels
            )

            logger.info(f"Admin {admin.get('email')} created alert rule: {rule.name}")

            return AlertRuleResponse(
                id=row["id"],
                name=row["name"],
                metric=row["metric"],
                description=row["description"],
                warning_threshold=float(row["warning_threshold"]) if row["warning_threshold"] else None,
                critical_threshold=float(row["critical_threshold"]) if row["critical_threshold"] else None,
                comparison_operator=ComparisonOperator(row["comparison_operator"]),
                unit=row["unit"],
                enabled=row["enabled"],
                check_interval_seconds=row["check_interval_seconds"],
                notification_channels=row["notification_channels"] or [],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

    except Exception as e:
        if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
            raise HTTPException(status_code=400, detail=f"Alert rule with name '{rule.name}' already exists")
        logger.error(f"Error creating alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/alerts/rules/{rule_id}",
    summary="Delete an alert rule",
    description="Delete an alert rule by ID. This will not delete associated alerts.",
)
async def delete_alert_rule(
    rule_id: int,
    admin: dict = Depends(require_admin)
):
    """
    Delete an alert rule.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM alert_rules WHERE id = $1", rule_id
            )

            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Alert rule not found")

            logger.info(f"Admin {admin.get('email')} deleted alert rule ID: {rule_id}")

            return {"message": "Alert rule deleted", "id": rule_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/alerts/{alert_id}/acknowledge",
    response_model=AlertResponse,
    summary="Acknowledge an alert",
    description="Acknowledge an active alert to indicate it's being handled.",
)
async def acknowledge_alert(
    alert_id: int,
    request_body: AcknowledgeAlertRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Acknowledge an alert.

    Updates the alert status to 'acknowledged' and records who acknowledged it.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Check alert exists and is active
            existing = await conn.fetchrow(
                "SELECT status FROM alerts WHERE id = $1", alert_id
            )

            if not existing:
                raise HTTPException(status_code=404, detail="Alert not found")

            if existing["status"] == "resolved":
                raise HTTPException(status_code=400, detail="Cannot acknowledge a resolved alert")

            user_email = current_user.get("email") or current_user.get("username") or "unknown"

            row = await conn.fetchrow(
                """
                UPDATE alerts
                SET status = 'acknowledged',
                    acknowledged_by = $1,
                    acknowledged_at = NOW(),
                    acknowledge_note = $2
                WHERE id = $3
                RETURNING a.*, r.metric, r.unit
                FROM alerts a
                LEFT JOIN alert_rules r ON a.rule_id = r.id
                WHERE a.id = $3
                """,
                user_email, request_body.note, alert_id
            )

            # Re-fetch with join since RETURNING with FROM doesn't work directly
            row = await conn.fetchrow(
                """
                SELECT
                    a.*, r.metric, r.unit
                FROM alerts a
                LEFT JOIN alert_rules r ON a.rule_id = r.id
                WHERE a.id = $1
                """,
                alert_id
            )

            logger.info(f"User {user_email} acknowledged alert ID: {alert_id}")

            return AlertResponse(
                id=row["id"],
                rule_id=row["rule_id"],
                severity=AlertSeverity(row["severity"]),
                name=row["name"],
                message=row["message"],
                source=AlertSource(row["source"]) if row["source"] else AlertSource.SYSTEM,
                labels=row["labels"] or {},
                value=float(row["value"]) if row["value"] else None,
                status=AlertStatus(row["status"]),
                acknowledged_by=row["acknowledged_by"],
                acknowledged_at=row["acknowledged_at"],
                acknowledge_note=row["acknowledge_note"],
                created_at=row["created_at"],
                resolved_at=row["resolved_at"],
                resolved_by=row["resolved_by"],
                resolution_note=row["resolution_note"],
                metric=row["metric"],
                unit=row["unit"]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/alerts/{alert_id}/resolve",
    response_model=AlertResponse,
    summary="Resolve an alert",
    description="Mark an alert as resolved.",
)
async def resolve_alert(
    alert_id: int,
    resolution_note: Optional[str] = Query(None, max_length=500, description="Resolution note"),
    current_user: dict = Depends(get_current_user)
):
    """
    Resolve an alert.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT status FROM alerts WHERE id = $1", alert_id
            )

            if not existing:
                raise HTTPException(status_code=404, detail="Alert not found")

            if existing["status"] == "resolved":
                raise HTTPException(status_code=400, detail="Alert is already resolved")

            user_email = current_user.get("email") or current_user.get("username") or "unknown"

            await conn.execute(
                """
                UPDATE alerts
                SET status = 'resolved',
                    resolved_at = NOW(),
                    resolved_by = $1,
                    resolution_note = $2
                WHERE id = $3
                """,
                user_email, resolution_note, alert_id
            )

            row = await conn.fetchrow(
                """
                SELECT a.*, r.metric, r.unit
                FROM alerts a
                LEFT JOIN alert_rules r ON a.rule_id = r.id
                WHERE a.id = $1
                """,
                alert_id
            )

            logger.info(f"User {user_email} resolved alert ID: {alert_id}")

            return AlertResponse(
                id=row["id"],
                rule_id=row["rule_id"],
                severity=AlertSeverity(row["severity"]),
                name=row["name"],
                message=row["message"],
                source=AlertSource(row["source"]) if row["source"] else AlertSource.SYSTEM,
                labels=row["labels"] or {},
                value=float(row["value"]) if row["value"] else None,
                status=AlertStatus(row["status"]),
                acknowledged_by=row["acknowledged_by"],
                acknowledged_at=row["acknowledged_at"],
                acknowledge_note=row["acknowledge_note"],
                created_at=row["created_at"],
                resolved_at=row["resolved_at"],
                resolved_by=row["resolved_by"],
                resolution_note=row["resolution_note"],
                metric=row["metric"],
                unit=row["unit"]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/alerts/prometheus",
    summary="Get raw Prometheus alerts",
    description="Fetch current alerts directly from Prometheus API.",
)
async def get_prometheus_alerts(
    current_user: dict = Depends(get_current_user)
):
    """
    Get alerts directly from Prometheus.

    Returns raw Prometheus alert data without database integration.
    """
    try:
        alerts = await fetch_prometheus_alerts()

        return {
            "alerts": alerts,
            "count": len(alerts),
            "source": PROMETHEUS_URL,
            "fetched_at": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        logger.error(f"Error fetching Prometheus alerts: {e}")
        return {
            "alerts": [],
            "count": 0,
            "source": PROMETHEUS_URL,
            "error": str(e),
            "fetched_at": datetime.utcnow().isoformat() + "Z"
        }


@router.get(
    "/alerts/statistics",
    response_model=AlertStatistics,
    summary="Get alert statistics",
    description="Get summary statistics of alerts.",
)
async def get_alert_statistics(
    current_user: dict = Depends(get_current_user)
):
    """
    Get alert statistics summary.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM alert_statistics_view")

            if not row:
                return AlertStatistics(
                    active_count=0,
                    acknowledged_count=0,
                    resolved_24h_count=0,
                    critical_active=0,
                    warning_active=0,
                    info_active=0,
                    total_24h=0,
                    total_7d=0
                )

            return AlertStatistics(
                active_count=row["active_count"],
                acknowledged_count=row["acknowledged_count"],
                resolved_24h_count=row["resolved_24h_count"],
                critical_active=row["critical_active"],
                warning_active=row["warning_active"],
                info_active=row["info_active"],
                total_24h=row["total_24h"],
                total_7d=row["total_7d"]
            )

    except Exception as e:
        logger.error(f"Error fetching alert statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    summary="Health check for alerts API",
    description="Check if the alerts API and its dependencies are healthy.",
)
async def alerts_health_check():
    """
    Health check endpoint for the alerts API.
    """
    health = {
        "status": "healthy",
        "service": "alerts-api",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dependencies": {}
    }

    # Check database
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
            health["dependencies"]["database"] = "healthy"
    except Exception as e:
        health["dependencies"]["database"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"

    # Check Prometheus
    prometheus_result = await query_prometheus("/api/v1/status/runtimeinfo")
    if prometheus_result and prometheus_result.get("status") == "success":
        health["dependencies"]["prometheus"] = "healthy"
    else:
        health["dependencies"]["prometheus"] = "unavailable"
        # Prometheus being unavailable doesn't make the service unhealthy
        # as we fall back to database-only mode

    return health


# Export router
__all__ = ["router"]
