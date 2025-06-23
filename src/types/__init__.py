"""
Type definitions for SentinelOps.

This module contains TypeScript-style type definitions, type aliases,
protocols, and common type patterns used throughout the application.
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    NewType,
    Optional,
    Protocol,
    Set,
    Tuple,
    TypeAlias,
    TypedDict,
    TypeVar,
    Union,
)

# ============================================================================
# Basic Type Aliases
# ============================================================================

# JSON-compatible types
JsonType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONDict = Dict[str, JsonType]
JSONList = List[JsonType]

# Common data structures
StringDict = Dict[str, str]
StringList = List[str]
StringSet = Set[str]
StringTuple = Tuple[str, ...]

# Identifiers
AgentID = NewType("AgentID", str)
IncidentID = NewType("IncidentID", str)
EventID = NewType("EventID", str)
MessageID = NewType("MessageID", str)
WorkflowID = NewType("WorkflowID", str)
ResourceID = NewType("ResourceID", str)
ProjectID = NewType("ProjectID", str)
UserID = NewType("UserID", str)

# Timestamps
Timestamp = Union[datetime, str, float]
TimestampStr = NewType("TimestampStr", str)  # ISO format string

# ============================================================================
# Agent Types
# ============================================================================


class AgentType(str, Enum):
    """Types of agents in the system."""

    DETECTION = "detection"
    ANALYSIS = "analysis"
    REMEDIATION = "remediation"
    COMMUNICATION = "communication"
    ORCHESTRATOR = "orchestrator"


class AgentStatus(str, Enum):
    """Agent operational status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    STARTING = "starting"
    STOPPING = "stopping"


# Agent message types
AgentMessage = TypedDict(
    "AgentMessage",
    {
        "agent_id": AgentID,
        "message_id": MessageID,
        "timestamp": Timestamp,
        "message_type": str,
        "payload": JSONDict,
        "correlation_id": Optional[str],
    },
)


# ============================================================================
# Incident Types
# ============================================================================

SeverityLevel = Literal["low", "medium", "high", "critical"]
IncidentStatus = Literal["new", "analyzing", "remediating", "resolved", "closed"]
RemediationStatus = Literal["pending", "approved", "executing", "completed", "failed"]

IncidentDict = TypedDict(
    "IncidentDict",
    {
        "incident_id": IncidentID,
        "severity": SeverityLevel,
        "status": IncidentStatus,
        "created_at": Timestamp,
        "updated_at": Timestamp,
        "events": List[JSONDict],
        "analysis": Optional[JSONDict],
        "remediation": Optional[JSONDict],
    },
)


# ============================================================================
# GCP Types
# ============================================================================

GCPResource = TypedDict(
    "GCPResource",
    {
        "project_id": ProjectID,
        "resource_type": str,
        "resource_id": ResourceID,
        "location": Optional[str],
        "labels": Optional[StringDict],
        "metadata": Optional[JSONDict],
    },
)

BigQueryResult = TypedDict(
    "BigQueryResult",
    {
        "query": str,
        "rows": List[JSONDict],
        "total_rows": int,
        "bytes_processed": int,
        "execution_time": float,
    },
)

PubSubMessage = TypedDict(
    "PubSubMessage",
    {
        "data": Union[str, bytes],
        "attributes": StringDict,
        "message_id": str,
        "publish_time": Timestamp,
        "ordering_key": Optional[str],
    },
)


# ============================================================================
# Configuration Types
# ============================================================================

ConfigDict = Dict[str, Any]
ConfigValue = Union[str, int, float, bool, List[Any], Dict[str, Any]]

AgentConfig = TypedDict(
    "AgentConfig",
    {
        "agent_id": AgentID,
        "agent_type": AgentType,
        "enabled": bool,
        "config": ConfigDict,
        "resources": Optional[JSONDict],
        "environment": Optional[StringDict],
    },
)


# ============================================================================
# Callback and Handler Types
# ============================================================================

# Generic type variables
T = TypeVar("T")
R = TypeVar("R")
T_contra = TypeVar("T_contra", contravariant=True)
R_co = TypeVar("R_co", covariant=True)

# Callback types
ErrorHandler = Callable[[Exception], None]
MessageHandler = Callable[[AgentMessage], None]
AsyncMessageHandler = Callable[[AgentMessage], asyncio.Future[None]]

# Result types
Result = Union[T, Exception]
AsyncResult = asyncio.Future[Result[T]]


# ============================================================================
# Protocol Definitions
# ============================================================================
class Loggable(Protocol):
    """Protocol for objects that can be logged."""

    def to_log_dict(self) -> JSONDict:
        ...


class Serializable(Protocol):
    """Protocol for objects that can be serialized."""

    def to_dict(self) -> JSONDict:
        ...

    @classmethod
    def from_dict(cls, data: JSONDict) -> "Serializable":
        ...


class AsyncProcessor(Protocol[T_contra, R_co]):
    """Protocol for async processors."""

    async def process(self, item: T_contra) -> R_co:
        ...


class MessagePublisher(Protocol):
    """Protocol for message publishers."""

    async def publish(self, message: AgentMessage) -> None:
        ...


