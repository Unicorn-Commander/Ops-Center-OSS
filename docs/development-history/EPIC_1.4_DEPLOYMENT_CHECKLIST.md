# Epic 1.4 Deployment Checklist

**Storage & Backup System - Production Deployment**

## Pre-Deployment Checks

### 1. Environment Verification

- [ ] **Verify Python version** (3.11+)
  ```bash
  python3 --version
  ```

- [ ] **Verify required packages installed**
  ```bash
  pip install -r backend/requirements.txt
  ```

- [ ] **Verify disk space available**
  ```bash
  df -h /opt/ops-center
  # Minimum: 50GB free for backups
  ```

- [ ] **Verify Docker is running**
  ```bash
  docker ps
  docker-compose ps
  ```

- [ ] **Check PostgreSQL is accessible**
  ```bash
  docker exec unicorn-postgresql psql -U unicorn -c "SELECT 1"
  ```

- [ ] **Check Redis is accessible**
  ```bash
  docker exec unicorn-redis redis-cli ping
  ```

### 2. Configuration Review

- [ ] **Review backup configuration** (`backend/.env`)
  - `BACKUP_DIR` - Where backups are stored
  - `BACKUP_RETENTION_DAYS` - How long to keep backups (default: 7)
  - `MIN_BACKUPS_KEEP` - Minimum backups to retain (default: 3)

- [ ] **Review cloud storage configuration** (optional)
  - `CLOUD_BACKUP_ENABLED` - Enable/disable cloud backups
  - `CLOUD_PROVIDER` - aws, gcp, or azure
  - `CLOUD_BUCKET` - Bucket/container name
  - `CLOUD_REGION` - Cloud region
  - Cloud credentials (AWS_ACCESS_KEY_ID, etc.)

- [ ] **Review notification configuration** (optional)
  - `EMAIL_NOTIFICATIONS` - Enable/disable email alerts
  - `EMAIL_TO` - Notification recipient
  - `SMTP_HOST` - SMTP server
  - `SMTP_PORT` - SMTP port

### 3. Script Verification

- [ ] **Verify all scripts exist**
  ```bash
  ls -lh scripts/automated-backup.sh
  ls -lh scripts/verify-backup.sh
  ls -lh scripts/disaster-recovery.sh
  ls -lh scripts/cleanup-old-backups.sh
  ls -lh scripts/sync-cloud-backups.sh
  ```

- [ ] **Make scripts executable**
  ```bash
  chmod +x scripts/*.sh
  ```

- [ ] **Test script help pages**
  ```bash
  ./scripts/automated-backup.sh --help
  ./scripts/verify-backup.sh --help
  ./scripts/disaster-recovery.sh --help
  ```

### 4. Test Execution

- [ ] **Run unit tests**
  ```bash
  cd backend
  pytest tests/test_storage_backup.py -v
  ```

- [ ] **Run integration tests**
  ```bash
  chmod +x tests/integration/test_epic_1.4.sh
  ./tests/integration/test_epic_1.4.sh
  ```

- [ ] **Verify test results**
  - All tests should pass
  - Check `tests/integration/test_epic_1.4.log` for details

### 5. Backup Directory Setup

- [ ] **Create backup directories**
  ```bash
  mkdir -p backups
  mkdir -p backups/rollback
  mkdir -p logs
  ```

- [ ] **Set proper permissions**
  ```bash
  chmod 755 backups
  chmod 700 backups/rollback
  ```

- [ ] **Create log files**
  ```bash
  touch /var/log/uc-cloud-backup.log
  touch /var/log/uc-cloud-backup-verify.log
  touch /var/log/uc-cloud-recovery.log
  chmod 644 /var/log/uc-cloud-*.log
  ```

## Deployment Steps

### 1. Database Migration

- [ ] **Apply database migrations** (if applicable)
  ```bash
  cd backend
  alembic upgrade head
  ```

- [ ] **Verify database schema**
  ```bash
  docker exec unicorn-postgresql psql -U unicorn -d ops_center -c "\dt"
  ```

### 2. API Deployment

- [ ] **Stop backend service**
  ```bash
  docker-compose stop ops-center-direct
  ```

