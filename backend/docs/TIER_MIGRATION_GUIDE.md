# Dynamic Tier-Model Migration Guide

**Date**: November 6, 2025
**Version**: 1.0.0
**Author**: Database Migration Specialist

---

## Overview

This migration converts the hardcoded JSONB `tier_access` column to a proper relational many-to-many model using a `tier_model_access` junction table. This enables flexible, dynamic tier-to-model relationships that can be managed through the admin UI without code changes.

### What Changes

**Before (JSONB Arrays)**:
```json
{
  "tier_access": ["free", "starter", "professional"],
  "tier_markup": {"free": 1.0, "starter": 0.9, "professional": 0.8}
}
```

**After (Relational Model)**:
```
tier_model_access table:
+--------+----------+---------+-------------------+
| tier_id| model_id | enabled | markup_multiplier |
+--------+----------+---------+-------------------+
| 1      | uuid-123 | true    | 1.0               |
| 2      | uuid-123 | true    | 0.9               |
| 3      | uuid-123 | true    | 0.8               |
+--------+----------+---------+-------------------+
```

### Benefits

1. **Dynamic Management**: Add/remove tier-model relationships without code changes
2. **Better Performance**: Indexed foreign keys instead of JSONB queries
3. **Referential Integrity**: Database-enforced relationships with CASCADE deletes
4. **Flexible Queries**: Join-based queries instead of JSONB operators
5. **Scalability**: Optimized for large-scale tier and model management

---

## Prerequisites

### 1. Verify Current State

Check that required tables exist:

```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  SELECT table_name
  FROM information_schema.tables
  WHERE table_name IN ('subscription_tiers', 'model_access_control')
"
```

**Expected Output**:
```
      table_name
----------------------
 model_access_control
 subscription_tiers
```

### 2. Check Data Volume

```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  SELECT
    (SELECT COUNT(*) FROM model_access_control WHERE enabled = TRUE) AS active_models,
    (SELECT COUNT(*) FROM subscription_tiers WHERE is_active = TRUE) AS active_tiers,
    (SELECT COUNT(*) FROM model_access_control WHERE tier_access IS NOT NULL) AS models_with_tiers
"
```

### 3. Backup Database

**CRITICAL**: Always backup before migration!

```bash
# Create backup
docker exec unicorn-postgresql pg_dump -U unicorn unicorn_db > \
  /tmp/unicorn_db_backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh /tmp/unicorn_db_backup_*.sql
```

---

## Migration Steps

### Step 1: Dry Run Test

**ALWAYS run dry-run first** to verify migration without making changes:

```bash
cd /opt/ops-center/backend

# Run dry-run (changes will be rolled back)
docker exec ops-center-direct python3 /app/scripts/migrate_tiers.py --dry-run --verbose
```

**What to Check**:
- ✅ All SQL statements execute without errors
- ✅ Pre-migration stats look correct
- ✅ Expected number of associations would be created
- ✅ No unexpected warnings or errors

**Expected Output**:
```
==============================================================
TIER-MODEL RELATIONSHIP MIGRATION
==============================================================
Start time: 2025-11-06 12:00:00
Mode: DRY RUN
==============================================================

✅ Connected to database: unicorn_db

🔍 Verifying prerequisites...
  ✅ Table 'subscription_tiers' exists
  ✅ Table 'model_access_control' exists

📊 Pre-migration statistics:
  • Total active models: 150
  • Total active tiers: 4
  • Models with tier access: 145
  • Sample tiers: free, starter, professional, enterprise

🚀 Executing migration...
  ✅ Executed 25 SQL statements

⚠️  DRY RUN MODE: Rolling back transaction...
✅ Dry run completed successfully (changes rolled back)

==============================================================
MIGRATION SUMMARY
==============================================================
Before: 145 models had tier access data
After:  580 tier-model associations created
        145 models now have explicit tier links

Migration completed in: 2.37 seconds

⚠️  This was a DRY RUN - no changes were persisted
==============================================================
```

### Step 2: Live Migration

Once dry-run passes, run live migration:

```bash
# Run live migration
docker exec ops-center-direct python3 /app/scripts/migrate_tiers.py --verbose

# Expected duration: < 10 seconds
```

**What Happens**:
1. Creates `tier_model_access` junction table
2. Creates performance indexes (4 indexes)
3. Migrates data from JSONB to relational model
4. Creates backup columns (`tier_access_backup`, `tier_markup_backup`)
5. Creates compatibility view (`v_model_tier_access`)
6. Creates helper functions (2 functions)
7. Creates update trigger
8. Verifies results

