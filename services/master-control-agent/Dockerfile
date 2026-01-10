# =============================================================================
# Master Control Agent Service Dockerfile
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy shared requirements and install
COPY services/shared/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy shared modules
COPY services/shared /app/shared

# Copy service code
COPY services/master-control-agent /app/master-control-agent

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the service
CMD ["uvicorn", "master-control-agent.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
