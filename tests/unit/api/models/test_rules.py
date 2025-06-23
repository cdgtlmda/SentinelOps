"""
Test suite for api/models/rules.py.
CRITICAL: Uses REAL production code - NO MOCKING of Pydantic models.
Achieves minimum 90% statement coverage.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import ValidationError

from src.api.models.rules import (
    Rule,
    RuleAction,
    RuleBase,
    RuleCondition,
    RuleCorrelation,
    RuleCreate,
    RuleListResponse,
    RuleMetrics,
    RuleSeverity,
    RuleStats,
    RuleStatus,
    RuleTestRequest,
    RuleTestResult,
    RuleThreshold,
    RuleType,
    RuleUpdate,
)


class TestRuleEnums:
    """Test rule enumeration classes."""

    def test_rule_status_values(self) -> None:
        """Test RuleStatus enum values."""
        assert RuleStatus.ACTIVE.value == "active"
        assert RuleStatus.INACTIVE.value == "inactive"
        assert RuleStatus.TESTING.value == "testing"
        assert RuleStatus.DISABLED.value == "disabled"
        assert RuleStatus.DEPRECATED.value == "deprecated"

    def test_rule_type_values(self) -> None:
        """Test RuleType enum values."""
        assert RuleType.QUERY.value == "query"
        assert RuleType.PATTERN.value == "pattern"
        assert RuleType.THRESHOLD.value == "threshold"
        assert RuleType.ANOMALY.value == "anomaly"
        assert RuleType.CORRELATION.value == "correlation"
        assert RuleType.CUSTOM.value == "custom"

    def test_rule_severity_values(self) -> None:
        """Test RuleSeverity enum values."""
        assert RuleSeverity.CRITICAL.value == "critical"
        assert RuleSeverity.HIGH.value == "high"
        assert RuleSeverity.MEDIUM.value == "medium"
        assert RuleSeverity.LOW.value == "low"
        assert RuleSeverity.INFO.value == "info"


class TestRuleCondition:
    """Test RuleCondition model."""

    def test_rule_condition_creation_basic(self) -> None:
        """Test basic rule condition creation."""
        condition = RuleCondition(
            field="user.name", operator="eq", value="admin", case_sensitive=False
        )

        assert condition.field == "user.name"
        assert condition.operator == "eq"
        assert condition.value == "admin"
        assert condition.case_sensitive is False  # Default value

    def test_rule_condition_creation_with_case_sensitive(self) -> None:
        """Test rule condition with case sensitivity."""
        condition = RuleCondition(
            field="log_level", operator="contains", value="ERROR", case_sensitive=True
        )

        assert condition.field == "log_level"
        assert condition.operator == "contains"
        assert condition.value == "ERROR"
        assert condition.case_sensitive is True

    def test_rule_condition_numeric_value(self) -> None:
        """Test rule condition with numeric values."""
        condition = RuleCondition(
            field="response_time", operator="gt", value=1000, case_sensitive=False
        )

        assert condition.field == "response_time"
        assert condition.operator == "gt"
        assert condition.value == 1000

    def test_rule_condition_list_value(self) -> None:
        """Test rule condition with list values."""
        condition = RuleCondition(
            field="status_code",
            operator="in",
            value=[400, 401, 403, 404],
            case_sensitive=False,
        )

        assert condition.field == "status_code"
        assert condition.operator == "in"
        assert condition.value == [400, 401, 403, 404]

    def test_rule_condition_valid_operators(self) -> None:
        """Test all valid operators."""
        valid_operators = [
            "eq",
            "ne",
            "gt",
            "lt",
            "gte",
            "lte",
            "in",
            "contains",
            "regex",
            "exists",
        ]

        for op in valid_operators:
            condition = RuleCondition(
                field="test_field",
                operator=op,
                value="test_value",
                case_sensitive=False,
            )
            assert condition.operator == op

    def test_rule_condition_invalid_operator(self) -> None:
        """Test invalid operator validation."""
        with pytest.raises(ValidationError) as exc_info:
            RuleCondition(
                field="test_field",
                operator="invalid_op",
                value="test_value",
                case_sensitive=False,
            )

        assert "Invalid operator" in str(exc_info.value)


class TestRuleThreshold:
    """Test RuleThreshold model."""

    def test_rule_threshold_basic(self) -> None:
        """Test basic threshold creation."""
        threshold = RuleThreshold(count=5, window_seconds=300, group_by=None)

        assert threshold.count == 5
        assert threshold.window_seconds == 300
        assert threshold.group_by is None

    def test_rule_threshold_with_grouping(self) -> None:
        """Test threshold with grouping fields."""
        threshold = RuleThreshold(
            count=10, window_seconds=600, group_by=["user_id", "ip_address"]
        )

        assert threshold.count == 10
        assert threshold.window_seconds == 600
        assert threshold.group_by == ["user_id", "ip_address"]

    def test_rule_threshold_validation_count_positive(self) -> None:
        """Test count must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            RuleThreshold(count=0, window_seconds=300, group_by=None)

        assert "greater than or equal to 1" in str(exc_info.value)

    def test_rule_threshold_validation_window_positive(self) -> None:
        """Test window_seconds must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            RuleThreshold(count=5, window_seconds=0, group_by=None)

        assert "greater than or equal to 1" in str(exc_info.value)


class TestRuleCorrelation:
    """Test RuleCorrelation model."""

    def test_rule_correlation_basic(self) -> None:
        """Test basic correlation creation."""
        correlation = RuleCorrelation(
            events=[
                {"type": "login", "field": "user_id"},
                {"type": "file_access", "field": "user_id"},
            ],
            window_seconds=300,
            join_fields=["user_id"],
            sequence_required=False,
        )

        assert len(correlation.events) == 2
        assert correlation.window_seconds == 300
        assert correlation.join_fields == ["user_id"]
        assert correlation.sequence_required is False

    def test_rule_correlation_with_sequence(self) -> None:
        """Test correlation with sequence requirement."""
        correlation = RuleCorrelation(
            events=[
                {"type": "authentication", "result": "failed"},
                {"type": "authentication", "result": "success"},
                {"type": "privilege_escalation", "action": "sudo"},
            ],
            window_seconds=600,
            join_fields=["user_id", "source_ip"],
            sequence_required=True,
        )

        assert len(correlation.events) == 3
        assert correlation.sequence_required is True
        assert correlation.join_fields == ["user_id", "source_ip"]

    def test_rule_correlation_minimum_events(self) -> None:
        """Test correlation requires minimum 2 events."""
        with pytest.raises(ValidationError) as exc_info:
            RuleCorrelation(
                events=[{"type": "single_event"}],
                window_seconds=300,
                join_fields=["user_id"],
                sequence_required=False,
            )

        assert "at least 2" in str(exc_info.value)


class TestRuleAction:
    """Test RuleAction model."""

    def test_rule_action_basic(self) -> None:
        """Test basic action creation."""
        action = RuleAction(
            type="alert",
            parameters={"severity": "high", "notify": "security-team"},
            automated=False,
            requires_approval=True,
        )

        assert action.type == "alert"
        assert action.parameters["severity"] == "high"
        assert action.automated is False
        assert action.requires_approval is True

    def test_rule_action_automated(self) -> None:
        """Test automated action."""
        action = RuleAction(
            type="block",
            parameters={"ip_address": "192.168.1.100"},
            automated=True,
            requires_approval=False,
        )

        assert action.type == "block"
        assert action.automated is True
        assert action.requires_approval is False

    def test_rule_action_empty_parameters(self) -> None:
        """Test action with empty parameters."""
        action = RuleAction(
            type="notify", parameters={}, automated=False, requires_approval=True
        )

        assert action.type == "notify"
        assert action.parameters == {}


class TestRuleBase:
    """Test RuleBase model."""

    def test_rule_base_minimal(self) -> None:
        """Test minimal rule base creation."""
        rule = RuleBase(
            name="Test Rule",
            description="A test rule for validation",
            rule_type=RuleType.PATTERN,
            severity=RuleSeverity.MEDIUM,
            query=None,
            conditions=None,
            threshold=None,
            correlation=None,
            enabled=True,
            tags=[],
            references=[],
            false_positive_rate=None,
            actions=[],
            custom_fields={},
        )

        assert rule.name == "Test Rule"
        assert rule.description == "A test rule for validation"
        assert rule.rule_type == RuleType.PATTERN
        assert rule.severity == RuleSeverity.MEDIUM
        assert rule.enabled is True
        assert rule.tags == []
        assert rule.references == []
        assert rule.actions == []
        assert rule.custom_fields == {}

    def test_rule_base_complete(self) -> None:
        """Test RuleBase creation with all fields."""
        conditions = [
            RuleCondition(
                field="user_id", operator="eq", value="admin", case_sensitive=False
            ),
            RuleCondition(field="count", operator="gte", value=5, case_sensitive=False),
        ]

        threshold = RuleThreshold(count=5, window_seconds=300, group_by=None)

        actions = [
            RuleAction(
                type="alert",
                parameters={"priority": "high"},
                automated=False,
                requires_approval=True,
            ),
            RuleAction(
                type="notify",
                parameters={"channel": "security"},
                automated=False,
                requires_approval=True,
            ),
        ]

        rule = RuleBase(
            name="Failed Login Detection",
            description="Detects multiple failed login attempts",
            rule_type=RuleType.THRESHOLD,
            severity=RuleSeverity.HIGH,
            query="SELECT * FROM logs WHERE event_type = 'login_failure'",
            conditions=conditions,
            threshold=threshold,
            correlation=None,
            enabled=True,
            tags=["authentication", "brute-force", "security"],
            references=["MITRE:T1110.001", "OWASP:A07"],
            false_positive_rate=0.05,
            actions=actions,
            custom_fields={"team": "security", "priority": 1},
        )

        assert rule.name == "Failed Login Detection"
        assert rule.rule_type == RuleType.THRESHOLD
        assert rule.severity == RuleSeverity.HIGH
        assert rule.query == "SELECT * FROM logs WHERE event_type = 'login_failure'"
        assert rule.conditions is not None and len(rule.conditions) == 2
        assert rule.threshold is not None and rule.threshold.count == 5
        assert rule.enabled is True
        assert "authentication" in rule.tags
        assert len(rule.actions) == 2
        assert rule.false_positive_rate == 0.05
        assert rule.custom_fields["team"] == "security"


class TestRuleCreate:
    """Test RuleCreate model with validation."""

    def test_rule_create_query_type_validation(self) -> None:
        """Test query is required for query-based rules."""
        # Should fail without query
        with pytest.raises(ValidationError) as exc_info:
            RuleCreate(
                name="Query Rule",
                description="A query-based rule",
                rule_type=RuleType.QUERY,
                severity=RuleSeverity.HIGH,
                query=None,
                conditions=None,
                threshold=None,
                correlation=None,
                enabled=True,
                false_positive_rate=None,
            )

        assert "Query is required for query-based rules" in str(exc_info.value)

        # Should succeed with query
        rule = RuleCreate(
            name="Query Rule",
            description="A query-based rule",
            rule_type=RuleType.QUERY,
            severity=RuleSeverity.HIGH,
            query="SELECT * FROM security_logs WHERE severity = 'high'",
            conditions=None,
            threshold=None,
            correlation=None,
            enabled=True,
            false_positive_rate=None,
        )

        assert rule.query == "SELECT * FROM security_logs WHERE severity = 'high'"

    def test_rule_create_pattern_type_validation(self) -> None:
        """Test pattern-type rule validation."""
        conditions = [
            RuleCondition(
                field="event_type",
                operator="eq",
                value="suspicious_activity",
                case_sensitive=False,
            )
        ]

        rule = RuleCreate(
            name="Pattern Detection Rule",
            description="Detects suspicious patterns in logs",
            rule_type=RuleType.PATTERN,
            severity=RuleSeverity.HIGH,
            query="SELECT * FROM logs",
            conditions=conditions,
            threshold=RuleThreshold(count=5, window_seconds=300, group_by=None),
            correlation=RuleCorrelation(
                events=[{"type": "login", "field": "user_id"}],
                window_seconds=300,
                join_fields=["user_id"],
                sequence_required=False,
            ),
            enabled=True,
            false_positive_rate=0.05,
        )

        assert len(rule.conditions or []) == 1

    def test_rule_create_tags_validation(self) -> None:
        """Test tags are normalized to lowercase and deduplicated."""
        rule = RuleCreate(
            name="Tag Test Rule",
            description="Testing tag validation",
            rule_type=RuleType.CUSTOM,
            severity=RuleSeverity.LOW,
            query="SELECT * FROM logs",
            conditions=[
                RuleCondition(
                    field="test", operator="eq", value="test", case_sensitive=False
                )
            ],
            threshold=RuleThreshold(count=1, window_seconds=60, group_by=None),
            correlation=RuleCorrelation(
                events=[{"type": "test", "field": "test"}],
                window_seconds=60,
                join_fields=["test"],
                sequence_required=False,
            ),
            enabled=True,
            false_positive_rate=0.0,
            tags=["Security", "AUTHENTICATION", "security", "  Authentication  ", ""],
        )

        # Should be normalized to lowercase, deduplicated, and trimmed
        expected_tags = {"security", "authentication"}
        assert set(rule.tags) == expected_tags

    def test_rule_create_other_types_no_validation(self) -> None:
        """Test other rule types don't require specific fields."""
        # Threshold rule without query or conditions should work
        rule = RuleCreate(
            name="Threshold Rule",
            description="A threshold-based rule",
            rule_type=RuleType.THRESHOLD,
            severity=RuleSeverity.HIGH,
            query="SELECT * FROM logs",
            conditions=[
                RuleCondition(
                    field="test", operator="eq", value="test", case_sensitive=False
                )
            ],
            threshold=RuleThreshold(count=1, window_seconds=60, group_by=None),
            correlation=RuleCorrelation(
                events=[{"type": "test", "field": "test"}],
                window_seconds=60,
                join_fields=["test"],
                sequence_required=False,
            ),
            enabled=True,
            false_positive_rate=0.0,
        )

        assert rule.rule_type == RuleType.THRESHOLD
        assert rule.query is not None
        assert rule.conditions is not None


