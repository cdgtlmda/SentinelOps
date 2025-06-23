# Detection Agent Architecture Guide

This document provides a comprehensive overview of the Detection Agent's technical architecture, components, and data flow patterns.

## Overview

The Detection Agent is a sophisticated security monitoring system that continuously scans Google Cloud logs and identifies potential security incidents. It's built with a modular architecture that emphasizes performance, scalability, and reliability.

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Detection Agent                            │
├─────────────────────────────────────────────────────────────────┤
│                    Agent Controller                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Query Builder  │  │ Rules Engine    │  │ Event Processor │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                   Performance Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Query Optimizer │  │ Query Cache     │  │ Quota Manager   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    Processing Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │Event Correlator │  │ Incident Dedup  │  │ Scan Manager    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    Data Access Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ BigQuery Client │  │ Pagination Mgr  │  │ Resource Filter │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                   Monitoring & Metrics                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Performance Mon │  │ Resource Monitor│  │ Error Tracking  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Agent Controller (`agent.py`)

The main orchestrator that coordinates all agent activities:

- **Lifecycle Management**: Handles agent startup, shutdown, and resource cleanup
- **Scan Orchestration**: Manages periodic scanning cycles and rule execution
- **Message Handling**: Processes requests from the orchestration agent
- **State Management**: Tracks scan progress and system state

**Key Responsibilities:**
- Initialize all subsystems and dependencies
- Execute detection rules on scheduled intervals
- Handle custom log queries from other agents
- Publish detected incidents to the orchestration agent
- Manage agent configuration and runtime parameters

### 2. Rules Engine (`rules_engine.py`)

Manages and executes detection rules against log data:

- **Rule Loading**: Dynamically loads detection rules from configuration
- **Rule Validation**: Ensures rule syntax and logic are correct
- **Rule Execution**: Executes enabled rules against log sources
- **Rule State Management**: Tracks rule status and execution history

**Built-in Rules:**
- Suspicious login detection
- Privilege escalation monitoring
- Data exfiltration detection
- Resource modification tracking
- Firewall change detection
- VPC suspicious activity

### 3. Query Builder (`query_builder.py`)

Constructs optimized BigQuery SQL for different log sources:

- **Template Management**: Maintains query templates for each log type
- **Parameter Injection**: Safely injects parameters into query templates
- **Query Validation**: Validates generated queries before execution
- **Dynamic Query Construction**: Builds queries based on rule requirements

**Supported Log Types:**
- Google Cloud Audit Logs
- VPC Flow Logs
- Firewall Logs
- IAM Audit Logs
- Data Access Logs

### 4. Performance Optimization Layer

#### Query Optimizer (`query_optimizer.py`)
Optimizes queries for better BigQuery performance:

- **Time Range Optimization**: Limits scan windows to reduce data processed
- **Column Pruning**: Removes unnecessary columns from SELECT statements
- **Partition Optimization**: Leverages BigQuery partitioning for faster scans
- **Join Optimization**: Optimizes join order and adds appropriate hints
- **Clustering Optimization**: Optimizes filters for clustered columns

#### Query Cache (`query_cache.py`)
Caches frequently used query results:

- **Intelligent Caching**: Caches based on query parameters and time windows
- **TTL Management**: Automatic expiration of stale cached results
- **Hit Rate Optimization**: Tracks and optimizes cache hit rates
- **Memory Management**: Limits cache size to prevent memory issues

#### Quota Manager (`quota_manager.py`)
Manages BigQuery resource consumption:

- **Quota Tracking**: Monitors daily and per-minute quota usage
- **Rate Limiting**: Prevents quota exceeded errors through throttling
- **Cost Estimation**: Estimates query costs before execution
- **Backoff Strategies**: Implements exponential backoff on quota limits

### 5. Event Processing Layer

#### Event Correlator (`event_correlator.py`)
Groups related security events into incidents:

- **Time-Based Correlation**: Groups events within time windows
- **Actor-Based Correlation**: Correlates events by user or service account
- **Resource-Based Correlation**: Groups events affecting the same resources
- **Pattern Recognition**: Identifies common attack patterns

#### Incident Deduplicator (`incident_deduplicator.py`)
Prevents duplicate incident creation:

- **Similarity Detection**: Uses multiple algorithms to detect similar incidents
- **Merging Logic**: Intelligently merges related incidents
- **Temporal Windows**: Deduplicates within configurable time windows
- **State Tracking**: Maintains history for accurate deduplication

