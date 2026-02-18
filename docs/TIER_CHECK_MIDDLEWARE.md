# Tier Check ForwardAuth Middleware

**Status**: ✅ Implemented and Ready
**Date**: October 10, 2025

## Overview

The Tier Check middleware is a Traefik ForwardAuth integration that enforces subscription tier-based access control across UC-1 Pro services. It works in conjunction with OAuth2 Proxy to verify that authenticated users have the required subscription tier to access specific resources.

## Architecture

```
User Request → Traefik
    ↓
OAuth2 Proxy (Authentication)
    ↓
Tier Check ForwardAuth (Authorization)
    ↓
Protected Service (Lago, Admin Panel, etc.)
```

### Flow Details

1. **User requests resource** (e.g., `https://billing.unicorncommander.ai`)
2. **Traefik intercepts** the request
3. **OAuth2 Proxy** checks authentication:
   - If not authenticated → Redirect to Keycloak
   - If authenticated → Add headers (`X-Auth-Request-Email`, `X-Auth-Request-User`)
4. **Tier Check middleware** validates subscription tier:
   - Extracts email from OAuth2 Proxy headers
   - Queries Keycloak for user's `subscription_tier` attribute
   - Compares user tier against required tier
   - Returns 200 OK if authorized, 403 Forbidden if not
5. **Traefik forwards** request to service if both checks pass

## Components

### 1. Tier Check Endpoint

**Location**: `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/tier_check_middleware.py`

**Endpoints**:
- `GET /api/v1/tier-check/health` - Health check
- `GET /api/v1/tier-check/check?tier=<tier>` - Generic tier check
- `GET /api/v1/tier-check/billing` - Billing access (Professional+)
- `GET /api/v1/tier-check/admin` - Admin access (Enterprise)
- `GET /api/v1/tier-check/byok` - BYOK access (Starter+)

**Expected Headers** (from OAuth2 Proxy):
```
X-Auth-Request-Email: user@example.com
X-Auth-Request-User: username
X-Forwarded-Uri: /path/being/accessed
```

**Response Headers** (added to original request):
```
X-User-Email: user@example.com
X-User-Tier: professional
X-Tier-Required: professional
```

### 2. Traefik Middleware Configuration

**Location**: `/home/deploy/Infrastructure/traefik/dynamic/middlewares.yml`

**Middleware Definitions**:

```yaml
http:
  middlewares:
    lago-tier-check:
      forwardAuth:
        address: "http://unicorn-ops-center:8084/api/v1/tier-check/billing"
        trustForwardHeader: true
        authResponseHeaders:
          - "X-User-Email"
          - "X-User-Tier"
          - "X-Tier-Required"

    admin-tier-check:
      forwardAuth:
        address: "http://unicorn-ops-center:8084/api/v1/tier-check/admin"
        trustForwardHeader: true
        authResponseHeaders:
          - "X-User-Email"
          - "X-User-Tier"
          - "X-Tier-Required"

    byok-tier-check:
      forwardAuth:
        address: "http://unicorn-ops-center:8084/api/v1/tier-check/byok"
        trustForwardHeader: true
        authResponseHeaders:
          - "X-User-Email"
          - "X-User-Tier"
          - "X-Tier-Required"
```

### 3. Docker Compose Integration

**Location**: `/home/deploy/Production/UC-1-Pro/billing/docker-compose.billing.yml`

**Lago Frontend Configuration**:
```yaml
labels:
  - "traefik.http.routers.lago-front.middlewares=lago-auth@docker,lago-tier-check@file"
```

Note the `@file` suffix - this tells Traefik to use the middleware defined in `middlewares.yml`, not a Docker label.

## Subscription Tiers

### Tier Hierarchy

| Tier | Level | Monthly Price | Lago Access | Admin Access | BYOK Access |
|------|-------|---------------|-------------|--------------|-------------|
| **Enterprise** | 1 | $99 | ✅ | ✅ | ✅ |
| **Professional** | 2 | $49 | ✅ | ❌ | ✅ |
| **Starter** | 3 | $19 | ❌ | ❌ | ✅ |
| **Trial** | 4 | $1 | ❌ | ❌ | ❌ |
| **Free** | 5 | $0 | ❌ | ❌ | ❌ |

**Access Rules**:
- **Lago Billing**: Requires Professional or Enterprise tier
- **Admin Panel**: Requires Enterprise tier
- **BYOK (Bring Your Own Keys)**: Requires Starter, Professional, or Enterprise tier
- **Basic Services**: All authenticated users (any tier)

## Configuration

### Environment Variables

**Ops-Center** (`.env`):
```bash
# Tier enforcement feature toggle
TIER_ENFORCEMENT_ENABLED=true

# Keycloak connection (for tier lookup)
KEYCLOAK_URL=https://auth.unicorncommander.ai
KEYCLOAK_REALM=uchub
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=your-admin-password
```

### Service Tier Requirements

Tier requirements are defined in `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/tier_check_middleware.py`:

```python
SERVICE_TIER_REQUIREMENTS = {
    "billing": "professional",  # Lago billing
    "admin": "enterprise",      # Admin features
    "byok": "starter",          # BYOK
    "default": "trial"          # Default access
}
```

