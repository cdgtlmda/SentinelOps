# SentinelOps DR Quick Reference

## 🚨 Emergency Commands

### Full System Restore
```bash
./scripts/master_restore.sh
# Select option 1
```

### Firestore Restore
```bash
# List backups
gsutil ls gs://your-gcp-project-id-firestore-backups/firestore_backup/

# Restore specific backup
./scripts/restore_firestore.sh gs://your-gcp-project-id-firestore-backups/firestore_backup/TIMESTAMP
```

### Configuration Restore
```bash
# List backups
gsutil ls gs://your-gcp-project-id-config-backups/config_backup/

# Restore specific backup
./scripts/restore_configuration.sh TIMESTAMP
```

### Redeploy Single Agent
```bash
./scripts/deploy_detection_only.sh
./scripts/deploy_analysis_only.sh
./scripts/deploy_remediation_only.sh
./scripts/deploy_communication_only.sh
./scripts/deploy_orchestrator_only.sh
```

### Redeploy All Agents
```bash
./scripts/deploy_all_agents.sh
```

### Verify Services
```bash
./scripts/verify_all_services.sh
```

## 📍 Important URLs

- **Project Console**: https://console.cloud.google.com/home/dashboard?project=your-gcp-project-id
- **Cloud Run**: https://console.cloud.google.com/run?project=your-gcp-project-id
- **Firestore**: https://console.cloud.google.com/firestore/data?project=your-gcp-project-id
- **Logs**: https://console.cloud.google.com/logs/query?project=your-gcp-project-id

## 🔑 Key Resources

| Resource | Location |
|----------|----------|
| Firestore Backups | `gs://your-gcp-project-id-firestore-backups/` |
| Config Backups | `gs://your-gcp-project-id-config-backups/` |
| Agent Images | `us-central1-docker.pkg.dev/your-gcp-project-id/sentinelops/` |
| Cloud Functions | `us-central1` region |

## ⚡ Health Check URLs

- Detection: https://sentinelops-detection-y7wdald4ea-uc.a.run.app/health
- Analysis: https://sentinelops-analysis-y7wdald4ea-uc.a.run.app/health
- Remediation: https://sentinelops-remediation-y7wdald4ea-uc.a.run.app/health
- Communication: https://sentinelops-communication-y7wdald4ea-uc.a.run.app/health
- Orchestrator: https://sentinelops-orchestrator-y7wdald4ea-uc.a.run.app/health

## 🆘 If All Else Fails

1. Check GCP service health: https://status.cloud.google.com/
2. Review quotas: Console > IAM & Admin > Quotas
3. Check billing: Console > Billing
4. Contact GCP Support
