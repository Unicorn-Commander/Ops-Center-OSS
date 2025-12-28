# Usage Tracking System Deployment Guide

**Date**: November 12, 2025
**Status**: Ready for Deployment
**Complexity**: Medium

## Overview

Complete API call metering system for enforcing subscription tier limits. Tracks usage in real-time with Redis (fast) and PostgreSQL (persistent).

---

## ✅ Files Created

### Backend (Python)
1. **`usage_tracking.py`** (542 lines) - Core metering logic
   - UsageTracker class with Redis + PostgreSQL dual-write
   - Tier limit enforcement (trial, starter, professional, enterprise)
   - Quota management and reset functions

2. **`usage_middleware.py`** (218 lines) - FastAPI middleware
   - Auto-intercepts `/api/v1/llm/*` requests
   - Checks limits BEFORE processing request
   - Returns 429 if limit exceeded
   - Adds rate limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`)

3. **`usage_tracking_api.py`** (309 lines) - RESTful API endpoints
   - `GET /api/v1/usage/current` - Current usage stats
   - `GET /api/v1/usage/history` - Historical data for charts
   - `GET /api/v1/usage/limits` - Tier limits info
   - `GET /api/v1/admin/usage/organization/{org_id}` - Org-wide stats (admin)
   - `POST /api/v1/usage/reset` - Reset quota (admin)
   - `GET /api/v1/usage/health` - Health check

### Database Migration
4. **`migrations/usage_tracking_schema.sql`** (297 lines)
   - `api_usage` table - All API call events
   - `usage_quotas` table - User tier and limits
   - `usage_alerts` table - Threshold alerts (50%, 80%, 95%)
   - Automatic triggers for quota updates and alerts
   - Materialized view for dashboard performance

### Frontend (React)
5. **`src/pages/subscription/SubscriptionUsage.jsx`** (Updated)
   - Real-time usage display with progress bars
   - Historical charts (daily, weekly, monthly)
   - Service breakdown (chat, search, TTS, STT)
   - Warning indicators when approaching limits

### Testing
6. **`tests/test_usage_tracking.py`** (533 lines)
   - 9 comprehensive test scenarios
   - Tests all tier limits (trial, starter, professional, enterprise)
   - Redis/PostgreSQL sync verification
   - Multi-user isolation tests
   - Quota reset tests

---

## 📊 Subscription Tier Limits

| Tier | Daily Limit | Monthly Limit | Reset Period |
|------|------------|---------------|--------------|
| **trial** | 100 calls | 700 calls (7 days) | Daily |
| **starter** | 34 calls | 1,000 calls | Monthly |
| **professional** | 334 calls | 10,000 calls | Monthly |
| **enterprise** | Unlimited | Unlimited | Monthly |
| **vip_founder** | Unlimited | Unlimited | Monthly |
| **byok** | Unlimited | Unlimited | Monthly |

---

## 🚀 Deployment Steps

### 1. Database Migration

```bash
# Connect to PostgreSQL
docker exec -it uchub-postgres psql -U unicorn -d unicorn_db

# Run migration SQL
\i /app/migrations/usage_tracking_schema.sql

# Verify tables created
\dt api_usage
\dt usage_quotas
\dt usage_alerts

# Verify triggers
\df update_usage_quota_cache
\df check_usage_alerts

# Exit
\q
```

**Expected Output**:
- 3 tables created (`api_usage`, `usage_quotas`, `usage_alerts`)
- 2 functions created (triggers)
- 1 materialized view created

### 2. Integrate Middleware into server.py

Add these imports at the top of `backend/server.py`:

```python
# Add after line 67 (after "from usage_api import router as usage_router")
from usage_tracking import usage_tracker
from usage_middleware import UsageTrackingMiddleware
from usage_tracking_api import router as usage_tracking_router
```

Add middleware registration (after line 420, after TierEnforcementMiddleware):

```python
# Usage tracking middleware (tracks API calls and enforces limits)
app.add_middleware(UsageTrackingMiddleware)
```

Register new API router (in the router registration section, around line 1200):

```python
# Usage tracking API (detailed usage stats)
app.include_router(usage_tracking_router)
```

Initialize usage tracker on startup (in the startup event handler, around line 280):

```python
@app.on_event("startup")
async def startup():
    # ... existing startup code ...

    # Initialize usage tracker
    await usage_tracker.initialize()
    logger.info("Usage tracker initialized")
```

Add shutdown handler (after startup):

```python
@app.on_event("shutdown")
async def shutdown():
    # Close usage tracker connections
    await usage_tracker.close()
    logger.info("Usage tracker connections closed")
