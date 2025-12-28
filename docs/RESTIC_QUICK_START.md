# Restic Backup Quick Start Guide

**For Ops-Center Administrators**

---

## Prerequisites

1. **Install Restic Binary** in ops-center container:
   ```bash
   docker exec ops-center-direct bash -c "
     cd /tmp && \
     wget https://github.com/restic/restic/releases/download/v0.16.0/restic_0.16.0_linux_amd64.bz2 && \
     bunzip2 restic_0.16.0_linux_amd64.bz2 && \
     chmod +x restic_0.16.0_linux_amd64 && \
     mv restic_0.16.0_linux_amd64 /usr/local/bin/restic && \
     restic version
   "
   ```

2. **Set Encryption Key** in `.env.auth`:
   ```bash
   # Generate key
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

   # Add to .env.auth
   RESTIC_ENCRYPTION_KEY=<generated-key>
   RESTIC_BINARY=/usr/local/bin/restic
   RESTIC_CACHE_DIR=/tmp/restic-cache
   ```

3. **Restart ops-center**:
   ```bash
   docker restart ops-center-direct
   ```

---

## Basic Workflow

### Step 1: Initialize Repository

```bash
curl -X POST "http://localhost:8084/api/v1/backups/restic/init" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "repository_path": "/backups/restic-repo",
    "password": "MySecurePassword123!"
  }'
```

**Save the encrypted_password returned** - you'll need it for all operations!

### Step 2: Create Your First Backup

```bash
curl -X POST "http://localhost:8084/api/v1/backups/restic/backup" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "source_paths": ["/var/lib/docker/volumes"],
    "repository_path": "/backups/restic-repo",
    "password": "MySecurePassword123!",
    "tags": ["docker", "production", "daily"],
    "exclude_patterns": ["*.log", "*.tmp", "cache/*"]
  }'
```

**Note the snapshot_id returned** - you'll need it to restore!

### Step 3: List Snapshots

```bash
curl "http://localhost:8084/api/v1/backups/restic/snapshots?repository_path=/backups/restic-repo&password=MySecurePassword123!" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 4: Restore a Snapshot

```bash
curl -X POST "http://localhost:8084/api/v1/backups/restic/restore/SNAPSHOT_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "snapshot_id": "SNAPSHOT_ID",
    "target_path": "/restore/temp",
    "repository_path": "/backups/restic-repo",
    "password": "MySecurePassword123!"
  }'
```

---

## Common Use Cases

### Daily Docker Volume Backups

```bash
# Create backup with daily tag
curl -X POST "http://localhost:8084/api/v1/backups/restic/backup" \
  -H "Content-Type: application/json" \
  -d '{
    "source_paths": [
      "/var/lib/docker/volumes/unicorn-postgresql",
      "/var/lib/docker/volumes/unicorn-redis"
    ],
    "repository_path": "/backups/restic-repo",
    "password": "MySecurePassword123!",
    "tags": ["docker", "database", "daily"],
    "exclude_patterns": ["*.log"]
  }'
```

### Backup to S3-Compatible Storage

```bash
# Initialize S3 repository
curl -X POST "http://localhost:8084/api/v1/backups/restic/init" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_path": "s3:https://s3.wasabisys.com/my-bucket/restic-repo",
    "password": "MySecurePassword123!"
  }'

# Environment variables needed for S3:
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key
```

### Backup to SFTP Server

```bash
# Initialize SFTP repository
curl -X POST "http://localhost:8084/api/v1/backups/restic/init" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_path": "sftp:user@backup-server:/backups/restic-repo",
    "password": "MySecurePassword123!"
  }'
```

### Weekly Cleanup (Prune Old Backups)

```bash
curl -X POST "http://localhost:8084/api/v1/backups/restic/prune" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_path": "/backups/restic-repo",
    "password": "MySecurePassword123!",
    "keep_policy": {
      "daily": 7,
      "weekly": 4,
      "monthly": 6,
      "yearly": 2
    }
  }'
```

### Monthly Integrity Check

```bash
curl -X POST "http://localhost:8084/api/v1/backups/restic/check?repository_path=/backups/restic-repo&password=MySecurePassword123!&read_data=false"
```

---

## Repository Types

### Local Repository
```json
{
  "repository_path": "/backups/restic-repo"
}
```

### S3 (AWS, Wasabi, MinIO)
```json
{
  "repository_path": "s3:https://s3.amazonaws.com/bucket/repo"
}
```

**Environment variables needed**:
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-west-2
```

### Backblaze B2
```json
{
  "repository_path": "b2:bucket-name:repo-path"
}
```

**Environment variables needed**:
```bash
B2_ACCOUNT_ID=your_account_id
B2_ACCOUNT_KEY=your_account_key
```

### SFTP
```json
{
  "repository_path": "sftp:user@host:/path/to/repo"
}
```

**SSH key setup**:
```bash
# Add SSH key to ~/.ssh/id_rsa
# Or use password via environment:
RESTIC_SFTP_PASSWORD=your_ssh_password
```

### Azure Blob Storage
```json
{
  "repository_path": "azure:container:/repo-path"
}
```

**Environment variables needed**:
```bash
AZURE_ACCOUNT_NAME=your_account
AZURE_ACCOUNT_KEY=your_key
```

