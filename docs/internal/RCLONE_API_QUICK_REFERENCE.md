# Rclone API Quick Reference

## Base URL

```
http://localhost:8084/api/v1/backups/rclone
```

**Authentication**: All endpoints require admin authentication.

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/configure` | Configure new remote |
| GET | `/remotes` | List configured remotes |
| POST | `/sync` | Sync directories |
| POST | `/copy` | Copy files |
| POST | `/move` | Move files |
| POST | `/delete` | Delete files |
| GET | `/list` | List remote files |
| GET | `/size` | Get remote size |
| GET | `/providers` | List all providers |
| POST | `/mount` | Mount remote filesystem |
| POST | `/check` | Test connection |

---

## 1. Configure Remote

### POST `/configure`

**Request**:
```json
{
  "remote_name": "my-s3",
  "provider": "s3",
  "config": {
    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "region": "us-east-1",
    "endpoint": "s3.amazonaws.com"
  },
  "encrypt": false
}
```

**Response**:
```json
{
  "success": true,
  "remote_name": "my-s3",
  "provider": "s3",
  "encrypted": false,
  "message": "Remote 'my-s3' configured successfully"
}
```

### Provider-Specific Configs

#### Google Drive
```json
{
  "remote_name": "my-drive",
  "provider": "drive",
  "config": {
    "client_id": "...",
    "client_secret": "...",
    "token": "{...}"
  }
}
```

#### Dropbox
```json
{
  "remote_name": "my-dropbox",
  "provider": "dropbox",
  "config": {
    "token": "..."
  }
}
```

#### OneDrive
```json
{
  "remote_name": "my-onedrive",
  "provider": "onedrive",
  "config": {
    "token": "{...}",
    "drive_id": "...",
    "drive_type": "personal"
  }
}
```

#### Backblaze B2
```json
{
  "remote_name": "my-b2",
  "provider": "b2",
  "config": {
    "account": "...",
    "key": "...",
    "bucket": "my-bucket"
  }
}
```

#### SFTP
```json
{
  "remote_name": "my-sftp",
  "provider": "sftp",
  "config": {
    "host": "example.com",
    "user": "username",
    "pass": "password",
    "port": "22"
  }
}
```

---

## 2. List Remotes

### GET `/remotes`

**Response**:
```json
[
  {
    "name": "my-s3",
    "type": "s3",
    "configured": true,
    "encrypted": false
  },
  {
    "name": "my-drive",
    "type": "drive",
    "configured": true,
    "encrypted": false
  }
]
```

---

## 3. Sync Directories

### POST `/sync`

Makes destination identical to source (deletes extra files).

**Request**:
```json
{
  "source": "/data/backups",
  "destination": "my-s3:backups",
  "dry_run": false,
  "checksum": true,
  "bwlimit": "10M",
  "exclude": ["*.tmp", "*.log"],
  "delete_excluded": false
}
```

**Response**:
```json
{
  "bytes_transferred": 1048576000,
  "files_transferred": 42,
  "files_checked": 100,
  "files_deleted": 5,
  "errors": 0,
  "elapsed_time": 120.5,
  "transfer_rate_mbps": 8.3
}
```

### Sync Scenarios

#### Local to Cloud
```json
{
  "source": "/data/backups",
  "destination": "my-s3:backups"
}
```

#### Cloud to Local
```json
{
  "source": "my-s3:backups",
  "destination": "/data/restore"
}
```

#### Cloud to Cloud
```json
{
  "source": "my-s3:data",
  "destination": "my-drive:data"
}
```

#### Dry-Run (Preview)
```json
{
  "source": "/data/backups",
  "destination": "my-s3:backups",
  "dry_run": true
}
```

---

## 4. Copy Files

### POST `/copy`

Copy files without deleting from destination.

**Request**:
```json
{
  "source": "/data/backups",
  "destination": "my-s3:backups",
  "dry_run": false,
  "checksum": false,
  "bwlimit": null,
  "exclude": []
}
```

**Response**: Same as sync

**Use Cases**:
- Incremental backups
- Multi-cloud replication
- Archive creation

---

## 5. Move Files

### POST `/move`

Move files (deletes from source after copy).

**Request**:
```json
{
  "source": "/data/temp",
  "destination": "my-s3:archive",
  "dry_run": false,
  "delete_empty_src_dirs": true
}
```

**Response**: Same as sync

⚠️ **Warning**: Source files will be deleted!

---

## 6. Delete Files

### POST `/delete`

Permanently delete files at remote path.

**Request**:
```json
{
  "remote_path": "my-s3:old-backups",
  "dry_run": true
}
```

**Response**:
```json
{
  "success": true,
  "remote_path": "my-s3:old-backups",
  "deleted_count": 15,
  "message": "Deleted 15 files"
}
```

⚠️ **Warning**: Permanent deletion! Always use `dry_run: true` first.

---

## 7. List Files

### GET `/list?remote_path=my-s3:backups&recursive=true`

**Query Parameters**:
- `remote_path` (required): Path to list
- `recursive` (optional): List subdirectories (default: true)
- `max_depth` (optional): Maximum depth (default: unlimited)

**Response**:
```json
[
  {
    "path": "backups/backup-2025-10-23.tar.gz",
    "name": "backup-2025-10-23.tar.gz",
    "size": 1048576000,
    "mime_type": "application/gzip",
    "mod_time": "2025-10-23T20:00:00Z",
    "is_dir": false
  },
  {
    "path": "backups/logs",
    "name": "logs",
    "size": 0,
    "mime_type": "inode/directory",
    "mod_time": "2025-10-23T19:00:00Z",
    "is_dir": true
  }
]
```

---

## 8. Get Size

### GET `/size?remote_path=my-s3:backups`

**Response**:
```json
{
  "remote_path": "my-s3:backups",
  "size_bytes": 10737418240,
  "size_mb": 10240.0,
  "size_gb": 10.0
}
```

---

## 9. List Providers

### GET `/providers`

**Response** (40+ providers):
```json
[
  {
    "name": "Amazon S3",
    "prefix": "s3",
    "description": "Amazon S3 and S3-compatible storage"
  },
  {
    "name": "Google Drive",
    "prefix": "drive",
    "description": "Google Drive"
  },
  {
    "name": "Dropbox",
    "prefix": "dropbox",
    "description": "Dropbox"
  },
  ...
]
```

---

## 10. Mount Remote

### POST `/mount`

Mount remote as local filesystem (requires FUSE).

**Request**:
```json
{
  "remote_path": "my-s3:backups",
  "mount_point": "/mnt/s3-backups",
  "read_only": true,
  "allow_other": false
}
```

**Response**:
```json
{
  "success": true,
  "remote_path": "my-s3:backups",
  "mount_point": "/mnt/s3-backups",
  "message": "Mounted my-s3:backups to /mnt/s3-backups"
}
```

---

## 11. Check Connection

### POST `/check?remote_name=my-s3`

**Response (Success)**:
```json
{
  "connected": true,
  "message": "Connection successful",
  "remote": "my-s3"
}
```

**Response (Failure)**:
```json
{
  "connected": false,
  "message": "Connection failed: connection timeout",
  "remote": "my-s3"
}
```

---

## Common Options

### Bandwidth Limiting

```json
{
  "bwlimit": "10M"   // 10 MB/s
  "bwlimit": "1M"    // 1 MB/s
  "bwlimit": "512k"  // 512 KB/s
  "bwlimit": "8:10M" // 8am-10am: unlimited, otherwise 10 MB/s
}
```

### Exclude Patterns

```json
{
  "exclude": [
    "*.tmp",           // Temporary files
    "*.log",           // Log files
    ".git/**",         // Git directory
    "node_modules/**", // Node modules
    "**/.DS_Store"     // macOS files
  ]
}
```

### Checksum Verification

```json
{
  "checksum": true  // Use MD5/SHA1 checksums instead of mod-time
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error: invalid provider"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Admin access required"
}
```

### 404 Not Found
```json
{
  "detail": "Remote not found: my-s3"
}
```

### 500 Server Error
```json
{
  "detail": "Sync failed: connection timeout"
}
```

---

## cURL Examples

### Configure S3 Remote
```bash
curl -X POST http://localhost:8084/api/v1/backups/rclone/configure \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "remote_name": "my-s3",
    "provider": "s3",
    "config": {
      "access_key_id": "...",
      "secret_access_key": "...",
      "region": "us-east-1"
    }
  }'