- [ ] **Pull latest code**
  ```bash
  git pull origin main
  ```

- [ ] **Rebuild container** (if needed)
  ```bash
  docker-compose build ops-center-direct
  ```

- [ ] **Start backend service**
  ```bash
  docker-compose up -d ops-center-direct
  ```

- [ ] **Check service health**
  ```bash
  curl http://localhost:8084/api/v1/health
  ```

### 3. Frontend Deployment

- [ ] **Stop frontend service** (if separate)
  ```bash
  # If using separate frontend container
  docker-compose stop ops-center-frontend
  ```

- [ ] **Build frontend assets**
  ```bash
  cd frontend
  npm run build
  ```

- [ ] **Start frontend service**
  ```bash
  docker-compose up -d ops-center-frontend
  ```

### 4. Schedule Configuration

- [ ] **Set up automated backups** (cron job)
  ```bash
  # Add to crontab
  crontab -e

  # Daily backup at 2 AM
  0 2 * * * /opt/ops-center/scripts/automated-backup.sh >> /var/log/uc-cloud-backup-cron.log 2>&1

  # Weekly cleanup (Sunday 3 AM)
  0 3 * * 0 /opt/ops-center/scripts/cleanup-old-backups.sh --force --days 7 --keep 3 >> /var/log/uc-cloud-cleanup-cron.log 2>&1
  ```

- [ ] **Verify cron jobs**
  ```bash
  crontab -l
  ```

### 5. Cloud Storage Setup (Optional)

- [ ] **Configure AWS credentials** (if using AWS)
  ```bash
  aws configure
  # Or set environment variables:
  export AWS_ACCESS_KEY_ID="your-key"
  export AWS_SECRET_ACCESS_KEY="your-secret"
  export AWS_DEFAULT_REGION="us-east-1"
  ```

- [ ] **Test cloud upload**
  ```bash
  CLOUD_BACKUP_ENABLED=true \
  CLOUD_PROVIDER=aws \
  CLOUD_BUCKET=your-bucket \
  ./scripts/automated-backup.sh --cloud
  ```

- [ ] **Verify backup in cloud**
  ```bash
  aws s3 ls s3://your-bucket/backups/
  ```

## Post-Deployment Verification

### 1. API Endpoint Testing

- [ ] **Test backup creation endpoint**
  ```bash
  curl -X POST http://localhost:8084/api/v1/storage/backups \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -d '{"include_volumes": true, "include_config": true}'
  ```

- [ ] **Test backup listing endpoint**
  ```bash
  curl http://localhost:8084/api/v1/storage/backups \
    -H "Authorization: Bearer YOUR_TOKEN"
  ```

- [ ] **Test backup details endpoint**
  ```bash
  curl http://localhost:8084/api/v1/storage/backups/{backup_id} \
    -H "Authorization: Bearer YOUR_TOKEN"
  ```

- [ ] **Test schedule configuration endpoint**
  ```bash
  curl http://localhost:8084/api/v1/storage/schedule \
    -H "Authorization: Bearer YOUR_TOKEN"
  ```

### 2. Functional Testing

- [ ] **Create test backup**
  ```bash
  ./scripts/automated-backup.sh
  ```

- [ ] **Verify backup integrity**
  ```bash
  ./scripts/verify-backup.sh --latest
  ```

- [ ] **Test backup restoration** (dry run)
  ```bash
  ./scripts/disaster-recovery.sh --latest --dry-run
  ```

- [ ] **Test backup cleanup** (dry run)
  ```bash
  ./scripts/cleanup-old-backups.sh --dry-run
  ```

### 3. Monitoring Setup

- [ ] **Verify backup logs are being created**
  ```bash
  tail -f /var/log/uc-cloud-backup.log
  ```

- [ ] **Check disk usage monitoring**
  ```bash
  df -h | grep backups
  ```

- [ ] **Test email notifications** (if configured)
  ```bash
  EMAIL_NOTIFICATIONS=true \
  EMAIL_TO="admin@example.com" \
  ./scripts/automated-backup.sh
  ```

### 4. Security Verification

- [ ] **Verify backup files have correct permissions**
  ```bash
  ls -la backups/
  # Should be 600 or 640
  ```

