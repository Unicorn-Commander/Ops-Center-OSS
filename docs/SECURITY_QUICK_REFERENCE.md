# Security Quick Reference Guide

**Last Updated**: November 12, 2025
**Team**: Security Hardening Team

---

## Quick Links

- **Security Test Script**: `/tests/security_test_billing.py`
- **Security Report**: `/tests/SECURITY_REPORT_BILLING.md`
- **Fix Summary**: `/tests/SECURITY_FIXES_SUMMARY.md`

---

## Running Security Tests

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center

# Run billing security tests
python3 tests/security_test_billing.py

# Expected output: 21/23 tests passing (91%)
# Critical issues: 0
# High issues: 1 (negative credits bug)
# Medium issues: 1 (rate limiting detection)
```

---

## Authentication Best Practices

### ✅ CORRECT: Use Auth Dependencies

```python
from auth_dependencies import require_authenticated_user, require_admin_user

@router.post("/endpoint")
async def my_endpoint(
    request: Request,
    user: Dict = Depends(require_authenticated_user),  # ← Auth FIRST
    data: MyRequestModel = None  # ← Validation SECOND
):
    # User is already authenticated here
    logger.info(f"User {user['email']} accessing endpoint")
```

### ❌ WRONG: Manual Auth After Validation

```python
@router.post("/endpoint")
async def my_endpoint(
    data: MyRequestModel,  # ← Validation FIRST (INSECURE!)
    request: Request
):
    user = await get_current_user(request)  # ← Auth SECOND (TOO LATE!)
```

**Why wrong?** FastAPI/Pydantic validates request body BEFORE reaching your code. If validation fails, it returns 422 with field names, leaking API structure to unauthenticated users.

---

## Rate Limiting

### Adding Rate Limits to Endpoints

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/endpoint")
@limiter.limit("100/minute")  # ← GET: 100 requests/minute
async def get_endpoint(request: Request):
    pass

@router.post("/endpoint")
@limiter.limit("20/minute")  # ← POST: 20 requests/minute
async def post_endpoint(request: Request):
    pass
```

### Rate Limit Guidelines

| Operation Type | Rate Limit | Use Case |
|----------------|------------|----------|
| GET (read) | 100/minute | Dashboards, list queries |
| POST (write) | 20/minute | Create, update operations |
| Admin endpoints | 500/minute | System admin operations |
| Public endpoints | 10/minute | Unauthenticated access |

---

## Request ID Tracking

### Using Request IDs in Logs

```python
from request_id_middleware import get_request_id

@router.get("/endpoint")
async def my_endpoint(request: Request):
    request_id = get_request_id(request)
    logger.info(f"[{request_id}] Processing endpoint")

    # Request ID automatically added to response headers as X-Request-ID
```

### Finding Request ID in Logs

```bash
# View logs with request IDs
docker logs ops-center-direct | grep "\[a1b2c3d4-"

# Example output:
# INFO [a1b2c3d4-e5f6-7890] POST /api/v1/org-billing/subscriptions from 192.168.1.100 - Request started
# INFO [a1b2c3d4-e5f6-7890] POST /api/v1/org-billing/subscriptions completed with status 201 in 45.23ms
```

---

## CORS Configuration

### Current Allowed Origins

```python
allowed_origins = [
    "https://your-domain.com",
    "https://api.your-domain.com",
    "https://auth.your-domain.com",
    "http://localhost:8084",
    "http://localhost:3000",
    "http://localhost:5173",  # Vite dev server
]
```

### Adding New Origins

**Method 1: Environment Variable** (Recommended)
```bash
# In .env.auth file
ADDITIONAL_CORS_ORIGINS=https://new-domain.com,https://another-domain.com
```

**Method 2: Code** (For permanent changes)
```python
# In server.py
allowed_origins = [
    "https://your-domain.com",
    "https://new-domain.com",  # ← Add here
]
```

---

## Common Security Issues & Fixes

### Issue 1: 422 Error Before Authentication

**Symptom**: Unauthenticated POST requests return 422 instead of 401

**Cause**: Request body validated before auth check

**Fix**: Use `Depends(require_authenticated_user)` BEFORE body parameter
```python
@router.post("/endpoint")
async def endpoint(
    request: Request,
    user: Dict = Depends(require_authenticated_user),  # ← First
    data: MyModel = None  # ← Second
):
```

### Issue 2: CORS Errors in Browser

**Symptom**: "Access to fetch blocked by CORS policy"

**Cause**: Origin not in allowed list

**Fix**: Add origin to CORS whitelist or use environment variable

### Issue 3: No Rate Limiting

**Symptom**: Can make unlimited requests

**Cause**: Missing `@limiter.limit()` decorator

**Fix**: Add rate limit decorator above endpoint
```python
@router.post("/endpoint")
@limiter.limit("20/minute")  # ← Add this
async def endpoint(request: Request):
```

### Issue 4: Can't Trace User Actions

**Symptom**: Multiple requests from same user can't be correlated

**Cause**: No request ID logging

**Fix**: Use `get_request_id(request)` in logs
```python
request_id = get_request_id(request)
logger.info(f"[{request_id}] User action: {action}")
```

---

## Security Checklist for New Endpoints

When adding a new API endpoint, verify:

- [ ] **Authentication**: Uses `Depends(require_authenticated_user)` FIRST
- [ ] **Authorization**: Checks user roles/permissions
- [ ] **Rate Limiting**: Has `@limiter.limit()` decorator
- [ ] **Input Validation**: Pydantic models validate all inputs
- [ ] **SQL Injection**: Uses parameterized queries (asyncpg $1, $2)
- [ ] **XSS Protection**: Returns JSON (FastAPI handles escaping)
- [ ] **Error Handling**: Doesn't expose sensitive data in errors
- [ ] **Logging**: Uses request IDs for audit trail
- [ ] **CORS**: Origin is whitelisted if needed from browser

---

## Emergency Contact

**Security Issues**: Report immediately to Security Team Lead
**Test Failures**: Run `/tests/security_test_billing.py` to reproduce
**Production Incidents**: Check logs with request ID for audit trail

---

## Additional Resources

- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **slowapi Docs**: https://github.com/laurentS/slowapi
- **OWASP Top 10**: https://owasp.org/Top10/
- **Asyncpg Security**: https://magicstack.github.io/asyncpg/current/usage.html#prepared-statements

---

*Keep this guide updated as security policies evolve*
