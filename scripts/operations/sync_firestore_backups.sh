#!/bin/bash
# Sync Firestore backups across regions

PROJECT_ID="your-gcp-project-id"
PRIMARY_BUCKET="gs://${PROJECT_ID}-firestore-backups"
SECONDARY_BUCKET="gs://${PROJECT_ID}-firestore-backups-us-east1"
TERTIARY_BUCKET="gs://${PROJECT_ID}-firestore-backups-us-west1"

echo "🔄 Syncing Firestore backups across regions"
echo "=========================================="

# Create regional backup buckets if they don't exist
for REGION in "us-east1" "us-west1"; do
    BUCKET="gs://${PROJECT_ID}-firestore-backups-${REGION}"
    
    if ! gsutil ls "$BUCKET" &>/dev/null; then
        echo "Creating bucket: $BUCKET"
        gsutil mb -p "$PROJECT_ID" -c STANDARD -l "$REGION" "$BUCKET"
    fi
done

# Sync backups from primary to secondary regions
echo ""
echo "Syncing to secondary region..."
gsutil -m rsync -r -d "$PRIMARY_BUCKET/firestore_backup/" "$SECONDARY_BUCKET/firestore_backup/"

echo ""
echo "Syncing to tertiary region..."
gsutil -m rsync -r -d "$PRIMARY_BUCKET/firestore_backup/" "$TERTIARY_BUCKET/firestore_backup/"

echo ""
echo "✅ Firestore backup sync completed!"

# List backups in all regions
echo ""
echo "Backup inventory:"
for BUCKET in "$PRIMARY_BUCKET" "$SECONDARY_BUCKET" "$TERTIARY_BUCKET"; do
    COUNT=$(gsutil ls "$BUCKET/firestore_backup/" 2>/dev/null | wc -l)
    echo "  $BUCKET: $COUNT backups"
done
