# Comprehensive Configuration Reference

This document provides a complete reference for all SentinelOps configuration options, including environment variables, ADK-specific settings, and agent configurations.

## Table of Contents
1. [Environment Variables](#environment-variables)
2. [ADK Configuration](#adk-configuration)
3. [Agent-Specific Configuration](#agent-specific-configuration)
4. [Security Configuration](#security-configuration)
5. [Integration Configuration](#integration-configuration)
6. [Performance Tuning](#performance-tuning)
7. [Configuration Files](#configuration-files)

## Environment Variables

### Core Configuration

```env
# GCP Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_REGION=us-central1
GCP_ZONE=us-central1-a

# ADK Configuration
ADK_TELEMETRY_ENABLED=true
ADK_LOG_LEVEL=INFO
ADK_TRACE_ENABLED=true
ADK_METRICS_ENABLED=true

# Vertex AI Configuration  
VERTEX_AI_MODEL=gemini-1.5-flash-002  # or gemini-1.5-pro-002
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_TEMPERATURE=0.3
VERTEX_AI_MAX_TOKENS=2048
VERTEX_AI_TIMEOUT=30

# Firestore Configuration
FIRESTORE_DATABASE=(default)
FIRESTORE_EMULATOR_HOST=localhost:8080  # For local development
```

### Deployment Configuration

```env
# Cloud Run Configuration
CLOUD_RUN_SERVICE_URL=https://orchestrator-agent-PROJECT_ID.run.app
CLOUD_RUN_REVISION=orchestrator-agent-00001-abc
PORT=8080

# Container Configuration
CONTAINER_REGISTRY=us-central1-docker.pkg.dev/PROJECT_ID/sentinelops
IMAGE_TAG=latest
```

## ADK Configuration

### ADK Agent Base Configuration

```python
# config/adk_config.py
ADK_CONFIG = {
    "telemetry": {
        "enabled": True,
        "export_interval": 60,  # seconds
        "batch_size": 100,
        "exporters": ["cloud_trace", "cloud_monitoring"]
    },
    "transfer": {
        "timeout": 300,  # seconds
        "retry_count": 3,
        "retry_delay": 5,  # seconds
        "circuit_breaker": {
            "enabled": True,
            "failure_threshold": 5,
            "recovery_timeout": 60
        }
    },
    "tools": {
        "validation": "strict",
        "timeout_default": 30,
        "parallel_execution": True,
        "max_parallel": 10
    },
    "context": {
        "max_size_mb": 10,
        "compression": True,
        "encryption": True
    }
}
```

### ADK Session Configuration

```yaml
# config/adk_sessions.yaml
session_config:
  storage_backend: firestore
  session_timeout: 3600  # 1 hour
  max_sessions_per_user: 10
  cleanup_interval: 300  # 5 minutes
  
  persistence:
    enabled: true
    collection: adk_sessions
    ttl_days: 7
```

## Agent-Specific Configuration

### Detection Agent

```yaml
# config/detection_agent.yaml
detection_agent:
  # Monitoring Configuration
  monitoring:
    poll_interval: 60  # seconds
    lookback_minutes: 10
    max_events_per_poll: 1000
    
  # BigQuery Configuration
  bigquery:
    dataset: sentinelops_logs
    table_prefix: security_events_
    query_timeout: 300
    max_results: 10000
    
  # Detection Rules
  rules:
    refresh_interval: 300  # 5 minutes
    cache_enabled: true
    parallel_evaluation: true
    max_parallel_rules: 20
    
  # Event Correlation
  correlation:
    window_minutes: 30
    max_events_per_incident: 100
    deduplication_enabled: true
    
  # Performance
  performance:
    batch_size: 100
    worker_threads: 4
    memory_limit_mb: 1024
```

### Analysis Agent

```yaml
# config/analysis_agent.yaml
analysis_agent:
  # Gemini Configuration
  gemini:
    model: gemini-1.5-pro
    temperature: 0.3
    max_tokens: 4096
    timeout: 60
    
  # Analysis Settings
  analysis:
    max_context_events: 50
    include_historical: true
    historical_days: 30
    
  # Caching Configuration
  caching:
    enabled: true
    ttl_seconds: 3600  # 1 hour
    max_cache_size_mb: 500
    similarity_threshold: 0.85
    
  # Batch Processing
  batch:
    enabled: true
    max_batch_size: 10
    batch_timeout: 30
    
  # Performance Optimization
  performance:
    parallel_analysis: true
    max_concurrent: 5
    rate_limit_per_minute: 60
```

### Remediation Agent

```yaml
# config/remediation_agent.yaml
remediation_agent:
  # Safety Controls
  safety:
    dry_run_default: true
    approval_required: true
    approval_timeout: 600  # 10 minutes
    rollback_enabled: true
    rollback_retention_days: 7
    
  # Action Limits
  limits:
    max_parallel_actions: 10
    rate_limit_per_minute: 20
    action_timeout: 300  # 5 minutes
    
  # Specific Action Configuration
  actions:
    block_ip:
      max_duration_hours: 168  # 7 days
      default_duration_hours: 24
      auto_unblock: true
      
    isolate_vm:
      snapshot_before: true
      preserve_logs: true
      notification_required: true
      
    revoke_credentials:
      immediate: true
      audit_log: true
      notify_owner: true
      
  # Rollback Configuration
  rollback:
    auto_rollback_on_error: true
    manual_approval_required: false
    max_rollback_age_days: 7
```

### Communication Agent

```yaml
# config/communication_agent.yaml
communication_agent:
  # Channel Configuration
  channels:
    slack:
      enabled: true
      rate_limit: 10  # per minute
      retry_count: 3
      timeout: 30
      
    email:
      enabled: true
      provider: sendgrid  # or smtp
      rate_limit: 100  # per hour
      batch_enabled: true
      
    sms:
      enabled: false
      provider: twilio
      critical_only: true
      rate_limit: 5  # per hour
      
  # Template Configuration
  templates:
    path: /templates/notifications
    cache_enabled: true
    variables_validation: strict
    
  # Notification Rules
  rules:
    immediate_severity: [CRITICAL, HIGH]
    batch_severity: [MEDIUM, LOW]
    batch_window_minutes: 5
    max_batch_size: 50
    
  # Escalation
  escalation:
    enabled: true
    intervals: [300, 900, 1800]  # 5, 15, 30 minutes
    max_escalations: 3
```

### Orchestrator Agent

```yaml
# config/orchestrator_agent.yaml
orchestrator_agent:
  # Workflow Configuration
  workflow:
    max_concurrent_incidents: 100
    incident_timeout: 3600  # 1 hour
    state_check_interval: 30  # seconds
    
  # Agent Management
  agents:
    health_check_interval: 60
    unhealthy_threshold: 3
    restart_unhealthy: true
    
  # State Management
  state:
    backend: firestore
    collection: incident_states
    retention_days: 90
    
  # Routing Rules
  routing:
    detection_to_analysis: always
    analysis_to_remediation: conditional
    remediation_to_communication: always
    
  # Performance
  performance:
    parallel_workflows: true
    max_parallel: 50
    queue_size: 1000
```

## Security Configuration

### Authentication & Authorization

```yaml
# config/security.yaml
security:
  # Service Account Configuration
  service_accounts:
    rotation_days: 90
    key_algorithm: RSA_2048
    
  # API Security
  api:
    auth_required: true
    auth_methods: [jwt, api_key]
    rate_limiting: true
    cors_enabled: false
    
  # Encryption
  encryption:
    at_rest: true
    in_transit: true
    key_management: cloud_kms
    
  # Audit Logging
  audit:
    enabled: true
    log_reads: false
    log_writes: true
    retention_days: 365
```

### Secret Management

```env
# Secret Manager References
SLACK_WEBHOOK_URL=sm://slack-webhook-url
SMTP_PASSWORD=sm://smtp-password
TWILIO_AUTH_TOKEN=sm://twilio-auth-token
SENDGRID_API_KEY=sm://sendgrid-api-key
```

## Integration Configuration

### Slack Integration

```yaml
# config/integrations/slack.yaml
slack:
  webhook_url: ${SLACK_WEBHOOK_URL}
  channels:
    critical: "#security-critical"
    high: "#security-alerts"
    medium: "#security-notifications"
    low: "#security-logs"
  formatting:
    use_blocks: true
    include_actions: true
    thread_replies: true
  retry:
    max_attempts: 3
    backoff_multiplier: 2
```

### Email Configuration

```yaml
# config/integrations/email.yaml
email:
  provider: sendgrid
  from_address: sentinelops@company.com
  from_name: SentinelOps Security
  
  sendgrid:
    api_key: ${SENDGRID_API_KEY}
    sandbox_mode: false
    
  smtp:
    host: smtp.gmail.com
    port: 587
    username: ${SMTP_USERNAME}
    password: ${SMTP_PASSWORD}
    use_tls: true
    
  templates:
    incident_alert: sg-template-123
    daily_summary: sg-template-456
```

### Monitoring Integration

```yaml
# config/integrations/monitoring.yaml
monitoring:
  # Prometheus Metrics
  prometheus:
    enabled: true
    port: 9090
    path: /metrics
    
  # Cloud Monitoring
  cloud_monitoring:
    enabled: true
    export_interval: 60
    resource_type: cloud_run_revision
    
  # Custom Metrics
  custom_metrics:
    - name: incidents_detected
      type: counter
      labels: [severity, agent]
    - name: remediation_duration
      type: histogram
      buckets: [1, 5, 10, 30, 60, 300]
```

## Performance Tuning

### Resource Limits

```yaml
# config/resources.yaml
resources:
  # CPU and Memory per Agent
  detection_agent:
    cpu: 1.0
    memory: 1Gi
    
  analysis_agent:
    cpu: 2.0
    memory: 4Gi
    
  remediation_agent:
    cpu: 1.0
    memory: 2Gi
    
  communication_agent:
    cpu: 0.5
    memory: 1Gi
    
  orchestrator_agent:
    cpu: 2.0
    memory: 2Gi
```

### Autoscaling Configuration

```yaml
# config/autoscaling.yaml
autoscaling:
  detection_agent:
    min_instances: 1
    max_instances: 20
    target_cpu_utilization: 70
    scale_down_delay: 300
    
  analysis_agent:
    min_instances: 1
    max_instances: 10
    target_cpu_utilization: 60
    concurrent_requests: 50
    
  remediation_agent:
    min_instances: 0  # Scale to zero
    max_instances: 5
    target_cpu_utilization: 50
    
  communication_agent:
    min_instances: 1
    max_instances: 10
    target_request_latency: 500  # ms
```

## Configuration Files

### Main Configuration Structure

```
config/
├── adk_config.py           # ADK framework settings
├── agents.yaml             # Agent registry and URLs
├── security.yaml           # Security settings
├── resources.yaml          # Resource allocations
├── autoscaling.yaml        # Scaling policies
├── agents/
│   ├── detection.yaml      # Detection agent config
│   ├── analysis.yaml       # Analysis agent config
│   ├── remediation.yaml    # Remediation agent config
│   ├── communication.yaml  # Communication agent config
│   └── orchestrator.yaml   # Orchestrator agent config
├── integrations/
│   ├── slack.yaml         # Slack configuration
│   ├── email.yaml         # Email configuration
│   ├── monitoring.yaml    # Monitoring configuration
│   └── webhooks.yaml      # Webhook endpoints
└── environments/
    ├── development.yaml   # Dev overrides
    ├── staging.yaml       # Staging overrides
    └── production.yaml    # Production overrides
```

### Loading Configuration

```python
# src/common/config_loader.py
import os
import yaml
from typing import Dict, Any

class ConfigLoader:
    def __init__(self, env: str = None):
        self.env = env or os.getenv("ENVIRONMENT", "production")
        self.config_dir = os.getenv("CONFIG_DIR", "/config")
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration with environment overrides."""
        # Load base configuration
        config = self._load_base_config()
        
        # Apply environment-specific overrides
        env_config = self._load_env_config()
        config = self._deep_merge(config, env_config)
        
        # Apply environment variable overrides
        config = self._apply_env_vars(config)
        
        return config
```

## Best Practices

1. **Environment Variables**
   - Never commit sensitive values
   - Use Secret Manager for production
   - Document all required variables

2. **Configuration Management**
   - Version control all config files
   - Use environment-specific overrides
   - Validate configuration on startup

3. **Performance Settings**
   - Start conservative, tune based on metrics
   - Monitor resource usage
   - Set appropriate timeouts

4. **Security Configuration**
   - Follow least privilege principle
   - Rotate credentials regularly
   - Enable audit logging

5. **Testing Configuration**
   - Maintain separate test configs
   - Use emulators for local development
   - Test configuration changes in staging

---

*This comprehensive configuration reference ensures consistent and secure deployment of SentinelOps across all environments.*