## Usage Examples

### Protecting a New Service

**Option 1: Use Predefined Middleware**

In `docker-compose.yml`:
```yaml
services:
  my-service:
    labels:
      - "traefik.http.routers.my-service.middlewares=oauth-auth@docker,lago-tier-check@file"
```

**Option 2: Create Custom Middleware**

In `/home/deploy/Infrastructure/traefik/dynamic/middlewares.yml`:
```yaml
http:
  middlewares:
    my-custom-tier-check:
      forwardAuth:
        address: "http://unicorn-ops-center:8084/api/v1/tier-check/check?tier=starter"
        trustForwardHeader: true
```

Then reference it:
```yaml
- "traefik.http.routers.my-service.middlewares=oauth-auth@docker,my-custom-tier-check@file"
```

### Testing Tier Check Manually

```bash
# Test health endpoint
curl http://localhost:8084/api/v1/tier-check/health

# Test billing tier check (simulating OAuth2 Proxy headers)
curl -H "X-Auth-Request-Email: user@example.com" \
     -H "X-Auth-Request-User: testuser" \
     http://localhost:8084/api/v1/tier-check/billing

# Test with specific tier requirement
curl -H "X-Auth-Request-Email: user@example.com" \
     http://localhost:8084/api/v1/tier-check/check?tier=professional
```

## Response Codes

| Code | Meaning | User Action |
|------|---------|-------------|
| **200 OK** | User has required tier | Access granted |
| **401 Unauthorized** | User not authenticated | Login required |
| **403 Forbidden** | Insufficient tier | Upgrade subscription |

### 403 Forbidden Response

When a user lacks the required tier, they receive:

```json
{
  "error": "insufficient_tier",
  "message": "This feature requires Professional tier or higher",
  "current_tier": "starter",
  "required_tier": "professional",
  "upgrade_url": "https://unicorncommander.ai/subscription"
}
```

## Keycloak Integration

### User Attribute Format

Subscription tiers are stored in Keycloak user attributes as **arrays**:

```json
{
  "attributes": {
    "subscription_tier": ["professional"],
    "subscription_status": ["active"],
    "subscription_id": ["lago-sub-123"]
  }
}
```

### Tier Lookup Process

1. Extract user email from `X-Auth-Request-Email` header
2. Query Keycloak Admin API: `GET /admin/realms/uchub/users`
3. Find user by email
4. Extract `subscription_tier[0]` from attributes
5. Compare against required tier using hierarchy

### Setting User Tier Manually

```bash
# Using Keycloak Admin API
curl -X PUT "https://auth.unicorncommander.ai/admin/realms/uchub/users/{user-id}" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "attributes": {
      "subscription_tier": ["professional"]
    }
  }'
```

## Deployment

### Step 1: Update Ops-Center Code

The tier check endpoint is already registered in `server.py`. No code changes needed.

### Step 2: Restart Ops-Center

```bash
docker restart unicorn-ops-center
```

### Step 3: Reload Traefik Configuration

Traefik automatically watches `/home/deploy/Infrastructure/traefik/dynamic/` for changes. If not:

```bash
docker restart traefik
```

### Step 4: Update Service Configurations

For each service that needs tier enforcement, update its `docker-compose.yml`:

```yaml
labels:
  - "traefik.http.routers.{service}.middlewares=oauth-auth@docker,{tier-check-middleware}@file"
```

Replace `{tier-check-middleware}` with:
- `lago-tier-check` for Professional+ access
- `admin-tier-check` for Enterprise-only access
- `byok-tier-check` for Starter+ access

### Step 5: Restart Services

```bash
cd /home/deploy/Production/UC-1-Pro/billing
docker compose -f docker-compose.billing.yml up -d
```

## Monitoring & Logging

### Log Messages

The tier check middleware logs all access attempts:

```
INFO: Tier check PASSED: user@example.com (professional) accessing /billing (requires professional)
WARNING: Tier check FAILED: user@example.com (starter) attempted to access /billing (requires professional)
```

### Viewing Logs

```bash
# Ops-Center logs (tier check endpoint)
docker logs unicorn-ops-center | grep "Tier check"

# Traefik logs (middleware execution)
docker logs traefik | grep "forwardauth"
```

### Metrics

Track tier enforcement metrics:
- Successful tier checks (200)
- Failed tier checks (403)
- Unauthenticated attempts (401)
- Tier upgrade conversions

## Troubleshooting

### Issue: Always Getting 401 Unauthorized

**Cause**: OAuth2 Proxy headers not being passed

**Solution**:
1. Verify OAuth2 Proxy is running:
   ```bash
   docker ps | grep oauth2-proxy
   ```

2. Check middleware order (auth must come before tier-check):
   ```yaml
   middlewares: "lago-auth@docker,lago-tier-check@file"
   ```

3. Verify OAuth2 Proxy configuration includes header passing:
   ```bash
   docker inspect uchub-oauth2-proxy | grep -i "PASS.*HEADER"
   ```

### Issue: Always Getting 403 Forbidden

