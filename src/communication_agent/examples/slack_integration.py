"""
Integration example for Slack notifications.

This demonstrates how to use the SlackNotificationService with the CommunicationAgent.
"""

import asyncio
import os

from src.communication_agent.agent import CommunicationAgent
from src.communication_agent.config.slack_config import get_slack_config
from src.communication_agent.services.slack_service import SlackNotificationService
from src.communication_agent.types import (
    MessageType,
    NotificationChannel,
    NotificationPriority,
)


async def main() -> None:
    """Main function to demonstrate Slack integration."""
    # Get Slack configuration
    slack_config = get_slack_config()

    if not slack_config:
        print(
            "Slack configuration not found. Please set the following environment variables:"
        )
        print("- SLACK_BOT_TOKEN (required)")
        print("- SLACK_DEFAULT_CHANNEL (optional, defaults to #alerts)")
        print("\nTo get a Slack bot token:")
        print("1. Go to https://api.slack.com/apps")
        print("2. Create a new app or select existing")
        print("3. Go to 'OAuth & Permissions'")
        print("4. Add the following scopes:")
        print("   - chat:write")
        print("   - channels:read")
        print("   - groups:read")
        print("5. Install the app to your workspace")
        print("6. Copy the 'Bot User OAuth Token'")
        return

    # Create Slack service
    slack_service = SlackNotificationService(slack_config)

    # Create communication agent
    agent = CommunicationAgent(
        agent_id="comm-agent-002",
        notification_services={
            NotificationChannel.SLACK: slack_service,
        },
    )
    # Start the agent
    await agent.start()

    try:
        # Send a test incident notification
        print("Sending incident notification...")
        await agent.send_incident_notification(
            incident_id="INC-SLACK-001",
            incident_type="Suspicious Network Activity",
            severity="high",
            affected_resources=["firewall-01", "vpn-gateway"],
            detection_source="Network Monitor",
            initial_assessment="Unusual outbound traffic pattern detected",
            recipients=[
                {
                    "channel": NotificationChannel.SLACK,
                    "address": os.getenv("SLACK_TEST_CHANNEL", "#general"),
                },
            ],
            priority=NotificationPriority.HIGH,
        )

        print("✅ Incident notification sent with message ID: {message_id}")

        # Wait a moment
        await asyncio.sleep(2)

        # Send a thread update using the service directly
        if slack_service.config.enable_threads:
            print("\nSending thread update...")
            update_result = await slack_service.send_thread_update(
                incident_id="INC-SLACK-001",
                update_type="Analysis Progress",
                message="Analyzing traffic patterns and identifying source IPs...",
                channel=os.getenv("SLACK_TEST_CHANNEL", "#general"),
                metadata={
                    "Progress": "25%",
                    "Analyzed IPs": "127",
                    "Suspicious Connections": "3",
                },
            )

            if update_result:
                print("✅ Thread update sent successfully")
            else:
                print("❌ Thread update failed (no thread found)")

        # Send analysis complete notification
        print("\nSending analysis complete notification...")
        agent.process(
            {
                "message_type": MessageType.ANALYSIS_COMPLETE,
                "recipients": [
                    {
                        "channel": NotificationChannel.SLACK,
                        "address": os.getenv("SLACK_TEST_CHANNEL", "#general"),
                    },
                ],
                "context": {
                    "incident_id": "INC-SLACK-001",
                    "risk_level": "High",
                    "impact_assessment": "Potential data exfiltration attempt",
                    "root_cause": "Compromised user credentials",
                    "affected_systems": "VPN gateway, Internal network",
                    "recommended_actions": (
                        "1. Block suspicious IPs\n2. Reset affected credentials\n"
                        "3. Review access logs"
                    ),
                    "next_steps": "Implement automated IP blocking",
                    "analysis_link": "https://sentinelops.example.com/incidents/INC-SLACK-001",
                },
                "priority": NotificationPriority.HIGH,
            }
        )

        print("✅ Analysis complete notification result: {result}")

        # Wait for messages to be processed
        await asyncio.sleep(3)

    finally:
        # Stop the agent
        await agent.stop()

        # Close Slack service
        await slack_service.close()

    print("\n✨ Slack integration demo completed!")


if __name__ == "__main__":
    asyncio.run(main())
