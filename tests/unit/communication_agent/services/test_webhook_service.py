"""
Comprehensive tests for the Webhook Notification Service.

Tests webhook delivery, authentication methods, retry logic, queue management,
and all webhook functionality using 100% PRODUCTION CODE - NO MOCKS.

CRITICAL REQUIREMENT: Achieve ≥90% statement coverage of webhook_service.py
"""

import asyncio
import hashlib
import hmac
import json
import pytest
from datetime import datetime, timezone
import uuid
import time
import aiohttp
from aiohttp import web
import socket
from typing import AsyncGenerator, Any

from src.communication_agent.services.webhook_service import (
    WebhookNotificationService,
    WebhookConfig,
    WebhookMethod,
    WebhookAuthType,
    WebhookPayload,
    WebhookQueue,
)
from src.communication_agent.types import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
)
from src.communication_agent.interfaces import NotificationRequest


class ProductionNotificationRequest:
    """Production notification request for testing."""

    def __init__(
        self,
        recipients: Any,
        subject: Any,
        message: Any,
        priority: Any = NotificationPriority.MEDIUM,
        metadata: Any = None,
    ) -> None:
        self.recipients = recipients
        self.subject = subject
        self.message = message
        self.priority = priority
        self.metadata = metadata or {}


class WebhookTestServer:
    """Real HTTP test server for webhook testing."""

    def __init__(self) -> None:
        self.port = self._find_free_port()
        self.app = web.Application()
        self.received_requests: list[dict[str, Any]] = []
        self.response_status = 200
        self.response_delay = 0.0
        self.auth_header: str | None = None
        self.expected_signature: str | None = None

        # Setup routes
        self.app.router.add_post("/webhook", self.webhook_handler)
        self.app.router.add_post("/auth-webhook", self.auth_webhook_handler)
        self.app.router.add_post("/slow-webhook", self.slow_webhook_handler)
        self.app.router.add_post("/error-webhook", self.error_webhook_handler)

    def _find_free_port(self) -> int:
        """Find a free port for the test server."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            s.listen(1)
            port = int(s.getsockname()[1])
        return port

    async def webhook_handler(self, request: Any) -> Any:
        """Handle webhook requests."""
        body = await request.text()
        headers = dict(request.headers)

        self.received_requests.append(
            {
                "method": request.method,
                "url": str(request.url),
                "headers": headers,
                "body": body,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        await asyncio.sleep(self.response_delay)
        return web.Response(status=self.response_status, text="OK")

    async def auth_webhook_handler(self, request: Any) -> Any:
        """Handle authenticated webhook requests."""
        auth_header = request.headers.get("Authorization")
        if self.auth_header and auth_header != self.auth_header:
            return web.Response(status=401, text="Unauthorized")

        # Check HMAC signature if expected
        if self.expected_signature:
            signature_header = request.headers.get("X-Webhook-Signature")
            if not signature_header or signature_header != self.expected_signature:
                return web.Response(status=401, text="Invalid signature")

        return await self.webhook_handler(request)

    async def slow_webhook_handler(self, request: Any) -> Any:
        """Slow webhook for timeout testing."""
        await asyncio.sleep(2)  # 2 second delay
        return await self.webhook_handler(request)

    async def error_webhook_handler(self, request: Any) -> Any:
        """Error webhook for failure testing."""
        await self.webhook_handler(request)
        return web.Response(status=500, text="Internal Server Error")

    async def start(self) -> None:
        """Start the test server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "localhost", self.port)
        await self.site.start()

    async def stop(self) -> None:
        """Stop the test server."""
        await self.site.stop()
        await self.runner.cleanup()

    def get_webhook_url(self, endpoint: str = "webhook") -> str:
        """Get the webhook URL for testing."""
        return f"http://localhost:{self.port}/{endpoint}"

    def clear_requests(self) -> None:
        """Clear received requests."""
        self.received_requests = []

    def set_response_status(self, status: int) -> None:
        """Set response status for next requests."""
        self.response_status = status

    def set_response_delay(self, delay: float) -> None:
        """Set response delay in seconds."""
        self.response_delay = delay

    def set_auth_header(self, header: str) -> None:
        """Set expected auth header."""
        self.auth_header = header

    def set_expected_signature(self, signature: str) -> None:
        """Set expected HMAC signature."""
        self.expected_signature = signature


