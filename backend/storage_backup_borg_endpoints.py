"""
BorgBackup API Endpoints Extension
Add these to storage_backup_api.py after the existing backup endpoints
"""

# ============================================================================
# BORGBACKUP REQUEST/RESPONSE MODELS
# ============================================================================
# Add to imports section:
# from pydantic import BaseModel, Field

class BorgInitRequest(BaseModel):
    """Request to initialize a Borg repository"""
    repository_path: str = Field(..., description="Path to repository (local or ssh://user@host/path)")
    passphrase: str = Field(..., description="Repository encryption passphrase")
    encryption_mode: str = Field("repokey-blake2", description="Encryption mode: repokey-blake2, repokey, keyfile-blake2, authenticated-blake2, none")

class BorgCreateRequest(BaseModel):
    """Request to create a Borg archive"""
    archive_name: str = Field(..., description="Name for the archive (timestamp added automatically)")
    source_paths: List[str] = Field(..., description="List of paths to backup")
    repository_path: str = Field(..., description="Repository path")
    passphrase: str = Field(..., description="Repository passphrase")
    compression: str = Field("lz4", description="Compression: lz4, zstd,3, zstd,10, zlib,6, lzma,6")
    exclude_patterns: List[str] = Field(default_factory=list, description="Glob patterns to exclude")

class BorgArchive(BaseModel):
    """Borg archive metadata"""
    name: str
    archive: str
    time: str
    hostname: str
    username: str
    id: str

class BorgArchiveStats(BaseModel):
    """Archive creation statistics"""
    success: bool
    archive_name: str
    original_size: Optional[int] = 0
    compressed_size: Optional[int] = 0
    deduplicated_size: Optional[int] = 0
    nfiles: Optional[int] = 0
    compression_ratio: Optional[float] = 0.0
    deduplication_ratio: Optional[float] = 0.0
    duration: Optional[float] = 0.0
    error: Optional[str] = None

class BorgPruneRequest(BaseModel):
    """Request to prune old archives"""
    repository_path: str = Field(..., description="Repository path")
    passphrase: str = Field(..., description="Repository passphrase")
    keep_hourly: int = Field(0, description="Keep N hourly archives")
    keep_daily: int = Field(7, description="Keep N daily archives")
    keep_weekly: int = Field(4, description="Keep N weekly archives")
    keep_monthly: int = Field(6, description="Keep N monthly archives")
    keep_yearly: int = Field(2, description="Keep N yearly archives")

class BorgExtractRequest(BaseModel):
    """Request to extract an archive"""
    archive_name: str = Field(..., description="Name of archive to extract")
    target_path: str = Field(..., description="Where to extract files")
    repository_path: str = Field(..., description="Repository path")
    passphrase: str = Field(..., description="Repository passphrase")
    paths: Optional[List[str]] = Field(None, description="Specific paths to extract (None = all)")

class BorgMountRequest(BaseModel):
    """Request to mount an archive"""
    archive_name: str = Field("", description="Archive to mount (empty = all archives)")
    mount_point: str = Field(..., description="Mount point path")
    repository_path: str = Field(..., description="Repository path")
    passphrase: str = Field(..., description="Repository passphrase")

class BorgInfo(BaseModel):
    """Repository information"""
    repository_id: str
    location: str
    last_modified: Optional[str] = None
    encryption_mode: str
    unique_chunks: int
    total_chunks: int
    total_size: int
    unique_size: int
    deduplication_ratio: float

# ============================================================================
# BORGBACKUP ENDPOINTS
# ============================================================================

@router.post("/backups/borg/init")
async def initialize_borg_repository(
    request: BorgInitRequest,
    current_user: Dict = Depends(require_admin)
):
    """
    Initialize a new Borg repository

    **Admin only** - Creates encrypted Borg repository

    - **repository_path**: Local path or ssh://user@host/path
    - **passphrase**: Strong passphrase for encryption
    - **encryption_mode**: Encryption type (repokey-blake2 recommended)

    Encryption modes:
    - `repokey-blake2`: AES-CTR-256 + BLAKE2b (recommended)
    - `repokey`: AES-CTR-256 + HMAC-SHA256
    - `keyfile-blake2`: Key stored separately
    - `authenticated-blake2`: No encryption, only authentication
    - `none`: No encryption (not recommended)
    """
    try:
        await audit_logger.log(
            action="borg.repository.init",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "repository_path": request.repository_path,
                "encryption_mode": request.encryption_mode
            }
        )

        result = borg_manager.initialize_repository(
            repository_path=request.repository_path,
            passphrase=request.passphrase,
            encryption_mode=request.encryption_mode
        )

        return result

    except Exception as e:
        logger.error(f"Borg repository initialization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/borg/create", response_model=BorgArchiveStats)
