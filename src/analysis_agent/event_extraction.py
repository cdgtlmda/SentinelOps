"""
Event data extraction functionality for the Analysis Agent.

This module handles extracting and processing event metadata and associated data.
"""

import logging
from typing import Any, Dict, List, Set

from src.common.models import Incident, SecurityEvent, SeverityLevel


class EventDataExtractor:
    """Handles extraction and processing of event data from incidents."""

    def __init__(self, logger: logging.Logger):
        """
        Initialize the event data extractor.

        Args:
            logger: Logger instance for logging
        """
        self.logger = logger

    def extract_incident_metadata(self, incident: Incident) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from an incident.

        Args:
            incident: The incident to extract metadata from

        Returns:
            Dictionary containing incident metadata
        """
        # Calculate time-based metrics
        duration = (incident.updated_at - incident.created_at).total_seconds()

        # Extract unique values
        unique_event_types = self._get_unique_event_types(incident.events)
        unique_sources = self._get_unique_sources(incident.events)
        affected_resources = self._get_all_affected_resources(incident.events)
        unique_actors = self._get_unique_actors(incident.events)

        # Calculate severity distribution
        severity_distribution = self._calculate_severity_distribution(incident.events)

        # Get time range of events
        time_range = self._get_event_time_range(incident.events)

        metadata = {
            "incident_id": incident.incident_id,
            "title": incident.title,
            "severity": incident.severity.value,
            "status": incident.status,
            "event_count": len(incident.events),
            "duration_seconds": duration,
            "unique_event_types": list(unique_event_types),
            "unique_sources": list(unique_sources),
            "affected_resources": list(affected_resources),
            "unique_actors": list(unique_actors),
            "severity_distribution": severity_distribution,
            "event_time_range": time_range,
            "has_critical_events": any(
                e.severity == SeverityLevel.CRITICAL for e in incident.events
            ),
            "tags": incident.tags,
        }

        self.logger.debug(f"Extracted metadata for incident {incident.incident_id}")
        return metadata

    def extract_associated_events(self, incident: Incident) -> List[Dict[str, Any]]:
        """
        Extract and enrich associated events from an incident.

        Args:
            incident: The incident containing events

        Returns:
            List of enriched event data dictionaries
        """
        enriched_events = []

        for event in incident.events:
            enriched_event = self._enrich_event_data(event, incident)
            enriched_events.append(enriched_event)

        # Sort events by timestamp
        enriched_events.sort(key=lambda e: e["timestamp"])

        self.logger.debug(
            f"Extracted {len(enriched_events)} events from incident {incident.incident_id}"
        )
        return enriched_events

    def validate_data_completeness(self, incident: Incident) -> Dict[str, Any]:
        """
        Validate the completeness of incident data.

        Args:
            incident: The incident to validate

        Returns:
            Dictionary containing validation results and missing data indicators
        """
        validation_results: Dict[str, Any] = {
            "is_complete": True,
            "missing_fields": [],
            "warnings": [],
            "data_quality_score": 1.0,
        }

        # Check incident-level fields
        if not incident.title:
            validation_results["missing_fields"].append("title")
            validation_results["is_complete"] = False

        if not incident.description:
            validation_results["missing_fields"].append("description")
            validation_results["is_complete"] = False

        if not incident.events:
            validation_results["missing_fields"].append("events")
            validation_results["is_complete"] = False
            validation_results["data_quality_score"] = 0.0
            return validation_results

        # Check event-level completeness
        events_with_issues = []
        total_quality_score = 0.0

        for i, event in enumerate(incident.events):
            event_validation = self._validate_event_completeness(event)
            if not event_validation["is_complete"]:
                events_with_issues.append(
                    {
                        "event_index": i,
                        "event_id": event.event_id,
                        "issues": event_validation["issues"],
                    }
                )
            total_quality_score += event_validation["quality_score"]

        # Calculate overall data quality score
        if incident.events:
            validation_results["data_quality_score"] = total_quality_score / len(
                incident.events
            )

        if events_with_issues:
            validation_results["warnings"].append(
                f"{len(events_with_issues)} events have data quality issues"
            )
            validation_results["events_with_issues"] = events_with_issues

        # Additional quality checks
        if len(incident.events) < 2:
            validation_results["warnings"].append(
                "Incident has very few events, analysis may be limited"
            )

        if not incident.tags:
            validation_results["warnings"].append("No tags assigned to incident")

        self.logger.info(
            f"Data completeness validation for incident {incident.incident_id}: "
            f"complete={validation_results['is_complete']}, "
            f"quality_score={validation_results['data_quality_score']:.2f}"
        )

        return validation_results

    def _enrich_event_data(
        self, event: SecurityEvent, incident: Incident
    ) -> Dict[str, Any]:
        """Enrich a single event with additional context."""
        enriched = event.to_dict()

        # Add incident context
        enriched["incident_context"] = {
            "incident_id": incident.incident_id,
            "incident_severity": incident.severity.value,
            "incident_title": incident.title,
        }

        # Add derived fields
        enriched["has_indicators"] = bool(event.indicators)
        enriched["resource_count"] = len(event.affected_resources)
        enriched["has_actor"] = event.actor is not None

        # Extract key fields from raw data for easier access
        if event.raw_data:
            enriched["key_fields"] = self._extract_key_fields(event.raw_data)

        return enriched

    def _validate_event_completeness(self, event: SecurityEvent) -> Dict[str, Any]:
        """Validate the completeness of a single event."""
        issues = []
        quality_score = 1.0

        # Check required fields
        if not event.event_type:
            issues.append("missing event_type")
            quality_score -= 0.2

        if not event.description:
            issues.append("missing description")
            quality_score -= 0.1

        if not event.source.source_type or event.source.source_type == "unknown":
            issues.append("unknown source_type")
            quality_score -= 0.1

        # Check data quality
        if not event.raw_data:
            issues.append("no raw data")
            quality_score -= 0.2

        if not event.affected_resources:
            issues.append("no affected resources")
            quality_score -= 0.1

        if not event.actor:
            issues.append("no actor identified")
            quality_score -= 0.1

        return {
            "is_complete": len(issues) == 0,
            "issues": issues,
            "quality_score": max(0.0, quality_score),
        }

    def _extract_key_fields(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract important fields from raw event data."""
        key_fields = {}

        # Common important fields to extract
        important_keys = [
            "ip_address",
            "source_ip",
            "destination_ip",
            "user",
            "username",
            "principal",
            "action",
            "operation",
            "method",
            "resource",
            "target",
            "object",
            "result",
            "status",
            "outcome",
            "error",
            "error_code",
            "error_message",
        ]

        for key in important_keys:
            if key in raw_data:
                key_fields[key] = raw_data[key]

        return key_fields

    def _get_unique_event_types(self, events: List[SecurityEvent]) -> Set[str]:
        """Get unique event types from a list of events."""
        return {event.event_type for event in events if event.event_type}

    def _get_unique_sources(self, events: List[SecurityEvent]) -> Set[str]:
        """Get unique event sources from a list of events."""
        sources = set()
        for event in events:
            source_str = f"{event.source.source_type}:{event.source.source_name}"
            sources.add(source_str)
        return sources

    def _get_all_affected_resources(self, events: List[SecurityEvent]) -> Set[str]:
        """Get all affected resources from a list of events."""
        resources = set()
        for event in events:
            resources.update(event.affected_resources)
        return resources

    def _get_unique_actors(self, events: List[SecurityEvent]) -> Set[str]:
        """Get unique actors from a list of events."""
        return {event.actor for event in events if event.actor}

    def _calculate_severity_distribution(
        self, events: List[SecurityEvent]
    ) -> Dict[str, int]:
        """Calculate the distribution of event severities."""
        distribution = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "informational": 0,
        }

        for event in events:
            distribution[event.severity.value] += 1

        return distribution

    def _get_event_time_range(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """Get the time range of events."""
        if not events:
            return {"start": None, "end": None, "duration_seconds": 0}

        timestamps = [event.timestamp for event in events]
        start_time = min(timestamps)
        end_time = max(timestamps)
        duration = (end_time - start_time).total_seconds()

        return {
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "duration_seconds": duration,
        }
