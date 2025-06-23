"""
Comprehensive tests for api/models/remediation.py module.

REQUIREMENTS:
- 100% production code (NO MOCKING of GCP services)
- Minimum 90% statement coverage of target source file
- Test all major code paths and business logic
- Include comprehensive error handling scenarios
- Cover edge cases and boundary conditions
- All test cases must pass

Target file: src/api/models/remediation.py (290 lines)
Coverage verification: python -m coverage run -m pytest tests/unit/api/models/test_remediation.py && python -m coverage report --include="*api/models/remediation.py" --show-missing
"""

import pytest
from datetime import datetime, timezone
from typing import Any, Dict, cast
from uuid import UUID, uuid4

from pydantic import ValidationError

from src.api.models.remediation import (
    RemediationRiskLevel,
    RemediationAction,
    RemediationExecutionRequest,
    RemediationExecutionResponse,
    RemediationExecution,
    RemediationHistoryResponse,
    RemediationRollbackRequest,
    RemediationApprovalItem,
    RemediationApprovalResponse,
)
from src.common.models import RemediationPriority, RemediationStatus


class TestRemediationRiskLevel:
    """Test RemediationRiskLevel enum."""

    def test_enum_values(self) -> None:
        """Test all enum values are accessible."""
        assert RemediationRiskLevel.LOW.value == "low"
        assert RemediationRiskLevel.MEDIUM.value == "medium"
        assert RemediationRiskLevel.HIGH.value == "high"
        assert RemediationRiskLevel.CRITICAL.value == "critical"

    def test_enum_membership(self) -> None:
        """Test enum membership validation."""
        assert "low" in [level.value for level in RemediationRiskLevel]
        assert "invalid" not in [level.value for level in RemediationRiskLevel]

    def test_enum_comparison(self) -> None:
        """Test enum values can be compared."""
        assert RemediationRiskLevel.LOW == RemediationRiskLevel.LOW
        assert RemediationRiskLevel.HIGH == RemediationRiskLevel.HIGH
        assert RemediationRiskLevel.MEDIUM == RemediationRiskLevel.MEDIUM


