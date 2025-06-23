"""
SMS/Twilio configuration for the Communication Agent.

Provides configuration loading for SMS notifications via Twilio.
"""

import os
from typing import Optional

from src.communication_agent.services.sms_service import TwilioConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)


def get_twilio_config() -> Optional[TwilioConfig]:
    """
    Get Twilio configuration from environment variables.

    Expected environment variables:
    - TWILIO_ACCOUNT_SID: Twilio account SID
    - TWILIO_AUTH_TOKEN: Twilio authentication token
    - TWILIO_FROM_NUMBER: Phone number to send SMS from (E.164 format)
    - TWILIO_STATUS_CALLBACK_URL: Optional webhook URL for delivery status
    - TWILIO_MESSAGING_SERVICE_SID: Optional messaging service SID
    - TWILIO_MAX_PRICE_PER_MESSAGE: Optional max price per message (default: 0.10)

    Returns:
        TwilioConfig if all required variables are set, None otherwise
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not all([account_sid, auth_token, from_number]):
        logger.warning(
            "Twilio configuration incomplete",
            extra={
                "has_account_sid": bool(account_sid),
                "has_auth_token": bool(auth_token),
                "has_from_number": bool(from_number),
            },
        )
        return None

    # Validate from_number format
    if from_number and not from_number.startswith("+"):
        logger.warning(
            "TWILIO_FROM_NUMBER should be in E.164 format (e.g., +1234567890)",
            extra={"from_number": from_number},
        )

    # Type narrowing - we know these are not None from the check above
    assert account_sid is not None
    assert auth_token is not None
    assert from_number is not None

    config = TwilioConfig(
        account_sid=account_sid,
        auth_token=auth_token,
        from_number=from_number,
        status_callback_url=os.getenv("TWILIO_STATUS_CALLBACK_URL"),
        messaging_service_sid=os.getenv("TWILIO_MESSAGING_SERVICE_SID"),
        max_price_per_message=os.getenv("TWILIO_MAX_PRICE_PER_MESSAGE", "0.10"),
    )

    logger.info(
        "Twilio configuration loaded",
        extra={
            "account_sid": account_sid[:8] + "..." if account_sid else None,
            "from_number": from_number,
            "has_status_callback": bool(config.status_callback_url),
            "has_messaging_service": bool(config.messaging_service_sid),
        },
    )

    return config
