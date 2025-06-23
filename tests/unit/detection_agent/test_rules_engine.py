"""
Comprehensive test suite for detection_agent/rules_engine.py

Tests all classes and methods with 100% production code (NO MOCKS).
Achieves ≥90% statement coverage of target source file.

Requirements:
- Use real data structures and business logic
- Test all code paths and edge cases
- No mocking of any functionality
- Comprehensive error handling scenarios
- All test cases must pass
"""

from datetime import datetime, timezone
from typing import Dict, Any

import pytest

from src.common.models import SeverityLevel
from src.detection_agent.rules_engine import RuleStatus, DetectionRule, RulesEngine


class TestRuleStatus:
    """Test RuleStatus enum."""

    def test_rule_status_values(self) -> None:
        """Test all RuleStatus enum values."""
        assert RuleStatus.ENABLED.value == "enabled"
        assert RuleStatus.DISABLED.value == "disabled"
        assert RuleStatus.TESTING.value == "testing"
        assert RuleStatus.DEPRECATED.value == "deprecated"

    def test_rule_status_equality(self) -> None:
        """Test RuleStatus equality comparisons."""
        assert RuleStatus.ENABLED == RuleStatus.ENABLED
        # Test different enum values
        enabled_status = RuleStatus.ENABLED
        disabled_status = RuleStatus.DISABLED
        assert enabled_status != disabled_status

    def test_rule_status_string_representation(self) -> None:
        """Test string representation of RuleStatus."""
        assert str(RuleStatus.ENABLED) == "RuleStatus.ENABLED"


