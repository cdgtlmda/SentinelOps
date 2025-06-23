# SentinelOps Resource Hierarchy

## Overview
This document describes the resource hierarchy and organization structure for the SentinelOps project in Google Cloud Platform.

## Project Structure

### Project Information
- **Project ID**: your-gcp-project-id
- **Project Name**: SentinelOps Demo
- **Primary Region**: us-central1
- **Organization**: Not part of an organization (standalone project)

## Resource Organization

### 1. Resource Labels
All resources in the project should include the following labels:

#### Required Labels
- `environment`: development|staging|production
- `application`: sentinelops
- `team`: security
- `owner`: Team or individual responsible

#### Optional Labels
- `managed-by`: terraform|manual
- `tier`: critical|important|non-critical
- `data-classification`: public|internal|sensitive|restricted
- `cost-center`: security-ops
- `compliance`: pci-dss|hipaa|sox|none
- `version`: Semantic version (e.g., v1-0-0)

### 2. Resource Naming Conventions

#### General Pattern
`{application}-{resource-type}-{purpose}-{environment}`

#### Specific Patterns by Service

**BigQuery**
- Dataset: `sentinelops_{environment}`
- Table: `{dataset}.{resource_type}_{purpose}`
- View: `{dataset}.view_{purpose}`

**Pub/Sub**
- Topic: `{purpose}-{resource_type}`
- Subscription: `{topic}-sub-{consumer}`

**Cloud Run**
- Service: `sentinelops-{component}-{environment}`

**Cloud Functions**
- Function: `sentinelops-{action}-{resource_type}`

**Storage**
- Bucket: `sentinelops-{project_id}-{purpose}-{environment}`

**Firestore**
- Database: `sentinelops-{environment}`
- Collection: `{resource_type}_{purpose}`

**Compute Engine**
- Instance: `sentinelops-{purpose}-{environment}-{index}`
- Template: `sentinelops-{purpose}-template-{version}`
- Group: `sentinelops-{purpose}-ig-{environment}`

**Network**
- VPC: `sentinelops-vpc-{environment}`
- Subnet: `{vpc}-subnet-{region}-{purpose}`
- Firewall: `sentinelops-fw-{direction}-{purpose}`

**IAM**
- Service Account: `sentinelops-{purpose}-sa`
- Custom Role: `sentinelops.{resource_type}.{permission_level}`

**Secret Manager**
- Secret: `sentinelops_{environment}_{secret_type}`

### 3. Environment Structure

| Environment | Short Code | Tier | Purpose |
|-------------|------------|------|---------|
| Development | dev | non-critical | Development and testing |
| Staging | stg | important | Pre-production validation |
| Production | prd | critical | Live system |

### 4. Resource Grouping

Resources are logically grouped by:

1. **Component/Agent**
   - Detection Agent resources
   - Analysis Agent resources
   - Remediation Agent resources
   - Communication Agent resources
   - Orchestration Agent resources

2. **Function**
   - Data storage (BigQuery, Firestore)
   - Messaging (Pub/Sub)
   - Compute (Cloud Run, Cloud Functions)
   - Security (IAM, Secret Manager)
   - Monitoring (Cloud Monitoring, Logging)

### 5. Access Control Hierarchy

1. **Project-level IAM**
   - Project Owner: Full administrative access
   - Project Editor: Modify resources
   - Project Viewer: Read-only access

2. **Service-specific IAM**
   - Each agent has its own service account
   - Least privilege principle applied
   - Cross-service permissions managed through custom roles

### 6. Cost Management

- Resources tagged with cost-center labels
- Budget alerts configured per environment
- Resource quotas set to prevent runaway costs
- Regular cost optimization reviews

## Implementation Notes

1. All resources must follow the naming conventions
2. Labels must be applied at resource creation time
3. Use Terraform for infrastructure provisioning to ensure consistency
4. Regular audits to ensure compliance with hierarchy standards
