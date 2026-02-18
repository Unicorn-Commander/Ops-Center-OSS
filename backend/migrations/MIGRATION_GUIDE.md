# Unified LLM Management System - Migration Guide

**Epic 3.2**: Database Migration for Consolidated LLM Management
**Version**: 1.0.0
**Date**: October 27, 2025

---

## Overview

This migration consolidates 4 fragmented LLM pages into a unified management system by creating comprehensive database tables for:

1. **Cloud Provider Management** - OpenRouter, OpenAI, Anthropic, etc.
2. **Local Model Servers** - Ollama, vLLM, LMStudio infrastructure
3. **Model Deployments** - Running model instances
4. **Access Control** - User/role/tier-based permissions
5. **Usage Tracking** - Cost analytics and billing integration
6. **Audit Logging** - Complete audit trail

---

## Files Included

| File | Purpose | Size |
|------|---------|------|
| `create_llm_management_tables.sql` | Forward migration (creates all tables) | ~25KB |
| `rollback_llm_management_tables.sql` | Rollback migration (safe cleanup) | ~8KB |
| `seed_tier_rules.sql` | Initial tier access rules (5 tiers) | ~7KB |
| `test_migration.sh` | Automated test suite | ~12KB |
| `MIGRATION_GUIDE.md` | This document | ~15KB |

---

## Pre-Migration Checklist

### 1. Backup Database

**CRITICAL**: Always backup before running migrations!

```bash
# Backup entire database
docker exec unicorn-postgresql pg_dump -U unicorn unicorn_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Or use pg_dumpall for all databases
docker exec unicorn-postgresql pg_dumpall -U unicorn > full_backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Verify PostgreSQL is Running

```bash
# Check container status
docker ps | grep unicorn-postgresql

# Test connection
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT version();"
```

### 3. Check Existing Tables

```bash
# List existing LLM-related tables
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt" | grep -E "(llm|model)"
```

Expected existing tables (if Epic 3.1 was completed):
- `llm_providers` (from create_llm_tables.sql)
- `llm_models` (from create_llm_tables.sql)
- `llm_usage_logs` (from create_llm_tables.sql)
- `model_servers` (from 001_model_servers.sql)

### 4. Review Migration Scripts

```bash
# Navigate to migrations directory
cd /opt/ops-center/backend/migrations

# Review forward migration
less create_llm_management_tables.sql

# Review rollback migration
less rollback_llm_management_tables.sql
```

---

## Migration Process

### Option A: Test First (RECOMMENDED)

**Always test migrations before applying to production!**

```bash
# Navigate to migrations directory
cd /opt/ops-center/backend/migrations

# Run full test suite
./test_migration.sh

# Expected output:
# ✓ PostgreSQL container is running
# ✓ Forward migration found
# ✓ Rollback migration found
# ✓ Seed data found
# ✓ Test database 'llm_test_db' created
# ✓ Forward migration applied successfully
# ✓ All 10 tables created successfully
# ✓ Created 25+ indexes
# ✓ Audit log is append-only (record preserved)
# ✓ Seeded 30+ tier rules
# ✓ All 5 tiers configured
# ✓ Rollback migration applied successfully
# ✓ All new tables dropped successfully
# ✓ All tests passed successfully!

# If tests pass, proceed to production migration
```

**Test Options**:
```bash
# Test forward migration only
./test_migration.sh --forward-only

# Test rollback only
./test_migration.sh --rollback-only

# Clean up test database
./test_migration.sh --cleanup
```

### Option B: Direct Production Migration

**WARNING**: Only use if you've tested thoroughly or are confident!

#### Step 1: Apply Forward Migration

```bash
# Navigate to migrations directory
cd /opt/ops-center/backend/migrations

# Apply forward migration
docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db < create_llm_management_tables.sql

# Expected output:
# CREATE EXTENSION
# CREATE TABLE
# CREATE INDEX
# ... (multiple lines)
# NOTICE:  Verified 10 LLM management tables exist
# COMMIT
```

#### Step 2: Verify Tables Created

```bash
# Check all tables exist
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN (
        'llm_providers',
        'model_servers',
        'installed_models',
        'model_deployments',
        'model_permissions',
        'tier_model_rules',
        'llm_usage_logs',
        'model_pricing',
        'daily_cost_summary',
        'audit_log'
    )
    ORDER BY table_name;
"

# Expected: 10 rows showing all tables
```

#### Step 3: Apply Seed Data

```bash
# Apply tier access rules
docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db < seed_tier_rules.sql

