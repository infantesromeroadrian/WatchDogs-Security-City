# ============================================================================
# WatchDogs Video Analysis System - Production Dockerfile
# Multi-stage build for optimal size and security
# ============================================================================

# ============================================================================
# Stage 1: Builder - Install dependencies
# ============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy dependency files
COPY requirements.txt .

# Install dependencies to a target directory
RUN pip install --no-cache-dir --target=/build/deps -r requirements.txt

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:3.11-slim AS runtime

# Environment configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash watchdogs && \
    mkdir -p /app/data/temp && \
    chown -R watchdogs:watchdogs /app

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /build/deps /usr/local/lib/python3.11/site-packages/

# Copy application code
COPY --chown=watchdogs:watchdogs src/ ./src/
COPY --chown=watchdogs:watchdogs tests/ ./tests/
COPY --chown=watchdogs:watchdogs data/ ./data/

# Switch to non-root user
USER watchdogs

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# Default command
CMD ["python", "-m", "src.backend.app"]

