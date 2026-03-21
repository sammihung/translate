"""
Qwen3-ASR 推理引擎 - 使用官方 qwen-asr 套件
基於 Transformers 後端，支持流式推理
"""

import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
import torch
import requests
import json
from logging_config import get_logger

logger = get_logger(__name__)


class SpeakerDiarization:
    """說話者分離模組 - 使用 PyAnnote"""
    
    def __init__(self) -> None:
        """初始化說話者分離"""
        self.pipeline = None
        self.loaded: bool = False
        self.min_speakers: int = 1
        self.max_speakers: int = 4
        
    def load_pipeline(self) -> None:
        """載入 PyAnnote 說話者分離模型"""
        if self.loaded:
            return
        
        logger.info("Loading Speaker Diarization pipeline...")
        
        try:
            from pyannote.audio import Pipeline
            
            # 使用預訓練模型（需要 HuggingFace token）
            try:
                from huggingface_hub import login
                import os
                token: Optional[str] = os.getenv("HF_TOKEN")
                if token:
                    login(token=token)
                    logger.info("HuggingFace 登入成功")
            except Exception as e:
                logger.warning(f"HuggingFace 登入失敗：{e}")
            
            # 載入模型
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=True
            )
            
            if self.pipeline:
                self.loaded = True
                logger.info("[OK] Speaker Diarization loaded")
            else:
                logger.warning("[WARN] Speaker Diarization load failed - running without speaker separation")
                
        except Exception as e:
            logger.warning(f"[WARN] Speaker Diarization load failed: {e}")
            logger.warning("Will run without speaker separation")
            self.pipeline = None
    
    def diarize(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> List[Tuple[float, float, str]]:
        """
        執行說話者分離
        
        Args:
            audio: 音訊數據 (float32, mono)
            sample_rate: 取樣率
            
        Returns:
            說話者段落列表 [(start, end, speaker_id), ...]
        """
        if not self.loaded or self.pipeline is None:
            return []
        
        try:
            import torch
            from torch import FloatTensor
            
            # 轉換為 torch tensor
            audio_tensor: FloatTensor = FloatTensor(audio.astype(np.float32))
            
            # 執行說話者分離
            diarization = self.pipeline(
                {"waveform": audio_tensor.unsqueeze(0), "sample_rate": sample_rate},
                min_speakers=self.min_speakers,
                max_speakers=self.max_speakers
            )
            
            # 提取結果
            segments: List[Tuple[float, float, str]] = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                start: float = turn.start
                end: float = turn.end
                speaker_name: str = f"Role {speaker.replace('SPEAKER_', '')}"
                segments.append((start, end, speaker_name))
            
            logger.debug(f"說話者分離完成：{len(segments)} 個段落")
            return segments
            
        except Exception as e:
            logger.warning(f"[WARN] Diarization failed: {e}")
            return []
    
    def set_num_speakers(self, min_speakers: int = 1, max_speakers: int = 4) -> None:
        """設定說話者數量範圍"""
        self.min_speakers = min_speakers
        self.max_speakers = max_speakers
        logger.debug(f"說話者數量設定：{min_speakers}-{max_speakers}")


class QwenASREngine:
    """Qwen3-ASR 語音辨識引擎"""
    
    def __init__(self, model_name: str = "Qwen/Qwen3-ASR-1.7B", device: str = "cpu") -> None:
        self.model_name: str = model_name
        self.device: str = device
        self.model = None
        self.loaded: bool = False
        
    def load_model(self) -> None:
        """載入 ASR 模型"""
        if self.loaded:
            logger.debug(f"ASR 模型已載入：{self.model_name}")
            return
        
        logger.info(f"🚀 Loading ASR: {self.model_name} on {self.device}...")
        
        try:
            import torch
            from qwen_asr import Qwen3ASRModel
            
            # 關鍵：GPU 必須用 float16，否則 1.7B 會爆 VRAM
            dtype: torch.dtype = torch.float16 if self.device == "cuda" else torch.float32
            
            self.model = Qwen3ASRModel.from_pretrained(
                self.model_name,
                dtype=dtype,
                device_map=self.device,
                trust_remote_code=True
            )
            self.loaded = True
            
            # 釋放未使用的 GPU 記憶體
            if self.device == "cuda" and torch.cuda.is_available():
                try:
                    torch.cuda.empty_cache()
                    logger.info(f"[OK] ASR loaded on {self.device}, VRAM cleared")
                except Exception as e:
                    logger.warning(f"VRAM 清理失敗：{e}")
            else:
                logger.info(f"[OK] ASR loaded on {self.device}")
                
        except Exception as e:
            logger.error(f"[ERROR] ASR Load Failed: {e}", exc_info=True)
            raise
    
    def process_audio(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None
    ) -> str:
        """
        處理音訊並返回轉錄文字
        
        Args:
            audio: 音訊數據 (float32, mono)
            sample_rate: 取樣率 (預設 16kHz)
            language: 語言設定 (None = 自動偵測，"Chinese", "English" 等)
            
        Returns:
            轉錄文字
        """
        if self.model is None:
            self.load_model()
        
        if self.model is None:
            logger.error("ASR 模型未載入")
            return ""
        
        try:
            # 確保 audio 是 float32
            audio = audio.astype(np.float32)
            
            # 重取樣到 16kHz (如果需要)
            if sample_rate != 16000:
                from librosa import resample
                audio = resample(audio, orig_sr=sample_rate, target_sr=16000)
                logger.debug(f"音訊已重取樣：{sample_rate} -> 16000")
            
            # 執行轉錄
            results = self.model.transcribe(
                audio=(audio, 16000),
                language=language,
            )
            
            # 提取文字
            if results and len(results) > 0:
                text: str = results[0].text
                result = text.strip()
                logger.debug(f"ASR 辨識結果：{result[:100]}...")
                return result
            else:
                logger.debug("ASR 未辨識到文字")
                return ""
                
        except Exception as e:
            logger.error(f"ASR 辨識錯誤：{e}", exc_info=True)
            return ""
    
    def process_audio_with_timestamps(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        處理音訊並返回帶時間戳的結果
        
        Args:
            audio: 音訊數據
            sample_rate: 取樣率
            language: 語言設定
            
        Returns:
            dict: {text: str, language: str, timestamps: List}
        """
        if self.model is None:
            self.load_model()
        
        if self.model is None:
            return {"text": "", "language": "", "timestamps": []}
        
        try:
            from qwen_asr import Qwen3ForcedAligner
            
            # 確保 audio 是 float32
            audio = audio.astype(np.float32)
            
            # 重取樣到 16kHz
            if sample_rate != 16000:
                from librosa import resample
                audio = resample(audio, orig_sr=sample_rate, target_sr=16000)
            
            # 先進行 ASR 辨識
            asr_results = self.model.transcribe(
                audio=(audio, 16000),
                language=language,
                return_time_stamps=True,
            )
            
            if asr_results and len(asr_results) > 0:
                result = asr_results[0]
                return {
                    "text": result.text.strip(),
                    "language": getattr(result, 'language', ''),
                    "timestamps": getattr(result, 'time_stamps', [])
                }
            
            return {"text": "", "language": "", "timestamps": []}
            
        except Exception as e:
            logger.error(f"ASR 時間戳辨識錯誤：{e}", exc_info=True)
            return {"text": "", "language": "", "timestamps": []}
    
    def set_language(self, language: str = "auto") -> None:
        """
        設定辨識語言（此方法僅用於介面相容性）
        
        Args:
            language: 語言代碼 ("zh", "en", "ja", "auto" 等)
        """
        # qwen-asr 在 transcribe 時指定語言
        logger.debug(f"ASR 語言設定：{language}")
        pass
    
    def unload_model(self) -> None:
        """卸載模型以釋放記憶體"""
        if self.model is not None:
            try:
                del self.model
                self.model = None
                self.loaded = False
                
                # 釋放 GPU 記憶體
                if self.device == "cuda" and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    logger.info(f"ASR 模型已卸載，VRAM 已釋放")
            except Exception as e:
                logger.error(f"卸載 ASR 模型失敗：{e}", exc_info=True)


class TranslationEngine:
    """翻譯引擎 - 使用本地端 Ollama (TranslateGemma)"""
    
    def __init__(self, source_lang: str = "auto", target_lang: str = "zh") -> None:
        self.source_lang: str = source_lang
        self.target_lang: str = target_lang
        self.loaded: bool = False
        
        # 指向 Ollama 嘅 API URL 同你下載咗嘅 Gemma 模型
        self.api_url: str = "http://localhost:11434/api/generate"
        self.model_name: str = "translategemma:4b-it-q4_K_M"
        self.history: List[str] = []
        
        # LLM 需要文字指令，所以我哋將代碼轉換成清晰嘅語言名稱
        self.lang_map: Dict[str, str] = {
            "zh": "Traditional Chinese (繁體中文)",
            "en": "English",
            "ja": "Japanese",
            "ko": "Korean"
        }
    
    def load_model(self) -> None:
        """檢查 Ollama 服務並進行模型預熱 (Warm-up)"""
        if self.loaded:
            logger.debug("翻譯引擎已載入")
            return
            
        try:
            # 第一步：Ping 一吓 Ollama 睇吓有無反應
            logger.info("正在連接 Ollama API...")
            response = requests.get("http://127.0.0.1:11434/", timeout=5)
            
            if response.status_code == 200:
                logger.info(f"成功連接 Ollama API. 正在預熱模型：{self.model_name}...")
                
                # 第二步：發送一個「熱身」請求，強迫 Ollama 立即將模型放入 RAM
                warmup_payload: Dict[str, Any] = {
                    "model": self.model_name,
                    "prompt": "hi",
                    "stream": False,
                    "options": {
                        "num_predict": 1
                    }
                }
                
                # 呢個動作會食你 5 到 10 秒時間，但因為係開 App 階段所以無問題
                requests.post(self.api_url, json=warmup_payload, timeout=60)
                
                logger.info(f"[OK] 模型預熱完成！Ollama 翻譯引擎已處於備戰狀態。")
                self.loaded = True
            else:
                logger.warning(f"Ollama API 回應異常：{response.status_code}")
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"無法連接 Ollama，請確保 Ollama 已經啟動！({e})")
        except Exception as e:
            logger.error(f"Ollama 預熱失敗：{e}", exc_info=True)
    
    def translate(self, text: str) -> str:
        """
        發送文字俾 Ollama 進行翻譯 (帶上下文記憶)
        
        Args:
            text: 需要翻譯的文字
            
        Returns:
            翻譯結果
        """
        if not text.strip():
            return ""
            
        if not self.loaded:
            self.load_model()
            
        try:
            tgt_lang_name: str = self.lang_map.get(
                self.target_lang,
                "Traditional Chinese (繁體中文)"
            )
            
            # 將過去的句子組合成上下文
            context_str: str = " ".join(self.history[-3:]) if self.history else "None"
            
            # 升級版 Prompt：明確區分「上下文」同「需要翻譯嘅新文字」
            prompt: str = (
                f"Here is the conversation context (for reference only): {context_str}\n\n"
                f"Translate the following NEW TEXT to {tgt_lang_name}. "
                f"ONLY output the translation of the NEW TEXT. Do not translate the context, "
                f"and do not include any explanations.\n\n"
                f"NEW TEXT: {text}"
            )
            
            payload: Dict[str, Any] = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(self.api_url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result: str = response.json().get("response", "").strip()
                
                # 成功翻譯後，將今次嘅「原文」加入歷史記錄，保持最多 3 句
                self.history.append(text)
                if len(self.history) > 3:
                    self.history.pop(0)
                
                logger.debug(f"翻譯完成：{text[:50]}... -> {result[:50]}...")
                return result
            else:
                logger.warning(f"翻譯 API 返回錯誤：{response.status_code}")
                return text
                
        except requests.exceptions.Timeout as e:
            logger.error(f"翻譯請求超時：{e}")
            return text
        except Exception as e:
            logger.error(f"翻譯發生錯誤：{e}", exc_info=True)
            return text
    
    def unload_model(self) -> None:
        """卸載翻譯模型"""
        self.loaded = False
        self.history = []
        logger.info("翻譯引擎已卸載")


class SubtitleGenerator:
    """雙語字幕生成器"""
    
    def __init__(self) -> None:
        self.segments: List[Dict[str, Any]] = []
    
    def add_segment(
        self,
        start: float,
        end: float,
        original: str,
        translated: str,
        speaker: Optional[str] = None
    ) -> None:
        """
        添加字幕段落
        
        Args:
            start: 開始時間（秒）
            end: 結束時間（秒）
            original: 原文
            translated: 譯文
            speaker: 說話者（可選）
        """
        self.segments.append({
            'start': start,
            'end': end,
            'original': original,
            'translated': translated,
            'speaker': speaker
        })
        logger.debug(f"添加字幕段落：{start:.2f}s - {end:.2f}s")
    
    def format_time(self, seconds: float) -> str:
        """將秒數轉換為 SRT 時間格式"""
        hours: int = int(seconds // 3600)
        minutes: int = int((seconds % 3600) // 60)
        secs: int = int(seconds % 60)
        millis: int = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def export_srt(self, filepath: str, dual_language: bool = True) -> None:
        """
        匯出 SRT 字幕檔
        
        Args:
            filepath: 輸出檔案路徑
            dual_language: 是否輸出雙語
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for i, seg in enumerate(self.segments, 1):
                    # 序號
                    f.write(f"{i}\n")
                    
                    # 時間軸
                    f.write(f"{self.format_time(seg['start'])} --> {self.format_time(seg['end'])}\n")
                    
                    # 文字
                    if seg.get('speaker'):
                        f.write(f"{seg['speaker']}: ")
                    
                    if dual_language:
                        f.write(f"{seg['original']}\n")
                        f.write(f"{seg['translated']}\n")
                    else:
                        f.write(f"{seg['translated']}\n")
                    
                    f.write("\n")
            
            logger.info(f"✅ 字幕已匯出：{filepath}")
            
        except Exception as e:
            logger.error(f"匯出 SRT 失敗：{e}", exc_info=True)
            raise
