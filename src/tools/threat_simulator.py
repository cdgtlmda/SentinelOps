"""
SentinelOps Threat Simulator
Generates realistic threat scenarios for testing and demonstration
"""

import random
import string
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, cast

import yaml
import numpy as np


class ThreatSimulator:
    """Generates realistic threat scenarios based on templates"""

    def __init__(self, scenarios_file: Optional[str] = None):
        self.scenarios_file = scenarios_file or "config/threat_scenarios.yaml"
        self.scenarios = self._load_scenarios()

    def _load_scenarios(self) -> Dict[str, Any]:
        """Load threat scenarios from YAML configuration"""
        try:
            with open(self.scenarios_file, "r", encoding="utf-8") as f:
                result = yaml.safe_load(f)
                return cast(Dict[str, Any], result)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Scenarios file not found: {self.scenarios_file}") from exc

    def rand_hex(self, n: int = 6) -> str:
        """Generate random hex string"""
        return "".join(random.choices("abcdef0123456789", k=n))

    def rand_ip(self) -> str:
        """Generate random IP address"""
        return f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"

    def rand_external_ip(self) -> str:
        """Generate random external IP from suspicious ranges"""
        suspicious_ranges = [
            (1, 126),
            (128, 191),
            (192, 223),  # Avoiding private ranges
        ]
        range_choice = random.choice(suspicious_ranges)
        return f"{random.randint(range_choice[0], range_choice[1])}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"

    def rand_sha256(self) -> str:
        """Generate random SHA256 hash"""
        random_data = "".join(
            random.choices(string.ascii_letters + string.digits, k=32)
        )
        return hashlib.sha256(random_data.encode()).hexdigest()

    def ts_now(self) -> str:
        """Generate current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()

    def random_values(self) -> Dict[str, Any]:
        """Generate random values for template substitution"""
        generators = self.scenarios.get("random_generators", {})

        values = {
            "ts": self.ts_now(),
            "bucket": f"demo-{self.rand_hex()}",
            "fqdn": f"app-{random.randint(1, 9)}.example.com",
            "user": random.choice(
                generators.get(
                    "user", ["alice@corp.com", "bob@corp.com", "svc-ci@corp.com"]
                )
            ),
            "attacker_ip": self.rand_ip(),
            "country": random.choice(
                generators.get("country", ["RU", "CN", "BR", "IR", "NG"])
            ),
            "subnet": f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.0/24",
            "ports": random.randint(50, 400),
            "vm": random.choice(generators.get("vm", ["web-1", "web-2", "db-1"])),
            "attacks": random.randint(20, 100),
            "dump_size": round(random.uniform(5, 30), 1),
            "db": random.choice(generators.get("db", ["orders-prod", "auth-prod"])),
            "files": random.randint(200, 5000),
            "domain": f"{self.rand_hex(8)}.bad.tld",
            "qps": random.randint(200, 800),
            "payload": self.rand_hex(12),
            "key_age": random.randint(90, 365),
            "patch_count": random.randint(3, 15),
            "port": random.choice([8080, 3389, 22, 445, 135]),
            "log_bucket": f"logs-{self.rand_hex(4)}",
            "retention": random.randint(7, 30),
            "violations": random.randint(2, 8),
            "storage_account": f"storage-{self.rand_hex(4)}",
            "usage": random.randint(85, 95),
            "api_endpoint": f"/api/v1/{random.choice(['users', 'orders', 'auth', 'data'])}",
            "rpm": random.randint(1000, 5000),
            "cpu_usage": random.randint(80, 100),
            "mining_pool": random.choice(
                ["pool.minergate.com", "xmr-pool.com", "cryptonight.net"]
            ),
            "small_transfer": round(random.uniform(1.5, 8.0), 1),
            "external_ip": self.rand_external_ip(),
            "malware_sig": random.choice(
                ["Trojan.Win32.Agent", "PUP.Optional.Miner", "Backdoor.Linux.Mirai"]
            ),
            "file_hash": self.rand_sha256(),
            "access_count": random.randint(50, 200),
            "resource_count": random.randint(20, 100),
            "container": f"container-{self.rand_hex(8)}",
            "escape_technique": random.choice(
                ["privileged_mount", "host_pid_namespace", "docker_socket"]
            ),
            "package": random.choice(
                ["eslint-scope", "event-stream", "ua-parser-js", "rc", "coa"]
            ),
            "version": f"1.{random.randint(0, 9)}.{random.randint(0, 20)}",
            "malware_family": random.choice(
                ["SolarWinds", "CodeCov", "Kaseya", "Log4Shell"]
            ),
            "attack_volume": random.randint(10, 100),
            "attack_type": random.choice(
                ["UDP_FLOOD", "SYN_FLOOD", "HTTP_FLOOD", "DNS_AMPLIFICATION"]
            ),
            "source_vm": random.choice(["web-1", "web-2", "api-1"]),
            "target_vm": random.choice(["db-1", "admin-1", "backup-1"]),
            "protocol": random.choice(["RDP", "SSH", "WinRM", "SMB"]),
        }

        return values

    def generate_scenario(
        self, scenario_id: Optional[str] = None, severity: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a single threat scenario"""
        scenarios = self.scenarios.get("scenarios", [])

        if scenario_id:
            # Find specific scenario
            scenario = next((s for s in scenarios if s["id"] == scenario_id), None)
            if not scenario:
                raise ValueError(f"Scenario {scenario_id} not found")
        elif severity:
            # Filter by severity
            filtered_scenarios = [
                s for s in scenarios if s["severity"] == severity.upper()
            ]
            if not filtered_scenarios:
                raise ValueError(f"No scenarios found for severity {severity}")
            scenario = random.choice(filtered_scenarios)
        else:
            # Random scenario
            scenario = random.choice(scenarios)

        # Generate random values for template substitution
        values = self.random_values()

        # Substitute template variables
        template = scenario["template"].strip()
        for key, value in values.items():
            template = template.replace("{{ " + key + " }}", str(value))

        # Parse the JSON template
        try:
            event_data = json.loads(template)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON template in scenario {scenario['id']}: {e}") from e

        # Add metadata
        event_data.update(
            {
                "scenario_id": scenario["id"],
                "scenario_category": scenario.get("category", "Unknown"),
                "mitre_tactic": scenario.get("mitre_tactic", ""),
                "mitre_technique": scenario.get("mitre_technique", ""),
                "generated_at": self.ts_now(),
                "simulator_version": "1.0.0",
            }
        )

        return cast(Dict[str, Any], event_data)

    def generate_batch(
        self, count: int = 10, severity_distribution: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """Generate a batch of threat scenarios with specified distribution"""
        if severity_distribution is None:
            # Default distribution: 40% LOW, 35% MEDIUM, 25% CRITICAL
            severity_distribution = {"LOW": 0.4, "MEDIUM": 0.35, "CRITICAL": 0.25}

        events = []
        for _ in range(count):
            # Choose severity based on distribution
            rand = random.random()
            cumulative = 0.0
            chosen_severity = "MEDIUM"  # default

            for severity, probability in severity_distribution.items():
                cumulative += probability
                if rand <= cumulative:
                    chosen_severity = severity
                    break

            try:
                event = self.generate_scenario(severity=chosen_severity)
                events.append(event)
            except ValueError:
                # Fallback to random scenario if severity not found
                event = self.generate_scenario()
                events.append(event)

        return events

    def get_scenario_stats(self) -> Dict[str, Any]:
        """Get statistics about available scenarios"""
        scenarios = self.scenarios.get("scenarios", [])

        severity_counts: Dict[str, int] = {}
        category_counts: Dict[str, int] = {}

        for scenario in scenarios:
            severity = scenario.get("severity", "UNKNOWN")
            category = scenario.get("category", "Unknown")

            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1

        return {
            "total_scenarios": len(scenarios),
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "scenario_ids": [s["id"] for s in scenarios],
        }

    def simulate_attack_campaign(
        self, duration_minutes: int = 60, intensity: str = "medium"
    ) -> List[Dict[str, Any]]:
        """Simulate a coordinated attack campaign over time"""
        intensity_settings = {
            "low": {"events_per_minute": 0.5, "escalation_probability": 0.1},
            "medium": {"events_per_minute": 2, "escalation_probability": 0.3},
            "high": {"events_per_minute": 5, "escalation_probability": 0.6},
        }

        settings = intensity_settings.get(intensity, intensity_settings["medium"])
        events = []
        current_severity = "LOW"

        for minute in range(duration_minutes):
            # Determine if severity should escalate
            if random.random() < settings["escalation_probability"]:
                if current_severity == "LOW":
                    current_severity = "MEDIUM"
                elif current_severity == "MEDIUM":
                    current_severity = "CRITICAL"

            # Generate events for this minute
            events_this_minute = max(
                1, int(np.random.poisson(settings["events_per_minute"]))
            )

            for _ in range(events_this_minute):
                try:
                    event = self.generate_scenario(severity=current_severity)
                    # Adjust timestamp to simulate progression
                    base_time = datetime.now(timezone.utc)
                    event_time = base_time.replace(minute=minute % 60)
                    event["timestamp"] = event_time.isoformat()
                    event["campaign_minute"] = minute
                    events.append(event)
                except ValueError:
                    continue

        return events


def main() -> None:
    """CLI interface for threat simulator"""
    import argparse

    parser = argparse.ArgumentParser(description="SentinelOps Threat Simulator")
    parser.add_argument("--scenario", help="Generate specific scenario by ID")
    parser.add_argument(
        "--severity",
        choices=["LOW", "MEDIUM", "CRITICAL"],
        help="Generate scenario by severity",
    )
    parser.add_argument(
        "--batch", type=int, default=1, help="Generate batch of scenarios"
    )
    parser.add_argument("--stats", action="store_true", help="Show scenario statistics")
    parser.add_argument(
        "--campaign", type=int, help="Simulate attack campaign (duration in minutes)"
    )
    parser.add_argument(
        "--intensity",
        choices=["low", "medium", "high"],
        default="medium",
        help="Campaign intensity",
    )
    parser.add_argument("--output", help="Output file (JSON)")

    args = parser.parse_args()

    simulator = ThreatSimulator()

    if args.stats:
        stats = simulator.get_scenario_stats()
        print(json.dumps(stats, indent=2))
        return

    if args.campaign:
        events = simulator.simulate_attack_campaign(args.campaign, args.intensity)
        print(f"Generated {len(events)} events for {args.campaign}-minute campaign")
    elif args.batch > 1:
        events = simulator.generate_batch(args.batch)
    else:
        event = simulator.generate_scenario(args.scenario, args.severity)
        events = [event]

    output = json.dumps(events, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Output written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
