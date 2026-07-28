"""
Notification Dispatcher
=======================

Single send-side entry point for user-facing notification emails:
    - low-credit warnings (hooked from litellm_credit_system.debit_credits)
    - fired monitoring alerts to admins (hooked from routers/alerts_api.py)
    - the Notification Settings page's "send test" button

Behavior:
    - Delivers through the ACTIVE row in `email_providers` (the provider system
      managed by email_provider_api.py). Microsoft 365 OAuth2 is the tested
      path and is reused verbatim via email_alerts.EmailAlertService
      (MSAL token + Graph sendMail). SMTP/SendGrid-style rows reuse the same
      request shapes as email_service.py.
    - Checks the caller's saved preferences in `user_notification_preferences`
      (the table notification_preferences_api.py reads/writes) before sending,
      unless force=True (explicit "send me a test email" clicks).
    - Rate-limits to max 1 email per (recipient, event_type) per hour via
      Redis (fail-open on Redis errors, matching alert_triggers.py).
    - Wraps content in a light branded shell consistent with the Keycloak
      email theme (keycloak-theme/uc-1-pro/email).

send_notification() NEVER raises: every failure path returns
{"sent": False, "provider": ..., "error"/"skipped": ...}. Hooks in hot paths
must still wrap their calls in try/except so this module can never break the
host path even at import time.

Created: 2026-07-02 (Track T7 — notification email delivery)
"""

import asyncio
import html as _html_mod
import inspect
import json
import logging
import os
import re
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import httpx
import redis.asyncio as aioredis

from database import get_db_connection

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (same env conventions as email_alerts.py / website_monitor.py)
# ---------------------------------------------------------------------------

_APP_URL = os.getenv("APP_URL", "https://unicorncommander.ai")
_SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@unicorncommander.ai")
# Existing admin-recipient convention (backup_scheduler.py / website_monitor.py)
_ADMIN_EMAIL_ENV = os.getenv("ADMIN_EMAIL", "admin@example.com")

# Max 1 email per (recipient, event_type) per hour
RATE_LIMIT_SECONDS = 3600

# Which saved-preference toggle gates each event type (see
# notification_preferences_api.NotificationPreferences for the field set).
_EVENT_PREF_FIELD = {
    "low_credit": "usage_alerts_enabled",
    "usage": "usage_alerts_enabled",
    "alert_fired": "hardware_alerts_enabled",
    "hardware": "hardware_alerts_enabled",
    "billing": "billing_alerts_enabled",
    "security": "security_alerts_enabled",
}

# Defaults mirror notification_preferences_api.NotificationPreferences
_PREF_DEFAULTS = {
    "usage_alerts_enabled": True,
    "hardware_alerts_enabled": True,
    "billing_alerts_enabled": True,
    "security_alerts_enabled": True,
    "alert_frequency": "immediate",
    "email_enabled": True,
    "email": None,
}

_redis_client: Optional[aioredis.Redis] = None


def _get_redis() -> aioredis.Redis:
    """Lazy per-process async Redis client (same env vars as the rest of the app)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.Redis(
            host=os.getenv("REDIS_HOST", "unicorn-redis"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
    return _redis_client


@asynccontextmanager
async def _db():
    """
    Acquire a DB connection compatibly across deployments (same shim as
    notification_preferences_api.py: pool-backed package on the running nodes,
    plain asyncpg connection in other checkouts).
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
# Preferences / rate limit
# ---------------------------------------------------------------------------

async def _load_prefs(user_id: Optional[str]) -> Dict:
    """Load the user's saved notification preferences over defaults."""
    merged = dict(_PREF_DEFAULTS)
    if not user_id:
        return merged
    try:
        async with _db() as conn:
            row = await conn.fetchrow(
                "SELECT preferences FROM user_notification_preferences WHERE user_id = $1",
                user_id,
            )
        if row and row["preferences"]:
            raw = row["preferences"]
            stored = raw if isinstance(raw, dict) else json.loads(raw)
            for key in merged:
                if key in stored and stored[key] is not None:
                    merged[key] = stored[key]
    except Exception as e:
        # Missing table / DB hiccup: fall back to defaults (send)
        logger.warning(f"Could not load notification preferences for {user_id}: {e}")
    return merged


