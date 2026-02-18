# Epic 3.1: LiteLLM Multi-Provider Routing - Executive Summary

**Document**: EPIC_3.1_ARCHITECTURE.md (2,391 lines, 97 pages)
**Date**: October 23, 2025
**Status**: Design Complete - Ready for Implementation

---

## What We're Building

A comprehensive multi-provider LLM routing system that allows users to:

1. **Bring Your Own Key (BYOK)** - Use their own OpenAI, Anthropic, Together, etc. API keys
2. **Power Level Selection** - Choose between Eco (cheap), Balanced, or Precision (quality) modes
3. **Automatic Routing** - System intelligently routes to best provider based on cost/latency/quality
4. **Automatic Fallback** - If primary provider fails, automatically try backup providers
5. **Usage Tracking** - Track all LLM usage for billing and analytics

---

## Architecture Overview

### Component Diagram

```
User Browser
    │
    ▼
Frontend (React)
    │
    ▼
Backend API (FastAPI)
    │
    ├──> PostgreSQL (6 new tables)
    ├──> Redis (caching + rate limits)
    ├──> SecretManager (Fernet encryption)
    │
    ▼
LiteLLM Proxy
    │
    ├──> OpenRouter (100+ models)
    ├──> OpenAI (user BYOK)
    ├──> Anthropic (user BYOK)
    ├──> Together AI
    ├──> Groq (free)
    └──> Local vLLM
```

### Data Flow: User Makes Request

```
1. User submits prompt in chat UI
2. Backend checks user's power level (Eco/Balanced/Precision)
3. Backend checks if user has BYOK keys
4. Routing Engine scores all available providers
5. Selects best provider (cost + latency + quality)
6. Forwards request to LiteLLM proxy
7. If primary fails → automatically tries fallback
8. Returns response + metadata (cost, provider used)
9. Logs usage for billing
```

---

## Database Schema (6 New Tables)

### 1. `llm_providers` - Platform providers (admin-managed)
- OpenRouter, OpenAI, Anthropic, Together, Groq, Local
- Encrypted API keys (platform keys)
- Health status tracking

### 2. `llm_models` - Model catalog
- Model name, cost per 1M tokens, context length
- Average latency, quality score
- 50+ models configured

### 3. `user_provider_keys` - User BYOK keys
- Encrypted user API keys (Fernet)
- One key per provider per user
- Enable/disable toggle

### 4. `llm_routing_rules` - Global routing config
- Strategy: cost, latency, balanced, custom
- Cost/latency/quality weights
- Fallback order

### 5. `user_llm_settings` - User preferences
- Power level (eco, balanced, precision)
- Credit balance
- Monthly spending cap

### 6. `llm_usage_logs` - Usage tracking
- Every LLM request logged
- Tokens used, cost incurred
- Provider used, latency

---

## API Endpoints (20+ New)

### Admin Endpoints

**Provider Management**:
- `GET /api/v1/llm/providers` - List providers
- `POST /api/v1/llm/providers` - Add provider
- `PUT /api/v1/llm/providers/{id}` - Update provider
- `DELETE /api/v1/llm/providers/{id}` - Delete provider
- `POST /api/v1/llm/test` - Test provider connection

**Model Management**:
- `GET /api/v1/llm/models` - List models
- `POST /api/v1/llm/models` - Add model

**Routing Rules**:
- `GET /api/v1/llm/routing/rules` - Get routing config
- `PUT /api/v1/llm/routing/rules` - Update routing config

### User Endpoints

**BYOK Management**:
- `POST /api/v1/llm/users/{id}/byok` - Add API key
- `GET /api/v1/llm/users/{id}/byok` - List keys (masked)
- `DELETE /api/v1/llm/users/{id}/byok/{provider}` - Delete key

**LLM Requests**:
- `POST /api/v1/llm/chat/completions` - OpenAI-compatible chat endpoint
- `GET /api/v1/llm/models` - List available models
- `GET /api/v1/llm/credits` - Check credit balance

**Analytics**:
- `GET /api/v1/llm/usage` - Usage statistics
- `GET /api/v1/llm/usage/export` - Export CSV

