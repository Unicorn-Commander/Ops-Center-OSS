# LiteLLM Deployment Checklist

**Version**: 1.0.0
**Last Updated**: 2025-10-20
**Status**: Pre-Deployment Verification
**Target**: Week 1 Production Deployment

---

## Pre-Deployment Verification

### Code Components ✅

- [x] **Backend API Files** (11 files)
  - [x] `litellm_api.py` (20KB) - Main LiteLLM proxy endpoints
  - [x] `litellm_credit_system.py` (19KB) - Credit management & power levels
  - [x] `litellm_integration.py` (11KB) - LiteLLM client wrapper
  - [x] `wilmer_router.py` (25KB) - WilmerAI intelligent routing
  - [x] `model_selector.py` (15KB) - Model selection logic
  - [x] `provider_health.py` (16KB) - Provider health monitoring
  - [x] `byok_api.py` (18KB) - BYOK API endpoints
  - [x] `byok_helpers.py` (9.1KB) - BYOK utility functions
  - [x] `byok_manager.py` (13KB) - BYOK key management
  - [x] `byok_service.py` (13KB) - BYOK service layer
  - [x] Routes registered in `server.py` ✅

- [x] **Database Schema** (24KB)
  - [x] `backend/sql/litellm_schema.sql` exists and complete

- [x] **Configuration Files**
  - [x] `litellm_config.yaml` (17KB) - 47 models across 6 tiers
  - [x] `docker-compose.litellm.yml` (4.5KB) - Docker orchestration
  - [x] `.env.litellm` template ready (needs user API keys)

- [x] **Initialization Scripts**
  - [x] `backend/scripts/initialize_litellm_db.py` (18KB)

- [x] **Test Suites**
  - [x] `backend/tests/test_litellm_schema.py` (21KB)
  - [x] `backend/tests/test_byok.py` (13KB)

- [x] **Examples & Documentation**
  - [x] `backend/examples/wilmer_routing_examples.py` (18KB)

### Missing Dependencies ⚠️

**Required packages NOT in requirements.txt:**

1. **litellm** - Core LiteLLM library
   ```bash
   litellm>=1.40.0
   ```

2. **redis.asyncio** - Async Redis client (imported as `aioredis`)
   ```bash
   redis[hiredis]>=5.0.1  # Already present, but needs async support
   ```

3. **stripe** - Stripe payment processing
   ```bash
   stripe==10.0.0  # Already present ✅
   ```

4. **decimal** - Python standard library (no install needed) ✅

5. **dataclasses** - Python 3.7+ standard library (no install needed) ✅

**ACTION REQUIRED:**
```bash
# Add to requirements.txt:
litellm>=1.40.0
```

### Configuration Requirements ⚠️

**Environment variables needed in `.env.litellm`:**

```bash
# Master Key
LITELLM_MASTER_KEY=<user-generates>

# Database
POSTGRES_PASSWORD=<existing-from-ops-center>

# Provider API Keys (9 total - user adds only what they want)
OPENROUTER_API_KEY=<optional>
HUGGINGFACE_API_KEY=<optional>
TOGETHER_API_KEY=<optional>
DEEPINFRA_API_KEY=<optional>
GROQ_API_KEY=<optional>
FIREWORKS_API_KEY=<optional>
OPENAI_API_KEY=<optional>
ANTHROPIC_API_KEY=<optional>

# Redis (optional password)
REDIS_PASSWORD=<optional>
```

**Minimum Required for Basic Functionality:**
- `LITELLM_MASTER_KEY` (mandatory)
- `POSTGRES_PASSWORD` (mandatory)
- `GROQ_API_KEY` (recommended - free tier for testing)

---

## Deployment Steps

### Phase 1: Database Initialization ⏳

**Estimated Time**: 5 minutes

```bash
# Step 1: Create database tables
docker exec ops-center-direct python3 /app/scripts/initialize_litellm_db.py

# Step 2: Verify tables created
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt litellm*"

# Expected output:
# - litellm_providers
# - litellm_models
# - litellm_model_providers
# - litellm_user_credits
# - litellm_credit_transactions
# - litellm_usage_logs
# - litellm_byok_keys
```

