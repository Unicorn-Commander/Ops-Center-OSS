"""
Notification Preferences API

Real, persisted notification preferences for the per-user Notification Settings
page (src/pages/NotificationSettings.jsx — the page the Account → "Notification
Preferences" menu item points at).

Replaces the previous mock GET in account_management_api.py, which returned a
hard-coded payload whose field names did not match the UI and had no PUT to save
against. Preferences persist to a small JSONB-backed table keyed by the Keycloak
user id (VARCHAR, consistent with usage_tracking / credit tables).

Endpoints (all session-authenticated):
    GET  /api/v1/notifications/preferences  - load the caller's preferences
    PUT  /api/v1/notifications/preferences  - save the caller's preferences
    POST /api/v1/notifications/test         - REALLY send a test email to the caller

Email delivery is wired through notification_dispatcher.py (active row in
email_providers; Microsoft 365 OAuth2 is the tested path). /test performs a
real send to the caller's notification address and returns {sent, provider}
or the provider error. Slack/SMS delivery is still not available; those
preferences are stored only. No secrets are logged.

Created: 2026-06-17
Updated: 2026-07-02 — /test now sends real email via notification_dispatcher
"""

import inspect
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from auth_dependencies import require_authenticated_user
from database import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Notification Preferences"])

_TABLE_READY = False


@asynccontextmanager
async def _db():
    """
    Acquire a DB connection compatibly across deployments.

    `get_db_connection` resolves to a pool-backed package on the running nodes
    (returns a pool-acquire context manager) but to a plain asyncpg connection
    in other checkouts. Handle both: await if needed, use as an async context
    manager when supported, otherwise close() on exit.
    """
    res = get_db_connection()
    conn = await res if inspect.isawaitable(res) else res
    if hasattr(conn, "__aenter__"):
        async with conn as c:
            yield c
    else:
        try:
            yield conn
        finally:
            await conn.close()


# ---------------------------------------------------------------------------
# Schema — mirrors the fields NotificationSettings.jsx reads/writes
# ---------------------------------------------------------------------------

class NotificationPreferences(BaseModel):
    """Full per-user notification preference set."""
    # Alert types
    usage_alerts_enabled: bool = True
    hardware_alerts_enabled: bool = True
    billing_alerts_enabled: bool = True
    security_alerts_enabled: bool = True

    # Thresholds
    usage_alert_threshold: int = Field(default=80, ge=50, le=95)
    hardware_temp_threshold: int = Field(default=85, ge=70, le=95)

    # Frequency: immediate | daily | weekly
    alert_frequency: str = "immediate"

    # Channels
    email_enabled: bool = True
    email: Optional[str] = None
    slack_enabled: bool = False
    slack_webhook_url: Optional[str] = None
    sms_enabled: bool = False


_ALERT_FREQUENCIES = {"immediate", "daily", "weekly"}

# type -> (subject, body) preview templates for /test
_TEST_TEMPLATES = {
    "usage": (
        "Usage approaching your tier limit",
        "You've reached {usage_alert_threshold}% of your plan's allotment for this period.",
    ),
    "hardware": (
        "Hardware temperature warning",
        "A GPU has crossed your {hardware_temp_threshold}°C alert threshold.",
    ),
    "billing": (
        "Billing update",
        "A new invoice or payment event is available on your account.",
    ),
    "security": (
        "Security alert",
        "A new sign-in or security-relevant event occurred on your account.",
    ),
}

# Which preference toggle gates each test type
_TYPE_ENABLED_FIELD = {
    "usage": "usage_alerts_enabled",
    "hardware": "hardware_alerts_enabled",
    "billing": "billing_alerts_enabled",
    "security": "security_alerts_enabled",
}


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

async def _ensure_table(conn) -> None:
    """Create the preferences table on first use (additive, idempotent)."""
    global _TABLE_READY
    if _TABLE_READY:
        return
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_notification_preferences (
            user_id     VARCHAR(255) PRIMARY KEY,
            preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    _TABLE_READY = True


def _resolve(user: dict) -> str:
    user_id = user.get("user_id") or user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="No user identity in session")
    return user_id


