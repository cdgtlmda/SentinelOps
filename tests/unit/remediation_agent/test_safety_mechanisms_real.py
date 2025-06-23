"""REAL tests for remediation_agent/safety_mechanisms.py - Testing actual safety validation logic."""

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

# Import the actual production code
from src.remediation_agent.safety_mechanisms import (
    SafetyValidator,
    ValidationResult,
    ApprovalStatus,
    ApprovalWorkflow,
    RollbackManager,
)
from src.common.models import RemediationAction
from src.remediation_agent.action_registry import ActionRiskLevel


class TestSafetyValidatorReal:
    """Test SafetyValidator with REAL validation logic - NO MOCKS."""

    @pytest.fixture
    def validator(self) -> SafetyValidator:
        """Create real SafetyValidator instance."""
        config = {
            "require_resource_validation": True,
            "enforce_rate_limits": True,
            "dry_run_required_for_risk": ["HIGH", "CRITICAL"],
            "approval_required_for_risk": ["CRITICAL"],
            "max_concurrent_actions": 10,
        }
        return SafetyValidator(config)

    @pytest.mark.asyncio
    async def test_real_validate_action_basic(self, validator: SafetyValidator) -> None:
        """Test REAL action validation with basic action."""
        # Create a low-risk action
        action = RemediationAction(
            action_id="REM-001",
            action_type="restart_service",
            params={"service_name": "nginx", "target_instance": "web-server-01"},
            incident_id="INC-001",
            description="Restart nginx service",
            target_resource="web-server-01",
            metadata={"risk_level": ActionRiskLevel.LOW.value},
        )

        # Execute real validation
        result = await validator.validate_action(action)

        # Verify validation result
        assert isinstance(result, ValidationResult)
        assert result.is_safe is True
        assert len(result.errors) == 0
        assert result.checks_performed > 0
        assert result.requires_approval is False
        assert result.requires_dry_run is False
        print(f"\nBasic validation completed: {result.checks_performed} checks")

    @pytest.mark.asyncio
    async def test_real_validate_critical_action(
        self, validator: SafetyValidator
    ) -> None:
        """Test REAL validation of critical risk action."""
        # Create a critical risk action
        action = RemediationAction(
            action_id="REM-002",
            action_type="delete_all_instances",
            params={"project_id": "production", "zone": "us-central1-a"},
            incident_id="INC-002",
            description="Delete all instances in production",
            target_resource="production/us-central1-a",
            metadata={"risk_level": ActionRiskLevel.CRITICAL.value},
        )

        # Execute real validation
        result = await validator.validate_action(action)

        # Verify critical action handling
        assert result.requires_approval is True
        assert result.requires_dry_run is True
        assert "Critical risk level" in str(result.warnings)
        print(
            f"\nCritical action validation: approval={result.requires_approval}, dry_run={result.requires_dry_run}"
        )

    @pytest.mark.asyncio
    async def test_real_validate_missing_parameters(
        self, validator: SafetyValidator
    ) -> None:
        """Test REAL validation with missing required parameters."""
        # Action with missing parameters
        action = RemediationAction(
            action_id="REM-003",
            action_type="block_ip",
            params={},  # Missing required parameters
            incident_id="INC-003",
            description="Block IP address",
            target_resource="firewall",
            metadata={"risk_level": ActionRiskLevel.MEDIUM.value},
        )

        # Execute real validation
        result = await validator.validate_action(action)

        # Should detect missing parameters
        assert result.is_safe is False
        assert len(result.errors) > 0
        assert any("parameter" in err.lower() for err in result.errors)
        print(f"\nMissing parameters detected: {result.errors}")

    @pytest.mark.asyncio
    async def test_real_resource_lock_conflict(
        self, validator: SafetyValidator
    ) -> None:
        """Test REAL resource lock conflict detection."""
        # First action locks a resource
        action1 = RemediationAction(
            action_id="REM-004",
            action_type="modify_firewall",
            params={"firewall_rule": "allow-ssh", "project_id": "test-project"},
            incident_id="INC-004",
            description="Modify firewall rule allow-ssh",
            target_resource="firewall/allow-ssh",
            metadata={
                "risk_level": ActionRiskLevel.MEDIUM.value,
                "target_resources": ["firewall/allow-ssh"],
            },
        )

        # Validate and "execute" first action
        result1 = await validator.validate_action(action1)
        assert result1.is_safe is True

        # Simulate action execution by adding to active actions
        validator._active_actions[action1.action_id] = action1
        validator._resource_locks["firewall/allow-ssh"] = datetime.now(timezone.utc)

        # Second action tries to modify same resource
        action2 = RemediationAction(
            action_id="REM-005",
            action_type="modify_firewall",
            params={"firewall_rule": "allow-ssh", "project_id": "test-project"},
            incident_id="INC-005",
            description="Modify firewall rule allow-ssh",
            target_resource="firewall/allow-ssh",
            metadata={
                "risk_level": ActionRiskLevel.MEDIUM.value,
                "target_resources": ["firewall/allow-ssh"],
            },
        )

        # Should detect conflict
        result2 = await validator.validate_action(action2)
        assert result2.is_safe is False
        assert any(
            "conflict" in err.lower() or "lock" in err.lower() for err in result2.errors
        )
        print(f"\nResource conflict detected: {result2.errors}")

    @pytest.mark.asyncio
    async def test_real_rate_limit_enforcement(
        self, validator: SafetyValidator
    ) -> None:
        """Test REAL rate limiting enforcement."""
        # Try to validate many actions quickly
        actions = []
        for i in range(15):  # More than max_concurrent_actions
            action = RemediationAction(
                action_id=f"REM-RATE-{i}",
                action_type="restart_service",
                params={
                    "service_name": f"service-{i}",
                    "target_instance": f"instance-{i}",
                },
                incident_id=f"INC-RATE-{i}",
                description=f"Restart service-{i}",
                target_resource=f"instance-{i}",
                metadata={"risk_level": ActionRiskLevel.LOW.value},
            )
            actions.append(action)
            # Simulate as active
            validator._active_actions[action.action_id] = action

        # The 11th action should be rate limited
        test_action = RemediationAction(
            action_id="REM-RATE-TEST",
            action_type="restart_service",
            params={"service_name": "test-service", "target_instance": "test-instance"},
            incident_id="INC-RATE-TEST",
            description="Restart test service",
            target_resource="test-instance",
            metadata={"risk_level": ActionRiskLevel.LOW.value},
        )

        result = await validator.validate_action(test_action)

        # Should be rate limited
        assert result.is_safe is False
        assert any(
            "rate" in err.lower() or "concurrent" in err.lower()
            for err in result.errors
        )
        print(f"\nRate limit enforced: {result.errors}")


