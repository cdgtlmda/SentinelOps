"""
Global exception handlers for FastAPI application.
"""

import traceback
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from ..api.middleware.correlation_id import get_correlation_id
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class SentinelOpsException(Exception):
    """Base exception for all SentinelOps errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class AgentException(SentinelOpsException):
    """Exception raised by agents."""

    def __init__(
        self, agent_name: str, message: str, error_code: str = "AGENT_ERROR", **kwargs: Any
    ) -> None:
        self.agent_name = agent_name
        details = kwargs.get("details", {})
        details["agent_name"] = agent_name
        kwargs["details"] = details
        super().__init__(message, error_code, **kwargs)


class ConfigurationException(SentinelOpsException):
    """Exception for configuration errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(
            message,
            error_code="CONFIG_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            **kwargs,
        )


class AuthenticationException(SentinelOpsException):
    """Exception for authentication failures."""

    def __init__(self, message: str = "Authentication failed", **kwargs: Any) -> None:
        super().__init__(
            message,
            error_code="AUTH_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            **kwargs,
        )


class AuthorizationException(SentinelOpsException):
    """Exception for authorization failures."""

    def __init__(self, message: str = "Insufficient permissions", **kwargs: Any) -> None:
        super().__init__(
            message,
            error_code="AUTHZ_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            **kwargs,
        )


class ResourceNotFoundException(SentinelOpsException):
    """Exception for resource not found."""

    def __init__(self, resource_type: str, resource_id: str, **kwargs: Any) -> None:
        message = f"{resource_type} with id '{resource_id}' not found"
        details = kwargs.get("details", {})
        details.update({"resource_type": resource_type, "resource_id": resource_id})
        kwargs["details"] = details
        super().__init__(
            message,
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            **kwargs,
        )


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
) -> JSONResponse:
    """Create a standardized error response."""
    content: Dict[str, Any] = {
        "error": {
            "code": error_code,
            "message": message,
            "correlation_id": correlation_id or get_correlation_id() or "unknown",
        }
    }

    if details:
        content["error"]["details"] = details

    return JSONResponse(status_code=status_code, content=content)


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Set up global exception handlers for the FastAPI application.

    Args:
        app: The FastAPI application instance
    """

    @app.exception_handler(SentinelOpsException)
    async def sentinelops_exception_handler(
        request: Request, exc: SentinelOpsException
    ) -> JSONResponse:
        """Handle SentinelOps custom exceptions."""
        logger.error(
            "SentinelOps exception: %s", exc.message,
            extra={
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "details": exc.details,
                "path": request.url.path,
            },
        )

        return create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request validation errors."""
        logger.warning(
            "Request validation error",
            extra={"path": request.url.path, "errors": exc.errors()},
        )

        return create_error_response(
            error_code="VALIDATION_ERROR",
            message="Invalid request data",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": exc.errors()},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        # Handle case where detail might be a dict or other type
        detail_message = str(exc.detail) if not isinstance(exc.detail, str) else exc.detail

        logger.warning(
            "HTTP exception: %s", detail_message,
            extra={"status_code": exc.status_code, "path": request.url.path},
        )

        return create_error_response(
            error_code="HTTP_ERROR", message=detail_message, status_code=exc.status_code
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle all unhandled exceptions."""
        # Log full traceback
        logger.error(
            "Unhandled exception: %s", str(exc),
            extra={
                "exception_type": type(exc).__name__,
                "path": request.url.path,
                "traceback": traceback.format_exc(),
            },
            exc_info=True,
        )

        # Don't expose internal details in production
        if app.debug:
            details = {
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc().split("\n"),
            }
        else:
            details = None

        return create_error_response(
            error_code="INTERNAL_ERROR",
            message="An internal error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )

    logger.info("Exception handlers configured")
