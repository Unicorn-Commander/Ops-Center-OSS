"""
Webhooks Management API Router

Provides REST endpoints for managing webhook configurations and tracking deliveries.
Webhooks allow external systems to receive real-time notifications about events
occurring within the Ops-Center platform.

Author: Ops-Center AI
Created: January 31, 2026

Endpoints:
    GET    /api/v1/admin/webhooks                       - List all webhooks
    POST   /api/v1/admin/webhooks                       - Create new webhook
    GET    /api/v1/admin/webhooks/{webhook_id}          - Get webhook details
    PUT    /api/v1/admin/webhooks/{webhook_id}          - Update webhook
    DELETE /api/v1/admin/webhooks/{webhook_id}          - Delete webhook
    POST   /api/v1/admin/webhooks/{webhook_id}/test     - Test webhook
    GET    /api/v1/admin/webhooks/{webhook_id}/deliveries - Get delivery history

Supported Events:
    - user.created, user.deleted
    - subscription.created, subscription.cancelled
    - payment.received, payment.failed
    - service.started, service.stopped
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import secrets
import hashlib
import hmac
import json
import sys
import os
import httpx

from database.connection import get_db_pool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/webhooks", tags=["Webhooks Management"])

# =============================================================================
# Constants
# =============================================================================

SUPPORTED_EVENTS = [
    "user.created",
    "user.deleted",
    "subscription.created",
    "subscription.cancelled",
    "payment.received",
    "payment.failed",
    "service.started",
    "service.stopped",
]

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_RETRY_COUNT = 3
MAX_DELIVERIES_PER_PAGE = 100


# =============================================================================
# Pydantic Models
# =============================================================================

class WebhookCreate(BaseModel):
    """Request model for creating a new webhook."""
    name: str = Field(..., min_length=1, max_length=255, description="Webhook name")
    url: str = Field(..., description="Webhook endpoint URL")
    events: List[str] = Field(..., min_length=1, description="Event types to subscribe to")
    description: Optional[str] = Field(None, max_length=1000, description="Webhook description")
    headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="Custom HTTP headers")
    retry_count: Optional[int] = Field(DEFAULT_RETRY_COUNT, ge=0, le=10, description="Number of retry attempts")
    timeout_seconds: Optional[int] = Field(DEFAULT_TIMEOUT_SECONDS, gt=0, le=120, description="Request timeout")
    is_active: Optional[bool] = Field(True, description="Whether webhook is active")

    @field_validator("events")
    @classmethod
    def validate_events(cls, v):
        invalid_events = [e for e in v if e not in SUPPORTED_EVENTS]
        if invalid_events:
            raise ValueError(f"Invalid event types: {invalid_events}. Supported: {SUPPORTED_EVENTS}")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class WebhookUpdate(BaseModel):
    """Request model for updating a webhook."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = None
    events: Optional[List[str]] = None
    description: Optional[str] = Field(None, max_length=1000)
    headers: Optional[Dict[str, str]] = None
    retry_count: Optional[int] = Field(None, ge=0, le=10)
    timeout_seconds: Optional[int] = Field(None, gt=0, le=120)
    is_active: Optional[bool] = None

    @field_validator("events")
    @classmethod
    def validate_events(cls, v):
        if v is not None:
            invalid_events = [e for e in v if e not in SUPPORTED_EVENTS]
            if invalid_events:
                raise ValueError(f"Invalid event types: {invalid_events}. Supported: {SUPPORTED_EVENTS}")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class WebhookResponse(BaseModel):
    """Response model for webhook data."""
    id: int
    name: str
    url: str
    secret_key: str
    events: List[str]
    is_active: bool
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime]
    description: Optional[str]
    headers: Dict[str, str]
    retry_count: int
    timeout_seconds: int


class WebhookDeliveryResponse(BaseModel):
    """Response model for webhook delivery data."""
    id: int
    webhook_id: int
    event_type: str
    payload: Optional[Dict[str, Any]]
    response_status: Optional[int]
    response_body: Optional[str]
    response_time_ms: Optional[int]
    success: bool
    error_message: Optional[str]
    created_at: datetime
    attempt_number: int