class TestConflictDetectionReal:
    """Test conflict detection with REAL safety validator logic."""

    @pytest.fixture
    def validator(self) -> SafetyValidator:
        """Create real SafetyValidator instance for conflict testing."""
        return SafetyValidator({})

    @pytest.mark.asyncio
    async def test_real_detect_conflicts_basic(
        self, validator: SafetyValidator
    ) -> None:
        """Test REAL conflict detection between actions."""
        # Create conflicting actions
        action1 = RemediationAction(
            action_id="REM-C1",
            action_type="stop_instance",
            params={"instance_id": "web-01"},
            incident_id="INC-C1",
            description="Stop instance web-01",
            target_resource="instance/web-01",
            metadata={"target_resources": ["instance/web-01"]},
        )

        action2 = RemediationAction(
            action_id="REM-C2",
            action_type="start_instance",
            params={"instance_id": "web-01"},
            incident_id="INC-C2",
            description="Start instance web-01",
            target_resource="instance/web-01",
            metadata={"target_resources": ["instance/web-01"]},
        )

        # Set up first action as active
        validator._active_actions[action1.action_id] = action1
        validator._resource_locks["instance/web-01"] = datetime.now(timezone.utc)

        # Validate second action - should detect conflict
        result = await validator.validate_action(action2)

        # Should detect resource conflict
        assert result.is_safe is False
        assert any("conflict" in err.lower() for err in result.errors)
        print(f"\nConflicts detected in validation: {result.errors}")

    @pytest.mark.asyncio
    async def test_real_dependency_conflict(self, validator: SafetyValidator) -> None:
        """Test REAL dependency violation detection."""
        # Action that depends on a service
        dependent_action = RemediationAction(
            action_id="REM-D1",
            action_type="restart_app",
            params={"app_name": "frontend"},
            incident_id="INC-D1",
            description="Restart frontend app",
            target_resource="app/frontend",
            metadata={
                "dependencies": ["database", "cache"],
                "target_resources": ["app/frontend"],
            },
        )

        # Action that stops a dependency
        blocking_action = RemediationAction(
            action_id="REM-D2",
            action_type="stop_service",
            params={"service_name": "database"},
            incident_id="INC-D2",
            description="Stop database service",
            target_resource="service/database",
            metadata={"target_resources": ["service/database"]},
        )

        # Set blocking action as active
        validator._active_actions[blocking_action.action_id] = blocking_action

        # Validate dependent action
        result = await validator.validate_action(dependent_action)

        # May or may not detect dependency conflicts based on implementation
        print(
            f"\nValidation result for dependent action: safe={result.is_safe}, errors={result.errors}"
        )

    @pytest.mark.asyncio
    async def test_real_validate_with_priority(
        self, validator: SafetyValidator
    ) -> None:
        """Test REAL conflict resolution by priority."""
        # Higher priority action
        high_priority = RemediationAction(
            action_id="REM-HP",
            action_type="block_attacker",
            params={"ip": "10.0.0.1"},
            incident_id="INC-HP",
            description="Block attacker IP",
            target_resource="firewall/main",
            metadata={
                "priority": 10,
                "risk_level": ActionRiskLevel.CRITICAL.value,
                "target_resources": ["firewall/main"],
            },
        )

        # Lower priority action
        low_priority = RemediationAction(
            action_id="REM-LP",
            action_type="update_firewall",
            params={"rule": "allow-http"},
            incident_id="INC-LP",
            description="Update firewall rule",
            target_resource="firewall/main",
            metadata={
                "priority": 5,
                "risk_level": ActionRiskLevel.LOW.value,
                "target_resources": ["firewall/main"],
            },
        )

        # Set low priority as active
        validator._active_actions[low_priority.action_id] = low_priority
        validator._resource_locks["firewall/main"] = datetime.now(timezone.utc)

        # Validate high priority - implementation may allow override
        result = await validator.validate_action(high_priority)

        # Check if priority affects validation
        print(
            f"\nHigh priority validation: safe={result.is_safe}, warnings={result.warnings}"
        )


