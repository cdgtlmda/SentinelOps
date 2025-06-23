"""Google Cloud Pub/Sub tool for ADK agents.

This module provides a Pub/Sub tool implementation using ADK's BaseTool
for publishing and subscribing to messages in Google Cloud Pub/Sub.
"""

import json
import logging
from typing import Any, Callable, Dict, List, Optional, Union

from google.cloud import pubsub_v1
from pydantic import BaseModel, Field, field_validator

from src.common.adk_import_fix import BaseTool

logger = logging.getLogger(__name__)


class PubSubConfig(BaseModel):
    """Configuration for Pub/Sub operations."""

    project_id: str = Field(description="Google Cloud Project ID")
    timeout: float = Field(default=30.0, description="Operation timeout in seconds")
    max_messages: int = Field(
        default=10, description="Maximum messages to pull at once"
    )

    @field_validator("timeout")
    def validate_timeout(cls, v: float) -> float:  # pylint: disable=no-self-argument
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v

    @field_validator("max_messages")
    def validate_max_messages(cls, v: int) -> int:  # pylint: disable=no-self-argument
        if v <= 0 or v > 1000:
            raise ValueError("max_messages must be between 1 and 1000")
        return v


class PublishMessageInput(BaseModel):
    """Input schema for publishing a message."""

    topic_name: str = Field(description="Name of the Pub/Sub topic")
    message: Union[str, Dict[str, Any]] = Field(description="Message to publish")
    attributes: Optional[Dict[str, str]] = Field(
        default=None, description="Optional message attributes"
    )


class PullMessagesInput(BaseModel):
    """Input schema for pulling messages."""

    subscription_name: str = Field(description="Name of the Pub/Sub subscription")
    max_messages: Optional[int] = Field(
        default=None, description="Maximum number of messages to pull"
    )
    auto_acknowledge: bool = Field(
        default=True, description="Automatically acknowledge pulled messages"
    )


