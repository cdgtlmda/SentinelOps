"""Tests for authentication middleware using real production code."""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Generator

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from src.api.middleware.auth import AuthMiddleware, auth_middleware


class TestAuthMiddleware:
    """Test cases for AuthMiddleware with real production code."""

    @pytest.fixture
    def project_id(self) -> str:
        """Test project ID."""
        return "test-project-123"

    @pytest.fixture
    def auth_instance(self, project_id: str) -> AuthMiddleware:
        """Create AuthMiddleware instance for testing."""
        return AuthMiddleware(project_id)

    @pytest.fixture
    def jwt_config_file(self) -> Generator[str, None, None]:
        """Create a temporary JWT config file."""
        config_data = {
            "algorithm": "RS256",
            "issuer": "test-issuer",
            "audience": "test-audience",
            "expiry_minutes": 30,
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            yield f.name
        os.unlink(f.name)

    def test_initialization(self, project_id: str) -> None:
        """Test AuthMiddleware initialization with real configuration."""
        middleware = AuthMiddleware(project_id)
        assert middleware.project_id == project_id
        assert isinstance(middleware.jwt_config, dict)
        assert middleware.jwt_config["algorithm"] == "RS256"
        assert middleware.jwt_config["issuer"] == f"sentinelops@{project_id}"
        assert middleware.jwt_config["audience"] == f"https://sentinelops-{project_id}.cloudfunctions.net"
        assert middleware.jwt_config["expiry_minutes"] == 60

    def test_load_jwt_config_from_file(self, project_id: str, jwt_config_file: str) -> None:
        """Test loading JWT configuration from an actual file."""
        # Create config directory structure
        config_dir = Path("config/auth")
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "jwt_config.json"

        # Write test config to expected location
        config_data = {
            "algorithm": "RS256",
            "issuer": "test-issuer",
            "audience": "test-audience",
            "expiry_minutes": 30,
        }
        with open(config_path, 'w') as f:
            json.dump(config_data, f)

        try:
            middleware = AuthMiddleware(project_id)
            assert middleware.jwt_config["algorithm"] == "RS256"
            assert middleware.jwt_config["issuer"] == "test-issuer"
            assert middleware.jwt_config["audience"] == "test-audience"
            assert middleware.jwt_config["expiry_minutes"] == 30
        finally:
            # Clean up
            if config_path.exists():
                config_path.unlink()
            # Clean up auth directory
            if config_dir.exists():
                # Remove any remaining files
                for file in config_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                config_dir.rmdir()
            # Clean up config directory if empty
            if Path("config").exists() and not any(Path("config").iterdir()):
                Path("config").rmdir()

    def test_load_jwt_config_missing_file(self, project_id: str) -> None:
        """Test JWT config loading when file doesn't exist."""
        # Ensure config file doesn't exist
        config_path = Path("config/auth/jwt_config.json")
        if config_path.exists():
            config_path.unlink()

        middleware = AuthMiddleware(project_id)
        # Should use default config
        assert middleware.jwt_config["algorithm"] == "RS256"
        assert middleware.jwt_config["issuer"] == f"sentinelops@{project_id}"
        assert middleware.jwt_config["expiry_minutes"] == 60

    @pytest.mark.asyncio
    async def test_verify_google_token_network_request(self, auth_instance: AuthMiddleware) -> None:
        """Test that Google OAuth2 token verification would make real network request."""
        mock_token = "ya29.invalid_google_token"
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=mock_token
        )

        # This will fail with a real network request to Google
        with pytest.raises(HTTPException) as exc_info:
            await auth_instance.verify_token(credentials)

        assert exc_info.value.status_code == 401

    def test_verify_jwt_token_valid(self, auth_instance: AuthMiddleware) -> None:
        """Test custom JWT token verification with valid token."""
        # Create a valid JWT token
        payload = {
            "user_id": "test-user",
            "email": "test@example.com",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        result = auth_instance._verify_jwt_token(token)

        assert result["user_id"] == "test-user"
        assert result["email"] == "test@example.com"
        assert "exp" in result

    def test_verify_jwt_token_expired(self, auth_instance: AuthMiddleware) -> None:
        """Test JWT token verification with expired token."""
        # Create an expired JWT token
        payload = {
            "user_id": "test-user",
            "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        with pytest.raises(ValueError) as exc_info:
            auth_instance._verify_jwt_token(token)

        assert "Token has expired" in str(exc_info.value)

    def test_verify_jwt_token_invalid_format(self, auth_instance: AuthMiddleware) -> None:
        """Test JWT token verification with invalid token format."""
        invalid_token = "not.a.jwt"

        with pytest.raises(ValueError) as exc_info:
            auth_instance._verify_jwt_token(invalid_token)

        assert "Invalid JWT token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_token_custom_jwt(self, auth_instance: AuthMiddleware) -> None:
        """Test verify_token with custom JWT token."""
        payload = {
            "user_id": "test-user",
            "role": "admin",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )

        result = await auth_instance.verify_token(credentials)

        assert result["user_id"] == "test-user"
        assert result["role"] == "admin"

    @pytest.mark.asyncio
    async def test_verify_token_empty_credentials(self, auth_instance: AuthMiddleware) -> None:
        """Test token verification with empty credentials."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=""
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_instance.verify_token(credentials)

        assert exc_info.value.status_code == 401

    def test_global_auth_middleware_instance(self) -> None:
        """Test that global auth_middleware is properly initialized."""
        assert isinstance(auth_middleware, AuthMiddleware)
        assert auth_middleware.project_id == os.getenv("PROJECT_ID", "your-gcp-project-id")
        assert isinstance(auth_middleware.jwt_config, dict)

    @pytest.mark.asyncio
    async def test_verify_auth_dependency(self) -> None:
        """Test verify_auth dependency function with real token."""
        # Create a valid JWT token
        payload = {
            "user_id": "test-user",
            "email": "test@example.com",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )

        # Test token verification directly through auth_middleware
        result = await auth_middleware.verify_token(credentials)

        assert result["user_id"] == "test-user"
        assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_concurrent_token_verification(self, auth_instance: AuthMiddleware) -> None:
        """Test concurrent token verification to ensure thread safety."""
        import asyncio

        tokens = []
        for i in range(5):
            payload = {
                "user_id": f"user-{i}",
                "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
            }
            token = jwt.encode(payload, "secret", algorithm="HS256")
            tokens.append(token)

        async def verify_token(token: str) -> dict[str, Any]:
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=token
            )
            return await auth_instance.verify_token(credentials)

        # Verify multiple tokens concurrently
        results = await asyncio.gather(*[verify_token(t) for t in tokens])

        # Check all tokens were verified correctly
        for i, result in enumerate(results):
            assert result["user_id"] == f"user-{i}"

    def test_jwt_config_with_invalid_json(self, project_id: str) -> None:
        """Test JWT config loading with invalid JSON file."""
        config_dir = Path("config/auth")
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "jwt_config.json"

        # Write invalid JSON
        with open(config_path, 'w') as f:
            f.write("{ invalid json")

        try:
            # Should fall back to default config
            middleware = AuthMiddleware(project_id)
            assert middleware.jwt_config["algorithm"] == "RS256"
            assert middleware.jwt_config["issuer"] == f"sentinelops@{project_id}"
        finally:
            # Clean up
            if config_path.exists():
                config_path.unlink()
            # Clean up auth directory
            if config_dir.exists():
                # Remove any remaining files
                for file in config_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                config_dir.rmdir()
            # Clean up config directory if empty
            if Path("config").exists() and not any(Path("config").iterdir()):
                Path("config").rmdir()

    def test_jwt_token_with_various_algorithms(self, auth_instance: AuthMiddleware) -> None:
        """Test JWT token verification with different algorithms."""
        algorithms = ["HS256", "HS384", "HS512"]

        for algo in algorithms:
            payload = {
                "user_id": f"test-{algo}",
                "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
            }
            token = jwt.encode(payload, "secret", algorithm=algo)

            result = auth_instance._verify_jwt_token(token)
            assert result["user_id"] == f"test-{algo}"

    def test_jwt_token_missing_exp_claim(self, auth_instance: AuthMiddleware) -> None:
        """Test JWT token verification when exp claim is missing."""
        payload = {
            "user_id": "test-user",
            "email": "test@example.com"
            # Missing exp claim
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        # Should not raise error, just return the payload
        result = auth_instance._verify_jwt_token(token)
        assert result["user_id"] == "test-user"
        assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_verify_token_with_malformed_google_token(self, auth_instance: AuthMiddleware) -> None:
        """Test token verification with malformed Google token."""
        malformed_token = "ya29.malformed.token.structure.missing.parts"
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=malformed_token
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_instance.verify_token(credentials)

        assert exc_info.value.status_code == 401

    def test_jwt_decode_options(self, auth_instance: AuthMiddleware) -> None:
        """Test JWT decoding with various option configurations."""
        payload = {
            "user_id": "test-user",
            "aud": "wrong-audience",
            "iss": "wrong-issuer",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        # Should decode without verifying audience/issuer
        result = auth_instance._verify_jwt_token(token)
        assert result["user_id"] == "test-user"
        assert result["aud"] == "wrong-audience"
        assert result["iss"] == "wrong-issuer"

    def test_real_google_request_module_import(self) -> None:
        """Test that Google auth request module can be imported."""
        try:
            from google.auth.transport import requests
            assert hasattr(requests, 'Request')
        except ImportError:
            pytest.skip("Google auth transport not available")
