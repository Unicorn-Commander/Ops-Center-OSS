# Ops-Center Master Implementation Checklist

**Project:** Complete Billing & Agent Management Integration
**Start Date:** October 14, 2025
**Status:** 🔄 In Progress
**Priority:** High

---

## 📊 Progress Overview

| Phase | Tasks | Completed | Progress |
|-------|-------|-----------|----------|
| Phase 1: Subscription Pages | 12 | 0 | 0% |
| Phase 2: Pricing & Rate Card | 10 | 0 | 0% |
| Phase 3: Agent Management | 8 | 0 | 0% |
| Phase 4: Unicorn Brigade Integration | 15 | 0 | 0% |
| Phase 5: Backend APIs | 18 | 0 | 0% |
| Phase 6: Testing | 12 | 0 | 0% |
| Phase 7: Production | 8 | 0 | 0% |
| **TOTAL** | **83** | **0** | **0%** |

---

## 🎯 PHASE 1: Subscription Pages Wiring (4-6 hours)

**Goal:** Connect existing frontend pages to Lago backend

### Backend Setup
- [ ] 1.1 Check if `/backend/subscription_manager.py` exists
- [ ] 1.2 Create `subscription_manager.py` if missing
- [ ] 1.3 Add Lago API client wrapper functions
  - [ ] `get_customer_subscription(customer_id)`
  - [ ] `get_subscription_usage(customer_id)`
  - [ ] `get_invoices(customer_id)`
  - [ ] `get_payment_methods(customer_id)`
- [ ] 1.4 Test Lago API connectivity
- [ ] 1.5 Add error handling and logging

### Frontend: SubscriptionPlan.jsx
- [ ] 1.6 Wire up to backend API: `GET /api/v1/subscriptions/current`
- [ ] 1.7 Display current tier (Trial, Starter, Professional, Enterprise)
- [ ] 1.8 Show features included in current plan
- [ ] 1.9 Display usage limits and remaining credits
- [ ] 1.10 Add Upgrade/Downgrade buttons → Stripe Checkout
- [ ] 1.11 Test with admin@example.com account

### Frontend: SubscriptionUsage.jsx
- [ ] 1.12 Wire up to backend API: `GET /api/v1/usage/current`
- [ ] 1.13 Display meters:
  - [ ] `llm.input_tok` (input tokens used)
  - [ ] `llm.output_tok` (output tokens used)
  - [ ] `agent.meter_tok` (agent tokens metered)
  - [ ] `tool.web.request` (web searches)
- [ ] 1.14 Add progress bars showing usage vs limits
- [ ] 1.15 Add historical usage charts (last 30 days)
- [ ] 1.16 Add export usage data button (CSV)

### Frontend: SubscriptionBilling.jsx
- [ ] 1.17 Wire up to backend API: `GET /api/v1/billing/invoices`
- [ ] 1.18 Display invoice table with columns:
  - [ ] Date, Amount, Status, Actions
- [ ] 1.19 Add status badges (Paid, Pending, Failed)
- [ ] 1.20 Add download PDF button per invoice
- [ ] 1.21 Add retry payment button for failed invoices
- [ ] 1.22 Add pagination for invoice history

### Frontend: SubscriptionPayment.jsx
- [ ] 1.23 Wire up to Stripe API: `GET /api/v1/billing/payment-methods`
- [ ] 1.24 Display saved payment methods (masked cards)
- [ ] 1.25 Add Stripe Elements for adding new card
- [ ] 1.26 Add remove payment method button
- [ ] 1.27 Add set default payment method toggle
- [ ] 1.28 Test with Stripe test cards (4242 4242 4242 4242)

---

## 💰 PHASE 2: Pricing & Rate Card UI (6-8 hours)

**Goal:** Build admin interface to configure LLM + Agent pricing

### Backend: Rate Card API
- [ ] 2.1 Create `/backend/rate_card_api.py`
- [ ] 2.2 Create PostgreSQL table: `pricing_rules`
  ```sql
  CREATE TABLE pricing_rules (
    id UUID PRIMARY KEY,
    provider VARCHAR(50),  -- 'openai', 'anthropic', 'house_vllm'
    model_name VARCHAR(100),
    input_cost_per_1k DECIMAL(10,6),
    output_cost_per_1k DECIMAL(10,6),
    markup_percent DECIMAL(5,2),
    byok_enabled BOOLEAN DEFAULT true,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
  );
  ```
