# BorgBackup Integration Guide

**Quick guide to integrate BorgBackup endpoints into Ops-Center**

---

## Step 1: Verify BorgBackup Installation

```bash
# Check if borg is installed
docker exec ops-center-direct which borg

# If not installed, install it
docker exec ops-center-direct apt-get update
docker exec ops-center-direct apt-get install -y borgbackup fuse

# Verify version
docker exec ops-center-direct borg --version
# Expected: borg 1.2.x or higher
```

---

## Step 2: Add Borg Manager to API

Edit `/backend/storage_backup_api.py`:

```python
# At the top, with other imports (line ~26)
from backup_borg import BorgBackupManager

# After creating router (line ~35)
# Initialize BorgBackup manager
borg_manager = BorgBackupManager()
```

---

## Step 3: Copy Borg Endpoints

Copy the endpoint code from `storage_backup_borg_endpoints.py` to the end of `storage_backup_api.py`.

**Location**: Append after line 940 (after `_verify_backup` function)

The file contains:
- 9 Pydantic models (BorgInitRequest, BorgCreateRequest, etc.)
- 11 API endpoint functions

Total addition: ~600 lines

---

## Step 4: Test Installation

```bash
# Restart ops-center to load new endpoints
docker restart ops-center-direct

# Wait for startup
sleep 10

# Check if Borg endpoints are registered
docker logs ops-center-direct | grep -i borg

# Test API documentation
curl http://localhost:8084/docs
# Look for /backups/borg/* endpoints
```

---

## Step 5: Initialize Test Repository

```bash
# Create test repository directory
docker exec ops-center-direct mkdir -p /app/backups/borg-test

# Initialize repository via API
curl -X POST http://localhost:8084/api/v1/backups/borg/init \
  -H "Content-Type: application/json" \
  -d '{
    "repository_path": "/app/backups/borg-test",
    "passphrase": "TestPassphrase123!",
    "encryption_mode": "repokey-blake2"
  }'

# Expected response:
# {
#   "success": true,
#   "repository_path": "/app/backups/borg-test",
#   "encryption_mode": "repokey-blake2",
#   "repository_id": "...",
#   "message": "Repository initialized successfully"
# }
```

---

## Step 6: Create Test Backup

```bash
# Create some test files
docker exec ops-center-direct mkdir -p /tmp/test-data
docker exec ops-center-direct bash -c 'echo "test file 1" > /tmp/test-data/file1.txt'
docker exec ops-center-direct bash -c 'echo "test file 2" > /tmp/test-data/file2.txt'

# Create backup via API
curl -X POST http://localhost:8084/api/v1/backups/borg/create \
  -H "Content-Type: application/json" \
  -d '{
    "archive_name": "test_backup",
    "source_paths": ["/tmp/test-data"],
    "repository_path": "/app/backups/borg-test",
    "passphrase": "TestPassphrase123!",
    "compression": "lz4"
  }'

# Expected response:
# {
#   "success": true,
#   "archive_name": "test_backup_20251023_XXXXXX",
#   "original_size": ...,
#   "compressed_size": ...,
#   "deduplicated_size": ...,
#   "nfiles": 2,
#   "compression_ratio": ...,
#   "deduplication_ratio": ...,
#   "duration": ...
# }
```

---

## Step 7: List Archives

```bash
curl -X GET "http://localhost:8084/api/v1/backups/borg/archives?repository_path=/app/backups/borg-test&passphrase=TestPassphrase123!"

# Expected response:
# [
#   {
#     "name": "test_backup_20251023_XXXXXX",
#     "archive": "test_backup_20251023_XXXXXX",
#     "time": "2025-10-23T...",
#     "hostname": "ops-center-direct",
#     "username": "root",
#     "id": "..."
#   }
# ]
```

---

## Step 8: Get Repository Info

