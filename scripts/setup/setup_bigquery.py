#!/usr/bin/env python3
"""
Set up BigQuery for SentinelOps
Implements checklist section 2: BigQuery Setup
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

from google.cloud import bigquery
from google.cloud.exceptions import Conflict, NotFound

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402

# Load environment variables
load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
DATASET_ID = os.getenv("BIGQUERY_DATASET", "sentinelops_dev")
DATASET_LOCATION = os.getenv("BIGQUERY_LOCATION", "US")

# Table schemas
TABLE_SCHEMAS = {
    "vpc_flow_logs": {
        "description": "VPC Flow Logs for network traffic analysis",
        "schema": [
            bigquery.SchemaField(
                "timestamp",
                "TIMESTAMP",
                mode="REQUIRED",
                description="Log entry timestamp",
            ),
            bigquery.SchemaField(
                "connection",
                "RECORD",
                mode="REQUIRED",
                fields=[
                    bigquery.SchemaField(
                        "src_ip",
                        "STRING",
                        mode="REQUIRED",
                        description="Source IP address",
                    ),
                    bigquery.SchemaField(
                        "src_port",
                        "INTEGER",
                        mode="REQUIRED",
                        description="Source port",
                    ),
                    bigquery.SchemaField(
                        "dest_ip",
                        "STRING",
                        mode="REQUIRED",
                        description="Destination IP address",
                    ),
                    bigquery.SchemaField(
                        "dest_port",
                        "INTEGER",
                        mode="REQUIRED",
                        description="Destination port",
                    ),
                    bigquery.SchemaField(
                        "protocol",
                        "INTEGER",
                        mode="REQUIRED",
                        description="IP protocol number",
                    ),
                ],
            ),
            bigquery.SchemaField(
                "vpc",
                "RECORD",
                mode="REQUIRED",
                fields=[
                    bigquery.SchemaField("project_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("vpc_name", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("subnetwork_name", "STRING", mode="REQUIRED"),
                ],
            ),
            bigquery.SchemaField("packets_sent", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("bytes_sent", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("rtt_msec", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField(
                "reporter", "STRING", mode="REQUIRED", description="SRC or DEST"
            ),
        ],
        "time_partitioning": bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp",
        ),
        "clustering_fields": ["connection.src_ip", "connection.dest_ip"],
    },
    "audit_logs": {
        "description": "Google Cloud audit logs for security monitoring",
        "schema": [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("severity", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("log_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField(
                "resource",
                "RECORD",
                mode="REQUIRED",
                fields=[
                    bigquery.SchemaField("type", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("labels", "JSON", mode="NULLABLE"),
                ],
            ),
            bigquery.SchemaField("principal_email", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("service_name", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("method_name", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("request", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("response", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("authentication_info", "JSON", mode="NULLABLE"),
            bigquery.SchemaField(
                "authorization_info",
                "JSON",
                mode="NULLABLE",
                description="Array of authorization attempts",
            ),
        ],
        "time_partitioning": bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp",
        ),
        "clustering_fields": ["principal_email", "service_name", "method_name"],
    },
    "firewall_logs": {
        "description": "Firewall rule logs for security analysis",
        "schema": [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField(
                "rule_details",
                "RECORD",
                mode="REQUIRED",
                fields=[
                    bigquery.SchemaField(
                        "reference",
                        "STRING",
                        mode="REQUIRED",
                        description="Firewall rule reference",
                    ),
                    bigquery.SchemaField(
                        "action", "STRING", mode="REQUIRED", description="ALLOW or DENY"
                    ),
                    bigquery.SchemaField(
                        "direction",
                        "STRING",
                        mode="REQUIRED",
                        description="INGRESS or EGRESS",
                    ),
                    bigquery.SchemaField("priority", "INTEGER", mode="REQUIRED"),
                ],
            ),
            bigquery.SchemaField(
                "connection",
                "RECORD",
                mode="REQUIRED",
                fields=[
                    bigquery.SchemaField("src_ip", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("src_port", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("dest_ip", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("dest_port", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("protocol", "STRING", mode="REQUIRED"),
                ],
            ),
            bigquery.SchemaField(
                "instance",
                "RECORD",
                mode="NULLABLE",
                fields=[
                    bigquery.SchemaField("project_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("vm_name", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("zone", "STRING", mode="REQUIRED"),
                ],
            ),
            bigquery.SchemaField(
                "disposition",
                "STRING",
                mode="REQUIRED",
                description="ALLOWED or DENIED",
            ),
        ],
        "time_partitioning": bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp",
        ),
        "clustering_fields": ["rule_details.action", "disposition"],
    },
    "iam_logs": {
        "description": "IAM permission changes and access logs",
        "schema": [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField(
                "operation",
                "RECORD",
                mode="REQUIRED",
                fields=[
                    bigquery.SchemaField(
                        "type",
                        "STRING",
                        mode="REQUIRED",
                        description="Type of IAM operation",
                    ),
                    bigquery.SchemaField("method", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("service", "STRING", mode="REQUIRED"),
                ],
            ),
            bigquery.SchemaField(
                "principal",
                "STRING",
                mode="REQUIRED",
                description="Who performed the action",
            ),
            bigquery.SchemaField(
                "resource",
                "STRING",
                mode="REQUIRED",
                description="Resource being accessed/modified",
            ),
            bigquery.SchemaField(
                "bindings",
                "RECORD",
                mode="REPEATED",
                fields=[
                    bigquery.SchemaField("role", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("members", "STRING", mode="REPEATED"),
                    bigquery.SchemaField("condition", "JSON", mode="NULLABLE"),
                ],
            ),
            bigquery.SchemaField(
                "policy_delta",
                "JSON",
                mode="NULLABLE",
                description="Changes made to IAM policy",
            ),
            bigquery.SchemaField("request_metadata", "JSON", mode="NULLABLE"),
        ],
        "time_partitioning": bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp",
        ),
        "clustering_fields": ["principal", "operation.type"],
    },
}

# Views to create
VIEWS = {
    "security_incidents_summary": {
        "description": "Aggregated view of security incidents across all log sources",
        "query": """
        SELECT
            'vpc_flow' as source,
            timestamp,
            CONCAT('Suspicious traffic from ', connection.src_ip, ' to ', connection.dest_ip) as description,
            'MEDIUM' as severity,
            connection.src_ip as principal,
            connection.dest_ip as target
        FROM `{PROJECT_ID}.{DATASET_ID}.vpc_flow_logs`
        WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
            AND (
                connection.dest_port IN (22, 3389, 445)  -- Common attack ports
                OR bytes_sent > 1000000000  -- Large data transfer
            )

        UNION ALL

        SELECT
            'audit_log' as source,
            timestamp,
            CONCAT('Unauthorized access attempt: ', method_name) as description,
            severity,
            principal_email as principal,
            resource.type as target
        FROM `{PROJECT_ID}.{DATASET_ID}.audit_logs`
        WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
            AND severity IN ('ERROR', 'CRITICAL')

        UNION ALL

        SELECT
            'firewall' as source,
            timestamp,
            CONCAT('Firewall ', disposition, ': ', connection.src_ip, ' -> ', connection.dest_ip) as description,
            CASE
                WHEN disposition = 'DENIED' AND rule_details.action = 'ALLOW' THEN 'HIGH'
                WHEN disposition = 'DENIED' THEN 'MEDIUM'
                ELSE 'LOW'
            END as severity,
            connection.src_ip as principal,
            connection.dest_ip as target
        FROM `{PROJECT_ID}.{DATASET_ID}.firewall_logs`
        WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
            AND disposition = 'DENIED'

        ORDER BY timestamp DESC
        """,
    }
}


class BigQuerySetup:
    """Handles BigQuery setup for SentinelOps"""

    def __init__(self):
        self.project_id = PROJECT_ID
        self.dataset_id = DATASET_ID
        self.location = DATASET_LOCATION
        self.client = bigquery.Client(project=self.project_id)
        self.created_resources = []
        self.failed_resources = []

    def create_dataset(self) -> bool:
        """Create the BigQuery dataset"""
        print("\n📊 Creating BigQuery dataset: {self.dataset_id}")

        dataset = bigquery.Dataset(f"{self.project_id}.{self.dataset_id}")
        dataset.location = self.location
        dataset.description = "SentinelOps security monitoring dataset"

        # Set dataset access controls
        dataset.default_table_expiration_ms = 90 * 24 * 60 * 60 * 1000  # 90 days

        try:
            dataset = self.client.create_dataset(dataset, exists_ok=True)
            print("✅ Dataset created/verified: {dataset.dataset_id}")
            self.created_resources.append(f"Dataset: {self.dataset_id}")
            return True
        except Exception as e:
            print("❌ Failed to create dataset: {e}")
            self.failed_resources.append(f"Dataset: {self.dataset_id} - {str(e)}")
            return False

    def create_table(self, table_id: str, config: Dict) -> bool:
        """Create a single BigQuery table"""
        print("\n📋 Creating table: {table_id}")

        table_ref = f"{self.project_id}.{self.dataset_id}.{table_id}"
        table = bigquery.Table(table_ref)

        # Set table properties
        table.schema = config["schema"]
        table.description = config["description"]

        if "time_partitioning" in config:
            table.time_partitioning = config["time_partitioning"]

        if "clustering_fields" in config:
            table.clustering_fields = config["clustering_fields"]

        try:
            table = self.client.create_table(table, exists_ok=True)
            print("✅ Table created/verified: {table_id}")
            print(
                f"   - Partitioned by: {config.get('time_partitioning', {}).field if 'time_partitioning' in config else 'None'}"
            )
            print("   - Clustered by: {config.get('clustering_fields', [])}")
            self.created_resources.append(f"Table: {table_id}")
            return True
        except Exception as e:
            print("❌ Failed to create table {table_id}: {e}")
            self.failed_resources.append(f"Table: {table_id} - {str(e)}")
            return False

    def create_view(self, view_id: str, config: Dict) -> bool:
        """Create a BigQuery view"""
        print("\n👁️  Creating view: {view_id}")

        view_ref = f"{self.project_id}.{self.dataset_id}.{view_id}"
        view = bigquery.Table(view_ref)
        view.view_query = config["query"]
        view.description = config["description"]

        try:
            view = self.client.create_table(view, exists_ok=True)
            print("✅ View created/verified: {view_id}")
            self.created_resources.append(f"View: {view_id}")
            return True
        except Exception as e:
            print("❌ Failed to create view {view_id}: {e}")
            self.failed_resources.append(f"View: {view_id} - {str(e)}")
            return False

    def setup_log_export(self) -> None:
        """Create log export configurations (requires Cloud Logging Admin permissions)"""
        print("\n📤 Setting up log exports...")

        log_sinks = [
            {
                "name": "vpc-flow-logs-to-bigquery",
                "filter": 'resource.type="gce_subnetwork" AND log_name:"vpc_flows"',
                "destination": f"bigquery.googleapis.com/projects/{self.project_id}/datasets/{self.dataset_id}",
                "description": "Export VPC flow logs to BigQuery",
            },
            {
                "name": "audit-logs-to-bigquery",
                "filter": 'log_name:"cloudaudit.googleapis.com" AND severity >= WARNING',
                "destination": f"bigquery.googleapis.com/projects/{self.project_id}/datasets/{self.dataset_id}",
                "description": "Export audit logs to BigQuery",
            },
            {
                "name": "firewall-logs-to-bigquery",
                "filter": 'resource.type="gce_firewall_rule"',
                "destination": f"bigquery.googleapis.com/projects/{self.project_id}/datasets/{self.dataset_id}",
                "description": "Export firewall logs to BigQuery",
            },
        ]

        # Create shell script for log sink creation
        script_content = """#!/bin/bash
