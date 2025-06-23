#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
ENVIRONMENT="${2:-prod}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [ENVIRONMENT]"
    exit 1
fi

echo "Setting up Cloud Armor WAF for project: $PROJECT_ID"
echo "Environment: $ENVIRONMENT"

# Enable Cloud Armor API
echo "Enabling Cloud Armor API..."
gcloud services enable compute.googleapis.com --project="$PROJECT_ID"

# Create security policy
echo "Creating Cloud Armor security policy..."
gcloud compute security-policies create sentinelops-waf-${ENVIRONMENT} \
    --description="SentinelOps WAF security policy" \
    --project="$PROJECT_ID"

# Add OWASP Top 10 rules
echo "Adding OWASP Top 10 protection rules..."

# SQL Injection protection
gcloud compute security-policies rules create 1000 \
    --security-policy=sentinelops-waf-${ENVIRONMENT} \
    --expression="evaluatePreconfiguredExpr('sqli-stable')" \
    --action=deny-403 \
    --description="SQL injection protection" \
    --project="$PROJECT_ID"# XSS protection
gcloud compute security-policies rules create 1001 \
    --security-policy=sentinelops-waf-${ENVIRONMENT} \
    --expression="evaluatePreconfiguredExpr('xss-stable')" \
    --action=deny-403 \
    --description="Cross-site scripting protection" \
    --project="$PROJECT_ID"

# Remote Code Execution protection
gcloud compute security-policies rules create 1002 \
    --security-policy=sentinelops-waf-${ENVIRONMENT} \
    --expression="evaluatePreconfiguredExpr('rce-stable')" \
    --action=deny-403 \
    --description="Remote code execution protection" \
    --project="$PROJECT_ID"

# Local File Inclusion protection
gcloud compute security-policies rules create 1003 \
    --security-policy=sentinelops-waf-${ENVIRONMENT} \
    --expression="evaluatePreconfiguredExpr('lfi-stable')" \
    --action=deny-403 \
    --description="Local file inclusion protection" \
    --project="$PROJECT_ID"

# Remote File Inclusion protection
gcloud compute security-policies rules create 1004 \
    --security-policy=sentinelops-waf-${ENVIRONMENT} \
    --expression="evaluatePreconfiguredExpr('rfi-stable')" \
    --action=deny-403 \
    --description="Remote file inclusion protection" \
    --project="$PROJECT_ID"# Scanner detection
gcloud compute security-policies rules create 1005 \
    --security-policy=sentinelops-waf-${ENVIRONMENT} \
    --expression="evaluatePreconfiguredExpr('scannerdetection-stable')" \
    --action=deny-403 \
    --description="Scanner and bot detection" \
    --project="$PROJECT_ID"

# Protocol attack protection
gcloud compute security-policies rules create 1006 \
    --security-policy=sentinelops-waf-${ENVIRONMENT} \
    --expression="evaluatePreconfiguredExpr('protocolattack-stable')" \
    --action=deny-403 \
    --description="Protocol attack protection" \
    --project="$PROJECT_ID"

# Rate limiting rule
echo "Adding rate limiting rules..."
gcloud compute security-policies rules create 2000 \
    --security-policy=sentinelops-waf-${ENVIRONMENT} \
    --expression="true" \
    --action=rate-based-ban \
    --rate-limit-threshold-count=100 \
    --rate-limit-threshold-interval-sec=60 \
    --ban-duration-sec=600 \
    --conform-action=allow \
    --exceed-action=deny-429 \
    --enforce-on-key=IP \
    --description="Rate limiting - 100 requests per minute" \
    --project="$PROJECT_ID"

# Apply to backend services
echo "Applying WAF policy to backend services..."
gcloud compute backend-services update sentinelops-backend-${ENVIRONMENT} \
    --security-policy=sentinelops-waf-${ENVIRONMENT} \
    --project="$PROJECT_ID"

echo "WAF configuration complete!"