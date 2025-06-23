# IAM Permissions Documentation

This document details all IAM roles and permissions required for SentinelOps components.

## Service Accounts

### 1. Detection Agent Service Account
**Name**: `detection-agent-sa@{project-id}.iam.gserviceaccount.com`

**Roles**:
- `roles/bigquery.dataViewer` - Read access to BigQuery datasets
- `roles/bigquery.jobUser` - Run BigQuery queries
- `roles/pubsub.publisher` - Publish messages to Pub/Sub topics
- `roles/logging.logWriter` - Write application logs
- `roles/monitoring.metricWriter` - Write custom metrics

**Custom Permissions**: None required

### 2. Analysis Agent Service Account
**Name**: `analysis-agent-sa@{project-id}.iam.gserviceaccount.com`

**Roles**:
- `roles/aiplatform.user` - Use Vertex AI services
- `roles/datastore.user` - Read/write Firestore documents
- `roles/pubsub.subscriber` - Subscribe to Pub/Sub topics
- `roles/pubsub.publisher` - Publish analysis results
- `roles/secretmanager.secretAccessor` - Access API keys
- `roles/logging.logWriter` - Write application logs
- `roles/monitoring.metricWriter` - Write custom metrics

**Custom Permissions**: None required

### 3. Remediation Agent Service Account
**Name**: `remediation-agent-sa@{project-id}.iam.gserviceaccount.com`

**Roles**:
- `roles/compute.instanceAdmin` - Manage compute instances
- `roles/compute.securityAdmin` - Manage firewall rules
- `roles/iam.securityAdmin` - Manage IAM policies
- `roles/pubsub.subscriber` - Subscribe to remediation requests
- `roles/datastore.user` - Update incident records
- `roles/logging.logWriter` - Write application logs
- `roles/monitoring.metricWriter` - Write custom metrics

**Custom Permissions**:
```yaml
title: "Remediation Agent Custom Role"
description: "Additional permissions for remediation actions"
stage: "GA"
includedPermissions:
- compute.instances.reset
- compute.instances.stop
- compute.instances.start
- compute.instances.setMetadata
- compute.instances.setTags
- compute.firewalls.create
- compute.firewalls.update
- compute.firewalls.delete
- iam.serviceAccountKeys.delete
- iam.serviceAccountKeys.disable
```

### 4. Communication Agent Service Account
**Name**: `communication-agent-sa@{project-id}.iam.gserviceaccount.com`

**Roles**:
- `roles/pubsub.subscriber` - Subscribe to notification requests
- `roles/datastore.viewer` - Read incident details
- `roles/secretmanager.secretAccessor` - Access notification credentials
- `roles/logging.logWriter` - Write application logs
- `roles/monitoring.metricWriter` - Write custom metrics

**Custom Permissions**: None required

### 5. Orchestration Agent Service Account
**Name**: `orchestration-agent-sa@{project-id}.iam.gserviceaccount.com`

**Roles**:
- `roles/pubsub.editor` - Manage all Pub/Sub operations
- `roles/datastore.owner` - Full Firestore access
- `roles/workflows.invoker` - Trigger workflows
- `roles/run.invoker` - Invoke Cloud Run services
- `roles/logging.logWriter` - Write application logs
- `roles/monitoring.metricWriter` - Write custom metrics

**Custom Permissions**: None required

### 6. Deployment Service Account
**Name**: `deployment-sa@{project-id}.iam.gserviceaccount.com`

**Roles**:
- `roles/run.admin` - Deploy Cloud Run services
- `roles/cloudfunctions.admin` - Deploy Cloud Functions
- `roles/iam.serviceAccountUser` - Act as service accounts
- `roles/storage.admin` - Manage deployment artifacts
- `roles/cloudbuild.builds.editor` - Trigger builds

**Custom Permissions**: None required

## Project-Level Roles

### Admin Roles
For project administrators:
- `roles/owner` - Full project control
- `roles/billing.admin` - Manage billing

### Developer Roles
For development team members:
- `roles/viewer` - View all resources
- `roles/logging.viewer` - View logs
- `roles/monitoring.viewer` - View metrics
- `roles/bigquery.dataViewer` - Query data

### Security Team Roles
For security analysts:
- `roles/securitycenter.findingsViewer` - View security findings
- `roles/logging.privateLogViewer` - View audit logs
- `roles/iam.securityReviewer` - Review IAM policies

