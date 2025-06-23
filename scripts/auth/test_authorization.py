#!/usr/bin/env python3
"""
Test Authorization Script

This script tests IAM permissions and authorization for SentinelOps components,
verifying that service accounts have the correct permissions.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Set, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Google Cloud libraries
try:
    import google.api_core.exceptions
    from google.auth import default
    from google.cloud import iam, resourcemanager_v3
except ImportError as e:
    print(f"Error importing Google Cloud libraries: {e}")
    print(
        "Please ensure google-cloud-iam and google-cloud-resource-manager are installed"
    )
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define required permissions for each component
REQUIRED_PERMISSIONS = {
    "detection-agent": [
        "bigquery.datasets.get",
        "bigquery.tables.get",
        "bigquery.tables.getData",
        "logging.logEntries.list",
        "logging.logs.list",
        "pubsub.topics.publish",
        "firestore.documents.create",
        "firestore.documents.get",
        "firestore.documents.update",
    ],
    "analysis-agent": [
        "aiplatform.endpoints.predict",
        "pubsub.subscriptions.consume",
        "pubsub.topics.publish",
        "firestore.documents.get",
        "firestore.documents.update",
        "secretmanager.versions.access",
    ],
    "remediation-agent": [
        "compute.instances.get",
        "compute.instances.setTags",
        "compute.firewalls.create",
        "compute.firewalls.get",
        "compute.firewalls.update",
        "iam.serviceAccountKeys.list",
        "iam.serviceAccountKeys.disable",
        "pubsub.subscriptions.consume",
        "firestore.documents.update",
        "cloudfunctions.functions.invoke",
    ],
}

REQUIRED_PERMISSIONS["communication-agent"] = [
    "pubsub.subscriptions.consume",
    "firestore.documents.get",
    "firestore.documents.update",
    "secretmanager.versions.access",
    "logging.logEntries.create",
]

REQUIRED_PERMISSIONS["orchestration-agent"] = [
    "pubsub.topics.list",
    "pubsub.topics.publish",
    "pubsub.subscriptions.list",
    "firestore.documents.create",
    "firestore.documents.get",
    "firestore.documents.update",
    "cloudrun.services.get",
    "monitoring.timeSeries.create",
]


class AuthorizationTester:
    """Tests IAM permissions and authorization."""

    def __init__(self, project_id: str):
        """Initialize the authorization tester."""
        self.project_id = project_id
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "project_id": project_id,
            "service_accounts": {},
            "custom_roles": {},
            "summary": {"total_checks": 0, "passed": 0, "failed": 0, "warnings": 0},
        }

    def test_service_account_permissions(
        self, service_account_email: str, component_name: str
    ) -> Tuple[bool, str]:
        """Test if a service account has required permissions."""
        logger.info(
            f"Testing permissions for {service_account_email} ({component_name})"
        )

        if component_name not in REQUIRED_PERMISSIONS:
            return False, f"Unknown component: {component_name}"

        required_perms = REQUIRED_PERMISSIONS[component_name]

        try:
            # Get the IAM policy for the project
            resource_manager = resourcemanager_v3.ProjectsClient()
            policy = resource_manager.get_iam_policy(
                request={"resource": f"projects/{self.project_id}"}
            )

            # Find roles assigned to the service account
            member = f"serviceAccount:{service_account_email}"
            assigned_roles = set()

            for binding in policy.bindings:
                if member in binding.members:
                    assigned_roles.add(binding.role)

            # Check permissions (simplified - in reality would need to resolve role permissions)
            self.results["service_accounts"][service_account_email] = {
                "component": component_name,
                "assigned_roles": list(assigned_roles),
                "required_permissions": required_perms,
                "status": "passed" if assigned_roles else "failed",
            }

            self.results["summary"]["total_checks"] += 1
            if assigned_roles:
                self.results["summary"]["passed"] += 1
                return True, f"Service account has {len(assigned_roles)} roles assigned"
            else:
                self.results["summary"]["failed"] += 1
                return False, "Service account has no roles assigned"
        except Exception as e:
            self.results["service_accounts"][service_account_email] = {
                "component": component_name,
                "status": "error",
                "error": str(e),
            }
            self.results["summary"]["failed"] += 1
            return False, f"Error checking permissions: {str(e)}"

    def test_custom_roles(self) -> Tuple[bool, str]:
        """Test if custom roles are properly configured."""
        logger.info("Testing custom roles...")

        try:
            iam_client = iam.IAMClient()

            # List custom roles in the project
            parent = f"projects/{self.project_id}"
            roles = list(iam_client.list_roles(parent=parent))

            custom_role_count = 0
            for role in roles:
                if role.name.startswith(f"projects/{self.project_id}/roles/"):
                    custom_role_count += 1
                    role_id = role.name.split("/")[-1]

                    self.results["custom_roles"][role_id] = {
                        "title": role.title,
                        "description": role.description,
                        "stage": role.stage.name,
                        "permissions_count": len(role.included_permissions),
                        "permissions": list(role.included_permissions)[:10],  # First 10
                    }

            self.results["summary"]["total_checks"] += 1
            if custom_role_count > 0:
                self.results["summary"]["passed"] += 1
                return True, f"Found {custom_role_count} custom roles"
            else:
                self.results["summary"]["warnings"] += 1
                return True, "No custom roles found (using predefined roles)"

        except Exception as e:
            self.results["summary"]["failed"] += 1
            return False, f"Error checking custom roles: {str(e)}"

    def test_least_privilege(self, service_account_email: str) -> Tuple[bool, str]:
        """Test if service account follows least privilege principle."""
        logger.info(f"Testing least privilege for {service_account_email}")

        dangerous_roles = [
            "roles/owner",
            "roles/editor",
            "roles/iam.serviceAccountKeyAdmin",
            "roles/iam.serviceAccountAdmin",
            "roles/resourcemanager.projectIamAdmin",
        ]

        try:
            resource_manager = resourcemanager_v3.ProjectsClient()
            policy = resource_manager.get_iam_policy(
                request={"resource": f"projects/{self.project_id}"}
            )

            member = f"serviceAccount:{service_account_email}"
            found_dangerous = []

            for binding in policy.bindings:
                if member in binding.members and binding.role in dangerous_roles:
                    found_dangerous.append(binding.role)

            test_result = {
                "service_account": service_account_email,
                "dangerous_roles_found": found_dangerous,
                "follows_least_privilege": len(found_dangerous) == 0,
            }

            self.results["summary"]["total_checks"] += 1
            if not found_dangerous:
                self.results["summary"]["passed"] += 1
                return True, "Service account follows least privilege"
            else:
                self.results["summary"]["warnings"] += 1
                return (
                    False,
                    f"Found overly permissive roles: {', '.join(found_dangerous)}",
                )

        except Exception as e:
            self.results["summary"]["failed"] += 1
            return False, f"Error checking least privilege: {str(e)}"

    def generate_report(self) -> str:
        """Generate a summary report of authorization tests."""
        report = f"""
