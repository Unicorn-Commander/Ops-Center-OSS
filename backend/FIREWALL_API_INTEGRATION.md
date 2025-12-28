# Firewall API Integration Guide

**Quick integration steps for ops-center backend**

---

## Prerequisites

✅ **firewall_manager.py** created by Backend Developer Agent
✅ **firewall_api.py** created (667 lines)
✅ **rate_limiter.py** exists (17KB)
✅ **admin_subscriptions_api.py** exists (authentication)

---

## Integration Steps

### Step 1: Verify Dependencies

Check that firewall_manager.py exists and exports the required classes:

```python
# Required exports from firewall_manager.py
from firewall_manager import (
    FirewallManager,       # Main manager class
    FirewallRuleCreate,    # Pydantic model for rule creation
    FirewallError,         # Exception class
    FirewallRule,          # Pydantic model for rule data
    FirewallStatus         # Pydantic model for status data
)
```

If firewall_manager.py doesn't exist yet, wait for Backend Developer Agent to create it.

---

### Step 2: Register Router in Main App

Edit `/home/muut/Production/UC-Cloud/services/ops-center/backend/server_auth_integrated.py`:

```python
# Add at top of file with other imports
from firewall_api import router as firewall_router

# Add after existing router registrations (search for "include_router")
app.include_router(firewall_router)
```

**Example**:
```python
# Existing routers
app.include_router(user_management_router)
app.include_router(billing_router)
app.include_router(org_router)

# Add firewall router
app.include_router(firewall_router)
```

---

### Step 3: Verify Redis Configuration

Ensure Redis environment variables are set in `.env.auth`:

```bash
REDIS_HOST=unicorn-redis
REDIS_PORT=6379
REDIS_RATELIMIT_DB=1
```

Test Redis connectivity:
```bash
docker exec ops-center-direct python3 -c "
import redis
r = redis.Redis(host='unicorn-redis', port=6379, db=1)
print('Redis ping:', r.ping())
"
```

---

### Step 4: Restart Backend

```bash
# Restart ops-center container
docker restart ops-center-direct

# Watch logs for errors
docker logs ops-center-direct -f
```

**Expected Output**:
```
INFO: Rate limiter connected to Redis at unicorn-redis:6379
INFO: Application startup complete
INFO: Uvicorn running on http://0.0.0.0:8084
```

---

### Step 5: Verify Endpoints

Check that endpoints are registered:

```bash
# Option 1: Visit Swagger docs
# https://your-domain.com/docs

# Option 2: List endpoints via API
curl http://localhost:8084/openapi.json | jq '.paths | keys[] | select(contains("firewall"))'
```

**Expected Endpoints**:
```
/api/v1/network/firewall/rules
/api/v1/network/firewall/rules/{rule_num}
/api/v1/network/firewall/rules/bulk-delete
/api/v1/network/firewall/status
/api/v1/network/firewall/enable
/api/v1/network/firewall/disable
/api/v1/network/firewall/reset
/api/v1/network/firewall/templates
/api/v1/network/firewall/templates/{template_name}
/api/v1/network/firewall/logs
/api/v1/network/firewall/health
```

---

### Step 6: Test Health Check

```bash
# Health check (no auth required)
curl http://localhost:8084/api/v1/network/firewall/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "ufw_available": true,
  "timestamp": "2025-10-22T20:00:00"
}
```

If `ufw_available: false`, UFW is not installed on host system.

---

### Step 7: Test Authenticated Endpoint

