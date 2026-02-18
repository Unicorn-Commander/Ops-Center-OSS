# Security Review: Role-Based Access Control (RBAC) System
## UC-1 Pro Ops-Center

**Review Date:** October 9, 2025
**Reviewer:** Claude Code Security Review Agent
**Files Reviewed:**
- `/home/deploy/Production/UC-1-Pro/services/ops-center/src/components/Layout.jsx`
- `/home/deploy/Production/UC-1-Pro/services/ops-center/src/App.jsx`
- `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/server.py`
- `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/auth_manager.py`
- `/home/deploy/Production/UC-1-Pro/services/ops-center/frontend/src/contexts/AuthContext.js`

---

## Executive Summary

The Ops-Center application implements a **CRITICAL SECURITY VULNERABILITY**: the role-based access control system exists in the backend but is **NOT enforced on most API endpoints**. While user management endpoints properly use `require_admin` dependency injection, the majority of administrative operations (services, models, network, storage, etc.) are completely unprotected.

### Severity Assessment
- **CRITICAL Issues:** 5
- **HIGH Issues:** 4
- **MEDIUM Issues:** 3
- **LOW Issues:** 2

### Overall RBAC Status: VULNERABLE

---

## Critical Security Findings

### 1. CRITICAL: Unauthenticated Access to Administrative Operations

**Issue:** Most API endpoints lack authentication and authorization checks.

**Affected Endpoints (50+ endpoints):**
```python
# Services Management - NO AUTH
/api/v1/services                          # GET, POST
/api/v1/services/{container_name}/action  # POST (start/stop/restart)
/api/v1/services/{container_name}/logs    # GET
/api/v1/services/{container_name}/stats   # GET

# AI Model Management - NO AUTH
/api/v1/models/search                     # GET
/api/v1/models/download                   # POST
/api/v1/models/{model_id}/config          # PUT
/api/v1/models/active                     # POST
/api/v1/vllm/switch-model                 # POST

# Network Configuration - NO AUTH
/api/v1/network/status                    # GET
/api/v1/network/wifi/connect              # POST
/api/v1/network/configure                 # POST

# Storage & Backup - NO AUTH
/api/v1/storage                           # GET
/api/v1/backup/create                     # POST
/api/v1/backup/{backup_id}/restore        # POST

# Landing Page Configuration - NO AUTH
/api/v1/landing/config                    # GET, POST
/api/v1/landing/theme/{preset}            # POST
/api/v1/landing/service/{service_id}      # POST

# Extensions - NO AUTH
/api/v1/extensions                        # GET, POST
/api/v1/extensions/{id}/start             # POST
/api/v1/extensions/{id}/stop              # POST

# Logs - NO AUTH
/api/v1/logs/search                       # POST
/api/v1/logs/export                       # POST

# System Updates - NO AUTH
/api/v1/updates/check                     # POST
/api/v1/updates/apply                     # POST
```

**Impact:**
- ANY unauthenticated user can start/stop critical services
- ANY unauthenticated user can download/activate AI models
- ANY unauthenticated user can modify network configuration
- ANY unauthenticated user can create/restore backups
- ANY unauthenticated user can install/remove extensions
- ANY unauthenticated user can apply system updates

**Risk Level:** CRITICAL (10/10)

**Evidence:**
```python
# File: backend/server.py, line 1317
@app.post("/api/v1/services/{container_name}/action")
async def service_action(container_name: str, action: ServiceAction):
    # NO authentication check!
    # NO authorization check!
    if action.action == "start":
        docker_manager.start_service(container_name)
```

---

### 2. CRITICAL: No Role Hierarchy Implementation

**Issue:** The system defines three roles (`admin`, `user`, `viewer`) but only implements binary admin checking.