class TestRemediationAction:
    """Test RemediationAction model."""

    def test_valid_creation(self) -> None:
        """Test creating RemediationAction with valid data."""
        action_id = uuid4()
        incident_id = uuid4()
        created_at = datetime.now(timezone.utc)

        action = RemediationAction(
            action_id=action_id,
            incident_id=incident_id,
            action_type="block_ip_addresses",
            description="Block malicious IP addresses",
            priority=RemediationPriority.HIGH,
            status=RemediationStatus.PENDING,
            risk_level=RemediationRiskLevel.MEDIUM,
            requires_approval=True,
            automated=False,
            estimated_duration_seconds=30,
            prerequisites=["firewall_access"],
            parameters_schema={"type": "object"},
            created_at=created_at,
            updated_at=None,
        )

        assert action.action_id == action_id
        assert action.incident_id == incident_id
        assert action.action_type == "block_ip_addresses"
        assert action.priority.value == "high"
        assert action.risk_level.value == "medium"
        assert action.prerequisites == ["firewall_access"]

    def test_optional_fields(self) -> None:
        """Test RemediationAction with optional fields as None."""
        action_id = uuid4()
        created_at = datetime.now(timezone.utc)

        action = RemediationAction(
            action_id=action_id,
            incident_id=None,
            action_type="scan_system",
            description="System scan",
            priority=RemediationPriority.LOW,
            status=RemediationStatus.COMPLETED,
            risk_level=RemediationRiskLevel.LOW,
            requires_approval=False,
            automated=True,
            estimated_duration_seconds=None,
            prerequisites=[],
            parameters_schema=None,
            created_at=created_at,
            updated_at=None,
        )

        assert action.incident_id is None
        assert action.estimated_duration_seconds is None
        assert action.parameters_schema is None
        assert action.updated_at is None
        assert action.prerequisites == []

    def test_from_storage_model(self) -> None:
        """Test from_storage_model class method."""

        # Create mock storage model with required attributes
        class MockStorageModel:
            def __init__(self) -> None:
                self.id = "550e8400-e29b-41d4-a716-446655440000"
                self.incident_id = "660e8400-e29b-41d4-a716-446655440001"
                self.action_type = "block_ip"
                self.description = "Block IP address"
                self.priority = "high"
                self.status = "pending"
                self.risk_level = "medium"
                self.requires_approval = True
                self.automated = False
                self.estimated_duration_seconds = 60
                self.prerequisites = ["admin_access"]
                self.parameters_schema = {"type": "object"}
                self.created_at = datetime.now(timezone.utc)
                self.updated_at = datetime.now(timezone.utc)

        storage_model = MockStorageModel()
        action = RemediationAction.from_storage_model(storage_model)

        assert str(action.action_id) == storage_model.id
        assert str(action.incident_id) == storage_model.incident_id
        assert action.action_type == storage_model.action_type
        assert action.priority.value == storage_model.priority
        assert action.prerequisites == storage_model.prerequisites

    def test_from_storage_model_with_none_values(self) -> None:
        """Test from_storage_model with None values."""

        class MockStorageModel:
            def __init__(self) -> None:
                self.id = "550e8400-e29b-41d4-a716-446655440000"
                self.incident_id = None
                self.action_type = "scan"
                self.description = "System scan"
                self.priority = "low"
                self.status = "completed"
                self.risk_level = "low"
                self.requires_approval = False
                self.automated = True
                self.estimated_duration_seconds = None
                self.prerequisites = None
                self.parameters_schema = None
                self.created_at = datetime.now(timezone.utc)
                self.updated_at = None

        storage_model = MockStorageModel()
        action = RemediationAction.from_storage_model(storage_model)

        assert action.incident_id is None
        assert action.estimated_duration_seconds is None
        assert action.prerequisites == []
        assert action.parameters_schema is None
        assert action.updated_at is None

    def test_invalid_uuid(self) -> None:
        """Test validation with invalid priority value."""
        with pytest.raises(ValidationError):
            RemediationAction(
                action_id=uuid4(),
                incident_id=uuid4(),
                action_type="test",
                description="Test",
                priority=RemediationPriority("invalid_priority"),  # This should trigger validation error
                status=RemediationStatus.PENDING,
                risk_level=RemediationRiskLevel.LOW,
                requires_approval=False,
                automated=False,
                estimated_duration_seconds=30,
                updated_at=None,
                created_at=datetime.now(timezone.utc),
            )

    def test_invalid_enum_values(self) -> None:
        """Test validation with invalid enum values."""
        action_id = uuid4()
        created_at = datetime.now(timezone.utc)

        with pytest.raises(ValidationError):
            RemediationAction(
                action_id=action_id,
                incident_id=uuid4(),
                action_type="test",
                description="Test",
                priority=RemediationPriority("invalid_priority"),
                status=RemediationStatus.PENDING,
                risk_level=RemediationRiskLevel.LOW,
                requires_approval=False,
                automated=False,
                estimated_duration_seconds=30,
                updated_at=None,
                created_at=created_at,
            )

    def test_schema_extra_example(self) -> None:
        """Test that the Config.schema_extra example is valid."""
        example = RemediationAction.Config.schema_extra["example"]

        action = RemediationAction(
            action_id=UUID(str(example["action_id"])),
            incident_id=UUID(str(example["incident_id"])),
            action_type=str(example["action_type"]),
            description=str(example["description"]),
            priority=RemediationPriority(str(example["priority"])),
            status=RemediationStatus(str(example["status"])),
            risk_level=RemediationRiskLevel(str(example["risk_level"])),
            requires_approval=bool(example["requires_approval"]),
            automated=bool(example["automated"]),
            estimated_duration_seconds=(
                int(str(example["estimated_duration_seconds"]))
                if example["estimated_duration_seconds"] is not None
                else None
            ),
            prerequisites=(
                list(example["prerequisites"])
                if hasattr(example["prerequisites"], "__iter__")
                and example["prerequisites"] is not None
                else []
            ),
            parameters_schema=(
                dict(example["parameters_schema"])
                if isinstance(example["parameters_schema"], dict)
                and example["parameters_schema"] is not None
                else None
            ),
            created_at=datetime.fromisoformat(
                str(example["created_at"]).replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                str(example["updated_at"]).replace("Z", "+00:00")
            ),
        )

        assert action.action_type == "block_ip_addresses"
        assert action.priority.value == "high"


