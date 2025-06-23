"""
Interim results storage for the Detection Agent.

This module provides storage for intermediate query results used in complex detection scenarios.
"""

import logging
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class InterimResult:
    """Represents an interim query result."""

    result_id: str
    rule_type: str
    stage: str  # e.g., "initial_scan", "correlation", "aggregation"
    data: Any
    metadata: Dict[str, Any]
    created_at: datetime
    expires_at: datetime


class InterimResultsStorage:
    """Manages storage of interim detection results."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the interim results storage.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Storage settings
        storage_config = (
            config.get("agents", {}).get("detection", {}).get("interim_storage", {})
        )
        self.enabled = storage_config.get("enabled", True)
        default_path = Path(tempfile.gettempdir()) / "sentinelops" / "interim"
        self.storage_path = Path(storage_config.get("storage_path", str(default_path)))
        self.max_results = storage_config.get("max_results", 10000)
        self.default_ttl_hours = storage_config.get("default_ttl_hours", 24)

        # In-memory storage (could be replaced with Redis or similar)
        self._storage: Dict[str, InterimResult] = {}

        # Create storage directory if needed
        if self.enabled:
            self.storage_path.mkdir(parents=True, exist_ok=True)

    def store(
        self,
        result_id: str,
        rule_type: str,
        stage: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        ttl_hours: Optional[int] = None,
    ) -> None:
        """
        Store an interim result.

        Args:
            result_id: Unique identifier for the result
            rule_type: Type of detection rule
            stage: Processing stage
            data: Result data to store
            metadata: Optional metadata
            ttl_hours: Optional custom TTL in hours
        """
        if not self.enabled:
            return

        # Check storage size
        if len(self._storage) >= self.max_results:
            self._cleanup_expired()

            # If still too many, remove oldest
            if len(self._storage) >= self.max_results:
                self._remove_oldest()

        # Create interim result
        ttl = ttl_hours or self.default_ttl_hours
        result = InterimResult(
            result_id=result_id,
            rule_type=rule_type,
            stage=stage,
            data=data,
            metadata=metadata or {},
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=ttl),
        )

        self._storage[result_id] = result
        self.logger.debug("Stored interim result: %s (stage: %s)", result_id, stage)

    def retrieve(self, result_id: str, stage: Optional[str] = None) -> Optional[Any]:
        """
        Retrieve an interim result.

        Args:
            result_id: Result identifier
            stage: Optional stage filter

        Returns:
            Stored data if found and valid, None otherwise
        """
        if not self.enabled:
            return None

        # Check if result exists
        if result_id not in self._storage:
            self.logger.debug("Interim result not found: %s", result_id)
            return None

        result = self._storage[result_id]

        # Check if expired
        if datetime.now() > result.expires_at:
            self.logger.debug("Interim result expired: %s", result_id)
            del self._storage[result_id]
            return None

        # Check stage filter
        if stage and result.stage != stage:
            self.logger.debug("Stage mismatch for result: %s", result_id)
            return None

        return result.data

    def retrieve_by_rule_type(
        self,
        rule_type: str,
        stage: Optional[str] = None,
        max_age_hours: Optional[int] = None,
    ) -> List[InterimResult]:
        """
        Retrieve all interim results for a rule type.

        Args:
            rule_type: Type of detection rule
            stage: Optional stage filter
            max_age_hours: Optional maximum age filter

        Returns:
            List of matching interim results
        """
        if not self.enabled:
            return []

        results = []
        min_created_at = None

        if max_age_hours:
            min_created_at = datetime.now() - timedelta(hours=max_age_hours)

        for _, result in self._storage.items():
            # Check if expired
            if datetime.now() > result.expires_at:
                continue

            # Check rule type
            if result.rule_type != rule_type:
                continue

            # Check stage filter
            if stage and result.stage != stage:
                continue

            # Check age filter
            if min_created_at and result.created_at < min_created_at:
                continue

            results.append(result)

        # Sort by creation time (newest first)
        results.sort(key=lambda r: r.created_at, reverse=True)

        return results

    def update_metadata(self, result_id: str, metadata_updates: Dict[str, Any]) -> bool:
        """
        Update metadata for an interim result.

        Args:
            result_id: Result identifier
            metadata_updates: Metadata updates

        Returns:
            True if updated, False if not found
        """
        if not self.enabled or result_id not in self._storage:
            return False

        result = self._storage[result_id]
        result.metadata.update(metadata_updates)
        self.logger.debug("Updated metadata for result: %s", result_id)

        return True

    def delete(self, result_id: str) -> bool:
        """
        Delete an interim result.

        Args:
            result_id: Result identifier

        Returns:
            True if deleted, False if not found
        """
        if not self.enabled or result_id not in self._storage:
            return False

        del self._storage[result_id]
        self.logger.debug("Deleted interim result: %s", result_id)
        return True

    def _cleanup_expired(self) -> int:
        """
        Remove expired interim results.

        Returns:
            Number of results removed
        """
        expired_keys = []
        now = datetime.now()

        for result_id, result in self._storage.items():
            if now > result.expires_at:
                expired_keys.append(result_id)

        for key in expired_keys:
            del self._storage[key]

        if expired_keys:
            self.logger.info("Cleaned up %s expired interim results", len(expired_keys))

        return len(expired_keys)

    def _remove_oldest(self) -> None:
        """Remove the oldest interim result."""
        if not self._storage:
            return

        oldest_id = min(self._storage.keys(), key=lambda k: self._storage[k].created_at)

        del self._storage[oldest_id]
        self.logger.debug("Removed oldest interim result: %s", oldest_id)

    def clear(self, rule_type: Optional[str] = None) -> int:
        """
        Clear interim results.

        Args:
            rule_type: Optional rule type filter

        Returns:
            Number of results cleared
        """
        if not self.enabled:
            return 0

        if rule_type:
            # Clear only specific rule type
            keys_to_remove = [
                key
                for key, result in self._storage.items()
                if result.rule_type == rule_type
            ]

            for key in keys_to_remove:
                del self._storage[key]

            self.logger.info(
                "Cleared %s interim results for rule type: %s",
                len(keys_to_remove),
                rule_type,
            )
            return len(keys_to_remove)
        else:
            # Clear all
            count = len(self._storage)
            self._storage.clear()
            self.logger.info("Cleared all %s interim results", count)
            return count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dictionary of storage statistics
        """
        rule_type_counts: Dict[str, int] = {}
        stage_counts: Dict[str, int] = {}

        for result in self._storage.values():
            # Count by rule type
            rule_type_counts[result.rule_type] = (
                rule_type_counts.get(result.rule_type, 0) + 1
            )

            # Count by stage
            stage_counts[result.stage] = stage_counts.get(result.stage, 0) + 1

        return {
            "enabled": self.enabled,
            "total_results": len(self._storage),
            "max_results": self.max_results,
            "by_rule_type": rule_type_counts,
            "by_stage": stage_counts,
            "storage_path": str(self.storage_path),
        }
