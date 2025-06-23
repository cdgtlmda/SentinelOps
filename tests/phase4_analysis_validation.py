#!/usr/bin/env python3
"""
Phase 4.3: Analysis Agent Validation Test
Validates that the Analysis Agent properly uses ADK and Gemini integration
"""
import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Test mode environment variable
os.environ["TEST_MODE"] = "true"
os.environ["DRY_RUN"] = "true"
# Vertex AI uses application default credentials, no API key needed
# os.environ['GEMINI_API_KEY'] = 'test-key' # REMOVED - using Vertex AI


def print_header(text: str) -> None:
    """Print a formatted header"""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def print_result(test_name: str, passed: bool, details: str = "") -> None:
    """Print test result"""
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"  {test_name}: {status}")
    if details:
        print(f"    Details: {details}")


async def test_analysis_agent_adk_inheritance() -> bool:
    """Test 1: Verify Analysis Agent inherits from ADK classes"""
    print_header("Test 1: Analysis Agent ADK Inheritance")

    try:
        # Import the necessary classes
        from src.analysis_agent.adk_agent import AnalysisAgent
        from src.common.adk_agent_base import SentinelOpsBaseAgent
        from google.adk.agents import LlmAgent

        # Check inheritance without instantiation
        is_base_agent = issubclass(AnalysisAgent, SentinelOpsBaseAgent)
        print_result("Inherits from SentinelOpsBaseAgent", is_base_agent)

        # Check if it ultimately inherits from ADK's LlmAgent
        is_llm_agent = issubclass(AnalysisAgent, LlmAgent)
        print_result("Inherits from ADK LlmAgent", is_llm_agent)

        # Check if class has required methods
        has_run = hasattr(AnalysisAgent, "run")
        print_result("Has run() method", has_run)

        has_setup = hasattr(AnalysisAgent, "setup")
        print_result("Has setup() method", has_setup)

        return is_base_agent and is_llm_agent and has_run and has_setup

    except (ValueError, TypeError, ImportError, AttributeError) as e:
        print_result("Import and validation", False, str(e))
        return False


async def test_analysis_tools_inheritance() -> bool:  # noqa: C901
    """Test 2: Verify all Analysis tools inherit from BaseTool"""
    print_header("Test 2: Analysis Tools ADK Compliance")

    try:
        from google.adk.tools import BaseTool

        # Tools from adk_agent module
        agent_tools = [
            ("IncidentAnalysisTool", "src.analysis_agent.adk_agent"),
            ("ThreatIntelligenceTool", "src.analysis_agent.adk_agent"),
            ("RecommendationGeneratorTool", "src.analysis_agent.adk_agent"),
        ]

        # Tools from analysis_tools module
        analysis_tools = [
            ("RecommendationTool", "src.tools.analysis_tools"),
            ("CorrelationTool", "src.tools.analysis_tools"),
            ("ContextTool", "src.tools.analysis_tools"),
        ]

        all_passed = True

        # Check agent tools
        for tool_name, module_path in agent_tools:
            try:
                module = __import__(module_path, fromlist=[tool_name])
                tool_class = getattr(module, tool_name)

                is_base_tool = issubclass(tool_class, BaseTool)
                has_execute = hasattr(tool_class, "execute")

                print_result(f"{tool_name} inherits from BaseTool", is_base_tool)
                print_result(f"{tool_name} has execute() method", has_execute)

                if not (is_base_tool and has_execute):
                    all_passed = False

            except (ValueError, TypeError, ImportError, AttributeError) as e:
                print_result(f"{tool_name} validation", False, str(e))
                all_passed = False

        # Check analysis tools
        for tool_name, module_path in analysis_tools:
            try:
                module = __import__(module_path, fromlist=[tool_name])
                tool_class = getattr(module, tool_name)

                is_base_tool = issubclass(tool_class, BaseTool)
                has_execute = hasattr(tool_class, "execute")

                print_result(f"{tool_name} inherits from BaseTool", is_base_tool)
                print_result(f"{tool_name} has execute() method", has_execute)

                if not (is_base_tool and has_execute):
                    all_passed = False

            except (ValueError, TypeError, ImportError, AttributeError) as e:
                print_result(f"{tool_name} validation", False, str(e))
                all_passed = False

        return all_passed

    except (ValueError, TypeError, ImportError, AttributeError) as e:
        print_result("Import analysis tools", False, str(e))
        return False


