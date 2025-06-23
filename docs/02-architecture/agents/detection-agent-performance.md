# Detection Agent Performance Tuning Guide

This guide provides comprehensive strategies for optimizing the performance of the SentinelOps Detection Agent, minimizing resource usage, and maximizing detection efficiency.

## Overview

The Detection Agent's performance depends on several factors:
- BigQuery query optimization
- Resource utilization management
- Caching strategies
- Concurrent processing
- Memory management

This guide covers optimization techniques for each area.

## Query Performance Optimization

### 1. Time Range Optimization

**Problem:** Large time ranges scan excessive data, increasing costs and latency.

**Solutions:**

```yaml
# Limit scan windows
agents:
  detection:
    query_optimization:
      max_scan_days: 3  # Reduce from default 7 days
      enable_time_partitioning: true

    # Use shorter scan intervals for better incremental processing
    scan_interval_seconds: 300  # 5 minutes instead of 60
```

**Implementation Details:**
- Partition pruning reduces data scanned by 80-90%
- Incremental scanning prevents re-processing old data
- Adaptive time windows based on data volume

### 2. Column Selection Optimization

**Problem:** SELECT * queries transfer unnecessary data.

**Solutions:**

```yaml
agents:
  detection:
    query_optimization:
      enable_column_pruning: true
      required_columns:
        - timestamp
        - actor
        - source_ip
        - resource_name
        - method_name
        - status_code
        # Remove unused columns like user_agent, request_metadata
```

**Performance Impact:**
- 40-60% reduction in data transfer
- 20-30% faster query execution
- Reduced memory usage

### 3. Sampling for Large Datasets

**Problem:** Some queries scan millions of rows unnecessarily.

**Solutions:**

```yaml
agents:
  detection:
    query_optimization:
      enable_sampling: true
      sample_percentage: 5  # Start with 5% for large datasets
```

**When to Use Sampling:**
- Historical analysis (> 7 days)
- Pattern detection (not precise counting)
- Exploratory queries
- Non-critical rules

**When NOT to Use Sampling:**
- Compliance reporting
- Precise incident counting
- Critical security rules

### 4. Query Result Limiting

**Problem:** Unbounded result sets consume excessive memory.

**Solutions:**

```yaml
agents:
  detection:
    query_optimization:
      default_limit: 5000  # Reduce from 10000

    performance:
      event_batch_size: 50  # Process in smaller batches
      max_events_in_memory: 5000  # Limit memory usage
```

## Caching Strategies

### 1. Query Result Caching

**Optimal Configuration:**

```yaml
agents:
  detection:
    query_cache:
      enabled: true
      max_entries: 2000  # Increase for high-frequency queries
      default_ttl_minutes: 30  # Shorter TTL for real-time data
      min_hit_count_for_extension: 2  # Extend popular queries sooner
```

**Performance Benefits:**
- 60-80% reduction in repeated queries
- 90% faster response for cached results
- Significant cost savings

**Cache Tuning:**

```python
# Monitor cache performance
def analyze_cache_performance():
    stats = agent.query_cache.get_stats()
    hit_rate = float(stats['hit_rate'].replace('%', ''))

    if hit_rate < 30:
        # Increase cache size or adjust TTL
        recommendations.append("Increase cache size")
    elif hit_rate > 90:
        # Consider increasing TTL
        recommendations.append("Increase TTL for better efficiency")
```

### 2. Interim Results Storage

**Configuration for Complex Rules:**

```yaml
agents:
  detection:
    interim_storage:
      enabled: true
      max_results: 20000  # Increase for complex correlation
      default_ttl_hours: 12  # Shorter for memory efficiency
```

**Use Cases:**
- Multi-stage detection rules
- Cross-rule correlation
- Temporal pattern analysis

### 3. Cache Invalidation Strategy

**Balanced Configuration:**

