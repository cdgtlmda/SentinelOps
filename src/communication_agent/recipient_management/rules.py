"""
Notification rules engine for intelligent message routing.

Implements severity-based routing, time-based rules, incident type routing,
and deduplication logic.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Set

from src.communication_agent.types import NotificationPriority
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RuleConditionType(str, Enum):
    """Types of rule conditions."""

    SEVERITY = "severity"
    TIME = "time"
    INCIDENT_TYPE = "incident_type"
    MESSAGE_TYPE = "message_type"
    TAG = "tag"
    RESOURCE = "resource"
    FREQUENCY = "frequency"
    REGEX = "regex"
    CUSTOM = "custom"


class RuleAction(str, Enum):
    """Actions that can be taken by rules."""

    ROUTE = "route"
    ESCALATE = "escalate"
    SUPPRESS = "suppress"
    MODIFY_PRIORITY = "modify_priority"
    ADD_RECIPIENTS = "add_recipients"
    REMOVE_RECIPIENTS = "remove_recipients"
    SET_CHANNEL = "set_channel"
    DELAY = "delay"


@dataclass
class RuleCondition:
    """A condition for a notification rule."""

    type: RuleConditionType
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, not_in, regex
    value: Any

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the condition against a context."""
        field_value = context.get(self.field)

        if field_value is None:
            return False

        try:
            return self._apply_operator(field_value)
        except (ValueError, AttributeError) as e:
            logger.error(
                "Error evaluating condition: %s",
                e,
                extra={
                    "type": self.type.value,
                    "field": self.field,
                    "operator": self.operator,
                },
                exc_info=True,
            )
            return False

    def _apply_operator(self, field_value: Any) -> bool:
        """Apply the operator to compare field value with condition value."""
        operator_map: Dict[str, Callable[[Any, Any], bool]] = {
            "eq": lambda fv, v: bool(fv == v),
            "ne": lambda fv, v: bool(fv != v),
            "gt": lambda fv, v: bool(fv > v),
            "lt": lambda fv, v: bool(fv < v),
            "gte": lambda fv, v: bool(fv >= v),
            "lte": lambda fv, v: bool(fv <= v),
            "in": lambda fv, v: fv in v,
            "not_in": lambda fv, v: fv not in v,
            "regex": lambda fv, v: bool(re.match(v, str(fv))),
        }

        if self.operator not in operator_map:
            logger.warning("Unknown operator: %s", self.operator)
            return False

        return operator_map[self.operator](field_value, self.value)


@dataclass
class NotificationRule:
    """A rule for notification routing and processing."""

    id: str
    name: str
    description: str
    enabled: bool = True
    priority: int = 100  # Higher priority rules execute first
    conditions: List[RuleCondition] = field(default_factory=list)
    condition_logic: str = "all"  # all, any, custom
    actions: List[Dict[str, Any]] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def evaluate_conditions(self, context: Dict[str, Any]) -> bool:
        """Evaluate all conditions against a context."""
        if not self.conditions:
            return True

        results = [cond.evaluate(context) for cond in self.conditions]

        if self.condition_logic == "all":
            return all(results)
        elif self.condition_logic == "any":
            return any(results)
        else:
            # Custom logic not implemented
            logger.warning("Unknown condition logic: %s", self.condition_logic)
            return False

    def matches(self, context: Dict[str, Any]) -> bool:
        """Check if the rule matches the given context."""
        if not self.enabled:
            return False

        return self.evaluate_conditions(context)


