"""ADK Agent Routing Configuration for SentinelOps.

This module configures agent routing patterns using Google ADK
to enable proper inter-agent communication and workflow orchestration.
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, cast

from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)


class AgentRoute(Enum):
    """Enum defining available agent routes in SentinelOps."""

    DETECTION_AGENT = "detection_agent"
    ANALYSIS_AGENT = "analysis_agent"
    REMEDIATION_AGENT = "remediation_agent"
    COMMUNICATION_AGENT = "communication_agent"
    ORCHESTRATOR_AGENT = "orchestrator_agent"


class AgentRoutingConfig:
    """Configuration for ADK agent routing patterns."""

    def __init__(self) -> None:
        """Initialize the routing configuration."""
        self.routes: Dict[str, Dict[str, Any]] = {
            AgentRoute.DETECTION_AGENT.value: {
                "name": "Detection Agent",
                "description": "Monitors security logs and detects incidents",
                "can_transfer_to": [
                    AgentRoute.ORCHESTRATOR_AGENT.value,
                    AgentRoute.ANALYSIS_AGENT.value,
                ],
                "accepts_from": [
                    AgentRoute.ORCHESTRATOR_AGENT.value,
                ],
                "priority": 1,
            },
            AgentRoute.ANALYSIS_AGENT.value: {
                "name": "Analysis Agent",
                "description": "Analyzes security incidents using Gemini AI",
                "can_transfer_to": [
                    AgentRoute.ORCHESTRATOR_AGENT.value,
                    AgentRoute.REMEDIATION_AGENT.value,
                    AgentRoute.COMMUNICATION_AGENT.value,
                ],
                "accepts_from": [
                    AgentRoute.ORCHESTRATOR_AGENT.value,
                    AgentRoute.DETECTION_AGENT.value,
                ],
                "priority": 2,
            },
            AgentRoute.REMEDIATION_AGENT.value: {
                "name": "Remediation Agent",
                "description": "Executes remediation actions",
                "can_transfer_to": [
                    AgentRoute.ORCHESTRATOR_AGENT.value,
                    AgentRoute.COMMUNICATION_AGENT.value,
                ],
                "accepts_from": [
                    AgentRoute.ORCHESTRATOR_AGENT.value,
                    AgentRoute.ANALYSIS_AGENT.value,
                ],
                "priority": 3,
            },
            AgentRoute.COMMUNICATION_AGENT.value: {
                "name": "Communication Agent",
                "description": "Handles notifications and reporting",
                "can_transfer_to": [
                    AgentRoute.ORCHESTRATOR_AGENT.value,
                ],
                "accepts_from": [
                    AgentRoute.ORCHESTRATOR_AGENT.value,
                    AgentRoute.ANALYSIS_AGENT.value,
                    AgentRoute.REMEDIATION_AGENT.value,
                ],
                "priority": 4,
            },
            AgentRoute.ORCHESTRATOR_AGENT.value: {
                "name": "Orchestrator Agent",
                "description": "Orchestrates workflow between agents",
                "can_transfer_to": [
                    AgentRoute.DETECTION_AGENT.value,
                    AgentRoute.ANALYSIS_AGENT.value,
                    AgentRoute.REMEDIATION_AGENT.value,
                    AgentRoute.COMMUNICATION_AGENT.value,
                ],
                "accepts_from": [
                    AgentRoute.DETECTION_AGENT.value,
                    AgentRoute.ANALYSIS_AGENT.value,
                    AgentRoute.REMEDIATION_AGENT.value,
                    AgentRoute.COMMUNICATION_AGENT.value,
                ],
                "priority": 0,  # Highest priority
            },
        }

        # Agent instance registry
        self._agent_registry: Dict[str, LlmAgent] = {}

    def register_agent(self, route: str, agent_instance: LlmAgent) -> None:
        """Register an agent instance for routing.

        Args:
            route: The agent route identifier
            agent_instance: The ADK agent instance
        """
        if route not in self.routes:
            raise ValueError(f"Unknown agent route: {route}")

        self._agent_registry[route] = agent_instance
        logger.info("Registered agent '%s' for route '%s'", agent_instance.name, route)

    def get_agent(self, route: str) -> Optional[LlmAgent]:
        """Get a registered agent by route.

        Args:
            route: The agent route identifier

        Returns:
            The registered agent instance or None
        """
        return self._agent_registry.get(route)

    def can_transfer(self, from_route: str, to_route: str) -> bool:
        """Check if transfer is allowed between agents.

        Args:
            from_route: Source agent route
            to_route: Destination agent route

        Returns:
            True if transfer is allowed
        """
        if from_route not in self.routes or to_route not in self.routes:
            return False

        allowed_transfers = self.routes[from_route].get("can_transfer_to", [])
        return to_route in allowed_transfers

    def get_allowed_transfers(self, from_route: str) -> List[str]:
        """Get list of allowed transfer destinations from an agent.

        Args:
            from_route: Source agent route

        Returns:
            List of allowed destination routes
        """
        if from_route not in self.routes:
            return []

        return cast(List[str], self.routes[from_route].get("can_transfer_to", []))

    def get_route_info(self, route: str) -> Dict[str, Any]:
        """Get information about a specific route.

        Args:
            route: The agent route identifier

        Returns:
            Route information dictionary
        """
        return self.routes.get(route, {})

    def validate_routing_integrity(self) -> List[str]:
        """Validate routing configuration integrity.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        for route, config in self.routes.items():
            # Check bidirectional consistency
            for target in config.get("can_transfer_to", []):
                if target in self.routes:
                    accepts_from = self.routes[target].get("accepts_from", [])
                    if route not in accepts_from:
                        errors.append(
                            f"Route '{route}' can transfer to '{target}', "
                            f"but '{target}' does not accept from '{route}'"
                        )

            # Check for orphaned routes
            has_incoming = any(
                route in other_config.get("can_transfer_to", [])
                for other_route, other_config in self.routes.items()
                if other_route != route
            )
            has_outgoing = bool(config.get("can_transfer_to"))

            if (not has_incoming and not has_outgoing and
                    route != AgentRoute.ORCHESTRATOR_AGENT.value):
                errors.append(f"Route '{route}' has no incoming or outgoing connections")

        return errors


