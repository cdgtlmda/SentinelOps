"""Production configuration for SentinelOps."""

from typing import List

# Override for production
DEBUG = False
APP_ENV = "production"

# Production logging
LOG_LEVEL = "WARNING"

# Production security
AGENT_REMEDIATION_DRY_RUN = False  # Enable actual remediation in production

# Disable demo mode in production
DEMO_MODE = False

# Production CORS settings
CORS_ORIGINS: List[str] = []  # Add your production domains here

# Production performance settings
WORKERS = 4
WORKER_CONNECTIONS = 1000
KEEPALIVE = 5

# Stricter rate limiting for production
RATE_LIMIT_REQUESTS = 50
RATE_LIMIT_WINDOW = 60

# Production monitoring
ENABLE_METRICS = True
METRICS_PORT = 9090

# Production caching
CACHE_ENABLED = True
CACHE_TTL = 300  # 5 minutes

# SSL/TLS settings
USE_SSL = True
SSL_REDIRECT = True

# Database connection pool settings
DB_POOL_SIZE = 20
DB_MAX_OVERFLOW = 10
DB_POOL_TIMEOUT = 30.0
DB_POOL_RECYCLE = 3600
DB_POOL_PRE_PING = True
DB_CONNECT_TIMEOUT = 10
DB_POOL_USE_LIFO = True
DB_ECHO_POOL = False
DB_QUERY_CACHE_SIZE = 1200
DB_USE_INSERTMANYVALUES = True
DB_MONITOR_ENABLED = True
