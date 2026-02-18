# Rollback Guide

## Overview

The rollback system automatically reverts Ops-Center to a previous working state when deployments fail. This guide covers automatic and manual rollback procedures.

## Quick Rollback

```bash
# Automatic rollback to latest backup
./scripts/rollback.sh

# Rollback to specific backup
./scripts/rollback.sh --backup-timestamp=20251022_153000
```

## Backup System

### Automatic Backups

Backups are created automatically:
- **Before every deployment**: Database, configuration, container state
- **Retention**: 30 days (configurable)
- **Location**: `/opt/ops-center/backups/`

### Backup Contents

Each backup includes:
1. **Database dump**: `db_backup_TIMESTAMP.sql`
2. **Docker Compose config**: `compose_TIMESTAMP.yml`
3. **Container state**: `containers_TIMESTAMP.txt`
4. **Latest marker**: `.latest_backup` (points to most recent)

### Manual Backup

```bash
# Create manual backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup database
docker exec unicorn-postgresql pg_dump -U unicorn unicorn_db > \
  /opt/ops-center/backups/db_backup_${TIMESTAMP}.sql

# Backup configuration
cp docker-compose.prod.yml /opt/ops-center/backups/compose_${TIMESTAMP}.yml

# Save container state
docker ps > /opt/ops-center/backups/containers_${TIMESTAMP}.txt
```

## Automatic Rollback

### When It Triggers

Automatic rollback occurs when:
1. Health check fails after deployment
2. Database migration fails
3. Service startup fails
4. Deployment script encounters error

### What It Does

1. **Stops current services**: Gracefully stops running containers
2. **Restores database**: Loads database from backup
3. **Reverts configuration**: Restores previous docker-compose.yml
4. **Restarts services**: Starts services with previous images
5. **Verifies health**: Runs health check to confirm restoration

### Disabling Automatic Rollback

```bash
# Deploy without automatic rollback
./scripts/deploy.sh --no-rollback

# Useful for debugging deployment issues
```

## Manual Rollback

### Step-by-Step Procedure

#### 1. Identify Backup to Restore

```bash
# List available backups
ls -lh /opt/ops-center/backups/db_backup_*

# Show latest 10 backups
ls -lt /opt/ops-center/backups/db_backup_* | head -10

# Check latest backup marker
cat /opt/ops-center/backups/.latest_backup
```

#### 2. Verify Backup Integrity

```bash
# Check database backup
docker exec -i unicorn-postgresql psql -U unicorn -d test_db < \
  /opt/ops-center/backups/db_backup_20251022_153000.sql

# Should complete without errors

# Drop test database
docker exec unicorn-postgresql psql -U unicorn -c "DROP DATABASE test_db;"
```

#### 3. Stop Current Services

```bash
# Graceful stop
docker compose -f docker-compose.prod.yml stop ops-center-backend ops-center-frontend

# Or force stop if needed
docker stop ops-center-backend ops-center-frontend
```

#### 4. Backup Current State (Safety)

```bash
# Before rollback, backup current state
SAFETY_BACKUP=$(date +%Y%m%d_%H%M%S)

docker exec unicorn-postgresql pg_dump -U unicorn unicorn_db > \
  /opt/ops-center/backups/pre_rollback_${SAFETY_BACKUP}.sql
```

#### 5. Restore Database

```bash
# Drop current database
docker exec unicorn-postgresql psql -U unicorn -c "DROP DATABASE unicorn_db;"

# Create fresh database
docker exec unicorn-postgresql psql -U unicorn -c "CREATE DATABASE unicorn_db;"

# Restore from backup
docker exec -i unicorn-postgresql psql -U unicorn unicorn_db < \
  /opt/ops-center/backups/db_backup_20251022_153000.sql
```

#### 6. Restore Configuration

```bash
# Restore docker-compose configuration
cp /opt/ops-center/backups/compose_20251022_153000.yml docker-compose.prod.yml
```

#### 7. Pull Previous Images (if needed)

```bash
# Check container state file for image versions
cat /opt/ops-center/backups/containers_20251022_153000.txt

# Pull previous backend image
docker pull ghcr.io/unicorn-commander/ops-center-backend:main-abc1234

# Pull previous frontend image
docker pull ghcr.io/unicorn-commander/ops-center-frontend:main-abc1234
```

#### 8. Restart Services

