# Colonel Skills Expansion Plan

**Created**: February 8, 2026
**Status**: PLANNING
**Context**: Colonel has 8 skills covering ~10% of Ops-Center. This plan fills the gaps.

---

## Part 1: Install Kuzu Knowledge Graph

### Decision: Auto-install with Colonel (no GUI button)

Kuzu is embedded (~3ms queries, no server, `pip install kuzu`). If someone enables The Colonel, the graph should just work. Making it a GUI toggle over-engineers a pip dependency.

### What Kuzu Does Currently

The `kuzu_client.py` stores infrastructure relationships:
- **Nodes**: Server, Container, Service, User
- **Relationships**: RUNS_ON, PROVIDES, DEPENDS_ON, INTERACTS_WITH
- Auto-populates from Docker on startup
- Provides graph context to system prompt when user asks about containers/services

### Installation Steps

1. **Add to requirements.txt** (`backend/requirements.txt`):
   ```
   kuzu>=0.7.0
   ```

2. **Install in running container** (immediate):
   ```bash
   docker exec ops-center-direct pip install kuzu
   docker restart ops-center-direct
   ```

3. **Verify**:
   ```bash
   docker logs ops-center-direct 2>&1 | grep kuzu
   # Should see: "Kuzu graph initialized at /app/data/colonel_graph"
   # Instead of: "kuzu not installed — graph memory disabled"
   ```

4. **Also add mem0ai** (semantic memory, same situation):
   ```
   mem0ai>=0.1.0
   ```
   Currently logs: "mem0ai not installed — memory features disabled"

### Dockerfile Note

The current Dockerfile's `COPY backend/*.py ./` pattern misses subdirectories, but this doesn't matter because production uses a bind mount (`backend/ -> /app`). However, for proper Docker builds (CI/CD, other servers), the Dockerfile should be updated:

```dockerfile
# Replace selective COPY lines with:
COPY backend/ ./
```

Or add the missing directories:
```dockerfile
COPY backend/colonel ./colonel
COPY backend/routers ./routers
COPY backend/migrations ./migrations
COPY backend/scripts ./scripts
```

### Graph Expansion (Future)

The kuzu schema should be expanded to model Ops-Center entities:
- Organizations, Subscriptions, API Keys
- Routes (Traefik), DNS Records
- LLM Providers, Models
- Billing relationships (Org -> Subscription -> Tier)

This lets Colonel answer questions like "What services does the retirement-leads org have access to?" by querying the graph instead of running SQL every time.

---

## Part 2: Missing Skills Inventory

### Architecture Pattern

Each skill needs 3 pieces:
1. **SKILL.md** file in `backend/colonel/skills/` (YAML frontmatter defining actions)
2. **Executor functions** in `backend/colonel/skill_executor.py` (or a new executor file)
3. **EXECUTOR_MAP entries** mapping `skill__action` to executor functions

Skills call Ops-Center's own backend APIs internally (via `httpx` to localhost:8084) or use Docker/bash for infrastructure ops. For API-backed skills, we should create a helper that calls the Ops-Center REST API with the service key.

### Helper: Internal API Client

Create `backend/colonel/internal_api.py`:
```python
"""Helper to call Ops-Center's own REST API from Colonel skills."""

async def ops_api(method: str, path: str, json=None, params=None) -> dict:
    """Call an Ops-Center API endpoint internally."""
    import httpx
    url = f"http://localhost:8084{path}"
    headers = {"Authorization": f"Bearer {os.getenv('COLONEL_SERVICE_KEY')}"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(method, url, json=json, params=params, headers=headers)
        return {"status": resp.status_code, "data": resp.json() if resp.status_code < 400 else resp.text}
```

This lets skills call any existing API endpoint without reimplementing logic.

---

## Part 3: Skills to Build (Priority Order)

### Phase 1: Critical (Weeks 1-2) — 5 skills

#### 1. `traefik-networking.skill.md`
**Why first**: Colonel managing a server needs to see routes, SSL, and service endpoints.

Actions:
- `list_routes` — GET /api/v1/traefik/routes (all HTTP routes)
- `list_services` — GET /api/v1/traefik/services (backend services)
- `get_route_detail` — GET /api/v1/traefik/routes/{name} (specific route)
- `list_ssl_certs` — GET /api/v1/traefik/ssl/certificates
- `get_metrics` — GET /api/v1/traefik/metrics (request counts, latency)
- `list_middlewares` — GET /api/v1/traefik/middlewares

Write-capable actions (confirmation_required: true):
- `create_route` — POST /api/v1/traefik/routes
- `delete_route` — DELETE /api/v1/traefik/routes/{name}

