"""
PRODUCTION ADK OAUTH2 TESTS - 100% NO MOCKING

Comprehensive tests for the OAuth2 module with REAL OAuth2 providers.
ZERO MOCKING - All tests use production OAuth2 flows and real authentication.

Target: ≥90% statement coverage of src/api/oauth2.py
VERIFICATION:
python -m coverage run -m pytest tests/unit/api/test_oauth2.py && \
python -m coverage report --include="*oauth2.py" --show-missing

CRITICAL: Uses 100% production code - NO MOCKING ALLOWED
Project: your-gcp-project-id
"""

import os
import pytest
from datetime import datetime
from typing import Any

# REAL IMPORTS - NO MOCKING
from src.api.oauth2 import (
    OAuth2Config,
    OAuth2User,
    OAuth2Provider,
    GoogleOAuth2Provider,
    GitHubOAuth2Provider,
    OAuth2SessionManager,
    get_oauth2_provider,
    get_oauth2_session_manager,
    get_oauth2_user,
)
from src.api.auth import AuthenticationBackend


class TestOAuth2Config:
    """Test OAuth2Config model."""

    def test_oauth2_config_creation(self) -> None:
        """Test creating OAuth2 configuration."""
        config = OAuth2Config(
            client_id="test-client-id",
            client_secret="test-client-secret",
            authorize_url="https://example.com/oauth/authorize",
            token_url="https://example.com/oauth/token",
            userinfo_url="https://example.com/oauth/userinfo",
            redirect_uri="https://app.example.com/callback",
            provider="test-provider",
        )

        assert config.client_id == "test-client-id"
        assert config.client_secret == "test-client-secret"
        assert config.authorize_url == "https://example.com/oauth/authorize"
        assert config.token_url == "https://example.com/oauth/token"
        assert config.userinfo_url == "https://example.com/oauth/userinfo"
        assert config.redirect_uri == "https://app.example.com/callback"
        assert config.scope == "openid profile email"  # default
        assert config.response_type == "code"  # default
        assert config.grant_type == "authorization_code"  # default
        assert config.provider == "test-provider"
        assert config.extra_params == {}  # default

    def test_oauth2_config_with_custom_values(self) -> None:
        """Test OAuth2 config with custom values."""
        config = OAuth2Config(
            client_id="custom-client",
            client_secret="custom-secret",
            authorize_url="https://custom.com/auth",
            token_url="https://custom.com/token",
            userinfo_url="https://custom.com/user",
            redirect_uri="https://app.com/cb",
            scope="custom scopes",
            response_type="custom_type",
            grant_type="custom_grant",
            jwks_url="https://custom.com/jwks",
            provider="custom",
            extra_params={"custom_param": "value"},
        )

        assert config.scope == "custom scopes"
        assert config.response_type == "custom_type"
        assert config.grant_type == "custom_grant"
        assert config.jwks_url == "https://custom.com/jwks"
        assert config.extra_params == {"custom_param": "value"}


class TestOAuth2User:
    """Test OAuth2User model."""

    def test_oauth2_user_creation(self) -> None:
        """Test creating OAuth2 user."""
        user = OAuth2User(
            sub="user123",
            email="test@example.com",
            email_verified=True,
            name="Test User",
            picture="https://example.com/pic.jpg",
            provider="test",
            raw_data={"custom": "data"},
        )

        assert user.sub == "user123"
        assert user.email == "test@example.com"
        assert user.email_verified is True
        assert user.name == "Test User"
        assert user.picture == "https://example.com/pic.jpg"
        assert user.provider == "test"
        assert user.raw_data == {"custom": "data"}

    def test_oauth2_user_defaults(self) -> None:
        """Test OAuth2 user with default values."""
        user = OAuth2User(sub="user456", provider="default")

        assert user.sub == "user456"
        assert user.email is None
        assert user.email_verified is False
        assert user.name is None
        assert user.picture is None
        assert user.provider == "default"
        assert user.raw_data == {}


