#!/usr/bin/env python3
"""Main entry point for Analysis Agent - PRODUCTION"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.agent_config import AGENT_CONFIG  # noqa: E402
from src.analysis_agent.adk_agent import AnalysisAgent  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize and run the production analysis agent"""
    # Get configuration
    project_id = os.environ.get("PROJECT_ID", "your-project-id")
    
    # Build agent configuration
    config = AGENT_CONFIG.get("analysis", {})
    config["project_id"] = project_id
    config["vertex_ai_location"] = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
    config["model"] = os.environ.get("VERTEX_AI_MODEL", "gemini-1.5-pro-002")
    config["temperature"] = float(os.environ.get("TEMPERATURE", "0.7"))
    config["max_tokens"] = int(os.environ.get("MAX_TOKENS", "2048"))
    config["auto_remediate_threshold"] = float(os.environ.get("AUTO_REMEDIATE_THRESHOLD", "0.8"))
    config["critical_alert_threshold"] = float(os.environ.get("CRITICAL_ALERT_THRESHOLD", "0.9"))
    
    # Vertex AI uses application default credentials
    # No API key validation needed
    
    # Initialize ADK agent with proper configuration
    agent = AnalysisAgent(config)
    
    logger.info(f"Starting Analysis Agent for project: {project_id}")
    logger.info(f"Using model: {config['model']}")
    
    # Run the agent (waits for transfers from other agents)
    try:
        logger.info("Analysis Agent ready and waiting for incident transfers...")
        
        # In production, the agent would be triggered by transfers
        # For testing, we can simulate an incident
        if os.environ.get("TEST_MODE") == "true":
            test_incident = {
                "id": "test-incident-001",
                "title": "Suspicious login activity detected",
                "description": "Multiple failed login attempts from unusual location",
                "severity": "high",
                "metadata": {
                    "source_ip": "192.168.1.100",
                    "actor": "user@example.com",
                    "anomaly_type": "brute_force_attempt"
                }
            }
            
            # Create an invocation context for ADK
            from google.adk.agents.invocation_context import InvocationContext
            context = InvocationContext()
            
            result = await agent._execute_agent_logic(context, None, incident=test_incident)
            logger.info(f"Analysis completed: {result}")
        else:
            # Keep agent running
            while True:
                await asyncio.sleep(60)
                
    except KeyboardInterrupt:
        logger.info("Shutting down Analysis Agent...")
    except Exception as e:
        logger.error(f"Error running Analysis Agent: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
