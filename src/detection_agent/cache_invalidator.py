"""
Cache invalidation strategies for the Detection Agent.

This module provides cache invalidation logic for query results.
"""

from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
import logging
from enum import Enum

from .query_cache import QueryCache


class InvalidationEvent(Enum):
    """Types of events that trigger cache invalidation."""
    RULE_UPDATE = "rule_update"
    CONFIG_CHANGE = "config_change"
    MANUAL_CLEAR = "manual_clear"
    SCHEDULED = "scheduled"
    DETECTION_FOUND = "detection_found"


class CacheInvalidator:
    """Manages cache invalidation strategies."""

    def __init__(self, query_cache: QueryCache, config: Dict[str, Any]):
        """
        Initialize the cache invalidator.

        Args:
            query_cache: QueryCache instance
            config: Configuration dictionary
        """
        self.query_cache = query_cache
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Invalidation settings
        inv_config = config.get("agents", {}).get("detection", {}).get("cache_invalidation", {})
        self.enabled = inv_config.get("enabled", True)
        self.invalidate_on_detection = inv_config.get("invalidate_on_detection", True)
        self.invalidate_on_rule_change = inv_config.get("invalidate_on_rule_change", True)
        self.scheduled_interval_hours = inv_config.get("scheduled_interval_hours", 6)

        # Track invalidation history
        self._invalidation_history: List[Dict[str, Any]] = []
        self._last_scheduled_invalidation = datetime.now()

        # Track rules that have changed
        self._changed_rules: Set[str] = set()

    def invalidate(
        self,
        event: InvalidationEvent,
        rule_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Perform cache invalidation based on event.

        Args:
            event: Type of invalidation event
            rule_type: Optional rule type to invalidate
            metadata: Optional event metadata

        Returns:
            Number of entries invalidated
        """
        if not self.enabled:
            return 0

        self.logger.info("Processing invalidation event: %s", event.value)

        count = 0

        if event == InvalidationEvent.RULE_UPDATE:
            count = self._invalidate_rule_update(rule_type)
        elif event == InvalidationEvent.CONFIG_CHANGE:
            count = self._invalidate_config_change()
        elif event == InvalidationEvent.MANUAL_CLEAR:
            count = self._invalidate_manual(rule_type)
        elif event == InvalidationEvent.SCHEDULED:
            count = self._invalidate_scheduled()
        elif event == InvalidationEvent.DETECTION_FOUND:
            count = self._invalidate_detection_found(rule_type, metadata)

        # Record invalidation event
        self._record_invalidation(event, count, rule_type, metadata)

        return count

    def _invalidate_rule_update(self, rule_type: Optional[str]) -> int:
        """
        Invalidate cache entries when rules are updated.

        Args:
            rule_type: Optional specific rule type

        Returns:
            Number of entries invalidated
        """
        if not self.invalidate_on_rule_change:
            return 0

        # Track changed rules
        if rule_type:
            self._changed_rules.add(rule_type)

        # Invalidate entries for the changed rule
        count = int(self.query_cache.invalidate(rule_type=rule_type))

        self.logger.info("Invalidated %s cache entries for rule update: %s", count, rule_type)
        return count

    def _invalidate_config_change(self) -> int:
        """
        Invalidate cache entries when configuration changes.

        Returns:
            Number of entries invalidated
        """
        # Clear entire cache on config change
        self.query_cache.clear()
        count = int(self.query_cache.get_stats()["size"])

        self.logger.info("Cleared entire cache due to config change: %s entries", count)
        return count

    def _invalidate_manual(self, rule_type: Optional[str]) -> int:
        """
        Manual cache invalidation.

        Args:
            rule_type: Optional specific rule type

        Returns:
            Number of entries invalidated
        """
        if rule_type:
            count = self.query_cache.invalidate(rule_type=rule_type)
            self.logger.info("Manually invalidated %s entries for rule type: %s", count, rule_type)
        else:
            self.query_cache.clear()
            count = int(self.query_cache.get_stats()["size"])
            self.logger.info("Manually cleared entire cache: %s entries", count)

        return count

    def _invalidate_scheduled(self) -> int:
        """
        Scheduled cache invalidation.

        Returns:
            Number of entries invalidated
        """
        # Invalidate entries older than scheduled interval
        older_than = datetime.now() - timedelta(hours=self.scheduled_interval_hours)
        count = int(self.query_cache.invalidate(older_than=older_than))

        self._last_scheduled_invalidation = datetime.now()

        self.logger.info("Scheduled invalidation: removed %s old entries", count)
        return count

    def _invalidate_detection_found(
        self,
        rule_type: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> int:
        """
        Invalidate cache when detection is found.

        Args:
            rule_type: Rule type that found detection
            metadata: Detection metadata

        Returns:
            Number of entries invalidated
        """
        if not self.invalidate_on_detection:
            return 0

        # Invalidate entries for the rule that found something
        count = 0

        if rule_type:
            count = self.query_cache.invalidate(rule_type=rule_type)
            self.logger.info("Invalidated %s entries after detection in rule: %s", count, rule_type)

        # If high severity, invalidate more aggressively
        if metadata and metadata.get("severity") in ["high", "critical"]:
            # Invalidate all entries older than 1 hour
            older_than = datetime.now() - timedelta(hours=1)
            additional_count = self.query_cache.invalidate(older_than=older_than)
            count += additional_count
            self.logger.info(
                "Additional %s entries invalidated due to high severity",
                additional_count
            )

        return count

    def _record_invalidation(
        self,
        event: InvalidationEvent,
        count: int,
        rule_type: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> None:
        """Record invalidation event in history."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": event.value,
            "entries_invalidated": count,
            "rule_type": rule_type,
            "metadata": metadata or {}
        }

        self._invalidation_history.append(record)

        # Keep only recent history (last 100 events)
        if len(self._invalidation_history) > 100:
            self._invalidation_history = self._invalidation_history[-100:]

    def should_run_scheduled(self) -> bool:
        """
        Check if scheduled invalidation should run.

        Returns:
            True if scheduled invalidation is due
        """
        if not self.enabled:
            return False

        time_since_last = datetime.now() - self._last_scheduled_invalidation
        return time_since_last >= timedelta(hours=self.scheduled_interval_hours)

    def on_rule_change(self, rule_type: str) -> None:
        """
        Handle rule change notification.

        Args:
            rule_type: Rule that changed
        """
        if self.enabled and self.invalidate_on_rule_change:
            self.invalidate(InvalidationEvent.RULE_UPDATE, rule_type=rule_type)

    def on_detection(
        self,
        rule_type: str,
        severity: str,
        event_count: int
    ) -> None:
        """
        Handle detection found notification.

        Args:
            rule_type: Rule that found detection
            severity: Detection severity
            event_count: Number of events detected
        """
        if self.enabled and self.invalidate_on_detection:
            metadata = {
                "severity": severity,
                "event_count": event_count
            }
            self.invalidate(
                InvalidationEvent.DETECTION_FOUND,
                rule_type=rule_type,
                metadata=metadata
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get invalidation statistics.

        Returns:
            Dictionary of invalidation stats
        """
        total_invalidations = sum(
            record["entries_invalidated"]
            for record in self._invalidation_history
        )

        event_counts: Dict[str, int] = {}
        for record in self._invalidation_history:
            event = record["event"]
            event_counts[event] = event_counts.get(event, 0) + 1

        return {
            "enabled": self.enabled,
            "total_invalidations": total_invalidations,
            "history_size": len(self._invalidation_history),
            "events_by_type": event_counts,
            "changed_rules": list(self._changed_rules),
            "last_scheduled": self._last_scheduled_invalidation.isoformat(),
            "next_scheduled": (
                self._last_scheduled_invalidation
                + timedelta(hours=self.scheduled_interval_hours)
            ).isoformat()
        }
