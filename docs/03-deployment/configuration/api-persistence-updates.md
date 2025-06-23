# API Documentation - Database Persistence Updates

## Overview

All API endpoints have been updated to use database persistence instead of in-memory storage. This document outlines the changes and new patterns used across the API.

## Key Changes

### 1. Repository Pattern Implementation

All endpoints now use repository classes for database operations:

- `RulesRepository` - Handles all rule-related database operations
- `IncidentsRepository` - Handles all incident-related database operations

### 2. Database Session Management

Each endpoint receives a database session through dependency injection:

```python
@router.get("/api/v1/rules")
async def list_rules(
    db: AsyncSession = Depends(get_db),
    auth_token: AuthToken = Depends(require_auth)
):
    repo = RulesRepository(db)
    rules, total = await repo.list_rules(...)
```

## Updated Endpoints

### Rules API (`/api/v1/rules`)

All rule endpoints now interact with the PostgreSQL database:

| Endpoint | Method | Database Operation |
|----------|---------|-------------------|
| `/api/v1/rules` | GET | `repo.list_rules()` with pagination |
| `/api/v1/rules/{id}` | GET | `repo.get_by_id()` |
| `/api/v1/rules` | POST | `repo.create()` with auto-generated rule_number |
| `/api/v1/rules/{id}` | PUT | `repo.update()` with version increment |
| `/api/v1/rules/{id}` | DELETE | `repo.delete()` |
| `/api/v1/rules/{id}/enable` | POST | `repo.update()` to set enabled=True |
| `/api/v1/rules/{id}/disable` | POST | `repo.update()` to set enabled=False |
| `/api/v1/rules/{id}/test` | POST | Fetches rule from DB, simulates execution |
| `/api/v1/rules/{id}/clone` | POST | Creates new rule based on existing |

### Incidents API (`/api/v1/incidents`)

All incident endpoints use database persistence:

| Endpoint | Method | Database Operation |
|----------|---------|-------------------|
| `/api/v1/incidents` | GET | `repo.list_incidents()` with filters |
| `/api/v1/incidents/{id}` | GET | `repo.get_by_id()` |
| `/api/v1/incidents` | POST | `repo.create()` with auto-generated number || `/api/v1/incidents/{id}` | PUT | `repo.update()` with timeline tracking |
| `/api/v1/incidents/{id}` | DELETE | `repo.delete()` |
| `/api/v1/incidents/{id}/timeline` | POST | Appends to timeline array |
| `/api/v1/incidents/{id}/assign` | POST | Updates assigned_to field |
| `/api/v1/incidents/{id}/merge/{target_id}` | POST | Merges incidents, updates references |

## Transaction Management

All database operations are wrapped in transactions:

```python
async with db.begin():
    # All operations here are in a transaction
    rule = await repo.create(rule_model)
    await repo.update_metrics(rule.id, metrics)
    # Automatically commits on success, rolls back on error
```

## Error Handling

Database errors are properly handled and returned as HTTP errors:

- `404 Not Found` - When resource doesn't exist in database
- `409 Conflict` - When unique constraints are violated
- `500 Internal Server Error` - For database connection issues

## Performance Optimizations

1. **Pagination**: All list endpoints support pagination to limit database load
2. **Selective field loading**: Only required fields are fetched
3. **Connection pooling**: Reuses database connections
4. **Async operations**: Non-blocking database queries

## Migration from In-Memory Storage

The following in-memory patterns have been completely removed:

❌ **Removed:**
```python
# Old in-memory storage
_rules: Dict[str, Rule] = {}
_incidents: Dict[str, Incident] = {}
```

✅ **Replaced with:**
```python
# Database repository pattern
repo = RulesRepository(db)
rules = await repo.list_rules()
```

## Testing

All endpoints have comprehensive tests that verify:

1. Database operations are used (no in-memory storage)
2. Repository pattern is properly implemented
3. Transactions work correctly
4. Error handling is appropriate

See `tests/unit/api/` for endpoint-specific tests.