def _rate_key(recipient: str, event_type: str) -> str:
    return f"notify:ratelimit:{event_type}:{recipient.strip().lower()}"


async def _is_rate_limited(recipient: str, event_type: str) -> bool:
    """True if an email of this type went to this recipient within the hour."""
    try:
        return bool(await _get_redis().exists(_rate_key(recipient, event_type)))
    except Exception as e:
        # Fail-open, matching alert_triggers.py cooldown behavior
        logger.warning(f"Redis rate-limit check failed (allowing send): {e}")
        return False


async def _mark_sent(recipient: str, event_type: str) -> None:
    try:
        await _get_redis().setex(
            _rate_key(recipient, event_type),
            RATE_LIMIT_SECONDS,
            datetime.utcnow().isoformat() + "Z",
        )
    except Exception as e:
        logger.warning(f"Redis rate-limit mark failed: {e}")


# ---------------------------------------------------------------------------
# Branded wrapper (tone/palette from keycloak-theme/uc-1-pro/email templates)
# ---------------------------------------------------------------------------

def build_branded_html(
    subject: str,
    body_html: str,
    cta_label: Optional[str] = None,
    cta_url: Optional[str] = None,
) -> str:
    """
    Wrap a content fragment in the light, table-based shell used by the
    Keycloak email theme: neutral #f4f4f7 background, white card, purple
    brand header, quiet footer.
    """
    cta_block = ""
    if cta_label and cta_url:
        cta_block = (
            '<tr><td align="center" style="padding:24px 32px;">'
            f'<a href="{_html_mod.escape(cta_url, quote=True)}" '
            'style="background:#6d28d9;color:#ffffff;text-decoration:none;'
            'padding:13px 30px;border-radius:8px;font-size:15px;font-weight:600;'
            f'display:inline-block;">{_html_mod.escape(cta_label)}</a>'
            "</td></tr>"
        )
    prefs_url = f"{_APP_URL}/admin/account/notification-settings"
    return f"""<html>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#2a2a35;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="520" cellpadding="0" cellspacing="0" style="max-width:520px;width:100%;background:#ffffff;border:1px solid #ececf0;border-radius:12px;">
        <tr><td style="padding:28px 32px 8px;font-size:18px;font-weight:600;color:#5b21b6;">Unicorn Commander</td></tr>
        <tr><td style="padding:8px 32px 0;font-size:16px;font-weight:600;color:#2a2a35;">{_html_mod.escape(subject)}</td></tr>
        <tr><td style="padding:10px 32px 8px;font-size:15px;line-height:1.6;">
          {body_html}
        </td></tr>
        {cta_block}
        <tr><td style="padding:18px 32px 26px;border-top:1px solid #ececf0;font-size:12px;color:#9a9aa5;">
          Unicorn Commander &middot; automated notification &middot;
          <a href="{prefs_url}" style="color:#5b21b6;text-decoration:none;">manage notification preferences</a><br>
          Questions? <a href="mailto:{_SUPPORT_EMAIL}" style="color:#5b21b6;text-decoration:none;">{_SUPPORT_EMAIL}</a>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _fallback_text(subject: str, body_html: str) -> str:
    """Derive a plain-text alternative when the caller didn't supply one."""
    text = re.sub(r"<br\s*/?>", "\n", body_html, flags=re.I)
    text = re.sub(r"</p>", "\n\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = _html_mod.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return f"{subject}\n\n{text}\n\n-- Unicorn Commander (automated notification)"


# ---------------------------------------------------------------------------
# Provider loading + send paths
# ---------------------------------------------------------------------------

async def _load_active_provider() -> Optional[Dict]:
    """Return the enabled email_providers row as a dict, or None."""
    try:
        async with _db() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM email_providers WHERE enabled = true LIMIT 1"
            )
        return dict(row) if row else None
    except Exception as e:
        # Missing table on this deployment, or DB down
        logger.warning(f"Could not load active email provider: {e}")
        return None


