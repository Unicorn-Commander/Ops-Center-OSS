# Security Integration - Quick Reference

## Environment Variables (Add to .env)

```bash
# Security Feature Toggles
CSRF_ENABLED=true
RATE_LIMIT_ENABLED=true
AUDIT_ENABLED=true
PASSWORD_POLICY_ENABLED=true

# CSRF Configuration
CSRF_SECRET_KEY=<run: openssl rand -hex 32>

# Rate Limiting Configuration  
RATE_LIMIT_AUTH=5/minute
RATE_LIMIT_ADMIN=100/minute
RATE_LIMIT_READ=200/minute
RATE_LIMIT_WRITE=50/minute
RATE_LIMIT_ADMIN_BYPASS=true
RATE_LIMIT_FAIL_OPEN=true
REDIS_URL=redis://unicorn-lago-redis:6379/0

# Audit Configuration
AUDIT_FAIL_OPEN=true
```

## Quick Test Commands

### Test CSRF Protection
```bash
# Get CSRF token
curl -b "session_token=$SESSION" http://localhost:8084/api/v1/auth/csrf-token

# Use in request
curl -X POST -H "X-CSRF-Token: $TOKEN" -b "session_token=$SESSION" \
  http://localhost:8084/api/v1/services/test/action
```

### Test Rate Limiting
```bash
# Trigger rate limit (6+ rapid requests)
for i in {1..10}; do curl -X POST http://localhost:8084/api/v1/auth/login \
  -d '{"username":"test","password":"test"}'; done
```

### View Audit Logs
```bash
# Recent logs
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8084/api/v1/audit/recent

# Statistics
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8084/api/v1/audit/stats

# Check database
sqlite3 /home/muut/Production/UC-1-Pro/services/ops-center/data/ops_center.db \
  "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 5;"
```

### Password Policy
```bash
# Get requirements
curl http://localhost:8084/api/v1/auth/password-policy
```

## Integrated Endpoints

### Authentication (Rate Limited + Audited)
- `POST /api/v1/auth/login` - 5 req/min
- `POST /auth/direct-login` - 5 req/min
- `GET /auth/callback` - OAuth callback (audited)
- `GET /auth/logout` - Logout (audited)
- `POST /api/v1/auth/change-password` - Password change (audited + validated)

### Service Management (Rate Limited + Audited)
- `POST /api/v1/services/{name}/action` - 100 req/min (admin)

### Audit Logs (Admin Only)
- `GET /api/v1/audit/logs` - Query logs
- `GET /api/v1/audit/stats` - Statistics
- `GET /api/v1/audit/recent` - Recent events
- `GET /api/v1/audit/security` - Security events
- `DELETE /api/v1/audit/cleanup` - Cleanup old logs

## Deployment Checklist

- [ ] Install dependencies: `pip install redis aiofiles pydantic`
- [ ] Set environment variables in .env
- [ ] Ensure Redis is running
- [ ] Create log directory: `mkdir -p /var/log/ops-center`
- [ ] Generate CSRF secret: `openssl rand -hex 32`
- [ ] Restart service: `docker restart unicorn-ops-center`
- [ ] Verify logs: `docker logs unicorn-ops-center | grep -E "CSRF|Rate|Audit"`
- [ ] Test CSRF protection
- [ ] Test rate limiting
- [ ] Verify audit logs writing
- [ ] Test password policy

## Monitoring Commands

```bash
# Check startup logs
docker logs unicorn-ops-center | grep -E "CSRF|Rate|Audit|Password"

# Monitor audit logs in real-time
tail -f /var/log/ops-center/audit.log

# Check Redis rate limit keys
redis-cli -u redis://unicorn-lago-redis:6379/0 KEYS "ratelimit:*"

# Weekly security report
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8084/api/v1/audit/stats" > security_report_$(date +%Y%m%d).json
```

## Files Created/Modified

**New Files:**
- `role_mapper.py` (8.0K)
- `csrf_protection.py` (11K)
- `rate_limiter.py` (18K)
- `audit_logger.py` (19K)
- `audit_endpoints.py` (11K)
- `audit_helpers.py` (13K)
- `password_policy.py` (8.8K)
- `SECURITY_INTEGRATION_COMPLETE.md` (comprehensive docs)
- `SECURITY_QUICK_REFERENCE.md` (this file)

**Modified Files:**
- `server.py` (main integration point)

## Support

Full documentation: `SECURITY_INTEGRATION_COMPLETE.md`  
API docs: http://localhost:8084/docs
