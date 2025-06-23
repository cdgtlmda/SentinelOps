#!/usr/bin/env python3
"""Main entry point for Orchestrator Agent - PRODUCTION"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.agent_config import AGENT_CONFIG  # noqa: E402
from src.orchestrator_agent.adk_agent import OrchestratorAgent  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize and run the production orchestrator agent"""
    # Get configuration
    project_id = os.environ.get("PROJECT_ID", "your-project-id")
    
    # Build agent configuration
    config = AGENT_CONFIG.get("orchestrator", {})
    config["project_id"] = project_id
    config["max_concurrent_workflows"] = int(os.environ.get("MAX_CONCURRENT_WORKFLOWS", "10"))
    config["workflow_timeout_minutes"] = int(os.environ.get("WORKFLOW_TIMEOUT_MINUTES", "120"))
    config["auto_approve_threshold"] = float(os.environ.get("AUTO_APPROVE_THRESHOLD", "0.7"))
    
    # Initialize ADK agent with proper configuration
    agent = OrchestratorAgent(config)
    
    logger.info(f"Starting Orchestrator Agent for project: {project_id}")
    logger.info(f"Configuration: Max workflows={config['max_concurrent_workflows']}, Timeout={config['workflow_timeout_minutes']}min")
    
    # Run the agent
    try:
        logger.info("Orchestrator Agent ready and coordinating workflows...")
        
        # Create an invocation context for ADK
        from google.adk.agents.invocation_context import InvocationContext
        context = InvocationContext()
        
        # Perform initial orchestration tasks
        result = await agent._execute_agent_logic(context, None)
        logger.info(f"Initial orchestration complete: {result}")
        
        # Keep agent running for continuous orchestration
        while True:
            # Perform periodic orchestration tasks
            orchestration_result = await agent._execute_agent_logic(context, None)
            
            if orchestration_result.get("tasks_performed"):
                logger.info(f"Orchestration tasks performed: {orchestration_result['tasks_performed']}")
            
            # Check every 30 seconds
            await asyncio.sleep(30)
            
    except KeyboardInterrupt:
        logger.info("Shutting down Orchestrator Agent...")
    except Exception as e:
        logger.error(f"Error running Orchestrator Agent: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
