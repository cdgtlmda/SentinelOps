#!/usr/bin/env python3
"""
Verify that all required Google Cloud APIs are enabled for SentinelOps.
Provides detailed status and instructions for any missing APIs.
"""

import subprocess
import json
import sys
from typing import List, Dict, Tuple

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Required APIs for SentinelOps
REQUIRED_APIS = {
    # Core APIs (usually enabled by default)
    "cloudapis.googleapis.com": {
        "name": "Google Cloud APIs",
        "required_for": "Basic API functionality",
        "billing_required": False
    },
    "servicemanagement.googleapis.com": {
        "name": "Service Management API",
        "required_for": "Managing services",
        "billing_required": False
    },
    "serviceusage.googleapis.com": {
        "name": "Service Usage API",
        "required_for": "Enabling other APIs",
        "billing_required": False
    },

    # Storage and Data APIs
    "storage.googleapis.com": {
        "name": "Cloud Storage API",
        "required_for": "Storing logs and artifacts",
        "billing_required": False
    },
    "bigquery.googleapis.com": {
        "name": "BigQuery API",
        "required_for": "Incident data storage and analytics",
        "billing_required": False
    },

    # AI/ML APIs
    "aiplatform.googleapis.com": {
        "name": "Vertex AI API",
        "required_for": "Gemini AI integration",
        "billing_required": False
    },

    # Compute and Infrastructure APIs
    "compute.googleapis.com": {
        "name": "Compute Engine API",
        "required_for": "VM management and remediation",
        "billing_required": True
    },
    "run.googleapis.com": {
        "name": "Cloud Run API",
        "required_for": "Deploying the SentinelOps service",
        "billing_required": True
    },
    "cloudfunctions.googleapis.com": {
        "name": "Cloud Functions API",
        "required_for": "Event-driven agent execution",
        "billing_required": False
    },

    # Security and Identity APIs
    "iam.googleapis.com": {
        "name": "Identity and Access Management API",
        "required_for": "Managing service accounts and permissions",
        "billing_required": False
    },
    "secretmanager.googleapis.com": {
        "name": "Secret Manager API",
        "required_for": "Storing API keys and credentials",
        "billing_required": True
    },
    "cloudresourcemanager.googleapis.com": {
        "name": "Cloud Resource Manager API",
        "required_for": "Managing project resources",
        "billing_required": False
    },

    # Monitoring and Logging APIs
    "logging.googleapis.com": {
        "name": "Cloud Logging API",
        "required_for": "Reading and writing logs",
        "billing_required": False
    },
    "monitoring.googleapis.com": {
        "name": "Cloud Monitoring API",
        "required_for": "Metrics and alerting",
        "billing_required": False
    },

    # Messaging APIs
    "pubsub.googleapis.com": {
        "name": "Cloud Pub/Sub API",
        "required_for": "Agent communication and event streaming",
        "billing_required": False
    },

    # Container APIs (for deployment)
    "containerregistry.googleapis.com": {
        "name": "Container Registry API",
        "required_for": "Storing Docker images",
        "billing_required": True
    },
    "artifactregistry.googleapis.com": {
        "name": "Artifact Registry API",
        "required_for": "Modern container image storage",
        "billing_required": True
    }
}

# Optional APIs
OPTIONAL_APIS = {
    "chronicle.googleapis.com": {
        "name": "Chronicle API",
        "required_for": "Advanced security analytics (if available)",
        "billing_required": True
    },
    "cloudkms.googleapis.com": {
        "name": "Cloud KMS API",
        "required_for": "Advanced encryption key management",
        "billing_required": True
    }
}


def get_project_id() -> str:
    """Get the current Google Cloud project ID."""
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("{RED}✗ Failed to get project ID. Is gcloud configured?{RESET}")
        sys.exit(1)