def _merge(stored: Optional[dict], default_email: Optional[str]) -> NotificationPreferences:
    """Build a full preference object from stored JSON over defaults."""
    data = dict(stored or {})
    prefs = NotificationPreferences(**{k: v for k, v in data.items()
                                       if k in NotificationPreferences.model_fields})
    if not prefs.email:
        prefs.email = default_email
    return prefs


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/api/v1/notifications/preferences", response_model=NotificationPreferences)
async def get_notification_preferences(
    user: dict = Depends(require_authenticated_user),
):
    """Return the caller's saved notification preferences (defaults if unset)."""
    user_id = _resolve(user)
    try:
        async with _db() as conn:
            await _ensure_table(conn)
            row = await conn.fetchrow(
                "SELECT preferences FROM user_notification_preferences WHERE user_id = $1",
                user_id,
            )
        stored = None
        if row and row["preferences"]:
            raw = row["preferences"]
            stored = raw if isinstance(raw, dict) else json.loads(raw)
        return _merge(stored, user.get("email"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading notification preferences: {e}")
        # Never hard-fail the settings page — return defaults
        return _merge(None, user.get("email"))


@router.put("/api/v1/notifications/preferences", response_model=NotificationPreferences)
async def update_notification_preferences(
    preferences: NotificationPreferences,
    request: Request,
    user: dict = Depends(require_authenticated_user),
):
    """Persist the caller's notification preferences."""
    user_id = _resolve(user)

    if preferences.alert_frequency not in _ALERT_FREQUENCIES:
        raise HTTPException(
            status_code=422,
            detail=f"alert_frequency must be one of {sorted(_ALERT_FREQUENCIES)}",
        )

    payload = preferences.model_dump()
    try:
        async with _db() as conn:
            await _ensure_table(conn)
            await conn.execute(
                """
                INSERT INTO user_notification_preferences (user_id, preferences, updated_at)
                VALUES ($1, $2::jsonb, now())
                ON CONFLICT (user_id)
                DO UPDATE SET preferences = EXCLUDED.preferences, updated_at = now()
                """,
                user_id,
                json.dumps(payload),
            )
    except Exception as e:
        logger.error(f"Error saving notification preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to save preferences")

    # Audit (no secrets: drop the slack webhook URL from the logged metadata)
    try:
        from audit_logger import audit_logger
        safe = {k: v for k, v in payload.items() if k != "slack_webhook_url"}
        safe["slack_webhook_url_set"] = bool(payload.get("slack_webhook_url"))
        await audit_logger.log(
            action="notifications.preferences_updated",
            result="success",
            user_id=user_id,
            username=user.get("email"),
            ip_address=request.client.host if request.client else None,
            resource_type="notification_preferences",
            resource_id=user_id,
            metadata=safe,
        )
    except Exception as audit_err:  # auditing must never block the save
        logger.warning(f"Audit log for notification prefs failed: {audit_err}")

    return _merge(payload, user.get("email"))


class TestRequest(BaseModel):
    notification_type: str


@router.post("/api/v1/notifications/test")
async def test_notification(
    body: TestRequest,
    user: dict = Depends(require_authenticated_user),
):
    """
    Send a REAL test email for one alert type to the caller.

    Delivers via notification_dispatcher (the active email provider). Because
    this is an explicit user action, it bypasses the alert-type toggles and the
    hourly rate limit (force=True) — but the response notes when the caller's
    saved preferences would suppress real alerts of this type.

    Returns {"sent": true, "provider": ...} on success, or
    {"sent": false, "provider": ..., "error": ...} with the provider error.
    """
    user_id = _resolve(user)
    ntype = (body.notification_type or "").strip().lower()
    if ntype not in _TEST_TEMPLATES:
        raise HTTPException(
            status_code=422,
            detail=f"notification_type must be one of {sorted(_TEST_TEMPLATES)}",
        )

    # Load current prefs for thresholds, recipient override and honest notes
    stored = None
    try:
        async with _db() as conn:
            await _ensure_table(conn)
            row = await conn.fetchrow(
                "SELECT preferences FROM user_notification_preferences WHERE user_id = $1",
                user_id,
            )
        if row and row["preferences"]:
            raw = row["preferences"]
            stored = raw if isinstance(raw, dict) else json.loads(raw)
    except Exception:
        stored = None

    prefs = _merge(stored, user.get("email"))
    subject, body_tmpl = _TEST_TEMPLATES[ntype]
    enabled_field = _TYPE_ENABLED_FIELD[ntype]
    type_enabled = bool(getattr(prefs, enabled_field))
    message = body_tmpl.format(
        usage_alert_threshold=prefs.usage_alert_threshold,
        hardware_temp_threshold=prefs.hardware_temp_threshold,
    )

    recipient = (prefs.email or user.get("email") or "").strip()
    if not recipient or "@" not in recipient:
        raise HTTPException(
            status_code=400,
            detail="No email address on your account or in your notification "
                   "preferences — add one, save, then retry the test.",
        )

    # Really send (explicit user action → force bypasses gating/rate limit)
    from notification_dispatcher import send_notification

    subject_line = f"[Test] {subject}"
    html_fragment = (
        f"<p style=\"margin:0 0 14px;\">This is a <strong>test "
        f"{ntype} alert</strong> from your Ops Center notification settings.</p>"
        f"<p style=\"margin:0 0 14px;\">{message}</p>"
        f"<p style=\"margin:0 0 14px;\">If you received this, email delivery "
        f"is working for your account.</p>"
    )
    text_fallback = (
        f"This is a test {ntype} alert from your Ops Center notification "
        f"settings.\n\n{message}\n\nIf you received this, email delivery is "
        "working for your account."
    )
    result = await send_notification(
        recipient,
        f"test_{ntype}",
        subject_line,
        html_fragment,
        text_fallback,
        user_id=user_id,
        force=True,
    )

    # Honest note about what the caller's SAVED prefs mean for real alerts
    if not prefs.email_enabled:
        note = ("Note: email notifications are turned OFF in your saved "
                "preferences, so real alerts will not be emailed. This test "
                "was sent because you requested it explicitly.")
    elif not type_enabled:
        note = (f"Note: {ntype} alerts are turned OFF in your saved "
                "preferences, so real alerts of this type will not be "
                "emailed. This test was sent because you requested it "
                "explicitly.")
    elif prefs.alert_frequency != "immediate":
        note = (f"Note: your alert frequency is set to '{prefs.alert_frequency}'. "
                "Digest delivery is not available yet, so real-time alert "
                "emails are suppressed until you switch to 'immediate'.")
    else:
        note = None

    if result.get("sent"):
        return {
            "sent": True,
            "provider": result.get("provider"),
            "recipient": result.get("recipient", recipient),
            "message": f"Test {ntype} email sent to {result.get('recipient', recipient)}",
            "note": note,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

    return {
        "sent": False,
        "provider": result.get("provider"),
        "recipient": result.get("recipient", recipient),
        "message": f"Test {ntype} email could not be sent",
        "error": result.get("error") or result.get("skipped") or "Unknown provider error",
        "note": note,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
