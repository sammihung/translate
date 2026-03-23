@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   QwenASR Translate - 環境凍結工具
echo   Freeze Environment for Deployment
echo ========================================
echo.

REM 檢查 Python
echo [1/4] 檢查 Python 環境...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 錯誤：未找到 Python
    pause
    exit /b 1
)

python --version
echo.

REM 升級 uv
echo [2/4] 升級 uv 套件管理器...
python -m pip install --upgrade uv
echo.

REM 生成凍結的依賴
echo [3/4] 生成凍結的依賴版本...
uv pip compile pyproject.toml --output-file requirements-freeze.txt

if exist "requirements-freeze.txt" (
    echo ✅ 已生成 requirements-freeze.txt
    echo.
    echo 內容預覽：
    type requirements-freeze.txt | findstr /C:"torch" /C:"numpy" /C:"customtkinter"
    echo.
) else (
    echo ❌ 生成失敗
    pause
    exit /b 1
)

REM 顯示環境資訊
echo [4/4] 收集環境資訊...
echo.

echo Python 版本:
python --version
echo.

echo 已安裝套件版本：
echo torch:
python -c "import torch; print(f'  {torch.__version__}')"
echo.
echo torchaudio:
python -c "import torchaudio; print(f'  {torchaudio.__version__}')"
echo.
echo CUDA Available:
python -c "import torch; print(f'  {torch.cuda.is_available()}')"
if torch.cuda.is_available == "True" (
    echo GPU Name:
    python -c "import torch; print(f'  {torch.cuda.get_device_name(0)}')"
    echo GPU VRAM:
    python -c "import torch; vram = torch.cuda.get_device_properties(0).total_memory / (1024**3); print(f'  {vram:.2f} GB')"
)
echo.
echo customtkinter:
python -c "import customtkinter; print(f'  {customtkinter.__version__}')"
echo.
echo qwen_asr:
python -c "import qwen_asr; print(f'  {qwen_asr.__version__}')" 2>nul || echo "  未安裝 (將在打包時安裝)"
echo.

echo ========================================
echo   ✅ 環境凍結完成！
echo ========================================
echo.
echo 生成的檔案：
echo   - requirements-freeze.txt (凍結的依賴版本)
echo   - VERSION.txt (版本資訊)
echo   - qwen_asr.spec (PyInstaller 配置)
echo   - build_exe.bat (一鍵打包腳本)
echo.
echo 下一步：
echo   1. 執行 build_exe.bat 打包成 .exe
echo   2. 將 dist\ 資料夾分發給用戶
echo   3. 或推送到 GitHub 自動打包
echo.

pause