Executor: Call Traefik API endpoints via internal API client.

#### 2. `llm-management.skill.md`
**Why**: Colonel needs to know what models are available and their status.

Actions:
- `list_models` — GET /api/v1/llm/models (all available models)
- `list_curated_models` — GET /api/v1/llm/models/curated?app={app}
- `categorized_models` — GET /api/v1/llm/models/categorized
- `list_providers` — GET /api/v1/llm/providers
- `provider_status` — GET /api/v1/llm/providers/{id}/status
- `usage_stats` — GET /api/v1/llm/usage

Write-capable actions:
- `update_provider` — PUT /api/v1/llm/providers/{id} (enable/disable, change priority)

Executor: Internal API client.

#### 3. `billing-credits.skill.md`
**Why**: Colonel should know credit balances, subscription tiers, and costs.

Actions:
- `credit_balance` — GET /api/v1/credits/balance (org credit pool)
- `recent_transactions` — GET /api/v1/credits/transactions?limit=20
- `subscription_info` — GET /api/v1/subscriptions/current
- `list_plans` — GET /api/v1/billing/plans
- `tier_info` — GET /api/v1/admin/tiers (all subscription tiers)
- `usage_summary` — GET /api/v1/usage/current
- `invoices` — GET /api/v1/billing/invoices

Write-capable actions:
- `adjust_credits` — POST /api/v1/admin/credits/adjust (add/subtract credits)
- `change_tier` — PUT /api/v1/admin/tiers/{code} (modify tier settings)

#### 4. `organization-management.skill.md`
**Why**: Multi-tenant SaaS needs org management.

Actions:
- `list_orgs` — GET /api/v1/organizations
- `org_detail` — GET /api/v1/organizations/{id}
- `org_members` — GET /api/v1/organizations/{id}/members
- `org_features` — GET /api/v1/admin/orgs/{id}/features
- `org_billing` — GET /api/v1/org/{id}/billing

Write-capable actions:
- `create_org` — POST /api/v1/organizations
- `invite_member` — POST /api/v1/organizations/{id}/invite
- `grant_feature` — POST /api/v1/admin/orgs/{id}/features
- `revoke_feature` — DELETE /api/v1/admin/orgs/{id}/features/{key}
- `remove_member` — DELETE /api/v1/organizations/{id}/members/{user_id}

#### 5. `monitoring-alerts.skill.md`
**Why**: Colonel should monitor and respond to alerts.

Actions:
- `active_alerts` — GET /api/v1/alerts/active
- `alert_history` — GET /api/v1/alerts/history?limit=50
- `alert_rules` — GET /api/v1/alerts/rules
- `system_metrics` — GET /api/v1/system/metrics (Prometheus-style)
- `website_status` — GET /api/v1/websites/status (monitored websites)

Write-capable actions:
- `acknowledge_alert` — POST /api/v1/alerts/{id}/acknowledge
- `create_alert_rule` — POST /api/v1/alerts/rules
- `update_alert_rule` — PUT /api/v1/alerts/rules/{id}
- `delete_alert_rule` — DELETE /api/v1/alerts/rules/{id}

---

### Phase 2: High Priority (Weeks 3-4) — 5 skills

#### 6. `user-management.skill.md`
Enhance beyond current keycloak-auth (which is read-only list only).

Actions:
- `list_users` — GET /api/v1/admin/users (with filtering)
- `user_detail` — GET /api/v1/admin/users/{id}
- `user_roles` — GET /api/v1/admin/users/{id}/roles
- `user_activity` — GET /api/v1/admin/users/{id}/activity
- `user_sessions` — GET /api/v1/admin/users/{id}/sessions
- `user_analytics` — GET /api/v1/admin/users/analytics/summary

Write-capable actions:
- `create_user` — POST /api/v1/admin/users/comprehensive
- `assign_role` — POST /api/v1/admin/users/{id}/roles/assign
- `revoke_role` — DELETE /api/v1/admin/users/{id}/roles/{role}
- `suspend_user` — POST /api/v1/admin/users/bulk/suspend
- `revoke_sessions` — DELETE /api/v1/admin/users/{id}/sessions

#### 7. `backup-restore.skill.md`
Actions:
- `list_backups` — GET /api/v1/backups
- `backup_status` — GET /api/v1/backups/status
- `backup_schedule` — GET /api/v1/backups/schedule

Write-capable actions:
- `create_backup` — POST /api/v1/backups/create
- `restore_backup` — POST /api/v1/backups/{id}/restore (confirmation_required)

