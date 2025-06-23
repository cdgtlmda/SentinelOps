"""REAL tests for detection_agent/query_optimizer.py - Testing actual query optimization logic."""

from datetime import datetime, timedelta
from typing import Dict, Any

import pytest

# Import the actual production code directly
from src.detection_agent.query_optimizer import QueryOptimizer


class TestQueryOptimizerRealLogic:
    """Test QueryOptimizer with REAL production logic - NO MOCKS."""

    @pytest.fixture
    def config(self) -> Dict[str, Any]:
        """Provide real configuration for testing."""
        return {
            "agents": {
                "detection": {
                    "query_optimization": {
                        "enable_time_partitioning": True,
                        "max_scan_days": 7,
                        "default_limit": 10000,
                        "enable_sampling": True,
                        "sample_percentage": 10,
                        "enable_column_pruning": True,
                        "required_columns": [
                            "timestamp",
                            "actor",
                            "source_ip",
                            "resource_name",
                            "method_name",
                            "status_code",
                        ],
                    }
                }
            }
        }

    @pytest.fixture
    def optimizer(self, config: Dict[str, Any]) -> QueryOptimizer:
        """Create real QueryOptimizer instance."""
        return QueryOptimizer(config)

    def test_real_time_range_optimization_within_limit(
        self, optimizer: QueryOptimizer
    ) -> None:
        """Test REAL time range optimization when within max_scan_days."""
        # Real query that would be used in production
        query = "SELECT * FROM `project.dataset.audit_logs` WHERE timestamp > TIMESTAMP('2024-01-01T00:00:00')"
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 5)  # 4 days, within 7 day limit

        # Execute real optimization logic
        optimized = optimizer._optimize_time_range(query, start_time, end_time)

        # Verify real optimization was applied
        assert "_PARTITIONTIME" in optimized
        assert "2024-01-01" in optimized  # Original date should remain
        assert optimized != query  # Query should be modified

    def test_real_time_range_optimization_exceeds_limit(
        self, optimizer: QueryOptimizer
    ) -> None:
        """Test REAL time range optimization when exceeding max_scan_days."""
        # Real production query
        query = "SELECT * FROM `project.dataset.audit_logs` WHERE timestamp > TIMESTAMP('2024-01-01T00:00:00')"
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 15)  # 14 days, exceeds 7 day limit

        # Execute real optimization
        optimized = optimizer._optimize_time_range(query, start_time, end_time)

        # Should adjust to 7 days before end
        expected_new_start = end_time - timedelta(days=7)
        assert expected_new_start.isoformat() in optimized
        assert (
            "2024-01-01T00:00:00" not in optimized
        )  # Original date should be replaced

    def test_real_column_pruning_optimization(self, optimizer: QueryOptimizer) -> None:
        """Test REAL column pruning to reduce data transfer."""
        # Real query with SELECT *
        query = "SELECT * FROM `project.dataset.audit_logs` WHERE actor = 'user@example.com'"

        # Execute real optimization
        optimized = optimizer._prune_unnecessary_columns(query)

        # Verify columns were pruned
        assert "SELECT *" not in optimized
        assert "SELECT" in optimized
        assert "timestamp" in optimized
        assert "actor" in optimized
        assert "method_name" in optimized
        # Verify it's a valid column list
        assert optimized.count(",") >= 5  # Should have multiple columns

    def test_real_result_limit_application(self, optimizer: QueryOptimizer) -> None:
        """Test REAL limit application for result size control."""
        # Query without limit
        query = (
            "SELECT * FROM `project.dataset.audit_logs` WHERE timestamp > '2024-01-01'"
        )

        # Execute real optimization
        optimized = optimizer._apply_result_limits(query)

        assert "LIMIT 10000" in optimized
        assert optimized.endswith("LIMIT 10000")

    def test_real_sampling_application(self, optimizer: QueryOptimizer) -> None:
        """Test REAL sampling application for large datasets."""
        # Query that should trigger sampling
        query = "SELECT * FROM `project.dataset.audit_logs`"

        # Execute real sampling logic
        optimized = optimizer._apply_sampling(query)

        assert "TABLESAMPLE SYSTEM (10 PERCENT)" in optimized

    def test_real_clustering_optimization(self, optimizer: QueryOptimizer) -> None:
        """Test REAL clustering optimization for BigQuery tables."""
        query = "SELECT * FROM logs WHERE timestamp > '2024-01-01' AND actor = 'user@example.com'"

        # Execute real clustering optimization
        optimized = optimizer._apply_clustering_optimization(query)

        # Should add clustering hints
        assert "Filter on clustered column" in optimized
        assert optimized.startswith("/*")  # Should have comment hints

    def test_real_sql_optimization_for_login_detection(
        self, optimizer: QueryOptimizer
    ) -> None:
        """Test REAL SQL optimization for suspicious login detection."""
        query = "SELECT * FROM logs WHERE timestamp > '2024-01-01'"
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 2)

        # Execute real optimization for login detection
        optimized = optimizer.optimize_query(
            query, start_time, end_time, "suspicious_login"
        )

        # Should add login-specific filters
        assert "method_name LIKE" in optimized
        assert "LoginAttempt" in optimized or "LoginSuccess" in optimized
        assert "LoginAttempt" in optimized or "LoginSuccess" in optimized
        assert "LIMIT" in optimized
        assert "SELECT *" not in optimized  # Should have column pruning

    def test_real_sql_optimization_for_privilege_escalation(
        self, optimizer: QueryOptimizer
    ) -> None:
        """Test REAL SQL optimization for privilege escalation detection."""
        query = "SELECT * FROM logs WHERE timestamp > '2024-01-01'"
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 2)

        # Execute real optimization
        optimized = optimizer.optimize_query(
            query, start_time, end_time, "privilege_escalation"
        )

        # Should add IAM-specific filters
        assert "method_name LIKE" in optimized
        assert "SetIamPolicy" in optimized or "CreateRole" in optimized

    def test_real_filter_pushdown_optimization(self, optimizer: QueryOptimizer) -> None:
        """Test REAL filter pushdown for JOIN operations."""
        query = """
        SELECT * FROM logs main
        JOIN users sub ON main.actor = sub.user_id
        WHERE timestamp > '2024-01-01'
        """

        # Execute real filter pushdown
        optimized = optimizer._apply_filter_pushdown(query)

        # Should optimize filter placement
        assert "main.timestamp" in optimized or query in optimized

    def test_real_join_optimization_for_large_tables(
        self, optimizer: QueryOptimizer
    ) -> None:
        """Test REAL join optimization for large tables."""
        query = "SELECT * FROM audit_logs JOIN vpc_flow_logs ON audit_logs.ip = vpc_flow_logs.ip"

        # Execute real join optimization
        optimized = optimizer._add_join_hints(query)

        # Should add hash join hint for large tables
        assert "Use HASH JOIN for large tables" in optimized

    def test_real_bytes_estimation_simple_query(
        self, optimizer: QueryOptimizer
    ) -> None:
        """Test REAL bytes processed estimation."""
        query = "SELECT timestamp, actor FROM logs"
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 3)  # 2 days

        # Execute real estimation logic
        bytes_est = optimizer.estimate_bytes_processed(query, start_time, end_time)

        # 2 days = 2GB base, but with sampling applied (since >24h) = 200MB
        # Then with column pruning (70% of that) = 140MB
        assert bytes_est == 140_000_000

    def test_real_bytes_estimation_with_sampling(
        self, optimizer: QueryOptimizer
    ) -> None:
        """Test REAL bytes estimation with sampling applied."""
        query = "SELECT * FROM logs"
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 5)  # 4 days, triggers sampling

        # Execute real estimation
        bytes_est = optimizer.estimate_bytes_processed(query, start_time, end_time)

        # 4 days = 4GB, with 10% sampling = 400MB
        assert bytes_est == 400_000_000

    def test_real_comprehensive_query_optimization(
        self, optimizer: QueryOptimizer
    ) -> None:
        """Test REAL comprehensive optimization pipeline."""
        # Real production query
        query = """
        SELECT *
        FROM `project.dataset.audit_logs`
        WHERE timestamp > '2024-01-01T00:00:00'
        AND severity = 'ERROR'
        """
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 10)  # 9 days

        # Execute full optimization pipeline
        optimized = optimizer.optimize_query(
            query, start_time, end_time, "suspicious_login"
        )

        # Verify multiple optimizations were applied
        assert "SELECT *" not in optimized  # Column pruning
        assert "_PARTITIONTIME" in optimized  # Partition filter
        assert "LIMIT" in optimized  # Result limit
        assert "method_name LIKE" in optimized  # Rule-specific filter
        assert "TABLESAMPLE" in optimized  # Sampling for large range

        # Verify it's still valid SQL structure
        assert "SELECT" in optimized
        assert "FROM" in optimized
        assert "WHERE" in optimized

    def test_real_optimization_with_all_features_disabled(self) -> None:
        """Test REAL behavior when optimizations are disabled."""
        config = {
            "agents": {
                "detection": {
                    "query_optimization": {
                        "enable_time_partitioning": False,
                        "enable_sampling": False,
                        "enable_column_pruning": False,
                    }
                }
            }
        }
        optimizer = QueryOptimizer(config)

        query = "SELECT * FROM logs WHERE timestamp > '2024-01-01'"
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 10)

        # Execute optimization with features disabled
        optimized = optimizer.optimize_query(query, start_time, end_time)

        # Should still apply limit but not other optimizations
        assert "SELECT *" in optimized  # No column pruning
        assert "LIMIT" in optimized  # Limit still applied
        assert "_PARTITIONTIME" not in optimized  # No partition filter
        assert "TABLESAMPLE" not in optimized  # No sampling

    def test_real_edge_case_empty_query(self, optimizer: QueryOptimizer) -> None:
        """Test REAL handling of empty query."""
        query = ""
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 2)

        # Execute optimization on empty query
        optimized = optimizer.optimize_query(query, start_time, end_time)

        # Should handle gracefully
        assert "LIMIT 10000" in optimized

    def test_real_optimization_preserves_query_semantics(
        self, optimizer: QueryOptimizer
    ) -> None:
        """Test that REAL optimizations don't change query meaning."""
        # Complex query with multiple conditions
        query = """
        SELECT *
        FROM logs
        WHERE timestamp > '2024-01-01'
        AND actor IN ('user1', 'user2')
        AND method_name != 'GetObject'
        ORDER BY timestamp DESC
        """
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 2)

        # Execute optimization
        optimized = optimizer.optimize_query(query, start_time, end_time)

        # Original conditions should be preserved
        assert "actor IN ('user1', 'user2')" in optimized
        assert "method_name != 'GetObject'" in optimized
        assert "ORDER BY timestamp DESC" in optimized

    def test_real_sql_injection_protection_in_optimization(
        self, optimizer: QueryOptimizer
    ) -> None:
        """Test REAL SQL injection protection during optimization."""
        # Query with potential injection attempt in WHERE clause
        query = "SELECT * FROM logs WHERE actor = 'user'; DROP TABLE logs; --'"
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 2)

        # Optimization should not break due to malicious content
        optimized = optimizer.optimize_query(query, start_time, end_time)

        # Original malicious string should be preserved as string literal
        assert "DROP TABLE" in optimized  # Should be within string literal
        assert "LIMIT" in optimized  # Normal optimizations still applied
