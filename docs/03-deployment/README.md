# Google Cloud Platform Integration Documentation

This directory contains comprehensive documentation for SentinelOps' integration with Google Cloud Platform (GCP).

## Table of Contents

1. [Architecture Overview](./architecture.md)
2. [Service Documentation](./services/)
   - [BigQuery](./services/bigquery.md)
   - [Cloud Run](./services/cloud-run.md)
   - [Cloud Functions](./services/cloud-functions.md)
   - [Firestore](./services/firestore.md)
   - [Pub/Sub](./services/pubsub.md)
3. [IAM and Security](./iam-permissions.md)
4. [Deployment Guide](./deployment.md)
5. [Cost Optimization](./cost-optimization.md)
6. [Monitoring and Logging](./monitoring.md)
7. [Troubleshooting](./troubleshooting.md)

## Quick Start

1. **Prerequisites**:
   - Google Cloud Project with billing enabled
   - gcloud CLI installed and authenticated
   - Required APIs enabled (see [deployment guide](./deployment.md))

2. **Environment Setup**:
   ```bash
   export GCP_PROJECT_ID=your-project-id
   export GCP_BILLING_ACCOUNT_ID=your-billing-account-id
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
   ```

3. **Deploy Infrastructure**:
   ```bash
   cd terraform/
   terraform init
   terraform plan
   terraform apply
   ```

4. **Deploy Services**:
   ```bash
   cd scripts/
   ./deploy_all_services.sh
   ```

## Architecture Overview

SentinelOps uses a microservices architecture deployed on Google Cloud Platform:

- **Detection Agent**: Cloud Run service monitoring security events
- **Analysis Agent**: Cloud Run service analyzing threats with Gemini AI
- **Remediation Agent**: Cloud Functions for automated response actions
- **Communication Agent**: Cloud Run service for notifications
- **Orchestration Agent**: Cloud Run service coordinating all agents

## Key GCP Services Used

### Data Storage
- **BigQuery**: Log storage and analysis
- **Firestore**: Real-time incident tracking and configuration

### Compute
- **Cloud Run**: Containerized agent services
- **Cloud Functions**: Event-driven remediation actions

### Messaging
- **Pub/Sub**: Inter-agent communication

### AI/ML
- **Vertex AI**: Gemini model integration

### Security
- **Secret Manager**: Secure credential storage
- **Cloud IAM**: Fine-grained access control

## Support

For issues or questions:
1. Check the [troubleshooting guide](./troubleshooting.md)
2. Review [deployment logs](./deployment.md#logging)
3. Contact the platform team
