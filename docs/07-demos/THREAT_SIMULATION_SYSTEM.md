# SentinelOps Threat Simulation System

## 🎯 Overview

A comprehensive threat simulation and analysis system that showcases SentinelOps capabilities in a production environment. The system mimics threats of various priority levels and provides AI-powered analysis with expert-level insights.

## 🏗️ System Components

### 1. Threat Scenario Library (`config/threat_scenarios.yaml`)
- **25 ready-made scenarios** balanced across LOW/MEDIUM/CRITICAL severities
- **Realistic threat templates** with MITRE ATT&CK mapping
- **Dynamic value generation** for IPs, domains, file counts, etc.
- **Production-ready categorization** with business context

#### Scenario Distribution:
- **LOW (8 scenarios)**: Hygiene/nuisance issues (bucket exposure, weak TLS, unused keys)
- **MEDIUM (9 scenarios)**: Suspicious activity (geo-anomalous logins, port scans, privilege escalation)
- **CRITICAL (8 scenarios)**: Active exploitation (brute force, ransomware, data exfiltration)

### 2. Threat Simulator (`src/tools/threat_simulator.py`)
- **Batch generation** with customizable severity distribution
- **Attack campaign simulation** with temporal progression and escalation
- **CLI interface** for testing and automation
- **Template-based** generation with realistic randomization

### 3. Gemini Threat Analyst (`src/integrations/gemini_threat_analyst.py`)
- **Tier-3 SOC expertise** via optimized prompts
- **Few-shot learning** with security incident examples
- **MITRE ATT&CK integration** with technique IDs
- **Structured JSON output** with confidence scoring
- **Slack-ready formatting** for instant notifications

### 4. Production APIs (`src/api/routes/threat_simulation.py`)
- **RESTful endpoints** for all simulation and analysis functions
- **FastAPI integration** with Pydantic validation
- **Firestore storage** for incident tracking
- **Batch processing** for correlated attacks

### 5. Cloud Function Scheduler (`functions/threat_simulation_scheduler/`)
- **Automated threat generation** via Cloud Scheduler
- **Pub/Sub integration** for event streaming
- **Time-aware simulation** (more threats during business hours)
- **Statistics tracking** in Firestore

### 6. Frontend Components (`frontend/components/threats/`)
- **Threat analysis drawer** with rich incident details
- **MITRE ATT&CK visualization** with clickable technique links
- **Slack notification preview** with copy-to-clipboard
- **Confidence indicators** and remediation steps

## 🚀 API Endpoints

```
GET  /api/v1/threats/scenarios                 # List available scenarios
POST /api/v1/threats/scenarios/generate        # Generate single scenario
POST /api/v1/threats/scenarios/batch           # Generate batch scenarios
POST /api/v1/threats/campaigns/simulate        # Simulate attack campaign
POST /api/v1/threats/analyze                   # Analyze threat with Gemini
POST /api/v1/threats/analyze/batch             # Batch threat analysis
GET  /api/v1/threats/analysis/{id}             # Retrieve analysis
GET  /api/v1/threats/analysis                  # List analyses (with filters)
GET  /api/v1/threats/stats                     # System statistics
```

## 📊 Demonstration Scenarios

### Scenario 1: Single Threat Analysis
```bash
# Generate a critical threat
curl -X POST "http://localhost:8000/api/v1/threats/scenarios/generate" \
  -H "Content-Type: application/json" \
  -d '{"severity": "CRITICAL"}'

# Analyze with Gemini
curl -X POST "http://localhost:8000/api/v1/threats/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "event_data": {
      "event_type": "SSH_BRUTE_FORCE",
      "actor_ip": "203.0.113.45",
      "target_vm": "web-1",
      "match_count": 156
    }
  }'
```

### Scenario 2: Attack Campaign Simulation
```bash
# Simulate 30-minute high-intensity campaign
curl -X POST "http://localhost:8000/api/v1/threats/campaigns/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "duration_minutes": 30,
    "intensity": "high"
  }'
```

### Scenario 3: Coordinated Multi-Stage Attack
```bash
# Analyze correlated events as single incident
curl -X POST "http://localhost:8000/api/v1/threats/analyze/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {"event_type": "PORT_SCAN", "actor_ip": "198.51.100.1"},
      {"event_type": "SUSPICIOUS_LOGIN", "actor_ip": "198.51.100.1"},
      {"event_type": "SSH_BRUTE_FORCE", "actor_ip": "198.51.100.1"},
      {"event_type": "LATERAL_MOVEMENT", "source_vm": "web-1"},
      {"event_type": "DB_BULK_DUMP", "db_instance": "orders-prod"}
    ],
    "correlation_context": "APT campaign: reconnaissance → access → persistence → lateral movement → exfiltration"
  }'
```

