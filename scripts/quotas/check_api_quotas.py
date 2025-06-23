#!/usr/bin/env python3
"""
Script to check and monitor Google Cloud API quotas and limits.
This helps ensure the SentinelOps project stays within usage limits.
"""

import json
import subprocess
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Define critical APIs and their recommended quotas for the hackathon
API_QUOTA_RECOMMENDATIONS = {
    "compute.googleapis.com": {
        "name": "Compute Engine API",
        "critical_quotas": [
            {"metric": "CPUS", "recommended": 10, "description": "CPU cores"},
            {"metric": "INSTANCES", "recommended": 5, "description": "VM instances"},
            {"metric": "DISKS_TOTAL_GB", "recommended": 200, "description": "Total disk GB"}
        ]
    },
    "bigquery.googleapis.com": {
        "name": "BigQuery API",
        "critical_quotas": [
            {"metric": "Query usage per day", "recommended": "1 TB", "description": "Daily query limit"},
            {"metric": "Query usage per day per user", "recommended": "100 GB", "description": "Per user query limit"}
        ]
    },
    "aiplatform.googleapis.com": {
        "name": "Vertex AI API",
        "critical_quotas": [
            {"metric": "Prediction requests per minute", "recommended": 60, "description": "Gemini API calls/min"},
            {"metric": "Online prediction requests per minute", "recommended": 300, "description": "Total predictions/min"}
        ]
    },
    "pubsub.googleapis.com": {
        "name": "Pub/Sub API",
        "critical_quotas": [
            {"metric": "Publisher quota", "recommended": "10000", "description": "Messages per second"},
            {"metric": "Subscriber quota", "recommended": "10000", "description": "Messages per second"}
        ]
    },
    "run.googleapis.com": {
        "name": "Cloud Run API",
        "critical_quotas": [
            {"metric": "Services", "recommended": 10, "description": "Number of services"},
            {"metric": "Concurrent requests", "recommended": 1000, "description": "Per service"}
        ]
    }
}


def get_current_project() -> Optional[str]:
    """Get the current Google Cloud project ID."""
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def list_enabled_apis(project_id: str) -> List[str]:
    """List all enabled APIs for the project."""
    try:
        result = subprocess.run(
            ["gcloud", "services", "list", "--enabled", "--format=json", f"--project={project_id}"],
            capture_output=True,
            text=True,
            check=True
        )
        apis = json.loads(result.stdout)
        return [api["config"]["name"] for api in apis]
    except subprocess.CalledProcessError as e:
        console.print("[red]Error listing APIs: {e}[/red]")
        return []


def check_compute_quotas(project_id: str) -> Dict:
    """Check Compute Engine quotas."""
    try:
        result = subprocess.run(
            ["gcloud", "compute", "project-info", "describe", f"--project={project_id}", "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        project_info = json.loads(result.stdout)
        quotas = {}
        for quota in project_info.get("quotas", []):
            quotas[quota["metric"]] = {
                "limit": quota["limit"],
                "usage": quota.get("usage", 0)
            }
        return quotas
    except subprocess.CalledProcessError:
        return {}


def display_quota_summary(project_id: str):
    """Display a summary of API quotas and recommendations."""
    console.print(Panel(f"[bold cyan]API Quotas Check for Project: {project_id}[/bold cyan]"))

    enabled_apis = list_enabled_apis(project_id)
    console.print("\n[green]Found {len(enabled_apis)} enabled APIs[/green]")

    # Check quotas for each critical API
    for api_name, api_config in API_QUOTA_RECOMMENDATIONS.items():
        if api_name in enabled_apis:
            console.print("\n[bold]{api_config['name']}[/bold] ✅ Enabled")

            # Create a table for quotas
            table = Table(title=f"Recommended Quotas for {api_config['name']}")
            table.add_column("Quota", style="cyan")
            table.add_column("Recommended", style="green")
            table.add_column("Description", style="white")

            for quota in api_config["critical_quotas"]:
                table.add_row(
                    quota["metric"],
                    str(quota["recommended"]),
                    quota["description"]
                )

            console.print(table)

            # Special handling for Compute Engine quotas
            if api_name == "compute.googleapis.com":
                compute_quotas = check_compute_quotas(project_id)
                if compute_quotas:
                    console.print("\n[yellow]Current Compute Engine Quotas:[/yellow]")
                    for metric, values in compute_quotas.items():
                        if metric in ["CPUS", "INSTANCES", "DISKS_TOTAL_GB"]:
                            console.print("  {metric}: {values['usage']}/{values['limit']}")
        else:
            console.print("\n[yellow]{api_config['name']}[/yellow] ⚠️  Not enabled")


def generate_quota_config(project_id: str):
    """Generate a quota configuration file for monitoring."""
    config = {
        "project_id": project_id,
        "quota_alerts": [],
        "monitoring_rules": []
    }

    # Add monitoring rules for each API
    for api_name, api_config in API_QUOTA_RECOMMENDATIONS.items():
        for quota in api_config["critical_quotas"]:
            config["quota_alerts"].append({
                "api": api_name,
                "metric": quota["metric"],
                "threshold_percentage": 80,  # Alert at 80% usage
                "description": f"Alert when {quota['description']} exceeds 80% of limit"
            })

    # Save configuration
    config_path = "/path/to/sentinelops/src/config/quota_monitoring.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    console.print("\n[green]Quota monitoring configuration saved to:[/green] {config_path}")


def main():
    """Main function to check and configure API quotas."""
    project_id = get_current_project()

    if not project_id:
        console.print("[red]Error: No Google Cloud project configured[/red]")
        return

    console.print("[bold]Checking API quotas for project:[/bold] {project_id}\n")

    # Display quota summary
    display_quota_summary(project_id)

    # Generate monitoring configuration
    generate_quota_config(project_id)

    # Provide recommendations
    console.print("\n[bold cyan]Recommendations:[/bold cyan]")
    console.print("1. Monitor API usage regularly during development")
    console.print("2. Set up billing alerts in Google Cloud Console")
    console.print("3. Use the free tier efficiently:")
    console.print("   - BigQuery: 1 TB of queries per month free")
    console.print("   - Cloud Run: 2 million requests per month free")
    console.print("   - Pub/Sub: 10 GB per month free")
    console.print("4. For the hackathon demo, consider using:")
    console.print("   - Smaller datasets for BigQuery")
    console.print("   - Rate limiting for Gemini API calls")
    console.print("   - Efficient caching strategies")

    console.print("\n[yellow]Note:[/yellow] Some quotas can only be increased through Google Cloud Console")
    console.print("Visit: https://console.cloud.google.com/iam-admin/quotas")


if __name__ == "__main__":
    main()