## Resource-Level Permissions

### BigQuery Datasets

**sentinelops_logs** dataset:
- Detection Agent SA: `bigquery.dataViewer`
- Analysis Agent SA: `bigquery.dataViewer`
- Security Team: `bigquery.dataViewer`

**sentinelops_billing** dataset:
- Billing Admin: `bigquery.dataOwner`
- Cost Analysis Scripts: `bigquery.dataViewer`

### Pub/Sub Topics

**detection-topic**:
- Detection Agent SA: `pubsub.publisher`
- Orchestration Agent SA: `pubsub.subscriber`

**analysis-topic**:
- Orchestration Agent SA: `pubsub.publisher`
- Analysis Agent SA: `pubsub.subscriber`

**remediation-topic**:
- Analysis Agent SA: `pubsub.publisher`
- Remediation Agent SA: `pubsub.subscriber`

**communication-topic**:
- All Agent SAs: `pubsub.publisher`
- Communication Agent SA: `pubsub.subscriber`

### Secret Manager Secrets

**gemini-api-key**:
- Analysis Agent SA: `secretmanager.secretAccessor`

**slack-webhook-url**:
- Communication Agent SA: `secretmanager.secretAccessor`

**twilio-credentials**:
- Communication Agent SA: `secretmanager.secretAccessor`

## Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Incidents collection
    match /incidents/{incident} {
      allow read: if request.auth != null;
      allow write: if request.auth != null &&
        request.auth.token.email.matches(".*-sa@.*gserviceaccount.com");
    }

    // Configurations collection
    match /configurations/{config} {
      allow read: if request.auth != null;
      allow write: if request.auth != null &&
        request.auth.uid in ['orchestration-agent-sa'];
    }

    // Audit logs collection
    match /audit_logs/{log} {
      allow read: if request.auth != null;
      allow create: if request.auth != null;
      allow update, delete: if false; // Immutable
    }

    // Cost data collections
    match /cost_drivers/{doc} {
      allow read: if request.auth != null;
      allow write: if request.auth != null &&
        request.auth.uid in ['cost-optimization-sa'];
    }
  }
}
```

## Best Practices

### 1. Principle of Least Privilege
- Grant only the minimum permissions required
- Use predefined roles where possible
- Create custom roles for specific needs

### 2. Service Account Management
- Use separate service accounts per component
- Rotate service account keys regularly
- Never store keys in code

### 3. Regular Audits
- Review IAM policies monthly
- Check for unused service accounts
- Monitor permission usage

### 4. Access Controls
- Use groups for human users
- Implement conditional access policies
- Enable 2FA for all admin accounts

## Permission Matrix

| Component | BigQuery | Firestore | Pub/Sub | Compute | IAM | Secrets |
|-----------|----------|-----------|---------|---------|-----|---------|
| Detection | Read | - | Publish | - | - | - |
| Analysis | Read | R/W | Pub/Sub | - | - | Read |
| Remediation | - | R/W | Subscribe | Admin | Admin | - |
| Communication | - | Read | Subscribe | - | - | Read |
| Orchestration | - | Admin | Admin | - | - | - |

## Troubleshooting

### Common Permission Issues

1. **"Permission denied" when querying BigQuery**
   - Verify service account has `bigquery.dataViewer` role
   - Check dataset-level permissions

2. **"Failed to publish to Pub/Sub"**
   - Ensure service account has `pubsub.publisher` role
   - Verify topic exists and is in the correct project

3. **"Cannot access Secret Manager"**
   - Grant `secretmanager.secretAccessor` role
   - Check secret-level IAM bindings

4. **"Firestore write failed"**
   - Review Firestore security rules
   - Verify service account authentication

### Debugging Commands

```bash
# List all service accounts
gcloud iam service-accounts list

# Check service account permissions
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:SA_EMAIL"

# Test service account impersonation
gcloud auth application-default login --impersonate-service-account=SA_EMAIL

# View effective permissions
gcloud iam list-testable-permissions //cloudresourcemanager.googleapis.com/projects/PROJECT_ID
```

## Compliance

### SOC 2 Requirements
- Quarterly access reviews
- Automated de-provisioning
- Audit trail for all changes

### GDPR Compliance
- Data access logging enabled
- Right to deletion implemented
- Data residency controls

### Security Certifications
- ISO 27001 aligned
- NIST framework compliance
- CIS benchmarks followed