class DeduplicationCache:
    """Cache for message deduplication."""

    def __init__(self, ttl_minutes: int = 60):
        """
        Initialize deduplication cache.

        Args:
            ttl_minutes: Time to live for cache entries in minutes
        """
        self.ttl = timedelta(minutes=ttl_minutes)
        self.cache: Dict[str, datetime] = {}
        self._cleanup_interval = timedelta(minutes=5)
        self._last_cleanup = datetime.now(timezone.utc)

    def _cleanup(self) -> None:
        """Remove expired entries from cache."""
        now = datetime.now(timezone.utc)
        if now - self._last_cleanup < self._cleanup_interval:
            return

        expired_keys = [
            key for key, timestamp in self.cache.items() if now - timestamp > self.ttl
        ]

        for key in expired_keys:
            del self.cache[key]

        self._last_cleanup = now

        if expired_keys:
            logger.debug(
                "Cleaned up %d expired deduplication entries", len(expired_keys)
            )

    def is_duplicate(self, key: str) -> bool:
        """Check if a message key is a duplicate."""
        self._cleanup()

        if key in self.cache:
            # Update timestamp for sliding window
            self.cache[key] = datetime.now(timezone.utc)
            return True

        return False

    def add(self, key: str) -> None:
        """Add a message key to the cache."""
        self.cache[key] = datetime.now(timezone.utc)

    def generate_key(self, context: Dict[str, Any]) -> str:
        """Generate a deduplication key from context."""
        # Use important fields for deduplication
        parts = []

        for field_name in ["message_type", "incident_id", "severity", "incident_type"]:
            if field_name in context:
                parts.append(f"{field_name}:{context[field_name]}")

        # Add recipient info if available
        if "recipients" in context:
            recipient_str = ",".join(
                sorted(
                    [
                        r.get("address", r.get("recipient_id", ""))
                        for r in context["recipients"]
                    ]
                )
            )
            parts.append(f"recipients:{recipient_str}")

        return "|".join(parts)