---

## Frontend Components (8 New Pages)

### Admin Pages

1. **Provider Management** (`/admin/llm/providers`)
   - Grid of provider cards
   - Add/edit/test providers
   - Health status indicators

2. **Model Management** (`/admin/llm/models`)
   - List of models with costs
   - Add/edit models
   - Enable/disable models

3. **Routing Configuration** (`/admin/llm/routing`)
   - Select routing strategy
   - Adjust cost/latency/quality weights
   - Configure fallback order

### User Pages

4. **BYOK Manager** (`/account/llm/byok`)
   - Add API keys for OpenAI, Anthropic, etc.
   - View masked keys
   - Enable/disable keys

5. **Power Level Selector** (`/account/llm/settings`)
   - Choose Eco, Balanced, or Precision
   - Set monthly spending cap
   - Configure preferences

6. **Usage Dashboard** (`/account/subscription/usage`)
   - Charts showing usage over time
   - Cost breakdown by provider
   - Export usage data

---

## Security Architecture

### Encryption Strategy

**Fernet (AES-128-CBC) encryption** for all API keys:
```python
# Generate master key (one-time)
BYOK_ENCRYPTION_KEY=ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=

# Encrypt API key before storage
cipher = Fernet(BYOK_ENCRYPTION_KEY)
encrypted = cipher.encrypt("sk-abc123...".encode())

# Decrypt API key before use
decrypted = cipher.decrypt(encrypted).decode()
```

### Access Control

- **Platform API Keys**: Admin write, all users use (encrypted)
- **User BYOK Keys**: Owner only (write/read), backend can decrypt for routing
- **Row-level security** on `user_provider_keys` table

### Audit Logging

All key operations logged:
- `byok_key_added`
- `byok_key_updated`
- `byok_key_deleted`
- `byok_key_accessed` (sampled)

### Rate Limiting

Per-tier limits enforced:
```
Trial:        10/min,  100/hour,    500/day
Starter:      30/min, 1000/hour,  10000/day
Professional: 100/min, 5000/hour, 50000/day
Enterprise:   500/min, 20000/hour, unlimited
```

---

## Routing Logic (WilmerAI-style)

### Power Level Configurations

**Eco** (Cost-optimized):
```
Max Cost: $0.001 per 1K tokens
Preferred: Local, Groq, HuggingFace (free)
Scoring: Cost 70%, Latency 20%, Quality 10%
```

**Balanced** (Default):
```
Max Cost: $0.01 per 1K tokens
Preferred: OpenRouter, Together, Fireworks
Scoring: Cost 40%, Latency 40%, Quality 20%
```

**Precision** (Quality-optimized):
```
Max Cost: $0.10 per 1K tokens
Preferred: OpenAI, Anthropic, OpenRouter Premium
Scoring: Cost 10%, Latency 30%, Quality 60%
```

### Scoring Algorithm

```python
def score_provider(model, power_level):
    weights = get_weights(power_level)

    cost_score = 1.0 - (model.cost / max_cost)
    latency_score = 1.0 - (model.latency / max_latency)
    quality_score = model.quality_rating

    composite_score = (
        weights.cost * cost_score +
        weights.latency * latency_score +
        weights.quality * quality_score
    )

    # Apply penalties for recent errors or rate limits
    composite_score *= (1.0 - error_rate * 0.5)

    return composite_score
```

### Fallback Strategy

```
1. Try Primary Provider (highest score)
   ↓ (if fails)
2. Try Fallback #1 (second highest score)
   ↓ (if fails)
3. Try Fallback #2 (third highest score)
   ↓ (if fails)
4. Return Error "All providers unavailable"
```

**Fallback Triggers**:
- Rate limit exceeded (429)
- Authentication failed (401)
- Timeout (504)
- Internal server error (500)

---

## Integration Points

### Keycloak SSO
- All API endpoints require Keycloak JWT
- User ID extracted from token
- BYOK keys tied to Keycloak user

### Lago Billing
- LLM usage events sent to Lago
- Credit balance synced from subscriptions
- Monthly spending caps enforced