```

### 3. Frontend Build and Deploy

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center

# Build frontend (includes updated SubscriptionUsage.jsx)
npm run build

# Deploy to public/
cp -r dist/* public/

# Verify build
ls -lh public/assets/*.js | tail -5
```

### 4. Restart Service

```bash
# Restart ops-center to load new code
docker restart ops-center-direct

# Wait for startup
sleep 5

# Check logs for errors
docker logs ops-center-direct --tail 50 | grep -i "error\|usage"

# Verify service is running
curl -s http://localhost:8084/api/v1/system/status | jq .
```

### 5. Verify Deployment

```bash
# Test health check
curl -s http://localhost:8084/api/v1/usage/health | jq .

# Should return:
# {
#   "success": true,
#   "healthy": true,
#   "components": {
#     "redis": "ok",
#     "postgresql": "ok"
#   }
# }

# Test current usage endpoint (requires authentication)
curl -s http://localhost:8084/api/v1/usage/current \
  -H "Cookie: session_token=YOUR_TOKEN" | jq .

# Expected response:
# {
#   "success": true,
#   "data": {
#     "user_id": "...",
#     "tier": "trial",
#     "usage": { "used": 0, "limit": 700, "remaining": 700 }
#   }
# }
```

---

## 🧪 Testing

### Run Automated Tests

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend

# Run usage tracking tests
python3 tests/test_usage_tracking.py

# Or with pytest (more detailed output)
docker exec ops-center-direct pytest /app/tests/test_usage_tracking.py -v

# Expected: All 9 tests should pass
```

### Manual Testing Scenarios

#### Test 1: User Within Limit
```bash
# Make an API call (should succeed)
curl -X POST http://localhost:8084/api/v1/llm/chat/completions \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_TOKEN" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Check response headers
# X-RateLimit-Limit: 700
# X-RateLimit-Remaining: 699
# X-RateLimit-Reset: 1699920000
```

#### Test 2: User At Limit
```bash
# Set user to trial tier with 0 remaining calls
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "
UPDATE usage_quotas
SET api_calls_used = 700, api_calls_limit = 700
WHERE user_id = 'YOUR_USER_ID';
"

# Try to make API call (should fail with 429)
curl -X POST http://localhost:8084/api/v1/llm/chat/completions \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_TOKEN" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Expected response:
# HTTP 429 Too Many Requests
# {
#   "error": "Rate Limit Exceeded",
#   "message": "You have exceeded your trial tier API call limit...",
#   "tier": "trial",
#   "used": 700,
#   "limit": 700,
#   "remaining": 0
# }
```

#### Test 3: Enterprise Unlimited
```bash
# Set user to enterprise tier
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "
UPDATE usage_quotas
SET subscription_tier = 'enterprise', api_calls_limit = -1
WHERE user_id = 'YOUR_USER_ID';
"

# Make 100 API calls (all should succeed)
for i in {1..100}; do
  curl -X POST http://localhost:8084/api/v1/llm/chat/completions \
    -H "Cookie: session_token=YOUR_TOKEN" \
    -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Test"}]}' \
    > /dev/null 2>&1
  echo "Call $i completed"
done

# Check X-RateLimit-Limit header (should be "unlimited")
```

#### Test 4: Usage Dashboard

1. Login to Ops-Center: https://your-domain.com
2. Navigate to **Subscription → Usage**
3. Verify you see:
   - Current usage progress bar
   - API calls used / limit
   - Reset date countdown
   - Historical usage chart (last 7 days)
   - Service breakdown (chat, search, TTS, STT)

---

## 📈 Performance Considerations

### Redis Caching
- **Fast counters**: All usage increments hit Redis first (~1ms)
- **TTL management**: Keys auto-expire at period end (daily/monthly)
- **Fallback**: If Redis fails, falls back to PostgreSQL

### PostgreSQL Optimization
- **Indexes**: Composite indexes on `(user_id, billing_period)`
- **Partitioning**: Consider partitioning `api_usage` by month for large datasets
- **Materialized View**: `mv_daily_usage_summary` pre-aggregates daily stats

### Request Performance Impact
- **Middleware overhead**: ~5ms per request (Redis lookup + increment)
- **Database writes**: Async, don't block requests
- **Cached quotas**: User tier info cached in Redis (60s TTL)

---

## 🚨 Troubleshooting

### Issue: "Usage tracker not initialized"

**Cause**: Tracker didn't initialize on startup
**Fix**:
```bash
docker exec ops-center-direct python3 -c "
import asyncio
from usage_tracking import usage_tracker
asyncio.run(usage_tracker.initialize())
print('Initialized successfully')
"
```

### Issue: Redis connection errors

**Cause**: Wrong Redis host or Redis not running
**Fix**:
```bash
# Check Redis is running
docker ps | grep redis