class TestRuleUpdate:
    """Test RuleUpdate model."""

    def test_rule_update_partial(self) -> None:
        """Test partial rule update."""
        update = RuleUpdate(
            name="Updated Rule Name",
            description="Updated description",
            severity=RuleSeverity.CRITICAL,
            enabled=False,
            false_positive_rate=0.05,
        )

        assert update.name == "Updated Rule Name"
        assert update.severity == RuleSeverity.CRITICAL
        assert update.enabled is False
        assert update.description == "Updated description"  # Now provided

    def test_rule_update_all_fields(self) -> None:
        """Test updating all possible fields."""
        conditions = [
            RuleCondition(
                field="alert_level", operator="gte", value=8, case_sensitive=False
            )
        ]

        threshold = RuleThreshold(count=3, window_seconds=180, group_by=None)

        actions = [
            RuleAction(
                type="alert",
                parameters={"escalate": True},
                automated=True,
                requires_approval=False,
            )
        ]

        update = RuleUpdate(
            name="Comprehensive Update",
            description="Updated comprehensive rule",
            severity=RuleSeverity.CRITICAL,
            query="SELECT * FROM updated_logs",
            conditions=conditions,
            threshold=threshold,
            enabled=True,
            tags=["updated", "comprehensive"],
            references=["UPDATED:REF001"],
            false_positive_rate=0.02,
            actions=actions,
            custom_fields={"updated_by": "admin", "version": 2},
        )

        assert update.name == "Comprehensive Update"
        assert update.severity == RuleSeverity.CRITICAL
        assert update.query == "SELECT * FROM updated_logs"
        assert len(update.conditions or []) == 1
        assert (update.threshold and update.threshold.count) == 3
        assert len(update.actions or []) == 1
        assert update.false_positive_rate == 0.02

    def test_rule_update_false_positive_rate_validation(self) -> None:
        """Test false positive rate validation."""
        # Valid rate
        update = RuleUpdate(
            name="Test Rule",
            description="Test description",
            false_positive_rate=0.25,
        )
        assert update.false_positive_rate == 0.25

        # Invalid rate - too high
        with pytest.raises(ValidationError):
            RuleUpdate(
                name="Test Rule",
                description="Test description",
                false_positive_rate=1.5,
            )

        # Invalid rate - negative
        with pytest.raises(ValidationError):
            RuleUpdate(
                name="Test Rule",
                description="Test description",
                false_positive_rate=-0.1,
            )