class NotificationRuleEngine:
    """Engine for processing notification rules."""

    def __init__(self) -> None:
        """Initialize the rule engine."""
        self.rules: List[NotificationRule] = []
        self.dedup_cache = DeduplicationCache()
        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        """Initialize default notification rules."""
        # Critical severity escalation rule
        critical_rule = NotificationRule(
            id="critical-escalation",
            name="Critical Incident Escalation",
            description="Escalate critical incidents immediately",
            priority=1000,
            conditions=[
                RuleCondition(
                    type=RuleConditionType.SEVERITY,
                    field="severity",
                    operator="eq",
                    value="critical",
                ),
            ],
            actions=[
                {
                    "action": RuleAction.MODIFY_PRIORITY,
                    "priority": NotificationPriority.CRITICAL,
                },
                {
                    "action": RuleAction.ADD_RECIPIENTS,
                    "recipients": [
                        {"role": "manager"},
                        {"on_call": True, "primary_only": True},
                    ],
                },
            ],
        )
        self.add_rule(critical_rule)

        # After hours routing rule
        after_hours_rule = NotificationRule(
            id="after-hours-routing",
            name="After Hours Routing",
            description="Route to on-call during off hours",
            priority=500,
            conditions=[
                RuleCondition(
                    type=RuleConditionType.TIME,
                    field="hour",
                    operator="not_in",
                    value=list(range(9, 18)),  # 9 AM to 6 PM
                ),
            ],
            actions=[
                {
                    "action": RuleAction.ADD_RECIPIENTS,
                    "recipients": [{"on_call": True}],
                },
            ],
        )
        self.add_rule(after_hours_rule)

        # Suppress low severity at night
        night_suppress_rule = NotificationRule(
            id="night-suppress-low",
            name="Suppress Low Severity at Night",
            description="Don't send low severity alerts at night",
            priority=400,
            conditions=[
                RuleCondition(
                    type=RuleConditionType.SEVERITY,
                    field="severity",
                    operator="eq",
                    value="low",
                ),
                RuleCondition(
                    type=RuleConditionType.TIME,
                    field="hour",
                    operator="not_in",
                    value=list(range(7, 23)),  # 7 AM to 11 PM
                ),
            ],
            actions=[
                {
                    "action": RuleAction.SUPPRESS,
                    "reason": "Low severity suppressed during night hours",
                },
            ],
        )
        self.add_rule(night_suppress_rule)

        logger.info("Initialized %d default notification rules", len(self.rules))

    def add_rule(self, rule: NotificationRule) -> None:
        """Add a rule to the engine."""
        self.rules.append(rule)
        # Keep rules sorted by priority (descending)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

        logger.info(
            "Added notification rule: %s",
            rule.id,
            extra={
                "rule_name": rule.name,
                "priority": rule.priority,
                "conditions": len(rule.conditions),
                "actions": len(rule.actions),
            },
        )

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule from the engine."""
        original_count = len(self.rules)
        self.rules = [r for r in self.rules if r.id != rule_id]

        if len(self.rules) < original_count:
            logger.info("Removed notification rule: %s", rule_id)
            return True
        return False

    def process_notification(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process a notification through the rule engine.

        Args:
            context: Notification context

        Returns:
            Modified context with applied rules
        """
        # Add time-based fields for rule evaluation
        now = datetime.now(timezone.utc)
        context["timestamp"] = now
        context["hour"] = now.hour
        context["day_of_week"] = now.weekday()
        context["date"] = now.date()

        # Check for duplicates
        dedup_key = self.dedup_cache.generate_key(context)
        if self.dedup_cache.is_duplicate(dedup_key):
            logger.info(
                "Duplicate notification suppressed",
                extra={"dedup_key": dedup_key},
            )
            context["suppressed"] = True
            context["suppression_reason"] = "Duplicate notification"
            return context

        # Track this notification
        self.dedup_cache.add(dedup_key)

        # Apply matching rules
        applied_rules = []
        for rule in self.rules:
            if rule.matches(context):
                logger.debug(
                    "Rule matched: %s",
                    rule.id,
                    extra={"rule_name": rule.name},
                )

                # Apply rule actions
                for action in rule.actions:
                    self._apply_action(context, action)

                applied_rules.append(rule.id)

                # Check if notification was suppressed
                if context.get("suppressed", False):
                    break

        context["applied_rules"] = applied_rules

        logger.info(
            "Notification processed by rule engine",
            extra={
                "applied_rules": len(applied_rules),
                "suppressed": context.get("suppressed", False),
                "priority": context.get("priority"),
            },
        )

        return context

    def _apply_action(
        self,
        context: Dict[str, Any],
        action: Dict[str, Any],
    ) -> None:
        """Apply a rule action to the context."""
        action_type = RuleAction(action["action"])

        action_handlers = {
            RuleAction.ROUTE: self._apply_route_action,
            RuleAction.ESCALATE: self._apply_escalate_action,
            RuleAction.SUPPRESS: self._apply_suppress_action,
            RuleAction.MODIFY_PRIORITY: self._apply_modify_priority_action,
            RuleAction.ADD_RECIPIENTS: self._apply_add_recipients_action,
            RuleAction.REMOVE_RECIPIENTS: self._apply_remove_recipients_action,
            RuleAction.SET_CHANNEL: self._apply_set_channel_action,
            RuleAction.DELAY: self._apply_delay_action,
        }

        handler = action_handlers.get(action_type)
        if handler:
            handler(context, action)
        else:
            logger.warning("Unknown action type: %s", action_type)

    def _apply_route_action(
        self, context: Dict[str, Any], action: Dict[str, Any]
    ) -> None:
        """Route to specific recipients."""
        context["recipients"] = action.get("recipients", [])

    def _apply_escalate_action(
        self, context: Dict[str, Any], action: Dict[str, Any]
    ) -> None:
        """Trigger escalation."""
        context["escalate"] = True
        context["escalation_chain"] = action.get("chain_id", "default")

    def _apply_suppress_action(
        self, context: Dict[str, Any], action: Dict[str, Any]
    ) -> None:
        """Suppress the notification."""
        context["suppressed"] = True
        context["suppression_reason"] = action.get("reason", "Rule suppression")

    def _apply_modify_priority_action(
        self, context: Dict[str, Any], action: Dict[str, Any]
    ) -> None:
        """Change notification priority."""
        context["priority"] = action.get("priority", NotificationPriority.MEDIUM)

    def _apply_add_recipients_action(
        self, context: Dict[str, Any], action: Dict[str, Any]
    ) -> None:
        """Add additional recipients."""
        if "recipients" not in context:
            context["recipients"] = []
        context["recipients"].extend(action.get("recipients", []))

    def _apply_remove_recipients_action(
        self, context: Dict[str, Any], action: Dict[str, Any]
    ) -> None:
        """Remove recipients."""
        if "recipients" in context:
            remove_specs = action.get("recipients", [])
            context["recipients"] = [
                r for r in context["recipients"] if r not in remove_specs
            ]

    def _apply_set_channel_action(
        self, context: Dict[str, Any], action: Dict[str, Any]
    ) -> None:
        """Override notification channel."""
        channel = action.get("channel")
        if channel and "recipients" in context:
            for recipient in context["recipients"]:
                recipient["channel"] = channel

    def _apply_delay_action(
        self, context: Dict[str, Any], action: Dict[str, Any]
    ) -> None:
        """Delay notification."""
        context["delay_minutes"] = action.get("minutes", 0)
