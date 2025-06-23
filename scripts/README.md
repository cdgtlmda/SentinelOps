# SentinelOps Scripts

This directory contains essential scripts for setting up, deploying, and maintaining the SentinelOps security platform.

## Quick Start

For a new deployment, run these commands in order:

```bash
# 1. Set up Google Cloud infrastructure
cd setup/
./enable-apis.sh
./create-service-account.sh
python setup_authentication.py
python setup_bigquery.py
python setup_firestore.py
python setup_pubsub.py
python setup_secret_manager.py
python setup_monitoring.py

# 2. Deploy the agents
cd ../deployment/
./build_amd64_images.sh
./deploy_all_agents.sh
```

## Directory Structure

### Core Directories

#### 📁 setup/
Infrastructure setup scripts that create Google Cloud resources.

**Core Setup Scripts:**
- `enable-apis.sh` - Enable required Google Cloud APIs
- `create-service-account.sh` - Create service accounts for agents
- `setup_authentication.py` - Configure IAM roles and permissions
- `setup_bigquery.py` - Create BigQuery dataset and tables
- `setup_firestore.py` - Set up Firestore collections
- `setup_pubsub.py` - Create Pub/Sub topics and subscriptions
- `setup_secret_manager.py` - Configure Secret Manager
- `setup_monitoring.py` - Set up monitoring and alerting

#### 📁 deployment/
Scripts for building and deploying SentinelOps agents to Cloud Run.

- `build_amd64_images.sh` - Build Docker images for all agents
- `deploy_all_agents.sh` - Deploy all agents at once
- `deploy_to_cloud_run.sh` - Generic Cloud Run deployment
- Individual deployment scripts for each agent

#### 📁 development/
Development tools for code quality and local setup.

- **`check-compliance.sh`** - Comprehensive code quality checker (runs all linters)
- `run_quality_checks.py` - Python implementation of compliance checks
- `setup_dev.sh` - Set up local development environment
- `pre-commit-hook.sh` - Git pre-commit hook

#### 📁 operations/
Scripts for day-to-day operations and maintenance.

- `backup_firestore.sh` - Backup Firestore data
- `restore_firestore.sh` - Restore from backup
- `check_authentication.py` - Verify authentication is working
- `verify_apis.py` - Check all required APIs are enabled

#### 📁 utilities/
General utility scripts for various tasks.

- `validate-environment.py` - Validate environment setup
- `check-python-version.py` - Check Python compatibility
- `manage_secrets.py` - Manage secrets in Secret Manager
- `security_check.py` - Run security audits

### Specialized Directories

#### 📁 auth/
Authentication and authorization management scripts.

- `setup_oidc.py` - Configure OpenID Connect authentication
- `test_authentication.py` - Test authentication flows
- `test_authorization.py` - Verify authorization policies

#### 📁 ci/
Continuous Integration gate checks for the CI/CD pipeline.

- `coverage_gate.py` - Enforce code coverage thresholds
- `performance_gate.py` - Check performance benchmarks
- `security_gate.py` - Run security validations

#### 📁 database/
Database management and migration scripts.

- `manage_migrations.py` - Handle database migrations
- `test_connection_pool.py` - Test database connection pooling
- `verify_migrations.py` - Verify migration status

#### 📁 monitoring/
Comprehensive monitoring and alerting setup.

- `configure_alerts.py` - Set up alerting rules
- `create_monitoring_dashboards.py` - Create monitoring dashboards
- `test_metrics_collector.py` - Collect and analyze test metrics
- `coverage_reporter.py` - Generate coverage reports

#### 📁 network/
Network configuration and security scripts.

- `configure_api_access.py` - Configure API access controls
- `configure_load_balancing.py` - Set up load balancing
- `setup_service_perimeters.py` - Configure VPC service perimeters

#### 📁 firestore_backup_function/
Cloud Function for automated Firestore backups.

- `main.py` - Cloud Function implementation
- `requirements.txt` - Function dependencies

#### 📁 quotas/
API quota monitoring and management.

- `check_api_quotas.py` - Monitor and report API quota usage

#### 📁 verification/
System verification and integration testing.

- `verify_gcp_integration.py` - Comprehensive GCP integration tests

## Prerequisites

- **Python 3.11+** with virtual environment
- **Google Cloud SDK** (`gcloud`) authenticated
- **Docker** for building container images
- **Project permissions**: Owner or Editor role

## Environment Setup

1. Set environment variables:
   ```bash
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
   ```

2. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Common Tasks

### Check Code Quality
```bash
cd development/
./check-compliance.sh
```

This runs:
- `flake8` - Style guide enforcement
- `pylint` - Code analysis
- `mypy` - Type checking
- `pytest` - Unit tests with coverage
- `bandit` - Security linting
- `radon` - Complexity analysis

### Deploy Updates
```bash
cd deployment/
./build_amd64_images.sh
./deploy_all_agents.sh
```

### Backup Data
```bash
cd operations/
./backup_firestore.sh
```

### Monitor System Health
```bash
cd monitoring/
python create_monitoring_dashboards.py
python configure_alerts.py
```

### Verify GCP Integration
```bash
cd verification/
python verify_gcp_integration.py
```

## Script Categories

### Infrastructure Setup (One-time)
Located in `setup/`, these scripts create the foundational GCP resources.

### Continuous Operations
- `operations/` - Regular maintenance tasks
- `monitoring/` - Observability setup
- `utilities/` - Ad-hoc tools

### Development Workflow
- `development/` - Code quality tools
- `ci/` - CI/CD gates
- `database/` - Schema management

### Security & Compliance
- `auth/` - Authentication setup
- `network/` - Network security
- `development/check-compliance.sh` - Code compliance

## Important Notes

- Always run scripts from their respective directories
- Most scripts require authenticated `gcloud` CLI
- Infrastructure setup scripts are idempotent (safe to run multiple times)
- Check script headers for specific requirements or parameters

## Troubleshooting

If you encounter issues:

1. **Authentication**: `operations/check_authentication.py`
2. **API Status**: `operations/verify_apis.py`
3. **Environment**: `utilities/validate-environment.py`
4. **GCP Integration**: `verification/verify_gcp_integration.py`
5. **Review logs** in Google Cloud Console

## Contributing

When adding new scripts:
1. Place them in the appropriate directory
2. Add clear documentation in the script header
3. Update this README with the script's purpose
4. Ensure the script handles errors gracefully
5. Test thoroughly before committing

## Directory Summary

- **Total Scripts**: ~100 organized scripts
- **Core Scripts**: 47 (setup, deployment, dev, ops, utilities)
- **Specialized Scripts**: 53 (auth, ci, database, monitoring, network, etc.)
- **Languages**: Primarily Python and Bash
- **Purpose**: Complete lifecycle management of SentinelOps platform
