"""
Security configuration for SentinelOps API.
"""

import os
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..config.logging_config import get_logger

logger = get_logger(__name__)


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Wrapper for rate limit exceeded handler to match FastAPI's expected signature."""
    if isinstance(exc, RateLimitExceeded):
        return _rate_limit_exceeded_handler(request, exc)
    # This should never happen, but satisfy type checker
    raise exc

# Security settings from environment
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds


class SecurityConfig:
    """Security configuration settings."""

    def __init__(self) -> None:
        # CORS settings
        self.cors_allow_origins = ALLOWED_ORIGINS
        self.cors_allow_credentials = True
        self.cors_allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        self.cors_allow_headers = ["*"]
        self.cors_expose_headers = [
            "X-Correlation-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
        ]

        # Trusted hosts
        self.allowed_hosts = ALLOWED_HOSTS

        # Rate limiting
        self.rate_limit_enabled = RATE_LIMIT_ENABLED
        self.rate_limit_default = f"{RATE_LIMIT_REQUESTS}/{RATE_LIMIT_WINDOW} seconds"

        # Security headers
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

        # API key settings
        self.api_key_header = "X-API-Key"
        self.api_key_enabled = os.getenv("API_KEY_ENABLED", "false").lower() == "true"

        # JWT settings
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_minutes = int(os.getenv("JWT_EXPIRATION_MINUTES", "30"))


# Global security config
_security_config = SecurityConfig()


def get_security_config() -> SecurityConfig:
    """Get security configuration."""
    return _security_config


def setup_cors(app: FastAPI, config: Optional[SecurityConfig] = None) -> None:
    """
    Configure CORS middleware.

    Args:
        app: FastAPI application instance
        config: Security configuration (uses default if None)
    """
    if config is None:
        config = get_security_config()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_allow_origins,
        allow_credentials=config.cors_allow_credentials,
        allow_methods=config.cors_allow_methods,
        allow_headers=config.cors_allow_headers,
        expose_headers=config.cors_expose_headers,
    )

    logger.info("CORS configured with origins: %s", config.cors_allow_origins)


def setup_trusted_hosts(app: FastAPI, config: Optional[SecurityConfig] = None) -> None:
    """
    Configure trusted host middleware.

    Args:
        app: FastAPI application instance
        config: Security configuration
    """
    if config is None:
        config = get_security_config()

    if config.allowed_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.allowed_hosts)

        logger.info("Trusted hosts configured: %s", config.allowed_hosts)


def get_rate_limit_key(request: Request) -> str:
    """
    Get rate limit key based on user authentication or IP address.

    Args:
        request: FastAPI request

    Returns:
        Rate limit key
    """
    # Try to get authenticated user from request state
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.get('sub', 'unknown')}"

    # Try to get API key from headers
    api_key = request.headers.get("X-API-Key")
    if api_key:
        # Use first 8 chars of API key for rate limiting
        return f"api_key:{api_key[:8]}"

    # Fall back to IP address
    return get_remote_address(request)


# Create rate limiter
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=(
        [get_security_config().rate_limit_default] if RATE_LIMIT_ENABLED else []
    ),
    storage_uri="memory://",
    headers_enabled=True,  # Add rate limit headers to responses
)


def setup_rate_limiting(app: FastAPI, config: Optional[SecurityConfig] = None) -> None:
    """
    Configure rate limiting.

    Args:
        app: FastAPI application instance
        config: Security configuration
    """
    if config is None:
        config = get_security_config()

    if not config.rate_limit_enabled:
        logger.info("Rate limiting disabled")
        return

    # Add rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)  # type: ignore[arg-type]

    # Add SlowAPI middleware
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    logger.info("Rate limiting configured: %s", config.rate_limit_default)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""

    def __init__(self, app: Any, headers: Dict[str, str]) -> None:
        super().__init__(app)
        self.headers = headers

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        response = await call_next(request)

        # Add security headers
        for header, value in self.headers.items():
            response.headers[header] = value

        return response


def setup_security_headers(
    app: FastAPI, config: Optional[SecurityConfig] = None
) -> None:
    """
    Configure security headers middleware.

    Args:
        app: FastAPI application instance
        config: Security configuration
    """
    if config is None:
        config = get_security_config()

    app.add_middleware(SecurityHeadersMiddleware, headers=config.security_headers)

    logger.info("Security headers configured")


def setup_all_security(app: FastAPI, config: Optional[SecurityConfig] = None) -> None:
    """
    Configure all security middleware.

    Args:
        app: FastAPI application instance
        config: Security configuration
    """
    if config is None:
        config = get_security_config()

    # Order matters - some middleware should be applied first
    setup_security_headers(app, config)
    setup_trusted_hosts(app, config)
    setup_cors(app, config)
    setup_rate_limiting(app, config)

    logger.info("All security middleware configured")


# Rate limiting decorators for specific endpoints
DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., Any])


def rate_limit(limit: str) -> Callable[[DecoratedCallable], DecoratedCallable]:
    """
    Custom rate limit decorator for specific endpoints.

    Args:
        limit: Rate limit string (e.g., "10/minute", "100/hour")

    Usage:
        @router.get("/endpoint")
        @rate_limit("10/minute")
        async def endpoint():
            ...
    """

    def decorator(func: DecoratedCallable) -> DecoratedCallable:
        return cast(DecoratedCallable, limiter.limit(limit)(func))

    return decorator


# Common rate limit presets
class RateLimits:
    """Common rate limit presets."""

    # Authentication endpoints
    AUTH_LOGIN = "5/minute"
    AUTH_REGISTER = "3/minute"
    AUTH_PASSWORD_RESET = "3/hour"

    # API endpoints
    API_DEFAULT = "100/minute"
    API_HEAVY = "10/minute"
    API_SEARCH = "30/minute"

    # Admin endpoints
    ADMIN_DEFAULT = "1000/minute"

    # Health checks (more permissive)
    HEALTH_CHECK = "1000/minute"


# Example middleware for request validation
class RequestValidationMiddleware:
    """Middleware for additional request validation."""

    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, request: Request, call_next: Any) -> Any:
        # Validate content type for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")

            if not content_type.startswith(("application/json", "multipart/form-data")):
                return HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Content-Type must be application/json or multipart/form-data",
                )

        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length:
            max_size = 10 * 1024 * 1024  # 10MB
            if int(content_length) > max_size:
                return HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Request size exceeds maximum allowed size of {max_size} bytes",
                )

        response = await call_next(request)
        return response
