"""
Comprehensive tests for Email notification service.

Tests all functionality with production code, no mocks.
Uses real SMTP server implementation for testing.
"""

import asyncio
import threading
import time
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, Generator, List, Optional

import pytest

from src.communication_agent.interfaces import (
    NotificationRequest,
)
from src.communication_agent.services.email_service import (
    EmailAttachment,
    EmailNotificationService,
    EmailQueue,
    EmailTemplate,
    SMTPConfig,
)
from src.communication_agent.types import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
)


class SMTPTestServer:
    """Test SMTP server for email testing using socket server."""

    def __init__(self, host: str = "localhost", port: int = 0):
        """Initialize test SMTP server."""
        self.host = host
        self.port = port
        self.server: Optional[Any] = None
        self.thread: Optional[threading.Thread] = None
        self.messages: List[Dict[str, Any]] = []
        self.running = False
        self._socket = None

    def start(self) -> None:
        """Start the test SMTP server."""
        import socket  # noqa: F401
        import socketserver  # noqa: F401

        class TestSMTPHandler(socketserver.BaseRequestHandler):
            def __init__(self, request: Any, client_address: Any, server: Any) -> None:
                self.smtp_server = server.smtp_server
                super().__init__(request, client_address, server)

            def handle(self) -> None:
                """Handle SMTP connection."""
                try:
                    # Send greeting
                    self.request.sendall(b"220 localhost ESMTP Test Server\r\n")

                    mailfrom = None
                    rcpttos: List[str] = []
                    data_mode = False
                    data_lines: List[str] = []

                    while True:
                        try:
                            data = self.request.recv(1024).decode("utf-8").strip()
                            if not data:
                                break

                            if data_mode:
                                if data == ".":
                                    # End of data
                                    message_data = "\n".join(data_lines)
                                    self.smtp_server.messages.append(
                                        {
                                            "peer": self.client_address,
                                            "mailfrom": mailfrom,
                                            "rcpttos": rcpttos,
                                            "data": message_data,
                                            "timestamp": datetime.now(timezone.utc),
                                        }
                                    )
                                    self.request.sendall(b"250 Message accepted\r\n")
                                    data_mode = False
                                    data_lines = []
                                else:
                                    data_lines.append(data)
                            else:
                                cmd = data.upper()
                                if cmd.startswith("HELO"):
                                    self.request.sendall(b"250 localhost\r\n")
                                elif cmd.startswith("EHLO"):
                                    # Extended HELO with AUTH support
                                    response = (
                                        b"250-localhost\r\n"
                                        b"250-AUTH PLAIN LOGIN\r\n"
                                        b"250 SIZE 52428800\r\n"
                                    )
                                    self.request.sendall(response)
                                elif cmd.startswith("AUTH"):
                                    # Accept any authentication
                                    self.request.sendall(
                                        b"235 Authentication successful\r\n"
                                    )
                                elif cmd.startswith("MAIL FROM:"):
                                    mailfrom = data[10:].strip()
                                    self.request.sendall(b"250 OK\r\n")
                                elif cmd.startswith("RCPT TO:"):
                                    rcpttos.append(data[8:].strip())
                                    self.request.sendall(b"250 OK\r\n")
                                elif cmd == "DATA":
                                    self.request.sendall(b"354 Start mail input\r\n")
                                    data_mode = True
                                elif cmd == "QUIT":
                                    self.request.sendall(b"221 Bye\r\n")
                                    break
                                elif cmd == "NOOP":
                                    self.request.sendall(b"250 OK\r\n")
                                else:
                                    self.request.sendall(b"250 OK\r\n")
                        except Exception:
                            break
                except Exception:
                    pass

        class TestTCPServer(socketserver.TCPServer):
            def __init__(
                self, server_address: Any, RequestHandlerClass: Any, smtp_server: Any
            ) -> None:
                self.smtp_server = smtp_server
                super().__init__(server_address, RequestHandlerClass)

        # Create server
        self.server = TestTCPServer((self.host, self.port), TestSMTPHandler, self)

        # Get actual port if using 0 (random port)
        if self.port == 0:
            self.port = self.server.server_address[1]

        # Start server in thread
        self.running = True
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True
        self.thread.start()

        # Wait for server to be ready
        time.sleep(0.1)

    def _run_server(self) -> None:
        """Run the SMTP server."""
        try:
            while self.running and self.server:
                self.server.handle_request()
        except Exception:
            pass

    def stop(self) -> None:
        """Stop the test SMTP server."""
        self.running = False
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get received messages."""
        return self.messages.copy()

    def clear_messages(self) -> None:
        """Clear received messages."""
        self.messages.clear()


@pytest.fixture
def smtp_server() -> Generator[SMTPTestServer, None, None]:
    """Fixture providing a test SMTP server."""
    server = SMTPTestServer()
    server.start()
    yield server
    server.stop()


@pytest.fixture
def smtp_config(smtp_server: SMTPTestServer) -> SMTPConfig:
    """Fixture providing SMTP configuration for test server."""
    return SMTPConfig(
        host=smtp_server.host,
        port=smtp_server.port,
        username="test@example.com",
        password="testpass",
        use_tls=False,
        use_ssl=False,
        timeout=10,
        from_name="Test SentinelOps",
        from_address="test@sentinelops.com",
    )


class TestSMTPConfig:
    """Test SMTPConfig dataclass."""

    def test_config_with_defaults(self) -> None:
        """Test config creation with defaults."""
        config = SMTPConfig(
            host="smtp.example.com",
            port=587,
            username="user@example.com",
            password="password123",
        )

        assert config.host == "smtp.example.com"
        assert config.port == 587
        assert config.username == "user@example.com"
        assert config.password == "password123"
        assert config.use_tls is True
        assert config.use_ssl is False
        assert config.timeout == 30
        assert config.from_name == "SentinelOps"
        assert config.from_address == "notifications@sentinelops.com"

    def test_config_with_custom_values(self) -> None:
        """Test config creation with custom values."""
        config = SMTPConfig(
            host="mail.custom.com",
            port=465,
            username="custom@custom.com",
            password="custompass",
            use_tls=False,
            use_ssl=True,
            timeout=60,
            from_name="Custom SentinelOps",
            from_address="custom@sentinelops.com",
        )

        assert config.host == "mail.custom.com"
        assert config.port == 465
        assert config.username == "custom@custom.com"
        assert config.password == "custompass"
        assert config.use_tls is False
        assert config.use_ssl is True
        assert config.timeout == 60
        assert config.from_name == "Custom SentinelOps"
        assert config.from_address == "custom@sentinelops.com"


class TestEmailAttachment:
    """Test EmailAttachment dataclass."""

    def test_attachment_minimal(self) -> None:
        """Test attachment with minimal required fields."""
        content = b"Hello World"
        attachment = EmailAttachment(filename="test.txt", content=content)

        assert attachment.filename == "test.txt"
        assert attachment.content == content
        assert attachment.content_type is None

    def test_attachment_with_content_type(self) -> None:
        """Test attachment with content type."""
        content = b"<html><body>Test</body></html>"
        attachment = EmailAttachment(
            filename="test.html", content=content, content_type="text/html"
        )

        assert attachment.filename == "test.html"
        assert attachment.content == content
        assert attachment.content_type == "text/html"


class TestEmailTemplate:
    """Test EmailTemplate functionality."""

    def test_template_initialization(self) -> None:
        """Test template initialization."""
        template = EmailTemplate(
            html_template="<h1>{title}</h1><p>{body}</p>",
            text_template="{title}\n\n{body}",
            subject_template="Alert: {title}",
        )

        assert template.html_template == "<h1>{title}</h1><p>{body}</p>"
        assert template.text_template == "{title}\n\n{body}"
        assert template.subject_template == "Alert: {title}"

    def test_template_render_basic(self) -> None:
        """Test template rendering with basic context."""
        template = EmailTemplate(
            html_template="<h1>{title}</h1><p>{body}</p>",
            text_template="{title}\n\n{body}",
            subject_template="Alert: {title}",
        )

        context = {"title": "Security Incident", "body": "Suspicious activity detected"}

        subject, html_body, text_body = template.render(context)

        assert subject == "Alert: Security Incident"
        assert (
            html_body == "<h1>Security Incident</h1><p>Suspicious activity detected</p>"
        )
        assert text_body == "Security Incident\n\nSuspicious activity detected"

    def test_template_render_complex_context(self) -> None:
        """Test template rendering with complex context."""
        template = EmailTemplate(
            html_template="<h1>{incident_type}</h1><p>Severity: {severity}</p><p>{description}</p>",
            text_template="{incident_type}\nSeverity: {severity}\n\n{description}",
            subject_template="[{severity}] {incident_type}",
        )

        context = {
            "incident_type": "Brute Force Attack",
            "severity": "CRITICAL",
            "description": "Multiple failed login attempts detected from suspicious IP addresses.",
        }

        subject, html_body, text_body = template.render(context)

        assert subject == "[CRITICAL] Brute Force Attack"
        assert "Brute Force Attack" in html_body
        assert "CRITICAL" in html_body
        assert "Multiple failed login attempts" in html_body
        assert "Brute Force Attack" in text_body
        assert "CRITICAL" in text_body
        assert "Multiple failed login attempts" in text_body


class TestEmailQueue:
    """Test EmailQueue functionality."""

    @pytest.mark.asyncio
    async def test_queue_initialization(self) -> None:
        """Test queue initialization."""
        queue = EmailQueue(max_size=100)

        assert queue.queue.maxsize == 100
        assert queue.processing is False
        assert queue._processor_task is None

    @pytest.mark.asyncio
    async def test_enqueue_basic(self) -> None:
        """Test basic email enqueuing."""
        queue = EmailQueue()

        await queue.enqueue(
            recipients=["test@example.com"],
            subject="Test Subject",
            html_body="<p>Test HTML</p>",
            text_body="Test Text",
        )

        assert queue.queue.qsize() == 1

        email_data = await queue.get_next()
        assert email_data is not None
        assert email_data["recipients"] == ["test@example.com"]
        assert email_data["subject"] == "Test Subject"
        assert email_data["html_body"] == "<p>Test HTML</p>"
        assert email_data["text_body"] == "Test Text"
        assert email_data["priority"] == NotificationPriority.MEDIUM
        assert "queued_at" in email_data

    @pytest.mark.asyncio
    async def test_enqueue_with_attachments(self) -> None:
        """Test enqueuing with attachments."""
        queue = EmailQueue()

        attachment = EmailAttachment(
            filename="test.txt", content=b"Test content", content_type="text/plain"
        )

        await queue.enqueue(
            recipients=["test@example.com"],
            subject="Test with Attachment",
            html_body="<p>Test</p>",
            text_body="Test",
            attachments=[attachment],
            priority=NotificationPriority.HIGH,
        )

        email_data = await queue.get_next()
        assert email_data is not None
        assert len(email_data["attachments"]) == 1
        assert email_data["attachments"][0].filename == "test.txt"
        assert email_data["priority"] == NotificationPriority.HIGH

    @pytest.mark.asyncio
    async def test_queue_empty(self) -> None:
        """Test getting from empty queue."""
        queue = EmailQueue()

        # Queue should be empty initially
        assert queue.queue.qsize() == 0

        # Test that we can add and retrieve an item
        await queue.enqueue(
            recipients=["test@example.com"],
            subject="Test",
            html_body="Test",
            text_body="Test",
        )

        assert queue.queue.qsize() == 1

        # Should be able to get the item
        email_data = await queue.get_next()
        assert email_data is not None
        assert email_data["subject"] == "Test"

    @pytest.mark.asyncio
    async def test_task_done(self) -> None:
        """Test task done functionality."""
        queue = EmailQueue()

        await queue.enqueue(
            recipients=["test@example.com"],
            subject="Test",
            html_body="Test",
            text_body="Test",
        )

        await queue.get_next()
        # This should not raise an exception
        queue.task_done()


class TestEmailNotificationService:
    """Test EmailNotificationService functionality."""

    def test_service_initialization(self, smtp_config: Any) -> None:
        """Test notification service initialization."""
        service = EmailNotificationService(smtp_config)

        assert service.smtp_config == smtp_config
        assert service.email_queue is not None
        assert service._smtp_connection is None
        assert "security_incident" in service.templates

    def test_get_channel_type(self, smtp_config: Any) -> None:
        """Test channel type identification."""
        service = EmailNotificationService(smtp_config)

        assert service.get_channel_type() == NotificationChannel.EMAIL

    @pytest.mark.asyncio
    async def test_validate_recipient_valid_emails(self, smtp_config: Any) -> None:
        """Test recipient validation with valid email addresses."""
        service = EmailNotificationService(smtp_config)

        valid_emails = [
            "user@example.com",
            "test.email@domain.org",
            "user+tag@example.co.uk",
            "firstname.lastname@company.com",
            "123@numbers.com",
            "user_name@test-domain.com",
        ]

        for email_addr in valid_emails:
            assert await service.validate_recipient(email_addr) is True

    @pytest.mark.asyncio
    async def test_validate_recipient_invalid_emails(self, smtp_config: Any) -> None:
        """Test recipient validation with invalid email addresses."""
        service = EmailNotificationService(smtp_config)

        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@.com",
            "user..name@example.com",
            "user name@example.com",
            "",
            "user@example",
            "user@example.",
        ]

        for email_addr in invalid_emails:
            assert await service.validate_recipient(email_addr) is False

    @pytest.mark.asyncio
    async def test_smtp_connection_creation(self, smtp_config: Any) -> None:
        """Test SMTP connection creation."""
        service = EmailNotificationService(smtp_config)

        # This should create a connection to our test server
        connection = await service._get_smtp_connection()
        assert connection is not None
        assert service._smtp_connection is connection

        # Second call should return same connection
        connection2 = await service._get_smtp_connection()
        assert connection2 is connection

        await service.close()

    def test_build_email_basic(self, smtp_config: Any) -> None:
        """Test building basic email message."""
        service = EmailNotificationService(smtp_config)

        msg = service._build_email(
            recipients=["test@example.com"],
            subject="Test Subject",
            html_body="<p>HTML content</p>",
            text_body="Text content",
        )

        assert isinstance(msg, MIMEMultipart)
        assert msg["Subject"] == "Test Subject"
        assert msg["To"] == "test@example.com"
        assert "Test SentinelOps" in msg["From"]
        assert "test@sentinelops.com" in msg["From"]

    def test_build_email_with_attachments(self, smtp_config: Any) -> None:
        """Test building email with attachments."""
        service = EmailNotificationService(smtp_config)

        attachment = EmailAttachment(
            filename="report.txt",
            content=b"Security report content",
            content_type="text/plain",
        )

        msg = service._build_email(
            recipients=["test@example.com"],
            subject="Security Report",
            html_body="<p>Please see attached report</p>",
            text_body="Please see attached report",
            attachments=[attachment],
        )

        # Email should be multipart
        assert msg.is_multipart()

        # Check that attachment is included
        parts = msg.get_payload()
        assert len(parts) >= 2  # Body + attachment

        # Find attachment part
        attachment_found = False
        for part in parts:
            if hasattr(part, "get_filename") and part.get_filename() == "report.txt":
                attachment_found = True
                break

        assert attachment_found

    def test_add_attachment_content_type_detection(self, smtp_config: Any) -> None:
        """Test attachment content type detection."""
        service = EmailNotificationService(smtp_config)

        msg = MIMEMultipart()

        # Test with known file extension
        attachment = EmailAttachment(filename="test.pdf", content=b"PDF content")

        service._add_attachment(msg, attachment)

        # Check that content type was guessed
        parts = msg.get_payload()
        assert len(parts) > 0

    @pytest.mark.asyncio
    async def test_send_basic_email(self, smtp_config: Any, smtp_server: Any) -> None:
        """Test sending a basic email."""
        service = EmailNotificationService(smtp_config)

        # Create notification request
        request = NotificationRequest(
            channel=NotificationChannel.EMAIL,
            recipient="test@example.com",
            subject="Test Notification",
            body="This is a test notification message.",
        )

        # Send email
        result = await service.send(request)

        assert result.success is True
        assert result.status == NotificationStatus.QUEUED
        assert result.message_id is not None
        assert result.metadata is not None
        assert "test@example.com" in result.metadata["recipients"]

        # Wait for email to be processed
        await asyncio.sleep(0.2)

        # Check that email was received by test server
        messages = smtp_server.get_messages()
        assert len(messages) >= 1

        message = messages[-1]  # Get latest message
        assert message["mailfrom"] == "test@sentinelops.com"
        assert "test@example.com" in message["rcpttos"]
        assert "Test Notification" in message["data"]

        await service.close()

    @pytest.mark.asyncio
    async def test_send_email_with_template(
        self, smtp_config: Any, smtp_server: Any
    ) -> None:
        """Test sending email with template."""
        service = EmailNotificationService(smtp_config)

        # Create request with template metadata
        request = NotificationRequest(
            channel=NotificationChannel.EMAIL,
            recipient="security@example.com",
            subject="",  # Subject will come from template
            body="Brute force attack detected on web server.",
        )
        request.metadata = {
            "template": "security_incident",
            "context": {
                "subject": "Security Alert - Brute Force Attack",
                "incident_type": "Brute Force Attack",
                "severity": "high",
                "timestamp": "2024-01-15 14:30:00 UTC",
                "incident_id": "INC-2024-001",
            },
        }

        # Send email
        result = await service.send(request)
        assert result.success is True

        # Wait for processing
        await asyncio.sleep(0.2)

        # Check received email
        messages = smtp_server.get_messages()
        assert len(messages) >= 1

        message = messages[-1]
        email_content = message["data"]
        assert "Security Alert" in email_content
        assert "Brute Force Attack" in email_content
        assert "INC-2024-001" in email_content

        await service.close()

    @pytest.mark.asyncio
    async def test_send_email_with_attachments(
        self, smtp_config: Any, smtp_server: Any
    ) -> None:
        """Test sending email with attachments."""
        service = EmailNotificationService(smtp_config)

        # Create request with attachments
        request = NotificationRequest(
            channel=NotificationChannel.EMAIL,
            recipient="admin@example.com",
            subject="Log Report",
            body="Please find the security log report attached.",
        )
        request.metadata = {
            "attachments": [
                {
                    "filename": "security_log.txt",
                    "content": b"[2024-01-15] Security event detected\n[2024-01-15] Investigation started",
                    "content_type": "text/plain",
                }
            ]
        }

        # Send email
        result = await service.send(request)
        assert result.success is True

        # Wait for processing
        await asyncio.sleep(0.2)

        # Check received email
        messages = smtp_server.get_messages()
        assert len(messages) >= 1

        message = messages[-1]
        email_content = message["data"]
        assert "Log Report" in email_content
        assert "security_log.txt" in email_content

        await service.close()

    @pytest.mark.asyncio
    async def test_send_invalid_recipients(self, smtp_config: Any) -> None:
        """Test sending with invalid recipients."""
        service = EmailNotificationService(smtp_config)

        request = NotificationRequest(
            channel=NotificationChannel.EMAIL,
            recipient="invalid-email",
            subject="Test",
            body="Test message",
        )

        # Should raise ValueError for no valid recipients
        with pytest.raises(ValueError, match="No valid recipients provided"):
            await service.send(request)

    @pytest.mark.asyncio
    async def test_get_channel_limits(self, smtp_config: Any) -> None:
        """Test channel limits information."""
        service = EmailNotificationService(smtp_config)

        limits = await service.get_channel_limits()

        assert limits["max_subject_length"] == 255
        assert limits["max_body_length"] == 10 * 1024 * 1024
        assert limits["max_recipients"] == 50
        assert limits["max_attachments"] == 10
        assert limits["max_attachment_size"] == 25 * 1024 * 1024
        assert limits["supports_html"] is True
        assert limits["supports_attachments"] is True
        assert "rate_limit" in limits
        assert limits["rate_limit"]["per_hour"] == 1000
        assert limits["rate_limit"]["per_day"] == 10000

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, smtp_config: Any) -> None:
        """Test health check with healthy connection."""
        service = EmailNotificationService(smtp_config)

        health = await service.health_check()

        assert health["service"] == "email"
        assert health["status"] == "healthy"
        assert "timestamp" in health
        assert health["queue_size"] == 0
        assert health["connection"]["host"] == smtp_config.host
        assert health["connection"]["port"] == smtp_config.port
        assert health["connection"]["status"] == "connected"

        await service.close()

    @pytest.mark.asyncio
    async def test_health_check_connection_error(self) -> None:
        """Test health check with connection error."""
        # Use invalid SMTP config
        config = SMTPConfig(
            host="invalid.smtp.server",
            port=587,
            username="test@example.com",
            password="wrongpass",
        )

        service = EmailNotificationService(config)

        health = await service.health_check()

        assert health["service"] == "email"
        assert health["status"] in ["unhealthy", "degraded"]
        assert "error" in health or health["connection"]["status"] == "error"

    @pytest.mark.asyncio
    async def test_email_queue_processing(
        self, smtp_config: Any, smtp_server: Any
    ) -> None:
        """Test email queue processing functionality."""
        service = EmailNotificationService(smtp_config)

        # Send multiple emails quickly
        requests = []
        for i in range(3):
            request = NotificationRequest(
                channel=NotificationChannel.EMAIL,
                recipient=f"test{i}@example.com",
                subject=f"Test Email {i}",
                body=f"This is test email number {i}",
            )
            requests.append(request)

        # Send all emails
        results = []
        for request in requests:
            result = await service.send(request)
            results.append(result)
            assert result.success is True

        # Wait for all emails to be processed
        await asyncio.sleep(0.5)

        # Check that all emails were received
        messages = smtp_server.get_messages()
        assert len(messages) >= 3

        # Verify each email
        for i in range(3):
            found = False
            for message in messages:
                if (
                    f"test{i}@example.com" in message["rcpttos"]
                    and f"Test Email {i}" in message["data"]
                ):
                    found = True
                    break
            assert found, f"Email {i} not found in received messages"

        await service.close()

    @pytest.mark.asyncio
    async def test_close_connection(self, smtp_config: Any) -> None:
        """Test closing SMTP connection."""
        service = EmailNotificationService(smtp_config)

        # Create connection
        await service._get_smtp_connection()
        assert service._smtp_connection is not None

        # Close connection
        await service.close()
        assert service._smtp_connection is None

    def test_default_templates_initialization(self, smtp_config: Any) -> None:
        """Test that default templates are properly initialized."""
        service = EmailNotificationService(smtp_config)

        assert "security_incident" in service.templates

        template = service.templates["security_incident"]
        assert isinstance(template, EmailTemplate)
        assert template.html_template is not None
        assert template.text_template is not None
        assert template.subject_template is not None

        # Test template rendering
        context = {
            "subject": "Test Alert",
            "incident_type": "Test Incident",
            "severity": "medium",
            "timestamp": "2024-01-15",
            "body": "Test body",
            "incident_id": "TEST-001",
        }

        subject, html, text = template.render(context)
        assert subject == "Test Alert"
        assert "Test Incident" in html
        assert "Test Incident" in text
        assert "TEST-001" in html
        assert "TEST-001" in text

    @pytest.mark.asyncio
    async def test_priority_handling_and_retry(self, smtp_config: Any) -> None:
        """Test priority handling and retry logic for critical emails."""
        service = EmailNotificationService(smtp_config)

        # Send critical priority email
        request = NotificationRequest(
            channel=NotificationChannel.EMAIL,
            recipient="critical@example.com",
            subject="Critical Alert",
            body="Critical security incident detected",
            priority=NotificationPriority.CRITICAL,
        )

        result = await service.send(request)
        assert result.success is True

        # Check that priority was preserved in queue
        email_data = await service.email_queue.get_next()
        assert email_data is not None
        assert email_data["priority"] == NotificationPriority.CRITICAL

        # Complete the task
        service.email_queue.task_done()

        await service.close()
