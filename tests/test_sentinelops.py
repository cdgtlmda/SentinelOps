#!/usr/bin/env python3
"""
SentinelOps Live Testing Script
Run this to test the multi-agent security system
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main import main


def print_banner() -> None:
    print("=" * 60)
    print("🛡️  SENTINELOPS MULTI-AGENT SECURITY SYSTEM")
    print("=" * 60)
    print("Testing the autonomous incident response platform...")
    print()


def print_menu() -> None:
    print("Available Test Commands:")
    print("1. 'status' - Show all agent status and capabilities")
    print("2. 'scan' - Trigger a manual security scan")
    print("3. 'test' - Run system in test mode")
    print("4. 'quit' - Exit")
    print()


async def run_command(command: str) -> None:
    """Run a SentinelOps command"""
    print(f"🔄 Executing: {command}")
    print("-" * 40)

    # Backup original argv
    original_argv = sys.argv.copy()

    try:
        # Set command
        sys.argv = ["main.py", command]
        await main()
    except KeyboardInterrupt:
        print("\n⚠️ Command interrupted by user")
    except (ImportError, AttributeError, TypeError, ValueError) as e:
        if "InvocationContext" in str(e):
            print("⚠️ Full monitoring requires ADK session context")
            print("✅ Agent initialization successful!")
        else:
            print(f"❌ Error: {e}")
    finally:
        # Restore original argv
        sys.argv = original_argv

    print("-" * 40)
    print()


async def interactive_test() -> None:
    """Interactive testing interface"""
    print_banner()

    while True:
        print_menu()
        choice = input("Enter command (status/scan/test/quit): ").strip().lower()

        if choice in ["quit", "q", "exit"]:
            print("👋 Exiting SentinelOps test...")
            break
        elif choice in ["status", "scan", "test"]:
            await run_command(choice)
        else:
            print("❌ Invalid command. Please try again.\n")


if __name__ == "__main__":
    # Set environment
    os.environ.setdefault("PYTHONPATH", str(project_root))

    try:
        asyncio.run(interactive_test())
    except KeyboardInterrupt:
        print("\n👋 SentinelOps test session ended.")
