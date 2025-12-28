# Audit Logging Quick Reference

## Quick Start

### 1. Initialize Database
```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center/backend
python3 init_audit_db.py
```

### 2. Add to server.py
```python
# Imports
from audit_logger import audit_logger
from audit_helpers import log_auth_success, log_service_operation
from audit_endpoints import router as audit_router

# Include router
app.include_router(audit_router)
```

### 3. Use in Endpoints
```python
# Log authentication
await log_auth_success(request, user_id, username)

# Log service operation
await log_service_operation(
    request, user_id, username,
    "start", "service-name", True
)
```

## Common Operations

### Log Authentication
```python
from audit_helpers import log_auth_success, log_auth_failure

# Success
await log_auth_success(request, user.id, user.username)

# Failure
await log_auth_failure(request, username, "Invalid password")
```

### Log Service Operation
```python
from audit_helpers import log_service_operation

await log_service_operation(
    request=request,
    user_id=user.id,
    username=user.username,
    operation="start",  # or "stop", "restart"
    service_name="unicorn-chat",
    success=True,
    error_message=None  # if failed
)
```

### Log Model Operation
```python
from audit_helpers import log_model_operation

await log_model_operation(
    request=request,
    user_id=user.id,
    username=user.username,
    operation="download",  # or "delete", "configure"
    model_name="llama2-7b",
    success=True
)
```

### Log Permission Denial
```python
from audit_helpers import log_permission_denied

await log_permission_denied(
    request=request,
    user_id=user.id,
    username=user.username,
    resource_type="admin_endpoint",
    required_permission="admin"
)
```

### Custom Audit Log
```python
from audit_logger import audit_logger
from models.audit_log import AuditAction, AuditResult

await audit_logger.log(
    action=AuditAction.SYSTEM_UPDATE.value,
    result=AuditResult.SUCCESS.value,
    user_id=user.id,
    username=user.username,
    ip_address=get_client_ip(request),
    resource_type="system",
    resource_id="uc1-pro",
    metadata={"version": "1.0.0"}
)
```

## API Endpoints

### Query Logs
```bash
# All logs
curl "http://localhost:8084/api/v1/audit/logs?limit=100"

# By user
curl "http://localhost:8084/api/v1/audit/logs?username=admin"

# By action
curl "http://localhost:8084/api/v1/audit/logs?action=auth.login.failed"

# By date range
curl "http://localhost:8084/api/v1/audit/logs?start_date=2025-10-01T00:00:00&end_date=2025-10-09T23:59:59"

# Failed logins from specific IP
curl "http://localhost:8084/api/v1/audit/logs?action=auth.login.failed&ip_address=192.168.1.100"
```

### Statistics
```bash
# Last 30 days (default)
curl "http://localhost:8084/api/v1/audit/stats"

# Custom date range
curl "http://localhost:8084/api/v1/audit/stats?start_date=2025-10-01T00:00:00"
```

### Recent Logs
```bash
curl "http://localhost:8084/api/v1/audit/recent?limit=50"
```

### Security Events
```bash
curl "http://localhost:8084/api/v1/audit/security?limit=100"
```

### Available Actions
```bash
curl "http://localhost:8084/api/v1/audit/actions"
```

### Cleanup
```bash
curl -X DELETE "http://localhost:8084/api/v1/audit/cleanup?days_to_keep=90"
```

## Audit Actions Reference

### Authentication
- `auth.login.success`
- `auth.login.failed`
- `auth.logout`
- `auth.token.refresh`
- `auth.password.change`
- `auth.password.reset`

### Services
- `service.start`
- `service.stop`
- `service.restart`
- `service.configure`

### Models
- `model.download`
- `model.delete`
- `model.configure`
- `model.update`

### Network
- `network.configure`
- `network.dns.update`
- `network.firewall.update`

### Backups
- `backup.create`
- `backup.restore`
- `backup.delete`
- `backup.download`

### Users
- `user.create`
- `user.update`
- `user.delete`
- `user.role.change`
- `user.activate`
- `user.deactivate`

### Security
- `security.permission.denied`
- `security.csrf.failed`
- `security.ratelimit.exceeded`
- `security.token.invalid`
- `security.suspicious.activity`

### Data Access
- `data.view`
- `data.export`
- `config.view`
- `config.export`