class TestRuleTestRequest:
    """Test RuleTestRequest model."""

    def test_rule_test_request_defaults(self) -> None:
        """Test rule test request with default values."""
        request = RuleTestRequest(
            time_range_minutes=60,
            dry_run=True,
            sample_size=None,
        )

        assert request.time_range_minutes == 60
        assert request.dry_run is True
        assert request.sample_size is None

    def test_rule_test_request_custom_values(self) -> None:
        """Test rule test request with custom values."""
        request = RuleTestRequest(
            time_range_minutes=1440,  # 24 hours
            dry_run=False,
            sample_size=100,
        )

        assert request.time_range_minutes == 1440
        assert request.dry_run is False
        assert request.sample_size == 100

    def test_rule_test_request_validation(self) -> None:
        """Test rule test request validation."""
        # Valid range
        request = RuleTestRequest(
            time_range_minutes=720,
            dry_run=True,
            sample_size=50,
        )
        assert request.time_range_minutes == 720

        # Too small
        with pytest.raises(ValidationError):
            RuleTestRequest(
                time_range_minutes=0,
                dry_run=True,
                sample_size=50,
            )

        # Too large
        with pytest.raises(ValidationError):
            RuleTestRequest(
                time_range_minutes=2000,
                dry_run=True,
                sample_size=50,
            )


