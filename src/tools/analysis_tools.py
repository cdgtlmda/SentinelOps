"""ADK Tool wrappers for analysis agent business logic.

This module provides ADK tool wrappers for the existing analysis
business logic components, allowing them to be used within the ADK framework.
"""

import logging
from typing import Any, Dict, Optional

from src.common.adk_import_fix import BaseTool, ToolContext

# Import existing business logic components
from src.analysis_agent.recommendation_engine import RecommendationEngine
from src.analysis_agent.event_correlation import EventCorrelator
from src.analysis_agent.context_retrieval import ContextRetriever

logger = logging.getLogger(__name__)


class RecommendationTool(BaseTool):
    """ADK tool wrapper for the recommendation engine."""

    def __init__(self, engine: Optional[RecommendationEngine] = None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize the recommendation tool.

        Args:
            engine: Existing recommendation engine instance
            config: Configuration for creating a new engine
        """
        super().__init__(
            name="recommendation_tool",
            description="Generate security recommendations based on incident analysis"
        )

        # config parameter reserved for future configuration options
        _ = config

        # Initialize or use provided recommendation engine
        if engine:
            self.engine = engine
        else:
            self.engine = RecommendationEngine(logger)

    async def execute(self, context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Generate recommendations for security incidents.

        Args:
            context: ADK tool context
            **kwargs: Should contain:
                - incident: Security incident data
                - analysis: Analysis results
                - risk_score: Risk assessment score

        Returns:
            Dictionary with recommendations
        """
        # context parameter required by ADK framework
        _ = context

        try:
            incident = kwargs.get("incident", {})
            analysis = kwargs.get("analysis", {})
            risk_score = kwargs.get("risk_score", 0.5)

            if not incident:
                return {
                    "status": "error",
                    "error": "No incident data provided",
                    "recommendations": []
                }
            # Extract parameters from incident and analysis
            incident_type = incident.get("incident_type", "unknown")
            attack_techniques = analysis.get("attack_techniques", [])
            severity = incident.get("severity", "MEDIUM")
            correlation_results = analysis.get("correlation_results", {})

            # Use the existing recommendation engine
            recommendations = self.engine.generate_recommendations(
                incident_type=incident_type,
                attack_techniques=attack_techniques,
                severity=severity,
                correlation_results=correlation_results,
                custom_context={"risk_score": risk_score}
            )

            return {
                "status": "success",
                "recommendations": recommendations.get("recommendations", []),
                "priority_actions": recommendations.get("priority_actions", []),
                "estimated_time": recommendations.get("estimated_time_minutes", 0),
                "confidence": recommendations.get("confidence", 0.8)
            }

        except (ValueError, KeyError, AttributeError, TypeError) as e:
            logger.error("Error in recommendation engine tool: %s", e, exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "recommendations": []
            }


class CorrelationTool(BaseTool):
    """ADK tool wrapper for advanced event correlation."""

    def __init__(self, correlator: Optional[EventCorrelator] = None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize the correlation tool."""
        super().__init__(
            name="correlation_tool",
            description="Perform advanced pattern detection and event correlation"
        )

        # Initialize or use provided correlator
        if correlator:
            self.correlator = correlator
        else:
            # EventCorrelator expects a logger as first argument
            correlation_window = config.get("correlation_window", 3600) if config else 3600
            self.correlator = EventCorrelator(logger, correlation_window)

    async def execute(self, context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Perform advanced event correlation.

        Args:
            context: ADK tool context
            **kwargs: Should contain:
                - events: List of security events
                - patterns: Known attack patterns to match
                - time_window: Analysis time window

        Returns:
            Dictionary with correlation results
        """
        # context parameter required by ADK framework
        _ = context

        try:
            events = kwargs.get("events", [])

            # Use the existing correlator
            correlation_results = self.correlator.correlate_events(events)
            return {
                "status": "success",
                "attack_patterns": correlation_results.get("patterns_detected", []),
                "attack_chain": correlation_results.get("attack_chain", []),
                "confidence_scores": correlation_results.get("confidence_scores", {}),
                "related_iocs": correlation_results.get("iocs", [])
            }

        except (ValueError, KeyError, AttributeError, TypeError) as e:
            logger.error("Error in advanced correlation tool: %s", e, exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "attack_patterns": []
            }


class ContextTool(BaseTool):
    """ADK tool wrapper for retrieving additional context."""

    def __init__(self, retriever: Optional[ContextRetriever] = None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize the context tool."""
        super().__init__(
            name="context_tool",
            description="Retrieve additional context for security incidents"
        )

        # config parameter reserved for future configuration options
        _ = config

        # Initialize or use provided retriever
        self.retriever: Optional[ContextRetriever] = retriever

    async def execute(self, context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Retrieve additional context for an incident.

        Args:
            context: ADK tool context
            **kwargs: Should contain:
                - incident: Security incident
                - entity: Entity to get context for (IP, user, etc.)
                - context_type: Type of context needed

        Returns:
            Dictionary with context information
        """
        # context parameter required by ADK framework
        _ = context

        try:
            incident = kwargs.get("incident", {})

            if not self.retriever:
                return {
                    "status": "error",
                    "error": "Context retriever not initialized",
                    "context": {}
                }

            # Use the existing context retriever with correct method
            context_data = await self.retriever.get_additional_context(incident)

            return {
                "status": "success",
                "context": context_data.get("context", {}),
                "threat_intelligence": context_data.get("threat_intel", {}),
                "historical_data": context_data.get("history", []),
                "risk_indicators": context_data.get("risk_indicators", [])
            }

        except (ValueError, KeyError, AttributeError, TypeError) as e:
            logger.error("Error in context retriever tool: %s", e, exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "context": {}
            }
