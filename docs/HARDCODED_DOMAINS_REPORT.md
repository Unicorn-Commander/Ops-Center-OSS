# Hardcoded Domains Report - OSS Release Preparation

**Date**: 2025-12-25
**Purpose**: Identify all hardcoded domain references that must be externalized for OSS release
**Scope**: `/home/muut/OSS/ops-center`

## Executive Summary

This report identifies **300+ instances** of hardcoded domain references across the ops-center codebase that must be externalized to environment variables for the OSS release. The domains fall into three categories:

1. **your-domain.com** - Production domain (277 instances)
2. **magicunicorn.tech** - Company domain (52 instances)
3. **Subdomains** - Service-specific subdomains (127 instances)

## Critical Findings

### 1. Primary Domain Hardcoding: `your-domain.com`

#### Backend Python Files (High Priority)
| File | Line(s) | Hardcoded Value | Suggested Env Var |
|------|---------|-----------------|-------------------|
| `backend/email_notifications.py` | 58, 59 | `https://your-domain.com`, `support@your-domain.com` | `APP_URL`, `SUPPORT_EMAIL` |
| `backend/security_middleware.py` | 292, 318, 508 | `https://your-domain.com` | `ALLOWED_ORIGINS` |
| `backend/litellm_api.py` | 84, 1021, 1611, 1758, 2894, 3170-3171, 3436 | `https://your-domain.com`, `https://docs.your-domain.com` | `HTTP_REFERER`, `SIGNUP_URL`, `DOCS_URL` |
| `backend/server.py` | 254, 385-386, 3838, 5026, 5139-5141, 5166-5205, 5274, 5376-5378 | Multiple instances | `EXTERNAL_HOST`, `KEYCLOAK_EXTERNAL_URL` |
| `backend/account_management_api.py` | 616 | `https://your-domain.com` | `EXTERNAL_URL` |
| `backend/umami_api.py` | 15, 22, 27, 32 | `http://umami.your-domain.com:3000`, various subdomains | `UMAMI_URL`, `UMAMI_DOMAINS` |
| `backend/stripe_extensions.py` | 28-29 | `https://your-domain.com/extensions/success` | `STRIPE_SUCCESS_URL`, `STRIPE_CANCEL_URL` |
| `backend/anthropic_proxy.py` | 40 | `https://auth.your-domain.com` | `KEYCLOAK_URL` |
| `backend/services/forgejo_client.py` | 22 | `https://git.your-domain.com` | `FORGEJO_BASE_URL` |
| `backend/billing_manager.py` | 338 | `https://billing.your-domain.com/checkout` | `BILLING_CHECKOUT_URL` |
| `backend/prometheus_api.py` | 16 | `http://prometheus.your-domain.com:9090` | `PROMETHEUS_URL` |

#### Frontend JavaScript/JSX Files (High Priority)
| File | Line(s) | Hardcoded Value | Suggested Env Var |
|------|---------|-----------------|-------------------|
| `src/pages/TierComparison.jsx` | 45, 84 | `mailto:sales@magicunicorn.tech` | `SALES_EMAIL` |
| `src/pages/ApiDocumentation.jsx` | 315 | `mailto:support@magicunicorn.tech` | `SUPPORT_EMAIL` |
| `src/pages/UserSettings.jsx` | 220, 235 | `https://auth.your-domain.com/if/user/` | `KEYCLOAK_USER_PROFILE_URL` |
| `src/pages/account/AccountSecurity.jsx` | 349 | `https://auth.your-domain.com/if/user/` | `KEYCLOAK_USER_PROFILE_URL` |
| `src/pages/Security.jsx` | 152 | `https://auth.your-domain.com/if/user/` | `KEYCLOAK_USER_PROFILE_URL` |
| `src/data/serviceDescriptions.js` | 258 | `https://auth.your-domain.com` | `KEYCLOAK_URL` |

