# Rollback Procedure - Database Migrations

**Last Updated**: October 22, 2025
**Emergency Contact**: See project README

---

## When to Rollback

Rollback a migration if:
- ✅ Application errors after migration
- ✅ Data corruption detected
- ✅ Performance degradation
- ✅ Migration applied incorrectly
- ✅ Wrong migration deployed

**DO NOT rollback if**:
- ❌ Migration succeeded but application code has bugs (fix code instead)
- ❌ Data changes are irreversible (restore from backup instead)
- ❌ Just to "start over" (create new migration instead)

---

## Quick Rollback (Standard)

### Step 1: Rollback Last Migration

```bash
./scripts/database/rollback_migration.sh
```

**What happens**:
1. Creates backup of current database
2. Shows migration history
3. Asks for confirmation
4. Executes `downgrade()` function
5. Verifies success

### Step 2: Restart Application

```bash
docker restart ops-center-direct
```

### Step 3: Verify

```bash
# Check migration status
./scripts/database/migration_status.sh

# Check application health
curl http://localhost:8084/api/v1/system/status

# Check logs
docker logs ops-center-direct --tail 50
```

---

## Rollback Multiple Migrations

If you need to rollback several migrations:

```bash
# Rollback 3 migrations
./scripts/database/rollback_migration.sh 3

# Or rollback to specific version
docker exec ops-center-direct bash -c "cd /app && alembic downgrade abc123"
```

**⚠️ WARNING**: Rolling back multiple migrations may cause data loss. Ensure you have backups!

---

## Emergency Rollback (Production)

### Critical Failure - Immediate Action Required

**Step 1: Take Application Offline** (Optional)

```bash
# Stop accepting new requests
docker stop ops-center-direct
```

**Step 2: Quick Rollback**

```bash
# Rollback migration
./scripts/database/rollback_migration.sh

# Confirm success
./scripts/database/migration_status.sh
```

**Step 3: Restore Application**

```bash
# Start application
docker start ops-center-direct

# Wait for startup
sleep 10

# Verify
curl http://localhost:8084/api/v1/system/status
```

**Step 4: Monitor**

```bash
# Watch logs
docker logs ops-center-direct -f

# Check metrics
# - Response times
# - Error rates
# - Database queries
```

---

## Rollback with Data Restoration

If migration caused data loss or corruption:

### Option 1: Rollback + Restore Backup

```bash
# 1. Rollback migration
./scripts/database/rollback_migration.sh

# 2. Restore from backup (before migration)
./scripts/database/restore_database.sh /home/muut/backups/database/unicorn_db_20251022_143025.sql

# 3. Verify data
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT COUNT(*) FROM organizations;"

# 4. Restart application
docker restart ops-center-direct
```

### Option 2: Direct Restore (Faster)

If rollback won't work (e.g., downgrade() is broken):

```bash
# 1. List backups
ls -lht /home/muut/backups/database/

# 2. Restore directly
./scripts/database/restore_database.sh /home/muut/backups/database/unicorn_db_TIMESTAMP.sql

# 3. Fix alembic version table
docker exec ops-center-direct bash -c "cd /app && alembic stamp <previous_version>"

# 4. Verify
./scripts/database/migration_status.sh
```

---

## Rollback Scenarios

### Scenario 1: Migration Applied, Application Broken

**Symptoms**:
- Application won't start
- 500 Internal Server Error
- Database connection errors

**Solution**:
```bash
# 1. Rollback migration
./scripts/database/rollback_migration.sh

# 2. Restart application
docker restart ops-center-direct

# 3. Check logs
docker logs ops-center-direct --tail 100

# 4. Fix migration file
vim alembic/versions/<migration_file>.py

# 5. Test locally before re-applying
```

### Scenario 2: Data Corruption Detected

**Symptoms**:
- Missing data
- Incorrect values
- Foreign key violations

**Solution**:
```bash
# 1. Stop application immediately
docker stop ops-center-direct

# 2. Create emergency backup
./scripts/database/backup_database.sh

# 3. Restore from pre-migration backup
./scripts/database/restore_database.sh /home/muut/backups/database/unicorn_db_BEFORE_MIGRATION.sql

# 4. Verify data integrity
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT COUNT(*) FROM <affected_table>;"

# 5. Investigate migration file
cat alembic/versions/<migration_file>.py

# 6. Fix migration
vim alembic/versions/<migration_file>.py

# 7. Test in development environment first
```

### Scenario 3: Wrong Migration Applied

**Symptoms**:
- Applied migration meant for different environment
- Applied outdated migration
- Applied experimental migration

**Solution**:
```bash
# 1. Rollback immediately
./scripts/database/rollback_migration.sh

# 2. Verify correct version
./scripts/database/migration_status.sh

# 3. Apply correct migration
./scripts/database/run_migrations.sh
```

### Scenario 4: Rollback Fails

**Symptoms**:
- `downgrade()` throws error
- Constraints prevent rollback
- Data dependencies exist

