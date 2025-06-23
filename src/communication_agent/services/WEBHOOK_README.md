# Webhook Notification Service

The webhook notification service provides flexible HTTP/HTTPS webhook delivery for integrating SentinelOps with external systems and services.

## Features

- **Multiple HTTP Methods**: Support for GET, POST, PUT, PATCH, DELETE
- **Authentication Methods**: None, Basic, Bearer, API Key, HMAC, Custom Headers
- **Automatic Retries**: Configurable retry logic with exponential backoff
- **Payload Formatting**: Standardized JSON payloads with customization options
- **Named Configurations**: Pre-configured webhooks for common integrations
- **Delivery Tracking**: History of webhook deliveries with status tracking
- **SSL/TLS Support**: Optional SSL certificate verification
- **Rate Limiting**: Respects target service limits

## Configuration

### Environment Variables

```bash
# Default webhook configuration
export WEBHOOK_URL="https://your-webhook.com/endpoint"
export WEBHOOK_METHOD="POST"  # GET, POST, PUT, PATCH, DELETE
export WEBHOOK_AUTH_TYPE="bearer"  # none, basic, bearer, api_key, hmac, custom_header
export WEBHOOK_AUTH_CREDENTIALS='{"token": "your-bearer-token"}'
export WEBHOOK_HEADERS='{"X-Custom-Header": "value"}'
export WEBHOOK_TIMEOUT="30"
export WEBHOOK_MAX_RETRIES="3"
export WEBHOOK_VERIFY_SSL="true"

# Named webhook configurations
export WEBHOOK_CONFIG_SLACK='{"url": "https://hooks.slack.com/services/YOUR/WEBHOOK", "auth_type": "none"}'
export WEBHOOK_CONFIG_PAGERDUTY='{"url": "https://events.pagerduty.com/v2/enqueue", "auth_type": "api_key", "auth_credentials": {"key_name": "Authorization", "key_value": "Token token=YOUR_KEY"}}'
```

## Usage

### Basic Usage

```python
from src.communication_agent.services.webhook_service import WebhookNotificationService
from src.communication_agent.config.webhook_config import get_webhook_config

# Initialize service
config = get_webhook_config()
webhook_service = WebhookNotificationService(default_config=config)

# Send to a webhook URL
result = await webhook_service.send(
    recipients=["https://your-webhook.com/alerts"],
    subject="Security Alert",
    message="Unauthorized access detected",
    priority=NotificationPriority.HIGH,
)
```

### Authentication Methods

#### No Authentication
```python
config = WebhookConfig(
    url="https://webhook.site/your-url",
    auth_type=WebhookAuthType.NONE,
)
```

#### Basic Authentication
```python
config = WebhookConfig(
    url="https://api.example.com/webhook",
    auth_type=WebhookAuthType.BASIC,
    auth_credentials={
        "username": "your-username",
        "password": "your-password",
    },
)
```

#### Bearer Token
```python
config = WebhookConfig(
    url="https://api.example.com/webhook",
    auth_type=WebhookAuthType.BEARER,
    auth_credentials={"token": "your-bearer-token"},
)
```

#### API Key
```python
config = WebhookConfig(
    url="https://api.example.com/webhook",
    auth_type=WebhookAuthType.API_KEY,
    auth_credentials={
        "key_name": "X-API-Key",  # Header name
        "key_value": "your-api-key",
    },
)
```

#### HMAC Signature
```python
config = WebhookConfig(
    url="https://api.example.com/webhook",
    auth_type=WebhookAuthType.HMAC,
    auth_credentials={
        "secret": "shared-secret",
        "algorithm": "sha256",  # or "sha1"
        "header_name": "X-Hub-Signature-256",
    },
)
```

#### Custom Headers
```python
config = WebhookConfig(
    url="https://api.example.com/webhook",
    auth_type=WebhookAuthType.CUSTOM_HEADER,
    auth_credentials={
        "X-Custom-Auth": "custom-value",
        "X-Another-Header": "another-value",
    },
)
```

### Payload Format

The service sends webhooks with the following JSON structure:

```json
{
    "event_type": "sentinelops.incident_detected",
    "timestamp": "2025-05-29T10:00:00Z",
    "incident_id": "INC-001",  // If provided
    "data": {
        "subject": "Security Alert",
        "message": "Detailed message content",
        "priority": "high",
        "metadata": {
            // Custom metadata fields
        }
    }
}
```

### Named Webhooks

Use pre-configured webhooks by name:

