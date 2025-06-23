"""
Incident management API routes.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.base import get_db
from src.database.repositories import IncidentsRepository

from ...config.logging_config import get_logger
from ..auth import Scopes, require_auth, require_scopes
from ..models.incidents import (
    Incident,
    IncidentActor,
    IncidentAsset,
    IncidentCreate,
    IncidentListResponse,
    IncidentSeverity,
    IncidentSource,
    IncidentStats,
    IncidentStatus,
    IncidentTimeline,
    IncidentUpdate,
    SecurityIncidentType,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/incidents", tags=["Incidents"])


class _IncidentNumberGenerator:
    """Thread-safe incident number generator."""

    def __init__(self) -> None:
        import threading

        self._lock = threading.Lock()
        self._counter = 0

    def generate(self) -> str:
        """Generate next incident number."""
        with self._lock:
            self._counter += 1
            return f"INC-{self._counter:06d}"


# Create a singleton instance
_incident_number_generator = _IncidentNumberGenerator()


def _generate_incident_number() -> str:
    """Generate a human-readable incident number."""
    return _incident_number_generator.generate()


def _model_to_api(incident_model: Any) -> Incident:
    """Convert database model to API model."""
    # Parse JSON fields
    actors = (
        [IncidentActor(**actor) for actor in incident_model.actors]
        if incident_model.actors
        else []
    )
    assets = (
        [IncidentAsset(**asset) for asset in incident_model.assets]
        if incident_model.assets
        else []
    )
    timeline = (
        [IncidentTimeline(**entry) for entry in incident_model.timeline]
        if incident_model.timeline
        else []
    )
    if not incident_model.source:
        # Create a default source if none exists
        source = IncidentSource(
            system="unknown",
            confidence=0.0,
            rule_id=None,
            rule_name="Unknown",
            raw_data={},
        )
    else:
        # Ensure required fields are present with defaults
        source_data = dict(incident_model.source)
        if "system" not in source_data:
            source_data["system"] = "unknown"
        source = IncidentSource(**source_data)

    return Incident(
        id=incident_model.id,
        incident_number=incident_model.incident_number,
        title=incident_model.title,
        description=incident_model.description,
        incident_type=incident_model.incident_type,
        severity=incident_model.severity,
        priority=incident_model.priority,
        status=incident_model.status,
        external_id=incident_model.external_id,
        tags=incident_model.tags,
        custom_fields=incident_model.custom_fields,
        created_at=incident_model.created_at,
        updated_at=incident_model.updated_at,
        detected_at=incident_model.detected_at,
        resolved_at=incident_model.resolved_at,
        source=source,
        actors=actors,
        assets=assets,
        timeline=timeline,
        analysis=incident_model.analysis,
        remediation_actions=incident_model.remediation_actions,
        created_by=incident_model.created_by,
        updated_by=incident_model.updated_by,
        assigned_to=incident_model.assigned_to,
        time_to_detect=incident_model.time_to_detect,
        time_to_respond=incident_model.time_to_respond,
        time_to_resolve=incident_model.time_to_resolve,
        parent_incident=incident_model.parent_incident_id,
        related_incidents=incident_model.related_incidents,
    )


@router.get("/", response_model=IncidentListResponse)
async def list_incidents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[List[IncidentStatus]] = Query(
        None, description="Filter by status"
    ),
    severity: Optional[List[IncidentSeverity]] = Query(
        None, description="Filter by severity"
    ),
    incident_type: Optional[List[SecurityIncidentType]] = Query(
        None, description="Filter by type"
    ),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    search: Optional[str] = Query(None, description="Search query"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    _auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_READ])),
    db: AsyncSession = Depends(get_db),
) -> IncidentListResponse:
    """
    List incidents with filtering and pagination.

    Requires: incidents:read scope
    """
    repo = IncidentsRepository(db)

    # Get incidents from database
    incidents_models, total = await repo.list_incidents(
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        severity_filter=severity,
        incident_type_filter=incident_type,
        assigned_to=assigned_to,
        tags=tags,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    # Convert to API models
    incidents = [_model_to_api(model) for model in incidents_models]

    logger.info(
        "Listed %d incidents (page %d/%d)",
        len(incidents),
        page,
        (total + page_size - 1) // page_size,
    )

    return IncidentListResponse(
        incidents=incidents,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/stats", response_model=IncidentStats)
async def get_incident_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    _auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_READ])),
    db: AsyncSession = Depends(get_db),
) -> IncidentStats:
    """
    Get incident statistics.

    Requires: incidents:read scope
    """
    repo = IncidentsRepository(db)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)

    # Get all incidents for statistics
    page_size_value: int = 10000
    incidents_models, _count = await repo.list_incidents(
        page=1,
        page_size=page_size_value,
        created_after=cutoff,
    )
    all_incidents_models, _total_count = await repo.list_incidents(
        page=1, page_size=page_size_value
    )

    incidents = [_model_to_api(model) for model in incidents_models]
    all_incidents = [_model_to_api(model) for model in all_incidents_models]

    # Calculate statistics
    stats = IncidentStats(
        total_incidents=len(all_incidents),
        open_incidents=len(
            [i for i in all_incidents if i.status == IncidentStatus.OPEN]
        ),
        by_status={},
        by_severity={},
        by_type={},
        avg_time_to_detect=0.0,
        avg_time_to_respond=0.0,
        avg_time_to_resolve=0.0,
        trend_daily=[],
        top_actors=[],
        top_assets=[],
    )

    # Count by status
    for incident in all_incidents:
        status_dict = (
            dict(stats.by_status) if hasattr(stats.by_status, "__iter__") else {}
        )
        severity_dict = (
            dict(stats.by_severity) if hasattr(stats.by_severity, "__iter__") else {}
        )
        type_dict = dict(stats.by_type) if hasattr(stats.by_type, "__iter__") else {}

        stats.by_status[incident.status] = status_dict.get(incident.status, 0) + 1
        stats.by_severity[incident.severity] = (
            severity_dict.get(incident.severity, 0) + 1
        )
        stats.by_type[incident.incident_type] = (
            type_dict.get(incident.incident_type, 0) + 1
        )

    # Calculate average times
    detect_times = [i.time_to_detect for i in incidents if i.time_to_detect]
    respond_times = [i.time_to_respond for i in incidents if i.time_to_respond]
    resolve_times = [i.time_to_resolve for i in incidents if i.time_to_resolve]

    stats.avg_time_to_detect = (
        sum(detect_times) / len(detect_times) if detect_times else 0
    )
    stats.avg_time_to_respond = (
        sum(respond_times) / len(respond_times) if respond_times else 0
    )
    stats.avg_time_to_resolve = (
        sum(resolve_times) / len(resolve_times) if resolve_times else 0
    )

    # Daily trend
    daily_counts: Dict[Any, int] = {}
    for incident in incidents:
        date = incident.created_at.date()
        daily_counts[date] = daily_counts.get(date, 0) + 1

    stats.trend_daily = [
        {"date": str(date), "count": count}
        for date, count in sorted(daily_counts.items())
    ]

    # Top actors
    actor_counts: Dict[str, int] = {}
    for incident in incidents:
        for actor in incident.actors:
            key = f"{actor.type}:{actor.identifier}"
            actor_counts[key] = actor_counts.get(key, 0) + 1

    stats.top_actors = [
        {"actor": actor, "count": count}
        for actor, count in sorted(
            actor_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]
    ]

    # Top assets
    asset_counts: Dict[str, int] = {}
    for incident in incidents:
        for asset in incident.assets:
            key = f"{asset.type}:{asset.identifier}"
            asset_counts[key] = asset_counts.get(key, 0) + 1

    stats.top_assets = [
        {"asset": asset, "count": count}
        for asset, count in sorted(
            asset_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]
    ]

    return stats


@router.get("/{incident_id}", response_model=Incident)
async def get_incident(
    incident_id: uuid.UUID,
    _auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_READ])),
    db: AsyncSession = Depends(get_db),
) -> Incident:
    """
    Get a specific incident by ID.

    Requires: incidents:read scope
    """
    repo = IncidentsRepository(db)
    incident_model = await repo.get_by_id(incident_id)

    if not incident_model:
        raise HTTPException(
            status_code=404, detail=f"Incident not found: {incident_id}"
        )

    incident = _model_to_api(incident_model)
    logger.info("Retrieved incident: %s", incident.incident_number)
    return incident


@router.post("/", response_model=Incident, status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident_data: IncidentCreate,
    auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_WRITE])),
    db: AsyncSession = Depends(get_db),
) -> Incident:
    """
    Create a new incident.

    Requires: incidents:write scope
    """
    repo = IncidentsRepository(db)

    # Generate incident number
    incident_number = _generate_incident_number()

    # Create incident in database
    incident_model = await repo.create(
        incident_data=incident_data,
        created_by=auth["subject"],
        incident_number=incident_number,
    )

    # Add initial timeline entry
    now = datetime.now(timezone.utc)
    timeline_entry = {
        "timestamp": now.isoformat(),
        "event_type": "incident_created",
        "description": f"Incident created: {incident_data.title}",
        "actor": auth["subject"],
        "details": {},
    }
    incident_model.timeline.append(timeline_entry)

    # Calculate initial metrics
    incident_model.time_to_detect = (now - incident_model.detected_at).total_seconds()

    await db.commit()

    incident = _model_to_api(incident_model)

    logger.info(
        "Created incident: %s - %s",
        incident_number,
        incident.title,
        extra={
            "incident_id": str(incident.id),
            "severity": incident.severity,
            "type": incident.incident_type,
            "created_by": auth["subject"],
        },
    )

    return incident


@router.put("/{incident_id}", response_model=Incident)
async def update_incident(
    incident_id: uuid.UUID,
    update_data: IncidentUpdate,
    auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_WRITE])),
    db: AsyncSession = Depends(get_db),
) -> Incident:
    """
    Update an existing incident.

    Requires: incidents:write scope
    """
    repo = IncidentsRepository(db)
    incident_model = await repo.get_by_id(incident_id)

    if not incident_model:
        raise HTTPException(
            status_code=404, detail=f"Incident not found: {incident_id}"
        )

    # Track what changed
    changes = []
    update_dict = update_data.model_dump(exclude_unset=True)

    for field, new_value in update_dict.items():
        old_value = getattr(incident_model, field, None)
        if old_value != new_value:
            changes.append(f"{field}: {old_value} → {new_value}")

    # Update the incident
    updated_model = await repo.update(
        incident_id=incident_id,
        incident_update=update_data,
        updated_by=auth["subject"],
    )

    if not updated_model:
        raise HTTPException(
            status_code=404, detail=f"Incident not found: {incident_id}"
        )

    if changes:
        # Add timeline entry
        timeline_entry = {
            "timestamp": updated_model.updated_at.isoformat(),
            "event_type": "incident_updated",
            "description": f"Updated: {', '.join(changes)}",
            "actor": auth["subject"],
            "details": {},
        }
        updated_model.timeline.append(timeline_entry)

        # Check if resolved
        if (
            update_data.status == IncidentStatus.CLOSED
            and not updated_model.resolved_at
        ):
            updated_model.resolved_at = updated_model.updated_at
            updated_model.time_to_resolve = (
                updated_model.resolved_at - updated_model.created_at
            ).total_seconds()

        await db.commit()

        logger.info(
            "Updated incident: %s",
            updated_model.incident_number if updated_model else "unknown",
            extra={
                "incident_id": str(incident_id),
                "changes": changes,
                "updated_by": auth["subject"],
            },
        )

    incident = _model_to_api(updated_model)
    return incident


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(
    incident_id: uuid.UUID,
    auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.ADMIN_DELETE])),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete an incident.

    Requires: admin:delete scope
    """
    repo = IncidentsRepository(db)
    incident_model = await repo.get_by_id(incident_id)

    if not incident_model:
        raise HTTPException(
            status_code=404, detail=f"Incident not found: {incident_id}"
        )

    # Store incident number for logging
    incident_number = incident_model.incident_number

    # Delete the incident
    await repo.delete(incident_id)

    logger.warning(
        "Deleted incident: %s",
        incident_number,
        extra={
            "incident_id": str(incident_id),
            "deleted_by": auth["subject"],
        },
    )


