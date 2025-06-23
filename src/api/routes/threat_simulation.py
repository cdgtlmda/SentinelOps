"""
SentinelOps Threat Simulation API Routes
Provides endpoints for generating and managing threat scenarios
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from pydantic import BaseModel, Field

from src.tools.threat_simulator import ThreatSimulator
from src.integrations.gemini import VertexAIGeminiClient as GeminiIntegration
from src.common.exceptions import GeminiError

# from src.database.repositories.incidents import IncidentRepository
from src.common.storage import get_firestore_client
from src.common.config_loader import get_config
from src.orchestrator_agent.adk_agent import OrchestratorAgent

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/threats", tags=["threat-simulation"])


# Pydantic models
class ScenarioRequest(BaseModel):
    scenario_id: Optional[str] = None
    severity: Optional[str] = None


class BatchScenarioRequest(BaseModel):
    count: int = Field(default=10, ge=1, le=100)
    severity_distribution: Optional[Dict[str, float]] = None


class CampaignRequest(BaseModel):
    duration_minutes: int = Field(default=60, ge=1, le=1440)
    intensity: str = Field(default="medium", pattern="^(low|medium|high)$")


class ThreatAnalysisRequest(BaseModel):
    event_data: Dict[str, Any]
    incident_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class BatchAnalysisRequest(BaseModel):
    events: List[Dict[str, Any]] = Field(max_length=20)
    correlation_context: Optional[str] = None


class APIResponse(BaseModel):
    status: str
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: str


# Initialize components
threat_simulator = ThreatSimulator()


def get_gemini(request: Request) -> GeminiIntegration:
    """Get Gemini integration from app state"""
    from typing import cast
    return cast(GeminiIntegration, request.app.state.gemini)


@router.get("/scenarios")
async def list_scenarios() -> APIResponse:
    """Get available threat scenarios and statistics"""
    try:
        stats = threat_simulator.get_scenario_stats()
        return APIResponse(
            status="success", data=stats, timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error("Failed to get scenario stats: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to retrieve scenario statistics",
                "error": str(e),
            },
        ) from e


@router.post("/scenarios/generate")
async def generate_scenario(request: ScenarioRequest) -> APIResponse:
    """Generate a single threat scenario"""
    try:
        scenario_id = request.scenario_id
        severity = request.severity

        # Validate severity if provided
        if severity and severity.upper() not in ["LOW", "MEDIUM", "CRITICAL"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid severity. Must be LOW, MEDIUM, or CRITICAL",
            )

        # Generate scenario
        scenario = threat_simulator.generate_scenario(
            scenario_id=scenario_id, severity=severity.upper() if severity else None
        )

        return APIResponse(
            status="success", data=scenario, timestamp=datetime.now().isoformat()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to generate scenario: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to generate threat scenario",
                "error": str(e),
            },
        ) from e


@router.post("/scenarios/batch")
async def generate_batch_scenarios(request: BatchScenarioRequest) -> APIResponse:
    """Generate multiple threat scenarios"""
    try:
        count = request.count
        severity_distribution = request.severity_distribution

        # Validate severity distribution if provided
        if severity_distribution:
            valid_severities = {"LOW", "MEDIUM", "CRITICAL"}
            if not all(k in valid_severities for k in severity_distribution.keys()):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid severity in distribution. Must be LOW, MEDIUM, or CRITICAL",
                )

            if abs(sum(severity_distribution.values()) - 1.0) > 0.01:
                raise HTTPException(
                    status_code=400,
                    detail="Severity distribution probabilities must sum to 1.0",
                )

        # Generate batch
        scenarios = threat_simulator.generate_batch(
            count=count, severity_distribution=severity_distribution
        )

        return APIResponse(
            status="success",
            data={
                "scenarios": scenarios,
                "count": len(scenarios),
                "generated_at": datetime.now().isoformat(),
            },
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error("Failed to generate batch scenarios: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to generate batch scenarios",
                "error": str(e),
            },
        ) from e


@router.post("/campaigns/simulate")
async def simulate_attack_campaign(request: CampaignRequest) -> APIResponse:
    """Simulate a coordinated attack campaign"""
    try:
        duration_minutes = request.duration_minutes
        intensity = request.intensity

        # Simulate campaign
        events = threat_simulator.simulate_attack_campaign(
            duration_minutes=duration_minutes, intensity=intensity
        )

        # Calculate campaign statistics
        severity_counts: Dict[str, int] = {}
        for event in events:
            severity = event.get("severity", "UNKNOWN")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return APIResponse(
            status="success",
            data={
                "campaign_id": f"CAMP-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "events": events,
                "statistics": {
                    "total_events": len(events),
                    "duration_minutes": duration_minutes,
                    "intensity": intensity,
                    "severity_breakdown": severity_counts,
                    "events_per_minute": (
                        len(events) / duration_minutes if duration_minutes > 0 else 0
                    ),
                },
                "generated_at": datetime.now().isoformat(),
            },
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error("Failed to simulate attack campaign: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to simulate attack campaign",
                "error": str(e),
            },
        ) from e


@router.post("/analyze")
async def analyze_threat_event(
    request: ThreatAnalysisRequest,
    gemini: GeminiIntegration = Depends(get_gemini)
) -> APIResponse:
    """Analyze a threat event using Gemini integration"""
    try:
        event_data = request.event_data
        incident_id = request.incident_id
        context = request.context

        # Convert event data to log format for analysis
        log_entries = json.dumps(event_data, indent=2)

        # Analyze using Gemini
        analysis_result = await gemini.analyze_logs(
            log_entries=log_entries,
            context={
                "incident_id": incident_id,
                "analysis_type": "threat_event",
                **(context or {})
            }
        )

        # Convert to expected format
        result = {
            "incident_id": incident_id,
            "analysis": analysis_result.data,
            "severity": analysis_result.get_severity(),
            "recommendations": analysis_result.get_recommendations()
        }

        # Store analysis in Firestore
        try:
            firestore_client = get_firestore_client()
            analysis_doc = firestore_client.collection("threat_analyses").document(
                incident_id
            )
            analysis_doc.set(result)
            logger.info("Stored analysis for incident %s", incident_id)
        except (AttributeError, ValueError, RuntimeError) as e:
            logger.warning("Failed to store analysis in Firestore: %s", e)

        return APIResponse(
            status="success",
            data=result,
            timestamp=datetime.now().isoformat(),
        )

    except GeminiError as e:
        logger.error("Gemini analysis error: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to analyze threat event",
                "error": str(e),
            },
        ) from e
    except Exception as e:
        logger.error("Failed to analyze threat event: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to analyze threat event",
                "error": str(e),
            },
        ) from e


@router.post("/analyze/batch")
async def analyze_threat_events_batch(
    request: BatchAnalysisRequest,
    gemini: GeminiIntegration = Depends(get_gemini)
) -> APIResponse:
    """Analyze multiple related threat events as a coordinated incident"""
    try:
        events = request.events
        correlation_context = request.correlation_context

        # Analyze each event using Gemini
        results = []
        for idx, event in enumerate(events):
            log_entries = json.dumps(event, indent=2)
            analysis_result = await gemini.analyze_logs(
                log_entries=log_entries,
                context={
                    "correlation_context": correlation_context,
                    "analysis_type": "threat_event_batch",
                    "event_index": idx
                }
            )
            results.append({
                "incident_id": event.get("incident_id", f"batch_{idx}"),
                "event": event,
                "analysis": analysis_result.data,
                "severity": analysis_result.get_severity(),
                "recommendations": analysis_result.get_recommendations()
            })

        # Store analyses in Firestore
        try:
            firestore_client = get_firestore_client()
            batch = firestore_client.batch()

            for result in results:
                doc_ref = firestore_client.collection("threat_analyses").document(
                    result["incident_id"]
                )
                batch.set(doc_ref, result)

            batch.commit()
            logger.info("Stored %d batch analyses", len(results))
        except (AttributeError, ValueError, RuntimeError) as e:
            logger.warning("Failed to store batch analyses in Firestore: %s", e)

        # Calculate batch statistics
        severity_counts: Dict[str, int] = {}
        for result in results:
            severity = result["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return APIResponse(
            status="success",
            data={
                "analyses": results,
                "batch_statistics": {
                    "total_events": len(results),
                    "severity_breakdown": severity_counts,
                    "severity_distribution": severity_counts,
                    "correlation_context": correlation_context,
                },
            },
            timestamp=datetime.now().isoformat(),
        )

    except GeminiError as e:
        logger.error("Gemini batch analysis error: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to analyze threat events batch",
                "error": str(e),
            },
        ) from e
    except Exception as e:
        logger.error("Failed to analyze threat events batch: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to analyze threat events batch",
                "error": str(e),
            },
        ) from e


@router.get("/analysis/{incident_id}")
async def get_threat_analysis(incident_id: str) -> APIResponse:
    """Retrieve stored threat analysis by incident ID"""
    try:
        firestore_client = get_firestore_client()
        analysis_doc = (
            firestore_client.collection("threat_analyses").document(incident_id).get()
        )

        if not analysis_doc.exists:
            raise HTTPException(
                status_code=404, detail=f"Analysis not found for incident {incident_id}"
            )

        analysis_data = analysis_doc.to_dict()

        return APIResponse(
            status="success", data=analysis_data, timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve analysis %s: %s", incident_id, e)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to retrieve threat analysis",
                "error": str(e),
            },
        ) from e


@router.get("/analysis")
async def list_threat_analyses(
    limit: int = Query(default=50, le=100),
    severity: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
) -> APIResponse:
    """List recent threat analyses with optional filtering"""
    try:
        firestore_client = get_firestore_client()
        query = firestore_client.collection("threat_analyses").order_by(
            "analysis_timestamp", direction="DESCENDING"
        )

        # Apply filters
        if severity and severity.upper() in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            query = query.where("severity", "==", severity.upper())

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                query = query.where("analysis_timestamp", ">=", start_dt.isoformat())
            except ValueError as exc:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
                ) from exc

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                query = query.where("analysis_timestamp", "<=", end_dt.isoformat())
            except ValueError as exc:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
                ) from exc

        # Execute query
        docs = query.limit(limit).stream()
        analyses = [doc.to_dict() for doc in docs]

        return APIResponse(
            status="success",
            data={
                "analyses": analyses,
                "count": len(analyses),
                "filters": {
                    "limit": limit,
                    "severity": severity,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            },
            timestamp=datetime.now().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list threat analyses: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to list threat analyses",
                "error": str(e),
            },
        ) from e


@router.get("/stats")
async def get_threat_simulation_stats() -> APIResponse:
    """Get comprehensive threat simulation and analysis statistics"""
    try:
        # Scenario statistics
        scenario_stats = threat_simulator.get_scenario_stats()

        # Analysis statistics
        analysis_stats: Dict[str, Any] = {}

        # Firestore statistics (recent analyses)
        try:
            firestore_client = get_firestore_client()
            recent_analyses = (
                firestore_client.collection("threat_analyses")
                .order_by("analysis_timestamp", direction="DESCENDING")
                .limit(100)
                .stream()
            )

            severity_counts: Dict[str, int] = {}
            confidence_sum = 0
            analysis_count = 0

            for doc in recent_analyses:
                data = doc.to_dict()
                severity = data.get("severity", "UNKNOWN")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                confidence_sum += data.get("confidence", 0)
                analysis_count += 1

            firestore_stats = {
                "total_analyses": analysis_count,
                "severity_breakdown": severity_counts,
                "average_confidence": (
                    confidence_sum / analysis_count if analysis_count > 0 else 0
                ),
            }

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.warning("Failed to get Firestore stats: %s", e)
            firestore_stats = {"error": "Unable to retrieve Firestore statistics"}

        return APIResponse(
            status="success",
            data={
                "scenario_statistics": scenario_stats,
                "analysis_statistics": analysis_stats,
                "storage_statistics": firestore_stats,
                "system_info": {
                    "threat_simulator_initialized": True,
                    "threat_analyst_initialized": False,
                    "timestamp": datetime.now().isoformat(),
                },
            },
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error("Failed to get threat simulation stats: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to retrieve threat simulation statistics",
                "error": str(e),
            },
        ) from e


async def get_orchestrator() -> OrchestratorAgent:
    """Get orchestrator agent instance."""
    config = get_config()
    return OrchestratorAgent(config)


async def simulate_privilege_escalation() -> None:
    """Simulate a privilege escalation attack."""
    return


async def simulate_data_exfiltration() -> None:
    """Simulate a data exfiltration attack."""
    return


async def simulate_lateral_movement() -> None:
    """Simulate lateral movement attack."""
    return


async def simulate_credential_theft() -> None:
    """Simulate credential theft attack."""
    return


async def simulate_ransomware() -> None:
    """Simulate ransomware attack."""
    return


@router.post("/start-simulation")
async def start_threat_simulation() -> None:
    """Start a new threat simulation."""
    return


async def get_simulation_status() -> None:
    """Get current simulation status."""
    return


async def stop_simulation() -> None:
    """Stop the current simulation."""
    return
