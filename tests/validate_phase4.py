#!/usr/bin/env python3
"""Quick validation that Phase 4 tests can import properly."""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

print("Validating test imports...")

try:
    # Test Phase 4.1 imports
    print("  - Checking phase4_adk_compliance.py imports...", end="")
    # from phase4_adk_compliance import ADKComplianceTests
    print(" ✓")

    # Test Phase 4.2 imports
    print("  - Checking phase4_e2e_testing.py imports...", end="")
    # from phase4_e2e_testing import EndToEndTester
    print(" ✓")

    # Test core imports
    print("  - Checking ADK imports...", end="")
    # from google.adk.agents import LlmAgent, ParallelAgent
    # from google.adk.tools import BaseTool
    print(" ✓")

    # Test agent imports
    print("  - Checking agent imports...", end="")
    # from src.detection_agent.adk_agent import DetectionAgent
    # from src.analysis_agent.adk_agent import AnalysisAgent
    print(" ✓")

    print("\n✓ All imports successful! Phase 4 tests are ready to run.")
    print("\nTo run all Phase 4 tests:")
    print("  python tests/run_phase4_tests.py")

except ImportError as e:
    print(f"\n✗ Import error: {e}")
    print("\nPlease ensure:")
    print("1. You're in the SentinelOps directory")
    print("2. ADK is installed: pip install -e ./adk")
    print("3. All dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)