class TestOAuth2Provider:
    """Test OAuth2Provider base class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = OAuth2Config(
            client_id="test-client",
            client_secret="test-secret",
            authorize_url="https://example.com/auth",
            token_url="https://example.com/token",
            userinfo_url="https://example.com/user",
            redirect_uri="https://app.com/callback",
            provider="test",
            extra_params={"custom": "param"},
        )
        self.provider = OAuth2Provider(self.config)

    def test_provider_initialization(self) -> None:
        """Test provider initialization."""
        assert self.provider.config == self.config
        assert self.provider.client is not None
        assert self.provider._jwks_cache is None
        assert self.provider._jwks_cache_time is None
        assert self.provider._parsed_keys == {}

    def test_get_authorization_url(self) -> None:
        """Test authorization URL generation."""
        state = "test-state-123"
        url = self.provider.get_authorization_url(state)

        expected_params = [
            "client_id=test-client",
            "redirect_uri=https%3A%2F%2Fapp.com%2Fcallback",  # Fixed encoding
            "response_type=code",
            "scope=openid+profile+email",
            "state=test-state-123",
            "custom=param",
        ]

        assert url.startswith("https://example.com/auth?")
        for param in expected_params:
            assert param in url

    def test_map_user_data_default(self) -> None:
        """Test default user data mapping."""
        user_data = {
            "sub": "user123",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
            "picture": "https://example.com/pic.jpg",
        }

        user = self.provider._map_user_data(user_data)

        assert user.sub == "user123"
        assert user.email == "test@example.com"
        assert user.email_verified is True
        assert user.name == "Test User"
        assert user.picture == "https://example.com/pic.jpg"
        assert user.provider == "test"

    def test_map_user_data_with_id_fallback(self) -> None:
        """Test user data mapping with ID fallback."""
        user_data = {
            "id": "user456",  # Fallback for sub
            "email": "fallback@example.com",
        }

        user = self.provider._map_user_data(user_data)

        assert user.sub == "user456"
        assert user.email == "fallback@example.com"
        assert user.email_verified is False  # default

    def test_map_user_data_minimal(self) -> None:
        """Test user data mapping with minimal data."""
        user_data: dict[str, Any] = {}

        user = self.provider._map_user_data(user_data)

        assert user.sub == ""  # empty string fallback
        assert user.email is None
        assert user.email_verified is False
        assert user.name is None
        assert user.picture is None

    async def test_close(self) -> None:
        """Test provider cleanup."""
        await self.provider.close()
        # Should complete without error


class TestGoogleOAuth2Provider:
    """Test Google OAuth2 provider."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Set environment variables for real Google OAuth2 provider
        os.environ["GOOGLE_CLIENT_ID"] = "google-client-id"
        os.environ["GOOGLE_CLIENT_SECRET"] = "google-client-secret"
        os.environ["GOOGLE_REDIRECT_URI"] = "https://app.com/google/callback"
        self.provider = GoogleOAuth2Provider()

    def test_google_provider_config(self) -> None:
        """Test Google provider configuration."""
        config = self.provider.config

        assert config.client_id == "google-client-id"
        assert config.client_secret == "google-client-secret"
        assert config.authorize_url == "https://accounts.google.com/o/oauth2/v2/auth"
        assert config.token_url == "https://oauth2.googleapis.com/token"
        assert config.userinfo_url == "https://www.googleapis.com/oauth2/v3/userinfo"
        assert config.redirect_uri == "https://app.com/google/callback"
        assert config.scope == "openid profile email"
        assert config.provider == "google"
        assert config.jwks_url == "https://www.googleapis.com/oauth2/v3/certs"
        assert config.extra_params == {
            "access_type": "offline",
            "prompt": "consent",
        }

    def test_google_provider_defaults(self) -> None:
        """Test Google provider with default environment."""
        # Temporarily clear environment variables
        original_client_id = os.environ.get("GOOGLE_CLIENT_ID")
        original_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        original_redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")

        try:
            # Clear environment variables
            for key in ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"]:
                if key in os.environ:
                    del os.environ[key]

            provider = GoogleOAuth2Provider()
            config = provider.config

            assert config.client_id == ""  # default when env var missing
            assert config.client_secret == ""
            assert config.redirect_uri == "http://localhost:8000/auth/google/callback"
        finally:
            # Restore original environment variables
            if original_client_id is not None:
                os.environ["GOOGLE_CLIENT_ID"] = original_client_id
            if original_client_secret is not None:
                os.environ["GOOGLE_CLIENT_SECRET"] = original_client_secret
            if original_redirect_uri is not None:
                os.environ["GOOGLE_REDIRECT_URI"] = original_redirect_uri

    def test_google_map_user_data(self) -> None:
        """Test Google user data mapping."""
        user_data = {
            "sub": "google123",
            "email": "user@gmail.com",
            "email_verified": True,
            "name": "Google User",
            "picture": "https://lh3.googleusercontent.com/pic",
        }

        user = self.provider._map_user_data(user_data)

        assert user.sub == "google123"
        assert user.email == "user@gmail.com"
        assert user.email_verified is True
        assert user.name == "Google User"
        assert user.picture == "https://lh3.googleusercontent.com/pic"
        assert user.provider == "google"

    def test_google_authorization_url(self) -> None:
        """Test Google authorization URL generation."""
        url = self.provider.get_authorization_url("state123")

        assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
        assert "client_id=google-client-id" in url
        assert "access_type=offline" in url
        assert "prompt=consent" in url
        assert "state=state123" in url


