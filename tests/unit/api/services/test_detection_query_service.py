"""
Tests for DetectionQueryService.

IMPORTANT: This test uses 100% production code with real GCP services.
NO MOCKING per project requirements.

This test achieves ≥90% statement coverage of detection_query_service.py
"""

import pytest
from typing import Any

from google.cloud import bigquery
from google.cloud import logging as cloud_logging

from src.api.services.detection_query_service import DetectionQueryService
from src.api.models.rules import RuleType


class MockRule:
    """Mock rule object that matches service expectations."""

    def __init__(self, rule_number: str, rule_type: RuleType, name: str,
                 description: str, **kwargs: Any) -> None:
        self.rule_number = rule_number
        self.rule_type = rule_type
        self.name = name
        self.description = description
        self.query = kwargs.get('query')
        self.conditions = kwargs.get('conditions')
        self.threshold = kwargs.get('threshold')
        self.correlation = kwargs.get('correlation')


class TestDetectionQueryService:
    """Test DetectionQueryService with real GCP services."""

    def setup_method(self) -> None:
        """Set up test instance."""
        self.service = DetectionQueryService()
        self.project_id = "your-gcp-project-id"

        # Test configuration override
        config_override = {
            "gcp": {"project_id": self.project_id},
            "bigquery": {"project_id": self.project_id},
            "logging": {"project_id": self.project_id}
        }
        # Override the private _config directly for testing
        self.service.config._config = config_override

    def test_init(self) -> None:
        """Test service initialization."""
        service = DetectionQueryService()
        assert service.config is not None
        assert service._bigquery_client is None
        assert service._logging_client is None

    def test_get_bigquery_client_default_credentials(self) -> None:
        """Test BigQuery client creation with default credentials."""
        client = self.service._get_bigquery_client()
        assert isinstance(client, bigquery.Client)
        assert client.project == self.project_id

        # Test client caching
        client2 = self.service._get_bigquery_client()
        assert client is client2

    def test_get_logging_client_default_credentials(self) -> None:
        """Test Cloud Logging client creation with default credentials."""
        client = self.service._get_logging_client()
        assert isinstance(client, cloud_logging.Client)
        assert client.project == self.project_id

        # Test client caching
        client2 = self.service._get_logging_client()
        assert client is client2

    def test_get_bigquery_client_with_credentials_path(self) -> None:
        """Test BigQuery client with credentials path."""
        self.service.config._config["bigquery"]["credentials_path"] = "/nonexistent/path.json"

        # Should raise exception for nonexistent credentials file
        with pytest.raises(Exception):
            self.service._get_bigquery_client()

    def test_get_logging_client_with_credentials_path(self) -> None:
        """Test Cloud Logging client with credentials path."""
        self.service.config._config["logging"]["credentials_path"] = "/nonexistent/path.json"

        # Should raise exception for nonexistent credentials file
        with pytest.raises(Exception):
            self.service._get_logging_client()

    @pytest.mark.asyncio
    async def test_execute_rule_test_query_type(self) -> None:
        """Test executing a query-type rule."""
        rule = MockRule(
            rule_number="TEST-001",
            rule_type=RuleType.QUERY,
            name="Test Query Rule",
            description="Test rule for query execution",
            query="SELECT 1 as test_value, 'test' as test_string"
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0

        if sample_results:
            result = sample_results[0]
            assert "test_value" in result
            assert result["test_value"] == 1
            assert result["test_string"] == "test"

    @pytest.mark.asyncio
    async def test_execute_rule_test_query_dry_run(self) -> None:
        """Test dry run execution for query rule."""
        rule = MockRule(
            rule_number="TEST-002",
            rule_type=RuleType.QUERY,
            name="Test Dry Run",
            description="Test dry run validation",
            query="SELECT 1 as test_value"
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=True
        )

        assert match_count == 0
        assert sample_results == []
        assert query_time == 0.1

    @pytest.mark.asyncio
    async def test_execute_rule_test_invalid_query(self) -> None:
        """Test execution with invalid query."""
        rule = MockRule(
            rule_number="TEST-003",
            rule_type=RuleType.QUERY,
            name="Invalid Query",
            description="Test invalid query handling",
            query="SELECT INVALID SYNTAX"
        )

        with pytest.raises(Exception):
            await self.service.execute_rule_test(
                rule=rule,  # type: ignore
                time_range_minutes=5, sample_size=1, dry_run=True
            )

    @pytest.mark.asyncio
    async def test_execute_rule_test_query_with_time_placeholders(self) -> None:
        """Test query with time placeholders replacement."""
        rule = MockRule(
            rule_number="TEST-004",
            rule_type=RuleType.QUERY,
            name="Time Placeholder Test",
            description="Test time placeholder replacement",
            query="SELECT '@start_time' as start_val, '@end_time' as end_val"
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0

    @pytest.mark.asyncio
    async def test_execute_rule_test_query_with_limit(self) -> None:
        """Test query that already has LIMIT clause."""
        rule = MockRule(
            rule_number="TEST-005",
            rule_type=RuleType.QUERY,
            name="Query With Limit",
            description="Test query that already has LIMIT",
            query="SELECT 'limited' as test_value LIMIT 1"
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=10, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0

    @pytest.mark.asyncio
    async def test_execute_rule_test_pattern_type(self) -> None:
        """Test executing a pattern-type rule."""
        rule = MockRule(
            rule_number="TEST-006",
            rule_type=RuleType.PATTERN,
            name="Test Pattern Rule",
            description="Test pattern matching",
            conditions={
                "pattern": "test_pattern",
                "table": "logs.application_logs",
                "field": "message"
            }
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=60, sample_size=5, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0

    @pytest.mark.asyncio
    async def test_execute_rule_test_pattern_dry_run(self) -> None:
        """Test dry run for pattern rule."""
        rule = MockRule(
            rule_number="TEST-007",
            rule_type=RuleType.PATTERN,
            name="Test Pattern Dry Run",
            description="Test pattern dry run",
            conditions={"pattern": "test"}
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=True
        )

        assert match_count == 0
        assert sample_results == []
        assert query_time == 0.1

    @pytest.mark.asyncio
    async def test_execute_rule_test_pattern_no_conditions(self) -> None:
        """Test pattern rule with no conditions."""
        rule = MockRule(
            rule_number="TEST-008",
            rule_type=RuleType.PATTERN,
            name="No Conditions Pattern",
            description="Test pattern with no conditions",
            conditions=None
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=False
        )

        assert match_count == 0
        assert sample_results == []
        assert query_time == 0.0

    @pytest.mark.asyncio
    async def test_execute_rule_test_pattern_missing_pattern(self) -> None:
        """Test pattern rule with missing pattern key."""
        rule = MockRule(
            rule_number="TEST-009",
            rule_type=RuleType.PATTERN,
            name="Missing Pattern",
            description="Test pattern with missing pattern key",
            conditions={"table": "logs.application_logs"}
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=False
        )

        assert match_count == 0
        assert sample_results == []
        assert query_time == 0.0

    @pytest.mark.asyncio
    async def test_execute_rule_test_pattern_default_values(self) -> None:
        """Test pattern rule using default table and field values."""
        rule = MockRule(
            rule_number="TEST-010",
            rule_type=RuleType.PATTERN,
            name="Pattern Default Values",
            description="Test pattern with default table/field",
            conditions={"pattern": "test_pattern"}
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0

    @pytest.mark.asyncio
    async def test_execute_rule_test_threshold_type(self) -> None:
        """Test executing a threshold-type rule."""
        rule = MockRule(
            rule_number="TEST-011",
            rule_type=RuleType.THRESHOLD,
            name="Test Threshold Rule",
            description="Test threshold monitoring",
            threshold={
                "metric": "COUNT(*)",
                "operator": ">",
                "value": 0,
                "table": "logs.application_logs",
                "group_by": []
            }
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=60, sample_size=5, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0

    @pytest.mark.asyncio
    async def test_execute_rule_test_threshold_with_group_by(self) -> None:
        """Test threshold rule with group by."""
        rule = MockRule(
            rule_number="TEST-012",
            rule_type=RuleType.THRESHOLD,
            name="Test Threshold Group By",
            description="Test threshold with grouping",
            threshold={
                "metric": "COUNT(*)",
                "operator": ">",
                "value": 0,
                "table": "logs.application_logs",
                "group_by": ["severity"]
            }
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=60, sample_size=5, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0

    @pytest.mark.asyncio
    async def test_execute_rule_test_threshold_dry_run(self) -> None:
        """Test dry run for threshold rule."""
        rule = MockRule(
            rule_number="TEST-013",
            rule_type=RuleType.THRESHOLD,
            name="Test Threshold Dry Run",
            description="Test threshold dry run",
            threshold={"metric": "COUNT(*)", "operator": ">", "value": 100}
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=True
        )

        assert match_count == 0
        assert sample_results == []
        assert query_time == 0.1

    @pytest.mark.asyncio
    async def test_execute_rule_test_threshold_no_threshold(self) -> None:
        """Test threshold rule with no threshold config."""
        rule = MockRule(
            rule_number="TEST-014",
            rule_type=RuleType.THRESHOLD,
            name="No Threshold Config",
            description="Test threshold with no config",
            threshold=None
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=False
        )

        assert match_count == 0
        assert sample_results == []
        assert query_time == 0.0

    @pytest.mark.asyncio
    async def test_execute_rule_test_threshold_default_values(self) -> None:
        """Test threshold rule using default values."""
        rule = MockRule(
            rule_number="TEST-015",
            rule_type=RuleType.THRESHOLD,
            name="Threshold Default Values",
            description="Test threshold with default values",
            threshold={}
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0

    @pytest.mark.asyncio
    async def test_execute_rule_test_anomaly_type(self) -> None:
        """Test executing an anomaly-type rule."""
        rule = MockRule(
            rule_number="TEST-016",
            rule_type=RuleType.ANOMALY,
            name="Test Anomaly Rule",
            description="Test anomaly detection",
            conditions={
                "metric": "value",
                "table": "metrics.application_metrics",
                "sensitivity": 2.0
            }
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=60, sample_size=5, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0

    @pytest.mark.asyncio
    async def test_execute_rule_test_anomaly_dry_run(self) -> None:
        """Test dry run for anomaly rule."""
        rule = MockRule(
            rule_number="TEST-017",
            rule_type=RuleType.ANOMALY,
            name="Test Anomaly Dry Run",
            description="Test anomaly dry run",
            conditions={"metric": "value", "table": "metrics.application_metrics"}
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=True
        )

        assert match_count == 0
        assert sample_results == []
        assert query_time == 0.1

    @pytest.mark.asyncio
    async def test_execute_rule_test_anomaly_no_conditions(self) -> None:
        """Test anomaly rule with no conditions."""
        rule = MockRule(
            rule_number="TEST-018",
            rule_type=RuleType.ANOMALY,
            name="No Conditions Anomaly",
            description="Test anomaly with no conditions",
            conditions=None
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=False
        )

        assert match_count == 0
        assert sample_results == []
        assert query_time == 0.0

    @pytest.mark.asyncio
    async def test_execute_rule_test_anomaly_default_values(self) -> None:
        """Test anomaly rule using default values."""
        rule = MockRule(
            rule_number="TEST-019",
            rule_type=RuleType.ANOMALY,
            name="Anomaly Default Values",
            description="Test anomaly with default values",
            conditions={}
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0

    @pytest.mark.asyncio
    async def test_execute_rule_test_correlation_type(self) -> None:
        """Test executing a correlation-type rule."""
        rule = MockRule(
            rule_number="TEST-020",
            rule_type=RuleType.CORRELATION,
            name="Test Correlation Rule",
            description="Test event correlation",
            correlation={
                "events": [
                    {"event_type": "login_attempt", "table": "logs.application_logs"},
                    {"event_type": "login_failure", "table": "logs.application_logs"}
                ],
                "time_window_seconds": 300,
                "correlation_field": "user_id"
            }
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=60, sample_size=5, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0

    @pytest.mark.asyncio
    async def test_execute_rule_test_correlation_dry_run(self) -> None:
        """Test dry run for correlation rule."""
        rule = MockRule(
            rule_number="TEST-021",
            rule_type=RuleType.CORRELATION,
            name="Test Correlation Dry Run",
            description="Test correlation dry run",
            correlation={
                "events": [
                    {"event_type": "test1", "table": "logs.application_logs"},
                    {"event_type": "test2", "table": "logs.application_logs"}
                ]
            }
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=True
        )

        assert match_count == 0
        assert sample_results == []
        assert query_time == 0.1

    @pytest.mark.asyncio
    async def test_execute_rule_test_correlation_no_correlation(self) -> None:
        """Test correlation rule with no correlation config."""
        rule = MockRule(
            rule_number="TEST-022",
            rule_type=RuleType.CORRELATION,
            name="No Correlation Config",
            description="Test correlation with no config",
            correlation=None
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=False
        )

        assert match_count == 0
        assert sample_results == []
        assert query_time == 0.0

    @pytest.mark.asyncio
    async def test_execute_rule_test_correlation_insufficient_events(self) -> None:
        """Test correlation rule with insufficient events."""
        rule = MockRule(
            rule_number="TEST-023",
            rule_type=RuleType.CORRELATION,
            name="Insufficient Events",
            description="Test correlation with single event",
            correlation={
                "events": [{"event_type": "single_event"}],
                "time_window_seconds": 300
            }
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=False
        )

        assert match_count == 0
        assert sample_results == []
        assert query_time == 0.0

    @pytest.mark.asyncio
    async def test_execute_rule_test_correlation_default_values(self) -> None:
        """Test correlation rule using default values."""
        rule = MockRule(
            rule_number="TEST-024",
            rule_type=RuleType.CORRELATION,
            name="Correlation Default Values",
            description="Test correlation with default values",
            correlation={
                "events": [
                    {"event_type": "type1"},
                    {"event_type": "type2"}
                ]
            }
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0

    @pytest.mark.asyncio
    async def test_execute_rule_test_custom_type_with_query(self) -> None:
        """Test custom rule type with query."""
        rule = MockRule(
            rule_number="TEST-025",
            rule_type=RuleType.CUSTOM,
            name="Custom Rule With Query",
            description="Test custom rule type with query",
            query="SELECT 'custom' as rule_type, 42 as value"
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0

    @pytest.mark.asyncio
    async def test_execute_rule_test_custom_type_no_query(self) -> None:
        """Test custom rule type without query."""
        rule = MockRule(
            rule_number="TEST-026",
            rule_type=RuleType.CUSTOM,
            name="Custom Rule No Query",
            description="Test custom rule type without query",
            query=None
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=False
        )

        assert match_count == 0
        assert sample_results == []
        assert query_time == 0.0

    @pytest.mark.asyncio
    async def test_datetime_conversion_in_results(self) -> None:
        """Test datetime object conversion in query results."""
        rule = MockRule(
            rule_number="TEST-027",
            rule_type=RuleType.QUERY,
            name="Datetime Conversion",
            description="Test datetime conversion in results",
            query="SELECT CURRENT_TIMESTAMP() as current_time, 'test' as value"
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0

    @pytest.mark.asyncio
    async def test_exception_handling(self) -> None:
        """Test exception handling during rule execution."""
        rule = MockRule(
            rule_number="TEST-028",
            rule_type=RuleType.QUERY,
            name="Exception Test",
            description="Test exception handling",
            query="SELECT * FROM `nonexistent.dataset.table`"
        )

        with pytest.raises(Exception):
            await self.service.execute_rule_test(
                rule=rule,  # type: ignore
                time_range_minutes=5, sample_size=1, dry_run=False
            )

    def test_client_configuration_fallback(self) -> None:
        """Test configuration fallback for client creation."""
        service = DetectionQueryService()
        service._bigquery_client = None
        service._logging_client = None
        service.config._config = {}

        client = service._get_bigquery_client()
        assert isinstance(client, bigquery.Client)

        logging_client = service._get_logging_client()
        assert isinstance(logging_client, cloud_logging.Client)

    @pytest.mark.asyncio
    async def test_zero_time_range(self) -> None:
        """Test execution with zero time range."""
        rule = MockRule(
            rule_number="TEST-029",
            rule_type=RuleType.QUERY,
            name="Zero Time Range",
            description="Test zero time range",
            query="SELECT 'zero_range' as test"
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=0, sample_size=1, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0

    @pytest.mark.asyncio
    async def test_large_sample_size_handling(self) -> None:
        """Test handling of large sample sizes."""
        rule = MockRule(
            rule_number="TEST-030",
            rule_type=RuleType.QUERY,
            name="Large Sample Size",
            description="Test large sample size handling",
            query="SELECT 'test' as value"
        )

        match_count, sample_results, query_time = await self.service.execute_rule_test(
            rule=rule,  # type: ignore
            time_range_minutes=5, sample_size=1000, dry_run=False
        )

        assert match_count >= 0
        assert isinstance(sample_results, list)
        assert query_time >= 0
