#!/usr/bin/env python3
"""
Coverage gate script for CI/CD pipeline.
Enforces coverage requirements and generates detailed reports.
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Tuple


def parse_coverage_xml(coverage_file: str) -> Dict[str, float]:
    """Parse coverage.xml and extract metrics."""
    tree = ET.parse(coverage_file)
    root = tree.getroot()

    # Get overall coverage
    overall = float(root.attrib.get("line-rate", 0)) * 100

    # Get package-level coverage
    packages = {}
    for package in root.findall(".//package"):
        name = package.attrib.get("name", "unknown")
        line_rate = float(package.attrib.get("line-rate", 0)) * 100
        packages[name] = line_rate

    return {"overall": overall, "packages": packages}


def check_coverage_requirements(
    metrics: Dict[str, float], min_coverage: float
) -> Tuple[bool, str]:
    """Check if coverage meets requirements."""
    overall = metrics["overall"]

    if overall < min_coverage:
        message = f"❌ Coverage {overall:.1f}% is below minimum {min_coverage}%"
        return False, message

    # Check critical packages
    critical_packages = [
        "src.detection_agent",
        "src.analysis_agent",
        "src.remediation_agent",
        "src.communication_agent",
    ]

    failed_packages = []
    for pkg in critical_packages:
        pkg_coverage = metrics["packages"].get(pkg, 0)
        if pkg_coverage < min_coverage:
            failed_packages.append(f"{pkg}: {pkg_coverage:.1f}%")

    if failed_packages:
        message = f"❌ Critical packages below {min_coverage}%:\n" + "\n".join(
            failed_packages
        )
        return False, message

    return True, f"✅ Coverage {overall:.1f}% meets requirements"


def main():
    """Main entry point."""
    coverage_file = sys.argv[1] if len(sys.argv) > 1 else "coverage.xml"
    min_coverage = float(sys.argv[2]) if len(sys.argv) > 2 else 90.0

    if not Path(coverage_file).exists():
        print("❌ Coverage file not found: {coverage_file}")
        sys.exit(1)

    metrics = parse_coverage_xml(coverage_file)
    passed, message = check_coverage_requirements(metrics, min_coverage)

    print(message)
    print("\nOverall coverage: {metrics['overall']:.1f}%")
    print("\nPackage coverage:")
    for pkg, cov in sorted(metrics["packages"].items()):
        print("  {pkg}: {cov:.1f}%")

    # Save metrics for reporting
    with open("coverage_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
