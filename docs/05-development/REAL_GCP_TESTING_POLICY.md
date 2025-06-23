# IMPORTANT: Real GCP Services Testing Policy

## ⚠️ MANDATORY TESTING REQUIREMENT

**ALL tests in the SentinelOps project MUST use REAL Google Cloud Platform (GCP) services and API calls.**

## Why Real Services?

This project is designed to work with actual GCP infrastructure in production. Our tests must validate real integration to ensure:

1. **Production Readiness**: Tests verify actual GCP API behavior
2. **Integration Accuracy**: Real service interactions are validated
3. **API Compatibility**: Changes in GCP APIs are detected early
4. **Performance Reality**: Actual latency and limits are tested
5. **Security Validation**: Real authentication and authorization flows

## What This Means

### ✅ DO Use Real Services:

- **Cloud Logging**: Use actual `google.cloud.logging.Client`
- **BigQuery**: Make real queries with `google.cloud.bigquery.Client`
- **Firestore**: Use real `google.cloud.firestore.Client`
- **Secret Manager**: Access real secrets with `secretmanager.SecretManagerServiceClient`
- **Pub/Sub**: Use actual message queues
- **Vertex AI/Gemini**: Make real AI/ML API calls
- **ADK Agents**: Use real agent communication
- **Cloud Storage**: Use actual bucket operations
- **IAM**: Test real permissions and service accounts

### ❌ DO NOT Mock:

- Google Cloud client libraries
- GCP API responses
- ADK agent communication
- Service authentication
- API error responses
- Cloud resource operations

## Project Configuration

All tests use the configured GCP project: `your-gcp-project-id`

```python
# All test files should include:
import os
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
```

## Example: Correct Testing Approach

### ✅ CORRECT - Using Real Services:

```python
import pytest
from google.cloud import firestore

class TestIncidentStorage:
    @pytest.fixture
    def firestore_client(self):
        # Real Firestore client
        return firestore.Client(project="your-gcp-project-id")
    
    def test_store_incident(self, firestore_client):
        # Create real document
        doc_ref = firestore_client.collection('incidents').document('TEST-001')
        doc_ref.set({
            'severity': 'HIGH',
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        
        # Verify with real read
        doc = doc_ref.get()
        assert doc.exists
        assert doc.to_dict()['severity'] == 'HIGH'
        
        # Clean up real resource
        doc_ref.delete()
```

### ❌ INCORRECT - Using Mocks:

```python
# DO NOT DO THIS!
from unittest.mock import Mock, patch

class TestIncidentStorage:
    @patch('google.cloud.firestore.Client')
    def test_store_incident(self, mock_firestore):
        # This is NOT acceptable
        mock_client = Mock()
        mock_firestore.return_value = mock_client
        # ... mock-based testing ...
```

## Test Data Management

### Use Unique Test Resources

Always use unique identifiers for test resources to avoid conflicts:

```python
import uuid
import time

# Unique collection names
test_collection = f"test_incidents_{int(time.time())}_{uuid.uuid4().hex[:8]}"

# Unique dataset names
test_dataset = f"test_logs_{int(time.time())}"

# Unique bucket names
test_bucket = f"test-artifacts-{uuid.uuid4().hex[:8]}"
```

### Always Clean Up

Every test MUST clean up its resources:

```python
@pytest.fixture
def test_collection(firestore_client):
    collection_name = f"test_{int(time.time())}"
    yield collection_name
    
    # Cleanup - delete all documents
    docs = firestore_client.collection(collection_name).stream()
    for doc in docs:
        doc.reference.delete()
```

## Handling Test Costs

Real GCP services incur costs. To minimize expenses:

1. **Use Small Datasets**: Test with minimal data
2. **Clean Up Immediately**: Delete resources after each test
3. **Batch Operations**: Group related tests
4. **Use Appropriate Regions**: Test in low-cost regions
5. **Monitor Usage**: Track API calls and storage

## Environment Setup

Ensure your test environment has:

1. **Valid Credentials**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
   export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
   ```

2. **Required APIs Enabled**:
   - Cloud Logging API
   - BigQuery API
   - Firestore API
   - Secret Manager API
   - Vertex AI API
   - Cloud Build API

3. **Sufficient Permissions**:
   The service account must have appropriate roles for all services being tested.

## CI/CD Considerations

GitHub Actions and other CI systems must:

1. Use real service account credentials (stored as secrets)
2. Run against the actual GCP project
3. Clean up all test resources after runs
4. Monitor for failed cleanup operations

## Performance Testing

When testing performance with real services:

```python
@pytest.mark.performance
async def test_real_api_latency(real_bigquery):
    start_time = time.time()
    
    # Real query
    query = "SELECT COUNT(*) FROM `bigquery-public-data.samples.shakespeare`"
    results = real_bigquery.query(query).result()
    
    duration = time.time() - start_time
    
    # Verify real performance
    assert duration < 5.0  # Should complete in < 5 seconds
    assert results.total_rows == 1
```

## Troubleshooting

### Common Issues:

1. **Authentication Errors**: Ensure GOOGLE_APPLICATION_CREDENTIALS is set
2. **Permission Denied**: Check service account roles
3. **Resource Not Found**: Verify project ID and resource names
4. **Quota Exceeded**: Implement rate limiting in tests
5. **Timeout Errors**: Increase timeout for slower operations

### Debug Real Service Issues:

```python
import logging

# Enable debug logging for GCP libraries
logging.getLogger('google.cloud').setLevel(logging.DEBUG)
```

## Questions?

If you have questions about testing with real GCP services:

1. Check the [testing guide](./testing-guide.md)
2. Review existing test examples in the codebase
3. Consult the GCP documentation for specific services
4. Ask in the project discussions

Remember: **NO MOCKS for Google Cloud services. Period.**
