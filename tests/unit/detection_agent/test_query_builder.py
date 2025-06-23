"""
Tests for the detection agent query builder.

This module tests the QueryBuilder class that constructs BigQuery queries
for detection rules with proper parameter substitution.
"""

from datetime import datetime, timezone

import pytest

from src.detection_agent.query_builder import QueryBuilder


class TestQueryBuilder:
    """Test cases for QueryBuilder."""

    def test_build_query_basic_substitution(self) -> None:
        """Test basic parameter substitution in query template."""
        template = """
        SELECT * FROM `{project_id}.{dataset_id}.logs`
        WHERE timestamp BETWEEN '{last_scan_time}' AND '{current_time}'
        """

        project_id = "test-project"
        dataset_id = "test-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)

        result = QueryBuilder.build_query(
            template, project_id, dataset_id, last_scan_time, current_time
        )

        expected = """
        SELECT * FROM `test-project.test-dataset.logs`
        WHERE timestamp BETWEEN '2024-01-01T10:00:00+00:00' AND '2024-01-01T11:00:00+00:00'
        """

        assert result == expected

    def test_build_query_with_additional_params(self) -> None:
        """Test query building with additional custom parameters."""
        template = """
        SELECT * FROM `{project_id}.{dataset_id}.{table_name}`
        WHERE timestamp BETWEEN '{last_scan_time}' AND '{current_time}'
        AND severity = '{severity}'
        AND user_id = {user_id}
        """

        project_id = "prod-project"
        dataset_id = "security-logs"
        last_scan_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        additional_params = {
            "table_name": "access_logs",
            "severity": "HIGH",
            "user_id": 12345,
        }

        result = QueryBuilder.build_query(
            template,
            project_id,
            dataset_id,
            last_scan_time,
            current_time,
            additional_params,
        )

        expected = """
        SELECT * FROM `prod-project.security-logs.access_logs`
        WHERE timestamp BETWEEN '2024-01-01T12:00:00+00:00' AND '2024-01-01T13:00:00+00:00'
        AND severity = 'HIGH'
        AND user_id = 12345
        """

        assert result == expected

    def test_build_query_empty_template(self) -> None:
        """Test handling of empty query template."""
        template = ""

        project_id = "test-project"
        dataset_id = "test-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)

        result = QueryBuilder.build_query(
            template, project_id, dataset_id, last_scan_time, current_time
        )

        assert result == ""

    def test_build_query_no_placeholders(self) -> None:
        """Test query template without any placeholders."""
        template = "SELECT * FROM static_table WHERE id = 1"

        project_id = "test-project"
        dataset_id = "test-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)

        result = QueryBuilder.build_query(
            template, project_id, dataset_id, last_scan_time, current_time
        )

        assert result == template

    def test_build_query_special_characters_in_params(self) -> None:
        """Test parameter values containing special characters."""
        template = (
            "SELECT * FROM `{project_id}.{dataset_id}.logs` WHERE message = '{message}'"
        )

        project_id = "test-project"
        dataset_id = "test-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        additional_params = {
            "message": "User's \"special\" message with {braces} and 'quotes'"
        }

        result = QueryBuilder.build_query(
            template,
            project_id,
            dataset_id,
            last_scan_time,
            current_time,
            additional_params,
        )

        expected = "SELECT * FROM `test-project.test-dataset.logs` WHERE message = 'User's \"special\" message with {braces} and 'quotes''"

        assert result == expected

    def test_build_query_missing_placeholder_raises_error(self) -> None:
        """Test that missing placeholders in template raise KeyError."""
        template = "SELECT * FROM `{project_id}.{dataset_id}.{missing_table}`"

        project_id = "test-project"
        dataset_id = "test-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(KeyError, match="missing_table"):
            QueryBuilder.build_query(
                template, project_id, dataset_id, last_scan_time, current_time
            )

    def test_build_query_naive_datetime(self) -> None:
        """Test handling of naive datetime objects (without timezone)."""
        template = "SELECT * FROM logs WHERE timestamp BETWEEN '{last_scan_time}' AND '{current_time}'"

        project_id = "test-project"
        dataset_id = "test-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 0, 0)  # No timezone
        current_time = datetime(2024, 1, 1, 11, 0, 0)  # No timezone

        result = QueryBuilder.build_query(
            template, project_id, dataset_id, last_scan_time, current_time
        )

        expected = "SELECT * FROM logs WHERE timestamp BETWEEN '2024-01-01T10:00:00' AND '2024-01-01T11:00:00'"

        assert result == expected

    def test_build_query_microseconds_in_datetime(self) -> None:
        """Test that microseconds are preserved in datetime formatting."""
        template = "SELECT * FROM logs WHERE timestamp = '{last_scan_time}'"

        project_id = "test-project"
        dataset_id = "test-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 30, 45, 123456, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)

        result = QueryBuilder.build_query(
            template, project_id, dataset_id, last_scan_time, current_time
        )

        expected = (
            "SELECT * FROM logs WHERE timestamp = '2024-01-01T10:30:45.123456+00:00'"
        )

        assert result == expected

    def test_build_query_override_default_params(self) -> None:
        """Test that additional params can override default parameters."""
        template = "SELECT * FROM `{project_id}.{dataset_id}.logs`"

        project_id = "original-project"
        dataset_id = "original-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        additional_params = {
            "project_id": "overridden-project",
            "dataset_id": "overridden-dataset",
        }

        result = QueryBuilder.build_query(
            template,
            project_id,
            dataset_id,
            last_scan_time,
            current_time,
            additional_params,
        )

        expected = "SELECT * FROM `overridden-project.overridden-dataset.logs`"

        assert result == expected

    def test_build_query_complex_nested_template(self) -> None:
        """Test complex query with nested structures and multiple parameters."""
        template = """
        WITH security_events AS (
            SELECT
                user_id,
                event_type,
                timestamp,
                STRUCT(
                    '{severity}' AS severity,
                    {risk_score} AS risk_score,
                    '{region}' AS region
                ) AS metadata
            FROM `{project_id}.{dataset_id}.{table_name}`
            WHERE timestamp BETWEEN '{last_scan_time}' AND '{current_time}'
                AND region IN ({regions})
        )
        SELECT * FROM security_events
        WHERE metadata.risk_score > {threshold}
        ORDER BY timestamp DESC
        LIMIT {limit}
        """

        project_id = "security-project"
        dataset_id = "threat-detection"
        last_scan_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 23, 59, 59, tzinfo=timezone.utc)
        additional_params = {
            "table_name": "security_logs",
            "severity": "CRITICAL",
            "risk_score": 85.5,
            "region": "us-east1",
            "regions": "'us-east1', 'us-west2', 'europe-west1'",
            "threshold": 75,
            "limit": 100,
        }

        result = QueryBuilder.build_query(
            template,
            project_id,
            dataset_id,
            last_scan_time,
            current_time,
            additional_params,
        )

        # Check that all parameters were substituted correctly
        assert "security-project.threat-detection.security_logs" in result
        assert "'CRITICAL' AS severity" in result
        assert "85.5 AS risk_score" in result
        assert "'us-east1' AS region" in result
        assert "2024-01-01T00:00:00+00:00" in result
        assert "2024-01-01T23:59:59+00:00" in result
        assert "region IN ('us-east1', 'us-west2', 'europe-west1')" in result
        assert "metadata.risk_score > 75" in result
        assert "LIMIT 100" in result

    def test_build_query_unicode_characters(self) -> None:
        """Test handling of Unicode characters in parameters."""
        template = "SELECT * FROM logs WHERE user_name = '{user_name}' AND message = '{message}'"

        project_id = "test-project"
        dataset_id = "test-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        additional_params = {"user_name": "José García", "message": "Hello 世界! 🌍"}

        result = QueryBuilder.build_query(
            template,
            project_id,
            dataset_id,
            last_scan_time,
            current_time,
            additional_params,
        )

        expected = "SELECT * FROM logs WHERE user_name = 'José García' AND message = 'Hello 世界! 🌍'"

        assert result == expected

    def test_build_query_numeric_types_in_params(self) -> None:
        """Test various numeric types in additional parameters."""
        template = """
        SELECT * FROM metrics
        WHERE int_value = {int_val}
        AND float_value = {float_val}
        AND bool_value = {bool_val}
        AND null_value IS {null_val}
        """

        project_id = "test-project"
        dataset_id = "test-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        additional_params = {
            "int_val": 42,
            "float_val": 3.14159,
            "bool_val": True,
            "null_val": None,
        }

        result = QueryBuilder.build_query(
            template,
            project_id,
            dataset_id,
            last_scan_time,
            current_time,
            additional_params,
        )

        expected = """
        SELECT * FROM metrics
        WHERE int_value = 42
        AND float_value = 3.14159
        AND bool_value = True
        AND null_value IS None
        """

        assert result == expected

    def test_build_query_empty_additional_params(self) -> None:
        """Test with explicitly empty additional parameters dict."""
        template = "SELECT * FROM `{project_id}.{dataset_id}.logs`"

        project_id = "test-project"
        dataset_id = "test-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)

        result = QueryBuilder.build_query(
            template, project_id, dataset_id, last_scan_time, current_time, {}
        )

        expected = "SELECT * FROM `test-project.test-dataset.logs`"

        assert result == expected

    def test_build_query_sql_injection_safe(self) -> None:
        """Test that the method doesn't perform SQL escaping (that's caller's responsibility)."""
        template = "SELECT * FROM logs WHERE user_input = '{user_input}'"

        project_id = "test-project"
        dataset_id = "test-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        additional_params = {"user_input": "'; DROP TABLE users; --"}

        result = QueryBuilder.build_query(
            template,
            project_id,
            dataset_id,
            last_scan_time,
            current_time,
            additional_params,
        )

        # The QueryBuilder should NOT escape SQL - that's the caller's responsibility
        expected = "SELECT * FROM logs WHERE user_input = ''; DROP TABLE users; --'"

        assert result == expected

    def test_build_query_multiline_preservation(self) -> None:
        """Test that multiline formatting is preserved in the output."""
        template = """
        -- Detection query for suspicious activity
        WITH base_data AS (
            SELECT
                user_id,
                COUNT(*) as event_count
            FROM `{project_id}.{dataset_id}.events`
            WHERE timestamp BETWEEN '{last_scan_time}' AND '{current_time}'
            GROUP BY user_id
        )
        SELECT * FROM base_data
        WHERE event_count > {threshold}
        """

        project_id = "test-project"
        dataset_id = "test-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        additional_params = {"threshold": 100}

        result = QueryBuilder.build_query(
            template,
            project_id,
            dataset_id,
            last_scan_time,
            current_time,
            additional_params,
        )

        # Check that the structure is preserved
        assert "-- Detection query for suspicious activity" in result
        assert "WITH base_data AS (" in result
        assert result.count("\n") == template.count("\n")

    def test_build_query_repeated_placeholders(self) -> None:
        """Test template with repeated placeholders."""
        template = """
        SELECT * FROM `{project_id}.{dataset_id}.logs`
        WHERE project = '{project_id}'
        AND dataset = '{dataset_id}'
        AND timestamp BETWEEN '{last_scan_time}' AND '{current_time}'
        UNION ALL
        SELECT * FROM `{project_id}.{dataset_id}.archived_logs`
        WHERE project = '{project_id}'
        AND dataset = '{dataset_id}'
        AND timestamp BETWEEN '{last_scan_time}' AND '{current_time}'
        """

        project_id = "my-project"
        dataset_id = "my-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)

        result = QueryBuilder.build_query(
            template, project_id, dataset_id, last_scan_time, current_time
        )

        # Count occurrences of substituted values
        # project_id appears 4 times (2 in table refs as part of `my-project.my-dataset`, 2 standalone)
        assert result.count("my-project") == 4
        # dataset_id appears 4 times (2 in table refs as part of `my-project.my-dataset`, 2 standalone)
        assert result.count("my-dataset") == 4
        assert result.count("2024-01-01T10:00:00+00:00") == 2
        assert result.count("2024-01-01T11:00:00+00:00") == 2

    def test_build_query_partial_formatting(self) -> None:
        """Test template with mixed format strings (some using {}, some not)."""
        template = """
        SELECT
            PARSE_TIMESTAMP('%Y-%m-%d', date_string) as parsed_date,
            *
        FROM `{project_id}.{dataset_id}.logs`
        WHERE timestamp BETWEEN '{last_scan_time}' AND '{current_time}'
        AND severity IN ('HIGH', 'CRITICAL')
        """

        project_id = "test-project"
        dataset_id = "test-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)

        result = QueryBuilder.build_query(
            template, project_id, dataset_id, last_scan_time, current_time
        )

        # Ensure % format strings are preserved
        assert "PARSE_TIMESTAMP('%Y-%m-%d', date_string)" in result
        # And our placeholders are substituted
        assert "`test-project.test-dataset.logs`" in result

    def test_build_query_edge_case_parameters(self) -> None:
        """Test edge cases for parameter values."""
        template = "VALUES ({empty_str}, {zero}, {false_bool}, {large_num}, {negative})"

        project_id = "test-project"
        dataset_id = "test-dataset"
        last_scan_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        additional_params = {
            "empty_str": "",
            "zero": 0,
            "false_bool": False,
            "large_num": 9223372036854775807,  # max int64
            "negative": -1.23e-10,
        }

        result = QueryBuilder.build_query(
            template,
            project_id,
            dataset_id,
            last_scan_time,
            current_time,
            additional_params,
        )

        expected = "VALUES (, 0, False, 9223372036854775807, -1.23e-10)"

        assert result == expected
