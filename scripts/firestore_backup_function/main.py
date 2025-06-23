import json
import os
from datetime import datetime

import requests
from google.cloud import firestore


def firestore_backup(request):
    """Cloud Function to backup Firestore using REST API"""

    project_id = os.environ.get("GCP_PROJECT", "your-gcp-project-id")
    backup_bucket = f"gs://{project_id}-firestore-backups"

    # Generate backup path with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{backup_bucket}/firestore_backup/{timestamp}"

    # Use the Firestore REST API to trigger export
    from google.auth import default
    from google.auth.transport.requests import Request

    # Get credentials
    credentials, _ = default()
    credentials.refresh(Request())

    # Firestore export endpoint
    url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default):exportDocuments"

    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }

    data = {"outputUriPrefix": backup_path}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()

        return {
            "status": "success",
            "backup_path": backup_path,
            "timestamp": timestamp,
            "operation": result.get("name", "N/A"),
            "metadata": result.get("metadata", {}),
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "backup_path": backup_path}, 500
