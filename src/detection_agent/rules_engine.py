"""
Detection Rules Engine for SentinelOps.

This module provides the rule management and evaluation engine for the detection agent.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from src.common.models import SeverityLevel


class RuleStatus(Enum):
    """Status of a detection rule."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    TESTING = "testing"
    DEPRECATED = "deprecated"


@dataclass
class DetectionRule:
    """Represents a single detection rule."""

    rule_id: str
    name: str
    description: str
    severity: SeverityLevel
    query: str
    status: RuleStatus = RuleStatus.DISABLED
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Rule configuration
    max_events_per_incident: int = 100
    correlation_window_minutes: int = 60

    # Statistics
    last_executed: Optional[datetime] = None
    execution_count: int = 0
    events_detected: int = 0
    incidents_created: int = 0

    def validate(self) -> List[str]:
        """
        Validate the detection rule.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate required fields
        if not self.rule_id:
            errors.append("rule_id is required")
        if not self.name:
            errors.append("name is required")
        if not self.description:
            errors.append("description is required")
        if not self.query:
            errors.append("query is required")

        # Validate query structure
        query_errors = self._validate_query()
        errors.extend(query_errors)

        # Validate correlation window
        if (
            self.correlation_window_minutes < 1
            or self.correlation_window_minutes > 1440
        ):
            errors.append(
                "correlation_window_minutes must be between 1 and 1440 (24 hours)"
            )

        # Validate max events
        if self.max_events_per_incident < 1 or self.max_events_per_incident > 10000:
            errors.append("max_events_per_incident must be between 1 and 10000")

        return errors

    def _validate_query(self) -> List[str]:
        """
        Validate the SQL query structure.

        Returns:
            List of query validation errors
        """
        errors = []

        # Check for required placeholders
        required_placeholders = [
            "{project_id}",
            "{dataset_id}",
            "{last_scan_time}",
            "{current_time}",
        ]
        for placeholder in required_placeholders:
            if placeholder not in self.query:
                errors.append(f"Query missing required placeholder: {placeholder}")
        # Check for dangerous operations
        dangerous_patterns = [
            r"\bDROP\b",
            r"\bDELETE\b",
            r"\bTRUNCATE\b",
            r"\bINSERT\b",
            r"\bUPDATE\b",
            r"\bCREATE\b",
            r"\bALTER\b",
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, self.query, re.IGNORECASE):
                errors.append(f"Query contains dangerous operation: {pattern}")

        # Check for required SELECT fields
        required_fields = ["timestamp"]
        query_lower = self.query.lower()
        for required_field in required_fields:
            if required_field not in query_lower:
                errors.append(f"Query must select '{required_field}' field")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert the rule to a dictionary representation."""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "query": self.query,
            "status": self.status.value,
            "tags": self.tags,
            "metadata": self.metadata,
            "max_events_per_incident": self.max_events_per_incident,
            "correlation_window_minutes": self.correlation_window_minutes,
            "last_executed": (
                self.last_executed.isoformat() if self.last_executed else None
            ),
            "execution_count": self.execution_count,
            "events_detected": self.events_detected,
            "incidents_created": self.incidents_created,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DetectionRule":
        """Create a DetectionRule from a dictionary."""
        return cls(
            rule_id=data["rule_id"],
            name=data["name"],
            description=data["description"],
            severity=SeverityLevel(data["severity"]),
            query=data["query"],
            status=RuleStatus(data.get("status", "disabled")),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            max_events_per_incident=data.get("max_events_per_incident", 100),
            correlation_window_minutes=data.get("correlation_window_minutes", 60),
            last_executed=(
                datetime.fromisoformat(data["last_executed"])
                if data.get("last_executed")
                else None
            ),
            execution_count=data.get("execution_count", 0),
            events_detected=data.get("events_detected", 0),
            incidents_created=data.get("incidents_created", 0),
        )


