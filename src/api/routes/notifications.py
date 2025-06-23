"""Notification API endpoints for SentinelOps."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from ..auth import Scopes, require_auth, require_scopes
from ..models.notifications import (
    NotificationChannel,
    NotificationPreferences,
    NotificationPreferencesUpdate,
    NotificationSendRequest,
    NotificationSendResponse,
)
from ...common.storage import Storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get("/channels")
async def get_notification_channels(
    channel_type: Optional[str] = Query(None, description="Filter by channel type"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    _auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_READ])),
) -> List[NotificationChannel]:
    """Get available notification channels.

    Args:
        channel_type: Optional channel type filter (email, slack, teams, webhook)
        enabled: Optional enabled status filter
        auth: Authentication context

    Returns:
        List of notification channels
    """
    try:
        storage = Storage()

        # Get all notification channels
        all_channels = await storage.get_notification_channels()

        # Apply filters
        filtered_channels = []
        for channel in all_channels:
            if channel_type and channel.channel_type != channel_type:
                continue
            if enabled is not None and channel.enabled != enabled:
                continue
            filtered_channels.append(channel)

        logger.info("Retrieved %d notification channels", len(filtered_channels))

        return [
            NotificationChannel.from_storage_model(channel)
            for channel in filtered_channels
        ]

    except Exception as e:
        logger.error("Failed to get notification channels: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get notification channels: {str(e)}"
        ) from e


@router.post("/send")
async def send_notification(
    request: NotificationSendRequest,
    background_tasks: BackgroundTasks,
    auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_WRITE])),
) -> NotificationSendResponse:
    """Send a notification.

    Args:
        request: Notification send request
        background_tasks: FastAPI background tasks
        auth: Authentication context

    Returns:
        NotificationSendResponse with notification details
    """
    try:
        storage = Storage()

        # Validate channels exist and are enabled
        for channel_id in request.channels:
            channel = await storage.get_notification_channel(channel_id)
            if not channel:
                raise HTTPException(
                    status_code=404, detail=f"Channel {channel_id} not found"
                )
            if not channel.enabled:
                raise HTTPException(
                    status_code=400, detail=f"Channel {channel_id} is disabled"
                )

        # Create notification record
        notification_id = await storage.create_notification(
            incident_id=str(request.incident_id) if request.incident_id else None,
            notification_type=request.notification_type,
            subject=request.subject,
            message=request.message,
            channels=request.channels,
            priority=request.priority,
            metadata=request.metadata or {},
            created_by=auth.get("sub", "unknown"),
        )

        # Send notifications in background
        background_tasks.add_task(
            _send_notifications_async,
            notification_id,
            request.channels,
            request.subject,
            request.message,
            request.priority,
            request.template_data,
        )

        logger.info(
            "Created notification %s for %d channels",
            notification_id,
            len(request.channels),
        )

        return NotificationSendResponse(
            notification_id=UUID(notification_id),
            status="sending",
            channels_count=len(request.channels),
            message="Notifications are being sent",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to send notification: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to send notification: {str(e)}"
        ) from e


@router.get("/preferences")
async def get_notification_preferences(
    auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_READ])),
) -> NotificationPreferences:
    """Get notification preferences for the authenticated user.

    Args:
        auth: Authentication context

    Returns:
        NotificationPreferences for the user
    """
    try:
        storage = Storage()
        user_id = auth.get("sub", "unknown")

        # Get user preferences
        preferences = await storage.get_notification_preferences(user_id)

        if not preferences:
            # Return default preferences
            return NotificationPreferences(
                user_id=user_id,
                email_enabled=True,
                slack_enabled=False,
                teams_enabled=False,
                webhook_enabled=False,
                severity_filter=["critical", "high"],
                notification_types=["incident_detected", "remediation_required"],
                quiet_hours_enabled=False,
                quiet_hours_start=None,
                quiet_hours_end=None,
                timezone="UTC",
            )

        return NotificationPreferences.from_storage_model(preferences)

    except Exception as e:
        logger.error("Failed to get notification preferences: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get notification preferences: {str(e)}"
        ) from e


@router.put("/preferences")
async def update_notification_preferences(
    update: NotificationPreferencesUpdate,
    auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_WRITE])),
) -> NotificationPreferences:
    """Update notification preferences for the authenticated user.

    Args:
        update: Notification preferences update
        auth: Authentication context

    Returns:
        Updated NotificationPreferences
    """
    try:
        storage = Storage()
        user_id = auth.get("sub", "unknown")

        # Get existing preferences or create new
        preferences = await storage.get_notification_preferences(user_id)

        if not preferences:
            # Create new preferences
            preferences = {
                "user_id": user_id,
                "email_enabled": True,
                "slack_enabled": False,
                "teams_enabled": False,
                "webhook_enabled": False,
                "severity_filter": ["critical", "high"],
                "notification_types": ["incident_detected", "remediation_required"],
                "quiet_hours_enabled": False,
                "timezone": "UTC",
            }

        # Update with provided values
        update_dict = update.dict(exclude_unset=True)
        preferences.update(update_dict)
        preferences["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Save preferences
        await storage.update_notification_preferences(user_id, preferences)

        logger.info("Updated notification preferences for user %s", user_id)

        return NotificationPreferences(**preferences)

    except Exception as e:
        logger.error("Failed to update notification preferences: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update notification preferences: {str(e)}",
        ) from e


async def _send_notifications_async(
    notification_id: str,
    channels: List[str],
    _subject: str,
    _message: str,
    priority: str,
    _template_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Send notifications asynchronously.

    This is a simplified implementation. In production, this would
    integrate with actual notification services.
    """
    storage = Storage()

    try:
        # Update status to sending
        await storage.update_notification(notification_id, status="sending")

        # Process each channel
        results = []
        for channel_id in channels:
            channel = await storage.get_notification_channel(channel_id)
            if not channel:
                results.append(
                    {"channel_id": channel_id, "status": "failed", "error": "Not found"}
                )
                continue

            # Simulate sending based on channel type
            logger.info(
                "Sending %s notification via %s (channel: %s)",
                priority,
                channel.channel_type,
                channel_id,
            )

            if channel.channel_type == "email":
                # Simulate email sending
                result = {
                    "channel_id": channel_id,
                    "status": "sent",
                    "sent_to": channel.config.get("recipients", []),
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                }
            elif channel.channel_type == "slack":
                # Simulate Slack notification
                result = {
                    "channel_id": channel_id,
                    "status": "sent",
                    "slack_channel": channel.config.get("channel"),
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                }
            elif channel.channel_type == "teams":
                # Simulate Teams notification
                result = {
                    "channel_id": channel_id,
                    "status": "sent",
                    "teams_channel": channel.config.get("channel"),
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                }
            elif channel.channel_type == "webhook":
                # Simulate webhook call
                result = {
                    "channel_id": channel_id,
                    "status": "sent",
                    "webhook_url": channel.config.get("url"),
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                }
            else:
                result = {
                    "channel_id": channel_id,
                    "status": "failed",
                    "error": f"Unknown channel type: {channel.channel_type}",
                }

            results.append(result)

        # Update notification status
        all_sent = all(r["status"] == "sent" for r in results)
        final_status = "sent" if all_sent else "partially_sent"

        await storage.update_notification(
            notification_id,
            status=final_status,
            results=results,
            completed_at=datetime.now(timezone.utc),
        )

        logger.info(
            "Completed notification %s with status %s", notification_id, final_status
        )

    except (OSError, ConnectionError, RuntimeError, ValueError) as e:
        logger.error("Failed to send notifications %s: %s", notification_id, str(e))
        await storage.update_notification(
            notification_id,
            status="failed",
            error=str(e),
            completed_at=datetime.now(timezone.utc),
        )
