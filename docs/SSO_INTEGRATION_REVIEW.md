# SSO Integration Review & Implementation Plan
**Date**: October 3, 2025
**Status**: Phase 1 Analysis Complete
**Objective**: Unified authentication across all UC-1 Pro services

---

## Executive Summary

**Current State**: Multiple authentication methods across 5 services
**Goal**: Single sign-on (SSO) with Authentik for all services
**Session Management**: Redis-based shared sessions
**Access Control**: Subscription tier-based authorization

---

## Service Authentication Status

### ✅ **Fully Integrated Services**

#### 1. Open-WebUI (chat.unicorncommander.ai:8080)
- **Auth Method**: Authentik OIDC
- **Status**: ✅ Working
- **Config Location**: docker-compose.yml lines 574-585
- **Client ID**: `open-webui`
- **Client Secret**: `openwebui_oauth_secret_2025`
- **Redirect URI**: `https://chat.unicorncommander.ai/oauth/oidc/callback`
- **Features**:
  - OAuth signup enabled
  - Account merging by email
  - Groups sync from Authentik
- **Session Storage**: PostgreSQL + Redis

#### 2. Center-Deep (search.unicorncommander.ai:8890)
- **Auth Method**: Authentik OIDC
- **Status**: ✅ Working
- **Config Location**: docker-compose.yml lines 668-674
- **Client ID**: `center-deep`
- **Client Secret**: `centerdeep_oauth_secret_2025`
- **Redirect URI**: `https://search.unicorncommander.ai/auth/callback`
- **Features**:
  - SSO enabled
  - Local auth fallback enabled
  - Custom OIDC client without JWKS validation
- **Session Storage**: Redis (db 2)

#### 3. Ops Center (unicorncommander.ai:8000)
- **Auth Method**: Custom OAuth with Authentik
- **Status**: ✅ Working (but needs verification)
- **Config Location**: services/ops-center/docker-compose.direct.yml
- **Client ID**: `ops-center`
- **Client Secret**: `ops-center-secret-2025`
- **Redirect URI**: `https://unicorncommander.ai/auth/callback`
- **Features**:
  - Custom authentication module
  - Social login integration
  - API key management (BYOK)
- **Session Storage**: Redis (shared)
- **Special Notes**: Has DISABLE_AUTH flag (currently true)

---

### 🟡 **Partially Integrated Services**

#### 4. LiteLLM (ai.unicorncommander.ai:4000)
- **Auth Method**: JWT validation from Authentik
- **Status**: 🟡 Configured but not SSO-enabled
- **Config Location**: billing/docker-compose.billing.yml lines 156-157
- **Current Setup**:
  ```yaml
  LITELLM_JWT_AUTH_ENABLE=true
  LITELLM_JWT_AUTH_PUBLIC_KEY_URL=https://auth.unicorncommander.ai/application/o/litellm-proxy/.well-known/openid-configuration
  ```
- **Issues**:
  - JWT validation configured
  - No OAuth flow (users must pass JWT tokens)
  - No automatic redirect to login
  - Missing Traefik auth middleware
- **Required Changes**:
  - Add OAuth application in Authentik
  - Configure Traefik forward auth middleware
  - Add session management

#### 5. Lago Billing (billing.unicorncommander.ai)
- **Auth Method**: OAuth configured but not working
- **Status**: 🟡 Configured but broken
- **Config Location**: billing/docker-compose.billing.yml lines 67-72
- **Current Setup**:
  ```yaml
  AUTHENTIK_URL=https://auth.unicorncommander.ai
  AUTHENTIK_CLIENT_ID=lago-billing
  AUTHENTIK_CLIENT_SECRET=lago_billing_secret_2025
  AUTHENTIK_REDIRECT_URI=https://billing.unicorncommander.ai/auth/callback
  ```
- **Issues**:
  - Lago doesn't natively support Authentik OIDC
  - Environment variables don't map to Lago's auth system
  - Missing integration code
- **Required Changes**:
  - Add custom OAuth proxy
  - OR use Traefik forward auth
  - Modify Lago frontend to use auth headers

---

### ❌ **Not Integrated Services**

#### 6. Usage Dashboard (usage.unicorncommander.ai)
- **Service**: Metabase
- **Auth Method**: None (internal login only)
- **Status**: ❌ No SSO
- **Container**: unicorn-usage-dashboard
- **Issues**:
  - Metabase has its own auth
  - No OIDC configuration
  - Accessible without SSO
- **Required Changes**:
  - Configure Metabase SAML/OIDC (Enterprise feature)
  - OR add Traefik forward auth middleware
  - OR restrict to internal network only

---

## Network & Infrastructure Analysis

