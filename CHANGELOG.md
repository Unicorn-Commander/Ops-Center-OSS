# Changelog

All notable changes to Ops-Center will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] — open-source refresh 2026-07-27

### Changed
- **Relicensed to AGPL-3.0-or-later** (was Apache-2.0), with a commercial-license
  option for organizations that cannot meet the network-copyleft terms. `NOTICE`
  added; README badge and CONTRIBUTING updated to match.
- **README rebuilt around the architecture**: rendered diagrams (ecosystem, system
  architecture, inference gateway with failover, federation topologies, capability
  layers, cross-instance request flow) replace the previous ASCII sketches, and the
  federation story is documented as the **Sovereign Zero-Trust Federated Mesh** —
  identity, topology, state, security, and resilience layers.
- Documentation index now points at the guides that actually ship (user, admin, API,
  billing, integration); dead links removed.
- Public references to **unicorncommander.com** (product & ecosystem suite) and
  **unicorncommander.ai** (hosted system) added throughout.

### Security
- Snapshot re-sanitized from source `main`. Internal operational runbooks
  (SSH targets, tailnet addresses, per-peer secret handling), deployment session
  reports, and the dead documentation archive are excluded from the published tree.
- Credential scrub corrected: the previous pass replaced a database port string
  instead of the password beside it, leaving one live credential in the staged
  snapshot. Scrubbing is now value-exact and verified by a residual check.
- Gate on the shipping commit: gitleaks (git + dir modes) clean, trufflehog
  `--only-verified` = 0.

## [3.12.0] - 2026-06-19

### Added
- **Public inference gateway: embeddings + reranking + LLM failover.** The
  `llm.unicorncommander.ai` LiteLLM gateway now fronts the whole GPU mesh with
  embeddings (`bge-m3`) + rerank (`bge-reranker-v2-m3`) routes, and a 4-tier
  automatic failover under one alias (`uc/chat-default`): local 3090 → local
  P40 → DeepSeek V4 Flash → OpenRouter. Direct DeepSeek + OpenAI providers
  wired (keys in env, not committed config). All authed per-org + metered to
  Lago; verified failover fires live.
- **Usage-based pricing across all modalities** (LLM/embeddings/rerank/STT/TTS)
  with per-tier budget gating (`subscription_tiers.max_monthly_llm_budget` →
  per-org litellm key `max_budget`): local is $0/unlimited, cloud counts against
  a bundled allowance, free = local-only/fail-closed.

### Changed
- **Retired the redundant `/api/v1/metered/embeddings` + `/rerank` proxy routes**
  (embeddings/rerank now ride the litellm gateway). The `/report` bridge for
  STT/TTS unit metrics stays. Removed dead helpers + imports.
- **Dope new README** — local-first/federated-mesh framing, the smart-gateway
  architecture + failover diagram, real screenshots, current feature set.
- Help/Guide FAQ updated for the gateway failover + local-first billing model.

## [3.11.0] - 2026-06-18

### Added
- **Lago metering for non-LLM local compute** (closes the gap where only the
  Qwen LLMs emitted billing events). Embeddings, reranking, STT, and TTS now
  meter through the existing federation rail (`FederationMeter.record_usage`,
  keyed `external_subscription_id = org_id`, with the `gateway_metered`
  double-bill guard), each with its own unit-based billable metric:
  `embeddings_tokens`, `rerank_searches`, `stt_audio_seconds`, `tts_characters`.
  - `FederationMeter._report_to_lago` extended to emit a distinct unit metric
    when `billing_metric` is set; the LLM `ai_api_call` path is unchanged.
  - New `metered_compute_api.py` (`/api/v1/metered`): metered **proxy** for
    embeddings/rerank (forwards to the Infinity server, counts units), and a
    service-key **report bridge** (`POST /api/v1/metered/report`) so the
    STT/TTS voice plane reports unit counts without transiting audio.
  - Exempt tiers (free / on-device / vip / internal) are not metered;
    collect-don't-gate (usage is metered, the call is never blocked).
  - `scripts/register_metering_metrics.py` registers the four billable
    metrics in Lago (idempotent). `/api/v1/metered/` added to CSRF exempt
    (API/service auth, like `/api/v1/llm/`).
  - NOTE: this builds and proves the metering rail; each client (Center-Deep
    RAG → embeddings/rerank, voice plane → STT/TTS) must point at the metered
    endpoints / call the report bridge for its real traffic to be billed, and
    a charge/price must be attached to each metric in the Lago plan.

