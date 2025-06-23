# Detection Agent Rule Definition Guide

This guide explains how to define, implement, and manage detection rules in the SentinelOps Detection Agent.

## Overview

Detection rules are the core logic that identify potential security threats in Google Cloud logs. The Detection Agent supports flexible rule definitions that can detect various types of suspicious activities.

## Rule Definition Format

Rules are defined using a standardized Python class structure that extends the base `DetectionRule` class.

### Basic Rule Structure

```python
from src.detection_agent.rules_engine import DetectionRule, RuleResult
from src.common.models import SecurityEvent, SeverityLevel, EventSource
from typing import List, Dict, Any
from datetime import datetime

class CustomDetectionRule(DetectionRule):
    def __init__(self):
        super().__init__(
            rule_id="custom_rule_id",
            name="Custom Rule Name",
            description="Description of what this rule detects",
            severity=SeverityLevel.MEDIUM,
            event_source=EventSource.AUDIT_LOG,
            enabled=True
        )

    def build_query(self, start_time: datetime, end_time: datetime) -> str:
        """Build the BigQuery SQL for this rule."""
        return f"""
        SELECT
            timestamp,
            actor,
            resource_name,
            method_name,
            source_ip,
            user_agent
        FROM `project.dataset.audit_logs`
        WHERE timestamp BETWEEN '{start_time}' AND '{end_time}'
            AND method_name = 'suspicious.method'
            AND status_code = 'SUCCESS'
        ORDER BY timestamp DESC
        """

    def evaluate_results(self, query_results: List[Dict]) -> RuleResult:
        """Evaluate query results and create security events."""
        events = []

        for row in query_results:
            # Apply rule logic
            if self._is_suspicious(row):
                event = SecurityEvent(
                    event_id=f"{self.rule_id}_{row['timestamp']}",
                    event_type="SUSPICIOUS_ACTIVITY",
                    severity=self.severity,
                    source=self.event_source,
                    timestamp=row['timestamp'],
                    actor=row['actor'],
                    affected_resources=[row['resource_name']],
                    description=f"Suspicious activity detected: {row['method_name']}",
                    metadata={
                        'source_ip': row['source_ip'],
                        'user_agent': row['user_agent'],
                        'method': row['method_name']
                    }
                )
                events.append(event)

        return RuleResult(
            rule_id=self.rule_id,
            success=True,
            events=events,
            execution_time=0.0  # Will be set by the engine
        )

    def _is_suspicious(self, row: Dict) -> bool:
        """Custom logic to determine if a log entry is suspicious."""
        # Implement your detection logic here
        return True
```

## Built-in Rule Types

### 1. Suspicious Login Rule

Detects unusual login patterns and authentication anomalies.

```python
class SuspiciousLoginRule(DetectionRule):
    def __init__(self):
        super().__init__(
            rule_id="suspicious_login",
            name="Suspicious Login Activity",
            description="Detects suspicious login patterns and authentication anomalies",
            severity=SeverityLevel.HIGH,
            event_source=EventSource.AUDIT_LOG,
            enabled=True
        )

    def build_query(self, start_time: datetime, end_time: datetime) -> str:
        return f"""
        SELECT
            timestamp,
            principal_email as actor,
            resource_name,
            method_name,
            source_ip,
            user_agent,
            authentication_info,
            request_metadata
        FROM `{self.get_audit_log_table()}`
        WHERE timestamp BETWEEN '{start_time}' AND '{end_time}'
            AND method_name IN (
                'google.iam.admin.v1.CreateServiceAccountKey',
                'SetIamPolicy',
                'google.cloud.sql.v1.SqlUsersService.Update'
            )
            AND (
                source_ip NOT LIKE '10.%'
                OR source_ip NOT LIKE '172.16.%'
                OR source_ip NOT LIKE '192.168.%'
            )
        ORDER BY timestamp DESC
        """

    def evaluate_results(self, query_results: List[Dict]) -> RuleResult:
        events = []
        ip_counts = {}

        # Count login attempts by IP
        for row in query_results:
            ip = row.get('source_ip', 'unknown')
            ip_counts[ip] = ip_counts.get(ip, 0) + 1

        for row in query_results:
            ip = row.get('source_ip', 'unknown')

            # Flag suspicious conditions
            is_suspicious = (
                ip_counts[ip] > 10 or  # High frequency from single IP
                self._is_known_malicious_ip(ip) or
                self._has_suspicious_user_agent(row.get('user_agent', ''))
            )

            if is_suspicious:
                event = SecurityEvent(
                    event_id=f"login_{row['timestamp']}_{ip}",
                    event_type="SUSPICIOUS_LOGIN",
                    severity=self.severity,
                    source=self.event_source,
                    timestamp=row['timestamp'],
                    actor=row['actor'],
                    affected_resources=[row['resource_name']],
                    description=f"Suspicious login detected from {ip}",
                    metadata={
                        'source_ip': ip,
                        'attempt_count': ip_counts[ip],
                        'method': row['method_name'],
                        'user_agent': row.get('user_agent')
                    }
                )
                events.append(event)

        return RuleResult(
            rule_id=self.rule_id,
            success=True,
            events=events
        )
```

