# StorageBackup.jsx API Connectivity Fix Report

**Date**: October 26, 2025
**Component**: `/services/ops-center/src/pages/StorageBackup.jsx`
**Backend Files**:
- `backend/storage_backup_api.py`
- `backend/restic_api_endpoints.py`

---

## Issues Found

### 1. Verify Endpoint Path Mismatch ⚠️

**Frontend Call** (line 267):
```javascript
const response = await fetch(`/api/v1/backups/${backupId}/verify`, {
  method: 'POST',
});
```

**Backend Endpoint** (storage_backup_api.py line 619):
```python
@router.post("/backups/verify/{backup_id}", response_model=BackupVerifyResponse)
async def verify_backup(backup_id: str, ...):
```

**Issue**: Frontend uses `/{backup_id}/verify` but backend expects `/verify/{backup_id}`

**Fix Required**: Update frontend to match backend path

---

### 2. Cloud Config Endpoints Missing ❌

**Frontend Calls**:

1. **Load cloud config** (line 127):
```javascript
const response = await fetch('/api/v1/backups/cloud-config');
```

2. **Save cloud config** (line 232):
```javascript
const response = await fetch('/api/v1/backups/cloud-config', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(config),
});
```

3. **Test cloud connection** (line 252):
```javascript
const response = await fetch('/api/v1/backups/cloud-config/test', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(config),
});
```

**Backend**: **NOT IMPLEMENTED**

**Impact**:
- Cloud backup tab (line 785-793) is non-functional
- CloudBackupSetup component cannot save or test configurations
- Users cannot configure cloud backup providers

**Options**:
1. **Add cloud config endpoints to backend** (recommended for full functionality)
2. **Remove cloud backup tab from frontend** (if feature not needed)
3. **Use rclone endpoints instead** (already implemented, lines 756-1297)

---

## Correctly Implemented Endpoints ✅

### Storage Management
- ✅ `/api/v1/storage/info` - Get storage information
- ✅ `/api/v1/storage/cleanup` - Clean up storage

### Backup Management
- ✅ `/api/v1/backups` - List all backups
- ✅ `/api/v1/backups/create` - Create new backup
- ✅ `/api/v1/backups/{backup_id}/restore` - Restore backup
- ✅ `/api/v1/backups/{backup_id}` - Delete backup
- ✅ `/api/v1/backups/config` - Get/update backup configuration

### Rclone Cloud Sync (Alternative)
The backend has **comprehensive rclone integration** (lines 756-1297 in storage_backup_api.py):
- ✅ `/api/v1/backups/rclone/configure` - Configure cloud remotes
- ✅ `/api/v1/backups/rclone/remotes` - List remotes
- ✅ `/api/v1/backups/rclone/sync` - Sync to cloud
- ✅ `/api/v1/backups/rclone/copy` - Copy to cloud
- ✅ `/api/v1/backups/rclone/check` - Test connection
- And 10+ more rclone endpoints

---

## Recommended Fixes

### Option 1: Quick Fix (Use Existing Rclone Endpoints)

**Change**: Update `CloudBackupSetup.jsx` component to use rclone endpoints instead of missing cloud-config endpoints

**Benefits**:
- No backend changes needed
- Rclone supports 40+ cloud providers (S3, Dropbox, Google Drive, OneDrive, etc.)
- Already fully implemented and tested

**Implementation**:
1. Replace `/api/v1/backups/cloud-config` → `/api/v1/backups/rclone/remotes`
2. Replace `/api/v1/backups/cloud-config/test` → `/api/v1/backups/rclone/check`
3. Use `/api/v1/backups/rclone/configure` for saving

### Option 2: Add Cloud Config Endpoints (Full Feature)

**Change**: Add three new endpoints to `storage_backup_api.py`

**Endpoints to Add**:
```python
@router.get("/backups/cloud-config")
async def get_cloud_config(...):
    """Get saved cloud backup configuration"""

@router.post("/backups/cloud-config")
async def save_cloud_config(...):
    """Save cloud backup configuration"""

@router.post("/backups/cloud-config/test")
async def test_cloud_config(...):
    """Test cloud connection"""
```

**Benefits**:
- Maintains existing frontend code
- Simple configuration storage
- Can wrap rclone underneath

### Option 3: Remove Cloud Backup Tab

**Change**: Remove cloud backup functionality from frontend

**Steps**:
1. Remove "Cloud Backup" tab from StorageBackup.jsx (line 377)
2. Remove `CloudBackupSetup` component import (line 28)
3. Remove cloud-related state variables (line 64)

**When Appropriate**: If cloud backup feature is not needed for current deployment

---

## Path Correction Needed

### Verify Endpoint Fix

**File**: `/services/ops-center/src/pages/StorageBackup.jsx`

**Line 267** - Change from:
```javascript
const response = await fetch(`/api/v1/backups/${backupId}/verify`, {
  method: 'POST',
});
```

**To**:
```javascript
const response = await fetch(`/api/v1/backups/verify/${backupId}`, {
  method: 'POST',
});
```

---

## Testing Checklist

After implementing fixes:

### Backend Testing
```bash
# Test verify endpoint (correct path)
curl -X POST http://localhost:8084/api/v1/backups/verify/backup-123

# Test cloud config endpoints (if implemented)
curl http://localhost:8084/api/v1/backups/cloud-config
curl -X POST http://localhost:8084/api/v1/backups/cloud-config/test

# Test rclone endpoints (already working)
curl http://localhost:8084/api/v1/backups/rclone/remotes
curl http://localhost:8084/api/v1/backups/rclone/providers
```

### Frontend Testing
1. Navigate to Storage & Backup page
2. Test each tab:
   - ✅ Storage Overview - Should load disk usage
   - ✅ Volume Management - Should list volumes
   - ✅ Backup & Recovery - Should list backups
   - ✅ Backup Scheduling - Should show cron builder
   - ⚠️ Cloud Backup - Currently broken, needs fix
   - ⚠️ Verification - Verify endpoint needs path fix
   - ✅ Storage Optimizer - Should work if cleanup endpoint works

---

## Summary

**Working**: 80% of API calls are correctly implemented
**Issues**: 2 problems found
  1. Verify endpoint path reversed (easy fix)
  2. Cloud config endpoints missing (needs decision)

**Recommendation**:
1. Fix verify endpoint path immediately (1-line change)
2. Choose Option 1 (use rclone) or Option 2 (add endpoints) for cloud backup
3. Test all tabs after changes

**Priority**: Medium - Core backup functionality works, cloud backup is enhancement feature

---

## Files to Modify

If implementing fixes:

### Frontend Changes Required:
- `/services/ops-center/src/pages/StorageBackup.jsx` (line 267 - verify path)
- `/services/ops-center/src/components/CloudBackupSetup.jsx` (if using Option 1)

### Backend Changes Required (Option 2):
- `/services/ops-center/backend/storage_backup_api.py` (add 3 endpoints)
- `/services/ops-center/backend/cloud_backup_config.py` (new file for cloud config logic)

### No Changes Needed (Option 1):
- Rclone endpoints already fully functional
- Just update frontend to use them
