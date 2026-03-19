@echo off
chcp 65001 >nul
title QwenASR - Easy Install

echo ============================================================
echo QwenASR Translate - Easy Install
echo ============================================================
echo.
echo This installer will:
echo 1. Create virtual environment (.venv)
echo 2. Install all dependencies
echo 3. Start the application
echo.
echo Installation time: about 10-15 minutes
echo.
pause

REM Change to project directory
cd /d %USERPROFILE%\lobsterai\project\qwen-asr-translate

echo Current directory: %CD%
echo.

REM Check Python
echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found
    echo Please install Python and add to PATH
    pause
    exit /b 1
)

echo Python installed
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VER=%%i
echo Python version: %PYTHON_VER%

REM Create virtual environment
echo.
echo [Step 1/4] Creating virtual environment...
if exist ".venv" (
    echo Removing old virtual environment...
    rmdir /s /q ".venv"
)
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created

REM Activate virtual environment
echo.
echo [Step 2/4] Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo [Step 3/4] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo pip upgraded

REM Install dependencies
echo.
echo [Step 4/4] Installing dependencies...
echo This may take 10-15 minutes, please be patient...
echo.

echo Installing base packages...
pip install customtkinter numpy requests tqdm

echo.
echo Installing audio processing packages...
pip install soundfile librosa onnxruntime

echo.
echo Installing translation packages...
pip install transformers sentencepiece

echo.
echo Installing PyAudio...
pip install pyaudio
if errorlevel 1 (
    echo Installing via pipwin...
    pip install pipwin
    pipwin install pyaudio
)

echo.
echo Installing OpenVINO (optional, for CPU acceleration)...
pip install openvino openvino-dev
if errorlevel 1 (
    echo OpenVINO installation failed, but app can still run
)

echo.
echo ============================================================
echo Installation Complete!
echo ============================================================
echo.
echo Application location: %CD%
echo.

REM Ask to download models
set /p download="Download AI models now? (Y/N, about 1.2GB): "
if /i "%download%"=="Y" (
    echo.
    Downloading models...
    python downloader.py
) else (
    echo.
    Note: Models will be downloaded on first app launch
)

echo.
echo Starting application...
echo.
python app.py

if errorlevel 1 (
    echo.
    echo WARNING: Application failed to start
    echo Possible cause: Models not downloaded
    echo Please run: python downloader.py
)

echo.
echo ============================================================
echo Tips
echo ============================================================
echo.
echo To start later, run:
echo cd %USERPROFILE%\lobsterai\project\qwen-asr-translate
echo call .venv\Scripts\activate.bat
echo python app.py
echo.
echo Or double-click: quick-start.bat
echo.

pause
