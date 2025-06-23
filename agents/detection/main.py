#!/usr/bin/env python3
"""Main entry point for Detection Agent - PRODUCTION"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.agent_config import AGENT_CONFIG  # noqa: E402
from src.detection_agent.adk_agent import DetectionAgent  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize and run the production detection agent"""
    # Get configuration
    project_id = os.environ.get("PROJECT_ID", "your-project-id")
    
    # Build agent configuration
    config = AGENT_CONFIG.get("detection", {})
    config["project_id"] = project_id
    config["bigquery_dataset"] = os.environ.get("BIGQUERY_DATASET", "security_logs")
    config["bigquery_table"] = os.environ.get("BIGQUERY_TABLE", "events")
    config["scan_interval_minutes"] = int(os.environ.get("SCAN_INTERVAL_MINUTES", "5"))
    
    # Initialize ADK agent with proper configuration
    agent = DetectionAgent(config)
    
    logger.info(f"Starting Detection Agent for project: {project_id}")
    logger.info(f"Configuration: Dataset={config['bigquery_dataset']}, Table={config['bigquery_table']}")
    
    # Run the agent
    try:
        # For production, run continuous monitoring
        while True:
            # Create an invocation context for ADK
            from google.adk.agents.invocation_context import InvocationContext
            context = InvocationContext()
            
            result = await agent._execute_agent_logic(context, None)
            logger.info(f"Detection scan completed: {result.get('status')}")
            
            # Log any incidents created
            incidents = result.get("incidents_created", [])
            if incidents:
                logger.info(f"Created {len(incidents)} incidents")
            
            # Wait for next scan interval
            await asyncio.sleep(config["scan_interval_minutes"] * 60)
            
    except KeyboardInterrupt:
        logger.info("Shutting down Detection Agent...")
    except Exception as e:
        logger.error(f"Error running Detection Agent: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
