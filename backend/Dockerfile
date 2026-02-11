# NARUU AI Tourism Platform - Backend Dockerfile
# Multi-stage build for production deployment on Railway

FROM python:3.12-slim AS base

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${APP_PORT:-8000}/health || exit 1

# Run
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE ${APP_PORT:-8000}

CMD ["python", "-m", "uvicorn", "naruu_api.main:app", "--host", "0.0.0.0", "--port", "${APP_PORT:-8000}"]
