"""
Authentication middleware and utilities for SentinelOps.
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import jwt
from fastapi import Depends, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from ..api.exceptions import AuthenticationException, AuthorizationException
from ..config.logging_config import get_logger
from .security import get_security_config

logger = get_logger(__name__)

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class TokenData(BaseModel):
    """JWT token payload data."""

    sub: str  # Subject (user ID or service account)
    exp: datetime  # Expiration time
    iat: datetime  # Issued at
    jti: str  # JWT ID (unique token ID)
    type: str = "access"  # Token type (access, refresh, service)
    scopes: List[str] = Field(default_factory=list)  # Permission scopes
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional metadata


class APIKey(BaseModel):
    """API key model."""

    key_hash: str  # Hashed API key
    name: str  # Key name/description
    created_at: datetime
    expires_at: Optional[datetime] = None
    scopes: List[str] = Field(default_factory=list)
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuthenticationBackend:
    """Handles authentication logic."""

    def __init__(self) -> None:
        self.config = get_security_config()
        # In production, these would come from a database
        self._api_keys: Dict[str, APIKey] = {}
        self._revoked_tokens: set[str] = set()

    def generate_api_key(self, name: str, scopes: Optional[List[str]] = None) -> str:
        """
        Generate a new API key.

        Args:
            name: Key name/description
            scopes: Permission scopes

        Returns:
            The API key (only returned once)
        """
        # Generate secure random key
        key = secrets.token_urlsafe(32)

        # Hash the key for storage
        key_hash = self._hash_api_key(key)

        # Store the key
        api_key = APIKey(
            key_hash=key_hash,
            name=name,
            created_at=datetime.now(timezone.utc),
            scopes=scopes or [],
            is_active=True,
        )

        self._api_keys[key_hash] = api_key

        logger.info("Generated API key: %s", name)
        return key

    def _hash_api_key(self, key: str) -> str:
        """Hash an API key for secure storage."""
        salt = os.getenv("API_KEY_SALT", "dev-salt")
        return hashlib.sha256(f"{key}{salt}".encode()).hexdigest()

    def verify_api_key(self, key: str) -> Optional[APIKey]:
        """
        Verify an API key.

        Args:
            key: The API key to verify

        Returns:
            APIKey object if valid, None otherwise
        """
        key_hash = self._hash_api_key(key)
        api_key = self._api_keys.get(key_hash)

        if not api_key or not api_key.is_active:
            return None

        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            return None

        return api_key

    def create_access_token(
        self,
        subject: str,
        scopes: Optional[List[str]] = None,
        expires_delta: Optional[timedelta] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a JWT access token.

        Args:
            subject: Token subject (user ID)
            scopes: Permission scopes
            expires_delta: Token expiration time
            metadata: Additional metadata

        Returns:
            JWT token string
        """
        now = datetime.now(timezone.utc)

        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=self.config.jwt_expiration_minutes)

        token_data = TokenData(
            sub=subject,
            exp=expire,
            iat=now,
            jti=secrets.token_urlsafe(16),
            type="access",
            scopes=scopes or [],
            metadata=metadata or {},
        )

        # Create JWT
        token = jwt.encode(
            token_data.model_dump(),
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm,
        )

        logger.info("Created access token for subject: %s", subject)
        return token

    def verify_token(self, token: str) -> Optional[TokenData]:
        """
        Verify a JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenData if valid, None otherwise
        """
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )

            # Check if token is revoked
            jti = payload.get("jti")
            if jti in self._revoked_tokens:
                logger.warning("Attempted to use revoked token: %s", jti)
                return None

            # Parse token data
            token_data = TokenData(**payload)

            # Check expiration
            if token_data.exp < datetime.now(timezone.utc):
                return None

            return token_data

        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            return None

        except jwt.InvalidTokenError as e:
            logger.debug("Invalid token: %s", e)
            return None

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a JWT token.

        Args:
            token: JWT token to revoke

        Returns:
            True if revoked, False if invalid
        """
        token_data = self.verify_token(token)
        if token_data:
            self._revoked_tokens.add(token_data.jti)
            logger.info("Revoked token: %s", token_data.jti)
            return True
        return False


# Global authentication backend
_auth_backend = AuthenticationBackend()


def get_auth_backend() -> AuthenticationBackend:
    """Get the authentication backend."""
    return _auth_backend


async def get_current_token(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> Optional[TokenData]:
    """
    Get current token from request.

    Args:
        credentials: Bearer token credentials

    Returns:
        TokenData if valid

    Raises:
        AuthenticationException if invalid
    """
    if not credentials:
        return None

    backend = get_auth_backend()
    token_data = backend.verify_token(credentials.credentials)

    if not token_data:
        raise AuthenticationException("Invalid or expired token")

    return token_data


async def get_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[APIKey]:
    """
    Get API key from request.

    Args:
        api_key: API key from header

    Returns:
        APIKey if valid

    Raises:
        AuthenticationException if invalid
    """
    if not api_key:
        return None

    backend = get_auth_backend()
    key_data = backend.verify_api_key(api_key)

    if not key_data:
        raise AuthenticationException("Invalid API key")

    return key_data


async def require_auth(
    token_data: Optional[TokenData] = Depends(get_current_token),
    api_key: Optional[APIKey] = Depends(get_api_key),
) -> Dict[str, Any]:
    """
    Require authentication via token or API key.

    Returns:
        Authentication info

    Raises:
        AuthenticationException if not authenticated
    """
    if token_data:
        return {
            "type": "token",
            "subject": token_data.sub,
            "scopes": token_data.scopes,
            "metadata": token_data.metadata,
        }

    if api_key:
        return {
            "type": "api_key",
            "subject": api_key.name,
            "scopes": api_key.scopes,
            "metadata": api_key.metadata,
        }

    raise AuthenticationException("Authentication required")


def require_scopes(required_scopes: List[str]) -> Any:
    """
    Require specific permission scopes.

    Args:
        required_scopes: List of required scopes

    Usage:
        @router.get("/admin")
        async def admin_endpoint(
            auth: Dict = Depends(require_auth),
            _: None = Depends(require_scopes(["admin:read"]))
        ):
            ...
    """

    async def scope_checker(auth: Dict[str, Any] = Depends(require_auth)) -> None:
        user_scopes = set(auth.get("scopes", []))
        required = set(required_scopes)

        # Check if user has all required scopes
        if not required.issubset(user_scopes):
            missing = required - user_scopes
            raise AuthorizationException(
                f"Missing required scopes: {', '.join(missing)}"
            )

    return scope_checker


# Common permission scopes
class Scopes:
    """Common permission scopes."""

    # Read permissions
    INCIDENTS_READ = "incidents:read"
    AGENTS_READ = "agents:read"
    LOGS_READ = "logs:read"
    METRICS_READ = "metrics:read"

    # Write permissions
    INCIDENTS_WRITE = "incidents:write"
    AGENTS_WRITE = "agents:write"
    REMEDIATION_EXECUTE = "remediation:execute"

    # Admin permissions
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_DELETE = "admin:delete"

    # Service account scopes
    SERVICE_AGENT = "service:agent"
    SERVICE_ORCHESTRATOR = "service:orchestrator"


# Initialize demo API key for development
if os.getenv("APP_ENV") == "development":
    demo_key = get_auth_backend().generate_api_key(
        "demo-key", scopes=[Scopes.INCIDENTS_READ, Scopes.AGENTS_READ, Scopes.LOGS_READ]
    )
    logger.info("Demo API key generated: %s", demo_key)
