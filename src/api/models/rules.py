"""
Detection rule data models for SentinelOps API.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RuleStatus(str, Enum):
    """Rule status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"


class RuleType(str, Enum):
    """Rule type enumeration."""

    QUERY = "query"  # SQL/BigQuery based
    PATTERN = "pattern"  # Pattern matching
    THRESHOLD = "threshold"  # Threshold based
    ANOMALY = "anomaly"  # Anomaly detection
    CORRELATION = "correlation"  # Multi-event correlation
    CUSTOM = "custom"  # Custom logic


class RuleSeverity(str, Enum):
    """Rule severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RuleCondition(BaseModel):
    """Condition for rule evaluation."""

    field: str = Field(..., description="Field to evaluate")
    operator: str = Field(
        ...,
        description="Comparison operator (eq, ne, gt, lt, gte, lte, in, contains, regex)",
    )
    value: Any = Field(..., description="Value to compare against")
    case_sensitive: bool = Field(False, description="Case sensitive comparison")

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: str) -> str:
        """Validate operator is supported."""
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
        if v not in valid_operators:
            raise ValueError(f"Invalid operator: {v}. Must be one of {valid_operators}")
        return v


class RuleThreshold(BaseModel):
    """Threshold configuration for rules."""

    count: int = Field(..., ge=1, description="Number of events")
    window_seconds: int = Field(..., ge=1, description="Time window in seconds")
    group_by: Optional[List[str]] = Field(None, description="Fields to group by")


class RuleCorrelation(BaseModel):
    """Correlation configuration for multi-event rules."""

    events: List[Dict[str, Any]] = Field(
        ..., min_length=2, description="Events to correlate"
    )
    window_seconds: int = Field(..., ge=1, description="Correlation window in seconds")
    join_fields: List[str] = Field(..., description="Fields to join events on")
    sequence_required: bool = Field(False, description="Whether event sequence matters")


class RuleAction(BaseModel):
    """Action to take when rule triggers."""

    type: str = Field(
        ..., description="Action type (alert, block, isolate, notify, custom)"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Action parameters"
    )
    automated: bool = Field(False, description="Whether to execute automatically")
    requires_approval: bool = Field(
        True, description="Whether action requires approval"
    )


class RuleBase(BaseModel):
    """Base rule model with common fields."""

    name: str = Field(..., min_length=1, max_length=200, description="Rule name")
    description: str = Field(..., min_length=1, description="Rule description")
    rule_type: RuleType = Field(..., description="Type of rule")
    severity: RuleSeverity = Field(..., description="Rule severity")

    # Rule logic
    query: Optional[str] = Field(None, description="Query for query-based rules")
    conditions: Optional[List[RuleCondition]] = Field(
        None, description="Conditions for pattern rules"
    )
    threshold: Optional[RuleThreshold] = Field(
        None, description="Threshold configuration"
    )
    correlation: Optional[RuleCorrelation] = Field(
        None, description="Correlation configuration"
    )

    # Configuration
    enabled: bool = Field(True, description="Whether rule is enabled")
    tags: List[str] = Field(default_factory=list, description="Rule tags")
    references: List[str] = Field(
        default_factory=list, description="External references (MITRE ATT&CK, etc.)"
    )
    false_positive_rate: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Estimated false positive rate"
    )

    # Actions
    actions: List[RuleAction] = Field(
        default_factory=list, description="Actions to take when triggered"
    )

    # Metadata
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Custom fields"
    )


class RuleCreate(RuleBase):
    """Model for creating a new rule."""

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tags are unique and lowercase."""
        return list(set(tag.lower().strip() for tag in v if tag.strip()))

    @model_validator(mode='after')
    def validate_rule_type_requirements(self) -> 'RuleCreate':
        """Validate rule type specific requirements."""
        if self.rule_type == RuleType.QUERY and not self.query:
            raise ValueError("Query is required for query-based rules")
        if self.rule_type == RuleType.PATTERN and not self.conditions:
            raise ValueError("Conditions are required for pattern rules")
        return self


