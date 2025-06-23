"""
Event correlation for the Detection Agent.

This module provides event correlation logic for grouping related security events.
"""

from collections import defaultdict
from datetime import timedelta
from typing import List

from src.common.models import SecurityEvent


class EventCorrelator:
    """Correlates security events to identify related incidents."""

    def __init__(self, correlation_window_minutes: int = 60):
        """
        Initialize the event correlator.

        Args:
            correlation_window_minutes: Time window for correlating events
        """
        self.correlation_window = timedelta(minutes=correlation_window_minutes)

    def correlate_events(
        self,
        events: List[SecurityEvent]
    ) -> List[List[SecurityEvent]]:
        """
        Correlate security events into groups.

        Args:
            events: List of security events to correlate

        Returns:
            List of correlated event groups
        """
        if not events:
            return []

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Group events by correlation criteria
        correlated_groups = []

        # Time-based correlation
        time_groups = self._correlate_by_time(sorted_events)

        # Further correlate each time group by other attributes
        for time_group in time_groups:
            # Correlate by actor
            actor_groups = self._correlate_by_actor(time_group)

            # Correlate by resource
            for actor_group in actor_groups:
                resource_groups = self._correlate_by_resource(actor_group)
                correlated_groups.extend(resource_groups)

        return correlated_groups

    def _correlate_by_time(
        self,
        events: List[SecurityEvent]
    ) -> List[List[SecurityEvent]]:
        """Correlate events that occur within the time window."""
        if not events:
            return []

        groups = []
        current_group = [events[0]]

        for event in events[1:]:
            # Check if event is within correlation window of the last event in group
            if event.timestamp - current_group[-1].timestamp <= self.correlation_window:
                current_group.append(event)
            else:
                # Start a new group
                groups.append(current_group)
                current_group = [event]

        # Add the last group
        if current_group:
            groups.append(current_group)

        return groups

    def _correlate_by_actor(
        self,
        events: List[SecurityEvent]
    ) -> List[List[SecurityEvent]]:
        """Correlate events by actor."""
        actor_groups = defaultdict(list)

        for event in events:
            actor = event.actor or "unknown"
            actor_groups[actor].append(event)

        return list(actor_groups.values())

    def _correlate_by_resource(
        self,
        events: List[SecurityEvent]
    ) -> List[List[SecurityEvent]]:
        """Correlate events by affected resources."""
        resource_groups = defaultdict(list)

        for event in events:
            # Use the first affected resource as the key
            if event.affected_resources:
                resource = event.affected_resources[0]
            else:
                resource = "unknown"
            resource_groups[resource].append(event)

        return list(resource_groups.values())

    def should_merge_incidents(
        self,
        incident1_events: List[SecurityEvent],
        incident2_events: List[SecurityEvent]
    ) -> bool:
        """
        Determine if two incidents should be merged.

        Args:
            incident1_events: Events from the first incident
            incident2_events: Events from the second incident

        Returns:
            True if incidents should be merged
        """
        if not incident1_events or not incident2_events:
            return False

        # Check time proximity
        latest_event1 = max(incident1_events, key=lambda e: e.timestamp)
        earliest_event2 = min(incident2_events, key=lambda e: e.timestamp)

        if earliest_event2.timestamp - latest_event1.timestamp > self.correlation_window:
            return False

        # Check for common actors
        actors1 = {e.actor for e in incident1_events if e.actor}
        actors2 = {e.actor for e in incident2_events if e.actor}

        if actors1 & actors2:  # Intersection
            return True

        # Check for common resources
        resources1 = {r for e in incident1_events for r in e.affected_resources}
        resources2 = {r for e in incident2_events for r in e.affected_resources}

        if resources1 & resources2:  # Intersection
            return True

        # Check for same event types
        types1 = {e.event_type for e in incident1_events}
        types2 = {e.event_type for e in incident2_events}

        if types1 & types2:  # Intersection
            return True

        return False

    def clear_correlation_cache(self) -> None:
        """Clear all correlation caches and state."""
        if hasattr(self, '_event_cache'):
            self._event_cache.clear()
        if hasattr(self, '_correlation_cache'):
            self._correlation_cache.clear()
        if hasattr(self, '_time_windows'):
            self._time_windows.clear()
