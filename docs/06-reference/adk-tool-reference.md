# ADK Tool Reference

**Last Updated**: June 11, 2025

## Overview

This reference documents all Google ADK (Agent Development Kit) tools implemented in SentinelOps. Each tool extends the `BaseTool` class and provides specific functionality for agent operations.

## Tool Categories

### 1. GCP Service Tools

#### PubSubTool
**Location**: `src/tools/pubsub_tool.py`  
**Purpose**: Manages Pub/Sub messaging for inter-agent communication

```python
class PubSubTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="pubsub_tool",
            description="Publish and subscribe to Pub/Sub topics"
        )
    
    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> Any:
        # Parameters in args:
        # - action: "publish" | "subscribe" | "acknowledge"
        # - topic: str (topic name)
        # - subscription: str (for subscribe/acknowledge)
        # - message: dict (for publish)
        # - message_ids: List[str] (for acknowledge)
```

**Key Methods**:
- `publish_message()`: Send messages to topics
- `pull_messages()`: Retrieve messages from subscriptions
- `acknowledge_messages()`: Mark messages as processed

#### FirestoreTool
**Location**: `src/tools/firestore_tool.py`  
**Purpose**: Database operations for incident and state management

```python
class FirestoreTool(BaseTool):
    name = "firestore_tool"
    description = "Perform Firestore database operations"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - action: "create" | "read" | "update" | "delete" | "query"
        # - collection: str
        # - document_id: str (optional)
        # - data: dict (for create/update)
        # - query_params: dict (for query)
```

**Key Operations**:
- Document CRUD operations
- Complex queries with filtering and ordering
- Batch operations for performance
- Transaction support

#### LoggingTool
**Location**: `src/tools/logging_tool.py`  
**Purpose**: Cloud Logging integration for log analysis

```python
class LoggingTool(BaseTool):
    name = "logging_tool"
    description = "Query and analyze Cloud Logging entries"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - action: "query" | "write" | "analyze"
        # - filter: str (for query)
        # - time_range: dict (start, end timestamps)
        # - severity: str (for filtering)
```

**Capabilities**:
- Advanced log filtering
- Time-based queries
- Severity-based filtering
- Custom metric extraction

#### MonitoringTool
**Location**: `src/tools/monitoring_tool.py`  
**Purpose**: Cloud Monitoring metrics and alerts

```python
class MonitoringTool(BaseTool):
    name = "monitoring_tool"
    description = "Access Cloud Monitoring metrics and alerts"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - action: "query_metrics" | "create_alert" | "get_alerts"
        # - metric_type: str
        # - time_range: dict
        # - aggregation: dict
```

**Features**:
- Time series data retrieval
- Alert policy management
- Custom metric creation
- Anomaly detection support

### 2. Detection Tools

#### LogMonitoringTool
**Location**: `src/detection_agent/adk_agent.py`  
**Purpose**: Real-time log monitoring with BigQuery

```python
class LogMonitoringTool(BaseTool):
    name = "log_monitoring"
    description = "Monitor logs for security events"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - query: str (BigQuery SQL)
        # - time_window: int (minutes)
        # - severity_filter: List[str]
```

**Detection Patterns**:
- Failed authentication attempts
- Privilege escalations
- Suspicious API calls
- Resource access anomalies

#### AnomalyDetectionTool
**Location**: `src/detection_agent/adk_agent.py`  
**Purpose**: Statistical anomaly detection

```python
class AnomalyDetectionTool(BaseTool):
    name = "anomaly_detection"
    description = "Detect anomalous patterns in metrics"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - metric_type: str
        # - threshold_multiplier: float
        # - lookback_window: int (hours)
```

**Detection Methods**:
- Statistical outlier detection
- Time series anomaly detection
- Behavioral pattern analysis
- Threshold-based alerts

#### RulesEngineTool
**Location**: `src/tools/detection_tools.py`  
**Purpose**: Rule-based detection engine

```python
class RulesEngineTool(BaseTool):
    name = "rules_engine"
    description = "Execute detection rules"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - action: "evaluate" | "create" | "update" | "delete"
        # - rule_id: str
        # - rule_data: dict
        # - event_data: dict (for evaluate)
```

### 3. Analysis Tools

#### IncidentAnalysisTool
**Location**: `src/analysis_agent/adk_agent.py`  
**Purpose**: AI-powered incident analysis using Gemini

```python
class IncidentAnalysisTool(BaseTool):
    name = "incident_analysis"
    description = "Analyze incidents using Gemini AI"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - incident_data: dict
        # - analysis_type: "root_cause" | "impact" | "recommendations"
        # - include_context: bool
```

**Analysis Types**:
- Root cause analysis
- Impact assessment
- Threat intelligence correlation
- Remediation recommendations

#### RecommendationTool
**Location**: `src/tools/analysis_tools.py`  
**Purpose**: Generate remediation recommendations

```python
class RecommendationTool(BaseTool):
    name = "recommendation_engine"
    description = "Generate remediation recommendations"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - incident_type: str
        # - severity: str
        # - affected_resources: List[str]
```

#### CorrelationTool
**Location**: `src/tools/analysis_tools.py`  
**Purpose**: Correlate events across multiple sources

```python
class CorrelationTool(BaseTool):
    name = "correlation_engine"
    description = "Correlate related security events"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - events: List[dict]
        # - correlation_window: int (minutes)
        # - correlation_keys: List[str]
```

### 4. Remediation Tools

