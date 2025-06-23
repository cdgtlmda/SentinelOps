"""
End-to-end test for privilege escalation scenario.

This test simulates a complete workflow for detecting and responding to
a subtle privilege escalation attack that requires deep analysis and careful remediation.
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
async def test_privilege_escalation_full_workflow() -> None:
    """Test the complete privilege escalation scenario workflow."""
    # Test data tracking
    published_messages: List[Dict[str, Any]] = []
    notifications_sent: List[Dict[str, Any]] = []
    remediation_actions_executed: List[Dict[str, Any]] = []

    # Create privilege escalation incident
    incident = Incident(
        incident_id="inc-" + str(uuid.uuid4()),
        title="Suspicious Privilege Escalation Activity Detected",
        description=(
            "Unusual IAM permission changes detected indicating "
            "potential insider threat or compromised account"
        ),
        severity=SeverityLevel.HIGH,
        status=IncidentStatus.DETECTED,
    )

    # Scenario parameters
    # Started 2 days ago
    base_time = datetime.now(timezone.utc) - timedelta(hours=48)
    compromised_user = "developer@company.com"
    initial_role = "roles/viewer"
    # escalated_roles = [
    #     "roles/editor",
    #     "roles/iam.serviceAccountUser",
    #     "roles/iam.serviceAccountKeyAdmin",
    #     "roles/compute.admin",
    #     "roles/storage.admin"
    # ]
    target_service_account = "production-app@test-project.iam.gserviceaccount.com"
    # Internal IP (potential insider)
    suspicious_ip = "192.168.1.105"

    # Stage 1: Initial reconnaissance - Unusual permission checks
    permissions = [
        "compute.instances.list",
        "storage.buckets.list",
        "iam.serviceAccounts.list",
    ]
    for idx, permission in enumerate(permissions):
        recon_event = SecurityEvent(
            event_type="permission_check_anomaly",
            source=EventSource(
                source_type="iam",
                source_name="iam.googleapis.com",
                source_id="test-project",
                resource_type="project",
                resource_name="test-project",
                resource_id="projects/test-project",
            ),
            severity=SeverityLevel.LOW,
            description=(
                f"Unusual permission check by {compromised_user}: " f"{permission}"
            ),
            timestamp=base_time + timedelta(hours=idx),
            actor=compromised_user,
            affected_resources=["projects/test-project"],
            indicators={
                "source_ip": suspicious_ip,
                "permission_checked": permission,
                "check_result": "DENIED",
                "user_role": initial_role,
                "anomaly_score": 0.6 + idx * 0.1,
                "baseline_deviation": True,
            },
        )
        incident.add_event(recon_event)

    # Stage 2: Self-permission grant attempts (failed)
    failed_grant_event = SecurityEvent(
        event_type="unauthorized_permission_grant_attempt",
        source=EventSource(
            source_type="iam",
            source_name="iam.googleapis.com",
            source_id="test-project",
            resource_type="project",
            resource_name="test-project",
            resource_id="projects/test-project",
        ),
        severity=SeverityLevel.MEDIUM,
        description=(
            f"Failed attempt to self-grant admin permissions by " f"{compromised_user}"
        ),
        timestamp=base_time + timedelta(hours=6),
        actor=compromised_user,
        affected_resources=["projects/test-project", compromised_user],
        indicators={
            "source_ip": suspicious_ip,
            "attempted_role": "roles/owner",
            "current_role": initial_role,
            "operation": "setIamPolicy",
            "result": "PERMISSION_DENIED",
            "suspicious_pattern": "SELF_PRIVILEGE_ESCALATION",
        },
    )
    incident.add_event(failed_grant_event)

    # Stage 3: Lateral movement - Finding misconfigured service account
    sa_discovery_event = SecurityEvent(
        event_type="service_account_enumeration",
        source=EventSource(
            source_type="iam",
            source_name="iam.googleapis.com",
            source_id="test-project",
            resource_type="serviceAccount",
            resource_name=target_service_account,
            resource_id=(
                f"projects/test-project/serviceAccounts/" f"{target_service_account}"
            ),
        ),
        severity=SeverityLevel.MEDIUM,
        description=(
            f"Service account with excessive permissions discovered "
            f"by {compromised_user}"
        ),
        timestamp=base_time + timedelta(hours=12),
        actor=compromised_user,
        affected_resources=[target_service_account],
        indicators={
            "source_ip": suspicious_ip,
            "operation": "iam.serviceAccounts.get",
            "service_account_roles": [
                "roles/editor",
                "roles/iam.serviceAccountTokenCreator",
            ],
            "discovery_method": "ENUMERATION",
            "time_spent_seconds": 1800,  # 30 minutes of enumeration
        },
    )
    incident.add_event(sa_discovery_event)

    # Stage 4: Privilege escalation via service account impersonation
    impersonation_event = SecurityEvent(
        event_type="service_account_impersonation",
        source=EventSource(
            source_type="iam",
            source_name="iamcredentials.googleapis.com",
            source_id="test-project",
            resource_type="serviceAccount",
            resource_name=target_service_account,
            resource_id=(
                f"projects/test-project/serviceAccounts/" f"{target_service_account}"
            ),
        ),
        severity=SeverityLevel.HIGH,
        description=(
            f"Service account impersonation detected: "
            f"{compromised_user} -> {target_service_account}"
        ),
        timestamp=base_time + timedelta(hours=13),
        actor=compromised_user,
        affected_resources=[target_service_account, compromised_user],
        indicators={
            "source_ip": suspicious_ip,
            "operation": "generateAccessToken",
            "token_lifetime_seconds": 3600,
            "impersonation_chain": [compromised_user, target_service_account],
            "risk_score": 0.85,
        },
    )
    incident.add_event(impersonation_event)

    # Stage 5: Exploiting elevated privileges
    for idx, (_, resource) in enumerate(
        [
            ("roles/compute.admin", "compute.instances.create"),
            ("roles/storage.admin", "storage.buckets.setIamPolicy"),
            ("roles/iam.serviceAccountKeyAdmin", "iam.serviceAccountKeys.create"),
        ]
    ):
        exploit_event = SecurityEvent(
            event_type="privilege_abuse",
            source=EventSource(
                source_type="admin",
                source_name="admin.googleapis.com",
                source_id="test-project",
                resource_type="project",
                resource_name="test-project",
                resource_id="projects/test-project",
            ),
            severity=SeverityLevel.HIGH,
            description=(
                f"Abusing elevated privileges: {resource} via " "impersonated account"
            ),
            timestamp=base_time + timedelta(hours=14 + idx),
            actor=target_service_account,  # Now acting as service account
            affected_resources=["projects/test-project"],
            indicators={
                "source_ip": suspicious_ip,
                "original_actor": compromised_user,
                "operation": resource,
                "impersonated_account": target_service_account,
                "privilege_level": "HIGH",
                "creates_persistence": resource == "iam.serviceAccountKeys.create",
            },
        )
        incident.add_event(exploit_event)

    # Stage 6: Persistence creation - New service account key
    persistence_event = SecurityEvent(
        event_type="persistence_mechanism_created",
        source=EventSource(
            source_type="iam",
            source_name="iam.googleapis.com",
            source_id="test-project",
            resource_type="serviceAccountKey",
            resource_name=f"key-{uuid.uuid4()}",
            resource_id=(
                f"projects/test-project/serviceAccounts/"
                f"{target_service_account}/keys/new-key"
            ),
        ),
        severity=SeverityLevel.CRITICAL,
        description="New service account key created for persistence",
        timestamp=base_time + timedelta(hours=18),
        actor=target_service_account,
        affected_resources=[target_service_account],
        indicators={
            "source_ip": suspicious_ip,
            "original_actor": compromised_user,
            "key_type": "USER_MANAGED",
            "key_algorithm": "KEY_ALG_RSA_2048",
            "persistence_type": "SERVICE_ACCOUNT_KEY",
            "exfiltration_risk": "HIGH",
        },
    )
    incident.add_event(persistence_event)

    # Create sophisticated analysis
    analysis_result = AnalysisResult(
        incident_id=incident.incident_id,
        confidence_score=0.88,
        summary=(
            "Sophisticated privilege escalation attack detected "
            "involving service account impersonation and persistence "
            "creation"
        ),
        detailed_analysis="""Complex privilege escalation attack chain identified:

