from datetime import datetime, timezone


def get_compliance_report() -> dict[str, str | float | int]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "compliance_score": 0.95,
        "checks_passed": 15,
        "total_checks": 16,
    }
