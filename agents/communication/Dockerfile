# Dockerfile for Communication Agent
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
COPY agents/communication/requirements.txt ./communication-requirements.txt

# Copy ADK if it exists (for local installation)
COPY adk/ ./adk/

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user -r communication-requirements.txt && \
    (test -d adk && pip install --no-cache-dir --user -e ./adk || echo "ADK not found locally, using PyPI version")

# Final stage
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    ENVIRONMENT=production \
    AGENT_TYPE=communication \
    LOG_LEVEL=INFO

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser agents/communication/ ./agents/communication/
# Templates are included in src/communication_agent/templates/

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Run the communication agent with simple Cloud Run wrapper
CMD ["python", "-m", "src.cloud_run_simple_wrapper"]