**Attack Timeline & Progression:**
1. **Initial Reconnaissance** (T-48h): Systematic permission enumeration by \
developer@company.com
2. **Failed Direct Escalation** (T-42h): Attempted self-grant of owner role \
(blocked)
3. **Lateral Discovery** (T-36h): Located misconfigured service account with \
elevated privileges
4. **Privilege Escalation** (T-35h): Successfully impersonated service account
5. **Privilege Exploitation** (T-34h to T-30h): Created resources and \
modified permissions
6. **Persistence Established** (T-30h): Created new service account key for \
future access

**Threat Assessment:**
- Actor shows advanced knowledge of GCP IAM mechanics
- Deliberate, patient approach suggests insider knowledge
- Successfully bypassed direct permission controls via impersonation
- Created multiple persistence mechanisms

**Indicators of Compromise:**
- Unusual permission checking patterns
- Service account enumeration activity
- Impersonation token generation
- New service account key creation
- All activity from internal IP (possible insider threat)""",
        # Valid Accounts, Exploitation, Account Manipulation,
        # Token Impersonation, Create Account
        attack_techniques=["T1078", "T1068", "T1098", "T1134", "T1136"],
        recommendations=[
            "Immediately revoke impersonation token and new service account key",
            "Disable compromised user account pending investigation",
            "Review all actions taken by impersonated service account",
            "Audit service account permissions across project",
            "Enable service account impersonation alerts",
            "Implement least-privilege for all service accounts",
            "Review insider threat detection capabilities",
            "Check for additional compromised accounts",
        ],
        evidence={
            "privilege_escalation_confirmed": True,
            "impersonation_used": True,
            "persistence_created": True,
            "insider_threat_probability": 0.75,
            "affected_accounts": [compromised_user, target_service_account],
            "attack_sophistication": "HIGH",
        },
        gemini_explanation=(
            "This attack demonstrates advanced understanding "
            "of cloud IAM systems. The attacker patiently "
            "enumerated permissions, found a misconfigured "
            "service account, and used impersonation to bypass "
            "security controls. The creation of persistence "
            "mechanisms suggests long-term access goals."
        ),
    )
    incident.analysis = analysis_result

    # Create targeted remediation actions
    remediation_actions = [
        RemediationAction(
            incident_id=incident.incident_id,
            action_type="disable_user_account",
            description=(
                f"Disable potentially compromised user account " f"{compromised_user}"
            ),
            target_resource=compromised_user,
            params={
                "user_email": compromised_user,
                "disable_immediately": True,
                "preserve_logs": True,
                "notify_hr": True,
            },
            status="pending",
        ),
        RemediationAction(
            incident_id=incident.incident_id,
            action_type="revoke_service_account_keys",
            description=(
                f"Revoke all keys for impersonated service account "
                f"{target_service_account}"
            ),
            target_resource=target_service_account,
            params={
                "service_account": target_service_account,
                "revoke_all_keys": True,
                # Don't regenerate until investigation complete
                "regenerate_keys": False,
            },
            status="pending",
        ),
        RemediationAction(
            incident_id=incident.incident_id,
            action_type="revoke_impersonation_tokens",
            description="Revoke all active impersonation tokens",
            target_resource="iam/tokens",
            params={
                "service_account": target_service_account,
                "revoke_all_tokens": True,
                "block_future_impersonation": True,
            },
            status="pending",
        ),
        RemediationAction(
            incident_id=incident.incident_id,
            action_type="audit_permission_changes",
            description="Audit and revert unauthorized permission changes",
            target_resource="projects/test-project",
            params={
                "time_range_hours": 72,
                "actors": [compromised_user, target_service_account],
                # Manual review required
                "auto_revert": False,
                "generate_report": True,
            },
            status="pending",
        ),
        RemediationAction(
            incident_id=incident.incident_id,
            action_type="enable_enhanced_monitoring",
            description="Enable enhanced IAM monitoring and alerting",
            target_resource="monitoring/iam",
            params={
                "monitor_impersonation": True,
                "monitor_key_creation": True,
                "monitor_permission_changes": True,
                "alert_threshold": "SENSITIVE",
            },
            status="pending",
        ),
        RemediationAction(
            incident_id=incident.incident_id,
            action_type="forensic_analysis",
            description="Initiate forensic analysis of user activity",
            target_resource=compromised_user,
            params={
                "analyze_login_patterns": True,
                "check_data_access": True,
                "review_code_commits": True,
                "time_window_days": 90,
            },
            status="pending",
        ),
    ]

    for action in remediation_actions:
        incident.add_remediation_action(action)

    # Simulate workflow execution
    # 1. Detection Phase
    detection_message = {
        "message_type": "incident_detected",
        "incident": incident.to_dict(),
    }
    published_messages.append(
        {
            "topic": "projects/test-project/topics/incidents",
            "data": detection_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    # 2. Deep Analysis Phase
    incident.status = IncidentStatus.ANALYZING

    analysis_message = {
        "message_type": "analysis_complete",
        "incident_id": incident.incident_id,
        "analysis": analysis_result.to_dict(),
        "analysis_depth": "DEEP",
        # Multiple events correlated
        "correlation_count": 15,
    }
    published_messages.append(
        {
            "topic": "projects/test-project/topics/analysis-results",
            "data": analysis_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    # 3. Careful Remediation Phase - Some actions need approval
    incident.status = IncidentStatus.REMEDIATION_PENDING
    for action in remediation_actions:
        # Critical security actions execute immediately
        critical_actions = [
            "disable_user_account",
            "revoke_service_account_keys",
            "revoke_impersonation_tokens",
        ]
        if action.action_type in critical_actions:
            action.status = "executing"
            remediation_message = {
                "message_type": "execute_remediation",
                "action": action.to_dict(),
                "auto_approved": True,
                "reason": "Critical security action - prevent further damage",
            }
            published_messages.append(
                {
                    "topic": "projects/test-project/topics/remediation-actions",
                    "data": remediation_message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            # Simulate execution
            execution_result = {
                "action": action.action_type,
                "params": action.params,
                "status": "completed",
                "execution_time": datetime.now(timezone.utc).isoformat(),
            }

            if action.action_type == "disable_user_account":
                execution_result["details"] = {
                    "account_disabled": True,
                    "sessions_terminated": 3,
                    "api_keys_revoked": 2,
                    "hr_notified": True,
                }
            elif action.action_type == "revoke_service_account_keys":
                execution_result["details"] = {
                    "keys_revoked": 4,
                    "keys_identified": ["key-1", "key-2", "key-3", "key-suspicious"],
                    "service_account_status": "KEYS_REVOKED",
                }
            elif action.action_type == "revoke_impersonation_tokens":
                execution_result["details"] = {
                    "tokens_revoked": 1,
                    "future_impersonation_blocked": True,
                    "delegation_chain_broken": True,
                }

            remediation_actions_executed.append(execution_result)
            action.status = "completed"
            action.execution_result = execution_result
        else:
            # Non-critical actions need review
            action.status = "pending_approval"
            approval_request = {
                "message_type": "approval_required",
                "action": action.to_dict(),
                "reason": (
                    "Manual review required for forensic and " "monitoring actions"
                ),
            }
            published_messages.append(
                {
                    "topic": "projects/test-project/topics/approval-requests",
                    "data": approval_request,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

    # 4. Targeted Notification Phase
    # Security team notification
    security_notification = {
        "channel": "#security-investigations",
        "text": (
            "🔍 HIGH PRIORITY: Privilege Escalation Detected - "
            "Possible Insider Threat"
        ),
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": (
                        "⚠️ Privilege Escalation via Service Account " "Impersonation"
                    ),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Compromised User:* `{compromised_user}`\n"
                        "*Method:* Service Account Impersonation\n"
                        "*Risk Level:* HIGH\n"
                        "*Insider Threat Probability:* 75%"
                    ),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Attack Chain:*\n"
                        "1. Permission enumeration (48h ago)\n"
                        "2. Failed self-escalation attempt\n"
                        "3. Discovered misconfigured SA\n"
                        f"4. Impersonated `{target_service_account}`\n"
                        "5. Created persistence mechanisms"
                    ),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Immediate Actions Taken:*\n"
                        "✅ User account disabled\n"
                        "✅ Service account keys revoked\n"
                        "✅ Impersonation tokens revoked\n"
                        "⏳ Forensic analysis pending approval"
                    ),
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Full Timeline"},
                        "url": (
                            f"https://sentinelops.example.com/incidents/"
                            f"{incident.incident_id}/timeline"
                        ),
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Start Investigation"},
                        "style": "primary",
                        "url": (
                            f"https://sentinelops.example.com/incidents/"
                            f"{incident.incident_id}/investigate"
                        ),
                    },
                ],
            },
        ],
    }
    notifications_sent.append(security_notification)

    # HR notification (sensitive insider threat)
    hr_notification = {
        "to": ["hr-security@company.com", "legal@company.com"],
        "subject": (
            "CONFIDENTIAL: Potential Insider Threat - Immediate " "Action Required"
        ),
        "body": f"""
