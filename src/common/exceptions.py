"""
Custom exceptions and error handling for SentinelOps.

This module defines the exception hierarchy and error handling strategies
used throughout the system.
"""

import asyncio
import logging
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar

# Import timezone-aware utility
from src.utils.datetime_utils import utcnow

T = TypeVar("T")


class ErrorCategory(Enum):
    """Categories of errors for classification and handling."""

    CONFIGURATION = "configuration"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    PROCESSING = "processing"
    EXTERNAL_SERVICE = "external_service"
    RESOURCE_LIMIT = "resource_limit"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Severity levels for errors."""

    CRITICAL = "critical"  # System cannot continue
    HIGH = "high"  # Major functionality impaired
    MEDIUM = "medium"  # Some functionality impaired
    LOW = "low"  # Minor issue, can be ignored
    INFO = "info"  # Informational, not really an error


class SentinelOpsError(Exception):
    """Base exception class for all SentinelOps errors."""

    category = ErrorCategory.UNKNOWN
    severity = ErrorSeverity.MEDIUM
    error_code = "SENTINEL_ERROR"

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the error.

        Args:
            message: Human-readable error message
            details: Additional error details
            cause: The underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause
        self.timestamp = utcnow()
        self.error_id = f"{self.error_code}_{self.timestamp.strftime('%Y%m%d%H%M%S%f')}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation."""
        return {
            "error_id": self.error_id,
            "error_code": self.error_code,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "cause": str(self.cause) if self.cause else None,
        }


# Configuration Errors
class ConfigurationError(SentinelOpsError):
    """Raised when there's a configuration problem."""

    category = ErrorCategory.CONFIGURATION
    severity = ErrorSeverity.HIGH
    error_code = "CONFIG_ERROR"


class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing."""

    error_code = "CONFIG_MISSING"


# Authentication and Authorization Errors
class AuthenticationError(SentinelOpsError):
    """Raised when authentication fails."""

    category = ErrorCategory.AUTHENTICATION
    severity = ErrorSeverity.HIGH
    error_code = "AUTH_ERROR"


class AuthorizationError(SentinelOpsError):
    """Raised when authorization fails."""

    category = ErrorCategory.AUTHORIZATION
    severity = ErrorSeverity.HIGH
    error_code = "AUTHZ_ERROR"


class SecurityError(SentinelOpsError):
    """Raised when there's a security violation or security check failure."""

    category = ErrorCategory.AUTHORIZATION
    severity = ErrorSeverity.CRITICAL
    error_code = "SECURITY_ERROR"


# Network and Communication Errors
class NetworkError(SentinelOpsError):
    """Raised when network operations fail."""

    category = ErrorCategory.NETWORK
    severity = ErrorSeverity.HIGH
    error_code = "NETWORK_ERROR"


class PubSubError(NetworkError):
    """Raised when Pub/Sub operations fail."""

    error_code = "PUBSUB_ERROR"


class OperationTimeoutError(NetworkError):
    """Raised when operations timeout."""

    category = ErrorCategory.TIMEOUT
    error_code = "TIMEOUT_ERROR"


# Processing Errors
class ProcessingError(SentinelOpsError):
    """Raised when message or data processing fails."""

    category = ErrorCategory.PROCESSING
    severity = ErrorSeverity.MEDIUM
    error_code = "PROCESSING_ERROR"


class ValidationError(ProcessingError):
    """Raised when data validation fails."""

    category = ErrorCategory.VALIDATION
    error_code = "VALIDATION_ERROR"


# External Service Errors
class ExternalServiceError(SentinelOpsError):
    """Raised when external service calls fail."""

    category = ErrorCategory.EXTERNAL_SERVICE
    severity = ErrorSeverity.HIGH
    error_code = "EXTERNAL_SERVICE_ERROR"


class GoogleCloudError(ExternalServiceError):
    """Raised when Google Cloud API calls fail."""

    error_code = "GCP_ERROR"


class GeminiError(ExternalServiceError):
    """Raised when Gemini AI calls fail."""

    error_code = "GEMINI_ERROR"


# Resource Errors
class ResourceLimitError(SentinelOpsError):
    """Raised when resource limits are exceeded."""

    category = ErrorCategory.RESOURCE_LIMIT
    severity = ErrorSeverity.HIGH
    error_code = "RESOURCE_LIMIT_ERROR"


class QuotaExceededError(ResourceLimitError):
    """Raised when API quotas are exceeded."""

    error_code = "QUOTA_EXCEEDED"


# Agent-specific Errors
class AgentError(SentinelOpsError):
    """Base class for agent-specific errors."""

    severity = ErrorSeverity.HIGH
    error_code = "AGENT_ERROR"


class DetectionAgentError(AgentError):
    """Errors specific to the detection agent."""

    error_code = "DETECTION_AGENT_ERROR"


class AnalysisAgentError(AgentError):
    """Errors specific to the analysis agent."""

    error_code = "ANALYSIS_AGENT_ERROR"


