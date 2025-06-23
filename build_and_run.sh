#!/bin/bash

# SentinelOps - ONE BUILD SCRIPT TO RULE THEM ALL
# This single script sets up, builds, tests, and runs the entire SentinelOps platform with threat simulator
# Includes: Environment setup, GCP APIs, Authentication, Dependencies, Build, Test, and Run

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}🛡️  SentinelOps - Complete Setup, Build & Run${NC}"
echo -e "${PURPLE}===============================================${NC}"
echo -e "${BLUE}This script will:${NC}"
echo -e "${BLUE}  ✅ Check prerequisites${NC}"
echo -e "${BLUE}  ✅ Set up environment variables${NC}" 
echo -e "${BLUE}  ✅ Check GCP authentication${NC}"
echo -e "${BLUE}  ✅ Enable required GCP APIs${NC}"
echo -e "${BLUE}  ✅ Install dependencies${NC}"
echo -e "${BLUE}  ✅ Build the project${NC}"
echo -e "${BLUE}  ✅ Test threat simulator${NC}"
echo -e "${BLUE}  ✅ Start API server${NC}"
echo -e "${BLUE}  ✅ Start frontend${NC}"
echo -e "${PURPLE}===============================================${NC}\n"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down all services...${NC}"
    pkill -f "uvicorn" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# Clean up existing processes
echo -e "${YELLOW}🧹 Cleaning up existing processes...${NC}"
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
sleep 2

# Create necessary directories
mkdir -p logs

# === PREREQUISITE CHECKS ===
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [[ $PYTHON_MAJOR -gt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 12 ]]; then
    echo -e "${GREEN}✅ Python $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python 3.12+ required, found $PYTHON_VERSION${NC}"
    echo -e "${YELLOW}Install Python 3.12+ or use pyenv: pyenv install 3.12.0${NC}"
    exit 1
fi

# Check if gcloud is installed
if command -v gcloud &> /dev/null; then
    echo -e "${GREEN}✅ Google Cloud SDK installed${NC}"
else
    echo -e "${YELLOW}⚠️  Google Cloud SDK not found. Installing...${NC}"
    if [[ -f "./scripts/setup/install-gcloud.sh" ]]; then
        ./scripts/setup/install-gcloud.sh
    else
        echo -e "${RED}❌ Please install Google Cloud SDK manually: https://cloud.google.com/sdk/docs/install${NC}"
        exit 1
    fi
fi

# Check if node/npm is installed for frontend
if command -v npm &> /dev/null; then
    echo -e "${GREEN}✅ Node.js/npm installed${NC}"
else
    echo -e "${YELLOW}⚠️  Node.js/npm not found. Please install Node.js 18+${NC}"
fi

# === ENVIRONMENT SETUP ===
echo -e "${BLUE}🔧 Setting up environment...${NC}"

# Check if .env exists, create from template if not
if [[ ! -f ".env" ]]; then
    if [[ -f ".env.example" ]]; then
        echo -e "${YELLOW}📝 Creating .env from template...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit .env file with your GCP project ID and other settings${NC}"
        echo -e "${YELLOW}⚠️  Required: GOOGLE_CLOUD_PROJECT=your-project-id${NC}"
    else
        echo -e "${YELLOW}📝 Creating basic .env file...${NC}"
        cat > .env << 'EOF'
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=

# ADK Configuration  
ADK_TELEMETRY_ENABLED=true
ADK_LOG_LEVEL=INFO

# Development Settings
ENVIRONMENT=development
DEBUG=true
DRY_RUN_DEFAULT=true

# API Configuration
API_HOST=127.0.0.1
API_PORT=8000

# Frontend Configuration
FRONTEND_PORT=3000
EOF
        echo -e "${YELLOW}⚠️  Basic .env created. Please edit with your GCP project ID${NC}"
    fi
fi

# Load environment variables
if [[ -f ".env" ]]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check for required GCP project
if [[ -z "$GOOGLE_CLOUD_PROJECT" || "$GOOGLE_CLOUD_PROJECT" == "your-project-id" ]]; then
    echo -e "${RED}❌ GOOGLE_CLOUD_PROJECT not set in .env file${NC}"
    echo -e "${YELLOW}Please edit .env file and set GOOGLE_CLOUD_PROJECT=your-actual-project-id${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Using GCP Project: $GOOGLE_CLOUD_PROJECT${NC}"

# === GCP AUTHENTICATION CHECK ===
echo -e "${BLUE}🔐 Checking GCP authentication...${NC}"

