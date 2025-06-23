#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
ENVIRONMENT="${2:-prod}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [ENVIRONMENT]"
    exit 1
fi

echo "Setting up DDoS protection for project: $PROJECT_ID"
echo "Environment: $ENVIRONMENT"

# Enable Cloud Armor Adaptive Protection
echo "Enabling Cloud Armor Adaptive Protection..."
gcloud compute security-policies update sentinelops-waf-${ENVIRONMENT} \
    --enable-layer7-ddos-defense \
    --layer7-ddos-defense-rule-visibility=STANDARD \
    --project="$PROJECT_ID"

# Create DDoS-specific security policy
echo "Creating DDoS protection policy..."
gcloud compute security-policies create sentinelops-ddos-${ENVIRONMENT} \
    --description="SentinelOps DDoS protection policy" \
    --type=CLOUD_ARMOR_EDGE \
    --project="$PROJECT_ID"

# Add geographic restrictions (optional - customize as needed)
echo "Adding geographic restrictions..."
gcloud compute security-policies rules create 3000 \
    --security-policy=sentinelops-ddos-${ENVIRONMENT} \
    --expression="origin.region_code == 'CN' || origin.region_code == 'RU'" \
    --action=deny-403 \
    --description="Block high-risk regions" \
    --project="$PROJECT_ID"# Add connection throttling
echo "Configuring connection throttling..."
gcloud compute security-policies rules create 3001 \
    --security-policy=sentinelops-ddos-${ENVIRONMENT} \
    --expression="true" \
    --action=throttle \
    --rate-limit-threshold-count=50 \
    --rate-limit-threshold-interval-sec=10 \
    --conform-action=allow \
    --exceed-action=deny-429 \
    --enforce-on-key=IP \
    --description="Connection throttling - 50 requests per 10 seconds" \
    --project="$PROJECT_ID"

# Configure Cloud CDN for DDoS mitigation
echo "Configuring Cloud CDN for DDoS mitigation..."
gcloud compute backend-services update sentinelops-backend-${ENVIRONMENT} \
    --enable-cdn \
    --cache-mode=CACHE_ALL_STATIC \
    --default-ttl=3600 \
    --max-ttl=86400 \
    --negative-caching \
    --project="$PROJECT_ID"

# Set up Cloud Armor Edge Security Policy
echo "Configuring Edge Security Policy..."
gcloud compute security-policies rules create 3002 \
    --security-policy=sentinelops-ddos-${ENVIRONMENT} \
    --expression="hasHeader('user-agent') && header('user-agent').contains('bot')" \
    --action=deny-403 \
    --description="Block suspicious bot traffic" \
    --project="$PROJECT_ID"

# Enable logging for DDoS events
echo "Enabling DDoS event logging..."
gcloud compute security-policies update sentinelops-ddos-${ENVIRONMENT} \
    --log-level=VERBOSE \
    --project="$PROJECT_ID"

echo "DDoS protection setup complete!"
echo "Note: Full DDoS protection requires Google Cloud Armor Managed Protection Plus"