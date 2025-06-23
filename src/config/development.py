"""Development configuration for SentinelOps."""

# Application Settings
APP_NAME = "SentinelOps"
APP_VERSION = "0.1.0"
APP_ENV = "development"
DEBUG = True
HOST = "0.0.0.0"  # nosec B104 - Development environment requires binding to all interfaces
PORT = 8000
LOG_LEVEL = "INFO"

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT = "sentinelops-dev"
GOOGLE_APPLICATION_CREDENTIALS = "./service-account-key.json"

# Vertex AI Configuration
VERTEX_AI_LOCATION = "us-central1"
GEMINI_MODEL = "gemini-1.5-pro-002"

# BigQuery Configuration
BIGQUERY_DATASET = "security_logs"
BIGQUERY_TABLE_PREFIX = "sentinel_"

# Pub/Sub Configuration
PUBSUB_TOPIC_INCIDENTS = "sentinelops-incidents-dev"
PUBSUB_TOPIC_ALERTS = "sentinelops-alerts-dev"
PUBSUB_SUBSCRIPTION_PREFIX = "sentinelops-sub-dev-"

# Agent Configuration
AGENT_DETECTION_INTERVAL = 30
AGENT_ANALYSIS_TIMEOUT = 300
AGENT_REMEDIATION_DRY_RUN = True
AGENT_ORCHESTRATOR_MAX_RETRIES = 3

# Security Configuration
JWT_SECRET_KEY = "dev-jwt-secret-key-for-testing-only-32chars!!"
API_KEY_SALT = "dev-api-salt-16char-minimum!!!"
RATE_LIMIT_REQUESTS = 1000
RATE_LIMIT_WINDOW = 60

# Communication Configuration
SLACK_WEBHOOK_URL = None
SLACK_CHANNEL = "#security-incidents"
EMAIL_SMTP_HOST = None
EMAIL_SMTP_PORT = 587
EMAIL_FROM_ADDRESS = None
