# System Requirements

This document outlines the requirements for running SentinelOps with Google Agent Development Kit (ADK).

## Verified System Specifications

### Operating System
- **OS**: macOS (Darwin)
- **Architecture**: arm64 (Apple Silicon)

### Python Environment
- **Python Version**: 3.12+ (3.13 verified)
- **Pip Version**: 25.1.1 or higher
- **Virtual Environment**: Recommended (venv or conda)

### Version Control
- **Git Version**: Installed (version 2.x or higher required)

### Storage
- **Required Minimum**: 10GB
- **Recommended**: 50GB for logs and temporary files

### Google Cloud SDK
- **Installation**: Required for deployment and API access
- **Installation Instructions**: Run `./scripts/setup/install-gcloud.sh`

### Development Tools Required
- Visual Studio Code (or preferred IDE)
- Python extensions for IDE
- Google Cloud SDK (gcloud CLI)
- Agent Development Kit (ADK) - installed via pip (google-adk>=1.2.0)
- Docker (optional, for local testing)

### Minimum Hardware Requirements
- **RAM**: 8GB (16GB recommended for development)
- **CPU**: 4 cores (8 cores recommended)
- **Network**: Stable internet connection for Google Cloud APIs

### Google Cloud Services Required
The following Google Cloud APIs must be enabled:
- Compute Engine API
- Cloud Logging API
- Cloud Storage API
- Vertex AI API (for Gemini integration)
- BigQuery API
- Cloud Run API (for agent deployment)
- Firestore API (for state management)
- Secret Manager API
- Cloud Trace API (for ADK telemetry)
- Cloud Monitoring API
- IAM API
- Chronicle API (optional, if available)

### ADK-Specific Requirements
- **ADK Version**: 1.2.0 or higher (installed via pip)
- **Python Compatibility**: Python 3.12+ (updated ADK requirement)
- **Memory**: Additional 2GB RAM for ADK runtime
- **Network**: Low-latency connection to GCP (for agent transfers)

### Python Package Requirements
Core dependencies include:
- `google-adk` - Agent Development Kit
- `google-cloud-aiplatform` - Vertex AI/Gemini integration
- `google-cloud-firestore` - State management
- `google-cloud-bigquery` - Log analysis
- `google-cloud-logging` - Cloud logging
- `langchain` - Additional LLM utilities
- `fastapi` - REST API framework
- `pydantic` - Data validation

See `requirements.txt` for complete list.

### Environment Variables Required
Minimum required configuration:
```env
# GCP Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# ADK Configuration
ADK_TELEMETRY_ENABLED=true
ADK_LOG_LEVEL=INFO

# Agent Configuration
GEMINI_MODEL=gemini-1.5-flash
FIRESTORE_DATABASE=(default)
```

See `.env.example` for complete configuration options.

### Network Requirements
- **Firewall**: Allow outbound HTTPS (443) to *.googleapis.com
- **Proxy**: Configure HTTP_PROXY/HTTPS_PROXY if behind corporate proxy
- **Bandwidth**: Minimum 10 Mbps for real-time agent communication

### Production Requirements
- **High Availability**: Deploy across multiple regions
- **Load Balancer**: For distributing agent workload
- **Monitoring**: Cloud Monitoring dashboards configured
- **Backup**: Firestore backup schedule configured
