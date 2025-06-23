#!/usr/bin/env python3
"""Sample Pub/Sub publisher for testing"""

import json
from datetime import datetime, timezone

from google.cloud import pubsub_v1

PROJECT_ID = "your-gcp-project-id"
TOPIC_ID = "detection-events"


def publish_test_event():
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    # Create a sample security event
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "suspicious_login",
        "severity": "HIGH",
        "source_ip": "192.168.1.100",
        "user": "test@example.com",
        "details": {
            "failed_attempts": 5,
            "location": "Unknown",
            "user_agent": "Unknown",
        },
    }

    # Publish the event
    message_data = json.dumps(event).encode("utf-8")
    future = publisher.publish(topic_path, message_data)
    message_id = future.result()

    print("Published event to {TOPIC_ID}: {message_id}")
    print("Event data: {json.dumps(event, indent=2)}")


if __name__ == "__main__":
    publish_test_event()
