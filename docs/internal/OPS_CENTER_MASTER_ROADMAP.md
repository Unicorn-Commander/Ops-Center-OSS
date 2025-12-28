# Ops-Center Master Roadmap & Status

**Last Updated**: October 28, 2025, 11:45 PM
**Version**: 5.1 - Multi-App Architecture Clarification
**Overall Status**: **90% COMPLETE** 🎉

---

## 🎯 VISION & ARCHITECTURE

### The Three Pillars

1. **Ops-Center** - Central management hub (THIS PROJECT)
2. **Brigade** - AI agent platform (integrated via A2A)
3. **Center-Deep** - Search & research platform (integrated)

### User Types (RBAC Model)

- **System Admin** - Platform-wide management (full access)
- **Org Admin** - Organization-level management
- **End User** - Personal subscription, usage, settings

### Multi-App Architecture

UC-Cloud is a **multi-service ecosystem** with **centralized authentication and billing**:

**Services**:
1. **Ops-Center** (THIS PROJECT) - https://your-domain.com:8084
   - Central management dashboard
   - User/org administration
   - Billing & subscription management
   - LLM infrastructure routing

2. **Brigade** - https://brigade.your-domain.com
   - AI agent factory (build, manage, deploy agents)
   - 48+ pre-built agents
   - Tool execution system
   - Agent API endpoints
   - **Database**: Separate `brigade_db` in shared PostgreSQL
   - **LLM Routing**: Uses Ops-Center API for billing integration

3. **Center-Deep** - https://search.your-domain.com
   - AI-powered metasearch engine (70+ search engines)
   - Tool servers for specialized search
   - Admin panel for search configuration
   - **Separate service** with own admin

4. **Open-WebUI** - https://chat.your-domain.com
   - Chat interface for LLMs
   - MCP tool usage
   - Multi-model conversations

**Shared Infrastructure**:
- ✅ **Keycloak SSO** (uchub realm) - Single authentication for ALL services
- ✅ **PostgreSQL** - Shared container, separate databases per service
- ✅ **Redis** - Shared cache and session storage
- ✅ **Traefik** - Shared reverse proxy with SSL/TLS
- ✅ **Lago + Stripe** - Centralized billing (managed via Ops-Center)

**Key Insight**: It's NOT "each app has its own admin and users" - instead:
- **Centralized users**: Keycloak manages authentication for all services
- **Centralized billing**: Ops-Center manages subscriptions and tiers
- **Service-specific data**: Each service stores its own operational data
- **Shared subscription tiers**: All services use the same pricing model

### Edge Device Management (Organizations)

**New Capability** (Epic 7.1 - Planned):

Organizations can deploy **edge devices** (laptops, workstations) that:
- Run local LLM models (Ollama, vLLM)
- Have their own local Keycloak instance
- Are **centrally managed** by cloud UC-Cloud

**Architecture**:
```
Cloud UC-Cloud (your-domain.com)
    │
    ├── Organization A
    │   ├── Cloud users (browser-based)
    │   └── Edge Devices (managed fleet)
    │       ├── Laptop 1 (Ollama, local Keycloak)
    │       ├── Laptop 2 (vLLM, local Keycloak)
    │       └── Workstation 3 (local models)
    │
    └── Organization B
        ├── Cloud users
        └── Edge Devices
            └── Laptop 4 (hybrid cloud/local)
```

**Features**:
- **Device Registration**: Edge devices register with cloud UC-Cloud
- **Configuration Sync**: Cloud pushes configs to edge devices
- **Model Management**: Deploy/update local models remotely
- **Monitoring**: Cloud monitors edge device health and usage
- **Billing**: Usage from edge devices attributed to organization
- **Failover**: Edge devices can work offline, sync when reconnected
- **Security**: Edge devices authenticate to cloud for management
- **Keycloak Federation**: Local Keycloak instances federate with cloud

**Use Cases**:
- Organizations with high-security requirements (data never leaves premises)
- Remote workers with powerful laptops running local models
- Hybrid deployment (some workloads cloud, some edge)
- Reduced latency for local inference
- Cost optimization (use local GPU vs cloud API calls)

### User Role Tiers (5 RBAC Levels)