class StorageBackend(Protocol):
    """Protocol for storage backends."""

    async def get(self, key: str) -> Optional[JSONDict]:
        ...

    async def set(self, key: str, value: JSONDict) -> None:
        ...

    async def delete(self, key: str) -> None:
        ...

    async def list(self, prefix: str) -> List[str]:
        ...


# ============================================================================
# Notification Types
# ============================================================================

NotificationChannel = Literal["email", "slack", "sms", "webhook"]
NotificationPriority = Literal["low", "medium", "high", "critical"]

NotificationRequest = TypedDict(
    "NotificationRequest",
    {
        "channel": NotificationChannel,
        "priority": NotificationPriority,
        "recipient": str,
        "subject": Optional[str],
        "message": str,
        "metadata": Optional[JSONDict],
    },
)


# ============================================================================
# Analysis Types
# ============================================================================
AnalysisRequest = TypedDict(
    "AnalysisRequest",
    {
        "incident_id": IncidentID,
        "events": List[JSONDict],
        "context": Optional[JSONDict],
        "priority": SeverityLevel,
    },
)

AnalysisResult = TypedDict(
    "AnalysisResult",
    {
        "incident_id": IncidentID,
        "severity": SeverityLevel,
        "root_cause": str,
        "impact": str,
        "recommendations": List[str],
        "confidence": float,
        "metadata": Optional[JSONDict],
    },
)


# ============================================================================
# Remediation Types
# ============================================================================

RemediationAction = Literal[
    "isolate_instance",
    "block_ip",
    "revoke_credentials",
    "update_firewall",
    "restart_service",
    "scale_resources",
    "apply_patch",
]

RemediationRequest = TypedDict(
    "RemediationRequest",
    {
        "incident_id": IncidentID,
        "action": RemediationAction,
        "target": GCPResource,
        "parameters": Optional[JSONDict],
        "auto_approve": bool,
        "dry_run": bool,
    },
)

RemediationResult = TypedDict(
    "RemediationResult",
    {
        "incident_id": IncidentID,
        "action": RemediationAction,
        "status": RemediationStatus,
        "executed_at": Timestamp,
        "duration": float,
        "result": Optional[JSONDict],
        "error": Optional[str],
    },
)


# ============================================================================
# Monitoring and Metrics Types
# ============================================================================

MetricType = Literal["counter", "gauge", "histogram", "summary"]

MetricData = TypedDict(
    "MetricData",
    {
        "name": str,
        "type": MetricType,
        "value": float,
        "labels": StringDict,
        "timestamp": Timestamp,
    },
)

HealthStatus = TypedDict(
    "HealthStatus",
    {
        "service": str,
        "status": AgentStatus,
        "uptime": float,
        "last_check": Timestamp,
        "details": Optional[JSONDict],
    },
)


# ============================================================================
# Workflow Types
# ============================================================================

WorkflowState = Literal[
    "pending", "running", "paused", "completed", "failed", "cancelled"
]

WorkflowStep = TypedDict(
    "WorkflowStep",
    {
        "step_id": str,
        "name": str,
        "status": WorkflowState,
        "started_at": Optional[Timestamp],
        "completed_at": Optional[Timestamp],
        "result": Optional[JSONDict],
        "error": Optional[str],
    },
)

WorkflowDefinition = TypedDict(
    "WorkflowDefinition",
    {
        "workflow_id": WorkflowID,
        "name": str,
        "steps": List[WorkflowStep],
        "timeout": Optional[int],
        "retry_policy": Optional[JSONDict],
    },
)


# Export all public types
__all__ = [
    # Basic types
    "JsonType",
    "JSONDict",
    "JSONList",
    "StringDict",
    "StringList",
    "StringSet",
    # Identifiers
    "AgentID",
    "IncidentID",
    "EventID",
    "MessageID",
    "WorkflowID",
    "ResourceID",
    "ProjectID",
    "UserID",
    # Timestamps
    "Timestamp",
    "TimestampStr",
    # Enums
    "AgentType",
    "AgentStatus",
    # Literals
    "SeverityLevel",
    "IncidentStatus",
    "RemediationStatus",
    "NotificationChannel",
    "NotificationPriority",
    "RemediationAction",
    "MetricType",
    "WorkflowState",
    # TypedDicts
    "AgentMessage",
    "IncidentDict",
    "GCPResource",
    "BigQueryResult",
    "PubSubMessage",
    "AgentConfig",
    "NotificationRequest",
    "AnalysisRequest",
    "AnalysisResult",
    "RemediationRequest",
    "RemediationResult",
    "MetricData",
    "HealthStatus",
    "WorkflowStep",
    "WorkflowDefinition",
    # Type aliases
    "ConfigDict",
    "ConfigValue",
    "Result",
    "AsyncResult",
    # Callables
    "ErrorHandler",
    "MessageHandler",
    "AsyncMessageHandler",
    # Protocols
    "Loggable",
    "Serializable",
    "AsyncProcessor",
    "MessagePublisher",
    "StorageBackend",
    # Type variables
    "T",
    "R",
]
