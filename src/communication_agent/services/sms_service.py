"""
SMS notification service for the Communication Agent.

Handles SMS notifications via Twilio integration with phone number validation,
message length optimization, and delivery status tracking.
"""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.communication_agent.interfaces import (
    NotificationService,
    NotificationRequest,
    NotificationResult,
)
from src.communication_agent.services.twilio import TwilioClient, TwilioClientError
from src.communication_agent.types import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TwilioConfig:
    """Twilio configuration."""

    account_sid: str
    auth_token: str
    from_number: str
    status_callback_url: Optional[str] = None
    messaging_service_sid: Optional[str] = None
    max_price_per_message: str = "0.10"  # Maximum price per message in USD


@dataclass
class SMSMessage:
    """SMS message data structure."""

    to_number: str
    body: str
    priority: NotificationPriority
    metadata: Optional[Dict[str, Any]] = None
    message_sid: Optional[str] = None
    status: str = "queued"
    created_at: datetime = datetime.now(timezone.utc)
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None


class SMSQueue:
    """SMS queue for managing message delivery."""

    def __init__(self, max_size: int = 1000):
        """Initialize SMS queue."""
        self.queue: asyncio.Queue[SMSMessage] = asyncio.Queue(maxsize=max_size)
        self.processing = False
        self._processor_task: Optional[asyncio.Task[Any]] = None
        self._delivery_status: Dict[str, SMSMessage] = {}

    async def enqueue(self, message: SMSMessage) -> None:
        """Add an SMS message to the queue."""
        await self.queue.put(message)
        logger.debug(
            "SMS queued for %s",
            message.to_number,
            extra={
                "priority": message.priority.value,
                "queue_size": self.queue.qsize(),
            },
        )

    async def get_next(self) -> Optional[SMSMessage]:
        """Get the next SMS from the queue."""
        try:
            return await self.queue.get()
        except asyncio.QueueEmpty:
            return None

    def task_done(self) -> None:
        """Mark the current task as done."""
        self.queue.task_done()

    def track_delivery(self, message_sid: str, message: SMSMessage) -> None:
        """Track delivery status of a message."""
        self._delivery_status[message_sid] = message

    def update_delivery_status(
        self,
        message_sid: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Update the delivery status of a message."""
        if message_sid in self._delivery_status:
            message = self._delivery_status[message_sid]
            message.status = status
            if status == "delivered":
                message.delivered_at = datetime.now(timezone.utc)
            if error_message:
                message.error_message = error_message

            logger.info(
                "SMS delivery status updated",
                extra={
                    "message_sid": message_sid,
                    "status": status,
                    "to_number": message.to_number,
                },
            )


class SMSNotificationService(NotificationService):
    """
    SMS notification service implementation using Twilio.

    Supports phone number validation, message length optimization,
    and delivery status tracking.
    """

    # SMS length limits
    SINGLE_SMS_LIMIT = 160
    CONCATENATED_SMS_LIMIT = 153
    MAX_CONCATENATED_PARTS = 5

    def __init__(self, twilio_config: TwilioConfig):
        """Initialize SMS notification service."""
        self.config = twilio_config
        self.sms_queue = SMSQueue()
        self._twilio_client: Optional[TwilioClient] = None
        self._init_twilio_client()

        logger.info(
            "SMS notification service initialized",
            extra={
                "from_number": twilio_config.from_number,
                "has_messaging_service": bool(twilio_config.messaging_service_sid),
            },
        )

    def _init_twilio_client(self) -> None:
        """Initialize Twilio client."""
        try:
            self._twilio_client = TwilioClient(
                account_sid=self.config.account_sid,
                auth_token=self.config.auth_token,
                from_number=self.config.from_number,
                messaging_service_sid=self.config.messaging_service_sid,
            )
            logger.info("Twilio client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Twilio client: %s", e, exc_info=True)
            raise

    def get_channel_type(self) -> NotificationChannel:
        """Get the channel type this service implements."""
        return NotificationChannel.SMS

    async def validate_recipient(self, recipient: str) -> bool:
        """
        Validate a phone number.

        Validates phone numbers in E.164 format (+1234567890).
        """
        # Remove all non-numeric characters except +
        cleaned = re.sub(r"[^\d+]", "", recipient)

        # Check for E.164 format
        e164_pattern = re.compile(r"^\+[1-9]\d{1,14}$")
        is_valid = bool(e164_pattern.match(cleaned))

        if not is_valid:
            # Try to format US numbers
            us_pattern = re.compile(r"^1?(\d{10})$")
            match = us_pattern.match(cleaned)
            if match:
                # Convert to E.164 format
                cleaned = f"+1{match.group(1)}"
                is_valid = True

        if not is_valid:
            logger.warning(
                "Invalid phone number: %s",
                recipient,
                extra={"recipient": recipient},
            )

        return is_valid

    def _optimize_message_length(self, message: str) -> List[str]:
        """
        Optimize message for SMS length limits.

        Splits long messages into multiple parts if necessary.
        """
        # Optimize message text
        optimized = self._apply_text_optimizations(message)

        # If message fits in single SMS, return as is
        if len(optimized) <= self.SINGLE_SMS_LIMIT:
            return [optimized]

        # Split into multiple parts
        parts = self._split_message_into_parts(optimized)

        # Ensure we don't exceed max parts
        parts = self._truncate_if_too_many_parts(parts)

        # Add part indicators
        parts = self._add_part_indicators(parts)

        return parts

    def _apply_text_optimizations(self, message: str) -> str:
        """Apply text optimizations to shorten message."""
        optimizations = {
            "Security Alert": "Alert",
            "Incident": "Inc",
            "Remediation": "Fix",
            "Critical": "CRIT",
            "Warning": "WARN",
            "Information": "INFO",
            "immediately": "now",
            "approximately": "~",
        }

        optimized = message
        for long_form, short_form in optimizations.items():
            optimized = optimized.replace(long_form, short_form)

        return optimized

    def _split_message_into_parts(self, message: str) -> List[str]:
        """Split message into parts by sentences."""
        parts = []
        max_length = self.CONCATENATED_SMS_LIMIT

        # Split by sentences first
        sentences = message.split(". ")
        current_part = ""

        for sentence in sentences:
            if len(current_part) + len(sentence) + 2 <= max_length:
                if current_part:
                    current_part += ". " + sentence
                else:
                    current_part = sentence
            else:
                if current_part:
                    parts.append(current_part + ".")
                current_part = sentence

        if current_part:
            parts.append(current_part)

        return parts

    def _truncate_if_too_many_parts(self, parts: List[str]) -> List[str]:
        """Truncate parts if exceeding maximum allowed."""
        if len(parts) > self.MAX_CONCATENATED_PARTS:
            # Truncate and add ellipsis
            parts = parts[: self.MAX_CONCATENATED_PARTS - 1]
            last_part = parts[-1]
            max_length = self.CONCATENATED_SMS_LIMIT
            if len(last_part) > max_length - 3:
                last_part = last_part[: max_length - 3]
            parts[-1] = last_part + "..."

        return parts

    def _add_part_indicators(self, parts: List[str]) -> List[str]:
        """Add part indicators to multi-part messages."""
        total_parts = len(parts)
        if total_parts > 1:
            max_length = self.CONCATENATED_SMS_LIMIT
            for i, part in enumerate(parts):
                indicator = f"({i + 1}/{total_parts}) "
                if len(indicator) + len(part) > max_length:
                    part = part[: max_length - len(indicator)]
                parts[i] = indicator + part

        return parts

    async def send(self, request: NotificationRequest) -> NotificationResult:
        """
        Send an SMS notification.

        Args:
            request: Notification request

        Returns:
            NotificationResult with status and details
        """
        # Call the internal send_sms method
        result = await self.send_sms(
            recipients=[request.recipient],
            subject=request.subject,
            message=request.body,
            priority=request.priority,
            metadata=request.metadata,
        )

        # Map the result to NotificationResult format
        success = result.get("status") == "queued"
        result_obj = NotificationResult(
            success=success,
            status=NotificationStatus.SENT if success else NotificationStatus.FAILED,
            message_id=result.get("messages", [{}])[0].get("body_preview", ""),  # Use first message preview as ID
            error=None if success else "Failed to queue SMS",
            metadata=result,
            timestamp=datetime.now(timezone.utc)
        )
        return result_obj

    async def send_sms(
        self,
        recipients: List[str],
        subject: str,
        message: str,
        priority: NotificationPriority,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send an SMS notification.

        This method queues the SMS for delivery and returns immediately.
        """
        # Validate recipients
        valid_recipients = []
        for recipient in recipients:
            # Normalize the phone number
            normalized = re.sub(r"[^\d+]", "", recipient)
            if await self.validate_recipient(normalized):
                valid_recipients.append(normalized)

        if not valid_recipients:
            raise ValueError("No valid phone numbers provided")

        # Combine subject and message for SMS
        sms_body = f"{subject}\n{message}" if subject else message

        # Optimize message length
        message_parts = self._optimize_message_length(sms_body)

        # Queue messages for each recipient
        queued_messages = []
        for recipient in valid_recipients:
            for part in message_parts:
                sms_message = SMSMessage(
                    to_number=recipient,
                    body=part,
                    priority=priority,
                    metadata=metadata,
                )
                await self.sms_queue.enqueue(sms_message)
                queued_messages.append(
                    {
                        "to": recipient,
                        "body_preview": part[:50] + "..." if len(part) > 50 else part,
                    }
                )

        # Start queue processor if not running
        if not self.sms_queue.processing:
            asyncio.create_task(self._process_sms_queue())

        return {
            "status": "queued",
            "recipients": valid_recipients,
            "message_count": len(queued_messages),
            "messages": queued_messages,
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _process_sms_queue(self) -> None:
        """Process SMS messages from the queue."""
        if self.sms_queue.processing:
            return

        self.sms_queue.processing = True
        logger.info("Starting SMS queue processor")

        try:
            while True:
                message = await self.sms_queue.get_next()
                if message is None:
                    await asyncio.sleep(1)
                    continue

                try:
                    await self._send_sms(message)
                    self.sms_queue.task_done()
                except (ValueError, RuntimeError, OSError) as e:
                    logger.error(
                        "Failed to send SMS: %s",
                        e,
                        extra={
                            "to_number": message.to_number,
                            "priority": message.priority.value,
                        },
                        exc_info=True,
                    )
                    self.sms_queue.task_done()

                    # Implement retry logic for high priority messages
                    if (
                        message.priority
                        in [
                            NotificationPriority.HIGH,
                            NotificationPriority.CRITICAL,
                        ]
                        and (message.metadata or {}).get("retry_count", 0) < 3
                    ):
                        message.metadata = message.metadata or {}
                        message.metadata["retry_count"] = (
                            message.metadata.get("retry_count", 0) + 1
                        )
                        await self.sms_queue.enqueue(message)

                # Rate limiting - Twilio recommends max 1 message per second
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("SMS queue processor cancelled")
            raise
        finally:
            self.sms_queue.processing = False

    async def _send_sms(self, message: SMSMessage) -> None:
        """Send a single SMS message via Twilio."""
        start_time = datetime.now(timezone.utc)

        try:
            # Send message via Twilio client
            if self._twilio_client is None:
                raise RuntimeError("Twilio client not initialized")
            result = await self._twilio_client.send_message(
                to_number=message.to_number,
                body=message.body,
                status_callback=self.config.status_callback_url,
                max_price=self.config.max_price_per_message,
            )

            # Update message with result
            message.message_sid = result["sid"]
            message.status = result["status"]
            self.sms_queue.track_delivery(result["sid"], message)

            delivery_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            logger.info(
                "SMS sent successfully",
                extra={
                    "to_number": message.to_number,
                    "message_sid": result["sid"],
                    "delivery_time": delivery_time,
                    "priority": message.priority.value,
                    "body_length": len(message.body),
                },
            )

        except TwilioClientError as e:
            message.status = "failed"
            message.error_message = str(e)
            raise
        except Exception as e:
            message.status = "failed"
            message.error_message = str(e)
            raise

    async def get_delivery_status(self, message_sid: str) -> Optional[Dict[str, Any]]:
        """Get the delivery status of a sent message."""
        if message_sid in self.sms_queue._delivery_status:
            message = self.sms_queue._delivery_status[message_sid]
            return {
                "message_sid": message_sid,
                "to_number": message.to_number,
                "status": message.status,
                "created_at": message.created_at.isoformat(),
                "delivered_at": (
                    message.delivered_at.isoformat() if message.delivered_at else None
                ),
                "error_message": message.error_message,
            }
        return None

    async def handle_status_callback(self, callback_data: Dict[str, Any]) -> None:
        """Handle Twilio status callback."""
        message_sid = callback_data.get("MessageSid")
        status = callback_data.get("MessageStatus")
        error_message = callback_data.get("ErrorMessage")

        if message_sid and status:
            self.sms_queue.update_delivery_status(
                message_sid=message_sid,
                status=status,
                error_message=error_message,
            )

    async def get_channel_limits(self) -> Dict[str, Any]:
        """Get SMS channel limits."""
        return {
            "max_message_size": self.SINGLE_SMS_LIMIT,
            "concatenated_limit": self.CONCATENATED_SMS_LIMIT,
            "max_parts": self.MAX_CONCATENATED_PARTS,
            "rate_limits": {"per_second": 1, "per_minute": 60},
            "supports_unicode": True,
            "supports_media": False,  # This is SMS, not MMS
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check SMS service health."""
        return {
            "status": "healthy" if self._twilio_client else "unhealthy",
            "queue_size": self.sms_queue.qsize() if hasattr(self.sms_queue, 'qsize') else 0,
            "twilio_connected": self._twilio_client is not None,
            "config_valid": bool(self.config.account_sid and self.config.auth_token),
        }

    async def close(self) -> None:
        """Clean up resources."""
        # In a real implementation, this would close Twilio client connections
        logger.info("SMS notification service closed")