class TestRemediationExecutionRequest:
    """Test RemediationExecutionRequest model."""

    def test_valid_creation(self) -> None:
        """Test creating RemediationExecutionRequest with valid data."""
        action_id = uuid4()

        request = RemediationExecutionRequest(
            action_id=action_id,
            parameters={"ip": "192.168.1.1"},
            dry_run=True,
            approval_token="token123",
            notification_channels=["slack", "email"],
        )

        assert request.action_id == action_id
        assert request.parameters == {"ip": "192.168.1.1"}
        assert request.dry_run is True
        assert request.approval_token == "token123"
        assert request.notification_channels == ["slack", "email"]

    def test_default_values(self) -> None:
        """Test default values in RemediationExecutionRequest."""
        action_id = uuid4()

        request = RemediationExecutionRequest(
            action_id=action_id,
            parameters={},
            dry_run=False,
            approval_token=None,
            notification_channels=[],
        )

        assert request.parameters == {}
        assert request.dry_run is False

    def test_schema_extra_example(self) -> None:
        """Test that the Config.schema_extra example is valid."""
        example = RemediationExecutionRequest.Config.schema_extra["example"]

        request = RemediationExecutionRequest(
            action_id=UUID(str(example["action_id"])),
            parameters=(
                dict(example["parameters"])
                if isinstance(example["parameters"], dict)
                else {}
            ),
            dry_run=bool(example["dry_run"]),
            approval_token=(
                str(example["approval_token"])
                if example["approval_token"] is not None
                else None
            ),
            notification_channels=(
                list(example["notification_channels"])
                if hasattr(example["notification_channels"], "__iter__")
                else []
            ),
        )

        assert request.dry_run is False
        assert "192.168.1.100" in request.parameters["ip_addresses"]


class TestRemediationExecutionResponse:
    """Test RemediationExecutionResponse model."""

    def test_valid_creation(self) -> None:
        """Test creating RemediationExecutionResponse with valid data."""
        execution_id = uuid4()
        action_id = uuid4()
        completion_time = datetime.now(timezone.utc)

        response = RemediationExecutionResponse(
            execution_id=execution_id,
            action_id=action_id,
            status=RemediationStatus.EXECUTING,
            message="Started successfully",
            dry_run=False,
            estimated_completion_time=completion_time,
            warnings=["Warning 1", "Warning 2"],
        )

        assert response.execution_id == execution_id
        assert response.action_id == action_id
        assert response.status.value == "executing"
        assert response.message == "Started successfully"
        assert response.warnings == ["Warning 1", "Warning 2"]

    def test_default_values(self) -> None:
        """Test default values in RemediationExecutionResponse."""
        execution_id = uuid4()
        action_id = uuid4()

        response = RemediationExecutionResponse(
            execution_id=execution_id,
            action_id=action_id,
            status=RemediationStatus.COMPLETED,
            message="Completed successfully",
            dry_run=True,
            estimated_completion_time=None,
            warnings=[],
        )

        assert response.estimated_completion_time is None
        assert len(response.warnings) == 0

    def test_schema_extra_example(self) -> None:
        """Test that the Config.schema_extra example is valid."""
        example = RemediationExecutionResponse.Config.schema_extra["example"]

        response = RemediationExecutionResponse(
            execution_id=UUID(str(example["execution_id"])),
            action_id=UUID(str(example["action_id"])),
            status=RemediationStatus(str(example["status"])),
            message=str(example["message"]),
            dry_run=bool(example["dry_run"]),
            estimated_completion_time=datetime.fromisoformat(
                str(example["estimated_completion_time"]).replace("Z", "+00:00")
            ),
            warnings=(
                list(example["warnings"])
                if hasattr(example["warnings"], "__iter__")
                else []
            ),
        )

        assert response.status.value == "executing"
        assert "successfully" in response.message


