#!/bin/bash
# Firestore composite index creation commands

PROJECT_ID=your-gcp-project-id

gcloud firestore indexes composite create --collection-group=incidents --field-config field-path=status,order=ASCENDING --field-config field-path=severity,order=DESCENDING --field-config field-path=timestamp,order=DESCENDING --project=$PROJECT_ID
gcloud firestore indexes composite create --collection-group=incidents --field-config field-path=type,order=ASCENDING --field-config field-path=timestamp,order=DESCENDING --project=$PROJECT_ID
gcloud firestore indexes composite create --collection-group=audit_logs --field-config field-path=action,order=ASCENDING --field-config field-path=timestamp,order=DESCENDING --project=$PROJECT_ID
gcloud firestore indexes composite create --collection-group=audit_logs --field-config field-path=actor,order=ASCENDING --field-config field-path=timestamp,order=DESCENDING --project=$PROJECT_ID
gcloud firestore indexes composite create --collection-group=agent_status --field-config field-path=agent_type,order=ASCENDING --field-config field-path=status,order=ASCENDING --project=$PROJECT_ID
