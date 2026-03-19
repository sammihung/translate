@echo off
chcp 65001 >nul
title QwenASR - 啟動檢查

echo ============================================================
echo QwenASR Translate - 啟動檢查
echo ============================================================
echo.

REM 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤：未偵測到 Python
    echo.
    echo ============================================
    echo  請先安裝 Python 3.10 或更高版本
    echo ============================================
    echo.
    echo 安裝步驟:
    echo 1. 開啟 https://www.python.org/downloads/
    echo 2. 下載 Python 3.12
    echo 3. 執行安裝檔
    echo 4. 勾選 "Add Python to PATH"
    echo 5. 重啟電腦
    echo.
    
    set /p open="現在開啟下載頁面？(Y/N): "
    if /i "%open%"=="Y" start https://www.python.org/downloads/
    
    echo.
    pause
    exit /b 1
)

REM 檢查虛擬環境
if not exist ".venv" (
    echo ❌ 錯誤：虛擬環境不存在
    echo.
    echo 請先執行安裝:
    echo INSTALL.bat
    echo.
    pause
    exit /b 1
)

echo ✅ 環境檢查完成
echo.
echo 正在啟動 QwenASR...
echo.

call .venv\Scripts\activate.bat
python app.py

if errorlevel 1 (
    echo.
    echo ❌ 啟動失敗
    echo.
    echo 可能原因:
    echo 1. 缺少依賴套件
    echo 2. 模型未下載
    echo.
    echo 請重新執行安裝:
    echo INSTALL.bat
    echo.
    pause
    exit /b 1
)

pause