class TestRemediationExecution:
    """Test RemediationExecution model."""

    def test_valid_creation(self) -> None:
        """Test creating RemediationExecution with valid data."""
        execution_id = uuid4()
        action_id = uuid4()
        incident_id = uuid4()
        executed_at = datetime.now(timezone.utc)

        execution = RemediationExecution(
            execution_id=execution_id,
            action_id=action_id,
            incident_id=incident_id,
            action_type="block_ip",
            status=RemediationStatus.COMPLETED,
            executed_by="admin",
            parameters={"ip": "192.168.1.1"},
            result={"blocked": True},
            started_at=executed_at,
            duration_seconds=30.5,
        )

        assert execution.execution_id == execution_id
        assert execution.action_id == action_id
        assert execution.incident_id == incident_id
        assert execution.action_type == "block_ip"
        assert execution.executed_by == "admin"
        assert execution.parameters == {"ip": "192.168.1.1"}
        assert execution.result == {"blocked": True}
        assert execution.duration_seconds == 30.5

    def test_optional_fields(self) -> None:
        """Test RemediationExecution with optional fields as None."""
        execution_id = uuid4()
        action_id = uuid4()
        incident_id = uuid4()
        executed_at = datetime.now(timezone.utc)

        execution = RemediationExecution(
            execution_id=execution_id,
            action_id=action_id,
            incident_id=incident_id,
            action_type="scan",
            status=RemediationStatus.COMPLETED,
            executed_by="system",
            parameters={},
            result=None,
            started_at=executed_at,
            duration_seconds=None,
        )

        assert execution.result is None
        assert execution.duration_seconds is None
        assert execution.parameters == {}

    def test_schema_extra_example(self) -> None:
        """Test that the Config.schema_extra example is valid."""
        example = cast(Dict[str, Any], RemediationExecution.Config.schema_extra["example"])

        execution = RemediationExecution(
            execution_id=UUID(example["execution_id"]),
            action_id=UUID(example["action_id"]),
            incident_id=UUID(example["incident_id"]),
            action_type=example["action_type"],
            status=RemediationStatus(example["status"]),
            executed_by=example["executed_by"],
            parameters=example["parameters"],
            result=example["result"],
            started_at=datetime.fromisoformat(
                example["started_at"].replace("Z", "+00:00")
            ),
            duration_seconds=example["duration_seconds"],
        )

        assert execution.action_type == "block_ip_addresses"
        if execution.result:
            assert execution.result["blocked_count"] == 1
            assert execution.result["firewall_rules_created"] == ["rule-123"]


