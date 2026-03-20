@echo off
chcp 65001 >nul
echo ==========================================
echo [SEARCH] Scanning system hardware...
echo ==========================================

:: Try to run nvidia-smi to detect NVIDIA GPU
nvidia-smi >nul 2>&1

IF %ERRORLEVEL% EQU 0 (
    echo [OK] NVIDIA GPU detected!
    echo [INFO] Environment: [GPU Acceleration Enabled]
    set COMPOSE_CMD=docker compose -f docker-compose.yml -f docker-compose-gpu.yml up -d
    :: With GPU, we make sure BOTH models are available for manual switching
    set OLLAMA_MODEL_DEFAULT=translategemma:4b-it-fp16
    set OLLAMA_MODEL_ALT=translategemma:4b-it-q4_K_M
) ELSE (
    echo [WARN] No NVIDIA GPU detected [or driver not installed].
    echo [INFO] Environment: [CPU Processing Only]
    set COMPOSE_CMD=docker compose -f docker-compose.yml up -d
    set OLLAMA_MODEL_DEFAULT=translategemma:4b-it-q4_K_M
    set OLLAMA_MODEL_ALT=
)

echo.
echo Starting Docker services...
%COMPOSE_CMD%

echo.
echo Waiting for Ollama service to be ready...
:: Give Docker a few seconds to initialize the API
timeout /t 5 /nobreak >nul

echo [DOWNLOAD] Syncing models with Ollama...
docker exec ollama_server ollama pull %OLLAMA_MODEL_DEFAULT%

:: If GPU exists, also pre-pull the small q4 model for fast switching
if not "%OLLAMA_MODEL_ALT%"=="" (
    echo [DOWNLOAD] Also pulling fallback model...
    docker exec ollama_server ollama pull %OLLAMA_MODEL_ALT%
)

echo.
echo [SUCCESS] Everything is ready! Launching QwenASR...
echo.

:: Start the Python application
call .venv\Scripts\activate
python src\app.py

pause