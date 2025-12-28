# SSO Implementation Checklist
**Project**: Unified Authentication for UC-1 Pro
**Created**: October 3, 2025
**Priority**: High

---

## 🎯 Phase 1: OAuth Application Setup (2-3 hours)

### Task 1.1: Create LiteLLM OAuth App in Authentik
**Priority**: High | **Status**: ⏳ Pending

**Steps**:
- [ ] Log in to Authentik admin: https://auth.your-domain.com/if/admin/
- [ ] Navigate to Applications → Providers
- [ ] Click "Create" → "OAuth2/OpenID Provider"
- [ ] Configure:
  ```
  Name: LiteLLM Proxy
  Authorization flow: default-provider-authorization-implicit-consent
  Client type: Confidential
  Client ID: litellm-proxy
  Client Secret: [GENERATE - Save to .env]
  Redirect URIs: https://ai.your-domain.com/auth/callback
  Scopes: openid, email, profile, groups
  ```
- [ ] Click "Create" → Save provider
- [ ] Create application linking provider
- [ ] Test OAuth discovery URL: https://auth.your-domain.com/application/o/litellm-proxy/.well-known/openid-configuration
- [ ] Update `/home/muut/Production/UC-1-Pro/billing/.env` with credentials

**Environment Variables to Add**:
```env
LITELLM_OAUTH_CLIENT_ID=litellm-proxy
LITELLM_OAUTH_CLIENT_SECRET=<generated-secret>
LITELLM_OAUTH_REDIRECT_URI=https://ai.your-domain.com/auth/callback
LITELLM_OAUTH_ENABLED=true
```

---

### Task 1.2: Verify Lago OAuth App Configuration
**Priority**: High | **Status**: ⏳ Pending

**Steps**:
- [ ] Log in to Authentik admin
- [ ] Navigate to Applications → Search "lago-billing"
- [ ] Verify provider exists with:
  ```
  Client ID: lago-billing
  Client Secret: lago_billing_secret_2025
  Redirect URI: https://billing.your-domain.com/auth/callback
  ```
- [ ] If missing, create new OAuth provider (same steps as 1.1)
- [ ] Test OAuth discovery URL
- [ ] Verify configuration in `/home/muut/Production/UC-1-Pro/billing/docker-compose.billing.yml`

**Current Config** (verify these match):
```yaml
AUTHENTIK_CLIENT_ID=lago-billing
AUTHENTIK_CLIENT_SECRET=lago_billing_secret_2025
AUTHENTIK_REDIRECT_URI=https://billing.your-domain.com/auth/callback
```

---

### Task 1.3: Verify Existing OAuth Apps
**Priority**: Medium | **Status**: ⏳ Pending

**Apps to Verify**:
- [ ] **ops-center**
  - Client ID: ops-center
  - Redirect: https://your-domain.com/auth/callback
  - Secret: ops-center-secret-2025

- [ ] **open-webui**
  - Client ID: open-webui
  - Redirect: https://chat.your-domain.com/oauth/oidc/callback
  - Secret: openwebui_oauth_secret_2025

- [ ] **center-deep**
  - Client ID: center-deep
  - Redirect: https://search.your-domain.com/auth/callback
  - Secret: centerdeep_oauth_secret_2025

**Verification Commands**:
```bash
# Test OAuth discovery for each app
curl https://auth.your-domain.com/application/o/ops-center/.well-known/openid-configuration
curl https://auth.your-domain.com/application/o/open-webui/.well-known/openid-configuration
curl https://auth.your-domain.com/application/o/center-deep/.well-known/openid-configuration
```

---

## 🔧 Phase 2: Traefik Forward Auth Middleware (4-6 hours)

### Task 2.1: Create Authentik Forward Auth Provider
**Priority**: High | **Status**: ⏳ Pending

