"""
Workflow definitions and state machine for incident response orchestration.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class WorkflowState(Enum):
    """Workflow states for incident response."""

    INITIALIZED = "initialized"
    DETECTION_RECEIVED = "detection_received"
    ANALYSIS_REQUESTED = "analysis_requested"
    ANALYSIS_IN_PROGRESS = "analysis_in_progress"
    ANALYSIS_COMPLETE = "analysis_complete"
    REMEDIATION_REQUESTED = "remediation_requested"
    REMEDIATION_PROPOSED = "remediation_proposed"
    APPROVAL_PENDING = "approval_pending"
    REMEDIATION_APPROVED = "remediation_approved"
    REMEDIATION_IN_PROGRESS = "remediation_in_progress"
    REMEDIATION_COMPLETE = "remediation_complete"
    INCIDENT_RESOLVED = "incident_resolved"
    INCIDENT_CLOSED = "incident_closed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_TIMEOUT = "workflow_timeout"


@dataclass
class WorkflowTransition:
    """Defines a valid state transition in the workflow."""

    from_state: WorkflowState
    to_state: WorkflowState
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    action: Optional[Callable[[Dict[str, Any]], None]] = None
    description: str = ""


@dataclass
class WorkflowStep:
    """Represents a step in the incident workflow."""

    step_id: str
    state: WorkflowState
    timestamp: datetime
    actor_agent: str
    details: Dict[str, Any]
    error: Optional[str] = None


class IncidentWorkflow:
    """Manages the incident response workflow state machine."""

    def __init__(self) -> None:
        """Initialize the workflow with transitions."""
        self.transitions = self._define_transitions()
        self.current_workflows: Dict[str, WorkflowState] = {}
        self.workflow_history: Dict[str, List[WorkflowStep]] = {}

    def _define_transitions(self) -> List[WorkflowTransition]:
        """Define all valid workflow transitions."""
        return [
            # Detection to Analysis
            WorkflowTransition(
                from_state=WorkflowState.INITIALIZED,
                to_state=WorkflowState.DETECTION_RECEIVED,
                description="New incident detected",
            ),
            WorkflowTransition(
                from_state=WorkflowState.DETECTION_RECEIVED,
                to_state=WorkflowState.ANALYSIS_REQUESTED,
                description="Request incident analysis",
            ),
            WorkflowTransition(
                from_state=WorkflowState.ANALYSIS_REQUESTED,
                to_state=WorkflowState.ANALYSIS_IN_PROGRESS,
                description="Analysis agent started processing",
            ),
            WorkflowTransition(
                from_state=WorkflowState.ANALYSIS_IN_PROGRESS,
                to_state=WorkflowState.ANALYSIS_COMPLETE,
                condition=lambda ctx: ctx.get("analysis", {}).get("confidence_score", 0)
                > 0,
                description="Analysis completed successfully",
            ),
            # Analysis to Remediation
            WorkflowTransition(
                from_state=WorkflowState.ANALYSIS_COMPLETE,
                to_state=WorkflowState.REMEDIATION_REQUESTED,
                condition=lambda ctx: ctx.get("analysis", {}).get("confidence_score", 0)
                >= 0.7,
                description="High confidence analysis triggers remediation",
            ),
            WorkflowTransition(
                from_state=WorkflowState.REMEDIATION_REQUESTED,
                to_state=WorkflowState.REMEDIATION_PROPOSED,
                description="Remediation actions proposed",
            ),
            # Approval workflow
            WorkflowTransition(
                from_state=WorkflowState.REMEDIATION_PROPOSED,
                to_state=WorkflowState.APPROVAL_PENDING,
                condition=lambda ctx: ctx.get("require_approval", True),
                description="Human approval required",
            ),
            WorkflowTransition(
                from_state=WorkflowState.REMEDIATION_PROPOSED,
                to_state=WorkflowState.REMEDIATION_APPROVED,
                condition=lambda ctx: not ctx.get("require_approval", True),
                description="Auto-approved remediation",
            ),
            WorkflowTransition(
                from_state=WorkflowState.APPROVAL_PENDING,
                to_state=WorkflowState.REMEDIATION_APPROVED,
                description="Human approved remediation",
            ),
            # Remediation execution
            WorkflowTransition(
                from_state=WorkflowState.REMEDIATION_APPROVED,
                to_state=WorkflowState.REMEDIATION_IN_PROGRESS,
                description="Starting remediation execution",
            ),
            WorkflowTransition(
                from_state=WorkflowState.REMEDIATION_IN_PROGRESS,
                to_state=WorkflowState.REMEDIATION_COMPLETE,
                condition=lambda ctx: all(
                    action.get("status") == "completed"
                    for action in ctx.get("remediation_actions", [])
                ),
                description="All remediation actions completed",
            ),
            # Resolution
            WorkflowTransition(
                from_state=WorkflowState.REMEDIATION_COMPLETE,
                to_state=WorkflowState.INCIDENT_RESOLVED,
                description="Incident marked as resolved",
            ),
            WorkflowTransition(
                from_state=WorkflowState.INCIDENT_RESOLVED,
                to_state=WorkflowState.INCIDENT_CLOSED,
                description="Incident closed",
            ),
            # Error transitions
            WorkflowTransition(
                from_state=WorkflowState.ANALYSIS_IN_PROGRESS,
                to_state=WorkflowState.WORKFLOW_FAILED,
                condition=lambda ctx: ctx.get("error") is not None,
                description="Analysis failed",
            ),
            WorkflowTransition(
                from_state=WorkflowState.REMEDIATION_IN_PROGRESS,
                to_state=WorkflowState.WORKFLOW_FAILED,
                condition=lambda ctx: any(
                    action.get("status") == "failed"
                    for action in ctx.get("remediation_actions", [])
                ),
                description="Remediation failed",
            ),
        ]

    def can_transition(
        self, incident_id: str, to_state: WorkflowState, context: Dict[str, Any]
    ) -> bool:
        """Check if a transition is valid for the current state."""
        current_state = self.current_workflows.get(
            incident_id, WorkflowState.INITIALIZED
        )

        for transition in self.transitions:
            if (
                transition.from_state == current_state
                and transition.to_state == to_state
            ):
                # Check condition if present
                if transition.condition:
                    return transition.condition(context)
                return True

        return False

    def transition(
        self,
        incident_id: str,
        to_state: WorkflowState,
        actor_agent: str,
        context: Dict[str, Any],
    ) -> bool:
        """Execute a state transition."""
        if not self.can_transition(incident_id, to_state, context):
            return False

        current_state = self.current_workflows.get(
            incident_id, WorkflowState.INITIALIZED
        )

        # Find and execute the transition
        for transition in self.transitions:
            if (
                transition.from_state == current_state
                and transition.to_state == to_state
            ):
                # Execute action if present
                if transition.action:
                    transition.action(context)

                # Update state
                self.current_workflows[incident_id] = to_state

                # Record history
                step = WorkflowStep(
                    step_id=f"{incident_id}_{datetime.now(timezone.utc).timestamp()}",
                    state=to_state,
                    timestamp=datetime.now(timezone.utc),
                    actor_agent=actor_agent,
                    details={
                        "from_state": current_state.value,
                        "transition": transition.description,
                        "context": context,
                    },
                )

                if incident_id not in self.workflow_history:
                    self.workflow_history[incident_id] = []
                self.workflow_history[incident_id].append(step)

                return True

        return False

    def get_current_state(self, incident_id: str) -> WorkflowState:
        """Get the current workflow state for an incident."""
        return self.current_workflows.get(incident_id, WorkflowState.INITIALIZED)

    def get_workflow_history(self, incident_id: str) -> List[WorkflowStep]:
        """Get the workflow history for an incident."""
        return self.workflow_history.get(incident_id, [])

    def get_allowed_transitions(
        self, incident_id: str, context: Dict[str, Any]
    ) -> List[WorkflowState]:
        """Get all allowed transitions from the current state."""
        current_state = self.current_workflows.get(
            incident_id, WorkflowState.INITIALIZED
        )
        allowed = []

        for transition in self.transitions:
            if transition.from_state == current_state:
                if not transition.condition or transition.condition(context):
                    allowed.append(transition.to_state)

        return allowed

    def is_terminal_state(self, state: WorkflowState) -> bool:
        """Check if a state is terminal (no outgoing transitions)."""
        terminal_states = {
            WorkflowState.INCIDENT_CLOSED,
            WorkflowState.WORKFLOW_FAILED,
            WorkflowState.WORKFLOW_TIMEOUT,
        }
        return state in terminal_states
