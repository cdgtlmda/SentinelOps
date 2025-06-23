"""
Test Environment Configuration for SentinelOps
"""

import os

# Application Configuration
APP_NAME = "SentinelOps"
APP_VERSION = "1.0.0-test"
APP_ENV = "test"
DEBUG = True
HOST = "127.0.0.1"
PORT = 8080

# Logging Configuration
LOG_LEVEL = "DEBUG"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "logs/test/sentinelops.log"
LOG_MAX_BYTES = 10485760  # 10MB
LOG_BACKUP_COUNT = 5

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT = "test-project"
GOOGLE_CLOUD_REGION = "us-central1"
GOOGLE_CLOUD_ZONE = "us-central1-a"
GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS"
)  # Use real GCP credentials

# Vertex AI Configuration
VERTEX_AI_LOCATION = "us-central1"
VERTEX_AI_MODEL = "gemini-1.5-pro-002"
VERTEX_AI_TEMPERATURE = 0.7
VERTEX_AI_MAX_OUTPUT_TOKENS = 2048

# BigQuery Configuration
BIGQUERY_DATASET = "test_sentinel_ops"
BIGQUERY_TABLE_PREFIX = "test_sentinel_"
BIGQUERY_LOCATION = "US"

# Pub/Sub Configuration
PUBSUB_TOPIC_INCIDENTS = "test-sentinel-incidents"
PUBSUB_TOPIC_ALERTS = "test-sentinel-alerts"
PUBSUB_SUBSCRIPTION_PREFIX = "test-sentinel-sub-"

# Firestore Configuration
FIRESTORE_DATABASE = "(default)"
FIRESTORE_COLLECTION_PREFIX = "test_"

# Agent Configuration
DETECTION_AGENT_INTERVAL = 60
ANALYSIS_AGENT_TIMEOUT = 300
REMEDIATION_AGENT_DRY_RUN = True
ORCHESTRATOR_AGENT_MAX_RETRIES = 3

# Security Configuration
JWT_SECRET_KEY = "test-jwt-secret-key-for-testing-only-do-not-use"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DELTA = 3600  # 1 hour
API_KEY_SALT = "test-api-salt-key-for-testing"
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds

# Communication Configuration
SLACK_WEBHOOK_URL = ""
SLACK_CHANNEL = "#test-alerts"
SLACK_USERNAME = "SentinelOps Test"
SLACK_ICON_EMOJI = ":robot_face:"

EMAIL_SMTP_HOST = "localhost"
EMAIL_SMTP_PORT = 25
EMAIL_SMTP_USER = ""
EMAIL_SMTP_PASSWORD = ""
EMAIL_FROM_ADDRESS = "test@example.com"
EMAIL_FROM_NAME = "SentinelOps Test"

# Testing Configuration
TEST_MODE = False  # Use real services for testing
MOCK_EXTERNAL_SERVICES = False  # NO MOCKING - use real GCP services
USE_FIXTURES = False  # Use real data, not fixtures
FIXTURE_PATH = "tests/fixtures"
