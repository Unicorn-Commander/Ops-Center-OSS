# Email Notifications System - Implementation Guide

**Epic**: 2.3 - Email Notifications
**Status**: ✅ COMPLETE
**Date**: October 24, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Email Templates](#email-templates)
5. [Scheduled Jobs](#scheduled-jobs)
6. [API Endpoints](#api-endpoints)
7. [Configuration](#configuration)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Email Notifications System provides automated email notifications for credit system events using the existing Microsoft 365 OAuth2 email infrastructure (`email_service.py`).

### Key Components

- **email_notifications.py** - Notification service with 7 email types
- **email_scheduler.py** - APScheduler-based automated triggers
- **email_notification_api.py** - REST API for manual testing
- **email_templates/** - 7 events × 2 formats (HTML + text)

---

## Features

### Priority 1: Must Have ✅

1. **Low Balance Alert** - Sent when credits < 10% remaining
   - Trigger: Daily check at 9 AM
   - Rate limit: Max 1 per user per day
   - Template: `low_balance.html` / `low_balance.txt`

2. **Monthly Credit Reset** - First day of month
   - Trigger: Automated on 1st at midnight
   - Includes: Usage summary, top service, next reset date
   - Template: `monthly_reset.html` / `monthly_reset.txt`

3. **Coupon Redemption Confirmation** - Instant notification
   - Trigger: On coupon redemption (manual or API)
   - Includes: Coupon code, credits added, new balance
   - Template: `coupon_redeemed.html` / `coupon_redeemed.txt`

4. **Welcome Email** - New user signup
   - Trigger: Manual (called from registration flow)
   - Includes: Tier info, dashboard link
   - Template: `welcome.html` / `welcome.txt`

### Priority 2: Nice to Have ✅

5. **Tier Upgrade Notification** - Subscription tier change
   - Trigger: Manual (called from upgrade flow)
   - Includes: Old → new tier comparison, new features
   - Template: `tier_upgrade.html` / `tier_upgrade.txt`

6. **Payment Failure Alert** - Stripe payment fails
   - Trigger: Manual (called from Stripe webhook)
   - Includes: Failure reason, grace period, retry date
   - Template: `payment_failure.html` / `payment_failure.txt`

7. **Usage Summary** - Weekly activity report
   - Trigger: Every Monday at 9 AM
   - Includes: Week stats, top services, usage trends
   - Template: `usage_summary.html` / `usage_summary.txt`

---

## Architecture

### Component Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  Email Notification System                   │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼───────┐   ┌──────▼──────┐
            │ email_scheduler│   │email_notif_ │
            │    .py         │   │ api.py      │
            │ (APScheduler)  │   │ (FastAPI)   │
            └───────┬────────┘   └──────┬──────┘
                    │                   │
                    └───────────┬───────┘
                                │
                        ┌───────▼───────┐
                        │email_notif_   │
                        │service.py     │
                        │               │
                        └───────┬───────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
    ┌───▼───┐              ┌───▼───┐              ┌───▼───┐
    │email_ │              │Keycloak│              │credit_│
    │service│              │(users) │              │system │
    │.py    │              └────────┘              │.py    │
    └───────┘                                      └───────┘
```

### Database Schema

**user_credits table** (new column):
```sql
email_notifications_enabled BOOLEAN DEFAULT TRUE
```

### Service Dependencies

- **email_service.py** - Handles actual email sending (SMTP/SendGrid/Mailgun)
- **keycloak_integration.py** - Fetches user email and username
- **credit_system.py** - Provides credit balance and transaction data
- **audit_logger.py** - Logs all notification events

---

## Email Templates

### Template Structure

All templates follow the Magic Unicorn theme:

- **Background**: Purple gradient (`#1a0033` → `#2d1b4e`)
- **Accent Colors**: Purple (`#a855f7`), Gold (`#fbbf24`)
- **Logo**: Centered unicorn emoji with glow effect
- **Card Design**: Glassmorphism with backdrop blur
- **Buttons**: Gradient with hover effects
- **Footer**: Links to dashboard, support, unsubscribe

### Template Variables

Common variables available in all templates:

```python
{
    "username": str,           # User's display name
    "dashboard_url": str,      # https://your-domain.com
    "support_email": str,      # support@your-domain.com
    "year": int,              # Current year
    "unsubscribe_url": str    # Unsubscribe link
}
```

### Template Files

Located in `backend/email_templates/`:

```
email_templates/
├── low_balance.html         # Low balance alert
├── low_balance.txt
├── monthly_reset.html       # Monthly credit reset
├── monthly_reset.txt
├── coupon_redeemed.html     # Coupon redemption
├── coupon_redeemed.txt
├── welcome.html             # Welcome email
├── welcome.txt
├── tier_upgrade.html        # Tier upgrade
├── tier_upgrade.txt
├── payment_failure.html     # Payment failure
├── payment_failure.txt
├── usage_summary.html       # Weekly usage summary
└── usage_summary.txt
```

---

## Scheduled Jobs

### Job Schedule

| Job | Trigger | Frequency | Recipients |
|-----|---------|-----------|------------|
| Low Balance Check | Daily 9 AM | Every day | Users with < 10% credits |
| Monthly Reset | 1st @ midnight | Monthly | All users with enabled notifications |
| Usage Summary | Monday 9 AM | Weekly | Users with activity in past 7 days |

### Job Configuration (APScheduler)

```python
# Daily low balance check (9 AM)
scheduler.add_job(
    func=_check_low_balances,
    trigger=CronTrigger(hour=9, minute=0),
    id="daily_low_balance_check"
)

# Monthly credit reset (1st day at midnight)
scheduler.add_job(
    func=_send_monthly_reset_notifications,
    trigger=CronTrigger(day=1, hour=0, minute=0),
    id="monthly_credit_reset"
)

# Weekly usage summary (Monday at 9 AM)
scheduler.add_job(
    func=_send_weekly_usage_summaries,
    trigger=CronTrigger(day_of_week="mon", hour=9, minute=0),
    id="weekly_usage_summary"
)
```

### Job Execution Flow

1. **Query Database** - Find eligible users
2. **Check Preferences** - Respect `email_notifications_enabled`
3. **Check Rate Limits** - Max 1 alert per user per day
4. **Fetch User Data** - Get email/username from Keycloak
5. **Render Templates** - Generate HTML + text versions
6. **Send Email** - Via `email_service.py`
7. **Audit Log** - Record success/failure

---

## API Endpoints

### Base Path

```
/api/v1/notifications
```

### Manual Notification Sending (Testing)

#### Send Low Balance Alert
```bash
POST /api/v1/notifications/send/low-balance
{
  "user_id": "uuid-here"
}
```

#### Send Monthly Reset
```bash
POST /api/v1/notifications/send/monthly-reset
{
  "user_id": "uuid-here"
}
```

#### Send Coupon Redeemed
```bash
POST /api/v1/notifications/send/coupon-redeemed
{
  "user_id": "uuid-here",
  "coupon_code": "WELCOME50",
  "credits_added": 50.00,
  "coupon_type": "Promotional"
}
```

#### Send Welcome Email
```bash
POST /api/v1/notifications/send/welcome
{
  "user_id": "uuid-here",
  "tier": "trial"
}
```

#### Send Tier Upgrade
```bash
POST /api/v1/notifications/send/tier-upgrade
{
  "user_id": "uuid-here",
  "old_tier": "trial",
  "new_tier": "professional",
  "new_features": [
    "Increased API limits",
    "Priority support",
    "Advanced analytics"
  ]
}
```

#### Send Payment Failure
```bash
POST /api/v1/notifications/send/payment-failure
{
  "user_id": "uuid-here",
  "tier": "professional",
  "amount": 49.00,
  "failure_reason": "Insufficient funds"
}
```

### Preference Management

#### Get Preferences
```bash
GET /api/v1/notifications/preferences/{user_id}

Response:
{
  "user_id": "uuid",
  "email_notifications_enabled": true
}
```

#### Update Preferences
```bash
PUT /api/v1/notifications/preferences/{user_id}
{
  "email_notifications_enabled": false
}

Response:
{
  "success": true,
  "message": "Notification preferences updated successfully",
  "user_id": "uuid",
  "email_notifications_enabled": false
}
```

#### Unsubscribe (Public Link)
```bash
GET /api/v1/notifications/unsubscribe/{user_id}

Response:
{
  "success": true,
  "message": "You have been unsubscribed from email notifications",
  "user_id": "uuid"
}
```

### Health Check
```bash
GET /api/v1/notifications/health

Response:
{
  "status": "healthy",
  "service": "email_notifications",
  "scheduler_running": true
}
```

---

## Configuration

### Environment Variables

Required in `.env` or `.env.auth`:

```bash
# Email Service (existing configuration)
EMAIL_ENABLED=true
EMAIL_PROVIDER=smtp  # smtp, sendgrid, mailgun, console
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=noreply@your-domain.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@your-domain.com
EMAIL_FROM_NAME=UC-1 Pro Ops Center
EMAIL_REPLY_TO=support@your-domain.com

# Application URLs
APP_URL=https://your-domain.com
SUPPORT_EMAIL=support@your-domain.com

# Database (existing configuration)
POSTGRES_HOST=unicorn-postgresql
POSTGRES_PORT=5432
POSTGRES_USER=unicorn
POSTGRES_PASSWORD=unicorn
POSTGRES_DB=unicorn_db
```

### Scheduler Configuration

Edit `email_scheduler.py` to customize:

```python
# Change schedule times
CronTrigger(hour=9, minute=0)        # Low balance check
CronTrigger(day=1, hour=0, minute=0) # Monthly reset
CronTrigger(day_of_week="mon", hour=9, minute=0)  # Usage summary
```

### Rate Limiting

Default rate limits (in `email_notifications.py`):

```python
# Alert-type notifications: Max 1 per user per 24 hours
_rate_limit = {}  # {user_id:notification_type: last_sent_time}
```

---

## Testing

### 1. Database Migration

```bash
# Apply database migration
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /app/migrations/add_email_notifications_column.sql

# Verify column exists
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d user_credits"
```

### 2. Test Email Sending (Manual API)

```bash
# Get a test user ID
USER_ID="your-keycloak-user-id-here"

# Test welcome email
curl -X POST http://localhost:8084/api/v1/notifications/send/welcome \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"tier\": \"trial\"}"

# Test low balance alert
curl -X POST http://localhost:8084/api/v1/notifications/send/low-balance \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\"}"

# Test coupon redemption
curl -X POST http://localhost:8084/api/v1/notifications/send/coupon-redeemed \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"coupon_code\": \"TEST50\",
    \"credits_added\": 50.00,
    \"coupon_type\": \"Test Coupon\"
  }"
```

### 3. Test Scheduled Jobs (Trigger Manually)

```python
# In Python console or test script
import asyncio
from email_scheduler import email_scheduler

async def test_jobs():
    await email_scheduler.initialize()

    # Test low balance check
    await email_scheduler._check_low_balances()

    # Test monthly reset
    await email_scheduler._send_monthly_reset_notifications()

    # Test usage summary
    await email_scheduler._send_weekly_usage_summaries()

    await email_scheduler.close()

asyncio.run(test_jobs())
```

### 4. Test Email Rendering

Check emails in different clients:

- ✅ **Gmail** (Desktop + Mobile)
- ✅ **Outlook** (Desktop + Mobile)
- ✅ **Apple Mail** (macOS + iOS)
- ✅ **Thunderbird**

Use [Litmus](https://litmus.com/) or [Email on Acid](https://www.emailonacid.com/) for comprehensive testing.

### 5. Test Unsubscribe Flow

```bash
# Unsubscribe user
curl http://localhost:8084/api/v1/notifications/unsubscribe/$USER_ID

# Verify preference updated
curl http://localhost:8084/api/v1/notifications/preferences/$USER_ID

# Try sending notification (should be skipped)
curl -X POST http://localhost:8084/api/v1/notifications/send/welcome \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"tier\": \"trial\"}"
```

---

## Deployment

### 1. Install Dependencies

```bash
# APScheduler already in requirements.txt
grep apscheduler backend/requirements.txt
# Output: apscheduler==3.10.4
```

### 2. Apply Database Migration

```bash
docker exec ops-center-direct python3 -c "
import asyncio
import asyncpg
import os

async def migrate():
    conn = await asyncpg.connect(
        host='unicorn-postgresql',
        port=5432,
        user='unicorn',
        password='unicorn',
        database='unicorn_db'
    )

    migration = '''
    ALTER TABLE user_credits
    ADD COLUMN IF NOT EXISTS email_notifications_enabled BOOLEAN DEFAULT TRUE;

    CREATE INDEX IF NOT EXISTS idx_user_credits_email_enabled
    ON user_credits(email_notifications_enabled);

    UPDATE user_credits
    SET email_notifications_enabled = TRUE
    WHERE email_notifications_enabled IS NULL;
    '''

    await conn.execute(migration)
    await conn.close()
    print('Migration applied successfully')

asyncio.run(migrate())
"
```

### 3. Update server.py

Add to startup/shutdown hooks:

```python
# In backend/server.py

from email_scheduler import email_scheduler

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # ... existing startup code ...

    # Start email scheduler
    await email_scheduler.start()
    logger.info("Email notification scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Stop email scheduler
    await email_scheduler.close()
    logger.info("Email notification scheduler stopped")

    # ... existing shutdown code ...
```

### 4. Register API Routes

```python
# In backend/server.py

from email_notification_api import router as email_notification_router

# Register router
app.include_router(email_notification_router)
```

### 5. Restart Service

```bash
# Restart ops-center container
docker restart ops-center-direct

# Check logs
docker logs ops-center-direct -f | grep -E "email|notification|scheduler"

# Verify scheduler started
curl http://localhost:8084/api/v1/notifications/health
```

---

## Troubleshooting

### Common Issues

#### 1. Emails Not Sending

**Symptoms**: API returns success but no email received

**Debug Steps**:
```bash
# Check email service configuration
docker exec ops-center-direct env | grep -E "EMAIL|SMTP"

# Check email service status
docker exec ops-center-direct python3 -c "
from email_service import email_service
print(f'Enabled: {email_service.enabled}')
print(f'Provider: {email_service.provider}')
"

# Test SMTP connection
docker exec ops-center-direct python3 -c "
import aiosmtplib
import asyncio

async def test():
    try:
        await aiosmtplib.send(
            message='',
            hostname='smtp.office365.com',
            port=587,
            start_tls=True,
            username='noreply@your-domain.com',
            password='your-password'
        )
        print('SMTP connection successful')
    except Exception as e:
        print(f'SMTP error: {e}')

asyncio.run(test())
"
```

**Solutions**:
- Verify SMTP credentials are correct
- Check firewall allows outbound SMTP (port 587)
- Enable "Authenticated SMTP" in Microsoft 365
- Use app-specific password (not account password)

#### 2. Scheduler Not Running

**Symptoms**: Scheduled jobs not executing

**Debug Steps**:
```bash
# Check scheduler status
curl http://localhost:8084/api/v1/notifications/health

# Check scheduler logs
docker logs ops-center-direct | grep -i scheduler

# Verify jobs are registered
docker exec ops-center-direct python3 -c "
from email_scheduler import email_scheduler
import asyncio

async def check():
    await email_scheduler.initialize()
    jobs = email_scheduler.scheduler.get_jobs()
    for job in jobs:
        print(f'{job.id}: {job.next_run_time}')
    await email_scheduler.close()

asyncio.run(check())
"
```

**Solutions**:
- Ensure `email_scheduler.start()` is called in server.py startup
- Check for APScheduler errors in logs
- Verify timezone settings (scheduler uses UTC)

#### 3. Templates Not Rendering

**Symptoms**: Email contains `{{ variable }}` placeholders

**Debug Steps**:
```bash
# Verify templates exist
docker exec ops-center-direct ls -la /app/email_templates/

# Test template rendering
docker exec ops-center-direct python3 -c "
from jinja2 import Template

template_str = open('/app/email_templates/welcome.html').read()
template = Template(template_str)
rendered = template.render(username='Test User', year=2025)
print('Rendered successfully' if '{{ ' not in rendered else 'Template error')
"
```

**Solutions**:
- Ensure all template files are copied to container
- Verify Jinja2 syntax in templates
- Check context variables match template placeholders

#### 4. Rate Limit Blocking Emails

**Symptoms**: Same notification not sent twice in 24 hours

**Expected Behavior**: This is intentional for alert-type emails (low_balance, payment_failure)

**Override** (for testing only):
```python
# Temporarily disable rate limiting in email_notifications.py
async def _check_rate_limit(self, user_id: str, notification_type: str) -> bool:
    return True  # Always allow (testing only)
```

#### 5. Keycloak User Not Found

**Symptoms**: "User not found in Keycloak" error

**Debug Steps**:
```bash
# Verify user exists in Keycloak
curl -X GET "http://uchub-keycloak:8080/admin/realms/uchub/users/{user_id}" \
  -H "Authorization: Bearer {admin-token}"

# Test Keycloak integration
docker exec ops-center-direct python3 -c "
import asyncio
from keycloak_integration import get_user_by_id

async def test():
    user = await get_user_by_id('user-id-here')
    print(f'Email: {user.get(\"email\")}')
    print(f'Username: {user.get(\"username\")}')

asyncio.run(test())
"
```

**Solutions**:
- Verify user ID is correct Keycloak UUID
- Check Keycloak admin token is valid
- Ensure user has email address in Keycloak profile

---

## Performance Considerations

### Database Queries

**Optimizations**:
- Index on `email_notifications_enabled` column
- Batch user queries (avoid N+1 queries)
- Limit transaction history lookups (LIMIT 1000)

### Email Sending

**Considerations**:
- Sending 1000 emails sequentially takes ~5-10 minutes
- Consider using background task queue (Celery/RQ) for large batches
- Rate limit API calls to avoid throttling

### Memory Usage

**APScheduler**:
- Minimal overhead (~5-10 MB)
- Runs in asyncio event loop (non-blocking)

**Email Service**:
- No persistent connections (each send creates new SMTP session)
- Jinja2 templates cached after first render

---

## Future Enhancements

### Phase 2 (Not Implemented Yet)

1. **Email Templates UI** - Admin panel for editing templates
2. **A/B Testing** - Test different email variants
3. **Click Tracking** - Track email link clicks
4. **Digest Mode** - Consolidate multiple alerts into daily digest
5. **SMS Notifications** - Add Twilio integration for SMS alerts
6. **Slack/Discord Webhooks** - Multi-channel notifications
7. **Localization** - Multi-language email templates
8. **Scheduled Reports** - Custom report scheduling

---

## Support & Documentation

### Related Documentation

- **Email Service**: `backend/email_service.py` (existing)
- **Credit System**: Epic 1.8 documentation
- **Keycloak Integration**: `backend/keycloak_integration.py`

### Contact

- **Implementation Team**: Email Notifications Team Lead
- **Support**: support@your-domain.com
- **Documentation**: This file

---

**Last Updated**: October 24, 2025
**Version**: 1.0.0
**Status**: ✅ PRODUCTION READY