class TestDetectionRule:
    """Test DetectionRule dataclass and its methods."""

    def create_valid_rule(self, rule_id: str = "test_rule") -> DetectionRule:
        """Create a valid detection rule for testing."""
        return DetectionRule(
            rule_id=rule_id,
            name="Test Rule",
            description="A test detection rule",
            severity=SeverityLevel.MEDIUM,
            query="""
                SELECT timestamp, actor, source_ip FROM
                `{project_id}.{dataset_id}.cloudaudit_googleapis_com_activity`
                WHERE timestamp > TIMESTAMP('{last_scan_time}')
                AND timestamp <= TIMESTAMP('{current_time}')
            """,
            status=RuleStatus.ENABLED,
            tags=["test", "security"],
            metadata={"author": "test_user"},
            max_events_per_incident=50,
            correlation_window_minutes=30,
        )

    def test_detection_rule_creation(self) -> None:
        """Test basic DetectionRule creation."""
        rule = self.create_valid_rule()
        assert rule.rule_id == "test_rule"
        assert rule.name == "Test Rule"
        assert rule.description == "A test detection rule"
        assert rule.severity == SeverityLevel.MEDIUM
        assert rule.status == RuleStatus.ENABLED
        assert rule.tags == ["test", "security"]
        assert rule.metadata == {"author": "test_user"}
        assert rule.max_events_per_incident == 50
        assert rule.correlation_window_minutes == 30
        assert rule.last_executed is None
        assert rule.execution_count == 0
        assert rule.events_detected == 0
        assert rule.incidents_created == 0

    def test_detection_rule_default_values(self) -> None:
        """Test DetectionRule with default values."""
        rule = DetectionRule(
            rule_id="default_rule",
            name="Default Rule",
            description="Rule with defaults",
            severity=SeverityLevel.LOW,
            query="SELECT timestamp FROM table WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}') AND 1=1",
        )
        assert rule.status == RuleStatus.DISABLED
        assert rule.tags == []
        assert rule.metadata == {}
        assert rule.max_events_per_incident == 100
        assert rule.correlation_window_minutes == 60
        assert rule.execution_count == 0

    def test_validate_valid_rule(self) -> None:
        """Test validation of a valid rule."""
        rule = self.create_valid_rule()
        errors = rule.validate()
        assert not errors

    def test_validate_missing_required_fields(self) -> None:
        """Test validation with missing required fields."""
        # Missing rule_id
        rule = DetectionRule(
            rule_id="",
            name="Test",
            description="Test",
            severity=SeverityLevel.LOW,
            query="SELECT timestamp FROM table WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
        )
        errors = rule.validate()
        assert "rule_id is required" in errors

        # Missing name
        rule.rule_id = "test"
        rule.name = ""
        errors = rule.validate()
        assert "name is required" in errors

        # Missing description
        rule.name = "Test"
        rule.description = ""
        errors = rule.validate()
        assert "description is required" in errors

        # Missing query
        rule.description = "Test"
        rule.query = ""
        errors = rule.validate()
        assert "query is required" in errors

    def test_validate_correlation_window_limits(self) -> None:
        """Test correlation window validation limits."""
        rule = self.create_valid_rule()

        # Too low
        rule.correlation_window_minutes = 0
        errors = rule.validate()
        assert (
            "correlation_window_minutes must be between 1 and 1440 (24 hours)" in errors
        )

        # Too high
        rule.correlation_window_minutes = 1441
        errors = rule.validate()
        assert (
            "correlation_window_minutes must be between 1 and 1440 (24 hours)" in errors
        )

        # Valid boundaries
        rule.correlation_window_minutes = 1
        errors = rule.validate()
        assert (
            "correlation_window_minutes must be between 1 and 1440 (24 hours)"
            not in errors
        )

        rule.correlation_window_minutes = 1440
        errors = rule.validate()
        assert (
            "correlation_window_minutes must be between 1 and 1440 (24 hours)"
            not in errors
        )

    def test_validate_max_events_limits(self) -> None:
        """Test max events per incident validation limits."""
        rule = self.create_valid_rule()

        # Too low
        rule.max_events_per_incident = 0
        errors = rule.validate()
        assert "max_events_per_incident must be between 1 and 10000" in errors

        # Too high
        rule.max_events_per_incident = 10001
        errors = rule.validate()
        assert "max_events_per_incident must be between 1 and 10000" in errors

        # Valid boundaries
        rule.max_events_per_incident = 1
        errors = rule.validate()
        assert "max_events_per_incident must be between 1 and 10000" not in errors

        rule.max_events_per_incident = 10000
        errors = rule.validate()
        assert "max_events_per_incident must be between 1 and 10000" not in errors

    def test_validate_query_missing_placeholders(self) -> None:
        """Test query validation for missing required placeholders."""
        rule = self.create_valid_rule()

        # Missing project_id placeholder
        rule.query = "SELECT timestamp FROM `dataset.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')"
        errors = rule.validate()
        assert "Query missing required placeholder: {project_id}" in errors

        # Missing dataset_id placeholder
        rule.query = "SELECT timestamp FROM `{project_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')"
        errors = rule.validate()
        assert "Query missing required placeholder: {dataset_id}" in errors

        # Missing last_scan_time placeholder
        rule.query = "SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp <= TIMESTAMP('{current_time}')"
        errors = rule.validate()
        assert "Query missing required placeholder: {last_scan_time}" in errors

        # Missing current_time placeholder
        rule.query = "SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}')"
        errors = rule.validate()
        assert "Query missing required placeholder: {current_time}" in errors

    def test_validate_query_dangerous_operations(self) -> None:
        """Test query validation for dangerous SQL operations."""
        rule = self.create_valid_rule()

        dangerous_queries = [
            "DROP TABLE test; SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
            "DELETE FROM test; SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
            "TRUNCATE TABLE test; SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
            "INSERT INTO test VALUES (1); SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
            "UPDATE test SET x=1; SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
            "CREATE TABLE test; SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
            "ALTER TABLE test; SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
        ]

        patterns = ["DROP", "DELETE", "TRUNCATE", "INSERT", "UPDATE", "CREATE", "ALTER"]

        for i, query in enumerate(dangerous_queries):
            rule.query = query
            errors = rule.validate()
            assert any(
                f"Query contains dangerous operation: \\b{patterns[i]}\\b" in error
                for error in errors
            )

    def test_validate_query_missing_timestamp_field(self) -> None:
        """Test query validation for missing timestamp field."""
        rule = self.create_valid_rule()
        rule.query = "SELECT actor FROM `{project_id}.{dataset_id}.table` WHERE actor IS NOT NULL AND timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')"
        errors = rule.validate()
        assert "Query must select 'timestamp' field" in errors

    def test_validate_query_case_insensitive_timestamp(self) -> None:
        """Test query validation finds timestamp field case-insensitively."""
        rule = self.create_valid_rule()
        rule.query = "SELECT TIMESTAMP, actor FROM `{project_id}.{dataset_id}.table` WHERE TIMESTAMP > TIMESTAMP('{last_scan_time}') AND TIMESTAMP <= TIMESTAMP('{current_time}')"
        errors = rule.validate()
        # Should not have timestamp field error
        assert not any("timestamp" in error.lower() for error in errors)

    def test_to_dict(self) -> None:
        """Test converting DetectionRule to dictionary."""
        timestamp = datetime.now(timezone.utc)
        rule = self.create_valid_rule()
        rule.last_executed = timestamp
        rule.execution_count = 5
        rule.events_detected = 10
        rule.incidents_created = 2

        result = rule.to_dict()

        expected = {
            "rule_id": "test_rule",
            "name": "Test Rule",
            "description": "A test detection rule",
            "severity": "medium",
            "query": rule.query,
            "status": "enabled",
            "tags": ["test", "security"],
            "metadata": {"author": "test_user"},
            "max_events_per_incident": 50,
            "correlation_window_minutes": 30,
            "last_executed": timestamp.isoformat(),
            "execution_count": 5,
            "events_detected": 10,
            "incidents_created": 2,
        }

        assert result == expected

    def test_to_dict_no_last_executed(self) -> None:
        """Test to_dict with None last_executed."""
        rule = self.create_valid_rule()
        result = rule.to_dict()
        assert result["last_executed"] is None

    def test_from_dict_complete(self) -> None:
        """Test creating DetectionRule from complete dictionary."""
        timestamp = datetime.now(timezone.utc)
        data = {
            "rule_id": "from_dict_rule",
            "name": "From Dict Rule",
            "description": "Rule created from dict",
            "severity": "high",
            "query": "SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
            "status": "testing",
            "tags": ["dict", "test"],
            "metadata": {"created_by": "dict_test"},
            "max_events_per_incident": 75,
            "correlation_window_minutes": 45,
            "last_executed": timestamp.isoformat(),
            "execution_count": 3,
            "events_detected": 8,
            "incidents_created": 1,
        }

        rule = DetectionRule.from_dict(data)

        assert rule.rule_id == "from_dict_rule"
        assert rule.name == "From Dict Rule"
        assert rule.description == "Rule created from dict"
        assert rule.severity == SeverityLevel.HIGH
        assert rule.status == RuleStatus.TESTING
        assert rule.tags == ["dict", "test"]
        assert rule.metadata == {"created_by": "dict_test"}
        assert rule.max_events_per_incident == 75
        assert rule.correlation_window_minutes == 45
        assert rule.last_executed == timestamp
        assert rule.execution_count == 3
        assert rule.events_detected == 8
        assert rule.incidents_created == 1

    def test_from_dict_minimal(self) -> None:
        """Test creating DetectionRule from minimal dictionary."""
        data = {
            "rule_id": "minimal_rule",
            "name": "Minimal Rule",
            "description": "Minimal rule data",
            "severity": "critical",
            "query": "SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
        }

        rule = DetectionRule.from_dict(data)

        assert rule.rule_id == "minimal_rule"
        assert rule.name == "Minimal Rule"
        assert rule.description == "Minimal rule data"
        assert rule.severity == SeverityLevel.CRITICAL
        assert rule.status == RuleStatus.DISABLED  # Default
        assert rule.tags == []  # Default
        assert rule.metadata == {}  # Default
        assert rule.max_events_per_incident == 100  # Default
        assert rule.correlation_window_minutes == 60  # Default
        assert rule.last_executed is None  # Default
        assert rule.execution_count == 0  # Default
        assert rule.events_detected == 0  # Default
        assert rule.incidents_created == 0  # Default

    def test_from_dict_no_last_executed(self) -> None:
        """Test from_dict with None last_executed."""
        data = {
            "rule_id": "no_exec_rule",
            "name": "No Execution Rule",
            "description": "Rule with no execution",
            "severity": "low",
            "query": "SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
            "last_executed": None,
        }

        rule = DetectionRule.from_dict(data)
        assert rule.last_executed is None


