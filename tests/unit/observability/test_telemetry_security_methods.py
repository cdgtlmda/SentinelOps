"""Specific tests to reach 90%+ coverage by targeting SecurityTelemetry methods with REAL GCP services."""

import asyncio
import os
from datetime import datetime, timezone
import pytest

from src.observability.telemetry import (
    TelemetryCollector,
    SecurityTelemetry,
)

# Use real project ID from credentials
PROJECT_ID = "your-gcp-project-id"
CREDENTIALS_PATH = "/path/to/sentinelops/credentials/service-account-key.json"

# Set environment for real GCP services
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_PATH
os.environ['GOOGLE_CLOUD_PROJECT'] = PROJECT_ID


class TestSecurityTelemetrySpecificMethods:
    """Test specific SecurityTelemetry methods to reach 90%+ coverage."""

    @pytest.mark.asyncio
    async def test_record_authentication_attempt_comprehensive(self) -> None:
        """Test record_authentication_attempt method for both success and failure paths."""
        collector = TelemetryCollector(PROJECT_ID, "test-auth-specific")
        await asyncio.sleep(0.1)

        security_telemetry = SecurityTelemetry(collector)

        # Test successful authentication
        await security_telemetry.record_authentication_attempt(
            user_id="success_user@example.com",
            success=True,
            method="mfa",
            source_ip="192.168.1.100"
        )

        # Test failed authentication (should record failure metrics and events)
        await security_telemetry.record_authentication_attempt(
            user_id="failed_user@example.com",
            success=False,
            method="password",
            source_ip="10.0.0.1"
        )

        # Verify metrics and events were recorded
        summary = collector.get_telemetry_summary()
        assert summary["metrics_buffered"] > 0
        assert summary["events_buffered"] > 0

    @pytest.mark.asyncio
    async def test_record_threat_detection_comprehensive(self) -> None:
        """Test record_threat_detection method comprehensively."""
        collector = TelemetryCollector(PROJECT_ID, "test-threat-specific")
        await asyncio.sleep(0.1)

        security_telemetry = SecurityTelemetry(collector)

        # Test threat detection with various parameters
        await security_telemetry.record_threat_detection(
            threat_type="malware",
            severity="critical",
            confidence=0.95,
            source="endpoint_agent",
            details={
                "file_hash": "sha256:abc123...",
                "process_name": "malicious.exe",
                "pid": 1234,
                "ip_address": "192.168.1.50"
            }
        )

        # Test different threat type
        await security_telemetry.record_threat_detection(
            threat_type="phishing",
            severity="high",
            confidence=0.85,
            source="email_scanner",
            details={
                "sender": "attacker@evil.com",
                "subject": "Urgent: Update your password",
                "url": "https://fake-bank.com/login"
            }
        )

        # Test low confidence threat
        await security_telemetry.record_threat_detection(
            threat_type="suspicious_behavior",
            severity="medium",
            confidence=0.60,
            source="behavior_analytics",
            details={
                "user": "user@company.com",
                "anomaly_score": 0.7,
                "action": "unusual_file_access"
            }
        )

        # Verify threat metrics were recorded
        summary = collector.get_telemetry_summary()
        assert summary["metrics_buffered"] > 0
        assert summary["events_buffered"] > 0

    @pytest.mark.asyncio
    async def test_record_incident_lifecycle_comprehensive(self) -> None:
        """Test record_incident_lifecycle method comprehensively."""
        collector = TelemetryCollector(PROJECT_ID, "test-incident-specific")
        await asyncio.sleep(0.1)

        security_telemetry = SecurityTelemetry(collector)

        # Test incident creation phase
        await security_telemetry.record_incident_lifecycle(
            incident_id="INC-2025-001",
            phase="created",
            metadata={
                "incident_type": "data_breach",
                "severity": "critical",
                "affected_systems": ["database-server", "web-application"],
                "estimated_impact": "high"
            }
        )

        # Test investigation phase
        await security_telemetry.record_incident_lifecycle(
            incident_id="INC-2025-001",
            phase="investigating",
            duration_seconds=1800.0,  # 30 minutes
            metadata={
                "assignee": "security_team",
                "priority": "high"
            }
        )

        # Test resolution phase
        await security_telemetry.record_incident_lifecycle(
            incident_id="INC-2025-001",
            phase="resolved",
            duration_seconds=7200.0,  # 2 hours total
            metadata={
                "resolution": "patched_vulnerability",
                "lessons_learned": "update_security_policies"
            }
        )

        # Test different incident
        await security_telemetry.record_incident_lifecycle(
            incident_id="INC-2025-002",
            phase="created",
            metadata={
                "incident_type": "unauthorized_access",
                "severity": "medium"
            }
        )

        # Verify incident metrics were recorded
        summary = collector.get_telemetry_summary()
        assert summary["metrics_buffered"] > 0
        assert summary["events_buffered"] > 0

    @pytest.mark.asyncio
    async def test_complete_security_scenario(self) -> None:
        """Test complete security scenario with all SecurityTelemetry methods."""
        collector = TelemetryCollector(PROJECT_ID, "test-security-scenario")
        await asyncio.sleep(0.1)

        security_telemetry = SecurityTelemetry(collector)

        # 1. Multiple failed authentication attempts
        for i in range(5):
            await security_telemetry.record_authentication_attempt(
                user_id=f"attacker_{i}@external.com",
                success=False,
                method="password",
                source_ip=f"192.168.1.{100 + i}"
            )

        # 2. Threat detection for brute force
        await security_telemetry.record_threat_detection(
            threat_type="brute_force",
            severity="high",
            confidence=0.90,
            source="auth_monitor",
            details={
                "failed_attempts": 5,
                "time_window": "5_minutes",
                "source_ips": [f"192.168.1.{100 + i}" for i in range(5)]
            }
        )

        # 3. Incident creation
        await security_telemetry.record_incident_lifecycle(
            incident_id="INC-BRUTE-001",
            phase="created",
            metadata={
                "incident_type": "brute_force_attack",
                "severity": "high",
                "affected_systems": ["auth-server"],
                "automated_response": "block_source_ips"
            }
        )

        # 4. Successful authentication after blocking
        await security_telemetry.record_authentication_attempt(
            user_id="legitimate_user@company.com",
            success=True,
            method="mfa",
            source_ip="10.0.0.50"
        )

        # 5. Incident investigation
        await security_telemetry.record_incident_lifecycle(
            incident_id="INC-BRUTE-001",
            phase="investigating",
            duration_seconds=600.0,
            metadata={
                "investigation_findings": "known_attack_pattern",
                "blocked_ips": 5
            }
        )

        # 6. Additional threat detection
        await security_telemetry.record_threat_detection(
            threat_type="lateral_movement",
            severity="critical",
            confidence=0.95,
            source="network_monitor",
            details={
                "source_host": "compromised-workstation",
                "target_hosts": ["server-1", "server-2"],
                "protocol": "SMB"
            }
        )

        # 7. Incident resolution
        await security_telemetry.record_incident_lifecycle(
            incident_id="INC-BRUTE-001",
            phase="resolved",
            duration_seconds=1200.0,
            metadata={
                "resolution": "implemented_rate_limiting",
                "preventive_measures": ["ip_blocking", "enhanced_monitoring"]
            }
        )

        # Verify comprehensive telemetry
        summary = collector.get_telemetry_summary()
        assert summary["metrics_buffered"] >= 15  # Many metrics from all operations
        assert summary["events_buffered"] >= 10   # Events from failed auth + threats + incidents

    @pytest.mark.asyncio
    async def test_security_telemetry_edge_cases(self) -> None:
        """Test SecurityTelemetry methods with edge cases."""
        collector = TelemetryCollector(PROJECT_ID, "test-security-edge")
        await asyncio.sleep(0.1)

        security_telemetry = SecurityTelemetry(collector)

        # Test with empty/minimal values
        await security_telemetry.record_authentication_attempt(
            user_id="",
            success=False,
            method="unknown",
            source_ip="0.0.0.0"
        )

        # Test threat with minimal confidence
        await security_telemetry.record_threat_detection(
            threat_type="unknown",
            severity="info",
            confidence=0.01,
            source="test",
            details={}
        )

        # Test incident with minimal data
        await security_telemetry.record_incident_lifecycle(
            incident_id="MIN-001",
            phase="created",
            metadata={}
        )

        # Test with very long values
        long_user_id = "very_long_user_" + "x" * 1000
        await security_telemetry.record_authentication_attempt(
            user_id=long_user_id,
            success=True,
            method="certificate",
            source_ip="192.168.1.200"
        )

        # Test threat with many details
        many_details = {f"detail_{i}": f"value_{i}" for i in range(50)}
        await security_telemetry.record_threat_detection(
            threat_type="complex_threat",
            severity="medium",
            confidence=0.75,
            source="comprehensive_scanner",
            details=many_details
        )

        # Test incident with complex metadata
        complex_metadata = {
            "systems": [f"system_{i}" for i in range(20)],
            "timeline": {
                "start": datetime.now(timezone.utc).isoformat(),
                "events": [f"event_{i}" for i in range(10)]
            },
            "impact_assessment": {
                "financial": "high",
                "reputation": "medium",
                "operational": "low"
            }
        }
        await security_telemetry.record_incident_lifecycle(
            incident_id="COMPLEX-001",
            phase="analyzing",
            duration_seconds=3600.0,
            metadata=complex_metadata
        )

        # Verify edge case handling
        summary = collector.get_telemetry_summary()
        assert summary["metrics_buffered"] > 0
        assert summary["events_buffered"] > 0

    @pytest.mark.asyncio
    async def test_high_volume_security_telemetry(self) -> None:
        """Test high volume security telemetry for performance."""
        collector = TelemetryCollector(PROJECT_ID, "test-security-volume")
        await asyncio.sleep(0.1)

        security_telemetry = SecurityTelemetry(collector)

        import time
        start_time = time.time()

        # Generate high volume of security events
        for i in range(30):
            # Authentication events
            await security_telemetry.record_authentication_attempt(
                user_id=f"user_{i}@company.com",
                success=(i % 3 != 0),  # 66% success rate
                method="password" if i % 2 == 0 else "mfa",
                source_ip=f"192.168.{i % 10}.{i % 100}"
            )

            # Threat detections (every 3rd iteration)
            if i % 3 == 0:
                await security_telemetry.record_threat_detection(
                    threat_type=["malware", "phishing", "insider_threat"][i % 3],
                    severity=["low", "medium", "high", "critical"][i % 4],
                    confidence=0.5 + (i % 5) * 0.1,
                    source=f"detector_{i % 3}",
                    details={"event_id": i, "timestamp": datetime.now(timezone.utc).isoformat()}
                )

            # Incidents (every 10th iteration)
            if i % 10 == 0:
                await security_telemetry.record_incident_lifecycle(
                    incident_id=f"INC-VOL-{i:03d}",
                    phase="created",
                    metadata={
                        "incident_type": ["breach", "attack", "violation"][i % 3],
                        "severity": ["medium", "high", "critical"][i % 3],
                        "automated": True
                    }
                )

        processing_time = time.time() - start_time

        # Should complete efficiently
        assert processing_time < 5.0, f"Security telemetry processing took too long: {processing_time}s"

        # Verify volume handling
        summary = collector.get_telemetry_summary()
        assert summary["metrics_buffered"] >= 30  # Many metrics from volume test
        assert summary["events_buffered"] >= 15   # Failed auth + threats + incidents
