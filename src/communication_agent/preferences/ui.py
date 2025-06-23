"""
Preference UI endpoints for the Communication Agent.

Provides API endpoints for managing user preferences through
a web interface.
"""

from datetime import datetime, time, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.communication_agent.preferences.manager import PreferenceManager
from src.communication_agent.preferences.validators import PreferenceValidator
from src.communication_agent.types import NotificationChannel
from src.utils.logging import get_logger

logger = get_logger(__name__)


# Pydantic models for API


class ChannelPreference(BaseModel):
    """Channel preference model."""

    channel: str
    enabled: bool


class QuietHoursConfig(BaseModel):
    """Quiet hours configuration model."""

    enabled: bool
    start: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    end: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: str = "UTC"


class FrequencyLimit(BaseModel):
    """Frequency limit model."""

    notification_type: str
    limit: int = Field(..., ge=0, le=1000)


class PreferenceUpdate(BaseModel):
    """Preference update request model."""

    channels: Optional[Dict[str, bool]] = None
    severity_threshold: Optional[str] = None
    quiet_hours: Optional[QuietHoursConfig] = None
    frequency_limits: Optional[Dict[str, int]] = None
    excluded_types: Optional[List[str]] = None


class PreferenceSummary(BaseModel):
    """Preference summary response model."""

    recipient_id: str
    enabled_channels: List[str]
    severity_threshold: str
    quiet_hours: str
    frequency_limits: Dict[str, int]
    excluded_types: List[str]
    timezone: str


