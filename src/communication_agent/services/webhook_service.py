"""
Webhook notification service for the Communication Agent.

Handles webhook notifications with generic webhook support, payload formatting,
retry mechanism, and authentication support.
"""

import asyncio
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiohttp

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


class WebhookMethod(str, Enum):
    """HTTP methods for webhook requests."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class WebhookAuthType(str, Enum):
    """Webhook authentication types."""

    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"
    HMAC = "hmac"
    CUSTOM_HEADER = "custom_header"


@dataclass
class WebhookConfig:
    """Webhook configuration."""

    url: str
    method: WebhookMethod = WebhookMethod.POST
    auth_type: WebhookAuthType = WebhookAuthType.NONE
    auth_credentials: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5
    verify_ssl: bool = True


@dataclass
class WebhookPayload:
    """Webhook payload structure."""

    event_type: str
    timestamp: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    signature: Optional[str] = None


class WebhookQueue:
    """Webhook queue for managing webhook deliveries."""

    def __init__(self, max_size: int = 1000):
        """Initialize webhook queue."""
        self.queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=max_size)
        self.processing = False
        self._processor_task: Optional[asyncio.Task[Any]] = None
        self._delivery_history: List[Dict[str, Any]] = []

    async def enqueue(self, webhook_data: Dict[str, Any]) -> None:
        """Add a webhook to the queue."""
        await self.queue.put(webhook_data)
        logger.debug(
            "Webhook queued for %s",
            webhook_data['url'],
            extra={
                "method": webhook_data.get("method", "POST"),
                "priority": webhook_data.get("priority", "medium"),
                "queue_size": self.queue.qsize(),
            },
        )

    async def get_next(self) -> Optional[Dict[str, Any]]:
        """Get the next webhook from the queue."""
        try:
            return await self.queue.get()
        except asyncio.QueueEmpty:
            return None

    def task_done(self) -> None:
        """Mark the current task as done."""
        self.queue.task_done()

    def add_to_history(self, delivery_record: Dict[str, Any]) -> None:
        """Add a delivery record to history."""
        self._delivery_history.append(delivery_record)
        # Keep only last 1000 records
        if len(self._delivery_history) > 1000:
            self._delivery_history = self._delivery_history[-1000:]


class WebhookNotificationService(NotificationService):
    """
    Webhook notification service implementation.

    Supports generic webhooks with various authentication methods,
    custom payloads, retry logic, and delivery tracking.
    """

    def __init__(
        self,
        default_config: Optional[WebhookConfig] = None,
        webhook_configs: Optional[Dict[str, WebhookConfig]] = None,
    ):
        """
        Initialize webhook notification service.

        Args:
            default_config: Default webhook configuration
            webhook_configs: Named webhook configurations
        """
        self.default_config = default_config
        self.webhook_configs = webhook_configs or {}
        self.webhook_queue = WebhookQueue()
        self._session: Optional[aiohttp.ClientSession] = None

        logger.info(
            "Webhook notification service initialized",
            extra={
                "has_default": bool(default_config),
                "named_webhooks": list(self.webhook_configs.keys()),
            },
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    def get_channel_type(self) -> NotificationChannel:
        """Get the channel type this service implements."""
        return NotificationChannel.WEBHOOK

    async def validate_recipient(self, recipient: str) -> bool:
        """
        Validate a webhook URL or webhook name.

        Args:
            recipient: Either a URL or a webhook configuration name

        Returns:
            True if valid URL or known webhook name
        """
        # Check if it's a named webhook
        if recipient in self.webhook_configs:
            return True

        # Validate as URL
        try:
            result = urlparse(recipient)
            return all([result.scheme, result.netloc])
        except (ValueError, AttributeError):
            return False

    def _format_payload(
        self,
        subject: str,
        message: str,
        priority: NotificationPriority,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Format the webhook payload."""
        payload: Dict[str, Any] = {
            "event_type": "sentinelops.notification",
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "data": {
                "subject": subject,
                "message": message,
                "priority": priority.value,
            },
        }

        # Add metadata if provided
        if metadata:
            payload["data"]["metadata"] = metadata

            # Extract specific fields to top level if present
            if "incident_id" in metadata:
                payload["incident_id"] = metadata["incident_id"]
            if "message_type" in metadata:
                payload["event_type"] = f"sentinelops.{metadata['message_type']}"

        return payload

    def _generate_signature(
        self,
        payload: str,
        secret: str,
        algorithm: str = "sha256",
    ) -> str:
        """Generate HMAC signature for webhook payload."""
        if algorithm == "sha256":
            hash_func = hashlib.sha256
        elif algorithm == "sha1":
            hash_func = hashlib.sha1
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hash_func,
        ).hexdigest()

        return f"{algorithm}={signature}"

    def _prepare_auth_headers(
        self,
        config: WebhookConfig,
        payload: Optional[str] = None,
    ) -> Dict[str, str]:
        """Prepare authentication headers based on config."""
        headers: Dict[str, str] = {}

        if config.auth_type == WebhookAuthType.NONE:
            return headers

        if not config.auth_credentials:
            logger.warning("No auth credentials provided for %s", config.auth_type)
            return headers

        if config.auth_type == WebhookAuthType.BASIC:
            import base64

            username = config.auth_credentials.get("username", "")
            password = config.auth_credentials.get("password", "")
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"

        elif config.auth_type == WebhookAuthType.BEARER:
            token = config.auth_credentials.get("token", "")
            headers["Authorization"] = f"Bearer {token}"

        elif config.auth_type == WebhookAuthType.API_KEY:
            key_name = config.auth_credentials.get("key_name", "X-API-Key")
            key_value = config.auth_credentials.get("key_value", "")
            headers[key_name] = key_value

        elif config.auth_type == WebhookAuthType.HMAC:
            if payload:
                secret = config.auth_credentials.get("secret", "")
                algorithm = config.auth_credentials.get("algorithm", "sha256")
                header_name = config.auth_credentials.get(
                    "header_name",
                    "X-Webhook-Signature",
                )
                signature = self._generate_signature(payload, secret, algorithm)
                headers[header_name] = signature

        elif config.auth_type == WebhookAuthType.CUSTOM_HEADER:
            for key, value in config.auth_credentials.items():
                headers[key] = value

        return headers

    async def send(self, request: NotificationRequest) -> NotificationResult:
        """
        Send webhook notifications.

        Args:
            request: Notification request

        Returns:
            Status of queued webhooks
        """
        # Extract data from request
        recipients = request.recipients if hasattr(request, 'recipients') else []
        subject = request.subject if hasattr(request, 'subject') else ""
        message = request.message if hasattr(request, 'message') else ""
        priority = request.priority if hasattr(request, 'priority') else NotificationPriority.MEDIUM
        metadata = request.metadata if hasattr(request, 'metadata') else None

        # Validate recipients
        valid_recipients = []
        for recipient in recipients:
            if await self.validate_recipient(recipient):
                valid_recipients.append(recipient)
            else:
                logger.warning("Invalid webhook recipient: %s", recipient)

        if not valid_recipients:
            raise ValueError("No valid webhook recipients provided")

        # Prepare payload
        payload = self._format_payload(subject, message, priority, metadata)

        # Queue webhooks for each recipient
        queued_webhooks = []
        for recipient in valid_recipients:
            # Get webhook configuration
            if recipient in self.webhook_configs:
                config = self.webhook_configs[recipient]
                webhook_url = config.url
                webhook_name = recipient
            else:
                # Use default config with custom URL
                config = self.default_config or WebhookConfig(url=recipient)
                webhook_url = recipient
                webhook_name = None

            webhook_data = {
                "url": webhook_url,
                "name": webhook_name,
                "config": config,
                "payload": payload,
                "priority": priority,
                "retry_count": 0,
                "queued_at": datetime.now(timezone.utc).isoformat(),
            }

            await self.webhook_queue.enqueue(webhook_data)
            queued_webhooks.append(
                {
                    "url": webhook_url,
                    "name": webhook_name,
                }
            )

        # Start queue processor if not running
        if not self.webhook_queue.processing:
            asyncio.create_task(self._process_webhook_queue())

        return NotificationResult(
            success=True,
            status=NotificationStatus.QUEUED,
            message_id=f"webhook-batch-{datetime.now(timezone.utc).isoformat()}",
            metadata={
                "webhooks": queued_webhooks,
                "queued_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def _process_webhook_queue(self) -> None:
        """Process webhooks from the queue."""
        if self.webhook_queue.processing:
            return

        self.webhook_queue.processing = True
        logger.info("Starting webhook queue processor")

        try:
            while True:
                webhook_data = await self.webhook_queue.get_next()
                if webhook_data is None:
                    await asyncio.sleep(1)
                    continue

                try:
                    await self._send_webhook(webhook_data)
                    self.webhook_queue.task_done()
                except (ValueError, RuntimeError, OSError) as e:
                    logger.error(
                        "Failed to send webhook: %s",
                        e,
                        extra={
                            "url": webhook_data.get("url"),
                            "name": webhook_data.get("name"),
                        },
                        exc_info=True,
                    )
                    self.webhook_queue.task_done()

                    # Implement retry logic
                    config = webhook_data["config"]
                    if webhook_data["retry_count"] < config.max_retries:
                        webhook_data["retry_count"] += 1
                        # Exponential backoff
                        delay = config.retry_delay * (
                            2 ** (webhook_data["retry_count"] - 1)
                        )
                        await asyncio.sleep(delay)
                        await self.webhook_queue.enqueue(webhook_data)

        except asyncio.CancelledError:
            logger.info("Webhook queue processor cancelled")
            raise
        finally:
            self.webhook_queue.processing = False

    async def _send_webhook(self, webhook_data: Dict[str, Any]) -> None:
        """Send a single webhook."""
        config: WebhookConfig = webhook_data["config"]
        payload = webhook_data["payload"]
        start_time = datetime.now(timezone.utc)

        # Prepare request
        payload_json = json.dumps(payload)

        # Build headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SentinelOps/1.0",
            "X-SentinelOps-Event": payload.get("event_type", "notification"),
            "X-SentinelOps-Priority": webhook_data["priority"].value,
        }

        # Add custom headers from config
        if config.headers:
            headers.update(config.headers)

        # Add authentication headers
        auth_headers = self._prepare_auth_headers(config, payload_json)
        headers.update(auth_headers)

        # Send request
        session = await self._get_session()

        try:
            async with session.request(
                method=config.method.value,
                url=config.url,
                data=payload_json if config.method != WebhookMethod.GET else None,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=config.timeout),
                ssl=config.verify_ssl,
            ) as response:
                response_data = {
                    "status_code": response.status,
                    "headers": dict(response.headers),
                }

                # Try to read response body
                try:
                    response_data["body"] = await response.text()
                except (ValueError, IOError):
                    response_data["body"] = None

                delivery_time = (datetime.now(timezone.utc) - start_time).total_seconds()

                # Log delivery
                delivery_record = {
                    "url": config.url,
                    "name": webhook_data.get("name"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "delivery_time": delivery_time,
                    "status_code": response.status,
                    "success": 200 <= response.status < 300,
                    "retry_count": webhook_data.get("retry_count", 0),
                }

                self.webhook_queue.add_to_history(delivery_record)

                if 200 <= response.status < 300:
                    logger.info(
                        "Webhook delivered successfully",
                        extra={
                            "url": config.url,
                            "status_code": response.status,
                            "delivery_time": delivery_time,
                        },
                    )
                else:
                    logger.warning(
                        "Webhook returned non-success status: %d",
                        response.status,
                        extra={
                            "url": config.url,
                            "status_code": response.status,
                            "response_body": response_data.get("body"),
                        },
                    )
                    # Raise to trigger retry
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                    )

        except asyncio.TimeoutError:
            logger.error(
                "Webhook timeout after %ds",
                config.timeout,
                extra={"url": config.url},
            )
            raise
        except Exception as e:
            logger.error(
                "Webhook delivery failed: %s",
                e,
                extra={"url": config.url},
                exc_info=True,
            )
            raise

    def get_delivery_history(
        self,
        limit: int = 100,
        url_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get webhook delivery history."""
        history = self.webhook_queue._delivery_history

        if url_filter:
            history = [record for record in history if record.get("url") == url_filter]

        return history[-limit:]

    async def close(self) -> None:
        """Close the webhook service and cleanup resources."""
        if self._session and not self._session.closed:
            await self._session.close()
        logger.info("Webhook notification service closed")

    async def get_channel_limits(self) -> Dict[str, Any]:
        """Get channel-specific limits and capabilities."""
        return {
            "max_message_size": 1024 * 1024 * 10,  # 10MB
            "rate_limits": {"per_minute": 100, "per_hour": 5000},
            "supports_attachments": False,
            "supports_retries": True,
            "max_retries": 3,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        health_status = {
            "status": "healthy",
            "service": "webhook",
            "active_session": self._session is not None and not self._session.closed,
            "queue_size": self.webhook_queue.queue.qsize() if self.webhook_queue else 0,
            "delivery_history_count": (
                len(self.webhook_queue._delivery_history) if self.webhook_queue else 0
            ),
        }
        # Check if default config is valid
        if self.default_config:
            try:
                is_valid = await self.validate_recipient(self.default_config.url)
                health_status["default_webhook_valid"] = is_valid
            except (ValueError, OSError) as e:
                health_status["default_webhook_valid"] = False
                health_status["default_webhook_error"] = str(e)

        return health_status
