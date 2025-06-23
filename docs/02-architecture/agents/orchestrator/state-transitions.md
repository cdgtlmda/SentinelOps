# Orchestration Agent State Transition Reference

## Overview

This document provides a detailed reference for all workflow states and valid transitions in the Orchestration Agent.

## Workflow States

### 1. INITIALIZED
- **Description**: Initial state when incident is created
- **Entry Conditions**: New incident created
- **Exit Transitions**: DETECTION_RECEIVED
- **Timeout**: None
- **Auto-Recovery**: N/A

### 2. DETECTION_RECEIVED
- **Description**: Incident has been received from detection agent
- **Entry Conditions**: Valid incident data received
- **Exit Transitions**: ANALYSIS_REQUESTED
- **Timeout**: 60 seconds
- **Auto-Recovery**: Retry incident creation

### 3. ANALYSIS_REQUESTED
- **Description**: Analysis has been requested from analysis agent
- **Entry Conditions**: Incident stored in Firestore
- **Exit Transitions**: ANALYSIS_IN_PROGRESS, WORKFLOW_TIMEOUT
- **Timeout**: 60 seconds
- **Auto-Recovery**: Retry analysis request

### 4. ANALYSIS_IN_PROGRESS
- **Description**: Analysis agent is processing the incident
- **Entry Conditions**: Analysis agent acknowledged request
- **Exit Transitions**: ANALYSIS_COMPLETE, WORKFLOW_TIMEOUT, WORKFLOW_FAILED
- **Timeout**: 300 seconds (configurable)
- **Auto-Recovery**: Escalate to human analyst

### 5. ANALYSIS_COMPLETE
- **Description**: Analysis has been completed
- **Entry Conditions**: Analysis results received with confidence > 0
- **Exit Transitions**: REMEDIATION_REQUESTED, INCIDENT_CLOSED
- **Timeout**: None
- **Auto-Recovery**: N/A

### 6. REMEDIATION_REQUESTED
- **Description**: Remediation has been requested
- **Entry Conditions**: Analysis confidence ≥ 0.7
- **Exit Transitions**: REMEDIATION_PROPOSED, WORKFLOW_TIMEOUT
- **Timeout**: 120 seconds
- **Auto-Recovery**: Skip to manual remediation

### 7. REMEDIATION_PROPOSED
- **Description**: Remediation actions have been proposed
- **Entry Conditions**: Valid remediation actions received
- **Exit Transitions**: APPROVAL_PENDING, REMEDIATION_APPROVED
- **Timeout**: None
- **Auto-Recovery**: N/A

### 8. APPROVAL_PENDING
- **Description**: Waiting for human approval
- **Entry Conditions**: Manual approval required
- **Exit Transitions**: REMEDIATION_APPROVED, WORKFLOW_TIMEOUT
- **Timeout**: 1800 seconds (configurable)
- **Auto-Recovery**: Auto-approve if configured

### 9. REMEDIATION_APPROVED
- **Description**: Remediation has been approved
- **Entry Conditions**: Approval received (manual or auto)
- **Exit Transitions**: REMEDIATION_IN_PROGRESS
- **Timeout**: 60 seconds
- **Auto-Recovery**: Retry execution request

### 10. REMEDIATION_IN_PROGRESS
- **Description**: Remediation actions are being executed
- **Entry Conditions**: Execution request sent
- **Exit Transitions**: REMEDIATION_COMPLETE, WORKFLOW_FAILED
- **Timeout**: 600 seconds (configurable)
- **Auto-Recovery**: Rollback if possible

### 11. REMEDIATION_COMPLETE
- **Description**: All remediation actions completed
- **Entry Conditions**: All actions reported success
- **Exit Transitions**: INCIDENT_RESOLVED
- **Timeout**: None
- **Auto-Recovery**: N/A

### 12. INCIDENT_RESOLVED
- **Description**: Incident has been resolved
- **Entry Conditions**: Remediation complete or manual resolution
- **Exit Transitions**: INCIDENT_CLOSED
- **Timeout**: None
- **Auto-Recovery**: N/A

