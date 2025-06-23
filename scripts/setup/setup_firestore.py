#!/usr/bin/env python3
"""
Set up Firestore collections, indexes, and security rules for SentinelOps
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from google.api_core.exceptions import AlreadyExists
from google.cloud import firestore

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")

# Collection schemas
COLLECTIONS = {
    "incidents": {
        "description": "Security incidents detected by SentinelOps",
        "sample_doc": {
            "id": "INC-001",
            "timestamp": firestore.SERVER_TIMESTAMP,
            "severity": "HIGH",
            "status": "OPEN",
            "type": "unauthorized_access",
            "title": "Unauthorized access attempt detected",
            "description": "Multiple failed login attempts from suspicious IP",
            "source": {"ip": "192.168.1.100", "port": 22, "service": "ssh"},
            "affected_resources": ["vm-instance-1", "vm-instance-2"],
            "detection_source": "audit_logs",
            "analysis": {
                "risk_score": 8.5,
                "attack_pattern": "brute_force",
                "recommendations": ["block_ip", "enforce_mfa"],
            },
            "remediation": {
                "status": "pending",
                "actions": [],
                "approved_by": None,
                "executed_at": None,
            },
            "metadata": {
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
                "created_by": "detection-agent",
                "tags": ["security", "access-control"],
            },
        },
    },
    "audit_logs": {
        "description": "Audit trail of all SentinelOps actions",
        "sample_doc": {
            "timestamp": firestore.SERVER_TIMESTAMP,
            "action": "remediation_executed",
            "actor": "remediation-agent",
            "resource": "INC-001",
            "details": {
                "action_type": "block_ip",
                "target_ip": "192.168.1.100",
                "success": True,
                "duration_ms": 245,
            },
            "metadata": {
                "service_account": "sentinelops-remediation@project.iam",
                "request_id": "req-12345",
                "ip_address": "10.0.0.1",
            },
        },
    },
    "remediation_templates": {
        "description": "Pre-defined remediation action templates",
        "sample_doc": {
            "id": "block_ip_template",
            "name": "Block IP Address",
            "description": "Block traffic from specific IP address",
            "type": "firewall_rule",
            "parameters": {
                "ip_address": {"type": "string", "required": True},
                "direction": {"type": "string", "default": "INGRESS"},
                "priority": {"type": "integer", "default": 1000},
            },
            "risk_level": "low",
            "requires_approval": False,
            "implementation": "cloud_function",
            "function_name": "block-ip-address",
        },
    },
    "system_config": {
        "description": "System configuration and settings",
        "sample_doc": {
            "id": "detection_config",
            "category": "detection",
            "settings": {
                "scan_interval_seconds": 300,
                "severity_thresholds": {
                    "critical": 9.0,
                    "high": 7.0,
                    "medium": 5.0,
                    "low": 3.0,
                },
                "enabled_detectors": [
                    "unauthorized_access",
                    "anomalous_traffic",
                    "privilege_escalation",
                    "data_exfiltration",
                ],
            },
            "updated_at": firestore.SERVER_TIMESTAMP,
            "updated_by": "admin",
        },
    },
    "agent_status": {
        "description": "Health and status of SentinelOps agents",
        "sample_doc": {
            "agent_id": "detection-agent-1",
            "agent_type": "detection",
            "status": "healthy",
            "last_heartbeat": firestore.SERVER_TIMESTAMP,
            "metrics": {
                "cpu_usage": 45.2,
                "memory_usage": 62.8,
                "processed_events": 1523,
                "errors_count": 0,
            },
            "version": "1.0.0",
            "uptime_seconds": 86400,
        },
    },
}

# Firestore indexes configuration
INDEXES = [
    {
        "collection": "incidents",
        "fields": [
            {"field": "status", "order": "ASCENDING"},
            {"field": "severity", "order": "DESCENDING"},
            {"field": "timestamp", "order": "DESCENDING"},
        ],
    },
    {
        "collection": "incidents",
        "fields": [
            {"field": "type", "order": "ASCENDING"},
            {"field": "timestamp", "order": "DESCENDING"},
        ],
    },
    {
        "collection": "audit_logs",
        "fields": [
            {"field": "action", "order": "ASCENDING"},
            {"field": "timestamp", "order": "DESCENDING"},
        ],
    },
    {
        "collection": "audit_logs",
        "fields": [
            {"field": "actor", "order": "ASCENDING"},
            {"field": "timestamp", "order": "DESCENDING"},
        ],
    },
    {
        "collection": "agent_status",
        "fields": [
            {"field": "agent_type", "order": "ASCENDING"},
            {"field": "status", "order": "ASCENDING"},
        ],
    },
]

# Security rules
SECURITY_RULES = """
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Helper functions
    function isAuthenticated() {
      return request.auth != null;
    }

    function isServiceAccount() {
      return request.auth.token.email.matches('.*@.*\\.iam\\.gserviceaccount\\.com$');
    }

    function hasRole(role) {
      return isAuthenticated() && request.auth.token.role == role;
    }

    // Incidents collection
    match /incidents/{incident} {
      // Read access for all authenticated service accounts
      allow read: if isServiceAccount();

      // Write access only for detection and orchestration agents
      allow create: if isServiceAccount() &&
        request.auth.token.email in [
          'sentinelops-detection@your-gcp-project-id.iam.gserviceaccount.com',
          'sentinelops-orchestrator@your-gcp-project-id.iam.gserviceaccount.com'
        ];

      // Update access for analysis, remediation, and orchestration agents
      allow update: if isServiceAccount() &&
        request.auth.token.email in [
          'sentinelops-analysis@your-gcp-project-id.iam.gserviceaccount.com',
          'sentinelops-remediation@your-gcp-project-id.iam.gserviceaccount.com',
          'sentinelops-orchestrator@your-gcp-project-id.iam.gserviceaccount.com'
        ];

      // No delete allowed
      allow delete: if false;
    }

    // Audit logs collection
    match /audit_logs/{log} {
      // Read access for all authenticated service accounts
      allow read: if isServiceAccount();

      // Write access for all agents (audit trail)
      allow create: if isServiceAccount();

      // No updates or deletes allowed (immutable audit log)
      allow update, delete: if false;
    }

    // Remediation templates collection
    match /remediation_templates/{template} {
      // Read access for all authenticated service accounts
      allow read: if isServiceAccount();

      // Write access only for admin operations
      allow write: if isServiceAccount() &&
        request.auth.token.email == 'sentinelops-sa@your-gcp-project-id.iam.gserviceaccount.com';
    }

    // System config collection
    match /system_config/{config} {
      // Read access for all authenticated service accounts
      allow read: if isServiceAccount();

      // Write access only for admin operations
      allow write: if isServiceAccount() &&
        request.auth.token.email == 'sentinelops-sa@your-gcp-project-id.iam.gserviceaccount.com';
    }

    // Agent status collection
    match /agent_status/{status} {
      // Read access for all authenticated service accounts
      allow read: if isServiceAccount();

      // Write access only for the agent itself
      allow write: if isServiceAccount() &&
        resource.data.agent_id == request.auth.token.email;
    }
  }
}
"""


class FirestoreSetup:
    def __init__(self):
        self.project_id = PROJECT_ID
        self.db = firestore.Client(project=self.project_id)
        self.created_collections = []
        self.created_indexes = []
        self.failed_operations = []

    def create_collections(self):
        """Create Firestore collections with sample documents"""
        print("📚 Creating Firestore collections...")

        for collection_name, config in COLLECTIONS.items():
            try:
                print("\n📝 Setting up collection: {collection_name}")
                print("   Description: {config['description']}")

                # Create collection by adding a sample document
                collection_ref = self.db.collection(collection_name)

                # Check if collection already has documents
                existing_docs = list(collection_ref.limit(1).stream())

                if not existing_docs:
                    # Add sample document
                    doc_id = f"sample_{collection_name}_doc"
                    collection_ref.document(doc_id).set(config["sample_doc"])
                    print("   ✅ Created collection with sample document")
                else:
                    print(
                        f"   ✓ Collection already exists with {len(list(collection_ref.stream()))} documents"
                    )

                self.created_collections.append(collection_name)

            except Exception as e:
                print("   ❌ Failed to create collection: {e}")
                self.failed_operations.append(f"Collection {collection_name}: {str(e)}")

    def create_indexes(self):
        """Create Firestore indexes using gcloud commands"""
        print("\n🔍 Creating Firestore indexes...")

        # Create indexes configuration file
        indexes_config = {"indexes": []}

        for index in INDEXES:
            index_config = {"collectionGroup": index["collection"], "fields": []}

            for field in index["fields"]:
                index_config["fields"].append(
                    {"fieldPath": field["field"], "order": field["order"]}
                )

            indexes_config["indexes"].append(index_config)

        # Write indexes configuration
        indexes_file = Path(__file__).parent / "firestore.indexes.json"
        with open(indexes_file, "w") as f:
            json.dump(indexes_config, f, indent=2)

        print("   📄 Created indexes configuration at: {indexes_file}")

        # Deploy indexes using gcloud
        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "firestore",
                    "indexes",
                    "create",
                    "--project",
                    self.project_id,
                    "--format=json",
                    str(indexes_file),
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("   ✅ Indexes deployment initiated")
                self.created_indexes.extend(
                    [f"{idx['collection']} composite index" for idx in INDEXES]
                )
            else:
                print("   ❌ Failed to deploy indexes: {result.stderr}")
                self.failed_operations.append(f"Indexes deployment: {result.stderr}")

        except Exception as e:
            print("   ❌ Failed to deploy indexes: {e}")
            self.failed_operations.append(f"Indexes deployment: {str(e)}")

    def create_security_rules(self):
        """Create Firestore security rules"""
        print("\n🔒 Setting up Firestore security rules...")

        # Write security rules to file
        rules_file = Path(__file__).parent / "firestore.rules"
        with open(rules_file, "w") as f:
            f.write(SECURITY_RULES)

        print("   📄 Created security rules at: {rules_file}")

        # Deploy security rules using gcloud
        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "firestore",
                    "databases",
                    "update",
                    "--project",
                    self.project_id,
                    "--rules",
                    str(rules_file),
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("   ✅ Security rules deployed successfully")
            else:
                print("   ❌ Failed to deploy security rules: {result.stderr}")
                self.failed_operations.append(f"Security rules: {result.stderr}")

        except Exception as e:
            print("   ❌ Failed to deploy security rules: {e}")
            self.failed_operations.append(f"Security rules: {str(e)}")

    def print_summary(self):
        """Print setup summary"""
        print("\n" + "=" * 60)
        print("📊 FIRESTORE SETUP SUMMARY")
        print("=" * 60)

        if self.created_collections:
            print("\n✅ Collections Created ({len(self.created_collections)}):")
            for collection in self.created_collections:
                print("   • {collection}")

        if self.created_indexes:
            print("\n✅ Indexes Created ({len(self.created_indexes)}):")
            for index in self.created_indexes:
                print("   • {index}")

        if self.failed_operations:
            print("\n❌ Failed Operations ({len(self.failed_operations)}):")
            for failure in self.failed_operations:
                print("   • {failure}")

        print("\n" + "=" * 60)

        # Print next steps
        print("\n📋 Next Steps:")
        print(
            "1. Monitor index creation at: https://console.cloud.google.com/firestore/indexes"
        )
        print(
            "2. Verify security rules at: https://console.cloud.google.com/firestore/security"
        )
        print("3. Test collection access with service accounts")

    def update_checklist(self):
        """Update the checklist"""
        checklist_path = (
            Path(__file__).parent.parent
            / "docs"
            / "checklists"
            / "08-google-cloud-integration.md"
        )

        try:
            with open(checklist_path, "r") as f:
                content = f.read()

            # Update Firestore section items
            if len(self.created_collections) >= len(COLLECTIONS):
                content = content.replace(
                    "  - [ ] Incidents collection", "  - [x] Incidents collection"
                )
                content = content.replace(
                    "  - [ ] Audit logs collection", "  - [x] Audit logs collection"
                )

            if self.created_indexes:
                content = content.replace(
                    "  - [ ] Create appropriate indexes",
                    "  - [x] Create appropriate indexes",
                )

            if "Security rules deployed" in str(self.created_indexes):
                content = content.replace(
                    "  - [ ] Configure validation rules",
                    "  - [x] Configure validation rules",
                )
                content = content.replace(
                    "  - [ ] Test security configuration",
                    "  - [x] Test security configuration",
                )

            # Update parent items if all sub-items are complete
            firestore_items = [
                "[x] Choose appropriate location",
                "[x] Configure database settings",
                "[x] Set up backup policies",
                "[x] Incidents collection",
                "[x] Audit logs collection",
                "[x] Create appropriate indexes",
            ]

            if all(item in content for item in firestore_items):
                content = content.replace(
                    "- [ ] Create Firestore database", "- [x] Create Firestore database"
                )
                content = content.replace(
                    "- [ ] Define collections and indexes",
                    "- [x] Define collections and indexes",
                )

            if (
                "[x] Set up access controls" in content
                and "[x] Configure validation rules" in content
            ):
                content = content.replace(
                    "- [ ] Configure security rules", "- [x] Configure security rules"
                )

            with open(checklist_path, "w") as f:
                f.write(content)

            print("\n✅ Updated checklist")

        except Exception as e:
            print("\n⚠️  Failed to update checklist: {e}")

    def run(self):
        """Run the complete Firestore setup"""
        self.create_collections()
        self.create_indexes()
        self.create_security_rules()
        self.print_summary()
        self.update_checklist()


def main():
    """Main entry point"""
    setup = FirestoreSetup()
    setup.run()


if __name__ == "__main__":
    main()
