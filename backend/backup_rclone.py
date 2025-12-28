"""
Rclone Cloud Sync Manager for Ops-Center
Provides universal cloud sync across 40+ providers using rclone
Supports sync, copy, move, mount, and bidirectional synchronization
"""

import os
import json
import logging
import subprocess
import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RcloneProvider(Enum):
    """Supported cloud providers"""
    S3 = "s3"
    GOOGLE_DRIVE = "drive"
    DROPBOX = "dropbox"
    ONEDRIVE = "onedrive"
    BACKBLAZE_B2 = "b2"
    WASABI = "s3"
    GOOGLE_CLOUD_STORAGE = "google cloud storage"
    AZURE_BLOB = "azureblob"
    SFTP = "sftp"
    FTP = "ftp"
    WEBDAV = "webdav"
    BOX = "box"
    MEGA = "mega"
    PCLOUD = "pcloud"
    SWIFT = "swift"
    YANDEX = "yandex"
    HTTP = "http"
    HUBIC = "hubic"
    JOTTACLOUD = "jottacloud"
    KOOFR = "koofr"
    MAILRU = "mailru"
    OPENDRIVE = "opendrive"
    QINGSTOR = "qingstor"
    UNION = "union"
    SEAFILE = "seafile"
    STORJ = "storj"
    SUGARSYNC = "sugarsync"
    UPTOBOX = "uptobox"
    ZOHO = "zoho"


@dataclass
class RcloneRemote:
    """Represents a configured rclone remote"""
    name: str
    type: str
    configured: bool
    encrypted: bool = False


@dataclass
class RcloneFile:
    """Represents a file/folder from rclone"""
    path: str
    name: str
    size: int
    mime_type: str
    mod_time: str
    is_dir: bool


@dataclass
class RcloneSyncStats:
    """Statistics from rclone operation"""
    bytes_transferred: int
    files_transferred: int
    files_checked: int
    files_deleted: int
    errors: int
    elapsed_time: float
    transfer_rate_mbps: float