---

## Retention Policies

### Conservative (Keep More)
```json
{
  "keep_policy": {
    "daily": 14,
    "weekly": 8,
    "monthly": 12,
    "yearly": 5
  }
}
```

### Balanced (Default)
```json
{
  "keep_policy": {
    "daily": 7,
    "weekly": 4,
    "monthly": 6,
    "yearly": 2
  }
}
```

### Aggressive (Save Space)
```json
{
  "keep_policy": {
    "daily": 3,
    "weekly": 2,
    "monthly": 3,
    "yearly": 1
  }
}
```

---

## Exclude Patterns

### Common Patterns
```json
{
  "exclude_patterns": [
    "*.log",
    "*.tmp",
    "*.cache",
    "node_modules/*",
    "__pycache__/*",
    ".git/*",
    "*.pyc",
    "*.swp",
    ".DS_Store"
  ]
}
```

### Size-Based Exclusions
```json
{
  "exclude_patterns": [
    "**/*.iso",
    "**/*.dmg",
    "**/*.vdi",
    "*.backup"
  ]
}
```

---

## Monitoring & Maintenance

### Check Repository Statistics
```bash
curl "http://localhost:8084/api/v1/backups/restic/stats?repository_path=/backups/restic-repo&password=MySecurePassword123!"
```

**Response**:
```json
{
  "total_size": 2147483648,
  "total_file_count": 1175,
  "snapshots_count": 5,
  "deduplication_ratio": 2.5,
  "message": "Repository contains 5 snapshot(s)"
}
```

### List Snapshots with Tags
```bash
curl "http://localhost:8084/api/v1/backups/restic/snapshots?repository_path=/backups/restic-repo&password=MySecurePassword123!&tags=docker&tags=production"
```

### Verify Repository Integrity
```bash
# Quick check (metadata only)
curl -X POST "http://localhost:8084/api/v1/backups/restic/check?repository_path=/backups/restic-repo&password=MySecurePassword123!&read_data=false"

# Thorough check (reads all data)
curl -X POST "http://localhost:8084/api/v1/backups/restic/check?repository_path=/backups/restic-repo&password=MySecurePassword123!&read_data=true"
```

---

## Automation Scripts

### Cron Job for Daily Backups

```bash
#!/bin/bash
# /scripts/daily-restic-backup.sh

API_URL="http://localhost:8084/api/v1/backups/restic"
REPO_PATH="/backups/restic-repo"
PASSWORD="MySecurePassword123!"

# Create backup
curl -X POST "$API_URL/backup" \
  -H "Content-Type: application/json" \
  -d "{
    \"source_paths\": [\"/var/lib/docker/volumes\"],
    \"repository_path\": \"$REPO_PATH\",
    \"password\": \"$PASSWORD\",
    \"tags\": [\"docker\", \"daily\", \"$(date +%Y-%m-%d)\"]
  }"

# Prune weekly (only on Sundays)
if [ $(date +%u) -eq 7 ]; then
  curl -X POST "$API_URL/prune" \
    -H "Content-Type: application/json" \
    -d "{
      \"repository_path\": \"$REPO_PATH\",
      \"password\": \"$PASSWORD\"
    }"
fi
```

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /scripts/daily-restic-backup.sh >> /var/log/restic-backup.log 2>&1
```

---

## Troubleshooting

### Error: "restic: command not found"
**Solution**: Install Restic binary (see Prerequisites)

### Error: "repository does not exist"
**Solution**: Initialize repository first with `/init` endpoint

### Error: "wrong password"
**Solution**: Check password matches what was used during initialization

### Error: "failed to create lock"
**Solution**: Another backup operation may be running, or stale lock exists:
```bash
# Check for stale locks
restic -r /backups/restic-repo unlock
```

### Error: "permission denied"
**Solution**: Check directory permissions:
```bash
chmod 755 /backups/restic-repo
```

---

## Best Practices

### Security
1. ✅ Use strong passwords (16+ characters)
2. ✅ Store encrypted passwords in database
3. ✅ Rotate encryption keys periodically
4. ✅ Use separate passwords for different repositories
5. ✅ Restrict API access to admin users only

### Performance
1. ✅ Exclude large temporary files
2. ✅ Run backups during low-traffic hours
3. ✅ Use local cache directory for better performance
4. ✅ Limit bandwidth for remote backups
5. ✅ Prune regularly to free space

### Reliability
1. ✅ Test restore procedures monthly
2. ✅ Monitor backup completion
3. ✅ Verify repository integrity weekly
4. ✅ Keep multiple backup copies
5. ✅ Document recovery procedures

---

## Next Steps

1. **Install Restic** in ops-center container
2. **Set encryption key** in environment
3. **Initialize repository** (local or remote)
4. **Create test backup** to verify setup
5. **Test restore** to ensure data recovery works
6. **Set up automation** for daily backups
7. **Monitor** backup status regularly

---

## Support

**Documentation**: `/services/ops-center/docs/RESTIC_BACKUP_INTEGRATION.md`
**API Reference**: http://localhost:8084/docs#/Restic%20Backup
**Restic Docs**: https://restic.readthedocs.io/

**For Issues**: Check audit logs in Ops-Center dashboard