**Current Implementation:**
```python
# File: backend/server.py, line 2402
async def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

**Missing:**
- No `require_power_user` function
- No role hierarchy (admin > power_user > regular_user > viewer)
- No granular permissions system
- No feature-level access control

**Impact:**
- Cannot implement tiered access (e.g., power users managing models but not services)
- All-or-nothing access model (admin vs non-admin)
- No support for role-based feature flags

**Risk Level:** CRITICAL (9/10)

---

### 3. CRITICAL: Frontend-Only Navigation Filtering

**Issue:** Navigation menu does NOT filter based on user role.

**Current Implementation:**
```javascript
// File: src/components/Layout.jsx, line 25-38
const navigation = [
  { name: 'Dashboard', href: '/admin/', icon: HomeIcon },
  { name: 'Models & AI', href: '/admin/models', icon: CubeIcon },
  { name: 'Services', href: '/admin/services', icon: ServerIcon },
  // ... ALL ITEMS SHOWN TO ALL USERS
];

// Line 107: No filtering
{navigation.map((item) => {
  // All items rendered without role check
  return <Link key={item.name} to={item.href}>
})}
```

**Expected Implementation:**
```javascript
const navigation = [
  { name: 'Dashboard', href: '/admin/', icon: HomeIcon, roles: ['admin', 'power_user', 'user'] },
  { name: 'Models & AI', href: '/admin/models', icon: CubeIcon, roles: ['admin', 'power_user'] },
  { name: 'Services', href: '/admin/services', icon: ServerIcon, roles: ['admin'] },
  // ...
].filter(item => item.roles.includes(userInfo.role));
```

**Impact:**
- Users see menu items they cannot access
- Security through obscurity (not actual security)
- Poor UX for non-admin users

**Risk Level:** CRITICAL (8/10)

---

### 4. HIGH: Session Management Vulnerabilities

**Issue:** Multiple session management implementations with inconsistent security.

**Dual Session Systems:**
1. **JWT-based sessions** (auth_manager.py) - Properly implemented with expiration
2. **Cookie-based sessions** (server.py, line 66) - In-memory dictionary, lost on restart

```python
# File: server.py, line 66
sessions = {}  # In-memory, not persistent!

# File: server.py, line 2831
session_token = secrets.token_urlsafe(32)
sessions[session_token] = {
    "user": user_info,
    "created_at": datetime.now().isoformat()
}
# NO expiration check!
# NO session invalidation!
# NO maximum session limit!
```

**Vulnerabilities:**
- Sessions persist indefinitely (no TTL)
- No concurrent session limits
- Sessions lost on server restart
- Two different authentication flows (JWT vs cookie)

**Risk Level:** HIGH (7/10)

---

### 5. HIGH: Missing CSRF Protection

**Issue:** State-changing operations lack CSRF token validation.

**Vulnerable Operations:**
```python
# All POST/PUT/DELETE operations accept requests without CSRF tokens
@app.post("/api/v1/services/{container_name}/action")
@app.post("/api/v1/models/download")
@app.post("/api/v1/network/configure")
@app.delete("/api/v1/models/{model_id}")
```

**Attack Scenario:**
```html
<!-- Malicious website -->
<form action="https://unicorncommander.ai/api/v1/services/unicorn-postgres/action" method="POST">
  <input type="hidden" name="action" value="stop">
</form>
<script>document.forms[0].submit();</script>
```

**Impact:**
- Authenticated users can be tricked into performing actions
- Cross-site request forgery attacks possible
- Service disruption through social engineering

**Risk Level:** HIGH (7/10)

---

### 6. HIGH: Insufficient Authorization Granularity

**Issue:** No permission system beyond role checking.

**Missing Capabilities:**
- Resource-based permissions (user can only manage their own API keys)
- Action-based permissions (read-only access to logs)
- Feature flags (beta features for specific users)
- Time-based access (temporary elevated privileges)

**Example Vulnerability:**
```python
# File: server.py, line 2537
@app.delete("/api/v1/api-keys/{key_id}")
async def delete_api_key(key_id: str, current_user: dict = Depends(get_current_user)):
    # Good: Checks user ownership
    success = auth_manager.delete_api_key(key_id, current_user["user_id"])

