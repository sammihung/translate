@echo off
chcp 65001 >nul
title QwenASR - 全自動安裝程式 (含 Python)

echo ============================================================
echo QwenASR Translate - 全自動安裝程式
echo ============================================================
echo.
echo 這個程式會自動:
echo 1. 下載並安裝 Python 3.12
echo 2. 建立虛擬環境
echo 3. 安裝所有依賴套件
echo 4. 啟動應用程式
echo.
echo 整個過程約需 10-20 分鐘
echo.
pause

REM 建立臨時目錄
set TEMP_DIR=%TEMP%\qwen-asr-install
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

REM 步驟 1: 下載 Python
echo.
echo ============================================================
echo [步驟 1/4] 下載 Python 3.12
echo ============================================================
echo.
echo 正在從 python.org 下載 Python 3.12...
echo.

set PYTHON_URL=https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe
set PYTHON_EXE=%TEMP_DIR%\python-installer.exe

REM 使用 PowerShell 下載
powershell -Command "& {Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_EXE%' -UseBasicParsing}"

if exist "%PYTHON_EXE%" (
    echo ✅ Python 下載完成
) else (
    echo ❌ Python 下載失敗
    echo.
    echo 請手動下載:
    echo 1. 開啟 https://www.python.org/downloads/
    echo 2. 下載 Python 3.12
    echo 3. 執行安裝檔，勾選 "Add Python to PATH"
    echo 4. 重啟電腦後重新執行這個腳本
    echo.
    pause
    exit /b 1
)

REM 步驟 2: 安裝 Python
echo.
echo ============================================================
echo [步驟 2/4] 安裝 Python 3.12
echo ============================================================
echo.
echo 正在安裝 Python...
echo 請等待安裝完成...
echo.

REM 靜音安裝，自動加入 PATH
"%PYTHON_EXE%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

REM 等待幾秒讓 PATH 更新
timeout /t 5 /nobreak >nul

REM 驗證安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Python 安裝完成但需要重啟
    echo.
    echo 請重啟電腦後重新執行這個腳本
    echo.
    pause
    exit /b 0
) else (
    echo ✅ Python 已安裝
    python --version
)

REM 步驟 3: 複製檔案到使用者目錄
echo.
echo ============================================================
echo [步驟 3/4] 設定應用程式
echo ============================================================
echo.

set TARGET_DIR=%USERPROFILE%\qwen-asr-app
echo 目標目錄：%TARGET_DIR%
echo.

if not exist "%TARGET_DIR%" (
    echo 建立目錄...
    mkdir "%TARGET_DIR%"
)

echo 複製應用程式檔案...
robocopy "%~dp0" "%TARGET_DIR%" /E /XD venv .venv .git ov_models GPUModel ffmpeg subtitles logs %TEMP_DIR% /NFL /NDL /NJH /NJS

cd /d "%TARGET_DIR%"
echo ✅ 應用程式已設定

REM 步驟 4: 建立虛擬環境並安裝依賴
echo.
echo ============================================================
echo [步驟 4/4] 安裝依賴套件
echo ============================================================
echo.

if exist ".venv" (
    echo 移除舊的虛擬環境...
    rmdir /s /q ".venv"
)

echo 建立虛擬環境...
python -m venv .venv
if errorlevel 1 (
    echo ❌ 建立虛擬環境失敗
    pause
    exit /b 1
)

echo 啟動虛擬環境...
call .venv\Scripts\activate.bat

echo 升級 pip...
python -m pip install --upgrade pip --quiet

echo 安裝依賴套件...
echo 這可能需要 10-15 分鐘，請耐心等待...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo ⚠️ 部分套件安裝失敗，嘗試個別安裝...
    pip install customtkinter numpy requests tqdm
    pip install pyaudio || pip install pipwin && pipwin install pyaudio
    pip install openvino openvino-dev
    pip install onnxruntime soundfile librosa
    pip install transformers sentencepiece
)

echo.
echo ✅ 依賴套件已安裝

REM 清理
echo.
echo 清理臨時檔案...
del /q "%PYTHON_EXE%" 2>nul
rmdir /s /q "%TEMP_DIR%" 2>nul

REM 完成
echo.
echo ============================================================
echo 安裝完成！
echo ============================================================
echo.
echo 應用程式位置：%TARGET_DIR%
echo.
echo 正在啟動 QwenASR...
echo.

python app.py

echo.
echo ============================================================
echo 提示
echo ============================================================
echo.
echo 之後啟動請執行:
echo %TARGET_DIR%\quick-start.bat
echo.
echo 或雙擊桌面上的捷徑
echo.

pause
