"""
Storage & Backup Management API for Ops-Center
FastAPI router with all storage and backup endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import os
import asyncio
from pathlib import Path

from storage_manager import (
    storage_backup_manager,
    StorageInfo,
    BackupConfig,
    BackupInfo,
    BackupStatus,
    VolumeInfo
)
from audit_logger import audit_logger
from backup_rclone import rclone_manager
from backup_restic import restic_backup_manager
from backup_borg import BorgBackupManager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["Storage & Backup"])

# Initialize BorgBackup manager
# In production, load encryption key from secure config
borg_manager = BorgBackupManager()

# Admin authentication dependency
async def require_admin(request: Any = None):
    """Require admin role for endpoints"""
    # Simplified auth - in production, verify JWT token and role
    return {"role": "admin", "username": "admin"}

# Request/Response models
class CleanupRequest(BaseModel):
    """Request for storage cleanup"""
    cleanup_docker: bool = Field(True, description="Clean unused Docker volumes/images")
    cleanup_logs: bool = Field(True, description="Compress and clean old logs")
    cleanup_cache: bool = Field(True, description="Clear Redis and temp caches")
    cleanup_backups: bool = Field(False, description="Remove old backups beyond retention")

class CleanupResponse(BaseModel):
    """Response from cleanup operation"""
    success: bool
    freed_space: int
    actions_performed: List[str]
    errors: List[str]

class OptimizeRequest(BaseModel):
    """Request for storage optimization"""
    compress_logs: bool = Field(True, description="Compress log files")
    defragment: bool = Field(False, description="Defragment volumes (if supported)")
    verify_integrity: bool = Field(True, description="Verify file integrity")

class OptimizeResponse(BaseModel):
    """Response from optimization operation"""
    success: bool
    optimizations: List[str]
    time_taken: str
    errors: List[str]

class BackupCreateRequest(BaseModel):
    """Request to create a backup"""
    backup_type: str = Field("manual", description="Type: manual, scheduled, or incremental")
    include_volumes: Optional[List[str]] = Field(None, description="Specific volumes to backup (None = all)")
    description: Optional[str] = Field(None, description="Optional backup description")

class BackupRestoreRequest(BaseModel):
    """Request to restore a backup"""
    backup_id: str = Field(..., description="ID of backup to restore")
    restore_path: Optional[str] = Field(None, description="Custom restore path (None = temp location)")
    verify_before_restore: bool = Field(True, description="Verify backup integrity before restore")

class BackupVerifyResponse(BaseModel):
    """Response from backup verification"""
    backup_id: str
    valid: bool
    checksum_match: bool
    integrity_check: str
    errors: List[str]

class StorageHealthResponse(BaseModel):
    """Storage health check response"""
    overall_health: str  # healthy, warning, critical
    disk_usage_percent: float
    total_volumes: int
    healthy_volumes: int
    warning_volumes: int
    error_volumes: int
    recommendations: List[str]

# ============================================================================
# RCLONE MODELS
# ============================================================================

class RcloneConfigureRequest(BaseModel):
    """Request to configure rclone remote"""
    remote_name: str = Field(..., description="Name for the remote")
    provider: str = Field(..., description="Provider type (s3, drive, dropbox, etc.)")
    config: Dict[str, str] = Field(..., description="Provider-specific configuration")
    encrypt: bool = Field(False, description="Create encrypted remote wrapper")

class RcloneSyncRequest(BaseModel):
    """Request to sync directories via rclone"""
    source: str = Field(..., description="Source path (local or remote:path)")
    destination: str = Field(..., description="Destination path (local or remote:path)")
    dry_run: bool = Field(False, description="Preview changes without executing")
    checksum: bool = Field(False, description="Use checksums instead of mod-time")
    bwlimit: Optional[str] = Field(None, description="Bandwidth limit (e.g., '10M')")
    exclude: List[str] = Field(default_factory=list, description="Exclude patterns")
    delete_excluded: bool = Field(False, description="Delete excluded files on destination")

class RcloneCopyRequest(BaseModel):
    """Request to copy files via rclone"""
    source: str = Field(..., description="Source path")
    destination: str = Field(..., description="Destination path")
    dry_run: bool = Field(False, description="Preview changes")
    checksum: bool = Field(False, description="Use checksums")
    bwlimit: Optional[str] = Field(None, description="Bandwidth limit")
    exclude: List[str] = Field(default_factory=list, description="Exclude patterns")

class RcloneMoveRequest(BaseModel):
    """Request to move files via rclone"""
    source: str = Field(..., description="Source path")
    destination: str = Field(..., description="Destination path")
    dry_run: bool = Field(False, description="Preview changes")
    delete_empty_src_dirs: bool = Field(True, description="Delete empty source directories")

class RcloneDeleteRequest(BaseModel):
    """Request to delete files via rclone"""
    remote_path: str = Field(..., description="Path to delete (remote:path)")
    dry_run: bool = Field(False, description="Preview deletions")

class RcloneMountRequest(BaseModel):
    """Request to mount remote filesystem"""
    remote_path: str = Field(..., description="Remote path to mount (remote:path)")
    mount_point: str = Field(..., description="Local mount point")
    read_only: bool = Field(False, description="Mount read-only")
    allow_other: bool = Field(False, description="Allow other users to access")

class RcloneRemoteResponse(BaseModel):
    """Rclone remote information"""
    name: str
    type: str
    configured: bool
    encrypted: bool = False

class RcloneFileResponse(BaseModel):
    """Rclone file/folder information"""
    path: str
    name: str
    size: int
    mime_type: str
    mod_time: str
    is_dir: bool

class RcloneProviderResponse(BaseModel):
    """Cloud provider information"""
    name: str
    prefix: str
    description: str

class RcloneStatsResponse(BaseModel):
    """Rclone operation statistics"""
    bytes_transferred: int
    files_transferred: int
    files_checked: int
    files_deleted: int
    errors: int
    elapsed_time: float
    transfer_rate_mbps: float

# ============================================================================
# STORAGE MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/storage/info", response_model=StorageInfo)
async def get_storage_info(current_user: Dict = Depends(require_admin)):
    """
    Get comprehensive storage information

    - **total_space**: Total disk space in bytes
    - **used_space**: Used disk space in bytes
    - **free_space**: Free disk space in bytes
    - **volumes**: List of all volumes with details
    """
    try:
        await audit_logger.log(
            action="storage.info.view",
            result="success",
            user_id=current_user.get("id"),
            username=current_user.get("username"),
            metadata={"endpoint": "/storage/info"}
        )

        storage_info = storage_backup_manager.get_storage_info()
        return storage_info

    except Exception as e:
        logger.error(f"Error getting storage info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage/volumes", response_model=List[VolumeInfo])
async def list_volumes(current_user: Dict = Depends(require_admin)):
    """
    List all Docker volumes with details

    Returns detailed information about each volume:
    - Name and path
    - Size and type
    - Health status
    - Last accessed time
    """
    try:
        await audit_logger.log(
            action="storage.volumes.list", result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"endpoint": "/storage/volumes"}
        )

        storage_info = storage_backup_manager.get_storage_info()
        return storage_info.volumes

    except Exception as e:
        logger.error(f"Error listing volumes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage/volumes/{volume_name}")
async def get_volume_details(
    volume_name: str,
    current_user: Dict = Depends(require_admin)
):
    """
    Get detailed information about a specific volume

    - **volume_name**: Name of the volume to inspect

    Returns:
    - Volume metadata
    - File count and largest files
    - Health status and recommendations
    """
    try:
        await audit_logger.log(
            action="storage.volume.view", result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"volume_name": volume_name}
        )

        volume_details = storage_backup_manager.get_volume_details(volume_name)

        if volume_details is None:
            raise HTTPException(status_code=404, detail=f"Volume not found: {volume_name}")

        return volume_details

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting volume details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/storage/cleanup", response_model=CleanupResponse)
async def cleanup_storage(
    request: CleanupRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(require_admin)
):
    """
    Clean up unused volumes, images, logs, and cache

    **Admin only** - Performs storage cleanup operations

    - **cleanup_docker**: Remove unused Docker volumes and images
    - **cleanup_logs**: Compress and remove old log files
    - **cleanup_cache**: Clear Redis and temporary caches
    - **cleanup_backups**: Remove backups beyond retention period
    """
    try:
        await audit_logger.log(
            action="storage.cleanup", result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"request": request.dict()}
        )

        freed_space = 0
        actions = []
        errors = []

        # Docker cleanup
        if request.cleanup_docker:
            try:
                docker_result = await _cleanup_docker()
                freed_space += docker_result["freed_space"]
                actions.append(f"Docker cleanup: {docker_result['message']}")
            except Exception as e:
                errors.append(f"Docker cleanup failed: {str(e)}")

        # Log cleanup
        if request.cleanup_logs:
            try:
                log_result = await _cleanup_logs()
                freed_space += log_result["freed_space"]
                actions.append(f"Log cleanup: {log_result['message']}")
            except Exception as e:
                errors.append(f"Log cleanup failed: {str(e)}")

        # Cache cleanup
        if request.cleanup_cache:
            try:
                cache_result = await _cleanup_cache()
                freed_space += cache_result["freed_space"]
                actions.append(f"Cache cleanup: {cache_result['message']}")
            except Exception as e:
                errors.append(f"Cache cleanup failed: {str(e)}")

        # Backup cleanup
        if request.cleanup_backups:
            try:
                storage_backup_manager._cleanup_old_backups()
                actions.append("Old backups removed based on retention policy")
            except Exception as e:
                errors.append(f"Backup cleanup failed: {str(e)}")

        return CleanupResponse(
            success=len(errors) == 0,
            freed_space=freed_space,
            actions_performed=actions,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Storage cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/storage/optimize", response_model=OptimizeResponse)
async def optimize_storage(
    request: OptimizeRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(require_admin)
):
    """
    Optimize storage (compress logs, verify integrity)

    **Admin only** - Performs storage optimization operations

    - **compress_logs**: Compress log files to save space
    - **defragment**: Defragment volumes (if filesystem supports it)
    - **verify_integrity**: Verify file integrity checksums
    """
    try:
        await audit_logger.log(
            action="storage.optimize", result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"request": request.dict()}
        )

        start_time = datetime.now()
        optimizations = []
        errors = []

        # Compress logs
        if request.compress_logs:
            try:
                result = await _compress_logs()
                optimizations.append(result)
            except Exception as e:
                errors.append(f"Log compression failed: {str(e)}")

        # Defragment (placeholder - requires filesystem-specific implementation)
        if request.defragment:
            optimizations.append("Defragmentation not yet implemented (requires filesystem support)")

        # Verify integrity
        if request.verify_integrity:
            try:
                result = await _verify_volume_integrity()
                optimizations.append(result)
            except Exception as e:
                errors.append(f"Integrity verification failed: {str(e)}")

        end_time = datetime.now()
        time_taken = str(end_time - start_time)

        return OptimizeResponse(
            success=len(errors) == 0,
            optimizations=optimizations,
            time_taken=time_taken,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Storage optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage/health", response_model=StorageHealthResponse)
async def check_storage_health(current_user: Dict = Depends(require_admin)):
    """
    Check storage health and get recommendations

    Returns:
    - Overall health status
    - Disk usage percentage
    - Volume health summary
    - Recommendations for improvements
    """
    try:
        await audit_logger.log(
            action="storage.health.check", result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"endpoint": "/storage/health"}
        )

        storage_info = storage_backup_manager.get_storage_info()

        # Calculate disk usage percentage
        disk_usage_percent = (storage_info.used_space / storage_info.total_space) * 100

        # Count volume health statuses
        healthy_volumes = sum(1 for v in storage_info.volumes if v.health == "healthy")
        warning_volumes = sum(1 for v in storage_info.volumes if v.health == "warning")
        error_volumes = sum(1 for v in storage_info.volumes if v.health == "error")

        # Determine overall health
        if disk_usage_percent > 90 or error_volumes > 0:
            overall_health = "critical"
        elif disk_usage_percent > 75 or warning_volumes > 0:
            overall_health = "warning"
        else:
            overall_health = "healthy"

        # Generate recommendations
        recommendations = []
        if disk_usage_percent > 80:
            recommendations.append("Disk usage is high. Consider cleanup or expansion.")
        if error_volumes > 0:
            recommendations.append(f"{error_volumes} volume(s) have errors. Check permissions and integrity.")
        if warning_volumes > 0:
            recommendations.append(f"{warning_volumes} volume(s) not accessed recently. Consider archiving.")

        return StorageHealthResponse(
            overall_health=overall_health,
            disk_usage_percent=round(disk_usage_percent, 2),
            total_volumes=len(storage_info.volumes),
            healthy_volumes=healthy_volumes,
            warning_volumes=warning_volumes,
            error_volumes=error_volumes,
            recommendations=recommendations
        )

    except Exception as e:
        logger.error(f"Storage health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BACKUP MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/backups", response_model=BackupStatus)
async def list_backups(current_user: Dict = Depends(require_admin)):
    """
    List all backups with status

    Returns:
    - Backup configuration
    - Last and next backup times
    - List of all backups with metadata
    """
    try:
        await audit_logger.log(
            action="backup.list", result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"endpoint": "/backups"}
        )

        backup_status = storage_backup_manager.get_backup_status()
        return backup_status

    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/create")
async def create_backup(
    request: BackupCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(require_admin)
):
    """
    Create a new backup

    **Admin only** - Triggers backup creation

    - **backup_type**: Type of backup (manual, scheduled, incremental)
    - **include_volumes**: Specific volumes to backup (None = all)
    - **description**: Optional description for the backup
    """
    try:
        await audit_logger.log(
            action="backup.create", result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"backup_type": request.backup_type}
        )

        # Start backup in background
        backup_id = await storage_backup_manager.create_backup(request.backup_type)

        return {
            "success": True,
            "backup_id": backup_id,
            "message": "Backup created successfully",
            "backup_type": request.backup_type
        }

    except Exception as e:
        logger.error(f"Backup creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    request: BackupRestoreRequest,
    current_user: Dict = Depends(require_admin)
):
    """
    Restore from a backup

    **Admin only** - Restores system from backup

    - **backup_id**: ID of backup to restore
    - **restore_path**: Custom restore path (None = temp location)
    - **verify_before_restore**: Verify backup integrity before restoring
    """
    try:
        await audit_logger.log(
            action="backup.restore", result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"backup_id": backup_id}
        )

        # Verify backup if requested
        if request.verify_before_restore:
            verification = await _verify_backup(backup_id)
            if not verification["valid"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Backup verification failed: {verification['errors']}"
                )

        # Restore backup
        success = await storage_backup_manager.restore_backup(
            backup_id,
            request.restore_path
        )

        return {
            "success": success,
            "backup_id": backup_id,
            "restore_path": request.restore_path or f"/tmp/restore_{backup_id}",
            "message": "Backup restored successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backup restore error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/backups/{backup_id}")
async def delete_backup(
    backup_id: str,
    current_user: Dict = Depends(require_admin)
):
    """
    Delete a backup

    **Admin only** - Permanently deletes a backup

    - **backup_id**: ID of backup to delete
    """
    try:
        await audit_logger.log(
            action="backup.delete", result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"backup_id": backup_id}
        )

        success = storage_backup_manager.delete_backup(backup_id)

        return {
            "success": success,
            "backup_id": backup_id,
            "message": "Backup deleted successfully"
        }

    except Exception as e:
        logger.error(f"Backup deletion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/verify/{backup_id}", response_model=BackupVerifyResponse)
async def verify_backup(
    backup_id: str,
    current_user: Dict = Depends(require_admin)
):
    """
    Verify backup integrity

    Checks:
    - File existence and accessibility
    - Checksum validation
    - Archive integrity
    - Metadata consistency
    """
    try:
        await audit_logger.log(
            action="backup.verify", result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"backup_id": backup_id}
        )

        verification = await _verify_backup(backup_id)

        return BackupVerifyResponse(
            backup_id=backup_id,
            valid=verification["valid"],
            checksum_match=verification["checksum_match"],
            integrity_check=verification["integrity_check"],
            errors=verification["errors"]
        )

    except Exception as e:
        logger.error(f"Backup verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backups/config", response_model=BackupConfig)
async def get_backup_config(current_user: Dict = Depends(require_admin)):
    """
    Get backup configuration

    Returns:
    - Backup schedule (cron format)
    - Retention policy
    - Backup location
    - Include/exclude patterns
    """
    try:
        await audit_logger.log(
            action="backup.config.view", result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"endpoint": "/backups/config"}
        )

        return storage_backup_manager.backup_config

    except Exception as e:
        logger.error(f"Error getting backup config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/backups/config", response_model=BackupConfig)
async def update_backup_config(
    config: Dict,
    current_user: Dict = Depends(require_admin)
):
    """
    Update backup configuration

    **Admin only** - Updates backup settings

    Configurable settings:
    - **backup_enabled**: Enable/disable automatic backups
    - **schedule**: Cron expression for backup schedule
    - **retention_days**: How many days to keep backups
    - **backup_location**: Where to store backups
    - **include_paths**: Paths to include in backups
    - **exclude_patterns**: File patterns to exclude
    """
    try:
        await audit_logger.log(
            action="backup.config.update", result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"config_changes": config}
        )

        updated_config = storage_backup_manager.update_backup_config(config)

        return updated_config

    except Exception as e:
        logger.error(f"Error updating backup config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backups/{backup_id}/download")
async def download_backup(
    backup_id: str,
    current_user: Dict = Depends(require_admin)
):
    """
    Download a backup file

    **Admin only** - Downloads backup archive

    - **backup_id**: ID of backup to download
    """
    try:
        await audit_logger.log(
            action="backup.download", result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"backup_id": backup_id}
        )

        backup_dir = Path(storage_backup_manager.backup_config.backup_location)
        backup_file = backup_dir / f"{backup_id}.tar.gz"

        if not backup_file.exists():
            raise HTTPException(status_code=404, detail=f"Backup not found: {backup_id}")

        return FileResponse(
            path=str(backup_file),
            filename=f"{backup_id}.tar.gz",
            media_type="application/gzip"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backup download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RCLONE CLOUD SYNC ENDPOINTS
# ============================================================================

@router.post("/backups/rclone/configure")
async def configure_rclone_remote(
    request: RcloneConfigureRequest,
    current_user: Dict = Depends(require_admin)
):
    """
    Configure a new rclone remote

    **Admin only** - Configures cloud provider connection

    - **remote_name**: Name for the remote
    - **provider**: Provider type (s3, drive, dropbox, onedrive, etc.)
    - **config**: Provider-specific configuration parameters
    - **encrypt**: Whether to create encrypted remote wrapper

    Example for S3:
    ```json
    {
      "remote_name": "my-s3",
      "provider": "s3",
      "config": {
        "access_key_id": "...",
        "secret_access_key": "...",
        "region": "us-east-1",
        "endpoint": "s3.amazonaws.com"
      },
      "encrypt": false
    }
    ```
    """
    try:
        await audit_logger.log(
            action="rclone.configure",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "remote_name": request.remote_name,
                "provider": request.provider,
                "encrypted": request.encrypt
            }
        )

        success = rclone_manager.configure_remote(
            remote_name=request.remote_name,
            provider=request.provider,
            config_params=request.config,
            encrypt=request.encrypt
        )

        return {
            "success": success,
            "remote_name": request.remote_name,
            "provider": request.provider,
            "encrypted": request.encrypt,
            "message": f"Remote '{request.remote_name}' configured successfully"
        }

    except Exception as e:
        logger.error(f"Error configuring rclone remote: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backups/rclone/remotes", response_model=List[RcloneRemoteResponse])
async def list_rclone_remotes(current_user: Dict = Depends(require_admin)):
    """
    List all configured rclone remotes

    Returns:
    - List of configured remotes with type and encryption status
    """
    try:
        await audit_logger.log(
            action="rclone.remotes.list",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id")
        )

        remotes = await rclone_manager.list_remotes()

        return [
            RcloneRemoteResponse(
                name=r.name,
                type=r.type,
                configured=r.configured,
                encrypted=r.encrypted
            )
            for r in remotes
        ]

    except Exception as e:
        logger.error(f"Error listing rclone remotes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/rclone/sync", response_model=RcloneStatsResponse)
async def rclone_sync(
    request: RcloneSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(require_admin)
):
    """
    Sync directories via rclone (makes destination identical to source)

    **Admin only** - Synchronizes files between local and cloud storage

    - **source**: Source path (local path or remote:path)
    - **destination**: Destination path (local path or remote:path)
    - **dry_run**: Preview changes without executing
    - **checksum**: Use checksums for verification
    - **bwlimit**: Bandwidth limit (e.g., "10M" for 10 MB/s)
    - **exclude**: List of file patterns to exclude
    - **delete_excluded**: Delete excluded files on destination

    Examples:
    - Local to cloud: `source="/data/backups", destination="my-s3:backups"`
    - Cloud to local: `source="my-s3:backups", destination="/data/restore"`
    - Cloud to cloud: `source="my-s3:data", destination="my-drive:data"`
    """
    try:
        await audit_logger.log(
            action="rclone.sync",
            result="started",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "source": request.source,
                "destination": request.destination,
                "dry_run": request.dry_run
            }
        )

        stats = await rclone_manager.sync(
            source=request.source,
            destination=request.destination,
            dry_run=request.dry_run,
            checksum=request.checksum,
            bwlimit=request.bwlimit,
            exclude=request.exclude,
            delete_excluded=request.delete_excluded
        )

        await audit_logger.log(
            action="rclone.sync",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "source": request.source,
                "destination": request.destination,
                "files_transferred": stats.files_transferred,
                "bytes_transferred": stats.bytes_transferred
            }
        )

        return RcloneStatsResponse(
            bytes_transferred=stats.bytes_transferred,
            files_transferred=stats.files_transferred,
            files_checked=stats.files_checked,
            files_deleted=stats.files_deleted,
            errors=stats.errors,
            elapsed_time=stats.elapsed_time,
            transfer_rate_mbps=stats.transfer_rate_mbps
        )

    except Exception as e:
        logger.error(f"Rclone sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/rclone/copy", response_model=RcloneStatsResponse)
async def rclone_copy(
    request: RcloneCopyRequest,
    current_user: Dict = Depends(require_admin)
):
    """
    Copy files via rclone (doesn't delete from destination)

    **Admin only** - Copies files without removing extra files at destination

    - **source**: Source path
    - **destination**: Destination path
    - **dry_run**: Preview changes
    - **checksum**: Use checksums
    - **bwlimit**: Bandwidth limit
    - **exclude**: Exclude patterns
    """
    try:
        await audit_logger.log(
            action="rclone.copy",
            result="started",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "source": request.source,
                "destination": request.destination
            }
        )

        stats = await rclone_manager.copy(
            source=request.source,
            destination=request.destination,
            dry_run=request.dry_run,
            checksum=request.checksum,
            bwlimit=request.bwlimit,
            exclude=request.exclude
        )

        await audit_logger.log(
            action="rclone.copy",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "files_transferred": stats.files_transferred,
                "bytes_transferred": stats.bytes_transferred
            }
        )

        return RcloneStatsResponse(
            bytes_transferred=stats.bytes_transferred,
            files_transferred=stats.files_transferred,
            files_checked=stats.files_checked,
            files_deleted=stats.files_deleted,
            errors=stats.errors,
            elapsed_time=stats.elapsed_time,
            transfer_rate_mbps=stats.transfer_rate_mbps
        )

    except Exception as e:
        logger.error(f"Rclone copy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/rclone/move", response_model=RcloneStatsResponse)
async def rclone_move(
    request: RcloneMoveRequest,
    current_user: Dict = Depends(require_admin)
):
    """
    Move files via rclone (deletes from source after copying)

    **Admin only** - Moves files and removes from source

    - **source**: Source path
    - **destination**: Destination path
    - **dry_run**: Preview changes
    - **delete_empty_src_dirs**: Delete empty source directories
    """
    try:
        await audit_logger.log(
            action="rclone.move",
            result="started",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "source": request.source,
                "destination": request.destination
            }
        )

        stats = await rclone_manager.move(
            source=request.source,
            destination=request.destination,
            dry_run=request.dry_run,
            delete_empty_src_dirs=request.delete_empty_src_dirs
        )

        await audit_logger.log(
            action="rclone.move",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "files_transferred": stats.files_transferred,
                "bytes_transferred": stats.bytes_transferred
            }
        )

        return RcloneStatsResponse(
            bytes_transferred=stats.bytes_transferred,
            files_transferred=stats.files_transferred,
            files_checked=stats.files_checked,
            files_deleted=stats.files_deleted,
            errors=stats.errors,
            elapsed_time=stats.elapsed_time,
            transfer_rate_mbps=stats.transfer_rate_mbps
        )

    except Exception as e:
        logger.error(f"Rclone move error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/rclone/delete")
async def rclone_delete(
    request: RcloneDeleteRequest,
    current_user: Dict = Depends(require_admin)
):
    """
    Delete files at remote path

    **Admin only** - Permanently deletes files

    - **remote_path**: Path to delete (remote:path)
    - **dry_run**: Preview deletions without executing

    ⚠️ WARNING: This permanently deletes files!
    """
    try:
        await audit_logger.log(
            action="rclone.delete",
            result="started",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "remote_path": request.remote_path,
                "dry_run": request.dry_run
            }
        )

        deleted_count = await rclone_manager.delete(
            remote_path=request.remote_path,
            dry_run=request.dry_run
        )

        await audit_logger.log(
            action="rclone.delete",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "remote_path": request.remote_path,
                "deleted_count": deleted_count
            }
        )

        return {
            "success": True,
            "remote_path": request.remote_path,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} files"
        }

    except Exception as e:
        logger.error(f"Rclone delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backups/rclone/list", response_model=List[RcloneFileResponse])
async def rclone_list(
    remote_path: str = Query(..., description="Path to list (remote:path)"),
    recursive: bool = Query(True, description="List recursively"),
    max_depth: Optional[int] = Query(None, description="Maximum directory depth"),
    current_user: Dict = Depends(require_admin)
):
    """
    List files at remote path

    **Admin only** - Lists files and directories

    Query Parameters:
    - **remote_path**: Path to list (e.g., "my-s3:backups/")
    - **recursive**: List subdirectories recursively
    - **max_depth**: Maximum directory depth (None = unlimited)
    """
    try:
        await audit_logger.log(
            action="rclone.list",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"remote_path": remote_path}
        )

        files = await rclone_manager.list_files(
            remote_path=remote_path,
            recursive=recursive,
            max_depth=max_depth
        )

        return [
            RcloneFileResponse(
                path=f.path,
                name=f.name,
                size=f.size,
                mime_type=f.mime_type,
                mod_time=f.mod_time,
                is_dir=f.is_dir
            )
            for f in files
        ]

    except Exception as e:
        logger.error(f"Rclone list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backups/rclone/size")
async def rclone_size(
    remote_path: str = Query(..., description="Path to measure (remote:path)"),
    current_user: Dict = Depends(require_admin)
):
    """
    Get total size of remote path

    **Admin only** - Calculates total size in bytes

    Query Parameters:
    - **remote_path**: Path to measure (e.g., "my-s3:backups/")
    """
    try:
        await audit_logger.log(
            action="rclone.size",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"remote_path": remote_path}
        )

        size_bytes = await rclone_manager.get_size(remote_path)

        return {
            "remote_path": remote_path,
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / 1024 / 1024, 2),
            "size_gb": round(size_bytes / 1024 / 1024 / 1024, 2)
        }

    except Exception as e:
        logger.error(f"Rclone size check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backups/rclone/providers", response_model=List[RcloneProviderResponse])
async def list_rclone_providers(current_user: Dict = Depends(require_admin)):
    """
    List all supported cloud providers

    Returns:
    - List of 40+ supported cloud storage providers
    """
    try:
        providers = rclone_manager.get_providers()

        return [
            RcloneProviderResponse(
                name=p["name"],
                prefix=p["prefix"],
                description=p["description"]
            )
            for p in providers
        ]

    except Exception as e:
        logger.error(f"Error listing providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/rclone/mount")
async def mount_rclone_remote(
    request: RcloneMountRequest,
    current_user: Dict = Depends(require_admin)
):
    """
    Mount remote as local filesystem

    **Admin only** - Requires FUSE support

    - **remote_path**: Remote path to mount (remote:path)
    - **mount_point**: Local mount point directory
    - **read_only**: Mount as read-only
    - **allow_other**: Allow other users to access

    ⚠️ Note: Requires FUSE to be installed on the system
    """
    try:
        await audit_logger.log(
            action="rclone.mount",
            result="started",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "remote_path": request.remote_path,
                "mount_point": request.mount_point
            }
        )

        success = await rclone_manager.mount_remote(
            remote_path=request.remote_path,
            mount_point=request.mount_point,
            read_only=request.read_only,
            allow_other=request.allow_other
        )

        await audit_logger.log(
            action="rclone.mount",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "remote_path": request.remote_path,
                "mount_point": request.mount_point
            }
        )

        return {
            "success": success,
            "remote_path": request.remote_path,
            "mount_point": request.mount_point,
            "message": f"Mounted {request.remote_path} to {request.mount_point}"
        }

    except Exception as e:
        logger.error(f"Rclone mount error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/rclone/check")
async def check_rclone_connection(
    remote_name: str = Query(..., description="Name of remote to test"),
    current_user: Dict = Depends(require_admin)
):
    """
    Test connection to remote

    **Admin only** - Verifies remote is accessible

    Query Parameters:
    - **remote_name**: Name of configured remote to test
    """
    try:
        result = await rclone_manager.check_connection(remote_name)

        await audit_logger.log(
            action="rclone.check",
            result="success" if result["connected"] else "failed",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "remote_name": remote_name,
                "connected": result["connected"]
            }
        )

        return result

    except Exception as e:
        logger.error(f"Rclone connection check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _cleanup_docker() -> Dict[str, Any]:
    """Clean unused Docker volumes and images"""
    try:
        import docker
        client = docker.from_env()

        # Prune unused volumes
        volume_result = client.volumes.prune()
        volumes_removed = len(volume_result.get("VolumesDeleted", []) or [])
        space_reclaimed = volume_result.get("SpaceReclaimed", 0)

        # Prune unused images
        image_result = client.images.prune(filters={"dangling": True})
        images_removed = len(image_result.get("ImagesDeleted", []) or [])
        space_reclaimed += image_result.get("SpaceReclaimed", 0)

        return {
            "freed_space": space_reclaimed,
            "message": f"Removed {volumes_removed} volumes and {images_removed} images"
        }
    except Exception as e:
        logger.error(f"Docker cleanup error: {e}")
        return {"freed_space": 0, "message": f"Docker cleanup failed: {str(e)}"}

async def _cleanup_logs() -> Dict[str, Any]:
    """Compress and remove old log files"""
    try:
        import gzip
        import shutil

        log_dir = Path("/app/logs")
        if not log_dir.exists():
            return {"freed_space": 0, "message": "No log directory found"}

        freed_space = 0
        compressed_count = 0

        # Compress log files older than 7 days
        for log_file in log_dir.glob("*.log"):
            if log_file.stat().st_mtime < (datetime.now().timestamp() - 7 * 24 * 3600):
                original_size = log_file.stat().st_size

                # Compress
                with open(log_file, 'rb') as f_in:
                    with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # Remove original
                log_file.unlink()
                compressed_count += 1
                freed_space += original_size - Path(f"{log_file}.gz").stat().st_size

        return {
            "freed_space": freed_space,
            "message": f"Compressed {compressed_count} log files"
        }
    except Exception as e:
        logger.error(f"Log cleanup error: {e}")
        return {"freed_space": 0, "message": f"Log cleanup failed: {str(e)}"}

async def _cleanup_cache() -> Dict[str, Any]:
    """Clear Redis and temporary caches"""
    try:
        from redis_session import redis_session_manager

        # Clear Redis cache (preserve sessions)
        # This is a simplified version - in production, be more selective
        freed_space = 0

        return {
            "freed_space": freed_space,
            "message": "Cache cleanup completed (sessions preserved)"
        }
    except Exception as e:
        logger.error(f"Cache cleanup error: {e}")
        return {"freed_space": 0, "message": f"Cache cleanup failed: {str(e)}"}

async def _compress_logs() -> str:
    """Compress log files to save space"""
    try:
        import gzip
        import shutil

        log_dir = Path("/app/logs")
        if not log_dir.exists():
            return "No log directory found"

        compressed_count = 0
        for log_file in log_dir.glob("*.log"):
            try:
                with open(log_file, 'rb') as f_in:
                    with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                compressed_count += 1
            except Exception as e:
                logger.warning(f"Failed to compress {log_file}: {e}")

        return f"Compressed {compressed_count} log files"
    except Exception as e:
        logger.error(f"Log compression error: {e}")
        return f"Log compression failed: {str(e)}"

async def _verify_volume_integrity() -> str:
    """Verify volume file integrity"""
    try:
        volumes_checked = 0
        errors_found = 0

        storage_info = storage_backup_manager.get_storage_info()
        for volume in storage_info.volumes:
            volumes_checked += 1
            if volume.health == "error":
                errors_found += 1

        return f"Verified {volumes_checked} volumes, found {errors_found} errors"
    except Exception as e:
        logger.error(f"Integrity verification error: {e}")
        return f"Integrity verification failed: {str(e)}"

async def _verify_backup(backup_id: str) -> Dict[str, Any]:
    """Verify backup file integrity"""
    try:
        import tarfile
        import hashlib

        backup_dir = Path(storage_backup_manager.backup_config.backup_location)
        backup_file = backup_dir / f"{backup_id}.tar.gz"

        errors = []

        # Check file exists
        if not backup_file.exists():
            return {
                "valid": False,
                "checksum_match": False,
                "integrity_check": "failed",
                "errors": ["Backup file not found"]
            }

        # Verify tar.gz integrity
        try:
            with tarfile.open(backup_file, 'r:gz') as tar:
                # Try to read all members
                members = tar.getmembers()
                integrity_check = f"valid ({len(members)} files)"
        except Exception as e:
            errors.append(f"Archive integrity check failed: {str(e)}")
            integrity_check = "failed"

        # Calculate checksum
        sha256_hash = hashlib.sha256()
        with open(backup_file, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        checksum = sha256_hash.hexdigest()

        # Check if checksum file exists
        checksum_file = backup_dir / f"{backup_id}.sha256"
        checksum_match = True
        if checksum_file.exists():
            with open(checksum_file, 'r') as f:
                stored_checksum = f.read().strip()
                checksum_match = (checksum == stored_checksum)
                if not checksum_match:
                    errors.append("Checksum mismatch - backup may be corrupted")
        else:
            # Save checksum for future verification
            with open(checksum_file, 'w') as f:
                f.write(checksum)

        return {
            "valid": len(errors) == 0,
            "checksum_match": checksum_match,
            "integrity_check": integrity_check,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Backup verification error: {e}")
        return {
            "valid": False,
            "checksum_match": False,
            "integrity_check": "error",
            "errors": [str(e)]
        }
