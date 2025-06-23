# Google Cloud Service Integration

## Overview

SentinelOps deeply integrates with Google Cloud Platform services to provide comprehensive security monitoring and automated response capabilities. This document details how each GCP service is integrated and utilized within the system.

## Core Service Integrations

### 1. Google Agent Development Kit (ADK)

**Purpose**: Foundation for multi-agent orchestration and coordination

**Integration Points**:
- Base framework for all SentinelOps agents
- Built-in support for async operations
- Native integration with Vertex AI/Gemini
- Event-driven architecture support

**Configuration**:
```python
from google.adk.agents import LLMAgent
from google.adk.tools import FunctionTool

class SentinelOpsAgent(LLMAgent):
    def __init__(self):
        super().__init__(
            name="sentinelops_orchestrator",
            model="gemini-1.5-pro",
            tools=[SecurityTool(), RemediationTool()],
            temperature=0.1  # Low temperature for consistent security decisions
        )
```

### 2. BigQuery

**Purpose**: Security log storage and analysis

**Integration Points**:
- Centralized storage for all security logs
- Real-time streaming inserts from Detection Agent
- Complex SQL queries for anomaly detection
- Historical data for trend analysis

**Schema Design**:
```sql
-- Security events table
CREATE TABLE `project.security_logs.events` (
  event_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  event_type STRING,
  severity STRING,
  source_ip STRING,
  destination_ip STRING,
  user_identity STRING,
  resource_name STRING,
  action STRING,
  outcome STRING,
  raw_log JSON,
  detection_rules ARRAY<STRING>,
  anomaly_score FLOAT64
)
PARTITION BY DATE(timestamp)
CLUSTER BY event_type, severity;

-- Incident tracking table
CREATE TABLE `project.security_logs.incidents` (
  incident_id STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP,
  status STRING,
  severity STRING,
  affected_resources ARRAY<STRING>,
  detection_agent_data JSON,
  analysis_results JSON,
  remediation_actions JSON,
  communication_log JSON
)
PARTITION BY DATE(created_at);
```

**Query Examples**:
```python
# Anomaly detection query
async def detect_unusual_api_calls():
    query = """
    WITH baseline AS (
      SELECT
        user_identity,
        COUNT(*) as typical_daily_calls
      FROM `project.security_logs.events`
      WHERE DATE(timestamp) BETWEEN
        DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
      GROUP BY user_identity, DATE(timestamp)
    ),
    today_activity AS (
      SELECT
        user_identity,
        COUNT(*) as today_calls
      FROM `project.security_logs.events`
      WHERE DATE(timestamp) = CURRENT_DATE()
      GROUP BY user_identity
    )
    SELECT
      t.user_identity,
      t.today_calls,
      AVG(b.typical_daily_calls) as avg_daily_calls,
      t.today_calls / AVG(b.typical_daily_calls) as anomaly_ratio
    FROM today_activity t
    JOIN baseline b ON t.user_identity = b.user_identity
    GROUP BY t.user_identity, t.today_calls
    HAVING anomaly_ratio > 3.0
    """

    return await bigquery_client.query(query)
```

### 3. Cloud Storage

**Purpose**: Artifact storage and evidence preservation

**Bucket Structure**:
```
sentinelops-artifacts/
├── incident-evidence/
│   ├── INC-2024-001/
│   │   ├── logs/
│   │   ├── screenshots/
│   │   ├── memory-dumps/
│   │   └── metadata.json
├── remediation-logs/
│   ├── 2024-01-01/
│   │   ├── action-logs/
│   │   └── rollback-data/
├── reports/
│   ├── daily/
│   ├── weekly/
│   └── monthly/
└── configurations/
    ├── detection-rules/
    ├── agent-configs/
    └── templates/
```

**Integration Code**:
```python
class ArtifactManager:
    def __init__(self, bucket_name: str):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    async def store_evidence(self, incident_id: str, evidence_type: str, data: bytes):
        """Store incident evidence with proper organization."""
        blob_path = f"incident-evidence/{incident_id}/{evidence_type}/{timestamp}.dat"
        blob = self.bucket.blob(blob_path)

        # Set metadata for compliance
        blob.metadata = {
            "incident_id": incident_id,
            "evidence_type": evidence_type,
            "collected_at": datetime.utcnow().isoformat(),
            "retention_days": "365"
        }

        # Upload with encryption
        blob.upload_from_string(data, content_type="application/octet-stream")

        # Set lifecycle for automatic deletion after retention period
        blob.lifecycle_rules = [{
            "action": {"type": "Delete"},
            "condition": {"age": 365}
        }]
```

