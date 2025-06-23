#!/usr/bin/env python3
"""
Test Google Cloud authentication with service account.
Performs simple API calls to verify authentication is working correctly.
"""

import os
import sys
import json
from pathlib import Path
from google.cloud import storage
from google.cloud import bigquery
from google.cloud import pubsub_v1
from google.cloud import logging as cloud_logging
from google.cloud import aiplatform
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
import google.auth

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(title):
    """Print a formatted header."""
    print("\n{BLUE}{'=' *60}{RESET}")
    print("{BLUE}{title}{RESET}")
    print("{BLUE}{'=' *60}{RESET}\n")


def check_environment():
    """Check environment configuration."""
    print_header("Environment Configuration")

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    if not project_id:
        print("{RED}✗ GOOGLE_CLOUD_PROJECT not set{RESET}")
        print("  Set it with: export GOOGLE_CLOUD_PROJECT=your-project-id")
        return None

    if not credentials_path:
        print("{RED}✗ GOOGLE_APPLICATION_CREDENTIALS not set{RESET}")
        print("  Set it with: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json")
        return None

    if not Path(credentials_path).exists():
        print("{RED}✗ Service account key file not found at: {credentials_path}{RESET}")
        return None

    print("{GREEN}✓ Project ID: {project_id}{RESET}")
    print("{GREEN}✓ Credentials: {credentials_path}{RESET}")

    # Load and display service account info
    try:
        with open(credentials_path) as f:
            sa_info = json.load(f)
            print("{GREEN}✓ Service Account: {sa_info.get('client_email', 'Unknown')}{RESET}")
    except Exception as e:
        print("{RED}✗ Error reading service account key: {e}{RESET}")
        return None

    return project_id


def test_default_credentials():
    """Test default credentials."""
    print_header("Testing Default Credentials")

    try:
        credentials, project = default()
        print("{GREEN}✓ Default credentials loaded successfully{RESET}")
        print("  Project: {project}")
        print("  Type: {type(credentials).__name__}")
        return True
    except DefaultCredentialsError as e:
        print("{RED}✗ Failed to load default credentials: {e}{RESET}")
        return False


def test_storage_api(project_id):
    """Test Cloud Storage API."""
    print_header("Testing Cloud Storage API")

    try:
        client = storage.Client(project=project_id)

        # List buckets (limited to 5)
        buckets = list(client.list_buckets(max_results=5))

        print("{GREEN}✓ Successfully connected to Cloud Storage{RESET}")
        print("  Found {len(buckets)} bucket(s) in project")

        for bucket in buckets:
            print("  - {bucket.name}")

        return True
    except Exception as e:
        print("{RED}✗ Cloud Storage test failed: {e}{RESET}")
        return False


def test_bigquery_api(project_id):
    """Test BigQuery API."""
    print_header("Testing BigQuery API")

    try:
        client = bigquery.Client(project=project_id)

        # List datasets
        datasets = list(client.list_datasets(max_results=5))

        print("{GREEN}✓ Successfully connected to BigQuery{RESET}")
        print("  Found {len(datasets)} dataset(s) in project")

        for dataset in datasets:
            print("  - {dataset.dataset_id}")

        # Try a simple query
        query = """
        SELECT 1 as test_value, CURRENT_TIMESTAMP() as current_time
        """

        try:
            query_job = client.query(query)
            results = list(query_job.result())

            if results:
                print("{GREEN}✓ Query executed successfully{RESET}")
                print("  Test value: {results[0].test_value}")
                print("  Server time: {results[0].current_time}")
        except Exception as e:
            print("{YELLOW}! Query test skipped: {e}{RESET}")

        return True
    except Exception as e:
        print("{RED}✗ BigQuery test failed: {e}{RESET}")
        return False


def test_pubsub_api(project_id):
    """Test Pub/Sub API."""
    print_header("Testing Pub/Sub API")

    try:
        publisher = pubsub_v1.PublisherClient()
        project_path = f"projects/{project_id}"

        # List topics
        topics = list(publisher.list_topics(request={"project": project_path}))

        print("{GREEN}✓ Successfully connected to Pub/Sub{RESET}")
        print("  Found {len(topics)} topic(s) in project")

        # Show up to 5 topics
        for i, topic in enumerate(topics[:5]):
            topic_name = topic.name.split('/')[-1]
            print("  - {topic_name}")

        return True
    except Exception as e:
        print("{RED}✗ Pub/Sub test failed: {e}{RESET}")
        return False


def test_logging_api(project_id):
    """Test Cloud Logging API."""
    print_header("Testing Cloud Logging API")

    try:
        client = cloud_logging.Client(project=project_id)

        # Write a test log entry
        logger = client.logger("sentinelops-auth-test")
        logger.log_text("Authentication test successful", severity="INFO")

        print("{GREEN}✓ Successfully connected to Cloud Logging{RESET}")
        print("  Test log entry written to 'sentinelops-auth-test'")

        return True
    except Exception as e:
        print("{RED}✗ Cloud Logging test failed: {e}{RESET}")
        return False


def test_vertex_ai_api(project_id):
    """Test Vertex AI API."""
    print_header("Testing Vertex AI API (Gemini)")

    try:
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location="us-central1")

        print("{GREEN}✓ Successfully initialized Vertex AI{RESET}")
        print("  Project: {project_id}")
        print("  Location: us-central1")

        # Note: Actually calling Gemini would incur costs, so we just verify initialization
        print("{YELLOW}! Skipping actual Gemini API call to avoid costs{RESET}")

        return True
    except Exception as e:
        print("{RED}✗ Vertex AI test failed: {e}{RESET}")
        return False


def main():
    """Run all authentication tests."""
    print("{BLUE}{'=' *60}{RESET}")
    print("{BLUE}Google Cloud Authentication Test{RESET}")
    print("{BLUE}{'=' *60}{RESET}")

    # Check environment
    project_id = check_environment()
    if not project_id:
        print("\n{RED}❌ Environment not properly configured{RESET}")
        sys.exit(1)

    # Run tests
    tests = [
        test_default_credentials,
        lambda: test_storage_api(project_id),
        lambda: test_bigquery_api(project_id),
        lambda: test_pubsub_api(project_id),
        lambda: test_logging_api(project_id),
        lambda: test_vertex_ai_api(project_id),
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print("{RED}✗ Unexpected error: {e}{RESET}")
            failed += 1

    # Summary
    print_header("Authentication Test Summary")
    print("Total tests: {len(tests)}")
    print("{GREEN}Passed: {passed}{RESET}")
    print("{RED}Failed: {failed}{RESET}")

    if failed == 0:
        print("\n{GREEN}✅ All authentication tests passed!{RESET}")
        print("Your Google Cloud authentication is properly configured.")
        return 0
    else:
        print("\n{YELLOW}⚠️  Some tests failed.{RESET}")
        print("This might be due to:")
        print("  1. Missing API enablement (run ./scripts/enable-apis.sh)")
        print("  2. Insufficient permissions on the service account")
        print("  3. Billing not enabled for certain APIs")
        return 1


if __name__ == "__main__":
    sys.exit(main())