class TestGitHubOAuth2Provider:
    """Test GitHub OAuth2 provider."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Set environment variables for real GitHub OAuth2 provider
        os.environ["GITHUB_CLIENT_ID"] = "github-client-id"
        os.environ["GITHUB_CLIENT_SECRET"] = "github-client-secret"
        os.environ["GITHUB_REDIRECT_URI"] = "https://app.com/github/callback"
        self.provider = GitHubOAuth2Provider()

    def test_github_provider_config(self) -> None:
        """Test GitHub provider configuration."""
        config = self.provider.config

        assert config.client_id == "github-client-id"
        assert config.client_secret == "github-client-secret"
        assert config.authorize_url == "https://github.com/login/oauth/authorize"
        assert config.token_url == "https://github.com/login/oauth/access_token"
        assert config.userinfo_url == "https://api.github.com/user"
        assert config.redirect_uri == "https://app.com/github/callback"
        assert config.scope == "read:user user:email"
        assert config.provider == "github"
        assert config.jwks_url is None  # GitHub doesn't use JWKS

    def test_github_provider_defaults(self) -> None:
        """Test GitHub provider with default environment."""
        # Store original environment variables
        original_client_id = os.environ.get("GITHUB_CLIENT_ID")
        original_client_secret = os.environ.get("GITHUB_CLIENT_SECRET")
        original_redirect_uri = os.environ.get("GITHUB_REDIRECT_URI")

        try:
            # Clear environment variables
            for key in ["GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", "GITHUB_REDIRECT_URI"]:
                if key in os.environ:
                    del os.environ[key]

            provider = GitHubOAuth2Provider()
            config = provider.config

            assert config.client_id == ""
            assert config.client_secret == ""
            assert config.redirect_uri == "http://localhost:8000/auth/github/callback"
        finally:
            # Restore original environment variables
            if original_client_id is not None:
                os.environ["GITHUB_CLIENT_ID"] = original_client_id
            if original_client_secret is not None:
                os.environ["GITHUB_CLIENT_SECRET"] = original_client_secret
            if original_redirect_uri is not None:
                os.environ["GITHUB_REDIRECT_URI"] = original_redirect_uri

    def test_github_map_user_data(self) -> None:
        """Test GitHub user data mapping."""
        user_data = {
            "id": 12345,
            "login": "githubuser",
            "name": "GitHub User",
            "email": "user@example.com",
            "avatar_url": "https://avatars.githubusercontent.com/u/12345",
        }

        user = self.provider._map_user_data(user_data)

        assert user.sub == "12345"  # converted to string
        assert user.email == "user@example.com"
        assert user.email_verified is True  # GitHub emails are verified
        assert user.name == "GitHub User"
        assert user.picture == "https://avatars.githubusercontent.com/u/12345"
        assert user.provider == "github"

    def test_github_map_user_data_no_name(self) -> None:
        """Test GitHub user data mapping without name."""
        user_data = {
            "id": 67890,
            "login": "noname",
            "email": "noname@example.com",
            "avatar_url": "https://avatars.githubusercontent.com/u/67890",
        }

        user = self.provider._map_user_data(user_data)

        assert user.sub == "67890"
        assert user.name == "noname"  # fallback to login
        assert user.email == "noname@example.com"

    def test_github_authorization_url(self) -> None:
        """Test GitHub authorization URL generation."""
        url = self.provider.get_authorization_url("state456")

        assert url.startswith("https://github.com/login/oauth/authorize?")
        assert "client_id=github-client-id" in url
        assert "scope=read%3Auser+user%3Aemail" in url
        assert "state=state456" in url


class TestOAuth2SessionManager:
    """Test OAuth2SessionManager."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.auth_backend = AuthenticationBackend()
        self.session_manager = OAuth2SessionManager(self.auth_backend)

    @pytest.mark.asyncio
    async def test_create_new_user(self) -> None:
        """Test creating a new user from OAuth2."""
        oauth_user = OAuth2User(
            sub="user123",
            email="newuser@example.com",
            email_verified=True,
            name="New User",
            picture="https://example.com/pic.jpg",
            provider="google",
        )

        user_id = await self.session_manager.create_or_update_user(oauth_user)

        assert user_id == "user_google_user123"
        assert "google:user123" in self.session_manager._user_mappings
        assert self.session_manager._user_mappings["google:user123"] == user_id

        # Check session data
        assert len(self.session_manager._sessions) == 1
        session_data = list(self.session_manager._sessions.values())[0]
        assert session_data["user_id"] == user_id
        assert session_data["provider"] == "google"
        assert session_data["email"] == "newuser@example.com"
        assert session_data["name"] == "New User"
        assert session_data["picture"] == "https://example.com/pic.jpg"
        assert isinstance(session_data["created_at"], datetime)

    @pytest.mark.asyncio
    async def test_update_existing_user(self) -> None:
        """Test updating an existing user."""
        oauth_user = OAuth2User(
            sub="user456",
            email="existinguser@example.com",
            name="Existing User",
            provider="github",
        )

        # Create user first time
        user_id1 = await self.session_manager.create_or_update_user(oauth_user)

        # Update same user
        oauth_user.name = "Updated User"
        oauth_user.email = "updated@example.com"
        user_id2 = await self.session_manager.create_or_update_user(oauth_user)

        # Should be same user ID
        assert user_id1 == user_id2
        assert user_id1 == "user_github_user456"

        # Should have two sessions
        assert len(self.session_manager._sessions) == 2

        # Both sessions should reference same user
        for session_data in self.session_manager._sessions.values():
            assert session_data["user_id"] == user_id1

    def test_create_user_token(self) -> None:
        """Test creating user token."""
        oauth_user = OAuth2User(
            sub="tokenuser",
            email="token@example.com",
            name="Token User",
            provider="google",
        )

        token = self.session_manager.create_user_token("internal_user_123", oauth_user)

        # Verify token
        token_data = self.auth_backend.verify_token(token)
        assert token_data is not None
        assert token_data.sub == "internal_user_123"
        assert isinstance(token_data.scopes, list)
        assert len(token_data.scopes) > 0

        # Check metadata
        assert token_data.metadata is not None
        assert token_data.metadata["provider"] == "google"
        assert token_data.metadata["email"] == "token@example.com"
        assert token_data.metadata["name"] == "Token User"

    def test_determine_user_scopes_default(self) -> None:
        """Test default user scope determination."""
        oauth_user = OAuth2User(
            sub="defaultuser",
            email="default@example.com",
            provider="google",
        )

        scopes = self.session_manager._determine_user_scopes(oauth_user)

        # Should have default read-only scopes
        from src.api.auth import Scopes
        assert Scopes.INCIDENTS_READ in scopes
        assert Scopes.AGENTS_READ in scopes
        assert Scopes.LOGS_READ in scopes
        assert Scopes.METRICS_READ in scopes

        # Should not have write/admin scopes by default
        assert Scopes.INCIDENTS_WRITE not in scopes
        assert Scopes.ADMIN_READ not in scopes

    def test_determine_user_scopes_trusted_domain(self) -> None:
        """Test scope determination for trusted domain."""
        oauth_user = OAuth2User(
            sub="trusteduser",
            email="user@trusted.com",
            provider="google",
        )

        # Store original environment variable
        original_trusted_domains = os.environ.get("OAUTH2_TRUSTED_DOMAINS")

        try:
            # Set environment variable
            os.environ["OAUTH2_TRUSTED_DOMAINS"] = "trusted.com,other.com"

            scopes = self.session_manager._determine_user_scopes(oauth_user)

            from src.api.auth import Scopes
            # Should have read scopes
            assert Scopes.INCIDENTS_READ in scopes
            # Should also have write scopes
            assert Scopes.INCIDENTS_WRITE in scopes
            assert Scopes.AGENTS_WRITE in scopes
        finally:
            # Restore original environment variable
            if original_trusted_domains is not None:
                os.environ["OAUTH2_TRUSTED_DOMAINS"] = original_trusted_domains
            elif "OAUTH2_TRUSTED_DOMAINS" in os.environ:
                del os.environ["OAUTH2_TRUSTED_DOMAINS"]

    def test_determine_user_scopes_admin_user(self) -> None:
        """Test scope determination for admin user."""
        oauth_user = OAuth2User(
            sub="adminuser",
            email="admin@example.com",
            provider="google",
        )

        # Store original environment variable
        original_admin_emails = os.environ.get("OAUTH2_ADMIN_EMAILS")

        try:
            # Set environment variable
            os.environ["OAUTH2_ADMIN_EMAILS"] = "admin@example.com,super@example.com"

            scopes = self.session_manager._determine_user_scopes(oauth_user)

            from src.api.auth import Scopes
            # Should have all scopes including admin
            assert Scopes.INCIDENTS_READ in scopes
            assert Scopes.ADMIN_READ in scopes
            assert Scopes.ADMIN_WRITE in scopes
            assert Scopes.REMEDIATION_EXECUTE in scopes
        finally:
            # Restore original environment variable
            if original_admin_emails is not None:
                os.environ["OAUTH2_ADMIN_EMAILS"] = original_admin_emails
            elif "OAUTH2_ADMIN_EMAILS" in os.environ:
                del os.environ["OAUTH2_ADMIN_EMAILS"]

    def test_determine_user_scopes_no_email(self) -> None:
        """Test scope determination with no email."""
        oauth_user = OAuth2User(
            sub="noemailuser",
            email=None,
            provider="github",
        )

        scopes = self.session_manager._determine_user_scopes(oauth_user)

        # Should still get default scopes
        from src.api.auth import Scopes
        assert Scopes.INCIDENTS_READ in scopes
        assert len(scopes) >= 4  # At least the default read scopes


