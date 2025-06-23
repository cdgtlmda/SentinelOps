# SentinelOps Quick Start Guide

Get SentinelOps up and running in your environment in just 5 minutes! This guide walks you through a local deployment and your first incident simulation.

## 🚨 **Important: Credentials Setup Required**

This repository does **NOT** include any service account keys or credentials. You must:

1. **Create your own GCP service account**:
   ```bash
   gcloud iam service-accounts create sentinelops-sa \
     --display-name="SentinelOps Service Account"

   gcloud iam service-accounts keys create service-account-key.json \
     --iam-account=sentinelops-sa@your-gcp-project-id.iam.gserviceaccount.com
   ```

2. **Replace ALL placeholder values** in configuration files:
   - `your-gcp-project-id` → Your actual GCP project ID
   - `/path/to/service-account-key.json` → Path to your downloaded key
   - `your-admin-password` → Your chosen secure password

## Prerequisites

Before starting, ensure you have:
- Python 3.12+ installed
- Google Cloud SDK (`gcloud`) installed and configured
- Node.js 18+ or Bun (for web interface)
- A GCP project with billing enabled
- Git installed

## UI Directory Structure

> **Important:** SentinelOps now uses a modern monorepo structure:
> - `/frontend/sentinelops-ui` - Production monorepo with multiple applications
>   - `/apps/app` - Main SentinelOps security interface (port 3000)
>   - `/apps/web` - Marketing and documentation site (port 3001)
>   - `/apps/api` - Backend integration layer
> - `/frontend` (excluding sentinelops-ui) - Legacy interface (deprecated, maintained for compatibility)
>
> All new development and deployments should use the `/frontend/sentinelops-ui` monorepo.

## 5-Minute Setup

> **💡 Recommended: One-Command Setup**
> Use `./build_and_run.sh` which handles everything automatically and starts both APIs needed for the production web interface.
> Or follow the manual steps below for development/learning purposes.

### Quick Start (Recommended)

```bash
# Clone repository
git clone https://github.com/cdgtlmda/SentinelOps.git
cd SentinelOps

# One-command setup and launch
./build_and_run.sh
```

This will:
- ✅ Install all dependencies (Python + Node.js/Bun)
- ✅ Set up GCP authentication
- ✅ Enable required APIs
- ✅ Start API server (port 8000) with threat simulator
- ✅ Launch production web interface (port 3000) with live dashboard

**Access URLs:**
- Main Application: http://localhost:3000
- Marketing Site: http://localhost:3001
- Threat Simulator: http://localhost:3000/threats
- API Health: http://localhost:8000/health
- API Docs: http://localhost:8000/docs

### Manual Setup (For Development)

### Step 1: Clone and Install (1 minute)

```bash
# Clone the repository
git clone https://github.com/cdgtlmda/SentinelOps.git
cd SentinelOps

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install ADK and dependencies
pip install google-adk>=1.2.0
pip install -r requirements.txt
```

### Step 2: Configure GCP (2 minutes)

```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Set your project (replace with your project ID)
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
gcloud config set project $GOOGLE_CLOUD_PROJECT

# Enable required APIs
gcloud services enable firestore.googleapis.com \
  cloudfunctions.googleapis.com \
  logging.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com
```

### Step 3: Start Backend Services (1 minute)

```bash
# Start the API server with threat simulation
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Launch Web Interface (1 minute)

```bash
# Navigate to the new monorepo
cd frontend/sentinelops-ui

# Install dependencies (choose one)
bun install    # Recommended
# OR
npm install

# Start all applications
bun dev        # Starts main app on port 3000, web on port 3001
# OR start individual apps
bun dev:app    # ✅ Starts main interface on port 3000
bun dev:web    # ✅ Starts marketing site on port 3001
```

## First Test (30 seconds)

Once everything is running:

1. **Open Dashboard**: http://localhost:3000
2. **Generate Test Incident**: Click "Simulate Threat" button
3. **Watch Live Updates**: See real-time security monitoring
4. **Check API Status**: http://localhost:8000/health

## What's Running

After setup, you'll have:

- ✅ **Backend API** (port 8000) - Core SentinelOps engine
- ✅ **Main Interface** (port 3000) - Security dashboard and management
- ✅ **Marketing Site** (port 3001) - Documentation and info
- ✅ **Real-time Data** - Live incident updates and agent status
- ✅ **Threat Simulator** - Interactive security scenario testing

## Next Steps

- 📖 **Learn**: Read [Architecture Overview](../02-architecture/architecture.md)
- 🔧 **Configure**: Customize [Agent Settings](../03-deployment/configuration/)
- 🚀 **Deploy**: Follow [GCP Deployment Guide](../03-deployment/gcp-deployment-comprehensive.md)
- 🎯 **Test**: Try [Threat Scenarios](../07-demos/THREAT_SIMULATION_SYSTEM.md)

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in package.json files or environment variables
2. **GCP authentication**: Run `gcloud auth application-default login`
3. **Dependencies**: Make sure you have Python 3.12+ and Node.js 18+/Bun installed
4. **Firewall**: Ensure ports 3000, 3001, and 8000 are accessible

### Get Help

- 📚 [Troubleshooting Guide](../04-operations/adk-troubleshooting.md)
- 🐛 [GitHub Issues](https://github.com/cdgtlmda/SentinelOps/issues)
- 📖 [Documentation](../README.md)

---

**🎉 Congratulations!** You now have SentinelOps running with real-time security monitoring, threat simulation, and a modern web interface.
