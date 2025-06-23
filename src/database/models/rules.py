"""
Database model for detection rules.
"""

from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from src.api.models.rules import RuleSeverity, RuleStatus, RuleType
from src.database.base import Base


class RuleModel(Base):  # type: ignore[misc]
    """SQLAlchemy model for detection rules."""

    __tablename__ = "rules"

    # Primary key
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Basic information
    rule_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Rule classification
    rule_type: Column[RuleType] = Column(Enum(RuleType), nullable=False, index=True)
    severity: Column[RuleSeverity] = Column(
        Enum(RuleSeverity), nullable=False, index=True
    )
    status: Column[RuleStatus] = Column(
        Enum(RuleStatus), nullable=False, default=RuleStatus.ACTIVE, index=True
    )

    # Rule logic (stored as JSON for flexibility)
    query = Column(Text, nullable=True)  # For query-based rules
    conditions = Column(JSON, nullable=True)  # For pattern rules
    threshold = Column(JSON, nullable=True)  # For threshold rules
    correlation = Column(JSON, nullable=True)  # For correlation rules

    # Configuration
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    tags = Column(JSON, nullable=False, default=list)
    references = Column(JSON, nullable=False, default=list)
    false_positive_rate = Column(Float, nullable=True)

    # Actions
    actions = Column(JSON, nullable=False, default=list)

    # Metadata
    custom_fields = Column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now,
        onupdate=func.now,
    )
    last_executed = Column(DateTime(timezone=True), nullable=True)

    # User tracking
    created_by = Column(String(255), nullable=False)
    updated_by = Column(String(255), nullable=False)

    # Versioning
    version = Column(Integer, nullable=False, default=1)

    # Performance metrics (stored as JSON)
    metrics = Column(
        JSON,
        nullable=False,
        default={
            "total_executions": 0,
            "total_matches": 0,
            "true_positives": 0,
            "false_positives": 0,
            "avg_execution_time_ms": 0.0,
            "last_match": None,
            "match_rate": 0.0,
            "precision": 0.0,
        },
    )

    # Relationships
    parent_rule_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("rules.id"), nullable=True
    )
    related_rules = Column(
        JSON, nullable=False, default=list
    )  # Store UUIDs as JSON array

    # Indexes for better query performance
    __table_args__ = (
        Index("idx_rules_name", "name"),
        Index("idx_rules_created_at", "created_at"),
        Index("idx_rules_updated_at", "updated_at"),
        Index("idx_rules_enabled_status", "enabled", "status"),
        Index("idx_rules_type_severity", "rule_type", "severity"),
        UniqueConstraint("rule_number", name="uq_rules_rule_number"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "rule_number": self.rule_number,
            "name": self.name,
            "description": self.description,
            "rule_type": self.rule_type.value if self.rule_type else None,
            "severity": self.severity.value if self.severity else None,
            "status": self.status.value if self.status else None,
            "query": self.query,
            "conditions": self.conditions,
            "threshold": self.threshold,
            "correlation": self.correlation,
            "enabled": self.enabled,
            "tags": self.tags,
            "references": self.references,
            "false_positive_rate": self.false_positive_rate,
            "actions": self.actions,
            "custom_fields": self.custom_fields,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_executed": (
                self.last_executed.isoformat() if self.last_executed else None
            ),
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "version": self.version,
            "metrics": self.metrics,
            "parent_rule_id": str(self.parent_rule_id) if self.parent_rule_id else None,
            "related_rules": self.related_rules,
        }
