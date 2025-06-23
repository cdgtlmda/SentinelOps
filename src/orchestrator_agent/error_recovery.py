"""
Error handling and recovery mechanisms for the orchestrator agent.
"""

import asyncio
import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ErrorType(Enum):
    """Types of errors that can occur."""

    AGENT_COMMUNICATION = "agent_communication"
    FIRESTORE_ERROR = "firestore_error"
    WORKFLOW_ERROR = "workflow_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"
    EXECUTION_FAILURE = "execution_failure"
    RESOURCE_UNAVAILABLE = "resource_unavailable"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""

    RETRY = "retry"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    SKIP = "skip"
    ESCALATE = "escalate"
    FAIL_INCIDENT = "fail_incident"
    RESTART_WORKFLOW = "restart_workflow"
    RESTART_AGENT = "restart_agent"
    MANUAL_INTERVENTION = "manual_intervention"


class ErrorRecoveryManager:
    """Manages error recovery for the orchestrator agent."""

    def __init__(self, orchestrator_agent: Any):
        """Initialize the error recovery manager."""
        self.agent = orchestrator_agent
        self.error_history: List[Dict[str, Any]] = []
        self.recovery_attempts: Dict[str, int] = {}

        # Define recovery strategies for each error type
        self.recovery_strategies = {
            ErrorType.AGENT_COMMUNICATION: RecoveryStrategy.RETRY_WITH_BACKOFF,
            ErrorType.FIRESTORE_ERROR: RecoveryStrategy.RETRY_WITH_BACKOFF,
            ErrorType.WORKFLOW_ERROR: RecoveryStrategy.ESCALATE,
            ErrorType.TIMEOUT_ERROR: RecoveryStrategy.ESCALATE,
            ErrorType.VALIDATION_ERROR: RecoveryStrategy.SKIP,
            ErrorType.UNKNOWN_ERROR: RecoveryStrategy.ESCALATE,
            ErrorType.EXECUTION_FAILURE: RecoveryStrategy.RESTART_AGENT,
            ErrorType.RESOURCE_UNAVAILABLE: RecoveryStrategy.RETRY_WITH_BACKOFF,
        }

        # Circuit breaker state
        self.circuit_breaker_state: Dict[str, Dict[str, Any]] = {}

    async def handle_error(
        self,
        error: Exception,
        error_type: ErrorType,
        incident_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Handle an error and attempt recovery.

        Returns:
            True if error was recovered, False otherwise
        """
        # Log and record the error
        await self._log_error(error, error_type, incident_id, context)

        # Check if recovery is possible
        if not self._can_attempt_recovery(error_type):
            return False

        # Execute recovery strategy
        return await self._execute_recovery_strategy(
            error, error_type, incident_id, context
        )

    async def _log_error(
        self,
        error: Exception,
        error_type: ErrorType,
        incident_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Log error and create error record."""
        error_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_type": error_type.value,
            "error_message": str(error),
            "incident_id": incident_id,
            "context": context or {},
            "traceback": traceback.format_exc(),
        }

        self.error_history.append(error_record)

        # Log to audit trail
        if self.agent.audit_logger:
            await self.agent.audit_logger.log_error(
                str(error), error_type.value, incident_id, error_record["traceback"]
            )

        return error_record

    def _can_attempt_recovery(self, error_type: ErrorType) -> bool:
        """Check if recovery can be attempted."""
        # Check circuit breaker
        if self._is_circuit_open(error_type):
            self.agent.logger.warning(f"Circuit breaker open for {error_type.value}")
            return False
        return True

    async def _execute_recovery_strategy(
        self,
        error: Exception,
        error_type: ErrorType,
        incident_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> bool:
        """Execute the appropriate recovery strategy."""
        # Determine recovery strategy
        strategy = self.recovery_strategies.get(error_type, RecoveryStrategy.ESCALATE)

        # Track recovery attempt
        recovery_key = f"{error_type.value}:{incident_id or 'global'}"
        self.recovery_attempts[recovery_key] = (
            self.recovery_attempts.get(recovery_key, 0) + 1
        )

        # Strategy dispatch map
        strategy_handlers = {
            RecoveryStrategy.RETRY: self._retry_operation,
            RecoveryStrategy.RETRY_WITH_BACKOFF: self._retry_with_backoff,
            RecoveryStrategy.SKIP: self._skip_operation,
            RecoveryStrategy.ESCALATE: self._escalate_error,
            RecoveryStrategy.FAIL_INCIDENT: self._fail_incident,
            RecoveryStrategy.RESTART_WORKFLOW: self._restart_workflow,
            RecoveryStrategy.RESTART_AGENT: self._restart_agent,
            RecoveryStrategy.MANUAL_INTERVENTION: self._manual_intervention,
        }

        try:
            handler = strategy_handlers.get(strategy)
            if handler:
                return await handler(error, error_type, incident_id, context)
            else:
                self.agent.logger.error(f"Unknown recovery strategy: {strategy}")
                return False

        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            self.agent.logger.error(f"Recovery failed: {e}")
            return False

    async def _retry_operation(
        self,
        error: Exception,
        error_type: ErrorType,
        incident_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> bool:
        """Retry the failed operation immediately."""
        # Log the error for debugging
        self.agent.logger.debug(f"Retrying operation after error: {error}")
        max_retries = 3
        recovery_key = f"{error_type.value}:{incident_id or 'global'}"
        attempts = self.recovery_attempts.get(recovery_key, 0)

        if attempts > max_retries:
            self.agent.logger.error(f"Max retries exceeded for {recovery_key}")
            self._trip_circuit_breaker(error_type)
            return False

        # Retry the operation based on context
        if context and "operation" in context:
            operation = context["operation"]
            try:
                await operation()
                self.recovery_attempts[recovery_key] = 0  # Reset on success
                return True
            except (OSError, ConnectionError, RuntimeError, ValueError) as e:
                self.agent.logger.warning(f"Retry failed: {e}")
                return False

        return False

    async def _retry_with_backoff(
        self,
        error: Exception,
        error_type: ErrorType,
        incident_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> bool:
        """Retry with exponential backoff."""
        recovery_key = f"{error_type.value}:{incident_id or 'global'}"
        attempts = self.recovery_attempts.get(recovery_key, 0)

        if attempts > 5:
            self._trip_circuit_breaker(error_type)
            return False

        # Calculate backoff time
        backoff_seconds = min(2**attempts, 60)  # Max 60 seconds

        self.agent.logger.info(f"Retrying after {backoff_seconds}s backoff")
        await asyncio.sleep(backoff_seconds)

        return await self._retry_operation(error, error_type, incident_id, context)

    async def _skip_operation(
        self,
        error: Exception,
        error_type: ErrorType,
        incident_id: Optional[str],
        _context: Optional[Dict[str, Any]],
    ) -> bool:
        """Skip the failed operation and continue."""
        self.agent.logger.warning(
            f"Skipping operation due to {error_type.value}: {error}"
        )

        # Record skip in incident
        if incident_id:
            try:
                await self.agent.incidents_collection.document(incident_id).update(
                    {
                        "skipped_operations": self.agent.db.ArrayUnion(
                            [
                                {
                                    "error_type": error_type.value,
                                    "error_message": str(error),
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                }
                            ]
                        )
                    }
                )
            except (OSError, ConnectionError, RuntimeError, ValueError) as e:
                self.agent.logger.warning(f"Failed to record skip: {e}")

        return True  # Consider it "recovered" by skipping

    async def _escalate_error(
        self,
        error: Exception,
        error_type: ErrorType,
        incident_id: Optional[str],
        _context: Optional[Dict[str, Any]],
    ) -> bool:
        """Escalate the error to human operators."""
        self.agent.logger.error(f"Escalating {error_type.value} error")

        # Send urgent notification
        if incident_id:
            await self.agent._request_notification(
                incident_id,
                "error_escalation",
                f"URGENT: {error_type.value} error in incident {incident_id}: {error}",
                priority="urgent",
            )
        else:
            # Global error notification
            self.agent.logger.critical(f"Global error requiring attention: {error}")

        return False

    async def _fail_incident(
        self,
        error: Exception,
        error_type: ErrorType,
        incident_id: Optional[str],
        _context: Optional[Dict[str, Any]],
    ) -> bool:
        """Mark the incident as failed."""
        if not incident_id:
            return False

        self.agent.logger.error(
            f"Failing incident {incident_id} due to {error_type.value}"
        )

        # Update workflow state
        await self.agent.workflow_engine.transition(
            incident_id,
            self.agent.workflow_engine.WorkflowState.WORKFLOW_FAILED,
            self.agent.agent_id,
            {"failure_reason": str(error)},
        )

        # Update incident status
        await self.agent._update_incident_status(
            incident_id, self.agent.common.models.IncidentStatus.FAILED
        )

        return True

    async def _restart_workflow(
        self,
        _error: Exception,
        _error_type: ErrorType,
        incident_id: Optional[str],
        _context: Optional[Dict[str, Any]],
    ) -> bool:
        """Restart the workflow from a safe state."""
        if not incident_id:
            return False

        self.agent.logger.info(f"Restarting workflow for incident {incident_id}")

        # Determine safe restart point
        current_state = self.agent.workflow_engine.get_current_state(incident_id)

        # Reset to last stable state
        if current_state in [
            self.agent.workflow_engine.WorkflowState.ANALYSIS_IN_PROGRESS,
            self.agent.workflow_engine.WorkflowState.ANALYSIS_COMPLETE,
        ]:
            # Restart from analysis
            await self.agent._request_analysis(incident_id)
            return True
        elif current_state in [
            self.agent.workflow_engine.WorkflowState.REMEDIATION_IN_PROGRESS,
            self.agent.workflow_engine.WorkflowState.REMEDIATION_PROPOSED,
        ]:
            # Restart from remediation
            await self.agent._request_remediation(incident_id)
            return True

        return False

    def _is_circuit_open(self, error_type: ErrorType) -> bool:
        """Check if circuit breaker is open for an error type."""
        breaker = self.circuit_breaker_state.get(error_type.value, {})

        if breaker.get("state") == "open":
            # Check if enough time has passed to attempt reset
            opened_at = breaker.get("opened_at")
            if opened_at:
                elapsed = (
                    datetime.now(timezone.utc) - datetime.fromisoformat(opened_at)
                ).seconds
                if elapsed > 300:  # 5 minutes
                    # Reset to half-open
                    breaker["state"] = "half-open"
                    return False
            return True

        return False

    def _trip_circuit_breaker(self, error_type: ErrorType) -> None:
        """Trip the circuit breaker for an error type."""
        self.circuit_breaker_state[error_type.value] = {
            "state": "open",
            "opened_at": datetime.now(timezone.utc).isoformat(),
            "failure_count": self.circuit_breaker_state.get(error_type.value, {}).get(
                "failure_count", 0
            )
            + 1,
        }

        self.agent.logger.warning(f"Circuit breaker tripped for {error_type.value}")

    async def repair_incident(self, incident_id: str) -> bool:
        """
        Attempt to repair a stuck or failed incident.

        Returns:
            True if repair was successful
        """
        try:
            # Get incident data
            doc = await self.agent.incidents_collection.document(incident_id).get()
            if not doc.exists:
                return False

            current_state = self.agent.workflow_engine.get_current_state(incident_id)

            # Determine repair action based on state
            if (
                current_state
                == self.agent.workflow_engine.WorkflowState.WORKFLOW_FAILED
            ):
                # Check if we can restart
                history = self.agent.workflow_engine.get_workflow_history(incident_id)
                if history:
                    # Find last successful state
                    for step in reversed(history):
                        if step.state not in [
                            self.agent.workflow_engine.WorkflowState.WORKFLOW_FAILED,
                            self.agent.workflow_engine.WorkflowState.WORKFLOW_TIMEOUT,
                        ]:
                            # Reset to this state
                            self.agent.workflow_engine.current_workflows[
                                incident_id
                            ] = step.state
                            self.agent.logger.info(
                                f"Reset incident {incident_id} to {step.state.value}"
                            )
                            return True

            elif (
                current_state
                == self.agent.workflow_engine.WorkflowState.WORKFLOW_TIMEOUT
            ):
                # Restart from timeout state
                return await self._restart_workflow(
                    Exception("Workflow timeout"),
                    ErrorType.TIMEOUT_ERROR,
                    incident_id,
                    {},
                )

            return False

        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            self.agent.logger.error(f"Failed to repair incident {incident_id}: {e}")
            return False

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        stats: Dict[str, Any] = {
            "total_errors": len(self.error_history),
            "errors_by_type": {},
            "recovery_success_rate": 0,
            "circuit_breakers": self.circuit_breaker_state,
        }

        # Count errors by type
        for error in self.error_history:
            error_type = error.get("error_type", "unknown")
            stats["errors_by_type"][error_type] = (
                stats["errors_by_type"].get(error_type, 0) + 1
            )

        # Calculate recovery success rate
        total_attempts = sum(self.recovery_attempts.values())
        if total_attempts > 0:
            # Estimate based on current error count vs attempts
            stats["recovery_success_rate"] = max(
                0, 1 - (len(self.error_history) / total_attempts)
            )

        return stats

    async def _restart_agent(
        self,
        error: Exception,
        error_type: ErrorType,
        incident_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> bool:
        """Restart the agent."""
        self.agent.logger.warning(f"Restarting agent after {error_type.value}")

        try:
            # Attempt to restart the agent's core components
            if hasattr(self.agent, "restart"):
                await self.agent.restart()
                return True
            else:
                # Fallback to escalation if restart not available
                return await self._escalate_error(
                    error, error_type, incident_id, context
                )
        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            self.agent.logger.error(f"Agent restart failed: {e}")
            return False

    async def _manual_intervention(
        self,
        error: Exception,
        error_type: ErrorType,
        incident_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> bool:
        """Trigger manual intervention."""
        self.agent.logger.critical(
            f"Manual intervention required for {error_type.value}"
        )

        # Create manual intervention record
        intervention_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_type": error_type.value,
            "error_message": str(error),
            "incident_id": incident_id,
            "context": context or {},
            "intervention_required": True,
            "status": "pending_manual_intervention",
        }

        # Log to audit trail
        if self.agent.audit_logger:
            await self.agent.audit_logger.log_error(
                f"Manual intervention required: {error}",
                error_type.value,
                incident_id,
                str(intervention_record),
            )

        # Set incident status to manual intervention required
        if incident_id and hasattr(self.agent, "update_incident_status"):
            await self.agent.update_incident_status(
                incident_id, "manual_intervention_required"
            )

        return True  # Always return True as intervention was triggered
