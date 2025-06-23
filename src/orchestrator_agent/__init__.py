"""
Orchestrator Agent Package

The orchestrator agent coordinates all other agents in the SentinelOps system,
managing the incident response workflow from detection to resolution.
"""

from src.orchestrator_agent.adk_agent import OrchestratorAgent
from src.orchestrator_agent.audit import AuditEventType, AuditLogger
from src.orchestrator_agent.auto_approval import ApprovalRule, AutoApprovalEngine
from src.orchestrator_agent.error_recovery import (
    ErrorRecoveryManager,
    ErrorType,
    RecoveryStrategy,
)
from src.orchestrator_agent.metrics import MetricsCollector, MetricType
from src.orchestrator_agent.performance import PerformanceOptimizer
from src.orchestrator_agent.workflow import (
    IncidentWorkflow,
    WorkflowState,
    WorkflowStep,
    WorkflowTransition,
)

__all__ = [
    "OrchestratorAgent",
    "IncidentWorkflow",
    "WorkflowState",
    "WorkflowTransition",
    "WorkflowStep",
    "AutoApprovalEngine",
    "ApprovalRule",
    "AuditLogger",
    "AuditEventType",
    "MetricsCollector",
    "MetricType",
    "ErrorRecoveryManager",
    "ErrorType",
    "RecoveryStrategy",
    "PerformanceOptimizer",
]

__version__ = "1.0.0"