# Log Export Setup Script
# Run this with appropriate permissions to create log sinks

PROJECT_ID="{self.project_id}"
DATASET_ID="{self.dataset_id}"

echo "Creating log sinks for SentinelOps..."

"""

        for sink in log_sinks:
            script_content += """
# Create {sink['name']}
gcloud logging sinks create {sink['name']} \\
    bigquery.googleapis.com/projects/$PROJECT_ID/datasets/$DATASET_ID \\
    --log-filter='{sink['filter']}' \\
    --description="{sink['description']}" \\
    --project=$PROJECT_ID

"""

        script_content += """
echo "Log sinks created. Don't forget to grant BigQuery Data Editor role to the service accounts created by the sinks."
"""

        script_path = Path(__file__).parent / "create_log_sinks.sh"
        with open(script_path, "w") as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)

        print("📝 Created log sink setup script: {script_path}")
        print("   Run this script with appropriate permissions to set up log exports")

    def create_sample_queries(self) -> None:
        """Create sample queries for security analysis"""
        queries_dir = Path(__file__).parent.parent / "queries"
        queries_dir.mkdir(exist_ok=True)

        sample_queries = {
            "suspicious_login_attempts.sql": """
-- Detect suspicious login attempts
SELECT
    timestamp,
    principal_email,
    authentication_info,
    COUNT(*) as attempt_count,
    ARRAY_AGG(DISTINCT JSON_EXTRACT_SCALAR(request, '$.sourceIp')) as source_ips
