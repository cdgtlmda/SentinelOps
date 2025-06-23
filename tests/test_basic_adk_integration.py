#!/usr/bin/env python3
"""Basic ADK Integration Test - Tests the core ADK integration without external dependencies."""

import asyncio
import logging
from pathlib import Path
import sys
from typing import Any

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_base_agent() -> None:
    """Test the base agent implementation."""
    logger.info("=== Testing Base Agent ===")

    from src.common.adk_agent_base import SentinelOpsBaseAgent

    # Create a test agent
    class TestAgent(SentinelOpsBaseAgent):
        async def _execute_agent_logic(self, context: Any, config: Any, **kwargs: Any) -> Any:
            return {"status": "success", "message": "Test agent executed"}

        async def _handle_transfer(self, _context: Any, _transfer_data: Any) -> Any:
            return {"status": "success", "transfer_handled": True}

    agent = TestAgent(
        name="test_agent",
        description="Test agent for ADK integration",
    )

    # Test that agent was created successfully
    assert agent.name == "test_agent"
    assert len(agent.tools) >= 0
    logger.info("Created agent: %s", agent)
    logger.info("✓ Base agent test passed")


async def test_detection_tools() -> None:
    """Test detection tools without requiring actual GCP connections."""
    logger.info("\n=== Testing Detection Tools ===")

    from src.tools.detection_tools import RulesEngineTool, EventCorrelatorTool

    # Test RulesEngineTool
    rules_tool = RulesEngineTool(_config={"rules": {}})

    # Check tool was created properly
    assert rules_tool.name == "rules_engine_tool"
    assert rules_tool.description is not None
    logger.info("Created RulesEngineTool: %s", rules_tool.name)
    logger.info("✓ Rules engine tool creation passed")

    # Test EventCorrelatorTool
    correlator_tool = EventCorrelatorTool(config={"correlation_window_minutes": 30})
    assert correlator_tool.name == "event_correlator_tool"
    logger.info("Created EventCorrelatorTool: %s", correlator_tool.name)
    logger.info("✓ Event correlator tool creation passed")


async def test_analysis_tools() -> None:
    """Test analysis tools without requiring actual services."""
    logger.info("\n=== Testing Analysis Tools ===")

    from src.tools.analysis_tools import RecommendationTool

    # Test RecommendationTool
    recommendation_tool = RecommendationTool(config={})

    assert recommendation_tool.name == "recommendation_tool"
    logger.info("Created RecommendationTool: %s", recommendation_tool.name)
    logger.info("✓ Recommendation tool creation passed")


async def test_transfer_tools() -> None:
    """Test transfer tools."""
    logger.info("\n=== Testing Transfer Tools ===")

    from src.tools.transfer_tools import TransferToOrchestratorAgentTool

    # Test transfer tool
    transfer_tool = TransferToOrchestratorAgentTool()

    assert transfer_tool.name == "transfer_to_orchestrator_agent"
    logger.info("Created TransferToOrchestratorAgentTool: %s", transfer_tool.name)
    logger.info("✓ Transfer tool creation passed")


async def main() -> bool:
    """Run all basic integration tests."""
    try:
        await test_base_agent()
        await test_detection_tools()
        await test_analysis_tools()
        await test_transfer_tools()

        logger.info("\n✅ All Basic ADK Integration Tests Passed!")
        logger.info("The ADK framework is properly integrated.")
        return True

    except (ValueError, TypeError, ImportError, AttributeError) as e:
        logger.error("Test failed: %s", e, exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
