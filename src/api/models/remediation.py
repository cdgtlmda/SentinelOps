"""
Pydantic models for remediation API endpoints."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.common.models import RemediationPriority, RemediationStatus


class RemediationRiskLevel(str, Enum):
    """Risk level for remediation actions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RemediationAction(BaseModel):
    """Model for a remediation action."""

    action_id: UUID
    incident_id: Optional[UUID]
    action_type: str
    description: str
    priority: RemediationPriority
    status: RemediationStatus
    risk_level: RemediationRiskLevel
    requires_approval: bool
    automated: bool
    estimated_duration_seconds: Optional[int]
    prerequisites: List[str] = Field(default_factory=list)
    parameters_schema: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime]

    @classmethod
    def from_storage_model(cls, model: Any) -> "RemediationAction":
        """Create from storage model."""
        return cls(
            action_id=UUID(model.id),
            incident_id=UUID(model.incident_id) if model.incident_id else None,
            action_type=model.action_type,
            description=model.description,
            priority=model.priority,
            status=model.status,
            risk_level=model.risk_level,
            requires_approval=model.requires_approval,
            automated=model.automated,
            estimated_duration_seconds=model.estimated_duration_seconds,
            prerequisites=model.prerequisites or [],
            parameters_schema=model.parameters_schema,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    class Config:
        schema_extra = {
            "example": {
                "action_id": "550e8400-e29b-41d4-a716-446655440000",
                "incident_id": "660e8400-e29b-41d4-a716-446655440001",
                "action_type": "block_ip_addresses",
                "description": "Block malicious IP addresses at firewall",
                "priority": "high",
                "status": "pending",
                "risk_level": "medium",
                "requires_approval": True,
                "automated": False,
                "estimated_duration_seconds": 30,
                "prerequisites": ["firewall_access", "network_admin_role"],
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "ip_addresses": {"type": "array", "items": {"type": "string"}},
                        "duration_hours": {"type": "integer", "minimum": 1},
                    },
                },
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:35:00Z",
            }
        }


class RemediationExecutionRequest(BaseModel):
    """Request model for executing a remediation action."""

    action_id: UUID
    parameters: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = Field(
        False, description="Simulate execution without making changes"
    )
    approval_token: Optional[str] = Field(
        None, description="Approval token if action requires approval"
    )
    notification_channels: List[str] = Field(
        default_factory=list, description="Channels to notify about execution"
    )

    class Config:
        schema_extra = {
            "example": {
                "action_id": "550e8400-e29b-41d4-a716-446655440000",
                "parameters": {
                    "ip_addresses": ["192.168.1.100", "10.0.0.50"],
                    "duration_hours": 24,
                },
                "dry_run": False,
                "approval_token": "appr_abc123xyz",
                "notification_channels": ["slack", "email"],
            }
        }


class RemediationExecutionResponse(BaseModel):
    """Response model for remediation execution."""

    execution_id: UUID
    action_id: UUID
    status: RemediationStatus
    message: str
    dry_run: bool
    estimated_completion_time: Optional[datetime] = None
    warnings: List[str] = Field(default_factory=list)

    class Config:
        schema_extra = {
            "example": {
                "execution_id": "770e8400-e29b-41d4-a716-446655440000",
                "action_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "executing",
                "message": "Remediation action started successfully",
                "dry_run": False,
                "estimated_completion_time": "2024-01-15T10:40:00Z",
                "warnings": ["Some IP addresses may affect legitimate users"],
            }
        }


class RemediationExecution(BaseModel):
    """Model for a remediation execution record."""

    execution_id: UUID
    action_id: UUID
    incident_id: Optional[UUID]
    action_type: str
    status: RemediationStatus
    executed_by: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    class Config:
        schema_extra = {
            "example": {
                "execution_id": "770e8400-e29b-41d4-a716-446655440000",
                "action_id": "550e8400-e29b-41d4-a716-446655440000",
                "incident_id": "660e8400-e29b-41d4-a716-446655440001",
                "action_type": "block_ip_addresses",
                "status": "completed",
                "executed_by": "security-analyst@company.com",
                "parameters": {"ip_addresses": ["192.168.1.100"], "duration_hours": 24},
                "result": {
                    "blocked_count": 1,
                    "firewall_rules_created": ["rule-123"],
                },
                "started_at": "2024-01-15T10:35:00Z",
                "completed_at": "2024-01-15T10:35:30Z",
                "duration_seconds": 30.5,
            }
        }


class RemediationHistoryResponse(BaseModel):
    """Response model for remediation history."""

    executions: List[RemediationExecution]
    total: int
    page: int
    page_size: int
    has_next: bool

    class Config:
        schema_extra = {
            "example": {
                "executions": [
                    {
                        "execution_id": "770e8400-e29b-41d4-a716-446655440000",
                        "action_id": "550e8400-e29b-41d4-a716-446655440000",
                        "action_type": "block_ip_addresses",
                        "status": "completed",
                        "executed_by": "security-analyst@company.com",
                        "started_at": "2024-01-15T10:35:00Z",
                        "completed_at": "2024-01-15T10:35:30Z",
                        "duration_seconds": 30.5,
                    }
                ],
                "total": 50,
                "page": 1,
                "page_size": 20,
                "has_next": True,
            }
        }


class RemediationRollbackRequest(BaseModel):
    """Request model for rolling back a remediation."""

    execution_id: UUID
    reason: str = Field(..., max_length=500)
    force: bool = Field(
        False, description="Force rollback even if some operations may fail"
    )

    class Config:
        schema_extra = {
            "example": {
                "execution_id": "770e8400-e29b-41d4-a716-446655440000",
                "reason": "False positive - blocked legitimate traffic",
                "force": False,
            }
        }


class RemediationApprovalItem(BaseModel):
    """Model for a remediation action pending approval."""

    approval_id: UUID
    action_id: UUID
    incident_id: Optional[UUID]
    action_type: str
    description: str
    priority: RemediationPriority
    risk_level: RemediationRiskLevel
    requested_by: str
    requested_at: datetime
    approval_status: str  # pending, approved, rejected
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "approval_id": "990e8400-e29b-41d4-a716-446655440000",
                "action_id": "550e8400-e29b-41d4-a716-446655440000",
                "incident_id": "660e8400-e29b-41d4-a716-446655440001",
                "action_type": "delete_user_data",
                "description": "Delete compromised user data from database",
                "priority": "critical",
                "risk_level": "high",
                "requested_by": "automated-system",
                "requested_at": "2024-01-15T10:30:00Z",
                "approval_status": "pending",
            }
        }


class RemediationApprovalResponse(BaseModel):
    """Response model for approval queue."""

    items: List[RemediationApprovalItem]
    total: int
    pending_count: int

    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "approval_id": "990e8400-e29b-41d4-a716-446655440000",
                        "action_id": "550e8400-e29b-41d4-a716-446655440000",
                        "action_type": "delete_user_data",
                        "priority": "critical",
                        "risk_level": "high",
                        "requested_by": "automated-system",
                        "requested_at": "2024-01-15T10:30:00Z",
                        "approval_status": "pending",
                    }
                ],
                "total": 5,
                "pending_count": 3,
            }
        }
