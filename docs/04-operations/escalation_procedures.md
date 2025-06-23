# SentinelOps Escalation Procedures

## Alert Severity Levels

### CRITICAL
- **Response Time**: Immediate
- **Notification Channels**: PagerDuty, SMS, Email, Slack
- **Escalation Timeline**:
  1. 0 minutes: On-call engineer (PagerDuty)
  2. 5 minutes: Team lead if not acknowledged
  3. 15 minutes: Engineering manager
  4. 30 minutes: VP of Engineering/CTO

### ERROR
- **Response Time**: Within 15 minutes
- **Notification Channels**: Email, Slack
- **Escalation Timeline**:
  1. 0 minutes: Security team email
  2. 30 minutes: Team lead
  3. 60 minutes: Engineering manager

### WARNING
- **Response Time**: Within 1 hour
- **Notification Channels**: Slack
- **Escalation Timeline**:
  1. 0 minutes: Slack notification
  2. 2 hours: Team lead if not acknowledged

## Incident Types

### Security Breach
1. Immediate: Alert Security Team and CISO
2. Isolate affected systems
3. Preserve evidence
4. Begin forensic analysis
5. Notify legal team if data breach suspected

### Service Outage
1. Check Cloud Run service status
2. Review recent deployments
3. Check for quota or resource issues
4. Initiate rollback if needed

### Performance Degradation
1. Check system resource utilization
2. Review traffic patterns
3. Scale resources if needed
4. Investigate root cause

## Contact Information

- On-Call: oncall@sentinelops.com
- Security Team: security@sentinelops.com
- Engineering Manager: eng-manager@sentinelops.com
- CTO: cto@sentinelops.com

## Tools and Resources

- Monitoring Dashboard: https://console.cloud.google.com/monitoring?project=your-gcp-project-id
- Logs Viewer: https://console.cloud.google.com/logs?project=your-gcp-project-id
- PagerDuty: https://sentinelops.pagerduty.com
- Runbooks: /docs/runbooks/
