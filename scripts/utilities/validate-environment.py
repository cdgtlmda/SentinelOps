#!/usr/bin/env python3
"""
Environment validation script for SentinelOps.
Checks that all required tools and configurations are in place.
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def check_command(command, min_version=None):
    """Check if a command is available and optionally its version."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            if min_version:
                return "✓", f"Installed ({output})"
            return "✓", "Installed"
        else:
            return "✗", "Not found"
    except Exception as e:
        return "✗", f"Error: {str(e)}"


def check_python_package(package):
    """Check if a Python package is installed."""
    try:
        __import__(package)
        return "✓", "Installed"
    except ImportError:
        return "✗", "Not installed"


def check_env_file():
    """Check if .env file exists and has required variables."""
    env_path = Path(".env")
    example_path = Path(".env.example")

    if not env_path.exists():
        return "✗", ".env file not found (copy from .env.example)"

    # Read required variables from .env.example
    required_vars = []
    if example_path.exists():
        with open(example_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    var_name = line.split("=")[0].strip()
                    required_vars.append(var_name)

    # Check which variables are set in .env
    missing_vars = []
    with open(env_path) as f:
        env_content = f.read()
        for var in required_vars:
            if f"{var}=" not in env_content:
                missing_vars.append(var)

    if missing_vars:
        return "⚠", f"Missing variables: {', '.join(missing_vars[:3])}..."

    return "✓", "All required variables present"


def check_google_cloud_auth():
    """Check Google Cloud authentication."""
    try:
        # First check if gcloud is in PATH
        gcloud_check = subprocess.run(
            ["which", "gcloud"],
            capture_output=True,
            text=True
        )
        if gcloud_check.returncode != 0:
            return "✗", "gcloud not found in PATH"

        # Check authentication
        result = subprocess.run(
            ["gcloud", "auth", "list", "--format=json"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            accounts = json.loads(result.stdout)
            if accounts:
                active = next((a for a in accounts if a.get("status") == "ACTIVE"), None)
                if active:
                    return "✓", f"Authenticated as {active['account']}"
            return "✗", "No active authentication"
        return "✗", "gcloud not installed or not in PATH"
    except Exception as e:
        return "✗", f"Error: {str(e)}"


def check_google_cloud_project():
    """Check if a Google Cloud project is configured."""
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            stderr=subprocess.DEVNULL
        )
        if result.returncode == 0 and result.stdout.strip():
            return "✓", f"Project: {result.stdout.strip()}"
        return "✗", "No project configured"
    except Exception:
        return "✗", "Could not check project"


def main():
    """Run all validation checks."""
    print("SentinelOps Environment Validation")
    print("=" * 50)

    checks = [
        ("Python Version", check_command("python3 --version")),
        ("pip Version", check_command("python3 -m pip --version")),
        ("Git Version", check_command("git --version")),
        ("Google Cloud SDK", check_command("gcloud --version 2>/dev/null | head -1")),
        ("Virtual Environment", ("✓", "Created") if Path("venv").exists() else ("✗", "Not created")),
        ("Environment File", check_env_file()),
        ("Google Cloud Auth", check_google_cloud_auth()),
        ("Google Cloud Project", check_google_cloud_project()),
    ]

    print("\nSystem Requirements:")
    for check_name, (status, message) in checks:
        print("  {status} {check_name}: {message}")

    # Check Python packages
    print("\nPython Dependencies:")
    packages = ["fastapi", "google.cloud.storage", "pytest", "mypy"]
    for package in packages:
        status, message = check_python_package(package)
        print("  {status} {package}: {message}")

    # Check project structure
    print("\nProject Structure:")
    dirs = ["src", "tests", "docs", "scripts", "config"]
    for dir_name in dirs:
        exists = "✓" if Path(dir_name).exists() else "✗"
        print("  {exists} {dir_name}/ directory")

    print("\n" + "=" * 50)
    print("Run 'make install' to install missing dependencies")
    print("Run './scripts/install-gcloud.sh' to install Google Cloud SDK")


if __name__ == "__main__":
    main()
