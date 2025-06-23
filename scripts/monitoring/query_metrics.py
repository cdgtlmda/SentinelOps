#!/usr/bin/env python3
"""Query SentinelOps metrics"""

from datetime import datetime, timedelta

from google.cloud import monitoring_v3

PROJECT_ID = "your-gcp-project-id"


def query_incident_count():
    """Query security incident count for the last hour"""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{PROJECT_ID}"

    interval = monitoring_v3.TimeInterval(
        {
            "end_time": {"seconds": int(datetime.now().timestamp())},
            "start_time": {
                "seconds": int((datetime.now() - timedelta(hours=1)).timestamp())
            },
        }
    )

    results = client.list_time_series(
        request={
            "name": project_name,
            "filter": 'metric.type="logging.googleapis.com/user/incident_count"',
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        }
    )

    for result in results:
        print("Incident count: {result}")


if __name__ == "__main__":
    query_incident_count()
