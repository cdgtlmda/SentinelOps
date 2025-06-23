"""Test Data Fixtures - Reusable test data for all test scenarios."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.common.models import (
    AnalysisResult,
    EventSource,
    Incident,
    IncidentStatus,
    Notification,
    RemediationAction,
    SecurityEvent,
    SeverityLevel,
)


class TestDataFixtures:
    """Central repository for all test data fixtures."""

    @staticmethod
    def get_sample_security_event() -> SecurityEvent:
        """Get a sample security event."""
        return SecurityEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            severity=SeverityLevel.MEDIUM,
            event_type="suspicious_login",
            source=EventSource(
                source_type="cloud_logging",
                source_name="gcp-logs",
                source_id="projects/test-project/logs",
                resource_type="gce_instance",
                resource_name="web-server-1",
                resource_id="projects/test-project/instances/web-server-1",
            ),
            description="Multiple failed login attempts followed by successful login",
            raw_data={
                "timestamp": datetime.utcnow().isoformat(),
                "event": "login",
                "status": "success",
                "previous_failures": 5,
                "source_ip": "192.168.1.100",
                "destination_ip": "10.0.0.50",
                "user": "test.user@example.com",
                "location": "US",
                "device_type": "unknown",
                "user_agent": "Mozilla/5.0",
            },
            actor="test.user@example.com",
            affected_resources=["projects/test-project/instances/web-server-1"],
        )

    @staticmethod
    def get_sample_incident() -> Incident:
        """Get a sample incident."""
        event = TestDataFixtures.get_sample_security_event()
        return Incident(
            incident_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            status=IncidentStatus.DETECTED,
            severity=SeverityLevel.HIGH,
            title="Suspicious Login Activity Detected",
            description=(
                "Multiple failed login attempts followed by successful login from unknown location"
            ),
            events=[event],
            tags=["authentication", "suspicious_activity"],
            metadata={
                "detection_rule": "AUTH-001",
                "confidence_score": 0.85,
                "affected_resources": ["projects/test-project/instances/web-server-1"],
            },
        )

    @staticmethod
    def get_sample_analysis_result() -> AnalysisResult:
        """Get a sample analysis result."""
        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            incident_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            summary="High severity authentication attack detected with account compromise",
            detailed_analysis=(
                "The pattern of multiple failed login attempts followed by a successful "
                "login from an unusual location strongly suggests a brute force attack "
                "that succeeded. The lack of previous login history from this IP address "
                "increases the likelihood of account compromise."
            ),
            attack_techniques=["T1110.001", "T1078"],
            recommendations=[
                "Force password reset for affected user",
                "Enable MFA if not already enabled",
                "Review recent account activity",
            ],
            confidence_score=0.85,
            gemini_explanation=(
                "The pattern of multiple failed login attempts followed by a successful "
                "login from an unusual location strongly suggests a brute force attack "
                "that succeeded. The lack of previous login history from this IP address "
                "increases the likelihood of account compromise."
            ),
            evidence={
                "threat_indicators": [
                    "Multiple failed authentication attempts",
                    "Login from unusual location",
                    "No previous login history from this IP",
                ],
                "severity_assessment": "HIGH",
                "false_positive_probability": 0.15,
                "analysis_duration": 2.5,
                "model_version": "gemini-1.5-pro",
            },
        )

    @staticmethod
    def get_sample_remediation_action() -> RemediationAction:
        """Get a sample remediation action."""
        return RemediationAction(
            action_id=str(uuid.uuid4()),
            incident_id=str(uuid.uuid4()),
            action_type="ISOLATE_INSTANCE",
            target_resource="projects/test-project/instances/web-server-1",
            params={
                "firewall_rule_name": "isolate-web-server-1",
                "allow_ssh_from": ["35.235.240.0/20"],  # Google Cloud Shell
                "block_all_other": True,
            },
            status="pending",
            description="Isolate compromised instance by applying restrictive firewall rules",
        )

    @staticmethod
    def get_sample_notification_message() -> Notification:
        """Get a sample notification message."""
        return Notification(
            notification_id=str(uuid.uuid4()),
            incident_id=str(uuid.uuid4()),
            notification_type="slack",
            recipients=["#security-alerts", "security-team@example.com"],
            subject="[HIGH] Suspicious Login Activity Detected",
            content=(
                "Multiple failed login attempts followed by successful login for user "
                "test.user@example.com from IP 192.168.1.100"
            ),
            status="pending",
            timestamp=datetime.utcnow(),
            error_message=None,
        )

    @staticmethod
    def get_test_log_entries(count: int = 10) -> List[Dict[str, Any]]:
        """Get sample log entries for testing."""
        log_types: List[Dict[str, Any]] = [
            {
                "type": "login_attempt",
                "severity": "INFO",
                "template": {
                    "event": "login",
                    "status": "success",
                    "user": "user{}_@example.com",
                    "ip": "192.168.1.{}",
                },
            },
            {
                "type": "failed_login",
                "severity": "WARNING",
                "template": {
                    "event": "login",
                    "status": "failed",
                    "user": "user{}_@example.com",
                    "ip": "192.168.1.{}",
                    "reason": "invalid_password",
                },
            },
            {
                "type": "api_call",
                "severity": "INFO",
                "template": {
                    "event": "api_call",
                    "method": "GET",
                    "path": "/api/v1/resource/{}",
                    "status_code": 200,
                    "duration_ms": 150,
                },
            },
            {
                "type": "permission_denied",
                "severity": "ERROR",
                "template": {
                    "event": "permission_denied",
                    "user": "user{}_@example.com",
                    "resource": "projects/test-project/resources/resource-{}",
                    "action": "compute.instances.delete",
                },
            },
        ]

        logs = []
        base_time = datetime.utcnow() - timedelta(hours=1)

        for i in range(count):
            log_type = log_types[i % len(log_types)]
            log_entry = {
                "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
                "severity": log_type["severity"],
                "resource": {
                    "type": "gce_instance",
                    "labels": {
                        "instance_id": f"instance-{i % 3}",
                        "project_id": "test-project",
                        "zone": "us-central1-a",
                    },
                },
                "jsonPayload": log_type["template"].copy(),
            }

            # Format template values
            if "{}" in str(log_entry["jsonPayload"]):
                for key, value in log_entry["jsonPayload"].items():
                    if isinstance(value, str) and "{}" in value:
                        log_entry["jsonPayload"][key] = value.format(i)

            logs.append(log_entry)

        return logs

    @staticmethod
    def get_performance_test_data() -> Dict[str, Any]:
        """Get data for performance testing."""
        return {
            "large_incident": Incident(
                incident_id=str(uuid.uuid4()),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                status=IncidentStatus.DETECTED,
                severity=SeverityLevel.CRITICAL,
                title="Large Scale Security Incident",
                description="Multiple security events detected across many resources",
                events=[
                    TestDataFixtures.get_sample_security_event() for _ in range(100)
                ],
                tags=["large_scale", "critical", "immediate_action"],
                metadata={
                    "event_count": 100,
                    "resource_count": 50,
                    "affected_resources": [
                        f"projects/test-project/instances/server-{i}" for i in range(50)
                    ],
                },
            ),
            "bulk_logs": TestDataFixtures.get_test_log_entries(1000),
            "concurrent_incidents": [
                TestDataFixtures.get_sample_incident() for _ in range(20)
            ],
        }

    @staticmethod
    def get_edge_case_data() -> Dict[str, Any]:
        """Get edge case test data."""
        return {
            "empty_incident": Incident(
                incident_id=str(uuid.uuid4()),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                status=IncidentStatus.DETECTED,
                severity=SeverityLevel.LOW,
                title="",
                description="",
                events=[],
                tags=[],
                metadata={},
            ),
            "unicode_event": SecurityEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                severity=SeverityLevel.MEDIUM,
                event_type="suspicious_activity",
                source=EventSource(
                    source_type="cloud_logging",
                    source_name="unicode-test",
                    source_id="projects/test-project/logs",
                    resource_type="gce_instance",
                    resource_name="서버-1",
                ),
                description="Suspicious activity with unicode characters: 🚨⚠️",
                actor="测试用户@example.com",
                affected_resources=["projects/test-project/instances/서버-1"],
                raw_data={
                    "message": "Unicode test: émojis 😀 and special chars ñ",
                    "source_ip": "192.168.1.100",
                    "destination_ip": "10.0.0.50",
                },
                indicators={"location": "東京", "message": "Тестовое сообщение"},
            ),
            "large_metadata": {
                "huge_string": "x" * 10000,
                "deeply_nested": {
                    "level1": {
                        "level2": {"level3": {"level4": {"level5": "deep value"}}}
                    }
                },
                "large_array": list(range(1000)),
            },
            "malformed_json": '{"invalid": "json", "missing": closing bracket',
            "null_values": {
                "event_id": None,
                "timestamp": None,
                "user": None,
                "description": None,
            },
        }

    @staticmethod
    def get_scenario_data(scenario: str) -> Dict[str, Any]:
        """Get data for specific test scenarios."""
        scenarios = {
            "brute_force_attack": {
                "events": [
                    SecurityEvent(
                        event_id=str(uuid.uuid4()),
                        timestamp=datetime.utcnow() - timedelta(minutes=30 - i),
                        severity=SeverityLevel.MEDIUM,
                        event_type="failed_login",
                        source=EventSource(
                            source_type="api_gateway",
                            source_name="api-gateway",
                            source_id="projects/test-project/services/api-gateway",
                        ),
                        description=f"Failed login attempt {i + 1} of 30",
                        actor="admin@example.com",
                        affected_resources=[
                            "projects/test-project/services/api-gateway"
                        ],
                        raw_data={
                            "event": "login",
                            "status": "failed",
                            "attempt": i + 1,
                            "reason": "invalid_password",
                            "source_ip": f"192.168.1.{100 + i % 10}",
                            "destination_ip": "10.0.0.50",
                        },
                        indicators={"attempt_number": i + 1},
                    )
                    for i in range(30)
                ]
            },
            "data_exfiltration": {
                "events": [
                    SecurityEvent(
                        event_id=str(uuid.uuid4()),
                        timestamp=datetime.utcnow() - timedelta(hours=2),
                        severity=SeverityLevel.HIGH,
                        event_type="unusual_data_transfer",
                        source=EventSource(
                            source_type="cloud_storage",
                            source_name="sensitive-data-bucket",
                            source_id="projects/test-project/buckets/sensitive-data",
                        ),
                        description="Large data transfer to suspicious IP",
                        actor="compromised.user@example.com",
                        affected_resources=[
                            "projects/test-project/buckets/sensitive-data"
                        ],
                        raw_data={
                            "event": "data_transfer",
                            "bytes_transferred": 5 * 1024 * 1024 * 1024,  # 5GB
                            "destination": "TOR_network",
                            "duration_seconds": 3600,
                            "source_ip": "10.0.0.50",
                            "destination_ip": "185.220.101.50",  # Known TOR exit node
                        },
                        indicators={
                            "data_classification": "confidential",
                            "destination_reputation": "malicious",
                        },
                    )
                ]
            },
            "privilege_escalation": {
                "events": [
                    SecurityEvent(
                        event_id=str(uuid.uuid4()),
                        timestamp=datetime.utcnow() - timedelta(minutes=15),
                        severity=SeverityLevel.CRITICAL,
                        event_type="privilege_change",
                        source=EventSource(
                            source_type="iam",
                            source_name="project-iam",
                            source_id="projects/test-project/iam",
                        ),
                        description="User granted owner role unexpectedly",
                        actor="regular.user@example.com",
                        affected_resources=["projects/test-project/iam"],
                        raw_data={
                            "event": "iam.roles.update",
                            "before": ["roles/viewer"],
                            "after": ["roles/viewer", "roles/owner"],
                            "modified_by": "regular.user@example.com",
                            "source_ip": "10.0.0.100",
                            "destination_ip": "10.0.0.1",
                        },
                        indicators={
                            "suspicious_indicators": [
                                "self_privilege_grant",
                                "outside_business_hours",
                                "no_approval_workflow",
                            ]
                        },
                    )
                ]
            },
            "ddos_attack": {
                "events": [
                    SecurityEvent(
                        event_id=str(uuid.uuid4()),
                        timestamp=datetime.utcnow() - timedelta(seconds=i),
                        severity=SeverityLevel.HIGH,
                        event_type="traffic_spike",
                        source=EventSource(
                            source_type="web_app",
                            source_name="web-app",
                            source_id="projects/test-project/services/web-app",
                        ),
                        description=f"Abnormal traffic spike - request {i + 1} of 10000",
                        actor="anonymous",
                        affected_resources=["projects/test-project/services/web-app"],
                        raw_data={
                            "event": "http_request",
                            "method": "GET",
                            "path": "/api/expensive-operation",
                            "status_code": 503,
                            "response_time_ms": 5000,
                            "source_ip": f"192.168.{i % 255}.{i % 255}",
                            "destination_ip": "10.0.0.80",
                        },
                        indicators={
                            "request_rate": "10000/second",
                            "pattern": "distributed_attack",
                        },
                    )
                    for i in range(100)  # Sample of 100 from 10000
                ]
            },
        }

        return scenarios.get(scenario, {"events": []})

    @staticmethod
    def reset_test_data() -> None:
        """Reset any stateful test data."""
        # In a real implementation, this might clear test databases,
        # reset counters, clean up temporary files, etc.


# Convenience functions for quick access
def get_test_incident() -> Incident:
    """Quick access to a test incident."""
    return TestDataFixtures.get_sample_incident()


def get_test_event() -> SecurityEvent:
    """Quick access to a test security event."""
    return TestDataFixtures.get_sample_security_event()


def get_test_analysis() -> AnalysisResult:
    """Quick access to a test analysis result."""
    return TestDataFixtures.get_sample_analysis_result()


def get_test_remediation() -> RemediationAction:
    """Quick access to a test remediation action."""
    return TestDataFixtures.get_sample_remediation_action()


def get_test_notification() -> Notification:
    """Quick access to a test notification message."""
    return TestDataFixtures.get_sample_notification_message()
