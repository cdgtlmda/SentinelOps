"""ADK Routing Initialization for SentinelOps.

This module handles the initialization of agent routing configuration
and sets up the agent network for proper inter-agent communication.
"""

import logging
from typing import Dict, Any, Optional

from src.common.adk_routing import get_routing_config, get_routing_manager, AgentRoute
from src.detection_agent.adk_agent import DetectionAgent
from src.analysis_agent.adk_agent import AnalysisAgent
from src.remediation_agent.adk_agent import RemediationAgent
from src.communication_agent.adk_agent import CommunicationAgent
from src.orchestrator_agent.adk_agent import OrchestratorAgent

logger = logging.getLogger(__name__)


def initialize_agent_routing(config: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize the agent routing configuration with all agents.

    This function creates all agent instances and registers them with
    the routing configuration to enable proper ADK-based transfers.

    Args:
        config: Configuration dictionary for agents

    Returns:
        Dictionary containing initialized agent instances
    """
    agents: Dict[str, Any] = {}
    routing_config = get_routing_config()

    try:
        # Initialize Detection Agent
        detection_config = config.get("detection_agent", {})
        detection_agent = DetectionAgent(detection_config)
        agents[AgentRoute.DETECTION_AGENT.value] = detection_agent
        logger.info("Initialized Detection Agent")

        # Initialize Analysis Agent
        analysis_config = config.get("analysis_agent", {})
        analysis_agent = AnalysisAgent(analysis_config)
        agents[AgentRoute.ANALYSIS_AGENT.value] = analysis_agent
        logger.info("Initialized Analysis Agent")

        # Initialize Remediation Agent
        remediation_config = config.get("remediation_agent", {})
        remediation_agent = RemediationAgent(remediation_config)
        agents[AgentRoute.REMEDIATION_AGENT.value] = remediation_agent
        logger.info("Initialized Remediation Agent")

        # Initialize Communication Agent
        communication_config = config.get("communication_agent", {})
        communication_agent = CommunicationAgent(communication_config)
        agents[AgentRoute.COMMUNICATION_AGENT.value] = communication_agent
        logger.info("Initialized Communication Agent")

        # Initialize Orchestrator Agent
        orchestrator_config = config.get("orchestrator_agent", {})
        orchestrator_agent = OrchestratorAgent(orchestrator_config)
        agents[AgentRoute.ORCHESTRATOR_AGENT.value] = orchestrator_agent
        logger.info("Initialized Orchestrator Agent")

        # Validate routing configuration
        errors = routing_config.validate_routing_integrity()
        if errors:
            logger.warning("Routing configuration validation warnings: %s", errors)
        else:
            logger.info("Routing configuration validated successfully")

        # Log routing paths for key workflows
        _log_workflow_paths(routing_config)

        return agents

    except Exception as e:
        logger.error("Failed to initialize agent routing: %s", str(e))
        raise


def _log_workflow_paths(routing_config: Any) -> None:
    """Log the workflow paths between agents for debugging."""
    _ = routing_config  # Unused but kept for consistency
    routing_manager = get_routing_manager()

    # Log detection to remediation path
    detection_to_remediation = routing_manager.get_workflow_path(
        AgentRoute.DETECTION_AGENT.value,
        AgentRoute.REMEDIATION_AGENT.value
    )
    logger.info("Detection → Remediation path: %s", ' → '.join(detection_to_remediation))

    # Log full incident response path
    full_path = routing_manager.get_workflow_path(
        AgentRoute.DETECTION_AGENT.value,
        AgentRoute.COMMUNICATION_AGENT.value
    )
    logger.info("Full incident response path: %s", ' → '.join(full_path))


def create_agent_network(config: Dict[str, Any]) -> 'AgentNetwork':
    """Create and configure the complete agent network.

    Args:
        config: Configuration dictionary

    Returns:
        Configured AgentNetwork instance
    """
    agents = initialize_agent_routing(config)
    return AgentNetwork(agents, config)


class AgentNetwork:
    """Manages the network of ADK agents for SentinelOps."""

    def __init__(self, agents: Dict[str, Any], config: Dict[str, Any]):
        """Initialize the agent network.

        Args:
            agents: Dictionary of initialized agents
            config: Configuration dictionary
        """
        self.agents = agents
        self.config = config
        self.routing_config = get_routing_config()
        self.routing_manager = get_routing_manager()

    def get_agent(self, route: str) -> Optional[Any]:
        """Get an agent by its route.

        Args:
            route: Agent route identifier

        Returns:
            Agent instance or None
        """
        return self.agents.get(route)

    def start_workflow(self, entry_point: str = AgentRoute.ORCHESTRATOR_AGENT.value) -> None:
        """Start the agent workflow from a specific entry point.

        Args:
            entry_point: Route of the agent to start from
        """
        agent = self.get_agent(entry_point)
        if not agent:
            raise ValueError(f"No agent found for route: {entry_point}")

        logger.info("Starting workflow from %s", entry_point)
        # In a real implementation, this would trigger the agent's run method
        # with appropriate context and configuration

    def get_routing_info(self) -> Dict[str, Any]:
        """Get information about the current routing configuration.

        Returns:
            Dictionary with routing information
        """
        return {
            "agents": list(self.agents.keys()),
            "routes": {
                route: self.routing_config.get_route_info(route)
                for route in self.agents.keys()
            },
            "validation_status": self.routing_config.validate_routing_integrity()
        }
