# SentinelOps Monitoring Setup

This directory contains scripts and configurations for the enhanced SentinelOps monitoring and logging infrastructure.

## Overview

The `setup_monitoring.py` script provides comprehensive monitoring, logging, and alerting setup for SentinelOps on Google Cloud Platform, including:

### 1. Cloud Logging Setup
- **Log Sinks**: Routes logs to different destinations based on severity and type
  - Security logs → Dedicated security log bucket
  - Audit logs → BigQuery for compliance and analysis
  - Performance metrics → Cloud Storage for archival
  - Critical alerts → Pub/Sub for immediate processing
  - All logs → Long-term storage in Cloud Storage

- **Log Retention Policies**:
  - Default logs: 30 days
  - Security logs: 365 days (1 year)
  - Audit logs: 2,555 days (7 years for compliance)
  - Performance logs: 90 days
  - Debug logs: 7 days

- **BigQuery Datasets**:
  - `sentinelops_audit_logs`: Audit trail for compliance
  - `sentinelops_security_events`: Security incidents and events
  - `sentinelops_compliance`: Compliance check results

### 2. Cloud Monitoring Setup
- **Custom Metrics**: 10 log-based metrics tracking:
  - Security incident counts
  - Remediation success rates
  - Threat detection latency
  - API errors by type
  - Agent performance scores
  - Attack sources and patterns
  - Data processing volumes
  - False positive rates
  - Compliance check results

- **Dashboards**: 7 comprehensive dashboards
  - SentinelOps Security Overview
  - Agent Performance Monitoring
  - Remediation Actions Tracking
  - Security Events Analysis
  - System Health Monitoring
  - Cost Monitoring and Optimization

- **Uptime Checks**: Health monitoring for critical services
  - Orchestrator health check
  - Detection agent health check

### 3. Alerting Configuration
- **Alert Policies**: 10 policies covering:
  - Critical: Service down, security breaches
  - Error: High error rates, remediation failures
  - Warning: Performance degradation, resource utilization, quota limits

- **Notification Channels**:
  - Email (Security Team, On-Call)
  - SMS (Critical alerts)
  - Slack (Team notifications)
  - PagerDuty (Incident management)

- **Escalation Procedures**:
  - Critical: Immediate → Team Lead (5m) → Manager (15m) → VP/CTO (30m)
  - Error: Security Team → Team Lead (30m) → Manager (60m)
  - Warning: Slack → Team Lead (2h)

### 4. Additional Features
- **Error Reporting**: Automated error grouping and tracking
- **Log Views**: Pre-configured views for common queries
- **Monitoring Scripts**: Utilities for querying metrics and testing alerts
- **Escalation Documentation**: Clear procedures for incident response

## Usage

### Running the Setup

```bash
# Ensure you have the required dependencies
pip install -r requirements.txt

# Set up your Google Cloud project
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Run the setup script
python scripts/setup_monitoring.py
```

### Post-Setup Steps

1. **Update Notification Channels**:
   - Replace placeholder values in notification channels:
     - SMS phone numbers
     - Slack webhook URLs
     - PagerDuty service keys

2. **Apply Log Retention Policies**:
   ```bash
   ./scripts/apply_log_retention.sh
   ```

3. **Test Alert Policies**:
   ```bash
   ./scripts/monitoring/test_alerts.sh
   ```

4. **Query Metrics**:
   ```bash
   python scripts/monitoring/query_metrics.py
   ```

## Configuration Files

- `config/log_retention.yaml`: Log retention policy configuration
- `config/error_reporting.yaml`: Error reporting and grouping rules
- `docs/operations/escalation_procedures.md`: Detailed escalation procedures

## Monitoring Links

After setup, access your monitoring infrastructure at:
- Monitoring Dashboard: https://console.cloud.google.com/monitoring
- Logs Viewer: https://console.cloud.google.com/logs
- Error Reporting: https://console.cloud.google.com/errors
- BigQuery: https://console.cloud.google.com/bigquery

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure your service account has:
   - Monitoring Admin
   - Logging Admin
   - BigQuery Admin
   - Storage Admin

2. **Notification Channel Failures**: Verify:
   - Valid email addresses
   - Correct webhook URLs
   - Active phone numbers for SMS

3. **BigQuery Dataset Issues**: Check:
   - Billing is enabled
   - BigQuery API is enabled
   - Sufficient quota available

## Maintenance

- Review and update alert thresholds monthly
- Test escalation procedures quarterly
- Audit log retention compliance annually
- Monitor storage costs for long-term retention
