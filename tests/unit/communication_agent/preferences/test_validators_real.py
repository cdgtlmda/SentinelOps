"""REAL tests for communication_agent/preferences/validators.py - Testing validation logic."""

from typing import Any, Dict

# Import the actual production code
from src.communication_agent.preferences.validators import PreferenceValidator


class TestPreferenceValidatorReal:
    """Test PreferenceValidator with REAL validation logic - NO MOCKS."""

    def test_real_validate_preferences_valid_complete(self) -> None:
        """Test REAL validation of complete valid preferences."""
        updates = {
            "channels": {
                "email": {
                    "enabled": True,
                    "address": "user@example.com",
                    "verified": True,
                },
                "slack": {
                    "enabled": True,
                    "webhook_url": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
                    "channel": "#alerts",
                },
            },
            "severity_threshold": "medium",
            "quiet_hours": {
                "enabled": True,
                "start": "22:00",
                "end": "07:00",
                "timezone": "US/Eastern",
            },
            "frequency_limits": {
                "incident_detected": 30,
                "status_update": 5,
                "daily_summary": 1,
            },
            "excluded_types": ["system_health", "test_notification"],
        }

        # Validate real preferences
        is_valid, errors = PreferenceValidator.validate_preferences(updates)

        # Should be valid
        assert is_valid is True
        assert len(errors) == 0
        print("\nValid preferences passed all validation checks")

    def test_real_validate_channels_invalid_email(self) -> None:
        """Test REAL validation of invalid email channel."""
        updates = {
            "channels": {
                "email": {
                    "enabled": True,
                    "address": "invalid-email",  # Invalid email format
                    "verified": True,
                }
            }
        }

        # Validate
        is_valid, errors = PreferenceValidator.validate_preferences(updates)

        # Should fail
        assert is_valid is False
        assert len(errors) > 0
        assert any("email" in err.lower() for err in errors)
        print(f"\nInvalid email detected: {errors}")

    def test_real_validate_channels_missing_required_fields(self) -> None:
        """Test REAL validation with missing required channel fields."""
        updates = {
            "channels": {
                "slack": {
                    "enabled": True
                    # Missing webhook_url and channel
                }
            }
        }

        # Validate
        is_valid, errors = PreferenceValidator.validate_preferences(updates)

        # Should fail
        assert is_valid is False
        assert any("webhook_url" in err for err in errors)
        print(f"\nMissing required fields: {errors}")

    def test_real_validate_severity_threshold_valid(self) -> None:
        """Test REAL validation of valid severity thresholds."""
        valid_severities = ["low", "medium", "high", "critical"]

        for severity in valid_severities:
            updates = {"severity_threshold": severity}
            is_valid, errors = PreferenceValidator.validate_preferences(updates)

            assert is_valid is True
            assert len(errors) == 0

        print(f"\nAll {len(valid_severities)} valid severities passed")

    def test_real_validate_severity_threshold_invalid(self) -> None:
        """Test REAL validation of invalid severity threshold."""
        updates = {"severity_threshold": "extreme"}  # Invalid severity

        # Validate
        is_valid, errors = PreferenceValidator.validate_preferences(updates)

        # Should fail
        assert is_valid is False
        assert any("severity" in err.lower() for err in errors)
        assert any("extreme" in err for err in errors)
        print(f"\nInvalid severity rejected: {errors}")

    def test_real_validate_quiet_hours_valid(self) -> None:
        """Test REAL validation of valid quiet hours configuration."""
        updates = {
            "quiet_hours": {
                "enabled": True,
                "start": "22:30",
                "end": "06:45",
                "timezone": "Europe/London",
            }
        }

        # Validate
        is_valid, errors = PreferenceValidator.validate_preferences(updates)

        # Should be valid
        assert is_valid is True
        assert len(errors) == 0
        print("\nQuiet hours validated successfully")

    def test_real_validate_quiet_hours_invalid_time_format(self) -> None:
        """Test REAL validation of invalid time format in quiet hours."""
        updates = {
            "quiet_hours": {
                "enabled": True,
                "start": "10:30 PM",  # Invalid format (should be 24-hour)
                "end": "6 AM",  # Invalid format
                "timezone": "US/Pacific",
            }
        }

        # Validate
        is_valid, errors = PreferenceValidator.validate_preferences(updates)

        # Should fail
        assert is_valid is False
        assert any("time format" in err or "HH:MM" in err for err in errors)
        print(f"\nInvalid time format detected: {errors}")

    def test_real_validate_quiet_hours_invalid_timezone(self) -> None:
        """Test REAL validation of invalid timezone."""
        updates = {
            "quiet_hours": {
                "enabled": True,
                "start": "22:00",
                "end": "07:00",
                "timezone": "Mars/Olympus_Mons",  # Invalid timezone
            }
        }

        # Validate
        is_valid, errors = PreferenceValidator.validate_preferences(updates)

        # Should fail
        assert is_valid is False
        assert any("timezone" in err.lower() for err in errors)
        print(f"\nInvalid timezone rejected: {errors}")

    def test_real_validate_frequency_limits_valid(self) -> None:
        """Test REAL validation of valid frequency limits."""
        updates = {
            "frequency_limits": {
                "incident_detected": 25,  # Within limit of 50
                "analysis_complete": 15,  # Within limit of 20
                "status_update": 8,  # Within limit of 10
                "daily_summary": 1,  # Exactly at limit
                "critical_alert": 999,  # No limit for critical
            }
        }

        # Validate
        is_valid, errors = PreferenceValidator.validate_preferences(updates)

        # Should be valid
        assert is_valid is True
        assert len(errors) == 0
        print("\nFrequency limits within bounds")

    def test_real_validate_frequency_limits_exceeded(self) -> None:
        """Test REAL validation when frequency limits are exceeded."""
        updates = {
            "frequency_limits": {
                "incident_detected": 100,  # Exceeds limit of 50
                "status_update": 20,  # Exceeds limit of 10
                "daily_summary": 5,  # Exceeds limit of 1
            }
        }

        # Validate
        is_valid, errors = PreferenceValidator.validate_preferences(updates)

        # Should fail
        assert is_valid is False
        assert len(errors) >= 3  # At least 3 exceeded limits
        assert any("incident_detected" in err and "50" in err for err in errors)
        assert any("status_update" in err and "10" in err for err in errors)
        assert any("daily_summary" in err and "1" in err for err in errors)
        print(f"\nExceeded limits detected: {len(errors)} errors")

    def test_real_validate_frequency_limits_negative(self) -> None:
        """Test REAL validation of negative frequency limits."""
        updates = {
            "frequency_limits": {
                "incident_detected": -1,  # Negative value
                "status_update": 0,  # Zero is valid
            }
        }

        # Validate
        is_valid, errors = PreferenceValidator.validate_preferences(updates)

        # Should fail for negative
        assert is_valid is False
        assert any("negative" in err.lower() or "-1" in err for err in errors)
        print(f"\nNegative frequency rejected: {errors}")

    def test_real_validate_excluded_types_valid(self) -> None:
        """Test REAL validation of valid excluded notification types."""
        updates = {
            "excluded_types": ["system_health", "test_notification", "daily_summary"]
        }

        # Validate
        is_valid, errors = PreferenceValidator.validate_preferences(updates)

        # Should be valid
        assert is_valid is True
        assert len(errors) == 0
        print("\nExcluded types validated")

    def test_real_validate_excluded_types_invalid_format(self) -> None:
        """Test REAL validation of invalid excluded types format."""
        updates = {"excluded_types": "system_health"}  # Should be a list, not string

        # Validate
        is_valid, errors = PreferenceValidator.validate_preferences(updates)

        # Should fail
        assert is_valid is False
        assert any("list" in err.lower() for err in errors)
        print(f"\nInvalid format detected: {errors}")

    def test_real_validate_channels_slack_invalid_webhook(self) -> None:
        """Test REAL validation of invalid Slack webhook URL."""
        updates = {
            "channels": {
                "slack": {
                    "enabled": True,
                    "webhook_url": "not-a-url",  # Invalid URL
                    "channel": "#alerts",
                }
            }
        }

        # Validate
        is_valid, errors = PreferenceValidator.validate_preferences(updates)

        # Should fail
        assert is_valid is False
        assert any("webhook" in err.lower() or "url" in err.lower() for err in errors)
        print(f"\nInvalid webhook URL: {errors}")

    def test_real_validate_channels_sms_phone_number(self) -> None:
        """Test REAL validation of SMS channel phone numbers."""
        test_cases = [
            ("+1234567890", True),  # Valid international format
            ("+12345678901", True),  # Valid US number
            ("1234567890", False),  # Missing + prefix
            ("+123", False),  # Too short
            ("not-a-number", False),  # Invalid format
            ("+1 234 567 8901", False),  # Spaces not allowed
        ]

        for phone, should_be_valid in test_cases:
            updates = {"channels": {"sms": {"enabled": True, "phone_number": phone}}}

            is_valid, errors = PreferenceValidator.validate_preferences(updates)

            if should_be_valid:
                assert is_valid is True
                assert len(errors) == 0
            else:
                assert is_valid is False
                assert len(errors) > 0

        print(f"\nPhone number validation tested for {len(test_cases)} cases")

    def test_real_validate_multiple_errors(self) -> None:
        """Test REAL validation with multiple errors."""
        updates = {
            "channels": {"email": {"enabled": True, "address": "bad-email"}},  # Invalid
            "severity_threshold": "ultra",  # Invalid
            "quiet_hours": {
                "enabled": True,
                "start": "25:00",  # Invalid time
                "end": "07:00",
                "timezone": "Invalid/Zone",  # Invalid timezone
            },
            "frequency_limits": {"incident_detected": 200},  # Exceeds limit
        }

        # Validate
        is_valid, errors = PreferenceValidator.validate_preferences(updates)

        # Should have multiple errors
        assert is_valid is False
        assert len(errors) >= 5  # At least 5 different errors

        # Check each type of error is present
        assert any("email" in err.lower() for err in errors)
        assert any("severity" in err.lower() for err in errors)
        assert any("time" in err.lower() for err in errors)
        assert any("timezone" in err.lower() for err in errors)
        assert any(
            "frequency" in err.lower() or "limit" in err.lower() for err in errors
        )

        print(f"\nMultiple validation errors detected: {len(errors)} total")

    def test_real_validate_empty_updates(self) -> None:
        """Test REAL validation with empty updates."""
        updates: Dict[str, Any] = {}

        # Validate
        is_valid, errors = PreferenceValidator.validate_preferences(updates)

        # Empty updates should be valid (no changes)
        assert is_valid is True
        assert len(errors) == 0
        print("\nEmpty updates validated as no-op")

    def test_real_validate_partial_updates(self) -> None:
        """Test REAL validation with partial preference updates."""
        # Only updating severity threshold
        updates1 = {"severity_threshold": "high"}
        is_valid1, errors1 = PreferenceValidator.validate_preferences(updates1)
        assert is_valid1 is True
        assert len(errors1) == 0

        # Only updating frequency limits
        updates2 = {"frequency_limits": {"status_update": 3}}
        is_valid2, errors2 = PreferenceValidator.validate_preferences(updates2)
        assert is_valid2 is True
        assert len(errors2) == 0

        # Only updating quiet hours
        updates3 = {"quiet_hours": {"enabled": False}}  # Disabling quiet hours
        is_valid3, errors3 = PreferenceValidator.validate_preferences(updates3)
        assert is_valid3 is True
        assert len(errors3) == 0

        print("\nPartial updates validated successfully")
