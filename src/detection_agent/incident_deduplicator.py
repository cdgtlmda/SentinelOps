"""
Incident deduplication module for the Detection Agent.

This module provides functionality to detect and merge duplicate incidents.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from src.common.models import Incident, SecurityEvent


class IncidentDeduplicator:
    """Handles incident deduplication and merging."""

    def __init__(self, similarity_threshold: float = 0.8, time_window_hours: int = 24):
        """
        Initialize the incident deduplicator.

        Args:
            similarity_threshold: Minimum similarity score to consider incidents as duplicates
                (0.0-1.0)
            time_window_hours: Time window in hours to look for duplicates
        """
        self.similarity_threshold = similarity_threshold
        self.time_window = timedelta(hours=time_window_hours)

        # Cache for recent incidents to check against
        self._recent_incidents: Dict[str, Incident] = {}
        self._incident_hashes: Dict[str, str] = {}

    def is_duplicate(
        self, new_incident: Incident, existing_incidents: List[Incident]
    ) -> Optional[Incident]:
        """
        Check if a new incident is a duplicate of an existing one.

        Args:
            new_incident: The new incident to check
            existing_incidents: List of existing incidents to compare against

        Returns:
            The existing incident if duplicate found, None otherwise
        """
        # Filter incidents within time window
        cutoff_time = datetime.now(timezone.utc) - self.time_window
        recent_incidents = [
            inc for inc in existing_incidents
            if inc.created_at > cutoff_time
        ]
        # Calculate hash for quick comparison
        new_hash = self._calculate_incident_hash(new_incident)

        # Check for exact hash match first
        for incident in recent_incidents:
            incident_hash = self._incident_hashes.get(
                incident.incident_id,
                self._calculate_incident_hash(incident)
            )
            if incident_hash == new_hash:
                return incident

        # Check for similarity if no exact match
        for incident in recent_incidents:
            similarity_score = self._calculate_similarity(new_incident, incident)
            if similarity_score >= self.similarity_threshold:
                return incident

        return None

    def merge_incidents(self, primary: Incident, duplicate: Incident) -> Incident:
        """
        Merge a duplicate incident into the primary incident.

        Args:
            primary: The primary incident to keep
            duplicate: The duplicate incident to merge

        Returns:
            The merged incident
        """
        # Combine events from both incidents
        merged_events = list(primary.events)

        # Add events from duplicate that aren't already in primary
        existing_event_ids = {e.event_id for e in primary.events}
        for event in duplicate.events:
            if event.event_id not in existing_event_ids:
                merged_events.append(event)

        # Update the primary incident
        primary.events = merged_events

        # Merge tags
        primary.tags = list(set(primary.tags + duplicate.tags))
        # Update severity to the highest of both
        if duplicate.severity > primary.severity:
            primary.severity = duplicate.severity

        # Update description to include information about the merge
        primary.description += (
            f"\n\n[Merged with incident {duplicate.incident_id} "
            f"at {datetime.now(timezone.utc).isoformat()}]"
        )

        # Merge metadata
        primary.metadata["merged_incidents"] = primary.metadata.get("merged_incidents", [])
        primary.metadata["merged_incidents"].append({
            "incident_id": duplicate.incident_id,
            "merged_at": datetime.now(timezone.utc).isoformat(),
            "event_count": len(duplicate.events)
        })

        # Update event count
        primary.metadata["event_count"] = len(primary.events)

        # Update time range
        all_event_times = [e.timestamp for e in primary.events]
        primary.metadata["first_event_time"] = min(all_event_times).isoformat()
        primary.metadata["last_event_time"] = max(all_event_times).isoformat()

        return primary

    def _calculate_incident_hash(self, incident: Incident) -> str:
        """
        Calculate a hash for an incident based on key attributes.

        Args:
            incident: The incident to hash

        Returns:
            Hash string
        """
        # Create hash based on key incident attributes
        hash_components = []

        # Include event types and actors
        for event in incident.events:
            hash_components.append(event.event_type)
            if event.actor:
                hash_components.append(event.actor)
        # Include affected resources
        resources = set()
        for event in incident.events:
            resources.update(event.affected_resources)
        hash_components.extend(sorted(resources))

        # Include detection rule if available
        if "detection_rule" in incident.metadata:
            hash_components.append(incident.metadata["detection_rule"])

        # Create hash
        hash_string = "|".join(hash_components)
        hash_object = hashlib.sha256(hash_string.encode())

        # Cache the hash
        self._incident_hashes[incident.incident_id] = hash_object.hexdigest()

        return hash_object.hexdigest()

    def _calculate_similarity(self, incident1: Incident, incident2: Incident) -> float:
        """
        Calculate similarity score between two incidents.

        Args:
            incident1: First incident
            incident2: Second incident

        Returns:
            Similarity score between 0.0 and 1.0
        """
        scores = []

        # Compare event types
        types1 = {e.event_type for e in incident1.events}
        types2 = {e.event_type for e in incident2.events}
        if types1 or types2:
            type_similarity = len(types1 & types2) / len(types1 | types2)
            scores.append(type_similarity)

        # Compare actors
        actors1 = {e.actor for e in incident1.events if e.actor}
        actors2 = {e.actor for e in incident2.events if e.actor}
        if actors1 or actors2:
            actor_similarity = len(actors1 & actors2) / len(actors1 | actors2)
            scores.append(actor_similarity)

        # Compare affected resources
        resources1 = {r for e in incident1.events for r in e.affected_resources}
        resources2 = {r for e in incident2.events for r in e.affected_resources}
        if resources1 or resources2:
            resource_similarity = len(resources1 & resources2) / len(resources1 | resources2)
            scores.append(resource_similarity)

        # Compare severity
        severity_similarity = 1.0 if incident1.severity == incident2.severity else 0.5
        scores.append(severity_similarity)

        # Compare time proximity
        time_diff = abs((incident1.created_at - incident2.created_at).total_seconds())
        # Score decreases as time difference increases (1 hour = 0.9, 24 hours = 0.1)
        time_similarity = max(0.0, 1.0 - (time_diff / (24 * 3600)))
        scores.append(time_similarity)

        # Compare tags
        tags1 = set(incident1.tags)
        tags2 = set(incident2.tags)
        if tags1 or tags2:
            tag_similarity = len(tags1 & tags2) / len(tags1 | tags2)
            scores.append(tag_similarity)

        # Calculate weighted average
        return sum(scores) / len(scores) if scores else 0.0

    def update_existing_incident(
        self, existing: Incident, new_events: List[SecurityEvent]
    ) -> Incident:
        """
        Update an existing incident with new events.

        Args:
            existing: The existing incident to update
            new_events: New events to add

        Returns:
            The updated incident
        """        # Add new events
        existing_event_ids = {e.event_id for e in existing.events}
        events_added = 0

        for event in new_events:
            if event.event_id not in existing_event_ids:
                existing.events.append(event)
                events_added += 1

        if events_added > 0:
            # Update metadata
            existing.metadata["event_count"] = len(existing.events)
            existing.metadata["last_updated"] = datetime.now(timezone.utc).isoformat()
            existing.metadata["updates"] = existing.metadata.get("updates", 0) + 1

            # Update time range
            all_event_times = [e.timestamp for e in existing.events]
            existing.metadata["first_event_time"] = min(all_event_times).isoformat()
            existing.metadata["last_event_time"] = max(all_event_times).isoformat()

            # Update description
            existing.description += (
                f"\n[Updated with {events_added} new events at "
                f"{datetime.now(timezone.utc).isoformat()}]"
            )

        return existing

    def cleanup_old_incidents(self) -> int:
        """
        Remove old incidents from the deduplication cache.

        Returns:
            Number of incidents removed
        """
        cutoff_time = datetime.now(timezone.utc) - self.time_window
        incidents_to_remove = []

        for incident_id, incident in self._recent_incidents.items():
            if incident.created_at < cutoff_time:
                incidents_to_remove.append(incident_id)

        for incident_id in incidents_to_remove:
            del self._recent_incidents[incident_id]
            if incident_id in self._incident_hashes:
                del self._incident_hashes[incident_id]

        return len(incidents_to_remove)

    def clear_cache(self) -> None:
        """Clear all deduplication caches and state."""
        self._recent_incidents.clear()
        self._incident_hashes.clear()
