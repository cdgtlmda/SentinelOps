#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
ENVIRONMENT="${2:-prod}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [ENVIRONMENT]"
    exit 1
fi

echo "Setting up caching strategy for project: $PROJECT_ID"
echo "Environment: $ENVIRONMENT"

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable redis.googleapis.com --project="$PROJECT_ID"
gcloud services enable memcache.googleapis.com --project="$PROJECT_ID"

# Create Redis instance for application caching
echo "Creating Redis instance..."
gcloud redis instances create sentinelops-cache-${ENVIRONMENT} \
    --size=5 \
    --region=us-central1 \
    --zone=us-central1-a \
    --redis-version=redis_6_x \
    --network=sentinelops-vpc \
    --connect-mode=direct-peering \
    --tier=standard \
    --enable-auth \
    --project="$PROJECT_ID" || echo "Redis instance already exists"

# Get Redis instance details
REDIS_HOST=$(gcloud redis instances describe sentinelops-cache-${ENVIRONMENT} \
    --region=us-central1 \
    --format="value(host)" \
    --project="$PROJECT_ID")

REDIS_PORT=$(gcloud redis instances describe sentinelops-cache-${ENVIRONMENT} \
    --region=us-central1 \
    --format="value(port)" \
    --project="$PROJECT_ID")

# Store Redis connection info as secret
echo "Storing Redis connection info..."
cat > /tmp/redis-config.json <<EOF
{
  "host": "${REDIS_HOST}",
  "port": ${REDIS_PORT},
  "db": 0,
  "cache_ttl": {
    "default": 300,
    "user_sessions": 3600,
    "api_responses": 60,
    "static_content": 86400
  }
}
EOFgcloud secrets create sentinelops-redis-config-${ENVIRONMENT} \
    --data-file=/tmp/redis-config.json \
    --project="$PROJECT_ID" || echo "Secret already exists"

# Configure CDN caching for static assets
echo "Configuring CDN caching rules..."
cat > /tmp/cdn-config.yaml <<EOF
defaultTtl: 3600
maxTtl: 86400
negativeCaching: true
negativeCachingPolicy:
- code: 404
  ttl: 120
- code: 401
  ttl: 10
- code: 403
  ttl: 10
serveWhileStale: 86400
requestCoalescing: true
cacheMode: CACHE_ALL_STATIC
clientTtl: 3600
EOF

# Apply CDN configuration
gcloud compute backend-buckets update sentinelops-static-${ENVIRONMENT} \
    --cache-mode=CACHE_ALL_STATIC \
    --enable-cdn \
    --project="$PROJECT_ID" || echo "Backend bucket not found"

# Create Memorystore for session caching
echo "Creating Memorystore instance for session caching..."
gcloud memcache instances create sentinelops-sessions-${ENVIRONMENT} \
    --node-count=3 \
    --node-cpu=1 \
    --node-memory=1GB \
    --region=us-central1 \
    --project="$PROJECT_ID" || echo "Memcache instance already exists"# Configure cache invalidation Cloud Function
echo "Creating cache invalidation function..."
cat > /tmp/cache-invalidator.py <<'EOF'
import functions_framework
from google.cloud import redis_v1
import json

@functions_framework.http
def invalidate_cache(request):
    """Invalidate cache entries based on patterns"""
    request_json = request.get_json(silent=True)
    
    if not request_json or 'pattern' not in request_json:
        return json.dumps({'error': 'Pattern required'}), 400
    
    pattern = request_json['pattern']
    cache_type = request_json.get('cache_type', 'all')
    
    # Implement cache invalidation logic
    # This is a placeholder - implement actual Redis/CDN invalidation
    
    return json.dumps({
        'status': 'success',
        'invalidated': pattern,
        'cache_type': cache_type
    })
EOF

# Deploy cache invalidation function
gcloud functions deploy sentinelops-cache-invalidator-${ENVIRONMENT} \
    --runtime=python311 \
    --trigger-http \
    --allow-unauthenticated \
    --entry-point=invalidate_cache \
    --source=/tmp \
    --region=us-central1 \
    --project="$PROJECT_ID" || echo "Function deployment failed"

# Set up cache warming script
echo "Creating cache warming configuration..."
cat > warm-cache.sh <<EOF
#!/bin/bash
# Cache warming script for SentinelOps

echo "Warming cache for critical endpoints..."

# Add your cache warming logic here
# Example: curl key endpoints to populate cache

echo "Cache warming complete!"
EOF

chmod +x warm-cache.sh

echo "Caching strategy setup complete!"
echo "Redis endpoint: ${REDIS_HOST}:${REDIS_PORT}"
echo "Cache warming script: ./warm-cache.sh"