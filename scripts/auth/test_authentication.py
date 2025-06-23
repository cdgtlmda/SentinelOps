#!/usr/bin/env python3
"""
Test Authentication Script

This script tests various authentication mechanisms for SentinelOps,
including service account authentication, OIDC, and API key validation.
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Google Cloud libraries
try:
    import google.auth.exceptions
    from google.auth import default
    from google.auth.transport.requests import Request
    from google.cloud import iam, secretmanager
    from google.oauth2 import service_account
except ImportError as e:
    print(f"Error importing Google Cloud libraries: {e}")
    print(
        "Please ensure google-cloud-iam and google-cloud-secret-manager are installed"
    )
    sys.exit(1)
# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AuthenticationTester:
    """Tests various authentication mechanisms."""

    def __init__(self, project_id: str):
        """Initialize the authentication tester."""
        self.project_id = project_id
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "project_id": project_id,
            "tests": {},
        }

    def test_default_credentials(self) -> Tuple[bool, str]:
        """Test default application credentials."""
        test_name = "default_credentials"
        logger.info("Testing default application credentials...")

        try:
            credentials, project = default()

            # Try to refresh the credentials
            if hasattr(credentials, "refresh"):
                request = Request()
                credentials.refresh(request)

            self.results["tests"][test_name] = {
                "status": "passed",
                "message": f"Successfully authenticated with project: {project}",
                "credential_type": type(credentials).__name__,
            }
            return True, "Default credentials working"
        except google.auth.exceptions.DefaultCredentialsError as e:
            self.results["tests"][test_name] = {
                "status": "failed",
                "message": f"Default credentials error: {str(e)}",
                "error": str(e),
            }
            return False, f"Default credentials failed: {str(e)}"
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "failed",
                "message": f"Unexpected error: {str(e)}",
                "error": str(e),
            }
            return False, f"Unexpected error: {str(e)}"

    def test_service_account_key(self, key_path: str = None) -> Tuple[bool, str]:
        """Test service account key authentication."""
        test_name = "service_account_key"
        logger.info("Testing service account key authentication...")

        if not key_path:
            key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

        if not key_path or not os.path.exists(key_path):
            self.results["tests"][test_name] = {
                "status": "skipped",
                "message": "No service account key path provided or found",
            }
            return False, "Service account key test skipped - no key path"

        try:
            credentials = service_account.Credentials.from_service_account_file(
                key_path, scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            # Test the credentials by making an API call
            iam_client = iam.IAMClient(credentials=credentials)

            # Try to list service accounts (this will fail if auth is bad)
            service_account_email = credentials.service_account_email
            name = f"projects/{self.project_id}/serviceAccounts/{service_account_email}"

            try:
                sa = iam_client.get_service_account(request={"name": name})
                self.results["tests"][test_name] = {
                    "status": "passed",
                    "message": f"Successfully authenticated with service account: {service_account_email}",
                    "service_account": service_account_email,
                }
                return (
                    True,
                    f"Service account authentication successful: {service_account_email}",
                )
            except Exception as api_error:
                self.results["tests"][test_name] = {
                    "status": "failed",
                    "message": f"Service account exists but API call failed: {str(api_error)}",
                    "service_account": service_account_email,
                    "error": str(api_error),
                }
                return False, f"Service account auth failed: {str(api_error)}"

        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "failed",
                "message": f"Failed to load service account key: {str(e)}",
                "error": str(e),
            }
            return False, f"Service account key error: {str(e)}"

    def test_oidc_authentication(self) -> Tuple[bool, str]:
        """Test OIDC authentication setup."""
        test_name = "oidc_authentication"
        logger.info("Testing OIDC authentication...")

        try:
            # Check if OIDC is configured by looking for workload identity pools
            cmd = [
                "gcloud",
                "iam",
                "workload-identity-pools",
                "list",
                "--project",
                self.project_id,
                "--location",
                "global",
                "--format",
                "json",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                self.results["tests"][test_name] = {
                    "status": "failed",
                    "message": "Failed to list workload identity pools",
                    "error": result.stderr,
                }
                return False, f"OIDC test failed: {result.stderr}"

            pools = json.loads(result.stdout) if result.stdout else []

            if pools:
                self.results["tests"][test_name] = {
                    "status": "passed",
                    "message": f"Found {len(pools)} workload identity pools",
                    "pools": [pool.get("name", "").split("/")[-1] for pool in pools],
                }
                return True, f"OIDC configured with {len(pools)} pools"
            else:
                self.results["tests"][test_name] = {
                    "status": "warning",
                    "message": "No workload identity pools found",
                }
                return True, "No OIDC pools configured"
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "failed",
                "message": f"OIDC test error: {str(e)}",
                "error": str(e),
            }
            return False, f"OIDC test error: {str(e)}"

    def test_api_key_access(self) -> Tuple[bool, str]:
        """Test API key access from Secret Manager."""
        test_name = "api_key_access"
        logger.info("Testing API key access from Secret Manager...")

        try:
            client = secretmanager.SecretManagerServiceClient()

            # List secrets to find API keys
            parent = f"projects/{self.project_id}"
            secrets = list(client.list_secrets(request={"parent": parent}))

            api_key_secrets = [
                s
                for s in secrets
                if "api" in s.name.lower() and "key" in s.name.lower()
            ]

            if api_key_secrets:
                # Try to access one of the API key secrets
                secret_name = api_key_secrets[0].name
                try:
                    version_name = f"{secret_name}/versions/latest"
                    response = client.access_secret_version(
                        request={"name": version_name}
                    )

                    self.results["tests"][test_name] = {
                        "status": "passed",
                        "message": f"Successfully accessed {len(api_key_secrets)} API key secrets",
                        "api_keys_found": len(api_key_secrets),
                    }
                    return (
                        True,
                        f"API key access successful - found {len(api_key_secrets)} keys",
                    )
                except Exception as access_error:
                    self.results["tests"][test_name] = {
                        "status": "failed",
                        "message": f"Found secrets but cannot access: {str(access_error)}",
                        "error": str(access_error),
                    }
                    return False, f"API key access denied: {str(access_error)}"
            else:
                self.results["tests"][test_name] = {
                    "status": "warning",
                    "message": "No API key secrets found in Secret Manager",
                }
                return True, "No API key secrets found"

        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "failed",
                "message": f"Secret Manager error: {str(e)}",
                "error": str(e),
            }
            return False, f"Secret Manager error: {str(e)}"

    def test_impersonation(
        self, target_service_account: str = None
    ) -> Tuple[bool, str]:
        """Test service account impersonation."""
        test_name = "service_account_impersonation"
        logger.info("Testing service account impersonation...")

        if not target_service_account:
            # Try to find a service account to impersonate
            target_service_account = (
                f"sentinelops-agent@{self.project_id}.iam.gserviceaccount.com"
            )

        try:
            from google.auth import impersonated_credentials

            # Get source credentials
            source_credentials, _ = default()

            # Create impersonated credentials
            target_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
            impersonated_creds = impersonated_credentials.Credentials(
                source_credentials=source_credentials,
                target_principal=target_service_account,
                target_scopes=target_scopes,
                lifetime=3600,
            )
            # Test the impersonated credentials
            request = Request()
            impersonated_creds.refresh(request)

            self.results["tests"][test_name] = {
                "status": "passed",
                "message": f"Successfully impersonated {target_service_account}",
                "target_account": target_service_account,
            }
            return True, f"Impersonation successful: {target_service_account}"

        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "failed",
                "message": f"Impersonation failed: {str(e)}",
                "target_account": target_service_account,
                "error": str(e),
            }
            return False, f"Impersonation failed: {str(e)}"

    def generate_report(self) -> str:
        """Generate a summary report of all tests."""
        passed = sum(
            1 for t in self.results["tests"].values() if t["status"] == "passed"
        )
        failed = sum(
            1 for t in self.results["tests"].values() if t["status"] == "failed"
        )
        warnings = sum(
            1 for t in self.results["tests"].values() if t["status"] == "warning"
        )
        skipped = sum(
            1 for t in self.results["tests"].values() if t["status"] == "skipped"
        )

        report = f"""