```yaml
agents:
  detection:
    cache_invalidation:
      enabled: true
      invalidate_on_detection: false  # Keep for performance
      invalidate_on_rule_change: true  # Essential for accuracy
      scheduled_interval_hours: 12  # More frequent cleanup
```

## Resource Utilization Optimization

### 1. Memory Management

**Memory-Optimized Configuration:**

```yaml
agents:
  detection:
    performance:
      max_memory_usage_mb: 1024  # Strict limit
      event_batch_size: 25  # Smaller batches
      max_events_in_memory: 2000  # Conservative limit
      enable_streaming: true  # Process results as they arrive
```

**Memory Monitoring:**

```python
# Monitor memory usage patterns
def optimize_memory_settings(monitoring_data):
    peak_memory = max(monitoring_data['memory_used_mb'])
    avg_memory = sum(monitoring_data['memory_used_mb']) / len(monitoring_data)

    if peak_memory > 1500:  # 1.5GB threshold
        return {
            'event_batch_size': 20,
            'max_events_in_memory': 1000,
            'query_cache_max_entries': 500
        }

    return current_config
```

### 2. CPU Optimization

**CPU-Optimized Configuration:**

```yaml
agents:
  detection:
    performance:
      max_concurrent_queries: 3  # Reduce from default 5
      max_cpu_percent: 70  # Leave headroom for system
      adaptive_intervals: true  # Adjust based on load
```

**CPU Load Balancing:**

```python
# Adaptive query concurrency
def adjust_concurrency(cpu_usage, current_concurrency):
    if cpu_usage > 80:
        return max(1, current_concurrency - 1)
    elif cpu_usage < 50 and current_concurrency < 5:
        return current_concurrency + 1
    return current_concurrency
```

### 3. I/O Optimization

**I/O-Optimized Configuration:**

```yaml
agents:
  detection:
    bigquery:
      connection_pool_size: 5  # Reduce connections
      retry_delay_seconds: 10  # Longer delays to reduce load

    performance:
      query_timeout_seconds: 180  # Shorter timeouts
```

## Concurrent Processing Optimization

### 1. Query Concurrency

**Low-Resource Environment:**
```yaml
agents:
  detection:
    performance:
      max_concurrent_queries: 2
      query_timeout_seconds: 120
```

**High-Resource Environment:**
```yaml
agents:
  detection:
    performance:
      max_concurrent_queries: 8
      query_timeout_seconds: 300
```

**Dynamic Concurrency:**

```python
class AdaptiveConcurrencyManager:
    def __init__(self):
        self.current_concurrency = 3
        self.performance_history = deque(maxlen=20)

    def adjust_based_on_performance(self, execution_time, success_rate):
        self.performance_history.append({
            'time': execution_time,
            'success': success_rate
        })

        if len(self.performance_history) >= 10:
            avg_time = sum(h['time'] for h in self.performance_history) / len(self.performance_history)
            avg_success = sum(h['success'] for h in self.performance_history) / len(self.performance_history)

            if avg_time > 120 or avg_success < 0.9:  # Performance degradation
                self.current_concurrency = max(1, self.current_concurrency - 1)
            elif avg_time < 60 and avg_success > 0.95:  # Good performance
                self.current_concurrency = min(10, self.current_concurrency + 1)
```

### 2. Rule Execution Parallelization

**Parallel Rule Execution:**

```python
async def execute_rules_optimized(rules, start_time, end_time):
    # Group rules by resource requirements
    lightweight_rules = [r for r in rules if r.estimated_cost < 1000]
    heavyweight_rules = [r for r in rules if r.estimated_cost >= 1000]

    # Execute lightweight rules in parallel
    lightweight_tasks = [
        execute_rule(rule, start_time, end_time)
        for rule in lightweight_rules
    ]

    # Execute heavyweight rules sequentially or with limited concurrency
    heavyweight_semaphore = asyncio.Semaphore(2)

    async def execute_heavyweight(rule):
        async with heavyweight_semaphore:
            return await execute_rule(rule, start_time, end_time)

    heavyweight_tasks = [
        execute_heavyweight(rule)
        for rule in heavyweight_rules
    ]

    # Wait for all tasks
    results = await asyncio.gather(
        *lightweight_tasks,
        *heavyweight_tasks,
        return_exceptions=True
    )

    return results
```

