# API Endpoint: [Endpoint Name]

## Overview

Brief description of what this API endpoint does.

## Endpoint Details

- **URL**: `/api/v1/[resource]/[action]`
- **Method**: `GET` | `POST` | `PUT` | `DELETE` | `PATCH`
- **Authentication**: Required | Optional
- **Rate Limit**: 100 requests per minute

## Request

### Headers

| Header | Description | Required | Example |
|--------|-------------|----------|---------|
| Authorization | Bearer token | Yes | `Bearer eyJhbGc...` |
| Content-Type | Request content type | Yes | `application/json` |
| X-Correlation-ID | Request tracking ID | No | `123e4567-e89b-12d3` |

### Path Parameters

| Parameter | Type | Description | Required | Example |
|-----------|------|-------------|----------|---------|
| id | string | Resource identifier | Yes | `resource-123` |

### Query Parameters

| Parameter | Type | Description | Default | Example |
|-----------|------|-------------|---------|---------|
| page | integer | Page number | 1 | `2` |
| page_size | integer | Items per page | 20 | `50` |
| filter | string | Filter expression | none | `status:active` |

### Request Body

```json
{
  "field1": "string",
  "field2": 123,
  "field3": {
    "nested_field": "value"
  },
  "field4": ["array", "of", "values"]
}
```

### Field Descriptions

- **field1** (string, required): Description of field1
- **field2** (integer, optional): Description of field2
- **field3** (object, optional): Description of field3
  - **nested_field** (string): Description of nested field
- **field4** (array[string], optional): Description of field4

## Response

### Success Response

**Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "resource-123",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "field1": "value1",
    "field2": 123
  },
  "metadata": {
    "request_id": "req-456",
    "timestamp": "2024-01-15T10:35:00Z"
  }
}
```

### Error Responses

#### 400 Bad Request

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "field1": "Field is required"
    }
  }
}
```

#### 401 Unauthorized

```json
{
  "error": {
    "code": "AUTH_ERROR",
    "message": "Authentication required"
  }
}
```

#### 403 Forbidden

```json
{
  "error": {
    "code": "AUTHZ_ERROR",
    "message": "Insufficient permissions"
  }
}
```

#### 404 Not Found

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found"
  }
}
```

#### 500 Internal Server Error

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An internal error occurred",
    "correlation_id": "123e4567-e89b-12d3"
  }
}
```

## Examples

### cURL

```bash
curl -X POST https://api.sentinelops.com/api/v1/resource/action \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "field1": "value1",
    "field2": 123
  }'
```

### Python

```python
import requests

response = requests.post(
    "https://api.sentinelops.com/api/v1/resource/action",
    headers={
        "Authorization": "Bearer YOUR_TOKEN",
        "Content-Type": "application/json"
    },
    json={
        "field1": "value1",
        "field2": 123
    }
)

data = response.json()
```

### JavaScript

```javascript
const response = await fetch('https://api.sentinelops.com/api/v1/resource/action', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    field1: 'value1',
    field2: 123
  })
});

const data = await response.json();
```

## Notes

- Note about specific behavior
- Important limitation or consideration
- Link to related endpoints

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-15 | Initial release |
