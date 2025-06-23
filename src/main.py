#!/usr/bin/env python3
"""Main entry point for SentinelOps Multi-Agent System - PRODUCTION"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the project root to the path early for imports
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

# pylint: disable=wrong-import-position
from src.common.config_loader import get_config
from src.multi_agent.sentinelops_multi_agent import create_sentinelops_multi_agent
# pylint: enable=wrong-import-position

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Initialize and run the production multi-agent system"""
    # Get configuration
    project_id = os.environ.get("PROJECT_ID", "your-project-id")

    # Get base configuration
    base_config = get_config()

    # Build coordinator configuration
    config = {
        "project_id": project_id,
        "max_concurrent_incidents": int(
            os.environ.get("MAX_CONCURRENT_INCIDENTS", "50")
        ),
        "health_check_interval_seconds": int(
            os.environ.get("HEALTH_CHECK_INTERVAL", "30")
        ),
        "emergency_threshold": int(os.environ.get("EMERGENCY_THRESHOLD", "10")),
        # Agent configurations
        "detection": base_config.get("detection", {}),
        "analysis": base_config.get("analysis", {}),
        "orchestrator": base_config.get("orchestrator", {}),
        "remediation": base_config.get("remediation", {}),
        "communication": base_config.get("communication", {}),
    }

    # Add environment-specific settings to each agent config
    config["detection"]["project_id"] = project_id
    config["analysis"]["project_id"] = project_id
    config["orchestrator"]["project_id"] = project_id
    config["remediation"]["project_id"] = project_id
    config["remediation"]["dry_run_mode"] = (
        os.environ.get("DRY_RUN_MODE", "true").lower() == "true"
    )
    config["communication"]["project_id"] = project_id

    # Communication settings
    config["communication"]["slack"] = {
        "webhook_url": os.environ.get("SLACK_WEBHOOK_URL", "")
    }
    config["communication"]["email"] = {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "username": os.environ.get("SMTP_USERNAME", ""),
        "password": os.environ.get("SMTP_PASSWORD", ""),
    }

    # Initialize multi-agent system
    multi_agent = create_sentinelops_multi_agent(config)

    logger.info("Starting SentinelOps Multi-Agent System for project: %s", project_id)
    logger.info(
        "System configuration: %d agents initialized", len(multi_agent.sub_agents)
    )

    # Run based on command
    command = sys.argv[1] if len(sys.argv) > 1 else "monitor"

    try:
        if command == "monitor":
            # Start continuous monitoring
            result = await multi_agent.start_monitoring()
            logger.info("Monitoring started: %s", result)

            # Keep running
            while True:
                # Check system metrics periodically
                metrics = multi_agent.get_metrics()
                logger.info(
                    "System metrics: Incidents processed=%s, Uptime=%ss",
                    metrics["incidents_processed"],
                    metrics["uptime_seconds"],
                )

                # Wait 5 minutes before next status check
                await asyncio.sleep(300)

        elif command == "status":
            # Get system metrics
            metrics = multi_agent.get_metrics()
            print("\n=== SentinelOps System Status ===")
            print(f"Uptime: {metrics['uptime_seconds']:.0f} seconds")
            print(f"Incidents Processed: {metrics['incidents_processed']}")
            print("\nAgents:")
            for agent_name, agent_info in metrics["agents"].items():
                print(
                    f"  {agent_name}: {agent_info['description']} "
                    f"(Tools: {agent_info['tools_count']})"
                )

        elif command == "scan":
            # Trigger manual scan by running the detection agent
            from google.adk.agents.invocation_context import InvocationContext

            # Create a minimal InvocationContext for manual scan
            context = InvocationContext(
                session_service=None,  # type: ignore[arg-type]
                invocation_id="manual_scan",
                agent=None,  # type: ignore[arg-type]
                session=None  # type: ignore[arg-type]
            )
            # InvocationContext doesn't have a data attribute, so we'll pass the command differently
            result = await multi_agent.run(context)
            logger.info("Manual scan result: %s", result)

        elif command == "test":
            # Run in test mode
            logger.info("Running in test mode...")

            # Start monitoring
            await multi_agent.start_monitoring()

            # Wait a bit
            await asyncio.sleep(10)

            # Get metrics
            metrics = multi_agent.get_metrics()
            logger.info("Test complete. Metrics: %s", metrics)

        else:
            print(f"Unknown command: {command}")
            print("Usage: python main.py [monitor|status|scan|test]")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Shutting down SentinelOps Multi-Agent System...")
        # Cleanup would go here
    except Exception as e:
        logger.error("Error running multi-agent system: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