### PostgreSQL
- All tables in shared `unicorn_db`
- Reuse existing connection pool
- Foreign key constraints

### Redis
- Cache routing rules (60s TTL)
- Cache provider health (5min TTL)
- Rate limiting (sliding window)

### LiteLLM Proxy
- OpenAI-compatible API
- Dynamic provider selection
- User API key injection (BYOK)

---

## Deployment

### Docker Services

**No new containers** - All functionality in existing `ops-center-direct`

### Environment Variables (New)

```bash
# .env.auth
LITELLM_PROXY_URL=http://unicorn-litellm-wilmer:4000
LITELLM_MASTER_KEY=<generated-secret>
BYOK_ENCRYPTION_KEY=<generated-fernet-key>

# Platform API Keys
OPENROUTER_API_KEY=<platform-key>
OPENAI_API_KEY=<platform-key>
ANTHROPIC_API_KEY=<platform-key>
TOGETHER_API_KEY=<platform-key>

# Feature Flags
FEATURE_BYOK_ENABLED=true
FEATURE_POWER_LEVELS_ENABLED=true
FEATURE_AUTO_FALLBACK_ENABLED=true
```

### Database Migration

```bash
# Run migration script
docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db < backend/migrations/003_llm_routing.sql

# Verify tables created
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt llm_*"
```

### Restart Services

```bash
# Restart ops-center with new config
docker restart ops-center-direct

# Test API
curl http://localhost:8084/api/v1/llm/providers
```

---

## Monitoring & Alerting

### Prometheus Metrics

```
llm_requests_total{provider, model, power_level, status}
llm_request_duration_seconds{provider, model}
llm_tokens_total{provider, model, type}
llm_cost_total{provider, model, power_level}
llm_provider_health{provider}
llm_fallbacks_total{primary_provider, fallback_provider, reason}
```

### Grafana Dashboard

Panels:
1. Requests per Provider (line chart)
2. Average Latency (histogram)
3. Cost per Provider (bar chart)
4. Provider Health (status panel)
5. Fallback Rate (line chart)

### Alerts

- **ProviderUnhealthy**: Provider down for 5+ minutes
- **HighFallbackRate**: Fallback rate > 10% for 10+ minutes
- **HighCost**: LLM costs > $10/hour

---

## Implementation Timeline

**Total Estimate**: 3-4 weeks (4-5 developer-days)

### Phase 1: Backend (1 week)
- [ ] Database schema migration
- [ ] API endpoints (20+ endpoints)
- [ ] Routing engine logic
- [ ] BYOK encryption/decryption
- [ ] Unit tests

### Phase 2: Frontend (1 week)
- [ ] Provider Management UI (admin)
- [ ] Model Management UI (admin)
- [ ] Routing Config UI (admin)
- [ ] BYOK Manager UI (user)
- [ ] Power Level Selector UI (user)
- [ ] Usage Dashboard UI (user)

### Phase 3: Integration (1 week)
- [ ] LiteLLM proxy configuration
- [ ] Dynamic provider injection
- [ ] Fallback logic testing
- [ ] End-to-end testing
- [ ] Performance testing

### Phase 4: Deployment (3 days)
- [ ] Production database migration
- [ ] Environment variable setup
- [ ] Service restart
- [ ] Monitoring dashboard setup
- [ ] Alert configuration
- [ ] User documentation

---

## Success Criteria

### Functional Requirements
- ✅ Users can add BYOK API keys securely
- ✅ Users can select power levels (Eco, Balanced, Precision)
- ✅ Automatic routing based on cost/latency/quality scoring
- ✅ Automatic fallback when providers fail
- ✅ Usage tracking and analytics
- ✅ Admin can manage providers and models

### Security Requirements
- ✅ All API keys encrypted (Fernet AES-128)
- ✅ Audit logging for all key operations
- ✅ Rate limiting per user/tier
- ✅ Row-level security on BYOK keys
- ✅ HTTPS for all API requests

### Performance Requirements
- ✅ Provider scoring < 50ms
- ✅ Fallback decision < 100ms
- ✅ End-to-end request < 5s (including LLM)
- ✅ Support 100+ concurrent users

