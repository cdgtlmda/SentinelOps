# API Reference

**Last Updated**: June 11, 2025

## Overview

SentinelOps provides a RESTful API for integrating with external systems and building custom interfaces. All API endpoints are secured and require authentication.

**Base URL**: `https://api.sentinelops.yourdomain.com/api/v1`

**API Documentation**: Interactive documentation is available at:
- Swagger UI: `https://api.sentinelops.yourdomain.com/docs`
- ReDoc: `https://api.sentinelops.yourdomain.com/redoc`

## Authentication

SentinelOps supports two authentication methods:

### 1. JWT Bearer Token
```bash
curl -X POST https://api.sentinelops.yourdomain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "your-password"}'

# Use the token in subsequent requests:
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://api.sentinelops.yourdomain.com/api/v1/incidents
```

### 2. API Key
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  https://api.sentinelops.yourdomain.com/api/v1/incidents
```

## Common Headers

| Header | Description | Required |
|--------|-------------|----------|
| `Authorization` | Bearer token for JWT auth | Yes (if not using API key) |
| `X-API-Key` | API key for authentication | Yes (if not using JWT) |
| `Content-Type` | Must be `application/json` for POST/PUT | Yes for POST/PUT |
| `X-Request-ID` | Unique request identifier for tracing | No |

## Response Format

All responses follow this structure:

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "meta": {
    "timestamp": "2025-06-11T10:00:00Z",
    "request_id": "req_123456"
  }
}
```

Error responses:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Detailed error message",
    "details": {
      // Additional error context
    }
  },
  "meta": {
    "timestamp": "2025-06-11T10:00:00Z",
    "request_id": "req_123456"
  }
}
```

## Endpoints

### Authentication

#### POST /auth/login
Login and receive JWT token.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "secure-password"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "expires_in": 3600,
    "refresh_token": "refresh_token_here"
  }
}
```

#### POST /auth/refresh
Refresh an expired token.

**Request:**
```json
{
  "refresh_token": "your_refresh_token"
}
```

#### POST /auth/logout
Invalidate current token.

**Headers:** Requires authentication

### Incidents

#### GET /api/v1/incidents
List all incidents with optional filtering.

**Query Parameters:**
- `status` (string): Filter by status (OPEN, INVESTIGATING, REMEDIATING, RESOLVED, FALSE_POSITIVE)
- `severity` (string): Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
- `type` (string): Filter by incident type
- `start_date` (string): ISO 8601 date for range start
- `end_date` (string): ISO 8601 date for range end
- `page` (integer): Page number (default: 1)
- `per_page` (integer): Items per page (default: 20, max: 100)
- `sort` (string): Sort field (created_at, severity, updated_at)
- `order` (string): Sort order (asc, desc)

**Response:**
```json
{
  "success": true,
  "data": {
    "incidents": [
      {
        "id": "inc_123456",
        "incident_id": "INC-2025-001",
        "type": "suspicious_login",
        "severity": "HIGH",
        "status": "OPEN",
        "affected_resources": ["user@example.com"],
        "created_at": "2025-06-11T10:00:00Z",
        "updated_at": "2025-06-11T10:05:00Z",
        "metadata": {
          "ip_addresses": ["192.168.1.1"],
          "gcp_projects": ["my-project"]
        }
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 150,
      "pages": 8
    }
  }
}
```

#### GET /api/v1/incidents/{incident_id}
Get detailed information about a specific incident.