```

### Sync to Cloud
```bash
curl -X POST http://localhost:8084/api/v1/backups/rclone/sync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "source": "/data/backups",
    "destination": "my-s3:backups",
    "checksum": true,
    "bwlimit": "10M"
  }'
```

### List Files
```bash
curl "http://localhost:8084/api/v1/backups/rclone/list?remote_path=my-s3:backups&recursive=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Check Connection
```bash
curl -X POST "http://localhost:8084/api/v1/backups/rclone/check?remote_name=my-s3" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Python Examples

### Using requests

```python
import requests

API_URL = "http://localhost:8084/api/v1/backups/rclone"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Configure remote
response = requests.post(
    f"{API_URL}/configure",
    headers=headers,
    json={
        "remote_name": "my-s3",
        "provider": "s3",
        "config": {
            "access_key_id": "...",
            "secret_access_key": "...",
            "region": "us-east-1"
        }
    }
)
print(response.json())

# Sync files
response = requests.post(
    f"{API_URL}/sync",
    headers=headers,
    json={
        "source": "/data/backups",
        "destination": "my-s3:backups",
        "checksum": True,
        "bwlimit": "10M"
    }
)
stats = response.json()
print(f"Transferred: {stats['files_transferred']} files, {stats['bytes_transferred']} bytes")
```

---

## Best Practices

### 1. Always Test with Dry-Run First
```json
{
  "dry_run": true  // Preview changes
}
```

### 2. Use Checksum for Critical Data
```json
{
  "checksum": true  // Verify integrity
}
```

### 3. Limit Bandwidth for Large Transfers
```json
{
  "bwlimit": "10M"  // Don't saturate network
}
```

### 4. Exclude Unnecessary Files
```json
{
  "exclude": ["*.tmp", "*.log", ".git/**"]
}
```

### 5. Use Encryption for Sensitive Data
```json
{
  "encrypt": true  // Creates encrypted remote wrapper
}
```

### 6. Test Connection Before Large Transfers
```bash
# Check first
POST /check?remote_name=my-s3

