"""Common test fixtures."""

import uuid
from datetime import datetime
from typing import Any, Dict

import pytest


@pytest.fixture
def sample_timestamp() -> datetime:
    """Provide a sample timestamp for tests."""
    return datetime(2024, 1, 15, 10, 30, 0)


@pytest.fixture
def sample_incident_data() -> Dict[str, Any]:
    """Provide sample incident data."""
    return {
        "incident_id": f"inc-{uuid.uuid4()}",
        "severity": "high",
        "status": "detected",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "events": [
            {
                "event_id": f"evt-{uuid.uuid4()}",
                "source": "bigquery",
                "data": {"suspicious_activity": True},
            }
        ],
        "analysis": None,
        "remediation": None,
    }


@pytest.fixture
def sample_agent_message() -> Dict[str, Any]:
    """Provide sample agent message."""
    return {
        "agent_id": "test-agent",
        "message_id": f"msg-{uuid.uuid4()}",
        "timestamp": datetime.now(),
        "message_type": "test_message",
        "payload": {"test": "data"},
        "correlation_id": f"corr-{uuid.uuid4()}",
    }


@pytest.fixture
def sample_gcp_resource() -> Dict[str, Any]:
    """Provide sample GCP resource data."""
    return {
        "project_id": "test-project",
        "resource_type": "compute.instance",
        "resource_id": f"instance-{uuid.uuid4()}",
        "location": "us-central1-a",
        "labels": {"env": "test", "app": "sentinelops"},
        "metadata": {"created": datetime.now().isoformat()},
    }
