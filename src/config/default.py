"""Default configuration for SentinelOps."""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application settings
APP_NAME = "SentinelOps"
APP_VERSION = "0.1.0"
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG_MODE", "false").lower() == "true"

# Server configuration
HOST = os.getenv("APP_HOST", "127.0.0.1")
PORT = int(os.getenv("APP_PORT", "8000"))

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = BASE_DIR / "logs" / "sentinelops.log"

# Google Cloud configuration
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Vertex AI / Gemini configuration
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

# BigQuery configuration
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "security_logs")
BIGQUERY_TABLE_PREFIX = os.getenv("BIGQUERY_TABLE_PREFIX", "sentinel_")

# Cloud Storage configuration
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "sentinelops-data")
GCS_LOGS_PREFIX = os.getenv("GCS_LOGS_PREFIX", "logs/")

# Pub/Sub configuration
PUBSUB_TOPIC_INCIDENTS = os.getenv("PUBSUB_TOPIC_INCIDENTS", "sentinelops-incidents")
PUBSUB_TOPIC_ALERTS = os.getenv("PUBSUB_TOPIC_ALERTS", "sentinelops-alerts")
PUBSUB_SUBSCRIPTION_PREFIX = os.getenv("PUBSUB_SUBSCRIPTION_PREFIX", "sentinelops-sub-")

# Agent configuration
AGENT_DETECTION_INTERVAL = int(os.getenv("AGENT_DETECTION_INTERVAL", "30"))
AGENT_ANALYSIS_TIMEOUT = int(os.getenv("AGENT_ANALYSIS_TIMEOUT", "300"))
AGENT_REMEDIATION_DRY_RUN = (
    os.getenv("AGENT_REMEDIATION_DRY_RUN", "true").lower() == "true"
)
AGENT_ORCHESTRATOR_MAX_RETRIES = int(os.getenv("AGENT_ORCHESTRATOR_MAX_RETRIES", "3"))

# Security configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-production")
API_KEY_SALT = os.getenv("API_KEY_SALT", "change-this-in-production")

# Rate limiting
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
