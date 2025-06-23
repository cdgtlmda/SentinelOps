# Natural Language Interface Documentation

## Overview

The Natural Language Interface (NLI) in SentinelOps provides a conversational API for querying security incidents, analyzing threats, and getting recommendations using Google's Gemini AI. This interface includes advanced safety features such as fact verification, consistency checking, and human review triggers.

## API Endpoints

### 1. Natural Language Query

**Endpoint:** `POST /api/v1/nlp/query`

Process a natural language query about security incidents or system status.

**Request Body:**
```json
{
  "query": "What security incidents occurred in the last hour?",
  "context": {
    "timeframe": "1h",
    "severity": "high"
  },
  "conversation_id": "conv_12345"  // Optional
}
```

**Response:**
```json
{
  "query": "What security incidents occurred in the last hour?",
  "response": "In the last hour, there were 3 high-severity incidents...",
  "intent": "status",
  "confidence": 0.92,
  "conversation_id": "conv_12345",
  "follow_up_questions": [
    "Would you like details about the most critical incident?",
    "Do you want to see the affected systems?"
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. Validated Query

**Endpoint:** `POST /api/v1/nlp/query/validated`

Process a query with validation and safety checks.

**Request Body:**
```json
{
  "query": "Analyze the authentication logs for anomalies",
  "context": {
    "log_source": "auth_service",
    "time_range": "24h"
  },
  "require_fact_check": true,
  "safety_level": "strict"
}
```

**Response:**
```json
{
  "response": "Analysis of authentication logs reveals...",
  "validation": {
    "passed": true,
    "confidence_score": 0.85,
    "issues": [],
    "hallucination_check": {
      "detected": false,
      "confidence": 0.95
    },
    "fact_check": {
      "all_verified": true,
      "verification_rate": 1.0
    },
    "consistency_check": {
      "consistent": true,
      "consistency_score": 1.0
    }
  },
  "confidence": 0.85,
  "human_review_needed": false,
  "review_reasons": [],
  "below_confidence_threshold": false
}
```

### 3. Incident Explanation

**Endpoint:** `POST /api/v1/nlp/explain/incident`

Generate user-friendly explanations of security incidents.

**Request Body:**
```json
{
  "incident_summary": "Detected 500 failed login attempts from IP 192.168.1.100 targeting admin accounts",
  "user_level": "executive"  // Options: "executive", "technical", "general"
}
```

**Response:**
```json
{
  "incident_summary": "Detected 500 failed login attempts...",
  "explanation": "Your system experienced what appears to be a targeted attack...",
  "user_level": "executive",
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### 4. Recommendation Clarification

**Endpoint:** `POST /api/v1/nlp/clarify/recommendation`

Get clarification on security recommendations.

**Request Body:**
```json
{
  "recommendation": "Implement rate limiting on authentication endpoints",
  "clarification_request": "What specific rate limits should I configure?"
}
```

### 5. Conversation Summary

**Endpoint:** `POST /api/v1/nlp/conversation/summary`

Summarize a security conversation.

**Request Body:**
```json
{
  "conversation_id": "conv_12345"
}
```

**Response:**
```json
{
  "conversation_id": "conv_12345",
  "summary": {
    "summary": "Discussion focused on brute force attack mitigation...",
    "key_points": [
      "Identified brute force attack pattern",
      "Implemented IP blocking"
    ],
    "unresolved_issues": ["Need to review rate limiting configuration"],
    "next_steps": ["Monitor for attack variations", "Update security policies"]
  },
  "message_count": 8,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

## Safety Features

### 1. Output Validation

All AI responses undergo comprehensive validation:

- **Schema Validation**: Ensures structured outputs match expected formats
- **Fact Verification**: Cross-references claims against provided context
- **Consistency Checking**: Detects contradictions within responses
- **Hallucination Detection**: Identifies potentially fabricated information

### 2. Human Review Triggers

Automatic triggers for human review based on:

- **Low Confidence**: Responses below configured threshold (default: 0.7)
- **High-Risk Actions**: Detection of keywords like "delete", "shutdown", "disable"
- **Critical Severity**: Responses mentioning critical or catastrophic issues
- **Multiple Inconsistencies**: More than 3 detected inconsistencies
- **Unverified Claims**: Over 30% of factual claims cannot be verified

### 3. Content Filtering

Administrators can configure content filters to:

- Redact sensitive information (IPs, emails, credentials)
- Block specific patterns or keywords
- Sanitize outputs for different audiences

**Add Filter Endpoint:** `POST /api/v1/nlp/safety/add-filter` (Admin only)

```json
{
  "patterns": ["password", "secret", "\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b"]
}
```

### 4. Confidence Thresholds

Set minimum confidence levels for responses:

**Set Threshold Endpoint:** `POST /api/v1/nlp/safety/set-threshold?threshold=0.8` (Admin only)

## Conversation Management

### Get Conversation History

**Endpoint:** `GET /api/v1/nlp/conversation/{conversation_id}/history`

Retrieve the full history of a conversation.

### Delete Conversation

**Endpoint:** `DELETE /api/v1/nlp/conversation/{conversation_id}`

Delete a conversation (users can only delete their own conversations).

## Intent Classification

The system automatically classifies query intents:

- **status**: Asking about current status or state
- **explanation**: Requesting explanation of an incident
- **recommendation**: Asking for recommendations or next steps
- **analysis**: Requesting analysis or investigation
- **other**: Doesn't fit the above categories

## Best Practices

1. **Provide Context**: Include relevant context in queries for more accurate responses
2. **Use Conversation IDs**: Maintain conversation continuity for complex discussions
3. **Enable Fact Checking**: For critical queries, enable fact checking
4. **Monitor Review Triggers**: Set up callbacks to handle human review requirements
5. **Configure Safety Levels**: Use appropriate safety levels based on use case

## Error Handling

All endpoints return standard error responses:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {}
}
```

Common error codes:
- `400`: Invalid request parameters
- `403`: Insufficient permissions
- `404`: Resource not found
- `500`: Internal server error

## Rate Limiting

The NLP interface respects Gemini API rate limits:
- 60 requests per minute
- 1000 requests per hour
- Token-based limits apply

## Security Considerations

1. **Authentication**: All endpoints require authentication
2. **Authorization**: Admin-only endpoints for safety configuration
3. **Audit Logging**: All queries and responses are logged
4. **Data Privacy**: Conversation data is isolated per user
5. **Input Validation**: All inputs undergo safety checks before processing