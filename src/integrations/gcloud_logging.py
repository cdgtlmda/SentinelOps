"""
Google Cloud Logging integration for SentinelOps
"""

import logging
import os
from typing import Any, Optional

try:
    import google.cloud.logging
    from google.cloud.logging.handlers import CloudLoggingHandler

    GOOGLE_CLOUD_LOGGING_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_LOGGING_AVAILABLE = False

from src.utils.logging import get_logger

logger = get_logger(__name__)


class GoogleCloudLoggingIntegration:
    """
    Integration with Google Cloud Logging service.
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Google Cloud Logging integration.

        Args:
            project_id: Google Cloud project ID (uses default if not provided)
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.client: Optional[Any] = None
        self.handler: Optional[Any] = None

    def setup(self, log_name: str = "sentinelops") -> bool:
        """
        Set up Google Cloud Logging handler.

        Args:
            log_name: Name for the log in Google Cloud Logging

        Returns:
            True if setup successful, False otherwise
        """
        if not GOOGLE_CLOUD_LOGGING_AVAILABLE:
            logger.warning("Google Cloud Logging library not available")
            return False

        if not self.project_id:
            logger.warning("No Google Cloud project ID configured")
            return False

        try:
            # Create client
            if GOOGLE_CLOUD_LOGGING_AVAILABLE:
                # Create client with proper typing
                client_class: Any = google.cloud.logging.Client
                self.client = client_class(project=self.project_id)
            else:
                raise ImportError("Google Cloud Logging is not available")

            # Create handler
            self.handler = CloudLoggingHandler(self.client, name=log_name)

            # Add handler to root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(self.handler)

            logger.info(
                "Google Cloud Logging configured for project %s",
                self.project_id,
                extra={"project_id": self.project_id, "log_name": log_name},
            )

            return True

        except (ValueError, ImportError, AttributeError) as e:
            logger.error("Failed to setup Google Cloud Logging: %s", e)
            return False

    def log_structured(
        self, message: str, severity: str = "INFO", **kwargs: Any
    ) -> None:
        """
        Log a structured message to Google Cloud Logging.

        Args:
            message: Log message
            severity: Log severity level
            **kwargs: Additional structured data
        """
        if not self.client:
            logger.warning("Google Cloud Logging client not initialized")
            return

        try:
            cloud_logger = self.client.logger("sentinelops-structured")
            cloud_logger.log_struct(
                {"message": message, "severity": severity, **kwargs}, severity=severity
            )
        except (ValueError, ImportError, AttributeError) as e:
            logger.error("Failed to log to Google Cloud: %s", e)


# Singleton instance
_GCLOUD_LOGGING = None


def get_gcloud_logging(
    project_id: Optional[str] = None,
) -> GoogleCloudLoggingIntegration:
    """
    Get or create Google Cloud Logging integration instance.

    Args:
        project_id: Google Cloud project ID

    Returns:
        GoogleCloudLoggingIntegration instance
    """
    global _GCLOUD_LOGGING  # pylint: disable=global-statement
    if _GCLOUD_LOGGING is None:
        _GCLOUD_LOGGING = GoogleCloudLoggingIntegration(project_id)
        _GCLOUD_LOGGING.setup()
    return _GCLOUD_LOGGING
