"""
Qwen ASR Translate - 企業級語音翻譯系統

主進入點 (Entry Point)
"""

import sys
from pathlib import Path

# 確保 src 目錄在 Python 路徑中
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# ✅ 修正 1：使用絕對路徑，並匯入正確的類別名稱 App
from qwen_asr_app.app import App

def main() -> None:
    """應用程式主函數"""
    try:
        # ✅ 修正 2：實例化 App
        app = App()
        
        # ✅ 修正 3：Tkinter / CustomTkinter 的正確啟動方法是 mainloop()
        app.mainloop()
        
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