"""
Custom exceptions for SentinelOps.
"""

from typing import Any, Optional


class SentinelOpsError(Exception):
    """Base exception for all SentinelOps errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(SentinelOpsError):
    """Raised when authentication fails."""


class AuthorizationError(SentinelOpsError):
    """Raised when authorization fails."""


class ValidationError(SentinelOpsError):
    """Raised when data validation fails."""

    def __init__(
        self, message: str, errors: Optional[list[dict[str, Any]]] = None
    ) -> None:
        super().__init__(message)
        self.errors = errors or []


class ResourceNotFoundError(SentinelOpsError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: str) -> None:
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} with identifier '{identifier}' not found")


class ConfigurationError(SentinelOpsError):
    """Raised when there's a configuration error."""


class AgentError(SentinelOpsError):
    """Base exception for agent-related errors."""

    def __init__(
        self,
        agent_id: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.agent_id = agent_id
        super().__init__(f"Agent {agent_id}: {message}", details)


class AgentInitializationError(AgentError):
    """Raised when an agent fails to initialize."""


class AgentCommunicationError(AgentError):
    """Raised when agent communication fails."""


class AgentTimeoutError(AgentError):
    """Raised when an agent operation times out."""


class AnalysisError(SentinelOpsError):
    """Raised when security analysis fails."""


class RemediationError(SentinelOpsError):
    """Raised when remediation action fails."""

    def __init__(
        self, action: str, reason: str, *, rollback_possible: bool = False
    ) -> None:
        self.action = action
        self.reason = reason
        self.rollback_possible = rollback_possible
        super().__init__(f"Remediation action '{action}' failed: {reason}")


class GoogleCloudError(SentinelOpsError):
    """Raised when Google Cloud API operations fail."""

    def __init__(self, service: str, operation: str, message: str) -> None:
        self.service = service
        self.operation = operation
        super().__init__(f"Google Cloud {service} error during {operation}: {message}")


class GeminiAPIError(SentinelOpsError):
    """Raised when Gemini API calls fail."""


class RateLimitError(SentinelOpsError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self, limit: int, window: int, retry_after: Optional[int] = None
    ) -> None:
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        message = f"Rate limit exceeded: {limit} requests per {window} seconds"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message)


class IncidentError(SentinelOpsError):
    """Raised when incident handling fails."""

    def __init__(self, incident_id: str, message: str) -> None:
        self.incident_id = incident_id
        super().__init__(f"Incident {incident_id}: {message}")


class NotificationError(SentinelOpsError):
    """Raised when notification delivery fails."""

    def __init__(self, channel: str, message: str) -> None:
        self.channel = channel
        super().__init__(f"Notification to {channel} failed: {message}")
