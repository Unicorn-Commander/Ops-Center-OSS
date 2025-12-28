"""
Cloud Backup Integration for Ops-Center
Supports S3-compatible storage (AWS S3, Backblaze B2, Wasabi, MinIO)
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    from botocore.config import Config
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("boto3 not installed - cloud backup features disabled")

from audit_logger import audit_logger

logger = logging.getLogger(__name__)

class CloudBackupManager:
    """Manages cloud backup operations with S3-compatible storage"""

    def __init__(self):
        self.enabled = os.getenv("CLOUD_BACKUP_ENABLED", "false").lower() == "true"
        self.provider = os.getenv("CLOUD_BACKUP_PROVIDER", "s3")
        self.bucket_name = os.getenv("CLOUD_BACKUP_BUCKET", "uc-cloud-backups")
        self.region = os.getenv("CLOUD_BACKUP_REGION", "us-west-2")

        if not BOTO3_AVAILABLE:
            self.enabled = False
            logger.warning("Cloud backups disabled - boto3 not installed")
            return

        if not self.enabled:
            logger.info("Cloud backups disabled in configuration")
            return

        # Initialize S3 client
        try:
            self._init_s3_client()
            logger.info(f"Cloud backup initialized: {self.provider} ({self.bucket_name})")
        except Exception as e:
            logger.error(f"Failed to initialize cloud backup: {e}")
            self.enabled = False

    def _init_s3_client(self):
        """Initialize boto3 S3 client based on provider"""
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 not installed")

        access_key = os.getenv("CLOUD_BACKUP_ACCESS_KEY")
        secret_key = os.getenv("CLOUD_BACKUP_SECRET_KEY")

        if not access_key or not secret_key:
            raise ValueError("Cloud backup credentials not configured")

        # Provider-specific endpoint configuration
        endpoint_url = os.getenv("CLOUD_BACKUP_ENDPOINT")

        if not endpoint_url:
            if self.provider == "backblaze":
                endpoint_url = f"https://s3.{self.region}.backblazeb2.com"
            elif self.provider == "wasabi":
                endpoint_url = f"https://s3.{self.region}.wasabisys.com"
            elif self.provider == "minio":
                endpoint_url = os.getenv("CLOUD_BACKUP_ENDPOINT", "http://minio:9000")
            # else use default AWS S3 endpoint

        # Configure boto3 client
        config = Config(
            region_name=self.region,
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )

        if endpoint_url:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=config
            )
        else:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=self.region,
                config=config
            )

        # Verify bucket access
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Successfully connected to bucket: {self.bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, try to create it
                logger.info(f"Bucket {self.bucket_name} not found, creating...")
                self._create_bucket()
            else:
                raise

    def _create_bucket(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            if self.region == 'us-east-1':
                # us-east-1 doesn't accept LocationConstraint
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )

            # Enable versioning for backup safety
            self.s3_client.put_bucket_versioning(
                Bucket=self.bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )

            logger.info(f"Created bucket: {self.bucket_name}")

        except ClientError as e:
            logger.error(f"Failed to create bucket: {e}")
            raise

    async def upload_backup(
        self,
        backup_id: str,
        local_path: str,
        metadata: Optional[Dict] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Upload a backup file to cloud storage

        Args:
            backup_id: Unique backup identifier
            local_path: Path to local backup file
            metadata: Optional metadata to attach to the object
            progress_callback: Optional callback for upload progress

        Returns:
            Dict with upload result details
        """
        if not self.enabled:
            raise Exception("Cloud backups are not enabled")

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Backup file not found: {local_path}")

        try:
            start_time = datetime.now()

            # Prepare S3 object key
            s3_key = f"backups/{backup_id}.tar.gz"

            # Prepare metadata
            s3_metadata = {
                'backup-id': backup_id,
                'upload-timestamp': datetime.now().isoformat(),
                'original-filename': os.path.basename(local_path)
            }
            if metadata:
                s3_metadata.update({k: str(v) for k, v in metadata.items()})

            # Get file size for progress tracking
            file_size = os.path.getsize(local_path)

            # Upload with multipart for large files
            if file_size > 100 * 1024 * 1024:  # > 100MB
                await self._multipart_upload(
                    local_path,
                    s3_key,
                    s3_metadata,
                    progress_callback
                )
            else:
                # Simple upload for smaller files
                with open(local_path, 'rb') as f:
                    self.s3_client.upload_fileobj(
                        f,
                        self.bucket_name,
                        s3_key,
                        ExtraArgs={'Metadata': s3_metadata}
                    )

            end_time = datetime.now()
            duration = end_time - start_time

            # Get uploaded object details
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            result = {
                "success": True,
                "backup_id": backup_id,
                "s3_key": s3_key,
                "bucket": self.bucket_name,
                "provider": self.provider,
                "size": file_size,
                "upload_duration": str(duration),
                "etag": response.get('ETag', '').strip('"'),
                "version_id": response.get('VersionId'),
                "timestamp": end_time.isoformat()
            }

            # Log to audit
            audit_logger.log(
                action="backup.cloud.upload",
                user_id="system",
                details=result
            )

            logger.info(f"Backup uploaded to cloud: {backup_id} (took {duration})")

            return result

        except Exception as e:
            logger.error(f"Cloud backup upload failed: {e}")
            raise Exception(f"Failed to upload backup to cloud: {str(e)}")

    async def _multipart_upload(
        self,
        local_path: str,
        s3_key: str,
        metadata: Dict,
        progress_callback: Optional[callable] = None
    ):
        """Upload large file using multipart upload"""
        try:
            # Initialize multipart upload
            multipart_upload = self.s3_client.create_multipart_upload(
                Bucket=self.bucket_name,
                Key=s3_key,
                Metadata=metadata
            )
            upload_id = multipart_upload['UploadId']

            # Upload parts (5MB chunks)
            part_size = 5 * 1024 * 1024
            parts = []
            part_number = 1

            with open(local_path, 'rb') as f:
                while True:
                    data = f.read(part_size)
                    if not data:
                        break

                    part = self.s3_client.upload_part(
                        Bucket=self.bucket_name,
                        Key=s3_key,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=data
                    )

                    parts.append({
                        'PartNumber': part_number,
                        'ETag': part['ETag']
                    })

                    if progress_callback:
                        await progress_callback(part_number * part_size)

                    part_number += 1

            # Complete multipart upload
            self.s3_client.complete_multipart_upload(
                Bucket=self.bucket_name,
                Key=s3_key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )

            logger.info(f"Multipart upload completed: {s3_key} ({part_number-1} parts)")

        except Exception as e:
            # Abort multipart upload on error
            try:
                self.s3_client.abort_multipart_upload(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    UploadId=upload_id
                )
            except Exception:
                pass
            raise e

    async def download_backup(
        self,
        backup_id: str,
        local_path: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Download a backup file from cloud storage

        Args:
            backup_id: Unique backup identifier
            local_path: Path where to save downloaded file
            progress_callback: Optional callback for download progress

        Returns:
            Dict with download result details
        """
        if not self.enabled:
            raise Exception("Cloud backups are not enabled")

        try:
            start_time = datetime.now()

            # Prepare S3 object key
            s3_key = f"backups/{backup_id}.tar.gz"

            # Ensure local directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Download file
            with open(local_path, 'wb') as f:
                self.s3_client.download_fileobj(
                    self.bucket_name,
                    s3_key,
                    f
                )

            end_time = datetime.now()
            duration = end_time - start_time

            # Get file size
            file_size = os.path.getsize(local_path)

            result = {
                "success": True,
                "backup_id": backup_id,
                "s3_key": s3_key,
                "local_path": local_path,
                "size": file_size,
                "download_duration": str(duration),
                "timestamp": end_time.isoformat()
            }

            # Log to audit
            audit_logger.log(
                action="backup.cloud.download",
                user_id="system",
                details=result
            )

            logger.info(f"Backup downloaded from cloud: {backup_id} (took {duration})")

            return result

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f"Backup not found in cloud: {backup_id}")
            else:
                raise Exception(f"Failed to download backup: {str(e)}")

    async def list_cloud_backups(self) -> List[Dict[str, Any]]:
        """
        List all backups stored in cloud

        Returns:
            List of backup metadata dicts
        """
        if not self.enabled:
            raise Exception("Cloud backups are not enabled")

        try:
            backups = []

            # List objects in backups/ prefix
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix='backups/')

            for page in pages:
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    # Extract backup ID from key
                    key = obj['Key']
                    if not key.endswith('.tar.gz'):
                        continue

                    backup_id = os.path.basename(key).replace('.tar.gz', '')

                    # Get object metadata
                    head = self.s3_client.head_object(
                        Bucket=self.bucket_name,
                        Key=key
                    )

                    backups.append({
                        'backup_id': backup_id,
                        's3_key': key,
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'etag': obj.get('ETag', '').strip('"'),
                        'storage_class': obj.get('StorageClass', 'STANDARD'),
                        'metadata': head.get('Metadata', {})
                    })

            # Sort by last modified (newest first)
            backups.sort(key=lambda b: b['last_modified'], reverse=True)

            logger.info(f"Found {len(backups)} backups in cloud storage")

            return backups

        except Exception as e:
            logger.error(f"Failed to list cloud backups: {e}")
            raise Exception(f"Failed to list cloud backups: {str(e)}")

    async def delete_cloud_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Delete a backup from cloud storage

        Args:
            backup_id: Unique backup identifier

        Returns:
            Dict with deletion result
        """
        if not self.enabled:
            raise Exception("Cloud backups are not enabled")

        try:
            # Prepare S3 object key
            s3_key = f"backups/{backup_id}.tar.gz"

            # Delete object
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            result = {
                "success": True,
                "backup_id": backup_id,
                "s3_key": s3_key,
                "timestamp": datetime.now().isoformat()
            }

            # Log to audit
            audit_logger.log(
                action="backup.cloud.delete",
                user_id="system",
                details=result
            )

            logger.info(f"Backup deleted from cloud: {backup_id}")

            return result

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f"Backup not found in cloud: {backup_id}")
            else:
                raise Exception(f"Failed to delete cloud backup: {str(e)}")

    async def sync_backups(
        self,
        local_backup_dir: str,
        direction: str = "upload"
    ) -> Dict[str, Any]:
        """
        Sync backups between local and cloud storage

        Args:
            local_backup_dir: Path to local backup directory
            direction: "upload" (local→cloud) or "download" (cloud→local)

        Returns:
            Dict with sync statistics
        """
        if not self.enabled:
            raise Exception("Cloud backups are not enabled")

        try:
            synced = []
            errors = []
            skipped = []

            if direction == "upload":
                # Upload local backups to cloud
                local_backups = list(Path(local_backup_dir).glob("backup-*.tar.gz"))

                for backup_file in local_backups:
                    backup_id = backup_file.stem
                    try:
                        result = await self.upload_backup(backup_id, str(backup_file))
                        synced.append(result)
                    except Exception as e:
                        errors.append({"backup_id": backup_id, "error": str(e)})

            elif direction == "download":
                # Download cloud backups to local
                cloud_backups = await self.list_cloud_backups()

                for backup in cloud_backups:
                    backup_id = backup['backup_id']
                    local_path = os.path.join(local_backup_dir, f"{backup_id}.tar.gz")

                    # Skip if already exists locally
                    if os.path.exists(local_path):
                        skipped.append(backup_id)
                        continue

                    try:
                        result = await self.download_backup(backup_id, local_path)
                        synced.append(result)
                    except Exception as e:
                        errors.append({"backup_id": backup_id, "error": str(e)})

            else:
                raise ValueError(f"Invalid direction: {direction} (must be 'upload' or 'download')")

            result = {
                "success": len(errors) == 0,
                "direction": direction,
                "synced": len(synced),
                "skipped": len(skipped),
                "errors": len(errors),
                "details": {
                    "synced": synced,
                    "skipped": skipped,
                    "errors": errors
                }
            }

            logger.info(f"Backup sync completed: {len(synced)} synced, {len(errors)} errors")

            return result

        except Exception as e:
            logger.error(f"Backup sync failed: {e}")
            raise Exception(f"Failed to sync backups: {str(e)}")

    def get_storage_info(self) -> Dict[str, Any]:
        """Get cloud storage information and statistics"""
        if not self.enabled:
            return {
                "enabled": False,
                "provider": None,
                "bucket": None
            }

        try:
            # Get bucket size and object count
            total_size = 0
            object_count = 0

            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix='backups/')

            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        total_size += obj['Size']
                        object_count += 1

            return {
                "enabled": True,
                "provider": self.provider,
                "bucket": self.bucket_name,
                "region": self.region,
                "total_backups": object_count,
                "total_size": total_size,
                "total_size_gb": round(total_size / (1024**3), 2)
            }

        except Exception as e:
            logger.error(f"Failed to get cloud storage info: {e}")
            return {
                "enabled": True,
                "provider": self.provider,
                "bucket": self.bucket_name,
                "error": str(e)
            }

# Create singleton instance
cloud_backup_manager = CloudBackupManager() if BOTO3_AVAILABLE else None
