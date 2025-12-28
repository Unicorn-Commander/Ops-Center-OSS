"""
Restic Backup Integration for Ops-Center
Open-source backup tool with encryption, deduplication, and incremental backups
"""

import os
import json
import logging
import subprocess
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path
from cryptography.fernet import Fernet
import base64
import hashlib

from audit_logger import audit_logger

logger = logging.getLogger(__name__)


class ResticBackupManager:
    """Manages Restic backup operations with encryption and deduplication"""

    def __init__(self):
        self.restic_binary = os.getenv("RESTIC_BINARY", "restic")
        self.cache_dir = Path(os.getenv("RESTIC_CACHE_DIR", "/tmp/restic-cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Password encryption key (stored in environment or generated)
        encryption_key = os.getenv("RESTIC_ENCRYPTION_KEY")
        if not encryption_key:
            # Generate new key and log warning
            encryption_key = Fernet.generate_key().decode()
            logger.warning("RESTIC_ENCRYPTION_KEY not set - generated temporary key (will not persist)")

        self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

        # Verify restic is installed
        self._verify_restic_installed()

        logger.info("Restic backup manager initialized")

    def _verify_restic_installed(self) -> bool:
        """Verify Restic binary is installed and accessible"""
        try:
            result = subprocess.run(
                [self.restic_binary, "version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"Restic installed: {version}")
                return True
            else:
                logger.error("Restic binary not working correctly")
                return False

        except FileNotFoundError:
            logger.error(f"Restic binary not found: {self.restic_binary}")
            logger.error("Install with: apt-get install restic")
            return False
        except Exception as e:
            logger.error(f"Error verifying Restic: {e}")
            return False

    def _encrypt_password(self, password: str) -> str:
        """Encrypt repository password using Fernet"""
        try:
            encrypted = self.cipher.encrypt(password.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Password encryption failed: {e}")
            raise

    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt repository password using Fernet"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_password.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Password decryption failed: {e}")
            raise

    async def _run_restic_command(
        self,
        command: List[str],
        repo_path: str,
        password: str,
        json_output: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Run Restic command with proper environment and error handling

        Args:
            command: Restic command arguments
            repo_path: Repository path
            password: Repository password (will be decrypted if encrypted)
            json_output: Whether to request JSON output
            progress_callback: Optional callback for progress updates

        Returns:
            Dict with command result (parsed JSON or raw output)
        """
        try:
            # Decrypt password if it appears to be encrypted (base64)
            try:
                decrypted_password = self._decrypt_password(password)
            except:
                # If decryption fails, assume it's already plaintext
                decrypted_password = password

            # Build full command
            full_command = [self.restic_binary] + command

            # Add JSON output flag if requested
            if json_output and "--json" not in full_command:
                full_command.append("--json")

            # Set up environment with password
            env = os.environ.copy()
            env["RESTIC_REPOSITORY"] = repo_path
            env["RESTIC_PASSWORD"] = decrypted_password
            env["RESTIC_CACHE_DIR"] = str(self.cache_dir)

            logger.debug(f"Running Restic command: {' '.join(command[:2])}...")

            # Run command
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            stdout_lines = []
            stderr_lines = []

            # Read output line by line for progress tracking
            async def read_stream(stream, lines, is_stderr=False):
                while True:
                    line = await stream.readline()
                    if not line:
                        break

                    line_str = line.decode().strip()
                    lines.append(line_str)

                    # Call progress callback for stdout
                    if not is_stderr and progress_callback and line_str:
                        try:
                            progress_callback(line_str)
                        except Exception as e:
                            logger.warning(f"Progress callback error: {e}")

            # Read both streams concurrently
            await asyncio.gather(
                read_stream(process.stdout, stdout_lines, False),
                read_stream(process.stderr, stderr_lines, True)
            )

            # Wait for process to complete
            returncode = await process.wait()

            # Parse output
            stdout_text = "\n".join(stdout_lines)
            stderr_text = "\n".join(stderr_lines)

            if returncode != 0:
                error_msg = stderr_text or stdout_text or "Unknown error"
                logger.error(f"Restic command failed: {error_msg}")
                raise RuntimeError(f"Restic command failed: {error_msg}")

            # Try to parse JSON output
            if json_output and stdout_text:
                try:
                    # Restic sometimes outputs multiple JSON objects (one per line)
                    json_lines = [line for line in stdout_lines if line.strip().startswith("{")]
                    if json_lines:
                        # Return last JSON object (usually the summary)
                        return json.loads(json_lines[-1])
                    else:
                        return {"output": stdout_text, "stderr": stderr_text}
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Restic JSON output")
                    return {"output": stdout_text, "stderr": stderr_text}

            return {
                "success": True,
                "output": stdout_text,
                "stderr": stderr_text
            }

        except Exception as e:
            logger.error(f"Restic command execution error: {e}")
            raise

    async def initialize_repository(
        self,
        repo_path: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Initialize a new Restic repository

        Args:
            repo_path: Repository location (local path or remote URL)
            password: Repository password for encryption

        Returns:
            Dict with initialization result
        """
        try:
            logger.info(f"Initializing Restic repository at: {repo_path}")

            # Encrypt password for storage
            encrypted_password = self._encrypt_password(password)

            # Initialize repository
            result = await self._run_restic_command(
                ["init"],
                repo_path,
                password,
                json_output=False
            )

            # Log to audit trail
            await audit_logger.log(
                action="restic.repository.init",
                result="success",
                metadata={
                    "repo_path": repo_path,
                    "encrypted_password": encrypted_password[:20] + "..."  # Log partial for verification
                }
            )

            return {
                "success": True,
                "repo_path": repo_path,
                "encrypted_password": encrypted_password,
                "message": "Repository initialized successfully"
            }

        except Exception as e:
            logger.error(f"Repository initialization failed: {e}")
            await audit_logger.log(
                action="restic.repository.init",
                result="error",
                metadata={"error": str(e), "repo_path": repo_path}
            )
            raise

    async def backup(
        self,
        source_paths: List[str],
        repo_path: str,
        password: str,
        tags: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Create a backup snapshot

        Args:
            source_paths: List of paths to backup
            repo_path: Repository path
            password: Repository password
            tags: Optional tags for snapshot
            exclude_patterns: File patterns to exclude
            progress_callback: Optional callback for progress updates

        Returns:
            Dict with backup result (snapshot ID, stats, etc.)
        """
        try:
            logger.info(f"Creating Restic backup of {len(source_paths)} path(s)")

            # Build backup command
            command = ["backup"] + source_paths

            # Add tags
            if tags:
                for tag in tags:
                    command.extend(["--tag", tag])

            # Add exclude patterns
            if exclude_patterns:
                for pattern in exclude_patterns:
                    command.extend(["--exclude", pattern])

            # Add verbose flag for progress
            command.append("--verbose")

            # Run backup
            result = await self._run_restic_command(
                command,
                repo_path,
                password,
                json_output=True,
                progress_callback=progress_callback
            )

            # Extract snapshot information
            snapshot_id = result.get("snapshot_id", "unknown")
            files_new = result.get("files_new", 0)
            files_changed = result.get("files_changed", 0)
            files_unmodified = result.get("files_unmodified", 0)
            data_added = result.get("data_added", 0)
            total_files = result.get("total_files_processed", 0)
            total_bytes = result.get("total_bytes_processed", 0)

            # Log to audit trail
            await audit_logger.log(
                action="restic.backup.create",
                result="success",
                metadata={
                    "snapshot_id": snapshot_id,
                    "source_paths": source_paths,
                    "tags": tags,
                    "files_new": files_new,
                    "files_changed": files_changed,
                    "data_added": data_added
                }
            )

            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "files_new": files_new,
                "files_changed": files_changed,
                "files_unmodified": files_unmodified,
                "total_files": total_files,
                "data_added": data_added,
                "total_bytes": total_bytes,
                "message": f"Backup completed: {snapshot_id}"
            }

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            await audit_logger.log(
                action="restic.backup.create",
                result="error",
                metadata={"error": str(e), "source_paths": source_paths}
            )
            raise

    async def list_snapshots(
        self,
        repo_path: str,
        password: str,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List all snapshots in repository

        Args:
            repo_path: Repository path
            password: Repository password
            tags: Optional filter by tags

        Returns:
            List of snapshot dictionaries
        """
        try:
            # Build snapshots command
            command = ["snapshots"]

            # Add tag filters
            if tags:
                for tag in tags:
                    command.extend(["--tag", tag])

            # Run command
            result = await self._run_restic_command(
                command,
                repo_path,
                password,
                json_output=True
            )

            # Parse snapshots
            snapshots = result if isinstance(result, list) else result.get("snapshots", [])

            # Convert to simplified format
            snapshot_list = []
            for snapshot in snapshots:
                snapshot_list.append({
                    "id": snapshot.get("id", snapshot.get("short_id", "unknown")),
                    "short_id": snapshot.get("short_id", snapshot.get("id", "unknown")[:8]),
                    "time": snapshot.get("time"),
                    "hostname": snapshot.get("hostname"),
                    "username": snapshot.get("username"),
                    "paths": snapshot.get("paths", []),
                    "tags": snapshot.get("tags", []),
                    "tree": snapshot.get("tree"),
                })

            logger.info(f"Listed {len(snapshot_list)} snapshots")

            return snapshot_list

        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}")
            raise

    async def restore(
        self,
        snapshot_id: str,
        target_path: str,
        repo_path: str,
        password: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Restore a snapshot to target path

        Args:
            snapshot_id: Snapshot ID to restore
            target_path: Where to restore files
            repo_path: Repository path
            password: Repository password
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            progress_callback: Optional callback for progress updates

        Returns:
            Dict with restore result
        """
        try:
            logger.info(f"Restoring snapshot {snapshot_id} to {target_path}")

            # Create target directory
            Path(target_path).mkdir(parents=True, exist_ok=True)

            # Build restore command
            command = ["restore", snapshot_id, "--target", target_path]

            # Add include patterns
            if include_patterns:
                for pattern in include_patterns:
                    command.extend(["--include", pattern])

            # Add exclude patterns
            if exclude_patterns:
                for pattern in exclude_patterns:
                    command.extend(["--exclude", pattern])

            # Add verbose flag
            command.append("--verbose")

            # Run restore
            result = await self._run_restic_command(
                command,
                repo_path,
                password,
                json_output=False,
                progress_callback=progress_callback
            )

            # Log to audit trail
            await audit_logger.log(
                action="restic.snapshot.restore",
                result="success",
                metadata={
                    "snapshot_id": snapshot_id,
                    "target_path": target_path
                }
            )

            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "target_path": target_path,
                "message": "Snapshot restored successfully"
            }

        except Exception as e:
            logger.error(f"Snapshot restore failed: {e}")
            await audit_logger.log(
                action="restic.snapshot.restore",
                result="error",
                metadata={"error": str(e), "snapshot_id": snapshot_id}
            )
            raise

    async def prune(
        self,
        repo_path: str,
        password: str,
        keep_policy: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Remove old snapshots and free storage space

        Args:
            repo_path: Repository path
            password: Repository password
            keep_policy: Retention policy (e.g., {"daily": 7, "weekly": 4, "monthly": 6})

        Returns:
            Dict with prune result
        """
        try:
            logger.info("Pruning Restic repository")

            # Default keep policy
            if not keep_policy:
                keep_policy = {
                    "daily": 7,
                    "weekly": 4,
                    "monthly": 6,
                    "yearly": 2
                }

            # Build prune command
            command = ["forget", "--prune"]

            # Add keep policies
            for period, count in keep_policy.items():
                command.append(f"--keep-{period}={count}")

            # Run prune
            result = await self._run_restic_command(
                command,
                repo_path,
                password,
                json_output=False
            )

            # Log to audit trail
            await audit_logger.log(
                action="restic.repository.prune",
                result="success",
                metadata={"keep_policy": keep_policy}
            )

            return {
                "success": True,
                "keep_policy": keep_policy,
                "message": "Repository pruned successfully"
            }

        except Exception as e:
            logger.error(f"Repository prune failed: {e}")
            await audit_logger.log(
                action="restic.repository.prune",
                result="error",
                metadata={"error": str(e)}
            )
            raise

    async def check_integrity(
        self,
        repo_path: str,
        password: str,
        read_data: bool = False
    ) -> Dict[str, Any]:
        """
        Verify repository integrity

        Args:
            repo_path: Repository path
            password: Repository password
            read_data: Whether to read and verify all data (slower but thorough)

        Returns:
            Dict with integrity check result
        """
        try:
            logger.info("Checking Restic repository integrity")

            # Build check command
            command = ["check"]

            # Add read-data flag for thorough check
            if read_data:
                command.append("--read-data")

            # Run check
            result = await self._run_restic_command(
                command,
                repo_path,
                password,
                json_output=False
            )

            # Check output for errors
            output = result.get("output", "")
            errors_found = "error" in output.lower()

            # Log to audit trail
            await audit_logger.log(
                action="restic.repository.check",
                result="success" if not errors_found else "warning",
                metadata={"read_data": read_data, "errors_found": errors_found}
            )

            return {
                "success": not errors_found,
                "integrity_ok": not errors_found,
                "read_data": read_data,
                "output": output,
                "message": "Integrity check completed" if not errors_found else "Errors found during check"
            }

        except Exception as e:
            logger.error(f"Integrity check failed: {e}")
            await audit_logger.log(
                action="restic.repository.check",
                result="error",
                metadata={"error": str(e)}
            )
            raise

    async def get_stats(
        self,
        repo_path: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Get repository statistics

        Args:
            repo_path: Repository path
            password: Repository password

        Returns:
            Dict with repository statistics
        """
        try:
            # Get stats using 'stats' command
            result = await self._run_restic_command(
                ["stats", "--mode", "raw-data"],
                repo_path,
                password,
                json_output=True
            )

            # Extract statistics
            total_size = result.get("total_size", 0)
            total_file_count = result.get("total_file_count", 0)

            # Get snapshot count
            snapshots = await self.list_snapshots(repo_path, password)
            snapshots_count = len(snapshots)

            # Calculate deduplication ratio (estimate)
            # This is approximate - Restic doesn't directly expose this
            deduplication_ratio = 1.0
            if total_size > 0:
                # Get actual repo size
                stats_result = await self._run_restic_command(
                    ["stats"],
                    repo_path,
                    password,
                    json_output=True
                )
                total_blob_count = stats_result.get("total_blob_count", total_file_count)
                if total_blob_count > 0:
                    deduplication_ratio = total_file_count / total_blob_count

            return {
                "total_size": total_size,
                "total_file_count": total_file_count,
                "snapshots_count": snapshots_count,
                "deduplication_ratio": round(deduplication_ratio, 2),
                "message": f"Repository contains {snapshots_count} snapshot(s)"
            }

        except Exception as e:
            logger.error(f"Failed to get repository stats: {e}")
            raise


# Global instance
restic_backup_manager = ResticBackupManager()
