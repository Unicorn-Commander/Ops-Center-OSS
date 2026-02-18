# Epic 3.1: LiteLLM Multi-Provider Routing - Quick Deployment Guide

**Status**: ✅ Ready to Deploy
**Date**: October 23, 2025

---

## TL;DR - Quick Commands

```bash
# 1. Navigate to ops-center
cd /opt/ops-center

# 2. Run database migration
docker cp backend/migrations/create_llm_tables.sql unicorn-postgresql:/tmp/
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /tmp/create_llm_tables.sql

# 3. Generate BYOK encryption key
python3 -c "from cryptography.fernet import Fernet; print('BYOK_ENCRYPTION_KEY=' + Fernet.generate_key().decode())"

# 4. Add key to .env.auth (copy output from step 3)
nano .env.auth

# 5. Restart ops-center
docker restart ops-center-direct

# 6. Verify health monitor started
docker logs ops-center-direct | grep -i "health monitor"

# 7. Check providers
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT provider_name, health_status, is_active FROM llm_providers;"
```

---

## Detailed Deployment Steps

### Step 1: Verify Prerequisites

```bash
# Check if ops-center is running
docker ps | grep ops-center-direct

# Check if PostgreSQL is accessible
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT 1;"

# Check current working directory
pwd
# Should be: /opt/ops-center
```

### Step 2: Run Database Migration

```bash
# Copy migration script into container
docker cp backend/migrations/create_llm_tables.sql unicorn-postgresql:/tmp/create_llm_tables.sql

# Execute migration
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /tmp/create_llm_tables.sql

# Expected output:
# CREATE EXTENSION
# CREATE TABLE (x5)
# CREATE INDEX (x15+)
# INSERT 0 7 (providers)
# INSERT 0 4 (models)
# INSERT 0 3 (routing rules)
# NOTICE: Created 5 LLM infrastructure tables
```

**Verify Tables Created**:
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public' AND tablename LIKE 'llm_%'
ORDER BY tablename;
"

# Should show:
# llm_models
# llm_providers
# llm_routing_rules
# llm_usage_logs
# user_api_keys (note: this is for BYOK, not llm_* prefix)
```

### Step 3: Configure Environment Variables

**Generate Encryption Key**:
```bash
python3 -c "from cryptography.fernet import Fernet; print('BYOK_ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

**Add to .env.auth**:
```bash
# Edit .env.auth
nano /opt/ops-center/.env.auth

# Add these lines at the end:
# ============================================================================
# LLM Multi-Provider Routing (Epic 3.1)
# ============================================================================

# BYOK Encryption Key (generate with: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
BYOK_ENCRYPTION_KEY=<paste-generated-key-here>

# LiteLLM Proxy Configuration
LITELLM_PROXY_URL=http://unicorn-litellm-wilmer:4000
LITELLM_MASTER_KEY=<your-litellm-master-key>

# Health Monitor Configuration
LLM_HEALTH_CHECK_INTERVAL=300  # 5 minutes

# Save and exit (Ctrl+X, Y, Enter)
```

**Verify Environment Variables**:
```bash
docker exec ops-center-direct printenv | grep -E "(BYOK|LITELLM|LLM_)"
```

### Step 4: Update server.py (if not already updated)

Check if server.py already includes health monitor:
```bash
grep -n "llm_health_monitor" /opt/ops-center/backend/server.py
```

**If not found**, add health monitor registration:

```bash
# Edit server.py
nano /opt/ops-center/backend/server.py

# Add these imports near the top:
# from llm_health_monitor import LLMHealthMonitor
# from llm_provider_management_api import router as provider_router

# Add after app creation:
# app.include_router(provider_router)

# Add startup/shutdown handlers (if not exist):
# @app.on_event("startup")
# async def startup_event():
#     # Start health monitor
#     pass
#
# @app.on_event("shutdown")
# async def shutdown_event():
#     # Stop health monitor
#     pass
```

**Note**: The existing backend may already have these registrations. Check first before modifying.

### Step 5: Restart Services

```bash
# Restart ops-center to load new environment variables and code
docker restart ops-center-direct

# Wait for startup (10 seconds)
sleep 10

# Check if container is running
docker ps | grep ops-center-direct

# Check logs for errors
docker logs ops-center-direct --tail 50
```