**Response:**
```json
{
  "success": true,
  "data": {
    "incident": {
      "id": "inc_123456",
      "incident_id": "INC-2025-001",
      "type": "suspicious_login",
      "severity": "HIGH",
      "status": "INVESTIGATING",
      "affected_resources": ["user@example.com"],
      "created_at": "2025-06-11T10:00:00Z",
      "updated_at": "2025-06-11T10:15:00Z",
      "timeline": [
        {
          "timestamp": "2025-06-11T10:00:00Z",
          "event": "Incident detected",
          "agent": "detection-agent",
          "details": "Multiple failed login attempts detected"
        },
        {
          "timestamp": "2025-06-11T10:05:00Z",
          "event": "Analysis started",
          "agent": "analysis-agent",
          "details": "Gemini AI analysis initiated"
        }
      ],
      "analysis": {
        "root_cause": "Credential stuffing attack",
        "recommendations": [
          "Block source IP addresses",
          "Force password reset for affected user"
        ],
        "confidence": 0.92
      },
      "metadata": {
        "ip_addresses": ["192.168.1.1", "10.0.0.1"],
        "user_accounts": ["user@example.com"],
        "gcp_projects": ["my-project"],
        "regions": ["us-central1"]
      }
    }
  }
}
```

#### POST /api/v1/incidents
Create a new incident (typically used by external systems).

**Request:**
```json
{
  "type": "custom_alert",
  "severity": "MEDIUM",
  "description": "Unusual activity detected",
  "affected_resources": ["resource-123"],
  "metadata": {
    "source": "external-siem",
    "alert_id": "ext-001"
  }
}
```

#### PUT /api/v1/incidents/{incident_id}
Update an incident.

**Request:**
```json
{
  "status": "INVESTIGATING",
  "assigned_to": "security-team",
  "notes": "Under investigation by SOC"
}
```

#### POST /api/v1/incidents/{incident_id}/assign
Assign an incident to a team or individual.

**Request:**
```json
{
  "assignee": "security-analyst-1",
  "notes": "Assigning to senior analyst for review"
}
```

#### POST /api/v1/incidents/{incident_id}/resolve
Mark an incident as resolved.

**Request:**
```json
{
  "resolution_notes": "False positive - legitimate user activity",
  "false_positive": true
}
```

### Rules

#### GET /api/v1/rules
List all detection rules.

**Query Parameters:**
- `enabled` (boolean): Filter by enabled status
- `type` (string): Filter by rule type (detection, correlation, response)
- `severity` (string): Filter by severity
- `page` (integer): Page number
- `per_page` (integer): Items per page

#### GET /api/v1/rules/{rule_id}
Get a specific rule.

#### POST /api/v1/rules
Create a new detection rule.

**Request:**
```json
{
  "name": "Failed SSH Login Detection",
  "description": "Detect multiple failed SSH login attempts",
  "type": "detection",
  "severity": "HIGH",
  "enabled": true,
  "conditions": {
    "query": "SELECT * FROM logs WHERE jsonPayload.message LIKE '%Failed password%'",
    "time_window": 300,
    "thresholds": [
      {
        "metric": "event_count",
        "operator": ">",
        "value": 5
      }
    ]
  },
  "actions": {
    "notify": ["security-team"],
    "escalate": true
  }
}
```

#### PUT /api/v1/rules/{rule_id}
Update a rule.

#### DELETE /api/v1/rules/{rule_id}
Delete a rule.

#### POST /api/v1/rules/{rule_id}/test
Test a rule against sample data.

**Request:**
```json
{
  "sample_data": {
    "logs": [
      {"message": "Failed password for user root"},
      {"message": "Failed password for user admin"}
    ]
  }
}
```

### Analysis

#### POST /api/v1/analysis/analyze
Trigger AI analysis for an incident.

**Request:**
```json
{
  "incident_id": "inc_123456",
  "analysis_type": "root_cause",
  "include_recommendations": true,
  "urgency": "high"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis_id": "ana_789012",
    "status": "in_progress",
    "estimated_completion": "2025-06-11T10:10:00Z"
  }
}
```

