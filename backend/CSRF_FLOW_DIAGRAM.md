# CSRF Protection Flow Diagram

## Overview
This document visualizes how CSRF protection works in the UC-1 Pro Ops Center.

## Authentication & Token Generation Flow

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ 1. POST /api/v1/auth/login
       │    (username, password)
       ▼
┌─────────────────────────────────────────┐
│         FastAPI Server                  │
│  ┌───────────────────────────────────┐  │
│  │  CSRF Middleware (exempt login)   │  │
│  └───────────────┬───────────────────┘  │
│                  ▼                       │
│  ┌───────────────────────────────────┐  │
│  │  Authentication Handler           │  │
│  │  - Validate credentials           │  │
│  │  - Create session                 │  │
│  │  - Generate session_token         │  │
│  └───────────────┬───────────────────┘  │
│                  │                       │
│                  ▼                       │
│         sessions[token] = {             │
│           "user": {...}                 │
│         }                               │
└─────────────────┬───────────────────────┘
                  │
                  │ 2. Response
                  │    Set-Cookie: session_token=abc123
                  ▼
            ┌─────────────┐
            │   Browser   │
            │  (Cookies)  │
            └──────┬──────┘
                   │
                   │ 3. GET /api/data
                   │    Cookie: session_token=abc123
                   ▼
┌─────────────────────────────────────────┐
│         FastAPI Server                  │
│  ┌───────────────────────────────────┐  │
│  │  CSRF Middleware                  │  │
│  │  - Method: GET (safe, skip)       │  │
│  │  - Check session exists           │  │
│  │  - Generate CSRF token if needed  │  │
│  └───────────────┬───────────────────┘  │
│                  │                       │
│         sessions[token] = {             │
│           "user": {...},                │
│           "csrf_token": "xyz789" ←──┐   │
│         }                           │   │
│                  │                  │   │
│                  ▼                  │   │
│  ┌───────────────────────────────┐ │   │
│  │  Route Handler                │ │   │
│  │  - Process request            │ │   │
│  │  - Return data                │ │   │
│  └───────────────┬───────────────┘ │   │
└──────────────────┼───────────────────┘   │
                   │                       │
                   │ 4. Response           │
                   │    Set-Cookie: csrf_token=xyz789
                   ▼                       │
            ┌─────────────┐                │
            │   Browser   │                │
            │  (Cookies)  │◄───────────────┘
            └─────────────┘
```

## Protected Request Flow (POST/PUT/DELETE/PATCH)

```
┌─────────────────────────┐
│   Browser/Frontend      │
│  - session_token cookie │
│  - csrf_token cookie    │
└───────────┬─────────────┘
            │
            │ 1. POST /api/v1/landing/config
            │    Headers:
            │      X-CSRF-Token: xyz789
            │    Cookies:
            │      session_token=abc123
            │      csrf_token=xyz789
            ▼
┌─────────────────────────────────────────────────────────┐
│                   CSRF Middleware                       │
│                                                         │
│  1. Check method → POST (protected)                     │
│                                                         │
│  2. Check if exempt → No                                │
│                                                         │
│  3. Extract tokens:                                     │
│     - request_token = Header["X-CSRF-Token"]            │
│     - cookie_token = Cookie["csrf_token"]               │
│     - session_token = Cookie["session_token"]           │
│                                                         │
│  4. Get expected token from session:                    │
│     session = sessions[session_token]                   │
│     expected_token = session["csrf_token"]              │
│                                                         │
│  5. Validate (constant-time comparison):                │
│     ┌──────────────────────────────────────┐            │
│     │  if request_token == expected_token: │            │
│     │      ✓ VALID                         │            │
│     │  elif cookie_token == expected_token:│            │
│     │      ✓ VALID (double-submit)         │            │
│     │  else:                               │            │
│     │      ✗ INVALID → 403 Forbidden       │            │
│     └──────────────────────────────────────┘            │
│                                                         │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ Token Valid ✓
                        ▼
            ┌───────────────────────┐
            │   Route Handler       │
            │  - Process request    │
            │  - Update config      │
            │  - Return response    │
            └───────────┬───────────┘
                        │
                        │ Response: 200 OK
                        ▼
                ┌───────────────┐
                │   Browser     │
                └───────────────┘
