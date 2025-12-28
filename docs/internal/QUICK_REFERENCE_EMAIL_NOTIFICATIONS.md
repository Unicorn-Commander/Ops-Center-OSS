# Email Notifications Quick Reference Card

**Epic**: 2.3 - Email Notifications
**Version**: 1.0.0
**Last Updated**: October 24, 2025

---

## One-Line Summary

Automated email notification system with 7 notification types, scheduled jobs, and API management.

---

## Quick Start

### Send Test Email
```bash
USER_ID="your-keycloak-user-id"

curl -X POST http://localhost:8084/api/v1/notifications/send/welcome \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"tier\": \"trial\"}"
```

### Check Health
```bash
curl http://localhost:8084/api/v1/notifications/health
```

### View Logs
```bash
docker logs ops-center-direct -f | grep -E "email|notification"
```

---

## 7 Notification Types

| # | Type | Trigger | Schedule |
|---|------|---------|----------|
| 1 | Low Balance Alert | Credits < 10% | Daily 9 AM |
| 2 | Monthly Reset | First of month | 1st @ midnight |
| 3 | Coupon Redeemed | Instant | On redemption |
| 4 | Welcome Email | Instant | On signup |
| 5 | Tier Upgrade | Instant | On upgrade |
| 6 | Payment Failure | Instant | On Stripe event |
| 7 | Usage Summary | Weekly | Monday 9 AM |

---

## API Endpoints

```bash
# Base path
/api/v1/notifications

# Manual sends
POST /send/low-balance
POST /send/monthly-reset
POST /send/coupon-redeemed
POST /send/welcome
POST /send/tier-upgrade
POST /send/payment-failure

# Preferences
GET  /preferences/{user_id}
PUT  /preferences/{user_id}
GET  /unsubscribe/{user_id}  # Public

# Health
GET  /health
```

---

## Files Locations

```
/backend/email_notifications.py       # Notification service (535 lines)
/backend/email_scheduler.py           # APScheduler jobs (458 lines)
/backend/email_notification_api.py    # FastAPI endpoints (565 lines)
/backend/email_templates/             # 7 events × 2 formats
/backend/migrations/add_email_notifications_column.sql
```

---

## Common Commands

### Database
```bash
# Apply migration
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -f /app/migrations/add_email_notifications_column.sql

# Check column exists
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "\d user_credits"

# Query preferences
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT user_id, email_notifications_enabled FROM user_credits LIMIT 10;"
```

### Testing
```bash
# Send welcome email
curl -X POST http://localhost:8084/api/v1/notifications/send/welcome \
  -H "Content-Type: application/json" \
  -d '{"user_id": "UUID", "tier": "trial"}'

# Send low balance alert
curl -X POST http://localhost:8084/api/v1/notifications/send/low-balance \
  -H "Content-Type: application/json" \
  -d '{"user_id": "UUID"}'

# Check preferences
curl http://localhost:8084/api/v1/notifications/preferences/UUID

# Unsubscribe user
curl http://localhost:8084/api/v1/notifications/unsubscribe/UUID
```

### Monitoring
```bash
# Check scheduler status
curl http://localhost:8084/api/v1/notifications/health

# View recent logs
docker logs ops-center-direct --tail 100 | grep notification

# View scheduler logs
docker logs ops-center-direct | grep -i "scheduler\|APScheduler"

# View email sending logs
docker logs ops-center-direct | grep -i "email.*sent"
```

---

## Troubleshooting

### Problem: Emails Not Sending

**Check 1**: Email service enabled
```bash
docker exec ops-center-direct env | grep EMAIL_ENABLED
# Should be: EMAIL_ENABLED=true
```

**Check 2**: SMTP credentials
```bash
docker exec ops-center-direct env | grep SMTP
# Verify: SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD
```

**Check 3**: Test SMTP connection
```bash
docker exec ops-center-direct python3 -c "
import aiosmtplib, asyncio
async def test():
    try:
        await aiosmtplib.send(message='', hostname='smtp.office365.com', port=587)
        print('✅ SMTP OK')
    except Exception as e:
        print(f'❌ SMTP Error: {e}')
asyncio.run(test())
"
```

### Problem: Scheduler Not Running

**Check 1**: Health endpoint
```bash
curl http://localhost:8084/api/v1/notifications/health
# "scheduler_running": should be true
```

**Check 2**: Verify jobs registered
```bash
docker exec ops-center-direct python3 -c "
from email_scheduler import email_scheduler
import asyncio
async def check():
    await email_scheduler.initialize()
    jobs = email_scheduler.scheduler.get_jobs()
    for job in jobs:
        print(f'{job.id}: {job.next_run_time}')
asyncio.run(check())
"
```