### 2. Privilege Escalation Rule

Detects attempts to escalate privileges or gain unauthorized access.

```python
class PrivilegeEscalationRule(DetectionRule):
    def __init__(self):
        super().__init__(
            rule_id="privilege_escalation",
            name="Privilege Escalation Detection",
            description="Detects attempts to escalate privileges or modify IAM policies",
            severity=SeverityLevel.CRITICAL,
            event_source=EventSource.AUDIT_LOG,
            enabled=True
        )

    ESCALATION_METHODS = [
        'SetIamPolicy',
        'CreateRole',
        'UpdateRole',
        'CreateServiceAccount',
        'CreateServiceAccountKey',
        'google.iam.admin.v1.CreateServiceAccountKey'
    ]

    SENSITIVE_ROLES = [
        'roles/owner',
        'roles/editor',
        'roles/iam.serviceAccountAdmin',
        'roles/iam.serviceAccountKeyAdmin',
        'roles/iam.roleAdmin'
    ]

    def build_query(self, start_time: datetime, end_time: datetime) -> str:
        methods_filter = "', '".join(self.ESCALATION_METHODS)

        return f"""
        SELECT
            timestamp,
            principal_email as actor,
            resource_name,
            method_name,
            service_name,
            request_metadata.caller_ip as source_ip,
            authorization_info,
            request
        FROM `{self.get_audit_log_table()}`
        WHERE timestamp BETWEEN '{start_time}' AND '{end_time}'
            AND method_name IN ('{methods_filter}')
            AND severity = 'NOTICE'
        ORDER BY timestamp DESC
        """

    def evaluate_results(self, query_results: List[Dict]) -> RuleResult:
        events = []
        actor_activity = {}

        for row in query_results:
            actor = row.get('actor', 'unknown')

            # Track activity per actor
            if actor not in actor_activity:
                actor_activity[actor] = {
                    'methods': set(),
                    'resources': set(),
                    'count': 0
                }

            actor_activity[actor]['methods'].add(row['method_name'])
            actor_activity[actor]['resources'].add(row['resource_name'])
            actor_activity[actor]['count'] += 1

            # Check for immediate suspicious patterns
            is_suspicious = (
                self._involves_sensitive_role(row.get('request', {})) or
                self._is_cross_project_escalation(row) or
                self._is_service_account_key_creation(row)
            )

            if is_suspicious:
                event = SecurityEvent(
                    event_id=f"privilege_esc_{row['timestamp']}_{actor}",
                    event_type="PRIVILEGE_ESCALATION",
                    severity=self.severity,
                    source=self.event_source,
                    timestamp=row['timestamp'],
                    actor=actor,
                    affected_resources=[row['resource_name']],
                    description=f"Privilege escalation attempt: {row['method_name']}",
                    metadata={
                        'method': row['method_name'],
                        'service': row.get('service_name'),
                        'source_ip': row.get('source_ip'),
                        'authorization': row.get('authorization_info')
                    }
                )
                events.append(event)

        # Check for bulk escalation patterns
        for actor, activity in actor_activity.items():
            if (activity['count'] > 5 and
                len(activity['methods']) > 2 and
                len(activity['resources']) > 3):

                event = SecurityEvent(
                    event_id=f"bulk_escalation_{actor}_{start_time}",
                    event_type="BULK_PRIVILEGE_ESCALATION",
                    severity=SeverityLevel.CRITICAL,
                    source=self.event_source,
                    timestamp=datetime.now(),
                    actor=actor,
                    affected_resources=list(activity['resources']),
                    description=f"Bulk privilege escalation detected for {actor}",
                    metadata={
                        'total_actions': activity['count'],
                        'unique_methods': len(activity['methods']),
                        'unique_resources': len(activity['resources']),
                        'methods': list(activity['methods'])
                    }
                )
                events.append(event)

        return RuleResult(
            rule_id=self.rule_id,
            success=True,
            events=events
        )
```

### 3. Data Exfiltration Rule

Detects potential data exfiltration through unusual data access patterns.

