"""
Storage & Backup Management Module for UC-1 Pro Admin Dashboard
Handles storage monitoring, volume management, and backup operations
"""

import os
import json
import asyncio
import subprocess
import shutil
import tarfile
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging
import psutil

logger = logging.getLogger(__name__)

# Dynamic path detection - works across different users
def _get_base_path() -> str:
    """Get base UC-1-Pro path dynamically"""
    home = os.path.expanduser("~")
    # Check if we're in production or development
    possible_paths = [
        os.path.join(home, "Production", "UC-1-Pro"),
        os.path.join(home, "UC-1-Pro"),
        "/opt/UC-1-Pro",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found UC-1-Pro at: {path}")
            return path

    # Default to home-based path (will be created if needed)
    default_path = os.path.join(home, "UC-1-Pro")
    logger.info(f"Using default UC-1-Pro path: {default_path}")
    return default_path

# Configuration paths - dynamically determined
BASE_PATH = _get_base_path()
STORAGE_CONFIG_PATH = os.path.join(BASE_PATH, "volumes", "storage_config.json")
BACKUP_CONFIG_PATH = os.path.join(BASE_PATH, "volumes", "backup_config.json")
BACKUP_LOCATION = os.path.join(BASE_PATH, "backups")
VOLUMES_PATH = os.path.join(BASE_PATH, "volumes")

# Pydantic models for API requests/responses
class VolumeInfo(BaseModel):
    name: str
    path: str
    size: int
    type: str
    health: str
    last_accessed: str

class StorageInfo(BaseModel):
    total_space: int
    used_space: int
    free_space: int
    volumes: List[VolumeInfo]

class BackupConfig(BaseModel):
    backup_enabled: bool = True
    schedule: str = "0 2 * * *"  # 2 AM daily
    retention_days: int = 7
    backup_location: str = BACKUP_LOCATION
    include_paths: List[str] = [VOLUMES_PATH]
    exclude_patterns: List[str] = ["*.tmp", "*.lock", "__pycache__"]

class BackupInfo(BaseModel):
    id: str
    timestamp: str
    size: int
    type: str
    status: str
    duration: str
    files_count: int

class BackupStatus(BaseModel):
    backup_enabled: bool
    schedule: str
    last_backup: Optional[str]
    next_backup: Optional[str]
    backup_location: str
    retention_days: int
    backups: List[BackupInfo]

class StorageBackupManager:
    def __init__(self):
        self.storage_config = self._load_storage_config()
        self.backup_config = self._load_backup_config()
        self._ensure_backup_directory()
        
    def _load_storage_config(self) -> Dict:
        """Load storage configuration from disk"""
        if os.path.exists(STORAGE_CONFIG_PATH):
            try:
                with open(STORAGE_CONFIG_PATH, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading storage config: {e}")
        
        return {
            "monitored_paths": [VOLUMES_PATH],
            "health_check_enabled": True,
            "alerts_enabled": True,
            "disk_usage_threshold": 90
        }
    
    def _load_backup_config(self) -> BackupConfig:
        """Load backup configuration from disk"""
        if os.path.exists(BACKUP_CONFIG_PATH):
            try:
                with open(BACKUP_CONFIG_PATH, 'r') as f:
                    data = json.load(f)
                    return BackupConfig(**data)
            except Exception as e:
                logger.error(f"Error loading backup config: {e}")
        
        return BackupConfig()
    
    def _save_storage_config(self):
        """Save storage configuration to disk"""
        try:
            os.makedirs(os.path.dirname(STORAGE_CONFIG_PATH), exist_ok=True)
            with open(STORAGE_CONFIG_PATH, 'w') as f:
                json.dump(self.storage_config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving storage config: {e}")
    
    def _save_backup_config(self):
        """Save backup configuration to disk"""
        try:
            os.makedirs(os.path.dirname(BACKUP_CONFIG_PATH), exist_ok=True)
            with open(BACKUP_CONFIG_PATH, 'w') as f:
                json.dump(self.backup_config.dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving backup config: {e}")
    
    def _ensure_backup_directory(self):
        """Ensure backup directory exists"""
        os.makedirs(self.backup_config.backup_location, exist_ok=True)
    
    def get_storage_info(self) -> StorageInfo:
        """Get comprehensive storage information"""
        # Get overall disk usage
        disk_usage = shutil.disk_usage("/")
        total_space = disk_usage.total
        free_space = disk_usage.free
        used_space = total_space - free_space
        
        # Get volume information
        volumes = []
        if os.path.exists(VOLUMES_PATH):
            for item in Path(VOLUMES_PATH).iterdir():
                if item.is_dir():
                    size = self._get_directory_size(item)
                    volume_type = self._determine_volume_type(item.name)
                    health = self._check_volume_health(item)
                    last_accessed = datetime.fromtimestamp(item.stat().st_atime).isoformat()
                    
                    volumes.append(VolumeInfo(
                        name=item.name,
                        path=str(item),
                        size=size,
                        type=volume_type,
                        health=health,
                        last_accessed=last_accessed
                    ))
        
        return StorageInfo(
            total_space=total_space,
            used_space=used_space,
            free_space=free_space,
            volumes=volumes
        )
    
    def _get_directory_size(self, path: Path) -> int:
        """Get total size of a directory"""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        except Exception as e:
            logger.warning(f"Error calculating size for {path}: {e}")
        return total
    
    def _determine_volume_type(self, volume_name: str) -> str:
        """Determine volume type based on name"""
        if any(keyword in volume_name.lower() for keyword in ['model', 'embedding', 'whisper', 'kokoro', 'vllm']):
            return 'AI Models'
        elif any(keyword in volume_name.lower() for keyword in ['postgres', 'database', 'db']):
            return 'Database'
        elif any(keyword in volume_name.lower() for keyword in ['redis', 'cache']):
            return 'Cache'
        elif any(keyword in volume_name.lower() for keyword in ['backup', 'archive']):
            return 'Backup'
        else:
            return 'Data'
    
    def _check_volume_health(self, path: Path) -> str:
        """Check volume health based on various factors"""
        try:
            # Basic checks
            if not os.access(path, os.R_OK | os.W_OK):
                return 'error'
            
            # Check for recent access (within 7 days = healthy, 30 days = warning)
            last_access = datetime.fromtimestamp(path.stat().st_atime)
            days_since_access = (datetime.now() - last_access).days
            
            if days_since_access > 30:
                return 'warning'
            
            return 'healthy'
        except Exception:
            return 'error'
    
    def get_backup_status(self) -> BackupStatus:
        """Get backup status and history"""
        backups = self._get_backup_history()
        
        last_backup = None
        if backups:
            last_backup = backups[0].timestamp
        
        # Calculate next backup (simplified - would need cron parsing for real implementation)
        next_backup = None
        if self.backup_config.backup_enabled:
            # For daily at 2 AM, calculate next occurrence
            now = datetime.now()
            next_backup_time = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if next_backup_time <= now:
                next_backup_time += timedelta(days=1)
            next_backup = next_backup_time.isoformat()
        
        return BackupStatus(
            backup_enabled=self.backup_config.backup_enabled,
            schedule=self.backup_config.schedule,
            last_backup=last_backup,
            next_backup=next_backup,
            backup_location=self.backup_config.backup_location,
            retention_days=self.backup_config.retention_days,
            backups=backups
        )
    
    def _get_backup_history(self) -> List[BackupInfo]:
        """Get list of existing backups"""
        backups = []
        backup_dir = Path(self.backup_config.backup_location)
        
        if not backup_dir.exists():
            return backups
        
        # Look for backup files (assuming .tar.gz format)
        for backup_file in backup_dir.glob("backup-*.tar.gz"):
            try:
                # Parse backup info from filename and file stats
                stat = backup_file.stat()
                backup_id = backup_file.stem
                timestamp = datetime.fromtimestamp(stat.st_mtime).isoformat()
                size = stat.st_size
                
                # Try to get additional info from metadata file if it exists
                metadata_file = backup_dir / f"{backup_id}.json"
                duration = "Unknown"
                files_count = 0
                backup_type = "Full"
                status = "completed"
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            duration = metadata.get('duration', duration)
                            files_count = metadata.get('files_count', files_count)
                            backup_type = metadata.get('type', backup_type)
                            status = metadata.get('status', status)
                    except Exception:
                        pass
                
                backups.append(BackupInfo(
                    id=backup_id,
                    timestamp=timestamp,
                    size=size,
                    type=backup_type,
                    status=status,
                    duration=duration,
                    files_count=files_count
                ))
            except Exception as e:
                logger.warning(f"Error processing backup file {backup_file}: {e}")
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda b: b.timestamp, reverse=True)
        return backups
    
    async def create_backup(self, backup_type: str = "manual") -> str:
        """Create a new backup"""
        timestamp = datetime.now()
        backup_id = f"backup-{timestamp.strftime('%Y%m%d-%H%M%S')}"
        
        backup_dir = Path(self.backup_config.backup_location)
        backup_file = backup_dir / f"{backup_id}.tar.gz"
        metadata_file = backup_dir / f"{backup_id}.json"
        
        start_time = datetime.now()
        files_count = 0
        
        try:
            # Create tar.gz backup
            with tarfile.open(backup_file, 'w:gz') as tar:
                for include_path in self.backup_config.include_paths:
                    if os.path.exists(include_path):
                        # Add path to backup
                        tar.add(include_path, arcname=os.path.basename(include_path))
                        
                        # Count files for metadata
                        for root, dirs, files in os.walk(include_path):
                            files_count += len(files)
            
            # Calculate duration
            end_time = datetime.now()
            duration = str(end_time - start_time)
            
            # Save metadata
            metadata = {
                'id': backup_id,
                'timestamp': timestamp.isoformat(),
                'type': backup_type,
                'status': 'completed',
                'duration': duration,
                'files_count': files_count,
                'size': backup_file.stat().st_size
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Clean up old backups based on retention policy
            self._cleanup_old_backups()
            
            return backup_id
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            # Mark backup as failed in metadata
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'w') as f:
                        json.dump({
                            'id': backup_id,
                            'timestamp': timestamp.isoformat(),
                            'type': backup_type,
                            'status': 'failed',
                            'error': str(e)
                        }, f, indent=2)
                except Exception:
                    pass
            
            raise Exception(f"Backup creation failed: {e}")
    
    def _cleanup_old_backups(self):
        """Remove old backups based on retention policy"""
        if self.backup_config.retention_days <= 0:
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.backup_config.retention_days)
        backup_dir = Path(self.backup_config.backup_location)
        
        for backup_file in backup_dir.glob("backup-*.tar.gz"):
            try:
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_date:
                    # Remove backup file and metadata
                    backup_file.unlink()
                    metadata_file = backup_dir / f"{backup_file.stem}.json"
                    if metadata_file.exists():
                        metadata_file.unlink()
                    logger.info(f"Removed old backup: {backup_file.name}")
            except Exception as e:
                logger.warning(f"Error removing old backup {backup_file}: {e}")
    
    async def restore_backup(self, backup_id: str, restore_path: Optional[str] = None) -> bool:
        """Restore from a backup"""
        backup_dir = Path(self.backup_config.backup_location)
        backup_file = backup_dir / f"{backup_id}.tar.gz"
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")
        
        if restore_path is None:
            restore_path = "/tmp/restore_" + backup_id
        
        try:
            # Extract backup
            with tarfile.open(backup_file, 'r:gz') as tar:
                tar.extractall(restore_path)
            
            logger.info(f"Backup restored to: {restore_path}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise Exception(f"Backup restore failed: {e}")
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup"""
        backup_dir = Path(self.backup_config.backup_location)
        backup_file = backup_dir / f"{backup_id}.tar.gz"
        metadata_file = backup_dir / f"{backup_id}.json"
        
        try:
            if backup_file.exists():
                backup_file.unlink()
            if metadata_file.exists():
                metadata_file.unlink()
            
            logger.info(f"Deleted backup: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting backup {backup_id}: {e}")
            raise Exception(f"Failed to delete backup: {e}")
    
    def update_backup_config(self, config: Dict) -> BackupConfig:
        """Update backup configuration"""
        # Update only provided fields
        for key, value in config.items():
            if hasattr(self.backup_config, key):
                setattr(self.backup_config, key, value)
        
        self._save_backup_config()
        self._ensure_backup_directory()
        
        return self.backup_config
    
    def get_volume_details(self, volume_name: str) -> Optional[Dict]:
        """Get detailed information about a specific volume"""
        volume_path = Path(VOLUMES_PATH) / volume_name
        
        if not volume_path.exists():
            return None
        
        # Get basic info
        size = self._get_directory_size(volume_path)
        health = self._check_volume_health(volume_path)
        last_accessed = datetime.fromtimestamp(volume_path.stat().st_atime).isoformat()
        
        # Get file count and largest files
        files = []
        total_files = 0
        
        try:
            for entry in volume_path.rglob('*'):
                if entry.is_file():
                    total_files += 1
                    files.append({
                        'name': entry.name,
                        'path': str(entry.relative_to(volume_path)),
                        'size': entry.stat().st_size,
                        'modified': datetime.fromtimestamp(entry.stat().st_mtime).isoformat()
                    })
            
            # Sort by size (largest first) and take top 10
            files.sort(key=lambda f: f['size'], reverse=True)
            largest_files = files[:10]
            
        except Exception as e:
            logger.warning(f"Error analyzing volume {volume_name}: {e}")
            largest_files = []
        
        return {
            'name': volume_name,
            'path': str(volume_path),
            'size': size,
            'type': self._determine_volume_type(volume_name),
            'health': health,
            'last_accessed': last_accessed,
            'total_files': total_files,
            'largest_files': largest_files
        }

# Create singleton instance
storage_backup_manager = StorageBackupManager()