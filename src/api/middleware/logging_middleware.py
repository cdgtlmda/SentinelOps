"""
Middleware for FastAPI to handle correlation IDs and logging context.
"""

import logging
import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.logging import CorrelationIdFilter, get_logger

logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation ID to requests for distributed tracing.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # Add correlation ID to request state
        request.state.correlation_id = correlation_id

        # Set correlation ID in logging filter
        correlation_filter = None
        for handler in logging.root.handlers:
            for filt in handler.filters:
                if isinstance(filt, CorrelationIdFilter):
                    correlation_filter = filt
                    break

        if correlation_filter:
            correlation_filter.set_correlation_id(correlation_id)

        # Log incoming request
        logger.info(
            "Incoming request: %s %s", request.method, request.url.path,
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None,
                "correlation_id": correlation_id,
            },
        )

        # Process request
        response: Response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        # Log response
        logger.info(
            "Request completed: %s %s - %s", request.method, request.url.path, response.status_code,
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "correlation_id": correlation_id,
            },
        )

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Additional logging middleware for detailed request/response logging.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Log request details
        logger.debug(
            "Request details",
            extra={
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
                "path_params": request.path_params,
                "correlation_id": getattr(request.state, "correlation_id", None),
            },
        )

        try:
            response: Response = await call_next(request)
            return response
        except Exception as e:
            logger.error(
                "Unhandled exception in request: %s", str(e),
                exc_info=True,
                extra={
                    "correlation_id": getattr(request.state, "correlation_id", None),
                    "path": request.url.path,
                    "method": request.method,
                },
            )
            raise
