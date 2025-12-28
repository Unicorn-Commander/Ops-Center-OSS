# CSRF Protection Implementation for UC-1 Pro Ops Center

## Overview

This implementation adds Cross-Site Request Forgery (CSRF) protection to the UC-1 Pro Ops Center backend API using a double-submit cookie pattern with session integration.

## Architecture

### Components

1. **csrf_protection.py** - Core CSRF protection module
   - `CSRFProtection` class: Token generation and validation
   - `CSRFMiddleware` class: FastAPI middleware for request validation
   - Helper functions for integration

2. **server.py** - Integrated CSRF middleware into FastAPI application
   - Added CSRF middleware after CORS and GZip
   - Added `/api/v1/auth/csrf-token` endpoint
   - Configured exempt URLs for OAuth flow

### Protection Strategy

**Double-Submit Cookie Pattern with Session Integration:**

1. CSRF token generated during session creation
2. Token stored in session dictionary (server-side)
3. Token sent to client via cookie (readable by JavaScript)
4. Client includes token in `X-CSRF-Token` header for state-changing requests
5. Middleware validates: header token matches session token

### Protected Methods

- POST
- PUT
- DELETE
- PATCH

### Safe Methods (No CSRF Validation)

- GET
- HEAD
- OPTIONS
- TRACE

### Exempt Endpoints

The following endpoints are exempt from CSRF validation:

- `/auth/callback` - OAuth callback
- `/auth/login` - Login endpoint
- `/auth/logout` - Logout endpoint
- `/docs` - API documentation
- `/redoc` - ReDoc documentation
- `/openapi.json` - OpenAPI schema
- `/api/v1/auth/login` - API login
- `/api/v1/auth/logout` - API logout

## Configuration

### Environment Variables

```bash
# Enable/disable CSRF protection (default: true)
CSRF_ENABLED=true

# Secret key for CSRF token generation (auto-generated if not set)
CSRF_SECRET_KEY=your-secret-key-here

# Protocol determines cookie security (https -> secure cookies)
EXTERNAL_PROTOCOL=https
```

### Configuration Options

All configuration is done via the `create_csrf_protection()` function:

```python
csrf_protect, csrf_middleware = create_csrf_protection(
    enabled=True,              # Enable/disable CSRF
    secret_key="secret",       # Secret for token generation
    exempt_urls={...},         # URLs exempt from validation
    sessions_store=sessions,   # Reference to sessions dict
    cookie_secure=True         # Secure flag for HTTPS
)
```

## Frontend Integration

### 1. Obtain CSRF Token

After authentication, the frontend can obtain the CSRF token:

**Method 1: From Cookie (Automatic)**
```javascript
// Token is automatically set in 'csrf_token' cookie
// Can be read by JavaScript (httponly=false)
function getCsrfTokenFromCookie() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrf_token') {
            return value;
        }
    }
    return null;
}
```

**Method 2: From API Endpoint**
```javascript
async function getCsrfToken() {
    const response = await fetch('/api/v1/auth/csrf-token', {
        credentials: 'include'  // Include session cookie
    });
    const data = await response.json();
    return data.csrf_token;
}
```

### 2. Include Token in Requests

**For all POST, PUT, DELETE, PATCH requests:**

```javascript
const csrfToken = getCsrfTokenFromCookie(); // or from API

// Using fetch
fetch('/api/v1/some-endpoint', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
    },
    credentials: 'include',  // Include cookies
    body: JSON.stringify(data)
});

// Using axios
axios.post('/api/v1/some-endpoint', data, {
    headers: {
        'X-CSRF-Token': csrfToken
    },
    withCredentials: true
});
```

### 3. React Integration Example

```javascript
import React, { createContext, useContext, useEffect, useState } from 'react';

const CsrfContext = createContext(null);

export function CsrfProvider({ children }) {
    const [csrfToken, setCsrfToken] = useState(null);

    useEffect(() => {
        // Fetch CSRF token on mount
        fetch('/api/v1/auth/csrf-token', { credentials: 'include' })
            .then(res => res.json())
            .then(data => setCsrfToken(data.csrf_token))
            .catch(err => console.error('Failed to fetch CSRF token:', err));
    }, []);

    return (
        <CsrfContext.Provider value={csrfToken}>
            {children}
        </CsrfContext.Provider>
    );
}

export function useCsrf() {
    return useContext(CsrfContext);
}

// Usage in component
function MyComponent() {
    const csrfToken = useCsrf();

    const handleSubmit = async (data) => {
        await fetch('/api/v1/landing/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            credentials: 'include',
            body: JSON.stringify(data)
        });
    };

    return <form onSubmit={handleSubmit}>...</form>;
}
```

### 4. Axios Interceptor (Global Setup)

```javascript
import axios from 'axios';

// Add CSRF token to all requests
axios.interceptors.request.use(config => {
    // Get token from cookie
    const csrfToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_token='))
        ?.split('=')[1];

    if (csrfToken && ['post', 'put', 'delete', 'patch'].includes(config.method)) {
        config.headers['X-CSRF-Token'] = csrfToken;
    }

    return config;
}, error => {
    return Promise.reject(error);
});

// Enable credentials for all requests
axios.defaults.withCredentials = true;
```

## Security Features

### Token Generation
- Cryptographically secure random tokens (32 bytes)
- URL-safe base64 encoding
- Unique token per session

### Token Validation
- Constant-time comparison to prevent timing attacks
- Double validation: header AND cookie must match session token
- Tokens tied to user sessions