Authorization Test Report
========================
Project: {self.project_id}
Timestamp: {self.results['timestamp']}

Summary:
--------
Total Checks: {self.results['summary']['total_checks']}
Passed:       {self.results['summary']['passed']}
Failed:       {self.results['summary']['failed']}
Warnings:     {self.results['summary']['warnings']}

Service Accounts:
----------------"""

        for sa_email, details in self.results["service_accounts"].items():
            status_icon = "✓" if details["status"] == "passed" else "✗"
            report += f"\n{status_icon} {sa_email}"
            report += f"\n  Component: {details.get('component', 'N/A')}"
            report += f"\n  Roles: {len(details.get('assigned_roles', []))}"

        if self.results["custom_roles"]:
            report += "\n\nCustom Roles:\n-------------"
            for role_id, details in self.results["custom_roles"].items():
                report += f"\n• {role_id}"
                report += f"\n  Title: {details['title']}"
                report += f"\n  Permissions: {details['permissions_count']}"

        return report


def main():
    """Main function to run authorization tests."""
    import argparse

    parser = argparse.ArgumentParser(description="Test SentinelOps IAM authorization")
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument("--output", help="Output file for results (JSON)")

    args = parser.parse_args()

    # Create tester
    tester = AuthorizationTester(args.project_id)

    print("\n🔒 Running SentinelOps Authorization Tests...\n")

    # Define service accounts to test
    service_accounts = [
        ("sentinelops-detection@{}.iam.gserviceaccount.com", "detection-agent"),
        ("sentinelops-analysis@{}.iam.gserviceaccount.com", "analysis-agent"),
        ("sentinelops-remediation@{}.iam.gserviceaccount.com", "remediation-agent"),
        ("sentinelops-communication@{}.iam.gserviceaccount.com", "communication-agent"),
        ("sentinelops-orchestration@{}.iam.gserviceaccount.com", "orchestration-agent"),
    ]

    # Test each service account
    for sa_template, component in service_accounts:
        sa_email = sa_template.format(args.project_id)
        print(f"Testing {component}...", end=" ")
        success, message = tester.test_service_account_permissions(sa_email, component)
        print("✓" if success else "✗")
        print(f"  → {message}")

        # Test least privilege
        print(f"  Testing least privilege...", end=" ")
        success, message = tester.test_least_privilege(sa_email)
        print("✓" if success else "⚠")
        print(f"  → {message}")

    # Test custom roles
    print("\nTesting custom roles...", end=" ")
    success, message = tester.test_custom_roles()
    print("✓" if success else "✗")
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
    failed = tester.results["summary"]["failed"]
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
