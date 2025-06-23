"""
Database operations for incidents.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.incidents import (
    IncidentCreate,
    IncidentSeverity,
    IncidentStatus,
    IncidentUpdate,
    SecurityIncidentType,
)
from src.database.models.incidents import IncidentModel


class IncidentsRepository:
    """Repository for incident database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self, incident_data: IncidentCreate, created_by: str, incident_number: str
    ) -> IncidentModel:
        """Create a new incident in the database."""
        incident = IncidentModel(
            incident_number=incident_number,
            title=incident_data.title,
            description=incident_data.description,
            incident_type=incident_data.incident_type,
            severity=incident_data.severity,
            priority=incident_data.priority,
            status=incident_data.status,
            external_id=incident_data.external_id,
            tags=incident_data.tags,
            custom_fields=incident_data.custom_fields,
            detected_at=datetime.now(timezone.utc),  # Set detection time to now
            source=incident_data.source.model_dump(),
            actors=[a.model_dump() for a in incident_data.actors],
            assets=[a.model_dump() for a in incident_data.assets],
            timeline=[],  # Initialize empty timeline
            analysis=None,  # No analysis yet
            remediation_actions=[],  # No remediation actions yet
            created_by=created_by,
            updated_by=created_by,
        )

        self.session.add(incident)
        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def get_by_id(self, incident_id: UUID) -> Optional[IncidentModel]:
        """Get an incident by ID."""
        result = await self.session.execute(
            select(IncidentModel).where(IncidentModel.id == incident_id)
        )
        return result.scalar_one_or_none()

    async def get_by_incident_number(
        self, incident_number: str
    ) -> Optional[IncidentModel]:
        """Get an incident by incident number."""
        result = await self.session.execute(
            select(IncidentModel).where(
                IncidentModel.incident_number == incident_number
            )
        )
        return result.scalar_one_or_none()

    async def list_incidents(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[List[IncidentStatus]] = None,
        severity_filter: Optional[List[IncidentSeverity]] = None,
        incident_type_filter: Optional[List[SecurityIncidentType]] = None,
        assigned_to: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[IncidentModel], int]:
        """List incidents with filtering and pagination."""
        # Build base query
        query = select(IncidentModel)

        # Apply filters
        filters: list[Any] = []

        if status_filter:
            filters.append(IncidentModel.status.in_(status_filter))

        if severity_filter:
            filters.append(IncidentModel.severity.in_(severity_filter))

        if incident_type_filter:
            filters.append(IncidentModel.incident_type.in_(incident_type_filter))

        if assigned_to:
            filters.append(IncidentModel.assigned_to == assigned_to)

        if created_after:
            filters.append(IncidentModel.created_at >= created_after)

        if created_before:
            filters.append(IncidentModel.created_at <= created_before)

        if tags:
            # Check if any of the tags are in the incident's tags array
            tag_filters = []
            for tag in tags:
                tag_filters.append(
                    func.jsonb_contains(IncidentModel.tags, f'["{tag}"]')
                )
            filters.append(or_(*tag_filters))

        if search:
            # Search in title and description
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    IncidentModel.title.ilike(search_pattern),
                    IncidentModel.description.ilike(search_pattern),
                )
            )

        if filters:
            query = query.where(and_(*filters))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())  # pylint: disable=not-callable
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(IncidentModel, sort_by, IncidentModel.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column)

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.limit(page_size).offset(offset)

        # Execute query
        result = await self.session.execute(query)
        incidents = list(result.scalars().all())

        return incidents, total or 0

    async def update(
        self, incident_id: UUID, incident_update: IncidentUpdate, updated_by: str
    ) -> Optional[IncidentModel]:
        """Update an incident."""
        incident = await self.get_by_id(incident_id)
        if not incident:
            return None

        # Update fields if provided
        update_data = incident_update.model_dump(exclude_unset=True)

        # Update basic fields
        if update_data.get("title"):
            incident.title = update_data["title"]
        if update_data.get("updated_at"):
            incident.updated_at = update_data["updated_at"]

        for field, value in update_data.items():
            setattr(incident, field, value)

        setattr(incident, "updated_by", updated_by)
        setattr(incident, "updated_at", datetime.now(timezone.utc))

        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def delete(self, incident_id: UUID) -> bool:
        """Delete an incident."""
        incident = await self.get_by_id(incident_id)
        if not incident:
            return False

        await self.session.delete(incident)
        await self.session.commit()
        return True

    async def update_status(
        self, incident_id: UUID, status: IncidentStatus, updated_by: str
    ) -> Optional[IncidentModel]:
        """Update incident status."""
        incident = await self.get_by_id(incident_id)
        if not incident:
            return None

        setattr(incident, "status", status)
        setattr(incident, "updated_by", updated_by)
        setattr(incident, "updated_at", datetime.now(timezone.utc))

        # If resolving, set resolved_at
        if status in [
            IncidentStatus.CLOSED,
            IncidentStatus.REMEDIATED,
            IncidentStatus.FALSE_POSITIVE,
        ]:
            setattr(incident, "resolved_at", datetime.now(timezone.utc))
            incident.time_to_resolve = (
                incident.resolved_at - incident.detected_at
            ).total_seconds()

        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def add_timeline_entry(
        self, incident_id: UUID, timeline_entry: Dict[str, Any], actor: str
    ) -> Optional[IncidentModel]:
        """Add a timeline entry to an incident."""
        incident = await self.get_by_id(incident_id)
        if not incident:
            return None

        # Add timestamp if not provided
        if "timestamp" not in timeline_entry:
            timeline_entry["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Ensure timeline is a list (JSON columns default to list)
        # Cast to ensure it's never None, since it has a default value
        current_timeline = incident.timeline if incident.timeline is not None else []
        # Type narrowing for mypy - at runtime JSON columns are Python lists
        # Cast to list to satisfy mypy while maintaining runtime safety
        timeline: List[Dict[str, Any]] = (
            list(current_timeline) if current_timeline else []
        )
        timeline.append(timeline_entry)
        setattr(incident, "timeline", timeline)
        setattr(incident, "updated_by", actor)
        setattr(incident, "updated_at", datetime.now(timezone.utc))

        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def update_analysis(
        self, incident_id: UUID, analysis: Dict[str, Any], updated_by: str
    ) -> Optional[IncidentModel]:
        """Update incident analysis."""
        incident = await self.get_by_id(incident_id)
        if not incident:
            return None

        setattr(incident, "analysis", analysis)
        setattr(incident, "updated_by", updated_by)
        setattr(incident, "updated_at", datetime.now(timezone.utc))

        # Update time to respond if this is the first analysis
        if not incident.time_to_respond and incident.analysis:
            incident.time_to_respond = (
                datetime.now(timezone.utc) - incident.detected_at
            ).total_seconds()

        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def add_remediation_action(
        self, incident_id: UUID, action: Dict[str, Any], actor: str
    ) -> Optional[IncidentModel]:
        """Add a remediation action to an incident."""
        incident = await self.get_by_id(incident_id)
        if not incident:
            return None

        # Ensure remediation_actions is a list (JSON columns default to list)
        # Cast to ensure it's never None, since it has a default value
        current_actions = (
            incident.remediation_actions
            if incident.remediation_actions is not None
            else []
        )
        # Type narrowing for mypy - at runtime JSON columns are Python lists
        # Cast to list to satisfy mypy while maintaining runtime safety
        remediation_actions: List[Dict[str, Any]] = (
            list(current_actions) if current_actions else []
        )
        remediation_actions.append(action)
        setattr(incident, "remediation_actions", remediation_actions)
        setattr(incident, "updated_by", actor)
        setattr(incident, "updated_at", datetime.now(timezone.utc))

        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def assign_incident(
        self, incident_id: UUID, assigned_to: str, updated_by: str
    ) -> Optional[IncidentModel]:
        """Assign an incident to a user or team."""
        incident = await self.get_by_id(incident_id)
        if not incident:
            return None

        setattr(incident, "assigned_to", assigned_to)
        setattr(incident, "updated_by", updated_by)
        setattr(incident, "updated_at", datetime.now(timezone.utc))

        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def get_next_incident_number(self) -> str:
        """Generate the next incident number."""
        # Get the highest incident number
        result = await self.session.execute(
            select(func.max(IncidentModel.incident_number))
        )
        max_incident_number = result.scalar()

        if not max_incident_number:
            return "INC-000001"

        # Extract the number part and increment
        try:
            current_num = int(max_incident_number.split("-")[1])
            next_num = current_num + 1
            return f"INC-{next_num:06d}"
        except (IndexError, ValueError):
            # Fallback if format is unexpected
            return "INC-000001"

    async def get_incident_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get incident statistics for the specified number of days."""
        from_date = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        from_date = from_date.replace(
            day=from_date.day - days if from_date.day > days else 1
        )

        # Get counts by status
        status_counts = await self.session.execute(
            select(
                IncidentModel.status, func.count(IncidentModel.id).label("count")  # pylint: disable=not-callable
            ).group_by(IncidentModel.status)
        )

        # Get counts by severity
        severity_counts = await self.session.execute(
            select(
                IncidentModel.severity, func.count(IncidentModel.id).label("count")  # pylint: disable=not-callable
            ).group_by(IncidentModel.severity)
        )

        # Get total and open counts
        total_count = await self.session.execute(select(func.count(IncidentModel.id)))  # pylint: disable=not-callable

        open_count = await self.session.execute(
            select(func.count(IncidentModel.id)).where(  # pylint: disable=not-callable
                IncidentModel.status == IncidentStatus.OPEN
            )
        )

        return {
            "total_incidents": total_count.scalar() or 0,
            "open_incidents": open_count.scalar() or 0,
            "by_status": {row.status.value: row.count for row in status_counts},
            "by_severity": {row.severity.value: row.count for row in severity_counts},
        }
