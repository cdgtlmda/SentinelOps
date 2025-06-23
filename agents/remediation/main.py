#!/usr/bin/env python3
"""Main entry point for Remediation Agent - PRODUCTION"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.agent_config import AGENT_CONFIG  # noqa: E402
from src.remediation_agent.adk_agent import RemediationAgent  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize and run the production remediation agent"""
    # Get configuration
    project_id = os.environ.get("PROJECT_ID", "your-project-id")
    
    # Build agent configuration
    config = AGENT_CONFIG.get("remediation", {})
    config["project_id"] = project_id
    config["dry_run_mode"] = os.environ.get("DRY_RUN_MODE", "true").lower() == "true"
    config["approval_required"] = os.environ.get("APPROVAL_REQUIRED", "true").lower() == "true"
    config["auto_approve_low_risk"] = os.environ.get("AUTO_APPROVE_LOW_RISK", "true").lower() == "true"
    config["max_concurrent_actions"] = int(os.environ.get("MAX_CONCURRENT_ACTIONS", "5"))
    
    # Initialize ADK agent with proper configuration
    agent = RemediationAgent(config)
    
    logger.info(f"Starting Remediation Agent for project: {project_id}")
    logger.info(f"Configuration: Dry run={config['dry_run_mode']}, Approval required={config['approval_required']}")
    
    # Run the agent (waits for transfers from other agents)
    try:
        logger.info("Remediation Agent ready and waiting for remediation requests...")
        
        # In production, the agent would be triggered by transfers
        # For testing, we can simulate a remediation request
        if os.environ.get("TEST_MODE") == "true":
            test_request = {
                "incident_id": "test-incident-001",
                "analysis": {
                    "threat_assessment": {
                        "threat_level": "high",
                        "confidence": 0.85
                    },
                    "impact_analysis": {
                        "source_ip": "192.168.1.100",
                        "actor": "compromised@example.com"
                    }
                },
                "recommendations": [
                    {
                        "action": "Block malicious IP address",
                        "priority": "high",
                        "automation_possible": True
                    }
                ]
            }
            
            result = await agent.run(remediation_request=test_request)
            logger.info(f"Remediation completed: {result}")
        else:
            # Keep agent running
            while True:
                await asyncio.sleep(60)
                
    except KeyboardInterrupt:
        logger.info("Shutting down Remediation Agent...")
    except Exception as e:
        logger.error(f"Error running Remediation Agent: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