Authentication Test Report
========================
Project: {self.project_id}
Timestamp: {self.results['timestamp']}

Summary:
--------
Passed:   {passed}
Failed:   {failed}
Warnings: {warnings}
Skipped:  {skipped}

Test Results:
------------"""
        for test_name, result in self.results["tests"].items():
            status_icon = {
                "passed": "✓",
                "failed": "✗",
                "warning": "⚠",
                "skipped": "-",
            }.get(result["status"], "?")

            report += f"\n{status_icon} {test_name}: {result['message']}"

        return report


def main():
    """Main function to run authentication tests."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test SentinelOps authentication mechanisms"
    )
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument(
        "--service-account-key", help="Path to service account key file"
    )
    parser.add_argument(
        "--target-service-account", help="Service account to test impersonation"
    )
    parser.add_argument("--output", help="Output file for results (JSON)")

    args = parser.parse_args()

    # Create tester
    tester = AuthenticationTester(args.project_id)

    # Run tests
    print("\n🔐 Running SentinelOps Authentication Tests...\n")

    tests = [
        ("Default Credentials", tester.test_default_credentials),
        (
            "Service Account Key",
            lambda: tester.test_service_account_key(args.service_account_key),
        ),
        ("OIDC Authentication", tester.test_oidc_authentication),
        ("API Key Access", tester.test_api_key_access),
        (
            "Service Account Impersonation",
            lambda: tester.test_impersonation(args.target_service_account),
        ),
    ]

    for test_name, test_func in tests:
        print(f"Running {test_name}...", end=" ")
        success, message = test_func()
        if success:
            print("✓")
        else:
            print("✗")
        print(f"  → {message}")

    # Generate report
    report = tester.generate_report()
    print(report)

    # Save results if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(tester.results, f, indent=2)
        print(f"\nResults saved to: {args.output}")

    # Exit with appropriate code
    failed_count = sum(
        1 for t in tester.results["tests"].values() if t["status"] == "failed"
    )
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == "__main__":
    main()