class RuleUpdate(BaseModel):
    """Model for updating a rule."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    severity: Optional[RuleSeverity] = None
    query: Optional[str] = None
    conditions: Optional[List[RuleCondition]] = None
    threshold: Optional[RuleThreshold] = None
    correlation: Optional[RuleCorrelation] = None
    enabled: Optional[bool] = None
    tags: Optional[List[str]] = None
    references: Optional[List[str]] = None
    false_positive_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    actions: Optional[List[RuleAction]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class RuleTestRequest(BaseModel):
    """Request to test a rule."""

    time_range_minutes: int = Field(
        60, ge=1, le=1440, description="Time range to test against"
    )
    dry_run: bool = Field(True, description="Whether to run in dry-run mode")
    sample_size: Optional[int] = Field(
        None, ge=1, le=1000, description="Maximum samples to return"
    )


class RuleTestResult(BaseModel):
    """Result of rule testing."""

    matches: int = Field(..., description="Number of matches found")
    samples: List[Dict[str, Any]] = Field(..., description="Sample matches")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    estimated_false_positive_rate: float = Field(
        ..., description="Estimated false positive rate"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Any warnings from testing"
    )


class RuleMetrics(BaseModel):
    """Rule performance metrics."""

    total_executions: int = Field(0, description="Total rule executions")
    total_matches: int = Field(0, description="Total matches")
    true_positives: int = Field(0, description="Confirmed true positives")
    false_positives: int = Field(0, description="Confirmed false positives")
    avg_execution_time_ms: float = Field(0.0, description="Average execution time")
    last_match: Optional[datetime] = Field(None, description="Last match timestamp")
    match_rate: float = Field(0.0, description="Match rate (matches/executions)")
    precision: float = Field(0.0, description="Precision (TP/(TP+FP))")


class Rule(RuleBase):
    """Complete rule model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Unique rule ID")
    rule_number: str = Field(..., description="Human-readable rule number")
    status: RuleStatus = Field(..., description="Rule status")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_executed: Optional[datetime] = Field(
        None, description="Last execution timestamp"
    )

    # Metadata
    created_by: str = Field(..., description="User who created the rule")
    updated_by: str = Field(..., description="User who last updated the rule")
    version: int = Field(1, description="Rule version")

    # Performance
    metrics: RuleMetrics = Field(
        default_factory=lambda: RuleMetrics(
            total_executions=0,
            total_matches=0,
            true_positives=0,
            false_positives=0,
            avg_execution_time_ms=0.0,
            last_match=None,
            match_rate=0.0,
            precision=0.0
        ),
        description="Rule performance metrics"
    )

    # Related rules
    parent_rule: Optional[UUID] = Field(
        None, description="Parent rule ID (for rule variants)"
    )
    related_rules: List[UUID] = Field(
        default_factory=list, description="Related rule IDs"
    )


class RuleListResponse(BaseModel):
    """Response model for rule list."""

    rules: List[Rule] = Field(..., description="List of rules")
    total: int = Field(..., description="Total number of rules")
    page: int = Field(1, ge=1, description="Current page")
    page_size: int = Field(20, ge=1, le=100, description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")


class RuleStats(BaseModel):
    """Rule statistics model."""

    total_rules: int = Field(..., description="Total number of rules")
    active_rules: int = Field(..., description="Number of active rules")

    by_status: Dict[str, int] = Field(..., description="Count by status")
    by_type: Dict[str, int] = Field(..., description="Count by rule type")
    by_severity: Dict[str, int] = Field(..., description="Count by severity")

    total_matches_24h: int = Field(..., description="Total matches in last 24 hours")
    top_matching_rules: List[Dict[str, Any]] = Field(
        ..., description="Top matching rules"
    )
    avg_execution_time: float = Field(..., description="Average execution time (ms)")
    false_positive_rate: float = Field(..., description="Overall false positive rate")