@router.post("/{incident_id}/timeline", response_model=Incident)
async def add_timeline_entry(
    incident_id: uuid.UUID,
    entry: IncidentTimeline,
    auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_WRITE])),
    db: AsyncSession = Depends(get_db),
) -> Incident:
    """
    Add a timeline entry to an incident.

    Requires: incidents:write scope
    """
    repo = IncidentsRepository(db)
    incident_model = await repo.get_by_id(incident_id)

    if not incident_model:
        raise HTTPException(
            status_code=404, detail=f"Incident not found: {incident_id}"
        )

    # Set actor if not provided
    if not entry.actor:
        entry.actor = auth["subject"]

    # Add entry
    timeline_dict = entry.model_dump()
    timeline_dict["timestamp"] = (
        timeline_dict["timestamp"].isoformat()
        if isinstance(timeline_dict["timestamp"], datetime)
        else timeline_dict["timestamp"]
    )
    incident_model.timeline.append(timeline_dict)
    incident_model.timeline.sort(key=lambda e: e["timestamp"])

    # Update metadata
    setattr(incident_model, "updated_at", datetime.now(timezone.utc))
    setattr(incident_model, "updated_by", auth["subject"])

    await db.commit()

    logger.info(
        "Added timeline entry to incident: %s",
        incident_model.incident_number,
        extra={
            "incident_id": str(incident_id),
            "event_type": entry.event_type,
            "added_by": auth["subject"],
        },
    )

    incident = _model_to_api(incident_model)
    return incident