#### GET /api/v1/analysis/{analysis_id}
Get analysis results.

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis": {
      "id": "ana_789012",
      "incident_id": "inc_123456",
      "status": "completed",
      "results": {
        "root_cause": "Credential stuffing attack from known botnet",
        "confidence": 0.89,
        "impact_assessment": "Medium - Single user account targeted",
        "recommendations": [
          {
            "action": "block_ip",
            "priority": "HIGH",
            "reasoning": "Source IPs associated with known botnet"
          },
          {
            "action": "reset_password",
            "priority": "MEDIUM",
            "reasoning": "Account may be compromised"
          }
        ],
        "threat_intelligence": {
          "ip_reputation": "malicious",
          "known_campaigns": ["Botnet-X"],
          "first_seen": "2025-05-01"
        }
      },
      "completed_at": "2025-06-11T10:08:00Z"
    }
  }
}
```

### Remediation

#### POST /api/v1/remediation/execute
Execute a remediation action.

**Request:**
```json
{
  "incident_id": "inc_123456",
  "action": "block_ip",
  "parameters": {
    "ip_addresses": ["192.168.1.1", "10.0.0.1"],
    "duration": 86400,
    "policy_name": "emergency-blocks"
  },
  "dry_run": false,
  "require_approval": true
}
```

#### GET /api/v1/remediation/{action_id}
Get remediation action status.

**Response:**
```json
{
  "success": true,
  "data": {
    "action": {
      "id": "rem_345678",
      "incident_id": "inc_123456",
      "type": "block_ip",
      "status": "pending_approval",
      "parameters": {
        "ip_addresses": ["192.168.1.1"],
        "duration": 86400
      },
      "approval": {
        "required": true,
        "requested_at": "2025-06-11T10:20:00Z",
        "approvers": ["security-manager"]
      }
    }
  }
}
```

#### POST /api/v1/remediation/{action_id}/approve
Approve a pending remediation action.

**Request:**
```json
{
  "approval_notes": "Approved - confirmed malicious activity"
}
```

#### POST /api/v1/remediation/{action_id}/rollback
Rollback a completed remediation action.

**Request:**
```json
{
  "reason": "False positive identified after review"
}
```

### Notifications

#### GET /api/v1/notifications/preferences
Get notification preferences for the authenticated user.

#### PUT /api/v1/notifications/preferences
Update notification preferences.

**Request:**
```json
{
  "channels": {
    "email": {
      "enabled": true,
      "address": "user@example.com",
      "severities": ["CRITICAL", "HIGH"]
    },
    "slack": {
      "enabled": true,
      "webhook_url": "https://hooks.slack.com/...",
      "severities": ["CRITICAL", "HIGH", "MEDIUM"]
    },
    "sms": {
      "enabled": false
    }
  },
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "08:00",
    "timezone": "America/New_York"
  }
}
```

#### POST /api/v1/notifications/test
Send a test notification.

**Request:**
```json
{
  "channel": "email",
  "message": "This is a test notification from SentinelOps"
}
```

### System

#### GET /api/v1/system/health
Get system health status.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "agents": {
      "detection": "active",
      "analysis": "active",
      "remediation": "active",
      "communication": "active",
      "orchestrator": "active"
    },
    "services": {
      "firestore": "connected",
      "pubsub": "connected",
      "bigquery": "connected"
    },
    "timestamp": "2025-06-11T10:30:00Z"
  }
}
```

#### GET /api/v1/system/metrics
Get system metrics.

**Query Parameters:**
- `period` (string): Time period (1h, 24h, 7d, 30d)
- `metrics` (array): Specific metrics to retrieve

**Response:**
```json
{
  "success": true,
  "data": {
    "metrics": {
      "incidents": {
        "total": 1523,
        "by_severity": {
          "CRITICAL": 23,
          "HIGH": 156,
          "MEDIUM": 743,
          "LOW": 601
        },
        "by_status": {
          "OPEN": 12,
          "INVESTIGATING": 5,
          "RESOLVED": 1506
        }
      },
      "performance": {
        "avg_detection_time": 3.2,
        "avg_analysis_time": 8.7,
        "avg_remediation_time": 15.3
      },
      "api": {
        "requests_per_minute": 127,
        "error_rate": 0.002,
        "avg_response_time": 145
      }
    },
    "period": "24h",
    "generated_at": "2025-06-11T10:35:00Z"
  }
}
```

