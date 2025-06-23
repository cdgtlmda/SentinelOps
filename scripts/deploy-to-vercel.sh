#!/bin/bash
set -euo pipefail

PROJECT_NAME="${1:-sentinelops}"
ENVIRONMENT="${2:-production}"
DOMAIN="${3:-}"

echo "Deploying SentinelOps UI to Vercel"
echo "Project: $PROJECT_NAME"
echo "Environment: $ENVIRONMENT"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Navigate to frontend directory
cd frontend

# Create environment file for Vercel
if [ "$ENVIRONMENT" == "production" ]; then
    API_URL="https://sentinelops-api-prod.run.app"
    WS_URL="wss://sentinelops-api-prod.run.app/ws"
else
    API_URL="https://sentinelops-api-${ENVIRONMENT}.run.app"
    WS_URL="wss://sentinelops-api-${ENVIRONMENT}.run.app/ws"
fi

# Build the application
echo "Building application..."
npm install
npm run build

# Deploy to Vercel
echo "Deploying to Vercel..."
if [ "$ENVIRONMENT" == "production" ]; then
    vercel --prod \
        --name="$PROJECT_NAME" \
        --env NEXT_PUBLIC_API_URL="$API_URL" \
        --env NEXT_PUBLIC_WEBSOCKET_URL="$WS_URL" \
        --env NEXT_PUBLIC_ENABLE_WEBSOCKET=true \
        --env NEXT_PUBLIC_ENABLE_OFFLINE_MODE=true \
        --env NEXT_PUBLIC_ENABLE_MESSAGE_QUEUE=true \
        --env NEXT_PUBLIC_ENVIRONMENT="$ENVIRONMENT" \
        --yes
else
    vercel \
        --name="$PROJECT_NAME-$ENVIRONMENT" \
        --env NEXT_PUBLIC_API_URL="$API_URL" \
        --env NEXT_PUBLIC_WEBSOCKET_URL="$WS_URL" \
        --env NEXT_PUBLIC_ENABLE_WEBSOCKET=true \
        --env NEXT_PUBLIC_ENABLE_OFFLINE_MODE=true \
        --env NEXT_PUBLIC_ENABLE_MESSAGE_QUEUE=true \
        --env NEXT_PUBLIC_ENVIRONMENT="$ENVIRONMENT" \
        --yes
fi

# Get deployment URL
DEPLOYMENT_URL=$(vercel ls --json | jq -r '.[0].url')

echo "Deployment complete!"
echo "URL: https://$DEPLOYMENT_URL"

# Configure custom domain if provided
if [ -n "$DOMAIN" ]; then
    echo "Configuring custom domain: $DOMAIN"
    vercel domains add "$DOMAIN" --yes
    vercel alias set "$DEPLOYMENT_URL" "$DOMAIN" --yes
    echo "Custom domain configured: https://$DOMAIN"
fi

# Run post-deployment tests
echo "Running post-deployment tests..."
curl -s -o /dev/null -w "%{http_code}" "https://$DEPLOYMENT_URL" | grep -q "200" && echo "✓ Site is accessible"
curl -s "https://$DEPLOYMENT_URL" | grep -q "SentinelOps" && echo "✓ Content loads correctly"

# Performance check
echo "Running performance check..."
curl -w "@-" -o /dev/null -s "https://$DEPLOYMENT_URL" <<'EOF'
    time_namelookup:  %{time_namelookup}s\n
       time_connect:  %{time_connect}s\n
    time_appconnect:  %{time_appconnect}s\n
   time_pretransfer:  %{time_pretransfer}s\n
      time_redirect:  %{time_redirect}s\n
 time_starttransfer:  %{time_starttransfer}s\n
                    ----------\n
         time_total:  %{time_total}s\n
EOF

echo "Deployment to Vercel completed successfully!"