"""
測試引擎初始化 - 診斷錄音按鈕無法使用嘅問題
"""

import sys
import logging
from pathlib import Path

# 添加 src 到路徑
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from logging_config import setup_logging
from controller import AppController
from ai_controller import AIController
from audio_manager import AudioManager

# 設置日誌
logger = setup_logging(
    log_dir="logs",
    log_level=logging.DEBUG,
    console_output=True
)

print("=" * 60)
print("🔍 QwenASR 引擎初始化測試")
print("=" * 60)

try:
    # 1. 測試 Audio Manager
    print("\n[1/4] 測試 Audio Manager...")
    audio_mgr = AudioManager()
    devices = audio_mgr.get_audio_devices()
    print(f"✓ 檢測到 {len(devices)} 個音訊設備")
    if devices:
        print(f"  第一個設備：{devices[0]}")
    
    # 2. 測試 AI Controller
    print("\n[2/4] 測試 AI Controller...")
    ai_ctrl = AIController()
    print(f"✓ AI Controller 已創建")
    
    # 3. 測試 App Controller
    print("\n[3/4] 測試 App Controller...")
    app_ctrl = AppController()
    print(f"✓ App Controller 已創建")
    print(f"  GPU 檢測：{app_ctrl.has_gpu}")
    if app_ctrl.has_gpu:
        print(f"  GPU VRAM: {app_ctrl.gpu_vram_gb:.1f} GB")
    
    # 4. 測試引擎初始化
    print("\n[4/4] 初始化引擎...")
    
    def progress_callback(status: str):
        print(f"  → {status}")
    
    success = app_ctrl.initialize_engines(progress_callback=progress_callback)
    
    if success:
        print("\n✅ 引擎初始化成功！")
        print(f"  ASR 引擎：{ai_ctrl.asr_engine is not None}")
        print(f"  翻譯引擎：{ai_ctrl.translate_engine is not None}")
        print(f"  引擎就緒：{app_ctrl.is_engines_ready()}")
    else:
        print("\n❌ 引擎初始化失敗 (success=False)")
        
except Exception as e:
    print(f"\n❌ 初始化異常：{e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("測試完成")
print("=" * 60)