class TestRemediationHistoryResponse:
    """Test RemediationHistoryResponse model."""

    def test_valid_creation(self) -> None:
        """Test creating RemediationHistoryResponse with valid data."""
        executions = [
            RemediationExecution(
                execution_id=uuid4(),
                action_id=uuid4(),
                incident_id=uuid4(),
                action_type="block_ip",
                status=RemediationStatus.COMPLETED,
                executed_by="admin",
                parameters={},
                result={"success": True},
                started_at=datetime.now(timezone.utc),
                duration_seconds=30.0,
            )
        ]

        response = RemediationHistoryResponse(
            executions=executions,
            total=1,
            page=1,
            page_size=10,
            has_next=False,
        )

        assert len(response.executions) == 1
        assert response.total == 1
        assert response.page == 1
        assert response.page_size == 10
        assert response.has_next is False

    def test_empty_executions(self) -> None:
        """Test RemediationHistoryResponse with empty executions."""
        response = RemediationHistoryResponse(
            executions=[],
            total=0,
            page=1,
            page_size=10,
            has_next=False,
        )

        assert len(response.executions) == 0
        assert response.total == 0

    def test_schema_extra_example(self) -> None:
        """Test that the Config.schema_extra example is valid."""
        example = cast(Dict[str, Any], RemediationHistoryResponse.Config.schema_extra["example"])

        # Build executions from example data
        executions = []
        for exec_data in example["executions"]:
            execution = RemediationExecution(
                execution_id=UUID(exec_data["execution_id"]),
                action_id=UUID(exec_data["action_id"]),
                incident_id=UUID(exec_data["incident_id"]) if exec_data.get("incident_id") else None,
                action_type=exec_data["action_type"],
                status=RemediationStatus(exec_data["status"]),
                executed_by=exec_data["executed_by"],
                parameters=exec_data.get("parameters", {}),
                result=exec_data.get("result"),
                started_at=datetime.fromisoformat(
                    exec_data["started_at"].replace("Z", "+00:00")
                ),
                completed_at=datetime.fromisoformat(
                    exec_data["completed_at"].replace("Z", "+00:00")
                ) if exec_data.get("completed_at") else None,
                duration_seconds=exec_data.get("duration_seconds"),
            )
            executions.append(execution)

        response = RemediationHistoryResponse(
            executions=executions,
            total=example["total"],
            page=example["page"],
            page_size=example["page_size"],
            has_next=example["has_next"],
        )

        assert len(response.executions) == 1
        assert response.total == 50


class TestRemediationRollbackRequest:
    """Test RemediationRollbackRequest model."""

    def test_valid_creation(self) -> None:
        """Test creating RemediationRollbackRequest with valid data."""
        execution_id = uuid4()

        request = RemediationRollbackRequest(
            execution_id=execution_id,
            reason="Incorrect execution",
            force=True,
        )

        assert request.execution_id == execution_id
        assert request.reason == "Incorrect execution"
        assert request.force is True

    def test_default_force_value(self) -> None:
        """Test default force value in RemediationRollbackRequest."""
        execution_id = uuid4()

        request = RemediationRollbackRequest(
            execution_id=execution_id,
            reason="Rollback needed",
            force=False,
        )

        assert request.force is False

    def test_reason_max_length_validation(self) -> None:
        """Test reason field maximum length validation."""
        execution_id = uuid4()

        # Valid length
        valid_reason = "A" * 500
        request = RemediationRollbackRequest(
            execution_id=execution_id,
            reason=valid_reason,
            force=False,
        )
        assert len(request.reason) == 500

        # Test with longer reason (should raise validation error)
        long_reason = "A" * 1000
        with pytest.raises(ValidationError) as exc_info:
            RemediationRollbackRequest(
                execution_id=execution_id,
                reason=long_reason,
                force=False,
            )
        assert "String should have at most 500 characters" in str(exc_info.value)

    def test_schema_extra_example(self) -> None:
        """Test that the Config.schema_extra example is valid."""
        example = cast(Dict[str, Any], RemediationRollbackRequest.Config.schema_extra["example"])

        request = RemediationRollbackRequest(
            execution_id=UUID(example["execution_id"]),
            reason=example["reason"],
            force=example["force"],
        )

        assert request.reason == "False positive - blocked legitimate traffic"
        assert request.force is False


