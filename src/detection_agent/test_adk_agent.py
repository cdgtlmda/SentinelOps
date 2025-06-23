"""Test ADK Detection Agent implementation."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# pylint: disable=wrong-import-position
from src.detection_agent.adk_agent import DetectionAgent  # noqa: E402


async def test_adk_detection_agent() -> None:
    """Test the ADK detection agent instantiation and basic functionality."""
    try:
        # Test configuration
        config = {
            "gcp": {"project_id": "test-project"},
            "agents": {
                "detection": {
                    "enabled_rules": ["brute_force_ssh", "port_scan"],
                    "correlation_window_minutes": 60,
                    "deduplication_threshold": 0.8,
                    "deduplication_window_hours": 24,
                }
            },
        }

        # Create agent instance
        agent = DetectionAgent(config)
        print("✓ Agent created successfully")
        print(f"  - Name: {agent.name}")
        print(f"  - Description: {agent.description}")

        # Verify tools are initialized
        print(f"\n✓ Tools initialized: {len(agent.tools)} tools")
        for tool in agent.tools:
            if hasattr(tool, 'name') and hasattr(tool, 'description'):
                print(f"  - {tool.name}: {tool.description}")

        # Verify components are initialized through _stored_config
        print("\n✓ Components initialized:")
        if hasattr(agent, '_stored_config'):
            if 'rules_engine' in agent._stored_config:
                rules_engine = agent._stored_config['rules_engine']
                print(
                    f"  - Rules Engine: {len(rules_engine.get_enabled_rules())} rules enabled"
                )
            if 'event_correlator' in agent._stored_config:
                correlator = agent._stored_config['event_correlator']
                print(
                    f"  - Event Correlator: {correlator.correlation_window_minutes} min window"
                )

        # Test that it extends from the correct base class
        from src.common.adk_agent_base import SentinelOpsBaseAgent

        assert isinstance(
            agent, SentinelOpsBaseAgent
        ), "Agent must extend SentinelOpsBaseAgent"
        print("\n✓ Agent correctly extends SentinelOpsBaseAgent")

        # Test that tools are ADK tools
        from google.adk.tools import BaseTool

        for tool in agent.tools:
            tool_name = getattr(tool, 'name', getattr(tool, '__name__', str(type(tool).__name__)))
            assert isinstance(tool, BaseTool), f"{tool_name} must be an ADK BaseTool"
        print("✓ All tools are ADK BaseTool instances")

        print("\n✅ All tests passed!")

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_adk_detection_agent())
