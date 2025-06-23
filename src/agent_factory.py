#!/usr/bin/env python3
"""
Factory for creating SentinelOps agents with proper configuration.
"""

import logging
import os
from typing import Any, Optional

from src.analysis_agent.adk_agent import AnalysisAgent
from src.common.config_loader import get_config
from src.communication_agent.adk_agent import CommunicationAgent
from src.detection_agent.adk_agent import DetectionAgent
from src.orchestrator_agent.adk_agent import OrchestratorAgent
from src.remediation_agent.adk_agent import RemediationAgent

logger = logging.getLogger(__name__)


def create_detection_agent(project_id: Optional[str] = None) -> DetectionAgent:
    """
    Create a detection agent with proper configuration.

    Args:
        project_id: Optional project ID override

    Returns:
        Configured DetectionAgent instance
    """
    # Load configuration
    config = get_config()

    # Override project ID if provided
    if project_id:
        if "gcp" not in config:
            config["gcp"] = {}
        config["gcp"]["project_id"] = project_id

        if "google_cloud" not in config:
            config["google_cloud"] = {}
        config["google_cloud"]["project_id"] = project_id
    else:
        # Ensure gcp key exists with project_id from google_cloud
        if "gcp" not in config and "google_cloud" in config:
            config["gcp"] = {"project_id": config["google_cloud"].get("project_id")}

    # Use project ID as agent ID if not specified
    agent_id = os.environ.get(
        "AGENT_ID",
        project_id or config.get("gcp", {}).get("project_id", "detection-agent"),
    )

    logger.info("Creating detection agent with ID: %s", agent_id)

    return DetectionAgent(config)


def create_analysis_agent(project_id: Optional[str] = None) -> AnalysisAgent:
    """
    Create an analysis agent with proper configuration.

    Args:
        project_id: Optional project ID override

    Returns:
        Configured AnalysisAgent instance
    """
    # Load configuration
    config = get_config()

    # Override project ID if provided
    if project_id:
        if "gcp" not in config:
            config["gcp"] = {}
        config["gcp"]["project_id"] = project_id

        if "google_cloud" not in config:
            config["google_cloud"] = {}
        config["google_cloud"]["project_id"] = project_id

    # Use project ID as agent ID if not specified
    agent_id = os.environ.get(
        "AGENT_ID",
        project_id or config.get("gcp", {}).get("project_id", "analysis-agent"),
    )

    logger.info("Creating analysis agent with ID: %s", agent_id)

    return AnalysisAgent(config)


def create_remediation_agent(project_id: Optional[str] = None) -> RemediationAgent:
    """
    Create a remediation agent with proper configuration.

    Args:
        project_id: Optional project ID override

    Returns:
        Configured RemediationAgent instance
    """
    # Load configuration
    config = get_config()

    # Override project ID if provided
    if project_id:
        if "gcp" not in config:
            config["gcp"] = {}
        config["gcp"]["project_id"] = project_id

        if "google_cloud" not in config:
            config["google_cloud"] = {}
        config["google_cloud"]["project_id"] = project_id

    logger.info("Creating remediation agent")

    return RemediationAgent(config)


def create_communication_agent(project_id: Optional[str] = None) -> CommunicationAgent:
    """
    Create a communication agent with proper configuration.

    Args:
        project_id: Optional project ID override

    Returns:
        Configured CommunicationAgent instance
    """
    # Load configuration
    config = get_config()

    # Override project ID if provided
    if project_id:
        if "gcp" not in config:
            config["gcp"] = {}
        config["gcp"]["project_id"] = project_id

        if "google_cloud" not in config:
            config["google_cloud"] = {}
        config["google_cloud"]["project_id"] = project_id

    logger.info("Creating communication agent")

    return CommunicationAgent(config)


def create_orchestrator_agent(project_id: Optional[str] = None) -> OrchestratorAgent:
    """
    Create an orchestrator agent with proper configuration.

    Args:
        project_id: Optional project ID override

    Returns:
        Configured OrchestratorAgent instance
    """
    # Load configuration
    config = get_config()

    # Override project ID if provided
    if project_id:
        if "gcp" not in config:
            config["gcp"] = {}
        config["gcp"]["project_id"] = project_id

        if "google_cloud" not in config:
            config["google_cloud"] = {}
        config["google_cloud"]["project_id"] = project_id

    # Use project ID as agent ID if not specified
    agent_id = os.environ.get(
        "AGENT_ID",
        project_id or config.get("google_cloud", {}).get("project_id", "orchestrator-agent"),
    )

    logger.info("Creating orchestrator agent with ID: %s", agent_id)

    return OrchestratorAgent(config)


def create_agent(agent_type: str, project_id: Optional[str] = None) -> Any:
    """
    Create an agent of the specified type.

    Args:
        agent_type: Type of agent to create
        project_id: Optional project ID override

    Returns:
        Configured agent instance

    Raises:
        ValueError: If agent type is unknown
    """
    agent_factories = {
        "detection": create_detection_agent,
        "analysis": create_analysis_agent,
        "remediation": create_remediation_agent,
        "communication": create_communication_agent,
        "orchestrator": create_orchestrator_agent,
    }

    if agent_type not in agent_factories:
        raise ValueError(f"Unknown agent type: {agent_type}")

    return agent_factories[agent_type](project_id)