**Fix**: Ensure `email_scheduler.start()` is in server.py startup

### Problem: Templates Not Rendering

**Check**: Templates exist
```bash
docker exec ops-center-direct ls -la /app/email_templates/
```

**Verify**: All 14 files present (7 × 2 formats)

### Problem: User Not Receiving Emails

**Check 1**: User has email in Keycloak
```bash
docker exec ops-center-direct python3 -c "
import asyncio
from keycloak_integration import get_user_by_id
async def check():
    user = await get_user_by_id('USER_ID')
    print(f'Email: {user.get(\"email\")}')
asyncio.run(check())
"
```

**Check 2**: Notifications enabled for user
```bash
curl http://localhost:8084/api/v1/notifications/preferences/USER_ID
# email_notifications_enabled should be true
```

**Check 3**: Rate limit not blocking
- Low balance and payment failure alerts: Max 1 per 24 hours
- Other notifications: No limit

---

## Configuration

### Environment Variables (Required)
```bash
# Already configured in .env.auth
EMAIL_ENABLED=true
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=noreply@your-domain.com
SMTP_PASSWORD=<app-password>
APP_URL=https://your-domain.com
SUPPORT_EMAIL=support@your-domain.com
```

### Database Schema
```sql
-- user_credits table
email_notifications_enabled BOOLEAN DEFAULT TRUE

-- Index for performance
idx_user_credits_email_enabled ON (email_notifications_enabled)
```

### Scheduled Jobs
```python
# APScheduler CronTriggers
Low Balance:     CronTrigger(hour=9, minute=0)           # Daily 9 AM
Monthly Reset:   CronTrigger(day=1, hour=0, minute=0)   # 1st @ midnight
Usage Summary:   CronTrigger(day_of_week="mon", hour=9) # Monday 9 AM
```

---

## Performance Metrics

| Metric | Expected Value |
|--------|----------------|
| Email send time | ~500ms (SMTP) |
| API response | <200ms |
| Template render | <10ms |
| Job execution | 5-10 min (1000 users) |
| Memory usage | ~10 MB (scheduler) |
| CPU usage | <5% |

---

## Security Notes

- ✅ Rate limiting: Max 1 alert per user per day
- ✅ Audit logging: All operations logged
- ✅ User preferences: Respects opt-out
- ✅ Template injection: Jinja2 auto-escapes
- ✅ Email spoofing: SPF/DKIM configured
- ✅ No sensitive data in emails

---

## Rate Limits

| Notification Type | Limit |
|-------------------|-------|
| Low Balance | 1 per 24 hours |
| Payment Failure | 1 per 24 hours |
| All Others | No limit |

---

## Documentation Links

- **Implementation Guide**: `/EMAIL_NOTIFICATIONS_GUIDE.md` (800+ lines)
- **Summary Report**: `/EPIC_2.3_IMPLEMENTATION_SUMMARY.md` (350+ lines)
- **PM Handoff**: `/PM_HANDOFF_EPIC_2.3.md`

---

## Support Contacts

- **Implementation**: Email Notifications Team Lead
- **Ops Support**: DevOps Team
- **User Issues**: support@your-domain.com

---

## Quick Debugging Commands

```bash
# View all notification logs
docker logs ops-center-direct | grep -i notification

# View scheduler execution
docker logs ops-center-direct | grep -i "Job.*executed"

# View email sending
docker logs ops-center-direct | grep "Email sent"

# Check database preferences
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT COUNT(*), email_notifications_enabled FROM user_credits GROUP BY email_notifications_enabled;"

# Check audit logs
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT * FROM audit_logs WHERE action LIKE 'email.%' ORDER BY timestamp DESC LIMIT 10;"
```

---

## Emergency Commands

### Stop Scheduler (if spamming)
```bash
docker exec ops-center-direct python3 -c "
from email_scheduler import email_scheduler
import asyncio
async def stop():
    await email_scheduler.initialize()
    email_scheduler.scheduler.shutdown()
    print('Scheduler stopped')
asyncio.run(stop())
"

# Then restart container
docker restart ops-center-direct
```

### Disable Notifications for All Users
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "UPDATE user_credits SET email_notifications_enabled = FALSE;"
```

### Re-enable Notifications
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "UPDATE user_credits SET email_notifications_enabled = TRUE;"
```

---

**Quick Reference Version**: 1.0.0
**Last Updated**: October 24, 2025
**Status**: Production Ready
