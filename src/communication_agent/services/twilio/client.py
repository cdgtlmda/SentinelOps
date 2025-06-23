"""
Twilio client wrapper for SMS notifications.

This module provides a wrapper around the Twilio Python SDK
for sending SMS messages and handling delivery status.
"""

import asyncio
from typing import Any, Dict, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


class TwilioClientError(Exception):
    """Exception raised for Twilio client errors."""


class TwilioClient:
    """
    Wrapper for Twilio SDK operations.

    This class abstracts the Twilio SDK to provide async operations
    and proper error handling for the SMS notification service.
    """

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        messaging_service_sid: Optional[str] = None,
    ):
        """
        Initialize Twilio client.

        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_number: Phone number to send from (E.164 format)
            messaging_service_sid: Optional messaging service SID
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.messaging_service_sid = messaging_service_sid
        self._client: Optional[Any] = None

        # Initialize the Twilio client
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Twilio REST client - PRODUCTION ONLY."""
        try:
            # Import Twilio SDK - required for production
            from twilio.rest import Client

            if not self.account_sid or not self.auth_token:
                raise ValueError("Twilio account_sid and auth_token are required for production")

            self._client = Client(self.account_sid, self.auth_token)
            logger.info(
                "Twilio client initialized for production",
                extra={
                    "account_sid": self.account_sid[:8] + "...",
                    "from_number": self.from_number,
                },
            )
        except ImportError as e:
            logger.error("Twilio SDK not installed. Install with: pip install twilio")
            raise TwilioClientError(f"Failed to import Twilio SDK: {e}") from e
        except (ValueError, AttributeError) as e:
            logger.error("Failed to initialize Twilio client: %s", e)
            raise TwilioClientError(f"Invalid Twilio configuration: {e}") from e

    async def send_message(
        self,
        to_number: str,
        body: str,
        status_callback: Optional[str] = None,
        max_price: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an SMS message.

        Args:
            to_number: Recipient phone number (E.164 format)
            body: Message body
            status_callback: Optional webhook URL for delivery status
            max_price: Optional maximum price per message

        Returns:
            Dictionary with message details including SID

        Raises:
            TwilioClientError: If message sending fails
        """
        if not self._client:
            raise TwilioClientError("Twilio client not initialized")

        try:
            # Prepare message parameters
            message_params = {
                "to": to_number,
                "body": body,
            }

            # Use messaging service or from number
            if self.messaging_service_sid:
                message_params["messaging_service_sid"] = self.messaging_service_sid
            else:
                message_params["from_"] = self.from_number

            # Add optional parameters
            if status_callback:
                message_params["status_callback"] = status_callback

            if max_price:
                message_params["max_price"] = max_price

            # Send message using thread pool for sync Twilio SDK (production only)
            message = await asyncio.to_thread(
                self._client.messages.create, **message_params
            )

            return {
                "sid": message.sid,
                "to": message.to,
                "from": getattr(message, "from_", self.from_number),
                "body": message.body,
                "status": getattr(message, "status", "queued"),
            }

        except (ImportError, ValueError, AttributeError) as e:
            logger.error(
                "Failed to send SMS: %s",
                e,
                extra={
                    "to_number": to_number,
                    "body_length": len(body),
                },
                exc_info=True,
            )
            raise TwilioClientError(f"Failed to send SMS: {e}") from e

    async def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Get the status of a sent message.

        Args:
            message_sid: Message SID to check

        Returns:
            Dictionary with message status details

        Raises:
            TwilioClientError: If status retrieval fails
        """
        if not self._client:
            raise TwilioClientError("Twilio client not initialized")

        try:
            # Fetch message details
            if (
                self._client
                and hasattr(self._client, "messages")
                and self._client.messages
                and hasattr(self._client.messages, "get")
            ):
                # Real Twilio client
                assert self._client is not None  # Type narrowing for mypy
                assert self._client.messages is not None  # Type narrowing for mypy
                client = self._client  # Store in local variable for lambda
                message = await asyncio.to_thread(
                    lambda: client.messages.get(message_sid).fetch()
                )

                return {
                    "sid": message.sid,
                    "status": message.status,
                    "to": message.to,
                    "from": message.from_,
                    "date_sent": message.date_sent,
                    "error_code": message.error_code,
                    "error_message": message.error_message,
                }
            else:
                # Mock client
                return {
                    "sid": message_sid,
                    "status": "delivered",
                    "to": "+1234567890",
                    "from": self.from_number,
                    "date_sent": None,
                    "error_code": None,
                    "error_message": None,
                }

        except (ImportError, ValueError, AttributeError) as e:
            logger.error(
                "Failed to get message status: %s",
                e,
                extra={"message_sid": message_sid},
                exc_info=True,
            )
            raise TwilioClientError(f"Failed to get message status: {e}") from e

    def validate_phone_number(self, phone_number: str) -> bool:
        """
        Validate a phone number using Twilio lookup API.

        Args:
            phone_number: Phone number to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            if self._client and hasattr(self._client, "lookups"):
                # Real Twilio client - use lookup API
                phone_info = self._client.lookups.v1.phone_numbers(phone_number).fetch()
                return bool(phone_info.phone_number)
            else:
                # Mock client - basic validation
                import re

                pattern = re.compile(r"^\+[1-9]\d{1,14}$")
                return bool(pattern.match(phone_number))

        except (ImportError, ValueError, AttributeError) as e:
            logger.debug(
                "Phone validation failed: %s",
                e,
                extra={"phone_number": phone_number},
            )
            return False
