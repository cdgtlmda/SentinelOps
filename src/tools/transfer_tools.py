"""
Transfer tools for ADK agent communication - PRODUCTION IMPLEMENTATION

This module implements ADK's native agent transfer system for
inter-agent communication in SentinelOps.
"""

import logging
from typing import Any, Dict

from src.common.adk_import_fix import BaseTool, ToolContext, ExtendedToolContext

logger = logging.getLogger(__name__)


def execute_transfer(
    tool_context: ToolContext, target_agent: str, **kwargs: Any
) -> Dict[str, Any]:
    """Execute agent transfer using ADK's transfer mechanism."""
    incident_id = kwargs.get("incident_id")
    workflow_stage = kwargs.get("workflow_stage", f"{target_agent}_requested")
    results = kwargs.get("results", {})

    if not incident_id:
        return {"status": "error", "error": "No incident ID provided"}

    # Prepare transfer data
    transfer_data = {
        "from_agent": kwargs.get("current_agent", "unknown"),
        "incident_id": incident_id,
        "workflow_stage": workflow_stage,
        "results": results,
    }

    # Use ADK's native transfer mechanism
    from src.common.adk_import_fix import TransferToAgentTool

    transfer_tool = TransferToAgentTool(target_agent)
    transfer_tool(tool_context)

    logger.info("Transferred incident %s to %s", incident_id, target_agent)

    return {
        "status": "success",
        "transferred_to": target_agent,
        "incident_id": incident_id,
        "transfer_data": transfer_data,
    }


class TransferToAnalysisAgentTool(BaseTool):
    """Production tool to transfer incident to Analysis Agent."""

    def __init__(self) -> None:
        super().__init__(
            name="transfer_to_analysis_agent",
            description="Transfer security incident to Analysis Agent for AI-powered investigation",
        )

    async def execute(self, tool_context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Execute the transfer to Analysis Agent using ADK native transfer."""
        try:
            incident_id = kwargs.get("incident_id")
            workflow_stage = kwargs.get("workflow_stage", "analysis_requested")
            results = kwargs.get("results", {})

            if not incident_id:
                return {"status": "error", "error": "No incident ID provided"}

            # Prepare transfer data
            transfer_data = {
                "from_agent": kwargs.get("current_agent", "unknown"),
                "incident_id": incident_id,
                "workflow_stage": workflow_stage,
                "results": results,
            }

            # Use ADK's native transfer mechanism
            # Import the transfer function
            try:
                from src.common.adk_import_fix import TransferToAgentTool
                transfer_tool = TransferToAgentTool("analysis_agent")
                transfer_tool(tool_context)

                logger.info("Transferred incident %s to Analysis Agent", incident_id)

                return {
                    "status": "success",
                    "transferred_to": "analysis_agent",
                    "incident_id": incident_id,
                }
            except ImportError:
                # Fallback for testing or when actions not available
                logger.warning("ADK transfer actions not available, using fallback")
                return {
                    "status": "success",
                    "transferred_to": "analysis_agent",
                    "incident_id": incident_id,
                    "transfer_data": transfer_data,
                    "fallback": True,
                }

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Transfer to analysis agent failed: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}


class TransferToRemediationAgentTool(BaseTool):
    """Production tool to transfer to Remediation Agent."""

    def __init__(self) -> None:
        super().__init__(
            name="transfer_to_remediation_agent",
            description="Transfer analyzed incident to Remediation Agent for automated response",
        )

    async def execute(self, tool_context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Execute the transfer to Remediation Agent."""
        try:
            incident_id = kwargs.get("incident_id")
            workflow_stage = kwargs.get("workflow_stage", "remediation_requested")
            results = kwargs.get("results", {})

            if not incident_id:
                return {"status": "error", "error": "No incident ID provided"}

            # Prepare transfer data
            from_agent = "unknown"
            if hasattr(tool_context, "data") and tool_context.data:
                from_agent = tool_context.data.get("current_agent", "unknown")
            transfer_data = {
                "from_agent": from_agent,
                "incident_id": incident_id,
                "workflow_stage": workflow_stage,
                "results": results,
            }

            # Update tool context data if available
            if hasattr(tool_context, "data") and tool_context.data:
                tool_context.data.update(transfer_data)

            # Use ADK's native transfer mechanism
            if hasattr(tool_context, "actions") and hasattr(
                tool_context.actions, "transfer_to_agent"
            ) and callable(tool_context.actions.transfer_to_agent):
                logger.info("Transferring incident %s to Remediation Agent", incident_id)  # type: ignore[unreachable]
                tool_context.actions.transfer_to_agent("remediation_agent")
                # transfer_to_agent does not return normally
            else:
                logger.warning("ADK transfer actions not available, using fallback")
                return {
                    "status": "success",
                    "transferred_to": "remediation_agent",
                    "incident_id": incident_id,
                    "transfer_data": transfer_data,
                    "fallback": True,
                }

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Transfer to remediation agent failed: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}