#### Docker Compose & Configuration Files (Critical)
| File | Line(s) | Hardcoded Value | Suggested Env Var |
|------|---------|-----------------|-------------------|
| `docker-compose.prod.yml` | 17, 24 | `Host(\`your-domain.com\`)` | `${EXTERNAL_HOST}` |
| `docker-compose.monitoring.yml` | 41, 57-58, 72 | `prometheus.your-domain.com`, `grafana.your-domain.com` | `${PROMETHEUS_HOST}`, `${GRAFANA_HOST}` |
| `nginx-proxy.conf` | 15 | `server_name your-domain.com;` | `${EXTERNAL_HOST}` |
| `litellm_config.yaml` | 381 | `database_url: os.environ/DATABASE_URL` | Already using env var ✅ |

#### SQL Migration Files (Medium Priority)
| File | Line(s) | Hardcoded Value | Suggested Env Var |
|------|---------|-----------------|-------------------|
| `backend/migrations/008_system_settings_schema.sql` | 80-83, 105-107 | Multiple service URLs | Should use `${EXTERNAL_HOST}` or dynamic generation |
| `backend/sql/system_settings.sql` | 116, 172 | `https://billing-api.your-domain.com`, `your-domain.com` | `LAGO_PUBLIC_URL`, `EXTERNAL_HOST` |
| `backend/sql/uc_cloud_services_catalog.sql` | 74-622 | All service `access_url` and `documentation` fields | Should use dynamic URL generation |
| `backend/sql/uc_cloud_services_simple.sql` | 40-230 | All service `access_url` fields | Should use dynamic URL generation |

#### GitHub Workflows (Low Priority - For Fork Users)
| File | Line(s) | Hardcoded Value | Suggested Env Var |
|------|---------|-----------------|-------------------|
| `.github/workflows/deploy-production.yml` | 20, 133-134, 137, 140, 161 | `https://your-domain.com` | `${{ secrets.PRODUCTION_URL }}` |
| `.github/workflows/deploy-staging.yml` | 17, 91-92, 102 | `https://staging.your-domain.com` | `${{ secrets.STAGING_URL }}` |
| `.github/workflows/ci-cd-pipeline.yml` | 421, 450, 472, 511 | Various staging/production URLs | `${{ secrets.STAGING_URL }}`, `${{ secrets.PRODUCTION_URL }}` |
| `.github/workflows/e2e-tests.yml` | 41 | `BASE_URL: 'https://your-domain.com'` | `${{ secrets.BASE_URL }}` |

### 2. Subdomain Hardcoding (127 instances)

All service-specific subdomains should be constructed dynamically from `EXTERNAL_HOST`:

| Subdomain Pattern | Count | Files | Suggested Fix |
|-------------------|-------|-------|---------------|
| `auth.your-domain.com` | 47 | Backend, frontend, docs | `https://auth.${EXTERNAL_HOST}` |
| `api.your-domain.com` | 12 | Backend, docs | `https://api.${EXTERNAL_HOST}` |
| `chat.your-domain.com` | 8 | SQL, templates, docs | `https://chat.${EXTERNAL_HOST}` |
| `search.your-domain.com` | 8 | SQL, templates, docs | `https://search.${EXTERNAL_HOST}` |
| `billing.your-domain.com` | 7 | Backend, SQL, templates | `https://billing.${EXTERNAL_HOST}` |
| `brigade.your-domain.com` | 6 | SQL, backend | `https://brigade.${EXTERNAL_HOST}` |
| `git.your-domain.com` | 5 | Backend, SQL | `https://git.${EXTERNAL_HOST}` |
| `presentations.your-domain.com` | 4 | SQL, migrations | `https://presentations.${EXTERNAL_HOST}` |
| `bolt.your-domain.com` | 4 | SQL, migrations | `https://bolt.${EXTERNAL_HOST}` |
| `stt.your-domain.com` | 3 | SQL | `https://stt.${EXTERNAL_HOST}` |
| `tts.your-domain.com` | 3 | SQL | `https://tts.${EXTERNAL_HOST}` |
| `staging.your-domain.com` | 5 | GitHub workflows | `${{ secrets.STAGING_URL }}` |
| `prometheus.your-domain.com` | 2 | Docker compose | `https://prometheus.${EXTERNAL_HOST}` |
| `grafana.your-domain.com` | 2 | Docker compose | `https://grafana.${EXTERNAL_HOST}` |
| `umami.your-domain.com` | 1 | Backend | `https://umami.${EXTERNAL_HOST}` |