- [ ] 2.3 Create table: `agent_pricing`
  ```sql
  CREATE TABLE agent_pricing (
    id UUID PRIMARY KEY,
    agent_name VARCHAR(100),
    agent_rate_per_1k DECIMAL(10,6),
    min_agent_fee DECIMAL(10,4),
    description TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
  );
  ```
- [ ] 2.4 Create table: `tool_pricing`
  ```sql
  CREATE TABLE tool_pricing (
    id UUID PRIMARY KEY,
    tool_name VARCHAR(100),
    unit_price DECIMAL(10,6),
    unit_type VARCHAR(50),  -- 'request', 'image', 'second'
    active BOOLEAN DEFAULT true
  );
  ```
- [ ] 2.5 Add API endpoints:
  - [ ] `GET /api/v1/pricing/rate-card` - Get all pricing rules
  - [ ] `PUT /api/v1/pricing/rate-card` - Update pricing rules
  - [ ] `POST /api/v1/pricing/llm-routes` - Add new LLM route
  - [ ] `GET /api/v1/pricing/agents` - Get agent pricing
  - [ ] `PUT /api/v1/pricing/agents/:id` - Update agent pricing
  - [ ] `GET /api/v1/pricing/tools` - Get tool pricing
- [ ] 2.6 Add rate card YAML export endpoint: `GET /api/v1/pricing/export`

### Frontend: RateCard.jsx
- [ ] 2.7 Create `/src/pages/RateCard.jsx`
- [ ] 2.8 Add to navigation: `/admin/system/rate-card`
- [ ] 2.9 Build LLM Pricing Table:
  - [ ] Columns: Provider, Model, Input Cost, Output Cost, Markup %, Final Price
  - [ ] Add/Edit/Delete rows
  - [ ] BYOK toggle per provider
  - [ ] Calculate final customer price automatically
- [ ] 2.10 Build Agent Pricing Section:
  - [ ] Default agent rate input
  - [ ] Per-agent overrides table
  - [ ] Minimum agent fee per job
- [ ] 2.11 Build Tool Pricing Section:
  - [ ] List tool types (web search, image processing, etc.)
  - [ ] Price per unit
  - [ ] Enable/disable toggles
- [ ] 2.12 Add Export Rate Card button (YAML download)
- [ ] 2.13 Add Import Rate Card button (YAML upload)
- [ ] 2.14 Add Save Changes button with confirmation
- [ ] 2.15 Test with sample pricing data

### Seed Data
- [ ] 2.16 Create default pricing rules:
  - [ ] OpenAI GPT-4: $0.03 input, $0.06 output, 25% markup
  - [ ] Anthropic Claude: $0.015 input, $0.075 output, 25% markup
  - [ ] House vLLM: $0.002 input, $0.004 output, 300% markup
- [ ] 2.17 Create default agent pricing:
  - [ ] Default: $0.005 per 1K tokens
  - [ ] Research Pro: $0.008 per 1K tokens
  - [ ] Code Generator: $0.006 per 1K tokens

---

## 🤖 PHASE 3: Agent Management UI (4-6 hours)

**Goal:** Configure per-agent settings in Ops Center

### Backend: Agent Management API
- [ ] 3.1 Create `/backend/agent_manager.py`
- [ ] 3.2 Add API endpoints:
  - [ ] `GET /api/v1/agents` - List all agents
  - [ ] `GET /api/v1/agents/:id` - Get agent details
  - [ ] `PUT /api/v1/agents/:id` - Update agent config
  - [ ] `POST /api/v1/agents/:id/enable` - Enable agent
  - [ ] `POST /api/v1/agents/:id/disable` - Disable agent
  - [ ] `GET /api/v1/agents/:id/usage` - Get agent usage stats
- [ ] 3.3 Integrate with agent_pricing table

### Frontend: AgentManagement.jsx
- [ ] 3.4 Create `/src/pages/AgentManagement.jsx`
- [ ] 3.5 Add to navigation: `/admin/system/agents`
- [ ] 3.6 Build agent list table:
  - [ ] Columns: Name, Status, Rate, Usage, Actions
  - [ ] Enable/Disable toggle per agent
  - [ ] Edit pricing button
- [ ] 3.7 Add agent configuration modal:
  - [ ] Agent rate per 1K tokens
  - [ ] Minimum fee per job
  - [ ] Description
  - [ ] Active toggle
- [ ] 3.8 Add usage analytics section:
  - [ ] Total requests per agent
  - [ ] Total tokens processed
  - [ ] Revenue generated
  - [ ] Charts showing usage over time

