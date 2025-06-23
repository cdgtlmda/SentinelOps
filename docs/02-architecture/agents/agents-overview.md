# SentinelOps Agents Documentation

**Last Updated**: June 11, 2025

This directory contains detailed documentation for each agent in the SentinelOps platform.

## Agent Overview

SentinelOps employs five specialized agents that work together to provide comprehensive cloud security:

1. **[Detection Agent](./detection-agent.md)** - Continuously monitors cloud resources for security threats
2. **[Analysis Agent](./analysis-agent.md)** - Uses AI to analyze and prioritize detected threats
3. **[Remediation Agent](./remediation-agent.md)** - Automatically remediates security issues
4. **[Communication Agent](./communication-agent.md)** - Manages notifications and alerts
5. **[Orchestration Agent](./orchestration-agent.md)** - Coordinates all agents and manages workflows

## Agent Architecture

Each agent follows a common architecture:

```
┌─────────────────────────────────────┐
│           Agent Core                │
├─────────────────────────────────────┤
│  - Configuration Management         │
│  - Health Monitoring                │
│  - Logging & Metrics                │
│  - Error Recovery                   │
├─────────────────────────────────────┤
│       Agent-Specific Logic          │
├─────────────────────────────────────┤
│  - Tools & Integrations             │
│  - AI/ML Models (if applicable)     │
│  - External Service Clients         │
└─────────────────────────────────────┘
```

## Inter-Agent Communication

Agents communicate through:
- **Event Bus** - Pub/Sub for asynchronous events
- **Direct API Calls** - For synchronous operations
- **Shared State Store** - BigQuery for persistent data

## Common Features

All agents share:
- Google ADK integration
- Structured logging
- Health check endpoints
- Configuration hot-reloading
- Graceful shutdown handling
- Retry and circuit breaker patterns

## Development Guidelines

When developing agents:
1. Extend the base agent class from ADK
2. Implement required interfaces
3. Add comprehensive logging
4. Include health checks
5. Write unit and integration tests
6. Document configuration options

## Monitoring

Each agent exposes:
- `/health` - Health status
- `/metrics` - Prometheus metrics
- `/config` - Current configuration (sanitized)
