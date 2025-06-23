"""
Test mode functionality for the Communication Agent.

Provides a test mode that can capture and mock notifications
without actually sending them, useful for testing and development.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.communication_agent.interfaces import (
    NotificationRequest,
    NotificationResult,
    NotificationService,
)
from src.communication_agent.types import NotificationChannel, NotificationStatus
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DemoModeConfig:
    """Configuration for demo/test mode."""

    enabled: bool = False
    capture_notifications: bool = True
    simulate_failures: bool = False
    failure_rate: float = 0.0
    delay_seconds: float = 0.0
    log_notifications: bool = True
    simulate_delivery: bool = True  # For delivery simulation
    override_recipients: Optional[List[str]] = None  # For test recipient override


@dataclass
class CapturedNotification:
    """A notification captured in test mode."""

    request: NotificationRequest
    result: NotificationResult
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class TemplatePreview:
    """Handles template preview functionality for test mode."""

    def __init__(self) -> None:
        """Initialize template preview."""
        try:
            from src.communication_agent.templates import TemplateRenderer

            self.template_renderer: Optional[TemplateRenderer] = TemplateRenderer()
        except ImportError:
            self.template_renderer = None
        self._preview_cache: Dict[str, Dict[str, Any]] = {}

    async def preview_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        channel: Optional[NotificationChannel] = None,
    ) -> Dict[str, Any]:
        """
        Preview a template without sending.

        Args:
            template_name: Name of the template
            context: Context for rendering
            channel: Optional channel to preview for

        Returns:
            Preview result with rendered content
        """
        preview_key = f"{template_name}:{channel}:{hash(str(sorted(context.items())))}"

        # Check cache
        if preview_key in self._preview_cache:
            return self._preview_cache[preview_key]

        # Render template
        result: Dict[str, Any] = {
            "template_name": template_name,
            "channel": channel.value if channel else "all",
            "context": context,
            "rendered": {},
            "preview_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Use template renderer if available
        if self.template_renderer:
            try:
                # Convert template name to MessageType
                from src.communication_agent.types import MessageType

                # Try to match template name to MessageType enum
                message_type = None
                for mt in MessageType:
                    if (
                        mt.value.lower() == template_name.lower()
                        or mt.name.lower() == template_name.lower()
                    ):
                        message_type = mt
                        break

                if message_type:
                    # Render for specific channel or default
                    if channel:
                        rendered = self.template_renderer.render_for_channel(
                            message_type=message_type,
                            context=context,
                            channel=channel.value,
                        )
                    else:
                        rendered = self.template_renderer.render(
                            message_type=message_type,
                            context=context,
                            format_type="both",
                        )

                    result["rendered"] = rendered
                    result["status"] = "success"

                    # Add validation info
                    missing_vars = self.template_renderer.validate_context(
                        message_type, context
                    )
                    if missing_vars:
                        result["warnings"] = [
                            f"Missing template variables: {', '.join(missing_vars)}"
                        ]
                else:
                    result["status"] = "error"
                    result["error"] = f"Unknown template: {template_name}"

            except (ValueError, AttributeError, KeyError) as e:
                logger.error("Failed to render template preview", exc_info=True)
                result["status"] = "error"
                result["error"] = f"Template rendering failed: {str(e)}"
        else:
            result["status"] = "error"
            result["error"] = "Template renderer not available"

        # Cache the result
        self._preview_cache[preview_key] = result

        return result


class DemoModeService(NotificationService):
    """Wrapper service that captures notifications in test mode."""

    def __init__(
        self,
        wrapped_service: Optional[NotificationService],
        test_mode: "DemoMode",
        channel: NotificationChannel,
    ):
        """Initialize test mode service wrapper."""
        self.wrapped_service = wrapped_service
        self.test_mode = test_mode
        self.channel = channel
        self.captured_notifications: List[CapturedNotification] = []

    async def send(self, request: NotificationRequest) -> NotificationResult:
        """Send notification through test mode."""
        await self._handle_recipient_override(request)
        self._log_notification_if_enabled(request)
        await self._apply_delay_if_configured()

        # Check for simulated failure
        failure_result = await self._check_simulated_failure(request)
        if failure_result:
            return failure_result

        # Use real service if available and not simulating
        if self._should_use_real_service() and self.wrapped_service:
            return await self.wrapped_service.send(request)

        # Create and return successful test result
        return await self._create_successful_result(request)

    async def _handle_recipient_override(self, request: NotificationRequest) -> None:
        """Override recipients if configured."""
        if not self.test_mode.config.override_recipients:
            return

        original_recipient = request.recipient
        test_recipients = self.test_mode.config.override_recipients

        if test_recipients:
            request.recipient = test_recipients[0]
            if self.test_mode.config.log_notifications:
                logger.info(
                    "Test mode: Overriding recipient",
                    extra={
                        "original": original_recipient,
                        "override": request.recipient,
                    },
                )

    def _log_notification_if_enabled(self, request: NotificationRequest) -> None:
        """Log notification if logging is enabled."""
        if self.test_mode.config.log_notifications:
            logger.info(
                "Test mode: Capturing notification",
                extra={
                    "channel": self.channel.value,
                    "subject": request.subject,
                    "recipient": request.recipient,
                    "priority": request.priority.value,
                },
            )

    async def _apply_delay_if_configured(self) -> None:
        """Apply delay if configured."""
        if self.test_mode.config.delay_seconds > 0:
            await asyncio.sleep(self.test_mode.config.delay_seconds)

    async def _check_simulated_failure(
        self, request: NotificationRequest
    ) -> Optional[NotificationResult]:
        """Check if we should simulate a failure."""
        if not self.test_mode.config.simulate_failures:
            return None

        import random

        if random.random() < self.test_mode.config.failure_rate:
            result = NotificationResult(
                success=False,
                status=NotificationStatus.FAILED,
                error="Simulated failure in test mode",
            )
            self._capture_notification_if_enabled(request, result)
            return result

        return None

    def _should_use_real_service(self) -> bool:
        """Check if we should use the real service."""
        return bool(
            self.wrapped_service and not self.test_mode.config.simulate_delivery
        )

    async def _create_successful_result(
        self, request: NotificationRequest
    ) -> NotificationResult:
        """Create a successful test result."""
        result = NotificationResult(
            success=True,
            status=NotificationStatus.SENT,
            message_id=f"test-{datetime.now(timezone.utc).timestamp()}",
            metadata={
                "test_mode": True,
                "simulated": True,
            },
        )
        self._capture_notification_if_enabled(request, result)
        return result

    def _capture_notification_if_enabled(
        self, request: NotificationRequest, result: NotificationResult
    ) -> None:
        """Capture notification if capturing is enabled."""
        if self.test_mode.config.capture_notifications:
            captured = CapturedNotification(
                request=request,
                result=result,
            )
            self.test_mode._captured_notifications.append(captured)
            self.captured_notifications.append(captured)

    async def validate_recipient(self, recipient: str) -> bool:
        """Validate recipient in test mode."""
        if self.wrapped_service:
            return await self.wrapped_service.validate_recipient(recipient)
        # Default to true in test mode
        return True

    async def get_channel_limits(self) -> Dict[str, Any]:
        """Get channel limits in test mode."""
        if self.wrapped_service:
            return await self.wrapped_service.get_channel_limits()
        # Return default test limits
        return {
            "max_message_size": 10000,
            "rate_limits": {"per_minute": 60},
            "test_mode": True,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Health check in test mode."""
        if self.wrapped_service:
            health = await self.wrapped_service.health_check()
            health["test_mode"] = True
            return health
        # Return test health status
        return {
            "status": "healthy",
            "service": "test_mode",
            "test_mode": True,
        }

    def get_channel_type(self) -> NotificationChannel:
        """Get the notification channel type."""
        return self.channel


