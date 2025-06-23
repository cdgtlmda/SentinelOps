"""
Orchestrator Agent using Google ADK - PRODUCTION IMPLEMENTATION

This agent coordinates the incident response workflow using ADK patterns.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional, List, Set

from google.adk.agents import SequentialAgent
from google.adk.agents.run_config import RunConfig
from google.adk.tools import BaseTool, ToolContext
from google.cloud import firestore

from src.common.adk_agent_base import SentinelOpsBaseAgent
from src.tools.transfer_tools import (
    TransferToAnalysisAgentTool,
    TransferToRemediationAgentTool,
    TransferToCommunicationAgentTool,
    TransferToDetectionAgentTool,
)

logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """Workflow stages for incident response."""

    DETECTION = "detection"
    ANALYSIS = "analysis"
    APPROVAL = "approval"
    REMEDIATION = "remediation"
    COMMUNICATION = "communication"
    RESOLUTION = "resolution"
    COMPLETED = "completed"


class WorkflowStatus(Enum):
    """Workflow execution status."""

    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"
    TIMEOUT = "timeout"


class WorkflowManagementTool(BaseTool):
    """Production tool for managing incident response workflows."""

    def __init__(self, firestore_client: firestore.Client, project_id: str):
        """Initialize with Firestore client."""
        super().__init__(
            name="workflow_management_tool",
            description="Manage incident response workflow state and transitions",
        )
        self.firestore_client = firestore_client
        self.project_id = project_id
        self.workflows_collection = "incident_workflows"

    async def execute(self, _context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Manage workflow state transitions."""
        action = kwargs.get("action")  # create, update, get, transition
        incident_id = kwargs.get("incident_id")

        try:
            if action == "create":
                # Create new workflow
                workflow = {
                    "incident_id": incident_id,
                    "status": WorkflowStatus.ACTIVE.value,
                    "current_stage": WorkflowStage.DETECTION.value,
                    "stages_completed": [],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "metadata": kwargs.get("metadata", {}),
                    "timeout_at": datetime.utcnow() + timedelta(hours=2),
                }

                doc_ref = self.firestore_client.collection(
                    self.workflows_collection
                ).document(incident_id)
                doc_ref.set(workflow)

                return {
                    "status": "success",
                    "workflow_id": incident_id,
                    "workflow": workflow,
                }

            elif action == "update":
                # Update workflow state
                doc_ref = self.firestore_client.collection(
                    self.workflows_collection
                ).document(incident_id)
                updates = kwargs.get("updates", {})
                updates["updated_at"] = datetime.utcnow()

                doc_ref.update(updates)

                return {
                    "status": "success",
                    "workflow_id": incident_id,
                    "updates": updates,
                }

            elif action == "transition":
                # Transition to next stage
                next_stage = kwargs.get("next_stage")
                doc_ref = self.firestore_client.collection(
                    self.workflows_collection
                ).document(incident_id)

                workflow = doc_ref.get().to_dict()
                if not workflow:
                    return {
                        "status": "error",
                        "error": f"Workflow not found for incident {incident_id}",
                    }

                current_stage = workflow.get("current_stage")
                stages_completed = workflow.get("stages_completed", [])

                # Add current stage to completed
                if current_stage not in stages_completed:
                    stages_completed.append(current_stage)

                doc_ref.update(
                    {
                        "current_stage": next_stage,
                        "stages_completed": stages_completed,
                        "updated_at": datetime.utcnow(),
                        f"stage_{current_stage}_completed_at": datetime.utcnow(),
                    }
                )

                return {
                    "status": "success",
                    "workflow_id": incident_id,
                    "previous_stage": current_stage,
                    "current_stage": next_stage,
                }

            elif action == "get":
                # Get workflow state
                doc_ref = self.firestore_client.collection(
                    self.workflows_collection
                ).document(incident_id)
                workflow = doc_ref.get()

                if workflow.exists:
                    return {"status": "success", "workflow": workflow.to_dict()}
                else:
                    return {
                        "status": "error",
                        "error": f"Workflow not found for incident {incident_id}",
                    }

            return {"status": "error", "error": f"Unknown action: {action}"}

        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            logger.error("Error in workflow management execution: %s", e)
            return {"status": "error", "error": str(e)}


