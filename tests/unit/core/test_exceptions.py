"""
Unit tests for common exceptions module.
"""

from src.common.exceptions import (
    ConfigurationError,
    ErrorCategory,
    ErrorSeverity,
    SentinelOpsError,
)


class TestSentinelOpsError:
    """Test base SentinelOpsError."""

    def test_basic_initialization(self) -> None:
        """Test basic exception initialization."""
        exc = SentinelOpsError("Test error message")

        assert str(exc) == "Test error message"
        assert exc.message == "Test error message"
        assert exc.details == {}
        assert exc.error_code == "SENTINEL_ERROR"
        assert exc.category == ErrorCategory.UNKNOWN
        assert exc.severity == ErrorSeverity.MEDIUM

    def test_initialization_with_details(self) -> None:
        """Test exception initialization with details."""
        details = {"error_code": "E001", "context": "test_function"}
        exc = SentinelOpsError("Test error", details=details)

        assert exc.message == "Test error"
        assert exc.details == details
        assert exc.details["error_code"] == "E001"


class TestConfigurationError:
    """Test ConfigurationError."""

    def test_configuration_error(self) -> None:
        """Test ConfigurationError attributes."""
        exc = ConfigurationError("Invalid config")

        assert exc.category == ErrorCategory.CONFIGURATION
        assert exc.severity == ErrorSeverity.HIGH
        assert exc.error_code == "CONFIG_ERROR"
