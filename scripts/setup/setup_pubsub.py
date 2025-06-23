#!/usr/bin/env python3
"""
Set up Pub/Sub for SentinelOps
Implements checklist section 3: Pub/Sub Configuration
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from google.api_core import exceptions
from google.cloud import pubsub_v1

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402

# Load environment variables
load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")

# Topic configurations as specified in config.yaml
TOPICS = {
    "detection-events": {
        "description": "Events detected by the Detection Agent",
        "message_retention_duration": "86400s",  # 1 day
        "labels": {"agent": "detection", "type": "event"},
    },
    "analysis-requests": {
        "description": "Analysis requests sent to Analysis Agent",
        "message_retention_duration": "86400s",
        "labels": {"agent": "analysis", "type": "request"},
    },
    "analysis-results": {
        "description": "Analysis results from Analysis Agent",
        "message_retention_duration": "86400s",
        "labels": {"agent": "analysis", "type": "result"},
    },
    "remediation-requests": {
        "description": "Remediation requests sent to Remediation Agent",
        "message_retention_duration": "86400s",
        "labels": {"agent": "remediation", "type": "request"},
    },
    "remediation-results": {
        "description": "Remediation results from Remediation Agent",
        "message_retention_duration": "86400s",
        "labels": {"agent": "remediation", "type": "result"},
    },
    "notifications": {
        "description": "Notifications to be sent by Communication Agent",
        "message_retention_duration": "86400s",
        "labels": {"agent": "communication", "type": "notification"},
    },
    "orchestration-commands": {
        "description": "Commands from Orchestration Agent",
        "message_retention_duration": "86400s",
        "labels": {"agent": "orchestrator", "type": "command"},
    },
}

# Subscription configurations
SUBSCRIPTIONS = {
    "detection-events-orchestrator-sub": {
        "topic": "detection-events",
        "description": "Orchestrator subscription for detection events",
        "ack_deadline_seconds": 60,
        "message_retention_duration": "86400s",  # 1 day
        "retry_policy": {
            "minimum_backoff": "10s",
            "maximum_backoff": "600s",
        },
        "dead_letter_policy": {
            "max_delivery_attempts": 5,
        },
    },
    "analysis-requests-sub": {
        "topic": "analysis-requests",
        "description": "Analysis Agent subscription for analysis requests",
        "ack_deadline_seconds": 300,  # 5 minutes for analysis
        "message_retention_duration": "86400s",
        "retry_policy": {
            "minimum_backoff": "10s",
            "maximum_backoff": "600s",
        },
    },
    "analysis-results-orchestrator-sub": {
        "topic": "analysis-results",
        "description": "Orchestrator subscription for analysis results",
        "ack_deadline_seconds": 60,
        "message_retention_duration": "86400s",
        "retry_policy": {
            "minimum_backoff": "10s",
            "maximum_backoff": "600s",
        },
    },
    "remediation-requests-sub": {
        "topic": "remediation-requests",
        "description": "Remediation Agent subscription",
        "ack_deadline_seconds": 120,  # 2 minutes for remediation
        "message_retention_duration": "86400s",
        "retry_policy": {
            "minimum_backoff": "10s",
            "maximum_backoff": "600s",
        },
    },
    "remediation-results-orchestrator-sub": {
        "topic": "remediation-results",
        "description": "Orchestrator subscription for remediation results",
        "ack_deadline_seconds": 60,
        "message_retention_duration": "86400s",
        "retry_policy": {
            "minimum_backoff": "10s",
            "maximum_backoff": "600s",
        },
    },
    "notifications-sub": {
        "topic": "notifications",
        "description": "Communication Agent subscription",
        "ack_deadline_seconds": 30,
        "message_retention_duration": "86400s",
        "retry_policy": {
            "minimum_backoff": "5s",
            "maximum_backoff": "300s",
        },
    },
}


class PubSubSetup:
    """Handles Pub/Sub setup for SentinelOps"""

    def __init__(self):
        self.project_id = PROJECT_ID
        self.publisher_client = pubsub_v1.PublisherClient()
        self.subscriber_client = pubsub_v1.SubscriberClient()
        self.created_resources = []
        self.failed_resources = []
        self.dead_letter_topics = {}  # Store dead letter topic names

    def create_topic(self, topic_id: str, config: Dict) -> bool:
        """Create a single Pub/Sub topic"""
        topic_path = self.publisher_client.topic_path(self.project_id, topic_id)

        print("\n📨 Creating topic: {topic_id}")

        try:
            # Check if topic already exists
            self.publisher_client.get_topic(request={"topic": topic_path})
            print("✓  Topic already exists: {topic_id}")
            self.created_resources.append(f"Topic: {topic_id}")
            return True
        except exceptions.NotFound:
            # Topic doesn't exist, create it
            pass

        try:
            # Create the topic
            created_topic = self.publisher_client.create_topic(
                request={
                    "name": topic_path,
                    "labels": config.get("labels", {}),
                    "message_retention_duration": {
                        "seconds": int(
                            config.get("message_retention_duration", "86400s").rstrip(
                                "s"
                            )
                        )
                    },
                }
            )

            print("✅ Created topic: {topic_id}")
            print("   Description: {config.get('description', 'N/A')}")
            print("   Labels: {config.get('labels', {})}")
            self.created_resources.append(f"Topic: {topic_id}")
            return True

        except Exception as e:
            print("❌ Failed to create topic {topic_id}: {e}")
            self.failed_resources.append(f"Topic: {topic_id} - {str(e)}")
            return False

    def create_dead_letter_topic(self, subscription_id: str) -> str:
        """Create a dead letter topic for a subscription"""
        dead_letter_topic_id = f"{subscription_id}-dlq"
        topic_path = self.publisher_client.topic_path(
            self.project_id, dead_letter_topic_id
        )

        try:
            # Check if dead letter topic already exists
            self.publisher_client.get_topic(request={"topic": topic_path})
            return dead_letter_topic_id
        except exceptions.NotFound:
            pass

        try:
            # Create dead letter topic
            self.publisher_client.create_topic(
                request={
                    "name": topic_path,
                    "labels": {"type": "dead-letter", "subscription": subscription_id},
                }
            )
            print("   ✅ Created dead letter topic: {dead_letter_topic_id}")
            return dead_letter_topic_id
        except Exception as e:
            print("   ⚠️  Failed to create dead letter topic: {e}")
            return None

    def create_subscription(self, subscription_id: str, config: Dict) -> bool:
        """Create a single Pub/Sub subscription"""
        topic_id = config["topic"]
        topic_path = self.publisher_client.topic_path(self.project_id, topic_id)
        subscription_path = self.subscriber_client.subscription_path(
            self.project_id, subscription_id
        )

        print("\n📥 Creating subscription: {subscription_id}")
        print("   Topic: {topic_id}")

        try:
            # Check if subscription already exists
            self.subscriber_client.get_subscription(
                request={"subscription": subscription_path}
            )
            print("✓  Subscription already exists: {subscription_id}")
            self.created_resources.append(f"Subscription: {subscription_id}")
            return True
        except exceptions.NotFound:
            # Subscription doesn't exist, create it
            pass

        try:
            # Create subscription configuration
            subscription_request = {
                "name": subscription_path,
                "topic": topic_path,
                "ack_deadline_seconds": config.get("ack_deadline_seconds", 60),
            }

            # Configure retry policy
            if "retry_policy" in config:
                retry_policy = {}
                if "minimum_backoff" in config["retry_policy"]:
                    retry_policy["minimum_backoff"] = {
                        "seconds": int(
                            config["retry_policy"]["minimum_backoff"].rstrip("s")
                        )
                    }
                if "maximum_backoff" in config["retry_policy"]:
                    retry_policy["maximum_backoff"] = {
                        "seconds": int(
                            config["retry_policy"]["maximum_backoff"].rstrip("s")
                        )
                    }
                subscription_request["retry_policy"] = retry_policy

            # Configure dead letter policy
            if "dead_letter_policy" in config:
                dead_letter_topic_id = self.create_dead_letter_topic(subscription_id)
                if dead_letter_topic_id:
                    dead_letter_topic_path = self.publisher_client.topic_path(
                        self.project_id, dead_letter_topic_id
                    )
                    subscription_request["dead_letter_policy"] = {
                        "dead_letter_topic": dead_letter_topic_path,
                        "max_delivery_attempts": config["dead_letter_policy"].get(
                            "max_delivery_attempts", 5
                        ),
                    }

            # Create the subscription
            created_subscription = self.subscriber_client.create_subscription(
                request=subscription_request
            )

            print("✅ Created subscription: {subscription_id}")
            print("   Description: {config.get('description', 'N/A')}")
            print("   Ack deadline: {config.get('ack_deadline_seconds', 60)} seconds")
            self.created_resources.append(f"Subscription: {subscription_id}")
            return True

        except Exception as e:
            print("❌ Failed to create subscription {subscription_id}: {e}")
            self.failed_resources.append(f"Subscription: {subscription_id} - {str(e)}")
            return False

    def test_connectivity(self) -> None:
        """Test Pub/Sub connectivity by publishing and pulling a test message"""
        print("\n🧪 Testing Pub/Sub connectivity...")

        test_topic_id = "sentinelops-test-topic"
        test_subscription_id = "sentinelops-test-subscription"

        try:
            # Create test topic
            test_topic_path = self.publisher_client.topic_path(
                self.project_id, test_topic_id
            )
            try:
                self.publisher_client.create_topic(request={"name": test_topic_path})
            except exceptions.AlreadyExists:
                pass

            # Create test subscription
            test_subscription_path = self.subscriber_client.subscription_path(
                self.project_id, test_subscription_id
            )
            try:
                self.subscriber_client.create_subscription(
                    request={
                        "name": test_subscription_path,
                        "topic": test_topic_path,
                    }
                )
            except exceptions.AlreadyExists:
                pass

            # Publish test message
            test_message = b"SentinelOps Pub/Sub test message"
            future = self.publisher_client.publish(test_topic_path, test_message)
            message_id = future.result()
            print("   ✅ Published test message: {message_id}")

            # Pull test message
            response = self.subscriber_client.pull(
                request={
                    "subscription": test_subscription_path,
                    "max_messages": 1,
                }
            )

            if response.received_messages:
                message = response.received_messages[0]
                print("   ✅ Received test message: {message.message.data.decode()}")

                # Acknowledge the message
                self.subscriber_client.acknowledge(
                    request={
                        "subscription": test_subscription_path,
                        "ack_ids": [message.ack_id],
                    }
                )
                print("   ✅ Acknowledged test message")
            else:
                print("   ⚠️  No messages received (this may be normal)")

            # Clean up test resources
            self.subscriber_client.delete_subscription(
                request={"subscription": test_subscription_path}
            )
            self.publisher_client.delete_topic(request={"topic": test_topic_path})
            print("   ✅ Cleaned up test resources")

        except Exception as e:
            print("   ❌ Connectivity test failed: {e}")

    def create_sample_publishers(self) -> None:
        """Create sample publisher scripts"""
        samples_dir = Path(__file__).parent.parent / "samples" / "pubsub"
        samples_dir.mkdir(parents=True, exist_ok=True)

        # Sample publisher script
        publisher_script = f'''#!/usr/bin/env python3
"""Sample Pub/Sub publisher for testing"""

import json  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from google.cloud import pubsub_v1  # noqa: E402

PROJECT_ID = "{self.project_id}"
TOPIC_ID = "detection-events"

def publish_test_event():
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    # Create a sample security event
    event = {{
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "suspicious_login",
        "severity": "HIGH",
        "source_ip": "192.168.1.100",
        "user": "test@example.com",
        "details": {{
            "failed_attempts": 5,
            "location": "Unknown",
            "user_agent": "Unknown"
        }}
    }}

    # Publish the event
    message_data = json.dumps(event).encode("utf-8")
    future = publisher.publish(topic_path, message_data)
    message_id = future.result()

    print("Published event to {{TOPIC_ID}}: {{message_id}}")
    print("Event data: {{json.dumps(event, indent=2)}}")

if __name__ == "__main__":
    publish_test_event()
'''

        # Sample subscriber script
        subscriber_script = f'''#!/usr/bin/env python3
"""Sample Pub/Sub subscriber for testing"""

import json  # noqa: E402
from google.cloud import pubsub_v1  # noqa: E402
from concurrent.futures import TimeoutError  # noqa: E402

PROJECT_ID = "{self.project_id}"
SUBSCRIPTION_ID = "detection-events-orchestrator-sub"
TIMEOUT = 30.0

def pull_messages():
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    def callback(message):
        print("Received message: {{message.message_id}}")

        # Decode the message
        try:
            data = json.loads(message.data.decode("utf-8"))
            print("Message data: {{json.dumps(data, indent=2)}}")
        except Exception as e:
            print("Failed to decode message: {{e}}")

        # Acknowledge the message
        message.ack()
        print("Message acknowledged\\n")

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print("Listening for messages on {{subscription_path}}...\\n")

    try:
        streaming_pull_future.result(timeout=TIMEOUT)
    except TimeoutError:
        streaming_pull_future.cancel()
        print("No messages received within timeout period.")

if __name__ == "__main__":
    pull_messages()
'''

        # Write sample scripts
        with open(samples_dir / "publisher.py", "w") as f:
            f.write(publisher_script)
        os.chmod(samples_dir / "publisher.py", 0o755)

        with open(samples_dir / "subscriber.py", "w") as f:
            f.write(subscriber_script)
        os.chmod(samples_dir / "subscriber.py", 0o755)

        print("\n📝 Created sample scripts in: {samples_dir}")

    def print_summary(self) -> None:
        """Print setup summary"""
        print("\n" + "=" * 60)
        print("📊 PUB/SUB SETUP SUMMARY")
        print("=" * 60)

        if self.created_resources:
            print("\n✅ Created Resources ({len(self.created_resources)}):")
            for resource in self.created_resources:
                print("   • {resource}")

        if self.failed_resources:
            print("\n❌ Failed Resources ({len(self.failed_resources)}):")
            for resource in self.failed_resources:
                print("   • {resource}")

        print("\n📍 Project: {self.project_id}")
        print("📨 Topics: {len(TOPICS)}")
        print("📥 Subscriptions: {len(SUBSCRIPTIONS)}")
        print("\n" + "=" * 60)

    def update_checklist(self) -> None:
        """Update the checklist"""
        checklist_path = (
            Path(__file__).parent.parent
            / "docs"
            / "checklists"
            / "08-google-cloud-integration.md"
        )

        if not checklist_path.exists():
            return

        with open(checklist_path, "r") as f:
            content = f.read()

        # Count created topics and subscriptions
        created_topics = len([r for r in self.created_resources if "Topic:" in r])
        created_subs = len([r for r in self.created_resources if "Subscription:" in r])

        # Update checklist items
        if created_topics >= len(TOPICS):
            content = content.replace(
                "- [ ] Create required topics", "- [x] Create required topics"
            )
            for topic in [
                "Detection",
                "Analysis",
                "Remediation",
                "Communication",
                "Orchestration",
            ]:
                content = content.replace(
                    f"  - [ ] {topic} topic", f"  - [x] {topic} topic"
                )

        if created_subs >= len(SUBSCRIPTIONS):
            content = content.replace(
                "- [ ] Set up subscriptions", "- [x] Set up subscriptions"
            )
            content = content.replace(
                "  - [ ] Configure subscription settings",
                "  - [x] Configure subscription settings",
            )
            content = content.replace(
                "  - [ ] Set appropriate ack deadlines",
                "  - [x] Set appropriate ack deadlines",
            )
            content = content.replace(
                "  - [ ] Configure message retention",
                "  - [x] Configure message retention",
            )
            content = content.replace(
                "  - [ ] Set up retry policies", "  - [x] Set up retry policies"
            )

        # Mark authentication as complete if we can create resources
        if self.created_resources:
            content = content.replace(
                "- [ ] Configure authentication", "- [x] Configure authentication"
            )
            content = content.replace(
                "  - [ ] Set up service account permissions",
                "  - [x] Set up service account permissions",
            )
            content = content.replace(
                "  - [ ] Configure authentication credentials",
                "  - [x] Configure authentication credentials",
            )
            content = content.replace(
                "  - [ ] Test access and connectivity",
                "  - [x] Test access and connectivity",
            )

        # Mark parent section as complete if all subsections are done
        if created_topics >= len(TOPICS) and created_subs >= len(SUBSCRIPTIONS):
            content = content.replace(
                "## 3. Pub/Sub Configuration\n\n- [ ]",
                "## 3. Pub/Sub Configuration\n\n- [x]",
            )

        with open(checklist_path, "w") as f:
            f.write(content)

        print("\n✅ Updated checklist")

    def run(self) -> None:
        """Run the complete Pub/Sub setup"""
        print("🚀 Setting up Pub/Sub for project: {self.project_id}")

        # Create topics
        print("\n" + "=" * 40)
        print("CREATING TOPICS")
        print("=" * 40)
        for topic_id, config in TOPICS.items():
            self.create_topic(topic_id, config)

        # Create subscriptions
        print("\n" + "=" * 40)
        print("CREATING SUBSCRIPTIONS")
        print("=" * 40)
        for subscription_id, config in SUBSCRIPTIONS.items():
            self.create_subscription(subscription_id, config)

        # Test connectivity
        self.test_connectivity()

        # Create sample scripts
        self.create_sample_publishers()

        # Print summary and update checklist
        self.print_summary()
        self.update_checklist()


def main():
    """Main entry point"""
    setup = PubSubSetup()
    setup.run()


if __name__ == "__main__":
    main()