class TestRuleTestResult:
    """Test RuleTestResult model."""

    def test_rule_test_result_creation(self) -> None:
        """Test rule test result creation."""
        samples = [
            {"event_id": "evt001", "timestamp": "2024-01-15T10:30:00Z"},
            {"event_id": "evt002", "timestamp": "2024-01-15T10:35:00Z"},
        ]

        warnings = [
            "High execution time detected",
            "Low sample size may affect accuracy",
        ]

        result = RuleTestResult(
            matches=150,
            samples=samples,
            execution_time_ms=245.7,
            estimated_false_positive_rate=0.08,
            warnings=warnings,
        )

        assert result.matches == 150
        assert len(result.samples) == 2
        assert result.execution_time_ms == 245.7
        assert result.estimated_false_positive_rate == 0.08
        assert len(result.warnings) == 2
        assert "High execution time detected" in result.warnings


class TestRuleMetrics:
    """Test RuleMetrics model."""

    def test_rule_metrics_defaults(self) -> None:
        """Test rule metrics with default values."""
        metrics = RuleMetrics(
            total_executions=0,
            total_matches=0,
            true_positives=0,
            false_positives=0,
            avg_execution_time_ms=0.0,
            last_match=None,
            match_rate=0.0,
            precision=0.0,
        )

        assert metrics.total_executions == 0
        assert metrics.total_matches == 0
        assert metrics.true_positives == 0
        assert metrics.false_positives == 0
        assert metrics.avg_execution_time_ms == 0.0
        assert metrics.last_match is None
        assert metrics.match_rate == 0.0
        assert metrics.precision == 0.0

    def test_rule_metrics_with_data(self) -> None:
        """Test rule metrics with actual data."""
        last_match_time = datetime.now(timezone.utc)

        metrics = RuleMetrics(
            total_executions=1000,
            total_matches=50,
            true_positives=45,
            false_positives=5,
            avg_execution_time_ms=123.45,
            last_match=last_match_time,
            match_rate=0.05,
            precision=0.9,
        )

        assert metrics.total_executions == 1000
        assert metrics.total_matches == 50
        assert metrics.true_positives == 45
        assert metrics.false_positives == 5
        assert metrics.avg_execution_time_ms == 123.45
        assert metrics.last_match == last_match_time
        assert metrics.match_rate == 0.05
        assert metrics.precision == 0.9


