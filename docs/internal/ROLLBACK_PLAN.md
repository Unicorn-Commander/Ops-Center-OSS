# LLM Hub Rollback Plan

This document describes emergency rollback procedures for the unified LLM Management system.

## Table of Contents

1. [Emergency Rollback (< 5 minutes)](#emergency-rollback--5-minutes)
2. [Full Rollback with Database](#full-rollback-with-database)
3. [Rollback Criteria](#rollback-criteria)
4. [Testing Rollback](#testing-rollback)
5. [Post-Rollback Actions](#post-rollback-actions)

---

## Emergency Rollback (< 5 minutes)

Use this procedure for immediate rollback without data loss.

### Step 1: Disable Feature Flag

**Fastest Method - Environment Variable**:
```bash
# SSH to production server
ssh ops-center-prod

# Set feature flag to disabled
export FEATURE_UNIFIED_LLM_HUB=false

# Restart Ops Center
docker restart ops-center-direct

# Verify restart
docker logs ops-center-direct --tail 50
```

**Alternative - Update .env file**:
```bash
# Edit environment file
cd /home/muut/Production/UC-Cloud/services/ops-center
nano .env.auth

# Change this line:
FEATURE_UNIFIED_LLM_HUB=false

# Save and restart
docker compose restart ops-center-direct
```

**Expected Result**:
- Feature flag disabled within 30 seconds
- All users redirected to old pages
- New hub UI no longer accessible

### Step 2: Verify Old Pages Working

Test all old LLM management pages:

```bash
# Test provider keys page
curl -I https://your-domain.com/admin/llm-provider-keys

# Test model catalog page
curl -I https://your-domain.com/admin/llm-model-catalog

# Test routing page
curl -I https://your-domain.com/admin/llm-routing

# Test analytics page
curl -I https://your-domain.com/admin/llm-analytics
```

**Expected Result**: All return `200 OK`

### Step 3: Verify Feature Flag Status

```bash
# Check feature flag endpoint
curl https://your-domain.com/api/v1/features/unified_llm_hub

# Expected response:
{
  "flag": "unified_llm_hub",
  "enabled": false,
  "config": {
    "enabled": false,
    "rollout_percentage": 0
  }
}
```

### Step 4: Monitor Logs

```bash
# Watch for errors
docker logs ops-center-direct -f | grep -E "ERROR|WARN"

# Check page views (should show old pages)
docker logs ops-center-direct | grep PAGE_VIEW | tail -20
```

### Step 5: Announce Rollback

**Internal Communication**:
```markdown
🔄 **LLM Hub Rollback - COMPLETED**

**Status**: System rolled back to old LLM management pages
**Impact**: None - all functionality restored
**Action Required**: None
**ETA for Fix**: TBD
```

**User-Facing Communication** (if needed):
```markdown
We've temporarily reverted to the classic LLM management interface
while we resolve an issue. All functionality is working normally.
```

---

## Full Rollback with Database

Use this if database migrations need to be rolled back.

### Step 1: Stop Ops Center

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center
docker compose stop ops-center-direct
```

### Step 2: Backup Current Database

```bash
# Create backup before rollback
docker exec unicorn-postgresql pg_dump \
  -U unicorn \
  -d unicorn_db \
  -F custom \
  -f /tmp/pre_rollback_backup.dump

# Copy backup to host
docker cp unicorn-postgresql:/tmp/pre_rollback_backup.dump \
  /home/muut/backups/pre_rollback_$(date +%Y%m%d_%H%M%S).dump
```

### Step 3: Run Database Rollback

```bash
# Apply rollback migration
docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db \
  < backend/migrations/rollback_llm_management_tables.sql

# Verify tables dropped
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'llm_%';"

# Should return empty result
```

**Rollback Script Contents**:
```sql
-- Drop LLM Hub tables in reverse dependency order
DROP TABLE IF EXISTS llm_usage_analytics CASCADE;
DROP TABLE IF EXISTS llm_routing_rules CASCADE;
DROP TABLE IF EXISTS llm_model_tier_rules CASCADE;
DROP TABLE IF EXISTS llm_models CASCADE;
DROP TABLE IF EXISTS llm_provider_keys CASCADE;
DROP TABLE IF EXISTS llm_providers CASCADE;

-- Drop indexes
DROP INDEX IF EXISTS idx_provider_keys_user_id;
DROP INDEX IF EXISTS idx_models_provider;
DROP INDEX IF EXISTS idx_routing_rules_user_id;
DROP INDEX IF EXISTS idx_usage_analytics_user_id;
DROP INDEX IF EXISTS idx_usage_analytics_timestamp;

-- Drop functions
DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;
```

### Step 4: Restore Old Code Version

```bash
# Checkout previous stable version
git fetch origin
git checkout tags/v1.0.0-pre-llm-hub

# Rebuild Docker image
docker compose build ops-center-direct

# Start service
docker compose up -d ops-center-direct
```

### Step 5: Verify System Health

```bash
# Run health check
./scripts/health-check-detailed.sh

# Test old pages
curl https://your-domain.com/admin/llm-provider-keys
curl https://your-domain.com/admin/llm-model-catalog

# Check logs
docker logs ops-center-direct --tail 100
```

---

## Rollback Criteria

Execute rollback if ANY of these conditions are met:

### Critical Issues (Immediate Rollback)

1. **Data Loss**: Users cannot access their provider keys or configurations
2. **Security Breach**: API keys exposed or authentication bypass detected
3. **Complete Outage**: LLM Hub crashes and won't recover
4. **Database Corruption**: Database tables corrupted or data inconsistent

### High Priority Issues (Rollback within 1 hour)

1. **Error Rate > 5%**: More than 5% of requests failing
2. **Performance Degradation > 50%**: Page load times doubled
3. **Critical Bug**: Affects all users or prevents core functionality
4. **Regulatory Violation**: Feature violates compliance requirements

### Medium Priority Issues (Consider Rollback)

1. **Error Rate > 2%**: Sustained error rate above 2%
2. **Performance Degradation > 20%**: Noticeable slowdown
3. **User Complaints**: Multiple users reporting issues
4. **Feature Adoption < 10%**: Very low adoption, high bounce rate

### Low Priority Issues (Fix Forward)

1. **Minor Bugs**: Cosmetic issues or edge cases
2. **Performance Issues < 10%**: Slight slowdown
3. **Low Error Rate < 1%**: Occasional errors
4. **UI/UX Issues**: Non-blocking interface problems

---

## Testing Rollback

Always test rollback procedure in staging before production.

### Test Environment Setup

```bash
# Create test database
docker exec unicorn-postgresql psql -U unicorn \
  -c "CREATE DATABASE unicorn_rollback_test;"

# Apply migrations
docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_rollback_test \
  < backend/migrations/002_llm_management_tables.sql

# Add test data
docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_rollback_test <<EOF
INSERT INTO users (id, email, tier) VALUES (gen_random_uuid(), 'test@example.com', 'professional');
EOF
```

### Run Rollback Test

```bash
# 1. Test feature flag disable
export FEATURE_UNIFIED_LLM_HUB=false
docker restart ops-center-staging

# Verify old pages load
curl http://staging.your-domain.com/admin/llm-provider-keys

# 2. Test database rollback
docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_rollback_test \
  < backend/migrations/rollback_llm_management_tables.sql

# Verify tables dropped
docker exec unicorn-postgresql psql -U unicorn -d unicorn_rollback_test \
  -c "\dt llm_*"

# 3. Cleanup test database
docker exec unicorn-postgresql psql -U unicorn \
  -c "DROP DATABASE unicorn_rollback_test;"
```

### Rollback Test Checklist

- [ ] Feature flag disable works instantly
- [ ] Old pages load correctly after flag disable
- [ ] Database rollback script executes without errors
- [ ] All LLM Hub tables dropped successfully
- [ ] No orphaned data or foreign key constraints
- [ ] Old functionality works after rollback
- [ ] No errors in application logs
- [ ] Service restarts cleanly

---

## Post-Rollback Actions

After executing rollback, complete these steps:

### 1. Incident Report

Create incident report with:
- Root cause analysis
- Timeline of events
- Impact assessment
- User communications sent
- Lessons learned
- Action items to prevent recurrence

### 2. User Communication

**Internal Teams**:
```markdown
📋 **LLM Hub Rollback - Post-Mortem**

**Issue**: [Brief description]
**Root Cause**: [Technical cause]
**Duration**: [Time in degraded state]
**Users Affected**: [Number/percentage]
**Data Loss**: None / [Description]
**Resolution**: Rolled back to stable version
**Prevention**: [Action items]
**Timeline**: [Detailed timeline]
```

**Users** (if external impact):
```markdown
We temporarily reverted to our classic LLM management interface
due to [issue]. Your data and configurations are safe. We're
working on improvements and will re-release soon.
```

### 3. Data Reconciliation

If database rollback occurred:

```bash
# Check for orphaned records
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db <<EOF
-- Check for any remaining LLM Hub tables
SELECT table_name FROM information_schema.tables
WHERE table_name LIKE 'llm_%';

-- Check for references to dropped tables
SELECT conname FROM pg_constraint
WHERE confrelid IN (
  SELECT oid FROM pg_class WHERE relname LIKE 'llm_%'
);
EOF
```

### 4. Monitoring Reset

```bash
# Clear metrics from failed deployment
# Reset error rate alerts
# Update status page
# Configure enhanced monitoring for next attempt
```

### 5. Team Retrospective

Schedule retrospective meeting to discuss:
- What went wrong?
- What went well?
- What could we do better?
- What should we do differently next time?

### 6. Fix and Re-Deploy Plan

Document plan for fixing issues and re-deploying:
- Root cause fix
- Additional testing required
- Phased rollout strategy
- Success criteria
- Monitoring plan
- Communication plan

---

## Emergency Contacts

**On-Call Engineer**: [Phone/Slack]
**Engineering Manager**: [Phone/Slack]
**Platform Team**: #platform-oncall
**Status Page**: status.your-domain.com

---

## Rollback Decision Tree

```
Is there a critical issue?
├── YES (data loss, security, outage)
│   └── EXECUTE IMMEDIATE ROLLBACK (< 5 min)
└── NO
    └── Is error rate > 5%?
        ├── YES
        │   └── EXECUTE ROLLBACK WITHIN 1 HOUR
        └── NO
            └── Is performance degraded > 50%?
                ├── YES
                │   └── EXECUTE ROLLBACK WITHIN 1 HOUR
                └── NO
                    └── Can we fix forward?
                        ├── YES
                        │   └── DEPLOY FIX
                        └── NO
                            └── EXECUTE CONTROLLED ROLLBACK
```

---

## Version History

- **v1.0** (2025-10-27): Initial rollback plan
- Feature flag-based rollback (primary)
- Database rollback procedures
- Testing procedures
- Post-rollback actions

---

**Last Updated**: 2025-10-27
**Owner**: Platform Team
**Review Frequency**: Monthly
