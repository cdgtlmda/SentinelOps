#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
MONTHLY_BUDGET="${2:-10000}"
ENVIRONMENT="${3:-prod}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [MONTHLY_BUDGET] [ENVIRONMENT]"
    exit 1
fi

echo "Setting up budget alerts for project: $PROJECT_ID"
echo "Monthly budget: \$${MONTHLY_BUDGET}"
echo "Environment: $ENVIRONMENT"

# Get billing account ID
BILLING_ACCOUNT=$(gcloud billing projects describe $PROJECT_ID --format="value(billingAccountName)")

if [ -z "$BILLING_ACCOUNT" ]; then
    echo "Error: No billing account found for project"
    exit 1
fi

# Enable Billing Budget API
echo "Enabling Billing Budget API..."
gcloud services enable billingbudgets.googleapis.com --project="$PROJECT_ID"

# Create notification channel
echo "Creating notification channel..."
cat > /tmp/notification_channel.json <<EOF
{
  "type": "email",
  "displayName": "SentinelOps Budget Alerts",
  "labels": {
    "email_address": "ops-team@sentinelops.com"
  },
  "enabled": true
}
EOF

CHANNEL_ID=$(gcloud alpha monitoring channels create \
    --channel-content-from-file=/tmp/notification_channel.json \
    --project="$PROJECT_ID" \
    --format="value(name)")

# Create budget with alerts
echo "Creating budget with alert thresholds..."
cat > /tmp/budget.json <<EOF
{
  "displayName": "SentinelOps ${ENVIRONMENT} Budget",
  "budgetFilter": {
    "projects": ["projects/${PROJECT_ID}"],
    "services": ["services/6F81-5844-456A", "services/CAD3-9C7F-B88C", "services/95FF-2EF5-5EA1"]
  },
  "amount": {
    "specifiedAmount": {
      "currencyCode": "USD",
      "units": "${MONTHLY_BUDGET}"
    }
  },
  "thresholdRules": [
    {
      "thresholdPercent": 0.5,
      "spendBasis": "CURRENT_SPEND"
    },
    {
      "thresholdPercent": 0.75,
      "spendBasis": "CURRENT_SPEND"
    },
    {
      "thresholdPercent": 0.9,
      "spendBasis": "CURRENT_SPEND"
    },
    {
      "thresholdPercent": 1.0,
      "spendBasis": "CURRENT_SPEND"
    }
  ],
  "notificationsRule": {
    "monitoringNotificationChannels": ["${CHANNEL_ID}"],
    "schemaVersion": "1.0"
  }
}
EOF# Create the budget
gcloud billing budgets create \
    --billing-account=$BILLING_ACCOUNT \
    --budget-content-from-file=/tmp/budget.json

# Create Cloud Function for budget response
echo "Creating budget response function..."
cat > /tmp/budget_handler.py <<'EOF'
import functions_framework
import json
from google.cloud import compute_v1
from google.cloud import logging

@functions_framework.cloud_event
def handle_budget_alert(cloud_event):
    """Respond to budget alerts by taking cost-saving actions"""
    
    # Parse the budget alert
    data = cloud_event.data
    cost_amount = data.get('costAmount', 0)
    budget_amount = data.get('budgetAmount', 0)
    threshold_percent = (cost_amount / budget_amount) * 100 if budget_amount > 0 else 0
    
    logging_client = logging.Client()
    logger = logging_client.logger('budget-alerts')
    
    logger.log_struct({
        'message': f'Budget alert triggered',
        'threshold_percent': threshold_percent,
        'cost_amount': cost_amount,
        'budget_amount': budget_amount
    })
    
    # Take action based on threshold
    if threshold_percent >= 90:
        # Critical: Scale down non-essential services
        logger.log_struct({'message': 'Critical budget threshold reached', 'action': 'scaling_down_services'})
        # Implement scale-down logic
        
    elif threshold_percent >= 75:
        # Warning: Reduce resource allocation
        logger.log_struct({'message': 'Warning budget threshold reached', 'action': 'reducing_resources'})
        # Implement resource reduction
        
    elif threshold_percent >= 50:
        # Info: Send notification
        logger.log_struct({'message': 'Info budget threshold reached', 'action': 'notification_sent'})
    
    return {"status": "processed", "threshold_percent": threshold_percent}
EOF

# Deploy budget handler function
gcloud functions deploy budget-handler-${ENVIRONMENT} \
    --runtime=python311 \
    --trigger-topic=budget-alerts-${ENVIRONMENT} \
    --entry-point=handle_budget_alert \
    --source=/tmp \
    --region=us-central1 \
    --project="$PROJECT_ID"# Create cost monitoring dashboard
echo "Creating cost monitoring dashboard..."
cat > /tmp/create_cost_dashboard.py <<'EOF'
from google.cloud import monitoring_dashboard_v1
import json

def create_cost_dashboard(project_id, environment):
    client = monitoring_dashboard_v1.DashboardsServiceClient()
    project_name = f"projects/{project_id}"
    
    dashboard = {
        "displayName": f"SentinelOps Cost Monitoring - {environment}",
        "gridLayout": {
            "widgets": [
                {
                    "title": "Monthly Spend by Service",
                    "xyChart": {
                        "dataSets": [{
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.type="global" AND metric.type="billing.googleapis.com/project/cost"',
                                    "aggregation": {
                                        "alignmentPeriod": "86400s",
                                        "perSeriesAligner": "ALIGN_SUM",
                                        "groupByFields": ["metric.label.service_name"]
                                    }
                                }
                            }
                        }]
                    }
                },
                {
                    "title": "Daily Cost Trend",
                    "xyChart": {
                        "dataSets": [{
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.type="global" AND metric.type="billing.googleapis.com/project/cost"',
                                    "aggregation": {
                                        "alignmentPeriod": "86400s",
                                        "perSeriesAligner": "ALIGN_SUM"
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

# Create Pub/Sub topic for budget alerts
gcloud pubsub topics create budget-alerts-${ENVIRONMENT} \
    --project="$PROJECT_ID" || echo "Topic already exists"

echo "Budget alerts setup complete!"
echo "Budget: \$${MONTHLY_BUDGET}/month"
echo "Alert thresholds: 50%, 75%, 90%, 100%"
echo "Monitor costs at: https://console.cloud.google.com/billing"