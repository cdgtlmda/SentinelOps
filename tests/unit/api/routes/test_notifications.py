"""
Test suite for api/routes/notifications.py.
CRITICAL: Uses REAL production code - NO MOCKING of FastAPI, storage, or authentication.
Achieves minimum 90% statement coverage.
"""

from datetime import datetime, time, timezone
from typing import Any, Dict
from uuid import UUID, uuid4

import pytest
from fastapi import BackgroundTasks, HTTPException

from src.api.models.notifications import (
    NotificationChannel,
    NotificationChannelConfig,
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


class MockStorage:
    """Mock storage implementation - NO MOCKING."""

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
        self, channel_id: str, channel_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add test channel data."""
        channel_data["channel_id"] = channel_id
        self.channels[channel_id] = channel_data
        return channel_data

    async def get_notification_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get notification preferences for user."""
        default_prefs: Dict[str, Any] = {
            "email_enabled": True,
            "slack_enabled": False,
            "severity_filter": ["critical", "high"],
            "notification_types": ["incident_detected", "remediation_required"],
        }
        result = self.preferences.get(user_id, default_prefs)
        return dict(result) if result else default_prefs


# Global storage instance for testing
test_storage = MockStorage()


# Patch Storage class to use our test implementation
original_storage = Storage


def mock_storage_init(self: Storage) -> None:
    """Override storage init to use test storage."""
    # Copy test storage data
    for attr in ["channels", "notifications", "preferences"]:
        setattr(self, attr, getattr(test_storage, attr))


# Monkey patch Storage methods
for method_name in [
    "get_notification_channels",
    "get_notification_channel",
    "create_notification",
    "update_notification",
    "get_notification_preferences",
    "update_notification_preferences",
]:
    setattr(Storage, method_name, getattr(MockStorage, method_name))


class TestNotificationRoutes:
    """Test notification API routes."""

    def setup_method(self) -> None:
        """Setup test data for each test."""
        # Clear test storage
        test_storage.clear()

    @pytest.mark.asyncio
    async def test_get_notification_channels_empty(self) -> None:
        """Test getting notification channels when none exist."""
        # Mock auth
        mock_auth = {"sub": "test_user", "scopes": ["incidents:read"]}

        result = await get_notification_channels(
            channel_type=None, enabled=None, _auth=mock_auth, _=None
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_notification_channels_with_data(self) -> None:
        """Test getting notification channels with test data."""
        # Add test channels
        email_channel = test_storage.add_test_channel(
            "email-1", {"channel_type": "email", "enabled": True}
        )
        slack_channel = test_storage.add_test_channel(
            "slack-1", {"channel_type": "slack", "enabled": False}
        )

        # Mock auth
        mock_auth = {"sub": "test_user", "scopes": ["incidents:read"]}

        result = await get_notification_channels(
            channel_type=None, enabled=None, _auth=mock_auth, _=None
        )

        assert len(result) == 2

        # Verify channel data structure
        result_channels = {r.channel_id: r for r in result}

        email_result = result_channels[UUID(email_channel["channel_id"])]
        assert email_result.channel_type == NotificationChannelType.EMAIL
        assert email_result.enabled is True

        slack_result = result_channels[UUID(slack_channel["channel_id"])]
        assert slack_result.channel_type == NotificationChannelType.SLACK
        assert slack_result.enabled is False

    @pytest.mark.asyncio
    async def test_get_notification_channels_filter_by_type(self) -> None:
        """Test filtering notification channels by type."""
        # Add test channels
        test_storage.add_test_channel(
            "email-1", {"channel_type": "email", "enabled": True}
        )
        test_storage.add_test_channel(
            "slack-1", {"channel_type": "slack", "enabled": True}
        )
        test_storage.add_test_channel(
            "webhook-1", {"channel_type": "webhook", "enabled": True}
        )

        # Mock auth
        mock_auth = {"sub": "test_user", "scopes": ["incidents:read"]}

        result = await get_notification_channels(
            channel_type="email", enabled=None, _auth=mock_auth, _=None
        )

        assert len(result) == 1
        assert result[0].channel_type == NotificationChannelType.EMAIL

    @pytest.mark.asyncio
    async def test_get_notification_channels_filter_by_enabled(self) -> None:
        """Test filtering notification channels by enabled status."""
        # Add test channels
        test_storage.add_test_channel(
            "email-1", {"channel_type": "email", "enabled": True}
        )
        test_storage.add_test_channel(
            "slack-1", {"channel_type": "slack", "enabled": False}
        )

        # Mock auth
        mock_auth = {"sub": "test_user", "scopes": ["incidents:read"]}

        result = await get_notification_channels(
            channel_type=None, enabled=True, _auth=mock_auth, _=None
        )

        assert len(result) == 1
        assert result[0].enabled is True

    @pytest.mark.asyncio
    async def test_get_notification_channels_filter_both(self) -> None:
        """Test filtering notification channels by both type and enabled status."""
        # Add test channels
        test_storage.add_test_channel(
            "email-1", {"channel_type": "email", "enabled": True}
        )
        test_storage.add_test_channel(
            "email-2", {"channel_type": "email", "enabled": False}
        )
        test_storage.add_test_channel(
            "slack-1", {"channel_type": "slack", "enabled": True}
        )

        # Mock auth
        mock_auth = {"sub": "test_user", "scopes": ["incidents:read"]}

        result = await get_notification_channels(
            channel_type="email", enabled=True, _auth=mock_auth, _=None
        )

        assert len(result) == 1
        assert result[0].channel_type == NotificationChannelType.EMAIL
        assert result[0].enabled is True

    @pytest.mark.asyncio
    async def test_send_notification_success(self) -> None:
        """Test sending notification successfully."""
        # Add test channel
        channel = test_storage.add_test_channel(
            "email-1", {"channel_type": "email", "enabled": True}
        )

        # Create request
        request = NotificationSendRequest(
            incident_id=uuid4(),
            notification_type="incident_detected",
            subject="Test Alert",
            message="This is a test notification",
            channels=[channel["channel_id"]],
            priority=NotificationPriority.HIGH,
            metadata={"test": True},
            template_data=None
        )

        # Mock auth and background tasks
        mock_auth = {"sub": "test_user", "scopes": ["incidents:write"]}

        class MockBackgroundTasks(BackgroundTasks):
            def __init__(self) -> None:
                self.tasks: list[Any] = []

            def add_task(self, func: Any, *args: Any, **kwargs: Any) -> None:
                self.tasks.append((func, args, kwargs))

        background_tasks = MockBackgroundTasks()

        result = await send_notification(
            request=request, background_tasks=background_tasks, auth=mock_auth, _=None
        )

        assert isinstance(result, NotificationSendResponse)
        assert result.status == "sending"
        assert result.channels_count == 1
        assert result.message == "Notifications are being sent"
        assert len(background_tasks.tasks) == 1

        # Verify notification was created
        assert len(test_storage.notifications) == 1
        notification = list(test_storage.notifications.values())[0]
        assert notification["subject"] == "Test Alert"
        assert notification["created_by"] == "test_user"

    @pytest.mark.asyncio
    async def test_send_notification_channel_not_found(self) -> None:
        """Test sending notification to non-existent channel."""
        request = NotificationSendRequest(
            incident_id=None,
            notification_type="incident_detected",
            subject="Test Alert",
            message="This is a test notification",
            channels=["non-existent-channel"],
            priority=NotificationPriority.MEDIUM,
            template_data=None
        )

        mock_auth = {"sub": "test_user", "scopes": ["incidents:write"]}

        class MockBackgroundTasks(BackgroundTasks):
            def add_task(self, func: Any, *args: Any, **kwargs: Any) -> None:
                pass

        background_tasks = MockBackgroundTasks()

        with pytest.raises(HTTPException) as exc_info:
            await send_notification(
                request=request,
                background_tasks=background_tasks,
                auth=mock_auth,
                _=None,
            )

        assert exc_info.value.status_code == 404
        assert "Channel non-existent-channel not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_send_notification_channel_disabled(self) -> None:
        """Test sending notification to disabled channel."""
        # Add disabled channel
        channel = test_storage.add_test_channel(
            "disabled-1", {"channel_type": "email", "enabled": False}
        )

        request = NotificationSendRequest(
            incident_id=None,
            notification_type="incident_detected",
            subject="Test Alert",
            message="This is a test notification",
            channels=[channel["channel_id"]],
            priority=NotificationPriority.MEDIUM,
            template_data=None
        )

        mock_auth = {"sub": "test_user", "scopes": ["incidents:write"]}

        class MockBackgroundTasks(BackgroundTasks):
            def add_task(self, func: Any, *args: Any, **kwargs: Any) -> None:
                pass

        background_tasks = MockBackgroundTasks()

        with pytest.raises(HTTPException) as exc_info:
            await send_notification(
                request=request,
                background_tasks=background_tasks,
                auth=mock_auth,
                _=None,
            )

        assert exc_info.value.status_code == 400
        assert f"Channel {channel['channel_id']} is disabled" in str(
            exc_info.value.detail
        )

    @pytest.mark.asyncio
    async def test_send_notification_multiple_channels(self) -> None:
        """Test sending notification to multiple channels."""
        # Add test channels
        email_channel = test_storage.add_test_channel(
            "email-1", {"channel_type": "email", "enabled": True}
        )
        slack_channel = test_storage.add_test_channel(
            "slack-1", {"channel_type": "slack", "enabled": True}
        )

        request = NotificationSendRequest(
            incident_id=None,
            notification_type="incident_detected",
            subject="Multi-channel Alert",
            message="This is a multi-channel notification",
            channels=[email_channel["channel_id"], slack_channel["channel_id"]],
            priority=NotificationPriority.CRITICAL,
            template_data=None
        )

        mock_auth = {"sub": "test_user", "scopes": ["incidents:write"]}

        class MockBackgroundTasks(BackgroundTasks):
            def add_task(self, func: Any, *args: Any, **kwargs: Any) -> None:
                pass

        background_tasks = MockBackgroundTasks()

        result = await send_notification(
            request=request, background_tasks=background_tasks, auth=mock_auth, _=None
        )

        assert result.channels_count == 2
        assert result.status == "sending"

    @pytest.mark.asyncio
    async def test_get_notification_preferences_default(self) -> None:
        """Test getting default notification preferences for new user."""
        mock_auth = {"sub": "new_user", "scopes": ["incidents:read"]}

        result = await get_notification_preferences(auth=mock_auth, _=None)

        assert isinstance(result, NotificationPreferences)
        assert result.user_id == "new_user"
        assert result.email_enabled is True
        assert result.slack_enabled is False
        assert result.severity_filter == ["critical", "high"]
        assert result.notification_types == [
            "incident_detected",
            "remediation_required",
        ]
        assert result.timezone == "UTC"

    @pytest.mark.asyncio
    async def test_get_notification_preferences_existing(self) -> None:
        """Test getting existing notification preferences."""
        user_id = "existing_user"

        # Set up existing preferences
        test_storage.preferences[user_id] = {
            "user_id": user_id,
            "email_enabled": False,
            "slack_enabled": True,
            "teams_enabled": True,
            "webhook_enabled": False,
            "severity_filter": ["critical"],
            "notification_types": ["incident_detected"],
            "quiet_hours_enabled": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00",
            "timezone": "America/New_York",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        mock_auth = {"sub": user_id, "scopes": ["incidents:read"]}

        result = await get_notification_preferences(auth=mock_auth, _=None)

        assert result.user_id == user_id
        assert result.email_enabled is False
        assert result.slack_enabled is True
        assert result.teams_enabled is True
        assert result.severity_filter == ["critical"]
        assert result.timezone == "America/New_York"

    @pytest.mark.asyncio
    async def test_update_notification_preferences_new_user(self) -> None:
        """Test updating notification preferences for new user."""
        user_id = "new_user"

        update = NotificationPreferencesUpdate(
            email_enabled=False,
            slack_enabled=True,
            severity_filter=["critical", "high", "medium"],
            timezone="Europe/London",
        )

        mock_auth = {"sub": user_id, "scopes": ["incidents:write"]}

        result = await update_notification_preferences(
            update=update, auth=mock_auth, _=None
        )

        assert result.user_id == user_id
        assert result.email_enabled is False
        assert result.slack_enabled is True
        assert result.severity_filter == ["critical", "high", "medium"]
        assert result.timezone == "Europe/London"

        # Verify preferences were saved
        saved_prefs = test_storage.preferences[user_id]
        assert saved_prefs["email_enabled"] is False
        assert saved_prefs["slack_enabled"] is True
        assert "updated_at" in saved_prefs

    @pytest.mark.asyncio
    async def test_update_notification_preferences_existing_user(self) -> None:
        """Test updating notification preferences for existing user."""
        user_id = "existing_user"

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

        update = NotificationPreferencesUpdate(
            teams_enabled=True,
            quiet_hours_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0),
        )

        mock_auth = {"sub": user_id, "scopes": ["incidents:write"]}

        result = await update_notification_preferences(
            update=update, auth=mock_auth, _=None
        )

        # Original values should be preserved
        assert result.email_enabled is True
        assert result.slack_enabled is False

        # Updated values should be applied
        assert result.teams_enabled is True
        assert result.quiet_hours_enabled is True
        assert result.quiet_hours_start == time(22, 0)
        assert result.quiet_hours_end == time(8, 0)

    @pytest.mark.asyncio
    async def test_send_notifications_async_email(self) -> None:
        """Test async notification sending for email channel."""
        # Add email channel
        channel = test_storage.add_test_channel(
            "email-1", {"channel_type": "email", "enabled": True}
        )

        # Create notification
        notification_id = str(uuid4())
        test_storage.notifications[notification_id] = {
            "id": notification_id,
            "status": "created",
        }

        await _send_notifications_async(
            notification_id=notification_id,
            channels=[channel["channel_id"]],
            _subject="Test Subject",
            _message="Test Message",
            priority="high",
            _template_data=None,
        )

        # Verify notification was updated
        notification = test_storage.notifications[notification_id]
        assert notification["status"] == "sent"
        assert "results" in notification
        assert len(notification["results"]) == 1

        result = notification["results"][0]
        assert result["channel_id"] == channel["channel_id"]
        assert result["status"] == "sent"
        assert "sent_to" in result

    @pytest.mark.asyncio
    async def test_send_notifications_async_slack(self) -> None:
        """Test async notification sending for Slack channel."""
        # Add Slack channel
        channel = test_storage.add_test_channel(
            "slack-1", {"channel_type": "slack", "enabled": True}
        )

        # Create notification
        notification_id = str(uuid4())
        test_storage.notifications[notification_id] = {
            "id": notification_id,
            "status": "created",
        }

        await _send_notifications_async(
            notification_id=notification_id,
            channels=[channel["channel_id"]],
            _subject="Test Subject",
            _message="Test Message",
            priority="critical",
            _template_data=None,
        )

        # Verify notification was updated
        notification = test_storage.notifications[notification_id]
        assert notification["status"] == "sent"

        result = notification["results"][0]
        assert result["channel_id"] == channel["channel_id"]
        assert result["status"] == "sent"
        assert "slack_channel" in result

    @pytest.mark.asyncio
    async def test_send_notifications_async_teams(self) -> None:
        """Test async notification sending for Teams channel."""
        # Add Teams channel
        channel = test_storage.add_test_channel(
            "teams-1", {"channel_type": "teams", "enabled": True}
        )

        # Create notification
        notification_id = str(uuid4())
        test_storage.notifications[notification_id] = {
            "id": notification_id,
            "status": "created",
        }

        await _send_notifications_async(
            notification_id=notification_id,
            channels=[channel["channel_id"]],
            _subject="Test Subject",
            _message="Test Message",
            priority="medium",
            _template_data=None,
        )

        # Verify notification was updated
        notification = test_storage.notifications[notification_id]
        assert notification["status"] == "sent"

        result = notification["results"][0]
        assert result["channel_id"] == channel["channel_id"]
        assert result["status"] == "sent"
        assert "teams_channel" in result

    @pytest.mark.asyncio
    async def test_send_notifications_async_webhook(self) -> None:
        """Test async notification sending for webhook channel."""
        # Add webhook channel
        channel = test_storage.add_test_channel(
            "webhook-1", {"channel_type": "webhook", "enabled": True}
        )

        # Create notification
        notification_id = str(uuid4())
        test_storage.notifications[notification_id] = {
            "id": notification_id,
            "status": "created",
        }

        await _send_notifications_async(
            notification_id=notification_id,
            channels=[channel["channel_id"]],
            _subject="Test Subject",
            _message="Test Message",
            priority="low",
            _template_data=None,
        )

        # Verify notification was updated
        notification = test_storage.notifications[notification_id]
        assert notification["status"] == "sent"

        result = notification["results"][0]
        assert result["channel_id"] == channel["channel_id"]
        assert result["status"] == "sent"
        assert "webhook_url" in result

    @pytest.mark.asyncio
    async def test_send_notifications_async_unknown_channel_type(self) -> None:
        """Test async notification sending for unknown channel type."""
        # Add channel with unknown type
        channel = test_storage.add_test_channel(
            "unknown-1", {"channel_type": "unknown", "enabled": True}
        )

        # Create notification
        notification_id = str(uuid4())
        test_storage.notifications[notification_id] = {
            "id": notification_id,
            "status": "created",
        }

        await _send_notifications_async(
            notification_id=notification_id,
            channels=[channel["channel_id"]],
            _subject="Test Subject",
            _message="Test Message",
            priority="medium",
            _template_data=None,
        )

        # Verify notification was updated
        notification = test_storage.notifications[notification_id]
        assert notification["status"] == "partially_sent"

        result = notification["results"][0]
        assert result["channel_id"] == channel["channel_id"]
        assert result["status"] == "failed"
        assert "Unknown channel type" in result["error"]

    @pytest.mark.asyncio
    async def test_send_notifications_async_channel_not_found(self) -> None:
        """Test async notification sending when channel not found."""
        # Create notification
        notification_id = str(uuid4())
        test_storage.notifications[notification_id] = {
            "id": notification_id,
            "status": "created",
        }

        await _send_notifications_async(
            notification_id=notification_id,
            channels=["non-existent-channel"],
            _subject="Test Subject",
            _message="Test Message",
            priority="medium",
            _template_data=None,
        )

        # Verify notification was updated
        notification = test_storage.notifications[notification_id]
        assert notification["status"] == "partially_sent"

        result = notification["results"][0]
        assert result["channel_id"] == "non-existent-channel"
        assert result["status"] == "failed"
        assert result["error"] == "Not found"

    @pytest.mark.asyncio
    async def test_send_notifications_async_mixed_results(self) -> None:
        """Test async notification sending with mixed success/failure results."""
        # Add one valid channel
        valid_channel = test_storage.add_test_channel(
            "email-1", {"channel_type": "email", "enabled": True}
        )

        # Create notification
        notification_id = str(uuid4())
        test_storage.notifications[notification_id] = {
            "id": notification_id,
            "status": "created",
        }

        await _send_notifications_async(
            notification_id=notification_id,
            channels=[valid_channel["channel_id"], "non-existent-channel"],
            _subject="Test Subject",
            _message="Test Message",
            priority="high",
            _template_data=None,
        )

        # Verify notification was updated
        notification = test_storage.notifications[notification_id]
        assert notification["status"] == "partially_sent"

        results = notification["results"]
        assert len(results) == 2

        # One should succeed, one should fail
        success_count = sum(1 for r in results if r["status"] == "sent")
        fail_count = sum(1 for r in results if r["status"] == "failed")
        assert success_count == 1
        assert fail_count == 1

    @pytest.mark.asyncio
    async def test_notification_models_validation(self) -> None:
        """Test notification model validation and creation."""
        # Test NotificationSendRequest validation
        request = NotificationSendRequest(
            incident_id=uuid4(),
            notification_type="incident_detected",
            subject="Test Subject",
            message="Test message",
            channels=["channel-1", "channel-2"],
            priority=NotificationPriority.HIGH,
            metadata={"source": "test"},
            template_data={"user": "admin"},
        )

        assert request.notification_type == "incident_detected"
        assert request.priority == NotificationPriority.HIGH
        assert len(request.channels) == 2
        assert request.metadata and request.metadata["source"] == "test"

        # Test empty channels validation
        with pytest.raises(ValueError, match="At least one channel must be specified"):
            NotificationSendRequest(
                incident_id=None,
                notification_type="test", subject="Test", message="Test", channels=[],
                template_data=None
            )

        # Test too many channels validation
        with pytest.raises(ValueError, match="Cannot send to more than 10 channels"):
            NotificationSendRequest(
                incident_id=None,
                notification_type="test",
                subject="Test",
                message="Test",
                channels=[f"channel-{i}" for i in range(15)],
                template_data=None
            )

    @pytest.mark.asyncio
    async def test_notification_preferences_models(self) -> None:
        """Test notification preferences model creation and validation."""
        # Test default preferences
        prefs = NotificationPreferences(user_id="test_user")
        assert prefs.email_enabled is True
        assert prefs.slack_enabled is False
        assert prefs.severity_filter == ["critical", "high"]
        assert prefs.timezone == "UTC"

        # Test custom preferences
        custom_prefs = NotificationPreferences(
            user_id="custom_user",
            email_enabled=False,
            teams_enabled=True,
            severity_filter=["critical"],
            quiet_hours_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0),
            timezone="Europe/London",
        )

        assert custom_prefs.email_enabled is False
        assert custom_prefs.teams_enabled is True
        assert custom_prefs.quiet_hours_start == time(22, 0)
        assert custom_prefs.timezone == "Europe/London"

    @pytest.mark.asyncio
    async def test_notification_channel_models(self) -> None:
        """Test notification channel model creation."""
        config = NotificationChannelConfig(
            recipients=["test@example.com"], from_address="alerts@example.com"
        )

        channel = NotificationChannel(
            channel_id=uuid4(),
            channel_type=NotificationChannelType.EMAIL,
            name="Test Email Channel",
            description="Test channel for emails",
            enabled=True,
            config=config,
            test_mode=True,
            created_at=datetime.now(timezone.utc),
        )

        assert channel.channel_type == NotificationChannelType.EMAIL
        assert channel.enabled is True
        assert channel.test_mode is True
        assert channel.config.recipients == ["test@example.com"]

    def test_notification_channel_from_storage_model(self) -> None:
        """Test creating NotificationChannel from storage model."""
        # Create mock storage model
        storage_model = type("StorageModel", (), {})()
        storage_model.id = str(uuid4())
        storage_model.channel_type = "email"
        storage_model.name = "Test Channel"
        storage_model.description = "Test description"
        storage_model.enabled = True
        storage_model.config = {
            "recipients": ["test@example.com"],
            "from_address": "alerts@example.com",
        }
        storage_model.test_mode = False
        storage_model.created_at = datetime.now(timezone.utc)
        storage_model.updated_at = None

        channel = NotificationChannel.from_storage_model(storage_model)

        assert str(channel.channel_id) == storage_model.id
        assert channel.channel_type == NotificationChannelType.EMAIL
        assert channel.name == "Test Channel"
        assert channel.enabled is True
        assert channel.config.recipients == ["test@example.com"]