**Platform Access Levels**:
1. **System Admin** - Platform-wide management (full access)
2. **Org Admin** - Organization-level management
3. **Developer** - Service access, API keys, development tools
4. **Analyst** - Read-only analytics, reports
5. **Viewer** - Basic read access

### Subscription Pricing (3 Tiers)

**1. VIP/Founder/Internal** - $0/month (Invite-Only)
- For: Founder's friends, admins, staff, partners
- No monthly credits included
- Must buy credits separately as needed
- Full platform access
- Direct support from founders
- **Not publicly available** - invite code required

**2. BYOK (Bring Your Own Key)** - $30/month
- Use your own API keys (OpenAI, Anthropic, Google, etc.)
- No platform markup - direct passthrough
- No credits needed (you manage your own billing)
- Priority support
- API key management interface

**3. Managed (Default)** - $50/month ⭐ Recommended
- Use Ops-Center's LLM routing infrastructure
- May include monthly credits (amount TBD)
- Platform manages all API keys
- Automatic billing and usage tracking
- Priority support
- Access to all 100+ models via OpenRouter

**Credit System**:
- **Credits**: Pre-paid balance used for LLM API calls (Managed tier only)
- **Purchase Anytime**: All users can buy credits separately
- **Free Credits**: Platform may give out promotional credits
  - OpenRouter credits (available now)
  - Google Cloud credits (coming soon)
- **Usage Metering**: Tracks every API call, LLM token, agent execution
- **Billing Attribution**:
  - User → charges their credit balance
  - Organization → charges org's shared balance
  - Agent → when Brigade agent calls LLM via Ops-Center
- **No Markup for BYOK**: Direct passthrough to your API keys

**Legacy Code Note**:
Old tier definitions exist in codebase (Trial, Free, Starter, Professional, Enterprise) from previous pricing model. These will be migrated to the new 3-tier structure: Advanced ($0), BYOK ($30), Managed ($50).

---

## 📊 CURRENT STATUS (October 28, 2025)

### What Works RIGHT NOW ✅

**Backend**: 92% complete - 452 endpoints across 44 API modules
**Frontend**: 87% complete - 74 fully functional pages (89 total)
**Database**: 100% operational - PostgreSQL + Redis
**Authentication**: 100% - Keycloak SSO with Google/GitHub/Microsoft
**Billing**: 100% - Lago + Stripe (LIVE keys configured)
**LLM Infrastructure**: 95% - LiteLLM routing, OpenRouter, BYOK

### Today's Achievements (Oct 28, 11:30 PM) 🎉

1. ✅ **Navigation Restructure**
   - Renamed "Platform Settings" → "Integrations"
   - Created "Monitoring & Analytics" section (5 pages)
   - Organized for long-term scalability

2. ✅ **Platform Settings Connection Tests Fixed**
   - Fixed Lago connection test
   - Fixed Keycloak connection test
   - Implemented credential fallback pattern

3. ✅ **New Monitoring Pages Created**
   - MonitoringOverview.jsx - Hub for all monitoring tools
   - GrafanaConfig.jsx - Dashboard configuration (placeholder)
   - PrometheusConfig.jsx - Metrics collection (placeholder)
   - UmamiConfig.jsx - Web analytics (placeholder)

### What's Left (10% remaining)

1. **Subscription Management GUI** (1-2 days) 🆕 HIGH PRIORITY
   - Admin interface to create/edit subscription tiers
   - Visual pricing tier editor
   - Feature flags per tier
   - Easy enable/disable tiers
   - Tier migration tools (move users between tiers)
   - Location: System → Billing → Subscription Management

2. **Dashboard Refinement** (1-2 days)
   - Modernize glassmorphism design
   - Add real-time metrics
   - Section-by-section polish

3. **Monitoring Tools Integration** (3-4 days) 🔄 IN PROGRESS
   - Implement Grafana API integration
   - Implement Prometheus scrape config
   - Implement Umami tracking scripts

4. **The Colonel AI Agent System** (1-2 weeks) 🔄 IN PROGRESS
   - Lt. Colonel "Atlas" - Ops-Center expert agent
   - Custom tools for Ops-Center API
   - Chat interface integration
   - A2A protocol for multi-instance coordination

