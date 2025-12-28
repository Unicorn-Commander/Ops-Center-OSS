# Log Retention & Alert Notifications Architecture

**Date**: October 28, 2025
**Status**: Implementation Phase
**Lead**: Backend Infrastructure Team

---

## Overview

This document outlines the architecture for two new backend features:
1. **Log Retention Policy Management** - Configure and enforce log retention policies
2. **Alert Notification System** - Email and webhook notifications for system alerts

---

## 1. Log Retention Policy Management

### 1.1 Database Schema

**New Table**: `log_retention_policies`

```sql
CREATE TABLE IF NOT EXISTS log_retention_policies (
    id SERIAL PRIMARY KEY,
    policy_name VARCHAR(255) NOT NULL UNIQUE,
    retention_days INTEGER NOT NULL DEFAULT 30,
    auto_cleanup_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    cleanup_schedule VARCHAR(100) DEFAULT '0 2 * * *',  -- Daily at 2 AM
    applies_to TEXT[] DEFAULT ARRAY['audit_logs', 'system_logs', 'docker_logs'],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    last_cleanup_at TIMESTAMP,
    CONSTRAINT valid_retention_days CHECK (retention_days >= 1 AND retention_days <= 365)
);

-- Create default policy
INSERT INTO log_retention_policies (policy_name, retention_days, applies_to)
VALUES ('default', 30, ARRAY['audit_logs', 'system_logs', 'docker_logs'])
ON CONFLICT (policy_name) DO NOTHING;

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_log_retention_policy_name ON log_retention_policies(policy_name);
```

**Existing Table Enhancement**: Add retention metadata to `audit_logs`

```sql
-- Add retention_until column to audit_logs (optional, for explicit tracking)
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS retention_until TIMESTAMP;
CREATE INDEX IF NOT EXISTS idx_audit_logs_retention ON audit_logs(retention_until) WHERE retention_until IS NOT NULL;
```

### 1.2 API Endpoints

**Base Path**: `/api/v1/logs/retention`

```python
# Get current retention policy
GET /api/v1/logs/retention
Response: {
    "policy_name": "default",
    "retention_days": 30,
    "auto_cleanup_enabled": true,
    "cleanup_schedule": "0 2 * * *",
    "applies_to": ["audit_logs", "system_logs", "docker_logs"],
    "last_cleanup_at": "2025-10-28T02:00:00Z"
}

# Update retention policy
PUT /api/v1/logs/retention
Body: {
    "retention_days": 60,
    "auto_cleanup_enabled": true,
    "cleanup_schedule": "0 3 * * *"
}
Response: {
    "success": true,
    "policy": {...},
    "message": "Retention policy updated successfully"
}

# Trigger manual cleanup
POST /api/v1/logs/retention/cleanup
Response: {
    "success": true,
    "deleted_count": 1250,
    "log_types": {
        "audit_logs": 500,
        "system_logs": 450,
        "docker_logs": 300
    },
    "cutoff_date": "2025-09-28T00:00:00Z"
}

# Get cleanup history
GET /api/v1/logs/retention/history
Response: {
    "cleanups": [
        {
            "timestamp": "2025-10-28T02:00:00Z",
            "deleted_count": 1250,
            "duration_seconds": 5.2,
            "trigger": "scheduled"
        }
    ]
}
```

### 1.3 Backend Implementation

**File**: `backend/log_retention_api.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import asyncpg

class LogRetentionPolicy(BaseModel):
    retention_days: int = Field(ge=1, le=365, default=30)
    auto_cleanup_enabled: bool = True
    cleanup_schedule: str = "0 2 * * *"

class LogRetentionManager:
    async def get_policy(self) -> LogRetentionPolicy:
        """Get current retention policy from database"""
        pass

    async def update_policy(self, policy: LogRetentionPolicy) -> dict:
        """Update retention policy in database"""
        pass

    async def cleanup_logs(self) -> dict:
        """Execute log cleanup based on retention policy"""
        # 1. Get retention policy
        # 2. Calculate cutoff date
        # 3. Delete audit_logs older than cutoff
        # 4. Delete system logs (file-based)
        # 5. Delete Docker logs (via docker logs prune)
        # 6. Record cleanup history
        pass
```

**File**: `backend/log_cleanup_service.py`

```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class LogCleanupService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        """Start scheduled cleanup service"""
        policy = await log_retention_manager.get_policy()
        if policy.auto_cleanup_enabled:
            self.scheduler.add_job(
                log_retention_manager.cleanup_logs,
                CronTrigger.from_crontab(policy.cleanup_schedule),
                id='log_cleanup',
                replace_existing=True
            )
            self.scheduler.start()

    async def stop(self):
        """Stop cleanup service"""
        self.scheduler.shutdown()
```

