# Audit Logging System

Comprehensive audit logging for the UC-1 Pro Ops Center backend.

## Overview

The audit logging system tracks all security-relevant events, user actions, and system operations. It provides both database and file-based logging for redundancy and compliance.

## Features

- **Dual Storage**: Logs to both SQLite database and rotating log files
- **Async Logging**: Non-blocking async operations for performance
- **Comprehensive Events**: Tracks authentication, authorization, data access, and system operations
- **Rich Metadata**: Captures IP address, user agent, timestamps, and custom metadata
- **Tamper-Evident**: Database indexes and file rotation prevent log tampering
- **Query API**: REST API for searching and analyzing audit logs
- **Statistics**: Built-in analytics for security monitoring

## Architecture

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  (server.py, various endpoints)         │
└──────────────┬──────────────────────────┘
               │
               ├──> audit_helpers.py
               │    (Helper functions)
               │
               ├──> audit_logger.py
               │    (Core logging service)
               │
               ├──────┬──────────────────┐
               │      │                  │
          ┌────▼──┐  ┌▼──────────────┐  │
          │  DB   │  │  Log Files    │  │
          │SQLite │  │/var/log/...   │  │
          └───────┘  └───────────────┘  │
                                        │
                    ┌───────────────────▼────┐
                    │  audit_endpoints.py    │
                    │  (Query API)           │
                    └────────────────────────┘
```

## File Structure

```
backend/
├── models/
│   ├── __init__.py
│   └── audit_log.py           # Data models
├── audit_logger.py             # Core logging service
├── audit_helpers.py            # Helper functions
├── audit_endpoints.py          # REST API endpoints
├── init_audit_db.py           # Database initialization
└── migrations/
    └── 001_create_audit_logs.py
```

## Database Schema

```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user_id TEXT,
    username TEXT,
    ip_address TEXT,
    user_agent TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    result TEXT NOT NULL,
    error_message TEXT,
    metadata TEXT,
    session_id TEXT
);

-- Indexes for performance
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_result ON audit_logs(result);
CREATE INDEX idx_audit_ip_address ON audit_logs(ip_address);
```

## Audit Actions

### Authentication
- `auth.login.success` - Successful login
- `auth.login.failed` - Failed login attempt
- `auth.logout` - User logout
- `auth.token.refresh` - Token refresh
- `auth.password.change` - Password change
- `auth.password.reset` - Password reset

### Service Management
- `service.start` - Service started
- `service.stop` - Service stopped
- `service.restart` - Service restarted
- `service.configure` - Service configuration changed

### Model Management
- `model.download` - Model downloaded
- `model.delete` - Model deleted
- `model.configure` - Model configuration changed
- `model.update` - Model updated

### Network Configuration
- `network.configure` - Network settings changed
- `network.dns.update` - DNS settings updated
- `network.firewall.update` - Firewall rules updated

### Backup & Restore
- `backup.create` - Backup created
- `backup.restore` - Backup restored
- `backup.delete` - Backup deleted
- `backup.download` - Backup downloaded

### User Management
- `user.create` - User created
- `user.update` - User updated
- `user.delete` - User deleted
- `user.role.change` - User role changed
- `user.activate` - User activated
- `user.deactivate` - User deactivated

### Security Events
- `security.permission.denied` - Permission denied
- `security.csrf.failed` - CSRF validation failed
- `security.ratelimit.exceeded` - Rate limit exceeded
- `security.token.invalid` - Invalid token
- `security.suspicious.activity` - Suspicious activity detected

### Data Access
- `data.view` - Data viewed
- `data.export` - Data exported
- `config.view` - Configuration viewed
- `config.export` - Configuration exported

### System Operations
- `system.update` - System updated
- `system.restart` - System restarted
- `system.shutdown` - System shutdown
- `system.package.install` - Package installed
- `system.package.remove` - Package removed

## Usage Examples

### Basic Logging

```python
from audit_logger import audit_logger
from models.audit_log import AuditAction, AuditResult