def _sync_m365_service_from_row(provider: Optional[Dict]):
    """
    Point the shared EmailAlertService at the ACTIVE provider row's
    Microsoft 365 credentials (the service snapshots config at import time;
    an admin may have configured/rotated the provider since startup).
    """
    from email_alerts import email_alert_service

    if provider:
        client_id = provider.get("oauth2_client_id")
        tenant_id = provider.get("oauth2_tenant_id")
        client_secret = provider.get("oauth2_client_secret")
        sender = provider.get("smtp_from")
        changed = False
        if client_id and client_id != email_alert_service.ms365_client_id:
            email_alert_service.ms365_client_id = client_id
            changed = True
        if tenant_id and tenant_id != email_alert_service.ms365_tenant_id:
            email_alert_service.ms365_tenant_id = tenant_id
            changed = True
        if client_secret and client_secret != email_alert_service.ms365_client_secret:
            email_alert_service.ms365_client_secret = client_secret
            changed = True
        if sender and sender != email_alert_service.email_from:
            email_alert_service.email_from = sender
        if changed:
            # Force MSAL re-auth with the fresh credentials
            email_alert_service._msal_app = None
            email_alert_service._access_token = None
            email_alert_service._token_expires_at = None
    return email_alert_service


async def _send_m365(provider: Optional[Dict], recipient: str, subject: str,
                     full_html: str) -> Tuple[bool, Optional[str]]:
    """Send via the tested Microsoft 365 OAuth2 path (email_alerts.py)."""
    service = _sync_m365_service_from_row(provider)

    if not all([service.ms365_client_id, service.ms365_tenant_id,
                service.ms365_client_secret]):
        return False, "Microsoft 365 provider is missing OAuth2 credentials"

    # Respect the service's global 100/hour limiter, like send_alert() does
    if not service.rate_limiter.can_send():
        return False, "Email system hourly rate limit reached (100/hour)"

    try:
        ok = await service._send_via_microsoft365(
            recipients=[recipient],
            subject=subject,
            html_content=full_html,
        )
    except Exception as e:
        return False, f"Microsoft 365 send failed: {e}"

    if ok:
        service.rate_limiter.record_send()
        return True, None
    return False, "Microsoft Graph API rejected the send (see server logs)"


async def _send_smtp_row(provider: Dict, recipient: str, subject: str,
                         full_html: str, text: str) -> Tuple[bool, Optional[str]]:
    """SMTP send using the provider row's credentials (email_service.py shape)."""
    import aiosmtplib
    from email.message import EmailMessage

    host = provider.get("smtp_host")
    port = int(provider.get("smtp_port") or 587)
    username = provider.get("smtp_user")
    password = provider.get("smtp_password")
    sender = provider.get("smtp_from") or username

    if not all([host, username, password]):
        return False, "SMTP provider is missing host/user/password"

    message = EmailMessage()
    message["From"] = f"Unicorn Commander <{sender}>"
    message["To"] = recipient
    message["Subject"] = subject
    message["Reply-To"] = _SUPPORT_EMAIL
    message.set_content(text)
    message.add_alternative(full_html, subtype="html")

    try:
        # Same TLS posture as email_service._send_via_smtp (587 = STARTTLS)
        if port == 465:
            await aiosmtplib.send(message, hostname=host, port=port,
                                  username=username, password=password,
                                  use_tls=True)
        else:
            await aiosmtplib.send(message, hostname=host, port=port,
                                  username=username, password=password,
                                  start_tls=True)
        return True, None
    except Exception as e:
        return False, f"SMTP send failed: {type(e).__name__}: {e}"