#### 8. `api-key-management.skill.md`
Actions:
- `list_service_keys` — GET /api/v1/admin/service-keys
- `list_user_keys` — GET /api/v1/admin/users/{id}/api-keys
- `list_provider_keys` — GET /api/v1/admin/provider-keys
- `list_byok_keys` — GET /api/v1/admin/byok-keys

Write-capable actions:
- `create_service_key` — POST /api/v1/admin/service-keys
- `rotate_service_key` — POST /api/v1/admin/service-keys/{id}/rotate
- `revoke_key` — DELETE /api/v1/admin/service-keys/{id}

#### 9. `analytics-reporting.skill.md`
Actions:
- `usage_overview` — GET /api/v1/admin/analytics/overview
- `revenue_summary` — GET /api/v1/admin/analytics/revenue
- `user_growth` — GET /api/v1/admin/analytics/users
- `api_usage` — GET /api/v1/admin/analytics/api-usage
- `model_usage` — GET /api/v1/admin/analytics/models
- `top_users` — GET /api/v1/admin/analytics/top-users

#### 10. `model-catalog.skill.md`
Actions:
- `list_model_lists` — GET /api/v1/admin/model-lists
- `get_model_list` — GET /api/v1/admin/model-lists/{id}
- `list_models_in_list` — GET /api/v1/admin/model-lists/{id}/models

Write-capable actions:
- `add_model_to_list` — POST /api/v1/admin/model-lists/{id}/models
- `remove_model` — DELETE /api/v1/admin/model-lists/{id}/models/{mid}
- `reorder_models` — PUT /api/v1/admin/model-lists/{id}/reorder
- `create_model_list` — POST /api/v1/admin/model-lists

---

### Phase 3: Medium Priority (Weeks 5-6) — 5 skills

#### 11. `email-configuration.skill.md`
- `list_email_providers` — list configured SMTP/OAuth providers
- `test_email` — send test email
- `list_alert_subscriptions` — who gets notified for what
- Write: `create_provider`, `update_provider`, `delete_provider`

#### 12. `feature-flags.skill.md`
- `list_features` — all defined features
- `list_tiers` — all subscription tiers
- `tier_features` — features enabled per tier
- Write: `enable_feature`, `disable_feature`, `create_feature`

#### 13. `extensions-marketplace.skill.md`
- `list_apps` — all apps in add_ons table
- `list_authorized_apps` — apps for a specific user/tier
- `app_detail` — single app info
- Write: `create_app`, `update_app`, `enable_for_tier`, `disable_for_tier`

#### 14. `search-audit.skill.md`
- `search_logs` — centralized log search across containers
- `audit_trail` — query colonel_audit_log table
- `recent_actions` — latest admin actions
- `user_audit` — actions by specific user

#### 15. `security-auth.skill.md`
Enhanced auth management (supersedes basic keycloak-auth):
- `list_identity_providers` — configured IDPs
- `realm_settings` — Keycloak realm config
- `client_list` — OAuth clients
- `session_count` — active sessions
- Write: `create_client`, `update_idp`, `force_logout_user`

---

## Part 4: Executor Architecture Decision

### Option A: One Big File (Current)
Keep everything in `skill_executor.py`. Gets unwieldy past ~1000 lines.

### Option B: Split by Domain (Recommended)
```
backend/colonel/executors/
├── __init__.py           # Imports and builds combined EXECUTOR_MAP
├── docker_executor.py    # Docker management
├── system_executor.py    # System status
├── bash_executor.py      # Bash execution
├── postgres_executor.py  # PostgreSQL ops
├── api_executor.py       # Internal API client (reusable)
├── traefik_executor.py   # Traefik/networking
├── llm_executor.py       # LLM management
├── billing_executor.py   # Billing/credits
├── org_executor.py       # Organizations
├── alert_executor.py     # Monitoring/alerts
├── user_executor.py      # User management
├── backup_executor.py    # Backup/restore
├── keys_executor.py      # API key management
├── analytics_executor.py # Analytics/reporting
└── catalog_executor.py   # Model catalog
```

Each file exports a partial EXECUTOR_MAP dict. `__init__.py` merges them:
```python
from .docker_executor import DOCKER_EXECUTORS
from .system_executor import SYSTEM_EXECUTORS
# ...

EXECUTOR_MAP = {
    **DOCKER_EXECUTORS,
    **SYSTEM_EXECUTORS,
    # ...
}
```

### Decision: Option B
Split now before adding 15 more skills. Move existing executors first, then add new ones in separate files.

---