## [3.10.2] - 2026-06-17

### Fixed
- **Notification Preferences now actually work.** The Account → "Notification
  Preferences" page (`NotificationSettings`) previously loaded a mock payload
  whose field names didn't match the UI and had no save endpoint, so toggles
  rendered blank and "Save" always failed.
  - New `notification_preferences_api.py`: real persisted `GET`/`PUT
    /api/v1/notifications/preferences` (JSONB-backed `user_notification_preferences`
    table keyed by Keycloak user id) plus `POST /api/v1/notifications/test`
    (non-sending preview, matching the "email delivery coming soon" notice).
  - Removed the conflicting mock GET from `account_management_api.py`.
  - Frontend sends the double-submit CSRF token on save/test so it works
    whether or not CSRF enforcement is enabled.
- **Removed the duplicate, broken notifications page.** The orphaned
  `AccountNotifications` page (route `/admin/account/notifications`, not in the
  menu) posted to a nonexistent `/api/v1/auth/notifications`; its route now
  redirects to the canonical `notification-settings` page and the file is gone.

### Audited
- Full admin sidebar menu audit (44 items): every other menu entry resolves to
  the correct route, component, and backing endpoints. No other mispointed or
  dead menu links found (FederationContracts and `/subscriptions/current` were
  verified real, not stubs).

## [3.10.1] - 2026-06-17

### Changed
- Anthropic BYOK clarifier now also appears in the **Add API Key** form (next to the "get your key" link), not just the provider card — so it shows at the moment a user is about to paste a key.

## [3.10.0] - 2026-06-17

### Added
- **`rotate_api_key`** — third confirm-gated Guide mutation, completing the API-key lifecycle
  (create · list · revoke · rotate). On confirm it issues a NEW key with the same scopes and
  revokes the old one; the new key is shown once. Generalized the pending-action to a `spec`
  (`{kind:"single"|"rotate", …}`) so the framework now supports **compound** mutations; rotate is
  best-effort on the revoke step (new key always created first; if the old can't be revoked the UI
  says so). The Guide lists keys to resolve the real id before proposing.
- **Anthropic BYOK clarifier** (`AccountAPIKeys.jsx`): the Anthropic provider card now notes that a
  Claude Pro/Max **subscription can't be used in third-party apps** — use an API key from the
  Console (bills the API account, separate from the subscription). Reflects Anthropic's current
  policy; pre-empts users expecting subscription sign-in.

## [3.9.3] - 2026-06-17

### Added / Fixed — canonical Free tier + consistent new-org default
- **New `free` tier** (both nodes): $0, `api_calls_limit=0` (in-browser / on-device AI + local
  storage — no server inference), no premium app grants. It's the safe floor and is already the
  name used in `CREDIT_EXEMPT_TIERS`. Added a matching `free` plan to the in-memory plan registry
  so it displays correctly in My Access.
- **New orgs now default to `free`** instead of `founders_friend`. The old default (`founders_friend`,
  plural) matched no tier-code, so every new org silently fell to trial. Normalized the default
  across `org_manager.py`, `server.py` (org-creation + gateway-key `plan_code` label), and
  `org_api.py`; added `free` to `NON_PURCHASABLE_TIERS`.
- **Tier-code drift fixed:** commander's `founder-friend` → `founder_friend`, matching bigboy.
- Frontend: org-tier filter + tier badge colors updated to the real tier set
  (free / founder_friend / vip_founder / byok / managed / client).

## [3.9.2] - 2026-06-17

