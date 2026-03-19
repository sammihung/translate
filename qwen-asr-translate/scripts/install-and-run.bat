@echo off
chcp 65001 >nul
title QwenASR - 一鍵安裝與啟動

echo ============================================================
echo QwenASR Translate - 一鍵安裝與啟動
echo ============================================================
echo.

REM 設定目標目錄
set TARGET_DIR=%USERPROFILE%\qwen-asr-app
echo 目標目錄：%TARGET_DIR%
echo.

REM 檢查目標目錄
if not exist "%TARGET_DIR%" (
    echo [步驟 1/6] 建立專案目錄...
    mkdir "%TARGET_DIR%"
    echo ✅ 目錄已建立
) else (
    echo [步驟 1/6] 專案目錄已存在
)

REM 複製專案檔案
echo.
echo [步驟 2/6] 複製專案檔案...
robocopy "%~dp0" "%TARGET_DIR%" /E /XD venv .venv .git ov_models GPUModel ffmpeg subtitles logs /NFL /NDL /NJH /NJS
echo ✅ 檔案已複製

cd /d "%TARGET_DIR%"

REM 檢查 Python
echo.
echo [步驟 3/6] 檢查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ 未偵測到 Python
    echo.
    echo 請先安裝 Python 3.10 或更高版本
    echo 下載連結：https://www.python.org/downloads/
    echo.
    echo 安裝時請務必勾選 "Add Python to PATH"
    echo.
    pause
    exit /b 1
) else (
    python --version
    echo ✅ Python 已安裝
)

REM 建立虛擬環境
echo.
echo [步驟 4/6] 建立虛擬環境...
if exist ".venv" (
    echo 虛擬環境已存在，跳過
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ 建立虛擬環境失敗
        pause
        exit /b 1
    )
    echo ✅ 虛擬環境已建立
)

REM 啟動虛擬環境並安裝依賴
echo.
echo [步驟 5/6] 安裝依賴套件...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
echo 正在安裝套件，這可能需要 5-15 分鐘...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo.
    echo ⚠️ 部分套件安裝失敗，嘗試重新安裝...
    pip install customtkinter numpy requests tqdm pyaudio
    pip install openvino openvino-dev
    pip install onnxruntime soundfile librosa
    pip install transformers sentencepiece
)
echo ✅ 依賴套件已安裝

REM 檢查環境
echo.
echo [步驟 6/6] 檢查安裝結果...
python setup_checker.py --quiet

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

pause