CONFIDENTIAL - INSIDER THREAT INVESTIGATION

Employee: {compromised_user}
Incident Type: Privilege Escalation / Unauthorized Access
Detection Time: {datetime.now(timezone.utc).isoformat()}
Risk Assessment: HIGH

SUMMARY:
Security systems have detected sophisticated unauthorized activity by the above \
employee.
The activity indicates deliberate attempts to gain elevated system access beyond \
assigned permissions.

ACTIONS TAKEN:
• Employee's system access has been disabled
• All active sessions terminated
• Security investigation initiated

REQUIRED HR ACTIONS:
1. Do not alert the employee yet
2. Preserve all employee records
3. Review recent behavior/performance issues
4. Prepare for potential termination procedures
5. Coordinate with Legal on next steps

EVIDENCE SUMMARY:
• 48-hour pattern of suspicious activity
• Multiple attempts to elevate privileges
• Successfully accessed sensitive service accounts
• Created backdoor access mechanisms

Please treat this matter with utmost confidentiality.
Security team contact: security-investigations@company.com

Legal hold is now in effect for all communications and records related to \
this employee.
""",
        "confidential": True,
        "encrypt": True,
    }
    notifications_sent.append(hr_notification)

    # Manager notification (limited details)
    manager_notification = {
        "to": (f"manager-of-{compromised_user.split('@', maxsplit=1)[0]}" "@company.com"),
        "subject": "Urgent: Temporary Access Suspension Required",
        "body": f"""
