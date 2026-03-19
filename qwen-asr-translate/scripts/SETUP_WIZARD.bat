@echo off
chcp 65001 >nul
title QwenASR - 完整安裝精靈

echo ============================================================
echo QwenASR Translate - 完整安裝精靈
echo ============================================================
echo.
echo 本精靈將協助您完成所有安裝步驟
echo.
pause

REM 步驟 1: 檢查 Python
echo.
echo [步驟 1/5] 檢查 Python...
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

REM 步驟 2: 建立虛擬環境
echo.
echo [步驟 2/5] 建立虛擬環境...
if exist "venv" (
    echo 虛擬環境已存在，跳過
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 建立虛擬環境失敗
        pause
        exit /b 1
    )
    echo ✅ 虛擬環境已建立
)

REM 步驟 3: 啟動虛擬環境並升級 pip
echo.
echo [步驟 3/5] 升級 pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet

REM 步驟 4: 安裝依賴
echo.
echo [步驟 4/5] 安裝依賴套件...
echo 這可能需要 5-15 分鐘，請耐心等待...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ⚠️ 部分套件安裝失敗，嘗試個別安裝...
    echo.
    pip install customtkinter numpy requests tqdm
    pip install openvino openvino-dev
    pip install onnxruntime
    pip install soundfile librosa
    pip install transformers sentencepiece
    pip install pyaudio || (
        echo.
        echo 嘗試使用 pipwin 安裝 PyAudio...
        pip install pipwin
        pipwin install pyaudio
    )
)

REM 步驟 5: 檢查環境
echo.
echo [步驟 5/5] 檢查安裝結果...
python setup_checker.py

echo.
echo ============================================================
echo 安裝完成！
echo ============================================================
echo.
echo 接下來請執行以下命令下載模型:
echo   download-models.bat
echo.
echo 或直接執行:
echo   start.bat
echo (程式會提示下載模型)
echo.
pause