### 13. INCIDENT_CLOSED
- **Description**: Terminal state - incident closed
- **Entry Conditions**: Resolution confirmed
- **Exit Transitions**: None (terminal)
- **Timeout**: None
- **Auto-Recovery**: N/A

### 14. WORKFLOW_FAILED
- **Description**: Terminal state - workflow failed
- **Entry Conditions**: Unrecoverable error occurred
- **Exit Transitions**: None (terminal)
- **Timeout**: None
- **Auto-Recovery**: Manual intervention required

### 15. WORKFLOW_TIMEOUT
- **Description**: Terminal state - workflow timed out
- **Entry Conditions**: State timeout exceeded
- **Exit Transitions**: None (terminal)
- **Timeout**: None
- **Auto-Recovery**: Manual intervention required

## State Transition Rules

### Valid Transitions

| From State | To State | Condition | Handler |
|------------|----------|-----------|---------|
| INITIALIZED | DETECTION_RECEIVED | Incident data valid | `_handle_new_incident` |
| DETECTION_RECEIVED | ANALYSIS_REQUESTED | Always | `_request_analysis` |
| ANALYSIS_REQUESTED | ANALYSIS_IN_PROGRESS | Agent acknowledged | `_handle_analysis_started` |
| ANALYSIS_IN_PROGRESS | ANALYSIS_COMPLETE | Results received | `_handle_analysis_complete` |
| ANALYSIS_COMPLETE | REMEDIATION_REQUESTED | Confidence ≥ 0.7 | `_request_remediation` |
| REMEDIATION_REQUESTED | REMEDIATION_PROPOSED | Actions received | `_handle_remediation_proposed` |
| REMEDIATION_PROPOSED | APPROVAL_PENDING | Manual approval required | `_request_approval` |
| REMEDIATION_PROPOSED | REMEDIATION_APPROVED | Auto-approved | `_approve_remediation` |
| APPROVAL_PENDING | REMEDIATION_APPROVED | Approval received | `_handle_approval` |
| REMEDIATION_APPROVED | REMEDIATION_IN_PROGRESS | Always | `_execute_remediation` |
| REMEDIATION_IN_PROGRESS | REMEDIATION_COMPLETE | All actions success | `_handle_remediation_complete` |
| REMEDIATION_COMPLETE | INCIDENT_RESOLVED | Always | `_resolve_incident` |
| INCIDENT_RESOLVED | INCIDENT_CLOSED | Cleanup complete | `_close_incident` |

### Error Transitions

| From State | To State | Condition | Handler |
|------------|----------|-----------|---------|
| Any non-terminal | WORKFLOW_FAILED | Unrecoverable error | `_handle_workflow_failure` |
| Any non-terminal | WORKFLOW_TIMEOUT | Timeout exceeded | `_handle_workflow_timeout` |

## Transition Guards

### Confidence Score Guard
```python
def confidence_guard(context: Dict[str, Any]) -> bool:
    """Check if confidence score meets threshold"""
    analysis = context.get("analysis", {})
    confidence = analysis.get("confidence_score", 0)
    return confidence >= 0.7
```

### Approval Required Guard
```python
def approval_required_guard(context: Dict[str, Any]) -> bool:
    """Check if manual approval is required"""
    if context.get("auto_approved"):
        return False
    return context.get("require_approval", True)
```

### Action Success Guard
```python
def all_actions_success_guard(context: Dict[str, Any]) -> bool:
    """Check if all remediation actions succeeded"""
    actions = context.get("remediation_actions", [])
    return all(
        action.get("status") == "completed" 
        for action in actions
    )
```

## State Timeout Configuration

