"""Tests for session management using real production code."""

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import pytest

from src.api.sessions import SessionManager, get_session_manager


class TestSessionManager:
    """Test cases for SessionManager with real production code."""

    @pytest.fixture
    def memory_session_manager(self) -> SessionManager:
        """Create SessionManager using in-memory store."""
        return SessionManager(redis_url="memory")

    @pytest.fixture
    def sample_session_data(self) -> Dict[str, Any]:
        """Sample session data for testing."""
        return {
            "username": "test_user",
            "email": "test@example.com",
            "role": "admin",
            "preferences": {"theme": "dark", "language": "en"},
        }

    def test_initialization_memory_mode(self) -> None:
        """Test SessionManager initialization in memory mode."""
        manager = SessionManager(redis_url="memory")
        assert manager.redis_url == "memory"
        assert manager._redis_client is None
        assert manager._in_memory_store == {}

    def test_initialization_redis_mode(self) -> None:
        """Test SessionManager initialization with Redis URL."""
        manager = SessionManager(redis_url="redis://localhost:6379/0")
        assert manager.redis_url == "redis://localhost:6379/0"
        assert manager._redis_client is None
        assert manager._in_memory_store == {}

    def test_initialization_from_env(self) -> None:
        """Test SessionManager initialization from environment variable."""
        # Save current env value
        original_redis_url = os.environ.get("REDIS_URL")

        # Set test value
        os.environ["REDIS_URL"] = "redis://test:6379/0"
        manager = SessionManager()
        assert manager.redis_url == "redis://test:6379/0"

        # Restore original value
        if original_redis_url is None:
            os.environ.pop("REDIS_URL", None)
        else:
            os.environ["REDIS_URL"] = original_redis_url

    def test_redis_client_lazy_initialization_memory_mode(self) -> None:
        """Test Redis client returns None in memory mode."""
        manager = SessionManager(redis_url="memory")
        client = manager.redis_client

        assert client is None
        assert manager.redis_url == "memory"

    def test_redis_client_connection_handling(self) -> None:
        """Test Redis client connection handling."""
        # Test with memory mode explicitly
        manager = SessionManager(redis_url="memory")
        client = manager.redis_client

        assert client is None
        assert manager.redis_url == "memory"

        # Test with localhost Redis (may or may not be available)
        manager2 = SessionManager(redis_url="redis://localhost:6379/0")
        try:
            client2 = manager2.redis_client
            # If Redis is available, client should not be None
            if client2 is not None:
                assert manager2.redis_url == "redis://localhost:6379/0"
        except Exception:
            # If Redis is not available, should fallback to memory
            assert manager2.redis_url == "memory"

    def test_create_session_memory(
        self,
        memory_session_manager: SessionManager,
        sample_session_data: Dict[str, Any],
    ) -> None:
        """Test creating a session in memory store."""
        session_id = "test-session-123"
        user_id = "user-456"

        result = memory_session_manager.create_session(
            session_id, user_id, sample_session_data, ttl_seconds=3600
        )

        assert result is True
        assert session_id in memory_session_manager._in_memory_store

        stored_data = memory_session_manager._in_memory_store[session_id]
        assert stored_data["user_id"] == user_id
        assert stored_data["username"] == "test_user"
        assert stored_data["email"] == "test@example.com"
        assert "created_at" in stored_data
        assert "last_accessed" in stored_data
        assert "_expires_at" in stored_data

    def test_create_session_memory_mode_with_user_tracking(
        self,
        memory_session_manager: SessionManager,
        sample_session_data: Dict[str, Any],
    ) -> None:
        """Test creating a session tracks user sessions properly."""
        session_id1 = "session-1"
        session_id2 = "session-2"
        user_id = "user-789"

        # Create multiple sessions for same user
        result1 = memory_session_manager.create_session(
            session_id1, user_id, sample_session_data, ttl_seconds=3600
        )
        result2 = memory_session_manager.create_session(
            session_id2, user_id, sample_session_data, ttl_seconds=3600
        )

        assert result1 is True
        assert result2 is True

        # Verify both sessions are tracked for the user
        user_sessions = memory_session_manager.get_user_sessions(user_id)
        assert len(user_sessions) == 2
        assert session_id1 in user_sessions
        assert session_id2 in user_sessions

    def test_get_session_memory_valid(
        self,
        memory_session_manager: SessionManager,
        sample_session_data: Dict[str, Any],
    ) -> None:
        """Test getting a valid session from memory store."""
        session_id = "test-session-123"
        user_id = "user-456"

        # Create session first
        memory_session_manager.create_session(
            session_id, user_id, sample_session_data, ttl_seconds=3600
        )

        # Get session
        retrieved = memory_session_manager.get_session(session_id)

        assert retrieved is not None
        assert retrieved["user_id"] == user_id
        assert retrieved["username"] == "test_user"
        assert "_expires_at" not in retrieved  # Internal field should be filtered

    def test_get_session_memory_expired(
        self,
        memory_session_manager: SessionManager,
        sample_session_data: Dict[str, Any],
    ) -> None:
        """Test getting an expired session from memory store."""
        session_id = "test-session-123"
        user_id = "user-456"

        # Create session with very short TTL
        memory_session_manager.create_session(
            session_id, user_id, sample_session_data, ttl_seconds=0
        )

        # Wait a bit
        time.sleep(0.001)

        # Try to get expired session
        retrieved = memory_session_manager.get_session(session_id)

        assert retrieved is None
        assert session_id not in memory_session_manager._in_memory_store

    def test_get_session_nonexistent(
        self, memory_session_manager: SessionManager
    ) -> None:
        """Test getting a nonexistent session."""
        retrieved = memory_session_manager.get_session("nonexistent-id")
        assert retrieved is None

    def test_get_session_memory_updates_last_accessed(
        self,
        memory_session_manager: SessionManager,
        sample_session_data: Dict[str, Any],
    ) -> None:
        """Test getting a session updates last accessed time."""
        session_id = "test-session-123"
        user_id = "user-456"

        # Create session
        memory_session_manager.create_session(
            session_id, user_id, sample_session_data, ttl_seconds=3600
        )

        # Get original last_accessed
        original_session = memory_session_manager._in_memory_store[session_id]
        original_last_accessed = original_session["last_accessed"]

        # Wait a bit
        time.sleep(0.01)

        # Get session (should update last_accessed)
        retrieved = memory_session_manager.get_session(session_id)

        assert retrieved is not None
        new_session = memory_session_manager._in_memory_store[session_id]
        new_last_accessed = new_session["last_accessed"]

        # Verify last_accessed was updated
        assert new_last_accessed > original_last_accessed

    def test_update_session_memory(
        self,
        memory_session_manager: SessionManager,
        sample_session_data: Dict[str, Any],
    ) -> None:
        """Test updating a session in memory store."""
        session_id = "test-session-123"
        user_id = "user-456"

        # Create session
        memory_session_manager.create_session(
            session_id, user_id, sample_session_data, ttl_seconds=3600
        )

        # Update session
        updates = {"role": "superadmin", "new_field": "new_value"}
        result = memory_session_manager.update_session(session_id, updates)

        assert result is True

        # Verify updates
        retrieved = memory_session_manager.get_session(session_id)
        assert retrieved is not None
        assert retrieved["role"] == "superadmin"
        assert retrieved["new_field"] == "new_value"
        assert retrieved["username"] == "test_user"  # Original data preserved

    def test_update_session_nonexistent(
        self, memory_session_manager: SessionManager
    ) -> None:
        """Test updating a nonexistent session."""
        result = memory_session_manager.update_session(
            "nonexistent-id", {"key": "value"}
        )
        assert result is False

    def test_delete_session_memory(
        self,
        memory_session_manager: SessionManager,
        sample_session_data: Dict[str, Any],
    ) -> None:
        """Test deleting a session from memory store."""
        session_id = "test-session-123"
        user_id = "user-456"

        # Create session
        memory_session_manager.create_session(session_id, user_id, sample_session_data)

        # Delete session
        result = memory_session_manager.delete_session(session_id)

        assert result is True
        assert session_id not in memory_session_manager._in_memory_store

    def test_delete_session_nonexistent(
        self, memory_session_manager: SessionManager
    ) -> None:
        """Test deleting a nonexistent session."""
        result = memory_session_manager.delete_session("nonexistent-id")
        assert result is False

    def test_delete_session_removes_from_user_tracking(
        self,
        memory_session_manager: SessionManager,
        sample_session_data: Dict[str, Any],
    ) -> None:
        """Test deleting a session removes it from user tracking."""
        session_id = "test-session-123"
        user_id = "user-456"

        # Create session
        memory_session_manager.create_session(session_id, user_id, sample_session_data)

        # Verify session is tracked
        user_sessions = memory_session_manager.get_user_sessions(user_id)
        assert session_id in user_sessions

        # Delete session
        result = memory_session_manager.delete_session(session_id)

        assert result is True
        # Verify removed from user tracking
        user_sessions = memory_session_manager.get_user_sessions(user_id)
        assert session_id not in user_sessions

    def test_get_user_sessions_memory(
        self,
        memory_session_manager: SessionManager,
        sample_session_data: Dict[str, Any],
    ) -> None:
        """Test getting all sessions for a user from memory store."""
        user_id = "user-456"

        # Create multiple sessions for user
        session_ids = ["session-1", "session-2", "session-3"]
        for sid in session_ids:
            memory_session_manager.create_session(sid, user_id, sample_session_data)

        # Create session for different user
        memory_session_manager.create_session(
            "other-session", "other-user", sample_session_data
        )

        # Get user sessions
        user_sessions = memory_session_manager.get_user_sessions(user_id)

        assert len(user_sessions) == 3
        assert all(sid in user_sessions for sid in session_ids)
        assert "other-session" not in user_sessions

    def test_get_user_sessions_empty_list(
        self, memory_session_manager: SessionManager
    ) -> None:
        """Test getting sessions for user with no sessions."""
        user_sessions = memory_session_manager.get_user_sessions(
            "user-with-no-sessions"
        )

        assert isinstance(user_sessions, list)
        assert len(user_sessions) == 0

    def test_delete_user_sessions(
        self,
        memory_session_manager: SessionManager,
        sample_session_data: Dict[str, Any],
    ) -> None:
        """Test deleting all sessions for a user."""
        user_id = "user-456"

        # Create multiple sessions
        session_ids = ["session-1", "session-2", "session-3"]
        for sid in session_ids:
            memory_session_manager.create_session(sid, user_id, sample_session_data)

        # Delete all user sessions
        deleted_count = memory_session_manager.delete_user_sessions(user_id)

        assert deleted_count == 3
        assert memory_session_manager.get_user_sessions(user_id) == []

    def test_cleanup_expired_sessions_memory(
        self,
        memory_session_manager: SessionManager,
        sample_session_data: Dict[str, Any],
    ) -> None:
        """Test cleanup of expired sessions in memory store."""
        # Create sessions with different TTLs
        memory_session_manager.create_session(
            "valid-1", "user-1", sample_session_data, ttl_seconds=3600
        )
        memory_session_manager.create_session(
            "expired-1", "user-2", sample_session_data, ttl_seconds=0
        )
        time.sleep(0.001)
        memory_session_manager.create_session(
            "valid-2", "user-3", sample_session_data, ttl_seconds=3600
        )
        memory_session_manager.create_session(
            "expired-2", "user-4", sample_session_data, ttl_seconds=0
        )

        # Run cleanup
        cleaned = memory_session_manager.cleanup_expired_sessions()

        assert cleaned == 2
        assert "valid-1" in memory_session_manager._in_memory_store
        assert "valid-2" in memory_session_manager._in_memory_store
        assert "expired-1" not in memory_session_manager._in_memory_store
        assert "expired-2" not in memory_session_manager._in_memory_store

    def test_cleanup_expired_sessions_redis_or_memory(self) -> None:
        """Test cleanup behavior with Redis URL."""
        manager = SessionManager(redis_url="redis://localhost:6379/0")

        # Trigger connection attempt
        _ = manager.redis_client

        # Check connection status
        if manager.redis_url == "redis://localhost:6379/0":
            # Redis is available - cleanup returns 0 (Redis handles expiration)
            cleaned = manager.cleanup_expired_sessions()
            assert cleaned == 0
        else:
            # Redis not available - using memory mode
            assert manager.redis_url == "memory"
            # Add some test data to memory store
            manager._in_memory_store["test"] = {
                "_expires_at": datetime.now(timezone.utc) - timedelta(seconds=1)
            }

            cleaned = manager.cleanup_expired_sessions()
            assert cleaned == 1

    def test_get_session_count_memory(
        self,
        memory_session_manager: SessionManager,
        sample_session_data: Dict[str, Any],
    ) -> None:
        """Test getting session count from memory store."""
        # Create mix of valid and expired sessions
        memory_session_manager.create_session(
            "valid-1", "user-1", sample_session_data, ttl_seconds=3600
        )
        memory_session_manager.create_session(
            "valid-2", "user-2", sample_session_data, ttl_seconds=3600
        )
        memory_session_manager.create_session(
            "expired", "user-3", sample_session_data, ttl_seconds=0
        )

        count = memory_session_manager.get_session_count()
        assert count == 2  # Only valid sessions

    def test_get_session_count_excludes_expired(
        self,
        memory_session_manager: SessionManager,
        sample_session_data: Dict[str, Any],
    ) -> None:
        """Test session count excludes expired sessions."""
        # Create mix of valid and expired sessions
        memory_session_manager.create_session(
            "valid-1", "user-1", sample_session_data, ttl_seconds=3600
        )
        memory_session_manager.create_session(
            "expired-1", "user-2", sample_session_data, ttl_seconds=0
        )
        time.sleep(0.001)
        memory_session_manager.create_session(
            "valid-2", "user-3", sample_session_data, ttl_seconds=3600
        )

        # Count should exclude expired
        count = memory_session_manager.get_session_count()
        assert count == 2

    def test_session_ttl_extension(
        self,
        memory_session_manager: SessionManager,
        sample_session_data: Dict[str, Any],
    ) -> None:
        """Test that session TTL is extended on update."""
        session_id = "test-session"
        user_id = "user-123"

        # Create session
        memory_session_manager.create_session(
            session_id, user_id, sample_session_data, ttl_seconds=60
        )

        # Get original expiration
        original_expires = memory_session_manager._in_memory_store[session_id][
            "_expires_at"
        ]

        # Wait a bit
        time.sleep(0.1)

        # Update session (should extend TTL)
        memory_session_manager.update_session(
            session_id, {"updated": True}, extend_ttl=True
        )

        # Check new expiration is later
        new_expires = memory_session_manager._in_memory_store[session_id]["_expires_at"]
        assert new_expires > original_expires

    def test_session_no_ttl_extension(
        self,
        memory_session_manager: SessionManager,
        sample_session_data: Dict[str, Any],
    ) -> None:
        """Test that session TTL is not extended when disabled."""
        session_id = "test-session"
        user_id = "user-123"

        # Create session
        memory_session_manager.create_session(
            session_id, user_id, sample_session_data, ttl_seconds=60
        )

        # Get original expiration
        original_expires = memory_session_manager._in_memory_store[session_id][
            "_expires_at"
        ]

        # Update session without extending TTL
        memory_session_manager.update_session(
            session_id, {"updated": True}, extend_ttl=False
        )

        # Check expiration unchanged
        new_expires = memory_session_manager._in_memory_store[session_id]["_expires_at"]
        assert new_expires == original_expires


class TestGlobalSessionManager:
    """Test cases for global session manager."""

    def test_get_session_manager_singleton(self) -> None:
        """Test that get_session_manager returns singleton instance."""
        manager1 = get_session_manager()
        manager2 = get_session_manager()

        assert manager1 is manager2
        assert isinstance(manager1, SessionManager)

    def test_get_session_manager_initialization(self) -> None:
        """Test global session manager initialization."""
        # Reset global instance
        import src.api.sessions

        src.api.sessions._session_manager = None

        manager = get_session_manager()
        assert isinstance(manager, SessionManager)
        assert src.api.sessions._session_manager is manager
