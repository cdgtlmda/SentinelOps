#!/usr/bin/env python3
"""
Integration test for ADK-based agent system.
Tests the complete workflow with business logic integration.
"""

# Standard library imports
import asyncio
import importlib.util
import logging
import os
import sys
from datetime import datetime, timedelta

# First-party imports
from src.analysis_agent.adk_agent import AnalysisAgent
from src.communication_agent.adk_agent import CommunicationAgent
from src.detection_agent.adk_agent import DetectionAgent
from src.orchestrator_agent.adk_agent import OrchestratorAgent
from src.remediation_agent.adk_agent import RemediationAgent

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TEST_PROJECT_ID = "your-gcp-project-id"

# Load agent configuration
config_path = os.path.join(os.path.dirname(__file__), "..", "config", "agent_config.py")
spec = importlib.util.spec_from_file_location("agent_config", config_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load module spec from {config_path}")
agent_config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_config_module)
AGENT_CONFIG = agent_config_module.AGENT_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ADKIntegrationTest:
    """Test the ADK-integrated SentinelOps system."""

    def __init__(self) -> None:
        """Initialize test with all agents."""
        logger.info("Initializing ADK Integration Test...")

        # Initialize all agents with test configuration
        self.detection_agent = self._create_detection_agent()
        self.analysis_agent = self._create_analysis_agent()
        self.orchestrator_agent = self._create_orchestrator_agent()
        self.remediation_agent = self._create_remediation_agent()
        self.communication_agent = self._create_communication_agent()

        logger.info("All agents initialized successfully")

    def _create_detection_agent(self) -> DetectionAgent:
        """Create detection agent with test config."""
        config = AGENT_CONFIG["detection"].copy()
        config["project_id"] = "test-project"
        config["scan_interval_minutes"] = 1
        return DetectionAgent(config)

    def _create_analysis_agent(self) -> AnalysisAgent:
        """Create analysis agent with test config."""
        config = AGENT_CONFIG["analysis"].copy()
        config["project_id"] = "test-project"
        config["vertex_ai_location"] = "us-central1"  # Use Vertex AI location
        return AnalysisAgent(config)

    def _create_orchestrator_agent(self) -> OrchestratorAgent:
        """Create orchestrator agent with test config."""
        config = AGENT_CONFIG["orchestrator"].copy()
        config["project_id"] = "test-project"
        return OrchestratorAgent(config)

    def _create_remediation_agent(self) -> RemediationAgent:
        """Create remediation agent with test config."""
        config = AGENT_CONFIG["remediation"].copy()
        config["project_id"] = "test-project"
        config["dry_run_by_default"] = True  # Always dry run for tests
        return RemediationAgent(config)

    def _create_communication_agent(self) -> CommunicationAgent:
        """Create communication agent with test config."""
        config = AGENT_CONFIG["communication"].copy()
        config["project_id"] = "test-project"
        # Disable actual notifications for testing
        config["channels"]["email"]["enabled"] = False
        config["channels"]["slack"]["enabled"] = False
        config["channels"]["sms"]["enabled"] = False
        return CommunicationAgent(config)

    async def test_detection_with_business_logic(self) -> None:
        """Test detection agent with integrated business logic tools."""
        logger.info("\n=== Testing Detection Agent with Business Logic ===")

        # Create test security events
        test_events = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "actor": "suspicious-user@example.com",
                "source_ip": "192.168.1.100",
                "method_name": "SetIamPolicy",
                "resource_type": "project",
                "status_code": 200,
                "metadata": {"severity": "high"},
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "actor": "suspicious-user@example.com",
                "source_ip": "192.168.1.100",
                "method_name": "UpdateRole",
                "resource_type": "role",
                "status_code": 200,
                "metadata": {"severity": "high"},
            },
        ]
        # Test the rules engine tool
        rules_engine_tool = None
        for tool in self.detection_agent.tools:
            if hasattr(tool, 'name') and tool.name == "rules_engine_tool":
                rules_engine_tool = tool
                break

        if rules_engine_tool:
            logger.info("Testing RulesEngineTool...")
            # Create test context since InvocationContext requires parameters

            class TestContext1:
                def __init__(self) -> None:
                    self.data = {"project_id": "test-project"}
            context = TestContext1()
            if hasattr(rules_engine_tool, 'execute'):
                result = await rules_engine_tool.execute(context, events=test_events)
            else:
                result = {"status": "error", "error": "Tool does not have execute method"}
            logger.info("Rules engine result: %s", result)

            assert result["status"] == "success", "Rules engine should succeed"
            assert "anomalies" in result, "Should return anomalies"
            logger.info(
                "✓ Rules engine detected %d anomalies", len(result["anomalies"])
            )

        # Test the event correlator tool
        correlator_tool = None
        for tool in self.detection_agent.tools:
            if hasattr(tool, 'name') and tool.name == "event_correlator_tool":
                correlator_tool = tool
                break

        if correlator_tool:
            logger.info("Testing EventCorrelatorTool...")
            # Create test context since InvocationContext requires parameters

            class TestContext2:
                def __init__(self) -> None:
                    self.data = {"project_id": "test-project"}
            context2 = TestContext2()
            if hasattr(correlator_tool, 'execute'):
                result = await correlator_tool.execute(context2, events=test_events)
            else:
                result = {"status": "error", "error": "Tool does not have execute method"}
            logger.info("Correlator result: %s", result)

            assert result["status"] == "success", "Correlator should succeed"
            assert "correlated_groups" in result, "Should return correlated groups"
            logger.info("✓ Correlator found %d event groups", result["total_groups"])

    async def test_analysis_with_business_logic(self) -> None:
        """Test analysis agent with integrated business logic tools."""
        logger.info("\n=== Testing Analysis Agent with Business Logic ===")

        # Create test incident for analysis
        test_incident = {
            "id": "test-inc-001",
            "title": "Privilege Escalation Detected",
            "description": "Multiple IAM policy changes from suspicious user",
            "severity": "high",
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {
                "actor": "suspicious-user@example.com",
                "source_ip": "192.168.1.100",
                "actions": ["SetIamPolicy", "UpdateRole"],
                "affected_resources": 2,
            },
        }
        # Test the recommendation engine tool
        recommendation_tool = None
        for tool in self.analysis_agent.tools:
            if hasattr(tool, 'name') and tool.name == "recommendation_engine_tool":
                recommendation_tool = tool
                break

        if recommendation_tool:
            logger.info("Testing RecommendationTool...")
            # Create test context since InvocationContext requires parameters

            class TestContext3:
                def __init__(self) -> None:
                    self.data = {"project_id": "test-project"}
            context = TestContext3()

            analysis_result = {
                "threat_level": "high",
                "attack_pattern": "privilege_escalation",
                "confidence": 0.85,
            }

            if hasattr(recommendation_tool, 'execute'):
                result = await recommendation_tool.execute(
                    context,
                    incident=test_incident,
                    analysis=analysis_result,
                    risk_score=0.85,
                )
            else:
                result = {"status": "error", "error": "Tool does not have execute method"}
            logger.info("Recommendation result: %s", result)

            assert result["status"] == "success", "Recommendation engine should succeed"
            assert "recommendations" in result, "Should return recommendations"
            logger.info(
                "✓ Generated %d recommendations", len(result["recommendations"])
            )

    async def test_full_workflow(self) -> None:
        """Test the complete ADK workflow integration."""
        logger.info("\n=== Testing Full ADK Workflow ===")

        # Step 1: Detection creates an incident
        # Create test context since InvocationContext requires parameters
        class TestContext4:
            def __init__(self) -> None:
                self.data = {"project_id": "test-project"}
        context = TestContext4()
        detection_result = await self.detection_agent._execute_agent_logic(
            context, None
        )
        logger.info("Detection completed: %s", detection_result["status"])

        # Step 2: If incident created, analyze it
        if detection_result.get("incidents_created"):
            incident_id = detection_result["incidents_created"][0]
            logger.info("Incident created: %s", incident_id)

            # Simulate transfer to analysis
            test_incident = {
                "id": incident_id,
                "title": "Test Security Incident",
                "severity": "high",
                "metadata": {"test": True},
            }

            analysis_result = await self.analysis_agent._execute_agent_logic(
                context, None, incident=test_incident
            )
            logger.info("Analysis completed: %s", analysis_result["status"])

        logger.info("✓ Full workflow test completed")

    async def run_all_tests(self) -> bool:
        """Run all integration tests."""
        try:
            await self.test_detection_with_business_logic()
            await self.test_analysis_with_business_logic()
            await self.test_full_workflow()

            logger.info("\n=== All ADK Integration Tests Passed! ===")
            return True

        except (ValueError, TypeError, ImportError, AttributeError, RuntimeError) as e:
            logger.error("Test failed: %s", e, exc_info=True)
            return False


async def main() -> None:
    """Run the ADK integration tests."""
    test = ADKIntegrationTest()
    success = await test.run_all_tests()

    if success:
        logger.info("\n✅ ADK Integration Successful!")
        logger.info("The ADK framework is properly integrated with the business logic.")
    else:
        logger.error("\n❌ ADK Integration Failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