### User Experience Requirements
- ✅ Intuitive BYOK key management
- ✅ Clear power level descriptions
- ✅ Real-time usage analytics
- ✅ Transparent cost tracking

---

## Key Benefits

### For Users

1. **Cost Savings**: Use own API keys → pay only 10% platform fee
2. **Flexibility**: Choose power level based on task importance
3. **Transparency**: See exactly which provider was used and cost
4. **Reliability**: Automatic fallback if provider fails
5. **Control**: Enable/disable providers as needed

### For Platform

1. **Reduced Costs**: Users with BYOK reduce platform API costs
2. **Increased Revenue**: Attract enterprise customers who want BYOK
3. **Better UX**: Intelligent routing improves response times
4. **Scalability**: Distribute load across multiple providers
5. **Observability**: Complete visibility into LLM usage

---

## Risk Mitigation

### Technical Risks

**Risk**: Encryption key compromise
**Mitigation**: Key rotation procedure, audit logging

**Risk**: Provider outages
**Mitigation**: Multi-provider fallback, health checks

**Risk**: Rate limits
**Mitigation**: Per-tier limits, Redis rate limiting

### Business Risks

**Risk**: Users over-consume credits
**Mitigation**: Monthly spending caps, usage alerts

**Risk**: Provider cost increases
**Mitigation**: Regular pricing updates, cost monitoring

---

## Documentation

### Technical Documentation
- `EPIC_3.1_ARCHITECTURE.md` - Complete technical specification (this document)
- `backend/migrations/003_llm_routing.sql` - Database migration
- `backend/litellm_routing_api.py` - API implementation
- `backend/byok_manager.py` - BYOK encryption logic

### User Documentation
- User Guide: "How to Add Your Own API Keys (BYOK)"
- User Guide: "Choosing the Right Power Level"
- Admin Guide: "Managing LLM Providers"
- Admin Guide: "Configuring Routing Rules"

### API Documentation
- OpenAPI specification for all endpoints
- Example requests/responses
- Error code reference
- Rate limit documentation

---

## Questions & Decisions

### Decisions Made

1. **Encryption**: Fernet (AES-128-CBC) for BYOK keys ✓
2. **Routing Strategy**: WilmerAI-style cost/latency/quality scoring ✓
3. **Fallback**: Automatic with configurable max retries ✓
4. **Storage**: PostgreSQL for all tables ✓
5. **Caching**: Redis for routing rules and health status ✓

### Open Questions

1. **Credit Purchase**: Should users be able to buy credits directly?
   - **Recommendation**: Yes, via Stripe integration (existing billing system)

2. **Provider Auto-Discovery**: Should we auto-discover new models from OpenRouter?
   - **Recommendation**: Yes, background job runs daily to sync models

3. **Usage Caps**: Should we enforce hard caps or soft caps with warnings?
   - **Recommendation**: Soft caps with warnings, hard caps for abusers

4. **BYOK Validation**: Should we validate keys before saving?
   - **Recommendation**: Yes, test with minimal request (5 tokens)

5. **Multi-Tenancy**: Should organizations share BYOK keys?
   - **Recommendation**: Phase 2 feature, not in initial release

---

## Next Steps

1. **Review Architecture** - Engineering team review (1 day)
2. **Create Jira Tickets** - Break into implementation tasks (1 day)
3. **Set Up Dev Environment** - Database migration in staging (1 day)
4. **Begin Phase 1** - Backend implementation (1 week)
5. **Weekly Check-ins** - Review progress and blockers

---

**Document Status**: Ready for Implementation
**Approval Required From**: Engineering Lead, Product Manager
**Expected Start Date**: Week of October 28, 2025
**Expected Completion**: Week of November 18, 2025

---

## Contact

**Architecture Designer**: System Architecture Team
**Technical Lead**: Backend Developer #1
**Product Owner**: Product Manager
**Stakeholders**: Engineering, Product, Operations teams

**Questions?** Review full architecture: `EPIC_3.1_ARCHITECTURE.md`
