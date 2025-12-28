# CSRF Protection - Quick Reference Card

## For Backend Developers

### Configuration (Environment Variables)
```bash
CSRF_ENABLED=true                    # Default: true
CSRF_SECRET_KEY=your-secret-key      # Auto-generated if not set
EXTERNAL_PROTOCOL=https              # Determines cookie security
```

### Exempt an Endpoint
```python
# In server.py, add to exempt_urls set:
csrf_protect, csrf_middleware = create_csrf_protection(
    exempt_urls={
        "/auth/callback",
        "/your/new/endpoint"  # Add here
    }
)
```

### Check Logs
```bash
# Verify CSRF is enabled
grep "CSRF Protection" /var/log/app.log

# Monitor failures
tail -f /var/log/app.log | grep "CSRF validation failed"
```

## For Frontend Developers

### Quick Start (3 Steps)

**1. Get CSRF Token from Cookie**
```javascript
const csrfToken = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrf_token='))
    ?.split('=')[1];
```

**2. Include in Request Headers**
```javascript
fetch('/api/v1/endpoint', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken  // Add this
    },
    credentials: 'include',  // Required
    body: JSON.stringify(data)
});
```

**3. Handle Errors**
```javascript
if (response.status === 403) {
    // CSRF validation failed - refresh token
    const res = await fetch('/api/v1/auth/csrf-token', {
        credentials: 'include'
    });
    const { csrf_token } = await res.json();
    // Retry with new token
}
```

### Axios Setup (Global)
```javascript
import axios from 'axios';

// Enable credentials
axios.defaults.withCredentials = true;

// Add interceptor
axios.interceptors.request.use(config => {
    if (['post', 'put', 'delete', 'patch'].includes(config.method)) {
        const token = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrf_token='))
            ?.split('=')[1];
        config.headers['X-CSRF-Token'] = token;
    }
    return config;
});
```

### React Hook (Recommended)
```javascript
// Use the CsrfProvider from frontend_csrf_guide.js
import { CsrfProvider, useCsrf } from './csrf-utils';

// Wrap your app
<CsrfProvider>
    <App />
</CsrfProvider>

// In components
const { csrfToken } = useCsrf();
```

## HTTP Methods Reference

| Method | CSRF Required? | Safe Method? |
|--------|---------------|--------------|
| GET | ❌ No | ✅ Yes |
| HEAD | ❌ No | ✅ Yes |
| OPTIONS | ❌ No | ✅ Yes |
| POST | ✅ Yes | ❌ No |
| PUT | ✅ Yes | ❌ No |
| DELETE | ✅ Yes | ❌ No |
| PATCH | ✅ Yes | ❌ No |

## Exempt Endpoints (No CSRF Required)

- `/auth/callback`
- `/auth/login`
- `/auth/logout`
- `/docs`
- `/redoc`
- `/openapi.json`
- `/api/v1/auth/login`
- `/api/v1/auth/logout`

## Common Errors

### 403 Forbidden
```json
{
    "detail": "CSRF validation failed. Invalid or missing CSRF token."
}
```
**Solution**: Add `X-CSRF-Token` header to request

### 401 Unauthorized (from token endpoint)
```json
{
    "detail": "No active session. Please login first."
}
```
**Solution**: Login first, then get CSRF token

## Testing Commands

```bash
# Login
curl -X POST http://localhost:8084/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"pass"}' \
    -c cookies.txt

# Get CSRF token
curl http://localhost:8084/api/v1/auth/csrf-token -b cookies.txt

# Test with token
curl -X POST http://localhost:8084/api/v1/endpoint \
    -H "X-CSRF-Token: YOUR_TOKEN" \
    -b cookies.txt

# Test without token (should fail)
curl -X POST http://localhost:8084/api/v1/endpoint -b cookies.txt
```

## Temporary Disable (Testing Only)

```bash
# In environment
export CSRF_ENABLED=false

# Or in server.py
CSRF_ENABLED = False
```

## Browser Console Test

```javascript
// Run this in browser console to test CSRF
async function testCSRF() {
    // Test without token (should fail)
    try {
        await fetch('/api/v1/landing/config', {
            method: 'POST',
            credentials: 'include',
            body: '{}'
        });
    } catch (e) {
        console.log('Without token: FAILED ✓');
    }

    // Test with token (should succeed)
    const token = document.cookie
        .split('; ')
        .find(r => r.startsWith('csrf_token='))
        ?.split('=')[1];

    const res = await fetch('/api/v1/landing/config', {
        method: 'POST',
        headers: { 'X-CSRF-Token': token },
        credentials: 'include',
        body: '{}'
    });
    console.log('With token:', res.status === 200 ? 'PASSED ✓' : 'FAILED ✗');
}

testCSRF();
```

## Key Files

| File | Purpose |
|------|---------|
| `csrf_protection.py` | Core implementation |
| `server.py` | Integration point |
| `CSRF_IMPLEMENTATION.md` | Full documentation |
| `frontend_csrf_guide.js` | React examples |
| `test_csrf.py` | Test suite |

## Need Help?

1. Check `CSRF_IMPLEMENTATION.md` for detailed docs
2. See `frontend_csrf_guide.js` for integration examples
3. Run `python test_csrf.py --manual` for tests
4. Search logs: `grep CSRF /var/log/app.log`

---
**Remember**: Always include `credentials: 'include'` in fetch requests!