@router.post("/{incident_id}/assign", response_model=Incident)
async def assign_incident(
    incident_id: uuid.UUID,
    assignee: str = Query(..., description="User or team to assign to"),
    auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_WRITE])),
    db: AsyncSession = Depends(get_db),
) -> Incident:
    """
    Assign an incident to a user or team.

    Requires: incidents:write scope
    """
    repo = IncidentsRepository(db)
    incident_model = await repo.get_by_id(incident_id)

    if not incident_model:
        raise HTTPException(
            status_code=404, detail=f"Incident not found: {incident_id}"
        )

    old_assignee = incident_model.assigned_to

    # Update assignment directly on the model
    setattr(incident_model, "assigned_to", assignee)
    setattr(incident_model, "updated_by", auth["subject"])
    setattr(incident_model, "updated_at", datetime.now(timezone.utc))

    # Add timeline entry
    timeline_entry = {
        "timestamp": incident_model.updated_at.isoformat(),
        "event_type": "incident_assigned",
        "description": f"Assigned to {assignee}"
        + (f" (was: {old_assignee})" if old_assignee else ""),
        "actor": auth["subject"],
        "details": {},
    }
    # Timeline is a JSON column that defaults to list
    incident_model.timeline.append(timeline_entry)

    # Update time to respond if first assignment
    if not incident_model.time_to_respond and old_assignee is None:
        incident_model.time_to_respond = (  # type: ignore[unreachable]
            incident_model.updated_at - incident_model.created_at
        ).total_seconds()

    # Save changes to database
    db.add(incident_model)
    await db.commit()
    await db.refresh(incident_model)

    logger.info(
        "Assigned incident: %s to %s",
        incident_model.incident_number,
        assignee,
        extra={
            "incident_id": str(incident_id),
            "assignee": assignee,
            "assigned_by": auth["subject"],
        },
    )

    incident = _model_to_api(incident_model)
    return incident


