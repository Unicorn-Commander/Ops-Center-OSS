# Security Fixes Required - Credential Management System

**Project**: UC-Cloud Ops-Center
**Date**: October 23, 2025
**Priority**: HIGH
**Estimated Time**: 4 hours

---

## Executive Summary

Security audit completed with **B+ (87/100)** rating. System is **APPROVED WITH CONDITIONS** for production deployment.

**Required Before Production**:
1. ✅ Add rate limiting to test endpoint (CRITICAL)
2. ⚠️ Sanitize metadata fields (RECOMMENDED)
3. ⚠️ Generic error messages (RECOMMENDED)

---

## Fix #1: Add Rate Limiting (CRITICAL)

**Priority**: 🔴 CRITICAL - MUST FIX BEFORE PRODUCTION
**Estimated Time**: 1 hour
**Risk**: High - External API abuse, service degradation

### Issue

The `/api/v1/credentials/{service}/test` endpoint has no rate limiting, allowing attackers to:
- Spam Cloudflare/GitHub/Stripe APIs (10,000+ requests)
- Get IP address blacklisted
- Cause service degradation

### Solution

**Step 1**: Install slowapi dependency

```bash
cd /opt/ops-center/backend
pip install slowapi
```

**Step 2**: Update `credential_api.py`

```python
# Add at top of file (after line 29)
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize limiter (after line 55)
limiter = Limiter(key_func=get_remote_address)

# Update test endpoint (line 380)
@router.post("/{service}/test", response_model=TestResultResponse)
@limiter.limit("5/minute")  # ← ADD THIS LINE
async def test_credential(
    service: str,
    request_body: TestCredentialRequest,
    request: Request,
    admin: dict = Depends(require_admin)
):
    """Test credential by calling service API..."""
    # Rest of function unchanged
```

**Step 3**: Add limiter to FastAPI app

```python
# In server.py (main FastAPI app)
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# After creating app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Step 4**: Test rate limiting

```bash
# Test with curl
for i in {1..10}; do
  curl -X POST http://localhost:8084/api/v1/credentials/cloudflare/test \
    -H "Content-Type: application/json" \
    -d '{"value": "test_token"}' &
done
wait

# Expected: 429 Too Many Requests after 5 requests
```

### Verification

```bash
# Check if slowapi is installed
pip show slowapi

# Check if rate limiting works
curl -I http://localhost:8084/api/v1/credentials/cloudflare/test
# Should see: X-RateLimit-Limit: 5
# Should see: X-RateLimit-Remaining: 4
```

---

## Fix #2: Sanitize Metadata Fields (RECOMMENDED)

**Priority**: 🟡 MEDIUM - FIX WITHIN 2 WEEKS
**Estimated Time**: 2 hours
**Risk**: Medium - XSS attack via stored metadata

### Issue

The `metadata.description` field is not sanitized, allowing XSS payloads:

```javascript
// Attacker enters:
description: "<script>alert(document.cookie)</script>"

// Stored in database and rendered in UI without sanitization
// Could steal admin session tokens
```

### Solution

**Step 1**: Install bleach dependency

```bash
cd /opt/ops-center/backend
pip install bleach
```

**Step 2**: Update `credential_api.py` request models

```python
# Add at top of file
from bleach import clean

# Update CreateCredentialRequest (line 60)
class CreateCredentialRequest(BaseModel):
    service: str = Field(...)
    credential_type: str = Field(...)
    value: str = Field(...)
    metadata: Optional[Dict[str, Any]] = Field(None)

    @validator('metadata')
    def sanitize_metadata(cls, v):
        """Sanitize metadata to prevent XSS attacks"""
        if v:
            # Sanitize description field
            if 'description' in v:
                v['description'] = clean(
                    v['description'],
                    tags=[],  # No HTML tags allowed
                    strip=True  # Strip all HTML
                )
            # Sanitize other string fields
            for key, val in v.items():
                if isinstance(val, str):
                    v[key] = clean(val, tags=[], strip=True)
        return v

# Update UpdateCredentialRequest (line 92)
class UpdateCredentialRequest(BaseModel):
    value: str = Field(...)
    metadata: Optional[Dict[str, Any]] = Field(None)

    @validator('metadata')
    def sanitize_metadata(cls, v):
        """Sanitize metadata to prevent XSS attacks"""
        if v:
            for key, val in v.items():
                if isinstance(val, str):
                    v[key] = clean(val, tags=[], strip=True)
        return v