```bash
# Start services
docker compose -f docker-compose.prod.yml up -d ops-center-backend ops-center-frontend

# Wait for startup
sleep 15
```

#### 9. Verify Rollback

```bash
# Run health check
./scripts/health_check.sh

# Check logs
docker logs ops-center-direct --tail 50

# Test endpoints
curl https://unicorncommander.ai/api/v1/health
curl https://unicorncommander.ai/api/v1/system/status
```

## Rollback Scenarios

### Scenario 1: Failed Deployment (Immediate)

**Situation**: Deployment just failed, automatic rollback didn't trigger

**Action**:
```bash
# Rollback to latest backup (before failed deployment)
./scripts/rollback.sh

# Check health
./scripts/health_check.sh
```

### Scenario 2: Bug Discovered After Deployment

**Situation**: Deployment succeeded but bug found hours later

**Action**:
```bash
# List recent backups
ls -lt /opt/ops-center/backups/db_backup_* | head -5

# Identify backup before problematic deployment
# Example: 20251022_140000 was before deployment at 15:00

# Rollback to that backup
./scripts/rollback.sh --backup-timestamp=20251022_140000

# Verify
./scripts/health_check.sh
```

### Scenario 3: Database Corruption

**Situation**: Database issues detected, need to restore

**Action**:
```bash
# Stop services
docker compose stop ops-center-backend

# Restore database only
docker exec unicorn-postgresql psql -U unicorn -c "DROP DATABASE unicorn_db;"
docker exec unicorn-postgresql psql -U unicorn -c "CREATE DATABASE unicorn_db;"
docker exec -i unicorn-postgresql psql -U unicorn unicorn_db < \
  /opt/ops-center/backups/db_backup_TIMESTAMP.sql

# Restart services
docker compose start ops-center-backend
```

### Scenario 4: Partial Rollback (Frontend Only)

**Situation**: Backend fine, frontend has issues

**Action**:
```bash
# Stop frontend
docker compose stop ops-center-frontend

# Pull previous frontend image
docker pull ghcr.io/unicorn-commander/ops-center-frontend:previous-tag

# Update docker-compose.yml with previous tag
# Or restore from backup:
cp /opt/ops-center/backups/compose_TIMESTAMP.yml docker-compose.prod.yml

# Restart frontend only
docker compose up -d ops-center-frontend

# Verify
curl https://unicorncommander.ai/
```

## Rollback Verification

### Critical Checks

After rollback, verify:

#### 1. Service Health
```bash
./scripts/health_check.sh
```

#### 2. Database Integrity
```bash
# Check user count
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c \
  "SELECT COUNT(*) FROM users;"

# Verify recent data
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c \
  "SELECT email, created_at FROM users ORDER BY created_at DESC LIMIT 5;"
```

#### 3. Authentication
```bash
# Test SSO login
curl -I https://unicorncommander.ai/auth/oidc/login

# Should redirect to Keycloak
```

#### 4. API Endpoints
```bash
# System status
curl https://unicorncommander.ai/api/v1/system/status

# User analytics
curl -H "Authorization: Bearer $TOKEN" \
  https://unicorncommander.ai/api/v1/admin/users/analytics/summary
```

#### 5. Frontend
```bash
# Homepage
curl -I https://unicorncommander.ai/

# Admin dashboard
curl -I https://unicorncommander.ai/admin
```

## Rollback Limitations

### What Can't Be Rolled Back

1. **External API calls**: Third-party API calls made during the failed deployment
2. **Emails sent**: Cannot unsend emails sent to users
3. **Stripe charges**: Payment transactions are irreversible
4. **User actions**: User-generated content created during deployment
5. **Cached data**: Redis cache may contain mixed old/new data

### Data Loss Scenarios

**Between backup and failure**: Changes made between backup creation and failure will be lost

**Example**:
```
14:00 - Backup created (automatic before deployment)
14:05 - Deployment starts
14:10 - User registers account
14:15 - Deployment fails
14:15 - Rollback to 14:00 backup
Result: User registration at 14:10 is lost
```

**Mitigation**:
```bash
# Enable maintenance mode before deployment
echo "Maintenance mode enabled" > /opt/ops-center/public/maintenance.html

# Restore after rollback
rm /opt/ops-center/public/maintenance.html
```

## Troubleshooting Rollback

### Rollback Script Fails

