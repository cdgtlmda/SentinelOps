"""Base agent class for SentinelOps using Google ADK.

This module provides the base implementation for all SentinelOps agents
using the Google Agent Development Kit (ADK).
"""

import logging
import os
from typing import Any, Dict, List, Optional

# Import ADK classes
from google.adk.agents import LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.run_config import RunConfig


from google.auth import default
from google.auth.credentials import Credentials
from google.cloud import logging as cloud_logging
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import BaseModel, Field

from .adk_routing import get_routing_config, AgentRoute

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentinelOpsConfig(BaseModel):
    """Configuration for SentinelOps agents."""

    project_id: str = Field(
        default_factory=lambda: os.environ.get("GCP_PROJECT_ID", ""),
        description="Google Cloud Project ID",
    )
    location: str = Field(default="us-central1", description="Google Cloud location")
    telemetry_enabled: bool = Field(default=True, description="Enable ADK telemetry")
    log_level: str = Field(default="INFO", description="Logging level")
    enable_cloud_logging: bool = Field(
        default=True, description="Enable Google Cloud Logging integration"
    )
    enable_cloud_trace: bool = Field(
        default=True, description="Enable Google Cloud Trace integration"
    )


class SentinelOpsBaseAgent(LlmAgent):
    """Base agent class for all SentinelOps agents using ADK.

    This class extends the ADK LlmAgent to provide common functionality
    for all SentinelOps agents including:
    - Google Cloud authentication setup
    - Logging integration
    - Common configuration patterns
    """

    def __init__(
        self,
        name: str,
        description: str,
        config: Optional[Dict[str, Any]] = None,
        model: str = "gemini-pro",
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the SentinelOps base agent.

        Args:
            name: Agent name
            description: Agent description
            config: Configuration dictionary (handled by subclasses)
            model: LLM model to use (default: gemini-pro)
            tools: List of tools available to the agent
            **kwargs: Additional arguments passed to LlmAgent
        """
        # Don't pass config to parent as it's not a valid LlmAgent parameter
        # Initialize the parent LlmAgent
        super().__init__(
            name=name, description=description, model=model, tools=tools or [], **kwargs
        )

        # Initialize instance variables
        self._tracer: Optional[Any] = None
        self._credentials: Optional[Any] = None
        self._project_id: str = ""
        self._cloud_logging_client: Optional[Any] = None

        # Set up basic logging
        logger.info("Initialized %s agent: %s", self.__class__.__name__, name)

        # Initialize Google Cloud authentication
        self._setup_google_cloud_auth()

        # Set up ADK telemetry if enabled
        if config and config.get("telemetry_enabled", True):
            self._setup_adk_telemetry()

        # Register agent with routing configuration
        self._register_with_routing()

    async def setup(self) -> None:
        """Setup method for async initialization.

        This method should be overridden by subclasses to perform any
        async initialization required by the specific agent.
        """
        # Base implementation - subclasses can override
        logger.info("Base setup for %s", self.__class__.__name__)

    def _register_with_routing(self) -> None:
        """Register this agent with the routing configuration."""
        # Map agent names to routes
        route_mapping = {
            "detection_agent": AgentRoute.DETECTION_AGENT.value,
            "analysis_agent": AgentRoute.ANALYSIS_AGENT.value,
            "remediation_agent": AgentRoute.REMEDIATION_AGENT.value,
            "communication_agent": AgentRoute.COMMUNICATION_AGENT.value,
            "orchestrator_agent": AgentRoute.ORCHESTRATOR_AGENT.value,
        }

        if self.name in route_mapping:
            routing_config = get_routing_config()
            routing_config.register_agent(route_mapping[self.name], self)
            logger.info("Registered agent '%s' with routing configuration", self.name)

    def _setup_google_cloud_auth(self) -> None:
        """Set up Google Cloud authentication."""
        try:
            # Get default credentials
            result = default()  # type: ignore[no-untyped-call]
            if isinstance(result, tuple) and len(result) == 2:
                self._credentials, project = result
            else:
                self._credentials = result
                project = None
            self._project_id = project or os.environ.get("GCP_PROJECT_ID", "")

            logger.info("Google Cloud auth configured for project: %s", self._project_id)

            # Set up Cloud Logging if enabled
            if (hasattr(self, "config") and self.config and
                    self.config.get("enable_cloud_logging", True)):
                try:
                    self._cloud_logging_client = cloud_logging.Client(  # type: ignore[no-untyped-call]
                        project=self._project_id,
                        credentials=self._credentials
                    )
                    self._cloud_logging_client.setup_logging()  # type: ignore[no-untyped-call]
                    logger.info("Google Cloud Logging integration enabled")
                except Exception as e:  # pylint: disable=broad-exception-caught
                    logger.warning("Could not set up Cloud Logging: %s", e)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Could not set up Google Cloud auth: %s", e)
            self._credentials = None
            self._project_id = os.environ.get("GCP_PROJECT_ID", "")

    def _setup_adk_telemetry(self) -> None:
        """Set up ADK telemetry with Cloud Trace integration."""
        try:
            # Configure OpenTelemetry for Cloud Trace
            if (hasattr(self, "config") and self.config and
                    self.config.get("enable_cloud_trace", True)):
                # Set up the tracer provider
                tracer_provider = TracerProvider()
                trace.set_tracer_provider(tracer_provider)

                # Add Cloud Trace exporter
                cloud_trace_exporter = CloudTraceSpanExporter(  # type: ignore[no-untyped-call]
                    project_id=self._project_id or os.environ.get("GCP_PROJECT_ID", "")
                )
                tracer_provider.add_span_processor(
                    BatchSpanProcessor(cloud_trace_exporter)
                )

                # Get a tracer for this agent
                self._tracer = trace.get_tracer(
                    f"sentinelops.{self.name}"
                )

                logger.info("ADK telemetry with Cloud Trace enabled")
            else:
                logger.info("ADK telemetry disabled by configuration")

        except (ImportError, ValueError, AttributeError, RuntimeError) as e:
            logger.warning("Could not set up ADK telemetry: %s", e)
            self._tracer = None

    async def run(
        self, context: Optional[Any] = None, config: Optional[RunConfig] = None, **kwargs: Any
    ) -> Any:
        """Execute the agent's main logic.

        This method handles incoming transfers and delegates to agent-specific logic.

        Args:
            context: ADK invocation context (InvocationContext or ToolContext)
            config: Optional run configuration
            **kwargs: Agent-specific arguments

        Returns:
            Agent-specific response
        """
        logger.info("Running agent: %s", self.name)

        # Check for incoming transfers
        transfer_result = await self._check_and_handle_transfer(context)
        if transfer_result is not None:
            return transfer_result

        # Check if this is a tool execution context
        tool_result = await self._check_and_execute_tool(context, **kwargs)
        if tool_result is not None:
            return tool_result

        # Default behavior - execute all tools or delegate to subclass
        try:
            return await self._execute_agent_logic(context, config, **kwargs)
        except NotImplementedError:
            return await self._execute_default_logic(context, **kwargs)

    async def _check_and_handle_transfer(self, context: Optional[Any]) -> Optional[Any]:
        """Check for and handle incoming transfers."""
        if context and hasattr(context, 'data') and context.data:
            transfer_data = context.data.get('transfer_data', {})
            if transfer_data:
                logger.info("Handling transfer in %s: %s", self.name, list(transfer_data.keys()))
                return await self._handle_transfer(context, transfer_data)
        return None

    async def _check_and_execute_tool(self, context: Optional[Any], **kwargs: Any) -> Optional[Any]:
        """Check if this is a tool execution context and execute the tool."""
        if context and hasattr(context, 'tool_name'):
            logger.info("Executing tool: %s", context.tool_name)
            for tool in self.tools:
                if hasattr(tool, 'name') and tool.name == context.tool_name:
                    if hasattr(tool, 'execute') and callable(tool.execute):
                        return await tool.execute(context, **kwargs)
                    elif callable(tool):
                        return await tool(context, **kwargs)
            logger.error("Tool not found: %s", context.tool_name)
            return {"error": f"Tool '{context.tool_name}' not found in agent '{self.name}'"}
        return None

    async def _execute_default_logic(self, context: Optional[Any], **kwargs: Any) -> Any:
        """Execute default agent logic when no specific implementation exists."""
        logger.info("Using default run implementation for %s", self.name)
        results = {}

        # Execute tools if any are registered
        if self.tools:
            for tool in self.tools:
                try:
                    tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                    if hasattr(tool, 'execute') and callable(tool.execute):
                        tool_result = await tool.execute(context, **kwargs)
                    elif callable(tool):
                        tool_result = await tool(context, **kwargs)
                    else:
                        tool_result = {"error": "Tool is not callable"}
                    results[tool_name] = tool_result
                except Exception as e:  # pylint: disable=broad-exception-caught
                    tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                    logger.error("Error executing tool %s: %s", tool_name, e)
                    results[tool_name] = {"error": str(e)}
            return results

        # No tools and no implementation - return basic response
        return {
            "agent": self.name,
            "status": "ready",
            "message": f"Agent {self.name} is ready but has no tools or implementation"
        }

    async def _handle_transfer(self, _context: Any, _transfer_data: Dict[str, Any]) -> Any:
        """Handle incoming agent transfers.

        This method should be overridden by subclasses to handle
        agent-specific transfer data.

        Args:
            context: ADK invocation context
            transfer_data: Data transferred from another agent

        Returns:
            Agent-specific response
        """
        logger.warning(
            "Agent %s received transfer but has not implemented _handle_transfer", self.name
        )
        raise NotImplementedError(
            f"Agent '{self.name}' must implement _handle_transfer to handle incoming transfers"
        )

    async def _execute_agent_logic(
        self, context: Any, config: Optional[RunConfig], **kwargs: Any
    ) -> Any:
        """Execute agent-specific logic.

        This method should be overridden by subclasses to implement
        the agent's core functionality.

        Args:
            context: ADK invocation context
            config: Optional run configuration
            **kwargs: Agent-specific arguments

        Returns:
            Agent-specific response
        """
        _ = (context, config, kwargs)  # Unused but required for interface
        logger.warning("Agent %s has not implemented _execute_agent_logic", self.name)
        raise NotImplementedError(
            f"Agent '{self.name}' must implement _execute_agent_logic for its core functionality"
        )

    async def handle_error(
        self, error: Exception, context: InvocationContext
    ) -> Dict[str, Any]:
        """Handle errors during agent execution.

        This method can be overridden by subclasses for custom error handling.

        Args:
            error: The exception that occurred
            context: ADK invocation context

        Returns:
            Error response dictionary
        """
        _ = context  # Unused but required for interface
        logger.error("Error in agent %s: %s", self.name, str(error), exc_info=True)
        return {
            "error": True,
            "agent": self.name,
            "message": str(error),
            "type": type(error).__name__,
        }

    def get_tools(self) -> List[Any]:
        """Get the list of tools available to this agent.

        Returns:
            List of ADK tools
        """
        return self.tools

    def add_tool(self, tool: Any) -> None:
        """Add a tool to the agent's toolset.

        Args:
            tool: ADK tool to add
        """
        # For Pydantic models, we need to work with the actual list
        current_tools = list(self.tools or [])
        if tool not in current_tools:
            current_tools.append(tool)
            object.__setattr__(self, 'tools', current_tools)
            logger.info("Added tool %s to agent %s", tool.__class__.__name__, self.name)

    def remove_tool(self, tool: Any) -> None:
        """Remove a tool from the agent's toolset.

        Args:
            tool: ADK tool to remove
        """
        # For Pydantic models, we need to work with the actual list
        current_tools = list(self.tools or [])
        if tool in current_tools:
            current_tools.remove(tool)
            object.__setattr__(self, 'tools', current_tools)
            logger.info(
                "Removed tool %s from agent %s", tool.__class__.__name__, self.name
            )

    def __repr__(self) -> str:
        """String representation of the agent."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"description='{self.description[:50]}...', "
            f"tools={len(self.tools)})"
        )

    def get_agent_route(self) -> Optional[str]:
        """Get the route identifier for this agent.

        Returns:
            The agent route or None if not mapped
        """
        route_mapping = {
            "detection_agent": AgentRoute.DETECTION_AGENT.value,
            "analysis_agent": AgentRoute.ANALYSIS_AGENT.value,
            "remediation_agent": AgentRoute.REMEDIATION_AGENT.value,
            "communication_agent": AgentRoute.COMMUNICATION_AGENT.value,
            "orchestrator_agent": AgentRoute.ORCHESTRATOR_AGENT.value,
        }
        return route_mapping.get(self.name)

    def prepare_tool_context(self, context: Any) -> Any:
        """Prepare tool context with agent identity.

        Args:
            context: Tool context to prepare

        Returns:
            Updated context
        """
        if hasattr(context, 'data') and isinstance(context.data, dict):
            agent_route = self.get_agent_route()
            if agent_route:
                context.data["current_agent"] = agent_route
        return context

    @property
    def credentials(self) -> Optional[Credentials]:
        """Get Google Cloud credentials.

        Returns:
            Google Cloud credentials or None if not configured
        """
        return getattr(self, "_credentials", None)

    @property
    def project_id(self) -> str:
        """Get Google Cloud project ID.

        Returns:
            Project ID or empty string if not configured
        """
        return getattr(self, "_project_id", "")

    @property
    def tracer(self) -> Optional[Any]:
        """Get OpenTelemetry tracer for this agent.

        Returns:
            OpenTelemetry tracer or None if telemetry is disabled
        """
        return getattr(self, "_tracer", None)
