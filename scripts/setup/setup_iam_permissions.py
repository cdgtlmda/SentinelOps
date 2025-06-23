#!/usr/bin/env python3
"""
Set up IAM permissions for SentinelOps
Implements checklist item: Set up IAM permissions
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402

# Load environment variables
load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")

# Service accounts to create
SERVICE_ACCOUNTS = {
    "sentinelops-orchestrator": {
        "display_name": "SentinelOps Orchestrator",
        "description": "Service account for the orchestration agent that coordinates all other agents",
        "roles": [
            "roles/pubsub.publisher",
            "roles/pubsub.subscriber",
            "roles/firestore.dataOwner",
            "roles/bigquery.dataViewer",
            "roles/logging.logWriter",
            "roles/monitoring.metricWriter",
            "roles/secretmanager.secretAccessor",
            "roles/cloudtrace.agent",
            "roles/run.invoker",  # To invoke other Cloud Run services
        ],
    },
    "sentinelops-detection": {
        "display_name": "SentinelOps Detection Agent",
        "description": "Service account for the detection agent that scans logs and identifies threats",
        "roles": [
            "roles/bigquery.dataViewer",
            "roles/bigquery.jobUser",
            "roles/logging.viewer",
            "roles/pubsub.publisher",
            "roles/firestore.dataWriter",
            "roles/logging.logWriter",
            "roles/monitoring.metricWriter",
            "roles/secretmanager.secretAccessor",
        ],
    },
    "sentinelops-analysis": {
        "display_name": "SentinelOps Analysis Agent",
        "description": "Service account for the analysis agent that analyzes security incidents",
        "roles": [
            "roles/aiplatform.user",  # For Gemini API access
            "roles/bigquery.dataViewer",
            "roles/firestore.dataOwner",
            "roles/pubsub.publisher",
            "roles/pubsub.subscriber",
            "roles/logging.logWriter",
            "roles/monitoring.metricWriter",
            "roles/secretmanager.secretAccessor",
        ],
    },
    "sentinelops-remediation": {
        "display_name": "SentinelOps Remediation Agent",
        "description": "Service account for the remediation agent that executes response actions",
        "roles": [
            "roles/compute.admin",  # For VM operations
            "roles/iam.serviceAccountAdmin",  # For credential revocation
            "roles/compute.securityAdmin",  # For firewall rules
            "roles/firestore.dataWriter",
            "roles/pubsub.publisher",
            "roles/pubsub.subscriber",
            "roles/logging.logWriter",
            "roles/monitoring.metricWriter",
            "roles/secretmanager.secretAccessor",
            "roles/cloudfunctions.invoker",  # To invoke remediation functions
        ],
    },
    "sentinelops-communication": {
        "display_name": "SentinelOps Communication Agent",
        "description": "Service account for the communication agent that sends notifications",
        "roles": [
            "roles/firestore.dataReader",
            "roles/pubsub.subscriber",
            "roles/logging.logWriter",
            "roles/monitoring.metricWriter",
            "roles/secretmanager.secretAccessor",
        ],
    },
    "sentinelops-cloud-functions": {
        "display_name": "SentinelOps Cloud Functions",
        "description": "Service account for Cloud Functions executing remediation actions",
        "roles": [
            "roles/compute.admin",
            "roles/iam.serviceAccountAdmin",
            "roles/firestore.dataWriter",
            "roles/logging.logWriter",
            "roles/monitoring.metricWriter",
        ],
    },
    "sentinelops-cloud-run": {
        "display_name": "SentinelOps Cloud Run",
        "description": "Default service account for Cloud Run services",
        "roles": [
            "roles/firestore.dataOwner",
            "roles/bigquery.dataViewer",
            "roles/pubsub.editor",
            "roles/logging.logWriter",
            "roles/monitoring.metricWriter",
            "roles/secretmanager.secretAccessor",
            "roles/cloudtrace.agent",
        ],
    },
}

# Additional project-level IAM bindings
PROJECT_LEVEL_BINDINGS = {
    "roles/serviceusage.serviceUsageAdmin": ["sentinelops-sa"],  # For enabling APIs
    "roles/resourcemanager.projectIamAdmin": ["sentinelops-sa"],  # For managing IAM
}


class IAMSetup:
    """Handles IAM setup for SentinelOps"""

    def __init__(self):
        self.project_id = PROJECT_ID
        self.created_accounts = []
        self.failed_accounts = []
        self.assigned_roles = []
        self.failed_roles = []

    def run_gcloud_command(self, command: List[str]) -> Tuple[bool, str, str]:
        """Run a gcloud command and return success status, stdout, and stderr"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr
        except Exception as e:
            return False, "", str(e)

    def create_service_account(self, account_id: str, config: Dict) -> bool:
        """Create a single service account"""
        print("\n🔨 Creating service account: {account_id}")

        # Check if account already exists
        email = f"{account_id}@{self.project_id}.iam.gserviceaccount.com"
        success, stdout, stderr = self.run_gcloud_command(
            [
                "gcloud",
                "iam",
                "service-accounts",
                "describe",
                email,
                f"--project={self.project_id}",
                "--format=json",
            ]
        )

        if success:
            print("✓  Service account already exists: {email}")
            self.created_accounts.append(account_id)
            return True

        # Create the service account
        success, stdout, stderr = self.run_gcloud_command(
            [
                "gcloud",
                "iam",
                "service-accounts",
                "create",
                account_id,
                f"--display-name={config['display_name']}",
                f"--description={config['description']}",
                f"--project={self.project_id}",
            ]
        )

        if success:
            print("✅ Created service account: {email}")
            self.created_accounts.append(account_id)
            return True
        else:
            print("❌ Failed to create service account: {stderr}")
            self.failed_accounts.append((account_id, stderr))
            return False

    def assign_role(self, account_id: str, role: str) -> bool:
        """Assign a role to a service account"""
        email = f"{account_id}@{self.project_id}.iam.gserviceaccount.com"

        success, stdout, stderr = self.run_gcloud_command(
            [
                "gcloud",
                "projects",
                "add-iam-policy-binding",
                self.project_id,
                f"--member=serviceAccount:{email}",
                f"--role={role}",
                "--condition=None",
            ]
        )

        if success:
            print("   ✅ Assigned role: {role}")
            self.assigned_roles.append((account_id, role))
            return True
        else:
            print("   ❌ Failed to assign role {role}: {stderr}")
            self.failed_roles.append((account_id, role, stderr))
            return False

    def setup_service_accounts(self) -> None:
        """Set up all service accounts and their roles"""
        print("🚀 Setting up service accounts...")

        for account_id, config in SERVICE_ACCOUNTS.items():
            if self.create_service_account(account_id, config):
                print("   Assigning roles to {account_id}...")
                for role in config["roles"]:
                    self.assign_role(account_id, role)

    def setup_project_level_bindings(self) -> None:
        """Set up project-level IAM bindings"""
        print("\n🔐 Setting up project-level IAM bindings...")

        for role, accounts in PROJECT_LEVEL_BINDINGS.items():
            for account in accounts:
                email = f"{account}@{self.project_id}.iam.gserviceaccount.com"
                print("   Assigning {role} to {email}...")

                success, stdout, stderr = self.run_gcloud_command(
                    [
                        "gcloud",
                        "projects",
                        "add-iam-policy-binding",
                        self.project_id,
                        f"--member=serviceAccount:{email}",
                        f"--role={role}",
                        "--condition=None",
                    ]
                )

                if success:
                    print("   ✅ Assigned role: {role}")
                else:
                    print("   ❌ Failed: {stderr}")

    def create_service_account_keys(self) -> None:
        """Create and download service account keys for local development"""
        print("\n🔑 Creating service account keys for local development...")

        keys_dir = Path(__file__).parent.parent / "keys"
        keys_dir.mkdir(exist_ok=True)

        # Add .gitignore to keys directory
        gitignore_path = keys_dir / ".gitignore"
        with open(gitignore_path, "w") as f:
            f.write("# Ignore all key files\n*.json\n")

        for account_id in self.created_accounts:
            if account_id == "sentinelops-sa":  # Skip the main service account
                continue

            email = f"{account_id}@{self.project_id}.iam.gserviceaccount.com"
            key_path = keys_dir / f"{account_id}-key.json"

            if key_path.exists():
                print("   ✓ Key already exists for {account_id}")
                continue

            success, stdout, stderr = self.run_gcloud_command(
                [
                    "gcloud",
                    "iam",
                    "service-accounts",
                    "keys",
                    "create",
                    str(key_path),
                    f"--iam-account={email}",
                    f"--project={self.project_id}",
                ]
            )

            if success:
                print("   ✅ Created key for {account_id}")
            else:
                print("   ❌ Failed to create key for {account_id}: {stderr}")

    def setup_access_controls(self) -> None:
        """Set up additional access controls and best practices"""
        print("\n🛡️  Setting up access controls...")

        # Create custom roles for fine-grained permissions
        custom_roles = {
            "sentinelopsIncidentReader": {
                "title": "SentinelOps Incident Reader",
                "description": "Read-only access to security incidents",
                "permissions": [
                    "firestore.documents.get",
                    "firestore.documents.list",
                    "bigquery.tables.get",
                    "bigquery.tables.getData",
                ],
            },
            "sentinelopsRemediationApprover": {
                "title": "SentinelOps Remediation Approver",
                "description": "Approve remediation actions",
                "permissions": [
                    "firestore.documents.update",
                    "pubsub.topics.publish",
                ],
            },
        }

        for role_id, config in custom_roles.items():
            full_role_id = f"projects/{self.project_id}/roles/{role_id}"

            # Check if role exists
            success, stdout, stderr = self.run_gcloud_command(
                [
                    "gcloud",
                    "iam",
                    "roles",
                    "describe",
                    role_id,
                    f"--project={self.project_id}",
                    "--format=json",
                ]
            )

            if success:
                print("   ✓ Custom role already exists: {role_id}")
            else:
                # Create the custom role
                permissions_str = ",".join(config["permissions"])
                success, stdout, stderr = self.run_gcloud_command(
                    [
                        "gcloud",
                        "iam",
                        "roles",
                        "create",
                        role_id,
                        f"--project={self.project_id}",
                        f"--title={config['title']}",
                        f"--description={config['description']}",
                        f"--permissions={permissions_str}",
                    ]
                )

                if success:
                    print("   ✅ Created custom role: {role_id}")
                else:
                    print("   ❌ Failed to create role: {stderr}")

    def print_summary(self) -> None:
        """Print a summary of the IAM setup"""
        print("\n" + "=" * 60)
        print("📊 IAM SETUP SUMMARY")
        print("=" * 60)

        if self.created_accounts:
            print("\n✅ Service Accounts ({len(self.created_accounts)}):")
            for account in self.created_accounts:
                email = f"{account}@{self.project_id}.iam.gserviceaccount.com"
                print("   • {email}")

        if self.failed_accounts:
            print("\n❌ Failed Service Accounts ({len(self.failed_accounts)}):")
            for account, error in self.failed_accounts:
                print("   • {account}: {error}")

        # Count successful role assignments
        role_count = len(self.assigned_roles)
        if role_count > 0:
            print("\n✅ Role Assignments: {role_count}")

        if self.failed_roles:
            print("\n❌ Failed Role Assignments ({len(self.failed_roles)}):")
            for account, role, error in self.failed_roles:
                print("   • {account} - {role}")

        print("\n" + "=" * 60)

    def update_checklist(self) -> None:
        """Update the checklist to mark completed items"""
        checklist_path = (
            Path(__file__).parent.parent
            / "docs"
            / "checklists"
            / "08-google-cloud-integration.md"
        )

        if not checklist_path.exists():
            return

        # Read current checklist
        with open(checklist_path, "r") as f:
            content = f.read()

        # Update based on what was completed
        if len(self.created_accounts) >= len(SERVICE_ACCOUNTS):
            content = content.replace(
                "  - [ ] Create service accounts", "  - [x] Create service accounts"
            )

        if len(self.assigned_roles) > 0:
            content = content.replace(
                "  - [ ] Assign least privilege permissions",
                "  - [x] Assign least privilege permissions",
            )
            content = content.replace(
                "  - [ ] Configure role bindings", "  - [x] Configure role bindings"
            )

        if "access controls" in str(self.created_accounts):
            content = content.replace(
                "  - [ ] Set up access controls", "  - [x] Set up access controls"
            )

        # Mark parent as complete if all sub-items are done
        if all(
            x in content
            for x in [
                "[x] Create service accounts",
                "[x] Assign least privilege permissions",
                "[x] Configure role bindings",
                "[x] Set up access controls",
            ]
        ):
            content = content.replace(
                "- [ ] Set up IAM permissions", "- [x] Set up IAM permissions"
            )

        # Write updated checklist
        with open(checklist_path, "w") as f:
            f.write(content)

        print("\n✅ Updated checklist")

    def run(self) -> None:
        """Run the complete IAM setup"""
        self.setup_service_accounts()
        self.setup_project_level_bindings()
        self.create_service_account_keys()
        self.setup_access_controls()
        self.print_summary()
        self.update_checklist()


def main():
    """Main entry point"""
    setup = IAMSetup()
    setup.run()


if __name__ == "__main__":
    main()
