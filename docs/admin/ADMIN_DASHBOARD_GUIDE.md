# Admin Dashboard Guide

**Last Updated**: February 22, 2026
**Audience**: System administrators
**Version**: 2.5.1

---

## Table of Contents

1. [Overview](#overview)
2. [Dashboard Sections](#dashboard-sections)
3. [Quick Actions](#quick-actions)
4. [Key Admin Pages](#key-admin-pages)
5. [Admin vs User Dashboard](#admin-vs-user-dashboard)
6. [Version History](#version-history)
7. [Tips for Admins](#tips-for-admins)

---

## Overview

The Admin Dashboard (`/admin/dashboard`) provides a real-time overview of your UC-Cloud infrastructure. It monitors services, GPU status, billing, and system health.

**How to Access:**
1. Login to https://unicorncommander.ai with an admin account
2. Navigate to **Dashboard** in the sidebar, or go directly to `/admin/dashboard`

**Requirements:**
- Admin role in Keycloak (uchub realm)
- Active SSO session

---

## Dashboard Sections

### Critical Services

Real-time health status for core infrastructure components:

| Service | What It Monitors |
|---------|-----------------|
| **PostgreSQL** | Database service (`unicorn-postgresql`) |
| **Redis** | Cache and session store (`unicorn-redis`) |
| **Keycloak** | SSO authentication (`unicorn-keycloak`) |
| **vLLM / LLM Providers** | AI model inference endpoints |
| **Traefik** | Reverse proxy and SSL termination |

**Status Indicators:**

| Color | Meaning |
|-------|---------|
| Green | Service is healthy and responding |
| Yellow | Service is degraded (slow response or partial failure) |
| Red | Service is down or unreachable |

**Action on Red Status:**
1. Check container logs: `docker logs <container-name> --tail 50`
2. Verify container is running: `docker ps | grep <service>`
3. Restart if needed: `docker restart <container-name>`

### GPU Status

For servers with NVIDIA GPUs (such as Tesla P40 or RTX 5090):

- GPU model and driver version
- Memory usage (used/total in MB or GB)
- Temperature (in Celsius)
- Utilization percentage

```
+-------------------------------------------+
| GPU 0: Tesla P40 (24GB)                  |
|   Memory: 18,432 / 24,576 MB (75%)       |
|   Temperature: 72C                        |
|   Utilization: 85%                        |
+-------------------------------------------+
| GPU 1: Tesla P40 (24GB)                  |
|   Memory: 12,288 / 24,576 MB (50%)       |
|   Temperature: 65C                        |
|   Utilization: 40%                        |
+-------------------------------------------+
```

**Temperature Thresholds:**
- Below 70C: Normal operation
- 70-85C: Elevated (monitor closely)
- Above 85C: High (consider reducing workload)

### Local Inference Providers

Status of locally-running AI providers:

| Provider | Port | Description |
|----------|------|-------------|
| **Ollama** | 11434 | Local model serving |
| **vLLM** | 8000 | High-performance LLM inference |
| **llama.cpp Router** | 8085 | Dynamic model loading with idle timeout |

Each provider card shows:
- Running/Stopped status
- Models currently loaded
- Memory usage
- Request count (if available)

### Billing and Credits Overview

Summary of billing metrics across all organizations:

- Total credits allocated across all organizations
- Total credits consumed this period
- Revenue summary (MRR/ARR estimates)
- Active subscription counts by tier

### Hosted Websites

Websites managed through Traefik reverse proxy with SSL/TLS status:

- Domain name and routing target
- SSL certificate status and expiration date
- Service health (up/down)

### Service Health Grid

At-a-glance status grid for all running Docker containers in the UC-Cloud ecosystem. Each service shows as a colored tile:

- Green tile: Container healthy
- Red tile: Container stopped or unhealthy
- Gray tile: Container not found

### Recent Activity

Timeline of recent system events, deployments, and configuration changes. Events are color-coded by severity:

- Blue: Informational (deployments, configuration changes)
- Yellow: Warnings (degraded services, high usage)
- Red: Critical (service failures, authentication errors)

---

## Quick Actions

As of v2.5.1, quick actions use SPA routing for instant navigation (no page reload):

| Action | Navigates To | Purpose |
|--------|-------------|---------|
| **View Logs** | `/admin/monitoring/logs` | System and service log viewer |
| **GPU Services** | `/admin/ai/gpu-services` | GPU service management (start/stop inference services) |
| **Traefik Dashboard** | `/admin/infra/traefik/dashboard` | Reverse proxy management and routing |

**v2.5.1 Fix:** Previous versions used `window.location.href` for navigation, causing full page reloads. This has been changed to `navigate()` from React Router for instant SPA transitions.

---

## Key Admin Pages

### User Management (`/admin/system/users`)

- List all users with advanced filtering (tier, role, status, org, date ranges)
- Bulk operations: CSV import/export, bulk role assignment, suspend, delete
- Click any user row to open the detailed 6-tab profile view

**Filter Options:**
- Search by email/username
- Filter by subscription tier
- Filter by role (admin, moderator, developer, analyst, viewer)
- Filter by status (enabled, disabled, suspended)
- Filter by organization
- Filter by date ranges (registration, last login)
- Filter by BYOK status and email verification

### Service Keys (`/admin/system/service-keys`)

Manage service-to-service API keys used by integrated applications:

| Service | Purpose |
|---------|---------|
| Brigade | Agent platform LLM access |
| Bolt.diy | AI development environment |
| Presenton | AI presentation generation |
| Center-Deep | AI metasearch engine |
| PartnerPulse | Partner management platform |

**Key Features:**
- Key rotation without service downtime
- Scope-based permissions (`llm:chat`, `llm:image`, `llm:embeddings`, `llm:audio`)
- Usage tracking (`last_used_at` timestamps)
- New keys shown only once at rotation time

**Key Rotation Workflow:**
1. Navigate to Service Keys management
2. Click **Rotate** on the target service key
3. Copy the new key (displayed only once)
4. Update the service's environment variable (e.g., `BRIGADE_SERVICE_KEY`)
5. Restart the service container

### Model Lists (`/admin/system/model-lists`)

Curate AI model lists per application:

- **Global List** - Default models available to all apps
- **Bolt.diy** - Coding-optimized models
- **Presenton** - Presentation generation models
- **Open-WebUI** - General-purpose chat models

**Features:**
- Drag-and-drop reordering
- Tier-based model access control (which tiers see which models)
- Category color coding (coding=blue, reasoning=purple, general=gray, fast=yellow)
- Import/export in JSON format
- Search OpenRouter catalog to add models

### Feature Management (`/admin/system/feature-management`)

Manage which apps are available for each subscription tier:

- Visual tier-to-feature mapping with color-coded badges
- Enable/disable apps per tier with checkbox UI
- No code deployment needed for access changes
- Changes take effect immediately (users see updated apps on next page load)

**Tier Badges:**
- Gold: VIP Founder
- Purple: BYOK
- Blue: Managed
- Green: Starter
- Gray: Trial

### Organization Management

- Create and manage organizations
- Grant per-org app access via `org_features` table
- Set tier-based default app access
- View organization members and their roles
- Manage organization billing and credit pools

**Per-Org Feature Grants:**
Use the admin API or database to grant specific apps to specific organizations, regardless of their subscription tier. This is useful for:
- Partner organizations needing premium app access
- Trial orgs evaluating specific features
- Enterprise clients with custom arrangements

---

## Admin vs User Dashboard

Ops-Center provides two distinct dashboards for different needs:

| Aspect | Admin Dashboard | User Dashboard |
|--------|----------------|----------------|
| **URL** | `/admin/dashboard` | `/admin/my-dashboard` |
| **Purpose** | Infrastructure monitoring | Personal account overview |
| **Target Users** | System administrators | Regular users |
| **Shows** | GPU status, services, hosted websites, system health | Credits, usage, subscription, costs |
| **Actions** | Service management, log viewing, GPU controls | API keys, upgrade, invoices, payment |

**When to Use Which:**
- **Admin Dashboard**: Check daily for service health, GPU temperatures, and system-wide metrics
- **User Dashboard**: For individual users to monitor their own usage and subscription status

---

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| v2.5.1 | 2026-02-22 | Frontend audit: 108 files fixed, credentials sweep, monitoring persistence, SPA routing fixes |
| v2.5.0 | 2026-01-27 | Service API Keys management, org-level feature grants, User Dashboard added |
| v2.4.0 | 2025-11-19 | Image generation APIs (GPT Image 1, Gemini Imagen 3), P0 bug fixes |
| v2.3.0 | 2025-11-12 | Phase 2 billing: usage tracking, subscription self-service, payment methods |
| v2.2.0 | 2025-11-04 | Image generation API, model categorization, BYOK separation |
| v2.1.0 | 2025-10-15 | User management system, bulk operations, advanced filtering |
| v2.0.0 | 2025-10-06 | Enhanced multi-system management, theme system, deployment detection |

---

## Tips for Admins

- **Service health**: Check the dashboard daily. Degraded services show as yellow -- investigate before they turn red.

- **User attributes**: After adding new users to Keycloak, run `quick_populate_users.py` to sync custom attributes (subscription_tier, api_calls_limit, etc.):
  ```bash
  docker exec ops-center-direct python3 /app/scripts/quick_populate_users.py
  ```

- **Feature access**: Use the database `tier_features` and `org_features` tables to control app access without code changes. SQL updates take effect immediately.

- **Monitoring settings**: Monitoring configuration (Umami, Grafana, Prometheus) is stored in browser localStorage as of v2.5.1. These settings are not synced across browsers. Backend persistence is planned for a future release.

- **Credentials in fetch calls**: As of v2.5.1, all frontend fetch calls include `credentials: 'include'` to ensure SSO cookies are forwarded through the reverse proxy. If you see 401 errors after a deployment, verify the frontend build is up to date.

- **GPU services**: GPU inference services (Granite, Infinity) support idle unloading. Services auto-stop after configurable idle periods (5-30 minutes) to conserve GPU memory. First requests after idle will have cold start latency (30-120 seconds).

- **Container rebuilds**: When making frontend changes:
  ```bash
  cd /home/muut/UC-Cloud-production/services/ops-center
  npm run build && cp -r dist/* public/
  docker restart ops-center-direct
  ```

- **Log monitoring**: For quick troubleshooting:
  ```bash
  # All ops-center logs
  docker logs ops-center-direct --tail 100 -f

  # Filter for errors
  docker logs ops-center-direct 2>&1 | grep -i error | tail -20

  # Check specific service
  docker logs unicorn-keycloak --tail 50
  docker logs unicorn-postgresql --tail 50
  ```

---

**Last Updated:** February 22, 2026
**Version:** 2.5.1
