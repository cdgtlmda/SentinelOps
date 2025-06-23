"""
Integration example for email notifications.

This demonstrates how to use the EmailNotificationService with the CommunicationAgent.
"""

import asyncio
import os

from src.communication_agent.agent import CommunicationAgent
from src.communication_agent.config.email_config import get_smtp_config
from src.communication_agent.services.email_service import EmailNotificationService
from src.communication_agent.types import (
    NotificationChannel,
    NotificationPriority,
)


async def main() -> None:
    """Main function to demonstrate email integration."""
    # Get SMTP configuration
    smtp_config = get_smtp_config()

    if not smtp_config:
        print(
            "SMTP configuration not found. Please set the following environment variables:"
        )
        print("- SMTP_HOST")
        print("- SMTP_PORT")
        print("- SMTP_USERNAME")
        print("- SMTP_PASSWORD")
        print("\nExample:")
        print("export SMTP_HOST=smtp.gmail.com")
        print("export SMTP_PORT=587")
        print("export SMTP_USERNAME=your-email@gmail.com")
        print("export SMTP_PASSWORD=your-app-password")
        return

    # Create email service
    email_service = EmailNotificationService(smtp_config)

    # Create communication agent
    agent = CommunicationAgent(
        agent_id="comm-agent-001",
        notification_services={
            NotificationChannel.EMAIL: email_service,
        },
    )

    # Start the agent
    await agent.start()

    try:
        # Send a test incident notification
        await agent.send_incident_notification(
            incident_id="INC-TEST-001",
            incident_type="Unauthorized Access Attempt",
            severity="high",
            affected_resources=["prod-server-01", "database-primary"],
            detection_source="Intrusion Detection System",
            initial_assessment="Multiple failed login attempts detected from suspicious IP",
            recipients=[
                {
                    "channel": NotificationChannel.EMAIL,
                    "address": os.getenv(
                        "TEST_EMAIL_RECIPIENT", "security@example.com"
                    ),
                },
            ],
            priority=NotificationPriority.HIGH,
        )

        print("Incident notification sent")

        # Process using the standard agent interface
        agent.process(
            {
                "message_type": "analysis_complete",
                "recipients": [
                    {
                        "channel": NotificationChannel.EMAIL,
                        "address": os.getenv(
                            "TEST_EMAIL_RECIPIENT", "security@example.com"
                        ),
                    },
                ],
                "context": {
                    "incident_id": "INC-TEST-001",
                    "risk_level": "High",
                    "impact_assessment": "Potential data breach risk",
                    "root_cause": "Weak password policy",
                    "affected_systems": "Authentication service",
                    "recommended_actions": (
                        "1. Reset affected accounts\n2. Enable MFA\n3. Review access logs"
                    ),
                    "next_steps": "Implement automated remediation",
                    "analysis_link": "https://sentinelops.example.com/incidents/INC-TEST-001",
                },
                "priority": NotificationPriority.HIGH,
            }
        )

        print("Analysis complete notification result: {result}")

        # Wait a bit for messages to be processed
        await asyncio.sleep(5)

    finally:
        # Stop the agent
        await agent.stop()

        # Close email service
        await email_service.close()


if __name__ == "__main__":
    asyncio.run(main())