---

## 🦄 PHASE 4: Unicorn Brigade Integration (8-10 hours)

**Goal:** Integrate Unicorn Brigade agent orchestration with Ops Center billing

### Setup Unicorn Brigade
- [ ] 4.1 Clone/update Unicorn Brigade repository
  ```bash
  cd /home/muut/Production/UC-Cloud
  git clone https://github.com/Unicorn-Commander/Unicorn-Brigade.git
  ```
- [ ] 4.2 Review Unicorn Brigade architecture
- [ ] 4.3 Add to docker-compose.yml
  ```yaml
  unicorn-brigade:
    build: ./Unicorn-Brigade
    ports:
      - "8100:8100"
    networks:
      - unicorn-network
    environment:
      - OPS_CENTER_URL=http://ops-center-direct:8000
  ```
- [ ] 4.4 Start Unicorn Brigade service

### Configuration Integration
- [ ] 4.5 Create Ops Center → Unicorn Brigade API client
- [ ] 4.6 Unicorn Brigade fetches rate card on startup:
  - [ ] `GET http://ops-center-direct:8000/api/v1/pricing/rate-card`
- [ ] 4.7 Unicorn Brigade fetches agent config:
  - [ ] `GET http://ops-center-direct:8000/api/v1/agents`
- [ ] 4.8 Add rate card refresh endpoint in Brigade:
  - [ ] `POST /api/v1/config/refresh` - Reload from Ops Center

### Usage Reporting
- [ ] 4.9 Unicorn Brigade posts usage after each job:
  ```python
  POST http://ops-center-direct:8000/api/v1/usage/record
  {
    "customer_id": "uuid",
    "agent_name": "research_pro",
    "input_tokens": 6000,
    "output_tokens": 2000,
    "tools_used": [
      {"tool": "web.search", "units": 3}
    ],
    "route_used": "openai:gpt-4",
    "byok_used": false
  }
  ```
- [ ] 4.10 Ops Center calculates pricing:
  - [ ] LLM_fee = (input * rate_in + output * rate_out) * (1 + markup)
  - [ ] Agent_fee = (input + output) * agent_rate / 1000
  - [ ] Tools_fee = Σ (tool_unit_price * units)
  - [ ] Total = LLM_fee + Agent_fee + Tools_fee
- [ ] 4.11 Ops Center posts to Lago:
  ```python
  lago.record_usage(
    customer_id=customer_id,
    meters={
      "llm.input_tok": 6000,
      "llm.output_tok": 2000,
      "agent.meter_tok": 8000,
      "tool.web.request": 3
    }
  )
  ```

