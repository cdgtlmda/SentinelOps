"""
Firewall logs query templates for the Detection Agent.

This module provides specialized queries for analyzing firewall logs.
"""

from typing import Dict, Any, List
from src.common.models import SeverityLevel
from .rules_engine import DetectionRule


class FirewallLogsQueries:
    """Query templates for firewall logs analysis."""

    @staticmethod
    def get_queries() -> Dict[str, Dict[str, Any]]:
        """
        Get all firewall logs detection queries.

        Returns:
            Dictionary of query definitions
        """
        return {
            "firewall_rule_modification": {
                "name": "Firewall Rule Modification",
                "description": "Detects modifications to firewall rules that may weaken security",
                "severity": SeverityLevel.HIGH,
                "query": """
                    SELECT
                        timestamp,
                        protoPayload.authenticationInfo.principalEmail as actor,
                        protoPayload.requestMetadata.callerIp as source_ip,
                        protoPayload.resourceName as resource_name,
                        protoPayload.methodName as method_name,
                        protoPayload.response.operationType as status_code,
                        STRUCT(
                            protoPayload.request.name as rule_name,
                            protoPayload.request.sourceRanges as source_ranges,
                            protoPayload.request.allowed as allowed_rules,
                            protoPayload.request.denied as denied_rules,
                            protoPayload.request.direction as direction,
                            protoPayload.request.priority as priority,
                            protoPayload.response.targetId as target_id
                        ) as request_details
                    FROM
                        `{project_id}.{dataset_id}.cloudaudit_googleapis_com_activity`
                    WHERE
                        timestamp > TIMESTAMP('{last_scan_time}')
                        AND timestamp <= TIMESTAMP('{current_time}')
                        AND resource.type = 'gce_firewall_rule'
                        AND protoPayload.methodName IN (
                            'v1.compute.firewalls.insert',
                            'v1.compute.firewalls.patch',
                            'v1.compute.firewalls.update',
                            'v1.compute.firewalls.delete'
                        )
                    ORDER BY timestamp DESC
                    LIMIT 100
                """,
                "tags": ["firewall", "configuration_change", "security"]
            },

            "permissive_firewall_rules": {
                "name": "Overly Permissive Firewall Rules",
                "description": (
                    "Detects creation of firewall rules that allow traffic from any source"
                ),
                "severity": SeverityLevel.CRITICAL,
                "query": """
                    SELECT
                        timestamp,
                        protoPayload.authenticationInfo.principalEmail as actor,
                        protoPayload.requestMetadata.callerIp as source_ip,
                        protoPayload.resourceName as resource_name,
                        protoPayload.methodName as method_name,
                        0 as status_code,
                        STRUCT(
                            protoPayload.request.name as rule_name,
                            protoPayload.request.sourceRanges as source_ranges,
                            protoPayload.request.allowed as allowed_rules,
                            protoPayload.request.direction as direction,
                            protoPayload.request.priority as priority,
                            protoPayload.request.targetTags as target_tags,
                            protoPayload.request.targetServiceAccounts as target_service_accounts
                        ) as request_details
                    FROM
                        `{project_id}.{dataset_id}.cloudaudit_googleapis_com_activity`
                    WHERE
                        timestamp > TIMESTAMP('{last_scan_time}')
                        AND timestamp <= TIMESTAMP('{current_time}')
                        AND resource.type = 'gce_firewall_rule'
                        AND protoPayload.methodName IN (
                            'v1.compute.firewalls.insert',
                            'v1.compute.firewalls.patch',
                            'v1.compute.firewalls.update'
                        )
                        AND (
                            '0.0.0.0/0' IN UNNEST(protoPayload.request.sourceRanges)
                            OR '*' IN UNNEST(protoPayload.request.sourceRanges)
                        )
                    ORDER BY timestamp DESC
                    LIMIT 100
                """,
                "tags": ["firewall", "misconfiguration", "critical"]
            },
            "denied_traffic_spike": {
                "name": "Spike in Denied Traffic",
                "description": (
                    "Detects sudden increases in firewall-denied traffic that "
                    "may indicate an attack"
                ),
                "severity": SeverityLevel.MEDIUM,
                "query": """
                    WITH denied_traffic_stats AS (
                        SELECT
                            jsonPayload.instance.vm_name as target_vm,
                            jsonPayload.vpc.vpc_name as vpc_name,
                            jsonPayload.rule_details.reference as firewall_rule,
                            jsonPayload.remote_location.country as source_country,
                            jsonPayload.connection.src_ip as source_ip,
                            COUNT(*) as denied_count,
                            COUNT(DISTINCT jsonPayload.connection.src_ip) as unique_sources,
                            COUNT(DISTINCT jsonPayload.connection.dest_port) as unique_ports,
                            MIN(timestamp) as first_denied,
                            MAX(timestamp) as last_denied
                        FROM
                            `{project_id}.{dataset_id}.compute_googleapis_com_firewall`
                        WHERE
                            timestamp > TIMESTAMP('{last_scan_time}')
                            AND timestamp <= TIMESTAMP('{current_time}')
                            AND jsonPayload.rule_details.action = 'DENY'
                        GROUP BY
                            target_vm, vpc_name, firewall_rule, source_country, source_ip
                        HAVING
                            denied_count >= 100  -- Threshold for spike detection
                    )
                    SELECT
                        first_denied as timestamp,
                        source_ip as actor,
                        source_ip,
                        target_vm as resource_name,
                        'firewall_denied_spike' as method_name,
                        denied_count as status_code,
                        STRUCT(
                            denied_count,
                            unique_sources,
                            unique_ports,
                            vpc_name,
                            firewall_rule,
                            source_country,
                            TIMESTAMP_DIFF(last_denied, first_denied, SECOND) as duration_seconds
                        ) as request_details
                    FROM denied_traffic_stats
                    ORDER BY denied_count DESC
                    LIMIT 100
                """,
                "tags": ["firewall", "denied_traffic", "attack_detection"]
            },
            "firewall_bypass_attempt": {
                "name": "Potential Firewall Bypass Attempts",
                "description": (
                    "Detects patterns that may indicate attempts to bypass firewall rules"
                ),
                "severity": SeverityLevel.HIGH,
                "query": """
                    WITH bypass_patterns AS (
                        SELECT
                            jsonPayload.connection.src_ip as source_ip,
                            jsonPayload.instance.vm_name as target_vm,
                            jsonPayload.connection.protocol as protocol,
                            ARRAY_AGG(
                                DISTINCT jsonPayload.connection.dest_port
                                ORDER BY jsonPayload.connection.dest_port
                            ) as attempted_ports,
                            COUNT(*) as total_attempts,
                            COUNT(DISTINCT jsonPayload.connection.dest_port) as unique_ports,
                            COUNT(DISTINCT jsonPayload.rule_details.reference) as rules_triggered,
                            MIN(timestamp) as first_attempt,
                            MAX(timestamp) as last_attempt
                        FROM
                            `{project_id}.{dataset_id}.compute_googleapis_com_firewall`
                        WHERE
                            timestamp > TIMESTAMP('{last_scan_time}')
                            AND timestamp <= TIMESTAMP('{current_time}')
                            AND jsonPayload.rule_details.action IN ('DENY', 'BLOCKED')
                        GROUP BY
                            source_ip, target_vm, protocol
                        HAVING
                            unique_ports >= 20  -- Many different ports attempted
                            OR total_attempts >= 500  -- High volume of attempts
                    )
                    SELECT
                        first_attempt as timestamp,
                        source_ip as actor,
                        source_ip,
                        target_vm as resource_name,
                        'firewall_bypass_attempt' as method_name,
                        total_attempts as status_code,
                        STRUCT(
                            total_attempts,
                            unique_ports,
                            rules_triggered,
                            protocol,
                            attempted_ports[SAFE_OFFSET(0):10] as sample_ports,  -- First 10 ports
                            TIMESTAMP_DIFF(last_attempt, first_attempt, SECOND) as duration_seconds
                        ) as request_details

                    FROM bypass_patterns
                    ORDER BY total_attempts DESC
                    LIMIT 100
                """,
                "tags": ["firewall", "bypass_attempt", "reconnaissance"]
            }
        }

    @staticmethod
    def create_detection_rules() -> List[DetectionRule]:
        """
        Create DetectionRule objects from firewall logs queries.

        Returns:
            List of DetectionRule objects
        """
        from src.detection_agent.rules_engine import DetectionRule as RulesEngineDetectionRule

        rules = []
        queries = FirewallLogsQueries.get_queries()

        for rule_id, query_def in queries.items():
            rule = RulesEngineDetectionRule(
                rule_id=f"firewall_{rule_id}",
                name=query_def["name"],
                description=query_def["description"],
                severity=query_def["severity"],
                query=query_def["query"],
                tags=query_def["tags"]
            )
            rules.append(rule)

        return rules