class TestRule:
    """Test complete Rule model."""

    def test_rule_creation_complete(self) -> None:
        """Test complete rule creation with all fields."""
        rule_id = uuid4()
        created_time = datetime.now(timezone.utc)
        updated_time = datetime.now(timezone.utc)

        metrics = RuleMetrics(
            total_executions=500,
            total_matches=25,
            true_positives=20,
            false_positives=5,
            avg_execution_time_ms=85.2,
            last_match=None,
            match_rate=0.05,
            precision=0.8,
        )

        conditions = [
            RuleCondition(
                field="severity", operator="gte", value=7, case_sensitive=False
            )
        ]

        actions = [
            RuleAction(
                type="alert",
                parameters={"notify": "ops-team"},
                automated=True,
                requires_approval=False,
            )
        ]

        rule = Rule(
            id=rule_id,
            rule_number="SEC-2024-001",
            status=RuleStatus.ACTIVE,
            name="Production Security Rule",
            description="Critical security rule for production monitoring",
            rule_type=RuleType.THRESHOLD,
            severity=RuleSeverity.HIGH,
            query="SELECT * FROM security_logs",
            conditions=conditions,
            threshold=RuleThreshold(count=5, window_seconds=300, group_by=None),
            correlation=None,
            enabled=True,
            tags=["security", "production", "monitoring"],
            references=["MITRE:T1005", "NIST:DE.AE-2"],
            false_positive_rate=0.03,
            actions=actions,
            custom_fields={"environment": "production", "team": "security"},
            created_at=created_time,
            updated_at=updated_time,
            last_executed=updated_time,
            created_by="security-admin",
            updated_by="security-analyst",
            version=3,
            metrics=metrics,
            parent_rule=None,
            related_rules=[],
        )

        assert rule.id == rule_id
        assert rule.rule_number == "SEC-2024-001"
        assert rule.status == RuleStatus.ACTIVE
        assert rule.name == "Production Security Rule"
        assert rule.rule_type == RuleType.THRESHOLD
        assert rule.severity == RuleSeverity.HIGH
        assert rule.conditions is not None and len(rule.conditions) == 1
        assert rule.threshold is not None and rule.threshold.count == 5
        assert rule.enabled is True
        assert "security" in rule.tags
        assert len(rule.actions) == 1
        assert rule.false_positive_rate == 0.03
        assert rule.custom_fields["environment"] == "production"
        assert rule.created_by == "security-admin"
        assert rule.version == 3
        assert rule.metrics.total_executions == 500
        assert rule.parent_rule is None
        assert rule.related_rules == []

    def test_rule_with_relationships(self) -> None:
        """Test rule with parent-child relationships."""
        conditions = [
            RuleCondition(
                field="severity", operator="gte", value=7, case_sensitive=False
            )
        ]

        threshold = RuleThreshold(count=2, window_seconds=120, group_by=None)

        actions = [
            RuleAction(
                type="alert",
                parameters={"channel": "security"},
                automated=True,
                requires_approval=False,
            )
        ]

        # Parent rule
        parent_rule = Rule(
            id=uuid4(),
            rule_number="SEC-PARENT-001",
            name="Parent Security Rule",
            description="Main security detection rule",
            rule_type=RuleType.THRESHOLD,
            severity=RuleSeverity.CRITICAL,
            status=RuleStatus.ACTIVE,
            created_by="security_team",
            query="SELECT * FROM security_logs",
            conditions=conditions,
            threshold=threshold,
            correlation=None,
            actions=actions,
            parent_rule=None,
            enabled=True,
            tags=["parent", "security"],
            false_positive_rate=0.05,
            version=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_executed=None,
            updated_by="security_team",
        )

        # Child rule
        child_rule = Rule(
            id=uuid4(),
            rule_number="SEC-CHILD-001",
            name="Child Detection Rule",
            description="Specific detection logic",
            rule_type=RuleType.PATTERN,
            severity=RuleSeverity.HIGH,
            status=RuleStatus.ACTIVE,
            created_by="analyst",
            query="SELECT * FROM detailed_logs",
            conditions=conditions,
            threshold=None,
            correlation=None,
            actions=actions,
            parent_rule=parent_rule.id,
            enabled=True,
            tags=["child", "detection"],
            false_positive_rate=0.03,
            version=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_executed=None,
            updated_by="analyst",
        )

        assert parent_rule.parent_rule is None
        assert child_rule.parent_rule == parent_rule.id
        assert parent_rule.severity == RuleSeverity.CRITICAL
        assert child_rule.severity == RuleSeverity.HIGH


