# Ops-Center: What Works Without API Keys

**Last Updated**: October 26, 2025

## TL;DR - What Should Work Right Now

✅ **Works with Mock Data (No API Keys Required)**:
- User Management (Keycloak SSO - already configured)
- Billing Dashboard (Lago billing - already configured)
- Permissions Management (in-memory RBAC)
- LLM Usage Analytics (mock data)
- System Monitoring
- Service Status
- Organization Management
- Analytics & Reports

⚠️ **Requires External Service Access**:
- Model Management (needs HuggingFace API access)
- LLM Providers (needs provider API keys: OpenAI, Anthropic, etc.)
- Traefik Services Detail (needs Traefik API endpoint configured)
- Cloudflare DNS (needs Cloudflare API token - already in .env.auth)

---

## Detailed Breakdown by Section

### ✅ Fully Functional (No Additional Keys Needed)

#### 1. Dashboard
- **Status**: WORKING
- **Requirements**: Keycloak SSO authentication (already configured)
- **What You See**: System overview, service status, quick stats
- **Data Source**: Internal APIs, Docker stats, system metrics

#### 2. User Management
- **Status**: WORKING
- **Requirements**: Keycloak uchub realm (already configured)
- **What You Can Do**:
  - List all users
  - View user details
  - Create/edit/delete users
  - Assign roles
  - Manage API keys
  - Bulk operations (CSV import/export)
- **Data Source**: Keycloak REST API at `http://uchub-keycloak:8080`

#### 3. Billing Dashboard
- **Status**: WORKING
- **Requirements**: Lago billing system (already configured)
- **What You Can Do**:
  - View revenue analytics (MRR, ARR)
  - Manage subscriptions
  - View invoices
  - Track payments
- **Data Source**: Lago REST API at `http://unicorn-lago-api:3000`
- **API Key**: Already configured in `.env.auth`

#### 4. Permissions Management
- **Status**: WORKING
- **Requirements**: None (in-memory)
- **What You Can Do**:
  - View permission matrix
  - Manage roles (admin, moderator, developer, analyst, viewer)
  - Grant/revoke permissions
  - View role hierarchy
- **Data Source**: In-memory RBAC system
- **Future**: Will migrate to PostgreSQL

#### 5. LLM Usage Analytics
- **Status**: WORKING (Mock Data)
- **Requirements**: None currently
- **What You Can Do**:
  - View usage overview (calls, tokens, costs)
  - Break down by model
  - Break down by user
  - Cost analysis
- **Data Source**: Mock data (realistic simulated usage)
- **Future**: Will connect to actual usage tracking database

#### 6. Organizations
- **Status**: WORKING
- **Requirements**: PostgreSQL unicorn_db (already configured)
- **What You Can Do**:
  - Create/manage organizations
  - Invite members
  - Manage roles
  - View organization billing
- **Data Source**: PostgreSQL `organizations` table

#### 7. System Monitoring
- **Status**: WORKING
- **Requirements**: Docker access (already configured)
- **What You Can Do**:
  - View system resources (CPU, RAM, Disk)
  - Monitor services
  - View logs
  - Check network status
- **Data Source**: Docker API, psutil, system commands

#### 8. Services Management
- **Status**: WORKING
- **Requirements**: Docker access (already configured)
- **What You Can Do**:
  - Start/stop/restart services
  - View service status
  - Monitor resource usage
- **Data Source**: Docker API

#### 9. Storage & Backup
- **Status**: WORKING
- **Requirements**: File system access (already configured)
- **What You Can Do**:
  - View storage usage
  - Create backups
  - Restore backups
  - Configure backup schedules
- **Data Source**: File system, Restic

---

### ⚠️ Requires Configuration or API Keys

#### 10. Model Management
- **Status**: PARTIAL - HuggingFace search works, local management needs vLLM
- **Requirements**:
  - Internet access (for HuggingFace API) ✅ Should work
  - vLLM service running (for local model management)
- **What Works**:
  - ✅ Search HuggingFace for models (no key needed)
  - ✅ Browse model categories
  - ✅ View popular models
- **What Needs vLLM**:
  - ⚠️ List locally installed models
  - ⚠️ Download models
  - ⚠️ Activate models
  - ⚠️ Delete models
- **How to Enable**:
  - Ensure vLLM service is running
  - Verify vLLM API accessible at configured endpoint

#### 11. LLM Provider Settings
- **Status**: PARTIAL - Interface works, testing requires keys
- **Requirements**:
  - **OpenAI**: API key from https://platform.openai.com
  - **Anthropic**: API key from https://console.anthropic.com
  - **Google**: API key from https://ai.google.dev
  - **Cohere**: API key from https://dashboard.cohere.com
  - **Together AI**: API key from https://api.together.xyz
  - **Replicate**: API key from https://replicate.com
- **What Works Without Keys**:
  - ✅ View available providers
  - ✅ Configure provider settings (UI)
  - ✅ Add/edit/delete provider configs
- **What Needs Keys**:
  - ⚠️ Test provider connection
  - ⚠️ Fetch available models from provider
  - ⚠️ Actually use the provider for inference

