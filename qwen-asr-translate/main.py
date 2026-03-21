import sys
from pathlib import Path

# 1. 取得專案根目錄與 src 目錄的絕對路徑
root_dir = Path(__file__).parent.absolute()
src_path = root_dir / "src"

# 2. 關鍵加固：確保 src 被排在 sys.path 的最前面
# 這樣 Python 會優先從 src 資料夾找你的 qwen_asr_app
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 3. 從你重新命名後的套件中匯入啟動函數
try:
    from qwen_asr_app.main import main as start_app
except ImportError as e:
    print(f"❌ 匯入錯誤：找不到 qwen_asr_app 套件。請確認 src 目錄下是否有 qwen_asr_app 資料夾。")
    print(f"錯誤訊息: {e}")
    sys.exit(1)

if __name__ == "__main__":
    start_app()