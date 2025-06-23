"""
SentinelOps Live Demo API Routes
Provides endpoints for managing live threat simulation demonstrations
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Request
from pydantic import BaseModel, Field

from src.tools.live_demo_orchestrator import (
    LiveDemoOrchestrator,
    LiveDemoConfig,
)
from src.common.storage import get_firestore_client
from src.common.config_loader import get_config

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/demo", tags=["live-demo"])


# Pydantic models
class StartDemoRequest(BaseModel):
    intensity: str = Field(default="medium", pattern="^(low|medium|high|extreme)$")
    duration_minutes: int = Field(default=20, ge=5, le=60)
    threat_intel_enabled: bool = True
    real_time_analysis: bool = True
    auto_remediation: bool = False


class APIResponse(BaseModel):
    status: str
    data: Optional[Any] = None
    message: Optional[str] = None
    timestamp: str


# Global demo orchestrator (singleton)
current_demo: Optional[LiveDemoOrchestrator] = None
demo_task: Optional[asyncio.Task[None]] = None


@router.post("/start")
async def start_live_demo(
    request: StartDemoRequest,
    _background_tasks: BackgroundTasks,
    fastapi_request: Request
) -> Dict[str, Any]:
    """Start a live threat simulation demonstration"""
    global current_demo, demo_task  # pylint: disable=global-statement

    try:
        # Check if demo is already running
        if current_demo and current_demo.demo_active:
            raise HTTPException(
                status_code=409,
                detail="Demo is already running. Stop current demo before starting a new one.",
            )

        # Get project configuration
        config_data = get_config()
        project_id = config_data.get("gcp_project_id", "your-gcp-project-id")

        # Create demo configuration
        demo_config = LiveDemoConfig(
            project_id=project_id,
            demo_duration_minutes=request.duration_minutes,
            demo_intensity=request.intensity,
            threat_intel_enabled=request.threat_intel_enabled,
            real_time_analysis=request.real_time_analysis,
            auto_remediation=request.auto_remediation,
        )

        # Get Gemini integration from app state
        gemini_integration = getattr(fastapi_request.app.state, 'gemini', None)
        # Initialize orchestrator with Gemini integration
        current_demo = LiveDemoOrchestrator(demo_config, gemini_integration=gemini_integration)

        # Start demo in background
        # Create a wrapper coroutine that returns None
        async def _start_demo() -> None:
            await current_demo.start_live_demo()
        demo_task = asyncio.create_task(_start_demo())

        # Create session info
        session_info = {
            "demo_id": f"DEMO-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "start_time": datetime.now().isoformat(),
            "config": {
                "intensity": request.intensity,
                "duration_minutes": request.duration_minutes,
                "threat_intel_enabled": request.threat_intel_enabled,
                "real_time_analysis": request.real_time_analysis,
            },
            "status": "starting",
        }

        logger.info("🚀 Starting live demo: %s", session_info["demo_id"])

        return {
            "status": "success",
            "data": {"session": session_info},
            "message": "Live demo started successfully",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error("Failed to start live demo: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to start live demo: {str(e)}"
        ) from e


@router.post("/stop")
async def stop_live_demo() -> Dict[str, Any]:
    """Stop the currently running live demonstration"""
    global current_demo, demo_task  # pylint: disable=global-statement

    try:
        if not current_demo or not current_demo.demo_active:
            raise HTTPException(status_code=404, detail="No active demo to stop")

        # Stop the demo
        current_demo.demo_active = False

        if demo_task:
            demo_task.cancel()
            try:
                await demo_task
            except asyncio.CancelledError:
                pass

        # Get final stats
        final_stats = current_demo.get_demo_summary()

        logger.info("🛑 Live demo stopped")

        # Clean up
        current_demo = None
        demo_task = None

        return {
            "status": "success",
            "data": {"final_stats": final_stats},
            "message": "Live demo stopped successfully",
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to stop live demo: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to stop live demo: {str(e)}"
        ) from e


@router.get("/status")
async def get_demo_status() -> Any:
    """Get current demo status and basic information"""
    try:
        if not current_demo:
            return APIResponse(
                status="success",
                data={"demo_active": False, "demo_status": "not_running"},
                timestamp=datetime.now().isoformat(),
            )

        status_info = {
            "demo_active": current_demo.demo_active,
            "demo_status": "running" if current_demo.demo_active else "stopped",
            "demo_start_time": (
                current_demo.demo_start_time.isoformat()
                if current_demo.demo_start_time
                else None
            ),
            "config": {
                "intensity": current_demo.config.demo_intensity,
                "duration_minutes": current_demo.config.demo_duration_minutes,
                "threat_intel_enabled": current_demo.config.threat_intel_enabled,
                "real_time_analysis": current_demo.config.real_time_analysis,
            },
            "basic_stats": current_demo.demo_stats,
        }

        return APIResponse(
            status="success", data=status_info, timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error("Failed to get demo status: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to get demo status: {str(e)}"
        ) from e


@router.get("/metrics")
async def get_live_metrics() -> Any:
    """Get real-time demo metrics from Firestore"""
    try:
        firestore_client = get_firestore_client()

        # Get live metrics document
        metrics_ref = firestore_client.collection("demo_metrics").document(
            "live_metrics"
        )
        metrics_doc = metrics_ref.get()

        if not metrics_doc.exists:
            return APIResponse(
                status="success",
                data={"metrics": None, "message": "No live metrics available"},
                timestamp=datetime.now().isoformat(),
            )

        metrics_data = metrics_doc.to_dict()

        return APIResponse(
            status="success",
            data={"metrics": metrics_data},
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error("Failed to get live metrics: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to get live metrics: {str(e)}"
        ) from e


@router.get("/incidents")
async def get_recent_incidents(
    limit: int = Query(default=20, le=100),
    severity: Optional[str] = Query(default=None),
    phase: Optional[str] = Query(default=None),
) -> Any:
    """Get recent demo incidents with optional filtering"""
    try:
        firestore_client = get_firestore_client()

        # Build query
        query = firestore_client.collection("demo_incidents").order_by(
            "timestamp", direction="DESCENDING"
        )

        # Apply filters
        if severity and severity.upper() in ["LOW", "MEDIUM", "CRITICAL"]:
            query = query.where("severity", "==", severity.upper())

        if phase:
            query = query.where("demo_phase", "==", phase)

        # Execute query
        docs = query.limit(limit).stream()
        incidents = [doc.to_dict() for doc in docs]

        return APIResponse(
            status="success",
            data={
                "incidents": incidents,
                "count": len(incidents),
                "filters": {"limit": limit, "severity": severity, "phase": phase},
            },
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error("Failed to get recent incidents: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to get recent incidents: {str(e)}"
        ) from e


@router.get("/analyses")
async def get_recent_analyses(
    limit: int = Query(default=20, le=100),
    min_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
) -> Any:
    """Get recent AI analyses with optional filtering"""
    try:
        firestore_client = get_firestore_client()

        # Build query
        query = firestore_client.collection("demo_analyses").order_by(
            "analysis_timestamp", direction="DESCENDING"
        )

        # Apply confidence filter if specified
        if min_confidence > 0:
            query = query.where("confidence", ">=", min_confidence)

        # Execute query
        docs = query.limit(limit).stream()
        analyses = [doc.to_dict() for doc in docs]

        # Calculate summary stats
        total_analyses = len(analyses)
        avg_confidence = (
            sum(a.get("confidence", 0) for a in analyses) / total_analyses
            if total_analyses > 0
            else 0
        )
        severity_counts: Dict[str, int] = {}

        for analysis in analyses:
            severity = analysis.get("severity", "UNKNOWN")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return APIResponse(
            status="success",
            data={
                "analyses": analyses,
                "summary": {
                    "total_analyses": total_analyses,
                    "average_confidence": avg_confidence,
                    "severity_breakdown": severity_counts,
                },
                "filters": {"limit": limit, "min_confidence": min_confidence},
            },
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error("Failed to get recent analyses: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to get recent analyses: {str(e)}"
        ) from e


@router.get("/detections")
async def get_threat_detections(
    limit: int = Query(default=50, le=200),
    query_type: Optional[str] = Query(default=None),
    hours_back: int = Query(default=1, ge=1, le=24),
) -> Any:
    """Get threat intelligence detections from the detection agent"""
    try:
        firestore_client = get_firestore_client()

        # Build query
        query = firestore_client.collection("demo_detections").order_by(
            "detection_timestamp", direction="DESCENDING"
        )

        # Apply filters
        if query_type:
            query = query.where("query_type", "==", query_type)

        # Execute query
        docs = query.limit(limit).stream()
        detections = [doc.to_dict() for doc in docs]

        # Group by detection type
        detection_types: Dict[str, Any] = {}
        for detection in detections:
            det_type = detection.get("query_type", "unknown")
            if det_type not in detection_types:
                detection_types[det_type] = []
            detection_types[det_type].append(detection)

        return APIResponse(
            status="success",
            data={
                "detections": detections,
                "detection_types": detection_types,
                "summary": {
                    "total_detections": len(detections),
                    "types_count": len(detection_types),
                    "hours_covered": hours_back,
                },
                "filters": {
                    "limit": limit,
                    "query_type": query_type,
                    "hours_back": hours_back,
                },
            },
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error("Failed to get threat detections: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to get threat detections: {str(e)}"
        ) from e


@router.get("/summary")
async def get_demo_summary() -> Any:
    """Get comprehensive demo summary including all metrics"""
    try:
        # Get current demo stats
        demo_stats = current_demo.get_demo_summary() if current_demo else {}

        # Get recent metrics from Firestore
        firestore_client = get_firestore_client()

        # Get latest metrics
        metrics_ref = firestore_client.collection("demo_metrics").document(
            "live_metrics"
        )
        metrics_doc = metrics_ref.get()
        latest_metrics = metrics_doc.to_dict() if metrics_doc.exists else {}

        # Get incident counts
        incident_query = firestore_client.collection("demo_incidents").limit(1000)
        incident_count = len(list(incident_query.stream()))

        # Get analysis counts
        analysis_query = firestore_client.collection("demo_analyses").limit(1000)
        analysis_count = len(list(analysis_query.stream()))

        # Get detection counts
        detection_query = firestore_client.collection("demo_detections").limit(1000)
        detection_count = len(list(detection_query.stream()))

        summary = {
            "demo_active": current_demo.demo_active if current_demo else False,
            "demo_stats": demo_stats,
            "latest_metrics": latest_metrics,
            "storage_counts": {
                "total_incidents": incident_count,
                "total_analyses": analysis_count,
                "total_detections": detection_count,
            },
            "system_health": {
                "threat_simulator": "operational",
                "threat_analyst": (
                    "operational"
                    if current_demo and current_demo.gemini_integration
                    else "standby"
                ),
                "threat_intel": "operational",
                "firestore": "operational",
            },
        }

        return APIResponse(
            status="success", data=summary, timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error("Failed to get demo summary: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to get demo summary: {str(e)}"
        ) from e


@router.post("/scenario/inject")
async def inject_custom_scenario(scenario_data: Dict[str, Any]) -> Any:
    """Inject a custom threat scenario into the running demo"""
    try:
        if not current_demo or not current_demo.demo_active:
            raise HTTPException(
                status_code=404, detail="No active demo to inject scenario into"
            )

        # Validate and enhance scenario
        enhanced_scenario = {
            **scenario_data,
            "demo_context": True,
            "injection_timestamp": datetime.now().isoformat() + "Z",
            "injection_type": "manual",
            "simulation_id": f"INJECT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        }

        # Add to demo incidents
        current_demo.generated_incidents.append(enhanced_scenario)
        current_demo.demo_stats["scenarios_generated"] += 1

        # Store in Firestore
        firestore_client = get_firestore_client()
        incident_ref = firestore_client.collection("demo_incidents").document(
            enhanced_scenario["simulation_id"]
        )
        incident_ref.set(enhanced_scenario)

        logger.info(
            "💉 Injected custom scenario: %s", enhanced_scenario['simulation_id']
        )

        return APIResponse(
            status="success",
            data={"injected_scenario": enhanced_scenario},
            message="Custom scenario injected successfully",
            timestamp=datetime.now().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to inject custom scenario: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to inject custom scenario: {str(e)}"
        ) from e


@router.delete("/cleanup")
async def cleanup_demo_data() -> Any:
    """Clean up all demo data from Firestore (for testing)"""
    try:
        firestore_client = get_firestore_client()

        # Collections to clean
        collections = [
            "demo_incidents",
            "demo_analyses",
            "demo_detections",
            "demo_metrics",
            "demo_noise_events",
            "live_demo_sessions",
        ]

        cleanup_stats = {}

        for collection_name in collections:
            collection_ref = firestore_client.collection(collection_name)
            docs = collection_ref.stream()

            count = 0
            for doc in docs:
                doc.reference.delete()
                count += 1

            cleanup_stats[collection_name] = count

        logger.info("🧹 Cleaned up demo data: %s", cleanup_stats)

        return APIResponse(
            status="success",
            data={"cleanup_stats": cleanup_stats},
            message="Demo data cleaned up successfully",
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error("Failed to cleanup demo data: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup demo data: {str(e)}"
        ) from e
