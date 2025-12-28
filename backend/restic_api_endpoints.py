"""
Restic Backup API Endpoints for Ops-Center
FastAPI endpoints for Restic backup operations
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from backup_restic import restic_backup_manager
from audit_logger import audit_logger

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/backups/restic", tags=["Restic Backup"])

# Admin authentication dependency
async def require_admin(request: Any = None):
    """Require admin role for endpoints"""
    # Simplified auth - in production, verify JWT token and role
    return {"role": "admin", "username": "admin", "id": "admin"}

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ResticInitRequest(BaseModel):
    """Request to initialize Restic repository"""
    repository_path: str = Field(..., description="Repository path (local or remote URL)")
    password: str = Field(..., description="Repository password for encryption")

class ResticBackupRequest(BaseModel):
    """Request to create Restic backup"""
    source_paths: List[str] = Field(..., description="List of paths to backup")
    repository_path: str = Field(..., description="Repository path")
    password: str = Field(..., description="Repository password")
    tags: List[str] = Field(default=[], description="Optional tags for snapshot")
    exclude_patterns: List[str] = Field(default=[], description="File patterns to exclude")

class ResticRestoreRequest(BaseModel):
    """Request to restore Restic snapshot"""
    snapshot_id: str = Field(..., description="Snapshot ID to restore")
    target_path: str = Field(..., description="Target path for restore")
    repository_path: str = Field(..., description="Repository path")
    password: str = Field(..., description="Repository password")
    include_patterns: Optional[List[str]] = Field(None, description="File patterns to include")
    exclude_patterns: Optional[List[str]] = Field(None, description="File patterns to exclude")

class ResticPruneRequest(BaseModel):
    """Request to prune Restic repository"""
    repository_path: str = Field(..., description="Repository path")
    password: str = Field(..., description="Repository password")
    keep_policy: Optional[Dict[str, int]] = Field(
        None,
        description="Retention policy (e.g., {'daily': 7, 'weekly': 4, 'monthly': 6})"
    )

class ResticSnapshot(BaseModel):
    """Restic snapshot information"""
    id: str
    short_id: str
    time: str
    hostname: str
    username: Optional[str] = None
    paths: List[str]
    tags: List[str]
    tree: Optional[str] = None

class ResticStats(BaseModel):
    """Restic repository statistics"""
    total_size: int
    total_file_count: int
    snapshots_count: int
    deduplication_ratio: float
    message: str

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/init")
async def initialize_restic_repository(
    request: ResticInitRequest,
    current_user: Dict = Depends(require_admin)
):
    """
    Initialize a new Restic repository

    **Admin only** - Creates a new encrypted backup repository

    - **repository_path**: Local path or remote URL (s3:, sftp:, etc.)
    - **password**: Encryption password (will be encrypted for storage)

    Supports:
    - Local repositories: `/path/to/repo`
    - SFTP: `sftp:user@host:/path/to/repo`
    - S3: `s3:s3.amazonaws.com/bucket/repo`
    - Backblaze B2: `b2:bucket:repo`
    - Azure: `azure:container:/repo`
    """
    try:
        await audit_logger.log(
            action="restic.init",
            result="pending",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"repository_path": request.repository_path}
        )

        result = await restic_backup_manager.initialize_repository(
            request.repository_path,
            request.password
        )

        await audit_logger.log(
            action="restic.init",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"repository_path": request.repository_path}
        )

        return {
            "success": True,
            "repository_path": request.repository_path,
            "encrypted_password": result["encrypted_password"],
            "message": "Restic repository initialized successfully"
        }

    except Exception as e:
        logger.error(f"Restic init error: {e}")
        await audit_logger.log(
            action="restic.init",
            result="error",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backup")
async def create_restic_backup(
    request: ResticBackupRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(require_admin)
):
    """
    Create a Restic backup snapshot

    **Admin only** - Creates incremental backup with deduplication

    - **source_paths**: List of directories/files to backup
    - **repository_path**: Repository location
    - **password**: Repository password
    - **tags**: Optional tags for organization
    - **exclude_patterns**: Patterns to exclude (e.g., `*.tmp`, `node_modules`)

    Features:
    - Automatic deduplication
    - Incremental backups (only changed data)
    - Encryption at rest
    - Compression
    """
    try:
        await audit_logger.log(
            action="restic.backup.create",
            result="pending",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "source_paths": request.source_paths,
                "tags": request.tags
            }
        )

        # Progress tracking callback
        progress_updates = []

        def progress_callback(message: str):
            progress_updates.append({
                "time": datetime.now().isoformat(),
                "message": message
            })
            logger.debug(f"Backup progress: {message}")

        # Create backup
        result = await restic_backup_manager.backup(
            source_paths=request.source_paths,
            repo_path=request.repository_path,
            password=request.password,
            tags=request.tags,
            exclude_patterns=request.exclude_patterns,
            progress_callback=progress_callback
        )

        return {
            "success": True,
            "snapshot_id": result["snapshot_id"],
            "files_new": result["files_new"],
            "files_changed": result["files_changed"],
            "files_unmodified": result["files_unmodified"],
            "total_files": result["total_files"],
            "data_added": result["data_added"],
            "total_bytes": result["total_bytes"],
            "progress_updates": progress_updates[-10:],  # Last 10 updates
            "message": f"Backup created: {result['snapshot_id']}"
        }

    except Exception as e:
        logger.error(f"Restic backup error: {e}")
        await audit_logger.log(
            action="restic.backup.create",
            result="error",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/snapshots")
async def list_restic_snapshots(
    repository_path: str = Query(..., description="Repository path"),
    password: str = Query(..., description="Repository password"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    current_user: Dict = Depends(require_admin)
):
    """
    List all Restic snapshots

    **Admin only** - Lists all backup snapshots in repository

    Query Parameters:
    - **repository_path**: Repository location
    - **password**: Repository password
    - **tags**: Optional tag filters

    Returns list of snapshots with metadata
    """
    try:
        await audit_logger.log(
            action="restic.snapshots.list",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"repository_path": repository_path}
        )

        snapshots = await restic_backup_manager.list_snapshots(
            repo_path=repository_path,
            password=password,
            tags=tags
        )

        return {
            "success": True,
            "count": len(snapshots),
            "snapshots": snapshots
        }

    except Exception as e:
        logger.error(f"Restic list snapshots error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restore/{snapshot_id}")
async def restore_restic_snapshot(
    snapshot_id: str,
    request: ResticRestoreRequest,
    current_user: Dict = Depends(require_admin)
):
    """
    Restore a Restic snapshot

    **Admin only** - Restores files from backup snapshot

    - **snapshot_id**: Snapshot ID to restore (or 'latest')
    - **target_path**: Where to restore files
    - **repository_path**: Repository location
    - **password**: Repository password
    - **include_patterns**: Optional file patterns to include
    - **exclude_patterns**: Optional file patterns to exclude

    Note: Files are restored to target_path, original directory structure preserved
    """
    try:
        await audit_logger.log(
            action="restic.snapshot.restore",
            result="pending",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "snapshot_id": snapshot_id,
                "target_path": request.target_path
            }
        )

        # Progress tracking
        progress_updates = []

        def progress_callback(message: str):
            progress_updates.append({
                "time": datetime.now().isoformat(),
                "message": message
            })

        # Restore snapshot
        result = await restic_backup_manager.restore(
            snapshot_id=snapshot_id,
            target_path=request.target_path,
            repo_path=request.repository_path,
            password=request.password,
            include_patterns=request.include_patterns,
            exclude_patterns=request.exclude_patterns,
            progress_callback=progress_callback
        )

        return {
            "success": True,
            "snapshot_id": snapshot_id,
            "target_path": request.target_path,
            "progress_updates": progress_updates[-10:],
            "message": f"Snapshot {snapshot_id} restored successfully"
        }

    except Exception as e:
        logger.error(f"Restic restore error: {e}")
        await audit_logger.log(
            action="restic.snapshot.restore",
            result="error",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"error": str(e), "snapshot_id": snapshot_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prune")
async def prune_restic_repository(
    request: ResticPruneRequest,
    current_user: Dict = Depends(require_admin)
):
    """
    Prune old Restic snapshots

    **Admin only** - Remove old snapshots and free storage space

    - **repository_path**: Repository location
    - **password**: Repository password
    - **keep_policy**: Retention policy

    Default retention policy:
    - Daily: 7 snapshots
    - Weekly: 4 snapshots
    - Monthly: 6 snapshots
    - Yearly: 2 snapshots

    Example custom policy:
    ```json
    {
      "daily": 14,
      "weekly": 8,
      "monthly": 12,
      "yearly": 3
    }
    ```
    """
    try:
        await audit_logger.log(
            action="restic.prune",
            result="pending",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"keep_policy": request.keep_policy}
        )

        result = await restic_backup_manager.prune(
            repo_path=request.repository_path,
            password=request.password,
            keep_policy=request.keep_policy
        )

        return {
            "success": True,
            "keep_policy": result["keep_policy"],
            "message": "Repository pruned successfully"
        }

    except Exception as e:
        logger.error(f"Restic prune error: {e}")
        await audit_logger.log(
            action="restic.prune",
            result="error",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=ResticStats)
async def get_restic_stats(
    repository_path: str = Query(..., description="Repository path"),
    password: str = Query(..., description="Repository password"),
    current_user: Dict = Depends(require_admin)
):
    """
    Get Restic repository statistics

    **Admin only** - Retrieve repository statistics and metrics

    Query Parameters:
    - **repository_path**: Repository location
    - **password**: Repository password

    Returns:
    - Total size of backed up data
    - Total file count
    - Number of snapshots
    - Deduplication ratio
    """
    try:
        await audit_logger.log(
            action="restic.stats",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"repository_path": repository_path}
        )

        stats = await restic_backup_manager.get_stats(
            repo_path=repository_path,
            password=password
        )

        return ResticStats(**stats)

    except Exception as e:
        logger.error(f"Restic stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check")
async def check_restic_integrity(
    repository_path: str = Query(..., description="Repository path"),
    password: str = Query(..., description="Repository password"),
    read_data: bool = Query(False, description="Read all data (thorough but slow)"),
    current_user: Dict = Depends(require_admin)
):
    """
    Check Restic repository integrity

    **Admin only** - Verify repository integrity and detect corruption

    Query Parameters:
    - **repository_path**: Repository location
    - **password**: Repository password
    - **read_data**: Read and verify all data blocks (slower but thorough)

    Checks:
    - Repository structure
    - Snapshot metadata
    - Index integrity
    - Data blocks (if read_data=true)
    """
    try:
        await audit_logger.log(
            action="restic.check",
            result="pending",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"repository_path": repository_path, "read_data": read_data}
        )

        result = await restic_backup_manager.check_integrity(
            repo_path=repository_path,
            password=password,
            read_data=read_data
        )

        return {
            "success": result["success"],
            "integrity_ok": result["integrity_ok"],
            "read_data": read_data,
            "message": result["message"],
            "output": result.get("output", "")
        }

    except Exception as e:
        logger.error(f"Restic check error: {e}")
        await audit_logger.log(
            action="restic.check",
            result="error",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))