class PubSubTool(BaseTool):
    """ADK tool for interacting with Google Cloud Pub/Sub.

    This tool provides methods for:
    - Publishing messages to topics
    - Pulling messages from subscriptions
    - Creating topics and subscriptions
    - Managing message acknowledgments
    """

    def __init__(self, config: PubSubConfig):
        """Initialize the Pub/Sub tool.

        Args:
            config: Pub/Sub configuration
        """
        super().__init__(
            name="pubsub_tool",
            description="Interact with Google Cloud Pub/Sub for message publishing and subscribing",
        )
        self.config = config
        self._publisher = None
        self._subscriber = None

    @property
    def publisher(self) -> pubsub_v1.PublisherClient:
        """Get or create the publisher client."""
        if self._publisher is None:
            self._publisher = pubsub_v1.PublisherClient()
        return self._publisher

    @property
    def subscriber(self) -> pubsub_v1.SubscriberClient:
        """Get or create the subscriber client."""
        if self._subscriber is None:
            self._subscriber = pubsub_v1.SubscriberClient()
        return self._subscriber

    def execute(self, operation: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a Pub/Sub operation.

        Args:
            operation: The operation to perform (publish, pull, create_topic, etc.)
            **kwargs: Operation-specific arguments

        Returns:
            Operation result
        """
        operations: Dict[str, Callable[..., Dict[str, Any]]] = {
            "publish": self._publish_message,
            "pull": self._pull_messages,
            "create_topic": self._create_topic,
            "create_subscription": self._create_subscription,
            "acknowledge": self._acknowledge_messages,
            "list_topics": self._list_topics,
            "list_subscriptions": self._list_subscriptions,
        }

        if operation not in operations:
            raise ValueError(f"Unknown operation: {operation}")

        try:
            func = operations[operation]
            return func(**kwargs)
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Pub/Sub operation '%s' failed: %s", operation, str(e))
            return {"success": False, "error": str(e), "operation": operation}

    def _publish_message(
        self,
        topic_name: str,
        message: Union[str, Dict[str, Any]],
        attributes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Publish a message to a topic.

        Args:
            topic_name: Name of the topic
            message: Message to publish
            attributes: Optional message attributes

        Returns:
            Result dictionary with message_id
        """
        topic_path = self.publisher.topic_path(self.config.project_id, topic_name)

        # Convert message to bytes
        if isinstance(message, dict):
            message_bytes = json.dumps(message).encode("utf-8")
        else:
            message_bytes = str(message).encode("utf-8")

        # Publish the message
        future = self.publisher.publish(topic_path, message_bytes, **(attributes or {}))
        message_id = future.result(timeout=self.config.timeout)

        logger.info("Published message %s to topic %s", message_id, topic_name)
        return {"success": True, "message_id": message_id, "topic": topic_name}

    def _pull_messages(
        self,
        subscription_name: str,
        max_messages: Optional[int] = None,
        auto_acknowledge: bool = True,
    ) -> Dict[str, Any]:
        """Pull messages from a subscription.

        Args:
            subscription_name: Name of the subscription
            max_messages: Maximum messages to pull
            auto_acknowledge: Whether to auto-acknowledge messages

        Returns:
            Result dictionary with messages
        """
        subscription_path = self.subscriber.subscription_path(
            self.config.project_id, subscription_name
        )

        # Pull messages
        response = self.subscriber.pull(
            request={
                "subscription": subscription_path,
                "max_messages": max_messages or self.config.max_messages,
            },
            timeout=self.config.timeout,
        )

        messages = []
        ack_ids = []

        for received_message in response.received_messages:
            message_data = {
                "message_id": received_message.message.message_id,
                "data": received_message.message.data.decode("utf-8"),
                "attributes": dict(received_message.message.attributes),
                "publish_time": received_message.message.publish_time.isoformat(),
                "ack_id": received_message.ack_id,
            }

            # Try to parse JSON data
            try:
                message_data["parsed_data"] = json.loads(message_data["data"])
            except json.JSONDecodeError:
                pass

            messages.append(message_data)
            ack_ids.append(received_message.ack_id)

        # Auto-acknowledge if requested
        if auto_acknowledge and ack_ids:
            self.subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": ack_ids}
            )
            logger.info("Acknowledged %d messages", len(ack_ids))

        return {
            "success": True,
            "messages": messages,
            "count": len(messages),
            "subscription": subscription_name,
            "acknowledged": auto_acknowledge and len(ack_ids) > 0,
        }

    def _create_topic(self, topic_name: str) -> Dict[str, Any]:
        """Create a new Pub/Sub topic.

        Args:
            topic_name: Name of the topic to create

        Returns:
            Result dictionary
        """
        topic_path = self.publisher.topic_path(self.config.project_id, topic_name)

        try:
            topic = self.publisher.create_topic(request={"name": topic_path})
            logger.info("Created topic: %s", topic.name)
            return {"success": True, "topic": topic_name, "path": topic.name}
        except Exception as e:
            if "already exists" in str(e):
                return {
                    "success": True,
                    "topic": topic_name,
                    "message": "Topic already exists",
                }
            raise

    def _create_subscription(
        self, subscription_name: str, topic_name: str, ack_deadline_seconds: int = 60
    ) -> Dict[str, Any]:
        """Create a new subscription.

        Args:
            subscription_name: Name of the subscription
            topic_name: Name of the topic to subscribe to
            ack_deadline_seconds: Acknowledgment deadline

        Returns:
            Result dictionary
        """
        topic_path = self.publisher.topic_path(self.config.project_id, topic_name)
        subscription_path = self.subscriber.subscription_path(
            self.config.project_id, subscription_name
        )

        try:
            subscription = self.subscriber.create_subscription(
                request={
                    "name": subscription_path,
                    "topic": topic_path,
                    "ack_deadline_seconds": ack_deadline_seconds,
                }
            )
            logger.info("Created subscription: %s", subscription.name)
            return {
                "success": True,
                "subscription": subscription_name,
                "topic": topic_name,
                "path": subscription.name,
            }
        except Exception as e:
            if "already exists" in str(e):
                return {
                    "success": True,
                    "subscription": subscription_name,
                    "message": "Subscription already exists",
                }
            raise

    def _acknowledge_messages(
        self, subscription_name: str, ack_ids: List[str]
    ) -> Dict[str, Any]:
        """Acknowledge messages.

        Args:
            subscription_name: Name of the subscription
            ack_ids: List of acknowledgment IDs

        Returns:
            Result dictionary
        """
        subscription_path = self.subscriber.subscription_path(
            self.config.project_id, subscription_name
        )

        self.subscriber.acknowledge(
            request={"subscription": subscription_path, "ack_ids": ack_ids}
        )

        return {
            "success": True,
            "acknowledged": len(ack_ids),
            "subscription": subscription_name,
        }

    def _list_topics(self) -> Dict[str, Any]:
        """List all topics in the project.

        Returns:
            Result dictionary with topic list
        """
        project_path = f"projects/{self.config.project_id}"
        topics = []

        for topic in self.publisher.list_topics(request={"project": project_path}):
            topics.append({"name": topic.name.split("/")[-1], "path": topic.name})

        return {"success": True, "topics": topics, "count": len(topics)}

    def _list_subscriptions(self) -> Dict[str, Any]:
        """List all subscriptions in the project.

        Returns:
            Result dictionary with subscription list
        """
        project_path = f"projects/{self.config.project_id}"
        subscriptions = []

        for subscription in self.subscriber.list_subscriptions(
            request={"project": project_path}
        ):
            subscriptions.append(
                {
                    "name": subscription.name.split("/")[-1],
                    "topic": subscription.topic.split("/")[-1],
                    "path": subscription.name,
                }
            )

        return {
            "success": True,
            "subscriptions": subscriptions,
            "count": len(subscriptions),
        }

    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input/output schema for ADK.

        Returns:
            Schema dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "operations": {
                "publish": {
                    "description": "Publish a message to a topic",
                    "input": PublishMessageInput.model_json_schema(),
                    "output": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "message_id": {"type": "string"},
                            "topic": {"type": "string"},
                        },
                    },
                },
                "pull": {
                    "description": "Pull messages from a subscription",
                    "input": PullMessagesInput.model_json_schema(),
                    "output": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "messages": {"type": "array"},
                            "count": {"type": "integer"},
                            "acknowledged": {"type": "boolean"},
                        },
                    },
                },
            },
        }