class ADKRoutingManager:
    """Manager for handling ADK agent routing and transfers."""

    def __init__(self, agent_routing_config: AgentRoutingConfig):
        """Initialize the routing manager.

        Args:
            agent_routing_config: The routing configuration
        """
        self.routing_config = agent_routing_config
        self._current_context: Optional[ToolContext] = None

    def set_context(self, context: ToolContext) -> None:
        """Set the current tool context for routing.

        Args:
            context: The ADK tool context
        """
        self._current_context = context

    def route_to_agent(self, target_route: str, data: Dict[str, Any]) -> bool:
        """Route execution to another agent using ADK patterns.

        Args:
            target_route: Target agent route
            data: Data to pass to the target agent

        Returns:
            True if routing was successful
        """
        if not self._current_context:
            logger.error("No tool context set for routing")
            return False

        # Validate routing is allowed
        current_agent = self._current_context.data.get("current_agent")  # type: ignore[attr-defined]
        if current_agent and not self.routing_config.can_transfer(current_agent, target_route):
            logger.warning(
                "Transfer not allowed from '%s' to '%s'", current_agent, target_route
            )
            return False

        # Set ADK transfer
        self._current_context.actions.transfer_to_agent = target_route

        # Pass data through context
        for key, value in data.items():
            self._current_context.data[key] = value  # type: ignore[attr-defined]

        logger.info("Routing to agent '%s' with data keys: %s", target_route, list(data.keys()))
        return True

    def get_workflow_path(self, start_route: str, end_route: str) -> List[str]:
        """Calculate the workflow path between agents.

        Args:
            start_route: Starting agent route
            end_route: Target agent route

        Returns:
            List of agent routes representing the path
        """
        # Simple BFS to find path
        from collections import deque

        if start_route == end_route:
            return [start_route]

        queue = deque([(start_route, [start_route])])
        visited = {start_route}

        while queue:
            current, path = queue.popleft()

            for next_route in self.routing_config.get_allowed_transfers(current):
                if next_route == end_route:
                    return path + [next_route]

                if next_route not in visited:
                    visited.add(next_route)
                    queue.append((next_route, path + [next_route]))

        return []  # No path found


# Global routing configuration instance
routing_config = AgentRoutingConfig()

# Global routing manager instance
routing_manager = ADKRoutingManager(routing_config)


def get_routing_config() -> AgentRoutingConfig:
    """Get the global routing configuration instance."""
    return routing_config


def get_routing_manager() -> ADKRoutingManager:
    """Get the global routing manager instance."""
    return routing_manager
