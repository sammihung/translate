"""
AI Controller - 連接 LM Studio API
"""

from typing import Optional, Tuple, List, Callable
import numpy as np
from core.logging_config import get_logger
from config.settings import config

logger = get_logger(__name__)


class AIController:
    
    def __init__(self) -> None:
        self.asr_engine = None
        self.translate_engine = None
        self.engines_ready: bool = False
    
    def load_all_models(
        self,
        target_lang: str = "zh",
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        try:
            if progress_callback:
                progress_callback("正在連接 ASR API...")
            
            logger.info(f"正在連接 ASR API: {config.asr_api_url}")
            
            from ai.asr_engine import ASREngine
            self.asr_engine = ASREngine()
            self.asr_engine.load_model()
            
            if progress_callback:
                progress_callback("正在連接翻譯 API...")
            
            logger.info(f"正在連接翻譯 API: {config.translate_api_url}")
            
            from ai.translation_engine import TranslationEngine
            self.translate_engine = TranslationEngine(target_lang=target_lang)
            self.translate_engine.load_model()
            
            self.engines_ready = True
            
            if progress_callback:
                progress_callback("[OK] API 已連接")
            
            logger.info("引擎初始化完成")
            return True
            
        except Exception as e:
            self.engines_ready = False
            logger.error(f"引擎初始化失敗：{e}", exc_info=True)
            
            if progress_callback:
                progress_callback(f"[ERROR] {str(e)}")
            
            return False
    
    def process_audio(
        self,
        audio: np.ndarray,
        src_lang: str = "auto",
        skip_translation: bool = False
    ) -> Tuple[str, str, Optional[str]]:
        try:
            if not self.engines_ready:
                return "", "", None
            
            text: str = ""
            if self.asr_engine:
                try:
                    lang_param: Optional[str] = None if src_lang == "auto" else src_lang
                    text = self.asr_engine.process_audio(audio, language=lang_param)
                except Exception as e:
                    logger.error(f"ASR 處理錯誤：{e}", exc_info=True)
            
            translated: str = ""
            if not skip_translation and text.strip() and self.translate_engine:
                try:
                    translated = self.translate_engine.translate(text)
                except Exception as e:
                    logger.error(f"翻譯錯誤：{e}", exc_info=True)
            
            if text.strip():
                return text, translated, None
            
            return "", "", None
            
        except Exception as e:
            logger.error(f"process_audio 失敗：{e}", exc_info=True)
            return "", "", None
    
    def get_status(self) -> str:
        if not self.engines_ready:
            return "引擎未就緒"
        
        parts: List[str] = []
        if self.asr_engine:
            parts.append("ASR")
        if self.translate_engine:
            parts.append("翻譯")
        return " + ".join(parts)
    
    def cleanup(self) -> None:
        try:
            if self.asr_engine and hasattr(self.asr_engine, 'unload_model'):
                self.asr_engine.unload_model()
            if self.translate_engine and hasattr(self.translate_engine, 'unload_model'):
                self.translate_engine.unload_model()
            self.engines_ready = False
            logger.info("AI 控制器資源已清理")
        except Exception as e:
            logger.error(f"cleanup 失敗：{e}", exc_info=True)
    
    def translate_text(self, text: str) -> str:
        if self.translate_engine:
            try:
                return self.translate_engine.translate(text)
            except Exception as e:
                logger.error(f"翻譯錯誤：{e}", exc_info=True)
        return text