```yaml
state_timeouts:
  ANALYSIS_REQUESTED: 60
  ANALYSIS_IN_PROGRESS: 300
  REMEDIATION_REQUESTED: 120
  APPROVAL_PENDING: 1800
  REMEDIATION_IN_PROGRESS: 600
  # Terminal states have no timeout
  INCIDENT_CLOSED: null
  WORKFLOW_FAILED: null
  WORKFLOW_TIMEOUT: null
```

## State History Tracking

Each state transition is recorded with:

```python
{
    "step_id": "INC-123_1234567890.123",
    "state": "ANALYSIS_COMPLETE",
    "timestamp": "2024-01-20T10:30:00Z",
    "actor_agent": "analysis-agent-001",
    "details": {
        "from_state": "ANALYSIS_IN_PROGRESS",
        "transition": "Analysis completed successfully",
        "context": {
            "confidence_score": 0.85,
            "analysis_duration": 45.2
        }
    }
}
```

## Parallel State Support

Some operations can occur in parallel:

```python
# Example: Parallel notifications during remediation
parallel_states = {
    "REMEDIATION_IN_PROGRESS": [
        "send_status_notification",
        "update_ticket_system",
        "log_to_siem"
    ]
}
```

## State Recovery Procedures

### 1. Recovery from ANALYSIS_IN_PROGRESS
```python
if state == WorkflowState.ANALYSIS_IN_PROGRESS:
    if time_in_state > timeout:
        # Option 1: Retry analysis
        await orchestrator._request_analysis(incident_id)
        
        # Option 2: Skip to manual remediation
        orchestrator.workflow_engine.transition(
            incident_id,
            WorkflowState.REMEDIATION_REQUESTED,
            "orchestrator",
            {"reason": "analysis_timeout"}
        )
```

### 2. Recovery from APPROVAL_PENDING
```python
if state == WorkflowState.APPROVAL_PENDING:
    if auto_approve_on_timeout:
        # Auto-approve after timeout
        await orchestrator._approve_remediation(
            incident_id, 
            actions,
            reason="timeout_auto_approval"
        )
    else:
        # Escalate to senior staff
        await orchestrator._escalate_approval(incident_id)
```

### 3. Recovery from REMEDIATION_IN_PROGRESS
```python
if state == WorkflowState.REMEDIATION_IN_PROGRESS:
    # Check partial completion
    completed_actions = get_completed_actions(incident_id)
    failed_actions = get_failed_actions(incident_id)
    
    if failed_actions and can_retry(failed_actions):
        # Retry failed actions only
        await orchestrator._retry_remediation(
            incident_id, 
            failed_actions
        )
    else:
        # Mark as partially complete
        orchestrator.workflow_engine.transition(
            incident_id,
            WorkflowState.WORKFLOW_FAILED,
            "orchestrator",
            {"partial_success": True}
        )
```

## Workflow Customization

### Adding Custom States

```python
# Define new state
class CustomWorkflowState(Enum):
    CUSTOM_VALIDATION = "custom_validation"

# Add transition
custom_transition = WorkflowTransition(
    from_state=WorkflowState.ANALYSIS_COMPLETE,
    to_state=CustomWorkflowState.CUSTOM_VALIDATION,
    condition=lambda ctx: ctx.get("requires_validation"),
    description="Custom validation required"
)

workflow_engine.add_transition(custom_transition)
```

### Custom Transition Actions

```python
def custom_action(context: Dict[str, Any]) -> None:
    """Execute custom action during transition"""
    incident_id = context.get("incident_id")
    # Perform custom logic
    send_webhook_notification(incident_id)
    update_external_system(incident_id)

# Add to transition
transition.action = custom_action
```

## Best Practices

1. **State Transition Atomicity**: Ensure state transitions are atomic
2. **Timeout Configuration**: Set appropriate timeouts based on historical data
3. **Guard Conditions**: Always validate context before transitions
4. **Error Handling**: Plan for failure scenarios in each state
5. **Audit Trail**: Log all state transitions for debugging
6. **Recovery Procedures**: Define clear recovery paths for each state

For more information, see the [Orchestration Agent Documentation](README.md).
