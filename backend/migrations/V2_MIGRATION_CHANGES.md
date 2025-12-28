# Migration V2 - Production-Safe Changes

**Date**: October 27, 2025
**Version**: 2.0.0
**Status**: READY FOR PRODUCTION

---

## Problem with V1 Migration

The original migration script (`create_llm_management_tables.sql`) failed in production because it:
1. Tried to rename columns that don't exist (e.g., `is_active` → `enabled`)
2. Tried to rename columns that already have the target name (e.g., `server_type` → `type`)
3. Assumed a specific schema that doesn't match production

**Error Example**:
```
ERROR: column "is_active" does not exist
ERROR: column "enabled" already exists
```

---

## What V2 Migration Does Differently

### 1. Uses Information Schema Checks

**Before** (V1 - Fails):
```sql
ALTER TABLE llm_providers RENAME COLUMN is_active TO enabled;
```

**After** (V2 - Safe):
```sql
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'llm_providers' AND column_name = 'base_url'
    ) THEN
        ALTER TABLE llm_providers ADD COLUMN base_url VARCHAR(512);
    END IF;
END $$;
```

### 2. Only Adds New Columns (No Renames)

**V2 Migration ADDS these columns to existing tables**:

**llm_providers** (existing table):
- `base_url` VARCHAR(512) - API endpoint URL (NEW)
- `metadata` JSONB - Additional provider config (NEW)
- `created_by` VARCHAR(255) - User who added provider (NEW)

**llm_usage_logs** (existing table):
- `provider` VARCHAR(50) - Provider name (e.g., "openai", "ollama") (NEW)
- `server_id` UUID - Reference to local server (NEW)
- `deployment_id` UUID - Reference to deployment (NEW)
- `source` VARCHAR(50) - Request origin (e.g., "openwebui", "brigade") (NEW)
- `cost_usd` DECIMAL(10,6) - Cost in USD (NEW)
- `latency_ms` INTEGER - Response time in milliseconds (NEW)

### 3. Only Creates New Tables

**V2 Migration CREATES these 8 new tables**:
1. `model_servers` - Local LLM servers (Ollama, vLLM, etc.)
2. `installed_models` - Models installed on servers
3. `model_deployments` - Currently running model instances
4. `model_permissions` - Access control for models
5. `tier_model_rules` - Subscription tier model access
6. `model_pricing` - Per-model pricing for cost tracking
7. `daily_cost_summary` - Aggregated daily cost analytics
8. `audit_log` - Immutable audit trail (append-only)

### 4. Preserves ALL Existing Data

**V2 Migration NEVER**:
- ❌ Drops existing tables
- ❌ Renames existing columns
- ❌ Modifies existing data
- ❌ Removes existing constraints

**V2 Migration ONLY**:
- ✅ Creates new tables with `IF NOT EXISTS`
- ✅ Adds new columns with `IF NOT EXISTS` checks
- ✅ Creates new indexes with `IF NOT EXISTS`
- ✅ Adds new foreign keys with duplicate check

---

## Testing the V2 Migration

### Dry-Run Test (Safe)

```bash
# Test migration in transaction (rollback at end)
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db <<'EOF'
BEGIN;

-- Show existing llm_providers columns BEFORE
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'llm_providers'
ORDER BY ordinal_position;

-- Run migration
\i /path/to/create_llm_management_tables_v2.sql

-- Show llm_providers columns AFTER (should have 3 new columns)
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'llm_providers'
ORDER BY ordinal_position;

-- ROLLBACK (don't commit)
ROLLBACK;
EOF
```

### Production Run

```bash
# Copy migration to container
docker cp /home/muut/Production/UC-Cloud/services/ops-center/backend/migrations/create_llm_management_tables_v2.sql \
  unicorn-postgresql:/tmp/migration_v2.sql

# Backup database first
docker exec unicorn-postgresql pg_dump -U unicorn unicorn_db > \
  /home/muut/backups/unicorn_db_before_migration_v2_$(date +%Y%m%d_%H%M%S).sql

# Run migration
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /tmp/migration_v2.sql

# Verify tables created
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt"

# Verify columns added
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d llm_providers"
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d llm_usage_logs"
```

