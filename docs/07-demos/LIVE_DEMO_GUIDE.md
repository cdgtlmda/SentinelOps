# SentinelOps Live Demo System 🚀

## Overview

A fully automated, production-ready threat simulation and analysis system that showcases SentinelOps operating in real-time with **genuine threat intelligence feeds** and **AI-powered analysis**. Perfect for live demonstrations, hackathons, and security training.

## 🎯 What Makes This Demo Special

### Real Threat Intelligence Integration
- **CISA Known Exploited Vulnerabilities** - Live CVE data with exploitation status
- **AbuseIPDB Blacklist** - Community-reported malicious IPs  
- **FireHOL IP Lists** - High-confidence threat reputation data
- **MITRE ATT&CK Framework** - Complete technique and tactic mappings
- **Spamhaus DROP Lists** - Botnet and spam IP ranges

### Live Rotating Threat Scenarios
- **25 realistic scenarios** across LOW/MEDIUM/CRITICAL severities
- **Temporal progression** - scenarios escalate as demo progresses
- **Attack campaign simulation** - coordinated multi-stage attacks
- **Threat intel enrichment** - scenarios enhanced with real IOCs

### AI-Powered Analysis
- **Gemini-based threat analyst** with tier-3 SOC expertise
- **MITRE ATT&CK mapping** - automatic technique identification
- **Confidence scoring** - AI uncertainty quantification
- **Slack-ready notifications** - instant team communication

### Real-Time Dashboard
- **Live metrics** updating every 2 seconds
- **Interactive incident stream** with threat details
- **Analysis performance** tracking with confidence trends
- **System health monitoring** across all components

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Threat Intel   │    │   Live Demo      │    │   AI Analysis   │
│     Feeds       │    │  Orchestrator    │    │    (Gemini)     │
│                 │    │                  │    │                 │
│ • CISA KEV      │───▶│ • Scenario Gen   │───▶│ • Threat Assess │
│ • AbuseIPDB     │    │ • Attack Chains  │    │ • MITRE Mapping │
│ • FireHOL       │    │ • Enrichment     │    │ • Confidence    │
│ • MITRE ATT&CK  │    │ • Metrics        │    │ • Remediation   │
│ • Spamhaus      │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BigQuery + Firestore                       │
│  • Threat indicators  • Detection results  • Analysis storage  │
└─────────────────────────────────────────────────────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Real-Time Dashboard                         │
│  • Live metrics  • Incident stream  • Analysis results        │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Deploy the Complete System
```bash
# Clone and enter the repository
cd SentinelOps

# Deploy everything (threat intel, cloud functions, APIs)
./deploy_live_demo.sh
```

### 2. Start the API Server
```bash
# Terminal 1: Start API server
./start_api_server.sh

# Server available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 3. Launch Live Demo
```bash
# Terminal 2: Start orchestrated demo
./start_live_demo.sh

# OR use the API
curl -X POST "http://localhost:8000/api/v1/demo/start" \
  -H "Content-Type: application/json" \
  -d '{
    "intensity": "high",
    "duration_minutes": 20,
    "threat_intel_enabled": true,
    "real_time_analysis": true
  }'
```

### 4. Monitor Live Dashboard
```bash
# Get real-time metrics
curl "http://localhost:8000/api/v1/demo/metrics"

# Get recent incidents  
curl "http://localhost:8000/api/v1/demo/incidents?limit=10"

# Get AI analyses
curl "http://localhost:8000/api/v1/demo/analyses?limit=10"
```

## 🎭 Demo Intensity Levels

### Low Intensity
- **0.5 scenarios/minute** - Steady, manageable pace
- **10% critical events** - Mostly routine threats
- **30-60s analysis delay** - Realistic SOC response times

### Medium Intensity  
- **1.5 scenarios/minute** - Moderate activity level
- **25% critical events** - Balanced threat distribution
- **10-30s analysis delay** - Efficient response

### High Intensity
- **3 scenarios/minute** - High activity simulation
- **40% critical events** - Frequent serious threats
- **5-15s analysis delay** - Rapid response mode

### Extreme Intensity
- **5 scenarios/minute** - Maximum stress testing
- **60% critical events** - Crisis simulation
- **2-8s analysis delay** - Emergency response

## 📊 Available Threat Intelligence

### Automatically Updated (Every 4 Hours)
| Feed | Description | Update Frequency | Records |
|------|-------------|------------------|---------|
| **CISA KEV** | Known exploited vulnerabilities | Daily | ~1000 CVEs |
| **AbuseIPDB** | Community malicious IPs | Hourly | ~100 high-confidence IPs |
| **FireHOL Level 1** | Premium IP reputation | 4 hours | ~50,000 IP ranges |
| **MITRE ATT&CK** | Tactics and techniques | Quarterly | ~500 techniques |
| **Spamhaus DROP** | Botnet IP ranges | 2 hours | ~300 networks |

### BigQuery Integration
```sql
-- Check for malicious IPs in VPC flow logs
SELECT 
  vpc.src_ip,
  vpc.dest_ip,
  ti.source as threat_source,
  ti.severity,
  ti.confidence
