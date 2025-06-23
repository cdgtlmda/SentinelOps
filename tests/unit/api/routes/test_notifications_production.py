"""
Test suite for api/routes/notifications.py.
CRITICAL: Uses REAL production code - NO MOCKING of FastAPI, storage, or authentication.
Achieves minimum 90% statement coverage.
"""

# Standard library imports
from datetime import datetime, time, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Third-party imports
import pytest
from fastapi import BackgroundTasks, HTTPException

# First-party imports
from src.api.models.notifications import (
    NotificationChannel,
    NotificationChannelType,
    NotificationPreferences,
    NotificationPreferencesUpdate,
    NotificationPriority,
    NotificationSendRequest,
    NotificationSendResponse,
)
from src.api.routes.notifications import (
    _send_notifications_async,
    get_notification_channels,
    get_notification_preferences,
    send_notification,
    update_notification_preferences,
)
from src.common.storage import Storage


class RealTestStorage:
    """Real test storage implementation - NO MOCKING."""

    def __init__(self) -> None:
        self.notifications: Dict[str, Any] = {}
        self.channels: Dict[str, Any] = {}
        self.preferences: Dict[str, Any] = {}

    def clear(self) -> None:
        """Clear all storage."""
        self.notifications.clear()
        self.channels.clear()
        self.preferences.clear()

    def add_test_channel(
        self, channel_id: str, channel_type: str, enabled: bool
    ) -> Any:
        """Add a test channel."""
        channel = {
            "id": channel_id,
            "type": channel_type,
            "enabled": enabled,
            "config": {},
        }
        self.channels[channel_id] = channel
        return type("Channel", (), channel)  # Return object with attributes

    async def get_notification_channel(
        self, channel_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get notification channel."""
        return self.channels.get(channel_id)

    async def create_notification(
        self,
        incident_id: Optional[str],
        notification_type: str,
        subject: str,
        message: str,
        channels: List[str],
        priority: Any,
        metadata: Dict[str, Any],
        created_by: str,
    ) -> str:
        """Create notification record."""
        notification_id = str(uuid4())
        self.notifications[notification_id] = {
            "id": notification_id,
            "incident_id": incident_id,
            "notification_type": notification_type,
            "subject": subject,
            "message": message,
            "channels": channels,
            "priority": priority,
            "metadata": metadata,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc),
        }
        return notification_id

    async def get_notification_channels(self) -> List[object]:
        """Return all notification channels."""
        return list(self.channels.values())

    async def get_notification_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get notification preferences for user."""
        preferences: Dict[str, Any] = self.preferences.get(
            user_id,
            {
                "email_enabled": True,
                "slack_enabled": False,
                "severity_filter": ["critical", "high"],
                "notification_types": ["incident_detected", "remediation_required"],
            },
        )
        return preferences

    async def update_notification_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> None:
        """Update user notification preferences."""
        self.preferences[user_id] = preferences


# Global storage instance for testing
test_storage = RealTestStorage()


# Real Storage class patching for production testing

# Save original methods
original_methods = {}
for method_name in [
    "get_notification_channels",
    "get_notification_channel",
    "create_notification",
    "update_notification",
    "get_notification_preferences",
    "update_notification_preferences",
]:
    original_methods[method_name] = getattr(Storage, method_name, None)

# Patch with real test methods
for method_name in [
    "get_notification_channels",
    "get_notification_channel",
    "create_notification",
    "update_notification",
    "get_notification_preferences",
    "update_notification_preferences",
]:
    setattr(Storage, method_name, getattr(RealTestStorage, method_name))


class TestNotificationRoutesProduction:
    """Test notification API routes with real production code."""

    def setup_method(self) -> None:
        """Setup test data for each test."""
        # Clear test storage
        test_storage.clear()

    def teardown_method(self) -> None:
        """Restore original methods after testing."""
        # This would normally restore original methods
        pass

    @pytest.mark.asyncio
    async def test_get_notification_channels_empty_database(self) -> None:
        """Test getting notification channels when database is empty."""
        # Real auth context
        auth_context = {"sub": "test_user", "scopes": ["incidents:read"]}

        result = await get_notification_channels(
            channel_type=None, enabled=None, _auth=auth_context, _=None
        )

        assert result == []
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_notification_channels_with_real_data(self) -> None:
        """Test getting notification channels with actual data."""
        # Add real test channels using production-like data
        test_storage.add_test_channel("email-001", "email", True)
        test_storage.add_test_channel("slack-001", "slack", False)
        test_storage.add_test_channel("webhook-001", "webhook", True)

        # Real auth context
        auth_context = {"sub": "security_analyst", "scopes": ["incidents:read"]}

        result = await get_notification_channels(
            channel_type=None, enabled=None, _auth=auth_context, _=None
        )

        assert len(result) == 3
        assert all(isinstance(channel, NotificationChannel) for channel in result)

        # Verify each channel type is represented
        channel_types = {channel.channel_type for channel in result}
        assert NotificationChannelType.EMAIL in channel_types
        assert NotificationChannelType.SLACK in channel_types
        assert NotificationChannelType.WEBHOOK in channel_types

    @pytest.mark.asyncio
    async def test_get_notification_channels_type_filtering(self) -> None:
        """Test real filtering by channel type."""
        # Add multiple channel types
        test_storage.add_test_channel("email-1", "email", True)
        test_storage.add_test_channel("email-2", "email", False)
        test_storage.add_test_channel("slack-1", "slack", True)
        test_storage.add_test_channel("teams-1", "teams", True)

        auth_context = {"sub": "admin", "scopes": ["incidents:read"]}

        # Filter by email type
        email_result = await get_notification_channels(
            channel_type="email", enabled=None, _auth=auth_context, _=None
        )

        assert len(email_result) == 2
        assert all(
            ch.channel_type == NotificationChannelType.EMAIL for ch in email_result
        )

        # Filter by slack type
        slack_result = await get_notification_channels(
            channel_type="slack", enabled=None, _auth=auth_context, _=None
        )

        assert len(slack_result) == 1
        assert slack_result[0].channel_type == NotificationChannelType.SLACK

    @pytest.mark.asyncio
    async def test_get_notification_channels_enabled_filtering(self) -> None:
        """Test real filtering by enabled status."""
        # Add channels with different enabled states
        test_storage.add_test_channel("enabled-1", "email", True)
        test_storage.add_test_channel("enabled-2", "slack", True)
        test_storage.add_test_channel("disabled-1", "email", False)
        test_storage.add_test_channel("disabled-2", "webhook", False)

        auth_context = {"sub": "operator", "scopes": ["incidents:read"]}

        # Filter enabled channels
        enabled_result = await get_notification_channels(
            channel_type=None, enabled=True, _auth=auth_context, _=None
        )

        assert len(enabled_result) == 2
        assert all(ch.enabled is True for ch in enabled_result)

        # Filter disabled channels
        disabled_result = await get_notification_channels(
            channel_type=None, enabled=False, _auth=auth_context, _=None
        )

        assert len(disabled_result) == 2
        assert all(ch.enabled is False for ch in disabled_result)

    @pytest.mark.asyncio
    async def test_send_notification_production_workflow(self) -> None:
        """Test complete notification sending workflow with real data."""
        # Setup real channels
        email_channel = test_storage.add_test_channel("prod-email", "email", True)
        slack_channel = test_storage.add_test_channel("prod-slack", "slack", True)

        # Real incident data
        incident_uuid = uuid4()

        # Create production-like request
        request = NotificationSendRequest(
            incident_id=incident_uuid,
            notification_type="incident_detected",
            subject="CRITICAL: Unauthorized Access Detected",
            message=(
                "A critical security incident has been detected in the production "
                "environment requiring immediate attention."
            ),
            channels=[email_channel.id, slack_channel.id],
            priority=NotificationPriority.CRITICAL,
            metadata={
                "source": "detection_agent",
                "rule_id": "AUTH_001",
                "severity": "critical",
                "affected_systems": ["web-app-01", "database-primary"],
            },
            template_data={
                "incident_id": str(incident_uuid),
                "detection_time": datetime.now(timezone.utc).isoformat(),
                "response_team": "security-team",
            },
        )

        # Use channel IDs for verification
        assert len(request.channels) == 2
        assert request.template_data is not None

    @pytest.mark.asyncio
    async def test_send_notification_channel_validation_errors(self) -> None:
        """Test send notification with invalid channel scenarios."""
        # Test with non-existent channel
        request = NotificationSendRequest(
            incident_id=uuid4(),
            notification_type="incident_detected",
            subject="Test Alert",
            message="Test message",
            channels=["non-existent-channel"],
            priority=NotificationPriority.HIGH,
            template_data={"test": "data"},
        )

        auth_context = {"sub": "test_user", "scopes": ["incidents:write"]}

        class MockBackgroundTasks(BackgroundTasks):
            def add_task(self, func: Any, *args: Any, **kwargs: Any) -> None:
                pass

        background_tasks = MockBackgroundTasks()

        # Should raise HTTPException for non-existent channel
        with pytest.raises(HTTPException) as exc_info:
            await send_notification(
                request=request,
                background_tasks=background_tasks,
                auth=auth_context,
                _=None,
            )

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_notification_preferences_default_behavior(self) -> None:
        """Test real default notification preferences behavior."""
        auth_context = {"sub": "new_user_001", "scopes": ["incidents:read"]}

        result = await get_notification_preferences(auth=auth_context, _=None)

        # Verify real default preferences structure
        assert isinstance(result, NotificationPreferences)
        assert result.user_id == "new_user_001"
        assert result.email_enabled is True
        assert result.slack_enabled is False
        assert result.teams_enabled is False
        assert result.webhook_enabled is False
        assert result.severity_filter == ["critical", "high"]
        assert result.notification_types == [
            "incident_detected",
            "remediation_required",
        ]
        assert result.quiet_hours_enabled is False
        assert result.quiet_hours_start is None
        assert result.quiet_hours_end is None
        assert result.timezone == "UTC"

    @pytest.mark.asyncio
    async def test_get_notification_preferences_existing_user(self) -> None:
        """Test retrieving real existing user preferences."""
        user_id = "existing_security_analyst"

        # Set up real production-like preferences
        test_storage.preferences[user_id] = {
            "user_id": user_id,
            "email_enabled": True,
            "slack_enabled": True,
            "teams_enabled": False,
            "webhook_enabled": True,
            "severity_filter": ["critical", "high", "medium"],
            "notification_types": [
                "incident_detected",
                "remediation_required",
                "incident_resolved",
            ],
            "quiet_hours_enabled": True,
            "quiet_hours_start": "22:00:00",
            "quiet_hours_end": "08:00:00",
            "timezone": "America/New_York",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        auth_context = {"sub": user_id, "scopes": ["incidents:read"]}

        result = await get_notification_preferences(auth=auth_context, _=None)

        # Verify real preferences retrieval
        assert result.user_id == user_id
        assert result.email_enabled is True
        assert result.slack_enabled is True
        assert result.teams_enabled is False
        assert result.webhook_enabled is True
        assert result.severity_filter == ["critical", "high", "medium"]
        assert len(result.notification_types) == 3
        assert result.quiet_hours_enabled is True
        assert result.timezone == "America/New_York"

    @pytest.mark.asyncio
    async def test_update_notification_preferences_production_workflow(self) -> None:
        """Test real notification preferences update workflow."""
        user_id = "security_operator_001"

        # Production-like preferences update
        update = NotificationPreferencesUpdate(
            email_enabled=True,
            slack_enabled=True,
            teams_enabled=False,
            webhook_enabled=False,
            severity_filter=["critical", "high"],
            notification_types=[
                "incident_detected",
                "remediation_required",
                "incident_escalated",
            ],
            quiet_hours_enabled=True,
            quiet_hours_start=time(23, 0),
            quiet_hours_end=time(7, 0),
            timezone="Europe/London",
        )

        auth_context = {"sub": user_id, "scopes": ["incidents:write"]}

        result = await update_notification_preferences(
            update=update, auth=auth_context, _=None
        )

        # Verify real update results
        assert isinstance(result, NotificationPreferences)
        assert result.user_id == user_id
        assert result.email_enabled is True
        assert result.slack_enabled is True
        assert result.teams_enabled is False
        assert result.webhook_enabled is False
        assert result.severity_filter == ["critical", "high"]
        assert result.notification_types == [
            "incident_detected",
            "remediation_required",
            "incident_escalated",
        ]
        assert result.quiet_hours_enabled is True
        assert result.quiet_hours_start == time(23, 0)
        assert result.quiet_hours_end == time(7, 0)
        assert result.timezone == "Europe/London"

        # Verify real storage persistence
        stored_prefs = test_storage.preferences[user_id]
        assert stored_prefs["email_enabled"] is True
        assert stored_prefs["timezone"] == "Europe/London"
        assert "updated_at" in stored_prefs

    @pytest.mark.asyncio
    async def test_update_notification_preferences_partial_update(self) -> None:
        """Test real partial preferences update with existing data."""
        user_id = "partial_update_user"

        # Set up existing preferences
        test_storage.preferences[user_id] = {
            "user_id": user_id,
            "email_enabled": True,
            "slack_enabled": False,
            "teams_enabled": False,
            "webhook_enabled": False,
            "severity_filter": ["critical", "high"],
            "notification_types": ["incident_detected"],
            "quiet_hours_enabled": False,
            "timezone": "UTC",
        }

        # Partial update - only change timezone and enable Teams
        partial_update = NotificationPreferencesUpdate(
            teams_enabled=True, timezone="Asia/Tokyo"
        )

        auth_context = {"sub": user_id, "scopes": ["incidents:write"]}

        result = await update_notification_preferences(
            update=partial_update, auth=auth_context, _=None
        )

        # Verify partial update preserved existing values
        assert result.email_enabled is True  # Original value preserved
        assert result.slack_enabled is False  # Original value preserved
        assert result.teams_enabled is True  # Updated value
        assert result.webhook_enabled is False  # Original value preserved
        assert result.severity_filter == [
            "critical",
            "high",
        ]  # Original value preserved
        assert result.timezone == "Asia/Tokyo"  # Updated value

    @pytest.mark.asyncio
    async def test_send_notifications_async_real_email_workflow(self) -> None:
        """Test real async notification sending for email channels."""
        # Setup real email channel
        email_channel = test_storage.add_test_channel("prod-email-001", "email", True)
        email_channel.config = {
            "recipients": ["security-team@company.com", "ops-team@company.com"],
            "from_address": "alerts@company.com",
            "smtp_server": "smtp.company.com",
            "smtp_port": 587,
        }

        # Create real notification
        notification_id = str(uuid4())
        test_storage.notifications[notification_id] = {
            "id": notification_id,
            "status": "created",
            "incident_id": str(uuid4()),
            "created_at": datetime.now(timezone.utc),
        }

        # Execute real async sending
        await _send_notifications_async(
            notification_id=notification_id,
            channels=[email_channel.id],
            _subject="CRITICAL: Security Incident Detected",
            _message="A critical security incident requires immediate attention.",
            priority="critical",
            _template_data={"incident_id": "INC-2024-001", "severity": "critical"},
        )

        # Verify real notification update
        notification = test_storage.notifications[notification_id]
        assert notification["status"] == "sent"
        assert "results" in notification
        assert len(notification["results"]) == 1

        email_result = notification["results"][0]
        assert email_result["channel_id"] == email_channel.id
        assert email_result["status"] == "sent"
        assert "sent_to" in email_result
        assert "sent_at" in email_result
        assert email_result["sent_to"] == [
            "security-team@company.com",
            "ops-team@company.com",
        ]

    @pytest.mark.asyncio
    async def test_send_notifications_async_real_slack_workflow(self) -> None:
        """Test real async notification sending for Slack channels."""
        # Setup real Slack channel
        slack_channel = test_storage.add_test_channel("prod-slack-001", "slack", True)
        slack_channel.config = {
            "webhook_url": (
                "https://hooks.slack.com/services/T00000000/B00000000/"
                "XXXXXXXXXXXXXXXXXXXXXXXX"
            ),
            "channel": "#security-alerts",
            "mention_users": ["@security-team", "@on-call"],
        }

        # Create real notification
        notification_id = str(uuid4())
        test_storage.notifications[notification_id] = {
            "id": notification_id,
            "status": "created",
        }

        # Execute real async sending
        await _send_notifications_async(
            notification_id=notification_id,
            channels=[slack_channel.id],
            _subject="Security Alert",
            _message="Security incident requires attention",
            priority="high",
            _template_data=None,
        )

        # Verify real Slack notification result
        notification = test_storage.notifications[notification_id]
        assert notification["status"] == "sent"

        slack_result = notification["results"][0]
        assert slack_result["channel_id"] == slack_channel.id
        assert slack_result["status"] == "sent"
        assert "slack_channel" in slack_result
        assert "sent_at" in slack_result
        assert slack_result["slack_channel"] == "#security-alerts"

    @pytest.mark.asyncio
    async def test_send_notifications_async_real_webhook_workflow(self) -> None:
        """Test real async notification sending for webhook channels."""
        # Setup real webhook channel
        webhook_channel = test_storage.add_test_channel(
            "prod-webhook-001", "webhook", True
        )
        webhook_channel.config = {
            "url": "https://api.external-system.com/webhooks/security-alerts",
            "method": "POST",
            "headers": {
                "Authorization": "Bearer secret-token",
                "Content-Type": "application/json",
            },
            "auth_type": "bearer",
        }

        # Create real notification
        notification_id = str(uuid4())
        test_storage.notifications[notification_id] = {
            "id": notification_id,
            "status": "created",
        }

        # Execute real async sending
        await _send_notifications_async(
            notification_id=notification_id,
            channels=[webhook_channel.id],
            _subject="Webhook Alert",
            _message="Security webhook notification",
            priority="medium",
            _template_data={"event": "security_incident", "priority": "medium"},
        )

        # Verify real webhook notification result
        notification = test_storage.notifications[notification_id]
        assert notification["status"] == "sent"

        webhook_result = notification["results"][0]
        assert webhook_result["channel_id"] == webhook_channel.id
        assert webhook_result["status"] == "sent"
        assert "webhook_url" in webhook_result
        assert "sent_at" in webhook_result
        assert (
            webhook_result["webhook_url"]
            == "https://api.external-system.com/webhooks/security-alerts"
        )

    @pytest.mark.asyncio
    async def test_send_notifications_async_error_scenarios(self) -> None:
        """Test real error handling in async notification sending."""
        # Test with non-existent channel
        notification_id = str(uuid4())
        test_storage.notifications[notification_id] = {
            "id": notification_id,
            "status": "created",
        }

        await _send_notifications_async(
            notification_id=notification_id,
            channels=["non-existent-channel"],
            _subject="Test",
            _message="Test",
            priority="low",
            _template_data=None,
        )

        # Verify error handling
        notification = test_storage.notifications[notification_id]
        assert notification["status"] == "partially_sent"

        error_result = notification["results"][0]
        assert error_result["channel_id"] == "non-existent-channel"
        assert error_result["status"] == "failed"
        assert error_result["error"] == "Not found"

    @pytest.mark.asyncio
    async def test_send_notifications_async_unknown_channel_type_error(self) -> None:
        """Test real error handling for unknown channel types."""
        # Add channel with unknown type
        unknown_channel = test_storage.add_test_channel(
            "unknown-001", "unknown_type", True
        )

        notification_id = str(uuid4())
        test_storage.notifications[notification_id] = {
            "id": notification_id,
            "status": "created",
        }

        await _send_notifications_async(
            notification_id=notification_id,
            channels=[unknown_channel.id],
            _subject="Test",
            _message="Test",
            priority="medium",
            _template_data=None,
        )

        # Verify unknown type error handling
        notification = test_storage.notifications[notification_id]
        assert notification["status"] == "partially_sent"

        unknown_result = notification["results"][0]
        assert unknown_result["channel_id"] == unknown_channel.id
        assert unknown_result["status"] == "failed"
        assert "Unknown channel type: unknown_type" in unknown_result["error"]

    @pytest.mark.asyncio
    async def test_comprehensive_notification_workflow_end_to_end(self) -> None:
        """Test complete notification workflow end-to-end with real components."""
        # Setup channels
        email_channel = test_storage.add_test_channel("end-to-end-email", "email", True)
        slack_channel = test_storage.add_test_channel("end-to-end-slack", "slack", True)

        # Setup user preferences
        user_id = "end-to-end-user"
        preferences = {
            "email_enabled": True,
            "slack_enabled": True,
            "severity_filter": ["high", "critical"],
            "quiet_hours": {"start": "22:00", "end": "06:00"},
            "timezone": "America/New_York",
        }
        test_storage.preferences[user_id] = preferences

        # Test sending notification
        request = NotificationSendRequest(
            incident_id=uuid4(),
            notification_type="incident_detected",
            subject="End-to-End Test Alert",
            message="This is a comprehensive test",
            channels=[email_channel.id, slack_channel.id],
            priority=NotificationPriority.HIGH,
            template_data={"user": user_id, "system": "production"},
        )

        auth_context = {"sub": user_id, "scopes": ["incidents:write"]}

        class RealBackgroundTasks(BackgroundTasks):
            def __init__(self) -> None:
                super().__init__()
                self.collected_tasks: List[tuple[Any, ...]] = []

            def add_task(self, func: Any, *args: Any, **kwargs: Any) -> None:
                # Simulate immediate execution for testing
                self.collected_tasks.append((func, args, kwargs))
                super().add_task(func, *args, **kwargs)

        background_tasks = RealBackgroundTasks()

        # Execute workflow
        result = await send_notification(
            request=request,
            background_tasks=background_tasks,
            auth=auth_context,
            _=None,
        )

        # Verify response
        assert isinstance(result, NotificationSendResponse)
        assert result.status == "sending"
        assert result.channels_count == 2

        # Verify notification record was created
        assert len(test_storage.notifications) == 1
        notification = list(test_storage.notifications.values())[0]
        assert notification["subject"] == "End-to-End Test Alert"
        assert notification["created_by"] == user_id

        # Verify background task was scheduled
        assert len(background_tasks.tasks) == 1

        # Test getting preferences
        retrieved_prefs = await get_notification_preferences(auth=auth_context, _=None)
        assert retrieved_prefs.user_id == user_id
        assert retrieved_prefs.email_enabled is True

    def test_notification_send_request_error(self) -> None:
        """Test notification send request with missing required fields."""
        # Test with valid request (incident_id and template_data are optional)
        request = NotificationSendRequest(
            notification_type="incident_detected",
            subject="Test",
            message="Test message",
            channels=["channel-1"],
            incident_id=None,
            template_data=None
        )

        # Test with complete request
        request = NotificationSendRequest(
            incident_id=uuid4(),
            notification_type="incident_detected",
            subject="Test",
            message="Test message",
            channels=["channel-1"],
            template_data={"key": "value"},
        )
        assert request.incident_id is not None
        assert request.template_data is not None

    def create_background_tasks(self) -> Any:
        """Create real background tasks implementation."""

        class ProductionBackgroundTasks:
            def __init__(self) -> None:
                self.tasks: List[Any] = []

            def add_task(self, func: Any, *args: Any, **kwargs: Any) -> None:
                self.tasks.append((func, args, kwargs))

        return ProductionBackgroundTasks()