## 🎭 Demo Script Usage

Run the comprehensive demonstration:

```bash
python demo_threat_simulation.py
```

The demo showcases:
1. **Scenario Library Statistics** - 25 scenarios across categories
2. **Batch Generation** - Balanced threat distribution
3. **Attack Campaign** - 30-minute high-intensity simulation
4. **Gemini Analysis** - AI-powered threat assessment
5. **Batch Analysis** - Correlated incident processing
6. **Storage Integration** - Firestore persistence
7. **Performance Metrics** - Speed and cost analysis

## 🔥 Key Features

### Advanced Threat Simulation
- **Realistic attack patterns** with proper MITRE mapping
- **Temporal correlation** in campaign simulations
- **Escalation modeling** (LOW → MEDIUM → CRITICAL)
- **Business context awareness** for impact assessment

### Expert-Level AI Analysis
- **Tier-3 SOC prompting** with security expertise
- **MITRE ATT&CK integration** for technique identification
- **Confidence scoring** with uncertainty quantification
- **Actionable remediation** with prioritized steps

### Production-Ready Architecture
- **FastAPI endpoints** with full OpenAPI documentation
- **Firestore integration** for incident persistence
- **Pub/Sub streaming** for real-time processing
- **Cloud Function automation** with intelligent scheduling

### Rich Frontend Experience
- **Interactive analysis drawer** with detailed breakdowns
- **MITRE technique links** to official documentation
- **Slack-ready formatting** for instant communication
- **Copy-to-clipboard** for IOCs and remediation steps

## 💰 Cost Analysis

### Gemini Analysis Costs
- **Single event analysis**: ~$0.001-0.003 per incident
- **Batch analysis**: ~$0.005-0.015 per batch (5 events)
- **Daily simulation**: ~$1-5 for continuous operation
- **Monthly budget**: ~$30-150 for production workload

### Performance Metrics
- **Scenario generation**: <100ms per scenario
- **Gemini analysis**: 2-5 seconds per event
- **Batch processing**: 8-15 seconds for 5 events
- **Storage latency**: <200ms Firestore writes

## 🎯 Production Deployment

### Cloud Function Deployment
```bash
gcloud functions deploy threat-simulation-scheduler \
  --runtime python311 \
  --trigger-http \
  --entry-point simulate_threats \
  --memory 512MB \
  --timeout 300s \
  --env-vars-file env.yaml
```

### Scheduled Automation
```bash
gcloud scheduler jobs create http threat-simulation-job \
  --schedule="0 */4 * * *" \
  --uri="https://us-central1-PROJECT.cloudfunctions.net/threat-simulation-scheduler" \
  --http-method=POST \
  --message-body='{"intensity":"medium","count":5}'
```

### API Server Deployment
```bash
docker build -t sentinelops-api .
docker run -p 8000:8000 -e GCP_PROJECT_ID=your-project sentinelops-api
```

## 🎪 Live Demo Flow

1. **System Overview** (2 min)
   - Show 25 scenarios in YAML configuration
   - Demonstrate CLI scenario generation
   - Display API endpoint documentation

2. **Threat Generation** (3 min)
   - Generate single critical scenario
   - Create batch with custom distribution
   - Simulate 10-minute attack campaign

3. **AI Analysis** (5 min)
   - Analyze SSH brute force attack
   - Show MITRE ATT&CK mapping
   - Display confidence scoring and remediation

4. **Batch Processing** (3 min)
   - Submit correlated multi-stage attack
   - Show incident relationship analysis
   - Export Slack-ready notifications

5. **Storage & Retrieval** (2 min)
   - Query Firestore for recent analyses
   - Show analysis filtering and search
   - Display real-time statistics

6. **Production Integration** (3 min)
   - Demonstrate Cloud Function automation
   - Show Pub/Sub event streaming
   - Review cost and performance metrics

**Total Demo Time**: 18 minutes + Q&A

## 🏆 Business Value

### For Security Teams
- **Realistic testing** of detection rules and playbooks
- **Training scenarios** for SOC analysts and incident responders
- **Red team exercises** with predictable, documented threats
- **Compliance demonstrations** with audit-ready documentation

### For Management
- **ROI measurement** with quantified threat response capabilities
- **Risk visualization** with business impact assessments
- **Cost optimization** through AI-assisted analysis automation
- **Competitive advantage** via advanced threat intelligence

### For Technical Teams
- **API-first design** enabling custom integrations
- **Open-source components** for transparency and customization
- **Cloud-native architecture** with auto-scaling and resilience
- **Production monitoring** with comprehensive observability

---

🚀 **Ready for immediate deployment and live demonstration!**