class RulesEngine:
    """Detection rules engine for managing and evaluating security detection rules."""

    def __init__(self) -> None:
        """Initialize the rules engine."""
        self.rules: Dict[str, DetectionRule] = {}
        self._load_builtin_rules()

    def _load_builtin_rules(self) -> None:
        """Load built-in detection rules."""
        # Import builtin rules here to avoid circular imports
        from .builtin_rules import BUILTIN_RULES
        from .firewall_logs_queries import FirewallLogsQueries
        from .vpc_flow_queries import VPCFlowLogsQueries

        # Add all built-in rules
        for rule in BUILTIN_RULES:
            try:
                self.add_rule(rule)
            except ValueError:
                # Rule might already exist
                pass

        # Add VPC flow log rules
        for rule in VPCFlowLogsQueries.create_detection_rules():
            try:
                self.add_rule(rule)
            except ValueError:
                pass

        # Add firewall log rules
        for rule in FirewallLogsQueries.create_detection_rules():
            try:
                self.add_rule(rule)
            except ValueError:
                pass

    def add_rule(self, rule: DetectionRule) -> None:
        """
        Add a detection rule to the engine.

        Args:
            rule: The detection rule to add

        Raises:
            ValueError: If the rule is invalid or already exists
        """
        # Validate the rule
        errors = rule.validate()
        if errors:
            raise ValueError(f"Invalid rule: {', '.join(errors)}")

        # Check for duplicate
        if rule.rule_id in self.rules:
            raise ValueError(f"Rule with ID '{rule.rule_id}' already exists")

        self.rules[rule.rule_id] = rule

    def get_rule(self, rule_id: str) -> Optional[DetectionRule]:
        """
        Get a detection rule by ID.

        Args:
            rule_id: The rule ID

        Returns:
            The detection rule or None if not found
        """
        return self.rules.get(rule_id)

    def get_enabled_rules(self) -> List[DetectionRule]:
        """
        Get all enabled detection rules.

        Returns:
            List of enabled rules
        """
        return [
            rule for rule in self.rules.values() if rule.status == RuleStatus.ENABLED
        ]

    def update_rule_status(self, rule_id: str, status: RuleStatus) -> None:
        """
        Update the status of a detection rule.

        Args:
            rule_id: The rule ID
            status: The new status

        Raises:
            ValueError: If the rule doesn't exist
        """
        if rule_id not in self.rules:
            raise ValueError(f"Rule with ID '{rule_id}' not found")

        self.rules[rule_id].status = status

    def enable_rule(self, rule_id: str) -> None:
        """Enable a detection rule."""
        self.update_rule_status(rule_id, RuleStatus.ENABLED)

    def disable_rule(self, rule_id: str) -> None:
        """Disable a detection rule."""
        self.update_rule_status(rule_id, RuleStatus.DISABLED)

    def update_rule_stats(
        self, rule_id: str, events_detected: int = 0, incidents_created: int = 0
    ) -> None:
        """
        Update rule execution statistics.

        Args:
            rule_id: The rule ID
            events_detected: Number of events detected in this execution
            incidents_created: Number of incidents created in this execution
        """
        if rule_id not in self.rules:
            return

        rule = self.rules[rule_id]
        rule.last_executed = datetime.now(timezone.utc)
        rule.execution_count += 1
        rule.events_detected += events_detected
        rule.incidents_created += incidents_created

    def get_rules_by_tag(self, tag: str) -> List[DetectionRule]:
        """
        Get all rules with a specific tag.

        Args:
            tag: The tag to search for

        Returns:
            List of rules with the specified tag
        """
        return [rule for rule in self.rules.values() if tag in rule.tags]

    def get_rules_by_severity(self, severity: SeverityLevel) -> List[DetectionRule]:
        """
        Get all rules with a specific severity level.

        Args:
            severity: The severity level

        Returns:
            List of rules with the specified severity
        """
        return [rule for rule in self.rules.values() if rule.severity == severity]

    def export_rules(self) -> Dict[str, Any]:
        """
        Export all rules as a dictionary.

        Returns:
            Dictionary containing all rules
        """
        return {
            "rules": [rule.to_dict() for rule in self.rules.values()],
            "total_rules": len(self.rules),
            "enabled_rules": len(self.get_enabled_rules()),
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def import_rules(self, rules_data: Dict[str, Any]) -> None:
        """
        Import rules from a dictionary.

        Args:
            rules_data: Dictionary containing rules to import
        """
        rules_list = rules_data.get("rules", [])

        for rule_data in rules_list:
            try:
                rule = DetectionRule.from_dict(rule_data)
                # Don't overwrite existing rules by default
                if rule.rule_id not in self.rules:
                    self.add_rule(rule)
            except (ValueError, AttributeError) as e:
                # Log error but continue importing other rules
                print(f"Error importing rule: {e}")
                continue
