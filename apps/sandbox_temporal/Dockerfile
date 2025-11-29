# Dockerfile for Sandbox Temporal Worker
#
# Multi-stage build for smaller final image

# Stage 1: Build
FROM python:3.11-slim as builder

WORKDIR /app

# Install uv for fast package management
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Create virtual environment and install dependencies
RUN uv venv && uv pip install -e .

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code
COPY --from=builder /app/src /app/src

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.connect(('localhost', 9091)); s.close()" || exit 1

# Default command
CMD ["python", "-m", "src.workers.sandbox_worker"]
