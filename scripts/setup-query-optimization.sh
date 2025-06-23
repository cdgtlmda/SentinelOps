#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
ENVIRONMENT="${2:-prod}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [ENVIRONMENT]"
    exit 1
fi

echo "Setting up query optimization for project: $PROJECT_ID"
echo "Environment: $ENVIRONMENT"

# Enable Query Insights for Cloud SQL
echo "Enabling Query Insights..."
INSTANCE_NAME="sentinelops-db-${ENVIRONMENT}"

gcloud sql instances patch $INSTANCE_NAME \
    --insights-config-query-insights-enabled \
    --insights-config-query-string-length=1024 \
    --insights-config-record-application-tags \
    --project="$PROJECT_ID"

# Create BigQuery optimization views
echo "Creating BigQuery optimization views..."
cat > /tmp/create_optimization_views.sql <<EOF
-- Create materialized view for frequently accessed data
CREATE MATERIALIZED VIEW IF NOT EXISTS \`${PROJECT_ID}.sentinelops_${ENVIRONMENT}.security_events_daily\`
PARTITION BY DATE(event_time)
CLUSTER BY severity, event_type
AS
SELECT 
    DATE(event_time) as event_date,
    event_type,
    severity,
    COUNT(*) as event_count,
    ARRAY_AGG(STRUCT(event_id, event_time, details) 
        ORDER BY event_time DESC LIMIT 100) as sample_events
FROM \`${PROJECT_ID}.sentinelops_${ENVIRONMENT}.security_events\`
WHERE event_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
GROUP BY event_date, event_type, severity;

-- Create optimized view for threat detection
CREATE OR REPLACE VIEW \`${PROJECT_ID}.sentinelops_${ENVIRONMENT}.threat_summary\`
AS
SELECT 
    threat_id,
    threat_type,
    first_seen,
    last_seen,
    severity_score,
    affected_resources,
    detection_confidence
FROM \`${PROJECT_ID}.sentinelops_${ENVIRONMENT}.threats\`
WHERE status = 'ACTIVE'
    AND last_seen >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR);
EOF# Execute BigQuery optimizations
bq query --use_legacy_sql=false < /tmp/create_optimization_views.sql

# Create index recommendations script
echo "Generating index recommendations..."
cat > /tmp/analyze_queries.py <<'EOF'
#!/usr/bin/env python3
import subprocess
import json
from datetime import datetime, timedelta

def get_slow_queries(project_id, instance_name):
    """Get slow queries from Cloud SQL Query Insights"""
    cmd = f"""gcloud sql operations list \
        --instance={instance_name} \
        --project={project_id} \
        --filter="start_time>'{(datetime.now() - timedelta(days=7)).isoformat()}'" \
        --format=json"""
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return json.loads(result.stdout) if result.returncode == 0 else []

def generate_index_recommendations(slow_queries):
    """Generate index recommendations based on slow queries"""
    recommendations = []
    
    # Analyze query patterns and recommend indexes
    # This is a simplified example - expand based on actual query patterns
    
    return recommendations

if __name__ == "__main__":
    import sys
    project_id = sys.argv[1]
    instance_name = f"sentinelops-db-{sys.argv[2]}"
    
    slow_queries = get_slow_queries(project_id, instance_name)
    recommendations = generate_index_recommendations(slow_queries)
    
    print("Index Recommendations:")
    for rec in recommendations:
        print(f"  - {rec}")
EOF

chmod +x /tmp/analyze_queries.py# Create query performance monitoring dashboard
echo "Creating query performance monitoring..."
cat > /tmp/create_query_dashboard.py <<'EOF'
from google.cloud import monitoring_dashboard_v1
import json

def create_query_performance_dashboard(project_id, environment):
    client = monitoring_dashboard_v1.DashboardsServiceClient()
    project_name = f"projects/{project_id}"
    
    dashboard = {
        "displayName": f"SentinelOps Query Performance - {environment}",
        "gridLayout": {
            "widgets": [
                {
                    "title": "Cloud SQL Query Latency",
                    "xyChart": {
                        "dataSets": [{
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.type="cloudsql_database" AND metric.type="cloudsql.googleapis.com/database/mysql/queries"',
                                    "aggregation": {
                                        "alignmentPeriod": "60s",
                                        "perSeriesAligner": "ALIGN_RATE"
                                    }
                                }
                            }
                        }]
                    }
                },
                {
                    "title": "BigQuery Slot Utilization",
                    "xyChart": {
                        "dataSets": [{
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.type="bigquery_project" AND metric.type="bigquery.googleapis.com/slots/total_allocated"',
                                    "aggregation": {
                                        "alignmentPeriod": "60s",
                                        "perSeriesAligner": "ALIGN_MEAN"
                                    }
                                }
                            }
                        }]
                    }
                }
            ]
        }
    }
    
    return client.create_dashboard(parent=project_name, dashboard=dashboard)
EOF

# Execute query optimization analysis
python3 /tmp/analyze_queries.py "$PROJECT_ID" "$ENVIRONMENT"

echo "Query optimization setup complete!"
echo "Monitor query performance in Cloud Console"
echo "Review slow query log regularly for optimization opportunities"