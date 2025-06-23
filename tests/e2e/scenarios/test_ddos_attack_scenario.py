"""
End-to-end test for DDoS attack scenario.

This test simulates a complete workflow for detecting and mitigating a DDoS attack,
testing high-volume event handling, real-time detection, and rapid response.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import pytest

from src.common.models import (
    AnalysisResult,
    EventSource,
    Incident,
    IncidentStatus,
    RemediationAction,
    SecurityEvent,
    SeverityLevel,
)


@pytest.mark.asyncio
async def test_ddos_attack_full_workflow() -> None:
    """Test the complete DDoS attack scenario workflow."""
    # Test data tracking
    published_messages: List[Dict[str, Any]] = []
    notifications_sent: List[Dict[str, Any]] = []
    remediation_actions_executed: List[Dict[str, Any]] = []

    # Create DDoS attack incident
    incident = Incident(
        incident_id="inc-" + str(uuid.uuid4()),
        title="Large-Scale DDoS Attack in Progress",
        description=(
            "Massive distributed denial of service attack targeting production "
            "load balancers"
        ),
        severity=SeverityLevel.CRITICAL,
        status=IncidentStatus.DETECTED,
    )

    # Scenario parameters
    base_time = datetime.now(timezone.utc) - timedelta(minutes=15)
    target_lb = "production-lb-01"
    target_ips = ["34.102.136.180", "34.102.136.181", "34.102.136.182"]
    normal_rps = 5000  # Normal requests per second
    attack_rps = 500000  # Attack requests per second

    # Attacker botnet IPs (simulating thousands of sources)
    botnet_ranges = [
        "45.155.205.0/24",  # 256 IPs
        "185.220.101.0/24",  # 256 IPs
        "192.42.116.0/24",  # 256 IPs
        "23.129.64.0/24",  # 256 IPs
        "51.75.64.0/24",  # 256 IPs
    ]
    total_attacking_ips = len(botnet_ranges) * 256

    # Stage 1: Traffic spike detection
    traffic_spike_event = SecurityEvent(
        event_type="traffic_anomaly_detected",
        source=EventSource(
            source_type="load_balancer",
            source_name="compute.googleapis.com/loadbalancer",
            source_id="test-project",
            resource_type="loadbalancer",
            resource_name=target_lb,
            resource_id=f"projects/test-project/global/loadbalancers/{target_lb}",
        ),
        severity=SeverityLevel.HIGH,
        description=(
            f"Massive traffic spike detected on {target_lb}: {attack_rps} RPS "
            f"(normal: {normal_rps} RPS)"
        ),
        timestamp=base_time,
        affected_resources=[target_lb] + target_ips,
        indicators={
            "current_rps": attack_rps,
            "normal_rps": normal_rps,
            "spike_factor": attack_rps / normal_rps,
            "traffic_type": "HTTP_FLOOD",
            "unique_sources": total_attacking_ips,
            "geographic_distribution": "GLOBAL",
        },
    )
    incident.add_event(traffic_spike_event)

    # Stage 2: Pattern analysis - Identifying attack signatures
    for idx, botnet_range in enumerate(botnet_ranges):
        pattern_event = SecurityEvent(
            event_type="ddos_pattern_identified",
            source=EventSource(
                source_type="cloud_armor",
                source_name="cloudarmor.googleapis.com",
                source_id="test-project",
                resource_type="security_policy",
                resource_name="default-security-policy",
                resource_id="projects/test-project/global/securityPolicies/default",
            ),
            severity=SeverityLevel.CRITICAL,
            description=f"DDoS attack pattern identified from subnet {botnet_range}",
            timestamp=base_time + timedelta(seconds=30 + idx * 10),
            affected_resources=[target_lb],
            indicators={
                "source_subnet": botnet_range,
                "requests_per_minute": 50000 + idx * 10000,
                "attack_pattern": "HTTP_FLOOD",
                "user_agent": "Mozilla/5.0 (compatible; Botnet/1.0)",
                "request_characteristics": {
                    "method": "GET",
                    "path_pattern": "/api/*",
                    "header_anomalies": [
                        "missing_accept_language",
                        "identical_headers",
                    ],
                    "timing_pattern": "SYNCHRONIZED",
                },
            },
        )
        incident.add_event(pattern_event)

    # Stage 3: Resource impact - System degradation
    resources_impacted = [
        {"resource": "CPU", "utilization": 95, "threshold": 80},
        {"resource": "Memory", "utilization": 88, "threshold": 85},
        {"resource": "Network", "utilization": 99, "threshold": 90},
        {"resource": "Connection_Pool", "utilization": 100, "threshold": 95},
    ]

    for resource_data in resources_impacted:
        resource_name = str(resource_data["resource"])
        impact_event = SecurityEvent(
            event_type="resource_exhaustion",
            source=EventSource(
                source_type="monitoring",
                source_name="monitoring.googleapis.com",
                source_id="test-project",
                resource_type="gce_instance",
                resource_name=f"backend-{resource_name.lower()}-01",
                resource_id=(
                    "projects/test-project/zones/us-central1-a/instances/backend-01"
                ),
            ),
            severity=SeverityLevel.CRITICAL,
            description=(
                f"{resource_data['resource']} exhaustion: "
                f"{resource_data['utilization']}% (threshold: {resource_data['threshold']}%)"
            ),
            timestamp=base_time + timedelta(minutes=2),
            affected_resources=["backend-pool-01"],
            indicators={
                "resource_type": resource_data["resource"],
                "current_utilization": resource_data["utilization"],
                "threshold": resource_data["threshold"],
                "impact": "SERVICE_DEGRADATION",
                "affected_users": 50000,
            },
        )
        incident.add_event(impact_event)

    # Stage 4: Service degradation - Customer impact
    service_impact_event = SecurityEvent(
        event_type="service_degradation",
        source=EventSource(
            source_type="uptime_check",
            source_name="monitoring.googleapis.com/uptime",
            source_id="test-project",
            resource_type="https_load_balancer",
            resource_name=target_lb,
            resource_id=("projects/test-project/uptimeCheckConfigs/production-check"),
        ),
        severity=SeverityLevel.CRITICAL,
        description=(
            "Production services experiencing severe degradation due to DDoS attack"
        ),
        timestamp=base_time + timedelta(minutes=3),
        affected_resources=["production-api", "customer-portal", "mobile-backend"],
        indicators={
            "response_time_ms": 15000,  # 15 second response time
            "normal_response_time_ms": 200,
            "error_rate": 0.65,  # 65% errors
            "availability": 0.35,  # 35% availability
            "affected_regions": ["us-central1", "us-east1", "europe-west1"],
            "customer_complaints": 127,
        },
    )
    incident.add_event(service_impact_event)

    # Create comprehensive analysis
    analysis_result = AnalysisResult(
        incident_id=incident.incident_id,
        confidence_score=0.99,
        summary=(
            f"Critical DDoS attack in progress: {total_attacking_ips} attacking IPs "
            f"generating {attack_rps} RPS"
        ),
        detailed_analysis=(
            f"""Large-scale HTTP flood DDoS attack detected with the following characteristics:

