"""測試 ASR 模型載入"""
import sys
sys.path.insert(0, '.')

print("測試 1: 檢查 qwen_asr 模組...")
try:
    from qwen_asr import Qwen3ASRModel
    print("✅ qwen_asr 模組載入成功")
except Exception as e:
    print(f"❌ qwen_asr 載入失敗：{e}")
    sys.exit(1)

print("\n測試 2: 檢查 asr_engine 模組...")
try:
    from asr_engine import QwenASREngine
    print("✅ asr_engine 模組載入成功")
except Exception as e:
    print(f"❌ asr_engine 載入失敗：{e}")
    sys.exit(1)

print("\n測試 3: 初始化 ASR 引擎...")
try:
    engine = QwenASREngine(model_name="Qwen/Qwen3-ASR-0.6B", device="cpu")
    print("✅ ASR 引擎初始化成功")
    print(f"   模型名稱：{engine.model_name}")
    print(f"   裝置：{engine.device}")
except Exception as e:
    print(f"❌ ASR 引擎初始化失敗：{e}")

print("\n測試 4: 載入 ASR 模型（可能需要幾分鐘）...")
try:
    engine.load_model()
    if engine.loaded:
        print("✅ ASR 模型載入成功！")
        print("   可以開始使用語音辨識功能")
    else:
        print("⚠️ ASR 模型載入失敗，但應用程式仍可運行（使用 VAD + 翻譯）")
except Exception as e:
    print(f"❌ 模型載入錯誤：{e}")
    print("⚠️ 應用程式仍可使用 VAD 和翻譯功能")

print("\n✅ 所有測試完成！")
