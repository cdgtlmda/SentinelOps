"""Configuration for communication services."""

import os
from typing import Optional

from src.communication_agent.services.email_service import SMTPConfig


def get_smtp_config() -> Optional[SMTPConfig]:
    """
    Get SMTP configuration from environment variables.

    Returns None if required environment variables are not set.
    """
    # Check if required environment variables are set
    required_vars = [
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
    ]

    if not all(os.getenv(var) for var in required_vars):
        return None

    return SMTPConfig(
        host=os.getenv("SMTP_HOST", ""),
        port=int(os.getenv("SMTP_PORT", "587")),
        username=os.getenv("SMTP_USERNAME", ""),
        password=os.getenv("SMTP_PASSWORD", ""),
        use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        use_ssl=os.getenv("SMTP_USE_SSL", "false").lower() == "true",
        timeout=int(os.getenv("SMTP_TIMEOUT", "30")),
        from_name=os.getenv("SMTP_FROM_NAME", "SentinelOps"),
        from_address=os.getenv("SMTP_FROM_ADDRESS", "notifications@sentinelops.com"),
    )


# Common email settings
EMAIL_SETTINGS = {
    "max_recipients_per_email": 50,
    "max_attachment_size": 10 * 1024 * 1024,  # 10MB
    "max_queue_size": 1000,
    "retry_attempts": 3,
    "retry_delay": 60,  # seconds
}