# But most endpoints don't have this!
@app.post("/api/v1/services/{container_name}/action")  # NO OWNERSHIP CHECK!
async def service_action(container_name: str, action: ServiceAction):
```

**Risk Level:** HIGH (6/10)

---

### 7. MEDIUM: Password Policy Weaknesses

**Issue:** Minimal password requirements.

**Current Policy:**
```python
# File: backend/auth_manager.py, line 60-63
@validator('new_password')
def password_strength(cls, v):
    assert len(v) >= 8, 'Password must be at least 8 characters'
    return v
```

**Missing:**
- No complexity requirements (uppercase, lowercase, numbers, symbols)
- No password history (prevent reuse)
- No password expiration
- No breach detection (HaveIBeenPwned integration)

**Risk Level:** MEDIUM (5/10)

---

### 8. MEDIUM: Insecure Default Credentials

**Issue:** Default admin password is weak and publicly visible.

```python
# File: backend/auth_manager.py, line 192
admin_password = os.getenv("ADMIN_PASSWORD", "MagicUnicorn!8-)")
```

**Problems:**
- Default password in source code
- Weak entropy (dictionary word + symbol)
- No forced password change on first login
- Password visible in GitHub repository

**Risk Level:** MEDIUM (5/10)

---

### 9. MEDIUM: No Rate Limiting

**Issue:** Authentication endpoints lack brute-force protection.

**Vulnerable Endpoints:**
```python
@app.post("/api/v1/auth/login")  # NO rate limiting
@app.post("/auth/direct-login")  # NO rate limiting
@app.get("/auth/callback")       # NO rate limiting
```

**Attack Scenario:**
```bash
# Attacker can attempt unlimited logins
for i in {1..10000}; do
  curl -X POST https://unicorncommander.ai/api/v1/auth/login \
    -d '{"username":"admin","password":"attempt'$i'"}'
done
```

**Risk Level:** MEDIUM (5/10)

---

### 10. LOW: Information Disclosure in Error Messages

**Issue:** Detailed error messages expose system internals.

**Example:**
```python
# File: server.py, line 2421
except ValueError as e:
    raise HTTPException(status_code=401, detail=str(e))
    # Returns: "Invalid username or password"
    # Should return: Generic "Authentication failed"
```

**Risk Level:** LOW (3/10)

---

### 11. LOW: Missing Security Headers

**Issue:** No security-related HTTP headers configured.

**Missing Headers:**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`
- `Strict-Transport-Security`
- `Referrer-Policy`

**Risk Level:** LOW (3/10)

---

## Role Hierarchy Implementation Status

### Defined Roles (auth_manager.py)
```python
role: str = "user"  # admin, user, viewer
```

### Current Implementation: INCOMPLETE

| Role | Should Have Access To | Currently Has Access To |
|------|----------------------|------------------------|
| **admin** | Everything | User management only (other endpoints unprotected) |
| **power_user** | Models, extensions, logs | NOT IMPLEMENTED |
| **user** | Dashboard, own settings | NOT IMPLEMENTED |
| **viewer** | Read-only access | NOT IMPLEMENTED |

---

## Protected vs Unprotected Endpoints Analysis

