@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   QwenASR Translate - Full Build
echo   PyInstaller + Inno Setup Installer
echo ========================================
echo.

REM Check Python
echo [1/6] Checking Python environment...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

python --version
echo.

REM Install dependencies
echo [2/6] Installing dependencies...
python -m pip install --upgrade uv
python -m pip install pyinstaller==6.5.0
echo.

REM Freeze dependencies (without pyannote-audio)
echo [3/6] Freezing dependency versions...
python -m uv pip compile pyproject.toml --output-file requirements-freeze.txt
echo Generated requirements-freeze.txt
echo.

REM Build with PyInstaller
echo [4/6] Building executable with PyInstaller...
pyinstaller --clean qwen_asr.spec
echo.

REM Check PyInstaller result
if not exist "dist\QwenASR Translate\QwenASR Translate.exe" (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

echo PyInstaller build successful!
echo.

REM Check Inno Setup
echo [5/6] Checking Inno Setup...
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set ISCC_PATH="C:\Program Files\Inno Setup 6\ISCC.exe"
) else (
    echo WARNING: Inno Setup not found!
    echo.
    echo Please download and install Inno Setup:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo The executable has been built successfully:
    echo   dist\QwenASR Translate\QwenASR Translate.exe
    echo.
    echo You can distribute the folder directly, or
    echo install Inno Setup to create a professional installer.
    echo.
    goto :skip_inno
)

echo Found Inno Setup: %ISCC_PATH%
echo.

REM Build installer with Inno Setup
echo [6/6] Building installer with Inno Setup...
%ISCC_PATH% installer.iss
echo.

REM Check Inno Setup result
if exist "installer_output\QwenASR-Translate-Setup-0.1.0.exe" (
    echo ========================================
    echo   Build Complete!
    echo ========================================
    echo.
    echo Executable:
    echo   dist\QwenASR Translate\QwenASR Translate.exe
    echo.
    echo Installer:
    echo   installer_output\QwenASR-Translate-Setup-0.1.0.exe
    echo.
    echo File sizes:
    for %%A in ("dist\QwenASR Translate\QwenASR Translate.exe") do echo   Executable: ~%%~zA bytes
    for %%A in ("installer_output\QwenASR-Translate-Setup-0.1.0.exe") do echo   Installer: ~%%~zA bytes
    echo.
) else (
    echo ========================================
    echo   PyInstaller Build Successful!
    echo   Inno Setup Build Failed
    echo ========================================
    echo.
    echo Executable:
    echo   dist\QwenASR Translate\QwenASR Translate.exe
    echo.
    echo Check Inno Setup script for errors.
    echo.
)

:skip_inno
pause