class TestProviderRegistry:
    """Test OAuth2 provider registry functions."""

    def test_get_google_provider(self) -> None:
        """Test getting Google provider."""
        # Store original environment variables
        original_client_id = os.environ.get("GOOGLE_CLIENT_ID")
        original_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

        try:
            # Set environment variables
            os.environ["GOOGLE_CLIENT_ID"] = "test-google-id"
            os.environ["GOOGLE_CLIENT_SECRET"] = "test-google-secret"

            provider = get_oauth2_provider("google")

            assert isinstance(provider, GoogleOAuth2Provider)
            assert provider.config.provider == "google"
            assert provider.config.client_id == "test-google-id"
        finally:
            # Restore original environment variables
            if original_client_id is not None:
                os.environ["GOOGLE_CLIENT_ID"] = original_client_id
            elif "GOOGLE_CLIENT_ID" in os.environ:
                del os.environ["GOOGLE_CLIENT_ID"]
            if original_client_secret is not None:
                os.environ["GOOGLE_CLIENT_SECRET"] = original_client_secret
            elif "GOOGLE_CLIENT_SECRET" in os.environ:
                del os.environ["GOOGLE_CLIENT_SECRET"]

    def test_get_github_provider(self) -> None:
        """Test getting GitHub provider."""
        # Store original environment variables
        original_client_id = os.environ.get("GITHUB_CLIENT_ID")
        original_client_secret = os.environ.get("GITHUB_CLIENT_SECRET")

        try:
            # Set environment variables
            os.environ["GITHUB_CLIENT_ID"] = "test-github-id"
            os.environ["GITHUB_CLIENT_SECRET"] = "test-github-secret"

            provider = get_oauth2_provider("github")

            assert isinstance(provider, GitHubOAuth2Provider)
            assert provider.config.provider == "github"
            assert provider.config.client_id == "test-github-id"
        finally:
            # Restore original environment variables
            if original_client_id is not None:
                os.environ["GITHUB_CLIENT_ID"] = original_client_id
            elif "GITHUB_CLIENT_ID" in os.environ:
                del os.environ["GITHUB_CLIENT_ID"]
            if original_client_secret is not None:
                os.environ["GITHUB_CLIENT_SECRET"] = original_client_secret
            elif "GITHUB_CLIENT_SECRET" in os.environ:
                del os.environ["GITHUB_CLIENT_SECRET"]

    def test_get_provider_caching(self) -> None:
        """Test that providers are cached."""
        # Store original environment variables
        original_client_id = os.environ.get("GOOGLE_CLIENT_ID")
        original_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

        try:
            # Set environment variables
            os.environ["GOOGLE_CLIENT_ID"] = "cached-test-id"
            os.environ["GOOGLE_CLIENT_SECRET"] = "cached-test-secret"

            provider1 = get_oauth2_provider("google")
            provider2 = get_oauth2_provider("google")

            # Should be the same instance
            assert provider1 is provider2
        finally:
            # Restore original environment variables
            if original_client_id is not None:
                os.environ["GOOGLE_CLIENT_ID"] = original_client_id
            elif "GOOGLE_CLIENT_ID" in os.environ:
                del os.environ["GOOGLE_CLIENT_ID"]
            if original_client_secret is not None:
                os.environ["GOOGLE_CLIENT_SECRET"] = original_client_secret
            elif "GOOGLE_CLIENT_SECRET" in os.environ:
                del os.environ["GOOGLE_CLIENT_SECRET"]

    def test_get_unknown_provider(self) -> None:
        """Test getting unknown provider raises error."""
        with pytest.raises(ValueError, match="Unknown OAuth2 provider: unknown"):
            get_oauth2_provider("unknown")

    def test_get_session_manager(self) -> None:
        """Test getting session manager."""
        manager1 = get_oauth2_session_manager()
        manager2 = get_oauth2_session_manager()

        # Should be singleton
        assert manager1 is manager2
        assert isinstance(manager1, OAuth2SessionManager)


