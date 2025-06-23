"""
Comprehensive tests for src/communication_agent/preferences/validators.py

COVERAGE REQUIREMENT: ≥90% statement coverage of target source file
VERIFICATION: python -m pytest tests/unit/communication_agent/preferences/test_validators.py --cov=src.communication_agent.preferences.validators --cov-report=term-missing
"""

import pytest
from datetime import time
from typing import Any, Dict, List, Tuple

# Import the class under test
from src.communication_agent.preferences.validators import PreferenceValidator
from src.communication_agent.types import NotificationChannel


class TestPreferenceValidatorConstants:
    """Test class constants and static attributes."""

    def test_valid_severities(self) -> None:
        """Test VALID_SEVERITIES constant."""
        expected_severities = {"low", "medium", "high", "critical"}
        assert PreferenceValidator.VALID_SEVERITIES == expected_severities
        assert len(PreferenceValidator.VALID_SEVERITIES) == 4
        assert all(isinstance(s, str) for s in PreferenceValidator.VALID_SEVERITIES)

    def test_valid_timezones(self) -> None:
        """Test VALID_TIMEZONES constant."""
        expected_timezones = {
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
        assert PreferenceValidator.VALID_TIMEZONES == expected_timezones
        assert len(PreferenceValidator.VALID_TIMEZONES) >= 12
        assert "UTC" in PreferenceValidator.VALID_TIMEZONES
        assert "US/Eastern" in PreferenceValidator.VALID_TIMEZONES

    def test_max_frequency_limits(self) -> None:
        """Test MAX_FREQUENCY_LIMITS constant."""
        expected_keys = {
            "default",
            "critical_alert",
            "incident_detected",
            "analysis_complete",
            "status_update",
            "daily_summary",
            "weekly_report",
        }
        assert set(PreferenceValidator.MAX_FREQUENCY_LIMITS.keys()) == expected_keys
        assert PreferenceValidator.MAX_FREQUENCY_LIMITS["default"] == 100
        assert PreferenceValidator.MAX_FREQUENCY_LIMITS["critical_alert"] == 0
        assert PreferenceValidator.MAX_FREQUENCY_LIMITS["daily_summary"] == 1
        assert PreferenceValidator.MAX_FREQUENCY_LIMITS["weekly_report"] == 1


class TestValidatePreferences:
    """Test the main validate_preferences method."""

    def test_validate_empty_updates(self) -> None:
        """Test validation with empty updates."""
        is_valid, errors = PreferenceValidator.validate_preferences({})
        assert is_valid is True
        assert errors == []

    def test_validate_all_valid_preferences(self) -> None:
        """Test validation with all valid preferences."""
        updates = {
            "channels": {"email": True, "slack": True, "sms": False, "webhook": False},
            "severity_threshold": "medium",
            "quiet_hours": {
                "enabled": True,
                "start": "22:00",
                "end": "08:00",
                "timezone": "UTC",
            },
            "frequency_limits": {"status_update": 5, "daily_summary": 1},
            "excluded_types": ["weekly_report"],
        }

        is_valid, errors = PreferenceValidator.validate_preferences(updates)
        assert is_valid is True
        assert errors == []

    def test_validate_multiple_invalid_preferences(self) -> None:
        """Test validation with multiple invalid preferences."""
        updates = {
            "channels": "not_a_dict",  # Invalid type
            "severity_threshold": "invalid",  # Invalid severity
            "quiet_hours": {"enabled": "not_bool"},  # Invalid type
            "frequency_limits": {"test": -1},  # Negative limit
            "excluded_types": "not_a_list",  # Invalid type
        }

        is_valid, errors = PreferenceValidator.validate_preferences(updates)
        assert is_valid is False
        assert len(errors) >= 5  # At least one error from each section

        # Check specific error types are present
        error_text = " ".join(errors)
        assert "must be a dictionary" in error_text
        assert "invalid severity threshold" in error_text.lower()
        assert "must be boolean" in error_text
        assert "cannot be negative" in error_text
        assert "must be a list" in error_text

    def test_validate_partial_updates(self) -> None:
        """Test validation with partial updates."""
        # Only channels
        updates1 = {"channels": {"email": True, "slack": False}}
        is_valid, errors = PreferenceValidator.validate_preferences(updates1)
        assert is_valid is True
        assert errors == []

        # Only severity threshold
        updates2 = {"severity_threshold": "high"}
        is_valid, errors = PreferenceValidator.validate_preferences(updates2)
        assert is_valid is True
        assert errors == []

        # Only quiet hours
        updates3 = {"quiet_hours": {"enabled": False}}
        is_valid, errors = PreferenceValidator.validate_preferences(updates3)
        assert is_valid is True
        assert errors == []


class TestValidateChannels:
    """Test channel validation."""

    def test_validate_channels_valid(self) -> None:
        """Test validation of valid channels."""
        channels = {"email": True, "slack": True, "sms": False, "webhook": False}
        errors = PreferenceValidator._validate_channels(channels)
        assert errors == []

    def test_validate_channels_not_dict(self) -> None:
        """Test validation when channels is not a dictionary."""
        channels = "not_a_dict"
        errors = PreferenceValidator._validate_channels(channels)
        assert len(errors) == 1
        assert "must be a dictionary" in errors[0]

    def test_validate_channels_invalid_channel(self) -> None:
        """Test validation with invalid channel names."""
        channels = {"email": True, "invalid_channel": True, "another_invalid": False}
        errors = PreferenceValidator._validate_channels(channels)
        assert len(errors) == 2
        assert any(
            "invalid channel: invalid_channel" in error.lower() for error in errors
        )
        assert any(
            "invalid channel: another_invalid" in error.lower() for error in errors
        )

    def test_validate_channels_non_boolean_values(self) -> None:
        """Test validation with non-boolean enabled values."""
        channels = {"email": "yes", "slack": 1, "sms": None}
        errors = PreferenceValidator._validate_channels(channels)
        assert len(errors) == 3
        assert all("must be boolean" in error for error in errors)

    def test_validate_channels_all_disabled(self) -> None:
        """Test validation when all channels are disabled."""
        channels = {"email": False, "slack": False, "sms": False, "webhook": False}
        errors = PreferenceValidator._validate_channels(channels)
        assert len(errors) == 1
        assert "at least one channel must be enabled" in errors[0].lower()

    def test_validate_channels_at_least_one_enabled(self) -> None:
        """Test validation when at least one channel is enabled."""
        channels = {
            "email": False,
            "slack": True,  # At least one enabled
            "sms": False,
            "webhook": False,
        }
        errors = PreferenceValidator._validate_channels(channels)
        assert errors == []

    def test_validate_channels_mixed_valid_invalid(self) -> None:
        """Test validation with mix of valid and invalid channels."""
        channels = {
            "email": True,  # Valid
            "invalid": False,  # Invalid channel name
            "slack": "not_bool",  # Invalid boolean value
            "sms": True,  # Valid
        }
        errors = PreferenceValidator._validate_channels(channels)
        assert len(errors) == 2
        error_text = " ".join(errors)
        assert "invalid channel: invalid" in error_text.lower()
        assert "must be boolean" in error_text


class TestValidateSeverityThreshold:
    """Test severity threshold validation."""

    def test_validate_severity_threshold_valid(self) -> None:
        """Test validation of valid severity thresholds."""
        for severity in ["low", "medium", "high", "critical"]:
            errors = PreferenceValidator._validate_severity_threshold(severity)
            assert errors == []

    def test_validate_severity_threshold_case_insensitive(self) -> None:
        """Test validation is case insensitive."""
        for severity in ["LOW", "Medium", "HIGH", "Critical"]:
            errors = PreferenceValidator._validate_severity_threshold(severity)
            assert errors == []

    def test_validate_severity_threshold_not_string(self) -> None:
        """Test validation when threshold is not a string."""
        for invalid_threshold in [123, True, [], {}, None]:
            errors = PreferenceValidator._validate_severity_threshold(invalid_threshold)
            assert len(errors) == 1
            assert "must be a string" in errors[0]

    def test_validate_severity_threshold_invalid_value(self) -> None:
        """Test validation with invalid severity values."""
        for invalid_severity in ["invalid", "super_high", "minimal", ""]:
            errors = PreferenceValidator._validate_severity_threshold(invalid_severity)
            assert len(errors) == 1
            assert "invalid severity threshold" in errors[0].lower()
            assert "must be one of" in errors[0].lower()


class TestValidateQuietHours:
    """Test quiet hours validation."""

    def test_validate_quiet_hours_valid_complete(self) -> None:
        """Test validation of complete valid quiet hours."""
        quiet_hours = {
            "enabled": True,
            "start": "22:00",
            "end": "08:00",
            "timezone": "UTC",
        }
        errors = PreferenceValidator._validate_quiet_hours(quiet_hours)
        assert errors == []

    def test_validate_quiet_hours_not_dict(self) -> None:
        """Test validation when quiet_hours is not a dictionary."""
        quiet_hours = "not_a_dict"
        errors = PreferenceValidator._validate_quiet_hours(quiet_hours)
        assert len(errors) == 1
        assert "must be a dictionary" in errors[0]

    def test_validate_quiet_hours_enabled_invalid(self) -> None:
        """Test validation of invalid enabled flag."""
        quiet_hours = {"enabled": "yes"}
        errors = PreferenceValidator._validate_quiet_hours(quiet_hours)
        assert len(errors) == 1
        assert "enabled must be boolean" in errors[0].lower()

    def test_validate_quiet_hours_invalid_times(self) -> None:
        """Test validation of invalid time formats."""
        quiet_hours = {
            "start": "25:00",  # Invalid hour
            "end": "not_time",  # Invalid format
        }
        errors = PreferenceValidator._validate_quiet_hours(quiet_hours)
        assert len(errors) == 2
        error_text = " ".join(errors)
        assert "hh:mm format" in error_text.lower()

    def test_validate_quiet_hours_invalid_timezone(self) -> None:
        """Test validation of invalid timezone."""
        quiet_hours = {"timezone": "Invalid/Timezone"}
        errors = PreferenceValidator._validate_quiet_hours(quiet_hours)
        assert len(errors) == 1
        assert "invalid timezone" in errors[0].lower()

    def test_validate_quiet_hours_same_times(self) -> None:
        """Test validation when start and end times are the same."""
        quiet_hours = {"start": "12:00", "end": "12:00"}
        errors = PreferenceValidator._validate_quiet_hours(quiet_hours)
        assert len(errors) == 1
        assert "cannot be the same" in errors[0].lower()

    def test_validate_quiet_hours_partial_valid(self) -> None:
        """Test validation of partial quiet hours configuration."""
        # Only enabled
        errors1 = PreferenceValidator._validate_quiet_hours({"enabled": True})
        assert errors1 == []

        # Only start time
        errors2 = PreferenceValidator._validate_quiet_hours({"start": "22:00"})
        assert errors2 == []

        # Only timezone
        errors3 = PreferenceValidator._validate_quiet_hours({"timezone": "UTC"})
        assert errors3 == []


class TestValidateTimeString:
    """Test time string validation."""

    def test_validate_time_string_valid(self) -> None:
        """Test validation of valid time strings."""
        valid_times = ["00:00", "12:00", "23:59", "09:30", "15:45"]
        for time_str in valid_times:
            errors = PreferenceValidator._validate_time_string(time_str, "Test time")
            assert errors == []

    def test_validate_time_string_not_string(self) -> None:
        """Test validation when time is not a string."""
        for invalid_time in [123, True, [], None]:
            errors = PreferenceValidator._validate_time_string(
                invalid_time, "Test time"
            )
            assert len(errors) == 1
            assert "must be a string" in errors[0]

    def test_validate_time_string_invalid_formats(self) -> None:
        """Test validation of invalid time formats."""
        invalid_times = [
            "25:00",  # Invalid hour
            "12:60",  # Invalid minute
            "12",  # Missing minute
            "12:30:45",  # Too many parts
            "not_time",  # Not a time
            "12:ab",  # Non-numeric minute
            "-1:30",  # Negative hour
            "12:-5",  # Negative minute
        ]

        for invalid_time in invalid_times:
            errors = PreferenceValidator._validate_time_string(
                invalid_time, "Test time"
            )
            assert len(errors) == 1
            assert "hh:mm format" in errors[0].lower()


class TestParseTime:
    """Test time parsing functionality."""

    def test_parse_time_valid(self) -> None:
        """Test parsing of valid time strings."""
        test_cases = [
            ("00:00", time(0, 0)),
            ("12:00", time(12, 0)),
            ("23:59", time(23, 59)),
            ("09:30", time(9, 30)),
            ("15:45", time(15, 45)),
        ]

        for time_str, expected_time in test_cases:
            result = PreferenceValidator._parse_time(time_str)
            assert result == expected_time

    def test_parse_time_invalid_format(self) -> None:
        """Test parsing of invalid time formats."""
        invalid_times = [
            "12",  # Missing minute
            "12:30:45",  # Too many parts
            "not_time",  # Not a time
            "25:00",  # Invalid hour
            "12:60",  # Invalid minute
            "-1:30",  # Negative hour
            "12:-5",  # Negative minute
        ]

        for invalid_time in invalid_times:
            with pytest.raises(ValueError):
                PreferenceValidator._parse_time(invalid_time)


class TestValidateFrequencyLimits:
    """Test frequency limits validation."""

    def test_validate_frequency_limits_valid(self) -> None:
        """Test validation of valid frequency limits."""
        limits = {"status_update": 5, "daily_summary": 1, "analysis_complete": 10}
        errors = PreferenceValidator._validate_frequency_limits(limits)
        assert errors == []

    def test_validate_frequency_limits_not_dict(self) -> None:
        """Test validation when limits is not a dictionary."""
        limits = "not_a_dict"
        errors = PreferenceValidator._validate_frequency_limits(limits)
        assert len(errors) == 1
        assert "must be a dictionary" in errors[0]

    def test_validate_frequency_limits_non_integer(self) -> None:
        """Test validation with non-integer limits."""
        limits = {
            "status_update": "five",
            "daily_summary": 1.5,
            "analysis_complete": True,
        }
        errors = PreferenceValidator._validate_frequency_limits(limits)
        assert len(errors) == 3
        assert all("must be an integer" in error for error in errors)

    def test_validate_frequency_limits_negative(self) -> None:
        """Test validation with negative limits."""
        limits = {
            "status_update": -1,
            "daily_summary": -5,
            "analysis_complete": 10,  # Valid for comparison
        }
        errors = PreferenceValidator._validate_frequency_limits(limits)
        assert len(errors) == 2
        assert all("cannot be negative" in error for error in errors)

    def test_validate_frequency_limits_exceeds_maximum(self) -> None:
        """Test validation when limits exceed maximum allowed."""
        limits = {
            "status_update": 50,  # Max is 10
            "daily_summary": 5,  # Max is 1
            "default_type": 150,  # Uses default max of 100
        }
        errors = PreferenceValidator._validate_frequency_limits(limits)
        assert len(errors) == 3
        assert all("exceeds maximum" in error for error in errors)

    def test_validate_frequency_limits_critical_alert_no_limit(self) -> None:
        """Test that critical_alert has no limit (max = 0 means no limit)."""
        limits = {"critical_alert": 1000}  # Very high value
        errors = PreferenceValidator._validate_frequency_limits(limits)
        assert errors == []  # Should not error as critical_alert has no limit

    def test_validate_frequency_limits_mixed_valid_invalid(self) -> None:
        """Test validation with mix of valid and invalid limits."""
        limits = {
            "status_update": 5,  # Valid
            "daily_summary": -1,  # Negative
            "analysis_complete": "not_int",  # Non-integer
            "weekly_report": 10,  # Exceeds max of 1
            "critical_alert": 1000,  # Valid (no limit)
        }
        errors = PreferenceValidator._validate_frequency_limits(limits)
        assert len(errors) == 3  # Three invalid items


class TestValidateExcludedTypes:
    """Test excluded types validation."""

    def test_validate_excluded_types_valid_list(self) -> None:
        """Test validation of valid excluded types list."""
        excluded_types = ["weekly_report", "daily_summary", "status_update"]
        errors = PreferenceValidator._validate_excluded_types(excluded_types)
        assert errors == []

    def test_validate_excluded_types_valid_set(self) -> None:
        """Test validation of valid excluded types set."""
        excluded_types = {"weekly_report", "daily_summary", "status_update"}
        errors = PreferenceValidator._validate_excluded_types(excluded_types)
        assert errors == []

    def test_validate_excluded_types_invalid_type(self) -> None:
        """Test validation when excluded_types is not list or set."""
        for invalid_types in ["not_list", 123, {"key": "value"}, None]:
            errors = PreferenceValidator._validate_excluded_types(invalid_types)
            assert len(errors) == 1
            assert "must be a list or set" in errors[0]

    def test_validate_excluded_types_critical_excluded(self) -> None:
        """Test validation when critical types are excluded."""
        excluded_types = ["critical_alert", "incident_escalation", "daily_summary"]
        errors = PreferenceValidator._validate_excluded_types(excluded_types)
        assert len(errors) == 1
        assert "cannot exclude critical notification types" in errors[0].lower()
        assert "critical_alert" in errors[0]
        assert "incident_escalation" in errors[0]

    def test_validate_excluded_types_empty(self) -> None:
        """Test validation of empty excluded types."""
        errors1 = PreferenceValidator._validate_excluded_types([])
        assert errors1 == []

        errors2 = PreferenceValidator._validate_excluded_types(set())
        assert errors2 == []


class TestValidateQuietHoursLogic:
    """Test quiet hours logic validation."""

    def test_validate_quiet_hours_logic_valid_same_day(self) -> None:
        """Test validation of valid quiet hours within same day."""
        start_time = time(22, 0)  # 10:00 PM
        end_time = time(23, 30)  # 11:30 PM
        timezone = "UTC"

        is_valid, error = PreferenceValidator.validate_quiet_hours_logic(
            start_time, end_time, timezone
        )
        assert is_valid is True
        assert error is None

    def test_validate_quiet_hours_logic_valid_span_midnight(self) -> None:
        """Test validation of valid quiet hours spanning midnight."""
        start_time = time(22, 0)  # 10:00 PM
        end_time = time(8, 0)  # 8:00 AM next day
        timezone = "US/Eastern"

        is_valid, error = PreferenceValidator.validate_quiet_hours_logic(
            start_time, end_time, timezone
        )
        assert is_valid is True
        assert error is None

    def test_validate_quiet_hours_logic_same_times(self) -> None:
        """Test validation when start and end times are the same."""
        start_time = time(12, 0)
        end_time = time(12, 0)
        timezone = "UTC"

        is_valid, error = PreferenceValidator.validate_quiet_hours_logic(
            start_time, end_time, timezone
        )
        assert is_valid is False
        assert error is not None and "cannot be the same" in error.lower()

    def test_validate_quiet_hours_logic_too_long_same_day(self) -> None:
        """Test validation when quiet hours exceed 20 hours (same day)."""
        start_time = time(1, 0)  # 1:00 AM
        end_time = time(23, 0)  # 11:00 PM (22 hours)
        timezone = "UTC"

        is_valid, error = PreferenceValidator.validate_quiet_hours_logic(
            start_time, end_time, timezone
        )
        assert is_valid is False
        assert error is not None and "cannot exceed 20 hours" in error.lower()

    def test_validate_quiet_hours_logic_too_long_span_midnight(self) -> None:
        """Test validation when quiet hours exceed 20 hours (spanning midnight)."""
        start_time = time(23, 0)  # 11:00 PM
        end_time = time(22, 0)  # 10:00 PM next day (23 hours)
        timezone = "UTC"

        is_valid, error = PreferenceValidator.validate_quiet_hours_logic(
            start_time, end_time, timezone
        )
        assert is_valid is False
        assert error is not None and "cannot exceed 20 hours" in error.lower()

    def test_validate_quiet_hours_logic_exactly_20_hours(self) -> None:
        """Test validation when quiet hours are exactly 20 hours."""
        start_time = time(2, 0)  # 2:00 AM
        end_time = time(22, 0)  # 10:00 PM (20 hours)
        timezone = "UTC"

        is_valid, error = PreferenceValidator.validate_quiet_hours_logic(
            start_time, end_time, timezone
        )
        assert is_valid is True
        assert error is None

    def test_validate_quiet_hours_logic_invalid_timezone(self) -> None:
        """Test validation with invalid timezone."""
        start_time = time(22, 0)
        end_time = time(8, 0)
        timezone = "Invalid/Timezone"

        is_valid, error = PreferenceValidator.validate_quiet_hours_logic(
            start_time, end_time, timezone
        )
        assert is_valid is False
        assert error is not None and "invalid timezone" in error.lower()

    def test_validate_quiet_hours_logic_various_timezones(self) -> None:
        """Test validation with various valid timezones."""
        start_time = time(22, 0)
        end_time = time(8, 0)

        valid_timezones = ["UTC", "US/Eastern", "Europe/London", "Asia/Tokyo"]

        for timezone in valid_timezones:
            is_valid, error = PreferenceValidator.validate_quiet_hours_logic(
                start_time, end_time, timezone
            )
            assert is_valid is True, f"Failed for timezone: {timezone}"
            assert error is None

    def test_validate_quiet_hours_logic_with_minutes(self) -> None:
        """Test validation with minutes in times."""
        start_time = time(22, 30)  # 10:30 PM
        end_time = time(8, 15)  # 8:15 AM
        timezone = "UTC"

        is_valid, error = PreferenceValidator.validate_quiet_hours_logic(
            start_time, end_time, timezone
        )
        assert is_valid is True
        assert error is None


class TestSuggestPreferences:
    """Test preference suggestion functionality."""

    def test_suggest_preferences_default_role(self) -> None:
        """Test suggestion for default/unknown role."""
        preferences = PreferenceValidator.suggest_preferences("unknown_role")

        # Check base structure
        assert "channels" in preferences
        assert "severity_threshold" in preferences
        assert "quiet_hours" in preferences
        assert "frequency_limits" in preferences
        assert "excluded_types" in preferences

        # Check default values
        assert preferences["severity_threshold"] == "medium"
        assert preferences["channels"]["email"] is True
        assert preferences["channels"]["slack"] is True
        assert preferences["channels"]["sms"] is False
        assert preferences["channels"]["webhook"] is False

        # Check quiet hours
        quiet_hours = preferences["quiet_hours"]
        assert quiet_hours["enabled"] is True
        assert quiet_hours["start"] == "22:00"
        assert quiet_hours["end"] == "08:00"
        assert quiet_hours["timezone"] == "UTC"

        # Check default empty collections
        assert preferences["frequency_limits"] == {}
        assert preferences["excluded_types"] == []

    def test_suggest_preferences_executive_role(self) -> None:
        """Test suggestion for executive role."""
        preferences = PreferenceValidator.suggest_preferences("executive")

        # Executive-specific adjustments
        assert preferences["severity_threshold"] == "high"
        assert preferences["channels"]["sms"] is True  # Enabled for executives

        # Check frequency limits
        assert preferences["frequency_limits"]["status_update"] == 1
        assert preferences["frequency_limits"]["daily_summary"] == 1
        assert preferences["frequency_limits"]["weekly_report"] == 1

        # Other defaults should remain
        assert preferences["channels"]["email"] is True
        assert preferences["quiet_hours"]["enabled"] is True

    def test_suggest_preferences_incident_responder_role(self) -> None:
        """Test suggestion for incident responder role."""
        preferences = PreferenceValidator.suggest_preferences("incident_responder")

        # Incident responder specific adjustments
        assert (
            preferences["severity_threshold"] == "low"
        )  # Low threshold for all alerts
        assert preferences["channels"]["sms"] is True  # SMS enabled for urgency
        assert preferences["quiet_hours"]["enabled"] is False  # No quiet hours

        # Other channels should remain default
        assert preferences["channels"]["email"] is True
        assert preferences["channels"]["slack"] is True

    def test_suggest_preferences_manager_role(self) -> None:
        """Test suggestion for manager role."""
        preferences = PreferenceValidator.suggest_preferences("manager")

        # Manager-specific adjustments
        assert preferences["severity_threshold"] == "medium"

        # Check frequency limits
        assert preferences["frequency_limits"]["status_update"] == 5
        assert preferences["frequency_limits"]["analysis_complete"] == 10

        # SMS should remain disabled by default for managers
        assert preferences["channels"]["sms"] is False
        assert preferences["quiet_hours"]["enabled"] is True

    def test_suggest_preferences_with_work_hours(self) -> None:
        """Test suggestion with work hours adjustment."""
        work_hours = (9, 17)  # 9 AM to 5 PM
        preferences = PreferenceValidator.suggest_preferences("manager", work_hours)

        # Quiet hours should be adjusted based on work hours
        quiet_hours = preferences["quiet_hours"]
        assert quiet_hours["start"] == "19:00"  # end_hour + 2 (17 + 2)
        assert quiet_hours["end"] == "08:00"  # start_hour - 1 (9 - 1)

        # Other preferences should remain as per role
        assert preferences["severity_threshold"] == "medium"

    def test_suggest_preferences_with_edge_work_hours(self) -> None:
        """Test suggestion with edge case work hours."""
        # Work hours that would create edge cases
        work_hours = (0, 23)  # Midnight to 11 PM
        preferences = PreferenceValidator.suggest_preferences("executive", work_hours)

        quiet_hours = preferences["quiet_hours"]
        assert quiet_hours["start"] == "01:00"  # 23 + 2 = 25, but formatted as 01:00
        assert quiet_hours["end"] == "23:00"  # 0 - 1 = -1, but handled as 23:00

        # Role-specific preferences should still apply
        assert preferences["severity_threshold"] == "high"
        assert preferences["channels"]["sms"] is True

    def test_suggest_preferences_work_hours_early_shift(self) -> None:
        """Test suggestion for early shift work hours."""
        work_hours = (6, 14)  # 6 AM to 2 PM
        preferences = PreferenceValidator.suggest_preferences(
            "incident_responder", work_hours
        )

        quiet_hours = preferences["quiet_hours"]
        assert quiet_hours["start"] == "16:00"  # 14 + 2
        assert quiet_hours["end"] == "05:00"  # 6 - 1

        # Role-specific: quiet hours should still be disabled for incident responders
        # But the calculation should still happen for the data structure
        assert preferences["quiet_hours"]["enabled"] is False

    def test_suggest_preferences_work_hours_late_shift(self) -> None:
        """Test suggestion for late shift work hours."""
        work_hours = (15, 23)  # 3 PM to 11 PM
        preferences = PreferenceValidator.suggest_preferences("manager", work_hours)

        quiet_hours = preferences["quiet_hours"]
        assert quiet_hours["start"] == "01:00"  # 23 + 2 = 25 -> 01:00
        assert quiet_hours["end"] == "14:00"  # 15 - 1

    def test_suggest_preferences_return_type_validation(self) -> None:
        """Test that suggested preferences return valid structure."""
        for role in ["executive", "incident_responder", "manager", "unknown"]:
            preferences = PreferenceValidator.suggest_preferences(role)

            # Validate the returned preferences would pass validation
            is_valid, errors = PreferenceValidator.validate_preferences(preferences)
            assert is_valid is True, f"Invalid preferences for role {role}: {errors}"

            # Check required keys exist
            required_keys = [
                "channels",
                "severity_threshold",
                "quiet_hours",
                "frequency_limits",
                "excluded_types",
            ]
            for key in required_keys:
                assert key in preferences, f"Missing key {key} for role {role}"

    def test_suggest_preferences_channels_type_safety(self) -> None:
        """Test that channels modification is type-safe."""
        # This tests the isinstance checks in the suggest_preferences method
        preferences = PreferenceValidator.suggest_preferences("executive")

        # Verify channels is a dict and modifications were applied correctly
        assert isinstance(preferences["channels"], dict)
        assert preferences["channels"]["sms"] is True

        # Test with incident_responder
        preferences2 = PreferenceValidator.suggest_preferences("incident_responder")
        assert isinstance(preferences2["channels"], dict)
        assert preferences2["channels"]["sms"] is True

    def test_suggest_preferences_quiet_hours_type_safety(self) -> None:
        """Test that quiet hours modification is type-safe."""
        preferences = PreferenceValidator.suggest_preferences("incident_responder")

        # Verify quiet_hours is a dict and modifications were applied correctly
        assert isinstance(preferences["quiet_hours"], dict)
        assert preferences["quiet_hours"]["enabled"] is False


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""

    def test_comprehensive_preference_validation(self) -> None:
        """Test comprehensive validation with complex preferences."""
        complex_preferences = {
            "channels": {"email": True, "slack": True, "sms": True, "webhook": False},
            "severity_threshold": "HIGH",  # Test case insensitivity
            "quiet_hours": {
                "enabled": True,
                "start": "23:30",
                "end": "07:45",
                "timezone": "Europe/London",
            },
            "frequency_limits": {
                "status_update": 8,
                "analysis_complete": 15,
                "daily_summary": 1,
                "critical_alert": 999,  # Should be allowed (no limit)
            },
            "excluded_types": ["weekly_report", "daily_summary"],
        }

        is_valid, errors = PreferenceValidator.validate_preferences(complex_preferences)
        assert is_valid is True
        assert errors == []

    def test_preference_validation_with_all_errors(self) -> None:
        """Test validation that triggers all error types."""
        invalid_preferences = {
            "channels": {
                "email": True,
                "invalid_channel": True,  # Invalid channel
                "slack": "not_boolean",  # Invalid type
                "sms": False,
                "webhook": False,  # All will be disabled except email
            },
            "severity_threshold": "super_critical",  # Invalid severity
            "quiet_hours": {
                "enabled": "yes",  # Invalid boolean
                "start": "25:70",  # Invalid time
                "end": "12:00",
                "timezone": "Moon/Crater",  # Invalid timezone
            },
            "frequency_limits": {
                "status_update": -5,  # Negative
                "daily_summary": "many",  # Non-integer
                "analysis_complete": 999,  # Exceeds maximum
            },
            "excluded_types": {
                "critical_alert",  # Set instead of list (should work)
                "incident_escalation",  # Critical type that shouldn't be excluded
            },
        }

        is_valid, errors = PreferenceValidator.validate_preferences(invalid_preferences)
        assert is_valid is False
        assert len(errors) >= 8  # Should have multiple errors from each category

        # Verify we get errors from each validation category
        error_text = " ".join(errors).lower()
        assert "invalid channel" in error_text
        assert "invalid severity threshold" in error_text
        assert "must be boolean" in error_text
        assert "hh:mm format" in error_text
        assert "invalid timezone" in error_text
        assert "cannot be negative" in error_text
        assert "must be an integer" in error_text
        assert "critical notification types" in error_text

    def test_suggested_preferences_all_roles_with_work_hours(self) -> None:
        """Test preference suggestions for all roles with various work hours."""
        roles = ["executive", "incident_responder", "manager", "analyst"]
        work_hours_options = [
            None,
            (9, 17),  # Standard
            (0, 8),  # Night shift
            (16, 23),  # Evening shift
            (6, 14),  # Early shift
        ]

        for role in roles:
            for work_hours in work_hours_options:
                preferences = PreferenceValidator.suggest_preferences(role, work_hours)

                # Each suggestion should be valid
                is_valid, errors = PreferenceValidator.validate_preferences(preferences)
                assert (
                    is_valid is True
                ), f"Invalid for role {role}, hours {work_hours}: {errors}"

                # Basic structure checks
                assert isinstance(preferences["channels"], dict)
                assert isinstance(preferences["quiet_hours"], dict)
                assert isinstance(preferences["frequency_limits"], dict)
                assert isinstance(preferences["excluded_types"], list)
                assert (
                    preferences["severity_threshold"]
                    in PreferenceValidator.VALID_SEVERITIES
                )

    def test_edge_case_empty_preferences(self) -> None:
        """Test edge cases with empty or minimal preferences."""
        # Empty dict should be valid
        is_valid, errors = PreferenceValidator.validate_preferences({})
        assert is_valid is True
        assert errors == []

        # Minimal valid preferences
        minimal = {"channels": {"email": True}, "severity_threshold": "low"}
        is_valid, errors = PreferenceValidator.validate_preferences(minimal)
        assert is_valid is True
        assert errors == []

    def test_boundary_time_values(self) -> None:
        """Test boundary values for time validation."""
        boundary_times = [
            ("00:00", True),  # Midnight
            ("23:59", True),  # Last minute of day
            ("12:00", True),  # Noon
            ("24:00", False),  # Invalid hour
            ("12:60", False),  # Invalid minute
            ("00:01", True),  # First minute after midnight
            ("23:58", True),  # Almost end of day
        ]

        for time_str, should_be_valid in boundary_times:
            errors = PreferenceValidator._validate_time_string(time_str, "Test")
            if should_be_valid:
                assert errors == [], f"Expected {time_str} to be valid"
            else:
                assert len(errors) > 0, f"Expected {time_str} to be invalid"

    def test_frequency_limits_boundary_values(self) -> None:
        """Test boundary values for frequency limits."""
        # Test limits at boundaries
        boundary_tests = [
            ({"status_update": 0}, True),  # Zero is valid
            ({"status_update": 10}, True),  # At maximum
            ({"status_update": 11}, False),  # Exceeds maximum
            ({"daily_summary": 1}, True),  # At maximum
            ({"daily_summary": 2}, False),  # Exceeds maximum
            ({"critical_alert": 9999}, True),  # No limit for critical
        ]

        for limits, should_be_valid in boundary_tests:
            errors = PreferenceValidator._validate_frequency_limits(limits)
            if should_be_valid:
                assert errors == [], f"Expected {limits} to be valid"
            else:
                assert len(errors) > 0, f"Expected {limits} to be invalid"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
