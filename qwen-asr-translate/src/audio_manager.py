"""
Audio Manager - 音訊設備管理與錄音
負責所有音訊相關的底層操作

🔧 優化 3: RMS 能量檢測 + 靜音判定
- 取代硬編碼 2 秒切割
- 使用音量 (RMS) 判斷靜音
- 支持可配置嘅靜音閾值同持續時間
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
        
        # 🔧 優化 3: RMS 能量檢測參數
        self.rms_threshold: float = 150.0  # 靜音閾值 (可調)
        self.silence_duration: float = 1.5  # 靜音持續時間 (秒)
        self.max_chunk_duration: float = 8.0  # 最大切片時長 (防止過長)
        
        # 錄音緩衝區
        self.audio_buffer: List[float] = []
        self.silence_start: Optional[float] = None
        self.chunk_start_time: Optional[float] = None
    
    def set_vad_params(self, rms_threshold: float = 150.0, silence_duration: float = 1.5, max_duration: float = 8.0) -> None:
        """
        設定 VAD 參數 (從 UI 傳入)
        
        Args:
            rms_threshold: RMS 靜音閾值 (越小越敏感)
            silence_duration: 靜音持續時間 (秒)
            max_duration: 最大切片時長 (秒)
        """
        self.rms_threshold = rms_threshold
        self.silence_duration = silence_duration
        self.max_chunk_duration = max_duration
        logger.info(f"VAD 參數已更新：RMS={rms_threshold}, 靜音={silence_duration}s, 最大={max_duration}s")
    
    def parse_device_index(self, device_string: str) -> Optional[int]:
        """
        從 UI 傳入嘅設備字串中解析出設備 Index
        
        例如輸入："麥克風 (Realtek(R) Audio) [2]" -> 回傳：2
        
        Args:
            device_string: UI 設備字串 (格式："設備名稱 [index]")
            
        Returns:
            設備 index (int)，如果係預設設備或解析失敗則返回 None
        """
        if not device_string or "預設" in device_string or "Default" in device_string:
            return None
        
        try:
            # 用 split 方法攔出中括號 [ ] 入面嘅數字
            index_str = device_string.split("[")[-1].split("]")[0]
            return int(index_str)
        except (IndexError, ValueError):
            # 如果解析失敗 (例如字串格式唔啱)，就 fallback 去預設設備
            return None
    
    def get_audio_devices(self) -> List[str]:
        """獲取所有可用音訊設備"""
        device_list: List[str] = []
        
        try:
            if self.p is None:
                self.p = pyaudio.PyAudio()
            
            device_count: int = self.p.get_device_count()
            
            for i in range(device_count):
                try:
                    device_info = self.p.get_device_info_by_index(i)
                    device_name: str = device_info.get('name', '')
                    max_input_channels: int = device_info.get('maxInputChannels', 0)
                    
                    # 只選有輸入通道的設備
                    if max_input_channels > 0 and device_name:
                        device_list.append(device_name)
                        
                except Exception as e:
                    logger.debug(f"設備 {i} 讀取失敗：{e}")
            
            logger.info(f"檢測到 {len(device_list)} 個音訊設備")
            
        except Exception as e:
            logger.error(f"獲取設備列表失敗：{e}", exc_info=True)
        
        return device_list
    
    def start_recording(self, device_index: Optional[int], callback: Callable[[np.ndarray], None]) -> None:
        """
        開始錄音 - 使用 RMS 能量檢測智能切割
        
        Args:
            device_index: 設備索引
            callback: 回調函數，接收音訊數據 (numpy array)
        """
        try:
            if self.p is None:
                self.p = pyaudio.PyAudio()
            
            self.is_recording = True
            
            # 🔧 優化 3: 重置緩衝區同狀態
            self.audio_buffer = []
            self.silence_start = None
            self.chunk_start_time = None
            
            stream_started: bool = False
            
            try:
                # 開啟音訊流 (16000Hz)
                self.stream = self.p.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=16000,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=1024
                )
                stream_started = True
                logger.info(f"音訊流已開啟：16000Hz, Mono, RMS 閾值={self.rms_threshold}")
                
            except Exception as e:
                logger.error(f"開啟音訊流失敗：{e}", exc_info=True)
                raise
            
            if not stream_started:
                raise Exception("無法開啟音訊流")
            
            import time
            last_callback_time: float = time.time()
            
            # 錄音主迴圈 - 智能切割
            while self.is_recording:
                try:
                    data = self.stream.read(1024, exception_on_overflow=False)
                    audio_np: np.ndarray = np.frombuffer(data, dtype=np.float32)
                    
                    # 計算當前 RMS 能量
                    rms: float = np.sqrt(np.mean(audio_np ** 2)) * 1000  # 放大方便計算
                    
                    current_time: float = time.time()
                    
                    # 檢查是否超過最大時長
                    max_duration_reached: bool = False
                    if self.chunk_start_time and (current_time - self.chunk_start_time) >= self.max_chunk_duration:
                        max_duration_reached = True
                    
                    # 添加到緩衝區
                    self.audio_buffer.extend(audio_np.tolist())
                    
                    # 🔧 優化 3: 智能切割邏輯
                    should_process: bool = False
                    
                    # 情況 1: 超過最大時長 → 強制切割
                    if max_duration_reached and len(self.audio_buffer) >= 16000 * 2:
                        should_process = True
                        logger.debug(f"達到最大時長 {self.max_chunk_duration}s，強制切割")
                        self.silence_start = None  # 重置靜音計時
                    
                    # 情況 2: 檢測到靜音 → 切割
                    elif rms < self.rms_threshold:
                        # 開始靜音計時
                        if self.silence_start is None:
                            self.silence_start = current_time
                        
                        # 靜音持續夠耐 → 切割
                        elif (current_time - self.silence_start) >= self.silence_duration:
                            if len(self.audio_buffer) >= 16000 * 1:  # 至少 1 秒
                                should_process = True
                                logger.debug(f"檢測到靜音 (RMS={rms:.1f} < {self.rms_threshold}), 切割")
                            self.silence_start = None  # 重置靜音計時
                    
                    else:
                        # 有聲音 → 重置靜音計時
                        self.silence_start = None
                    
                    # 執行切割
                    if should_process:
                        callback(np.array(self.audio_buffer))
                        self.audio_buffer = []  # 清空緩衝區
                        self.chunk_start_time = current_time  # 記錄新切片開始時間
                    
                    # 保險：如果緩衝區超過 10 秒，強制切割
                    if len(self.audio_buffer) >= 16000 * 10:
                        callback(np.array(self.audio_buffer))
                        self.audio_buffer = []
                        self.chunk_start_time = current_time
                    
                except Exception as e:
                    logger.error(f"錄音讀取錯誤：{e}")
                    break
            
        except Exception as e:
            logger.error(f"錄音啟動失敗：{e}", exc_info=True)
            raise
        finally:
            # 安全關閉音訊流
            self._close_stream()
    
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