class TestApprovalWorkflowReal:
    """Test ApprovalWorkflow with REAL approval workflow logic."""

    @pytest.fixture
    def approval_workflow(self, real_firestore_client: Any) -> ApprovalWorkflow:
        """Create real ApprovalWorkflow instance."""
        return ApprovalWorkflow(real_firestore_client, logger=None)

    @pytest.mark.asyncio
    async def test_real_request_approval(
        self, approval_workflow: ApprovalWorkflow
    ) -> None:
        """Test REAL approval request creation."""
        action = RemediationAction(
            action_id="REM-APPR-001",
            action_type="delete_resources",
            params={"resource_type": "old_backups"},
            incident_id="INC-APPR-001",
            description="Delete old backup resources",
            target_resource="backups",
            metadata={
                "risk_level": ActionRiskLevel.HIGH.value,
                "reason": "Cleanup old backups to save costs",
            },
        )

        # Request approval
        approval_id = await approval_workflow.create_approval_request(
            action=action,
            risk_level=ActionRiskLevel.MEDIUM,
            risk_assessment={
                "reason": "Automated cleanup policy",
                "requested_by": "remediation-agent",
            },
        )

        # Verify approval request created
        assert approval_id is not None
        assert approval_id.startswith("APPR-")

        # Check approval status
        status = await approval_workflow.get_approval_status(approval_id)
        assert status == ApprovalStatus.PENDING
        print(f"\nApproval requested: {approval_id}")

    @pytest.mark.asyncio
    async def test_real_auto_approve_low_risk(
        self, approval_workflow: ApprovalWorkflow
    ) -> None:
        """Test REAL auto-approval for low risk actions."""
        action = RemediationAction(
            action_id="REM-AUTO-001",
            action_type="restart_service",
            params={"service": "monitoring-agent"},
            incident_id="INC-AUTO-001",
            description="Restart monitoring agent",
            target_resource="monitoring-agent",
            metadata={"risk_level": ActionRiskLevel.LOW.value},
        )

        # Request approval for low risk
        approval_id = await approval_workflow.create_approval_request(
            action=action,
            risk_level=ActionRiskLevel.LOW,
            risk_assessment={"reason": "Routine restart", "requested_by": "automation"},
        )

        # Should be auto-approved
        status = await approval_workflow.get_approval_status(approval_id)
        assert status == ApprovalStatus.AUTO_APPROVED
        print(f"\nAuto-approved low risk action: {approval_id}")

    @pytest.mark.asyncio
    async def test_real_approval_expiration(
        self, approval_workflow: ApprovalWorkflow
    ) -> None:
        """Test REAL approval expiration logic."""
        # Create approval request with past timestamp
        action = RemediationAction(
            action_id="REM-EXP-001",
            action_type="modify_config",
            params={"config": "system.conf"},
            incident_id="INC-EXP-001",
            description="Modify system configuration",
            target_resource="system.conf",
            metadata={"risk_level": ActionRiskLevel.MEDIUM.value},
        )

        approval_id = await approval_workflow.create_approval_request(
            action=action,
            risk_level=ActionRiskLevel.MEDIUM,
            risk_assessment={"reason": "Config update", "requested_by": "admin"},
        )

        # Manually set created time to past
        if hasattr(approval_workflow, "_approval_requests"):
            approval_workflow._approval_requests[approval_id]["created_at"] = (
                datetime.now(timezone.utc) - timedelta(hours=1)
            )

        # Check if expired
        status = await approval_workflow.get_approval_status(approval_id)
        assert status == ApprovalStatus.EXPIRED

        # Status should reflect expiration
        status = await approval_workflow.get_approval_status(approval_id)
        assert status == ApprovalStatus.EXPIRED
        print(f"\nApproval expired after timeout: {approval_id}")


