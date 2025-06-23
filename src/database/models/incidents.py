"""
Database model for incidents.
"""

from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from src.api.models.incidents import (
    IncidentSeverity,
    IncidentStatus,
    Priority,
    SecurityIncidentType,
)
from src.database.base import Base


class IncidentModel(Base):  # type: ignore[misc]
    """SQLAlchemy model for incidents."""

    __tablename__ = "incidents"

    # Primary key
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Basic information
    incident_number = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Classification
    incident_type = Column(
        Enum(SecurityIncidentType), nullable=False, index=True
    )  # type: ignore[var-annotated]
    severity = Column(
        Enum(IncidentSeverity), nullable=False, index=True
    )  # type: ignore[var-annotated]
    priority = Column(
        Enum(Priority), nullable=False, default=Priority.MEDIUM, index=True
    )  # type: ignore[var-annotated]
    status = Column(
        Enum(IncidentStatus), nullable=False, default=IncidentStatus.OPEN, index=True
    )  # type: ignore[var-annotated]

    # External reference
    external_id = Column(String(255), nullable=True, index=True)

    # Tags and custom fields
    tags = Column(JSON, nullable=False, default=list)
    custom_fields = Column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now,
        onupdate=func.now,
    )
    detected_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Nested data structures (stored as JSON)
    source = Column(JSON, nullable=False)  # IncidentSource
    actors = Column(JSON, nullable=False, default=list)  # List[IncidentActor]
    assets = Column(JSON, nullable=False, default=list)  # List[IncidentAsset]
    timeline = Column(JSON, nullable=False, default=list)  # List[IncidentTimeline]
    analysis = Column(JSON, nullable=True)  # Optional[IncidentAnalysis]
    remediation_actions = Column(
        JSON, nullable=False, default=list
    )  # List[IncidentRemediation]

    # User tracking
    created_by = Column(String(255), nullable=False)
    updated_by = Column(String(255), nullable=False)
    assigned_to = Column(String(255), nullable=True, index=True)

    # Metrics
    time_to_detect = Column(Float, nullable=True)  # in seconds
    time_to_respond = Column(Float, nullable=True)  # in seconds
    time_to_resolve = Column(Float, nullable=True)  # in seconds

    # Relationships
    parent_incident_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True
    )
    related_incidents = Column(
        JSON, nullable=False, default=list
    )  # Store UUIDs as JSON array

    # Indexes for better query performance
    __table_args__ = (
        Index("idx_incidents_title", "title"),
        Index("idx_incidents_created_at", "created_at"),
        Index("idx_incidents_updated_at", "updated_at"),
        Index("idx_incidents_detected_at", "detected_at"),
        Index("idx_incidents_status_severity", "status", "severity"),
        Index("idx_incidents_type_priority", "incident_type", "priority"),
        Index("idx_incidents_assigned_status", "assigned_to", "status"),
        UniqueConstraint("incident_number", name="uq_incidents_incident_number"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "incident_number": self.incident_number,
            "title": self.title,
            "description": self.description,
            "incident_type": self.incident_type.value if self.incident_type else None,
            "severity": self.severity.value if self.severity else None,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "external_id": self.external_id,
            "tags": self.tags,
            "custom_fields": self.custom_fields,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "source": self.source,
            "actors": self.actors,
            "assets": self.assets,
            "timeline": self.timeline,
            "analysis": self.analysis,
            "remediation_actions": self.remediation_actions,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "assigned_to": self.assigned_to,
            "time_to_detect": self.time_to_detect,
            "time_to_respond": self.time_to_respond,
            "time_to_resolve": self.time_to_resolve,
            "parent_incident_id": (
                str(self.parent_incident_id) if self.parent_incident_id else None
            ),
            "related_incidents": self.related_incidents,
        }