FROM `{self.project_id}.{self.dataset_id}.audit_logs`
WHERE method_name LIKE '%authenticate%'
    AND severity = 'ERROR'
    AND DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
GROUP BY timestamp, principal_email, authentication_info
HAVING attempt_count > 5
ORDER BY attempt_count DESC
""",
            "data_exfiltration_detection.sql": """
-- Detect potential data exfiltration
SELECT
    timestamp,
    connection.src_ip,
    connection.dest_ip,
    SUM(bytes_sent) as total_bytes,
    COUNT(*) as connection_count
FROM `{self.project_id}.{self.dataset_id}.vpc_flow_logs`
WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
    AND connection.dest_port NOT IN (80, 443)  -- Non-standard ports
    AND reporter = 'SRC'
GROUP BY timestamp, connection.src_ip, connection.dest_ip
HAVING total_bytes > 1000000000  -- More than 1GB
ORDER BY total_bytes DESC
""",
            "privilege_escalation.sql": """
-- Detect privilege escalation attempts
SELECT
    timestamp,
    principal,
    resource,
    bindings,
    JSON_EXTRACT_SCALAR(policy_delta, '$.action') as action
FROM `{self.project_id}.{self.dataset_id}.iam_logs`
WHERE operation.type IN ('SetIamPolicy', 'UpdateRole')
    AND DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND EXISTS (
        SELECT 1 FROM UNNEST(bindings) AS b
        WHERE b.role IN ('roles/owner', 'roles/editor', 'roles/iam.securityAdmin')
    )
