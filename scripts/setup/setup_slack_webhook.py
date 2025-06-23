#!/usr/bin/env python3
"""
Script to help set up and test Slack webhook integration for SentinelOps.
"""

import os
import json
import requests
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

SLACK_WEBHOOK_DOCS = """
To create a Slack webhook for SentinelOps:

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name it "SentinelOps Alert Bot"
4. Select your workspace
5. Go to "Incoming Webhooks" in the sidebar
6. Toggle "Activate Incoming Webhooks" to ON
7. Click "Add New Webhook to Workspace"
8. Select the channel for alerts (e.g., #security-incidents)
9. Copy the webhook URL

The webhook URL will look like:
https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
"""


def load_env_file(env_path: str) -> dict:
    """Load environment variables from .env file."""
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars


def save_env_file(env_path: str, env_vars: dict):
    """Save environment variables to .env file."""
    lines = []

    # Read existing file to preserve comments and order
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('#'):
                    key = line_stripped.split('=', 1)[0].strip() if '=' in line_stripped else None
                    if key and key in env_vars:
                        lines.append(f"{key}={env_vars[key]}\n")
                        del env_vars[key]  # Remove from dict so we don't add it again
                    else:
                        lines.append(line)
                else:
                    lines.append(line)

    # Add any new variables
    for key, value in env_vars.items():
        lines.append(f"{key}={value}\n")

    with open(env_path, 'w') as f:
        f.writelines(lines)


def test_webhook(webhook_url: str) -> bool:
    """Test the Slack webhook by sending a test message."""
    test_message = {
        "text": "🚀 SentinelOps Test Message",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*SentinelOps Slack Integration Test*\n✅ Your webhook is configured correctly!"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Status:*\nOperational"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Component:*\nCommunication Agent"
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(webhook_url, json=test_message, timeout=10)
        return response.status_code == 200
    except Exception as e:
        console.print("[red]Error testing webhook: {e}[/red]")
        return False


def create_webhook_config():
    """Create Slack webhook configuration file."""
    config = {
        "webhook_settings": {
            "retry_attempts": 3,
            "timeout_seconds": 10,
            "rate_limit": {
                "max_messages_per_minute": 10,
                "burst_limit": 20
            }
        },
        "message_templates": {
            "incident_detected": {
                "severity_high": {
                    "color": "danger",
                    "emoji": "🚨"
                },
                "severity_medium": {
                    "color": "warning",
                    "emoji": "⚠️"
                },
                "severity_low": {
                    "color": "good",
                    "emoji": "ℹ️"
                }
            },
            "remediation_complete": {
                "color": "good",
                "emoji": "✅"
            },
            "analysis_report": {
                "color": "#1f77b4",
                "emoji": "📊"
            }
        },
        "channels": {
            "default": "#security-incidents",
            "high_priority": "#security-critical",
            "reports": "#security-reports"
        }
    }

    config_path = "/path/to/sentinelops/src/config/slack_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    console.print("[green]Slack configuration saved to:[/green] {config_path}")


def main():
    """Main function to set up Slack webhook."""
    console.print(Panel("[bold cyan]SentinelOps Slack Webhook Setup[/bold cyan]"))

    # Show instructions
    console.print("\n[bold]Instructions for creating a Slack webhook:[/bold]")
    console.print(SLACK_WEBHOOK_DOCS)

    # Check if webhook already exists in .env
    env_path = "/path/to/sentinelops/.env"
    env_vars = load_env_file(env_path)

    current_webhook = env_vars.get("SLACK_WEBHOOK_URL", "")

    if current_webhook and not current_webhook.startswith("https://"):
        current_webhook = ""

    if current_webhook:
        console.print("\n[yellow]Current webhook URL found:[/yellow] {current_webhook[:50]}...")
        if Confirm.ask("Do you want to test the current webhook?"):
            if test_webhook(current_webhook):
                console.print("[green]✅ Webhook test successful![/green]")
            else:
                console.print("[red]❌ Webhook test failed![/red]")

        if not Confirm.ask("Do you want to update the webhook URL?"):
            create_webhook_config()
            return

    # Get new webhook URL
    webhook_url = Prompt.ask("\nEnter your Slack webhook URL (or 'skip' to add later)")

    if webhook_url.lower() == 'skip':
        # Add placeholder
        env_vars["SLACK_WEBHOOK_URL"] = "https://hooks.slack.com/services/YOUR_WEBHOOK_URL_HERE"
        save_env_file(env_path, env_vars)
        console.print("[yellow]Added placeholder webhook URL to .env file[/yellow]")
        console.print("Remember to update it with your actual webhook URL later!")
    else:
        # Validate and test webhook
        if webhook_url.startswith("https://hooks.slack.com/services/"):
            env_vars["SLACK_WEBHOOK_URL"] = webhook_url
            save_env_file(env_path, env_vars)
            console.print("[green]Webhook URL saved to .env file[/green]")

            if Confirm.ask("Do you want to test the webhook now?"):
                if test_webhook(webhook_url):
                    console.print("[green]✅ Webhook test successful![/green]")
                else:
                    console.print("[red]❌ Webhook test failed! Please check your webhook URL.[/red]")
        else:
            console.print("[red]Invalid webhook URL format![/red]")
            console.print("URL should start with: https://hooks.slack.com/services/")

    # Create configuration file
    create_webhook_config()

    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Update the webhook URL in .env if you used 'skip'")
    console.print("2. Configure channel mappings in src/config/slack_config.json")
    console.print("3. Test the Communication Agent with the webhook")


if __name__ == "__main__":
    main()
