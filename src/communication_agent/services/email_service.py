"""
Email notification service for the Communication Agent.

Handles email notifications with SMTP configuration, template support,
HTML/plain text formatting, attachments, and queuing.
"""

import asyncio
import mimetypes
import re
import smtplib
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from typing import Any, Dict, List, Optional, Tuple

from src.communication_agent.interfaces import (
    NotificationService,
    NotificationRequest,
    NotificationResult,
)
from src.communication_agent.types import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SMTPConfig:
    """SMTP server configuration."""

    host: str
    port: int
    username: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False
    timeout: int = 30
    from_name: str = "SentinelOps"
    from_address: str = "notifications@sentinelops.com"


@dataclass
class EmailAttachment:
    """Email attachment configuration."""

    filename: str
    content: bytes
    content_type: Optional[str] = None


class EmailTemplate:
    """Email template with HTML and plain text support."""

    def __init__(
        self,
        html_template: str,
        text_template: str,
        subject_template: str,
    ):
        """Initialize email template."""
        self.html_template = html_template
        self.text_template = text_template
        self.subject_template = subject_template

    def render(self, context: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        Render the email template with context.

        Returns:
            Tuple of (subject, html_body, text_body)
        """
        subject = self.subject_template.format(**context)
        html_body = self.html_template.format(**context)
        text_body = self.text_template.format(**context)

        return subject, html_body, text_body


class EmailQueue:
    """Email queue for managing email delivery."""

    def __init__(self, max_size: int = 1000):
        """Initialize email queue."""
        self.queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=max_size)
        self.processing = False
        self._processor_task: Optional[asyncio.Task[Any]] = None

    async def enqueue(
        self,
        recipients: List[str],
        subject: str,
        html_body: str,
        text_body: str,
        attachments: Optional[List[EmailAttachment]] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an email to the queue."""
        email_data = {
            "recipients": recipients,
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body,
            "attachments": attachments or [],
            "priority": priority,
            "metadata": metadata or {},
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }

        await self.queue.put(email_data)
        logger.debug(
            "Email queued for %d recipients",
            len(recipients),
            extra={
                "subject": subject,
                "priority": priority.value,
                "queue_size": self.queue.qsize(),
            },
        )

    async def get_next(self) -> Optional[Dict[str, Any]]:
        """Get the next email from the queue."""
        try:
            return await self.queue.get()
        except asyncio.QueueEmpty:
            return None

    def task_done(self) -> None:
        """Mark the current task as done."""
        self.queue.task_done()


class EmailNotificationService(NotificationService):
    """
    Email notification service implementation.

    Supports SMTP configuration, HTML/plain text emails, attachments,
    and email queuing.
    """

    def __init__(
        self,
        smtp_config: SMTPConfig,
        templates: Optional[Dict[str, EmailTemplate]] = None,
    ):
        """Initialize email notification service."""
        self.smtp_config = smtp_config
        self.templates = templates or {}
        self.email_queue = EmailQueue()
        self._smtp_connection: Optional[smtplib.SMTP] = None
        self._connection_lock = asyncio.Lock()

        # Default templates
        self._init_default_templates()

        logger.info(
            "Email notification service initialized",
            extra={
                "smtp_host": smtp_config.host,
                "smtp_port": smtp_config.port,
                "from_address": smtp_config.from_address,
            },
        )

    def _init_default_templates(self) -> None:
        """Initialize default email templates."""
        # Security incident template
        self.templates["security_incident"] = EmailTemplate(
            html_template="""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f8f9fa; padding: 20px; margin-top: 20px; }}
        .alert {{ background-color: #fff3cd; border: 1px solid #ffeeba;
                  padding: 15px; margin: 10px 0; }}
        .details {{ background-color: white; padding: 15px; margin: 10px 0; }}
        .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 Security Alert</h1>
        </div>
        <div class="content">
            <h2>{subject}</h2>
            <div class="alert">
                <strong>Incident Type:</strong> {incident_type}<br>
                <strong>Severity:</strong> {severity}<br>
                <strong>Time:</strong> {timestamp}
            </div>
            <div class="details">
                {body}
            </div>
        </div>
        <div class="footer">
            <p>This is an automated notification from SentinelOps</p>
            <p>Incident ID: {incident_id}</p>
        </div>
    </div>
</body>
</html>
            """.strip(),
            text_template="""
SECURITY ALERT

{subject}

Incident Type: {incident_type}
Severity: {severity}
Time: {timestamp}

{body}

---
This is an automated notification from SentinelOps
Incident ID: {incident_id}
            """.strip(),
            subject_template="{subject}",
        )

    def get_channel_type(self) -> NotificationChannel:
        """Get the channel type this service implements."""
        return NotificationChannel.EMAIL

    async def validate_recipient(self, recipient: str) -> bool:
        """Validate an email address."""
        # Basic email validation regex
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

        is_valid = bool(email_pattern.match(recipient))

        if not is_valid:
            logger.warning(
                "Invalid email address: %s",
                recipient,
                extra={"recipient": recipient},
            )

        return is_valid

    async def _get_smtp_connection(self) -> smtplib.SMTP:
        """Get or create SMTP connection."""
        async with self._connection_lock:
            if self._smtp_connection is None:
                await self._create_smtp_connection()

            # Test if connection is still alive
            try:
                if self._smtp_connection is not None:
                    status = await asyncio.to_thread(self._smtp_connection.noop)
                    if status[0] != 250:
                        await self._create_smtp_connection()
                else:
                    await self._create_smtp_connection()
            except (ValueError, OSError, RuntimeError):
                await self._create_smtp_connection()

            if self._smtp_connection is None:
                raise RuntimeError("Failed to establish SMTP connection")

            return self._smtp_connection

    async def _create_smtp_connection(self) -> None:
        """Create a new SMTP connection."""
        try:
            if self.smtp_config.use_ssl:
                context = ssl.create_default_context()
                self._smtp_connection = await asyncio.to_thread(
                    smtplib.SMTP_SSL,
                    self.smtp_config.host,
                    self.smtp_config.port,
                    context=context,
                    timeout=self.smtp_config.timeout,
                )
            else:
                self._smtp_connection = await asyncio.to_thread(
                    smtplib.SMTP,
                    self.smtp_config.host,
                    self.smtp_config.port,
                    timeout=self.smtp_config.timeout,
                )

                if self.smtp_config.use_tls:
                    await asyncio.to_thread(self._smtp_connection.starttls)

            # Authenticate
            await asyncio.to_thread(
                self._smtp_connection.login,
                self.smtp_config.username,
                self.smtp_config.password,
            )

            logger.info(
                "SMTP connection established",
                extra={
                    "host": self.smtp_config.host,
                    "port": self.smtp_config.port,
                },
            )

        except Exception as e:
            logger.error(
                "Failed to create SMTP connection: %s",
                e,
                extra={
                    "host": self.smtp_config.host,
                    "port": self.smtp_config.port,
                },
                exc_info=True,
            )
            raise

    def _build_email(
        self,
        recipients: List[str],
        subject: str,
        html_body: str,
        text_body: str,
        attachments: Optional[List[EmailAttachment]] = None,
    ) -> MIMEMultipart:
        """Build a MIME multipart email message."""
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = formataddr(
            (
                self.smtp_config.from_name,
                self.smtp_config.from_address,
            )
        )
        msg["To"] = ", ".join(recipients)
        msg["Date"] = formataddr(("", ""))

        # Create the body part
        msg_body = MIMEMultipart("alternative")

        # Add plain text part
        text_part = MIMEText(text_body, "plain", "utf-8")
        msg_body.attach(text_part)

        # Add HTML part
        html_part = MIMEText(html_body, "html", "utf-8")
        msg_body.attach(html_part)

        msg.attach(msg_body)

        # Add attachments
        if attachments:
            for attachment in attachments:
                self._add_attachment(msg, attachment)

        return msg

    def _add_attachment(
        self,
        msg: MIMEMultipart,
        attachment: EmailAttachment,
    ) -> None:
        """Add an attachment to the email message."""
        # Determine content type
        content_type = attachment.content_type
        if not content_type:
            content_type, _ = mimetypes.guess_type(attachment.filename)
            if not content_type:
                content_type = "application/octet-stream"

        # Create attachment
        maintype, subtype = content_type.split("/", 1)
        attachment_part = MIMEBase(maintype, subtype)
        attachment_part.set_payload(attachment.content)
        attachment_part.add_header(
            "Content-Disposition",
            f"attachment; filename={attachment.filename}",
        )
        attachment_part.add_header(
            "Content-Transfer-Encoding",
            "base64",
        )

        # Encode the payload
        from email.encoders import encode_base64

        encode_base64(attachment_part)

        msg.attach(attachment_part)

    async def send(self, request: NotificationRequest) -> NotificationResult:
        """
        Send an email notification.

        This method queues the email for delivery and returns immediately.
        """
        # Extract data from request
        recipients = request.recipients if hasattr(request, 'recipients') else []
        subject = request.subject if hasattr(request, 'subject') else ""
        message = request.message if hasattr(request, 'message') else ""
        priority = request.priority if hasattr(request, 'priority') else NotificationPriority.MEDIUM
        metadata = request.metadata if hasattr(request, 'metadata') else None

        # Validate recipients
        valid_recipients = []
        for recipient in recipients:
            if await self.validate_recipient(recipient):
                valid_recipients.append(recipient)

        if not valid_recipients:
            raise ValueError("No valid recipients provided")

        # Determine if we should use a template
        template_name = metadata.get("template") if metadata else None

        if template_name and template_name in self.templates:
            # Use template
            template = self.templates[template_name]
            context = metadata.get("context", {}) if metadata else {}
            context["body"] = message
            subject, html_body, text_body = template.render(context)
        else:
            # Use plain message
            html_body = f"<html><body><pre>{message}</pre></body></html>"
            text_body = message

        # Extract attachments from metadata
        attachments = []
        if metadata and "attachments" in metadata:
            for att_data in metadata["attachments"]:
                attachments.append(
                    EmailAttachment(
                        filename=att_data["filename"],
                        content=att_data["content"],
                        content_type=att_data.get("content_type"),
                    )
                )

        # Queue the email
        await self.email_queue.enqueue(
            recipients=valid_recipients,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            attachments=attachments,
            priority=priority,
            metadata=metadata,
        )

        # Start queue processor if not running
        if not self.email_queue.processing:
            asyncio.create_task(self._process_email_queue())

        return NotificationResult(
            success=True,
            status=NotificationStatus.QUEUED,
            message_id=f"email-batch-{datetime.now(timezone.utc).isoformat()}",
            metadata={
                "recipients": valid_recipients,
                "queued_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def _process_email_queue(self) -> None:
        """Process emails from the queue."""
        if self.email_queue.processing:
            return

        self.email_queue.processing = True
        logger.info("Starting email queue processor")

        try:
            while True:
                email_data = await self.email_queue.get_next()
                if email_data is None:
                    await asyncio.sleep(1)
                    continue

                try:
                    await self._send_email(email_data)
                    self.email_queue.task_done()
                except (ValueError, RuntimeError, OSError) as e:
                    logger.error(
                        "Failed to send email: %s", e,
                        extra={
                            "subject": email_data.get("subject"),
                            "recipients": email_data.get("recipients"),
                        },
                        exc_info=True,
                    )
                    self.email_queue.task_done()

                    # Implement retry logic for high priority emails
                    if (
                        email_data.get("priority") == NotificationPriority.CRITICAL
                        and email_data.get("retry_count", 0) < 3
                    ):
                        email_data["retry_count"] = email_data.get("retry_count", 0) + 1
                        await self.email_queue.enqueue(**email_data)

        except asyncio.CancelledError:
            logger.info("Email queue processor cancelled")
            raise
        finally:
            self.email_queue.processing = False

    async def _send_email(self, email_data: Dict[str, Any]) -> None:
        """Send a single email."""
        recipients = email_data["recipients"]
        subject = email_data["subject"]
        html_body = email_data["html_body"]
        text_body = email_data["text_body"]
        attachments = email_data.get("attachments", [])

        # Build the email message
        msg = self._build_email(
            recipients=recipients,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            attachments=attachments,
        )

        # Get SMTP connection
        smtp = await self._get_smtp_connection()

        # Send the email
        start_time = datetime.now(timezone.utc)
        await asyncio.to_thread(
            smtp.sendmail,
            self.smtp_config.from_address,
            recipients,
            msg.as_string(),
        )

        delivery_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        logger.info(
            "Email sent successfully",
            extra={
                "recipients": recipients,
                "subject": subject,
                "delivery_time": delivery_time,
                "priority": email_data.get("priority"),
            },
        )

    async def close(self) -> None:
        """Close the SMTP connection."""
        async with self._connection_lock:
            if self._smtp_connection:
                try:
                    await asyncio.to_thread(self._smtp_connection.quit)
                except (ValueError, OSError) as e:
                    logger.warning("Error closing SMTP connection: %s", e)
                finally:
                    self._smtp_connection = None

    async def get_channel_limits(self) -> Dict[str, Any]:
        """
        Get email channel limits and capabilities.

        Returns:
            Dictionary of limits
        """
        return {
            "max_subject_length": 255,
            "max_body_length": 10 * 1024 * 1024,  # 10MB
            "max_recipients": 50,
            "max_attachments": 10,
            "max_attachment_size": 25 * 1024 * 1024,  # 25MB
            "supports_html": True,
            "supports_attachments": True,
            "rate_limit": {
                "per_hour": 1000,
                "per_day": 10000,
            },
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check email service health.

        Returns:
            Health status information
        """
        health_status = {
            "service": "email",
            "status": "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "queue_size": self.email_queue.queue.qsize(),
            "connection": {
                "host": self.smtp_config.host,
                "port": self.smtp_config.port,
                "ssl": self.smtp_config.use_ssl,
                "tls": self.smtp_config.use_tls,
            },
        }

        try:
            # Test SMTP connection
            await self._get_smtp_connection()
            if self._smtp_connection:
                health_status["status"] = "healthy"
                connection_dict = health_status["connection"]
                if isinstance(connection_dict, dict):
                    connection_dict["status"] = "connected"
            else:
                health_status["status"] = "degraded"
                connection_dict = health_status["connection"]
                if isinstance(connection_dict, dict):
                    connection_dict["status"] = "disconnected"
        except (ValueError, RuntimeError, OSError) as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            connection_dict = health_status["connection"]
            if isinstance(connection_dict, dict):
                connection_dict["status"] = "error"

        return health_status
