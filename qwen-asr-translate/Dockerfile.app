# App Container - UI + API Gateway only
# No torch/CUDA dependencies - minimal size
FROM python:3.11-slim

WORKDIR /app

# Install minimal dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

# Install only UI and API dependencies (no torch)
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    python-dotenv \
    httpx \
    pydantic \
    pyaudio

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser main.py ./
COPY --chown=appuser:appuser config.ini ./
COPY --chown=appuser:appuser .env.example ./.env.example

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ROLE=gateway

# Switch to non-root user
USER appuser

# Create logs directory
RUN mkdir -p /app/logs

EXPOSE 8000

CMD ["python", "main.py"]