### Properly Protected Endpoints (14 endpoints)
```python
# User Management (admin only)
GET    /api/v1/users                    ✓ require_admin
POST   /api/v1/users                    ✓ require_admin
GET    /api/v1/users/{user_id}          ✓ require_admin
PUT    /api/v1/users/{user_id}          ✓ require_admin
DELETE /api/v1/users/{user_id}          ✓ require_admin

# SSO Management (admin only)
GET    /api/v1/sso/users                ✓ require_admin
POST   /api/v1/sso/users                ✓ require_admin
PUT    /api/v1/sso/users/{user_id}      ✓ require_admin
DELETE /api/v1/sso/users/{user_id}      ✓ require_admin
POST   /api/v1/sso/users/{id}/set-password  ✓ require_admin
GET    /api/v1/sso/groups               ✓ require_admin
POST   /api/v1/sso/groups               ✓ require_admin
POST   /api/v1/sso/users/{uid}/groups/{gid}  ✓ require_admin

# User-scoped endpoints (authenticated)
GET    /api/v1/auth/me                  ✓ get_current_user
POST   /api/v1/auth/logout              ✓ get_current_user
POST   /api/v1/auth/change-password     ✓ get_current_user
GET    /api/v1/api-keys                 ✓ get_current_user
POST   /api/v1/api-keys                 ✓ get_current_user
DELETE /api/v1/api-keys/{key_id}        ✓ get_current_user
GET    /api/v1/sessions                 ✓ get_current_user
DELETE /api/v1/sessions/{session_id}    ✓ get_current_user
```

### Unprotected Endpoints (54+ endpoints)
```python
# System Management
GET    /api/v1/system/status            ✗ NO AUTH
GET    /api/v1/system/hardware          ✗ NO AUTH
GET    /api/v1/system/disk-io           ✗ NO AUTH

# Service Management
GET    /api/v1/services                 ✗ NO AUTH
POST   /api/v1/services/{name}/action   ✗ NO AUTH (CRITICAL!)
GET    /api/v1/services/{name}/logs     ✗ NO AUTH
GET    /api/v1/services/{name}/stats    ✗ NO AUTH

# AI Model Management
GET    /api/v1/models                   ✗ NO AUTH
POST   /api/v1/models/download          ✗ NO AUTH (CRITICAL!)
DELETE /api/v1/models/{model_id}        ✗ NO AUTH (CRITICAL!)
POST   /api/v1/models/active            ✗ NO AUTH (CRITICAL!)
POST   /api/v1/vllm/switch-model        ✗ NO AUTH (CRITICAL!)

# Network Configuration
GET    /api/v1/network/status           ✗ NO AUTH
POST   /api/v1/network/wifi/connect     ✗ NO AUTH (CRITICAL!)
POST   /api/v1/network/configure        ✗ NO AUTH (CRITICAL!)

# Storage & Backup
GET    /api/v1/storage                  ✗ NO AUTH
POST   /api/v1/backup/create            ✗ NO AUTH (CRITICAL!)
POST   /api/v1/backup/{id}/restore      ✗ NO AUTH (CRITICAL!)
DELETE /api/v1/backup/{id}              ✗ NO AUTH (CRITICAL!)

# Extensions
GET    /api/v1/extensions               ✗ NO AUTH
POST   /api/v1/extensions/install       ✗ NO AUTH (CRITICAL!)
DELETE /api/v1/extensions/{id}          ✗ NO AUTH (CRITICAL!)
POST   /api/v1/extensions/{id}/control  ✗ NO AUTH (CRITICAL!)

# Logs
GET    /api/v1/logs/sources             ✗ NO AUTH
POST   /api/v1/logs/search              ✗ NO AUTH
POST   /api/v1/logs/export              ✗ NO AUTH

# System Updates
GET    /api/v1/updates/status           ✗ NO AUTH
POST   /api/v1/updates/check            ✗ NO AUTH
POST   /api/v1/updates/apply            ✗ NO AUTH (CRITICAL!)

# Landing Page Customization
GET    /api/v1/landing/config           ✗ NO AUTH
POST   /api/v1/landing/config           ✗ NO AUTH
POST   /api/v1/landing/theme/{preset}   ✗ NO AUTH
```

---

## Recommended Security Improvements

### Immediate Actions (Deploy within 24 hours)

#### 1. Add Authentication to ALL Administrative Endpoints

**Priority:** CRITICAL