5. **Edge Device Management** (2-3 weeks) 🆕 FUTURE (Epic 7.1)
   - Device registration and authentication
   - Remote configuration management
   - Model deployment to edge devices
   - Edge monitoring dashboard
   - Keycloak federation support
   - Hybrid cloud/edge billing

---

## 🗂️ NAVIGATION STRUCTURE

### Current Organization (October 28, 2025)

```
🏠 Personal
├── Dashboard
├── My Account
│   ├── Profile & Preferences
│   ├── Notifications
│   ├── Notification Settings
│   ├── Security & Sessions
│   └── API Keys (BYOK)
├── My Subscription
│   ├── Current Plan
│   ├── Usage & Limits
│   ├── Billing History
│   └── Payment Methods
└── Credits & Usage
    ├── Credit Dashboard
    └── Pricing Tiers

🏢 Organization (Org Admins Only)
├── Team Members
├── Roles & Permissions
├── Organization Settings
└── Organization Billing

⚙️ System (Platform Admins Only)
├── AI Models
├── Services
├── Resources
├── Hardware Management
├── Billing Analytics
├── User Management
├── Network
├── Cloudflare DNS
├── Traefik (5 sub-pages)
├── Storage & Backup
├── Security
├── Authentication
├── Local Users
├── LLM Providers
├── OpenRouter Settings
├── LLM Usage
├── Extensions
├── Landing Page
├── Integrations (RENAMED 🎉)
│   ├── API Credentials (Stripe, Lago, Cloudflare, NameCheap)
│   └── Email Providers
└── Monitoring & Analytics (NEW 🎉)
    ├── Overview
    ├── Grafana
    ├── Prometheus
    ├── Umami Analytics
    └── System Logs
```

### Proposed Optimal Structure (For Next Sprint)

```
⚙️ System (Platform Admins Only)
├── 📊 Dashboard
│
├── 👥 Users & Organizations
│   ├── User Management
│   ├── Organization Management
│   ├── Local Users (Linux)
│   └── Billing Analytics
│
├── 🤖 LLM & AI
│   ├── AI Models (vLLM, Ollama)
│   ├── LLM Providers (LiteLLM)
│   ├── OpenRouter (348 models)
│   └── Usage Analytics
│
├── 🏗️ Infrastructure
│   ├── Services (Docker)
│   ├── Resources (CPU, RAM, GPU)
│   ├── Hardware Monitoring
│   ├── Network
│   ├── Storage & Backup
│   └── Traefik (Reverse Proxy)
│
├── 🔗 Integrations
│   ├── API Credentials (Stripe, Lago, Cloudflare, NameCheap, Forgejo)
│   ├── Email Providers
│   └── DNS Management
│
├── 📈 Monitoring & Analytics
│   ├── Overview
│   ├── Grafana
│   ├── Prometheus
│   ├── Umami
│   └── System Logs
│
├── 🔐 Security & Compliance
│   ├── Authentication (Keycloak/SSO)
│   ├── Security Policies
│   └── Audit Logs
│
└── ⚙️ Configuration
    ├── Landing Page
    ├── Extensions
    └── System Settings
```

**Benefit**: Clear functional categories, predictable location for features, scalable structure.

---

## 🔗 INTEGRATIONS STATUS

### External APIs Configured

| Service | Status | Purpose | API Key Location |
|---------|--------|---------|------------------|
| **Stripe** | ✅ LIVE | Payment processing | Integrations → Credentials |
| **Lago** | ✅ Active | Billing management | Integrations → Credentials |
| **Keycloak** | ✅ Active | SSO authentication | Integrations → Credentials |
| **Cloudflare** | ✅ Active | DNS/CDN management | Integrations → Credentials |
| **NameCheap** | ✅ Active | Domain registrar | Integrations → Credentials |
| **Email (M365)** | ✅ Active | Transactional email | Integrations → Email |
| **Forgejo** | 🟡 Planned | Git forge integration | To be added |

### Internal Services Integrated