class DemoMode:
    """Demo mode manager for the Communication Agent."""

    def __init__(self, config: Optional[DemoModeConfig] = None):
        """Initialize test mode."""
        self.config = config or DemoModeConfig()
        self._captured_notifications: List[CapturedNotification] = []
        self.preview = TemplatePreview()  # Initialize template preview
        self.wrapped_services: Dict[NotificationChannel, NotificationService] = {}

    def wrap_service(
        self,
        service: NotificationService,
        channel: Optional[NotificationChannel] = None,
    ) -> NotificationService:
        """Wrap a notification service for test mode."""
        if not self.config.enabled:
            return service

        # Determine channel from service if not provided
        if channel is None:
            # Try to get channel from service's get_channel_type method
            get_channel_type = getattr(service, "get_channel_type", None)
            if get_channel_type:
                channel = get_channel_type()
            else:
                # Try to determine from service type or attributes
                for ch in NotificationChannel:
                    if ch.value.lower() in service.__class__.__name__.lower():
                        channel = ch
                        break
                else:
                    # Default to webhook if can't determine
                    channel = NotificationChannel.WEBHOOK

        wrapped = DemoModeService(service, self, channel)
        self.wrapped_services[channel] = wrapped
        return wrapped

    def reset(self) -> None:
        """Reset test mode state."""
        self._captured_notifications.clear()
        self.wrapped_services.clear()
        self.preview._preview_cache.clear()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of test mode activity."""
        channel_counts: Dict[str, int] = {}
        for notification in self._captured_notifications:
            channel = notification.request.channel.value
            channel_counts[channel] = channel_counts.get(channel, 0) + 1

        return {
            "enabled": self.config.enabled,
            "total_notifications": len(self._captured_notifications),
            "by_channel": channel_counts,
            "failed_count": len(
                [n for n in self._captured_notifications if not n.result.success]
            ),
            "preview_cache_size": len(self.preview._preview_cache),
            "config": {
                "capture_notifications": self.config.capture_notifications,
                "simulate_failures": self.config.simulate_failures,
                "failure_rate": self.config.failure_rate,
                "override_recipients": self.config.override_recipients,
            },
        }

    def get_captured_notifications(
        self, channel: Optional[NotificationChannel] = None
    ) -> List[CapturedNotification]:
        """Get captured notifications, optionally filtered by channel."""
        if channel is None:
            return self._captured_notifications.copy()

        return [n for n in self._captured_notifications if n.request.channel == channel]

    def clear_captured_notifications(self) -> None:
        """Clear all captured notifications."""
        self._captured_notifications.clear()

    def get_all_captured_notifications(self) -> List[CapturedNotification]:
        """Get all captured notifications from all wrapped services."""
        all_notifications = self._captured_notifications.copy()

        # Add notifications from wrapped services if they have captured_notifications attribute
        for service in self.wrapped_services.values():
            if hasattr(service, "captured_notifications"):
                all_notifications.extend(service.captured_notifications)

        return all_notifications

    def clear_all_captured_notifications(self) -> None:
        """Clear all captured notifications from all wrapped services."""
        self._captured_notifications.clear()

        # Clear notifications from wrapped services if they have captured_notifications attribute
        for service in self.wrapped_services.values():
            if hasattr(service, "captured_notifications"):
                service.captured_notifications.clear()

    def get_config(self) -> DemoModeConfig:
        """Get the current configuration."""
        return self.config

    @property
    def captured_notifications(self) -> List[CapturedNotification]:
        """Property to access captured notifications."""
        return self._captured_notifications

    def get_notification_count(
        self, channel: Optional[NotificationChannel] = None
    ) -> int:
        """Get count of captured notifications."""
        return len(self.get_captured_notifications(channel))

    def enable(self) -> None:
        """Enable test mode."""
        self.config.enabled = True
        logger.info("Test mode enabled")

    def disable(self) -> None:
        """Disable test mode."""
        self.config.enabled = False
        logger.info("Test mode disabled")

    def __enter__(self) -> "DemoMode":
        """Context manager entry."""
        self.enable()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.disable()
        self.clear_captured_notifications()

    async def __aenter__(self) -> "DemoMode":
        """Async context manager entry."""
        self.enable()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        self.disable()
        self.clear_captured_notifications()