**Cause**: User tier not set in Keycloak or insufficient tier

**Solution**:
1. Check user's tier in Keycloak:
   ```bash
   # Via Keycloak Admin UI or API
   GET /admin/realms/uchub/users/{user-id}
   ```

2. Verify tier attribute exists and is correct format (array):
   ```json
   "subscription_tier": ["professional"]  // Correct
   "subscription_tier": "professional"    // Wrong
   ```

3. Check tier requirement for service:
   ```bash
   # Look at middleware definition
   cat /home/deploy/Infrastructure/traefik/dynamic/middlewares.yml
   ```

### Issue: Tier Check Not Being Called

**Cause**: Middleware not referenced correctly in service labels

**Solution**:
1. Verify middleware suffix is `@file`:
   ```yaml
   middlewares: "lago-auth@docker,lago-tier-check@file"
                                                   ^^^^^ Must be @file
   ```

2. Verify middleware file exists:
   ```bash
   ls -l /home/deploy/Infrastructure/traefik/dynamic/middlewares.yml
   ```

3. Restart Traefik to reload configuration:
   ```bash
   docker restart traefik
   ```

### Issue: Keycloak Integration Not Working

**Cause**: Keycloak credentials missing from Ops-Center

**Solution**:
1. Add Keycloak credentials to `.env`:
   ```bash
   echo "KEYCLOAK_URL=https://auth.unicorncommander.ai" >> /home/deploy/Production/UC-1-Pro/services/ops-center/.env
   echo "KEYCLOAK_REALM=uchub" >> .env
   echo "KEYCLOAK_ADMIN_USER=admin" >> .env
   echo "KEYCLOAK_ADMIN_PASSWORD=your-admin-password" >> .env
   ```

2. Restart Ops-Center:
   ```bash
   docker restart unicorn-ops-center
   ```

## Security Considerations

### Authentication vs Authorization

- **OAuth2 Proxy**: Handles authentication (WHO are you?)
- **Tier Check**: Handles authorization (WHAT can you do?)

Both layers are required for proper access control.

### Fail-Safe Behavior

If Keycloak is unavailable:
- Development mode: Fails open (allows access)
- Production mode: Fails closed (denies access)

Controlled by `KEYCLOAK_AVAILABLE` flag in code.

### Bypass Prevention

- Tier check runs on every request (no caching)
- Headers are validated to come from OAuth2 Proxy
- Traefik enforces middleware chain order
- Cannot access tier-check endpoint directly from outside

## Performance

### Caching Strategy

Currently **no caching** to ensure real-time tier enforcement. Future optimization:

1. **Redis cache**: Cache tier lookups for 60 seconds
2. **In-memory cache**: Keep recent tier checks in memory
3. **Batch lookups**: Query multiple users at once

### Latency

- OAuth2 Proxy: ~10-20ms
- Tier Check: ~50-100ms (Keycloak query)
- Total overhead: ~60-120ms per request

Acceptable for dashboard/billing access (not API-intensive operations).

## Future Enhancements

### Planned Features

1. **Usage-based limits**: Check API call quotas in tier check
2. **Time-based access**: Grant temporary tier upgrades
3. **Team-based tiers**: Enterprise tier shared across team members
4. **Tier analytics**: Track tier upgrade conversion rates
5. **A/B testing**: Test different tier requirements
6. **Grace periods**: Allow access for X days after tier downgrade

### Integration with Lago Webhooks

When subscription changes in Lago:
1. Webhook fires to Ops-Center
2. Keycloak attributes updated
3. Next tier check uses new tier (immediate enforcement)

No cache invalidation needed since we don't cache.

## Testing Checklist

- [ ] Health endpoint returns 200 OK
- [ ] Billing tier check requires Professional+ tier
- [ ] Admin tier check requires Enterprise tier
- [ ] BYOK tier check requires Starter+ tier
- [ ] 401 returned when no email header present
- [ ] 403 returned when tier insufficient
- [ ] 200 returned when tier meets requirement
- [ ] Response headers include X-User-Tier
- [ ] Traefik correctly chains middlewares
- [ ] OAuth2 Proxy headers passed correctly
- [ ] Keycloak tier lookup works
- [ ] Logs show tier check attempts

## Documentation References

- **Traefik ForwardAuth**: https://doc.traefik.io/traefik/middlewares/http/forwardauth/
- **OAuth2 Proxy**: https://oauth2-proxy.github.io/oauth2-proxy/
- **Keycloak Admin API**: https://www.keycloak.org/docs-api/latest/rest-api/
- **UC-1 Pro Billing System**: `/home/deploy/Production/UC-1-Pro/docs/BILLING-SYSTEM-COMPLETE.md`

## Support

For issues:
1. Check logs: `docker logs unicorn-ops-center | grep "Tier check"`
2. Verify Keycloak attributes: Keycloak Admin UI → Users → {user} → Attributes
3. Test endpoint manually: `curl http://localhost:8084/api/v1/tier-check/health`
4. Review this documentation

---

**Status**: ✅ **Tier Check Middleware Fully Implemented and Ready for Deployment**
