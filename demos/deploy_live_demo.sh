#!/bin/bash
# SentinelOps Live Demo Deployment Script
# Sets up complete threat intelligence and live demo system

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"your-gcp-project-id"}
REGION=${GCP_REGION:-"us-central1"}
DEMO_DURATION=${DEMO_DURATION:-"30"}
DEMO_INTENSITY=${DEMO_INTENSITY:-"medium"}

echo "🚀 Deploying SentinelOps Live Demo System"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Demo Duration: ${DEMO_DURATION} minutes"
echo "Demo Intensity: ${DEMO_INTENSITY}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
echo "🔍 Checking required tools..."
MISSING_TOOLS=()

if ! command_exists gcloud; then
    MISSING_TOOLS+=("gcloud")
fi

if ! command_exists bq; then
    MISSING_TOOLS+=("bq")
fi

if ! command_exists gsutil; then
    MISSING_TOOLS+=("gsutil")
fi

if ! command_exists python3; then
    MISSING_TOOLS+=("python3")
fi

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo "❌ Missing required tools: ${MISSING_TOOLS[@]}"
    echo "Please install the missing tools and try again."
    exit 1
fi

echo "✅ All required tools are available"

# Authenticate with GCP
echo ""
echo "🔐 Setting up GCP authentication..."
gcloud auth application-default login --quiet || true
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo ""
echo "⚙️ Enabling required GCP APIs..."
APIs=(
    "bigquery.googleapis.com"
    "firestore.googleapis.com"
    "pubsub.googleapis.com"
    "cloudfunctions.googleapis.com"
    "cloudscheduler.googleapis.com"
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "aiplatform.googleapis.com"
    "logging.googleapis.com"
    "monitoring.googleapis.com"
)

for api in "${APIs[@]}"; do
    echo "  Enabling ${api}..."
    gcloud services enable ${api} --quiet
done

echo "✅ APIs enabled"

# Set up threat intelligence feeds
echo ""
echo "📡 Setting up threat intelligence feeds..."
chmod +x ./scripts/threat_intel/setup_threat_feeds.sh
./scripts/threat_intel/setup_threat_feeds.sh

echo ""
echo "🔄 Ingesting initial threat intelligence data..."
chmod +x ./scripts/threat_intel/ingest_threat_feeds.sh
./scripts/threat_intel/ingest_threat_feeds.sh

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet
else
    echo "⚠️ requirements.txt not found, skipping Python dependency installation"
fi

# Set up Firestore
echo ""
echo "🗄️ Setting up Firestore database..."
gcloud firestore databases create --location=${REGION} --quiet || echo "Firestore database already exists"

# Create Firestore collections and indexes
echo "📊 Creating Firestore collections..."
python3 -c "
from src.common.storage import get_firestore_client
import logging

logging.basicConfig(level=logging.INFO)
client = get_firestore_client()

# Create initial collections with sample documents
collections = [
    'demo_incidents',
    'demo_analyses', 
    'demo_detections',
    'demo_metrics',
    'demo_noise_events',
    'live_demo_sessions',
    'threat_analyses'
]

for collection_name in collections:
    try:
        # Create collection with a placeholder document
        doc_ref = client.collection(collection_name).document('_placeholder')
        doc_ref.set({
            'created_at': client.SERVER_TIMESTAMP,
            'type': 'initialization_placeholder'
        })
        print(f'✅ Created collection: {collection_name}')
    except Exception as e:
        print(f'⚠️ Collection {collection_name}: {e}')

print('🗄️ Firestore collections initialized')
"

# Deploy Cloud Function for threat simulation
echo ""
echo "☁️ Deploying threat simulation Cloud Function..."
cd functions/threat_simulation_scheduler

gcloud functions deploy threat-simulation-scheduler \
    --runtime python311 \
    --trigger-http \
    --allow-unauthenticated \
    --entry-point simulate_threats \
    --memory 512MB \
    --timeout 300s \
    --set-env-vars GCP_PROJECT_ID=${PROJECT_ID},THREAT_EVENTS_TOPIC=threat-events \
    --region ${REGION} \
    --quiet

cd ../..

# Set up Pub/Sub topic for threat events
echo ""
echo "📮 Setting up Pub/Sub topic..."
gcloud pubsub topics create threat-events --quiet || echo "Topic already exists"
gcloud pubsub subscriptions create threat-events-sub --topic=threat-events --quiet || echo "Subscription already exists"

# Set up Cloud Scheduler for automated threat simulation
echo ""
echo "⏰ Setting up Cloud Scheduler..."
FUNCTION_URL="https://${REGION}-${PROJECT_ID}.cloudfunctions.net/threat-simulation-scheduler"

gcloud scheduler jobs create http threat-simulation-job \
    --location=${REGION} \
    --schedule="*/5 * * * *" \
    --uri="${FUNCTION_URL}" \
    --http-method=POST \
    --message-body='{"intensity":"medium","count":3}' \
    --quiet || echo "Scheduler job already exists"

# Test threat simulator
echo ""
echo "🧪 Testing threat simulator..."
python3 -c "
from src.tools.threat_simulator import ThreatSimulator
import json