#### BlockIPTool
**Location**: `src/remediation_agent/adk_agent.py`  
**Purpose**: Block malicious IP addresses

```python
class BlockIPTool(BaseTool):
    name = "block_ip"
    description = "Block IP addresses in Cloud Armor"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - ip_addresses: List[str]
        # - duration: int (seconds)
        # - policy_name: str
        # - dry_run: bool
```

#### IsolateVMTool
**Location**: `src/remediation_agent/adk_agent.py`  
**Purpose**: Isolate compromised VMs

```python
class IsolateVMTool(BaseTool):
    name = "isolate_vm"
    description = "Isolate VM instances"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - instance_name: str
        # - project_id: str
        # - zone: str
        # - isolation_type: "network" | "full"
```

#### RevokeIAMTool
**Location**: `src/remediation_agent/adk_agent.py`  
**Purpose**: Revoke compromised IAM permissions

```python
class RevokeIAMTool(BaseTool):
    name = "revoke_iam"
    description = "Revoke IAM permissions"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - member: str (user/service account)
        # - roles: List[str]
        # - resource: str
        # - temporary: bool
```

#### SnapshotTool
**Location**: `src/remediation_agent/adk_agent.py`  
**Purpose**: Create forensic snapshots

```python
class SnapshotTool(BaseTool):
    name = "create_snapshot"
    description = "Create disk snapshots for forensics"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - disk_name: str
        # - snapshot_name: str
        # - labels: dict
```

### 5. Communication Tools

#### SlackNotificationTool
**Location**: `src/communication_agent/adk_agent.py`  
**Purpose**: Send Slack notifications

```python
class SlackNotificationTool(BaseTool):
    name = "slack_notification"
    description = "Send notifications to Slack"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - channel: str
        # - message: str
        # - attachments: List[dict]
        # - priority: str
```

#### EmailNotificationTool
**Location**: `src/communication_agent/adk_agent.py`  
**Purpose**: Send email alerts

```python
class EmailNotificationTool(BaseTool):
    name = "email_notification"
    description = "Send email notifications"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - recipients: List[str]
        # - subject: str
        # - body: str
        # - attachments: List[dict]
```

### 6. Transfer Tools

#### TransferToDetectionAgentTool
**Location**: `src/tools/transfer_tools.py`  
**Purpose**: Transfer control to Detection Agent

```python
class TransferToDetectionAgentTool(BaseTool):
    name = "transfer_to_detection"
    description = "Transfer task to Detection Agent"
    
    async def execute(self, context: ToolContext) -> ToolResult:
        # Parameters:
        # - task_type: str
        # - task_data: dict
        # - priority: str
```

Similar transfer tools exist for:
- `TransferToAnalysisAgentTool`
- `TransferToRemediationAgentTool`
- `TransferToCommunicationAgentTool`
- `TransferToOrchestratorAgentTool`

## Tool Development Guidelines

### Creating New Tools

1. **Extend BaseTool**:
```python
from google.adk import BaseTool, ToolContext
from typing import Any

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_custom_tool",
            description="Clear description of tool purpose"
        )
    
    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> Any:
        # Implementation
        pass
```

2. **Define Parameters**:
```python
def __init__(self):
    super().__init__()
    self.required_params = ["param1", "param2"]
    self.optional_params = ["param3"]
```

3. **Implement Validation**:
```python
def validate_params(self, params: dict) -> bool:
    # Validate required parameters
    for param in self.required_params:
        if param not in params:
            raise ValueError(f"Missing required parameter: {param}")
    return True
```

4. **Error Handling**:
```python
try:
    result = await self.perform_action(args)
    return {"success": True, "data": result}
except Exception as e:
    return {"success": False, "error": str(e)}
```

### Best Practices

1. **Idempotency**: Tools should be idempotent when possible
2. **Dry Run Support**: Implement dry_run mode for destructive operations
3. **Logging**: Use structured logging for debugging
4. **Timeouts**: Set appropriate timeouts for external calls
5. **Rate Limiting**: Implement rate limiting for API calls
6. **Caching**: Cache results when appropriate
7. **Testing**: Write comprehensive unit tests

### Tool Context

The `ToolContext` provides:
- `agent_id`: Calling agent's identifier
- `incident_id`: Current incident being processed
- `workflow_id`: Active workflow identifier
- `metadata`: Additional context data
- `auth_token`: Authentication credentials

### Tool Results

Tools return any data type, but commonly return dictionaries with:
- `success`: Boolean indicating success/failure
- `data`: Result data (dict)
- `error`: Error message if failed
- `metadata`: Additional information
- `next_action`: Suggested follow-up action

## Performance Considerations

### Optimization Strategies

1. **Batch Operations**:
```python
# Instead of multiple individual calls
for item in items:
    await process_item(item)

# Use batch processing
await process_items_batch(items)
```

2. **Caching**:
```python
@lru_cache(maxsize=128)
def get_cached_result(key: str):
    return expensive_operation(key)
```

3. **Async Operations**:
```python
# Concurrent execution
results = await asyncio.gather(
    tool1.execute(context1),
    tool2.execute(context2),
    tool3.execute(context3)
)
```

### Resource Management

- Set connection pool limits
- Implement circuit breakers
- Monitor memory usage
- Profile execution time

## Related Documentation

- [Agent Documentation](../02-architecture/agents/)
- [ADK Troubleshooting Guide](../04-operations/adk-troubleshooting.md)
- [Testing Guide](../05-development/testing-guide.md)
- [Performance Profiling](../05-development/performance-profiling-guide.md)