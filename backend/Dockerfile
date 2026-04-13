# ── Google Cloud Run — ScholarPath Backend ────────────────────────────────────
# Python 3.11 slim image for minimal size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for asyncpg and cryptography
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create uploads directory (local media provider)
RUN mkdir -p uploads

# Cloud Run sets the PORT env variable (default 8080)
ENV PORT=8080

# Expose the port
EXPOSE 8080

# Start the FastAPI server
# Cloud Run injects $PORT automatically
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
