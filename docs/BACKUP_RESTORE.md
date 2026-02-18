# Backup and Restore Procedures

**Last Updated**: October 22, 2025
**Critical**: Read this before performing backup/restore operations

---

## Overview

Ops-Center provides automated database backup system with:
- ✅ **Automatic backups** before every migration
- ✅ **Manual backup** on-demand
- ✅ **7-day retention** (configurable)
- ✅ **Metadata tracking** for each backup
- ✅ **Point-in-time recovery** capability
- ✅ **Verification** after backup

**Backup Location**: `/opt/backups/database/`

---

## Quick Reference

```bash
# Create backup
./scripts/database/backup_database.sh

# List backups
ls -lht /opt/backups/database/

# Restore from backup
./scripts/database/restore_database.sh /path/to/backup.sql

# Check backup metadata
cat /opt/backups/database/unicorn_db_TIMESTAMP.metadata.json
```

---

## Backup System

### Automatic Backups

**When backups are created automatically**:

1. **Before migrations**
   ```bash
   ./scripts/database/run_migrations.sh
   # → Creates backup automatically
   ```

2. **Before rollbacks**
   ```bash
   ./scripts/database/rollback_migration.sh
   # → Creates backup automatically
   ```

3. **Before restore**
   ```bash
   ./scripts/database/restore_database.sh /path/to/backup.sql
   # → Creates "safety backup" of current database
   ```

### Manual Backups

**When to create manual backups**:
- ✅ Before major application changes
- ✅ Before production deployment
- ✅ Before testing potentially destructive operations
- ✅ On a regular schedule (daily/weekly)
- ✅ Before data migrations

**How to create manual backup**:

```bash
# Standard backup
./scripts/database/backup_database.sh

# Output:
# - Backup file: unicorn_db_20251022_143025.sql
# - Metadata file: unicorn_db_20251022_143025.metadata.json
# - Size: 2.3 MB
# - Retention: 7 days
```

---

## Backup File Structure

### Backup File (.sql)

Standard PostgreSQL dump file:
```
/opt/backups/database/unicorn_db_20251022_143025.sql
```

**Contents**:
- DROP TABLE IF EXISTS statements
- CREATE TABLE statements
- INSERT statements for all data
- Indexes and constraints
- No ownership or ACL (portable)

**Format**: Plain text SQL (human-readable)

### Metadata File (.metadata.json)

```json
{
  "database": "unicorn_db",
  "timestamp": "20251022_143025",
  "date": "2025-10-22T14:30:25Z",
  "db_size": "2.3 MB",
  "backup_file": "/opt/backups/database/unicorn_db_20251022_143025.sql",
  "backup_size": "1.8 MB",
  "retention_days": 7,
  "expires_on": "2025-10-29",
  "pg_version": "16.1",
  "tables": 12,
  "created_by": "backup_database.sh"
}
```

---

## Backup Retention

**Default Policy**: 7 days

**How it works**:
- Backups older than 7 days are automatically deleted
- Cleanup runs after each backup
- Retention configurable in `backup_database.sh`

**Change retention period**:

Edit `scripts/database/backup_database.sh`:
```bash
RETENTION_DAYS=14  # Keep for 14 days instead
```

**Manual cleanup**:

```bash
# Delete backups older than 7 days
find /opt/backups/database/ -name "unicorn_db_*.sql" -type f -mtime +7 -delete
find /opt/backups/database/ -name "unicorn_db_*.metadata.json" -type f -mtime +7 -delete
```

**Keep important backups**:

```bash
# Move to permanent location
cp /opt/backups/database/unicorn_db_20251022_143025.sql /opt/backups/permanent/
```

---

## Restore Procedures

### Standard Restore

**Step 1: List available backups**

```bash
./scripts/database/restore_database.sh
```

Shows:
```
Available backups:
  /opt/backups/database/unicorn_db_20251022_143025.sql (1.8M, Oct 22 14:30)
  /opt/backups/database/unicorn_db_20251022_120000.sql (1.7M, Oct 22 12:00)
  ...
```

**Step 2: Restore from backup**

```bash
./scripts/database/restore_database.sh /opt/backups/database/unicorn_db_20251022_143025.sql
```

**Step 3: Confirmation**

```
WARNING: This will OVERWRITE the current database!
Are you sure you want to continue? (yes/no):
```

Type `yes` and press Enter.

**Step 4: Automatic safety backup**

Script creates backup of current database:
```
Creating backup of current database first...
✓ Safety backup created: unicorn_db_before_restore_20251022_150000.sql
```

**Step 5: Restoration**

```
Restoring database from backup...
✓ Database restored successfully
✓ Tables restored: 12
```

**Step 6: Verification**