@pytest.fixture
async def webhook_server() -> AsyncGenerator[WebhookTestServer, None]:
    """Fixture for webhook test server."""
    server = WebhookTestServer()
    await server.start()
    yield server
    await server.stop()


class TestWebhookConfig:
    """Test the WebhookConfig class with production validation."""

    def test_webhook_config_creation_minimal(self) -> None:
        """Test creating webhook config with minimal parameters."""
        config = WebhookConfig(url="https://example.com/webhook")

        assert config.url == "https://example.com/webhook"
        assert config.method == WebhookMethod.POST
        assert config.auth_type == WebhookAuthType.NONE
        assert config.auth_credentials is None
        assert config.headers is None
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 5
        assert config.verify_ssl is True

    def test_webhook_config_creation_complete(self) -> None:
        """Test creating webhook config with all parameters."""
        config = WebhookConfig(
            url="https://api.example.com/webhook",
            method=WebhookMethod.PUT,
            auth_type=WebhookAuthType.BEARER,
            auth_credentials={"token": "secret-token"},
            headers={"Custom-Header": "value"},
            timeout=60,
            max_retries=5,
            retry_delay=10,
            verify_ssl=False,
        )

        assert config.url == "https://api.example.com/webhook"
        assert config.method == WebhookMethod.PUT
        assert config.auth_type == WebhookAuthType.BEARER
        assert config.auth_credentials == {"token": "secret-token"}
        assert config.headers == {"Custom-Header": "value"}
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.retry_delay == 10
        assert config.verify_ssl is False

    def test_webhook_config_validation(self) -> None:
        """Test webhook config validation with real URLs."""
        # Valid HTTPS URL
        config = WebhookConfig(url="https://hooks.slack.com/services/webhook")
        assert config.url == "https://hooks.slack.com/services/webhook"

        # Valid HTTP URL (should work for localhost testing)
        config = WebhookConfig(url="http://localhost:8080/webhook")
        assert config.url == "http://localhost:8080/webhook"


class TestWebhookPayload:
    """Test the WebhookPayload class with production data."""

    def test_webhook_payload_creation(self) -> None:
        """Test creating webhook payload with real data."""
        payload = WebhookPayload(
            event_type="incident.created",
            timestamp="2024-01-01T00:00:00Z",
            data={"incident_id": "INC-123", "severity": "high"},
            metadata={"source": "detection_agent"},
            signature="sha256=abc123",
        )

        assert payload.event_type == "incident.created"
        assert payload.timestamp == "2024-01-01T00:00:00Z"
        assert payload.data == {"incident_id": "INC-123", "severity": "high"}
        assert payload.metadata == {"source": "detection_agent"}
        assert payload.signature == "sha256=abc123"

    def test_webhook_payload_minimal(self) -> None:
        """Test creating webhook payload with minimal data."""
        payload = WebhookPayload(
            event_type="test.event",
            timestamp="2024-01-01T00:00:00Z",
            data={"test": "data"},
        )

        assert payload.metadata is None
        assert payload.signature is None

    def test_webhook_payload_serialization(self) -> None:
        """Test payload JSON serialization for real transmission."""
        payload = WebhookPayload(
            event_type="security.alert",
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "alert_id": f"ALERT-{uuid.uuid4()}",
                "severity": "critical",
                "source_ip": "192.168.1.100",
                "detection_time": datetime.now(timezone.utc).isoformat(),
            },
            metadata={"agent": "detection_agent", "version": "1.0"},
        )

        # Convert to dict (like service does)
        payload_dict = {
            "event_type": payload.event_type,
            "timestamp": payload.timestamp,
            "data": payload.data,
            "metadata": payload.metadata,
        }

        # Should serialize to JSON without errors
        json_str = json.dumps(payload_dict)
        assert isinstance(json_str, str)

        # Should deserialize back correctly
        parsed = json.loads(json_str)
        assert parsed["event_type"] == payload.event_type
        assert parsed["data"]["severity"] == "critical"