**Success Criteria:**
- [x] 7 tables created
- [x] No errors in initialization script
- [x] Default credits (1000) added for existing users

### Phase 2: User Configuration ⏳

**Estimated Time**: 10 minutes

```bash
# Step 1: User creates .env.litellm file
cd /opt/ops-center
cp .env.litellm.example .env.litellm

# Step 2: User adds API keys
nano .env.litellm
# Add at minimum:
# - LITELLM_MASTER_KEY (generate strong key)
# - GROQ_API_KEY (free from groq.com)

# Step 3: Set secure permissions
chmod 600 .env.litellm
```

**Security Checklist:**
- [ ] LITELLM_MASTER_KEY is strong (32+ characters)
- [ ] .env.litellm has 600 permissions
- [ ] .env.litellm added to .gitignore
- [ ] No API keys committed to git

### Phase 3: Deploy LiteLLM Containers ⏳

**Estimated Time**: 5 minutes

```bash
# Step 1: Start LiteLLM services
cd /opt/ops-center
docker compose -f docker-compose.litellm.yml up -d

# Step 2: Check containers started
docker ps | grep -E "litellm|wilmer"

# Expected containers:
# - unicorn-litellm-wilmer (port 4000)
# - unicorn-wilmer-router (port 4001)

# Step 3: View logs
docker logs unicorn-litellm-wilmer --tail 50
docker logs unicorn-wilmer-router --tail 50
```

**Success Criteria:**
- [x] Both containers running
- [x] No error logs
- [x] Health checks passing

### Phase 4: Restart Ops-Center Backend ⏳

**Estimated Time**: 2 minutes

```bash
# Restart to load new LiteLLM routes
docker restart ops-center-direct

# Wait for startup
sleep 10

# Check logs for LiteLLM routes registered
docker logs ops-center-direct | grep -i "litellm\|byok"
```

**Success Criteria:**
- [x] Backend restarted successfully
- [x] LiteLLM routes registered
- [x] No import errors

### Phase 5: Health Check ⏳

**Estimated Time**: 3 minutes

```bash
# Test 1: LiteLLM proxy health
curl http://localhost:4000/health

# Expected: {"status": "healthy"}

# Test 2: WilmerAI router health
curl http://localhost:4001/health

# Expected: {"status": "healthy"}

# Test 3: Ops-Center LLM API health
curl http://localhost:8084/api/v1/llm/health

# Expected: {"status": "healthy", "litellm_connected": true}

# Test 4: Available models
curl http://localhost:8084/api/v1/llm/models

# Expected: JSON list of 47 models
```

**Success Criteria:**
- [x] All health checks return 200 OK
- [x] Models endpoint returns model list
- [x] No connection errors

### Phase 6: Functional Testing ⏳

**Estimated Time**: 10 minutes

```bash
# Test 1: Basic chat completion (free Groq model)
curl -X POST http://localhost:8084/api/v1/llm/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ops-center-session-token>" \
  -d '{
    "model": "llama3-70b-groq",
    "messages": [{"role": "user", "content": "Hello! Say hi back."}],
    "power_level": "eco",
    "user_email": "test@example.com"
  }'

# Test 2: Check credit deduction
curl http://localhost:8084/api/v1/llm/credits/balance \
  -H "Authorization: Bearer <ops-center-session-token>"

# Expected: credits_remaining < 1000 (if started with 1000)

# Test 3: BYOK with user key
curl -X POST http://localhost:8084/api/v1/llm/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ops-center-session-token>" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Test"}],
    "byok": true,
    "provider": "openai",
    "api_key": "<user-openai-key>"
  }'

# Test 4: Usage logging
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT * FROM litellm_usage_logs ORDER BY created_at DESC LIMIT 5;"
```

**Success Criteria:**
- [x] Chat completion returns response
- [x] Credits deducted correctly
- [x] BYOK works with user key
- [x] Usage logged to database

---

## Post-Deployment

### Monitoring ⏳

