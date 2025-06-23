"""
Main message formatter for the Communication Agent.

Integrates markdown formatting, visualizations, and contextual
information to create rich, formatted messages.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Union

from src.communication_agent.formatting.markdown import MarkdownFormatter
from src.communication_agent.formatting.visualizations import (
    ChartGenerator,
    TimelineGenerator,
)
from src.communication_agent.types import NotificationChannel
from src.utils.logging import get_logger

logger = get_logger(__name__)


class MessageFormatter:
    """
    Main formatter for creating rich, formatted messages.

    Provides high-level formatting functions that combine
    markdown, visualizations, and contextual information.
    """

    def __init__(self) -> None:
        """Initialize the message formatter."""
        self.markdown = MarkdownFormatter()
        self.charts = ChartGenerator()
        self.timelines = TimelineGenerator()

    def format_incident_details(
        self,
        incident: Dict[str, Any],
        include_timeline: bool = True,
        include_resources: bool = True,
    ) -> str:
        """
        Format comprehensive incident details.

        Args:
            incident: Incident data
            include_timeline: Whether to include timeline
            include_resources: Whether to include affected resources

        Returns:
            Formatted incident details
        """
        sections = []

        # Header with severity badge
        severity = incident.get("severity", "unknown")
        incident_id = incident.get("id", "Unknown")
        incident_type = incident.get("type", "Security Incident")

        sections.append(
            self.markdown.heading(f"Incident {incident_id}: {incident_type}", level=2)
        )
        sections.append(self.markdown.format_severity_badge(severity))
        sections.append("")

        # Key details table
        details = [
            ["Field", "Value"],
            ["Incident ID", incident_id],
            ["Type", incident_type],
            ["Severity", severity.upper()],
            ["Status", incident.get("status", "Active")],
            [
                "Detected",
                self.markdown.format_timestamp(
                    incident.get("detected_at", datetime.now(timezone.utc).isoformat())
                ),
            ],
            ["Source", incident.get("detection_source", "Unknown")],
        ]

        sections.append(self.markdown.heading("Key Information", level=3))
        sections.append(
            self.markdown.table(
                headers=details[0],
                rows=details[1:],
                alignment=["left", "left"],
            )
        )
        sections.append("")

        # Description
        if "description" in incident:
            sections.append(self.markdown.heading("Description", level=3))
            sections.append(incident["description"])
            sections.append("")

        # Affected resources
        if include_resources and "affected_resources" in incident:
            sections.append(self.markdown.heading("Affected Resources", level=3))
            sections.append(
                self.markdown.format_resource_list(incident["affected_resources"])
            )
            sections.append("")

        # Impact assessment
        if "impact" in incident:
            sections.append(self.markdown.heading("Impact Assessment", level=3))
            impact = incident["impact"]
            if isinstance(impact, dict):
                impact_items: List[str] = []
                for key, value in impact.items():
                    impact_items.append(
                        self.markdown.format_key_value(key.title(), value)
                    )
                sections.append(self.markdown.bullet_list(impact_items))
            else:
                sections.append(str(impact))
            sections.append("")

        # Timeline
        if include_timeline and "timeline" in incident:
            sections.append(self.markdown.heading("Event Timeline", level=3))
            sections.append(self.timelines.event_timeline(incident["timeline"]))
            sections.append("")

        # Recommended actions
        if "recommended_actions" in incident:
            sections.append(self.markdown.heading("Recommended Actions", level=3))
            actions = incident["recommended_actions"]
            if isinstance(actions, list):
                sections.append(self.markdown.numbered_list(actions))
            else:
                sections.append(str(actions))
            sections.append("")

        return "\n".join(sections)

    def format_analysis_results(  # noqa: C901
        self,
        analysis: Dict[str, Any],
        include_charts: bool = True,
    ) -> str:
        """
        Format analysis results with visualizations.

        Args:
            analysis: Analysis data
            include_charts: Whether to include charts

        Returns:
            Formatted analysis results
        """
        sections = []

        # Header
        sections.append(self.markdown.heading("Analysis Results", level=2))

        # Summary
        if "summary" in analysis:
            sections.append(self.markdown.quote(analysis["summary"]))
            sections.append("")

        # Risk assessment
        if "risk_assessment" in analysis:
            risk = analysis["risk_assessment"]
            risk_level = risk.get("level", "Unknown")
            risk_score = risk.get("score", 0)

            sections.append(self.markdown.heading("Risk Assessment", level=3))
            sections.append(
                self.markdown.format_alert(
                    f"Risk Level: {self.markdown.bold(risk_level.upper())} "
                    f"(Score: {risk_score}/10)",
                    alert_type="danger" if risk_score > 7 else "warning",
                )
            )
            sections.append("")

            # Risk factors
            if "factors" in risk:
                sections.append("**Risk Factors:**")
                sections.append(self.markdown.bullet_list(risk["factors"]))
                sections.append("")

        # Threat indicators
        if "threat_indicators" in analysis and include_charts:
            indicators = analysis["threat_indicators"]
            if isinstance(indicators, dict):
                sections.append(self.markdown.heading("Threat Indicators", level=3))
                sections.append(self.charts.bar_chart(indicators, width=30))
                sections.append("")

        # Attack patterns
        if "attack_patterns" in analysis:
            sections.append(self.markdown.heading("Detected Attack Patterns", level=3))
            patterns = analysis["attack_patterns"]
            if isinstance(patterns, list):
                pattern_items: List[Union[str, Dict[str, Any]]] = []
                for pattern in patterns:
                    if isinstance(pattern, dict):
                        name = pattern.get("name", "Unknown")
                        confidence = pattern.get("confidence", 0)
                        pattern_items.append(f"{name} (Confidence: {confidence}%)")
                    else:
                        pattern_items.append(str(pattern))
                sections.append(self.markdown.bullet_list(pattern_items))
            sections.append("")

        # Vulnerabilities
        if "vulnerabilities" in analysis:
            sections.append(
                self.markdown.heading("Identified Vulnerabilities", level=3)
            )
            vulns = analysis["vulnerabilities"]

            if isinstance(vulns, list) and vulns:
                # Create vulnerability table
                headers = ["CVE ID", "Severity", "CVSS", "Affected Component"]
                rows = []

                for vuln in vulns:
                    if isinstance(vuln, dict):
                        rows.append(
                            [
                                vuln.get("cve_id", "N/A"),
                                vuln.get("severity", "Unknown"),
                                str(vuln.get("cvss_score", "N/A")),
                                vuln.get("component", "Unknown"),
                            ]
                        )

                if rows:
                    sections.append(self.markdown.table(headers, rows))
                    sections.append("")

        # Recommendations
        if "recommendations" in analysis:
            sections.append(self.markdown.heading("Recommendations", level=3))
            recs = analysis["recommendations"]

            if isinstance(recs, dict):
                # Categorized recommendations
                for category, items in recs.items():
                    sections.append(f"**{category}:**")
                    if isinstance(items, list):
                        sections.append(self.markdown.numbered_list(items))
                    else:
                        sections.append(str(items))
                    sections.append("")
            elif isinstance(recs, list):
                sections.append(self.markdown.numbered_list(recs))
                sections.append("")

        return "\n".join(sections)

    def format_remediation_summary(  # noqa: C901
        self,
        remediation: Dict[str, Any],
        include_progress: bool = True,
    ) -> str:
        """
        Format remediation action summary.

        Args:
            remediation: Remediation data
            include_progress: Whether to include progress bars

        Returns:
            Formatted remediation summary
        """
        sections = []

        # Header
        remediation_id = remediation.get("id", "Unknown")
        sections.append(
            self.markdown.heading(f"Remediation Summary - {remediation_id}", level=2)
        )

        # Status
        status = remediation.get("status", "Unknown")
        success = status.lower() in ["completed", "success"]
        sections.append(self.markdown.format_status_indicator(status, success))
        sections.append("")

        # Progress
        if include_progress:
            completed = remediation.get("actions_completed", 0)
            total = remediation.get("total_actions", 0)

            if total > 0:
                sections.append("**Overall Progress:**")
                sections.append(self.timelines.progress_bar(completed, total))
                sections.append("")

        # Actions taken
        if "actions" in remediation:
            sections.append(self.markdown.heading("Actions Taken", level=3))

            actions = remediation["actions"]
            if isinstance(actions, list):
                action_items: List[Union[str, Dict[str, Any]]] = []
                for action in actions:
                    if isinstance(action, dict):
                        name = action.get("name", "Action")
                        status = action.get("status", "pending")
                        duration = action.get("duration", "N/A")

                        success = status.lower() in ["completed", "success"]
                        status_text = self.markdown.format_status_indicator(
                            status, success
                        )

                        action_items.append(
                            f"{status_text} {name} (Duration: {duration})"
                        )
                    else:
                        action_items.append(str(action))

                sections.append(self.markdown.bullet_list(action_items))
                sections.append("")

        # Results
        if "results" in remediation:
            sections.append(self.markdown.heading("Results", level=3))
            results = remediation["results"]

            if isinstance(results, dict):
                # Show before/after comparison
                if "before" in results and "after" in results:
                    sections.append("**Configuration Changes:**")
                    for key in results["before"]:
                        if key in results["after"]:
                            before_val = results["before"][key]
                            after_val = results["after"][key]
                            if before_val != after_val:
                                sections.append(
                                    f"- {key}: {self.markdown.format_diff(before_val, after_val)}"
                                )
                    sections.append("")
                else:
                    # Generic results
                    for key, value in results.items():
                        sections.append(
                            self.markdown.format_key_value(key.title(), value)
                        )
            else:
                sections.append(str(results))
            sections.append("")

        # Verification
        if "verification" in remediation:
            sections.append(self.markdown.heading("Verification", level=3))
            verification = remediation["verification"]

            if isinstance(verification, dict):
                passed = verification.get("passed", False)
                checks = verification.get("checks", [])

                if passed:
                    sections.append(
                        self.markdown.format_alert(
                            "All verification checks passed", alert_type="success"
                        )
                    )
                else:
                    sections.append(
                        self.markdown.format_alert(
                            "Some verification checks failed", alert_type="warning"
                        )
                    )

                if checks:
                    sections.append("")
                    check_items: List[Union[str, Dict[str, Any]]] = []
                    for check in checks:
                        if isinstance(check, dict):
                            name = check.get("name", "Check")
                            passed = check.get("passed", False)
                            indicator = "✅" if passed else "❌"
                            check_items.append(f"{indicator} {name}")
                        else:
                            check_items.append(str(check))
                    sections.append(self.markdown.bullet_list(check_items))

            sections.append("")

        return "\n".join(sections)

    def format_for_channel(
        self,
        content: str,
        channel: NotificationChannel,
    ) -> str:
        """
        Format content for a specific notification channel.

        Args:
            content: Markdown-formatted content
            channel: Target notification channel

        Returns:
            Channel-optimized content
        """
        if channel == NotificationChannel.SLACK:
            return self.markdown.to_slack_format(content)
        elif channel == NotificationChannel.SMS:
            # Convert to plain text and truncate
            plain = self.markdown.to_plain_text(content)
            # SMS typically has 160 char limit
            if len(plain) > 160:
                return plain[:157] + "..."
            return plain
        elif channel == NotificationChannel.EMAIL:
            # Email supports full markdown/HTML
            return content
        else:
            # Webhooks and other channels typically want markdown
            return content

    def create_summary_report(  # noqa: C901
        self,
        incidents: List[Dict[str, Any]],
        period: str = "daily",
        include_stats: bool = True,
    ) -> str:
        """
        Create a summary report for multiple incidents.

        Args:
            incidents: List of incident data
            period: Report period (daily, weekly, monthly)
            include_stats: Whether to include statistics

        Returns:
            Formatted summary report
        """
        sections = []

        # Header
        title = f"{period.title()} Security Summary"
        sections.append(self.markdown.heading(title, level=1))
        sections.append(
            f"Report generated: "
            f"{self.markdown.format_timestamp(datetime.now(timezone.utc).isoformat())}"
        )
        sections.append("")

        # Statistics
        if include_stats and incidents:
            sections.append(self.markdown.heading("Statistics", level=2))

            # Count by severity
            severity_counts: Dict[str, int] = {}
            for incident in incidents:
                severity = incident.get("severity", "unknown").lower()
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # Total incidents
            total = len(incidents)
            sections.append(f"**Total Incidents:** {total}")
            sections.append("")

            # Severity breakdown
            if severity_counts:
                sections.append("**By Severity:**")
                # Convert int values to float for bar_chart compatibility
                severity_counts_float = {
                    k: float(v) for k, v in severity_counts.items()
                }
                sections.append(self.charts.bar_chart(severity_counts_float, width=20))
                sections.append("")

            # Trend
            if period == "daily" and total > 0:
                # Compare with previous period (mock data)
                previous = total - 2  # Mock previous count
                sections.append(
                    f"**Trend:** {self.charts.trend_indicator(total, previous)}"
                )
                sections.append("")

        # Critical incidents
        critical_incidents = [
            i for i in incidents if i.get("severity", "").lower() == "critical"
        ]

        if critical_incidents:
            sections.append(self.markdown.heading("Critical Incidents", level=2))
            sections.append(
                self.markdown.format_alert(
                    f"{len(critical_incidents)} critical incidents require immediate attention",
                    alert_type="danger",
                )
            )
            sections.append("")

            # List critical incidents
            for incident in critical_incidents[:5]:  # Limit to 5
                incident_id = incident.get("id", "Unknown")
                incident_type = incident.get("type", "Security Incident")
                sections.append(f"- {self.markdown.bold(incident_id)}: {incident_type}")

            if len(critical_incidents) > 5:
                sections.append(f"- ... and {len(critical_incidents) - 5} more")
            sections.append("")

        # Recent incidents
        if incidents:
            sections.append(self.markdown.heading("Recent Incidents", level=2))

            # Create incident table
            headers = ["Time", "ID", "Type", "Severity", "Status"]
            rows = []

            for incident in incidents[:10]:  # Limit to 10
                rows.append(
                    [
                        incident.get("detected_at", "Unknown")[
                            :16
                        ],  # Truncate timestamp
                        incident.get("id", "Unknown"),
                        incident.get("type", "Unknown")[:20],  # Truncate type
                        incident.get("severity", "Unknown").upper(),
                        incident.get("status", "Active"),
                    ]
                )

            sections.append(self.markdown.table(headers, rows))

            if len(incidents) > 10:
                sections.append(f"\n*Showing 10 of {len(incidents)} total incidents*")

        sections.append("")
        sections.append(self.markdown.horizontal_rule())
        sections.append(
            self.markdown.italic(
                "This report was automatically generated by SentinelOps"
            )
        )

        return "\n".join(sections)