**Solution**:
```bash
# 1. Check error message
docker logs ops-center-direct --tail 50

# 2. Restore from backup instead
./scripts/database/restore_database.sh /home/muut/backups/database/unicorn_db_LATEST.sql

# 3. Update alembic version manually
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "UPDATE alembic_version SET version_num='<correct_version>';"

# 4. Or re-stamp
docker exec ops-center-direct bash -c "cd /app && alembic stamp <correct_version>"
```

---

## Manual Rollback (Advanced)

If scripts don't work:

### Step 1: Check Current Version

```bash
docker exec ops-center-direct bash -c "cd /app && alembic current"
```

### Step 2: Identify Previous Version

```bash
docker exec ops-center-direct bash -c "cd /app && alembic history"
```

### Step 3: Rollback

```bash
docker exec ops-center-direct bash -c "cd /app && alembic downgrade -1"
```

### Step 4: Verify

```bash
./scripts/database/migration_status.sh
```

---

## Prevention - Avoid Needing Rollbacks

### Before Migration

1. **Test locally**
   ```bash
   ./scripts/database/run_migrations.sh --dry-run
   ```

2. **Review migration file**
   ```bash
   cat alembic/versions/<migration_file>.py
   ```

3. **Test rollback works**
   ```bash
   # In development:
   ./scripts/database/run_migrations.sh
   ./scripts/database/rollback_migration.sh
   ./scripts/database/run_migrations.sh
   ```

4. **Backup before applying**
   ```bash
   ./scripts/database/backup_database.sh
   ```

### During Migration

1. **Monitor logs**
   ```bash
   docker logs ops-center-direct -f
   ```

2. **Watch for errors**
   - SQL errors
   - Constraint violations
   - Timeout errors

3. **Verify immediately**
   ```bash
   curl http://localhost:8084/api/v1/system/status
   ```

### After Migration

1. **Test critical paths**
   - User login
   - API calls
   - Data retrieval

2. **Monitor metrics**
   - Response times
   - Error rates
   - Database performance

3. **Keep backup for 24 hours**
   - Don't delete pre-migration backup
   - Keep for quick rollback if needed

---

## Rollback Checklist

**Before Rollback**:
- [ ] Identify problematic migration
- [ ] Create current database backup
- [ ] Notify team/users (if production)
- [ ] Review rollback procedure

**During Rollback**:
- [ ] Execute rollback script
- [ ] Verify migration version changed
- [ ] Check database integrity
- [ ] Restart application
- [ ] Monitor logs

**After Rollback**:
- [ ] Verify application works
- [ ] Test critical functionality
- [ ] Document what went wrong
- [ ] Fix migration file
- [ ] Test fix in development
- [ ] Plan re-deployment

---

## Troubleshooting Rollback Issues

### Issue: "No migrations to rollback"

**Cause**: Database is at initial version

**Solution**: Nothing to rollback, database is clean

### Issue: "Migration downgrade failed"

**Cause**: `downgrade()` function has errors

**Solution**: Restore from backup instead
```bash
./scripts/database/restore_database.sh /home/muut/backups/database/unicorn_db_LATEST.sql
```

### Issue: "Alembic version table missing"

**Cause**: alembic_version table was deleted

**Solution**: Re-stamp database
```bash
docker exec ops-center-direct bash -c "cd /app && alembic stamp head"
```

### Issue: "Cannot rollback, data will be lost"

**Cause**: Migration deleted data, rollback can't restore it

**Solution**: Restore from backup
```bash
./scripts/database/restore_database.sh /home/muut/backups/database/unicorn_db_BEFORE_MIGRATION.sql
```

---

## Emergency Contacts

**Database Issues**:
- Check: `docker logs unicorn-postgresql`
- Restart: `docker restart unicorn-postgresql`

**Application Issues**:
- Check: `docker logs ops-center-direct`
- Restart: `docker restart ops-center-direct`

**Backup Issues**:
- Location: `/home/muut/backups/database/`
- List: `ls -lht /home/muut/backups/database/`

---

## Post-Rollback Actions

### Investigate Root Cause

1. **Review migration file**
   ```bash
   cat alembic/versions/<failed_migration>.py
   ```

2. **Check logs**
   ```bash
   docker logs ops-center-direct | grep -i error
   docker logs unicorn-postgresql | grep -i error
   ```

3. **Test in development**
   - Reproduce issue
   - Fix migration
   - Test upgrade/downgrade

### Fix and Re-deploy

1. **Update migration file**
   - Fix errors
   - Add missing steps
   - Improve downgrade()

2. **Test thoroughly**
   ```bash
   # Development environment:
   ./scripts/database/run_migrations.sh --dry-run
   ./scripts/database/run_migrations.sh
   # Test application
   ./scripts/database/rollback_migration.sh
   ./scripts/database/run_migrations.sh
   ```

3. **Document changes**
   - Update migration comments
   - Add to changelog
   - Notify team

4. **Re-deploy when ready**
   ```bash
   git add alembic/versions/<migration_file>.py
   git commit -m "fix: correct migration issues"
   git push origin main
   ```

---

**Remember**: Rollback is the safety net, but prevention is better! Always test migrations before production deployment.
