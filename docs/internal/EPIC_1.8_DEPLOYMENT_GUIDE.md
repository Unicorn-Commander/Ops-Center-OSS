# Epic 1.8: Credit System Deployment Guide

**Date**: October 23, 2025
**Version**: 1.0.0
**Status**: Production Ready

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Requirements](#environment-requirements)
3. [Deployment Steps](#deployment-steps)
4. [Verification](#verification)
5. [Rollback Procedure](#rollback-procedure)
6. [Post-Deployment Tasks](#post-deployment-tasks)
7. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Required Reviews

- [ ] **Code Review**: All credit system code reviewed and approved
- [ ] **Security Audit**: Security tests passed (15/15 tests)
- [ ] **Performance Validation**: Performance benchmarks met
- [ ] **Documentation**: API docs, user guide, admin guide complete

### Backup Requirements

- [ ] **Database Backup**: Full PostgreSQL backup created
- [ ] **Configuration Backup**: `.env.auth` file backed up
- [ ] **Code Backup**: Git commit tagged with release version

### Team Notifications

- [ ] **Engineering Team**: Notified of deployment window
- [ ] **Operations Team**: On standby for monitoring
- [ ] **Support Team**: Informed of new credit system features

---

## Environment Requirements

### System Requirements

| Component | Requirement | Status |
|-----------|-------------|--------|
| PostgreSQL | 12+ running | ✅ unicorn-postgresql |
| Redis | 6+ running | ✅ unicorn-redis |
| Python | 3.10+ | ✅ In ops-center container |
| FastAPI | 0.100+ | ✅ Backend framework |

### Container Status

```bash
# Verify all required containers are running
docker ps | grep -E "(postgresql|redis|ops-center)"

# Expected output:
# unicorn-postgresql   (healthy)
# unicorn-redis        (healthy)
# ops-center-direct    (running)
```

### Database Connectivity

```bash
# Test PostgreSQL connection
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT 1;"

# Expected output:
# ?column?
# ----------
#        1
# (1 row)
```

### Redis Connectivity

```bash
# Test Redis connection
docker exec unicorn-redis redis-cli PING

# Expected output:
# PONG
```

---

## Deployment Steps

### Step 1: Backup Current State (5 minutes)

```bash
# Navigate to ops-center directory
cd /home/muut/Production/UC-Cloud/services/ops-center

# Create timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup database
docker exec unicorn-postgresql pg_dump -U unicorn unicorn_db > \
    /tmp/ops-center-backups/pre_epic_1.8_backup_${TIMESTAMP}.sql

# Backup environment file
cp .env.auth .env.auth.backup.${TIMESTAMP}

# Verify backup size
ls -lh /tmp/ops-center-backups/pre_epic_1.8_backup_${TIMESTAMP}.sql

# Tag git commit
git tag -a "pre-epic-1.8-${TIMESTAMP}" -m "Pre Epic 1.8 deployment backup"
git push origin "pre-epic-1.8-${TIMESTAMP}"
```

### Step 2: Deploy Database Migration (10 minutes)

```bash
# Set environment (production or development)
export ENVIRONMENT=production

# Run migration script
./scripts/migrate_credit_system.sh

# Expected output:
# ==========================================
#   Epic 1.8 Credit System Migration
# ==========================================
#
# [INFO] Checking prerequisites...
# [SUCCESS] Prerequisites check passed
# [INFO] Creating database backup...
# [SUCCESS] Backup created: /tmp/...
# [INFO] Applying credit system migration...
# [SUCCESS] Migration applied successfully
# [INFO] Verifying tables...
# [SUCCESS] ✓ Table 'user_credits' exists
# [SUCCESS] ✓ Table 'credit_transactions' exists
# [SUCCESS] ✓ Table 'openrouter_accounts' exists
# [SUCCESS] ✓ Table 'coupon_codes' exists
# [SUCCESS] ✓ Table 'usage_events' exists
# [SUCCESS] All tables verified
# [INFO] Verifying indexes...
# [SUCCESS] Migration completed successfully!
```

**If migration fails**: Script will automatically rollback. See [Rollback Procedure](#rollback-procedure).

### Step 3: Deploy Backend Code (5 minutes)

```bash
# Ensure latest code is pulled
git pull origin main

# Verify credit system module exists
ls -l backend/litellm_credit_system.py

# Restart backend container to load new code
docker restart ops-center-direct

# Wait for container to be healthy
sleep 10

# Verify container is running
docker ps | grep ops-center-direct

# Check logs for errors
docker logs ops-center-direct --tail 50 | grep -i error
```

### Step 4: Environment Variables (2 minutes)

Add the following to `.env.auth` if not already present:

```bash
# Credit System Configuration
CREDIT_SYSTEM_ENABLED=true
CREDIT_CACHE_TTL=60
OPENROUTER_API_BASE_URL=https://openrouter.ai/api/v1
ENCRYPTION_KEY=<generate-with-fernet>

# Generate encryption key (if needed)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Restart after adding variables:

```bash
docker restart ops-center-direct
```

### Step 5: Initial Data Setup (3 minutes)

```bash
# Create test coupon (optional, development only)
if [ "$ENVIRONMENT" != "production" ]; then
    docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db << 'EOF'
    INSERT INTO coupon_codes (code, discount_type, discount_value, max_uses, expires_at)
    VALUES
        ('WELCOME100', 'fixed', 100.00, 1000, NOW() + INTERVAL '30 days'),
        ('SAVE50', 'percentage', 50, 500, NOW() + INTERVAL '60 days')
    ON CONFLICT (code) DO NOTHING;
EOF
fi

# Verify data
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c \
    "SELECT code, discount_type, discount_value FROM coupon_codes LIMIT 5;"
```

---

## Verification

### Verification Checklist

Run these checks to verify successful deployment:

#### 1. Database Verification (5 minutes)

```bash
# Check all tables exist
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt" | grep -E "(user_credits|credit_transactions|openrouter_accounts|coupon_codes|usage_events)"

# Expected output:
# public | user_credits           | table | unicorn
# public | credit_transactions    | table | unicorn
# public | openrouter_accounts    | table | unicorn
# public | coupon_codes           | table | unicorn
# public | usage_events           | table | unicorn

# Check table schemas
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d user_credits"
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d credit_transactions"

# Verify indexes exist
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\di" | grep -E "idx_(user_credits|credit_transactions)"
```

#### 2. API Endpoint Verification (10 minutes)

```bash
# Test balance endpoint (requires authentication)
curl -X GET "http://localhost:8084/api/v1/credits/balance" \
    -H "Authorization: Bearer <token>" \
    -H "Cookie: session_token=<session>"

# Expected response:
# {
#   "balance": 0.0,
#   "tier": "free",
#   "monthly_cap": null
# }

# Test cost calculation endpoint
curl -X POST "http://localhost:8084/api/v1/credits/calculate-cost" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <token>" \
    -d '{
      "tokens_used": 1000,
      "model": "gpt-4o",
      "power_level": "balanced"
    }'

# Expected response:
# {
#   "cost": 0.00375
# }

# Test admin allocation endpoint (requires admin role)
curl -X POST "http://localhost:8084/api/v1/admin/credits/allocate" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <admin_token>" \
    -d '{
      "user_id": "test@example.com",
      "amount": 100.0,
      "reason": "bonus"
    }'

# Expected response:
# {
#   "new_balance": 100.0,
#   "transaction_id": "..."
# }
```

#### 3. Cache Verification (2 minutes)

```bash
# Check Redis connection
docker exec unicorn-redis redis-cli PING

# Check if credit balances are being cached
docker exec unicorn-redis redis-cli KEYS "credits:balance:*"

# Check TTL on cached keys
docker exec unicorn-redis redis-cli TTL "credits:balance:test@example.com"

# Expected: 60 seconds or less
```

#### 4. Test Transaction Flow (5 minutes)

```bash
# 1. Check initial balance
curl -X GET "http://localhost:8084/api/v1/credits/balance" \
    -H "Authorization: Bearer <token>"

# 2. Allocate credits (admin)
curl -X POST "http://localhost:8084/api/v1/admin/credits/allocate" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <admin_token>" \
    -d '{"user_id": "test@example.com", "amount": 50.0, "reason": "test"}'

# 3. Verify new balance
curl -X GET "http://localhost:8084/api/v1/credits/balance" \
    -H "Authorization: Bearer <token>"

# 4. Deduct credits
curl -X POST "http://localhost:8084/api/v1/credits/deduct" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <token>" \
    -d '{
      "amount": 10.0,
      "metadata": {
        "provider": "openai",
        "model": "gpt-4o",
        "tokens_used": 1000
      }
    }'

# 5. Check transaction history
curl -X GET "http://localhost:8084/api/v1/credits/transactions?limit=5" \
    -H "Authorization: Bearer <token>"
```

#### 5. Run Automated Tests (10 minutes)

```bash
# Run unit tests
docker exec ops-center-direct pytest backend/tests/test_credit_system.py -v

# Expected: All tests pass

# Run integration tests (subset)
docker exec ops-center-direct pytest backend/tests/integration/test_credit_api.py::TestCreditBalanceEndpoints -v

# Run security tests (subset)
docker exec ops-center-direct pytest backend/tests/security/test_credit_security.py::TestAuthorizationChecks -v
```

---

## Rollback Procedure

### When to Rollback

Rollback if any of the following occur:
- ❌ Migration fails and cannot be fixed
- ❌ Critical API endpoints return 500 errors
- ❌ Database corruption detected
- ❌ Performance degradation >50%
- ❌ Security vulnerability discovered

### Automatic Rollback (Migration Failure)

If the migration script fails, it will automatically rollback using the backup created at the start of the migration.

```bash
# Migration script handles rollback automatically
# You will see:
# [WARNING] Rolling back migration...
# [SUCCESS] Rollback completed successfully
```

### Manual Rollback Steps

If you need to manually rollback after successful migration:

```bash
# 1. Stop accepting new requests (optional)
docker stop ops-center-direct

# 2. Restore database from backup
BACKUP_FILE="/tmp/ops-center-backups/pre_epic_1.8_backup_<timestamp>.sql"

docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db << EOF
-- Drop credit system tables
DROP TABLE IF EXISTS usage_events CASCADE;
DROP TABLE IF EXISTS coupon_codes CASCADE;
DROP TABLE IF EXISTS openrouter_accounts CASCADE;
DROP TABLE IF EXISTS credit_transactions CASCADE;
DROP TABLE IF EXISTS user_credits CASCADE;
EOF

# Restore from backup
docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db < ${BACKUP_FILE}

# 3. Revert code changes
git checkout pre-epic-1.8-<timestamp>

# 4. Remove environment variables
# Edit .env.auth and remove credit system variables

# 5. Restart container
docker restart ops-center-direct

# 6. Verify rollback successful
docker logs ops-center-direct --tail 50
```

### Post-Rollback Verification

```bash
# Verify tables are restored
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt"

# Verify application is running
curl http://localhost:8084/api/v1/system/status
```

---

## Post-Deployment Tasks

### 1. Monitoring Setup (15 minutes)

```bash
# Add Prometheus metrics for credit operations
# (If Prometheus is enabled)

# Add Grafana dashboard for credit system
# Dashboard includes:
# - Credit balance distribution
# - Transaction volume
# - API endpoint latency
# - Error rates
```

### 2. Alert Configuration (10 minutes)

Set up alerts for:
- Low credit balance warnings
- High error rate on credit endpoints
- Unusual spending patterns
- Failed transaction spikes

### 3. Documentation Updates (5 minutes)

- [ ] Update API documentation with credit endpoints
- [ ] Update user guide with credit system usage
- [ ] Update admin guide with credit management procedures
- [ ] Announce new features to users

### 4. User Communication (2 minutes)

Send announcement to users:
```
Subject: New Feature: Credit & Usage Metering System

We're excited to announce the launch of our new Credit & Usage Metering System!

Key Features:
- Real-time credit balance tracking
- Detailed transaction history
- Usage analytics by model and provider
- Monthly spending caps
- Promotional coupon support

Learn more: [Link to user guide]
```

---

## Troubleshooting

### Issue: Migration Script Fails

**Symptoms**: Migration script exits with error

**Solution**:
```bash
# Check PostgreSQL logs
docker logs unicorn-postgresql --tail 100

# Check if tables partially created
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt" | grep credit

# If partial, drop tables and retry
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
DROP TABLE IF EXISTS usage_events CASCADE;
DROP TABLE IF EXISTS coupon_codes CASCADE;
DROP TABLE IF EXISTS openrouter_accounts CASCADE;
DROP TABLE IF EXISTS credit_transactions CASCADE;
DROP TABLE IF EXISTS user_credits CASCADE;
"

# Retry migration
./scripts/migrate_credit_system.sh
```

### Issue: API Endpoints Return 500 Errors

**Symptoms**: Credit endpoints return Internal Server Error

**Solution**:
```bash
# Check application logs
docker logs ops-center-direct --tail 100 | grep -i error

# Common causes:
# 1. Database connection issue
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT 1;"

# 2. Redis connection issue
docker exec unicorn-redis redis-cli PING

# 3. Missing environment variable
docker exec ops-center-direct printenv | grep CREDIT

# Restart container
docker restart ops-center-direct
```

### Issue: Slow Performance

**Symptoms**: Credit operations take >5 seconds

**Solution**:
```bash
# Check database indexes
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE tablename LIKE '%credit%';
"

# Check Redis cache hit rate
docker exec unicorn-redis redis-cli INFO stats | grep keyspace

# Check for slow queries
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
WHERE query LIKE '%credit%'
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# Restart Redis to clear stale cache
docker restart unicorn-redis
```

### Issue: Incorrect Credit Calculations

**Symptoms**: Cost calculations don't match expected values

**Solution**:
```bash
# Verify pricing configuration
docker exec ops-center-direct python3 << 'EOF'
from litellm_credit_system import PRICING, MODEL_PRICING, TIER_MARKUP, POWER_LEVELS
print("PRICING:", PRICING)
print("MODEL_PRICING:", MODEL_PRICING)
print("TIER_MARKUP:", TIER_MARKUP)
print("POWER_LEVELS:", POWER_LEVELS)
EOF

# Test cost calculation
curl -X POST "http://localhost:8084/api/v1/credits/calculate-cost" \
    -H "Content-Type: application/json" \
    -d '{"tokens_used": 1000, "model": "gpt-4o", "power_level": "balanced"}'

# Expected formula:
# cost = (tokens / 1000) * base_cost * power_multiplier * tier_multiplier
```

---

## Success Criteria

Deployment is considered successful when:

- ✅ All 5 tables exist in database
- ✅ All 20+ indexes are created
- ✅ Credit balance endpoint returns 200
- ✅ Credit allocation works (admin)
- ✅ Credit deduction works (user)
- ✅ Transaction history retrieves records
- ✅ Cost calculation returns correct values
- ✅ Cache hit rate >50% after 5 minutes
- ✅ API response times <500ms (p95)
- ✅ No errors in application logs
- ✅ Unit tests pass (60/60)
- ✅ Integration tests pass (30/30)
- ✅ Security tests pass (15/15)

---

## Support Contacts

**Engineering Team Lead**: [Contact Info]
**Database Administrator**: [Contact Info]
**DevOps Engineer**: [Contact Info]
**On-Call Rotation**: [PagerDuty/OnCall Link]

---

## Deployment Log Template

Use this template to log your deployment:

```
=== Epic 1.8 Deployment Log ===
Date: _______________
Time: _______________
Deployed By: _______________
Environment: Production / Staging / Development

Pre-Deployment:
[ ] Backup created: _______________
[ ] Code reviewed
[ ] Tests passed

Deployment:
[ ] Migration completed at: _______________
[ ] Backend restarted at: _______________
[ ] Environment variables updated

Verification:
[ ] Database tables verified
[ ] API endpoints tested
[ ] Cache verified
[ ] Transaction flow tested
[ ] Automated tests run

Post-Deployment:
[ ] Monitoring configured
[ ] Alerts set up
[ ] Documentation updated
[ ] Users notified

Issues Encountered:
_______________________________________________
_______________________________________________

Resolution:
_______________________________________________
_______________________________________________

Sign-off:
Engineer: _______________ Date: _______________
Reviewer: _______________ Date: _______________
```

---

**Document Version**: 1.0.0
**Last Updated**: October 23, 2025
**Status**: ✅ **READY FOR PRODUCTION DEPLOYMENT**
