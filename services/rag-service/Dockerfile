FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc

# Install dependencies
RUN pip install -r requirements.txt

# Copy all source files
COPY . .
COPY models_local ./models_local

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

ENV HF_HUB_OFFLINE=1
CMD ["python", "main.py"]

