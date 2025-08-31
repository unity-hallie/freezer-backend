# Multi-stage Docker build for production
FROM python:3.9-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Production stage
FROM python:3.9-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Make sure scripts are executable
RUN chmod +x docker-entrypoint.sh

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
USER app

# Add local Python packages to PATH
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000

# Use entrypoint script for initialization
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]