| Service | Status | Purpose |
|---------|--------|---------|
| **Brigade** | ✅ Active | AI agent platform |
| **Center-Deep** | ✅ Active | Search engine |
| **Open-WebUI** | ✅ Active | Chat interface |
| **LiteLLM** | ✅ Active | LLM routing proxy |
| **PostgreSQL** | ✅ Active | Database |
| **Redis** | ✅ Active | Cache/queue |
| **Traefik** | ✅ Active | Reverse proxy |

---

## 🤖 THE COLONEL - AI AGENT SYSTEM

### Vision

An intelligent AI agent system that knows Ops-Center inside and out, can execute tasks, answer questions, and coordinate across multiple UC-Cloud instances.

### Architecture

```
🎖️ The Colonel (Ecosystem Orchestrator)
    │
    ├─ 🎖️ Lt. Colonel "Atlas" (Ops-Center System Agent)
    │   │
    │   ├─ 👤 Major "Roster" (Users & Orgs Specialist)
    │   ├─ 🤖 Major "Neural" (LLM & AI Specialist)
    │   ├─ 🏗️ Major "Forge" (Infrastructure Specialist)
    │   ├─ 🔗 Major "Link" (Integrations Specialist)
    │   ├─ 📈 Major "Sentinel" (Monitoring Specialist)
    │   └─ 🔐 Major "Guardian" (Security Specialist)
    │
    ├─ 🎖️ Lt. Colonel "Brigade-One" (Brigade System Agent)
    └─ 🎖️ Lt. Colonel "DeepSearch" (Center-Deep System Agent)
```

### Implementation Plan

**Phase 1: Lt. Colonel Atlas (Single Super-Agent)**
- [ ] Create agent definition in Brigade
- [ ] Write comprehensive system prompt covering all Ops-Center sections
- [ ] Implement custom tools:
  - `ops_center_api_query()` - Call any API endpoint
  - `get_system_status()` - Service health and metrics
  - `manage_user()` - User CRUD operations
  - `check_billing()` - Lago/Stripe queries
  - `restart_service()` - Docker management
  - `query_logs()` - Search logs and errors
  - `generate_report()` - Analytics and insights
- [ ] Add chat interface to Ops-Center dashboard
- [ ] Implement context awareness (knows what page user is on)
- [ ] Test with real administrative tasks

**Phase 2: Specialist Majors (Optional - If Needed)**
- [ ] Create 6 specialist agents (Roster, Neural, Forge, Link, Sentinel, Guardian)
- [ ] Implement A2A coordination between Atlas and Majors
- [ ] Parallel task execution
- [ ] Deep domain expertise per section

**Phase 3: The Colonel (Ecosystem Orchestrator)**
- [ ] Create ecosystem-level orchestrator
- [ ] A2A protocol for multi-instance coordination
- [ ] Cross-system task delegation
- [ ] Unified command center

**Timeline**: 1-2 weeks for Phase 1, prioritize before production release

### Why This Matters

1. **User Experience**: Chat with an expert instead of navigating menus
2. **Efficiency**: "Create 5 test users with trial subscriptions" → Done
3. **Troubleshooting**: "Why is service X failing?" → Instant diagnosis
4. **Learning**: Natural language guide through complex workflows
5. **Scalability**: Manage multiple instances from one interface

---

## 💳 LIVE STRIPE TESTING READY

### Current State

- ✅ **Live Stripe API keys** configured (not test mode)
- ✅ **Stripe webhooks** configured and operational
- ✅ **Lago billing** fully integrated
- ✅ **Subscription plans** defined (Trial, Starter, Pro, Enterprise)
- ✅ **Credit system** operational

### What Can Be Tested NOW

1. **Real Subscription Creation**
   - Sign up flow with real payment
   - Stripe checkout integration
   - Webhook-driven account provisioning

2. **Real Credit Purchases**
   - Buy credits with real card
   - Credits added to account
   - Usage tracking and deduction

3. **Real LLM API Calls**
   - Use credits to call OpenAI, Anthropic, etc.
   - Real-time cost tracking
   - Invoice generation

4. **Plan Upgrades/Downgrades**
   - Change subscription tiers
   - Proration handling
   - Immediate access changes

### Testing Plan

**User**: admin@example.com will:
1. Add credits to account (real purchase)
2. Test LLM API calls with real models
3. Verify billing accuracy
4. Test upgrade/downgrade flows

