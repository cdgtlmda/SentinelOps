"""
Detection Agent using Google ADK - PRODUCTION IMPLEMENTATION

This agent monitors cloud logs for security anomalies and creates incidents.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from google.adk.tools import BaseTool, ToolContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.run_config import RunConfig
from google.cloud import bigquery

from src.common.adk_agent_base import SentinelOpsBaseAgent
from src.common.secure_query_builder import SecureQueryBuilder
from src.common.models import (
    Incident,
    IncidentStatus,
    SeverityLevel,
    SecurityEvent,
    EventSource,
)
from src.tools.transfer_tools import TransferToOrchestratorAgentTool

# Import business logic components and their tool wrappers
from src.detection_agent.rules_engine import RulesEngine
from src.detection_agent.event_correlator import EventCorrelator
from src.detection_agent.query_builder import QueryBuilder
from src.tools.detection_tools import (
    RulesEngineTool,
    EventCorrelatorTool,
    QueryBuilderTool,
    DeduplicatorTool,
)

logger = logging.getLogger(__name__)


class LogMonitoringTool(BaseTool):
    """Production-grade tool for monitoring BigQuery security logs."""

    def __init__(self, bigquery_client: bigquery.Client, dataset: str, table: str, project_id: str):
        """Initialize the log monitoring tool."""
        super().__init__(
            name="log_monitoring_tool",
            description="Monitor BigQuery security logs for security events",
        )
        self.bigquery_client = bigquery_client
        self.dataset = dataset
        self.table = table
        self.project_id = project_id

    async def execute(self, _context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Execute production log monitoring queries."""
        try:
            current_time = datetime.now()
            last_scan_time = kwargs.get(
                "last_scan_time", current_time - timedelta(minutes=5)
            )

            # Production detection queries
            # Create base table name (validated through config)
            # nosec B608 - table name components are validated config values, not user input
            table_name = (
                f"`{self.project_id}.{self.dataset}.cloudaudit_googleapis_com_activity`"
            )

            queries = {
                "failed_authentication": {
                    # Build query using secure query builder
                    "query": SecureQueryBuilder.build_select_query(
                        table_name.replace('`', ''),
                        [
                            "timestamp",
                            "protoPayload.authenticationInfo.principalEmail as actor",
                            "protoPayload.requestMetadata.callerIp as source_ip",
                            "protoPayload.methodName as method_name",
                            "protoPayload.status.code as status_code",
                            "protoPayload.status.message as error_message",
                            "resource.type as resource_type",
                            "resource.labels.project_id as project"
                        ],
                        [
                            "timestamp > TIMESTAMP(@last_scan_time)",
                            "timestamp <= TIMESTAMP(@current_time)",
                            "protoPayload.status.code IN (401, 403)"
                        ],
                        limit=1000
                    ) + "\nORDER BY timestamp DESC",
                    "params": [
                        bigquery.ScalarQueryParameter(
                            "last_scan_time", "STRING", last_scan_time.isoformat()
                        ),
                        bigquery.ScalarQueryParameter(
                            "current_time", "STRING", current_time.isoformat()
                        ),
                    ],
                },
                "privilege_escalation": {
                    # Build query using secure query builder
                    "query": SecureQueryBuilder.build_select_query(
                        table_name.replace('`', ''),
                        [
                            "timestamp",
                            "protoPayload.authenticationInfo.principalEmail as actor",
                            "protoPayload.requestMetadata.callerIp as source_ip",
                            "protoPayload.resourceName as resource_name",
                            "protoPayload.methodName as method_name",
                            "protoPayload.request.policy.bindings as bindings",
                            "resource.type as resource_type"
                        ],
                        [
                            "timestamp > TIMESTAMP(@last_scan_time)",
                            "timestamp <= TIMESTAMP(@current_time)",
                            "protoPayload.methodName IN ("
                            "'SetIamPolicy', 'UpdateRole', 'CreateRole', "
                            "'google.iam.admin.v1.CreateServiceAccount', "
                            "'google.iam.admin.v1.CreateServiceAccountKey')"
                        ],
                        limit=1000
                    ) + "\nORDER BY timestamp DESC",
                    "params": [
                        bigquery.ScalarQueryParameter(
                            "last_scan_time", "STRING", last_scan_time.isoformat()
                        ),
                        bigquery.ScalarQueryParameter(
                            "current_time", "STRING", current_time.isoformat()
                        ),
                    ],
                },
                "suspicious_api_activity": {
                    # Build query using secure query builder
                    "query": SecureQueryBuilder.build_select_query(
                        table_name.replace('`', ''),
                        [
                            "timestamp",
                            "protoPayload.authenticationInfo.principalEmail as actor",
                            "protoPayload.requestMetadata.callerIp as source_ip",
                            "protoPayload.methodName as method_name",
                            "protoPayload.resourceName as resource_name",
                            "protoPayload.requestMetadata.callerSuppliedUserAgent as user_agent",
                            "resource.type as resource_type"
                        ],
                        [
                            "timestamp > TIMESTAMP(@last_scan_time)",
                            "timestamp <= TIMESTAMP(@current_time)",
                            "(protoPayload.methodName LIKE '%Delete%' OR "
                            "protoPayload.methodName LIKE '%Remove%' OR "
                            "protoPayload.methodName LIKE '%Destroy%')"
                        ],
                        limit=1000
                    ) + "\nORDER BY timestamp DESC",
                    "params": [
                        bigquery.ScalarQueryParameter(
                            "last_scan_time", "STRING", last_scan_time.isoformat()
                        ),
                        bigquery.ScalarQueryParameter(
                            "current_time", "STRING", current_time.isoformat()
                        ),
                    ],
                },
                "firewall_modifications": {
                    # Build query using secure query builder
                    "query": SecureQueryBuilder.build_select_query(
                        table_name.replace('`', ''),
                        [
                            "timestamp",
                            "protoPayload.authenticationInfo.principalEmail as actor",
                            "protoPayload.requestMetadata.callerIp as source_ip",
                            "protoPayload.methodName as method_name",
                            "protoPayload.resourceName as resource_name",
                            "protoPayload.request.name as rule_name",
                            "protoPayload.request.sourceRanges as source_ranges",
                            "protoPayload.request.allowed as allowed_rules"
                        ],
                        [
                            "timestamp > TIMESTAMP(@last_scan_time)",
                            "timestamp <= TIMESTAMP(@current_time)",
                            "resource.type = 'gce_firewall_rule'",
                            "protoPayload.methodName IN ("
                            "'v1.compute.firewalls.insert', "
                            "'v1.compute.firewalls.patch', "
                            "'v1.compute.firewalls.delete')"
                        ],
                        limit=500
                    ) + "\nORDER BY timestamp DESC",
                    "params": [
                        bigquery.ScalarQueryParameter(
                            "last_scan_time", "STRING", last_scan_time.isoformat()
                        ),
                        bigquery.ScalarQueryParameter(
                            "current_time", "STRING", current_time.isoformat()
                        ),
                    ],
                },
            }

            # Execute queries and collect events
            all_events = []
            queries_executed = 0

            for query_type, query_info in queries.items():
                try:
                    logger.info("Executing %s detection query", query_type)
                    # Configure query with parameters
                    job_config = bigquery.QueryJobConfig(
                        query_parameters=query_info["params"]
                    )
                    query_job = self.bigquery_client.query(
                        str(query_info["query"]), job_config=job_config
                    )
                    results = query_job.result()
                    queries_executed += 1

                    for row in results:
                        event = {
                            "query_type": query_type,
                            "timestamp": (
                                row.timestamp.isoformat()
                                if hasattr(row, "timestamp")
                                else datetime.now().isoformat()
                            ),
                            "actor": getattr(row, "actor", "unknown"),
                            "source_ip": getattr(row, "source_ip", "unknown"),
                            "method_name": getattr(row, "method_name", "unknown"),
                            "resource_type": getattr(row, "resource_type", "unknown"),
                            "raw_data": dict(row),
                        }

                        # Add query-specific fields
                        if query_type == "failed_authentication":
                            event["status_code"] = getattr(row, "status_code", 0)
                            event["error_message"] = getattr(row, "error_message", "")
                        elif query_type == "privilege_escalation":
                            event["resource_name"] = getattr(row, "resource_name", "")
                            event["bindings"] = getattr(row, "bindings", [])
                        elif query_type == "suspicious_api_activity":
                            event["user_agent"] = getattr(row, "user_agent", "")
                            event["resource_name"] = getattr(row, "resource_name", "")
                        elif query_type == "firewall_modifications":
                            event["rule_name"] = getattr(row, "rule_name", "")
                            event["source_ranges"] = getattr(row, "source_ranges", [])
                            event["allowed_rules"] = getattr(row, "allowed_rules", [])

                        all_events.append(event)

                except (ValueError, RuntimeError, KeyError) as e:
                    logger.error("Error executing %s query: %s", query_type, e)

            return {
                "status": "success",
                "events": all_events,
                "queries_executed": queries_executed,
                "scan_time": current_time.isoformat(),
            }

        except (ValueError, RuntimeError, KeyError) as e:
            logger.error("Error in log monitoring: %s", e, exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "events": [],
                "queries_executed": 0,
            }