async def create_borg_archive(
    request: BorgCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(require_admin)
):
    """
    Create a new Borg backup archive

    **Admin only** - Creates compressed, deduplicated backup

    - **archive_name**: Base name (timestamp added automatically)
    - **source_paths**: List of paths to backup
    - **repository_path**: Borg repository path
    - **passphrase**: Repository passphrase
    - **compression**: Compression algorithm (lz4, zstd,3, zlib,6, etc.)
    - **exclude_patterns**: File patterns to exclude

    Compression options:
    - `lz4`: Fast, low compression (default)
    - `zstd,3`: Balanced speed/compression
    - `zstd,10`: High compression
    - `zlib,6`: Standard compression
    - `lzma,6`: Maximum compression (slow)
    """
    try:
        await audit_logger.log(
            action="borg.archive.create",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "archive_name": request.archive_name,
                "source_paths": request.source_paths,
                "compression": request.compression
            }
        )

        result = borg_manager.create_archive(
            archive_name=request.archive_name,
            source_paths=request.source_paths,
            repository_path=request.repository_path,
            passphrase=request.passphrase,
            compression=request.compression,
            exclude_patterns=request.exclude_patterns
        )

        return BorgArchiveStats(**result)

    except Exception as e:
        logger.error(f"Borg archive creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backups/borg/archives", response_model=List[BorgArchive])
async def list_borg_archives(
    repository_path: str = Query(..., description="Repository path"),
    passphrase: str = Query(..., description="Repository passphrase"),
    prefix: Optional[str] = Query(None, description="Filter by name prefix"),
    current_user: Dict = Depends(require_admin)
):
    """
    List all archives in Borg repository

    **Admin only** - Returns list of all backup archives

    - **repository_path**: Borg repository path
    - **passphrase**: Repository passphrase
    - **prefix**: Filter archives by name prefix (optional)
    """
    try:
        await audit_logger.log(
            action="borg.archives.list",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"repository_path": repository_path}
        )

        archives = borg_manager.list_archives(
            repository_path=repository_path,
            passphrase=passphrase,
            prefix=prefix
        )

        return [BorgArchive(**arc) for arc in archives]

    except Exception as e:
        logger.error(f"Borg archive listing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/borg/extract/{archive_name}")
async def extract_borg_archive(
    archive_name: str,
    request: BorgExtractRequest,
    current_user: Dict = Depends(require_admin)
):
    """
    Extract Borg archive contents

    **Admin only** - Extracts files from backup archive

    - **archive_name**: Name of archive to extract
    - **target_path**: Where to extract files
    - **repository_path**: Borg repository path
    - **passphrase**: Repository passphrase
    - **paths**: Specific paths to extract (None = all)
    """
    try:
        await audit_logger.log(
            action="borg.archive.extract",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "archive_name": archive_name,
                "target_path": request.target_path
            }
        )

        result = borg_manager.extract_archive(
            archive_name=archive_name,
            target_path=request.target_path,
            repository_path=request.repository_path,
            passphrase=request.passphrase,
            paths=request.paths
        )

        return result

    except Exception as e:
        logger.error(f"Borg archive extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/backups/borg/archives/{archive_name}")
async def delete_borg_archive(
    archive_name: str,
    repository_path: str = Query(..., description="Repository path"),
    passphrase: str = Query(..., description="Repository passphrase"),
    current_user: Dict = Depends(require_admin)
):
    """
    Delete an archive from Borg repository

    **Admin only** - Permanently deletes backup archive

    - **archive_name**: Name of archive to delete
    - **repository_path**: Borg repository path
    - **passphrase**: Repository passphrase

    Note: Space is not reclaimed until `compact` is run
    """
    try:
        await audit_logger.log(
            action="borg.archive.delete",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"archive_name": archive_name}
        )

        result = borg_manager.delete_archive(
            archive_name=archive_name,
            repository_path=repository_path,
            passphrase=passphrase
        )

        return result

    except Exception as e:
        logger.error(f"Borg archive deletion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/borg/prune")
async def prune_borg_repository(
    request: BorgPruneRequest,
    current_user: Dict = Depends(require_admin)
):
    """
    Prune old archives based on retention policy

    **Admin only** - Removes old backups according to policy

    - **repository_path**: Borg repository path
    - **passphrase**: Repository passphrase
    - **keep_hourly**: Keep N hourly backups
    - **keep_daily**: Keep N daily backups
    - **keep_weekly**: Keep N weekly backups
    - **keep_monthly**: Keep N monthly backups
    - **keep_yearly**: Keep N yearly backups

    Example policy:
    - Keep last 24 hourly backups
    - Keep last 7 daily backups
    - Keep last 4 weekly backups
    - Keep last 6 monthly backups
    - Keep last 2 yearly backups

    Note: Run `compact` after pruning to reclaim disk space
    """
    try:
        await audit_logger.log(
            action="borg.repository.prune",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "repository_path": request.repository_path,
                "keep_policy": {
                    "hourly": request.keep_hourly,
                    "daily": request.keep_daily,
                    "weekly": request.keep_weekly,
                    "monthly": request.keep_monthly,
                    "yearly": request.keep_yearly
                }
            }
        )

        keep_policy = {
            "keep_hourly": request.keep_hourly,
            "keep_daily": request.keep_daily,
            "keep_weekly": request.keep_weekly,
            "keep_monthly": request.keep_monthly,
            "keep_yearly": request.keep_yearly
        }

        result = borg_manager.prune_repository(
            repository_path=request.repository_path,
            passphrase=request.passphrase,
            keep_policy=keep_policy
        )

        return result

    except Exception as e:
        logger.error(f"Borg repository pruning error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/borg/compact")