## BigQuery Optimization

### 1. Query Structure Optimization

**Optimized Query Patterns:**

```sql
-- GOOD: Partition pruning + early filtering
SELECT timestamp, actor, resource_name, method_name
FROM `project.dataset.audit_logs`
WHERE _PARTITIONTIME >= TIMESTAMP('2024-01-15')
  AND _PARTITIONTIME <= TIMESTAMP('2024-01-16')
  AND timestamp BETWEEN '2024-01-15 10:00:00' AND '2024-01-15 11:00:00'
  AND method_name IN ('SetIamPolicy', 'CreateRole')  -- Selective filter
  AND severity = 'NOTICE'
ORDER BY timestamp DESC
LIMIT 1000

-- BAD: No partition pruning, late filtering
SELECT *
FROM `project.dataset.audit_logs`
WHERE method_name IN ('SetIamPolicy', 'CreateRole')
  AND timestamp BETWEEN '2024-01-15 10:00:00' AND '2024-01-15 11:00:00'
ORDER BY timestamp DESC
```

### 2. Join Optimization

**Optimized Joins:**

```sql
-- GOOD: Filter before join, use clustering
SELECT
  a.timestamp,
  a.actor,
  a.resource_name,
  v.source_ip,
  v.dest_port
FROM (
  SELECT timestamp, actor, resource_name
  FROM `project.dataset.audit_logs`
  WHERE _PARTITIONTIME >= TIMESTAMP('2024-01-15')
    AND method_name = 'CreateInstance'
) a
JOIN (
  SELECT timestamp, source_ip, dest_port, resource_name
  FROM `project.dataset.vpc_flow_logs`
  WHERE _PARTITIONTIME >= TIMESTAMP('2024-01-15')
    AND action = 'ALLOW'
) v
ON a.resource_name = v.resource_name
AND ABS(TIMESTAMP_DIFF(a.timestamp, v.timestamp, SECOND)) < 300
```

### 3. Cost Optimization

**Query Cost Estimation:**

```python
class QueryCostEstimator:
    def __init__(self):
        self.bytes_per_gb_cost = 0.005  # $5 per TB

    def estimate_cost(self, query, time_range_days):
        # Estimate based on table size and time range
        base_table_size_gb = 100  # Estimate per day
        estimated_gb = base_table_size_gb * time_range_days

        # Apply optimization factors
        if "SELECT *" in query:
            optimization_factor = 1.0  # No optimization
        elif "TABLESAMPLE" in query:
            sample_match = re.search(r'TABLESAMPLE SYSTEM \((\d+) PERCENT\)', query)
            if sample_match:
                sample_pct = int(sample_match.group(1))
                optimization_factor = sample_pct / 100
            else:
                optimization_factor = 0.1
        else:
            optimization_factor = 0.3  # Column pruning

        final_gb = estimated_gb * optimization_factor
        estimated_cost = final_gb * self.bytes_per_gb_cost

        return {
            'estimated_gb': final_gb,
            'estimated_cost_usd': estimated_cost,
            'optimization_factor': optimization_factor
        }
```

## Monitoring-Based Optimization

### 1. Performance Metrics Monitoring

**Key Metrics to Track:**