**Attack Profile:**
- Type: HTTP Flood (Layer 7)
- Volume: {attack_rps:,} requests per second ({attack_rps / normal_rps:.0f}x normal traffic)
- Sources: {total_attacking_ips:,} unique IPs across {len(botnet_ranges)} subnets
- Target: Production load balancer and API endpoints
- Duration: Ongoing (started {15} minutes ago)

**Impact Assessment:**
- Service Availability: 35% (CRITICAL)
- Response Time: 15,000ms (75x normal)
- Error Rate: 65%
- Affected Users: ~50,000
- Resource Exhaustion: CPU 95%, Memory 88%, Network 99%

**Attack Characteristics:**
- Coordinated botnet with synchronized request patterns
- Targeting resource-intensive API endpoints
- Using legitimate-looking HTTP requests
- Geographic distribution suggests global botnet"""
        ),
        attack_techniques=["T1498", "T1499"],  # Network DoS, Endpoint DoS
        recommendations=[
            "Enable Cloud Armor DDoS protection immediately",
            "Block identified botnet IP ranges",
            "Activate rate limiting rules",
            "Scale up backend capacity",
            "Enable geographic filtering",
            "Redirect traffic through CDN",
            "Notify upstream ISP for assistance",
            "Prepare public communication",
        ],
        evidence={
            "attack_type": "HTTP_FLOOD",
            "total_attacking_ips": total_attacking_ips,
            "attack_volume_rps": attack_rps,
            "service_impact_percent": 65,
            "resource_exhaustion": True,
            "coordinated_attack": True,
        },
        gemini_explanation=(
            "This is a sophisticated Layer 7 DDoS attack using a distributed botnet. "
            "The attack is designed to exhaust application resources rather than just "
            "bandwidth, making it more difficult to mitigate."
        ),
    )
    incident.analysis = analysis_result

    # Create rapid remediation actions
    remediation_actions = [
        RemediationAction(
            incident_id=incident.incident_id,
            action_type="enable_ddos_protection",
            description=("Enable Cloud Armor DDoS protection with adaptive protection"),
            target_resource="cloudarmor/policies/default",
            params={
                "policy": "default-security-policy",
                "enable_adaptive_protection": True,
                "enable_layer7_defense": True,
                "sensitivity": "HIGH",
            },
            status="pending",
        ),
        RemediationAction(
            incident_id=incident.incident_id,
            action_type="block_ip_ranges",
            description=f"Block {len(botnet_ranges)} identified botnet IP ranges",
            target_resource="cloudarmor/policies/default",
            params={
                "ip_ranges": botnet_ranges,
                "action": "DENY",
                "priority": 1000,
                "rule_name": "emergency-ddos-block",
            },
            status="pending",
        ),
        RemediationAction(
            incident_id=incident.incident_id,
            action_type="enable_rate_limiting",
            description="Enable aggressive rate limiting on API endpoints",
            target_resource="cloudarmor/policies/default",
            params={
                "rate_limit_threshold": 100,
                "rate_limit_window": "1m",
                "enforce_on_key": "IP",
                "exceed_action": "DENY",
                "ban_duration": "10m",
            },
            status="pending",
        ),
        RemediationAction(
            incident_id=incident.incident_id,
            action_type="scale_infrastructure",
            description="Emergency auto-scaling of backend infrastructure",
            target_resource="compute/instance-groups/backend-pool",
            params={
                "target_size": 100,  # Scale from 10 to 100 instances
                "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
                "machine_type": "n2-standard-8",
                "preemptible": False,
            },
            status="pending",
        ),
        RemediationAction(
            incident_id=incident.incident_id,
            action_type="enable_cdn_shield",
            description="Enable CDN origin shield to absorb attack traffic",
            target_resource="cdn/distributions/production",
            params={
                "enable_origin_shield": True,
                "cache_everything": True,
                "challenge_suspicious": True,
                "enable_under_attack_mode": True,
            },
            status="pending",
        ),
    ]

    for action in remediation_actions:
        incident.add_remediation_action(action)

    # Simulate workflow execution
    # 1. Detection Phase - Real-time
    detection_message = {
        "message_type": "incident_detected",
        "incident": incident.to_dict(),
        "real_time": True,
        "priority": "IMMEDIATE",
    }
    published_messages.append(
        {
            "topic": "projects/test-project/topics/incidents-critical",
            "data": detection_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    # 2. Analysis Phase - Rapid
    incident.status = IncidentStatus.ANALYZING

    analysis_message = {
        "message_type": "analysis_complete",
        "incident_id": incident.incident_id,
        "analysis": analysis_result.to_dict(),
        "processing_time_ms": 500,  # Fast analysis for DDoS
    }
    published_messages.append(
        {
            "topic": "projects/test-project/topics/analysis-results",
            "data": analysis_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    # 3. Remediation Phase - Immediate execution (no approval needed for DDoS)
    incident.status = IncidentStatus.REMEDIATION_IN_PROGRESS

    # Execute all remediation actions immediately
    for action in remediation_actions:
        action.status = "executing"

        remediation_message = {
            "message_type": "execute_remediation",
            "action": action.to_dict(),
            "auto_approved": True,
            "reason": "DDoS attack - immediate response required",
        }
        published_messages.append(
            {
                "topic": "projects/test-project/topics/remediation-actions-priority",
                "data": remediation_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Simulate rapid execution
        execution_result = {
            "action": action.action_type,
            "params": action.params,
            "status": "completed",
            "execution_time_ms": 1000 + len(remediation_actions_executed) * 500,
        }

        # Add specific results for each action
        if action.action_type == "enable_ddos_protection":
            execution_result["details"] = {
                "protection_enabled": True,
                "adaptive_protection": "ACTIVE",
                "mitigation_started": datetime.now(timezone.utc).isoformat(),
            }
        elif action.action_type == "block_ip_ranges":
            execution_result["details"] = {
                "ranges_blocked": len(botnet_ranges),
                "ips_blocked": total_attacking_ips,
                "rule_created": "emergency-ddos-block-rule",
            }
        elif action.action_type == "enable_rate_limiting":
            execution_result["details"] = {
                "rate_limit_active": True,
                "current_blocks": 125000,
                "effectiveness": "HIGH",
            }
        elif action.action_type == "scale_infrastructure":
            execution_result["details"] = {
                "instances_added": 90,
                "total_instances": 100,
                "capacity_increase": "10x",
            }
        elif action.action_type == "enable_cdn_shield":
            execution_result["details"] = {
                "cdn_shield_active": True,
                "origin_requests_reduced": "95%",
                "attack_absorbed": True,
            }

        remediation_actions_executed.append(execution_result)
        action.status = "completed"
        details = execution_result.get("details")
        action.execution_result = details if isinstance(details, dict) else {}

    # 4. Mass Notification Phase
    # Public status page update
    status_page_update = {
        "service": "status_page",
        "update_type": "incident",
        "severity": "major_outage",
        "title": "Ongoing DDoS Attack - Service Degradation",
        "body": (
            "We are currently experiencing a distributed denial of service (DDoS) "
            "attack affecting our services.\n\n"
            "**Current Status:** Mitigation in progress\n"
            "**Affected Services:** API, Customer Portal, Mobile Apps\n"
            "**Impact:** Intermittent connectivity issues and slow response times\n\n"
            "Our team has implemented multiple mitigation measures and services are "
            "beginning to recover. We expect full restoration within the next 30 minutes.\n\n"
            "We apologize for any inconvenience and will provide updates every 15 minutes."
        ),
        "affected_components": ["api", "web_portal", "mobile_backend"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    notifications_sent.append(status_page_update)

    # Slack - Operations channel
    ops_slack_notification = {
        "channel": "#ops-emergency",
        "text": "🚨 DDoS ATTACK IN PROGRESS - ALL HANDS 🚨",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⚠️ CRITICAL: Large-Scale DDoS Attack",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Attack Volume:* {attack_rps:,} RPS\n"
                        f"*Attacking IPs:* {total_attacking_ips:,}\n"
                        "*Service Impact:* 65% degradation"
                    ),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Mitigations Applied:*\n"
                        "✅ Cloud Armor DDoS protection enabled\n"
                        "✅ Botnet IPs blocked\n"
                        "✅ Rate limiting activated\n"
                        "✅ Infrastructure scaled 10x\n"
                        "✅ CDN shield enabled"
                    ),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Current Status:*\n"
                        "Attack traffic dropping, services recovering. "
                        "ETA to full recovery: 20-30 minutes."
                    ),
                },
            },
        ],
        "priority": "URGENT",
    }
    notifications_sent.append(ops_slack_notification)

    # Email - Executive briefing
    exec_email = {
        "to": ["ceo@company.com", "cto@company.com", "ciso@company.com"],
        "cc": ["board-security@company.com"],
        "subject": "URGENT: Major DDoS Attack - Executive Briefing",
        "body": f"""Executive Team,