```

## CSRF Validation Failure Flow

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ POST /api/v1/data
       │ Headers: (no X-CSRF-Token)
       │ Cookies: session_token=abc123
       ▼
┌─────────────────────────────────────────┐
│         CSRF Middleware                 │
│                                         │
│  1. Check method → POST (protected)     │
│                                         │
│  2. Extract tokens:                     │
│     - request_token = None              │
│     - cookie_token = None               │
│     - session_token = "abc123"          │
│                                         │
│  3. Get expected token:                 │
│     expected_token = "xyz789"           │
│                                         │
│  4. Validate:                           │
│     None != "xyz789" → INVALID ✗        │
│                                         │
│  5. Log warning:                        │
│     "CSRF validation failed for         │
│      POST /api/v1/data"                 │
│                                         │
│  6. Return 403 Forbidden                │
│     {                                   │
│       "detail": "CSRF validation        │
│                  failed. Invalid or     │
│                  missing CSRF token."   │
│     }                                   │
└─────────────┬───────────────────────────┘
              │
              │ Response: 403 Forbidden
              ▼
        ┌─────────────┐
        │   Browser   │
        │             │
        │ Error       │
        │ Handler:    │
        │  - Refresh  │
        │    token    │
        │  - Retry    │
        └─────────────┘
```

## Token Lifecycle

```
Session Creation
      │
      ▼
┌─────────────────┐
│ User Login      │
│ session_token   │
│ created         │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ First GET Request After Login   │
│ - CSRF token generated          │
│ - Stored in sessions[token]     │
│ - Set in cookie                 │
└────────┬────────────────────────┘
         │
         │ ┌──────────────────────────┐
         │ │ Token valid for:         │
         │ │ - Current session only   │
         │ │ - 24 hours (cookie max)  │
         │ └──────────────────────────┘
         ▼
┌─────────────────────────────────┐
│ Protected Requests              │
│ - Token validated each request  │
│ - Same token used for session   │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Session End     │
│ - Logout        │
│ - Timeout       │
│ - Token deleted │
└─────────────────┘
```

## Security Layers

```
┌─────────────────────────────────────────────────────┐
│                  CSRF Protection                    │
│  ┌───────────────────────────────────────────────┐  │
│  │        Double-Submit Cookie Pattern           │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │    Session Integration                  │  │  │
│  │  │  ┌───────────────────────────────────┐  │  │  │
│  │  │  │   Constant-Time Comparison        │  │  │  │
│  │  │  │  ┌─────────────────────────────┐  │  │  │  │
│  │  │  │  │  Cryptographic Random      │  │  │  │  │
│  │  │  │  │  (secrets.token_urlsafe)   │  │  │  │  │
│  │  │  │  └─────────────────────────────┘  │  │  │  │
│  │  │  └───────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
             │                    │
             ▼                    ▼
    ┌────────────────┐   ┌────────────────┐
    │ SameSite=Lax   │   │ HTTPS Secure   │
    │ Cookie         │   │ (Production)   │
    └────────────────┘   └────────────────┘
```

## Request Flow Matrix

