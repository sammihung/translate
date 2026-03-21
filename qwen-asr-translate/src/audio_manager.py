"""
Audio Manager - 音訊設備管理與錄音
負責所有音訊相關的底層操作
"""

import pyaudio
import numpy as np
from typing import List, Optional, Callable
import threading
from logging_config import get_logger

logger = get_logger(__name__)


class AudioManager:
    """音訊管理器 - 處理設備枚舉和錄音"""
    
    def __init__(self) -> None:
        self.p: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        self.is_recording: bool = False
        self._stream_lock: threading.Lock = threading.Lock()
    
    def get_audio_devices(self) -> List[str]:
        """獲取音訊輸入裝置列表"""
        try:
            self.p = pyaudio.PyAudio()
            devices: List[str] = []
            
            try:
                for i in range(self.p.get_device_count()):
                    try:
                        info = self.p.get_device_info_by_index(i)
                        if info['maxInputChannels'] > 0:
                            device_name: str = info['name']
                            device_idx: str = f"{i}: {device_name}"
                            
                            # 標記系統音源設備
                            if any(keyword in device_name.lower() for keyword in 
                                   ['stereo mix', '立體聲混音', 'wave out', 'what u hear', 
                                    'virtual audio', 'vb-audio', 'voicemeeter']):
                                device_idx = f"{i}: {device_name} 🎵 (系統音源)"
                            
                            devices.append(device_idx)
                    except Exception as e:
                        logger.debug(f"Error getting device {i}: {e}")
                        pass
            finally:
                self.p.terminate()
                self.p = None
            
            # 確保有預設選項
            if not devices:
                devices = ["預設麥克風"]
                logger.warning("未檢測到音訊設備，使用預設選項")
            
            logger.info(f"檢測到 {len(devices)} 個音訊設備")
            return devices
            
        except Exception as e:
            logger.error(f"獲取音訊設備失敗：{e}", exc_info=True)
            return ["預設麥克風"]
    
    def parse_device_index(self, device_text: str) -> int:
        """從裝置文字解析設備索引"""
        try:
            if ":" in device_text:
                return int(device_text.split(":")[0])
            return 0
        except ValueError:
            logger.warning(f"無法解析設備索引：{device_text}")
            return 0
    
    def start_recording(
        self,
        device_index: int,
        callback: Callable[[np.ndarray], None]
    ) -> None:
        """
        開始錄音
        
        Args:
            device_index: 設備索引
            callback: 回調函數，接收音訊數據 (numpy array)
        """
        try:
            if self.p is None:
                self.p = pyaudio.PyAudio()
            
            self.is_recording = True
            stream_started: bool = False
            
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
                    logger.info(f"音訊流已開啟：16000Hz, Mono")
                    
                except Exception as e:
                    # 如果 16000Hz 失敗，嘗試使用裝置預設取樣率
                    try:
                        device_info = self.p.get_device_info_by_index(device_index)
                        sample_rate: int = int(device_info.get('defaultSampleRate', 48000))
                        logger.info(f"使用裝置預設取樣率：{sample_rate}Hz")
                        
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
                        logger.warning(f"使用 Stereo Mix 模式：48000Hz, Stereo")
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
                
                audio_buffer: List[float] = []
                
                # 錄音主迴圈
                while self.is_recording:
                    try:
                        data = self.stream.read(1024, exception_on_overflow=False)
                        audio_np: np.ndarray = np.frombuffer(data, dtype=np.float32)
                        audio_buffer.extend(audio_np.tolist())
                        
                        # 每 2 秒處理一次
                        if len(audio_buffer) >= 16000 * 2:
                            # 透過 callback 傳遞音訊數據
                            callback(np.array(audio_buffer))
                            audio_buffer = audio_buffer[-3200:]  # 保留最後 2.0 秒作為重疊緩衝
                    
                    except Exception as e:
                        logger.error(f"錄音讀取錯誤：{e}")
                        break
            
            except Exception as e:
                logger.error(f"錄音錯誤：{e}", exc_info=True)
                raise
            finally:
                # 安全關閉音訊流
                self._close_stream()
                
        except Exception as e:
            logger.error(f"錄音啟動失敗：{e}", exc_info=True)
            raise
    
    def _close_stream(self) -> None:
        """關閉音訊流"""
        try:
            with self._stream_lock:
                if self.stream is not None:
                    try:
                        if self.stream.is_active():
                            self.stream.stop_stream()
                        self.stream.close()
                        logger.debug("音訊流已關閉")
                    except Exception as e:
                        logger.error(f"關閉音訊流時出錯：{e}")
                    finally:
                        self.stream = None
                
                if self.p is not None:
                    try:
                        self.p.terminate()
                        logger.debug("PyAudio 已終結")
                    except Exception as e:
                        logger.error(f"終結 PyAudio 時出錯：{e}")
                    finally:
                        self.p = None
        except Exception as e:
            logger.error(f"關閉音訊流失敗：{e}", exc_info=True)
    
    def stop_recording(self) -> None:
        """停止錄音"""
        logger.info("正在停止錄音...")
        self.is_recording = False
        # 等待 stream 在背景線程中安全關閉
        import time
        time.sleep(0.3)
    
    def cleanup(self) -> None:
        """清理資源"""
        logger.info("正在清理音訊資源...")
        self.is_recording = False
        self._close_stream()
        logger.info("音訊資源已清理")