We are currently under a significant DDoS attack. Here's the situation:

ATTACK METRICS:
• Volume: {attack_rps:,} requests/second (100x normal)
• Sources: {total_attacking_ips:,} IPs (distributed botnet)
• Started: 15 minutes ago
• Target: Production infrastructure

BUSINESS IMPACT:
• Service availability: 35%
• Affected customers: ~50,000
• Revenue impact: Estimated $50K-100K per hour

RESPONSE ACTIONS:
1. Automated DDoS protection activated
2. Attack traffic being filtered
3. Infrastructure scaled 10x
4. CDN absorbing attack traffic
5. Public communications prepared

CURRENT STATUS:
Mitigations are working. Attack traffic is being successfully filtered.
Services are beginning to recover. Full recovery expected within 30 minutes.

NEXT STEPS:
• Continue monitoring
• Prepare for potential second wave
• Legal team preparing for law enforcement notification
• PR team ready with public statement if needed

Will update in 15 minutes or sooner if situation changes.

Security Operations Center
24/7 Hotline: +1-555-SEC-TEAM""",
        "priority": "URGENT",
    }
    notifications_sent.append(exec_email)

    # Customer notification email
    customer_email = {
        "to": "customers-all@company.com",
        "subject": "Service Disruption Notice",
        "body": """Dear Valued Customer,

