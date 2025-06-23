# GCP Test Project Infrastructure

This document describes the complete GCP test project infrastructure for SentinelOps testing.

## Overview

The GCP test project infrastructure provides a comprehensive mock environment that simulates all GCP services used by SentinelOps. This ensures consistent, reliable testing without requiring actual GCP resources.

## Features

### 1. Complete Service Coverage
- **BigQuery**: Mock datasets and tables for log analysis
- **Firestore**: Mock collections for data storage
- **Pub/Sub**: Mock topics and subscriptions for messaging
- **Compute Engine**: Mock VMs and firewall rules
- **IAM**: Mock service accounts and permissions
- **Secret Manager**: Mock secrets for API keys
- **Cloud Logging**: Mock logging client
- **Cloud Monitoring**: Mock monitoring client
- **Resource Manager**: Mock project management
- **KMS**: Mock key management service

### 2. Automatic Setup
- Environment variables configured automatically
- Test data populated in all services
- Consistent project ID across all services
- Service account permissions pre-configured

### 3. Test Isolation
- Session-scoped fixture for shared test data
- Function-scoped fixture for isolated tests
- Reset capability for clean state

## Usage

### Basic Usage

```python
def test_with_gcp_project(gcp_test_project):
    """Test using the complete GCP test project."""
    # Access any service
    bigquery = gcp_test_project.bigquery_client
    firestore = gcp_test_project.firestore_client
    
    # Project ID is consistent everywhere
    assert gcp_test_project.project_id == "test-project"
```

### Accessing Individual Services

```python
def test_bigquery_operations(mock_bigquery_client):
    """Test using just the BigQuery client."""
    dataset = mock_bigquery_client.dataset("security_logs")
    table = dataset.table("admin_activity")
    
    # Insert test data
    table.insert_rows_json([{"test": "data"}])
```

### Clean Test Environment

```python
def test_with_clean_project(gcp_test_project_clean):
    """Test with a fresh project that resets after the test."""
    # Modify data without affecting other tests
    collection = gcp_test_project_clean.firestore_client.collection("test")
    collection.add({"data": "test"})
    # Automatically reset after test
```

## Pre-configured Resources

### BigQuery
- Dataset: `security_logs`
- Tables:
  - `admin_activity`
  - `data_access`
  - `system_event`
  - `cloudaudit_googleapis_com_activity`
  - `cloudaudit_googleapis_com_data_access`
  - `cloudaudit_googleapis_com_system_event`

### Firestore Collections
- `incidents`
- `analysis_results`
- `remediation_actions`
- `notifications`
- `agent_state`
- `system_config`

### Pub/Sub Topics
- `incident-detection` (subscriptions: analysis, orchestrator)
- `analysis-complete` (subscriptions: remediation, orchestrator)
- `remediation-complete` (subscriptions: notification, orchestrator)
- `orchestrator-commands` (subscription: all agents)

### Compute Resources
- VMs: `test-vm-1`, `test-vm-2`
- Firewall rules: `allow-ssh`, `allow-http`

### Service Accounts
- `sentinelops-sa@test-project.iam.gserviceaccount.com`
- `detection-agent@test-project.iam.gserviceaccount.com`
- `analysis-agent@test-project.iam.gserviceaccount.com`
- `remediation-agent@test-project.iam.gserviceaccount.com`

### Secrets
- `slack-webhook-url`
- `email-api-key`
- `sms-api-key`
- `gemini-api-key`

## Environment Variables

The following environment variables are automatically set:
- `GOOGLE_CLOUD_PROJECT`: Project ID
- `GCP_PROJECT_ID`: Project ID
- `SENTINELOPS_TEST_MODE`: "true"
- `SENTINELOPS_PROJECT_ID`: Project ID

## Advanced Usage

### Custom Project ID

```python
from tests.infrastructure import setup_gcp_test_project

def test_with_custom_project():
    project = setup_gcp_test_project("my-test-project")
    assert project.project_id == "my-test-project"
```

### Direct Service Access

```python
def test_service_access(gcp_test_project):
    # Get service by name
    compute = gcp_test_project.get_service_client("compute")
    iam = gcp_test_project.get_service_client("iam")
```

### Reset Project State

```python
def test_with_reset(gcp_test_project_clean):
    # Modify state
    gcp_test_project_clean.firestore_client.collection("test").add({"data": 1})
    
    # Manual reset if needed
    gcp_test_project_clean.reset()
    
    # Clean state restored
```

## Best Practices

1. **Use session-scoped fixture for read-only tests** to improve performance
2. **Use function-scoped fixture for tests that modify state**
3. **Access services through the test project** for consistency
4. **Leverage pre-configured resources** instead of creating new ones
5. **Test with realistic data** using the pre-populated test data

## Implementation Status

✅ **Complete**
- Environment variable setup
- All mock service initialization
- Test data population
- Fixture configuration
- Comprehensive test coverage

This infrastructure provides a solid foundation for testing all GCP-dependent components of SentinelOps without requiring actual cloud resources.
