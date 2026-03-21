"""
Qwen ASR Translate - 企業級語音翻譯系統

主進入點 (Entry Point)

使用方法:
    python -m qwen_asr.main
    或
    python src/qwen_asr/main.py
"""

import sys
from pathlib import Path

# 確保 src 目錄在 Python 路徑中
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from app import QwenASRApp


def main() -> None:
    """應用程式主函數"""
    try:
        # 創建並啟動應用程式
        app = QwenASRApp()
        app.run()
        
    except KeyboardInterrupt:
        print("\n👋 應用程式已終止")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ 應用程式錯誤：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