```python
def analyze_performance_metrics(metrics):
    recommendations = []

    # Query performance analysis
    avg_query_time = metrics['query_statistics']['avg_execution_time']
    if avg_query_time > 60:  # 60 seconds threshold
        recommendations.append({
            'area': 'query_performance',
            'issue': 'High query execution time',
            'suggestion': 'Reduce time ranges or increase sampling'
        })

    # Cache performance analysis
    cache_hit_rate = float(metrics['query_statistics']['cache_hit_rate'].replace('%', ''))
    if cache_hit_rate < 40:
        recommendations.append({
            'area': 'caching',
            'issue': 'Low cache hit rate',
            'suggestion': 'Increase cache size or adjust TTL'
        })

    # Resource usage analysis
    peak_memory = metrics['resource_statistics']['memory']['peak_percent']
    if peak_memory > 90:
        recommendations.append({
            'area': 'memory',
            'issue': 'High memory usage',
            'suggestion': 'Reduce batch sizes or enable streaming'
        })

    return recommendations
```

### 2. Automated Performance Tuning

**Self-Optimizing Configuration:**

```python
class AutoPerformanceTuner:
    def __init__(self, initial_config):
        self.config = initial_config
        self.performance_history = []
        self.tuning_enabled = True

    async def auto_tune(self, performance_metrics):
        if not self.tuning_enabled:
            return

        current_performance = self._calculate_performance_score(performance_metrics)

        # Try different configurations
        test_configs = self._generate_test_configs()

        for test_config in test_configs:
            # Test configuration for a short period
            test_metrics = await self._test_configuration(test_config, duration_minutes=10)
            test_performance = self._calculate_performance_score(test_metrics)

            if test_performance > current_performance * 1.1:  # 10% improvement
                self.config.update(test_config)
                self.logger.info(f"Applied auto-tuning: {test_config}")
                break

    def _generate_test_configs(self):
        base_config = self.config.copy()

        return [
            # Test smaller batch sizes
            {**base_config, 'event_batch_size': max(10, base_config['event_batch_size'] // 2)},

            # Test larger cache
            {**base_config, 'query_cache_max_entries': base_config['query_cache_max_entries'] * 2},

            # Test different concurrency
            {**base_config, 'max_concurrent_queries': max(1, base_config['max_concurrent_queries'] - 1)},

            # Test shorter time ranges
            {**base_config, 'max_scan_days': max(1, base_config['max_scan_days'] - 1)}
        ]
```

## Environment-Specific Optimization

### Development Environment
```yaml
# Optimized for development/testing
agents:
  detection:
    scan_interval_seconds: 300
    query_optimization:
      enable_sampling: true
      sample_percentage: 20
    performance:
      max_concurrent_queries: 2
      max_memory_usage_mb: 512
    query_cache:
      max_entries: 100
```

### Staging Environment
```yaml
# Balanced configuration for staging
agents:
  detection:
    scan_interval_seconds: 120
    query_optimization:
      enable_sampling: true
      sample_percentage: 10
    performance:
      max_concurrent_queries: 4
      max_memory_usage_mb: 1024
    query_cache:
      max_entries: 500
```

### Production Environment
```yaml
# Optimized for production performance
agents:
  detection:
    scan_interval_seconds: 60
    query_optimization:
      enable_sampling: false  # Full data for accuracy
      max_scan_days: 1  # Smaller windows, more frequent
    performance:
      max_concurrent_queries: 6
      max_memory_usage_mb: 2048
    query_cache:
      max_entries: 2000
      default_ttl_minutes: 45
```

## Troubleshooting Performance Issues

### High Memory Usage
1. Reduce `event_batch_size`
2. Enable `enable_streaming`
3. Decrease `max_events_in_memory`
4. Clear caches more frequently

### Slow Query Performance
1. Enable sampling for non-critical rules
2. Reduce `max_scan_days`
3. Optimize query filters
4. Check BigQuery slot availability

### High BigQuery Costs
1. Enable aggressive sampling
2. Implement stricter resource filters
3. Use shorter scan intervals with smaller windows
4. Cache more aggressively

### Low Cache Hit Rates
1. Increase cache size
2. Extend TTL for stable data
3. Review query patterns
4. Consider pre-warming cache

This performance tuning guide provides the tools and strategies needed to optimize the Detection Agent for any environment and workload.
