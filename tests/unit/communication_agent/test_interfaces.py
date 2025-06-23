"""
Tests for communication agent interfaces - real implementation, no mocks.
"""

from datetime import datetime, timezone
from typing import Dict, Any
import pytest

from src.communication_agent.interfaces import (
    NotificationRequest,
    NotificationResult,
    NotificationService,
)
from src.communication_agent.types import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
)


class TestNotificationRequest:
    """Test NotificationRequest dataclass."""

    def test_create_minimal_request(self) -> None:
        """Test creating a notification request with minimal required fields."""
        request = NotificationRequest(
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            subject="Test Subject",
            body="Test Body",
        )

        assert request.channel == NotificationChannel.EMAIL
        assert request.recipient == "user@example.com"
        assert request.subject == "Test Subject"
        assert request.body == "Test Body"
        assert request.priority == NotificationPriority.MEDIUM  # default
        assert request.metadata is None
        assert request.attachments is None
        assert request.retry_count == 0
        assert isinstance(request.created_at, datetime)
        assert request.created_at.tzinfo == timezone.utc

    def test_create_full_request(self) -> None:
        """Test creating a notification request with all fields."""
        now = datetime.now(timezone.utc)
        metadata = {"incident_id": "INC-123", "severity": "high"}
        attachments = [{"filename": "report.pdf", "size": 1024}]

        request = NotificationRequest(
            channel=NotificationChannel.SLACK,
            recipient="#incidents",
            subject="Critical Incident",
            body="Database connection pool exhausted",
            priority=NotificationPriority.CRITICAL,
            metadata=metadata,
            attachments=attachments,
            retry_count=2,
            created_at=now,
        )

        assert request.channel == NotificationChannel.SLACK
        assert request.recipient == "#incidents"
        assert request.subject == "Critical Incident"
        assert request.body == "Database connection pool exhausted"
        assert request.priority == NotificationPriority.CRITICAL
        assert request.metadata == metadata
        assert request.attachments == attachments
        assert request.retry_count == 2
        assert request.created_at == now

    def test_created_at_auto_generation(self) -> None:
        """Test that created_at is automatically set when not provided."""
        before = datetime.now(timezone.utc)

        request = NotificationRequest(
            channel=NotificationChannel.SMS,
            recipient="+1234567890",
            subject="Alert",
            body="System alert",
        )
        after = datetime.now(timezone.utc)

        assert request.created_at is not None
        assert before <= request.created_at <= after
        assert request.created_at.tzinfo == timezone.utc

    def test_different_notification_channels(self) -> None:
        """Test requests with various notification channels."""
        channels_and_recipients = [
            (NotificationChannel.EMAIL, "admin@company.com"),
            (NotificationChannel.SLACK, "#security-alerts"),
            (NotificationChannel.SMS, "+15551234567"),
            (NotificationChannel.WEBHOOK, "https://api.company.com/webhook"),
        ]

        for channel, recipient in channels_and_recipients:
            request = NotificationRequest(
                channel=channel,
                recipient=recipient,
                subject=f"{channel.value} notification",
                body="Test notification",
            )
            assert request.channel == channel
            assert request.recipient == recipient

    def test_all_priority_levels(self) -> None:
        """Test requests with all priority levels."""
        priorities = [
            NotificationPriority.LOW,
            NotificationPriority.MEDIUM,
            NotificationPriority.HIGH,
            NotificationPriority.CRITICAL,
        ]

        for priority in priorities:
            request = NotificationRequest(
                channel=NotificationChannel.EMAIL,
                recipient="test@example.com",
                subject=f"{priority.value} priority",
                body="Priority test",
                priority=priority,
            )
            assert request.priority == priority


