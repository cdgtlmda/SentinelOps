#!/usr/bin/env python3
"""
Quick verification that SentinelOpsMultiAgent can be instantiated.
"""

import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# pylint: disable=wrong-import-position
from src.multi_agent.sentinelops_multi_agent import SentinelOpsMultiAgent  # noqa: E402
# pylint: enable=wrong-import-position


def verify_multi_agent() -> bool:
    """Verify the multi-agent system can be created."""
    print("Testing SentinelOpsMultiAgent instantiation...")

    # Basic configuration
    config = {
        "project_id": "test-project",
        "detection": {
            "scan_interval_minutes": 5,
            "bigquery_dataset": "security_logs",
            "bigquery_table": "events",
        },
        "analysis": {"vertex_ai_location": "us-central1"},
        "orchestrator": {},
        "remediation": {},
        "communication": {},
    }

    try:
        # Create the multi-agent system
        multi_agent = SentinelOpsMultiAgent(config)
        print(f"✓ Successfully created: {multi_agent}")
        print(f"✓ Sub-agents: {len(multi_agent.sub_agents)}")
        for agent in multi_agent.sub_agents:
            print(f"  - {agent.name}: {agent.description}")
        return True
    except (ValueError, TypeError, ImportError, AttributeError) as e:
        print(f"✗ Failed to create multi-agent system: {e}")
        return False


if __name__ == "__main__":
    success = verify_multi_agent()
    sys.exit(0 if success else 1)