class RemediationAgentError(AgentError):
    """Errors specific to the remediation agent."""

    error_code = "REMEDIATION_AGENT_ERROR"


class CommunicationAgentError(AgentError):
    """Errors specific to the communication agent."""

    error_code = "COMMUNICATION_AGENT_ERROR"


class OrchestrationAgentError(AgentError):
    """Errors specific to the orchestration agent."""

    error_code = "ORCHESTRATION_AGENT_ERROR"


# Error Handling Strategies
class ErrorHandler:
    """
    Provides error handling strategies and utilities.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the error handler.

        Args:
            logger: Logger instance for error reporting
        """
        self.logger = logger or logging.getLogger(__name__)
        self.error_callbacks: Dict[type, List[Callable[..., Any]]] = {}

    def register_error_callback(
        self, error_type: type, callback: Callable[..., Any]
    ) -> None:
        """
        Register a callback for specific error types.

        Args:
            error_type: Type of error to handle
            callback: Function to call when error occurs
        """
        if error_type not in self.error_callbacks:
            self.error_callbacks[error_type] = []
        self.error_callbacks[error_type].append(callback)

    def handle_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Handle an error with appropriate logging and callbacks.

        Args:
            error: The error to handle
            context: Additional context about where the error occurred
        """
        context = context or {}

        # Log the error
        if isinstance(error, SentinelOpsError):
            self.logger.error(
                f"{error.error_code}: {error.message}",
                extra={"error_details": error.to_dict(), "context": context},
                exc_info=True,
            )
        else:
            self.logger.error(
                f"Unhandled error: {str(error)}",
                extra={"error_type": type(error).__name__, "context": context},
                exc_info=True,
            )

        # Call registered callbacks
        for error_type, callbacks in self.error_callbacks.items():
            if isinstance(error, error_type):
                for callback in callbacks:
                    try:
                        callback(error, context)
                    except (RuntimeError, ValueError, TypeError) as e:
                        self.logger.error("Error in error callback: %s", e)


def retry_on_error(  # noqa: C901
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger: Optional[logging.Logger] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to retry functions on specific exceptions.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Factor to multiply delay by after each retry
        exceptions: Tuple of exceptions to catch and retry on
        logger: Logger for retry messages
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        if logger:
                            logger.warning(
                                f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                                f"after {type(e).__name__}: {str(e)}"
                            )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        if logger:
                            logger.error(f"Max retries exceeded for {func.__name__}")
                        raise

            if last_exception is not None:
                raise last_exception
            else:
                raise RuntimeError("Unexpected error in retry logic")

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    return result
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        if logger:
                            logger.warning(
                                f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                                f"after {type(e).__name__}: {str(e)}"
                            )
                        import time

                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        if logger:
                            logger.error(f"Max retries exceeded for {func.__name__}")
                        raise

            if last_exception is not None:
                raise last_exception
            else:
                raise RuntimeError("Unexpected error in retry logic")

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class GracefulDegradation:
    """
    Provides graceful degradation strategies when errors occur.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize graceful degradation handler."""
        self.logger = logger or logging.getLogger(__name__)
        self.fallback_functions: Dict[str, Callable[..., Any]] = {}

    def register_fallback(
        self, operation: str, fallback_func: Callable[..., Any]
    ) -> None:
        """
        Register a fallback function for an operation.

        Args:
            operation: Name of the operation
            fallback_func: Function to call when operation fails
        """
        self.fallback_functions[operation] = fallback_func

    async def execute_with_fallback(
        self,
        operation: str,
        primary_func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a function with fallback on failure.

        Args:
            operation: Name of the operation
            primary_func: Primary function to execute
            *args, **kwargs: Arguments for the function

        Returns:
            Result from primary or fallback function
        """
        try:
            if asyncio.iscoroutinefunction(primary_func):
                return await primary_func(*args, **kwargs)
            else:
                return primary_func(*args, **kwargs)
        except (ValueError, RuntimeError, AttributeError) as e:
            self.logger.warning(
                f"Primary function failed for {operation}: {e}. "
                f"Attempting fallback."
            )

            if operation in self.fallback_functions:
                fallback = self.fallback_functions[operation]
                try:
                    if asyncio.iscoroutinefunction(fallback):
                        return await fallback(*args, **kwargs)
                    else:
                        return fallback(*args, **kwargs)
                except (ValueError, RuntimeError, AttributeError) as fallback_error:
                    self.logger.error(
                        f"Fallback also failed for {operation}: {fallback_error}"
                    )
                    raise
            else:
                self.logger.error("No fallback registered for %s", operation)
                raise


# Global instances
_error_handler: Optional[ErrorHandler] = None
_graceful_degradation: Optional[GracefulDegradation] = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _error_handler  # pylint: disable=global-statement
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def get_graceful_degradation() -> GracefulDegradation:
    """Get the global graceful degradation instance."""
    global _graceful_degradation  # pylint: disable=global-statement
    if _graceful_degradation is None:
        _graceful_degradation = GracefulDegradation()
    return _graceful_degradation
