# Rclone Installation Guide

## Quick Start

The rclone integration requires the `rclone` binary to be installed in the ops-center container.

---

## Option 1: Install in Docker Container (Recommended)

### Step 1: Add to Dockerfile

Edit `/home/muut/Production/UC-Cloud/services/ops-center/Dockerfile`:

```dockerfile
# Add after other system packages
RUN curl https://rclone.org/install.sh | bash

# Verify installation
RUN rclone version
```

### Step 2: Rebuild Container

```bash
cd /home/muut/Production/UC-Cloud

# Rebuild ops-center
docker compose -f services/ops-center/docker-compose.direct.yml build

# Restart with new image
docker compose -f services/ops-center/docker-compose.direct.yml up -d

# Verify rclone is installed
docker exec ops-center-direct rclone version
```

---

## Option 2: Install in Running Container

If you need to install rclone without rebuilding:

```bash
# Access container
docker exec -it ops-center-direct /bin/bash

# Install rclone
curl https://rclone.org/install.sh | bash

# Verify
rclone version

# Exit container
exit

# Restart FastAPI to load module
docker restart ops-center-direct
```

**Note**: This method doesn't persist across container recreations. Use Option 1 for production.

---

## Option 3: Volume Mount rclone Binary

If rclone is installed on the host:

```bash
# Check host installation
which rclone
# Output: /usr/bin/rclone

# Add to docker-compose
docker-compose.yml:
  volumes:
    - /usr/bin/rclone:/usr/bin/rclone:ro
    - ~/.config/rclone:/root/.config/rclone:rw
```

---

## Verification

### 1. Check rclone Installation

```bash
# In container
docker exec ops-center-direct rclone version

# Expected output:
# rclone v1.64.0
# - os/version: alpine 3.18.4 (64 bit)
# - os/kernel: 6.8.0-86-generic (x86_64)
# - os/type: linux
# - os/arch: amd64
# - go/version: go1.21.3
# ...
```

### 2. Test API Endpoint

```bash
# List providers (no rclone needed)
curl http://localhost:8084/api/v1/backups/rclone/providers | jq '.[0:3]'

# Expected:
# [
#   {
#     "name": "Amazon S3",
#     "prefix": "s3",
#     "description": "Amazon S3 and S3-compatible storage"
#   },
#   {
#     "name": "Google Drive",
#     "prefix": "drive",
#     "description": "Google Drive"
#   },
#   ...
# ]
```

### 3. Check Module Import

```bash
# In container
docker exec ops-center-direct python3 -c "from backup_rclone import rclone_manager; print('✓ Module loaded successfully')"

# Expected:
# ✓ Module loaded successfully
```

---

## Configuration

### Config Directory

Rclone stores configuration in `~/.config/rclone/rclone.conf`

**In container**: `/root/.config/rclone/rclone.conf`

### Volume Mount for Persistence

To persist rclone configuration across container recreations:

```yaml
# docker-compose.yml
volumes:
  - rclone-config:/root/.config/rclone

volumes:
  rclone-config:
    driver: local
```

Or bind mount:

```yaml
volumes:
  - ./volumes/rclone-config:/root/.config/rclone
```

---

## Common Issues

### Issue 1: "rclone not installed"

**Error**:
```
RuntimeError: rclone is not installed. Install with: curl https://rclone.org/install.sh | sudo bash
```

**Solution**: Follow Option 1 or Option 2 above.

### Issue 2: Permission Denied

**Error**:
```
PermissionError: [Errno 13] Permission denied: '/root/.config/rclone/rclone.conf'
```

**Solution**:
```bash
# Fix permissions
docker exec ops-center-direct chmod 600 /root/.config/rclone/rclone.conf
docker exec ops-center-direct chown root:root /root/.config/rclone/rclone.conf
```

### Issue 3: Config Lost After Restart

**Problem**: Remote configuration disappears after container restart.

**Solution**: Use volume mount (see Configuration section above).

---

## Testing Installation

### 1. Configure Test Remote (Local)

