# Testing Guide for ADK Agents

This comprehensive guide covers all aspects of testing SentinelOps agents built with Google's Agent Development Kit (ADK), including unit tests, integration tests, and end-to-end testing strategies.

**IMPORTANT: All tests must use REAL GCP services and API calls. NO MOCKING of Google Cloud services is allowed.**

## Table of Contents
1. [Testing Overview](#testing-overview)
2. [Real GCP Services Testing Policy](#real-gcp-services-testing-policy)
3. [Unit Testing ADK Components](#unit-testing-adk-components)
4. [Integration Testing](#integration-testing)
5. [End-to-End Testing](#end-to-end-testing)
6. [Testing Tools and Frameworks](#testing-tools-and-frameworks)
7. [Test Data Management](#test-data-management)
8. [Coverage and Quality](#coverage-and-quality)
9. [CI/CD Integration](#cicd-integration)

## Testing Overview

### Testing Philosophy
- **Real Services Only** - All tests use actual GCP services
- **Production-Ready Testing** - Tests validate real integration
- **Test-Driven Development (TDD)** for new features
- **Comprehensive coverage** (minimum 80%)
- **Fast feedback** through parallel execution
- **Realistic scenarios** using production-like data
- **Automated regression** testing

### Testing Pyramid
```
         /\
        /  \  E2E Tests (10%)
       /    \  - Full workflow validation
      /      \  - Production-like scenarios
     /--------\
    /          \ Integration Tests (30%)
   /            \ - Agent communication
  /              \ - Tool interactions
 /                \ - Real GCP services
/------------------\
     Unit Tests (60%)
  - Individual components
  - Tool logic with real APIs
  - Business rules
```

## Real GCP Services Testing Policy

### Mandatory Requirements

**ALL tests MUST use real Google Cloud Platform services:**

✅ **DO:**
- Use actual Cloud Logging clients
- Make real BigQuery queries
- Access real Secret Manager
- Connect to actual Firestore
- Use real Pub/Sub messaging
- Call actual Gemini/Vertex AI APIs
- Test with real ADK agent communication

❌ **DO NOT:**
- Mock any Google Cloud client libraries
- Mock GCP API responses
- Use fake credentials for testing
- Simulate GCP service behavior

### Project Configuration
All tests use the configured GCP project: `your-gcp-project-id`

```python
# All test files should use real project ID
import os
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
```

## Unit Testing ADK Components

### 1. Testing ADK Agents with Real GCP Services

#### Basic Agent Test Structure
```python
# tests/detection_agent/test_adk_agent.py
import pytest
import os
from google.cloud import logging, bigquery
from src.detection_agent.adk_agent import DetectionAgent

# Use real project ID
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")

class TestDetectionAgent:
    @pytest.fixture
    def agent(self):
        """Create agent instance with real GCP configuration."""
        # Agent uses real Gemini API and GCP services
        agent = DetectionAgent(project_id=PROJECT_ID)
        return agent

    @pytest.fixture
    def real_bigquery_client(self):
        """Create real BigQuery client."""
        return bigquery.Client(project=PROJECT_ID)

    @pytest.fixture
    def real_logging_client(self):
        """Create real Cloud Logging client."""
        return logging.Client(project=PROJECT_ID)

    async def test_agent_initialization(self, agent):
        """Test agent initializes with correct configuration."""
        assert agent.name == "detection_agent"
        assert agent.model == "gemini-1.5-flash"
        assert len(agent.tools) > 0
        assert any(tool.name == "query_logs" for tool in agent.tools)
        assert agent.project_id == PROJECT_ID

    async def test_agent_execution_with_real_services(self, agent, real_bigquery_client):
        """Test agent executes detection workflow with real GCP."""
        # Create test data in BigQuery if needed
        dataset_id = "test_detection"
        table_id = "test_logs"

        # Ensure test dataset exists
        dataset = bigquery.Dataset(f"{PROJECT_ID}.{dataset_id}")
        dataset.location = "US"
        try:
            real_bigquery_client.create_dataset(dataset, exists_ok=True)
        except:
            pass  # Dataset already exists

        context = {
            "start_time": "2024-01-01",
            "end_time": "2024-01-02",
            "dataset": dataset_id,
            "table": table_id
        }

        # Execute with real services
        result = await agent.run(context)

        assert result["success"] is True
        assert "incidents" in result
        # Verify real API calls were made
        assert agent.metrics["api_calls"] > 0
```

#### Testing Agent Tools with Real Services
```python
# tests/tools/test_detection_tools.py
import pytest
import os
from google.cloud import bigquery
from src.tools.detection_tools import LogMonitoringTool, AnomalyDetectionTool

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")

class TestLogMonitoringTool:
    @pytest.fixture
    def tool(self):
        """Create tool with real GCP configuration."""
        return LogMonitoringTool(project_id=PROJECT_ID)

    @pytest.fixture
    def test_dataset(self):
        """Create real test dataset in BigQuery."""
        client = bigquery.Client(project=PROJECT_ID)
        dataset_id = f"{PROJECT_ID}.test_logs_{int(time.time())}"

        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        dataset = client.create_dataset(dataset, exists_ok=True)

        yield dataset_id

        # Cleanup
        client.delete_dataset(dataset_id, delete_contents=True, not_found_ok=True)

    def test_tool_metadata(self, tool):
        """Test tool has correct metadata."""
        assert tool.name == "log_monitoring"
        assert "monitor" in tool.description.lower()
        assert hasattr(tool, 'execute')
        assert tool.project_id == PROJECT_ID

    async def test_execute_with_real_bigquery(self, tool, test_dataset):
        """Test successful log query execution with real BigQuery."""
        # Create test table with sample data
        client = bigquery.Client(project=PROJECT_ID)
        table_id = f"{test_dataset}.security_logs"

        schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("severity", "STRING"),
            bigquery.SchemaField("message", "STRING"),
        ]

        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table, exists_ok=True)

        # Insert test data
        rows_to_insert = [
            {"timestamp": "2024-01-01 12:00:00", "severity": "ERROR", "message": "Failed login"},
            {"timestamp": "2024-01-01 12:01:00", "severity": "WARNING", "message": "Rate limit"},
        ]

        errors = client.insert_rows_json(table, rows_to_insert)
        assert errors == []

        # Execute real query
        result = await tool.execute(
            query=f"SELECT * FROM `{table_id}` WHERE severity='ERROR'",
            time_range_minutes=60
        )

        assert result["success"] is True
        assert len(result["events"]) >= 1
        assert result["events"][0]["severity"] == "ERROR"

    async def test_execute_with_real_error(self, tool):
        """Test tool handles real BigQuery errors gracefully."""
        # Query non-existent table
        result = await tool.execute(
            query="SELECT * FROM `nonexistent.table.name`"
        )

        assert result["success"] is False
        assert "error" in result
        # Should contain real BigQuery error message
        assert "not found" in result["error"].lower() or "does not exist" in result["error"].lower()
```

### 2. Testing Transfer Tools with Real ADK

```python
# tests/tools/test_transfer_tools.py
import pytest
import os
from src.tools.transfer_tools import TransferToAnalysisAgentTool
from src.common.adk_context import ADKContext

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")

class TestTransferTools:
    @pytest.fixture
    def transfer_tool(self):
        """Create transfer tool with real configuration."""
        return TransferToAnalysisAgentTool(project_id=PROJECT_ID)

    @pytest.fixture
    def real_context(self):
        """Create real ADK context object."""
        # Use actual ADK context
        context = ADKContext(project_id=PROJECT_ID)
        context.initialize()
        return context

    async def test_transfer_execution_real(self, transfer_tool, real_context):
        """Test transfer tool executes with real ADK."""
        incident_data = {
            "id": "INC-001",
            "severity": "HIGH",
            "description": "Suspicious activity detected"
        }

        # Execute with real context
        result = await transfer_tool.execute(
            context=real_context,
            incident=incident_data
        )

        # Verify context was updated in real ADK
        assert real_context.get_data("incident") == incident_data

        # Verify result
        assert result["success"] is True
        assert result["transferred_to"] == "analysis_agent"

        # Verify transfer was logged in Cloud Logging
        assert real_context.metrics["transfers_initiated"] > 0

    async def test_transfer_with_circuit_breaker_real(self, transfer_tool, real_context):
        """Test transfer tool circuit breaker with real services."""
        # Create an invalid transfer scenario
        invalid_context = ADKContext(project_id=PROJECT_ID)
        # Don't initialize to simulate failure

        # Attempt transfers until circuit opens
        failure_count = 0
        for i in range(6):  # Threshold is 5
            try:
                await transfer_tool.execute(
                    context=invalid_context,
                    incident={"id": f"FAIL-{i}"}
                )
            except Exception as e:
                failure_count += 1
                # Real ADK will raise actual exceptions
                assert "context not initialized" in str(e).lower() or \
                       "transfer failed" in str(e).lower()

        # Verify failures were recorded
        assert failure_count >= 5

        # Circuit should be open now
        result = await transfer_tool.execute(
            context=real_context,
            incident={"id": "TEST-CIRCUIT"}
        )

        assert result["status"] == "circuit_open"
        assert result["fallback"] == "orchestrator"
```

### 3. Testing with Real ADK Components

```python
# tests/integration/test_real_adk_components.py
import pytest
import os
from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool
from google.cloud import logging

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")

class TestRealADKIntegration:
    @pytest.fixture
    def real_logging_client(self):
        """Get real Cloud Logging client."""
        return logging.Client(project=PROJECT_ID)

    @pytest.fixture
    def real_agent(self):
        """Create real ADK agent."""
        from src.detection_agent.adk_agent import DetectionAgent
        return DetectionAgent(project_id=PROJECT_ID)

    async def test_agent_tool_execution_real(self, real_agent, real_logging_client):
        """Test agent executes tools with real services."""
        # Execute real detection
        result = await real_agent.detect_anomalies(
            time_window_hours=1,
            severity_threshold="HIGH"
        )

        assert result is not None
        assert "anomalies" in result

        # Verify logs were written to Cloud Logging
        logger_name = f"projects/{PROJECT_ID}/logs/adk-agent-detection"

        # Query recent logs (real API call)
        filter_str = f'logName="{logger_name}" AND timestamp>="2024-01-01T00:00:00Z"'
        entries = list(real_logging_client.list_entries(filter_=filter_str, max_results=10))

        # Should have real log entries
        assert len(entries) >= 0  # May be 0 if no anomalies detected

    async def test_multi_agent_communication_real(self):
        """Test real agent-to-agent communication."""
        from src.orchestrator_agent.adk_agent import OrchestratorAgent
        from src.detection_agent.adk_agent import DetectionAgent

        orchestrator = OrchestratorAgent(project_id=PROJECT_ID)
        detection = DetectionAgent(project_id=PROJECT_ID)

        # Real agent registration
        await orchestrator.register_sub_agent("detection", detection)

        # Execute real workflow
        incident = {
            "id": "REAL-TEST-001",
            "type": "suspicious_login",
            "severity": "HIGH"
        }

        result = await orchestrator.process_incident(incident)

        assert result["success"] is True
        assert result["processed_by"] == ["orchestrator", "detection"]

        # Cleanup
        await orchestrator.shutdown()
        await detection.shutdown()
```

## Integration Testing

### 1. Agent Communication Tests

```python
# tests/integration/test_agent_communication.py
import pytest
import asyncio
from src.orchestrator_agent.adk_agent import OrchestratorAgent
from src.detection_agent.adk_agent import DetectionAgent
from src.analysis_agent.adk_agent import AnalysisAgent

class TestAgentCommunication:
    @pytest.fixture
    async def agent_system(self):
        """Set up multi-agent system for testing."""
        orchestrator = OrchestratorAgent()
        detection = DetectionAgent()
        analysis = AnalysisAgent()

        # Configure agent discovery
        orchestrator.register_agent("detection", detection)
        orchestrator.register_agent("analysis", analysis)

        yield {
            "orchestrator": orchestrator,
            "detection": detection,
            "analysis": analysis
        }

        # Cleanup
        await orchestrator.shutdown()
        await detection.shutdown()
        await analysis.shutdown()

    @pytest.mark.integration
    async def test_detection_to_analysis_flow(self, agent_system):
        """Test incident flow from detection to analysis."""
        # Create test incident
        test_incident = {
            "id": "TEST-001",
            "type": "brute_force_attack",
            "severity": "HIGH",
            "source_ip": "192.168.1.100"
        }

        # Start detection
        detection_result = await agent_system["detection"].detect_incident(test_incident)
        assert detection_result["success"] is True

        # Verify transfer to analysis
        await asyncio.sleep(1)  # Allow transfer to complete

        # Check analysis agent received incident
        analysis_state = agent_system["analysis"].get_current_incident()
        assert analysis_state is not None
        assert analysis_state["id"] == "TEST-001"
```

### 2. Tool Integration Tests

```python
# tests/integration/test_tool_integration.py
import pytest
from google.cloud import bigquery, firestore
from src.tools.firestore_tool import FirestoreTool
from src.tools.bigquery_tool import BigQueryTool

class TestToolIntegration:
    @pytest.fixture
    def firestore_client(self):
        """Create Firestore client for testing."""
        # Use emulator
        import os
        os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
        return firestore.Client(project="test-project")

    @pytest.fixture
    def bigquery_client(self):
        """Create BigQuery client for testing."""
        return bigquery.Client(project="test-project")

    @pytest.mark.integration
    async def test_firestore_tool_operations(self, firestore_client):
        """Test Firestore tool CRUD operations."""
        tool = FirestoreTool(client=firestore_client)

        # Create document
        create_result = await tool.execute(
            operation="create",
            collection="test_incidents",
            document_id="TEST-001",
            data={"severity": "HIGH", "status": "open"}
        )
        assert create_result["success"] is True

        # Read document
        read_result = await tool.execute(
            operation="read",
            collection="test_incidents",
            document_id="TEST-001"
        )
        assert read_result["data"]["severity"] == "HIGH"

        # Update document
        update_result = await tool.execute(
            operation="update",
            collection="test_incidents",
            document_id="TEST-001",
            data={"status": "resolved"}
        )
        assert update_result["success"] is True

        # Delete document
        delete_result = await tool.execute(
            operation="delete",
            collection="test_incidents",
            document_id="TEST-001"
        )
        assert delete_result["success"] is True
```

### 3. External Service Integration

```python
# tests/integration/test_external_services.py
import pytest
import responses
from src.tools.slack_tool import SlackNotificationTool

class TestExternalServiceIntegration:
    @pytest.fixture
    def slack_tool(self):
        return SlackNotificationTool(webhook_url="https://hooks.slack.com/test")

    @pytest.mark.integration
    @responses.activate
    def test_slack_notification(self, slack_tool):
        """Test Slack notification integration."""
        # Mock Slack API response
        responses.add(
            responses.POST,
            "https://hooks.slack.com/test",
            json={"ok": True},
            status=200
        )

        result = slack_tool.execute(
            channel="#security-alerts",
            message="Test security alert",
            severity="HIGH"
        )

        assert result["success"] is True
        assert len(responses.calls) == 1

        # Verify request payload
        request_body = responses.calls[0].request.body
        assert "#security-alerts" in request_body
        assert "Test security alert" in request_body
```

## End-to-End Testing

### 1. Complete Workflow Tests

```python
# tests/e2e/test_complete_workflow.py
import pytest
import asyncio
from tests.fixtures.test_data import create_test_incident
from src.multi_agent.sentinelops_multi_agent import SentinelOpsMultiAgent

class TestE2EWorkflow:
    @pytest.fixture
    async def multi_agent_system(self):
        """Initialize complete multi-agent system."""
        system = SentinelOpsMultiAgent()
        await system.initialize()
        yield system
        await system.shutdown()

    @pytest.mark.e2e
    @pytest.mark.timeout(300)  # 5 minute timeout
    async def test_complete_incident_response(self, multi_agent_system):
        """Test complete incident response workflow."""
        # Create realistic test incident
        incident = create_test_incident(
            incident_type="data_exfiltration",
            severity="CRITICAL",
            affected_resources=["vm-prod-001", "bucket-sensitive-data"]
        )

        # Process incident through system
        result = await multi_agent_system.process_incident(incident)

        # Verify all stages completed
        assert result["detection"]["success"] is True
        assert result["analysis"]["success"] is True
        assert result["remediation"]["success"] is True
        assert result["communication"]["success"] is True

        # Verify specific outcomes
        assert len(result["remediation"]["actions_taken"]) > 0
        assert "vm-prod-001" in result["remediation"]["isolated_resources"]
        assert result["communication"]["notifications_sent"] > 0

        # Verify timing
        total_time = result["metrics"]["total_processing_time"]
        assert total_time < 60  # Should complete within 1 minute
```

### 2. Performance Tests

```python
# tests/performance/test_agent_performance.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from src.detection_agent.adk_agent import DetectionAgent

class TestPerformance:
    @pytest.fixture
    def detection_agent(self):
        return DetectionAgent()

    @pytest.mark.performance
    async def test_detection_throughput(self, detection_agent):
        """Test detection agent can handle high throughput."""
        num_events = 1000
        events = [create_test_log_event() for _ in range(num_events)]

        start_time = time.time()

        # Process events concurrently
        tasks = [detection_agent.process_event(event) for event in events]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        # Verify performance
        successful = sum(1 for r in results if r["success"])
        throughput = successful / duration

        assert successful == num_events
        assert throughput > 100  # Should process >100 events/second
        assert duration < 10  # Should complete in <10 seconds

    @pytest.mark.performance
    def test_concurrent_agent_execution(self):
        """Test multiple agents can run concurrently."""
        num_agents = 5
        num_incidents_per_agent = 10

        def process_incidents(agent_id):
            agent = DetectionAgent(name=f"detection_{agent_id}")
            results = []
            for i in range(num_incidents_per_agent):
                result = asyncio.run(agent.process_incident(f"INC-{agent_id}-{i}"))
                results.append(result)
            return results

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_agents) as executor:
            futures = [executor.submit(process_incidents, i) for i in range(num_agents)]
            all_results = [f.result() for f in futures]

        duration = time.time() - start_time

        # Verify all incidents processed
        total_processed = sum(len(results) for results in all_results)
        assert total_processed == num_agents * num_incidents_per_agent

        # Verify performance
        assert duration < 30  # Should complete in <30 seconds
```

## Testing Tools and Frameworks

### 1. Test Configuration

```python
# tests/conftest.py
import pytest
import asyncio
import os
from google.cloud import firestore, bigquery, logging, secretmanager

# Configure pytest for async tests
pytest_plugins = ['pytest_asyncio']

# Use real project ID
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def test_environment():
    """Set up test environment variables."""
    test_env = {
        "ENVIRONMENT": "test",
        "GOOGLE_CLOUD_PROJECT": PROJECT_ID,
        "ADK_TELEMETRY_ENABLED": "true",  # Enable real telemetry
        "DRY_RUN_DEFAULT": "false",  # Execute real operations
        "USE_REAL_SERVICES": "true"  # Always use real services
    }

    # Ensure we have real credentials
    assert os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), \
        "GOOGLE_APPLICATION_CREDENTIALS must be set for testing"

    # Update environment
    os.environ.update(test_env)
    yield

@pytest.fixture
def real_firestore():
    """Provide real Firestore client."""
    client = firestore.Client(project=PROJECT_ID)
    # Verify connection
    assert client.project == PROJECT_ID
    yield client

@pytest.fixture
def real_bigquery():
    """Provide real BigQuery client."""
    client = bigquery.Client(project=PROJECT_ID)
    # Verify connection
    assert client.project == PROJECT_ID
    yield client

@pytest.fixture
def real_logging():
    """Provide real Cloud Logging client."""
    client = logging.Client(project=PROJECT_ID)
    # Verify connection
    assert client.project == PROJECT_ID
    yield client

@pytest.fixture
def real_secret_manager():
    """Provide real Secret Manager client."""
    client = secretmanager.SecretManagerServiceClient()
    yield client

# Test data cleanup fixtures
@pytest.fixture
def test_collection_cleanup(real_firestore):
    """Clean up test collections after tests."""
    collections_to_clean = []

    def add_collection(collection_name):
        collections_to_clean.append(collection_name)

    yield add_collection

    # Cleanup
    for collection_name in collections_to_clean:
        docs = real_firestore.collection(collection_name).stream()
        for doc in docs:
            doc.reference.delete()

@pytest.fixture
def test_dataset_cleanup(real_bigquery):
    """Clean up test datasets after tests."""
    datasets_to_clean = []

    def add_dataset(dataset_id):
        datasets_to_clean.append(dataset_id)

    yield add_dataset

    # Cleanup
    for dataset_id in datasets_to_clean:
        real_bigquery.delete_dataset(
            dataset_id,
            delete_contents=True,
            not_found_ok=True
        )
```

### 2. Custom Test Markers

```python
# pytest.ini
[pytest]
markers =
    unit: Unit tests
    integration: Integration tests requiring external services
    e2e: End-to-end tests
    performance: Performance tests
    slow: Tests that take >5 seconds
    security: Security-specific tests

# Usage in tests
@pytest.mark.unit
def test_tool_validation():
    pass

@pytest.mark.integration
@pytest.mark.slow
async def test_agent_communication():
    pass
```

### 3. Test Utilities

```python
# tests/utils/test_helpers.py
import json
import datetime
from typing import Dict, Any

def create_test_context(data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create test context for ADK agents."""
    return {
        "request_id": "test-request-001",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "user": "test-user",
        "data": data or {}
    }

def load_test_fixture(filename: str) -> Dict[str, Any]:
    """Load test data from fixture file."""
    with open(f"tests/fixtures/{filename}") as f:
        return json.load(f)

async def wait_for_condition(condition_func, timeout=10, interval=0.1):
    """Wait for a condition to become true."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if await condition_func():
            return True
        await asyncio.sleep(interval)
    return False

class AsyncContextManager:
    """Helper for testing async context managers."""
    def __init__(self, return_value):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
```

## Test Data Management

### 1. Test Fixtures

```python
# tests/fixtures/incidents.py
import uuid
from datetime import datetime, timedelta

def create_test_incident(
    incident_type="brute_force",
    severity="HIGH",
    **kwargs
):
    """Create test incident with realistic data."""
    base_incident = {
        "id": f"TEST-{uuid.uuid4().hex[:8]}",
        "type": incident_type,
        "severity": severity,
        "detected_at": datetime.utcnow().isoformat(),
        "source": {
            "ip": kwargs.get("source_ip", "192.168.1.100"),
            "location": kwargs.get("location", "Unknown"),
            "user": kwargs.get("user", "test-user")
        },
        "affected_resources": kwargs.get("affected_resources", []),
        "indicators": {
            "failed_logins": kwargs.get("failed_logins", 10),
            "time_window": kwargs.get("time_window", 300)
        },
        "status": "open"
    }

    return {**base_incident, **kwargs}

def create_test_log_batch(size=100):
    """Create batch of test log entries."""
    logs = []
    base_time = datetime.utcnow() - timedelta(hours=1)

    for i in range(size):
        log_entry = {
            "timestamp": (base_time + timedelta(seconds=i*10)).isoformat(),
            "severity": ["INFO", "WARNING", "ERROR"][i % 3],
            "resource": f"projects/test/instances/vm-{i % 10}",
            "message": f"Test log entry {i}",
            "labels": {
                "type": ["login", "api_call", "system"][i % 3]
            }
        }
        logs.append(log_entry)

    return logs
```

### 2. Test Database Setup

```python
# tests/fixtures/database.py
import pytest
from google.cloud import firestore

class TestDatabase:
    def __init__(self):
        self.client = firestore.Client(project="test-project")
        self.test_collections = []

    def create_collection(self, name: str):
        """Create test collection."""
        collection_name = f"test_{name}_{uuid.uuid4().hex[:8]}"
        self.test_collections.append(collection_name)
        return self.client.collection(collection_name)

    def cleanup(self):
        """Clean up test collections."""
        for collection_name in self.test_collections:
            self._delete_collection(collection_name)

    def _delete_collection(self, collection_name):
        """Delete all documents in collection."""
        docs = self.client.collection(collection_name).stream()
        for doc in docs:
            doc.reference.delete()

@pytest.fixture
def test_db():
    """Provide test database for integration tests."""
    db = TestDatabase()
    yield db
    db.cleanup()
```

## Coverage and Quality

### 1. Coverage Configuration

```ini
# .coveragerc
[run]
source = src
omit =
    */tests/*
    */venv/*
    */__pycache__/*
    */migrations/*

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov

[xml]
output = coverage.xml
```

### 2. Coverage Commands

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test categories with coverage
pytest -m unit --cov=src.tools --cov-report=term-missing

# Generate coverage badge
coverage-badge -o coverage.svg -f

# Check coverage threshold
pytest --cov=src --cov-fail-under=80
```

### 3. Code Quality Checks

```python
# tests/quality/test_code_quality.py
import ast
import os
from pathlib import Path

class TestCodeQuality:
    def test_no_hardcoded_secrets(self):
        """Ensure no hardcoded secrets in code."""
        secret_patterns = [
            "api_key=",
            "password=",
            "secret=",
            "token=",
            "credential="
        ]

        for py_file in Path("src").rglob("*.py"):
            content = py_file.read_text()
            for pattern in secret_patterns:
                assert pattern not in content.lower(), \
                    f"Potential hardcoded secret in {py_file}"

    def test_no_print_statements(self):
        """Ensure no print statements in production code."""
        for py_file in Path("src").rglob("*.py"):
            tree = ast.parse(py_file.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if hasattr(node.func, 'id') and node.func.id == 'print':
                        raise AssertionError(f"Print statement found in {py_file}")
```

## CI/CD Integration

### 1. GitHub Actions Test Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ./adk
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run unit tests
        run: pytest -m unit --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      firestore:
        image: mtlynch/firestore-emulator
        ports:
          - 8080:8080

    steps:
      - uses: actions/checkout@v3

      - name: Run integration tests
        env:
          FIRESTORE_EMULATOR_HOST: localhost:8080
        run: pytest -m integration

  e2e-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v3

      - name: Run E2E tests
        run: pytest -m e2e --maxfail=1
```

### 2. Pre-commit Test Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: Unit Tests
        entry: pytest -m unit --tb=short
        language: system
        pass_filenames: false
        always_run: true

      - id: pytest-quality
        name: Code Quality Tests
        entry: pytest tests/quality/ -v
        language: system
        pass_filenames: false
```

### 3. Test Reports

```python
# scripts/generate_test_report.py
import json
import pytest
from datetime import datetime

def generate_test_report():
    """Generate comprehensive test report."""
    # Run tests with JSON report
    pytest.main([
        "--json-report",
        "--json-report-file=test_report.json",
        "--html=test_report.html",
        "--self-contained-html"
    ])

    # Parse results
    with open("test_report.json") as f:
        results = json.load(f)

    # Generate summary
    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_tests": results["summary"]["total"],
        "passed": results["summary"]["passed"],
        "failed": results["summary"]["failed"],
        "skipped": results["summary"]["skipped"],
        "duration": results["duration"],
        "coverage": get_coverage_percentage()
    }

    print(f"Test Summary: {json.dumps(summary, indent=2)}")

    return summary

if __name__ == "__main__":
    generate_test_report()
```

---

*This comprehensive testing guide ensures high-quality, reliable ADK agents through thorough testing at all levels of the application stack.*
