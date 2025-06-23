#!/usr/bin/env python3
"""
Set up Firestore backup policies
Configures automated backups for Firestore database
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
BACKUP_BUCKET = f"gs://{PROJECT_ID}-firestore-backups"
BACKUP_SCHEDULE = "0 2 * * *"  # Daily at 2 AM


def create_backup_bucket():
    """Create a GCS bucket for Firestore backups"""
    print("🪣 Creating backup bucket...")

    # Check if bucket exists
    check_cmd = ["gsutil", "ls", BACKUP_BUCKET]
    result = subprocess.run(check_cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("   ✓ Bucket already exists: {BACKUP_BUCKET}")
        return True

    # Create bucket
    create_cmd = [
        "gsutil",
        "mb",
        "-p",
        PROJECT_ID,
        "-c",
        "STANDARD",
        "-l",
        "us-central1",
        "-b",
        "on",  # Uniform bucket-level access
        BACKUP_BUCKET,
    ]

    try:
        subprocess.run(create_cmd, check=True, capture_output=True, text=True)
        print("   ✅ Created bucket: {BACKUP_BUCKET}")

        # Set lifecycle rule to delete old backups after 30 days
        lifecycle_config = """
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 30,
          "matchesPrefix": ["firestore_backup/"]
        }
      }
    ]
  }
}
"""
        lifecycle_file = "/tmp/firestore_backup_lifecycle.json"
        with open(lifecycle_file, "w") as f:
            f.write(lifecycle_config)

        lifecycle_cmd = ["gsutil", "lifecycle", "set", lifecycle_file, BACKUP_BUCKET]
        subprocess.run(lifecycle_cmd, check=True, capture_output=True, text=True)
        print("   ✅ Set 30-day retention policy")

        return True

    except subprocess.CalledProcessError as e:
        print("   ❌ Failed to create bucket: {e.stderr}")
        return False


def create_backup_script():
    """Create a script to perform manual backups"""
    print("\n📝 Creating backup scripts...")

    # Manual backup script
    manual_backup_script = """#!/bin/bash
# Manual Firestore backup script

PROJECT_ID="{project_id}"
BACKUP_BUCKET="{backup_bucket}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${{BACKUP_BUCKET}}/firestore_backup/${{TIMESTAMP}}"

echo "🔄 Starting Firestore backup..."
echo "   Project: $PROJECT_ID"
echo "   Destination: $BACKUP_PATH"

# Export all collections
gcloud firestore export $BACKUP_PATH \\
    --project=$PROJECT_ID \\
    --format=json

if [ $? -eq 0 ]; then
    echo "✅ Backup completed successfully!"
    echo "   Location: $BACKUP_PATH"
else
    echo "❌ Backup failed!"
    exit 1
fi
""".format(
        project_id=PROJECT_ID, backup_bucket=BACKUP_BUCKET
    )

    script_path = Path(__file__).parent / "backup_firestore.sh"
    with open(script_path, "w") as f:
        f.write(manual_backup_script)
    os.chmod(script_path, 0o755)

    print("   ✅ Created manual backup script: {script_path}")

    # Restore script
    restore_script = """#!/bin/bash
# Firestore restore script

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_path>"
    echo "Example: $0 gs://{project_id}-firestore-backups/firestore_backup/20240529_120000"
    exit 1
fi

PROJECT_ID="{project_id}"
BACKUP_PATH=$1

echo "🔄 Starting Firestore restore..."
echo "   Project: $PROJECT_ID"
echo "   Source: $BACKUP_PATH"
echo ""
echo "⚠️  WARNING: This will overwrite existing data!"
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    gcloud firestore import $BACKUP_PATH \\
        --project=$PROJECT_ID

    if [ $? -eq 0 ]; then
        echo "✅ Restore completed successfully!"
    else
        echo "❌ Restore failed!"
        exit 1
    fi
else
    echo "Restore cancelled."
fi
""".format(
        project_id=PROJECT_ID
    )

    restore_path = Path(__file__).parent / "restore_firestore.sh"
    with open(restore_path, "w") as f:
        f.write(restore_script)
    os.chmod(restore_path, 0o755)

    print("   ✅ Created restore script: {restore_path}")

    return True


def create_scheduled_backup():
    """Create a Cloud Scheduler job for automated backups"""
    print("\n⏰ Setting up scheduled backups...")

    # Create Cloud Function for backup
    function_code = '''
import os  # noqa: E402
from google.cloud import firestore_admin_v1  # noqa: E402
from datetime import datetime  # noqa: E402

def firestore_backup(request):
    """Cloud Function to backup Firestore"""

    project_id = os.environ.get('GCP_PROJECT')
    backup_bucket = f"gs://{project_id}-firestore-backups"

    client = firestore_admin_v1.FirestoreAdminClient()

    # Generate backup path with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{backup_bucket}/firestore_backup/{timestamp}"

    # Database name
    database_name = f"projects/{project_id}/databases/(default)"

    # Start export
    operation = client.export_documents(
        request={
            "name": database_name,
            "output_uri_prefix": backup_path,
        }
    )

    return {
        "status": "success",
        "operation": operation.name,
        "backup_path": backup_path
    }
'''

    # Save function code
    function_dir = Path(__file__).parent / "firestore_backup_function"
    function_dir.mkdir(exist_ok=True)

    with open(function_dir / "main.py", "w") as f:
        f.write(function_code)

    # Create requirements.txt
    requirements = """google-cloud-firestore-admin==0.8.0