### Fixed
- **Org resolution now only resolves *active* organizations.** The login lookup used
  `LIMIT 1` with no status filter, so a user in multiple orgs could be dropped into a
  suspended/stale workspace arbitrarily (e.g. landing in a defunct pilot org instead of their
  real one). Now filters `status='active'`, so suspended/deleted orgs are skipped and multi-org
  users land in a live workspace.

### Housekeeping (data)
- Suspended stale orgs on production (commander): NDA-AutoPilot, Test Organization (API Tests),
  M10 Ventures, Doug "Crash" Walker, Ceejay Teodoro; and on dogfood (bigboy): M10 Ventures.
  Deactivated 4 unused bespoke tier-codes (crash-dev, m10_partner, nda-autopilot, partnerpulse).
  All reversible — Keycloak users + memberships preserved (status flip only, no deletes). This
  also resolves the earlier "dashboard says Professional / plan says Trial" mismatch (it came
  from a defunct org whose `plan_tier` matched no tier-code → silent trial).

## [3.9.1] - 2026-06-14

### Added
- **`revoke_api_key`** — second confirm-gated mutation, completing the API-key self-service
  lifecycle (create · list · revoke). The Guide lists the user's keys to find the right id,
  then proposes a revoke; the confirm card spells out that any app using the key stops working
  immediately. Generalized the pending-action record to carry method/path/body (supports the
  `DELETE /account/uc-api-keys/{id}` path param), with `key_id` validated against a strict
  pattern to block path injection. Read tools execute before a same-turn write proposal, so the
  list→revoke chain resolves the real key id before the confirm card is shown.

## [3.9.0] - 2026-06-14

**Personal Account Assistant — Phase 2 (confirm-gated mutations).** The Guide can now
*propose* account actions; nothing executes without an explicit user Confirm.

