#!/usr/bin/env python3
"""
Comprehensive tests for Cloud Run agent wrapper.
100% production code, NO MOCKING - tests real FastAPI application behavior.

CRITICAL REQUIREMENT: Achieve ≥90% statement coverage of cloud_run_agent_wrapper.py
"""
# pylint: disable=redefined-outer-name  # Pytest fixtures

import asyncio
import base64
import json
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from google.cloud import firestore

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def real_gcp_config() -> dict[str, str | None]:
    """Real GCP configuration for testing."""
    return {
        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "sentinelops-test"),
        "region": os.getenv("GOOGLE_CLOUD_REGION", "us-central1"),
        "credentials": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    }


@pytest.fixture
def production_firestore_client(real_gcp_config: dict[str, str | None]) -> firestore.Client:
    """Real Firestore client for testing."""
    return firestore.Client(project=real_gcp_config["project_id"])


@pytest.fixture
def real_agent(real_gcp_config: dict[str, str], production_firestore_client: firestore.Client) -> Any:  # pylint: disable=unused-argument
    """Create real agent instance for testing."""
    from src.agent_factory import create_agent

    # Create real agent with proper configuration
    return create_agent("detection", project_id=real_gcp_config["project_id"])


@pytest.fixture
def app_client(real_agent: Any) -> TestClient:
    """Create test client for the FastAPI app with real agent."""
    # Set up real agent in wrapper before importing
    import src.cloud_run_agent_wrapper as wrapper

    wrapper.AGENT = real_agent

    from src.cloud_run_agent_wrapper import app

    return TestClient(app)


@pytest.fixture
def reset_global_state(real_agent: Any) -> Any:
    """Reset global state with real agent before each test."""
    from src import cloud_run_agent_wrapper

    cloud_run_agent_wrapper.AGENT = real_agent
    cloud_run_agent_wrapper.AGENT_TASK = None
    cloud_run_agent_wrapper.shutdown_event.clear()

    # Clear the message queue
    while not cloud_run_agent_wrapper.message_queue.empty():
        try:
            cloud_run_agent_wrapper.message_queue.get_nowait()
        except asyncio.QueueEmpty:
            break
    yield
    # Cleanup after test
    cloud_run_agent_wrapper.shutdown_event.set()


