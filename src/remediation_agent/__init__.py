"""
SentinelOps Remediation Agent.

This module provides automated remediation capabilities for security incidents
detected in Google Cloud Platform environments.
"""

from .action_registry import (
    ActionCategory,
    ActionDefinition,
    ActionRegistry,
    ActionRiskLevel,
    BaseRemediationAction,
)
from .adk_agent import RemediationAgent
from .execution_engine import (
    ActionQueue,
    ConcurrencyController,
    ExecutionMonitor,
    ExecutionPriority,
    RateLimiter,
    determine_action_priority,
)
from .integrations import (
    AnalysisAgentIntegration,
    CommunicationAgentIntegration,
    IntegrationManager,
    OrchestrationAgentIntegration,
)
from .performance import (
    BatchOperationManager,
    CacheManager,
    CloudMonitoringIntegration,
    PerformanceMetrics,
    ResourceOptimizer,
    performance_monitor,
)
from .safety_mechanisms import (
    ApprovalStatus,
    ApprovalWorkflow,
    ConflictType,
    RollbackManager,
    SafetyValidator,
)
from .security import (
    ActionAuthorizer,
    AuditLogger,
    AuthorizationLevel,
    CredentialManager,
    SecurityContext,
    generate_action_signature,
    verify_action_signature,
)

# from .testing_harness import (
#     ActionTestRunner,
#     DryRunSimulator,
#     MockGCPResponses,
#     create_test_action,
# )

__version__ = "1.0.0"

__all__ = [
    # Main agent
    "RemediationAgent",
    # Action registry
    "ActionRegistry",
    "ActionDefinition",
    "ActionRiskLevel",
    "ActionCategory",
    "BaseRemediationAction",
    # Execution engine
    "ActionQueue",
    "RateLimiter",
    "ConcurrencyController",
    "ExecutionMonitor",
    "ExecutionPriority",
    "determine_action_priority",
    # Safety mechanisms
    "SafetyValidator",
    "ApprovalWorkflow",
    "RollbackManager",
    "ApprovalStatus",
    "ConflictType",
    # Integrations
    "IntegrationManager",
    "AnalysisAgentIntegration",
    "OrchestrationAgentIntegration",
    "CommunicationAgentIntegration",
    # Testing - commented out as module doesn't exist
    # "MockGCPResponses",
    # "DryRunSimulator",
    # "ActionTestRunner",
    # "create_test_action",
    # Security
    "ActionAuthorizer",
    "AuditLogger",
    "CredentialManager",
    "SecurityContext",
    "AuthorizationLevel",
    "generate_action_signature",
    "verify_action_signature",
    # Performance
    "PerformanceMetrics",
    "CacheManager",
    "BatchOperationManager",
    "ResourceOptimizer",
    "CloudMonitoringIntegration",
    "performance_monitor",
]
