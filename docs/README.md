# SentinelOps Documentation

> **🚨 IMPORTANT SETUP NOTICE**: This documentation uses placeholder values like `your-gcp-project-id` and `/path/to/service-account-key.json`. You **MUST** replace these with your actual GCP project ID, service account paths, and credentials when setting up SentinelOps. Never use the placeholder values directly.

Welcome to the comprehensive SentinelOps documentation. This guide will help you understand, deploy, and operate the SentinelOps security monitoring and response platform.

## Documentation Structure

### 📚 [01 - Getting Started](./01-getting-started/)
- Introduction to SentinelOps
- System requirements
- Quick start guide
- Basic concepts

### 🏗️ [02 - Architecture](./02-architecture/)
- System architecture overview
- Agent documentation (Detection, Analysis, Orchestrator, Remediation, Communication)
- ADK integration patterns
- Data flow and interactions
- Architecture diagrams

### 🚀 [03 - Deployment](./03-deployment/)
- ADK deployment guide
- GCP deployment procedures
- Configuration reference
- IAM permissions and security
- Production deployment guide

### 🔧 [04 - Operations](./04-operations/)
- ADK troubleshooting
- Disaster recovery procedures
- Monitoring and maintenance
- Incident response procedures
- Scaling guidelines

### 💻 [05 - Development](./05-development/)
- **[REAL GCP TESTING POLICY](./05-development/REAL_GCP_TESTING_POLICY.md)** ⚠️ **MUST READ** - Mandatory testing requirements
- CI/CD pipeline setup
- Development environment
- Testing strategies
- Performance optimization
- Security reviews

### 📖 [06 - Reference](./06-reference/)
- Configuration reference
- API documentation
- Database schemas
- Glossary of terms

## Quick Links

- **[ADK Deployment Guide](./03-deployment/adk-deployment-guide.md)** - Essential for getting started with ADK
- **[System Architecture](./02-architecture/diagrams/system-architecture.md)** - High-level system overview
- **[Troubleshooting Guide](./04-operations/adk-troubleshooting.md)** - Common issues and solutions
- **[Configuration Reference](./03-deployment/configuration/)** - All configuration options

## About SentinelOps

SentinelOps is a production-grade security operations platform built on Google's Agent Development Kit (ADK). It provides automated incident detection, analysis, and response capabilities using a multi-agent architecture.

### Key Features
- **Multi-Agent Architecture**: Specialized agents for detection, analysis, orchestration, remediation, and communication
- **ADK Integration**: Built on Google's production-ready Agent Development Kit
- **GCP Native**: Fully integrated with Google Cloud Platform services
- **Automated Response**: Intelligent remediation with safety controls
- **Scalable**: Designed for enterprise-scale deployments

## Getting Help

- For deployment issues, see the [ADK Troubleshooting Guide](./04-operations/adk-troubleshooting.md)
- For architecture questions, refer to the [Architecture Documentation](./02-architecture/)
- For configuration help, check the [Configuration Reference](./03-deployment/configuration/)