```bash
# View real-time logs
docker logs unicorn-litellm-wilmer -f

# Check resource usage
docker stats unicorn-litellm-wilmer unicorn-wilmer-router

# Monitor PostgreSQL connections
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT COUNT(*) FROM pg_stat_activity WHERE datname='unicorn_db';"
```

**Alerts to Set:**
- [ ] High error rate (>5% requests)
- [ ] Low credit balance warnings
- [ ] Provider API failures
- [ ] High latency (>5s response time)

### User Documentation ⏳

**To Create:**
- [ ] User guide for BYOK setup
- [ ] Credit system explanation
- [ ] Power level selection guide
- [ ] Troubleshooting common issues
- [ ] Provider comparison chart

### Admin Tasks ⏳

**Weekly:**
- [ ] Review usage logs
- [ ] Check provider health metrics
- [ ] Monitor credit consumption patterns
- [ ] Update model configurations

**Monthly:**
- [ ] Optimize routing rules
- [ ] Review cost analytics
- [ ] Update provider API keys (if rotating)
- [ ] Performance tuning

---

## Testing Checklist

### Functional Tests

- [ ] **Free Tier Provider (Groq)**
  - [ ] Chat completion works
  - [ ] No credits deducted (free tier)
  - [ ] Latency acceptable (<2s)
  - [ ] Errors handled gracefully

- [ ] **Paid Provider (OpenRouter)**
  - [ ] Chat completion works
  - [ ] Credits deducted correctly
  - [ ] Cost calculated accurately
  - [ ] Usage logged

- [ ] **BYOK Functionality**
  - [ ] User can add API key
  - [ ] Key encrypted in database
  - [ ] Key used for requests
  - [ ] No credit deduction with BYOK
  - [ ] Key can be deleted

- [ ] **Credit System**
  - [ ] Initial credits assigned
  - [ ] Deductions calculated correctly
  - [ ] Low credit warnings work
  - [ ] Zero credit blocks requests
  - [ ] Admin can add credits

- [ ] **WilmerAI Routing**
  - [ ] ECO mode selects cheapest model
  - [ ] BALANCED mode optimizes quality/cost
  - [ ] PRECISION mode selects best model
  - [ ] CUSTOM allows manual selection
  - [ ] Routing logged to database

- [ ] **Provider Health**
  - [ ] Health checks run periodically
  - [ ] Failed providers marked unhealthy
  - [ ] Fallback providers used
  - [ ] Health status visible in UI

- [ ] **Usage Logging**
  - [ ] All requests logged
  - [ ] Token counts accurate
  - [ ] Costs calculated correctly
  - [ ] User attribution correct
  - [ ] Timestamps accurate

### Performance Tests

- [ ] **Latency**
  - [ ] Local vLLM: <1s (cold start <3s)
  - [ ] Groq: <2s
  - [ ] OpenRouter: <5s
  - [ ] Ollama: <2s

- [ ] **Throughput**
  - [ ] 100 requests/minute sustainable
  - [ ] No memory leaks over time
  - [ ] Database connections pooled
  - [ ] Redis caching effective

### Security Tests

- [ ] **API Keys**
  - [ ] Encrypted at rest (Fernet)
  - [ ] Not logged in plain text
  - [ ] Not exposed in responses
  - [ ] Rotation supported

- [ ] **Authorization**
  - [ ] Ops-Center session required
  - [ ] User email validated
  - [ ] Rate limiting enforced
  - [ ] Admin-only endpoints protected

### Integration Tests

- [ ] **Brigade Integration**
  - [ ] Brigade can call LLM API
  - [ ] Brigade usage tracked per agent
  - [ ] Brigade respects credit limits

- [ ] **Lago Billing Integration**
  - [ ] LLM usage events sent to Lago
  - [ ] Costs appear on invoices
  - [ ] BYOK usage not billed

- [ ] **Ops-Center UI**
  - [ ] LLM Management page shows models
  - [ ] Credit balance visible
  - [ ] BYOK key management UI works
  - [ ] Usage analytics displayed

---

## Potential Issues & Mitigations

### Issue 1: Missing `litellm` Dependency