@router.post("/{incident_id}/merge/{target_id}", response_model=Incident)
async def merge_incidents(
    incident_id: uuid.UUID,
    target_id: uuid.UUID,
    auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_WRITE])),
    db: AsyncSession = Depends(get_db),
) -> Incident:
    """
    Merge an incident into another incident.

    The source incident will be closed and linked to the target.

    Requires: incidents:write scope
    """
    if incident_id == target_id:
        raise HTTPException(
            status_code=400, detail="Cannot merge an incident with itself"
        )

    repo = IncidentsRepository(db)
    source_model = await repo.get_by_id(incident_id)
    target_model = await repo.get_by_id(target_id)

    if not source_model:
        raise HTTPException(
            status_code=404, detail=f"Source incident not found: {incident_id}"
        )
    if not target_model:
        raise HTTPException(
            status_code=404, detail=f"Target incident not found: {target_id}"
        )

    now = datetime.now(timezone.utc)

    # Merge actors and assets (avoiding duplicates)
    target_actors: list[dict[str, Any]] = list(target_model.actors or [])
    source_actors: list[dict[str, Any]] = list(source_model.actors or [])

    existing_actors = {f"{a['type']}:{a['identifier']}" for a in target_actors}
    for actor in source_actors:
        if f"{actor['type']}:{actor['identifier']}" not in existing_actors:
            target_actors.append(actor)

    target_assets: list[dict[str, Any]] = list(target_model.assets or [])
    source_assets: list[dict[str, Any]] = list(source_model.assets or [])

    existing_assets = {f"{a['type']}:{a['identifier']}" for a in target_assets}
    for asset in source_assets:
        if f"{asset['type']}:{asset['identifier']}" not in existing_assets:
            target_assets.append(asset)

    # Merge timeline entries
    target_timeline: list[dict[str, Any]] = list(target_model.timeline or [])
    source_timeline: list[dict[str, Any]] = list(source_model.timeline or [])

    target_timeline.extend(source_timeline)
    target_timeline.append(
        {
            "timestamp": now.isoformat(),
            "event_type": "incident_merged",
            "description": f"Merged incident {source_model.incident_number} into this incident",
            "actor": auth["subject"],
            "details": {"source_incident_id": str(incident_id)},
        }
    )
    target_timeline.sort(key=lambda e: e["timestamp"])

    # Update target incident
    setattr(target_model, "updated_at", now)
    setattr(target_model, "updated_by", auth["subject"])

    # Link incidents
    if incident_id not in target_model.related_incidents:
        target_model.related_incidents.append(incident_id)

    # Close source incident
    setattr(source_model, "status", IncidentStatus.CLOSED)
    setattr(source_model, "resolved_at", now)
    setattr(source_model, "parent_incident_id", target_id)
    setattr(source_model, "updated_at", now)
    setattr(source_model, "updated_by", auth["subject"])
    # Timeline is a JSON column that defaults to list
    source_model.timeline.append(
        {
            "timestamp": now.isoformat(),
            "event_type": "incident_merged",
            "description": f"Merged into incident {target_model.incident_number}",
            "actor": auth["subject"],
            "details": {"target_incident_id": str(target_id)},
        }
    )

    await db.commit()

    logger.info(
        "Merged incident %s into %s",
        source_model.incident_number,
        target_model.incident_number,
        extra={
            "source_id": str(incident_id),
            "target_id": str(target_id),
            "merged_by": auth["subject"],
        },
    )

    target = _model_to_api(target_model)
    return target
