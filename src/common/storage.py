"""Storage layer for SentinelOps data persistence."""

import json
import logging
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from google.cloud.firestore import Client as FirestoreClient

from src.common.models import (
    AnalysisResult,
    Incident,
    IncidentStatus,
    SeverityLevel,
)
from src.detection_agent.rules_engine import DetectionRule, RuleStatus
from src.utils.datetime_utils import utcnow

logger = logging.getLogger(__name__)


class Storage:
    """Storage interface for SentinelOps data.

    This is a basic implementation using file storage.
    In production, this would be replaced with a proper database.
    """

    def __init__(self, base_path: Optional[str] = None):
        """Initialize storage with base path."""
        if base_path is None:
            base_path = tempfile.mkdtemp(prefix="sentinelops_")
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.incidents_path = self.base_path / "incidents"
        self.incidents_path.mkdir(exist_ok=True)

        self.analyses_path = self.base_path / "analyses"
        self.analyses_path.mkdir(exist_ok=True)

        self.rules_path = self.base_path / "rules"
        self.rules_path.mkdir(exist_ok=True)

        self.feedback_path = self.base_path / "feedback"
        self.feedback_path.mkdir(exist_ok=True)

        self.incident_history_path = self.base_path / "incident_history"
        self.incident_history_path.mkdir(exist_ok=True)

        self.archive_path = self.base_path / "archive"
        self.archive_path.mkdir(exist_ok=True)

        self.remediation_path = self.base_path / "remediation"
        self.remediation_path.mkdir(exist_ok=True)

        self.notifications_path = self.base_path / "notifications"
        self.notifications_path.mkdir(exist_ok=True)

        logger.info("Storage initialized at %s", self.base_path)

    async def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get an incident by ID."""
        try:
            file_path = self.incidents_path / f"{incident_id}.json"
            if not file_path.exists():
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Incident.from_dict(data)
        except (IOError, json.JSONDecodeError, ValueError) as e:
            logger.error("Failed to get incident %s: %s", incident_id, e)
            return None

    async def create_incident(self, incident: Incident) -> str:
        """Create a new incident."""
        try:
            incident_id = str(uuid4())
            incident.incident_id = incident_id

            file_path = self.incidents_path / f"{incident_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(incident.to_dict(), f, default=str)

            logger.info("Created incident %s", incident_id)
            return incident_id
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to create incident: %s", e)
            raise

    async def update_incident(self, incident_id: str, incident: Incident) -> bool:
        """Update an existing incident."""
        try:
            file_path = self.incidents_path / f"{incident_id}.json"
            if not file_path.exists():
                return False

            incident.updated_at = datetime.now(timezone.utc)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(incident.to_dict(), f, default=str)

            logger.info("Updated incident %s", incident_id)
            return True
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to update incident %s: %s", incident_id, e)
            return False

    async def get_analysis(self, incident_id: str) -> Optional[AnalysisResult]:
        """Get analysis result for an incident."""
        try:
            file_path = self.analyses_path / f"{incident_id}.json"
            if not file_path.exists():
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AnalysisResult.from_dict(data)
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to get analysis for %s: %s", incident_id, e)
            return None

    async def store_analysis(self, incident_id: str, analysis: AnalysisResult) -> bool:
        """Store analysis result for an incident."""
        try:
            file_path = self.analyses_path / f"{incident_id}.json"

            # Add metadata
            analysis_data = analysis.to_dict()
            analysis_data["id"] = incident_id
            analysis_data["created_at"] = datetime.now(timezone.utc).isoformat()

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(analysis_data, f, default=str)

            logger.info("Stored analysis for incident %s", incident_id)
            return True
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to store analysis for %s: %s", incident_id, e)
            return False

    async def get_recent_analyses(self, limit: int = 100) -> List[AnalysisResult]:
        """Get recent analysis results."""
        try:
            analyses = []
            files = sorted(
                self.analyses_path.glob("*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )[:limit]

            for file_path in files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        analyses.append(AnalysisResult.from_dict(data))
                except (IOError, ValueError, KeyError, AttributeError) as e:
                    logger.error("Failed to load analysis from %s: %s", file_path, e)
                    continue

            return analyses
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to get recent analyses: %s", e)
            return []

    async def store_feedback(
        self, feedback_type: str, feedback_data: Dict[str, Any]
    ) -> str:
        """Store feedback data."""
        try:
            feedback_id = str(uuid4())
            feedback_data["id"] = feedback_id
            feedback_data["type"] = feedback_type
            feedback_data["created_at"] = utcnow().isoformat()

            file_path = self.feedback_path / f"{feedback_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(feedback_data, f, default=str)

            logger.info("Stored %s feedback %s", feedback_type, feedback_id)
            return feedback_id
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to store feedback: %s", e)
            raise

    async def get_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[SeverityLevel] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Incident]:
        """Get incidents with optional filtering."""
        try:
            incidents = []
            files = sorted(
                self.incidents_path.glob("*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )

            for file_path in files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        incident = Incident.from_dict(data)

                        # Apply filters
                        if status and incident.status != status:
                            continue
                        if severity and incident.severity != severity:
                            continue

                        incidents.append(incident)
                except (IOError, ValueError, KeyError, AttributeError) as e:
                    logger.error("Failed to load incident from %s: %s", file_path, e)
                    continue

            # Apply pagination
            return incidents[offset : offset + limit]
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to get incidents: %s", e)
            return []

    async def delete_incident(self, incident_id: str) -> bool:
        """Delete an incident."""
        try:
            # Delete incident file
            incident_file = self.incidents_path / f"{incident_id}.json"
            if incident_file.exists():
                incident_file.unlink()

            # Delete associated analysis
            analysis_file = self.analyses_path / f"{incident_id}.json"
            if analysis_file.exists():
                analysis_file.unlink()

            logger.info("Deleted incident %s", incident_id)
            return True
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to delete incident %s: %s", incident_id, e)
            return False

    async def get_rule(self, rule_id: str) -> Optional[DetectionRule]:
        """Get a detection rule by ID."""
        try:
            file_path = self.rules_path / f"{rule_id}.json"
            if not file_path.exists():
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return DetectionRule.from_dict(data)
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to get rule %s: %s", rule_id, e)
            return None

    async def create_rule(self, rule: DetectionRule) -> str:
        """Create a new detection rule."""
        try:
            rule_id = str(uuid4())
            rule.rule_id = rule_id

            # Ensure directory exists
            self.rules_path.mkdir(parents=True, exist_ok=True)

            file_path = self.rules_path / f"{rule_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(rule.to_dict(), f, default=str)

            logger.info("Created rule %s", rule_id)
            return rule_id
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to create rule: %s", e)
            raise

    async def update_rule(self, rule_id: str, rule: DetectionRule) -> bool:
        """Update an existing rule."""
        try:
            file_path = self.rules_path / f"{rule_id}.json"
            if not file_path.exists():
                return False

            # Since DetectionRule is a dataclass, we update the rule_id
            rule.rule_id = rule_id
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(rule.to_dict(), f, default=str)

            logger.info("Updated rule %s", rule_id)
            return True
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to update rule %s: %s", rule_id, e)
            return False

    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a detection rule."""
        try:
            file_path = self.rules_path / f"{rule_id}.json"
            if file_path.exists():
                file_path.unlink()
                logger.info("Deleted rule %s", rule_id)
                return True
            return False
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to delete rule %s: %s", rule_id, e)
            return False

    async def get_rules(self, enabled: Optional[bool] = None) -> List[DetectionRule]:
        """Get all detection rules."""
        try:
            rules = []
            for file_path in self.rules_path.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        rule = DetectionRule.from_dict(data)

                        # Apply filter
                        if enabled is not None:
                            # Check if rule is enabled based on status
                            rule_enabled = rule.status == RuleStatus.ENABLED
                            if rule_enabled != enabled:
                                continue

                        rules.append(rule)
                except (IOError, ValueError, KeyError, AttributeError) as e:
                    logger.error("Failed to load rule from %s: %s", file_path, e)
                    continue

            return sorted(
                rules, key=lambda r: r.last_executed or datetime.min, reverse=True
            )
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to get rules: %s", e)
            return []

    async def count_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[SeverityLevel] = None,
    ) -> int:
        """Count incidents with optional filtering."""
        incidents = await self.get_incidents(
            status=status, severity=severity, limit=10000
        )
        return len(incidents)

    async def get_incident_stats(self) -> Dict[str, Any]:
        """Get incident statistics."""
        try:
            all_incidents = await self.get_incidents(limit=10000)

            # Count by status
            status_counts = {}
            for status in IncidentStatus:
                status_counts[status.value] = sum(
                    1 for i in all_incidents if i.status == status
                )

            # Count by severity
            severity_counts = {}
            for severity in SeverityLevel:
                severity_counts[severity.value] = sum(
                    1 for i in all_incidents if i.severity == severity
                )

            # Recent incidents (last 24 hours)
            recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_count = sum(1 for i in all_incidents if i.created_at > recent_cutoff)

            return {
                "total": len(all_incidents),
                "by_status": status_counts,
                "by_severity": severity_counts,
                "recent_24h": recent_count,
            }
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to get incident stats: %s", e)
            return {"total": 0, "by_status": {}, "by_severity": {}, "recent_24h": 0}

    async def get_remediation_actions(self) -> List[Any]:
        """Get all remediation actions."""
        try:
            actions = []
            remediation_path = self.base_path / "remediation_actions"
            remediation_path.mkdir(exist_ok=True)

            for file_path in remediation_path.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Convert dict to object-like structure
                        action = type("RemediationAction", (), data)()
                        for key, value in data.items():
                            setattr(action, key, value)
                        actions.append(action)
                except (IOError, ValueError, KeyError, AttributeError) as e:
                    logger.error("Failed to load action from %s: %s", file_path, e)
                    continue

            return actions
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to get remediation actions: %s", e)
            return []

    async def get_remediation_action(self, action_id: str) -> Optional[Any]:
        """Get a specific remediation action."""
        try:
            remediation_path = self.base_path / "remediation_actions"
            file_path = remediation_path / f"{action_id}.json"

            if not file_path.exists():
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert dict to object-like structure
                action = type("RemediationAction", (), data)()
                for key, value in data.items():
                    setattr(action, key, value)
                return action
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to get remediation action %s: %s", action_id, e)
            return None

    async def create_remediation_execution(
        self,
        action_id: str,
        executed_by: str,
        parameters: Dict[str, Any],
        dry_run: bool,
    ) -> str:
        """Create a remediation execution record."""
        try:
            execution_id = str(uuid4())
            executions_path = self.base_path / "remediation_executions"
            executions_path.mkdir(exist_ok=True)

            execution_data = {
                "id": execution_id,
                "action_id": action_id,
                "executed_by": executed_by,
                "parameters": parameters,
                "dry_run": dry_run,
                "status": "pending",
                "created_at": utcnow().isoformat(),
            }

            file_path = executions_path / f"{execution_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(execution_data, f, default=str)

            logger.info("Created remediation execution %s", execution_id)
            return execution_id
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to create remediation execution: %s", e)
            raise

    async def validate_approval_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate an approval token."""
        try:
            approvals_path = self.base_path / "remediation_approvals"
            approvals_path.mkdir(exist_ok=True)

            # Simple token validation - in production would be more sophisticated
            for file_path in approvals_path.glob("*.json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    approval: Dict[str, Any] = json.load(f)
                    if (
                        approval.get("token") == token
                        and approval.get("status") == "valid"
                    ):
                        return approval

            return None
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to validate approval token: %s", e)
            return None

    async def get_remediation_history(  # noqa: C901
        self,
        incident_id: Optional[str] = None,
        action_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Any]:
        """Get remediation execution history."""
        try:
            executions = []
            executions_path = self.base_path / "remediation_executions"
            executions_path.mkdir(exist_ok=True)

            for file_path in sorted(
                executions_path.glob("*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            ):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                        # Apply filters
                        if incident_id and data.get("incident_id") != incident_id:
                            continue
                        if action_type and data.get("action_type") != action_type:
                            continue
                        if status and data.get("status") != status:
                            continue

                        # Date filtering
                        created_at = datetime.fromisoformat(
                            data.get("created_at", utcnow().isoformat())
                        )
                        if start_date and created_at < start_date:
                            continue
                        if end_date and created_at > end_date:
                            continue

                        # Convert to object-like structure
                        execution = type("RemediationExecution", (), data)()
                        for key, value in data.items():
                            setattr(execution, key, value)
                        executions.append(execution)
                except (IOError, ValueError, KeyError, AttributeError) as e:
                    logger.error("Failed to load execution from %s: %s", file_path, e)
                    continue

            # Apply pagination
            return executions[offset : offset + limit]
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to get remediation history: %s", e)
            return []

    async def count_remediation_history(
        self,
        incident_id: Optional[str] = None,
        action_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count remediation executions matching criteria."""
        history = await self.get_remediation_history(
            incident_id=incident_id,
            action_type=action_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=10000,
        )
        return len(history)

    async def get_remediation_execution(self, execution_id: str) -> Optional[Any]:
        """Get a specific remediation execution."""
        try:
            executions_path = self.base_path / "remediation_executions"
            file_path = executions_path / f"{execution_id}.json"

            if not file_path.exists():
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert dict to object-like structure
                execution = type("RemediationExecution", (), data)()
                for key, value in data.items():
                    setattr(execution, key, value)
                return execution
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to get remediation execution %s: %s", execution_id, e)
            return None

    async def create_remediation_rollback(
        self, execution_id: str, reason: str, initiated_by: str
    ) -> str:
        """Create a remediation rollback record."""
        try:
            rollback_id = str(uuid4())
            rollbacks_path = self.base_path / "remediation_rollbacks"
            rollbacks_path.mkdir(exist_ok=True)

            rollback_data = {
                "id": rollback_id,
                "execution_id": execution_id,
                "reason": reason,
                "initiated_by": initiated_by,
                "status": "pending",
                "created_at": utcnow().isoformat(),
            }

            file_path = rollbacks_path / f"{rollback_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(rollback_data, f, default=str)

            logger.info("Created remediation rollback %s", rollback_id)
            return rollback_id
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to create remediation rollback: %s", e)
            raise

    async def get_approval_queue(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100,
    ) -> List[Any]:
        """Get remediation actions pending approval."""
        try:
            approvals = []
            approvals_path = self.base_path / "remediation_approvals"
            approvals_path.mkdir(exist_ok=True)

            for file_path in sorted(
                approvals_path.glob("*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )[:limit]:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                        # Apply filters
                        if status and data.get("status") != status:
                            continue
                        if priority and data.get("priority") != priority:
                            continue

                        # Convert to object-like structure
                        approval = type("ApprovalItem", (), data)()
                        for key, value in data.items():
                            setattr(approval, key, value)
                        approvals.append(approval)
                except (OSError, json.JSONDecodeError, KeyError) as e:
                    logger.error("Failed to load approval from %s: %s", file_path, e)
                    continue

            return approvals
        except (OSError, KeyError) as e:
            logger.error("Failed to get approval queue: %s", e)
            return []

    async def update_remediation_execution(
        self, execution_id: str, **kwargs: Any
    ) -> bool:
        """Update a remediation execution."""
        try:
            executions_path = self.base_path / "remediation_executions"
            file_path = executions_path / f"{execution_id}.json"

            if not file_path.exists():
                return False

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Update fields
            data.update(kwargs)
            data["updated_at"] = utcnow().isoformat()

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, default=str)

            logger.info("Updated remediation execution %s", execution_id)
            return True
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to update remediation execution: %s", e)
            return False

    async def update_remediation_rollback(
        self, rollback_id: str, **kwargs: Any
    ) -> bool:
        """Update a remediation rollback."""
        try:
            rollbacks_path = self.base_path / "remediation_rollbacks"
            file_path = rollbacks_path / f"{rollback_id}.json"

            if not file_path.exists():
                return False

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Update fields
            data.update(kwargs)
            data["updated_at"] = utcnow().isoformat()

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, default=str)

            logger.info("Updated remediation rollback %s", rollback_id)
            return True
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to update remediation rollback: %s", e)
            return False

    async def get_notification_channels(self) -> List[Any]:
        """Get all notification channels."""
        try:
            channels = []
            channels_path = self.base_path / "notification_channels"
            channels_path.mkdir(exist_ok=True)

            for file_path in channels_path.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Convert dict to object-like structure
                        channel = type("NotificationChannel", (), data)()
                        for key, value in data.items():
                            setattr(channel, key, value)
                        channels.append(channel)
                except (OSError, json.JSONDecodeError, KeyError) as e:
                    logger.error("Failed to load channel from %s: %s", file_path, e)
                    continue

            return channels
        except (OSError, KeyError) as e:
            logger.error("Failed to get notification channels: %s", e)
            return []

    async def get_notification_channel(self, channel_id: str) -> Optional[Any]:
        """Get a specific notification channel."""
        try:
            channels_path = self.base_path / "notification_channels"
            file_path = channels_path / f"{channel_id}.json"

            if not file_path.exists():
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert dict to object-like structure
                channel = type("NotificationChannel", (), data)()
                for key, value in data.items():
                    setattr(channel, key, value)
                return channel
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to get notification channel %s: %s", channel_id, e)
            return None

    async def create_notification(
        self,
        incident_id: Optional[str],
        notification_type: str,
        subject: str,
        message: str,
        channels: List[str],
        priority: str,
        metadata: Dict[str, Any],
        created_by: str,
    ) -> str:
        """Create a notification record."""
        try:
            notification_id = str(uuid4())
            notifications_path = self.base_path / "notifications"
            notifications_path.mkdir(exist_ok=True)

            notification_data = {
                "id": notification_id,
                "incident_id": incident_id,
                "notification_type": notification_type,
                "subject": subject,
                "message": message,
                "channels": channels,
                "priority": priority,
                "metadata": metadata,
                "created_by": created_by,
                "status": "pending",
                "created_at": utcnow().isoformat(),
            }

            file_path = notifications_path / f"{notification_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(notification_data, f, default=str)

            logger.info("Created notification %s", notification_id)
            return notification_id
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to create notification: %s", e)
            raise

    async def update_notification(self, notification_id: str, **kwargs: Any) -> bool:
        """Update a notification."""
        try:
            notifications_path = self.base_path / "notifications"
            file_path = notifications_path / f"{notification_id}.json"

            if not file_path.exists():
                return False

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Update fields
            data.update(kwargs)
            data["updated_at"] = utcnow().isoformat()

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, default=str)

            logger.info("Updated notification %s", notification_id)
            return True
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to update notification: %s", e)
            return False

    async def get_notification_preferences(self, user_id: str) -> Optional[Any]:
        """Get notification preferences for a user."""
        try:
            preferences_path = self.base_path / "notification_preferences"
            preferences_path.mkdir(exist_ok=True)
            file_path = preferences_path / f"{user_id}.json"

            if not file_path.exists():
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert dict to object-like structure
                preferences = type("NotificationPreferences", (), data)()
                for key, value in data.items():
                    setattr(preferences, key, value)
                return preferences
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.error(
                "Failed to get notification preferences for %s: %s", user_id, e
            )
            return None

    async def update_notification_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> bool:
        """Update notification preferences for a user."""
        try:
            preferences_path = self.base_path / "notification_preferences"
            preferences_path.mkdir(exist_ok=True)
            file_path = preferences_path / f"{user_id}.json"

            # Ensure user_id is in preferences
            preferences["user_id"] = user_id

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(preferences, f, default=str)

            logger.info("Updated notification preferences for %s", user_id)
            return True
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to update notification preferences: %s", e)
            return False

    async def store_incident_history(
        self, incident_id: str, history_entry: Dict[str, Any]
    ) -> bool:
        """Store incident history entry."""
        try:
            file_path = self.incident_history_path / f"{incident_id}.json"

            # Load existing history or create new
            history = []
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    history = json.load(f)

            # Add new entry
            history.append(history_entry)

            # Save updated history
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(history, f, default=str)

            return True
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to store incident history: %s", e)
            return False

    async def get_incident_history(self, incident_id: str) -> List[Dict[str, Any]]:
        """Get incident history."""
        try:
            file_path = self.incident_history_path / f"{incident_id}.json"
            if not file_path.exists():
                return []

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to get incident history: %s", e)
            return []

    async def get_feedback(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get feedback for an incident."""
        try:
            file_path = self.feedback_path / f"{incident_id}.json"
            if not file_path.exists():
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else None
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to get feedback: %s", e)
            return None

    async def archive_incident(self, incident_id: str) -> bool:
        """Archive an incident."""
        try:
            active_path = self.incidents_path / f"{incident_id}.json"
            if not active_path.exists():
                return False

            # Create archive directory for incidents
            archive_incidents_path = self.archive_path / "incidents"
            archive_incidents_path.mkdir(exist_ok=True)

            archive_path = archive_incidents_path / f"{incident_id}.json"
            if archive_path.exists():
                return False  # Already archived

            # Move file to archive
            active_path.rename(archive_path)
            return True
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to archive incident: %s", e)
            return False

    async def get_archived_incident(self, incident_id: str) -> Optional[Incident]:
        """Get an archived incident."""
        try:
            archive_path = self.archive_path / "incidents" / f"{incident_id}.json"
            if not archive_path.exists():
                return None

            with open(archive_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Incident.from_dict(data)
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to get archived incident: %s", e)
            return None

    async def list_archived_incidents(self) -> List[Incident]:
        """List all archived incidents."""
        try:
            incidents = []
            archive_incidents_path = self.archive_path / "incidents"
            if not archive_incidents_path.exists():
                return []

            for file_path in archive_incidents_path.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        incidents.append(Incident.from_dict(data))
                except (IOError, ValueError, KeyError, AttributeError) as e:
                    logger.error(
                        "Failed to load archived incident from %s: %s", file_path, e
                    )
                    continue

            return incidents
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to list archived incidents: %s", e)
            return []

    async def list_rules(self) -> List[DetectionRule]:
        """List all detection rules."""
        try:
            rules = []
            for file_path in self.rules_path.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # DetectionRule.from_dict needs to be implemented
                        rules.append(DetectionRule(**data))
                except (IOError, ValueError, KeyError, AttributeError) as e:
                    logger.error("Failed to load rule from %s: %s", file_path, e)
                    continue

            return rules
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to list rules: %s", e)
            return []

    async def store_remediation_action(self, action: Dict[str, Any]) -> str:
        """Store a remediation action."""
        try:
            action_id = str(uuid4())
            action["action_id"] = action_id
            action["created_at"] = datetime.now(timezone.utc).isoformat()

            file_path = self.remediation_path / f"{action_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(action, f, default=str)

            return action_id
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to store remediation action: %s", e)
            raise

    async def list_remediation_actions(self) -> List[Dict[str, Any]]:
        """List all remediation actions."""
        try:
            actions = []
            for file_path in self.remediation_path.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        actions.append(json.load(f))
                except (IOError, ValueError, KeyError, AttributeError) as e:
                    logger.error(
                        "Failed to load remediation action from %s: %s", file_path, e
                    )
                    continue

            return actions
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to list remediation actions: %s", e)
            return []

    async def list_remediation_executions(self) -> List[Dict[str, Any]]:
        """List all remediation executions."""
        try:
            executions = []
            executions_path = self.remediation_path / "executions"
            if not executions_path.exists():
                return []

            for file_path in executions_path.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        executions.append(json.load(f))
                except (IOError, ValueError, KeyError, AttributeError) as e:
                    logger.error(
                        "Failed to load remediation execution from %s: %s", file_path, e
                    )
                    continue

            return executions
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to list remediation executions: %s", e)
            return []

    async def store_notification_channel(self, channel: Dict[str, Any]) -> str:
        """Store a notification channel."""
        try:
            channel_id = str(uuid4())
            channel["channel_id"] = channel_id
            channel["created_at"] = datetime.now(timezone.utc).isoformat()

            channels_path = self.notifications_path / "channels"
            channels_path.mkdir(exist_ok=True)

            file_path = channels_path / f"{channel_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(channel, f, default=str)

            return channel_id
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to store notification channel: %s", e)
            raise

    async def list_notification_channels(self) -> List[Dict[str, Any]]:
        """List all notification channels."""
        try:
            channels = []
            channels_path = self.notifications_path / "channels"
            if not channels_path.exists():
                return []

            for file_path in channels_path.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        channels.append(json.load(f))
                except (IOError, ValueError, KeyError, AttributeError) as e:
                    logger.error(
                        "Failed to load notification channel from %s: %s", file_path, e
                    )
                    continue

            return channels
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to list notification channels: %s", e)
            return []

    async def get_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Get a notification by ID."""
        try:
            file_path = self.notifications_path / f"{notification_id}.json"
            if not file_path.exists():
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else None
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to get notification: %s", e)
            return None

    async def list_notifications(self) -> List[Dict[str, Any]]:
        """List all notifications."""
        try:
            notifications = []
            for file_path in self.notifications_path.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        notifications.append(json.load(f))
                except (IOError, ValueError, KeyError, AttributeError) as e:
                    logger.error(
                        "Failed to load notification from %s: %s", file_path, e
                    )
                    continue

            return notifications
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to list notifications: %s", e)
            return []

    async def list_incidents(self) -> List[Incident]:
        """List all incidents."""
        try:
            incidents = []
            for file_path in self.incidents_path.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        incidents.append(Incident.from_dict(data))
                except (IOError, ValueError, KeyError, AttributeError) as e:
                    logger.error("Failed to load incident from %s: %s", file_path, e)
                    continue

            return incidents
        except (IOError, ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to list incidents: %s", e)
            return []


def get_firestore_client() -> FirestoreClient:
    """Get Firestore client instance."""
    return FirestoreClient()