**Steps**:
- [ ] Log in to Authentik admin
- [ ] Navigate to Applications → Providers
- [ ] Click "Create" → "Proxy Provider"
- [ ] Configure:
  ```
  Name: Traefik Forward Auth
  Type: Forward auth (single application)
  External host: https://auth.your-domain.com
  ```
- [ ] Create application:
  ```
  Name: Traefik Forward Auth
  Slug: traefik-forward-auth
  Provider: (select created provider)
  ```
- [ ] Note the outpost endpoint: `/outpost.goauthentik.io/auth/traefik`

---

### Task 2.2: Create Traefik Middleware Configuration
**Priority**: High | **Status**: ⏳ Pending

**File**: `/home/muut/Infrastructure/traefik/dynamic/middleware.yml`

**Steps**:
- [ ] Create middleware.yml if doesn't exist
- [ ] Add authentik forward auth middleware:
```yaml
http:
  middlewares:
    authentik:
      forwardAuth:
        address: "http://authentik-server:9000/outpost.goauthentik.io/auth/traefik"
        trustForwardHeader: true
        authResponseHeaders:
          - X-authentik-username
          - X-authentik-groups
          - X-authentik-email
          - X-authentik-name
          - X-authentik-uid
        authRequestHeaders:
          - "X-Forwarded-Proto"
          - "X-Forwarded-Host"
          - "X-Forwarded-Uri"
```

- [ ] Restart Traefik: `docker restart traefik`
- [ ] Verify middleware loaded: `docker logs traefik | grep middleware`

---

### Task 2.3: Apply Middleware to LiteLLM
**Priority**: High | **Status**: ⏳ Pending

**File**: `/home/muut/Production/UC-1-Pro/billing/docker-compose.billing.yml`

**Steps**:
- [ ] Update LiteLLM service labels (around line 179):
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.litellm.rule=Host(`ai.your-domain.com`)"
  - "traefik.http.routers.litellm.entrypoints=https"
  - "traefik.http.routers.litellm.tls.certresolver=letsencrypt"
  - "traefik.http.routers.litellm.middlewares=authentik@file"  # ADD THIS
  - "traefik.http.services.litellm.loadbalancer.server.port=4000"
```

- [ ] Restart LiteLLM: `docker-compose -f billing/docker-compose.billing.yml restart litellm-proxy`
- [ ] Test access: Navigate to https://ai.your-domain.com
- [ ] Should redirect to Authentik login
- [ ] After login, should access LiteLLM

---

### Task 2.4: Apply Middleware to Lago
**Priority**: High | **Status**: ⏳ Pending

**File**: `/home/muut/Production/UC-1-Pro/billing/docker-compose.billing.yml`

**Steps**:
- [ ] Update Lago frontend labels (around line 78):
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.lago-front.rule=Host(`billing.your-domain.com`)"
  - "traefik.http.routers.lago-front.entrypoints=https"
  - "traefik.http.routers.lago-front.tls.certresolver=letsencrypt"
  - "traefik.http.routers.lago-front.middlewares=authentik@file"  # ADD THIS
  - "traefik.http.routers.lago-front.priority=100"
  - "traefik.http.services.lago-front.loadbalancer.server.port=80"
```

- [ ] Restart Lago frontend: `docker-compose -f billing/docker-compose.billing.yml restart lago-front`
- [ ] Test access: Navigate to https://billing.your-domain.com
- [ ] Should redirect to Authentik login

---

### Task 2.5: Apply Middleware to Usage Dashboard
**Priority**: Medium | **Status**: ⏳ Pending

**File**: `/home/muut/Production/UC-1-Pro/billing/docker-compose.billing.yml`

**Steps**:
- [ ] Update Metabase labels (around line 214):
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.usage-dashboard.rule=Host(`usage.your-domain.com`)"
  - "traefik.http.routers.usage-dashboard.entrypoints=https"
  - "traefik.http.routers.usage-dashboard.tls.certresolver=letsencrypt"
  - "traefik.http.routers.usage-dashboard.middlewares=authentik@file"  # ADD THIS
  - "traefik.http.services.usage-dashboard.loadbalancer.server.port=3000"