class WebhookTestRequest(BaseModel):
    """Request model for testing a webhook."""
    event_type: Optional[str] = Field("user.created", description="Event type to simulate")
    payload: Optional[Dict[str, Any]] = Field(None, description="Custom test payload")

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v):
        if v not in SUPPORTED_EVENTS:
            raise ValueError(f"Invalid event type: {v}. Supported: {SUPPORTED_EVENTS}")
        return v


class WebhookTestResponse(BaseModel):
    """Response model for webhook test result."""
    success: bool
    response_status: Optional[int]
    response_body: Optional[str]
    response_time_ms: int
    error_message: Optional[str]
    delivery_id: int


# =============================================================================
# Authentication Dependencies
# =============================================================================

async def get_current_user(request: Request) -> dict:
    """Verify user is authenticated via Redis session."""
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


async def require_admin(request: Request) -> dict:
    """Verify user is authenticated and has admin role."""
    user = await get_current_user(request)

    if not user.get("is_admin") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


# =============================================================================
# Helper Functions
# =============================================================================

def generate_secret_key() -> str:
    """Generate a secure secret key for webhook signing."""
    return secrets.token_urlsafe(32)


def generate_signature(payload: str, secret_key: str) -> str:
    """Generate HMAC-SHA256 signature for webhook payload."""
    return hmac.new(
        secret_key.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def get_sample_payload(event_type: str) -> Dict[str, Any]:
    """Generate a sample payload for testing based on event type."""
    timestamp = datetime.utcnow().isoformat()

    payloads = {
        "user.created": {
            "user_id": "test-user-123",
            "email": "test@example.com",
            "username": "testuser",
            "created_at": timestamp
        },
        "user.deleted": {
            "user_id": "test-user-123",
            "email": "test@example.com",
            "deleted_at": timestamp
        },
        "subscription.created": {
            "subscription_id": "sub-test-456",
            "user_id": "test-user-123",
            "tier": "professional",
            "created_at": timestamp
        },
        "subscription.cancelled": {
            "subscription_id": "sub-test-456",
            "user_id": "test-user-123",
            "tier": "professional",
            "cancelled_at": timestamp,
            "reason": "Test cancellation"
        },
        "payment.received": {
            "payment_id": "pay-test-789",
            "user_id": "test-user-123",
            "amount": 49.00,
            "currency": "USD",
            "received_at": timestamp
        },
        "payment.failed": {
            "payment_id": "pay-test-789",
            "user_id": "test-user-123",
            "amount": 49.00,
            "currency": "USD",
            "error": "Card declined",
            "failed_at": timestamp
        },
        "service.started": {
            "service_name": "test-service",
            "started_at": timestamp,
            "started_by": "admin"
        },
        "service.stopped": {
            "service_name": "test-service",
            "stopped_at": timestamp,
            "stopped_by": "admin",
            "reason": "Test stop"
        }
    }

    return payloads.get(event_type, {"event": event_type, "timestamp": timestamp})


async def send_webhook(
    url: str,
    payload: Dict[str, Any],
    secret_key: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS
) -> tuple[bool, Optional[int], Optional[str], int, Optional[str]]:
    """
    Send webhook request with signature.

    Returns:
        Tuple of (success, status_code, response_body, response_time_ms, error_message)
    """
    payload_json = json.dumps(payload, default=str, sort_keys=True)
    signature = generate_signature(payload_json, secret_key)

    request_headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": f"sha256={signature}",
        "X-Webhook-Timestamp": datetime.utcnow().isoformat(),
        "User-Agent": "Ops-Center-Webhooks/1.0"
    }

    if headers:
        request_headers.update(headers)

    start_time = datetime.utcnow()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                content=payload_json,
                headers=request_headers,
                timeout=timeout
            )

        response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        success = 200 <= response.status_code < 300

        return (
            success,
            response.status_code,
            response.text[:5000] if response.text else None,  # Limit response body
            response_time_ms,
            None if success else f"HTTP {response.status_code}"
        )

    except httpx.TimeoutException:
        response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        return (False, None, None, response_time_ms, f"Request timed out after {timeout}s")

    except httpx.RequestError as e:
        response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        return (False, None, None, response_time_ms, f"Request failed: {str(e)}")

    except Exception as e:
        response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Unexpected error sending webhook: {e}")
        return (False, None, None, response_time_ms, f"Unexpected error: {str(e)}")


