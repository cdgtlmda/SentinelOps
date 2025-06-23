"""
Performance tuning configuration for the Detection Agent.

This module provides performance tuning parameters and optimization settings.
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class PerformanceTuningConfig:
    """Performance tuning configuration parameters."""

    # Query performance settings
    query_timeout_seconds: int = 30
    max_concurrent_queries: int = 5
    query_result_cache_ttl: int = 300  # 5 minutes
    enable_query_cache: bool = True

    # Memory management
    max_events_in_memory: int = 50000
    event_batch_size: int = 1000
    max_processed_events_cache: int = 100000

    # Processing optimization
    parallel_rule_execution: bool = True
    max_parallel_rules: int = 3
    enable_adaptive_throttling: bool = True

    # Resource limits
    max_cpu_percent: float = 80.0
    max_memory_mb: int = 2048

    # BigQuery optimization
    use_query_priority: bool = True
    query_priority: str = "INTERACTIVE"  # BATCH or INTERACTIVE
    enable_result_caching: bool = True
    use_standard_sql: bool = True

    # Scan optimization
    enable_smart_scanning: bool = True
    skip_low_priority_on_high_load: bool = True
    adaptive_scan_interval: bool = True
    min_scan_interval_seconds: int = 30
    max_scan_interval_seconds: int = 300

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "PerformanceTuningConfig":
        """Create performance config from configuration dictionary."""
        perf_config = config.get("agents", {}).get("detection", {}).get("performance_tuning", {})

        return cls(
            query_timeout_seconds=perf_config.get("query_timeout_seconds", 30),
            max_concurrent_queries=perf_config.get("max_concurrent_queries", 5),
            query_result_cache_ttl=perf_config.get("query_result_cache_ttl", 300),
            enable_query_cache=perf_config.get("enable_query_cache", True),
            max_events_in_memory=perf_config.get("max_events_in_memory", 50000),
            event_batch_size=perf_config.get("event_batch_size", 1000),
            max_processed_events_cache=perf_config.get("max_processed_events_cache", 100000),
            parallel_rule_execution=perf_config.get("parallel_rule_execution", True),
            max_parallel_rules=perf_config.get("max_parallel_rules", 3),
            enable_adaptive_throttling=perf_config.get("enable_adaptive_throttling", True),
            max_cpu_percent=perf_config.get("max_cpu_percent", 80.0),
            max_memory_mb=perf_config.get("max_memory_mb", 2048),
            use_query_priority=perf_config.get("use_query_priority", True),
            query_priority=perf_config.get("query_priority", "INTERACTIVE"),
            enable_result_caching=perf_config.get("enable_result_caching", True),
            use_standard_sql=perf_config.get("use_standard_sql", True),
            enable_smart_scanning=perf_config.get("enable_smart_scanning", True),
            skip_low_priority_on_high_load=perf_config.get("skip_low_priority_on_high_load", True),
            adaptive_scan_interval=perf_config.get("adaptive_scan_interval", True),
            min_scan_interval_seconds=perf_config.get("min_scan_interval_seconds", 30),
            max_scan_interval_seconds=perf_config.get("max_scan_interval_seconds", 300)
        )

    def get_bigquery_job_config(self) -> Dict[str, Any]:
        """Get BigQuery job configuration based on performance settings."""
        config: Dict[str, Any] = {
            "use_query_cache": self.enable_result_caching,
            "use_legacy_sql": not self.use_standard_sql,
            "timeout_ms": self.query_timeout_seconds * 1000
        }

        if self.use_query_priority:
            # This is a string value ("INTERACTIVE" or "BATCH")
            config["priority"] = self.query_priority

        return config

    def should_skip_rule(self, rule_priority: int, system_load: float) -> bool:
        """
        Determine if a rule should be skipped based on system load.

        Args:
            rule_priority: Priority of the rule (higher = more important)
            system_load: Current system load (0.0 to 1.0)

        Returns:
            True if rule should be skipped
        """
        if not self.skip_low_priority_on_high_load:
            return False

        # Skip low priority rules when load is high
        if system_load > 0.8 and rule_priority < 5:
            return True
        elif system_load > 0.9 and rule_priority < 7:
            return True

        return False

    def calculate_adaptive_scan_interval(
        self,
        base_interval: int,
        error_rate: float,
        processing_time: float,
        event_rate: float
    ) -> int:
        """
        Calculate adaptive scan interval based on system metrics.

        Args:
            base_interval: Base scan interval in seconds
            error_rate: Recent error rate (0.0 to 1.0)
            processing_time: Average processing time per scan
            event_rate: Average events per scan

        Returns:
            Adjusted scan interval in seconds
        """
        if not self.adaptive_scan_interval:
            return base_interval

        # Start with base interval
        adjusted_interval = base_interval

        # Increase interval if error rate is high
        if error_rate > 0.1:
            adjusted_interval = int(adjusted_interval * (1 + error_rate))

        # Increase interval if processing is slow
        if processing_time > base_interval * 0.5:
            adjusted_interval = int(adjusted_interval * 1.5)

        # Decrease interval if event rate is high (more frequent checks needed)
        if event_rate > 100:
            adjusted_interval = int(adjusted_interval * 0.8)

        # Apply bounds
        adjusted_interval = max(self.min_scan_interval_seconds, adjusted_interval)
        adjusted_interval = min(self.max_scan_interval_seconds, adjusted_interval)

        return adjusted_interval

    def get_event_processing_batch_size(self, available_memory_mb: int) -> int:
        """
        Calculate optimal batch size based on available memory.

        Args:
            available_memory_mb: Available memory in MB

        Returns:
            Optimal batch size
        """
        # Estimate memory per event (rough estimate: 1KB per event)
        memory_per_event_kb = 1

        # Use 50% of available memory for events
        usable_memory_kb = (available_memory_mb * 1024) * 0.5

        # Calculate max events that fit in memory
        max_events = int(usable_memory_kb / memory_per_event_kb)

        # Apply configured limits
        max_events = min(max_events, self.max_events_in_memory)

        # Return batch size (smaller of calculated or configured)
        return min(max_events, self.event_batch_size)

    def validate(self) -> List[str]:
        """
        Validate performance configuration.

        Returns:
            List of validation errors
        """
        errors = []

        if self.max_concurrent_queries < 1:
            errors.append("max_concurrent_queries must be at least 1")

        if self.query_timeout_seconds < 1:
            errors.append("query_timeout_seconds must be at least 1")

        if self.max_cpu_percent <= 0 or self.max_cpu_percent > 100:
            errors.append("max_cpu_percent must be between 0 and 100")

        if self.min_scan_interval_seconds >= self.max_scan_interval_seconds:
            errors.append("min_scan_interval must be less than max_scan_interval")

        if self.query_priority not in ["BATCH", "INTERACTIVE"]:
            errors.append("query_priority must be BATCH or INTERACTIVE")

        return errors

    def clear_cache(self) -> None:
        """Clear any cached performance calculations."""
        # Clear any cached performance metrics or tuning data
        if hasattr(self, '_cache'):
            self._cache.clear()
        if hasattr(self, '_performance_history'):
            self._performance_history.clear()
