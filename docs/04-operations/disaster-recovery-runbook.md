# SentinelOps Disaster Recovery Runbook

## Overview
This runbook provides step-by-step procedures for recovering SentinelOps in various failure scenarios.

**Project ID**: your-gcp-project-id

## Quick Links
- [GCP Console](https://console.cloud.google.com/home/dashboard?project=your-gcp-project-id)
- [Cloud Run Services](https://console.cloud.google.com/run?project=your-gcp-project-id)
- [Firestore Console](https://console.cloud.google.com/firestore/data?project=your-gcp-project-id)
- [Secret Manager](https://console.cloud.google.com/security/secret-manager?project=your-gcp-project-id)

## Failure Scenarios

### 1. Complete System Failure
**Symptoms**: All services down, no response from any agent

**Recovery Steps**:
1. Run master restore script:
   ```bash
   ./scripts/master_restore.sh
   ```
2. Select option 1 (Full system restore)
3. Follow prompts to select appropriate backups
4. Verify all services are running:
   ```bash
   ./scripts/verify_all_services.sh
   ```

### 2. Firestore Data Corruption
**Symptoms**: Agents running but data inconsistent or missing

**Recovery Steps**:
1. Stop all agent services to prevent further corruption
2. List available Firestore backups:
   ```bash
   gsutil ls gs://your-gcp-project-id-firestore-backups/firestore_backup/
   ```
3. Restore from most recent good backup:
   ```bash
   ./scripts/restore_firestore.sh gs://your-gcp-project-id-firestore-backups/firestore_backup/TIMESTAMP
   ```
4. Restart agent services
5. Verify data integrity

### 3. Single Agent Failure
**Symptoms**: Specific agent not responding or erroring

**Recovery Steps**:
1. Check agent logs:
   ```bash
   gcloud run services logs read sentinelops-AGENT --limit=100
   ```
2. Redeploy the affected agent:
   ```bash
   ./scripts/deploy_AGENT_only.sh
   ```
3. If issue persists, check service account permissions
4. Verify agent health endpoint

### 4. Configuration Drift
**Symptoms**: Unexpected behavior, missing features

**Recovery Steps**:
1. List configuration backups:
   ```bash
   gsutil ls gs://your-gcp-project-id-config-backups/config_backup/
   ```
2. Compare current config with backup:
   ```bash
   # Download backup to temp location
   gsutil cp gs://your-gcp-project-id-config-backups/config_backup/TIMESTAMP/metadata.json /tmp/
   ```
3. Restore configuration:
   ```bash
   ./scripts/restore_configuration.sh TIMESTAMP
   ```
4. Redeploy affected services

### 5. Secret/Credential Issues
**Symptoms**: Authentication failures, API errors

**Recovery Steps**:
1. Access Secret Manager console
2. Check secret versions and access logs
3. Recreate affected secrets:
   - `gemini-api-key`: Get from Google AI Studio
   - `slack-webhook-url`: Get from Slack app settings
   - Service account keys: Regenerate in IAM console
4. Update agent environment variables if needed
5. Restart affected services

## Recovery Verification Checklist

After any recovery procedure, verify:

- [ ] All Cloud Run services show "✓" status
- [ ] Health endpoints respond with 200 OK:
  ```bash
  for agent in detection analysis remediation communication orchestrator; do
    echo "Checking $agent..."
    curl https://sentinelops-$agent-y7wdald4ea-uc.a.run.app/health
  done
  ```
- [ ] Firestore collections are accessible
- [ ] Recent incidents are visible (if applicable)
- [ ] Pub/Sub messages are flowing
- [ ] Monitoring dashboards show normal metrics

## Preventive Measures

### Daily Tasks
- Monitor backup job success
- Check service health metrics
- Review error logs

### Weekly Tasks
- Test manual backup procedures
- Verify configuration backup
- Review security alerts

### Monthly Tasks
- Perform restoration drill
- Update this runbook
- Review and rotate credentials

## Emergency Contacts

| Role | Contact | Responsibility |
|------|---------|----------------|
| Platform Lead | On-call rotation | Infrastructure decisions |
| Security Lead | Security team | Access and credentials |
| GCP Support | Support ticket | Platform issues |

## Recovery Time Objectives

| Component | RTO Target | RPO Target |
|-----------|------------|------------|
| Agent Services | 15 minutes | Real-time |
| Firestore Data | 30 minutes | 24 hours |
| Configuration | 15 minutes | 7 days |
| Full System | 60 minutes | 24 hours |

## Post-Recovery Actions

1. **Document the incident**:
   - What failed and when
   - Recovery steps taken
   - Time to recovery
   - Root cause (if known)

2. **Update monitoring**:
   - Add alerts for the failure pattern
   - Adjust thresholds if needed

3. **Review and improve**:
   - Update procedures based on lessons learned
   - Schedule post-mortem meeting
   - Update automation where possible

## Automation Scripts

All restoration procedures can be run manually or via the master script:

```bash
# Interactive restoration
./scripts/master_restore.sh

# Specific restores
./scripts/restore_firestore.sh <backup_path>
./scripts/restore_configuration.sh <timestamp>
./scripts/deploy_all_agents.sh
```

## Testing Schedule

- **Weekly**: Health check verification
- **Monthly**: Single component restore test
- **Quarterly**: Full disaster recovery drill
- **Annually**: Complete DR plan review