```python
# File: backend/server.py

# Add authentication decorator
from functools import wraps

def require_authenticated(func):
    """Require any authenticated user"""
    async def wrapper(*args, current_user: dict = Depends(get_current_user), **kwargs):
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper

# Apply to ALL endpoints
@app.get("/api/v1/services")
async def get_services(current_user: dict = Depends(get_current_user)):
    # Only authenticated users can view services
    pass

@app.post("/api/v1/services/{container_name}/action")
async def service_action(
    container_name: str,
    action: ServiceAction,
    current_user: dict = Depends(require_admin)  # Admin only!
):
    # Only admins can control services
    pass
```

#### 2. Implement Role-Based Endpoint Protection

**Priority:** CRITICAL

```python
# File: backend/auth_manager.py

# Add role hierarchy
ROLE_HIERARCHY = {
    "admin": 4,
    "power_user": 3,
    "user": 2,
    "viewer": 1
}

# File: backend/server.py

async def require_role(minimum_role: str):
    """Require minimum role level"""
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "viewer")
        if ROLE_HIERARCHY.get(user_role, 0) < ROLE_HIERARCHY.get(minimum_role, 999):
            raise HTTPException(
                status_code=403,
                detail=f"{minimum_role} role required"
            )
        return current_user
    return Depends(role_checker)

# Usage
@app.post("/api/v1/models/download")
async def download_model(
    model: ModelDownload,
    current_user: dict = require_role("power_user")  # power_user or admin
):
    pass

@app.post("/api/v1/services/{name}/action")
async def service_action(
    name: str,
    action: ServiceAction,
    current_user: dict = require_role("admin")  # admin only
):
    pass
```

#### 3. Add CSRF Protection

**Priority:** HIGH

```python
# File: backend/server.py

from fastapi_csrf_protect import CsrfProtect
from pydantic import BaseModel

class CsrfSettings(BaseModel):
    secret_key: str = os.getenv("CSRF_SECRET_KEY", secrets.token_urlsafe(32))
    cookie_samesite: str = "lax"
    cookie_secure: bool = True

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

# Add to all state-changing operations
@app.post("/api/v1/services/{container_name}/action")
async def service_action(
    container_name: str,
    action: ServiceAction,
    csrf_protect: CsrfProtect = Depends(),
    current_user: dict = Depends(require_admin)
):
    await csrf_protect.validate_csrf(request)
    # ... rest of endpoint
```

#### 4. Implement Rate Limiting

**Priority:** HIGH

```python
# File: backend/server.py

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to authentication endpoints
@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(request: Request, credentials: LoginCredentials):
    pass

@app.post("/auth/direct-login")
@limiter.limit("5/minute")
async def direct_login(request: Request, credentials: LoginCredentials):
    pass
```

---

### Short-Term Improvements (Deploy within 1 week)

#### 5. Implement Frontend Role Filtering

**Priority:** HIGH

```javascript
// File: src/components/Layout.jsx

const navigation = [
  { name: 'Dashboard', href: '/admin/', icon: HomeIcon, roles: ['admin', 'power_user', 'user', 'viewer'] },
  { name: 'Models & AI', href: '/admin/models', icon: CubeIcon, roles: ['admin', 'power_user'] },
  { name: 'Services', href: '/admin/services', icon: ServerIcon, roles: ['admin'] },
  { name: 'Resources', href: '/admin/system', icon: ChartBarIcon, roles: ['admin'] },
  { name: 'Network', href: '/admin/network', icon: WifiIcon, roles: ['admin'] },
  { name: 'Storage', href: '/admin/storage', icon: ArchiveBoxIcon, roles: ['admin', 'power_user'] },
  { name: 'Logs', href: '/admin/logs', icon: DocumentTextIcon, roles: ['admin', 'power_user'] },
  { name: 'Security', href: '/admin/security', icon: ShieldCheckIcon, roles: ['admin'] },
  { name: 'Authentication', href: '/admin/authentication', icon: KeyIcon, roles: ['admin'] },
  { name: 'Extensions', href: '/admin/extensions', icon: PuzzlePieceIcon, roles: ['admin', 'power_user'] },
  { name: 'Landing Page', href: '/admin/landing', icon: PaintBrushIcon, roles: ['admin'] },
  { name: 'Settings', href: '/admin/settings', icon: CogIcon, roles: ['admin', 'power_user', 'user'] },
];

// Filter navigation based on user role
const userRole = userInfo.role || 'viewer';
const filteredNavigation = navigation.filter(item =>
  item.roles.includes(userRole)
);

// Render filtered navigation
{filteredNavigation.map((item) => {
  // ...
})}
```