Hello,

We need to temporarily suspend system access for {compromised_user} due to a \
security investigation.

Please:
1. Do not discuss this with the employee
2. Redirect any urgent work items
3. Contact security-investigations@company.com for questions

HR will reach out shortly with more information.

Thank you for your cooperation.
Security Team
""",
        "priority": "HIGH",
    }
    notifications_sent.append(manager_notification)

    # 5. Investigation Phase
    # Immediate threat contained, investigation ongoing
    incident.status = IncidentStatus.RESOLVED

    # Verification Tests
    # Test 1: Subtle Attack Detection
    incident_messages = [
        msg for msg in published_messages if "incidents" in msg.get("topic", "")
    ]
    assert len(incident_messages) > 0, "No incident detection"

    detected_incident = incident_messages[0]["data"]["incident"]
    # Escalated to critical due to persistence creation
    assert detected_incident["severity"] == "critical"
    assert len(detected_incident["events"]) >= 8, "Not all attack stages detected"

    # Verify attack chain detected
    event_types = [e["event_type"] for e in detected_incident["events"]]
    assert "permission_check_anomaly" in event_types, "Initial recon not detected"
    assert "service_account_impersonation" in event_types, "Impersonation not detected"
    assert "persistence_mechanism_created" in event_types, "Persistence not detected"

    # Test 2: Deep Analysis Requirements
    analysis_messages = [
        msg for msg in published_messages if "analysis-results" in msg.get("topic", "")
    ]
    assert len(analysis_messages) > 0, "No analysis performed"

    analysis_data = analysis_messages[0]["data"]["analysis"]
    assert analysis_data["confidence_score"] >= 0.85, "Confidence too low"
    assert (
        analysis_messages[0]["data"]["analysis_depth"] == "DEEP"
    ), "Deep analysis not performed"

    # Verify attack techniques identified
    # Valid Accounts, Token Impersonation, Account Manipulation
    expected_techniques = ["T1078", "T1134", "T1098"]
    for technique in expected_techniques:
        assert (
            technique in analysis_data["attack_techniques"]
        ), f"Missing technique {technique}"

    # Verify insider threat identified
    assert (
        analysis_data["evidence"]["insider_threat_probability"] >= 0.7
    ), "Insider threat not identified"

    # Test 3: Careful Remediation
    assert len(remediation_actions_executed) >= 3, "Critical actions not executed"

    # Verify account disabled
    account_actions = [
        a for a in remediation_actions_executed if a["action"] == "disable_user_account"
    ]
    assert len(account_actions) > 0, "User account not disabled"
    assert account_actions[0]["details"]["account_disabled"] is True
    assert account_actions[0]["details"]["hr_notified"] is True, "HR not notified"

    # Verify tokens revoked
    token_actions = [
        a
        for a in remediation_actions_executed
        if a["action"] == "revoke_impersonation_tokens"
    ]
    assert len(token_actions) > 0, "Tokens not revoked"
    assert token_actions[0]["details"]["future_impersonation_blocked"] is True

    # Verify some actions pending approval
    approval_messages = [
        msg for msg in published_messages if "approval-requests" in msg.get("topic", "")
    ]
    assert (
        len(approval_messages) >= 2
    ), "Not all actions requiring approval were flagged"

    # Test 4: Targeted Notifications
    assert len(notifications_sent) >= 3, "Not all stakeholders notified"

    # Verify security team notified with details
    security_notifs = [
        n for n in notifications_sent if n.get("channel") == "#security-investigations"
    ]
    assert len(security_notifs) > 0, "Security team not notified"
    assert (
        "Insider Threat" in security_notifs[0]["text"]
    ), "Insider threat not highlighted"
    assert compromised_user in str(security_notifs[0]["blocks"]), "User not identified"

    # Verify HR notified confidentially
    hr_notifs = [
        n
        for n in notifications_sent
        if "hr-security@company.com" in str(n.get("to", []))
    ]
    assert len(hr_notifs) > 0, "HR not notified"
    assert (
        hr_notifs[0].get("confidential") is True
    ), "HR notification not marked confidential"
    assert hr_notifs[0].get("encrypt") is True, "HR notification not encrypted"

    # Verify manager notified with limited info
    manager_notifs = [
        n for n in notifications_sent if "manager-of-" in str(n.get("to", ""))
    ]
    assert len(manager_notifs) > 0, "Manager not notified"
    assert (
        "Do not discuss" in manager_notifs[0]["body"]
    ), "Manager not instructed on confidentiality"

    # Test 5: Incident Handling
    assert incident.status == IncidentStatus.RESOLVED, "Incident not marked resolved"

    # Verify forensic actions created but pending
    forensic_actions = [
        a for a in incident.remediation_actions if a.action_type == "forensic_analysis"
    ]
    assert len(forensic_actions) > 0, "Forensic analysis not initiated"
    assert (
        forensic_actions[0].status == "pending_approval"
    ), "Forensic analysis should require approval"

    print("\n✅ Privilege escalation scenario test completed successfully!")
    print("   - Attack duration: 48 hours (patient attacker)")
    print(f"   - Detection confidence: {incident.analysis.confidence_score:.2%}")
    print("   - Insider threat probability: 75%")
    print(
        f"   - Critical remediations: {len(remediation_actions_executed)} "
        "executed immediately"
    )
    print(
        f"   - Stakeholders notified: {len(notifications_sent)} "
        "(including HR and Legal)"
    )
