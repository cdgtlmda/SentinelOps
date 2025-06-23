# GCP Test Project Infrastructure Guide

This guide explains how to use the GCP test project infrastructure for testing SentinelOps components.

## Overview

The GCP test project infrastructure provides a complete mock environment for all Google Cloud Platform services used by SentinelOps. This allows for comprehensive testing without requiring actual GCP resources or incurring costs.

## Components

### GCPTestProject Class

The main class that provides a unified interface to all mock GCP services:

```python
from tests.infrastructure import GCPTestProject

# Create a test project
test_project = GCPTestProject()

# Access services
bigquery = test_project.bigquery_client
firestore = test_project.firestore_client
pubsub_publisher = test_project.publisher_client
pubsub_subscriber = test_project.subscriber_client
compute = test_project.compute_client
iam = test_project.iam_client
secret_manager = test_project.secret_manager_client
```

### Pre-configured Resources

The test project comes with pre-configured resources:

#### BigQuery
- Dataset: `security_logs`
- Tables:
  - `admin_activity`
  - `data_access`  - `system_event`
  - `cloudaudit_googleapis_com_activity`
  - `cloudaudit_googleapis_com_data_access`
  - `cloudaudit_googleapis_com_system_event`

#### Firestore Collections
- `incidents`
- `analysis_results`
- `remediation_actions`
- `notifications`
- `agent_state`
- `system_config`

#### Pub/Sub Topics and Subscriptions
- Topics:
  - `incident-detection`
  - `analysis-complete`
  - `remediation-complete`
  - `orchestrator-commands`
- Subscriptions are automatically created for each topic

#### Compute Resources
- VMs:
  - `test-vm-1` (running, default network)
  - `test-vm-2` (running, custom-vpc network)
- Firewall Rules:
  - `allow-ssh` (port 22)
  - `allow-http` (ports 80, 443)

#### IAM Configuration
- Service Accounts:
  - `sentinelops-sa@{project-id}.iam.gserviceaccount.com`
  - `detection-agent@{project-id}.iam.gserviceaccount.com`  - `analysis-agent@{project-id}.iam.gserviceaccount.com`
  - `remediation-agent@{project-id}.iam.gserviceaccount.com`
- Pre-configured IAM roles for the default service account

#### Secrets
- `slack-webhook-url`
- `email-api-key`
- `sms-api-key`
- `gemini-api-key`

## Usage in Tests

### Using Pytest Fixtures

The infrastructure provides two main fixtures:

```python
def test_my_component(gcp_test_project):
    """Test using the complete test project."""
    # Access any service
    bigquery = gcp_test_project.bigquery_client
    
    # Query data
    job = bigquery.query("SELECT * FROM security_logs.admin_activity")
    results = list(job.result())

def test_another_component(gcp_services):
    """Test using the service dictionary."""
    # Access services by name
    firestore = gcp_services['firestore']
    
    # Add a document
    doc_ref = firestore.collection('incidents').add({
        'severity': 'HIGH',
        'timestamp': datetime.now()
    })
```

### Direct Usage

```python
from tests.infrastructure import setup_gcp_test_project

# Set up test project with custom project ID
test_project = setup_gcp_test_project("my-test-project-123")

# Environment variables are automatically set
assert os.environ["GOOGLE_CLOUD_PROJECT"] == "my-test-project-123"

# Use services
dataset = test_project.bigquery_client.dataset("security_logs")
table = dataset.table("admin_activity")
```

### Custom Configuration

```python
# Create test project
test_project = GCPTestProject("custom-project")

# Add custom resources
test_project.create_instance({
    "name": "custom-vm",
    "zone": "us-central1-b",
    "machine_type": "n2-standard-2",
    "status": "RUNNING"
})

# Add custom firewall rule
test_project.create_firewall_rule({
    "name": "custom-rule",
    "source_ranges": ["10.0.0.0/8"],
    "allowed": [{"IPProtocol": "tcp", "ports": ["8080"]}]
})
```

## Best Practices

1. **Use fixtures for test isolation**: The `gcp_test_project` fixture automatically resets state between tests.

2. **Test with realistic data**: The infrastructure includes realistic table schemas and resource configurations.

3. **Verify mock behavior**: The mocks behave like real GCP services:
   ```python
   # Topics and subscriptions are linked
   topic_path = f"projects/{project_id}/topics/test-topic"
   sub_path = f"projects/{project_id}/subscriptions/test-sub"
   
   publisher.create_topic(request={"name": topic_path})
   subscriber.create_subscription(request={
       "name": sub_path,
       "topic": topic_path
   })
   ```

4. **Reset when needed**: Use `test_project.reset()` to restore initial state during tests.

5. **Check internal state**: Access mock internals for verification:
   ```python
   # Verify VM was created
   assert "test-project/us-central1-a/my-vm" in test_project.compute_client._instances
   
   # Check published messages
   assert len(test_project.publisher_client._topics[topic_path]) > 0
   ```

## Integration with SentinelOps Components

The test infrastructure is designed to work seamlessly with all SentinelOps agents:

```python
def test_detection_agent_with_gcp(gcp_test_project):
    """Test detection agent with full GCP mock environment."""
    config = {        "project_id": gcp_test_project.project_id,
        "bigquery_dataset": "security_logs",
        "pubsub_topic": "incident-detection"
    }
    
    agent = DetectionAgent(config)
    
    # The agent will use the mock BigQuery client automatically
    results = agent.run_detection_rules()
    
    # Verify results were published to mock Pub/Sub
    topic_path = f"projects/{gcp_test_project.project_id}/topics/incident-detection"
    published_messages = gcp_test_project.publisher_client._topics.get(topic_path, [])
    assert len(published_messages) > 0
```

## Troubleshooting

1. **Import errors**: Ensure you're importing from the correct path:
   ```python
   from tests.infrastructure import GCPTestProject, setup_gcp_test_project
   ```

2. **Missing resources**: Check that resources are created in setup methods:
   ```python
   # Datasets and tables are created in _setup_bigquery_data()
   # Topics and subscriptions are created in _setup_pubsub_data()
   ```

3. **Environment variables**: The `setup_gcp_test_project()` function sets required environment variables automatically.

4. **Mock limitations**: While comprehensive, mocks may not implement every GCP API feature. Add missing functionality as needed.

## Summary

The GCP test project infrastructure provides a complete, consistent, and isolated testing environment for SentinelOps. It eliminates the need for real GCP resources during development and testing while maintaining realistic behavior.