```

**Step 3**: Test XSS prevention

```bash
# Try to inject XSS payload
curl -X POST http://localhost:8084/api/v1/credentials \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{
    "service": "cloudflare",
    "credential_type": "api_token",
    "value": "cf_test_123",
    "metadata": {
      "description": "<script>alert(\"XSS\")</script>Production token"
    }
  }'

# Expected response:
# {
#   "metadata": {
#     "description": "Production token"  # Script tags stripped
#   }
# }
```

### Verification

```bash
# Check if bleach is installed
pip show bleach

# Check if sanitization works
# (Use test case above)
```

---

## Fix #3: Generic Error Messages (RECOMMENDED)

**Priority**: 🟢 LOW - FIX WITHIN 3 WEEKS
**Estimated Time**: 1 hour
**Risk**: Low - Information disclosure via stack traces

### Issue

Error messages return exception details to frontend:

```python
raise HTTPException(status_code=500, detail=f"Failed to create credential: {str(e)}")
```

This could leak:
- Database schema information
- File paths
- Internal service names

### Solution

**Update all exception handlers in `credential_api.py`**

```python
# Line 196 - create_credential
except UnsupportedServiceError as e:
    raise HTTPException(status_code=400, detail=str(e))  # Keep detailed
except CredentialValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))  # Keep detailed
except Exception as e:
    logger.error(f"Failed to create credential: {e}", exc_info=True)  # Log full details
    raise HTTPException(status_code=500, detail="Failed to create credential")  # Generic

# Line 227 - list_credentials
except Exception as e:
    logger.error(f"Failed to list credentials: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Failed to list credentials")

# Line 274 - get_credential
except HTTPException:
    raise  # Keep HTTP exceptions as-is
except Exception as e:
    logger.error(f"Failed to get credential: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Failed to get credential")

# Line 325 - update_credential
except UnsupportedServiceError as e:
    raise HTTPException(status_code=400, detail=str(e))
except CredentialValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Failed to update credential: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Failed to update credential")

# Line 376 - delete_credential
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Failed to delete credential: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Failed to delete credential")

# Line 440 - test_credential
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Failed to test credential: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Failed to test credential")

# Line 497 - list_supported_services
except Exception as e:
    logger.error(f"Failed to list services: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Failed to list services")
```

### Verification

```bash
# Cause an error and check response
curl -X POST http://localhost:8084/api/v1/credentials \
  -H "Content-Type: application/json" \
  -d '{"service": "invalid"}'

# Expected: Generic error message, NOT stack trace
# {
#   "detail": "Failed to create credential"  # Generic
# }

# Check logs for full details
docker logs ops-center-direct | grep "Failed to create credential"
# Should see full exception with stack trace
```

---

## Fix #4: User ID Validation (ENHANCEMENT)

**Priority**: 🟢 LOW - NICE TO HAVE
**Estimated Time**: 15 minutes
**Risk**: Very Low - Minor data consistency issue

### Issue

User ID extraction uses dual fallback which may cause inconsistency:

```python
user_id = admin.get("user_id") or admin.get("email")
```

### Solution

**Update all endpoints in `credential_api.py`**

Replace:
```python
user_id = admin.get("user_id") or admin.get("email")
```

With:
```python
user_id = admin.get("user_id")
if not user_id:
    raise HTTPException(status_code=401, detail="User ID not found in session")
```

**Locations to update**:
- Line 180 (create_credential)
- Line 221 (list_credentials)
- Line 257 (get_credential)
- Line 309 (update_credential)
- Line 357 (delete_credential)
- Line 414 (test_credential)
- Line 477 (list_supported_services)

### Verification

```bash
# Test with valid session
curl -X GET http://localhost:8084/api/v1/credentials \
  -H "Cookie: session=valid_session"

# Expected: Success (200 OK)

# Test with session missing user_id
# (Manual test via modified session)
```

---

## Fix #5: Add Security Warning UX (ENHANCEMENT)

**Priority**: 🟢 LOW - NICE TO HAVE
**Estimated Time**: 30 minutes
**Risk**: Very Low - UX improvement for security awareness

### Issue

When users click "show password" toggle, no warning is displayed about security risk.

### Solution

**Update `CloudflareSettings.jsx`**

```javascript
// After the TextField (around line 340)
<TextField
  fullWidth
  label="API Token"
  type={showToken ? 'text' : 'password'}
  value={apiToken}
  onChange={(e) => setApiToken(e.target.value)}
  placeholder="cf_..."
  sx={{ mb: 2 }}
  InputProps={{
    endAdornment: (
      <InputAdornment position="end">
        <IconButton onClick={handleToggleVisibility} edge="end">
          {showToken ? (
            <EyeSlashIcon className="h-5 w-5" />
          ) : (
            <EyeIcon className="h-5 w-5" />
          )}
        </IconButton>
      </InputAdornment>
    )
  }}
  helperText="Create at: Cloudflare Dashboard → My Profile → API Tokens → Create Token"
