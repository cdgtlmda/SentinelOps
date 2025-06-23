"""
OAuth2 integration for SentinelOps API.
"""

import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urlencode

import httpx
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends
from fastapi.security import OAuth2AuthorizationCodeBearer
from jwt import PyJWTError as JWTError
from pydantic import BaseModel, Field

from ..config.logging_config import get_logger
from .auth import AuthenticationBackend, get_auth_backend
from .exceptions import AuthenticationException

logger = get_logger(__name__)


class OAuth2Config(BaseModel):
    """OAuth2 provider configuration."""

    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    redirect_uri: str
    scope: str = "openid profile email"
    response_type: str = "code"
    grant_type: str = "authorization_code"

    # Optional JWKS URL for token validation
    jwks_url: Optional[str] = None

    # Provider-specific settings
    provider: str = "generic"  # google, github, okta, auth0, etc.
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class OAuth2User(BaseModel):
    """OAuth2 user information."""

    sub: str  # Unique user ID from provider
    email: Optional[str] = None
    email_verified: bool = False
    name: Optional[str] = None
    picture: Optional[str] = None
    provider: str
    raw_data: Dict[str, Any] = Field(default_factory=dict)


class OAuth2Provider:
    """Base OAuth2 provider implementation."""

    def __init__(self, config: OAuth2Config):
        self.config = config
        self.client = httpx.AsyncClient()
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._jwks_cache_time: Optional[datetime] = None
        self._parsed_keys: Dict[str, Any] = {}  # kid -> public key

    def get_authorization_url(self, state: str) -> str:
        """
        Get the authorization URL for OAuth2 flow.

        Args:
            state: CSRF protection state parameter

        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": self.config.response_type,
            "scope": self.config.scope,
            "state": state,
            **self.config.extra_params,
        }

        return f"{self.config.authorize_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth2 provider

        Returns:
            Token response from provider
        """
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": code,
            "redirect_uri": self.config.redirect_uri,
            "grant_type": self.config.grant_type,
        }

        try:
            response = await self.client.post(
                self.config.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()

            return cast(Dict[str, Any], response.json())

        except httpx.HTTPError as e:
            logger.error("Failed to exchange code for token: %s", e)
            raise AuthenticationException(
                "Failed to authenticate with OAuth2 provider"
            ) from e

    async def get_user_info(self, access_token: str) -> OAuth2User:
        """
        Get user information from OAuth2 provider.

        Args:
            access_token: Access token from provider

        Returns:
            User information
        """
        try:
            response = await self.client.get(
                self.config.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()

            user_data = response.json()

            # Map provider-specific fields
            user = self._map_user_data(user_data)
            user.provider = self.config.provider
            user.raw_data = user_data

            return user

        except httpx.HTTPError as e:
            logger.error("Failed to get user info: %s", e)
            raise AuthenticationException("Failed to get user information") from e

    def _map_user_data(self, user_data: Dict[str, Any]) -> OAuth2User:
        """Map provider-specific user data to standard format."""
        # Default mapping for OpenID Connect
        return OAuth2User(
            sub=user_data.get("sub", user_data.get("id", "")),
            email=user_data.get("email"),
            email_verified=user_data.get("email_verified", False),
            name=user_data.get("name"),
            picture=user_data.get("picture"),
            provider=self.config.provider,
        )

    async def validate_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate an ID token from the provider.

        Args:
            id_token: ID token to validate

        Returns:
            Decoded token payload if valid
        """
        if not self.config.jwks_url:
            return None

        try:
            # Get JWKS (with caching)
            jwks = await self._get_jwks()

            # Get the kid from the token header
            unverified_header = jwt.get_unverified_header(id_token)
            kid = unverified_header.get("kid")

            if not kid:
                logger.error("No kid found in token header")
                return None

            # Get the signing key based on kid
            signing_key = await self._get_signing_key(kid, jwks)

            if not signing_key:
                logger.error("No signing key found for kid: %s", kid)
                return None

            # Decode and verify token with the proper key
            payload = jwt.decode(
                id_token,
                signing_key,
                algorithms=["RS256"],
                audience=self.config.client_id,
                options={"verify_signature": True},
            )

            return cast(Dict[str, Any], payload)

        except JWTError as e:
            logger.error("Failed to validate ID token: %s", e)
            return None

    async def _get_jwks(self) -> Dict[str, Any]:
        """Get JWKS from provider with caching."""
        now = datetime.now(timezone.utc)

        # Check cache (1 hour TTL)
        if (
            self._jwks_cache
            and self._jwks_cache_time
            and now - self._jwks_cache_time < timedelta(hours=1)
        ):
            return self._jwks_cache

        # Fetch JWKS
        if not self.config.jwks_url:
            raise ValueError("JWKS URL not configured")
        response = await self.client.get(self.config.jwks_url)
        response.raise_for_status()

        self._jwks_cache = cast(Dict[str, Any], response.json())
        self._jwks_cache_time = now

        # Clear parsed keys cache when JWKS is refreshed
        self._parsed_keys.clear()

        return self._jwks_cache

    async def _get_signing_key(self, kid: str, jwks: Dict[str, Any]) -> Optional[Any]:
        """
        Extract the signing key from JWKS based on kid.

        Args:
            kid: Key ID from JWT header
            jwks: JWKS response from provider

        Returns:
            Public key for verification
        """
        # Check if we already parsed this key
        if kid in self._parsed_keys:
            return self._parsed_keys[kid]

        # Find the key in JWKS
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                # Only support RSA keys for now
                if key.get("kty") != "RSA":
                    logger.warning("Unsupported key type: %s", key.get("kty"))
                    continue

                # Extract RSA components
                n = key.get("n")  # modulus
                e = key.get("e")  # exponent

                if not n or not e:
                    logger.error("Missing RSA key components")
                    continue

                try:
                    # Convert base64url to int
                    n_int = int.from_bytes(base64.urlsafe_b64decode(n + "=="), "big")
                    e_int = int.from_bytes(base64.urlsafe_b64decode(e + "=="), "big")

                    # Create RSA public key
                    public_numbers = rsa.RSAPublicNumbers(e_int, n_int)
                    public_key = public_numbers.public_key()

                    # Convert to PEM format for PyJWT
                    pem = public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    )

                    # Cache the parsed key
                    self._parsed_keys[kid] = pem

                    return pem

                except (ValueError, TypeError, OSError) as e:
                    logger.error("Failed to parse RSA key: %s", e)
                    continue

        return None

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()


class GoogleOAuth2Provider(OAuth2Provider):
    """Google OAuth2 provider implementation."""

    def __init__(self) -> None:
        config = OAuth2Config(
            client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://www.googleapis.com/oauth2/v3/userinfo",
            redirect_uri=os.getenv(
                "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"
            ),
            scope="openid profile email",
            provider="google",
            jwks_url="https://www.googleapis.com/oauth2/v3/certs",
            extra_params={
                "access_type": "offline",
                "prompt": "consent",
            },
        )
        super().__init__(config)

    def _map_user_data(self, user_data: Dict[str, Any]) -> OAuth2User:
        """Map Google user data."""
        return OAuth2User(
            sub=user_data.get("sub", ""),
            email=user_data.get("email"),
            email_verified=user_data.get("email_verified", False),
            name=user_data.get("name"),
            picture=user_data.get("picture"),
            provider="google",
        )


class GitHubOAuth2Provider(OAuth2Provider):
    """GitHub OAuth2 provider implementation."""

    def __init__(self) -> None:
        config = OAuth2Config(
            client_id=os.getenv("GITHUB_CLIENT_ID", ""),
            client_secret=os.getenv("GITHUB_CLIENT_SECRET", ""),
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            userinfo_url="https://api.github.com/user",
            redirect_uri=os.getenv(
                "GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github/callback"
            ),
            scope="read:user user:email",
            provider="github",
        )
        super().__init__(config)

    def _map_user_data(self, user_data: Dict[str, Any]) -> OAuth2User:
        """Map GitHub user data."""
        return OAuth2User(
            sub=str(user_data.get("id", "")),
            email=user_data.get("email"),
            email_verified=True,  # GitHub verifies emails
            name=user_data.get("name") or user_data.get("login"),
            picture=user_data.get("avatar_url"),
            provider="github",
        )

    async def get_user_info(self, access_token: str) -> OAuth2User:
        """Get user info from GitHub (including email if not public)."""
        user = await super().get_user_info(access_token)

        # If email is not public, fetch from emails endpoint
        if not user.email:
            try:
                response = await self.client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()

                emails = response.json()
                # Get primary verified email
                for email_data in emails:
                    if email_data.get("primary") and email_data.get("verified"):
                        user.email = email_data.get("email")
                        user.email_verified = True
                        break

            except httpx.HTTPError:
                pass  # Email fetch is optional

        return user


class OAuth2SessionManager:
    """Manages OAuth2 sessions and user mapping."""

    def __init__(self, auth_backend: AuthenticationBackend):
        self.auth_backend = auth_backend
        # In production, these would be stored in a database
        self._user_mappings: Dict[str, str] = {}  # provider_user_id -> internal_user_id
        self._sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> session_data

    async def create_or_update_user(self, oauth_user: OAuth2User) -> str:
        """
        Create or update user from OAuth2 provider.

        Args:
            oauth_user: OAuth2 user information

        Returns:
            Internal user ID
        """
        # Create provider-specific user ID
        provider_user_id = f"{oauth_user.provider}:{oauth_user.sub}"

        # Check if user exists
        internal_user_id = self._user_mappings.get(provider_user_id, None)

        if not internal_user_id:
            # Create new user
            internal_user_id = f"user_{oauth_user.provider}_{oauth_user.sub}"
            self._user_mappings[provider_user_id] = internal_user_id

            logger.info(
                "Created new user from %s: %s", oauth_user.provider, internal_user_id
            )
        else:
            # Update existing user
            logger.info(
                "Updated user from %s: %s", oauth_user.provider, internal_user_id
            )

        # Store user data in session
        session_id = os.urandom(32).hex()
        self._sessions[session_id] = {
            "user_id": internal_user_id,
            "provider": oauth_user.provider,
            "email": oauth_user.email,
            "name": oauth_user.name,
            "picture": oauth_user.picture,
            "created_at": datetime.now(timezone.utc),
        }

        return internal_user_id

    def create_user_token(self, user_id: str, oauth_user: OAuth2User) -> str:
        """
        Create JWT token for authenticated user.

        Args:
            user_id: Internal user ID
            oauth_user: OAuth2 user information

        Returns:
            JWT access token
        """
        # Determine user scopes based on email/domain
        scopes = self._determine_user_scopes(oauth_user)

        # Create access token
        token = self.auth_backend.create_access_token(
            subject=user_id,
            scopes=scopes,
            metadata={
                "provider": oauth_user.provider,
                "email": oauth_user.email,
                "name": oauth_user.name,
            },
        )

        return token

    def _determine_user_scopes(self, oauth_user: OAuth2User) -> List[str]:
        """Determine user scopes based on OAuth2 user info."""
        from .auth import Scopes

        # Default read-only scopes
        scopes = [
            Scopes.INCIDENTS_READ,
            Scopes.AGENTS_READ,
            Scopes.LOGS_READ,
            Scopes.METRICS_READ,
        ]

        # Add write scopes for specific domains (example)
        trusted_domains = os.getenv("OAUTH2_TRUSTED_DOMAINS", "").split(",")
        if oauth_user.email and any(
            oauth_user.email.endswith(f"@{domain}") for domain in trusted_domains
        ):
            scopes.extend(
                [
                    Scopes.INCIDENTS_WRITE,
                    Scopes.AGENTS_WRITE,
                ]
            )

        # Add admin scopes for specific users (example)
        admin_emails = os.getenv("OAUTH2_ADMIN_EMAILS", "").split(",")
        if oauth_user.email in admin_emails:
            scopes.extend(
                [
                    Scopes.ADMIN_READ,
                    Scopes.ADMIN_WRITE,
                    Scopes.REMEDIATION_EXECUTE,
                ]
            )

        return scopes


# OAuth2 provider registry
_oauth2_providers: Dict[str, OAuth2Provider] = {}
_oauth2_session_manager: Optional[OAuth2SessionManager] = None


def get_oauth2_provider(provider: str) -> OAuth2Provider:
    """Get OAuth2 provider by name."""
    if provider not in _oauth2_providers:
        if provider == "google":
            _oauth2_providers[provider] = GoogleOAuth2Provider()
        elif provider == "github":
            _oauth2_providers[provider] = GitHubOAuth2Provider()
        else:
            raise ValueError(f"Unknown OAuth2 provider: {provider}")

    return _oauth2_providers[provider]


def get_oauth2_session_manager() -> OAuth2SessionManager:
    """Get OAuth2 session manager."""
    global _oauth2_session_manager  # pylint: disable=global-statement

    if not _oauth2_session_manager:
        _oauth2_session_manager = OAuth2SessionManager(get_auth_backend())

    return _oauth2_session_manager


# OAuth2 scheme for FastAPI
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="",  # Dynamic based on provider
    tokenUrl="",  # Dynamic based on provider
    auto_error=False,
)


async def get_oauth2_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[Dict[str, Any]]:
    """
    Get OAuth2 authenticated user from request.

    Args:
        token: OAuth2 token

    Returns:
        User information if authenticated
    """
    if not token:
        return None

    # Get token data from auth backend
    auth_backend = get_auth_backend()
    token_data = auth_backend.verify_token(token)

    if not token_data:
        return None

    # Check if this is an OAuth2 user
    if (
        token_data.metadata
        and isinstance(token_data.metadata, dict)
        and token_data.metadata.get("provider")  # pylint: disable=no-member
    ):
        return {
            "user_id": token_data.sub,
            "provider": token_data.metadata["provider"],
            "email": (
                token_data.metadata.get("email")  # pylint: disable=no-member
                if isinstance(token_data.metadata, dict)
                else None
            ),
            "name": (
                token_data.metadata.get("name")  # pylint: disable=no-member
                if isinstance(token_data.metadata, dict)
                else None
            ),
            "scopes": token_data.scopes,
        }

    return None