# Check Redis host in .env.auth
grep REDIS_HOST /home/muut/Production/UC-Cloud/services/ops-center/.env.auth

# Test Redis connection
docker exec ops-center-direct python3 -c "
import redis.asyncio as aioredis
import asyncio
async def test():
    r = await aioredis.from_url('redis://unicorn-lago-redis:6379')
    await r.ping()
    print('Redis OK')
asyncio.run(test())
"
```

### Issue: PostgreSQL connection errors

**Cause**: Database not accessible or wrong credentials
**Fix**:
```bash
# Test PostgreSQL connection
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "SELECT 1;"

# Verify tables exist
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "\dt api_usage"
```

### Issue: Migration failed

**Cause**: Tables already exist or syntax error
**Fix**:
```bash
# Drop existing tables (CAUTION: deletes data)
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "
DROP TABLE IF EXISTS api_usage CASCADE;
DROP TABLE IF EXISTS usage_quotas CASCADE;
DROP TABLE IF EXISTS usage_alerts CASCADE;
"

# Re-run migration
docker exec uchub-postgres psql -U unicorn -d unicorn_db -f /app/migrations/usage_tracking_schema.sql
```

---

## 📊 Monitoring & Alerts

### Check Usage Stats

```bash
# Top 10 users by API usage
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "
SELECT user_id, COUNT(*) as api_calls, SUM(tokens_used) as total_tokens
FROM api_usage
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY user_id
ORDER BY api_calls DESC
LIMIT 10;
"

# Users approaching limit (> 80%)
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "
SELECT user_id, subscription_tier, api_calls_used, api_calls_limit,
       ROUND((api_calls_used::FLOAT / NULLIF(api_calls_limit, 0)) * 100, 2) as percent_used
FROM usage_quotas
WHERE api_calls_limit > 0
  AND api_calls_used::FLOAT / api_calls_limit > 0.8
ORDER BY percent_used DESC;
"

# Pending usage alerts
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "
SELECT * FROM usage_alerts
WHERE alert_sent = false
ORDER BY created_at DESC
LIMIT 20;
"
```

### Refresh Dashboard Stats

```bash
# Refresh materialized view (run daily via cron)
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "
SELECT refresh_usage_summary();
"
```

---

## 🎯 Success Criteria

✅ **All tests pass** (9/9)
✅ **API calls are metered** automatically
✅ **Users see real-time usage** in dashboard
✅ **Requests blocked** when limit exceeded (429)
✅ **Quotas reset** automatically on billing cycle
✅ **Enterprise users** have unlimited access
✅ **Historical data** available for charts
✅ **Performance impact** < 5ms per request
✅ **Rate limit headers** present in responses

---

## 📝 Next Steps (Post-Deployment)

1. **Email Notifications**: Send alerts at 50%, 80%, 95% thresholds
2. **Webhook Integration**: Notify external systems when limits hit
3. **Admin Dashboard**: Add usage analytics page for admins
4. **Auto-Tier-Upgrade**: Suggest upgrades when users hit limits
5. **Rate Limiting**: Add per-minute rate limits (not just monthly totals)
6. **Cost Tracking**: Track actual provider costs vs credits charged

---

## 🔗 Related Files

- **Backend Core**: `usage_tracking.py`, `usage_middleware.py`, `usage_tracking_api.py`
- **Database**: `migrations/usage_tracking_schema.sql`
- **Frontend**: `src/pages/subscription/SubscriptionUsage.jsx`
- **Tests**: `tests/test_usage_tracking.py`
- **Config**: `.env.auth` (Redis/PostgreSQL connection strings)

---

**Deployment Checklist**:
- [ ] Run database migration
- [ ] Update server.py imports
- [ ] Add middleware registration
- [ ] Register API router
- [ ] Build frontend
- [ ] Restart service
- [ ] Run tests
- [ ] Verify health endpoint
- [ ] Test trial tier limit
- [ ] Test enterprise unlimited
- [ ] Check usage dashboard

**Estimated Deployment Time**: 30 minutes

**Rollback Plan**: Remove middleware from server.py, restart service. Tables can remain (no harm).

---

**Questions or Issues?**
Contact: Usage Tracking Team Lead
Documentation: This file
