# SMS Notification Service

The SMS notification service provides reliable text message delivery for critical security alerts using Twilio's messaging infrastructure.

## Features

- **E.164 Phone Number Validation**: Ensures all phone numbers are in proper international format
- **Message Length Optimization**: Automatically optimizes and splits long messages
- **Intelligent Word Replacement**: Shortens common security terms to fit more content
- **Multi-part Message Support**: Handles messages up to 5 concatenated SMS parts
- **Delivery Status Tracking**: Real-time tracking of message delivery status
- **Priority-based Retry Logic**: Automatic retries for high-priority messages
- **Rate Limiting**: Respects Twilio's rate limits (1 message/second)
- **Messaging Service Support**: Can use Twilio Messaging Services for advanced features

## Configuration

### Environment Variables

```bash
# Required
export TWILIO_ACCOUNT_SID="your-account-sid"
export TWILIO_AUTH_TOKEN="your-auth-token"
export TWILIO_FROM_NUMBER="+15551234567"  # Must be E.164 format

# Optional
export TWILIO_STATUS_CALLBACK_URL="https://your-app.com/sms/status"
export TWILIO_MESSAGING_SERVICE_SID="your-messaging-service-sid"
export TWILIO_MAX_PRICE_PER_MESSAGE="0.10"  # USD
```

### Phone Number Formats

The service accepts phone numbers in various formats and normalizes them:
- E.164 format (preferred): `+15551234567`
- US numbers: `15551234567` or `5551234567`
- International: `+441234567890`

## Usage

### Basic Usage

```python
from src.communication_agent.config.sms_config import get_twilio_config
from src.communication_agent.services.sms_service import SMSNotificationService

# Initialize service
config = get_twilio_config()
sms_service = SMSNotificationService(config)

# Send a message
result = await sms_service.send(
    recipients=["+15551234567"],
    subject="Security Alert",
    message="Unauthorized access detected on production server",
    priority=NotificationPriority.HIGH,
)
```

### With Communication Agent

```python
from src.communication_agent.agent import CommunicationAgent

# Create agent with SMS service
agent = CommunicationAgent(
    notification_services={
        NotificationChannel.SMS: sms_service,
    }
)

# Send incident notification
await agent.send_incident_notification(
    incident_id="INC-001",
    incident_type="Data Breach",
    severity="critical",
    recipients=[{"channel": "sms", "address": "+15551234567"}],
)
```

## Message Optimization

The service automatically optimizes messages for SMS delivery:

### Word Replacements
- "Security Alert" → "Alert"
- "Incident" → "Inc"
- "Remediation" → "Fix"
- "Critical" → "CRIT"
- "immediately" → "now"

### Length Limits
- Single SMS: 160 characters
- Concatenated SMS: 153 characters per part
- Maximum parts: 5

### Example Optimization

Input:
```
Security Alert: Critical Incident detected. Remediation required immediately. 
The incident involves unauthorized access to production servers...
```

Output:
```
(1/2) Alert: CRIT Inc detected. Fix required now. The incident involves 
unauthorized access to production servers...
(2/2) Please review and take action: https://app.com/inc/001
```

## Delivery Status Tracking

### Status Webhook

Configure `TWILIO_STATUS_CALLBACK_URL` to receive delivery updates:

```python
async def handle_sms_webhook(request):
    data = await request.json()
    await sms_service.handle_status_callback(data)
```

### Status Values
- `queued`: Message queued in Twilio
- `sent`: Message sent to carrier
- `delivered`: Message delivered to device
- `failed`: Delivery failed
- `undelivered`: Could not be delivered

### Query Status

```python
status = await sms_service.get_delivery_status("SM123456789")
print(f"Message status: {status['status']}")
```

## Error Handling

The service includes comprehensive error handling:

```python
try:
    result = await sms_service.send(...)
except ValueError as e:
    # Invalid recipients
    print(f"Invalid phone numbers: {e}")
except TwilioClientError as e:
    # Twilio API errors
    print(f"SMS delivery failed: {e}")
```

## Testing

### Unit Tests

Run SMS service tests:
```bash
python -m pytest tests/communication_agent/test_sms_service.py -v
```

### Integration Testing

Use the example script:
```bash
export TEST_SMS_RECIPIENT="+15551234567"
python -m src.communication_agent.examples.sms_integration
```

### Mock Mode

The service includes a mock mode when Twilio SDK is not installed:
- Simulates SMS sending without actual delivery
- Useful for development and testing
- Logs mock operations for debugging

## Best Practices

1. **Use E.164 Format**: Always use international format for phone numbers
2. **Keep Messages Concise**: SMS has strict length limits
3. **Include Action Links**: Use shortened URLs for incident details
4. **Test Delivery**: Verify delivery status for critical alerts
5. **Handle Failures**: Implement fallback channels for failed deliveries
6. **Respect Rate Limits**: Don't exceed 1 message per second per number
7. **Use Templates**: Create reusable templates for common alerts

## Troubleshooting

### Common Issues

1. **"Invalid phone number"**
   - Ensure number is in E.164 format
   - Check country code is included
   - Verify number is SMS-capable

2. **"Authentication failed"**
   - Verify TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
   - Check credentials are not expired

3. **"Message too long"**
   - Message exceeds 5-part limit
   - Review optimization settings
   - Consider using a different channel

4. **"Rate limit exceeded"**
   - Too many messages sent too quickly
   - Implement batching or queuing
   - Use Twilio Messaging Service for higher limits

## Security Considerations

- **Never log full phone numbers**: Use last 4 digits only
- **Sanitize message content**: Remove PII before sending
- **Secure webhooks**: Validate Twilio signatures on callbacks
- **Encrypt credentials**: Use secure storage for API tokens
- **Audit trail**: Log all SMS activities for compliance

## Cost Management

- Set `TWILIO_MAX_PRICE_PER_MESSAGE` to control costs
- Monitor usage through Twilio console
- Use Messaging Services for volume discounts
- Implement message deduplication
- Consider time-based throttling for non-critical alerts
