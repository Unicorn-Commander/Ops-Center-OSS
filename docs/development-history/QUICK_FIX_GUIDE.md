# Ops-Center Backend - Quick Fix Guide

**Generated**: 2025-10-28
**Priority**: HIGH - Fix before production deployment

---

## 🚨 Critical Bugs (Fix Immediately)

### Bug #1: Billing Plans Returns 404

**Endpoint**: `GET /api/v1/billing/plans`

**Quick Test**:
```bash
# Test endpoint
curl http://localhost:8084/api/v1/billing/plans

# Verify Lago connection
docker exec ops-center-direct curl http://unicorn-lago-api:3000/health

# Check environment variables
docker exec ops-center-direct printenv | grep LAGO
```

**Likely Fix**:
```python
# File: backend/billing_api.py
# Check if Lago API URL is correct
# Verify graphql query is properly formatted
```

---

### Bug #2: LLM Models Wrong Format

**Endpoint**: `GET /api/v1/llm/models`

**Quick Test**:
```bash
curl http://localhost:8084/api/v1/llm/models
# Should return: {"object": "list", "data": [...]}
# Actually returns: [...]
```

**Quick Fix**:
```python
# File: backend/litellm_api.py

@router.get("/models")
async def list_models():
    models = await get_available_models()

    # FIX: Wrap in OpenAI format
    return {
        "object": "list",
        "data": models
    }
```

---

### Bug #3: Organization Creation 500 Error

**Endpoint**: `POST /api/v1/organizations`

**Quick Test**:
```bash
# Check logs
docker logs ops-center-direct --tail 100 | grep -i organization

# Test database
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d organizations"

# Try manual insert
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "INSERT INTO organizations (id, name, owner_id, created_at) VALUES (gen_random_uuid(), 'Test Org', 'user-id-here', NOW());"
```

**Likely Issues**:
- Missing `owner_id` field
- Database constraint violation
- Foreign key constraint on users table

**Quick Fix**:
```python
# File: backend/org_api.py

@router.post("/organizations")
async def create_organization(org: OrganizationCreate, user=Depends(get_current_user)):
    # Make sure owner_id is set
    org_data = org.dict()
    org_data["owner_id"] = user.id  # Add this line

    # Rest of creation logic...
```

---

### Bug #4: 2FA Endpoints 500 Error

**Endpoints**:
- `POST /api/v1/admin/2fa/users/{id}/enforce`
- `POST /api/v1/admin/2fa/users/{id}/reset`

**Quick Test**:
```bash
# Check if file exists
ls -l backend/two_factor_api.py

# Check logs
docker logs ops-center-direct --tail 50 | grep -i "2fa\|two.*factor"
```

**Likely Issue**: Keycloak API integration not complete

**Quick Fix Options**:
1. **Short-term**: Return 501 Not Implemented instead of 500
2. **Long-term**: Implement Keycloak Admin API calls

```python
# File: backend/two_factor_api.py

@router.post("/admin/2fa/users/{user_id}/enforce")
async def enforce_2fa(user_id: str):
    # TEMP FIX: Return not implemented
    raise HTTPException(status_code=501, detail="2FA enforcement not yet implemented")

    # TODO: Call Keycloak API
    # POST /admin/realms/uchub/users/{user_id}/execute-actions-email
    # Body: ["CONFIGURE_TOTP"]
```

---

### Bug #5: Subscription Tier CRUD 500 Error

**Endpoints**:
- `POST /api/v1/admin/tiers`
- `PUT /api/v1/admin/tiers/{id}`

**Quick Test**:
```bash
# Test creation
curl -X POST http://localhost:8084/api/v1/admin/tiers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Test Tier",
    "price": 9.99,
    "api_limit": 1000
  }'

# Check database schema
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d subscription_tiers"

# Check logs
docker logs ops-center-direct --tail 50 | grep -i tier
```

**Likely Issues**:
- Missing required fields in request body
- Database column mismatch
- Validation error