```bash
# Check migration status
./scripts/database/migration_status.sh

# Verify data
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT COUNT(*) FROM organizations;"

# Test application
curl http://localhost:8084/api/v1/system/status
```

---

## Restore Scenarios

### Scenario 1: Rollback Failed, Need Full Restore

**Problem**: Migration rollback didn't work, need to restore

**Solution**:
```bash
# 1. Find backup from before migration
ls -lht /opt/backups/database/ | head -10

# 2. Restore
./scripts/database/restore_database.sh /opt/backups/database/unicorn_db_BEFORE_MIGRATION.sql

# 3. Fix alembic version
docker exec ops-center-direct bash -c "cd /app && alembic stamp <previous_version>"

# 4. Verify
./scripts/database/migration_status.sh

# 5. Restart application
docker restart ops-center-direct
```

### Scenario 2: Data Corruption Detected

**Problem**: Realized data is corrupted, need to restore to earlier state

**Solution**:
```bash
# 1. Stop application immediately
docker stop ops-center-direct

# 2. Create emergency backup of corrupted state (for investigation)
./scripts/database/backup_database.sh

# 3. Find last known good backup
ls -lht /opt/backups/database/ | head -20

# 4. Restore
./scripts/database/restore_database.sh /opt/backups/database/unicorn_db_GOOD_BACKUP.sql

# 5. Verify data integrity
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT COUNT(*) FROM <affected_table>;"

# 6. Start application
docker start ops-center-direct

# 7. Monitor
docker logs ops-center-direct -f
```

### Scenario 3: Accidental Data Deletion

**Problem**: Accidentally deleted important data

**Solution**:
```bash
# Option 1: Restore entire database from backup
./scripts/database/restore_database.sh /opt/backups/database/unicorn_db_LATEST.sql

# Option 2: Extract specific data from backup
# 1. Restore to temporary database
docker exec unicorn-postgresql psql -U unicorn -c "CREATE DATABASE unicorn_db_temp;"
cat /opt/backups/database/unicorn_db_LATEST.sql | docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db_temp

# 2. Copy specific data
docker exec unicorn-postgresql psql -U unicorn -c "INSERT INTO unicorn_db.organizations SELECT * FROM unicorn_db_temp.organizations WHERE id IN (...);"

# 3. Clean up
docker exec unicorn-postgresql psql -U unicorn -c "DROP DATABASE unicorn_db_temp;"
```

### Scenario 4: Restore to Different Environment

**Problem**: Need to restore production backup to development

**Solution**:
```bash
# 1. Copy backup from production
scp production:/opt/backups/database/unicorn_db_PROD.sql ./

# 2. Restore to dev database
./scripts/database/restore_database.sh ./unicorn_db_PROD.sql

# 3. Anonymize sensitive data (optional)
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "UPDATE api_keys SET key_hash = md5(random()::text);"

# 4. Update alembic version if needed
docker exec ops-center-direct bash -c "cd /app && alembic stamp head"
```

---

## Advanced Backup Operations

### Backup Specific Tables

```bash
# Backup single table
docker exec unicorn-postgresql pg_dump -U unicorn -d unicorn_db -t organizations > organizations_backup.sql

# Backup multiple tables
docker exec unicorn-postgresql pg_dump -U unicorn -d unicorn_db -t organizations -t organization_members > orgs_backup.sql
```

### Compressed Backups

For large databases:

```bash
# Create compressed backup
docker exec unicorn-postgresql pg_dump -U unicorn -d unicorn_db | gzip > /opt/backups/database/unicorn_db_$(date +%Y%m%d_%H%M%S).sql.gz

# Restore compressed backup
gunzip -c /opt/backups/database/unicorn_db_20251022_143025.sql.gz | docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db
```

### Custom Format Backups

For faster restore on large databases:

```bash
# Create custom format backup
docker exec unicorn-postgresql pg_dump -U unicorn -d unicorn_db -Fc > /opt/backups/database/unicorn_db_$(date +%Y%m%d_%H%M%S).dump

# Restore custom format
docker exec -i unicorn-postgresql pg_restore -U unicorn -d unicorn_db -c < /opt/backups/database/unicorn_db_20251022_143025.dump
```

---

## Backup Verification

### Verify Backup Integrity

```bash
# 1. Check file exists and not empty
ls -lh /opt/backups/database/unicorn_db_20251022_143025.sql

# 2. Check SQL syntax
head -100 /opt/backups/database/unicorn_db_20251022_143025.sql

# 3. Test restore to temp database
docker exec unicorn-postgresql psql -U unicorn -c "CREATE DATABASE unicorn_db_verify;"
cat /opt/backups/database/unicorn_db_20251022_143025.sql | docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db_verify

# 4. Verify table count
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db_verify -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"

# 5. Clean up
docker exec unicorn-postgresql psql -U unicorn -c "DROP DATABASE unicorn_db_verify;"
```