### Step 6: Verify Health Monitor

```bash
# Check if health monitor started
docker logs ops-center-direct | grep -i "health monitor"

# Expected logs:
# INFO:llm_health_monitor:Health monitor started (interval: 300s)
# INFO:llm_health_monitor:Running health checks for 7 providers
# INFO:llm_health_monitor:Health check complete: 7/7 updated
```

**Check Provider Health Status**:
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
SELECT
    provider_name,
    health_status,
    health_response_time_ms,
    is_active,
    to_char(health_last_checked, 'YYYY-MM-DD HH24:MI:SS') as last_checked
FROM llm_providers
ORDER BY provider_name;
"
```

**Expected Output** (after first health check):
```
 provider_name | health_status | health_response_time_ms | is_active |     last_checked
---------------+---------------+-------------------------+-----------+---------------------
 Anthropic     | healthy       |                     245 | t         | 2025-10-23 10:15:00
 Fireworks     | healthy       |                     182 | t         | 2025-10-23 10:15:00
 Google        | healthy       |                     156 | t         | 2025-10-23 10:15:00
 Groq          | healthy       |                      89 | t         | 2025-10-23 10:15:00
 OpenAI        | healthy       |                     203 | t         | 2025-10-23 10:15:00
 OpenRouter    | healthy       |                     178 | t         | 2025-10-23 10:15:00
 Together      | healthy       |                     195 | t         | 2025-10-23 10:15:00
```

### Step 7: Test BYOK Functionality

**Store a Test API Key**:
```bash
# Via curl (if endpoint is exposed)
curl -X POST http://localhost:8084/api/v1/llm/byok/keys \
  -H "Authorization: Bearer test-user-token" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-test-1234567890abcdefghijklmnop"
  }'

# Expected response:
# {
#   "success": true,
#   "key_id": "12345",
#   "provider": "openai",
#   "message": "API key stored successfully"
# }
```

**List User's Providers**:
```bash
curl http://localhost:8084/api/v1/llm/byok/keys \
  -H "Authorization: Bearer test-user-token"

# Expected response:
# {
#   "providers": [
#     {
#       "provider": "openai",
#       "enabled": true,
#       "masked_key": "***...enai",
#       "created_at": "2025-10-23T10:30:00"
#     }
#   ]
# }
```

### Step 8: Test Model Routing

**Make a Chat Completion Request**:
```bash
curl -X POST http://localhost:8084/api/v1/llm/chat/completions \
  -H "Authorization: Bearer test-user-token" \
  -H "Content-Type: application/json" \
  -H "X-Power-Level: balanced" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, what is 2+2?"}
    ]
  }'

# Expected response includes:
# - Actual LLM response
# - _metadata.provider_used
# - _metadata.cost_incurred
# - _metadata.power_level
```

---

## Verification Checklist

Use this checklist to verify successful deployment:

- [ ] **Database Migration**: All 5 tables created (llm_providers, llm_models, user_api_keys, llm_routing_rules, llm_usage_logs)
- [ ] **Seed Data**: 7 providers, 4 models, 3 routing rules inserted
- [ ] **Environment Variables**: BYOK_ENCRYPTION_KEY set in .env.auth
- [ ] **Container Running**: ops-center-direct container is running
- [ ] **Health Monitor**: Started and running checks every 5 minutes
- [ ] **Provider Health**: All 7 providers show health status (healthy/degraded/down/unknown)
- [ ] **API Endpoints**: BYOK endpoints responding (POST /byok/keys, GET /byok/keys, DELETE /byok/keys/{provider})
- [ ] **LLM Routing**: Chat completions endpoint working with routing logic
- [ ] **Logs Clean**: No errors in ops-center-direct logs

---

## Troubleshooting

### Issue: Database migration fails

**Error**: `relation "llm_providers" already exists`
**Solution**: Tables already exist. Either drop and recreate, or skip migration.

```bash
# Check if tables exist
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt llm_*"

