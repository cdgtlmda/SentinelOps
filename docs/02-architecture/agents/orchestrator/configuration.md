# Orchestration Agent Configuration Guide

## Overview

This guide provides detailed configuration options for the Orchestration Agent, including examples and best practices for different deployment scenarios.

## Configuration Structure

The orchestration agent configuration is organized into several main sections:

```yaml
orchestrator:
  # Core settings
  agent_id: "orchestrator-001"
  
  # Workflow settings
  workflow:
    max_concurrent_incidents: 10
    global_timeout_seconds: 1800
    
  # Stage-specific timeouts
  timeouts:
    analysis: 300
    remediation: 600
    approval: 1800
    notification_delivery: 60
    
  # Auto-remediation settings
  auto_remediation:
    enabled: true
    confidence_threshold: 0.7
    max_auto_approvals_per_hour: 50
    
  # Performance settings
  performance:
    cache_ttl_minutes: 5
    batch_size: 50
    max_cache_size: 1000
    query_cache_size: 100
    
  # Error recovery settings
  error_recovery:
    max_retries: 3
    backoff_multiplier: 2.0
    circuit_breaker_threshold: 5
    circuit_breaker_timeout: 300
```

## Detailed Configuration Options

### Workflow Configuration

#### max_concurrent_incidents
- **Type**: Integer
- **Default**: 10
- **Description**: Maximum number of incidents to process simultaneously
- **Considerations**: Higher values increase throughput but require more resources

```yaml
# Production environment with high resources
max_concurrent_incidents: 20

# Development environment
max_concurrent_incidents: 5
```

#### global_timeout_seconds
- **Type**: Integer
- **Default**: 1800 (30 minutes)
- **Description**: Maximum time for complete incident resolution
- **Considerations**: Should be sum of all stage timeouts plus buffer

### Timeout Configuration

Configure timeouts for each workflow stage:

```yaml
timeouts:
  # Analysis phase timeout
  analysis: 300  # 5 minutes
  
  # Remediation proposal timeout
  remediation_proposal: 120  # 2 minutes
  
  # Remediation execution timeout
  remediation_execution: 600  # 10 minutes
  
  # Human approval timeout
  approval: 1800  # 30 minutes
  
  # Notification delivery confirmation
  notification_delivery: 60  # 1 minute
```

### Auto-Remediation Configuration

#### Basic Settings

```yaml
auto_remediation:
  # Enable/disable auto-remediation globally
  enabled: true
  
  # Minimum confidence score for auto-remediation
  confidence_threshold: 0.7
  
  # Rate limiting
  max_auto_approvals_per_hour: 50
  
  # Auto-approve on timeout
  auto_approve_on_timeout: false
```

#### Custom Approval Rules

```yaml
approval_rules:
  # Rule 1: Safe read-only operations
  - rule_id: "safe_readonly_ops"
    name: "Auto-approve read-only operations"
    enabled: true
    conditions:
      severity:
        operator: "in"
        value: ["low", "medium"]
      confidence_score:
        operator: "greater_than"
        value: 0.7
    action_patterns:
      - "get_.*"
      - "list_.*"
      - "describe_.*"
    max_risk_score: 0.2
    
  # Rule 2: Emergency isolation
  - rule_id: "emergency_isolation"
    name: "Auto-isolate critical threats"
    enabled: true
    conditions:
      severity: "critical"
      threat_type:
        operator: "in"
        value: ["active_breach", "data_exfiltration"]
      confidence_score:
        operator: "greater_than"
        value: 0.9
    action_patterns:
      - "isolate_instance"
      - "block_ip_address"
      - "revoke_all_access"
    max_risk_score: 0.6
```

### Retention Policies

Configure data retention policies to manage storage and compliance requirements:

```yaml
retention:
  # Enable archival before deletion
  archive_enabled: true
  archive_bucket: "sentinelops-archive"
  
  # Define retention policies
  policies:
    # Default incident retention
    default_incidents:
      retention_days: 90
      applies_to: ["incidents"]
      conditions:
        status: ["closed", "resolved"]
      archive_before_delete: true
    
    # Compliance audit log retention (7 years)
    compliance_audit:
      retention_days: 2555  # 7 years
      applies_to: ["audit_logs"]
      archive_before_delete: true
    
    # Metrics retention
    metrics_retention:
      retention_days: 30
      applies_to: ["metrics"]
      archive_before_delete: false
  
  # Severity-based retention overrides
  by_severity:
    low: 30      # 30 days for low severity
    medium: 90   # 90 days for medium
    high: 180    # 180 days for high
    critical: 365  # 1 year for critical
```

#### Retention Policy Features

1. **Automatic Cleanup**: Daily automated cleanup based on policies
2. **Conditional Retention**: Apply different policies based on incident attributes
3. **Archival Support**: Archive data before deletion for compliance
4. **Severity-Based**: Different retention periods by incident severity

#### Example: Custom Retention Policy

```yaml
retention:
  policies:
    # Retain failed incidents longer for analysis
    failed_incidents:
      retention_days: 180
      applies_to: ["incidents"]
      conditions:
        status: "failed"
      archive_before_delete: true
    
    # Short retention for test incidents
    test_incidents:
      retention_days: 7
      applies_to: ["incidents"]
      conditions:
        category: "test"
      archive_before_delete: false
```

### Performance Optimization

#### Caching Configuration

```yaml
performance:
  # Incident cache settings
  cache:
    ttl_minutes: 5
    max_size: 1000
    eviction_policy: "lru"  # least recently used
    
  # Query result caching
  query_cache:
    enabled: true
    ttl_seconds: 30
    max_entries: 100
```

#### Batch Processing

