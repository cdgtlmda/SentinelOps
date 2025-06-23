"""Configuration for Slack notifications."""

import os
from typing import Optional

from src.communication_agent.services.slack_service import SlackConfig


def get_slack_config() -> Optional[SlackConfig]:
    """
    Get Slack configuration from environment variables.

    Returns None if required environment variables are not set.
    """
    # Check if required environment variables are set
    bot_token = os.getenv("SLACK_BOT_TOKEN")

    if not bot_token:
        return None

    return SlackConfig(
        bot_token=bot_token,
        default_channel=os.getenv("SLACK_DEFAULT_CHANNEL", "#alerts"),
        timeout=int(os.getenv("SLACK_TIMEOUT", "30")),
        max_retries=int(os.getenv("SLACK_MAX_RETRIES", "3")),
        retry_delay=int(os.getenv("SLACK_RETRY_DELAY", "1")),
        enable_threads=os.getenv("SLACK_ENABLE_THREADS", "true").lower() == "true",
        enable_interactive=os.getenv("SLACK_ENABLE_INTERACTIVE", "true").lower()
        == "true",
    )


# Common Slack settings
SLACK_SETTINGS = {
    "max_message_length": 4000,  # Slack's limit
    "max_blocks": 50,  # Maximum blocks per message
    "max_attachments": 20,  # Maximum attachments
    "rate_limit_tier": "Tier 3",  # Default rate limit tier
    "rate_limit_requests": 50,  # Requests per minute
}