class IncidentPrioritizationTool(BaseTool):
    """Production tool for prioritizing incidents based on severity and impact."""

    def __init__(self) -> None:
        """Initialize the prioritization tool."""
        super().__init__(
            name="incident_prioritization_tool",
            description="Prioritize incidents for optimal response ordering",
        )

    async def execute(self, _context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Calculate incident priority score."""
        incident = kwargs.get("incident", {})

        try:
            # Base priority on severity
            severity_scores = {"critical": 100, "high": 75, "medium": 50, "low": 25}

            severity = incident.get("severity", "medium").lower()
            base_score = severity_scores.get(severity, 50)

            # Adjust based on metadata
            metadata = incident.get("metadata", {})

            # Boost score for certain conditions
            if metadata.get("anomaly_type") == "privilege_escalation_abuse":
                base_score += 20

            if metadata.get("confidence", 0) > 0.8:
                base_score += 10

            if metadata.get("affected_resources_count", 0) > 5:
                base_score += 15

            # Time-based decay (older incidents get slight priority)
            created_at = incident.get("created_at")
            if created_at:
                age_minutes = (
                    datetime.utcnow() - datetime.fromisoformat(created_at)
                ).total_seconds() / 60
                if age_minutes > 30:
                    base_score += min(10, int(age_minutes / 10))

            # Cap at 100
            priority_score = min(100, base_score)

            return {
                "status": "success",
                "incident_id": incident.get("id"),
                "priority_score": priority_score,
                "factors": {
                    "severity": severity,
                    "confidence": metadata.get("confidence", 0),
                    "anomaly_type": metadata.get("anomaly_type", "unknown"),
                    "age_boost": (
                        age_minutes > 30 if "age_minutes" in locals() else False
                    ),
                },
            }

        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            logger.error("Error in prioritization execution: %s", e)
            return {"status": "error", "error": str(e)}


class OrchestratorAgent(SentinelOpsBaseAgent):
    """Production ADK Orchestrator Agent for coordinating incident response."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Orchestrator Agent with production configuration."""
        # Extract configuration
        project_id = config.get("project_id", "")
        max_concurrent_workflows = config.get("max_concurrent_workflows", 10)
        workflow_timeout_minutes = config.get("workflow_timeout_minutes", 120)
        auto_approve_threshold = config.get("auto_approve_threshold", 0.7)

        # Initialize Firestore
        firestore_client = firestore.Client(project=project_id)

        # Initialize production tools
        tools = [
            WorkflowManagementTool(firestore_client, project_id),
            IncidentPrioritizationTool(),
            TransferToAnalysisAgentTool(),
            TransferToRemediationAgentTool(),
            TransferToCommunicationAgentTool(),
            TransferToDetectionAgentTool(),
        ]

        # Initialize base agent
        super().__init__(
            name="orchestrator_agent",
            description="Production workflow orchestrator for incident response",
            config=config,
            model="gemini-pro",
            tools=tools,
        )

        # Initialize workflow management attributes
        self._active_workflows: Set[str] = set()
        self._workflow_queue: List[Dict[str, Any]] = []
        self._max_concurrent_workflows: int = max_concurrent_workflows
        self._workflow_timeout_minutes: int = workflow_timeout_minutes
        self._auto_approve_threshold: float = auto_approve_threshold

        # Use SequentialAgent pattern for workflow execution
        self._sequential_agent = SequentialAgent(
            name="incident_response_workflow",
            description="Sequential incident response workflow",
        )

    async def run(
        self,
        context: Optional[Any] = None,
        config: Optional[RunConfig] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute the production orchestration workflow."""
        try:
            # Check for incoming transfers
            if context and hasattr(context, "data") and context.data:
                return await self._handle_agent_transfer(context, config, **kwargs)

            # Regular orchestration tasks
            return await self._perform_orchestration(context, config, **kwargs)

        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            logger.error("Error in orchestrator agent: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}

    async def _handle_agent_transfer(
        self, context: Any, _config: Optional[RunConfig], **_kwargs: Any
    ) -> Dict[str, Any]:
        """Handle transfers from other agents."""
        transfer_data = context.data if hasattr(context, "data") else {}
        from_agent = transfer_data.get("from_agent", "unknown")
        workflow_stage = transfer_data.get("workflow_stage", "")
        incident_id = transfer_data.get("incident_id", "")
        results = transfer_data.get("results", {})

        logger.info(
            "Orchestrator received transfer from %s, stage: %s",
            from_agent,
            workflow_stage,
        )

        # Update workflow state
        workflow_tool = self.tools[0]  # WorkflowManagementTool
        # Use the passed context or create a mock one
        if context and hasattr(context, '__class__'):
            tool_context = context
        else:
            tool_context = type("MockToolContext", (), {
                "data": {},
                "actions": None,
                "invocation_context": None,
                "function_call_id": None
            })()

        # Handle based on workflow stage
        if workflow_stage == "detection_complete":
            # New incident detected
            incident = results.get("incident", {})

            # Create workflow
            if hasattr(workflow_tool, 'execute'):
                await workflow_tool.execute(
                    tool_context,
                    action="create",
                    incident_id=incident_id,
                    metadata={"incident": incident},
                )

            # Prioritize incident
            priority_tool = self.tools[1]  # IncidentPrioritizationTool
            priority_result = {}
            if hasattr(priority_tool, 'execute'):
                priority_result = await priority_tool.execute(
                    tool_context, incident=incident
                )

            priority_score = priority_result.get("priority_score", 50)

            # Queue or process based on capacity
            if len(self._active_workflows) < self._max_concurrent_workflows:
                return await self._process_incident(
                    incident, priority_score, tool_context
                )
            else:
                self._workflow_queue.append(
                    {
                        "incident": incident,
                        "priority": priority_score,
                        "queued_at": datetime.utcnow(),
                    }
                )
                self._workflow_queue.sort(key=lambda x: x["priority"], reverse=True)

                return {
                    "status": "queued",
                    "incident_id": incident_id,
                    "queue_position": len(self._workflow_queue),
                }

        elif workflow_stage == "analysis_complete":
            # Analysis completed
            analysis_results = results

            # Update workflow
            if hasattr(workflow_tool, 'execute'):
                await workflow_tool.execute(
                    tool_context,
                    action="transition",
                    incident_id=incident_id,
                    next_stage=WorkflowStage.APPROVAL.value,
                )

            # Determine if auto-remediation should proceed
            threat_assessment = (
                analysis_results.get("stages", {})
                .get("ai_analysis", {})
                .get("threat_assessment", {})
            )
            confidence = threat_assessment.get("confidence", 0)

            if confidence >= self._auto_approve_threshold:
                # Auto-approve remediation
                return await self._initiate_remediation(
                    incident_id if incident_id else "", analysis_results, tool_context
                )
            else:
                # Request approval
                return await self._request_approval(
                    incident_id if incident_id else "", analysis_results, tool_context
                )

        elif workflow_stage == "remediation_complete":
            # Remediation completed
            remediation_results = results

            # Update workflow
            if hasattr(workflow_tool, 'execute'):
                await workflow_tool.execute(
                    tool_context,
                    action="transition",
                    incident_id=incident_id,
                    next_stage=WorkflowStage.COMMUNICATION.value,
                )

            # Initiate communication
            return await self._initiate_communication(
                incident_id if incident_id else "", remediation_results, tool_context
            )
        elif workflow_stage == "communication_complete":
            # Communication completed
            # Update workflow
            if hasattr(workflow_tool, 'execute'):
                await workflow_tool.execute(
                    tool_context,
                    action="transition",
                    incident_id=incident_id,
                    next_stage=WorkflowStage.COMPLETED.value,
                )

            # Mark workflow as completed
            if hasattr(workflow_tool, 'execute'):
                await workflow_tool.execute(
                    tool_context,
                    action="update",
                    incident_id=incident_id,
                    updates={
                        "status": WorkflowStatus.COMPLETED.value,
                        "completed_at": datetime.utcnow(),
                    },
                )

            # Remove from active workflows
            self._active_workflows.discard(incident_id)

            # Process next queued incident if any
            if self._workflow_queue:
                next_incident = self._workflow_queue.pop(0)
                await self._process_incident(
                    next_incident["incident"], next_incident["priority"], tool_context
                )

            return {
                "status": "success",
                "message": f"Workflow completed for incident {incident_id}",
                "workflow_stage": WorkflowStage.COMPLETED.value,
            }

        return {
            "status": "success",
            "message": f"Processed transfer from {from_agent}",
            "workflow_stage": workflow_stage,
        }

    async def _perform_orchestration(
        self, context: Any, _config: Optional[RunConfig], **_kwargs: Any
    ) -> Dict[str, Any]:
        """Perform regular orchestration tasks."""
        orchestration_results = {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "active_workflows": len(self._active_workflows),
            "queued_workflows": len(self._workflow_queue),
            "tasks_performed": [],
        }

        try:
            # Use the passed context or create a mock one
            if context and hasattr(context, '__class__'):
                tool_context = context
            else:
                tool_context = type("MockToolContext", (), {
                    "data": {},
                    "actions": None,
                    "invocation_context": None,
                    "function_call_id": None
                })()
            workflow_tool = self.tools[0]  # WorkflowManagementTool

            # Check for stalled workflows
            for workflow_id in list(self._active_workflows):
                workflow_result = {}
                if hasattr(workflow_tool, 'execute'):
                    workflow_result = await workflow_tool.execute(
                        tool_context, action="get", incident_id=workflow_id
                    )

                if workflow_result.get("status") == "success":
                    workflow = workflow_result.get("workflow", {})

                    # Check for timeout
                    timeout_at = workflow.get("timeout_at")
                    if timeout_at and datetime.utcnow() > datetime.fromisoformat(
                        timeout_at
                    ):
                        await self._handle_workflow_timeout(
                            workflow_id, workflow, tool_context
                        )
                        tasks_performed = orchestration_results.get("tasks_performed", [])
                        if isinstance(tasks_performed, list):
                            tasks_performed.append(
                                f"Handled timeout for {workflow_id}"
                            )

                    # Check for stalled stages
                    updated_at = workflow.get("updated_at")
                    if updated_at and (
                        datetime.utcnow() - datetime.fromisoformat(updated_at)
                    ) > timedelta(minutes=30):
                        await self._handle_stalled_workflow(
                            workflow_id, workflow, tool_context
                        )
                        tasks_performed = orchestration_results.get("tasks_performed", [])
                        if isinstance(tasks_performed, list):
                            tasks_performed.append(
                                f"Handled stalled workflow {workflow_id}"
                            )

            # Process queued workflows if capacity available
            while (
                self._workflow_queue
                and len(self._active_workflows) < self._max_concurrent_workflows
            ):
                next_incident = self._workflow_queue.pop(0)
                await self._process_incident(
                    next_incident["incident"], next_incident["priority"], tool_context
                )
                tasks_performed = orchestration_results.get("tasks_performed", [])
                if isinstance(tasks_performed, list):
                    tasks_performed.append(
                        f"Started queued workflow for {next_incident['incident']['id']}"
                    )

            return orchestration_results

        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            logger.error("Error during orchestration: %s", e)
            orchestration_results["status"] = "error"
            orchestration_results["error"] = str(e)
            return orchestration_results

    async def _process_incident(
        self, incident: Dict[str, Any], priority: float, context: ToolContext
    ) -> Dict[str, Any]:
        """Process a new incident through the workflow."""
        incident_id = incident.get("id", "")
        if incident_id:
            self._active_workflows.add(incident_id)

        # Update workflow to analysis stage
        workflow_tool = self.tools[0]
        if hasattr(workflow_tool, 'execute'):
            await workflow_tool.execute(
                context,
                action="transition",
                incident_id=incident_id,
                next_stage=WorkflowStage.ANALYSIS.value,
            )

        # Transfer to analysis agent
        analysis_tool = self.tools[2]  # TransferToAnalysisAgentTool
        if hasattr(analysis_tool, 'execute'):
            await analysis_tool.execute(
                context,
                incident_id=incident_id,
                workflow_stage="analysis_requested",
                results={"incident": incident, "priority": priority},
            )

        return {
            "status": "success",
            "message": f"Incident {incident_id} sent for analysis",
            "priority": priority,
        }

    async def _initiate_remediation(
        self, incident_id: str, analysis: Dict[str, Any], context: ToolContext
    ) -> Dict[str, Any]:
        """Initiate remediation based on analysis."""
        # Update workflow
        workflow_tool = self.tools[0]
        if hasattr(workflow_tool, 'execute'):
            await workflow_tool.execute(
                context,
                action="transition",
                incident_id=incident_id,
                next_stage=WorkflowStage.REMEDIATION.value,
            )

        # Transfer to remediation agent
        remediation_tool = self.tools[3]  # TransferToRemediationAgentTool
        recommendations = analysis.get("stages", {}).get("recommendations", {})

        if hasattr(remediation_tool, 'execute'):
            await remediation_tool.execute(
                context,
                incident_id=incident_id,
                workflow_stage="remediation_requested",
                results={
                    "incident_id": incident_id,
                    "analysis": analysis.get("stages", {}).get("ai_analysis", {}),
                    "recommendations": recommendations.get("immediate_actions", []),
                    "auto_approve": True,
                },
            )

        return {
            "status": "success",
            "message": f"Remediation initiated for incident {incident_id}",
        }

    async def _request_approval(
        self, incident_id: str, analysis: Dict[str, Any], context: ToolContext
    ) -> Dict[str, Any]:
        """Request approval for remediation."""
        # Update workflow
        workflow_tool = self.tools[0]
        if hasattr(workflow_tool, 'execute'):
            await workflow_tool.execute(
                context,
                action="update",
                incident_id=incident_id,
                updates={"approval_requested_at": datetime.utcnow()},
            )

        # Send approval request via communication agent
        comm_tool = self.tools[4]  # TransferToCommunicationAgentTool
        if hasattr(comm_tool, 'execute'):
            await comm_tool.execute(
                context,
                incident_id=incident_id,
                workflow_stage="approval_request",
                results={
                    "analysis": analysis,
                    "channels": ["slack", "email"],
                    "priority": "high",
                },
            )

        return {
            "status": "success",
            "message": f"Approval requested for incident {incident_id}",
        }

    async def _initiate_communication(
        self, incident_id: str, remediation: Dict[str, Any], context: ToolContext
    ) -> Dict[str, Any]:
        """Initiate communication about remediation results."""
        # Transfer to communication agent
        comm_tool = self.tools[4]  # TransferToCommunicationAgentTool
        if hasattr(comm_tool, 'execute'):
            await comm_tool.execute(
                context,
                incident_id=incident_id,
                workflow_stage="remediation_summary",
                results={
                    "remediation_results": remediation,
                    "channels": ["slack", "email"],
                    "priority": "medium",
                },
            )

        return {
            "status": "success",
            "message": f"Communication initiated for incident {incident_id}",
        }

    async def _handle_workflow_timeout(
        self, workflow_id: str, workflow: Dict[str, Any], context: ToolContext
    ) -> None:
        """Handle workflow timeout."""
        logger.warning("Workflow %s timed out", workflow_id)

        # Update workflow status
        workflow_tool = self.tools[0]
        if hasattr(workflow_tool, 'execute'):
            await workflow_tool.execute(
                context,
                action="update",
                incident_id=workflow_id,
                updates={
                    "status": WorkflowStatus.TIMEOUT.value,
                    "timeout_handled_at": datetime.utcnow(),
                },
            )

        # Notify via communication agent
        comm_tool = self.tools[4]
        if hasattr(comm_tool, 'execute'):
            await comm_tool.execute(
                context,
                incident_id=workflow_id,
                workflow_stage="timeout_notification",
                results={"workflow": workflow, "channels": ["slack"], "priority": "high"},
            )

        # Remove from active workflows
        self._active_workflows.discard(workflow_id)

    async def _handle_stalled_workflow(
        self, workflow_id: str, workflow: Dict[str, Any], context: ToolContext
    ) -> None:
        """Handle stalled workflow."""
        current_stage = workflow.get("current_stage")
        logger.warning("Workflow %s stalled at stage %s", workflow_id, current_stage)

        # Attempt to restart the stage
        if current_stage == WorkflowStage.ANALYSIS.value:
            # Re-send to analysis
            analysis_tool = self.tools[2]
            if hasattr(analysis_tool, 'execute'):
                await analysis_tool.execute(
                    context,
                    incident_id=workflow_id,
                    workflow_stage="analysis_retry",
                    results=workflow.get("metadata", {}),
                )
        elif current_stage == WorkflowStage.REMEDIATION.value:
            # Skip to communication
            await self._initiate_communication(
                workflow_id, {"status": "skipped_due_to_stall"}, context
            )
