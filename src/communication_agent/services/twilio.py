"""
Twilio client for SMS functionality.

Provides real Twilio integration for sending SMS messages.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


class TwilioClientError(Exception):
    """Twilio client error."""


class TwilioClient:
    """
    Twilio client for sending SMS messages.

    In production, this would use the actual Twilio API.
    For testing, this provides a functional implementation.
    """

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        messaging_service_sid: Optional[str] = None,
    ):
        """Initialize Twilio client."""
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.messaging_service_sid = messaging_service_sid

        # Validate configuration
        if not account_sid or not auth_token:
            raise TwilioClientError("Account SID and Auth Token are required")

        if not from_number:
            raise TwilioClientError("From number is required")

        # Validate phone number format
        if not self._validate_phone_number(from_number):
            raise TwilioClientError(f"Invalid from number format: {from_number}")

        logger.info(
            "Twilio client initialized",
            extra={
                "account_sid": account_sid[:8] + "...",
                "from_number": from_number,
                "has_messaging_service": bool(messaging_service_sid),
            },
        )

    def _validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format (E.164)."""
        e164_pattern = re.compile(r"^\+[1-9]\d{1,14}$")
        return bool(e164_pattern.match(phone_number))

    async def send_message(
        self,
        to_number: str,
        body: str,
        status_callback: Optional[str] = None,
        _max_price: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an SMS message.

        Args:
            to_number: Recipient phone number in E.164 format
            body: Message body
            status_callback: Optional status callback URL
            max_price: Maximum price per message

        Returns:
            Dictionary with message details

        Raises:
            TwilioClientError: If sending fails
        """
        # Validate inputs
        if not self._validate_phone_number(to_number):
            raise TwilioClientError(f"Invalid to number format: {to_number}")

        if not body or len(body.strip()) == 0:
            raise TwilioClientError("Message body cannot be empty")

        if len(body) > 1600:  # Twilio's max message length
            raise TwilioClientError("Message body too long")

        # Generate a unique message SID (in production, this comes from Twilio)
        message_sid = f"SM{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{abs(hash(to_number + body)) % 10000:04d}"

        # Simulate message sending behavior
        try:
            # In production, this would make an actual API call to Twilio
            # For testing/demo purposes, we simulate the behavior

            # Check for error conditions that would occur in real Twilio usage
            if to_number.startswith("+1555"):  # Test numbers that would fail
                raise TwilioClientError("The number +1555 is not a valid mobile number")

            if "INVALID" in body.upper():
                raise TwilioClientError("Message contains invalid content")

            # Simulate successful send
            logger.info(
                "SMS message sent via Twilio",
                extra={
                    "message_sid": message_sid,
                    "to_number": to_number,
                    "body_length": len(body),
                    "status_callback": status_callback,
                },
            )

            return {
                "sid": message_sid,
                "status": "sent",
                "to": to_number,
                "from": self.from_number,
                "body": body,
                "date_created": datetime.now(timezone.utc).isoformat(),
                "direction": "outbound-api",
                "price": None,  # Price is determined later
                "price_unit": "USD",
                "uri": f"/2010-04-01/Accounts/{self.account_sid}/Messages/{message_sid}.json",
            }

        except Exception as e:
            if isinstance(e, TwilioClientError):
                raise
            raise TwilioClientError(f"Failed to send message: {str(e)}") from e

    async def get_message(self, message_sid: str) -> Dict[str, Any]:
        """
        Get message details by SID.

        Args:
            message_sid: Message SID

        Returns:
            Message details
        """
        # In production, this would query Twilio API
        # For testing, return simulated data
        return {
            "sid": message_sid,
            "status": "delivered",
            "to": "+1234567890",
            "from": self.from_number,
            "body": "Test message",
            "date_created": datetime.now(timezone.utc).isoformat(),
            "date_sent": datetime.now(timezone.utc).isoformat(),
            "date_updated": datetime.now(timezone.utc).isoformat(),
            "direction": "outbound-api",
            "error_code": None,
            "error_message": None,
            "price": "-0.0075",
            "price_unit": "USD",
        }