# Log a successful login
await audit_logger.log(
    action=AuditAction.AUTH_LOGIN_SUCCESS.value,
    result=AuditResult.SUCCESS.value,
    user_id="user123",
    username="john_doe",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0...",
    metadata={"login_method": "password"}
)
```

### Using Helper Functions

```python
from audit_helpers import log_auth_success, log_service_operation

# Log authentication
await log_auth_success(
    request=request,
    user_id="user123",
    username="john_doe",
    metadata={"method": "oauth"}
)

# Log service operation
await log_service_operation(
    request=request,
    user_id="admin1",
    username="admin",
    operation="start",
    service_name="unicorn-open-webui",
    success=True
)
```

### Using Decorator

```python
from audit_helpers import audit_operation
from models.audit_log import AuditAction

@audit_operation(
    action=AuditAction.SERVICE_START.value,
    resource_type="service",
    get_resource_id=lambda kwargs: kwargs.get("service_name")
)
async def start_service(request: Request, service_name: str):
    # Service start logic
    docker_manager.start_service(service_name)
    return {"status": "started"}
```

### Integration in FastAPI Endpoints

```python
from fastapi import APIRouter, Request
from audit_helpers import log_auth_failure, get_client_ip

@app.post("/api/auth/login")
async def login(request: Request, credentials: LoginCredentials):
    try:
        user = authenticate(credentials.username, credentials.password)

        await log_auth_success(
            request=request,
            user_id=user.id,
            username=user.username
        )

        return {"token": create_token(user)}

    except AuthenticationError as e:
        await log_auth_failure(
            request=request,
            username=credentials.username,
            reason=str(e)
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
```

## API Endpoints

### Query Audit Logs

```bash
GET /api/v1/audit/logs

# Query parameters:
# - user_id: Filter by user ID
# - username: Filter by username
# - action: Filter by action
# - resource_type: Filter by resource type
# - result: Filter by result (success/failure/error/denied)
# - start_date: Start date (ISO format)
# - end_date: End date (ISO format)
# - ip_address: Filter by IP address
# - limit: Results per page (max 1000)
# - offset: Pagination offset

curl "http://localhost:8084/api/v1/audit/logs?username=admin&limit=50"
```

### Get Audit Statistics

```bash
GET /api/v1/audit/stats

# Query parameters:
# - start_date: Start date (defaults to 30 days ago)
# - end_date: End date (defaults to now)

curl "http://localhost:8084/api/v1/audit/stats?start_date=2025-10-01T00:00:00"
```

### Get Available Actions

```bash
GET /api/v1/audit/actions

curl "http://localhost:8084/api/v1/audit/actions"
```

### Get Recent Logs

```bash
GET /api/v1/audit/recent?limit=100

curl "http://localhost:8084/api/v1/audit/recent?limit=100"
```

### Get Security Events

```bash
GET /api/v1/audit/security

curl "http://localhost:8084/api/v1/audit/security?limit=50"
```

### Clean Up Old Logs

```bash
DELETE /api/v1/audit/cleanup?days_to_keep=90

curl -X DELETE "http://localhost:8084/api/v1/audit/cleanup?days_to_keep=90"
```

## Configuration

### Initialize Database

```bash
cd /home/deploy/Production/UC-1-Pro/services/ops-center/backend
python3 init_audit_db.py
```

### Log File Configuration

Audit logs are written to: `/var/log/ops-center/audit.log`

Configuration in `audit_logger.py`:
- `max_log_size_mb`: Maximum log file size (default: 100 MB)
- `backup_count`: Number of backup files (default: 10)

### Adjust Settings

```python
from audit_logger import AuditLogger

# Custom configuration
audit_logger = AuditLogger(
    db_path="data/ops_center.db",
    log_dir="/var/log/ops-center",
    enable_file_logging=True,
    enable_db_logging=True,
    max_log_size_mb=200,  # 200 MB per file
    backup_count=20       # Keep 20 backup files
)
```

## Security Considerations

### What is Logged

✅ **Logged:**
- User IDs and usernames
- IP addresses
- User agents
- Timestamps
- Actions performed
- Resources affected
- Results (success/failure)
- Error messages
- Session IDs
- Non-sensitive metadata

❌ **NOT Logged:**
- Passwords (plain or hashed)
- API keys or tokens (full values)
- Sensitive user data (SSN, credit cards, etc.)
- Personal health information
- Private encryption keys

### Tamper Evidence

1. **Database Constraints**: Timestamp and action fields are NOT NULL
2. **Indexes**: Improve query performance and data integrity
3. **Append-Only**: No UPDATE operations on audit logs
4. **File Rotation**: Old logs archived, not modified
5. **Permissions**: Restrict write access to audit logger service only

### Access Control

- Audit log endpoints require **admin role**
- Database file permissions: `600` (owner read/write only)
- Log file permissions: `600` (owner read/write only)
- Log directory permissions: `700` (owner access only)

## Monitoring and Alerts

### Suspicious Activity Detection

The system automatically tracks:
- Multiple failed login attempts from same IP
- Permission denials
- CSRF validation failures
- Rate limit violations

Query suspicious IPs:

```python
stats = await audit_logger.get_statistics()
print(f"Suspicious IPs: {stats.recent_suspicious_ips}")
```

### Failed Login Monitoring

```python
# Get failed logins in last 24 hours
filter_params = AuditLogFilter(
    action=AuditAction.AUTH_LOGIN_FAILED.value,
    start_date=(datetime.utcnow() - timedelta(hours=24)).isoformat()
)
logs = await audit_logger.query_logs(filter_params)
```

## Performance

- **Async Operations**: Non-blocking I/O
- **Database Indexes**: Fast queries on common filters
- **Log Rotation**: Prevents disk space issues
- **Pagination**: Efficient handling of large result sets
- **Background Tasks**: Heavy operations run in thread pool

## Compliance

The audit logging system helps meet compliance requirements for:

- **GDPR**: Track data access and modifications
- **SOC 2**: Security monitoring and incident response
- **ISO 27001**: Information security management
- **HIPAA**: Healthcare data access audit trails
- **PCI DSS**: Payment card data security

## Maintenance

### Database Cleanup

```bash
# Clean up logs older than 90 days
curl -X DELETE "http://localhost:8084/api/v1/audit/cleanup?days_to_keep=90"
```

### Manual Cleanup

```python
# From Python
deleted = await audit_logger.cleanup_old_logs(days_to_keep=90)
print(f"Deleted {deleted} old audit logs")
```

### Log Rotation

Log files automatically rotate when they reach the configured size. Old logs are compressed and numbered:

```
/var/log/ops-center/
├── audit.log          # Current log
├── audit.log.1        # Previous log
├── audit.log.2
└── ...
```

### Backup Audit Logs

```bash
# Backup database
sqlite3 data/ops_center.db ".dump audit_logs" > audit_logs_backup.sql

# Backup log files
tar -czf audit_logs_backup.tar.gz /var/log/ops-center/
```

## Troubleshooting

### Database Permission Errors

```bash
# Fix database permissions
chmod 666 data/ops_center.db
chmod 777 data/
```

### Log Directory Not Writable

```bash
# Create directory and set permissions
sudo mkdir -p /var/log/ops-center
sudo chown $USER:$USER /var/log/ops-center
sudo chmod 700 /var/log/ops-center
```

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- [ ] Log shipping to external SIEM systems
- [ ] Real-time alerting via webhooks
- [ ] Advanced anomaly detection
- [ ] Log encryption at rest
- [ ] Multi-tenant isolation
- [ ] Elasticsearch integration
- [ ] Grafana dashboards
- [ ] Compliance report generation

## Support

For issues or questions:
- GitHub: https://github.com/Unicorn-Commander/UC-1-Pro/issues
- Documentation: /home/deploy/Production/UC-1-Pro/services/ops-center/backend/docs/
