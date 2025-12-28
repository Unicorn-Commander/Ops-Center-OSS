"""
Alert Triggers API for Ops-Center
Version: 1.0.0
Author: Backend Team Lead
Date: November 29, 2025

Purpose: REST API endpoints for alert trigger management and monitoring.

Endpoints:
- POST /api/v1/alert-triggers/register - Register new trigger
- DELETE /api/v1/alert-triggers/{trigger_id} - Unregister trigger
- GET /api/v1/alert-triggers - List all triggers
- GET /api/v1/alert-triggers/{trigger_id} - Get trigger details
- POST /api/v1/alert-triggers/{trigger_id}/check - Manually check trigger
- POST /api/v1/alert-triggers/check-all - Check all triggers
- GET /api/v1/alert-triggers/history - Get alert history
- GET /api/v1/alert-triggers/statistics - Get statistics
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, EmailStr

from alert_triggers import alert_trigger_manager

# Logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/v1/alert-triggers", tags=["Alert Triggers"])


# ===== MODELS =====

class RegisterTriggerRequest(BaseModel):
    """Register alert trigger request"""
    trigger_id: str = Field(..., min_length=1, max_length=100, description="Unique trigger ID")
    name: str = Field(..., min_length=1, max_length=200, description="Human-readable name")
    alert_type: str = Field(..., description="Alert type: system_critical, billing, security, usage")
    condition_name: str = Field(..., description="Condition function name from alert_conditions module")
    recipients: List[EmailStr] = Field(..., min_items=1, max_items=10, description="Email recipients")
    cooldown_minutes: int = Field(60, ge=1, le=1440, description="Cooldown period in minutes (1-1440)")
    priority: str = Field("medium", description="Priority: low, medium, high, critical")
    enabled: bool = Field(True, description="Enable trigger immediately")


class TriggerResponse(BaseModel):
    """Alert trigger response"""
    trigger_id: str
    name: str
    alert_type: str
    recipients: List[str]
    cooldown_minutes: int
    priority: str
    enabled: bool
    metadata: Dict[str, Any]


class TriggerCheckResponse(BaseModel):
    """Trigger check response"""
    trigger_id: str
    should_trigger: bool
    alert_sent: bool
    message: str
    context: Optional[Dict[str, Any]] = None


class TriggerHistoryResponse(BaseModel):
    """Trigger history response"""
    success: bool
    history: List[Dict[str, Any]]
    total: int


class TriggerStatisticsResponse(BaseModel):
    """Trigger statistics response"""
    success: bool
    statistics: Dict[str, Any]


class CheckAllResponse(BaseModel):
    """Check all triggers response"""
    success: bool
    results: Dict[str, bool]
    alerts_sent: int
    message: str


# ===== ENDPOINTS =====

@router.post("/register", response_model=TriggerResponse, summary="Register alert trigger")
async def register_trigger(request: RegisterTriggerRequest):
    """
    Register a new alert trigger

    **Alert Types**:
    - `system_critical`: Service down, database errors, API failures
    - `billing`: Payment failures, subscription expiring
    - `security`: Failed logins, API key compromise
    - `usage`: Quota warnings, quota exceeded

    **Condition Functions** (from alert_conditions module):
    - `check_service_health`: Monitor service health
    - `check_database_errors`: Database connection errors
    - `check_api_failures`: High API error rate
    - `check_payment_failures`: Payment failures
    - `check_subscription_expiring`: Expiring subscriptions
    - `check_failed_logins`: Failed login attempts
    - `check_api_key_compromise`: Suspicious API key usage
    - `check_quota_usage`: Users at 80%+ quota
    - `check_quota_exceeded`: Users over 100% quota

    **Example**:
    ```json
    {
      "trigger_id": "service-health",
      "name": "Service Health Monitor",
      "alert_type": "system_critical",
      "condition_name": "check_service_health",
      "recipients": ["admin@example.com"],
      "cooldown_minutes": 60,
      "priority": "critical"
    }
    ```
    """
    try:
        # Validate alert type
        valid_types = ["system_critical", "billing", "security", "usage"]
        if request.alert_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid alert_type. Must be one of: {', '.join(valid_types)}"
            )

        # Validate priority
        valid_priorities = ["low", "medium", "high", "critical"]
        if request.priority not in valid_priorities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
            )

        # Import condition function
        from alert_conditions import (
            check_service_health,
            check_database_errors,
            check_api_failures,
            check_payment_failures,
            check_subscription_expiring,
            check_failed_logins,
            check_api_key_compromise,
            check_quota_usage,
            check_quota_exceeded
        )

        condition_funcs = {
            "check_service_health": check_service_health,
            "check_database_errors": check_database_errors,
            "check_api_failures": check_api_failures,
            "check_payment_failures": check_payment_failures,
            "check_subscription_expiring": check_subscription_expiring,
            "check_failed_logins": check_failed_logins,
            "check_api_key_compromise": check_api_key_compromise,
            "check_quota_usage": check_quota_usage,
            "check_quota_exceeded": check_quota_exceeded
        }

        if request.condition_name not in condition_funcs:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid condition_name. Must be one of: {', '.join(condition_funcs.keys())}"
            )

        condition_func = condition_funcs[request.condition_name]

        # Register trigger
        trigger = alert_trigger_manager.register_trigger(
            trigger_id=request.trigger_id,
            name=request.name,
            alert_type=request.alert_type,
            condition_func=condition_func,
            recipients=request.recipients,
            cooldown_minutes=request.cooldown_minutes,
            priority=request.priority,
            metadata={"condition_name": request.condition_name}
        )

        if not request.enabled:
            trigger.enabled = False

        return TriggerResponse(
            trigger_id=trigger.trigger_id,
            name=trigger.name,
            alert_type=trigger.alert_type,
            recipients=trigger.recipients,
            cooldown_minutes=trigger.cooldown_minutes,
            priority=trigger.priority,
            enabled=trigger.enabled,
            metadata=trigger.metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register trigger: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{trigger_id}", summary="Unregister alert trigger")
async def unregister_trigger(trigger_id: str):
    """
    Unregister an alert trigger

    **Example**: `DELETE /api/v1/alert-triggers/service-health`
    """
    success = alert_trigger_manager.unregister_trigger(trigger_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Trigger not found: {trigger_id}"
        )

    return {"success": True, "message": f"Trigger {trigger_id} unregistered"}


@router.get("", response_model=List[TriggerResponse], summary="List all triggers")
async def list_triggers():
    """
    List all registered alert triggers

    Returns list of triggers with their configuration.
    """
    triggers = alert_trigger_manager.list_triggers()

    return [
        TriggerResponse(
            trigger_id=t.trigger_id,
            name=t.name,
            alert_type=t.alert_type,
            recipients=t.recipients,
            cooldown_minutes=t.cooldown_minutes,
            priority=t.priority,
            enabled=t.enabled,
            metadata=t.metadata
        )
        for t in triggers
    ]


@router.get("/{trigger_id}", response_model=TriggerResponse, summary="Get trigger details")
async def get_trigger(trigger_id: str):
    """
    Get details for a specific trigger

    **Example**: `GET /api/v1/alert-triggers/service-health`
    """
    trigger = alert_trigger_manager.get_trigger(trigger_id)

    if not trigger:
        raise HTTPException(
            status_code=404,
            detail=f"Trigger not found: {trigger_id}"
        )

    return TriggerResponse(
        trigger_id=trigger.trigger_id,
        name=trigger.name,
        alert_type=trigger.alert_type,
        recipients=trigger.recipients,
        cooldown_minutes=trigger.cooldown_minutes,
        priority=trigger.priority,
        enabled=trigger.enabled,
        metadata=trigger.metadata
    )


@router.post("/{trigger_id}/check", response_model=TriggerCheckResponse, summary="Check trigger condition")
async def check_trigger(trigger_id: str):
    """
    Manually check a trigger condition and send alert if needed

    **Example**: `POST /api/v1/alert-triggers/service-health/check`
    """
    trigger = alert_trigger_manager.get_trigger(trigger_id)

    if not trigger:
        raise HTTPException(
            status_code=404,
            detail=f"Trigger not found: {trigger_id}"
        )

    try:
        # Check condition
        should_trigger, context = await alert_trigger_manager.check_trigger_condition(trigger_id)

        alert_sent = False

        if should_trigger:
            # Send alert
            subject = context.get('subject', f"Alert: {trigger.name}")
            message = context.get('message', f"Trigger {trigger.name} activated")

            alert_sent = await alert_trigger_manager.check_and_send(
                trigger_id=trigger_id,
                subject=subject,
                message=message,
                context=context
            )

        return TriggerCheckResponse(
            trigger_id=trigger_id,
            should_trigger=should_trigger,
            alert_sent=alert_sent,
            message="Alert sent" if alert_sent else "Condition not met or in cooldown",
            context=context if should_trigger else None
        )

    except Exception as e:
        logger.error(f"Error checking trigger {trigger_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-all", response_model=CheckAllResponse, summary="Check all triggers")
async def check_all_triggers():
    """
    Check all registered triggers and send alerts as needed

    This endpoint checks ALL enabled triggers and sends alerts for any that meet their conditions.
    Use this for manual monitoring or scheduled checks via cron.

    **Returns**:
    - `results`: Dict mapping trigger_id to success status
    - `alerts_sent`: Count of alerts sent
    """
    try:
        results = await alert_trigger_manager.check_all_triggers()

        alerts_sent = sum(1 for success in results.values() if success)

        return CheckAllResponse(
            success=True,
            results=results,
            alerts_sent=alerts_sent,
            message=f"Checked {len(results)} triggers, sent {alerts_sent} alerts"
        )

    except Exception as e:
        logger.error(f"Error checking all triggers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=TriggerHistoryResponse, summary="Get alert history")
async def get_alert_history(
    trigger_id: Optional[str] = None,
    limit: int = 100
):
    """
    Get alert trigger history

    **Query Parameters**:
    - `trigger_id`: Filter by trigger ID (optional)
    - `limit`: Maximum entries to return (default: 100)

    **Example**: `GET /api/v1/alert-triggers/history?trigger_id=service-health&limit=50`
    """
    try:
        history = alert_trigger_manager.get_alert_history(
            trigger_id=trigger_id,
            limit=limit
        )

        return TriggerHistoryResponse(
            success=True,
            history=history,
            total=len(history)
        )

    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=TriggerStatisticsResponse, summary="Get trigger statistics")
async def get_statistics():
    """
    Get alert trigger statistics

    Returns:
    - Total triggers
    - Enabled/disabled count
    - Breakdown by alert type
    - Breakdown by priority
    - Total alerts sent
    """
    try:
        statistics = alert_trigger_manager.get_statistics()

        return TriggerStatisticsResponse(
            success=True,
            statistics=statistics
        )

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