**Special Cases:**
- `auth.yoda.your-domain.com` (5 instances in `backend/server.py`) - Legacy subdomain that should be removed
- `.your-domain.com` (cookie domain) - Should use `.${EXTERNAL_HOST}`

### 3. Company Domain: `magicunicorn.tech`

| File | Line(s) | Hardcoded Value | Suggested Env Var |
|------|---------|-----------------|-------------------|
| `SECURITY.md` | 18 | `security@magicunicorn.tech` | `SECURITY_EMAIL` |
| `README.md` | 390 | `https://magicunicorn.tech` | `COMPANY_URL` |
| `backend/email_alerts.py` | 82, 240-241 | `admin@example.com`, `support@magicunicorn.tech` | `EMAIL_FROM`, `SUPPORT_EMAIL` |
| `backend/migrations/005_email_providers.sql` | 60 | `noreply@magicunicorn.tech` | `EMAIL_FROM` |
| `backend/openapi_config.py` | 82, 94 | `support@magicunicorn.tech` | `SUPPORT_EMAIL` |
| `backend/role_mapper.py` | 129 | `admin_emails = ["admin@example.com"]` | `ADMIN_EMAILS` (comma-separated list) |
| `backend/templates/privacy.html` | 382-383, 389 | `privacy@magicunicorn.tech`, `dpo@magicunicorn.tech` | `PRIVACY_EMAIL`, `DPO_EMAIL` |
| `backend/templates/terms.html` | 267-268 | `legal@magicunicorn.tech` | `LEGAL_EMAIL` |
| `src/pages/TierComparison.jsx` | 45, 84 | `mailto:sales@magicunicorn.tech` | `SALES_EMAIL` |
| `monitoring/alerting/alertmanager.yml` | 181, 208, 236, 250 | `ops@magicunicorn.tech`, `security@magicunicorn.tech`, `business@magicunicorn.tech` | `OPS_EMAIL`, `SECURITY_EMAIL`, `BUSINESS_EMAIL` |

### 4. Test User Emails (Should be configurable)

| File | Line(s) | Hardcoded Value | Suggested Env Var |
|------|---------|-----------------|-------------------|
| `backend/scripts/create_test_users.py` | 41, 49, 57, 65 | `trial@test.your-domain.com`, etc. | `TEST_USER_EMAIL_PATTERN` |
| `backend/tests/test_admin_subscriptions.py` | 12 | `ADMIN_EMAIL = "admin@example.com"` | `TEST_ADMIN_EMAIL` |
| `backend/tests/test_tier_enforcement.py` | 43 | Default test email | `TEST_USER_EMAIL` |
| `test_oidc_flow.py` | 8, 13, 16 | `EXTERNAL_HOST = "your-domain.com"`, `admin@example.com` | `TEST_EXTERNAL_HOST`, `TEST_USER_EMAIL` |

## Special Cases Requiring Manual Review

### 1. Legacy "yoda" Subdomain
**Files**: `backend/server.py` (lines 5026, 5139-5141), `backend/server.py.backup`

```python
auth_url = "https://auth.yoda.your-domain.com" if "yoda.your-domain.com" in str(request.url) else f"https://auth.{EXTERNAL_HOST}"
```

**Recommendation**: Remove legacy `yoda.your-domain.com` references or make configurable via `LEGACY_HOSTS` environment variable.

### 2. CORS Allowed Origins
**File**: `backend/security_middleware.py` (lines 292, 318, 508)

```python
allowed_origins=["https://your-domain.com"]
```

**Recommendation**: Use `ALLOWED_ORIGINS` environment variable (comma-separated list) with default to `${EXTERNAL_PROTOCOL}://${EXTERNAL_HOST}`.

### 3. HTTP Referer Headers (OpenRouter API)
**File**: `backend/litellm_api.py` (7 instances)