class TestNotificationResult:
    """Test NotificationResult dataclass."""

    def test_create_success_result(self) -> None:
        """Test creating a successful notification result."""
        result = NotificationResult(
            success=True, status=NotificationStatus.SENT, message_id="msg-12345"
        )

        assert result.success is True
        assert result.status == NotificationStatus.SENT
        assert result.message_id == "msg-12345"
        assert result.error is None
        assert isinstance(result.timestamp, datetime)
        assert result.timestamp.tzinfo == timezone.utc
        assert result.metadata is None

    def test_create_failure_result(self) -> None:
        """Test creating a failed notification result."""
        result = NotificationResult(
            success=False,
            status=NotificationStatus.FAILED,
            error="SMTP connection timeout",
        )

        assert result.success is False
        assert result.status == NotificationStatus.FAILED
        assert result.message_id is None
        assert result.error == "SMTP connection timeout"
        assert isinstance(result.timestamp, datetime)

    def test_create_result_with_all_fields(self) -> None:
        """Test creating a result with all fields specified."""
        now = datetime.now(timezone.utc)
        metadata = {"provider": "twilio", "cost": 0.01, "delivery_time_ms": 250}

        result = NotificationResult(
            success=True,
            status=NotificationStatus.SENT,
            message_id="tw-98765",
            error=None,
            timestamp=now,
            metadata=metadata,
        )

        assert result.success is True
        assert result.status == NotificationStatus.SENT
        assert result.message_id == "tw-98765"
        assert result.error is None
        assert result.timestamp == now
        assert result.metadata == metadata

    def test_timestamp_auto_generation(self) -> None:
        """Test that timestamp is automatically set when not provided."""
        before = datetime.now(timezone.utc)

        result = NotificationResult(success=True, status=NotificationStatus.QUEUED)

        after = datetime.now(timezone.utc)

        assert result.timestamp is not None
        assert before <= result.timestamp <= after
        assert result.timestamp.tzinfo == timezone.utc

    def test_all_notification_statuses(self) -> None:
        """Test results with all possible notification statuses."""
        status_success_map = [
            (NotificationStatus.PENDING, False),
            (NotificationStatus.QUEUED, False),
            (NotificationStatus.SENDING, False),
            (NotificationStatus.SENT, True),
            (NotificationStatus.FAILED, False),
            (NotificationStatus.RETRYING, False),
        ]

        for status, expected_success in status_success_map:
            result = NotificationResult(success=expected_success, status=status)
            assert result.status == status
            assert result.success == expected_success


class TestNotificationService:
    """Test NotificationService abstract base class."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Test that NotificationService cannot be instantiated directly."""
        # Note: This test validates that the class is properly abstract
        # The abstract class will raise TypeError if instantiated directly
        with pytest.raises(TypeError) as exc_info:
            NotificationService()  # type: ignore[abstract]  # pylint: disable=abstract-class-instantiated
        assert "abstract" in str(exc_info.value).lower() or "instantiate" in str(exc_info.value).lower()

    def test_concrete_implementation_required(self) -> None:
        """Test that a concrete implementation must implement all abstract methods."""

        class IncompleteService(NotificationService):
            """Service missing some abstract method implementations."""

            async def send(self, request: NotificationRequest) -> NotificationResult:
                return NotificationResult(success=True, status=NotificationStatus.SENT)

        # This should fail because not all abstract methods are implemented
        with pytest.raises(TypeError):
            IncompleteService()  # type: ignore[abstract]  # pylint: disable=abstract-class-instantiated

    @pytest.mark.asyncio
    async def test_valid_concrete_implementation(self) -> None:
        """Test that a complete concrete implementation works correctly."""

        class EmailService(NotificationService):
            """Complete concrete implementation of NotificationService."""

            async def send(self, request: NotificationRequest) -> NotificationResult:
                # Simulate email sending logic
                if "@" not in request.recipient:
                    return NotificationResult(
                        success=False,
                        status=NotificationStatus.FAILED,
                        error="Invalid email address",
                    )
                return NotificationResult(
                    success=True,
                    status=NotificationStatus.SENT,
                    message_id=f"email-{request.created_at.timestamp() if request.created_at else 'unknown'}",
                )

            async def validate_recipient(self, recipient: str) -> bool:
                return "@" in recipient and "." in recipient.split("@")[1]

            async def get_channel_limits(self) -> Dict[str, Any]:
                return {
                    "max_message_size": 10 * 1024 * 1024,  # 10MB
                    "max_recipients": 50,
                    "rate_limit": "100/hour",
                }

            async def health_check(self) -> Dict[str, Any]:
                return {"status": "healthy", "smtp_connected": True, "queue_size": 0}

            def get_channel_type(self) -> NotificationChannel:
                return NotificationChannel.EMAIL

        # Should be able to instantiate the complete implementation
        service = EmailService()  # pylint: disable=abstract-class-instantiated

        # Test sending a valid email
        request = NotificationRequest(
            channel=NotificationChannel.EMAIL,
            recipient="test@example.com",
            subject="Test",
            body="Test email",
        )
        result = await service.send(request)
        assert result.success is True
        assert result.status == NotificationStatus.SENT
        assert result.message_id is not None
        assert result.message_id.startswith("email-")

        # Test sending to invalid recipient
        bad_request = NotificationRequest(
            channel=NotificationChannel.EMAIL,
            recipient="not-an-email",
            subject="Test",
            body="Test",
        )
        bad_result = await service.send(bad_request)
        assert bad_result.success is False
        assert bad_result.status == NotificationStatus.FAILED
        assert bad_result.error == "Invalid email address"

        # Test validate_recipient
        assert await service.validate_recipient("valid@example.com") is True
        assert await service.validate_recipient("invalid@") is False
        assert await service.validate_recipient("no-at-sign") is False

        # Test get_channel_limits
        limits = await service.get_channel_limits()
        assert limits["max_message_size"] == 10 * 1024 * 1024
        assert limits["max_recipients"] == 50

        # Test health_check
        health = await service.health_check()
        assert health["status"] == "healthy"
        assert health["smtp_connected"] is True
