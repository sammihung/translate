"""
Qwen ASR Translate - 根目錄啟動腳本

使用方法:
    python main.py
    或
    uv run main.py
"""

import sys
from pathlib import Path

# 將 src 加入環境變數，確保 Python 找得到 qwen_asr 套件
root_dir = Path(__file__).parent
src_path = root_dir / "src"

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 從套件啟動應用程式
from qwen_asr.main import main

if __name__ == "__main__":
    main()