#### 6. Add Security Headers

**Priority:** MEDIUM

```python
# File: backend/server.py

from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["unicorncommander.ai", "*.unicorncommander.ai", "localhost"]
)
```

#### 7. Strengthen Password Policy

**Priority:** MEDIUM

```python
# File: backend/auth_manager.py

import re

@validator('new_password')
def password_strength(cls, v):
    if len(v) < 12:
        raise ValueError('Password must be at least 12 characters')

    if not re.search(r'[A-Z]', v):
        raise ValueError('Password must contain at least one uppercase letter')

    if not re.search(r'[a-z]', v):
        raise ValueError('Password must contain at least one lowercase letter')

    if not re.search(r'[0-9]', v):
        raise ValueError('Password must contain at least one number')

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
        raise ValueError('Password must contain at least one special character')

    # Check against common passwords
    common_passwords = ['Password123!', 'Admin123!', 'Welcome123!']
    if v in common_passwords:
        raise ValueError('Password is too common, please choose a stronger password')

    return v
```

#### 8. Implement Session Expiration

**Priority:** MEDIUM

```python
# File: backend/server.py

# Add session cleanup task
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', minutes=15)
async def cleanup_sessions():
    """Remove expired sessions every 15 minutes"""
    now = datetime.now()
    expired = []

    for session_id, session_data in sessions.items():
        created_at = datetime.fromisoformat(session_data['created_at'])
        if (now - created_at).total_seconds() > 3600:  # 1 hour expiry
            expired.append(session_id)

    for session_id in expired:
        del sessions[session_id]

    print(f"Cleaned up {len(expired)} expired sessions")

scheduler.start()
```

---

### Long-Term Improvements (Deploy within 1 month)

#### 9. Implement Audit Logging

**Priority:** MEDIUM

```python
# File: backend/audit_logger.py

class AuditLogger:
    """Log security-relevant events"""

    def log_event(self, event_type: str, user_id: str, resource: str, action: str, success: bool, details: dict = None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "success": success,
            "details": details or {},
            "ip_address": request.client.host if request.client else "unknown"
        }

        # Write to audit log
        with open("/var/log/uc1-audit.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")

# Usage
@app.post("/api/v1/services/{container_name}/action")
async def service_action(
    container_name: str,
    action: ServiceAction,
    current_user: dict = Depends(require_admin)
):
    try:
        result = docker_manager.perform_action(container_name, action.action)
        audit_logger.log_event(
            event_type="service_action",
            user_id=current_user["user_id"],
            resource=container_name,
            action=action.action,
            success=True
        )
        return result
    except Exception as e:
        audit_logger.log_event(
            event_type="service_action",
            user_id=current_user["user_id"],
            resource=container_name,
            action=action.action,
            success=False,
            details={"error": str(e)}
        )
        raise
```

#### 10. Add Permission-Based Access Control

**Priority:** MEDIUM