async def _send_sendgrid_row(provider: Dict, recipient: str, subject: str,
                             full_html: str, text: str) -> Tuple[bool, Optional[str]]:
    """SendGrid send using the provider row's API key (email_service.py shape)."""
    api_key = provider.get("api_key")
    sender = provider.get("smtp_from")
    if not api_key or not sender:
        return False, "SendGrid provider is missing api_key or from-address"

    payload = {
        "personalizations": [{"to": [{"email": recipient}]}],
        "from": {"email": sender, "name": "Unicorn Commander"},
        "reply_to": {"email": _SUPPORT_EMAIL},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text},
            {"type": "text/html", "value": full_html},
        ],
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {api_key}",
                         "Content-Type": "application/json"},
                json=payload,
                timeout=10.0,
            )
        if resp.status_code in (200, 202):
            return True, None
        return False, f"SendGrid API error {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, f"SendGrid send failed: {type(e).__name__}: {e}"


async def _deliver(recipient: str, event_type: str, subject: str,
                   full_html: str, text: str) -> Dict:
    """Resolve the active provider and deliver one email through it."""
    provider = await _load_active_provider()
    provider_type = provider.get("provider_type") if provider else None

    if provider is None:
        # No DB row: the M365 service may still be configured via env vars
        # (email_alerts.py supports env-first config)
        from email_alerts import email_alert_service
        if all([email_alert_service.ms365_client_id,
                email_alert_service.ms365_tenant_id,
                email_alert_service.ms365_client_secret]):
            provider_type = "microsoft365"
        else:
            return {
                "sent": False,
                "provider": None,
                "error": ("No active email provider configured. "
                          "Configure one under System > Email."),
            }

    if provider_type == "microsoft365":
        ok, err = await _send_m365(provider, recipient, subject, full_html)
    elif provider_type == "sendgrid":
        ok, err = await _send_sendgrid_row(provider, recipient, subject, full_html, text)
    elif provider and provider.get("smtp_host"):
        # custom_smtp / google-app-password style rows
        ok, err = await _send_smtp_row(provider, recipient, subject, full_html, text)
    else:
        ok, err = False, (
            f"Email delivery for provider type '{provider_type}' is not "
            "supported yet (supported: microsoft365, sendgrid, SMTP-based)"
        )

    # Record in the shared email_logs history (best-effort, never raises here)
    try:
        from email_alerts import email_alert_service
        await asyncio.to_thread(
            email_alert_service.log_email_send,
            event_type, [recipient], subject, "sent" if ok else "failed",
        )
    except Exception as log_exc:
        logger.debug(f"email_logs write skipped: {log_exc}")

    if ok:
        return {"sent": True, "provider": provider_type, "error": None}
    return {"sent": False, "provider": provider_type, "error": err}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def send_notification(
    user_email: str,
    event_type: str,
    subject: str,
    html: str,
    text: Optional[str] = None,
    *,
    user_id: Optional[str] = None,
    force: bool = False,
    cta_label: Optional[str] = None,
    cta_url: Optional[str] = None,
) -> Dict:
    """
    Send one notification email through the active email provider.

    Args:
        user_email: recipient address (may be overridden by the address saved
                    in the user's notification preferences when user_id given)
        event_type: e.g. "low_credit", "alert_fired", "test_usage" — used for
                    preference gating and the per-recipient hourly rate limit
        subject:    email subject line
        html:       CONTENT FRAGMENT (gets wrapped in the branded shell)
        text:       plain-text alternative (derived from html if omitted)
        user_id:    Keycloak user id, enables preference lookup
        force:      skip preference gating and rate limit (explicit user
                    action, e.g. the settings page "send test" button)
        cta_label/cta_url: optional button in the branded shell

    Returns (never raises):
        {"sent": bool, "provider": str|None, "recipient": str,
         "error": str|None, "skipped": str|None}
    """
    result = {"sent": False, "provider": None, "recipient": user_email,
              "error": None, "skipped": None}
    try:
        recipient = (user_email or "").strip()

        if not force:
            prefs = await _load_prefs(user_id)
            # The settings page lets users route notifications to a different
            # address than their login email — honor it.
            if user_id and prefs.get("email"):
                recipient = str(prefs["email"]).strip()
                result["recipient"] = recipient
            if not prefs.get("email_enabled", True):
                result["skipped"] = "email notifications disabled in user preferences"
                return result
            pref_field = _EVENT_PREF_FIELD.get(event_type)
            if pref_field and not prefs.get(pref_field, True):
                result["skipped"] = f"{pref_field} is off in user preferences"
                return result
            if prefs.get("alert_frequency", "immediate") != "immediate":
                # Digest delivery does not exist yet; honor the user's
                # "not immediate" choice rather than emailing anyway.
                result["skipped"] = (
                    f"user prefers {prefs.get('alert_frequency')} digest "
                    "(real-time email suppressed; digests not implemented)"
                )
                return result

        if not recipient or "@" not in recipient:
            result["error"] = "No valid recipient email address"
            return result

        if not force and await _is_rate_limited(recipient, event_type):
            result["skipped"] = (
                f"rate limited (max 1 '{event_type}' email per hour per recipient)"
            )
            return result

        body_text = text or _fallback_text(subject, html)
        full_html = build_branded_html(subject, html, cta_label, cta_url)

        outcome = await _deliver(recipient, event_type, subject, full_html, body_text)
        result.update(outcome)

        if result["sent"]:
            await _mark_sent(recipient, event_type)
            logger.info(
                f"Notification '{event_type}' sent to {recipient} "
                f"via {result['provider']}"
            )
        else:
            logger.warning(
                f"Notification '{event_type}' to {recipient} NOT sent: "
                f"{result.get('error')}"
            )
        return result

    except Exception as e:
        logger.error(f"send_notification failed: {e}", exc_info=True)
        result["error"] = f"{type(e).__name__}: {e}"
        return result