class TestRulesEngine:
    """Test RulesEngine class and its methods."""

    def create_test_rule(
        self, rule_id: str, status: RuleStatus = RuleStatus.DISABLED
    ) -> DetectionRule:
        """Create a test rule with given ID and status."""
        return DetectionRule(
            rule_id=rule_id,
            name=f"Test Rule {rule_id}",
            description=f"Test rule with ID {rule_id}",
            severity=SeverityLevel.MEDIUM,
            query="SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
            status=status,
            tags=["test"],
        )

    def test_rules_engine_initialization(self) -> None:
        """Test RulesEngine initialization and builtin rules loading."""
        engine = RulesEngine()

        # Should have some rules loaded from builtin modules
        assert len(engine.rules) > 0

        # Check that builtin rules are loaded
        rule_ids = list(engine.rules.keys())

        # Should have some suspicious_login rule from builtin_rules
        suspicious_login_found = any(
            "suspicious_login" in rule_id for rule_id in rule_ids
        )
        assert (
            suspicious_login_found
        ), f"Expected suspicious_login rule, found: {rule_ids}"

        # Should have some VPC and firewall rules
        vpc_rules_found = any("vpc_" in rule_id for rule_id in rule_ids)
        firewall_rules_found = any("firewall_" in rule_id for rule_id in rule_ids)

        # At least one should be loaded (VPC or firewall rules)
        assert (
            vpc_rules_found or firewall_rules_found
        ), f"Expected VPC or firewall rules, found: {rule_ids}"

    def test_add_rule_valid(self) -> None:
        """Test adding a valid rule."""
        engine = RulesEngine()
        initial_count = len(engine.rules)

        rule = self.create_test_rule("new_rule")
        engine.add_rule(rule)

        assert len(engine.rules) == initial_count + 1
        assert "new_rule" in engine.rules
        assert engine.rules["new_rule"] == rule

    def test_add_rule_invalid(self) -> None:
        """Test adding an invalid rule raises ValueError."""
        engine = RulesEngine()

        # Create invalid rule (missing required fields)
        invalid_rule = DetectionRule(
            rule_id="",  # Invalid empty rule_id
            name="Invalid Rule",
            description="Rule with invalid data",
            severity=SeverityLevel.LOW,
            query="SELECT timestamp FROM table WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
        )

        with pytest.raises(ValueError) as exc_info:
            engine.add_rule(invalid_rule)

        assert "Invalid rule:" in str(exc_info.value)
        assert "rule_id is required" in str(exc_info.value)

    def test_add_rule_duplicate(self) -> None:
        """Test adding a rule with duplicate ID raises ValueError."""
        engine = RulesEngine()

        rule1 = self.create_test_rule("duplicate_rule")
        rule2 = self.create_test_rule("duplicate_rule")

        engine.add_rule(rule1)

        with pytest.raises(ValueError) as exc_info:
            engine.add_rule(rule2)

        assert "Rule with ID 'duplicate_rule' already exists" in str(exc_info.value)

    def test_get_rule_exists(self) -> None:
        """Test getting an existing rule."""
        engine = RulesEngine()
        rule = self.create_test_rule("get_rule_test")
        engine.add_rule(rule)

        result = engine.get_rule("get_rule_test")
        assert result == rule

    def test_get_rule_not_exists(self) -> None:
        """Test getting a non-existent rule returns None."""
        engine = RulesEngine()
        result = engine.get_rule("nonexistent_rule")
        assert result is None

    def test_get_enabled_rules(self) -> None:
        """Test getting only enabled rules."""
        engine = RulesEngine()

        # Clear existing rules for clean test
        engine.rules.clear()

        enabled_rule1 = self.create_test_rule("enabled1", RuleStatus.ENABLED)
        enabled_rule2 = self.create_test_rule("enabled2", RuleStatus.ENABLED)
        disabled_rule = self.create_test_rule("disabled", RuleStatus.DISABLED)
        testing_rule = self.create_test_rule("testing", RuleStatus.TESTING)

        engine.add_rule(enabled_rule1)
        engine.add_rule(enabled_rule2)
        engine.add_rule(disabled_rule)
        engine.add_rule(testing_rule)

        enabled_rules = engine.get_enabled_rules()

        assert len(enabled_rules) == 2
        rule_ids = [rule.rule_id for rule in enabled_rules]
        assert "enabled1" in rule_ids
        assert "enabled2" in rule_ids
        assert "disabled" not in rule_ids
        assert "testing" not in rule_ids

    def test_update_rule_status_exists(self) -> None:
        """Test updating status of existing rule."""
        engine = RulesEngine()
        rule = self.create_test_rule("status_update_test", RuleStatus.DISABLED)
        engine.add_rule(rule)

        engine.update_rule_status("status_update_test", RuleStatus.ENABLED)

        assert engine.rules["status_update_test"].status == RuleStatus.ENABLED

    def test_update_rule_status_not_exists(self) -> None:
        """Test updating status of non-existent rule raises ValueError."""
        engine = RulesEngine()

        with pytest.raises(ValueError) as exc_info:
            engine.update_rule_status("nonexistent", RuleStatus.ENABLED)

        assert "Rule with ID 'nonexistent' not found" in str(exc_info.value)

    def test_enable_rule(self) -> None:
        """Test enabling a rule."""
        engine = RulesEngine()
        rule = self.create_test_rule("enable_test", RuleStatus.DISABLED)
        engine.add_rule(rule)

        engine.enable_rule("enable_test")

        assert engine.rules["enable_test"].status == RuleStatus.ENABLED

    def test_disable_rule(self) -> None:
        """Test disabling a rule."""
        engine = RulesEngine()
        rule = self.create_test_rule("disable_test", RuleStatus.ENABLED)
        engine.add_rule(rule)

        engine.disable_rule("disable_test")

        assert engine.rules["disable_test"].status == RuleStatus.DISABLED

    def test_update_rule_stats_exists(self) -> None:
        """Test updating statistics for existing rule."""
        engine = RulesEngine()
        rule = self.create_test_rule("stats_test")
        engine.add_rule(rule)

        # Record initial values
        initial_execution_count = rule.execution_count
        initial_events_detected = rule.events_detected
        initial_incidents_created = rule.incidents_created
        initial_last_executed = rule.last_executed

        # Update stats
        engine.update_rule_stats("stats_test", events_detected=5, incidents_created=2)

        updated_rule = engine.rules["stats_test"]
        assert updated_rule.execution_count == initial_execution_count + 1
        assert updated_rule.events_detected == initial_events_detected + 5
        assert updated_rule.incidents_created == initial_incidents_created + 2
        assert updated_rule.last_executed is not None
        assert updated_rule.last_executed != initial_last_executed
        assert updated_rule.last_executed.tzinfo == timezone.utc

    def test_update_rule_stats_default_values(self) -> None:
        """Test updating rule stats with default parameter values."""
        engine = RulesEngine()
        rule = self.create_test_rule("stats_default_test")
        engine.add_rule(rule)

        initial_execution_count = rule.execution_count
        initial_events_detected = rule.events_detected
        initial_incidents_created = rule.incidents_created

        # Update with defaults (0 events, 0 incidents)
        engine.update_rule_stats("stats_default_test")

        updated_rule = engine.rules["stats_default_test"]
        assert updated_rule.execution_count == initial_execution_count + 1
        assert updated_rule.events_detected == initial_events_detected + 0
        assert updated_rule.incidents_created == initial_incidents_created + 0
        assert updated_rule.last_executed is not None

    def test_update_rule_stats_not_exists(self) -> None:
        """Test updating stats for non-existent rule (should not crash)."""
        engine = RulesEngine()

        # Should not raise exception, just return silently
        engine.update_rule_stats("nonexistent", events_detected=5, incidents_created=2)

    def test_get_rules_by_tag(self) -> None:
        """Test getting rules by tag."""
        engine = RulesEngine()
        engine.rules.clear()  # Clear for clean test

        rule1 = self.create_test_rule("tag_test1")
        rule1.tags = ["security", "network"]

        rule2 = self.create_test_rule("tag_test2")
        rule2.tags = ["security", "auth"]

        rule3 = self.create_test_rule("tag_test3")
        rule3.tags = ["performance", "monitoring"]

        engine.add_rule(rule1)
        engine.add_rule(rule2)
        engine.add_rule(rule3)

        # Test finding by "security" tag
        security_rules = engine.get_rules_by_tag("security")
        security_rule_ids = [rule.rule_id for rule in security_rules]

        assert len(security_rules) == 2
        assert "tag_test1" in security_rule_ids
        assert "tag_test2" in security_rule_ids
        assert "tag_test3" not in security_rule_ids

        # Test finding by "network" tag
        network_rules = engine.get_rules_by_tag("network")
        assert len(network_rules) == 1
        assert network_rules[0].rule_id == "tag_test1"

        # Test finding by non-existent tag
        nonexistent_rules = engine.get_rules_by_tag("nonexistent")
        assert len(nonexistent_rules) == 0

    def test_get_rules_by_severity(self) -> None:
        """Test getting rules by severity level."""
        engine = RulesEngine()
        engine.rules.clear()  # Clear for clean test

        critical_rule = self.create_test_rule("critical_test")
        critical_rule.severity = SeverityLevel.CRITICAL

        high_rule1 = self.create_test_rule("high_test1")
        high_rule1.severity = SeverityLevel.HIGH

        high_rule2 = self.create_test_rule("high_test2")
        high_rule2.severity = SeverityLevel.HIGH

        medium_rule = self.create_test_rule("medium_test")
        medium_rule.severity = SeverityLevel.MEDIUM

        engine.add_rule(critical_rule)
        engine.add_rule(high_rule1)
        engine.add_rule(high_rule2)
        engine.add_rule(medium_rule)

        # Test finding HIGH severity rules
        high_rules = engine.get_rules_by_severity(SeverityLevel.HIGH)
        high_rule_ids = [rule.rule_id for rule in high_rules]

        assert len(high_rules) == 2
        assert "high_test1" in high_rule_ids
        assert "high_test2" in high_rule_ids
        assert "critical_test" not in high_rule_ids
        assert "medium_test" not in high_rule_ids

        # Test finding CRITICAL severity rules
        critical_rules = engine.get_rules_by_severity(SeverityLevel.CRITICAL)
        assert len(critical_rules) == 1
        assert critical_rules[0].rule_id == "critical_test"

        # Test finding LOW severity rules (none exist)
        low_rules = engine.get_rules_by_severity(SeverityLevel.LOW)
        assert len(low_rules) == 0

    def test_export_rules(self) -> None:
        """Test exporting all rules."""
        engine = RulesEngine()
        engine.rules.clear()  # Clear for clean test

        rule1 = self.create_test_rule("export_test1", RuleStatus.ENABLED)
        rule2 = self.create_test_rule("export_test2", RuleStatus.DISABLED)

        engine.add_rule(rule1)
        engine.add_rule(rule2)

        export_data = engine.export_rules()

        assert "rules" in export_data
        assert "total_rules" in export_data
        assert "enabled_rules" in export_data
        assert "export_timestamp" in export_data

        assert export_data["total_rules"] == 2
        assert export_data["enabled_rules"] == 1

        # Check export timestamp format
        export_timestamp = export_data["export_timestamp"]
        assert "T" in export_timestamp  # ISO format
        assert (
            export_timestamp.endswith("Z") or "+" in export_timestamp
        )  # Timezone info

        # Check rules list
        rules_list = export_data["rules"]
        assert len(rules_list) == 2

        # Verify rules are exported as dictionaries
        rule_ids = [rule_dict["rule_id"] for rule_dict in rules_list]
        assert "export_test1" in rule_ids
        assert "export_test2" in rule_ids

        # Verify rule structure
        for rule_dict in rules_list:
            assert "rule_id" in rule_dict
            assert "name" in rule_dict
            assert "severity" in rule_dict
            assert "status" in rule_dict

    def test_import_rules_valid(self) -> None:
        """Test importing valid rules."""
        engine = RulesEngine()
        initial_count = len(engine.rules)

        import_data = {
            "rules": [
                {
                    "rule_id": "import_test1",
                    "name": "Import Test 1",
                    "description": "First imported rule",
                    "severity": "high",
                    "query": "SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
                    "status": "enabled",
                    "tags": ["imported"],
                },
                {
                    "rule_id": "import_test2",
                    "name": "Import Test 2",
                    "description": "Second imported rule",
                    "severity": "medium",
                    "query": "SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
                    "tags": ["imported", "test"],
                },
            ]
        }

        engine.import_rules(import_data)

        # Check that rules were imported
        assert len(engine.rules) >= initial_count + 2
        assert "import_test1" in engine.rules
        assert "import_test2" in engine.rules

        # Verify imported rule properties
        rule1 = engine.rules["import_test1"]
        assert rule1.name == "Import Test 1"
        assert rule1.severity == SeverityLevel.HIGH
        assert rule1.status == RuleStatus.ENABLED
        assert "imported" in rule1.tags

        rule2 = engine.rules["import_test2"]
        assert rule2.name == "Import Test 2"
        assert rule2.severity == SeverityLevel.MEDIUM
        assert rule2.status == RuleStatus.DISABLED  # Default status
        assert rule2.tags == ["imported", "test"]

    def test_import_rules_empty_list(self) -> None:
        """Test importing empty rules list."""
        engine = RulesEngine()
        initial_count = len(engine.rules)

        import_data: Dict[str, Any] = {"rules": []}
        engine.import_rules(import_data)

        # Should not change rule count
        assert len(engine.rules) == initial_count

    def test_import_rules_no_rules_key(self) -> None:
        """Test importing data without 'rules' key."""
        engine = RulesEngine()
        initial_count = len(engine.rules)

        import_data = {"other_data": "value"}
        engine.import_rules(import_data)

        # Should not change rule count
        assert len(engine.rules) == initial_count

    def test_import_rules_invalid_rule_data(self) -> None:
        """Test importing invalid rule data (should skip and continue)."""
        engine = RulesEngine()
        initial_count = len(engine.rules)

        import_data = {
            "rules": [
                {
                    "rule_id": "valid_import",
                    "name": "Valid Rule",
                    "description": "Valid rule for import",
                    "severity": "low",
                    "query": "SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
                },
                {
                    "rule_id": "",  # Invalid - empty rule_id
                    "name": "Invalid Rule",
                    "description": "Rule with invalid data",
                    "severity": "medium",
                    "query": "SELECT timestamp FROM table WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
                },
                {
                    # Missing required fields
                    "rule_id": "incomplete_rule"
                },
            ]
        }

        engine.import_rules(import_data)

        # Should import only the valid rule
        assert len(engine.rules) == initial_count + 1
        assert "valid_import" in engine.rules
        assert "" not in engine.rules  # Invalid rule not imported
        assert "incomplete_rule" not in engine.rules  # Incomplete rule not imported

    def test_import_rules_duplicate_existing(self) -> None:
        """Test importing rules that already exist (should not overwrite)."""
        engine = RulesEngine()

        # Add initial rule
        existing_rule = self.create_test_rule("existing_rule")
        existing_rule.name = "Original Name"
        engine.add_rule(existing_rule)

        # Try to import rule with same ID but different name
        import_data = {
            "rules": [
                {
                    "rule_id": "existing_rule",
                    "name": "New Name",
                    "description": "Attempting to overwrite",
                    "severity": "critical",
                    "query": "SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
                }
            ]
        }

        engine.import_rules(import_data)

        # Original rule should remain unchanged
        rule = engine.rules["existing_rule"]
        assert rule is not None
        assert rule.name == "Original Name"  # Should not be overwritten
        assert rule.severity == SeverityLevel.MEDIUM  # Original value


class TestRulesEngineEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_rules_engine_with_complex_builtin_rules(self) -> None:
        """Test that engine properly loads complex builtin rules."""
        engine = RulesEngine()

        # Should have multiple types of rules loaded
        all_rule_ids = list(engine.rules.keys())

        # Should have at least some rules
        assert len(all_rule_ids) > 0

        # Test that we can get rules by different categories
        all_rules = list(engine.rules.values())

        # Should have rules with different severities
        severities = {rule.severity for rule in all_rules}
        assert len(severities) > 1  # Multiple severity levels

        # Should have rules with tags
        tagged_rules = [rule for rule in all_rules if rule.tags]
        assert len(tagged_rules) > 0

        # Test that all loaded rules are valid
        for rule in all_rules:
            errors = rule.validate()
            assert (
                not errors
            ), f"Builtin rule {rule.rule_id} has validation errors: {errors}"

    def test_complete_workflow(self) -> None:
        """Test complete workflow with rule management."""
        engine = RulesEngine()

        # Create and add a new rule
        custom_rule = DetectionRule(
            rule_id="workflow_test",
            name="Workflow Test Rule",
            description="Testing complete workflow",
            severity=SeverityLevel.HIGH,
            query="SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}')",
            tags=["workflow", "test"],
        )

        engine.add_rule(custom_rule)

        # Enable the rule
        engine.enable_rule("workflow_test")
        rule = engine.get_rule("workflow_test")
        assert rule is not None
        assert rule.status == RuleStatus.ENABLED

        # Update statistics
        engine.update_rule_stats(
            "workflow_test", events_detected=15, incidents_created=3
        )

        rule = engine.get_rule("workflow_test")
        assert rule is not None
        assert rule.execution_count == 1
        assert rule.events_detected == 15
        assert rule.incidents_created == 3
        assert rule.last_executed is not None

        # Export and re-import
        export_data = engine.export_rules()

        # Create new engine and import
        new_engine = RulesEngine()
        new_engine.import_rules(export_data)

        # Verify imported rule
        imported_rule = new_engine.get_rule("workflow_test")
        assert imported_rule is not None
        assert imported_rule.name == "Workflow Test Rule"
        assert imported_rule.severity == SeverityLevel.HIGH
        assert imported_rule.tags == ["workflow", "test"]

    def test_unicode_and_special_characters(self) -> None:
        """Test handling of Unicode and special characters."""
        engine = RulesEngine()

        unicode_rule = DetectionRule(
            rule_id="unicode_test_¿¡",
            name="Unicode Test Rule ∑∆√",
            description="Testing Unicode: Ñoño, 中文, العربية, Русский",
            severity=SeverityLevel.MEDIUM,
            query="SELECT timestamp FROM `{project_id}.{dataset_id}.table` WHERE timestamp > TIMESTAMP('{last_scan_time}') AND timestamp <= TIMESTAMP('{current_time}') AND message LIKE '%ñ%'",
            tags=["unicode", "测试", "тест"],
        )

        engine.add_rule(unicode_rule)

        # Verify rule was added correctly
        retrieved_rule = engine.get_rule("unicode_test_¿¡")
        assert retrieved_rule is not None
        assert retrieved_rule.name == "Unicode Test Rule ∑∆√"
        assert "中文" in retrieved_rule.description
        assert "测试" in retrieved_rule.tags

        # Test export/import with Unicode
        export_data = engine.export_rules()

        new_engine = RulesEngine()
        new_engine.import_rules(export_data)

        imported_rule = new_engine.get_rule("unicode_test_¿¡")
        assert imported_rule is not None
        assert imported_rule.description == unicode_rule.description
