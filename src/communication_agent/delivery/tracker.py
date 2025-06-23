"""
Delivery tracking and analytics for the Communication Agent.

Tracks message delivery status, read receipts, responses,
and provides analytics on delivery performance.
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from src.utils.logging import get_logger

logger = get_logger(__name__)


class DeliveryStatus(str, Enum):
    """Message delivery status."""

    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"
    EXPIRED = "expired"


@dataclass
class DeliveryRecord:
    """Record of a message delivery attempt."""

    message_id: str
    channel: str
    recipient: str
    status: DeliveryStatus
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    attempts: int = 1
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Tracking timestamps
    queued_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    # Response tracking
    response_received: bool = False
    response_time: Optional[datetime] = None
    response_content: Optional[str] = None

    def update_status(
        self, new_status: DeliveryStatus, error: Optional[str] = None
    ) -> None:
        """Update delivery status with timestamp."""
        self.status = new_status
        self.timestamp = datetime.now(timezone.utc)

        if error:
            self.error = error

        # Update specific timestamps
        if new_status == DeliveryStatus.SENT:
            self.sent_at = self.timestamp
        elif new_status == DeliveryStatus.DELIVERED:
            self.delivered_at = self.timestamp
        elif new_status == DeliveryStatus.READ:
            self.read_at = self.timestamp
        elif new_status == DeliveryStatus.FAILED:
            self.failed_at = self.timestamp

    def get_delivery_time(self) -> Optional[float]:
        """Get time from queued to delivered in seconds."""
        if self.queued_at and self.delivered_at:
            return (self.delivered_at - self.queued_at).total_seconds()
        return None

    def get_read_time(self) -> Optional[float]:
        """Get time from delivered to read in seconds."""
        if self.delivered_at and self.read_at:
            return (self.read_at - self.delivered_at).total_seconds()
        return None


class DeliveryTracker:
    """
    Tracks message delivery status and provides analytics.

    Features:
    - Real-time delivery status tracking
    - Read receipt handling
    - Response tracking
    - Delivery analytics and reporting
    """

    def __init__(
        self,
        retention_hours: int = 24,
        cleanup_interval_minutes: int = 60,
    ):
        """
        Initialize delivery tracker.

        Args:
            retention_hours: Hours to retain delivery records
            cleanup_interval_minutes: Cleanup interval in minutes
        """
        self.retention_hours = retention_hours
        self.cleanup_interval = timedelta(minutes=cleanup_interval_minutes)

        # Storage
        self._records: Dict[str, DeliveryRecord] = {}
        self._records_lock = asyncio.Lock()

        # Indexes for fast lookup
        self._by_channel: Dict[str, Set[str]] = defaultdict(set)
        self._by_recipient: Dict[str, Set[str]] = defaultdict(set)
        self._by_status: Dict[DeliveryStatus, Set[str]] = defaultdict(set)

        # Analytics
        self._analytics: Dict[str, Any] = {
            "total_messages": 0,
            "delivery_rates": defaultdict(
                lambda: {"sent": 0, "delivered": 0, "failed": 0}
            ),
            "avg_delivery_time": defaultdict(list),
            "read_rates": defaultdict(lambda: {"delivered": 0, "read": 0}),
        }

        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task[None]] = None
        self._last_cleanup = datetime.now(timezone.utc)

    async def track_queued(
        self,
        message_id: str,
        channel: str,
        recipient: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeliveryRecord:
        """Track a newly queued message."""
        record = DeliveryRecord(
            message_id=message_id,
            channel=channel,
            recipient=recipient,
            status=DeliveryStatus.QUEUED,
            queued_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )

        await self._add_record(record)

        logger.debug(
            "Tracking queued message",
            extra={
                "message_id": message_id,
                "channel": channel,
                "recipient": recipient,
            },
        )

        return record

    async def track_sent(
        self,
        message_id: str,
        provider_message_id: Optional[str] = None,
    ) -> None:
        """Track that a message was sent."""
        async with self._records_lock:
            if message_id not in self._records:
                logger.warning("Message %s not found for sent tracking", message_id)
                return

            record = self._records[message_id]
            old_status = record.status

            record.update_status(DeliveryStatus.SENT)
            if provider_message_id:
                record.metadata["provider_message_id"] = provider_message_id

            # Update indexes
            self._by_status[old_status].discard(message_id)
            self._by_status[DeliveryStatus.SENT].add(message_id)

            # Update analytics
            delivery_rates = self._analytics["delivery_rates"]
            if hasattr(delivery_rates, "__getitem__"):
                channel_rates = delivery_rates[record.channel]
                if isinstance(channel_rates, dict):
                    channel_rates["sent"] += 1

    async def track_delivered(
        self,
        message_id: str,
        delivered_at: Optional[datetime] = None,
    ) -> None:
        """Track that a message was delivered."""
        async with self._records_lock:
            if message_id not in self._records:
                logger.warning("Message %s not found for delivery tracking", message_id)
                return

            record = self._records[message_id]
            old_status = record.status

            record.update_status(DeliveryStatus.DELIVERED)
            if delivered_at:
                record.delivered_at = delivered_at

            # Update indexes
            self._by_status[old_status].discard(message_id)
            self._by_status[DeliveryStatus.DELIVERED].add(message_id)

            # Update analytics
            delivery_rates = self._analytics["delivery_rates"]
            if hasattr(delivery_rates, "__getitem__"):
                channel_rates = delivery_rates[record.channel]
                if isinstance(channel_rates, dict):
                    channel_rates["delivered"] += 1

            # Track delivery time
            delivery_time = record.get_delivery_time()
            if delivery_time:
                avg_delivery_time = self._analytics["avg_delivery_time"]
                if hasattr(avg_delivery_time, "__getitem__"):
                    channel_times = avg_delivery_time[record.channel]
                    if hasattr(channel_times, "append"):
                        channel_times.append(delivery_time)

            read_rates = self._analytics["read_rates"]
            if hasattr(read_rates, "__getitem__"):
                channel_read_rates = read_rates[record.channel]
                if isinstance(channel_read_rates, dict):
                    channel_read_rates["delivered"] += 1

    async def track_read(
        self,
        message_id: str,
        read_at: Optional[datetime] = None,
    ) -> None:
        """Track that a message was read."""
        async with self._records_lock:
            if message_id not in self._records:
                logger.warning("Message %s not found for read tracking", message_id)
                return

            record = self._records[message_id]
            old_status = record.status

            record.update_status(DeliveryStatus.READ)
            if read_at:
                record.read_at = read_at

            # Update indexes
            self._by_status[old_status].discard(message_id)
            self._by_status[DeliveryStatus.READ].add(message_id)

            # Update analytics
            read_rates = self._analytics["read_rates"]
            if hasattr(read_rates, "__getitem__"):
                channel_read_rates = read_rates[record.channel]
                if isinstance(channel_read_rates, dict):
                    channel_read_rates["read"] += 1

    async def track_failed(
        self,
        message_id: str,
        error: str,
        attempts: Optional[int] = None,
    ) -> None:
        """Track that a message failed to deliver."""
        async with self._records_lock:
            if message_id not in self._records:
                logger.warning("Message %s not found for failure tracking", message_id)
                return

            record = self._records[message_id]
            old_status = record.status

            record.update_status(DeliveryStatus.FAILED, error=error)
            if attempts:
                record.attempts = attempts

            # Update indexes
            self._by_status[old_status].discard(message_id)
            self._by_status[DeliveryStatus.FAILED].add(message_id)

            # Update analytics
            delivery_rates = self._analytics["delivery_rates"]
            if hasattr(delivery_rates, "__getitem__"):
                channel_rates = delivery_rates[record.channel]
                if isinstance(channel_rates, dict):
                    channel_rates["failed"] += 1

    async def track_response(
        self,
        message_id: str,
        response_content: str,
        response_time: Optional[datetime] = None,
    ) -> None:
        """Track a response to a message."""
        async with self._records_lock:
            if message_id not in self._records:
                logger.warning("Message %s not found for response tracking", message_id)
                return

            record = self._records[message_id]
            record.response_received = True
            record.response_content = response_content
            record.response_time = response_time or datetime.now(timezone.utc)

    async def get_record(self, message_id: str) -> Optional[DeliveryRecord]:
        """Get a delivery record by message ID."""
        async with self._records_lock:
            return self._records.get(message_id)

    async def get_records_by_status(
        self,
        status: DeliveryStatus,
        limit: Optional[int] = None,
    ) -> List[DeliveryRecord]:
        """Get delivery records by status."""
        async with self._records_lock:
            message_ids = self._by_status[status]

            records = [
                self._records[mid] for mid in message_ids if mid in self._records
            ]

            # Sort by timestamp (newest first)
            records.sort(key=lambda r: r.timestamp, reverse=True)

            if limit:
                records = records[:limit]

            return records

    async def get_records_by_channel(
        self,
        channel: str,
        limit: Optional[int] = None,
    ) -> List[DeliveryRecord]:
        """Get delivery records by channel."""
        async with self._records_lock:
            message_ids = self._by_channel[channel]

            records = [
                self._records[mid] for mid in message_ids if mid in self._records
            ]

            # Sort by timestamp (newest first)
            records.sort(key=lambda r: r.timestamp, reverse=True)

            if limit:
                records = records[:limit]

            return records

    async def get_analytics(self, channel: Optional[str] = None) -> Dict[str, Any]:
        """
        Get delivery analytics.

        Args:
            channel: Optional channel to filter by

        Returns:
            Analytics data
        """
        async with self._records_lock:
            if channel:
                # Channel-specific analytics
                delivery_rates = self._analytics["delivery_rates"]
                delivery_rate = (
                    delivery_rates[channel]
                    if hasattr(delivery_rates, "__getitem__")
                    else {"sent": 0, "delivered": 0, "failed": 0}
                )
                total_sent = delivery_rate["sent"] if isinstance(delivery_rate, dict) else 0

                # Calculate average delivery time
                avg_delivery_time_data = self._analytics["avg_delivery_time"]
                delivery_times = (
                    avg_delivery_time_data[channel]
                    if hasattr(avg_delivery_time_data, "__getitem__")
                    else []
                )
                avg_delivery_time = (
                    sum(delivery_times) / len(delivery_times) if delivery_times else 0
                )

                # Calculate read rate
                read_rates = self._analytics["read_rates"]
                read_rate_data = (
                    read_rates[channel]
                    if hasattr(read_rates, "__getitem__")
                    else {"delivered": 0, "read": 0}
                )
                read_rate = (
                    read_rate_data["read"] / read_rate_data["delivered"]
                    if read_rate_data["delivered"] > 0
                    else 0
                )

                return {
                    "channel": channel,
                    "total_sent": total_sent,
                    "delivery_rate": (
                        delivery_rate["delivered"] / total_sent
                        if isinstance(delivery_rate, dict) and total_sent > 0
                        else 0
                    ),
                    "failure_rate": (
                        delivery_rate["failed"] / total_sent
                        if isinstance(delivery_rate, dict) and total_sent > 0
                        else 0
                    ),
                    "avg_delivery_time": avg_delivery_time,
                    "read_rate": read_rate,
                    "current_queued": len(self._by_status[DeliveryStatus.QUEUED]),
                    "current_failed": len(self._by_status[DeliveryStatus.FAILED]),
                }
            else:
                # Overall analytics
                total_messages = len(self._records)
                status_counts = {
                    status: len(message_ids)
                    for status, message_ids in self._by_status.items()
                }

                # Calculate overall rates
                delivery_rates = self._analytics["delivery_rates"]
                total_sent = 0
                total_delivered = 0
                total_failed = 0

                if hasattr(delivery_rates, "values"):
                    total_sent = sum(
                        rates["sent"] if isinstance(rates, dict) else 0
                        for rates in delivery_rates.values()
                    )
                    total_delivered = sum(
                        rates["delivered"] if isinstance(rates, dict) else 0
                        for rates in delivery_rates.values()
                    )
                    total_failed = sum(
                        rates["failed"] if isinstance(rates, dict) else 0
                        for rates in delivery_rates.values()
                    )

                return {
                    "total_messages": total_messages,
                    "status_breakdown": status_counts,
                    "overall_delivery_rate": (
                        total_delivered / total_sent if total_sent > 0 else 0
                    ),
                    "overall_failure_rate": (
                        total_failed / total_sent if total_sent > 0 else 0
                    ),
                    "channels": list(self._by_channel.keys()),
                }

    async def _add_record(self, record: DeliveryRecord) -> None:
        """Add a delivery record to tracking."""
        async with self._records_lock:
            self._records[record.message_id] = record

            # Update indexes
            self._by_channel[record.channel].add(record.message_id)
            self._by_recipient[record.recipient].add(record.message_id)
            self._by_status[record.status].add(record.message_id)

            # Update analytics
            if isinstance(self._analytics["total_messages"], int):
                self._analytics["total_messages"] += 1
            else:
                self._analytics["total_messages"] = 1

    async def cleanup_old_records(self) -> int:
        """Remove old delivery records and return count removed."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.retention_hours)

        async with self._records_lock:
            old_message_ids = [
                mid
                for mid, record in self._records.items()
                if record.timestamp < cutoff_time
            ]

            for message_id in old_message_ids:
                record = self._records[message_id]

                # Remove from indexes
                self._by_channel[record.channel].discard(message_id)
                self._by_recipient[record.recipient].discard(message_id)
                self._by_status[record.status].discard(message_id)

                # Remove record
                del self._records[message_id]

            if old_message_ids:
                logger.info(
                    "Cleaned up %d old delivery records", len(old_message_ids),
                    extra={"retention_hours": self.retention_hours},
                )

            return len(old_message_ids)

    async def start_cleanup_task(self) -> None:
        """Start the periodic cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            return

        async def cleanup_loop() -> None:
            while True:
                try:
                    await asyncio.sleep(self.cleanup_interval.total_seconds())
                    await self.cleanup_old_records()
                except asyncio.CancelledError:
                    break
                except (ValueError, IOError, OSError) as e:
                    logger.error("Error in cleanup task: %s", e, exc_info=True)

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    async def stop_cleanup_task(self) -> None:
        """Stop the cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
