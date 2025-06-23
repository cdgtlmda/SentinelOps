"""
Tests for SMS/Twilio configuration - real implementation, no mocks.
"""

import os

from src.communication_agent.config.sms_config import get_twilio_config
from src.communication_agent.services.sms_service import TwilioConfig


class TestGetTwilioConfig:
    """Test the get_twilio_config function with real environment variables."""

    def setup_method(self) -> None:
        """Save original environment variables before each test."""
        self.original_env = {}
        env_vars = [
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN",
            "TWILIO_FROM_NUMBER",
            "TWILIO_STATUS_CALLBACK_URL",
            "TWILIO_MESSAGING_SERVICE_SID",
            "TWILIO_MAX_PRICE_PER_MESSAGE"
        ]
        for var in env_vars:
            self.original_env[var] = os.environ.get(var)

    def teardown_method(self) -> None:
        """Restore original environment variables after each test."""
        for var, value in self.original_env.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value

    def test_get_twilio_config_with_all_required_vars(self) -> None:
        """Test successful config loading with all required environment variables."""
        # Set required environment variables
        os.environ["TWILIO_ACCOUNT_SID"] = "ACtest123456789"
        os.environ["TWILIO_AUTH_TOKEN"] = "test_auth_token_123"
        os.environ["TWILIO_FROM_NUMBER"] = "+1234567890"

        config = get_twilio_config()

        assert config is not None
        assert isinstance(config, TwilioConfig)
        assert config.account_sid == "ACtest123456789"
        assert config.auth_token == "test_auth_token_123"
        assert config.from_number == "+1234567890"
        assert config.status_callback_url is None
        assert config.messaging_service_sid is None
        assert config.max_price_per_message == "0.10"

    def test_get_twilio_config_with_all_vars(self) -> None:
        """Test config loading with all environment variables including optional ones."""
        # Set all environment variables
        os.environ["TWILIO_ACCOUNT_SID"] = "ACprod987654321"
        os.environ["TWILIO_AUTH_TOKEN"] = "prod_auth_token_456"
        os.environ["TWILIO_FROM_NUMBER"] = "+9876543210"
        os.environ["TWILIO_STATUS_CALLBACK_URL"] = "https://example.com/twilio/status"
        os.environ["TWILIO_MESSAGING_SERVICE_SID"] = "MG123456789"
        os.environ["TWILIO_MAX_PRICE_PER_MESSAGE"] = "0.25"

        config = get_twilio_config()
        assert config is not None
        assert config.account_sid == "ACprod987654321"
        assert config.auth_token == "prod_auth_token_456"
        assert config.from_number == "+9876543210"
        assert config.status_callback_url == "https://example.com/twilio/status"
        assert config.messaging_service_sid == "MG123456789"
        assert config.max_price_per_message == "0.25"

    def test_get_twilio_config_missing_account_sid(self) -> None:
        """Test config returns None when account SID is missing."""
        # Set only some required variables
        os.environ["TWILIO_AUTH_TOKEN"] = "test_token"
        os.environ["TWILIO_FROM_NUMBER"] = "+1234567890"

        config = get_twilio_config()

        assert config is None

    def test_get_twilio_config_missing_auth_token(self) -> None:
        """Test config returns None when auth token is missing."""
        os.environ["TWILIO_ACCOUNT_SID"] = "ACtest123"
        os.environ["TWILIO_FROM_NUMBER"] = "+1234567890"

        config = get_twilio_config()

        assert config is None

    def test_get_twilio_config_missing_from_number(self) -> None:
        """Test config returns None when from number is missing."""
        os.environ["TWILIO_ACCOUNT_SID"] = "ACtest123"
        os.environ["TWILIO_AUTH_TOKEN"] = "test_token"
        config = get_twilio_config()

        assert config is None

    def test_get_twilio_config_no_env_vars(self) -> None:
        """Test config returns None when no environment variables are set."""
        # Clear all Twilio environment variables
        for var in ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER"]:
            os.environ.pop(var, None)

        config = get_twilio_config()

        assert config is None

    def test_get_twilio_config_from_number_without_plus(self) -> None:
        """Test config still works when from number doesn't have + prefix."""
        os.environ["TWILIO_ACCOUNT_SID"] = "ACtest123"
        os.environ["TWILIO_AUTH_TOKEN"] = "test_token"
        os.environ["TWILIO_FROM_NUMBER"] = "1234567890"  # Missing + prefix

        config = get_twilio_config()

        # Config should still be created (with a warning logged)
        assert config is not None
        assert config.from_number == "1234567890"

    def test_get_twilio_config_default_max_price(self) -> None:
        """Test default max price per message is set correctly."""
        os.environ["TWILIO_ACCOUNT_SID"] = "ACtest123"
        os.environ["TWILIO_AUTH_TOKEN"] = "test_token"
        os.environ["TWILIO_FROM_NUMBER"] = "+1234567890"        # Don't set TWILIO_MAX_PRICE_PER_MESSAGE
        os.environ.pop("TWILIO_MAX_PRICE_PER_MESSAGE", None)

        config = get_twilio_config()

        assert config is not None
        assert config.max_price_per_message == "0.10"  # Default value

    def test_get_twilio_config_empty_strings(self) -> None:
        """Test config returns None when required vars are empty strings."""
        os.environ["TWILIO_ACCOUNT_SID"] = ""
        os.environ["TWILIO_AUTH_TOKEN"] = "test_token"
        os.environ["TWILIO_FROM_NUMBER"] = "+1234567890"

        config = get_twilio_config()

        assert config is None

    def test_get_twilio_config_whitespace_values(self) -> None:
        """Test config accepts whitespace values (actual behavior)."""
        os.environ["TWILIO_ACCOUNT_SID"] = "ACtest123"
        os.environ["TWILIO_AUTH_TOKEN"] = "   "  # Only whitespace
        os.environ["TWILIO_FROM_NUMBER"] = "+1234567890"

        config = get_twilio_config()

        # The actual implementation doesn't strip whitespace
        assert config is not None
        assert config.auth_token == "   "