### 4. Compute Engine

**Purpose**: Resource management and remediation actions

**Integration Points**:
- Instance metadata for security tagging
- Firewall rule management
- Snapshot creation for forensics
- Instance isolation during incidents

**Remediation Actions**:
```python
class ComputeRemediator:
    def __init__(self, project_id: str):
        self.compute = compute_v1.InstancesClient()
        self.firewall = compute_v1.FirewallsClient()
        self.project_id = project_id

    async def isolate_instance(self, instance_name: str, zone: str):
        """Isolate a compromised instance."""
        # 1. Create deny-all firewall rule
        firewall_rule = {
            "name": f"isolate-{instance_name}-{timestamp}",
            "priority": 0,  # Highest priority
            "direction": "INGRESS",
            "sourceRanges": ["0.0.0.0/0"],
            "denied": [{
                "IPProtocol": "all"
            }],
            "targetTags": [f"isolated-{instance_name}"]
        }

        await self.firewall.insert(
            project=self.project_id,
            firewall_resource=firewall_rule
        )

        # 2. Tag the instance
        instance = await self.compute.get(
            project=self.project_id,
            zone=zone,
            instance=instance_name
        )

        instance.tags.items.append(f"isolated-{instance_name}")

        await self.compute.set_tags(
            project=self.project_id,
            zone=zone,
            instance=instance_name,
            tags_resource=instance.tags
        )

        # 3. Create forensic snapshot
        await self.create_forensic_snapshot(instance_name, zone)
```

### 5. Pub/Sub

**Purpose**: Event-driven communication between agents

**Topic Structure**:
```
projects/my-project/topics/
├── sentinelops-incidents          # New incidents from Detection Agent
├── sentinelops-analysis-requests  # Analysis requests
├── sentinelops-analysis-results   # Analysis results
├── sentinelops-remediation-tasks  # Remediation commands
├── sentinelops-remediation-status # Remediation results
├── sentinelops-notifications      # Communication requests
└── sentinelops-dlq               # Dead letter queue
```

**Message Schema**:
```python
class PubSubMessage(BaseModel):
    """Standard message format for agent communication."""

    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str  # Links related messages
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_agent: str
    target_agent: Optional[str] = None
    message_type: str
    priority: int = Field(ge=1, le=5, default=3)
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

**Publisher/Subscriber Setup**:
```python
class AgentPubSub:
    def __init__(self, project_id: str):
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        self.project_id = project_id

    async def publish_event(self, topic_name: str, message: PubSubMessage):
        """Publish event to topic."""
        topic_path = self.publisher.topic_path(self.project_id, topic_name)

        # Convert to JSON bytes
        message_bytes = message.model_dump_json().encode("utf-8")

        # Add attributes for filtering
        attributes = {
            "source_agent": message.source_agent,
            "message_type": message.message_type,
            "priority": str(message.priority)
        }

        # Publish with retry
        future = self.publisher.publish(
            topic_path,
            message_bytes,
            **attributes
        )

        return await future