### Cookie Security
- SameSite=Lax protection
- Secure flag for HTTPS (auto-detected)
- Not HttpOnly (frontend needs to read it)
- 24-hour expiration

### Session Integration
- Tokens stored server-side in session
- Token regenerated on session creation
- Tokens invalidated on logout

## Error Handling

### CSRF Validation Failure

When CSRF validation fails, the API returns:

```json
{
    "detail": "CSRF validation failed. Invalid or missing CSRF token."
}
```

HTTP Status: `403 Forbidden`

### Frontend Error Handling

```javascript
try {
    const response = await fetch('/api/v1/some-endpoint', {
        method: 'POST',
        headers: {
            'X-CSRF-Token': csrfToken
        },
        credentials: 'include',
        body: JSON.stringify(data)
    });

    if (response.status === 403) {
        // CSRF validation failed - refresh token
        const tokenResponse = await fetch('/api/v1/auth/csrf-token', {
            credentials: 'include'
        });
        const newToken = await tokenResponse.json();
        // Retry request with new token
        // ...
    }
} catch (error) {
    console.error('Request failed:', error);
}
```

## Logging

The middleware logs CSRF-related events:

```python
# Info level
logger.info("Generated new CSRF token for session: abc12345...")
logger.info("CSRF Protection: Enabled")

# Debug level
logger.debug("CSRF check skipped for exempt URL: /auth/callback")
logger.debug("CSRF validation passed (header) for /api/v1/landing/config")
logger.debug("CSRF validation passed (cookie) for /api/v1/models/download")

# Warning level
logger.warning(
    "CSRF validation failed for POST /api/v1/services/start - "
    "Request token: missing, Cookie token: present, Session token: present"
)
```

## Testing

### Manual Testing

```bash
# 1. Login to get session
curl -X POST http://localhost:8084/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"password"}' \
    -c cookies.txt

# 2. Get CSRF token
curl http://localhost:8084/api/v1/auth/csrf-token \
    -b cookies.txt

# 3. Make protected request WITH CSRF token
curl -X POST http://localhost:8084/api/v1/landing/config \
    -H "Content-Type: application/json" \
    -H "X-CSRF-Token: YOUR_TOKEN_HERE" \
    -b cookies.txt \
    -d '{"title":"Test"}'

# 4. Make protected request WITHOUT CSRF token (should fail)
curl -X POST http://localhost:8084/api/v1/landing/config \
    -H "Content-Type: application/json" \
    -b cookies.txt \
    -d '{"title":"Test"}'
```

### Automated Testing

See `test_csrf.py` for automated test suite.

## Migration Guide

### For Existing Clients

1. **No changes required for GET requests** - They continue to work as before

2. **For POST/PUT/DELETE/PATCH requests:**
   - Add CSRF token to request headers
   - Token available in `csrf_token` cookie after login
   - Or fetch from `/api/v1/auth/csrf-token` endpoint

3. **Error handling:**
   - Handle 403 responses by refreshing CSRF token
   - Implement automatic retry with new token

### Gradual Rollout

To disable CSRF protection during testing/migration:

```bash
# In .env or environment
CSRF_ENABLED=false
```

Or modify `server.py`:

```python
# Temporarily disable CSRF
CSRF_ENABLED = False
```

## Troubleshooting

### Common Issues

**Issue: 403 Forbidden on all POST requests**
- Check that CSRF token is included in `X-CSRF-Token` header
- Verify cookies are being sent (`credentials: 'include'`)
- Check browser console for CORS errors

**Issue: Token not found in cookie**
- Ensure user is authenticated (has session)
- Check cookie domain and path settings
- Verify browser accepts third-party cookies

**Issue: CORS errors**
- CORS middleware allows `X-CSRF-Token` header
- Ensure `credentials: 'include'` in fetch requests
- Check `allow_credentials=True` in CORS config

**Issue: Token validation fails after login**
- Token is generated on first GET request after login
- Make a GET request before POST to initialize token
- Or call `/api/v1/auth/csrf-token` explicitly

### Debug Mode

Enable debug logging:

```python
# In server.py
logging.basicConfig(level=logging.DEBUG)
```

This will log all CSRF validation attempts.

## Performance Impact

- **Minimal overhead**: Token validation is O(1)
- **No database queries**: Tokens stored in memory (sessions dict)
- **Constant-time comparison**: No timing attack surface
- **Cookie overhead**: ~50 bytes per request

## Security Considerations

### What CSRF Protects Against

- Cross-site request forgery attacks
- Clickjacking combined with state-changing requests
- Malicious third-party sites making authenticated requests

### What CSRF Does NOT Protect Against

- XSS attacks (sanitize user input separately)
- SQL injection (use parameterized queries)
- Authentication bypass (use proper session management)
- Man-in-the-middle attacks (use HTTPS)

### Best Practices

1. Always use HTTPS in production (`EXTERNAL_PROTOCOL=https`)
2. Keep CSRF secret key secure and unique per deployment
3. Regenerate tokens on privilege escalation
4. Implement rate limiting on authentication endpoints
5. Use SameSite cookies for additional protection
6. Monitor CSRF validation failures for potential attacks

## References

- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Double Submit Cookie Pattern](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html#double-submit-cookie)

## Changelog

### Version 1.0.0 (2025-10-09)
- Initial CSRF protection implementation
- Double-submit cookie pattern with session integration
- FastAPI middleware integration
- Frontend API for token retrieval
- Comprehensive documentation
