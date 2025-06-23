#!/usr/bin/env python3
"""
Script to check Google Cloud connectivity and service availability.
"""

import os
import sys
import json
from typing import Dict, Tuple, Optional


def check_environment_vars() -> Tuple[bool, str]:
    """Check if required environment variables are set."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not project_id:
        return False, "GOOGLE_CLOUD_PROJECT not set"

    if creds_path and not os.path.exists(creds_path):
        return False, f"Credentials file not found: {creds_path}"

    return True, f"Project: {project_id}"


def check_gcloud_cli() -> Tuple[bool, str]:
    """Check if gcloud CLI is installed and authenticated."""
    try:
        import subprocess

        # Check if gcloud is installed
        result = subprocess.run(
            ["gcloud", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return False, "gcloud CLI not installed"

        # Check authentication
        auth_result = subprocess.run(
            ["gcloud", "auth", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if auth_result.returncode == 0:
            accounts = json.loads(auth_result.stdout)
            active = [a for a in accounts if a.get("status") == "ACTIVE"]
            if active:
                return True, f"Authenticated as {active[0]['account']}"
            else:
                return False, "No active gcloud authentication"

        return False, "Could not check gcloud authentication"

    except FileNotFoundError:
        return False, "gcloud CLI not found in PATH"
    except Exception as e:
        return False, f"Error checking gcloud: {str(e)}"


def check_google_cloud_apis() -> Dict[str, Tuple[bool, str]]:
    """Check connectivity to Google Cloud APIs."""
    results = {}

    # Try to import Google Cloud libraries
    apis = {
        "Storage": "google.cloud.storage",
        "BigQuery": "google.cloud.bigquery",
        "Pub/Sub": "google.cloud.pubsub_v1",
        "Compute": "google.cloud.compute_v1",
        "Logging": "google.cloud.logging",
        "Vertex AI": "google.cloud.aiplatform",
    }

    for api_name, module_name in apis.items():
        try:
            __import__(module_name)
            results[api_name] = (True, "Library installed")
        except ImportError:
            results[api_name] = (False, "Library not installed")

    return results


def test_api_connectivity() -> Dict[str, Tuple[bool, str]]:
    """Test actual connectivity to Google Cloud services."""
    results = {}

    # Test Storage
    try:
        from google.cloud import storage
        client = storage.Client()
        list(client.list_buckets(max_results=1))
        results["Storage API"] = (True, "Connected")
    except Exception as e:
        results["Storage API"] = (False, f"Error: {str(e)}")

    # Test BigQuery
    try:
        from google.cloud import bigquery
        client = bigquery.Client()
        list(client.list_datasets(max_results=1))
        results["BigQuery API"] = (True, "Connected")
    except Exception as e:
        results["BigQuery API"] = (False, f"Error: {str(e)}")

    return results


def main():
    """Run all connectivity checks."""
    print("Google Cloud Connectivity Check")
    print("=" * 50)

    # Check environment variables
    env_ok, env_msg = check_environment_vars()
    print("\nEnvironment Variables: {'✓' if env_ok else '✗'} {env_msg}")

    # Check gcloud CLI
    gcloud_ok, gcloud_msg = check_gcloud_cli()
    print("gcloud CLI: {'✓' if gcloud_ok else '✗'} {gcloud_msg}")

    # Check Google Cloud libraries
    print("\nGoogle Cloud Libraries:")
    api_results = check_google_cloud_apis()
    for api_name, (ok, msg) in api_results.items():
        print("  {'✓' if ok else '✗'} {api_name}: {msg}")

    # Test API connectivity if environment is set up
    if env_ok:
        print("\nAPI Connectivity Tests:")
        connectivity_results = test_api_connectivity()
        for api_name, (ok, msg) in connectivity_results.items():
            print("  {'✓' if ok else '✗'} {api_name}: {msg}")
    else:
        print("\nSkipping API connectivity tests (environment not configured)")

    print("\n" + "=" * 50)

    # Return non-zero if any critical checks failed
    if not env_ok or not all(ok for ok, _ in api_results.values()):
        print("Some checks failed. Please install missing dependencies.")
        sys.exit(1)
    else:
        print("All critical checks passed!")


if __name__ == "__main__":
    main()
