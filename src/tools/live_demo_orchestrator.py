"""
SentinelOps Live Demo Orchestrator
Manages rotating threat scenarios with real threat intel integration for live demonstrations
"""

import asyncio
import random
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from google.cloud import bigquery

from src.tools.threat_simulator import ThreatSimulator
# Removed deprecated import - using GeminiIntegration from app state instead
from src.detection_agent.threat_intel_queries import ThreatIntelQueries
from src.common.storage import get_firestore_client

logger = logging.getLogger(__name__)


@dataclass
class LiveDemoConfig:
    """Configuration for live demo orchestration"""

    project_id: str
    demo_duration_minutes: int = 30
    scenario_interval_seconds: int = 45
    threat_intel_enabled: bool = True
    real_time_analysis: bool = True
    auto_remediation: bool = False
    demo_intensity: str = "medium"  # low, medium, high, extreme


class LiveDemoOrchestrator:
    """
    Orchestrates a live, rotating threat simulation demonstration.

    Features:
    - Continuous threat scenario generation on rotation
    - Real-time threat intelligence enrichment
    - AI-powered analysis with Gemini
    - Live dashboard updates via Firestore
    - Simulated incident response workflows
    """

    def __init__(self, config: LiveDemoConfig, gemini_integration: Optional[Any] = None) -> None:
        self.config = config
        self.simulator = ThreatSimulator()
        self.gemini_integration = gemini_integration  # Passed from FastAPI app state
        self.threat_intel = ThreatIntelQueries(config.project_id)
        self.bigquery_client = bigquery.Client(project=config.project_id)
        self.firestore_client = get_firestore_client()

        # Demo state
        self.demo_active = False
        self.demo_start_time: Optional[datetime] = None
        self.generated_incidents: List[Dict[str, Any]] = []
        self.analysis_results: List[Dict[str, Any]] = []
        self.demo_stats = {
            "scenarios_generated": 0,
            "incidents_analyzed": 0,
            "threats_detected": 0,
            "false_positives": 0,
            "critical_incidents": 0,
        }

        # Intensity configurations
        self.intensity_configs: Dict[str, Dict[str, Any]] = {
            "low": {
                "scenarios_per_minute": 0.5,
                "critical_probability": 0.1,
                "analysis_delay_range": (30, 60),
                "noise_events": 2,
            },
            "medium": {
                "scenarios_per_minute": 1.5,
                "critical_probability": 0.25,
                "analysis_delay_range": (10, 30),
                "noise_events": 5,
            },
            "high": {
                "scenarios_per_minute": 3.0,
                "critical_probability": 0.4,
                "analysis_delay_range": (5, 15),
                "noise_events": 10,
            },
            "extreme": {
                "scenarios_per_minute": 5.0,
                "critical_probability": 0.6,
                "analysis_delay_range": (2, 8),
                "noise_events": 20,
            },
        }

    async def start_live_demo(self) -> Dict[str, Any]:
        """Start the live demonstration"""
        logger.info(
            "🚀 Starting SentinelOps live demo - Duration: %s minutes",
            self.config.demo_duration_minutes,
        )

        self.demo_active = True
        self.demo_start_time = datetime.now(timezone.utc)

        # Verify Gemini integration is available
        if self.config.real_time_analysis and not self.gemini_integration:
            logger.warning("Real-time analysis requested but Gemini integration not provided")
            self.config.real_time_analysis = False

        # Create demo session document
        assert self.demo_start_time is not None  # Set above
        demo_session: Dict[str, Any] = {
            "demo_id": f"DEMO-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "start_time": self.demo_start_time.isoformat() + "Z",
            "config": asdict(self.config),
            "status": "running",
            "stats": self.demo_stats.copy(),
        }

        # Store in Firestore for real-time dashboard updates
        session_ref = self.firestore_client.collection("live_demo_sessions").document(
            demo_session["demo_id"]
        )
        session_ref.set(demo_session)

        # Start concurrent tasks
        tasks = [
            self._scenario_generator_loop(),
            self._threat_intel_enrichment_loop(),
            self._analysis_loop(),
            self._dashboard_update_loop(),
            self._demo_timer(),
        ]

        try:
            await asyncio.gather(*tasks)
        except (asyncio.CancelledError, ValueError, RuntimeError) as e:
            logger.error("Demo error: %s", e)
        finally:
            await self._cleanup_demo(demo_session["demo_id"])

        return {
            "demo_id": demo_session["demo_id"],
            "status": "completed",
            "duration_minutes": self.config.demo_duration_minutes,
            "final_stats": self.demo_stats,
            "incidents_generated": len(self.generated_incidents),
            "analyses_completed": len(self.analysis_results),
        }

    async def _scenario_generator_loop(self) -> None:
        """Continuously generate threat scenarios"""
        intensity_config = self.intensity_configs[self.config.demo_intensity]
        interval = (
            60 / intensity_config["scenarios_per_minute"]
        )  # Convert to seconds between scenarios

        while self.demo_active:
            try:
                # Determine scenario severity based on demo progression
                assert self.demo_start_time is not None  # Checked in start_live_demo
                elapsed_minutes = (
                    datetime.now(timezone.utc) - self.demo_start_time
                ).total_seconds() / 60

                # Escalate severity as demo progresses
                if elapsed_minutes < 5:
                    severity_weights = {"LOW": 0.6, "MEDIUM": 0.3, "CRITICAL": 0.1}
                elif elapsed_minutes < 15:
                    severity_weights = {"LOW": 0.3, "MEDIUM": 0.5, "CRITICAL": 0.2}
                else:
                    severity_weights = {"LOW": 0.2, "MEDIUM": 0.3, "CRITICAL": 0.5}

                # Choose severity
                rand = random.random()
                cumulative = 0.0
                chosen_severity = "MEDIUM"
                for severity, weight in severity_weights.items():
                    cumulative += weight
                    if rand <= cumulative:
                        chosen_severity = severity
                        break

                # Generate scenario
                scenario = self.simulator.generate_scenario(severity=chosen_severity)

                # Enhance with demo metadata
                scenario.update(
                    {
                        "demo_context": True,
                        "demo_timestamp": datetime.utcnow().isoformat() + "Z",
                        "demo_sequence": len(self.generated_incidents) + 1,
                        "demo_phase": self._get_demo_phase(elapsed_minutes),
                    }
                )

                # Add realistic threat intel context
                if self.config.threat_intel_enabled:
                    scenario = await self._enrich_with_threat_intel(scenario)

                self.generated_incidents.append(scenario)
                self.demo_stats["scenarios_generated"] += 1

                if scenario["severity"] == "CRITICAL":
                    self.demo_stats["critical_incidents"] += 1

                # Store in Firestore for real-time updates
                incident_ref = self.firestore_client.collection(
                    "demo_incidents"
                ).document(
                    scenario.get(
                        "simulation_id", f"incident-{len(self.generated_incidents)}"
                    )
                )
                incident_ref.set(scenario)

                logger.info(
                    "📡 Generated %s scenario: %s",
                    chosen_severity,
                    scenario["event_type"],
                )

                # Add some noise events (benign activities)
                if random.random() < 0.3:  # 30% chance of noise
                    await self._generate_noise_events(int(intensity_config["noise_events"]))

            except (ValueError, KeyError, AttributeError, TypeError) as e:
                logger.error("Error generating scenario: %s", e)

            await asyncio.sleep(interval + random.uniform(-5, 5))  # Add jitter

    async def _threat_intel_enrichment_loop(self) -> None:
        """Continuously enrich incidents with threat intelligence"""
        if not self.config.threat_intel_enabled:
            return

        while self.demo_active:
            try:
                # Run threat intel queries
                queries = [
                    (
                        "malicious_ips",
                        self.threat_intel.get_malicious_ip_connections(1),
                    ),
                    (
                        "cve_exploitation",
                        self.threat_intel.get_vulnerable_asset_exploitation_attempts(1),
                    ),
                    (
                        "suspicious_dns",
                        self.threat_intel.get_suspicious_dns_activity(1),
                    ),
                    (
                        "mitre_correlation",
                        self.threat_intel.get_mitre_attack_correlation(1),
                    ),
                ]

                for query_name, query_sql in queries:
                    try:
                        query_job = self.bigquery_client.query(query_sql)
                        results = list(query_job.result())

                        if results:
                            logger.info(
                                "🔍 Threat intel: %s %s detections",
                                len(results),
                                query_name,
                            )
                            self.demo_stats["threats_detected"] += len(results)

                            # Store detections for analysis
                            for detection_result in results:
                                detection = dict(detection_result)
                                detection["detection_source"] = "threat_intel"
                                detection["query_type"] = query_name

                                # Store in Firestore
                                _ = self.firestore_client.collection(
                                    "demo_detections"
                                ).add(detection)

                    except (ValueError, AttributeError, TypeError) as e:
                        logger.warning(
                            "Threat intel query %s failed: %s", query_name, e
                        )

            except (ValueError, KeyError, AttributeError, TypeError) as e:
                logger.error("Threat intel enrichment error: %s", e)

            await asyncio.sleep(30)  # Run every 30 seconds

    async def _analysis_loop(self) -> None:
        """Continuously analyze incidents with Gemini"""
        if not self.config.real_time_analysis or not self.gemini_integration:
            return

        analyzed_incidents = set()

        while self.demo_active:
            try:
                # Find unanalyzed incidents
                unanalyzed = [
                    incident
                    for incident in self.generated_incidents
                    if incident.get("simulation_id") not in analyzed_incidents
                ]

                for incident in unanalyzed:
                    try:
                        # Add realistic delay for analysis
                        intensity_config = self.intensity_configs[self.config.demo_intensity]
                        delay_range = intensity_config["analysis_delay_range"]
                        assert isinstance(delay_range, tuple) and len(delay_range) == 2
                        analysis_delay = random.uniform(delay_range[0], delay_range[1])

                        await asyncio.sleep(analysis_delay)

                        # Analyze with Gemini
                        log_entries = json.dumps(incident, indent=2)
                        analysis_response = await self.gemini_integration.analyze_logs(
                            log_entries=log_entries,
                            context={
                                "demo_mode": True,
                                "threat_intel_available": self.config.threat_intel_enabled,
                                "incident_id": incident.get("simulation_id"),
                                "analysis_type": "live_demo",
                                "demo_phase": incident.get("demo_phase", "unknown"),
                            },
                        )

                        # Convert analysis response to dict format
                        analysis_dict = {
                            "incident_id": incident.get("simulation_id"),
                            "analysis": analysis_response.data,
                            "severity": analysis_response.get_severity(),
                            "recommendations": analysis_response.get_recommendations(),
                            "demo_context": True,
                            "analysis_delay_seconds": analysis_delay,
                            "original_incident": incident,
                        }

                        self.analysis_results.append(analysis_dict)
                        self.demo_stats["incidents_analyzed"] += 1

                        # Determine if this is a false positive (for demo realism)
                        if random.random() < 0.15:  # 15% false positive rate
                            analysis_dict["demo_classification"] = "false_positive"
                            self.demo_stats["false_positives"] += 1
                        else:
                            analysis_dict["demo_classification"] = "true_positive"

                        # Store analysis in Firestore
                        analysis_ref = self.firestore_client.collection(
                            "demo_analyses"
                        ).document(incident.get("simulation_id"))
                        analysis_ref.set(analysis_dict)

                        analyzed_incidents.add(incident.get("simulation_id"))

                        logger.info(
                            "🧠 Analyzed incident %s - Severity: %s",
                            incident.get("simulation_id"),
                            analysis_dict["severity"]
                        )

                    except (ValueError, AttributeError, TypeError) as e:
                        logger.error("Error analyzing incident: %s", e)
                        continue

            except (ValueError, KeyError, AttributeError, TypeError) as e:
                logger.error("Analysis loop error: %s", e)

            await asyncio.sleep(10)  # Check for new incidents every 10 seconds

    async def _dashboard_update_loop(self) -> None:
        """Update live dashboard metrics"""
        while self.demo_active:
            try:
                # Calculate real-time metrics
                current_time = datetime.now(timezone.utc)
                assert self.demo_start_time is not None  # Checked in start_live_demo
                elapsed_seconds = (current_time - self.demo_start_time).total_seconds()

                # Severity distribution
                severity_counts: Dict[str, int] = {}
                for incident in self.generated_incidents:
                    severity = incident.get("severity", "UNKNOWN")
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1

                # Analysis performance
                avg_confidence = 0
                if self.analysis_results:
                    avg_confidence = sum(
                        r.get("confidence", 0) for r in self.analysis_results
                    ) / len(self.analysis_results)

                # Live metrics
                metrics = {
                    "timestamp": current_time.isoformat() + "Z",
                    "demo_elapsed_seconds": elapsed_seconds,
                    "scenarios_per_minute": (
                        (len(self.generated_incidents) / elapsed_seconds) * 60
                        if elapsed_seconds > 0
                        else 0
                    ),
                    "severity_distribution": severity_counts,
                    "analysis_performance": {
                        "total_analyzed": len(self.analysis_results),
                        "average_confidence": avg_confidence,
                        "analysis_rate": (
                            (len(self.analysis_results) / elapsed_seconds) * 60
                            if elapsed_seconds > 0
                            else 0
                        ),
                    },
                    "threat_intel_stats": {
                        "threats_detected": self.demo_stats["threats_detected"],
                        "detection_rate": (
                            (self.demo_stats["threats_detected"] / elapsed_seconds) * 60
                            if elapsed_seconds > 0
                            else 0
                        ),
                    },
                    "demo_stats": self.demo_stats.copy(),
                }

                # Update Firestore
                metrics_ref = self.firestore_client.collection("demo_metrics").document(
                    "live_metrics"
                )
                metrics_ref.set(metrics)

            except (ValueError, AttributeError, TypeError) as e:
                logger.error("Dashboard update error: %s", e)

            await asyncio.sleep(5)  # Update every 5 seconds

    async def _demo_timer(self) -> None:
        """Demo duration timer"""
        await asyncio.sleep(self.config.demo_duration_minutes * 60)
        logger.info("⏰ Demo duration completed")
        self.demo_active = False

    async def _enrich_with_threat_intel(
        self, scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enrich scenario with realistic threat intelligence context"""
        try:
            # Add threat intel indicators based on scenario type
            threat_context: Dict[str, Any] = {
                "threat_intel_enrichment": True,
                "indicators_of_compromise": [],
                "threat_intel_sources": [],
                "risk_score": 0,
            }

            # Extract IPs for enrichment
            ips_to_check = []
            if "actor_ip" in scenario:
                ips_to_check.append(scenario["actor_ip"])
            if "src_ip" in scenario:
                ips_to_check.append(scenario["src_ip"])

            for ip in ips_to_check:
                # Simulate threat intel lookup
                if random.random() < 0.3:  # 30% chance IP is in threat intel
                    threat_context["indicators_of_compromise"].append(
                        {
                            "indicator": ip,
                            "type": "ip",
                            "source": random.choice(
                                ["abuseipdb", "firehol", "spamhaus"]
                            ),
                            "confidence": random.uniform(0.7, 0.95),
                            "last_seen": (
                                datetime.utcnow()
                                - timedelta(hours=random.randint(1, 48))
                            ).isoformat()
                            + "Z",
                        }
                    )
                    threat_context["threat_intel_sources"].append("ip_reputation")
                    threat_context["risk_score"] += 25

            # Add CVE context for exploitation scenarios
            if (
                "cve" in scenario.get("event_type", "").lower()
                or "exploit" in scenario.get("finding", "").lower()
            ):
                threat_context["indicators_of_compromise"].append(
                    {
                        "indicator": f"CVE-2024-{random.randint(1000, 9999)}",
                        "type": "cve",
                        "source": "cisa_kev",
                        "severity": scenario.get("severity", "MEDIUM"),
                        "exploitation_active": True,
                    }
                )
                threat_context["threat_intel_sources"].append(
                    "vulnerability_intelligence"
                )
                threat_context["risk_score"] += 35

            # Add MITRE ATT&CK context
            if scenario.get("mitre_tactic"):
                threat_context["mitre_context"] = {
                    "tactic": scenario["mitre_tactic"],
                    "technique": scenario.get("mitre_technique", "Unknown"),
                    "confidence": random.uniform(0.8, 0.95),
                }
                threat_context["threat_intel_sources"].append("mitre_attack")
                threat_context["risk_score"] += 20

            # Normalize risk score
            threat_context["risk_score"] = min(100, threat_context["risk_score"])

            scenario.update(threat_context)

        except (ValueError, KeyError, AttributeError, TypeError) as e:
            logger.warning("Failed to enrich scenario with threat intel: %s", e)

        return scenario

    async def _generate_noise_events(self, count: int) -> None:
        """Generate benign events to simulate normal activity"""
        noise_events = [
            {"event_type": "NORMAL_LOGIN", "severity": "INFO"},
            {"event_type": "SOFTWARE_UPDATE", "severity": "INFO"},
            {"event_type": "BACKUP_COMPLETED", "severity": "INFO"},
            {"event_type": "HEALTH_CHECK", "severity": "INFO"},
            {"event_type": "LOG_ROTATION", "severity": "INFO"},
        ]

        for _ in range(random.randint(1, count)):
            noise_event = random.choice(noise_events).copy()
            noise_event.update(
                {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "demo_context": "true",
                    "event_classification": "benign",
                }
            )

            # Store noise events separately
            _ = self.firestore_client.collection("demo_noise_events").add(
                noise_event
            )

    def _get_demo_phase(self, elapsed_minutes: float) -> str:
        """Determine current demo phase based on elapsed time"""
        if elapsed_minutes < 5:
            return "reconnaissance"
        elif elapsed_minutes < 15:
            return "initial_access"
        elif elapsed_minutes < 25:
            return "lateral_movement"
        else:
            return "data_exfiltration"

    async def _cleanup_demo(self, demo_id: str) -> None:
        """Clean up demo resources"""
        try:
            # Update demo session status
            session_ref = self.firestore_client.collection(
                "live_demo_sessions"
            ).document(demo_id)
            session_ref.update(
                {
                    "status": "completed",
                    "end_time": datetime.utcnow().isoformat() + "Z",
                    "final_stats": self.demo_stats,
                }
            )

            # Close Gemini analyst
            # Gemini integration cleanup handled by FastAPI

            logger.info("✅ Demo %s cleanup completed", demo_id)

        except (ValueError, AttributeError, TypeError) as e:
            logger.error("Error during demo cleanup: %s", e)

    def get_demo_summary(self) -> Dict[str, Any]:
        """Get comprehensive demo summary"""
        return {
            "demo_stats": self.demo_stats,
            "total_incidents": len(self.generated_incidents),
            "total_analyses": len(self.analysis_results),
            "demo_duration": self.config.demo_duration_minutes,
            "demo_intensity": self.config.demo_intensity,
            "features_demonstrated": {
                "threat_simulation": True,
                "threat_intelligence": self.config.threat_intel_enabled,
                "ai_analysis": self.config.real_time_analysis,
                "real_time_detection": True,
                "live_dashboard": True,
            },
        }


async def run_live_demo(
    gcp_project_id: str,
    duration_minutes: int = 20,
    demo_intensity: str = "medium",
    threat_intel_enabled: bool = True,
) -> Dict[str, Any]:
    """
    Run a complete live SentinelOps demonstration

    Args:
        gcp_project_id: GCP project ID
        duration_minutes: Demo duration
        demo_intensity: Demo intensity (low, medium, high, extreme)
        threat_intel_enabled: Enable threat intelligence integration

    Returns:
        Demo summary and results
    """
    config = LiveDemoConfig(
        project_id=gcp_project_id,
        demo_duration_minutes=duration_minutes,
        demo_intensity=demo_intensity,
        threat_intel_enabled=threat_intel_enabled,
        real_time_analysis=True,
    )

    orchestrator = LiveDemoOrchestrator(config)

    try:
        demo_result = await orchestrator.start_live_demo()
        summary = orchestrator.get_demo_summary()

        return {"demo_result": demo_result, "demo_summary": summary, "status": "success"}

    except (ValueError, RuntimeError, AttributeError, TypeError) as e:
        logger.error("Live demo failed: %s", e)
        return {
            "status": "error",
            "error": str(e),
            "partial_summary": orchestrator.get_demo_summary(),
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python live_demo_orchestrator.py <project_id> [duration_minutes] [intensity]"
        )
        sys.exit(1)

    project_id = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    intensity = sys.argv[3] if len(sys.argv) > 3 else "medium"

    print("🚀 Starting SentinelOps Live Demo")
    print(f"Project: {project_id}")
    print(f"Duration: {duration} minutes")
    print(f"Intensity: {intensity}")

    result = asyncio.run(run_live_demo(project_id, duration, intensity))

    print("\n📊 Demo Results:")
    print(json.dumps(result, indent=2, default=str))
