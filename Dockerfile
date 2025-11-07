# Momentum Trading Strategy - Dockerfile
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies (minimal for production)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data/cache database alerts

# Health check - check both main bot and fill monitor
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f trading_system.py || exit 1

# Create startup script to run both services
RUN echo '#!/bin/bash\npython fill_monitor_service.py &\npython trading_system.py' > /app/start.sh && chmod +x /app/start.sh

# Default command - runs both bot and fill monitor
CMD ["/app/start.sh"]