# Expected output:
# INSERT 0 6
# INSERT 0 9
# INSERT 0 18
# INSERT 0 12
# INSERT 0 5
# NOTICE:  Seeded 50 rules across 5 tiers
# COMMIT
```

#### Step 4: Verify Seed Data

```bash
# Check tier rules
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
    SELECT tier_code, COUNT(*) as rule_count
    FROM tier_model_rules
    GROUP BY tier_code
    ORDER BY tier_code;
"

# Expected:
#   tier_code   | rule_count
# --------------+------------
#  enterprise   |         12
#  free         |          4
#  professional |         18
#  starter      |          9
#  trial        |          6
```

---

## Verification Queries

### Check Table Counts

```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
    SELECT 'llm_providers' as table_name, COUNT(*) as count FROM llm_providers
    UNION ALL
    SELECT 'model_servers', COUNT(*) FROM model_servers
    UNION ALL
    SELECT 'installed_models', COUNT(*) FROM installed_models
    UNION ALL
    SELECT 'model_deployments', COUNT(*) FROM model_deployments
    UNION ALL
    SELECT 'model_permissions', COUNT(*) FROM model_permissions
    UNION ALL
    SELECT 'tier_model_rules', COUNT(*) FROM tier_model_rules
    UNION ALL
    SELECT 'llm_usage_logs', COUNT(*) FROM llm_usage_logs
    UNION ALL
    SELECT 'model_pricing', COUNT(*) FROM model_pricing
    UNION ALL
    SELECT 'daily_cost_summary', COUNT(*) FROM daily_cost_summary
    UNION ALL
    SELECT 'audit_log', COUNT(*) FROM audit_log
    ORDER BY table_name;
"
```

### Check Indexes

```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
    SELECT schemaname, tablename, indexname
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND tablename IN (
        'llm_providers', 'model_servers', 'installed_models',
        'model_deployments', 'model_permissions', 'tier_model_rules',
        'llm_usage_logs', 'model_pricing', 'daily_cost_summary', 'audit_log'
    )
    ORDER BY tablename, indexname;
"
```

### Test Audit Log Protection

```bash
# Try to insert (should work)
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
    INSERT INTO audit_log (user_id, action_type, resource_type, resource_id)
    VALUES ('test-user', 'test_action', 'test_resource', 'test-123');
"

# Try to update (should be blocked silently)
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
    UPDATE audit_log SET user_id = 'hacker' WHERE resource_id = 'test-123';
"

# Try to delete (should be blocked silently)
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
    DELETE FROM audit_log WHERE resource_id = 'test-123';
"

# Verify record still exists
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
    SELECT user_id FROM audit_log WHERE resource_id = 'test-123';
"
# Expected: user_id = 'test-user' (unchanged)
```

### Test Tier Access Rules

```bash
# Check if trial user can access GPT-4 (should be FALSE)
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
    SELECT allowed FROM tier_model_rules
    WHERE tier_code = 'trial'
    AND 'openai/gpt-4' LIKE model_pattern
    ORDER BY priority DESC
    LIMIT 1;
"
# Expected: allowed = f (false)

# Check if professional user can access GPT-4 (should be TRUE)
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
    SELECT allowed, max_requests_per_day FROM tier_model_rules
    WHERE tier_code = 'professional'
    AND 'openai/gpt-4' LIKE model_pattern
    ORDER BY priority DESC
    LIMIT 1;
"
# Expected: allowed = t (true), max_requests_per_day = 300
```

---

## Rollback Procedure

**If something goes wrong**, you can safely rollback the migration.

### Step 1: Apply Rollback Migration

```bash
cd /opt/ops-center/backend/migrations

docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db < rollback_llm_management_tables.sql
```

### Step 2: Verify Rollback

```bash
# Check that new tables are dropped
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN (
        'installed_models',
        'model_deployments',
        'model_permissions',
        'tier_model_rules',
        'model_pricing',
        'daily_cost_summary',
        'audit_log'
    )
    ORDER BY table_name;
