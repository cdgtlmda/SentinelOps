"""
Test suite for api/auth.py.
CRITICAL: Uses REAL production code - NO MOCKING.
Achieves minimum 90% statement coverage.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
import pytest
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials

from src.api.auth import (
    APIKey,
    AuthenticationBackend,
    Scopes,
    TokenData,
    get_api_key,
    get_auth_backend,
    get_current_token,
    require_auth,
    require_scopes,
)
from src.api.exceptions import AuthenticationException, AuthorizationException


class TestTokenData:
    """Test TokenData model."""

    def test_token_data_creation_minimal(self) -> None:
        """Test creating TokenData with minimal fields."""
        now = datetime.now(timezone.utc)
        token_data = TokenData(
            sub="user123",
            exp=now + timedelta(hours=1),
            iat=now,
            jti="token123",
        )

        assert token_data.sub == "user123"
        assert token_data.type == "access"
        assert token_data.scopes == []
        assert token_data.metadata == {}
        assert token_data.jti == "token123"

    def test_token_data_creation_full(self) -> None:
        """Test creating TokenData with all fields."""
        now = datetime.now(timezone.utc)
        exp = now + timedelta(hours=1)
        scopes = ["read", "write"]
        metadata = {"role": "admin"}

        token_data = TokenData(
            sub="user456",
            exp=exp,
            iat=now,
            jti="token456",
            type="refresh",
            scopes=scopes,
            metadata=metadata,
        )

        assert token_data.sub == "user456"
        assert token_data.exp == exp
        assert token_data.iat == now
        assert token_data.jti == "token456"
        assert token_data.type == "refresh"
        assert token_data.scopes == scopes
        assert token_data.metadata == metadata


class TestAPIKey:
    """Test APIKey model."""

    def test_api_key_creation_minimal(self) -> None:
        """Test creating APIKey with minimal fields."""
        now = datetime.now(timezone.utc)
        api_key = APIKey(
            key_hash="hash123",
            name="test-key",
            created_at=now,
        )

        assert api_key.key_hash == "hash123"
        assert api_key.name == "test-key"
        assert api_key.created_at == now
        assert api_key.expires_at is None
        assert api_key.scopes == []
        assert api_key.is_active is True
        assert api_key.metadata == {}

    def test_api_key_creation_full(self) -> None:
        """Test creating APIKey with all fields."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=30)
        scopes = ["admin:read", "admin:write"]
        metadata = {"department": "security"}

        api_key = APIKey(
            key_hash="hash456",
            name="admin-key",
            created_at=now,
            expires_at=expires,
            scopes=scopes,
            is_active=False,
            metadata=metadata,
        )

        assert api_key.key_hash == "hash456"
        assert api_key.name == "admin-key"
        assert api_key.created_at == now
        assert api_key.expires_at == expires
        assert api_key.scopes == scopes
        assert api_key.is_active is False
        assert api_key.metadata == metadata


