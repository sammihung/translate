@echo off
chcp 65001 >nul
title QwenASR 模型下載

echo ============================================================
echo QwenASR 模型下載器
echo ============================================================
echo.

REM 檢查虛擬環境
if not exist "venv\Scripts\python.exe" (
    echo [錯誤] 未找到虛擬環境，請先執行 install.bat
    pause
    exit /b 1
)

REM 執行下載器
call venv\Scripts\activate.bat
python downloader.py

echo.
echo 模型下載完成！
echo 現在可以執行 start.bat 啟動程式
echo.

pause
