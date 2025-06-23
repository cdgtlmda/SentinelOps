#!/bin/bash
# Script to create log views in Cloud Console

echo "📋 Log Views Configuration for SentinelOps"
echo ""
echo "Please create the following log views in Cloud Console:"
echo "https://console.cloud.google.com/logs/query?project=$PROJECT_ID"
echo ""

echo "View: security-incidents"
echo "Filter: jsonPayload.event_type="security_incident""
echo "Description: Security incidents across all agents"
echo "---"

echo "View: remediation-actions"
echo "Filter: resource.type="cloud_function" AND jsonPayload.action=~"remediation.*""
echo "Description: All remediation actions"
echo "---"

echo "View: agent-errors"
echo "Filter: severity >= ERROR AND resource.type="cloud_run_revision""
echo "Description: Errors from all agents"
echo "---"

echo "View: api-requests"
echo "Filter: httpRequest.requestUrl=~".+""
echo "Description: All API requests"
echo "---"
