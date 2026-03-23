@echo off
REM ==========================================
REM Quick Start Script for Docker Deployment
REM ==========================================

echo.
echo ========================================
echo  Qwen ASR Translate - Docker Setup
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://www.docker.com/
    pause
    exit /b 1
)

echo [OK] Docker detected
echo.

REM Check if .env exists
if not exist ".env" (
    echo [INFO] Creating .env from .env.example...
    copy .env.example .env >nul
    echo [OK] .env created - please edit if needed
    echo.
) else (
    echo [OK] .env found
    echo.
)

REM Build containers
echo ========================================
echo  Building Docker containers...
echo ========================================
echo.

docker-compose build

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [OK] Build completed successfully
echo.

REM Start services
echo ========================================
echo  Starting services...
echo ========================================
echo.

docker-compose up -d

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start services!
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Services:
echo   - App:        http://localhost:8000
echo   - CPU Worker: http://localhost:8001
echo   - GPU Worker: http://localhost:8001
echo   - Ollama:     http://localhost:11434
echo.
echo Commands:
echo   - View logs:     docker-compose logs -f
echo   - Stop:          docker-compose down
echo   - Restart:       docker-compose restart
echo   - Rebuild:       docker-compose build --no-cache
echo.
echo Opening app in browser...
timeout /t 3 /nobreak >nul
start http://localhost:8000

echo.
pause
