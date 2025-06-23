#!/usr/bin/env python3
"""
Enable Google Cloud APIs for SentinelOps
Implements checklist item: Enable required APIs
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402

# Load environment variables
load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")

# List of required APIs as specified in the checklist
REQUIRED_APIS = [
    ("BigQuery API", "bigquery.googleapis.com"),
    ("Pub/Sub API", "pubsub.googleapis.com"),
    ("Firestore API", "firestore.googleapis.com"),
    ("Cloud Functions API", "cloudfunctions.googleapis.com"),
    ("Cloud Run API", "run.googleapis.com"),
    ("Secret Manager API", "secretmanager.googleapis.com"),
    ("Cloud Logging API", "logging.googleapis.com"),
    ("Cloud Monitoring API", "monitoring.googleapis.com"),
    ("Vertex AI API", "aiplatform.googleapis.com"),  # For Gemini
    ("Cloud Billing API", "cloudbilling.googleapis.com"),  # For billing checks
    (
        "Cloud Resource Manager API",
        "cloudresourcemanager.googleapis.com",
    ),  # For project management
    ("IAM API", "iam.googleapis.com"),  # For IAM operations
    ("Compute Engine API", "compute.googleapis.com"),  # For VM operations
    ("Cloud Build API", "cloudbuild.googleapis.com"),  # For CI/CD
    (
        "Artifact Registry API",
        "artifactregistry.googleapis.com",
    ),  # For container storage
    (
        "Cloud Run Admin API",
        "run.googleapis.com",
    ),  # Already included but ensure it's admin
]


class APIEnabler:
    """Handles enabling Google Cloud APIs"""

    def __init__(self):
        self.project_id = PROJECT_ID
        self.enabled_apis = []
        self.failed_apis = []
        self.already_enabled = []

    def run_gcloud_command(self, command: List[str]) -> Tuple[bool, str, str]:
        """Run a gcloud command and return success status, stdout, and stderr"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr
        except Exception as e:
            return False, "", str(e)

    def check_api_enabled(self, api_name: str, api_id: str) -> bool:
        """Check if an API is already enabled"""
        print("🔍 Checking if {api_name} is enabled...")

        success, stdout, stderr = self.run_gcloud_command(
            [
                "gcloud",
                "services",
                "list",
                f"--project={self.project_id}",
                "--enabled",
                f"--filter=config.name:{api_id}",
                "--format=value(config.name)",
            ]
        )

        if success and api_id in stdout:
            print("✓  {api_name} is already enabled")
            self.already_enabled.append(api_name)
            return True
        return False

    def enable_api(self, api_name: str, api_id: str) -> bool:
        """Enable a single API"""
        # Check if already enabled
        if self.check_api_enabled(api_name, api_id):
            return True

        print("🚀 Enabling {api_name}...")

        success, stdout, stderr = self.run_gcloud_command(
            ["gcloud", "services", "enable", api_id, f"--project={self.project_id}"]
        )

        if success:
            print("✅ Successfully enabled {api_name}")
            self.enabled_apis.append(api_name)
            # Wait a bit for the API to propagate
            time.sleep(2)
            return True
        else:
            print("❌ Failed to enable {api_name}: {stderr}")
            self.failed_apis.append((api_name, stderr))
            return False

    def enable_all_apis(self) -> None:
        """Enable all required APIs"""
        print("🎯 Enabling required APIs for project: {self.project_id}")
        print("   Total APIs to process: {len(REQUIRED_APIS)}")
        print("=" * 60)

        for api_name, api_id in REQUIRED_APIS:
            self.enable_api(api_name, api_id)
            print("-" * 60)

        self.print_summary()
        self.update_checklist()

    def print_summary(self) -> None:
        """Print a summary of the API enablement process"""
        print("\n" + "=" * 60)
        print("📊 API ENABLEMENT SUMMARY")
        print("=" * 60)

        if self.already_enabled:
            print("\n✓  Already Enabled ({len(self.already_enabled)}):")
            for api in self.already_enabled:
                print("   • {api}")

        if self.enabled_apis:
            print("\n✅ Newly Enabled ({len(self.enabled_apis)}):")
            for api in self.enabled_apis:
                print("   • {api}")

        if self.failed_apis:
            print("\n❌ Failed ({len(self.failed_apis)}):")
            for api, error in self.failed_apis:
                print("   • {api}")
                print("     Error: {error.strip()}")

        total_success = len(self.already_enabled) + len(self.enabled_apis)
        print("\n📈 Total Success: {total_success}/{len(REQUIRED_APIS)}")

        if not self.failed_apis:
            print("\n🎉 All required APIs are now enabled!")
        else:
            print("\n⚠️  Some APIs failed to enable. Please check the errors above.")

        print("=" * 60)

    def update_checklist(self) -> None:
        """Update the checklist to mark completed API enablements"""
        checklist_path = (
            Path(__file__).parent.parent
            / "docs"
            / "checklists"
            / "08-google-cloud-integration.md"
        )

        if not checklist_path.exists():
            print("\n⚠️  Could not find checklist at {checklist_path}")
            return

        # Read current checklist
        with open(checklist_path, "r") as f:
            content = f.read()

        # Map API names to checklist items
        api_mapping = {
            "BigQuery API": "  - [ ] BigQuery API",
            "Pub/Sub API": "  - [ ] Pub/Sub API",
            "Firestore API": "  - [ ] Firestore API",
            "Cloud Functions API": "  - [ ] Cloud Functions API",
            "Cloud Run API": "  - [ ] Cloud Run API",
            "Secret Manager API": "  - [ ] Secret Manager API",
            "Cloud Logging API": "  - [ ] Cloud Logging API",
            "Cloud Monitoring API": "  - [ ] Monitoring API",
            "Vertex AI API": "  - [ ] Gemini API",
        }

        # Mark completed items
        updates_made = False
        for api_name in self.already_enabled + self.enabled_apis:
            if api_name in api_mapping:
                old_line = api_mapping[api_name]
                new_line = old_line.replace("[ ]", "[x]")
                if old_line in content:
                    content = content.replace(old_line, new_line)
                    updates_made = True

        # If all main APIs are enabled, mark the parent item as complete
        all_apis_enabled = all(
            api_name in (self.already_enabled + self.enabled_apis)
            for api_name in api_mapping.keys()
        )

        if all_apis_enabled:
            content = content.replace(
                "- [ ] Enable required APIs", "- [x] Enable required APIs"
            )

        # Write updated checklist
        if updates_made:
            with open(checklist_path, "w") as f:
                f.write(content)
            print("\n✅ Updated checklist at {checklist_path}")

    def create_api_test_script(self) -> None:
        """Create a script to test API connectivity"""
        test_script = '''#!/usr/bin/env python3
"""Test Google Cloud API connectivity"""

import os  # noqa: E402
import sys  # noqa: E402
from google.cloud import bigquery  # noqa: E402
from google.cloud import pubsub_v1  # noqa: E402
from google.cloud import firestore  # noqa: E402
from google.cloud import secretmanager  # noqa: E402
from google.cloud import logging  # noqa: E402
from google.cloud import monitoring_v3  # noqa: E402

def test_apis():
    """Test basic connectivity to each API"""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    print("Testing APIs for project: {project_id}")

    # Test BigQuery
    try:
        client = bigquery.Client(project=project_id)
        datasets = list(client.list_datasets())
        print("✅ BigQuery API: Connected")
    except Exception as e:
        print("❌ BigQuery API: {e}")

    # Test Pub/Sub
    try:
        publisher = pubsub_v1.PublisherClient()
        project_path = f"projects/{project_id}"
        topics = list(publisher.list_topics(request={"project": project_path}))
        print("✅ Pub/Sub API: Connected")
    except Exception as e:
        print("❌ Pub/Sub API: {e}")

    # Test Firestore
    try:
        db = firestore.Client(project=project_id)
        collections = list(db.collections())
        print("✅ Firestore API: Connected")
    except Exception as e:
        print("❌ Firestore API: {e}")

    # Test Secret Manager
    try:
        client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{project_id}"
        secrets = list(client.list_secrets(request={"parent": parent}))
        print("✅ Secret Manager API: Connected")
    except Exception as e:
        print("❌ Secret Manager API: {e}")

    # Test Cloud Logging
    try:
        client = logging.Client(project=project_id)
        logger = client.logger("test")
        print("✅ Cloud Logging API: Connected")
    except Exception as e:
        print("❌ Cloud Logging API: {e}")

    # Test Cloud Monitoring
    try:
        client = monitoring_v3.MetricServiceClient()
        project_name = f"projects/{project_id}"
        print("✅ Cloud Monitoring API: Connected")
    except Exception as e:
        print("❌ Cloud Monitoring API: {e}")

if __name__ == "__main__":
    test_apis()
'''

        test_script_path = Path(__file__).parent / "test_gcp_apis.py"
        with open(test_script_path, "w") as f:
            f.write(test_script)
        os.chmod(test_script_path, 0o755)
        print("\n📝 Created API test script at: {test_script_path}")


def main():
    """Main entry point"""
    enabler = APIEnabler()
    enabler.enable_all_apis()
    enabler.create_api_test_script()


if __name__ == "__main__":
    main()
