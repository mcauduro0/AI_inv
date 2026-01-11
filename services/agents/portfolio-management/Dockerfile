# =============================================================================
# Idea Generation Agent Service Dockerfile
# Build context: services/
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

# Copy shared modules
COPY shared /app/shared

# Copy agent code
COPY agents/portfolio-management /app/portfolio-management

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run the agent
CMD ["uvicorn", "portfolio-management.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
