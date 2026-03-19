"""
Audio Manager - 音訊設備管理與錄音
負責所有音訊相關的底層操作
"""

import pyaudio
import numpy as np
from typing import List, Optional, Callable
import threading


class AudioManager:
    """音訊管理器 - 處理設備枚舉和錄音"""
    
    def __init__(self):
        self.p = None
        self.stream = None
        self.is_recording = False
        self._stream_lock = threading.Lock()
    
    def get_audio_devices(self) -> List[str]:
        """獲取音訊輸入裝置列表"""
        self.p = pyaudio.PyAudio()
        devices = []
        
        try:
            for i in range(self.p.get_device_count()):
                try:
                    info = self.p.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0:
                        device_name = info['name']
                        device_idx = f"{i}: {device_name}"
                        
                        # 標記系統音源設備
                        if any(keyword in device_name.lower() for keyword in 
                               ['stereo mix', '立體聲混音', 'wave out', 'what u hear', 
                                'virtual audio', 'vb-audio', 'voicemeeter']):
                            device_idx = f"{i}: {device_name} 🎵 (系統音源)"
                        
                        devices.append(device_idx)
                except Exception as e:
                    print(f"Error getting device {i}: {e}")
                    pass
        finally:
            self.p.terminate()
            self.p = None
        
        # 確保有預設選項
        if not devices:
            devices = ["預設麥克風"]
        
        return devices
    
    def parse_device_index(self, device_text: str) -> int:
        """從裝置文字解析設備索引"""
        if ":" in device_text:
            try:
                return int(device_text.split(":")[0])
            except ValueError:
                return 0
        return 0
    
    def start_recording(self, device_index: int, callback: Callable[[np.ndarray], None]):
        """
        開始錄音
        
        Args:
            device_index: 設備索引
            callback: 回調函數，接收音訊數據 (numpy array)
        """
        if self.p is None:
            self.p = pyaudio.PyAudio()
        
        self.is_recording = True
        stream_started = False
        
        try:
            # 嘗試開啟音訊流，處理可能的錯誤
            try:
                # 嘗試 16000Hz (ASR 模型要求)
                self.stream = self.p.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=16000,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=1024
                )
                stream_started = True
            except Exception as e:
                # 如果 16000Hz 失敗，嘗試使用裝置預設取樣率
                try:
                    device_info = self.p.get_device_info_by_index(device_index)
                    sample_rate = int(device_info.get('defaultSampleRate', 48000))
                    print(f"使用裝置預設取樣率：{sample_rate}Hz")
                    
                    self.stream = self.p.open(
                        format=pyaudio.paFloat32,
                        channels=1,
                        rate=sample_rate,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=1024
                    )
                    stream_started = True
                except Exception as e2:
                    # Stereo Mix 可能需要在 Windows 聲音設定中啟用
                    print(f"使用 Stereo Mix 模式：48000Hz, Stereo")
                    self.stream = self.p.open(
                        format=pyaudio.paFloat32,
                        channels=2,  # Stereo Mix 通常是立體聲
                        rate=48000,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=1024
                    )
                    stream_started = True
            
            if not stream_started:
                raise Exception("無法開啟音訊流")
            
            audio_buffer = []
            
            # 錄音主迴圈
            while self.is_recording:
                try:
                    data = self.stream.read(1024, exception_on_overflow=False)
                    audio_np = np.frombuffer(data, dtype=np.float32)
                    audio_buffer.extend(audio_np.tolist())
                    
                    # 每 2 秒處理一次
                    if len(audio_buffer) >= 16000 * 2:
                        # 透過 callback 傳遞音訊數據
                        callback(np.array(audio_buffer))
                        audio_buffer = audio_buffer[-3200:]  # 保留最後 2.0 秒作為重疊緩衝
                
                except Exception as e:
                    print(f"錄音讀取錯誤：{e}")
                    break
        
        except Exception as e:
            print(f"錄音錯誤：{e}")
            raise
        finally:
            # 安全關閉音訊流
            self._close_stream()
    
    def _close_stream(self):
        """關閉音訊流"""
        with self._stream_lock:
            if self.stream is not None:
                try:
                    if self.stream.is_active():
                        self.stream.stop_stream()
                    self.stream.close()
                except Exception as e:
                    print(f"關閉音訊流時出錯：{e}")
                finally:
                    self.stream = None
            
            if self.p is not None:
                try:
                    self.p.terminate()
                except Exception as e:
                    print(f"終結 PyAudio 時出錯：{e}")
                finally:
                    self.p = None
    
    def stop_recording(self):
        """停止錄音"""
        self.is_recording = False
        # 等待 stream 在背景線程中安全關閉
        import time
        time.sleep(0.3)
    
    def cleanup(self):
        """清理資源"""
        self.is_recording = False
        self._close_stream()
