"""Audit Logging Service

This module provides comprehensive audit logging functionality for tracking
security events, user actions, and system operations.
"""

import os
import json
import sqlite3
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from contextlib import contextmanager
import aiofiles
from logging.handlers import RotatingFileHandler
from collections import defaultdict

from models.audit_log import (
    AuditLog, AuditLogCreate, AuditLogFilter, AuditLogResponse,
    AuditStats, AuditAction, AuditResult
)


class AuditLogger:
    """Audit logging service with database and file-based logging"""

    def __init__(
        self,
        db_path: str = "data/ops_center.db",
        log_dir: str = "/var/log/ops-center",
        enable_file_logging: bool = True,
        enable_db_logging: bool = True,
        max_log_size_mb: int = 100,
        backup_count: int = 10
    ):
        """Initialize audit logger

        Args:
            db_path: Path to SQLite database
            log_dir: Directory for audit log files
            enable_file_logging: Enable file-based audit logging
            enable_db_logging: Enable database audit logging
            max_log_size_mb: Maximum size of each log file in MB
            backup_count: Number of backup log files to keep
        """
        self.db_path = db_path
        self.log_dir = Path(log_dir)
        self.enable_file_logging = enable_file_logging
        self.enable_db_logging = enable_db_logging

        # Ensure directories exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        if enable_file_logging:
            self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database
        if enable_db_logging:
            self._init_database()

        # Configure file logger
        if enable_file_logging:
            self.file_logger = logging.getLogger('audit')
            self.file_logger.setLevel(logging.INFO)
            self.file_logger.propagate = False

            # Remove existing handlers
            self.file_logger.handlers = []

            # Add rotating file handler
            audit_log_file = self.log_dir / "audit.log"
            handler = RotatingFileHandler(
                audit_log_file,
                maxBytes=max_log_size_mb * 1024 * 1024,
                backupCount=backup_count
            )

            # JSON format for structured logging
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}',
                datefmt='%Y-%m-%dT%H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.file_logger.addHandler(handler)

    def _init_database(self):
        """Initialize audit log database table"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    username TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    result TEXT NOT NULL,
                    error_message TEXT,
                    metadata TEXT,
                    session_id TEXT
                )
            """)

            # Create indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_logs(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_user_id
                ON audit_logs(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_action
                ON audit_logs(action)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_result
                ON audit_logs(result)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_ip_address
                ON audit_logs(ip_address)
            """)

            conn.commit()

    @contextmanager
    def _get_db_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    async def log(
        self,
        action: str,
        result: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Optional[int]:
        """Log an audit event asynchronously

        Args:
            action: Action being audited (e.g., 'auth.login.success')
            result: Result of the action ('success', 'failure', 'error', 'denied')
            user_id: ID of the user performing the action
            username: Username of the user
            ip_address: IP address of the request
            user_agent: User agent string
            resource_type: Type of resource affected (e.g., 'service', 'model')
            resource_id: ID of the resource
            error_message: Error message if result is failure/error
            metadata: Additional metadata as dictionary
            session_id: Session identifier

        Returns:
            ID of the created audit log entry (if database logging enabled)
        """
        audit_entry = AuditLogCreate(
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            error_message=error_message,
            metadata=metadata or {},
            session_id=session_id
        )

        # Run both logging methods concurrently
        tasks = []

        if self.enable_db_logging:
            tasks.append(self._log_to_database(audit_entry))

        if self.enable_file_logging:
            tasks.append(self._log_to_file(audit_entry))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Return the database ID if available
            for result in results:
                if isinstance(result, int):
                    return result

        return None

    async def _log_to_database(self, entry: AuditLogCreate) -> Optional[int]:
        """Log audit entry to database"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._db_insert, entry)
        except Exception as e:
            logging.error(f"Failed to log to database: {e}")
            return None

    def _db_insert(self, entry: AuditLogCreate) -> int:
        """Insert audit entry into database (synchronous)"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (
                    timestamp, user_id, username, ip_address, user_agent,
                    action, resource_type, resource_id, result, error_message,
                    metadata, session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.utcnow().isoformat(),
                entry.user_id,
                entry.username,
                entry.ip_address,
                entry.user_agent,
                entry.action,
                entry.resource_type,
                entry.resource_id,
                entry.result,
                entry.error_message,
                json.dumps(entry.metadata) if entry.metadata else None,
                entry.session_id
            ))
            conn.commit()
            return cursor.lastrowid

    async def _log_to_file(self, entry: AuditLogCreate):
        """Log audit entry to file"""
        try:
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": entry.user_id,
                "username": entry.username,
                "ip_address": entry.ip_address,
                "action": entry.action,
                "resource_type": entry.resource_type,
                "resource_id": entry.resource_id,
                "result": entry.result,
                "error_message": entry.error_message,
                "metadata": entry.metadata,
                "session_id": entry.session_id
            }

            # Filter out None values for cleaner logs
            log_data = {k: v for k, v in log_data.items() if v is not None}

            self.file_logger.info(json.dumps(log_data))
        except Exception as e:
            logging.error(f"Failed to log to file: {e}")

    async def query_logs(self, filter_params: AuditLogFilter) -> AuditLogResponse:
        """Query audit logs with filtering

        Args:
            filter_params: Filter parameters for the query

        Returns:
            AuditLogResponse with matching logs
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._query_logs_sync, filter_params)

    def _query_logs_sync(self, filter_params: AuditLogFilter) -> AuditLogResponse:
        """Query audit logs synchronously"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            # Build WHERE clause
            where_clauses = []
            params = []

            if filter_params.user_id:
                where_clauses.append("user_id = ?")
                params.append(filter_params.user_id)

            if filter_params.username:
                where_clauses.append("username = ?")
                params.append(filter_params.username)

            if filter_params.action:
                where_clauses.append("action = ?")
                params.append(filter_params.action)

            if filter_params.resource_type:
                where_clauses.append("resource_type = ?")
                params.append(filter_params.resource_type)

            if filter_params.resource_id:
                where_clauses.append("resource_id = ?")
                params.append(filter_params.resource_id)

            if filter_params.result:
                where_clauses.append("result = ?")
                params.append(filter_params.result)

            if filter_params.ip_address:
                where_clauses.append("ip_address = ?")
                params.append(filter_params.ip_address)

            if filter_params.start_date:
                where_clauses.append("timestamp >= ?")
                params.append(filter_params.start_date)

            if filter_params.end_date:
                where_clauses.append("timestamp <= ?")
                params.append(filter_params.end_date)

            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            # Get total count
            count_query = f"SELECT COUNT(*) FROM audit_logs WHERE {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            # Get paginated results
            query = f"""
                SELECT * FROM audit_logs
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """
            params.extend([filter_params.limit, filter_params.offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Convert rows to AuditLog objects
            logs = []
            for row in rows:
                log = AuditLog(
                    id=row['id'],
                    timestamp=row['timestamp'],
                    user_id=row['user_id'],
                    username=row['username'],
                    ip_address=row['ip_address'],
                    user_agent=row['user_agent'],
                    action=row['action'],
                    resource_type=row['resource_type'],
                    resource_id=row['resource_id'],
                    result=row['result'],
                    error_message=row['error_message'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    session_id=row['session_id']
                )
                logs.append(log)

            return AuditLogResponse(
                total=total,
                offset=filter_params.offset,
                limit=filter_params.limit,
                logs=logs
            )

    async def get_statistics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> AuditStats:
        """Get audit statistics for a time period

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            AuditStats object with statistics
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_statistics_sync, start_date, end_date)

    def _get_statistics_sync(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> AuditStats:
        """Get audit statistics synchronously"""
        # Default to last 30 days if not specified
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()

        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            # Total events
            cursor.execute("""
                SELECT COUNT(*) FROM audit_logs
                WHERE timestamp >= ? AND timestamp <= ?
            """, (start_date, end_date))
            total_events = cursor.fetchone()[0]

            # Events by action
            cursor.execute("""
                SELECT action, COUNT(*) as count
                FROM audit_logs
                WHERE timestamp >= ? AND timestamp <= ?
                GROUP BY action
                ORDER BY count DESC
            """, (start_date, end_date))
            events_by_action = {row['action']: row['count'] for row in cursor.fetchall()}

            # Events by result
            cursor.execute("""
                SELECT result, COUNT(*) as count
                FROM audit_logs
                WHERE timestamp >= ? AND timestamp <= ?
                GROUP BY result
            """, (start_date, end_date))
            events_by_result = {row['result']: row['count'] for row in cursor.fetchall()}

            # Events by user
            cursor.execute("""
                SELECT COALESCE(username, 'anonymous') as user, COUNT(*) as count
                FROM audit_logs
                WHERE timestamp >= ? AND timestamp <= ?
                GROUP BY username
                ORDER BY count DESC
                LIMIT 20
            """, (start_date, end_date))
            events_by_user = {row['user']: row['count'] for row in cursor.fetchall()}

            # Failed logins
            cursor.execute("""
                SELECT COUNT(*) FROM audit_logs
                WHERE action = ? AND timestamp >= ? AND timestamp <= ?
            """, (AuditAction.AUTH_LOGIN_FAILED.value, start_date, end_date))
            failed_logins = cursor.fetchone()[0]

            # Security events
            security_actions = [
                AuditAction.PERMISSION_DENIED.value,
                AuditAction.CSRF_VALIDATION_FAILED.value,
                AuditAction.RATE_LIMIT_EXCEEDED.value,
                AuditAction.INVALID_TOKEN.value,
                AuditAction.SUSPICIOUS_ACTIVITY.value
            ]
            placeholders = ','.join(['?' for _ in security_actions])
            cursor.execute(f"""
                SELECT COUNT(*) FROM audit_logs
                WHERE action IN ({placeholders})
                AND timestamp >= ? AND timestamp <= ?
            """, (*security_actions, start_date, end_date))
            security_events = cursor.fetchone()[0]

            # Recent suspicious IPs (IPs with multiple failed logins)
            cursor.execute("""
                SELECT ip_address, COUNT(*) as count
                FROM audit_logs
                WHERE action = ? AND result = ?
                AND timestamp >= ? AND timestamp <= ?
                GROUP BY ip_address
                HAVING count >= 5
                ORDER BY count DESC
                LIMIT 10
            """, (
                AuditAction.AUTH_LOGIN_FAILED.value,
                AuditResult.FAILURE.value,
                start_date,
                end_date
            ))
            recent_suspicious_ips = [row['ip_address'] for row in cursor.fetchall() if row['ip_address']]

            return AuditStats(
                total_events=total_events,
                events_by_action=events_by_action,
                events_by_result=events_by_result,
                events_by_user=events_by_user,
                failed_logins=failed_logins,
                security_events=security_events,
                recent_suspicious_ips=recent_suspicious_ips,
                period_start=start_date,
                period_end=end_date
            )

    async def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """Clean up old audit logs

        Args:
            days_to_keep: Number of days of logs to keep

        Returns:
            Number of logs deleted
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._cleanup_old_logs_sync, days_to_keep)

    def _cleanup_old_logs_sync(self, days_to_keep: int) -> int:
        """Clean up old audit logs synchronously"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()

        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM audit_logs
                WHERE timestamp < ?
            """, (cutoff_date,))
            conn.commit()
            return cursor.rowcount


# Global audit logger instance
audit_logger = AuditLogger()
