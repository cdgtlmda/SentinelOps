# Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying SentinelOps in a production environment with all security and persistence features enabled.

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 14 or higher
- Redis (for caching and queues)
- Google Cloud Project (for GCP integration)
- OAuth2 provider configured

## Environment Setup

### 1. Clone and Setup Repository

```bash
git clone https://github.com/cdgtlmda/SentinelOps.git
cd sentinelops
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file with production settings:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/sentinelops
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# OAuth2
OAUTH2_CLIENT_ID=your-client-id
OAUTH2_CLIENT_SECRET=your-client-secret
OAUTH2_AUTHORIZATION_ENDPOINT=https://oauth.provider.com/authorize
OAUTH2_TOKEN_ENDPOINT=https://oauth.provider.com/token
OAUTH2_JWKS_URL=https://oauth.provider.com/.well-known/jwks.json
OAUTH2_ISSUER=https://oauth.provider.com

# GCP Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Communication Services
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=notifications@yourdomain.com
SMTP_PASSWORD=your-smtp-password

SLACK_API_TOKEN=xoxb-your-slack-token
SLACK_DEFAULT_CHANNEL=#security-alerts

# Security
SECRET_KEY=generate-a-secure-secret-key
API_KEY_SALT=generate-another-secure-salt

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## Database Setup

### 1. Create Database

```sql
CREATE DATABASE sentinelops;
CREATE USER sentinelops_user WITH ENCRYPTED PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE sentinelops TO sentinelops_user;
```

### 2. Run Migrations

```bash
cd src/database
alembic upgrade head
```

### 3. Verify Database

```bash
python scripts/database/verify_migrations.py
```

## Service Configuration

### 1. GCP Service Account

Create a service account with the following roles:
- Security Admin
- Resource Manager Admin
- IAM Admin
- Compute Admin

Download the service account key and set `GOOGLE_APPLICATION_CREDENTIALS`.

### 2. OAuth2 Provider Setup

Configure your OAuth2 provider:

1. Register application and get client ID/secret
2. Configure redirect URIs:
   - `https://your-domain.com/auth/callback`
   - `https://your-domain.com/api/v1/auth/callback`
3. Enable required scopes: openid, profile, email
4. Note the JWKS endpoint URL

### 3. Communication Channels

**Email (SMTP):**
- Use app-specific passwords for Gmail
- Configure SPF/DKIM for better deliverability

**Slack:**
- Create a Slack app at api.slack.com
- Install to workspace and get bot token
- Add bot to required channels

## Deployment Steps

### 1. Pre-deployment Checks

```bash
# Run all tests
pytest tests/unit -v
pytest tests/integration -v --run-integration

# Verify production readiness
python scripts/verify_production_readiness.py

# Check configuration
python scripts/check_config.py --env production
```

### 2. Start Services

**Using Docker Compose (Recommended):**

```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Manual Start:**

```bash
# Start API server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Start detection agent
python -m src.detection_agent.main

# Start remediation agent
python -m src.remediation_agent.main

# Start communication agent
python -m src.communication_agent.main
```

### 3. Health Checks

```bash
# API health
curl https://your-domain.com/health

# Database health
curl https://your-domain.com/health/db

# All services
curl https://your-domain.com/health/full
```

## Monitoring and Maintenance

### 1. Logging

- All logs go to `/var/log/sentinelops/`
- Use structured logging for easier parsing
- Set up log rotation

### 2. Metrics

Monitor the following:
- API response times
- Database connection pool usage
- Queue lengths
- Error rates
- Authentication failures

### 3. Backups

```bash
# Database backup
pg_dump sentinelops > backup_$(date +%Y%m%d).sql

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env config/
```

### 4. Updates

```bash
# Update code
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run new migrations
alembic upgrade head

# Restart services
docker-compose restart
```

## Security Checklist

- [ ] All secrets in environment variables
- [ ] HTTPS enabled with valid certificates
- [ ] Database connections use SSL
- [ ] OAuth2 properly configured
- [ ] API rate limiting enabled
- [ ] Audit logging configured
- [ ] Backup encryption enabled
- [ ] Firewall rules configured
- [ ] Service accounts use minimal permissions

## Troubleshooting

See individual component guides:
- [Database Schema Guide](database-schema-guide.md)
- [API Persistence Updates](api-persistence-updates.md)
- [OAuth2 Configuration](oauth2-configuration.md)