class TestAuthenticationBackend:
    """Test AuthenticationBackend class."""

    @pytest.fixture
    def backend(self) -> AuthenticationBackend:
        """Create fresh authentication backend for each test."""
        return AuthenticationBackend()

    def test_initialization(self, backend: AuthenticationBackend) -> None:
        """Test backend initialization."""
        assert backend.config is not None
        assert isinstance(backend._api_keys, dict)
        assert isinstance(backend._revoked_tokens, set)
        assert len(backend._api_keys) == 0
        assert len(backend._revoked_tokens) == 0

    def test_hash_api_key_consistent(self, backend: AuthenticationBackend) -> None:
        """Test API key hashing is consistent."""
        key = "test-key-123"
        hash1 = backend._hash_api_key(key)
        hash2 = backend._hash_api_key(key)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest length

    def test_hash_api_key_different_keys(self, backend: AuthenticationBackend) -> None:
        """Test different keys produce different hashes."""
        key1 = "test-key-123"
        key2 = "test-key-456"
        hash1 = backend._hash_api_key(key1)
        hash2 = backend._hash_api_key(key2)
        assert hash1 != hash2

    def test_generate_api_key_basic(self, backend: AuthenticationBackend) -> None:
        """Test basic API key generation."""
        key = backend.generate_api_key("test-key")

        # Key should be returned as string
        assert isinstance(key, str)
        assert len(key) > 20  # Should be substantial length

        # Key should be stored in backend
        assert len(backend._api_keys) == 1

        # Should be able to verify the key
        api_key = backend.verify_api_key(key)
        assert api_key is not None
        assert api_key.name == "test-key"
        assert api_key.is_active is True
        assert api_key.scopes == []

    def test_generate_api_key_with_scopes(self, backend: AuthenticationBackend) -> None:
        """Test API key generation with scopes."""
        scopes = ["read", "write", "admin"]
        key = backend.generate_api_key("admin-key", scopes=scopes)

        api_key = backend.verify_api_key(key)
        assert api_key is not None
        assert api_key.name == "admin-key"
        assert api_key.scopes == scopes

    def test_verify_api_key_invalid(self, backend: AuthenticationBackend) -> None:
        """Test verifying invalid API key."""
        result = backend.verify_api_key("invalid-key")
        assert result is None

    def test_verify_api_key_inactive(self, backend: AuthenticationBackend) -> None:
        """Test verifying inactive API key."""
        key = backend.generate_api_key("test-key")
        key_hash = backend._hash_api_key(key)

        # Make key inactive
        backend._api_keys[key_hash].is_active = False

        result = backend.verify_api_key(key)
        assert result is None

    def test_verify_api_key_expired(self, backend: AuthenticationBackend) -> None:
        """Test verifying expired API key."""
        key = backend.generate_api_key("test-key")
        key_hash = backend._hash_api_key(key)

        # Set expiration in the past
        backend._api_keys[key_hash].expires_at = datetime.now(timezone.utc) - timedelta(
            hours=1
        )

        result = backend.verify_api_key(key)
        assert result is None

    def test_verify_api_key_not_yet_expired(
        self, backend: AuthenticationBackend
    ) -> None:
        """Test verifying API key that hasn't expired yet."""
        key = backend.generate_api_key("test-key")
        key_hash = backend._hash_api_key(key)

        # Set expiration in the future
        backend._api_keys[key_hash].expires_at = datetime.now(timezone.utc) + timedelta(
            hours=1
        )

        result = backend.verify_api_key(key)
        assert result is not None
        assert result.name == "test-key"

    def test_create_access_token_basic(self, backend: AuthenticationBackend) -> None:
        """Test basic access token creation."""
        token = backend.create_access_token("user123")

        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are substantial length

        # Should be able to verify the token
        token_data = backend.verify_token(token)
        assert token_data is not None
        assert token_data.sub == "user123"
        assert token_data.type == "access"
        assert token_data.scopes == []
        assert token_data.metadata == {}

    def test_create_access_token_with_scopes(
        self, backend: AuthenticationBackend
    ) -> None:
        """Test access token creation with scopes."""
        scopes = ["read", "write"]
        token = backend.create_access_token("user456", scopes=scopes)

        token_data = backend.verify_token(token)
        assert token_data is not None
        assert token_data.sub == "user456"
        assert token_data.scopes == scopes

    def test_create_access_token_with_metadata(
        self, backend: AuthenticationBackend
    ) -> None:
        """Test access token creation with metadata."""
        metadata = {"role": "admin", "department": "security"}
        token = backend.create_access_token("user789", metadata=metadata)

        token_data = backend.verify_token(token)
        assert token_data is not None
        assert token_data.sub == "user789"
        assert token_data.metadata == metadata

    def test_create_access_token_with_expiration(
        self, backend: AuthenticationBackend
    ) -> None:
        """Test access token creation with custom expiration."""
        expires_delta = timedelta(minutes=5)
        token = backend.create_access_token("user123", expires_delta=expires_delta)

        token_data = backend.verify_token(token)
        assert token_data is not None

        # Check expiration is approximately correct (within 10 seconds)
        expected_exp = datetime.now(timezone.utc) + expires_delta
        time_diff = abs((token_data.exp - expected_exp).total_seconds())
        assert time_diff < 10

    def test_verify_token_invalid(self, backend: AuthenticationBackend) -> None:
        """Test verifying invalid token."""
        result = backend.verify_token("invalid-token")
        assert result is None

    def test_verify_token_malformed(self, backend: AuthenticationBackend) -> None:
        """Test verifying malformed token."""
        result = backend.verify_token("not.a.jwt.token")
        assert result is None

    def test_verify_token_wrong_secret(self, backend: AuthenticationBackend) -> None:
        """Test verifying token with wrong secret."""
        # Create token with different secret
        payload = {
            "sub": "user123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
            "jti": "test123",
        }
        wrong_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        result = backend.verify_token(wrong_token)
        assert result is None

    def test_verify_token_expired(self, backend: AuthenticationBackend) -> None:
        """Test verifying expired token."""
        # Create token that expires immediately
        token = backend.create_access_token(
            "user123", expires_delta=timedelta(seconds=-1)
        )

        result = backend.verify_token(token)
        assert result is None

    def test_revoke_token_valid(self, backend: AuthenticationBackend) -> None:
        """Test revoking valid token."""
        token = backend.create_access_token("user123")

        # Token should work initially
        token_data = backend.verify_token(token)
        assert token_data is not None

        # Revoke token
        result = backend.revoke_token(token)
        assert result is True

        # Token should no longer work
        token_data = backend.verify_token(token)
        assert token_data is None

    def test_revoke_token_invalid(self, backend: AuthenticationBackend) -> None:
        """Test revoking invalid token."""
        result = backend.revoke_token("invalid-token")
        assert result is False

    def test_revoke_token_already_revoked(self, backend: AuthenticationBackend) -> None:
        """Test revoking already revoked token."""
        token = backend.create_access_token("user123")

        # Revoke once
        result1 = backend.revoke_token(token)
        assert result1 is True

        # Try to revoke again
        result2 = backend.revoke_token(token)
        assert result2 is False

    def test_multiple_api_keys(self, backend: AuthenticationBackend) -> None:
        """Test managing multiple API keys."""
        key1 = backend.generate_api_key("key1", scopes=["read"])
        key2 = backend.generate_api_key("key2", scopes=["write"])
        key3 = backend.generate_api_key("key3", scopes=["admin"])

        assert len(backend._api_keys) == 3

        # All keys should verify correctly
        api_key1 = backend.verify_api_key(key1)
        api_key2 = backend.verify_api_key(key2)
        api_key3 = backend.verify_api_key(key3)

        assert api_key1 is not None
        assert api_key1.name == "key1"
        assert api_key1.scopes == ["read"]
        assert api_key2 is not None
        assert api_key2.name == "key2"
        assert api_key2.scopes == ["write"]
        assert api_key3 is not None
        assert api_key3.name == "key3"
        assert api_key3.scopes == ["admin"]

    def test_multiple_tokens(self, backend: AuthenticationBackend) -> None:
        """Test managing multiple tokens."""
        token1 = backend.create_access_token("user1", scopes=["read"])
        token2 = backend.create_access_token("user2", scopes=["write"])

        # Both tokens should verify
        token_data1 = backend.verify_token(token1)
        token_data2 = backend.verify_token(token2)

        assert token_data1 is not None
        assert token_data1.sub == "user1"
        assert token_data1.scopes == ["read"]
        assert token_data2 is not None
        assert token_data2.sub == "user2"
        assert token_data2.scopes == ["write"]

        # Revoke one token
        backend.revoke_token(token1)

        # First should be invalid, second should still work
        assert backend.verify_token(token1) is None
        assert backend.verify_token(token2) is not None