/>

{/* ADD THIS ALERT */}
{showToken && (
  <Alert severity="warning" sx={{ mb: 2 }}>
    ⚠️ Your credential is now visible. It will automatically hide in 30 seconds.
  </Alert>
)}
```

**Update `NameCheapSettings.jsx`** (same pattern around line 428)

### Verification

```bash
# Rebuild frontend
cd /opt/ops-center
npm run build
cp -r dist/* public/

# Restart service
docker restart ops-center-direct

# Test in browser
# 1. Go to Settings → Credentials → Cloudflare
# 2. Click "eye" icon to show password
# 3. Should see warning alert appear
# 4. Wait 30 seconds, should auto-hide
```

---

## Deployment Checklist

**Before deploying fixes to production**:

- [ ] Install dependencies (`slowapi`, `bleach`)
- [ ] Update backend code (`credential_api.py`)
- [ ] Update frontend code (CloudflareSettings.jsx, NameCheapSettings.jsx)
- [ ] Run unit tests
- [ ] Run penetration tests
- [ ] Update `requirements.txt`
- [ ] Rebuild Docker container
- [ ] Deploy to staging
- [ ] Test all credential operations
- [ ] Monitor logs for errors
- [ ] Deploy to production
- [ ] Verify rate limiting works
- [ ] Verify XSS prevention works
- [ ] Update security documentation

---

## Testing Commands

```bash
# 1. Test rate limiting
for i in {1..10}; do
  curl -X POST http://localhost:8084/api/v1/credentials/cloudflare/test \
    -H "Content-Type: application/json" \
    -d '{"value": "test"}' &
done
wait
# Expected: 429 Too Many Requests after 5 requests

# 2. Test XSS prevention
curl -X POST http://localhost:8084/api/v1/credentials \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{
    "service": "cloudflare",
    "credential_type": "api_token",
    "value": "cf_test_123",
    "metadata": {"description": "<script>alert(1)</script>Test"}
  }'
# Expected: description = "Test" (script stripped)

# 3. Test error messages
curl -X POST http://localhost:8084/api/v1/credentials \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'
# Expected: Generic error message, NOT stack trace

# 4. Test authentication
curl -X GET http://localhost:8084/api/v1/credentials
# Expected: 401 Unauthorized

# 5. Test credential masking
curl -X GET http://localhost:8084/api/v1/credentials \
  -H "Cookie: session=..."
# Expected: All credentials show "masked_value", NOT plaintext
```

---

## Dependencies to Add

**Backend** (`requirements.txt`):
```
slowapi>=0.1.9
bleach>=6.1.0
```

**Installation**:
```bash
cd /opt/ops-center/backend
pip install slowapi bleach
pip freeze > requirements.txt
```

---

## Estimated Timeline

| Fix | Priority | Time | Status |
|-----|----------|------|--------|
| Rate Limiting | CRITICAL | 1 hour | ⏳ Pending |
| XSS Sanitization | MEDIUM | 2 hours | ⏳ Pending |
| Error Messages | LOW | 1 hour | ⏳ Pending |
| User ID Validation | ENHANCEMENT | 15 min | ⏳ Pending |
| Security Warning UX | ENHANCEMENT | 30 min | ⏳ Pending |

**Total Time**: 4 hours 45 minutes

**Recommended Order**:
1. Rate Limiting (CRITICAL - do first)
2. XSS Sanitization (MEDIUM - do second)
3. Error Messages (LOW - do third)
4. Enhancements (optional - do if time permits)

---

## Post-Fix Verification

After implementing all fixes:

1. ✅ Run security audit script
2. ✅ Run penetration tests (7 test cases)
3. ✅ Review audit logs
4. ✅ Test all credential operations
5. ✅ Monitor for errors in production
6. ✅ Update security documentation

**Final Security Score Expected**: A- (92/100)

---

## Contact

**Questions?** Contact Security Team
**Issues?** Open ticket in issue tracker
**Review?** Schedule follow-up audit after fixes

---

*This document is for internal use only. Do not share publicly.*