print('Testing threat simulator...')
simulator = ThreatSimulator()

# Test basic functionality
stats = simulator.get_scenario_stats()
print(f'📊 Available scenarios: {stats[\"total_scenarios\"]}')

# Generate test scenario
scenario = simulator.generate_scenario(severity='CRITICAL')
print(f'🎯 Test scenario: {scenario[\"event_type\"]}')

print('✅ Threat simulator working correctly')
"

# Test Gemini integration (if credentials available)
echo ""
echo "🧠 Testing Gemini integration..."
python3 -c "
try:
    from src.integrations.gemini_threat_analyst import create_threat_analyst
    from src.tools.threat_simulator import ThreatSimulator
    
    print('Testing Gemini threat analyst...')
    
    # Generate a test scenario
    simulator = ThreatSimulator()
    scenario = simulator.generate_scenario(severity='MEDIUM')
    
    # Test analysis (with timeout)
    analyst = create_threat_analyst()
    result = analyst.analyze_security_event(
        event_data=scenario,
        context={'demo_mode': True}
    )
    
    print(f'🧠 Analysis completed: {result.incident_id}')
    print(f'📊 Confidence: {result.confidence:.2f}')
    print(f'🎯 Severity: {result.severity}')
    
    analyst.close()
    print('✅ Gemini integration working correctly')
    
except Exception as e:
    print(f'⚠️ Gemini integration test failed: {e}')
    print('This is expected if Vertex AI credentials are not configured')
"

# Create demo startup script
echo ""
echo "📝 Creating demo startup script..."
cat > start_live_demo.sh << EOF
#!/bin/bash
# SentinelOps Live Demo Startup Script

echo "🚀 Starting SentinelOps Live Demo"
echo "Duration: ${DEMO_DURATION} minutes"
echo "Intensity: ${DEMO_INTENSITY}"
echo ""

# Start the live demo orchestrator
python3 -c "
import asyncio
from src.tools.live_demo_orchestrator import run_live_demo

async def main():
    result = await run_live_demo(
        project_id='${PROJECT_ID}',
        duration_minutes=${DEMO_DURATION},
        intensity='${DEMO_INTENSITY}',
        threat_intel_enabled=True
    )
    
    print('📊 Demo Results:')
    print(f'Status: {result[\"status\"]}')
    if 'demo_summary' in result:
        stats = result['demo_summary']['demo_stats']
        print(f'Scenarios generated: {stats[\"scenarios_generated\"]}')
        print(f'Incidents analyzed: {stats[\"incidents_analyzed\"]}')
        print(f'Threats detected: {stats[\"threats_detected\"]}')
        print(f'Critical incidents: {stats[\"critical_incidents\"]}')

if __name__ == '__main__':
    asyncio.run(main())
"
EOF

chmod +x start_live_demo.sh

# Create API server startup script
echo ""
echo "🌐 Creating API server startup script..."
cat > start_api_server.sh << EOF
#!/bin/bash
# SentinelOps API Server Startup Script

echo "🌐 Starting SentinelOps API Server"
echo "Available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""

# Set environment variables
export GCP_PROJECT_ID=${PROJECT_ID}
export ENVIRONMENT=development

# Start the FastAPI server
python3 -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
EOF

chmod +x start_api_server.sh

# Show available BigQuery queries
echo ""
echo "📊 BigQuery threat intelligence tables available:"
bq ls threat_intel

echo ""
echo "🎯 Sample threat intelligence query:"
echo "bq query --use_legacy_sql=false \"
SELECT 
  indicator,
  indicator_type,
  severity,
  source,
  confidence
FROM \`${PROJECT_ID}.threat_intel.threat_indicators\`
ORDER BY confidence DESC
LIMIT 10
\""

echo ""
echo "✅ SentinelOps Live Demo System Deployed Successfully!"
echo ""
echo "🎮 Available Commands:"
echo "  ./start_live_demo.sh          - Run live demo orchestrator"
echo "  ./start_api_server.sh         - Start API server"
echo "  ./demo_threat_simulation.py   - Run interactive demo"
echo ""
echo "🌐 API Endpoints:"
echo "  POST /api/v1/demo/start       - Start live demo"
echo "  GET  /api/v1/demo/metrics     - Get live metrics"
echo "  GET  /api/v1/demo/incidents   - Get recent incidents"
echo "  POST /api/v1/threats/analyze  - Analyze threat events"
echo ""
echo "📊 Cloud Resources:"
echo "  BigQuery dataset: ${PROJECT_ID}.threat_intel"
echo "  Firestore collections: demo_incidents, demo_analyses, etc."
echo "  Cloud Function: threat-simulation-scheduler"
echo "  Cloud Scheduler: threat-simulation-job (runs every 5 minutes)"
echo ""
echo "🎯 Ready for live demonstration!"
echo ""
echo "💡 Quick Start:"
echo "  1. ./start_api_server.sh &"
echo "  2. Open http://localhost:8000/docs"
echo "  3. POST to /api/v1/demo/start with intensity='high'"
echo "  4. Monitor live metrics at /api/v1/demo/metrics"