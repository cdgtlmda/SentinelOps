"""
Preference validators for user notification preferences.

Validates preference updates to ensure data integrity and business rules.
"""

from datetime import time
from typing import Any, Dict, List, Optional, Tuple

from src.communication_agent.types import NotificationChannel
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PreferenceValidator:
    """Validates preference updates."""

    # Valid severity levels
    VALID_SEVERITIES = {"low", "medium", "high", "critical"}

    # Valid timezones (subset for example)
    VALID_TIMEZONES = {
        "UTC",
        "US/Eastern",
        "US/Central",
        "US/Mountain",
        "US/Pacific",
        "Europe/London",
        "Europe/Paris",
        "Europe/Berlin",
        "Asia/Tokyo",
        "Asia/Shanghai",
        "Asia/Singapore",
        "Australia/Sydney",
        "Australia/Melbourne",
    }

    # Maximum frequency limits
    MAX_FREQUENCY_LIMITS = {
        "default": 100,
        "critical_alert": 0,  # No limit for critical
        "incident_detected": 50,
        "analysis_complete": 20,
        "status_update": 10,
        "daily_summary": 1,
        "weekly_report": 1,
    }

    @classmethod
    def validate_preferences(
        cls,
        updates: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """
        Validate preference updates.

        Args:
            updates: Preference updates to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Validate channels
        if "channels" in updates:
            channel_errors = cls._validate_channels(updates["channels"])
            errors.extend(channel_errors)

        # Validate severity threshold
        if "severity_threshold" in updates:
            severity_errors = cls._validate_severity_threshold(
                updates["severity_threshold"]
            )
            errors.extend(severity_errors)

        # Validate quiet hours
        if "quiet_hours" in updates:
            quiet_errors = cls._validate_quiet_hours(updates["quiet_hours"])
            errors.extend(quiet_errors)

        # Validate frequency limits
        if "frequency_limits" in updates:
            frequency_errors = cls._validate_frequency_limits(
                updates["frequency_limits"]
            )
            errors.extend(frequency_errors)

        # Validate excluded types
        if "excluded_types" in updates:
            excluded_errors = cls._validate_excluded_types(updates["excluded_types"])
            errors.extend(excluded_errors)

        return len(errors) == 0, errors

    @classmethod
    def _validate_channels(
        cls,
        channels: Any,
    ) -> List[str]:
        """Validate channel preferences."""
        errors = []

        if not isinstance(channels, dict):
            errors.append("Channels must be a dictionary")
            return errors  # Early return for type error

        valid_channels = {ch.value for ch in NotificationChannel}

        for channel, enabled in channels.items():
            if channel not in valid_channels:
                errors.append(f"Invalid channel: {channel}")

            if not isinstance(enabled, bool):
                errors.append(f"Channel {channel} enabled status must be boolean")

        # Ensure at least one channel is enabled
        if all(not enabled for enabled in channels.values()):
            errors.append("At least one channel must be enabled")

        return errors

    @classmethod
    def _validate_severity_threshold(
        cls,
        threshold: Any,
    ) -> List[str]:
        """Validate severity threshold."""
        errors = []

        if not isinstance(threshold, str):
            errors.append("Severity threshold must be a string")
            return errors

        threshold_lower = threshold.lower()
        if threshold_lower not in cls.VALID_SEVERITIES:
            errors.append(
                f"Invalid severity threshold: {threshold}. "
                f"Must be one of: {', '.join(cls.VALID_SEVERITIES)}"
            )

        return errors

    @classmethod
    def _validate_quiet_hours(
        cls,
        quiet_hours: Any,
    ) -> List[str]:
        """Validate quiet hours configuration."""
        errors = []

        if not isinstance(quiet_hours, dict):
            errors.append("Quiet hours must be a dictionary")
            return errors  # Early return for type error

        # Validate individual components
        errors.extend(cls._validate_quiet_hours_enabled(quiet_hours))
        errors.extend(cls._validate_quiet_hours_times(quiet_hours))
        errors.extend(cls._validate_quiet_hours_timezone(quiet_hours))

        # Validate time logic if no errors
        if not errors:
            errors.extend(cls._validate_quiet_hours_time_logic(quiet_hours))

        return errors

    @classmethod
    def _validate_quiet_hours_enabled(
        cls,
        quiet_hours: Dict[str, Any],
    ) -> List[str]:
        """Validate enabled flag in quiet hours."""
        errors = []
        if "enabled" in quiet_hours:
            if not isinstance(quiet_hours["enabled"], bool):
                errors.append("Quiet hours enabled must be boolean")
        return errors

    @classmethod
    def _validate_quiet_hours_times(
        cls,
        quiet_hours: Dict[str, Any],
    ) -> List[str]:
        """Validate start and end times in quiet hours."""
        errors = []

        if "start" in quiet_hours:
            errors.extend(
                cls._validate_time_string(quiet_hours["start"], "Quiet hours start")
            )

        if "end" in quiet_hours:
            errors.extend(
                cls._validate_time_string(quiet_hours["end"], "Quiet hours end")
            )

        return errors

    @classmethod
    def _validate_quiet_hours_timezone(
        cls,
        quiet_hours: Dict[str, Any],
    ) -> List[str]:
        """Validate timezone in quiet hours."""
        errors = []
        if "timezone" in quiet_hours:
            tz = quiet_hours["timezone"]
            if tz not in cls.VALID_TIMEZONES:
                errors.append(
                    f"Invalid timezone: {tz}. "
                    f"Must be one of: {', '.join(sorted(cls.VALID_TIMEZONES))}"
                )
        return errors

    @classmethod
    def _validate_quiet_hours_time_logic(
        cls,
        quiet_hours: Dict[str, Any],
    ) -> List[str]:
        """Validate time logic in quiet hours."""
        errors = []
        if "start" in quiet_hours and "end" in quiet_hours:
            try:
                start_time = cls._parse_time(quiet_hours["start"])
                end_time = cls._parse_time(quiet_hours["end"])

                if start_time == end_time:
                    errors.append("Quiet hours start and end times cannot be the same")
            except ValueError:
                pass  # Already validated above
        return errors

    @classmethod
    def _validate_time_string(
        cls,
        time_str: Any,
        field_name: str,
    ) -> List[str]:
        """Validate time string format."""
        errors = []

        if not isinstance(time_str, str):
            errors.append(f"{field_name} must be a string")
            return errors

        try:
            cls._parse_time(time_str)
        except ValueError:
            errors.append(f"{field_name} must be in HH:MM format (24-hour)")

        return errors

    @classmethod
    def _parse_time(cls, time_str: str) -> time:
        """Parse time string."""
        parts = time_str.split(":")
        if len(parts) != 2:
            raise ValueError("Invalid time format")

        hour = int(parts[0])
        minute = int(parts[1])

        if not 0 <= hour <= 23:
            raise ValueError("Hour must be 0-23")

        if not 0 <= minute <= 59:
            raise ValueError("Minute must be 0-59")

        return time(hour, minute)

    @classmethod
    def _validate_frequency_limits(
        cls,
        limits: Any,
    ) -> List[str]:
        """Validate frequency limits."""
        errors = []

        if not isinstance(limits, dict):
            errors.append("Frequency limits must be a dictionary")
            return errors  # Early return for type error

        for notification_type, limit in limits.items():
            if not isinstance(limit, int):
                errors.append(
                    f"Frequency limit for {notification_type} must be an integer"
                )
                continue

            if limit < 0:
                errors.append(
                    f"Frequency limit for {notification_type} cannot be negative"
                )
                continue

            # Check maximum limits
            max_limit = cls.MAX_FREQUENCY_LIMITS.get(
                notification_type, cls.MAX_FREQUENCY_LIMITS["default"]
            )

            if max_limit > 0 and limit > max_limit:
                errors.append(
                    f"Frequency limit for {notification_type} "
                    f"exceeds maximum ({max_limit})"
                )

        return errors

    @classmethod
    def _validate_excluded_types(
        cls,
        excluded_types: Any,
    ) -> List[str]:
        """Validate excluded notification types."""
        errors = []

        if isinstance(excluded_types, list):
            # Convert to set for validation
            excluded_set = set(excluded_types)
        elif isinstance(excluded_types, set):
            excluded_set = excluded_types
        else:
            errors.append("Excluded types must be a list or set")
            return errors

        # Check for critical types that shouldn't be excluded
        critical_types = {"critical_alert", "incident_escalation"}
        excluded_critical = excluded_set.intersection(critical_types)

        if excluded_critical:
            errors.append(
                f"Cannot exclude critical notification types: "
                f"{', '.join(excluded_critical)}"
            )

        return errors

    @classmethod
    def validate_quiet_hours_logic(
        cls,
        start_time: time,
        end_time: time,
        timezone: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate quiet hours logic.

        Args:
            start_time: Start time
            end_time: End time
            timezone: Timezone

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if quiet hours span is reasonable
        if start_time == end_time:
            return False, "Start and end times cannot be the same"

        # Calculate duration
        if end_time > start_time:
            # Same day
            duration_hours = (
                end_time.hour
                - start_time.hour
                + (end_time.minute - start_time.minute) / 60
            )
        else:
            # Spans midnight
            duration_hours = (
                24
                - start_time.hour
                + end_time.hour
                + (end_time.minute - start_time.minute) / 60
            )

        # Check if duration is too long
        if duration_hours > 20:
            return False, "Quiet hours cannot exceed 20 hours"

        # Validate timezone
        if timezone not in cls.VALID_TIMEZONES:
            return False, f"Invalid timezone: {timezone}"

        return True, None

    @classmethod
    def suggest_preferences(
        cls,
        role: str,
        work_hours: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """
        Suggest default preferences based on role.

        Args:
            role: User role
            work_hours: Optional work hours tuple (start, end)

        Returns:
            Suggested preferences
        """
        # Base preferences
        preferences: Dict[str, Any] = {
            "channels": {
                "email": True,
                "slack": True,
                "sms": False,
                "webhook": False,
            },
            "severity_threshold": "medium",
            "quiet_hours": {
                "enabled": True,
                "start": "22:00",
                "end": "08:00",
                "timezone": "UTC",
            },
            "frequency_limits": {},
            "excluded_types": [],
        }

        # Adjust based on role
        if role == "executive":
            preferences["severity_threshold"] = "high"
            channels = preferences.get("channels", {})
            if isinstance(channels, dict):
                channels["sms"] = True
            preferences["frequency_limits"] = {
                "status_update": 1,
                "daily_summary": 1,
                "weekly_report": 1,
            }

        elif role == "incident_responder":
            preferences["severity_threshold"] = "low"
            channels = preferences.get("channels", {})
            if isinstance(channels, dict):
                channels["sms"] = True
            quiet_hours = preferences.get("quiet_hours", {})
            if isinstance(quiet_hours, dict):
                quiet_hours["enabled"] = False

        elif role == "manager":
            preferences["severity_threshold"] = "medium"
            preferences["frequency_limits"] = {
                "status_update": 5,
                "analysis_complete": 10,
            }

        # Adjust quiet hours based on work hours
        if work_hours:
            start_hour, end_hour = work_hours
            # Set quiet hours outside work hours
            quiet_hours = preferences.get("quiet_hours", {})
            if isinstance(quiet_hours, dict):
                quiet_hours["start"] = f"{end_hour + 2:02d}:00"
                quiet_hours["end"] = f"{start_hour - 1:02d}:00"

        return preferences