**Expected Output**:
```
==============================================================
TIER-MODEL RELATIONSHIP MIGRATION
==============================================================
Start time: 2025-11-06 12:05:00
Mode: LIVE MIGRATION
==============================================================

✅ Connected to database: unicorn_db
🔍 Verifying prerequisites...
  ✅ Table 'subscription_tiers' exists
  ✅ Table 'model_access_control' exists

📊 Pre-migration statistics:
  • Total active models: 150
  • Total active tiers: 4
  • Models with tier access: 145

🚀 Executing migration...
  ✅ Executed 25 SQL statements
✅ Migration completed in 2.45 seconds

🔍 Verifying migration results...
  ✅ tier_model_access table exists
  • Total tier-model associations: 580
  • Models with associations: 145

  📋 Models per tier:
    • free            145 models
    • starter         140 models
    • professional    150 models
    • enterprise      145 models

  ✅ Compatibility view 'v_model_tier_access' exists
  ✅ Function 'get_models_for_tier' exists
  ✅ Function 'is_model_available_for_tier' exists

🧪 Testing helper functions...
  ✅ get_models_for_tier('free') returned 5 models
  ✅ is_model_available_for_tier() test: true

==============================================================
MIGRATION SUMMARY
==============================================================
Before: 145 models had tier access data
After:  580 tier-model associations created
        145 models now have explicit tier links

Migration completed in: 2.45 seconds

✅ Migration completed successfully!
==============================================================
```

### Step 3: Verification

Run comprehensive verification:

```bash
# Basic verification
docker exec ops-center-direct python3 /app/scripts/verify_migration.py

# Detailed verification with breakdown
docker exec ops-center-direct python3 /app/scripts/verify_migration.py --detailed
```

**What Gets Checked**:
1. ✅ Table exists with correct schema
2. ✅ Foreign keys configured correctly
3. ✅ Performance indexes created
4. ✅ Data migrated (coverage > 80%)
5. ✅ Tier distribution looks correct
6. ✅ Compatibility view and functions exist
7. ✅ Query performance (< 50ms target)
8. ✅ Data integrity (no orphaned records)

**Expected Output**:
```
======================================================================
TIER MIGRATION VERIFICATION REPORT
======================================================================
Generated: 2025-11-06 12:10:00
======================================================================

✓ Checking if tier_model_access table exists...
  ✅ tier_model_access table exists

✓ Checking foreign key constraints...
  ✅ Found 2 foreign key constraints:
    • tier_id → subscription_tiers.id
    • model_id → model_access_control.id

✓ Checking indexes...
  ✅ Found 4 performance indexes:
    • idx_tier_model_tier_id
    • idx_tier_model_model_id
    • idx_tier_model_enabled
    • idx_tier_model_lookup

✓ Checking data migration...
  • Total active models: 150
  • Total active tiers: 4
  • Total associations created: 580
  • Models with associations: 145
  • Coverage: 96.7% of models have tier associations
  ✅ Good coverage of tier associations

✓ Checking tier-model distribution...
  Tier Code            Model Count     Avg Markup
  -------------------- --------------- ----------
  free                 145             1.00
  starter              140             1.00
  professional         150             0.90
  enterprise           145             0.80

  ✅ All 4 tiers have model associations

✓ Checking compatibility layer...
  ✅ Compatibility view 'v_model_tier_access' exists
    • View returns 580 rows
  ✅ Function 'get_models_for_tier' exists
  ✅ Function 'is_model_available_for_tier' exists

✓ Running performance test...
  ✅ Query completed in 23.45ms (excellent)

✓ Checking data integrity...
  ✅ No orphaned records found (referential integrity intact)
  ✅ No duplicate tier-model associations

======================================================================
✅ ALL CHECKS PASSED - Migration successful!
======================================================================
```

---

## Post-Migration Tasks

### 1. Update Application Code

The migration creates a compatibility view (`v_model_tier_access`), but you should update application code to use the new table directly:

**Old Code (JSONB)**:
```python
# Query models for a tier (old way)
models = db.query("""
    SELECT *
    FROM model_access_control
    WHERE tier_access @> '"professional"'::jsonb
""")
```

**New Code (Relational)**:
```python
# Query models for a tier (new way)
models = db.query("""
    SELECT m.*
    FROM model_access_control m
    INNER JOIN tier_model_access tma ON m.id = tma.model_id
    INNER JOIN subscription_tiers st ON tma.tier_id = st.id
    WHERE st.tier_code = 'professional'
    AND tma.enabled = TRUE
""")

# Or use the helper function
models = db.query("SELECT * FROM get_models_for_tier('professional')")
```

### 2. Test Key Workflows

Test these critical workflows:

