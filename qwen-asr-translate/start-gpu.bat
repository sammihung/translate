@echo off
chcp 65001 >nul
title QwenASR - GPU 模式

echo ============================================================
echo QwenASR 即時語音辨識與翻譯 - GPU 模式
echo ============================================================
echo.

REM 檢查虛擬環境
if not exist "venv\Scripts\activate.bat" (
    echo [錯誤] 未找到虛擬環境，請先執行:
    echo python -m venv venv
    echo venv\Scripts\activate
    echo pip install -r requirements.txt
    pause
    exit /b 1
)

REM 激活虛擬環境
call venv\Scripts\activate.bat

REM 檢查 GPU 模型
if not exist "GPUModel\qwen3-asr-1.7b.bin" (
    echo.
    echo [提示] 未找到 GPU 模型，是否現在下載？
    echo 模型大小：~2.3 GB
    set /p download="下載模型？(Y/N): "
    
    if /i "%download%"=="Y" (
        echo 正在下載模型...
        python downloader.py
    )
)

REM 啟動 GPU 版本
echo.
echo 啟動 GPU 模式...
python app_gpu.py

pause