### Test Restore Process

Regularly test that backups can be restored:

```bash
# Monthly backup verification test
# 1. Create temp database
docker exec unicorn-postgresql psql -U unicorn -c "CREATE DATABASE test_restore;"

# 2. Restore latest backup
cat /opt/backups/database/unicorn_db_LATEST.sql | docker exec -i unicorn-postgresql psql -U unicorn -d test_restore

# 3. Verify
docker exec unicorn-postgresql psql -U unicorn -d test_restore -c "\dt"

# 4. Clean up
docker exec unicorn-postgresql psql -U unicorn -c "DROP DATABASE test_restore;"
```

---

## Automated Backup Schedule

### Using Cron

Setup automatic daily backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/ops-center/scripts/database/backup_database.sh >> /var/log/ops-center-backup.log 2>&1
```

### Using Systemd Timer

More modern alternative to cron:

```bash
# Create timer unit
sudo cat > /etc/systemd/system/ops-center-backup.timer <<EOF
[Unit]
Description=Ops-Center Daily Database Backup

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Create service unit
sudo cat > /etc/systemd/system/ops-center-backup.service <<EOF
[Unit]
Description=Ops-Center Database Backup Service

[Service]
Type=oneshot
ExecStart=/opt/ops-center/scripts/database/backup_database.sh
User=muut
Group=muut
EOF

# Enable and start
sudo systemctl enable ops-center-backup.timer
sudo systemctl start ops-center-backup.timer

# Check status
sudo systemctl status ops-center-backup.timer
```

---

## Off-site Backups

For disaster recovery, store backups off-site:

### Option 1: Cloud Storage (S3/GCS)

```bash
# Install AWS CLI
sudo apt install awscli

# Configure
aws configure

# Sync backups to S3
aws s3 sync /opt/backups/database/ s3://my-bucket/ops-center-backups/
```

### Option 2: Remote Server

```bash
# Add to backup script
rsync -avz /opt/backups/database/ backup-server:/backups/ops-center/
```

### Option 3: NAS/Network Drive

```bash
# Mount network share
sudo mount -t nfs backup-nas:/backups /mnt/backups

# Copy backups
cp /opt/backups/database/*.sql /mnt/backups/ops-center/
```

---

## Troubleshooting

### Issue: Backup File Too Large

**Solution**: Use compression
```bash
docker exec unicorn-postgresql pg_dump -U unicorn -d unicorn_db | gzip > backup.sql.gz
```

### Issue: Restore Takes Too Long

**Solution**: Use custom format (faster)
```bash
docker exec unicorn-postgresql pg_dump -U unicorn -d unicorn_db -Fc > backup.dump
docker exec -i unicorn-postgresql pg_restore -U unicorn -d unicorn_db -c -j 4 < backup.dump
```

### Issue: Out of Disk Space

**Solution**: Clean old backups
```bash
# Remove backups older than 3 days
find /opt/backups/database/ -name "unicorn_db_*.sql" -mtime +3 -delete

# Or move to archive storage
mv /opt/backups/database/*.sql /mnt/archive/
```

### Issue: Backup Script Fails

**Solution**: Check permissions and container status
```bash
# Check if directory writable
touch /opt/backups/database/test.txt && rm /opt/backups/database/test.txt

# Check container running
docker ps | grep unicorn-postgresql

# Check disk space
df -h /opt/backups/
```

---

## Best Practices

### DO ✅

1. **Backup before major changes**
   - Migrations
   - Application updates
   - Data imports

2. **Test restore process regularly**
   - Monthly verification
   - Document restore time

3. **Keep multiple backup copies**
   - Local backups (7 days)
   - Off-site backups (30 days)
   - Archive backups (yearly)

4. **Monitor backup success**
   - Check logs
   - Verify file size
   - Test restore

5. **Document backup procedures**
   - Update this guide
   - Train team members

### DON'T ❌

1. **Don't rely on single backup**
   - Multiple copies in different locations

2. **Don't skip backup testing**
   - Untested backups may not restore

3. **Don't ignore backup failures**
   - Investigate immediately

4. **Don't delete backups prematurely**
   - May need older backups

5. **Don't store backups only locally**
   - Off-site storage essential

---

## Emergency Contacts

**Backup Location**: `/opt/backups/database/`
**Scripts Location**: `/opt/ops-center/scripts/database/`
**Documentation**: `/opt/ops-center/docs/`

**Database Container**: `unicorn-postgresql`
**Application Container**: `ops-center-direct`

---

**Remember**: Backups are only useful if they can be restored. Test your backup and restore procedures regularly!
