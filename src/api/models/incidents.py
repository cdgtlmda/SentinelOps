"""
Incident data models for SentinelOps API.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# from ...agents.common.message_types import Priority, SecurityIncidentType


class Priority(str, Enum):
    """Priority levels for incidents."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityIncidentType(str, Enum):
    """Types of security incidents."""
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH = "data_breach"
    MALWARE = "malware"
    DOS_ATTACK = "dos_attack"
    POLICY_VIOLATION = "policy_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    OTHER = "other"


class IncidentStatus(str, Enum):
    """Incident status enumeration."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    REMEDIATED = "remediated"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"


class IncidentSeverity(str, Enum):
    """Incident severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IncidentSource(BaseModel):
    """Source of an incident detection."""

    system: str = Field(..., description="System that detected the incident")
    rule_id: Optional[str] = Field(None, description="Detection rule ID")
    rule_name: Optional[str] = Field(None, description="Detection rule name")
    confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Detection confidence score"
    )
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw detection data")


class IncidentActor(BaseModel):
    """Actor involved in an incident."""

    type: str = Field(..., description="Actor type (user, service, ip, etc.)")
    identifier: str = Field(..., description="Actor identifier")
    name: Optional[str] = Field(None, description="Actor display name")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Additional attributes"
    )


class IncidentAsset(BaseModel):
    """Asset affected by an incident."""

    type: str = Field(..., description="Asset type (server, database, file, etc.)")
    identifier: str = Field(..., description="Asset identifier")
    name: Optional[str] = Field(None, description="Asset display name")
    criticality: Optional[str] = Field(None, description="Asset criticality level")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Additional attributes"
    )


class IncidentTimeline(BaseModel):
    """Timeline entry for an incident."""

    timestamp: datetime = Field(..., description="Event timestamp")
    event_type: str = Field(..., description="Type of event")
    description: str = Field(..., description="Event description")
    actor: Optional[str] = Field(None, description="Who performed the action")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional event details"
    )


class IncidentAnalysis(BaseModel):
    """Analysis results for an incident."""

    summary: str = Field(..., description="Analysis summary")
    risk_score: float = Field(0.0, ge=0.0, le=100.0, description="Risk score (0-100)")
    attack_patterns: List[str] = Field(
        default_factory=list, description="Detected attack patterns"
    )
    indicators: List[Dict[str, Any]] = Field(
        default_factory=list, description="Indicators of compromise"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Recommended actions"
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Analysis confidence")
    ai_insights: Optional[str] = Field(None, description="AI-generated insights")


class IncidentRemediation(BaseModel):
    """Remediation action for an incident."""

    action_id: str = Field(..., description="Unique action ID")
    action_type: str = Field(..., description="Type of remediation action")
    description: str = Field(..., description="Action description")
    status: str = Field("pending", description="Action status")
    automated: bool = Field(False, description="Whether action was automated")
    executed_at: Optional[datetime] = Field(None, description="Execution timestamp")
    executed_by: Optional[str] = Field(None, description="Who executed the action")
    result: Optional[Dict[str, Any]] = Field(None, description="Action result")
    rollback_available: bool = Field(False, description="Whether rollback is available")


class IncidentBase(BaseModel):
    """Base incident model with common fields."""

    title: str = Field(..., min_length=1, max_length=200, description="Incident title")
    description: str = Field(..., min_length=1, description="Detailed description")
    incident_type: SecurityIncidentType = Field(
        ..., description="Type of security incident"
    )
    severity: IncidentSeverity = Field(..., description="Incident severity")
    priority: Priority = Field(Priority.MEDIUM, description="Incident priority")
    status: IncidentStatus = Field(IncidentStatus.OPEN, description="Current status")

    # Optional fields
    external_id: Optional[str] = Field(None, description="External system ID")
    tags: List[str] = Field(default_factory=list, description="Incident tags")
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Custom fields"
    )