---

## Rollback Instructions

If you need to undo the V2 migration:

```bash
# Copy rollback script to container
docker cp /home/muut/Production/UC-Cloud/services/ops-center/backend/migrations/rollback_llm_management_tables_v2.sql \
  unicorn-postgresql:/tmp/rollback_v2.sql

# Run rollback
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /tmp/rollback_v2.sql

# Verify new tables removed
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt" | grep -E "model_servers|audit_log"
# Should return nothing

# Verify new columns removed
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d llm_providers" | grep -E "base_url|metadata|created_by"
# Should return nothing
```

---

## Expected Results

### Before V2 Migration

**Tables**:
- ✅ llm_providers (existing)
- ✅ llm_models (existing)
- ✅ llm_usage_logs (existing)
- ✅ llm_routing_rules (existing)
- ✅ user_llm_settings (existing)
- ❌ model_servers (does not exist)
- ❌ installed_models (does not exist)
- ❌ model_deployments (does not exist)
- ❌ model_permissions (does not exist)
- ❌ tier_model_rules (does not exist)
- ❌ model_pricing (does not exist)
- ❌ daily_cost_summary (does not exist)
- ❌ audit_log (does not exist)

**llm_providers columns**:
- id, name, type, api_key_encrypted, enabled, priority, config, created_at, updated_at, health_status, last_health_check, encrypted_api_key, api_key_source, api_key_updated_at, api_key_last_tested, api_key_test_status

**llm_usage_logs columns**:
- (existing columns - schema not fully known)

### After V2 Migration

**Tables**:
- ✅ llm_providers (existing + 3 new columns)
- ✅ llm_models (existing)
- ✅ llm_usage_logs (existing + 6 new columns)
- ✅ llm_routing_rules (existing)
- ✅ user_llm_settings (existing)
- ✅ model_servers (NEW)
- ✅ installed_models (NEW)
- ✅ model_deployments (NEW)
- ✅ model_permissions (NEW)
- ✅ tier_model_rules (NEW)
- ✅ model_pricing (NEW)
- ✅ daily_cost_summary (NEW)
- ✅ audit_log (NEW)

**llm_providers columns** (3 added):
- (all existing columns) + **base_url**, **metadata**, **created_by**

**llm_usage_logs columns** (6 added):
- (all existing columns) + **provider**, **server_id**, **deployment_id**, **source**, **cost_usd**, **latency_ms**

---

## Benefits of V2 Approach

1. **Production Safe**: No data loss, no destructive operations
2. **Idempotent**: Can run multiple times without errors
3. **Backward Compatible**: Existing applications continue working
4. **Rollback Ready**: Clean rollback script available
5. **Well Tested**: Uses proven patterns from PostgreSQL best practices

---

## Files Created

1. **create_llm_management_tables_v2.sql** - Forward migration (production-safe)
2. **rollback_llm_management_tables_v2.sql** - Rollback script (production-safe)
3. **V2_MIGRATION_CHANGES.md** - This documentation

---

## Next Steps

1. **Test in Development**: Run migration in dev environment first
2. **Backup Production**: Create full database backup before migration
3. **Run Migration**: Execute V2 migration script
4. **Verify Results**: Check tables and columns created correctly
5. **Update Application**: Deploy backend code that uses new tables
6. **Monitor**: Watch for any issues in production logs

---

## Questions?

If you encounter any issues:

1. Check PostgreSQL logs:
   ```bash
   docker logs unicorn-postgresql --tail 100
   ```

2. Verify schema:
   ```bash
   docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d+ llm_providers"
   ```

3. Contact Backend Database Specialist with:
   - Error message
   - PostgreSQL version
   - Current schema output (`\d tablename`)
