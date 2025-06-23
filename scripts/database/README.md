# Database Migrations Guide

This guide explains how to manage database migrations for the SentinelOps project.

## Overview

SentinelOps uses Alembic for database migrations with PostgreSQL as the backend. The migration system is designed to work with async SQLAlchemy and provides both automated and manual migration capabilities.

## Migration Files

Current migration files:
- `001_create_rules_table.py` - Creates the rules table with all necessary columns and indexes
- `002_create_incidents_table.py` - Creates the incidents table with relationships and indexes

## Using the Migration Management Script

The `scripts/database/manage_migrations.py` script provides a comprehensive interface for managing migrations.

### Prerequisites

1. Ensure PostgreSQL is running:
   ```bash
   # Check if PostgreSQL is running
   pg_isready
   
   # Start PostgreSQL if needed (macOS)
   brew services start postgresql
   ```

2. Set the DATABASE_URL environment variable:
   ```bash
   export DATABASE_URL="postgresql://sentinelops:sentinelops@localhost:5432/sentinelops"
   ```


### Commands

#### Initialize Database
Creates the database if it doesn't exist and runs all migrations:
```bash
python scripts/database/manage_migrations.py init
```

#### Check Database Connection
Verify that the database is accessible:
```bash
python scripts/database/manage_migrations.py check
```

#### Check Migration Status
View current database revision and pending migrations:
```bash
python scripts/database/manage_migrations.py status
```

#### Run Migrations
Apply all pending migrations:
```bash
python scripts/database/manage_migrations.py upgrade
```

Run migrations to a specific revision:
```bash
python scripts/database/manage_migrations.py upgrade --target <revision>
```

#### Rollback Migrations
Rollback the last migration:
```bash
python scripts/database/manage_migrations.py downgrade
```

Rollback multiple migrations:
```bash
python scripts/database/manage_migrations.py downgrade --steps 2
```


#### Create New Migration
Create a new migration with auto-detection of model changes:
```bash
python scripts/database/manage_migrations.py create "add user table"
```

Create a manual migration without auto-detection:
```bash
python scripts/database/manage_migrations.py create "custom migration" --no-autogenerate
```

#### View Migration History
Display all migrations:
```bash
python scripts/database/manage_migrations.py history
```

#### Verify Migrations
Check that all migrations can be applied cleanly:
```bash
python scripts/database/manage_migrations.py verify
```

## Direct Alembic Commands

You can also use Alembic directly from the project root:

```bash
# Show current revision
alembic current

# Upgrade to latest
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# Downgrade one revision
alembic downgrade -1
```


## Migration Best Practices

1. **Always create a backup before running migrations in production**
   ```bash
   pg_dump sentinelops > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Test migrations in a development environment first**
   ```bash
   # Create a test database
   createdb sentinelops_test
   
   # Run migrations on test database
   DATABASE_URL="postgresql://user:pass@localhost/sentinelops_test" \
     python scripts/database/manage_migrations.py init
   ```

3. **Review generated migrations before applying**
   - Check the generated migration file in `src/database/migrations/versions/`
   - Ensure the upgrade and downgrade functions are correct
   - Test both upgrade and downgrade paths

4. **Use descriptive migration messages**
   - Good: `"add_email_verification_to_users"`
   - Bad: `"update_table"`

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
systemctl status postgresql  # Linux
brew services list          # macOS

# Test connection
psql -U sentinelops -d sentinelops -h localhost
```

### Migration Conflicts
If you encounter migration conflicts:
1. Check current revision: `alembic current`
2. Check migration history: `alembic history`
3. Manually resolve conflicts in the migration files
4. Update the revision identifiers if needed

### Reset Migrations (Development Only)
```bash
# Drop and recreate database
dropdb sentinelops
createdb sentinelops

# Run migrations from scratch
python scripts/database/manage_migrations.py init
```

## Environment Variables

- `DATABASE_URL`: Full database connection string
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: sentinelops)
- `DB_USER`: Database user (default: sentinelops)
- `DB_PASSWORD`: Database password (default: sentinelops)

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
