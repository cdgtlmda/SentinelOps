"""
Priority-based delivery queue for the Communication Agent.

Implements priority queuing with support for batch processing
and failed delivery handling.
"""

import asyncio
import heapq
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.communication_agent.types import NotificationPriority
from src.utils.logging import get_logger
from src.utils.datetime_utils import utcnow

logger = get_logger(__name__)


@dataclass(order=True)
class QueuedMessage:
    """A message in the delivery queue with priority ordering."""

    priority_value: float = field(compare=True)
    queued_at: datetime = field(compare=True)
    message_id: str = field(compare=False)
    channel: str = field(compare=False)
    recipients: List[str] = field(compare=False)
    content: Dict[str, Any] = field(compare=False)
    retry_count: int = field(default=0, compare=False)
    scheduled_for: Optional[datetime] = field(default=None, compare=False)
    batch_id: Optional[str] = field(default=None, compare=False)
    metadata: Dict[str, Any] = field(default_factory=dict, compare=False)

    @property
    def priority(self) -> NotificationPriority:
        """Get the notification priority."""
        # Map priority value back to enum
        if self.priority_value <= 1:
            return NotificationPriority.CRITICAL
        elif self.priority_value <= 2:
            return NotificationPriority.HIGH
        elif self.priority_value <= 3:
            return NotificationPriority.MEDIUM
        else:
            return NotificationPriority.LOW

    def is_ready(self) -> bool:
        """Check if message is ready for delivery."""
        if self.scheduled_for:
            return utcnow() >= self.scheduled_for
        return True