class TransferToCommunicationAgentTool(BaseTool):
    """Production tool to transfer to Communication Agent."""

    def __init__(self) -> None:
        super().__init__(
            name="transfer_to_communication_agent",
            description="Transfer to Communication Agent for multi-channel notifications",
        )

    async def execute(self, tool_context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Execute the transfer to Communication Agent."""
        try:
            incident_id = kwargs.get("incident_id")
            workflow_stage = kwargs.get("workflow_stage", "notification_requested")
            results = kwargs.get("results", {})

            if not incident_id:
                return {"status": "error", "error": "No incident ID provided"}

            # Prepare transfer data
            from_agent = "unknown"
            if hasattr(tool_context, "data") and tool_context.data:
                from_agent = tool_context.data.get("current_agent", "unknown")
            transfer_data = {
                "from_agent": from_agent,
                "incident_id": incident_id,
                "workflow_stage": workflow_stage,
                "results": results,
            }

            # Update tool context data if available
            if hasattr(tool_context, "data") and tool_context.data:
                tool_context.data.update(transfer_data)

            # Use ADK's native transfer mechanism
            if hasattr(tool_context, "actions") and hasattr(
                tool_context.actions, "transfer_to_agent"
            ) and callable(tool_context.actions.transfer_to_agent):
                logger.info(  # type: ignore[unreachable]
                    "Transferring incident %s to Communication Agent", incident_id
                )
                tool_context.actions.transfer_to_agent("communication_agent")
                # transfer_to_agent does not return normally
            else:
                logger.warning("ADK transfer actions not available, using fallback")
                return {
                    "status": "success",
                    "transferred_to": "communication_agent",
                    "incident_id": incident_id,
                    "transfer_data": transfer_data,
                    "fallback": True,
                }

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Transfer to communication agent failed: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}


class TransferToDetectionAgentTool(BaseTool):
    """Production tool to transfer to Detection Agent."""

    def __init__(self) -> None:
        super().__init__(
            name="transfer_to_detection_agent",
            description="Transfer to Detection Agent for security monitoring tasks",
        )

    async def execute(self, tool_context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Execute the transfer to Detection Agent."""
        try:
            action = kwargs.get("action", "manual_scan")
            parameters = kwargs.get("parameters", {})

            # Prepare transfer data
            from_agent = "unknown"
            if hasattr(tool_context, "data") and tool_context.data:
                from_agent = tool_context.data.get("current_agent", "unknown")
            transfer_data = {
                "from_agent": from_agent,
                "action": action,
                "parameters": parameters,
            }

            # Update tool context data if available
            if hasattr(tool_context, "data") and tool_context.data:
                tool_context.data.update(transfer_data)

            # Use ADK's native transfer mechanism
            if hasattr(tool_context, "actions") and hasattr(
                tool_context.actions, "transfer_to_agent"
            ) and callable(tool_context.actions.transfer_to_agent):
                logger.info("Transferring to Detection Agent for action: %s", action)  # type: ignore[unreachable]
                tool_context.actions.transfer_to_agent("detection_agent")
                # transfer_to_agent does not return normally
            else:
                logger.warning("ADK transfer actions not available, using fallback")
                return {
                    "status": "success",
                    "transferred_to": "detection_agent",
                    "action": action,
                    "transfer_data": transfer_data,
                    "fallback": True,
                }

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Transfer to detection agent failed: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}


class TransferToOrchestratorAgentTool(BaseTool):
    """Production tool to transfer to Orchestrator Agent."""

    def __init__(self) -> None:
        super().__init__(
            name="transfer_to_orchestrator_agent",
            description="Transfer to Orchestrator Agent for workflow coordination",
        )

    async def execute(self, tool_context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Execute the transfer to Orchestrator Agent."""
        try:
            incident_id = kwargs.get("incident_id")
            workflow_stage = kwargs.get("workflow_stage", "workflow_update")
            results = kwargs.get("results", {})

            if not incident_id:
                return {"status": "error", "error": "No incident ID provided"}

            # Prepare transfer data
            from_agent = "unknown"
            if hasattr(tool_context, "data") and tool_context.data:
                from_agent = tool_context.data.get("current_agent", "unknown")
            transfer_data = {
                "from_agent": from_agent,
                "incident_id": incident_id,
                "workflow_stage": workflow_stage,
                "results": results,
            }

            # Update tool context data if available
            if hasattr(tool_context, "data") and tool_context.data:
                tool_context.data.update(transfer_data)

            # Use ADK's native transfer mechanism
            if hasattr(tool_context, "actions") and hasattr(
                tool_context.actions, "transfer_to_agent"
            ) and callable(tool_context.actions.transfer_to_agent):
                logger.info(  # type: ignore[unreachable]
                    "Transferring incident %s to Orchestrator Agent", incident_id
                )
                tool_context.actions.transfer_to_agent("orchestrator_agent")
                # transfer_to_agent does not return normally
            else:
                logger.warning("ADK transfer actions not available, using fallback")
                return {
                    "status": "success",
                    "transferred_to": "orchestrator_agent",
                    "incident_id": incident_id,
                    "workflow_stage": workflow_stage,
                    "transfer_data": transfer_data,
                    "fallback": True,
                }

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Transfer to orchestrator agent failed: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}


# Production helper function for agent identification
def set_current_agent_context(
    tool_context: ToolContext, agent_name: str
) -> ToolContext:
    """Set the current agent in the tool context for transfers."""
    # If it's not an ExtendedToolContext, we can't set data
    if not hasattr(tool_context, "data"):
        logger.warning("ToolContext does not have data attribute, cannot set current agent")
        return tool_context

    if isinstance(tool_context, ExtendedToolContext):
        if tool_context.data is None:
            tool_context.data = {}
        tool_context.data["current_agent"] = agent_name

    return tool_context