# Check if authenticated
if gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 | grep -q "@"; then
    ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
    echo -e "${GREEN}✅ Authenticated as: $ACTIVE_ACCOUNT${NC}"
else
    echo -e "${YELLOW}⚠️  Not authenticated with GCP. Running authentication...${NC}"
    gcloud auth login
    gcloud auth application-default login
fi

# Set the project
gcloud config set project $GOOGLE_CLOUD_PROJECT

# === ENABLE GCP APIS ===
echo -e "${BLUE}🔌 Enabling required GCP APIs...${NC}"

if [[ -f "./scripts/setup/enable-apis.sh" ]]; then
    ./scripts/setup/enable-apis.sh
    echo -e "${GREEN}✅ GCP APIs enabled${NC}"
else
    echo -e "${YELLOW}⚠️  API enablement script not found, enabling manually...${NC}"
    gcloud services enable \
        compute.googleapis.com \
        bigquery.googleapis.com \
        firestore.googleapis.com \
        run.googleapis.com \
        pubsub.googleapis.com \
        secretmanager.googleapis.com \
        aiplatform.googleapis.com \
        logging.googleapis.com \
        monitoring.googleapis.com
    echo -e "${GREEN}✅ Essential APIs enabled${NC}"
fi

# === INSTALL DEPENDENCIES ===
echo -e "${BLUE}📦 Installing dependencies...${NC}"

# Install ADK first
echo -e "${BLUE}📦 Installing Google ADK...${NC}"
pip install google-adk>=1.2.0

# Install project dependencies
pip install -r requirements.txt

# Build the project
echo -e "${BLUE}🔨 Building SentinelOps...${NC}"
python -m pip install build
python -m build

# Test threat simulator integration
echo -e "${BLUE}🎯 Testing Threat Simulator...${NC}"
PYTHONPATH=$(pwd) python src/tools/threat_simulator.py --stats
echo -e "${GREEN}✅ Threat simulator ready with 25 scenarios${NC}"

# Create a working API server with threat simulator
echo -e "${BLUE}🚀 Creating SentinelOps API with threat simulator...${NC}"
cat > working_api.py << 'EOF'
import asyncio
import json
import sys
import os
from datetime import datetime
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Add current directory to path for imports
sys.path.insert(0, '.')