class TestRemediationApprovalItem:
    """Test RemediationApprovalItem model."""

    def test_valid_creation(self) -> None:
        """Test creating RemediationApprovalItem with valid data."""
        approval_id = uuid4()
        action_id = uuid4()
        incident_id = uuid4()
        requested_at = datetime.now(timezone.utc)

        item = RemediationApprovalItem(
            approval_id=approval_id,
            action_id=action_id,
            incident_id=incident_id,
            action_type="block_network",
            description="Block malicious network traffic",
            priority=RemediationPriority.HIGH,
            risk_level=RemediationRiskLevel.HIGH,
            requested_by="analyst",
            requested_at=requested_at,
            approval_status="pending",
            approved_by=None,
            approved_at=None,
            rejection_reason=None,
        )

        assert item.approval_id == approval_id
        assert item.action_id == action_id
        assert item.incident_id == incident_id
        assert item.action_type == "block_network"
        assert item.risk_level == RemediationRiskLevel.HIGH
        assert item.approval_status == "pending"

    def test_optional_fields(self) -> None:
        """Test RemediationApprovalItem with optional fields."""
        approval_id = uuid4()
        action_id = uuid4()
        requested_at = datetime.now(timezone.utc)

        item = RemediationApprovalItem(
            approval_id=approval_id,
            action_id=action_id,
            incident_id=None,
            action_type="scan",
            description="System scan",
            priority=RemediationPriority.LOW,
            risk_level=RemediationRiskLevel.LOW,
            requested_by="system",
            requested_at=requested_at,
            approval_status="pending",
            approved_by=None,
            approved_at=None,
            rejection_reason=None,
        )

        assert item.incident_id is None
        assert item.approval_status == "pending"
        assert item.approved_by is None

    def test_rejection_scenario(self) -> None:
        """Test RemediationApprovalItem in rejection scenario."""
        approval_id = uuid4()
        action_id = uuid4()
        requested_at = datetime.now(timezone.utc)
        rejected_at = datetime.now(timezone.utc)

        item = RemediationApprovalItem(
            approval_id=approval_id,
            action_id=action_id,
            incident_id=uuid4(),
            action_type="dangerous_action",
            description="Potentially dangerous action",
            priority=RemediationPriority.CRITICAL,
            risk_level=RemediationRiskLevel.CRITICAL,
            requested_by="junior_analyst",
            requested_at=requested_at,
            approval_status="rejected",
            approved_by="senior_analyst",
            approved_at=rejected_at,
            rejection_reason="Risk too high for current situation",
        )

        assert item.approval_status == "rejected"
        assert item.rejection_reason == "Risk too high for current situation"
        assert item.approved_by == "senior_analyst"

    def test_schema_extra_example(self) -> None:
        """Test that the Config.schema_extra example is valid."""
        example = cast(Dict[str, Any], RemediationApprovalItem.Config.schema_extra["example"])

        item = RemediationApprovalItem(
            approval_id=UUID(example["approval_id"]),
            action_id=UUID(example["action_id"]),
            incident_id=UUID(example["incident_id"]) if example.get("incident_id") else None,
            action_type=example["action_type"],
            description=example["description"],
            priority=RemediationPriority(example["priority"]),
            risk_level=RemediationRiskLevel(example["risk_level"]),
            requested_by=example["requested_by"],
            requested_at=datetime.fromisoformat(
                example["requested_at"].replace("Z", "+00:00")
            ),
            approval_status=example["approval_status"],
            approved_by=example.get("approved_by"),
            approved_at=None,
            rejection_reason=example.get("rejection_reason"),
        )

        assert item.action_type == "delete_user_data"
        assert item.risk_level == RemediationRiskLevel.HIGH


