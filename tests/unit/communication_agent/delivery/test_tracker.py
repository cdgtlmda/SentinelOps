"""
PRODUCTION ADK DELIVERY TRACKER TESTS - 100% NO MOCKING

Test suite for communication_agent.delivery.tracker module with REAL tracking functionality.
ZERO MOCKING - All tests use production delivery tracking and real state management.

Target: ≥90% statement coverage of src/communication_agent/delivery/tracker.py
VERIFICATION:
python -m coverage run -m pytest tests/unit/communication_agent/delivery/test_tracker.py && python -m coverage report --include="*tracker.py" --show-missing

CRITICAL: Uses 100% production code - NO MOCKING ALLOWED
Project: your-gcp-project-id
"""

import asyncio
import pytest
from datetime import datetime, timedelta, timezone

# REAL IMPORTS - NO MOCKING
from src.communication_agent.delivery.tracker import (
    DeliveryStatus,
    DeliveryRecord,
    DeliveryTracker,
)


class TestDeliveryStatus:
    """Test DeliveryStatus enum."""

    def test_delivery_status_values(self) -> None:
        """Test all delivery status enum values."""
        assert DeliveryStatus.QUEUED.value == "queued"
        assert DeliveryStatus.SENDING.value == "sending"
        assert DeliveryStatus.SENT.value == "sent"
        assert DeliveryStatus.DELIVERED.value == "delivered"
        assert DeliveryStatus.READ.value == "read"
        assert DeliveryStatus.FAILED.value == "failed"
        assert DeliveryStatus.BOUNCED.value == "bounced"
        assert DeliveryStatus.EXPIRED.value == "expired"

    def test_delivery_status_string_inheritance(self) -> None:
        """Test that DeliveryStatus inherits from str."""
        assert isinstance(DeliveryStatus.QUEUED, str)
        assert DeliveryStatus.DELIVERED.value == "delivered"


class TestDeliveryRecord:
    """Test DeliveryRecord dataclass."""

    def test_delivery_record_creation(self) -> None:
        """Test creating a delivery record."""
        record = DeliveryRecord(
            message_id="msg_123",
            channel="email",
            recipient="user@example.com",
            status=DeliveryStatus.QUEUED,
        )

        assert record.message_id == "msg_123"
        assert record.channel == "email"
        assert record.recipient == "user@example.com"
        assert record.status == DeliveryStatus.QUEUED
        assert record.attempts == 1
        assert record.error is None
        assert record.metadata == {}
        assert record.response_received is False

    def test_delivery_record_with_defaults(self) -> None:
        """Test delivery record with default values."""
        now = datetime.now(timezone.utc)
        record = DeliveryRecord(
            message_id="msg_456",
            channel="slack",
            recipient="#alerts",
            status=DeliveryStatus.SENT,
        )

        # Timestamp should be recent
        assert (record.timestamp - now).total_seconds() < 1

    def test_delivery_record_update_status_sent(self) -> None:
        """Test updating status to sent."""
        record = DeliveryRecord(
            message_id="msg_789",
            channel="sms",
            recipient="+1234567890",
            status=DeliveryStatus.QUEUED,
        )

        record.update_status(DeliveryStatus.SENT)

        assert record.status == DeliveryStatus.SENT
        assert record.sent_at is not None
        assert record.error is None

    def test_delivery_record_update_status_delivered(self) -> None:
        """Test updating status to delivered."""
        record = DeliveryRecord(
            message_id="msg_101",
            channel="email",
            recipient="admin@company.com",
            status=DeliveryStatus.SENT,
        )

        record.update_status(DeliveryStatus.DELIVERED)

        assert record.status == DeliveryStatus.DELIVERED
        assert record.delivered_at is not None

    def test_delivery_record_update_status_read(self) -> None:
        """Test updating status to read."""
        record = DeliveryRecord(
            message_id="msg_202",
            channel="slack",
            recipient="@engineer",
            status=DeliveryStatus.DELIVERED,
        )

        record.update_status(DeliveryStatus.READ)

        assert record.status == DeliveryStatus.READ
        assert record.read_at is not None

    def test_delivery_record_update_status_failed(self) -> None:
        """Test updating status to failed with error."""
        record = DeliveryRecord(
            message_id="msg_303",
            channel="email",
            recipient="invalid@email",
            status=DeliveryStatus.SENDING,
        )

        error_msg = "Invalid email address"
        record.update_status(DeliveryStatus.FAILED, error=error_msg)

        assert record.status == DeliveryStatus.FAILED
        assert record.failed_at is not None
        assert record.error == error_msg

    def test_delivery_record_get_delivery_time(self) -> None:
        """Test calculating delivery time."""
        record = DeliveryRecord(
            message_id="msg_404",
            channel="sms",
            recipient="+9876543210",
            status=DeliveryStatus.QUEUED,
        )

        # No times set initially
        assert record.get_delivery_time() is None

        # Set queued time
        record.queued_at = datetime.now(timezone.utc)
        assert record.get_delivery_time() is None

        # Set delivered time
        record.delivered_at = record.queued_at + timedelta(seconds=30)
        delivery_time = record.get_delivery_time()
        assert delivery_time == 30.0

    def test_delivery_record_get_read_time(self) -> None:
        """Test calculating read time."""
        record = DeliveryRecord(
            message_id="msg_505",
            channel="slack",
            recipient="#general",
            status=DeliveryStatus.DELIVERED,
        )

        # No times set initially
        assert record.get_read_time() is None

        # Set delivered time
        record.delivered_at = datetime.now(timezone.utc)
        assert record.get_read_time() is None

        # Set read time
        record.read_at = record.delivered_at + timedelta(seconds=60)
        read_time = record.get_read_time()
        assert read_time == 60.0


