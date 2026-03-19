@echo off
chcp 65001 >nul
title QwenASR - Complete Install

echo ============================================================
echo QwenASR Translate - Complete Installation
echo ============================================================
echo.
echo This installer will:
echo 1. Check Python installation
echo 2. Create virtual environment
echo 3. Install ALL dependencies (including PyAudio)
echo 4. Download models (optional)
echo 5. Start the application
echo.
echo Installation time: 15-20 minutes
echo.
pause

REM Change to project directory
cd /d %USERPROFILE%\lobsterai\project\qwen-asr-translate

echo Current directory: %CD%
echo.

REM Check Python
echo [Step 1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo.
    echo Please install Python 3.10 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VER=%%i
echo Python %PYTHON_VER% found

REM Check Python version
python -c "import sys; exit(0) if sys.version_info >= (3, 10) else exit(1)"
if errorlevel 1 (
    echo ERROR: Python 3.10 or higher required!
    echo Current version: %PYTHON_VER%
    pause
    exit /b 1
)
echo Python version OK

REM Create virtual environment
echo.
echo [Step 2/6] Creating virtual environment...
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
echo [Step 3/6] Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo [Step 4/6] Upgrading pip and build tools...
python -m pip install --upgrade pip --quiet
python -m pip install --upgrade setuptools wheel --quiet
echo pip upgraded

REM Install dependencies
echo.
echo [Step 5/6] Installing dependencies...
echo This will take 15-20 minutes. Please be patient...
echo.

echo Installing core packages...
pip install numpy requests tqdm Pillow protobuf

echo.
echo Installing GUI packages...
pip install customtkinter

echo.
echo Installing audio processing packages...
pip install soundfile librosa

echo.
echo Installing ONNX runtime...
pip install onnxruntime

echo.
echo Installing PyAudio (this may fail, will retry)...
pip install pyaudio
if errorlevel 1 (
    echo PyAudio failed, trying alternative method...
    pip install pipwin
    pipwin install pyaudio
    if errorlevel 1 (
        echo WARNING: PyAudio installation failed
        echo You may need to install manually later
    )
)

echo.
echo Installing translation packages...
pip install transformers sentencepiece

echo.
echo Installing video/audio packages...
pip install ffmpeg-python pydub

echo.
echo Installing PyTorch (CPU version for compatibility)...
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

echo.
echo Installing OpenVINO (optional, for CPU acceleration)...
pip install openvino openvino-dev
if errorlevel 1 (
    echo OpenVINO installation failed, but app can still run
)

echo.
echo Installing VAD package...
pip install silero-vad

echo.
echo [Step 6/6] Verifying installation...
python setup_checker.py

echo.
echo ============================================================
echo Installation Complete!
echo ============================================================
echo.

REM Ask to download models
set /p download="Download AI models now? (Y/N, about 1.2GB): "
if /i "%download%"=="Y" (
    echo.
    echo Downloading models...
    echo This will take 10-30 minutes depending on your connection...
    python downloader.py
    if errorlevel 1 (
        echo.
        echo WARNING: Model download failed
        echo You can download later by running: python downloader.py
    )
) else (
    echo.
    echo Note: Models will be downloaded on first app launch
)

echo.
echo ============================================================
echo SUCCESS! Application is ready.
echo ============================================================
echo.
echo Starting application...
echo.
python app.py

if errorlevel 1 (
    echo.
    echo WARNING: Application failed to start
    echo This might be because models are not downloaded yet
    echo Please run: python downloader.py
)

echo.
echo ============================================================
echo How to start later
echo ============================================================
echo.
echo Option 1 - Double-click: quick-start.bat
echo.
echo Option 2 - Run these commands:
echo cd %USERPROFILE%\lobsterai\project\qwen-asr-translate
echo call .venv\Scripts\activate.bat
echo python app.py
echo.

pause