### 1.4 Frontend UI

**File**: `src/pages/Logs.jsx` (Enhancement)

Add retention settings panel:

```jsx
// Add to Logs.jsx advanced filters section
<div className="retention-settings">
  <h3>Log Retention Policy</h3>
  <div className="form-group">
    <label>Retention Period</label>
    <select value={retentionDays} onChange={handleRetentionChange}>
      <option value={7}>7 days</option>
      <option value={14}>14 days</option>
      <option value={30}>30 days (Default)</option>
      <option value={60}>60 days</option>
      <option value={90}>90 days</option>
    </select>
  </div>
  <div className="form-group">
    <label>
      <input type="checkbox" checked={autoCleanup} onChange={...} />
      Auto-cleanup enabled
    </label>
  </div>
  <button onClick={handleSaveRetention}>Save Policy</button>
  <button onClick={handleManualCleanup}>Manual Cleanup</button>
</div>
```

---

## 2. Alert Notification System

### 2.1 Database Schema

**New Table**: `alert_notification_config`

```sql
CREATE TABLE IF NOT EXISTS alert_notification_config (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),  -- NULL = system-wide config
    organization_id VARCHAR(36),  -- NULL = system-wide config
    channel_type VARCHAR(50) NOT NULL CHECK (channel_type IN ('email', 'webhook', 'both')),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- Email config
    email_recipients TEXT[],
    email_on_severities TEXT[] DEFAULT ARRAY['critical', 'error'],

    -- Webhook config
    webhook_url VARCHAR(512),
    webhook_method VARCHAR(10) DEFAULT 'POST',
    webhook_headers JSONB,
    webhook_on_severities TEXT[] DEFAULT ARRAY['critical', 'error'],

    -- Rate limiting
    rate_limit_minutes INTEGER DEFAULT 60,
    last_notification_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_channel_config CHECK (
        (channel_type = 'email' AND email_recipients IS NOT NULL) OR
        (channel_type = 'webhook' AND webhook_url IS NOT NULL) OR
        (channel_type = 'both' AND email_recipients IS NOT NULL AND webhook_url IS NOT NULL)
    )
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_alert_notification_user ON alert_notification_config(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_notification_org ON alert_notification_config(organization_id);
```

**New Table**: `alert_notification_history`

```sql
CREATE TABLE IF NOT EXISTS alert_notification_history (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(255) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    alert_severity VARCHAR(50) NOT NULL,
    channel_type VARCHAR(50) NOT NULL,
    recipient VARCHAR(512),
    status VARCHAR(50) NOT NULL CHECK (status IN ('sent', 'failed', 'rate_limited')),
    error_message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Index for analytics
    INDEX idx_alert_notification_history_alert(alert_id),
    INDEX idx_alert_notification_history_status(status),
    INDEX idx_alert_notification_history_sent_at(sent_at)
);
```

### 2.2 API Endpoints

**Base Path**: `/api/v1/alerts/notifications`

```python
# Get notification configuration
GET /api/v1/alerts/notifications/config
Response: {
    "channel_type": "both",
    "enabled": true,
    "email": {
        "recipients": ["admin@example.com"],
        "severities": ["critical", "error"]
    },
    "webhook": {
        "url": "https://hooks.slack.com/services/...",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "severities": ["critical", "error", "warning"]
    },
    "rate_limit_minutes": 60
}

# Update notification configuration
PUT /api/v1/alerts/notifications/config
Body: {
    "channel_type": "both",
    "enabled": true,
    "email": {
        "recipients": ["admin@example.com", "ops@example.com"],
        "severities": ["critical", "error"]
    },
    "webhook": {
        "url": "https://hooks.slack.com/services/...",
        "severities": ["critical"]
    },
    "rate_limit_minutes": 30
}
Response: {
    "success": true,
    "config": {...}
}

# Test notification (dry-run)
POST /api/v1/alerts/notifications/test
Body: {
    "channel_type": "email",
    "test_alert": {
        "severity": "warning",
        "message": "Test notification"
    }
}
Response: {
    "success": true,
    "sent": true,
    "channel": "email",
    "recipient": "admin@example.com"
}

# Get notification history
GET /api/v1/alerts/notifications/history?limit=50
Response: {
    "notifications": [
        {
            "alert_type": "high_cpu",
            "severity": "critical",
            "channel": "email",
            "recipient": "admin@example.com",
            "status": "sent",
            "sent_at": "2025-10-28T10:30:00Z"
        }
    ],
    "total": 150,
    "success_rate": 0.98
}
```

