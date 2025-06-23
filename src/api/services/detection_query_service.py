"""
Detection query service for executing rule tests against actual data sources.

This service provides the ability to execute detection rules against configured
data sources (BigQuery, Cloud Logging, etc.) for testing and validation purposes.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from google.cloud import bigquery
from google.cloud import logging as cloud_logging
from google.oauth2 import service_account

from src.api.models.rules import Rule, RuleType
from src.common.config_loader import ConfigLoader
from src.common.secure_query_builder import SecureQueryBuilder
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class DetectionQueryService:
    """Service for executing detection queries against data sources."""

    def __init__(self) -> None:
        """Initialize the detection query service."""
        self.config = ConfigLoader()
        self._bigquery_client: Optional[bigquery.Client] = None
        self._logging_client: Optional[cloud_logging.Client] = None

    def _get_bigquery_client(self) -> bigquery.Client:
        """Get or create BigQuery client."""
        if not self._bigquery_client:
            project_id = self.config.get(
                "bigquery.project_id", self.config.get("gcp.project_id")
            )

            # Check for service account credentials
            creds_path = self.config.get(
                "bigquery.credentials_path", self.config.get("gcp.credentials_path")
            )
            if creds_path:
                credentials = service_account.Credentials.from_service_account_file(
                    creds_path
                )  # type: ignore[no-untyped-call]
                self._bigquery_client = bigquery.Client(
                    project=project_id, credentials=credentials
                )
            else:
                # Use application default credentials
                self._bigquery_client = bigquery.Client(project=project_id)

        return self._bigquery_client

    def _get_logging_client(self) -> cloud_logging.Client:
        """Get or create Cloud Logging client."""
        if not self._logging_client:
            project_id = self.config.get(
                "logging.project_id", self.config.get("gcp.project_id")
            )

            # Check for service account credentials
            creds_path = self.config.get(
                "logging.credentials_path", self.config.get("gcp.credentials_path")
            )
            if creds_path:
                credentials = service_account.Credentials.from_service_account_file(
                    creds_path
                )  # type: ignore[no-untyped-call]
                self._logging_client = cloud_logging.Client(
                    project=project_id, credentials=credentials
                )  # type: ignore[no-untyped-call]
            else:
                # Use application default credentials
                self._logging_client = cloud_logging.Client(
                    project=project_id
                )  # type: ignore[no-untyped-call]

        return self._logging_client

    async def execute_rule_test(
        self,
        rule: Rule,
        time_range_minutes: int,
        sample_size: int = 10,
        dry_run: bool = False,
    ) -> Tuple[int, List[Dict[str, Any]], float]:
        """
        Execute a rule test against actual data sources.

        Args:
            rule: The rule to test
            time_range_minutes: Time range in minutes to query
            sample_size: Maximum number of sample results to return
            dry_run: If True, validate query without execution

        Returns:
            Tuple of (match_count, sample_results, query_time_seconds)
        """
        start_time = datetime.now(timezone.utc)
        end_time = start_time
        start_time = end_time - timedelta(minutes=time_range_minutes)

        try:
            if rule.rule_type == RuleType.QUERY:
                return await self._execute_query_rule(
                    rule, start_time, end_time, sample_size, dry_run
                )
            elif rule.rule_type == RuleType.PATTERN:
                return await self._execute_pattern_rule(
                    rule, start_time, end_time, sample_size, dry_run
                )
            elif rule.rule_type == RuleType.THRESHOLD:
                return await self._execute_threshold_rule(
                    rule, start_time, end_time, sample_size, dry_run
                )
            elif rule.rule_type == RuleType.ANOMALY:
                return await self._execute_anomaly_rule(
                    rule, start_time, end_time, sample_size, dry_run
                )
            elif rule.rule_type == RuleType.CORRELATION:
                return await self._execute_correlation_rule(
                    rule, start_time, end_time, sample_size, dry_run
                )
            else:
                # Custom rule type - use query if available
                if rule.query:
                    return await self._execute_query_rule(
                        rule, start_time, end_time, sample_size, dry_run
                    )
                else:
                    logger.warning(
                        "No execution handler for rule type: %s", rule.rule_type
                    )
                    return 0, [], 0.0

        except Exception as e:
            logger.error(
                "Error executing rule test for %s: %s", rule.rule_number, str(e)
            )
            raise

    async def _execute_query_rule(
        self,
        rule: Rule,
        start_time: datetime,
        end_time: datetime,
        sample_size: int,
        dry_run: bool,
    ) -> Tuple[int, List[Dict[str, Any]], float]:
        """Execute a query-based rule."""
        if not rule.query:
            return 0, [], 0.0

        query_start = datetime.now(timezone.utc)

        # Replace time placeholders in query
        query = rule.query.replace("@start_time", f"'{start_time.isoformat()}'")
        query = query.replace("@end_time", f"'{end_time.isoformat()}'")

        # Add limit for sample size
        if "LIMIT" not in query.upper():
            query += f" LIMIT {sample_size + 100}"  # Get extra for counting

        if dry_run:
            # Validate query syntax
            client = self._get_bigquery_client()
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)

            try:
                client.query(query, job_config=job_config)
                # Query is valid, return simulated results
                return 0, [], 0.1
            except Exception as e:
                logger.error("Query validation failed: %s", str(e))
                raise

        # Execute the query
        client = self._get_bigquery_client()
        job_config = bigquery.QueryJobConfig(use_query_cache=False)

        query_job = client.query(query, job_config=job_config)
        results = list(query_job.result())

        query_time = (datetime.now(timezone.utc) - query_start).total_seconds()

        # Process results
        match_count = len(results)
        sample_results = []

        for row in results[:sample_size]:
            result_dict = dict(row.items())
            # Convert datetime objects to ISO format
            for key, value in result_dict.items():
                if isinstance(value, datetime):
                    result_dict[key] = value.isoformat()
            sample_results.append(result_dict)

        return match_count, sample_results, query_time

    async def _execute_pattern_rule(
        self,
        rule: Rule,
        start_time: datetime,
        end_time: datetime,
        sample_size: int,
        dry_run: bool,
    ) -> Tuple[int, List[Dict[str, Any]], float]:
        """Execute a pattern-based rule."""
        if not rule.conditions:
            return 0, [], 0.0

        # Find pattern condition
        pattern_condition = next(
            (c for c in rule.conditions if c.field == "pattern"), None
        )
        if not pattern_condition:
            return 0, [], 0.0

        query_start = datetime.now(timezone.utc)
        pattern = pattern_condition.value

        # Find table and field conditions
        table_condition = next((c for c in rule.conditions if c.field == "table"), None)
        field_condition = next((c for c in rule.conditions if c.field == "field"), None)

        table_name = (
            table_condition.value if table_condition else "logs.application_logs"
        )
        field_name = field_condition.value if field_condition else "message"

        # Build query using secure query builder
        try:
            query = SecureQueryBuilder.build_pattern_query(
                table_name,
                field_name,
                "@pattern",
                {
                    "start_time": "@start_time",
                    "end_time": "@end_time"
                }
            )
            # Add limit clause
            query = query.replace("LIMIT 1000", "LIMIT @limit_size")
        except ValueError as e:
            logger.error("Invalid table or field name: %s", e)
            return 0, [], 0.0

        # Define query parameters
        query_params = [
            bigquery.ScalarQueryParameter("pattern", "STRING", f"%{pattern}%"),
            bigquery.ScalarQueryParameter("start_time", "TIMESTAMP", start_time),
            bigquery.ScalarQueryParameter("end_time", "TIMESTAMP", end_time),
            bigquery.ScalarQueryParameter("limit_size", "INT64", sample_size + 100),
        ]

        if dry_run:
            return 0, [], 0.1

        # Execute pattern search
        client = self._get_bigquery_client()
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = client.query(query, job_config=job_config)
        results = list(query_job.result())

        query_time = (datetime.now(timezone.utc) - query_start).total_seconds()

        match_count = len(results)
        sample_results = []

        for row in results[:sample_size]:
            result_dict = dict(row.items())
            for key, value in result_dict.items():
                if isinstance(value, datetime):
                    result_dict[key] = value.isoformat()
            sample_results.append(result_dict)

        return match_count, sample_results, query_time

    async def _execute_threshold_rule(
        self,
        rule: Rule,
        start_time: datetime,
        end_time: datetime,
        sample_size: int,
        dry_run: bool,
    ) -> Tuple[int, List[Dict[str, Any]], float]:
        """Execute a threshold-based rule."""
        if not rule.threshold:
            return 0, [], 0.0

        query_start = datetime.now(timezone.utc)

        # Extract threshold configuration
        threshold_count = rule.threshold.count
        window_seconds = rule.threshold.window_seconds
        group_by = rule.threshold.group_by or []

        # Build aggregation query
        # Get table name from conditions if available
        table_condition = (
            next((c for c in rule.conditions if c.field == "table"), None)
            if rule.conditions
            else None
        )
        table_name = (
            table_condition.value if table_condition else "logs.application_logs"
        )

        # Build query using secure query builder
        try:
            query = SecureQueryBuilder.build_aggregation_query(
                table_name,
                group_by_fields=group_by if group_by else None,
                threshold_count=threshold_count,
                time_params={
                    "start_time": "@start_time",
                    "end_time": "@end_time"
                },
                limit=sample_size
            )
            # Replace the limit placeholder with parameter
            query = query.replace(f"LIMIT {sample_size}", "LIMIT @sample_size")
        except ValueError as e:
            logger.error("Invalid table or field name: %s", e)
            return 0, [], 0.0

        # Define query parameters
        query_params = [
            bigquery.ScalarQueryParameter("start_time", "TIMESTAMP", start_time),
            bigquery.ScalarQueryParameter("end_time", "TIMESTAMP", end_time),
            bigquery.ScalarQueryParameter("sample_size", "INT64", sample_size),
        ]

        if dry_run:
            return 0, [], 0.1

        # Execute threshold query
        client = self._get_bigquery_client()
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = client.query(query, job_config=job_config)
        results = list(query_job.result())

        query_time = (datetime.now(timezone.utc) - query_start).total_seconds()

        match_count = len(results)
        sample_results = []

        for row in results:
            result_dict = dict(row.items())
            result_dict["threshold_violated"] = True
            result_dict["threshold_config"] = {
                "count": threshold_count,
                "window_seconds": window_seconds,
                "group_by": group_by,
            }
            sample_results.append(result_dict)

        return match_count, sample_results, query_time

    async def _execute_anomaly_rule(
        self,
        rule: Rule,
        start_time: datetime,
        end_time: datetime,
        sample_size: int,
        dry_run: bool,
    ) -> Tuple[int, List[Dict[str, Any]], float]:
        """Execute an anomaly detection rule."""
        if not rule.conditions:
            return 0, [], 0.0

        query_start = datetime.now(timezone.utc)

        # For now, implement a simple statistical anomaly detection
        # In production, this would integrate with ML models

        # Find relevant conditions
        metric_condition = next(
            (c for c in rule.conditions if c.field == "metric"), None
        )
        table_condition = next((c for c in rule.conditions if c.field == "table"), None)
        sensitivity_condition = next(
            (c for c in rule.conditions if c.field == "sensitivity"), None
        )

        metric = metric_condition.value if metric_condition else "value"
        table_name = (
            table_condition.value if table_condition else "metrics.application_metrics"
        )
        sensitivity = (
            float(sensitivity_condition.value) if sensitivity_condition else 2.0
        )  # Standard deviations

        # Build query using secure query builder
        try:
            baseline_query = SecureQueryBuilder.build_anomaly_detection_query(
                table_name,
                metric,
                "@sensitivity",
                {
                    "baseline_start_time": "@baseline_start_time",
                    "start_time": "@start_time",
                    "end_time": "@end_time"
                },
                limit=sample_size
            )
            # Replace the limit placeholder with parameter
            baseline_query = baseline_query.replace(f"LIMIT {sample_size}", "LIMIT @sample_size")
        except ValueError as e:
            logger.error("Invalid table or metric name: %s", e)
            return 0, [], 0.0

        # Define query parameters
        query_params = [
            bigquery.ScalarQueryParameter(
                "baseline_start_time", "TIMESTAMP", start_time - timedelta(days=7)
            ),
            bigquery.ScalarQueryParameter("start_time", "TIMESTAMP", start_time),
            bigquery.ScalarQueryParameter("end_time", "TIMESTAMP", end_time),
            bigquery.ScalarQueryParameter("sensitivity", "FLOAT64", sensitivity),
            bigquery.ScalarQueryParameter("sample_size", "INT64", sample_size),
        ]

        if dry_run:
            return 0, [], 0.1

        # Execute anomaly detection query with parameters
        client = self._get_bigquery_client()
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = client.query(baseline_query, job_config=job_config)
        results = list(query_job.result())

        query_time = (datetime.now(timezone.utc) - query_start).total_seconds()

        match_count = len(results)
        sample_results = []

        for row in results:
            result_dict = dict(row.items())
            for key, value in result_dict.items():
                if isinstance(value, datetime):
                    result_dict[key] = value.isoformat()
            result_dict["anomaly_type"] = "statistical"
            result_dict["sensitivity"] = sensitivity
            sample_results.append(result_dict)

        return match_count, sample_results, query_time

    async def _execute_correlation_rule(
        self,
        rule: Rule,
        start_time: datetime,
        end_time: datetime,
        sample_size: int,
        dry_run: bool,
    ) -> Tuple[int, List[Dict[str, Any]], float]:
        """Execute a correlation rule."""
        if not rule.correlation:
            return 0, [], 0.0

        query_start = datetime.now(timezone.utc)

        # Extract correlation configuration
        if hasattr(rule.correlation, "model_dump"):
            correlation_dict = rule.correlation.model_dump()
            events = correlation_dict.get("events", [])
            time_window = correlation_dict.get("time_window_seconds", 300)
            correlation_field = correlation_dict.get("correlation_field", "user_id")
        else:
            events = getattr(rule.correlation, "events", [])
            time_window = getattr(rule.correlation, "time_window_seconds", 300)
            correlation_field = getattr(
                rule.correlation, "correlation_field", "user_id"
            )

        if len(events) < 2:
            return 0, [], 0.0

        # Build correlation query using self-joins
        # This is a simplified example - production would be more sophisticated
        base_event = events[0]
        correlated_events = events[1:]

        query_parts = []
        query_params = []

        for i, event in enumerate(correlated_events):
            # Build query using secure query builder
            try:
                query_template = SecureQueryBuilder.build_correlation_query(
                    base_event.get('table', 'logs.application_logs'),
                    event.get('table', 'logs.application_logs'),
                    correlation_field,
                    i,
                    f"@time_window_{i}",
                    {
                        f"start_time_{i}": f"@start_time_{i}",
                        f"end_time_{i}": f"@end_time_{i}"
                    }
                )
                query_parts.append(query_template)
            except ValueError as e:
                logger.error("Invalid table or field name in correlation: %s", e)
                return 0, [], 0.0

            # Add parameters for this query part
            query_params.extend(
                [
                    bigquery.ScalarQueryParameter(
                        f"time_window_{i}", "INT64", time_window
                    ),
                    bigquery.ScalarQueryParameter(
                        f"start_time_{i}", "TIMESTAMP", start_time
                    ),
                    bigquery.ScalarQueryParameter(
                        f"end_time_{i}", "TIMESTAMP", end_time
                    ),
                    bigquery.ScalarQueryParameter(
                        f"base_event_type_{i}",
                        "STRING",
                        base_event.get("event_type", "unknown"),
                    ),
                    bigquery.ScalarQueryParameter(
                        f"event_type_{i}", "STRING", event.get("event_type", "unknown")
                    ),
                ]
            )

        query = " UNION ALL ".join(query_parts) + " LIMIT @sample_size"
        query_params.append(
            bigquery.ScalarQueryParameter("sample_size", "INT64", sample_size)
        )

        if dry_run:
            return 0, [], 0.1

        # Execute correlation query with parameters
        client = self._get_bigquery_client()
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = client.query(query, job_config=job_config)
        results = list(query_job.result())

        query_time = (datetime.now(timezone.utc) - query_start).total_seconds()

        match_count = len(results)
        sample_results = []

        for row in results:
            result_dict = dict(row.items())
            for key, value in result_dict.items():
                if isinstance(value, datetime):
                    result_dict[key] = value.isoformat()
            result_dict["correlation_type"] = "temporal"
            result_dict["time_window_seconds"] = time_window
            sample_results.append(result_dict)

        return match_count, sample_results, query_time
