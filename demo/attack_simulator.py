#!/usr/bin/env python3
"""
Attack simulation script for SentinelOps demo.
Simulates realistic attack scenarios to showcase the platform's capabilities.
"""

import asyncio
import json
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Any
import subprocess
import sys

# Color codes for terminal output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class AttackSimulator:
    """Simulates various attack scenarios for demo purposes."""

    def __init__(self, project_id: str = "your-gcp-project-id"):
        self.project_id = project_id
        self.simulated_ips = [
            "198.51.100.42",  # Suspicious external IP
            "203.0.113.12",   # Data exfiltration destination
            "192.0.2.178",    # Compromised internal IP
        ]

    def print_scenario(self, title: str, description: str):
        """Print scenario information with formatting."""
        print("\n{BLUE}{'=' *60}{RESET}")
        print("{YELLOW}ATTACK SCENARIO: {title}{RESET}")
        print("{BLUE}{'=' *60}{RESET}")
        print("{description}\n")

    async def simulate_brute_force_attack(self):
        """Simulate SSH brute force attack."""
        self.print_scenario(
            "SSH Brute Force Attack",
            "Simulating multiple failed SSH login attempts from suspicious IP addresses.\n"
            "This demonstrates the detection of unauthorized access attempts."
        )

        attack_data = {
            "attack_type": "brute_force",
            "target_service": "SSH",
            "target_port": 22,
            "source_ips": random.sample(self.simulated_ips, 2),
            "attempts": []
        }

        usernames = ["root", "admin", "ubuntu", "ec2-user", "postgres", "mysql"]

        print("{RED}[ATTACK]{RESET} Starting brute force simulation...")

        for i in range(15):
            attempt = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_ip": random.choice(attack_data["source_ips"]),
                "username": random.choice(usernames),
                "status": "failed",
                "attempt_number": i + 1
            }
            attack_data["attempts"].append(attempt)

            print("{RED}[ATTEMPT {i +1}]{RESET} {attempt['source_ip']} -> "
                  f"SSH login as '{attempt['username']}' - FAILED")

            await asyncio.sleep(0.5)  # Rapid attempts

        print("\n{GREEN}[DETECTION]{RESET} Attack pattern detected! "
              f"Triggering security response...")

        return attack_data

    async def simulate_data_exfiltration(self):
        """Simulate data exfiltration attack."""
        self.print_scenario(
            "Data Exfiltration Attack",
            "Simulating large data transfer to external destination.\n"
            "This demonstrates detection of potential data theft."
        )

        bucket_name = f"gs://{self.project_id}-sensitive-data"
        destination_ip = "203.0.113.12"

        print("{RED}[ATTACK]{RESET} Initiating data exfiltration...")
        print("{YELLOW}[SOURCE]{RESET} {bucket_name}")
        print("{YELLOW}[DESTINATION]{RESET} {destination_ip}:443 (HTTPS)")

        total_size = 0
        files_transferred = []

        for i in range(5):
            file_size = random.uniform(5, 15)  # GB
            total_size += file_size

            file_info = {
                "filename": f"sensitive_data_{i +1}.db",
                "size_gb": round(file_size, 2),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            files_transferred.append(file_info)

            print("{RED}[TRANSFER]{RESET} {file_info['filename']} "
                  f"({file_info['size_gb']} GB) -> {destination_ip}")

            await asyncio.sleep(1)

        print("\n{RED}[ALERT]{RESET} Total data transferred: {round(total_size, 2)} GB")
        print("{GREEN}[DETECTION]{RESET} Anomalous data transfer detected! "
              f"Initiating response...")

        return {
            "attack_type": "data_exfiltration",
            "source": bucket_name,
            "destination": destination_ip,
            "total_size_gb": round(total_size, 2),
            "files": files_transferred
        }

    async def simulate_privilege_escalation(self):
        """Simulate privilege escalation attack."""
        self.print_scenario(
            "Privilege Escalation Attack",
            "Simulating unauthorized elevation of user privileges.\n"
            "This demonstrates detection of IAM policy violations."
        )

        compromised_user = "developer@example.com"
        service_account = f"app-service@{self.project_id}.iam.gserviceaccount.com"

        print("{RED}[ATTACK]{RESET} Compromised user: {compromised_user}")
        print("{YELLOW}[TARGET]{RESET} Service account: {service_account}")

        escalation_steps = [
            {
                "action": "List current roles",
                "command": f"gcloud iam service-accounts get-iam-policy {service_account}",
                "result": "Current role: roles/viewer"
            },
            {
                "action": "Attempt to add editor role",
                "command": "gcloud iam service-accounts add-iam-policy-binding",
                "result": "Added role: roles/editor"
            },
            {
                "action": "Escalate to owner role",
                "command": f"gcloud projects add-iam-policy-binding {self.project_id}",
                "result": "Added role: roles/owner (CRITICAL)"
            }
        ]

        for step in escalation_steps:
            print("\n{RED}[STEP]{RESET} {step['action']}")
            print("{YELLOW}[COMMAND]{RESET} {step['command'][:50]}...")
            await asyncio.sleep(1)
            print("{RED}[RESULT]{RESET} {step['result']}")

        print("\n{GREEN}[DETECTION]{RESET} Privilege escalation detected! "
              f"Triggering immediate response...")

        return {
            "attack_type": "privilege_escalation",
            "compromised_user": compromised_user,
            "target_account": service_account,
            "escalation_chain": escalation_steps
        }

    async def simulate_cryptomining(self):
        """Simulate cryptomining attack."""
        self.print_scenario(
            "Cryptomining Malware",
            "Simulating cryptocurrency mining on compromised compute instance.\n"
            "This demonstrates detection of resource abuse."
        )

        instance_name = "backend-api-prod-03"

        print("{RED}[ATTACK]{RESET} Cryptominer deployed on: {instance_name}")
        print("{YELLOW}[PROCESS]{RESET} xmrig (PID: 31337)")

        cpu_usage = []
        for i in range(10):
            usage = random.uniform(85, 99)
            cpu_usage.append(usage)

            bar = "█" * int(usage / 5)
            print("{RED}[CPU]{RESET} {bar} {usage:.1f}%")

            await asyncio.sleep(0.5)

        print("\n{YELLOW}[MINING POOL]{RESET} Connected to: pool.minexmr.com:4444")
        print("{RED}[COST IMPACT]{RESET} Estimated: $12.50/hour")

        print("\n{GREEN}[DETECTION]{RESET} Cryptomining activity detected! "
              f"Initiating cleanup...")

        return {
            "attack_type": "cryptomining",
            "instance": instance_name,
            "process": "xmrig",
            "avg_cpu_usage": round(sum(cpu_usage) / len(cpu_usage), 2),
            "mining_pool": "pool.minexmr.com:4444"
        }


async def run_demo_scenario(scenario: str = "all"):
    """Run specific attack scenario or all scenarios."""
    simulator = AttackSimulator()

    scenarios = {
        "brute_force": simulator.simulate_brute_force_attack,
        "exfiltration": simulator.simulate_data_exfiltration,
        "privilege": simulator.simulate_privilege_escalation,
        "cryptomining": simulator.simulate_cryptomining
    }

    if scenario == "all":
        print("{BLUE}Running all attack scenarios for SentinelOps demo...{RESET}")
        results = []

        for name, func in scenarios.items():
            result = await func()
            results.append(result)

            print("\n{GREEN}[COMPLETE]{RESET} {name} scenario finished.")
            print("{YELLOW}Waiting before next scenario...{RESET}\n")
            await asyncio.sleep(3)

        return results

    elif scenario in scenarios:
        return await scenarios[scenario]()

    else:
        print("{RED}Unknown scenario: {scenario}{RESET}")
        print("Available scenarios: {', '.join(scenarios.keys())}, all")
        sys.exit(1)


def main():
    """Main entry point for attack simulator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="SentinelOps Attack Simulator for Demo"
    )
    parser.add_argument(
        "--scenario",
        choices=["brute_force", "exfiltration", "privilege", "cryptomining", "all"],
        default="all",
        help="Attack scenario to simulate"
    )
    parser.add_argument(
        "--output",
        help="Output file for attack data (JSON format)"
    )

    args = parser.parse_args()

    # Run the simulation
    results = asyncio.run(run_demo_scenario(args.scenario))

    # Save results if output file specified
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print("\n{GREEN}Attack data saved to: {args.output}{RESET}")

    print("\n{BLUE}{'=' *60}{RESET}")
    print("{GREEN}Demo simulation complete!{RESET}")
    print("{BLUE}{'=' *60}{RESET}")


if __name__ == "__main__":
    main()