### LiteLLM Middleware
- [ ] 4.12 Create pricing calculation middleware in Unicorn Brigade
- [ ] 4.13 Implement routing logic:
  - [ ] Check BYOK first (user's keys)
  - [ ] Fall back to House models (highest margin)
  - [ ] Use Frontier models (OpenAI, Anthropic) as last resort
- [ ] 4.14 Add job ceiling enforcement (max cost per job)
- [ ] 4.15 Add pre-job estimate calculation:
  ```python
  def estimate_job_cost(agent, estimated_tokens, tools):
      llm_fee = estimate_llm_cost(estimated_tokens)
      agent_fee = estimated_tokens * agent_rate / 1000
      tools_fee = estimate_tools_cost(tools)
      return llm_fee + agent_fee + tools_fee
  ```

### Testing Integration
- [ ] 4.16 Test agent request flow end-to-end:
  - [ ] User sends request to Unicorn Brigade
  - [ ] Brigade fetches pricing from Ops Center
  - [ ] Brigade executes agent job
  - [ ] Brigade posts usage to Ops Center
  - [ ] Ops Center posts to Lago
  - [ ] Verify Lago invoice reflects usage
- [ ] 4.17 Test BYOK flow:
  - [ ] User with BYOK enabled
  - [ ] Verify LLM_fee = 0
  - [ ] Verify Agent_fee still charged
- [ ] 4.18 Test routing preferences:
  - [ ] BYOK → House → Frontier order
  - [ ] Verify highest margin route selected
- [ ] 4.19 Test job ceiling enforcement
- [ ] 4.20 Test rate card hot reload (update in Ops Center, Brigade picks up)

---

## 🔧 PHASE 5: Backend API Implementation (6-8 hours)

**Goal:** Implement missing backend APIs for frontend pages

### Account APIs
- [ ] 5.1 Create `/backend/profile_api.py`
- [ ] 5.2 Add endpoints:
  - [ ] `GET /api/v1/auth/profile` - Get user profile
  - [ ] `PUT /api/v1/auth/profile` - Update name, email, avatar
  - [ ] `POST /api/v1/auth/profile/avatar` - Upload avatar image
  - [ ] `GET /api/v1/auth/notifications` - Get notification preferences
  - [ ] `PUT /api/v1/auth/notifications` - Update notification settings
  - [ ] `PUT /api/v1/auth/password` - Change password
  - [ ] `GET /api/v1/auth/sessions` - List active sessions
  - [ ] `DELETE /api/v1/auth/sessions/:id` - Revoke session

### Organization APIs
- [ ] 5.3 Create `/backend/org_api.py`
- [ ] 5.4 Add endpoints:
  - [ ] `GET /api/v1/org/members` - List team members
  - [ ] `POST /api/v1/org/members` - Invite team member
  - [ ] `PUT /api/v1/org/members/:id` - Update member role
  - [ ] `DELETE /api/v1/org/members/:id` - Remove member
  - [ ] `GET /api/v1/org/stats` - Organization statistics
  - [ ] `GET /api/v1/org/roles` - List available roles
  - [ ] `GET /api/v1/org/settings` - Get org settings
  - [ ] `PUT /api/v1/org/settings` - Update org settings
  - [ ] `POST /api/v1/org/settings/logo` - Upload org logo
  - [ ] `GET /api/v1/org/billing` - Get org billing info (owner only)

### Usage Tracking APIs
- [ ] 5.5 Create `/backend/usage_tracker.py`
- [ ] 5.6 Add endpoints:
  - [ ] `POST /api/v1/usage/record` - Record usage from Unicorn Brigade
  - [ ] `GET /api/v1/usage/current` - Get current period usage
  - [ ] `GET /api/v1/usage/history` - Get historical usage
  - [ ] `GET /api/v1/usage/export` - Export usage data (CSV)
  - [ ] `GET /api/v1/usage/breakdown` - Usage by service/agent

### Integration with Existing Systems
- [ ] 5.7 Wire profile APIs to Keycloak user attributes
- [ ] 5.8 Wire org APIs to Keycloak groups/roles
- [ ] 5.9 Wire usage APIs to Lago meters
- [ ] 5.10 Add authentication middleware to all new endpoints
- [ ] 5.11 Add rate limiting to prevent abuse
- [ ] 5.12 Add audit logging for sensitive operations

---

## 🧪 PHASE 6: Testing & Validation (4-6 hours)

**Goal:** Comprehensive testing of all new features

### Unit Tests
- [ ] 6.1 Test rate card API endpoints
- [ ] 6.2 Test pricing calculation logic
- [ ] 6.3 Test usage recording
- [ ] 6.4 Test Lago integration
- [ ] 6.5 Test Stripe integration

### Integration Tests
- [ ] 6.6 Test complete subscription flow:
  - [ ] New user signup
  - [ ] Select plan (Trial)
  - [ ] Payment via Stripe
  - [ ] Subscription activated in Lago
  - [ ] User can access services
- [ ] 6.7 Test usage metering flow:
  - [ ] User makes API call via Unicorn Brigade
  - [ ] Usage recorded in Ops Center
  - [ ] Usage posted to Lago
  - [ ] Usage visible in SubscriptionUsage.jsx
- [ ] 6.8 Test billing flow:
  - [ ] User exceeds included usage
  - [ ] Overage charges calculated
  - [ ] Invoice generated by Lago
  - [ ] Invoice visible in SubscriptionBilling.jsx
  - [ ] Payment processed via Stripe
- [ ] 6.9 Test BYOK flow:
  - [ ] User adds OpenAI API key
  - [ ] User makes API call
  - [ ] LLM_fee = 0
  - [ ] Agent_fee charged
  - [ ] Total cost correct
- [ ] 6.10 Test rate card updates:
  - [ ] Admin updates pricing in Ops Center
  - [ ] Unicorn Brigade refreshes config
  - [ ] New pricing applied to next job

### End-to-End Tests
- [ ] 6.11 Test as regular user (no admin):
  - [ ] Signup + payment
  - [ ] Use services
  - [ ] View usage
  - [ ] View billing
  - [ ] Upgrade plan
- [ ] 6.12 Test as platform admin:
  - [ ] Configure rate card
  - [ ] Configure agent pricing
  - [ ] View all users' usage
  - [ ] Manage subscriptions

---

## 🚀 PHASE 7: Production Deployment (2-3 hours)

**Goal:** Deploy to production environment

### Pre-Deployment
- [ ] 7.1 Create production backup:
  ```bash
  cd /home/muut/Production/UC-Cloud/services/ops-center
  tar -czf /home/muut/backups/ops-center-backup-$(date +%Y%m%d-%H%M%S).tar.gz .
  ```
- [ ] 7.2 Review all environment variables
- [ ] 7.3 Switch Stripe to live mode (when ready)
- [ ] 7.4 Update Keycloak OAuth redirect URIs for production
- [ ] 7.5 Set up monitoring alerts (Grafana)

### Build & Deploy
- [ ] 7.6 Build React frontend:
  ```bash
  npm run build
  ```
- [ ] 7.7 Restart ops-center container:
  ```bash
  docker-compose restart ops-center-direct
  ```
- [ ] 7.8 Restart Unicorn Brigade:
  ```bash
  docker-compose restart unicorn-brigade
  ```
- [ ] 7.9 Verify all services healthy:
  ```bash
  docker ps | grep unicorn
  ```

### Post-Deployment Verification
- [ ] 7.10 Test login flow
- [ ] 7.11 Test subscription pages load
- [ ] 7.12 Test rate card admin interface
- [ ] 7.13 Test agent management
- [ ] 7.14 Test Unicorn Brigade integration
- [ ] 7.15 Monitor logs for errors:
  ```bash
  docker logs ops-center-direct -f
  docker logs unicorn-brigade -f
  ```

### Documentation
- [ ] 7.16 Update CLAUDE.md with new features
- [ ] 7.17 Create user guide for subscription management
- [ ] 7.18 Create admin guide for rate card configuration
- [ ] 7.19 Document Unicorn Brigade integration
- [ ] 7.20 Update API documentation

---

## 🎯 Quick Wins (Do First)

High-impact, low-effort tasks to do immediately:

- [ ] **QW1**: Test current subscription status with Lago API
- [ ] **QW2**: Display current plan in SubscriptionPlan.jsx
- [ ] **QW3**: Create basic rate card table (read-only)
- [ ] **QW4**: Test usage posting to Lago manually
- [ ] **QW5**: Verify Stripe webhook receiving events

---

## 📝 Notes & Decisions

### Architecture Decisions
1. **Rate Card Storage**: PostgreSQL in Ops Center (not YAML files)
   - Reason: Dynamic updates, audit trail, API access
2. **Agent Config**: Ops Center owns, Unicorn Brigade reads
   - Reason: Centralized control, consistent pricing
3. **BYOK Pricing**: Agent fee always charged, LLM fee = 0
   - Reason: Platform value, sustainable revenue
4. **Usage Flow**: Brigade → Ops Center → Lago
   - Reason: Ops Center as billing source of truth

### Open Questions
- [ ] Should agent config live in Ops Center or Unicorn Brigade?
  - **Decision**: Ops Center (centralized management)
- [ ] How to handle rate card updates? Hot reload or restart?
  - **Decision**: Hot reload via API endpoint
- [ ] Where to display agent usage analytics?
  - **Decision**: Both Ops Center admin + Unicorn Brigade dashboard

---

## 🐛 Known Issues

### Current Blockers
- None

### Future Enhancements
1. Add forecasting for usage/costs
2. Add budget alerts (email when approaching limit)
3. Add team seat management
4. Add custom plan creation
5. Add usage export (CSV, PDF)
6. Add Grafana dashboard for billing metrics

---

## 📞 Support Resources

### Documentation
- Lago API: https://doc.getlago.com/api-reference/intro
- Stripe API: https://stripe.com/docs/api
- Unicorn Brigade: https://github.com/Unicorn-Commander/Unicorn-Brigade

### Local Docs
- `/docs/LAGO_SETUP_CHECKLIST.md`
- `/docs/BILLING_ARCHITECTURE_FINAL.md`
- `/IMPLEMENTATION-COMPLETE.md`
- `/backend/docs/API-ENDPOINT-COVERAGE.md`

### Access
- Lago Dashboard: https://billing.your-domain.com
- Stripe Dashboard: https://dashboard.stripe.com/test
- Keycloak Admin: https://auth.your-domain.com/admin/uchub/console/

---

**Last Updated:** October 14, 2025
**Next Review:** After Phase 1 completion
**Owner:** Aaron / Claude Assistant