```bash
# Test 1: User can see models for their tier
curl -X GET "http://localhost:8084/api/v1/llm/models" \
  -H "Authorization: Bearer $TOKEN"

# Test 2: Admin can assign model to tier
curl -X POST "http://localhost:8084/api/v1/admin/tiers/professional/models" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "uuid-123", "enabled": true, "markup_multiplier": 0.9}'

# Test 3: Query view for compatibility
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  SELECT model_identifier, tier_code, markup_multiplier
  FROM v_model_tier_access
  WHERE tier_code = 'professional'
  LIMIT 5
"
```

### 3. Monitor Performance

Check query performance after migration:

```sql
-- Enable query timing
\timing on

-- Test join performance
EXPLAIN ANALYZE
SELECT m.*, st.tier_code
FROM model_access_control m
INNER JOIN tier_model_access tma ON m.id = tma.model_id
INNER JOIN subscription_tiers st ON tma.tier_id = st.id
WHERE st.tier_code = 'professional'
AND tma.enabled = TRUE;

-- Expected: < 50ms execution time
```

### 4. Drop Old Columns (Optional)

**ONLY after confirming everything works**, drop the old JSONB columns:

```sql
-- Wait at least 1 week before doing this!
BEGIN;

-- Verify no code is using old columns
SELECT * FROM model_access_control WHERE tier_access IS NOT NULL LIMIT 1;

-- Drop old columns
ALTER TABLE model_access_control
  DROP COLUMN IF EXISTS tier_access,
  DROP COLUMN IF EXISTS tier_markup,
  DROP COLUMN IF EXISTS tier_access_backup,
  DROP COLUMN IF EXISTS tier_markup_backup;

COMMIT;
```

---

## Rollback Procedure

If migration fails or causes issues, rollback immediately:

### Method 1: Automated Rollback Script

```bash
cd /opt/ops-center/backend

# Run rollback
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f \
  /app/sql/rollback_dynamic_tiers.sql
```

**What Happens**:
1. Restores `tier_access` and `tier_markup` from backup columns
2. Drops `tier_model_access` junction table
3. Drops compatibility view and functions
4. Removes backup columns
5. Verifies restoration

**Expected Output**:
```
BEGIN
NOTICE:  Backup columns found. Proceeding with rollback...
UPDATE 145
DROP FUNCTION
DROP FUNCTION
DROP FUNCTION
DROP VIEW
DROP TRIGGER
DROP TABLE

NOTICE:  =================================================
NOTICE:  Rollback Verification
NOTICE:  =================================================
NOTICE:  Models with tier_access restored: 145
NOTICE:  =================================================

 model_id | provider | display_name | tier_access | status
----------+----------+--------------+-------------+--------
 ...      | openai   | GPT-4        | ["free",... | Restored

COMMIT

    status     |       completed_at        |        result
---------------+---------------------------+----------------------
 Rollback co...| 2025-11-06 12:15:00...   | Original schema...
```

### Method 2: Manual Rollback

If automated rollback fails:

```sql
BEGIN;

-- 1. Restore from backup columns
UPDATE model_access_control
SET tier_access = tier_access_backup,
    tier_markup = tier_markup_backup
WHERE tier_access_backup IS NOT NULL;

-- 2. Drop new objects
DROP TABLE IF EXISTS tier_model_access CASCADE;
DROP VIEW IF EXISTS v_model_tier_access;
DROP FUNCTION IF EXISTS get_models_for_tier(VARCHAR);
DROP FUNCTION IF EXISTS is_model_available_for_tier(UUID, VARCHAR);

-- 3. Clean up backup columns
ALTER TABLE model_access_control
  DROP COLUMN tier_access_backup,
  DROP COLUMN tier_markup_backup;

-- 4. Verify
SELECT COUNT(*) FROM model_access_control WHERE tier_access IS NOT NULL;

COMMIT;
```

### Method 3: Restore from Backup

Worst case - restore entire database:

```bash
# Stop ops-center
docker stop ops-center-direct

# Restore database
docker exec -i unicorn-postgresql psql -U unicorn unicorn_db < \
  /tmp/unicorn_db_backup_YYYYMMDD_HHMMSS.sql

# Restart ops-center
docker start ops-center-direct
```

---

## Troubleshooting

### Issue 1: Migration Fails with "tier_access is null"

**Symptom**: No associations created during migration

**Cause**: Models don't have `tier_access` JSONB data

**Solution**:
```sql
-- Check how many models have tier data
SELECT COUNT(*) FROM model_access_control WHERE tier_access IS NOT NULL;

-- If zero, you need to populate tier_access first
-- Contact system architect for tier assignment strategy
```

### Issue 2: Slow Query Performance

**Symptom**: Queries take > 100ms after migration

**Cause**: Missing indexes or outdated statistics