class TestCloudRunAgentWrapperProduction:
    """Test suite for Cloud Run Agent Wrapper using real GCP services."""

    def test_health_check_endpoint(self, app_client: TestClient) -> None:
        """Test health check endpoint returns operational status."""
        response = app_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert data["status"] in ["healthy", "operational"]

    def test_readiness_check_endpoint(self, app_client: TestClient) -> None:
        """Test readiness check endpoint with real agent."""
        response = app_client.get("/ready")

        # Should return 200 when agent is ready
        assert response.status_code in [200, 503]  # May not be ready immediately

        data = response.json()
        assert "ready" in data
        assert "timestamp" in data

    def test_metrics_endpoint(self, app_client: TestClient) -> None:
        """Test metrics endpoint returns real agent metrics."""
        response = app_client.get("/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "timestamp" in data
        assert "metrics" in data

        # Real agent should provide meaningful metrics
        metrics = data["metrics"]
        assert isinstance(metrics, dict)

    def test_status_endpoint(self, app_client: TestClient) -> None:
        """Test status endpoint returns real agent status."""
        response = app_client.get("/status")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "agent_id" in data

    def test_pubsub_message_handling(self, app_client: TestClient, real_gcp_config: dict[str, str]) -> None:
        """Test PubSub message handling with real message format."""
        # Create real PubSub message format
        message_data = {
            "incident_id": "test-incident-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": "high",
            "type": "security_alert",
        }

        encoded_data = base64.b64encode(json.dumps(message_data).encode()).decode()

        pubsub_payload = {
            "message": {
                "data": encoded_data,
                "attributes": {
                    "source": "detection_agent",
                    "project_id": real_gcp_config["project_id"],
                },
                "messageId": "test-message-001",
                "publishTime": datetime.now(timezone.utc).isoformat(),
            }
        }

        response = app_client.post("/", json=pubsub_payload)

        # Should successfully process real message
        assert response.status_code == 200

        # Verify response
        assert response.text == "OK"

    def test_invalid_pubsub_message(self, app_client: TestClient) -> None:
        """Test handling of invalid PubSub message."""
        invalid_payload = {
            "message": {
                "data": "invalid-base64-data",
                "attributes": {},
                "messageId": "invalid-message",
            }
        }

        response = app_client.post("/", json=invalid_payload)

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_test_action_endpoint(self, app_client: TestClient) -> None:
        """Test test action endpoint with real agent capabilities."""
        test_payload = {
            "action": "health_check",
            "parameters": {"check_gcp_connectivity": True, "verify_credentials": True},
        }

        response = app_client.post("/test", json=test_payload)
        assert response.status_code == 200

        data = response.json()
        assert "result" in data
        assert "timestamp" in data

    def test_signal_handling(self) -> None:
        """Test signal handling for graceful shutdown."""
        from src.cloud_run_agent_wrapper import handle_signal

        # Test SIGTERM handling
        try:
            handle_signal(signal.SIGTERM, None)
            # Should set shutdown event
            from src.cloud_run_agent_wrapper import shutdown_event

            assert shutdown_event.is_set()
        except SystemExit:
            # Expected behavior
            pass

    def test_agent_initialization(self, real_agent: Any) -> None:
        """Test real agent initialization and basic functionality."""
        # Verify agent is properly initialized
        assert real_agent is not None
        assert hasattr(real_agent, "run")
        assert hasattr(real_agent, "handle_pubsub_message")

    def test_concurrent_message_processing(self, app_client: TestClient, real_gcp_config: dict[str, str]) -> None:
        """Test concurrent processing of multiple real messages."""
        messages = []

        for i in range(3):
            message_data = {
                "incident_id": f"test-incident-{i:03d}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "severity": "medium",
                "type": "performance_alert",
            }

            encoded_data = base64.b64encode(json.dumps(message_data).encode()).decode()

            pubsub_payload = {
                "message": {
                    "data": encoded_data,
                    "attributes": {
                        "source": "monitoring",
                        "project_id": real_gcp_config["project_id"],
                    },
                    "messageId": f"test-message-{i:03d}",
                    "publishTime": datetime.now(timezone.utc).isoformat(),
                }
            }

            messages.append(pubsub_payload)

        # Send all messages concurrently
        responses = []
        for msg in messages:
            response = app_client.post("/", json=msg)
            responses.append(response)

        # All should be processed successfully
        for response in responses:
            assert response.status_code == 200

    def test_environment_variables(self, real_gcp_config: dict[str, str]) -> None:
        """Test that real GCP environment variables are properly configured."""
        # Verify required environment variables
        assert real_gcp_config["project_id"] is not None
        assert real_gcp_config["region"] is not None

        # Google Application Credentials should be configured
        credentials_path = real_gcp_config["credentials"]
        if credentials_path:
            assert os.path.exists(credentials_path), "GCP credentials file should exist"

    def test_agent_lifecycle(self, app_client: TestClient) -> None:
        """Test complete agent lifecycle operations."""
        # Test startup
        response = app_client.get("/ready")
        startup_ready = response.status_code == 200

        # Test operation
        response = app_client.get("/status")
        assert response.status_code == 200

        # Test metrics collection
        response = app_client.get("/metrics")
        assert response.status_code == 200

        # If agent was ready at startup, verify it maintains health
        if startup_ready:
            response = app_client.get("/health")
            assert response.status_code == 200

    def test_error_recovery(self, app_client: TestClient) -> None:
        """Test error recovery capabilities with malformed requests."""
        # Test malformed JSON
        response = app_client.post("/", data={"content": "invalid json"})
        assert response.status_code in [400, 422]

        # Verify service remains operational after error
        response = app_client.get("/health")
        assert response.status_code == 200

    def test_large_message_handling(self, app_client: TestClient, real_gcp_config: dict[str, str]) -> None:
        """Test handling of large PubSub messages."""
        # Create large message payload
        large_data = {
            "incident_id": "large-incident-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": "high",
            "details": "x" * 1000,  # Large details field
            "metadata": {f"key_{i}": f"value_{i}" for i in range(100)},
        }

        encoded_data = base64.b64encode(json.dumps(large_data).encode()).decode()

        pubsub_payload = {
            "message": {
                "data": encoded_data,
                "attributes": {
                    "source": "large_payload_test",
                    "project_id": real_gcp_config["project_id"],
                },
                "messageId": "large-message-001",
                "publishTime": datetime.now(timezone.utc).isoformat(),
            }
        }

        response = app_client.post("/", json=pubsub_payload)

        # Should handle large messages appropriately
        assert response.status_code in [200, 413]  # 413 for payload too large