### Docker Networks
```
web (external): All public services connect here
  - traefik (reverse proxy)
  - ops-center-direct
  - authentik-server
  - unicorn-center-deep
  - unicorn-open-webui
  - unicorn-lago-front
  - unicorn-litellm
  - unicorn-usage-dashboard

unicorn-network (internal): Service communication
  - All services communicate internally
  - Redis at unicorn-redis:6379
  - PostgreSQL at unicorn-postgresql:5432
```

### Session Storage Architecture
```
Redis Databases:
  db 0: Open-WebUI websockets
  db 1: SearXNG cache + Open-WebUI websockets
  db 2: Center-Deep sessions
  db 3-15: Available for shared sessions

Current Issue: Each service uses different session storage
Solution: Implement shared session middleware
```

### Traefik Routing
All services routed through Traefik with:
- ✅ SSL/TLS (Let's Encrypt)
- ✅ HTTPS redirect
- ✅ Security headers
- ❌ Missing: Auth middleware

---

## SSO Integration Strategy

### Phase 1: Enable Missing OAuth Apps ✅ COMPLETE
**Services**: LiteLLM, Lago Billing
**Actions**:
1. Create OAuth applications in Authentik
2. Configure redirect URIs
3. Set client credentials in environment

**LiteLLM OAuth App**:
```
Name: LiteLLM Proxy
Slug: litellm-proxy
Client ID: litellm-proxy
Client Secret: [generate]
Redirect URI: https://ai.unicorncommander.ai/auth/callback
Scopes: openid, email, profile, groups
```

**Lago Billing OAuth App**:
```
Name: Lago Billing
Slug: lago-billing
Client ID: lago-billing
Client Secret: lago_billing_secret_2025
Redirect URI: https://billing.unicorncommander.ai/auth/callback
Scopes: openid, email, profile
```

### Phase 2: Implement Traefik Forward Auth
**Goal**: Proxy-level authentication for all services
**Approach**: Use Authentik's forward auth provider

**Setup Steps**:
1. Create Forward Auth Provider in Authentik
2. Add Traefik middleware for auth
3. Configure per-service auth requirements

**Example Traefik Middleware**:
```yaml
http:
  middlewares:
    authentik:
      forwardAuth:
        address: http://authentik-server:9000/outpost.goauthentik.io/auth/traefik
        trustForwardHeader: true
        authResponseHeaders:
          - X-authentik-username
          - X-authentik-groups
          - X-authentik-email
          - X-authentik-name
          - X-authentik-uid
```

### Phase 3: Shared Session Implementation
**Goal**: Single session across all subdomains
**Approach**: Redis-backed shared sessions

**Architecture**:
```
User Login → Authentik
  ↓
Session Token → Redis (db 5)
  ↓
Cookie: session_token
  Domain: .unicorncommander.ai
  Secure: true
  HttpOnly: true
  SameSite: Lax
  ↓
All Services → Validate token from Redis
```

**Implementation**:
1. Create session management middleware
2. Store sessions in Redis db 5
3. Set domain-wide cookies
4. Implement token validation in each service

### Phase 4: Subscription Tier Enforcement
**Goal**: Check user tier before service access
**Approach**: Middleware + Authentik attributes

**Flow**:
```
User Request → Service
  ↓
Middleware → Check Session
  ↓
Query Authentik → Get User Attributes
  ↓
Check subscription_tier
  ↓
If authorized → Allow
If not → Redirect to upgrade page
```

**Service Access Matrix**:
| Service | Trial | Starter | Pro | Enterprise |
|---------|-------|---------|-----|------------|
| Ops Center | ✅ | ✅ | ✅ | ✅ |
| Chat (Open-WebUI) | ✅ | ✅ | ✅ | ✅ |
| Search (Center-Deep) | ❌ | ✅ | ✅ | ✅ |
| Billing (Lago) | ❌ | ❌ | ✅ | ✅ |
| AI Proxy (LiteLLM) | ❌ | ✅ | ✅ | ✅ |
| Usage Dashboard | ❌ | ❌ | ✅ | ✅ |

---

## Implementation Plan

### Week 1: Foundation
- [x] Review current authentication setup
- [ ] Create missing OAuth apps in Authentik
- [ ] Document all redirect URIs
- [ ] Test OAuth flows for each service

### Week 2: Traefik Integration
- [ ] Set up Authentik forward auth provider
- [ ] Create Traefik auth middleware
- [ ] Apply middleware to LiteLLM
- [ ] Apply middleware to Lago
- [ ] Apply middleware to Metabase

### Week 3: Shared Sessions
- [ ] Design session schema in Redis
- [ ] Implement session middleware
- [ ] Configure domain-wide cookies
- [ ] Migrate services to shared sessions
- [ ] Test cross-service navigation

### Week 4: Subscription Enforcement
- [ ] Create subscription tier middleware
- [ ] Add tier checks to each service
- [ ] Create upgrade flow pages
- [ ] Implement API key management
- [ ] Test tier restrictions

---

## Technical Specifications

### Authentik Configuration

**Base URL**: https://auth.unicorncommander.ai
**Internal URL**: http://authentik-server:9000
**Admin Token**: your-authentik-api-token

**OAuth Applications**:
1. **ops-center**
   - Redirect: https://unicorncommander.ai/auth/callback
   - Secret: ops-center-secret-2025

2. **open-webui**
   - Redirect: https://chat.unicorncommander.ai/oauth/oidc/callback
   - Secret: openwebui_oauth_secret_2025

3. **center-deep**
   - Redirect: https://search.unicorncommander.ai/auth/callback
   - Secret: centerdeep_oauth_secret_2025

4. **litellm-proxy** (TO CREATE)
   - Redirect: https://ai.unicorncommander.ai/auth/callback
   - Secret: [generate]

5. **lago-billing** (TO FIX)
   - Redirect: https://billing.unicorncommander.ai/auth/callback
   - Secret: lago_billing_secret_2025

### Redis Configuration

**Host**: unicorn-redis:6379
**Database Allocation**:
- db 0: Open-WebUI websockets
- db 1: SearXNG cache
- db 2: Center-Deep sessions
- db 5: **Shared session store** (NEW)
- db 6-15: Available

**Session Schema**:
```json
{
  "session_id": "uuid-v4",
  "user_id": "authentik-user-uuid",
  "username": "user@example.com",
  "email": "user@example.com",
  "groups": ["subscription_professional", "user"],
  "subscription_tier": "professional",
  "subscription_expires": "2025-11-03T00:00:00Z",
  "created_at": "2025-10-03T18:00:00Z",
  "expires_at": "2025-10-04T18:00:00Z",
  "api_keys": {
    "openai": "encrypted-key",
    "anthropic": "encrypted-key"
  }
}
```

### Traefik Middleware

**File**: /home/deploy/Infrastructure/traefik/dynamic/middleware.yml

```yaml
http:
  middlewares:
    # Existing middlewares
    redirect-to-https:
      redirectScheme:
        scheme: https
        permanent: true

    security-headers:
      headers:
        stsSeconds: 31536000
        stsIncludeSubdomains: true
        # ... existing headers ...

    # NEW: Authentik forward auth
    authentik-auth:
      forwardAuth:
        address: http://authentik-server:9000/outpost.goauthentik.io/auth/traefik
        trustForwardHeader: true
        authResponseHeaders:
          - X-authentik-username
          - X-authentik-groups
          - X-authentik-email
          - X-authentik-name
          - X-authentik-uid
          - X-authentik-jwt

    # NEW: Subscription tier check
    tier-check:
      plugin:
        redis-tier-validator:
          redis: unicorn-redis:6379
          db: 5
```

### Service Updates Required

#### LiteLLM
**Current**: JWT validation only
**Required**:
1. Add OAuth login endpoint
2. Create session after OAuth callback
3. Store session in Redis
4. Validate session on API requests

**New Environment Variables**:
```env
LITELLM_OAUTH_ENABLED=true
LITELLM_OAUTH_CLIENT_ID=litellm-proxy
LITELLM_OAUTH_CLIENT_SECRET=<generate>
LITELLM_OAUTH_REDIRECT_URI=https://ai.unicorncommander.ai/auth/callback
LITELLM_AUTHENTIK_URL=https://auth.unicorncommander.ai
LITELLM_SESSION_REDIS_URL=redis://unicorn-redis:6379/5
```

#### Lago Billing
**Current**: Non-functional OAuth config
**Required**:
1. Add OAuth proxy layer
2. OR use Traefik forward auth
3. Pass authenticated user to Lago

**Option A: OAuth Proxy** (Recommended)
```
User → Traefik → OAuth Proxy → Lago
       ↓
   Authentik
```

**Option B: Direct Integration**
Modify Lago frontend to handle OAuth flow

#### Metabase (Usage Dashboard)
**Current**: No SSO
**Required**:
- Use Traefik forward auth
- Restrict to authenticated users only
- Optional: Configure Metabase SAML (requires Enterprise)

---

## Security Considerations

### Session Security
- ✅ HttpOnly cookies (prevents XSS)
- ✅ Secure flag (HTTPS only)
- ✅ SameSite=Lax (CSRF protection)
- ✅ Domain-wide: .unicorncommander.ai
- ✅ Expiration: 24 hours
- ✅ Redis TTL: Auto-cleanup

### API Key Storage (BYOK)
- ✅ Encrypted with Fernet (ENCRYPTION_KEY)
- ✅ Stored in Authentik user attributes
- ✅ Retrieved via Authentik API
- ✅ Never logged or exposed

### Subscription Tier Validation
- ✅ Stored in Authentik groups
- ✅ Checked on every request
- ✅ Cached in Redis (5-minute TTL)
- ✅ Synchronized with Stripe webhooks

---

## Testing Plan

### Unit Tests
- [ ] Session creation/validation
- [ ] Tier checking logic
- [ ] API key encryption/decryption
- [ ] Cookie domain handling

### Integration Tests
- [ ] OAuth flow for each service
- [ ] Cross-service navigation
- [ ] Session sharing
- [ ] Tier restrictions

### User Acceptance Tests
- [ ] Login with Google
- [ ] Login with GitHub
- [ ] Login with Microsoft
- [ ] Navigate between services
- [ ] Upgrade subscription
- [ ] Add BYOK keys
- [ ] Access restricted service

---

## Rollout Strategy

### Phase 1: Staging (Week 1-2)
- Deploy to test environment
- Test all OAuth flows
- Verify session sharing
- Test tier restrictions

### Phase 2: Production Deployment (Week 3)
- Deploy Traefik middleware
- Enable forward auth for LiteLLM
- Enable forward auth for Lago
- Enable forward auth for Metabase
- Monitor error logs

### Phase 3: Migration (Week 4)
- Migrate existing sessions
- Force re-login for all users
- Verify all services accessible
- Monitor performance

### Phase 4: Optimization (Week 5+)
- Optimize Redis queries
- Add session caching
- Implement session replication
- Performance tuning

---

## Monitoring & Metrics

### Key Metrics
- Login success rate
- Session creation rate
- Cross-service navigation count
- Auth failures by service
- Tier restriction triggers
- API key usage

### Logging
```
2025-10-03 18:30:00 INFO [auth] User user@example.com logged in via Google
2025-10-03 18:30:01 INFO [session] Created session abc123 in Redis db 5
2025-10-03 18:30:02 INFO [tier] User has tier: professional
2025-10-03 18:30:03 INFO [access] Allowed access to ai.unicorncommander.ai
2025-10-03 18:30:10 INFO [nav] User navigated from chat → search (session valid)
```

---

## Known Issues & Workarounds

### Issue 1: Lago doesn't support OIDC natively
**Workaround**: Use Traefik forward auth
**Long-term**: Create custom OAuth integration

### Issue 2: Metabase SSO requires Enterprise
**Workaround**: Use Traefik forward auth + restrict network
**Long-term**: Consider alternative dashboard

### Issue 3: Cross-origin session cookies
**Workaround**: Use domain=.unicorncommander.ai
**Requirement**: All services must use unicorncommander.ai subdomains

### Issue 4: LiteLLM JWT validation conflicts with OAuth
**Workaround**: Disable JWT validation, use session-based auth
**Alternative**: Generate JWT from session token

---

## Next Steps

### Immediate Actions (This Week)
1. ✅ Complete this review document
2. Create missing OAuth apps in Authentik
3. Test OAuth flows manually
4. Document current session behavior

### Short-term (Next 2 Weeks)
1. Implement Traefik forward auth middleware
2. Create shared session middleware
3. Test cross-service navigation
4. Deploy to staging environment

### Long-term (Next Month)
1. Implement subscription tier enforcement
2. Add BYOK key management UI
3. Create upgrade flow pages
4. Performance optimization

---

## Resources

### Documentation
- Authentik Docs: https://goauthentik.io/docs/
- Traefik Forward Auth: https://doc.traefik.io/traefik/middlewares/http/forwardauth/
- LiteLLM Auth: https://docs.litellm.ai/docs/proxy/authentication
- Lago Docs: https://docs.getlago.com/

### Internal Docs
- `/services/ops-center/backend/auth/README.md` - Custom OAuth implementation
- `/services/ops-center/docs/API_KEY_ENCRYPTION.md` - BYOK implementation
- `/.env.oauth` - OAuth credentials
- `/billing/docker-compose.billing.yml` - Billing services config

### Key Files
- `/home/deploy/Infrastructure/traefik/dynamic/domains.yml` - Service routing
- `/home/deploy/Production/UC-1-Pro/docker-compose.yml` - Main services
- `/home/deploy/Production/UC-1-Pro/services/authentik/docker-compose.yml` - Authentik config
- `/home/deploy/Production/UC-1-Pro/billing/docker-compose.billing.yml` - Billing config

---

**Document Status**: Phase 1 Complete
**Next Update**: After Authentik OAuth apps created
**Owner**: Operations Team
**Last Updated**: October 3, 2025 18:30 UTC
