"""Pydantic models for analysis API endpoints."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.common.models import (
    AnalysisResult,
    RemediationPriority,
    SecurityEvent,
    SeverityLevel,
)


class AnalysisStatus(str, Enum):
    """Status of an analysis."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisRecommendation(BaseModel):
    """Extended recommendation model for API responses."""

    id: str
    action: str
    description: str
    priority: RemediationPriority
    estimated_impact: str
    resources_required: List[str]
    severity: SeverityLevel
    attack_techniques: List[str] = Field(default_factory=list)

    class Config:
        schema_extra = {
            "example": {
                "id": "rec-123",
                "action": "Block suspicious IP addresses",
                "description": "Implement firewall rules to block identified malicious IPs",
                "priority": "high",
                "estimated_impact": "High reduction in attack surface",
                "resources_required": ["firewall-admin", "network-team"],
                "severity": "high",
                "attack_techniques": ["T1190", "T1133"],
            }
        }


# Type alias for backward compatibility
Recommendation = AnalysisRecommendation


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""

    analysis_id: UUID
    incident_id: Optional[UUID]
    status: AnalysisStatus
    severity: SeverityLevel
    confidence_score: float = Field(ge=0.0, le=1.0)
    summary: str
    recommendations: List[Recommendation]
    attack_techniques: List[str]
    iocs: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]
    analysis_duration_seconds: Optional[float]

    @classmethod
    def from_analysis_result(
        cls, result: AnalysisResult, incident_id: Optional[UUID] = None
    ) -> "AnalysisResponse":
        """Create AnalysisResponse from AnalysisResult."""
        # Extract IOCs and timeline from evidence dict
        evidence = result.evidence if hasattr(result, "evidence") else {}
        iocs = (
            evidence.get("iocs", [])
            if "evidence" in evidence
            else evidence.get("iocs", [])
        )
        timeline = (
            evidence.get("timeline", [])
            if "evidence" in evidence
            else evidence.get("timeline", [])
        )

        # Convert string recommendations to AnalysisRecommendation objects
        recommendations = []
        for i, rec_str in enumerate(result.recommendations):
            recommendations.append(
                AnalysisRecommendation(
                    id=f"rec-{i + 1}",
                    action=rec_str,
                    description=rec_str,
                    priority=RemediationPriority.MEDIUM,
                    estimated_impact="To be determined",
                    resources_required=[],
                    severity=SeverityLevel.MEDIUM,
                    attack_techniques=result.attack_techniques,
                )
            )

        return cls(
            analysis_id=(
                UUID(result.analysis_id)
                if hasattr(result, "analysis_id")
                else UUID(int=0)
            ),
            incident_id=incident_id,
            status=AnalysisStatus.COMPLETED,
            # Default severity since AnalysisResult doesn't have severity
            severity=SeverityLevel.MEDIUM,
            confidence_score=result.confidence_score,
            summary=result.summary,
            recommendations=recommendations,
            attack_techniques=result.attack_techniques,
            iocs=iocs,
            timeline=timeline,
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            analysis_duration_seconds=None,
        )

    class Config:
        schema_extra = {
            "example": {
                "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                "incident_id": "660e8400-e29b-41d4-a716-446655440001",
                "status": "completed",
                "severity": "high",
                "confidence_score": 0.85,
                "summary": "Detected potential data exfiltration attempt via DNS tunneling",
                "recommendations": [
                    {
                        "action": "Block suspicious domains",
                        "description": "Add identified domains to DNS blocklist",
                        "priority": "high",
                        "estimated_impact": "Prevent data exfiltration",
                        "resources_required": ["dns-admin"],
                    }
                ],
                "attack_techniques": ["T1048", "T1071.004"],
                "iocs": [
                    {"type": "domain", "value": "evil.example.com", "confidence": 0.9}
                ],
                "timeline": [
                    {
                        "timestamp": "2024-01-15T10:30:00Z",
                        "event": "Initial DNS query detected",
                    }
                ],
                "created_at": "2024-01-15T10:35:00Z",
                "completed_at": "2024-01-15T10:36:30Z",
                "analysis_duration_seconds": 90.5,
            }
        }


class ManualAnalysisRequest(BaseModel):
    """Request model for manual analysis."""

    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    severity: SeverityLevel
    events: List[SecurityEvent]
    metadata: Optional[Dict[str, Any]] = None
    create_incident: bool = Field(
        False, description="Whether to create a new incident from this analysis"
    )

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not v:
            raise ValueError("At least one event must be provided")
        if len(v) > 1000:
            raise ValueError("Cannot analyze more than 1000 events at once")
        return v

    class Config:
        schema_extra = {
            "example": {
                "title": "Suspicious login activity",
                "description": "Multiple failed login attempts from unusual locations",
                "severity": "medium",
                "events": [
                    {
                        "id": "evt-001",
                        "timestamp": "2024-01-15T10:00:00Z",
                        "source": "auth-system",
                        "type": "authentication_failure",
                        "data": {
                            "username": "admin",
                            "ip_address": "192.168.1.100",
                            "user_agent": "Mozilla/5.0...",
                        },
                    }
                ],
                "metadata": {
                    "source_system": "manual-review",
                    "reviewer": "security-team",
                },
                "create_incident": True,
            }
        }


class AnalysisRecommendationsResponse(BaseModel):
    """Response model for recommendation queries."""

    recommendations: List[AnalysisRecommendation]
    total: int
    filters_applied: Dict[str, Optional[str]]

    class Config:
        schema_extra = {
            "example": {
                "recommendations": [
                    {
                        "id": "rec-123",
                        "action": "Enable MFA",
                        "description": "Enable multi-factor authentication for all admin accounts",
                        "priority": "critical",
                        "estimated_impact": "Significant reduction in account compromise risk",
                        "resources_required": ["identity-team"],
                        "severity": "high",
                        "attack_techniques": ["T1078"],
                    }
                ],
                "total": 1,
                "filters_applied": {"severity": "high", "attack_technique": "T1078"},
            }
        }


class AnalysisFeedback(BaseModel):
    """Model for analysis feedback submission."""

    analysis_id: UUID
    incident_id: Optional[UUID] = None
    rating: int = Field(ge=1, le=5, description="Overall rating from 1-5")
    accuracy_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Accuracy score from 0-1"
    )
    usefulness_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Usefulness score from 0-1"
    )
    false_positives: List[str] = Field(
        default_factory=list, description="List of false positive findings"
    )
    false_negatives: List[str] = Field(
        default_factory=list, description="List of missed findings"
    )
    comments: Optional[str] = Field(None, max_length=2000)

    class Config:
        schema_extra = {
            "example": {
                "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                "incident_id": "660e8400-e29b-41d4-a716-446655440001",
                "rating": 4,
                "accuracy_score": 0.85,
                "usefulness_score": 0.9,
                "false_positives": ["IP 10.0.0.1 is internal DNS server"],
                "false_negatives": ["Missed lateral movement to host 10.0.0.50"],
                "comments": "Good analysis overall, but needs better internal IP filtering",
            }
        }