### System
- `system.update`
- `system.restart`
- `system.shutdown`
- `system.package.install`
- `system.package.remove`

## Results
- `success` - Operation succeeded
- `failure` - Operation failed (expected error)
- `error` - Operation error (unexpected)
- `denied` - Permission denied

## Helper Functions

```python
from audit_helpers import (
    log_auth_success,      # Log successful login
    log_auth_failure,      # Log failed login
    log_logout,            # Log logout
    log_permission_denied, # Log access denial
    log_service_operation, # Log service ops
    log_model_operation,   # Log model ops
    log_user_management,   # Log user management
    log_data_access,       # Log data access
    get_client_ip,         # Get client IP (proxy-aware)
    get_user_agent,        # Get user agent
    get_session_id         # Get session ID
)
```

## Database Queries

### Direct SQL Queries
```bash
# Recent logs
sqlite3 data/ops_center.db "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 10;"

# Failed logins
sqlite3 data/ops_center.db "SELECT * FROM audit_logs WHERE action = 'auth.login.failed';"

# Logs by user
sqlite3 data/ops_center.db "SELECT * FROM audit_logs WHERE username = 'admin';"

# Count by action
sqlite3 data/ops_center.db "SELECT action, COUNT(*) FROM audit_logs GROUP BY action;"
```

### Python Queries
```python
# Query logs
from models.audit_log import AuditLogFilter

filter_params = AuditLogFilter(
    username="admin",
    action="service.start",
    limit=50
)
results = await audit_logger.query_logs(filter_params)

# Get statistics
stats = await audit_logger.get_statistics()
print(f"Total events: {stats.total_events}")
print(f"Failed logins: {stats.failed_logins}")
print(f"Suspicious IPs: {stats.recent_suspicious_ips}")
```

## Configuration

```python
from audit_logger import AuditLogger

audit_logger = AuditLogger(
    db_path="data/ops_center.db",      # Database path
    log_dir="/var/log/ops-center",     # Log directory
    enable_file_logging=True,          # Enable file logs
    enable_db_logging=True,            # Enable DB logs
    max_log_size_mb=100,               # Max log file size
    backup_count=10                    # Backup files to keep
)
```

## Testing

```bash
# Run test suite
python3 test_audit.py

# Check database
sqlite3 data/ops_center.db ".tables"
sqlite3 data/ops_center.db "SELECT COUNT(*) FROM audit_logs;"

# Check log files
ls -lh /var/log/ops-center/
tail -f /var/log/ops-center/audit.log
```

## Troubleshooting

### Database Permissions
```bash
chmod 666 data/ops_center.db
chmod 777 data/
```

### Log Directory
```bash
sudo mkdir -p /var/log/ops-center
sudo chown $USER:$USER /var/log/ops-center
sudo chmod 700 /var/log/ops-center
```

### Enable Debug
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Files Reference

- **`models/audit_log.py`** - Data models
- **`audit_logger.py`** - Core service
- **`audit_helpers.py`** - Helper functions
- **`audit_endpoints.py`** - API endpoints
- **`init_audit_db.py`** - DB initialization
- **`test_audit.py`** - Test suite
- **`migrations/001_create_audit_logs.py`** - DB migration

## Documentation

- **`docs/AUDIT_LOGGING.md`** - Full documentation
- **`docs/INTEGRATION_EXAMPLES.md`** - Integration guide
- **`docs/AUDIT_IMPLEMENTATION_SUMMARY.md`** - Implementation overview
- **`docs/AUDIT_QUICK_REFERENCE.md`** - This file

## Security Checklist

- [ ] Database permissions: `600`
- [ ] Log directory permissions: `700`
- [ ] Log files permissions: `600`
- [ ] Admin-only API access
- [ ] No passwords logged
- [ ] No full tokens logged
- [ ] Regular log cleanup enabled
- [ ] Monitoring suspicious IPs

## Maintenance Tasks

### Daily
- Monitor suspicious activity
- Review failed logins

### Weekly
- Check log file sizes
- Review security events

### Monthly
- Generate compliance reports
- Review statistics
- Clean up old logs (90+ days)

### Quarterly
- Audit log retention policy
- Review access patterns
- Update security policies

---

**Quick Help:**
- Full docs: `cat docs/AUDIT_LOGGING.md`
- Examples: `cat docs/INTEGRATION_EXAMPLES.md`
- Test: `python3 test_audit.py`