def check_billing_enabled(project_id: str) -> bool:
    """Check if billing is enabled for the project."""
    try:
        result = subprocess.run(
            ["gcloud", "beta", "billing", "projects", "describe", project_id, "--format=json"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            billing_info = json.loads(result.stdout)
            return billing_info.get("billingEnabled", False)
    except Exception:
        pass
    return False


def get_enabled_apis(project_id: str) -> set:
    """Get list of currently enabled APIs."""
    try:
        result = subprocess.run(
            ["gcloud", "services", "list", "--enabled", f"--project={project_id}", "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        apis = json.loads(result.stdout)
        return {api["config"]["name"] for api in apis}
    except subprocess.CalledProcessError as e:
        print("{RED}✗ Failed to list enabled APIs: {e}{RESET}")
        return set()


def check_api_status(enabled_apis: set, api_dict: Dict[str, dict], api_type: str) -> Tuple[List[str], List[str], List[str]]:
    """Check status of APIs and categorize them."""
    enabled = []
    disabled_no_billing = []
    disabled_billing_ok = []

    for api_id, api_info in api_dict.items():
        if api_id in enabled_apis:
            enabled.append(api_id)
        elif api_info["billing_required"]:
            disabled_no_billing.append(api_id)
        else:
            disabled_billing_ok.append(api_id)

    return enabled, disabled_no_billing, disabled_billing_ok


def print_api_status(api_id: str, api_info: dict, status: str):
    """Print formatted API status."""
    status_symbol = "✓" if status == "enabled" else "✗"
    status_color = GREEN if status == "enabled" else RED if status == "disabled_billing" else YELLOW

    print("{status_color}{status_symbol} {api_info['name']}{RESET}")
    print("    API: {api_id}")
    print("    Used for: {api_info['required_for']}")
    if status != "enabled" and api_info["billing_required"]:
        print("    {YELLOW}Note: Requires billing to be enabled{RESET}")
    print()


def generate_enable_command(apis: List[str]) -> str:
    """Generate gcloud command to enable APIs."""
    if not apis:
        return ""
    return f"gcloud services enable {' '.join(apis)} --project=PROJECT_ID"


def main():
    """Main function to verify API status."""
    print("{BLUE}{'=' *60}{RESET}")
    print("{BLUE}Google Cloud API Verification for SentinelOps{RESET}")
    print("{BLUE}{'=' *60}{RESET}\n")

    # Get project ID
    project_id = get_project_id()
    print("Project ID: {project_id}\n")

    # Check billing status
    billing_enabled = check_billing_enabled(project_id)
    if billing_enabled:
        print("{GREEN}✓ Billing is enabled{RESET}\n")
    else:
        print("{YELLOW}⚠ Billing is not enabled{RESET}")
        print("Some APIs require billing to be enabled.\n")

    # Get enabled APIs
    print("Checking API status...")
    enabled_apis = get_enabled_apis(project_id)

    # Check required APIs
    print("\n{BLUE}Required APIs:{RESET}\n")
    req_enabled, req_disabled_billing, req_disabled_ok = check_api_status(
        enabled_apis, REQUIRED_APIS, "Required"
    )

    # Print enabled APIs
    if req_enabled:
        print("{GREEN}Enabled ({len(req_enabled)}):{RESET}\n")
        for api_id in req_enabled:
            print_api_status(api_id, REQUIRED_APIS[api_id], "enabled")

    # Print disabled APIs that need billing
    if req_disabled_billing:
        print("{RED}Disabled - Billing Required ({len(req_disabled_billing)}):{RESET}\n")
        for api_id in req_disabled_billing:
            print_api_status(api_id, REQUIRED_APIS[api_id], "disabled_billing")

    # Print disabled APIs that don't need billing
    if req_disabled_ok:
        print("{YELLOW}Disabled - Can Enable Now ({len(req_disabled_ok)}):{RESET}\n")
        for api_id in req_disabled_ok:
            print_api_status(api_id, REQUIRED_APIS[api_id], "disabled_ok")

    # Check optional APIs
    print("\n{BLUE}Optional APIs:{RESET}\n")
    opt_enabled, opt_disabled_billing, opt_disabled_ok = check_api_status(
        enabled_apis, OPTIONAL_APIS, "Optional"
    )

    for api_id in OPTIONAL_APIS:
        if api_id in opt_enabled:
            print_api_status(api_id, OPTIONAL_APIS[api_id], "enabled")
        else:
            print("{YELLOW}○ {OPTIONAL_APIS[api_id]['name']} (optional){RESET}")
            print("    API: {api_id}")
            print("    Used for: {OPTIONAL_APIS[api_id]['required_for']}\n")

    # Summary and recommendations
    print("{BLUE}{'=' *60}{RESET}")
    print("{BLUE}Summary:{RESET}\n")

    total_required = len(REQUIRED_APIS)
    total_enabled = len(req_enabled)

    print("Required APIs: {total_enabled}/{total_required} enabled")
    print("Optional APIs: {len(opt_enabled)}/{len(OPTIONAL_APIS)} enabled\n")

    if req_disabled_ok:
        print("{YELLOW}Action Required - Enable APIs:{RESET}")
        print("Run the following command to enable APIs that don't require billing:\n")
        cmd = generate_enable_command(req_disabled_ok)
        print("    {cmd.replace('PROJECT_ID', project_id)}\n")

    if req_disabled_billing:
        print("{RED}Action Required - Enable Billing:{RESET}")
        print("The following APIs require billing to be enabled:")
        for api_id in req_disabled_billing:
            print("  - {REQUIRED_APIS[api_id]['name']}")
        print("\nSteps:")
        print("1. Enable billing in Google Cloud Console")
        print("2. Run the following command:\n")
        cmd = generate_enable_command(req_disabled_billing)
        print("    {cmd.replace('PROJECT_ID', project_id)}\n")

    if total_enabled == total_required:
        print("{GREEN}✅ All required APIs are enabled!{RESET}")
        return 0
    else:
        print("{YELLOW}⚠️  Some required APIs are not enabled.{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