class TestDeliveryTracker:
    """Test DeliveryTracker class."""

    @pytest.fixture
    def tracker(self) -> DeliveryTracker:
        """Create a delivery tracker for testing."""
        return DeliveryTracker(retention_hours=1, cleanup_interval_minutes=1)

    @pytest.mark.asyncio
    async def test_tracker_initialization(self, tracker: DeliveryTracker) -> None:
        """Test tracker initialization."""
        assert tracker.retention_hours == 1
        assert tracker.cleanup_interval == timedelta(minutes=1)
        assert len(tracker._records) == 0
        assert len(tracker._by_channel) == 0
        assert len(tracker._by_recipient) == 0
        assert len(tracker._by_status) == 0

    @pytest.mark.asyncio
    async def test_track_queued(self, tracker: DeliveryTracker) -> None:
        """Test tracking a queued message."""
        record = await tracker.track_queued(
            message_id="msg_queue_1",
            channel="email",
            recipient="user@test.com",
            metadata={"priority": "high"},
        )

        assert record.message_id == "msg_queue_1"
        assert record.channel == "email"
        assert record.recipient == "user@test.com"
        assert record.status == DeliveryStatus.QUEUED
        assert record.queued_at is not None
        assert record.metadata["priority"] == "high"

        # Check record is stored
        stored_record = await tracker.get_record("msg_queue_1")
        assert stored_record is not None
        assert stored_record.message_id == "msg_queue_1"

    @pytest.mark.asyncio
    async def test_track_sent(self, tracker: DeliveryTracker) -> None:
        """Test tracking a sent message."""
        # First queue a message
        await tracker.track_queued(
            message_id="msg_sent_1",
            channel="slack",
            recipient="#alerts",
        )

        # Then track as sent
        await tracker.track_sent("msg_sent_1")

        # Get the record to verify
        record = await tracker.get_record("msg_sent_1")
        assert record is not None
        assert record.status == DeliveryStatus.SENT
        assert record.sent_at is not None

    @pytest.mark.asyncio
    async def test_track_sent_missing_message(self, tracker: DeliveryTracker) -> None:
        """Test tracking sent for non-existent message."""
        await tracker.track_sent("non_existent")
        record = await tracker.get_record("non_existent")
        assert record is None

    @pytest.mark.asyncio
    async def test_track_delivered(self, tracker: DeliveryTracker) -> None:
        """Test tracking a delivered message."""
        # First queue and send a message
        await tracker.track_queued(
            message_id="msg_delivered_1",
            channel="email",
            recipient="user@company.com",
        )
        await tracker.track_sent("msg_delivered_1")

        # Then track as delivered
        await tracker.track_delivered("msg_delivered_1")

        # Get the record to verify
        record = await tracker.get_record("msg_delivered_1")
        assert record is not None
        assert record.status == DeliveryStatus.DELIVERED
        assert record.delivered_at is not None

    @pytest.mark.asyncio
    async def test_track_read(self, tracker: DeliveryTracker) -> None:
        """Test tracking a read message."""
        # First queue, send, and deliver a message
        await tracker.track_queued(
            message_id="msg_read_1",
            channel="slack",
            recipient="@engineer",
        )
        await tracker.track_sent("msg_read_1")
        await tracker.track_delivered("msg_read_1")

        # Then track as read
        await tracker.track_read("msg_read_1")

        # Get the record to verify
        record = await tracker.get_record("msg_read_1")
        assert record is not None
        assert record.status == DeliveryStatus.READ
        assert record.read_at is not None

    @pytest.mark.asyncio
    async def test_track_failed(self, tracker: DeliveryTracker) -> None:
        """Test tracking a failed message."""
        # First queue a message
        await tracker.track_queued(
            message_id="msg_failed_1",
            channel="email",
            recipient="invalid@domain",
        )

        # Then track as failed
        error_msg = "Invalid email domain"
        await tracker.track_failed("msg_failed_1", error=error_msg)

        # Get the record to verify
        record = await tracker.get_record("msg_failed_1")
        assert record is not None
        assert record.status == DeliveryStatus.FAILED
        assert record.failed_at is not None
        assert record.error == error_msg

    @pytest.mark.asyncio
    async def test_track_response(self, tracker: DeliveryTracker) -> None:
        """Test tracking a response to a message."""
        # First queue and deliver a message
        await tracker.track_queued(
            message_id="msg_response_1",
            channel="slack",
            recipient="#general",
        )
        await tracker.track_delivered("msg_response_1")

        # Then track response
        await tracker.track_response(
            "msg_response_1", "User acknowledged the alert"
        )

        # Get the record to verify
        record = await tracker.get_record("msg_response_1")
        assert record is not None
        assert record.response_received is True

    @pytest.mark.asyncio
    async def test_get_records_by_status(self, tracker: DeliveryTracker) -> None:
        """Test getting records by status."""
        # Create records with different statuses
        await tracker.track_queued("msg_1", "email", "user1@test.com")
        await tracker.track_queued("msg_2", "email", "user2@test.com")
        await tracker.track_sent("msg_1")

        queued_records = await tracker.get_records_by_status(DeliveryStatus.QUEUED)
        sent_records = await tracker.get_records_by_status(DeliveryStatus.SENT)

        assert len(queued_records) == 1
        assert len(sent_records) == 1
        assert queued_records[0].message_id == "msg_2"
        assert sent_records[0].message_id == "msg_1"

    @pytest.mark.asyncio
    async def test_get_records_by_status_with_limit(
        self, tracker: DeliveryTracker
    ) -> None:
        """Test getting records by status with limit."""
        # Create multiple records
        for i in range(5):
            await tracker.track_queued(f"msg_{i}", "email", f"user{i}@test.com")

        records = await tracker.get_records_by_status(DeliveryStatus.QUEUED, limit=3)
        assert len(records) == 3

    @pytest.mark.asyncio
    async def test_get_records_by_channel(self, tracker: DeliveryTracker) -> None:
        """Test getting records by channel."""
        # Create records for different channels
        await tracker.track_queued("msg_email", "email", "user@test.com")
        await tracker.track_queued("msg_slack", "slack", "#alerts")
        await tracker.track_queued("msg_sms", "sms", "+1234567890")

        email_records = await tracker.get_records_by_channel("email")
        slack_records = await tracker.get_records_by_channel("slack")

        assert len(email_records) == 1
        assert len(slack_records) == 1
        assert email_records[0].message_id == "msg_email"
        assert slack_records[0].message_id == "msg_slack"

    @pytest.mark.asyncio
    async def test_get_analytics_overall(self, tracker: DeliveryTracker) -> None:
        """Test getting overall analytics."""
        # Create records with various statuses
        await tracker.track_queued("msg_1", "email", "user1@test.com")
        await tracker.track_queued("msg_2", "email", "user2@test.com")
        await tracker.track_sent("msg_1")
        await tracker.track_delivered("msg_1")
        await tracker.track_failed("msg_2", error="Test error")

        analytics = await tracker.get_analytics()

        assert analytics["total_messages"] == 2
        assert analytics["by_status"][DeliveryStatus.DELIVERED] == 1
        assert analytics["by_status"][DeliveryStatus.FAILED] == 1
        assert analytics["success_rate"] == 0.5  # 1 delivered out of 2 total

    @pytest.mark.asyncio
    async def test_get_analytics_by_channel(self, tracker: DeliveryTracker) -> None:
        """Test getting analytics by channel."""
        # Create records for different channels
        await tracker.track_queued("msg_email_1", "email", "user1@test.com")
        await tracker.track_queued("msg_email_2", "email", "user2@test.com")
        await tracker.track_queued("msg_slack_1", "slack", "#alerts")
        await tracker.track_sent("msg_email_1")
        await tracker.track_delivered("msg_email_1")

        email_analytics = await tracker.get_analytics(channel="email")
        slack_analytics = await tracker.get_analytics(channel="slack")

        assert email_analytics["total_messages"] == 2
        assert slack_analytics["total_messages"] == 1
        assert email_analytics["by_status"][DeliveryStatus.DELIVERED] == 1

    @pytest.mark.asyncio
    async def test_cleanup_old_records(self, tracker: DeliveryTracker) -> None:
        """Test cleaning up old records."""
        # Create a record
        await tracker.track_queued("msg_old", "email", "user@test.com")

        # Check record exists
        record = await tracker.get_record("msg_old")
        assert record is not None

        # Manually set the timestamp to be old
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        record.timestamp = old_time

        # Run cleanup
        await tracker.cleanup_old_records()

        # Record should be gone
        cleaned_record = await tracker.get_record("msg_old")
        assert cleaned_record is None

    @pytest.mark.asyncio
    async def test_start_and_stop_cleanup_task(self, tracker: DeliveryTracker) -> None:
        """Test starting and stopping the cleanup task."""
        # Start cleanup task
        await tracker.start_cleanup_task()
        assert tracker._cleanup_task is not None
        assert not tracker._cleanup_task.done()

        # Stop cleanup task
        await tracker.stop_cleanup_task()
        assert tracker._cleanup_task is None

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, tracker: DeliveryTracker) -> None:
        """Test concurrent operations on tracker."""
        # Create tasks that operate concurrently
        tasks = []
        for i in range(10):
            task = tracker.track_queued(f"msg_{i}", "email", f"user{i}@test.com")
            tasks.append(task)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

        # Check all records were created
        for i in range(10):
            record = await tracker.get_record(f"msg_{i}")
            assert record is not None

    @pytest.mark.asyncio
    async def test_edge_case_empty_metadata(self, tracker: DeliveryTracker) -> None:
        """Test handling empty metadata."""
        record = await tracker.track_queued(
            message_id="msg_empty_meta",
            channel="email",
            recipient="user@test.com",
            metadata={},
        )

        assert record.metadata == {}

    @pytest.mark.asyncio
    async def test_edge_case_unicode_content(self, tracker: DeliveryTracker) -> None:
        """Test handling Unicode content."""
        record = await tracker.track_queued(
            message_id="msg_unicode",
            channel="email",
            recipient="ユーザー@テスト.com",
            metadata={"subject": "メッセージ テスト 🚀"},
        )

        assert record.recipient == "ユーザー@テスト.com"
        assert record.metadata["subject"] == "メッセージ テスト 🚀"
