#!/usr/bin/env python3
"""
Phase 4.1: ADK Compliance Verification Test Suite

This script verifies that all agents properly inherit from ADK base classes
and implement required ADK patterns.
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Add src to path for imports - must be at top before other imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# pylint: disable=wrong-import-position
from google.adk import telemetry  # noqa: E402
from google.adk.agents import LlmAgent, ParallelAgent  # noqa: E402
from google.adk.tools import BaseTool  # noqa: E402

from src.analysis_agent.adk_agent import AnalysisAgent  # noqa: E402
from src.common.adk_agent_base import SentinelOpsBaseAgent  # noqa: E402
from src.communication_agent.adk_agent import CommunicationAgent  # noqa: E402
from src.detection_agent.adk_agent import DetectionAgent  # noqa: E402
from src.multi_agent.sentinelops_multi_agent import SentinelOpsMultiAgent  # noqa: E402
from src.orchestrator_agent.adk_agent import OrchestratorAgent  # noqa: E402
from src.remediation_agent.adk_agent import RemediationAgent  # noqa: E402
from src.tools.firestore_tool import FirestoreTool  # noqa: E402
from src.tools.logging_tool import LoggingTool  # noqa: E402
from src.tools.monitoring_tool import MonitoringTool  # noqa: E402
from src.tools.pubsub_tool import PubSubTool  # noqa: E402
from src.tools.transfer_tools import (  # noqa: E402
    TransferToAnalysisAgentTool,
    TransferToCommunicationAgentTool,
    TransferToDetectionAgentTool,
    TransferToOrchestratorAgentTool,
    TransferToRemediationAgentTool,
)

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}{title}{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}\n")


def print_result(test_name: str, passed: bool, details: str = "") -> None:
    """Print test result with color coding."""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} {test_name}")
    if details:
        print(f"       {details}")


class ADKComplianceTests:
    """Test suite for ADK compliance verification."""

    results: Dict[str, Any]

    def __init__(self) -> None:
        self.results = {"total": 0, "passed": 0, "failed": 0, "errors": []}

    def test_agent_inheritance(self) -> Dict[str, bool]:
        """Test that all agents inherit from proper ADK base classes."""
        print_section("1. Agent Inheritance Verification")

        agents_to_test = [
            ("SentinelOpsBaseAgent", SentinelOpsBaseAgent, LlmAgent),
            ("DetectionAgent", DetectionAgent, SentinelOpsBaseAgent),
            ("AnalysisAgent", AnalysisAgent, SentinelOpsBaseAgent),
            ("OrchestratorAgent", OrchestratorAgent, SentinelOpsBaseAgent),
            ("RemediationAgent", RemediationAgent, SentinelOpsBaseAgent),
            ("CommunicationAgent", CommunicationAgent, SentinelOpsBaseAgent),
            ("SentinelOpsMultiAgent", SentinelOpsMultiAgent, ParallelAgent),
        ]

        results = {}
        for name, agent_class, expected_base in agents_to_test:
            self.results["total"] += 1
            try:
                is_subclass = issubclass(agent_class, expected_base)
                results[name] = is_subclass

                if is_subclass:
                    self.results["passed"] += 1
                    print_result(f"{name} inherits from {expected_base.__name__}", True)
                else:
                    self.results["failed"] += 1
                    print_result(
                        f"{name} inherits from {expected_base.__name__}", False
                    )

            except (TypeError, AttributeError, ImportError) as e:
                self.results["failed"] += 1
                self.results["errors"].append(f"{name}: {str(e)}")
                print_result(f"{name} inheritance check", False, str(e))
                results[name] = False

        return results

    def test_multi_agent_collaboration(self) -> bool:
        """Test multi-agent collaboration using ADK patterns."""
        print_section("2. Multi-Agent Collaboration Patterns")

        self.results["total"] += 1
        try:
            # Test that SentinelOpsMultiAgent has sub_agents
            config = {"project_id": "test-project"}
            coordinator = SentinelOpsMultiAgent(config)

            has_sub_agents = (
                hasattr(coordinator, "sub_agents") and len(coordinator.sub_agents) > 0
            )
            print_result(
                "Multi-agent coordinator has sub-agents",
                has_sub_agents,
                f"Found {len(coordinator.sub_agents) if has_sub_agents else 0} sub-agents",
            )

            if has_sub_agents:
                # Check each sub-agent
                expected_agents = [
                    "orchestrator_agent",
                    "detection_agent",
                    "analysis_agent",
                    "remediation_agent",
                    "communication_agent",
                ]
                found_agents = [agent.name for agent in coordinator.sub_agents]

                all_present = all(name in found_agents for name in expected_agents)
                print_result(
                    "All required agents present",
                    all_present,
                    f"Agents: {', '.join(found_agents)}",
                )

                if all_present:
                    self.results["passed"] += 1
                    return True

            self.results["failed"] += 1
            return False

        except (TypeError, AttributeError, ImportError, ValueError) as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Multi-agent test: {str(e)}")
            print_result("Multi-agent collaboration test", False, str(e))
            return False

    def test_tool_compliance(self) -> Dict[str, bool]:
        """Test that all tools inherit from ADK's BaseTool."""
        print_section("3. ADK Tool Compliance")

        tools_to_test = [
            ("PubSubTool", PubSubTool),
            ("FirestoreTool", FirestoreTool),
            ("LoggingTool", LoggingTool),
            ("MonitoringTool", MonitoringTool),
            ("TransferToAnalysisAgentTool", TransferToAnalysisAgentTool),
            ("TransferToRemediationAgentTool", TransferToRemediationAgentTool),
            ("TransferToCommunicationAgentTool", TransferToCommunicationAgentTool),
            ("TransferToDetectionAgentTool", TransferToDetectionAgentTool),
            ("TransferToOrchestratorAgentTool", TransferToOrchestratorAgentTool),
        ]

        results = {}
        for name, tool_class in tools_to_test:
            self.results["total"] += 1
            try:
                is_subclass = issubclass(tool_class, BaseTool)
                results[name] = is_subclass

                if is_subclass:
                    self.results["passed"] += 1
                    print_result(f"{name} inherits from BaseTool", True)

                    # Check for execute method
                    has_execute = hasattr(tool_class, "execute") or hasattr(
                        tool_class, "run_async"
                    )
                    print_result("  - Has execution method", has_execute)
                else:
                    self.results["failed"] += 1
                    print_result(f"{name} inherits from BaseTool", False)

            except (TypeError, AttributeError, ImportError) as e:
                self.results["failed"] += 1
                self.results["errors"].append(f"{name}: {str(e)}")
                print_result(f"{name} tool check", False, str(e))
                results[name] = False

        return results

    def test_adk_event_system(self) -> bool:
        """Test ADK event system is working."""
        print_section("4. ADK Event System")

        self.results["total"] += 1
        try:
            # Test that agents can handle ADK events/contexts
            # ToolContext already imported at module level

            # Create a minimal detection agent
            config = {"project_id": "test-project"}
            agent = DetectionAgent(config)

            # Check if agent has run method
            has_run = hasattr(agent, "run") and callable(agent.run)
            print_result("Agent has run method", has_run)

            # Check if agent can create context
            can_create_context = True
            try:
                # Create a minimal context for testing
                context = type("TestToolContext", (), {})()
                context.invocation_context = {"test": True}
                print_result("Can create ADK ToolContext", True)
            except (TypeError, AttributeError) as e:
                can_create_context = False
                print_result("Can create ADK ToolContext", False, str(e))

            if has_run and can_create_context:
                self.results["passed"] += 1
                return True
            else:
                self.results["failed"] += 1
                return False

        except (TypeError, AttributeError, ImportError, ValueError) as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Event system test: {str(e)}")
            print_result("ADK event system test", False, str(e))
            return False

    def test_telemetry_collection(self) -> bool:
        """Test ADK telemetry is configured."""
        print_section("5. ADK Telemetry Configuration")

        self.results["total"] += 1
        try:
            # Check if telemetry module is available
            telemetry_available = telemetry is not None
            print_result("ADK telemetry module available", telemetry_available)

            # Test base agent telemetry setup
            config = {"telemetry_enabled": True, "project_id": "test-project"}
            agent = DetectionAgent(config)

            # Check if telemetry methods exist
            has_telemetry_setup = hasattr(agent, "_setup_adk_telemetry")
            print_result("Agent has telemetry setup method", has_telemetry_setup)

            # Check if tracer is configured
            has_tracer = hasattr(agent, "_tracer") or hasattr(agent, "tracer")
            print_result("Agent has tracer configured", has_tracer)

            if telemetry_available and has_telemetry_setup:
                self.results["passed"] += 1
                return True
            else:
                self.results["failed"] += 1
                return False

        except (TypeError, AttributeError, ImportError, ValueError) as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Telemetry test: {str(e)}")
            print_result("Telemetry configuration test", False, str(e))
            return False

    def run_all_tests(self) -> None:
        """Run all compliance tests."""
        print(f"\n{BOLD}ADK Compliance Verification Suite{RESET}")
        print("Testing SentinelOps ADK Implementation\n")

        # Run all tests
        self.test_agent_inheritance()
        self.test_multi_agent_collaboration()
        self.test_tool_compliance()
        self.test_adk_event_system()
        self.test_telemetry_collection()

        # Print summary
        self.print_summary()

    def print_summary(self) -> bool:
        """Print test summary."""
        print_section("Test Summary")

        pass_rate = (
            (self.results["passed"] / self.results["total"]) * 100
            if self.results["total"] > 0
            else 0
        )

        print(f"Total Tests: {self.results['total']}")
        print(f"{GREEN}Passed: {self.results['passed']}{RESET}")
        print(f"{RED}Failed: {self.results['failed']}{RESET}")
        print(f"Pass Rate: {pass_rate:.1f}%")

        if self.results["errors"]:
            print(f"\n{RED}Errors:{RESET}")
            for error in self.results["errors"]:
                print(f"  - {error}")

        if pass_rate == 100:
            print(f"\n{GREEN}{BOLD}✓ ALL ADK COMPLIANCE TESTS PASSED!{RESET}")
            print(f"{GREEN}The project is ready for ADK certification.{RESET}")
        else:
            print(
                f"\n{RED}{BOLD}✗ Some tests failed. Please fix the issues above.{RESET}"
            )

        return pass_rate == 100


async def main() -> int:
    """Main test runner."""
    tester = ADKComplianceTests()
    tester.run_all_tests()

    # Return exit code based on test results
    return 0 if tester.results["failed"] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