### Added
- **Confirm-card / pending-action framework** (`help_guide_api.py`): a WRITE tool is never
  auto-executed. When the model calls one, the params are validated, a single-use pending
  action is stashed in Redis (owner-scoped, short-lived), and the UI gets a Confirm/Cancel
  card (`GuideActionCard.jsx`, wired into the Guide bubble + Help panel). Only an explicit
  `POST /api/v1/help/guide/confirm-action` runs the underlying mutation — **as the user**
  (forwards the session + CSRF cookies, so the endpoint's own auth/RLS/RBAC re-run). The
  model can PROPOSE but never DO; the human approves the exact action. Every proposal and
  execution is audited (`audit_logger`, secrets never logged).
- **First mutation: `create_api_key`** — wraps `POST /api/v1/account/uc-api-keys`; the new
  key is shown once in the confirm result with a "save it now" warning. Discovery chip added.
- **Financial actions are intentionally NOT agent-executed**: the Guide will not change plans
  or buy credits — it points the user to the existing checkout UI (`/admin/billing/tiers`,
  `/admin/billing/credits`), so the agent never moves money. (Revisit once the model is proven
  reliable enough to trust with payments.)

## [3.8.0] - 2026-06-14

**Personal Account Assistant — Phase 1 (read-only).** The Guide can now answer questions about
the signed-in user's **own** account with real data.

### Added
- **Read-only account tools for The Guide** (`help_guide_api.py`): when a logged-in user asks
  about their own balance, usage, plan, invoices, or API keys, the Guide calls a small set of
  fixed, read-only tools and answers from real data — `get_my_credit_balance`, `get_my_usage`,
  `get_my_plan`, `get_my_invoices`, `list_my_api_keys` (names/prefixes only — never a secret),
  and `get_my_account_summary`. New discovery chips in the Guide bubble ("What's my balance?",
  "How much usage do I have left?", "Show my recent invoices").
- **Safety model:** every tool is a thin wrapper over an existing user-facing endpoint, invoked
  via a localhost self-call that forwards **only the caller's session cookie** — so each
  endpoint's own auth + RLS + RBAC re-run and the Guide can do nothing the user couldn't do
  themselves in the UI. The LLM call stays internal (master key + local model = free); only the
  tool *executions* run as the user. Tool paths/params are fixed server-side (the model only
  picks which tool — no URL/param injection surface). Bounded tool-calling loop with graceful
  fallback to plain help when the model/gateway doesn't support tools. Phase 1 is read-only;
  mutations (upgrade/buy-credits/create-key) are a future Phase 2 behind confirmation + audit.
- Configurable via `ACCOUNT_ASSISTANT_ENABLED` (default on) and `OPS_CENTER_SELF_URL`.

## [3.7.0] - 2026-06-14

Comprehensive Help section + **The Guide** (end-user help agent).

### Added
- **Comprehensive, route-aware Help** (`HelpPanel.jsx` + `src/data/helpContent.js`): help for
  ~40 admin routes across all 8 areas (billing, AI/models, infra/federation, people/access,
  monitoring, integrations, platform), auto-selected by the current route, plus a searchable
  **FAQ** tab (~20 Q&As) and refreshed Docs links. Content authored grounded in the real pages.
- **The Guide** — a separate, end-user-facing help agent (distinct from Colonel, which is the
  root-level admin agent). The Guide has **zero system access**: it cannot run any skill,
  command, or change any setting — it only explains the platform and points to the right page.
  Ops-center-native (calls the local inference gateway directly with an internal key + a local
  model, so users are never billed and a prompt can't run anything). Backend `help_guide_api.py`
  (`POST /api/v1/help/guide/ask`, seeded with the help knowledge), front-end "Ask the Guide" tab
  with its own avatar.

### Fixed
- Stale sidebar version label (`v3.3.0` → live version).

## [3.6.0] - 2026-06-13

Federation monetization complete + inference cost-recovery substrate. (Tracked in
Project-Ops P-00067. Full detail: `~/Documents/federation-build-report.md` and
`~/Documents/UC-Inference-Cost-Recovery-Design.md`.)

### Added
- **Federation reconciliation**: trust modes (full/scoped/consumer/publisher/isolated)
  now ENFORCED at `/services`, `/agents`, `/route` with deny-by-default
  (`FEDERATION_DEFAULT_TRUST_MODE`, platform_settings-overridable). The per-org gateway
  key (`user_id == org_id`) now survives the federation hop (`X-Federation-Org-Id`), so
  the single billable Lago `ai_api_call` event keys to the consuming org across nodes.
- **Billing-on-signup** (`plan_provisioning`): plan activation auto-provisions the org's
  gateway key (migration 011; `/key/update` on plan changes).
- **Federated local models in the customer LLM API**: a trusted peer's published model is
  served via federation under the caller's org; publisher resolves raw catalog names →
  gateway aliases. Surfaced in `/models` and `/models/categorized`.
- **Layer-2 agent contracts**: per-agent ACLs (`consume: ["agents/<id>"]`) +
  `POST /federation/agents/{id}/invoke` → one `agent_invocation` Lago event (completed-only;
  units from `FEDERATION_AGENT_PRICING`).
- **True SSE stream-through** for federated inference — token-by-token relay across both
  nodes (`serve_federated_inference_stream`, `proxy_to_node_stream`,
  `stream_llm_via_federation`); the publisher's gateway meters once on stream completion.
- **Per-(app, model) included-vs-metered policy** (`inference_policy.py` + `app_model_policy`
  table) — bundle specific models into an app subscription; default metered (zero rows = no
  behavior change).
- **Routing-audit timed flush** (`FEDERATION_AUDIT_FLUSH_SECONDS`, default 30s).

### Fixed
- **Credit double-debit**: chat/image handlers stamp `_metadata.credits_settled`; the credit
  middleware skips its own deduction on `credits_settled`/`gateway_metered` (was a latent
  double-charge for non-exempt paid users, masked by exempt tiers).
- **Mode C cost leak**: direct-API (`uc_`) keys now bill the key owner's real tier instead of
  a hardcoded `vip_founder` exempt (fail-open to exempt on lookup error).
- **Budget/tier decouple**: gateway-key budget is no longer sourced from the subscription
  tier — inference spend is guarded by the credit wallet (subscription and credits are
  orthogonal axes).

### Removed
- Opus-distill model (weights + presets + alias).

## [2.5.2] - 2026-02-27

### Added
- **Colonel → Brigade Delegation**: One-way A2A delegation from Colonel to Unicorn Brigade
  - New `brigade-delegation` skill with `delegate_task` and `list_agents` actions
  - Colonel can delegate research, coding, finance, legal, medical, and other domain tasks to Brigade's 17 specialist agents
  - Uses A2A protocol (JSON-RPC over HTTP) for inter-service communication
  - Agent discovery via public A2A endpoint, task execution via authenticated invoke
  - Handles timeouts (120s), auth errors, missing agents, and empty responses gracefully

### Configuration
- **Brigade Auth**: Added `BRIGADE_ADMIN_KEY` to Brigade container for service-to-service authentication
- **Ops-Center Env**: Added `BRIGADE_API_URL` and `BRIGADE_API_KEY` environment variables
- **Docker Compose**: Updated `docker-compose.brigade.yml` and `docker-compose.direct.yml`

### Files Added
- `backend/colonel/skills/brigade-delegation.skill.md` - Skill definition (YAML frontmatter)

### Files Modified
- `backend/colonel/skill_executor.py` - Added `brigade_delegate_task()` and `brigade_list_agents()` executors
- `backend/colonel/models.py` - Added `brigade-delegation` to default `enabled_skills`

---

## [2.5.1] - 2026-02-22

### Fixed
- **Frontend Audit Sweep**: Comprehensive 108-file frontend quality audit and fix
  - Removed dead code: 3 unused files deleted (useColonelSkills.js, useColonelMemory.js, CommandOutput.jsx)
  - Removed unused imports across 10 files (App.jsx, Layout.jsx, RootRedirect.jsx, ColonelChat.jsx, UserDetail.jsx, AccountAPIKeys.jsx)
  - Removed duplicate routes for `platform/white-label` and `apps` in App.jsx
  - Removed debug `console.log` statements from App.jsx, Layout.jsx, OrganizationTeam.jsx
  - Fixed Dashboard.jsx quick actions: `window.location.href` → `navigate()` for SPA routing
  - Fixed swapped Visitors/Page Views labels in UmamiConfig.jsx
  - Fixed hardcoded `localhost:8084` URLs in UmamiConfig, GrafanaConfig, PrometheusConfig, GrafanaViewer → relative paths
  - Added `credentials: 'include'` to 232 fetch() calls across 74 files for proper SSO cookie handling
  - Added `StatusBadge` null checks in SubscriptionBilling and SubscriptionPlan to prevent crashes
  - Added missing `FireIcon` import in Security.jsx
  - Wired OrganizationBilling buttons (Change Plan, View Invoices, Cancel)
  - Wired SubscriptionCancel buttons (Pause Instead → plan page, Get Help → email)
  - Added WebSocket `streamBuffer` reset on session change in useColonelWebSocket.js
  - Replaced mock session fallback with empty array in AccountSecurity.jsx

### Improved
- **Monitoring Config Persistence**: UmamiConfig, GrafanaConfig, PrometheusConfig now save settings to localStorage and restore on page load (previously lost on refresh)
- **GrafanaViewer Preferences**: Theme, time range, and refresh interval now persist via localStorage
- **Colonel API Standardization**: ColonelSidebar.jsx now uses colonelApi.js instead of raw fetch calls
- **Dynamic URLs**: AccountAPIKeys.jsx now uses `window.location.origin` instead of hardcoded domain

### Changed
- Version bumped from v2.4.0 to v2.5.0 in Layout.jsx footer

---

## [2.3.0] - 2025-11-09

### Major Refactoring: Feature → App Terminology

**Breaking Changes**:
- API endpoint `/api/v1/admin/features` renamed to `/api/v1/admin/apps`
- Frontend route `/admin/system/feature-management` renamed to `/admin/system/app-management`

### Changed

#### Database Schema
- **Table Renamed**: `feature_definitions` → `app_definitions`
- **Table Renamed**: `tier_features` → `tier_apps`
- **Column Renamed** (app_definitions): `feature_key` → `app_key`, `feature_name` → `app_name`, `feature_description` → `app_description`, `feature_icon` → `app_icon`
- **Column Renamed** (tier_apps): `feature_key` → `app_key`, `feature_value` → `app_value`
- **Backward Compatibility**: Created views `feature_definitions` and `tier_features` as aliases for transition period

#### Backend API
- **New File**: `backend/app_definitions_api.py` - App management endpoints
- **Updated**: `backend/tier_features_api.py` - Updated to use `tier_apps` table
- **Updated**: `backend/server.py` - Router registration updated
- **Updated**: `backend/subscription_tiers_api.py` - Updated JOIN to use `tier_apps`
- **Updated**: `backend/my_apps_api.py` - Updated terminology throughout

#### Frontend
- **Renamed**: `FeatureManagement.jsx` → `AppManagement.jsx` (16.15 KB)
- **Updated**: `App.jsx` - Route and import updated
- **Updated**: `Layout.jsx` - Navigation menu updated
- **Updated**: `SubscriptionManagement.jsx` - API calls and data mapping updated
- **UI Text**: All instances of "Feature" changed to "App" throughout interface

### Added
- **Migration Script**: `backend/migrations/rename_features_to_apps.sql` (1.8 KB)
- **Documentation**: `FEATURE_TO_APP_REFACTORING_COMPLETE.md` - Comprehensive refactoring guide
- **API Endpoints**: 4 new endpoints under `/api/v1/admin/apps/*`

### Fixed
- **Terminology Confusion**: Eliminated ambiguity between tier properties (e.g., `is_active`, `byok_enabled`) and user-facing services/applications (e.g., Brigade, Bolt, Chat)
- **Consistent Naming**: Database, backend, and frontend now use consistent "app" terminology

### Migration Guide

**For API Clients**:
```bash
# Old endpoint (deprecated but still works via backward-compatible views)
GET /api/v1/admin/features

# New endpoint (recommended)
GET /api/v1/admin/apps
```

**For Users**:
- Bookmark update: `/admin/system/feature-management` → `/admin/system/app-management`

**Database Migration** (automatic):
```sql
-- Backward-compatible views created automatically
-- Old code continues to work during transition period
SELECT * FROM feature_definitions;  -- Still works (view → app_definitions)
SELECT * FROM tier_features;        -- Still works (view → tier_apps)
```

### Data Preservation
- ✅ **100% Data Integrity**: All 17 apps and 21 tier-app associations preserved
- ✅ **Zero Downtime**: Backward-compatible views ensure old code continues working
- ✅ **Rollback Ready**: Complete rollback procedure documented if needed

---

## [2.2.0] - 2025-11-04

### Added
- **Image Generation API**: OpenAI-compatible `/api/v1/llm/image/generations` endpoint
  - Support for DALL-E 2/3, Stable Diffusion XL/3 via OpenRouter
  - BYOK support (no credits charged when using own API keys)
  - Tier-based pricing with automatic cost calculation
  - Quality options (standard/HD) and batch generation (up to 10 images)
  - OpenAI SDK compatible

- **Model Categorization**: New `/api/v1/llm/models/categorized` endpoint
  - Separates BYOK models (free) from Platform models (charged)
  - Smart provider detection based on user's API keys
  - Detailed provider-level summaries
  - Integration guide for Bolt/Presenton/Open-WebUI

### Documentation
- `docs/api/IMAGE_GENERATION_API_GUIDE.md` - Complete image generation guide (20+ pages)
- `docs/api/IMAGE_GENERATION_QUICK_START.md` - Quick start guide
- `docs/INTEGRATION_GUIDE.md` - Bolt/Presenton/Open-WebUI integration (800+ lines)

---

## [2.1.0] - 2025-10-29

### Fixed
- **Credit System Authentication**: Fixed user session integration
  - Replaced test user fallback with real Keycloak session authentication
  - Added automatic field mapping: Keycloak `sub` → application `user_id`
  - Fixed circular import in `credit_api.py`

- **Credit Display Formatting**: Removed misleading dollar signs
  - Changed display from "$10,000" to "10,000 credits"
  - Created `formatCredits()` function with comma separators
  - Updated 4 display locations in Credit Dashboard

### Added
- **Organization Setup**: Created "Magic Unicorn" organization with professional tier
- **Credit Allocation**: Allocated 10,000 credits to admin user
- **OpenRouter Integration**: Verified API key configuration in LiteLLM proxy

### Documentation
- `CREDIT_BALANCE_EXPLAINED.md` - Guide to understanding credit vs OpenRouter balances
- `CREDIT_API_USER_ID_FIX.md` - Authentication fix documentation
- `CREDIT_DISPLAY_FIX.md` - Display formatting documentation
- `FINAL_CREDIT_FIX_SUMMARY.md` - Complete technical summary

---

## [2.0.0] - 2025-10-15

### Added - Phase 1: User Management & Billing Dashboard

#### User Management System (Complete)
- **Bulk Operations**: CSV import/export, bulk role assignment, bulk suspend/delete, bulk tier changes
- **Advanced Filtering**: 10+ filter options (tier, role, status, org, date ranges, BYOK, email verified)
- **User Detail Page**: Comprehensive 6-tab profile view with charts and activity timeline
- **Enhanced Role Management**: Dual-panel UI with visual permission matrix
- **API Key Management**: Full CRUD for user API keys with bcrypt hashing
- **User Impersonation**: Admin "login as user" feature with 24hr sessions
- **Activity Timeline**: Color-coded audit log with expandable details

#### Billing Dashboard (Complete)
- **Subscription Plans**: Trial ($1/week), Starter ($19/mo), Professional ($49/mo), Enterprise ($99/mo)
- **Lago Integration**: Full billing system with GraphQL API
- **Stripe Integration**: Payment processing with 7 webhook events
- **Invoice Management**: History, payment tracking, usage metering
- **Webhook Handling**: Automated subscription lifecycle management

#### New Components
- `UserDetail.jsx` - 6-tab user profile page (1,078 lines)
- `RoleManagementModal.jsx` - Enhanced role UI (534 lines)
- `PermissionMatrix.jsx` - Visual permission grid (177 lines)
- `BulkActionsToolbar.jsx` - Bulk operations UI
- `ImportCSVModal.jsx` - CSV import wizard
- `APIKeysManager.jsx` - API key management (493 lines)
- `ActivityTimeline.jsx` - Activity audit log (418 lines)

#### New API Endpoints
- User Management: 15+ new endpoints for bulk operations, impersonation, API keys
- Role Management: 4 new endpoints for hierarchy, permissions, effective permissions
- Session Management: 3 endpoints for session tracking and revocation

### Changed
- **User Management**: Enhanced with advanced filtering (10+ parameters)
- **Keycloak Integration**: Automatic user attribute population for 9 users
- **Frontend Build**: Added dependencies: `react-chartjs-2`, `chart.js`

### Documentation
- `USER_MANAGEMENT_GAP_ANALYSIS.md` - Feature gap analysis
- `DEPLOYMENT_VERIFICATION_GUIDE.md` - 82-page testing guide
- `docs/API_REFERENCE.md` - OpenAPI-style API documentation
- `docs/ADMIN_OPERATIONS_HANDBOOK.md` - Practical admin guide
- `CODE_REVIEW_REPORT.md` - Quality assessment (B+ grade)
- `NEXT_PHASE_ROADMAP.md` - Strategic roadmap (Phases 2-4)

---

## [1.0.0] - 2025-09-01

### Initial Release
- Basic user management
- Service management dashboard
- Keycloak SSO integration
- LLM management via LiteLLM
- Docker deployment configuration