```yaml
performance:
  batching:
    # Firestore batch settings
    firestore:
      enabled: true
      max_batch_size: 50
      flush_interval_ms: 1000
      
    # Pub/Sub batch settings
    pubsub:
      enabled: true
      max_messages: 100
      max_latency_ms: 100
```

### Error Recovery Configuration

```yaml
error_recovery:
  # Retry configuration
  retry:
    max_attempts: 3
    initial_delay_ms: 1000
    max_delay_ms: 60000
    multiplier: 2.0
    
  # Circuit breaker settings
  circuit_breaker:
    failure_threshold: 5
    success_threshold: 2
    timeout_seconds: 300
    
  # Error type specific settings
  error_handlers:
    - error_type: "agent_communication"
      strategy: "retry_with_backoff"
      max_retries: 5
      
    - error_type: "firestore_error"
      strategy: "retry_with_backoff"
      max_retries: 3
      
    - error_type: "validation_error"
      strategy: "skip"
      
    - error_type: "timeout_error"
      strategy: "escalate"
```

## Environment-Specific Configurations

### Development Environment

```yaml
orchestrator:
  environment: "development"
  
  workflow:
    max_concurrent_incidents: 3
    
  timeouts:
    analysis: 60
    remediation: 120
    approval: 300
    
  auto_remediation:
    enabled: false  # Manual approval in dev
    
  logging:
    level: "DEBUG"
    
  performance:
    cache_ttl_minutes: 1
    batch_size: 10
```

### Staging Environment

```yaml
orchestrator:
  environment: "staging"
  
  workflow:
    max_concurrent_incidents: 5
    
  timeouts:
    analysis: 180
    remediation: 300
    approval: 900
    
  auto_remediation:
    enabled: true
    confidence_threshold: 0.8  # Higher threshold for staging
    
  logging:
    level: "INFO"
```

### Production Environment

```yaml
orchestrator:
  environment: "production"
  
  workflow:
    max_concurrent_incidents: 20
    
  timeouts:
    analysis: 300
    remediation: 600
    approval: 1800
    
  auto_remediation:
    enabled: true
    confidence_threshold: 0.7
    max_auto_approvals_per_hour: 100
    
  logging:
    level: "WARNING"
    
  performance:
    cache_ttl_minutes: 5
    batch_size: 50
    
  high_availability:
    enabled: true
    health_check_interval: 30
```

## Security Configuration

### Access Control

```yaml
security:
  # IAM settings
  service_account: "orchestrator@project.iam.gserviceaccount.com"
  
  # Firestore security
  firestore:
    encrypt_at_rest: true
    audit_writes: true
    
  # Pub/Sub security
  pubsub:
    enable_message_encryption: true
    validate_signatures: true
```

### Blocked Actions

```yaml
security:
  blocked_actions:
    - "delete_production_*"
    - "modify_security_group"
    - "change_iam_policy"
    - "disable_logging"
    
  require_approval_for:
    - "modify_firewall_rule"
    - "change_instance_type"
    - "update_access_policy"
```

## Monitoring Configuration

```yaml
monitoring:
  # Metrics export
  metrics:
    export_interval: 60
    exporters:
      - type: "stackdriver"
        project_id: "your-project"
      - type: "prometheus"
        endpoint: "http://prometheus:9090"
        
  # Alerting rules
  alerts:
    - name: "high_error_rate"
      condition: "error_rate > 0.1"
      window: "5m"
      severity: "critical"
      
    - name: "workflow_backup"
      condition: "pending_incidents > 50"
      window: "10m"
      severity: "warning"
```

## Best Practices

### 1. Timeout Configuration
- Set stage timeouts based on historical data
- Add 20% buffer to average completion times
- Configure escalation for critical incidents

### 2. Auto-Approval Rules
- Start with conservative rules
- Monitor auto-approval decisions
- Gradually expand based on success rate
- Always require approval for destructive actions

### 3. Performance Tuning
- Monitor cache hit rates (target > 80%)
- Adjust batch sizes based on throughput
- Use connection pooling for external services
- Implement query result caching

### 4. Error Recovery
- Use exponential backoff for transient errors
- Implement circuit breakers for external dependencies
- Configure different strategies per error type
- Monitor error rates and adjust thresholds

### 5. Resource Management
- Set concurrent incident limits based on resources
- Monitor memory usage with large caches
- Implement graceful degradation
- Use rate limiting to prevent overload

## Configuration Validation

Use the configuration validator before deployment:

```python
from src.orchestrator_agent.config_validator import validate_config

config = load_config("orchestrator_config.yaml")
errors = validate_config(config)

if errors:
    for error in errors:
        print(f"Configuration error: {error}")
else:
    print("Configuration is valid")
```

## Dynamic Configuration Updates

Some settings can be updated without restart:

```python
# Update auto-approval setting
orchestrator.update_config("auto_remediation.enabled", False)

# Update timeout
orchestrator.update_config("timeouts.analysis", 600)

# Add new approval rule
new_rule = {
    "rule_id": "custom_rule",
    "name": "Custom approval rule",
    # ... rule details
}
orchestrator.add_approval_rule(new_rule)
```

## Troubleshooting Configuration Issues

### Common Issues

1. **Incidents timing out frequently**
   - Increase stage-specific timeouts
   - Check if analysis/remediation agents are healthy
   - Review logs for bottlenecks

2. **Auto-approval not working**
   - Verify auto_remediation.enabled = true
   - Check rule conditions match incidents
   - Review confidence thresholds

3. **Poor performance**
   - Increase cache sizes
   - Enable batching
   - Reduce concurrent incident limit

4. **High error rates**
   - Check circuit breaker settings
   - Review retry configurations
   - Verify external service health

For more information, see the main [Orchestration Agent Documentation](README.md).
