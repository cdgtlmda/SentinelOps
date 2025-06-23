#!/usr/bin/env python3
"""Sample Pub/Sub subscriber for testing"""

import json
from concurrent.futures import TimeoutError

from google.cloud import pubsub_v1

PROJECT_ID = "your-gcp-project-id"
SUBSCRIPTION_ID = "detection-events-orchestrator-sub"
TIMEOUT = 30.0


def pull_messages():
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    def callback(message):
        print("Received message: {message.message_id}")

        # Decode the message
        try:
            data = json.loads(message.data.decode("utf-8"))
            print("Message data: {json.dumps(data, indent=2)}")
        except Exception as e:
            print("Failed to decode message: {e}")

        # Acknowledge the message
        message.ack()
        print("Message acknowledged\n")

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print("Listening for messages on {subscription_path}...\n")

    try:
        streaming_pull_future.result(timeout=TIMEOUT)
    except TimeoutError:
        streaming_pull_future.cancel()
        print("No messages received within timeout period.")


if __name__ == "__main__":
    pull_messages()
