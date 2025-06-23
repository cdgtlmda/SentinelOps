"""
Correlation ID middleware for request tracing.
"""

import logging
import uuid
from contextvars import ContextVar
from typing import Awaitable, Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Context variable to store correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID from context."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID in context."""
    correlation_id_var.set(correlation_id)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation ID to all requests.

    The correlation ID is used to trace requests across services
    and correlate logs for a single request.
    """

    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Correlation-ID",
        generator: Optional[Callable[[], str]] = None,
    ):
        """
        Initialize the middleware.

        Args:
            app: The ASGI application
            header_name: Name of the correlation ID header
            generator: Optional function to generate correlation IDs
        """
        super().__init__(app)
        self.header_name = header_name
        self.generator = generator or self._default_generator

    def _default_generator(self) -> str:
        """Default correlation ID generator using UUID4."""
        return str(uuid.uuid4())

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process the request and add correlation ID.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            The response with correlation ID header
        """
        # Get or generate correlation ID
        correlation_id = request.headers.get(self.header_name, self.generator())

        # Set correlation ID in context
        set_correlation_id(correlation_id)

        # Add correlation ID to logging context
        logger = logging.getLogger("sentinelops")
        adapter = logging.LoggerAdapter(logger, {"correlation_id": correlation_id})

        # Log request
        adapter.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "correlation_id": correlation_id,
            },
        )

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers[self.header_name] = correlation_id

        # Log response
        adapter.info(
            f"Request completed: {response.status_code}",
            extra={
                "status_code": response.status_code,
                "correlation_id": correlation_id,
            },
        )

        return response


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter to add correlation ID to log records.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add correlation ID to the log record.

        Args:
            record: The log record

        Returns:
            True to include the record
        """
        # Get correlation ID from context
        correlation_id = get_correlation_id()

        # Add to record
        record.correlation_id = correlation_id or "no-correlation-id"

        return True
