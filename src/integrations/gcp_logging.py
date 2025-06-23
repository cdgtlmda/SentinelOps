"""
Google Cloud Logging integration for SentinelOps.
"""

import logging
import os
from typing import Any, List, Optional

from google.cloud import logging as cloud_logging
from google.cloud.logging.handlers import CloudLoggingHandler
from google.cloud.logging_v2.handlers import setup_logging as gcp_setup_logging

logger = logging.getLogger(__name__)


class GoogleCloudLoggingIntegration:
    """Integrates Python logging with Google Cloud Logging."""

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Google Cloud Logging integration.

        Args:
            project_id: Google Cloud project ID (uses default if None)
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.client: Optional[cloud_logging.Client] = None
        self.handler: Optional[CloudLoggingHandler] = None

    def setup(
        self, log_level: str = "INFO", excluded_loggers: Optional[List[str]] = None
    ) -> bool:
        """
        Set up Google Cloud Logging.

        Args:
            log_level: Minimum log level to send to Cloud Logging
            excluded_loggers: List of logger names to exclude

        Returns:
            True if setup successful, False otherwise
        """
        try:
            # Initialize Cloud Logging client
            self.client = cloud_logging.Client(
                project=self.project_id
            )  # type: ignore[no-untyped-call]

            # Create handler
            self.handler = CloudLoggingHandler(self.client, name="sentinelops")

            # Set handler level
            self.handler.setLevel(getattr(logging, log_level))

            # Excluded loggers (to prevent feedback loops)
            excluded = excluded_loggers or [
                "google.cloud",
                "google.auth",
                "google.api_core",
                "urllib3",
            ]

            # Setup logging with exclusions
            gcp_setup_logging(  # type: ignore[no-untyped-call]
                self.handler,
                excluded_loggers=excluded,
                log_level=getattr(logging, log_level),
            )

            logger.info(
                "Google Cloud Logging configured",
                extra={"project_id": self.project_id, "log_level": log_level},
            )

            return True

        except (ValueError, ImportError, AttributeError) as e:
            logger.error("Failed to setup Google Cloud Logging: %s", e)
            return False

    def log_structured(
        self, message: str, severity: str = "INFO", **kwargs: Any
    ) -> None:
        """
        Log a structured message to Cloud Logging.

        Args:
            message: Log message
            severity: Log severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            **kwargs: Additional structured data
        """
        if not self.client:
            logger.warning("Cloud Logging client not initialized")
            return

        try:
            # Get logger from client
            cloud_logger = self.client.logger("sentinelops")  # type: ignore[no-untyped-call]

            # Create structured log entry
            log_entry = {"message": message, "severity": severity, **kwargs}

            # Log to Cloud Logging
            cloud_logger.log_struct(log_entry, severity=severity)

        except (ValueError, ImportError, AttributeError) as e:
            logger.error("Failed to log to Cloud Logging: %s", e)


# Singleton instance
_GCP_LOGGING_INTEGRATION = None


def get_gcp_logging() -> GoogleCloudLoggingIntegration:
    """Get or create the Google Cloud Logging integration instance."""
    global _GCP_LOGGING_INTEGRATION  # pylint: disable=global-statement

    if _GCP_LOGGING_INTEGRATION is None:
        _GCP_LOGGING_INTEGRATION = GoogleCloudLoggingIntegration()

    return _GCP_LOGGING_INTEGRATION


def setup_cloud_logging(enabled: bool = True) -> bool:
    """
    Setup Cloud Logging based on environment.

    Args:
        enabled: Whether to enable Cloud Logging

    Returns:
        True if setup successful or disabled, False on error
    """
    if not enabled:
        logger.info("Google Cloud Logging disabled")
        return True

    # Only enable in production by default
    env = os.getenv("APP_ENV", "development").lower()
    if env != "production" and not os.getenv("FORCE_CLOUD_LOGGING"):
        logger.info("Skipping Cloud Logging setup in %s environment", env)
        return True

    # Setup Cloud Logging
    integration = get_gcp_logging()
    return integration.setup(log_level=os.getenv("CLOUD_LOG_LEVEL", "INFO"))
