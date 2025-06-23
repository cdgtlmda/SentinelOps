"""
Additional context retrieval for the Analysis Agent.

This module handles fetching related incidents, historical patterns, and
knowledge base information to enhance incident analysis.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from src.common.models import Incident


class ContextRetriever:
    """Retrieves additional context for incident analysis."""

    def __init__(self, db: Any, logger: logging.Logger):
        """
        Initialize the context retriever.

        Args:
            db: Firestore client instance
            logger: Logger instance for logging
        """
        self.db = db
        self.logger = logger
        self.incidents_collection = db.collection("incidents")
        self.knowledge_base_collection = db.collection("knowledge_base")
        self.historical_patterns_collection = db.collection("historical_patterns")

    async def gather_additional_context(
        self, incident: Incident, correlation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Gather comprehensive additional context for the incident.

        Args:
            incident: The incident being analyzed
            correlation_results: Results from event correlation

        Returns:
            Dictionary containing additional context
        """
        context: Dict[str, Any] = {
            "related_incidents": [],
            "historical_patterns": [],
            "knowledge_base_entries": [],
            "similar_incidents": [],
            "threat_intelligence": {},
            "context_summary": "",
        }

        try:
            # Fetch related incidents
            context["related_incidents"] = await self._fetch_related_incidents(
                incident, correlation_results
            )

            # Retrieve historical patterns
            context["historical_patterns"] = await self._retrieve_historical_patterns(
                incident, correlation_results
            )

            # Access knowledge base
            context["knowledge_base_entries"] = await self._query_knowledge_base(
                incident, correlation_results
            )

            # Find similar incidents
            context["similar_incidents"] = await self._find_similar_incidents(incident)

            # Get threat intelligence (if available)
            context["threat_intelligence"] = await self._get_threat_intelligence(
                incident, correlation_results
            )

            # Generate context summary
            context["context_summary"] = self._generate_context_summary(context)

            self.logger.info(
                f"Gathered additional context for incident {incident.incident_id}: "
                f"{len(context['related_incidents'])} related incidents, "
                f"{len(context['similar_incidents'])} similar incidents"
            )

        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error(f"Error gathering additional context: {e}")

        return context

    async def _fetch_related_incidents(  # noqa: C901
        self, incident: Incident, correlation_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch incidents that may be related to the current one."""
        related = []

        try:
            # Get time window (24 hours before and after)
            time_window_start = incident.created_at - timedelta(hours=24)
            time_window_end = incident.created_at + timedelta(hours=24)

            # Extract key identifiers from correlation results
            suspicious_actors = set()
            for actor_info in correlation_results.get("actor_patterns", {}).get(
                "suspicious_actors", []
            ):
                suspicious_actors.add(actor_info.get("actor"))

            affected_resources = set()
            for event in incident.events:
                affected_resources.update(event.affected_resources)

            # Query for related incidents
            query = self.incidents_collection

            # Time-based query
            query = query.where("created_at", ">=", time_window_start)
            query = query.where("created_at", "<=", time_window_end)

            # Execute query
            docs = query.stream()

            for doc in docs:
                if doc.id == incident.incident_id:
                    continue  # Skip the current incident

                incident_data = doc.to_dict()
                if not incident_data:
                    continue

                # Calculate relevance score
                relevance_score = 0.0
                relevance_reasons = []

                # Check for common actors
                incident_actors = set()
                events_data: List[Dict[str, Any]] = incident_data.get("events", [])
                for event_dict in events_data:
                    if event_dict.get("actor"):
                        incident_actors.add(event_dict["actor"])

                common_actors = suspicious_actors & incident_actors
                if common_actors:
                    relevance_score += 0.4
                    relevance_reasons.append(
                        f"Common actors: {', '.join(common_actors)}"
                    )

                # Check for common resources
                incident_resources = set()
                events_data_resources: List[Dict[str, Any]] = incident_data.get(
                    "events", []
                )
                for event_dict in events_data_resources:
                    incident_resources.update(event_dict.get("affected_resources", []))

                common_resources = affected_resources & incident_resources
                if common_resources:
                    relevance_score += 0.3
                    relevance_reasons.append(
                        f"Common resources: {len(common_resources)} shared"
                    )

                # Check for similar event types
                incident_event_types = set()
                events_data_types: List[Dict[str, Any]] = incident_data.get(
                    "events", []
                )
                for event_dict in events_data_types:
                    incident_event_types.add(event_dict.get("event_type"))

                current_event_types = {e.event_type for e in incident.events}
                common_event_types = current_event_types & incident_event_types
                if len(common_event_types) > 2:
                    relevance_score += 0.2
                    relevance_reasons.append("Similar event patterns")

                # Check severity
                if incident_data.get("severity") == incident.severity.value:
                    relevance_score += 0.1

                # Include if relevance score is high enough
                if relevance_score >= 0.3:
                    related.append(
                        {
                            "incident_id": doc.id,
                            "title": incident_data.get("title", ""),
                            "created_at": incident_data.get("created_at"),
                            "severity": incident_data.get("severity"),
                            "status": incident_data.get("status"),
                            "relevance_score": relevance_score,
                            "relevance_reasons": relevance_reasons,
                            "event_count": len(incident_data.get("events", [])),
                        }
                    )

            # Sort by relevance score
            related.sort(key=lambda x: x["relevance_score"], reverse=True)

            # Limit to top 10
            return related[:10]

        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error(f"Error fetching related incidents: {e}")
            return []

    async def _retrieve_historical_patterns(  # noqa: C901
        self, incident: Incident, correlation_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant historical attack patterns."""
        patterns = []

        try:
            # Extract attack indicators
            attack_techniques = []
            event_sequences = []

            # Get attack techniques from events
            for event in incident.events:
                if "attack" in event.event_type.lower():
                    attack_techniques.append(event.event_type)

            # Get event sequences from correlation
            for sequence in correlation_results.get("causal_patterns", {}).get(
                "action_sequences", []
            ):
                event_types = [e["type"] for e in sequence.get("events", [])]
                event_sequences.append(" -> ".join(event_types))

            # Query historical patterns
            if self.historical_patterns_collection:
                # Query by attack techniques
                for technique in attack_techniques[:5]:  # Limit queries
                    query = self.historical_patterns_collection.where(
                        "attack_techniques", "array_contains", technique
                    ).limit(3)

                    for doc in query.stream():
                        pattern_data = doc.to_dict()
                        if pattern_data:
                            patterns.append(
                                {
                                    "pattern_id": doc.id,
                                    "pattern_name": pattern_data.get("name", ""),
                                    "description": pattern_data.get("description", ""),
                                    "attack_techniques": pattern_data.get(
                                        "attack_techniques", []
                                    ),
                                    "typical_duration": pattern_data.get(
                                        "typical_duration", ""
                                    ),
                                    "severity": pattern_data.get("severity", ""),
                                    "countermeasures": pattern_data.get(
                                        "countermeasures", []
                                    ),
                                }
                            )

            # Remove duplicates
            seen_ids = set()
            unique_patterns = []
            for pattern in patterns:
                if pattern["pattern_id"] not in seen_ids:
                    seen_ids.add(pattern["pattern_id"])
                    unique_patterns.append(pattern)

            return unique_patterns[:10]  # Limit to 10 patterns

        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error(f"Error retrieving historical patterns: {e}")
            return []

    async def _query_knowledge_base(  # noqa: C901
        self, incident: Incident, correlation_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Query the knowledge base for relevant information."""
        kb_entries = []

        try:
            # Extract search terms
            search_terms = set()

            # Add event types
            for event in incident.events:
                search_terms.add(event.event_type.lower())

            # Add attack techniques from correlation
            for technique in correlation_results.get("attack_techniques", []):
                search_terms.add(technique.lower())

            # Add resource types
            for event in incident.events:
                if event.source.resource_type:
                    search_terms.add(event.source.resource_type.lower())

            # Query knowledge base
            if self.knowledge_base_collection:
                # Limit search terms to prevent too many queries
                for term in list(search_terms)[:10]:
                    query = self.knowledge_base_collection.where(
                        "tags", "array_contains", term
                    ).limit(3)

                    for doc in query.stream():
                        kb_data = doc.to_dict()
                        if kb_data:
                            kb_entries.append(
                                {
                                    "entry_id": doc.id,
                                    "title": kb_data.get("title", ""),
                                    "category": kb_data.get("category", ""),
                                    "content": kb_data.get("content", "")[
                                        :500
                                    ],  # Truncate
                                    "tags": kb_data.get("tags", []),
                                    "relevance": (
                                        "high"
                                        if term in kb_data.get("tags", [])
                                        else "medium"
                                    ),
                                    "last_updated": kb_data.get("last_updated"),
                                }
                            )

            # Remove duplicates and limit
            seen_ids = set()
            unique_entries = []
            for entry in kb_entries:
                if entry["entry_id"] not in seen_ids:
                    seen_ids.add(entry["entry_id"])
                    unique_entries.append(entry)

            return unique_entries[:10]

        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error(f"Error querying knowledge base: {e}")
            return []

    async def _find_similar_incidents(  # noqa: C901
        self, incident: Incident
    ) -> List[Dict[str, Any]]:
        """Find historically similar incidents based on patterns."""
        similar = []

        try:
            # Create incident signature
            event_types = sorted([e.event_type for e in incident.events])
            severity = incident.severity.value
            resource_types = sorted(
                set(
                    e.source.resource_type
                    for e in incident.events
                    if e.source.resource_type
                )
            )

            # Query for similar incidents (last 90 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)

            query = self.incidents_collection
            query = query.where("created_at", ">=", cutoff_date)
            query = query.where("severity", "==", severity)
            query = query.where("status", "==", "resolved")  # Only resolved incidents
            query = query.limit(50)

            docs = query.stream()

            for doc in docs:
                if doc.id == incident.incident_id:
                    continue

                incident_data = doc.to_dict()
                if not incident_data:
                    continue

                # Calculate similarity score
                similarity_score = 0.0

                # Compare event types
                other_event_types = sorted(
                    [
                        e.get("event_type")
                        for e in incident_data.get("events", [])
                        if e.get("event_type")
                    ]
                )

                # Jaccard similarity for event types
                if event_types and other_event_types:
                    intersection = len(set(event_types) & set(other_event_types))
                    union = len(set(event_types) | set(other_event_types))
                    if union > 0:
                        similarity_score += (intersection / union) * 0.5

                # Compare resource types
                other_resource_types = sorted(
                    set(
                        e.get("source", {}).get("resource_type")
                        for e in incident_data.get("events", [])
                        if e.get("source", {}).get("resource_type")
                    )
                )

                if resource_types and other_resource_types:
                    intersection = len(set(resource_types) & set(other_resource_types))
                    union = len(set(resource_types) | set(other_resource_types))
                    if union > 0:
                        similarity_score += (intersection / union) * 0.3

                # Event count similarity
                event_count_diff = abs(
                    len(incident.events) - len(incident_data.get("events", []))
                )
                if event_count_diff < 5:
                    similarity_score += 0.2
                elif event_count_diff < 10:
                    similarity_score += 0.1

                # Include if similarity is high enough
                if similarity_score >= 0.4:
                    similar.append(
                        {
                            "incident_id": doc.id,
                            "title": incident_data.get("title", ""),
                            "created_at": incident_data.get("created_at"),
                            "resolved_at": incident_data.get("updated_at"),
                            "similarity_score": similarity_score,
                            "event_count": len(incident_data.get("events", [])),
                            "resolution_notes": incident_data.get(
                                "resolution_notes", ""
                            )[:200],
                        }
                    )

            # Sort by similarity score
            similar.sort(key=lambda x: x["similarity_score"], reverse=True)

            return similar[:5]  # Top 5 similar incidents

        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error(f"Error finding similar incidents: {e}")
            return []

    async def _get_threat_intelligence(  # noqa: C901
        self, incident: Incident, correlation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get threat intelligence information."""
        threat_intel: Dict[str, Any] = {
            "indicators_of_compromise": [],
            "threat_actors": [],
            "ttps": [],  # Tactics, Techniques, and Procedures
            "risk_assessment": "",
        }

        try:
            # Extract IoCs from events
            for event in incident.events:
                # IP addresses
                if "ip_address" in event.raw_data:
                    threat_intel["indicators_of_compromise"].append(
                        {
                            "type": "ip",
                            "value": event.raw_data["ip_address"],
                            "context": f"From event: {event.event_type}",
                        }
                    )

                # Domains
                if "domain" in event.raw_data:
                    threat_intel["indicators_of_compromise"].append(
                        {
                            "type": "domain",
                            "value": event.raw_data["domain"],
                            "context": f"From event: {event.event_type}",
                        }
                    )

                # File hashes
                for key in ["file_hash", "md5", "sha256"]:
                    if key in event.raw_data:
                        threat_intel["indicators_of_compromise"].append(
                            {
                                "type": "hash",
                                "value": event.raw_data[key],
                                "context": f"From event: {event.event_type}",
                            }
                        )

            # Extract threat actors from correlation
            for actor_info in correlation_results.get("actor_patterns", {}).get(
                "suspicious_actors", []
            ):
                threat_intel["threat_actors"].append(
                    {
                        "actor": actor_info.get("actor"),
                        "reasons": actor_info.get("reasons", []),
                        "risk_level": (
                            "high"
                            if len(actor_info.get("reasons", [])) > 2
                            else "medium"
                        ),
                    }
                )

            # Map to MITRE ATT&CK TTPs
            attack_mapping = {
                "unauthorized_access": [
                    "T1078",
                    "T1133",
                ],  # Valid Accounts, External Remote Services
                "privilege_escalation": [
                    "T1068",
                    "T1055",
                ],  # Exploitation, Process Injection
                "data_exfiltration": [
                    "T1041",
                    "T1048",
                ],  # Exfiltration Over C2, Alternative Protocol
                "persistence": ["T1053", "T1136"],  # Scheduled Task, Create Account
                "lateral_movement": [
                    "T1021",
                    "T1080",
                ],  # Remote Services, Taint Shared Content
            }

            for event in incident.events:
                event_lower = event.event_type.lower()
                for pattern, ttps in attack_mapping.items():
                    if pattern in event_lower:
                        threat_intel["ttps"].extend(ttps)

            # Remove duplicates
            threat_intel["ttps"] = list(set(threat_intel["ttps"]))

            # Risk assessment
            risk_factors = []
            if len(threat_intel["threat_actors"]) > 0:
                risk_factors.append("Suspicious actors identified")
            if len(threat_intel["indicators_of_compromise"]) > 5:
                risk_factors.append("Multiple IoCs detected")
            if (
                correlation_results.get("correlation_scores", {}).get(
                    "overall_score", 0
                )
                > 0.7
            ):
                risk_factors.append(
                    "High correlation score indicates coordinated attack"
                )

            if risk_factors:
                threat_intel["risk_assessment"] = "HIGH RISK: " + "; ".join(
                    risk_factors
                )
            else:
                threat_intel["risk_assessment"] = (
                    "MODERATE RISK: Standard security incident"
                )

        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error(f"Error getting threat intelligence: {e}")

        return threat_intel

    def _generate_context_summary(self, context: Dict[str, Any]) -> str:
        """Generate a summary of the additional context."""
        summary_parts = []

        # Related incidents
        if context["related_incidents"]:
            summary_parts.append(
                f"Found {len(context['related_incidents'])} related incidents "
                f"with similar patterns"
            )

        # Similar historical incidents
        if context["similar_incidents"]:
            summary_parts.append(
                f"Identified {len(context['similar_incidents'])} historically similar "
                f"incidents for reference"
            )

        # Historical patterns
        if context["historical_patterns"]:
            pattern_names = [
                p["pattern_name"] for p in context["historical_patterns"][:3]
            ]
            summary_parts.append(
                f"Matches historical attack patterns: {', '.join(pattern_names)}"
            )

        # Knowledge base
        if context["knowledge_base_entries"]:
            summary_parts.append(
                f"Found {len(context['knowledge_base_entries'])} relevant "
                f"knowledge base articles"
            )

        # Threat intelligence
        threat_intel = context.get("threat_intelligence", {})
        if threat_intel.get("indicators_of_compromise"):
            summary_parts.append(
                f"Extracted {len(threat_intel['indicators_of_compromise'])} IoCs"
            )

        if threat_intel.get("threat_actors"):
            summary_parts.append(
                f"Identified {len(threat_intel['threat_actors'])} suspicious actors"
            )

        return (
            ". ".join(summary_parts) if summary_parts else "No additional context found"
        )

    def _calculate_risk_score(self, incident: Incident) -> float:
        """Calculate risk score for an incident."""
        # Base score based on severity
        severity_scores = {"low": 2.5, "medium": 5.0, "high": 7.5, "critical": 10.0}

        base_score = severity_scores.get(incident.severity.value, 5.0)

        # Additional factors can be added here
        return base_score

    def _classify_risk_category(self, risk_score: float) -> str:
        """Classify risk based on score."""
        if risk_score >= 8.0:
            return "CRITICAL"
        elif risk_score >= 6.0:
            return "HIGH"
        elif risk_score >= 4.0:
            return "MEDIUM"
        else:
            return "LOW"

    def _calculate_composite_risk(self, factors: Dict[str, float]) -> float:
        """Calculate composite risk from multiple factors."""
        if not factors:
            return 0.0

        # Simple weighted average
        total_weight = sum(factors.values())
        if total_weight == 0:
            return 0.0

        return min(total_weight / len(factors), 10.0)

    async def get_additional_context(self, incident: Incident) -> Dict[str, Any]:
        """Get additional context for an incident (alias for gather_additional_context)."""
        # This is an alias for the existing method
        return await self.gather_additional_context(incident, {})