```bash
curl -X GET "http://localhost:8084/api/v1/backups/borg/info?repository_path=/app/backups/borg-test&passphrase=TestPassphrase123!"

# Expected response:
# {
#   "repository_id": "...",
#   "location": "/app/backups/borg-test",
#   "encryption_mode": "repokey-blake2",
#   "unique_chunks": ...,
#   "total_chunks": ...,
#   "total_size": ...,
#   "unique_size": ...,
#   "deduplication_ratio": ...
# }
```

---

## Troubleshooting

### Error: "borg: command not found"

```bash
# Install borgbackup in container
docker exec ops-center-direct apt-get update
docker exec ops-center-direct apt-get install -y borgbackup

# Verify
docker exec ops-center-direct which borg
```

### Error: "Failed to import BorgBackupManager"

```bash
# Check if backup_borg.py exists
docker exec ops-center-direct ls -la /app/backend/backup_borg.py

# Check Python imports
docker exec ops-center-direct python3 -c "from backup_borg import BorgBackupManager; print('OK')"

# Check logs for import errors
docker logs ops-center-direct | grep -i "import error\|module not found"
```

### Error: "Passphrase encryption failed"

The BorgBackupManager generates a new encryption key on startup. In production, you should:

1. Generate a persistent key:
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())
```

2. Store it securely in environment variable:
```bash
# In .env.auth or docker-compose
BORG_ENCRYPTION_KEY=your_base64_key_here
```

3. Pass it to BorgBackupManager:
```python
import os
encryption_key = os.getenv("BORG_ENCRYPTION_KEY")
borg_manager = BorgBackupManager(encryption_key=encryption_key)
```

### Error: "FUSE not available"

For mount functionality:

```bash
# Install FUSE
docker exec ops-center-direct apt-get install -y fuse

# Add FUSE device to docker-compose.yml
devices:
  - /dev/fuse:/dev/fuse
cap_add:
  - SYS_ADMIN

# Restart container
docker restart ops-center-direct
```

---

## Production Deployment Checklist

- [ ] BorgBackup installed in container
- [ ] FUSE installed (if using mount feature)
- [ ] Persistent encryption key configured
- [ ] Backup repository directory created
- [ ] Repository initialized with strong passphrase
- [ ] Test backup created and verified
- [ ] Retention policy configured
- [ ] Scheduled backups configured (if using)
- [ ] Monitoring/alerting configured
- [ ] Backup verification scheduled (weekly)
- [ ] Disaster recovery plan documented
- [ ] Passphrase backup stored securely

---

## Security Best Practices

### Passphrase Management

1. **Strong Passphrases**: Minimum 20 characters, mixed case, numbers, symbols
2. **Secure Storage**: Use secrets manager (HashiCorp Vault, AWS Secrets Manager)
3. **Key Rotation**: Rotate repository passphrases annually
4. **Access Control**: Limit who can access passphrases

### Repository Security

1. **File Permissions**: Repository directory should be 0700
2. **Encryption Mode**: Use `repokey-blake2` for best security
3. **Off-site Backups**: Store on separate physical location
4. **Immutable Backups**: Use append-only mode for ransomware protection

### Audit & Compliance

1. **Audit Logging**: All Borg operations logged to audit trail
2. **Access Tracking**: Monitor who accesses backups
3. **Retention Compliance**: Configure retention to meet regulatory requirements
4. **Verification**: Regular integrity checks

---

## Recommended Retention Policy

```json
{
  "keep_hourly": 24,    // Last 24 hours
  "keep_daily": 7,      // Last 7 days
  "keep_weekly": 4,     // Last 4 weeks
  "keep_monthly": 6,    // Last 6 months
  "keep_yearly": 2      // Last 2 years
}
```

Adjust based on:
- Data change frequency
- Storage capacity
- Recovery requirements
- Compliance regulations

---

## Scheduled Backup Example

To schedule daily backups, add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * curl -X POST http://localhost:8084/api/v1/backups/borg/create \
  -H "Content-Type: application/json" \
  -d '{"archive_name":"daily_backup","source_paths":["/var/lib/docker/volumes"],"repository_path":"/backups/borg-repo","passphrase":"'$BORG_PASSPHRASE'","compression":"zstd,3"}'

# Weekly prune on Sundays at 3 AM
0 3 * * 0 curl -X POST http://localhost:8084/api/v1/backups/borg/prune \
  -H "Content-Type: application/json" \
  -d '{"repository_path":"/backups/borg-repo","passphrase":"'$BORG_PASSPHRASE'","keep_daily":7,"keep_weekly":4,"keep_monthly":6}'

# Weekly compact on Sundays at 4 AM
0 4 * * 0 curl -X POST "http://localhost:8084/api/v1/backups/borg/compact?repository_path=/backups/borg-repo&passphrase=$BORG_PASSPHRASE"
```

