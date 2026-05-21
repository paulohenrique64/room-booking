# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements/ requirements/
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements/prod.txt

# Final stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create necessary runtime directories
RUN mkdir -p logs media staticfiles

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DJANGO_SETTINGS_MODULE=config.settings.docker

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "60", "config.wsgi:application"]
