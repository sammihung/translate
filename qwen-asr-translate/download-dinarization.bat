@echo off
chcp 65001 >nul
echo.
echo ===============================================
echo QwenASR 模型下載器 - 說話者分離模型
echo ===============================================
echo.
echo 正在下載說話者分離模型...
echo.

cd /d "%~dp0"

REM 創建模型目錄
if not exist "ov_models\dinarization" mkdir "ov_models\dinarization"

REM 使用 downloader.py 下載
python downloader.py <<EOF
4
q
EOF

echo.
echo ===============================================
echo 下載完成！
echo ===============================================
echo.
echo 請確保已設定 HuggingFace Token 以使用說話者分離功能
echo 設定方法：
echo 1. 取得 token: https://huggingface.co/settings/tokens
echo 2. 設定環境變數：set HF_TOKEN=your_token_here
echo.
pause
