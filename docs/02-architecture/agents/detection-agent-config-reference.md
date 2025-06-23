# Detection Agent Configuration Reference

This document provides a comprehensive reference for all configuration options available in the SentinelOps Detection Agent.

## Complete Configuration Example

```yaml
agents:
  detection:
    # Core Agent Settings
    enabled_rules:
      - suspicious_login
      - privilege_escalation
      - data_exfiltration
      - vpc_suspicious_port_scan
      - firewall_rule_modification
      - resource_modification

    scan_interval_seconds: 60
    initial_lookback_hours: 1
    correlation_window_minutes: 60
    deduplication_threshold: 0.8
    deduplication_window_hours: 24

    # Query Optimization Settings
    query_optimization:
      enabled: true
      enable_time_partitioning: true
      max_scan_days: 7
      default_limit: 10000
      enable_sampling: true
      sample_percentage: 10
      enable_column_pruning: true
      required_columns:
        - timestamp
        - actor
        - source_ip
        - resource_name
        - method_name
        - status_code

    # Query Cache Configuration
    query_cache:
      enabled: true
      max_entries: 1000
      default_ttl_minutes: 60
      min_hit_count_for_extension: 3

    # Cache Invalidation Settings
    cache_invalidation:
      enabled: true
      invalidate_on_detection: true
      invalidate_on_rule_change: true
      scheduled_interval_hours: 6

    # Interim Results Storage
    interim_storage:
      enabled: true
      storage_path: "/tmp/sentinelops/interim"
      max_results: 10000
      default_ttl_hours: 24

    # Performance Tuning
    performance:
      max_concurrent_queries: 5
      query_timeout_seconds: 300
      max_memory_usage_mb: 2048
      max_cpu_percent: 80
      event_batch_size: 100
      max_events_in_memory: 10000
      enable_streaming: true
      min_scan_interval_seconds: 30
      max_scan_interval_seconds: 3600
      adaptive_intervals: true
      query_priority: "INTERACTIVE"

    # BigQuery Settings
    bigquery:
      project_id: "your-project-id"
      datasets:
        audit_logs: "audit_dataset"
        vpc_flow_logs: "vpc_flow_dataset"
        firewall_logs: "firewall_dataset"
      connection_pool_size: 10
      retry_attempts: 3
      retry_delay_seconds: 5

    # Resource Filtering
    resource_filters:
      included_projects:
        - "production-project"
        - "staging-project"
      excluded_projects:
        - "test-project"
        - "dev-project"
      included_zones:
        - "us-central1-a"
        - "us-central1-b"
        - "europe-west1-b"
      excluded_zones:
        - "asia-east1-a"
      included_regions:
        - "us-central1"
        - "europe-west1"
      included_resource_types:
        - "gce_instance"
        - "gcs_bucket"
        - "bigquery_dataset"
      excluded_resource_types:
        - "logging_sink"
      included_patterns:
        - ".*prod.*"
        - ".*critical.*"
      excluded_patterns:
        - ".*test.*"
        - ".*temp.*"
      included_labels:
        environment: "production"
        critical: "true"
      excluded_labels:
        temporary: "true"
        testing: "true"

    # Quota Management
    quota_management:
      enabled: true
      daily_bytes_limit: 1099511627776  # 1TB
      daily_query_limit: 10000
      queries_per_minute: 100
      bytes_per_minute: 107374182400  # 100GB
      enable_backoff: true
      backoff_multiplier: 2.0
      max_backoff_seconds: 300
      cost_estimation: true
      alert_threshold_percent: 80

    # Monitoring and Metrics
    monitoring:
      enabled: true
      retention_hours: 24
      resource_sample_interval: 60
      metrics_export:
        enabled: true
        endpoint: "http://prometheus:9090"
        push_interval_seconds: 30

    # Rule-Specific Configuration
    rule_specific_config:
      suspicious_login:
        max_attempts_threshold: 10
        time_window_minutes: 15
        excluded_source_ranges:
          - "10.0.0.0/8"
          - "172.16.0.0/12"
          - "192.168.0.0/16"
        suspicious_user_agents:
          - "curl"
          - "wget"
          - "python-requests"

      privilege_escalation:
        sensitive_roles:
          - "roles/owner"
          - "roles/editor"
          - "roles/iam.serviceAccountAdmin"
          - "roles/iam.serviceAccountKeyAdmin"
        bulk_threshold: 5
        cross_project_threshold: 3
        excluded_actors:
          - "automation@your-project.iam.gserviceaccount.com"

      data_exfiltration:
        volume_threshold_gb: 10
        file_count_threshold: 1000
        time_window_hours: 1
        excluded_buckets:
          - "logs-*"
          - "temp-*"
        suspicious_extensions:
          - ".sql"
          - ".db"
          - ".csv"
          - ".json"

      vpc_suspicious_port_scan:
        port_scan_threshold: 50
        time_window_minutes: 10
        excluded_internal_ranges:
          - "10.0.0.0/8"
          - "172.16.0.0/12"
        monitored_ports:
          - 22
          - 80
          - 443
          - 3389
          - 5432
          - 3306

      firewall_rule_modification:
        critical_rules:
          - "deny-all"
          - "allow-internal"
        excluded_actors:
          - "terraform@your-project.iam.gserviceaccount.com"
        monitor_rule_deletions: true
        monitor_priority_changes: true

      resource_modification:
        critical_resources:
          - "production-database"
          - "secrets-storage"
        excluded_modifications:
          - "labels.update"
          - "metadata.update"
        monitor_deletions: true
        monitor_permission_changes: true

# Global Configuration
gcp:
  project_id: "your-project-id"
  credentials_path: "/path/to/service-account-key.json"
  default_region: "us-central1"
  default_zone: "us-central1-a"

# Pub/Sub Configuration for Agent Communication
pubsub:
  orchestration_topic: "orchestration-commands"
  detection_results_topic: "detection-results"
  custom_queries_topic: "custom-queries"
  subscription_prefix: "detection-agent"

# Logging Configuration
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_path: "/var/log/sentinelops/detection-agent.log"
  max_file_size_mb: 100
  backup_count: 5
  console_logging: true
```

