"""
ASR & Translation 引擎 - 連接 LM Studio / OpenAI-compatible API
"""

import numpy as np
from typing import Optional, List, Tuple, Dict, Any
import requests
from core.logging_config import get_logger
from config.settings import config, BackendType

logger = get_logger(__name__)


class ASREngine:
    """ASR 引擎 - 連接 LM Studio / OpenAI-compatible API"""
    
    def __init__(
        self,
        backend: BackendType = None,
        model: str = None,
        api_url: str = None,
        api_key: str = None
    ) -> None:
        self.backend = backend or config.asr_backend
        self.model = model or config.asr_model
        self.api_url = api_url or config.asr_api_url
        self.api_key = api_key or config.asr_api_key
        self.loaded: bool = False
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
    
    def load_model(self) -> None:
        if self.loaded:
            return
        
        logger.info(f"Connecting to ASR API: {self.api_url}")
        
        try:
            response = self.session.get(f"{self.api_url}/models", timeout=5)
            if response.status_code == 200:
                self.loaded = True
                logger.info(f"[OK] API connected, model: {self.model}")
            else:
                logger.warning(f"API 回應異常：{response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.error(f"無法連接 API：{self.api_url}")
        except Exception as e:
            logger.error(f"API 連接失敗：{e}")
    
    def process_audio(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None
    ) -> str:
        if not self.loaded:
            self.load_model()
        
        if not self.loaded:
            logger.warning("ASR API 未連接")
            return ""
        
        try:
            audio = audio.astype(np.float32)
            
            if sample_rate != 16000:
                from librosa import resample
                audio = resample(audio, orig_sr=sample_rate, target_sr=16000)
            
            audio_b64 = self._audio_to_base64(audio)
            
            payload = {
                "model": self.model,
                "audio": audio_b64,
                "language": language or "auto"
            }
            
            response = self.session.post(
                f"{self.api_url}/audio/transcriptions",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                text = response.json().get("text", "").strip()
                logger.debug(f"ASR 結果：{text[:100]}...")
                return text
            else:
                logger.warning(f"API 錯誤：{response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"ASR 辨識錯誤：{e}", exc_info=True)
            return ""
    
    def _audio_to_base64(self, audio: np.ndarray) -> str:
        import base64
        import io
        import soundfile as sf
        
        buffer = io.BytesIO()
        sf.write(buffer, audio, 16000, format='WAV')
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
    
    def unload_model(self) -> None:
        self.loaded = False
        logger.info("ASR 引擎已卸載")


class TranslationEngine:
    """翻譯引擎 - 連接 LM Studio / OpenAI-compatible API"""
    
    def __init__(
        self,
        backend: BackendType = None,
        model: str = None,
        api_url: str = None,
        api_key: str = None,
        target_lang: str = "zh"
    ) -> None:
        self.backend = backend or config.translate_backend
        self.model = model or config.translate_model
        self.api_url = api_url or config.translate_api_url
        self.api_key = api_key or config.translate_api_key
        self.target_lang = target_lang
        self.loaded: bool = False
        self.history: List[str] = []
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        
        self.lang_map: Dict[str, str] = {
            "zh": "Traditional Chinese (繁體中文)",
            "en": "English",
            "ja": "Japanese",
            "ko": "Korean"
        }
    
    def load_model(self) -> None:
        if self.loaded:
            return
        
        logger.info(f"Connecting to Translation API: {self.api_url}")
        
        try:
            response = self.session.get(f"{self.api_url}/models", timeout=5)
            if response.status_code == 200:
                self.loaded = True
                logger.info(f"[OK] API connected, model: {self.model}")
            else:
                logger.warning(f"API 回應異常：{response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.error(f"無法連接 API：{self.api_url}")
        except Exception as e:
            logger.error(f"API 連接失敗：{e}")
    
    def translate(self, text: str) -> str:
        if not text.strip():
            return ""
        
        if not self.loaded:
            self.load_model()
        
        if not self.loaded:
            logger.warning("翻譯 API 未連接")
            return text
        
        try:
            tgt_lang = self.lang_map.get(self.target_lang, "Traditional Chinese (繁體中文)")
            context = " ".join(self.history[-3:]) if self.history else "None"
            
            prompt = (
                f"Context: {context}\n\n"
                f"Translate to {tgt_lang}. Only output the translation, no explanations:\n\n{text}"
            )
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 1024
            }
            
            response = self.session.post(
                f"{self.api_url}/chat/completions",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                translated = result["choices"][0]["message"]["content"].strip()
                
                self.history.append(text)
                if len(self.history) > 3:
                    self.history.pop(0)
                
                logger.debug(f"翻譯結果：{translated[:50]}...")
                return translated
            else:
                logger.warning(f"API 錯誤：{response.status_code}")
                return text
                
        except Exception as e:
            logger.error(f"翻譯錯誤：{e}")
            return text
    
    def unload_model(self) -> None:
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
        self.segments.append({
            'start': start,
            'end': end,
            'original': original,
            'translated': translated,
            'speaker': speaker
        })
    
    def format_time(self, seconds: float) -> str:
        hours: int = int(seconds // 3600)
        minutes: int = int((seconds % 3600) // 60)
        secs: int = int(seconds % 60)
        millis: int = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def export_srt(self, filepath: str, dual_language: bool = True) -> None:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for i, seg in enumerate(self.segments, 1):
                    f.write(f"{i}\n")
                    f.write(f"{self.format_time(seg['start'])} --> {self.format_time(seg['end'])}\n")
                    if seg.get('speaker'):
                        f.write(f"{seg['speaker']}: ")
                    if dual_language:
                        f.write(f"{seg['original']}\n")
                        f.write(f"{seg['translated']}\n")
                    else:
                        f.write(f"{seg['translated']}\n")
                    f.write("\n")
            logger.info(f"字幕已匯出：{filepath}")
        except Exception as e:
            logger.error(f"匯出 SRT 失敗：{e}", exc_info=True)
            raise