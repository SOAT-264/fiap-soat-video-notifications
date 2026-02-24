FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy shared package first
COPY fiap-soat-video-shared/ /tmp/video-processor-shared/
RUN pip install --no-cache-dir /tmp/video-processor-shared/

# Copy requirements
COPY fiap-soat-video-notifications/pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir \
    "fastapi>=0.109.0" \
    "uvicorn[standard]>=0.27.0" \
    "prometheus-client>=0.20.0" \
    "pydantic>=2.0.0" \
    "pydantic-settings>=2.0.0" \
    "sqlalchemy>=2.0.0" \
    "asyncpg>=0.29.0" \
    "psycopg2-binary>=2.9.0" \
    "redis>=5.0.0" \
    "aioboto3>=12.0.0" \
    "aiosmtplib>=3.0.0" \
    "jinja2>=3.1.0" \
    "httpx>=0.26.0"

# Copy application code
COPY fiap-soat-video-notifications/src/ ./src/

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "notification_service.infrastructure.adapters.input.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
