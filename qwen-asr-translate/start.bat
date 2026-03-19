@echo off
chcp 65001 >nul
title QwenASR - CPU 模式

echo ============================================================
echo QwenASR 即時語音辨識與翻譯
echo ============================================================
echo.

REM 檢查虛擬環境
if not exist "venv\Scripts\activate.bat" (
    echo [錯誤] 未找到虛擬環境，請先執行安裝腳本：scripts\install.bat
    echo 或者手動執行：
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM 激活虛擬環境
call venv\Scripts\activate.bat

REM 啟動應用程式
echo.
echo 啟動應用程式...
python src/app.py

pause