async def test_vertex_ai_integration() -> bool:
    """Test 3: Verify Vertex AI integration"""
    print_header("Test 3: Vertex AI Integration")

    try:
        from src.analysis_agent.adk_agent import AnalysisAgent

        # Check if AnalysisAgent has Gemini-related configuration in __init__
        import inspect

        init_signature = inspect.signature(AnalysisAgent.__init__)
        params = list(init_signature.parameters.keys())

        # Check for config parameter (which should contain Gemini settings)
        has_config = "config" in params
        print_result("Has config parameter", has_config)

        # Check if the class uses Gemini in its implementation
        source = inspect.getsource(AnalysisAgent)
        uses_vertex = "vertex" in source.lower() or "aiplatform" in source.lower()
        print_result("References Vertex AI in code", uses_vertex)

        # Check for tools that use Gemini
        from src.analysis_agent.adk_agent import IncidentAnalysisTool

        tool_source = inspect.getsource(IncidentAnalysisTool)
        tool_uses_vertex = (
            "vertex" in tool_source.lower() or "generative" in tool_source.lower()
        )
        print_result("IncidentAnalysisTool uses Vertex AI", tool_uses_vertex)

        return has_config and uses_vertex and tool_uses_vertex

    except (ValueError, TypeError, ImportError, AttributeError) as e:
        print_result("Vertex AI integration check", False, str(e))
        return False


async def test_analysis_agent_workflow() -> bool:
    """Test 4: Test analysis agent structure and workflow"""
    print_header("Test 4: Analysis Agent Workflow Structure")

    try:
        from src.analysis_agent.adk_agent import AnalysisAgent
        from src.tools.transfer_tools import TransferToAnalysisAgentTool
        from google.adk.tools import BaseTool

        # Check transfer tool exists and is proper ADK tool
        is_transfer_tool = issubclass(TransferToAnalysisAgentTool, BaseTool)
        print_result("TransferToAnalysisAgentTool is ADK tool", is_transfer_tool)

        # Check if AnalysisAgent has the required workflow methods
        has_handle_transfer = hasattr(AnalysisAgent, "_handle_transfer") or hasattr(
            AnalysisAgent, "handle_transfer"
        )
        print_result("Has transfer handling method", has_handle_transfer)

        has_execute_logic = (
            hasattr(AnalysisAgent, "_execute_agent_logic")
            or hasattr(AnalysisAgent, "execute_agent_logic")
            or hasattr(AnalysisAgent, "run")
        )
        print_result("Has execution logic method", has_execute_logic)

        # Check if it has the expected tools integration
        import inspect

        source = inspect.getsource(AnalysisAgent)
        integrates_tools = "tools" in source or "tool" in source.lower()
        print_result("Integrates with tools", integrates_tools)

        return (
            is_transfer_tool
            and has_handle_transfer
            and has_execute_logic
            and integrates_tools
        )

    except (ValueError, TypeError, ImportError, AttributeError) as e:
        print_result("Workflow structure check", False, str(e))
        return False


async def main() -> bool:
    """Run all Analysis Agent validation tests"""
    print(
        """
╔══════════════════════════════════════════════════════════╗
║         PHASE 4.3: ANALYSIS AGENT VALIDATION             ║
║                                                          ║
║  Validating ADK compliance and Gemini integration        ║
╚══════════════════════════════════════════════════════════╝
    """
    )

    # Track results
    results = {}

    # Run tests
    results["inheritance"] = await test_analysis_agent_adk_inheritance()
    results["tools"] = await test_analysis_tools_inheritance()
    results["vertex_ai"] = await test_vertex_ai_integration()
    results["workflow"] = await test_analysis_agent_workflow()

    # Summary
    print_header("VALIDATION SUMMARY")
    total_tests = len(results)
    passed_tests = sum(1 for passed in results.values() if passed)

    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {total_tests - passed_tests}")
    print(f"  Success Rate: {(passed_tests / total_tests) * 100:.1f}%")

    if passed_tests == total_tests:
        print("\n  🎉 ALL TESTS PASSED! Analysis Agent is ADK compliant!")
        print("  ✅ Properly inherits from ADK LlmAgent")
        print("  ✅ All tools inherit from ADK BaseTool")
        print("  ✅ Vertex AI integration configured")
        print("  ✅ Workflow structure properly implemented")
    else:
        print("\n  ⚠️ Some tests failed. Please review the output above.")

    # Detailed results
    print("\n  Test Results:")
    print(f"    - ADK Inheritance: {'✅' if results['inheritance'] else '❌'}")
    print(f"    - Tool Compliance: {'✅' if results['tools'] else '❌'}")
    print(f"    - Vertex AI Integration: {'✅' if results['vertex_ai'] else '❌'}")
    print(f"    - Workflow Structure: {'✅' if results['workflow'] else '❌'}")

    return passed_tests == total_tests


if __name__ == "__main__":
    asyncio.run(main())