# If exists and you want to recreate:
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
DROP TABLE IF EXISTS llm_usage_logs CASCADE;
DROP TABLE IF EXISTS llm_routing_rules CASCADE;
DROP TABLE IF EXISTS user_api_keys CASCADE;
DROP TABLE IF EXISTS llm_models CASCADE;
DROP TABLE IF EXISTS llm_providers CASCADE;
"

# Then re-run migration
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /tmp/create_llm_tables.sql
```

### Issue: BYOK_ENCRYPTION_KEY not set

**Error**: `ValueError: Invalid encryption key`
**Solution**: Generate and set encryption key.

```bash
# Generate key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env.auth
echo "BYOK_ENCRYPTION_KEY=<generated-key>" >> .env.auth

# Restart container
docker restart ops-center-direct
```

### Issue: Health monitor not starting

**Error**: No "health monitor started" in logs
**Solution**: Check if startup event handler is registered.

```bash
# Check server.py for @app.on_event("startup")
grep -n "on_event.*startup" backend/server.py

# Check if health monitor is imported
grep -n "import.*health_monitor" backend/server.py

# If missing, health monitor needs to be registered in server.py
```

### Issue: Providers show "unknown" health status

**Cause**: Health check hasn't run yet (runs every 5 minutes)
**Solution**: Wait 5 minutes or manually trigger health check.

```bash
# Wait for first health check
sleep 300

# Or trigger manually (if endpoint exists)
curl -X POST http://localhost:8084/api/v1/admin/llm/health/check \
  -H "Authorization: Bearer admin-token"

# Check status again
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
SELECT provider_name, health_status FROM llm_providers;
"
```

### Issue: LiteLLM proxy not responding

**Error**: `Connection refused` when calling /chat/completions
**Solution**: Check if LiteLLM container is running.

```bash
# Check if LiteLLM is running
docker ps | grep litellm

# Check LiteLLM logs
docker logs unicorn-litellm-wilmer --tail 50

# Test LiteLLM directly
curl http://localhost:4000/health
```

---

## Post-Deployment Tasks

After successful deployment:

1. **Monitor Logs** (first 24 hours):
   ```bash
   docker logs ops-center-direct -f
   ```

2. **Check Provider Health** (every hour for first day):
   ```bash
   docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
   SELECT provider_name, health_status, health_response_time_ms
   FROM llm_providers
   ORDER BY health_last_checked DESC;
   "
   ```

3. **Monitor Usage Logs** (verify billing integration):
   ```bash
   docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
   SELECT COUNT(*), SUM(total_tokens), SUM(cost_total_usd)
   FROM llm_usage_logs
   WHERE created_at > NOW() - INTERVAL '1 hour';
   "
   ```

4. **Test BYOK with Real API Keys** (one provider at a time):
   ```bash
   # Store real OpenAI key
   curl -X POST http://localhost:8084/api/v1/llm/byok/keys \
     -H "Authorization: Bearer <user-token>" \
     -H "Content-Type: application/json" \
     -d '{
       "provider": "openai",
       "api_key": "<real-openai-key>"
     }'

   # Test with real request
   curl -X POST http://localhost:8084/api/v1/llm/chat/completions \
     -H "Authorization: Bearer <user-token>" \
     -H "Content-Type: application/json" \
     -d '{
       "messages": [{"role": "user", "content": "test"}],
       "model": "gpt-3.5-turbo"
     }'
   ```

5. **Update Documentation** (add to wiki/README):
   - BYOK setup instructions for users
   - Provider health status page
   - Model routing configuration guide
   - Cost optimization tips

---

## Success Criteria

Deployment is successful when:

✅ All 5 database tables exist and contain seed data
✅ Health monitor is running and updating provider status every 5 minutes
✅ BYOK endpoints accept, store, and retrieve encrypted API keys
✅ Chat completions endpoint routes to correct models based on power level
✅ Usage logging captures all requests for billing integration
✅ No errors in ops-center-direct logs
✅ All 7 providers show realistic health status (not all "unknown")

---

**Deployment Date**: October 23, 2025
**Deployment Time**: ~15 minutes (if no issues)
**Rollback Plan**: Remove tables, revert .env.auth, restart container

---

Need help? Check the full implementation guide: `EPIC_3.1_BACKEND_COMPLETE.md`