```python
# File: backend/permissions.py

from enum import Enum

class Permission(Enum):
    # Service permissions
    SERVICE_VIEW = "service:view"
    SERVICE_START = "service:start"
    SERVICE_STOP = "service:stop"
    SERVICE_RESTART = "service:restart"
    SERVICE_LOGS = "service:logs"

    # Model permissions
    MODEL_VIEW = "model:view"
    MODEL_DOWNLOAD = "model:download"
    MODEL_ACTIVATE = "model:activate"
    MODEL_DELETE = "model:delete"

    # System permissions
    SYSTEM_VIEW = "system:view"
    SYSTEM_CONFIGURE = "system:configure"
    NETWORK_CONFIGURE = "network:configure"

    # User permissions
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

# Role permission mapping
ROLE_PERMISSIONS = {
    "admin": [p.value for p in Permission],  # All permissions
    "power_user": [
        Permission.SERVICE_VIEW.value,
        Permission.SERVICE_LOGS.value,
        Permission.MODEL_VIEW.value,
        Permission.MODEL_DOWNLOAD.value,
        Permission.MODEL_ACTIVATE.value,
        Permission.SYSTEM_VIEW.value,
    ],
    "user": [
        Permission.SERVICE_VIEW.value,
        Permission.MODEL_VIEW.value,
        Permission.SYSTEM_VIEW.value,
    ],
    "viewer": [
        Permission.SERVICE_VIEW.value,
        Permission.MODEL_VIEW.value,
        Permission.SYSTEM_VIEW.value,
    ]
}

def require_permission(permission: Permission):
    """Dependency to check if user has specific permission"""
    def permission_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "viewer")
        user_permissions = ROLE_PERMISSIONS.get(user_role, [])

        if permission.value not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission {permission.value} required"
            )

        return current_user
    return Depends(permission_checker)

# Usage
@app.post("/api/v1/services/{container_name}/action")
async def service_action(
    container_name: str,
    action: ServiceAction,
    current_user: dict = require_permission(Permission.SERVICE_RESTART)
):
    pass
```

---

## Recommended Access Control Matrix

| Feature | Admin | Power User | User | Viewer |
|---------|-------|------------|------|--------|
| **Dashboard** | ✓ Full | ✓ Full | ✓ Full | ✓ Read-only |
| **Services** |
| - View services | ✓ | ✓ | ✓ | ✓ |
| - Start/stop services | ✓ | ✗ | ✗ | ✗ |
| - View logs | ✓ | ✓ | ✓ | ✓ |
| - Configure services | ✓ | ✗ | ✗ | ✗ |
| **AI Models** |
| - View models | ✓ | ✓ | ✓ | ✓ |
| - Download models | ✓ | ✓ | ✗ | ✗ |
| - Activate models | ✓ | ✓ | ✗ | ✗ |
| - Delete models | ✓ | ✗ | ✗ | ✗ |
| **Network** |
| - View status | ✓ | ✓ | ✓ | ✓ |
| - Configure network | ✓ | ✗ | ✗ | ✗ |
| - WiFi management | ✓ | ✗ | ✗ | ✗ |
| **Storage & Backup** |
| - View storage | ✓ | ✓ | ✓ | ✓ |
| - Create backups | ✓ | ✓ | ✗ | ✗ |
| - Restore backups | ✓ | ✗ | ✗ | ✗ |
| - Delete backups | ✓ | ✗ | ✗ | ✗ |
| **Extensions** |
| - View extensions | ✓ | ✓ | ✓ | ✓ |
| - Install extensions | ✓ | ✓ | ✗ | ✗ |
| - Remove extensions | ✓ | ✗ | ✗ | ✗ |
| - Configure extensions | ✓ | ✓ | ✗ | ✗ |
| **Logs** |
| - View logs | ✓ | ✓ | ✓ | ✓ |
| - Export logs | ✓ | ✓ | ✗ | ✗ |
| - Search logs | ✓ | ✓ | ✓ | ✓ |
| **Security** |
| - View security status | ✓ | ✓ | ✗ | ✗ |
| - Configure security | ✓ | ✗ | ✗ | ✗ |
| **Authentication** |
| - View users | ✓ | ✗ | ✗ | ✗ |
| - Create users | ✓ | ✗ | ✗ | ✗ |
| - Manage SSO | ✓ | ✗ | ✗ | ✗ |
| **System Updates** |
| - Check updates | ✓ | ✓ | ✓ | ✓ |
| - Apply updates | ✓ | ✗ | ✗ | ✗ |
| **Landing Page** |
| - Customize landing | ✓ | ✗ | ✗ | ✗ |
| **Settings** |
| - View settings | ✓ | ✓ | ✓ | ✗ |
| - Modify settings | ✓ | ✓ (limited) | ✗ | ✗ |

