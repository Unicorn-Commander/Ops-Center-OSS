"""
Email Service for UC-1 Pro Ops Center
Handles transactional emails for subscription events
"""

import os
import logging
from typing import Dict, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending transactional emails"""

    def __init__(self):
        # Email configuration from environment
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
        self.provider = os.getenv("EMAIL_PROVIDER", "console")  # console, sendgrid, mailgun, smtp

        # Provider credentials
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.mailgun_api_key = os.getenv("MAILGUN_API_KEY")
        self.mailgun_domain = os.getenv("MAILGUN_DOMAIN")
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")

        # Email settings
        self.from_email = os.getenv("EMAIL_FROM", "noreply@your-domain.com")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "Unicorn Commander")
        self.reply_to = os.getenv("EMAIL_REPLY_TO", "support@your-domain.com")

        logger.info(f"Email service initialized: provider={self.provider}, enabled={self.enabled}")

    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send email using configured provider

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"[EMAIL DISABLED] Would send to {to}: {subject}")
            logger.debug(f"Email content: {html_content}")
            return True

        try:
            if self.provider == "console":
                # Console logger for development
                logger.info(f"[EMAIL] To: {to}")
                logger.info(f"[EMAIL] Subject: {subject}")
                logger.info(f"[EMAIL] Content:\n{html_content}")
                return True

            elif self.provider == "sendgrid":
                return await self._send_via_sendgrid(to, subject, html_content, text_content)

            elif self.provider == "mailgun":
                return await self._send_via_mailgun(to, subject, html_content, text_content)

            elif self.provider == "smtp":
                return await self._send_via_smtp(to, subject, html_content, text_content)

            else:
                logger.error(f"Unknown email provider: {self.provider}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {type(e).__name__}: {e}")
            return False

    async def _send_via_sendgrid(
        self, to: str, subject: str, html_content: str, text_content: Optional[str]
    ) -> bool:
        """Send email via SendGrid API"""
        if not self.sendgrid_api_key:
            logger.error("SendGrid API key not configured")
            return False

        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {self.sendgrid_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": self.from_email, "name": self.from_name},
            "reply_to": {"email": self.reply_to},
            "subject": subject,
            "content": [
                {"type": "text/html", "value": html_content}
            ]
        }

        if text_content:
            payload["content"].insert(0, {"type": "text/plain", "value": text_content})

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)

            if response.status_code in [200, 202]:
                logger.info(f"Email sent successfully via SendGrid to {to}")
                return True
            else:
                logger.error(f"SendGrid API error: {response.status_code} - {response.text}")
                return False

    async def _send_via_mailgun(
        self, to: str, subject: str, html_content: str, text_content: Optional[str]
    ) -> bool:
        """Send email via Mailgun API"""
        if not self.mailgun_api_key or not self.mailgun_domain:
            logger.error("Mailgun API key or domain not configured")
            return False

        url = f"https://api.mailgun.net/v3/{self.mailgun_domain}/messages"
        auth = ("api", self.mailgun_api_key)

        data = {
            "from": f"{self.from_name} <{self.from_email}>",
            "to": to,
            "subject": subject,
            "html": html_content
        }

        if text_content:
            data["text"] = text_content

        async with httpx.AsyncClient() as client:
            response = await client.post(url, auth=auth, data=data, timeout=10.0)

            if response.status_code == 200:
                logger.info(f"Email sent successfully via Mailgun to {to}")
                return True
            else:
                logger.error(f"Mailgun API error: {response.status_code} - {response.text}")
                return False

    async def _send_via_smtp(
        self, to: str, subject: str, html_content: str, text_content: Optional[str]
    ) -> bool:
        """Send email via SMTP"""
        import aiosmtplib
        from email.message import EmailMessage

        if not all([self.smtp_host, self.smtp_username, self.smtp_password]):
            logger.error("SMTP credentials not configured")
            return False

        message = EmailMessage()
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = to
        message["Subject"] = subject
        message["Reply-To"] = self.reply_to

        if text_content:
            message.set_content(text_content)
            message.add_alternative(html_content, subtype="html")
        else:
            message.set_content(html_content, subtype="html")

        try:
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                use_tls=True
            )
            logger.info(f"Email sent successfully via SMTP to {to}")
            return True
        except Exception as e:
            logger.error(f"SMTP send error: {type(e).__name__}: {e}")
            return False

    # ===== TEMPLATE METHODS =====

    async def send_subscription_confirmation(
        self,
        to: str,
        tier: str,
        amount: float,
        period_end: Optional[str] = None
    ) -> bool:
        """Send subscription confirmation email"""
        subject = f"Welcome to Unicorn Commander {tier.title()}!"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">🦄 Unicorn Commander</h1>
            </div>

            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333;">Subscription Confirmed!</h2>

                <p style="color: #666; font-size: 16px;">
                    Thank you for subscribing to <strong>{tier.title()}</strong> tier!
                </p>

                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <table style="width: 100%;">
                        <tr>
                            <td style="padding: 10px;"><strong>Tier:</strong></td>
                            <td style="padding: 10px;">{tier.title()}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px;"><strong>Amount:</strong></td>
                            <td style="padding: 10px;">${amount:.2f}/month</td>
                        </tr>
                        {f'<tr><td style="padding: 10px;"><strong>Next Billing:</strong></td><td style="padding: 10px;">{period_end}</td></tr>' if period_end else ''}
                    </table>
                </div>

                <p style="color: #666;">
                    You now have access to all {tier} features including:
                </p>
                <ul style="color: #666;">
                    <li>Open-WebUI Chat Interface</li>
                    <li>Center-Deep AI Search</li>
                    <li>50+ AI Models via OpenRouter</li>
                    <li>Bring Your Own Key (BYOK) Support</li>
                    <li>Priority Support</li>
                </ul>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://your-domain.com/dashboard"
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Go to Dashboard
                    </a>
                </div>

                <p style="color: #999; font-size: 14px; border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px;">
                    Questions? Contact us at <a href="mailto:support@your-domain.com">support@your-domain.com</a>
                </p>
            </div>
        </body>
        </html>
        """

        return await self.send_email(to, subject, html_content)

    async def send_subscription_updated(
        self,
        to: str,
        old_tier: str,
        new_tier: str,
        amount: float
    ) -> bool:
        """Send subscription update email"""
        subject = f"Subscription Updated to {new_tier.title()}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">🦄 Unicorn Commander</h1>
            </div>

            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333;">Subscription Updated</h2>

                <p style="color: #666; font-size: 16px;">
                    Your subscription has been updated from <strong>{old_tier.title()}</strong> to <strong>{new_tier.title()}</strong>.
                </p>

                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>New Plan:</strong> {new_tier.title()}</p>
                    <p><strong>New Price:</strong> ${amount:.2f}/month</p>
                </div>

                <p style="color: #666;">
                    Your new features and limits are now active.
                </p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://your-domain.com/dashboard"
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Dashboard
                    </a>
                </div>
            </div>
        </body>
        </html>
        """

        return await self.send_email(to, subject, html_content)

    async def send_subscription_canceled(
        self,
        to: str,
        tier: str,
        end_date: str
    ) -> bool:
        """Send subscription cancellation email"""
        subject = "Subscription Canceled"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">🦄 Unicorn Commander</h1>
            </div>

            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333;">Subscription Canceled</h2>

                <p style="color: #666; font-size: 16px;">
                    We're sorry to see you go! Your <strong>{tier.title()}</strong> subscription has been canceled.
                </p>

                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Access Until:</strong> {end_date}</p>
                    <p>You'll still have access to your subscription features until this date.</p>
                </div>

                <p style="color: #666;">
                    After this date, your account will be downgraded to the Trial tier with limited features.
                </p>

                <p style="color: #666;">
                    Changed your mind? You can reactivate your subscription anytime from your dashboard.
                </p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://your-domain.com/pricing"
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reactivate Subscription
                    </a>
                </div>

                <p style="color: #999; font-size: 14px; border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px;">
                    Need help? Contact us at <a href="mailto:support@your-domain.com">support@your-domain.com</a>
                </p>
            </div>
        </body>
        </html>
        """

        return await self.send_email(to, subject, html_content)

    async def send_payment_failed(
        self,
        to: str,
        amount: float,
        reason: Optional[str] = None
    ) -> bool:
        """Send payment failed email"""
        subject = "Payment Failed - Action Required"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">⚠️ Payment Failed</h1>
            </div>

            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333;">Payment Could Not Be Processed</h2>

                <p style="color: #666; font-size: 16px;">
                    We were unable to process your payment of <strong>${amount:.2f}</strong>.
                </p>

                {f'<div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;"><p style="margin: 0; color: #856404;"><strong>Reason:</strong> {reason}</p></div>' if reason else ''}

                <p style="color: #666;">
                    To avoid interruption of your service, please update your payment method or retry the payment.
                </p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://your-domain.com/dashboard/billing"
                       style="background: #dc3545; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Update Payment Method
                    </a>
                </div>

                <p style="color: #999; font-size: 14px; border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px;">
                    Questions? Contact us at <a href="mailto:support@your-domain.com">support@your-domain.com</a>
                </p>
            </div>
        </body>
        </html>
        """

        return await self.send_email(to, subject, html_content)

    async def send_invoice(
        self,
        to: str,
        invoice_number: str,
        amount: float,
        invoice_url: Optional[str] = None
    ) -> bool:
        """Send invoice email"""
        subject = f"Invoice {invoice_number} - Unicorn Commander"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">🦄 Unicorn Commander</h1>
            </div>

            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333;">Payment Receipt</h2>

                <p style="color: #666; font-size: 16px;">
                    Thank you for your payment!
                </p>

                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Invoice Number:</strong> {invoice_number}</p>
                    <p><strong>Amount Paid:</strong> ${amount:.2f}</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                </div>

                {f'<div style="text-align: center; margin: 30px 0;"><a href="{invoice_url}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">View Invoice</a></div>' if invoice_url else ''}

                <p style="color: #999; font-size: 14px; border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px;">
                    Questions about this invoice? Contact us at <a href="mailto:billing@your-domain.com">billing@your-domain.com</a>
                </p>
            </div>
        </body>
        </html>
        """

        return await self.send_email(to, subject, html_content)


# Singleton instance
email_service = EmailService()
