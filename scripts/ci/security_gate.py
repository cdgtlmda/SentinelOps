#!/usr/bin/env python3
"""Security gate to prevent security vulnerabilities in CI/CD."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SecurityGate:
    """Performs security checks and enforces security policies in CI/CD."""

    def __init__(self):
        """Initialize security gate."""
        # Security thresholds
        self.thresholds = {
            "high_severity_limit": 0,  # No high severity issues allowed
            "medium_severity_limit": 5,  # Max 5 medium severity issues
            "low_severity_limit": 20,  # Max 20 low severity issues
            "cvss_score_limit": 7.0,  # No vulnerabilities with CVSS >= 7.0
        }

        # Known false positives or accepted risks
        self.whitelist = {
            "bandit": [],  # List of bandit issue IDs to ignore
            "safety": [],  # List of CVE IDs to ignore
            "secrets": [],  # List of secret patterns to ignore
        }

    def run_all_checks(self) -> Tuple[bool, List[str]]:
        """Run all security checks.

        Returns:
            Tuple of (passed, list of failures)
        """
        all_failures = []

        # Run individual security checks
        checks = [
            ("Bandit (AST Security)", self.check_bandit),
            ("Safety (Dependency Security)", self.check_safety),
            ("Secret Detection", self.check_secrets),
            ("SAST Analysis", self.check_sast),
            ("License Compliance", self.check_licenses),
            ("Security Headers", self.check_security_headers),
        ]

        for check_name, check_func in checks:
            print("\n🔍 Running {check_name}...")
            passed, failures = check_func()

            if not passed:
                all_failures.extend([f"[{check_name}] {f}" for f in failures])
                print("❌ {check_name} failed with {len(failures)} issue(s)")
            else:
                print("✅ {check_name} passed")

        return len(all_failures) == 0, all_failures

    def check_bandit(self, report_file: Optional[str] = None) -> Tuple[bool, List[str]]:
        """Check for security issues using Bandit.

        Args:
            report_file: Path to bandit JSON report (if pre-generated)

        Returns:
            Tuple of (passed, list of failures)
        """
        if report_file and Path(report_file).exists():
            with open(report_file, "r") as f:
                results = json.load(f)
        else:
            # Run bandit
            cmd = ["bandit", "-r", "src", "-f", "json", "-ll"]
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False
                )
                results = json.loads(result.stdout)
            except Exception as e:
                return False, [f"Failed to run bandit: {e}"]

        # Process results
        failures = []
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for issue in results.get("results", []):
            severity = issue["issue_severity"]
            severity_counts[severity] += 1

            # Skip whitelisted issues
            if issue["test_id"] in self.whitelist["bandit"]:
                continue

            if severity == "HIGH":
                failures.append(
                    f"{issue['filename']}:{issue['line_number']} - "
                    f"{issue['issue_text']} (CWE-{issue.get('cwe', 'unknown')})"
                )

        # Check against thresholds
        if severity_counts["HIGH"] > self.thresholds["high_severity_limit"]:
            failures.append(
                f"Found {severity_counts['HIGH']} high severity issues "
                f"(limit: {self.thresholds['high_severity_limit']})"
            )

        if severity_counts["MEDIUM"] > self.thresholds["medium_severity_limit"]:
            failures.append(
                f"Found {severity_counts['MEDIUM']} medium severity issues "
                f"(limit: {self.thresholds['medium_severity_limit']})"
            )

        return len(failures) == 0, failures

    def check_safety(self, report_file: Optional[str] = None) -> Tuple[bool, List[str]]:
        """Check for known security vulnerabilities in dependencies.

        Args:
            report_file: Path to safety JSON report (if pre-generated)

        Returns:
            Tuple of (passed, list of failures)
        """
        if report_file and Path(report_file).exists():
            with open(report_file, "r") as f:
                results = json.load(f)
        else:
            # Run safety check
            cmd = ["safety", "check", "--json"]
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False
                )
                results = json.loads(result.stdout)
            except Exception as e:
                return False, [f"Failed to run safety check: {e}"]

        failures = []

        for vuln in results.get("vulnerabilities", []):
            # Skip whitelisted CVEs
            if vuln.get("cve") in self.whitelist["safety"]:
                continue

            # Check CVSS score
            cvss_score = vuln.get("cvss_score", 0)
            if cvss_score >= self.thresholds["cvss_score_limit"]:
                failures.append(
                    f"{vuln['package']} {vuln['installed_version']} - "
                    f"{vuln['vulnerability']} (CVSS: {cvss_score})"
                )

        return len(failures) == 0, failures

    def check_secrets(self) -> Tuple[bool, List[str]]:
        """Check for hardcoded secrets and credentials.

        Returns:
            Tuple of (passed, list of failures)
        """
        failures = []

        # Patterns for common secrets
        secret_patterns = [
            (r'(?i)api[_\s-]?key\s*=\s*["\'][\w\-]+["\']', "API Key"),
            (r'(?i)secret[_\s-]?key\s*=\s*["\'][\w\-]+["\']', "Secret Key"),
            (r'(?i)password\s*=\s*["\'][^"\']+["\']', "Hardcoded Password"),
            (r'(?i)token\s*=\s*["\'][\w\-\.]+["\']', "Access Token"),
            (r'(?i)private[_\s-]?key\s*=\s*["\'][^"\']+["\']', "Private Key"),
            (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", "Private Key File"),
        ]

        # Files to check
        extensions = [
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".env",
            ".yaml",
            ".yml",
            ".json",
        ]
        exclude_dirs = {"node_modules", ".git", "__pycache__", "venv", ".env"}

        for file_path in Path("src").rglob("*"):
            if file_path.is_file() and file_path.suffix in extensions:
                # Skip excluded directories
                if any(excluded in file_path.parts for excluded in exclude_dirs):
                    continue

                try:
                    content = file_path.read_text()

                    for pattern, secret_type in secret_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            line_num = content[: match.start()].count("\n") + 1

                            # Check if whitelisted
                            if match.group(0) in self.whitelist["secrets"]:
                                continue

                            # Check if it's a placeholder
                            value = match.group(0)
                            if any(
                                placeholder in value.lower()
                                for placeholder in [
                                    "example",
                                    "placeholder",
                                    "your-",
                                    "xxx",
                                    "***",
                                    "<",
                                ]
                            ):
                                continue

                            failures.append(
                                f"{file_path}:{line_num} - Potential {secret_type} found"
                            )

                except Exception:
                    continue

        return len(failures) == 0, failures

    def check_sast(self) -> Tuple[bool, List[str]]:
        """Perform Static Application Security Testing.

        Returns:
            Tuple of (passed, list of failures)
        """
        failures = []

        # Security anti-patterns to check
        security_checks = [
            # SQL Injection
            (r'f["\'].*SELECT.*WHERE.*{.*}', "Potential SQL Injection"),
            (
                r"\.format\(.*\).*(?:SELECT|INSERT|UPDATE|DELETE)",
                "Potential SQL Injection",
            ),
            # Command Injection
            (
                r"subprocess\.(?:call|run|Popen)\([^,\]]*\+",
                "Potential Command Injection",
            ),
            (r"os\.system\([^)]*\+", "Potential Command Injection"),
            # Path Traversal
            (r"open\([^,)]*\+", "Potential Path Traversal"),
            # XXE
            (
                r"etree\.parse\([^,)]*,\s*parser\s*=\s*None",
                "Potential XXE Vulnerability",
            ),
            # Insecure Random
            (
                r"random\.(?:random|randint|choice)\s*\(",
                "Insecure Random Number Generator",
            ),
            # Weak Cryptography
            (r"hashlib\.(?:md5|sha1)\s*\(", "Weak Cryptographic Hash"),
            # Insecure Deserialization
            (r"pickle\.loads?\s*\(", "Insecure Deserialization"),
            (r"yaml\.load\s*\([^,)]*\)", "Insecure YAML Loading"),
        ]

        for file_path in Path("src").rglob("*.py"):
            try:
                content = file_path.read_text()

                for pattern, issue_type in security_checks:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        failures.append(f"{file_path}:{line_num} - {issue_type}")

            except Exception:
                continue

        return len(failures) == 0, failures

    def check_licenses(self) -> Tuple[bool, List[str]]:
        """Check for license compliance issues.

        Returns:
            Tuple of (passed, list of failures)
        """
        failures = []

        # List of prohibited licenses
        prohibited_licenses = [
            "GPL",
            "GPLv2",
            "GPLv3",
            "AGPL",
            "AGPL-3.0",
            "Commons Clause",
            "SSPL",
            "SSPL-1.0",
        ]

        # Run pip-licenses
        cmd = ["pip-licenses", "--format=json"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            licenses = json.loads(result.stdout)
        except Exception as e:
            return False, [f"Failed to check licenses: {e}"]

        for package in licenses:
            license_name = package.get("License", "Unknown")

            # Check for prohibited licenses
            for prohibited in prohibited_licenses:
                if prohibited.lower() in license_name.lower():
                    failures.append(
                        f"{package['Name']} uses prohibited license: {license_name}"
                    )
                    break

            # Check for unknown licenses
            if license_name == "Unknown":
                failures.append(f"{package['Name']} has unknown license")

        return len(failures) == 0, failures

    def check_security_headers(self) -> Tuple[bool, List[str]]:
        """Check for security headers in web responses.

        Returns:
            Tuple of (passed, list of failures)
        """
        failures = []

        # Required security headers
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "X-XSS-Protection",
        ]

        # Check FastAPI middleware configuration
        middleware_files = list(Path("src").rglob("*middleware*.py"))

        if not middleware_files:
            failures.append("No middleware configuration found")
            return False, failures

        headers_found = set()

        for file_path in middleware_files:
            try:
                content = file_path.read_text()

                for header in required_headers:
                    if header in content:
                        headers_found.add(header)

            except Exception:
                continue

        # Check for missing headers
        missing_headers = set(required_headers) - headers_found
        for header in missing_headers:
            failures.append(f"Missing security header: {header}")

        return len(failures) == 0, failures

    def generate_security_report(self, failures: List[str]) -> str:
        """Generate security report in markdown format.

        Args:
            failures: List of security failures

        Returns:
            Markdown formatted report
        """
        report = "# Security Gate Report\n\n"

        if not failures:
            report += "✅ **All security checks passed!**\n\n"
            report += "No security vulnerabilities or policy violations detected.\n"
        else:
            report += f"❌ **Security gate failed with {len(failures)} issue(s)**\n\n"

            # Group failures by category
            categories = {}
            for failure in failures:
                category = (
                    failure.split("]")[0].strip("[") if "]" in failure else "General"
                )
                if category not in categories:
                    categories[category] = []
                categories[category].append(failure)

            # Add failures by category
            for category, issues in categories.items():
                report += f"## {category}\n\n"
                for issue in issues:
                    report += f"- {issue}\n"
                report += "\n"

            # Add remediation guide
            report += "## Remediation Guide\n\n"
            report += "1. **High Severity Issues**: Must be fixed immediately\n"
            report += "2. **Dependency Vulnerabilities**: Update packages or add to whitelist if false positive\n"
            report += (
                "3. **Code Security Issues**: Refactor code to use secure patterns\n"
            )
            report += "4. **Secrets**: Remove hardcoded secrets and use environment variables\n"

        return report

    def create_sarif_report(self, failures: List[str], output_file: str):
        """Create SARIF (Static Analysis Results Interchange Format) report.

        Args:
            failures: List of security failures
            output_file: Path to save SARIF report
        """
        sarif = {
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "SentinelOps Security Gate",
                            "version": "1.0.0",
                            "rules": [],
                        }
                    },
                    "results": [],
                }
            ],
        }

        # Convert failures to SARIF format
        for i, failure in enumerate(failures):
            # Parse failure message
            parts = failure.split(" - ", 1)
            if ":" in parts[0]:
                location_parts = parts[0].split(":")
                file_path = location_parts[0].strip("[]").split("] ")[-1]
                line_number = int(location_parts[1]) if len(location_parts) > 1 else 1
            else:
                file_path = "unknown"
                line_number = 1

            message = parts[1] if len(parts) > 1 else failure

            result = {
                "ruleId": f"SEC{i:03d}",
                "level": "error",
                "message": {"text": message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": file_path},
                            "region": {"startLine": line_number},
                        }
                    }
                ],
            }

            sarif["runs"][0]["results"].append(result)

        with open(output_file, "w") as f:
            json.dump(sarif, f, indent=2)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Security gate for CI/CD")
    parser.add_argument("--bandit-report", help="Path to bandit JSON report")
    parser.add_argument("--safety-report", help="Path to safety JSON report")
    parser.add_argument("--generate-report", help="Generate markdown report file")
    parser.add_argument("--sarif-output", help="Generate SARIF report")
    parser.add_argument("--high-limit", type=int, help="Override high severity limit")
    parser.add_argument(
        "--medium-limit", type=int, help="Override medium severity limit"
    )
    parser.add_argument("--whitelist-file", help="Path to whitelist configuration")
    args = parser.parse_args()

    gate = SecurityGate()

    # Load whitelist if provided
    if args.whitelist_file and Path(args.whitelist_file).exists():
        with open(args.whitelist_file, "r") as f:
            gate.whitelist = json.load(f)

    # Override thresholds if provided
    if args.high_limit is not None:
        gate.thresholds["high_severity_limit"] = args.high_limit
    if args.medium_limit is not None:
        gate.thresholds["medium_severity_limit"] = args.medium_limit

    # Run security checks
    passed, failures = gate.run_all_checks()

    # Generate reports if requested
    if args.generate_report:
        report = gate.generate_security_report(failures)
        with open(args.generate_report, "w") as f:
            f.write(report)
        print("\n📄 Security report saved to {args.generate_report}")

    if args.sarif_output:
        gate.create_sarif_report(failures, args.sarif_output)
        print("📄 SARIF report saved to {args.sarif_output}")

    # Print summary and exit
    print("\n" + "=" * 50)
    if passed:
        print("✅ Security gate PASSED")
        print("All security checks completed successfully!")
        sys.exit(0)
    else:
        print("❌ Security gate FAILED")
        print("Found {len(failures)} security issue(s)")
        print("\nTop issues:")
        for failure in failures[:5]:
            print("  - {failure}")
        if len(failures) > 5:
            print("  ... and {len(failures) - 5} more")
        sys.exit(1)


if __name__ == "__main__":
    main()