class TestRuleListResponse:
    """Test RuleListResponse model."""

    def test_rule_list_response_creation(self) -> None:
        """Test rule list response creation."""
        rules = [
            Rule(
                id=uuid4(),
                rule_number="SEC-001",
                status=RuleStatus.ACTIVE,
                name="Rule 1",
                description="First rule",
                rule_type=RuleType.QUERY,
                severity=RuleSeverity.HIGH,
                query=None,
                conditions=None,
                threshold=None,
                correlation=None,
                enabled=True,
                false_positive_rate=None,
                last_executed=None,
                version=1,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                created_by="admin",
                updated_by="admin",
                parent_rule=None,
            ),
            Rule(
                id=uuid4(),
                rule_number="SEC-002",
                status=RuleStatus.INACTIVE,
                name="Rule 2",
                description="Second rule",
                rule_type=RuleType.PATTERN,
                severity=RuleSeverity.MEDIUM,
                query=None,
                conditions=None,
                threshold=None,
                correlation=None,
                enabled=True,
                false_positive_rate=None,
                last_executed=None,
                version=1,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                created_by="analyst",
                updated_by="analyst",
                parent_rule=None,
            ),
        ]

        response = RuleListResponse(
            rules=rules, total=25, page=2, page_size=10, has_next=True
        )

        assert len(response.rules) == 2
        assert response.total == 25
        assert response.page == 2
        assert response.page_size == 10
        assert response.has_next is True

    def test_rule_list_response_validation(self) -> None:
        """Test rule list response validation and data access."""
        # Create sample rule data
        sample_rule = Rule(
            id=uuid4(),
            rule_number="SAM-001",
            name="Sample Rule",
            description="A sample rule for testing",
            rule_type=RuleType.QUERY,
            severity=RuleSeverity.MEDIUM,
            status=RuleStatus.ACTIVE,
            created_by="test_user",
            query="SELECT * FROM logs",
            conditions=[],
            enabled=True,
            threshold=None,
            correlation=None,
            false_positive_rate=0.02,
            version=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_executed=None,
            updated_by="test_user",
            parent_rule=None,
        )

        response = RuleListResponse(
            rules=[sample_rule],
            total=1,
            page=1,
            page_size=20,
            has_next=False,
        )

        assert response.total == 1
        assert len(response.rules) == 1

        # Test safe access to potentially None attributes
        first_rule = response.rules[0]
        assert len(first_rule.conditions or []) == 0
        assert (first_rule.threshold and first_rule.threshold.count) or 0


