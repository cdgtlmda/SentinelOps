"""
Session management for SentinelOps API.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import redis

from ..config.logging_config import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Manages user sessions with Redis backend."""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize session manager.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis_client: Optional[redis.Redis] = None
        self._in_memory_store: Dict[str, Dict[str, Any]] = (
            {}
        )  # Fallback for development

    @property
    def redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client with lazy initialization."""
        if self._redis_client is None and self.redis_url != "memory":
            try:
                self._redis_client = redis.Redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                )
                # Test connection
                self._redis_client.ping()
                logger.info("Connected to Redis for session management")
            except (ValueError, ConnectionError, AttributeError) as e:
                logger.warning(
                    "Failed to connect to Redis: %s. Using in-memory store.", e
                )
                self.redis_url = "memory"

        return self._redis_client

    def create_session(
        self,
        session_id: str,
        user_id: str,
        data: Dict[str, Any],
        ttl_seconds: int = 3600,
    ) -> bool:
        """
        Create a new session.

        Args:
            session_id: Unique session ID
            user_id: User ID associated with session
            data: Session data
            ttl_seconds: Time to live in seconds

        Returns:
            True if created successfully
        """
        session_data = {
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_accessed": datetime.now(timezone.utc).isoformat(),
            **data,
        }

        try:
            if self.redis_client:
                # Use Redis
                key = f"session:{session_id}"
                self.redis_client.setex(
                    key,
                    ttl_seconds,
                    json.dumps(session_data),
                )

                # Also track user sessions
                user_key = f"user_sessions:{user_id}"
                self.redis_client.sadd(user_key, session_id)
                self.redis_client.expire(user_key, ttl_seconds)

                logger.debug("Created session in Redis: %s", session_id)
                return True
            else:
                # Use in-memory store
                self._in_memory_store[session_id] = {
                    **session_data,
                    "_expires_at": datetime.now(timezone.utc)
                    + timedelta(seconds=ttl_seconds),
                }
                logger.debug("Created session in memory: %s", session_id)
                return True

        except (ValueError, ConnectionError, AttributeError) as e:
            logger.error("Failed to create session: %s", e)
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.

        Args:
            session_id: Session ID

        Returns:
            Session data if found and valid
        """
        try:
            if self.redis_client:
                # Get from Redis
                key = f"session:{session_id}"
                data = self.redis_client.get(key)

                if data:
                    parsed_data: Any = (
                        json.loads(data) if isinstance(data, str) else data
                    )
                    if not isinstance(parsed_data, dict):
                        return None
                    session_data: dict[str, Any] = parsed_data

                    # Update last accessed time
                    session_data["last_accessed"] = datetime.now(
                        timezone.utc
                    ).isoformat()
                    ttl = self.redis_client.ttl(key)
                    if isinstance(ttl, int) and ttl > 0:
                        self.redis_client.setex(key, ttl, json.dumps(session_data))

                    return session_data
            else:
                # Get from in-memory store
                memory_session_data: Optional[Dict[str, Any]] = (
                    self._in_memory_store.get(session_id)
                )

                if memory_session_data:
                    # Check expiration
                    if memory_session_data["_expires_at"] > datetime.now(timezone.utc):
                        memory_session_data["last_accessed"] = datetime.now(
                            timezone.utc
                        ).isoformat()
                        return {
                            k: v
                            for k, v in memory_session_data.items()
                            if not k.startswith("_")
                        }
                    else:
                        # Expired, remove it
                        del self._in_memory_store[session_id]

        except (ValueError, ConnectionError, AttributeError) as e:
            logger.error("Failed to get session: %s", e)

        return None

    def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any],
        extend_ttl: bool = True,
    ) -> bool:
        """
        Update session data.

        Args:
            session_id: Session ID
            updates: Data to update
            extend_ttl: Whether to extend session TTL

        Returns:
            True if updated successfully
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return False

            # Update data
            session_data.update(updates)
            session_data["last_accessed"] = datetime.now(timezone.utc).isoformat()

            if self.redis_client:
                # Update in Redis
                key = f"session:{session_id}"
                ttl = self.redis_client.ttl(key)

                if extend_ttl and isinstance(ttl, int) and ttl > 0:
                    # Extend TTL to original duration
                    ttl = max(ttl, 3600)  # At least 1 hour
                elif not isinstance(ttl, int) or ttl <= 0:
                    ttl = 3600  # Default to 1 hour

                self.redis_client.setex(key, ttl, json.dumps(session_data))
                logger.debug("Updated session in Redis: %s", session_id)
                return True
            else:
                # Update in memory
                if session_id in self._in_memory_store:
                    self._in_memory_store[session_id].update(session_data)

                    if extend_ttl:
                        # Extend expiration
                        self._in_memory_store[session_id]["_expires_at"] = datetime.now(
                            timezone.utc
                        ) + timedelta(hours=1)

                    logger.debug("Updated session in memory: %s", session_id)
                    return True

        except (ValueError, ConnectionError, AttributeError) as e:
            logger.error("Failed to update session: %s", e)

        return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session ID

        Returns:
            True if deleted successfully
        """
        try:
            if self.redis_client:
                # Get session to find user ID
                session_data = self.get_session(session_id)

                # Delete from Redis
                key = f"session:{session_id}"
                delete_result = self.redis_client.delete(key)
                result = isinstance(delete_result, int) and delete_result > 0

                # Remove from user sessions set
                if session_data and "user_id" in session_data:
                    user_key = f"user_sessions:{session_data['user_id']}"
                    self.redis_client.srem(user_key, session_id)

                logger.debug("Deleted session from Redis: %s", session_id)
                return result
            else:
                # Delete from memory
                if session_id in self._in_memory_store:
                    del self._in_memory_store[session_id]
                    logger.debug("Deleted session from memory: %s", session_id)
                    return True

        except (ValueError, ConnectionError, AttributeError) as e:
            logger.error("Failed to delete session: %s", e)

        return False

    def get_user_sessions(self, user_id: str) -> List[str]:
        """
        Get all active sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of session IDs
        """
        try:
            if self.redis_client:
                # Get from Redis
                user_key = f"user_sessions:{user_id}"
                members = self.redis_client.smembers(user_key)
                return list(members) if isinstance(members, set) else []
            else:
                # Get from memory
                sessions = []
                now = datetime.now(timezone.utc)

                for session_id, data in list(self._in_memory_store.items()):
                    if (
                        data.get("user_id") == user_id
                        and data.get("_expires_at", now) > now
                    ):
                        sessions.append(session_id)

                return sessions

        except (ValueError, ConnectionError, AttributeError) as e:
            logger.error("Failed to get user sessions: %s", e)
            return []

    def delete_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a user.

        Args:
            user_id: User ID

        Returns:
            Number of sessions deleted
        """
        sessions = self.get_user_sessions(user_id)
        deleted = 0

        for session_id in sessions:
            if self.delete_session(session_id):
                deleted += 1

        logger.info("Deleted %d sessions for user: %s", deleted, user_id)
        return deleted

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (for in-memory store).

        Returns:
            Number of sessions cleaned up
        """
        if self.redis_client:
            # Redis handles expiration automatically
            return 0

        cleaned = 0
        now = datetime.now(timezone.utc)

        for session_id in list(self._in_memory_store.keys()):
            if self._in_memory_store[session_id].get("_expires_at", now) <= now:
                del self._in_memory_store[session_id]
                cleaned += 1

        if cleaned > 0:
            logger.info("Cleaned up %d expired sessions", cleaned)

        return cleaned

    def get_session_count(self) -> int:
        """
        Get total number of active sessions.

        Returns:
            Session count
        """
        try:
            if self.redis_client:
                # Count keys matching pattern
                return len(list(self.redis_client.scan_iter("session:*")))
            else:
                # Count non-expired sessions in memory
                now = datetime.now(timezone.utc)
                return sum(
                    1
                    for data in self._in_memory_store.values()
                    if data.get("_expires_at", now) > now
                )
        except (ValueError, ConnectionError, AttributeError) as e:
            logger.error("Failed to get session count: %s", e)
            return 0


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager  # pylint: disable=global-statement

    if _session_manager is None:
        _session_manager = SessionManager()

    return _session_manager