ORDER BY timestamp DESC
""",
        }

        for filename, query in sample_queries.items():
            query_path = queries_dir / filename
            with open(query_path, "w") as f:
                f.write(query)

        print("\n📝 Created sample queries in: {queries_dir}")

    def print_summary(self) -> None:
        """Print setup summary"""
        print("\n" + "=" * 60)
        print("📊 BIGQUERY SETUP SUMMARY")
        print("=" * 60)

        if self.created_resources:
            print("\n✅ Created Resources ({len(self.created_resources)}):")
            for resource in self.created_resources:
                print("   • {resource}")

        if self.failed_resources:
            print("\n❌ Failed Resources ({len(self.failed_resources)}):")
            for resource in self.failed_resources:
                print("   • {resource}")

        print("\n📍 Dataset Location: {self.location}")
        print("📅 Default Table Expiration: 90 days")
        print("\n" + "=" * 60)

    def update_checklist(self) -> None:
        """Update the checklist"""
        checklist_path = (
            Path(__file__).parent.parent
            / "docs"
            / "checklists"
            / "08-google-cloud-integration.md"
        )

        if not checklist_path.exists():
            return

        with open(checklist_path, "r") as f:
            content = f.read()

        # Update based on completed tasks
        if any("Dataset" in r for r in self.created_resources):
            content = content.replace(
                "- [ ] Create BigQuery dataset", "- [x] Create BigQuery dataset"
            )
            content = content.replace(
                "  - [ ] Configure dataset settings",
                "  - [x] Configure dataset settings",
            )
            content = content.replace(
                "  - [ ] Set up appropriate access controls",
                "  - [x] Set up appropriate access controls",
            )
            content = content.replace(
                "  - [ ] Configure dataset location",
                "  - [x] Configure dataset location",
            )

        if len([r for r in self.created_resources if "Table" in r]) >= 4:
            content = content.replace(
                "- [ ] Create required tables", "- [x] Create required tables"
            )
            content = content.replace(
                "  - [ ] VPC flow logs table", "  - [x] VPC flow logs table"
            )
            content = content.replace(
                "  - [ ] Audit logs table", "  - [x] Audit logs table"
            )
            content = content.replace(
                "  - [ ] Firewall logs table", "  - [x] Firewall logs table"
            )
            content = content.replace(
                "  - [ ] IAM logs table", "  - [x] IAM logs table"
            )

        with open(checklist_path, "w") as f:
            f.write(content)

        print("\n✅ Updated checklist")

    def run(self) -> None:
        """Run the complete BigQuery setup"""
        # Create dataset
        if not self.create_dataset():
            print("❌ Failed to create dataset. Stopping.")
            return

        # Create tables
        for table_id, config in TABLE_SCHEMAS.items():
            self.create_table(table_id, config)

        # Create views
        for view_id, config in VIEWS.items():
            self.create_view(view_id, config)

        # Setup log export (creates script)
        self.setup_log_export()

        # Create sample queries
        self.create_sample_queries()

        # Print summary and update checklist
        self.print_summary()
        self.update_checklist()


def main():
    """Main entry point"""
    setup = BigQuerySetup()
    setup.run()


if __name__ == "__main__":
    main()
