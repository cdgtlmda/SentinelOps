# Database Connection Pool Configuration

This document describes the database connection pool configuration for SentinelOps in production environments.

## Overview

SentinelOps uses SQLAlchemy with asyncpg driver for PostgreSQL connections. The connection pool is configured to handle high-throughput production workloads with proper health monitoring and metrics collection.

## Configuration

### Environment Variables

The following environment variables control the database connection pool:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://sentinelops:sentinelops@localhost:5432/sentinelops` | Full database connection URL |
| `APP_ENV` | `development` | Environment (development/production) |
| `DB_POOL_SIZE` | `20` | Number of connections to maintain in pool |
| `DB_MAX_OVERFLOW` | `10` | Maximum overflow connections beyond pool_size |
| `DB_POOL_TIMEOUT` | `30.0` | Seconds to wait before connection timeout |
| `DB_POOL_RECYCLE` | `3600` | Recycle connections after N seconds (1 hour) |
| `DB_POOL_PRE_PING` | `true` | Test connections before using |
| `DB_CONNECT_TIMEOUT` | `10` | Connection timeout in seconds |
| `DB_COMMAND_TIMEOUT` | `None` | Command timeout in seconds (optional) |
| `DB_POOL_USE_LIFO` | `true` | Use LIFO to prefer recently used connections |
| `DB_ECHO_POOL` | `false` | Echo pool checkouts/checkins (verbose logging) |
| `DB_QUERY_CACHE_SIZE` | `1200` | Number of queries to cache |
| `DB_USE_INSERTMANYVALUES` | `true` | Use efficient bulk inserts |
| `DB_MONITOR_ENABLED` | `true` | Enable connection pool monitoring |
| `DATABASE_ECHO` | `false` | Echo all SQL statements (debug only) |


## Production Configuration

For production environments, use these recommended settings:

```bash
# Core pool settings
export DB_POOL_SIZE=20              # Adjust based on expected concurrent connections
export DB_MAX_OVERFLOW=10           # Allow temporary spike handling
export DB_POOL_TIMEOUT=30.0         # Fail fast on connection issues
export DB_POOL_RECYCLE=3600         # Recycle every hour to avoid stale connections
export DB_POOL_PRE_PING=true       # Always test connections

# Performance settings
export DB_QUERY_CACHE_SIZE=1200     # Cache frequently used queries
export DB_USE_INSERTMANYVALUES=true # Optimize bulk operations
export DB_POOL_USE_LIFO=true        # Prefer warm connections

# Monitoring
export DB_MONITOR_ENABLED=true      # Enable pool monitoring
export DB_ECHO_POOL=false           # Disable verbose logging
```

## Connection Pool Sizing

To determine the appropriate pool size:

1. **Calculate Base Pool Size**:
   ```
   pool_size = (number_of_workers × average_connections_per_worker)
   ```

2. **Add Buffer for Spikes**:
   ```
   max_overflow = pool_size × 0.5
   ```

3. **Example for Production**:
   - 4 API workers
   - 5 average connections per worker
   - Base pool_size = 20
   - max_overflow = 10
   - Total max connections = 30


## Monitoring

### Health Check Endpoint

The database health is automatically included in the main health check:

```bash
GET /api/v1/health
```

Response includes database status:
```json
{
  "status": "healthy",
  "components": {
    "database": {
      "status": "healthy",
      "message": "Database is healthy",
      "metadata": {
        "query_time_ms": 2.5,
        "pool_health": {
          "status": "healthy",
          "checks": {
            "connection": {"status": "pass", "time_ms": 2.5},
            "pool_saturation": {"status": "pass", "utilization": 25.0},
            "slow_queries": {"status": "pass", "rate": 0.5}
          }
        }
      }
    }
  }
}
```

### Pool Status Endpoint

Get detailed pool metrics:

```bash
GET /api/v1/database/pool/status
```

Response:
```json
{
  "pool_class": "QueuePool",
  "metrics": {
    "connections": {
      "active": 5,
      "idle": 15,
      "total": 20,
      "overflow": 0,
      "failed": 0
    },
    "performance": {
      "avg_connection_time_ms": 12.5,
      "avg_query_time_ms": 3.2,
      "slow_queries": 2
    },
    "events": {
      "checkouts": 1523,
      "checkins": 1518,
      "connects": 20,
      "disconnects": 0
    }
  },
  "pool_config": {
    "size": 20,
    "timeout": 30.0,
    "recycle": 3600,
    "pre_ping": true
  }
}
```


### Pool Health Endpoint

Check pool health status:

```bash
GET /api/v1/database/pool/health
```

### Reset Metrics

Reset accumulated metrics:

```bash
POST /api/v1/database/pool/reset-metrics
```

## Troubleshooting

### High Connection Pool Utilization

Symptoms:
- Pool saturation warnings in health checks
- Connection timeouts
- Slow API responses

Solutions:
1. Increase `DB_POOL_SIZE` and `DB_MAX_OVERFLOW`
2. Check for connection leaks (connections not being closed)
3. Optimize long-running queries
4. Add read replicas for read-heavy workloads

### Connection Recycling Issues

Symptoms:
- "connection has been closed" errors
- Intermittent connection failures

Solutions:
1. Adjust `DB_POOL_RECYCLE` based on your database's connection timeout
2. Ensure `DB_POOL_PRE_PING=true` for production
3. Check database logs for connection limits

### Slow Query Performance

Symptoms:
- High slow_queries count in metrics
- Degraded health status

Solutions:
1. Enable query logging: `log_min_duration_statement` in PostgreSQL
2. Add appropriate indexes
3. Use query optimization tools
4. Consider connection pooling at database level (PgBouncer)

## Best Practices

1. **Monitor Pool Metrics**: Regularly check pool utilization and adjust sizing
2. **Set Appropriate Timeouts**: Balance between failing fast and allowing legitimate slow operations
3. **Use Connection Pooling**: Always use the provided session management functions
4. **Handle Connection Errors**: Implement retry logic for transient connection issues
5. **Regular Health Checks**: Monitor `/api/v1/health` endpoint in production
6. **Capacity Planning**: Plan pool size based on expected load and growth

## Integration with Monitoring Systems

The pool metrics can be integrated with monitoring systems:

```python
# Prometheus metrics example
from prometheus_client import Gauge

# Create gauges for pool metrics
pool_active_connections = Gauge('db_pool_active_connections', 'Active database connections')
pool_utilization = Gauge('db_pool_utilization_percent', 'Pool utilization percentage')

# Update metrics (in your monitoring code)
status = get_pool_status()
metrics = status['metrics']['connections']
pool_active_connections.set(metrics['active'])
pool_utilization.set((metrics['active'] / metrics['total']) * 100)
```

## Security Considerations

1. **Connection String Security**: Store `DATABASE_URL` in secure secret management
2. **SSL/TLS**: Use SSL connections in production: `postgresql+asyncpg://user:pass@host/db?ssl=require`
3. **Connection Limits**: Set database-level connection limits to prevent DoS
4. **Monitoring Access**: Restrict access to pool monitoring endpoints in production