**Quick Fix**:
```python
# File: backend/subscription_tiers_api.py

# Check Pydantic model
class SubscriptionTierCreate(BaseModel):
    name: str
    price: float
    api_limit: int
    # Add any missing fields that database requires
    features: List[str] = []  # Make optional with default
    description: Optional[str] = None
```

---

## ⚠️ Configuration Issues (Non-blocking)

### Monitoring Endpoints Not Configured

**Quick Fix**: Make these return 503 instead of crashing

```python
# Files: backend/grafana_api.py, backend/prometheus_api.py, backend/umami_api.py

@router.get("/monitoring/grafana/dashboards")
async def get_dashboards():
    if not os.environ.get("GRAFANA_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Grafana not configured. Set GRAFANA_API_KEY environment variable."
        )
    # Rest of logic...
```

---

### System Status Requires Auth

**Quick Fix**: Make public endpoint

```python
# File: backend/server.py

@app.get("/api/v1/system/status")
# REMOVE: dependencies=[Depends(get_current_user)]
async def system_status():
    # This should be public for health checks
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
```

---

## 🔧 Testing Commands

### Run All Tests
```bash
cd /opt/ops-center

# Automated test suite
python3 tests/test_all_endpoints.py

# With authentication (set token first)
export AUTH_TOKEN="your_jwt_token"
python3 tests/test_detailed_authenticated.py
```

### Check Service Health
```bash
# Ops-Center
curl http://localhost:8084/api/v1/deployment/config

# Lago API
docker exec ops-center-direct curl http://unicorn-lago-api:3000/health

# PostgreSQL
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT 1;"

# Redis
docker exec unicorn-redis redis-cli PING
```

### View Logs
```bash
# All logs
docker logs ops-center-direct

# Last 100 lines
docker logs ops-center-direct --tail 100

# Follow logs (real-time)
docker logs ops-center-direct -f

# Search for errors
docker logs ops-center-direct | grep -i "error\|exception\|500"
```

### Restart Service
```bash
# Quick restart
docker restart ops-center-direct

# Full rebuild
cd /opt/uc-cloud
docker compose -f services/ops-center/docker-compose.direct.yml build
docker compose -f services/ops-center/docker-compose.direct.yml up -d
```

---

## 📊 Priority Matrix

| Bug | Impact | Effort | Priority | Fix Order |
|-----|--------|--------|----------|-----------|
| Bug #1 (Billing) | HIGH | Low | 🔴 CRITICAL | 1st |
| Bug #3 (Orgs) | HIGH | Medium | 🔴 CRITICAL | 2nd |
| Bug #5 (Tiers) | HIGH | Medium | 🔴 CRITICAL | 3rd |
| Bug #2 (LLM) | MEDIUM | Low | 🟡 HIGH | 4th |
| Bug #4 (2FA) | MEDIUM | High | 🟢 MEDIUM | 5th |

**Estimated Total Fix Time**: 1-2 days for critical bugs (Bugs #1, #3, #5)

---

## 🚀 Deployment Checklist

Before deploying to production:

- [ ] Fix Bug #1 (Billing plans)
- [ ] Fix Bug #3 (Organization creation)
- [ ] Fix Bug #5 (Subscription tier CRUD)
- [ ] Fix Bug #2 (LLM models format)
- [ ] Make /system/status public
- [ ] Add proper error messages (no generic 500s)
- [ ] Test with real authentication token
- [ ] Verify database state after operations
- [ ] Run integration tests
- [ ] Load test (50+ concurrent users)
- [ ] Security audit (basic SQL injection tests)
- [ ] Update API documentation

---

## 📞 Support

**Main Report**: `/opt/ops-center/TEST_REPORT_BACKEND.md`

**Test Scripts**:
- `/opt/ops-center/tests/test_all_endpoints.py`
- `/opt/ops-center/tests/test_detailed_authenticated.py`

**Working Directory**: `/opt/ops-center`

---

**Last Updated**: 2025-10-28
**Version**: 1.0
**Status**: ACTIVE BUGS - NEEDS FIXES
