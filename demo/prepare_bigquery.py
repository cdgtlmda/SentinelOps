#!/usr/bin/env python3
"""
Script to prepare BigQuery datasets for SentinelOps demo.
Creates tables and loads sample security incident data.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from google.cloud import bigquery
from google.cloud.exceptions import Conflict
import random

# Configuration
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
DATASET_ID = "sentinelops_demo"
LOCATION = "US"

# Table schemas
INCIDENTS_SCHEMA = [
    bigquery.SchemaField("incident_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("severity", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("type", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("source_ip", "STRING"),
    bigquery.SchemaField("target_resource", "STRING"),
    bigquery.SchemaField("description", "STRING"),
    bigquery.SchemaField("status", "STRING"),
    bigquery.SchemaField("assigned_to", "STRING"),
    bigquery.SchemaField("resolved_at", "TIMESTAMP"),
    bigquery.SchemaField("resolution_notes", "STRING"),
    bigquery.SchemaField("indicators", "JSON"),
    bigquery.SchemaField("recommended_actions", "REPEATED", "STRING"),
]

LOGS_SCHEMA = [
    bigquery.SchemaField("log_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("resource_type", "STRING"),
    bigquery.SchemaField("resource_name", "STRING"),
    bigquery.SchemaField("severity", "STRING"),
    bigquery.SchemaField("message", "STRING"),
    bigquery.SchemaField("source_ip", "STRING"),
    bigquery.SchemaField("user_email", "STRING"),
    bigquery.SchemaField("metadata", "JSON"),
]

ALERTS_SCHEMA = [
    bigquery.SchemaField("alert_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("alert_type", "STRING"),
    bigquery.SchemaField("severity", "STRING"),
    bigquery.SchemaField("resource", "STRING"),
    bigquery.SchemaField("condition", "STRING"),
    bigquery.SchemaField("threshold_value", "FLOAT"),
    bigquery.SchemaField("actual_value", "FLOAT"),
    bigquery.SchemaField("status", "STRING"),
]


def create_dataset(client: bigquery.Client):
    """Create BigQuery dataset if it doesn't exist."""
    dataset_id = f"{PROJECT_ID}.{DATASET_ID}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = LOCATION
    dataset.description = "SentinelOps demo dataset for security incidents and logs"

    try:
        dataset = client.create_dataset(dataset, timeout=30)
        print("✅ Created dataset {dataset_id}")
    except Conflict:
        print("ℹ️  Dataset {dataset_id} already exists")


def create_tables(client: bigquery.Client):
    """Create required tables in the dataset."""
    tables = {
        "incidents": INCIDENTS_SCHEMA,
        "logs": LOGS_SCHEMA,
        "alerts": ALERTS_SCHEMA,
    }

    for table_name, schema in tables.items():
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        table = bigquery.Table(table_id, schema=schema)

        try:
            table = client.create_table(table)
            print("✅ Created table {table_id}")
        except Conflict:
            print("ℹ️  Table {table_id} already exists")


def generate_sample_incidents(count: int = 50):
    """Generate sample incident data."""
    incident_types = [
        "Unauthorized Access", "Data Exfiltration", "Privilege Escalation",
        "Malware Detection", "DDoS Attack", "API Abuse", "Cryptomining",
        "Suspicious Login", "Configuration Change", "Policy Violation"
    ]

    severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    statuses = ["new", "investigating", "resolved", "false_positive"]

    incidents = []
    base_time = datetime.now(timezone.utc) - timedelta(days=7)

    for i in range(count):
        incident_time = base_time + timedelta(
            hours=random.randint(0, 168),
            minutes=random.randint(0, 59)
        )

        severity = random.choice(severities)
        status = random.choice(statuses)

        incident = {
            "incident_id": f"INC-2025-{i +1:04d}",
            "timestamp": incident_time.isoformat(),
            "severity": severity,
            "type": random.choice(incident_types),
            "source_ip": f"{random.randint(1,255)}.{random.randint(1,255)}."
                        f"{random.randint(1,255)}.{random.randint(1,255)}",
            "target_resource": f"resource-{random.randint(1, 20)}",
            "description": f"Security incident detected with {severity} severity",
            "status": status,
            "indicators": json.dumps({
                "score": round(random.uniform(0.5, 1.0), 2),
                "confidence": random.choice(["high", "medium", "low"])
            }),
            "recommended_actions": [
                "Investigate the source",
                "Review access logs",
                "Apply security patch"
            ][:random.randint(1, 3)]
        }

        if status == "resolved":
            incident["resolved_at"] = (
                incident_time + timedelta(hours=random.randint(1, 24))
            ).isoformat()
            incident["resolution_notes"] = "Issue resolved after investigation"

        incidents.append(incident)

    return incidents


def load_data_to_bigquery(client: bigquery.Client, table_name: str, data: list):
    """Load data into BigQuery table."""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=False,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    job = client.load_table_from_json(data, table_id, job_config=job_config)
    job.result()  # Wait for the job to complete

    table = client.get_table(table_id)
    print("✅ Loaded {table.num_rows} rows into {table_id}")


def main():
    """Main function to set up BigQuery for demo."""
    print("🚀 Setting up BigQuery for SentinelOps demo...")
    print("📍 Project: {PROJECT_ID}")
    print("📍 Dataset: {DATASET_ID}")
    print("-" * 50)

    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=PROJECT_ID)
    except Exception as e:
        print("❌ Error initializing BigQuery client: {e}")
        print("Make sure you have set up authentication and billing is enabled.")
        return

    # Create dataset
    print("\n1️⃣ Creating dataset...")
    create_dataset(client)

    # Create tables
    print("\n2️⃣ Creating tables...")
    create_tables(client)

    # Generate and load sample data
    print("\n3️⃣ Generating sample data...")
    incidents = generate_sample_incidents(100)

    print("\n4️⃣ Loading data to BigQuery...")
    load_data_to_bigquery(client, "incidents", incidents)

    print("\n✅ BigQuery setup complete!")
    print("\nYou can query the data using:")
    print("  SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.incidents` LIMIT 10")

    # Run a sample query
    print("\n5️⃣ Running sample query...")
    query = f"""
    SELECT
        severity,
        COUNT(*) as count
    FROM `{PROJECT_ID}.{DATASET_ID}.incidents`
    GROUP BY severity
    ORDER BY count DESC
    """

    results = client.query(query)
    print("\nIncident distribution by severity:")
    for row in results:
        print("  {row.severity}: {row.count} incidents")


if __name__ == "__main__":
    main()
