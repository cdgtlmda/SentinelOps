# SentinelOps GCP Architecture

## Overview

SentinelOps is deployed on Google Cloud Platform using a cloud-native, serverless architecture that maximizes scalability, reliability, and cost efficiency.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Google Cloud Project                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐             │
│  │   BigQuery  │     │  Firestore  │     │   Secret    │             │
│  │   (Logs)    │     │ (Incidents) │     │   Manager   │             │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘             │
│         │                    │                    │                     │
│  ┌──────┴───────────────────┴────────────────────┴─────────┐          │
│  │                      Pub/Sub Topics                      │          │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │          │
│  │  │Detection│  │Analysis │  │Remediate│  │ Notify  │   │          │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘   │          │
│  └───────┼────────────┼────────────┼────────────┼─────────┘          │
│          │            │            │            │                      │
│  ┌───────┴────┐ ┌────┴─────┐ ┌───┴──────┐ ┌──┴───────┐              │
│  │ Detection  │ │ Analysis │ │Remediation│ │  Comm.   │              │
│  │   Agent    │ │  Agent   │ │  Agent    │ │  Agent   │              │
│  │(Cloud Run) │ │(Cloud Run)│ │(Functions)│ │(Cloud Run)│             │
│  └────────────┘ └──────────┘ └───────────┘ └──────────┘              │
│                         │                                              │
│                    ┌────┴─────┐                                       │
│                    │Orchestrate│                                       │
│                    │   Agent   │                                       │
│                    │(Cloud Run)│                                       │
│                    └───────────┘                                       │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────┐          │
│  │                    Monitoring & Logging                  │          │
│  │  Cloud Monitoring │ Cloud Logging │ Error Reporting     │          │
│  └─────────────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Layer

#### BigQuery
- **Purpose**: Centralized log storage and analysis
- **Tables**:
  - `vpc_flow_logs`: Network traffic logs
  - `audit_logs`: Cloud audit logs
  - `firewall_logs`: Firewall rule logs
  - `iam_logs`: IAM activity logs
- **Features**:
  - Partitioned by date for cost optimization
  - Clustered by severity and resource type
  - Streaming inserts for real-time data

#### Firestore
- **Purpose**: Real-time incident tracking and configuration storage
- **Collections**:
  - `incidents`: Active security incidents
  - `configurations`: Agent configurations
  - `remediation_history`: Action audit trail
  - `resource_limits`: Cost control settings
- **Features**:
  - Real-time synchronization
  - Automatic scaling
  - Strong consistency

### 2. Messaging Layer

#### Pub/Sub Topics
- **detection-topic**: New security events detected
- **analysis-topic**: Events requiring analysis
- **remediation-topic**: Approved remediation actions
- **communication-topic**: Notification requests
- **orchestration-topic**: Coordination messages

#### Message Flow
1. Detection Agent → detection-topic → Orchestration Agent
2. Orchestration Agent → analysis-topic → Analysis Agent
3. Analysis Agent → remediation-topic → Remediation Agent
4. All Agents → communication-topic → Communication Agent

### 3. Compute Layer

#### Cloud Run Services

**Detection Agent**
- Container: `gcr.io/{project}/detection-agent:latest`
- Resources: 1 CPU, 512Mi memory
- Scaling: 1-100 instances
- Concurrency: 1000 requests

**Analysis Agent**
- Container: `gcr.io/{project}/analysis-agent:latest`
- Resources: 2 CPU, 2Gi memory
- Scaling: 1-50 instances
- Concurrency: 100 requests
- Integration: Vertex AI (Gemini)

**Communication Agent**
- Container: `gcr.io/{project}/communication-agent:latest`
- Resources: 0.5 CPU, 256Mi memory
- Scaling: 1-20 instances
- Concurrency: 500 requests

**Orchestration Agent**
- Container: `gcr.io/{project}/orchestration-agent:latest`
- Resources: 1 CPU, 1Gi memory
- Scaling: 2-50 instances
- Concurrency: 200 requests

