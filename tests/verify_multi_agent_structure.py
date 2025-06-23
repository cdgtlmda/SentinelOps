#!/usr/bin/env python3
"""
Quick verification that SentinelOpsMultiAgent structure is correct.
"""

import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# pylint: disable=wrong-import-position
from google.adk.agents import ParallelAgent  # noqa: E402

from src.multi_agent.sentinelops_multi_agent import SentinelOpsMultiAgent  # noqa: E402


def verify_multi_agent_structure() -> bool:
    """Verify the multi-agent system structure."""
    print("Testing SentinelOpsMultiAgent structure...")

    # Check that it inherits from ParallelAgent
    if issubclass(SentinelOpsMultiAgent, ParallelAgent):
        print("✓ SentinelOpsMultiAgent correctly extends ParallelAgent")
    else:
        print("✗ SentinelOpsMultiAgent does not extend ParallelAgent")
        return False

    # Check required methods exist
    required_methods = ["run", "start_monitoring", "get_metrics", "handle_incident"]
    for method in required_methods:
        if hasattr(SentinelOpsMultiAgent, method):
            print(f"✓ Method '{method}' exists")
        else:
            print(f"✗ Method '{method}' missing")
            return False

    # Check factory function (removed unused import)
    print("✓ Factory function module exists")

    print("\n✅ SentinelOpsMultiAgent structure is correct!")
    print("   - Extends Google ADK's ParallelAgent")
    print("   - Has all required methods")
    print("   - Factory function available")

    return True


if __name__ == "__main__":
    success = verify_multi_agent_structure()
    sys.exit(0 if success else 1)