```bash
# Get firewall status (requires authentication)
curl http://localhost:8084/api/v1/network/firewall/status \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

**Expected Response** (authenticated):
```json
{
  "enabled": true,
  "status": "active",
  "default_policy": {
    "incoming": "deny",
    "outgoing": "allow",
    "routed": "deny"
  },
  "total_rules": 15,
  "active_rules": 12,
  "ipv6_enabled": true,
  "logging": "on"
}
```

**Expected Error** (not authenticated):
```json
HTTP 403 Forbidden
{
  "detail": "Admin access required"
}
```

---

## Troubleshooting

### Issue: "Module 'firewall_manager' not found"

**Cause**: firewall_manager.py doesn't exist yet or has import errors

**Solution**:
1. Wait for Backend Developer Agent to create firewall_manager.py
2. Verify file exists: `ls backend/firewall_manager.py`
3. Check for syntax errors: `python3 -m py_compile backend/firewall_manager.py`

---

### Issue: "Rate limiter Redis unavailable"

**Cause**: Redis container not running or wrong configuration

**Solution**:
```bash
# Check Redis container
docker ps | grep redis

# Test Redis connection
docker exec unicorn-redis redis-cli ping

# Check environment variables
docker exec ops-center-direct env | grep REDIS
```

---

### Issue: "Admin access required" even for admin users

**Cause**: Session not properly configured or user doesn't have admin role

**Solution**:
1. Verify user has admin role in Keycloak
2. Check session data:
   ```python
   # In endpoint, add logging:
   logger.info(f"User session: {request.session.get('user', {})}")
   ```
3. Ensure `require_admin()` dependency is working

---

### Issue: "UFW is not installed"

**Cause**: UFW not installed on host system

**Solution**:
```bash
# Install UFW on host (not in container)
sudo apt-get update
sudo apt-get install -y ufw

# Verify installation
which ufw
ufw version
```

---

### Issue: Rate limit always returns 429

**Cause**: Rate limit key not expiring in Redis

**Solution**:
```bash
# Check Redis keys
docker exec unicorn-redis redis-cli KEYS "ratelimit:*"

# Delete all rate limit keys (testing only!)
docker exec unicorn-redis redis-cli FLUSHDB

# Or delete specific key
docker exec unicorn-redis redis-cli DEL "ratelimit:list_firewall_rules:admin"
```

---

## Testing Checklist

### Manual Testing

- [ ] Health check returns status
- [ ] List rules requires authentication
- [ ] Add rule creates new firewall rule
- [ ] Delete rule removes firewall rule
- [ ] Bulk delete removes multiple rules
- [ ] Get status returns current firewall state
- [ ] Enable/disable toggles firewall
- [ ] Reset clears all rules
- [ ] Apply template adds predefined rules
- [ ] List templates shows available templates
- [ ] Get logs returns firewall logs
- [ ] Rate limiting triggers after limit exceeded
- [ ] SSH protection prevents SSH rule deletion
- [ ] Audit logging records all actions

---

### Automated Testing

Create `test_firewall_api.py`:

```python
import pytest
from fastapi.testclient import TestClient

# Import after firewall_api is integrated
from server_auth_integrated import app

client = TestClient(app)

def test_health_check():
    """Health check should not require authentication"""
    response = client.get("/api/v1/network/firewall/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_list_rules_requires_auth():
    """List rules should require authentication"""
    response = client.get("/api/v1/network/firewall/rules")
    assert response.status_code in [401, 403]

# Add more tests for authenticated endpoints
# (requires mock authentication)
```

Run tests:
```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend
pytest test_firewall_api.py -v
```

---

## Frontend Integration (Next Phase)

Once backend is working, Frontend Developer Agent will create:

- `FirewallManagement.jsx` - Main firewall page
- `FirewallRuleForm.jsx` - Add/edit rule modal
- `FirewallStatusCard.jsx` - Status display
- `FirewallTemplateSelector.jsx` - Template selection

**Route**: `/admin/network/firewall`

---

## Documentation References

- **API Documentation**: `FIREWALL_API_README.md`
- **Architecture Spec**: `/docs/epic1.2_architecture_spec.md`
- **Rate Limiter**: `rate_limiter.py`
- **Authentication**: `admin_subscriptions_api.py`
- **Network Manager**: `network_manager.py`

---

## Support

**Created**: October 22, 2025
**Author**: API Developer Agent
**Epic**: 1.2 Phase 1 - Network Configuration Enhancement

**Next Steps**: Wait for Backend Developer Agent to complete firewall_manager.py

---
