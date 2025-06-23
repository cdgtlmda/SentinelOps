def get_telemetry_data() -> dict[str, str]:
    """Get basic telemetry data."""
    from datetime import datetime, timezone

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "active",
        "version": "1.0.0",
    }
