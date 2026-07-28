"""
BorgBackup Integration for Ops-Center Storage Management
Provides secure, deduplicated, compressed backup functionality

BorgBackup Features:
- Strong encryption (AES-CTR-256 + HMAC-SHA256)
- Deduplication at block level
- Compression (lz4, zstd, zlib, lzma)
- Mount archives as FUSE filesystem
- Integrity verification
- Incremental backups
"""

import os
import json
import subprocess
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)


class BorgBackupManager:
    """
    Manages BorgBackup operations for secure, deduplicated backups

    Features:
    - Repository initialization with encryption
    - Archive creation with compression
    - Archive listing, extraction, deletion
    - Repository pruning and compaction
    - Integrity verification
    - FUSE mount support
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize BorgBackup manager

        Args:
            encryption_key: Key for encrypting passphrases (generates new if None)
        """
        # Generate or use provided encryption key for passphrase encryption
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            # Generate new key (in production, store this securely)
            key = Fernet.generate_key()
            self.cipher = Fernet(key)
            logger.warning("Generated new encryption key. Store this securely!")
            logger.info(f"Encryption key (base64): {key.decode()}")

        # Check if borg is installed
        self._check_borg_installed()

        # Active mount points (for cleanup)
        self.active_mounts: Dict[str, str] = {}

    def _check_borg_installed(self) -> None:
        """Check if borg binary is available"""
        try:
            result = subprocess.run(
                ["borg", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"BorgBackup version: {result.stdout.strip()}")
            else:
                raise RuntimeError("Borg binary found but not working properly")
        except FileNotFoundError:
            logger.warning(
                "BorgBackup not installed. Borg backup features will be disabled. "
                "Install with: apt-get install borgbackup"
            )
            return
        except subprocess.TimeoutExpired:
            raise RuntimeError("Borg binary is not responding")

    def _encrypt_passphrase(self, passphrase: str) -> str:
        """Encrypt a passphrase for secure storage"""
        encrypted = self.cipher.encrypt(passphrase.encode())
        return base64.b64encode(encrypted).decode()

    def _decrypt_passphrase(self, encrypted_passphrase: str) -> str:
        """Decrypt a passphrase from storage"""
        encrypted = base64.b64decode(encrypted_passphrase.encode())
        return self.cipher.decrypt(encrypted).decode()

    def _run_borg_command(
        self,
        args: List[str],
        passphrase: Optional[str] = None,
        check_returncode: bool = True,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Run a borg command with proper environment setup

        Args:
            args: Command arguments (without 'borg')
            passphrase: Repository passphrase (if encrypted)
            check_returncode: Raise exception on non-zero return code
            timeout: Command timeout in seconds

        Returns:
            Dict with stdout, stderr, returncode
        """
        env = os.environ.copy()

        # Set passphrase via environment variable (more secure than CLI)
        if passphrase:
            env["BORG_PASSPHRASE"] = passphrase

        # Disable warnings about unknown unencrypted repositories
        env["BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK"] = "yes"

        # Don't save SSH keys automatically
        env["BORG_RSH"] = "ssh -o StrictHostKeyChecking=accept-new"

        cmd = ["borg"] + args
        logger.info(f"Running borg command: {' '.join(args[:2])} ...")

        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if check_returncode and result.returncode != 0:
                logger.error(f"Borg command failed: {result.stderr}")
                raise RuntimeError(f"Borg error: {result.stderr}")

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }

        except subprocess.TimeoutExpired:
            logger.error(f"Borg command timed out after {timeout}s")
            raise RuntimeError(f"Borg command timed out after {timeout}s")
        except Exception as e:
            logger.error(f"Borg command exception: {e}")
            raise

    def initialize_repository(
        self,
        repository_path: str,
        passphrase: str,
        encryption_mode: str = "repokey-blake2"
    ) -> Dict[str, Any]:
        """
        Initialize a new Borg repository

        Args:
            repository_path: Path to repository (local or remote)
            passphrase: Repository encryption passphrase
            encryption_mode: Encryption mode:
                - 'repokey-blake2': AES-CTR-256 + BLAKE2b (recommended)
                - 'repokey': AES-CTR-256 + HMAC-SHA256
                - 'keyfile-blake2': Key stored separately
                - 'authenticated-blake2': No encryption, only auth
                - 'none': No encryption (not recommended)

        Returns:
            Dict with success status and repository info
        """
        logger.info(f"Initializing Borg repository: {repository_path}")

        try:
            # Create repository directory if local
            if not repository_path.startswith("ssh://"):
                Path(repository_path).mkdir(parents=True, exist_ok=True)

            # Initialize repository
            args = [
                "init",
                "--encryption", encryption_mode,
                repository_path
            ]

            result = self._run_borg_command(args, passphrase=passphrase)

            # Get repository info
            info = self.get_info(repository_path, passphrase)

            logger.info(f"Repository initialized successfully: {repository_path}")

            return {
                "success": True,
                "repository_path": repository_path,
                "encryption_mode": encryption_mode,
                "repository_id": info.get("repository_id"),
                "message": "Repository initialized successfully"
            }

        except Exception as e:
            logger.error(f"Failed to initialize repository: {e}")
            return {
                "success": False,
                "error": str(e),
                "repository_path": repository_path
            }

    def create_archive(
        self,
        archive_name: str,
        source_paths: List[str],
        repository_path: str,
        passphrase: str,
        compression: str = "lz4",
        exclude_patterns: Optional[List[str]] = None,
        progress: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new backup archive

        Args:
            archive_name: Name for the archive (timestamp added automatically)
            source_paths: List of paths to backup
            repository_path: Repository path
            passphrase: Repository passphrase
            compression: Compression algorithm:
                - 'lz4': Fast, low compression (default)
                - 'zstd,3': Balanced speed/compression
                - 'zstd,10': High compression
                - 'zlib,6': Standard compression
                - 'lzma,6': Maximum compression (slow)
            exclude_patterns: Glob patterns to exclude
            progress: Show progress indicator

        Returns:
            Dict with archive statistics
        """
        # Add timestamp to archive name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_archive_name = f"{archive_name}_{timestamp}"

        logger.info(f"Creating archive: {full_archive_name}")

        try:
            # Build command arguments
            args = [
                "create",
                "--stats",
                "--json",
                "--compression", compression,
                f"{repository_path}::{full_archive_name}"
            ]

            # Add progress flag
            if progress:
                args.append("--progress")

            # Add exclude patterns
            if exclude_patterns:
                for pattern in exclude_patterns:
                    args.extend(["--exclude", pattern])

            # Add source paths
            args.extend(source_paths)

            # Run backup
            result = self._run_borg_command(
                args,
                passphrase=passphrase,
                timeout=3600  # 1 hour timeout for large backups
            )

            # Parse JSON output
            stats = json.loads(result["stdout"])

            logger.info(f"Archive created: {full_archive_name}")
            logger.info(
                f"Original size: {stats['archive']['stats']['original_size'] / 1024**3:.2f} GB, "
                f"Compressed: {stats['archive']['stats']['compressed_size'] / 1024**3:.2f} GB, "
                f"Deduplicated: {stats['archive']['stats']['deduplicated_size'] / 1024**3:.2f} GB"
            )

            return {
                "success": True,
                "archive_name": full_archive_name,
                "original_size": stats["archive"]["stats"]["original_size"],
                "compressed_size": stats["archive"]["stats"]["compressed_size"],
                "deduplicated_size": stats["archive"]["stats"]["deduplicated_size"],
                "nfiles": stats["archive"]["stats"]["nfiles"],
                "compression_ratio": (
                    stats["archive"]["stats"]["compressed_size"] /
                    stats["archive"]["stats"]["original_size"]
                ) if stats["archive"]["stats"]["original_size"] > 0 else 0,
                "deduplication_ratio": (
                    stats["archive"]["stats"]["deduplicated_size"] /
                    stats["archive"]["stats"]["original_size"]
                ) if stats["archive"]["stats"]["original_size"] > 0 else 0,
                "duration": stats.get("duration", 0)
            }

        except Exception as e:
            logger.error(f"Failed to create archive: {e}")
            return {
                "success": False,
                "error": str(e),
                "archive_name": full_archive_name
            }

    def list_archives(
        self,
        repository_path: str,
        passphrase: str,
        prefix: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all archives in repository

        Args:
            repository_path: Repository path
            passphrase: Repository passphrase
            prefix: Filter archives by name prefix

        Returns:
            List of archive metadata dicts
        """
        logger.info(f"Listing archives in: {repository_path}")

        try:
            args = [
                "list",
                "--json",
                repository_path
            ]

            if prefix:
                args.extend(["--prefix", prefix])

            result = self._run_borg_command(args, passphrase=passphrase)

            data = json.loads(result["stdout"])
            archives = data.get("archives", [])

            logger.info(f"Found {len(archives)} archives")

            return [
                {
                    "name": arc["name"],
                    "archive": arc["archive"],
                    "time": arc["time"],
                    "hostname": arc.get("hostname", "unknown"),
                    "username": arc.get("username", "unknown"),
                    # Get detailed stats if available
                    "id": arc["id"]
                }
                for arc in archives
            ]

        except Exception as e:
            logger.error(f"Failed to list archives: {e}")
            raise

    def extract_archive(
        self,
        archive_name: str,
        target_path: str,
        repository_path: str,
        passphrase: str,
        paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract archive contents

        Args:
            archive_name: Name of archive to extract
            target_path: Where to extract files
            repository_path: Repository path
            passphrase: Repository passphrase
            paths: Specific paths to extract (None = all)

        Returns:
            Dict with extraction results
        """
        logger.info(f"Extracting archive: {archive_name} to {target_path}")

        try:
            # Create target directory
            Path(target_path).mkdir(parents=True, exist_ok=True)

            args = [
                "extract",
                "--progress",
                f"{repository_path}::{archive_name}"
            ]

            # Add specific paths if provided
            if paths:
                args.extend(paths)

            # Run extraction
            result = self._run_borg_command(
                args,
                passphrase=passphrase,
                timeout=3600
            )

            logger.info(f"Archive extracted successfully: {archive_name}")

            return {
                "success": True,
                "archive_name": archive_name,
                "target_path": target_path,
                "message": "Archive extracted successfully"
            }

        except Exception as e:
            logger.error(f"Failed to extract archive: {e}")
            return {
                "success": False,
                "error": str(e),
                "archive_name": archive_name
            }

    def delete_archive(
        self,
        archive_name: str,
        repository_path: str,
        passphrase: str
    ) -> Dict[str, Any]:
        """
        Delete an archive from repository

        Args:
            archive_name: Name of archive to delete
            repository_path: Repository path
            passphrase: Repository passphrase

        Returns:
            Dict with deletion results
        """
        logger.info(f"Deleting archive: {archive_name}")

        try:
            args = [
                "delete",
                "--stats",
                f"{repository_path}::{archive_name}"
            ]

            result = self._run_borg_command(args, passphrase=passphrase)

            logger.info(f"Archive deleted: {archive_name}")

            return {
                "success": True,
                "archive_name": archive_name,
                "message": "Archive deleted successfully"
            }

        except Exception as e:
            logger.error(f"Failed to delete archive: {e}")
            return {
                "success": False,
                "error": str(e),
                "archive_name": archive_name
            }

    def prune_repository(
        self,
        repository_path: str,
        passphrase: str,
        keep_policy: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Prune old archives based on retention policy

        Args:
            repository_path: Repository path
            passphrase: Repository passphrase
            keep_policy: Retention policy, e.g.:
                {
                    "keep_hourly": 24,
                    "keep_daily": 7,
                    "keep_weekly": 4,
                    "keep_monthly": 6,
                    "keep_yearly": 2
                }

        Returns:
            Dict with pruning results
        """
        logger.info(f"Pruning repository: {repository_path}")

        try:
            args = [
                "prune",
                "--stats",
                "--list",
                repository_path
            ]

            # Add retention policy
            for key, value in keep_policy.items():
                if value > 0:
                    # Convert keep_daily -> --keep-daily
                    flag = f"--{key.replace('_', '-')}"
                    args.extend([flag, str(value)])

            result = self._run_borg_command(args, passphrase=passphrase)

            logger.info(f"Repository pruned successfully")

            return {
                "success": True,
                "repository_path": repository_path,
                "keep_policy": keep_policy,
                "output": result["stderr"],  # Stats go to stderr
                "message": "Repository pruned successfully"
            }

        except Exception as e:
            logger.error(f"Failed to prune repository: {e}")
            return {
                "success": False,
                "error": str(e),
                "repository_path": repository_path
            }

    def compact_repository(
        self,
        repository_path: str,
        passphrase: str
    ) -> Dict[str, Any]:
        """
        Compact repository after pruning to reclaim space

        Args:
            repository_path: Repository path
            passphrase: Repository passphrase

        Returns:
            Dict with compaction results
        """
        logger.info(f"Compacting repository: {repository_path}")

        try:
            args = [
                "compact",
                "--progress",
                repository_path
            ]

            result = self._run_borg_command(
                args,
                passphrase=passphrase,
                timeout=1800  # 30 minutes for compaction
            )

            logger.info(f"Repository compacted successfully")

            return {
                "success": True,
                "repository_path": repository_path,
                "message": "Repository compacted successfully"
            }

        except Exception as e:
            logger.error(f"Failed to compact repository: {e}")
            return {
                "success": False,
                "error": str(e),
                "repository_path": repository_path
            }

    def check_repository(
        self,
        repository_path: str,
        passphrase: str,
        verify_data: bool = False
    ) -> Dict[str, Any]:
        """
        Verify repository integrity

        Args:
            repository_path: Repository path
            passphrase: Repository passphrase
            verify_data: Also verify data integrity (slower)

        Returns:
            Dict with verification results
        """
        logger.info(f"Checking repository: {repository_path}")

        try:
            args = [
                "check",
                "--progress",
                repository_path
            ]

            if verify_data:
                args.append("--verify-data")

            result = self._run_borg_command(
                args,
                passphrase=passphrase,
                timeout=3600
            )

            logger.info(f"Repository check completed successfully")

            return {
                "success": True,
                "repository_path": repository_path,
                "verify_data": verify_data,
                "message": "Repository integrity verified"
            }

        except Exception as e:
            logger.error(f"Repository check failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "repository_path": repository_path
            }

    def mount_archive(
        self,
        archive_name: str,
        mount_point: str,
        repository_path: str,
        passphrase: str
    ) -> Dict[str, Any]:
        """
        Mount archive as read-only FUSE filesystem

        Args:
            archive_name: Name of archive to mount (or empty for all)
            mount_point: Where to mount the filesystem
            repository_path: Repository path
            passphrase: Repository passphrase

        Returns:
            Dict with mount results
        """
        logger.info(f"Mounting archive: {archive_name} at {mount_point}")

        try:
            # Create mount point
            Path(mount_point).mkdir(parents=True, exist_ok=True)

            # Build mount command
            if archive_name:
                target = f"{repository_path}::{archive_name}"
            else:
                target = repository_path  # Mount all archives

            args = [
                "mount",
                target,
                mount_point
            ]

            # Note: Mount runs in foreground, so we need background process
            # For API usage, we'll start it in background and track PID
            env = os.environ.copy()
            env["BORG_PASSPHRASE"] = passphrase

            cmd = ["borg"] + args
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Track mount point
            self.active_mounts[mount_point] = {
                "archive_name": archive_name,
                "pid": process.pid,
                "repository_path": repository_path
            }

            logger.info(f"Archive mounted at: {mount_point} (PID: {process.pid})")

            return {
                "success": True,
                "archive_name": archive_name,
                "mount_point": mount_point,
                "pid": process.pid,
                "message": f"Archive mounted at {mount_point}"
            }

        except Exception as e:
            logger.error(f"Failed to mount archive: {e}")
            return {
                "success": False,
                "error": str(e),
                "archive_name": archive_name
            }

    def umount_archive(self, mount_point: str) -> Dict[str, Any]:
        """
        Unmount a mounted archive

        Args:
            mount_point: Mount point to unmount

        Returns:
            Dict with unmount results
        """
        logger.info(f"Unmounting: {mount_point}")

        try:
            args = ["umount", mount_point]

            result = self._run_borg_command(args, check_returncode=False)

            # Remove from tracking
            if mount_point in self.active_mounts:
                del self.active_mounts[mount_point]

            logger.info(f"Archive unmounted: {mount_point}")

            return {
                "success": True,
                "mount_point": mount_point,
                "message": "Archive unmounted successfully"
            }

        except Exception as e:
            logger.error(f"Failed to unmount archive: {e}")
            return {
                "success": False,
                "error": str(e),
                "mount_point": mount_point
            }

    def get_info(
        self,
        repository_path: str,
        passphrase: str
    ) -> Dict[str, Any]:
        """
        Get repository information and statistics

        Args:
            repository_path: Repository path
            passphrase: Repository passphrase

        Returns:
            Dict with repository info
        """
        logger.info(f"Getting repository info: {repository_path}")

        try:
            args = [
                "info",
                "--json",
                repository_path
            ]

            result = self._run_borg_command(args, passphrase=passphrase)

            data = json.loads(result["stdout"])

            # Extract repository info
            repo_info = data.get("repository", {})
            cache_info = data.get("cache", {})

            return {
                "repository_id": repo_info.get("id"),
                "location": repo_info.get("location"),
                "last_modified": repo_info.get("last_modified"),
                "encryption_mode": data.get("encryption", {}).get("mode"),
                "unique_chunks": cache_info.get("stats", {}).get("unique_chunks", 0),
                "total_chunks": cache_info.get("stats", {}).get("total_chunks", 0),
                "total_size": cache_info.get("stats", {}).get("total_size", 0),
                "unique_size": cache_info.get("stats", {}).get("unique_csize", 0),
                "deduplication_ratio": (
                    cache_info.get("stats", {}).get("total_size", 0) /
                    cache_info.get("stats", {}).get("unique_csize", 1)
                )
            }

        except Exception as e:
            logger.error(f"Failed to get repository info: {e}")
            raise
