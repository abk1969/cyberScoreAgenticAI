# CyberScore Backend — Multi-stage Docker build
# Python 3.12 on Debian slim for WeasyPrint system dependencies

# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system deps for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.5

# Copy dependency files
COPY pyproject.toml ./

# Export requirements (without dev deps)
RUN poetry export -f requirements.txt --without-hashes --without dev -o requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime system deps (WeasyPrint needs these)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libcairo2 \
    libgirepository1.0-dev \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r csadmin && useradd -r -g csadmin csadmin
USER csadmin

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