class PriorityDeliveryQueue:
    """
    Priority-based delivery queue with batch processing support.

    Messages are delivered based on priority, with support for
    scheduled delivery, batching, and retry handling.
    """

    def __init__(
        self,
        max_size: int = 10000,
        batch_size: int = 100,
        batch_timeout: float = 5.0,
    ):
        """
        Initialize the delivery queue.

        Args:
            max_size: Maximum queue size
            batch_size: Maximum messages per batch
            batch_timeout: Timeout for batch collection in seconds
        """
        self.max_size = max_size
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout

        # Priority queue (heap)
        self._queue: List[QueuedMessage] = []
        self._queue_lock = asyncio.Lock()

        # Failed delivery handling
        self._failed_messages: List[QueuedMessage] = []
        self._retry_delays = [60, 300, 900, 3600]  # 1m, 5m, 15m, 1h

        # Batch processing
        self._batch_event = asyncio.Event()
        self._current_batch: List[QueuedMessage] = []

        # Statistics
        self._stats = {
            "total_queued": 0,
            "total_delivered": 0,
            "total_failed": 0,
            "total_retried": 0,
            "current_size": 0,
        }

    def _priority_to_value(self, priority: NotificationPriority) -> int:
        """Convert priority enum to numeric value for sorting."""
        priority_map = {
            NotificationPriority.CRITICAL: 1,
            NotificationPriority.HIGH: 2,
            NotificationPriority.MEDIUM: 3,
            NotificationPriority.LOW: 4,
        }
        return priority_map.get(priority, 3)

    async def enqueue(
        self,
        message_id: str,
        channel: str,
        recipients: List[str],
        content: Dict[str, Any],
        priority: NotificationPriority,
        scheduled_for: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a message to the queue.

        Args:
            message_id: Unique message identifier
            channel: Delivery channel
            recipients: List of recipients
            content: Message content
            priority: Message priority
            scheduled_for: Optional scheduled delivery time
            metadata: Optional metadata

        Returns:
            True if message was queued, False if queue is full
        """
        async with self._queue_lock:
            if len(self._queue) >= self.max_size:
                logger.warning(
                    "Delivery queue is full",
                    extra={
                        "queue_size": len(self._queue),
                        "max_size": self.max_size,
                    },
                )
                return False

            message = QueuedMessage(
                priority_value=self._priority_to_value(priority),
                queued_at=utcnow(),
                message_id=message_id,
                channel=channel,
                recipients=recipients,
                content=content,
                scheduled_for=scheduled_for,
                metadata=metadata or {},
            )

            heapq.heappush(self._queue, message)
            self._stats["total_queued"] += 1
            self._stats["current_size"] = len(self._queue)

            # Signal batch processor
            self._batch_event.set()

            logger.debug(
                "Message queued for delivery",
                extra={
                    "message_id": message_id,
                    "priority": priority.value,
                    "channel": channel,
                    "recipient_count": len(recipients),
                    "queue_size": len(self._queue),
                },
            )

            return True

    async def dequeue_batch(
        self,
        max_messages: Optional[int] = None,
    ) -> List[QueuedMessage]:
        """
        Dequeue a batch of messages.

        Args:
            max_messages: Maximum messages to dequeue (default: batch_size)

        Returns:
            List of messages ready for delivery
        """
        max_messages = max_messages or self.batch_size
        batch: List[QueuedMessage] = []

        async with self._queue_lock:
            # First, check for ready scheduled messages
            ready_scheduled = []
            remaining = []

            for msg in self._queue:
                if msg.is_ready():
                    ready_scheduled.append(msg)
                else:
                    remaining.append(msg)

            # Rebuild queue with remaining messages
            self._queue = remaining
            heapq.heapify(self._queue)

            # Add ready scheduled messages back
            for msg in ready_scheduled:
                heapq.heappush(self._queue, msg)

            # Dequeue up to max_messages
            while len(batch) < max_messages and self._queue:
                # Peek at the top message
                if self._queue[0].is_ready():
                    batch.append(heapq.heappop(self._queue))
                else:
                    # Top message is scheduled for future
                    break

            self._stats["current_size"] = len(self._queue)

            # Clear batch event if queue is empty
            if not self._queue:
                self._batch_event.clear()

        if batch:
            logger.info(
                "Dequeued batch of %d messages", len(batch),
                extra={
                    "batch_size": len(batch),
                    "remaining_queue_size": len(self._queue),
                },
            )

        return batch

    async def wait_for_messages(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for messages to be available.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if messages are available, False if timeout
        """
        try:
            await asyncio.wait_for(
                self._batch_event.wait(),
                timeout=timeout or self.batch_timeout,
            )
            return True
        except asyncio.TimeoutError:
            return False

    async def requeue_failed(
        self,
        message: QueuedMessage,
        error: Optional[str] = None,
    ) -> bool:
        """
        Requeue a failed message with retry logic.

        Args:
            message: Failed message
            error: Error description

        Returns:
            True if message was requeued, False if max retries exceeded
        """
        message.retry_count += 1

        # Check max retries
        if message.retry_count > len(self._retry_delays):
            logger.error(
                "Message exceeded max retries",
                extra={
                    "message_id": message.message_id,
                    "retry_count": message.retry_count,
                    "error": error,
                },
            )

            async with self._queue_lock:
                self._failed_messages.append(message)
                self._stats["total_failed"] += 1

            return False

        # Calculate retry delay
        delay_seconds = self._retry_delays[message.retry_count - 1]
        message.scheduled_for = utcnow() + timedelta(seconds=delay_seconds)

        # Update priority for retries (slightly lower)
        if message.priority_value < 4:
            message.priority_value += 0.5

        # Requeue
        async with self._queue_lock:
            heapq.heappush(self._queue, message)
            self._stats["total_retried"] += 1
            self._stats["current_size"] = len(self._queue)
            self._batch_event.set()

        logger.info(
            "Message requeued for retry",
            extra={
                "message_id": message.message_id,
                "retry_count": message.retry_count,
                "retry_delay": delay_seconds,
                "scheduled_for": message.scheduled_for.isoformat(),
            },
        )

        return True

    def mark_delivered(self, message: QueuedMessage) -> None:
        """Mark a message as successfully delivered."""
        self._stats["total_delivered"] += 1

        logger.debug(
            "Message delivered successfully",
            extra={
                "message_id": message.message_id,
                "channel": message.channel,
                "retry_count": message.retry_count,
            },
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            **self._stats,
            "failed_count": len(self._failed_messages),
            "oldest_message_age": self._get_oldest_message_age(),
        }

    def _get_oldest_message_age(self) -> Optional[float]:
        """Get age of oldest message in queue (seconds)."""
        if not self._queue:
            return None

        oldest = min(self._queue, key=lambda m: m.queued_at)
        age = (utcnow() - oldest.queued_at).total_seconds()
        return age

    async def get_failed_messages(
        self,
        limit: Optional[int] = None,
    ) -> List[QueuedMessage]:
        """Get failed messages for inspection."""
        async with self._queue_lock:
            if limit:
                return self._failed_messages[-limit:]
            return self._failed_messages.copy()

    async def clear_failed_messages(self) -> int:
        """Clear failed messages and return count."""
        async with self._queue_lock:
            count = len(self._failed_messages)
            self._failed_messages.clear()
            return count

    def group_by_channel(
        self,
        messages: List[QueuedMessage],
    ) -> Dict[str, List[QueuedMessage]]:
        """Group messages by channel for batch processing."""
        grouped: Dict[str, List[QueuedMessage]] = {}

        for message in messages:
            if message.channel not in grouped:
                grouped[message.channel] = []
            grouped[message.channel].append(message)

        return grouped

    def group_by_batch_id(
        self,
        messages: List[QueuedMessage],
    ) -> Dict[Optional[str], List[QueuedMessage]]:
        """Group messages by batch ID."""
        grouped: Dict[Optional[str], List[QueuedMessage]] = {}

        for message in messages:
            batch_id = message.batch_id
            if batch_id not in grouped:
                grouped[batch_id] = []
            grouped[batch_id].append(message)

        return grouped
