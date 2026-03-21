"""
VAD (Voice Activity Detection) 靜音偵測與音訊分段
使用 Silero VAD 模型
"""

import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path
import onnxruntime as ort
from qwen_asr_app.core.logging_config import get_logger

logger = get_logger(__name__)


class VADProcessor:
    """語音活動偵測處理器"""
    
    def __init__(self, model_path: Optional[str] = None) -> None:
        """
        初始化 VAD 處理器
        
        Args:
            model_path: ONNX 模型路徑（如無則使用預設）
        """
        self.model_path: Optional[str] = model_path
        self.session: Optional[ort.InferenceSession] = None
        self.sample_rate: int = 16000
        self.state: Optional[np.ndarray] = None  # RNN 狀態
        
        # VAD 參數
        self.threshold: float = 0.35  # 語音閾值（降低到 0.35，更敏感以捕捉小聲說話）
        self.min_speech_duration: float = 0.2  # 最小語音長度（秒）- 降低到 0.2 秒，捕捉短語
        self.min_silence_duration: float = 1.2  # 最小靜音長度（秒）- 增加到 1.2 秒，避免切斷慢速說話或停頓
        
        self._load_model()
    
    def _load_model(self) -> None:
        """載入 Silero VAD 模型"""
        try:
            if self.model_path is None:
                # 嘗試從 silero-vad 套件目錄載入模型
                import silero_vad
                package_dir = Path(silero_vad.__file__).parent
                self.model_path = str(package_dir / "data" / "silero_vad.onnx")
            
            if not Path(self.model_path).exists():
                raise FileNotFoundError(f"VAD 模型不存在：{self.model_path}")
            
            # 載入 ONNX 模型
            self.session = ort.InferenceSession(self.model_path)
            
            # 獲取模型輸入信息
            inputs = self.session.get_inputs()
            self.input_names: List[str] = [inp.name for inp in inputs]
            
            # 初始化 RNN 狀態 (根據模型結構)
            self._init_state()
            
            logger.info(f"[OK] VAD model loaded: {self.model_path}")
            logger.debug(f"VAD Inputs: {self.input_names}")
            
        except Exception as e:
            logger.error(f"VAD 模型載入失敗：{e}", exc_info=True)
            raise
    
    def _init_state(self) -> None:
        """初始化 RNN 狀態"""
        # Silero VAD 需要 2 層 LSTM，每層 128 個單元
        # 狀態格式：[num_layers, batch_size, hidden_size]
        self.state = np.zeros((2, 1, 128), dtype=np.float32)
        logger.debug("VAD RNN 狀態已初始化")
    
    def reset(self) -> None:
        """重置 VAD 狀態（用於重新開始檢測）"""
        self._init_state()
        logger.debug("VAD 狀態已重置")
    
    def detect_speech(self, audio: np.ndarray, sample_rate: int = 16000) -> float:
        """
        對單幀音訊進行 VAD 檢測
        
        Args:
            audio: 音訊數據 (float32, mono)
            sample_rate: 取樣率
            
        Returns:
            語音概率 (0.0-1.0)
        """
        try:
            # 確保音訊是正確格式
            if len(audio.shape) == 1:
                audio = audio.reshape(1, -1)
            
            # 構建輸入
            ort_inputs = {
                'input': audio.astype(np.float32),
                'state': self.state,
                'sr': np.array(sample_rate, dtype=np.int64)
            }
            
            # 執行推理
            output, self.state = self.session.run(None, ort_inputs)
            
            # 返回語音概率
            prob: float = float(output[0, 0])
            return prob
            
        except Exception as e:
            logger.error(f"VAD 檢測失敗：{e}", exc_info=True)
            return 0.0
    
    def detect_speech_segments(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> List[Tuple[float, float]]:
        """
        偵測語音段落
        
        Args:
            audio: 音訊數據 (float32, mono)
            sample_rate: 取樣率
            
        Returns:
            語音段落列表 [(start, end), ...]，時間單位為秒
        """
        try:
            # 重取樣
            if sample_rate != self.sample_rate:
                from librosa import resample
                audio = resample(audio, orig_sr=sample_rate, target_sr=self.sample_rate)
                sample_rate = self.sample_rate
                logger.debug(f"音訊已重取樣至 {self.sample_rate}Hz")
            
            # 重置狀態
            self.reset()
            
            # 分幀處理
            frame_size_samples: int = int(self.sample_rate * 0.04)  # 40ms
            segments: List[Tuple[float, float]] = []
            
            is_speech: bool = False
            speech_start: float = 0
            silence_counter: int = 0
            speech_counter: int = 0
            
            for i in range(0, len(audio), frame_size_samples):
                frame = audio[i:i + frame_size_samples]
                
                if len(frame) < frame_size_samples:
                    frame = np.pad(frame, (0, frame_size_samples - len(frame)))
                
                # 執行 VAD 推理
                prob: float = self.detect_speech(frame, self.sample_rate)
                
                # 判斷是否為語音
                if prob > self.threshold:
                    speech_counter += 1
                    silence_counter = 0
                    if not is_speech and speech_counter >= 2:  # 連續 2 幀語音
                        is_speech = True
                        speech_start = i / self.sample_rate
                else:
                    silence_counter += 1
                    speech_counter = 0
                    if is_speech and silence_counter >= int(self.min_silence_duration / 0.04):
                        # 語音結束
                        speech_end: float = i / self.sample_rate
                        duration: float = speech_end - speech_start
                        
                        if duration >= self.min_speech_duration:
                            segments.append((speech_start, speech_end))
                            logger.debug(f"偵測到語音段落：{speech_start:.2f}s - {speech_end:.2f}s ({duration:.2f}s)")
                        
                        is_speech = False
                        silence_counter = 0
            
            # 處理最後一段
            if is_speech:
                speech_end = len(audio) / self.sample_rate
                duration = speech_end - speech_start
                if duration >= self.min_speech_duration:
                    segments.append((speech_start, speech_end))
                    logger.debug(f"偵測到最後語音段落：{speech_start:.2f}s - {speech_end:.2f}s")
            
            logger.info(f"VAD 偵測完成：共 {len(segments)} 個語音段落")
            return segments
            
        except Exception as e:
            logger.error(f"VAD 語音段落偵測失敗：{e}", exc_info=True)
            return []