```bash
curl -X POST http://localhost:8084/api/v1/backups/rclone/configure \
  -H "Content-Type: application/json" \
  -d '{
    "remote_name": "test-local",
    "provider": "local",
    "config": {},
    "encrypt": false
  }'
```

### 2. List Remotes

```bash
curl http://localhost:8084/api/v1/backups/rclone/remotes | jq
```

**Expected**:
```json
[
  {
    "name": "test-local",
    "type": "local",
    "configured": true,
    "encrypted": false
  }
]
```

### 3. Test Sync (Dry-Run)

```bash
# Create test directory
docker exec ops-center-direct mkdir -p /tmp/test-source /tmp/test-dest
docker exec ops-center-direct touch /tmp/test-source/file1.txt

# Sync with dry-run
curl -X POST http://localhost:8084/api/v1/backups/rclone/sync \
  -H "Content-Type: application/json" \
  -d '{
    "source": "/tmp/test-source",
    "destination": "/tmp/test-dest",
    "dry_run": true,
    "checksum": false
  }'
```

---

## Production Deployment

### Recommended Dockerfile Changes

```dockerfile
FROM python:3.11-alpine

# Install system dependencies
RUN apk add --no-cache \
    curl \
    fuse \
    ca-certificates

# Install rclone
RUN curl https://rclone.org/install.sh | bash

# Verify installation
RUN rclone version

# Create config directory
RUN mkdir -p /root/.config/rclone
RUN chmod 700 /root/.config/rclone

# ... rest of Dockerfile
```

### Docker Compose Volume Configuration

```yaml
services:
  ops-center-direct:
    image: ops-center:latest
    volumes:
      # Persist rclone config
      - rclone-config:/root/.config/rclone

      # Optional: Mount FUSE for remote mounting
      - /dev/fuse:/dev/fuse

    # Required for FUSE mounting
    cap_add:
      - SYS_ADMIN
    devices:
      - /dev/fuse

    # Enable privileged mode if needed for FUSE
    # privileged: true

volumes:
  rclone-config:
    driver: local
```

---

## Security Considerations

### 1. Config File Protection

```bash
# Inside container
chmod 600 /root/.config/rclone/rclone.conf
chown root:root /root/.config/rclone/rclone.conf
```

### 2. Secrets Management

For production, use environment variables or secrets:

```yaml
# docker-compose.yml
environment:
  RCLONE_CONFIG_S3_TYPE: s3
  RCLONE_CONFIG_S3_ACCESS_KEY_ID: ${S3_ACCESS_KEY}
  RCLONE_CONFIG_S3_SECRET_ACCESS_KEY: ${S3_SECRET_KEY}
```

### 3. Encrypted Remotes

Always use `encrypt: true` for sensitive data:

```bash
curl -X POST http://localhost:8084/api/v1/backups/rclone/configure \
  -d '{
    "remote_name": "my-s3",
    "provider": "s3",
    "config": {...},
    "encrypt": true  # Creates my-s3_encrypted
  }'
```

---

## Advanced Configuration

### FUSE Mounting

To enable remote mounting as local filesystem:

1. Install FUSE in container
2. Add device and capability to docker-compose
3. Use mount endpoint

```bash
curl -X POST http://localhost:8084/api/v1/backups/rclone/mount \
  -d '{
    "remote_path": "my-s3:backups",
    "mount_point": "/mnt/s3-backups",
    "read_only": true
  }'
```

### OAuth Providers

For Google Drive, Dropbox, OneDrive:

1. Configure via rclone CLI (interactive)
2. Copy config to container
3. Use in API

```bash
# On host with browser
rclone config

# Copy config to container
docker cp ~/.config/rclone/rclone.conf ops-center-direct:/root/.config/rclone/
```

---

## Support

For rclone-specific issues, see:
- **Documentation**: https://rclone.org/docs/
- **Forum**: https://forum.rclone.org/
- **GitHub**: https://github.com/rclone/rclone

For ops-center integration issues, check:
- Container logs: `docker logs ops-center-direct`
- API docs: http://localhost:8084/docs
- Module: `/app/backend/backup_rclone.py`
