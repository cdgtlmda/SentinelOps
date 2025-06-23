"""Analysis API endpoints for SentinelOps."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from ...common.models import AnalysisResult, Incident, RemediationPriority
from ...common.storage import Storage
from ..auth import Scopes, require_auth, require_scopes
from ..models.analysis import (
    AnalysisFeedback,
    AnalysisRecommendation,
    AnalysisRecommendationsResponse,
    AnalysisResponse,
    ManualAnalysisRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis"])


@router.get("/{incident_id}")
async def get_incident_analysis(
    incident_id: UUID = Path(..., description="The incident ID to get analysis for"),
    _auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_READ])),
) -> AnalysisResponse:
    """Get analysis results for a specific incident.

    Args:
        incident_id: The UUID of the incident to analyze
        auth: Authentication context

    Returns:
        AnalysisResponse containing the analysis results

    Raises:
        HTTPException: If incident not found or analysis failed
    """
    try:
        # Initialize storage
        storage = Storage()

        # Get the incident
        incident = await storage.get_incident(str(incident_id))
        if not incident:
            raise HTTPException(
                status_code=404, detail=f"Incident {incident_id} not found"
            )

        # Check if analysis already exists
        existing_analysis = await storage.get_analysis(str(incident_id))
        if existing_analysis:
            logger.info("Returning existing analysis for incident %s", incident_id)
            return AnalysisResponse.from_analysis_result(existing_analysis, incident_id)

        # Perform new analysis using simplified logic
        logger.info("Performing new analysis for incident %s", incident_id)
        analysis_result = await _perform_simple_analysis(incident)

        # Store the analysis result
        await storage.store_analysis(str(incident_id), analysis_result)

        return AnalysisResponse.from_analysis_result(analysis_result, incident_id)

    except Exception as e:
        logger.error("Failed to analyze incident %s: %s", incident_id, str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze incident: {str(e)}"
        ) from e


@router.post("/manual")
async def create_manual_analysis(
    request: ManualAnalysisRequest,
    _auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_WRITE])),
) -> AnalysisResponse:
    """Create a manual analysis for security events.

    Args:
        request: Manual analysis request containing event data
        auth: Authentication context

    Returns:
        AnalysisResponse containing the analysis results

    Raises:
        HTTPException: If analysis failed
    """
    try:
        logger.info("Creating manual analysis for %d events", len(request.events))

        # Create a temporary incident for analysis
        from common.models import IncidentStatus

        temp_incident = Incident(
            incident_id=str(UUID(int=0)),  # Temporary ID
            title=request.title or "Manual Analysis",
            description=request.description or "Manual analysis request",
            severity=request.severity,
            status=IncidentStatus.ANALYZING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            metadata=request.metadata or {},
            events=request.events,
        )

        # Perform analysis
        analysis_result = await _perform_simple_analysis(temp_incident)

        # If user wants to save as incident
        if request.create_incident:
            storage = Storage()
            incident_id = await storage.create_incident(temp_incident)
            await storage.store_analysis(incident_id, analysis_result)
            return AnalysisResponse.from_analysis_result(
                analysis_result, UUID(incident_id)
            )

        return AnalysisResponse.from_analysis_result(analysis_result)

    except Exception as e:
        logger.error("Failed to create manual analysis: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to create manual analysis: {str(e)}"
        ) from e


@router.get("/recommendations")
async def get_analysis_recommendations(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    attack_technique: Optional[str] = Query(
        None, description="Filter by MITRE ATT&CK technique"
    ),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of recommendations"
    ),
    _auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_READ])),
) -> AnalysisRecommendationsResponse:
    """Get analysis recommendations based on filters.

    Args:
        severity: Optional severity filter
        attack_technique: Optional MITRE ATT&CK technique filter
        limit: Maximum number of recommendations to return
        auth: Authentication context

    Returns:
        AnalysisRecommendationsResponse containing filtered recommendations
    """
    try:
        storage = Storage()
        recent_analyses = await storage.get_recent_analyses(limit=100)
        recommendations = await _process_analyses(
            storage, recent_analyses, severity, attack_technique, limit
        )

        return AnalysisRecommendationsResponse(
            recommendations=recommendations,
            total=len(recommendations),
            filters_applied={
                "severity": severity,
                "attack_technique": attack_technique,
            },
        )

    except Exception as e:
        logger.error("Failed to get recommendations: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get recommendations: {str(e)}"
        ) from e


async def _process_analyses(
    storage: Storage,
    recent_analyses: list[Any],
    severity: Optional[str],
    attack_technique: Optional[str],
    limit: int,
) -> list[AnalysisRecommendation]:
    """Process analyses to extract recommendations."""
    recommendations: list[AnalysisRecommendation] = []
    seen_recommendations: set[str] = set()

    for analysis in recent_analyses:
        if not analysis.incident_id:
            continue

        incident = await storage.get_incident(analysis.incident_id)
        if not incident:
            continue

        if _should_skip_analysis(incident, analysis, severity, attack_technique):
            continue

        new_recs = _extract_recommendations(
            analysis, incident, seen_recommendations, len(recommendations)
        )
        recommendations.extend(new_recs)

        if len(recommendations) >= limit:
            return recommendations[:limit]

    return recommendations


def _should_skip_analysis(
    incident: Any,
    analysis: Any,
    severity: Optional[str],
    attack_technique: Optional[str],
) -> bool:
    """Check if analysis should be skipped based on filters."""
    if severity and incident.severity.value != severity:
        return True
    if attack_technique and attack_technique not in analysis.attack_techniques:
        return True
    return False


def _extract_recommendations(
    analysis: Any,
    incident: Any,
    seen_recommendations: set[str],
    current_count: int,
) -> list[AnalysisRecommendation]:
    """Extract unique recommendations from analysis."""
    new_recommendations = []

    for i, rec_str in enumerate(analysis.recommendations):
        if rec_str not in seen_recommendations:
            seen_recommendations.add(rec_str)
            new_recommendations.append(
                AnalysisRecommendation(
                    id=str(UUID(int=current_count + i)),
                    action=rec_str,
                    description=rec_str,
                    priority=RemediationPriority.MEDIUM,
                    estimated_impact="high",
                    resources_required=[],
                    severity=incident.severity,
                    attack_techniques=analysis.attack_techniques,
                )
            )

    return new_recommendations


@router.post("/feedback")
async def submit_analysis_feedback(
    feedback: AnalysisFeedback,
    auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_WRITE])),
) -> Dict[str, Any]:
    """Submit feedback on analysis results.

    Args:
        feedback: Feedback data including rating and comments
        auth: Authentication context

    Returns:
        Success response with feedback ID
    """
    try:
        storage = Storage()

        # Validate analysis exists
        analysis = await storage.get_analysis(str(feedback.analysis_id))
        if not analysis:
            raise HTTPException(
                status_code=404, detail=f"Analysis {feedback.analysis_id} not found"
            )

        # Store feedback
        feedback_data = {
            "analysis_id": str(feedback.analysis_id),
            "incident_id": str(feedback.incident_id) if feedback.incident_id else None,
            "rating": feedback.rating,
            "accuracy_score": feedback.accuracy_score,
            "usefulness_score": feedback.usefulness_score,
            "false_positives": feedback.false_positives,
            "false_negatives": feedback.false_negatives,
            "comments": feedback.comments,
            "user_id": auth.get("sub"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        feedback_id = await storage.store_feedback("analysis", feedback_data)

        logger.info(
            "Stored analysis feedback %s for analysis %s",
            feedback_id,
            feedback.analysis_id,
        )

        return {
            "feedback_id": feedback_id,
            "status": "success",
            "message": "Feedback submitted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to submit feedback: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to submit feedback: {str(e)}"
        ) from e


async def _perform_simple_analysis(incident: Incident) -> AnalysisResult:  # noqa: C901
    """Perform simplified analysis without full AnalysisAgent configuration.

    This is a basic implementation for API usage that doesn't require
    the full Google Cloud setup.
    """
    # Basic analysis logic
    event_count = len(incident.events) if incident.events else 0
    critical_events = [
        e for e in (incident.events or []) if e.severity.value == "critical"
    ]
    high_events = [e for e in (incident.events or []) if e.severity.value == "high"]

    # Calculate confidence score based on event severity
    confidence_score = 0.5
    if critical_events:
        confidence_score = 0.9
    elif high_events:
        confidence_score = 0.7
    elif event_count > 10:
        confidence_score = 0.6

    # Generate summary
    summary = f"Detected {event_count} security events with severity {incident.severity.value}. "
    if critical_events:
        summary += (
            f"{len(critical_events)} critical events require immediate attention."
        )
    elif high_events:
        summary += f"{len(high_events)} high-severity events detected."

    # Basic attack technique detection
    attack_techniques = []
    event_types = set(e.event_type for e in (incident.events or []))

    if "authentication_failure" in event_types:
        attack_techniques.append("T1078")  # Valid Accounts
    if "privilege_escalation" in event_types:
        attack_techniques.append("T1548")  # Abuse Elevation Control Mechanism
    if "data_exfiltration" in event_types:
        attack_techniques.append("T1048")  # Exfiltration Over Alternative Protocol
    if "malware_detection" in event_types:
        attack_techniques.append("T1204")  # User Execution

    # Generate recommendations
    recommendations: list[AnalysisRecommendation] = []

    if incident.severity.value in ["critical", "high"]:
        recommendations.append(
            AnalysisRecommendation(
                id=f"rec-{len(recommendations) + 1}",
                action="Isolate affected systems",
                description="Immediately isolate affected systems to prevent lateral movement",
                priority=RemediationPriority.CRITICAL,
                estimated_impact="Prevents further compromise",
                resources_required=["network-admin", "security-team"],
                severity=incident.severity,
                attack_techniques=[],
            )
        )

    if "authentication_failure" in event_types:
        recommendations.append(
            AnalysisRecommendation(
                id=f"rec-{len(recommendations) + 1}",
                action="Reset compromised credentials",
                description="Force password reset for affected accounts and enable MFA",
                priority=RemediationPriority.HIGH,
                estimated_impact="Prevents unauthorized access",
                resources_required=["identity-admin"],
                severity=incident.severity,
                attack_techniques=[],
            )
        )

    recommendations.append(
        AnalysisRecommendation(
            id=f"rec-{len(recommendations) + 1}",
            action="Collect forensic evidence",
            description="Preserve logs and system state for investigation",
            priority=RemediationPriority.MEDIUM,
            estimated_impact="Enables root cause analysis",
            resources_required=["forensics-team"],
            severity=incident.severity,  # Use enum directly
            attack_techniques=[],
        )
    )

    # Extract IOCs
    iocs = []
    for event in incident.events or []:
        if hasattr(event, "indicators") and event.indicators:
            for key, value in event.indicators.items():
                iocs.append({"type": key, "value": str(value), "confidence": 0.8})

    # Create timeline
    timeline = []
    for event in sorted((incident.events or []), key=lambda e: e.timestamp):
        timeline.append(
            {
                "timestamp": event.timestamp.isoformat(),
                "event": f"{event.event_type}: {event.description}",
            }
        )

    # Create analysis result
    return AnalysisResult(
        incident_id=incident.incident_id if hasattr(incident, "incident_id") else "",
        confidence_score=confidence_score,
        summary=summary,
        recommendations=[rec.action for rec in recommendations],
        attack_techniques=attack_techniques,
        evidence={"iocs": iocs[:10], "timeline": timeline[:20]},
    )
