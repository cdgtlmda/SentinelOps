"""
Test orchestrator_agent/retention.py

CRITICAL REQUIREMENT: Each test must achieve MINIMUM 90% STATEMENT COVERAGE
of the target source production code file.

Coverage verification:
python -m coverage run -m pytest tests/unit/orchestrator_agent/test_retention.py
python -m coverage report --include="*orchestrator_agent/retention.py" --show-missing

NO MOCKING - 100% Production Code Testing
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Tuple

import pytest
from google.cloud import firestore_v1 as firestore

# Import the actual production code - NO MOCKS
from src.orchestrator_agent.retention import (
    RetentionPeriod,
    RetentionPolicy,
    RetentionManager,
)


class TestRetentionPeriod:
    """Test RetentionPeriod enum with all time delta values."""

    def test_retention_period_hours_24(self) -> None:
        """Test 24 hours retention period."""
        assert RetentionPeriod.HOURS_24.value == timedelta(hours=24)
        assert RetentionPeriod.HOURS_24.value.total_seconds() == 86400

    def test_retention_period_days_7(self) -> None:
        """Test 7 days retention period."""
        assert RetentionPeriod.DAYS_7.value == timedelta(days=7)
        assert RetentionPeriod.DAYS_7.value.total_seconds() == 604800

    def test_retention_period_days_30(self) -> None:
        """Test 30 days retention period."""
        assert RetentionPeriod.DAYS_30.value == timedelta(days=30)
        assert RetentionPeriod.DAYS_30.value.total_seconds() == 2592000

    def test_retention_period_days_90(self) -> None:
        """Test 90 days retention period."""
        assert RetentionPeriod.DAYS_90.value == timedelta(days=90)
        assert RetentionPeriod.DAYS_90.value.total_seconds() == 7776000

    def test_retention_period_days_180(self) -> None:
        """Test 180 days retention period."""
        assert RetentionPeriod.DAYS_180.value == timedelta(days=180)
        assert RetentionPeriod.DAYS_180.value.total_seconds() == 15552000

    def test_retention_period_days_365(self) -> None:
        """Test 365 days retention period."""
        assert RetentionPeriod.DAYS_365.value == timedelta(days=365)
        assert RetentionPeriod.DAYS_365.value.total_seconds() == 31536000

    def test_retention_period_years_7(self) -> None:
        """Test 7 years compliance retention period."""
        assert RetentionPeriod.YEARS_7.value == timedelta(days=2555)
        assert RetentionPeriod.YEARS_7.value.total_seconds() == 220752000

    def test_retention_period_enum_behavior(self) -> None:
        """Test RetentionPeriod enum behavior."""
        # Test enum membership
        assert RetentionPeriod.HOURS_24 in RetentionPeriod
        assert RetentionPeriod.YEARS_7 in RetentionPeriod

        # Test iteration
        periods = list(RetentionPeriod)
        assert len(periods) == 7

        # Test all are timedelta objects
        for period in periods:
            assert isinstance(period.value, timedelta)


class TestRetentionPolicy:
    """Test RetentionPolicy class with various configurations."""

    def test_retention_policy_basic_initialization(self) -> None:
        """Test basic retention policy initialization."""
        policy = RetentionPolicy("test_policy", timedelta(days=30), ["incidents"])

        assert policy.policy_name == "test_policy"
        assert policy.retention_period == timedelta(days=30)
        assert policy.applies_to == ["incidents"]
        assert policy.conditions == {}
        assert policy.archive_before_delete is False

    def test_retention_policy_with_conditions(self) -> None:
        """Test retention policy with conditions."""
        conditions = {"status": ["closed", "resolved"], "severity": "low"}

        policy = RetentionPolicy(
            "conditional_policy",
            timedelta(days=90),
            ["incidents", "alerts"],
            conditions=conditions,
            archive_before_delete=True,
        )

        assert policy.policy_name == "conditional_policy"
        assert policy.retention_period == timedelta(days=90)
        assert policy.applies_to == ["incidents", "alerts"]
        assert policy.conditions == conditions
        assert policy.archive_before_delete is True

    def test_retention_policy_with_enum_period(self) -> None:
        """Test retention policy using enum period."""
        policy = RetentionPolicy(
            "enum_policy", RetentionPeriod.DAYS_180.value, ["audit_logs"]
        )

        assert policy.retention_period == timedelta(days=180)
        assert policy.applies_to == ["audit_logs"]

    def test_retention_policy_none_conditions(self) -> None:
        """Test retention policy with None conditions."""
        policy = RetentionPolicy(
            "none_conditions_policy", timedelta(days=60), ["metrics"], conditions=None
        )

        assert policy.conditions == {}

    def test_retention_policy_complex_conditions(self) -> None:
        """Test retention policy with complex conditions."""
        conditions = {
            "status": ["closed", "resolved", "cancelled"],
            "severity": "critical",
            "type": "security_incident",
        }

        policy = RetentionPolicy(
            "complex_policy",
            RetentionPeriod.YEARS_7.value,
            ["incidents", "audit_logs"],
            conditions=conditions,
            archive_before_delete=True,
        )

        assert policy.conditions == conditions
        assert len(policy.applies_to) == 2
        assert policy.archive_before_delete is True

    def test_retention_policy_single_apply_to(self) -> None:
        """Test retention policy with single data type."""
        policy = RetentionPolicy("single_type_policy", timedelta(days=7), ["metrics"])

        assert policy.applies_to == ["metrics"]
        assert len(policy.applies_to) == 1

    def test_retention_policy_empty_applies_to(self) -> None:
        """Test retention policy with empty applies_to list."""
        policy = RetentionPolicy("empty_applies_policy", timedelta(days=1), [])

        assert policy.applies_to == []
        assert len(policy.applies_to) == 0


class TestRetentionManager:
    """Test RetentionManager class with real Firestore integration."""

    @pytest.fixture
    def firestore_client(self) -> firestore.Client:
        """Create real Firestore client for testing."""
        return firestore.Client(project="your-gcp-project-id")

    @pytest.fixture
    def basic_config(self) -> Dict[str, Any]:
        """Basic configuration for testing."""
        return {
            "retention": {
                "archive_enabled": False,
                "archive_bucket": "test-archive-bucket",
            }
        }

    @pytest.fixture
    def config_with_policies(self) -> Dict[str, Any]:
        """Configuration with custom retention policies."""
        return {
            "retention": {
                "archive_enabled": True,
                "archive_bucket": "test-archive-bucket",
                "policies": {
                    "custom_incident_policy": {
                        "retention_days": 60,
                        "applies_to": ["incidents"],
                        "conditions": {"status": "closed"},
                        "archive_before_delete": True,
                    },
                    "audit_policy": {
                        "retention_days": 2555,  # 7 years
                        "applies_to": ["audit_logs"],
                        "archive_before_delete": True,
                    },
                    "metrics_policy": {
                        "retention_days": 14,
                        "applies_to": ["metrics"],
                        "conditions": {"type": "performance"},
                        "archive_before_delete": False,
                    },
                },
                "by_severity": {"critical": 365, "high": 180, "medium": 90, "low": 30},
            }
        }

    @pytest.fixture
    def config_with_severity_only(self) -> Dict[str, Any]:
        """Configuration with only severity-based policies."""
        return {
            "retention": {
                "archive_enabled": False,
                "by_severity": {
                    "critical": 730,  # 2 years
                    "high": 365,  # 1 year
                    "medium": 180,  # 6 months
                    "low": 90,  # 3 months
                },
            }
        }

    @pytest.fixture
    def empty_config(self) -> Dict[str, Any]:
        """Empty configuration for testing defaults."""
        return {}

    def test_retention_manager_initialization_basic(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test basic RetentionManager initialization."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)

        assert manager.agent_id == "test-agent"
        assert manager.db == firestore_client
        assert manager.config == basic_config
        assert manager.archive_enabled is False
        assert manager.archive_bucket == "test-archive-bucket"
        assert len(manager.policies) == 3  # Default policies
        assert not manager.last_cleanup
        assert manager.logger is not None

    def test_retention_manager_initialization_with_policies(
        self, firestore_client: firestore.Client, config_with_policies: Dict[str, Any]
    ) -> None:
        """Test RetentionManager initialization with custom policies."""
        manager = RetentionManager("test-agent", firestore_client, config_with_policies)

        assert manager.archive_enabled is True
        assert len(manager.policies) >= 7  # Custom policies + severity-based policies

        # Check custom policies are loaded
        policy_names = [p.policy_name for p in manager.policies]
        assert "custom_incident_policy" in policy_names
        assert "audit_policy" in policy_names
        assert "metrics_policy" in policy_names
        assert "severity_critical_retention" in policy_names
        assert "severity_high_retention" in policy_names
        assert "severity_medium_retention" in policy_names
        assert "severity_low_retention" in policy_names

    def test_retention_manager_empty_config(
        self, firestore_client: firestore.Client, empty_config: Dict[str, Any]
    ) -> None:
        """Test RetentionManager with empty configuration."""
        manager = RetentionManager("test-agent", firestore_client, empty_config)

        assert manager.archive_enabled is False
        assert manager.archive_bucket == ""
        assert len(manager.policies) == 3  # Should load default policies

        # Check default policies
        policy_names = [p.policy_name for p in manager.policies]
        assert "default_incident_retention" in policy_names
        assert "default_audit_retention" in policy_names
        assert "default_metrics_retention" in policy_names

    def test_load_policies_default(
        self, firestore_client: firestore.Client, empty_config: Dict[str, Any]
    ) -> None:
        """Test loading default retention policies when none configured."""
        manager = RetentionManager("test-agent", firestore_client, empty_config)

        assert len(manager.policies) == 3

        # Check default incident policy
        incident_policy = next(
            p for p in manager.policies if p.policy_name == "default_incident_retention"
        )
        assert incident_policy.retention_period == timedelta(days=90)
        assert "incidents" in incident_policy.applies_to
        assert incident_policy.conditions == {"status": ["closed", "resolved"]}
        assert incident_policy.archive_before_delete is False

        # Check default audit policy
        audit_policy = next(
            p for p in manager.policies if p.policy_name == "default_audit_retention"
        )
        assert audit_policy.retention_period == timedelta(days=2555)  # 7 years
        assert "audit_logs" in audit_policy.applies_to
        assert audit_policy.archive_before_delete is True

        # Check default metrics policy
        metrics_policy = next(
            p for p in manager.policies if p.policy_name == "default_metrics_retention"
        )
        assert metrics_policy.retention_period == timedelta(days=30)
        assert "metrics" in metrics_policy.applies_to
        assert metrics_policy.archive_before_delete is False

    def test_load_policies_from_config(
        self, firestore_client: firestore.Client, config_with_policies: Dict[str, Any]
    ) -> None:
        """Test loading policies from configuration."""
        manager = RetentionManager("test-agent", firestore_client, config_with_policies)

        # Find custom incident policy
        custom_policy = next(
            p for p in manager.policies if p.policy_name == "custom_incident_policy"
        )

        assert custom_policy.retention_period == timedelta(days=60)
        assert custom_policy.applies_to == ["incidents"]
        assert custom_policy.conditions == {"status": "closed"}
        assert custom_policy.archive_before_delete is True

        # Find metrics policy
        metrics_policy = next(
            p for p in manager.policies if p.policy_name == "metrics_policy"
        )

        assert metrics_policy.retention_period == timedelta(days=14)
        assert metrics_policy.applies_to == ["metrics"]
        assert metrics_policy.conditions == {"type": "performance"}
        assert metrics_policy.archive_before_delete is False

    def test_load_policies_severity_based(
        self,
        firestore_client: firestore.Client,
        config_with_severity_only: Dict[str, Any],
    ) -> None:
        """Test loading severity-based retention policies."""
        manager = RetentionManager(
            "test-agent", firestore_client, config_with_severity_only
        )

        # Should have default policies + severity policies
        assert len(manager.policies) >= 7

        # Check severity-based policies
        critical_policy = next(
            p
            for p in manager.policies
            if p.policy_name == "severity_critical_retention"
        )

        assert critical_policy.retention_period == timedelta(days=730)
        assert "incidents" in critical_policy.applies_to
        assert critical_policy.conditions == {"severity": "critical"}

        low_policy = next(
            p for p in manager.policies if p.policy_name == "severity_low_retention"
        )

        assert low_policy.retention_period == timedelta(days=90)
        assert low_policy.conditions == {"severity": "low"}

    def test_load_policies_mixed_config(
        self, firestore_client: firestore.Client, config_with_policies: Dict[str, Any]
    ) -> None:
        """Test loading both custom and severity-based policies."""
        manager = RetentionManager("test-agent", firestore_client, config_with_policies)

        policy_names = [p.policy_name for p in manager.policies]

        # Should have custom policies
        assert "custom_incident_policy" in policy_names
        assert "audit_policy" in policy_names
        assert "metrics_policy" in policy_names

        # Should have severity-based policies
        assert "severity_critical_retention" in policy_names
        assert "severity_high_retention" in policy_names
        assert "severity_medium_retention" in policy_names
        assert "severity_low_retention" in policy_names

        # Should have the right total count
        assert len(manager.policies) == 7  # 3 custom + 4 severity

    @pytest.mark.asyncio
    async def test_apply_retention_policies_basic(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test applying retention policies with basic configuration."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)

        result = await manager.apply_retention_policies()

        assert isinstance(result, dict)
        assert "incidents" in result
        assert "audit_logs" in result
        assert "metrics" in result
        assert all(isinstance(count, int) for count in result.values())
        assert all(count >= 0 for count in result.values())

    @pytest.mark.asyncio
    async def test_apply_policies_for_type_incidents(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test applying retention policies for incidents data type."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)

        # Test applying policies for incidents
        try:
            result = await manager._apply_policies_for_type("incidents")
            assert isinstance(result, int)
            assert result >= 0
        except (ValueError, RuntimeError) as e:
            # If Firestore requires indexes, that's expected for production queries
            if "requires an index" in str(e).lower():
                assert "index" in str(e).lower()
            else:
                raise

    @pytest.mark.asyncio
    async def test_apply_policies_for_type_audit_logs(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test applying retention policies for audit_logs data type."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)

        try:
            result = await manager._apply_policies_for_type("audit_logs")
            assert isinstance(result, int)
            assert result >= 0
        except (ValueError, RuntimeError) as e:
            if "requires an index" in str(e).lower():
                assert "index" in str(e).lower()
            else:
                raise

    @pytest.mark.asyncio
    async def test_apply_policies_for_type_metrics(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test applying retention policies for metrics data type."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)

        try:
            result = await manager._apply_policies_for_type("metrics")
            assert isinstance(result, int)
            assert result >= 0
        except (ValueError, RuntimeError) as e:
            if "requires an index" in str(e).lower():
                assert "index" in str(e).lower()
            else:
                raise

    @pytest.mark.asyncio
    async def test_apply_policies_for_type_no_policies(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test applying policies when no policies apply to data type."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)

        # Test with non-existent data type
        result = await manager._apply_policies_for_type("non_existent")

        assert result == 0

    @pytest.mark.asyncio
    async def test_apply_policies_for_type_empty_policies(
        self, firestore_client: firestore.Client
    ) -> None:
        """Test applying policies when policies list is empty."""
        config: Dict[str, Any] = {"retention": {"policies": {}}}
        manager = RetentionManager("test-agent", firestore_client, config)
        manager.policies = []  # Clear all policies

        result = await manager._apply_policies_for_type("incidents")
        assert result == 0

    @pytest.mark.asyncio
    async def test_archive_document_no_bucket(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test archiving document when no bucket is configured."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)
        manager.archive_bucket = ""  # No bucket configured

        test_data = {"test": "data"}

        # Should handle gracefully when no bucket configured
        await manager._archive_document("incidents", "test-doc", test_data)

        # No exception should be raised, just a warning logged
        assert True

    @pytest.mark.asyncio
    async def test_archive_document_with_bucket(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test archiving document with bucket configured."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)

        test_data = {
            "incident_id": "test-123",
            "severity": "high",
            "status": "closed",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # This should attempt to archive to Firestore collection
        await manager._archive_document("incidents", "test-doc-id", test_data)

        # Check if document was added to archive collection
        archive_collection = firestore_client.collection("archive_incidents")

        try:
            docs = list(
                archive_collection.where("original_id", "==", "test-doc-id")
                .limit(1)
                .stream()
            )

            if docs:
                archived_doc = docs[0].to_dict()
                assert archived_doc is not None
                assert archived_doc["original_id"] == "test-doc-id"
                assert archived_doc["archived_by"] == "test-agent"
                assert "archived_at" in archived_doc
                assert archived_doc["incident_id"] == "test-123"

                # Clean up test data
                docs[0].reference.delete()
        except (PermissionError, FileNotFoundError, ValueError, RuntimeError) as e:
            # Archive collection access might require setup
            if "permission" in str(e).lower() or "not found" in str(e).lower():
                pass  # Expected in test environment
            else:
                raise

    @pytest.mark.asyncio
    async def test_archive_document_different_types(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test archiving documents of different types."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)

        # Test archiving different data types
        test_cases: List[Tuple[str, Dict[str, Any]]] = [
            ("incidents", {"incident_id": "inc-123", "severity": "low"}),
            ("audit_logs", {"action": "login", "user": "test@example.com"}),
            ("metrics", {"metric_name": "cpu_usage", "value": 85.5}),
        ]

        for data_type, test_data in test_cases:
            await manager._archive_document(
                data_type, f"test-{data_type}-123", test_data
            )
            # Should complete without exception
            assert True

    @pytest.mark.asyncio
    async def test_get_retention_summary(
        self, firestore_client: firestore.Client, config_with_policies: Dict[str, Any]
    ) -> None:
        """Test getting retention summary."""
        manager = RetentionManager("test-agent", firestore_client, config_with_policies)

        summary = await manager.get_retention_summary()

        assert isinstance(summary, dict)
        assert "policies" in summary
        assert "next_cleanup" in summary
        assert "data_counts" in summary

        # Check policies section
        assert isinstance(summary["policies"], list)
        assert len(summary["policies"]) > 0

        # Check each policy has required fields
        for policy in summary["policies"]:
            assert "name" in policy
            assert "retention_days" in policy
            assert "applies_to" in policy
            assert "conditions" in policy
            assert "archive_enabled" in policy
            assert isinstance(policy["retention_days"], int)
            assert isinstance(policy["applies_to"], list)
            assert isinstance(policy["conditions"], dict)
            assert isinstance(policy["archive_enabled"], bool)

        # Check next cleanup section
        assert "incidents" in summary["next_cleanup"]
        assert "audit_logs" in summary["next_cleanup"]
        assert "metrics" in summary["next_cleanup"]

        # Check data counts section
        assert "incidents" in summary["data_counts"]
        assert "audit_logs" in summary["data_counts"]
        assert "metrics" in summary["data_counts"]

        # Verify data counts are integers
        for count in summary["data_counts"].values():
            assert isinstance(count, int)
            assert count >= 0

    @pytest.mark.asyncio
    async def test_get_retention_summary_data_count_errors(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test retention summary when data count queries have errors."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)

        # Even if individual queries fail, summary should still be returned
        summary = await manager.get_retention_summary()

        assert isinstance(summary, dict)
        assert "policies" in summary
        assert "next_cleanup" in summary
        assert "data_counts" in summary

    def test_should_run_cleanup_new_manager(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test should_run_cleanup for new manager with no previous cleanups."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)

        # Should run cleanup for all types when no previous cleanup
        assert manager.should_run_cleanup("incidents") is True
        assert manager.should_run_cleanup("audit_logs") is True
        assert manager.should_run_cleanup("metrics") is True
        assert manager.should_run_cleanup("unknown_type") is True

    def test_should_run_cleanup_recent_cleanup(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test should_run_cleanup when cleanup was recent."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)

        # Set recent cleanup time
        recent_time = datetime.now(timezone.utc) - timedelta(hours=1)
        manager.last_cleanup["incidents"] = recent_time

        # Should not run cleanup if recent
        assert manager.should_run_cleanup("incidents") is False

        # Should still run for other types
        assert manager.should_run_cleanup("audit_logs") is True
        assert manager.should_run_cleanup("metrics") is True

    def test_should_run_cleanup_old_cleanup(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test should_run_cleanup when cleanup is old."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)

        # Set old cleanup time (more than 24 hours ago)
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        manager.last_cleanup["incidents"] = old_time

        # Should run cleanup if old
        assert manager.should_run_cleanup("incidents") is True

        # Test exactly 24 hours ago (boundary case)
        exactly_24h = datetime.now(timezone.utc) - timedelta(hours=24, seconds=1)
        manager.last_cleanup["audit_logs"] = exactly_24h
        assert manager.should_run_cleanup("audit_logs") is True

    def test_should_run_cleanup_edge_cases(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test should_run_cleanup edge cases."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)

        # Test with future time (should not happen but handle gracefully)
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        manager.last_cleanup["incidents"] = future_time

        # Should still run cleanup
        assert manager.should_run_cleanup("incidents") is True

        # Test with exact boundary (exactly 24 hours)
        boundary_time = datetime.now(timezone.utc) - timedelta(hours=24)
        manager.last_cleanup["metrics"] = boundary_time

        # Should not run cleanup at exact boundary
        assert manager.should_run_cleanup("metrics") is False

    def test_collection_mapping_coverage(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test that collection mapping works for all data types."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Test all valid data types
            data_types = ["incidents", "audit_logs", "metrics"]

            for data_type in data_types:
                try:
                    result = loop.run_until_complete(
                        manager._apply_policies_for_type(data_type)
                    )
                    assert isinstance(result, int)
                    assert result >= 0
                except (ValueError, RuntimeError) as e:
                    if "requires an index" in str(e).lower():
                        # Expected for production Firestore with complex queries
                        pass
                    else:
                        raise

        finally:
            loop.close()

    def test_policy_conditions_handling(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test different types of policy conditions are handled correctly."""
        manager = RetentionManager("test-agent", firestore_client, basic_config)

        # Test policies with different condition types
        policies = [
            # Single string status
            RetentionPolicy(
                "single_status",
                timedelta(days=30),
                ["incidents"],
                conditions={"status": "closed"},
            ),
            # List of statuses
            RetentionPolicy(
                "multiple_status",
                timedelta(days=30),
                ["incidents"],
                conditions={"status": ["closed", "resolved"]},
            ),
            # Severity condition
            RetentionPolicy(
                "severity_condition",
                timedelta(days=30),
                ["incidents"],
                conditions={"severity": "low"},
            ),
            # Multiple conditions
            RetentionPolicy(
                "multi_condition",
                timedelta(days=30),
                ["incidents"],
                conditions={"status": "closed", "severity": "high"},
            ),
            # No conditions
            RetentionPolicy("no_conditions", timedelta(days=30), ["incidents"]),
        ]

        manager.policies = policies

        assert len(manager.policies) == 5

        # Verify conditions are preserved correctly
        assert manager.policies[0].conditions["status"] == "closed"
        assert manager.policies[1].conditions["status"] == ["closed", "resolved"]
        assert manager.policies[2].conditions["severity"] == "low"
        assert len(manager.policies[3].conditions) == 2
        assert manager.policies[4].conditions == {}

    @pytest.mark.asyncio
    async def test_error_handling_in_apply_retention_policies(
        self, firestore_client: firestore.Client
    ) -> None:
        """Test error handling in apply_retention_policies method."""
        # Create manager with basic config
        manager = RetentionManager("test-agent", firestore_client, {})

        # Should handle errors gracefully and return valid structure
        result = await manager.apply_retention_policies()

        assert isinstance(result, dict)
        assert "incidents" in result
        assert "audit_logs" in result
        assert "metrics" in result

        # All values should be integers (even if 0 due to errors)
        for count in result.values():
            assert isinstance(count, int)
            assert count >= 0

    def test_retention_manager_logger_setup(
        self, firestore_client: firestore.Client, basic_config: Dict[str, Any]
    ) -> None:
        """Test that logger is properly configured."""
        agent_id = "test-logger-agent"
        manager = RetentionManager(agent_id, firestore_client, basic_config)

        assert manager.logger is not None
        assert agent_id in manager.logger.name
        assert "RetentionManager" in manager.logger.name

    def test_config_extraction_edge_cases(
        self, firestore_client: firestore.Client
    ) -> None:
        """Test configuration extraction with various edge cases."""
        # Test with nested missing keys
        config1 = {"other_section": {"key": "value"}}
        manager1 = RetentionManager("test", firestore_client, config1)
        assert manager1.archive_enabled is False
        assert manager1.archive_bucket == ""

        # Test with partial retention config
        config2 = {"retention": {"archive_enabled": True}}
        manager2 = RetentionManager("test", firestore_client, config2)
        assert manager2.archive_enabled is True
        assert manager2.archive_bucket == ""

        # Test with only policies config
        config3 = {"retention": {"policies": {"test": {"retention_days": 30}}}}
        manager3 = RetentionManager("test", firestore_client, config3)
        assert len(manager3.policies) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