#### 12. Traefik Services Detail
- **Status**: CODE COMPLETE - Needs Traefik API Access
- **Requirements**:
  - Traefik HTTP API endpoint accessible to ops-center
- **Current Issue**:
  - Traefik API not exposed to ops-center container
- **What Will Work After Config**:
  - Service health checks
  - Metrics collection
  - Service reload
  - Load balancer stats
- **How to Enable**:
  ```yaml
  # Add to Traefik config
  api:
    insecure: true  # Or configure TLS
    dashboard: true
  ```
  - Or add environment variable: `TRAEFIK_API_URL=http://traefik:8080`

#### 13. Cloudflare DNS
- **Status**: WORKING
- **Requirements**: Cloudflare API token (already in `.env.auth`)
- **API Token**: `your-cloudflare-api-token`
- **What You Can Do**:
  - Manage DNS records
  - View zones
  - Update configurations
- **Security Note**: Token should be rotated before production use

---

## Authentication Flow

### How Login Works (No Additional Setup Needed)

1. **User visits**: https://unicorncommander.ai
2. **Redirected to**: Keycloak SSO login page
3. **Login options**:
   - ✅ **Google** - SSO via Google account
   - ✅ **GitHub** - SSO via GitHub account
   - ✅ **Microsoft** - SSO via Microsoft account
   - ✅ **Email/Password** - Direct Keycloak authentication
4. **After login**: Redirected back to Ops-Center dashboard
5. **Session**: Stored in Redis, 2-hour TTL

### Test Users (Keycloak)

You can test with these users (if they exist in your Keycloak):
- **Admin**: `admin@example.com` (full access)
- Or create new users via Keycloak admin console

---

## What Pages Should Work Right Now

### ✅ Should Load and Function

| Page | Status | Requirements |
|------|--------|--------------|
| Dashboard | ✅ WORKING | Keycloak auth |
| User Management | ✅ WORKING | Keycloak auth |
| User Detail | ✅ WORKING | Keycloak auth |
| Billing Dashboard | ✅ WORKING | Keycloak + Lago |
| Organizations | ✅ WORKING | PostgreSQL |
| Services | ✅ WORKING | Docker API |
| System Monitoring | ✅ WORKING | Docker + psutil |
| Permissions | ✅ WORKING | In-memory |
| LLM Usage | ✅ WORKING | Mock data |
| Analytics | ✅ WORKING | Various sources |
| Storage & Backup | ✅ WORKING | File system |
| Subscription Management | ✅ WORKING | Lago billing |
| Account Settings | ✅ WORKING | Keycloak |

### ⚠️ Partial Functionality

| Page | What Works | What Needs Keys |
|------|-----------|----------------|
| Model Management | HuggingFace search | Local model ops (vLLM) |
| LLM Providers | UI, config management | Connection testing |
| Traefik Services | UI | Service health/metrics |
| Cloudflare DNS | Everything | Nothing (key in config) |

### ❌ Not Yet Implemented

(None - all planned pages have backend APIs)

---

## Troubleshooting

### Issue: "TypeError: undefined is not an object"
**Solution**: ✅ FIXED in latest build - added null checks to tier handling

### Issue: Invoice page crashes
**Solution**: ✅ FIXED - invoice tier rendering now handles undefined gracefully

### Issue: Traefik navigation confusing
**Solution**: ✅ FIXED - moved "Local Users" to "Users & Organizations" section

### Issue: "Connection failed" on Traefik Services page
**Solution**: Configure Traefik to expose API endpoint (see above)

### Issue: Can't test LLM provider connections
**Solution**: Add provider API keys via "LLM Providers" page, then test

### Issue: No local models showing
**Solution**: Ensure vLLM service is running and accessible

---

## API Keys Reference

### Already Configured (In `.env.auth`)

```bash
# Keycloak SSO
KEYCLOAK_URL=http://uchub-keycloak:8080
KEYCLOAK_REALM=uchub
KEYCLOAK_CLIENT_ID=ops-center
KEYCLOAK_CLIENT_SECRET=your-keycloak-client-secret

# Lago Billing
LAGO_API_URL=http://unicorn-lago-api:3000
LAGO_API_KEY=your-lago-api-key

# Cloudflare DNS
CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
```

### Optional (Configure via UI)

- **OpenAI API Key**: Add via LLM Providers page
- **Anthropic API Key**: Add via LLM Providers page
- **Google AI API Key**: Add via LLM Providers page
- **Cohere API Key**: Add via LLM Providers page
- etc.

---

## Summary

**You should be able to use 95% of Ops-Center features without adding any API keys.**

The only things that won't work are:
1. Testing LLM provider connections (needs provider API keys)
2. Downloading new models to vLLM (needs vLLM service)
3. Traefik service health checks (needs Traefik API config)

Everything else - user management, billing, permissions, analytics, services, monitoring - all works out of the box with the existing configuration.

**Just login via Keycloak SSO and start exploring!** 🚀

---

**Questions?**
- Check the error console in browser (F12)
- Check backend logs: `docker logs ops-center-direct`
- Check Keycloak: https://auth.unicorncommander.ai/admin
- Check Lago: https://billing.unicorncommander.ai