FROM `project.logs.vpc_flow` vpc
LEFT JOIN `project.threat_intel.threat_indicators` ti
  ON vpc.src_ip = ti.indicator
WHERE ti.indicator IS NOT NULL
  AND ti.confidence >= 0.8
```

## 🎯 Live Demo Scenarios

### Phase 1: Reconnaissance (0-5 minutes)
- Port scans and network discovery
- DNS reconnaissance queries  
- Service enumeration attempts
- **Threat Intel Enhancement**: Attacker IPs cross-referenced with reputation feeds

### Phase 2: Initial Access (5-15 minutes)
- Suspicious login attempts from foreign countries
- CVE exploitation attempts against known vulnerabilities
- Phishing and social engineering indicators
- **AI Analysis**: Gemini correlates activities with MITRE techniques

### Phase 3: Lateral Movement (15-25 minutes)
- Privilege escalation attempts
- Internal network reconnaissance
- Credential harvesting activities
- **Attack Chain Detection**: Multi-stage attack correlation

### Phase 4: Data Exfiltration (25+ minutes)
- Large database exports
- Unusual file access patterns
- Data compression and staging
- **Critical Response**: High-priority incident analysis and remediation

## 🧠 AI Analysis Features

### Gemini Threat Analyst Capabilities
- **Expert Prompting**: Tier-3 SOC analyst persona with security expertise
- **Few-Shot Learning**: Pre-trained on security incident examples
- **MITRE Integration**: Automatic ATT&CK technique identification
- **Confidence Scoring**: Uncertainty quantification (0.0-1.0)
- **Business Context**: Impact assessment and prioritization

### Analysis Output Example
```json
{
  "incident_id": "INC-20250617-001",
  "severity": "CRITICAL",
  "root_cause": "Active SSH brute force from 203.0.113.45 with 156 failed attempts",
  "blast_radius": "Single VM at risk, potential lateral movement if successful",
  "recommended_action": "Immediately block source IP, isolate target VM, rotate SSH keys",
  "confidence": 0.95,
  "mitre_tactics": ["TA0006"],
  "mitre_techniques": ["T1110.001"],
  "indicators_of_compromise": ["203.0.113.45", "156 failed SSH attempts"],
  "remediation_steps": [
    "Block IP 203.0.113.45 at firewall level",
    "Isolate web-1 from production network", 
    "Check logs for successful logins",
    "Rotate all SSH keys",
    "Implement fail2ban protection"
  ],
  "estimated_impact": "High - potential system compromise and data access",
  "business_context": "Web server compromise could disrupt services and expose customer data"
}
```

## 📱 Real-Time Dashboard Features

### Live Metrics (Updates every 2 seconds)
- **Scenario Generation Rate**: Threats per minute
- **AI Analysis Performance**: Average confidence and processing time
- **Threat Detection Stats**: Real-time IOC matches
- **System Health**: Component status monitoring

### Interactive Incident Stream
- **Severity-coded events** with visual indicators
- **Threat intel enrichment** badges for enhanced events
- **Demo phase tracking** showing attack progression
- **Risk scoring** with business impact assessment

### Analysis Viewer
- **Incident details drawer** with complete analysis
- **MITRE ATT&CK visualization** with clickable technique links
- **Slack notification preview** with copy-to-clipboard
- **Remediation steps** with priority ordering

## 🔧 API Endpoints

### Demo Control
```bash
POST /api/v1/demo/start          # Start live demo
POST /api/v1/demo/stop           # Stop demo
GET  /api/v1/demo/status         # Get demo status
GET  /api/v1/demo/summary        # Complete overview
```

### Real-Time Data
```bash
GET  /api/v1/demo/metrics        # Live metrics (updates every 5s)
GET  /api/v1/demo/incidents      # Recent incidents with filters
GET  /api/v1/demo/analyses       # AI analysis results
GET  /api/v1/demo/detections     # Threat intel detections
```

### Threat Simulation
```bash
POST /api/v1/threats/scenarios/generate    # Generate single scenario
POST /api/v1/threats/scenarios/batch       # Generate batch scenarios  
POST /api/v1/threats/campaigns/simulate    # Simulate attack campaign
POST /api/v1/threats/analyze               # Analyze with Gemini
```

### Manual Controls
```bash
POST /api/v1/demo/scenario/inject    # Inject custom scenario
DELETE /api/v1/demo/cleanup          # Clean demo data
```

## 💰 Cost Analysis

### Threat Intelligence (Free Tier)
- **CISA KEV**: Free government feed
- **AbuseIPDB**: Free up to 1000 requests/day
- **FireHOL**: Free open-source lists
- **MITRE ATT&CK**: Free public dataset
- **Spamhaus**: Free for non-commercial use

### BigQuery (First 1TB/month free)
- **Storage**: ~50MB for all threat feeds
- **Queries**: ~10MB per detection query
- **Monthly usage**: <1GB for continuous demo

### Gemini Analysis
- **Cost per analysis**: $0.001-0.003
- **20-minute demo**: ~$0.50-2.00 total
- **Daily continuous**: ~$5-15

### Cloud Infrastructure
- **Cloud Functions**: Free tier covers demo usage
- **Firestore**: Free tier sufficient for demo data
- **Cloud Scheduler**: Free tier includes required jobs

**Total Demo Cost**: <$5 for extended demonstrations

## 🎪 Live Demonstration Flow

### Opening (2 minutes)
1. **Show threat intelligence** - Query BigQuery for live threat data
2. **Display scenario library** - 25 scenarios across severities  
3. **Explain AI analysis** - Gemini threat analyst capabilities

### Real-Time Simulation (15 minutes)
1. **Start high-intensity demo** - 3 scenarios/minute with escalation
2. **Live dashboard monitoring** - Real-time metrics and incident stream
3. **AI analysis showcase** - Gemini processing threats with confidence scores
4. **Threat intel correlation** - Live IOC matching and enrichment

### Deep Dive Analysis (8 minutes)
1. **Critical incident focus** - SSH brute force or ransomware scenario
2. **Complete analysis walkthrough** - MITRE mapping and remediation steps
3. **Business impact assessment** - Risk scoring and communication
4. **Slack notification demo** - Ready-to-send incident reports

### System Integration (5 minutes)
1. **BigQuery threat hunting** - Live queries against threat intel
2. **API demonstration** - Programmatic access to all features
3. **Attack chain correlation** - Multi-stage incident analysis
4. **Performance metrics** - Response times and accuracy statistics

**Total Demo Time**: 30 minutes + Q&A

## 🏆 Key Differentiators

### Production-Ready Architecture
- **Real threat intelligence** from authoritative sources
- **Enterprise-grade APIs** with comprehensive documentation
- **Cloud-native deployment** with auto-scaling and resilience
- **Observability** with metrics, logging, and monitoring

### AI-First Security
- **Gemini integration** for expert-level threat analysis
- **Natural language queries** for threat hunting
- **Automated correlation** across multiple data sources
- **Continuous learning** from new threat patterns

### Demo Excellence
- **Zero manual intervention** - fully automated operation
- **Realistic scenarios** based on actual threat patterns
- **Live audience interaction** - real-time adjustments possible
- **Comprehensive reporting** - detailed analysis and statistics

---

## 🚀 Ready for Launch!

The SentinelOps Live Demo System is production-ready and provides a complete showcase of modern security operations:

✅ **Real threat intelligence** feeds automatically updated  
✅ **AI-powered analysis** with expert-level insights  
✅ **Live rotating scenarios** demonstrating real-world threats  
✅ **Interactive dashboard** with real-time metrics  
✅ **Production APIs** ready for integration  
✅ **Cost-effective operation** within free tier limits  

**Perfect for hackathons, investor demos, security conferences, and training sessions.**