## Configuration Sections

### Core Agent Settings

#### `enabled_rules`
**Type:** List of strings
**Default:** `[]`
**Description:** List of detection rule IDs to enable. Only enabled rules will be executed during scan cycles.

**Available Rules:**
- `suspicious_login` - Detects unusual login patterns
- `privilege_escalation` - Monitors privilege escalation attempts
- `data_exfiltration` - Identifies potential data exfiltration
- `vpc_suspicious_port_scan` - Detects port scanning activities
- `firewall_rule_modification` - Monitors firewall rule changes
- `resource_modification` - Tracks critical resource modifications

#### `scan_interval_seconds`
**Type:** Integer
**Default:** `60`
**Range:** `30` - `3600`
**Description:** Interval between scan cycles in seconds.

#### `initial_lookback_hours`
**Type:** Integer
**Default:** `1`
**Range:** `1` - `24`
**Description:** How far back to look for events on agent startup.

#### `correlation_window_minutes`
**Type:** Integer
**Default:** `60`
**Range:** `5` - `240`
**Description:** Time window for correlating related security events.

#### `deduplication_threshold`
**Type:** Float
**Default:** `0.8`
**Range:** `0.0` - `1.0`
**Description:** Similarity threshold for incident deduplication (0.0 = no deduplication, 1.0 = exact match only).

#### `deduplication_window_hours`
**Type:** Integer
**Default:** `24`
**Range:** `1` - `168`
**Description:** Time window for checking duplicate incidents.

### Query Optimization Settings

#### `query_optimization.enabled`
**Type:** Boolean
**Default:** `true`
**Description:** Enable/disable query optimization features.

#### `query_optimization.enable_time_partitioning`
**Type:** Boolean
**Default:** `true`
**Description:** Use BigQuery partition pruning for time-based queries.

#### `query_optimization.max_scan_days`
**Type:** Integer
**Default:** `7`
**Range:** `1` - `30`
**Description:** Maximum number of days to scan in a single query.

#### `query_optimization.default_limit`
**Type:** Integer
**Default:** `10000`
**Range:** `100` - `100000`
**Description:** Default LIMIT clause for queries without explicit limits.

#### `query_optimization.enable_sampling`
**Type:** Boolean
**Default:** `true`
**Description:** Enable query sampling for large time ranges.

#### `query_optimization.sample_percentage`
**Type:** Integer
**Default:** `10`
**Range:** `1` - `100`
**Description:** Percentage of data to sample when sampling is enabled.

#### `query_optimization.enable_column_pruning`
**Type:** Boolean
**Default:** `true`
**Description:** Replace SELECT * with specific columns to reduce data transfer.

#### `query_optimization.required_columns`
**Type:** List of strings
**Default:** `["timestamp", "actor", "source_ip", "resource_name", "method_name", "status_code"]`
**Description:** Columns to include when column pruning is enabled.

### Query Cache Configuration

#### `query_cache.enabled`
**Type:** Boolean
**Default:** `true`
**Description:** Enable/disable query result caching.

#### `query_cache.max_entries`
**Type:** Integer
**Default:** `1000`
**Range:** `100` - `10000`
**Description:** Maximum number of cached query results.

#### `query_cache.default_ttl_minutes`
**Type:** Integer
**Default:** `60`
**Range:** `5` - `1440`
**Description:** Default time-to-live for cached results in minutes.

#### `query_cache.min_hit_count_for_extension`
**Type:** Integer
**Default:** `3`
**Range:** `1` - `10`
**Description:** Minimum hit count before extending cache TTL for popular queries.

### Performance Tuning

#### `performance.max_concurrent_queries`
**Type:** Integer
**Default:** `5`
**Range:** `1` - `20`
**Description:** Maximum number of concurrent BigQuery queries.

