"""
測試音頻設備是否可以正常開啟
"""
import pyaudio
import sys

def test_device(device_index, device_name):
    """測試指定設備"""
    p = pyaudio.PyAudio()
    
    print(f"\n=== 測試設備 {device_index}: {device_name} ===")
    
    try:
        device_info = p.get_device_info_by_index(device_index)
        print(f"  預設取樣率：{device_info['defaultSampleRate']}")
        print(f"  最大輸入通道：{device_info['maxInputChannels']}")
        
        # 測試不同配置
        configs = [
            {"channels": 1, "rate": 16000},
            {"channels": 1, "rate": 48000},
            {"channels": 2, "rate": 48000},
        ]
        
        for config in configs:
            try:
                stream = p.open(
                    format=pyaudio.paFloat32,
                    channels=config["channels"],
                    rate=config["rate"],
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=1024
                )
                print(f"  [OK] 成功：{config['channels']} 通道，{config['rate']}Hz")
                stream.stop_stream()
                stream.close()
                return True  # 只要有一個成功就返回 True
            except Exception as e:
                print(f"  [FAIL] 失敗：{config['channels']} 通道，{config['rate']}Hz - {e}")
        
        return False
        
    except Exception as e:
        print(f"  [FAIL] 無法獲取設備信息：{e}")
        return False
    finally:
        p.terminate()

if __name__ == "__main__":
    # 測試 Stereo Mix (設備 12)
    device_idx = 12  # 根據之前的輸出，Stereo Mix 是設備 12
    device_name = "Stereo Mix"
    
    if len(sys.argv) > 1:
        device_idx = int(sys.argv[1])
    
    success = test_device(device_idx, device_name)
    
    if success:
        print(f"\n✅ 設備 {device_idx} 可以正常工作！")
    else:
        print(f"\n❌ 設備 {device_idx} 無法開啟。可能需要在 Windows 聲音設定中啟用。")
        print("\n啟用 Stereo Mix 的步驟:")
        print("1. 右鍵點擊工作列喇叭圖示 → 選擇『聲音』")
        print("2. 切換到『錄音』分頁")
        print("3. 找到 Stereo Mix，右鍵 → 啟用")
        print("4. 重新運行此測試")
