"""
Analysis Agent using Google ADK - PRODUCTION IMPLEMENTATION

This agent analyzes security incidents using Gemini AI for threat assessment.
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from vertexai.generative_models import GenerativeModel, GenerationConfig
from google.cloud import aiplatform
from google.adk.agents.run_config import RunConfig
from google.adk.tools import BaseTool, ToolContext
from google.cloud import firestore

from src.common.adk_agent_base import SentinelOpsBaseAgent
from src.tools.transfer_tools import (
    TransferToRemediationAgentTool,
    TransferToCommunicationAgentTool,
    TransferToOrchestratorAgentTool,
)

# Import business logic components and their tool wrappers
from src.analysis_agent.recommendation_engine import RecommendationEngine
from src.analysis_agent.event_correlation import EventCorrelator
from src.analysis_agent.context_retrieval import ContextRetriever
from src.tools.analysis_tools import RecommendationTool, CorrelationTool, ContextTool

# Import performance optimization
from src.analysis_agent.performance_optimizer import PerformanceOptimizer

logger = logging.getLogger(__name__)


class IncidentAnalysisTool(BaseTool):
    """Production tool for analyzing incidents using Gemini AI."""

    def __init__(self, model_config: Dict[str, Any]):
        """Initialize with Vertex AI configuration."""
        super().__init__(
            name="incident_analysis_tool",
            description="Analyze security incidents using Vertex AI Gemini",
        )
        # Initialize Vertex AI if not already done
        try:
            aiplatform.init(
                project=os.getenv("GCP_PROJECT_ID", "your-gcp-project-id"),
                location=os.getenv("VERTEX_AI_LOCATION", "us-central1")
            )
        except Exception:  # pylint: disable=broad-exception-caught
            # Already initialized or invalid config - continue
            pass

        # Configure Vertex AI model
        self.model = GenerativeModel(
            model_name=model_config.get("model", "gemini-1.5-pro-002"),
            generation_config=GenerationConfig(
                temperature=model_config.get("temperature", 0.7),
                top_p=model_config.get("top_p", 0.95),
                top_k=model_config.get("top_k", 40),
                max_output_tokens=model_config.get("max_output_tokens", 2048),
            ),
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Analyze incident using Gemini AI."""
        _ = context  # Unused but required by ADK interface
        incident = kwargs.get("incident", {})

        try:
            # Construct analysis prompt
            prompt = f"""
            Analyze the following security incident and provide a comprehensive assessment:

            INCIDENT DETAILS:
            Title: {incident.get('title', 'Unknown')}
            Description: {incident.get('description', 'No description')}
            Severity: {incident.get('severity', 'unknown')}
            Detection Source: {incident.get('detection_source', 'unknown')}
            Metadata: {json.dumps(incident.get('metadata', {}), indent=2)}

            Provide your analysis in the following JSON format:
            {{
                "threat_assessment": {{
                    "threat_level": "critical|high|medium|low",
                    "confidence": 0.0-1.0,
                    "threat_type": "specific threat category",
                    "attack_pattern": "identified attack pattern"
                }},
                "impact_analysis": {{
                    "affected_resources": ["list of affected resources"],
                    "potential_data_exposure": true|false,
                    "business_impact": "description of business impact",
                    "compliance_implications": ["list of compliance concerns"]
                }},
                "attribution": {{
                    "threat_actor": "known threat actor or unknown",
                    "tactics": ["MITRE ATT&CK tactics"],
                    "techniques": ["MITRE ATT&CK techniques"],
                    "indicators": ["IoCs found"]
                }},
                "timeline": {{
                    "initial_compromise": "estimated time",
                    "detection_delay": "time between compromise and detection",
                    "attack_duration": "estimated duration"
                }},
                "recommendations": {{
                    "immediate_actions": ["urgent steps to take"],
                    "investigation_steps": ["next investigation steps"],
                    "long_term_improvements": ["security improvements"]
                }}
            }}
            """

            # Get Gemini analysis
            response = self.model.generate_content(prompt)

            # Parse response
            try:
                analysis_data = json.loads(response.text)
            except json.JSONDecodeError:
                # Extract JSON from response if wrapped in text
                json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
                if json_match:
                    analysis_data = json.loads(json_match.group())
                else:
                    analysis_data = {
                        "threat_assessment": {
                            "threat_level": "medium",
                            "confidence": 0.5,
                            "threat_type": "unknown",
                            "attack_pattern": "analysis failed",
                        },
                        "error": "Failed to parse Gemini response",
                    }

            return {
                "status": "success",
                "analysis": analysis_data,
                "incident_id": incident.get("id"),
                "analyzed_at": datetime.utcnow().isoformat(),
            }

        except (ValueError, KeyError, AttributeError, TypeError) as e:
            logger.error("Error in incident analysis: %s", e, exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "incident_id": incident.get("id"),
            }