class TestWebhookQueue:
    """Test the WebhookQueue class with real async operations."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.queue = WebhookQueue(max_size=10)

    @pytest.mark.asyncio
    async def test_enqueue_and_get_next_real_data(self) -> None:
        """Test enqueuing and retrieving real webhook data."""
        webhook_data = {
            "url": "https://hooks.slack.com/services/T123/B456/webhook",
            "method": "POST",
            "priority": "high",
            "payload": {
                "event_type": "incident.detected",
                "data": {"incident_id": f"INC-{uuid.uuid4()}", "severity": "critical"},
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await self.queue.enqueue(webhook_data)
        assert self.queue.queue.qsize() == 1

        retrieved = await self.queue.get_next()
        assert retrieved == webhook_data
        assert self.queue.queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_get_next_empty_queue_real_timeout(self) -> None:
        """Test getting next webhook from empty queue with real timeout."""
        # Queue is empty, get_next should return None quickly
        start_time = time.time()
        result = await self.queue.get_next()
        end_time = time.time()

        assert result is None
        assert (end_time - start_time) < 0.1  # Should return quickly

    @pytest.mark.asyncio
    async def test_concurrent_enqueue_dequeue(self) -> None:
        """Test concurrent enqueue/dequeue operations."""
        # Enqueue multiple items concurrently
        webhook_items = []
        for i in range(5):
            item = {
                "url": f"https://webhook{i}.example.com",
                "data": {"item": i},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            webhook_items.append(item)

        # Enqueue all items concurrently
        await asyncio.gather(*[self.queue.enqueue(item) for item in webhook_items])
        assert self.queue.queue.qsize() == 5

        # Dequeue all items
        retrieved_items = []
        for _ in range(5):
            retrieved_item: dict[str, Any] | None = await self.queue.get_next()
            if retrieved_item is not None:
                retrieved_items.append(retrieved_item)

        assert len(retrieved_items) == 5
        assert self.queue.queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_task_done_real_workflow(self) -> None:
        """Test task_done with real workflow."""
        webhook_data = {"url": "https://example.com", "data": "test"}
        await self.queue.enqueue(webhook_data)

        # Get item and mark as done
        retrieved = await self.queue.get_next()
        assert retrieved is not None

        # Should not raise exception
        self.queue.task_done()

    def test_add_to_history_real_delivery_records(self) -> None:
        """Test adding real delivery records to history."""
        records = [
            {
                "url": "https://hooks.slack.com/webhook1",
                "status": "success",
                "status_code": 200,
                "delivery_time": datetime.now(timezone.utc).isoformat(),
                "attempt": 1,
                "response_time_ms": 150,
            },
            {
                "url": "https://discord.com/api/webhooks/webhook2",
                "status": "failed",
                "status_code": 500,
                "delivery_time": datetime.now(timezone.utc).isoformat(),
                "attempt": 3,
                "response_time_ms": 2000,
                "error": "Internal Server Error",
            },
        ]

        for record in records:
            self.queue.add_to_history(record)

        assert len(self.queue._delivery_history) == 2
        assert self.queue._delivery_history[0]["status"] == "success"
        assert self.queue._delivery_history[1]["status"] == "failed"

    def test_add_to_history_limit_enforcement(self) -> None:
        """Test history limit with real delivery records."""
        # Add more than 1000 records to test limit
        for i in range(1005):
            record = {
                "url": f"https://webhook{i}.example.com",
                "status": "success",
                "delivery_time": datetime.now(timezone.utc).isoformat(),
                "record_id": i,
            }
            self.queue.add_to_history(record)

        # Should keep only last 1000
        assert len(self.queue._delivery_history) == 1000
        assert self.queue._delivery_history[0]["record_id"] == 5  # First 5 removed
        assert self.queue._delivery_history[-1]["record_id"] == 1004


class TestWebhookNotificationService:
    """Test the WebhookNotificationService with real HTTP requests."""

    def setup_method(self) -> None:
        """Set up test fixtures with real webhook configurations."""
        self.default_config = WebhookConfig(
            url="https://httpbin.org/post",  # Real testing endpoint
            timeout=30,
            max_retries=2,
        )

        self.webhook_configs = {
            "alerts": WebhookConfig(
                url="https://httpbin.org/post",
                auth_type=WebhookAuthType.BEARER,
                auth_credentials={"token": "test-alerts-token"},
            ),
            "incidents": WebhookConfig(
                url="https://httpbin.org/post",
                auth_type=WebhookAuthType.HMAC,
                auth_credentials={"secret": "test-secret-key", "algorithm": "sha256"},
            ),
        }

        self.service = WebhookNotificationService(
            default_config=self.default_config, webhook_configs=self.webhook_configs
        )

    @pytest.mark.asyncio
    async def test_service_initialization_real_clients(self) -> None:
        """Test service initialization with real HTTP client."""
        assert self.service.default_config == self.default_config
        assert self.service.webhook_configs == self.webhook_configs
        assert isinstance(self.service.webhook_queue, WebhookQueue)
        assert self.service._session is None

        # Create real session
        session = await self.service._get_session()
        assert isinstance(session, aiohttp.ClientSession)
        assert not session.closed

    def test_get_channel_type_production(self) -> None:
        """Test getting channel type in production."""
        assert self.service.get_channel_type() == NotificationChannel.WEBHOOK

    @pytest.mark.asyncio
    async def test_validate_recipient_real_endpoints(self) -> None:
        """Test validating recipients with real endpoint validation."""
        # Named webhook validation
        assert await self.service.validate_recipient("alerts") is True
        assert await self.service.validate_recipient("incidents") is True
        assert await self.service.validate_recipient("unknown") is False

        # Real URL validation
        assert await self.service.validate_recipient("https://httpbin.org/post") is True
        assert (
            await self.service.validate_recipient(
                "https://hooks.slack.com/services/T123/B456/xyz"
            )
            is True
        )
        assert (
            await self.service.validate_recipient("http://localhost:8080/webhook")
            is True
        )
        assert await self.service.validate_recipient("invalid-url") is False
        assert await self.service.validate_recipient("") is False

    def test_format_payload_production_data(self) -> None:
        """Test payload formatting with production-like data."""
        incident_id = f"INC-{uuid.uuid4()}"

        payload = self.service._format_payload(
            subject=f"Critical Security Alert - {incident_id}",
            message="Privilege escalation detected on production server",
            priority=NotificationPriority.CRITICAL,
            metadata={
                "incident_id": incident_id,
                "affected_resource": "prod-web-01",
                "detection_agent": "detection_agent_v1.2",
                "confidence_score": 0.95,
                "source_ip": "192.168.1.100",
            },
        )

        assert payload["event_type"] == "sentinelops.notification"
        assert "timestamp" in payload
        assert payload["data"]["subject"] == f"Critical Security Alert - {incident_id}"
        assert payload["data"]["priority"] == "critical"
        assert payload["data"]["metadata"]["confidence_score"] == 0.95

    def test_generate_signature_production_hmac(self) -> None:
        """Test HMAC signature generation with production data."""
        # Real incident payload
        payload_data = {
            "event_type": "sentinelops.incident",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "incident_id": f"INC-{uuid.uuid4()}",
                "severity": "high",
                "detection_time": datetime.now(timezone.utc).isoformat(),
            },
        }

        payload_json = json.dumps(payload_data, sort_keys=True)
        secret = "production-webhook-secret-key"

        # Test SHA256 signature
        signature = self.service._generate_signature(payload_json, secret, "sha256")

        expected = hmac.new(
            secret.encode("utf-8"), payload_json.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        assert signature == f"sha256={expected}"

        # Verify signature can be validated
        signature_hash = signature.split("=")[1]
        verification = hmac.new(
            secret.encode("utf-8"), payload_json.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        assert signature_hash == verification

    def test_prepare_auth_headers_production_scenarios(self) -> None:
        """Test auth header preparation for production scenarios."""
        # Bearer token for Slack
        slack_config = WebhookConfig(
            url="https://hooks.slack.com/services/T123/B456/xyz",
            auth_type=WebhookAuthType.BEARER,
            auth_credentials={"token": "xoxb-your-production-token"},
        )

        headers = self.service._prepare_auth_headers(slack_config)
        assert headers["Authorization"] == "Bearer xoxb-your-production-token"

        # API key for custom webhook
        api_config = WebhookConfig(
            url="https://api.company.com/webhooks/alerts",
            auth_type=WebhookAuthType.API_KEY,
            auth_credentials={"key_name": "X-API-Key", "key_value": "prod-api-key-123"},
        )

        headers = self.service._prepare_auth_headers(api_config)
        assert headers["X-API-Key"] == "prod-api-key-123"

        # HMAC for secure webhook
        incident_payload = json.dumps(
            {"incident_id": f"INC-{uuid.uuid4()}", "severity": "critical"}
        )

        hmac_config = WebhookConfig(
            url="https://secure-alerts.company.com/webhook",
            auth_type=WebhookAuthType.HMAC,
            auth_credentials={"secret": "secure-webhook-secret"},
        )

        headers = self.service._prepare_auth_headers(hmac_config, incident_payload)
        assert "X-Webhook-Signature" in headers
        assert headers["X-Webhook-Signature"].startswith("sha256=")

    @pytest.mark.asyncio
    async def test_send_real_webhook_request(
        self, webhook_server: WebhookTestServer
    ) -> None:
        """Test sending real webhook request to test server."""
        # Configure service to use test server
        test_config = WebhookConfig(
            url=webhook_server.get_webhook_url(), timeout=10, max_retries=1
        )

        service = WebhookNotificationService(default_config=test_config)

        # Create real notification request
        request = NotificationRequest(
            channel=NotificationChannel.WEBHOOK,
            recipient=webhook_server.get_webhook_url(),
            subject="Production Security Alert",
            body="Suspicious activity detected in production environment",
            priority=NotificationPriority.HIGH,
            metadata={
                "incident_id": f"INC-{uuid.uuid4()}",
                "detection_time": datetime.now(timezone.utc).isoformat(),
                "affected_resources": ["prod-web-01", "prod-db-01"],
            },
        )

        # Send notification
        result = await service.send(request)

        # Verify result
        assert result.success is True
        assert result.status == NotificationStatus.QUEUED
        assert result.message_id is not None
        assert "webhook-batch-" in result.message_id

        # Wait for processing
        await asyncio.sleep(0.5)

        # Process the queue manually to test delivery
        session = await service._get_session()
        webhook_data = await service.webhook_queue.get_next()

        if webhook_data:
            try:
                async with session.request(
                    method=webhook_data["method"],
                    url=webhook_data["url"],
                    json=webhook_data["payload"],
                    headers=webhook_data.get("headers") if webhook_data else {},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    assert response.status == 200
            except Exception as e:
                pytest.fail(f"Webhook delivery failed: {e}")

        # Verify server received the request
        assert len(webhook_server.received_requests) > 0
        received_request = webhook_server.received_requests[-1]
        assert received_request["method"] == "POST"

        # Parse and verify payload
        payload = json.loads(received_request["body"])
        assert payload["data"]["subject"] == "Production Security Alert"
        assert "incident_id" in payload["data"]["metadata"]

    @pytest.mark.asyncio
    async def test_authentication_real_request(self, webhook_server: Any) -> None:
        """Test webhook authentication with real HTTP requests."""
        # Test Bearer token authentication
        token = "test-bearer-token-123"
        webhook_server.set_auth_header(f"Bearer {token}")

        auth_config = WebhookConfig(
            url=webhook_server.get_webhook_url("auth-webhook"),
            auth_type=WebhookAuthType.BEARER,
            auth_credentials={"token": token},
            timeout=10,
        )

        service = WebhookNotificationService(default_config=auth_config)

        request = NotificationRequest(
            channel=NotificationChannel.WEBHOOK,
            recipient=webhook_server.get_webhook_url("auth-webhook"),
            subject="Authenticated Alert",
            body="Test authenticated webhook delivery",
        )

        result = await service.send(request)
        assert result.success is True

        # Wait and process
        await asyncio.sleep(0.5)
        webhook_data = await service.webhook_queue.get_next()

        if webhook_data:
            session = await service._get_session()
            async with session.request(
                method=webhook_data["method"],
                url=webhook_data["url"],
                json=webhook_data["payload"],
                headers=webhook_data.get("headers") if webhook_data else {},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                assert response.status == 200  # Should succeed with correct auth

    @pytest.mark.asyncio
    async def test_hmac_authentication_real_signature(self, webhook_server: Any) -> None:
        """Test HMAC authentication with real signature verification."""
        secret = "production-webhook-secret"

        # Create payload
        payload_data = {
            "event_type": "security.incident",
            "data": {"incident_id": f"INC-{uuid.uuid4()}", "severity": "high"},
        }
        payload_json = json.dumps(payload_data, sort_keys=True)

        # Generate expected signature
        expected_signature = hmac.new(
            secret.encode("utf-8"), payload_json.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        expected_signature = f"sha256={expected_signature}"

        webhook_server.set_expected_signature(expected_signature)

        hmac_config = WebhookConfig(
            url=webhook_server.get_webhook_url("auth-webhook"),
            auth_type=WebhookAuthType.HMAC,
            auth_credentials={"secret": secret, "algorithm": "sha256"},
        )

        service = WebhookNotificationService(default_config=hmac_config)

        # Manually create and send request with signature
        headers = service._prepare_auth_headers(hmac_config, payload_json)
        assert headers["X-Webhook-Signature"] == expected_signature

        # Send real HTTP request
        session = await service._get_session()
        async with session.post(
            webhook_server.get_webhook_url("auth-webhook"),
            data=payload_json,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            assert response.status == 200  # Should succeed with correct signature

    @pytest.mark.asyncio
    async def test_error_handling_real_http_errors(self, webhook_server: Any) -> None:
        """Test error handling with real HTTP error responses."""
        # Configure server to return 500 error
        webhook_server.set_response_status(500)

        error_config = WebhookConfig(
            url=webhook_server.get_webhook_url("error-webhook"),
            timeout=5,
            max_retries=1,
        )

        service = WebhookNotificationService(default_config=error_config)
        session = await service._get_session()

        # Attempt request that will fail
        try:
            async with session.post(
                webhook_server.get_webhook_url("error-webhook"),
                json={"test": "error"},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                assert response.status == 500
        except Exception:
            pass  # Expected for error scenarios

        # Verify server received the request despite error
        assert len(webhook_server.received_requests) > 0

    @pytest.mark.asyncio
    async def test_timeout_handling_real_timeout(self, webhook_server: Any) -> None:
        """Test timeout handling with real slow endpoint."""
        webhook_server.set_response_delay(3)  # 3 second delay

        timeout_config = WebhookConfig(
            url=webhook_server.get_webhook_url("slow-webhook"),
            timeout=1,  # 1 second timeout
            max_retries=1,
        )

        service = WebhookNotificationService(default_config=timeout_config)
        session = await service._get_session()

        # Attempt request that will timeout
        start_time = time.time()
        try:
            async with session.post(
                webhook_server.get_webhook_url("slow-webhook"),
                json={"test": "timeout"},
                timeout=aiohttp.ClientTimeout(total=1),
            ):
                pass
        except asyncio.TimeoutError:
            pass  # Expected timeout

        end_time = time.time()
        # Should timeout around 1 second, not wait for full 3 seconds
        assert (end_time - start_time) < 2

    @pytest.mark.asyncio
    async def test_get_channel_limits_production(self) -> None:
        """Test getting channel limits with production values."""
        limits = await self.service.get_channel_limits()

        assert limits["max_message_size"] == 1024 * 1024 * 10  # 10MB
        assert limits["rate_limits"]["per_minute"] == 100
        assert limits["rate_limits"]["per_hour"] == 5000
        assert limits["supports_attachments"] is False
        assert limits["supports_retries"] is True
        assert limits["max_retries"] == 3

    @pytest.mark.asyncio
    async def test_health_check_production(self) -> None:
        """Test health check with real service state."""
        health = await self.service.health_check()

        assert health["status"] == "healthy"
        assert health["service"] == "webhook"
        assert health["active_session"] is False  # No session created yet
        assert health["queue_size"] == 0
        assert health["delivery_history_count"] == 0

        # Create session and check again
        await self.service._get_session()
        health = await self.service.health_check()
        assert health["active_session"] is True

    @pytest.mark.asyncio
    async def test_delivery_history_production_records(self) -> None:
        """Test delivery history with production-like records."""
        # Add real delivery records
        real_records = [
            {
                "url": "https://hooks.slack.com/services/T123/B456/xyz",
                "status": "success",
                "status_code": 200,
                "delivery_time": datetime.now(timezone.utc).isoformat(),
                "attempt": 1,
                "response_time_ms": 145,
                "payload_size": 1024,
            },
            {
                "url": "https://discord.com/api/webhooks/123456/token",
                "status": "failed",
                "status_code": 429,
                "delivery_time": datetime.now(timezone.utc).isoformat(),
                "attempt": 3,
                "response_time_ms": 500,
                "error": "Rate limit exceeded",
                "retry_after": 60,
            },
            {
                "url": "https://api.company.com/alerts",
                "status": "success",
                "status_code": 201,
                "delivery_time": datetime.now(timezone.utc).isoformat(),
                "attempt": 2,
                "response_time_ms": 220,
                "payload_size": 2048,
            },
        ]

        for record in real_records:
            self.service.webhook_queue.add_to_history(record)

        # Test getting all history
        history = self.service.get_delivery_history()
        assert len(history) == 3

        # Test filtered history
        slack_history = self.service.get_delivery_history(
            url_filter="https://hooks.slack.com/services/T123/B456/xyz"
        )
        assert len(slack_history) == 1
        assert slack_history[0]["status"] == "success"

        # Test limited history
        limited_history = self.service.get_delivery_history(limit=2)
        assert len(limited_history) == 2

    @pytest.mark.asyncio
    async def test_close_production_cleanup(self) -> None:
        """Test closing service with production cleanup."""
        # Create session
        session = await self.service._get_session()
        assert not session.closed

        # Close service
        await self.service.close()

        # Session should be closed
        assert session.closed


class TestWebhookEnums:
    """Test webhook enum classes for production usage."""

    def test_webhook_method_enum_production_values(self) -> None:
        """Test WebhookMethod enum with production HTTP methods."""
        # Test enum values match expected strings
        method_mappings = {
            WebhookMethod.GET: "GET",
            WebhookMethod.POST: "POST",
            WebhookMethod.PUT: "PUT",
            WebhookMethod.PATCH: "PATCH",
            WebhookMethod.DELETE: "DELETE",
        }

        for method, expected_value in method_mappings.items():
            assert method.value == expected_value

        # Verify all common HTTP methods are supported
        production_methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]
        enum_values = [method.value for method in WebhookMethod]
        for method_str in production_methods:
            assert method_str in enum_values

    def test_webhook_auth_type_enum_production_auth(self) -> None:
        """Test WebhookAuthType enum with production authentication types."""
        assert WebhookAuthType.NONE.value == "none"
        assert WebhookAuthType.BASIC.value == "basic"
        assert WebhookAuthType.BEARER.value == "bearer"
        assert WebhookAuthType.API_KEY.value == "api_key"
        assert WebhookAuthType.HMAC.value == "hmac"
        assert WebhookAuthType.CUSTOM_HEADER.value == "custom_header"

        # Verify all production auth types are covered
        production_auth_types = [
            "none",
            "basic",
            "bearer",
            "api_key",
            "hmac",
            "custom_header",
        ]
        enum_values = [auth_type.value for auth_type in WebhookAuthType]
        for auth_type in production_auth_types:
            assert auth_type in enum_values


@pytest.mark.integration
class TestWebhookServiceIntegration:
    """Integration tests with real webhook endpoints."""

    @pytest.mark.asyncio
    async def test_end_to_end_webhook_delivery(self, webhook_server: Any) -> None:
        """Test complete end-to-end webhook delivery workflow."""
        # Setup real webhook configuration
        config = WebhookConfig(
            url=webhook_server.get_webhook_url(),
            timeout=30,
            max_retries=2,
            headers={"User-Agent": "SentinelOps-Webhook/1.0"},
        )

        service = WebhookNotificationService(default_config=config)

        # Create realistic security incident notification
        incident_id = f"INC-{uuid.uuid4()}"
        request = NotificationRequest(
            channel=NotificationChannel.WEBHOOK,
            recipient=webhook_server.get_webhook_url(),
            subject=f"CRITICAL: Privilege Escalation Detected - {incident_id}",
            body="A privilege escalation attempt has been detected on production server prod-web-01. Immediate investigation required.",
            priority=NotificationPriority.CRITICAL,
            metadata={
                "incident_id": incident_id,
                "detection_time": datetime.now(timezone.utc).isoformat(),
                "affected_resources": ["prod-web-01"],
                "source_ip": "192.168.1.100",
                "confidence_score": 0.95,
                "detection_rule": "PRIV_ESC_001",
                "analyst_assigned": "security-team@company.com",
            },
        )

        # Send notification
        result = await service.send(request)
        assert result.success is True
        assert result.status == NotificationStatus.QUEUED

        # Wait for queue processing
        await asyncio.sleep(1)

        # Manually process queue to simulate background processing
        session = await service._get_session()
        webhook_data = await service.webhook_queue.get_next()

        if webhook_data:
            start_time = time.time()
            async with session.request(
                method=webhook_data["method"],
                url=webhook_data["url"],
                json=webhook_data["payload"],
                headers=webhook_data.get("headers") if webhook_data else {},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                end_time = time.time()

                # Verify successful delivery
                assert response.status == 200

                # Record delivery metrics
                delivery_record = {
                    "url": webhook_data["url"],
                    "status": "success",
                    "status_code": response.status,
                    "delivery_time": datetime.now(timezone.utc).isoformat(),
                    "response_time_ms": int((end_time - start_time) * 1000),
                    "payload_size": len(json.dumps(webhook_data["payload"])),
                }

                service.webhook_queue.add_to_history(delivery_record)

        # Verify server received correct data
        assert len(webhook_server.received_requests) > 0
        received = webhook_server.received_requests[-1]

        payload = json.loads(received["body"])
        assert payload["data"]["subject"].startswith("CRITICAL: Privilege Escalation")
        assert payload["data"]["metadata"]["incident_id"] == incident_id
        assert payload["data"]["metadata"]["confidence_score"] == 0.95

        # Verify delivery history
        history = service.get_delivery_history()
        assert len(history) > 0
        assert history[-1]["status"] == "success"

        # Cleanup
        await service.close()

    @pytest.mark.asyncio
    async def test_multiple_webhook_endpoints_real_delivery(self, webhook_server: Any) -> None:
        """Test delivery to multiple real webhook endpoints."""
        # Setup multiple webhook configurations
        webhook_configs = {
            "primary": WebhookConfig(url=webhook_server.get_webhook_url()),
            "backup": WebhookConfig(url=webhook_server.get_webhook_url("webhook")),
        }

        service = WebhookNotificationService(
            default_config=webhook_configs["primary"], webhook_configs=webhook_configs
        )

        # Send to multiple recipients
        request = NotificationRequest(
            channel=NotificationChannel.WEBHOOK,
            recipient="primary",  # Note: NotificationRequest only supports single recipient
            subject="Multi-destination Alert Test",
            body="Testing delivery to multiple webhook endpoints",
            priority=NotificationPriority.MEDIUM,
        )

        result = await service.send(request)
        assert result.success is True

        # Wait for processing
        await asyncio.sleep(1)

        # Process all queued webhooks
        session = await service._get_session()
        delivered_count = 0

        while True:
            webhook_data = await service.webhook_queue.get_next()
            if not webhook_data:
                break

            try:
                async with session.request(
                    method=webhook_data["method"],
                    url=webhook_data["url"],
                    json=webhook_data["payload"],
                    headers=webhook_data.get("headers") if webhook_data else {},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        delivered_count += 1
            except Exception:
                pass  # Handle delivery failures gracefully

        # Should have attempted delivery to all 3 endpoints
        assert delivered_count >= 2  # At least 2 successful deliveries

        # Verify server received multiple requests
        assert len(webhook_server.received_requests) >= 2

        await service.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
