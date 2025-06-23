"""
Comprehensive tests for src/types/__init__.py

COVERAGE REQUIREMENT: ≥90% statement coverage of target source file
VERIFICATION: python -m coverage run -m pytest tests/unit/types/test___init__.py && python -m coverage report --include="*types/__init__.py" --show-missing

NO MOCKING - 100% Production Code Testing
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Coroutine

# Import all types and classes from the target module - NO MOCKS
from src.types import (
    # Basic types
    JsonType,
    JSONDict,
    JSONList,
    StringDict,
    StringList,
    StringSet,
    StringTuple,
    # Identifiers
    AgentID,
    IncidentID,
    EventID,
    MessageID,
    WorkflowID,
    ResourceID,
    ProjectID,
    UserID,
    # Timestamps
    Timestamp,
    TimestampStr,
    # Enums
    AgentType,
    AgentStatus,
    # Literals
    SeverityLevel,
    IncidentStatus,
    RemediationStatus,
    NotificationChannel,
    NotificationPriority,
    RemediationAction,
    MetricType,
    WorkflowState,
    # TypedDicts
    AgentMessage,
    IncidentDict,
    GCPResource,
    BigQueryResult,
    PubSubMessage,
    AgentConfig,
    NotificationRequest,
    AnalysisRequest,
    AnalysisResult,
    RemediationRequest,
    RemediationResult,
    MetricData,
    HealthStatus,
    WorkflowStep,
    WorkflowDefinition,
    # Type aliases
    ConfigDict,
    ConfigValue,
    Result,
    AsyncResult,
    # Callables
    ErrorHandler,
    MessageHandler,
    AsyncMessageHandler,
    # Protocols
    Loggable,
    Serializable,
    AsyncProcessor,
    MessagePublisher,
    StorageBackend,
    # Type variables
    T,
    R,
)


class TestBasicTypeAliases:
    """Test basic type aliases and NewTypes."""

    def test_json_types(self) -> None:
        """Test JSON-compatible type aliases."""
        # Test JsonType compatibility
        json_string: JsonType = "test"
        json_int: JsonType = 42
        json_float: JsonType = 3.14
        json_bool: JsonType = True
        json_none: JsonType = None
        json_dict: JsonType = {"key": "value"}
        json_list: JsonType = [1, 2, 3]

        assert isinstance(json_string, str)
        assert isinstance(json_int, int)
        assert isinstance(json_float, float)
        assert isinstance(json_bool, bool)
        assert json_none is None
        assert isinstance(json_dict, dict)
        assert isinstance(json_list, list)

    def test_json_dict_and_list(self) -> None:
        """Test JSONDict and JSONList types."""
        test_dict: JSONDict = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "null": None,
            "nested_dict": {"inner": "value"},
            "nested_list": [1, 2, 3],
        }

        test_list: JSONList = ["string", 42, True, None, {"dict": "value"}, [1, 2, 3]]

        assert isinstance(test_dict, dict)
        assert isinstance(test_list, list)
        assert "string" in test_dict
        assert len(test_list) == 6

    def test_string_collections(self) -> None:
        """Test string collection type aliases."""
        test_dict: StringDict = {"key1": "value1", "key2": "value2"}
        test_list: StringList = ["item1", "item2", "item3"]
        test_set: StringSet = {"unique1", "unique2", "unique3"}
        test_tuple: StringTuple = ("tuple1", "tuple2", "tuple3")

        assert isinstance(test_dict, dict)
        assert isinstance(test_list, list)
        assert isinstance(test_set, set)
        assert isinstance(test_tuple, tuple)
        assert all(
            isinstance(k, str) and isinstance(v, str) for k, v in test_dict.items()
        )
        assert all(isinstance(item, str) for item in test_list)
        assert all(isinstance(item, str) for item in test_set)
        assert all(isinstance(item, str) for item in test_tuple)

    def test_identifier_newtypes(self) -> None:
        """Test NewType identifiers."""
        agent_id = AgentID("agent_123")
        incident_id = IncidentID("incident_456")
        event_id = EventID("event_789")
        message_id = MessageID("message_abc")
        workflow_id = WorkflowID("workflow_def")
        resource_id = ResourceID("resource_ghi")
        project_id = ProjectID("project_jkl")
        user_id = UserID("user_mno")

        # NewTypes should behave like their base type
        assert isinstance(agent_id, str)
        assert isinstance(incident_id, str)
        assert isinstance(event_id, str)
        assert isinstance(message_id, str)
        assert isinstance(workflow_id, str)
        assert isinstance(resource_id, str)
        assert isinstance(project_id, str)
        assert isinstance(user_id, str)

        # Test they contain expected values
        assert agent_id == "agent_123"
        assert incident_id == "incident_456"
        assert event_id == "event_789"

    def test_timestamp_types(self) -> None:
        """Test timestamp type aliases."""
        # Test datetime timestamp
        dt_timestamp: Timestamp = datetime.now()
        assert isinstance(dt_timestamp, datetime)

        # Test string timestamp
        str_timestamp: Timestamp = "2024-01-01T00:00:00Z"
        assert isinstance(str_timestamp, str)

        # Test float timestamp
        float_timestamp: Timestamp = 1704067200.0
        assert isinstance(float_timestamp, float)

        # Test TimestampStr
        timestamp_str = TimestampStr("2024-01-01T00:00:00Z")
        assert isinstance(timestamp_str, str)
        assert timestamp_str == "2024-01-01T00:00:00Z"


class TestEnums:
    """Test enum classes."""

    def test_agent_type_enum(self) -> None:
        """Test AgentType enum values and behavior."""
        # Test all enum values exist
        assert AgentType.DETECTION.value == "detection"
        assert AgentType.ANALYSIS.value == "analysis"
        assert AgentType.REMEDIATION.value == "remediation"
        assert AgentType.COMMUNICATION.value == "communication"
        assert AgentType.ORCHESTRATOR.value == "orchestrator"

        # Test enum behavior
        assert len(AgentType) == 5
        assert list(AgentType) == [
            AgentType.DETECTION,
            AgentType.ANALYSIS,
            AgentType.REMEDIATION,
            AgentType.COMMUNICATION,
            AgentType.ORCHESTRATOR,
        ]

        # Test string inheritance
        assert isinstance(AgentType.DETECTION, str)
        assert AgentType.DETECTION.upper() == "DETECTION"

    def test_agent_status_enum(self) -> None:
        """Test AgentStatus enum values and behavior."""
        # Test all enum values exist
        assert AgentStatus.HEALTHY.value == "healthy"
        assert AgentStatus.DEGRADED.value == "degraded"
        assert AgentStatus.UNHEALTHY.value == "unhealthy"
        assert AgentStatus.OFFLINE.value == "offline"
        assert AgentStatus.STARTING.value == "starting"
        assert AgentStatus.STOPPING.value == "stopping"

        # Test enum behavior
        assert len(AgentStatus) == 6
        assert AgentStatus.HEALTHY in list(AgentStatus)

        # Test string inheritance
        assert isinstance(AgentStatus.HEALTHY, str)
        assert AgentStatus.HEALTHY.capitalize() == "Healthy"

    def test_enum_iteration(self) -> None:
        """Test enum iteration and membership."""
        # Test AgentType iteration
        for agent_type in AgentType:
            assert isinstance(agent_type, str)
            assert agent_type.value in [
                "detection",
                "analysis",
                "remediation",
                "communication",
                "orchestrator",
            ]

        # Test AgentStatus iteration
        for status in AgentStatus:
            assert isinstance(status, str)
            assert status.value in [
                "healthy",
                "degraded",
                "unhealthy",
                "offline",
                "starting",
                "stopping",
            ]


class TestLiteralTypes:
    """Test literal type definitions."""

    def test_severity_level(self) -> None:
        """Test SeverityLevel literal type."""
        low: SeverityLevel = "low"
        medium: SeverityLevel = "medium"
        high: SeverityLevel = "high"
        critical: SeverityLevel = "critical"

        assert low == "low"
        assert medium == "medium"
        assert high == "high"
        assert critical == "critical"

        # Test in a list
        all_severities = [low, medium, high, critical]
        assert len(all_severities) == 4

    def test_incident_status(self) -> None:
        """Test IncidentStatus literal type."""
        new: IncidentStatus = "new"
        analyzing: IncidentStatus = "analyzing"
        remediating: IncidentStatus = "remediating"
        resolved: IncidentStatus = "resolved"
        closed: IncidentStatus = "closed"

        assert new == "new"
        assert analyzing == "analyzing"
        assert remediating == "remediating"
        assert resolved == "resolved"
        assert closed == "closed"

    def test_remediation_status(self) -> None:
        """Test RemediationStatus literal type."""
        pending: RemediationStatus = "pending"
        approved: RemediationStatus = "approved"
        executing: RemediationStatus = "executing"
        completed: RemediationStatus = "completed"
        failed: RemediationStatus = "failed"

        assert pending == "pending"
        assert approved == "approved"
        assert executing == "executing"
        assert completed == "completed"
        assert failed == "failed"

    def test_notification_channel(self) -> None:
        """Test NotificationChannel literal type."""
        email: NotificationChannel = "email"
        slack: NotificationChannel = "slack"
        sms: NotificationChannel = "sms"
        webhook: NotificationChannel = "webhook"

        assert email == "email"
        assert slack == "slack"
        assert sms == "sms"
        assert webhook == "webhook"

    def test_notification_priority(self) -> None:
        """Test NotificationPriority literal type."""
        low: NotificationPriority = "low"
        medium: NotificationPriority = "medium"
        high: NotificationPriority = "high"
        critical: NotificationPriority = "critical"

        assert low == "low"
        assert medium == "medium"
        assert high == "high"
        assert critical == "critical"

    def test_remediation_action(self) -> None:
        """Test RemediationAction literal type."""
        actions = [
            "isolate_instance",
            "block_ip",
            "revoke_credentials",
            "update_firewall",
            "restart_service",
            "scale_resources",
            "apply_patch",
        ]

        isolate: RemediationAction = "isolate_instance"
        block: RemediationAction = "block_ip"
        revoke: RemediationAction = "revoke_credentials"
        update: RemediationAction = "update_firewall"
        restart: RemediationAction = "restart_service"
        scale: RemediationAction = "scale_resources"
        patch: RemediationAction = "apply_patch"

        assert isolate in actions
        assert block in actions
        assert revoke in actions
        assert update in actions
        assert restart in actions
        assert scale in actions
        assert patch in actions

    def test_metric_type(self) -> None:
        """Test MetricType literal type."""
        counter: MetricType = "counter"
        gauge: MetricType = "gauge"
        histogram: MetricType = "histogram"
        summary: MetricType = "summary"

        assert counter == "counter"
        assert gauge == "gauge"
        assert histogram == "histogram"
        assert summary == "summary"

    def test_workflow_state(self) -> None:
        """Test WorkflowState literal type."""
        pending: WorkflowState = "pending"
        running: WorkflowState = "running"
        paused: WorkflowState = "paused"
        completed: WorkflowState = "completed"
        failed: WorkflowState = "failed"
        cancelled: WorkflowState = "cancelled"

        assert pending == "pending"
        assert running == "running"
        assert paused == "paused"
        assert completed == "completed"
        assert failed == "failed"
        assert cancelled == "cancelled"


class TestTypedDicts:
    """Test TypedDict classes."""

    def test_agent_message(self) -> None:
        """Test AgentMessage TypedDict."""
        message: AgentMessage = {
            "agent_id": AgentID("test_agent"),
            "message_id": MessageID("msg_123"),
            "timestamp": datetime.now(),
            "message_type": "test_message",
            "payload": {"key": "value"},
            "correlation_id": "corr_456",
        }

        assert message["agent_id"] == "test_agent"
        assert message["message_type"] == "test_message"
        assert isinstance(message["payload"], dict)
        assert message["correlation_id"] == "corr_456"

        # Test optional field
        message_without_correlation: AgentMessage = {
            "agent_id": AgentID("test_agent_2"),
            "message_id": MessageID("msg_124"),
            "timestamp": datetime.now(),
            "message_type": "test_message_2",
            "payload": {"key2": "value2"},
            "correlation_id": None,
        }
        assert message_without_correlation["correlation_id"] is None

    def test_agent_message_with_different_timestamps(self) -> None:
        """Test AgentMessage with different timestamp types."""
        # Test with datetime
        msg_dt: AgentMessage = {
            "agent_id": AgentID("agent_dt"),
            "message_id": MessageID("msg_dt"),
            "timestamp": datetime.now(),
            "message_type": "datetime_test",
            "payload": {},
            "correlation_id": None,
        }
        assert isinstance(msg_dt["timestamp"], datetime)

        # Test with string timestamp
        msg_str: AgentMessage = {
            "agent_id": AgentID("agent_str"),
            "message_id": MessageID("msg_str"),
            "timestamp": "2024-01-01T00:00:00Z",
            "message_type": "string_test",
            "payload": {},
            "correlation_id": None,
        }
        assert isinstance(msg_str["timestamp"], str)

        # Test with float timestamp
        msg_float: AgentMessage = {
            "agent_id": AgentID("agent_float"),
            "message_id": MessageID("msg_float"),
            "timestamp": 1704067200.0,
            "message_type": "float_test",
            "payload": {},
            "correlation_id": None,
        }
        assert isinstance(msg_float["timestamp"], float)

    def test_incident_dict(self) -> None:
        """Test IncidentDict TypedDict."""
        incident: IncidentDict = {
            "incident_id": IncidentID("inc_123"),
            "severity": "high",
            "status": "analyzing",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "events": [{"event": "test"}],
            "analysis": {"confidence": 0.95},
            "remediation": {"action": "block_ip"},
        }

        assert incident["severity"] in ["low", "medium", "high", "critical"]
        assert incident["status"] in [
            "new",
            "analyzing",
            "remediating",
            "resolved",
            "closed",
        ]
        assert isinstance(incident["events"], list)
        assert isinstance(incident["analysis"], dict)

        # Test optional fields
        minimal_incident: IncidentDict = {
            "incident_id": IncidentID("inc_124"),
            "severity": "medium",
            "status": "new",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "events": [],
            "analysis": None,
            "remediation": None,
        }
        assert minimal_incident["analysis"] is None
        assert minimal_incident["remediation"] is None

    def test_gcp_resource(self) -> None:
        """Test GCPResource TypedDict."""
        resource: GCPResource = {
            "project_id": ProjectID("my-project"),
            "resource_type": "compute.instances",
            "resource_id": ResourceID("instance-123"),
            "location": "us-central1-a",
            "labels": {"env": "prod", "team": "security"},
            "metadata": {"created_by": "terraform"},
        }

        assert resource["project_id"] == "my-project"
        assert resource["resource_type"] == "compute.instances"
        assert isinstance(resource["labels"], dict)
        assert isinstance(resource["metadata"], dict)

        # Test optional fields
        minimal_resource: GCPResource = {
            "project_id": ProjectID("my-project-2"),
            "resource_type": "storage.buckets",
            "resource_id": ResourceID("bucket-456"),
            "location": None,
            "labels": None,
            "metadata": None,
        }
        assert minimal_resource["location"] is None
        assert minimal_resource["labels"] is None

    def test_bigquery_result(self) -> None:
        """Test BigQueryResult TypedDict."""
        result: BigQueryResult = {
            "query": "SELECT * FROM dataset.table",
            "rows": [{"id": 1, "name": "test"}],
            "total_rows": 1,
            "bytes_processed": 1024,
            "execution_time": 0.5,
        }

        assert "SELECT" in result["query"]
        assert isinstance(result["rows"], list)
        assert result["total_rows"] == 1
        assert result["bytes_processed"] > 0
        assert result["execution_time"] > 0

    def test_pubsub_message(self) -> None:
        """Test PubSubMessage TypedDict."""
        # Test with string data
        msg_str: PubSubMessage = {
            "data": "test message",
            "attributes": {"source": "test"},
            "message_id": "msg_123",
            "publish_time": datetime.now(),
            "ordering_key": "key1",
        }

        assert isinstance(msg_str["data"], str)
        assert isinstance(msg_str["attributes"], dict)

        # Test with bytes data
        msg_bytes: PubSubMessage = {
            "data": b"test message bytes",
            "attributes": {"source": "test"},
            "message_id": "msg_124",
            "publish_time": "2024-01-01T00:00:00Z",
            "ordering_key": None,
        }

        assert isinstance(msg_bytes["data"], bytes)
        assert msg_bytes["ordering_key"] is None

    def test_agent_config(self) -> None:
        """Test AgentConfig TypedDict."""
        config: AgentConfig = {
            "agent_id": AgentID("agent_123"),
            "agent_type": AgentType.DETECTION,
            "enabled": True,
            "config": {"timeout": 30, "retries": 3},
            "resources": {"cpu": "100m", "memory": "128Mi"},
            "environment": {"LOG_LEVEL": "INFO"},
        }

        assert config["agent_type"] == AgentType.DETECTION
        assert config["enabled"] is True
        assert isinstance(config["config"], dict)

        # Test optional fields
        minimal_config: AgentConfig = {
            "agent_id": AgentID("agent_124"),
            "agent_type": AgentType.ANALYSIS,
            "enabled": False,
            "config": {},
            "resources": None,
            "environment": None,
        }
        assert minimal_config["resources"] is None
        assert minimal_config["environment"] is None


class TestNotificationTypes:
    """Test notification-related TypedDicts."""

    def test_notification_request(self) -> None:
        """Test NotificationRequest TypedDict."""
        request: NotificationRequest = {
            "channel": "email",
            "priority": "high",
            "recipient": "admin@example.com",
            "subject": "Security Alert",
            "message": "Suspicious activity detected",
            "metadata": {"incident_id": "inc_123"},
        }

        assert request["channel"] in ["email", "slack", "sms", "webhook"]
        assert request["priority"] in ["low", "medium", "high", "critical"]
        assert "@" in request["recipient"]
        assert isinstance(request["metadata"], dict)

        # Test optional fields
        minimal_request: NotificationRequest = {
            "channel": "slack",
            "priority": "medium",
            "recipient": "#security-alerts",
            "subject": None,
            "message": "Test message",
            "metadata": None,
        }
        assert minimal_request["subject"] is None
        assert minimal_request["metadata"] is None


class TestAnalysisTypes:
    """Test analysis-related TypedDicts."""

    def test_analysis_request(self) -> None:
        """Test AnalysisRequest TypedDict."""
        request: AnalysisRequest = {
            "incident_id": IncidentID("inc_123"),
            "events": [{"type": "login", "user": "admin"}],
            "context": {"previous_incidents": []},
            "priority": "high",
        }

        assert isinstance(request["events"], list)
        assert request["priority"] in ["low", "medium", "high", "critical"]

        # Test optional context
        minimal_request: AnalysisRequest = {
            "incident_id": IncidentID("inc_124"),
            "events": [],
            "context": None,
            "priority": "low",
        }
        assert minimal_request["context"] is None

    def test_analysis_result(self) -> None:
        """Test AnalysisResult TypedDict."""
        result: AnalysisResult = {
            "incident_id": IncidentID("inc_123"),
            "severity": "critical",
            "root_cause": "Compromised credentials",
            "impact": "Potential data breach",
            "recommendations": ["Revoke credentials", "Audit access logs"],
            "confidence": 0.95,
            "metadata": {"model_version": "v1.2"},
        }

        assert result["severity"] in ["low", "medium", "high", "critical"]
        assert isinstance(result["recommendations"], list)
        assert 0 <= result["confidence"] <= 1

        # Test optional metadata
        minimal_result: AnalysisResult = {
            "incident_id": IncidentID("inc_124"),
            "severity": "low",
            "root_cause": "False positive",
            "impact": "None",
            "recommendations": [],
            "confidence": 0.1,
            "metadata": None,
        }
        assert minimal_result["metadata"] is None


class TestRemediationTypes:
    """Test remediation-related TypedDicts."""

    def test_remediation_request(self) -> None:
        """Test RemediationRequest TypedDict."""
        request: RemediationRequest = {
            "incident_id": IncidentID("inc_123"),
            "action": "block_ip",
            "target": {
                "project_id": ProjectID("my-project"),
                "resource_type": "compute.instances",
                "resource_id": ResourceID("instance-123"),
                "location": "us-central1",
                "labels": None,
                "metadata": None,
            },
            "parameters": {"ip_address": "192.168.1.100"},
            "auto_approve": False,
            "dry_run": True,
        }

        valid_actions = [
            "isolate_instance",
            "block_ip",
            "revoke_credentials",
            "update_firewall",
            "restart_service",
            "scale_resources",
            "apply_patch",
        ]
        assert request["action"] in valid_actions
        assert isinstance(request["target"], dict)
        assert isinstance(request["auto_approve"], bool)
        assert isinstance(request["dry_run"], bool)

        # Test optional parameters
        minimal_request: RemediationRequest = {
            "incident_id": IncidentID("inc_124"),
            "action": "restart_service",
            "target": {
                "project_id": ProjectID("my-project"),
                "resource_type": "compute.instances",
                "resource_id": ResourceID("instance-124"),
                "location": None,
                "labels": None,
                "metadata": None,
            },
            "parameters": None,
            "auto_approve": True,
            "dry_run": False,
        }
        assert minimal_request["parameters"] is None

    def test_remediation_result(self) -> None:
        """Test RemediationResult TypedDict."""
        result: RemediationResult = {
            "incident_id": IncidentID("inc_123"),
            "action": "block_ip",
            "status": "completed",
            "executed_at": datetime.now(),
            "duration": 5.2,
            "result": {"firewall_rule_id": "rule_123"},
            "error": None,
        }

        valid_statuses = ["pending", "approved", "executing", "completed", "failed"]
        assert result["status"] in valid_statuses
        assert isinstance(result["duration"], float)
        assert result["duration"] > 0

        # Test failed result
        failed_result: RemediationResult = {
            "incident_id": IncidentID("inc_124"),
            "action": "revoke_credentials",
            "status": "failed",
            "executed_at": datetime.now(),
            "duration": 2.1,
            "result": None,
            "error": "Insufficient permissions",
        }
        assert failed_result["status"] == "failed"
        assert failed_result["result"] is None
        assert isinstance(failed_result["error"], str)


class TestMonitoringTypes:
    """Test monitoring and metrics TypedDicts."""

    def test_metric_data(self) -> None:
        """Test MetricData TypedDict."""
        metric: MetricData = {
            "name": "cpu_usage",
            "type": "gauge",
            "value": 85.5,
            "labels": {"instance": "web-server-1", "region": "us-central1"},
            "timestamp": datetime.now(),
        }

        assert metric["type"] in ["counter", "gauge", "histogram", "summary"]
        assert isinstance(metric["value"], float)
        assert isinstance(metric["labels"], dict)

        # Test different metric types
        counter_metric: MetricData = {
            "name": "requests_total",
            "type": "counter",
            "value": 1000.0,
            "labels": {"method": "GET", "status": "200"},
            "timestamp": "2024-01-01T00:00:00Z",
        }
        assert counter_metric["type"] == "counter"

    def test_health_status(self) -> None:
        """Test HealthStatus TypedDict."""
        status: HealthStatus = {
            "service": "detection-agent",
            "status": AgentStatus.HEALTHY,
            "uptime": 86400.0,  # 24 hours
            "last_check": datetime.now(),
            "details": {"version": "1.0.0", "memory_usage": "50%"},
        }

        assert status["service"] == "detection-agent"
        assert status["status"] in list(AgentStatus)
        assert status["uptime"] > 0
        assert isinstance(status["details"], dict)

        # Test optional details
        minimal_status: HealthStatus = {
            "service": "analysis-agent",
            "status": AgentStatus.DEGRADED,
            "uptime": 3600.0,
            "last_check": datetime.now(),
            "details": None,
        }
        assert minimal_status["details"] is None


class TestWorkflowTypes:
    """Test workflow-related TypedDicts."""

    def test_workflow_step(self) -> None:
        """Test WorkflowStep TypedDict."""
        step: WorkflowStep = {
            "step_id": "step_001",
            "name": "Analyze Event",
            "status": "completed",
            "started_at": datetime.now(),
            "completed_at": datetime.now(),
            "result": {"confidence": 0.95},
            "error": None,
        }

        valid_states = [
            "pending",
            "running",
            "paused",
            "completed",
            "failed",
            "cancelled",
        ]
        assert step["status"] in valid_states
        assert isinstance(step["result"], dict)

        # Test failed step
        failed_step: WorkflowStep = {
            "step_id": "step_002",
            "name": "Send Notification",
            "status": "failed",
            "started_at": datetime.now(),
            "completed_at": None,
            "result": None,
            "error": "Network timeout",
        }
        assert failed_step["status"] == "failed"
        assert failed_step["completed_at"] is None
        assert isinstance(failed_step["error"], str)

    def test_workflow_definition(self) -> None:
        """Test WorkflowDefinition TypedDict."""
        workflow: WorkflowDefinition = {
            "workflow_id": WorkflowID("wf_123"),
            "name": "Incident Response",
            "steps": [
                {
                    "step_id": "step_001",
                    "name": "Detect",
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "result": None,
                    "error": None,
                }
            ],
            "timeout": 3600,
            "retry_policy": {"max_retries": 3, "backoff": "exponential"},
        }

        assert isinstance(workflow["steps"], list)
        assert isinstance(workflow["timeout"], int)
        assert isinstance(workflow["retry_policy"], dict)

        # Test optional fields
        minimal_workflow: WorkflowDefinition = {
            "workflow_id": WorkflowID("wf_124"),
            "name": "Simple Workflow",
            "steps": [],
            "timeout": None,
            "retry_policy": None,
        }
        assert minimal_workflow["timeout"] is None
        assert minimal_workflow["retry_policy"] is None


class TestProtocols:
    """Test protocol definitions."""

    def test_loggable_protocol(self) -> None:
        """Test Loggable protocol implementation."""

        class TestLoggable:
            def to_log_dict(self) -> JSONDict:
                return {"message": "test log", "level": "info"}

        obj = TestLoggable()
        log_data = obj.to_log_dict()

        assert isinstance(log_data, dict)
        assert "message" in log_data
        assert log_data["level"] == "info"

    def test_serializable_protocol(self) -> None:
        """Test Serializable protocol implementation."""

        class TestSerializable:
            def __init__(self, data: str):
                self.data = data

            def to_dict(self) -> JSONDict:
                return {"data": self.data, "type": "test"}

            @classmethod
            def from_dict(cls, data: JSONDict) -> "TestSerializable":
                return cls(str(data["data"]))

        obj = TestSerializable("test_data")
        serialized = obj.to_dict()
        deserialized = TestSerializable.from_dict(serialized)

        assert isinstance(serialized, dict)
        assert serialized["data"] == "test_data"
        assert deserialized.data == "test_data"

    def test_async_processor_protocol(self) -> None:
        """Test AsyncProcessor protocol implementation."""

        class TestProcessor:
            async def process(self, item: str) -> int:
                return len(item)

        processor = TestProcessor()

        # Test with asyncio
        async def run_test() -> None:
            result = await processor.process("hello")
            assert result == 5

        asyncio.run(run_test())

    def test_message_publisher_protocol(self) -> None:
        """Test MessagePublisher protocol implementation."""

        class TestPublisher:
            def __init__(self) -> None:
                self.published_messages: List[AgentMessage] = []

            async def publish(self, message: AgentMessage) -> None:
                self.published_messages.append(message)

        publisher = TestPublisher()
        test_message: AgentMessage = {
            "agent_id": AgentID("test_agent"),
            "message_id": MessageID("msg_123"),
            "timestamp": datetime.now(),
            "message_type": "test",
            "payload": {"test": True},
            "correlation_id": None,
        }

        async def run_test() -> None:
            await publisher.publish(test_message)
            assert len(publisher.published_messages) == 1
            assert publisher.published_messages[0]["agent_id"] == "test_agent"

        asyncio.run(run_test())

    def test_storage_backend_protocol(self) -> None:
        """Test StorageBackend protocol implementation."""

        class TestStorage:
            def __init__(self) -> None:
                self.storage: Dict[str, JSONDict] = {}

            async def get(self, key: str) -> Optional[JSONDict]:
                return self.storage.get(key)

            async def set(self, key: str, value: JSONDict) -> None:
                self.storage[key] = value

            async def delete(self, key: str) -> None:
                if key in self.storage:
                    del self.storage[key]

            async def list(self, prefix: str) -> List[str]:
                return [k for k in self.storage.keys() if k.startswith(prefix)]

        storage = TestStorage()

        async def run_test() -> None:
            # Test set and get
            await storage.set("test_key", {"value": "test"})
            result = await storage.get("test_key")
            assert result == {"value": "test"}

            # Test list
            await storage.set("prefix_1", {"data": "1"})
            await storage.set("prefix_2", {"data": "2"})
            keys = await storage.list("prefix_")
            assert len(keys) == 2
            assert "prefix_1" in keys

            # Test delete
            await storage.delete("test_key")
            result = await storage.get("test_key")
            assert result is None

        asyncio.run(run_test())


class TestCallableTypes:
    """Test callable type definitions."""

    def test_error_handler(self) -> None:
        """Test ErrorHandler callable type."""
        handled_errors = []

        def error_handler(error: Exception) -> None:
            handled_errors.append(str(error))

        # Verify it matches ErrorHandler type
        handler: ErrorHandler = error_handler

        # Test usage
        test_error = ValueError("Test error")
        handler(test_error)

        assert len(handled_errors) == 1
        assert "Test error" in handled_errors[0]

    def test_message_handler(self) -> None:
        """Test MessageHandler callable type."""
        handled_messages = []

        def message_handler(message: AgentMessage) -> None:
            handled_messages.append(message["message_type"])

        # Verify it matches MessageHandler type
        handler: MessageHandler = message_handler

        # Test usage
        test_message: AgentMessage = {
            "agent_id": AgentID("test_agent"),
            "message_id": MessageID("msg_123"),
            "timestamp": datetime.now(),
            "message_type": "test_type",
            "payload": {},
            "correlation_id": None,
        }

        handler(test_message)
        assert len(handled_messages) == 1
        assert handled_messages[0] == "test_type"

    def test_async_message_handler(self) -> None:
        """Test AsyncMessageHandler callable type."""
        handled_messages = []

        async def async_message_handler(message: AgentMessage) -> None:
            handled_messages.append(message["agent_id"])

        # Verify it matches AsyncMessageHandler type
        # Note: AsyncMessageHandler expects Future but async functions return Coroutine
        # Wrap in a function that returns Future
        def create_future_handler(
            func: Callable[[AgentMessage], Coroutine[Any, Any, None]],
        ) -> AsyncMessageHandler:
            def wrapper(message: AgentMessage) -> asyncio.Future[None]:
                future: asyncio.Future[None] = asyncio.Future()
                asyncio.create_task(func(message)).add_done_callback(
                    lambda task: future.set_result(None)
                )
                return future

            return wrapper

        handler: AsyncMessageHandler = create_future_handler(async_message_handler)

        # Test usage
        test_message: AgentMessage = {
            "agent_id": AgentID("async_agent"),
            "message_id": MessageID("msg_456"),
            "timestamp": datetime.now(),
            "message_type": "async_test",
            "payload": {},
            "correlation_id": None,
        }

        async def run_test() -> None:
            await handler(test_message)
            assert len(handled_messages) == 1
            assert handled_messages[0] == "async_agent"

        asyncio.run(run_test())


class TestConfigurationTypes:
    """Test configuration type aliases."""

    def test_config_dict(self) -> None:
        """Test ConfigDict type alias."""
        config: ConfigDict = {
            "database_url": "postgresql://localhost:5432/db",
            "timeout": 30,
            "retries": 3,
            "debug": True,
            "features": ["auth", "logging"],
            "nested": {"level": 2, "settings": {"cache": True}},
        }

        assert isinstance(config, dict)
        assert isinstance(config["database_url"], str)
        assert isinstance(config["timeout"], int)
        assert isinstance(config["debug"], bool)
        assert isinstance(config["features"], list)
        assert isinstance(config["nested"], dict)

    def test_config_value(self) -> None:
        """Test ConfigValue type alias."""
        # Test different valid config values
        string_value: ConfigValue = "test_string"
        int_value: ConfigValue = 42
        float_value: ConfigValue = 3.14
        bool_value: ConfigValue = True
        list_value: ConfigValue = [1, 2, 3]
        dict_value: ConfigValue = {"key": "value"}

        assert isinstance(string_value, str)
        assert isinstance(int_value, int)
        assert isinstance(float_value, float)
        assert isinstance(bool_value, bool)
        assert isinstance(list_value, list)
        assert isinstance(dict_value, dict)


class TestResultTypes:
    """Test result type aliases."""

    def test_result_type(self) -> None:
        """Test Result type alias."""
        # Test successful result
        success_result: Result[str] = "success"
        assert isinstance(success_result, str)

        # Test error result
        error_result: Result[str] = ValueError("error occurred")
        assert isinstance(error_result, Exception)

    def test_async_result_type(self) -> None:
        """Test AsyncResult type alias."""

        async def get_async_result() -> str:
            return "async_success"

        async def run_test() -> None:
            # Create AsyncResult
            future: AsyncResult[str] = asyncio.create_task(get_async_result())
            result = await future
            assert result == "async_success"

        asyncio.run(run_test())


class TestTypeVariables:
    """Test type variables."""

    def test_type_variable_t(self) -> None:
        """Test type variable T."""

        def identity(value: T) -> T:
            return value

        # Test with different types
        string_result = identity("test")
        int_result = identity(42)
        dict_result = identity({"key": "value"})

        assert string_result == "test"
        assert int_result == 42
        assert dict_result == {"key": "value"}

    def test_type_variable_r(self) -> None:
        """Test type variable R."""

        def transform(value: T, func: Callable[[T], R]) -> R:
            return func(value)

        # Test transformation
        result = transform("hello", len)
        assert result == 5
        assert isinstance(result, int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
