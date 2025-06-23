#!/usr/bin/env python3
"""
Performance gate script for CI/CD pipeline.
Checks if performance benchmarks meet requirements.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def load_benchmarks(benchmark_file: str) -> Dict[str, float]:
    """Load benchmark results from file."""
    with open(benchmark_file, "r") as f:
        return json.load(f)


def check_performance_requirements(
    benchmarks: Dict[str, float],
) -> Tuple[bool, List[str]]:
    """Check if benchmarks meet performance requirements."""
    requirements = {
        "detection_latency_ms": 1000,
        "analysis_latency_ms": 5000,
        "remediation_latency_ms": 3000,
        "notification_latency_ms": 2000,
        "log_throughput_per_sec": 1000,
        "incident_throughput_per_sec": 100,
    }

    failures = []
    for metric, threshold in requirements.items():
        if metric in benchmarks:
            value = benchmarks[metric]
            if metric.endswith("_ms") and value > threshold:
                failures.append(f"{metric}: {value}ms > {threshold}ms (max)")
            elif metric.endswith("_per_sec") and value < threshold:
                failures.append(f"{metric}: {value}/s < {threshold}/s (min)")

    return len(failures) == 0, failures


def main():
    """Main entry point."""
    benchmark_file = sys.argv[1] if len(sys.argv) > 1 else "benchmarks.json"

    if not Path(benchmark_file).exists():
        print("❌ Benchmark file not found: {benchmark_file}")
        sys.exit(1)

    benchmarks = load_benchmarks(benchmark_file)
    passed, failures = check_performance_requirements(benchmarks)

    if passed:
        print("✅ All performance requirements met")
    else:
        print("❌ Performance requirements not met:")
        for failure in failures:
            print("  - {failure}")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