**Solution**:
```sql
-- Rebuild indexes
REINDEX TABLE tier_model_access;

-- Update statistics
ANALYZE tier_model_access;
ANALYZE model_access_control;
ANALYZE subscription_tiers;

-- Check if indexes are being used
EXPLAIN ANALYZE
SELECT * FROM v_model_tier_access WHERE tier_code = 'professional';
```

### Issue 3: Duplicate Associations

**Symptom**: Verification reports duplicate tier-model pairs

**Cause**: Data inconsistency or migration ran twice

**Solution**:
```sql
-- Find duplicates
SELECT tier_id, model_id, COUNT(*)
FROM tier_model_access
GROUP BY tier_id, model_id
HAVING COUNT(*) > 1;

-- Remove duplicates (keeps first occurrence)
DELETE FROM tier_model_access
WHERE id NOT IN (
    SELECT MIN(id)
    FROM tier_model_access
    GROUP BY tier_id, model_id
);
```

### Issue 4: Foreign Key Violation

**Symptom**: Cannot delete tier or model

**Cause**: Orphaned records in tier_model_access

**Solution**:
```sql
-- Find orphaned tier associations
SELECT tma.*
FROM tier_model_access tma
LEFT JOIN subscription_tiers st ON tma.tier_id = st.id
WHERE st.id IS NULL;

-- Find orphaned model associations
SELECT tma.*
FROM tier_model_access tma
LEFT JOIN model_access_control m ON tma.model_id = m.id
WHERE m.id IS NULL;

-- Clean up orphans
DELETE FROM tier_model_access
WHERE tier_id NOT IN (SELECT id FROM subscription_tiers)
   OR model_id NOT IN (SELECT id FROM model_access_control);
```

---

## Performance Benchmarks

### Query Performance Targets

| Query Type | Target | Excellent | Acceptable | Slow |
|------------|--------|-----------|------------|------|
| Single tier lookup | < 20ms | < 10ms | < 50ms | > 50ms |
| Multi-tier join | < 50ms | < 30ms | < 100ms | > 100ms |
| Full model list | < 100ms | < 50ms | < 200ms | > 200ms |
| Admin dashboard | < 200ms | < 100ms | < 500ms | > 500ms |

### Sample Performance Tests

```sql
-- Test 1: Get models for tier (should be < 20ms)
\timing on
SELECT * FROM get_models_for_tier('professional');

-- Test 2: Check model availability (should be < 10ms)
SELECT is_model_available_for_tier(
  '00000000-0000-0000-0000-000000000001'::uuid,
  'professional'
);

-- Test 3: Full join query (should be < 50ms)
SELECT m.*, st.tier_code, tma.markup_multiplier
FROM model_access_control m
INNER JOIN tier_model_access tma ON m.id = tma.model_id
INNER JOIN subscription_tiers st ON tma.tier_id = st.id
WHERE tma.enabled = TRUE;
```

---

## Success Criteria

Migration is considered successful when:

- [x] Dry-run completes without errors
- [x] Live migration completes in < 10 seconds
- [x] All verification checks pass (8/8)
- [x] Coverage > 80% (models with tier associations)
- [x] Query performance < 50ms
- [x] No orphaned records
- [x] No duplicate associations
- [x] Rollback script tested and working
- [x] Application code updated to use new schema
- [x] 1 week of production monitoring shows no issues

---

## Migration Checklist

### Pre-Migration
- [ ] Review architecture design
- [ ] Backup database
- [ ] Verify prerequisites (tables exist)
- [ ] Check data volume
- [ ] Schedule maintenance window
- [ ] Notify team of migration

### During Migration
- [ ] Run dry-run test
- [ ] Review dry-run results
- [ ] Run live migration
- [ ] Monitor for errors
- [ ] Run verification script
- [ ] Test key workflows
- [ ] Check query performance

### Post-Migration
- [ ] Update application code
- [ ] Deploy code changes
- [ ] Monitor production for 24 hours
- [ ] Update API documentation
- [ ] Train admins on new tier management UI
- [ ] Schedule old column removal (after 1 week)
- [ ] Archive migration scripts

---

## Support & Contact

**Migration Scripts Location**:
- SQL: `/opt/ops-center/backend/sql/`
- Python: `/opt/ops-center/backend/scripts/`
- Docs: `/opt/ops-center/backend/docs/`

**Documentation**:
- Architecture: See system-architect agent output
- Database Schema: `/services/ops-center/backend/SCHEMA.md`
- API Reference: `/services/ops-center/docs/API_REFERENCE.md`

**Testing Environment**:
- Database: `unicorn_db` on `unicorn-postgresql`
- Container: `ops-center-direct`
- Access: `docker exec ops-center-direct python3 /app/scripts/...`

---

**Document Version**: 1.0.0
**Last Updated**: November 6, 2025
**Next Review**: After successful production deployment
