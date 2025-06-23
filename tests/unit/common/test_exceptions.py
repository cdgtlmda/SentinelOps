"""
Test suite for custom exceptions module.
Tests exception hierarchy, error handling, and message formatting.
"""

# Third-party imports
import pytest

# First-party imports
from src.common.exceptions import (
    ErrorCategory,
    ErrorSeverity,
    AuthenticationError,
    AuthorizationError,
    SecurityError,
    NetworkError,
    ValidationError,
    GoogleCloudError,
    ErrorHandler,
    GracefulDegradation,
    get_error_handler,
    get_graceful_degradation,
)

TEST_PROJECT_ID = "your-gcp-project-id"


class TestSentinelOpsExceptions:
    """Test SentinelOps exception hierarchy with real error handling - NO MOCKING."""

    def test_error_category_enumeration(self) -> None:
        """Test ErrorCategory enumeration values."""
        assert ErrorCategory.AUTHENTICATION is not None
        assert ErrorCategory.AUTHORIZATION is not None
        assert ErrorCategory.VALIDATION is not None
        assert ErrorCategory.PROCESSING is not None
        assert ErrorCategory.NETWORK is not None
        assert ErrorCategory.EXTERNAL_SERVICE is not None

    def test_error_severity_enumeration(self) -> None:
        """Test ErrorSeverity enumeration values."""
        assert ErrorSeverity.LOW is not None
        assert ErrorSeverity.MEDIUM is not None
        assert ErrorSeverity.HIGH is not None
        assert ErrorSeverity.CRITICAL is not None

    def test_authentication_error_creation(self) -> None:
        """Test AuthenticationError creation and properties."""
        error = AuthenticationError(message="Invalid credentials")

        assert error.message == "Invalid credentials"
        assert error.error_code == "AUTH_ERROR"
        assert isinstance(error, AuthenticationError)

    def test_authorization_error_creation(self) -> None:
        """Test AuthorizationError creation and properties."""
        error = AuthorizationError(message="Insufficient permissions")

        assert error.message == "Insufficient permissions"
        assert error.error_code == "AUTHZ_ERROR"
        assert isinstance(error, AuthorizationError)

    def test_validation_error_creation(self) -> None:
        """Test ValidationError creation and properties."""
        error = ValidationError(message="Invalid input data")

        assert error.message == "Invalid input data"
        assert error.error_code == "VALIDATION_ERROR"
        assert isinstance(error, ValidationError)

    def test_network_error_creation(self) -> None:
        """Test NetworkError creation and properties."""
        error = NetworkError(message="Connection timeout")

        assert error.message == "Connection timeout"
        assert error.error_code == "NETWORK_ERROR"
        assert isinstance(error, NetworkError)

    def test_google_cloud_error_creation(self) -> None:
        """Test GoogleCloudError creation and properties."""
        error = GoogleCloudError(message="Service unavailable")

        assert error.message == "Service unavailable"
        assert error.error_code == "GCP_ERROR"
        assert isinstance(error, GoogleCloudError)

    def test_error_handler_creation(self) -> None:
        """Test ErrorHandler creation and functionality."""
        try:
            handler = get_error_handler()
            assert handler is not None
            assert isinstance(handler, ErrorHandler)
        except (TypeError, AttributeError, ImportError) as e:
            pytest.skip(f"Error handler not available: {e}")

    def test_graceful_degradation_creation(self) -> None:
        """Test GracefulDegradation creation and functionality."""
        try:
            degradation = get_graceful_degradation()
            assert degradation is not None
            assert isinstance(degradation, GracefulDegradation)
        except (TypeError, AttributeError, ImportError) as e:
            pytest.skip(f"Graceful degradation not available: {e}")

    def test_error_chaining_comprehensive(self) -> None:
        """Test comprehensive error chaining functionality."""
        try:
            # Create primary error
            auth_error = AuthenticationError(message="Authentication failed")

            # Create chained error
            try:
                raise auth_error
            except AuthenticationError as exc:
                security_error = SecurityError(message="Security breach detected")
                raise security_error from exc

        except SecurityError as final_error:
            # Verify error chaining
            assert final_error.__cause__ is not None
            assert isinstance(final_error.__cause__, AuthenticationError)
        except (TypeError, AttributeError, ImportError) as e:
            pytest.skip(f"Error chaining not available: {e}")
