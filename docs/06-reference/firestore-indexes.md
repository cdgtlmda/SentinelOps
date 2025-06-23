# Firestore Index Management

This document describes the Firestore indexes required by the SentinelOps Orchestrator Agent.

## Index Deployment

To deploy the indexes defined in `firestore.indexes.json`, run:

```bash
firebase deploy --only firestore:indexes
```

Or using gcloud:

```bash
gcloud firestore indexes create --collection-group=incidents --field-config=field-path=status,order=ascending --field-config=field-path=created_at,order=descending
```

## Index Descriptions

### 1. Status and Creation Time Index
- **Purpose**: Query active incidents sorted by creation time
- **Fields**: `status` (ASC), `created_at` (DESC)
- **Usage**: Used in `_recover_active_incidents()` and status-based queries

### 2. Status Array Contains Index
- **Purpose**: Query incidents with status in a list of values
- **Fields**: `status` (ARRAY_CONTAINS)
- **Usage**: Used to find all active incidents efficiently

### 3. Severity and Creation Time Index
- **Purpose**: Query incidents by severity level
- **Fields**: `severity` (DESC), `created_at` (DESC)
- **Usage**: Used for priority-based incident handling

### 4. Assignment and Status Index
- **Purpose**: Query incidents assigned to specific users
- **Fields**: `assigned_to` (ASC), `status` (ASC)
- **Usage**: Used for workload distribution queries

### 5. Workflow Status Index
- **Purpose**: Track incidents by workflow state
- **Fields**: `audit.workflow_status` (ASC), `updated_at` (DESC)
- **Usage**: Used in timeout and stuck incident detection

## Index Monitoring

Monitor index usage and performance in the Firebase Console:
1. Go to Firestore Database
2. Click on "Indexes" tab
3. Review index usage statistics

## Best Practices

1. **Composite Indexes**: Always create composite indexes for queries with multiple fields
2. **Array Fields**: Use ARRAY_CONTAINS for fields that store arrays (like tags)
3. **Exemptions**: Some fields may need single-field index exemptions
4. **Testing**: Test queries in development before deploying to production
