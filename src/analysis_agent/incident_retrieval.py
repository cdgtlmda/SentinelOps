"""
Incident retrieval functionality for the Analysis Agent.

This module handles retrieving and validating incident data from Firestore.
"""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from google.cloud import firestore_v1 as firestore

from src.common.models import (
    EventSource,
    Incident,
    IncidentStatus,
    SecurityEvent,
    SeverityLevel,
)

if TYPE_CHECKING:
    pass


class IncidentRetriever:
    """Handles incident data retrieval and validation from Firestore."""

    def __init__(self, db: "firestore.Client", logger: logging.Logger) -> None:
        """
        Initialize the incident retriever.

        Args:
            db: Firestore client instance
            logger: Logger instance for logging
        """
        self.db = db
        self.logger = logger
        self.incidents_collection = db.collection("incidents")

    async def retrieve_incident(self, incident_id: str) -> Optional[Incident]:
        """
        Retrieve an incident from Firestore with full validation.

        Args:
            incident_id: The ID of the incident to retrieve

        Returns:
            The validated Incident object, or None if not found or invalid
        """
        try:
            # Get the incident document
            incident_doc = self.incidents_collection.document(incident_id).get()

            if not incident_doc.exists:
                self.logger.error("Incident %s not found in Firestore", incident_id)
                return None

            # Extract and validate the data
            incident_data = incident_doc.to_dict()
            if not incident_data:
                self.logger.error(f"Incident {incident_id} has no data")
                return None

            # Convert to Incident object
            incident = self._convert_to_incident(incident_id, incident_data)

            # Validate the incident
            self._validate_incident_completeness(incident)

            return incident

        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error(f"Error retrieving incident {incident_id}: {e}")
            return None

    def _convert_to_incident(self, incident_id: str, data: dict[str, Any]) -> Incident:
        """
        Convert Firestore document data to an Incident object.

        Args:
            incident_id: The incident ID
            data: The document data from Firestore

        Returns:
            The Incident object
        """
        # Parse dates
        created_at = self._parse_timestamp(data.get("created_at"))
        updated_at = self._parse_timestamp(data.get("updated_at"))

        # Create the incident
        incident = Incident(
            incident_id=incident_id,
            created_at=created_at,
            updated_at=updated_at,
            title=data.get("title", ""),
            description=data.get("description", ""),
            severity=self._parse_severity(data.get("severity")),
            status=self._parse_status(data.get("status")),
            events=[],  # Will be populated below
            assigned_to=data.get("assigned_to"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

        # Convert events
        events_data = data.get("events", [])
        for event_data in events_data:
            event = self._convert_to_event(event_data)
            if event:
                incident.events.append(event)

        return incident

    def _convert_to_event(self, event_data: dict[str, Any]) -> Optional[SecurityEvent]:
        """
        Convert event data to a SecurityEvent object.

        Args:
            event_data: The event data dictionary

        Returns:
            The SecurityEvent object, or None if conversion fails
        """
        try:
            # Parse event source
            source_data = event_data.get("source", {})
            source = EventSource(
                source_type=source_data.get("source_type", "unknown"),
                source_name=source_data.get("source_name", "unknown"),
                source_id=source_data.get("source_id", "unknown"),
                resource_type=source_data.get("resource_type"),
                resource_name=source_data.get("resource_name"),
                resource_id=source_data.get("resource_id"),
            )

            # Parse timestamp
            timestamp = self._parse_timestamp(event_data.get("timestamp"))

            # Create the event
            event = SecurityEvent(
                event_id=event_data.get("event_id", ""),
                timestamp=timestamp,
                event_type=event_data.get("event_type", ""),
                source=source,
                severity=self._parse_severity(event_data.get("severity")),
                description=event_data.get("description", ""),
                raw_data=event_data.get("raw_data", {}),
                actor=event_data.get("actor"),
                affected_resources=event_data.get("affected_resources", []),
                indicators=event_data.get("indicators", {}),
            )

            return event

        except (ValueError, KeyError, AttributeError) as e:
            self.logger.warning(f"Failed to convert event data: {e}")
            return None

    def _parse_timestamp(self, timestamp_value: Any) -> datetime:
        """
        Parse a timestamp value from various formats.

        Args:
            timestamp_value: The timestamp value (string, datetime, or None)

        Returns:
            A datetime object
        """
        if isinstance(timestamp_value, datetime):
            return timestamp_value
        if isinstance(timestamp_value, str):
            try:
                return datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
            except ValueError:
                self.logger.warning(f"Invalid timestamp format: {timestamp_value}")
                return datetime.now(timezone.utc)
        else:
            return datetime.now(timezone.utc)

    def _parse_severity(self, severity_value: Any) -> SeverityLevel:
        """
        Parse a severity value to SeverityLevel enum.

        Args:
            severity_value: The severity value (string or SeverityLevel)

        Returns:
            A SeverityLevel enum value
        """
        if isinstance(severity_value, SeverityLevel):
            return severity_value
        if isinstance(severity_value, str):
            try:
                return SeverityLevel(severity_value.lower())
            except ValueError:
                self.logger.warning(f"Invalid severity value: {severity_value}")
                return SeverityLevel.INFORMATIONAL
        else:
            return SeverityLevel.INFORMATIONAL

    def _parse_status(self, status_value: Any) -> IncidentStatus:
        """
        Parse a status value to IncidentStatus enum.

        Args:
            status_value: The status value (string or IncidentStatus)

        Returns:
            An IncidentStatus enum value
        """
        if isinstance(status_value, IncidentStatus):
            return status_value
        if isinstance(status_value, str):
            try:
                return IncidentStatus(status_value)
            except ValueError:
                self.logger.warning(f"Invalid status value: {status_value}")
                return IncidentStatus.DETECTED
        else:
            return IncidentStatus.DETECTED

    def _validate_incident_completeness(self, incident: Incident) -> None:
        """
        Validate that the incident has all required data.

        Args:
            incident: The incident to validate

        Raises:
            ValueError: If the incident is missing required data
        """
        # Check required fields
        if not incident.title:
            raise ValueError("Incident is missing title")

        if not incident.description:
            raise ValueError("Incident is missing description")

        if not incident.events:
            raise ValueError("Incident has no events")

        # Validate each event
        for i, event in enumerate(incident.events):
            try:
                event.validate()
            except ValueError as e:
                raise ValueError(f"Event {i} validation failed: {e}") from e

        # Log validation success
        self.logger.debug(
            f"Incident {incident.incident_id} validated successfully: "
            f"{len(incident.events)} events, severity: {incident.severity.value}",
        )