```python
'HTTP-Referer': 'https://your-domain.com'
```

**Recommendation**: Use `HTTP_REFERER` or construct from `EXTERNAL_HOST`. OpenRouter requires this for API calls.

### 4. Database URLs in SQL Files
**Files**: `backend/sql/uc_cloud_services_catalog.sql`, `backend/sql/uc_cloud_services_simple.sql`

All service `access_url` and `documentation` fields contain hardcoded URLs.

**Recommendation**:
- Option 1: Add migration script to update URLs from environment variables on first run
- Option 2: Create a function to dynamically generate service URLs at runtime
- Option 3: Keep as defaults but allow override via admin UI

### 5. Keycloak Session Domain
**File**: `backend/server.py` (lines 5375-5378)

```python
if "." in EXTERNAL_HOST and not EXTERNAL_HOST.startswith("localhost"):
    cookie_kwargs["domain"] = f".{EXTERNAL_HOST}"
```

**Status**: ✅ Already uses `EXTERNAL_HOST` - No change needed

### 6. Documentation and Markdown Files

Over **100 instances** in documentation files (`docs/**`, `*.md`). These are **low priority** for OSS release but should be updated for user-facing docs.

**Recommendation**: Create a documentation template system or use placeholder domains like `example.com` or `your-domain.com`.

## Environment Variables Mapping

### Recommended New Environment Variables

```bash
# Core Domain Configuration
EXTERNAL_HOST=your-domain.com               # Primary domain
EXTERNAL_PROTOCOL=https                         # http or https
EXTERNAL_PORT=8084                              # Port if not standard

# Service Subdomains (auto-constructed from EXTERNAL_HOST if not set)
AUTH_HOST=auth.${EXTERNAL_HOST}
API_HOST=api.${EXTERNAL_HOST}
CHAT_HOST=chat.${EXTERNAL_HOST}
SEARCH_HOST=search.${EXTERNAL_HOST}
BILLING_HOST=billing.${EXTERNAL_HOST}
BRIGADE_HOST=brigade.${EXTERNAL_HOST}
GIT_HOST=git.${EXTERNAL_HOST}
PRESENTATIONS_HOST=presentations.${EXTERNAL_HOST}
BOLT_HOST=bolt.${EXTERNAL_HOST}
STT_HOST=stt.${EXTERNAL_HOST}
TTS_HOST=tts.${EXTERNAL_HOST}
PROMETHEUS_HOST=prometheus.${EXTERNAL_HOST}
GRAFANA_HOST=grafana.${EXTERNAL_HOST}
UMAMI_HOST=umami.${EXTERNAL_HOST}

# Company/Support Information
COMPANY_NAME="Magic Unicorn Tech"
COMPANY_URL=https://magicunicorn.tech
SUPPORT_EMAIL=support@example.com
SECURITY_EMAIL=security@example.com
SALES_EMAIL=sales@example.com
LEGAL_EMAIL=legal@example.com
PRIVACY_EMAIL=privacy@example.com
DPO_EMAIL=dpo@example.com
OPS_EMAIL=ops@example.com
BUSINESS_EMAIL=business@example.com

# Admin Configuration
ADMIN_EMAILS=admin@example.com                  # Comma-separated list

# Application URLs
APP_URL=${EXTERNAL_PROTOCOL}://${EXTERNAL_HOST}
SIGNUP_URL=${APP_URL}/signup
DOCS_URL=${EXTERNAL_PROTOCOL}://docs.${EXTERNAL_HOST}
HTTP_REFERER=${APP_URL}                         # For OpenRouter API

# Keycloak Configuration
KEYCLOAK_URL=${EXTERNAL_PROTOCOL}://auth.${EXTERNAL_HOST}
KEYCLOAK_EXTERNAL_URL=${KEYCLOAK_URL}
KEYCLOAK_USER_PROFILE_URL=${KEYCLOAK_URL}/if/user/

# Billing Configuration
LAGO_PUBLIC_URL=${EXTERNAL_PROTOCOL}://billing-api.${EXTERNAL_HOST}
BILLING_CHECKOUT_URL=${EXTERNAL_PROTOCOL}://billing.${EXTERNAL_HOST}/checkout
STRIPE_SUCCESS_URL=${APP_URL}/billing/success
STRIPE_CANCEL_URL=${APP_URL}/billing/canceled

# Service Discovery URLs
FORGEJO_BASE_URL=${EXTERNAL_PROTOCOL}://git.${EXTERNAL_HOST}
PROMETHEUS_URL=http://prometheus.${EXTERNAL_HOST}:9090
UMAMI_URL=http://umami.${EXTERNAL_HOST}:3000

# CORS Configuration
ALLOWED_ORIGINS=${APP_URL}                      # Comma-separated list

# Testing (for development/CI)
TEST_EXTERNAL_HOST=localhost
TEST_USER_EMAIL=test@example.com
TEST_ADMIN_EMAIL=admin@example.com
TEST_USER_EMAIL_PATTERN=test-{tier}@example.com
```