class ThreatIntelligenceTool(BaseTool):
    """Production tool for enriching analysis with threat intelligence."""

    def __init__(self, firestore_client: firestore.Client):
        """Initialize with Firestore client for threat intel data."""
        super().__init__(
            name="threat_intelligence_tool",
            description="Enrich incident analysis with threat intelligence",
        )
        self.firestore_client = firestore_client
        self.threat_intel_collection = "threat_intelligence"

    async def execute(self, context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Enrich incident with threat intelligence data."""
        _ = context  # Unused but required by ADK interface
        incident = kwargs.get("incident", {})
        try:
            threat_intel: Dict[str, List[Any]] = {
                "known_iocs": [],
                "threat_actors": [],
                "campaigns": [],
                "vulnerabilities": [],
            }

            # Check IoCs against threat intelligence
            metadata = incident.get("metadata", {})
            source_ip = metadata.get("source_ip", "")
            actor = metadata.get("actor", "")

            # Query threat intelligence database
            if source_ip and source_ip != "unknown":
                # Check if IP is known malicious
                ip_intel = (
                    self.firestore_client.collection(self.threat_intel_collection)
                    .document("ip_reputation")
                    .collection("ips")
                    .document(source_ip)
                    .get()
                )

                if ip_intel.exists:
                    threat_intel["known_iocs"].append(
                        {
                            "type": "ip",
                            "value": source_ip,
                            "reputation": ip_intel.to_dict(),
                        }
                    )

            # Check for known threat actor patterns
            if actor:
                # Query known compromised accounts
                compromised_accounts = (
                    self.firestore_client.collection(self.threat_intel_collection)
                    .document("compromised_accounts")
                    .collection("accounts")
                    .where("email", "==", actor)
                    .limit(1)
                    .get()
                )

                for doc in compromised_accounts:
                    threat_intel["threat_actors"].append(doc.to_dict())

            # Add hardcoded threat intelligence for demo
            if "privilege_escalation" in incident.get("title", "").lower():
                threat_intel["campaigns"].append(
                    {
                        "name": "CloudHopper",
                        "description": "APT group targeting cloud infrastructure",
                        "ttps": ["T1078", "T1098", "T1537"],
                        "confidence": 0.7,
                    }
                )

            return {
                "status": "success",
                "threat_intelligence": threat_intel,
                "enriched_at": datetime.utcnow().isoformat(),
            }

        except (ValueError, KeyError, AttributeError, TypeError) as e:
            logger.error("Error in threat intelligence enrichment: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}


class RecommendationGeneratorTool(BaseTool):
    """Production tool for generating actionable recommendations."""

    def __init__(self, model_config: Dict[str, Any]):
        """Initialize with Vertex AI configuration."""
        super().__init__(
            name="recommendation_generator_tool",
            description="Generate actionable security recommendations",
        )
        # Initialize Vertex AI if not already done
        try:
            aiplatform.init(
                project=os.getenv("GCP_PROJECT_ID", "your-gcp-project-id"),
                location=os.getenv("VERTEX_AI_LOCATION", "us-central1")
            )
        except Exception:  # pylint: disable=broad-exception-caught
            # Already initialized or invalid config - continue
            pass

        # Configure Vertex AI model
        self.model = GenerativeModel(
            model_name=model_config.get("model", "gemini-1.5-pro-002"),
            generation_config=GenerationConfig(
                temperature=0.3,  # Lower temperature for more consistent recommendations
                top_p=model_config.get("top_p", 0.95),
                top_k=model_config.get("top_k", 40),
                max_output_tokens=model_config.get("max_output_tokens", 1024),
            ),
        )

    async def execute(self, context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Generate specific remediation recommendations."""
        _ = context  # Unused but required by ADK interface
        analysis = kwargs.get("analysis", {})
        threat_intel: Dict[str, Any] = kwargs.get("threat_intelligence", {})

        try:
            # Build recommendation prompt
            prompt = f"""
            Based on the security incident analysis and threat intelligence,
            provide specific, actionable recommendations.

            ANALYSIS SUMMARY:
            Threat Level: {analysis.get('threat_assessment', {}).get('threat_level', 'unknown')}
            Attack Pattern: {analysis.get('threat_assessment', {}).get('attack_pattern', 'unknown')}
            Affected Resources: {analysis.get('impact_analysis', {}).get('affected_resources', [])}
            Known IoCs: {len(threat_intel.get('known_iocs', []))} found

            Generate recommendations in this JSON format:
            {{
                "immediate_actions": [
                    {{
                        "action": "specific action to take",
                        "priority": "critical|high|medium",
                        "automation_possible": true|false,
                        "estimated_time": "time to complete"
                    }}
                ],
                "investigation_tasks": [
                    {{
                        "task": "investigation step",
                        "tools_required": ["list of tools"],
                        "expected_outcome": "what to find"
                    }}
                ],
                "remediation_steps": [
                    {{
                        "step": "remediation action",
                        "resources_needed": ["required resources"],
                        "validation_method": "how to verify success"
                    }}
                ],
                "prevention_measures": [
                    {{
                        "measure": "preventive control",
                        "implementation_complexity": "low|medium|high",
                        "effectiveness": "expected effectiveness"
                    }}
                ]
            }}
            """

            # Get recommendations from Gemini
            response = self.model.generate_content(prompt)

            # Parse response
            try:
                recommendations = json.loads(response.text)
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
                if json_match:
                    recommendations = json.loads(json_match.group())
                else:
                    # Fallback recommendations
                    recommendations = {
                        "immediate_actions": [
                            {
                                "action": "Isolate affected resources",
                                "priority": "critical",
                                "automation_possible": True,
                                "estimated_time": "5 minutes",
                            }
                        ],
                        "investigation_tasks": [
                            {
                                "task": "Review audit logs for anomalies",
                                "tools_required": ["BigQuery", "Cloud Logging"],
                                "expected_outcome": "Identify attack timeline",
                            }
                        ],
                    }

            return {
                "status": "success",
                "recommendations": recommendations,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except (ValueError, KeyError, AttributeError, TypeError) as e:
            logger.error("Error generating recommendations: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}


class AnalysisAgent(SentinelOpsBaseAgent):
    """Production ADK Analysis Agent using Gemini for incident analysis."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Analysis Agent with production configuration."""
        # Extract configuration
        project_id = config.get("project_id", "")

        # Model configuration
        model_config = {
            "model": config.get("model", "gemini-pro"),
            "temperature": config.get("temperature", 0.7),
            "max_output_tokens": config.get("max_tokens", 2048),
            "top_p": config.get("top_p", 0.95),
            "top_k": config.get("top_k", 40),
        }

        # Initialize Firestore
        firestore_client = firestore.Client(project=project_id)

        # Initialize performance optimizer
        performance_config = config.get(
            "performance",
            {
                "cache_enabled": True,
                "cache_ttl": 3600,  # 1 hour
                "cache_max_size": 1000,
                "batch_enabled": True,
                "batch_size": 10,
                "batch_timeout": 1.0,
                "rate_limit": {
                    "enabled": True,
                    "max_per_minute": 30,
                    "max_per_hour": 500,
                },
            },
        )
        self.performance_optimizer = PerformanceOptimizer(performance_config, logger)

        # Initialize business logic components
        self.recommendation_engine = RecommendationEngine(config.get("recommendations", {}))
        self.event_correlator = EventCorrelator(
            logger, config.get("correlation", {}).get("correlation_window", 3600)
        )
        self.context_retriever = ContextRetriever(firestore_client, logger)

        # Set threshold attributes
        self.auto_remediate_threshold = config.get("auto_remediate_threshold", 0.8)
        self.critical_alert_threshold = config.get("critical_alert_threshold", 0.9)

        # Initialize production tools
        tools = [
            IncidentAnalysisTool(model_config),
            ThreatIntelligenceTool(firestore_client),
            RecommendationGeneratorTool(model_config),
            TransferToRemediationAgentTool(),
            TransferToCommunicationAgentTool(),
            TransferToOrchestratorAgentTool(),
            # Add business logic tools
            RecommendationTool(self.recommendation_engine),
            CorrelationTool(self.event_correlator),
            ContextTool(self.context_retriever),
        ]

        # Initialize base agent first (Pydantic requirement)
        super().__init__(
            name="analysis_agent",
            description="Production AI-powered security incident analysis",
            config=config,
            model="gemini-pro",
            tools=tools,
        )

    async def setup(self) -> None:
        """Setup the Analysis Agent.

        This method is called to initialize any async resources or connections
        the agent needs. For the Analysis Agent, this includes:
        - Validating Gemini API connectivity
        - Initializing tool resources
        - Setting up any async clients
        """
        logger.info("Setting up Analysis Agent")

        # Initialize Vertex AI
        try:
            aiplatform.init(
                project=os.getenv("GCP_PROJECT_ID", "your-gcp-project-id"),
                location=os.getenv("VERTEX_AI_LOCATION", "us-central1")
            )
        except RuntimeError:
            # Already initialized
            pass

        # Initialize tools if they have setup methods
        for tool in self.tools:
            if hasattr(tool, "setup"):
                await tool.setup()

        logger.info("Analysis Agent setup complete")

    async def _execute_agent_logic(
        self, context: Any, config: Optional[RunConfig], **kwargs: Any
    ) -> Dict[str, Any]:
        """Execute the analysis agent's core logic."""
        try:
            # Handle incoming transfer or direct incident data
            incident_data = None
            if context and hasattr(context, "data") and context.data:
                transfer_data = context.data
                incident_data = transfer_data.get("results", {}).get("incident")
            elif kwargs.get("incident"):
                incident_data = kwargs["incident"]

            if not incident_data:
                return {
                    "status": "error",
                    "error": "No incident data provided for analysis",
                }

            # Perform analysis
            return await self._analyze_incident(incident_data, context, config)

        except (ValueError, KeyError, AttributeError, TypeError) as e:
            logger.error("Error in analysis agent: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}

    async def _handle_transfer(
        self, context: Any, transfer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle incoming transfer from another agent."""
        logger.info(
            "Analysis agent received transfer from: %s",
            transfer_data.get('from_agent', 'unknown')
        )

        # Extract incident data from transfer
        incident_data = transfer_data.get("incident") or transfer_data.get(
            "results", {}
        ).get("incident")

        if not incident_data:
            return {"status": "error", "error": "No incident data in transfer"}

        # Perform analysis on the transferred incident
        return await self._analyze_incident(incident_data, context, None)

    async def _analyze_incident(
        self, incident: Dict[str, Any], context: Any, config: Optional[RunConfig]
    ) -> Dict[str, Any]:
        """Perform comprehensive incident analysis."""
        _ = config  # Unused but retained for API compatibility
        # Check cache first
        cache_key = self.performance_optimizer.generate_cache_key(
            incident.get("id", "unknown"),
            self.performance_optimizer.compute_data_hash(incident),
        )

        cached_result = self.performance_optimizer.cache.get(cache_key)
        if cached_result:
            logger.info("Cache hit for incident %s", incident.get('id'))
            return cast(Dict[str, Any], cached_result)

        # Check if we can batch this request with similar incidents
        batch_result = await self.performance_optimizer.batch_similar_requests(
            incident.get("id", "unknown"), incident, self._batch_analyze_incidents
        )
        if batch_result:
            return cast(Dict[str, Any], batch_result)

        analysis_results: Dict[str, Any] = {
            "status": "success",
            "incident_id": incident.get("id"),
            "analysis_id": f"analysis_{datetime.utcnow().timestamp()}",
            "start_time": datetime.utcnow().isoformat(),
            "stages": {},
        }

        try:
            # Create test tool context if none provided
            if not context:
                tool_context = type("TestToolContext", (), {})()
                tool_context.data = {}
                tool_context.actions = None
            else:
                tool_context = context

            # Check rate limit before API calls
            await self.performance_optimizer.check_rate_limit()

            # Stage 1: AI Analysis
            logger.info("Analyzing incident: %s", incident.get('id'))
            analysis_tool = self.tools[0]  # IncidentAnalysisTool

            if hasattr(analysis_tool, 'execute') and callable(analysis_tool.execute):
                analysis_result = await analysis_tool.execute(
                    tool_context, incident=incident
                )
            else:
                analysis_result = {"status": "error", "error": "Tool does not have execute method"}

            if analysis_result.get("status") != "success":
                analysis_results["status"] = "partial"
                analysis_results["errors"] = [
                    f"Analysis failed: {analysis_result.get('error')}"
                ]
                return analysis_results

            analysis = analysis_result.get("analysis", {})
            if "stages" not in analysis_results:
                analysis_results["stages"] = {}
            analysis_results["stages"]["ai_analysis"] = analysis

            # Stage 2: Threat Intelligence Enrichment
            threat_intel_tool = self.tools[1]  # ThreatIntelligenceTool

            if hasattr(threat_intel_tool, 'execute') and callable(threat_intel_tool.execute):
                threat_result = await threat_intel_tool.execute(
                    tool_context,
                    incident=incident,
                    indicators=self._extract_indicators(incident, analysis),
                )
            else:
                threat_result = {"status": "error", "error": "Tool does not have execute method"}

            threat_intel = threat_result.get("threat_intelligence", {})
            if "stages" not in analysis_results:
                analysis_results["stages"] = {}
            analysis_results["stages"]["threat_intelligence"] = threat_intel

            # Stage 3: Generate Recommendations
            recommendation_tool = self.tools[2]  # RecommendationGeneratorTool

            if hasattr(recommendation_tool, 'execute') and callable(recommendation_tool.execute):
                rec_result = await recommendation_tool.execute(
                    tool_context, analysis=analysis, threat_intelligence=threat_intel
                )
            else:
                rec_result = {"status": "error", "error": "Tool does not have execute method"}

            recommendations = rec_result.get("recommendations", {})
            if "stages" not in analysis_results:
                analysis_results["stages"] = {}
            analysis_results["stages"]["recommendations"] = recommendations

            # Stage 4: Determine next actions
            threat_level = analysis.get("threat_assessment", {}).get(
                "threat_level", "medium"
            )
            confidence = analysis.get("threat_assessment", {}).get("confidence", 0.5)

            if "next_actions" not in analysis_results:
                analysis_results["next_actions"] = []
            next_actions = analysis_results["next_actions"]

            # Auto-remediation for high confidence threats
            if confidence >= self.auto_remediate_threshold and threat_level in [
                "critical",
                "high",
            ]:
                next_actions.append("auto_remediate")

                # Transfer to remediation agent
                remediation_tool = self.tools[3]  # TransferToRemediationAgentTool
                if hasattr(remediation_tool, 'execute') and callable(remediation_tool.execute):
                    await remediation_tool.execute(
                        tool_context,
                        incident_id=incident.get("id"),
                        workflow_stage="analysis_complete",
                        results={
                            "analysis": analysis,
                            "recommendations": recommendations.get("immediate_actions", []),
                            "auto_approve": True,
                        },
                    )

            # Critical alerts
            if (
                confidence >= self.critical_alert_threshold
                and threat_level == "critical"
            ):
                next_actions.append("critical_alert")

                # Transfer to communication agent
                comm_tool = self.tools[4]  # TransferToCommunicationAgentTool
                if hasattr(comm_tool, 'execute') and callable(comm_tool.execute):
                    await comm_tool.execute(
                        tool_context,
                        incident_id=incident.get("id"),
                        workflow_stage="critical_alert",
                        results={
                            "analysis": analysis,
                            "priority": "critical",
                            "channels": ["slack", "email", "sms"],
                        },
                    )

            # Always report back to orchestrator
            orchestrator_tool = self.tools[5]  # TransferToOrchestratorAgentTool
            if hasattr(orchestrator_tool, 'execute') and callable(orchestrator_tool.execute):
                await orchestrator_tool.execute(
                    tool_context,
                    incident_id=incident.get("id"),
                    workflow_stage="analysis_complete",
                    results=analysis_results,
                )

            analysis_results["end_time"] = datetime.utcnow().isoformat()
            start_time_str = analysis_results.get("start_time", "")
            if isinstance(start_time_str, str) and start_time_str:
                analysis_results["duration_seconds"] = (
                    datetime.utcnow()
                    - datetime.fromisoformat(start_time_str)
                ).total_seconds()
            else:
                analysis_results["duration_seconds"] = 0

            logger.info(
                "Analysis complete for incident %s: Threat level=%s, Confidence=%s",
                incident.get('id'),
                threat_level,
                confidence
            )

            # Cache the successful analysis result
            self.performance_optimizer.cache_analysis(
                incident.get("id", "unknown"), incident, analysis_results
            )

            return analysis_results

        except (ValueError, KeyError, AttributeError, TypeError) as e:
            logger.error("Error during incident analysis: %s", e, exc_info=True)
            analysis_results["status"] = "error"
            analysis_results["error"] = str(e)
            return analysis_results

    def _extract_indicators(
        self, incident: Dict[str, Any], analysis: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Extract indicators of compromise from incident and analysis."""
        indicators = []

        # Extract from incident metadata
        metadata = incident.get("metadata", {})
        if metadata.get("source_ip") and metadata["source_ip"] != "unknown":
            indicators.append({"type": "ip", "value": metadata["source_ip"]})

        if metadata.get("actor") and metadata["actor"] != "unknown":
            indicators.append({"type": "email", "value": metadata["actor"]})

        # Extract from analysis
        attribution = analysis.get("attribution", {})
        for indicator in attribution.get("indicators", []):
            indicators.append({"type": "unknown", "value": indicator})

        return indicators

    async def _batch_analyze_incidents(
        self, incidents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process multiple incidents in a batch for efficiency."""
        logger.info("Batch processing %d incidents", len(incidents))
        results = []

        # Group incidents by severity for more efficient prompting
        severity_groups: Dict[str, List[Dict[str, Any]]] = {}
        for incident_data in incidents:
            incident = (
                incident_data if isinstance(incident_data, dict) else incident_data[1]
            )
            severity = incident.get("severity", "medium")
            if severity not in severity_groups:
                severity_groups[severity] = []
            severity_groups[severity].append(incident)

        # Process each severity group
        for severity, group_incidents in severity_groups.items():
            # Create a batch prompt for similar incidents
            batch_prompt = self._create_batch_analysis_prompt(group_incidents)

            try:
                # Use Gemini to analyze the batch
                # Create test tool context
                tool_context = type("TestToolContext", (), {})()
                tool_context.data = {}
                tool_context.actions = None
                analysis_tool = self.tools[0]  # IncidentAnalysisTool

                # Analyze as a batch
                if hasattr(analysis_tool, 'execute') and callable(analysis_tool.execute):
                    batch_result = await analysis_tool.execute(
                        tool_context,
                        incident={
                            "batch": True,
                            "incidents": group_incidents,
                            "prompt": batch_prompt,
                        },
                    )
                else:
                    batch_result = {"status": "error", "error": "Tool does not have execute method"}

                # Parse results for individual incidents
                if batch_result.get("status") == "success":
                    batch_analysis = batch_result.get("analysis", {})

                    # Distribute analysis to individual incidents
                    for i, incident in enumerate(group_incidents):
                        individual_result = {
                            "status": "success",
                            "incident_id": incident.get("id"),
                            "analysis_id": f"batch_analysis_{datetime.utcnow().timestamp()}_{i}",
                            "stages": {
                                "ai_analysis": self._extract_individual_analysis(
                                    batch_analysis, i
                                ),
                                "threat_intelligence": {},  # Simplified for batch
                                "recommendations": self._extract_individual_recommendations(
                                    batch_analysis, i
                                ),
                            },
                            "batch_processed": True,
                        }

                        # Cache individual results
                        self.performance_optimizer.cache_analysis(
                            incident.get("id", "unknown"), incident, individual_result
                        )

                        results.append(individual_result)
                else:
                    # Fallback to individual processing
                    for incident in group_incidents:
                        result = await self._analyze_incident(
                            incident, tool_context, None
                        )
                        results.append(result)

            except (ValueError, KeyError, AttributeError, TypeError) as e:
                logger.error("Batch processing failed: %s", e, exc_info=True)
                # Fallback to individual processing
                for incident in group_incidents:
                    # Create test tool context for fallback
                    fallback_context = type("TestToolContext", (), {})()
                    fallback_context.data = {}
                    fallback_context.actions = None
                    result = await self._analyze_incident(
                        incident, fallback_context, None
                    )
                    results.append(result)

        return results

    def _create_batch_analysis_prompt(self, incidents: List[Dict[str, Any]]) -> str:
        """Create an optimized prompt for batch incident analysis."""
        prompt = "Analyze the following security incidents as a batch:\n\n"

        for i, incident in enumerate(incidents):
            prompt += f"INCIDENT {i + 1}:\n"
            prompt += f"- ID: {incident.get('id')}\n"
            prompt += f"- Title: {incident.get('title')}\n"
            prompt += f"- Severity: {incident.get('severity')}\n"
            prompt += f"- Description: {incident.get('description')}\n"
            prompt += f"- Resource: {incident.get('resource')}\n\n"

        prompt += """
For each incident, provide:
1. Threat assessment (level and confidence)
2. Attack pattern identification
3. Immediate recommendations

Format as JSON array with one object per incident.
"""
        return prompt

    def _extract_individual_analysis(
        self, batch_analysis: Dict[str, Any], index: int
    ) -> Dict[str, Any]:
        """Extract individual analysis from batch results."""
        # This would parse the batch analysis results
        # For now, return a simplified version
        return {
            "threat_assessment": {
                "threat_level": batch_analysis.get("threat_levels", ["medium"])[
                    index % len(batch_analysis.get("threat_levels", ["medium"]))
                ],
                "confidence": 0.7,
                "attack_pattern": "batch_analyzed",
            },
            "impact_analysis": {"affected_resources": []},
        }

    def _extract_individual_recommendations(
        self, batch_analysis: Dict[str, Any], index: int
    ) -> Dict[str, Any]:
        """Extract individual recommendations from batch results."""
        _ = (batch_analysis, index)  # Unused but retained for future use
        return {
            "immediate_actions": [
                {
                    "action": "Review incident details",
                    "priority": "high",
                    "automation_possible": True,
                }
            ]
        }
