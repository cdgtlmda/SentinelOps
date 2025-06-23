#!/usr/bin/env python3
"""
Phase 4: Master Test Runner for ADK Testing & Validation

This script runs all Phase 4 tests:
- 4.1 ADK Compliance Verification
- 4.2 End-to-End Testing
"""

import subprocess
import sys
import os
from datetime import datetime
from typing import List, Optional

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{BOLD}{'=' * 70}{RESET}")
    print(f"{BOLD}{text.center(70)}{RESET}")
    print(f"{BOLD}{'=' * 70}{RESET}\n")


def run_test(
    test_name: str, script_path: str, args: Optional[List[str]] = None
) -> bool:
    """Run a test script and return success status."""
    print(f"{BLUE}Running {test_name}...{RESET}")

    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        # Print output
        print(result.stdout)
        if result.stderr:
            print(f"{RED}Errors:{RESET}")
            print(result.stderr)

        if result.returncode == 0:
            print(f"{GREEN}✓ {test_name} completed successfully{RESET}")
            return True
        else:
            print(
                f"{RED}✗ {test_name} failed with exit code {result.returncode}{RESET}"
            )
            return False

    except (ValueError, TypeError, OSError, subprocess.SubprocessError) as e:
        print(f"{RED}✗ Failed to run {test_name}: {str(e)}{RESET}")
        return False


def main() -> int:
    """Run all Phase 4 tests."""
    print_header("PHASE 4: ADK TESTING & VALIDATION")

    start_time = datetime.now()

    # Get project ID from environment or use default
    project_id = os.environ.get("PROJECT_ID", "test-project")
    print(f"Project ID: {project_id}")

    # Track results
    results = {}

    # Change to tests directory
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(tests_dir)

    # Run 4.1: ADK Compliance Verification
    print_header("4.1 ADK COMPLIANCE VERIFICATION")
    results["compliance"] = run_test(
        "ADK Compliance Verification", "phase4_adk_compliance.py"
    )

    # Run 4.2: End-to-End Testing
    print_header("4.2 END-TO-END TESTING")
    results["e2e"] = run_test(
        "End-to-End Testing", "phase4_e2e_testing.py", [project_id]
    )

    # Print final summary
    print_header("PHASE 4 TEST SUMMARY")

    all_passed = all(results.values())
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print("Test Results:")
    for test, passed in results.items():
        status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
        print(f"  {status} {test}")

    duration = datetime.now() - start_time
    print(f"\nTotal Duration: {duration.total_seconds():.1f} seconds")
    print(f"Tests Passed: {passed_count}/{total_count}")

    if all_passed:
        print(f"\n{GREEN}{BOLD}✓ PHASE 4 COMPLETE: ALL TESTS PASSED!{RESET}")
        print(
            f"{GREEN}The ADK implementation is validated and ready for deployment.{RESET}"
        )
        print(f"\n{BOLD}Next Steps:{RESET}")
        print("1. Run deployment script: scripts/deploy-adk-agents.sh")
        print("2. Complete Phase 6: Hackathon Submission Prep")
        return 0
    else:
        print(f"\n{RED}{BOLD}✗ PHASE 4 INCOMPLETE: Some tests failed{RESET}")
        print(f"{RED}Please fix the failing tests before proceeding.{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
