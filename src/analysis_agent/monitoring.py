"""
Monitoring and metrics collection for the Analysis Agent.

This module provides comprehensive monitoring, metrics collection, and
observability features for the Analysis Agent.
"""

import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any, DefaultDict, Deque, Dict, List

import google.cloud.monitoring_v3 as monitoring_v3


class MetricsCollector:
    """Collects and aggregates metrics for the Analysis Agent."""

    def __init__(self, project_id: str, logger: logging.Logger):
        """
        Initialize the metrics collector.

        Args:
            project_id: Google Cloud project ID
            logger: Logger instance
        """
        self.project_id = project_id
        self.logger = logger

        # Initialize Cloud Monitoring client
        try:
            self.monitoring_client = monitoring_v3.MetricServiceClient()
            self.project_name = f"projects/{project_id}"
            self.cloud_monitoring_enabled = True
        except (ImportError, ValueError, AttributeError) as e:
            self.logger.warning(f"Failed to initialize Cloud Monitoring: {e}")
            self.cloud_monitoring_enabled = False

        # Local metrics storage
        self.metrics: Dict[str, Any] = {
            "analyses_total": 0,
            "analyses_success": 0,
            "analyses_failed": 0,
            "analyses_cached": 0,
            "analysis_duration": deque(maxlen=1000),
            "confidence_scores": deque(maxlen=1000),
            "gemini_api_calls": 0,
            "gemini_api_errors": 0,
            "gemini_response_time": deque(maxlen=1000),
            "correlation_scores": deque(maxlen=1000),
            "recommendations_generated": 0,
            "events_processed": 0,
            "rate_limit_hits": 0,
            "memory_usage": deque(maxlen=100),
        }

        # Time-series data for graphs
        self.time_series: DefaultDict[str, Deque[Any]] = defaultdict(
            lambda: deque(maxlen=1440)
        )  # 24 hours at 1-minute intervals

        # Error tracking
        self.error_counts: DefaultDict[str, int] = defaultdict(int)
        self.recent_errors: Deque[Dict[str, Any]] = deque(maxlen=100)

    def record_analysis_start(self, incident_id: str) -> Dict[str, Any]:
        """Record the start of an analysis."""
        return {
            "incident_id": incident_id,
            "start_time": time.time(),
            "timestamp": datetime.now(timezone.utc),
        }

    def record_analysis_complete(
        self,
        context: Dict[str, Any],
        analysis_result: Dict[str, Any],
        from_cache: bool = False,
    ) -> None:
        """Record completion of an analysis."""
        duration = time.time() - context["start_time"]

        # Update metrics
        self.metrics["analyses_total"] += 1
        self.metrics["analyses_success"] += 1

        if from_cache:
            self.metrics["analyses_cached"] += 1
        else:
            self.metrics["analysis_duration"].append(duration)

        # Record confidence score
        confidence = analysis_result.get("confidence_score", 0)
        self.metrics["confidence_scores"].append(confidence)

        # Record recommendations count
        recommendations = analysis_result.get("recommendations", [])
        self.metrics["recommendations_generated"] += len(recommendations)

        # Update time series
        current_minute = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        self.time_series["analyses_per_minute"].append((current_minute, 1))
        self.time_series["avg_confidence"].append((current_minute, confidence))

        # Log metrics
        self.logger.info(
            f"Analysis completed for {context['incident_id']} "
            f"in {duration:.2f}s (cached={from_cache})"
        )

        # Send to Cloud Monitoring if enabled
        if self.cloud_monitoring_enabled and not from_cache:
            self._send_cloud_metrics(
                {
                    "analysis_duration": duration,
                    "confidence_score": confidence,
                    "recommendations_count": len(recommendations),
                }
            )

    def record_analysis_failure(
        self, context: Dict[str, Any], error: Exception
    ) -> None:
        """Record a failed analysis."""
        duration = time.time() - context["start_time"]

        # Update metrics
        self.metrics["analyses_total"] += 1
        self.metrics["analyses_failed"] += 1

        # Track error
        error_type = type(error).__name__
        self.error_counts[error_type] += 1
        self.recent_errors.append(
            {
                "incident_id": context["incident_id"],
                "error_type": error_type,
                "error_message": str(error),
                "timestamp": datetime.now(timezone.utc),
                "duration": duration,
            }
        )

        self.logger.error(
            f"Analysis failed for {context['incident_id']} "
            f"after {duration:.2f}s: {error}"
        )

    def record_gemini_api_call(
        self, success: bool, response_time: float, retry_count: int = 0
    ) -> None:
        """Record a Gemini API call."""
        self.metrics["gemini_api_calls"] += 1

        if success:
            self.metrics["gemini_response_time"].append(response_time)
        else:
            self.metrics["gemini_api_errors"] += 1

        # Track retries
        if retry_count > 0:
            self.time_series["gemini_retries"].append(
                (datetime.now(timezone.utc), retry_count)
            )

    def record_correlation_analysis(
        self, event_count: int, correlation_scores: Dict[str, float]
    ) -> None:
        """Record event correlation analysis metrics."""
        self.metrics["events_processed"] += event_count

        overall_score = correlation_scores.get("overall_score", 0)
        self.metrics["correlation_scores"].append(overall_score)

        # Track high correlation incidents
        if overall_score > 0.8:
            self.time_series["high_correlation_incidents"].append(
                (datetime.now(timezone.utc), 1)
            )

    def record_rate_limit_hit(self) -> None:
        """Record a rate limit hit."""
        self.metrics["rate_limit_hits"] += 1
        self.time_series["rate_limit_hits"].append((datetime.now(timezone.utc), 1))

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        # Calculate rates
        success_rate = (
            self.metrics["analyses_success"] / self.metrics["analyses_total"]
            if self.metrics["analyses_total"] > 0
            else 0
        )

        cache_hit_rate = (
            self.metrics["analyses_cached"] / self.metrics["analyses_total"]
            if self.metrics["analyses_total"] > 0
            else 0
        )

        # Calculate averages
        avg_duration = (
            sum(self.metrics["analysis_duration"])
            / len(self.metrics["analysis_duration"])
            if self.metrics["analysis_duration"]
            else 0
        )

        avg_confidence = (
            sum(self.metrics["confidence_scores"])
            / len(self.metrics["confidence_scores"])
            if self.metrics["confidence_scores"]
            else 0
        )

        avg_gemini_time = (
            sum(self.metrics["gemini_response_time"])
            / len(self.metrics["gemini_response_time"])
            if self.metrics["gemini_response_time"]
            else 0
        )

        return {
            "summary": {
                "total_analyses": self.metrics["analyses_total"],
                "successful_analyses": self.metrics["analyses_success"],
                "failed_analyses": self.metrics["analyses_failed"],
                "cached_analyses": self.metrics["analyses_cached"],
                "success_rate": success_rate,
                "cache_hit_rate": cache_hit_rate,
            },
            "performance": {
                "avg_analysis_duration": avg_duration,
                "avg_confidence_score": avg_confidence,
                "avg_gemini_response_time": avg_gemini_time,
                "events_processed": self.metrics["events_processed"],
                "recommendations_generated": self.metrics["recommendations_generated"],
            },
            "api_usage": {
                "gemini_api_calls": self.metrics["gemini_api_calls"],
                "gemini_api_errors": self.metrics["gemini_api_errors"],
                "gemini_error_rate": (
                    self.metrics["gemini_api_errors"] / self.metrics["gemini_api_calls"]
                    if self.metrics["gemini_api_calls"] > 0
                    else 0
                ),
                "rate_limit_hits": self.metrics["rate_limit_hits"],
            },
            "errors": {
                "error_counts": dict(self.error_counts),
                "recent_errors": list(self.recent_errors)[-10:],  # Last 10 errors
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_time_series_data(
        self, metric_name: str, duration_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Get time series data for a specific metric."""
        if metric_name not in self.time_series:
            return []

        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=duration_minutes)
        data = self.time_series[metric_name]

        # Filter and aggregate by minute
        aggregated = defaultdict(list)
        for timestamp, value in data:
            if timestamp >= cutoff_time:
                minute_key = timestamp.replace(second=0, microsecond=0)
                aggregated[minute_key].append(value)

        # Calculate averages per minute
        result = []
        for minute, values in sorted(aggregated.items()):
            result.append(
                {
                    "timestamp": minute.isoformat(),
                    "value": sum(values) / len(values) if values else 0,
                    "count": len(values),
                }
            )

        return result

    def _send_cloud_metrics(self, metrics: Dict[str, float]) -> None:
        """Send metrics to Google Cloud Monitoring."""
        if not self.cloud_monitoring_enabled:
            return

        try:
            # Create time series data
            series_list = []
            interval = monitoring_v3.TimeInterval(
                {"end_time": {"seconds": int(time.time())}}
            )

            for metric_name, value in metrics.items():
                series = monitoring_v3.TimeSeries()
                series.metric.type = (
                    f"custom.googleapis.com/sentinelops/analysis/{metric_name}"
                )
                series.resource.type = "global"
                series.resource.labels["project_id"] = self.project_id

                point = monitoring_v3.Point()
                point.value.double_value = value
                point.interval = interval

                series.points = [point]
                series_list.append(series)

            # Write time series data
            if series_list:
                self.monitoring_client.create_time_series(
                    name=self.project_name, time_series=series_list
                )
        except (ImportError, ValueError, AttributeError) as e:
            self.logger.warning(f"Failed to send metrics to Cloud Monitoring: {e}")

    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics for external storage or analysis."""
        return {
            "metrics": self.get_current_metrics(),
            "time_series": {
                "analyses_per_minute": self.get_time_series_data(
                    "analyses_per_minute", 1440
                ),
                "avg_confidence": self.get_time_series_data("avg_confidence", 1440),
                "high_correlation_incidents": self.get_time_series_data(
                    "high_correlation_incidents", 1440
                ),
                "rate_limit_hits": self.get_time_series_data("rate_limit_hits", 1440),
            },
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_info": {
                "project_id": self.project_id,
                "cloud_monitoring_enabled": self.cloud_monitoring_enabled,
            },
        }