## Rate Limiting

API rate limits are enforced per authentication method:

| Authentication Type | Rate Limit | Window |
|-------------------|------------|---------|
| JWT Token | 1000 requests | 1 hour |
| API Key | 5000 requests | 1 hour |

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

When rate limited, you'll receive a 429 response:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded",
    "retry_after": 3600
  }
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Malformed request or invalid parameters |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate) |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## Pagination

List endpoints support pagination through query parameters:

- `page`: Page number (starting from 1)
- `per_page`: Items per page (max 100)

Pagination metadata is included in responses:
```json
{
  "pagination": {
    "page": 2,
    "per_page": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": true
  }
}
```

## Filtering and Sorting

Most list endpoints support filtering and sorting:

**Filtering:**
- Use query parameters matching field names
- Multiple values: `?status=OPEN&status=INVESTIGATING`
- Date ranges: `?created_after=2025-06-01&created_before=2025-06-11`

**Sorting:**
- `sort`: Field to sort by
- `order`: Sort order (asc/desc)

Example: `?sort=severity&order=desc&status=OPEN`

## Webhooks

Configure webhooks to receive real-time notifications:

### Webhook Events

- `incident.created`
- `incident.updated`
- `incident.resolved`
- `analysis.completed`
- `remediation.executed`
- `rule.triggered`

### Webhook Payload

```json
{
  "event": "incident.created",
  "timestamp": "2025-06-11T10:00:00Z",
  "data": {
    // Event-specific data
  },
  "signature": "sha256=..."
}
```

### Webhook Security

All webhooks include an HMAC signature in the `X-Webhook-Signature` header for verification.

## SDK Examples

### Python
```python
from sentinelops import SentinelOpsClient

client = SentinelOpsClient(api_key="your-api-key")

# List incidents
incidents = client.incidents.list(status="OPEN", severity="HIGH")

# Analyze an incident
analysis = client.analysis.analyze(
    incident_id="inc_123456",
    analysis_type="root_cause"
)

# Execute remediation
client.remediation.execute(
    incident_id="inc_123456",
    action="block_ip",
    parameters={"ip_addresses": ["192.168.1.1"]}
)
```

### JavaScript
```javascript
const SentinelOps = require('@sentinelops/sdk');

const client = new SentinelOps({ apiKey: 'your-api-key' });

// List incidents
const incidents = await client.incidents.list({
  status: 'OPEN',
  severity: 'HIGH'
});

// Analyze an incident
const analysis = await client.analysis.analyze({
  incidentId: 'inc_123456',
  analysisType: 'root_cause'
});
```

### cURL
```bash
# List open incidents
curl -H "X-API-Key: your-api-key" \
  "https://api.sentinelops.yourdomain.com/api/v1/incidents?status=OPEN"

# Create an incident
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"type": "custom_alert", "severity": "HIGH"}' \
  "https://api.sentinelops.yourdomain.com/api/v1/incidents"
```

## API Versioning

The API version is included in the URL path (e.g., `/api/v1/`). 

- Current version: v1
- Version lifecycle: Minimum 12 months support
- Deprecation notices: 6 months in advance
- Breaking changes: Only in new major versions

## Support

- Documentation: [https://docs.sentinelops.com](https://docs.sentinelops.com)
- API Status: [https://status.sentinelops.com](https://status.sentinelops.com)
- Support: cdgtlmda@pm.me
- GitHub: [https://github.com/cdgtlmda/SentinelOps](https://github.com/cdgtlmda/SentinelOps)

## Related Documentation

- [WebSocket API Reference](./websocket-api.md)
- [Agent Communication API](../02-architecture/agent-communication-api.md)
- [ADK Tool Reference](./adk-tool-reference.md)
- [API Quick Start Guide](../01-getting-started/api-quickstart.md)