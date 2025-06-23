#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
DOMAIN="${2:-sentinelops.example.com}"
ENVIRONMENT="${3:-dev}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [DOMAIN] [ENVIRONMENT]"
    exit 1
fi

echo "Setting up load balancing and CDN for project: $PROJECT_ID"

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable compute.googleapis.com --project="$PROJECT_ID"
gcloud services enable certificatemanager.googleapis.com --project="$PROJECT_ID"

# Reserve global IP address
echo "Reserving global IP address..."
gcloud compute addresses create sentinelops-lb-ip-${ENVIRONMENT} \
    --global \
    --project="$PROJECT_ID" || echo "IP already reserved"

LB_IP=$(gcloud compute addresses describe sentinelops-lb-ip-${ENVIRONMENT} \
    --global \
    --project="$PROJECT_ID" \
    --format="value(address)")

echo "Load balancer IP: $LB_IP"

# Create SSL certificate
echo "Creating managed SSL certificate..."
gcloud compute ssl-certificates create sentinelops-ssl-cert-${ENVIRONMENT} \
    --domains="$DOMAIN" \
    --global \
    --project="$PROJECT_ID" || echo "Certificate already exists"

# Create health check
echo "Creating health check..."
gcloud compute health-checks create https sentinelops-health-check-${ENVIRONMENT} \
    --port=443 \
    --request-path=/health \
    --interval=10s \
    --timeout=5s \
    --healthy-threshold=2 \
    --unhealthy-threshold=3 \
    --global \
    --project="$PROJECT_ID" || echo "Health check already exists"

# Create backend service with CDN
echo "Creating backend service with CDN enabled..."
gcloud compute backend-services create sentinelops-backend-${ENVIRONMENT} \
    --protocol=HTTPS \
    --health-checks=sentinelops-health-check-${ENVIRONMENT} \
    --global \
    --enable-cdn \
    --cache-mode=USE_ORIGIN_HEADERS \
    --enable-logging \
    --logging-sample-rate=1.0 \
    --project="$PROJECT_ID" || echo "Backend service already exists"

# Configure CDN policy
echo "Configuring CDN policy..."
gcloud compute backend-services update sentinelops-backend-${ENVIRONMENT} \
    --global \
    --cache-key-policy-include-host \
    --cache-key-policy-include-protocol \
    --cache-key-policy-include-query-string \
    --cache-max-ttl=86400 \
    --default-ttl=3600 \
    --project="$PROJECT_ID"

# Create URL map
echo "Creating URL map..."
cat > /tmp/url-map-config.yaml <<EOF
name: sentinelops-url-map-${ENVIRONMENT}
defaultService: global/backendServices/sentinelops-backend-${ENVIRONMENT}
hostRules:
- hosts:
  - "$DOMAIN"
  pathMatcher: api-paths
pathMatchers:
- name: api-paths
  defaultService: global/backendServices/sentinelops-backend-${ENVIRONMENT}
  pathRules:
  - paths:
    - /api/*
    - /ws/*
    service: global/backendServices/sentinelops-backend-${ENVIRONMENT}
    routeAction:
      corsPolicy:
        allowOrigins: ["https://$DOMAIN"]
        allowMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        allowHeaders: ["Authorization", "Content-Type"]
        exposeHeaders: ["Content-Length", "Content-Type"]
        maxAge: 3600
        allowCredentials: true
EOF

gcloud compute url-maps import sentinelops-url-map-${ENVIRONMENT} \
    --source=/tmp/url-map-config.yaml \
    --global \
    --project="$PROJECT_ID" || echo "URL map already exists"

# Create HTTPS proxy
echo "Creating HTTPS proxy..."
gcloud compute target-https-proxies create sentinelops-https-proxy-${ENVIRONMENT} \
    --ssl-certificates=sentinelops-ssl-cert-${ENVIRONMENT} \
    --url-map=sentinelops-url-map-${ENVIRONMENT} \
    --global \
    --project="$PROJECT_ID" || echo "HTTPS proxy already exists"

# Create forwarding rule
echo "Creating forwarding rule..."
gcloud compute forwarding-rules create sentinelops-forwarding-rule-${ENVIRONMENT} \
    --address=sentinelops-lb-ip-${ENVIRONMENT} \
    --target-https-proxy=sentinelops-https-proxy-${ENVIRONMENT} \
    --ports=443 \
    --global \
    --project="$PROJECT_ID" || echo "Forwarding rule already exists"

# Set up Cloud Armor
echo "Configuring Cloud Armor security policy..."
gcloud compute security-policies create sentinelops-security-policy-${ENVIRONMENT} \
    --description="SentinelOps security policy" \
    --project="$PROJECT_ID" || echo "Security policy already exists"

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
    --security-policy=sentinelops-security-policy-${ENVIRONMENT} \
    --action=rate-based-ban \
    --rate-limit-threshold-count=100 \
    --rate-limit-threshold-interval-sec=60 \
    --ban-duration-sec=600 \
    --conform-action=allow \
    --exceed-action=deny-429 \
    --enforce-on-key=IP \
    --project="$PROJECT_ID" || echo "Rate limiting rule already exists"

# Apply security policy to backend
gcloud compute backend-services update sentinelops-backend-${ENVIRONMENT} \
    --security-policy=sentinelops-security-policy-${ENVIRONMENT} \
    --global \
    --project="$PROJECT_ID"

echo "Load balancing and CDN setup complete!"
echo ""
echo "Next steps:"
echo "1. Update your DNS records to point $DOMAIN to $LB_IP"
echo "2. Wait for SSL certificate to be provisioned (can take up to 60 minutes)"
echo "3. Add backend endpoints to the backend service"
echo ""
echo "To add Cloud Run service as backend:"
echo "gcloud compute network-endpoint-groups create sentinelops-neg-REGION \\"
echo "    --region=REGION \\"
echo "    --network-endpoint-type=serverless \\"
echo "    --cloud-run-service=sentinelops-api"