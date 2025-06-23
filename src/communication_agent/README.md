# Communication Agent

The Communication Agent is responsible for notifying stakeholders about security incidents and remediation actions through various communication channels.

## Implemented Features

### 1. Agent Core Implementation ✅
- `CommunicationAgent` class that inherits from `BaseAgent`
- Notification services initialization and validation
- Template system for message formatting
- Asynchronous message handling with queue support
- Comprehensive logging with agent-specific logger

### 2. Email Notifications ✅
- Full SMTP configuration support (TLS/SSL)
- Email template system with HTML and plain text support
- Attachment handling
- Email queuing with priority support
- Retry mechanism for critical emails
- Validation of email addresses
- Connection pooling and management

### 3. Slack Integration ✅
- Slack API client with retry logic
- Channel configuration and validation
- Rich message formatting with blocks
- Interactive messages with buttons
- Thread management for incident tracking
- Support for channels, users, and direct messages
- Automatic thread creation for incidents

## Configuration

### Email Configuration

Set the following environment variables for email support:

```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
export SMTP_USE_TLS=true
export SMTP_USE_SSL=false
export SMTP_FROM_NAME="SentinelOps"
export SMTP_FROM_ADDRESS=notifications@sentinelops.com
```

### Slack Configuration

Set the following environment variables for Slack support:

```bash
export SLACK_BOT_TOKEN=xoxb-your-bot-token
export SLACK_DEFAULT_CHANNEL="#alerts"
export SLACK_ENABLE_THREADS=true
export SLACK_ENABLE_INTERACTIVE=true
```

To get a Slack bot token:
1. Go to https://api.slack.com/apps
2. Create a new app or select existing
3. Go to 'OAuth & Permissions'
4. Add the following scopes:
   - chat:write
   - channels:read
   - groups:read
5. Install the app to your workspace
6. Copy the 'Bot User OAuth Token'

## Usage Example

```python
from src.communication_agent.agent import CommunicationAgent, NotificationChannel
from src.communication_agent.services.email_service import EmailNotificationService
from src.communication_agent.config.email_config import get_smtp_config

# Create email service
smtp_config = get_smtp_config()
email_service = EmailNotificationService(smtp_config)

# Create communication agent
agent = CommunicationAgent(
    agent_id="comm-agent-001",
    notification_services={
        NotificationChannel.EMAIL: email_service,
    },
)

# Send notification
await agent.send_incident_notification(
    incident_id="INC-001",
    incident_type="Security Breach",
    severity="high",
    affected_resources=["server-01"],
    detection_source="IDS",
    initial_assessment="Unauthorized access detected",
    recipients=[{"channel": "email", "address": "security@example.com"}],
)
```

### Slack Usage Example

```python
from src.communication_agent.services.slack_service import SlackNotificationService
from src.communication_agent.config.slack_config import get_slack_config

# Create Slack service
slack_config = get_slack_config()
slack_service = SlackNotificationService(slack_config)

# Add to communication agent
agent = CommunicationAgent(
    agent_id="comm-agent-001",
    notification_services={
        NotificationChannel.EMAIL: email_service,
        NotificationChannel.SLACK: slack_service,
    },
)

# Send to multiple channels
recipients = [
    {"channel": "email", "address": "security@example.com"},
    {"channel": "slack", "address": "#security-alerts"},
]
```

## Testing

Run the tests:

```bash
# Email service tests
python -m pytest tests/communication_agent/test_email_service.py

# Slack service tests
python -m pytest tests/communication_agent/test_slack_service.py
```

## Next Steps

The following notification channels are ready to be implemented:
- SMS notifications (Twilio)
- Webhook notifications
