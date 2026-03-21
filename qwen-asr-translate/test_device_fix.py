"""測試設備索引修復"""
import sys
sys.path.insert(0, 'src')

from audio_manager import AudioManager

am = AudioManager()
devices = am.get_audio_devices()

print(f"檢測到 {len(devices)} 個設備:\n")

for i, device in enumerate(devices):
    print(f"{i+1}. {device}")
    
    # 測試 parse_device_index
    parsed = am.parse_device_index(device)
    print(f"   解析結果：{parsed}")
    
    if parsed is None:
        print(f"   ❌ 錯誤：解析失敗！")
    else:
        print(f"   ✅ 正確：索引 = {parsed}")
    
    print()

print(f"\n總計：{len(devices)} 個設備，全部應該有正確的索引格式")