class RcloneSyncManager:
    """Manages rclone cloud synchronization operations"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize rclone manager

        Args:
            config_dir: Custom config directory (default: ~/.config/rclone)
        """
        self.config_dir = config_dir or os.path.expanduser("~/.config/rclone")
        self.config_file = os.path.join(self.config_dir, "rclone.conf")
        self.rclone_available = False
        self._ensure_rclone_installed()
        if self.rclone_available:
            self._ensure_config_dir()

    def _ensure_rclone_installed(self):
        """Check if rclone is installed"""
        try:
            result = subprocess.run(
                ["rclone", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                logger.warning("rclone is installed but not working correctly")
                return

            logger.info(f"rclone version: {result.stdout.split()[1]}")
            self.rclone_available = True
        except FileNotFoundError:
            logger.warning(
                "rclone is not installed. Rclone backup features will be disabled. "
                "Install with: curl https://rclone.org/install.sh | sudo bash"
            )
        except subprocess.TimeoutExpired:
            logger.warning("rclone command timed out. Rclone backup features will be disabled.")

    def _ensure_config_dir(self):
        """Ensure rclone config directory exists"""
        os.makedirs(self.config_dir, exist_ok=True)

        # Create empty config file if it doesn't exist
        if not os.path.exists(self.config_file):
            Path(self.config_file).touch(mode=0o600)
            logger.info(f"Created rclone config file: {self.config_file}")

    async def _run_rclone(
        self,
        args: List[str],
        timeout: int = 300,
        capture_json: bool = False
    ) -> Tuple[int, str, str]:
        """
        Run rclone command asynchronously

        Args:
            args: Command arguments
            timeout: Command timeout in seconds
            capture_json: Parse output as JSON

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = ["rclone"] + args + [f"--config={self.config_file}"]

        if capture_json and "--json" not in args:
            cmd.append("--json")

        logger.debug(f"Running rclone command: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                return (
                    process.returncode,
                    stdout.decode('utf-8'),
                    stderr.decode('utf-8')
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise RuntimeError(f"rclone command timed out after {timeout} seconds")

        except Exception as e:
            logger.error(f"Error running rclone command: {e}")
            raise

    def configure_remote(
        self,
        remote_name: str,
        provider: str,
        config_params: Dict[str, str],
        encrypt: bool = False
    ) -> bool:
        """
        Configure a new rclone remote

        Args:
            remote_name: Name for the remote
            provider: Provider type (s3, drive, dropbox, etc.)
            config_params: Provider-specific configuration
            encrypt: Whether to create encrypted remote wrapper

        Returns:
            True if successful
        """
        try:
            # Build config content
            config_lines = [f"[{remote_name}]", f"type = {provider}"]

            for key, value in config_params.items():
                config_lines.append(f"{key} = {value}")

            # Read existing config
            existing_config = ""
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    existing_config = f.read()

            # Remove existing remote with same name
            lines = existing_config.split('\n')
            filtered_lines = []
            skip = False

            for line in lines:
                if line.strip().startswith(f"[{remote_name}]"):
                    skip = True
                elif line.strip().startswith('[') and skip:
                    skip = False

                if not skip:
                    filtered_lines.append(line)

            # Append new config
            new_config = '\n'.join(filtered_lines).strip() + '\n\n' + '\n'.join(config_lines) + '\n'

            # Write config file
            with open(self.config_file, 'w') as f:
                f.write(new_config)

            os.chmod(self.config_file, 0o600)

            logger.info(f"Configured rclone remote: {remote_name} ({provider})")

            # Create encrypted wrapper if requested
            if encrypt:
                encrypted_name = f"{remote_name}_encrypted"
                self._create_crypt_remote(remote_name, encrypted_name)

            return True

        except Exception as e:
            logger.error(f"Error configuring rclone remote: {e}")
            raise

    def _create_crypt_remote(self, base_remote: str, crypt_name: str) -> bool:
        """Create encrypted remote wrapper using rclone crypt"""
        try:
            # Generate encryption password
            password = hashlib.sha256(os.urandom(32)).hexdigest()
            password2 = hashlib.sha256(os.urandom(32)).hexdigest()

            crypt_config = [
                f"[{crypt_name}]",
                "type = crypt",
                f"remote = {base_remote}:",
                f"password = {password}",
                f"password2 = {password2}",
                "filename_encryption = standard",
                "directory_name_encryption = true"
            ]

            # Append to config
            with open(self.config_file, 'a') as f:
                f.write('\n' + '\n'.join(crypt_config) + '\n')

            logger.info(f"Created encrypted remote: {crypt_name}")
            return True

        except Exception as e:
            logger.error(f"Error creating crypt remote: {e}")
            raise

    async def list_remotes(self) -> List[RcloneRemote]:
        """
        List all configured remotes

        Returns:
            List of RcloneRemote objects
        """
        try:
            returncode, stdout, stderr = await self._run_rclone(["listremotes"])

            if returncode != 0:
                raise RuntimeError(f"Failed to list remotes: {stderr}")

            remotes = []
            for line in stdout.strip().split('\n'):
                if line:
                    remote_name = line.rstrip(':')
                    remote_type = await self._get_remote_type(remote_name)
                    encrypted = remote_type == "crypt"

                    remotes.append(RcloneRemote(
                        name=remote_name,
                        type=remote_type,
                        configured=True,
                        encrypted=encrypted
                    ))

            return remotes

        except Exception as e:
            logger.error(f"Error listing remotes: {e}")
            raise

    async def _get_remote_type(self, remote_name: str) -> str:
        """Get the type of a configured remote"""
        try:
            # Read config file
            with open(self.config_file, 'r') as f:
                lines = f.readlines()

            # Find remote section
            in_section = False
            for line in lines:
                if line.strip() == f"[{remote_name}]":
                    in_section = True
                elif in_section and line.strip().startswith("type = "):
                    return line.split("=")[1].strip()
                elif in_section and line.strip().startswith('['):
                    break

            return "unknown"

        except Exception as e:
            logger.error(f"Error getting remote type: {e}")
            return "unknown"

    async def sync(
        self,
        source: str,
        destination: str,
        dry_run: bool = False,
        checksum: bool = False,
        bwlimit: Optional[str] = None,
        exclude: Optional[List[str]] = None,
        delete_excluded: bool = False,
        progress: bool = True
    ) -> RcloneSyncStats:
        """
        Sync source to destination (makes dest identical to source)

        Args:
            source: Source path (local or remote:path)
            destination: Destination path (local or remote:path)
            dry_run: Preview changes without executing
            checksum: Use checksums instead of mod-time & size
            bwlimit: Bandwidth limit (e.g., "10M")
            exclude: List of exclude patterns
            delete_excluded: Delete excluded files on destination
            progress: Show progress

        Returns:
            RcloneSyncStats with transfer statistics
        """
        args = ["sync", source, destination, "--stats=1s"]

        if dry_run:
            args.append("--dry-run")

        if checksum:
            args.append("--checksum")

        if bwlimit:
            args.append(f"--bwlimit={bwlimit}")

        if exclude:
            for pattern in exclude:
                args.extend(["--exclude", pattern])

        if delete_excluded:
            args.append("--delete-excluded")

        if progress:
            args.append("--progress")

        logger.info(f"Syncing: {source} → {destination}")

        try:
            start_time = datetime.now()
            returncode, stdout, stderr = await self._run_rclone(args, timeout=3600)
            end_time = datetime.now()

            elapsed = (end_time - start_time).total_seconds()

            if returncode != 0:
                logger.error(f"Sync failed: {stderr}")
                raise RuntimeError(f"Sync failed: {stderr}")

            # Parse stats from stderr
            stats = self._parse_stats(stderr, elapsed)

            logger.info(
                f"Sync completed: {stats.files_transferred} files, "
                f"{stats.bytes_transferred / 1024 / 1024:.2f} MB in {elapsed:.1f}s"
            )

            return stats

        except Exception as e:
            logger.error(f"Error during sync: {e}")
            raise

    async def copy(
        self,
        source: str,
        destination: str,
        dry_run: bool = False,
        checksum: bool = False,
        bwlimit: Optional[str] = None,
        exclude: Optional[List[str]] = None
    ) -> RcloneSyncStats:
        """
        Copy files from source to destination (doesn't delete)

        Args:
            source: Source path
            destination: Destination path
            dry_run: Preview changes
            checksum: Use checksums
            bwlimit: Bandwidth limit
            exclude: Exclude patterns

        Returns:
            RcloneSyncStats
        """
        args = ["copy", source, destination, "--stats=1s"]

        if dry_run:
            args.append("--dry-run")

        if checksum:
            args.append("--checksum")

        if bwlimit:
            args.append(f"--bwlimit={bwlimit}")

        if exclude:
            for pattern in exclude:
                args.extend(["--exclude", pattern])

        args.append("--progress")

        logger.info(f"Copying: {source} → {destination}")

        try:
            start_time = datetime.now()
            returncode, stdout, stderr = await self._run_rclone(args, timeout=3600)
            end_time = datetime.now()

            elapsed = (end_time - start_time).total_seconds()

            if returncode != 0:
                raise RuntimeError(f"Copy failed: {stderr}")

            stats = self._parse_stats(stderr, elapsed)
            logger.info(f"Copy completed: {stats.files_transferred} files")

            return stats

        except Exception as e:
            logger.error(f"Error during copy: {e}")
            raise

    async def move(
        self,
        source: str,
        destination: str,
        dry_run: bool = False,
        delete_empty_src_dirs: bool = True
    ) -> RcloneSyncStats:
        """
        Move files from source to destination (deletes from source)

        Args:
            source: Source path
            destination: Destination path
            dry_run: Preview changes
            delete_empty_src_dirs: Delete empty source directories

        Returns:
            RcloneSyncStats
        """
        args = ["move", source, destination, "--stats=1s", "--progress"]

        if dry_run:
            args.append("--dry-run")

        if delete_empty_src_dirs:
            args.append("--delete-empty-src-dirs")

        logger.info(f"Moving: {source} → {destination}")

        try:
            start_time = datetime.now()
            returncode, stdout, stderr = await self._run_rclone(args, timeout=3600)
            end_time = datetime.now()

            elapsed = (end_time - start_time).total_seconds()

            if returncode != 0:
                raise RuntimeError(f"Move failed: {stderr}")

            stats = self._parse_stats(stderr, elapsed)
            logger.info(f"Move completed: {stats.files_transferred} files")

            return stats

        except Exception as e:
            logger.error(f"Error during move: {e}")
            raise

    async def delete(self, remote_path: str, dry_run: bool = False) -> int:
        """
        Delete files at remote path

        Args:
            remote_path: Path to delete (remote:path)
            dry_run: Preview deletions

        Returns:
            Number of files deleted
        """
        args = ["delete", remote_path]

        if dry_run:
            args.append("--dry-run")

        logger.info(f"Deleting: {remote_path}")

        try:
            returncode, stdout, stderr = await self._run_rclone(args)

            if returncode != 0:
                raise RuntimeError(f"Delete failed: {stderr}")

            # Count deletions from stderr
            deleted_count = stderr.count("Deleted")
            logger.info(f"Deleted {deleted_count} files")

            return deleted_count

        except Exception as e:
            logger.error(f"Error during delete: {e}")
            raise

    async def list_files(
        self,
        remote_path: str,
        recursive: bool = True,
        max_depth: Optional[int] = None
    ) -> List[RcloneFile]:
        """
        List files at remote path

        Args:
            remote_path: Path to list (remote:path)
            recursive: List recursively
            max_depth: Maximum directory depth

        Returns:
            List of RcloneFile objects
        """
        args = ["lsjson", remote_path]

        if recursive:
            args.append("--recursive")

        if max_depth:
            args.append(f"--max-depth={max_depth}")

        try:
            returncode, stdout, stderr = await self._run_rclone(args, capture_json=True)

            if returncode != 0:
                raise RuntimeError(f"List failed: {stderr}")

            # Parse JSON output
            files_data = json.loads(stdout) if stdout.strip() else []

            files = []
            for item in files_data:
                files.append(RcloneFile(
                    path=item.get("Path", ""),
                    name=item.get("Name", ""),
                    size=item.get("Size", 0),
                    mime_type=item.get("MimeType", ""),
                    mod_time=item.get("ModTime", ""),
                    is_dir=item.get("IsDir", False)
                ))

            return files

        except Exception as e:
            logger.error(f"Error listing files: {e}")
            raise

    async def get_size(self, remote_path: str) -> int:
        """
        Get total size of remote path in bytes

        Args:
            remote_path: Path to measure (remote:path)

        Returns:
            Size in bytes
        """
        args = ["size", remote_path, "--json"]

        try:
            returncode, stdout, stderr = await self._run_rclone(args, capture_json=True)

            if returncode != 0:
                raise RuntimeError(f"Size check failed: {stderr}")

            data = json.loads(stdout)
            return data.get("bytes", 0)

        except Exception as e:
            logger.error(f"Error getting size: {e}")
            raise

    async def check_connection(self, remote_name: str) -> Dict[str, Any]:
        """
        Test connection to remote

        Args:
            remote_name: Name of remote to test

        Returns:
            Dict with connection status
        """
        try:
            # Try to list root directory
            returncode, stdout, stderr = await self._run_rclone(
                ["lsd", f"{remote_name}:"],
                timeout=30
            )

            if returncode == 0:
                return {
                    "connected": True,
                    "message": "Connection successful",
                    "remote": remote_name
                }
            else:
                return {
                    "connected": False,
                    "message": f"Connection failed: {stderr}",
                    "remote": remote_name
                }

        except Exception as e:
            return {
                "connected": False,
                "message": f"Connection error: {str(e)}",
                "remote": remote_name
            }

    def get_providers(self) -> List[Dict[str, str]]:
        """
        Get list of supported cloud providers

        Returns:
            List of provider information
        """
        return [
            {"name": "Amazon S3", "prefix": "s3", "description": "Amazon S3 and S3-compatible storage"},
            {"name": "Google Drive", "prefix": "drive", "description": "Google Drive"},
            {"name": "Dropbox", "prefix": "dropbox", "description": "Dropbox"},
            {"name": "Microsoft OneDrive", "prefix": "onedrive", "description": "Microsoft OneDrive"},
            {"name": "Backblaze B2", "prefix": "b2", "description": "Backblaze B2"},
            {"name": "Wasabi", "prefix": "s3", "description": "Wasabi (S3-compatible)"},
            {"name": "Google Cloud Storage", "prefix": "google cloud storage", "description": "Google Cloud Storage"},
            {"name": "Azure Blob Storage", "prefix": "azureblob", "description": "Microsoft Azure Blob Storage"},
            {"name": "SFTP", "prefix": "sftp", "description": "SSH/SFTP"},
            {"name": "FTP", "prefix": "ftp", "description": "FTP"},
            {"name": "WebDAV", "prefix": "webdav", "description": "WebDAV"},
            {"name": "Box", "prefix": "box", "description": "Box.com"},
            {"name": "Mega", "prefix": "mega", "description": "Mega.nz"},
            {"name": "pCloud", "prefix": "pcloud", "description": "pCloud"},
            {"name": "OpenStack Swift", "prefix": "swift", "description": "OpenStack Swift"},
            {"name": "Yandex Disk", "prefix": "yandex", "description": "Yandex Disk"},
            {"name": "HTTP", "prefix": "http", "description": "HTTP/HTTPS server"},
            {"name": "hubiC", "prefix": "hubic", "description": "hubiC"},
            {"name": "Jottacloud", "prefix": "jottacloud", "description": "Jottacloud"},
            {"name": "Koofr", "prefix": "koofr", "description": "Koofr"},
            {"name": "Mail.ru Cloud", "prefix": "mailru", "description": "Mail.ru Cloud"},
            {"name": "OpenDrive", "prefix": "opendrive", "description": "OpenDrive"},
            {"name": "QingStor", "prefix": "qingstor", "description": "QingCloud QingStor"},
            {"name": "Union", "prefix": "union", "description": "Union of remotes"},
            {"name": "Seafile", "prefix": "seafile", "description": "Seafile"},
            {"name": "Storj", "prefix": "storj", "description": "Storj Decentralized Cloud Storage"},
            {"name": "SugarSync", "prefix": "sugarsync", "description": "SugarSync"},
            {"name": "Uptobox", "prefix": "uptobox", "description": "Uptobox"},
            {"name": "Zoho WorkDrive", "prefix": "zoho", "description": "Zoho WorkDrive"},
            {"name": "Citrix ShareFile", "prefix": "sharefile", "description": "Citrix ShareFile"},
            {"name": "Alibaba Cloud (Aliyun) OSS", "prefix": "oss", "description": "Alibaba Cloud Object Storage"},
            {"name": "DigitalOcean Spaces", "prefix": "s3", "description": "DigitalOcean Spaces (S3-compatible)"},
            {"name": "Dreamhost", "prefix": "s3", "description": "Dreamhost Object Storage (S3-compatible)"},
            {"name": "IBM COS S3", "prefix": "s3", "description": "IBM Cloud Object Storage (S3-compatible)"},
            {"name": "Minio", "prefix": "s3", "description": "Minio (S3-compatible)"},
            {"name": "Scaleway", "prefix": "s3", "description": "Scaleway Object Storage (S3-compatible)"},
            {"name": "StackPath", "prefix": "s3", "description": "StackPath Object Storage (S3-compatible)"},
            {"name": "Tencent COS", "prefix": "s3", "description": "Tencent Cloud Object Storage (S3-compatible)"},
            {"name": "Linode Object Storage", "prefix": "s3", "description": "Linode Object Storage (S3-compatible)"},
            {"name": "Vultr Object Storage", "prefix": "s3", "description": "Vultr Object Storage (S3-compatible)"},
        ]

    async def mount_remote(
        self,
        remote_path: str,
        mount_point: str,
        read_only: bool = False,
        allow_other: bool = False
    ) -> bool:
        """
        Mount remote as local filesystem (requires FUSE)

        Args:
            remote_path: Remote path to mount (remote:path)
            mount_point: Local mount point
            read_only: Mount read-only
            allow_other: Allow other users to access

        Returns:
            True if mounted successfully
        """
        # Create mount point if it doesn't exist
        os.makedirs(mount_point, exist_ok=True)

        args = ["mount", remote_path, mount_point, "--daemon"]

        if read_only:
            args.append("--read-only")

        if allow_other:
            args.append("--allow-other")

        logger.info(f"Mounting {remote_path} to {mount_point}")

        try:
            returncode, stdout, stderr = await self._run_rclone(args, timeout=30)

            if returncode != 0:
                raise RuntimeError(f"Mount failed: {stderr}")

            logger.info(f"Successfully mounted {remote_path}")
            return True

        except Exception as e:
            logger.error(f"Error mounting remote: {e}")
            raise

    def _parse_stats(self, stderr: str, elapsed: float) -> RcloneSyncStats:
        """Parse rclone statistics from stderr output"""
        try:
            bytes_transferred = 0
            files_transferred = 0
            files_checked = 0
            files_deleted = 0
            errors = 0

            for line in stderr.split('\n'):
                if "Transferred:" in line and "Bytes" in line:
                    # Parse: "Transferred:   1.234 MBytes (100.5 kBytes/s)"
                    parts = line.split()
                    if len(parts) >= 2:
                        size_str = parts[1]
                        # Convert to bytes
                        if "kBytes" in line or "kB" in line:
                            bytes_transferred = int(float(size_str) * 1024)
                        elif "MBytes" in line or "MB" in line:
                            bytes_transferred = int(float(size_str) * 1024 * 1024)
                        elif "GBytes" in line or "GB" in line:
                            bytes_transferred = int(float(size_str) * 1024 * 1024 * 1024)

                elif "Transferred:" in line and "files" in line:
                    # Parse: "Transferred:   5 / 10, 50%"
                    parts = line.split()
                    if len(parts) >= 2:
                        files_transferred = int(parts[1])

                elif "Checks:" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        files_checked = int(parts[1])

                elif "Deleted:" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        files_deleted = int(parts[1])

                elif "Errors:" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        errors = int(parts[1])

            # Calculate transfer rate
            transfer_rate_mbps = 0
            if elapsed > 0:
                transfer_rate_mbps = (bytes_transferred / 1024 / 1024) / elapsed

            return RcloneSyncStats(
                bytes_transferred=bytes_transferred,
                files_transferred=files_transferred,
                files_checked=files_checked,
                files_deleted=files_deleted,
                errors=errors,
                elapsed_time=elapsed,
                transfer_rate_mbps=transfer_rate_mbps
            )

        except Exception as e:
            logger.error(f"Error parsing stats: {e}")
            return RcloneSyncStats(
                bytes_transferred=0,
                files_transferred=0,
                files_checked=0,
                files_deleted=0,
                errors=0,
                elapsed_time=elapsed,
                transfer_rate_mbps=0
            )


# Create singleton instance
rclone_manager = RcloneSyncManager()
