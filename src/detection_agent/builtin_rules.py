"""
Built-in detection rules for SentinelOps.

This module contains the default security detection rules.
"""

from src.common.models import SeverityLevel
from .rules_engine import DetectionRule

# Define all built-in rules
BUILTIN_RULES = [
    DetectionRule(
        rule_id="suspicious_login",
        name="Suspicious Login Detection",
        description="Detects login attempts from unauthorized IP addresses",
        severity=SeverityLevel.HIGH,
        query="""
            SELECT
                timestamp,
                protopayload_auditlog.authenticationInfo.principalEmail as actor,
                protopayload_auditlog.requestMetadata.callerIp as source_ip,
                protopayload_auditlog.resourceName as resource_name,
                protopayload_auditlog.methodName as method_name,
                protopayload_auditlog.status.code as status_code,
                protopayload_auditlog.status.message as status_message
            FROM
                `{project_id}.{dataset_id}.cloudaudit_googleapis_com_activity`
            WHERE
                timestamp > TIMESTAMP('{last_scan_time}')
                AND timestamp <= TIMESTAMP('{current_time}')
                AND protopayload_auditlog.methodName = 'google.login.LoginService.loginSuccess'
                AND protopayload_auditlog.requestMetadata.callerIp NOT IN (
                    SELECT ip FROM `{project_id}.{dataset_id}.allowed_ips`
                )
            ORDER BY
                timestamp DESC
            LIMIT 1000
        """,
        tags=["authentication", "login", "access_control"],
    ),
    DetectionRule(
        rule_id="unusual_api_calls",
        name="Unusual API Call Detection",
        description="Detects potentially malicious API calls",
        severity=SeverityLevel.MEDIUM,
        query="""
            SELECT
                timestamp,
                protopayload_auditlog.authenticationInfo.principalEmail as actor,
                protopayload_auditlog.requestMetadata.callerIp as source_ip,
                protopayload_auditlog.resourceName as resource_name,
                protopayload_auditlog.methodName as method_name,
                protopayload_auditlog.status.code as status_code,
                protopayload_auditlog.request as request_details
            FROM
                `{project_id}.{dataset_id}.cloudaudit_googleapis_com_activity`
            WHERE
                timestamp > TIMESTAMP('{last_scan_time}')
                AND timestamp <= TIMESTAMP('{current_time}')
                AND protopayload_auditlog.methodName IN (
                    'SetIamPolicy',
                    'compute.instances.setMetadata',
                    'compute.disks.createSnapshot',
                    'storage.buckets.delete',
                    'storage.objects.delete'
                )
            ORDER BY
                timestamp DESC
            LIMIT 1000
        """,
        tags=["api", "suspicious_activity"],
    ),
    DetectionRule(
        rule_id="privilege_escalation",
        name="Privilege Escalation Detection",
        description="Detects potential privilege escalation attempts",
        severity=SeverityLevel.CRITICAL,
        query="""
            SELECT
                timestamp,
                protopayload_auditlog.authenticationInfo.principalEmail as actor,
                protopayload_auditlog.requestMetadata.callerIp as source_ip,
                protopayload_auditlog.resourceName as resource_name,
                protopayload_auditlog.methodName as method_name,
                protopayload_auditlog.request as request_details,
                protopayload_auditlog.response as response_details
            FROM
                `{project_id}.{dataset_id}.cloudaudit_googleapis_com_activity`
            WHERE
                timestamp > TIMESTAMP('{last_scan_time}')
                AND timestamp <= TIMESTAMP('{current_time}')
                AND (
                    protopayload_auditlog.methodName = 'SetIamPolicy'
                    OR protopayload_auditlog.methodName LIKE '%roles%'
                    OR protopayload_auditlog.methodName LIKE '%permissions%'
                )
                AND protopayload_auditlog.status.code = 0
            ORDER BY
                timestamp DESC
            LIMIT 1000
        """,
        tags=["iam", "privilege_escalation", "critical"],
    ),
    DetectionRule(
        rule_id="data_exfiltration",
        name="Data Exfiltration Detection",
        description="Detects potential data exfiltration activities",
        severity=SeverityLevel.HIGH,
        query="""
            SELECT
                timestamp,
                protopayload_auditlog.authenticationInfo.principalEmail as actor,
                protopayload_auditlog.requestMetadata.callerIp as source_ip,
                protopayload_auditlog.resourceName as resource_name,
                protopayload_auditlog.methodName as method_name,
                protopayload_auditlog.request as request_details,
                protopayload_auditlog.response as response_details
            FROM
                `{project_id}.{dataset_id}.cloudaudit_googleapis_com_data_access`
            WHERE
                timestamp > TIMESTAMP('{last_scan_time}')
                AND timestamp <= TIMESTAMP('{current_time}')
                AND (
                    protopayload_auditlog.methodName LIKE '%storage.objects.get%'
                    OR protopayload_auditlog.methodName LIKE '%bigquery.tables.export%'
                    OR protopayload_auditlog.methodName LIKE '%compute.disks.createSnapshot%'
                )
                AND protopayload_auditlog.requestMetadata.callerIp NOT IN (
                    SELECT ip FROM `{project_id}.{dataset_id}.allowed_ips`
                )
            ORDER BY
                timestamp DESC
            LIMIT 1000
        """,
        tags=["data_exfiltration", "data_loss"],
    ),
    DetectionRule(
        rule_id="resource_modification",
        name="Unauthorized Resource Modification",
        description="Detects unauthorized modifications to cloud resources",
        severity=SeverityLevel.MEDIUM,
        query="""
            SELECT
                timestamp,
                protopayload_auditlog.authenticationInfo.principalEmail as actor,
                protopayload_auditlog.requestMetadata.callerIp as source_ip,
                protopayload_auditlog.resourceName as resource_name,
                protopayload_auditlog.methodName as method_name,
                protopayload_auditlog.request as request_details,
                protopayload_auditlog.response as response_details
            FROM
                `{project_id}.{dataset_id}.cloudaudit_googleapis_com_activity`
            WHERE
                timestamp > TIMESTAMP('{last_scan_time}')
                AND timestamp <= TIMESTAMP('{current_time}')
                AND (
                    protopayload_auditlog.methodName LIKE '%delete%'
                    OR protopayload_auditlog.methodName LIKE '%update%'
                    OR protopayload_auditlog.methodName LIKE '%patch%'
                )
                AND protopayload_auditlog.status.code = 0
            ORDER BY
                timestamp DESC
            LIMIT 1000
        """,
        tags=["resource_management", "modification"],
    ),
    DetectionRule(
        rule_id="firewall_change",
        name="Firewall Configuration Change",
        description="Detects changes to firewall rules or network security settings",
        severity=SeverityLevel.HIGH,
        query="""
            SELECT
                timestamp,
                protopayload_auditlog.authenticationInfo.principalEmail as actor,
                protopayload_auditlog.requestMetadata.callerIp as source_ip,
                protopayload_auditlog.resourceName as resource_name,
                protopayload_auditlog.methodName as method_name,
                protopayload_auditlog.request as request_details,
                protopayload_auditlog.response as response_details
            FROM
                `{project_id}.{dataset_id}.cloudaudit_googleapis_com_activity`
            WHERE
                timestamp > TIMESTAMP('{last_scan_time}')
                AND timestamp <= TIMESTAMP('{current_time}')                AND (
                    protopayload_auditlog.methodName LIKE '%firewalls%'
                    OR protopayload_auditlog.methodName LIKE '%securityPolicies%'
                    OR protopayload_auditlog.methodName LIKE '%networks%'
                )
                AND protopayload_auditlog.status.code = 0
            ORDER BY
                timestamp DESC
            LIMIT 1000
        """,
        tags=["network_security", "firewall", "configuration_change"],
    ),
]
