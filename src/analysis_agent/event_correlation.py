"""
Event correlation functionality for the Analysis Agent.

This module implements various correlation strategies to identify relationships
between security events within an incident.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

from src.common.models import SecurityEvent, SeverityLevel


class EventCorrelator:
    """Handles correlation of security events to identify patterns and relationships."""

    def __init__(self, logger: logging.Logger, correlation_window: int = 3600) -> None:
        """
        Initialize the event correlator.

        Args:
            logger: Logger instance for logging
            correlation_window: Time window in seconds for correlation (default: 1 hour)
        """
        self.logger = logger
        self.correlation_window = correlation_window

    def correlate_events(self, events: list[SecurityEvent]) -> dict[str, Any]:
        """
        Perform comprehensive event correlation analysis.

        Args:
            events: List of security events to correlate

        Returns:
            Dictionary containing correlation results
        """
        if not events:
            return self._empty_correlation_result()

        # Sort events by timestamp for temporal analysis
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Perform different types of correlation
        temporal_patterns = self._temporal_correlation(sorted_events)
        spatial_patterns = self._spatial_correlation(sorted_events)
        causal_patterns = self._causal_correlation(sorted_events)
        actor_patterns = self._actor_correlation(sorted_events)

        # Calculate correlation scores
        correlation_scores = self._calculate_correlation_scores(
            temporal_patterns,
            spatial_patterns,
            causal_patterns,
            actor_patterns,
        )

        # Identify primary events
        primary_events = self._identify_primary_events(
            sorted_events,
            temporal_patterns,
            causal_patterns,
        )

        # Filter relevant events
        relevant_events = self._filter_relevant_events(
            sorted_events,
            correlation_scores,
        )

        correlation_result = {
            "total_events": len(events),
            "correlation_window_seconds": self.correlation_window,
            "temporal_patterns": temporal_patterns,
            "spatial_patterns": spatial_patterns,
            "causal_patterns": causal_patterns,
            "actor_patterns": actor_patterns,
            "correlation_scores": correlation_scores,
            "primary_events": primary_events,
            "relevant_events": relevant_events,
            "correlation_summary": self._generate_correlation_summary(
                temporal_patterns,
                spatial_patterns,
                causal_patterns,
                actor_patterns,
            ),
        }

        self.logger.info(
            "Event correlation completed: %d events analyzed, %d primary events identified",
            len(events),
            len(primary_events),
        )

        return correlation_result

    def _temporal_correlation(self, events: list[SecurityEvent]) -> dict[str, Any]:
        """Analyze temporal patterns in events."""
        patterns: dict[str, Any] = {
            "event_clusters": [],
            "time_gaps": [],
            "burst_periods": [],
            "event_frequency": {},
            "temporal_sequence": [],
        }

        min_events_for_correlation = 2
        if len(events) < min_events_for_correlation:
            return patterns

        self._identify_event_clusters(events, patterns)
        self._identify_burst_periods(events, patterns)
        self._calculate_event_frequency(events, patterns)
        self._build_temporal_sequence(events, patterns)

        return patterns

    def _identify_event_clusters(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Identify event clusters (events happening close together)."""
        cluster_threshold = timedelta(seconds=300)  # 5 minutes
        current_cluster = [events[0]]

        for i in range(1, len(events)):
            time_diff = events[i].timestamp - events[i - 1].timestamp

            if time_diff <= cluster_threshold:
                current_cluster.append(events[i])
            else:
                self._add_cluster_if_valid(current_cluster, patterns)
                self._record_time_gap(events[i - 1], events[i], time_diff, patterns)
                current_cluster = [events[i]]

        # Handle last cluster
        self._add_cluster_if_valid(current_cluster, patterns)

    def _add_cluster_if_valid(
        self, cluster: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Add cluster to patterns if it has more than one event."""
        if len(cluster) > 1:
            patterns["event_clusters"].append(
                {
                    "start_time": cluster[0].timestamp.isoformat(),
                    "end_time": cluster[-1].timestamp.isoformat(),
                    "event_count": len(cluster),
                    "event_types": list({e.event_type for e in cluster}),
                },
            )

    def _record_time_gap(
        self,
        before_event: SecurityEvent,
        after_event: SecurityEvent,
        time_diff: timedelta,
        patterns: dict[str, Any],
    ) -> None:
        """Record time gap between events."""
        patterns["time_gaps"].append(
            {
                "gap_seconds": time_diff.total_seconds(),
                "before_event": before_event.event_id,
                "after_event": after_event.event_id,
            },
        )

    def _identify_burst_periods(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Identify burst periods (high frequency of events)."""
        time_buckets: defaultdict[datetime, int] = defaultdict(int)
        for event in events:
            bucket = event.timestamp.replace(second=0, microsecond=0)
            time_buckets[bucket] += 1

        avg_events_per_minute = len(events) / max(1, len(time_buckets))
        burst_threshold = avg_events_per_minute * 2

        for bucket, count in time_buckets.items():
            if count >= burst_threshold:
                patterns["burst_periods"].append(
                    {
                        "timestamp": bucket.isoformat(),
                        "event_count": count,
                        "intensity": count / avg_events_per_minute,
                    },
                )

    def _calculate_event_frequency(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Calculate event frequency by type."""
        type_frequency = defaultdict(list)
        for event in events:
            type_frequency[event.event_type].append(event.timestamp)

        for event_type, timestamps in type_frequency.items():
            patterns["event_frequency"][event_type] = {
                "count": len(timestamps),
                "first_occurrence": min(timestamps).isoformat(),
                "last_occurrence": max(timestamps).isoformat(),
            }

    def _build_temporal_sequence(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Build temporal sequence of events."""
        patterns["temporal_sequence"] = [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in events[:20]  # Limit to first 20 for readability
        ]

    def _spatial_correlation(self, events: list[SecurityEvent]) -> dict[str, Any]:
        """Analyze spatial patterns (resource-based correlations)."""
        patterns: dict[str, Any] = {
            "resource_clusters": {},
            "resource_access_patterns": {},
            "cross_resource_activity": [],
            "resource_targeting": {},
        }

        resource_events = self._group_events_by_resources(events)
        self._analyze_resource_clusters(resource_events, patterns)
        self._identify_resource_access_patterns(events, patterns)
        self._identify_cross_resource_activity(events, patterns)
        self._analyze_resource_targeting(events, patterns)
        self._detect_lateral_movement(events, patterns)

        return patterns

    def _group_events_by_resources(
        self, events: list[SecurityEvent]
    ) -> defaultdict[str, list[SecurityEvent]]:
        """Group events by affected resources."""
        resource_events: defaultdict[str, list[SecurityEvent]] = defaultdict(list)
        for event in events:
            for resource in event.affected_resources:
                resource_events[resource].append(event)

            # Also consider source resources
            if event.source.resource_name:
                resource_key = (
                    f"{event.source.resource_type}:{event.source.resource_name}"
                )
                resource_events[resource_key].append(event)
        return resource_events

    def _analyze_resource_clusters(
        self,
        resource_events: defaultdict[str, list[SecurityEvent]],
        patterns: dict[str, Any],
    ) -> None:
        """Analyze resource clusters (multiple events on same resource)."""
        for resource, res_events in resource_events.items():
            if len(res_events) > 1:
                patterns["resource_clusters"][resource] = {
                    "event_count": len(res_events),
                    "event_types": list({e.event_type for e in res_events}),
                    "severity_levels": list({e.severity.value for e in res_events}),
                    "time_span_seconds": (
                        res_events[-1].timestamp - res_events[0].timestamp
                    ).total_seconds(),
                }

    def _identify_resource_access_patterns(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Identify resource access patterns."""
        source_target_pairs: defaultdict[tuple[str, str], int] = defaultdict(int)
        for event in events:
            if event.source.resource_name and event.affected_resources:
                source = f"{event.source.resource_type}:{event.source.resource_name}"
                for target in event.affected_resources:
                    source_target_pairs[(source, target)] += 1

        patterns["resource_access_patterns"] = [
            {"source": source, "target": target, "access_count": count}
            for (source, target), count in source_target_pairs.items()
            if count > 1
        ]

    def _identify_cross_resource_activity(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Identify cross-resource activity."""
        for event in events:
            if len(event.affected_resources) > 1:
                patterns["cross_resource_activity"].append(
                    {
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "resource_count": len(event.affected_resources),
                        "resources": event.affected_resources[
                            :10
                        ],  # Limit for readability
                    },
                )

    def _analyze_resource_targeting(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Analyze resource targeting (which resources are most affected)."""
        resource_impact: defaultdict[str, dict[str, int]] = defaultdict(
            lambda: {"events": 0, "severity_sum": 0},
        )
        severity_weights = {
            SeverityLevel.CRITICAL: 5,
            SeverityLevel.HIGH: 4,
            SeverityLevel.MEDIUM: 3,
            SeverityLevel.LOW: 2,
            SeverityLevel.INFORMATIONAL: 1,
        }

        for event in events:
            weight = severity_weights.get(event.severity, 1)
            for resource in event.affected_resources:
                resource_impact[resource]["events"] += 1
                resource_impact[resource]["severity_sum"] += weight

        # Sort by impact score
        sorted_targets = sorted(
            resource_impact.items(),
            key=lambda x: x[1]["severity_sum"],
            reverse=True,
        )[
            :10
        ]  # Top 10 targeted resources

        patterns["resource_targeting"] = {
            resource: {
                "event_count": data["events"],
                "impact_score": data["severity_sum"],
            }
            for resource, data in sorted_targets
        }

    def _causal_correlation(self, events: list[SecurityEvent]) -> dict[str, Any]:
        """Analyze causal patterns (action-based correlations)."""
        patterns: dict[str, Any] = {
            "action_sequences": [],
            "cause_effect_pairs": [],
            "action_chains": [],
            "common_patterns": {},
        }

        self._find_cause_effect_pairs(events, patterns)
        self._identify_action_sequences(events, patterns)
        self._identify_common_patterns(events, patterns)
        self._detect_special_patterns(events, patterns)
        self._detect_attack_chains(events, patterns)

        return patterns

    def _get_cause_effect_rules(self) -> dict[str, list[str]]:
        """Define common cause-effect relationships."""
        return {
            "failed_login": [
                "account_locked",
                "privilege_escalation",
                "unauthorized_access",
            ],
            "permission_change": ["unauthorized_access", "data_exfiltration"],
            "firewall_rule_change": ["network_intrusion", "port_scan"],
            "user_creation": ["privilege_escalation", "unauthorized_access"],
            "configuration_change": ["service_disruption", "security_misconfiguration"],
        }

    def _find_cause_effect_pairs(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Look for cause-effect pairs in events."""
        cause_effect_rules = self._get_cause_effect_rules()

        for i in range(len(events) - 1):
            current_event = events[i]

            # Check next few events for potential effects
            for j in range(i + 1, min(i + 5, len(events))):
                next_event = events[j]
                time_diff = (
                    next_event.timestamp - current_event.timestamp
                ).total_seconds()

                # Only consider events within 30 minutes
                if time_diff > 1800:
                    break

                self._check_cause_effect_relationship(
                    current_event, next_event, time_diff, cause_effect_rules, patterns
                )

    def _check_cause_effect_relationship(
        self,
        current_event: SecurityEvent,
        next_event: SecurityEvent,
        time_diff: float,
        cause_effect_rules: dict[str, list[str]],
        patterns: dict[str, Any],
    ) -> None:
        """Check if two events have a cause-effect relationship."""
        for cause_type, effect_types in cause_effect_rules.items():
            if cause_type in current_event.event_type.lower() and any(
                effect in next_event.event_type.lower() for effect in effect_types
            ):
                patterns["cause_effect_pairs"].append(
                    {
                        "cause_event": {
                            "id": current_event.event_id,
                            "type": current_event.event_type,
                            "timestamp": current_event.timestamp.isoformat(),
                        },
                        "effect_event": {
                            "id": next_event.event_id,
                            "type": next_event.event_type,
                            "timestamp": next_event.timestamp.isoformat(),
                        },
                        "time_delay_seconds": time_diff,
                    },
                )

    def _identify_action_sequences(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Identify action sequences (consecutive related actions)."""
        current_sequence: list[SecurityEvent] = []
        for event in events:
            if not current_sequence:
                current_sequence.append(event)
            else:
                # Check if this event is related to the sequence
                time_diff = (
                    event.timestamp - current_sequence[-1].timestamp
                ).total_seconds()

                # Consider same actor or same resource as related
                is_related = time_diff < 300 and (  # Within 5 minutes
                    event.actor == current_sequence[-1].actor
                    or bool(
                        set(event.affected_resources)
                        & set(current_sequence[-1].affected_resources),
                    )
                )

                if is_related:
                    current_sequence.append(event)
                else:
                    self._add_action_sequence(current_sequence, patterns)
                    current_sequence = [event]

        # Handle last sequence
        self._add_action_sequence(current_sequence, patterns)

    def _add_action_sequence(
        self, sequence: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Add an action sequence to patterns if it's long enough."""
        if len(sequence) > 2:
            patterns["action_sequences"].append(
                {
                    "sequence_length": len(sequence),
                    "duration_seconds": (
                        sequence[-1].timestamp - sequence[0].timestamp
                    ).total_seconds(),
                    "events": [
                        {"id": e.event_id, "type": e.event_type, "actor": e.actor}
                        for e in sequence
                    ],
                },
            )

    def _identify_common_patterns(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Identify common action patterns."""
        action_pairs: defaultdict[tuple[str, str], int] = defaultdict(int)
        for i in range(len(events) - 1):
            if (events[i + 1].timestamp - events[i].timestamp).total_seconds() < 600:
                pair = (events[i].event_type, events[i + 1].event_type)
                action_pairs[pair] += 1

        patterns["common_patterns"] = {
            f"{pair[0]} -> {pair[1]}": count
            for pair, count in action_pairs.items()
            if count > 1
        }

    def _actor_correlation(self, events: list[SecurityEvent]) -> dict[str, Any]:
        """Analyze actor-based patterns (user behavior correlations)."""
        patterns: dict[str, Any] = {
            "actor_activity": {},
            "multi_actor_resources": {},
            "actor_collaboration": [],
            "suspicious_actors": [],
        }

        actor_events = self._group_events_by_actor(events)
        self._analyze_actor_activities(actor_events, patterns)
        self._identify_multi_actor_resources(events, patterns)
        self._detect_actor_collaboration(events, patterns)

        return patterns

    def _group_events_by_actor(
        self, events: list[SecurityEvent]
    ) -> defaultdict[str, list[SecurityEvent]]:
        """Group events by actor."""
        actor_events: defaultdict[str, list[SecurityEvent]] = defaultdict(list)
        for event in events:
            if event.actor:
                actor_events[event.actor].append(event)
        return actor_events

    def _analyze_actor_activities(
        self,
        actor_events: defaultdict[str, list[SecurityEvent]],
        patterns: dict[str, Any],
    ) -> None:
        """Analyze each actor's activity."""
        for actor, actor_event_list in actor_events.items():
            actor_data = self._build_actor_data(actor_event_list)
            patterns["actor_activity"][actor] = actor_data

            if self._is_actor_suspicious(actor_data):
                patterns["suspicious_actors"].append(
                    {
                        "actor": actor,
                        "reasons": self._get_suspicion_reasons(actor_data),
                    },
                )

    def _build_actor_data(
        self, actor_event_list: list[SecurityEvent]
    ) -> dict[str, Any]:
        """Build actor data from their events."""
        severity_distribution: dict[str, int] = defaultdict(int)
        resources_accessed: set[str] = set()

        # Calculate severity distribution and resources
        for event in actor_event_list:
            severity_distribution[event.severity.value] += 1
            resources_accessed.update(event.affected_resources)

        actor_data: dict[str, Any] = {
            "event_count": len(actor_event_list),
            "event_types": list(set(e.event_type for e in actor_event_list)),
            "severity_distribution": dict(severity_distribution),
            "resources_accessed": list(resources_accessed),
            "time_span_seconds": 0,
            "activity_periods": [],
        }

        # Calculate time span
        if len(actor_event_list) > 1:
            actor_data["time_span_seconds"] = (
                actor_event_list[-1].timestamp - actor_event_list[0].timestamp
            ).total_seconds()

        # Identify activity periods
        if len(actor_event_list) > 2:
            actor_data["activity_periods"] = self._calculate_activity_periods(
                actor_event_list
            )

        return actor_data

    def _calculate_activity_periods(
        self, actor_event_list: list[SecurityEvent]
    ) -> list[dict[str, Any]]:
        """Calculate activity periods for an actor."""
        periods = []
        period_start = actor_event_list[0].timestamp
        last_time = actor_event_list[0].timestamp

        for event in actor_event_list[1:]:
            if (event.timestamp - last_time).total_seconds() > 1800:  # 30 min gap
                periods.append(
                    {
                        "start": period_start.isoformat(),
                        "end": last_time.isoformat(),
                        "duration_seconds": (last_time - period_start).total_seconds(),
                    },
                )
                period_start = event.timestamp
            last_time = event.timestamp

        # Add last period
        periods.append(
            {
                "start": period_start.isoformat(),
                "end": last_time.isoformat(),
                "duration_seconds": (last_time - period_start).total_seconds(),
            },
        )

        return periods

    def _is_actor_suspicious(self, actor_data: dict[str, Any]) -> bool:
        """Check if an actor's activity is suspicious."""
        return (
            actor_data["event_count"] > 10
            or actor_data["severity_distribution"].get("critical", 0) > 0
            or actor_data["severity_distribution"].get("high", 0) > 2
            or len(actor_data["resources_accessed"]) > 20
        )

    def _identify_multi_actor_resources(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Identify resources accessed by multiple actors."""
        resource_actors = defaultdict(set)
        for event in events:
            if event.actor:
                for resource in event.affected_resources:
                    resource_actors[resource].add(event.actor)

        for resource, actors in resource_actors.items():
            if len(actors) > 1:
                patterns["multi_actor_resources"][resource] = list(actors)

    def _detect_actor_collaboration(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Look for potential actor collaboration."""
        actor_pairs: defaultdict[tuple[str, str], int] = defaultdict(int)
        time_window = timedelta(minutes=5)

        for i, event_i in enumerate(events):
            if not event_i.actor:
                continue

            for j in range(i + 1, len(events)):
                if not events[j].actor or events[j].actor == event_i.actor:
                    continue

                if events[j].timestamp - event_i.timestamp > time_window:
                    break

                self._check_actor_collaboration(event_i, events[j], actor_pairs)

        patterns["actor_collaboration"] = [
            {"actors": list(pair), "interaction_count": count}
            for pair, count in actor_pairs.items()
            if count > 1
        ]

    def _check_actor_collaboration(
        self,
        event_i: SecurityEvent,
        event_j: SecurityEvent,
        actor_pairs: defaultdict[tuple[str, str], int],
    ) -> None:
        """Check if two events show actor collaboration."""
        # Check if they're working on same resources
        common_resources = set(event_i.affected_resources) & set(
            event_j.affected_resources,
        )

        if common_resources and event_i.actor and event_j.actor:
            actor1 = event_i.actor
            actor2 = event_j.actor
            if actor1 is not None and actor2 is not None:
                sorted_actors = sorted([actor1, actor2])
                if len(sorted_actors) == 2:
                    pair = (sorted_actors[0], sorted_actors[1])
                    actor_pairs[pair] += 1

    def _get_suspicion_reasons(self, actor_data: dict[str, Any]) -> list[str]:
        """Determine reasons why an actor is suspicious."""
        reasons = []

        if actor_data["event_count"] > 10:
            reasons.append(f"High activity volume ({actor_data['event_count']} events)")

        if actor_data["severity_distribution"].get("critical", 0) > 0:
            reasons.append(
                f"Critical severity events ({actor_data['severity_distribution']['critical']})",
            )

        if actor_data["severity_distribution"].get("high", 0) > 2:
            reasons.append(
                f"Multiple high severity events ({actor_data['severity_distribution']['high']})",
            )

        if len(actor_data["resources_accessed"]) > 20:
            reasons.append(
                f"Accessed many resources ({len(actor_data['resources_accessed'])})",
            )

        if (
            actor_data["time_span_seconds"] > 0
            and actor_data["time_span_seconds"] < 300
        ):
            reasons.append("Rapid burst of activity")

        return reasons

    def _calculate_correlation_scores(
        self,
        temporal: dict[str, Any],
        spatial: dict[str, Any],
        causal: dict[str, Any],
        actor: dict[str, Any],
    ) -> dict[str, float]:
        """Calculate correlation strength scores."""
        scores = {
            "temporal_score": 0.0,
            "spatial_score": 0.0,
            "causal_score": 0.0,
            "actor_score": 0.0,
            "overall_score": 0.0,
        }

        scores["temporal_score"] = self._calculate_temporal_score(temporal)
        scores["spatial_score"] = self._calculate_spatial_score(spatial)
        scores["causal_score"] = self._calculate_causal_score(causal)
        scores["actor_score"] = self._calculate_actor_score(actor)
        scores["overall_score"] = self._calculate_overall_score(scores)

        # Ensure all scores are between 0 and 1
        for key in scores:
            scores[key] = min(1.0, max(0.0, scores[key]))

        return scores

    def _calculate_temporal_score(self, temporal: dict[str, Any]) -> float:
        """Calculate temporal correlation score."""
        score = 0.0
        if temporal["event_clusters"]:
            score += 0.3
        if temporal["burst_periods"]:
            score += 0.4
        if len(temporal["event_frequency"]) > 3:
            score += 0.3
        return score

    def _calculate_spatial_score(self, spatial: dict[str, Any]) -> float:
        """Calculate spatial correlation score."""
        score = 0.0
        if len(spatial["resource_clusters"]) > 2:
            score += 0.3
        if spatial["resource_access_patterns"]:
            score += 0.3
        if spatial["cross_resource_activity"]:
            score += 0.2
        if spatial["resource_targeting"]:
            score += 0.2
        return score

    def _calculate_causal_score(self, causal: dict[str, Any]) -> float:
        """Calculate causal correlation score."""
        score = 0.0
        if causal["cause_effect_pairs"]:
            score += 0.4
        if causal["action_sequences"]:
            score += 0.4
        if len(causal["common_patterns"]) > 2:
            score += 0.2
        return score

    def _calculate_actor_score(self, actor: dict[str, Any]) -> float:
        """Calculate actor correlation score."""
        score = 0.0
        if actor["suspicious_actors"]:
            score += 0.4
        if actor["multi_actor_resources"]:
            score += 0.3
        if actor["actor_collaboration"]:
            score += 0.3
        return score

    def _calculate_overall_score(self, scores: dict[str, float]) -> float:
        """Calculate overall score (weighted average)."""
        weights = {
            "temporal_score": 0.25,
            "spatial_score": 0.25,
            "causal_score": 0.3,
            "actor_score": 0.2,
        }
        return sum(scores[key] * weight for key, weight in weights.items())

    def _identify_primary_events(
        self,
        events: list[SecurityEvent],
        temporal: dict[str, Any],
        causal: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Identify the most important events in the incident."""
        event_scores = self._score_events(events, temporal, causal)
        return self._select_top_events(events, event_scores)

    def _score_events(
        self,
        events: list[SecurityEvent],
        temporal: dict[str, Any],
        causal: dict[str, Any],
    ) -> defaultdict[str, float]:
        """Score events based on various factors."""
        event_scores: defaultdict[str, float] = defaultdict(float)

        # Score based on severity
        self._apply_severity_scores(events, event_scores)

        # Boost score for events that appear as causes
        self._boost_cause_event_scores(causal, event_scores)

        # Boost score for events at the start of sequences
        self._boost_sequence_start_scores(causal, event_scores)

        # Boost score for events in burst periods
        self._boost_burst_period_scores(events, temporal, event_scores)

        return event_scores

    def _apply_severity_scores(
        self, events: list[SecurityEvent], event_scores: defaultdict[str, float]
    ) -> None:
        """Apply scores based on event severity."""
        severity_weights = {
            SeverityLevel.CRITICAL: 1.0,
            SeverityLevel.HIGH: 0.8,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.LOW: 0.3,
            SeverityLevel.INFORMATIONAL: 0.1,
        }

        for event in events:
            event_scores[event.event_id] = severity_weights.get(event.severity, 0.1)

    def _boost_cause_event_scores(
        self, causal: dict[str, Any], event_scores: defaultdict[str, float]
    ) -> None:
        """Boost scores for events that appear as causes."""
        for pair in causal.get("cause_effect_pairs", []):
            cause_id = pair["cause_event"]["id"]
            if cause_id in event_scores:
                event_scores[cause_id] += 0.3

    def _boost_sequence_start_scores(
        self, causal: dict[str, Any], event_scores: defaultdict[str, float]
    ) -> None:
        """Boost scores for events at the start of sequences."""
        for sequence in causal.get("action_sequences", []):
            if sequence["events"]:
                first_event_id = sequence["events"][0]["id"]
                if first_event_id in event_scores:
                    event_scores[first_event_id] += 0.2

    def _boost_burst_period_scores(
        self,
        events: list[SecurityEvent],
        temporal: dict[str, Any],
        event_scores: defaultdict[str, float],
    ) -> None:
        """Boost scores for events in burst periods."""
        burst_times = {
            datetime.fromisoformat(burst["timestamp"])
            for burst in temporal.get("burst_periods", [])
        }

        for event in events:
            event_minute = event.timestamp.replace(second=0, microsecond=0)
            if event_minute in burst_times:
                event_scores[event.event_id] += 0.2

    def _select_top_events(
        self, events: list[SecurityEvent], event_scores: defaultdict[str, float]
    ) -> list[dict[str, Any]]:
        """Select top scoring events."""
        primary_events = []
        sorted_events = sorted(
            events,
            key=lambda e: event_scores[e.event_id],
            reverse=True,
        )

        for event in sorted_events[:5]:  # Top 5 primary events
            if event_scores[event.event_id] > 0.3:  # Minimum threshold
                primary_events.append(
                    {
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "severity": event.severity.value,
                        "timestamp": event.timestamp.isoformat(),
                        "actor": event.actor,
                        "importance_score": event_scores[event.event_id],
                        "description": event.description,
                    },
                )

        return primary_events

    def _filter_relevant_events(
        self,
        events: list[SecurityEvent],
        correlation_scores: dict[str, float],
    ) -> list[str]:
        """Filter events to include only the most relevant ones."""
        if correlation_scores["overall_score"] < 0.3:
            # Low correlation, include all events
            return [e.event_id for e in events]

        relevant_ids = set()

        # Always include high severity events
        for event in events:
            if event.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
                relevant_ids.add(event.event_id)

        # Include events with actors (if actor correlation is high)
        if correlation_scores["actor_score"] > 0.5:
            for event in events:
                if event.actor:
                    relevant_ids.add(event.event_id)

        # Include events with multiple affected resources
        for event in events:
            if len(event.affected_resources) > 2:
                relevant_ids.add(event.event_id)

        return list(relevant_ids)

    def _detect_special_patterns(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Detect special security patterns like data exfiltration and privilege escalation."""
        self._detect_data_exfiltration(events, patterns)
        self._detect_privilege_escalation(events, patterns)

    def _detect_data_exfiltration(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Detect data exfiltration patterns."""
        data_query_events = self._find_data_query_events(events)
        data_transfer_events = self._find_data_transfer_events(events)

        # Check for data exfiltration pattern: large query followed by large transfer
        if data_query_events and data_transfer_events:
            self._check_exfiltration_pattern(
                data_query_events, data_transfer_events, patterns
            )

    def _find_data_query_events(
        self, events: list[SecurityEvent]
    ) -> list[SecurityEvent]:
        """Find events related to data queries."""
        data_query_events = []
        data_access_indicators = ["database_query", "file_access", "data_collection"]

        for event in events:
            event_type_lower = event.event_type.lower()
            if any(
                indicator in event_type_lower for indicator in data_access_indicators
            ):
                if self._is_large_data_access(event):
                    data_query_events.append(event)

        return data_query_events

    def _find_data_transfer_events(
        self, events: list[SecurityEvent]
    ) -> list[SecurityEvent]:
        """Find events related to data transfers."""
        data_transfer_events = []
        transfer_indicators = ["network_traffic", "data_transfer", "file_download"]

        for event in events:
            event_type_lower = event.event_type.lower()
            if any(indicator in event_type_lower for indicator in transfer_indicators):
                if self._is_large_data_transfer(event):
                    data_transfer_events.append(event)

        return data_transfer_events

    def _is_large_data_access(self, event: SecurityEvent) -> bool:
        """Check if event represents large data access."""
        if not event.raw_data:
            return False
        rows = int(event.raw_data.get("rows_returned", 0))
        bytes_read = int(event.raw_data.get("bytes_read", 0))
        return rows > 10000 or bytes_read > 1000000

    def _is_large_data_transfer(self, event: SecurityEvent) -> bool:
        """Check if event represents large data transfer."""
        if not event.raw_data:
            return False
        bytes_sent = int(event.raw_data.get("bytes_sent", 0))
        return bytes_sent > 100000000  # 100MB+

    def _check_exfiltration_pattern(
        self,
        data_query_events: list[SecurityEvent],
        data_transfer_events: list[SecurityEvent],
        patterns: dict[str, Any],
    ) -> None:
        """Check for data exfiltration pattern."""
        for query in data_query_events:
            for transfer in data_transfer_events:
                time_diff = (transfer.timestamp - query.timestamp).total_seconds()
                if 0 <= time_diff <= 1800:  # Within 30 minutes
                    patterns["data_exfiltration_suspected"] = True
                    patterns["exfiltration_details"] = {
                        "query_event": query.event_id,
                        "transfer_event": transfer.event_id,
                        "time_gap_seconds": time_diff,
                    }
                    return

    def _detect_privilege_escalation(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Detect privilege escalation patterns."""
        login_events = self._find_login_events(events)
        privilege_events = self._find_privilege_events(events)
        all_priv_events = self._combine_login_and_privilege_events(
            login_events, privilege_events
        )

        if len(all_priv_events) >= 2:
            self._check_privilege_escalation_pattern(all_priv_events, patterns)

    def _find_login_events(self, events: list[SecurityEvent]) -> list[SecurityEvent]:
        """Find login events."""
        return [e for e in events if "login" in e.event_type.lower()]

    def _find_privilege_events(
        self, events: list[SecurityEvent]
    ) -> list[SecurityEvent]:
        """Find privilege-related events."""
        privilege_indicators = [
            "privilege",
            "permission",
            "role",
            "binding",
            "sudo",
            "admin",
            "root",
            "owner",
            "editor",
        ]
        privilege_events = []

        for event in events:
            event_type_lower = event.event_type.lower()
            if any(indicator in event_type_lower for indicator in privilege_indicators):
                privilege_events.append(event)

        return privilege_events

    def _combine_login_and_privilege_events(
        self,
        login_events: list[SecurityEvent],
        privilege_events: list[SecurityEvent],
    ) -> list[SecurityEvent]:
        """Combine login and privilege events that are related."""
        all_priv_events = []

        # Include login events if followed by privilege events
        if login_events and privilege_events:
            for login in login_events:
                for priv in privilege_events:
                    time_diff = (priv.timestamp - login.timestamp).total_seconds()
                    if 0 <= time_diff <= 3600:  # Within 1 hour
                        if login not in all_priv_events:
                            all_priv_events.append(login)
                        break

        all_priv_events.extend(privilege_events)

        # Remove duplicates by event_id while preserving order
        return self._remove_duplicate_events(all_priv_events)

    def _remove_duplicate_events(
        self, events: list[SecurityEvent]
    ) -> list[SecurityEvent]:
        """Remove duplicate events while preserving order."""
        seen_ids = set()
        unique_events = []
        for event in events:
            if event.event_id not in seen_ids:
                seen_ids.add(event.event_id)
                unique_events.append(event)
        unique_events.sort(key=lambda x: x.timestamp)
        return unique_events

    def _check_privilege_escalation_pattern(
        self, all_priv_events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Check for suspicious privilege escalation patterns."""
        has_escalation = self._has_escalation_pattern(all_priv_events)

        if has_escalation:
            patterns["privilege_escalation_detected"] = True
            patterns["escalation_path"] = [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type,
                    "role": e.raw_data.get("role", "") if e.raw_data else "",
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in all_priv_events
            ]
            patterns["escalation_details"] = {
                "events": [e.event_id for e in all_priv_events],
                "duration_seconds": (
                    all_priv_events[-1].timestamp - all_priv_events[0].timestamp
                ).total_seconds(),
            }

    def _has_escalation_pattern(self, all_priv_events: list[SecurityEvent]) -> bool:
        """Check if events show an escalation pattern."""
        # Look for pattern: low privilege -> attempted/actual high privilege
        for i in range(len(all_priv_events) - 1):
            current = all_priv_events[i]
            next_event = all_priv_events[i + 1]

            if self._is_privilege_escalation(current, next_event):
                return True
        return False

    def _is_privilege_escalation(
        self, current: SecurityEvent, next_event: SecurityEvent
    ) -> bool:
        """Check if two events represent privilege escalation."""
        escalation_indicators = [
            next_event.severity.value > current.severity.value,
            "attempt" in next_event.event_type.lower(),
            "binding" in next_event.event_type.lower(),
        ]

        if next_event.raw_data:
            raw_data_str = str(next_event.raw_data).lower()
            escalation_indicators.extend(
                [
                    "owner" in raw_data_str,
                    "admin" in raw_data_str,
                ]
            )

        return any(escalation_indicators)

    def _detect_lateral_movement(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Detect lateral movement patterns in events."""
        movement_events = self._find_movement_events(events)

        if len(movement_events) >= 2:
            self._analyze_movement_chain(movement_events, patterns)

    def _find_movement_events(
        self, events: list[SecurityEvent]
    ) -> list[dict[str, Any]]:
        """Find events related to lateral movement."""
        movement_indicators = [
            "remote_login",
            "rdp_connection",
            "ssh_connection",
            "lateral_movement",
        ]
        movement_events = []

        for event in events:
            if any(
                indicator in event.event_type.lower()
                for indicator in movement_indicators
            ):
                movement_data = self._extract_movement_data(event)
                if movement_data:
                    movement_events.append(movement_data)

        # Sort by timestamp
        movement_events.sort(key=lambda x: x["timestamp"])
        return movement_events

    def _extract_movement_data(self, event: SecurityEvent) -> Optional[dict[str, Any]]:
        """Extract source and target machines from event."""
        source_machine = None
        target_machine = None

        if event.raw_data:
            source_machine = event.raw_data.get("source_machine")
            target_machine = event.raw_data.get("target_machine")

        # If not in raw_data, try to infer from affected resources
        if (
            not source_machine
            and not target_machine
            and len(event.affected_resources) >= 2
        ):
            # Assume first resource is source, second is target
            source_machine = event.affected_resources[0]
            target_machine = event.affected_resources[1]

        if source_machine and target_machine:
            return {
                "event": event,
                "source": source_machine,
                "target": target_machine,
                "timestamp": event.timestamp,
            }
        return None

    def _analyze_movement_chain(
        self, movement_events: list[dict[str, Any]], patterns: dict[str, Any]
    ) -> None:
        """Analyze movement events to detect chains."""
        movement_path = self._build_movement_path(movement_events)
        is_chain = self._is_movement_chain(movement_events)

        # If it's a proper chain or we have enough movement events, flag it
        if is_chain or len(movement_events) >= 3:
            patterns["lateral_movement_detected"] = True
            patterns["movement_path"] = movement_path
            patterns["movement_events"] = [
                {
                    "event_id": move["event"].event_id,
                    "source": move["source"],
                    "target": move["target"],
                    "timestamp": move["timestamp"].isoformat(),
                }
                for move in movement_events
            ]

    def _build_movement_path(self, movement_events: list[dict[str, Any]]) -> list[str]:
        """Build a path of unique machines involved in movement."""
        movement_path = []
        machines_seen = set()

        for move in movement_events:
            if move["source"] not in machines_seen:
                movement_path.append(move["source"])
                machines_seen.add(move["source"])
            if move["target"] not in machines_seen:
                movement_path.append(move["target"])
                machines_seen.add(move["target"])

        return movement_path

    def _is_movement_chain(self, movement_events: list[dict[str, Any]]) -> bool:
        """Check if movements form a chain (target of one is source of next)."""
        for i in range(len(movement_events) - 1):
            curr_target = movement_events[i]["target"]
            next_source = movement_events[i + 1]["source"]
            # Allow for some flexibility in matching (e.g., instances/vm-001 vs vm-001)
            if not (
                curr_target == next_source
                or curr_target.endswith(f"/{next_source}")
                or next_source.endswith(f"/{curr_target}")
            ):
                return False
        return True

    def _detect_attack_chains(
        self, events: list[SecurityEvent], patterns: dict[str, Any]
    ) -> None:
        """Detect attack chains based on kill chain phases."""
        kill_chain_phases = self._get_kill_chain_phases()
        phase_events = self._map_events_to_phases(events, kill_chain_phases)

        if len(phase_events) >= 2:
            self._analyze_attack_chains(phase_events, patterns)

    def _get_kill_chain_phases(self) -> dict[str, list[str]]:
        """Get kill chain phase mappings."""
        return {
            "reconnaissance": [
                "port_scan",
                "vulnerability_scan",
                "dns_query",
                "network_scan",
            ],
            "initial_access": [
                "successful_login",
                "authentication",
                "access_granted",
                "login",
            ],
            "execution": ["command_execution", "script_run", "process_creation"],
            "persistence": [
                "service_account_created",
                "user_creation",
                "scheduled_task",
                "registry_modification",
            ],
            "privilege_escalation": [
                "privilege_escalation",
                "sudo_command",
                "role_assignment",
            ],
            "defense_evasion": [
                "log_deletion",
                "firewall_rule_change",
                "security_tool_disabled",
            ],
            "credential_access": [
                "password_reset",
                "credential_dump",
                "keylogger_detected",
            ],
            "discovery": [
                "network_discovery",
                "system_enumeration",
                "account_discovery",
            ],
            "lateral_movement": [
                "remote_login",
                "lateral_movement",
                "rdp_connection",
                "ssh_connection",
            ],
            "collection": ["data_collection", "file_access", "database_query"],
            "exfiltration": ["data_exfiltration", "file_download", "data_transfer"],
            "impact": ["service_disruption", "data_deletion", "ransomware_detected"],
        }

    def _map_events_to_phases(
        self, events: list[SecurityEvent], kill_chain_phases: dict[str, list[str]]
    ) -> defaultdict[str, list[SecurityEvent]]:
        """Map events to kill chain phases."""
        phase_events: defaultdict[str, list[SecurityEvent]] = defaultdict(list)
        for event in events:
            event_type_lower = event.event_type.lower()
            for phase, indicators in kill_chain_phases.items():
                if any(indicator in event_type_lower for indicator in indicators):
                    phase_events[phase].append(event)
        return phase_events

    def _analyze_attack_chains(
        self,
        phase_events: defaultdict[str, list[SecurityEvent]],
        patterns: dict[str, Any],
    ) -> None:
        """Analyze phase events to find attack chains."""
        all_chain_events = self._prepare_chain_events(phase_events)
        chains = self._group_events_into_chains(all_chain_events)
        self._add_chains_to_patterns(chains, patterns)

    def _prepare_chain_events(
        self, phase_events: defaultdict[str, list[SecurityEvent]]
    ) -> list[tuple[SecurityEvent, str]]:
        """Prepare events for chain analysis."""
        all_chain_events = []
        for phase, phase_event_list in phase_events.items():
            all_chain_events.extend([(e, phase) for e in phase_event_list])
        all_chain_events.sort(key=lambda x: x[0].timestamp)
        return all_chain_events

    def _group_events_into_chains(
        self, all_chain_events: list[tuple[SecurityEvent, str]]
    ) -> list[list[tuple[SecurityEvent, str]]]:
        """Group events into chains based on time proximity."""
        chains = []
        current_chain: list[tuple[SecurityEvent, str]] = []
        last_time: Optional[datetime] = None

        for event, phase in all_chain_events:
            if not current_chain:
                current_chain.append((event, phase))
                last_time = event.timestamp
            else:
                # last_time is always set when current_chain is not empty
                assert last_time is not None
                time_diff = (event.timestamp - last_time).total_seconds()
                # Group if within 1 hour
                if time_diff <= 3600:
                    current_chain.append((event, phase))
                    last_time = event.timestamp
                else:
                    if len(current_chain) >= 2:
                        chains.append(current_chain)
                    current_chain = [(event, phase)]
                    last_time = event.timestamp

        # Don't forget the last chain
        if len(current_chain) >= 2:
            chains.append(current_chain)

        return chains

    def _add_chains_to_patterns(
        self,
        chains: list[list[tuple[SecurityEvent, str]]],
        patterns: dict[str, Any],
    ) -> None:
        """Add detected chains to patterns."""
        for chain in chains:
            phases_in_chain = list(dict.fromkeys([phase for _, phase in chain]))
            chain_events = [event for event, _ in chain]

            sequence_data = {
                "sequence_length": len(chain),
                "duration_seconds": (
                    chain_events[-1].timestamp - chain_events[0].timestamp
                ).total_seconds(),
                "events": [
                    {
                        "id": e.event_id,
                        "type": e.event_type,
                        "actor": e.actor,
                    }
                    for e in chain_events
                ],
                "phases_identified": ", ".join(phases_in_chain),
            }

            patterns["action_sequences"].append(sequence_data)

    def _generate_correlation_summary(
        self,
        temporal: dict[str, Any],
        spatial: dict[str, Any],
        causal: dict[str, Any],
        actor: dict[str, Any],
    ) -> str:
        """Generate a human-readable summary of correlation findings."""
        summary_parts = []

        # Temporal summary
        if temporal["event_clusters"]:
            summary_parts.append(
                f"Found {len(temporal['event_clusters'])} temporal clusters of events",
            )

        if temporal["burst_periods"]:
            summary_parts.append(
                f"Detected {len(temporal['burst_periods'])} burst periods of high activity",
            )

        # Spatial summary
        if len(spatial["resource_clusters"]) > 0:
            summary_parts.append(
                f"Identified {len(spatial['resource_clusters'])} resources with multiple events",
            )

        # Causal summary
        if causal["cause_effect_pairs"]:
            summary_parts.append(
                f"Found {len(causal['cause_effect_pairs'])} potential cause-effect relationships",
            )

        if causal["action_sequences"]:
            summary_parts.append(
                f"Detected {len(causal['action_sequences'])} sequences of related actions",
            )

        # Actor summary
        if actor["suspicious_actors"]:
            summary_parts.append(
                f"Identified {len(actor['suspicious_actors'])} suspicious actors",
            )

        if actor["actor_collaboration"]:
            summary_parts.append(
                f"Found evidence of collaboration between "
                f"{len(actor['actor_collaboration'])} actor pairs",
            )

        return (
            ". ".join(summary_parts)
            if summary_parts
            else "No significant correlations found"
        )

    def _empty_correlation_result(self) -> dict[str, Any]:
        """Return an empty correlation result structure."""
        return {
            "total_events": 0,
            "correlation_window_seconds": self.correlation_window,
            "temporal_patterns": {},
            "spatial_patterns": {},
            "causal_patterns": {},
            "actor_patterns": {},
            "correlation_scores": {
                "temporal_score": 0.0,
                "spatial_score": 0.0,
                "causal_score": 0.0,
                "actor_score": 0.0,
                "overall_score": 0.0,
            },
            "primary_events": [],
            "relevant_events": [],
            "correlation_summary": "No events to correlate",
        }
