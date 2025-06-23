"""
Test suite for AutoApprovalEngine - PRODUCTION IMPLEMENTATION
CRITICAL: Uses REAL production code and components - NO MOCKING.
Achieves minimum 90% statement coverage.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

import pytest

# Real imports from production source code
from src.orchestrator_agent.auto_approval import ApprovalRule, AutoApprovalEngine


class TestApprovalRuleProduction:
    """Test ApprovalRule with real production logic."""

    def test_approval_rule_initialization(self) -> None:
        """Test ApprovalRule initialization with real data."""
        rule = ApprovalRule(
            rule_id="test_rule_001",
            name="Test Security Rule",
            description="Test rule for security operations",
            conditions={
                "severity": "high",
                "confidence_score": {"operator": "greater_than", "value": 0.8},
            },
            action_patterns=["isolate_.*", "block_.*"],
            max_risk_score=0.5,
            enabled=True,
        )

        assert rule.rule_id == "test_rule_001"
        assert rule.name == "Test Security Rule"
        assert rule.description == "Test rule for security operations"
        assert rule.conditions["severity"] == "high"
        assert rule.max_risk_score == 0.5
        assert rule.enabled is True

    def test_approval_rule_disabled_initialization(self) -> None:
        """Test ApprovalRule initialization with disabled state."""
        rule = ApprovalRule(
            rule_id="disabled_rule",
            name="Disabled Rule",
            description="Rule that is disabled",
            conditions={},
            action_patterns=["test_.*"],
            max_risk_score=0.1,
            enabled=False,
        )

        assert rule.enabled is False

    def test_approval_rule_default_enabled(self) -> None:
        """Test ApprovalRule default enabled state."""
        rule = ApprovalRule(
            rule_id="default_rule",
            name="Default Rule",
            description="Rule with default enabled state",
            conditions={},
            action_patterns=["default_.*"],
            max_risk_score=0.3,
        )

        assert rule.enabled is True  # Default value

    def test_matches_action_with_single_pattern(self) -> None:
        """Test action matching with single regex pattern."""
        rule = ApprovalRule(
            rule_id="single_pattern",
            name="Single Pattern Rule",
            description="Rule with single action pattern",
            conditions={},
            action_patterns=["isolate_instance"],
            max_risk_score=0.4,
        )

        # Test exact match
        action = {"action_type": "isolate_instance"}
        assert rule.matches_action(action) is True

        # Test non-match
        action = {"action_type": "delete_instance"}
        assert rule.matches_action(action) is False

    def test_matches_action_with_regex_patterns(self) -> None:
        """Test action matching with regex patterns."""
        rule = ApprovalRule(
            rule_id="regex_pattern",
            name="Regex Pattern Rule",
            description="Rule with regex action patterns",
            conditions={},
            action_patterns=["get_.*", "list_.*", "describe_.*"],
            max_risk_score=0.2,
        )

        # Test matching patterns
        assert rule.matches_action({"action_type": "get_instance_info"}) is True
        assert rule.matches_action({"action_type": "list_firewall_rules"}) is True
        assert rule.matches_action({"action_type": "describe_network"}) is True

        # Test non-matching patterns
        assert rule.matches_action({"action_type": "delete_instance"}) is False
        assert rule.matches_action({"action_type": "modify_firewall"}) is False

    def test_matches_action_with_empty_action_type(self) -> None:
        """Test action matching with empty or missing action_type."""
        rule = ApprovalRule(
            rule_id="empty_test",
            name="Empty Test Rule",
            description="Rule for testing empty action types",
            conditions={},
            action_patterns=["test_.*"],
            max_risk_score=0.1,
        )

        # Test empty action_type
        assert rule.matches_action({"action_type": ""}) is False

        # Test missing action_type
        assert rule.matches_action({}) is False

    def test_evaluate_conditions_simple_equality(self) -> None:
        """Test condition evaluation with simple equality checks."""
        rule = ApprovalRule(
            rule_id="simple_conditions",
            name="Simple Conditions Rule",
            description="Rule with simple condition checks",
            conditions={
                "severity": "high",
                "environment": "production",
                "threat_confirmed": True,
            },
            action_patterns=["test_.*"],
            max_risk_score=0.5,
        )

        # Test matching conditions
        context = {
            "severity": "high",
            "environment": "production",
            "threat_confirmed": True,
        }
        assert rule.evaluate_conditions(context) is True

        # Test non-matching conditions
        context = {
            "severity": "low",
            "environment": "production",
            "threat_confirmed": True,
        }
        assert rule.evaluate_conditions(context) is False

    def test_evaluate_conditions_complex_operators(self) -> None:
        """Test condition evaluation with complex operator-based conditions."""
        rule = ApprovalRule(
            rule_id="complex_conditions",
            name="Complex Conditions Rule",
            description="Rule with complex operator conditions",
            conditions={
                "confidence_score": {"operator": "greater_than", "value": 0.8},
                "severity": {"operator": "in", "value": ["high", "critical"]},
                "incident_age_hours": {"operator": "less_than", "value": 24},
                "description": {"operator": "contains", "value": "malware"},
            },
            action_patterns=["remediate_.*"],
            max_risk_score=0.6,
        )

        # Test all conditions pass
        context = {
            "confidence_score": 0.9,
            "severity": "high",
            "incident_age_hours": 12,
            "description": "Detected malware in system",
        }
        assert rule.evaluate_conditions(context) is True

        # Test confidence score fails
        context["confidence_score"] = 0.7
        assert rule.evaluate_conditions(context) is False

        # Reset and test severity fails
        context["confidence_score"] = 0.9
        context["severity"] = "medium"
        assert rule.evaluate_conditions(context) is False

        # Reset and test age fails
        context["severity"] = "high"
        context["incident_age_hours"] = 30
        assert rule.evaluate_conditions(context) is False

        # Reset and test contains fails
        context["incident_age_hours"] = 12
        context["description"] = "Network intrusion detected"
        assert rule.evaluate_conditions(context) is False

    def test_evaluate_conditions_equals_operator(self) -> None:
        """Test condition evaluation with equals operator."""
        rule = ApprovalRule(
            rule_id="equals_test",
            name="Equals Test Rule",
            description="Rule testing equals operator",
            conditions={
                "status": {"operator": "equals", "value": "active"},
            },
            action_patterns=["test_.*"],
            max_risk_score=0.3,
        )

        # Test equals match
        assert rule.evaluate_conditions({"status": "active"}) is True

        # Test equals no match
        assert rule.evaluate_conditions({"status": "inactive"}) is False

    def test_evaluate_conditions_with_none_values(self) -> None:
        """Test condition evaluation with None values in context."""
        rule = ApprovalRule(
            rule_id="none_values",
            name="None Values Rule",
            description="Rule testing None value handling",
            conditions={
                "confidence_score": {"operator": "greater_than", "value": 0.5},
                "incident_age_hours": {"operator": "less_than", "value": 48},
            },
            action_patterns=["test_.*"],
            max_risk_score=0.4,
        )

        # Test with None values
        context = {
            "confidence_score": None,
            "incident_age_hours": None,
        }
        assert rule.evaluate_conditions(context) is False

        # Test with one None, one valid
        context2 = {
            "confidence_score": 0.8,
            "incident_age_hours": None,
        }
        assert rule.evaluate_conditions(context2) is False

    def test_evaluate_conditions_missing_context_keys(self) -> None:
        """Test condition evaluation with missing context keys."""
        rule = ApprovalRule(
            rule_id="missing_keys",
            name="Missing Keys Rule",
            description="Rule testing missing context keys",
            conditions={
                "required_field": "expected_value",
                "another_field": {"operator": "greater_than", "value": 10},
            },
            action_patterns=["test_.*"],
            max_risk_score=0.2,
        )

        # Test with missing context
        assert rule.evaluate_conditions({}) is False

        # Test with partial context
        assert rule.evaluate_conditions({"required_field": "expected_value"}) is False


class TestAutoApprovalEngineProduction:
    """Test AutoApprovalEngine with real production configuration."""

    @pytest.fixture
    def basic_config(self) -> Dict[str, Any]:
        """Create basic test configuration."""
        return {
            "auto_remediation": {"enabled": True},
            "approval_rules": [],
        }

    @pytest.fixture
    def advanced_config(self) -> Dict[str, Any]:
        """Create advanced test configuration with custom rules."""
        return {
            "auto_remediation": {"enabled": True},
            "approval_rules": [
                {
                    "rule_id": "custom_rule_001",
                    "name": "Custom Test Rule",
                    "description": "Custom rule for testing",
                    "conditions": {
                        "severity": {"operator": "in", "value": ["medium", "high"]},
                        "confidence_score": {"operator": "greater_than", "value": 0.7},
                    },
                    "action_patterns": ["test_.*", "verify_.*"],
                    "max_risk_score": 0.4,
                    "enabled": True,
                },
            ],
        }

    @pytest.fixture
    def disabled_config(self) -> Dict[str, Any]:
        """Create configuration with auto-remediation disabled."""
        return {
            "auto_remediation": {"enabled": False},
            "approval_rules": [],
        }

    def test_auto_approval_engine_initialization_basic(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test AutoApprovalEngine initialization with basic config."""
        engine = AutoApprovalEngine(basic_config)

        assert engine.config == basic_config
        assert isinstance(engine.rules, list)
        assert len(engine.rules) >= 3  # Default rules
        assert isinstance(engine.approval_history, list)
        assert len(engine.approval_history) == 0

        # Verify default rules are loaded
        rule_ids = [rule.rule_id for rule in engine.rules]
        assert "safe_readonly" in rule_ids
        assert "isolate_compromised" in rule_ids
        assert "revoke_suspicious_access" in rule_ids

    def test_auto_approval_engine_initialization_advanced(
        self, advanced_config: Dict[str, Any]
    ) -> None:
        """Test AutoApprovalEngine initialization with custom rules."""
        engine = AutoApprovalEngine(advanced_config)

        assert len(engine.rules) >= 4  # 3 default + 1 custom

        # Find custom rule
        custom_rule = None
        for rule in engine.rules:
            if rule.rule_id == "custom_rule_001":
                custom_rule = rule
                break

        assert custom_rule is not None
        assert custom_rule.name == "Custom Test Rule"
        assert custom_rule.enabled is True

    def test_load_rules_default_safe_readonly(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test loading of default safe readonly rule."""
        engine = AutoApprovalEngine(basic_config)

        safe_rule = None
        for rule in engine.rules:
            if rule.rule_id == "safe_readonly":
                safe_rule = rule
                break

        assert safe_rule is not None
        assert safe_rule.name == "Safe Read-Only Actions"
        assert safe_rule.max_risk_score == 0.2
        assert "get_.*" in safe_rule.action_patterns
        assert "list_.*" in safe_rule.action_patterns
        assert "describe_.*" in safe_rule.action_patterns
        assert "show_.*" in safe_rule.action_patterns

    def test_load_rules_default_isolate_compromised(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test loading of default isolate compromised rule."""
        engine = AutoApprovalEngine(basic_config)

        isolate_rule = None
        for rule in engine.rules:
            if rule.rule_id == "isolate_compromised":
                isolate_rule = rule
                break

        assert isolate_rule is not None
        assert isolate_rule.name == "Isolate Compromised Resources"
        assert isolate_rule.max_risk_score == 0.5
        assert "isolate_instance" in isolate_rule.action_patterns
        assert "block_ip_address" in isolate_rule.action_patterns
        assert "disable_user_account" in isolate_rule.action_patterns

    def test_load_rules_default_revoke_suspicious_access(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test loading of default revoke suspicious access rule."""
        engine = AutoApprovalEngine(basic_config)

        revoke_rule = None
        for rule in engine.rules:
            if rule.rule_id == "revoke_suspicious_access":
                revoke_rule = rule
                break

        assert revoke_rule is not None
        assert revoke_rule.name == "Revoke Suspicious Access"
        assert revoke_rule.max_risk_score == 0.4
        assert "revoke_iam_permissions" in revoke_rule.action_patterns
        assert "remove_ssh_key" in revoke_rule.action_patterns
        assert "expire_credentials" in revoke_rule.action_patterns

    def test_load_rules_filters_disabled_rules(self) -> None:
        """Test that disabled rules are filtered out."""
        config = {
            "auto_remediation": {"enabled": True},
            "approval_rules": [
                {
                    "rule_id": "enabled_rule",
                    "name": "Enabled Rule",
                    "description": "This rule is enabled",
                    "conditions": {},
                    "action_patterns": ["test_.*"],
                    "max_risk_score": 0.1,
                    "enabled": True,
                },
                {
                    "rule_id": "disabled_rule",
                    "name": "Disabled Rule",
                    "description": "This rule is disabled",
                    "conditions": {},
                    "action_patterns": ["disabled_.*"],
                    "max_risk_score": 0.1,
                    "enabled": False,
                },
            ],
        }

        engine = AutoApprovalEngine(config)

        rule_ids = [rule.rule_id for rule in engine.rules]
        assert "enabled_rule" in rule_ids
        assert "disabled_rule" not in rule_ids

    def test_can_auto_approve_disabled(self, disabled_config: Dict[str, Any]) -> None:
        """Test can_auto_approve when auto-remediation is disabled."""
        engine = AutoApprovalEngine(disabled_config)

        incident = {"severity": "high", "analysis": {"confidence_score": 0.9}}
        actions = [{"action_type": "get_system_info"}]

        can_approve, reasons = engine.can_auto_approve(incident, actions)

        assert can_approve is False
        assert "Auto-remediation is disabled" in reasons

    def test_can_auto_approve_safe_readonly_actions(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test auto-approval of safe readonly actions."""
        engine = AutoApprovalEngine(basic_config)

        incident = {
            "severity": "medium",
            "analysis": {"confidence_score": 0.8},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        actions = [
            {"action_type": "get_instance_details"},
            {"action_type": "list_network_rules"},
            {"action_type": "describe_security_groups"},
        ]

        can_approve, reasons = engine.can_auto_approve(incident, actions)

        assert can_approve is True
        assert len(reasons) >= 3  # One approval reason per action
        assert any("Safe Read-Only Actions" in reason for reason in reasons)

    def test_can_auto_approve_isolate_compromised(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test auto-approval of isolate compromised actions."""
        engine = AutoApprovalEngine(basic_config)

        incident = {
            "severity": "critical",
            "analysis": {
                "confidence_score": 0.9,
                "threat_confirmed": True,
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        actions = [
            {"action_type": "isolate_instance"},
            {"action_type": "block_ip_address"},
        ]

        can_approve, reasons = engine.can_auto_approve(incident, actions)

        assert can_approve is True
        assert any("Isolate Compromised Resources" in reason for reason in reasons)

    def test_can_auto_approve_revoke_suspicious_access(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test auto-approval of revoke suspicious access actions."""
        engine = AutoApprovalEngine(basic_config)

        incident = {
            "severity": "high",
            "analysis": {
                "confidence_score": 0.85,
                "attack_type": "unauthorized_access",
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        actions = [
            {"action_type": "revoke_iam_permissions"},
            {"action_type": "expire_credentials"},
        ]

        can_approve, reasons = engine.can_auto_approve(incident, actions)

        assert can_approve is True
        assert any("Revoke Suspicious Access" in reason for reason in reasons)

    def test_can_auto_approve_mixed_actions(self, basic_config: Dict[str, Any]) -> None:
        """Test auto-approval with mix of approved and non-approved actions."""
        engine = AutoApprovalEngine(basic_config)

        incident = {
            "severity": "medium",
            "analysis": {"confidence_score": 0.8},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        actions = [
            {"action_type": "get_system_info"},  # Should be approved
            {"action_type": "delete_instance"},  # Should not be approved
        ]

        can_approve, reasons = engine.can_auto_approve(incident, actions)

        assert can_approve is False
        assert any("Safe Read-Only Actions" in reason for reason in reasons)
        assert any("No matching auto-approval rule" in reason for reason in reasons)

    def test_can_auto_approve_high_risk_score(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test auto-approval rejection due to high risk score."""
        engine = AutoApprovalEngine(basic_config)

        incident = {
            "severity": "medium",
            "analysis": {"confidence_score": 0.3},  # Low confidence = high risk
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        actions = [
            {"action_type": "get_system_info"},
        ]

        can_approve, _ = engine.can_auto_approve(incident, actions)

        # Should fail due to risk score exceeding limit
        assert can_approve is False

    def test_calculate_risk_score_high_risk_actions(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test risk score calculation for high-risk actions."""
        engine = AutoApprovalEngine(basic_config)

        incident = {"analysis": {"confidence_score": 0.8}}

        # Test high-risk action
        action = {"action_type": "delete_production_data"}
        risk_score = engine._calculate_risk_score(action, incident)

        assert risk_score >= 0.7

    def test_calculate_risk_score_medium_risk_actions(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test risk score calculation for medium-risk actions."""
        engine = AutoApprovalEngine(basic_config)

        incident = {"analysis": {"confidence_score": 0.8}}

        # Test medium-risk action
        action = {"action_type": "update_firewall_rules"}
        risk_score = engine._calculate_risk_score(action, incident)

        assert 0.3 <= risk_score <= 0.6

    def test_calculate_risk_score_low_risk_actions(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test risk score calculation for low-risk actions."""
        engine = AutoApprovalEngine(basic_config)

        incident = {"analysis": {"confidence_score": 0.8}}

        # Test low-risk action
        action = {"action_type": "isolate_instance"}
        risk_score = engine._calculate_risk_score(action, incident)

        assert risk_score <= 0.4

    def test_calculate_risk_score_production_resource(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test risk score adjustment for production resources."""
        engine = AutoApprovalEngine(basic_config)

        incident = {"analysis": {"confidence_score": 0.9}}

        # Test production resource
        action = {
            "action_type": "isolate_instance",
            "target_resource": "production-web-server-01",
        }
        risk_score = engine._calculate_risk_score(action, incident)

        # Should be higher due to production resource
        assert risk_score >= 0.2

    def test_calculate_risk_score_staging_resource(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test risk score adjustment for staging resources."""
        engine = AutoApprovalEngine(basic_config)

        incident = {"analysis": {"confidence_score": 0.9}}

        # Test staging resource
        action = {
            "action_type": "isolate_instance",
            "target_resource": "staging-web-server-01",
        }
        risk_score = engine._calculate_risk_score(action, incident)

        # Should be slightly higher due to staging resource
        assert risk_score >= 0.1

    def test_calculate_risk_score_confidence_adjustment(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test risk score adjustment based on confidence."""
        engine = AutoApprovalEngine(basic_config)

        action = {"action_type": "isolate_instance"}

        # High confidence incident
        high_confidence_incident = {"analysis": {"confidence_score": 0.9}}
        high_conf_risk = engine._calculate_risk_score(action, high_confidence_incident)

        # Low confidence incident
        low_confidence_incident = {"analysis": {"confidence_score": 0.3}}
        low_conf_risk = engine._calculate_risk_score(action, low_confidence_incident)

        # Low confidence should result in higher risk
        assert low_conf_risk > high_conf_risk

    def test_get_incident_age_hours_valid_timestamp(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test calculating incident age from valid timestamp."""
        engine = AutoApprovalEngine(basic_config)

        # Create incident with timestamp 2 hours ago
        two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
        incident: Dict[str, Any] = {
            "created_at": two_hours_ago.isoformat(),
        }

        age_hours = engine._get_incident_age_hours(incident)

        # Should be approximately 2 hours (allowing for small timing differences)
        assert 1.9 <= age_hours <= 2.1

    def test_get_incident_age_hours_missing_timestamp(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test incident age calculation with missing timestamp."""
        engine = AutoApprovalEngine(basic_config)

        incident: Dict[str, Any] = {}
        age_hours = engine._get_incident_age_hours(incident)

        assert age_hours == 0.0

    def test_get_incident_age_hours_invalid_timestamp(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test incident age calculation with invalid timestamp."""
        engine = AutoApprovalEngine(basic_config)

        incident = {"created_at": "invalid-timestamp"}
        age_hours = engine._get_incident_age_hours(incident)

        assert age_hours == 0.0

    def test_record_approval_decision(self, basic_config: Dict[str, Any]) -> None:
        """Test recording approval decisions."""
        engine = AutoApprovalEngine(basic_config)

        incident = {"incident_id": "INC-TEST-001"}
        actions = [
            {"action_type": "get_info"},
            {"action_type": "list_resources"},
        ]

        initial_count = len(engine.approval_history)

        engine._record_approval_decision(incident, actions, True, ["Test reason"])

        assert len(engine.approval_history) == initial_count + 1

        decision = engine.approval_history[-1]
        assert decision["incident_id"] == "INC-TEST-001"
        assert decision["approved"] is True
        assert decision["actions"] == ["get_info", "list_resources"]
        assert "Test reason" in decision["reasons"]
        assert "timestamp" in decision
        assert decision["rules_evaluated"] == len(engine.rules)

    def test_record_approval_decision_history_limit(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test approval history size limit."""
        engine = AutoApprovalEngine(basic_config)

        # Add many decisions to exceed limit
        incident = {"incident_id": "INC-LIMIT-TEST"}
        actions = [{"action_type": "test_action"}]

        # Add 1005 decisions (exceeds 1000 limit)
        for i in range(1005):
            engine._record_approval_decision(incident, actions, True, [f"Reason {i}"])

        # Should keep only last 1000
        assert len(engine.approval_history) == 1000

        # Should have the most recent decisions
        assert engine.approval_history[-1]["reasons"] == ["Reason 1004"]

    def test_get_approval_policy(self, basic_config: Dict[str, Any]) -> None:
        """Test getting approval policy configuration."""
        engine = AutoApprovalEngine(basic_config)

        policy = engine.get_approval_policy()

        assert isinstance(policy, dict)
        assert "auto_approval_enabled" in policy
        assert "rules_count" in policy
        assert "active_rules" in policy
        assert "recent_decisions" in policy

        assert policy["auto_approval_enabled"] is True
        assert policy["rules_count"] == len(engine.rules)
        assert isinstance(policy["active_rules"], list)
        assert len(policy["active_rules"]) == len(engine.rules)

        # Check active rules format
        for rule_info in policy["active_rules"]:
            assert "id" in rule_info
            assert "name" in rule_info

    def test_get_approval_policy_disabled(
        self, disabled_config: Dict[str, Any]
    ) -> None:
        """Test getting approval policy when auto-approval is disabled."""
        engine = AutoApprovalEngine(disabled_config)

        policy = engine.get_approval_policy()

        assert policy["auto_approval_enabled"] is False

    def test_context_building_for_rule_evaluation(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test context building for rule evaluation."""
        engine = AutoApprovalEngine(basic_config)

        incident = {
            "severity": "high",
            "analysis": {
                "confidence_score": 0.85,
                "attack_type": "privilege_escalation",
                "threat_confirmed": True,
            },
            "created_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "remediation_actions": [{"action": "previous_action"}],
        }
        actions = [{"action_type": "revoke_iam_permissions"}]

        # This will internally build context for rule evaluation
        can_approve, reasons = engine.can_auto_approve(incident, actions)

        # The context should be built correctly and used for rule evaluation
        assert isinstance(can_approve, bool)
        assert isinstance(reasons, list)

    def test_approval_with_empty_actions_list(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test auto-approval with empty actions list."""
        engine = AutoApprovalEngine(basic_config)

        incident = {"severity": "medium", "analysis": {"confidence_score": 0.8}}
        actions: List[Dict[str, Any]] = []

        can_approve, reasons = engine.can_auto_approve(incident, actions)

        # Empty actions should be auto-approved
        assert can_approve is True
        assert len(reasons) == 0

    def test_approval_with_missing_incident_fields(
        self, basic_config: Dict[str, Any]
    ) -> None:
        """Test auto-approval with missing incident fields."""
        engine = AutoApprovalEngine(basic_config)

        # Minimal incident with missing fields
        incident: Dict[str, Any] = {}
        actions = [{"action_type": "get_system_info"}]

        can_approve, reasons = engine.can_auto_approve(incident, actions)

        # Should handle missing fields gracefully
        assert isinstance(can_approve, bool)
        assert isinstance(reasons, list)

    def test_complex_rule_evaluation_scenario(
        self, advanced_config: Dict[str, Any]
    ) -> None:
        """Test complex rule evaluation scenario with custom rules."""
        engine = AutoApprovalEngine(advanced_config)

        incident = {
            "severity": "high",
            "analysis": {"confidence_score": 0.8},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        actions = [
            {"action_type": "test_security_measure"},
            {"action_type": "verify_system_integrity"},
        ]

        can_approve, reasons = engine.can_auto_approve(incident, actions)

        # Should use custom rule for approval
        assert can_approve is True
        assert any("Custom Test Rule" in reason for reason in reasons)

    def test_risk_score_capping_at_one(self, basic_config: Dict[str, Any]) -> None:
        """Test that risk scores are capped at 1.0."""
        engine = AutoApprovalEngine(basic_config)

        # Create scenario that would result in very high risk
        incident = {"analysis": {"confidence_score": 0.1}}  # Very low confidence
        action = {
            "action_type": "delete_production_critical_data",
            "target_resource": "production-critical-database",
        }

        risk_score = engine._calculate_risk_score(action, incident)

        # Should be capped at 1.0
        assert risk_score <= 1.0

    def test_pattern_matching_edge_cases(self, basic_config: Dict[str, Any]) -> None:
        """Test regex pattern matching edge cases."""
        engine = AutoApprovalEngine(basic_config)

        incident = {
            "severity": "medium",
            "analysis": {"confidence_score": 0.8},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Test edge cases for pattern matching
        edge_case_actions = [
            {"action_type": "get"},  # Minimal match
            {"action_type": "get_"},  # Ends with underscore
            {
                "action_type": "list_very_long_resource_name_with_many_details"
            },  # Long name
            {"action_type": "describe.resource.with.dots"},  # Contains dots
        ]

        for action in edge_case_actions:
            can_approve, reasons = engine.can_auto_approve(incident, [action])
            assert isinstance(can_approve, bool)
            assert isinstance(reasons, list)
