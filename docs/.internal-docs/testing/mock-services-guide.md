# Mock Services Guide

This guide describes the mock service infrastructure for testing SentinelOps components without requiring actual cloud resources.

## Overview

The mock services infrastructure provides:
- Comprehensive mock implementations of Google Cloud services
- Centralized service registry for managing mocks
- Failure injection capabilities for resilience testing
- State management and reset functionality
- Call history tracking for verification

## Service Registry

The `MockServiceRegistry` provides centralized management of all mock services:

```python
from tests.mocks import MockServiceRegistry, register_mock_service, get_mock_service

# Register a service
register_mock_service("my_service", MyMockService)

# Get a service instance
service = get_mock_service("my_service")

# Reset all services
reset_all_mocks()
```

### Registry Features

1. **Service Registration**: Register mock services with unique names
2. **Singleton Management**: Services are instantiated once and reused
3. **Enable/Disable**: Temporarily disable services for testing
4. **Call History**: Track all service accesses for verification
5. **Failure Injection**: Configure services to fail with specific errors
6. **Custom Responses**: Override service methods with custom responses

## Available Mock Services

### Google Cloud Platform Mocks

#### Firestore Mock
```python
from tests.mocks import MockFirestoreClient

# Create mock client
firestore = MockFirestoreClient()

# Document operations
doc_ref = firestore.collection("users").document("user1")
doc_ref.set({"name": "John", "age": 30})
doc = doc_ref.get()
print(doc.to_dict())  # {"name": "John", "age": 30}

# Queries
users = firestore.collection("users")
results = users.where("age", ">", 25).order_by("name").limit(10).get()

# Transactions
with firestore.transaction() as txn:
    doc1 = txn.get(ref1)
    txn.update(ref1, {"balance": doc1.get("balance") - 100})
    txn.update(ref2, {"balance": doc2.get("balance") + 100})
```

#### BigQuery Mock
```python
from tests.mocks import MockBigQueryClient

bigquery = MockBigQueryClient()

# Query execution
results = bigquery.query("SELECT * FROM dataset.table WHERE status = 'active'")
for row in results:
    print(row)

# Pre-configured responses
bigquery.add_query_response(
    "SELECT COUNT(*) FROM logs",
    [{"count": 1000}]
)
```

#### Pub/Sub Mock
```python
from tests.mocks import MockPubSubClient

pubsub = MockPubSubClient()

# Create topic and subscription
topic = pubsub.create_topic("my-topic")
subscription = pubsub.create_subscription("my-sub", "my-topic")

# Publish messages
topic.publish(b"Hello World", attributes={"key": "value"})

# Pull messages
messages = subscription.pull(max_messages=10)
for msg in messages:
    print(msg.data)
    msg.ack()
```

#### Storage Mock
```python
from tests.mocks import MockStorageClient

storage = MockStorageClient()

# Bucket operations
bucket = storage.create_bucket("my-bucket")
blob = bucket.blob("path/to/file.txt")
blob.upload_from_string("Hello World")

# Download
content = blob.download_as_text()
```

#### Secret Manager Mock
```python
from tests.mocks import MockSecretManagerClient

secrets = MockSecretManagerClient()

# Create secret
secret = secrets.create_secret("my-secret")
version = secrets.add_secret_version("my-secret", b"secret-value")

# Access secret
response = secrets.access_secret_version("my-secret", "latest")
print(response.payload.data)  # b"secret-value"
```

#### Vertex AI Mock
```python
from tests.mocks import MockVertexAIClient

vertex = MockVertexAIClient()

# Configure responses
vertex.add_response("Analyze this log", "This appears to be a security incident...")

# Generate content
response = vertex.generate_content("Analyze this log: ...")
print(response.text)
```

### Notification Service Mocks

Currently disabled due to circular imports, but available directly:

```python
from tests.mocks.notification_mocks import (
    MockEmailService,
    MockSlackService,
    MockSMSService,
    MockWebhookService
)

# Email
email = MockEmailService()
await email.send_email("user@example.com", "Subject", "Body")

# Slack
slack = MockSlackService()
await slack.post_message("#security", "Alert: Incident detected")

# SMS
sms = MockSMSService()
await sms.send_sms("+1234567890", "Security alert")

# Webhook
webhook = MockWebhookService()
await webhook.send_webhook("https://example.com/hook", {"event": "incident"})
```

## Failure Injection