#### `performance.query_timeout_seconds`
**Type:** Integer
**Default:** `300`
**Range:** `30` - `1800`
**Description:** Timeout for individual BigQuery queries.

#### `performance.max_memory_usage_mb`
**Type:** Integer
**Default:** `2048`
**Range:** `512` - `8192`
**Description:** Maximum memory usage for the agent process.

#### `performance.max_cpu_percent`
**Type:** Integer
**Default:** `80`
**Range:** `10` - `100`
**Description:** Maximum CPU usage percentage.

#### `performance.event_batch_size`
**Type:** Integer
**Default:** `100`
**Range:** `10` - `1000`
**Description:** Number of events to process in a single batch.

#### `performance.query_priority`
**Type:** String
**Default:** `"INTERACTIVE"`
**Options:** `"BATCH"`, `"INTERACTIVE"`
**Description:** BigQuery job priority level.

### BigQuery Settings

#### `bigquery.project_id`
**Type:** String
**Required:** Yes
**Description:** GCP project ID containing the log datasets.

#### `bigquery.datasets`
**Type:** Object
**Description:** Dataset names for different log types.

- `audit_logs` - Dataset containing Google Cloud Audit Logs
- `vpc_flow_logs` - Dataset containing VPC Flow Logs
- `firewall_logs` - Dataset containing Firewall Logs

#### `bigquery.connection_pool_size`
**Type:** Integer
**Default:** `10`
**Range:** `1` - `50`
**Description:** Size of the BigQuery client connection pool.

#### `bigquery.retry_attempts`
**Type:** Integer
**Default:** `3`
**Range:** `0` - `10`
**Description:** Number of retry attempts for failed queries.

### Resource Filtering

#### `resource_filters.included_projects`
**Type:** List of strings
**Default:** `[]`
**Description:** Only scan resources in these GCP projects. Empty list means all projects.

#### `resource_filters.excluded_projects`
**Type:** List of strings
**Default:** `[]`
**Description:** Skip scanning resources in these GCP projects.

#### `resource_filters.included_zones`
**Type:** List of strings
**Default:** `[]`
**Description:** Only scan resources in these zones.

#### `resource_filters.included_patterns`
**Type:** List of strings
**Default:** `[]`
**Description:** Regex patterns for resource names to include.

#### `resource_filters.included_labels`
**Type:** Object
**Default:** `{}`
**Description:** Only scan resources with these labels (key-value pairs).

### Quota Management

#### `quota_management.enabled`
**Type:** Boolean
**Default:** `true`
**Description:** Enable BigQuery quota monitoring and enforcement.

#### `quota_management.daily_bytes_limit`
**Type:** Integer
**Default:** `1099511627776` (1TB)
**Description:** Daily limit for bytes processed by BigQuery.

#### `quota_management.daily_query_limit`
**Type:** Integer
**Default:** `10000`
**Description:** Daily limit for number of queries.

#### `quota_management.queries_per_minute`
**Type:** Integer
**Default:** `100`
**Range:** `1` - `1000`
**Description:** Rate limit for queries per minute.

#### `quota_management.enable_backoff`
**Type:** Boolean
**Default:** `true`
**Description:** Enable exponential backoff when quotas are approached.

### Monitoring Settings

#### `monitoring.enabled`
**Type:** Boolean
**Default:** `true`
**Description:** Enable monitoring and metrics collection.

#### `monitoring.retention_hours`
**Type:** Integer
**Default:** `24`
**Range:** `1` - `168`
**Description:** How long to retain monitoring data.

#### `monitoring.resource_sample_interval`
**Type:** Integer
**Default:** `60`
**Range:** `10` - `300`
**Description:** Interval for sampling system resource usage (seconds).

## Environment Variables

The following environment variables can override configuration values:

- `SENTINELOPS_LOG_LEVEL` - Override logging level
- `SENTINELOPS_GCP_PROJECT` - Override GCP project ID
- `SENTINELOPS_BIGQUERY_TIMEOUT` - Override query timeout
- `SENTINELOPS_CACHE_ENABLED` - Enable/disable caching
- `SENTINELOPS_DEBUG_MODE` - Enable debug mode

## Configuration Validation

The agent validates configuration on startup and will log warnings for:

- Invalid value ranges
- Missing required settings
- Conflicting options
- Resource constraints

## Configuration Management

### Development Environment
```yaml
agents:
  detection:
    scan_interval_seconds: 300  # Longer intervals
    query_cache:
      enabled: false  # Disable caching for testing
    performance:
      max_concurrent_queries: 2  # Lower concurrency
```

### Production Environment
```yaml
agents:
  detection:
    scan_interval_seconds: 60  # Frequent scanning
    query_cache:
      enabled: true
      max_entries: 5000  # Larger cache
    performance:
      max_concurrent_queries: 10  # Higher concurrency
    monitoring:
      enabled: true
      retention_hours: 168  # 7 days retention
```

This configuration reference provides complete control over the Detection Agent's behavior, performance characteristics, and resource usage patterns.
