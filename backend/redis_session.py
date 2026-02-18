"""
Redis Session Manager for UC-Cloud
Replaces in-memory session storage with Redis-backed persistence
"""
import json
import logging
import redis
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)


class RedisSessionManager:
    """Manages user sessions in Redis with TTL support"""

    def __init__(
        self,
        host: str = "unicorn-redis",
        port: int = 6379,
        db: int = 0,
        ttl: int = 7200,  # 2 hours in seconds
        key_prefix: str = "session:"
    ):
        """
        Initialize Redis session manager

        Args:
            host: Redis host (default: unicorn-redis)
            port: Redis port (default: 6379)
            db: Redis database number (default: 0)
            ttl: Session time-to-live in seconds (default: 7200 = 2 hours)
            key_prefix: Prefix for session keys (default: "session:")
        """
        self.host = host
        self.port = port
        self.db = db
        self.ttl = ttl
        self.key_prefix = key_prefix
        self._client: Optional[redis.Redis] = None

        # Initialize connection
        self._connect()

    def _connect(self):
        """Establish Redis connection"""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self._client.ping()
            logger.info(f"Redis session manager connected to {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def _get_key(self, session_id: str) -> str:
        """Generate full Redis key for session"""
        return f"{self.key_prefix}{session_id}"

    def set(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Store session data in Redis with TTL

        Args:
            session_id: Unique session identifier
            session_data: Session data dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._get_key(session_id)
            value = json.dumps(session_data)
            self._client.setex(key, self.ttl, value)
            logger.debug(f"Session stored: {session_id[:10]}... (TTL: {self.ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Failed to store session {session_id}: {e}")
            return False

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data from Redis

        Args:
            session_id: Unique session identifier

        Returns:
            Session data dictionary or None if not found/expired
        """
        try:
            key = self._get_key(session_id)
            value = self._client.get(key)

            if value is None:
                logger.debug(f"Session not found or expired: {session_id[:10]}...")
                return None

            session_data = json.loads(value)
            logger.debug(f"Session retrieved: {session_id[:10]}...")
            return session_data
        except Exception as e:
            logger.error(f"Failed to retrieve session {session_id}: {e}")
            return None

    def delete(self, session_id: str) -> bool:
        """
        Delete session from Redis

        Args:
            session_id: Unique session identifier

        Returns:
            True if deleted, False otherwise
        """
        try:
            key = self._get_key(session_id)
            result = self._client.delete(key)
            if result:
                logger.debug(f"Session deleted: {session_id[:10]}...")
                return True
            else:
                logger.debug(f"Session not found for deletion: {session_id[:10]}...")
                return False
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def exists(self, session_id: str) -> bool:
        """
        Check if session exists in Redis

        Args:
            session_id: Unique session identifier

        Returns:
            True if exists, False otherwise
        """
        try:
            key = self._get_key(session_id)
            return bool(self._client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check session existence {session_id}: {e}")
            return False

    def refresh(self, session_id: str) -> bool:
        """
        Refresh session TTL (reset expiration timer)

        Args:
            session_id: Unique session identifier

        Returns:
            True if refreshed, False otherwise
        """
        try:
            key = self._get_key(session_id)
            result = self._client.expire(key, self.ttl)
            if result:
                logger.debug(f"Session TTL refreshed: {session_id[:10]}...")
                return True
            else:
                logger.debug(f"Session not found for refresh: {session_id[:10]}...")
                return False
        except Exception as e:
            logger.error(f"Failed to refresh session {session_id}: {e}")
            return False

    def count(self) -> int:
        """
        Count total active sessions

        Returns:
            Number of active sessions
        """
        try:
            pattern = f"{self.key_prefix}*"
            keys = self._client.keys(pattern)
            return len(keys)
        except Exception as e:
            logger.error(f"Failed to count sessions: {e}")
            return 0

    def clear_all(self) -> int:
        """
        Clear all sessions (use with caution!)

        Returns:
            Number of sessions cleared
        """
        try:
            pattern = f"{self.key_prefix}*"
            keys = self._client.keys(pattern)
            if keys:
                deleted = self._client.delete(*keys)
                logger.warning(f"Cleared {deleted} sessions")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Failed to clear sessions: {e}")
            return 0

    def __contains__(self, session_id: str) -> bool:
        """Support 'in' operator: if session_id in session_manager"""
        return self.exists(session_id)

    def __getitem__(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Support dict-style access: session_manager[session_id]"""
        session_data = self.get(session_id)
        if session_data is None:
            raise KeyError(f"Session not found: {session_id}")
        return session_data

    def __setitem__(self, session_id: str, session_data: Dict[str, Any]):
        """Support dict-style assignment: session_manager[session_id] = data"""
        self.set(session_id, session_data)

    def __delitem__(self, session_id: str):
        """Support dict-style deletion: del session_manager[session_id]"""
        if not self.delete(session_id):
            raise KeyError(f"Session not found: {session_id}")

    def close(self):
        """Close Redis connection"""
        if self._client:
            self._client.close()
            logger.info("Redis session manager connection closed")


# Create global instance with environment-based configuration
redis_session_manager = RedisSessionManager(
    host=os.getenv("REDIS_HOST", "unicorn-redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=int(os.getenv("REDIS_DB", "0")),
    ttl=int(os.getenv("SESSION_TTL", "7200")),  # 2 hours
    key_prefix=os.getenv("SESSION_KEY_PREFIX", "session:")
)