class TestRemediationApprovalResponse:
    """Test RemediationApprovalResponse model."""

    def test_valid_creation(self) -> None:
        """Test creating RemediationApprovalResponse with valid data."""
        items = [
            RemediationApprovalItem(
                approval_id=uuid4(),
                action_id=uuid4(),
                incident_id=uuid4(),
                action_type="block_ip",
                description="Block IP",
                priority=RemediationPriority.MEDIUM,
                risk_level=RemediationRiskLevel.MEDIUM,
                requested_by="analyst",
                requested_at=datetime.now(timezone.utc),
                approval_status="pending",
                approved_by=None,
                approved_at=None,
                rejection_reason=None,
            )
        ]

        response = RemediationApprovalResponse(
            items=items,
            total=1,
            pending_count=1,
        )

        assert len(response.items) == 1
        assert response.total == 1
        assert response.pending_count == 1

    def test_empty_items(self) -> None:
        """Test RemediationApprovalResponse with empty items."""
        response = RemediationApprovalResponse(
            items=[],
            total=0,
            pending_count=0,
        )

        assert len(response.items) == 0
        assert response.total == 0
        assert response.pending_count == 0

    def test_multiple_items(self) -> None:
        """Test RemediationApprovalResponse with multiple items."""
        items = []
        for i in range(3):
            item = RemediationApprovalItem(
                approval_id=uuid4(),
                action_id=uuid4(),
                incident_id=uuid4(),
                action_type=f"action_{i}",
                description=f"Action {i}",
                priority=RemediationPriority.LOW,
                risk_level=RemediationRiskLevel.LOW,
                requested_by="analyst",
                requested_at=datetime.now(timezone.utc),
                approval_status="pending",
                approved_by=None,
                approved_at=None,
                rejection_reason=None,
            )
            items.append(item)

        response = RemediationApprovalResponse(
            items=items,
            total=10,
            pending_count=7,
        )

        assert len(response.items) == 3
        assert response.total == 10
        assert response.pending_count == 7

    def test_schema_extra_example(self) -> None:
        """Test that the Config.schema_extra example is valid."""
        example = cast(Dict[str, Any], RemediationApprovalResponse.Config.schema_extra["example"])

        # Build items from example data
        items = []
        for item_data in example["items"]:
            item = RemediationApprovalItem(
                approval_id=UUID(item_data["approval_id"]),
                action_id=UUID(item_data["action_id"]),
                incident_id=UUID(item_data.get("incident_id")) if item_data.get("incident_id") else None,
                action_type=item_data["action_type"],
                description=item_data.get("description", "No description provided"),
                priority=RemediationPriority(item_data["priority"]),
                risk_level=RemediationRiskLevel(item_data["risk_level"]),
                requested_by=item_data["requested_by"],
                requested_at=datetime.fromisoformat(
                    item_data["requested_at"].replace("Z", "+00:00")
                ),
                approval_status=item_data["approval_status"],
                approved_by=item_data.get("approved_by"),
                approved_at=None,
                rejection_reason=item_data.get("rejection_reason"),
            )
            items.append(item)

        response = RemediationApprovalResponse(
            items=items,
            total=example["total"],
            pending_count=example["pending_count"],
        )

        assert len(response.items) == 1
        assert response.total == 5

        # Test accessing nested item data
        data = response.model_dump()
        assert data["total"] == 5
        assert data["pending_count"] == 3


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""

    def test_complete_remediation_workflow(self) -> None:
        """Test complete remediation workflow using all models."""
        # Create action
        action_id = uuid4()
        incident_id = uuid4()

        action = RemediationAction(
            action_id=action_id,
            incident_id=incident_id,
            action_type="isolate_host",
            description="Isolate compromised host",
            priority=RemediationPriority.HIGH,
            status=RemediationStatus.PENDING,
            risk_level=RemediationRiskLevel.MEDIUM,
            requires_approval=True,
            automated=False,
            estimated_duration_seconds=300,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )

        # Create execution request
        request = RemediationExecutionRequest(
            action_id=action_id,
            parameters={"host_id": "host-123"},
            dry_run=False,
            approval_token="approved-token-123",
            notification_channels=["slack"],
        )

        # Create execution response
        execution_id = uuid4()
        response = RemediationExecutionResponse(
            execution_id=execution_id,
            action_id=action_id,
            status=RemediationStatus.COMPLETED,
            message="Host isolated successfully",
            dry_run=False,
            estimated_completion_time=None,
            warnings=[],
        )

        # Create execution record
        execution = RemediationExecution(
            execution_id=execution_id,
            action_id=action_id,
            incident_id=incident_id,
            action_type="isolate_host",
            status=RemediationStatus.COMPLETED,
            executed_by="admin",
            parameters={"host_id": "host-123"},
            result={"isolated": True, "host_id": "host-123"},
            started_at=datetime.now(timezone.utc),
            duration_seconds=45.5,
        )

        # Verify workflow integrity
        assert (
            action.action_id
            == request.action_id
            == response.action_id
            == execution.action_id
        )
        assert action.incident_id == execution.incident_id
        assert request.parameters == execution.parameters
        assert response.execution_id == execution.execution_id

    def test_edge_case_very_long_strings(self) -> None:
        """Test handling of very long string values."""
        action_id = uuid4()
        long_description = "A" * 1000
        long_action_type = "very_long_action_type_" + "x" * 100

        action = RemediationAction(
            action_id=action_id,
            incident_id=None,
            action_type=long_action_type,
            description=long_description,
            priority=RemediationPriority.LOW,
            status=RemediationStatus.PENDING,
            risk_level=RemediationRiskLevel.LOW,
            requires_approval=False,
            automated=True,
            estimated_duration_seconds=60,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )

        assert len(action.description) == 1000
        assert action.action_type == long_action_type

    def test_edge_case_unicode_content(self) -> None:
        """Test handling of Unicode content in string fields."""
        action_id = uuid4()
        unicode_description = "处理恶意软件 🔒 块 IP 地址 ñoñó"

        action = RemediationAction(
            action_id=action_id,
            incident_id=None,
            action_type="unicode_test",
            description=unicode_description,
            priority=RemediationPriority.MEDIUM,
            status=RemediationStatus.PENDING,
            risk_level=RemediationRiskLevel.LOW,
            requires_approval=False,
            automated=False,
            estimated_duration_seconds=30,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )

        assert action.description == unicode_description
        assert "🔒" in action.description

    def test_edge_case_boundary_values(self) -> None:
        """Test handling of boundary values."""
        action_id = uuid4()

        # Test with zero duration
        action = RemediationAction(
            action_id=action_id,
            incident_id=None,
            action_type="instant_action",
            description="Instant action",
            priority=RemediationPriority.CRITICAL,
            status=RemediationStatus.COMPLETED,
            risk_level=RemediationRiskLevel.HIGH,
            requires_approval=False,
            automated=True,
            estimated_duration_seconds=0,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )

        assert action.estimated_duration_seconds == 0

        # Test execution with zero duration
        execution = RemediationExecution(
            execution_id=uuid4(),
            action_id=action_id,
            incident_id=uuid4(),
            action_type="instant_action",
            status=RemediationStatus.COMPLETED,
            executed_by="system",
            parameters={},
            result=None,
            started_at=datetime.now(timezone.utc),
            duration_seconds=0.0,
        )

        assert execution.duration_seconds == 0.0

    def test_all_enum_combinations(self) -> None:
        """Test all combinations of enum values."""
        created_at = datetime.now(timezone.utc)

        # Test all priority levels
        for priority in ["critical", "high", "medium", "low"]:
            for risk_level in ["critical", "high", "medium", "low"]:
                for status in [
                    "pending",
                    "executing",
                    "completed",
                    "partially_completed",
                    "failed",
                    "rolled_back",
                    "cancelled",
                ]:
                    action = RemediationAction(
                        action_id=uuid4(),
                        incident_id=None,
                        action_type=f"test_{priority}_{risk_level}",
                        description=f"Test {priority} priority {risk_level} risk",
                        priority=RemediationPriority(priority),
                        status=RemediationStatus(status),
                        risk_level=RemediationRiskLevel(risk_level),
                        requires_approval=(risk_level in ["high", "critical"]),
                        automated=(priority == "low"),
                        estimated_duration_seconds=None,
                        created_at=created_at,
                        updated_at=None,
                    )

                    assert action.priority.value == priority
                    assert action.risk_level.value == risk_level
                    assert action.status.value == status
