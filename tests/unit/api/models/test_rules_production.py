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
    RuleCondition,
    RuleCreate,
    RuleMetrics,
    RuleSeverity,
    RuleStatus,
    RuleThreshold,
    RuleType,
    RuleUpdate,
    RuleCorrelation,
)


class TestRuleModelsProduction:
    """Production tests for rule models - NO MOCKING."""

    def test_rule_enums_real_values(self) -> None:
        """Test all enum values are correctly defined."""
        # RuleStatus
        assert RuleStatus.ACTIVE.value == "active"
        assert RuleStatus.INACTIVE.value == "inactive"
        assert RuleStatus.TESTING.value == "testing"
        assert RuleStatus.DISABLED.value == "disabled"
        assert RuleStatus.DEPRECATED.value == "deprecated"

        # RuleType
        assert RuleType.QUERY.value == "query"
        assert RuleType.PATTERN.value == "pattern"
        assert RuleType.THRESHOLD.value == "threshold"
        assert RuleType.ANOMALY.value == "anomaly"
        assert RuleType.CORRELATION.value == "correlation"
        assert RuleType.CUSTOM.value == "custom"

        # RuleSeverity
        assert RuleSeverity.CRITICAL.value == "critical"
        assert RuleSeverity.HIGH.value == "high"
        assert RuleSeverity.MEDIUM.value == "medium"
        assert RuleSeverity.LOW.value == "low"
        assert RuleSeverity.INFO.value == "info"

    def test_rule_condition_real_validation(self) -> None:
        """Test real RuleCondition validation and creation."""
        # Valid condition
        condition = RuleCondition(
            field="user.name", operator="eq", value="admin", case_sensitive=True
        )

        assert condition.field == "user.name"
        assert condition.operator == "eq"
        assert condition.value == "admin"
        assert condition.case_sensitive is True

        # Test all valid operators
        valid_ops = [
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
        for op in valid_ops:
            condition = RuleCondition(
                field="test", operator=op, value="test", case_sensitive=False
            )
            assert condition.operator == op

        # Invalid operator should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            RuleCondition(
                field="test", operator="invalid", value="test", case_sensitive=False
            )

        assert "Invalid operator" in str(exc_info.value)

    def test_rule_threshold_real_validation(self) -> None:
        """Test real RuleThreshold validation."""
        # Valid threshold
        threshold = RuleThreshold(
            count=5, window_seconds=300, group_by=["user_id", "ip_address"]
        )

        assert threshold.count == 5
        assert threshold.window_seconds == 300
        assert threshold.group_by == ["user_id", "ip_address"]

        # Count must be >= 1
        with pytest.raises(ValidationError):
            RuleThreshold(count=0, window_seconds=300, group_by=None)

        # Window must be >= 1
        with pytest.raises(ValidationError):
            RuleThreshold(count=5, window_seconds=0, group_by=None)

    def test_rule_action_real_creation(self) -> None:
        """Test real RuleAction creation with all scenarios."""
        # Basic action
        action = RuleAction(
            type="alert", parameters={}, automated=False, requires_approval=True
        )
        assert action.type == "alert"
        assert action.parameters == {}
        assert action.automated is False
        assert action.requires_approval is True

        # Complex action
        action = RuleAction(
            type="block",
            parameters={"ip": "192.168.1.100", "duration": 3600},
            automated=True,
            requires_approval=False,
        )

        assert action.type == "block"
        assert action.parameters["ip"] == "192.168.1.100"
        assert action.parameters["duration"] == 3600
        assert action.automated is True
        assert action.requires_approval is False

    def test_rule_create_real_type_validation(self) -> None:
        """Test real RuleCreate type-specific validation."""
        # Query rule without query should fail
        with pytest.raises(ValidationError) as exc_info:
            RuleCreate(
                name="Query Rule",
                description="Test query rule",
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

        # Query rule with query should succeed
        rule = RuleCreate(
            name="Valid Query Rule",
            description="Test query rule",
            rule_type=RuleType.QUERY,
            severity=RuleSeverity.HIGH,
            query="SELECT * FROM logs WHERE severity = 'high'",
            conditions=None,
            threshold=None,
            correlation=None,
            enabled=True,
            false_positive_rate=None,
        )

        assert rule.query == "SELECT * FROM logs WHERE severity = 'high'"

        # Pattern rule without conditions should fail
        with pytest.raises(ValidationError) as exc_info:
            RuleCreate(
                name="Pattern Rule",
                description="Test pattern rule",
                rule_type=RuleType.PATTERN,
                severity=RuleSeverity.MEDIUM,
                query=None,
                conditions=None,
                threshold=None,
                correlation=None,
                enabled=True,
                false_positive_rate=None,
            )

        assert "Conditions are required for pattern rules" in str(exc_info.value)

        # Pattern rule with conditions should succeed
        rule = RuleCreate(
            name="Valid Pattern Rule",
            description="Test pattern rule",
            rule_type=RuleType.PATTERN,
            severity=RuleSeverity.MEDIUM,
            query=None,
            conditions=[
                RuleCondition(
                    field="event_type",
                    operator="eq",
                    value="login_failure",
                    case_sensitive=False,
                )
            ],
            threshold=None,
            correlation=None,
            enabled=True,
            false_positive_rate=None,
        )

        assert rule.conditions is not None and len(rule.conditions) == 1

    def test_rule_create_real_tag_normalization(self) -> None:
        """Test real tag normalization in RuleCreate."""
        rule = RuleCreate(
            name="Tag Test",
            description="Testing tag normalization",
            rule_type=RuleType.CUSTOM,
            severity=RuleSeverity.LOW,
            query=None,
            conditions=None,
            threshold=None,
            correlation=None,
            enabled=True,
            false_positive_rate=None,
            tags=[
                "Security",
                "AUTHENTICATION",
                "security",
                "  Authentication  ",
                "",
                "   ",
            ],
        )

        # Tags should be normalized: lowercase, deduplicated, trimmed, empty removed
        expected_tags = {"security", "authentication"}
        assert set(rule.tags) == expected_tags

    def test_rule_update_real_partial_updates(self) -> None:
        """Test real partial updates with RuleUpdate."""
        # Test partial update
        update = RuleUpdate(
            name="Updated Name",
            description=None,
            false_positive_rate=None,
            severity=RuleSeverity.CRITICAL,
        )

        assert update.name == "Updated Name"
        assert update.severity == RuleSeverity.CRITICAL
        assert update.description is None  # Not provided

        # Test false positive rate validation
        update = RuleUpdate(name=None, description=None, false_positive_rate=0.25)
        assert update.false_positive_rate == 0.25

        # Invalid false positive rate
        with pytest.raises(ValidationError):
            RuleUpdate(name=None, description=None, false_positive_rate=1.5)  # > 1.0

        with pytest.raises(ValidationError):
            RuleUpdate(name=None, description=None, false_positive_rate=-0.1)  # < 0.0

    def test_rule_metrics_real_defaults_and_values(self) -> None:
        """Test real RuleMetrics with defaults and custom values."""
        # Default metrics
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

        # Custom metrics
        now = datetime.now(timezone.utc)
        metrics = RuleMetrics(
            total_executions=1000,
            total_matches=50,
            true_positives=45,
            false_positives=5,
            avg_execution_time_ms=125.7,
            last_match=now,
            match_rate=0.05,
            precision=0.9,
        )

        assert metrics.total_executions == 1000
        assert metrics.total_matches == 50
        assert metrics.true_positives == 45
        assert metrics.false_positives == 5
        assert metrics.avg_execution_time_ms == 125.7
        assert metrics.last_match == now
        assert metrics.match_rate == 0.05
        assert metrics.precision == 0.9

    def test_complete_rule_real_creation(self) -> None:
        """Test complete Rule creation with real production data."""
        rule_id = uuid4()
        created_time = datetime.now(timezone.utc)

        # Create realistic conditions
        conditions = [
            RuleCondition(
                field="event_type",
                operator="eq",
                value="failed_login",
                case_sensitive=False,
            ),
            RuleCondition(
                field="attempts", operator="gte", value=5, case_sensitive=False
            ),
        ]

        # Create threshold
        threshold = RuleThreshold(count=5, window_seconds=300, group_by=None)

        # Create actions
        actions = [
            RuleAction(
                type="alert",
                parameters={"severity": "high", "notify": "security-team"},
                automated=False,
                requires_approval=True,
            ),
            RuleAction(
                type="block",
                parameters={"duration": 1800},
                automated=True,
                requires_approval=False,
            ),
        ]

        # Create metrics
        metrics = RuleMetrics(
            total_executions=500,
            total_matches=25,
            true_positives=23,
            false_positives=2,
            avg_execution_time_ms=87.3,
            last_match=created_time,
            match_rate=0.05,
            precision=0.92,
        )

        # Create complete rule
        rule = Rule(
            id=rule_id,
            rule_number="SEC-2024-001",
            status=RuleStatus.ACTIVE,
            name="Failed Login Detection",
            description="Detects multiple failed login attempts within a time window",
            rule_type=RuleType.THRESHOLD,
            severity=RuleSeverity.HIGH,
            query=None,
            conditions=conditions,
            threshold=threshold,
            correlation=None,
            enabled=True,
            tags=["authentication", "brute-force", "security"],
            references=["MITRE:T1110.001", "OWASP:A07:2021"],
            false_positive_rate=0.04,
            actions=actions,
            custom_fields={"team": "security", "environment": "production"},
            created_at=created_time,
            updated_at=created_time,
            last_executed=created_time,
            created_by="security-admin",
            updated_by="security-admin",
            version=1,
            metrics=metrics,
            parent_rule=None,
            related_rules=[],
        )

        # Verify all fields
        assert rule.id == rule_id
        assert rule.rule_number == "SEC-2024-001"
        assert rule.status == RuleStatus.ACTIVE
        assert rule.name == "Failed Login Detection"
        assert rule.rule_type == RuleType.THRESHOLD
        assert rule.severity == RuleSeverity.HIGH
        assert rule.query is None
        assert rule.conditions is not None and len(rule.conditions) == 2
        assert rule.threshold is not None and rule.threshold.count == 5
        assert rule.correlation is None
        assert rule.enabled is True
        assert "authentication" in rule.tags
        assert "MITRE:T1110.001" in rule.references
        assert rule.false_positive_rate == 0.04
        assert len(rule.actions) == 2
        assert rule.custom_fields["team"] == "security"
        assert rule.created_by == "security-admin"
        assert rule.version == 1
        assert rule.metrics.total_executions == 500

    def test_rule_with_relationships_real_scenario(self) -> None:
        """Test rule creation with realistic relationships and complex data."""
        # Create complex conditions for APT detection
        conditions = [
            RuleCondition(
                field="process.name",
                operator="in",
                value=["powershell.exe", "cmd.exe", "wscript.exe"],
                case_sensitive=False,
            ),
            RuleCondition(
                field="network.bytes_out",
                operator="gt",
                value=10485760,  # 10MB
                case_sensitive=False,
            ),
            RuleCondition(
                field="user.type", operator="eq", value="admin", case_sensitive=False
            ),
        ]

        # Create threshold for multiple events
        threshold = RuleThreshold(
            count=3,
            window_seconds=1800,  # 30 minutes
            group_by=["user.name", "host.ip"],
        )

        # Create comprehensive actions
        actions = [
            RuleAction(
                type="alert",
                parameters={
                    "severity": "critical",
                    "escalate": True,
                    "notify": ["soc-team", "incident-response"],
                },
                automated=True,
                requires_approval=False,
            ),
            RuleAction(
                type="isolate",
                parameters={"isolation_type": "network", "duration": 3600},
                automated=False,
                requires_approval=True,
            ),
            RuleAction(
                type="custom",
                parameters={
                    "script": "collect_forensics.py",
                    "args": ["--host", "{host.ip}", "--user", "{user.name}"],
                },
                automated=False,
                requires_approval=True,
            ),
        ]

        # Create correlation for complex event patterns
        correlation = RuleCorrelation(
            events=[
                {"type": "process_execution", "priority": 1},
                {"type": "network_connection", "priority": 2},
                {"type": "file_access", "priority": 3},
            ],
            window_seconds=600,  # 10 minutes
            join_fields=["user_id", "host_id"],
            sequence_required=True,
        )

        # Create complete rule
        rule_id = uuid4()
        created_time = datetime.now(timezone.utc)

        rule = Rule(
            id=rule_id,
            rule_number="APT-2024-001",
            status=RuleStatus.ACTIVE,
            name="Advanced Persistent Threat Detection",
            description="Detects sophisticated multi-stage attacks with correlation",
            rule_type=RuleType.CORRELATION,
            severity=RuleSeverity.CRITICAL,
            query=None,
            conditions=conditions,
            threshold=threshold,
            correlation=correlation,
            enabled=True,
            tags=["apt", "correlation", "multi-stage", "critical"],
            references=[
                "MITRE:T1110.001",
                "MITRE:T1059.001",
                "MITRE:T1041",
                "NIST:DE.AE-2",
                "NIST:DE.CM-1",
            ],
            false_positive_rate=0.02,
            actions=actions,
            custom_fields={
                "threat_intel_sources": ["internal", "commercial", "osint"],
                "automation_level": "semi-automated",
                "business_impact": "high",
                "compliance_frameworks": ["SOX", "PCI-DSS", "ISO27001"],
            },
            created_at=created_time,
            updated_at=created_time,
            last_executed=created_time,
            created_by="threat-intel-team",
            updated_by="threat-intel-team",
            version=1,
            parent_rule=None,
            related_rules=[],
        )

        # Comprehensive validation
        assert rule.id == rule_id
        assert rule.rule_number == "APT-2024-001"
        assert rule.name == "Advanced Persistent Threat Detection"
        assert rule.rule_type == RuleType.CORRELATION
        assert rule.severity == RuleSeverity.CRITICAL
        assert rule.conditions is not None and len(rule.conditions) == 3
        assert rule.correlation is not None
        assert rule.correlation.sequence_required is True
        assert len(rule.correlation.events) == 3
        assert rule.correlation.window_seconds == 600
        assert "user_id" in rule.correlation.join_fields
        assert rule.enabled is True
        assert "apt" in rule.tags
        assert len(rule.references) == 5
        assert "MITRE:T1110.001" in rule.references
        assert rule.false_positive_rate == 0.02
        assert len(rule.actions) == 3

        # Test action types
        action_types = [action.type for action in rule.actions]
        assert "alert" in action_types
        assert "isolate" in action_types
        assert "custom" in action_types

        # Test custom fields
        assert rule.custom_fields["threat_intel_sources"] == [
            "internal",
            "commercial",
            "osint",
        ]
        assert rule.custom_fields["automation_level"] == "semi-automated"
        assert rule.custom_fields["business_impact"] == "high"

    def test_rule_field_validation_edge_cases(self) -> None:
        """Test edge cases for rule field validation."""
        # Test empty name should fail
        with pytest.raises(ValidationError):
            RuleCreate(
                name="",  # Empty name
                description="Valid description",
                rule_type=RuleType.CUSTOM,
                severity=RuleSeverity.LOW,
                query=None,
                conditions=None,
                threshold=None,
                correlation=None,
                enabled=True,
                false_positive_rate=None,
            )

        # Test empty description should fail
        with pytest.raises(ValidationError):
            RuleCreate(
                name="Valid Name",
                description="",  # Empty description
                rule_type=RuleType.CUSTOM,
                severity=RuleSeverity.LOW,
                query=None,
                conditions=None,
                threshold=None,
                correlation=None,
                enabled=True,
                false_positive_rate=None,
            )

        # Test invalid false positive rate > 1.0
        with pytest.raises(ValidationError):
            RuleCreate(
                name="Valid Name",
                description="Valid description",
                rule_type=RuleType.CUSTOM,
                severity=RuleSeverity.LOW,
                query=None,
                conditions=None,
                threshold=None,
                correlation=None,
                enabled=True,
                false_positive_rate=1.5,  # > 1.0
            )

        # Test invalid false positive rate < 0.0
        with pytest.raises(ValidationError):
            RuleCreate(
                name="Valid Name",
                description="Valid description",
                rule_type=RuleType.CUSTOM,
                severity=RuleSeverity.LOW,
                query=None,
                conditions=None,
                threshold=None,
                correlation=None,
                enabled=True,
                false_positive_rate=-0.1,  # < 0.0
            )

    def test_complex_rule_scenario_real_production(self) -> None:
        """Test complex production scenario with all rule components."""
        # Build comprehensive rule step by step
        conditions = [
            RuleCondition(
                field="source_ip",
                operator="in",
                value=["192.168.1.0/24", "10.0.0.0/8"],
                case_sensitive=False,
            ),
            RuleCondition(
                field="user_agent",
                operator="regex",
                value=r".*(?:bot|crawler|spider).*",
                case_sensitive=False,
            ),
            RuleCondition(
                field="request_count", operator="gte", value=100, case_sensitive=False
            ),
            RuleCondition(
                field="response_code",
                operator="in",
                value=[200, 404, 500],
                case_sensitive=False,
            ),
            RuleCondition(
                field="payload_size",
                operator="gt",
                value=1048576,  # 1MB
                case_sensitive=False,
            ),
        ]

        threshold = RuleThreshold(
            count=10, window_seconds=300, group_by=["source_ip", "user_id"]  # 5 minutes
        )

        correlation = RuleCorrelation(
            events=[
                {"type": "http_request", "field": "request_id", "required": True},
                {"type": "auth_attempt", "field": "session_id", "required": False},
                {"type": "data_access", "field": "resource_id", "required": True},
            ],
            window_seconds=900,  # 15 minutes
            join_fields=["user_id", "session_id"],
            sequence_required=False,
        )

        actions = [
            RuleAction(
                type="alert",
                parameters={
                    "severity": "high",
                    "channels": ["email", "slack", "pagerduty"],
                    "escalation_time": 300,
                },
                automated=True,
                requires_approval=False,
            ),
            RuleAction(
                type="rate_limit",
                parameters={"requests_per_minute": 10, "duration": 1800},
                automated=True,
                requires_approval=False,
            ),
            RuleAction(
                type="investigate",
                parameters={
                    "collect_logs": True,
                    "timeline_hours": 24,
                    "evidence_retention_days": 90,
                },
                automated=False,
                requires_approval=True,
            ),
        ]

        # Create the comprehensive rule
        rule = RuleCreate(
            name="Comprehensive Threat Detection",
            description="Multi-layered detection for sophisticated attacks",
            rule_type=RuleType.CORRELATION,
            severity=RuleSeverity.HIGH,
            query="SELECT * FROM security_events WHERE timestamp > NOW() - INTERVAL 1 HOUR",
            conditions=conditions,
            threshold=threshold,
            correlation=correlation,
            enabled=True,
            tags=["comprehensive", "multi-layer", "correlation", "production"],
            references=[
                "MITRE:T1071.001",
                "MITRE:T1033",
                "MITRE:T1041",
                "OWASP:A05:2021",
                "NIST:DE.AE-3",
            ],
            false_positive_rate=0.03,
            actions=actions,
            custom_fields={
                "developed_by": "security-research-team",
                "testing_environment": ["staging", "pre-prod"],
                "performance_impact": "medium",
                "data_sources": ["web_logs", "auth_logs", "database_logs"],
                "compliance_requirements": ["SOX", "GDPR", "HIPAA"],
            },
        )

        # Validate the complex rule
        assert rule.name == "Comprehensive Threat Detection"
        assert rule.rule_type == RuleType.CORRELATION
        assert rule.severity == RuleSeverity.HIGH
        assert rule.query is not None
        assert rule.conditions is not None and len(rule.conditions) == 5
        assert rule.threshold is not None
        assert rule.correlation is not None
        assert rule.correlation.sequence_required is False
        assert len(rule.correlation.events) == 3
        assert rule.correlation.window_seconds == 900
        assert "user_id" in rule.correlation.join_fields
        assert rule.enabled is True
        assert "comprehensive" in rule.tags
        assert len(rule.references) == 5
        assert "MITRE:T1071.001" in rule.references
        assert rule.false_positive_rate == 0.03
        assert len(rule.actions) == 3

        # Validate actions
        action_types = [action.type for action in rule.actions]
        assert "alert" in action_types
        assert "rate_limit" in action_types
        assert "investigate" in action_types

        # Validate custom fields
        assert rule.custom_fields["developed_by"] == "security-research-team"
        assert "staging" in rule.custom_fields["testing_environment"]
        assert rule.custom_fields["performance_impact"] == "medium"
        assert "web_logs" in rule.custom_fields["data_sources"]
        assert "GDPR" in rule.custom_fields["compliance_requirements"]

    def test_rule_threshold_creation_production(self) -> None:
        """Test RuleThreshold creation with all required fields."""
        threshold = RuleThreshold(
            count=5, window_seconds=300, group_by=["source_ip", "user_id"]
        )

        assert threshold.count == 5
        assert threshold.window_seconds == 300
        assert threshold.group_by == ["source_ip", "user_id"]

    def test_rule_threshold_minimal_creation_production(self) -> None:
        """Test RuleThreshold creation with minimal required fields."""
        threshold = RuleThreshold(count=10, window_seconds=600, group_by=None)

        assert threshold.count == 10
        assert threshold.window_seconds == 600
        assert threshold.group_by is None

    def test_rule_action_creation_production(self) -> None:
        """Test RuleAction creation with all required fields."""
        action = RuleAction(
            type="alert",
            parameters={"severity": "high"},
            automated=True,
            requires_approval=False,
        )

        assert action.type == "alert"
        assert action.parameters == {"severity": "high"}
        assert action.automated is True
        assert action.requires_approval is False

    def test_rule_create_validation_production(self) -> None:
        """Test RuleCreate validation with all required fields."""
        conditions = [
            RuleCondition(
                field="source_ip",
                operator="eq",
                value="192.168.1.1",
                case_sensitive=False,
            )
        ]

        threshold = RuleThreshold(count=5, window_seconds=300, group_by=["source_ip"])

        correlation = RuleCorrelation(
            events=[{"type": "login"}, {"type": "access"}],
            window_seconds=600,
            join_fields=["user_id"],
            sequence_required=True,
        )

        rule = RuleCreate(
            name="Test Rule",
            description="Test rule description",
            rule_type=RuleType.PATTERN,
            severity=RuleSeverity.HIGH,
            query="SELECT * FROM events",
            conditions=conditions,
            threshold=threshold,
            correlation=correlation,
            enabled=True,
            false_positive_rate=0.1,
        )

        assert rule.name == "Test Rule"
        assert rule.rule_type == RuleType.PATTERN
        assert rule.conditions is not None and len(rule.conditions) == 1

    def test_rule_condition_case_sensitivity(self) -> None:
        """Test RuleCondition with case sensitivity."""
        condition = RuleCondition(
            field="hostname", operator="contains", value="malware", case_sensitive=True
        )

        assert condition.case_sensitive is True
        if condition.case_sensitive and isinstance(condition.value, str):
            assert condition.value == "malware"

    def test_rule_update_validation_production(self) -> None:
        """Test RuleUpdate validation with partial fields."""
        update = RuleUpdate(
            name="Updated Rule",
            description="Updated description",
            false_positive_rate=0.05,
        )

        assert update.name == "Updated Rule"
        assert update.description == "Updated description"
        assert update.false_positive_rate == 0.05

    def test_rule_metrics_creation_production(self) -> None:
        """Test RuleMetrics creation with all required fields."""
        from datetime import datetime, timezone

        metrics = RuleMetrics(
            total_executions=100,
            total_matches=25,
            true_positives=20,
            false_positives=5,
            avg_execution_time_ms=150.5,
            last_match=datetime.now(timezone.utc),
            match_rate=0.25,
            precision=0.8,
        )

        assert metrics.total_executions == 100
        assert metrics.total_matches == 25
        assert metrics.true_positives == 20
        assert metrics.false_positives == 5
        assert metrics.avg_execution_time_ms == 150.5
        assert metrics.match_rate == 0.25
        assert metrics.precision == 0.8

    def test_rule_complete_creation_production(self) -> None:
        """Test complete Rule creation with all required fields."""
        from datetime import datetime, timezone
        from uuid import uuid4

        conditions = [
            RuleCondition(
                field="event_type",
                operator="eq",
                value="suspicious_login",
                case_sensitive=False,
            ),
            RuleCondition(
                field="failed_attempts", operator="gte", value=5, case_sensitive=False
            ),
        ]

        threshold = RuleThreshold(count=3, window_seconds=600, group_by=["source_ip"])

        actions = [
            RuleAction(
                type="alert",
                parameters={"channel": "email"},
                automated=True,
                requires_approval=False,
            )
        ]

        rule = Rule(
            id=uuid4(),
            rule_number="R001",
            name="Suspicious Login Detection",
            description="Detects suspicious login attempts",
            rule_type=RuleType.PATTERN,
            severity=RuleSeverity.HIGH,
            status=RuleStatus.ACTIVE,
            query="SELECT * FROM login_events WHERE failed_attempts >= 5",
            conditions=conditions,
            threshold=threshold,
            correlation=None,
            enabled=True,
            false_positive_rate=0.05,
            actions=actions,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_executed=datetime.now(timezone.utc),
            created_by="admin",
            updated_by="admin",
            version=1,
            parent_rule=None,
        )

        assert rule.name == "Suspicious Login Detection"
        assert rule.conditions is not None and len(rule.conditions) == 2
        if rule.threshold is not None:
            assert rule.threshold.count == 3

    def test_rule_validation_with_complex_conditions(self) -> None:
        """Test rule validation with complex conditions."""
        conditions = [
            RuleCondition(
                field="source_ip",
                operator="in",
                value=["192.168.1.1", "10.0.0.1"],
                case_sensitive=False,
            ),
            RuleCondition(
                field="user_agent",
                operator="regex",
                value=r".*bot.*",
                case_sensitive=False,
            ),
            RuleCondition(
                field="request_count", operator="gt", value=100, case_sensitive=False
            ),
        ]

        actions = [
            RuleAction(
                type="block",
                parameters={"duration": 3600},
                automated=False,
                requires_approval=True,
            )
        ]

        rule = RuleCreate(
            name="Complex Rule",
            description="Complex rule with multiple conditions",
            rule_type=RuleType.PATTERN,
            severity=RuleSeverity.CRITICAL,
            query=None,
            conditions=conditions,
            threshold=None,
            correlation=None,
            enabled=True,
            false_positive_rate=0.02,
            actions=actions,
        )

        assert rule.conditions is not None and len(rule.conditions) == 3
        if rule.conditions is not None:
            assert len(rule.conditions) == 3

    def test_rule_correlation_complex_validation(self) -> None:
        """Test complex rule correlation validation."""
        correlation = RuleCorrelation(
            events=[
                {"type": "login_attempt", "result": "failed"},
                {"type": "privilege_escalation", "method": "sudo"},
                {"type": "file_access", "path": "/etc/passwd"},
            ],
            window_seconds=1800,
            join_fields=["user_id", "session_id"],
            sequence_required=True,
        )

        conditions = [
            RuleCondition(
                field="severity", operator="gte", value="medium", case_sensitive=False
            )
        ]

        rule = RuleCreate(
            name="Correlation Rule",
            description="Multi-event correlation rule",
            rule_type=RuleType.CORRELATION,
            severity=RuleSeverity.HIGH,
            query=None,
            conditions=conditions,
            threshold=None,
            correlation=correlation,
            enabled=True,
            false_positive_rate=0.08,
        )

        assert rule.correlation is not None
        if rule.correlation is not None:
            assert rule.correlation.sequence_required is True
            assert rule.correlation.events is not None
            assert rule.correlation.window_seconds == 1800
            assert rule.correlation.join_fields == ["user_id", "session_id"]