class PreferenceUI:
    """
    UI endpoints for preference management.

    Provides RESTful API for preference CRUD operations.
    """

    def __init__(self, preference_manager: PreferenceManager):
        """
        Initialize preference UI.

        Args:
            preference_manager: Preference manager instance
        """
        self.manager = preference_manager
        self.router = APIRouter(prefix="/preferences", tags=["preferences"])
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up API routes."""
        self._setup_get_routes()
        self._setup_update_routes()
        self._setup_channel_routes()
        self._setup_quiet_hours_routes()
        self._setup_threshold_routes()
        self._setup_exclusion_routes()
        self._setup_bulk_routes()
        self._setup_export_import_routes()

    def _setup_get_routes(self) -> None:
        """Set up GET routes."""

        @self.router.get("/{recipient_id}", response_model=PreferenceSummary)
        async def get_preferences(recipient_id: str) -> PreferenceSummary:
            """Get preferences for a recipient."""
            summary = self.manager.get_preference_summary(recipient_id)

            if "error" in summary:
                raise HTTPException(status_code=404, detail=summary["error"])

            return PreferenceSummary(**summary)

        @self.router.get("/{recipient_id}/suggestions")
        async def get_preference_suggestions(
            recipient_id: str,
            role: str = Query(...),
            work_start: Optional[int] = Query(None, ge=0, le=23),
            work_end: Optional[int] = Query(None, ge=0, le=23),
        ) -> Dict[str, Any]:
            """Get preference suggestions based on role."""
            work_hours = None
            if work_start is not None and work_end is not None:
                work_hours = (work_start, work_end)

            suggestions = PreferenceValidator.suggest_preferences(
                role,
                work_hours,
            )

            return {
                "recipient_id": recipient_id,
                "role": role,
                "suggestions": suggestions,
            }

    def _setup_update_routes(self) -> None:
        """Set up general update routes."""

        @self.router.put("/{recipient_id}")
        async def update_preferences(
            recipient_id: str,
            updates: PreferenceUpdate,
        ) -> Dict[str, Any]:
            """Update preferences for a recipient."""
            # Convert Pydantic model to dict
            update_dict = updates.dict(exclude_unset=True)

            # Convert quiet hours if present
            if updates.quiet_hours:
                update_dict["quiet_hours"] = updates.quiet_hours.dict()

            # Validate updates
            is_valid, errors = PreferenceValidator.validate_preferences(update_dict)

            if not is_valid:
                raise HTTPException(status_code=400, detail={"errors": errors})

            # Apply updates
            success = self.manager.update_preferences(recipient_id, update_dict)

            if not success:
                raise HTTPException(
                    status_code=500, detail="Failed to update preferences"
                )

            return {"status": "success", "recipient_id": recipient_id}

        @self.router.post("/{recipient_id}/reset")
        async def reset_preferences(recipient_id: str) -> Dict[str, Any]:
            """Reset preferences to defaults."""
            success = self.manager.reset_preferences(recipient_id)

            if not success:
                raise HTTPException(
                    status_code=500, detail="Failed to reset preferences"
                )

            return {"status": "success", "message": "Preferences reset to defaults"}

    def _setup_channel_routes(self) -> None:
        """Set up channel preference routes."""

        @self.router.post("/{recipient_id}/channels")
        async def set_channel_preference(
            recipient_id: str,
            preference: ChannelPreference,
        ) -> Dict[str, Any]:
            """Set preference for a specific channel."""
            try:
                channel = NotificationChannel(preference.channel)
            except ValueError as exc:
                raise HTTPException(
                    status_code=400, detail=f"Invalid channel: {preference.channel}"
                ) from exc

            success = self.manager.set_channel_preference(
                recipient_id,
                channel,
                preference.enabled,
            )

            if not success:
                raise HTTPException(
                    status_code=500, detail="Failed to update channel preference"
                )

            return {
                "status": "success",
                "channel": preference.channel,
                "enabled": preference.enabled,
            }

    def _setup_quiet_hours_routes(self) -> None:
        """Set up quiet hours routes."""

        @self.router.post("/{recipient_id}/quiet-hours")
        async def set_quiet_hours(
            recipient_id: str,
            config: QuietHoursConfig,
        ) -> Dict[str, Any]:
            """Set quiet hours configuration."""
            # Parse times
            try:
                start_hour, start_min = map(int, config.start.split(":"))
                end_hour, end_min = map(int, config.end.split(":"))

                start_time = time(start_hour, start_min)
                end_time = time(end_hour, end_min)
            except ValueError as exc:
                raise HTTPException(
                    status_code=400, detail="Invalid time format"
                ) from exc

            # Validate logic
            is_valid, error = PreferenceValidator.validate_quiet_hours_logic(
                start_time,
                end_time,
                config.timezone,
            )

            if not is_valid:
                raise HTTPException(status_code=400, detail=error)

            success = self.manager.set_quiet_hours(
                recipient_id,
                config.enabled,
                start_time,
                end_time,
                config.timezone,
            )

            if not success:
                raise HTTPException(
                    status_code=500, detail="Failed to update quiet hours"
                )

            return {"status": "success", "quiet_hours": config.dict()}

    def _setup_threshold_routes(self) -> None:
        """Set up threshold and limit routes."""

        @self.router.post("/{recipient_id}/severity-threshold")
        async def set_severity_threshold(
            recipient_id: str,
            threshold: str = Query(..., regex="^(low|medium|high|critical)$"),
        ) -> Dict[str, Any]:
            """Set severity threshold."""
            success = self.manager.set_severity_threshold(
                recipient_id,
                threshold,
            )

            if not success:
                raise HTTPException(
                    status_code=500, detail="Failed to update severity threshold"
                )

            return {
                "status": "success",
                "severity_threshold": threshold,
            }

        @self.router.post("/{recipient_id}/frequency-limits")
        async def set_frequency_limit(
            recipient_id: str,
            limit: FrequencyLimit,
        ) -> Dict[str, Any]:
            """Set frequency limit for a notification type."""
            success = self.manager.set_frequency_limit(
                recipient_id,
                limit.notification_type,
                limit.limit,
            )

            if not success:
                raise HTTPException(
                    status_code=500, detail="Failed to update frequency limit"
                )

            return {
                "status": "success",
                "notification_type": limit.notification_type,
                "limit": limit.limit,
            }

    def _setup_exclusion_routes(self) -> None:
        """Set up exclusion routes."""

        @self.router.post("/{recipient_id}/exclude-type")
        async def exclude_notification_type(
            recipient_id: str,
            notification_type: str,
            exclude: bool = True,
        ) -> Dict[str, Any]:
            """Exclude or include a notification type."""
            # Validate against critical types
            if exclude and notification_type in [
                "critical_alert",
                "incident_escalation",
            ]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot exclude critical notification type: {notification_type}",
                )

            success = self.manager.exclude_notification_type(
                recipient_id,
                notification_type,
                exclude,
            )

            if not success:
                raise HTTPException(
                    status_code=500, detail="Failed to update excluded types"
                )

            return {
                "status": "success",
                "notification_type": notification_type,
                "excluded": exclude,
            }

    def _setup_bulk_routes(self) -> None:
        """Set up bulk operation routes."""

        @self.router.post("/bulk-update")
        async def bulk_update_preferences(
            updates: Dict[str, PreferenceUpdate],
        ) -> Dict[str, Any]:
            """Update preferences for multiple recipients."""
            # Convert to dict format
            update_dict = {}
            for recipient_id, preference_update in updates.items():
                update_dict[recipient_id] = preference_update.dict(exclude_unset=True)

                # Convert quiet hours if present
                if preference_update.quiet_hours:
                    update_dict[recipient_id][
                        "quiet_hours"
                    ] = preference_update.quiet_hours.dict()

            results = self.manager.bulk_update_preferences(update_dict)

            return {
                "status": "completed",
                "results": results,
                "success_count": sum(1 for v in results.values() if v),
                "failure_count": sum(1 for v in results.values() if not v),
            }

    def _setup_export_import_routes(self) -> None:
        """Set up export/import routes."""

        @self.router.get("/export/{recipient_id}")
        async def export_preferences(recipient_id: str) -> Dict[str, Any]:
            """Export preferences for a recipient."""
            exported = self.manager.export_preferences(recipient_id)

            if not exported:
                raise HTTPException(status_code=404, detail="Preferences not found")

            return {
                "recipient_id": recipient_id,
                "preferences": exported[recipient_id],
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }

        @self.router.post("/import")
        async def import_preferences(
            preference_data: Dict[str, Dict[str, Any]],
        ) -> Dict[str, Any]:
            """Import preferences from exported data."""
            results = self.manager.import_preferences(preference_data)

            return {
                "status": "completed",
                "results": results,
                "success_count": sum(1 for v in results.values() if v),
                "failure_count": sum(1 for v in results.values() if not v),
            }

    def get_router(self) -> APIRouter:
        """Get the FastAPI router."""
        return self.router

    @staticmethod
    def create_preference_dashboard_data(
        manager: PreferenceManager,
        recipient_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Create data for preference dashboard.

        Args:
            manager: Preference manager
            recipient_ids: List of recipient IDs

        Returns:
            Dashboard data
        """
        dashboard_data: Dict[str, Any] = {
            "total_recipients": len(recipient_ids),
            "channel_usage": {
                "email": 0,
                "slack": 0,
                "sms": 0,
                "webhook": 0,
            },
            "severity_distribution": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0,
            },
            "quiet_hours_enabled": 0,
            "recipients": [],
        }

        channel_usage = dashboard_data["channel_usage"]
        severity_dist = dashboard_data["severity_distribution"]
        recipients_list = dashboard_data["recipients"]

        for recipient_id in recipient_ids:
            summary = manager.get_preference_summary(recipient_id)

            if "error" not in summary:
                # Count channel usage
                for channel in summary["enabled_channels"]:
                    if isinstance(channel_usage, dict) and channel in channel_usage:
                        channel_usage[channel] += 1

                # Count severity distribution
                threshold = summary["severity_threshold"]
                if isinstance(severity_dist, dict) and threshold in severity_dist:
                    severity_dist[threshold] += 1

                # Count quiet hours
                if summary["quiet_hours"] != "Disabled":
                    quiet_hours_count = dashboard_data.get("quiet_hours_enabled", 0)
                    if isinstance(quiet_hours_count, int):
                        dashboard_data["quiet_hours_enabled"] = quiet_hours_count + 1

                # Add to recipient list
                if isinstance(recipients_list, list):
                    recipients_list.append(
                        {
                            "id": recipient_id,
                            "channels": len(summary["enabled_channels"]),
                            "threshold": threshold,
                            "quiet_hours": summary["quiet_hours"] != "Disabled",
                        }
                    )

        return dashboard_data
