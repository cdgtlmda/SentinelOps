"""API documentation configuration and customization for SentinelOps."""

from typing import Any, Dict

# API metadata
API_TITLE = "SentinelOps API"
API_VERSION = "1.0.0"
API_DESCRIPTION = """
# SentinelOps Security Operations Platform API

## Overview

SentinelOps is an AI-powered security operations platform that provides:

- **Incident Detection**: Real-time security incident detection and alerting
- **Automated Analysis**: AI-driven incident analysis with Gemini integration
- **Smart Remediation**: Automated and manual remediation workflows
- **Communication**: Multi-channel notifications and alerts
- **Natural Language Processing**: Query and interact with the system using natural language

## Authentication

The API uses JWT tokens and API keys for authentication. Include your authentication
token in the `Authorization` header:

```
Authorization: Bearer <your-token>
```

Or use an API key in the `X-API-Key` header:

```
X-API-Key: <your-api-key>
```

## Rate Limiting

API requests are rate-limited to ensure fair usage:
- **Standard tier**: 1000 requests per hour
- **Premium tier**: 10000 requests per hour

## WebSocket Support

Real-time updates are available via WebSocket at `/ws`. Authentication is required via
query parameter:

```
ws://api.sentinelops.com/ws?token=<your-token>
```

## Error Handling

The API uses standard HTTP status codes and returns errors in a consistent format:

```json
{
    "error": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
}
```

## Versioning

The API is versioned via URL path. Current version is v1:
- Base URL: `https://api.sentinelops.com/api/v1`
"""

# Tag descriptions for better organization
TAGS_METADATA = [
    {
        "name": "Health",
        "description": "Health check and status endpoints",
    },
    {
        "name": "Authentication",
        "description": "Authentication and authorization endpoints",
    },
    {
        "name": "Incidents",
        "description": "Security incident management",
    },
    {
        "name": "Rules",
        "description": "Detection rule configuration and management",
    },
    {
        "name": "Analysis",
        "description": "AI-powered security analysis endpoints",
    },
    {
        "name": "Remediation",
        "description": "Automated and manual remediation actions",
    },
    {
        "name": "Notifications",
        "description": "Multi-channel notification management",
    },
    {
        "name": "NLP",
        "description": "Natural language processing endpoints",
    },
]


# Custom OpenAPI schema modifications
def custom_openapi_schema(openapi_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Customize the OpenAPI schema with additional information."""

    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "https://api.sentinelops.com",
            "description": "Production server",
        },
        {
            "url": "https://staging-api.sentinelops.com",
            "description": "Staging server",
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server",
        },
    ]

    # Add external documentation
    openapi_schema["externalDocs"] = {
        "description": "SentinelOps Documentation",
        "url": "https://docs.sentinelops.com",
    }

    # Add security schemes
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT authentication token",
        },
        "apiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key authentication",
        },
    }

    # Add global security requirement
    openapi_schema["security"] = [
        {"bearerAuth": []},
        {"apiKeyAuth": []},
    ]

    # Add contact and license info
    if "info" in openapi_schema:
        openapi_schema["info"]["contact"] = {
            "name": "SentinelOps Support",
            "email": "support@sentinelops.com",
            "url": "https://sentinelops.com/support",
        }
        openapi_schema["info"]["license"] = {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        }
        openapi_schema["info"]["termsOfService"] = "https://sentinelops.com/terms"

    # Add API response examples
    if "paths" in openapi_schema:
        # Add common response schemas
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        if "schemas" not in openapi_schema["components"]:
            openapi_schema["components"]["schemas"] = {}

        openapi_schema["components"]["schemas"]["ErrorResponse"] = {
            "type": "object",
            "properties": {
                "error": {
                    "type": "string",
                    "description": "Error code",
                    "example": "VALIDATION_ERROR",
                },
                "message": {
                    "type": "string",
                    "description": "Human-readable error message",
                    "example": "Invalid input parameters",
                },
                "details": {
                    "type": "object",
                    "description": "Additional error details",
                    "additionalProperties": True,
                },
            },
            "required": ["error", "message"],
        }

        openapi_schema["components"]["schemas"]["SuccessResponse"] = {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["success"],
                    "example": "success",
                },
                "message": {
                    "type": "string",
                    "example": "Operation completed successfully",
                },
                "data": {
                    "type": "object",
                    "description": "Response data",
                    "additionalProperties": True,
                },
            },
            "required": ["status", "message"],
        }

    return openapi_schema


# Example request/response pairs for documentation
EXAMPLE_REQUESTS = {
    "incident_create": {
        "summary": "Create security incident",
        "value": {
            "title": "Suspicious Login Activity",
            "description": "Multiple failed login attempts detected from unusual IP addresses",
            "severity": "high",
            "source": "auth-system",
            "events": [
                {
                    "timestamp": "2024-01-15T10:30:00Z",
                    "event_type": "authentication_failure",
                    "source": {
                        "source_type": "application",
                        "source_name": "auth-service",
                        "source_id": "auth-001",
                    },
                    "severity": "medium",
                    "description": "Failed login attempt",
                    "raw_data": {
                        "username": "admin",
                        "ip_address": "192.168.1.100",
                        "user_agent": "Mozilla/5.0...",
                    },
                }
            ],
        },
    },
    "rule_create": {
        "summary": "Create detection rule",
        "value": {
            "name": "Brute Force Detection",
            "description": "Detect brute force login attempts",
            "query": "event_type:authentication_failure AND count > 5",
            "severity": "high",
            "enabled": True,
            "conditions": {
                "time_window": 300,
                "threshold": 5,
                "group_by": ["source_ip", "username"],
            },
            "actions": [
                {
                    "type": "notify",
                    "channels": ["email", "slack"],
                },
                {
                    "type": "block_ip",
                    "duration": 3600,
                },
            ],
        },
    },
}


# Response examples for documentation
EXAMPLE_RESPONSES = {
    "incident_response": {
        "summary": "Incident created successfully",
        "value": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Suspicious Login Activity",
            "severity": "high",
            "status": "detected",
            "created_at": "2024-01-15T10:35:00Z",
            "analysis_status": "pending",
        },
    },
    "error_response": {
        "summary": "Validation error",
        "value": {
            "error": "VALIDATION_ERROR",
            "message": "Invalid severity level",
            "details": {
                "field": "severity",
                "value": "extreme",
                "allowed_values": ["low", "medium", "high", "critical"],
            },
        },
    },
}
