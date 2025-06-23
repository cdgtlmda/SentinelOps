"""
Delivery manager for the Communication Agent.

Coordinates message delivery with priority queuing, rate limiting,
batch processing, and delivery tracking.
"""

import asyncio
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional

from src.communication_agent.delivery.queue import PriorityDeliveryQueue, QueuedMessage
from src.communication_agent.delivery.rate_limiter import RateLimitConfig, RateLimiter
from src.communication_agent.delivery.tracker import DeliveryTracker
from src.communication_agent.interfaces import (
    NotificationService,
    NotificationRequest,
    NotificationResult,
)
from src.communication_agent.types import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DeliveryManager:
    """
    Manages message delivery with advanced features.

    Features:
    - Priority-based queuing
    - Rate limiting per channel
    - Batch processing for efficiency
    - Failed delivery handling with retries
    - Comprehensive delivery tracking
    """

    def __init__(
        self,
        notification_services: Dict[NotificationChannel, NotificationService],
        queue_config: Optional[Dict[str, Any]] = None,
        rate_limit_config: Optional[Dict[str, RateLimitConfig]] = None,
    ):
        """
        Initialize delivery manager.

        Args:
            notification_services: Available notification services
            queue_config: Queue configuration
            rate_limit_config: Rate limiting configuration
        """
        self.notification_services = notification_services

        # Initialize components
        queue_config = queue_config or {}
        self.queue = PriorityDeliveryQueue(
            max_size=queue_config.get("max_size", 10000),
            batch_size=queue_config.get("batch_size", 100),
            batch_timeout=queue_config.get("batch_timeout", 5.0),
        )

        self.rate_limiter = RateLimiter(
            channel_configs=rate_limit_config,
        )

        self.tracker = DeliveryTracker()

        # Processing tasks
        self._processor_tasks: Dict[str, asyncio.Task[None]] = {}
        self._running = False

        # Callbacks
        self._delivery_callbacks: List[
            Callable[[QueuedMessage, Dict[str, Any]], Awaitable[None]]
        ] = []

        logger.info(
            "Delivery manager initialized",
            extra={
                "channels": list(notification_services.keys()),
                "queue_size": queue_config.get("max_size", 10000),
            },
        )

    async def send_message(
        self,
        message_id: str,
        channel: NotificationChannel,
        recipients: List[str],
        subject: str,
        content: str,
        priority: NotificationPriority,
        scheduled_for: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a message through the delivery system.

        Args:
            message_id: Unique message identifier
            channel: Delivery channel
            recipients: List of recipients
            subject: Message subject
            content: Message content
            priority: Message priority
            scheduled_for: Optional scheduled delivery time
            metadata: Optional metadata

        Returns:
            Delivery status information
        """
        # Validate channel
        if channel not in self.notification_services:
            raise ValueError(f"No service configured for channel: {channel}")

        # Prepare message content
        message_content = {
            "subject": subject,
            "body": content,
            "metadata": metadata or {},
        }

        # Queue the message
        queued = await self.queue.enqueue(
            message_id=message_id,
            channel=channel.value,
            recipients=recipients,
            content=message_content,
            priority=priority,
            scheduled_for=scheduled_for,
            metadata=metadata,
        )

        if not queued:
            logger.error(
                "Failed to queue message - queue full",
                extra={"message_id": message_id},
            )
            return {
                "status": "failed",
                "error": "Queue full",
                "message_id": message_id,
            }

        # Track the queued message
        for recipient in recipients:
            await self.tracker.track_queued(
                message_id=f"{message_id}:{recipient}",
                channel=channel.value,
                recipient=recipient,
                metadata=metadata,
            )

        return {
            "status": "queued",
            "message_id": message_id,
            "channel": channel.value,
            "recipient_count": len(recipients),
            "priority": priority.value,
            "scheduled_for": scheduled_for.isoformat() if scheduled_for else None,
        }

    async def start(self) -> None:
        """Start the delivery manager."""
        if self._running:
            return

        self._running = True

        # Start tracker cleanup
        await self.tracker.start_cleanup_task()

        # Start processor for each channel
        for channel in self.notification_services:
            task = asyncio.create_task(self._process_channel(channel.value))
            self._processor_tasks[channel.value] = task

        logger.info(
            "Delivery manager started",
            extra={"channels": list(self._processor_tasks.keys())},
        )

    async def stop(self) -> None:
        """Stop the delivery manager."""
        if not self._running:
            return

        self._running = False

        # Stop tracker cleanup
        await self.tracker.stop_cleanup_task()

        # Cancel processor tasks
        for task in self._processor_tasks.values():
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(
            *self._processor_tasks.values(),
            return_exceptions=True,
        )

        self._processor_tasks.clear()

        logger.info("Delivery manager stopped")

    async def _process_channel(self, channel: str) -> None:
        """Process messages for a specific channel."""
        logger.info("Starting processor for channel: %s", channel)

        while self._running:
            try:
                # Wait for messages
                has_messages = await self.queue.wait_for_messages(timeout=1.0)
                if not has_messages:
                    continue

                # Get a batch of messages
                batch = await self.queue.dequeue_batch()
                if not batch:
                    continue

                # Filter messages for this channel
                channel_messages = [msg for msg in batch if msg.channel == channel]

                # Return other messages to queue
                for msg in batch:
                    if msg.channel != channel:
                        await self.queue.enqueue(
                            message_id=msg.message_id,
                            channel=msg.channel,
                            recipients=msg.recipients,
                            content=msg.content,
                            priority=msg.priority,
                            scheduled_for=msg.scheduled_for,
                            metadata=msg.metadata,
                        )

                if channel_messages:
                    # Process in batches by recipient similarity
                    await self._process_batch(channel, channel_messages)

            except asyncio.CancelledError:
                break
            except (ValueError, RuntimeError, OSError) as e:
                logger.error(
                    "Error processing channel %s: %s", channel, e,
                    exc_info=True,
                )
                await asyncio.sleep(1)

    async def _process_batch(
        self,
        channel: str,
        messages: List[QueuedMessage],
    ) -> None:
        """Process a batch of messages."""
        service = self.notification_services[NotificationChannel(channel)]

        # Group messages that can be batched together
        batches = self._group_messages_for_batching(messages)

        for batch_messages in batches:
            # Apply rate limiting
            total_recipients = sum(len(msg.recipients) for msg in batch_messages)

            await self.rate_limiter.wait_if_limited(
                channel=channel,
                message_count=total_recipients,
            )

            # Process each message in the batch
            for message in batch_messages:
                await self._deliver_message(service, message)

    async def _deliver_message(
        self,
        service: NotificationService,
        message: QueuedMessage,
    ) -> None:
        """Deliver a single message."""
        try:
            # Send to each recipient individually
            results = []
            for recipient in message.recipients:
                tracking_id = f"{message.message_id}:{recipient}"
                await self.tracker.track_sent(tracking_id)

                # Create request for this recipient
                request = NotificationRequest(
                    channel=NotificationChannel[message.channel.upper()],
                    recipient=recipient,
                    subject=message.content.get("subject", ""),
                    body=message.content.get("body", ""),
                    priority=message.priority,
                    metadata=message.content.get("metadata"),
                )

                # Send the message
                result = await service.send(request)
                results.append(result)

                # Update tracking based on result
                if result.success:
                    await self.tracker.track_delivered(tracking_id)
                else:
                    await self.tracker.track_failed(tracking_id, result.error or "Unknown error")

            # Mark as delivered if at least one succeeded
            if any(r.success for r in results):
                self.queue.mark_delivered(message)

            # Execute callbacks with combined result
            combined_result = NotificationResult(
                success=any(r.success for r in results),
                status=(
                    NotificationStatus.SENT
                    if any(r.success for r in results)
                    else NotificationStatus.FAILED
                ),
                metadata={
                    "individual_results": [
                        {"recipient": r, "result": res}
                        for r, res in zip(message.recipients, results)
                    ]
                }
            )
            await self._execute_callbacks(message, {"result": combined_result})

            logger.info(
                "Message delivered successfully",
                extra={
                    "message_id": message.message_id,
                    "channel": message.channel,
                    "recipients": len(message.recipients),
                },
            )

        except (ValueError, RuntimeError, OSError) as e:
            logger.error(
                "Failed to deliver message: %s", e,
                extra={
                    "message_id": message.message_id,
                    "channel": message.channel,
                },
                exc_info=True,
            )

            # Track failure
            for recipient in message.recipients:
                tracking_id = f"{message.message_id}:{recipient}"
                await self.tracker.track_failed(
                    tracking_id,
                    error=str(e),
                    attempts=message.retry_count + 1,
                )

            # Requeue for retry if applicable
            await self.queue.requeue_failed(message, error=str(e))

    def _group_messages_for_batching(
        self,
        messages: List[QueuedMessage],
    ) -> List[List[QueuedMessage]]:
        """
        Group messages that can be efficiently batched together.

        Currently groups by:
        - Same content (for broadcast messages)
        - Similar priority
        """
        # For now, simple implementation - no batching
        # Each message is its own batch
        return [[msg] for msg in messages]

    async def _execute_callbacks(
        self,
        message: QueuedMessage,
        result: Dict[str, Any],
    ) -> None:
        """Execute delivery callbacks."""
        for callback in self._delivery_callbacks:
            try:
                await callback(message, result)
            except (ValueError, RuntimeError, AttributeError) as e:
                logger.error(
                    "Error in delivery callback: %s", e,
                    exc_info=True,
                )

    def add_delivery_callback(
        self,
        callback: Callable[[QueuedMessage, Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Add a callback to be executed after message delivery."""
        self._delivery_callbacks.append(callback)

    def remove_delivery_callback(
        self,
        callback: Callable[[QueuedMessage, Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Remove a delivery callback."""
        if callback in self._delivery_callbacks:
            self._delivery_callbacks.remove(callback)

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return self.queue.get_stats()

    async def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        return self.rate_limiter.get_stats()

    async def get_delivery_analytics(
        self,
        channel: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get delivery analytics."""
        return await self.tracker.get_analytics(channel)

    async def get_failed_messages(
        self,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get failed messages for inspection."""
        failed_messages = await self.queue.get_failed_messages(limit)

        return [
            {
                "message_id": msg.message_id,
                "channel": msg.channel,
                "recipients": msg.recipients,
                "priority": msg.priority.value,
                "retry_count": msg.retry_count,
                "queued_at": msg.queued_at.isoformat(),
                "error": msg.metadata.get("last_error"),
            }
            for msg in failed_messages
        ]

    async def retry_failed_message(self, message_id: str) -> bool:
        """Manually retry a failed message."""
        failed_messages = await self.queue.get_failed_messages()

        for msg in failed_messages:
            if msg.message_id == message_id:
                # Reset retry count and requeue
                msg.retry_count = 0
                return await self.queue.enqueue(
                    message_id=msg.message_id,
                    channel=msg.channel,
                    recipients=msg.recipients,
                    content=msg.content,
                    priority=msg.priority,
                    metadata=msg.metadata,
                )

        return False