---

## Monitoring & Alerts

### Metrics to Track

1. **Backup Success Rate**: Should be >99%
2. **Backup Duration**: Track for performance degradation
3. **Repository Size**: Monitor growth rate
4. **Deduplication Ratio**: Should remain stable
5. **Last Successful Backup**: Alert if >25 hours old

### Alert Conditions

```python
# Example alert logic
if last_backup_age > 25_hours:
    send_alert("Backup overdue")

if backup_success_rate < 0.99:
    send_alert("High failure rate")

if deduplication_ratio < 1.5:
    send_alert("Poor deduplication")

if repository_growth_rate > expected:
    send_alert("Unexpected data growth")
```

---

## Disaster Recovery

### Recovery Time Objective (RTO)

- **Critical data**: <1 hour
- **Standard data**: <4 hours
- **Archived data**: <24 hours

### Recovery Point Objective (RPO)

- **Hourly backups**: 1 hour data loss max
- **Daily backups**: 24 hours data loss max

### Recovery Procedure

1. **Identify Required Archive**:
   ```bash
   curl -X GET "http://localhost:8084/api/v1/backups/borg/archives?repository_path=/backups/borg-repo&passphrase=$BORG_PASSPHRASE"
   ```

2. **Verify Archive Integrity**:
   ```bash
   curl -X POST "http://localhost:8084/api/v1/backups/borg/check?repository_path=/backups/borg-repo&passphrase=$BORG_PASSPHRASE"
   ```

3. **Extract to Temporary Location**:
   ```bash
   curl -X POST http://localhost:8084/api/v1/backups/borg/extract/archive_name \
     -H "Content-Type: application/json" \
     -d '{"archive_name":"daily_backup_20251023_120000","target_path":"/tmp/restore","repository_path":"/backups/borg-repo","passphrase":"'$BORG_PASSPHRASE'"}'
   ```

4. **Verify Restored Data**
5. **Copy to Production Location**
6. **Restart Services**
7. **Document Recovery in Incident Log**

---

## Cost Estimation

### Storage Requirements

| Backup Frequency | Data Size | Deduplication | Storage Needed |
|------------------|-----------|---------------|----------------|
| Daily (7 days) | 100 GB | 80% | ~140 GB |
| Weekly (4 weeks) | 100 GB | 70% | ~120 GB |
| Monthly (6 months) | 100 GB | 60% | ~240 GB |

**Total for 6-month retention**: ~500 GB

### Performance Impact

- CPU: 5-15% during backup
- Memory: 100-500 MB
- Network: Minimal (local backups)
- Disk I/O: Moderate

---

## Next Steps

1. **Integrate Endpoints**: Copy Borg endpoints to main API file
2. **Test All Operations**: Run through testing checklist
3. **Configure Production**: Set up encryption keys, repositories
4. **Schedule Backups**: Configure automated backups
5. **Set Up Monitoring**: Implement alerts and dashboards
6. **Document Procedures**: Create runbooks for common operations
7. **Train Team**: Ensure team knows recovery procedures

---

**Support**: For questions, refer to:
- BorgBackup docs: https://borgbackup.readthedocs.io/
- Implementation doc: `BORGBACKUP_IMPLEMENTATION.md`
- Ops-Center docs: `/services/ops-center/CLAUDE.md`
