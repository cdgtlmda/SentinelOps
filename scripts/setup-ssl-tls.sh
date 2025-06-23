#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
DOMAIN="${2:-sentinelops.example.com}"
ENVIRONMENT="${3:-prod}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [DOMAIN] [ENVIRONMENT]"
    exit 1
fi

echo "Setting up SSL/TLS for project: $PROJECT_ID"
echo "Domain: $DOMAIN"
echo "Environment: $ENVIRONMENT"

# Enable required APIs
echo "Enabling Certificate Manager API..."
gcloud services enable certificatemanager.googleapis.com --project="$PROJECT_ID"

# Create managed SSL certificate
echo "Creating managed SSL certificate..."
gcloud certificate-manager certificates create sentinelops-cert-${ENVIRONMENT} \
    --domains="$DOMAIN,www.$DOMAIN,api.$DOMAIN" \
    --project="$PROJECT_ID"

# Create certificate map
echo "Creating certificate map..."
gcloud certificate-manager maps create sentinelops-cert-map-${ENVIRONMENT} \
    --project="$PROJECT_ID"

# Create certificate map entry
echo "Creating certificate map entry..."
gcloud certificate-manager maps entries create sentinelops-cert-entry-${ENVIRONMENT} \
    --map=sentinelops-cert-map-${ENVIRONMENT} \
    --certificates=sentinelops-cert-${ENVIRONMENT} \
    --hostname="$DOMAIN" \
    --project="$PROJECT_ID"# Configure SSL policy
echo "Creating SSL policy..."
gcloud compute ssl-policies create sentinelops-ssl-policy-${ENVIRONMENT} \
    --profile=MODERN \
    --min-tls-version=1.2 \
    --project="$PROJECT_ID"

# Update load balancers with SSL certificate
echo "Updating HTTPS load balancer..."
gcloud compute target-https-proxies update sentinelops-https-proxy-${ENVIRONMENT} \
    --certificate-map=sentinelops-cert-map-${ENVIRONMENT} \
    --ssl-policy=sentinelops-ssl-policy-${ENVIRONMENT} \
    --project="$PROJECT_ID"

# Configure backend service SSL
echo "Configuring backend service SSL..."
gcloud compute backend-services update sentinelops-backend-${ENVIRONMENT} \
    --protocol=HTTPS \
    --port-name=https \
    --project="$PROJECT_ID"

# Set up Cloud Run service with SSL
echo "Configuring Cloud Run SSL endpoints..."
for SERVICE in orchestrator detection analysis remediation communication; do
    echo "Updating $SERVICE service..."
    gcloud run services update sentinelops-${SERVICE}-${ENVIRONMENT} \
        --platform=managed \
        --region=us-central1 \
        --update-env-vars="FORCE_SSL=true" \
        --project="$PROJECT_ID"
done

echo "SSL/TLS setup complete!"
echo "Certificate provisioning may take up to 15 minutes."
echo "Check status: gcloud certificate-manager certificates describe sentinelops-cert-${ENVIRONMENT}"