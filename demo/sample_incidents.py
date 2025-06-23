# Sample Security Incidents for SentinelOps Demo

incidents = [
    {
        "incident_id": "INC-2025-001",
        "timestamp": "2025-05-28T10:30:00Z",
        "severity": "HIGH",
        "type": "Unauthorized Access",
        "source_ip": "198.51.100.42",
        "target_resource": "compute.googleapis.com/projects/your-project-id/zones/us-central1-a/instances/web-server-01",
        "description": "Multiple failed SSH login attempts detected from suspicious IP",
        "indicators": {
            "failed_attempts": 47,
            "time_window_minutes": 5,
            "authentication_method": "password",
            "username_tried": ["root", "admin", "ubuntu", "ec2-user"]
        },
        "recommended_actions": [
            "Block source IP in firewall",
            "Enable SSH key-only authentication",
            "Review and rotate credentials"
        ]
    },
    {
        "incident_id": "INC-2025-002",
        "timestamp": "2025-05-28T11:15:00Z",
        "severity": "CRITICAL",
        "type": "Data Exfiltration",
        "source_ip": "10.0.1.45",
        "target_resource": "storage.googleapis.com/your-project-id-sensitive-data",
        "description": "Unusual data transfer volume detected from internal IP to external destination",
        "indicators": {
            "data_transferred_gb": 45.7,
            "destination_ip": "203.0.113.12",
            "destination_country": "Unknown",
            "normal_daily_average_gb": 2.3,
            "anomaly_score": 0.94
        },
        "recommended_actions": [
            "Immediately revoke access for compromised service account",
            "Block outbound traffic to destination IP",
            "Initiate incident response protocol",
            "Preserve logs for forensic analysis"
        ]
    },
    {
        "incident_id": "INC-2025-003",
        "timestamp": "2025-05-28T12:00:00Z",
        "severity": "MEDIUM",
        "type": "Privilege Escalation",
        "source_ip": "10.0.2.78",
        "target_resource": "iam.googleapis.com/projects/your-project-id/serviceAccounts/app-service@your-project-id.iam.gserviceaccount.com",
        "description": "Service account granted excessive permissions",
        "indicators": {
            "new_roles": ["roles/owner", "roles/iam.securityAdmin"],
            "granted_by": "user:suspicious@example.com",
            "previous_roles": ["roles/viewer"],
            "risk_score": 0.78
        },
        "recommended_actions": [
            "Revert IAM changes immediately",
            "Investigate the granting user account",
            "Implement IAM change alerts",
            "Review all recent IAM modifications"
        ]
    }
]