async def compact_borg_repository(
    repository_path: str = Query(..., description="Repository path"),
    passphrase: str = Query(..., description="Repository passphrase"),
    current_user: Dict = Depends(require_admin)
):
    """
    Compact Borg repository to reclaim space

    **Admin only** - Frees disk space after pruning/deleting

    - **repository_path**: Borg repository path
    - **passphrase**: Repository passphrase

    This should be run after:
    - Deleting archives
    - Pruning old backups

    Compaction can take significant time for large repositories.
    """
    try:
        await audit_logger.log(
            action="borg.repository.compact",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"repository_path": repository_path}
        )

        result = borg_manager.compact_repository(
            repository_path=repository_path,
            passphrase=passphrase
        )

        return result

    except Exception as e:
        logger.error(f"Borg repository compaction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/borg/check")
async def check_borg_repository(
    repository_path: str = Query(..., description="Repository path"),
    passphrase: str = Query(..., description="Repository passphrase"),
    verify_data: bool = Query(False, description="Also verify data integrity (slower)"),
    current_user: Dict = Depends(require_admin)
):
    """
    Verify Borg repository integrity

    **Admin only** - Checks repository for corruption

    - **repository_path**: Borg repository path
    - **passphrase**: Repository passphrase
    - **verify_data**: Also verify data blocks (slow, thorough)

    Regular integrity check validates:
    - Repository structure
    - Archive metadata
    - Chunk references

    Full data verification (verify_data=true) additionally checks:
    - All data blocks
    - Checksums
    - Encryption integrity

    Warning: Full verification can take hours on large repositories.
    """
    try:
        await audit_logger.log(
            action="borg.repository.check",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "repository_path": repository_path,
                "verify_data": verify_data
            }
        )

        result = borg_manager.check_repository(
            repository_path=repository_path,
            passphrase=passphrase,
            verify_data=verify_data
        )

        return result

    except Exception as e:
        logger.error(f"Borg repository check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/borg/mount")
async def mount_borg_archive(
    request: BorgMountRequest,
    current_user: Dict = Depends(require_admin)
):
    """
    Mount Borg archive as read-only FUSE filesystem

    **Admin only** - Mounts archive for browsing

    - **archive_name**: Archive to mount (empty = all archives)
    - **mount_point**: Where to mount filesystem
    - **repository_path**: Borg repository path
    - **passphrase**: Repository passphrase

    Requires:
    - FUSE support (libfuse installed)
    - Mount point directory exists
    - User has mount permissions

    Mounted archives are read-only. Use `umount` to unmount.

    Example:
    ```bash
    # Mount specific archive
    POST /backups/borg/mount
    {
      "archive_name": "backup_20251023_120000",
      "mount_point": "/mnt/backup",
      "repository_path": "/backups/borg-repo",
      "passphrase": "..."
    }

    # Browse files
    ls /mnt/backup

    # Unmount
    borg umount /mnt/backup
    ```
    """
    try:
        await audit_logger.log(
            action="borg.archive.mount",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={
                "archive_name": request.archive_name,
                "mount_point": request.mount_point
            }
        )

        result = borg_manager.mount_archive(
            archive_name=request.archive_name,
            mount_point=request.mount_point,
            repository_path=request.repository_path,
            passphrase=request.passphrase
        )

        return result

    except Exception as e:
        logger.error(f"Borg archive mount error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/borg/umount")
async def umount_borg_archive(
    mount_point: str = Query(..., description="Mount point to unmount"),
    current_user: Dict = Depends(require_admin)
):
    """
    Unmount a mounted Borg archive

    **Admin only** - Unmounts FUSE filesystem

    - **mount_point**: Path that was mounted
    """
    try:
        await audit_logger.log(
            action="borg.archive.umount",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"mount_point": mount_point}
        )

        result = borg_manager.umount_archive(mount_point=mount_point)

        return result

    except Exception as e:
        logger.error(f"Borg archive unmount error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backups/borg/info", response_model=BorgInfo)
async def get_borg_info(
    repository_path: str = Query(..., description="Repository path"),
    passphrase: str = Query(..., description="Repository passphrase"),
    current_user: Dict = Depends(require_admin)
):
    """
    Get Borg repository information and statistics

    **Admin only** - Returns repository metadata

    - **repository_path**: Borg repository path
    - **passphrase**: Repository passphrase

    Returns:
    - Repository ID
    - Location
    - Encryption mode
    - Total chunks and size
    - Deduplication statistics
    """
    try:
        await audit_logger.log(
            action="borg.repository.info",
            result="success",
            username=current_user.get("username"),
            user_id=current_user.get("id"),
            metadata={"repository_path": repository_path}
        )

        info = borg_manager.get_info(
            repository_path=repository_path,
            passphrase=passphrase
        )

        return BorgInfo(**info)

    except Exception as e:
        logger.error(f"Borg repository info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