class IncidentCreate(IncidentBase):
    """Model for creating a new incident."""

    source: IncidentSource = Field(..., description="Incident source")
    actors: List[IncidentActor] = Field(
        default_factory=list, description="Involved actors"
    )
    assets: List[IncidentAsset] = Field(
        default_factory=list, description="Affected assets"
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags are unique and lowercase."""
        if v is None:
            return None
        return list(set(tag.lower().strip() for tag in v if tag.strip()))


class IncidentUpdate(BaseModel):
    """Model for updating an incident."""

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    severity: Optional[IncidentSeverity] = None
    priority: Optional[Priority] = None
    status: Optional[IncidentStatus] = None
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags if provided."""
        if v is not None:
            return list(set(tag.lower().strip() for tag in v if tag.strip()))
        return v


class Incident(IncidentBase):
    """Complete incident model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Unique incident ID")
    incident_number: str = Field(..., description="Human-readable incident number")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    detected_at: datetime = Field(..., description="Detection timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")

    # Relationships
    source: IncidentSource = Field(..., description="Incident source")
    actors: List[IncidentActor] = Field(
        default_factory=list, description="Involved actors"
    )
    assets: List[IncidentAsset] = Field(
        default_factory=list, description="Affected assets"
    )
    timeline: List[IncidentTimeline] = Field(
        default_factory=list, description="Event timeline"
    )
    analysis: Optional[IncidentAnalysis] = Field(None, description="Analysis results")
    remediation_actions: List[IncidentRemediation] = Field(
        default_factory=list, description="Remediation actions"
    )

    # Metadata
    created_by: str = Field(..., description="User who created the incident")
    updated_by: str = Field(..., description="User who last updated the incident")
    assigned_to: Optional[str] = Field(None, description="Assigned user/team")

    # Metrics
    time_to_detect: Optional[float] = Field(
        None, description="Time to detect in seconds"
    )
    time_to_respond: Optional[float] = Field(
        None, description="Time to respond in seconds"
    )
    time_to_resolve: Optional[float] = Field(
        None, description="Time to resolve in seconds"
    )

    # Related incidents
    related_incidents: List[UUID] = Field(
        default_factory=list, description="Related incident IDs"
    )
    parent_incident: Optional[UUID] = Field(None, description="Parent incident ID")


class IncidentListResponse(BaseModel):
    """Response model for incident list."""

    incidents: List[Incident] = Field(..., description="List of incidents")
    total: int = Field(..., description="Total number of incidents")
    page: int = Field(1, ge=1, description="Current page")
    page_size: int = Field(20, ge=1, le=100, description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")


class IncidentFilters(BaseModel):
    """Filters for querying incidents."""

    status: Optional[List[IncidentStatus]] = Field(None, description="Filter by status")
    severity: Optional[List[IncidentSeverity]] = Field(
        None, description="Filter by severity"
    )
    incident_type: Optional[List[SecurityIncidentType]] = Field(
        None, description="Filter by type"
    )
    assigned_to: Optional[str] = Field(None, description="Filter by assignee")
    created_after: Optional[datetime] = Field(
        None, description="Filter by creation date"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter by creation date"
    )
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    search: Optional[str] = Field(None, description="Search in title and description")


class IncidentStats(BaseModel):
    """Incident statistics model."""

    total_incidents: int = Field(..., description="Total number of incidents")
    open_incidents: int = Field(..., description="Number of open incidents")

    by_status: Dict[str, int] = Field(..., description="Count by status")
    by_severity: Dict[str, int] = Field(..., description="Count by severity")
    by_type: Dict[str, int] = Field(..., description="Count by incident type")

    avg_time_to_detect: float = Field(
        ..., description="Average time to detect (seconds)"
    )
    avg_time_to_respond: float = Field(
        ..., description="Average time to respond (seconds)"
    )
    avg_time_to_resolve: float = Field(
        ..., description="Average time to resolve (seconds)"
    )

    trend_daily: List[Dict[str, Any]] = Field(..., description="Daily incident trend")
    top_actors: List[Dict[str, Any]] = Field(..., description="Top actors involved")
    top_assets: List[Dict[str, Any]] = Field(..., description="Top affected assets")
