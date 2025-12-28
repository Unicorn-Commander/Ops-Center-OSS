# Tier Migration Quick Reference

**Date**: November 6, 2025
**Version**: 1.0.0

---

## 🚀 Quick Commands

### Dry Run (Safe Test)
```bash
docker exec ops-center-direct python3 /app/scripts/migrate_tiers.py --dry-run
```

### Live Migration
```bash
# 1. Backup first!
docker exec unicorn-postgresql pg_dump -U unicorn unicorn_db > /tmp/db_backup_$(date +%Y%m%d).sql

# 2. Run migration
docker exec ops-center-direct python3 /app/scripts/migrate_tiers.py --verbose

# 3. Verify results
docker exec ops-center-direct python3 /app/scripts/verify_migration.py
```

### Rollback (If Needed)
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f \
  /app/sql/rollback_dynamic_tiers.sql
```

---

## 📁 File Locations

| File | Purpose | Location |
|------|---------|----------|
| Migration SQL | Creates tables, indexes, views | `/backend/sql/migrate_to_dynamic_tiers.sql` |
| Rollback SQL | Restores original schema | `/backend/sql/rollback_dynamic_tiers.sql` |
| Migration Script | Python execution wrapper | `/backend/scripts/migrate_tiers.py` |
| Verification Script | Post-migration checks | `/backend/scripts/verify_migration.py` |
| Full Guide | Complete documentation | `/backend/docs/TIER_MIGRATION_GUIDE.md` |

---

## ✅ Success Checklist

**Before Migration**:
- [ ] Database backup created
- [ ] Dry-run test passes
- [ ] Pre-migration stats reviewed

**During Migration**:
- [ ] Migration completes in < 10 seconds
- [ ] No SQL errors reported
- [ ] Expected associations created

**After Migration**:
- [ ] All verification checks pass (8/8)
- [ ] Query performance < 50ms
- [ ] Key workflows tested
- [ ] Application code updated

---

## 🔍 What Gets Created

### Tables
- `tier_model_access` - Junction table (many-to-many)

### Indexes
- `idx_tier_model_tier_id` - Fast tier lookups
- `idx_tier_model_model_id` - Fast model lookups
- `idx_tier_model_enabled` - Filter enabled only
- `idx_tier_model_lookup` - Combined tier+model+enabled

### Views
- `v_model_tier_access` - Compatibility view (backward compat)

### Functions
- `get_models_for_tier(tier_code)` - Get all models for a tier
- `is_model_available_for_tier(model_id, tier_code)` - Check availability

### Triggers
- `trigger_update_tier_model_access_timestamp` - Auto-update `updated_at`

---

## 📊 Expected Results

### Data Migration
- **Before**: 145 models with JSONB `tier_access` arrays
- **After**: 580 tier-model associations (145 models × 4 tiers avg)

### Performance
- **Query Time**: < 50ms for tier-model joins
- **Coverage**: > 80% of active models have tier associations
- **Migration Time**: < 10 seconds total

---

## 🐛 Quick Troubleshooting

### No Associations Created
```sql
-- Check if tier_access data exists
SELECT COUNT(*) FROM model_access_control WHERE tier_access IS NOT NULL;
-- If 0, models need tier_access populated first
```

### Slow Queries
```sql
-- Rebuild indexes
REINDEX TABLE tier_model_access;
ANALYZE tier_model_access;
```

### Duplicate Associations
```sql
-- Find duplicates
SELECT tier_id, model_id, COUNT(*)
FROM tier_model_access
GROUP BY tier_id, model_id
HAVING COUNT(*) > 1;

-- Remove duplicates
DELETE FROM tier_model_access
WHERE id NOT IN (
    SELECT MIN(id) FROM tier_model_access GROUP BY tier_id, model_id
);
```

---

## 📖 Usage Examples

### Query Models for Tier
```sql
-- Old way (JSONB)
SELECT * FROM model_access_control
WHERE tier_access @> '"professional"'::jsonb;

-- New way (relational)
SELECT m.*
FROM model_access_control m
INNER JOIN tier_model_access tma ON m.id = tma.model_id
INNER JOIN subscription_tiers st ON tma.tier_id = st.id
WHERE st.tier_code = 'professional' AND tma.enabled = TRUE;

-- Or use helper function
SELECT * FROM get_models_for_tier('professional');
```

### Add Model to Tier
```sql
INSERT INTO tier_model_access (tier_id, model_id, markup_multiplier, enabled)
VALUES (
    (SELECT id FROM subscription_tiers WHERE tier_code = 'professional'),
    'model-uuid-here'::uuid,
    0.9,
    TRUE
);
```

### Check Model Availability
```sql
SELECT is_model_available_for_tier(
    'model-uuid-here'::uuid,
    'professional'
);
-- Returns: true or false
```

---

## 🎯 Key Points

1. **Always dry-run first** - Test without committing changes
2. **Backup before migration** - Safety first!
3. **Verify after migration** - Run verification script
4. **Keep backup columns** - Don't drop `tier_access_backup` for 1 week
5. **Monitor performance** - Check query times after migration
6. **Update app code** - Use new relational model in queries
7. **Test rollback** - Verify rollback script works before deleting backups

---

## 📞 Support

- Full Guide: `/backend/docs/TIER_MIGRATION_GUIDE.md`
- Database Schema: `/backend/SCHEMA.md`
- Architecture: See system-architect agent output

---

**Document Version**: 1.0.0
**Last Updated**: November 6, 2025
