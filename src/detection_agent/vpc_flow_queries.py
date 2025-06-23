"""
VPC Flow Logs query templates for the Detection Agent.

This module provides specialized queries for analyzing VPC flow logs.
"""

from typing import Any, Dict, List

from src.common.models import SeverityLevel

from .rules_engine import DetectionRule


class VPCFlowLogsQueries:
    """Query templates for VPC flow logs analysis."""

    @staticmethod
    def get_queries() -> Dict[str, Dict[str, Any]]:
        """
        Get all VPC flow logs detection queries.

        Returns:
            Dictionary of query definitions
        """
        return {
            "suspicious_port_scan": {
                "name": "Suspicious Port Scanning Activity",
                "description": "Detects potential port scanning activity from a single source",
                "severity": SeverityLevel.HIGH,
                "query": """
                    WITH port_scan_activity AS (
                        SELECT
                            jsonPayload.connection.src_ip as source_ip,
                            jsonPayload.connection.dest_ip as destination_ip,
                            COUNT(DISTINCT jsonPayload.connection.dest_port) as unique_ports,
                            COUNT(*) as connection_attempts,
                            MIN(timestamp) as first_seen,
                            MAX(timestamp) as last_seen,
                            ARRAY_AGG(
                                DISTINCT jsonPayload.connection.dest_port
                                ORDER BY jsonPayload.connection.dest_port
                                LIMIT 100
                            ) as scanned_ports
                        FROM
                            `{project_id}.{dataset_id}.compute_googleapis_com_vpc_flows`
                        WHERE
                            timestamp > TIMESTAMP('{last_scan_time}')
                            AND timestamp <= TIMESTAMP('{current_time}')
                            AND jsonPayload.connection.protocol IN (6, 17)  -- TCP or UDP
                            AND jsonPayload.reporter = 'DEST'
                        GROUP BY
                            source_ip, destination_ip
                        HAVING
                            unique_ports >= 10  -- Threshold for port scan detection
                    )                    SELECT
                        first_seen as timestamp,
                        source_ip as actor,
                        source_ip,
                        destination_ip as resource_name,
                        'port_scan' as method_name,
                        unique_ports as status_code,
                        STRUCT(
                            connection_attempts,
                            unique_ports,
                            scanned_ports,
                            TIMESTAMP_DIFF(last_seen, first_seen, SECOND) as duration_seconds
                        ) as request_details
                    FROM port_scan_activity
                    ORDER BY unique_ports DESC
                    LIMIT 100
                """,
                "tags": ["network", "port_scan", "reconnaissance"],
            },
            "unusual_traffic_volume": {
                "name": "Unusual Network Traffic Volume",
                "description": (
                    "Detects unusually high traffic volumes that may indicate "
                    "data exfiltration"
                ),
                "severity": SeverityLevel.HIGH,
                "query": """
                    WITH traffic_stats AS (
                        SELECT
                            jsonPayload.connection.src_ip as source_ip,
                            jsonPayload.connection.dest_ip as destination_ip,
                            jsonPayload.src_instance.vm_name as source_vm,
                            jsonPayload.dest_instance.vm_name as destination_vm,
                            SUM(CAST(jsonPayload.bytes_sent AS INT64)) as total_bytes_sent,
                            COUNT(*) as flow_count,
                            MIN(timestamp) as first_seen,
                            MAX(timestamp) as last_seen
                        FROM
                            `{project_id}.{dataset_id}.compute_googleapis_com_vpc_flows`
                        WHERE
                            timestamp > TIMESTAMP('{last_scan_time}')
                            AND timestamp <= TIMESTAMP('{current_time}')
                            AND jsonPayload.reporter = 'SRC'
                        GROUP BY
                            source_ip, destination_ip, source_vm, destination_vm
                        HAVING
                            total_bytes_sent > 1073741824  -- 1GB threshold
                    )                    SELECT
                        first_seen as timestamp,
                        source_ip as actor,
                        source_ip,
                        COALESCE(destination_vm, destination_ip) as resource_name,
                        'high_volume_transfer' as method_name,
                        0 as status_code,
                        STRUCT(
                            total_bytes_sent,
                            flow_count,
                            source_vm,
                            destination_vm,
                            TIMESTAMP_DIFF(last_seen, first_seen, SECOND) as duration_seconds,
                            total_bytes_sent / TIMESTAMP_DIFF(
                                last_seen, first_seen, SECOND
                            ) as bytes_per_second
                        ) as request_details
                    FROM traffic_stats
                    ORDER BY total_bytes_sent DESC
                    LIMIT 100
                """,
                "tags": ["network", "data_exfiltration", "high_volume"],
            },
            "blocked_traffic_attempts": {
                "name": "Blocked Network Traffic Attempts",
                "description": (
                    "Detects repeated blocked connection attempts that may indicate "
                    "an attack"
                ),
                "severity": SeverityLevel.MEDIUM,
                "query": """
                    WITH blocked_connections AS (
                        SELECT
                            jsonPayload.connection.src_ip as source_ip,
                            jsonPayload.connection.dest_ip as destination_ip,
                            jsonPayload.connection.dest_port as destination_port,
                            COUNT(*) as blocked_attempts,
                            MIN(timestamp) as first_attempt,
                            MAX(timestamp) as last_attempt,
                            ARRAY_AGG(
                                DISTINCT jsonPayload.connection.protocol IGNORE NULLS
                            ) as protocols
                        FROM
                            `{project_id}.{dataset_id}.compute_googleapis_com_vpc_flows`
                        WHERE
                            timestamp > TIMESTAMP('{last_scan_time}')
                            AND timestamp <= TIMESTAMP('{current_time}')
                            AND jsonPayload.reporter = 'DEST'
                            AND jsonPayload.connection.protocol IN (6, 17)  -- TCP or UDP
                            AND CAST(jsonPayload.packets_sent AS INT64) > 0
                            -- No response packets
                            AND CAST(jsonPayload.packets_received AS INT64) = 0
                        GROUP BY
                            source_ip, destination_ip, destination_port
                        HAVING
                            blocked_attempts >= 10
                    )                    SELECT
                        first_attempt as timestamp,
                        source_ip as actor,
                        source_ip,
                        CONCAT(
                            destination_ip, ':', CAST(destination_port AS STRING)
                        ) as resource_name,
                        'blocked_connection' as method_name,
                        blocked_attempts as status_code,
                        STRUCT(
                            blocked_attempts,
                            destination_port,
                            protocols,
                            TIMESTAMP_DIFF(last_attempt, first_attempt, SECOND) as duration_seconds
                        ) as request_details
                    FROM blocked_connections
                    ORDER BY blocked_attempts DESC
                    LIMIT 100
                """,
                "tags": ["network", "firewall", "blocked_traffic"],
            },
            "external_ip_communication": {
                "name": "Suspicious External IP Communication",
                "description": "Detects communication with known malicious or unusual external IPs",
                "severity": SeverityLevel.HIGH,
                "query": """
                    WITH external_traffic AS (
                        SELECT
                            jsonPayload.connection.src_ip as source_ip,
                            jsonPayload.connection.dest_ip as destination_ip,
                            jsonPayload.src_instance.vm_name as source_vm,
                            jsonPayload.src_location.country as source_country,
                            jsonPayload.dest_location.country as dest_country,
                            SUM(CAST(jsonPayload.bytes_sent AS INT64)) as bytes_sent,
                            SUM(CAST(jsonPayload.bytes_received AS INT64)) as bytes_received,
                            COUNT(*) as connection_count,
                            MIN(timestamp) as first_seen,
                            MAX(timestamp) as last_seen
                        FROM
                            `{project_id}.{dataset_id}.compute_googleapis_com_vpc_flows`
                        WHERE
                            timestamp > TIMESTAMP('{last_scan_time}')
                            AND timestamp <= TIMESTAMP('{current_time}')
                            AND jsonPayload.reporter = 'SRC'
                            AND (
                                NOT REGEXP_CONTAINS(
                                    jsonPayload.connection.dest_ip,
                                    r'^(10\\.|172\\.(1[6-9]|2[0-9]|3[0-1])\\.|192\\.168\\.)'
                                )
                                OR jsonPayload.dest_location.country NOT IN (
                                    'US', 'GB', 'CA', 'AU', 'DE', 'FR', 'JP'
                                )
                            )
                        GROUP BY
                            source_ip, destination_ip, source_vm, source_country, dest_country
                    )                    SELECT
                        first_seen as timestamp,
                        source_ip as actor,
                        source_ip,
                        destination_ip as resource_name,
                        'external_communication' as method_name,
                        0 as status_code,
                        STRUCT(
                            bytes_sent,
                            bytes_received,
                            connection_count,
                            source_vm,
                            source_country,
                            dest_country,
                            TIMESTAMP_DIFF(last_seen, first_seen, SECOND) as duration_seconds
                        ) as request_details
                    FROM external_traffic
                    WHERE
                        bytes_sent > 104857600  -- 100MB threshold
                        OR dest_country IN ('CN', 'RU', 'KP', 'IR')  -- High-risk countries
                    ORDER BY bytes_sent DESC
                    LIMIT 100
                """,
                "tags": ["network", "external_communication", "data_exfiltration"],
            },
            "lateral_movement": {
                "name": "Potential Lateral Movement",
                "description": (
                    "Detects unusual internal network connections that may indicate "
                    "lateral movement"
                ),
                "severity": SeverityLevel.HIGH,
                "query": """
                    WITH internal_connections AS (
                        SELECT
                            jsonPayload.connection.src_ip as source_ip,
                            jsonPayload.connection.dest_ip as destination_ip,
                            jsonPayload.src_instance.vm_name as source_vm,
                            jsonPayload.dest_instance.vm_name as destination_vm,
                            jsonPayload.connection.dest_port as destination_port,
                            COUNT(*) as connection_count,
                            MIN(timestamp) as first_seen,
                            MAX(timestamp) as last_seen
                        FROM
                            `{project_id}.{dataset_id}.compute_googleapis_com_vpc_flows`
                        WHERE
                            timestamp > TIMESTAMP('{last_scan_time}')
                            AND timestamp <= TIMESTAMP('{current_time}')
                            AND jsonPayload.reporter = 'SRC'
                            -- Internal IPs only
                            AND REGEXP_CONTAINS(
                                jsonPayload.connection.src_ip,
                                r'^(10\\.|172\\.(1[6-9]|2[0-9]|3[0-1])\\.|192\\.168\\.)'
                            )
                            AND REGEXP_CONTAINS(
                                jsonPayload.connection.dest_ip,
                                r'^(10\\.|172\\.(1[6-9]|2[0-9]|3[0-1])\\.|192\\.168\\.)'
                            )
                            -- Common lateral movement ports
                            -- Common lateral movement ports
                            AND jsonPayload.connection.dest_port IN (
                                22, 23, 135, 139, 445, 3389, 5985, 5986
                            )
                        GROUP BY
                            source_ip, destination_ip, source_vm, destination_vm, destination_port
                    )                    SELECT
                        first_seen as timestamp,
                        source_ip as actor,
                        source_ip,
                        COALESCE(destination_vm, destination_ip) as resource_name,
                        'lateral_movement' as method_name,
                        destination_port as status_code,
                        STRUCT(
                            connection_count,
                            destination_port,
                            source_vm,
                            destination_vm,
                            TIMESTAMP_DIFF(last_seen, first_seen, SECOND) as duration_seconds
                        ) as request_details
                    FROM internal_connections
                    WHERE
                        connection_count >= 5  -- Multiple connection attempts
                    ORDER BY first_seen DESC
                    LIMIT 100
                """,
                "tags": ["network", "lateral_movement", "internal_reconnaissance"],
            },
        }

    @staticmethod
    def create_detection_rules() -> List[DetectionRule]:
        """
        Create DetectionRule objects from VPC flow log queries.

        Returns:
            List of DetectionRule objects
        """
        from src.detection_agent.rules_engine import DetectionRule as RulesEngineDetectionRule

        rules = []
        queries = VPCFlowLogsQueries.get_queries()

        for rule_id, query_def in queries.items():
            rule = RulesEngineDetectionRule(
                rule_id=f"vpc_{rule_id}",
                name=query_def["name"],
                description=query_def["description"],
                severity=query_def["severity"],
                query=query_def["query"],
                tags=query_def["tags"],
            )
            rules.append(rule)

        return rules
