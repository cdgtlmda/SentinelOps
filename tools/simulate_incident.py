#!/usr/bin/env python3
"""
Incident Simulation Tool for SentinelOps.

This script simulates security incidents for testing the SentinelOps platform.
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google.cloud import pubsub_v1  # noqa: E402
import yaml  # noqa: E402

from src.common.models import (  # noqa: E402
    EventSource, Incident, IncidentStatus, SecurityEvent, SeverityLevel
)


def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def simulate_suspicious_login(project_id: str, pubsub_topic: str) -> None:
    """Simulate a suspicious SSH login incident."""
    print("Simulating suspicious SSH login...")

    # Create a suspicious login event
    event = SecurityEvent(
        event_type="suspicious_login",
        source=EventSource(
            source_type="vpc_flow",
            source_name="vpc_flow_logs",
            source_id=f"vpc-flow-{uuid.uuid4()}"
        ),
        severity=SeverityLevel.HIGH,
        description="Suspicious SSH login detected from unknown IP address",
        raw_data={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "proto": "TCP",
            "src_ip": "198.51.100.123",  # Example IP
            "dest_ip": "10.0.0.15",
            "dest_port": 22,
            "bytes_sent": 4532,
            "packets_sent": 12
        }
    )

    # Create an incident
    incident = Incident(
        title="Suspicious SSH login detected",
        description="Potential unauthorized SSH login detected from unknown IP address",
        severity=SeverityLevel.HIGH,
        status=IncidentStatus.DETECTED,
        events=[event],
        tags=["ssh", "unauthorized_access", "test_incident"]
    )

    # Publish to Pub/Sub
    publish_incident(project_id, pubsub_topic, incident)


def simulate_privilege_escalation(project_id: str, pubsub_topic: str) -> None:
    """Simulate a privilege escalation incident."""
    print("Simulating privilege escalation...")

    # Create a privilege escalation event
    event = SecurityEvent(
        event_type="privilege_escalation",
        source=EventSource(
            source_type="audit",
            source_name="audit_logs",
            source_id=f"audit-{uuid.uuid4()}",
            resource_type="IAM",
            resource_name="roles/admin",
            resource_id="projects/test-project/roles/admin"
        ),
        severity=SeverityLevel.CRITICAL,
        description="Privilege escalation detected: user granted admin permissions",
        raw_data={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "resource_type": "IAM",
            "resource_labels": {"project_id": "test-project"},
            "severity": "WARNING",
            "logName": "projects/test-project/logs/cloudaudit.googleapis.com%2Factivity",
            "method_name": "SetIamPolicy",
            "principal": "user@example.com",
            "caller_ip": "203.0.113.45"
        },
        actor="user@example.com",
        affected_resources=["projects/test-project/roles/admin"]
    )

    # Create an incident
    incident = Incident(
        title="Potential privilege escalation detected",
        description="User granted admin permissions outside of normal process",
        severity=SeverityLevel.CRITICAL,
        status=IncidentStatus.DETECTED,
        events=[event],
        tags=["privilege_escalation", "iam", "test_incident"]
    )

    # Publish to Pub/Sub
    publish_incident(project_id, pubsub_topic, incident)


def simulate_data_exfiltration(project_id: str, pubsub_topic: str) -> None:
    """Simulate a data exfiltration incident."""
    print("Simulating data exfiltration...")

    # Create multiple events for the exfiltration
    events = []

    # First event: Unusual API call
    events.append(SecurityEvent(
        event_type="unusual_api_call",
        source=EventSource(
            source_type="audit",
            source_name="audit_logs",
            source_id=f"audit-{uuid.uuid4()}",
            resource_type="storage.googleapis.com/Bucket",
            resource_name="confidential-data",
            resource_id="projects/test-project/buckets/confidential-data"
        ),
        severity=SeverityLevel.MEDIUM,
        description="Unusual API call to download large number of objects",
        raw_data={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "resource_type": "storage.googleapis.com/Bucket",
            "resource_labels": {"bucket_name": "confidential-data"},
            "severity": "NOTICE",
            "logName": "projects/test-project/logs/cloudaudit.googleapis.com%2Fdata_access",
            "method_name": "storage.objects.get",
            "principal": "user@example.com",
            "caller_ip": "198.51.100.76"
        },
        actor="user@example.com",
        affected_resources=["projects/test-project/buckets/confidential-data"]
    ))

    # Second event: Large data transfer
    events.append(SecurityEvent(
        event_type="large_data_transfer",
        source=EventSource(
            source_type="vpc_flow",
            source_name="vpc_flow_logs",
            source_id=f"vpc-flow-{uuid.uuid4()}"
        ),
        severity=SeverityLevel.HIGH,
        description="Large data transfer to external IP",
        raw_data={
            "timestamp": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
            "proto": "TCP",
            "src_ip": "10.0.0.25",
            "dest_ip": "203.0.113.88",  # External IP
            "dest_port": 443,
            "bytes_sent": 1572864000,  # 1.5 GB
            "packets_sent": 1048576
        }
    ))

    # Create an incident with multiple events
    incident = Incident(
        title="Potential data exfiltration detected",
        description="Large volume of data transferred to external location after unusual API activity",
        severity=SeverityLevel.HIGH,
        status=IncidentStatus.DETECTED,
        events=events,
        tags=["data_exfiltration", "data_access", "test_incident"]
    )

    # Publish to Pub/Sub
    publish_incident(project_id, pubsub_topic, incident)


def publish_incident(project_id: str, topic: str, incident: Incident) -> None:
    """Publish an incident to Pub/Sub."""
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic)

    # Convert incident to dictionary
    incident_dict = incident.model_dump()

    # Create message payload
    message = {
        "message_type": "new_incident",
        "incident": incident_dict,
        "metadata": {
            "agent_id": "incident-simulator",
            "agent_type": "TestTool",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": str(uuid.uuid4())
        }
    }

    # Convert to JSON string and encode
    data = json.dumps(message).encode("utf-8")

    # Publish message
    future = publisher.publish(topic_path, data)
    message_id = future.result()

    print("Published incident {incident.incident_id} with message ID: {message_id}")
    print("Incident details:")
    print("  - Title: {incident.title}")
    print("  - Severity: {incident.severity.value}")
    print("  - Events: {len(incident.events)}")
    print("  - Created at: {incident.created_at}")


def main() -> None:
    """Main function to simulate incidents."""
    parser = argparse.ArgumentParser(description="Simulate security incidents for SentinelOps")
    parser.add_argument("--config", default="../config/config.yaml", help="Path to configuration file")
    parser.add_argument("--incident-type", choices=["ssh", "privilege", "exfiltration", "all"],
                        default="all", help="Type of incident to simulate")

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)
    project_id = config["gcp"]["project_id"]
    orchestration_topic = config["gcp"]["pubsub"]["topics"]["orchestration"]

    # Simulate the requested incident type
    if args.incident_type == "ssh" or args.incident_type == "all":
        simulate_suspicious_login(project_id, orchestration_topic)

    if args.incident_type == "privilege" or args.incident_type == "all":
        simulate_privilege_escalation(project_id, orchestration_topic)

    if args.incident_type == "exfiltration" or args.incident_type == "all":
        simulate_data_exfiltration(project_id, orchestration_topic)


if __name__ == "__main__":
    main()