```

- [ ] Restart Usage Dashboard: `docker restart unicorn-usage-dashboard`
- [ ] Test access: Navigate to https://usage.your-domain.com

---

## 🍪 Phase 3: Shared Session Implementation (6-8 hours)

### Task 3.1: Design Session Schema
**Priority**: High | **Status**: ⏳ Pending

**Steps**:
- [ ] Create `/home/muut/Production/UC-1-Pro/services/ops-center/backend/session_manager.py`
- [ ] Define session schema:
```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict
import redis
import json
import uuid

@dataclass
class UserSession:
    session_id: str
    user_id: str
    username: str
    email: str
    groups: list[str]
    subscription_tier: str
    subscription_expires: str
    created_at: str
    expires_at: str
    api_keys: Dict[str, str]

    def to_dict(self):
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'groups': self.groups,
            'subscription_tier': self.subscription_tier,
            'subscription_expires': self.subscription_expires,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'api_keys': self.api_keys
        }
```

- [ ] Test schema serialization

---

### Task 3.2: Create Session Manager Class
**Priority**: High | **Status**: ⏳ Pending

**File**: `/home/muut/Production/UC-1-Pro/services/ops-center/backend/session_manager.py`

**Implementation**:
```python
class SessionManager:
    def __init__(self, redis_url: str = "redis://unicorn-redis:6379/5"):
        self.redis = redis.from_url(redis_url)
        self.session_ttl = 86400  # 24 hours

    def create_session(self, user_data: dict) -> str:
        """Create new session and return session ID"""
        session_id = str(uuid.uuid4())
        session = UserSession(
            session_id=session_id,
            user_id=user_data['user_id'],
            username=user_data['username'],
            email=user_data['email'],
            groups=user_data.get('groups', []),
            subscription_tier=user_data.get('subscription_tier', 'trial'),
            subscription_expires=user_data.get('subscription_expires', ''),
            created_at=datetime.utcnow().isoformat(),
            expires_at=(datetime.utcnow() + timedelta(seconds=self.session_ttl)).isoformat(),
            api_keys=user_data.get('api_keys', {})
        )

        self.redis.setex(
            f"session:{session_id}",
            self.session_ttl,
            json.dumps(session.to_dict())
        )
        return session_id

    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Retrieve session by ID"""
        data = self.redis.get(f"session:{session_id}")
        if data:
            return UserSession(**json.loads(data))
        return None

    def validate_session(self, session_id: str) -> bool:
        """Check if session is valid"""
        return self.redis.exists(f"session:{session_id}") > 0

    def delete_session(self, session_id: str):
        """Logout - delete session"""
        self.redis.delete(f"session:{session_id}")

    def refresh_session(self, session_id: str):
        """Extend session TTL"""
        self.redis.expire(f"session:{session_id}", self.session_ttl)
```

**Steps**:
- [ ] Create file
- [ ] Add above code
- [ ] Add unit tests
- [ ] Test Redis connection

---

### Task 3.3: Implement Session Middleware
**Priority**: High | **Status**: ⏳ Pending

**File**: `/home/muut/Production/UC-1-Pro/services/ops-center/backend/middleware/session_middleware.py`

**Implementation**:
```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from session_manager import SessionManager

class SessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, session_manager: SessionManager):
        super().__init__(app)
        self.session_manager = session_manager

    async def dispatch(self, request: Request, call_next):
        # Get session cookie
        session_id = request.cookies.get('session_token')

        if session_id and self.session_manager.validate_session(session_id):
            # Valid session - attach to request
            session = self.session_manager.get_session(session_id)
            request.state.user_session = session

            # Refresh TTL
            self.session_manager.refresh_session(session_id)
        else:
            request.state.user_session = None

        response = await call_next(request)
        return response
```

**Steps**:
- [ ] Create middleware file
- [ ] Add to server.py
- [ ] Test middleware activation

---

### Task 3.4: Update OAuth Callback to Create Session
**Priority**: High | **Status**: ⏳ Pending

**File**: `/home/muut/Production/UC-1-Pro/services/ops-center/backend/server.py`

**Steps**:
- [ ] Locate OAuth callback endpoint (around line 300)
- [ ] After successful OAuth validation, create session:
```python
@app.get("/auth/callback")
async def oauth_callback(code: str, state: str, response: Response):
    # ... existing OAuth validation code ...

    # After getting user info from Authentik
    user_data = {
        'user_id': userinfo['sub'],
        'username': userinfo['preferred_username'],
        'email': userinfo['email'],
        'groups': userinfo.get('groups', []),
        'subscription_tier': get_user_tier(userinfo),
        'subscription_expires': get_user_expiry(userinfo),
        'api_keys': {}
    }

    # Create session
    session_id = session_manager.create_session(user_data)

    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_id,
        domain=".your-domain.com",  # Domain-wide
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400  # 24 hours
    )

    return RedirectResponse("/")
```

- [ ] Test OAuth login flow
- [ ] Verify cookie is set
- [ ] Check session in Redis

---

### Task 3.5: Add Session Validation to Protected Routes
**Priority**: High | **Status**: ⏳ Pending

**File**: `/home/muut/Production/UC-1-Pro/services/ops-center/backend/server.py`

**Steps**:
- [ ] Create dependency for session validation:
```python
from fastapi import Depends, HTTPException

async def require_session(request: Request):
    if not hasattr(request.state, 'user_session') or request.state.user_session is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return request.state.user_session

async def require_tier(min_tier: str):
    def check_tier(session: UserSession = Depends(require_session)):
        tier_order = ['trial', 'starter', 'professional', 'enterprise']
        if tier_order.index(session.subscription_tier) < tier_order.index(min_tier):
            raise HTTPException(status_code=403, detail="Upgrade required")
        return session
    return check_tier
```

- [ ] Apply to protected routes:
```python
@app.get("/api/v1/protected-route")
async def protected_route(session: UserSession = Depends(require_session)):
    return {"user": session.username}

@app.get("/api/v1/professional-only")
async def pro_route(session: UserSession = Depends(require_tier('professional'))):
    return {"message": "Welcome professional user"}
```

---

## 🔒 Phase 4: Subscription Tier Enforcement (4-6 hours)

### Task 4.1: Create Tier Validation Middleware
**Priority**: High | **Status**: ⏳ Pending

**File**: `/home/muut/Production/UC-1-Pro/services/ops-center/backend/service_access.py`

**Steps**:
- [ ] Review existing code (already exists)
- [ ] Update to use session manager
- [ ] Add subscription tier checks

**Integration**:
```python
from session_manager import SessionManager

class ServiceAccessManager:
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    def check_service_access(self, session_id: str, service_name: str) -> bool:
        session = self.session_manager.get_session(session_id)
        if not session:
            return False

        tier = session.subscription_tier
        return service_name in SUBSCRIPTION_TIERS[tier]['services']
```

---

### Task 4.2: Create Upgrade Flow Pages
**Priority**: Medium | **Status**: ⏳ Pending

**Files to Create**:
- [ ] `/services/ops-center/public/upgrade.html` - Upgrade landing page
- [ ] `/services/ops-center/backend/templates/access-denied.html` - Access denied page

**Upgrade Page Features**:
- Tier comparison table
- Current user tier display
- Upgrade button (Stripe checkout)
- Service access matrix

---

### Task 4.3: Integrate with Stripe Webhooks
**Priority**: High | **Status**: ⏳ Pending

**Steps**:
- [ ] Review existing Stripe webhook handler
- [ ] Update session on subscription change
- [ ] Update Authentik user attributes

**Webhook Handler**:
```python
@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request: Request):
    event = await request.json()

    if event['type'] == 'customer.subscription.updated':
        # Update user tier
        customer_id = event['data']['object']['customer']
        new_tier = get_tier_from_subscription(event['data']['object'])

        # Update Authentik
        await update_user_tier_in_authentik(customer_id, new_tier)

        # Update all active sessions
        await update_user_sessions(customer_id, new_tier)
```

---

## 📊 Phase 5: Testing & Validation (4-6 hours)

### Task 5.1: Unit Tests
**Priority**: High | **Status**: ⏳ Pending

**Tests to Create**:
- [ ] Session creation/validation
- [ ] Cookie domain handling
- [ ] Tier checking logic
- [ ] API key encryption
- [ ] OAuth flow

**File**: `/home/muut/Production/UC-1-Pro/services/ops-center/tests/test_session.py`

---

### Task 5.2: Integration Tests
**Priority**: High | **Status**: ⏳ Pending

**Scenarios to Test**:
- [ ] Login via Google → navigate to all services
- [ ] Login via GitHub → check session persistence
- [ ] Login via Microsoft → verify tier restrictions
- [ ] Upgrade subscription → verify immediate access
- [ ] Logout → verify session cleared across all services

---

### Task 5.3: User Acceptance Testing
**Priority**: Medium | **Status**: ⏳ Pending

**Test Users**:
- [ ] Create trial user → test limited access
- [ ] Create starter user → test service access
- [ ] Create professional user → test all features
- [ ] Test subscription upgrade flow
- [ ] Test BYOK key management

---

## 🚀 Phase 6: Deployment (2-4 hours)

### Task 6.1: Staging Deployment
**Priority**: High | **Status**: ⏳ Pending

**Steps**:
- [ ] Deploy to staging environment
- [ ] Run all tests
- [ ] Monitor error logs
- [ ] Performance testing

---

### Task 6.2: Production Deployment
**Priority**: High | **Status**: ⏳ Pending

**Steps**:
- [ ] Backup production database
- [ ] Deploy Traefik middleware
- [ ] Deploy session manager
- [ ] Enable forward auth for services
- [ ] Monitor dashboards
- [ ] Test all services

**Rollback Plan**:
- [ ] Document current configuration
- [ ] Create rollback scripts
- [ ] Test rollback procedure

---

### Task 6.3: User Communication
**Priority**: Medium | **Status**: ⏳ Pending

**Communications**:
- [ ] Email to users about SSO changes
- [ ] Update documentation
- [ ] Create FAQ for common issues
- [ ] Prepare support team

---

## 📈 Post-Deployment Monitoring

### Metrics to Track
- [ ] Login success rate
- [ ] Session creation rate
- [ ] Cross-service navigation count
- [ ] Auth failures by service
- [ ] Tier restriction triggers
- [ ] Response time impact

### Alerts to Configure
- [ ] Auth failure rate > 5%
- [ ] Session creation failures
- [ ] Redis connection issues
- [ ] Authentik downtime

---

## ✅ Success Criteria

- [ ] All 6 services accessible via SSO
- [ ] Single login works across all subdomains
- [ ] Subscription tiers enforced correctly
- [ ] BYOK keys accessible in all services
- [ ] No performance degradation
- [ ] 99.9% auth success rate
- [ ] < 200ms session validation
- [ ] Zero security incidents

---

## 📝 Notes & Decisions

### Decision Log
- **2025-10-03**: Chose Traefik forward auth over service-level OAuth
  - Reason: Easier to maintain, works for all services
  - Trade-off: Less flexibility per-service

- **2025-10-03**: Chose Redis for session storage
  - Reason: Already in use, fast, supports TTL
  - Alternative considered: PostgreSQL (rejected - slower)

### Known Limitations
- Lago doesn't natively support OIDC → using proxy auth
- Metabase SAML requires Enterprise → using forward auth
- LiteLLM JWT conflicts with session auth → disabled JWT

---

**Last Updated**: October 3, 2025
**Next Review**: After Phase 1 completion
**Owner**: Operations Team
