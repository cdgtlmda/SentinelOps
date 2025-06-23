"""
Interfaces and base classes for the Communication Agent.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.communication_agent.types import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
)


@dataclass
class NotificationRequest:
    """Request to send a notification."""

    channel: NotificationChannel
    recipient: str
    subject: str
    body: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    metadata: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    retry_count: int = 0
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


@dataclass
class NotificationResult:
    """Result of a notification attempt."""

    success: bool
    status: NotificationStatus
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class NotificationService(ABC):
    """Base interface for notification services."""

    @abstractmethod
    async def send(self, request: NotificationRequest) -> NotificationResult:
        """
        Send a notification.

        Args:
            request: Notification request

        Returns:
            NotificationResult with status and details
        """

    @abstractmethod
    async def validate_recipient(self, recipient: str) -> bool:
        """
        Validate a recipient address/identifier.

        Args:
            recipient: Recipient to validate

        Returns:
            True if valid, False otherwise
        """

    @abstractmethod
    async def get_channel_limits(self) -> Dict[str, Any]:
        """
        Get channel-specific limits and capabilities.

        Returns:
            Dictionary of limits (e.g., max_message_size, rate_limits)
        """

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check service health.

        Returns:
            Health status information
        """

    @abstractmethod
    def get_channel_type(self) -> NotificationChannel:
        """
        Get the notification channel type.

        Returns:
            The notification channel type
        """