- [ ] **Check API authentication is working**
  ```bash
  # Should fail without token
  curl http://localhost:8084/api/v1/storage/backups
  ```

- [ ] **Verify cloud credentials are not in logs**
  ```bash
  grep -i "secret\|password\|key" /var/log/uc-cloud-*.log
  # Should not find credentials
  ```

## Rollback Procedures

### If Deployment Fails

1. **Stop new services**
   ```bash
   docker-compose stop ops-center-direct
   ```

2. **Restore from backup** (if needed)
   ```bash
   ./scripts/disaster-recovery.sh --latest --force
   ```

3. **Revert code changes**
   ```bash
   git checkout HEAD~1
   docker-compose up -d ops-center-direct
   ```

4. **Verify old version is working**
   ```bash
   curl http://localhost:8084/api/v1/health
   ```

### If Backup System Fails

1. **Check script logs**
   ```bash
   tail -100 /var/log/uc-cloud-backup.log
   ```

2. **Verify disk space**
   ```bash
   df -h
   ```

3. **Check Docker containers**
   ```bash
   docker ps
   docker logs unicorn-postgresql
   ```

4. **Run manual backup**
   ```bash
   ./scripts/automated-backup.sh --verbose
   ```

5. **Disable automated backups** (if critical)
   ```bash
   crontab -e
   # Comment out backup cron job
   ```

## Documentation Updates

- [ ] **Update API documentation**
  - Add new endpoints to OpenAPI spec
  - Update Postman collection

- [ ] **Update user guide**
  - Add backup/restore procedures
  - Document recovery scenarios

- [ ] **Update operations runbook**
  - Backup schedule
  - Recovery procedures
  - Monitoring guidelines

## Success Criteria

### Functional Requirements
- ✅ Backups can be created successfully
- ✅ Backups can be verified for integrity
- ✅ Backups can be restored successfully
- ✅ Old backups are cleaned up automatically
- ✅ Cloud sync is functional (if configured)
- ✅ Disaster recovery works end-to-end

### Performance Requirements
- ✅ Backup creation completes in < 30 minutes
- ✅ Backup verification completes in < 5 minutes
- ✅ API endpoints respond in < 2 seconds
- ✅ Cleanup runs without blocking other operations

### Security Requirements
- ✅ All backups are checksummed
- ✅ API endpoints require authentication
- ✅ Cloud credentials are encrypted
- ✅ Backup files have restrictive permissions

### Reliability Requirements
- ✅ All automated tests pass (100%)
- ✅ No errors in service logs
- ✅ Backups complete without manual intervention
- ✅ Recovery works from any backup

## Sign-off

**Deployment Date**: _______________

**Deployed By**: _______________

**Verified By**: _______________

**Issues Encountered**:

_______________________________________________

_______________________________________________

**Resolution Notes**:

_______________________________________________

_______________________________________________

**Production Ready**: [ ] Yes  [ ] No

---

## Quick Reference Commands

### Create Manual Backup
```bash
cd /opt/ops-center
./scripts/automated-backup.sh
```

### Verify Latest Backup
```bash
./scripts/verify-backup.sh --latest
```

### Restore from Latest Backup
```bash
./scripts/disaster-recovery.sh --latest
```

### Clean Old Backups
```bash
./scripts/cleanup-old-backups.sh --days 7 --keep 3
```

### Sync to Cloud
```bash
CLOUD_BACKUP_ENABLED=true \
CLOUD_PROVIDER=aws \
CLOUD_BUCKET=your-bucket \
./scripts/sync-cloud-backups.sh --mode upload
```

### View Logs
```bash
tail -f /var/log/uc-cloud-backup.log
tail -f /var/log/uc-cloud-recovery.log
```

### Emergency Recovery
```bash
# 1. Stop services
docker-compose stop

# 2. Restore from backup
./scripts/disaster-recovery.sh --latest --force --auto-confirm

# 3. Verify services
docker-compose ps
curl http://localhost:8084/api/v1/health
```

---

**Document Version**: 1.0
**Last Updated**: October 23, 2025
**Next Review**: November 23, 2025
