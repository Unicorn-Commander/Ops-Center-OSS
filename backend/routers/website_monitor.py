"""
Website Uptime Monitor API Router

Monitors website availability, response times, SSL certificate status,
and provides uptime history.

Includes email alerting for downtime and recovery events.
Includes a background scheduler that periodically checks all active websites.
"""

import os
import asyncio
import httpx
import ssl
import socket
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging
import asyncpg

# Import email service for alerts
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/website-monitor", tags=["website-monitor"])

# Background scheduler configuration
WEBSITE_CHECK_INTERVAL_SECONDS = int(os.getenv("WEBSITE_CHECK_INTERVAL_SECONDS", "300"))  # Default: 5 minutes

# Scheduler state
_scheduler_task: Optional[asyncio.Task] = None
_scheduler_running: bool = False
_last_scheduler_run: Optional[datetime] = None
_scheduler_run_count: int = 0

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://unicorn:your-postgres-password@unicorn-postgresql:5432/unicorn_db")

# In-memory cache for quick access (refreshed periodically)
_websites_cache: Dict[str, dict] = {}
_last_check: Dict[str, dict] = {}


class WebsiteCreate(BaseModel):
    name: str
    url: str
    server: str = "primary"  # Server identifier (primary, secondary, etc.)
    check_interval: int = 60  # seconds
    timeout: int = 10  # seconds
    expected_status: int = 200
    notify_on_down: bool = True
    alert_email: Optional[str] = None  # Email address to send alerts to


class WebsiteUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    server: Optional[str] = None
    check_interval: Optional[int] = None
    timeout: Optional[int] = None
    expected_status: Optional[int] = None
    notify_on_down: Optional[bool] = None
    is_active: Optional[bool] = None
    alert_email: Optional[str] = None  # Email address to send alerts to


class WebsiteStatus(BaseModel):
    id: str
    name: str
    url: str
    server: str = "primary"
    status: str  # up, down, unknown
    response_time_ms: Optional[int] = None
    status_code: Optional[int] = None
    ssl_valid: Optional[bool] = None
    ssl_expiry: Optional[str] = None
    last_check: Optional[str] = None
    uptime_24h: Optional[float] = None
    error: Optional[str] = None


async def get_db_pool():
    """Get database connection pool"""
    return await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)