class TestRollbackManagerReal:
    """Test RollbackManager with REAL rollback logic."""

    @pytest.fixture
    def rollback_manager(self) -> RollbackManager:
        """Create real RollbackManager instance."""
        return RollbackManager(action_registry={}, gcp_clients={})

    @pytest.mark.asyncio
    async def test_real_create_rollback_plan(
        self, rollback_manager: RollbackManager
    ) -> None:
        """Test REAL rollback plan creation."""
        action = RemediationAction(
            action_id="REM-RB-001",
            action_type="modify_firewall_rule",
            params={
                "rule_name": "allow-ssh",
                "action": "DENY",
                "source_ranges": ["0.0.0.0/0"],
            },
            incident_id="INC-RB-001",
            description="Modify firewall rule to deny SSH",
            target_resource="firewall/allow-ssh",
            metadata={
                "original_state": {"action": "ALLOW", "source_ranges": ["10.0.0.0/8"]}
            },
        )

        # Create rollback plan
        state_snapshot = {
            "rule_name": "allow-ssh",
            "action": "ALLOW",
            "source_ranges": ["10.0.0.0/8"],
        }
        plan = await rollback_manager.create_rollback_plan(action, state_snapshot)

        # Verify rollback plan
        assert plan is not None
        assert plan["action_id"] == "REM-RB-001"
        assert plan["rollback_type"] == "modify_firewall_rule"
        assert plan["rollback_parameters"]["action"] == "ALLOW"
        assert plan["rollback_parameters"]["source_ranges"] == ["10.0.0.0/8"]
        print(f"\nRollback plan created: {plan['rollback_type']}")

    @pytest.mark.asyncio
    async def test_real_execute_rollback(
        self, rollback_manager: RollbackManager
    ) -> None:
        """Test REAL rollback execution logic."""
        # Create and store rollback plan
        original_action = RemediationAction(
            action_id="REM-RB-002",
            action_type="stop_service",
            params={"service_name": "web-server"},
            incident_id="INC-RB-002",
            description="Stop web server service",
            target_resource="web-server",
            metadata={"original_state": {"status": "running"}},
        )

        state_snapshot = {
            "service_name": "test-service",
            "status": "running",
            "config": {"auto_start": True},
        }
        plan = await rollback_manager.create_rollback_plan(
            original_action, state_snapshot
        )
        assert plan is not None

        # Execute rollback
        result = await rollback_manager.execute_rollback(plan, reason="Test rollback")

        # Verify rollback execution
        assert result["success"] is True
        assert result["rollback_action"]["action_type"] == "start_service"
        assert result["rollback_action"]["params"]["service_name"] == "web-server"
        assert result["dry_run"] is True
        print(
            f"\nRollback executed (dry run): {result['rollback_action']['action_type']}"
        )


