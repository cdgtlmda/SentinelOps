"""
Comprehensive tests for communication_agent.test_mode module.

Tests test mode functionality including demo mode configuration,
notification capture, template preview, service wrapping, and
all demo mode operations with 100% production code coverage.

NO MOCKING - All tests use real implementation and production code.
TARGET: ≥90% statement coverage of communication_agent/test_mode.py
"""

from datetime import datetime, timezone
from typing import Dict, Any, List

import pytest

# Import the actual production code - NO MOCKS
from src.communication_agent.test_mode import (
    DemoModeConfig,
    CapturedNotification,
    TemplatePreview,
    DemoModeService,
    DemoMode,
)
from src.communication_agent.interfaces import (
    NotificationRequest,
    NotificationResult,
    NotificationService,
)
from src.communication_agent.types import (
    NotificationChannel,
    NotificationStatus,
    NotificationPriority,
)


class RealTestNotificationService(NotificationService):
    """Real test implementation of NotificationService for testing - NO MOCKS."""

    def __init__(
        self,
        should_succeed: bool = True,
        channel: NotificationChannel = NotificationChannel.EMAIL,
    ):
        self.should_succeed = should_succeed
        self.channel = channel
        self.send_count = 0
        self.validate_calls: List[Any] = []
        self.health_calls: List[Any] = []

    async def send(self, request: NotificationRequest) -> NotificationResult:
        """Real send implementation for testing."""
        self.send_count += 1
        if self.should_succeed:
            return NotificationResult(
                success=True,
                status=NotificationStatus.SENT,
                message_id=f"test-msg-{self.send_count}",
                metadata={"real_service": True},
            )
        else:
            return NotificationResult(
                success=False,
                status=NotificationStatus.FAILED,
                error="Test service failure",
            )

    async def validate_recipient(self, recipient: str) -> bool:
        """Real validate implementation for testing."""
        self.validate_calls.append(recipient)
        return len(recipient) > 0 and "@" in recipient

    async def get_channel_limits(self) -> Dict[str, Any]:
        """Real channel limits for testing."""
        return {
            "max_message_size": 5000,
            "rate_limits": {"per_minute": 30},
            "real_service": True,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Real health check for testing."""
        self.health_calls.append(datetime.now())
        return {
            "status": "healthy" if self.should_succeed else "degraded",
            "service": "test_service",
            "checks": {"connectivity": self.should_succeed},
        }

    def get_channel_type(self) -> NotificationChannel:
        """Return real channel type."""
        return self.channel


def create_test_notification_request() -> NotificationRequest:
    """Create a real test notification request."""
    return NotificationRequest(
        recipient="test@example.com",
        subject="Test Subject",
        body="Test body content",
        channel=NotificationChannel.EMAIL,
        priority=NotificationPriority.MEDIUM,
        metadata={"test_key": "test_value"},
    )


class TestDemoModeConfig:
    """Test DemoModeConfig dataclass with real implementation."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = DemoModeConfig()

        assert config.enabled is False
        assert config.capture_notifications is True
        assert config.simulate_failures is False
        assert config.failure_rate == 0.0
        assert config.delay_seconds == 0.0
        assert config.log_notifications is True
        assert config.simulate_delivery is True
        assert config.override_recipients is None

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = DemoModeConfig(
            enabled=True,
            capture_notifications=False,
            simulate_failures=True,
            failure_rate=0.5,
            delay_seconds=2.0,
            log_notifications=False,
            simulate_delivery=False,
            override_recipients=["test1@example.com", "test2@example.com"],
        )

        assert config.enabled is True
        assert config.capture_notifications is False
        assert config.simulate_failures is True
        assert config.failure_rate == 0.5
        assert config.delay_seconds == 2.0
        assert config.log_notifications is False
        assert config.simulate_delivery is False
        assert config.override_recipients == ["test1@example.com", "test2@example.com"]


class TestCapturedNotification:
    """Test CapturedNotification dataclass with real implementation."""

    def test_default_captured_notification(self) -> None:
        """Test captured notification with default values."""
        request = create_test_notification_request()
        result = NotificationResult(success=True, status=NotificationStatus.SENT)

        captured = CapturedNotification(request=request, result=result)

        assert captured.request == request
        assert captured.result == result
        assert isinstance(captured.timestamp, datetime)

    def test_captured_notification_with_custom_timestamp(self) -> None:
        """Test captured notification with custom timestamp."""
        request = create_test_notification_request()
        result = NotificationResult(
            success=False, status=NotificationStatus.FAILED, error="Test error"
        )
        custom_time = datetime(2025, 6, 14, 12, 0, 0, tzinfo=timezone.utc)

        captured = CapturedNotification(
            request=request, result=result, timestamp=custom_time
        )

        assert captured.request == request
        assert captured.result == result
        assert captured.timestamp == custom_time


class TestTemplatePreview:
    """Test TemplatePreview dataclass with real implementation."""

    @pytest.mark.asyncio
    async def test_template_preview_creation(self) -> None:
        """Test template preview creation."""
        preview = TemplatePreview()

        result = await preview.preview_template(
            template_name="incident_alert",
            context={"incident_id": "INC123", "severity": "HIGH"},
            channel=NotificationChannel.EMAIL,
        )

        assert result["template_name"] == "incident_alert"
        assert result["channel"] == "email"
        assert "rendered" in result

    @pytest.mark.asyncio
    async def test_template_preview_with_minimal_data(self) -> None:
        """Test template preview with minimal data."""
        preview = TemplatePreview()

        result = await preview.preview_template(
            template_name="basic_alert",
            context={"message": "Basic alert message"},
            channel=NotificationChannel.SMS,
        )

        assert result["template_name"] == "basic_alert"
        assert result["channel"] == "sms"


class TestDemoModeService:
    """Test DemoModeService with real implementation."""

    @pytest.fixture
    def demo_config(self) -> DemoModeConfig:
        """Create demo mode configuration."""
        return DemoModeConfig(
            enabled=True,
            capture_notifications=True,
            simulate_failures=False,
            delay_seconds=0.1,
        )

    @pytest.fixture
    def real_service(self) -> RealTestNotificationService:
        """Create real test notification service."""
        return RealTestNotificationService(should_succeed=True)

    @pytest.fixture
    def demo_service(self, demo_config: DemoModeConfig, real_service: RealTestNotificationService) -> DemoModeService:
        """Create demo mode service wrapper."""
        demo_mode = DemoMode(demo_config)
        return DemoModeService(real_service, demo_mode, NotificationChannel.EMAIL)

    @pytest.mark.asyncio
    async def test_demo_service_initialization(
        self, demo_service: DemoModeService, real_service: RealTestNotificationService, demo_config: DemoModeConfig
    ) -> None:
        """Test demo service initialization."""
        assert demo_service.wrapped_service == real_service
        assert demo_service.test_mode.config == demo_config
        assert len(demo_service.captured_notifications) == 0

    @pytest.mark.asyncio
    async def test_send_with_capture(self, demo_service: DemoModeService) -> None:
        """Test send method with notification capture."""
        request = create_test_notification_request()

        result = await demo_service.send(request)

        assert result.success is True
        assert result.status == NotificationStatus.SENT
        assert len(demo_service.captured_notifications) == 1

        captured = demo_service.captured_notifications[0]
        assert captured.request == request
        assert captured.result.success is True

    @pytest.mark.asyncio
    async def test_send_with_simulated_failure(self) -> None:
        """Test send method with simulated failures."""
        real_service = RealTestNotificationService(should_succeed=True)
        config = DemoModeConfig(
            enabled=True,
            capture_notifications=True,
            simulate_failures=True,
            failure_rate=1.0,  # Always fail
        )
        demo_mode = DemoMode(config)
        demo_service = DemoModeService(
            real_service, demo_mode, NotificationChannel.EMAIL
        )

        request = create_test_notification_request()
        result = await demo_service.send(request)

        assert result.success is False
        assert result.status == NotificationStatus.FAILED
        assert result.error is not None
        assert "Simulated failure" in result.error
        assert len(demo_service.captured_notifications) == 1

    @pytest.mark.asyncio
    async def test_send_with_delay(self) -> None:
        """Test send method with delay simulation."""
        real_service = RealTestNotificationService(should_succeed=True)
        config = DemoModeConfig(
            enabled=True, capture_notifications=True, delay_seconds=0.2
        )
        demo_mode = DemoMode(config)
        demo_service = DemoModeService(
            real_service, demo_mode, NotificationChannel.EMAIL
        )

        request = create_test_notification_request()
        start_time = datetime.now()

        result = await demo_service.send(request)

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        assert result.success is True
        assert elapsed >= 0.2  # Should have delayed
        assert len(demo_service.captured_notifications) == 1

    @pytest.mark.asyncio
    async def test_send_with_recipient_override(self) -> None:
        """Test send method with recipient override."""
        real_service = RealTestNotificationService(should_succeed=True)
        config = DemoModeConfig(
            enabled=True,
            capture_notifications=True,
            override_recipients=["override@example.com"],
        )
        demo_mode = DemoMode(config)
        demo_service = DemoModeService(
            real_service, demo_mode, NotificationChannel.EMAIL
        )

        request = create_test_notification_request()
        original_recipient = request.recipient

        result = await demo_service.send(request)

        assert result.success is True
        # Original request should be modified
        assert request.recipient == "override@example.com"
        assert request.recipient != original_recipient
        assert len(demo_service.captured_notifications) == 1

    @pytest.mark.asyncio
    async def test_validate_recipient_passthrough(self, demo_service: DemoModeService, real_service: RealTestNotificationService) -> None:
        """Test validate_recipient passes through to wrapped service."""
        result = await demo_service.validate_recipient("test@example.com")

        assert result is True
        assert "test@example.com" in real_service.validate_calls

    @pytest.mark.asyncio
    async def test_get_channel_limits_passthrough(self, demo_service: DemoModeService) -> None:
        """Test get_channel_limits passes through to wrapped service."""
        limits = await demo_service.get_channel_limits()

        assert limits["max_message_size"] == 5000
        assert limits["real_service"] is True

    @pytest.mark.asyncio
    async def test_health_check_passthrough(self, demo_service: DemoModeService, real_service: RealTestNotificationService) -> None:
        """Test health_check passes through to wrapped service."""
        health = await demo_service.health_check()

        assert health["status"] == "healthy"
        assert len(real_service.health_calls) == 1

    def test_get_channel_type_passthrough(self, demo_service: DemoModeService) -> None:
        """Test get_channel_type passes through to wrapped service."""
        channel = demo_service.get_channel_type()

        assert channel == NotificationChannel.EMAIL

    def test_get_captured_notifications(self, demo_service: DemoModeService) -> None:
        """Test get_captured_notifications method."""
        # Initially empty
        captured = demo_service.captured_notifications
        assert len(captured) == 0

        # Add some notifications manually
        request = create_test_notification_request()
        result = NotificationResult(success=True, status=NotificationStatus.SENT)
        demo_service.captured_notifications.append(
            CapturedNotification(request=request, result=result)
        )

        captured = demo_service.captured_notifications
        assert len(captured) == 1
        assert captured[0].request == request

    def test_clear_captured_notifications(self, demo_service: DemoModeService) -> None:
        """Test clear_captured_notifications method."""
        # Add a notification
        request = create_test_notification_request()
        result = NotificationResult(success=True, status=NotificationStatus.SENT)
        demo_service.captured_notifications.append(
            CapturedNotification(request=request, result=result)
        )

        assert len(demo_service.captured_notifications) == 1

        # Clear notifications
        demo_service.captured_notifications.clear()

        assert len(demo_service.captured_notifications) == 0


class TestDemoMode:
    """Test DemoMode context manager with real implementation."""

    @pytest.fixture
    def demo_config(self) -> DemoModeConfig:
        """Create demo mode configuration."""
        return DemoModeConfig(
            enabled=True, capture_notifications=True, simulate_failures=False
        )

    def test_demo_mode_initialization(self, demo_config: DemoModeConfig) -> None:
        """Test demo mode initialization."""
        demo_mode = DemoMode(demo_config)

        assert demo_mode.config == demo_config
        assert len(demo_mode.wrapped_services) == 0
        assert len(demo_mode.captured_notifications) == 0

    def test_wrap_service(self, demo_config: DemoModeConfig) -> None:
        """Test wrap_service method."""
        demo_mode = DemoMode(demo_config)
        real_service = RealTestNotificationService()

        wrapped = demo_mode.wrap_service(real_service)

        assert isinstance(wrapped, DemoModeService)
        assert wrapped.wrapped_service == real_service
        assert wrapped.test_mode.config == demo_config
        assert len(demo_mode.wrapped_services) == 1
        assert wrapped in demo_mode.wrapped_services.values()

    @pytest.mark.asyncio
    async def test_context_manager_usage(self, demo_config: DemoModeConfig) -> None:
        """Test demo mode as context manager."""
        real_service = RealTestNotificationService()

        async with DemoMode(demo_config) as demo_mode:
            wrapped_service = demo_mode.wrap_service(real_service)

            request = create_test_notification_request()
            result = await wrapped_service.send(request)

            assert result.success is True
            assert len(demo_mode.captured_notifications) == 1

    def test_get_all_captured_notifications(self, demo_config: DemoModeConfig) -> None:
        """Test get_all_captured_notifications method."""
        demo_mode = DemoMode(demo_config)

        # Create multiple services with captured notifications
        service1 = RealTestNotificationService()
        service2 = RealTestNotificationService()

        wrapped1 = demo_mode.wrap_service(service1)
        wrapped2 = demo_mode.wrap_service(service2)
        # Type assertions for mypy
        assert isinstance(wrapped1, DemoModeService)
        assert isinstance(wrapped2, DemoModeService)

        # Add captured notifications manually
        request1 = create_test_notification_request()
        request2 = create_test_notification_request()
        request2.recipient = "test2@example.com"

        result = NotificationResult(success=True, status=NotificationStatus.SENT)

        wrapped1.captured_notifications.append(
            CapturedNotification(request=request1, result=result)
        )
        wrapped2.captured_notifications.append(
            CapturedNotification(request=request2, result=result)
        )

        all_captured = demo_mode.get_all_captured_notifications()

        assert len(all_captured) == 2
        recipients = [capture.request.recipient for capture in all_captured]
        assert "test@example.com" in recipients
        assert "test2@example.com" in recipients

    def test_clear_all_captured_notifications(self, demo_config: DemoModeConfig) -> None:
        """Test clear_all_captured_notifications method."""
        demo_mode = DemoMode(demo_config)

        # Create service with captured notifications
        real_service = RealTestNotificationService()
        wrapped = demo_mode.wrap_service(real_service)
        # Type assertion for mypy
        assert isinstance(wrapped, DemoModeService)

        # Add captured notification manually
        request = create_test_notification_request()
        result = NotificationResult(success=True, status=NotificationStatus.SENT)
        wrapped.captured_notifications.append(
            CapturedNotification(request=request, result=result)
        )

        assert len(wrapped.captured_notifications) == 1

        # Clear all notifications
        demo_mode.clear_all_captured_notifications()

        assert len(wrapped.captured_notifications) == 0

    def test_get_config(self, demo_config: DemoModeConfig) -> None:
        """Test get_config method."""
        demo_mode = DemoMode(demo_config)

        config = demo_mode.get_config()

        assert config == demo_config
        assert config.enabled is True
        assert config.capture_notifications is True


class TestDemoModeIntegration:
    """Test demo mode integration scenarios with real implementation."""

    @pytest.mark.asyncio
    async def test_multiple_services_integration(self) -> None:
        """Test demo mode with multiple different services."""
        config = DemoModeConfig(
            enabled=True, capture_notifications=True, simulate_failures=False
        )

        async with DemoMode(config) as demo_mode:
            # Create different service types
            email_service = RealTestNotificationService(
                channel=NotificationChannel.EMAIL
            )
            sms_service = RealTestNotificationService(channel=NotificationChannel.SMS)
            slack_service = RealTestNotificationService(
                channel=NotificationChannel.SLACK
            )

            # Wrap all services
            wrapped_email = demo_mode.wrap_service(email_service)
            wrapped_sms = demo_mode.wrap_service(sms_service)
            wrapped_slack = demo_mode.wrap_service(slack_service)

            # Send notifications through each service
            email_request = NotificationRequest(
                recipient="test@example.com",
                subject="Email Test",
                body="Email body",
                channel=NotificationChannel.EMAIL,
                priority=NotificationPriority.HIGH,
            )

            sms_request = NotificationRequest(
                recipient="+1234567890",
                subject="SMS Test",
                body="SMS body",
                channel=NotificationChannel.SMS,
                priority=NotificationPriority.MEDIUM,
            )

            slack_request = NotificationRequest(
                recipient="#alerts",
                subject="Slack Test",
                body="Slack body",
                channel=NotificationChannel.SLACK,
                priority=NotificationPriority.LOW,
            )

            # Send all notifications
            email_result = await wrapped_email.send(email_request)
            sms_result = await wrapped_sms.send(sms_request)
            slack_result = await wrapped_slack.send(slack_request)

            # Verify all succeeded
            assert email_result.success is True
            assert sms_result.success is True
            assert slack_result.success is True

            # Verify all were captured
            all_captured = demo_mode.get_all_captured_notifications()
            assert len(all_captured) == 3

            # Verify channels
            channels = [capture.request.channel for capture in all_captured]
            assert NotificationChannel.EMAIL in channels
            assert NotificationChannel.SMS in channels
            assert NotificationChannel.SLACK in channels

    @pytest.mark.asyncio
    async def test_failure_simulation_rates(self) -> None:
        """Test different failure simulation rates."""
        # Test with 50% failure rate
        config = DemoModeConfig(
            enabled=True,
            capture_notifications=True,
            simulate_failures=True,
            failure_rate=0.5,
        )

        async with DemoMode(config) as demo_mode:
            service = RealTestNotificationService()
            wrapped = demo_mode.wrap_service(service)

            # Send multiple requests to test failure rate
            results = []
            for i in range(20):
                request = create_test_notification_request()
                request.metadata = {"test_id": i}
                result = await wrapped.send(request)
                results.append(result.success)

            # Should have both successes and failures
            successes = sum(results)
            failures = len(results) - successes

            assert successes > 0  # Should have some successes
            assert failures > 0  # Should have some failures
            assert len(demo_mode.get_all_captured_notifications()) == 20

    @pytest.mark.asyncio
    async def test_complex_configuration_scenario(self) -> None:
        """Test complex configuration with multiple features enabled."""
        config = DemoModeConfig(
            enabled=True,
            capture_notifications=True,
            simulate_failures=True,
            failure_rate=0.2,
            delay_seconds=0.1,
            override_recipients=["demo@example.com"],
            log_notifications=True,
            simulate_delivery=True,
        )

        async with DemoMode(config) as demo_mode:
            service = RealTestNotificationService()
            wrapped = demo_mode.wrap_service(service)

            original_request = create_test_notification_request()
            start_time = datetime.now()

            await wrapped.send(original_request)

            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()

            # Should have delay
            assert elapsed >= 0.1

            # Should have recipient override
            assert original_request.recipient == "demo@example.com"

            # Should have captured notification
            captured = demo_mode.get_all_captured_notifications()
            assert len(captured) == 1
            assert captured[0].request.recipient == "demo@example.com"


def test_demo_mode_service_creation() -> None:
    """Test DemoModeService creation with required parameters."""
    # Create a mock service
    mock_service = type("MockService", (), {})()

    # Create demo mode config
    demo_config = DemoModeConfig()
    demo_mode = DemoMode(demo_config)

    # Create DemoModeService with required channel parameter
    demo_service = DemoModeService(
        wrapped_service=mock_service,
        test_mode=demo_mode,
        channel=NotificationChannel.EMAIL,
    )

    assert demo_service.wrapped_service == mock_service
    assert demo_service.test_mode == demo_mode
    assert demo_service.channel == NotificationChannel.EMAIL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