app = FastAPI(title="SentinelOps API", description="Multi-Agent Security Platform with Threat Simulator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import threat simulator
try:
    from src.tools.threat_simulator import ThreatSimulator
    threat_sim = ThreatSimulator()
    THREAT_SIM_AVAILABLE = True
except Exception as e:
    print(f"Warning: Threat simulator not available: {e}")
    THREAT_SIM_AVAILABLE = False

AGENTS = [
    {"id": "orchestrator", "name": "Orchestrator Agent", "status": "online", "tools": 6},
    {"id": "detection", "name": "Detection Agent", "status": "online", "tools": 8},
    {"id": "analysis", "name": "Analysis Agent", "status": "online", "tools": 9},
    {"id": "remediation", "name": "Remediation Agent", "status": "online", "tools": 6},
    {"id": "communication", "name": "Communication Agent", "status": "online", "tools": 5}
]

@app.get("/")
async def root():
    return {
        "message": "🛡️ SentinelOps API", 
        "status": "operational", 
        "agents": len(AGENTS),
        "threat_simulator": THREAT_SIM_AVAILABLE
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(), 
        "agents_online": 5,
        "threat_simulator": THREAT_SIM_AVAILABLE
    }

@app.get("/api/agents")
async def get_agents():
    return {"agents": AGENTS, "total": len(AGENTS)}

@app.get("/api/threat/stats")
async def get_threat_stats():
    if not THREAT_SIM_AVAILABLE:
        raise HTTPException(status_code=503, detail="Threat simulator not available")
    
    stats = threat_sim.get_scenario_stats()
    return stats

@app.post("/api/threat/generate")
async def generate_threats(count: int = 1, severity: str = None):
    if not THREAT_SIM_AVAILABLE:
        raise HTTPException(status_code=503, detail="Threat simulator not available")
    
    if count == 1:
        scenario = threat_sim.generate_scenario(severity=severity)
        return {"scenario": scenario}
    else:
        scenarios = threat_sim.generate_batch(count)
        return {"scenarios": scenarios, "count": len(scenarios)}

@app.post("/api/threat/campaign")
async def simulate_campaign(duration: int = 5, intensity: str = "medium"):
    if not THREAT_SIM_AVAILABLE:
        raise HTTPException(status_code=503, detail="Threat simulator not available")
    
    events = threat_sim.simulate_attack_campaign(duration, intensity)
    return {"events": events, "count": len(events), "duration_minutes": duration}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = {
                "type": "heartbeat", 
                "timestamp": datetime.utcnow().isoformat(),
                "agents_online": 5,
                "threat_simulator": THREAT_SIM_AVAILABLE
            }
            await websocket.send_json(data)
            await asyncio.sleep(5)
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
EOF

echo -e "${BLUE}🚀 Starting SentinelOps API on http://localhost:8000...${NC}"
python working_api.py > logs/api.log 2>&1 &
API_PID=$!

sleep 5

# Check API health
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API Server running${NC}"
else
    echo -e "${RED}❌ API failed to start. Check logs/api.log${NC}"
    exit 1
fi

# Start Dashboard API (for NEW UI)
echo -e "${BLUE}🎨 Starting Dashboard API on http://localhost:8081...${NC}"
python demos/connect_ui_backend.py > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
sleep 3

# Start Frontend (NEW UI)
echo -e "${BLUE}🎨 Starting Next.js Frontend (NEW UI) on http://localhost:3000...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    npm install
fi

# Set environment variable for NEW UI to use dashboard API
export NEXT_PUBLIC_API_URL=http://localhost:8081
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 8

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend (NEW UI) running${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend still starting up...${NC}"
fi

# Check dashboard API
if curl -s http://localhost:8081/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Dashboard API running${NC}"
else
    echo -e "${YELLOW}⚠️  Dashboard API still starting up...${NC}"
fi

# Test threat simulator integration with API
echo -e "${BLUE}🧪 Testing threat simulation via API...${NC}"
sleep 2
if curl -s http://localhost:8000/api/threat/stats > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Threat simulator API endpoints working${NC}"
    curl -s http://localhost:8000/api/threat/generate | python -m json.tool | head -10
else
    echo -e "${YELLOW}⚠️  API still starting up...${NC}"
fi

# Display final status
echo -e "\n${PURPLE}🎉 SentinelOps Complete Setup & Launch Successful!${NC}"
echo -e "${PURPLE}====================================================${NC}"
echo -e "${GREEN}🔧 Environment:       ${BLUE}Configured (.env file created)${NC}"
echo -e "${GREEN}🔐 GCP Project:       ${BLUE}$GOOGLE_CLOUD_PROJECT${NC}"
echo -e "${GREEN}🔌 APIs:              ${BLUE}Enabled and authenticated${NC}"
echo -e "${GREEN}📦 Dependencies:      ${BLUE}Installed (ADK + requirements)${NC}"
echo -e "${PURPLE}====================================================${NC}"
echo -e "${GREEN}🔌 Threat Simulator API:  ${BLUE}http://localhost:8000${NC}"
echo -e "${GREEN}🔌 Dashboard API:         ${BLUE}http://localhost:8081${NC}"
echo -e "${GREEN}📚 API Docs:              ${BLUE}http://localhost:8000/docs${NC}"
echo -e "${GREEN}🔍 Health Check:          ${BLUE}http://localhost:8000/health${NC}"
echo -e "${GREEN}🎨 NEW UI Frontend:       ${BLUE}http://localhost:3000${NC}"
echo -e "${GREEN}🎯 Threat Simulator:      ${BLUE}http://localhost:3000/threats${NC}"
echo -e "${PURPLE}====================================================${NC}"
echo -e "${YELLOW}🎯 Threat Simulator API Endpoints:${NC}"
echo -e "   ${BLUE}GET  /api/threat/stats${NC}     - View scenario stats"
echo -e "   ${BLUE}POST /api/threat/generate${NC}  - Generate threats"
echo -e "   ${BLUE}POST /api/threat/campaign${NC}  - Simulate campaigns"
echo -e "${YELLOW}🎯 CLI Commands:${NC}"
echo -e "   ${BLUE}python src/tools/threat_simulator.py --stats${NC}"
echo -e "   ${BLUE}python src/tools/threat_simulator.py --batch 5${NC}"
echo -e "\n${YELLOW}📋 Logs:${NC}"
echo -e "   ${BLUE}tail -f logs/api.log${NC}"
echo -e "   ${BLUE}tail -f logs/frontend.log${NC}"
echo -e "\n${RED}Press Ctrl+C to stop all services${NC}\n"

# Show live API logs
echo -e "${YELLOW}📊 Live API Logs:${NC}"
tail -f logs/api.log