# ---------------------------------------------------------------------------
# Event helpers used by the append-only hooks
# ---------------------------------------------------------------------------

LOW_CREDIT_FRACTION = 0.10  # notify when balance crosses below 10% of allocation


async def maybe_notify_low_credit(
    user_id: str,
    previous_balance: float,
    new_balance: float,
    db_pool=None,
) -> Optional[Dict]:
    """
    Called (fire-and-forget) from the credit deduction path after a balance
    update. Sends a low-credit email only when the balance CROSSED below 10%
    of the user's allocation with this deduction. Never raises.
    """
    try:
        if not user_id or user_id.startswith("org_"):
            return None

        allocated = None
        try:
            if db_pool is not None:
                async with db_pool.acquire() as conn:
                    allocated = await conn.fetchval(
                        "SELECT credits_allocated FROM user_credits WHERE user_id = $1",
                        user_id,
                    )
            else:
                async with _db() as conn:
                    allocated = await conn.fetchval(
                        "SELECT credits_allocated FROM user_credits WHERE user_id = $1",
                        user_id,
                    )
        except Exception as e:
            logger.debug(f"low-credit check: allocation lookup failed for {user_id}: {e}")
            return None

        if not allocated:
            return None
        allocated = float(allocated)
        if allocated <= 0:
            return None

        threshold = allocated * LOW_CREDIT_FRACTION
        if not (previous_balance >= threshold and new_balance < threshold):
            return None  # did not cross the line on this deduction

        # Resolve the user's email from Keycloak (existing helper)
        email = None
        try:
            from keycloak_integration import get_user_by_id
            kc_user = await get_user_by_id(user_id)
            if kc_user:
                email = kc_user.get("email")
        except Exception as e:
            logger.warning(f"low-credit notify: Keycloak lookup failed for {user_id}: {e}")
        if not email:
            logger.info(f"low-credit notify: no email on record for user {user_id}")
            return None

        pct = (new_balance / allocated) * 100 if allocated else 0.0
        subject = "Your credit balance is running low"
        body = (
            f"<p style=\"margin:0 0 14px;\">Your Unicorn Commander credit balance "
            f"just dropped below 10% of your allocation.</p>"
            f"<p style=\"margin:0 0 14px;\"><strong>{new_balance:.2f}</strong> of "
            f"<strong>{allocated:.2f}</strong> credits remaining "
            f"({pct:.1f}%).</p>"
            f"<p style=\"margin:0 0 14px;\">Once your balance reaches zero, API "
            f"requests that use platform credits will be declined until your "
            f"credits reset or you top up.</p>"
        )
        text = (
            "Your Unicorn Commander credit balance just dropped below 10% of "
            f"your allocation.\n\n{new_balance:.2f} of {allocated:.2f} credits "
            f"remaining ({pct:.1f}%).\n\nOnce your balance reaches zero, API "
            "requests that use platform credits will be declined until your "
            "credits reset or you top up."
        )
        return await send_notification(
            email,
            "low_credit",
            subject,
            body,
            text,
            user_id=user_id,
            cta_label="Review your plan",
            cta_url=f"{_APP_URL}/admin/subscription/plan",
        )
    except Exception as e:
        logger.error(f"maybe_notify_low_credit failed (non-blocking): {e}")
        return None