"
# Expected: 0 rows (all new tables dropped)
```

### Step 3: Restore from Backup (if needed)

```bash
# If rollback isn't sufficient, restore from backup
docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db < backup_20251027_143000.sql
```

---

## Post-Migration Tasks

### 1. Update Backend API

The new tables need corresponding API endpoints. Update these files:

- `backend/llm_management_api.py` - Main LLM management API
- `backend/server.py` - Register new routes
- `backend/tier_access_control.py` - Tier-based access logic

### 2. Update Frontend

Update frontend components to use new unified API:

- `src/pages/LLMManagement.jsx` - Main LLM management page
- `src/components/ModelServerManager.jsx` - Server management
- `src/components/ModelDeploymentManager.jsx` - Deployment management

### 3. Populate Initial Data

```bash
# Add your existing vLLM server
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
    INSERT INTO model_servers (name, type, host, port, enabled)
    VALUES ('vLLM-RTX-5090', 'vllm', 'unicorn-vllm', 8000, true)
    ON CONFLICT DO NOTHING;
"

# Add existing Ollama server (if available)
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
    INSERT INTO model_servers (name, type, host, port, enabled)
    VALUES ('Ollama-Local', 'ollama', 'localhost', 11434, true)
    ON CONFLICT DO NOTHING;
"
```

### 4. Monitor Performance

```bash
# Check query performance
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
    SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
    FROM pg_stat_user_indexes
    WHERE schemaname = 'public'
    AND tablename LIKE '%llm%'
    ORDER BY idx_scan DESC;
"
```

---

## Troubleshooting

### Issue: "relation already exists"

**Cause**: Tables from previous migration attempts exist
**Solution**: Either use the rollback script first, or manually drop conflicting tables

```bash
# Check existing tables
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt"

# Drop specific table if needed
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "DROP TABLE IF EXISTS installed_models CASCADE;"
```

### Issue: "column already exists"

**Cause**: Migration was partially applied
**Solution**: The migration uses `IF NOT EXISTS` and `ADD COLUMN IF NOT EXISTS`, so re-running should be safe

```bash
# Re-apply migration (idempotent)
docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db < create_llm_management_tables.sql
```

### Issue: Foreign key constraint errors

**Cause**: Referenced table doesn't exist yet
**Solution**: Ensure dependencies are created first. The migration handles this automatically.

### Issue: Test script fails

**Cause**: PostgreSQL container name mismatch
**Solution**: Edit `test_migration.sh` line 24 to match your container name

```bash
# Find your PostgreSQL container name
docker ps | grep postgres

# Edit test script
vim test_migration.sh
# Change CONTAINER_NAME="unicorn-postgresql" to your container name
```

### Issue: Permission denied

**Cause**: Script not executable
**Solution**: Make script executable

```bash
chmod +x test_migration.sh
```

---

## Database Schema Summary

### New Tables Created

| Table | Purpose | Rows (initial) |
|-------|---------|----------------|
| `installed_models` | Models installed on servers | 0 |
| `model_deployments` | Running model instances | 0 |
| `model_permissions` | Fine-grained access control | 0 |
| `tier_model_rules` | Subscription tier rules | 50+ |
| `model_pricing` | Per-model pricing data | 0 |
| `daily_cost_summary` | Pre-aggregated cost analytics | 0 |
| `audit_log` | Immutable audit trail | 0 |

### Extended Tables

| Table | Changes | Backward Compatible |
|-------|---------|---------------------|
| `llm_providers` | Added `api_key_encrypted`, `metadata` | ✅ Yes |
| `model_servers` | Added `location`, `host`, `port`, `gpu_id`, `auto_start` | ✅ Yes |
| `llm_usage_logs` | Added `provider`, `server_id`, `deployment_id`, `source`, `cost_usd`, `latency_ms` | ✅ Yes |

---

## Migration Timeline

**Estimated Time**: 5-10 minutes

- **Backup Database**: 1-2 minutes
- **Test Migration**: 2-3 minutes
- **Apply Forward Migration**: 1 minute
- **Apply Seed Data**: 30 seconds
- **Verification**: 1-2 minutes
- **Restart Services**: 1 minute

---

## Support & Questions

**Documentation Location**: `/opt/ops-center/backend/migrations/`

**Related Epic**: Epic 3.2 - Unified LLM Management System

**Database Specialist**: Backend Database Specialist Agent

**Test Results**: Run `./test_migration.sh` to generate test report

---

## Next Steps

After successful migration:

1. ✅ Update backend API to use new tables
2. ✅ Update frontend to call new endpoints
3. ✅ Populate initial server and model data
4. ✅ Test tier-based access control
5. ✅ Monitor audit log for all changes
6. ✅ Set up cost tracking for cloud providers

**Ready to begin Phase 2: Backend API Development!**
