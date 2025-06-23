"""
Slack notification service for the Communication Agent.

Handles Slack notifications with channel configuration, message formatting,
interactive messages, and thread management.
"""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

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
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SlackConfig:
    """Slack API configuration."""

    bot_token: str
    default_channel: str = "#alerts"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1
    enable_threads: bool = True
    enable_interactive: bool = True


@dataclass
class SlackMessage:
    """Slack message structure."""

    channel: str
    text: str
    blocks: Optional[List[Dict[str, Any]]] = None
    thread_ts: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    unfurl_links: bool = False
    unfurl_media: bool = False


class SlackMessageFormatter:
    """Formats messages for Slack with rich formatting support."""

    @staticmethod
    def format_incident_notification(
        incident_type: str,
        severity: str,
        timestamp: str,
        affected_resources: List[str],
        detection_source: str,
        initial_assessment: str,
        incident_id: str,
    ) -> Dict[str, Any]:
        """Format an incident notification for Slack."""
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }.get(severity.lower(), "⚪")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{severity_emoji} Security Incident Detected",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{incident_type}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{severity.upper()}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{timestamp}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Detection Source:*\n{detection_source}",
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Affected Resources:*\n• "
                    + "\n• ".join(affected_resources),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Initial Assessment:*\n{initial_assessment}",
                },
            },
            {
                "type": "divider",
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Incident ID: `{incident_id}`",
                    },
                ],
            },
        ]

        # Add interactive buttons
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Details",
                            "emoji": True,
                        },
                        "value": f"view_incident_{incident_id}",
                        "action_id": "view_incident",
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Acknowledge",
                            "emoji": True,
                        },
                        "value": f"ack_incident_{incident_id}",
                        "action_id": "acknowledge_incident",
                        "style": "primary",
                    },
                ],
            }
        )

        return {
            "text": f"Security Incident: {incident_type}",
            "blocks": blocks,
        }

    @staticmethod
    def format_thread_update(
        update_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Format a thread update message."""
        blocks = [
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"*{update_type}* • "
                            f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                        ),
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message,
                },
            },
        ]

        if metadata:
            fields = []
            for key, value in metadata.items():
                fields.append(
                    {
                        "type": "mrkdwn",
                        "text": f"*{key}:*\n{value}",
                    }
                )

            if fields:
                blocks.append(
                    {
                        "type": "section",
                        "fields": fields[:10],  # Slack limits to 10 fields
                    }
                )

        return {"blocks": blocks}


class SlackAPIClient:
    """Slack API client for making API calls."""

    def __init__(self, config: SlackConfig):
        """Initialize the Slack API client."""
        self.config = config
        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {config.bot_token}",
            "Content-Type": "application/json",
        }
        self._session: Optional[aiohttp.ClientSession] = None
        self.thread_map: Dict[str, str] = {}  # incident_id -> thread_ts

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout,
            )
        return self._session

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """Make a request to the Slack API with retry logic."""
        url = f"{self.base_url}/{endpoint}"
        session = await self._get_session()

        try:
            async with session.request(method, url, json=data) as response:
                result: Dict[str, Any] = await response.json()

                if not result.get("ok", False):
                    error = result.get("error", "Unknown error")
                    raise ValueError(f"Slack API error: {error}")

                return result

        except Exception:
            if retry_count < self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay * (retry_count + 1))
                return await self._make_request(method, endpoint, data, retry_count + 1)
            raise

    async def post_message(self, message: SlackMessage) -> Dict[str, Any]:
        """Post a message to Slack."""
        data: Dict[str, Any] = {
            "channel": message.channel,
            "text": message.text,
        }

        if message.blocks:
            data["blocks"] = message.blocks

        if message.thread_ts:
            data["thread_ts"] = message.thread_ts

        if message.attachments:
            data["attachments"] = message.attachments

        data["unfurl_links"] = message.unfurl_links
        data["unfurl_media"] = message.unfurl_media

        return await self._make_request("POST", "chat.postMessage", data)

    async def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Update an existing message."""
        data: Dict[str, Any] = {
            "channel": channel,
            "ts": ts,
            "text": text,
        }

        if blocks:
            data["blocks"] = blocks

        return await self._make_request("POST", "chat.update", data)

    async def get_channel_id(self, channel_name: str) -> Optional[str]:
        """Get channel ID from channel name."""
        try:
            # List conversations to find the channel
            result = await self._make_request(
                "GET", "conversations.list", {"limit": 1000}
            )

            for channel in result.get("channels", []):
                if channel["name"] == channel_name.lstrip("#"):
                    return str(channel["id"])

            return None
        except (ValueError, RuntimeError, OSError) as e:
            logger.error("Failed to get channel ID: %s", e)
            return None

    async def create_thread(
        self,
        channel: str,
        initial_message: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[str]:
        """Create a new thread and return the thread timestamp."""
        message = SlackMessage(
            channel=channel,
            text=initial_message,
            blocks=blocks,
        )

        result = await self.post_message(message)
        return result.get("ts")

    async def close(self) -> None:
        """Close the API client session."""
        if self._session and not self._session.closed:
            await self._session.close()


class SlackNotificationService(NotificationService):
    """
    Slack notification service implementation.

    Supports channel configuration, message formatting, interactive messages,
    and thread management.
    """

    def __init__(self, config: SlackConfig):
        """Initialize Slack notification service."""
        self.config = config
        self.api_client = SlackAPIClient(config)
        self.formatter = SlackMessageFormatter()
        self.channel_cache: Dict[str, str] = {}  # channel_name -> channel_id

        logger.info(
            "Slack notification service initialized",
            extra={
                "default_channel": config.default_channel,
                "enable_threads": config.enable_threads,
                "enable_interactive": config.enable_interactive,
            },
        )

    def get_channel_type(self) -> NotificationChannel:
        """Get the channel type this service implements."""
        return NotificationChannel.SLACK

    async def validate_recipient(self, recipient: str) -> bool:
        """
        Validate a Slack channel or user.

        Accepts:
        - Channel names: #channel-name
        - Channel IDs: C1234567890
        - User IDs: U1234567890
        - User mentions: @username
        """
        # Basic validation patterns
        patterns = [
            r"^#[a-z0-9-_]+$",  # Channel name
            r"^C[A-Z0-9]+$",  # Channel ID
            r"^U[A-Z0-9]+$",  # User ID
            r"^@[a-z0-9._-]+$",  # Username mention
        ]

        for pattern in patterns:
            if re.match(pattern, recipient, re.IGNORECASE):
                return True

        logger.warning(
            "Invalid Slack recipient: %s",
            recipient,
            extra={"recipient": recipient},
        )
        return False

    async def _resolve_channel(self, recipient: str) -> str:
        """Resolve channel name to ID if needed."""
        # If it's already a channel ID or user ID, return as-is
        if re.match(r"^[CU][A-Z0-9]+$", recipient, re.IGNORECASE):
            return recipient

        # If it's a channel name, get the ID
        if recipient.startswith("#"):
            channel_name = recipient.lstrip("#")

            # Check cache first
            if channel_name in self.channel_cache:
                return self.channel_cache[channel_name]

            # Look up the channel
            channel_id = await self.api_client.get_channel_id(channel_name)
            if channel_id:
                self.channel_cache[channel_name] = channel_id
                return channel_id

        # For user mentions, we'd need to resolve to user ID
        # For now, return the default channel
        logger.warning(
            "Could not resolve recipient %s, using default channel",
            recipient,
            extra={"recipient": recipient, "default": self.config.default_channel},
        )
        return self.config.default_channel

    async def send(self, request: NotificationRequest) -> NotificationResult:
        """Send a Slack notification."""
        # Extract data from request
        data = self._extract_request_data(request)

        # Get valid recipients
        valid_recipients = await self._get_valid_recipients(data["recipients"])

        # Format message
        blocks, thread_ts, message = await self._format_message(
            data["message"], data["subject"], data["metadata"]
        )

        # Send to each recipient
        results = await self._send_to_recipients(
            valid_recipients,
            data["subject"],
            message,
            blocks,
            thread_ts,
            data["metadata"],
            data["priority"],
        )

        return NotificationResult(
            success=True,
            status=NotificationStatus.SENT,
            message_id=f"slack-batch-{datetime.now(timezone.utc).isoformat()}",
            metadata={
                "results": results,
                "sent_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    def _extract_request_data(self, request: NotificationRequest) -> Dict[str, Any]:
        """Extract data from notification request."""
        return {
            "recipients": request.recipients if hasattr(request, "recipients") else [],
            "subject": request.subject if hasattr(request, "subject") else "",
            "message": request.message if hasattr(request, "message") else "",
            "priority": (
                request.priority
                if hasattr(request, "priority")
                else NotificationPriority.MEDIUM
            ),
            "metadata": request.metadata if hasattr(request, "metadata") else None,
        }

    async def _get_valid_recipients(self, recipients: List[str]) -> List[str]:
        """Get validated recipients or default channel."""
        valid_recipients = []
        for recipient in recipients:
            if await self.validate_recipient(recipient):
                valid_recipients.append(recipient)

        if not valid_recipients:
            valid_recipients = [self.config.default_channel]

        return valid_recipients

    async def _format_message(
        self,
        message: str,
        subject: str,  # pylint: disable=unused-argument
        metadata: Optional[Dict[str, Any]],
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str], str]:
        """Format message based on metadata."""
        blocks = None
        thread_ts = None

        if metadata:
            message_type = metadata.get("message_type")

            if message_type == "incident_detected":
                blocks, message = self._format_incident_notification(metadata, message)

            thread_ts = await self._get_thread_ts(metadata)

        return blocks, thread_ts, message

    def _format_incident_notification(
        self, metadata: Dict[str, Any], default_message: str
    ) -> Tuple[Optional[List[Dict[str, Any]]], str]:
        """Format incident detection notification."""
        context = metadata.get("context", {})
        formatted = self.formatter.format_incident_notification(
            incident_type=context.get("incident_type", "Unknown"),
            severity=context.get("severity", "unknown"),
            timestamp=context.get("timestamp", ""),
            affected_resources=context.get("affected_resources", "").split(", "),
            detection_source=context.get("detection_source", "Unknown"),
            initial_assessment=context.get("initial_assessment", ""),
            incident_id=context.get("incident_id", ""),
        )
        return formatted.get("blocks"), formatted.get("text", default_message)

    async def _get_thread_ts(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Get thread timestamp if threads are enabled."""
        if self.config.enable_threads:
            incident_id = metadata.get("context", {}).get("incident_id")
            if incident_id and incident_id in self.api_client.thread_map:
                return self.api_client.thread_map[incident_id]
        return None

    async def _send_to_recipients(
        self,
        recipients: List[str],
        subject: str,
        message: str,
        blocks: Optional[List[Dict[str, Any]]],
        thread_ts: Optional[str],
        metadata: Optional[Dict[str, Any]],
        priority: NotificationPriority,
    ) -> List[Dict[str, Any]]:
        """Send message to all recipients."""
        results = []

        for recipient in recipients:
            result = await self._send_single_message(
                recipient, subject, message, blocks, thread_ts, metadata, priority
            )
            results.append(result)

        return results

    async def _send_single_message(
        self,
        recipient: str,
        subject: str,
        message: str,
        blocks: Optional[List[Dict[str, Any]]],
        thread_ts: Optional[str],
        metadata: Optional[Dict[str, Any]],
        priority: NotificationPriority,
    ) -> Dict[str, Any]:
        """Send message to a single recipient."""
        try:
            channel = await self._resolve_channel(recipient)

            slack_message = SlackMessage(
                channel=channel,
                text=f"*{subject}*\n{message}" if subject else message,
                blocks=blocks,
                thread_ts=thread_ts,
            )

            result = await self.api_client.post_message(slack_message)

            # Store thread timestamp if needed
            await self._store_thread_ts(result, thread_ts, metadata)

            logger.info(
                "Slack message sent successfully",
                extra={
                    "channel": channel,
                    "priority": priority.value,
                    "is_threaded": bool(thread_ts),
                },
            )

            return {
                "channel": channel,
                "timestamp": result.get("ts"),
                "status": "success",
            }

        except (ValueError, RuntimeError, OSError) as e:
            logger.error(
                "Failed to send Slack message: %s",
                e,
                extra={
                    "recipient": recipient,
                    "error": str(e),
                },
                exc_info=True,
            )
            return {
                "channel": recipient,
                "status": "failed",
                "error": str(e),
            }

    async def _store_thread_ts(
        self,
        result: Dict[str, Any],
        thread_ts: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> None:
        """Store thread timestamp if this created a new thread."""
        if (
            self.config.enable_threads
            and not thread_ts
            and metadata
            and "context" in metadata
        ):
            incident_id = metadata["context"].get("incident_id")
            if incident_id and "ts" in result:
                self.api_client.thread_map[incident_id] = result["ts"]

    async def send_thread_update(
        self,
        incident_id: str,
        update_type: str,
        message: str,
        channel: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send an update to an existing thread."""
        if not self.config.enable_threads:
            return None

        # Get thread timestamp
        thread_ts = self.api_client.thread_map.get(incident_id)
        if not thread_ts:
            logger.warning(
                "No thread found for incident %s",
                incident_id,
                extra={"incident_id": incident_id},
            )
            return None

        # Format the update
        formatted = self.formatter.format_thread_update(
            update_type=update_type,
            message=message,
            metadata=metadata,
        )

        # Use the channel from the original message or default
        if not channel:
            channel = self.config.default_channel

        slack_message = SlackMessage(
            channel=channel,
            text=f"{update_type}: {message}",
            blocks=formatted.get("blocks"),
            thread_ts=thread_ts,
        )

        try:
            result = await self.api_client.post_message(slack_message)
            return {
                "status": "success",
                "timestamp": result.get("ts"),
            }
        except (ValueError, RuntimeError, OSError) as e:
            logger.error(
                "Failed to send thread update: %s",
                e,
                extra={"incident_id": incident_id, "error": str(e)},
                exc_info=True,
            )
            return None

    async def get_channel_limits(self) -> Dict[str, Any]:
        """Get Slack channel limits."""
        return {
            "max_message_size": 40000,  # 40KB
            "max_blocks": 50,
            "max_attachments": 20,
            "rate_limits": {"per_minute": 60, "per_workspace_per_minute": 600},
            "supports_markdown": True,
            "supports_threading": True,
            "supports_reactions": True,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check Slack service health."""
        return {
            "status": "healthy" if self.api_client else "unhealthy",
            "bot_token_valid": bool(self.config.bot_token),
            "rate_limit_remaining": getattr(
                self.api_client, "rate_limit_remaining", None
            ),
        }

    async def close(self) -> None:
        """Close the Slack notification service."""
        await self.api_client.close()
        logger.info("Slack notification service closed")