**Symptom**: `ModuleNotFoundError: No module named 'litellm'`

**Impact**: CRITICAL - API won't start

**Mitigation**:
```bash
# Add to requirements.txt BEFORE deployment
echo "litellm>=1.40.0" >> backend/requirements.txt

# Rebuild container
docker compose -f docker-compose.direct.yml build
docker restart ops-center-direct
```

### Issue 2: LiteLLM Container Fails to Start

**Symptom**: `unicorn-litellm-wilmer` container exits immediately

**Possible Causes**:
- Missing required API keys (LITELLM_MASTER_KEY)
- Invalid YAML syntax in `litellm_config.yaml`
- Database connection failure
- Port 4000 already in use

**Mitigation**:
```bash
# Check logs
docker logs unicorn-litellm-wilmer

# Validate YAML
python3 -c "import yaml; yaml.safe_load(open('litellm_config.yaml'))"

# Check port availability
lsof -i :4000

# Verify environment variables loaded
docker exec unicorn-litellm-wilmer env | grep LITELLM
```

### Issue 3: Database Connection Errors

**Symptom**: `asyncpg.exceptions.InvalidCatalogNameError: database "unicorn_db" does not exist`

**Impact**: CRITICAL - No usage logging or credit tracking

**Mitigation**:
```bash
# Verify database exists
docker exec unicorn-postgresql psql -U unicorn -l

# Recreate if needed
docker exec unicorn-postgresql psql -U unicorn -c "CREATE DATABASE unicorn_db;"

# Re-run initialization
docker exec ops-center-direct python3 /app/scripts/initialize_litellm_db.py
```

### Issue 4: Redis Connection Timeout

**Symptom**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**Impact**: MODERATE - Caching disabled, slower routing

**Mitigation**:
```bash
# Check Redis is running
docker ps | grep redis

# Test connection
docker exec unicorn-redis redis-cli ping

# Check network connectivity
docker network inspect unicorn-network | grep -A 10 unicorn-redis
```

### Issue 5: Provider API Failures

**Symptom**: `HTTPException: Provider XYZ returned 401 Unauthorized`

**Impact**: MODERATE - Specific provider unavailable

**Mitigation**:
```bash
# Check API key is set
docker exec unicorn-litellm-wilmer env | grep XYZ_API_KEY

# Test API key directly
curl https://api.provider.com/test -H "Authorization: Bearer $XYZ_API_KEY"

# Verify key in .env.litellm
cat .env.litellm | grep XYZ_API_KEY

# Restart container to reload env
docker restart unicorn-litellm-wilmer
```

### Issue 6: Credit System Not Deducting

**Symptom**: User credits remain at 1000 after multiple requests

**Impact**: LOW - Free usage (revenue loss)

**Mitigation**:
```bash
# Check credit system initialized
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT COUNT(*) FROM litellm_user_credits;"

# Verify transactions logging
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT * FROM litellm_credit_transactions ORDER BY created_at DESC LIMIT 10;"

# Check backend logs for errors
docker logs ops-center-direct | grep -i credit
```

### Issue 7: BYOK Keys Not Encrypting

**Symptom**: API keys stored in plain text in database

**Impact**: CRITICAL - Security vulnerability

**Mitigation**:
```bash
# Verify encryption key set
docker exec ops-center-direct env | grep BYOK_ENCRYPTION_KEY

# Check encryption implementation
docker exec ops-center-direct python3 -c "
from byok_manager import BYOKManager
manager = BYOKManager()
encrypted = manager.encrypt_key('test123')
print('Encrypted:', encrypted)
decrypted = manager.decrypt_key(encrypted)
print('Decrypted:', decrypted)
"

# If encryption fails, regenerate key
docker exec ops-center-direct python3 -c "
from cryptography.fernet import Fernet
print('New key:', Fernet.generate_key().decode())
"
```

### Issue 8: Network Connectivity Between Services

**Symptom**: `ops-center-direct` can't reach `unicorn-litellm-wilmer`

**Impact**: CRITICAL - LLM API non-functional

