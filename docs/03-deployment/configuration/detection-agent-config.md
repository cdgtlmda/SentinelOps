# Detection Agent Configuration Guide

This guide covers all configuration options for the Detection Agent, including the new features added in Section 3 of the BigQuery Integration.

## Complete Configuration Example

```yaml
agents:
  detection:
    enabled_rules:
      - suspicious_login
      - privilege_escalation
      - vpc_suspicious_port_scan
      - firewall_rule_modification

    scan_interval_seconds: 60
    initial_lookback_hours: 1
    correlation_window_minutes: 60

    # Pagination settings
    query_page_size: 1000
    max_results_per_query: 10000
    query_timeout_ms: 30000
    max_events_per_rule: 5000

    # Resource filtering
    resource_filters:
      included_projects:
        - production-project
        - staging-project
      excluded_projects:
        - test-project
        - dev-project
      included_zones:
        - us-central1-a
        - us-central1-b
        - europe-west1-b
      excluded_zones:
        - asia-east1-a
      included_regions:
        - us-central1
        - europe-west1
      included_resource_types:
        - gce_instance
        - gcs_bucket
        - bigquery_dataset
      excluded_resource_types:
        - logging_sink
      included_vms:
        - production-web-server        - production-db-server
      excluded_vms:
        - test-vm
        - debug-instance
      included_patterns:
        - ".*prod.*"
        - ".*critical.*"
      excluded_patterns:
        - ".*test.*"
        - ".*temp.*"
      included_labels:
        environment: production
        critical: "true"
      excluded_labels:
        temporary: "true"
        testing: "true"

    # BigQuery quota management
    bigquery_quotas:
      daily_bytes_limit: 1099511627776  # 1TB
      daily_query_limit: 10000
      daily_slot_ms_limit: 86400000  # 24 hours
      max_bytes_per_query: 10737418240  # 10GB
      max_slot_ms_per_query: 600000  # 10 minutes
      queries_per_minute: 100
      bytes_per_minute: 107374182400  # 100GB
      enable_backoff: true
      backoff_multiplier: 2
      max_backoff_seconds: 300
```

## Feature Descriptions

### VPC Flow Logs Queries
The detection agent now includes specialized queries for analyzing VPC flow logs:
- **Suspicious Port Scanning**: Detects sources scanning multiple ports
- **Unusual Traffic Volume**: Identifies potential data exfiltration via high traffic volumes
- **Blocked Traffic Attempts**: Finds repeated blocked connection attempts
- **External IP Communication**: Monitors communication with external or suspicious IPs
- **Lateral Movement**: Detects internal network movement patterns

### Firewall Logs Queries
New firewall-specific detection rules:
- **Firewall Rule Modifications**: Tracks changes to firewall configurations
- **Overly Permissive Rules**: Alerts on rules allowing 0.0.0.0/0 traffic
- **Denied Traffic Spikes**: Detects sudden increases in blocked traffic
- **Firewall Bypass Attempts**: Identifies patterns suggesting bypass attempts

### Resource Filtering
Resource filtering allows you to:
- **Include/Exclude by Project**: Focus on specific GCP projects
- **Zone/Region Filtering**: Limit detection to specific geographic locations
- **Resource Type Filtering**: Monitor only specific resource types
- **VM Filtering**: Target specific virtual machines
- **Pattern Matching**: Use regex patterns for flexible resource matching
- **Label-based Filtering**: Filter resources based on their labels

### Quota Management
Prevents excessive BigQuery usage and costs:
- **Daily Limits**: Enforce daily quotas for bytes processed and queries
- **Rate Limiting**: Control queries per minute to avoid throttling
- **Per-Query Limits**: Prevent individual queries from consuming too many resources
- **Automatic Backoff**: Exponentially back off when limits are reached
- **Cost Estimation**: Track estimated costs based on data processed

## Best Practices

1. **Start Conservative**: Begin with strict resource filters and gradually expand
2. **Monitor Quotas**: Regularly check quota usage to avoid surprises
3. **Test Rules**: Use test projects to validate new detection rules
4. **Incremental Rollout**: Enable new rules one at a time in production
5. **Regular Review**: Periodically review and update filters based on your environment

## Troubleshooting

### High Quota Usage
- Review enabled rules and their query efficiency
- Increase filtering to reduce data scanned
- Consider increasing scan intervals for non-critical rules

### Missing Detections
- Check resource filters aren't too restrictive
- Verify the correct log types are being scanned
- Ensure BigQuery datasets have proper permissions

### Performance Issues
- Reduce page size for better memory usage
- Lower max_events_per_rule if processing is slow
- Enable query result caching where appropriate
