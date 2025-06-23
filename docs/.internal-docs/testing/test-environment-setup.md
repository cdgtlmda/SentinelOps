# Test Environment Setup Guide

This guide describes how to set up a dedicated GCP test environment for SentinelOps.

## Overview

The test environment provides an isolated GCP project with all necessary resources for running integration and end-to-end tests without affecting production resources.

## Prerequisites

1. Google Cloud SDK installed (`gcloud` CLI)
2. A GCP billing account (optional, but required for some services)
3. Appropriate permissions to create GCP projects

## Automatic Setup

Run the setup script to automatically create and configure the test project:

```bash
# Basic setup (no billing)
python scripts/setup/setup_test_gcp_project.py

# Setup with billing account
python scripts/setup/setup_test_gcp_project.py --billing-account YOUR_BILLING_ACCOUNT_ID

# Custom project ID
python scripts/setup/setup_test_gcp_project.py --project-id my-sentinelops-test
```

## What Gets Created

The setup script creates the following resources:

### 1. GCP Project
- Project ID: `sentinelops-test` (or custom)
- Display name: "SentinelOps Test"

### 2. Enabled APIs
- BigQuery API
- Pub/Sub API
- Cloud Run API
- Secret Manager API
- Cloud Storage API
- Vertex AI API
- Logging & Monitoring APIs
- IAM APIs

### 3. Service Account
- Name: `sentinelops-test-sa@[PROJECT_ID].iam.gserviceaccount.com`
- Roles:
  - BigQuery Admin
  - Pub/Sub Admin
  - Storage Admin
  - Logging Admin
  - Secret Manager Admin
  - AI Platform User
  - Cloud Run Admin

### 4. BigQuery Resources
- Dataset: `test_security_logs`
- Location: US

### 5. Pub/Sub Resources
Topics and subscriptions:
- `test-sentinelops-incidents` / `test-sentinelops-incidents-sub`
- `test-sentinelops-alerts` / `test-sentinelops-alerts-sub`
- `test-sentinelops-remediation` / `test-sentinelops-remediation-sub`
- `test-sentinelops-analysis` / `test-sentinelops-analysis-sub`

### 6. Cloud Storage
- Bucket: `[PROJECT_ID]-data`
- Location: US
- Uniform bucket-level access enabled

### 7. Secret Manager
Test secrets:
- `test-slack-webhook`
- `test-email-password`
- `test-api-key`

### 8. Service Account Key
- Location: `tests/fixtures/test-service-account.json`
- Automatically downloaded and configured

## Manual Configuration

After running the setup script, manually configure:

### 1. Resource Quotas (Recommended)
In GCP Console, set quotas to prevent runaway costs:
- BigQuery: 1TB query limit per day
- Compute Engine: 10 instances max
- Cloud Run: 5 services max

### 2. Budget Alerts
1. Go to Billing > Budgets & alerts
2. Create a budget for the test project
3. Set alert at $50, $100, $200

### 3. VPC Service Controls (Optional)
For additional isolation:
1. Create a VPC Service Control perimeter
2. Include only the test project
3. Restrict access to production resources

## Using the Test Environment

### 1. Load Environment Variables
```bash
source .env.test
```

### 2. Verify Setup
```bash
# Check current project
gcloud config get-value project

# Verify service account
gcloud auth list

# Test BigQuery access
bq ls
```

### 3. Run Tests
```bash
# Run tests requiring GCP
pytest -m requires_gcp

# Run all integration tests
make test-integration

# Run specific test suite
pytest tests/integration/gcp/
```

## Local Development with Emulators

For local development without GCP costs, use emulators:

```bash
# Start BigQuery emulator
docker run -p 9050:9050 ghcr.io/goccy/bigquery-emulator:latest

# Start Pub/Sub emulator
gcloud beta emulators pubsub start --host-port=localhost:8085

# Start Firestore emulator
gcloud beta emulators firestore start --host-port=localhost:8080
```

The `.env.test` file is pre-configured to use these emulators when available.

## Cleanup

To clean up test resources:

```bash
# Delete all test data (keeps project)
python scripts/cleanup_test_resources.py

# Delete entire test project
gcloud projects delete sentinelops-test
```

## Troubleshooting

### Permission Denied Errors
- Ensure you have `Project Creator` role in your organization
- Check if billing account is properly linked

### API Not Enabled Errors
- Wait 2-3 minutes after enabling APIs
- Manually enable in Console if script fails

### Service Account Key Issues
- Delete existing key and regenerate
- Check file permissions on `tests/fixtures/`

### Emulator Connection Issues
- Verify emulator is running on correct port
- Check firewall rules for local connections

## Cost Management

Estimated monthly costs for test environment:
- Minimal usage: < $10
- Moderate testing: $20-50
- Heavy integration testing: $50-100

Tips to minimize costs:
1. Use emulators for local development
2. Set up budget alerts
3. Clean up resources after test runs
4. Use resource quotas
5. Schedule automatic shutdowns

## Security Considerations

1. **Never use production credentials in test environment**
2. Test service account has admin permissions - restrict access
3. Rotate service account keys regularly
4. Use separate test data, never copy production data
5. Enable audit logging for compliance

## Next Steps

1. Run the setup script
2. Configure budget alerts
3. Test the environment with sample tests
4. Set up CI/CD integration
5. Document any project-specific test configurations