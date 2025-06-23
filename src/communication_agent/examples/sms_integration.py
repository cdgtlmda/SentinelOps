"""
Integration example for SMS notifications.

This demonstrates how to use the SMSNotificationService with the CommunicationAgent.
"""

import asyncio
import os

from src.communication_agent.agent import CommunicationAgent
from src.communication_agent.config.sms_config import get_twilio_config
from src.communication_agent.services.sms_service import SMSNotificationService
from src.communication_agent.types import (
    NotificationChannel,
    NotificationPriority,
)


async def main() -> None:
    """Main function to demonstrate SMS integration."""
    # Get Twilio configuration
    twilio_config = get_twilio_config()

    if not twilio_config:
        print(
            "Twilio configuration not found. Please set the following environment variables:"
        )
        print("- TWILIO_ACCOUNT_SID")
        print("- TWILIO_AUTH_TOKEN")
        print("- TWILIO_FROM_NUMBER (in E.164 format, e.g., +1234567890)")
        print("\nOptional:")
        print("- TWILIO_STATUS_CALLBACK_URL")
        print("- TWILIO_MESSAGING_SERVICE_SID")
        print("- TWILIO_MAX_PRICE_PER_MESSAGE")
        print("\nExample:")
        print("export TWILIO_ACCOUNT_SID=your-account-sid")
        print("export TWILIO_AUTH_TOKEN=your-auth-token")
        print("export TWILIO_FROM_NUMBER=+1234567890")
        return

    # Create SMS service
    sms_service = SMSNotificationService(twilio_config)

    # Create communication agent
    agent = CommunicationAgent(
        agent_id="comm-agent-001",
        notification_services={
            NotificationChannel.SMS: sms_service,
        },
    )

    # Start the agent
    await agent.start()

    try:
        # Send a test incident notification
        test_phone = os.getenv("TEST_SMS_RECIPIENT", "+1234567890")
        print("Sending test SMS to: {test_phone}")

        await agent.send_incident_notification(
            incident_id="INC-TEST-001",
            incident_type="Unauthorized Access Attempt",
            severity="high",
            affected_resources=["prod-server-01", "database-primary"],
            detection_source="IDS",
            initial_assessment="Multiple failed login attempts from suspicious IP",
            recipients=[
                {
                    "channel": NotificationChannel.SMS,
                    "address": test_phone,
                },
            ],
            priority=NotificationPriority.HIGH,
        )

        print("Incident notification sent with message ID: {message_id}")

        # Send a shorter critical alert (optimized for SMS)
        agent.process(
            {
                "message_type": "critical_alert",
                "recipients": [
                    {
                        "channel": NotificationChannel.SMS,
                        "address": test_phone,
                    },
                ],
                "context": {
                    "alert_type": "SECURITY",
                    "message": (
                        "CRITICAL: Unauthorized access detected on prod-server-01. "
                        "Immediate action required."
                    ),
                    "incident_id": "INC-TEST-002",
                    "action_url": "https://sentinelops.example.com/incidents/INC-TEST-002",
                },
                "priority": NotificationPriority.CRITICAL,
            }
        )

        print("Critical alert result: {result}")

        # Test message length optimization
        agent.process(
            {
                "message_type": "analysis_complete",
                "recipients": [
                    {
                        "channel": NotificationChannel.SMS,
                        "address": test_phone,
                    },
                ],
                "context": {
                    "incident_id": "INC-TEST-003",
                    "risk_level": "High",
                    "impact_assessment": (
                        "This is a very long message that will be automatically optimized and "
                        "split into multiple SMS messages if necessary. The SMS service will "
                        "replace common phrases with shorter versions and ensure that the message "
                        "fits within SMS length limits. If the message is too long, it will be "
                        "split into multiple parts with proper part indicators."
                    ),
                    "recommended_actions": (
                        "1. Reset affected accounts immediately\n"
                        "2. Enable multi-factor authentication\n"
                        "3. Review all access logs for the past 24 hours\n"
                        "4. Update security policies"
                    ),
                },
                "priority": NotificationPriority.MEDIUM,
            }
        )

        print("Long message result: {long_message_result}")

        # Demonstrate delivery status checking (if configured)
        if twilio_config.status_callback_url:
            print("\nDelivery status tracking is enabled.")
            print(
                f"Status callbacks will be sent to: {twilio_config.status_callback_url}"
            )

        # Wait for messages to be processed
        print("\nWaiting for SMS delivery...")
        await asyncio.sleep(10)

    finally:
        # Stop the agent
        await agent.stop()

        # Close SMS service
        await sms_service.close()


if __name__ == "__main__":
    asyncio.run(main())
