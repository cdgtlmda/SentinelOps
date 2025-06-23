"""
Audit logging system for the orchestrator agent.
"""

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from google.cloud import firestore_v1 as firestore

if TYPE_CHECKING:
    pass


class AuditEventType(Enum):
    """Types of audit events."""

    INCIDENT_CREATED = "incident_created"
    INCIDENT_UPDATED = "incident_updated"
    STATE_TRANSITION = "state_transition"
    ANALYSIS_REQUESTED = "analysis_requested"
    ANALYSIS_COMPLETED = "analysis_completed"
    REMEDIATION_PROPOSED = "remediation_proposed"
    REMEDIATION_APPROVED = "remediation_approved"
    REMEDIATION_EXECUTED = "remediation_executed"
    REMEDIATION_COMPLETED = "remediation_completed"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    NOTIFICATION_SENT = "notification_sent"
    WORKFLOW_TIMEOUT = "workflow_timeout"
    WORKFLOW_FAILED = "workflow_failed"
    ERROR_OCCURRED = "error_occurred"
    CONFIGURATION_CHANGED = "configuration_changed"
    RETENTION_CLEANUP = "retention_cleanup"


class AuditLogger:
    """Handles audit logging for the orchestrator agent."""

    def __init__(self, agent_id: str, db: "firestore.Client"):
        """Initialize the audit logger."""
        self.agent_id = agent_id
        self.db = db
        self.audit_collection = db.collection("audit_logs")
        self.incident_audit_collection = db.collection("incident_audit_logs")

    async def log_event(
        self,
        event_type: AuditEventType,
        incident_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        actor: Optional[str] = None,
        severity: str = "info",
    ) -> str:
        """
        Log an audit event.

        Args:
            event_type: Type of the event
            incident_id: Related incident ID (if applicable)
            details: Additional event details
            actor: The entity that triggered the event
            severity: Event severity (info, warning, error, critical)

        Returns:
            The audit log entry ID
        """
        # Create audit entry
        audit_entry = {
            "event_id": self._generate_event_id(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type.value,
            "severity": severity,
            "agent_id": self.agent_id,
            "actor": actor or self.agent_id,
            "details": details or {},
        }

        if incident_id:
            audit_entry["incident_id"] = incident_id

        # Add hash for integrity
        audit_entry["hash"] = self._calculate_hash(audit_entry)

        try:
            # Store in main audit collection
            doc_ref = self.audit_collection.add(audit_entry)[1]

            # Also store in incident-specific audit if applicable
            if incident_id:
                self.incident_audit_collection.document(incident_id).collection(
                    "events"
                ).add(audit_entry)

            return str(doc_ref.id)

        except Exception as e:
            # Log to standard logging if audit storage fails
            print(f"Failed to store audit log: {e}")
            print(f"Audit entry: {json.dumps(audit_entry)}")
            raise

    async def log_state_transition(
        self, incident_id: str, from_state: str, to_state: str, reason: str, actor: str
    ) -> None:
        """Log a workflow state transition."""
        await self.log_event(
            AuditEventType.STATE_TRANSITION,
            incident_id=incident_id,
            details={
                "from_state": from_state,
                "to_state": to_state,
                "reason": reason,
                "transition_time": datetime.now(timezone.utc).isoformat(),
            },
            actor=actor,
        )

    async def log_remediation_action(
        self,
        incident_id: str,
        action: Dict[str, Any],
        status: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a remediation action execution."""
        event_type = AuditEventType.REMEDIATION_EXECUTED
        if status == "completed":
            event_type = AuditEventType.REMEDIATION_COMPLETED
        elif status == "failed":
            event_type = AuditEventType.WORKFLOW_FAILED

        await self.log_event(
            event_type,
            incident_id=incident_id,
            details={
                "action_type": action.get("action_type"),
                "target_resource": action.get("target_resource"),
                "status": status,
                "result": result,
                "execution_time": datetime.now(timezone.utc).isoformat(),
            },
            severity="error" if status == "failed" else "info",
        )

    async def log_approval_decision(
        self,
        incident_id: str,
        approved: bool,
        approver: str,
        reason: str,
        actions: List[Dict[str, Any]],
    ) -> None:
        """Log an approval decision."""
        event_type = (
            AuditEventType.APPROVAL_GRANTED
            if approved
            else AuditEventType.APPROVAL_DENIED
        )

        await self.log_event(
            event_type,
            incident_id=incident_id,
            details={
                "approver": approver,
                "reason": reason,
                "actions_count": len(actions),
                "action_types": [a.get("action_type") for a in actions],
                "decision_time": datetime.now(timezone.utc).isoformat(),
            },
            actor=approver,
        )

    async def log_error(
        self,
        error_message: str,
        error_type: str,
        incident_id: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> None:
        """Log an error event."""
        await self.log_event(
            AuditEventType.ERROR_OCCURRED,
            incident_id=incident_id,
            details={
                "error_message": error_message,
                "error_type": error_type,
                "stack_trace": stack_trace,
                "error_time": datetime.now(timezone.utc).isoformat(),
            },
            severity="error",
        )

    async def get_incident_audit_trail(
        self, incident_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get the complete audit trail for an incident."""
        try:
            # Query incident-specific audit logs
            query = (
                self.incident_audit_collection.document(incident_id)
                .collection("events")
                .order_by("timestamp", direction="DESCENDING")
                .limit(limit)
            )

            audit_trail = []
            for doc in query.stream():
                audit_trail.append(doc.to_dict())

            return audit_trail

        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            print(f"Failed to retrieve audit trail: {e}")
            return []

    async def verify_audit_integrity(self, incident_id: str) -> Dict[str, Any]:
        """Verify the integrity of audit logs for an incident."""
        audit_trail = await self.get_incident_audit_trail(incident_id, limit=1000)

        valid_entries = 0
        invalid_entries = 0

        for entry in audit_trail:
            stored_hash = entry.pop("hash", None)
            calculated_hash = self._calculate_hash(entry)

            if stored_hash == calculated_hash:
                valid_entries += 1
            else:
                invalid_entries += 1

        return {
            "total_entries": len(audit_trail),
            "valid_entries": valid_entries,
            "invalid_entries": invalid_entries,
            "integrity_valid": invalid_entries == 0,
        }

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        return f"{self.agent_id}_{timestamp}_{hash(timestamp) % 10000}"

    def _calculate_hash(self, entry: Dict[str, Any]) -> str:
        """Calculate a hash for audit entry integrity."""
        # Create a deterministic string representation
        entry_copy = entry.copy()
        entry_copy.pop("hash", None)  # Remove existing hash if present

        # Sort keys for consistent hashing
        entry_str = json.dumps(entry_copy, sort_keys=True)

        # Calculate SHA-256 hash
        return hashlib.sha256(entry_str.encode()).hexdigest()
