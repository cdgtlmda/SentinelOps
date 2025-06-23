#!/bin/bash
# Firestore restore script

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_path>"
    echo "Example: $0 gs://your-gcp-project-id-firestore-backups/firestore_backup/20240529_120000"
    exit 1
fi

PROJECT_ID="your-gcp-project-id"
BACKUP_PATH=$1

echo "🔄 Starting Firestore restore..."
echo "   Project: $PROJECT_ID"
echo "   Source: $BACKUP_PATH"
echo ""
echo "⚠️  WARNING: This will overwrite existing data!"
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    gcloud firestore import $BACKUP_PATH \
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