```

### 6. Vertex AI / Gemini

**Purpose**: Intelligent analysis and decision making

**Integration Points**:
- Incident analysis and severity assessment
- Root cause analysis
- Remediation recommendation
- Natural language report generation

**Analysis Implementation**:
```python
class GeminiAnalyzer:
    def __init__(self, project_id: str, location: str = "us-central1"):
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-1.5-pro")

        # Configure for security analysis
        self.config = GenerationConfig(
            temperature=0.1,  # Low for consistency
            top_p=0.8,
            max_output_tokens=2048,
        )

        # Safety settings for security content
        self.safety_settings = [
            SafetySetting(
                category=SafetyCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=SafetyThreshold.BLOCK_NONE  # Security analysis needs this
            )
        ]

    async def analyze_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze security incident using Gemini."""

        # Construct analysis prompt
        prompt = f"""
        Analyze the following security incident and provide:
        1. Severity assessment (critical/high/medium/low) with justification
        2. Likely root cause
        3. Potential impact on the system
        4. Recommended remediation actions
        5. Similar historical incidents if any

        Incident Data:
        {json.dumps(incident_data, indent=2)}

        Provide response in JSON format.
        """

        response = await self.model.generate_content_async(
            prompt,
            generation_config=self.config,
            safety_settings=self.safety_settings
        )

        # Parse and validate response
        try:
            analysis = json.loads(response.text)
            return self._validate_analysis(analysis)
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            raise
```

### 7. Secret Manager

**Purpose**: Secure credential storage

**Secret Organization**:
```
projects/my-project/secrets/
├── sentinelops-api-key
├── sentinelops-jwt-secret
├── sentinelops-slack-webhook
├── sentinelops-smtp-password
├── sentinelops-encryption-key
└── sentinelops-service-accounts/
    ├── detection-agent-key
    ├── analysis-agent-key
    ├── remediation-agent-key
    └── communication-agent-key
```

**Usage Example**:
```python
async def get_secret_value(secret_name: str) -> str:
    """Retrieve secret from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"

    # Access the secret
    response = await client.access_secret_version(request={"name": name})

    # Decode the payload
    return response.payload.data.decode("UTF-8")
```

### 8. Cloud Logging

**Purpose**: Centralized logging and monitoring

**Log Structure**:
```python
# Structured logging format
{
    "timestamp": "2024-01-01T12:00:00Z",
    "severity": "INFO",
    "agent": "detection_agent",
    "correlation_id": "corr-12345",
    "message": "Processing security event",
    "labels": {
        "environment": "production",
        "version": "1.0.0"
    },
    "jsonPayload": {
        "event_type": "api_call",
        "user": "user@example.com",
        "action": "compute.instances.delete",
        "result": "denied"
    }
}
```

**Integration**:
```python
# Cloud Logging client setup
logging_client = google.cloud.logging.Client()
logging_client.setup_logging()

# Agent-specific logger
agent_logger = logging_client.logger(f"sentinelops-{agent_name}")

# Log with structured data
agent_logger.log_struct({
    "message": "Incident detected",
    "severity": "WARNING",
    "incident_id": incident_id,
    "detection_confidence": 0.95,
    "affected_resources": resource_list
})
```

### 9. Cloud IAM

**Purpose**: Access control and permissions

**Service Account Permissions**:

| Service Account | Required Roles |
|----------------|----------------|
| Detection Agent | `roles/bigquery.dataViewer`<br>`roles/logging.viewer`<br>`roles/pubsub.publisher` |
| Analysis Agent | `roles/bigquery.user`<br>`roles/aiplatform.user`<br>`roles/storage.objectViewer` |
| Remediation Agent | `roles/compute.admin`<br>`roles/iam.securityAdmin`<br>`roles/storage.objectCreator` |
| Communication Agent | `roles/secretmanager.secretAccessor`<br>`roles/logging.logWriter` |
| Orchestrator | `roles/pubsub.editor`<br>`roles/cloudsql.client` |

**Permission Validation**:
```python
async def validate_permissions(service_account: str, required_permissions: List[str]):
    """Validate service account has required permissions."""
    iam = iam_v1.IAMClient()

    # Test permissions
    response = await iam.test_iam_permissions(
        resource=f"projects/{project_id}",
        permissions=required_permissions
    )

    missing = set(required_permissions) - set(response.permissions)
    if missing:
        raise PermissionError(f"Missing permissions: {missing}")
```

## Best Practices

### 1. Service Account Management
- Use separate service accounts per agent
- Rotate service account keys quarterly
- Monitor service account usage

### 2. API Quotas
- Implement exponential backoff
- Use batch operations where possible
- Monitor quota usage

### 3. Cost Optimization
- Use appropriate storage classes
- Set data retention policies
- Enable auto-scaling with limits

### 4. Security
- Enable VPC Service Controls
- Use Customer-Managed Encryption Keys
- Implement audit logging

### 5. Monitoring
- Set up alerts for API errors
- Monitor service latencies
- Track resource utilization