## Part 5: Config & Enabled Skills

### Current `enabled_skills` Default
```python
enabled_skills: List[str] = Field(default_factory=lambda: [
    "docker-management", "bash-execution", "system-status",
    "service-health", "log-viewer"
])
```

Missing from default: `keycloak-auth`, `forgejo-management`, `postgresql-ops`

### Proposed New Default (After Phase 1)
```python
enabled_skills: List[str] = Field(default_factory=lambda: [
    # Infrastructure (existing)
    "docker-management", "bash-execution", "system-status",
    "service-health", "log-viewer", "postgresql-ops",
    # Identity & Git (existing)
    "keycloak-auth", "forgejo-management",
    # Phase 1 (new)
    "traefik-networking", "llm-management", "billing-credits",
    "organization-management", "monitoring-alerts",
])
```

Admin can disable any skill via PUT /api/v1/colonel/config.

### Tool Count Concern

With 15 skills averaging 6 actions each = ~90 tool definitions. This is within limits for capable models (Opus handles 100+ tools well), but smaller models may struggle. Solutions:
- Only load enabled_skills (already implemented)
- Group related actions (e.g., one `query` action with a `type` param instead of 5 separate list actions)
- Add skill "profiles" (minimal, standard, full)

---

## Part 6: Write-Capable Model Integration

The write capabilities we just implemented in this session work perfectly with new skills. Each new skill's write actions:

1. Get `confirmation_required: true` in their SKILL.md
2. Safety module blocks nuclear commands (already done)
3. Executor checks `_write_enabled` before running write operations
4. Confirmation dialog asks user before proceeding
5. Read-only models see actions described as "read-only" in system prompt

No additional write-capability work needed for new skills — the infrastructure is in place.

---

## Part 7: Implementation Order

### Session 1: Foundation
- [ ] Add `kuzu` and `mem0ai` to requirements.txt
- [ ] Install in running container and verify graph populates
- [ ] Create `backend/colonel/internal_api.py` helper
- [ ] Split `skill_executor.py` into `executors/` package
- [ ] Move existing 8 executor groups into separate files
- [ ] Verify all 8 existing skills still work after refactor

### Session 2: Phase 1 Skills (Critical)
- [ ] `traefik-networking.skill.md` + executor
- [ ] `llm-management.skill.md` + executor
- [ ] `billing-credits.skill.md` + executor
- [ ] `organization-management.skill.md` + executor
- [ ] `monitoring-alerts.skill.md` + executor
- [ ] Update default `enabled_skills`
- [ ] Build frontend + restart

### Session 3: Phase 2 Skills (High Priority)
- [ ] `user-management.skill.md` + executor (enhanced)
- [ ] `backup-restore.skill.md` + executor
- [ ] `api-key-management.skill.md` + executor
- [ ] `analytics-reporting.skill.md` + executor
- [ ] `model-catalog.skill.md` + executor

### Session 4: Phase 3 Skills (Medium Priority)
- [ ] `email-configuration.skill.md` + executor
- [ ] `feature-flags.skill.md` + executor
- [ ] `extensions-marketplace.skill.md` + executor
- [ ] `search-audit.skill.md` + executor
- [ ] `security-auth.skill.md` + executor (supersedes keycloak-auth)

### Session 5: Graph Expansion + Polish
- [ ] Expand kuzu schema with Org, Subscription, Route, Provider nodes
- [ ] Auto-populate graph from Ops-Center APIs (not just Docker)
- [ ] Add graph-aware context for billing, org, and LLM queries
- [ ] Test all 23 skills end-to-end
- [ ] Update CLAUDE.md documentation

---

## Files Reference

| File | Purpose |
|------|---------|
| `backend/colonel/skills/*.skill.md` | Skill definitions (YAML frontmatter) |
| `backend/colonel/skill_loader.py` | Parses SKILL.md into OpenAI tool defs |
| `backend/colonel/skill_executor.py` | Executor functions (to be split) |
| `backend/colonel/skill_router.py` | Routes tool_calls to executors |
| `backend/colonel/safety.py` | Blocked patterns, confirmation, sanitization |
| `backend/colonel/system_prompt.py` | Builds LLM system prompt |
| `backend/colonel/websocket_gateway.py` | WebSocket handler, LLM streaming |
| `backend/colonel/models.py` | Pydantic models, config |
| `backend/colonel/memory/kuzu_client.py` | Graph database client |
| `backend/colonel/memory/mem0_client.py` | Semantic memory client |
| `backend/requirements.txt` | Python dependencies (add kuzu, mem0ai) |

---

**End of Plan**