```python
# Configure named webhooks
webhook_configs = {
    "slack": WebhookConfig(url="https://hooks.slack.com/..."),
    "pagerduty": WebhookConfig(url="https://events.pagerduty.com/..."),
    "custom": WebhookConfig(url="https://your-api.com/..."),
}

service = WebhookNotificationService(webhook_configs=webhook_configs)

# Send to named webhook
await service.send(
    recipients=["slack", "pagerduty"],  # Use names instead of URLs
    subject="Alert",
    message="Critical issue",
    priority=NotificationPriority.CRITICAL,
)
```

### Retry Logic

Configure retry behavior:

```python
config = WebhookConfig(
    url="https://api.example.com/webhook",
    max_retries=5,        # Maximum retry attempts
    retry_delay=10,       # Initial delay in seconds
    timeout=60,           # Request timeout
)
```

Retries use exponential backoff:
- 1st retry: 10 seconds
- 2nd retry: 20 seconds
- 3rd retry: 40 seconds
- etc.

## Integration Examples

### Slack Incoming Webhook

```python
slack_config = WebhookConfig(
    url="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
    method=WebhookMethod.POST,
    auth_type=WebhookAuthType.NONE,
)

# Slack expects a specific payload format
# The service will send standard format, but you can customize via metadata
```

### PagerDuty Events API

```python
pagerduty_config = WebhookConfig(
    url="https://events.pagerduty.com/v2/enqueue",
    method=WebhookMethod.POST,
    auth_type=WebhookAuthType.NONE,  # PagerDuty uses routing key in payload
    headers={"Content-Type": "application/json"},
)
```

### Custom API Integration

```python
custom_config = WebhookConfig(
    url="https://your-api.com/v1/security/alerts",
    method=WebhookMethod.POST,
    auth_type=WebhookAuthType.BEARER,
    auth_credentials={"token": os.getenv("API_TOKEN")},
    headers={
        "X-API-Version": "2.0",
        "X-Client-ID": "sentinelops",
    },
    max_retries=5,
    verify_ssl=True,
)
```

## Delivery Tracking

Monitor webhook deliveries:

```python
# Get delivery history
history = webhook_service.get_delivery_history(limit=50)

for record in history:
    print(f"{record['timestamp']}: {record['url']}")
    print(f"  Status: {record['status_code']}")
    print(f"  Success: {record['success']}")
    print(f"  Time: {record['delivery_time']}s")
    print(f"  Retries: {record['retry_count']}")
```

## Error Handling

```python
try:
    result = await webhook_service.send(...)
except ValueError as e:
    # Invalid recipients or configuration
    print(f"Configuration error: {e}")
except aiohttp.ClientError as e:
    # HTTP client errors
    print(f"HTTP error: {e}")
except asyncio.TimeoutError:
    # Request timeout
    print("Webhook delivery timed out")
```

## Security Considerations

1. **HTTPS Only**: Always use HTTPS URLs for webhooks in production
2. **Authentication**: Use appropriate authentication for your webhook endpoints
3. **HMAC Signatures**: Verify webhook authenticity with HMAC signatures
4. **IP Whitelisting**: Consider IP restrictions on webhook endpoints
5. **Rate Limiting**: Implement rate limiting to prevent abuse
6. **Payload Size**: Keep payloads under 1MB for reliability
7. **Secrets Management**: Store credentials securely, never in code

## Troubleshooting

### Common Issues

1. **"Connection refused"**
   - Verify the webhook URL is correct
   - Check if the service is running
   - Ensure firewall rules allow outbound HTTPS

2. **"SSL certificate verify failed"**
   - Set `verify_ssl=False` for self-signed certificates (not recommended for production)
   - Update CA certificates on the system

3. **"401 Unauthorized"**
   - Verify authentication credentials
   - Check if token/API key is expired
   - Ensure correct auth type is configured

4. **"Request timeout"**
   - Increase timeout value
   - Check target service performance
   - Consider async processing for slow endpoints

5. **"Too many retries"**
   - Check if target service is rate limiting
   - Implement backoff strategy
   - Monitor service health

## Best Practices

1. **Use HTTPS**: Always use encrypted connections
2. **Implement Idempotency**: Design webhooks to handle duplicate deliveries
3. **Keep Payloads Small**: Large payloads can cause timeouts
4. **Monitor Deliveries**: Track success rates and response times
5. **Handle Failures Gracefully**: Implement proper retry and fallback logic
6. **Document Webhooks**: Maintain clear documentation of webhook formats
7. **Version Your APIs**: Include version information in webhooks
8. **Test Thoroughly**: Use webhook testing services during development
