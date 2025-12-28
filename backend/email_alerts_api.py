"""
Email Alert API Endpoints for Ops-Center
Version: 1.0.0
Author: Email Notification Specialist
Date: November 29, 2025

Purpose: REST API endpoints for sending email alerts and testing email system.

Endpoints:
- POST /api/v1/alerts/send - Send email alert
- POST /api/v1/alerts/test - Send test email
- GET  /api/v1/alerts/history - Get email history
- GET  /api/v1/alerts/health - Check email system health
"""

import logging
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

from email_alerts import email_alert_service

# Logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/v1/alerts", tags=["Email Alerts"])


# ===== MODELS =====

class SendAlertRequest(BaseModel):
    """Send email alert request"""
    alert_type: str = Field(..., description="Alert type: system_critical, billing, security, usage")
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    recipients: List[EmailStr] = Field(..., min_items=1, max_items=10)
    context: Optional[dict] = Field(default=None, description="Additional template context")


class SendTestEmailRequest(BaseModel):
    """Send test email request"""
    recipient: EmailStr


class AlertResponse(BaseModel):
    """Alert API response"""
    success: bool
    message: str
    alert_id: Optional[int] = None


class EmailHistoryItem(BaseModel):
    """Email history item"""
    id: int
    recipient: str
    subject: str
    alert_type: str
    status: str
    sent_at: datetime


class EmailHistoryResponse(BaseModel):
    """Email history response"""
    success: bool
    history: List[EmailHistoryItem]
    total: int
    page: int
    per_page: int


class HealthCheckResponse(BaseModel):
    """Email system health check"""
    healthy: bool
    message: str
    provider: Optional[str] = None
    rate_limit_remaining: int
    last_sent: Optional[datetime] = None


# ===== ENDPOINTS =====

@router.post("/send", response_model=AlertResponse, summary="Send email alert")
async def send_alert(request: SendAlertRequest):
    """
    Send email alert

    **Alert Types**:
    - `system_critical`: Server down, high CPU/memory, disk full
    - `billing`: Payment failed, subscription expiring, quota exceeded
    - `security`: Failed logins, unauthorized access, API key leaked
    - `usage`: API quota warning (80%), quota exceeded, tier upgrade suggestion

    **Rate Limit**: 100 emails per hour

    **Example**:
    ```json
    {
      "alert_type": "billing",
      "subject": "Payment Failed",
      "message": "Your recent payment of $49.00 failed to process.",
      "recipients": ["user@example.com"],
      "context": {
        "amount": "49.00",
        "subscription_tier": "Professional"
      }
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

        # Send alert
        success = await email_alert_service.send_alert(
            alert_type=request.alert_type,
            subject=request.subject,
            message=request.message,
            recipients=request.recipients,
            context=request.context
        )

        if success:
            return AlertResponse(
                success=True,
                message=f"Alert sent successfully to {len(request.recipients)} recipients"
            )
        else:
            return AlertResponse(
                success=False,
                message="Failed to send alert. Check logs for details."
            )

    except Exception as e:
        logger.error(f"Failed to send alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test", response_model=AlertResponse, summary="Send test email")
async def send_test_email(request: SendTestEmailRequest):
    """
    Send test email to verify email system configuration

    Uses the provided Microsoft 365 credentials to send a test message.

    **Example**:
    ```json
    {
      "recipient": "admin@example.com"
    }
    ```
    """
    try:
        success = await email_alert_service.send_alert(
            alert_type="system_critical",
            subject="Test Email from Unicorn Commander Ops Center",
            message="This is a test email to verify your email configuration is working correctly. If you received this, everything is set up properly!",
            recipients=[request.recipient],
            context={
                "server_name": "ops-center-direct",
                "test": True
            }
        )

        if success:
            return AlertResponse(
                success=True,
                message=f"Test email sent successfully to {request.recipient}. Check your inbox!"
            )
        else:
            return AlertResponse(
                success=False,
                message="Failed to send test email. Check your email provider configuration."
            )

    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=EmailHistoryResponse, summary="Get email history")
async def get_email_history(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    status: Optional[str] = Query(None, description="Filter by status (sent/failed)")
):
    """
    Get email sending history

    **Filters**:
    - `alert_type`: system_critical, billing, security, usage
    - `status`: sent, failed

    **Pagination**:
    - `page`: Page number (1-indexed)
    - `per_page`: Items per page (max 100)
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'unicorn-postgresql'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'unicorn'),
            password=os.getenv('POSTGRES_PASSWORD', 'unicorn'),
            database=os.getenv('POSTGRES_DB', 'unicorn_db')
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Build query with filters
        where_clauses = []
        params = []

        if alert_type:
            where_clauses.append("alert_type = %s")
            params.append(alert_type)

        if status:
            where_clauses.append("status = %s")
            params.append(status)

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Count total
        cursor.execute(f"SELECT COUNT(*) FROM email_logs {where_sql}", params)
        total = cursor.fetchone()['count']

        # Get paginated results
        offset = (page - 1) * per_page
        params.extend([per_page, offset])

        cursor.execute(f"""
            SELECT id, recipient, subject, alert_type, status, sent_at
            FROM email_logs
            {where_sql}
            ORDER BY sent_at DESC
            LIMIT %s OFFSET %s
        """, params)

        history = [EmailHistoryItem(**dict(row)) for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return EmailHistoryResponse(
            success=True,
            history=history,
            total=total,
            page=page,
            per_page=per_page
        )

    except Exception as e:
        logger.error(f"Failed to get email history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthCheckResponse, summary="Email system health check")
async def health_check():
    """
    Check email system health

    Returns:
    - Configuration status
    - Rate limit remaining
    - Last email sent timestamp
    """
    try:
        # Check if email system is configured
        if not all([
            email_alert_service.ms365_client_id,
            email_alert_service.ms365_tenant_id,
            email_alert_service.ms365_client_secret
        ]):
            return HealthCheckResponse(
                healthy=False,
                message="Email system not configured. Missing Microsoft 365 credentials.",
                rate_limit_remaining=0
            )

        # Get rate limit info
        rate_limit_remaining = email_alert_service.rate_limiter.get_remaining()

        # Get last sent email
        try:
            conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'unicorn-postgresql'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                user=os.getenv('POSTGRES_USER', 'unicorn'),
                password=os.getenv('POSTGRES_PASSWORD', 'unicorn'),
                database=os.getenv('POSTGRES_DB', 'unicorn_db')
            )
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT sent_at FROM email_logs
                WHERE status = 'sent'
                ORDER BY sent_at DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            last_sent = result['sent_at'] if result else None

            cursor.close()
            conn.close()
        except:
            last_sent = None

        return HealthCheckResponse(
            healthy=True,
            message="Email system configured and operational",
            provider="microsoft365",
            rate_limit_remaining=rate_limit_remaining,
            last_sent=last_sent
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            healthy=False,
            message=f"Health check failed: {str(e)}",
            rate_limit_remaining=0
        )
