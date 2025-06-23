"""
Integration example for webhook notifications.

This demonstrates how to use the WebhookNotificationService with the CommunicationAgent.
"""

import asyncio

from src.communication_agent.agent import CommunicationAgent
from src.communication_agent.config.webhook_config import (
    get_webhook_config,
    get_webhook_configs,
)
from src.communication_agent.services.webhook_service import (
    WebhookAuthType,
    WebhookConfig,
    WebhookMethod,
    WebhookNotificationService,
)
from src.communication_agent.types import (
    NotificationChannel,
    NotificationPriority,
)


async def main() -> None:
    """Main function to demonstrate webhook integration."""
    # Example 1: Using environment configuration
    default_config = get_webhook_config()
    named_configs = get_webhook_configs()

    # Example 2: Creating webhook configurations programmatically
    slack_webhook_config = WebhookConfig(
        url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        method=WebhookMethod.POST,
        auth_type=WebhookAuthType.NONE,
        headers={"X-Custom-Header": "SentinelOps"},
    )

    pagerduty_webhook_config = WebhookConfig(
        url="https://events.pagerduty.com/v2/enqueue",
        method=WebhookMethod.POST,
        auth_type=WebhookAuthType.API_KEY,
        auth_credentials={
            "key_name": "Authorization",
            "key_value": "Token token=YOUR_API_KEY",
        },
    )

    custom_webhook_config = WebhookConfig(
        url="https://your-api.example.com/webhooks/security",
        method=WebhookMethod.POST,
        auth_type=WebhookAuthType.HMAC,
        auth_credentials={
            "secret": "your-webhook-secret",
            "algorithm": "sha256",
            "header_name": "X-Hub-Signature-256",
        },
        max_retries=5,
        retry_delay=10,
    )

    # Create webhook service with configurations
    webhook_configs = {
        "slack": slack_webhook_config,
        "pagerduty": pagerduty_webhook_config,
        "custom": custom_webhook_config,
    }

    # Add named configs from environment
    webhook_configs.update(named_configs)

    webhook_service = WebhookNotificationService(
        default_config=default_config,
        webhook_configs=webhook_configs,
    )

    # Create communication agent
    agent = CommunicationAgent(
        agent_id="comm-agent-001",
        notification_services={
            NotificationChannel.WEBHOOK: webhook_service,
        },
    )

    # Start the agent
    await agent.start()

    try:
        # Example 1: Send to a specific webhook URL
        print("Sending notification to direct webhook URL...")
        await agent.send_incident_notification(
            incident_id="INC-WEBHOOK-001",
            incident_type="Data Exfiltration Attempt",
            severity="critical",
            affected_resources=["api-server-01", "database-prod"],
            detection_source="Network Monitor",
            initial_assessment="Unusual data transfer detected to external IP",
            recipients=[
                {
                    "channel": NotificationChannel.WEBHOOK,
                    "address": "https://webhook.site/your-unique-url",
                },
            ],
            priority=NotificationPriority.CRITICAL,
        )

        print("Incident notification sent: {message_id}")

        # Example 2: Send to named webhook configurations
        print("\nSending to named webhook configurations...")
        agent.process(
            {
                "message_type": "critical_alert",
                "recipients": [
                    {
                        "channel": NotificationChannel.WEBHOOK,
                        "address": "slack",  # Uses named configuration
                    },
                    {
                        "channel": NotificationChannel.WEBHOOK,
                        "address": "pagerduty",  # Uses named configuration
                    },
                ],
                "context": {
                    "alert_type": "SECURITY",
                    "title": "Critical Security Alert",
                    "description": "Multiple failed authentication attempts detected",
                    "severity": "critical",
                    "source": "auth-service",
                    "incident_url": "https://sentinelops.example.com/incidents/INC-002",
                    "affected_users": ["admin", "root"],
                    "recommendation": "Investigate immediately and consider blocking source IPs",
                },
                "priority": NotificationPriority.CRITICAL,
            }
        )

        print("Critical alert result: {result}")

        # Example 3: Custom webhook with HMAC signature
        print("\nSending to custom webhook with HMAC...")
        agent.process(
            {
                "message_type": "remediation_complete",
                "recipients": [
                    {
                        "channel": NotificationChannel.WEBHOOK,
                        "address": "custom",  # Uses HMAC configuration
                    },
                ],
                "context": {
                    "incident_id": "INC-003",
                    "remediation_type": "automated",
                    "actions_taken": [
                        "Blocked suspicious IP addresses",
                        "Reset compromised credentials",
                        "Enabled additional monitoring",
                    ],
                    "completion_time": "2025-05-29T12:00:00Z",
                    "success": True,
                },
                "priority": NotificationPriority.HIGH,
            }
        )

        print("Custom webhook result: {custom_result}")

        # Wait for webhooks to be processed
        print("\nWaiting for webhook delivery...")
        await asyncio.sleep(5)

        # Check delivery history
        history = webhook_service.get_delivery_history(limit=10)
        print("\nDelivery history ({len(history)} records):")
        for record in history:
            print(
                f"- {record['timestamp']}: {record['url']} "
                f"(status: {record['status_code']}, "
                f"success: {record['success']}, "
                f"time: {record['delivery_time']:.2f}s)"
            )

    finally:
        # Stop the agent
        await agent.stop()

        # Close webhook service
        await webhook_service.close()


if __name__ == "__main__":
    # Example environment setup
    print("Webhook Integration Example")
    print("==========================")
    print("\nYou can set these environment variables:")
    print("- WEBHOOK_URL: Default webhook endpoint")
    print("- WEBHOOK_AUTH_TYPE: none, basic, bearer, api_key, hmac")
    print("- WEBHOOK_AUTH_CREDENTIALS: JSON with auth details")
    print("\nExample:")
    print('export WEBHOOK_URL="https://your-webhook.com/endpoint"')
    print('export WEBHOOK_AUTH_TYPE="bearer"')
    print('export WEBHOOK_AUTH_CREDENTIALS=\'{"token": "your-token"}\'')
    print("\nFor named webhooks:")
    print(
        'export WEBHOOK_CONFIG_ALERTS=\'{"url": "https://alerts.com", "auth_type": "api_key", '
        '"auth_credentials": {"key_name": "X-API-Key", "key_value": "secret"}}\''
    )
    print("\n")

    asyncio.run(main())