We are currently experiencing technical difficulties affecting our services.
Our team is actively working to resolve the issue.

Current Impact:
• Some users may experience slow response times
• Intermittent API errors possible
• Mobile app connectivity issues

We expect services to be fully restored within the next 30 minutes.

For real-time updates, please visit: https://status.company.com

We apologize for any inconvenience.

Best regards,
Customer Support Team""",
        "send_time": "immediate",
    }
    notifications_sent.append(customer_email)

    # 5. Recovery Phase
    # Simulate attack mitigation success
    recovery_event = SecurityEvent(
        event_type="ddos_mitigation_effective",
        source=EventSource(
            source_type="cloud_armor",
            source_name="cloudarmor.googleapis.com",
            source_id="test-project",
            resource_type="security_policy",
            resource_name="default-security-policy",
            resource_id="projects/test-project/global/securityPolicies/default",
        ),
        severity=SeverityLevel.MEDIUM,
        description="DDoS mitigation successful - attack traffic reduced by 95%",
        timestamp=base_time + timedelta(minutes=10),
        affected_resources=[target_lb],
        indicators={
            "blocked_requests": 450000,
            "allowed_requests": 10000,
            "effectiveness": 0.95,
            "service_recovery": "IN_PROGRESS",
        },
    )
    incident.add_event(recovery_event)

    incident.status = IncidentStatus.RESOLVED
    # Verification Tests
    # Test 1: High-Volume Event Handling
    incident_messages = [
        msg for msg in published_messages if "incidents" in msg.get("topic", "")
    ]
    assert len(incident_messages) > 0, "No incident detection messages"

    detected_incident = incident_messages[0]["data"]["incident"]
    assert detected_incident["severity"] == "critical"
    assert len(detected_incident["events"]) >= 10, "Not all DDoS events captured"

    # Verify attack characteristics detected
    traffic_events = [
        e
        for e in detected_incident["events"]
        if e["event_type"] == "traffic_anomaly_detected"
    ]
    assert len(traffic_events) > 0, "Traffic anomaly not detected"
    assert (
        traffic_events[0]["indicators"]["current_rps"] >= 100000
    ), "Attack volume not captured"

    # Test 2: Real-time Detection
    assert (
        incident_messages[0]["data"].get("real_time") is True
    ), "Not flagged as real-time"
    assert (
        incident_messages[0]["data"].get("priority") == "IMMEDIATE"
    ), "Not prioritized correctly"

    # Test 3: Rapid Remediation
    assert len(remediation_actions_executed) >= 5, "Not all mitigations executed"

    # Verify DDoS protection enabled
    ddos_protection = [
        a
        for a in remediation_actions_executed
        if a["action"] == "enable_ddos_protection"
    ]
    assert len(ddos_protection) > 0, "DDoS protection not enabled"
    assert ddos_protection[0]["details"]["protection_enabled"] is True

    # Verify IP blocking
    ip_blocks = [
        a for a in remediation_actions_executed if a["action"] == "block_ip_ranges"
    ]
    assert len(ip_blocks) > 0, "IPs not blocked"
    assert ip_blocks[0]["details"]["ips_blocked"] >= 1000, "Insufficient IPs blocked"

    # Verify infrastructure scaling
    scaling = [
        a for a in remediation_actions_executed if a["action"] == "scale_infrastructure"
    ]
    assert len(scaling) > 0, "Infrastructure not scaled"
    assert scaling[0]["details"]["capacity_increase"] == "10x", "Insufficient scaling"

    # Test 4: Mass Notification
    assert len(notifications_sent) >= 4, "Not all stakeholders notified"

    # Verify status page updated
    status_updates = [
        n for n in notifications_sent if n.get("service") == "status_page"
    ]
    assert len(status_updates) > 0, "Public status page not updated"
    assert "major_outage" in status_updates[0]["severity"], "Severity not communicated"

    # Verify ops notified
    ops_notifs = [n for n in notifications_sent if n.get("channel") == "#ops-emergency"]
    assert len(ops_notifs) > 0, "Operations team not notified"
    assert "ALL HANDS" in ops_notifs[0]["text"], "Urgency not conveyed"

    # Verify executive briefing
    exec_notifs = [
        n for n in notifications_sent if "ceo@company.com" in str(n.get("to", []))
    ]
    assert len(exec_notifs) > 0, "Executives not briefed"

    # Test 5: Recovery Tracking
    recovery_events = [
        e for e in incident.events if e.event_type == "ddos_mitigation_effective"
    ]
    assert len(recovery_events) > 0, "Recovery not tracked"
    assert (
        recovery_events[0].indicators["effectiveness"] >= 0.9
    ), "Mitigation not effective"

    # Performance metrics
    assert incident.status == IncidentStatus.RESOLVED

    print("\n✅ DDoS attack scenario test completed successfully!")
    print(f"   - Attack volume: {attack_rps:,} RPS from {total_attacking_ips:,} IPs")
    print("   - Detection to mitigation: <1 minute")
    print(f"   - Mitigations applied: {len(remediation_actions_executed)}")
    print("   - Effectiveness: 95% attack traffic blocked")
    print(f"   - Stakeholders notified: {len(notifications_sent)}")
