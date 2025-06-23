#!/usr/bin/env python3
"""Main entry point for Communication Agent - PRODUCTION"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.agent_config import AGENT_CONFIG  # noqa: E402
from src.communication_agent.adk_agent import CommunicationAgent  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize and run the production communication agent"""
    # Get configuration
    project_id = os.environ.get("PROJECT_ID", "your-project-id")
    
    # Build agent configuration
    config = AGENT_CONFIG.get("communication", {})
    config["project_id"] = project_id
    
    # Slack configuration
    config["slack"] = {
        "webhook_url": os.environ.get("SLACK_WEBHOOK_URL", "")
    }
    
    # Email configuration
    config["email"] = {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "username": os.environ.get("SMTP_USERNAME", ""),
        "password": os.environ.get("SMTP_PASSWORD", ""),
        "use_tls": True
    }
    
    # SMS configuration (Twilio)
    config["sms"] = {
        "account_sid": os.environ.get("TWILIO_ACCOUNT_SID", ""),
        "auth_token": os.environ.get("TWILIO_AUTH_TOKEN", ""),
        "from_number": os.environ.get("TWILIO_FROM_NUMBER", "")
    }
    
    # Notification settings
    config["default_channels"] = os.environ.get("DEFAULT_CHANNELS", "slack,email").split(",")
    config["critical_channels"] = os.environ.get("CRITICAL_CHANNELS", "slack,email,sms").split(",")
    
    # Recipient mapping
    config["recipient_mapping"] = {
        "email": os.environ.get("EMAIL_RECIPIENTS", "security-team@company.com").split(","),
        "sms": os.environ.get("SMS_RECIPIENTS", "").split(",") if os.environ.get("SMS_RECIPIENTS") else []
    }
    
    # Initialize ADK agent with proper configuration
    agent = CommunicationAgent(config)
    
    logger.info(f"Starting Communication Agent for project: {project_id}")
    logger.info(f"Enabled channels: Default={config['default_channels']}, Critical={config['critical_channels']}")
    
    # Run the agent (waits for transfers from other agents)
    try:
        logger.info("Communication Agent ready and waiting for notification requests...")
        
        # In production, the agent would be triggered by transfers
        # For testing, we can simulate a notification request
        if os.environ.get("TEST_MODE") == "true":
            test_request = {
                "incident_id": "test-incident-001",
                "workflow_stage": "critical_alert",
                "results": {
                    "priority": "high",
                    "channels": ["slack", "email"],
                    "analysis": {
                        "threat_assessment": {
                            "threat_level": "high",
                            "threat_type": "Brute Force Attack",
                            "attack_pattern": "Multiple failed authentication attempts"
                        },
                        "impact_analysis": {
                            "affected_resources": ["user-accounts", "authentication-service"]
                        }
                    }
                }
            }
            
            result = await agent.run(notification_request=test_request)
            logger.info(f"Notification sent: {result}")
        else:
            # Keep agent running
            while True:
                await asyncio.sleep(60)
                
    except KeyboardInterrupt:
        logger.info("Shutting down Communication Agent...")
    except Exception as e:
        logger.error(f"Error running Communication Agent: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