### 2.3 Backend Implementation

**File**: `backend/alert_notification_api.py`

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import asyncio
import httpx

class AlertNotificationConfig(BaseModel):
    channel_type: str  # email, webhook, both
    enabled: bool = True
    email: Optional[EmailConfig] = None
    webhook: Optional[WebhookConfig] = None
    rate_limit_minutes: int = 60

class EmailConfig(BaseModel):
    recipients: List[str]
    severities: List[str] = ["critical", "error"]

class WebhookConfig(BaseModel):
    url: HttpUrl
    method: str = "POST"
    headers: Dict[str, str] = {}
    severities: List[str] = ["critical", "error"]

class AlertNotificationManager:
    async def get_config(self, user_id: Optional[str] = None) -> AlertNotificationConfig:
        """Get notification configuration"""
        pass

    async def update_config(self, config: AlertNotificationConfig) -> dict:
        """Update notification configuration"""
        pass

    async def should_send_notification(self, alert: Alert, config: AlertNotificationConfig) -> bool:
        """Check if notification should be sent (rate limiting)"""
        pass

    async def send_email_notification(self, alert: Alert, recipients: List[str]) -> bool:
        """Send email notification using existing email_service"""
        from email_notifications import email_notification_service

        subject = f"[{alert.severity.upper()}] System Alert: {alert.type}"
        body = f"""
        Alert Type: {alert.type}
        Severity: {alert.severity}
        Message: {alert.message}
        Timestamp: {alert.timestamp}
        Details: {json.dumps(alert.details, indent=2)}
        """

        success = await email_notification_service.send_email(
            to=recipients[0],
            subject=subject,
            text_content=body
        )
        return success

    async def send_webhook_notification(self, alert: Alert, webhook: WebhookConfig) -> bool:
        """Send webhook notification"""
        async with httpx.AsyncClient() as client:
            payload = {
                "alert_type": alert.type,
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "details": alert.details
            }

            response = await client.request(
                webhook.method,
                str(webhook.url),
                json=payload,
                headers=webhook.headers,
                timeout=10.0
            )
            return response.status_code < 300

    async def record_notification(self, alert: Alert, channel: str, recipient: str, status: str) -> None:
        """Record notification in history"""
        pass
```

**Integration with `alert_manager.py`**:

```python
# In AlertManager.check_alerts() method, add after alert creation:

async def check_alerts(self) -> List[Dict]:
    """Check for new alerts and send notifications"""
    # ... existing alert checking code ...

    for alert in new_alerts:
        if alert.id not in self.active_alerts:
            self.active_alerts[alert.id] = alert
            self.alert_history.append(alert)

            # NEW: Send notifications for new alerts
            await self._send_alert_notifications(alert)

    return [a.to_dict() for a in self.active_alerts.values()]

async def _send_alert_notifications(self, alert: Alert) -> None:
    """Send notifications for alert"""
    try:
        from alert_notification_api import alert_notification_manager

        # Get notification config
        config = await alert_notification_manager.get_config()

        if not config.enabled:
            return

        # Check rate limiting
        if not await alert_notification_manager.should_send_notification(alert, config):
            logger.info(f"Alert {alert.id} rate-limited")
            return

        # Send email notifications
        if config.channel_type in ['email', 'both']:
            if alert.severity.value in config.email.severities:
                await alert_notification_manager.send_email_notification(
                    alert, config.email.recipients
                )

        # Send webhook notifications
        if config.channel_type in ['webhook', 'both']:
            if alert.severity.value in config.webhook.severities:
                await alert_notification_manager.send_webhook_notification(
                    alert, config.webhook
                )

    except Exception as e:
        logger.error(f"Failed to send alert notifications: {e}")
```

### 2.4 Frontend UI

**New Component**: `src/components/AlertNotificationSettings.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { Switch, Select, Input, Button } from '@mui/material';