**Expected Result**: Full end-to-end payment and billing workflow functional with real money.

---

## 📋 EPIC TRACKER

### Completed Epics ✅

1. **Epic 1.1** - Local Linux User Management (Oct 22)
2. **Epic 1.2** - Network Configuration (Oct 23)
3. **Epic 1.6** - Cloudflare DNS Management (Oct 24)
4. **Epic 1.7** - NameCheap Migration (Oct 25)
5. **Epic 2.1** - User Management Enhancement (Oct 26)
6. **Epic 3.1** - Billing System Integration (Oct 27)
7. **Epic 3.2** - Unified LLM Management (Oct 28)
8. **Epic 4.1** - Navigation Restructure (Oct 28) 🎉

### Active Epics 🟢

1. **Epic 4.2** - Menu Structure Consolidation (In Planning)
2. **Epic 4.3** - Dashboard Refinement (User requested defer)

### Planned Epics 🟡

1. **Epic 5.1** - Monitoring Tools Integration (Grafana, Prometheus, Umami)
2. **Epic 6.1** - The Colonel AI Agent System (Phase 1)
3. **Epic 6.2** - Specialist Majors (Phase 2 - Optional)
4. **Epic 6.3** - Ecosystem Orchestrator (Phase 3)

---

## 🚀 PRE-RELEASE REQUIREMENTS

### Must-Have Before Production Launch

1. ✅ All core features functional (88% → 90% by end of week)
2. ✅ Live Stripe integration working
3. ✅ User management complete
4. ✅ Billing system operational
5. ✅ LLM infrastructure stable
6. 🟡 Dashboard refined (deferred - will do before launch)
7. 🟡 Lt. Colonel Atlas agent operational
8. 🟡 Forgejo API integration added
9. 🟡 Menu structure optimized
10. ✅ Security audit passed

### Nice-to-Have (Post-Launch)

1. Specialist Major agents (if Atlas needs help)
2. The Colonel ecosystem orchestrator
3. Grafana/Prometheus full integration
4. Advanced analytics dashboards
5. Mobile-optimized views

---

## 📅 TIMELINE

### This Week (Oct 28 - Nov 3)
- [x] Navigation restructure (DONE)
- [x] Platform Settings connection tests fixed (DONE)
- [x] Monitoring section created (DONE)
- [ ] Forgejo API integration added
- [ ] Menu structure consolidation
- [ ] Live Stripe testing with real transactions

### Next Week (Nov 4 - Nov 10)
- [ ] Lt. Colonel Atlas implementation (Phase 1)
- [ ] Chat interface integration
- [ ] Dashboard refinement
- [ ] Section-by-section polish

### Week 3 (Nov 11 - Nov 17)
- [ ] Final testing with real users
- [ ] Performance optimization
- [ ] Security final review
- [ ] Production deployment prep

### Release Target: **November 18, 2025** 🎯

---

## 📝 NOTES

### Priority Order (User Specified)

1. **Immediate**: Fix what's broken, get core working
2. **Short-term**: Menu consolidation, Forgejo, live testing
3. **Pre-launch**: The Colonel agent, dashboard polish
4. **Post-launch**: Advanced features, specialist agents

### Key Decisions

- **Navigation**: Option 2 (enhanced System Settings structure) - IMPLEMENTED
- **AI Agent**: Start with single super-agent (Lt. Col Atlas), add specialists if needed
- **Monitoring**: Placeholder pages created, full implementation post-launch
- **Billing**: Live Stripe keys configured, ready for real transactions

### User Feedback Integration

- ✅ "Get everything fixed now" - Completed platform settings fix
- ✅ "Worry about dashboard later" - Deferred to pre-launch
- ✅ "Should we add Forgejo?" - Added to integration plan
- ✅ "Want The Colonel before release" - Prioritized in Epic 6.1

---

**Next Actions**:
1. Add Forgejo to Integrations → API Credentials
2. Consolidate LLM section pages
3. Begin Lt. Colonel Atlas implementation
4. Test live Stripe transactions with real money

---

*This roadmap is a living document. Updated after each major milestone.*
