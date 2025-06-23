"""
Metrics collection and reporting for the orchestrator agent.
"""

import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import google.cloud.monitoring_v3 as monitoring_v3
from google.cloud import firestore_v1 as firestore

if TYPE_CHECKING:
    pass


class MetricType:
    """Metric type definitions."""

    INCIDENTS_PROCESSED = "incidents_processed"
    INCIDENTS_BY_SEVERITY = "incidents_by_severity"
    INCIDENTS_BY_STATUS = "incidents_by_status"
    WORKFLOW_DURATION = "workflow_duration"
    STATE_TRANSITION_TIME = "state_transition_time"
    REMEDIATION_SUCCESS_RATE = "remediation_success_rate"
    APPROVAL_RESPONSE_TIME = "approval_response_time"
    AGENT_PERFORMANCE = "agent_performance"
    ERROR_RATE = "error_rate"
    NOTIFICATION_DELIVERY_RATE = "notification_delivery_rate"


class MetricsCollector:
    """Collects and reports metrics for the orchestrator agent."""

    monitoring_client: Optional[monitoring_v3.MetricServiceClient]

    def __init__(self, agent_id: str, project_id: str, db: firestore.Client):
        """Initialize the metrics collector."""
        self.agent_id = agent_id
        self.project_id = project_id
        self.db = db
        self.metrics_collection = db.collection("orchestrator_metrics")

        # Initialize Cloud Monitoring client
        try:
            self.monitoring_client = monitoring_v3.MetricServiceClient()
            self.project_name = f"projects/{project_id}"
        except (OSError, ConnectionError, RuntimeError, ValueError, ImportError):
            self.monitoring_client = None

        # In-memory metrics buffer
        self.metrics_buffer: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.last_flush = datetime.now(timezone.utc)

    async def record_metric(
        self,
        metric_type: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Record a metric value."""
        metric_entry = {
            "metric_type": metric_type,
            "value": value,
            "labels": labels or {},
            "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
            "agent_id": self.agent_id,
        }

        # Add to buffer
        self.metrics_buffer[metric_type].append(metric_entry)

        # Flush if buffer is getting large or time-based
        if (
            len(self.metrics_buffer[metric_type]) > 100
            or (datetime.now(timezone.utc) - self.last_flush).seconds > 60
        ):
            await self.flush_metrics()

    async def increment_counter(
        self,
        metric_type: str,
        labels: Optional[Dict[str, str]] = None,
        increment: int = 1,
    ) -> None:
        """Increment a counter metric."""
        await self.record_metric(metric_type, increment, labels)

    async def record_duration(
        self,
        metric_type: str,
        duration_seconds: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a duration metric."""
        await self.record_metric(metric_type, duration_seconds, labels)

    async def flush_metrics(self) -> None:
        """Flush metrics buffer to storage."""
        if not self.metrics_buffer:
            return

        try:
            # Batch write to Firestore
            batch = self.db.batch()

            for metric_type, entries in self.metrics_buffer.items():
                # Aggregate metrics
                aggregated = self._aggregate_metrics(metric_type, entries)

                # Store aggregated metrics
                doc_ref = self.metrics_collection.document()
                batch.set(doc_ref, aggregated)

                # Send to Cloud Monitoring if available
                if self.monitoring_client:
                    await self._send_to_cloud_monitoring(metric_type, aggregated)

            # Commit batch
            batch.commit()

            # Clear buffer
            self.metrics_buffer.clear()
            self.last_flush = datetime.now(timezone.utc)

        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            print(f"Failed to flush metrics: {e}")

    def _aggregate_metrics(
        self, metric_type: str, entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate metric entries."""
        if not entries:
            return {}

        values = [e["value"] for e in entries]

        aggregated = {
            "metric_type": metric_type,
            "period_start": min(e["timestamp"] for e in entries),
            "period_end": max(e["timestamp"] for e in entries),
            "count": len(entries),
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "agent_id": self.agent_id,
        }

        # Add median and percentiles for larger datasets
        if len(values) > 10:
            aggregated["median"] = statistics.median(values)
            aggregated["p95"] = self._percentile(values, 95)
            aggregated["p99"] = self._percentile(values, 99)

        # Aggregate by labels
        label_aggregates: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"count": 0, "sum": 0}
        )
        for entry in entries:
            for label_key, label_value in entry.get("labels", {}).items():
                key = f"{label_key}:{label_value}"
                label_aggregates[key]["count"] += 1
                label_aggregates[key]["sum"] += entry["value"]

        if label_aggregates:
            aggregated["label_aggregates"] = dict(label_aggregates)

        return aggregated

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    async def _send_to_cloud_monitoring(
        self, metric_type: str, aggregated: Dict[str, Any]
    ) -> None:
        """Send metrics to Google Cloud Monitoring."""
        if not self.monitoring_client:
            return

        try:
            # Create time series
            series = monitoring_v3.TimeSeries()
            series.metric.type = f"custom.googleapis.com/orchestrator/{metric_type}"
            series.resource.type = "global"
            if hasattr(series.resource, "labels"):
                series.resource.labels["project_id"] = self.project_id

            # Add metric labels
            if hasattr(series.metric, "labels"):
                series.metric.labels["agent_id"] = self.agent_id

            # Create point
            point = monitoring_v3.Point()
            point.value.double_value = aggregated["mean"]
            now = datetime.now(timezone.utc)
            if hasattr(point.interval, "end_time"):
                point.interval.end_time.seconds = int(now.timestamp())
                point.interval.end_time.nanos = now.microsecond * 1000

            series.points = [point]

            # Write time series
            self.monitoring_client.create_time_series(
                name=self.project_name, time_series=[series]
            )

        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            print(f"Failed to send to Cloud Monitoring: {e}")

    async def generate_report(
        self, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """Generate a metrics report for the specified time period."""
        # Query metrics from Firestore
        query = (
            self.metrics_collection.where("period_start", ">=", start_time.isoformat())
            .where("period_end", "<=", end_time.isoformat())
            .where("agent_id", "==", self.agent_id)
        )

        metrics_data = []
        for doc in query.stream():
            metrics_data.append(doc.to_dict())

        # Generate report
        report = {
            "period": {"start": start_time.isoformat(), "end": end_time.isoformat()},
            "agent_id": self.agent_id,
            "summary": self._generate_summary(metrics_data),
            "details": self._generate_details(metrics_data),
        }

        return report

    def _generate_summary(self, metrics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics."""
        summary = {
            "total_incidents": 0,
            "average_resolution_time": 0,
            "remediation_success_rate": 0,
            "incidents_by_severity": {},
            "incidents_by_status": {},
        }

        # Process metrics
        for metric in metrics_data:
            metric_type = metric.get("metric_type")

            if metric_type == MetricType.INCIDENTS_PROCESSED:
                summary["total_incidents"] += metric.get("sum", 0)
            elif metric_type == MetricType.WORKFLOW_DURATION:
                summary["average_resolution_time"] = metric.get("mean", 0)
            elif metric_type == MetricType.REMEDIATION_SUCCESS_RATE:
                summary["remediation_success_rate"] = metric.get("mean", 0)

        return summary

    def _generate_details(
        self, metrics_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate detailed metrics."""
        details = []

        # Group by metric type
        by_type = defaultdict(list)
        for metric in metrics_data:
            by_type[metric["metric_type"]].append(metric)

        # Process each metric type
        for metric_type, metrics in by_type.items():
            detail = {
                "metric_type": metric_type,
                "data_points": len(metrics),
                "total_count": sum(m.get("count", 0) for m in metrics),
                "overall_mean": statistics.mean([m.get("mean", 0) for m in metrics]),
                "overall_min": min(m.get("min", 0) for m in metrics),
                "overall_max": max(m.get("max", 0) for m in metrics),
            }
            details.append(detail)

        return details

    async def get_current_stats(self) -> Dict[str, Any]:
        """Get current real-time statistics."""
        # Flush any pending metrics
        await self.flush_metrics()

        # Calculate stats for the last hour
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=1)

        report = await self.generate_report(start_time, end_time)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "last_hour": report["summary"],
            "agent_status": "active",
            "buffer_size": sum(
                len(entries) for entries in self.metrics_buffer.values()
            ),
        }
