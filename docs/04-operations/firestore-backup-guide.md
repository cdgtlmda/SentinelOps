# Firestore Backup and Restore Guide

## Overview
This guide describes the Firestore backup and restore procedures for SentinelOps.

## Backup Configuration

### Backup Storage
- **Bucket**: `gs://your-gcp-project-id-firestore-backups`
- **Retention**: 30 days (automatic deletion)
- **Schedule**: Daily at 2:00 AM UTC

### Backup Types

#### 1. Automated Daily Backups
- Runs automatically via Cloud Scheduler
- Stores backups with timestamp: `firestore_backup/YYYYMMDD_HHMMSS`
- Managed by Cloud Function: `firestore-backup`

#### 2. Manual Backups
Run the backup script:
```bash
./scripts/backup_firestore.sh
```

## Restore Procedures

### Restore from Backup
1. List available backups:
   ```bash
   gsutil ls gs://your-gcp-project-id-firestore-backups/firestore_backup/
   ```

2. Run restore script with backup path:
   ```bash
   ./scripts/restore_firestore.sh gs://path/to/backup
   ```

### Important Notes
- Restores overwrite existing data
- Backup/restore operations may take several minutes
- Monitor operations at: https://console.cloud.google.com/firestore/import-export

## Backup Monitoring

### Check Backup Status
```bash
# List recent backups
gsutil ls -l gs://your-gcp-project-id-firestore-backups/firestore_backup/ | tail -10

# Check Cloud Scheduler job
gcloud scheduler jobs describe firestore-daily-backup --location us-central1
```

### Backup Alerts
Configure alerts in Cloud Monitoring for:
- Failed backup operations
- Missing daily backups
- Storage quota warnings

## Disaster Recovery

### Recovery Time Objective (RTO)
- **Target**: < 1 hour
- **Process**: Identify backup → Run restore → Verify data

### Recovery Point Objective (RPO)
- **Target**: < 24 hours (daily backups)
- **Critical data**: Consider more frequent backups

## Testing

### Backup Testing Checklist
- [ ] Perform manual backup
- [ ] Verify backup contents
- [ ] Test restore to dev environment
- [ ] Validate restored data
- [ ] Document recovery time

### Recommended Testing Schedule
- Monthly: Test manual backup/restore
- Quarterly: Full DR drill
- Annually: Review and update procedures
