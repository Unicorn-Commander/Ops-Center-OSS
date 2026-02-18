"""
Email Alert System for Ops-Center
Version: 1.0.0
Author: Email Notification Specialist
Date: November 29, 2025

Purpose: Production-ready email alert notification system using Microsoft 365 OAuth.

Features:
- Microsoft 365 OAuth2 authentication via MSAL
- Four alert types: System Critical, Billing, Security, Usage
- HTML email templates with mobile responsiveness
- Rate limiting (max 100 emails/hour)
- Retry logic with exponential backoff
- Comprehensive logging
- Template caching for performance
"""

import os
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
import asyncio
from jinja2 import Environment, FileSystemLoader, Template
import psycopg2
from psycopg2.extras import RealDictCursor
import httpx
from msal import ConfidentialClientApplication

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self, max_emails_per_hour: int = 100):
        self.max_emails_per_hour = max_emails_per_hour
        self.email_timestamps: List[float] = []

    def can_send(self) -> bool:
        """Check if we can send another email without exceeding rate limit"""
        now = time.time()
        hour_ago = now - 3600

        # Remove timestamps older than 1 hour
        self.email_timestamps = [ts for ts in self.email_timestamps if ts > hour_ago]

        # Check if under limit
        return len(self.email_timestamps) < self.max_emails_per_hour

    def record_send(self):
        """Record that an email was sent"""
        self.email_timestamps.append(time.time())

    def get_remaining(self) -> int:
        """Get remaining emails before hitting rate limit"""
        now = time.time()
        hour_ago = now - 3600
        self.email_timestamps = [ts for ts in self.email_timestamps if ts > hour_ago]
        return self.max_emails_per_hour - len(self.email_timestamps)