# Then sync
POST /sync
```

### 7. Monitor Transfer Statistics
```json
{
  "bytes_transferred": 1048576000,  // Monitor progress
  "transfer_rate_mbps": 8.3,        // Check speed
  "errors": 0                        // Check for failures
}
```

---

## Automation Examples

### Scheduled Backup to Cloud

```bash
#!/bin/bash
# backup-to-cloud.sh

# Create local backup
curl -X POST http://localhost:8084/api/v1/backups/create \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"backup_type": "scheduled"}'

# Wait for backup to complete
sleep 300

# Sync to cloud
curl -X POST http://localhost:8084/api/v1/backups/rclone/sync \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "source": "/backups",
    "destination": "my-s3:backups",
    "checksum": true
  }'
```

### Multi-Cloud Replication

```bash
# Replicate to multiple clouds
for remote in my-s3 my-b2 my-drive; do
  curl -X POST http://localhost:8084/api/v1/backups/rclone/sync \
    -H "Authorization: Bearer $TOKEN" \
    -d "{
      \"source\": \"/data/backups\",
      \"destination\": \"${remote}:backups\"
    }"
done
```

---

## Troubleshooting

### Connection Failures
```bash
# Test connection first
curl -X POST "http://localhost:8084/api/v1/backups/rclone/check?remote_name=my-s3"
```

### Large File Transfers Timeout
```json
{
  "bwlimit": "50M"  // Increase transfer speed
}
```

### Checksum Mismatches
```json
{
  "checksum": true,  // Force checksum verification
  "dry_run": true    // Preview issues first
}
```

---

## API Documentation

Full interactive API docs available at:
- **Swagger UI**: http://localhost:8084/docs
- **ReDoc**: http://localhost:8084/redoc
- **OpenAPI JSON**: http://localhost:8084/openapi.json
