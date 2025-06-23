"""
Authentication routes for SentinelOps API.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field

from ..config.logging_config import get_logger
from .auth import (
    Scopes,
    TokenData,
    get_auth_backend,
    get_current_token,
    require_auth,
)
from .exceptions import AuthenticationException  # , ValidationException
from .oauth2 import (
    get_oauth2_provider,
    get_oauth2_session_manager,
    get_oauth2_user,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Login request model."""

    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    remember_me: bool = False


class LoginResponse(BaseModel):
    """Login response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    refresh_token: Optional[str] = None
    scopes: list[str] = Field(default_factory=list)


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""

    refresh_token: str


class APIKeyRequest(BaseModel):
    """API key creation request."""

    name: str = Field(..., min_length=3, max_length=100)
    scopes: list[str] = Field(default_factory=list)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """API key response model."""

    api_key: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    scopes: list[str]


class UserInfo(BaseModel):
    """User information model."""

    user_id: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    scopes: list[str] = Field(default_factory=list)
    auth_type: str  # token, api_key, oauth2
    provider: Optional[str] = None  # OAuth2 provider


# Session storage (in production, use Redis or similar)
_sessions: dict[str, dict[str, Any]] = {}


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Login with username and password.

    This is a simplified implementation. In production, you would:
    - Validate credentials against a user database
    - Hash passwords properly (bcrypt, argon2, etc.)
    - Implement proper session management
    """
    # Demo implementation - accept specific test credentials
    valid_users = {
        "admin": {
            "password": "your-admin-password",
            "scopes": [
                Scopes.ADMIN_READ,
                Scopes.ADMIN_WRITE,
                Scopes.INCIDENTS_READ,
                Scopes.INCIDENTS_WRITE,
                Scopes.REMEDIATION_EXECUTE,
            ],
        },
        "operator": {
            "password": "your-operator-password",
            "scopes": [
                Scopes.INCIDENTS_READ,
                Scopes.INCIDENTS_WRITE,
                Scopes.AGENTS_READ,
                Scopes.LOGS_READ,
            ],
        },
        "viewer": {
            "password": "your-viewer-password",
            "scopes": [
                Scopes.INCIDENTS_READ,
                Scopes.AGENTS_READ,
                Scopes.LOGS_READ,
                Scopes.METRICS_READ,
            ],
        },
    }

    # Validate credentials
    user_data = valid_users.get(request.username)
    if not user_data or user_data["password"] != request.password:
        raise AuthenticationException("Invalid username or password")

    # Create tokens
    auth_backend = get_auth_backend()

    # Access token expires in 30 minutes or 7 days if remember_me
    expires_delta = timedelta(days=7) if request.remember_me else timedelta(minutes=30)

    access_token = auth_backend.create_access_token(
        subject=request.username,
        scopes=list(user_data["scopes"]),
        expires_delta=expires_delta,
        metadata={"auth_type": "password"},
    )

    # Create refresh token (expires in 30 days)
    refresh_token = None
    if request.remember_me:
        refresh_token = auth_backend.create_access_token(
            subject=request.username,
            scopes=["refresh"],
            expires_delta=timedelta(days=30),
            metadata={"auth_type": "refresh", "parent": request.username},
        )

    logger.info("User logged in: %s", request.username)

    return LoginResponse(
        access_token=access_token,
        expires_in=int(expires_delta.total_seconds()),
        refresh_token=refresh_token,
        scopes=list(user_data["scopes"]),
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_access_token(request: RefreshTokenRequest) -> LoginResponse:
    """Refresh access token using refresh token."""
    auth_backend = get_auth_backend()

    # Verify refresh token
    token_data = auth_backend.verify_token(request.refresh_token)
    if not token_data or "refresh" not in token_data.scopes:
        raise AuthenticationException("Invalid refresh token")

    # Get original user scopes (in production, fetch from database)
    parent_user = (
        getattr(token_data, "metadata", {}).get("parent")
        if hasattr(token_data, "metadata")
        else None
    )
    if not parent_user:
        raise AuthenticationException("Invalid refresh token")

    # For demo, use hardcoded scopes
    user_scopes = [
        Scopes.INCIDENTS_READ,
        Scopes.AGENTS_READ,
        Scopes.LOGS_READ,
    ]

    # Create new access token
    access_token = auth_backend.create_access_token(
        subject=parent_user,
        scopes=user_scopes,
        expires_delta=timedelta(minutes=30),
        metadata={"auth_type": "refreshed"},
    )

    logger.info("Token refreshed for user: %s", parent_user)

    return LoginResponse(
        access_token=access_token,
        expires_in=1800,  # 30 minutes
        scopes=user_scopes,
    )


@router.post("/logout")
async def logout(
    response: Response,
    token_data: Optional[TokenData] = Depends(get_current_token),
) -> dict[str, str]:
    """Logout and revoke token."""
    if token_data:
        auth_backend = get_auth_backend()
        auth_backend.revoke_token(token_data.jti)
        logger.info("User logged out: %s", token_data.sub)

    # Clear any cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserInfo)
async def get_current_user(
    auth: dict[str, Any] = Depends(require_auth),
    oauth2_user: Optional[dict[str, Any]] = Depends(get_oauth2_user),
) -> UserInfo:
    """Get current user information."""
    if oauth2_user:
        # OAuth2 authenticated user
        return UserInfo(
            user_id=oauth2_user["user_id"],
            email=oauth2_user.get("email"),
            name=oauth2_user.get("name"),
            scopes=oauth2_user["scopes"],
            auth_type="oauth2",
            provider=oauth2_user["provider"],
        )
    else:
        # Token or API key authenticated
        return UserInfo(
            user_id=auth["subject"],
            scopes=auth["scopes"],
            auth_type=auth["type"],
        )


# OAuth2 routes
@router.get("/oauth2/{provider}")
async def oauth2_login(provider: str, request: Request) -> RedirectResponse:
    """Initiate OAuth2 login flow."""
    try:
        oauth_provider = get_oauth2_provider(provider)
    except ValueError as exc:
        raise HTTPException(404, f"OAuth2 provider not found: {provider}") from exc

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state in session (in production, use secure session storage)
    session_id = secrets.token_urlsafe(32)
    _sessions[session_id] = {
        "state": state,
        "provider": provider,
        "created_at": datetime.now(timezone.utc),
    }

    # Set session cookie
    response = RedirectResponse(url=oauth_provider.get_authorization_url(state))
    response.set_cookie(
        "oauth_session",
        session_id,
        max_age=600,  # 10 minutes
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
    )

    return response


@router.get("/oauth2/{provider}/callback")
async def oauth2_callback(
    provider: str,
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
) -> RedirectResponse:
    """Handle OAuth2 callback."""
    # Check for errors
    if error:
        raise HTTPException(400, f"OAuth2 error: {error}")

    if not code or not state:
        raise HTTPException(400, "Missing code or state parameter")

    # Verify state
    session_id = request.cookies.get("oauth_session")
    if not session_id or session_id not in _sessions:
        raise HTTPException(400, "Invalid session")

    session = _sessions.pop(session_id)
    if session["state"] != state:
        raise HTTPException(400, "Invalid state parameter")

    # Check session expiry (10 minutes)
    if datetime.now(timezone.utc) - session["created_at"] > timedelta(minutes=10):
        raise HTTPException(400, "Session expired")

    try:
        # Get OAuth2 provider
        oauth_provider = get_oauth2_provider(provider)

        # Exchange code for token
        token_response = await oauth_provider.exchange_code_for_token(code)

        # Get user info
        access_token = token_response.get("access_token")
        if not access_token:
            raise AuthenticationException("No access token received")

        oauth_user = await oauth_provider.get_user_info(access_token)

        # Create or update user
        session_manager = get_oauth2_session_manager()
        user_id = await session_manager.create_or_update_user(oauth_user)

        # Create JWT token
        jwt_token = session_manager.create_user_token(user_id, oauth_user)

        # Create response with token
        response = RedirectResponse(
            url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/auth/success"
        )

        # Set token in cookie (in production, consider using secure storage)
        response.set_cookie(
            "access_token",
            jwt_token,
            max_age=1800,  # 30 minutes
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
        )

        # Clear OAuth session cookie
        response.delete_cookie("oauth_session")

        logger.info("OAuth2 login successful: %s:%s", provider, oauth_user.sub)

        return response

    except Exception as e:
        logger.error("OAuth2 callback error: %s", e)
        raise HTTPException(500, "Authentication failed") from e


# API Key management
@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: APIKeyRequest,
    auth: dict[str, Any] = Depends(require_auth),
) -> APIKeyResponse:
    """
    Create a new API key.

    Requires admin permissions.
    """
    # Check permissions
    if Scopes.ADMIN_WRITE not in auth["scopes"]:
        raise HTTPException(403, "Insufficient permissions")

    # Validate requested scopes
    requested_scopes = set(request.scopes)
    user_scopes = set(auth["scopes"])

    # User can only grant scopes they have
    if not requested_scopes.issubset(user_scopes):
        invalid_scopes = requested_scopes - user_scopes
        raise HTTPException(
            status_code=400,
            detail=f"Cannot grant scopes you don't have: {', '.join(invalid_scopes)}",
        )

    # Create API key
    auth_backend = get_auth_backend()
    api_key = auth_backend.generate_api_key(
        name=request.name,
        scopes=request.scopes,
    )

    # Calculate expiration
    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=request.expires_in_days
        )

    logger.info("API key created: %s by %s", request.name, auth["subject"])

    return APIKeyResponse(
        api_key=api_key,
        name=request.name,
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at,
        scopes=request.scopes,
    )