#### Cloud Functions

**Remediation Functions**
- `revoke-credentials`: Disable compromised accounts
- `block-ip-address`: Update firewall rules
- `isolate-vm`: Quarantine instances
- `update-iam`: Modify permissions

### 4. Security Layer

#### IAM Configuration
- **Service Accounts**:
  - `detection-sa@`: BigQuery Data Viewer, Pub/Sub Publisher
  - `analysis-sa@`: Vertex AI User, Firestore User
  - `remediation-sa@`: Compute Admin, Security Admin
  - `communication-sa@`: Pub/Sub Subscriber

#### Network Security
- **VPC**: `sentinelops-vpc`
- **Firewall Rules**:
  - Deny all ingress by default
  - Allow HTTPS (443) to Cloud Run services
  - Allow internal communication
- **Private Google Access**: Enabled
- **Cloud NAT**: For outbound connectivity

### 5. Monitoring Layer

#### Metrics
- Request latency (p50, p95, p99)
- Error rates by service
- Resource utilization
- Cost per service

#### Alerts
- High error rate (>1%)
- Service unavailable
- Budget threshold exceeded
- Security incident detected

## Deployment Patterns

### Multi-Region Setup
```
Primary Region: us-central1
├── All Cloud Run services
├── Firestore (multi-region)
└── Primary Pub/Sub endpoints

Secondary Region: us-east1
├── BigQuery dataset (multi-region)
├── Backup Cloud Functions
└── Disaster recovery resources
```

### High Availability
- **Cloud Run**: Automatic failover across zones
- **Firestore**: Multi-region replication
- **Pub/Sub**: Built-in redundancy
- **BigQuery**: Automatic replication

### Disaster Recovery
- **RTO**: 15 minutes
- **RPO**: 5 minutes
- **Backup Strategy**:
  - Firestore: Daily exports to Cloud Storage
  - Configurations: Version controlled in Git
  - Logs: Retained in BigQuery for 90 days

## Cost Optimization

### Resource Scheduling
- Development environments: Shutdown outside business hours
- Staging: Reduced capacity on weekends
- Production: Always on with auto-scaling

### Committed Use Discounts
- Compute Engine: 1-year commitment
- BigQuery: Flat-rate pricing for predictable workloads

### Budget Controls
- Project-level budget: $10,000/month
- Service-specific budgets with alerts
- Automatic scaling limits

## Performance Targets

| Component | Metric | Target | Current |
|-----------|--------|--------|---------|
| Detection | Latency | <60s | 45s |
| Analysis | Latency | <30s | 22s |
| Remediation | Latency | <120s | 95s |
| End-to-End | Response Time | <5min | 3.5min |
| System | Availability | 99.9% | 99.95% |

## Scaling Considerations

### Horizontal Scaling
- Cloud Run: Automatic based on CPU and concurrency
- Pub/Sub: Unlimited message throughput
- Firestore: Automatic with usage

### Vertical Scaling
- Increase Cloud Run CPU/memory via configuration
- Adjust Pub/Sub subscription concurrency
- Modify Cloud Function memory allocation

### Cost vs Performance
- Use preemptible instances for batch workloads
- Implement request batching for API calls
- Cache frequently accessed data

## Security Best Practices

1. **Least Privilege**: Each service has minimal required permissions
2. **Encryption**: All data encrypted at rest and in transit
3. **Audit Logging**: All actions logged and monitored
4. **Secret Management**: No hardcoded credentials
5. **Network Isolation**: Private IPs where possible
6. **Regular Updates**: Automated dependency updates

## Future Enhancements

1. **Multi-Cloud Support**: AWS and Azure integration
2. **ML Model Training**: Custom threat detection models
3. **Advanced Analytics**: Predictive threat intelligence
4. **API Gateway**: Public API for third-party integration
5. **Compliance Automation**: SOC2, ISO27001 reporting