```python
class DataExfiltrationRule(DetectionRule):
    def __init__(self):
        super().__init__(
            rule_id="data_exfiltration",
            name="Data Exfiltration Detection",
            description="Detects unusual data access patterns indicating potential exfiltration",
            severity=SeverityLevel.HIGH,
            event_source=EventSource.DATA_ACCESS_LOG,
            enabled=True
        )

    def build_query(self, start_time: datetime, end_time: datetime) -> str:
        return f"""
        SELECT
            timestamp,
            principal_email as actor,
            resource_name,
            method_name,
            request_metadata.caller_ip as source_ip,
            response.status as status_code,
            resource_location,
            request
        FROM `{self.get_data_access_log_table()}`
        WHERE timestamp BETWEEN '{start_time}' AND '{end_time}'
            AND (
                method_name LIKE '%GetObject%' OR
                method_name LIKE '%ListObjects%' OR
                method_name LIKE '%DownloadObject%' OR
                method_name LIKE '%ExportTable%'
            )
            AND response.status = 200
        ORDER BY timestamp DESC
        """
```

## Rule Configuration

### Enabling/Disabling Rules

```yaml
agents:
  detection:
    enabled_rules:
      - suspicious_login
      - privilege_escalation
      - data_exfiltration
      - vpc_suspicious_port_scan
      - firewall_rule_modification

    rule_specific_config:
      suspicious_login:
        max_attempts_threshold: 10
        time_window_minutes: 15

      privilege_escalation:
        sensitive_roles:
          - roles/owner
          - roles/iam.serviceAccountAdmin
        bulk_threshold: 5
```

### Rule Parameters

Each rule can accept configuration parameters:

```python
class ConfigurableRule(DetectionRule):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(...)

        # Load rule-specific configuration
        rule_config = config.get('rule_specific_config', {}).get(self.rule_id, {})
        self.threshold = rule_config.get('threshold', 10)
        self.time_window = rule_config.get('time_window_minutes', 60)
        self.excluded_actors = rule_config.get('excluded_actors', [])
```

## Testing Rules

### Unit Testing

```python
import unittest
from datetime import datetime, timedelta
from your_rule import CustomDetectionRule

class TestCustomDetectionRule(unittest.TestCase):
    def setUp(self):
        self.rule = CustomDetectionRule()
        self.start_time = datetime.now() - timedelta(hours=1)
        self.end_time = datetime.now()

    def test_query_generation(self):
        query = self.rule.build_query(self.start_time, self.end_time)
        self.assertIn('SELECT', query)
        self.assertIn('timestamp', query)

    def test_evaluation_logic(self):
        mock_results = [
            {
                'timestamp': '2024-01-15T10:30:00Z',
                'actor': 'test@example.com',
                'resource_name': 'test-resource',
                'method_name': 'suspicious.method',
                'source_ip': '192.168.1.1'
            }
        ]

        result = self.rule.evaluate_results(mock_results)
        self.assertTrue(result.success)
        self.assertEqual(len(result.events), 1)
        self.assertEqual(result.events[0].event_type, 'SUSPICIOUS_ACTIVITY')
```

### Integration Testing

```python
async def test_rule_integration():
    """Test rule with actual BigQuery data."""
    agent = DetectionAgent(test_config)
    rule = CustomDetectionRule()

    # Execute rule against test data
    result = await agent.execute_rule(rule, start_time, end_time)

    assert result.success
    assert len(result.events) >= 0
```

## Best Practices

### 1. Query Optimization
- Use appropriate time ranges to limit data scanned
- Include relevant WHERE clauses to filter early
- Avoid SELECT * queries
- Use proper indexing hints when available

### 2. Performance Considerations
- Set reasonable query timeouts
- Limit result set sizes
- Use pagination for large result sets
- Consider query caching for repeated patterns

### 3. False Positive Reduction
- Implement allow-lists for known good actors
- Use statistical thresholds rather than fixed limits
- Consider time-of-day and behavioral patterns
- Implement feedback mechanisms

### 4. Security
- Validate all input parameters
- Sanitize query parameters to prevent injection
- Limit access to sensitive log fields
- Implement proper error handling

### 5. Maintainability
- Document rule logic and thresholds
- Use clear variable names and comments
- Implement comprehensive logging
- Version control rule changes

## Rule Deployment

### Development Workflow

1. **Rule Development**
   - Write rule class
   - Implement unit tests
   - Test with sample data

2. **Testing**
   - Deploy to test environment
   - Run against historical data
   - Validate detection accuracy

3. **Staging**
   - Deploy to staging environment
   - Monitor performance impact
   - Tune thresholds based on results

4. **Production**
   - Gradual rollout
   - Monitor false positive rates
   - Adjust based on feedback

### Configuration Management

Rules should be managed through version-controlled configuration:

```yaml
# rules/production_rules.yaml
detection_rules:
  suspicious_login:
    enabled: true
    severity: HIGH
    parameters:
      max_attempts: 10
      time_window: 15

  privilege_escalation:
    enabled: true
    severity: CRITICAL
    parameters:
      bulk_threshold: 5
      sensitive_roles:
        - roles/owner
        - roles/editor
```

This guide provides the foundation for creating effective detection rules that can identify security threats while minimizing false positives and maintaining good performance characteristics.
