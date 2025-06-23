# Database Schema and Migration Guide

## Overview

SentinelOps uses PostgreSQL as its primary database with Alembic for schema migrations. The database layer has been fully implemented to replace all in-memory storage with persistent, production-ready data storage.

## Database Schema

### Rules Table

The `rules` table stores all detection rules with the following schema:

```sql
CREATE TABLE rules (
    id UUID PRIMARY KEY,
    rule_number VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    rule_type ENUM('query', 'pattern', 'threshold', 'anomaly', 'correlation', 'custom') NOT NULL,
    severity ENUM('critical', 'high', 'medium', 'low', 'info') NOT NULL,
    status ENUM('active', 'inactive', 'testing', 'disabled', 'deprecated') NOT NULL,
    query TEXT,
    conditions JSON,
    threshold JSON,
    correlation JSON,
    enabled BOOLEAN NOT NULL,
    tags JSON NOT NULL,
    references JSON NOT NULL,    false_positive_rate FLOAT,
    actions JSON NOT NULL,
    custom_fields JSON NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_executed TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255) NOT NULL,
    updated_by VARCHAR(255) NOT NULL,
    version INTEGER NOT NULL,
    metrics JSON NOT NULL,
    parent_rule_id UUID REFERENCES rules(id),
    related_rules JSON NOT NULL
);
```

### Incidents Table

The `incidents` table stores security incidents with the following schema:

```sql
CREATE TABLE incidents (
    id UUID PRIMARY KEY,
    incident_number VARCHAR(20) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    incident_type ENUM('unauthorized_access', 'data_breach', 'malware', 
                      'dos_attack', 'policy_violation', 'suspicious_activity', 'other') NOT NULL,
    severity ENUM('critical', 'high', 'medium', 'low', 'info') NOT NULL,
    priority ENUM('low', 'medium', 'high', 'critical') NOT NULL,    status ENUM('open', 'investigating', 'contained', 'remediated', 'closed', 'false_positive') NOT NULL,
    external_id VARCHAR(255),
    tags JSON NOT NULL,
    custom_fields JSON NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    source JSON NOT NULL,
    actors JSON NOT NULL,
    assets JSON NOT NULL,
    timeline JSON NOT NULL,
    analysis JSON,
    remediation_actions JSON NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    updated_by VARCHAR(255) NOT NULL,
    assigned_to VARCHAR(255),
    time_to_detect FLOAT,
    time_to_respond FLOAT,
    time_to_resolve FLOAT,
    parent_incident_id UUID REFERENCES incidents(id),
    related_incidents JSON NOT NULL
);
```

## Migration Process

### Initial Setup

1. Install Alembic (included in requirements):
```bash
pip install -r requirements.txt
```

2. Configure database connection in `.env`:
```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
```

### Running Migrations

1. **Apply all migrations:**
```bash
cd src/database
alembic upgrade head
```

2. **Create a new migration:**
```bash
alembic revision -m "description of changes"
```

3. **Check migration status:**
```bash
alembic current
```

4. **Rollback migrations:**
```bash
alembic downgrade -1  # Rollback one migration
alembic downgrade base  # Rollback all migrations
```

### Migration Files

Migrations are stored in `src/database/migrations/versions/`:
- `001_create_rules_table.py` - Creates the rules table with all fields- `002_create_incidents_table.py` - Creates the incidents table with relationships

## Connection Pool Configuration

The database uses production-ready connection pooling with the following defaults:

```python
# src/database/pool_config.py
pool_size = 20          # Number of persistent connections
max_overflow = 10       # Additional connections when needed
pool_timeout = 30.0     # Seconds to wait for connection
pool_recycle = 3600     # Recycle connections after 1 hour
pool_pre_ping = True    # Test connections before use
```

## Repository Pattern

All database operations use the repository pattern:

```python
# Example usage
from src.database.repositories import RulesRepository
from src.database.base import get_db

async with get_db() as db:
    repo = RulesRepository(db)
    rules, total = await repo.list_rules(page=1, page_size=10)
```

## Performance Considerations

1. **Indexes**: Primary keys and unique constraints are automatically indexed
2. **Connection pooling**: Reduces connection overhead
3. **Async operations**: All database operations are asynchronous
4. **Query optimization**: Use pagination for large result sets