**Problem**: `./scripts/rollback.sh` exits with error

**Solution**:
```bash
# Check if backup exists
ls -lh /opt/ops-center/backups/

# Verify backup timestamp
cat /opt/ops-center/backups/.latest_backup

# Try manual rollback procedure (see above)
```

### Database Restore Fails

**Problem**: Database restore produces errors

**Solution**:
```bash
# Check PostgreSQL logs
docker logs unicorn-postgresql | tail -50

# Verify backup file integrity
head -50 /opt/ops-center/backups/db_backup_TIMESTAMP.sql
tail -50 /opt/ops-center/backups/db_backup_TIMESTAMP.sql

# Try restoring to different database first
docker exec unicorn-postgresql psql -U unicorn -c "CREATE DATABASE test_restore;"
docker exec -i unicorn-postgresql psql -U unicorn test_restore < backup.sql
```

### Service Won't Start After Rollback

**Problem**: Containers fail to start after rollback

**Solution**:
```bash
# Check logs
docker logs ops-center-direct

# Verify configuration
docker exec ops-center-direct env | grep -E "POSTGRES|REDIS"

# Test connectivity
docker exec ops-center-direct ping unicorn-postgresql
docker exec ops-center-direct nc -zv unicorn-postgresql 5432

# Restart dependencies
docker restart unicorn-postgresql unicorn-redis
sleep 10
docker restart ops-center-direct
```

### Health Check Fails After Rollback

**Problem**: Health check fails even though rollback completed

**Solution**:
```bash
# Check individual services
./scripts/health_check.sh --service=database
./scripts/health_check.sh --service=redis
./scripts/health_check.sh --service=backend

# Review logs for errors
docker logs ops-center-direct --since 5m | grep -i error

# Verify database connection
docker exec ops-center-direct python -c "
from backend.database import test_connection
test_connection()
"
```

## Post-Rollback Actions

### 1. Investigate Root Cause

```bash
# Collect logs from failed deployment
docker logs ops-center-direct > failed_deployment_$(date +%Y%m%d).log

# Review deployment log
cat /opt/ops-center/deployment/deploy.log

# Check resource usage at time of failure
docker stats --no-stream
df -h
free -h
```

### 2. Notify Stakeholders

```bash
# Send notification (if configured)
curl -X POST $SLACK_WEBHOOK -d '{
  "text": "⚠️ Rollback completed. System restored to previous version."
}'
```

### 3. Document Incident

Create incident report:
- What failed
- When it was detected
- Rollback timestamp
- What was lost (if anything)
- Root cause analysis
- Prevention measures

### 4. Plan Next Deployment

Before next deployment:
- Fix identified issues
- Test in staging
- Update deployment documentation
- Increase monitoring
- Consider blue-green deployment

## Backup Management

### Cleanup Old Backups

```bash
# Delete backups older than 30 days
find /opt/ops-center/backups/ -name "db_backup_*.sql" -mtime +30 -delete
find /opt/ops-center/backups/ -name "compose_*.yml" -mtime +30 -delete
find /opt/ops-center/backups/ -name "containers_*.txt" -mtime +30 -delete

# Or use automated cleanup (add to cron)
0 2 * * * find /opt/ops-center/backups/ -name "*.sql" -mtime +30 -delete
```

### Compress Old Backups

```bash
# Compress backups older than 7 days
find /opt/ops-center/backups/ -name "db_backup_*.sql" -mtime +7 \
  -exec gzip {} \;

# Decompress for restore
gunzip /opt/ops-center/backups/db_backup_20251022_153000.sql.gz
```

### Backup to Remote Storage

```bash
# Sync to S3 (example)
aws s3 sync /opt/ops-center/backups/ s3://ops-center-backups/

# Or rsync to remote server
rsync -avz /opt/ops-center/backups/ backup-server:/backups/ops-center/
```

## Best Practices

1. **Test rollback regularly**: Practice rollback procedure quarterly
2. **Verify backups**: Test restore process monthly
3. **Automate cleanup**: Set up cron jobs for old backup deletion
4. **Monitor backup size**: Ensure sufficient disk space
5. **Document changes**: Keep deployment log with backup timestamp
6. **Quick access**: Keep rollback script easily accessible
7. **Multiple backups**: Maintain at least 7 days of backups

## References

- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [CI/CD Pipeline](./CI_CD_PIPELINE.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