class EmailAlertService:
    """
    Email alert sender using Microsoft 365 OAuth2

    Configuration via environment variables or database settings:
    - EMAIL_PROVIDER: "microsoft365"
    - EMAIL_FROM: Sender email address
    - MS365_CLIENT_ID: Azure AD application client ID
    - MS365_TENANT_ID: Azure AD tenant ID
    - MS365_CLIENT_SECRET: Azure AD application client secret
    """

    def __init__(self):
        # Configuration
        self.email_from = os.getenv("EMAIL_FROM", "admin@example.com")
        self.ms365_client_id = os.getenv("MS365_CLIENT_ID")
        self.ms365_tenant_id = os.getenv("MS365_TENANT_ID")
        self.ms365_client_secret = os.getenv("MS365_CLIENT_SECRET")

        # Database configuration (fallback if env vars not set)
        self.db_config = None
        self.load_config_from_db()

        # Template setup
        self.template_dir = Path(__file__).parent / "email_templates"
        self.template_dir.mkdir(exist_ok=True)

        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )

        # Rate limiting
        self.rate_limiter = RateLimiter(max_emails_per_hour=100)

        # MSAL app for Microsoft OAuth
        self._msal_app = None
        self._access_token = None
        self._token_expires_at = None

        logger.info(f"EmailAlertService initialized (from: {self.email_from})")

    def load_config_from_db(self):
        """Load email configuration from database if env vars not set"""
        if self.ms365_client_id and self.ms365_tenant_id and self.ms365_client_secret:
            return  # Already configured via env vars

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT * FROM email_providers
                WHERE enabled = true AND provider_type = 'microsoft365'
                LIMIT 1
            """)
            provider = cursor.fetchone()

            cursor.close()
            conn.close()

            if provider:
                self.ms365_client_id = provider.get('oauth2_client_id')
                self.ms365_tenant_id = provider.get('oauth2_tenant_id')
                self.ms365_client_secret = provider.get('oauth2_client_secret')
                self.email_from = provider.get('smtp_from') or self.email_from
                self.db_config = dict(provider)
                logger.info("Loaded email configuration from database")
        except Exception as e:
            logger.warning(f"Could not load email config from database: {e}")

    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'unicorn-postgresql'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'unicorn'),
            password=os.getenv('POSTGRES_PASSWORD', 'unicorn'),
            database=os.getenv('POSTGRES_DB', 'unicorn_db')
        )

    def get_msal_app(self) -> ConfidentialClientApplication:
        """Get or create MSAL application instance"""
        if not self._msal_app:
            if not all([self.ms365_client_id, self.ms365_tenant_id, self.ms365_client_secret]):
                raise ValueError("Microsoft 365 OAuth credentials not configured")

            authority = f"https://login.microsoftonline.com/{self.ms365_tenant_id}"
            self._msal_app = ConfidentialClientApplication(
                client_id=self.ms365_client_id,
                client_credential=self.ms365_client_secret,
                authority=authority
            )

        return self._msal_app

    async def get_access_token(self) -> str:
        """Get Microsoft Graph API access token (with caching)"""
        # Check if token is still valid
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):
                return self._access_token

        # Acquire new token
        app = self.get_msal_app()
        scopes = ["https://graph.microsoft.com/.default"]

        result = app.acquire_token_for_client(scopes=scopes)

        if "access_token" in result:
            self._access_token = result["access_token"]
            expires_in = result.get("expires_in", 3600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            logger.info("Acquired new Microsoft Graph access token")
            return self._access_token
        else:
            error = result.get("error_description", result.get("error", "Unknown error"))
            raise Exception(f"Failed to acquire access token: {error}")

    def get_template(self, alert_type: str) -> Template:
        """
        Load HTML email template

        Args:
            alert_type: "system_critical", "billing", "security", "usage"

        Returns:
            Jinja2 Template object
        """
        template_name = f"alert_{alert_type}.html"

        try:
            return self.jinja_env.get_template(template_name)
        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {e}")
            # Fallback to base template
            return self.jinja_env.get_template("base_template.html")

    async def send_alert(
        self,
        alert_type: str,
        subject: str,
        message: str,
        recipients: List[str],
        context: Optional[Dict[str, Any]] = None,
        retry_count: int = 3
    ) -> bool:
        """
        Send email alert using Microsoft 365 OAuth

        Args:
            alert_type: "system_critical", "billing", "security", "usage"
            subject: Email subject line
            message: Email body (can include basic HTML)
            recipients: List of email addresses
            context: Template context data (optional)
            retry_count: Number of retry attempts (default: 3)

        Returns:
            True if sent successfully, False otherwise
        """
        # Rate limiting check
        if not self.rate_limiter.can_send():
            logger.warning(f"Rate limit exceeded. {self.rate_limiter.get_remaining()} emails remaining.")
            return False

        # Build template context
        template_context = {
            "subject": subject,
            "message": message,
            "alert_type": alert_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dashboard_url": os.getenv("APP_URL", "https://unicorncommander.ai"),
            "support_email": os.getenv("SUPPORT_EMAIL", "support@unicorncommander.ai"),
            **(context or {})
        }

        # Render HTML template
        try:
            template = self.get_template(alert_type)
            html_content = template.render(**template_context)
        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            html_content = f"<html><body><h1>{subject}</h1><p>{message}</p></body></html>"

        # Send email with retry logic
        for attempt in range(retry_count):
            try:
                success = await self._send_via_microsoft365(
                    recipients=recipients,
                    subject=subject,
                    html_content=html_content
                )

                if success:
                    self.rate_limiter.record_send()
                    self.log_email_send(alert_type, recipients, subject, "sent")
                    return True

            except Exception as e:
                logger.error(f"Email send attempt {attempt + 1} failed: {e}")

                if attempt < retry_count - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

        # All retries failed
        self.log_email_send(alert_type, recipients, subject, "failed")
        return False

    async def _send_via_microsoft365(
        self,
        recipients: List[str],
        subject: str,
        html_content: str
    ) -> bool:
        """
        Send email via Microsoft Graph API

        Args:
            recipients: List of email addresses
            subject: Email subject
            html_content: HTML email body

        Returns:
            True if successful, False otherwise
        """
        # Get access token
        try:
            access_token = await self.get_access_token()
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise

        # Build Graph API request
        url = f"https://graph.microsoft.com/v1.0/users/{self.email_from}/sendMail"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Build email message
        to_recipients = [{"emailAddress": {"address": email}} for email in recipients]

        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": html_content
                },
                "toRecipients": to_recipients
            },
            "saveToSentItems": "true"
        }

        # Send request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)

            if response.status_code == 202:
                logger.info(f"Email sent successfully to {len(recipients)} recipients")
                return True
            else:
                logger.error(f"Microsoft Graph API error: {response.status_code} - {response.text}")
                return False

    def log_email_send(
        self,
        alert_type: str,
        recipients: List[str],
        subject: str,
        status: str
    ):
        """
        Log email send to database

        Args:
            alert_type: Alert type
            recipients: List of email addresses
            subject: Email subject
            status: "sent" or "failed"
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            for recipient in recipients:
                cursor.execute("""
                    INSERT INTO email_logs (
                        recipient, subject, alert_type, status, sent_at
                    ) VALUES (%s, %s, %s, %s, NOW())
                """, (recipient, subject, alert_type, status))

            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to log email send: {e}")

    # Convenience methods for specific alert types

    async def send_critical_alert(
        self,
        subject: str,
        message: str,
        recipients: List[str],
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send system critical alert (server down, high CPU, disk full, etc.)"""
        context = {
            "alert_level": "CRITICAL",
            "color": "#dc3545",
            **(details or {})
        }
        return await self.send_alert("system_critical", subject, message, recipients, context)

    async def send_billing_alert(
        self,
        subject: str,
        message: str,
        recipients: List[str],
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send billing alert (payment failed, subscription expiring, quota exceeded)"""
        context = {
            "alert_level": "BILLING",
            "color": "#ffc107",
            **(details or {})
        }
        return await self.send_alert("billing", subject, message, recipients, context)

    async def send_security_alert(
        self,
        subject: str,
        message: str,
        recipients: List[str],
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send security alert (failed logins, unauthorized access, API key leaked)"""
        context = {
            "alert_level": "SECURITY",
            "color": "#e74c3c",
            **(details or {})
        }
        return await self.send_alert("security", subject, message, recipients, context)

    async def send_usage_alert(
        self,
        subject: str,
        message: str,
        recipients: List[str],
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send usage alert (API quota warning, quota exceeded, tier upgrade suggestion)"""
        context = {
            "alert_level": "USAGE",
            "color": "#17a2b8",
            **(details or {})
        }
        return await self.send_alert("usage", subject, message, recipients, context)


# Singleton instance
email_alert_service = EmailAlertService()