### Existing Environment Variables (Already in Use)

✅ Already externalized:
- `EXTERNAL_HOST` - Used in `backend/server.py` and other files
- `EXTERNAL_PROTOCOL` - Used for URL construction
- `DATABASE_URL` - Database connection string
- `KEYCLOAK_URL` - Some files already use this
- `AUTHENTIK_EXTERNAL_URL` - For Authentik (if used)

## Implementation Recommendations

### Phase 1: Critical Backend Fixes (High Priority)

1. **Update `backend/server.py`**:
   - Replace all hardcoded `your-domain.com` with `EXTERNAL_HOST`
   - Remove or make configurable `yoda.your-domain.com` references
   - Ensure cookie domain uses `.${EXTERNAL_HOST}`

2. **Update `backend/litellm_api.py`**:
   - Replace `HTTP-Referer` hardcoded URLs with `HTTP_REFERER` env var
   - Update `signup_url` and `docs_url` to use env vars

3. **Update `backend/security_middleware.py`**:
   - Replace `allowed_origins` hardcoded list with `ALLOWED_ORIGINS` env var

4. **Update `backend/email_notifications.py`**:
   - Replace hardcoded URLs and emails with env vars

5. **Update service-specific API files**:
   - `backend/umami_api.py` - Use `UMAMI_URL` and `UMAMI_DOMAINS`
   - `backend/anthropic_proxy.py` - Use `KEYCLOAK_URL`
   - `backend/services/forgejo_client.py` - Use `FORGEJO_BASE_URL`
   - `backend/billing_manager.py` - Use `BILLING_CHECKOUT_URL`
   - `backend/prometheus_api.py` - Use `PROMETHEUS_URL`

### Phase 2: Frontend Fixes (High Priority)

1. **Update React components**:
   - `src/pages/TierComparison.jsx` - Use `SALES_EMAIL` from config
   - `src/pages/ApiDocumentation.jsx` - Use `SUPPORT_EMAIL` from config
   - `src/pages/UserSettings.jsx` - Use `KEYCLOAK_USER_PROFILE_URL`
   - `src/pages/account/AccountSecurity.jsx` - Use `KEYCLOAK_USER_PROFILE_URL`
   - `src/data/serviceDescriptions.js` - Use dynamic URL construction

