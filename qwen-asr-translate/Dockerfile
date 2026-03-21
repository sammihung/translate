# Multi-stage Dockerfile for Qwen ASR Translate
# Optimized for minimal image size and GPU support

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    portaudio19-dev \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install uv
RUN pip install --upgrade pip uv

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Install dependencies with uv (faster than pip)
RUN uv pip install --system -r requirements.txt

# ============================================
# Stage 2: Runtime (CPU)
# ============================================
FROM python:3.11-slim as runtime-cpu

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser main.py ./
COPY --chown=appuser:appuser config.ini ./

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TRANSFORMERS_VERBOSITY=error \
    CUDA_VISIBLE_DEVICES=""

# Switch to non-root user
USER appuser

# Create logs directory
RUN mkdir -p /app/logs

EXPOSE 8000

CMD ["python", "main.py"]

# ============================================
# Stage 3: Runtime (GPU with CUDA)
# ============================================
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 as runtime-gpu

WORKDIR /app

# Install Python and runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    portaudio19-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

# Upgrade pip
RUN pip3 install --upgrade pip uv

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Install Python dependencies with GPU support
RUN uv pip install --system -r requirements.txt \
    && pip3 install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser main.py ./
COPY --chown=appuser:appuser config.ini ./

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TRANSFORMERS_VERBOSITY=error \
    CUDA_VISIBLE_DEVICES=0

# Switch to non-root user
USER appuser

# Create logs directory
RUN mkdir -p /app/logs

EXPOSE 8000

CMD ["python3", "main.py"]
