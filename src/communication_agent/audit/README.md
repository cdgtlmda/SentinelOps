# Communication Agent Audit Trail Documentation

## Overview

The Communication Agent audit trail provides comprehensive logging and tracking of all notification activities, ensuring compliance with security standards and enabling detailed analysis of communication patterns.

## Features

### 1. Notification History
- Complete record of all sent notifications
- Tracks delivery status (sent, delivered, failed, read)
- Stores message content previews
- Records delivery time metrics
- Maintains sender and recipient information

### 2. Recipient Tracking
- Activity monitoring per recipient
- Delivery success/failure rates
- Channel preferences and usage
- Average read times
- Notification type distribution

### 3. Compliance Reporting
- Support for multiple standards (GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001)
- Automated compliance checks
- PII detection and flagging
- Data retention policy enforcement
- Violation tracking and recommendations

## Configuration

```python
from src.communication_agent.audit import AuditConfig, ComplianceStandard
from pathlib import Path

audit_config = AuditConfig(
    storage_path=Path("data/audit/communication_agent"),
    retention_days=90,  # Data retention period
    max_entries_per_file=10000,  # Entries per audit file
    enable_compression=True,
    compliance_standards=[
        ComplianceStandard.GDPR,
        ComplianceStandard.SOC2
    ],
    pii_detection_enabled=True,
    real_time_monitoring=True,
    export_formats=["json", "csv"]
)
```

## Usage Examples

### Retrieving Notification History

```python
# Get recent notifications
history = await agent.get_notification_history(
    start_date=datetime.utcnow() - timedelta(days=7),
    end_date=datetime.utcnow(),
    channel="email",
    status="delivered",
    limit=100
)

for entry in history:
    print(f"ID: {entry['notification_id']}")
    print(f"Channel: {entry['channel']}")
    print(f"Recipients: {entry['recipients']}")
    print(f"Status: {entry['status']}")
    print(f"Delivery Time: {entry.get('delivery_time_ms', 'N/A')}ms")
```

### Tracking Recipient Activity

```python
# Get activity report for a specific recipient
activity = await agent.get_recipient_activity("user@example.com")

if activity:
    print(f"Total Notifications: {activity['total_notifications']}")
    print(f"Success Rate: {activity['successful_deliveries'] / activity['total_notifications'] * 100:.2f}%")
    print(f"Channels Used: {', '.join(activity['channels_used'])}")
    print(f"Average Read Time: {activity['average_read_time_hours']:.2f} hours")
```

### Generating Compliance Reports

```python
# Generate GDPR compliance report
report = await agent.generate_compliance_report(
    standards=["GDPR", "SOC2"],
    start_date=datetime.utcnow() - timedelta(days=30),
    end_date=datetime.utcnow()
)

print(f"Report ID: {report['report_id']}")
print(f"Total Notifications: {report['total_notifications']}")
print(f"Notifications with PII: {report['notifications_with_pii']}")
print(f"Compliance Violations: {len(report['compliance_violations'])}")
print(f"Recommendations: {report['recommendations']}")
```

### Marking Notifications as Read

```python
# Mark a notification as read by a recipient
await agent.mark_notification_read(
    notification_id="notif_12345",
    recipient="user@example.com",
    channel="email"
)
```

### Exporting Audit Data

```python
# Export audit data as CSV
export_path = await agent.export_audit_data(
    format="csv",
    start_date=datetime.utcnow() - timedelta(days=90),
    end_date=datetime.utcnow(),
    output_path=Path("exports/audit_report.csv")
)
print(f"Audit data exported to: {export_path}")
```

## Storage Structure

The audit trail organizes data in the following directory structure:

```
data/audit/communication_agent/
├── notifications/      # Notification history files
│   ├── audit_20240101_120000.json
│   └── audit_20240102_120000.json
├── recipients/         # Recipient activity tracking
│   └── activities.json
├── compliance/         # Compliance reports
│   └── compliance_20240101_120000.json
└── exports/           # Exported data files
    ├── audit_export_20240101_120000.json
    └── audit_export_20240101_120000.csv
```

## Security Considerations

1. **Data Sanitization**: All notification content is automatically sanitized to remove PII before storage
2. **Access Control**: Audit files should be protected with appropriate file system permissions
3. **Encryption**: Consider encrypting audit files at rest for sensitive environments
4. **Retention**: Automatic cleanup of old audit data based on retention policy

## Performance Metrics

- **Storage Efficiency**: Each audit file can store up to 10,000 entries
- **Query Performance**: Indexed by timestamp for fast retrieval
- **Real-time Monitoring**: Background cleanup tasks run daily
- **Memory Usage**: In-memory caching for recent notifications

## Compliance Standards Support

| Standard | Features |
|----------|----------|
| GDPR | PII detection, data retention, right to erasure |
| HIPAA | PHI detection, access logging, encryption verification |
| SOC2 | Access controls, monitoring, audit trails |
| PCI-DSS | Credit card data detection, secure storage |
| ISO 27001 | Comprehensive logging, incident tracking |

## API Reference

### AuditTrail Class

```python
class AuditTrail:
    async def log_notification(...) -> NotificationAuditEntry
    async def mark_notification_delivered(notification_id, channel)
    async def mark_notification_read(notification_id, recipient, channel)
    async def get_notification_history(...) -> List[NotificationAuditEntry]
    async def get_recipient_report(recipient_id) -> RecipientActivity
    async def generate_compliance_report(...) -> ComplianceReport
    async def export_audit_data(...) -> Path
    async def close()
```

## Best Practices

1. **Regular Exports**: Schedule regular exports of audit data for long-term archival
2. **Compliance Reviews**: Generate monthly compliance reports for security teams
3. **Performance Monitoring**: Track delivery times to ensure SLA compliance
4. **Recipient Analytics**: Use recipient reports to optimize notification strategies
5. **Incident Response**: Leverage audit trail for security incident investigation