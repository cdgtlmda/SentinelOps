# Manual Setup Instructions for Google Cloud

Due to permission limitations of the current service account, the following steps need to be completed manually by a project owner or someone with appropriate permissions:

## 1. Enable Missing APIs

Run these commands with owner permissions:
```bash
gcloud services enable firestore.googleapis.com --project=your-gcp-project-id
gcloud services enable cloudbilling.googleapis.com --project=your-gcp-project-id
gcloud services enable cloudbuild.googleapis.com --project=your-gcp-project-id
```

## 2. Grant IAM Admin Permissions to Service Account

Grant the current service account permission to manage IAM:
```bash
gcloud projects add-iam-policy-binding your-gcp-project-id \
    --member="serviceAccount:sentinelops-sa@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/resourcemanager.projectIamAdmin"

gcloud projects add-iam-policy-binding your-gcp-project-id \
    --member="serviceAccount:sentinelops-sa@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountAdmin"

gcloud projects add-iam-policy-binding your-gcp-project-id \
    --member="serviceAccount:sentinelops-sa@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountKeyAdmin"
```

## 3. After Manual Steps Complete

Once the above permissions are granted, re-run the setup scripts:
```bash
cd /path/to/sentinelops
python scripts/enable_gcp_apis.py
python scripts/setup_iam_permissions.py
```

## Current Status

✅ Completed:
- Project exists and is accessible
- Most required APIs are enabled (11/14)
- Project is configured with service account

⏳ Pending (requires manual intervention):
- Enable Firestore, Cloud Billing, and Cloud Build APIs
- Create service accounts for each agent
- Set up IAM permissions
- Configure billing

## Alternative: Continue with Available Resources

I can proceed with the following checklist items using the current permissions:
- BigQuery setup (dataset and tables)
- Pub/Sub configuration (topics and subscriptions)
- Create configuration files and code structure
