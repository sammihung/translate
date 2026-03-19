@echo off
chcp 65001 >nul
title QwenASR - 安裝程式

echo ============================================================
echo QwenASR 安裝程式
echo ============================================================
echo.

REM 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未檢測到 Python，請先安裝 Python 3.10+
    echo 下載連結：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [✓] Python 已安裝
echo.

REM 創建虛擬環境
if not exist "venv" (
    echo 正在創建虛擬環境...
    python -m venv venv
    echo [✓] 虛擬環境創建完成
) else (
    echo [✓] 虛擬環境已存在
)
echo.

REM 激活虛擬環境
echo 正在激活虛擬環境...
call venv\Scripts\activate.bat

REM 安裝依賴
echo 正在安裝依賴套件...
pip install --upgrade pip
pip install -r requirements.txt
echo [✓] 依賴安裝完成
echo.

REM 檢查是否下載模型
if not exist "GPUModel\qwen3-asr-1.7b.bin" (
    echo.
    echo [提示] 未找到 GPU 模型
    set /p download="是否現在下載 GPU 模型？(Y/N): "
    
    if /i "%download%"=="Y" (
        echo 正在下載模型...
        python download-models.bat
    )
)

echo.
echo ============================================================
echo 安裝完成！
echo ============================================================
echo.
echo 下一步：
echo   1. 關閉此視窗
echo   2. 雙擊 start.bat (CPU 模式) 或 start-gpu.bat (GPU 模式)
echo.
pause