```
┌──────────┬─────────────┬──────────────┬─────────────┬───────────┐
│  Method  │   Endpoint  │ CSRF Token   │  Exempt?    │  Result   │
├──────────┼─────────────┼──────────────┼─────────────┼───────────┤
│  GET     │ /api/data   │ Not Required │ No          │ ✓ Pass    │
│  POST    │ /auth/login │ Not Required │ Yes (Auth)  │ ✓ Pass    │
│  POST    │ /api/data   │ Valid Token  │ No          │ ✓ Pass    │
│  POST    │ /api/data   │ No Token     │ No          │ ✗ 403     │
│  POST    │ /api/data   │ Invalid Token│ No          │ ✗ 403     │
│  PUT     │ /api/data   │ Valid Token  │ No          │ ✓ Pass    │
│  DELETE  │ /api/data   │ Valid Token  │ No          │ ✓ Pass    │
│  PATCH   │ /api/data   │ Valid Token  │ No          │ ✓ Pass    │
└──────────┴─────────────┴──────────────┴─────────────┴───────────┘
```

## Frontend Integration Points

```
┌───────────────────────────────────────────────────────────┐
│                    React Application                      │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              CsrfProvider (Context)                 │  │
│  │  - Fetches token on mount                           │  │
│  │  - Provides to all child components                 │  │
│  └────────────────────┬────────────────────────────────┘  │
│                       │                                   │
│         ┌─────────────┼─────────────┐                     │
│         │             │             │                     │
│         ▼             ▼             ▼                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │Component │  │Component │  │Component │                │
│  │    A     │  │    B     │  │    C     │                │
│  │          │  │          │  │          │                │
│  │useCsrf() │  │useCsrf() │  │useCsrf() │                │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                │
│       │             │             │                       │
│       └─────────────┼─────────────┘                       │
│                     │                                     │
│                     ▼                                     │
│            Include in fetch()                             │
│            headers: {                                     │
│              'X-CSRF-Token': csrfToken                    │
│            }                                              │
└───────────────────────────────────────────────────────────┘
```

## Token Validation Algorithm

```python
def validate_csrf(request):
    """
    CSRF validation pseudocode
    """
    # Step 1: Check if method requires CSRF
    if request.method in ['GET', 'HEAD', 'OPTIONS']:
        return True  # Safe methods, skip validation

    # Step 2: Check if endpoint is exempt
    if request.path in exempt_urls:
        return True  # Exempt, skip validation

    # Step 3: Extract tokens
    request_token = request.headers.get('X-CSRF-Token')
    cookie_token = request.cookies.get('csrf_token')
    session_token = request.cookies.get('session_token')

    # Step 4: Get expected token from session
    if not session_token or session_token not in sessions:
        return False  # No session

    expected_token = sessions[session_token].get('csrf_token')

    # Step 5: Validate (constant-time comparison)
    if secrets.compare_digest(request_token or '', expected_token or ''):
        return True  # Valid via header

    if secrets.compare_digest(cookie_token or '', expected_token or ''):
        return True  # Valid via cookie (double-submit)

    # Step 6: Validation failed
    log_warning("CSRF validation failed", request.path, request.method)
    return False
```

## Configuration Decision Tree

```
                    Start
                      │
                      ▼
              Is this production?
                   /   \
                  /     \
             Yes /       \ No
                /         \
               ▼           ▼
        CSRF_ENABLED=true  Development mode
        COOKIE_SECURE=true      │
        HTTPS required          ▼
               │          Testing CSRF?
               │             /   \
               │        Yes /     \ No
               │           /       \
               │          ▼         ▼
               │    CSRF_ENABLED    CSRF_ENABLED
               │    =true           =false
               │    COOKIE_SECURE   (faster dev)
               │    =false
               │
               ▼
        All requests include
        X-CSRF-Token header
```

## Deployment Checklist Flow

```
┌────────────────────┐
│ Phase 1: Prepare   │
│ - Deploy backend   │
│ - CSRF disabled    │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Phase 2: Frontend  │
│ - Update React app │
│ - Add CSRF tokens  │
│ - Test locally     │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Phase 3: Testing   │
│ - Enable CSRF      │
│ - Test all flows   │
│ - Monitor logs     │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Phase 4: Deploy    │
│ - Frontend to prod │
│ - Enable CSRF      │
│ - Monitor alerts   │
└────────────────────┘
```

---
*Last Updated: October 9, 2025*
