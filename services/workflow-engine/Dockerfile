# =============================================================================
# Workflow Engine Service Dockerfile
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy shared requirements and install
COPY shared/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install Prefect
RUN pip install --no-cache-dir prefect>=2.0

# Copy shared modules
COPY shared /app/shared

# Copy service code
COPY workflow-engine /app/workflow-engine

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the service
CMD ["python", "-m", "workflow-engine.app.workflows"]