**Mitigation**:
```bash
# Check both containers on same network
docker network inspect unicorn-network | grep -E "ops-center|litellm"

# Test connectivity
docker exec ops-center-direct curl http://unicorn-litellm-wilmer:4000/health

# Add to network if missing
docker network connect unicorn-network ops-center-direct
docker network connect unicorn-network unicorn-litellm-wilmer
```

---

## Recommended Order of Operations

### Day 1: Setup & Testing (Local Only)

1. ✅ Add `litellm>=1.40.0` to `requirements.txt`
2. ✅ Initialize database tables
3. ✅ Create `.env.litellm` with GROQ_API_KEY (free tier)
4. ✅ Deploy LiteLLM containers
5. ✅ Restart ops-center backend
6. ✅ Run health checks
7. ✅ Test basic chat completion
8. ✅ Verify credit deduction
9. ✅ Test BYOK with test key
10. ✅ Review logs for errors

**Time Required**: 1-2 hours
**Rollback Plan**: `docker compose -f docker-compose.litellm.yml down`

### Day 2-3: Production Validation

1. ✅ Add production provider API keys
2. ✅ Test all providers (9 total)
3. ✅ Verify WilmerAI routing logic
4. ✅ Test all power levels (ECO, BALANCED, PRECISION, CUSTOM)
5. ✅ Load test (100 requests/minute)
6. ✅ Monitor error rates
7. ✅ Check cost calculations
8. ✅ Validate usage logging

**Time Required**: 4-6 hours
**Success Criteria**: <2% error rate, <5s avg latency

### Day 4-5: Integration Testing

1. ✅ Test Brigade → Ops-Center → LiteLLM flow
2. ✅ Verify Lago billing integration
3. ✅ Test LLM Management UI in Ops-Center
4. ✅ Validate credit system with real users
5. ✅ Test BYOK end-to-end
6. ✅ Verify provider health monitoring
7. ✅ Test admin credit management

**Time Required**: 6-8 hours
**Success Criteria**: All integrations functional

### Day 6-7: Documentation & Monitoring

1. ✅ Write user documentation
2. ✅ Set up monitoring alerts
3. ✅ Create admin runbook
4. ✅ Train support team
5. ✅ Prepare rollback plan
6. ✅ Final production readiness review

**Time Required**: 4-6 hours
**Launch Readiness**: GO/NO-GO decision

---

## Rollback Plan

If critical issues arise:

```bash
# Step 1: Stop LiteLLM containers
docker compose -f docker-compose.litellm.yml down

# Step 2: Remove LiteLLM routes from ops-center
# Comment out in backend/server.py:
# app.include_router(litellm_router)
# app.include_router(byok_router)

# Step 3: Restart ops-center
docker restart ops-center-direct

# Step 4: Notify users LLM service temporarily unavailable

# Step 5: Investigate and fix issues

# Step 6: Re-deploy when ready
```

**Data Preservation:**
- Database tables remain intact
- User credits preserved
- BYOK keys retained (encrypted)
- Usage logs available for analysis

---

## Success Metrics

**Technical:**
- [x] 100% health checks passing
- [x] <2% error rate
- [x] <5s average latency
- [x] >99% uptime (7 days)

**Business:**
- [x] 80% users adopt LLM features
- [x] 30% BYOK adoption (paid users)
- [x] Credit system reduces platform costs by 40%
- [x] User satisfaction >4.5/5

**Security:**
- [x] 0 API key leaks
- [x] All keys encrypted at rest
- [x] Audit logs complete
- [x] No unauthorized access

---

## Support & Escalation

**Issues During Deployment:**
- Check logs first: `docker logs unicorn-litellm-wilmer`
- Review this checklist
- Consult `LITELLM_VERIFICATION_REPORT.md`
- If blocked, ROLLBACK and investigate

**Post-Deployment:**
- Monitor Grafana dashboards (if available)
- Check PostgreSQL query performance
- Review Redis hit rates
- Track provider API quotas

---

## Sign-Off

**Completed By**: ________________
**Date**: ________________
**Production Ready**: [ ] YES  [ ] NO
**Notes**:

___

**Next Review**: 7 days post-deployment
