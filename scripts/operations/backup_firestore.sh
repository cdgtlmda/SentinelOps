#!/bin/bash
# Manual Firestore backup script

PROJECT_ID="your-gcp-project-id"
BACKUP_BUCKET="gs://your-gcp-project-id-firestore-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_BUCKET}/firestore_backup/${TIMESTAMP}"

echo "🔄 Starting Firestore backup..."
echo "   Project: $PROJECT_ID"
echo "   Destination: $BACKUP_PATH"

# Export all collections
gcloud firestore export $BACKUP_PATH \
    --project=$PROJECT_ID \
    --format=json

if [ $? -eq 0 ]; then
    echo "✅ Backup completed successfully!"
    echo "   Location: $BACKUP_PATH"
else
    echo "❌ Backup failed!"
    exit 1
fi