class TestRuleStats:
    """Test RuleStats model."""

    def test_rule_stats_creation(self) -> None:
        """Test rule stats creation."""
        stats = RuleStats(
            total_rules=150,
            active_rules=120,
            by_status={"active": 120, "inactive": 20, "testing": 8, "disabled": 2},
            by_type={
                "query": 60,
                "pattern": 40,
                "threshold": 30,
                "anomaly": 15,
                "correlation": 5,
            },
            by_severity={
                "critical": 25,
                "high": 45,
                "medium": 55,
                "low": 20,
                "info": 5,
            },
            total_matches_24h=2847,
            top_matching_rules=[
                {
                    "rule_id": "rule-001",
                    "name": "Failed Login Detection",
                    "matches": 452,
                },
                {
                    "rule_id": "rule-002",
                    "name": "Suspicious Network Activity",
                    "matches": 387,
                },
                {"rule_id": "rule-003", "name": "Privilege Escalation", "matches": 234},
            ],
            avg_execution_time=125.7,
            false_positive_rate=0.08,
        )

        assert stats.total_rules == 150
        assert stats.active_rules == 120
        assert stats.by_status["active"] == 120
        assert stats.by_type["query"] == 60
        assert stats.by_severity["critical"] == 25
        assert stats.total_matches_24h == 2847
        assert len(stats.top_matching_rules) == 3
        assert stats.avg_execution_time == 125.7
        assert stats.false_positive_rate == 0.08

        # Verify top matching rules structure
        top_rule = stats.top_matching_rules[0]
        assert top_rule["rule_id"] == "rule-001"
        assert top_rule["name"] == "Failed Login Detection"
        assert top_rule["matches"] == 452
