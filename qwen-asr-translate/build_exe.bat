@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   QwenASR Translate - Build Tool
echo   Build Executable Application
echo ========================================
echo.

REM Check Python
echo [1/5] Checking Python environment...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found
    echo Please install Python 3.11 first
    pause
    exit /b 1
)

python --version
echo.

REM Install dependencies
echo [2/5] Installing dependencies...
echo This may take 5-10 minutes, please wait...
echo.

REM Upgrade uv
python -m pip install --upgrade uv

REM Install PyInstaller
python -m pip install pyinstaller==6.5.0

REM Freeze dependencies
echo.
echo [3/5] Freezing dependency versions...
python -m uv pip compile pyproject.toml --output-file requirements-freeze.txt
echo Generated requirements-freeze.txt

REM Create virtual environment if not exists
if not exist ".venv" (
    echo [4/5] Creating virtual environment...
    python -m venv .venv
)

echo.
echo [5/5] Starting build process...
echo This may take 10-15 minutes...
echo.

REM Use PyInstaller to build
pyinstaller --clean qwen_asr.spec

REM Check build result
if exist "dist\QwenASR Translate\QwenASR Translate.exe" (
    echo.
    echo ========================================
    echo   Build Successful!
    echo ========================================
    echo.
    echo Executable location:
    echo   dist\QwenASR Translate\QwenASR Translate.exe
    echo.
    echo Entire folder can be distributed:
    echo   dist\QwenASR Translate\
    echo.
    echo Contains:
    echo   - QwenASR Translate.exe (main program)
    echo   - All dependencies
    echo   - Configuration files
    echo.
) else (
    echo.
    echo ========================================
    echo   Build Failed
    echo ========================================
    echo.
    echo Please check error messages above
    echo.
)

pause