class AnomalyDetectionTool(BaseTool):
    """Production anomaly detection tool with sophisticated rules."""

    def __init__(self, detection_rules: Dict[str, Any], _metrics_client: Optional[Any] = None):
        """Initialize with detection rules configuration."""
        super().__init__(
            name="anomaly_detection_tool",
            description="Apply detection rules to identify security anomalies",
        )
        self.detection_rules = detection_rules

    async def execute(self, _context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Apply production detection rules to identify anomalies."""
        events = kwargs.get("events", [])
        anomalies = []

        try:
            # Production detection rules
            for event_group in events:
                # Multiple failed authentications from same IP
                if self._check_brute_force_pattern(event_group):
                    anomalies.append(
                        {
                            "type": "brute_force_attempt",
                            "severity": "high",
                            "confidence": 0.9,
                            "event": event_group[0],
                            "related_events": event_group,
                            "detected_at": datetime.now().isoformat(),
                            "description": (
                                f"Multiple failed authentication attempts from "
                                f"{event_group[0].get('source_ip')}"
                            ),
                        }
                    )

                # Privilege escalation followed by suspicious activity
                if self._check_privilege_escalation_pattern(event_group):
                    anomalies.append(
                        {
                            "type": "privilege_escalation_abuse",
                            "severity": "critical",
                            "confidence": 0.85,
                            "event": event_group[0],
                            "related_events": event_group,
                            "detected_at": datetime.now().isoformat(),
                            "description": (
                                f"Privilege escalation by {event_group[0].get('actor')} "
                                f"followed by suspicious activity"
                            ),
                        }
                    )

                # Rapid API deletions
                if self._check_destructive_pattern(event_group):
                    anomalies.append(
                        {
                            "type": "potential_data_destruction",
                            "severity": "critical",
                            "confidence": 0.8,
                            "event": event_group[0],
                            "related_events": event_group,
                            "detected_at": datetime.now().isoformat(),
                            "description": f"Rapid deletion operations by {event_group[0].get('actor')}",
                        }
                    )

                # Firewall rule weakening
                if self._check_firewall_weakening(event_group):
                    anomalies.append(
                        {
                            "type": "security_control_weakening",
                            "severity": "high",
                            "confidence": 0.75,
                            "event": event_group[0],
                            "related_events": event_group,
                            "detected_at": datetime.now().isoformat(),
                            "description": "Firewall rules modified to allow broader access",
                        }
                    )

            return {
                "status": "success",
                "anomalies": anomalies,
                "events_analyzed": len(events),
            }

        except (ValueError, RuntimeError, KeyError) as e:
            logger.error("Error in anomaly detection: %s", e, exc_info=True)
            return {"status": "error", "error": str(e), "anomalies": []}

    def _check_brute_force_pattern(self, events: List[Dict[str, Any]]) -> bool:
        """Check for brute force authentication patterns."""
        if not events:
            return False

        failed_auth_events = [
            e for e in events if e.get("query_type") == "failed_authentication"
        ]
        if len(failed_auth_events) >= 5:
            # Check if from same IP within short time
            first_event = failed_auth_events[0]
            source_ip = first_event.get("source_ip")

            same_ip_count = sum(
                1 for e in failed_auth_events if e.get("source_ip") == source_ip
            )
            return same_ip_count >= 5

        return False

    def _check_privilege_escalation_pattern(self, events: List[Dict[str, Any]]) -> bool:
        """Check for privilege escalation followed by suspicious activity."""
        if len(events) < 2:
            return False

        # Look for privilege escalation
        priv_esc_events = [
            e for e in events if e.get("query_type") == "privilege_escalation"
        ]
        if not priv_esc_events:
            return False

        # Look for subsequent suspicious activity by same actor
        actor = priv_esc_events[0].get("actor")
        subsequent_suspicious = [
            e
            for e in events
            if e.get("actor") == actor
            and e.get("query_type")
            in ["suspicious_api_activity", "firewall_modifications"]
            and e.get("timestamp", "") > priv_esc_events[0].get("timestamp", "")
        ]

        return len(subsequent_suspicious) > 0

    def _check_destructive_pattern(self, events: List[Dict[str, Any]]) -> bool:
        """Check for rapid deletion operations."""
        if not events:
            return False

        delete_events = [
            e
            for e in events
            if e.get("query_type") == "suspicious_api_activity"
            and any(
                keyword in e.get("method_name", "").lower()
                for keyword in ["delete", "destroy", "remove"]
            )
        ]

        # More than 10 deletions in the time window is suspicious
        return len(delete_events) >= 10

    def _check_firewall_weakening(self, events: List[Dict[str, Any]]) -> bool:
        """Check for firewall rules being weakened."""
        if not events:
            return False

        firewall_events = [
            e for e in events if e.get("query_type") == "firewall_modifications"
        ]

        for event in firewall_events:
            source_ranges = event.get("source_ranges", [])
            # Check for overly permissive rules
            if "0.0.0.0/0" in source_ranges or "::/0" in source_ranges:
                return True

        return False


class IncidentCreationTool(BaseTool):
    """Tool for creating security incidents from detected anomalies."""

    def __init__(self) -> None:
        """Initialize the incident creation tool."""
        super().__init__(
            name="incident_creation_tool",
            description="Create security incidents from detected anomalies",
        )

    async def execute(self, _context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Create an incident from anomaly data."""
        anomaly = kwargs.get("anomaly", {})

        try:
            # Map severity string to SeverityLevel enum
            severity_str = anomaly.get("severity", "medium").lower()
            severity_map = {
                "critical": SeverityLevel.CRITICAL,
                "high": SeverityLevel.HIGH,
                "medium": SeverityLevel.MEDIUM,
                "low": SeverityLevel.LOW,
                "informational": SeverityLevel.INFORMATIONAL,
            }
            severity = severity_map.get(severity_str, SeverityLevel.MEDIUM)

            # Create security event from anomaly data
            event = SecurityEvent(
                event_type=anomaly.get("type", "security_anomaly"),
                source=EventSource(
                    source_type="bigquery_logs",
                    source_name="adk_detection_agent",
                    source_id="detection_scan",
                ),
                severity=severity,
                description=anomaly.get("description", "Security anomaly detected"),
                actor=anomaly.get("event", {}).get("actor"),
                raw_data=anomaly.get("event", {}),
            )

            # Create incident model
            incident = Incident(
                title=f"{anomaly.get('type', 'Unknown')} detected",
                description=anomaly.get("description", "Security anomaly detected"),
                severity=severity,
                status=IncidentStatus.DETECTED,
                events=[event],
                metadata={
                    "detection_source": "adk_detection_agent",
                    "anomaly_type": anomaly.get("type"),
                    "confidence": anomaly.get("confidence", 0.5),
                    "actor": anomaly.get("event", {}).get("actor", "unknown"),
                    "source_ip": anomaly.get("event", {}).get("source_ip", "unknown"),
                    "related_events_count": len(anomaly.get("related_events", [])),
                    "detection_time": anomaly.get(
                        "detected_at", datetime.now().isoformat()
                    ),
                },
            )

            # Store incident (in production, this would persist to Firestore)
            logger.info(
                "Created incident: %s - %s", incident.incident_id, incident.title
            )

            return {
                "status": "success",
                "incident_id": incident.incident_id,
                "incident": incident.to_dict(),
            }

        except (ValueError, RuntimeError, KeyError) as e:
            logger.error("Error creating incident: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}


class DetectionAgent(SentinelOpsBaseAgent):
    """Production ADK Detection Agent for monitoring security logs."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Detection Agent with production configuration."""
        # Store configuration first
        stored_config = config.copy()

        # Extract configuration
        project_id = config.get("project_id", "")
        scan_interval = config.get("scan_interval_minutes", 5)
        bigquery_dataset = config.get("bigquery_dataset", "security_logs")
        bigquery_table = config.get("bigquery_table", "events")

        # Initialize BigQuery client
        bigquery_client = bigquery.Client(project=project_id)

        # Initialize business logic components
        rules_engine = RulesEngine()
        correlation_config = config.get("correlation", {})
        event_correlator = EventCorrelator(
            correlation_window_minutes=correlation_config.get("time_window_minutes", 60)
        )
        query_builder = QueryBuilder()  # No arguments needed

        # Initialize production tools
        tools = [
            LogMonitoringTool(
                bigquery_client, bigquery_dataset, bigquery_table, project_id=project_id
            ),
            AnomalyDetectionTool(config.get("detection_rules", {})),
            IncidentCreationTool(),
            TransferToOrchestratorAgentTool(),
            # Add business logic tools
            RulesEngineTool(rules_engine),
            EventCorrelatorTool(event_correlator),
            QueryBuilderTool(query_builder),
            DeduplicatorTool(config.get("deduplication", {})),
        ]

        # Initialize base agent
        super().__init__(
            name="detection_agent",
            description="Production security detection agent monitoring cloud logs",
            config=config,
            model="gemini-pro",
            tools=tools,
        )

        # Store components after initialization
        self._stored_config = stored_config
        self._stored_config["rules_engine"] = rules_engine
        self._stored_config["event_correlator"] = event_correlator
        self._stored_config["query_builder"] = query_builder
        self._stored_config["last_scan_time"] = datetime.now() - timedelta(
            minutes=scan_interval
        )

    async def _execute_agent_logic(
        self, context: Any, config: Optional[RunConfig], **kwargs: Any
    ) -> Dict[str, Any]:
        """Execute the detection agent's core logic."""
        try:
            # Regular detection scan
            return await self._perform_detection_scan(context, config, **kwargs)

        except (ValueError, RuntimeError, KeyError) as e:
            logger.error("Error in detection agent: %s", e, exc_info=True)
            return await self.handle_error(e, context)

    async def _perform_detection_scan(
        self, context: InvocationContext, _config: Optional[RunConfig], **_kwargs: Any
    ) -> Dict[str, Any]:
        """Perform production security detection scan."""
        scan_results = {
            "status": "success",
            "scan_id": f"scan_{datetime.now().timestamp()}",
            "scan_time": datetime.now().isoformat(),
            "incidents_created": [],
            "events_processed": 0,
            "anomalies_detected": 0,
            "errors": [],
        }

        try:
            # Step 1: Monitor logs
            log_tool = self.tools[0]  # LogMonitoringTool
            tool_context = ToolContext(invocation_context=context)

            if hasattr(log_tool, 'execute'):
                log_results = await log_tool.execute(
                    tool_context, last_scan_time=self._stored_config["last_scan_time"]
                )
            else:
                log_results = {"status": "error", "error": "Tool does not have execute method"}

            if log_results.get("status") != "success":
                errors_list = scan_results["errors"]
                if isinstance(errors_list, list):
                    errors_list.append(
                        f"Log monitoring failed: {log_results.get('error')}"
                    )
                return scan_results

            events = log_results.get("events", [])
            scan_results["events_processed"] = len(events)

            # Update last scan time
            self._stored_config["last_scan_time"] = datetime.now()

            if not events:
                logger.info("No new events detected in this scan")
                return scan_results

            # Step 2: Correlate and group events
            correlated_events = self._correlate_events(events)

            # Step 3: Detect anomalies
            anomaly_tool = self.tools[1]  # AnomalyDetectionTool
            if hasattr(anomaly_tool, 'execute'):
                anomaly_results = await anomaly_tool.execute(
                    tool_context, events=correlated_events
                )
            else:
                anomaly_results = {"status": "error", "error": "Tool does not have execute method"}

            anomalies = anomaly_results.get("anomalies", [])
            scan_results["anomalies_detected"] = len(anomalies)

            if not anomalies:
                logger.info("Processed %s events, no anomalies detected", len(events))
                return scan_results

            # Step 4: Create incidents and transfer to orchestrator
            incident_tool = self.tools[2]  # IncidentCreationTool
            transfer_tool = self.tools[3]  # TransferToOrchestratorAgentTool

            for anomaly in anomalies:
                # Create incident
                if hasattr(incident_tool, 'execute'):
                    incident_result = await incident_tool.execute(
                        tool_context, anomaly=anomaly
                    )
                else:
                    incident_result = {"status": "error", "error": "Tool does not have execute method"}

                if incident_result.get("status") == "success":
                    incident_id = incident_result.get("incident_id")
                    incidents_list = scan_results["incidents_created"]
                    if isinstance(incidents_list, list):
                        incidents_list.append(incident_id)

                    # Transfer to orchestrator
                    if hasattr(transfer_tool, 'execute'):
                        transfer_result = await transfer_tool.execute(
                            tool_context,
                            incident_id=incident_id,
                            workflow_stage="detection_complete",
                            results={
                                "incident": incident_result.get("incident"),
                                "anomaly": anomaly,
                                "scan_id": scan_results["scan_id"],
                            },
                        )
                    else:
                        transfer_result = {"status": "error", "error": "Tool does not have execute method"}

                    if transfer_result.get("status") != "success":
                        errors_list = scan_results["errors"]
                        if isinstance(errors_list, list):
                            errors_list.append(
                                f"Failed to transfer incident {incident_id}: "
                                f"{transfer_result.get('error')}"
                            )

            logger.info(
                "Detection scan complete: %s anomalies, %s incidents created",
                scan_results["anomalies_detected"],
                len(scan_results["incidents_created"]) if isinstance(scan_results["incidents_created"], list) else 0,
            )

            return scan_results

        except (ValueError, RuntimeError, KeyError) as e:
            logger.error("Error during detection scan: %s", e, exc_info=True)
            scan_results["status"] = "error"
            errors_list = scan_results["errors"]
            if isinstance(errors_list, list):
                errors_list.append(str(e))
            return scan_results

    def _correlate_events(self, events: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Correlate related events for anomaly detection."""
        # Group events by actor and time window
        correlated = []
        processed = set()

        for i, event in enumerate(events):
            if i in processed:
                continue

            group = [event]
            processed.add(i)

            actor = event.get("actor", "")
            source_ip = event.get("source_ip", "")
            event_time = datetime.fromisoformat(
                event.get("timestamp", datetime.now().isoformat())
            )

            # Find related events within 10 minute window
            for j, other in enumerate(events[i + 1 :], start=i + 1):
                if j in processed:
                    continue

                other_time = datetime.fromisoformat(
                    other.get("timestamp", datetime.now().isoformat())
                )

                # Group by same actor or IP within time window
                if abs(event_time - other_time) <= timedelta(minutes=10):
                    if (actor and actor == other.get("actor")) or (
                        source_ip and source_ip == other.get("source_ip")
                    ):
                        group.append(other)
                        processed.add(j)

            correlated.append(group)

        return correlated

    async def _handle_transfer(
        self, context: Any, transfer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle incoming transfer from another agent."""
        config = None  # Use default config for transfers

        logger.info(
            "Detection agent received transfer: %s",
            transfer_data.get("from_agent", "unknown"),
        )

        # Process based on transfer type
        if transfer_data.get("action") == "manual_scan":
            return await self._perform_detection_scan(context, config)

        return {
            "status": "success",
            "message": "Transfer processed",
            "transfer_data": transfer_data,
        }
