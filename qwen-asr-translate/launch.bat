@echo off
chcp 65001 >nul
echo ========================================
echo Qwen ASR Translate - Launcher
echo ========================================
echo.

cd /d C:\Users\sherm\translate\qwen-asr-translate

echo Installing missing dependencies...
.venv\Scripts\pip.exe install pydantic pydantic-settings python-dotenv --quiet

echo Starting application...
echo.

.venv\Scripts\python.exe src\qwen_asr_app\main.py

pause