class TestGlobalFunctions:
    """Test global authentication functions."""

    def test_get_auth_backend(self) -> None:
        """Test getting global auth backend."""
        backend = get_auth_backend()
        assert isinstance(backend, AuthenticationBackend)

        # Should return same instance
        backend2 = get_auth_backend()
        assert backend is backend2

    @pytest.mark.asyncio
    async def test_get_current_token_no_credentials(self) -> None:
        """Test get_current_token with no credentials."""
        # The function checks if not credentials, so passing None should work
        # but we need to handle the fact that Security(bearer_scheme) is the default
        # Let's test by creating a TestClient and making a request without auth
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        @app.get("/test")
        async def test_endpoint(
            token_data: Optional[TokenData] = Depends(get_current_token),
        ) -> dict[str, Any]:
            return {"token": token_data}

        client = TestClient(app)
        response = client.get("/test")  # No auth header
        assert response.status_code == 200
        assert response.json()["token"] is None

    @pytest.mark.asyncio
    async def test_get_current_token_valid_token(self) -> None:
        """Test get_current_token with valid token."""
        backend = get_auth_backend()
        token = backend.create_access_token("user123", scopes=["read"])

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        result = await get_current_token(credentials)

        assert result is not None
        assert result.sub == "user123"
        assert result.scopes == ["read"]

    @pytest.mark.asyncio
    async def test_get_current_token_invalid_token(self) -> None:
        """Test get_current_token with invalid token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid"
        )

        with pytest.raises(AuthenticationException) as exc_info:
            await get_current_token(credentials)

        assert "Invalid or expired token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_api_key_none(self) -> None:
        """Test get_api_key with no key."""
        result = await get_api_key(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_api_key_valid(self) -> None:
        """Test get_api_key with valid key."""
        backend = get_auth_backend()
        key = backend.generate_api_key("test-key", scopes=["write"])

        result = await get_api_key(key)

        assert result is not None
        assert result.name == "test-key"
        assert result.scopes == ["write"]

    @pytest.mark.asyncio
    async def test_get_api_key_invalid(self) -> None:
        """Test get_api_key with invalid key."""
        with pytest.raises(AuthenticationException) as exc_info:
            await get_api_key("invalid-key")

        assert "Invalid API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_require_auth_with_token(self) -> None:
        """Test require_auth with valid token."""
        backend = get_auth_backend()
        token = backend.create_access_token(
            "user123", scopes=["read"], metadata={"role": "user"}
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        token_data = await get_current_token(credentials)

        result = await require_auth(token_data=token_data, api_key=None)

        assert result["type"] == "token"
        assert result["subject"] == "user123"
        assert result["scopes"] == ["read"]
        assert result["metadata"] == {"role": "user"}

    @pytest.mark.asyncio
    async def test_require_auth_with_api_key(self) -> None:
        """Test require_auth with valid API key."""
        backend = get_auth_backend()
        key = backend.generate_api_key("test-key", scopes=["write"])
        api_key = await get_api_key(key)

        result = await require_auth(token_data=None, api_key=api_key)

        assert result["type"] == "api_key"
        assert result["subject"] == "test-key"
        assert result["scopes"] == ["write"]
        assert result["metadata"] == {}

    @pytest.mark.asyncio
    async def test_require_auth_no_authentication(self) -> None:
        """Test require_auth with no authentication."""
        with pytest.raises(AuthenticationException) as exc_info:
            await require_auth(token_data=None, api_key=None)

        assert "Authentication required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_require_scopes_sufficient_permissions(self) -> None:
        """Test require_scopes with sufficient permissions."""
        required_scopes = ["read", "write"]
        scope_checker = require_scopes(required_scopes)

        # Mock auth with sufficient scopes
        auth = {
            "type": "token",
            "subject": "user123",
            "scopes": ["read", "write", "admin"],
            "metadata": {},
        }

        # Should not raise exception
        result = await scope_checker(auth)
        assert result is None

    @pytest.mark.asyncio
    async def test_require_scopes_insufficient_permissions(self) -> None:
        """Test require_scopes with insufficient permissions."""
        required_scopes = ["admin", "delete"]
        scope_checker = require_scopes(required_scopes)

        # Mock auth with insufficient scopes
        auth = {
            "type": "token",
            "subject": "user123",
            "scopes": ["read", "write"],
            "metadata": {},
        }

        with pytest.raises(AuthorizationException) as exc_info:
            await scope_checker(auth)

        error_message = str(exc_info.value)
        assert "Missing required scopes" in error_message
        assert "admin" in error_message or "delete" in error_message

    @pytest.mark.asyncio
    async def test_require_scopes_exact_match(self) -> None:
        """Test require_scopes with exact scope match."""
        required_scopes = ["read", "write"]
        scope_checker = require_scopes(required_scopes)

        # Mock auth with exact scopes
        auth = {
            "type": "api_key",
            "subject": "test-key",
            "scopes": ["read", "write"],
            "metadata": {},
        }

        # Should not raise exception
        result = await scope_checker(auth)
        assert result is None

    @pytest.mark.asyncio
    async def test_require_scopes_no_scopes_required(self) -> None:
        """Test require_scopes with no scopes required."""
        required_scopes: list[str] = []
        scope_checker = require_scopes(required_scopes)

        # Mock auth with any scopes
        auth = {
            "type": "token",
            "subject": "user123",
            "scopes": ["anything"],
            "metadata": {},
        }

        # Should not raise exception
        result = await scope_checker(auth)
        assert result is None

    @pytest.mark.asyncio
    async def test_require_scopes_no_user_scopes(self) -> None:
        """Test require_scopes when user has no scopes."""
        required_scopes: list[str] = ["read"]
        scope_checker = require_scopes(required_scopes)

        # Mock auth with no scopes
        auth = {"type": "token", "subject": "user123", "scopes": [], "metadata": {}}

        with pytest.raises(AuthorizationException) as exc_info:
            await scope_checker(auth)

        assert "Missing required scopes: read" in str(exc_info.value)


class TestScopes:
    """Test Scopes class constants."""

    def test_read_permissions(self) -> None:
        """Test read permission scopes."""
        assert Scopes.INCIDENTS_READ == "incidents:read"
        assert Scopes.AGENTS_READ == "agents:read"
        assert Scopes.LOGS_READ == "logs:read"
        assert Scopes.METRICS_READ == "metrics:read"

    def test_write_permissions(self) -> None:
        """Test write permission scopes."""
        assert Scopes.INCIDENTS_WRITE == "incidents:write"
        assert Scopes.AGENTS_WRITE == "agents:write"
        assert Scopes.REMEDIATION_EXECUTE == "remediation:execute"

    def test_admin_permissions(self) -> None:
        """Test admin permission scopes."""
        assert Scopes.ADMIN_READ == "admin:read"
        assert Scopes.ADMIN_WRITE == "admin:write"
        assert Scopes.ADMIN_DELETE == "admin:delete"

    def test_service_permissions(self) -> None:
        """Test service account scopes."""
        assert Scopes.SERVICE_AGENT == "service:agent"
        assert Scopes.SERVICE_ORCHESTRATOR == "service:orchestrator"

    def test_all_scopes_are_strings(self) -> None:
        """Test all scope constants are strings."""
        scope_attrs = [attr for attr in dir(Scopes) if not attr.startswith("_")]
        for attr_name in scope_attrs:
            scope_value = getattr(Scopes, attr_name)
            assert isinstance(scope_value, str)
            assert ":" in scope_value  # Should follow namespace:action pattern


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components."""

    @pytest.mark.asyncio
    async def test_end_to_end_token_authentication(self) -> None:
        """Test complete token authentication workflow."""
        # Create token
        backend = get_auth_backend()
        token = backend.create_access_token(
            "admin_user",
            scopes=[Scopes.ADMIN_READ, Scopes.ADMIN_WRITE],
            metadata={"role": "administrator"},
        )

        # Simulate FastAPI request authentication
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        token_data = await get_current_token(credentials)

        # Require authentication
        auth = await require_auth(token_data=token_data, api_key=None)

        # Verify authentication result
        assert auth["type"] == "token"
        assert auth["subject"] == "admin_user"
        assert Scopes.ADMIN_READ in auth["scopes"]
        assert Scopes.ADMIN_WRITE in auth["scopes"]
        assert auth["metadata"]["role"] == "administrator"

        # Test scope requirement
        admin_scope_checker = require_scopes([Scopes.ADMIN_READ])
        result = await admin_scope_checker(auth)
        assert result is None  # Should pass

    @pytest.mark.asyncio
    async def test_end_to_end_api_key_authentication(self) -> None:
        """Test complete API key authentication workflow."""
        # Create API key
        backend = get_auth_backend()
        key = backend.generate_api_key(
            "service_bot", scopes=[Scopes.INCIDENTS_READ, Scopes.INCIDENTS_WRITE]
        )

        # Simulate FastAPI request authentication
        api_key = await get_api_key(key)

        # Require authentication
        auth = await require_auth(token_data=None, api_key=api_key)

        # Verify authentication result
        assert auth["type"] == "api_key"
        assert auth["subject"] == "service_bot"
        assert Scopes.INCIDENTS_READ in auth["scopes"]
        assert Scopes.INCIDENTS_WRITE in auth["scopes"]

        # Test scope requirement
        incident_scope_checker = require_scopes([Scopes.INCIDENTS_READ])
        result = await incident_scope_checker(auth)
        assert result is None  # Should pass

        # Test insufficient scope
        admin_scope_checker = require_scopes([Scopes.ADMIN_DELETE])
        with pytest.raises(AuthorizationException):
            await admin_scope_checker(auth)

    @pytest.mark.asyncio
    async def test_token_lifecycle_management(self) -> None:
        """Test complete token lifecycle."""
        backend = get_auth_backend()

        # Create token
        token = backend.create_access_token("user123", scopes=["read"])

        # Verify token works
        token_data = backend.verify_token(token)
        assert token_data is not None
        assert token_data.sub == "user123"

        # Use token for authentication
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        verified_token = await get_current_token(credentials)
        assert verified_token is not None
        assert verified_token.sub == "user123"

        # Revoke token
        revoked = backend.revoke_token(token)
        assert revoked is True

        # Token should no longer work
        with pytest.raises(AuthenticationException):
            await get_current_token(credentials)

    def test_api_key_security_features(self) -> None:
        """Test API key security features."""
        # Use fresh backend to avoid interference from global state
        backend = AuthenticationBackend()

        # Generate key
        key = backend.generate_api_key("security-test")

        # Key should be returned only once
        assert isinstance(key, str)
        assert len(key) > 20

        # Key should be hashed for storage
        key_hash = backend._hash_api_key(key)

        # Should have exactly one key stored
        assert len(backend._api_keys) == 1

        # Get the stored key (should be the one we just created)
        stored_key = list(backend._api_keys.values())[0]
        assert stored_key.key_hash == key_hash
        assert stored_key.name == "security-test"

        # Original key should not be stored anywhere
        for api_key in backend._api_keys.values():
            assert key not in str(api_key.__dict__)

        # Hash should be consistent
        hash1 = backend._hash_api_key(key)
        hash2 = backend._hash_api_key(key)
        assert hash1 == hash2

        # Different keys should produce different hashes
        key2 = backend.generate_api_key("different-key")
        hash_key2 = backend._hash_api_key(key2)
        assert hash1 != hash_key2

    def test_environment_dependent_behavior(self) -> None:
        """Test behavior that depends on environment variables."""
        # Test salt usage in hashing
        backend = get_auth_backend()
        key = "test-key"

        # Hash should incorporate salt from environment
        original_salt = os.getenv("API_KEY_SALT")
        try:
            # Test with custom salt
            os.environ["API_KEY_SALT"] = "test-salt-123"
            hash_with_custom_salt = backend._hash_api_key(key)

            # Test with different salt
            os.environ["API_KEY_SALT"] = "different-salt"
            hash_with_different_salt = backend._hash_api_key(key)

            # Should produce different hashes
            assert hash_with_custom_salt != hash_with_different_salt

        finally:
            # Restore original salt
            if original_salt is not None:
                os.environ["API_KEY_SALT"] = original_salt
            elif "API_KEY_SALT" in os.environ:
                del os.environ["API_KEY_SALT"]
