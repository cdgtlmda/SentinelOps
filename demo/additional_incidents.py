# Additional Sample Security Incidents

additional_incidents = [
    {
        "incident_id": "INC-2025-004",
        "timestamp": "2025-05-28T13:30:00Z",
        "severity": "HIGH",
        "type": "Cryptomining Activity",
        "source_ip": "10.0.3.112",
        "target_resource": "compute.googleapis.com/projects/your-project-id/zones/us-east1-b/instances/backend-api-03",
        "description": "Abnormal CPU usage pattern consistent with cryptocurrency mining",
        "indicators": {
            "cpu_usage_percent": 98.5,
            "duration_hours": 3.2,
            "processes_detected": ["xmrig", "minergate"],
            "network_connections": ["pool.minexmr.com:4444", "xmr-us-east1.nanopool.org:14444"],
            "estimated_cost_impact_usd": 127.50
        },
        "recommended_actions": [
            "Terminate suspicious processes",
            "Isolate affected instance",
            "Scan for malware and rootkits",
            "Review instance access logs"
        ]
    },
    {
        "incident_id": "INC-2025-005",
        "timestamp": "2025-05-28T14:45:00Z",
        "severity": "MEDIUM",
        "type": "API Key Exposure",
        "source_ip": "public",
        "target_resource": "github.com/user/repo/commit/abc123",
        "description": "Google Cloud API key found in public repository",
        "indicators": {
            "key_type": "Service Account Key",
            "key_age_days": 45,
            "key_permissions": ["storage.objects.create", "bigquery.datasets.get"],
            "repository_visibility": "public",
            "exposure_duration_hours": 2.5
        },
        "recommended_actions": [
            "Rotate exposed API key immediately",
            "Scan for unauthorized usage",
            "Implement secret scanning in CI/CD",
            "Train developers on secure coding practices"
        ]
    },
    {
        "incident_id": "INC-2025-006",
        "timestamp": "2025-05-28T15:20:00Z",
        "severity": "LOW",
        "type": "Suspicious Login Pattern",
        "source_ip": "variable",
        "target_resource": "console.cloud.google.com",
        "description": "User account accessed from multiple geographic locations within short timeframe",
        "indicators": {
            "login_locations": ["New York, USA", "London, UK", "Tokyo, Japan"],
            "time_between_logins_minutes": 45,
            "user_email": "developer@example.com",
            "impossible_travel_detected": True,
            "mfa_enabled": False
        },
        "recommended_actions": [
            "Force password reset",
            "Enable mandatory MFA",
            "Review recent account activity",
            "Contact user to verify legitimate access"
        ]
    }
]