### 6. Data Access Layer

#### Paginated Query Executor (`query_pagination.py`)
Handles large result sets efficiently:

- **Streaming Results**: Processes results without loading all into memory
- **Configurable Page Sizes**: Optimizes based on query characteristics
- **Error Handling**: Robust handling of pagination errors and timeouts
- **Progress Tracking**: Provides progress updates for long-running queries

#### Resource Filter (`resource_filter.py`)
Filters resources based on configuration:

- **Project Filtering**: Include/exclude specific GCP projects
- **Regional Filtering**: Focus on specific regions or zones
- **Label-Based Filtering**: Filter based on resource labels
- **Pattern Matching**: Support for regex patterns and wildcards

### 7. Monitoring and Metrics (`monitoring.py`)

Comprehensive performance and health monitoring:

- **Rule Metrics**: Tracks execution time, success rate, and detection counts
- **Query Metrics**: Monitors query performance and resource usage
- **System Metrics**: Tracks CPU, memory, and I/O usage
- **Error Tracking**: Categorizes and tracks different error types

## Data Flow

### 1. Initialization Flow

```
Agent Startup → Load Configuration → Initialize Components →
Validate Rules → Start Monitoring → Begin Scan Cycles
```

### 2. Detection Flow

```
Scan Trigger → Rule Selection → Query Building → Query Optimization →
BigQuery Execution → Result Processing → Event Creation →
Event Correlation → Incident Generation → Deduplication →
Incident Publishing
```

### 3. Query Processing Flow

```
Rule Execution → Query Template → Parameter Injection →
Optimization → Cache Check → BigQuery Execution →
Result Pagination → Event Processing → Metrics Recording
```

## Component Interactions

### Query Execution Pipeline

1. **Rules Engine** selects enabled rules for execution
2. **Query Builder** constructs SQL queries from rule definitions
3. **Query Optimizer** optimizes queries for performance
4. **Query Cache** checks for cached results
5. **Quota Manager** validates resource availability
6. **Paginated Executor** executes and streams results
7. **Event Processor** creates SecurityEvent objects
8. **Monitoring** records performance metrics

### Incident Creation Pipeline

1. **Event Correlator** groups related security events
2. **Incident Generator** creates incident objects
3. **Incident Deduplicator** checks for duplicates
4. **Publisher** sends incidents to orchestration agent
5. **State Manager** updates tracking information

## Configuration Architecture

The agent uses a hierarchical configuration system:

```yaml
agents:
  detection:
    # Core settings
    enabled_rules: []
    scan_interval_seconds: 60

    # Performance tuning
    query_optimization:
      enable_time_partitioning: true
      max_scan_days: 7
      default_limit: 10000

    # Caching configuration
    query_cache:
      enabled: true
      max_entries: 1000
      default_ttl_minutes: 60

    # Monitoring settings
    monitoring:
      enabled: true
      retention_hours: 24
      resource_sample_interval: 60
```

## Scaling Considerations

### Horizontal Scaling
- Multiple agent instances can run simultaneously
- Each instance handles a subset of rules or projects
- Load balancing through project-based sharding

### Vertical Scaling
- Configurable concurrency limits
- Memory usage optimization through streaming
- CPU optimization through query result caching

### Performance Optimization
- Incremental scanning reduces redundant work
- Query optimization minimizes BigQuery costs
- Caching reduces redundant query execution
- Resource filtering limits scope of operations

## Error Handling and Resilience

### Error Recovery
- Automatic retry with exponential backoff
- Graceful degradation when quotas are exceeded
- Circuit breaker patterns for external dependencies
- Comprehensive error logging and alerting

### State Recovery
- Persistent tracking of scan progress
- Recovery from partial failures
- Idempotent operations where possible
- State validation on startup

## Security Considerations

### Access Control
- Minimal required BigQuery permissions
- Read-only access to log data
- No modification capabilities
- Service account key rotation support

### Data Protection
- Sensitive data redaction in logs
- Encrypted data transmission
- Secure credential storage
- Audit logging of all operations

## Extension Points

### Custom Rules
- Plugin architecture for custom detection rules
- Standardized rule definition format
- Dynamic rule loading and reloading
- Rule testing and validation framework

### Custom Data Sources
- Extensible query builder for new log types
- Pluggable data source adapters
- Standardized event format
- Custom correlation logic

This architecture provides a robust, scalable, and maintainable foundation for security event detection while maintaining high performance and reliability standards.