def _admin_recipients() -> List[str]:
    """Admin notification recipients — existing ADMIN_EMAIL env convention
    (see website_monitor.py / backup_scheduler.py). Comma-separated allowed."""
    return [e.strip() for e in _ADMIN_EMAIL_ENV.split(",") if e.strip()]


async def notify_admins_alert_fired(alerts: List[Dict]) -> List[Dict]:
    """
    Called (fire-and-forget) when new monitoring alerts fire (rows inserted as
    'active' by the alerts sync). Emails the configured admin recipient(s).
    Rate limiting (1 'alert_fired' email per recipient per hour) applies.
    Never raises.
    """
    results: List[Dict] = []
    try:
        if not alerts:
            return results

        count = len(alerts)
        if count == 1:
            subject = f"Monitoring alert fired: {alerts[0].get('name', 'unknown')}"
        else:
            subject = f"{count} monitoring alerts fired"

        items = []
        for a in alerts[:10]:
            name = _html_mod.escape(str(a.get("name", "unknown")))
            severity = _html_mod.escape(str(a.get("severity", "warning")).upper())
            message = _html_mod.escape(str(a.get("message") or ""))
            sev_color = "#b91c1c" if severity == "CRITICAL" else "#b45309"
            items.append(
                f"<li style=\"margin:0 0 8px;\"><span style=\"color:{sev_color};"
                f"font-weight:600;\">[{severity}]</span> {name}"
                + (f" &mdash; {message}" if message else "")
                + "</li>"
            )
        more = count - min(count, 10)
        body = (
            "<p style=\"margin:0 0 14px;\">New monitoring alert"
            + ("s are" if count != 1 else " is")
            + " active on your Ops Center:</p>"
            "<ul style=\"margin:0 0 14px;padding-left:20px;\">"
            + "".join(items)
            + "</ul>"
            + (f"<p style=\"margin:0 0 14px;\">…and {more} more.</p>" if more > 0 else "")
        )
        text_lines = [
            f"[{str(a.get('severity', 'warning')).upper()}] {a.get('name', 'unknown')}"
            + (f" - {a.get('message')}" if a.get("message") else "")
            for a in alerts[:10]
        ]
        text = (
            "New monitoring alerts are active on your Ops Center:\n\n"
            + "\n".join(text_lines)
            + (f"\n...and {more} more." if more > 0 else "")
        )

        for admin_email in _admin_recipients():
            res = await send_notification(
                admin_email,
                "alert_fired",
                subject,
                body,
                text,
                cta_label="Open monitoring",
                cta_url=f"{_APP_URL}/admin/monitoring/overview",
            )
            results.append(res)
        return results
    except Exception as e:
        logger.error(f"notify_admins_alert_fired failed (non-blocking): {e}")
        return results
