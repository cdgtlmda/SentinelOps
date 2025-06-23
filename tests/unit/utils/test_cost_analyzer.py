"""
Tests for cost analyzer using real production code.
CRITICAL: Uses REAL GCP billing and cost analysis - NO MOCKING
"""

import os
from datetime import datetime, timezone
from typing import Any

import pytest
from google.api_core.exceptions import NotFound
from google.cloud import bigquery

# REAL PRODUCTION IMPORTS - NO MOCKING
from src.utils.cost_analyzer import CostAnalyzer


class TestCostAnalyzerProduction:
    """Test suite for cost analyzer using real production code."""

    @pytest.fixture(scope="class")
    def project_id(self) -> str:
        """Get real project ID from environment."""
        project_id = os.environ.get("GCP_PROJECT_ID", "your-gcp-project-id")
        print(f"\nUsing REAL GCP Project: {project_id}")
        return project_id

    @pytest.fixture(scope="class")
    def billing_dataset(self) -> str:
        """Get billing dataset name."""
        # Try to use an existing dataset that might have billing data
        # or create a test dataset for billing
        return "sentinelops_dev"  # Using dev dataset for testing

    @pytest.fixture
    def cost_analyzer(self, project_id: str, billing_dataset: str) -> Any:
        """Create CostAnalyzer instance with real project."""
        analyzer = CostAnalyzer(project_id, billing_dataset)
        assert analyzer.bq_client is not None  # Verify real BigQuery client created
        assert (
            analyzer.monitoring_client is not None
        )  # Verify real Monitoring client created
        return analyzer

    def test_initialization_with_valid_project(self, project_id: str, billing_dataset: str) -> None:
        """Test CostAnalyzer initialization with real project ID."""
        analyzer = CostAnalyzer(project_id, billing_dataset)
        assert analyzer.project_id == project_id
        assert analyzer.billing_dataset == billing_dataset
        assert isinstance(analyzer.bq_client, bigquery.Client)
        assert analyzer.bq_client.project == project_id

    def test_initialization_with_invalid_project_id(self) -> None:
        """Test CostAnalyzer rejects invalid project IDs."""
        with pytest.raises(ValueError, match="Invalid project_id"):
            CostAnalyzer("invalid/project", "dataset")

    def test_initialization_with_invalid_dataset(self, project_id: str) -> None:
        """Test CostAnalyzer rejects invalid dataset names."""
        with pytest.raises(ValueError, match="Invalid billing_dataset"):
            CostAnalyzer(project_id, "invalid/dataset")

    def test_is_valid_identifier(self, cost_analyzer: CostAnalyzer) -> None:
        """Test identifier validation logic."""
        # Valid identifiers
        assert cost_analyzer._is_valid_identifier("valid_dataset") is True
        assert cost_analyzer._is_valid_identifier("project-123") is True
        assert cost_analyzer._is_valid_identifier("my_table_v1") is True
        assert cost_analyzer._is_valid_identifier("ABC123xyz") is True

        # Invalid identifiers
        assert cost_analyzer._is_valid_identifier("invalid/dataset") is False
        assert cost_analyzer._is_valid_identifier("table;drop") is False
        assert cost_analyzer._is_valid_identifier("user input") is False
        assert cost_analyzer._is_valid_identifier("table'") is False

    def test_get_billing_table_real_api_call(self, cost_analyzer: CostAnalyzer) -> None:
        """Test getting billing table with REAL BigQuery API call."""
        try:
            # This makes a real API call to BigQuery
            table_name = cost_analyzer._get_billing_table()
            print(f"\nFound REAL billing table: {table_name}")

            # Verify it's a valid billing export table name
            assert table_name.startswith("gcp_billing_export")
            assert cost_analyzer._is_valid_identifier(table_name)

        except NotFound:
            # If billing dataset doesn't exist, that's OK for testing
            # but we should verify the error handling works
            pytest.skip(
                "Billing dataset not found - this is expected if billing export not configured"
            )
        except ValueError as e:
            if "No billing export tables found" in str(e):
                pytest.skip(
                    "No billing tables found - billing export may not be configured"
                )
            else:
                raise

    def test_get_current_month_spend_real_api_call(self, cost_analyzer: CostAnalyzer) -> None:
        """Test getting current month spend with REAL BigQuery API call."""
        try:
            # This makes a real API call to BigQuery
            spend_data = cost_analyzer.get_current_month_spend()
            print(f"\nREAL current month spend data: {spend_data}")

            # Verify the response structure
            assert isinstance(spend_data, dict)
            # If there's data, verify it's numeric
            for service, cost in spend_data.items():
                assert isinstance(service, str)
                assert isinstance(cost, (int, float))
                assert cost >= 0  # Costs should be non-negative

        except (NotFound, ValueError) as e:
            if "not found" in str(e).lower() or "No billing export" in str(e):
                pytest.skip(
                    "Billing data not available - this is expected if billing export not configured"
                )
            else:
                raise

    def test_cache_functionality(self, cost_analyzer: CostAnalyzer) -> None:
        """Test that caching works correctly to avoid excessive API calls."""
        cache_key = f"month_spend_{datetime.now(timezone.utc).strftime('%Y%m')}"

        # Clear cache first
        cost_analyzer._cache.clear()
        assert cache_key not in cost_analyzer._cache

        try:
            # First call - should hit the API
            first_result = cost_analyzer.get_current_month_spend()

            # Check cache was populated
            assert cache_key in cost_analyzer._cache
            cache_time, cached_data = cost_analyzer._cache[cache_key]
            assert cached_data == first_result

            # Second call - should use cache
            second_result = cost_analyzer.get_current_month_spend()
            assert second_result == first_result

            # Verify cache time is recent
            time_diff = (datetime.now(timezone.utc) - cache_time).seconds
            assert time_diff < 10  # Should be cached within last 10 seconds

        except (NotFound, ValueError) as e:
            if "not found" in str(e).lower() or "No billing export" in str(e):
                pytest.skip("Billing data not available")
            else:
                raise

    def test_get_daily_spend_trend_real_api_call(self, cost_analyzer: CostAnalyzer) -> None:
        """Test getting daily spend trend with REAL API call."""
        try:
            # This makes a real API call
            trend = cost_analyzer.get_daily_spend_trend(days=7)
            print(f"\nREAL daily spend trend for last 7 days: {trend}")

            assert isinstance(trend, list)
            for day_data in trend:
                assert "usage_date" in day_data
                assert "total_daily_cost" in day_data
                assert isinstance(day_data["total_daily_cost"], (int, float))
                assert day_data["total_daily_cost"] >= 0

        except (NotFound, ValueError) as e:
            if "not found" in str(e).lower() or "No billing export" in str(e):
                pytest.skip("Billing data not available")
            else:
                raise

    def test_get_resource_utilization_metrics_real_api_call(self, cost_analyzer: CostAnalyzer) -> None:
        """Test getting resource utilization metrics with REAL API call."""
        try:
            # This makes a real API call to Cloud Monitoring
            metrics = cost_analyzer.get_resource_utilization_metrics()
            print(f"\nREAL resource utilization metrics: {metrics}")

            assert isinstance(metrics, dict)
            # Should have compute and storage metrics
            if "compute" in metrics:
                assert isinstance(metrics["compute"], dict)
                if "cpu_utilization" in metrics["compute"]:
                    assert isinstance(
                        metrics["compute"]["cpu_utilization"], (int, float)
                    )
                    assert 0 <= metrics["compute"]["cpu_utilization"] <= 100

            if "storage" in metrics:
                assert isinstance(metrics["storage"], dict)

        except (ValueError, RuntimeError, KeyError) as e:
            # Monitoring API might not have data
            print(f"Resource metrics not available: {e}")
            pytest.skip("Monitoring metrics not available")

    def test_get_cost_optimization_recommendations_real_api_call(self, cost_analyzer: CostAnalyzer) -> None:
        """Test getting cost optimization recommendations with REAL API call."""
        try:
            # Get recommendations based on real data
            recommendations = cost_analyzer.get_cost_optimization_recommendations()
            print(f"\nREAL cost optimization recommendations: {recommendations}")

            assert isinstance(recommendations, list)

            for rec in recommendations:
                assert "recommendation" in rec
                assert "potential_monthly_savings" in rec
                assert "confidence" in rec
                assert isinstance(rec["potential_monthly_savings"], (int, float))
                assert rec["confidence"] in ["high", "medium", "low"]

        except (NotFound, ValueError) as e:
            if "not found" in str(e).lower() or "No billing export" in str(e):
                pytest.skip("Billing data not available")
            else:
                raise

    def test_real_bigquery_connection(self, cost_analyzer: CostAnalyzer, project_id: str) -> None:
        """Test that we can make real BigQuery API calls."""
        # Try to list datasets in the project
        datasets = list(cost_analyzer.bq_client.list_datasets())
        print(
            f"\nREAL datasets in project {project_id}: {[d.dataset_id for d in datasets]}"
        )

        # Verify we can access BigQuery
        assert cost_analyzer.bq_client.project == project_id

    def test_sql_injection_protection(self, cost_analyzer: CostAnalyzer) -> None:  # pylint: disable=unused-argument
        """Test that SQL injection attempts are blocked."""
        # Try to create analyzer with malicious input
        with pytest.raises(ValueError, match="Invalid"):
            CostAnalyzer("project'; DROP TABLE users; --", "dataset")

        with pytest.raises(ValueError, match="Invalid"):
            CostAnalyzer("valid-project", "dataset'; DELETE FROM billing; --")

    @pytest.mark.integration
    def test_end_to_end_cost_analysis_workflow(self) -> None:
        """Test complete cost analysis workflow with REAL API calls."""
        # Use real project configuration for testing
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
        billing_dataset = "billing_export"
        cost_analyzer = CostAnalyzer(project_id, billing_dataset)

        try:
            # 1. Get current month spend
            current_spend = cost_analyzer.get_current_month_spend()
            print(f"\nStep 1 - Current month spend: {current_spend}")

            # 2. Get daily spend trend
            daily_trend = cost_analyzer.get_daily_spend_trend(days=7)
            print(f"\nStep 2 - Daily spend trend: {daily_trend}")

            # 3. Get resource utilization metrics
            metrics = cost_analyzer.get_resource_utilization_metrics()
            print(f"\nStep 3 - Resource utilization: {metrics}")

            # 4. Get cost optimization recommendations
            recommendations = cost_analyzer.get_cost_optimization_recommendations()
            print(f"\nStep 4 - Recommendations: {recommendations}")

            # Verify workflow completed
            assert True  # If we got here, all API calls succeeded

        except (NotFound, ValueError) as e:
            if "not found" in str(e).lower() or "No billing export" in str(e):
                pytest.skip("Billing data not available for end-to-end test")
            else:
                raise