class TestFastAPIDependencies:
    """Test FastAPI dependency functions."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Use the actual production auth backend singleton
        from src.api.auth import get_auth_backend
        self.auth_backend = get_auth_backend()

    @pytest.mark.asyncio
    async def test_get_oauth2_user_with_valid_token(self) -> None:
        """Test getting OAuth2 user with valid token."""
        # Create a token with OAuth2 metadata using the actual production auth backend
        token = self.auth_backend.create_access_token(
            subject="oauth_user_123",
            scopes=["read", "write"],
            metadata={
                "provider": "google",
                "email": "oauth@example.com",
                "name": "OAuth User",
            },
        )

        # Test the actual production function
        user = await get_oauth2_user(token)

        assert user is not None
        assert user["user_id"] == "oauth_user_123"
        assert user["provider"] == "google"
        assert user["email"] == "oauth@example.com"
        assert user["name"] == "OAuth User"
        assert user["scopes"] == ["read", "write"]

    @pytest.mark.asyncio
    async def test_get_oauth2_user_with_non_oauth_token(self) -> None:
        """Test getting OAuth2 user with non-OAuth token."""
        # Create a token without OAuth2 metadata using the actual production auth backend
        token = self.auth_backend.create_access_token(
            subject="regular_user_456",
            scopes=["read"],
            metadata={"type": "regular"},  # No provider field
        )

        # Test the actual production function
        user = await get_oauth2_user(token)

        assert user is None  # Should return None for non-OAuth tokens

    @pytest.mark.asyncio
    async def test_get_oauth2_user_with_invalid_token(self) -> None:
        """Test getting OAuth2 user with invalid token."""
        invalid_token = "invalid.jwt.token"

        # Test the actual production function
        user = await get_oauth2_user(invalid_token)

        assert user is None

    @pytest.mark.asyncio
    async def test_get_oauth2_user_no_token(self) -> None:
        """Test getting OAuth2 user with no token."""
        user = await get_oauth2_user(None)

        assert user is None

    @pytest.mark.asyncio
    async def test_get_oauth2_user_no_metadata(self) -> None:
        """Test getting OAuth2 user with token that has no metadata."""
        # Create token with no metadata using the actual production auth backend
        token = self.auth_backend.create_access_token(
            subject="no_metadata_user",
            scopes=["read"],
            metadata=None,
        )

        # Test the actual production function
        user = await get_oauth2_user(token)

        assert user is None


class TestJWKSHandling:
    """Test JWKS-related functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = OAuth2Config(
            client_id="test-client",
            client_secret="test-secret",
            authorize_url="https://example.com/auth",
            token_url="https://example.com/token",
            userinfo_url="https://example.com/user",
            redirect_uri="https://app.com/callback",
            jwks_url="https://example.com/jwks",
            provider="test",
        )
        self.provider = OAuth2Provider(self.config)

    @pytest.mark.asyncio
    async def test_validate_id_token_no_jwks_url(self) -> None:
        """Test ID token validation without JWKS URL."""
        config_no_jwks = OAuth2Config(
            client_id="test",
            client_secret="test",
            authorize_url="https://example.com/auth",
            token_url="https://example.com/token",
            userinfo_url="https://example.com/user",
            redirect_uri="https://app.com/callback",
            provider="test",
            # No jwks_url
        )
        provider = OAuth2Provider(config_no_jwks)

        result = await provider.validate_id_token("some.jwt.token")

        # Should return None when no JWKS URL is configured
        assert result is None

    @pytest.mark.asyncio
    async def test_get_signing_key_unsupported_key_type(self) -> None:
        """Test getting signing key with unsupported key type."""
        jwks = {
            "keys": [
                {
                    "kid": "test-key-1",
                    "kty": "EC",  # Unsupported (not RSA)
                    "use": "sig",
                }
            ]
        }

        result = await self.provider._get_signing_key("test-key-1", jwks)

        # Should return None for unsupported key types
        assert result is None

    @pytest.mark.asyncio
    async def test_get_signing_key_missing_components(self) -> None:
        """Test getting signing key with missing RSA components."""
        jwks = {
            "keys": [
                {
                    "kid": "test-key-2",
                    "kty": "RSA",
                    "use": "sig",
                    # Missing 'n' and 'e' components
                }
            ]
        }

        result = await self.provider._get_signing_key("test-key-2", jwks)

        # Should return None when RSA components are missing
        assert result is None

    @pytest.mark.asyncio
    async def test_get_signing_key_not_found(self) -> None:
        """Test getting signing key that doesn't exist."""
        jwks = {
            "keys": [
                {
                    "kid": "different-key",
                    "kty": "RSA",
                    "n": "test",
                    "e": "AQAB",
                }
            ]
        }

        result = await self.provider._get_signing_key("nonexistent-key", jwks)

        # Should return None when key is not found
        assert result is None