Test resilience by injecting failures:

```python
from tests.mocks import configure_mock_failures, MockConfiguration

# Configure specific service failures
configure_mock_failures({
    "gcp_firestore": {
        "failure_rate": 0.5,  # 50% failure rate
        "failure_exception": Exception("Firestore unavailable")
    },
    "gcp_pubsub": {
        "failure_rate": 1.0,  # Always fail
        "failure_exception": TimeoutError("Pub/Sub timeout")
    }
})

# Temporary failure configuration
with MockConfiguration(
    failure_configs={
        "gcp_bigquery": {"failure_rate": 0.3}
    },
    disabled_services=["gcp_storage"]
):
    # Services have temporary configurations
    pass
# Configuration restored after context
```

## Testing Patterns

### Unit Testing with Mocks

```python
import pytest
from tests.mocks import MockFirestoreClient, with_mock_gcp

class TestMyService:
    @pytest.fixture
    def firestore(self):
        return MockFirestoreClient()
    
    def test_user_creation(self, firestore):
        service = UserService(firestore)
        
        # Test the service
        user = service.create_user("John", "john@example.com")
        
        # Verify in Firestore
        doc = firestore.collection("users").document(user.id).get()
        assert doc.exists
        assert doc.get("email") == "john@example.com"
```

### Integration Testing

```python
@with_mock_gcp
async def test_full_workflow():
    # All GCP services are automatically mocked
    detector = DetectionAgent()
    analyzer = AnalysisAgent()
    
    # Simulate incident
    incident = await detector.detect_incident(test_logs)
    analysis = await analyzer.analyze(incident)
    
    # Verify interactions
    assert analysis.risk_level == "HIGH"
```

### Testing with State

```python
def test_stateful_operations():
    firestore = MockFirestoreClient()
    
    # Set up initial state
    firestore.collection("config").document("settings").set({
        "threshold": 100,
        "enabled": True
    })
    
    # Test operations that depend on state
    service = ConfigService(firestore)
    assert service.get_threshold() == 100
    
    # Modify state
    service.update_threshold(200)
    
    # Verify state change
    doc = firestore.collection("config").document("settings").get()
    assert doc.get("threshold") == 200
```

## Best Practices

1. **Reset Between Tests**: Always reset mocks between tests
   ```python
   @pytest.fixture(autouse=True)
   def reset_mocks():
       yield
       reset_all_mocks()
   ```

2. **Use Type Hints**: Ensure proper typing for mock services
   ```python
   def get_firestore() -> MockFirestoreClient:
       return get_mock_service("gcp_firestore")
   ```

3. **Configure Realistic Responses**: Make mocks behave realistically
   ```python
   # Add realistic delays
   mock.configure_latency(min_ms=10, max_ms=50)
   
   # Add realistic data
   mock.add_test_data(generate_realistic_logs())
   ```

4. **Test Error Conditions**: Always test failure scenarios
   ```python
   with MockConfiguration(failure_configs={"service": {"failure_rate": 1.0}}):
       with pytest.raises(ServiceUnavailableError):
           service.operation()
   ```

5. **Verify Interactions**: Use call history for verification
   ```python
   history = get_mock_call_history("gcp_pubsub")
   assert len(history["gcp_pubsub"]) == 3
   assert any("publish" in str(call) for call in history["gcp_pubsub"])
   ```

## Extending Mock Services

To add a new mock service:

```python
from tests.mocks.service_registry import register_mock_service

class MockNewService:
    def __init__(self):
        self.data = {}
        self.calls = []
    
    def operation(self, param):
        self.calls.append(("operation", param))
        return {"result": "success"}
    
    def reset(self):
        self.data.clear()
        self.calls.clear()

# Register the service
register_mock_service("new_service", MockNewService)
```

## Troubleshooting

### Circular Import Issues
If you encounter circular imports:
1. Import mocks directly instead of from `__init__.py`
2. Use string imports in type hints
3. Move shared types to a separate module

### Service Not Found
If a service isn't found:
1. Ensure it's registered before use
2. Check the service name matches exactly
3. Verify the service is enabled

### State Pollution
If tests affect each other:
1. Use `reset_all_mocks()` in test teardown
2. Create fresh instances for each test
3. Use fixtures with proper scope

### Performance Issues
If mocks are slow:
1. Disable unnecessary features (logging, history)
2. Use batch operations where possible
3. Configure appropriate timeouts