async def record_delivery(
    pool,
    webhook_id: int,
    event_type: str,
    payload: Dict[str, Any],
    response_status: Optional[int],
    response_body: Optional[str],
    response_time_ms: int,
    success: bool,
    error_message: Optional[str],
    request_headers: Optional[Dict[str, str]] = None,
    attempt_number: int = 1
) -> int:
    """Record webhook delivery attempt in database."""
    async with pool.acquire() as conn:
        delivery_id = await conn.fetchval(
            """
            INSERT INTO webhook_deliveries (
                webhook_id, event_type, payload, response_status, response_body,
                response_time_ms, success, error_message, request_headers, attempt_number
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
            """,
            webhook_id,
            event_type,
            json.dumps(payload, default=str),
            response_status,
            response_body,
            response_time_ms,
            success,
            error_message,
            json.dumps(request_headers) if request_headers else None,
            attempt_number
        )

        # Update last_triggered_at on webhook
        await conn.execute(
            "UPDATE webhooks SET last_triggered_at = CURRENT_TIMESTAMP WHERE id = $1",
            webhook_id
        )

        return delivery_id


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("")
async def list_webhooks(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    event_type: Optional[str] = Query(None, description="Filter by subscribed event type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    admin: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    List all webhooks with optional filtering.

    **Query Parameters**:
    - `is_active`: Filter by active/inactive status
    - `event_type`: Filter webhooks subscribed to specific event
    - `limit`: Maximum results (1-100, default: 50)
    - `offset`: Pagination offset

    **Returns**:
    - List of webhooks
    - Total count
    - Pagination info
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Build query with filters
            conditions = []
            params = []
            param_idx = 1

            if is_active is not None:
                conditions.append(f"is_active = ${param_idx}")
                params.append(is_active)
                param_idx += 1

            if event_type:
                conditions.append(f"${param_idx} = ANY(events)")
                params.append(event_type)
                param_idx += 1

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            # Get total count
            count_query = f"SELECT COUNT(*) FROM webhooks {where_clause}"
            total_count = await conn.fetchval(count_query, *params)

            # Get webhooks
            query = f"""
                SELECT id, name, url, secret_key, events, is_active, created_by,
                       created_at, updated_at, last_triggered_at, description,
                       COALESCE(headers, '{{}}')::text as headers, retry_count, timeout_seconds
                FROM webhooks
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            params.extend([limit, offset])

            rows = await conn.fetch(query, *params)

            webhooks = []
            for row in rows:
                webhooks.append({
                    "id": row["id"],
                    "name": row["name"],
                    "url": row["url"],
                    "secret_key": row["secret_key"][:8] + "..." if row["secret_key"] else None,  # Mask secret
                    "events": row["events"],
                    "is_active": row["is_active"],
                    "created_by": row["created_by"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    "last_triggered_at": row["last_triggered_at"].isoformat() if row["last_triggered_at"] else None,
                    "description": row["description"],
                    "headers": json.loads(row["headers"]) if row["headers"] else {},
                    "retry_count": row["retry_count"],
                    "timeout_seconds": row["timeout_seconds"]
                })

            return {
                "webhooks": webhooks,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(webhooks) < total_count
            }

    except Exception as e:
        logger.error(f"Failed to list webhooks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list webhooks: {str(e)}")


@router.post("", status_code=201)
async def create_webhook(
    webhook: WebhookCreate,
    admin: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Create a new webhook configuration.

    **Request Body**:
    - `name`: Webhook name (required)
    - `url`: Webhook endpoint URL (required)
    - `events`: List of event types to subscribe to (required)
    - `description`: Optional description
    - `headers`: Custom HTTP headers to include
    - `retry_count`: Number of retry attempts (0-10, default: 3)
    - `timeout_seconds`: Request timeout (1-120, default: 30)
    - `is_active`: Whether webhook is active (default: true)

    **Returns**:
    - Created webhook details
    - Generated secret key (shown only once)
    """
    try:
        pool = await get_db_pool()
        secret_key = generate_secret_key()
        created_by = admin.get("email") or admin.get("username") or "admin"

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO webhooks (name, url, secret_key, events, is_active, created_by,
                                      description, headers, retry_count, timeout_seconds)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id, name, url, secret_key, events, is_active, created_by,
                          created_at, updated_at, last_triggered_at, description,
                          COALESCE(headers, '{}')::text as headers, retry_count, timeout_seconds
                """,
                webhook.name,
                webhook.url,
                secret_key,
                webhook.events,
                webhook.is_active,
                created_by,
                webhook.description,
                json.dumps(webhook.headers) if webhook.headers else "{}",
                webhook.retry_count,
                webhook.timeout_seconds
            )

            logger.info(f"Webhook created: {webhook.name} by {created_by}")

            return {
                "message": "Webhook created successfully",
                "webhook": {
                    "id": row["id"],
                    "name": row["name"],
                    "url": row["url"],
                    "secret_key": row["secret_key"],  # Show full key on creation
                    "events": row["events"],
                    "is_active": row["is_active"],
                    "created_by": row["created_by"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    "last_triggered_at": None,
                    "description": row["description"],
                    "headers": json.loads(row["headers"]) if row["headers"] else {},
                    "retry_count": row["retry_count"],
                    "timeout_seconds": row["timeout_seconds"]
                },
                "note": "Save the secret_key securely. It will not be shown again in full."
            }

    except Exception as e:
        logger.error(f"Failed to create webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create webhook: {str(e)}")


@router.get("/{webhook_id}")
async def get_webhook(
    webhook_id: int,
    admin: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get webhook details by ID.

    **Path Parameters**:
    - `webhook_id`: Webhook ID

    **Returns**:
    - Webhook configuration details
    - Delivery statistics
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, name, url, secret_key, events, is_active, created_by,
                       created_at, updated_at, last_triggered_at, description,
                       COALESCE(headers, '{}')::text as headers, retry_count, timeout_seconds
                FROM webhooks WHERE id = $1
                """,
                webhook_id
            )

            if not row:
                raise HTTPException(status_code=404, detail="Webhook not found")

            # Get delivery statistics
            stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_deliveries,
                    COUNT(CASE WHEN success = true THEN 1 END) as successful_deliveries,
                    COUNT(CASE WHEN success = false THEN 1 END) as failed_deliveries,
                    AVG(response_time_ms) as avg_response_time_ms
                FROM webhook_deliveries
                WHERE webhook_id = $1
                """,
                webhook_id
            )

            return {
                "webhook": {
                    "id": row["id"],
                    "name": row["name"],
                    "url": row["url"],
                    "secret_key": row["secret_key"][:8] + "..." if row["secret_key"] else None,
                    "events": row["events"],
                    "is_active": row["is_active"],
                    "created_by": row["created_by"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    "last_triggered_at": row["last_triggered_at"].isoformat() if row["last_triggered_at"] else None,
                    "description": row["description"],
                    "headers": json.loads(row["headers"]) if row["headers"] else {},
                    "retry_count": row["retry_count"],
                    "timeout_seconds": row["timeout_seconds"]
                },
                "statistics": {
                    "total_deliveries": stats["total_deliveries"] or 0,
                    "successful_deliveries": stats["successful_deliveries"] or 0,
                    "failed_deliveries": stats["failed_deliveries"] or 0,
                    "success_rate": round(
                        (stats["successful_deliveries"] or 0) / max(stats["total_deliveries"] or 1, 1) * 100, 2
                    ),
                    "avg_response_time_ms": round(stats["avg_response_time_ms"] or 0, 2)
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get webhook: {str(e)}")


@router.put("/{webhook_id}")
async def update_webhook(
    webhook_id: int,
    webhook: WebhookUpdate,
    admin: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Update an existing webhook.

    **Path Parameters**:
    - `webhook_id`: Webhook ID

    **Request Body**:
    - Any webhook fields to update (all optional)

    **Returns**:
    - Updated webhook details
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Check if webhook exists
            existing = await conn.fetchval("SELECT id FROM webhooks WHERE id = $1", webhook_id)
            if not existing:
                raise HTTPException(status_code=404, detail="Webhook not found")

            # Build update query dynamically
            updates = []
            params = []
            param_idx = 1

            update_data = webhook.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field == "headers" and value is not None:
                    updates.append(f"headers = ${param_idx}")
                    params.append(json.dumps(value))
                else:
                    updates.append(f"{field} = ${param_idx}")
                    params.append(value)
                param_idx += 1

            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")

            params.append(webhook_id)
            query = f"""
                UPDATE webhooks
                SET {', '.join(updates)}
                WHERE id = ${param_idx}
                RETURNING id, name, url, secret_key, events, is_active, created_by,
                          created_at, updated_at, last_triggered_at, description,
                          COALESCE(headers, '{{}}')::text as headers, retry_count, timeout_seconds
            """

            row = await conn.fetchrow(query, *params)

            logger.info(f"Webhook updated: {row['name']} (ID: {webhook_id})")

            return {
                "message": "Webhook updated successfully",
                "webhook": {
                    "id": row["id"],
                    "name": row["name"],
                    "url": row["url"],
                    "secret_key": row["secret_key"][:8] + "..." if row["secret_key"] else None,
                    "events": row["events"],
                    "is_active": row["is_active"],
                    "created_by": row["created_by"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    "last_triggered_at": row["last_triggered_at"].isoformat() if row["last_triggered_at"] else None,
                    "description": row["description"],
                    "headers": json.loads(row["headers"]) if row["headers"] else {},
                    "retry_count": row["retry_count"],
                    "timeout_seconds": row["timeout_seconds"]
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update webhook: {str(e)}")


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    admin: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Delete a webhook and all its delivery history.

    **Path Parameters**:
    - `webhook_id`: Webhook ID

    **Returns**:
    - Confirmation message
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Check if webhook exists
            webhook = await conn.fetchrow(
                "SELECT id, name FROM webhooks WHERE id = $1",
                webhook_id
            )
            if not webhook:
                raise HTTPException(status_code=404, detail="Webhook not found")

            # Delete webhook (cascade deletes deliveries)
            await conn.execute("DELETE FROM webhooks WHERE id = $1", webhook_id)

            logger.info(f"Webhook deleted: {webhook['name']} (ID: {webhook_id})")

            return {
                "message": "Webhook deleted successfully",
                "deleted_id": webhook_id,
                "deleted_name": webhook["name"]
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete webhook: {str(e)}")


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    test_request: WebhookTestRequest = WebhookTestRequest(),
    admin: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Test a webhook by sending a sample payload.

    **Path Parameters**:
    - `webhook_id`: Webhook ID

    **Request Body**:
    - `event_type`: Event type to simulate (default: user.created)
    - `payload`: Custom test payload (optional)

    **Returns**:
    - Test result including response status and timing
    - Delivery ID for reference
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            webhook = await conn.fetchrow(
                """
                SELECT id, name, url, secret_key, is_active,
                       COALESCE(headers, '{}')::text as headers, timeout_seconds
                FROM webhooks WHERE id = $1
                """,
                webhook_id
            )

            if not webhook:
                raise HTTPException(status_code=404, detail="Webhook not found")

            if not webhook["is_active"]:
                raise HTTPException(status_code=400, detail="Webhook is not active")

            # Prepare payload
            event_type = test_request.event_type
            payload = test_request.payload or get_sample_payload(event_type)
            payload["_test"] = True
            payload["_webhook_id"] = webhook_id

            headers = json.loads(webhook["headers"]) if webhook["headers"] else {}

            # Send webhook
            success, status, body, response_time, error = await send_webhook(
                url=webhook["url"],
                payload=payload,
                secret_key=webhook["secret_key"],
                headers=headers,
                timeout=webhook["timeout_seconds"]
            )

            # Record delivery
            delivery_id = await record_delivery(
                pool=pool,
                webhook_id=webhook_id,
                event_type=event_type,
                payload=payload,
                response_status=status,
                response_body=body,
                response_time_ms=response_time,
                success=success,
                error_message=error,
                request_headers=headers
            )

            logger.info(f"Webhook test {'succeeded' if success else 'failed'}: {webhook['name']} (ID: {webhook_id})")

            return {
                "success": success,
                "response_status": status,
                "response_body": body[:1000] if body else None,  # Limit for display
                "response_time_ms": response_time,
                "error_message": error,
                "delivery_id": delivery_id,
                "webhook_name": webhook["name"],
                "event_type": event_type
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test webhook: {str(e)}")


@router.get("/{webhook_id}/deliveries")
async def get_webhook_deliveries(
    webhook_id: int,
    success: Optional[bool] = Query(None, description="Filter by success status"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(50, ge=1, le=MAX_DELIVERIES_PER_PAGE, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    admin: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get delivery history for a specific webhook.

    **Path Parameters**:
    - `webhook_id`: Webhook ID

    **Query Parameters**:
    - `success`: Filter by success/failure status
    - `event_type`: Filter by event type
    - `limit`: Maximum results (1-100, default: 50)
    - `offset`: Pagination offset

    **Returns**:
    - List of delivery records
    - Pagination info
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Check if webhook exists
            webhook = await conn.fetchrow(
                "SELECT id, name FROM webhooks WHERE id = $1",
                webhook_id
            )
            if not webhook:
                raise HTTPException(status_code=404, detail="Webhook not found")

            # Build query with filters
            conditions = ["webhook_id = $1"]
            params = [webhook_id]
            param_idx = 2

            if success is not None:
                conditions.append(f"success = ${param_idx}")
                params.append(success)
                param_idx += 1

            if event_type:
                conditions.append(f"event_type = ${param_idx}")
                params.append(event_type)
                param_idx += 1

            where_clause = " AND ".join(conditions)

            # Get total count
            count_query = f"SELECT COUNT(*) FROM webhook_deliveries WHERE {where_clause}"
            total_count = await conn.fetchval(count_query, *params)

            # Get deliveries
            query = f"""
                SELECT id, webhook_id, event_type, payload, response_status,
                       response_body, response_time_ms, success, error_message,
                       created_at, attempt_number
                FROM webhook_deliveries
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            params.extend([limit, offset])

            rows = await conn.fetch(query, *params)

            deliveries = []
            for row in rows:
                deliveries.append({
                    "id": row["id"],
                    "webhook_id": row["webhook_id"],
                    "event_type": row["event_type"],
                    "payload": json.loads(row["payload"]) if row["payload"] else None,
                    "response_status": row["response_status"],
                    "response_body": row["response_body"][:500] if row["response_body"] else None,
                    "response_time_ms": row["response_time_ms"],
                    "success": row["success"],
                    "error_message": row["error_message"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "attempt_number": row["attempt_number"]
                })

            return {
                "webhook_id": webhook_id,
                "webhook_name": webhook["name"],
                "deliveries": deliveries,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(deliveries) < total_count
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deliveries for webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get deliveries: {str(e)}")


@router.get("/events/types")
async def get_supported_events(
    admin: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get list of supported webhook event types.

    **Returns**:
    - List of event types with descriptions
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT event_type, description, payload_schema FROM webhook_event_types ORDER BY event_type"
            )

            if rows:
                events = [
                    {
                        "event_type": row["event_type"],
                        "description": row["description"],
                        "payload_schema": json.loads(row["payload_schema"]) if row["payload_schema"] else None
                    }
                    for row in rows
                ]
            else:
                # Fallback to hardcoded list if table is empty
                events = [
                    {"event_type": e, "description": f"Event: {e}", "payload_schema": None}
                    for e in SUPPORTED_EVENTS
                ]

            return {
                "events": events,
                "total": len(events)
            }

    except Exception as e:
        logger.error(f"Failed to get event types: {e}")
        # Fallback to hardcoded list
        return {
            "events": [
                {"event_type": e, "description": f"Event: {e}", "payload_schema": None}
                for e in SUPPORTED_EVENTS
            ],
            "total": len(SUPPORTED_EVENTS)
        }


# =============================================================================
# Export
# =============================================================================

__all__ = ["router"]