async def init_database():
    """Initialize the websites monitoring table"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS monitored_websites (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    url VARCHAR(1024) NOT NULL,
                    server VARCHAR(255) DEFAULT 'primary',
                    check_interval INTEGER DEFAULT 60,
                    timeout INTEGER DEFAULT 10,
                    expected_status INTEGER DEFAULT 200,
                    notify_on_down BOOLEAN DEFAULT TRUE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );

                -- Add server column if it doesn't exist (migration)
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name='monitored_websites' AND column_name='server') THEN
                        ALTER TABLE monitored_websites ADD COLUMN server VARCHAR(255) DEFAULT 'primary';
                    END IF;
                END $$;

                -- Add alert tracking columns (migration)
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name='monitored_websites' AND column_name='last_alert_status') THEN
                        ALTER TABLE monitored_websites ADD COLUMN last_alert_status VARCHAR(20) DEFAULT NULL;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name='monitored_websites' AND column_name='last_alert_sent_at') THEN
                        ALTER TABLE monitored_websites ADD COLUMN last_alert_sent_at TIMESTAMP DEFAULT NULL;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name='monitored_websites' AND column_name='alert_email') THEN
                        ALTER TABLE monitored_websites ADD COLUMN alert_email VARCHAR(255) DEFAULT NULL;
                    END IF;
                END $$;

                CREATE TABLE IF NOT EXISTS website_checks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    website_id UUID REFERENCES monitored_websites(id) ON DELETE CASCADE,
                    status VARCHAR(20) NOT NULL,
                    status_code INTEGER,
                    response_time_ms INTEGER,
                    ssl_valid BOOLEAN,
                    ssl_expiry TIMESTAMP,
                    error TEXT,
                    checked_at TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_website_checks_website_id ON website_checks(website_id);
                CREATE INDEX IF NOT EXISTS idx_website_checks_checked_at ON website_checks(checked_at);
            """)
        await pool.close()
        logger.info("Website monitoring tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


async def check_ssl_certificate(hostname: str) -> dict:
    """Check SSL certificate validity and expiry"""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expiry_str = cert.get('notAfter', '')
                # Parse the expiry date
                if expiry_str:
                    expiry = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (expiry - datetime.now()).days
                    return {
                        "valid": True,
                        "expiry": expiry.isoformat(),
                        "days_until_expiry": days_until_expiry,
                        "issuer": dict(x[0] for x in cert.get('issuer', []))
                    }
        return {"valid": True, "expiry": None}
    except ssl.SSLError as e:
        return {"valid": False, "error": str(e)}
    except Exception as e:
        return {"valid": None, "error": str(e)}


async def check_website(url: str, timeout: int = 10, expected_status: int = 200) -> dict:
    """Check a website's availability"""
    result = {
        "status": "unknown",
        "status_code": None,
        "response_time_ms": None,
        "ssl_valid": None,
        "ssl_expiry": None,
        "error": None,
        "checked_at": datetime.now().isoformat()
    }

    try:
        start_time = datetime.now()

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            end_time = datetime.now()

            result["response_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
            result["status_code"] = response.status_code

            if response.status_code == expected_status or (200 <= response.status_code < 400):
                result["status"] = "up"
            else:
                result["status"] = "down"
                result["error"] = f"Unexpected status code: {response.status_code}"

        # Check SSL if HTTPS
        if url.startswith("https://"):
            from urllib.parse import urlparse
            hostname = urlparse(url).hostname
            ssl_info = await asyncio.get_event_loop().run_in_executor(
                None, lambda: asyncio.run(check_ssl_certificate(hostname))
            )
            # Simpler sync SSL check
            try:
                import ssl
                import socket
                context = ssl.create_default_context()
                with socket.create_connection((hostname, 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        expiry_str = cert.get('notAfter', '')
                        if expiry_str:
                            expiry = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
                            result["ssl_valid"] = True
                            result["ssl_expiry"] = expiry.isoformat()
            except Exception as ssl_err:
                result["ssl_valid"] = False
                logger.warning(f"SSL check failed for {url}: {ssl_err}")

    except httpx.TimeoutException:
        result["status"] = "down"
        result["error"] = "Connection timed out"
    except httpx.ConnectError as e:
        result["status"] = "down"
        result["error"] = f"Connection failed: {str(e)}"
    except Exception as e:
        result["status"] = "down"
        result["error"] = str(e)

    return result


# ===== EMAIL ALERTING FUNCTIONS =====

# Default alert email (admin email from environment)
DEFAULT_ALERT_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")


async def send_website_alert(website: dict, status: str, check_result: dict) -> bool:
    """
    Send an email alert for website status change (down or recovery).

    Args:
        website: Website record from database (dict with id, name, url, alert_email, etc.)
        status: 'down' or 'up' (for recovery)
        check_result: The check result dict with status_code, response_time_ms, error, etc.

    Returns:
        True if email sent successfully, False otherwise
    """
    # Determine recipient email
    to_email = website.get('alert_email') or DEFAULT_ALERT_EMAIL

    if not to_email:
        logger.warning(f"No alert email configured for website {website['name']}")
        return False

    website_name = website['name']
    website_url = website['url']
    checked_at = check_result.get('checked_at', datetime.now().isoformat())

    if status == 'down':
        # DOWN alert
        subject = f"[ALERT] Website Down: {website_name}"

        error_message = check_result.get('error') or 'Unknown error'
        status_code = check_result.get('status_code')
        response_time = check_result.get('response_time_ms')

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Website Down Alert</h1>
            </div>

            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #dc3545; margin-top: 0;">{website_name} is DOWN</h2>

                <p style="color: #666; font-size: 16px;">
                    We detected that your website is not responding correctly.
                </p>

                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc3545;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 10px 10px 10px 0; color: #666;"><strong>Website:</strong></td>
                            <td style="padding: 10px 0;">{website_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 10px 10px 0; color: #666;"><strong>URL:</strong></td>
                            <td style="padding: 10px 0;"><a href="{website_url}" style="color: #667eea;">{website_url}</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 10px 10px 0; color: #666;"><strong>Status:</strong></td>
                            <td style="padding: 10px 0;"><span style="background: #dc3545; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold;">DOWN</span></td>
                        </tr>
                        {f'<tr><td style="padding: 10px 10px 10px 0; color: #666;"><strong>HTTP Status:</strong></td><td style="padding: 10px 0;">{status_code}</td></tr>' if status_code else ''}
                        {f'<tr><td style="padding: 10px 10px 10px 0; color: #666;"><strong>Response Time:</strong></td><td style="padding: 10px 0;">{response_time}ms</td></tr>' if response_time else ''}
                        <tr>
                            <td style="padding: 10px 10px 10px 0; color: #666;"><strong>Error:</strong></td>
                            <td style="padding: 10px 0; color: #dc3545;">{error_message}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 10px 10px 0; color: #666;"><strong>Detected At:</strong></td>
                            <td style="padding: 10px 0;">{checked_at}</td>
                        </tr>
                    </table>
                </div>

                <p style="color: #666;">
                    Please investigate this issue as soon as possible. You will receive another alert when the website recovers.
                </p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{website_url}"
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Check Website
                    </a>
                </div>

                <p style="color: #999; font-size: 12px; border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px;">
                    This alert was sent by Unicorn Commander Website Monitor.<br>
                    <a href="https://unicorncommander.ai/admin/website-monitor" style="color: #667eea;">Manage monitoring settings</a>
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
WEBSITE DOWN ALERT

{website_name} is DOWN

Website: {website_name}
URL: {website_url}
Status: DOWN
{f'HTTP Status: {status_code}' if status_code else ''}
{f'Response Time: {response_time}ms' if response_time else ''}
Error: {error_message}
Detected At: {checked_at}

Please investigate this issue as soon as possible.

---
Unicorn Commander Website Monitor
https://unicorncommander.ai/admin/website-monitor
        """

    else:
        # RECOVERY alert
        subject = f"[RECOVERED] Website Back Up: {website_name}"

        response_time = check_result.get('response_time_ms')
        status_code = check_result.get('status_code', 200)

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Website Recovered</h1>
            </div>

            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #28a745; margin-top: 0;">{website_name} is back UP</h2>

                <p style="color: #666; font-size: 16px;">
                    Good news! Your website has recovered and is responding normally.
                </p>

                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 10px 10px 10px 0; color: #666;"><strong>Website:</strong></td>
                            <td style="padding: 10px 0;">{website_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 10px 10px 0; color: #666;"><strong>URL:</strong></td>
                            <td style="padding: 10px 0;"><a href="{website_url}" style="color: #667eea;">{website_url}</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 10px 10px 0; color: #666;"><strong>Status:</strong></td>
                            <td style="padding: 10px 0;"><span style="background: #28a745; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold;">UP</span></td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 10px 10px 0; color: #666;"><strong>HTTP Status:</strong></td>
                            <td style="padding: 10px 0;">{status_code}</td>
                        </tr>
                        {f'<tr><td style="padding: 10px 10px 10px 0; color: #666;"><strong>Response Time:</strong></td><td style="padding: 10px 0;">{response_time}ms</td></tr>' if response_time else ''}
                        <tr>
                            <td style="padding: 10px 10px 10px 0; color: #666;"><strong>Recovered At:</strong></td>
                            <td style="padding: 10px 0;">{checked_at}</td>
                        </tr>
                    </table>
                </div>

                <p style="color: #666;">
                    The website is now responding normally. No further action is required.
                </p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{website_url}"
                       style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Visit Website
                    </a>
                </div>

                <p style="color: #999; font-size: 12px; border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px;">
                    This alert was sent by Unicorn Commander Website Monitor.<br>
                    <a href="https://unicorncommander.ai/admin/website-monitor" style="color: #667eea;">Manage monitoring settings</a>
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
WEBSITE RECOVERED

{website_name} is back UP

Website: {website_name}
URL: {website_url}
Status: UP
HTTP Status: {status_code}
{f'Response Time: {response_time}ms' if response_time else ''}
Recovered At: {checked_at}

The website is now responding normally.

---
Unicorn Commander Website Monitor
https://unicorncommander.ai/admin/website-monitor
        """

    # Send the email
    try:
        success = await email_service.send_email(
            to=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        if success:
            logger.info(f"Sent {status.upper()} alert email for {website_name} to {to_email}")
        else:
            logger.error(f"Failed to send {status.upper()} alert email for {website_name} to {to_email}")
        return success
    except Exception as e:
        logger.error(f"Error sending alert email for {website_name}: {e}")
        return False


async def process_website_alert(conn, website: dict, check_result: dict) -> None:
    """
    Process alert logic after a website check.

    Sends an alert only when:
    - Site transitions from 'up' (or null) to 'down' -> DOWN alert
    - Site transitions from 'down' to 'up' -> RECOVERY alert

    Does NOT send alerts for repeated same-status checks (no spam).

    Args:
        conn: Database connection
        website: Website record from database
        check_result: The check result dict
    """
    # Skip if notifications are disabled for this website
    if not website.get('notify_on_down', True):
        return

    current_status = check_result['status']
    last_alert_status = website.get('last_alert_status')
    website_id = website['id']
    website_name = website['name']

    # Determine if we need to send an alert
    should_send_alert = False
    alert_type = None

    if current_status == 'down' and last_alert_status != 'down':
        # Site went down (from 'up', 'unknown', or first check)
        should_send_alert = True
        alert_type = 'down'
        logger.warning(f"Website {website_name} went DOWN (previous: {last_alert_status})")

    elif current_status == 'up' and last_alert_status == 'down':
        # Site recovered from down state
        should_send_alert = True
        alert_type = 'up'
        logger.info(f"Website {website_name} RECOVERED (was down)")

    if should_send_alert:
        # Send the alert email
        email_sent = await send_website_alert(website, alert_type, check_result)

        # Update the alert tracking columns
        try:
            await conn.execute("""
                UPDATE monitored_websites
                SET last_alert_status = $1,
                    last_alert_sent_at = NOW(),
                    updated_at = NOW()
                WHERE id = $2
            """, current_status, website_id)

            logger.info(f"Updated alert status for {website_name}: {current_status}")
        except Exception as e:
            logger.error(f"Failed to update alert status for {website_name}: {e}")

    elif current_status == 'up' and last_alert_status != 'down':
        # Site is up and wasn't previously down - just update status silently (no alert needed)
        # This handles the case where last_alert_status was null or 'up'
        try:
            await conn.execute("""
                UPDATE monitored_websites
                SET last_alert_status = $1,
                    updated_at = NOW()
                WHERE id = $2
            """, current_status, website_id)
        except Exception as e:
            logger.error(f"Failed to update status for {website_name}: {e}")


@router.on_event("startup")
async def startup():
    """Initialize on startup"""
    await init_database()


@router.get("/health")
async def monitor_health():
    """Health check for website monitor"""
    return {"status": "healthy", "service": "website-monitor"}


@router.get("/websites")
async def list_websites():
    """List all monitored websites with their current status"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            websites = await conn.fetch("""
                SELECT
                    w.id, w.name, w.url, w.server, w.check_interval, w.timeout,
                    w.expected_status, w.notify_on_down, w.is_active,
                    w.created_at, w.updated_at,
                    c.status as last_status,
                    c.status_code as last_status_code,
                    c.response_time_ms as last_response_time,
                    c.ssl_valid, c.ssl_expiry,
                    c.error as last_error,
                    c.checked_at as last_check
                FROM monitored_websites w
                LEFT JOIN LATERAL (
                    SELECT * FROM website_checks
                    WHERE website_id = w.id
                    ORDER BY checked_at DESC
                    LIMIT 1
                ) c ON true
                WHERE w.is_active = true
                ORDER BY w.server, w.name
            """)

            result = []
            for row in websites:
                website = dict(row)
                # Calculate uptime for last 24 hours
                uptime_result = await conn.fetchrow("""
                    SELECT
                        COUNT(*) FILTER (WHERE status = 'up') as up_count,
                        COUNT(*) as total_count
                    FROM website_checks
                    WHERE website_id = $1 AND checked_at > NOW() - INTERVAL '24 hours'
                """, row['id'])

                if uptime_result and uptime_result['total_count'] > 0:
                    website['uptime_24h'] = round(
                        (uptime_result['up_count'] / uptime_result['total_count']) * 100, 2
                    )
                else:
                    website['uptime_24h'] = None

                # Convert UUID to string
                website['id'] = str(website['id'])
                result.append(website)

        await pool.close()
        return {"websites": result, "count": len(result)}

    except Exception as e:
        logger.error(f"Error listing websites: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/websites")
async def add_website(website: WebsiteCreate):
    """Add a new website to monitor"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO monitored_websites (name, url, server, check_interval, timeout, expected_status, notify_on_down, alert_email)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id, name, url, server, check_interval, timeout, expected_status, notify_on_down, alert_email, is_active, created_at
            """, website.name, website.url, website.server, website.check_interval, website.timeout,
                website.expected_status, website.notify_on_down, website.alert_email)

        await pool.close()

        return {
            "id": str(result['id']),
            "name": result['name'],
            "url": result['url'],
            "alert_email": result['alert_email'],
            "message": "Website added successfully"
        }

    except Exception as e:
        logger.error(f"Error adding website: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/websites/{website_id}")
async def get_website(website_id: str):
    """Get details for a specific website"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            website = await conn.fetchrow("""
                SELECT * FROM monitored_websites WHERE id = $1
            """, website_id)

            if not website:
                raise HTTPException(status_code=404, detail="Website not found")

            # Get last 10 checks
            checks = await conn.fetch("""
                SELECT status, status_code, response_time_ms, ssl_valid, ssl_expiry, error, checked_at
                FROM website_checks
                WHERE website_id = $1
                ORDER BY checked_at DESC
                LIMIT 10
            """, website_id)

            # Get uptime stats
            uptime_stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'up') as up_count,
                    COUNT(*) as total_count,
                    AVG(response_time_ms) FILTER (WHERE status = 'up') as avg_response_time
                FROM website_checks
                WHERE website_id = $1 AND checked_at > NOW() - INTERVAL '24 hours'
            """, website_id)

        await pool.close()

        result = dict(website)
        result['id'] = str(result['id'])
        result['recent_checks'] = [dict(c) for c in checks]
        result['uptime_24h'] = round(
            (uptime_stats['up_count'] / uptime_stats['total_count']) * 100, 2
        ) if uptime_stats['total_count'] > 0 else None
        result['avg_response_time_24h'] = round(uptime_stats['avg_response_time']) if uptime_stats['avg_response_time'] else None

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting website: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/websites/{website_id}")
async def update_website(website_id: str, website: WebsiteUpdate):
    """Update a monitored website"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Build update query dynamically
            updates = []
            values = []
            idx = 1

            for field, value in website.dict(exclude_unset=True).items():
                if value is not None:
                    updates.append(f"{field} = ${idx}")
                    values.append(value)
                    idx += 1

            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")

            values.append(website_id)
            query = f"""
                UPDATE monitored_websites
                SET {', '.join(updates)}, updated_at = NOW()
                WHERE id = ${idx}
                RETURNING id, name, url
            """

            result = await conn.fetchrow(query, *values)

            if not result:
                raise HTTPException(status_code=404, detail="Website not found")

        await pool.close()
        return {"message": "Website updated", "id": str(result['id'])}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating website: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/websites/{website_id}")
async def delete_website(website_id: str):
    """Delete a monitored website"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM monitored_websites WHERE id = $1
            """, website_id)

        await pool.close()

        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Website not found")

        return {"message": "Website deleted", "id": website_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting website: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/websites/{website_id}/check")
async def check_website_now(website_id: str):
    """Manually trigger a check for a website"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            website = await conn.fetchrow("""
                SELECT * FROM monitored_websites WHERE id = $1
            """, website_id)

            if not website:
                raise HTTPException(status_code=404, detail="Website not found")

            # Perform the check
            result = await check_website(
                website['url'],
                timeout=website['timeout'],
                expected_status=website['expected_status']
            )

            # Store the result
            await conn.execute("""
                INSERT INTO website_checks
                (website_id, status, status_code, response_time_ms, ssl_valid, ssl_expiry, error)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, website_id, result['status'], result['status_code'],
                result['response_time_ms'], result['ssl_valid'],
                datetime.fromisoformat(result['ssl_expiry']) if result['ssl_expiry'] else None,
                result['error'])

            # Process alerts (send email if status changed)
            await process_website_alert(conn, dict(website), result)

        await pool.close()

        return {
            "website_id": website_id,
            "name": website['name'],
            "url": website['url'],
            **result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking website: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-all")
async def check_all_websites():
    """Check all active websites immediately"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Fetch all fields needed for alert processing including last_alert_status
            websites = await conn.fetch("""
                SELECT id, name, url, timeout, expected_status, notify_on_down,
                       alert_email, last_alert_status, last_alert_sent_at
                FROM monitored_websites
                WHERE is_active = true
            """)

            results = []
            alerts_sent = 0
            for website in websites:
                result = await check_website(
                    website['url'],
                    timeout=website['timeout'],
                    expected_status=website['expected_status']
                )

                # Store the result
                await conn.execute("""
                    INSERT INTO website_checks
                    (website_id, status, status_code, response_time_ms, ssl_valid, ssl_expiry, error)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, website['id'], result['status'], result['status_code'],
                    result['response_time_ms'], result['ssl_valid'],
                    datetime.fromisoformat(result['ssl_expiry']) if result['ssl_expiry'] else None,
                    result['error'])

                # Process alerts (send email if status changed)
                await process_website_alert(conn, dict(website), result)

                results.append({
                    "id": str(website['id']),
                    "name": website['name'],
                    "url": website['url'],
                    **result
                })

        await pool.close()

        up_count = sum(1 for r in results if r['status'] == 'up')
        down_count = sum(1 for r in results if r['status'] == 'down')

        return {
            "checked": len(results),
            "up": up_count,
            "down": down_count,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error checking all websites: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/websites/{website_id}/history")
async def get_website_history(website_id: str, hours: int = 24):
    """Get check history for a website"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            checks = await conn.fetch("""
                SELECT status, status_code, response_time_ms, ssl_valid, error, checked_at
                FROM website_checks
                WHERE website_id = $1 AND checked_at > NOW() - INTERVAL '%s hours'
                ORDER BY checked_at DESC
            """ % hours, website_id)

        await pool.close()

        return {
            "website_id": website_id,
            "period_hours": hours,
            "checks": [dict(c) for c in checks],
            "count": len(checks)
        }

    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-add")
async def bulk_add_websites(websites: List[WebsiteCreate]):
    """Add multiple websites at once"""
    try:
        pool = await get_db_pool()
        added = []
        skipped = []

        async with pool.acquire() as conn:
            for website in websites:
                # Check if URL already exists
                existing = await conn.fetchrow(
                    "SELECT id FROM monitored_websites WHERE url = $1",
                    website.url
                )

                if existing:
                    skipped.append({"name": website.name, "url": website.url, "reason": "Already exists"})
                    continue

                result = await conn.fetchrow("""
                    INSERT INTO monitored_websites (name, url, server, check_interval, timeout, expected_status, notify_on_down, alert_email)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id, name, url, server
                """, website.name, website.url, website.server, website.check_interval,
                    website.timeout, website.expected_status, website.notify_on_down, website.alert_email)

                added.append({
                    "id": str(result['id']),
                    "name": result['name'],
                    "url": result['url'],
                    "server": result['server']
                })

        await pool.close()

        return {
            "added": len(added),
            "skipped": len(skipped),
            "websites": added,
            "skipped_details": skipped
        }

    except Exception as e:
        logger.error(f"Error bulk adding websites: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public-status")
async def get_public_status():
    """
    Public status page data - no authentication required.
    Returns sanitized status data for all monitored websites.
    Does not expose internal IDs or configuration details.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            websites = await conn.fetch("""
                SELECT
                    w.name, w.url,
                    c.status as last_status,
                    c.ssl_valid,
                    c.checked_at as last_check
                FROM monitored_websites w
                LEFT JOIN LATERAL (
                    SELECT status, ssl_valid, checked_at
                    FROM website_checks
                    WHERE website_id = w.id
                    ORDER BY checked_at DESC
                    LIMIT 1
                ) c ON true
                WHERE w.is_active = true
                ORDER BY w.name
            """)

            services = []
            for row in websites:
                # Calculate uptime for last 24 hours
                uptime_result = await conn.fetchrow("""
                    SELECT
                        COUNT(*) FILTER (WHERE status = 'up') as up_count,
                        COUNT(*) as total_count
                    FROM website_checks wc
                    JOIN monitored_websites mw ON wc.website_id = mw.id
                    WHERE mw.url = $1 AND wc.checked_at > NOW() - INTERVAL '24 hours'
                """, row['url'])

                uptime_24h = None
                if uptime_result and uptime_result['total_count'] > 0:
                    uptime_24h = round(
                        (uptime_result['up_count'] / uptime_result['total_count']) * 100, 2
                    )

                services.append({
                    "name": row['name'],
                    "url": row['url'],
                    "status": row['last_status'] or 'unknown',
                    "ssl_valid": row['ssl_valid'],
                    "uptime_24h": uptime_24h,
                    "last_check": row['last_check'].isoformat() if row['last_check'] else None
                })

        await pool.close()

        # Calculate summary
        up_count = sum(1 for s in services if s['status'] == 'up')
        down_count = sum(1 for s in services if s['status'] == 'down')

        return {
            "services": services,
            "summary": {
                "total": len(services),
                "up": up_count,
                "down": down_count,
                "unknown": len(services) - up_count - down_count
            },
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting public status: {e}")
        # Return empty status rather than error for public page
        return {
            "services": [],
            "summary": {"total": 0, "up": 0, "down": 0, "unknown": 0},
            "generated_at": datetime.now().isoformat(),
            "error": "Status temporarily unavailable"
        }


@router.get("/discover")
async def discover_local_websites():
    """
    Discover websites running on this server by checking:
    1. Docker containers with Traefik labels
    2. Common service ports

    Returns a list of discovered websites that can be added to monitoring.
    """
    import subprocess
    import json as json_module

    discovered = []
    server_hostname = os.uname().nodename

    try:
        # Get all running containers with their labels
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}|||{{.Ports}}|||{{.Labels}}"],
            capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')

            for line in lines:
                if not line.strip():
                    continue

                parts = line.split('|||')
                if len(parts) < 3:
                    continue

                container_name = parts[0].strip()
                ports = parts[1].strip()
                labels = parts[2].strip()

                # Parse Traefik labels for domain info
                domain = None
                if 'traefik.http.routers' in labels:
                    # Extract domain from Host rule
                    import re
                    host_match = re.search(r'Host\(`([^`]+)`\)', labels)
                    if host_match:
                        domain = host_match.group(1)

                # If we found a domain, add it
                if domain:
                    discovered.append({
                        "name": container_name.replace('unicorn-', '').replace('-', ' ').title(),
                        "url": f"https://{domain}",
                        "server": server_hostname,
                        "source": "traefik-labels",
                        "container": container_name
                    })

        # Also get domains from Traefik dynamic configuration
        traefik_result = subprocess.run(
            ["docker", "exec", "traefik", "cat", "/etc/traefik/traefik.yml"],
            capture_output=True, text=True, timeout=5
        )

    except subprocess.TimeoutExpired:
        logger.warning("Docker command timed out during discovery")
    except Exception as e:
        logger.warning(f"Error during docker discovery: {e}")

    # Add known services based on common patterns
    known_services = [
        {"name": "Unicorn Commander", "url": "https://unicorncommander.ai", "server": server_hostname},
        {"name": "Authentication", "url": "https://auth.unicorncommander.ai", "server": server_hostname},
        {"name": "Chat (Open-WebUI)", "url": "https://chat.unicorncommander.ai", "server": server_hostname},
        {"name": "Center Deep Search", "url": "https://search.unicorncommander.ai", "server": server_hostname},
        {"name": "Forgejo Git", "url": "https://git.unicorncommander.ai", "server": server_hostname},
        {"name": "Billing", "url": "https://billing.unicorncommander.ai", "server": server_hostname},
        {"name": "Brigade", "url": "https://brigade.unicorncommander.ai", "server": server_hostname},
        {"name": "Bolt.diy", "url": "https://bolt.unicorncommander.ai", "server": server_hostname},
        {"name": "Presenton", "url": "https://presentations.unicorncommander.ai", "server": server_hostname},
        {"name": "PartnerPulse", "url": "https://partnerpulse.unicorncommander.ai", "server": server_hostname},
        {"name": "Magic Unicorn", "url": "https://magicunicorn.tech", "server": server_hostname},
        {"name": "Unicorn Commander .com", "url": "https://unicorncommander.com", "server": server_hostname},
        {"name": "Adorna Design", "url": "https://adornadesign.com", "server": server_hostname},
        {"name": "Cognitive Companion", "url": "https://cognitivecompanion.shop", "server": server_hostname},
        {"name": "Superior B Solutions", "url": "https://superiorbsolutions.com", "server": server_hostname},
        {"name": "Lavora Remodeling", "url": "https://lavora-remodeling.com", "server": server_hostname},
        {"name": "Umami Analytics", "url": "https://analytics.unicorncommander.ai", "server": server_hostname},
    ]

    # Add known services, avoiding duplicates
    existing_urls = {d['url'] for d in discovered}
    for service in known_services:
        if service['url'] not in existing_urls:
            discovered.append({**service, "source": "known-service"})

    return {
        "discovered": discovered,
        "count": len(discovered),
        "server": server_hostname,
        "note": "Use POST /bulk-add to add these websites to monitoring"
    }


# =============================================================================
# Background Scheduler Functions
# =============================================================================

async def _run_scheduled_checks():
    """
    Internal function that runs website checks on a schedule.
    This runs in the background and stores results in the database.
    Includes email alerting for status changes.
    """
    global _scheduler_running, _last_scheduler_run, _scheduler_run_count

    logger.info(f"[Scheduler] Started background website monitor (interval: {WEBSITE_CHECK_INTERVAL_SECONDS}s)")

    while _scheduler_running:
        try:
            logger.info("[Scheduler] Starting scheduled website checks...")
            _last_scheduler_run = datetime.now()
            _scheduler_run_count += 1

            pool = await get_db_pool()
            async with pool.acquire() as conn:
                # Get all active websites with alert tracking fields
                websites = await conn.fetch("""
                    SELECT id, name, url, timeout, expected_status, notify_on_down,
                           alert_email, last_alert_status, last_alert_sent_at
                    FROM monitored_websites
                    WHERE is_active = true
                """)

                if not websites:
                    logger.info("[Scheduler] No active websites to check")
                else:
                    up_count = 0
                    down_count = 0
                    alerts_sent = 0

                    for website in websites:
                        try:
                            # Perform the check
                            result = await check_website(
                                website['url'],
                                timeout=website['timeout'],
                                expected_status=website['expected_status']
                            )

                            # Store the result
                            await conn.execute("""
                                INSERT INTO website_checks
                                (website_id, status, status_code, response_time_ms, ssl_valid, ssl_expiry, error)
                                VALUES ($1, $2, $3, $4, $5, $6, $7)
                            """, website['id'], result['status'], result['status_code'],
                                result['response_time_ms'], result['ssl_valid'],
                                datetime.fromisoformat(result['ssl_expiry']) if result['ssl_expiry'] else None,
                                result['error'])

                            # Process alerts (send email if status changed)
                            await process_website_alert(conn, dict(website), result)

                            if result['status'] == 'up':
                                up_count += 1
                            else:
                                down_count += 1
                                logger.warning(f"[Scheduler] Website DOWN: {website['name']} ({website['url']}) - {result.get('error', 'Unknown error')}")

                        except Exception as e:
                            logger.error(f"[Scheduler] Error checking {website['name']}: {e}")
                            down_count += 1

                    logger.info(f"[Scheduler] Completed check #{_scheduler_run_count}: {len(websites)} sites checked, {up_count} up, {down_count} down")

            await pool.close()

        except Exception as e:
            logger.error(f"[Scheduler] Error during scheduled check: {e}")

        # Wait for the next interval
        if _scheduler_running:
            await asyncio.sleep(WEBSITE_CHECK_INTERVAL_SECONDS)

    logger.info("[Scheduler] Background website monitor stopped")


async def start_scheduler():
    """Start the background scheduler task"""
    global _scheduler_task, _scheduler_running

    if _scheduler_running:
        logger.warning("[Scheduler] Scheduler is already running")
        return False

    _scheduler_running = True
    _scheduler_task = asyncio.create_task(_run_scheduled_checks())
    logger.info("[Scheduler] Scheduler started")
    return True


async def stop_scheduler():
    """Stop the background scheduler task"""
    global _scheduler_task, _scheduler_running

    if not _scheduler_running:
        logger.warning("[Scheduler] Scheduler is not running")
        return False

    _scheduler_running = False

    if _scheduler_task:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None

    logger.info("[Scheduler] Scheduler stopped")
    return True


# =============================================================================
# Scheduler API Endpoints
# =============================================================================

@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get the current status of the background scheduler"""
    return {
        "running": _scheduler_running,
        "check_interval_seconds": WEBSITE_CHECK_INTERVAL_SECONDS,
        "last_run": _last_scheduler_run.isoformat() if _last_scheduler_run else None,
        "total_runs": _scheduler_run_count,
        "next_run_in_seconds": (
            max(0, WEBSITE_CHECK_INTERVAL_SECONDS - (datetime.now() - _last_scheduler_run).total_seconds())
            if _last_scheduler_run and _scheduler_running
            else None
        )
    }


@router.post("/scheduler/start")
async def start_scheduler_endpoint():
    """Start the background scheduler to check websites periodically"""
    if _scheduler_running:
        raise HTTPException(
            status_code=400,
            detail="Scheduler is already running"
        )

    success = await start_scheduler()

    if success:
        return {
            "message": "Scheduler started successfully",
            "check_interval_seconds": WEBSITE_CHECK_INTERVAL_SECONDS
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to start scheduler"
        )


@router.post("/scheduler/stop")
async def stop_scheduler_endpoint():
    """Stop the background scheduler"""
    if not _scheduler_running:
        raise HTTPException(
            status_code=400,
            detail="Scheduler is not running"
        )

    success = await stop_scheduler()

    if success:
        return {
            "message": "Scheduler stopped successfully",
            "total_runs_completed": _scheduler_run_count
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to stop scheduler"
        )