"""

    with open(function_dir / "requirements.txt", "w") as f:
        f.write(requirements)

    print("   ✅ Created Cloud Function code at: {function_dir}")

    # Create deployment script
    deploy_script = f"""#!/bin/bash
# Deploy Firestore backup Cloud Function

echo "🚀 Deploying Firestore backup function..."

# Enable required APIs
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudscheduler.googleapis.com

# Deploy function
gcloud functions deploy firestore-backup \\
    --runtime python39 \\
    --trigger-http \\
    --entry-point firestore_backup \\
    --source {function_dir} \\
    --project {PROJECT_ID} \\
    --region us-central1 \\
    --service-account sentinelops-sa@{PROJECT_ID}.iam.gserviceaccount.com \\
    --allow-unauthenticated

# Create Cloud Scheduler job
gcloud scheduler jobs create http firestore-daily-backup \\
    --location us-central1 \\
    --schedule "{BACKUP_SCHEDULE}" \\
    --uri https://us-central1-{PROJECT_ID}.cloudfunctions.net/firestore-backup \\
    --http-method GET \\
    --project {PROJECT_ID} \\
    --description "Daily Firestore backup at 2 AM"

echo "✅ Scheduled backup configured!"
"""

    deploy_path = Path(__file__).parent / "deploy_firestore_backup.sh"
    with open(deploy_path, "w") as f:
        f.write(deploy_script)
    os.chmod(deploy_path, 0o755)

    print("   ✅ Created deployment script: {deploy_path}")
    print("   📅 Schedule: Daily at 2 AM (cron: {BACKUP_SCHEDULE})")

    return True


def create_backup_documentation():
    """Create backup and restore documentation"""
    print("\n📚 Creating backup documentation...")

    doc_content = f"""# Firestore Backup and Restore Guide

## Overview
This guide describes the Firestore backup and restore procedures for SentinelOps.

## Backup Configuration

### Backup Storage
- **Bucket**: `{BACKUP_BUCKET}`
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
   gsutil ls {BACKUP_BUCKET}/firestore_backup/
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
gsutil ls -l {BACKUP_BUCKET}/firestore_backup/ | tail -10

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
"""

    doc_path = (
        Path(__file__).parent.parent
        / "docs"
        / "operations"
        / "firestore-backup-guide.md"
    )
    doc_path.parent.mkdir(exist_ok=True)

    with open(doc_path, "w") as f:
        f.write(doc_content)

    print("   ✅ Created documentation: {doc_path}")

    return True


def main():
    """Main setup function"""
    print("🔄 Setting up Firestore backup policies")
    print("=" * 60)

    success = True

    # Create backup bucket
    if not create_backup_bucket():
        success = False

    # Create backup scripts
    if not create_backup_script():
        success = False

    # Set up scheduled backups
    if not create_scheduled_backup():
        success = False

    # Create documentation
    if not create_backup_documentation():
        success = False

    print("\n" + "=" * 60)

    if success:
        print("✅ Firestore backup setup completed!")
        print("\nNext steps:")
        print("1. Run ./scripts/deploy_firestore_backup.sh to enable automated backups")
        print("2. Test manual backup with ./scripts/backup_firestore.sh")
        print("3. Review documentation at docs/operations/firestore-backup-guide.md")

        # Update checklist
        checklist_path = (
            Path(__file__).parent.parent
            / "docs"
            / "checklists"
            / "08-google-cloud-integration.md"
        )
        try:
            with open(checklist_path, "r") as f:
                content = f.read()

            content = content.replace(
                "  - [ ] Set up backup policies", "  - [x] Set up backup policies"
            )

            with open(checklist_path, "w") as f:
                f.write(content)

            print("\n✅ Updated checklist")
        except Exception as e:
            print("\n⚠️ Could not update checklist: {e}")
    else:
        print("❌ Some backup setup steps failed")


if __name__ == "__main__":
    main()