---

## Security Best Practices

### 1. Defense in Depth
- **Backend validation is mandatory** - Never trust frontend
- **Frontend filtering is UX enhancement** - Not security
- **Multiple layers of security** - Authentication + Authorization + Validation

### 2. Principle of Least Privilege
- Users should have minimum permissions needed
- Default to most restrictive, grant as needed
- Regular permission audits

### 3. Fail Securely
```python
# BAD
if user.role == "admin":
    allow_access()
# Falls through to allow if role check fails!

# GOOD
if user.role != "admin":
    raise HTTPException(status_code=403, detail="Admin required")
# Explicit denial
```

### 4. Audit Everything
- Log all authentication attempts
- Log all authorization failures
- Log all administrative actions
- Retain logs for compliance

### 5. Regular Security Reviews
- Monthly dependency updates
- Quarterly penetration testing
- Annual security audits
- Continuous monitoring

---

## Testing Recommendations

### 1. Authentication Tests
```python
# Test unauthenticated access
def test_services_requires_auth():
    response = client.get("/api/v1/services")
    assert response.status_code == 401

# Test expired token
def test_expired_token_rejected():
    expired_token = generate_expired_token()
    response = client.get("/api/v1/services", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
```

### 2. Authorization Tests
```python
# Test role-based access
def test_power_user_cannot_stop_services():
    token = login_as("power_user")
    response = client.post(
        "/api/v1/services/unicorn-postgres/action",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "stop"}
    )
    assert response.status_code == 403

# Test admin can stop services
def test_admin_can_stop_services():
    token = login_as("admin")
    response = client.post(
        "/api/v1/services/unicorn-postgres/action",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "stop"}
    )
    assert response.status_code == 200
```

### 3. CSRF Tests
```python
def test_csrf_protection():
    # Login to get session
    token = login_as("admin")

    # Attempt action without CSRF token
    response = client.post(
        "/api/v1/services/unicorn-postgres/action",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "restart"}
    )
    assert response.status_code == 403
    assert "CSRF" in response.json()["detail"]
```

---

## Compliance Considerations

### GDPR
- ✓ User data protection (password hashing)
- ✗ Missing data retention policies
- ✗ No user data export functionality
- ✗ Incomplete audit trails

### SOC 2
- ✗ Insufficient access controls
- ✗ Incomplete audit logging
- ✗ No session management policy
- ✗ Missing encryption at rest

### ISO 27001
- ✗ No documented access control policy
- ✗ Insufficient authentication mechanisms
- ✗ Missing security incident response procedures

---

## Conclusion

The Ops-Center RBAC system has **critical security vulnerabilities** that must be addressed immediately. While the authentication infrastructure exists, it is **not enforced** on the majority of administrative endpoints.

### Priority Actions:
1. **CRITICAL (Today):** Add authentication to all administrative endpoints
2. **CRITICAL (Today):** Implement role-based access controls
3. **HIGH (This Week):** Add CSRF protection
4. **HIGH (This Week):** Implement rate limiting
5. **MEDIUM (This Month):** Strengthen password policies and session management

### Risk Summary:
- **Current Risk Level:** CRITICAL
- **Post-Immediate Actions:** HIGH
- **Post-All Fixes:** LOW

The system should **not be deployed to production** in its current state without implementing at minimum the critical and high-priority fixes outlined in this review.

---

## References

- OWASP Top 10 2021: https://owasp.org/Top10/
- OWASP API Security Top 10: https://owasp.org/API-Security/
- FastAPI Security Best Practices: https://fastapi.tiangolo.com/tutorial/security/
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework

---

**Report Generated:** October 9, 2025
**Next Review Due:** November 9, 2025
