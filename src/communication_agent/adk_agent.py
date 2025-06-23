"""
Communication Agent using Google ADK - PRODUCTION IMPLEMENTATION

This agent handles multi-channel notifications for security incidents.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.run_config import RunConfig
from google.adk.tools import BaseTool, ToolContext
from jinja2 import Template

from src.common.adk_agent_base import SentinelOpsBaseAgent
from src.tools.transfer_tools import TransferToOrchestratorAgentTool

logger = logging.getLogger(__name__)


class SlackNotificationTool(BaseTool):
    """Production tool for sending Slack notifications."""

    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize with Slack webhook URL."""
        super().__init__(
            name="slack_notification_tool",
            description="Send notifications to Slack channels",
        )
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")

    async def execute(self, _context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Send notification to Slack."""
        message = kwargs.get("message", "")
        channel = kwargs.get("channel", "#security-alerts")
        priority = kwargs.get("priority", "medium")
        attachments = kwargs.get("attachments", [])

        try:
            if not self.webhook_url:
                logger.warning("Slack webhook URL not configured")
                return {"status": "skipped", "reason": "Slack webhook not configured"}

            # Build Slack message
            slack_message = {
                "channel": channel,
                "username": "SentinelOps Security Bot",
                "icon_emoji": ":shield:",
                "text": message,
                "attachments": [],
            }

            # Add color based on priority
            color_map = {
                "critical": "#ff0000",
                "high": "#ff9900",
                "medium": "#ffcc00",
                "low": "#00cc00",
            }

            # Format attachments
            for attachment in attachments:
                slack_attachment: Dict[str, Any] = {
                    "color": color_map.get(priority, "#0099ff"),
                    "fields": [],
                    "footer": "SentinelOps",
                    "ts": int(datetime.utcnow().timestamp()),
                }

                # Add fields
                for key, value in attachment.items():
                    slack_attachment["fields"].append(
                        {
                            "title": key.replace("_", " ").title(),
                            "value": str(value),
                            "short": len(str(value)) < 40,
                        }
                    )

                slack_message["attachments"].append(slack_attachment)

            # Send to Slack (in production, use actual Slack SDK)
            import requests

            response = requests.post(self.webhook_url, json=slack_message, timeout=10)

            if response.status_code == 200:
                return {"status": "success", "channel": channel, "message_sent": True}
            else:
                return {
                    "status": "error",
                    "error": f"Slack API returned {response.status_code}",
                }

        except (ValueError, RuntimeError, KeyError) as e:
            logger.error("Error sending Slack notification: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}


class EmailNotificationTool(BaseTool):
    """Production tool for sending email notifications."""

    def __init__(self, smtp_config: Dict[str, Any]):
        """Initialize with SMTP configuration."""
        super().__init__(
            name="email_notification_tool",
            description="Send email notifications for security incidents",
        )
        self.smtp_config = smtp_config

    async def execute(self, _context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Send email notification."""
        recipients = kwargs.get("recipients", [])
        subject = kwargs.get("subject", "Security Alert")
        body = kwargs.get("body", "")
        priority = kwargs.get("priority", "medium")

        try:
            if not recipients:
                return {"status": "error", "error": "No recipients specified"}

            # Use environment variables if SMTP not configured
            if not self.smtp_config.get("host"):
                self.smtp_config = {
                    "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
                    "port": int(os.environ.get("SMTP_PORT", "587")),
                    "username": os.environ.get("SMTP_USERNAME"),
                    "password": os.environ.get("SMTP_PASSWORD"),
                    "use_tls": True,
                }

            if not self.smtp_config.get("username"):
                logger.warning("SMTP not configured")
                return {"status": "skipped", "reason": "SMTP not configured"}

            # Send email
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg["From"] = self.smtp_config.get("username", "")
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = f"[{priority.upper()}] {subject}"

            # Add priority header
            if priority in ["critical", "high"]:
                msg["X-Priority"] = "1"

            msg.attach(MIMEText(body, "html"))

            # Send via SMTP
            with smtplib.SMTP(
                self.smtp_config["host"], self.smtp_config["port"]
            ) as server:
                if self.smtp_config.get("use_tls"):
                    server.starttls()
                server.login(self.smtp_config["username"], self.smtp_config["password"])
                server.send_message(msg)

            return {"status": "success", "recipients": recipients, "subject": subject}

        except (ValueError, RuntimeError, KeyError) as e:
            logger.error("Error sending email: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}


class SMSNotificationTool(BaseTool):
    """Production tool for sending SMS notifications."""

    def __init__(self, twilio_config: Dict[str, Any]):
        """Initialize with Twilio configuration."""
        super().__init__(
            name="sms_notification_tool",
            description="Send SMS alerts for critical incidents",
        )
        self.twilio_config = twilio_config

    async def execute(self, _context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Send SMS notification."""
        phone_numbers = kwargs.get("phone_numbers", [])
        message = kwargs.get("message", "")

        try:
            if not phone_numbers:
                return {"status": "error", "error": "No phone numbers specified"}

            # Use environment variables if not configured
            if not self.twilio_config.get("account_sid"):
                self.twilio_config = {
                    "account_sid": os.environ.get("TWILIO_ACCOUNT_SID"),
                    "auth_token": os.environ.get("TWILIO_AUTH_TOKEN"),
                    "from_number": os.environ.get("TWILIO_FROM_NUMBER"),
                }

            if not self.twilio_config.get("account_sid"):
                logger.warning("Twilio not configured")
                return {"status": "skipped", "reason": "Twilio not configured"}

            # Send SMS (in production, use Twilio SDK)
            from twilio.rest import Client

            client = Client(
                self.twilio_config["account_sid"], self.twilio_config["auth_token"]
            )

            sent_to = []
            errors = []

            for phone in phone_numbers:
                try:
                    client.messages.create(
                        body=message[:160],  # SMS limit
                        from_=self.twilio_config["from_number"],
                        to=phone,
                    )
                    sent_to.append(phone)
                except (ValueError, RuntimeError, KeyError) as e:
                    errors.append(f"Failed to send to {phone}: {str(e)}")

            return {
                "status": "success" if sent_to else "error",
                "sent_to": sent_to,
                "errors": errors,
            }

        except (ValueError, RuntimeError, KeyError) as e:
            logger.error("Error sending SMS: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}


class MessageFormatterTool(BaseTool):
    """Tool for formatting messages using templates."""

    def __init__(self, template_dir: str = "templates"):
        """Initialize with template directory."""
        super().__init__(
            name="message_formatter_tool",
            description="Format messages using Jinja2 templates",
        )
        self.template_dir = template_dir
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load message templates."""
        # Default templates
        return {
            "incident_alert": """
                <h2>🚨 Security Incident Alert</h2>
                <p><strong>Incident ID:</strong> {{ incident_id }}</p>
                <p><strong>Severity:</strong> {{ severity | upper }}</p>
                <p><strong>Type:</strong> {{ incident_type }}</p>
                <p><strong>Time:</strong> {{ timestamp }}</p>

                <h3>Details:</h3>
                <p>{{ description }}</p>

                {% if affected_resources %}
                <h3>Affected Resources:</h3>
                <ul>
                {% for resource in affected_resources %}
                    <li>{{ resource }}</li>
                {% endfor %}
                </ul>
                {% endif %}

                {% if actions_taken %}
                <h3>Actions Taken:</h3>
                <ul>
                {% for action in actions_taken %}
                    <li>{{ action.action }} - {{ action.status }}</li>
                {% endfor %}
                </ul>
                {% endif %}
            """,
            "remediation_summary": """
                <h2>✅ Remediation Complete</h2>
                <p><strong>Incident ID:</strong> {{ incident_id }}</p>
                <p><strong>Duration:</strong> {{ duration_seconds }}s</p>

                <h3>Actions Executed:</h3>
                <ul>
                {% for action in actions_executed %}
                    <li>{{ action.action }} (Risk: {{ action.risk_level }})</li>
                {% endfor %}
                </ul>

                {% if actions_skipped %}
                <h3>Actions Skipped:</h3>
                <ul>
                {% for action in actions_skipped %}
                    <li>{{ action.action }} - Reason: {{ action.reason }}</li>
                {% endfor %}
                </ul>
                {% endif %}
            """,
            "approval_request": """
                <h2>🔐 Approval Required</h2>
                <p><strong>Incident ID:</strong> {{ incident_id }}</p>
                <p><strong>Risk Level:</strong> {{ risk_level | upper }}</p>

                <h3>Proposed Action:</h3>
                <p>{{ action }}</p>

                <h3>Justification:</h3>
                <p>{{ justification }}</p>

                <p><strong>Please approve or deny this action.</strong></p>
            """,
        }

    async def execute(self, _context: ToolContext, **kwargs: Any) -> Dict[str, Any]:
        """Format a message using a template."""
        template_name = kwargs.get("template", "incident_alert")
        data = kwargs.get("data", {})

        try:
            template_str = self.templates.get(template_name)
            if not template_str:
                return {
                    "status": "error",
                    "error": f"Template '{template_name}' not found",
                }

            template = Template(template_str)
            formatted_message = template.render(**data)

            # Also create plain text version
            plain_text = formatted_message
            # Remove HTML tags for plain text
            import re

            plain_text = re.sub("<[^<]+?>", "", plain_text)
            plain_text = re.sub(r"\s+", " ", plain_text).strip()

            return {
                "status": "success",
                "html": formatted_message,
                "plain_text": plain_text,
            }

        except (ValueError, AttributeError, KeyError) as e:
            logger.error("Error formatting message: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}


class CommunicationAgent(SentinelOpsBaseAgent):
    """Production ADK Communication Agent for multi-channel notifications."""

    # Define instance attributes
    default_channels: List[str]
    critical_channels: List[str]
    recipient_mapping: Dict[str, List[str]]
    sent_notifications: Set[str]

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Communication Agent with production configuration."""
        # Extract configuration
        # Note: project_id is available via inherited property, no need to set it

        # Channel configurations
        slack_config = config.get("slack", {})
        email_config = config.get("email", {})
        sms_config = config.get("sms", {})

        # Notification settings - use object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, "default_channels", config.get("default_channels", ["slack", "email"]))
        object.__setattr__(self, "critical_channels", config.get(
            "critical_channels", ["slack", "email", "sms"]
        ))
        object.__setattr__(self, "recipient_mapping", config.get(
            "recipient_mapping",
            {"email": ["security-team@company.com"], "sms": ["+1234567890"]},
        ))

        # Initialize production tools
        tools = [
            SlackNotificationTool(slack_config.get("webhook_url")),
            EmailNotificationTool(email_config),
            SMSNotificationTool(sms_config),
            MessageFormatterTool(),
            TransferToOrchestratorAgentTool(),
        ]

        # Initialize base agent
        super().__init__(
            name="communication_agent",
            description="Production multi-channel security notification agent",
            config=config,
            model="gemini-pro",
            tools=tools,
        )

        # Track sent notifications to prevent duplicates - use object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, "sent_notifications", set())

    async def run(
        self,
        context: Optional[Any] = None,
        config: Optional[RunConfig] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute the production communication workflow."""
        try:
            # Handle incoming transfer
            notification_request = None
            if context and hasattr(context, "data") and context.data:
                transfer_data = context.data
                notification_request = transfer_data
            elif kwargs.get("notification_request"):
                notification_request = kwargs["notification_request"]

            if not notification_request:
                return {"status": "error", "error": "No notification request provided"}

            # Send notifications
            return await self._send_notifications(notification_request, context, config)

        except (ValueError, RuntimeError, KeyError) as e:
            logger.error("Error in communication agent: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}

    async def _send_notifications(
        self, request: Dict[str, Any], context: Any, _config: Optional[RunConfig]
    ) -> Dict[str, Any]:
        """Send notifications through configured channels."""
        notification_results = self._init_notification_results(request)

        try:
            # Create ToolContext with proper invocation context
            if context and isinstance(context, InvocationContext):
                tool_context = ToolContext(invocation_context=context)
            else:
                # Create a minimal InvocationContext if none provided
                invocation_ctx = InvocationContext(
                    session_service=None,  # type: ignore
                    invocation_id="default",
                    agent=self,
                    session=None  # type: ignore
                )
                tool_context = ToolContext(invocation_context=invocation_ctx)

            # Determine notification settings
            workflow_stage = request.get("workflow_stage", "")
            priority = request.get("results", {}).get("priority", "medium")
            channels = self._get_notification_channels(request, priority)

            # Format the message
            format_result = await self._format_notification_message(
                tool_context, request, workflow_stage
            )

            if format_result.get("status") != "success":
                notification_results["errors"].append(
                    f"Failed to format message: {format_result.get('error')}"
                )
                return notification_results

            # Check for duplicate notifications
            if self._is_duplicate_notification(request, workflow_stage):
                return self._create_duplicate_response(notification_results)

            # Send notifications
            results = await self._send_to_channels(
                channels, tool_context, format_result, request, priority
            )

            # Process results
            self._process_notification_results(results, notification_results)

            # Mark as sent and report back
            await self._finalize_notification(
                tool_context, request, workflow_stage, notification_results
            )

            return notification_results

        except (ValueError, RuntimeError, KeyError, OSError) as e:
            logger.error("Error sending notifications: %s", e, exc_info=True)
            notification_results["status"] = "error"
            notification_results["error"] = str(e)
            return notification_results

    def _init_notification_results(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize notification results structure."""
        return {
            "status": "success",
            "incident_id": request.get("incident_id"),
            "notification_id": f"notif_{datetime.utcnow().timestamp()}",
            "timestamp": datetime.utcnow().isoformat(),
            "channels_notified": [],
            "errors": [],
        }

    def _get_notification_channels(
        self, request: Dict[str, Any], priority: str
    ) -> List[str]:
        """Determine which channels to use for notification."""
        channels = request.get("results", {}).get("channels", self.default_channels)
        if priority == "critical":
            channels = self.critical_channels
        # Ensure we always return a list of strings
        return list(channels) if isinstance(channels, list) else []

    async def _format_notification_message(
        self, tool_context: ToolContext, request: Dict[str, Any], workflow_stage: str
    ) -> Dict[str, Any]:
        """Format the notification message using templates."""
        formatter_tool = self.tools[3]  # MessageFormatterTool
        template_data = self._prepare_template_data(request)
        template_name = self._get_template_name(workflow_stage)

        # Check if the tool has execute method
        if hasattr(formatter_tool, 'execute') and callable(formatter_tool.execute):
            result = await formatter_tool.execute(
                tool_context, template=template_name, data=template_data
            )
        else:
            # Fallback if tool doesn't have execute method
            result = {"status": "error", "error": "Invalid formatter tool"}
        return result if isinstance(result, dict) else {"status": "error", "error": "Invalid formatter result"}

    def _is_duplicate_notification(
        self, request: Dict[str, Any], workflow_stage: str
    ) -> bool:
        """Check if this notification has already been sent."""
        notification_key = f"{request.get('incident_id')}_{workflow_stage}"
        return notification_key in self.sent_notifications

    def _create_duplicate_response(
        self, notification_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create response for duplicate notification."""
        notification_results["status"] = "skipped"
        notification_results["reason"] = "Duplicate notification"
        return notification_results

    async def _send_to_channels(
        self,
        channels: List[str],
        tool_context: ToolContext,
        format_result: Dict[str, Any],
        request: Dict[str, Any],
        priority: str,
    ) -> List[Any]:
        """Send notifications to all specified channels."""
        tasks = []
        formatted_message = format_result.get("html", "")
        plain_message = format_result.get("plain_text", "")
        template_data = self._prepare_template_data(request)

        if "slack" in channels:
            slack_tool = self.tools[0]  # SlackNotificationTool
            if isinstance(slack_tool, SlackNotificationTool):
                tasks.append(
                    self._send_slack_notification(
                        slack_tool, tool_context, plain_message, template_data, priority
                    )
                )

        if "email" in channels:
            email_tool = self.tools[1]  # EmailNotificationTool
            if isinstance(email_tool, EmailNotificationTool):
                tasks.append(
                    self._send_email_notification(
                        email_tool, tool_context, formatted_message, template_data, priority
                    )
                )

        if "sms" in channels and priority in ["critical", "high"]:
            sms_tool = self.tools[2]  # SMSNotificationTool
            if isinstance(sms_tool, SMSNotificationTool):
                tasks.append(
                    self._send_sms_notification(
                        sms_tool, tool_context, plain_message, template_data
                    )
                )

        results: List[Any] = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    def _process_notification_results(
        self, results: List[Any], notification_results: Dict[str, Any]
    ) -> None:
        """Process results from all notification channels."""
        for result in results:
            if isinstance(result, Exception):
                notification_results["errors"].append(str(result))
            elif isinstance(result, dict):
                if result.get("status") == "success":
                    notification_results["channels_notified"].append(
                        result.get("channel", "unknown")
                    )
                else:
                    notification_results["errors"].append(
                        result.get("error", "Unknown error")
                    )

    async def _finalize_notification(
        self,
        tool_context: ToolContext,
        request: Dict[str, Any],
        workflow_stage: str,
        notification_results: Dict[str, Any],
    ) -> None:
        """Finalize notification by marking as sent and reporting back."""
        # Mark as sent
        notification_key = f"{request.get('incident_id')}_{workflow_stage}"
        self.sent_notifications.add(notification_key)

        # Report back to orchestrator
        orchestrator_tool = self.tools[4]  # TransferToOrchestratorAgentTool
        if hasattr(orchestrator_tool, 'execute'):
            await orchestrator_tool.execute(
                tool_context,
                incident_id=request.get("incident_id"),
                workflow_stage="communication_complete",
                results=notification_results,
            )

    def _prepare_template_data(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for message templates."""
        results = request.get("results", {})
        incident_id = request.get("incident_id", "unknown")

        # Base data
        data = {
            "incident_id": incident_id,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "severity": "medium",
            "description": "Security incident detected",
        }

        # Add stage-specific data
        workflow_stage = request.get("workflow_stage", "")

        if workflow_stage == "critical_alert":
            analysis = results.get("analysis", {})
            threat_assessment = analysis.get("threat_assessment", {})
            data.update(
                {
                    "severity": threat_assessment.get("threat_level", "high"),
                    "incident_type": threat_assessment.get("threat_type", "Unknown"),
                    "description": threat_assessment.get(
                        "attack_pattern", "Security anomaly detected"
                    ),
                    "affected_resources": analysis.get("impact_analysis", {}).get(
                        "affected_resources", []
                    ),
                }
            )

        elif workflow_stage == "remediation_summary":
            remediation = results.get("remediation_results", {})
            data.update(
                {
                    "duration_seconds": remediation.get("duration_seconds", 0),
                    "actions_executed": remediation.get("actions_executed", []),
                    "actions_skipped": remediation.get("actions_skipped", []),
                }
            )

        elif workflow_stage == "approval_request":
            data.update(
                {
                    "action": results.get("action", "Unknown action"),
                    "risk_level": results.get("risk_level", "medium"),
                    "justification": results.get("metadata", {}).get(
                        "description", "Security remediation required"
                    ),
                }
            )

        return data

    def _get_template_name(self, workflow_stage: str) -> str:
        """Get appropriate template based on workflow stage."""
        template_mapping = {
            "critical_alert": "incident_alert",
            "remediation_summary": "remediation_summary",
            "approval_request": "approval_request",
            "remediation_notification": "remediation_summary",
        }

        return template_mapping.get(workflow_stage, "incident_alert")

    async def _send_slack_notification(
        self,
        tool: BaseTool,
        context: ToolContext,
        message: str,
        data: Dict[str, Any],
        priority: str,
    ) -> Dict[str, Any]:
        """Send Slack notification."""
        attachments = []

        # Build attachment based on data
        if data.get("affected_resources"):
            attachments.append(
                {
                    "affected_resources": ", ".join(data["affected_resources"][:5]),
                    "severity": data.get("severity", "medium"),
                    "incident_id": data.get("incident_id"),
                }
            )

        result = await tool.execute(  # type: ignore[attr-defined]
            context,
            message=message[:500],  # Slack message limit
            priority=priority,
            attachments=attachments,
        )

        if isinstance(result, dict):
            result["channel"] = "slack"
            return result
        else:
            return {"status": "error", "error": "Invalid tool result", "channel": "slack"}

    async def _send_email_notification(
        self,
        tool: BaseTool,
        context: ToolContext,
        message: str,
        data: Dict[str, Any],
        priority: str,
    ) -> Dict[str, Any]:
        """Send email notification."""
        recipients = self.recipient_mapping.get("email", [])
        subject = f"Security Incident: {data.get('incident_id')}"

        result = await tool.execute(  # type: ignore[attr-defined]
            context,
            recipients=recipients,
            subject=subject,
            body=message,
            priority=priority,
        )

        if isinstance(result, dict):
            result["channel"] = "email"
            return result
        else:
            return {"status": "error", "error": "Invalid tool result", "channel": "email"}

    async def _send_sms_notification(
        self, tool: BaseTool, context: ToolContext, _message: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send SMS notification for critical incidents."""
        phone_numbers = self.recipient_mapping.get("sms", [])

        # Shorten message for SMS
        sms_message = (
            f"CRITICAL: Incident {data.get('incident_id')} - "
            f"{data.get('description', 'Security alert')[:100]}"
        )

        result = await tool.execute(  # type: ignore[attr-defined]
            context, phone_numbers=phone_numbers, message=sms_message
        )

        if isinstance(result, dict):
            result["channel"] = "sms"
            return result
        else:
            return {"status": "error", "error": "Invalid tool result", "channel": "sms"}
