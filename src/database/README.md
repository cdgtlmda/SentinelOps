# SentinelOps Database Module

This module provides the database infrastructure for SentinelOps production deployment.

## Structure

```
src/database/
├── __init__.py          # Package initialization
├── base.py              # Database configuration and session management
├── models/              # SQLAlchemy models
│   ├── __init__.py
│   ├── rules.py         # Rules table model
│   └── incidents.py     # Incidents table model
├── repositories/        # Database repositories for business logic
│   ├── __init__.py
│   ├── rules.py         # Rules repository
│   └── incidents.py     # Incidents repository
├── migrations/          # Alembic migrations
│   ├── env.py          # Alembic environment config
│   ├── script.py.mako  # Migration template
│   └── versions/       # Migration files
└── utils.py            # Database utilities
```

## Setup

1. **Install dependencies** (already added to requirements.txt):
   ```bash
   pip install sqlalchemy alembic asyncpg
   ```

2. **Set environment variable**:
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/sentinelops"
   ```

3. **Initialize database**:
   ```python
   from src.database.utils import initialize_database
   
   # Run this once to set up the database
   await initialize_database()
   ```

## Usage

### Using the Repository Pattern

```python
from src.database.base import get_db_context
from src.database.repositories.rules import RulesRepository
from src.api.models.rules import RuleCreate

# Create a rule
async with get_db_context() as db:
    repo = RulesRepository(db)
    rule_data = RuleCreate(
        name="Suspicious Login",
        description="Detect suspicious login attempts",
        rule_type="pattern",
        severity="high",
        # ... other fields
    )
    rule = await repo.create(rule_data, created_by="user@example.com", rule_number="RULE-000001")

# Create an incident
from src.database.repositories.incidents import IncidentsRepository
from src.api.models.incidents import IncidentCreate, IncidentSource

async with get_db_context() as db:
    repo = IncidentsRepository(db)
    incident_data = IncidentCreate(
        title="Suspicious Login Activity",
        description="Multiple failed login attempts detected",
        incident_type="suspicious_activity",
        severity="high",
        source=IncidentSource(
            system="Detection Agent",
            rule_id="rule-123",
            confidence=0.85
        ),
        # ... other fields
    )
    incident = await repo.create(incident_data, created_by="system", incident_number="INC-000001")
```

### Using with FastAPI

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.base import get_db
from src.database.repositories.rules import RulesRepository

@router.get("/rules")
async def list_rules(db: AsyncSession = Depends(get_db)):
    repo = RulesRepository(db)
    rules, total = await repo.list_rules()
    return {"rules": rules, "total": total}

@router.get("/incidents")
async def list_incidents(db: AsyncSession = Depends(get_db)):
    repo = IncidentsRepository(db)
    incidents, total = await repo.list_incidents()
    return {"incidents": incidents, "total": total}
```

## Migrations

### Create a new migration

```bash
# Auto-generate migration based on model changes
alembic revision --autogenerate -m "Add new column to rules"

# Or create empty migration
alembic revision -m "Custom migration"
```

### Run migrations

```bash
# Upgrade to latest
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# View migration history
alembic history
```

## Database Schema

### Rules Table

The rules table stores detection rules with the following columns:

- `id` (UUID): Primary key
- `rule_number` (String): Unique human-readable identifier (e.g., RULE-000001)
- `name` (String): Rule name
- `description` (Text): Rule description
- `rule_type` (Enum): Type of rule (query, pattern, threshold, etc.)
- `severity` (Enum): Severity level (critical, high, medium, low, info)
- `status` (Enum): Rule status (active, inactive, testing, etc.)
- `query` (Text): SQL query for query-based rules
- `conditions` (JSON): Conditions for pattern-based rules
- `threshold` (JSON): Threshold configuration
- `correlation` (JSON): Correlation configuration
- `enabled` (Boolean): Whether rule is enabled
- `tags` (JSON): Array of tags
- `references` (JSON): External references
- `false_positive_rate` (Float): Estimated false positive rate
- `actions` (JSON): Actions to take when triggered
- `custom_fields` (JSON): Custom metadata
- `created_at` (Timestamp): Creation time
- `updated_at` (Timestamp): Last update time
- `last_executed` (Timestamp): Last execution time
- `created_by` (String): User who created the rule
- `updated_by` (String): User who last updated the rule
- `version` (Integer): Rule version number
- `metrics` (JSON): Performance metrics
- `parent_rule_id` (UUID): Reference to parent rule
- `related_rules` (JSON): Array of related rule IDs

### Incidents Table

The incidents table stores security incidents with the following columns:

- `id` (UUID): Primary key
- `incident_number` (String): Unique human-readable identifier (e.g., INC-000001)
- `title` (String): Incident title
- `description` (Text): Incident description
- `incident_type` (Enum): Type of incident (unauthorized_access, data_breach, etc.)
- `severity` (Enum): Severity level (critical, high, medium, low, info)
- `priority` (Enum): Priority level (critical, high, medium, low)
- `status` (Enum): Incident status (open, investigating, contained, etc.)
- `external_id` (String): External system reference
- `tags` (JSON): Array of tags
- `custom_fields` (JSON): Custom metadata
- `created_at` (Timestamp): Creation time
- `updated_at` (Timestamp): Last update time
- `detected_at` (Timestamp): Detection time
- `resolved_at` (Timestamp): Resolution time (nullable)
- `source` (JSON): Detection source information
- `actors` (JSON): Array of actors involved
- `assets` (JSON): Array of affected assets
- `timeline` (JSON): Array of timeline entries
- `analysis` (JSON): Analysis results (nullable)
- `remediation_actions` (JSON): Array of remediation actions
- `created_by` (String): User who created the incident
- `updated_by` (String): User who last updated the incident
- `assigned_to` (String): Assigned user/team (nullable)
- `time_to_detect` (Float): Time to detect in seconds
- `time_to_respond` (Float): Time to respond in seconds
- `time_to_resolve` (Float): Time to resolve in seconds
- `parent_incident_id` (UUID): Reference to parent incident
- `related_incidents` (JSON): Array of related incident IDs

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `DATABASE_ECHO`: Set to "true" to enable SQL query logging

## Notes

- The database uses PostgreSQL with asyncpg driver for async operations
- All timestamps are stored with timezone information
- JSON columns are used for flexible schema evolution
- Proper indexes are created for common query patterns