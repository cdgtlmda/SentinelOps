"""
Preference manager for user notification preferences.

Manages user preferences for notification channels, frequency,
severity thresholds, and quiet hours.
"""

import json
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.communication_agent.recipient_management.models import (
    NotificationPreferences,
)
from src.communication_agent.recipient_management.registry import RecipientRegistry
from src.communication_agent.types import NotificationChannel
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PreferenceManager:
    """
    Manages user notification preferences.

    Features:
    - Channel preferences (enable/disable)
    - Frequency settings
    - Severity thresholds
    - Quiet hours configuration
    - Preference persistence
    """

    def __init__(
        self,
        registry: RecipientRegistry,
        storage_path: Optional[Path] = None,
    ):
        """
        Initialize preference manager.

        Args:
            registry: Recipient registry
            storage_path: Optional path for preference persistence
        """
        self.registry = registry
        self.storage_path = storage_path

        # Load preferences from storage if available
        if self.storage_path and self.storage_path.exists():
            self._load_preferences()

        logger.info("Preference manager initialized")

    def get_preferences(
        self,
        recipient_id: str,
    ) -> Optional[NotificationPreferences]:
        """
        Get preferences for a recipient.

        Args:
            recipient_id: Recipient identifier

        Returns:
            Notification preferences or None
        """
        return self.registry.get_preferences(recipient_id)

    def update_preferences(
        self,
        recipient_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """
        Update preferences for a recipient.

        Args:
            recipient_id: Recipient identifier
            updates: Dictionary of preference updates

        Returns:
            True if successful, False otherwise
        """
        try:
            prefs = self._get_or_create_preferences(recipient_id)
            if not prefs:
                return False

            # Apply all updates
            self._apply_preference_updates(prefs, updates)

            # Save to registry
            self.registry.update_preferences(prefs)

            # Persist to storage
            if self.storage_path:
                self._save_preferences()

            logger.info(
                "Updated preferences for recipient: %s",
                recipient_id,
                extra={"updates": list(updates.keys())},
            )

            return True

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(
                "Error updating preferences: %s",
                e,
                extra={"recipient_id": recipient_id},
                exc_info=True,
            )
            return False

    def _get_or_create_preferences(
        self, recipient_id: str
    ) -> Optional[NotificationPreferences]:
        """Get existing preferences or create new ones."""
        prefs = self.get_preferences(recipient_id)
        if prefs:
            return prefs

        recipient = self.registry.get_recipient(recipient_id)
        if not recipient:
            logger.error("Recipient not found: %s", recipient_id)
            return None

        return NotificationPreferences(
            recipient_id=recipient_id,
            timezone=recipient.timezone,
        )

    def _apply_preference_updates(
        self, prefs: NotificationPreferences, updates: Dict[str, Any]
    ) -> None:
        """Apply all preference updates."""
        if "channels" in updates:
            self._update_channel_preferences(prefs, updates["channels"])

        if "severity_threshold" in updates:
            self._update_severity_threshold(prefs, updates["severity_threshold"])

        if "quiet_hours" in updates:
            self._update_quiet_hours(prefs, updates["quiet_hours"])

        if "frequency_limits" in updates:
            self._update_frequency_limits(prefs, updates["frequency_limits"])

        if "excluded_types" in updates:
            self._update_excluded_types(prefs, updates["excluded_types"])

        if "metadata" in updates:
            prefs.metadata.update(updates["metadata"])

    def _update_channel_preferences(
        self, prefs: NotificationPreferences, channels: Dict[str, Any]
    ) -> None:
        """Update channel preferences."""
        for channel, enabled in channels.items():
            try:
                channel_enum = NotificationChannel(channel)
                prefs.channels[channel_enum] = bool(enabled)
            except ValueError:
                logger.warning("Invalid channel: %s", channel)

    def _update_severity_threshold(
        self, prefs: NotificationPreferences, threshold: str
    ) -> None:
        """Update severity threshold."""
        threshold_lower = threshold.lower()
        if threshold_lower in ["low", "medium", "high", "critical"]:
            prefs.severity_threshold = threshold_lower
        else:
            logger.warning("Invalid severity threshold: %s", threshold)

    def _update_quiet_hours(
        self, prefs: NotificationPreferences, quiet_config: Dict[str, Any]
    ) -> None:
        """Update quiet hours configuration."""
        if "enabled" in quiet_config:
            prefs.quiet_hours_enabled = bool(quiet_config["enabled"])

        if "start" in quiet_config:
            prefs.quiet_hours_start = self._parse_time(quiet_config["start"])

        if "end" in quiet_config:
            prefs.quiet_hours_end = self._parse_time(quiet_config["end"])

        if "timezone" in quiet_config:
            prefs.timezone = quiet_config["timezone"]

    def _update_frequency_limits(
        self, prefs: NotificationPreferences, limits: Dict[str, Any]
    ) -> None:
        """Update frequency limits."""
        for notification_type, limit in limits.items():
            if isinstance(limit, int) and limit >= 0:
                prefs.frequency_limits[notification_type] = limit
            else:
                logger.warning(
                    "Invalid frequency limit for %s: %s", notification_type, limit
                )

    def _update_excluded_types(
        self, prefs: NotificationPreferences, excluded: Union[List[str], set[str]]
    ) -> None:
        """Update excluded notification types."""
        if isinstance(excluded, list):
            prefs.excluded_types = set(excluded)
        elif isinstance(excluded, set):
            prefs.excluded_types = excluded

    def set_channel_preference(
        self,
        recipient_id: str,
        channel: NotificationChannel,
        enabled: bool,
    ) -> bool:
        """
        Set preference for a specific channel.

        Args:
            recipient_id: Recipient identifier
            channel: Notification channel
            enabled: Whether channel is enabled

        Returns:
            True if successful
        """
        return self.update_preferences(
            recipient_id,
            {"channels": {channel.value: enabled}},
        )

    def set_quiet_hours(
        self,
        recipient_id: str,
        enabled: bool,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        tz: Optional[str] = None,
    ) -> bool:
        """
        Set quiet hours for a recipient.

        Args:
            recipient_id: Recipient identifier
            enabled: Whether quiet hours are enabled
            start_time: Start time for quiet hours
            end_time: End time for quiet hours
            tz: Timezone for quiet hours

        Returns:
            True if successful
        """
        quiet_config: Dict[str, Union[bool, str]] = {"enabled": enabled}

        if start_time:
            quiet_config["start"] = start_time.strftime("%H:%M")

        if end_time:
            quiet_config["end"] = end_time.strftime("%H:%M")

        if tz:
            quiet_config["timezone"] = tz

        return self.update_preferences(
            recipient_id,
            {"quiet_hours": quiet_config},
        )

    def set_severity_threshold(
        self,
        recipient_id: str,
        threshold: str,
    ) -> bool:
        """
        Set minimum severity threshold for notifications.

        Args:
            recipient_id: Recipient identifier
            threshold: Minimum severity (low, medium, high, critical)

        Returns:
            True if successful
        """
        return self.update_preferences(
            recipient_id,
            {"severity_threshold": threshold},
        )

    def set_frequency_limit(
        self,
        recipient_id: str,
        notification_type: str,
        limit: int,
    ) -> bool:
        """
        Set frequency limit for a notification type.

        Args:
            recipient_id: Recipient identifier
            notification_type: Type of notification
            limit: Maximum notifications per hour

        Returns:
            True if successful
        """
        return self.update_preferences(
            recipient_id,
            {"frequency_limits": {notification_type: limit}},
        )

    def exclude_notification_type(
        self,
        recipient_id: str,
        notification_type: str,
        exclude: bool = True,
    ) -> bool:
        """
        Exclude or include a notification type.

        Args:
            recipient_id: Recipient identifier
            notification_type: Type of notification
            exclude: Whether to exclude (True) or include (False)

        Returns:
            True if successful
        """
        prefs = self.get_preferences(recipient_id)
        if not prefs:
            return False

        if exclude:
            prefs.excluded_types.add(notification_type)
        else:
            prefs.excluded_types.discard(notification_type)

        self.registry.update_preferences(prefs)

        if self.storage_path:
            self._save_preferences()

        return True

    def get_preference_summary(
        self,
        recipient_id: str,
    ) -> Dict[str, Any]:
        """
        Get a summary of recipient preferences.

        Args:
            recipient_id: Recipient identifier

        Returns:
            Preference summary
        """
        prefs = self.get_preferences(recipient_id)
        if not prefs:
            return {"error": "No preferences found"}

        # Get enabled channels
        enabled_channels = [
            channel.value for channel, enabled in prefs.channels.items() if enabled
        ]

        # Format quiet hours
        quiet_hours_str = "Disabled"
        if prefs.quiet_hours_enabled:
            quiet_hours_str = (
                f"{prefs.quiet_hours_start.strftime('%H:%M')} - "
                f"{prefs.quiet_hours_end.strftime('%H:%M')} "
                f"({prefs.timezone})"
            )

        return {
            "recipient_id": recipient_id,
            "enabled_channels": enabled_channels,
            "severity_threshold": prefs.severity_threshold,
            "quiet_hours": quiet_hours_str,
            "frequency_limits": dict(prefs.frequency_limits),
            "excluded_types": list(prefs.excluded_types),
            "timezone": prefs.timezone,
        }

    def bulk_update_preferences(
        self,
        updates: Dict[str, Dict[str, Any]],
    ) -> Dict[str, bool]:
        """
        Update preferences for multiple recipients.

        Args:
            updates: Dictionary of recipient_id to preference updates

        Returns:
            Dictionary of recipient_id to success status
        """
        results = {}

        for recipient_id, recipient_updates in updates.items():
            results[recipient_id] = self.update_preferences(
                recipient_id,
                recipient_updates,
            )

        return results

    def reset_preferences(
        self,
        recipient_id: str,
    ) -> bool:
        """
        Reset preferences to defaults.

        Args:
            recipient_id: Recipient identifier

        Returns:
            True if successful
        """
        recipient = self.registry.get_recipient(recipient_id)
        if not recipient:
            return False

        # Create new default preferences
        default_prefs = NotificationPreferences(
            recipient_id=recipient_id,
            timezone=recipient.timezone,
        )

        # Enable all channels by default
        for channel in NotificationChannel:
            default_prefs.channels[channel] = True

        self.registry.update_preferences(default_prefs)

        if self.storage_path:
            self._save_preferences()

        logger.info("Reset preferences for recipient: %s", recipient_id)

        return True

    def _parse_time(self, time_str: str) -> time:
        """Parse time string to time object."""
        try:
            # Try HH:MM format
            hour, minute = map(int, time_str.split(":"))
            return time(hour, minute)
        except (ValueError, AttributeError):
            # Try other formats
            for fmt in ["%H:%M", "%I:%M %p", "%H:%M:%S"]:
                try:
                    parsed = datetime.strptime(time_str, fmt).time()
                    return parsed
                except ValueError:
                    continue

            # Default to midnight if parsing fails
            logger.warning("Failed to parse time: %s", time_str)
            return time(0, 0)

    def _load_preferences(self) -> None:
        """Load preferences from storage."""
        if not self.storage_path or not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Load preferences from JSON
            preferences_data = data.get("preferences", {})

            for recipient_id, pref_data in preferences_data.items():
                # Convert channel settings
                channels = {}
                for channel_str, enabled in pref_data.get("channels", {}).items():
                    try:
                        channel = NotificationChannel(channel_str)
                        channels[channel] = enabled
                    except ValueError:
                        logger.warning("Unknown channel type: %s", channel_str)

                # Create preferences object
                preferences = NotificationPreferences(
                    recipient_id=recipient_id,
                    channels=channels,
                    severity_threshold=pref_data.get("severity_threshold", "medium"),
                    quiet_hours_enabled=pref_data.get("quiet_hours_enabled", False),
                    quiet_hours_start=time.fromisoformat(
                        pref_data.get("quiet_hours_start", "22:00")
                    ),
                    quiet_hours_end=time.fromisoformat(
                        pref_data.get("quiet_hours_end", "08:00")
                    ),
                    timezone=pref_data.get("timezone", "UTC"),
                    frequency_limits=pref_data.get("frequency_limits", {}),
                    excluded_types=set(pref_data.get("excluded_types", [])),
                    metadata=pref_data.get("metadata", {}),
                )

                # Update in registry
                self.registry.update_preferences(preferences)

            logger.info("Loaded %d preferences from storage", len(preferences_data))

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(
                "Failed to load preferences: %s",
                e,
                exc_info=True,
            )

    def _save_preferences(self) -> None:
        """Save preferences to storage."""
        if not self.storage_path:
            return

        try:
            # Get all preferences from registry
            all_preferences = {}

            # Iterate through all recipients to get their preferences
            for recipient in self.registry.recipients.values():
                prefs = self.registry.get_preferences(recipient.id)
                if prefs:
                    # Convert preferences to JSON-serializable format
                    pref_data = {
                        "channels": {
                            channel.value: enabled
                            for channel, enabled in prefs.channels.items()
                        },
                        "severity_threshold": prefs.severity_threshold,
                        "quiet_hours_enabled": prefs.quiet_hours_enabled,
                        "quiet_hours_start": prefs.quiet_hours_start.isoformat(),
                        "quiet_hours_end": prefs.quiet_hours_end.isoformat(),
                        "timezone": prefs.timezone,
                        "frequency_limits": prefs.frequency_limits,
                        "excluded_types": list(prefs.excluded_types),
                        "metadata": prefs.metadata,
                    }
                    all_preferences[recipient.id] = pref_data

            # Prepare complete data structure
            data = {
                "version": "1.0",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "preferences": all_preferences,
            }

            # Ensure directory exists
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug("Saved %d preferences to storage", len(all_preferences))

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(
                "Failed to save preferences: %s",
                e,
                exc_info=True,
            )

    def export_preferences(
        self,
        recipient_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Export preferences for backup or transfer.

        Args:
            recipient_id: Optional specific recipient (None for all)

        Returns:
            Exported preference data
        """
        if recipient_id:
            prefs = self.get_preferences(recipient_id)
            if not prefs:
                return {}

            return {recipient_id: self._serialize_preferences(prefs)}
        else:
            # Export all preferences
            all_prefs = {}
            for recipient in self.registry.recipients.values():
                prefs = self.get_preferences(recipient.id)
                if prefs:
                    all_prefs[recipient.id] = self._serialize_preferences(prefs)

            return all_prefs

    def import_preferences(
        self,
        preference_data: Dict[str, Any],
    ) -> Dict[str, bool]:
        """
        Import preferences from exported data.

        Args:
            preference_data: Exported preference data

        Returns:
            Import results by recipient ID
        """
        results = {}

        for recipient_id, prefs_data in preference_data.items():
            try:
                self.update_preferences(recipient_id, prefs_data)
                results[recipient_id] = True
            except (ValueError, KeyError, AttributeError) as e:
                logger.error(
                    "Failed to import preferences for %s: %s",
                    recipient_id,
                    e,
                    exc_info=True,
                )
                results[recipient_id] = False

        return results

    def _serialize_preferences(
        self,
        prefs: NotificationPreferences,
    ) -> Dict[str, Any]:
        """Serialize preferences for export."""
        return {
            "channels": {
                channel.value: enabled for channel, enabled in prefs.channels.items()
            },
            "severity_threshold": prefs.severity_threshold,
            "quiet_hours": {
                "enabled": prefs.quiet_hours_enabled,
                "start": prefs.quiet_hours_start.strftime("%H:%M"),
                "end": prefs.quiet_hours_end.strftime("%H:%M"),
                "timezone": prefs.timezone,
            },
            "frequency_limits": dict(prefs.frequency_limits),
            "excluded_types": list(prefs.excluded_types),
            "metadata": dict(prefs.metadata),
        }