export default function AlertNotificationSettings() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    const response = await fetch('/api/v1/alerts/notifications/config');
    const data = await response.json();
    setConfig(data);
    setLoading(false);
  };

  const saveConfig = async () => {
    await fetch('/api/v1/alerts/notifications/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    alert('Configuration saved!');
  };

  const testNotification = async (channel) => {
    await fetch('/api/v1/alerts/notifications/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel_type: channel })
    });
    alert(`Test ${channel} sent!`);
  };

  return (
    <div className="alert-notification-settings">
      <h2>Alert Notifications</h2>

      <div className="form-section">
        <label>
          <Switch checked={config?.enabled} onChange={...} />
          Enable Notifications
        </label>
      </div>

      <div className="form-section">
        <h3>Email Notifications</h3>
        <Input
          label="Recipients (comma-separated)"
          value={config?.email?.recipients?.join(', ')}
          onChange={...}
        />
        <Select
          multiple
          label="Severities"
          value={config?.email?.severities}
          onChange={...}
        >
          <option value="critical">Critical</option>
          <option value="error">Error</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
        </Select>
        <Button onClick={() => testNotification('email')}>Test Email</Button>
      </div>

      <div className="form-section">
        <h3>Webhook Notifications</h3>
        <Input
          label="Webhook URL"
          value={config?.webhook?.url}
          onChange={...}
        />
        <Select
          multiple
          label="Severities"
          value={config?.webhook?.severities}
          onChange={...}
        >
          <option value="critical">Critical</option>
          <option value="error">Error</option>
          <option value="warning">Warning</option>
        </Select>
        <Button onClick={() => testNotification('webhook')}>Test Webhook</Button>
      </div>

      <div className="form-section">
        <h3>Rate Limiting</h3>
        <Input
          type="number"
          label="Minimum minutes between notifications"
          value={config?.rate_limit_minutes}
          onChange={...}
        />
      </div>

      <Button variant="contained" onClick={saveConfig}>Save Configuration</Button>
    </div>
  );
}
```

**Integration**: Add to Security or Settings page

```jsx
// In src/pages/Security.jsx or Settings.jsx
import AlertNotificationSettings from '../components/AlertNotificationSettings';

// Add tab or section
<Tab label="Alert Notifications">
  <AlertNotificationSettings />
</Tab>
```

---

## 3. Implementation Checklist

### 3.1 Database Migrations

- [ ] Create `log_retention_policies` table
- [ ] Create `alert_notification_config` table
- [ ] Create `alert_notification_history` table
- [ ] Add indexes for performance
- [ ] Insert default policies

### 3.2 Backend APIs

- [ ] `log_retention_api.py` - GET/PUT retention policy
- [ ] `log_cleanup_service.py` - Scheduled cleanup service
- [ ] `alert_notification_api.py` - GET/PUT notification config
- [ ] Integration with `alert_manager.py` - Auto-send notifications
- [ ] Integration with `email_notifications.py` - Reuse email sender

### 3.3 Frontend UIs

- [ ] Enhance `Logs.jsx` with retention settings
- [ ] Create `AlertNotificationSettings.jsx` component
- [ ] Add to Security or Settings page
- [ ] Test email/webhook configuration

### 3.4 Testing

- [ ] Unit tests for retention API
- [ ] Unit tests for notification API
- [ ] Integration test: Log cleanup service
- [ ] Integration test: Alert → Email notification
- [ ] Integration test: Alert → Webhook notification
- [ ] End-to-end test: UI → API → Database

### 3.5 Documentation

- [ ] API reference for retention endpoints
- [ ] API reference for notification endpoints
- [ ] Admin guide: Configuring log retention
- [ ] Admin guide: Setting up alert notifications
- [ ] Troubleshooting guide

---

## 4. Dependencies

**Backend**:
- `asyncpg` - Already installed
- `apscheduler` - For cron-based cleanup (install: `pip install apscheduler`)
- `httpx` - For webhook HTTP client (install: `pip install httpx`)

**Frontend**:
- No new dependencies needed (uses existing MUI components)

---

## 5. Security Considerations

1. **Rate Limiting**: Prevent notification spam
2. **Webhook Validation**: Validate webhook URLs before saving
3. **Email Validation**: Validate email addresses
4. **Authentication**: All endpoints require admin role
5. **Audit Logging**: Log all configuration changes
6. **Webhook Secrets**: Support webhook signature verification (future)

---

## 6. Performance Considerations

1. **Async Notifications**: Don't block alert creation
2. **Batch Cleanup**: Delete logs in batches (1000 records at a time)
3. **Index Usage**: Ensure cleanup queries use timestamp indexes
4. **Webhook Timeout**: 10-second timeout for webhook calls
5. **Connection Pooling**: Reuse HTTP clients for webhooks

---

## 7. Future Enhancements

1. **Multiple Recipients**: Support multiple webhook URLs
2. **Notification Templates**: Customizable email/webhook templates
3. **Slack Integration**: Built-in Slack connector
4. **PagerDuty Integration**: Built-in PagerDuty connector
5. **Alert Aggregation**: Group similar alerts before notification
6. **Webhook Retries**: Retry failed webhook deliveries
7. **Email Attachments**: Include log excerpts as attachments
8. **SMS Notifications**: SMS via Twilio integration

---

**End of Architecture Document**