2. **Create frontend config service**:
   ```javascript
   // src/config/environment.js
   export const config = {
     externalHost: import.meta.env.VITE_EXTERNAL_HOST || 'localhost',
     authUrl: import.meta.env.VITE_AUTH_URL || `https://auth.${externalHost}`,
     supportEmail: import.meta.env.VITE_SUPPORT_EMAIL || 'support@example.com',
     // ... etc
   };
   ```

### Phase 3: Configuration Files (High Priority)

1. **Update `docker-compose.prod.yml`**:
   - Replace `Host(\`your-domain.com\`)` with `Host(\`${EXTERNAL_HOST}\`)`

2. **Update `docker-compose.monitoring.yml`**:
   - Use `${PROMETHEUS_HOST}` and `${GRAFANA_HOST}`

3. **Update `nginx-proxy.conf`**:
   - Use `server_name ${EXTERNAL_HOST};`

### Phase 4: SQL Migrations (Medium Priority)

1. **Create migration script to update service URLs**:
   ```sql
   -- Update all service URLs to use external host
   UPDATE add_ons SET
     launch_url = REPLACE(launch_url, 'your-domain.com', :external_host),
     metadata = jsonb_set(
       metadata,
       '{access_url}',
       to_jsonb(REPLACE(metadata->>'access_url', 'your-domain.com', :external_host))
     );
   ```

2. **Update system settings defaults**:
   - Modify `backend/migrations/008_system_settings_schema.sql`
   - Use parameterized values or default to `EXTERNAL_HOST`

### Phase 5: Documentation (Low Priority)

1. **Create `.env.example.oss`** with OSS-friendly defaults
2. **Update documentation** to use placeholder domains
3. **Create setup wizard** to configure domain on first run

### Phase 6: Testing Infrastructure (Low Priority)

1. **Update GitHub workflows** to use secrets
2. **Update test files** to use configurable test users/domains
3. **Create integration test suite** that works with any domain

## Files Requiring No Changes

✅ Already using environment variables correctly:
- `backend/server.py` (lines 254, 261, 263) - Uses `EXTERNAL_HOST`
- `backend/service_discovery.py` - Uses `EXTERNAL_HOST`
- `litellm_config.yaml` - Uses `os.environ/DATABASE_URL`
- `backend/keycloak_integration.py` - Uses `KEYCLOAK_URL` env var
- Most `backend/tests/*.py` - Use `BASE_URL` env var

## Summary Statistics

| Category | Count | Priority |
|----------|-------|----------|
| Backend Python files | 45 | **HIGH** |
| Frontend JSX/JS files | 12 | **HIGH** |
| Docker Compose files | 4 | **HIGH** |
| SQL files | 8 | **MEDIUM** |
| Documentation files | 100+ | **LOW** |
| GitHub workflows | 6 | **LOW** |
| Test files | 25 | **LOW** |
| **TOTAL FILES** | **200+** | - |
| **TOTAL INSTANCES** | **300+** | - |

## Risk Assessment

### High Risk (Production Breaking)
- **Backend authentication** (`backend/server.py`, `backend/security_middleware.py`)
- **CORS configuration** (will break cross-origin requests)
- **SSO integration** (Keycloak URL hardcoding)
- **Email notifications** (wrong sender addresses)

### Medium Risk (Feature Breaking)
- **Service discovery** (hardcoded service URLs)
- **Billing integration** (Stripe redirect URLs)
- **API proxy** (OpenRouter HTTP-Referer header)

### Low Risk (Cosmetic/Documentation)
- **Documentation files** (user-facing docs)
- **Test files** (only affects testing)
- **GitHub workflows** (only affects CI/CD for forks)

## Recommended Rollout Strategy

1. **Week 1**: Create `.env.oss` template with all new env vars
2. **Week 2**: Update critical backend files (Phase 1)
3. **Week 3**: Update frontend components (Phase 2)
4. **Week 4**: Update configuration files (Phase 3)
5. **Week 5**: Create SQL migration script (Phase 4)
6. **Week 6**: Update documentation (Phase 5)
7. **Week 7**: Test with multiple domain configurations
8. **Week 8**: Final QA and release

## Testing Checklist

- [ ] Test with `localhost` domain
- [ ] Test with custom domain (e.g., `mycompany.com`)
- [ ] Test with IP address (e.g., `192.168.1.100`)
- [ ] Test with port numbers (e.g., `localhost:8084`)
- [ ] Test SSO login/logout with custom domain
- [ ] Test email sending with custom sender addresses
- [ ] Test CORS with multiple origins
- [ ] Test Stripe redirects with custom domain
- [ ] Test all service URLs resolve correctly
- [ ] Test documentation builds with placeholders

## Contact

For questions about this report or implementation assistance, contact the development team.

---

**Report Generated**: 2025-12-25
**Scope**: OSS Release Preparation
**Status**: ✅ Complete