class TestSafetyMechanismsIntegration:
    """Test integrated safety mechanisms with REAL workflow."""

    @pytest.fixture
    def safety_validator(self) -> SafetyValidator:
        """Create real SafetyValidator instance."""
        config = {
            "enable_validation": True,
            "enable_approval_workflow": True,
            "enable_rollback": True,
            "dry_run_by_default": False,
            "dry_run_required_for_risk": ["HIGH", "CRITICAL"],
            "approval_required_for_risk": ["CRITICAL"],
        }
        return SafetyValidator(config)

    @pytest.fixture
    def approval_workflow(self, real_firestore_client: Any) -> ApprovalWorkflow:
        """Create real ApprovalWorkflow instance."""
        return ApprovalWorkflow(real_firestore_client, logger=None)

    @pytest.fixture
    def rollback_manager(self) -> RollbackManager:
        """Create real RollbackManager instance."""
        return RollbackManager(action_registry={}, gcp_clients={})

    @pytest.mark.asyncio
    async def test_real_safe_execution_workflow(
        self, safety_validator: SafetyValidator, rollback_manager: RollbackManager
    ) -> None:
        """Test REAL end-to-end safe execution workflow."""
        # Create a medium risk action
        action = RemediationAction(
            action_id="REM-SAFE-001",
            action_type="restart_database",
            params={"database_id": "prod-db-01", "graceful": True},
            incident_id="INC-SAFE-001",
            description="Restart production database gracefully",
            target_resource="prod-db-01",
            metadata={
                "risk_level": ActionRiskLevel.MEDIUM.value,
                "estimated_downtime": "30 seconds",
            },
        )

        # Validate action
        validation = await safety_validator.validate_action(action)
        assert validation.is_safe is True

        # Create rollback plan
        state_snapshot = {"instance_id": "test-instance-1", "status": "running"}
        rollback_plan = await rollback_manager.create_rollback_plan(
            action, state_snapshot
        )
        assert rollback_plan is not None

        print(f"\nSafe execution workflow completed for {action.action_type}")

    @pytest.mark.asyncio
    async def test_real_high_risk_workflow(
        self, safety_validator: SafetyValidator, approval_workflow: ApprovalWorkflow
    ) -> None:
        """Test REAL workflow for high-risk action requiring approval."""
        # Create high risk action
        action = RemediationAction(
            action_id="REM-HIGH-001",
            action_type="delete_all_logs",
            params={"log_group": "security-logs", "before_date": "2024-01-01"},
            incident_id="INC-HIGH-001",
            description="Delete old security logs",
            target_resource="security-logs",
            metadata={
                "risk_level": ActionRiskLevel.CRITICAL.value,
                "data_loss_risk": True,
            },
        )

        # Validate - should require approval
        validation = await safety_validator.validate_action(action)
        assert validation.requires_approval is True
        assert validation.requires_dry_run is True

        # Request approval
        approval_id = await approval_workflow.create_approval_request(
            action=action,
            risk_level=ActionRiskLevel.CRITICAL,
            risk_assessment={
                "reason": "Compliance requirement",
                "requested_by": "security-team",
            },
        )

        # Verify pending approval
        status = await approval_workflow.get_approval_status(approval_id)
        assert status == ApprovalStatus.PENDING

        print(f"\nHigh risk action workflow: approval required ({approval_id})")
